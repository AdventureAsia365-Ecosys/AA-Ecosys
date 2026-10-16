"""S239 AA-825: enqueue one manual DRY RUN per CIS retention kind via the admin API and record the result.

DRY RUN only: every POST body is {"kind": k, "dry_run": true}; the script refuses to send anything else.
The admin secret is read from Secrets Manager at run time, held in memory only, never printed or saved.
"""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

API = "https://api-cis.lumiguides.it.com"
OUT = sys.argv[1]
SECRET_ID = "aa-cis/dev/admin-secret"
KINDS = ["retention_llm_call_log", "retention_tenant_api_usage", "retention_job",
         "retention_decision_log", "retention_cost_explorer_snapshot"]

_secret = subprocess.run(
    ["aws", "secretsmanager", "get-secret-value", "--secret-id", SECRET_ID, "--profile", "aa365-admin",
     "--region", "us-west-1", "--query", "SecretString", "--output", "text"],
    capture_output=True, text=True, check=True).stdout.strip()
HDR = {"X-Admin-Secret": _secret, "x-admin-user-id": "claude-code-s239", "Content-Type": "application/json"}


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    if method == "POST":
        assert body is not None and body.get("dry_run") is True and set(body) == {"kind", "dry_run"}, "DRY RUN only"
    req = urllib.request.Request(API + path, data=data, method=method, headers=HDR)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:500]}


def save(name, obj):
    with open(f"{OUT}/{name}", "w") as f:
        json.dump(obj, f, indent=1, default=str)


now = lambda: datetime.now(timezone.utc).isoformat()

# 1. idle check
gate = call("GET", "/admin/job-runner/deploy-gate")
summ = call("GET", "/admin/job-runner/summary")
workers = call("GET", "/admin/job-runner/workers")
before = call("GET", "/admin/job-runner/retention")
save("01_preflight.json", {"at": now(), "deploy_gate": gate, "summary": summ,
                           "workers": workers, "retention_before": before})
registered = {k["kind"] for k in (summ[1] or {}).get("kinds", [])}
missing = [k for k in KINDS if k not in registered]
print("deploy_gate", gate, "missing_kinds", missing)
if gate[0] != 200 or not gate[1].get("safe_to_deploy") or missing:
    print("NOT IDLE or kinds missing; stop"); sys.exit(2)

# 2. one DRY RUN per kind, sequential
runs = []
for kind in KINDS:
    t0 = time.time()
    st, enq = call("POST", "/admin/job-runner/retention/run", {"kind": kind, "dry_run": True})
    rec = {"kind": kind, "enqueue_status": st, "enqueue": enq, "enqueued_at": now()}
    print(kind, st, enq)
    if st != 200:
        runs.append(rec); continue
    jid = enq["job_id"]
    job = None
    for _ in range(120):  # up to ~10 min
        time.sleep(5)
        s, job = call("GET", f"/admin/job-runner/jobs/{jid}")
        if s == 200 and job.get("status") not in ("queued", "running"):
            break
    rec.update({"wall_seconds": round(time.time() - t0, 1), "job": job})
    print(kind, job.get("status") if job else None, (job or {}).get("result", {}) and
          {k: (job["result"] or {}).get(k) for k in ("mode", "candidates_total")})
    runs.append(rec)
save("02_runs.json", runs)

# 3. after
after = call("GET", "/admin/job-runner/retention")
gate2 = call("GET", "/admin/job-runner/deploy-gate")
save("03_after.json", {"at": now(), "retention_after": after, "deploy_gate": gate2})
del _secret, HDR
print("done")
