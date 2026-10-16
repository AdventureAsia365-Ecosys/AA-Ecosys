"""AA-817 S239 — live verify of the two tenant-pool flags on Dev through the public API.

Flags (turned on by Nghiep; this script never touches Redis, DB rows or AWS resources):
  aa817:content_piece_reads_pool   -> GET /v1/content-writing/requests/{id}/latest-piece
  aa544:integration_disconnect_pool -> DELETE /v1/integrations/wordpress (and /facebook)

Tenants: the four E2E test tenants (aa-cis/dev/e2e-tenant/<slug>). Tenant A = terra-family does the
writes (WordPress connect + disconnect on the TasteWP site aa-cis/dev/e2e-wordpress-test). The other
three are used read-only, as the "foreign" tenants whose request/piece ids A must not read.
Secrets are read at run time and never printed or saved; JWTs and app passwords are not written out.

Run: python3 verify_flags.py  (writes raw/*.json next to this file, prints a summary).
"""
import json
import pathlib
import subprocess
import uuid
from datetime import datetime, timezone

import requests

API = "https://api-cis.lumiguides.it.com"
OUT = pathlib.Path(__file__).resolve().parent / "raw"
OUT.mkdir(exist_ok=True)
A = "terra-family"
OTHERS = ["atlas-hearth", "trail-pulse", "wildkind-travel"]
CHECKS = []


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def secret(name):
    return subprocess.check_output(
        ["aws", "secretsmanager", "get-secret-value", "--secret-id", name, "--profile", "aa365-admin",
         "--region", "us-west-1", "--query", "SecretString", "--output", "text"], text=True).strip()


def trim(obj):
    """Keep evidence small: content_text cut to 120 chars (tenant copy, not a secret)."""
    if isinstance(obj, dict):
        return {k: (v[:120] + "...") if k == "content_text" and isinstance(v, str) and len(v) > 120 else trim(v)
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [trim(x) for x in obj]
    return obj


def call(method, path, h, name, **kw):
    t = now()
    r = requests.request(method, API + path, headers=h, timeout=90, **kw)
    try:
        body = r.json()
    except ValueError:
        body = r.text[:500]
    rec = {"at": t, "method": method, "path": path, "status": r.status_code,
           "x_request_id": r.headers.get("x-request-id") or r.headers.get("x-amzn-requestid"), "body": trim(body)}
    (OUT / f"{name}.json").write_text(json.dumps(rec, indent=1, default=str))
    return r.status_code, body, rec


def check(cid, desc, ok, evidence):
    CHECKS.append({"id": cid, "check": desc, "result": "PASS" if ok else "FAIL", "evidence": evidence})
    print(f"[{'PASS' if ok else 'FAIL'}] {cid} {desc} -> {evidence}", flush=True)


def login(slug):
    r = requests.post(API + "/auth/tenant-login", json={"api_key": secret(f"aa-cis/dev/e2e-tenant/{slug}")}, timeout=30)
    r.raise_for_status()
    j = r.json()
    return j["tenant_id"], {"Authorization": "Bearer " + j["token"]}


started = now()
tenants = {s: login(s) for s in [A] + OTHERS}
tid_a, ha = tenants[A]

# ── 1. aa817:content_piece_reads_pool ────────────────────────────────────────────────────────
own = {}  # slug -> list of (request_id, piece_id) from the tenant's own review list
for slug, (tid, h) in tenants.items():
    st, body, _ = call("GET", "/v1/content-writing/reviews", h, f"c0_reviews_{slug}")
    own[slug] = [(d["request_id"], d["piece_id"]) for d in (body.get("data") or [])] if st == 200 else []

# 1a. own request ids -> 200 with own piece (angle_gate_request_id matches)
for i, (rid, pid) in enumerate(own[A]):
    st, body, _ = call("GET", f"/v1/content-writing/requests/{rid}/latest-piece", ha, f"c1_own_latest_{i}")
    p = body.get("piece") if isinstance(body, dict) else None
    check(f"C1.{i}", f"{A} own request {rid[:8]} latest-piece",
          st == 200 and p is not None and p.get("angle_gate_request_id") == rid,
          f"raw/c1_own_latest_{i}.json status={st} piece={'yes' if p else 'null'}")

# 1b. each other tenant reads its OWN first request (proves the foreign id really has a piece)
foreign = []
for slug in OTHERS:
    if not own[slug]:
        continue
    rid, pid = own[slug][0]
    st, body, _ = call("GET", f"/v1/content-writing/requests/{rid}/latest-piece", tenants[slug][1], f"c2_owner_latest_{slug}")
    p = body.get("piece") if isinstance(body, dict) else None
    check(f"C2.{slug}", f"{slug} reads its own request {rid[:8]} (control)",
          st == 200 and p is not None, f"raw/c2_owner_latest_{slug}.json status={st}")
    foreign.append((slug, rid, pid))

# 1c. tenant A asks for every foreign request id -> never another tenant's content
for slug, rid, pid in foreign:
    st, body, _ = call("GET", f"/v1/content-writing/requests/{rid}/latest-piece", ha, f"c3_cross_latest_{slug}")
    p = body.get("piece") if isinstance(body, dict) else "?"
    check(f"C3.{slug}", f"{A} -> {slug}'s request {rid[:8]} latest-piece",
          st in (200, 404) and not p, f"raw/c3_cross_latest_{slug}.json status={st} piece={p!r}")

# 1d. the reverse direction: one other tenant asks for A's request
if foreign and own[A]:
    slug = foreign[0][0]
    rid = own[A][0][0]
    st, body, _ = call("GET", f"/v1/content-writing/requests/{rid}/latest-piece", tenants[slug][1], "c4_reverse_latest")
    p = body.get("piece") if isinstance(body, dict) else "?"
    check("C4", f"{slug} -> {A}'s request {rid[:8]} latest-piece", st in (200, 404) and not p,
          f"raw/c4_reverse_latest.json status={st} piece={p!r}")

# 1e. random UUID
rnd = str(uuid.uuid4())
st, body, _ = call("GET", f"/v1/content-writing/requests/{rnd}/latest-piece", ha, "c5_random_latest")
check("C5", "random request id latest-piece", st in (200, 404) and not (body or {}).get("piece"),
      f"raw/c5_random_latest.json status={st}")

# 1f. GET /pieces/{id} (separate flag aa544:stage5:get_piece_pool, not one of the two under test;
# called so the logs show which pool it uses today). Own -> 200, foreign -> 404.
if own[A]:
    st, body, _ = call("GET", f"/v1/content-writing/pieces/{own[A][0][1]}", ha, "c6_own_piece")
    check("C6", f"{A} own piece GET /pieces/{{id}} (stage5 flag, context)", st == 200,
          f"raw/c6_own_piece.json status={st}")
for slug, rid, pid in foreign:
    st, body, _ = call("GET", f"/v1/content-writing/pieces/{pid}", ha, f"c7_cross_piece_{slug}")
    check(f"C7.{slug}", f"{A} -> {slug}'s piece GET /pieces/{{id}} (stage5 flag, context)", st == 404,
          f"raw/c7_cross_piece_{slug}.json status={st}")

# ── 2. aa544:integration_disconnect_pool ────────────────────────────────────────────────────
wp = json.loads(secret("aa-cis/dev/e2e-wordpress-test"))
st, body, _ = call("GET", "/v1/integrations/wordpress", ha, "w0_status_before")
check("W0", f"{A} WordPress status before", st == 200, f"raw/w0_status_before.json connected={body.get('connected')}")
st, body, _ = call("POST", "/v1/integrations/wordpress", ha, "w1_connect",
                   json={"wp_url": wp["site_url"], "username": wp["app_user"], "app_password": wp["app_password"]})
check("W1", "connect WordPress (TasteWP test site)", st == 200 and body.get("connected") is True,
      f"raw/w1_connect.json status={st}")
st, body, _ = call("POST", "/v1/integrations/wordpress/test", ha, "w2_test")
check("W2", "test connection", st == 200 and body.get("success") is True, f"raw/w2_test.json status={st} success={body.get('success')}")
st, body, _ = call("GET", "/v1/integrations/wordpress", ha, "w3_status_connected")
check("W3", "status shows connected", st == 200 and body.get("connected") is True, f"raw/w3_status_connected.json")
st, body, _ = call("DELETE", "/v1/integrations/wordpress", ha, "w4_disconnect")
check("W4", "DELETE /v1/integrations/wordpress (flag route)",
      st == 200 and body.get("disconnected") is True and body.get("connected") is False,
      f"raw/w4_disconnect.json status={st} disconnected={body.get('disconnected')}")
st, body, _ = call("GET", "/v1/integrations/wordpress", ha, "w5_status_after")
check("W5", "re-read shows disconnected", st == 200 and body.get("connected") is False, "raw/w5_status_after.json")
st, body, _ = call("DELETE", "/v1/integrations/wordpress", ha, "w6_disconnect_again")
check("W6", "second DELETE, no row (idempotent)", st == 200 and body.get("disconnected") is False,
      f"raw/w6_disconnect_again.json status={st} disconnected={body.get('disconnected')}")
st, body, _ = call("GET", "/v1/integrations/facebook", ha, "w7a_facebook_status")
if st == 200 and body.get("connected") is False:  # only when there is nothing to disconnect
    st, body, _ = call("DELETE", "/v1/integrations/facebook", ha, "w7_disconnect_facebook_none")
    check("W7", "DELETE /v1/integrations/facebook, tenant has none (same flag)", st == 200 and body.get("disconnected") is False,
          f"raw/w7_disconnect_facebook_none.json status={st}")

summary = {"started": started, "finished": now(), "tenant_a": {"slug": A, "tenant_id": tid_a},
           "others": {s: tenants[s][0] for s in OTHERS}, "checks": CHECKS}
(OUT / "summary.json").write_text(json.dumps(summary, indent=1))
print(json.dumps({"started": started, "finished": summary["finished"],
                  "pass": sum(c["result"] == "PASS" for c in CHECKS), "fail": sum(c["result"] == "FAIL" for c in CHECKS)}))
