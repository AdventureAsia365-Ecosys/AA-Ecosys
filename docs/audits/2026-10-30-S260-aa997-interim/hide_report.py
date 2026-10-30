# S260 AA-997: queue the hide_flagged REPORT (no write) through the admin API inside the api container, wait, print.
import json, os, time, urllib.request
BASE = "http://127.0.0.1:8000"
H = {"x-admin-secret": os.environ["ADMIN_SECRET"], "content-type": "application/json", "x-admin-role": "admin", "x-admin-user-id": "s260-orchestrator"}
def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method, headers=H, data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]
st, j = call("POST", "/admin/places/relocate", {"mode": "hide_flagged"})
print("POST", st, json.dumps(j)[:400])
jid = j.get("job_id") if isinstance(j, dict) else None
for _ in range(60):
    if not jid: break
    time.sleep(5)
    st, job = call("GET", f"/admin/job-runner/jobs/{jid}")
    s = (job or {}).get("status") if isinstance(job, dict) else None
    if s in ("succeeded", "failed", "cancelled", "stopped_budget"):
        res = job.get("result") or {}
        print("JOB", s, job.get("error"))
        for k in ("mode", "rows", "linked", "by_country", "by_outcome", "by_reason", "by_stamp_version", "by_located_by", "restored_skipped", "hidden", "audit_rows", "located_by", "outcomes"):
            print(k, json.dumps(res.get(k), default=str)[:600])
        print("samples", json.dumps((res.get("samples") or [])[:25], default=str, ensure_ascii=False)[:6000])
        break
# negative check: confirm without a matching narrowed report -> 409
st, j = call("POST", "/admin/places/relocate", {"mode": "hide_flagged", "confirm": True, "country": "India"})
print("NEG confirm India", st, str(j)[:300])
