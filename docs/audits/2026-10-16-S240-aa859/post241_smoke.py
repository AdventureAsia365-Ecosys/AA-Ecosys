"""AA-859 S240 — live smoke after migration 241 + PR-A double-click evidence (Dev, public API only).

1. The 5 routes already on the tenant pool still answer for their own tenant after 241 (they LEFT JOIN
   angle_gate_option, which 241 put under RLS):
   GET /v1/publish-log, GET /v1/publish-log/pending, GET .../requests/{id}/latest-piece,
   GET /v1/content-writing/pieces/{id}; a foreign tenant gets 404 / null on A's ids.
2. PR-A: tenant A connects the E2E WordPress test site, then sends two DELETEs at the same time.
   Expected: both 200, one disconnected=true and one disconnected=false (or both true->false order),
   no 503 / 500. End state = not connected (same as start).

Secrets (tenant api keys, WP app password) are read at run time and never printed or saved.
Run: python3 post241_smoke.py  -> writes post241_smoke_raw/*.json + post241_smoke_summary.json.
"""
import json
import pathlib
import subprocess
import threading
import uuid
from datetime import datetime, timezone

import requests

API = "https://api-cis.lumiguides.it.com"
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "post241_smoke_raw"
OUT.mkdir(exist_ok=True)
A, B = "terra-family", "atlas-hearth"
CHECKS = []


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def secret(name):
    return subprocess.check_output(
        ["aws", "secretsmanager", "get-secret-value", "--secret-id", name, "--profile", "aa365-admin",
         "--region", "us-west-1", "--query", "SecretString", "--output", "text"], text=True).strip()


def trim(obj):
    if isinstance(obj, dict):
        return {k: (v[:120] + "...") if k == "content_text" and isinstance(v, str) and len(v) > 120 else trim(v)
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [trim(x) for x in obj[:20]]
    return obj


def call(method, path, h, name, **kw):
    t = now()
    r = requests.request(method, API + path, headers=h, timeout=90, **kw)
    try:
        body = r.json()
    except ValueError:
        body = r.text[:500]
    rec = {"at": t, "method": method, "path": path, "status": r.status_code, "body": trim(body)}
    (OUT / f"{name}.json").write_text(json.dumps(rec, indent=1, default=str))
    return r.status_code, body


def check(cid, desc, ok, evidence):
    CHECKS.append({"id": cid, "desc": desc, "pass": bool(ok), "evidence": evidence})
    print(("PASS " if ok else "FAIL ") + cid + " " + desc + " | " + evidence)


def login(slug):
    r = requests.post(API + "/auth/tenant-login", json={"api_key": secret(f"aa-cis/dev/e2e-tenant/{slug}")}, timeout=30)
    r.raise_for_status()
    j = r.json()
    return j["tenant_id"], {"Authorization": "Bearer " + j["token"]}


started = now()
(tid_a, ha), (tid_b, hb) = login(A), login(B)

# ── 1. existing tenant-pool routes after 241 ──────────────────────────────────────────────────
st, body = call("GET", "/v1/content-writing/reviews", ha, "r0_reviews_a")
own = [(d["request_id"], d["piece_id"]) for d in (body.get("data") or [])] if st == 200 else []
check("R0", f"{A} GET /v1/content-writing/reviews", st == 200 and own, f"status={st} n={len(own)}")
st, body = call("GET", "/v1/publish-log", ha, "r1_publish_log")
check("R1", "GET /v1/publish-log (aa544:publish_log_list_pool)", st == 200, f"status={st}")
st, body = call("GET", "/v1/publish-log/pending", ha, "r2_pending")
check("R2", "GET /v1/publish-log/pending (aa544:stage1:publish_pending_pool)", st == 200, f"status={st}")
if own:
    rid, pid = own[0]
    st, body = call("GET", f"/v1/content-writing/requests/{rid}/latest-piece", ha, "r3_latest_own")
    check("R3", "own latest-piece (aa817:content_piece_reads_pool)", st == 200 and (body or {}).get("piece"),
          f"status={st}")
    st, body = call("GET", f"/v1/content-writing/pieces/{pid}", ha, "r4_piece_own")
    check("R4", "own GET /pieces/{id} (aa544:stage5:get_piece_pool)", st == 200, f"status={st}")
    st, body = call("GET", f"/v1/content-writing/requests/{rid}/latest-piece", hb, "r5_latest_foreign")
    check("R5", f"{B} -> {A}'s latest-piece", st in (200, 404) and not (body or {}).get("piece"), f"status={st}")
    st, body = call("GET", f"/v1/content-writing/pieces/{pid}", hb, "r6_piece_foreign")
    check("R6", f"{B} -> {A}'s piece", st == 404, f"status={st}")

# ── 2. PR-A double-click disconnect ───────────────────────────────────────────────────────────
wp = json.loads(secret("aa-cis/dev/e2e-wordpress-test"))
st, body = call("GET", "/v1/integrations/wordpress", ha, "w0_status_before")
check("W0", "WordPress status before", st == 200, f"status={st} connected={(body or {}).get('connected')}")
st, body = call("POST", "/v1/integrations/wordpress", ha, "w1_connect",
                json={"wp_url": wp["site_url"], "username": wp["app_user"], "app_password": wp["app_password"]})
check("W1", "connect the E2E WordPress test site", st in (200, 201), f"status={st}")
results = {}
barrier = threading.Barrier(2)


def fire(i):
    barrier.wait()
    results[i] = call("DELETE", "/v1/integrations/wordpress", ha, f"w2_delete_parallel_{i}")


ts = [threading.Thread(target=fire, args=(i,)) for i in (1, 2)]
[t.start() for t in ts]
[t.join() for t in ts]
codes = sorted(results[i][0] for i in results)
flags = sorted(bool((results[i][1] or {}).get("disconnected")) for i in results)
check("W2", "two parallel DELETEs: both 200, exactly one disconnected=true", codes == [200, 200] and flags == [False, True],
      f"statuses={codes} disconnected={flags}")
st, body = call("GET", "/v1/integrations/wordpress", ha, "w3_status_after")
check("W3", "status after: not connected", st == 200 and not (body or {}).get("connected"), f"status={st}")

summary = {"started": started, "finished": now(), "tenant_a": tid_a, "tenant_b": tid_b,
           "pass": sum(c["pass"] for c in CHECKS), "total": len(CHECKS), "checks": CHECKS,
           "note": "random id probe " + str(uuid.uuid4())[:8]}
(HERE / "post241_smoke_summary.json").write_text(json.dumps(summary, indent=1))
print(f"{summary['pass']}/{summary['total']} PASS")
