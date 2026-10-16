"""S239 AA-825: read-only context for the retention_job DRY RUN (oldest finished jobs per status). GET only."""
import json, subprocess, sys, urllib.request
API = "https://api-cis.lumiguides.it.com"
s = subprocess.run(["aws", "secretsmanager", "get-secret-value", "--secret-id", "aa-cis/dev/admin-secret", "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], capture_output=True, text=True, check=True).stdout.strip()
H = {"X-Admin-Secret": s}
def get(p):
    with urllib.request.urlopen(urllib.request.Request(API + p, headers=H), timeout=60) as r:
        return json.loads(r.read())
out = {}
for st in ("succeeded", "failed", "cancelled", "stopped_budget"):
    j = get(f"/admin/job-runner/jobs?status={st}&sort=finished_at&sort_dir=asc&page_size=3")
    out[st] = {"total": j["total"], "oldest": [{k: x.get(k) for k in ("kind", "created_at", "finished_at")} for x in j["jobs"]]}
j = get("/admin/job-runner/jobs?sort=created_at&sort_dir=asc&page_size=1")
out["oldest_created_any"] = [{k: x.get(k) for k in ("kind", "status", "created_at", "finished_at")} for x in j["jobs"]]
out["succeeded_created_before_2026-09-16"] = get("/admin/job-runner/jobs?status=succeeded&until=2026-09-16T00:00:00%2B00:00&page_size=1")["total"]
out["failed_created_before_2026-07-18"] = get("/admin/job-runner/jobs?status=failed&until=2026-07-18T00:00:00%2B00:00&page_size=1")["total"]
del s, H
json.dump(out, open(sys.argv[1], "w"), indent=1)
print(json.dumps(out, indent=1))
