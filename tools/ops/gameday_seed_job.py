"""Game-day helper (AA-1023): seed or clear ONE harmless busy row in shared.job, to prove the job-idle gate.

Runs inside the CIS api container through tools/ecs/ecsx.sh (orchestrator only), with the container's own
DATABASE_URL (cis_app: INSERT/UPDATE on shared.job). It touches only rows it created itself
(kind noop_sleep, created_by GAMEDAY_TAG). noop_sleep is the Dev-only test kind: it sleeps and touches no data, and
the worker registers (and so claims) it ONLY while JOB_TEST_KINDS=1 is set on it (unset on Dev by default).
Whether the worker claims it (running) or not (queued, due now), the row makes shared.job busy for the DB Migrate
idle check, Migration Apply and the terraform-apply job-idle gate (not for the CIS deploy gate: not deploy_blocking).

    tools/ecs/ecsx.sh tools/ops/gameday_seed_job.py ACTION=seed      -> prints SEEDED id=<uuid> status=queued, then
                                                                        CLAIMED or UNCLAIMED (see below)
    tools/ecs/ecsx.sh tools/ops/gameday_seed_job.py ACTION=status    -> prints every row of this tag still open
    tools/ecs/ecsx.sh tools/ops/gameday_seed_job.py ACTION=clear     -> cancels every open row of this tag

ACTION=clear, then ACTION=status -> OPEN_COUNT 0, is MANDATORY before the game day ends. The row ends by itself after
SLEEP_SECONDS (default 900, 60..3600) ONLY when the worker runs noop_sleep (JOB_TEST_KINDS=1). With the normal Dev
config nothing claims it: it stays queued, due now, and blocks every gate above until it is cleared. After the insert
the seed watches the row for CLAIM_WAIT_SECONDS (default 15, 0..120) and prints CLAIMED (running: ends by itself) or
UNCLAIMED (still queued: clear it, it never ends by itself). ACTION=seed refuses when an open row of the tag exists.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

GAMEDAY_TAG = "aa1023-gameday"
KIND = "noop_sleep"

OPEN_SQL = """
SELECT id::text AS id, status, attempt, run_after, started_at, cancel_requested
  FROM shared.job
 WHERE kind = $1 AND created_by = $2 AND status IN ('queued', 'running')
 ORDER BY created_at"""
SEED_SQL = """
INSERT INTO shared.job (kind, payload, max_attempts, created_by)
VALUES ($1, $2::jsonb, 1, $3)
RETURNING id::text AS id, status, run_after"""
ROW_STATUS_SQL = "SELECT status FROM shared.job WHERE id = $1::uuid"
# A queued row is cancelled at once; a running one gets cancel_requested (the noop_sleep handler stops at its next
# progress write, within 5 s) so the worker ends it itself.
CANCEL_QUEUED_SQL = """
UPDATE shared.job SET status = 'cancelled', finished_at = now(), error = 'cancelled by the AA-1023 game day'
 WHERE kind = $1 AND created_by = $2 AND status = 'queued'
RETURNING id::text AS id"""
CANCEL_RUNNING_SQL = """
UPDATE shared.job SET cancel_requested = true
 WHERE kind = $1 AND created_by = $2 AND status = 'running'
RETURNING id::text AS id"""


def claim_wait_from_env(env) -> int:
    raw = (env.get("CLAIM_WAIT_SECONDS") or "15").strip()
    if not raw.isdigit() or not 0 <= int(raw) <= 120:
        raise ValueError("CLAIM_WAIT_SECONDS must be a whole number from 0 to 120")
    return int(raw)


def seconds_from_env(env) -> int:
    raw = (env.get("SLEEP_SECONDS") or "900").strip()
    if not raw.isdigit() or not 60 <= int(raw) <= 3600:
        raise ValueError("SLEEP_SECONDS must be a whole number from 60 to 3600")
    return int(raw)


async def watch_claim(conn, job_id: str, wait_s: int, sleep=asyncio.sleep) -> str:
    """The row's status after up to wait_s seconds (polled every second): 'running' once the worker claims it."""
    status = "queued"
    for _ in range(wait_s):
        await sleep(1)
        status = await conn.fetchval(ROW_STATUS_SQL, job_id)
        if status != "queued":
            break
    return status


async def run(conn, action: str, env, sleep=asyncio.sleep) -> int:
    open_rows = await conn.fetch(OPEN_SQL, KIND, GAMEDAY_TAG)
    if action == "status":
        for r in open_rows:
            print(f"OPEN id={r['id']} status={r['status']} attempt={r['attempt']} run_after={r['run_after']} "
                  f"started_at={r['started_at']} cancel_requested={r['cancel_requested']}")
        print(f"OPEN_COUNT {len(open_rows)}")
        return 0
    if action == "seed":
        if open_rows:
            print(f"REFUSED: {len(open_rows)} open row(s) of {GAMEDAY_TAG} already exist (first {open_rows[0]['id']})")
            return 1
        seconds = seconds_from_env(env)
        wait_s = claim_wait_from_env(env)
        row = await conn.fetchrow(SEED_SQL, KIND, json.dumps({"seconds": seconds}), GAMEDAY_TAG)
        print(f"SEEDED id={row['id']} kind={KIND} status={row['status']} seconds={seconds} run_after={row['run_after']}")
        status = await watch_claim(conn, row["id"], wait_s, sleep)
        if status == "running":
            print(f"CLAIMED id={row['id']}: the worker runs {KIND}; it ends by itself after {seconds} s. "
                  "Still run ACTION=clear and ACTION=status (OPEN_COUNT 0) when the drill is done.")
        elif status == "queued":
            print(f"UNCLAIMED id={row['id']} after {wait_s} s: no worker runs {KIND} (JOB_TEST_KINDS is off). "
                  "The row stays queued and blocks DB Migrate, Migration Apply and the terraform-apply job-idle gate "
                  "until ACTION=clear. It NEVER ends by itself: clear it, then ACTION=status must print OPEN_COUNT 0.")
        else:
            print(f"ENDED id={row['id']} status={status} already: re-seed only if the drill still needs a busy row.")
        return 0
    if action == "clear":
        queued = await conn.fetch(CANCEL_QUEUED_SQL, KIND, GAMEDAY_TAG)
        running = await conn.fetch(CANCEL_RUNNING_SQL, KIND, GAMEDAY_TAG)
        print(f"CLEARED queued_cancelled={len(queued)} running_cancel_requested={len(running)}")
        return 0
    print(f"unknown ACTION {action!r} (seed, status, clear)")
    return 2


async def main() -> int:
    import asyncpg  # inside the container only; the unit tests use a fake connection

    action = (os.environ.get("ACTION") or "status").strip()
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        return await run(conn, action, os.environ)
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
