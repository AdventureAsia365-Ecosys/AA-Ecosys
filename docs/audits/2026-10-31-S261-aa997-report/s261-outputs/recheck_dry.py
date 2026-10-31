# S261 AA-997: relocate recheck DRY RUN (no call, no write) for the aa997.1 llm_point/off_route rows, strategy v2, aa997.3.
import json, os, sys, time, urllib.request
BASE = "http://127.0.0.1:8000"
H = {"x-admin-secret": os.environ["ADMIN_SECRET"], "content-type": "application/json", "x-admin-role": "admin", "x-admin-user-id": "s261-orchestrator"}
MODE = os.environ.get("MODE", "dry_run")
def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method, headers=H, data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]
body = {"mode": MODE, "located_by": ["llm"], "limit": int(os.environ.get("LIMIT", "400")), "strategy": "v2", "accept_rule": os.environ.get("ACCEPT", "aa997.3"), "recheck": ["llm_point", "off_route"]}
if os.environ.get("MAXREQ"): body["max_requests"] = int(os.environ["MAXREQ"])
st, j = call("POST", "/admin/places/relocate", body)
print("POST", st, json.dumps(j)[:600])
jid = j.get("job_id") if isinstance(j, dict) else None
for _ in range(int(os.environ.get("WAIT_LOOPS", "100"))):
    if not jid: break
    time.sleep(6)
    st, job = call("GET", f"/admin/job-runner/jobs/{jid}")
    s = (job or {}).get("status") if isinstance(job, dict) else None
    if s in ("succeeded", "failed", "cancelled", "stopped_budget"):
        res = job.get("result") or {}
        print("JOB", jid, s, job.get("error"))
        slim = {k: v for k, v in res.items() if k not in ("samples", "ids")}
        print("RESULT", json.dumps(slim, default=str)[:4000])
        print("SAMPLES", json.dumps((res.get("samples") or [])[:12], default=str, ensure_ascii=False)[:3000])
        break
else:
    print("TIMEOUT", jid)
