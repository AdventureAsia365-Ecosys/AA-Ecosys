"""AA-859 S247 — automated flip-verify-revert for the D5b and wave-3 tenant-pool flags, modelled on the S240 tool
(docs/audits/2026-10-16-S240-aa859/aa859_flip_verify.py + aa859_flip_checks.py). NOT RUN by the lane that wrote it.

    python3 aa859_wave3_flip_verify.py <flag-short-name> [...]      e.g. t2_version_detail_reads brand_identity publish
    python3 aa859_wave3_flip_verify.py --off <flag-short-name> ...  explicit OFF (rollback; NOT DEL, S241 D-12)
    python3 aa859_wave3_flip_verify.py --get <flag-short-name> ...

Ritual per flag: (optional) baseline with the flag OFF -> SET "true" -> checks as tenant A / B through the public
Dev API -> Logs Insights: >= 1 used_tenant_pool=True line and 0 False lines for the flag's events -> keep ON if every
check passed, else SET "false" (the rollback; a missing key would mean ON). Same tenants as S240: A = terra-family
(does the writes), B = atlas-hearth (foreign tenant). Every id is discovered through list endpoints; a missing
precondition is one failing check that says what is missing (no invented data, no paid generation).

Preconditions the orchestrator owns (this script does not check them):
  - the wave-3 build is deployed (rollout COMPLETED) and CIS 262 is applied before flipping brand_identity
    (read-only check: aa859_262_preflight.py post -> post_262_ok);
  - the D5b divergence probe is 0 before keeping t2_version_detail_reads ON (aa859_262_preflight.py, d5b_divergence).

Flags (api/core/aa544_tenant_pool.py) and what each check does:

t2_version_detail_reads (D5b, aa859:t2_version_detail_reads_pool) — GET /v1/tours/{id}, /v1/tours/{id}/full
  (tenant branch), /v1/tours/versions/{id}/export-docx; log aa859_t2_version_detail_read.
  Baseline (flag OFF): A's three answers. Checks (flag ON): A's answers equal the baseline (full JSON for /{id} and
  /full; status, content type and file name for the .docx); B GET A-only tour -> 404 (skipped with a note if B has a
  version of the same tour); B export of A's version -> 404; A random uuid -> 404 on /{id} and export. Read-only.

brand_identity (wave 3, aa859:brand_identity_pool, needs 262) — GET / POST /admin/brand-identity with a tenant Bearer;
  log aa859_brand_identity.
  Baseline (flag OFF): A's and B's GET. Checks (flag ON): A GET equals the baseline; A POST the SAME content back
  -> 200, version = baseline + 1; A GET -> same content, new version; B GET unchanged; a POST with an over-long field
  -> 422 before any DB write. Needs A to have a brand identity already (never creates one). Leaves one new brand
  version row for A with identical content (a tenant cannot delete rows; the version history shows it).

publish (wave 3, aa859:publish_pool) — POST /v1/publish-log/{piece_id}/publish; logs aa859_publish, channel_publish.
  Needs A's WordPress = the E2E test site (connected here if A is disconnected) and a pending blog piece.
  Checks: B publish A's piece -> 404; A publish -> 200 published (uses 1 of A's 20 daily publishes); A publish the
  same piece again -> 200 replayed (no second post); A publish a random uuid -> 404; publish-log shows the row.
  Restores (finally): A unpublishes it (DELETE /v1/publish-log/{id}, W4 route) -> trashed; the WP post is deleted
  permanently on the test site; A's WP connection is disconnected again if this check connected it.

Secrets (tenant api keys, WP app password) are read at run time and never printed or saved.
Output: flip_raw_s247/<flag>/*.json, flip_report_s247.json (appended per run), next to this file.
"""
import hashlib
import json
import pathlib
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

API = "https://api-cis.lumiguides.it.com"
HERE = pathlib.Path(__file__).resolve().parent
PROFILE = ["--profile", "aa365-admin", "--region", "us-west-1"]
BUCKET = "aa-cis-bronze-005097885195"
FLAG_TOOL = HERE / "aa859_wave3_flag.py"
FLAG_TOOL_KEY = "scripts/s247_aa859_wave3_flag.py"
FLAG_OUT_KEY = "scripts/out/s247_aa859_wave3_flag.json"
TENANTS = ["terra-family", "atlas-hearth"]          # A does the writes, B is the foreign tenant
WP_SECRET = "aa-cis/dev/e2e-wordpress-test"
FLAGS = {
    "t2_version_detail_reads": "aa859:t2_version_detail_reads_pool",
    "brand_identity": "aa859:brand_identity_pool",
    "publish": "aa859:publish_pool",
}
LOG_EVENTS = {
    "t2_version_detail_reads": ["aa859_t2_version_detail_read"],
    "brand_identity": ["aa859_brand_identity"],
    "publish": ["aa859_publish", "channel_publish"],
}
OUT_DIR = HERE / "flip_raw_s247"
REPORT = HERE / "flip_report_s247.json"


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


def _all_my_versions(r, slug, tag, max_pages=5):
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


# ── D5b: t2_version_detail_reads ─────────────────────────────────────────────────────────────────
def _d5b_snapshot(ctx, tag):
    """A's three D5b answers for the first version of A's: {'v', 'pt', 'tour', 'full', 'docx'}."""
    r = _Run(ctx, f"{tag}.")
    st, rows, _ = _all_my_versions(r, ctx.A, "my_versions")
    if st != 200 or not rows:
        return {"error": f"my-versions status={st} rows={len(rows)}: A has no tour version to read"}
    v = rows[0]
    vid, pt = str(v["id"]), str(v["published_tour_id"])
    st1, tour = r.call(ctx.A, "GET", f"/v1/tours/{pt}", "tour")
    st2, full = r.call(ctx.A, "GET", f"/v1/tours/{pt}/full", "full")
    d = ctx.raw(ctx.A, "GET", f"/v1/tours/versions/{vid}/export-docx")
    return {"at": now(), "v": vid, "pt": pt, "tour": {"status": st1, "sha": _sha(tour), "body": tour},
            "full": {"status": st2, "sha": _sha(full), "keys": sorted(_j(full))},
            "docx": {"status": d.status_code, "type": d.headers.get("content-type"),
                     "disposition": d.headers.get("content-disposition"), "bytes": len(d.content)}}


def baseline_t2_version_detail_reads(ctx):
    return _d5b_snapshot(ctx, "BASE")


def check_t2_version_detail_reads(ctx, base):
    r = _Run(ctx, "DR.")
    A, B = ctx.A, ctx.B
    if not base or base.get("error"):
        r.add("0", "precondition: a flag-OFF baseline of A's three reads", False, (base or {}).get("error"))
        return r.res
    snap = None
    with r.guard("1", "A /{id}, /{id}/full, export-docx -> 200, equal to the flag-OFF baseline"):
        snap = _d5b_snapshot(ctx, "ON")
        r.save("1_snapshot", snap)
        ok = (snap.get("v") == base["v"]
              and snap["tour"]["status"] == 200 and snap["tour"]["sha"] == base["tour"]["sha"]
              and snap["full"]["status"] == 200 and snap["full"]["sha"] == base["full"]["sha"]
              and snap["full"]["keys"] == ["published", "raw", "seo"]
              and snap["docx"]["status"] == 200 and snap["docx"]["disposition"] == base["docx"]["disposition"]
              and "wordprocessingml" in (snap["docx"]["type"] or ""))
        r.add("1", "A /{id}, /{id}/full, export-docx -> 200, equal to the flag-OFF baseline", ok,
              f"tour {base['tour']['status']}->{snap['tour']['status']} same={snap['tour']['sha'] == base['tour']['sha']} "
              f"full same={snap['full']['sha'] == base['full']['sha']} keys={snap['full']['keys']} "
              f"docx {snap['docx']['status']} {snap['docx']['disposition']}")
    pt, vid = base["pt"], base["v"]
    with r.guard("2", "B GET A's tour -> 404 (B has no version of it)"):
        st, rows_b, _ = _all_my_versions(r, B, "2_my_versions_b")
        if any(str(x.get("published_tour_id")) == pt for x in rows_b):
            r.add("2", "B GET A's tour -> 404 (B has no version of it)", True,
                  "skipped: B rewrote the same tour, so /{id} is legitimately B's too")
        else:
            st1, _ = r.call(B, "GET", f"/v1/tours/{pt}", "2_foreign_tour")
            st2, _ = r.call(B, "GET", f"/v1/tours/{pt}/full", "2_foreign_full")
            r.add("2", "B GET A's tour -> 404 (B has no version of it)", st1 == 404 and st2 == 404,
                  f"tour={st1} full={st2}")
    with r.guard("3", "B export A's version -> 404"):
        d = ctx.raw(B, "GET", f"/v1/tours/versions/{vid}/export-docx")
        r.add("3", "B export A's version -> 404", d.status_code == 404, f"status={d.status_code}")
    with r.guard("4", "A random uuid -> 404 on /{id} and export"):
        rnd = str(uuid.uuid4())
        st1, _ = r.call(A, "GET", f"/v1/tours/{rnd}", "4_random_tour")
        d = ctx.raw(A, "GET", f"/v1/tours/versions/{rnd}/export-docx")
        r.add("4", "A random uuid -> 404 on /{id} and export", st1 == 404 and d.status_code == 404,
              f"tour={st1} export={d.status_code}")
    return r.res


# ── wave 3: brand_identity ───────────────────────────────────────────────────────────────────────
_BRAND_FIELDS = ("system_prompt", "style_guide", "forbidden_words", "brand_name", "brand_type", "core_idea",
                 "customer_segment", "customer_mindset", "tone_of_voice", "good_examples", "target_markets",
                 "default_cta")


def _brand_content(b):
    return {k: b.get(k) for k in _BRAND_FIELDS}


def baseline_brand_identity(ctx):
    r = _Run(ctx, "BASE.")
    sa, a = r.call(ctx.A, "GET", "/admin/brand-identity", "brand_a")
    sb, b = r.call(ctx.B, "GET", "/admin/brand-identity", "brand_b")
    return {"at": now(), "a": {"status": sa, "body": a}, "b": {"status": sb, "body": b}}


def check_brand_identity(ctx, base):
    r = _Run(ctx, "BI.")
    A, B = ctx.A, ctx.B
    a0 = _j((base or {}).get("a", {}).get("body"))
    if not base or base["a"]["status"] != 200 or not a0.get("configured"):
        r.add("0", "precondition: A has a brand identity (flag-OFF baseline)", False,
              f"baseline status={(base or {}).get('a', {}).get('status')} configured={a0.get('configured')} — "
              "not creating one")
        return r.res
    r.add("0", "precondition: A has a brand identity (flag-OFF baseline)", True,
          f"version={a0.get('version')} history={len(a0.get('history') or [])}")
    with r.guard("1", "A GET -> 200, equal to the flag-OFF baseline"):
        st, body = r.call(A, "GET", "/admin/brand-identity", "1_get_a")
        r.add("1", "A GET -> 200, equal to the flag-OFF baseline", st == 200 and body == a0,
              f"status={st} same={body == a0} sha_on={_sha(body)} sha_off={_sha(a0)}")
    with r.guard("2", "A POST an over-long field -> 422, nothing written"):
        st, body = r.call(A, "POST", "/admin/brand-identity", "2_post_too_long",
                          json={**_brand_content(a0), "style_guide": "A" * 50000})
        st2, after = r.call(A, "GET", "/admin/brand-identity", "2_get_after")
        r.add("2", "A POST an over-long field -> 422, nothing written",
              st == 422 and _j(after).get("version") == a0.get("version"),
              f"status={st} version_after={_j(after).get('version')}")
    with r.guard("3", "A POST the same content back -> 200, version + 1, same content"):
        st, body = r.call(A, "POST", "/admin/brand-identity", "3_post_same", json=_brand_content(a0))
        st2, after = r.call(A, "GET", "/admin/brand-identity", "3_get_after")
        after = _j(after)
        same = _brand_content(after) == _brand_content(a0)
        r.add("3", "A POST the same content back -> 200, version + 1, same content",
              st == 200 and _j(body).get("version") == (a0.get("version") or 0) + 1
              and after.get("version") == _j(body).get("version") and same,
              f"post={st} version {a0.get('version')}->{_j(body).get('version')} get_version={after.get('version')} "
              f"same_content={same} (one new brand version row for A, identical content)")
    with r.guard("4", "B GET -> B's own, unchanged by A's save"):
        st, body = r.call(B, "GET", "/admin/brand-identity", "4_get_b")
        r.add("4", "B GET -> B's own, unchanged by A's save",
              st == base["b"]["status"] and body == base["b"]["body"], f"status={st} same={body == base['b']['body']}")
    return r.res


# ── wave 3: publish ──────────────────────────────────────────────────────────────────────────────
def _wp_post(wp, method, external_id, params):
    url = wp["site_url"].rstrip("/") + f"/wp-json/wp/v2/posts/{external_id}"
    resp = requests.request(method, url, params=params, auth=(wp["app_user"], wp["app_password"]), timeout=60)
    try:
        return resp.status_code, resp.json()
    except ValueError:
        return resp.status_code, {}


def _log_row(r, publish_id, name):
    st, body = r.call(r.ctx.A, "GET", "/v1/publish-log?limit=200", name)
    return st, next((d for d in _j(body).get("data") or [] if d.get("publish_id") == publish_id), None)


def check_publish(ctx, base):
    r = _Run(ctx, "PB.")
    A, B = ctx.A, ctx.B
    wp = json.loads(secret(WP_SECRET))
    we_connected = False
    pid = publish_id = external_id = external_url = None
    with r.guard("0a", "precondition: A's WordPress = E2E test site (connect it if disconnected)"):
        st, body = r.call(A, "GET", "/v1/integrations/wordpress", "0a_wp_status_before")
        b = _j(body)
        if st != 200:
            r.add("0a", "precondition: A's WordPress = E2E test site (connect it if disconnected)", False, f"status={st}")
            return r.res
        if b.get("connected"):
            same = _host(b.get("site_url")) == _host(wp["site_url"])
            r.add("0a", "precondition: A's WordPress = E2E test site (connect it if disconnected)", same,
                  f"already connected, e2e_host_match={same}")
            if not same:
                return r.res
        else:
            st, body = r.call(A, "POST", "/v1/integrations/wordpress", "0a_wp_connect",
                              json={"wp_url": wp["site_url"], "username": wp["app_user"],
                                    "app_password": wp["app_password"]})
            we_connected = st == 200 and _j(body).get("connected") is True
            r.add("0a", "precondition: A's WordPress = E2E test site (connect it if disconnected)", we_connected,
                  f"was disconnected; connect status={st}")
            if not we_connected:
                return r.res
    try:
        with r.guard("0b", "precondition: A has a blog piece in /pending"):
            st, body = r.call(A, "GET", "/v1/publish-log/pending", "0b_pending")
            blogs = [d for d in _j(body).get("data") or [] if d.get("channel") == "blog"]
            pid = blogs[-1]["piece_id"] if st == 200 and blogs else None
            r.add("0b", "precondition: A has a blog piece in /pending", bool(pid),
                  f"status={st} blog_pending={len(blogs)}" + ("" if pid else " — not generating content (paid run)"))
        if not pid:
            return r.res
        with r.guard("1", "B publish A's piece -> 404, nothing written"):
            st, body = r.call(B, "POST", f"/v1/publish-log/{pid}/publish", "1_foreign_publish")
            st2, body2 = r.call(A, "GET", "/v1/publish-log/pending", "1_pending_after_foreign")
            still = any(d.get("piece_id") == pid for d in _j(body2).get("data") or [])
            r.add("1", "B publish A's piece -> 404, nothing written", st == 404 and still,
                  f"status={st} detail={str(_j(body).get('detail'))[:60]!r} piece_still_pending={still}")
        with r.guard("2", "A publish -> 200 published to the E2E site"):
            st, body = r.call(A, "POST", f"/v1/publish-log/{pid}/publish", "2_publish")
            b = _j(body)
            if st == 200 and b.get("success") and b.get("status") == "published":
                publish_id, external_id, external_url = b.get("publish_id"), b.get("external_id"), b.get("external_url")
            r.add("2", "A publish -> 200 published to the E2E site", bool(publish_id and external_id),
                  f"status={st} publish_id={publish_id} external_id={external_id} "
                  f"detail={str(b.get('detail') or b.get('last_error') or '')[:80]!r} (1 of A's daily publishes)")
        if not publish_id:
            return r.res
        with r.guard("3", "A publish the same piece again -> 200 replayed, same post"):
            st, body = r.call(A, "POST", f"/v1/publish-log/{pid}/publish", "3_publish_again")
            b = _j(body)
            r.add("3", "A publish the same piece again -> 200 replayed, same post",
                  st == 200 and b.get("replayed") is True and b.get("external_id") == external_id,
                  f"status={st} replayed={b.get('replayed')} same_post={b.get('external_id') == external_id}")
        with r.guard("4", "A publish a random uuid -> 404"):
            st, _ = r.call(A, "POST", f"/v1/publish-log/{uuid.uuid4()}/publish", "4_random")
            r.add("4", "A publish a random uuid -> 404", st == 404, f"status={st}")
        with r.guard("5", "publish-log shows A's row published"):
            st, row = _log_row(r, publish_id, "5_log")
            r.add("5", "publish-log shows A's row published", st == 200 and row and row.get("status") == "published",
                  f"row={row and row.get('status')}")
    finally:
        with r.guard("R", "restore: unpublished (W4 route), WP post deleted, WP integration as it started"):
            notes, ok = [], True
            if publish_id:
                st, row = _log_row(r, publish_id, "R_log")
                if row and row.get("status") == "published":
                    s, b = r.call(A, "DELETE", f"/v1/publish-log/{publish_id}", "R_unpublish")
                    notes.append(f"unpublish={s} remote={_j(b).get('remote')}")
                    st, row = _log_row(r, publish_id, "R_log2")
                if row and row.get("status") == "published":
                    ok = False
                    notes.append(f"publish_id {publish_id} STILL published: unpublish it as A")
            if external_id and (not _host(external_url) or _host(external_url) == _host(wp["site_url"])):
                s, b = _wp_post(wp, "DELETE", external_id, {"force": "true"})
                deleted = s == 200 and _j(b).get("deleted") is True
                notes.append(f"wp_force_delete={s} deleted={deleted}")
                ok = ok and deleted
            if we_connected:
                s, _ = r.call(A, "DELETE", "/v1/integrations/wordpress", "R_wp_disconnect")
                s2, b2 = r.call(A, "GET", "/v1/integrations/wordpress", "R_wp_status")
                notes.append(f"wp_disconnect={s} connected_after={_j(b2).get('connected')}")
                ok = ok and s == 200 and _j(b2).get("connected") is False
            r.add("R", "restore: unpublished (W4 route), WP post deleted, WP integration as it started", ok,
                  " ".join(notes) or "nothing to restore")
    return r.res


CHECKS = {
    "t2_version_detail_reads": check_t2_version_detail_reads,
    "brand_identity": check_brand_identity,
    "publish": check_publish,
}
BASELINES = {   # taken with the flag OFF, right before the flip
    "t2_version_detail_reads": baseline_t2_version_detail_reads,
    "brand_identity": baseline_brand_identity,
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
        raise SystemExit(f"usage: aa859_wave3_flip_verify.py <{'|'.join(FLAGS)}> ...; unknown: {bad}")
    report = json.loads(REPORT.read_text()) if REPORT.exists() else []
    for short in argv:
        rec = flip_one(short)
        report.append(rec)
        REPORT.write_text(json.dumps(report, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1:])
