"""AA-859 S240 — per-flag live checks for aa859_flip_verify.py (Dev, public API only).

aa859_flip_verify.py turns one flag ON, calls CHECKS[short](ctx), then looks in CloudWatch for the
LOG_EVENTS[short] lines with used_tenant_pool=True. ctx.A = terra-family (does the writes), ctx.B =
atlas-hearth (the foreign tenant). Every id is discovered as tenant A through list endpoints; nothing
is hard-coded. A missing precondition is one failing check that says what is missing (no invented data).
Secrets are read only through the framework's secret() and never printed or saved.

piece_edit (W2, aa859:piece_edit_pool) — PATCH /v1/content-writing/pieces/{id}; log aa859_piece_edit
  Needs: one of A's pieces with ready_state "ready" and content (GET /v1/content-writing/reviews).
  Checks: A PATCH own piece (original + probe suffix) -> 200, tenant-safe shape (ready_state "ready",
    content_text = sent text, no `status`); read back; B PATCH A's piece -> 404 and A's text unchanged;
    A PATCH random uuid -> 404.
  Restores (finally): A PATCH the exact original text, then GET and compare sha256 byte for byte.
    Leaves 2 content_piece.edited audit rows (probe + restore), as the route always does.

t2_version_write (W6, aa859:t2_version_write_pool) — PATCH /v1/tours/versions/{id}; log aa859_t2_version_write
  Needs: one of A's versions with status "approved" whose tour has no pending version
    (GET /v1/tours/my-versions, history from GET /v1/tours/versions/{id}).
  Checks: A reject -> 200 rejected, approve -> 200 approved; A edit {} -> 400; A edit with V's own
    content -> 200 edited, new_version_id N, version_number = max + 1; N resolved (approve when V is the
    newest approved version of the tour, so the newest approved content is unchanged; reject otherwise);
    B reject / approve / edit on V -> 404 each; A on a random uuid -> 404; V still approved after B.
  Restores (finally): V back to approved if it is not; N never left pending. N itself stays as a normal
    tenant_edit row (the tenant role cannot delete it; deleting goes through the DRY-RUN procedure) and
    is named in the evidence.

angle_gate_decide (W3, aa859:angle_gate_decide_pool) — POST /v1/angle-gate/requests/{id}/reopen and
  .../choose; logs aa859_angle_gate_reopen, aa859_angle_gate_choose
  Needs: one of A's angle-gate requests (request ids from /v1/content-writing/reviews) with status
    "approved", >= 2 angles and exactly one chosen (IDX0).
  Checks: B reopen A's approved request -> 404; A reopen -> 200 "reusable"; A reopen again -> 409;
    B choose on A's reusable request -> 404; A choose IDX1 != IDX0 -> 200 "approved", only IDX1 chosen;
    A choose IDX1 again -> 409; A reopen / choose on a random uuid -> 404.
  Restores (finally): reopen (if approved on another idx) + choose IDX0, then GET and compare status,
    chosen idx and option ids with the baseline (only updated_at moves).

unpublish (W4, aa859:unpublish_pool) — DELETE /v1/publish-log/{publish_id}; logs aa859_unpublish,
  tenant_self_unpublish
  Needs: A's WordPress integration either disconnected or connected to the E2E test site
    (aa-cis/dev/e2e-wordpress-test); one blog piece in GET /v1/publish-log/pending.
  Setup: connect the E2E WP site if A is disconnected (POST /v1/integrations/wordpress); publish the
    pending piece through POST /v1/publish-log/{piece_id}/publish (MAIN route; uses 1 of A's 20 daily
    publishes, not refundable).
  Checks: B DELETE A's publish_id -> 404, A's row still "published"; A DELETE -> 200 unpublished,
    unpublished_by tenant:<A>, remote trashed; WP read-back status "trash"; A DELETE again -> 404;
    A DELETE random uuid -> 404; publish-log shows "unpublished"; the piece is back in /pending.
  Restores (finally): if the row is still "published", one more A DELETE; the WP post is deleted
    permanently on the test site (force=true); A's WP integration is disconnected again if this check
    connected it (only when no published row is left behind). Publish/unpublish publish_log and
    audit_log rows stay as the audit trail.

t2_version_reads (W5a, aa859:t2_version_reads_pool) — GET /v1/tours/my-versions, /v1/tours/pool,
  /v1/tours/versions/{id}; log aa859_t2_version_read (route=pool|my_versions|version)
  Needs: A has >= 1 version (preferably one with a job_status).
  Checks: A my-versions / pool / versions/{V} -> 200 with the expected keys; consistency between them
    (V's job_status equal in list and detail, history ids are A's ids, pool already_rewritten matches A's
    tours, pool tenant_id = A); B GET versions/{V} -> 404; B's my-versions holds none of A's ids; A GET a
    random uuid -> 404. If flip_raw/t2_version_reads_baseline.json exists (taken with the flag OFF by
    `python3 aa859_flip_checks.py baseline-t2-reads`), the flag-on answers are compared with it.
  Restores: nothing (read-only).

integration_connect (W9, aa859:integration_connect_pool) — GET/POST /v1/integrations/wordpress,
  POST /v1/integrations/wordpress/test, GET /v1/integrations/facebook; logs aa859_integration_status,
  aa859_integration_connect, aa859_integration_test
  Needs: A disconnected, or connected with readable stored creds (acp/cms/<A>) / to the E2E site.
  Checks: status as A and B (WP + FB) -> 200; A POST connect (the stored creds when A was connected,
    else the E2E test-site creds) -> 200 connected, site_url as expected, connected_at unchanged when it
    was already connected; A POST test -> 200 success, last_verified_at moved; B's WP/FB status unchanged
    by A's writes; B POST test -> 404 when B has no WordPress connection.
  Restores (finally): A disconnected again (DELETE /v1/integrations/wordpress) if it started
    disconnected; when it started connected, the same creds were re-posted (only updated_at /
    last_verified_at move).

Run `python3 aa859_flip_checks.py baseline-t2-reads` only with aa859:t2_version_reads_pool OFF.
"""
import hashlib
import json
import pathlib
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

HERE = pathlib.Path(__file__).resolve().parent
T2_READS_BASELINE = HERE / "flip_raw" / "t2_version_reads_baseline.json"
WP_SECRET = "aa-cis/dev/e2e-wordpress-test"
PROBE_SUFFIX = "\n\n[AA-859 W2 probe]"
_REG = {}


# ── shared helpers ───────────────────────────────────────────────────────────────────────────────
def _framework():
    """The module that called register() (aa859_flip_verify, often as __main__): source of secret()."""
    for m in list(sys.modules.values()):
        if getattr(m, "CHECKS", None) is _REG.get("checks") and callable(getattr(m, "secret", None)):
            return m
    raise RuntimeError("aa859_flip_verify framework module not found (secret() unavailable)")


def _secret_json(name):
    return json.loads(_framework().secret(name))


def _j(body):
    return body if isinstance(body, dict) else {}


def _sha(s):
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:16]


def _host(url):
    h = (urlparse(url or "").hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class _Run:
    """Collects (id, desc, ok, evidence); `guard` turns any exception in a step into a failing check."""

    def __init__(self, ctx, prefix):
        self.ctx, self.prefix, self.res = ctx, prefix, []

    def add(self, cid, desc, ok, evidence):
        self.res.append((f"{self.prefix}{cid}", desc, bool(ok), str(evidence)[:400]))

    def call(self, slug, method, path, name, **kw):
        return self.ctx.call(slug, method, path, f"{self.prefix}{name}", **kw)

    @contextmanager
    def guard(self, cid, desc):
        try:
            yield
        except Exception as exc:  # noqa: BLE001 — a crashing step is a failed check
            self.add(cid, desc, False, f"error: {exc!r}"[:300])

    def save(self, name, obj):
        (self.ctx.out / f"{self.prefix}{name}.json").write_text(json.dumps(obj, indent=1, default=str))


# ── W2 piece_edit ────────────────────────────────────────────────────────────────────────────────
def check_piece_edit(ctx):
    r = _Run(ctx, "PE.")
    A, B = ctx.A, ctx.B
    pid = orig = None
    with r.guard("0", "precondition: A has a ready piece with content"):
        st, body = r.call(A, "GET", "/v1/content-writing/reviews", "0_reviews_a")
        rows = _j(body).get("data") or []
        cands = [d for d in rows if d.get("ready_state") == "ready" and (d.get("content_text") or "").strip()]
        if st != 200 or not cands:
            r.add("0", "precondition: A has a ready piece with content", False,
                  f"status={st} rows={len(rows)} ready_with_content=0 — nothing safe to edit")
            return r.res
        pid = cands[0]["piece_id"]
        st, body = r.call(A, "GET", f"/v1/content-writing/pieces/{pid}", "0_piece_before")
        orig = _j(body).get("content_text")
        ok = st == 200 and isinstance(orig, str) and orig.strip() != ""
        r.add("0", "precondition: A has a ready piece with content", ok,
              f"piece={pid} status={st} len={len(orig or '')} sha={_sha(orig)}")
        if not ok:
            return r.res
    if pid is None or not isinstance(orig, str):
        return r.res
    probe = orig + PROBE_SUFFIX
    try:
        with r.guard("1", "A PATCH own piece -> 200, tenant-safe shape"):
            st, body = r.call(A, "PATCH", f"/v1/content-writing/pieces/{pid}", "1_patch_probe",
                              json={"content_text": probe})
            b = _j(body)
            r.add("1", "A PATCH own piece -> 200, tenant-safe shape",
                  st == 200 and b.get("piece_id") == pid and b.get("ready_state") == "ready"
                  and b.get("content_text") == probe and "status" not in b,
                  f"status={st} ready_state={b.get('ready_state')} text_is_probe={b.get('content_text') == probe} "
                  f"has_status_key={'status' in b}")
        with r.guard("2", "A GET reads the probe text back"):
            st, body = r.call(A, "GET", f"/v1/content-writing/pieces/{pid}", "2_get_probe")
            r.add("2", "A GET reads the probe text back", st == 200 and _j(body).get("content_text") == probe,
                  f"status={st}")
        with r.guard("3", "B PATCH A's piece -> 404, A's text unchanged"):
            st, body = r.call(B, "PATCH", f"/v1/content-writing/pieces/{pid}", "3_patch_foreign",
                              json={"content_text": "[AA-859 W2 foreign probe]"})
            st2, body2 = r.call(A, "GET", f"/v1/content-writing/pieces/{pid}", "3_get_after_foreign")
            r.add("3", "B PATCH A's piece -> 404, A's text unchanged",
                  st == 404 and st2 == 200 and _j(body2).get("content_text") == probe,
                  f"foreign_status={st} detail={str(_j(body).get('detail'))[:80]!r} a_get={st2}")
        with r.guard("4", "A PATCH random uuid -> 404"):
            rnd = str(uuid.uuid4())
            st, _ = r.call(A, "PATCH", f"/v1/content-writing/pieces/{rnd}", "4_patch_random",
                           json={"content_text": "x"})
            r.add("4", "A PATCH random uuid -> 404", st == 404, f"status={st} id={rnd[:8]}")
    finally:
        with r.guard("R", "restore: original text back, sha256 equal"):
            st, _ = r.call(A, "PATCH", f"/v1/content-writing/pieces/{pid}", "R_patch_restore",
                           json={"content_text": orig})
            st2, body2 = r.call(A, "GET", f"/v1/content-writing/pieces/{pid}", "R_get_restored")
            now_text = _j(body2).get("content_text")
            r.add("R", "restore: original text back, sha256 equal", st == 200 and st2 == 200 and now_text == orig,
                  f"patch={st} get={st2} sha_before={_sha(orig)} sha_after={_sha(now_text)} "
                  f"(2 content_piece.edited audit rows: probe + restore)")
    return r.res


# ── W6 t2_version_write ──────────────────────────────────────────────────────────────────────────
def _all_my_versions(r, slug, tag, max_pages=5):
    """Every version of `slug` (up to max_pages x 100). Returns (status, rows, total)."""
    rows, total, st = [], None, None
    for page in range(1, max_pages + 1):
        st, body = r.call(slug, "GET", f"/v1/tours/my-versions?page_size=100&page={page}", f"{tag}_p{page}")
        if st != 200:
            return st, rows, total
        b = _j(body)
        total = (b.get("pagination") or {}).get("total")
        data = b.get("data") or []
        rows.extend(data)
        if not data or (total is not None and len(rows) >= total):
            break
    return st, rows, total


def _content_dict(v):
    c = v.get("rewritten_content")
    if isinstance(c, str):
        try:
            c = json.loads(c)
        except ValueError:
            return None
    return c if isinstance(c, dict) and c else None


def check_t2_version_write(ctx):
    r = _Run(ctx, "VW.")
    A, B = ctx.A, ctx.B
    V = content = None
    history = []
    with r.guard("0", "precondition: A has an approved version on a tour with no pending version"):
        st, rows, total = _all_my_versions(r, A, "0_my_versions_a")
        approved = [v for v in rows if v.get("status") == "approved" and _content_dict(v)]
        for v in approved[:10]:
            st2, body2 = r.call(A, "GET", f"/v1/tours/versions/{v['id']}", f"0_version_{str(v['id'])[:8]}")
            hist = _j(body2).get("version_history") or []
            if st2 == 200 and not any(h.get("status") == "pending" for h in hist):
                V, content, history = str(v["id"]), _content_dict(v), hist
                break
        if V is None:
            r.add("0", "precondition: A has an approved version on a tour with no pending version", False,
                  f"my-versions status={st} total={total} approved_with_content={len(approved)} — none usable; "
                  "status can only be restored to approved, so nothing safe to flip")
            return r.res
        r.add("0", "precondition: A has an approved version on a tour with no pending version", True,
              f"V={V} history={len(history)}")
    if V is None:
        return r.res
    max_num = max((h.get("version_number") or 0) for h in history) if history else 0
    approved_nums = [h.get("version_number") or 0 for h in history if h.get("status") == "approved"]
    v_num = next((h.get("version_number") for h in history if str(h.get("id")) == V), None)
    v_is_newest_approved = v_num is not None and v_num == max(approved_nums or [0])
    new_id = None
    new_final = None
    try:
        with r.guard("1", "A reject then approve V -> 200 rejected / approved"):
            st1, b1 = r.call(A, "PATCH", f"/v1/tours/versions/{V}", "1_reject", json={"action": "reject"})
            st2, b2 = r.call(A, "PATCH", f"/v1/tours/versions/{V}", "1_approve", json={"action": "approve"})
            r.add("1", "A reject then approve V -> 200 rejected / approved",
                  st1 == 200 and _j(b1).get("status") == "rejected" and _j(b1).get("version_id") == V
                  and st2 == 200 and _j(b2).get("status") == "approved",
                  f"reject={st1}/{_j(b1).get('status')} approve={st2}/{_j(b2).get('status')} (edited_at moved)")
        with r.guard("2", "A edit with empty content -> 400, nothing written"):
            st, body = r.call(A, "PATCH", f"/v1/tours/versions/{V}", "2_edit_empty",
                              json={"action": "edit", "edited_content": {}})
            r.add("2", "A edit with empty content -> 400, nothing written", st == 400,
                  f"status={st} detail={str(_j(body).get('detail'))[:60]!r}")
        with r.guard("3", "A edit V with its own content -> 200 edited, version_number = max + 1"):
            st, body = r.call(A, "PATCH", f"/v1/tours/versions/{V}", "3_edit",
                              json={"action": "edit", "edited_content": content, "edited_by": "aa859-verify"})
            b = _j(body)
            new_id = b.get("new_version_id") if st == 200 else None
            r.add("3", "A edit V with its own content -> 200 edited, version_number = max + 1",
                  st == 200 and b.get("status") == "edited" and new_id and b.get("version_number") == max_num + 1,
                  f"status={st} new_version_id={new_id} version_number={b.get('version_number')} "
                  f"expected={max_num + 1}")
        if new_id:
            new_final = "approve" if v_is_newest_approved else "reject"
            with r.guard("4", f"A {new_final} the new version N -> 200 (no pending row left)"):
                st, body = r.call(A, "PATCH", f"/v1/tours/versions/{new_id}", "4_resolve_new",
                                  json={"action": new_final})
                ok = st == 200 and _j(body).get("status") == ("approved" if new_final == "approve" else "rejected")
                if ok:
                    new_final = "done:" + new_final
                r.add("4", f"A {new_final.split(':')[-1]} the new version N -> 200 (no pending row left)", ok,
                      f"N={new_id} status={st}/{_j(body).get('status')} V_newest_approved={v_is_newest_approved} "
                      "(N stays as a tenant_edit row)")
        for i, payload in enumerate([{"action": "reject"}, {"action": "approve"},
                                     {"action": "edit", "edited_content": {"name": "x"}}]):
            with r.guard(f"5.{i}", f"B {payload['action']} on A's V -> 404"):
                st, body = r.call(B, "PATCH", f"/v1/tours/versions/{V}", f"5_{i}_foreign_{payload['action']}",
                                  json=payload)
                r.add(f"5.{i}", f"B {payload['action']} on A's V -> 404", st == 404,
                      f"status={st} detail={str(_j(body).get('detail'))[:40]!r}")
        with r.guard("6", "A PATCH a random uuid -> 404"):
            rnd = str(uuid.uuid4())
            st, _ = r.call(A, "PATCH", f"/v1/tours/versions/{rnd}", "6_random", json={"action": "approve"})
            r.add("6", "A PATCH a random uuid -> 404", st == 404, f"status={st} id={rnd[:8]}")
        with r.guard("7", "A GET V: still approved, history has N and nothing from B"):
            st, body = r.call(A, "GET", f"/v1/tours/versions/{V}", "7_get_v")
            b = _j(body)
            hist = b.get("version_history") or []
            extra = [h for h in hist if str(h.get("id")) not in {str(x.get("id")) for x in history}
                     and str(h.get("id")) != str(new_id)]
            r.add("7", "A GET V: still approved, history has N and nothing from B",
                  st == 200 and b.get("status") == "approved" and not extra
                  and (not new_id or any(str(h.get("id")) == str(new_id) for h in hist)),
                  f"status={st} v_status={b.get('status')} history={len(hist)} unexpected_new={len(extra)}")
    finally:
        with r.guard("R", "restore: V approved, N not pending"):
            notes = []
            if new_id and not str(new_final).startswith("done:"):
                act = "approve" if v_is_newest_approved else "reject"
                st, _ = r.call(A, "PATCH", f"/v1/tours/versions/{new_id}", "R_resolve_new", json={"action": act})
                notes.append(f"N {act}={st}")
            st, body = r.call(A, "GET", f"/v1/tours/versions/{V}", "R_get_v")
            if _j(body).get("status") != "approved":
                st2, _ = r.call(A, "PATCH", f"/v1/tours/versions/{V}", "R_approve_v", json={"action": "approve"})
                notes.append(f"V approve={st2}")
                st, body = r.call(A, "GET", f"/v1/tours/versions/{V}", "R_get_v2")
            hist = _j(body).get("version_history") or []
            n_status = next((h.get("status") for h in hist if str(h.get("id")) == str(new_id)), None)
            r.add("R", "restore: V approved, N not pending",
                  st == 200 and _j(body).get("status") == "approved" and n_status != "pending",
                  f"V={V} status={_j(body).get('status')} N={new_id} N_status={n_status} {' '.join(notes)} "
                  "(N kept: new tenant_edit row; edited_at of V moved)")
    return r.res


# ── W3 angle_gate_decide ─────────────────────────────────────────────────────────────────────────
def _chosen(req):
    return [a.get("idx") for a in (req.get("angles") or []) if a.get("chosen")]


def _option_sig(req):
    return [(a.get("option_id"), a.get("idx")) for a in (req.get("angles") or [])]


def check_angle_gate_decide(ctx):
    r = _Run(ctx, "AG.")
    A, B = ctx.A, ctx.B
    rid = base = None
    idx0 = idx1 = None
    with r.guard("0", "precondition: A has an approved request with >= 2 angles, one chosen"):
        st, body = r.call(A, "GET", "/v1/content-writing/reviews", "0_reviews_a")
        rids = []
        for d in _j(body).get("data") or []:
            if d.get("request_id") and d["request_id"] not in rids:
                rids.append(d["request_id"])
        for i, cand in enumerate(rids[:15]):
            st2, b2 = r.call(A, "GET", f"/v1/angle-gate/requests/{cand}", f"0_req_{i}")
            b2 = _j(b2)
            ch = _chosen(b2)
            if st2 == 200 and b2.get("status") == "approved" and len(b2.get("angles") or []) >= 2 and len(ch) == 1:
                rid, base, idx0 = cand, b2, ch[0]
                idx1 = next(a.get("idx") for a in b2["angles"] if a.get("idx") != idx0)
                break
        if rid is None:
            r.add("0", "precondition: A has an approved request with >= 2 angles, one chosen", False,
                  f"reviews status={st} requests_checked={min(len(rids), 15)} — no approved request with "
                  "a single chosen angle and a second angle to switch to")
            return r.res
        r.add("0", "precondition: A has an approved request with >= 2 angles, one chosen", True,
              f"request={rid} IDX0={idx0} IDX1={idx1} angles={len(base['angles'])}")
    if rid is None:
        return r.res
    base_path = f"/v1/angle-gate/requests/{rid}"
    try:
        with r.guard("1", "B reopen A's approved request -> 404"):
            st, body = r.call(B, "POST", f"{base_path}/reopen", "1_foreign_reopen")
            r.add("1", "B reopen A's approved request -> 404", st == 404, f"status={st}")
        with r.guard("2", "A reopen -> 200 reusable"):
            st, body = r.call(A, "POST", f"{base_path}/reopen", "2_reopen")
            r.add("2", "A reopen -> 200 reusable", st == 200 and _j(body).get("status") == "reusable",
                  f"status={st} req_status={_j(body).get('status')}")
        with r.guard("3", "A reopen again -> 409"):
            st, body = r.call(A, "POST", f"{base_path}/reopen", "3_reopen_again")
            r.add("3", "A reopen again -> 409", st == 409, f"status={st}")
        with r.guard("4", "B choose on A's reusable request -> 404"):
            st, body = r.call(B, "POST", f"{base_path}/choose", "4_foreign_choose", json={"idx": idx1})
            r.add("4", "B choose on A's reusable request -> 404", st == 404, f"status={st}")
        with r.guard("5", "A choose IDX1 -> 200 approved, only IDX1 chosen"):
            st, body = r.call(A, "POST", f"{base_path}/choose", "5_choose_idx1", json={"idx": idx1})
            b = _j(body)
            r.add("5", "A choose IDX1 -> 200 approved, only IDX1 chosen",
                  st == 200 and b.get("status") == "approved" and _chosen(b) == [idx1],
                  f"status={st} req_status={b.get('status')} chosen={_chosen(b)}")
        with r.guard("6", "A choose IDX1 again -> 409"):
            st, body = r.call(A, "POST", f"{base_path}/choose", "6_choose_again", json={"idx": idx1})
            r.add("6", "A choose IDX1 again -> 409", st == 409, f"status={st}")
        with r.guard("7", "A reopen / choose on a random uuid -> 404"):
            rnd = str(uuid.uuid4())
            st1, _ = r.call(A, "POST", f"/v1/angle-gate/requests/{rnd}/reopen", "7_random_reopen")
            st2, _ = r.call(A, "POST", f"/v1/angle-gate/requests/{rnd}/choose", "7_random_choose", json={"idx": 0})
            r.add("7", "A reopen / choose on a random uuid -> 404", st1 == 404 and st2 == 404,
                  f"reopen={st1} choose={st2} id={rnd[:8]}")
    finally:
        with r.guard("R", "restore: approved, chosen IDX0, same option ids"):
            notes = []
            st, body = r.call(A, "GET", base_path, "R_get_before_restore")
            cur = _j(body)
            if cur.get("status") == "approved" and _chosen(cur) != [idx0]:
                s, _ = r.call(A, "POST", f"{base_path}/reopen", "R_reopen")
                notes.append(f"reopen={s}")
                st, body = r.call(A, "GET", base_path, "R_get_mid")
                cur = _j(body)
            if cur.get("status") in ("reusable", "pending_choice"):
                s, _ = r.call(A, "POST", f"{base_path}/choose", "R_choose_idx0", json={"idx": idx0})
                notes.append(f"choose_idx0={s}")
            st, body = r.call(A, "GET", base_path, "R_get_final")
            fin = _j(body)
            r.add("R", "restore: approved, chosen IDX0, same option ids",
                  st == 200 and fin.get("status") == "approved" and _chosen(fin) == [idx0]
                  and _option_sig(fin) == _option_sig(base),
                  f"status={fin.get('status')} chosen={_chosen(fin)} IDX0={idx0} "
                  f"options_same={_option_sig(fin) == _option_sig(base)} {' '.join(notes)} (updated_at moved)")
    return r.res


# ── W4 unpublish ─────────────────────────────────────────────────────────────────────────────────
def _wp_post(wp, method, external_id, params):
    """Direct call to the E2E WordPress test site (app password, Basic auth). Returns (status, json)."""
    url = wp["site_url"].rstrip("/") + f"/wp-json/wp/v2/posts/{external_id}"
    resp = requests.request(method, url, params=params, auth=(wp["app_user"], wp["app_password"]), timeout=60)
    try:
        return resp.status_code, resp.json()
    except ValueError:
        return resp.status_code, {}


def _log_row(r, publish_id, name):
    st, body = r.call(r.ctx.A, "GET", "/v1/publish-log?limit=200", name)
    row = next((d for d in _j(body).get("data") or [] if d.get("publish_id") == publish_id), None)
    return st, row


def check_unpublish(ctx):
    r = _Run(ctx, "UP.")
    A, B = ctx.A, ctx.B
    tid_a = ctx.tid[A]
    wp = None
    we_connected = False
    wp_ready = False
    pid = publish_id = external_id = external_url = None
    with r.guard("0a", "precondition: A's WordPress = E2E test site (connect it if disconnected)"):
        wp = _secret_json(WP_SECRET)
        st, body = r.call(A, "GET", "/v1/integrations/wordpress", "0a_wp_status_before")
        b = _j(body)
        if st != 200:
            r.add("0a", "precondition: A's WordPress = E2E test site (connect it if disconnected)", False,
                  f"status={st}")
            return r.res
        if b.get("connected"):
            same = _host(b.get("site_url")) == _host(wp["site_url"])
            r.add("0a", "precondition: A's WordPress = E2E test site (connect it if disconnected)", same,
                  f"already connected, site_host={_host(b.get('site_url'))} e2e_host_match={same}")
            if not same:
                return r.res
            wp_ready = True
        else:
            st, body = r.call(A, "POST", "/v1/integrations/wordpress", "0a_wp_connect",
                              json={"wp_url": wp["site_url"], "username": wp["app_user"],
                                    "app_password": wp["app_password"]})
            we_connected = st == 200 and _j(body).get("connected") is True
            r.add("0a", "precondition: A's WordPress = E2E test site (connect it if disconnected)", we_connected,
                  f"was disconnected; connect status={st}")
            if not we_connected:
                return r.res
            wp_ready = True
    if not wp_ready:
        if we_connected:  # an error after connecting: put it back
            r.call(A, "DELETE", "/v1/integrations/wordpress", "R_wp_disconnect_early")
        return r.res
    try:
        with r.guard("0b", "precondition: A has a blog piece in /pending"):
            st, body = r.call(A, "GET", "/v1/publish-log/pending", "0b_pending_before")
            blogs = [d for d in _j(body).get("data") or [] if d.get("channel") == "blog"]
            if st == 200 and blogs:
                pid = blogs[-1]["piece_id"]   # the oldest pending blog piece
            r.add("0b", "precondition: A has a blog piece in /pending", bool(pid),
                  f"status={st} blog_pending={len(blogs)} piece={pid}" + ("" if pid else
                  " — no pending blog piece; not generating content (paid run)"))
        if not pid:
            return r.res
        with r.guard("1", "setup: A publishes the piece to the E2E WP site (MAIN route) -> 200 published"):
            st, body = r.call(A, "POST", f"/v1/publish-log/{pid}/publish", "1_publish")
            b = _j(body)
            if st == 200 and b.get("success") and b.get("status") == "published":
                publish_id, external_id, external_url = b.get("publish_id"), b.get("external_id"), b.get("external_url")
            r.add("1", "setup: A publishes the piece to the E2E WP site (MAIN route) -> 200 published",
                  bool(publish_id and external_id),
                  f"status={st} success={b.get('success')} publish_id={publish_id} external_id={external_id} "
                  f"detail={str(b.get('detail') or b.get('last_error') or '')[:80]!r} (1 of A's daily publishes used)")
        if not publish_id:
            return r.res
        with r.guard("2", "B DELETE A's publish_id -> 404, A's row still published"):
            st, body = r.call(B, "DELETE", f"/v1/publish-log/{publish_id}", "2_foreign_delete")
            st2, row = _log_row(r, publish_id, "2_log_after_foreign")
            r.add("2", "B DELETE A's publish_id -> 404, A's row still published",
                  st == 404 and st2 == 200 and row and row.get("status") == "published",
                  f"foreign={st} detail={str(_j(body).get('detail'))[:60]!r} a_row={row and row.get('status')}")
        with r.guard("3", "A DELETE own publish_id -> 200 unpublished, tenant:<A>, remote trashed"):
            st, body = r.call(A, "DELETE", f"/v1/publish-log/{publish_id}", "3_unpublish")
            b = _j(body)
            r.add("3", "A DELETE own publish_id -> 200 unpublished, tenant:<A>, remote trashed",
                  st == 200 and b.get("status") == "unpublished" and b.get("unpublished_by") == f"tenant:{tid_a}"
                  and b.get("remote") == "trashed" and b.get("publish_id") == publish_id,
                  f"status={st} row_status={b.get('status')} by_ok={b.get('unpublished_by') == f'tenant:{tid_a}'} "
                  f"remote={b.get('remote')} detail={str(b.get('detail') or '')[:80]!r}")
        with r.guard("4", "WP read-back: post status trash"):
            if _host(external_url) and _host(external_url) != _host(wp["site_url"]):
                r.add("4", "WP read-back: post status trash", False,
                      f"post host {_host(external_url)} is not the E2E site")
            else:
                st, body = _wp_post(wp, "GET", external_id, {"context": "edit"})
                r.save("4_wp_readback", {"at": _now(), "status": st, "post_id": external_id,
                                         "post_status": _j(body).get("status")})
                r.add("4", "WP read-back: post status trash", st == 200 and _j(body).get("status") == "trash",
                      f"wp_status={st} post_status={_j(body).get('status')}")
        with r.guard("5", "A DELETE again -> 404 (status guard)"):
            st, _ = r.call(A, "DELETE", f"/v1/publish-log/{publish_id}", "5_unpublish_again")
            r.add("5", "A DELETE again -> 404 (status guard)", st == 404, f"status={st}")
        with r.guard("6", "A DELETE random uuid -> 404"):
            rnd = str(uuid.uuid4())
            st, _ = r.call(A, "DELETE", f"/v1/publish-log/{rnd}", "6_random")
            r.add("6", "A DELETE random uuid -> 404", st == 404, f"status={st} id={rnd[:8]}")
        with r.guard("7", "publish-log shows unpublished; the piece is back in /pending"):
            st, row = _log_row(r, publish_id, "7_log_after")
            st2, body2 = r.call(A, "GET", "/v1/publish-log/pending", "7_pending_after")
            back = any(d.get("piece_id") == pid for d in _j(body2).get("data") or [])
            r.add("7", "publish-log shows unpublished; the piece is back in /pending",
                  st == 200 and row and row.get("status") == "unpublished" and back,
                  f"row={row and row.get('status')} piece_back_in_pending={back}")
    finally:
        with r.guard("R", "restore: no published row left, WP post deleted, WP integration as it started"):
            notes, ok = [], True
            still_published = False
            if publish_id:
                st, row = _log_row(r, publish_id, "R_log")
                if row and row.get("status") == "published":
                    s, b = r.call(A, "DELETE", f"/v1/publish-log/{publish_id}", "R_unpublish_retry")
                    notes.append(f"retry_unpublish={s}")
                    st, row = _log_row(r, publish_id, "R_log2")
                still_published = bool(row and row.get("status") == "published")
                if still_published:
                    ok = False
                    notes.append(f"publish_id {publish_id} STILL published: unpublish it as A after the flag is off")
            if external_id and wp and (not _host(external_url) or _host(external_url) == _host(wp["site_url"])):
                s, b = _wp_post(wp, "DELETE", external_id, {"force": "true"})
                deleted = s == 200 and _j(b).get("deleted") is True
                r.save("R_wp_force_delete", {"at": _now(), "status": s, "post_id": external_id, "deleted": deleted})
                notes.append(f"wp_force_delete={s} deleted={deleted}")
                ok = ok and deleted
            if we_connected:
                if still_published:
                    notes.append("WP left CONNECTED (a published row remains; disconnect after it is unpublished)")
                    ok = False
                else:
                    s, b = r.call(A, "DELETE", "/v1/integrations/wordpress", "R_wp_disconnect")
                    s2, b2 = r.call(A, "GET", "/v1/integrations/wordpress", "R_wp_status_after")
                    back = s == 200 and s2 == 200 and _j(b2).get("connected") is False
                    notes.append(f"wp_disconnect={s} connected_after={_j(b2).get('connected')}")
                    ok = ok and back
            r.add("R", "restore: no published row left, WP post deleted, WP integration as it started", ok,
                  " ".join(notes) or "nothing to restore")
    return r.res


# ── W5a t2_version_reads ─────────────────────────────────────────────────────────────────────────
def _t2_reads_snapshot(r, tag):
    """A's three read answers in a comparable form; raises on a non-200."""
    A = r.ctx.A
    st, rows, total = _all_my_versions(r, A, f"{tag}_my_versions")
    if st != 200:
        raise RuntimeError(f"my-versions status={st}")
    st, body = r.call(A, "GET", "/v1/tours/pool?page_size=20", f"{tag}_pool")
    if st != 200:
        raise RuntimeError(f"pool status={st}")
    pool = _j(body)
    v = next((x for x in rows if x.get("job_status")), rows[0] if rows else None)
    ver = None
    if v:
        st, body = r.call(A, "GET", f"/v1/tours/versions/{v['id']}", f"{tag}_version")
        if st != 200:
            raise RuntimeError(f"versions/{v['id']} status={st}")
        ver = _j(body)
    return {
        "at": _now(),
        "my_versions": {"total": total, "ids": sorted(str(x["id"]) for x in rows),
                        "job_status": {str(x["id"]): x.get("job_status") for x in rows},
                        "tours": sorted({str(x.get("published_tour_id")) for x in rows}),
                        "keys": sorted(rows[0].keys()) if rows else []},
        "pool": {"total": (pool.get("pagination") or {}).get("total"), "countries": pool.get("countries"),
                 "tenant_id": pool.get("tenant_id"), "keys": sorted(pool.keys()),
                 "row_keys": sorted((pool.get("data") or [{}])[0].keys()),
                 "rewritten": {str(p.get("id")): p.get("already_rewritten") for p in pool.get("data") or []},
                 "null_country": sum(1 for p in pool.get("data") or [] if p.get("country") is None)},
        "version": None if ver is None else {
            "id": str(ver.get("id")), "job_status": ver.get("job_status"), "status": ver.get("status"),
            "history_ids": sorted(str(h.get("id")) for h in ver.get("version_history") or []),
            "keys": sorted(ver.keys())},
    }


def check_t2_version_reads(ctx):
    r = _Run(ctx, "VR.")
    A, B = ctx.A, ctx.B
    snap = None
    with r.guard("1", "A my-versions / pool / versions/{V} -> 200 with the expected keys"):
        snap = _t2_reads_snapshot(r, "1")
        r.save("1_snapshot", snap)
        mv, pool, ver = snap["my_versions"], snap["pool"], snap["version"]
        if ver is None:
            r.add("1", "A my-versions / pool / versions/{V} -> 200 with the expected keys", False,
                  f"A has no tour version (my-versions total={mv['total']}) — cannot read versions/{{id}}")
            snap = None
        else:
            need_pool = {"data", "pagination", "countries", "tenant_id"}
            need_ver = {"id", "status", "job_status", "version_history", "rewritten_content", "published_tour_id"}
            ok = (need_pool <= set(pool["keys"]) and need_ver <= set(ver["keys"])
                  and (not mv["ids"] or {"id", "status", "job_status", "published_tour_id"} <= set(mv["keys"])))
            r.add("1", "A my-versions / pool / versions/{V} -> 200 with the expected keys", ok,
                  f"my_versions total={mv['total']} pool total={pool['total']} "
                  f"countries={len(pool['countries'] or [])} "
                  f"V={ver['id']} job_status={ver['job_status']} missing_ver={sorted(need_ver - set(ver['keys']))}")
    if snap is None:
        return r.res
    mv, pool, ver = snap["my_versions"], snap["pool"], snap["version"]
    complete = mv["total"] is not None and len(mv["ids"]) >= mv["total"]
    with r.guard("2", "consistency: V's job_status list = detail, history ids are A's, pool tenant_id = A"):
        hist_ok = set(ver["history_ids"]) <= set(mv["ids"]) if complete else True
        r.add("2", "consistency: V's job_status list = detail, history ids are A's, pool tenant_id = A",
              mv["job_status"].get(ver["id"]) == ver["job_status"] and hist_ok and pool["tenant_id"] == ctx.tid[A],
              f"list_job={mv['job_status'].get(ver['id'])} detail_job={ver['job_status']} "
              f"history_in_list={hist_ok} (list complete={complete}) pool_tenant_ok={pool['tenant_id'] == ctx.tid[A]}")
    with r.guard("3", "pool already_rewritten matches A's own tours"):
        tours = set(mv["tours"])
        wrong = [pid for pid, rw in pool["rewritten"].items() if bool(rw) != (pid in tours)] if complete else \
            [pid for pid, rw in pool["rewritten"].items() if pid in tours and not rw]
        r.add("3", "pool already_rewritten matches A's own tours", not wrong,
              f"pool_rows={len(pool['rewritten'])} rewritten={sum(1 for v in pool['rewritten'].values() if v)} "
              f"mismatch={len(wrong)} null_country_rows={pool['null_country']}")
    with r.guard("4", "B GET A's versions/{V} -> 404"):
        st, body = r.call(B, "GET", f"/v1/tours/versions/{ver['id']}", "4_foreign_version")
        r.add("4", "B GET A's versions/{V} -> 404", st == 404, f"status={st}")
    with r.guard("5", "B my-versions holds none of A's ids"):
        st, rows_b, total_b = _all_my_versions(r, B, "5_my_versions_b")
        leak = set(str(x["id"]) for x in rows_b) & set(mv["ids"])
        r.add("5", "B my-versions holds none of A's ids", st == 200 and not leak,
              f"status={st} b_total={total_b} overlap={len(leak)}")
    with r.guard("6", "A GET versions/{random uuid} -> 404"):
        rnd = str(uuid.uuid4())
        st, _ = r.call(A, "GET", f"/v1/tours/versions/{rnd}", "6_random")
        r.add("6", "A GET versions/{random uuid} -> 404", st == 404, f"status={st} id={rnd[:8]}")
    with r.guard("7", "flag-on answers match the flag-off baseline"):
        if not T2_READS_BASELINE.exists():
            r.add("7", "flag-on answers match the flag-off baseline", True,
                  "no baseline file (run `aa859_flip_checks.py baseline-t2-reads` with the flag off to compare); "
                  "consistency checks only")
        else:
            base = json.loads(T2_READS_BASELINE.read_text())
            diffs = []
            if base["pool"]["total"] != pool["total"]:
                diffs.append(f"pool total {base['pool']['total']}->{pool['total']}")
            if base["pool"]["countries"] != pool["countries"]:
                diffs.append("pool countries differ")
            if base["pool"]["null_country"] != pool["null_country"]:
                diffs.append(f"pool null_country {base['pool']['null_country']}->{pool['null_country']}")
            common = set(base["pool"]["rewritten"]) & set(pool["rewritten"])
            if any(base["pool"]["rewritten"][k] != pool["rewritten"][k] for k in common):
                diffs.append("already_rewritten differs")
            if not set(base["my_versions"]["ids"]) <= set(mv["ids"]):
                diffs.append("baseline my-versions ids missing now")
            if set(base["my_versions"]["keys"]) != set(mv["keys"]) or set(base["pool"]["keys"]) != set(pool["keys"]):
                diffs.append("response keys differ")
            bv = base.get("version") or {}
            if bv.get("id") == ver["id"]:
                if bv.get("job_status") != ver["job_status"]:
                    diffs.append(f"V job_status {bv.get('job_status')}->{ver['job_status']}")
                if not set(bv.get("history_ids") or []) <= set(ver["history_ids"]):
                    diffs.append("V history ids missing now")
                if set(bv.get("keys") or []) != set(ver["keys"]):
                    diffs.append("V keys differ")
            r.add("7", "flag-on answers match the flag-off baseline", not diffs,
                  f"baseline_at={base.get('at')} " + ("; ".join(diffs) or "same (new versions since allowed)"))
    return r.res


# ── W9 integration_connect ───────────────────────────────────────────────────────────────────────
_WP_STATUS_KEYS = {"connected", "site_url", "connected_at", "last_verified_at", "last_verify_error"}
_FB_STATUS_KEYS = {"connected", "page_id", "connected_at", "last_verified_at", "last_verify_error"}


def check_integration_connect(ctx):
    r = _Run(ctx, "IC.")
    A, B = ctx.A, ctx.B
    tid_a = ctx.tid[A]
    before = {}
    creds = None
    a_was_connected = None
    connected_now = False
    prev_verified = None
    with r.guard("0", "status as A and B (WordPress + Facebook) -> 200 with the status shape"):
        parts, ok = [], True
        for slug in (A, B):
            for kind, keys in (("wordpress", _WP_STATUS_KEYS), ("facebook", _FB_STATUS_KEYS)):
                st, body = r.call(slug, "GET", f"/v1/integrations/{kind}", f"0_{kind}_{slug}")
                before[(slug, kind)] = _j(body)
                ok = ok and st == 200 and keys <= set(_j(body).keys())
                parts.append(f"{slug[:5]}/{kind[:2]}={st}:{_j(body).get('connected')}")
        r.add("0", "status as A and B (WordPress + Facebook) -> 200 with the status shape", ok, " ".join(parts))
        if not ok:
            return r.res
    if len(before) < 4:
        return r.res
    a_wp = before[(A, "wordpress")]
    a_was_connected = bool(a_wp.get("connected"))
    with r.guard("1", "precondition: creds to re-post without changing A's connection"):
        e2e = _secret_json(WP_SECRET)
        e2e_creds = {"wp_url": e2e["site_url"], "username": e2e["app_user"], "app_password": e2e["app_password"]}
        if not a_was_connected:
            creds, src = e2e_creds, "E2E test site (A was disconnected)"
        else:
            try:
                stored = _secret_json(f"acp/cms/{tid_a}")
            except Exception:  # noqa: BLE001 — unreadable: fall back below
                stored = {}
            if stored.get("wp_url") and stored.get("username") and stored.get("app_password"):
                creds = {k: stored[k] for k in ("wp_url", "username", "app_password")}
                src = "A's stored creds (re-posted unchanged)"
            elif _host(a_wp.get("site_url")) == _host(e2e["site_url"]):
                creds, src = e2e_creds, "E2E test site creds (A connected to that site, stored creds unreadable)"
            else:
                src = "none: A is connected elsewhere and its stored creds are unreadable; not changing them"
        r.add("1", "precondition: creds to re-post without changing A's connection", creds is not None, src)
    try:
        if creds is not None:
            with r.guard("2", "A POST connect -> 200 connected, site_url as expected"):
                st, body = r.call(A, "POST", "/v1/integrations/wordpress", "2_connect", json=creds)
                b = _j(body)
                connected_now = st == 200 and b.get("connected") is True
                ok = connected_now and _host(b.get("site_url")) == _host(creds["wp_url"])
                if a_was_connected:
                    ok = ok and b.get("connected_at") == a_wp.get("connected_at")
                r.add("2", "A POST connect -> 200 connected, site_url as expected", ok,
                      f"status={st} site_host_ok={_host(b.get('site_url')) == _host(creds['wp_url'])} "
                      f"was_connected={a_was_connected} connected_at_unchanged="
                      f"{b.get('connected_at') == a_wp.get('connected_at') if a_was_connected else 'n/a (new row)'}")
            with r.guard("3", "A GET status after connect -> connected, same site"):
                st, body = r.call(A, "GET", "/v1/integrations/wordpress", "3_status_after_connect")
                b = _j(body)
                r.add("3", "A GET status after connect -> connected, same site",
                      st == 200 and b.get("connected") is True and _host(b.get("site_url")) == _host(creds["wp_url"]),
                      f"status={st} connected={b.get('connected')}")
                prev_verified = b.get("last_verified_at")
            with r.guard("4", "A POST test -> 200 success, last_verified_at moved"):
                st, body = r.call(A, "POST", "/v1/integrations/wordpress/test", "4_test")
                b = _j(body)
                moved = bool(b.get("last_verified_at")) and b.get("last_verified_at") != prev_verified
                r.add("4", "A POST test -> 200 success, last_verified_at moved",
                      st == 200 and b.get("success") is True and moved,
                      f"status={st} success={b.get('success')} verified_moved={moved} "
                      f"error={str(b.get('last_verify_error') or '')[:60]!r}")
        with r.guard("5", "B's WordPress / Facebook status unchanged by A's writes"):
            same = []
            for kind in ("wordpress", "facebook"):
                st, body = r.call(B, "GET", f"/v1/integrations/{kind}", f"5_{kind}_b_after")
                same.append(st == 200 and _j(body) == before[(B, kind)])
            r.add("5", "B's WordPress / Facebook status unchanged by A's writes", all(same), f"same={same}")
        with r.guard("6", "B POST test -> 404 when B has no WordPress connection"):
            if before[(B, "wordpress")].get("connected"):
                r.add("6", "B POST test -> 404 when B has no WordPress connection", True,
                      "skipped: B has its own WordPress connection (a test would change B's verify state)")
            else:
                st, body = r.call(B, "POST", "/v1/integrations/wordpress/test", "6_test_b")
                r.add("6", "B POST test -> 404 when B has no WordPress connection", st == 404,
                      f"status={st} detail={str(_j(body).get('detail'))[:50]!r}")
    finally:
        with r.guard("R", "restore: A's WordPress connection as it started"):
            if a_was_connected is None:
                r.add("R", "restore: A's WordPress connection as it started", True, "nothing changed")
            elif a_was_connected:
                st, body = r.call(A, "GET", "/v1/integrations/wordpress", "R_status")
                b = _j(body)
                r.add("R", "restore: A's WordPress connection as it started",
                      st == 200 and b.get("connected") is True and b.get("site_url") == a_wp.get("site_url")
                      and b.get("connected_at") == a_wp.get("connected_at"),
                      f"still connected={b.get('connected')} same_site={b.get('site_url') == a_wp.get('site_url')} "
                      "(same creds re-posted; updated_at / last_verified_at moved)")
            else:
                notes = []
                st, body = r.call(A, "GET", "/v1/integrations/wordpress", "R_status_pre")
                if _j(body).get("connected"):
                    s, _ = r.call(A, "DELETE", "/v1/integrations/wordpress", "R_disconnect")
                    notes.append(f"disconnect={s}")
                st, body = r.call(A, "GET", "/v1/integrations/wordpress", "R_status")
                r.add("R", "restore: A's WordPress connection as it started",
                      st == 200 and _j(body).get("connected") is False,
                      f"connected_after={_j(body).get('connected')} {' '.join(notes)}")
    return r.res


# ── registration ─────────────────────────────────────────────────────────────────────────────────
def register(CHECKS, LOG_EVENTS):
    _REG["checks"] = CHECKS
    CHECKS.update({
        "piece_edit": check_piece_edit,
        "t2_version_write": check_t2_version_write,
        "angle_gate_decide": check_angle_gate_decide,
        "unpublish": check_unpublish,
        "t2_version_reads": check_t2_version_reads,
        "integration_connect": check_integration_connect,
    })
    LOG_EVENTS.update({
        "piece_edit": ["aa859_piece_edit"],
        "t2_version_write": ["aa859_t2_version_write"],
        "angle_gate_decide": ["aa859_angle_gate_choose", "aa859_angle_gate_reopen"],
        "unpublish": ["aa859_unpublish", "tenant_self_unpublish"],
        "t2_version_reads": ["aa859_t2_version_read"],
        "integration_connect": ["aa859_integration_status", "aa859_integration_connect", "aa859_integration_test"],
    })


def _baseline_t2_reads():
    """Flag-OFF baseline for check 7 of t2_version_reads. Refuses when the flag is on."""
    sys.path.insert(0, str(HERE))
    import aa859_flip_verify as fv
    key = fv.FLAGS["t2_version_reads"]
    _REG["checks"] = fv.CHECKS
    val = fv.flag("get", [key])["after"][key]
    if str(val).strip('"').lower() in ("true", "1"):
        sys.exit(f"{key} is ON ({val!r}); the baseline must be taken with the flag off")
    ctx = fv.Ctx("t2_version_reads_baseline")
    snap = _t2_reads_snapshot(_Run(ctx, "BASE."), "base")
    snap["flag_value"] = val
    T2_READS_BASELINE.write_text(json.dumps(snap, indent=1, default=str))
    print(f"baseline written: {T2_READS_BASELINE} (my_versions={snap['my_versions']['total']}, "
          f"pool={snap['pool']['total']}, V={(snap['version'] or {}).get('id')})")


if __name__ == "__main__":
    if sys.argv[1:] == ["baseline-t2-reads"]:
        _baseline_t2_reads()
    else:
        print(__doc__)
