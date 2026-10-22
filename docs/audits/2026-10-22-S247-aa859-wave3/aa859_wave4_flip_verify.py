"""AA-859 S247 wave 4 — automated flip-verify-revert for the six wave-4 tenant-pool flags, extended from
aa859_wave3_flip_verify.py (same ritual, same fixed log check: the JSON form `"used_tenant_pool": true` is counted and
the log window starts AFTER the flag is set). NOT RUN by the lane that wrote it.

    python3 aa859_wave4_flip_verify.py <flag-short-name> [...]      e.g. slate_reads angle_gate_read
    python3 aa859_wave4_flip_verify.py --off <flag-short-name> ...  explicit OFF (rollback; NOT DEL, S241 D-12)
    python3 aa859_wave4_flip_verify.py --get <flag-short-name> ...

Ritual per flag: baseline with the flag OFF -> SET "true" -> checks as tenant A / B through the public Dev API ->
Logs Insights: >= 1 used_tenant_pool=True line and 0 False lines for the flag's events, aa859_tenant_pool_timing p95
wait_ms < 50 for the flag and no aa817_tenant_pool_unavailable for it -> keep ON if every check passed, else SET
"false". A = terra-family (the writes), B = atlas-hearth (foreign tenant). Ids are discovered through list endpoints;
a missing precondition is one failing check that says what is missing (no invented data, no paid generation).

Preconditions the orchestrator owns (not checked here):
  - the wave-4 build is deployed (api AND worker, rollout COMPLETED), all six keys were SET "false" before it;
  - 265 applied before slate_reads / angle_gate_read (aa859_w4_preflight.py post-265 -> post_265_ok);
  - 266 applied before marketplace / reviews / trip_reallocation / subject_decide (post-266 -> post_266_ok);
  - flip order: slate_reads, angle_gate_read, then marketplace, reviews, trip_reallocation, subject_decide.

Flags (api/core/aa544_tenant_pool.py) and what each check does:

slate_reads (aa859:slate_reads_pool) — GET /v1/slate; log aa859_slate_read. Baseline: A's and B's subject ids per
  Channel and unmatched_markets. Checks: A's answer equals the baseline (subject ids, states, unmatched_markets,
  posts_per_week); B's answer holds none of A's subject ids; POST /v1/slate/refresh as A -> 202 (stays on MAIN).
angle_gate_read (aa859:angle_gate_read_pool) — GET /v1/angle-gate/requests/{id} and the choose / reopen re-read; logs
  aa859_angle_gate_read, aa859_angle_gate_reread. Baseline: A's first request (from the review list) and, if there is
  one, A's first approved request with a chosen angle. Checks: A's GET equals the baseline (hash without updated_at);
  B GET A's request -> 404; A GET a random uuid -> 404; reopen then choose the SAME idx on the approved request
  -> 200 / 200 and status back to approved with the same chosen angle (the request's updated_at moves, nothing else).
reviews (aa859:reviews_pool) — GET /v1/content-writing/reviews, /requests/{id}/review; logs aa859_reviews_list,
  aa859_review_detail. Checks: A's list and first detail equal the baseline; B detail of A's request -> 404; B's list
  holds none of A's request ids. (The review responses carry no trip_url: the master trip page is checked by the CI
  LATERAL test, not here.)
marketplace (aa859:marketplace_pool) — GET /v1/marketplace; log aa859_marketplace_read. Checks: A's and B's
  total_atoms, total_tours and tours equal the baseline.
trip_reallocation (aa859:trip_reallocation_pool) — GET .../suggest, POST .../confirm; logs
  aa859_trip_reallocation_suggest, aa859_trip_reallocation_confirm. Checks (next quarter): A's suggestion equals the
  baseline (added / removed / unchanged / has_existing_plan); confirm with accept=false -> 200 accepted false (audit
  row only). accept=true is covered in CI (test_aa859_wave4_pool_routes), not run live: say so in the report.
subject_decide (aa859:subject_decide_pool) — POST /v1/subjects/{id}/pick, /cut; logs aa859_subject_pick,
  aa859_subject_cut. Needs three 'proposed' Subjects of A. IRREVERSIBLE: the picked Subject stays 'picked' (with its
  new angle_gate_request) and the cut ones stay 'cut' until the next Slate proposal. Checks: B pick / cut A's
  Subject -> 404; A pick #1 -> 200 with a request id; A pick #1 again -> 409; A cut #2 -> 200 cut; a concurrent pick
  and cut of #3 -> one 200 and one 409.

Secrets (tenant api keys) are read at run time and never printed or saved.
Output: flip_raw_s247w4/<flag>/*.json, flip_report_s247w4.json (appended per run), next to this file.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

API = "https://api-cis.lumiguides.it.com"
HERE = pathlib.Path(__file__).resolve().parent
PROFILE = ["--profile", "aa365-admin", "--region", "us-west-1"]
BUCKET = "aa-cis-bronze-005097885195"
FLAG_TOOL = HERE / "aa859_wave4_flag.py"
FLAG_TOOL_KEY = "scripts/s247_aa859_wave4_flag.py"
FLAG_OUT_KEY = "scripts/out/s247_aa859_wave4_flag.json"
TENANTS = ["terra-family", "atlas-hearth"]          # A does the writes, B is the foreign tenant
FLAGS = {
    "slate_reads": "aa859:slate_reads_pool",
    "angle_gate_read": "aa859:angle_gate_read_pool",
    "reviews": "aa859:reviews_pool",
    "marketplace": "aa859:marketplace_pool",
    "trip_reallocation": "aa859:trip_reallocation_pool",
    "subject_decide": "aa859:subject_decide_pool",
}
LOG_EVENTS = {
    "slate_reads": ["aa859_slate_read"],
    "angle_gate_read": ["aa859_angle_gate_read", "aa859_angle_gate_reread"],
    "reviews": ["aa859_reviews_list", "aa859_review_detail"],
    "marketplace": ["aa859_marketplace_read"],
    "trip_reallocation": ["aa859_trip_reallocation_suggest", "aa859_trip_reallocation_confirm"],
    "subject_decide": ["aa859_subject_pick", "aa859_subject_cut"],
}
WAIT_P95_MAX_MS = 50.0
OUT_DIR = HERE / "flip_raw_s247w4"
REPORT = HERE / "flip_report_s247w4.json"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def aws(*args, text=True):
    return subprocess.check_output(["aws", *args, *PROFILE], text=text).strip()


def secret(name):
    return aws("secretsmanager", "get-secret-value", "--secret-id", name, "--query", "SecretString", "--output", "text")


# ── Redis flags through ECS exec (S3-mediated) ───────────────────────────────────────────────────
def flag(action, keys):
    aws("s3", "cp", str(FLAG_TOOL), f"s3://{BUCKET}/{FLAG_TOOL_KEY}", "--quiet")
    out_uri = f"s3://{BUCKET}/{FLAG_OUT_KEY}"
    last = ""
    for _ in range(6):   # a task replaced by a deploy needs ~1 min before ECS exec works
        subprocess.run(["aws", "s3", "rm", out_uri, "--quiet", *PROFILE], capture_output=True)  # no stale result
        url = aws("s3", "presign", f"s3://{BUCKET}/{FLAG_TOOL_KEY}", "--expires-in", "300")
        task = aws("ecs", "list-tasks", "--cluster", "aa-cis-dev-cluster", "--service-name", "aa-cis-dev-api",
                   "--desired-status", "RUNNING", "--query", "taskArns[0]", "--output", "text")
        cmd = f"sh -c 'curl -s \"{url}\" -o /tmp/f.py && python3 /tmp/f.py {action} {' '.join(keys)}'"
        p = subprocess.run(["aws", "ecs", "execute-command", "--cluster", "aa-cis-dev-cluster", "--task", task,
                            "--container", "api", "--interactive", "--command", cmd, *PROFILE],
                           capture_output=True, text=True, timeout=120)
        got = subprocess.run(["aws", "s3", "cp", out_uri, "-", *PROFILE], capture_output=True, text=True)
        if p.returncode == 0 and got.returncode == 0 and got.stdout.strip():
            break
        last = (p.stderr or p.stdout)[-300:]
        time.sleep(20)
    else:
        raise RuntimeError(f"flag {action} {keys}: ECS exec failed 6 times: {last}")
    out = json.loads(got.stdout)
    if "error" in out or out.get("action") != action:
        raise RuntimeError(f"flag {action} failed: {out}")
    return out


# ── Logs Insights: used_tenant_pool per moved event ─────────────────────────────────────────────
def log_pool_lines(events, start_epoch, end_epoch):
    pattern = "|".join(events)
    q = (f"fields @message | filter @logStream like /^api\\// | filter @message like /{pattern}/ "
         f"| filter @message like /used_tenant_pool/ | limit 200")
    qid = aws("logs", "start-query", "--log-group-name", "/ecs/aa-cis-dev", "--start-time", str(start_epoch),
              "--end-time", str(end_epoch), "--query-string", q, "--query", "queryId", "--output", "text")
    while True:
        res = json.loads(aws("logs", "get-query-results", "--query-id", qid, "--output", "json"))
        if res["status"] in ("Complete", "Failed", "Cancelled", "Timeout"):
            break
        time.sleep(3)
    msgs = [next(c["value"] for c in r if c["field"] == "@message") for r in res.get("results", [])]
    # Since AA-871 (CIS #924) the api logs JSON lines ("used_tenant_pool": true); count the old text form too.
    def has(m, value):
        return f"used_tenant_pool={value}" in m or f'"used_tenant_pool": {str(value).lower()}' in m
    return {"true": sum(has(m, True) for m in msgs),
            "false": sum(has(m, False) for m in msgs), "sample": [m[:240] for m in msgs[:6]]}


# ── API context ──────────────────────────────────────────────────────────────────────────────────
class Ctx:
    def __init__(self, short):
        self.short = short
        self.out = OUT_DIR / short
        self.out.mkdir(parents=True, exist_ok=True)
        self.h, self.tid = {}, {}
        for slug in TENANTS:
            r = requests.post(API + "/auth/tenant-login",
                              json={"api_key": secret(f"aa-cis/dev/e2e-tenant/{slug}")}, timeout=30)
            r.raise_for_status()
            j = r.json()
            self.tid[slug], self.h[slug] = j["tenant_id"], {"Authorization": "Bearer " + j["token"]}
        self.A, self.B = TENANTS

    def raw(self, slug, method, path, **kw):
        return requests.request(method, API + path, headers=self.h[slug], timeout=120, **kw)

    def call(self, slug, method, path, name, **kw):
        r = self.raw(slug, method, path, **kw)
        try:
            body = r.json()
        except ValueError:
            body = r.text[:500]
        (self.out / f"{name}.json").write_text(json.dumps(
            {"at": now(), "tenant": slug, "method": method, "path": path, "status": r.status_code,
             "body": _trim(body)}, indent=1, default=str))
        return r.status_code, body


def _trim(o):
    if isinstance(o, dict):
        return {k: (v[:160] + "...") if isinstance(v, str) and len(v) > 160 else _trim(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_trim(x) for x in o[:15]]
    return o


def _j(body):
    return body if isinstance(body, dict) else {}


def _sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _host(url):
    h = (urlparse(url or "").hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


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


# ── Logs Insights: tenant-pool timing and unavailability for one flag ───────────────────────────
def _insights(q, start_epoch, end_epoch):
    qid = aws("logs", "start-query", "--log-group-name", "/ecs/aa-cis-dev", "--start-time", str(start_epoch),
              "--end-time", str(end_epoch), "--query-string", q, "--query", "queryId", "--output", "text")
    while True:
        res = json.loads(aws("logs", "get-query-results", "--query-id", qid, "--output", "json"))
        if res["status"] in ("Complete", "Failed", "Cancelled", "Timeout"):
            return [next(c["value"] for c in r if c["field"] == "@message") for r in res.get("results", [])]
        time.sleep(3)


_WAIT_RE = re.compile(r"wait_ms[\"']?\s*[:=]\s*([0-9.]+)")


def pool_health(flag_key, start_epoch, end_epoch):
    """p95 wait_ms of aa859_tenant_pool_timing for this flag (text or JSON lines) and the unavailable count."""
    timing = _insights("fields @message | filter @logStream like /^api\\// "
                       "| filter @message like /aa859_tenant_pool_timing/ "
                       f"| filter @message like /{flag_key}/ | limit 500", start_epoch, end_epoch)
    waits = sorted(float(m.group(1)) for m in (_WAIT_RE.search(x) for x in timing) if m)
    p95 = waits[min(len(waits) - 1, int(round(0.95 * (len(waits) - 1))))] if waits else None
    unavailable = _insights("fields @message | filter @logStream like /^api\\// "
                            "| filter @message like /aa817_tenant_pool_unavailable/ "
                            f"| filter @message like /{flag_key}/ | limit 50", start_epoch, end_epoch)
    return {"timing_lines": len(waits), "p95_wait_ms": p95, "unavailable": len(unavailable)}


def _no_volatile(obj):
    """The response without the fields that move on their own (timestamps of a reopen / choose)."""
    if isinstance(obj, dict):
        return {k: _no_volatile(v) for k, v in obj.items() if k not in ("updated_at", "refresh", "finished_at")}
    if isinstance(obj, list):
        return [_no_volatile(x) for x in obj]
    return obj


# ── slate_reads ──────────────────────────────────────────────────────────────────────────────────
def _slate(r, slug, name):
    st, body = r.call(slug, "GET", "/v1/slate", name)
    b = _j(body)
    subjects = {s["subject_id"]: s["state"] for ch in (b.get("channels") or {}).values()
                for s in (ch.get("subjects") or [])}
    return st, {"subjects": subjects, "unmatched_markets": b.get("unmatched_markets"),
                "posts_per_week": b.get("posts_per_week"),
                "enabled": sorted(c for c, ch in (b.get("channels") or {}).items() if ch.get("enabled"))}


def baseline_slate_reads(ctx):
    r = _Run(ctx, "BASE.")
    sa, a = _slate(r, ctx.A, "slate_a")
    sb, b = _slate(r, ctx.B, "slate_b")
    return {"a": a, "b": b, "status": [sa, sb]}


def check_slate_reads(ctx, base):
    r = _Run(ctx, "ON.")
    with r.guard("S1", "A's Slate equals the flag-OFF baseline"):
        st, a = _slate(r, ctx.A, "slate_a")
        r.add("S1", "A's Slate equals the flag-OFF baseline", st == 200 and a == base["a"],
              f"status={st} subjects={len(a['subjects'])} base={len(base['a']['subjects'])}")
    with r.guard("S2", "B's Slate holds none of A's Subjects"):
        st, b = _slate(r, ctx.B, "slate_b")
        r.add("S2", "B's Slate holds none of A's Subjects",
              st == 200 and not set(b["subjects"]) & set(base["a"]["subjects"]) and b == base["b"],
              f"status={st} overlap={len(set(b['subjects']) & set(base['a']['subjects']))}")
    with r.guard("S3", "POST /v1/slate/refresh still 202 (main pool)"):
        st, body = r.call(ctx.A, "POST", "/v1/slate/refresh", "refresh")
        r.add("S3", "POST /v1/slate/refresh still 202 (main pool)", st == 202, f"status={st} body={str(body)[:120]}")
    return r.res


# ── angle_gate_read ──────────────────────────────────────────────────────────────────────────────
def _review_rows(r, slug, name):
    st, body = r.call(slug, "GET", "/v1/content-writing/reviews", name)
    return st, _j(body).get("data") or []


def baseline_angle_gate_read(ctx):
    r = _Run(ctx, "BASE.")
    st, rows = _review_rows(r, ctx.A, "reviews_a")
    if st != 200 or not rows:
        return {"error": f"reviews status={st} rows={len(rows)}: A has no angle-gate request to read"}
    rid = rows[0]["request_id"]
    st, req = r.call(ctx.A, "GET", f"/v1/angle-gate/requests/{rid}", "request")
    approved = None
    for row in rows:
        s2, q = r.call(ctx.A, "GET", f"/v1/angle-gate/requests/{row['request_id']}", f"probe_{row['request_id'][:8]}")
        q = _j(q)
        chosen = [a for a in (q.get("angles") or []) if a.get("chosen")]
        if s2 == 200 and q.get("status") == "approved" and chosen:
            approved = {"rid": row["request_id"], "idx": chosen[0]["idx"], "option_id": chosen[0]["option_id"]}
            break
    return {"rid": rid, "status": st, "sha": _sha(_no_volatile(req)), "approved": approved}


def check_angle_gate_read(ctx, base):
    r = _Run(ctx, "ON.")
    if base.get("error"):
        r.add("G0", "precondition: A has an angle-gate request", False, base["error"])
        return r.res
    rid = base["rid"]
    with r.guard("G1", "A's request equals the flag-OFF baseline"):
        st, req = r.call(ctx.A, "GET", f"/v1/angle-gate/requests/{rid}", "request")
        r.add("G1", "A's request equals the flag-OFF baseline", st == 200 and _sha(_no_volatile(req)) == base["sha"],
              f"status={st}")
    with r.guard("G2", "B GET A's request -> 404"):
        st, _ = r.call(ctx.B, "GET", f"/v1/angle-gate/requests/{rid}", "b_request")
        r.add("G2", "B GET A's request -> 404", st == 404, f"status={st}")
    with r.guard("G3", "A GET a random request id -> 404"):
        st, _ = r.call(ctx.A, "GET", f"/v1/angle-gate/requests/{uuid.uuid4()}", "random")
        r.add("G3", "A GET a random request id -> 404", st == 404, f"status={st}")
    ap = base.get("approved")
    if not ap:
        r.add("G4", "reopen + choose re-read (needs an approved request of A)", False,
              "A has no approved request with a chosen angle: the re-read event is not exercised")
        return r.res
    with r.guard("G4", "reopen then choose the same idx -> 200 / 200, back to approved, same angle"):
        s1, _ = r.call(ctx.A, "POST", f"/v1/angle-gate/requests/{ap['rid']}/reopen", "reopen")
        s2, body = r.call(ctx.A, "POST", f"/v1/angle-gate/requests/{ap['rid']}/choose", "choose",
                          json={"idx": ap["idx"]})
        b = _j(body)
        chosen = [a.get("option_id") for a in (b.get("angles") or []) if a.get("chosen")]
        r.add("G4", "reopen then choose the same idx -> 200 / 200, back to approved, same angle",
              s1 == 200 and s2 == 200 and b.get("status") == "approved" and chosen == [ap["option_id"]],
              f"reopen={s1} choose={s2} status={b.get('status')}")
    return r.res


# ── reviews ──────────────────────────────────────────────────────────────────────────────────────
def baseline_reviews(ctx):
    r = _Run(ctx, "BASE.")
    st, rows = _review_rows(r, ctx.A, "reviews_a")
    sb, rows_b = _review_rows(r, ctx.B, "reviews_b")
    out = {"status": [st, sb], "a_sha": _sha(rows), "a_ids": [x["request_id"] for x in rows],
           "b_sha": _sha(rows_b)}
    if rows:
        s2, detail = r.call(ctx.A, "GET", f"/v1/content-writing/requests/{rows[0]['request_id']}/review", "detail")
        out.update(detail_rid=rows[0]["request_id"], detail_status=s2, detail_sha=_sha(detail))
    return out


def check_reviews(ctx, base):
    r = _Run(ctx, "ON.")
    with r.guard("R1", "A's review list equals the flag-OFF baseline"):
        st, rows = _review_rows(r, ctx.A, "reviews_a")
        r.add("R1", "A's review list equals the flag-OFF baseline", st == 200 and _sha(rows) == base["a_sha"],
              f"status={st} rows={len(rows)}")
    with r.guard("R2", "B's list equals its baseline and holds none of A's requests"):
        st, rows = _review_rows(r, ctx.B, "reviews_b")
        overlap = {x["request_id"] for x in rows} & set(base["a_ids"])
        r.add("R2", "B's list equals its baseline and holds none of A's requests",
              st == 200 and _sha(rows) == base["b_sha"] and not overlap, f"status={st} overlap={len(overlap)}")
    if not base.get("detail_rid"):
        r.add("R3", "review detail (needs a review row of A)", False, "A has no review row")
        return r.res
    with r.guard("R3", "A's review detail equals the baseline"):
        st, detail = r.call(ctx.A, "GET", f"/v1/content-writing/requests/{base['detail_rid']}/review", "detail")
        r.add("R3", "A's review detail equals the baseline", st == base["detail_status"] and
              _sha(detail) == base["detail_sha"], f"status={st}")
    with r.guard("R4", "B review detail of A's request -> 404"):
        st, _ = r.call(ctx.B, "GET", f"/v1/content-writing/requests/{base['detail_rid']}/review", "b_detail")
        r.add("R4", "B review detail of A's request -> 404", st == 404, f"status={st}")
    return r.res


# ── marketplace ──────────────────────────────────────────────────────────────────────────────────
def _market(r, slug, name):
    st, body = r.call(slug, "GET", "/v1/marketplace", name)
    b = _j(body)
    return st, {"total_atoms": b.get("total_atoms"), "total_tours": b.get("total_tours"), "sha": _sha(b.get("tours"))}


def baseline_marketplace(ctx):
    r = _Run(ctx, "BASE.")
    return {"a": _market(r, ctx.A, "market_a"), "b": _market(r, ctx.B, "market_b")}


def check_marketplace(ctx, base):
    r = _Run(ctx, "ON.")
    for cid, slug, key in (("M1", ctx.A, "a"), ("M2", ctx.B, "b")):
        with r.guard(cid, f"{slug}'s marketplace (total_atoms, tours) equals the baseline"):
            got = _market(r, slug, f"market_{key}")
            r.add(cid, f"{slug}'s marketplace (total_atoms, tours) equals the baseline",
                  got[0] == 200 and list(got) == list(base[key]), f"got={got} base={base[key]}")
    return r.res


# ── trip_reallocation ────────────────────────────────────────────────────────────────────────────
def _next_quarter():
    d = datetime.now(timezone.utc)
    q = (d.month - 1) // 3 + 2
    return (d.year + 1, 1) if q == 5 else (d.year, q)


def _suggest(r, slug, name):
    y, q = _next_quarter()
    st, body = r.call(slug, "GET", f"/v1/planning/trip-reallocation/suggest?year={y}&quarter={q}", name)
    b = _j(body)
    return st, {k: b.get(k) for k in ("has_existing_plan", "added", "removed", "unchanged")}


def baseline_trip_reallocation(ctx):
    r = _Run(ctx, "BASE.")
    return {"a": _suggest(r, ctx.A, "suggest_a"), "b": _suggest(r, ctx.B, "suggest_b")}


def check_trip_reallocation(ctx, base):
    r = _Run(ctx, "ON.")
    for cid, slug, key in (("T1", ctx.A, "a"), ("T2", ctx.B, "b")):
        with r.guard(cid, f"{slug}'s suggestion equals the baseline"):
            got = _suggest(r, slug, f"suggest_{key}")
            r.add(cid, f"{slug}'s suggestion equals the baseline", got[0] == 200 and list(got) == list(base[key]),
                  f"status={got[0]}")
    with r.guard("T3", "confirm accept=false -> 200 accepted false (audit only)"):
        y, q = _next_quarter()
        st, body = r.call(ctx.A, "POST", "/v1/planning/trip-reallocation/confirm", "confirm_reject",
                          json={"year": y, "quarter": q, "accept": False})
        r.add("T3", "confirm accept=false -> 200 accepted false (audit only)",
              st == 200 and _j(body).get("accepted") is False, f"status={st}")
    r.add("T4", "confirm accept=true NOT run live (covered in CI: test_aa859_wave4_pool_routes)", True,
          "report this as not tested live")
    return r.res


# ── subject_decide (IRREVERSIBLE) ────────────────────────────────────────────────────────────────
def baseline_subject_decide(ctx):
    r = _Run(ctx, "BASE.")
    st, a = _slate(r, ctx.A, "slate_a")
    proposed = [sid for sid, state in a["subjects"].items() if state == "proposed"]
    return {"status": st, "proposed": proposed[:3]}


def check_subject_decide(ctx, base):
    r = _Run(ctx, "ON.")
    subs = base.get("proposed") or []
    if len(subs) < 3:
        r.add("D0", "precondition: three proposed Subjects of A", False, f"found {len(subs)}")
        return r.res
    s1, s2, s3 = subs
    with r.guard("D1", "B pick / cut A's Subject -> 404 / 404"):
        p, _ = r.call(ctx.B, "POST", f"/v1/subjects/{s1}/pick", "b_pick")
        c, _ = r.call(ctx.B, "POST", f"/v1/subjects/{s2}/cut", "b_cut")
        r.add("D1", "B pick / cut A's Subject -> 404 / 404", p == 404 and c == 404, f"pick={p} cut={c}")
    with r.guard("D2", "A pick #1 -> 200 with a request id (IRREVERSIBLE: stays picked)"):
        st, body = r.call(ctx.A, "POST", f"/v1/subjects/{s1}/pick", "pick")
        r.add("D2", "A pick #1 -> 200 with a request id (IRREVERSIBLE: stays picked)",
              st == 200 and bool(_j(body).get("request_id")), f"status={st}")
    with r.guard("D3", "A pick #1 again -> 409"):
        st, _ = r.call(ctx.A, "POST", f"/v1/subjects/{s1}/pick", "pick_again")
        r.add("D3", "A pick #1 again -> 409", st == 409, f"status={st}")
    with r.guard("D4", "A cut #2 -> 200 cut"):
        st, body = r.call(ctx.A, "POST", f"/v1/subjects/{s2}/cut", "cut")
        r.add("D4", "A cut #2 -> 200 cut", st == 200 and _j(body).get("state") == "cut", f"status={st}")
    with r.guard("D5", "concurrent pick and cut of #3 -> one 200, one 409"):
        with ThreadPoolExecutor(max_workers=2) as pool:
            fp = pool.submit(ctx.raw, ctx.A, "POST", f"/v1/subjects/{s3}/pick")
            fc = pool.submit(ctx.raw, ctx.A, "POST", f"/v1/subjects/{s3}/cut")
            codes = sorted([fp.result().status_code, fc.result().status_code])
        r.add("D5", "concurrent pick and cut of #3 -> one 200, one 409", codes == [200, 409], f"codes={codes}")
    return r.res


CHECKS = {
    "slate_reads": check_slate_reads,
    "angle_gate_read": check_angle_gate_read,
    "reviews": check_reviews,
    "marketplace": check_marketplace,
    "trip_reallocation": check_trip_reallocation,
    "subject_decide": check_subject_decide,
}
BASELINES = {   # taken with the flag OFF, right before the flip
    "slate_reads": baseline_slate_reads,
    "angle_gate_read": baseline_angle_gate_read,
    "reviews": baseline_reviews,
    "marketplace": baseline_marketplace,
    "trip_reallocation": baseline_trip_reallocation,
    "subject_decide": baseline_subject_decide,
}


# ── the flip ritual ──────────────────────────────────────────────────────────────────────────────
def flip_one(short):
    key = FLAGS[short]
    rec = {"flag": key, "started": now(), "checks": [], "kept_on": False}
    rec["before"] = flag("get", [key])["after"][key]
    ctx = Ctx(short)
    base = None
    if short in BASELINES:
        flag("off", [key])
        time.sleep(2)
        try:
            base = BASELINES[short](ctx)
        except Exception as e:  # noqa: BLE001 — the check reports the missing baseline
            base = {"error": repr(e)[:300]}
        (ctx.out / "baseline.json").write_text(json.dumps(base, indent=1, default=str))
    flag("on", [key])
    # The log window starts AFTER the flag is on (the flag is read per request, no TTL): the earlier "- 5 s" slack
    # pulled the flag-OFF baseline requests (used_tenant_pool false) into the window and failed healthy flags.
    time.sleep(2)
    t0 = int(time.time())
    try:
        rec["checks"] = [{"id": i, "desc": d, "pass": bool(ok), "evidence": e}
                         for i, d, ok, e in CHECKS[short](ctx, base)]
    except Exception as e:  # noqa: BLE001 — a crashing check is a failed check
        rec["checks"].append({"id": "CRASH", "desc": "check function raised", "pass": False, "evidence": repr(e)[:300]})
    time.sleep(20)   # let the log lines reach CloudWatch
    logs = log_pool_lines(LOG_EVENTS[short], t0, int(time.time()) + 5)
    rec["logs"] = logs
    rec["checks"].append({"id": "LOG", "desc": "used_tenant_pool=True seen, no False with the flag on",
                          "pass": logs["true"] >= 1 and logs["false"] == 0,
                          "evidence": f"true={logs['true']} false={logs['false']}"})
    health = pool_health(key, t0, int(time.time()) + 5)
    rec["pool_health"] = health
    rec["checks"].append({"id": "POOL", "desc": f"tenant pool p95 wait_ms < {WAIT_P95_MAX_MS}, no unavailable",
                          "pass": health["p95_wait_ms"] is not None and health["p95_wait_ms"] < WAIT_P95_MAX_MS
                          and health["unavailable"] == 0, "evidence": json.dumps(health)})
    if all(c["pass"] for c in rec["checks"]):
        rec["kept_on"] = True
    else:
        flag("off", [key])     # the rollback: explicit "false" (a missing key would mean ON, S241 D-12)
        rec["reverted"] = now()
    rec["after"] = flag("get", [key])["after"][key]
    rec["finished"] = now()
    for c in rec["checks"]:
        print(("PASS " if c["pass"] else "FAIL ") + f"[{short}] {c['id']} {c['desc']} | {c['evidence']}")
    print(f"[{short}] {'KEPT ON' if rec['kept_on'] else 'REVERTED (off)'}")
    return rec


def main(argv):
    if argv and argv[0] in ("--off", "--get"):
        bad = [s for s in argv[1:] if s not in FLAGS]
        if bad or len(argv) < 2:
            raise SystemExit(f"unknown flag short names {bad}; known: {sorted(FLAGS)}")
        print(json.dumps(flag("off" if argv[0] == "--off" else "get", [FLAGS[s] for s in argv[1:]])))
        return
    bad = [s for s in argv if s not in FLAGS]
    if bad or not argv:
        raise SystemExit(f"usage: aa859_wave4_flip_verify.py <{'|'.join(FLAGS)}> ...; unknown: {bad}")
    report = json.loads(REPORT.read_text()) if REPORT.exists() else []
    for short in argv:
        rec = flip_one(short)
        report.append(rec)
        REPORT.write_text(json.dumps(report, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1:])
