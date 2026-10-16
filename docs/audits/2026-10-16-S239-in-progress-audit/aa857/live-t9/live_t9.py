"""AA-857 S239 — one live T9 write on a fixed Subject (terra-family, LinkedIn).

Subject 3833fa3d-9587-4e18-9dff-804652bf717d: Segment 50870fc4cfa77887 "Traditional Arts & Craft School",
seed atom c64ebfc5d8c3b815 (Thimphu, Bhutan). Before AA-857 the place shared a Segment with "National Library".

Flow (tenant API only, same as the AA-668 run): slate read -> POST /v1/subjects/{id}/pick ->
POST angle-gate goal (t8_angles job) -> poll until angles -> choose idx 0 -> POST content-writing write
(t9_write job) -> poll piece until ready/held -> read piece, latest-piece, review.
Each paid POST is sent at most once. The api_key and JWT are never printed or written.
"""
import json
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timezone

import requests

API = "https://api-cis.lumiguides.it.com"
OUT = pathlib.Path(__file__).resolve().parent / "raw"
OUT.mkdir(exist_ok=True)
SUBJECT = "3833fa3d-9587-4e18-9dff-804652bf717d"
GOAL = "introduction_awareness"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def secret(name):
    return subprocess.check_output(
        ["aws", "secretsmanager", "get-secret-value", "--secret-id", name, "--profile", "aa365-admin",
         "--region", "us-west-1", "--query", "SecretString", "--output", "text"], text=True).strip()


def call(method, path, h, name, **kw):
    t = now()
    r = requests.request(method, API + path, headers=h, timeout=90, **kw)
    try:
        body = r.json()
    except ValueError:
        body = r.text[:2000]
    rec = {"at": t, "method": method, "path": path, "status": r.status_code, "body": body}
    if "json" in kw:
        rec["request_body"] = kw["json"]
    (OUT / f"{name}.json").write_text(json.dumps(rec, indent=1, default=str))
    print(f"{t} {method} {path} -> {r.status_code}", flush=True)
    return r.status_code, body


r = requests.post(API + "/auth/tenant-login", json={"api_key": secret("aa-cis/dev/e2e-tenant/terra-family")}, timeout=30)
r.raise_for_status()
j = r.json()
print("tenant_id", j["tenant_id"])
H = {"Authorization": "Bearer " + j["token"]}

# 0. slate read (read-only): is the subject there and 'proposed'?
st, slate = call("GET", "/v1/slate", H, "00_slate")
hit = None
def walk(o):
    global hit
    if isinstance(o, dict):
        if o.get("subject_id") == SUBJECT:
            hit = o
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)
walk(slate)
(OUT / "00_subject_in_slate.json").write_text(json.dumps(hit, indent=1, default=str))
print("subject in slate:", json.dumps(hit, default=str)[:600])

# 1. pick
st, pick = call("POST", f"/v1/subjects/{SUBJECT}/pick", H, "01_pick")
if st != 200:
    print("PICK REFUSED", st, json.dumps(pick)[:1000])
    sys.exit(2)
rid = pick.get("request_id") or (pick.get("request") or {}).get("request_id") or pick.get("angle_gate_request_id")
print("request_id", rid, "pick keys", list(pick.keys()))
if not rid:
    sys.exit(3)

# 2. goal (t8_angles) — once
st, g = call("POST", f"/v1/angle-gate/requests/{rid}/goal", H, "02_goal", json={"goal": GOAL})
if st != 202:
    sys.exit(4)
for i in range(40):
    time.sleep(6)
    st, req = call("GET", f"/v1/angle-gate/requests/{rid}", H, "03_request_poll")
    if st == 200 and (req.get("status") != "pending_goal" or req.get("generation_failed")):
        break
(OUT / "03_request_angles.json").write_text(json.dumps(req, indent=1, default=str))
if req.get("generation_failed") or req.get("status") == "pending_goal":
    print("angles not ready", req.get("status"), req.get("generation_failed"))
    sys.exit(5)

# 3. choose first angle
st, ch = call("POST", f"/v1/angle-gate/requests/{rid}/choose", H, "04_choose", json={"idx": 0})
if st != 200:
    sys.exit(6)

# 4. write (t9_write) — once
st, w = call("POST", f"/v1/content-writing/requests/{rid}/write", H, "05_write", json={})
if st != 202:
    sys.exit(7)
pid = w["piece_id"]
for i in range(60):
    time.sleep(8)
    st, p = call("GET", f"/v1/content-writing/pieces/{pid}", H, "06_piece_poll")
    if st == 200 and p.get("ready_state") not in ("in_progress", "processing", None):
        break
call("GET", f"/v1/content-writing/pieces/{pid}", H, "07_piece_final")
call("GET", f"/v1/content-writing/requests/{rid}/latest-piece", H, "08_latest_piece")
call("GET", f"/v1/content-writing/requests/{rid}/review", H, "09_review")
call("GET", f"/v1/progress/piece/{pid}", H, "10_progress")
call("GET", f"/v1/angle-gate/requests/{rid}", H, "11_request_final")
print(json.dumps({"request_id": rid, "piece_id": pid}))
