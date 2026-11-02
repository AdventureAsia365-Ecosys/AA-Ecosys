"""Game-day helper (AA-1023): seed or clear ONE harmless busy row in shared.job, to prove the job-idle gate.

Runs inside the CIS api container through tools/ecs/ecsx.sh (orchestrator only), with the container's own
DATABASE_URL (cis_app: INSERT/UPDATE on shared.job). It touches only rows it created itself
(kind noop_sleep, created_by GAMEDAY_TAG). noop_sleep is the Dev-only test kind (JOB_TEST_KINDS=1): it sleeps and
touches no data. Whether the worker claims it (running) or not (queued, due now), the row makes shared.job busy for
the DB Migrate idle check and the terraform-apply job-idle gate.

    tools/ecs/ecsx.sh tools/ops/gameday_seed_job.py ACTION=seed      -> prints SEEDED id=<uuid> status=queued
    tools/ecs/ecsx.sh tools/ops/gameday_seed_job.py ACTION=status    -> prints every row of this tag still open
    tools/ecs/ecsx.sh tools/ops/gameday_seed_job.py ACTION=clear     -> cancels every open row of this tag

ACTION=seed refuses when an open row of the tag already exists (one busy row is enough). Optional SLEEP_SECONDS (default
900, 60..3600) is the sleep length; the row ends by itself after it, so a forgotten clear frees the queue anyway.
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


def seconds_from_env(env) -> int:
    raw = (env.get("SLEEP_SECONDS") or "900").strip()
    if not raw.isdigit() or not 60 <= int(raw) <= 3600:
        raise ValueError("SLEEP_SECONDS must be a whole number from 60 to 3600")
    return int(raw)


async def run(conn, action: str, env) -> int:
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
        row = await conn.fetchrow(SEED_SQL, KIND, json.dumps({"seconds": seconds}), GAMEDAY_TAG)
        print(f"SEEDED id={row['id']} kind={KIND} status={row['status']} seconds={seconds} run_after={row['run_after']}")
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
