"""S286 AA-1146 part 1 live proof (CIS api container, role cis_app, $0, nothing persists).

CIS #1598 (192d1adb, CIS 457/458) + #1599 (56a348c8): tour draft versions with reason / author / word diff, the source
tour's revision history (silver_aa_internal.raw_tour_revision), the one publish gate that locks a hand-edited Master
(gold_aa_internal.published_tours.human_lock_at / _by / _reason), and the S1 job, run-tour and S1 batch skipping a
locked tour before any paid call.

How: ONE transaction on the live Dev DB, ROLLED BACK at the end, mirroring tests/integration/test_aa1146_tour_versions_pg.py
on one existing published AA Master (chosen by id, only its id is printed). The route functions themselves are called
with a request stand-in whose pool hands out this one connection: update_raw_tour_fields (PATCH /admin/tours/{id}/raw),
put_tour_draft (PUT /admin/tours/{id}/draft), publish_tour_draft (POST /admin/tours/{id}/draft/publish), run_tour
(POST /admin/run-tour) and submit_s1_batch_endpoint (POST /admin/s1-batch/submit), plus the S1 job's own lock check
(s1_rewrite_job._early_result) and the export guard (human_lock.guard_export).

Patched in THIS script's process only (the API process is untouched):
- verify_admin_secret: a no-op (the staff route policy is enforced by middleware, not under test here);
- process_export opens its own connection (asyncpg.connect): it is handed this connection instead, so the real publish
  (lifecycle publish, Master swap, lock) runs inside the rolled-back transaction; its conn.close() is a no-op;
- the job enqueues and post-commit effects of the publish (a3_atomize, source fan-out, TripPlanner purge, tenant
  fan-out, recompute) and of the raw edit (source fan-out) are recorders: nothing is enqueued, the script prints what
  WOULD have been enqueued;
- _execute_run_tour and submit_s1_batch are recorders that must stay at 0 calls (a locked tour never reaches them);
- the re-validation (the paid S1 checks graph) is NOT run: the gate refusal without it is shown (409
  revalidate_required), then revalidate_passed is set in the transaction exactly as the integration test does.

No LLM call, no job row, no S3 / HTTP call. Prints ids, counts, codes and booleans only (no tour text, no reason text).
Optional env TOUR_ID=<uuid> pins the tour. Exit 1 when an expectation fails.
"""
import asyncio
import json
import os
import sys
import traceback
import uuid
from contextlib import asynccontextmanager
from types import SimpleNamespace

import asyncpg
from fastapi import HTTPException

from api.routers import admin_pipeline as ap
from services.content_generation import human_lock
from services.export import handler as export_handler

MASTER = "00000000-0000-0000-0000-000000000001"
EDITOR = "00000000-0000-4000-8000-000000000286"     # synthetic staff ids (no admin_users row needed)
LEAD = "00000000-0000-4000-8000-000000000287"
TAG = "S286-PROOF"
RAW_REASON = f"{TAG} supplier sheet correction"
DRAFT_REASON = f"{TAG} clearer summary for the proof"

failed: list[str] = []
calls: dict[str, int] = {}


def out(step: str, **kw) -> None:
    print(json.dumps({"step": step, **kw}, default=str), flush=True)


def expect(name: str, ok: bool, **kw) -> None:
    out(name, ok=bool(ok), **kw)
    if not ok:
        failed.append(name)


def recorder(name: str, result=None):
    async def _rec(*_a, **_k):
        calls[name] = calls.get(name, 0) + 1
        return result
    return _rec


class _OneConnPool:
    def __init__(self, conn):
        self.conn = conn

    @asynccontextmanager
    async def acquire(self, timeout=None):
        yield self.conn


class _Borrowed:
    """This script's connection handed to process_export: every call goes to it, close() does nothing."""

    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, name):
        return getattr(self._conn, name)

    async def close(self, *_a, **_k):
        return None


class _AsyncpgShim:
    """services.export.handler's `asyncpg` while the publish runs: connect() returns this script's connection."""

    def __init__(self, real, conn):
        self._real, self._conn = real, conn

    def __getattr__(self, name):
        return getattr(self._real, name)

    async def connect(self, *_a, **_k):
        calls["process_export_connect_borrowed"] = calls.get("process_export_connect_borrowed", 0) + 1
        return _Borrowed(self._conn)


def request(conn, *, role: str, user: str, body=None):
    async def _json():
        return dict(body or {})
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(pool=_OneConnPool(conn))), scope={},
                           headers={"x-admin-role": role, "x-admin-user-id": user}, json=_json)


def http_code(exc: HTTPException):
    d = exc.detail
    code = d.get("code") if isinstance(d, dict) else None
    return exc.status_code, code or (exc.headers or {}).get("X-Error-Code")


def word_counts(diff: list) -> dict:
    ins = sum(len(o["text"].split()) for d in diff for o in d["ops"] if o["op"] == "insert")
    dele = sum(len(o["text"].split()) for d in diff for o in d["ops"] if o["op"] == "delete")
    return {"fields": [d["field"] for d in diff], "ops": sum(len(d["ops"]) for d in diff),
            "words_inserted": ins, "words_deleted": dele}


def patch_side_effects(conn) -> list:
    """Set every patch; returns (target, name, original) to restore."""
    from services.jobs import a3_atomize_job
    from services.quality import source_fanout
    from services.tour_lifecycle import effects
    from services.content_generation import s1_batch
    saved = []

    def put(target, name, value):
        saved.append((target, name, getattr(target, name)))
        setattr(target, name, value)

    put(ap, "verify_admin_secret", lambda *_a, **_k: None)
    put(ap, "_source_fanout_raw", recorder("raw_source_fanout_enqueue"))
    put(ap, "_execute_run_tour", recorder("execute_run_tour_PAID_PATH"))
    put(s1_batch, "submit_s1_batch", recorder("submit_s1_batch_PAID_PATH"))
    put(export_handler, "asyncpg", _AsyncpgShim(export_handler.asyncpg, conn))
    put(export_handler, "get_database_url", lambda *_a, **_k: "borrowed-connection")
    put(a3_atomize_job, "enqueue_a3_atomize", recorder("a3_atomize_enqueue", "s286-proof-not-enqueued"))
    put(source_fanout, "enqueue_safe", recorder("master_source_fanout_enqueue", {"enqueued": False}))
    for name in ("notify_tripplanner", "fan_out_to_tenants"):
        put(effects, name, recorder(f"effects_{name}", 0))
    for name in ("recompute_after_status_change", "recheck_trip_pages"):
        put(effects, name, recorder(f"effects_{name}"))
    return saved


CANDIDATES_SQL = """
    SELECT p.tour_id::text AS tour_id
      FROM gold_aa_internal.published_tours p
      JOIN silver_aa_internal.raw_tours r ON r.tour_id = p.tour_id
     WHERE p.tenant_id = '00000000-0000-0000-0000-000000000001'::uuid
       AND p.master_status = 'active' AND p.deleted_at IS NULL AND p.human_lock_at IS NULL
       AND r.source_status = 'active' AND r.deleted_at IS NULL
       AND NOT EXISTS (SELECT 1 FROM silver_aa_internal.generated_content g
                        WHERE g.tour_id = p.tour_id AND g.status = 'draft' AND g.origin = 'human')
     ORDER BY p.tour_id
     LIMIT 5
"""


async def prove(conn, tour_id: str) -> bool:
    """The whole flow on one tour. False = the tour was refused by a rule outside this proof (try the next one)."""
    gc_before = await conn.fetchval(
        "SELECT count(*) FROM silver_aa_internal.generated_content WHERE tour_id = $1::uuid", tour_id)
    rev_before = await conn.fetchval(
        "SELECT count(*) FROM silver_aa_internal.raw_tour_revision WHERE tour_id = $1::uuid", tour_id)
    live_before = await conn.fetchval(
        "SELECT generated_content_id::text FROM gold_aa_internal.published_tours WHERE tour_id = $1::uuid", tour_id)
    switch = await ap.drafts.gate.switch_on(conn)
    out("tour", tour_id=tour_id, versions_before=gc_before, raw_revisions_before=rev_before,
        two_person_publish_switch=switch)

    # 1. A staff edit of the source tour keeps the old values: one raw_tour_revision row (staff_edit, actor, reason).
    cur = await conn.fetchval("SELECT inclusions FROM silver_aa_internal.raw_tours WHERE tour_id = $1::uuid", tour_id)
    raw = await ap.update_raw_tour_fields(tour_id, request(conn, role="content", user=EDITOR, body={
        "inclusions": f"{cur or ''} ({TAG})".strip(), "reason": RAW_REASON}))
    rev = await conn.fetchrow(
        "SELECT revision_num, source, fields, actor, reason = $2 AS reason_matches,"
        " before ? 'inclusions' AS has_before, after ? 'inclusions' AS has_after"
        " FROM silver_aa_internal.raw_tour_revision WHERE tour_id = $1::uuid ORDER BY revision_num DESC LIMIT 1",
        tour_id, RAW_REASON)
    rev_after = await conn.fetchval(
        "SELECT count(*) FROM silver_aa_internal.raw_tour_revision WHERE tour_id = $1::uuid", tour_id)
    expect("raw_edit_revision_row", rev_after - rev_before == 1 and rev["source"] == "staff_edit"
           and rev["actor"] == f"admin:{EDITOR}" and rev["reason_matches"] and rev["has_before"] and rev["has_after"],
           revision_num=raw["revision_num"], raw_revisions_delta=rev_after - rev_before, source=rev["source"],
           fields=list(rev["fields"]), actor_is_editor=rev["actor"] == f"admin:{EDITOR}",
           reason_matches=rev["reason_matches"], keeps_before_and_after=rev["has_before"] and rev["has_after"])

    # 2. A wording draft: a new version (origin human, reason, author), the live version untouched, a word diff.
    live_summary = await conn.fetchval(
        "SELECT aa_summary FROM silver_aa_internal.generated_content WHERE id = $1::uuid", live_before)
    new_summary = f"{live_summary or ''} {TAG} hand edit.".strip()
    saved = await ap.put_tour_draft(tour_id, request(conn, role="content", user=EDITOR),
                                    ap.drafts.DraftSave(fields={"aa_summary": new_summary}, reason=DRAFT_REASON))
    d = saved["draft"]
    row = await conn.fetchrow(
        "SELECT status::text AS status, origin, edit_reason = $2 AS reason_matches, author_id, human_edited,"
        " parent_version_num FROM silver_aa_internal.generated_content WHERE id = $1::uuid", d["id"], DRAFT_REASON)
    gc_after = await conn.fetchval(
        "SELECT count(*) FROM silver_aa_internal.generated_content WHERE tour_id = $1::uuid", tour_id)
    live_now = await conn.fetchval(
        "SELECT generated_content_id::text FROM gold_aa_internal.published_tours WHERE tour_id = $1::uuid", tour_id)
    wd = word_counts(saved["diff"])
    expect("draft_version_created",
           saved["created"] and gc_after - gc_before == 1 and row["status"] == "draft" and row["origin"] == "human"
           and row["reason_matches"] and row["author_id"] == f"admin:{EDITOR}" and live_now == live_before
           and wd["fields"] == ["aa_summary"] and wd["words_inserted"] >= 2,
           draft_id=d["id"], version_num=d["version_num"], base_version_num=d["base_version_num"],
           versions_delta=gc_after - gc_before, status=row["status"], origin=row["origin"],
           reason_matches=row["reason_matches"], author_is_editor=row["author_id"] == f"admin:{EDITOR}",
           editors=len(d["editors"]), live_version_untouched=live_now == live_before, word_diff=wd)

    # 3. The gate: no publish before a passing re-check (409 revalidate_required).
    lead = request(conn, role="content_lead", user=LEAD)
    try:
        await ap.publish_tour_draft(tour_id, lead)
        code = (200, None)
    except HTTPException as exc:
        code = http_code(exc)
    expect("gate_refuses_unchecked_draft", code == (409, "revalidate_required"), status=code[0], code=code[1])
    if switch:   # two-person rule: the draft's own editor may not publish it
        try:
            await ap.publish_tour_draft(tour_id, request(conn, role="content_lead", user=EDITOR))
            same = (200, None)
        except HTTPException as exc:
            same = http_code(exc)
        expect("gate_refuses_the_editor", same[0] == 403 and same[1] in ("same_person", "two_person_required"),
               status=same[0], code=same[1])
    # the paid S1 re-check is not run: its passing verdict is set as the integration test does
    await conn.execute("UPDATE silver_aa_internal.generated_content SET revalidate_passed = true WHERE id = $1::uuid",
                       d["id"])

    # 4. Publish through the gate (a second person): process_export exit human_publish on this connection.
    try:
        res = await ap.publish_tour_draft(tour_id, lead)
    except HTTPException as exc:
        status, code = http_code(exc)
        if status == 409 and code in ("policy_review_required", "source_not_live"):
            out("tour_refused_outside_proof", tour_id=tour_id, status=status, code=code)
            return False
        raise
    pt = await conn.fetchrow(
        "SELECT generated_content_id::text AS gc, human_lock_at IS NOT NULL AS locked, human_lock_by,"
        " human_lock_reason = $2 AS reason_matches FROM gold_aa_internal.published_tours WHERE tour_id = $1::uuid",
        tour_id, DRAFT_REASON)
    vstatus = await conn.fetchval(
        "SELECT status::text FROM silver_aa_internal.generated_content WHERE id = $1::uuid", d["id"])
    expect("published_and_master_locked",
           res["published"] and res["locked"] and pt["gc"] == d["id"] and pt["locked"]
           and pt["human_lock_by"] == f"admin:{LEAD}" and pt["reason_matches"] and vstatus == "approved",
           version_num=res["version_num"], master_points_to_draft=pt["gc"] == d["id"], version_status=vstatus,
           human_lock_at_set=pt["locked"], human_lock_by_is_publisher=pt["human_lock_by"] == f"admin:{LEAD}",
           human_lock_reason_is_draft_reason=pt["reason_matches"],
           process_export_used_this_connection=calls.get("process_export_connect_borrowed", 0) == 1)
    after_state = await ap.get_tour_draft(tour_id, request(conn, role="content", user=EDITOR))
    expect("no_open_draft_after_publish", after_state["draft"] is None and after_state["lock"] is not None,
           open_draft=after_state["draft"] is not None, lock_reported=after_state["lock"] is not None)

    # 5. Automatic reruns skip the locked tour before any paid call.
    from services.jobs import s1_rewrite_job as job
    progress = []

    async def _progress(**kw):
        progress.append(kw)
    ctx = SimpleNamespace(pool=_OneConnPool(conn), job_id="s286-proof-no-job", progress=_progress)
    early = await job._early_result(ctx, {}, tour_id)
    expect("s1_job_skips_locked_tour", bool(early) and early.get("skipped") and early.get("reason") == "human_locked",
           result_skipped=bool(early and early.get("skipped")), reason=(early or {}).get("reason"),
           progress_phase=[p.get("phase") for p in progress], progress_skip_reason=[p.get("skip_reason")
                                                                                  for p in progress])
    try:
        await ap.run_tour(ap.TourRunRequest(tour_id=tour_id, batch_id=str(uuid.uuid4()), tenant_id=MASTER), lead)
        rt = (200, None)
    except HTTPException as exc:
        rt = http_code(exc)
    expect("run_tour_refuses_locked_tour", rt == (409, "human_locked")
           and calls.get("execute_run_tour_PAID_PATH", 0) == 0,
           status=rt[0], code=rt[1], paid_path_calls=calls.get("execute_run_tour_PAID_PATH", 0))
    try:
        await ap.submit_s1_batch_endpoint(ap.S1BatchSubmitRequest(tour_ids=[tour_id], batch_id=str(uuid.uuid4())),
                                          lead)
        sb, skipped = (202, None), None
    except HTTPException as exc:
        sb = http_code(exc)
        skipped = exc.detail.get("skipped_locked") if isinstance(exc.detail, dict) else None
    expect("s1_batch_leaves_out_locked_tour", sb == (409, "human_locked") and skipped == [tour_id]
           and calls.get("submit_s1_batch_PAID_PATH", 0) == 0,
           status=sb[0], code=sb[1], skipped_locked_is_tour=skipped == [tour_id],
           paid_path_calls=calls.get("submit_s1_batch_PAID_PATH", 0))
    # the export backstop: an automatic exit over the lock is refused (inside a savepoint, rolled back)
    refused = None
    try:
        async with conn.transaction():
            await human_lock.guard_export(conn, "silver_aa_internal", d["id"], tour_id, "auto_publish")
    except human_lock.HumanLockedError:
        refused = "HumanLockedError"
    expect("export_refuses_automatic_exit", refused == "HumanLockedError", refused=refused)
    return True


async def main() -> int:
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    outer = conn.transaction()
    await outer.start()
    saved = []
    tour_done = None
    try:
        ready = await conn.fetchval(
            "SELECT count(*) FROM information_schema.columns WHERE table_schema = 'gold_aa_internal'"
            " AND table_name = 'published_tours' AND column_name = 'human_lock_at'")
        expect("cis_457_applied", ready == 1, columns=ready)
        saved = patch_side_effects(conn)
        pinned = os.environ.get("TOUR_ID")
        candidates = [pinned] if pinned else [r["tour_id"] for r in await conn.fetch(CANDIDATES_SQL)]
        out("candidates", count=len(candidates))
        for tour_id in candidates:
            sp = conn.transaction()
            await sp.start()
            if await prove(conn, tour_id):
                tour_done = tour_id
                break
            await sp.rollback()
            calls.clear()
        if tour_done is None:
            failed.append("no_tour_proved")
        out("would_have_enqueued_or_called", calls=dict(sorted(calls.items())))
        expect("no_paid_path_reached", calls.get("execute_run_tour_PAID_PATH", 0) == 0
               and calls.get("submit_s1_batch_PAID_PATH", 0) == 0)
    except Exception as exc:  # noqa: BLE001 — class, app code and location only, never a DB message
        failed.append("unexpected_error")
        tb = traceback.extract_tb(exc.__traceback__)
        detail = http_code(exc) if isinstance(exc, HTTPException) else None
        out("unexpected_error", error=type(exc).__name__, http=detail,
            where=[f"{os.path.basename(f.filename)}:{f.lineno}:{f.name}" for f in tb[-5:]])
    finally:
        await outer.rollback()
        for target, name, value in reversed(saved):
            setattr(target, name, value)
    try:
        if tour_done:
            left = await conn.fetchrow(
                "SELECT (SELECT count(*) FROM silver_aa_internal.generated_content WHERE tour_id = $1::uuid"
                "         AND origin = 'human' AND edit_reason = $2) AS drafts,"
                "       (SELECT count(*) FROM silver_aa_internal.raw_tour_revision WHERE tour_id = $1::uuid"
                "         AND reason = $3) AS revisions,"
                "       (SELECT count(*) FROM gold_aa_internal.published_tours WHERE tour_id = $1::uuid"
                "         AND human_lock_at IS NOT NULL) AS locks", tour_done, DRAFT_REASON, RAW_REASON)
            expect("rolled_back_nothing_persists", left["drafts"] == 0 and left["revisions"] == 0
                   and left["locks"] == 0, drafts_left=left["drafts"], revisions_left=left["revisions"],
                   locks_left=left["locks"])
    finally:
        await conn.close()
    print(json.dumps({"summary": "AA-1146 part 1 live proof", "tour_id": tour_done, "ok": not failed,
                      "failed": failed}), flush=True)
    return 0 if not failed else 1


sys.exit(asyncio.run(main()))
