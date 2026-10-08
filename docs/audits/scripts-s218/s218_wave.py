"""S218 wave runner: SEO prefetch (one job) -> enqueue s1_rewrite for every id -> poll until terminal.
usage: python3 s218_wave.py <ids.json> <out.json>    (ADMIN_SECRET in env)"""
import json, os, sys, time, urllib.request
A = "https://api-cis.lumiguides.it.com"
T = "00000000-0000-0000-0000-000000000001"
BRAND = ("e0138a58-62b0-49cb-8b16-159bf2436f5a", "default")
H = {"X-Admin-Secret": os.environ["ADMIN_SECRET"], "Content-Type": "application/json", "x-admin-user-id": "claude-code-s218"}

def call(method, path, body=None):
    req = urllib.request.Request(A + path, method=method, headers=H,
                                 data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def job(jid):
    return call("GET", f"/admin/job-runner/jobs/{jid}")

ids = json.load(open(sys.argv[1])); out = sys.argv[2]
log = {"ids": ids, "t0": time.time()}
BATCH = os.environ.get("BATCH", T)  # a new batch_id = a regenerate (idempotency key includes it)
pf = call("POST", "/admin/s1/seo-prefetch", {"tour_ids": ids, "tenant_id": T})
print("prefetch job", pf, flush=True)
while True:
    j = job(pf["job_id"]); st = j.get("status") or j.get("job", {}).get("status")
    if st in ("succeeded", "failed", "stopped_budget", "cancelled"): break
    time.sleep(30)
log["prefetch"] = {"status": st, "secs": round(time.time() - log["t0"])}
print("prefetch", log["prefetch"], flush=True)
if st != "succeeded":
    json.dump(log, open(out, "w"), indent=1); sys.exit(1)
jobs = {}
for tid in ids:
    r = call("POST", "/admin/run-tour-async", {"tour_id": tid, "batch_id": BATCH, "tenant_id": T, "seo_mode": "standard",
                                               "model_tier": os.environ.get("MODEL") or None, "brand_identity_id": BRAND[0], "brand_name": BRAND[1]})
    jobs[tid] = r.get("job_id")
log["t_enqueued"] = time.time(); log["jobs"] = jobs
print("enqueued", len(jobs), flush=True)
done = {}
while len(done) < len(jobs):
    time.sleep(60)
    for tid, jid in jobs.items():
        if tid in done or not jid: continue
        try:
            j = job(jid); jj = j.get("job", j)
        except Exception as e:
            print(time.strftime("%H:%M"), "poll_error", type(e).__name__, flush=True); break
        if jj.get("status") in ("succeeded", "failed", "cancelled", "stopped_budget"):
            done[tid] = {"status": jj["status"], "error": (jj.get("error") or "")[:200]}
    print(time.strftime("%H:%M"), "done", len(done), "/", len(jobs), flush=True)
    log["done"] = done; json.dump(log, open(out, "w"), indent=1)
log["t_s1_done"] = time.time(); json.dump(log, open(out, "w"), indent=1)
print("S1 finished in", round((log["t_s1_done"] - log["t_enqueued"]) / 60, 1), "min", flush=True)
