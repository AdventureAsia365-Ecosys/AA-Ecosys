"""S235 T9 checkpoint r5 driver — PREPARED, NOT RUN by the lane (paid runs are the orchestrator's).

r5 = n=20 T9 pieces on the SAME 6 angle-gate requests and chosen angles as S234 r4
(.tmp-session/s234/checkpoint_r4.json): blog x4 for atlas-hearth + terra-family (Mongolia route),
LinkedIn x3 for atlas-hearth (Punakha), terra-family (Paro Taktsang), trail-pulse (Kuang Si),
wildkind-travel (Punakha). Verifies live AA-776, AA-786, AA-774, AA-773, AA-775 (and AA-785).

Chạy bằng gì (how it runs): client-side from WSL. Every piece goes through the REAL tenant path
  POST /v1/content-writing/requests/{id}/write (tenant JWT from aa-cis/dev/e2e-tenant/<slug>)
  -> durable `t9_write` job on aa-cis-dev-worker (JOB_WORKER_IN_API=false). Nothing runs in the api
  task; the laptop only enqueues and polls. One piece in flight per request (same as r4: the writer's
  sibling-opener check reads earlier pieces of the same request), up to 6 requests in parallel.

Known confound (documented, plan r5-checkpoint): the r4 Terra LinkedIn angle "The Checkpoint Before the
Temple" rests on a practical card fact ("Visitors must leave cameras and bags at a checkpoint…") that
AA-774 now keeps out of the seed. Phase `regen` regenerates that ONE request's angles via the existing
admin path POST /admin/content-quality/requests/{id}/regenerate-angles (clone request + `t8_angles` job
on the worker, ~$0.02), then chooses the new recommended angle. Terra LinkedIn r4-vs-r5 is therefore
angle-confounded; every other cell keeps its r4 request + angle. r5 also includes the S234 card merge
(cards 122 -> 110), so seed changes are not only from the PRs.

Cost guard (pattern of .tmp-session/s235/t2_rerun/driver.py): cumulative = sum of shared.llm_call_log
cost over every r5 job (t9_write jobs + the t8_angles regen job), read through the admin endpoint
GET /admin/job-runner/jobs/{job_id}/llm-calls (totals.cost_usd).
  - before each enqueue: spent + open reserve (in-flight pieces: reserve - cost so far) + reserve(new)
    must stay <= HARD_STOP, else the piece is skipped (reported, never queued).
  - every poll: spent >= HARD_STOP -> cancel every open r5 job and exit 2.
  Reserve per piece = max(floor, worst piece seen in r5 for that channel). Floors from r4 actuals
  (blog max $0.119, LinkedIn max $0.037): blog $0.15, LinkedIn $0.05.

Secrets (never printed): tenant API keys from Secrets Manager aa-cis/dev/e2e-tenant/<slug> (profile
aa365-admin); admin secret from env CQ_SECRET, e.g.
  export CQ_SECRET=$(aws secretsmanager get-secret-value --secret-id aa-cis/dev/admin-secret --profile aa365-admin --region us-west-1 --query SecretString --output text)

Phases (state in checkpoint_r5.json next to this file; every phase is resumable):
  python3 r5_run.py init                 # seed state from r4 (same request_ids + chosen angles), $0
  python3 r5_run.py preflight [--expect-sha <sha>]   # shared.job idle + api/worker same image, $0
  python3 r5_run.py regen                # Terra LinkedIn new angles + choose recommended, ~$0.02
  python3 r5_run.py write --trial 3      # 3 pieces (Terra LI on the new angle, A&H blog, Trail LI), ~$0.20
  python3 r5_run.py write                # fill up to 20 pieces (trial pieces count), ~$0.95 more
  python3 r5_run.py status               # per-piece status + cost, cumulative
  python3 r5_run.py cancel               # emergency: cancel every open r5 job
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

API = "https://api-cis.lumiguides.it.com"
HERE = Path(__file__).resolve().parent
R4_STATE = HERE.parent.parent / "s234" / "checkpoint_r4.json"
STATE = HERE / "checkpoint_r5.json"
PROFILE, REGION = "aa365-admin", "us-west-1"
CLUSTER = "aa-cis-dev-cluster"
SERVICES = ("aa-cis-dev-api", "aa-cis-dev-worker")

HARD_STOP = 1.50                       # USD cumulative, all r5 jobs (orchestrator cap)
RESERVE_FLOOR = {"blog": 0.15, "linkedin": 0.05}
WRITES = {"blog": 4, "linkedin": 3}    # per request -> 2x4 + 4x3 = 20
CTA = {"atlas-hearth": "Talk to an Atlas & Hearth travel designer about this journey",
       "terra-family": "Ask Terra Family Expeditions to plan this trip for your family",
       "trail-pulse": "Get the full Trail Pulse itinerary and dates",
       "wildkind-travel": "Ask WildKind Travel for the full itinerary"}
CONFOUND_REQUEST = "ff45fd8a-a9e9-4881-ac8b-25aa25cee014"   # terra-family linkedin (r4 angle idx 0)
# --trial order: the regenerated Terra LI angle first (checks the confound fix), one route blog (checks
# Status lines / no practical bullets / F9 v1.1 / pace on a blog), one Trail Pulse LI (pace on LinkedIn).
TRIAL_ORDER = [("terra-family", "linkedin"), ("atlas-hearth", "blog"), ("trail-pulse", "linkedin")]
POLL_S = 30
PIECE_TIMEOUT_S = 25 * 60
RUN_TIMEOUT_S = 120 * 60
TERMINAL = {"succeeded", "failed", "cancelled", "stopped_budget", "stopped"}


# ── auth ────────────────────────────────────────────────────────────────────────────────────────

def admin_headers(role: bool = False) -> dict:
    secret = os.environ.get("CQ_SECRET")
    if not secret:
        sys.exit("set CQ_SECRET (admin secret, aa-cis/dev/admin-secret) in the environment first")
    h = {"X-Admin-Secret": secret}
    if role:  # regenerate-angles requires the admin staff role (BFF header)
        h.update({"x-admin-role": "admin", "x-admin-user-id": "s235-r5-checkpoint"})
    return h


_tokens: dict[str, dict] = {}


def tenant_headers(slug: str, fresh: bool = False) -> dict:
    if fresh or slug not in _tokens:
        key = subprocess.check_output(
            ["aws", "secretsmanager", "get-secret-value", "--secret-id", f"aa-cis/dev/e2e-tenant/{slug}",
             "--profile", PROFILE, "--region", REGION, "--query", "SecretString", "--output", "text"],
            text=True).strip()
        r = requests.post(f"{API}/auth/tenant-login", json={"api_key": key}, timeout=30)
        r.raise_for_status()
        _tokens[slug] = {"Authorization": f"Bearer {r.json()['token']}"}
    return _tokens[slug]


def tenant_call(method: str, slug: str, path: str, **kw) -> requests.Response:
    r = requests.request(method, f"{API}{path}", headers=tenant_headers(slug), timeout=60, **kw)
    if r.status_code == 401:  # JWT expired on a long run: log in again once
        r = requests.request(method, f"{API}{path}", headers=tenant_headers(slug, fresh=True), timeout=60, **kw)
    return r


# ── state ───────────────────────────────────────────────────────────────────────────────────────

def load() -> dict:
    if not STATE.exists():
        sys.exit(f"no {STATE.name} — run `init` first")
    return json.loads(STATE.read_text())


def save(state: dict) -> None:
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, ensure_ascii=False))
    tmp.replace(STATE)


def init(_args) -> None:
    if STATE.exists():
        sys.exit(f"{STATE.name} exists — refusing to overwrite (delete it by hand to start over)")
    r4 = json.loads(R4_STATE.read_text())
    reqs = []
    for r in r4["requests"]:
        reqs.append({"slug": r["slug"], "channel": r["channel"], "request_id": r["request_id"],
                     "r4_request_id": r["request_id"], "chosen": r.get("chosen"),
                     "chosen_angle": (r.get("angles") or [{}])[r["chosen"]].get("name")
                     if r.get("chosen") is not None and r.get("angles") else None,
                     "angles": r.get("angles"), "place": r.get("place"), "hub": r.get("hub")})
    state = {"round": "r5", "source": str(R4_STATE), "hard_stop_usd": HARD_STOP, "requests": reqs,
             "pieces": [], "regen": None, "skipped": [], "events": []}
    save(state)
    for r in reqs:
        print(f"{r['slug']:16} {r['channel']:8} {r['request_id']}  angle={r['chosen']}: {r['chosen_angle']}")
    print(f"state -> {STATE}  (pieces 0/20, nothing paid)")


# ── cost + status ───────────────────────────────────────────────────────────────────────────────

def job_ids(state: dict) -> list[str]:
    ids = [p["job_id"] for p in state["pieces"] if p.get("job_id")]
    if state.get("regen") and state["regen"].get("job_id"):
        ids.append(state["regen"]["job_id"])
    return ids


def refresh(state: dict) -> float:
    """Update each r5 piece (job_id, piece status, job status, cost) and the regen job; return spent."""
    h = admin_headers()
    for p in state["pieces"]:
        if p.get("done") and p.get("cost_final"):
            continue
        d = requests.get(f"{API}/admin/content-quality/pieces/{p['piece_id']}", headers=h, timeout=60)
        if d.ok:
            dj = d.json()
            p["job_id"] = p.get("job_id") or dj.get("job_id")
            p["status"], p["held_reason"] = dj.get("status"), dj.get("held_reason")
        if p.get("job_id"):
            j = requests.get(f"{API}/admin/job-runner/jobs/{p['job_id']}", headers=h, timeout=30)
            if j.ok:
                p["job_status"] = j.json().get("status")
            c = requests.get(f"{API}/admin/job-runner/jobs/{p['job_id']}/llm-calls", headers=h, timeout=30)
            if c.ok:
                p["cost_usd"] = float(c.json()["totals"].get("cost_usd") or 0)
        p["done"] = p.get("job_status") in TERMINAL and p.get("status") not in (None, "processing")
        p["cost_final"] = bool(p["done"])
    rg = state.get("regen")
    if rg and rg.get("job_id") and not rg.get("cost_final"):
        j = requests.get(f"{API}/admin/job-runner/jobs/{rg['job_id']}", headers=h, timeout=30)
        c = requests.get(f"{API}/admin/job-runner/jobs/{rg['job_id']}/llm-calls", headers=h, timeout=30)
        if j.ok:
            rg["job_status"] = j.json().get("status")
        if c.ok:
            rg["cost_usd"] = float(c.json()["totals"].get("cost_usd") or 0)
        rg["cost_final"] = rg.get("job_status") in TERMINAL
    save(state)
    spent = sum(p.get("cost_usd") or 0 for p in state["pieces"]) + ((rg or {}).get("cost_usd") or 0)
    return round(spent, 4)


def reserve(state: dict, channel: str) -> float:
    seen = [p.get("cost_usd") or 0 for p in state["pieces"] if p["channel"] == channel and p.get("done")]
    return max([RESERVE_FLOOR[channel]] + seen)


def open_reserve(state: dict) -> float:
    return sum(max(0.0, reserve(state, p["channel"]) - (p.get("cost_usd") or 0))
               for p in state["pieces"] if not p.get("done"))


def cancel_all(state: dict, _args=None) -> None:
    h = admin_headers()
    for jid, done in [(p.get("job_id"), p.get("done")) for p in state["pieces"]] + \
                     [((state.get("regen") or {}).get("job_id"), (state.get("regen") or {}).get("cost_final"))]:
        if jid and not done:
            r = requests.post(f"{API}/admin/job-runner/jobs/{jid}/cancel", headers=h, timeout=30)
            print("cancel", jid, r.status_code, r.text[:120])
    refresh(state)


# ── preflight ($0) ──────────────────────────────────────────────────────────────────────────────

def _aws(*args: str) -> str:
    return subprocess.check_output(["aws", *args, "--profile", PROFILE, "--region", REGION], text=True).strip()


def preflight(_state, args) -> None:
    ok = True
    gate = requests.get(f"{API}/admin/job-runner/deploy-gate", headers=admin_headers(), timeout=30)
    gate.raise_for_status()
    g = gate.json()
    print("shared.job active (queued+running):", {k: v for k, v in g.items() if k != "safe_to_deploy"})
    if not g.get("safe_to_deploy"):
        ok = False
        print("  NOT IDLE — wait for the queue to drain (also: do not deploy while r5 runs)")
    images = {}
    for svc in SERVICES:
        td = _aws("ecs", "describe-services", "--cluster", CLUSTER, "--services", svc,
                  "--query", "services[0].taskDefinition", "--output", "text")
        img = _aws("ecs", "describe-task-definition", "--task-definition", td,
                   "--query", "taskDefinition.containerDefinitions[0].image", "--output", "text")
        dep = _aws("ecs", "describe-services", "--cluster", CLUSTER, "--services", svc,
                   "--query", "services[0].deployments[0].rolloutState", "--output", "text")
        images[svc] = img
        print(f"{svc:20} {td.rsplit('/', 1)[-1]:28} rollout={dep:10} image={img.rsplit(':', 1)[-1]}")
        if dep != "COMPLETED":
            ok = False
    tags = {i.rsplit(":", 1)[-1] for i in images.values()}
    if len(tags) != 1:
        ok = False
        print("  api and worker run DIFFERENT images — t9_write runs on the worker; deploy both first")
    if args.expect_sha and not all(args.expect_sha in t for t in tags):
        ok = False
        print(f"  image tag does not contain the expected sha {args.expect_sha}")
    print("PREFLIGHT", "OK" if ok else "FAILED — do not run r5 yet")
    if not ok:
        sys.exit(1)


# ── regen (Terra LinkedIn, ~$0.02) ──────────────────────────────────────────────────────────────

def regen(state: dict, _args) -> None:
    req = next(r for r in state["requests"] if r["r4_request_id"] == CONFOUND_REQUEST)
    rg = state.get("regen")
    if rg and rg.get("chosen") is not None:
        print("regen already done:", rg["new_request_id"], "->", rg["chosen_angle"])
        return
    if not rg:
        r = requests.post(f"{API}/admin/content-quality/requests/{CONFOUND_REQUEST}/regenerate-angles",
                          headers=admin_headers(role=True), timeout=60)
        if r.status_code != 202:
            sys.exit(f"regenerate-angles {r.status_code}: {r.text[:300]}")
        body = r.json()
        rg = state["regen"] = {"old_request_id": CONFOUND_REQUEST, "new_request_id": body["request_id"],
                               "job_id": body["job_id"], "old_angle": req["chosen_angle"],
                               "why": "r4 angle rests on a practical card fact AA-774 removes (confound)"}
        save(state)
        print("regenerate-angles queued: new request", rg["new_request_id"], "job", rg["job_id"])
    started = time.time()
    while True:
        d = tenant_call("GET", req["slug"], f"/v1/angle-gate/requests/{rg['new_request_id']}")
        d.raise_for_status()
        dj = d.json()
        if dj.get("generation_failed"):
            sys.exit("t8_angles generation failed on the regenerated request — check /admin/jobs")
        if dj.get("status") != "pending_goal" and dj.get("angles"):
            break
        if time.time() - started > 15 * 60:
            sys.exit("angles not ready after 15 min — check the t8_angles job, then re-run `regen`")
        time.sleep(15)
    angles = dj["angles"]
    rec = next((a["idx"] for a in angles if a.get("recommended")), angles[0]["idx"])
    c = tenant_call("POST", req["slug"], f"/v1/angle-gate/requests/{rg['new_request_id']}/choose", json={"idx": rec})
    if c.status_code != 200:
        sys.exit(f"choose {c.status_code}: {c.text[:300]}")
    name = next(a["name"] for a in angles if a["idx"] == rec)
    rg.update({"chosen": rec, "chosen_angle": name,
               "angles": [{k: a.get(k) for k in ("idx", "name", "recommended")} for a in angles]})
    req.update({"request_id": rg["new_request_id"], "chosen": rec, "chosen_angle": name,
                "angles": rg["angles"], "confound": "angle regenerated for r5 (AA-774), r4 angle: "
                                                    + str(rg["old_angle"])})
    spent = refresh(state)
    print(f"Terra LinkedIn: r4 angle '{rg['old_angle']}' -> r5 angle #{rec} '{name}'  (regen cost ${spent:.3f})")
    for a in rg["angles"]:
        print(f"   {a['idx']} {'*' if a.get('recommended') else ' '} {a['name']}")


# ── write ───────────────────────────────────────────────────────────────────────────────────────

def _targets(state: dict, trial: int | None) -> dict[str, int]:
    """request_id -> how many r5 pieces it should have when this phase ends."""
    if trial:
        want = {}
        for slug, ch in TRIAL_ORDER[:trial]:
            r = next(x for x in state["requests"] if x["slug"] == slug and x["channel"] == ch)
            want[r["request_id"]] = 1
        return want
    return {r["request_id"]: WRITES[r["channel"]] for r in state["requests"]}


def write(state: dict, args) -> None:
    if not state.get("regen") or state["regen"].get("chosen") is None:
        sys.exit("run `regen` first (Terra LinkedIn angle must be regenerated before any write)")
    stop = min(HARD_STOP, args.hard_stop or HARD_STOP)
    want = _targets(state, args.trial)
    by_id = {r["request_id"]: r for r in state["requests"]}
    started = time.time()
    while True:
        spent = refresh(state)
        if spent >= stop:
            print(f"HARD STOP: cumulative ${spent:.3f} >= ${stop} — cancelling open r5 jobs")
            cancel_all(state)
            sys.exit(2)
        for rid, n in want.items():
            r = by_id[rid]
            mine = [p for p in state["pieces"] if p["request_id"] == rid]
            if len(mine) >= n or any(not p.get("done") for p in mine):
                continue
            if any(s["request_id"] == rid for s in state["skipped"]):
                continue
            need = spent + open_reserve(state) + reserve(state, r["channel"])
            if need > stop:
                msg = f"cost guard: spent ${spent:.3f} + open reserve + new > ${stop}"
                state["skipped"].append({"request_id": rid, "slug": r["slug"], "channel": r["channel"], "why": msg})
                print("SKIP", r["slug"], r["channel"], msg)
                save(state)
                continue
            w = tenant_call("POST", r["slug"], f"/v1/content-writing/requests/{rid}/write",
                            json={"cta": CTA[r["slug"]]})
            if w.status_code != 202:
                print("write failed", r["slug"], r["channel"], w.status_code, w.text[:200])
                state["skipped"].append({"request_id": rid, "slug": r["slug"], "channel": r["channel"],
                                         "why": f"write {w.status_code}: {w.text[:200]}"})
                save(state)
                continue
            pid = w.json()["piece_id"]
            state["pieces"].append({"slug": r["slug"], "channel": r["channel"], "request_id": rid,
                                    "piece_id": pid, "n": len(mine) + 1, "enqueued_at": time.time(),
                                    "trial": bool(args.trial), "job_id": None, "done": False})
            save(state)
            print(f"queued {r['slug']:16} {r['channel']:8} #{len(mine) + 1} piece={pid}")
        open_p = [p for p in state["pieces"] if not p.get("done")]
        have = sum(min(n, len([p for p in state["pieces"] if p["request_id"] == rid and p.get("done")]))
                   for rid, n in want.items())
        print(f"[{time.strftime('%H:%M:%S')}] done {have}/{sum(want.values())} open {len(open_p)} "
              f"spent ${spent:.3f} / ${stop}")
        blocked = {s["request_id"] for s in state["skipped"]}
        finished = all(len([p for p in state["pieces"] if p["request_id"] == rid and p.get("done")]) >= n
                       or rid in blocked for rid, n in want.items())
        if finished and not open_p:
            break
        for p in open_p:
            if time.time() - p["enqueued_at"] > PIECE_TIMEOUT_S and not p.get("timeout_warned"):
                p["timeout_warned"] = True
                print(f"WARN piece {p['piece_id']} open > {PIECE_TIMEOUT_S // 60} min (job {p.get('job_id')}) — "
                      "check /admin/jobs; the run keeps waiting")
        if time.time() - started > RUN_TIMEOUT_S:
            print("run timeout — jobs left running; check /admin/jobs, then `status` / re-run `write`")
            sys.exit(3)
        time.sleep(POLL_S)
    status(state, args)


def status(state: dict, _args=None) -> None:
    spent = refresh(state)
    for p in state["pieces"]:
        print(f"{p['slug']:16} {p['channel']:8} #{p['n']} {p['piece_id'][:8]} job={p.get('job_status')} "
              f"status={p.get('status')} held={p.get('held_reason') or '-'} ${p.get('cost_usd') or 0:.3f}"
              f"{' (trial)' if p.get('trial') else ''}")
    rg = state.get("regen") or {}
    if rg:
        print(f"regen t8_angles job={rg.get('job_status')} ${rg.get('cost_usd') or 0:.3f} -> '{rg.get('chosen_angle')}'")
    for s in state["skipped"]:
        print("skipped:", s)
    n = len(state["pieces"])
    print(f"pieces {n}/20 | cumulative ${spent:.3f} / hard stop ${HARD_STOP}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["init", "preflight", "regen", "write", "status", "cancel"])
    ap.add_argument("--trial", type=int, choices=[1, 2, 3])
    ap.add_argument("--hard-stop", type=float, help=f"lower the ${HARD_STOP} cap (never raises it)")
    ap.add_argument("--expect-sha", help="preflight: the image tag must contain this git sha")
    a = ap.parse_args()
    if a.phase == "init":
        return init(a)
    state = load()
    {"preflight": preflight, "regen": regen, "write": write, "status": status,
     "cancel": cancel_all}[a.phase](state, a)


if __name__ == "__main__":
    main()
