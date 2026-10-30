"""When did each LLM account / connection last answer a billed call? Read-only.

Playbook: docs/ops/playbooks/llm-access-denied.md (OPS-04-llm-access-denied), step 2.

Runs inside the CIS api (or worker) container through tools/ecs/ecsx.sh:
    tools/ecs/ecsx.sh tools/llm/llm_last_ok.py [LAST_OK_DAYS=7] [LAST_OK_ACCOUNT=<account label>]
Uses the container's DATABASE_URL (cis_app) and reads shared.llm_call_log only. No LLM call, no write, no cost.

A refused call leaves no shared.llm_call_log row, so "last billed call" (cost_usd > 0) is the last time the
provider answered for that account. Prints one JSON line per account (last_ok, calls in the window), then, for
LAST_OK_ACCOUNT (default: the account with the oldest last_ok), the billed calls per hour around its last success.
"""
import asyncio
import json
import os

import asyncpg

DAYS = int(os.environ.get("LAST_OK_DAYS", "7"))
ACCOUNT = os.environ.get("LAST_OK_ACCOUNT") or None

PER_ACCOUNT_SQL = """
SELECT account, max(created_at) AS last_ok,
       count(*) FILTER (WHERE created_at > now() - make_interval(days => $1)) AS calls_in_window
FROM shared.llm_call_log
WHERE account IS NOT NULL AND cost_usd > 0
GROUP BY 1 ORDER BY 2 DESC
"""

HOURLY_SQL = """
SELECT date_trunc('hour', created_at) AS hour, count(*) AS calls, round(sum(cost_usd), 4) AS usd
FROM shared.llm_call_log
WHERE account = $1 AND cost_usd > 0 AND created_at > $2::timestamptz - interval '1 day'
GROUP BY 1 ORDER BY 1 DESC LIMIT 12
"""


def _row(r):
    return {k: (v.isoformat() if hasattr(v, "isoformat") else (float(v) if k == "usd" else v)) for k, v in r.items()}


async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        rows = await conn.fetch(PER_ACCOUNT_SQL, DAYS)
        for r in rows:
            print(json.dumps({"window_days": DAYS, **_row(r)}))
        target = ACCOUNT or (rows[-1]["account"] if rows else None)
        last = next((r["last_ok"] for r in rows if r["account"] == target), None)
        if target and last:
            for r in await conn.fetch(HOURLY_SQL, target, last):
                print(json.dumps({"account": target, **_row(r)}))
    finally:
        await conn.close()


asyncio.run(main())
