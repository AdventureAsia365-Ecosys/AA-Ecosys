# S261 AA-1003: read-only report register + latest run per report (admin API inside the CIS api container).
import json, os, urllib.request
BASE = "http://127.0.0.1:8000"
H = {"x-admin-secret": os.environ["ADMIN_SECRET"], "x-admin-role": "admin", "x-admin-user-id": "s261-orchestrator"}
def get(p):
    with urllib.request.urlopen(urllib.request.Request(BASE + p, headers=H), timeout=30) as r:
        return json.loads(r.read())
reg = get("/admin/reports")
items = reg.get("reports") if isinstance(reg, dict) else reg
print("KEYS", list(reg.keys())[:10] if isinstance(reg, dict) else type(reg).__name__, "n", len(items or []))
for it in items or []:
    lr = it.get("last_run") or {}
    print("REP", json.dumps({k: it.get(k) for k in ("report_id", "id", "slice", "status", "cadence", "due", "due_state")}, default=str),
          json.dumps({k: lr.get(k) for k in ("id", "status", "trigger", "started_at", "finished_at", "period")}, default=str))
