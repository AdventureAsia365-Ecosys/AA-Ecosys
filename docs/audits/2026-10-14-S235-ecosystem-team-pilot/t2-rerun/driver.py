"""S235 T2 rerun driver (AA-792 + AA-794) — DESIGNED, NOT RUN by the lane implementer.

Re-runs the 14 S234 tour x tenant T2 rewrites through the REAL tenant path (POST
/v1/tours/pool/{published_tour_id}/rewrite -> durable `t2_rewrite` job on the worker), in waves of
4 / 8 / 2, with a hard stop at $4.50 cumulative LLM cost (sum of shared.llm_call_log.cost_usd over
the rerun job ids, read through GET /admin/job-runner/jobs/{id}/llm-calls).

Run it from WSL, after AA-794 + AA-792 are deployed (api AND worker on the same SHA) and
`shared.job` has no queued/running work. Paid: ~$2.8-4.2 expected, $4.50 hard stop (Nghiệp approved
<= $5 for this rerun). Each run creates a new tenant_tour_versions row and counts against the
tenant's monthly rewrite quota (AA-640: over quota is allowed and billed in trial).

Secrets (never printed):
  - tenant API keys: Secrets Manager aa-cis/dev/e2e-tenant/<slug> (read with profile aa365-admin)
  - admin secret: env CQ_SECRET (same as the S233/S234 analyze scripts)

Phases (state in state.json next to this file; every phase is re-runnable / resumable):
  python3 driver.py resolve        # S234 version -> published_tour_id via the tenant API (GET, $0)
  python3 driver.py run --wave 1   # wave 1 (4 runs, Bhutan x 4 tenants) — the pilot; STOP and read
  python3 driver.py run --wave 2   # wave 2 (8 runs: Mongolia + Laos->Vietnam x 4 tenants)
  python3 driver.py run --wave 3   # wave 3 (2 runs: Bhutan repeats for Terra + WildKind = A/A')
  python3 driver.py status         # job status + cost per run, cumulative cost
  python3 driver.py cancel         # cancel every queued/running rerun job (emergency stop)

Cost guard:
  - before each enqueue: spent + reserve(n_unfinished + 1) must stay <= HARD_STOP, where reserve is
    the worst per-version cost seen so far in this rerun (floor $0.45 — S234 mean $0.372); a run
    that does not fit is skipped and reported, never queued.
  - while a wave runs: poll every POLL_S seconds; when spent >= HARD_STOP, cancel every queued or
    running rerun job and exit non-zero.
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
PAIRS = HERE / "pairs.json"
STATE = HERE / "state.json"
HARD_STOP = 4.50          # USD, cumulative over all rerun jobs
RESERVE_FLOOR = 0.45      # USD, worst-case cost of one more version before any is measured
POLL_S = 60               # seconds between status/cost polls inside a wave
WAVE_TIMEOUT_S = 40 * 60  # a T2 job is ~3-6 min; a wave that takes 40 min is stuck
TERMINAL = {"succeeded", "failed", "cancelled", "stopped_budget", "stopped"}


def _admin_headers() -> dict:
    secret = os.environ.get("CQ_SECRET")
    if not secret:
        sys.exit("set CQ_SECRET (admin secret) in the environment first")
    return {"X-Admin-Secret": secret}


_tokens: dict[str, dict] = {}


def tenant_headers(slug: str) -> dict:
    if slug not in _tokens:
        key = subprocess.check_output(
            ["aws", "secretsmanager", "get-secret-value", "--secret-id", f"aa-cis/dev/e2e-tenant/{slug}",
             "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"],
            text=True).strip()
        r = requests.post(f"{API}/auth/tenant-login", json={"api_key": key}, timeout=30)
        r.raise_for_status()
        _tokens[slug] = {"Authorization": f"Bearer {r.json()['token']}"}
    return _tokens[slug]


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    pairs = json.loads(PAIRS.read_text())["runs"]
    return {"runs": [{**p, "published_tour_id": None, "version_id": None, "job_id": None,
                      "job_status": None, "cost_usd": 0.0, "skipped": None} for p in pairs]}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=1, ensure_ascii=False))


# ── phase: resolve ──────────────────────────────────────────────────────────────────────────

def resolve(state: dict) -> None:
    for run in state["runs"]:
        if run["published_tour_id"]:
            continue
        r = requests.get(f"{API}/v1/tours/versions/{run['s234_version_id']}",
                         headers=tenant_headers(run["slug"]), timeout=30)
        r.raise_for_status()
        run["published_tour_id"] = r.json()["published_tour_id"]
        print(f"{run['slug']:16} {run['country']:9} {run['s234_version_id'][:8]} -> {run['published_tour_id']}")
    save_state(state)


# ── cost + status ───────────────────────────────────────────────────────────────────────────

def refresh(state: dict) -> float:
    """Update job_status + cost_usd for every enqueued run; return cumulative cost."""
    h = _admin_headers()
    for run in state["runs"]:
        if not run["job_id"]:
            continue
        job = requests.get(f"{API}/admin/job-runner/jobs/{run['job_id']}", headers=h, timeout=30)
        job.raise_for_status()
        run["job_status"] = job.json().get("status")
        run["job_result"] = job.json().get("result")
        calls = requests.get(f"{API}/admin/job-runner/jobs/{run['job_id']}/llm-calls", headers=h, timeout=30)
        calls.raise_for_status()
        run["cost_usd"] = float(calls.json()["totals"]["cost_usd"] or 0)
    save_state(state)
    return round(sum(r["cost_usd"] for r in state["runs"]), 4)


def reserve(state: dict) -> float:
    done = [r["cost_usd"] for r in state["runs"] if r.get("job_status") in TERMINAL and r["cost_usd"] > 0]
    return max([RESERVE_FLOOR] + done)


def cancel_all(state: dict) -> None:
    h = _admin_headers()
    for run in state["runs"]:
        if run["job_id"] and run.get("job_status") not in TERMINAL:
            r = requests.post(f"{API}/admin/job-runner/jobs/{run['job_id']}/cancel", headers=h, timeout=30)
            print("cancel", run["job_id"], r.status_code, r.text[:120])
    refresh(state)


# ── phase: run ──────────────────────────────────────────────────────────────────────────────

def run_wave(state: dict, wave: int) -> None:
    runs = [r for r in state["runs"] if r["wave"] == wave]
    if any(not r["published_tour_id"] for r in runs):
        sys.exit("run `resolve` first")
    spent = refresh(state)
    for run in runs:
        if run["job_id"]:
            continue  # resumable: already enqueued
        in_flight = sum(1 for r in state["runs"] if r["job_id"] and r.get("job_status") not in TERMINAL)
        if spent + reserve(state) * (in_flight + 1) > HARD_STOP:
            run["skipped"] = f"cost guard: spent ${spent:.2f} + reserve x{in_flight + 1} > ${HARD_STOP}"
            print("SKIP", run["slug"], run["country"], run["skipped"])
            continue
        r = requests.post(f"{API}/v1/tours/pool/{run['published_tour_id']}/rewrite",
                          headers=tenant_headers(run["slug"]),
                          json={"rewrite_language": run["rewrite_language"], "seo_mode": run["seo_mode"]},
                          timeout=60)
        if r.status_code != 200:
            run["skipped"] = f"trigger {r.status_code}: {r.text[:200]}"
            print("SKIP", run["slug"], run["country"], run["skipped"])
            continue
        body = r.json()
        run["version_id"], run["job_id"], run["job_status"] = body["version_id"], body["job_id"], "queued"
        print(f"queued {run['slug']:16} {run['country']:9} version={run['version_id']} job={run['job_id']}")
        save_state(state)

    started = time.time()
    while True:
        spent = refresh(state)
        open_runs = [r for r in runs if r["job_id"] and r.get("job_status") not in TERMINAL]
        print(f"[{time.strftime('%H:%M:%S')}] wave {wave}: {len(open_runs)} open, cumulative ${spent:.3f}")
        if spent >= HARD_STOP:
            print(f"HARD STOP: cumulative ${spent:.3f} >= ${HARD_STOP} — cancelling open rerun jobs")
            cancel_all(state)
            sys.exit(2)
        if not open_runs:
            break
        if time.time() - started > WAVE_TIMEOUT_S:
            print("wave timeout — leaving jobs running; check /admin/jobs, then `status`")
            sys.exit(3)
        time.sleep(POLL_S)
    for r in runs:
        print(f"{r['slug']:16} {r['country']:9} job={r.get('job_status')} cost=${r['cost_usd']:.3f} "
              f"result={json.dumps(r.get('job_result'))[:160]}")
    print(f"wave {wave} done — cumulative ${spent:.3f} of ${HARD_STOP} hard stop")


def status(state: dict) -> None:
    spent = refresh(state)
    for r in state["runs"]:
        print(f"w{r['wave']} {r['slug']:16} {r['country']:9} job={r.get('job_status')} "
              f"cost=${r['cost_usd']:.3f} version={r.get('version_id')} skipped={r.get('skipped')}")
    print(f"cumulative ${spent:.3f} / hard stop ${HARD_STOP}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["resolve", "run", "status", "cancel"])
    ap.add_argument("--wave", type=int, choices=[1, 2, 3, 4])
    a = ap.parse_args()
    state = load_state()
    if a.phase == "resolve":
        resolve(state)
    elif a.phase == "run":
        if not a.wave:
            sys.exit("--wave is required")
        run_wave(state, a.wave)
    elif a.phase == "status":
        status(state)
    else:
        cancel_all(state)


if __name__ == "__main__":
    main()
