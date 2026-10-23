# AA-896 (S248) read-only, run by the orchestrator through the S3-mediated ECS exec (docs/ops/runbooks/ecs-exec-s3-mediated.md).
# Output: s3://aa-cis-bronze-005097885195/scripts/aa896_result.json. For the refresh after 01/11 set MONTHS' last end to 2026-11-01.
# LLM spend by month/app/account/stage/model + unit-cost denominators. SELECT only.
import asyncio
import datetime
import decimal
import json
import os

import asyncpg
import boto3

MONTHS = [("2026-08", "2026-08-01", "2026-09-01"), ("2026-09", "2026-09-01", "2026-10-01"), ("2026-10", "2026-10-01", "2026-10-23")]
U = """
WITH u AS (
  SELECT d.day::timestamp AS ts, d.stage, d.role, d.model, d.account, d.provider, d.calls, d.cost_usd
    FROM shared.llm_call_daily d WHERE d.day >= $1::date AND d.day < $2::date
  UNION ALL
  SELECT l.created_at AT TIME ZONE 'UTC', l.stage, l.role, l.model, l.account, l.provider, 1, coalesce(l.cost_usd, 0)
    FROM shared.llm_call_log l
   WHERE l.created_at >= ($1::date::timestamp AT TIME ZONE 'UTC') AND l.created_at < ($2::date::timestamp AT TIME ZONE 'UTC')
     AND NOT EXISTS (SELECT 1 FROM shared.llm_call_daily d WHERE d.day = (l.created_at AT TIME ZONE 'UTC')::date))
"""
Q = {
  "by_app_account": U + (
        "SELECT CASE WHEN stage LIKE 'tp\\_%' THEN 'tripplanner' ELSE 'cis' END AS app,"
        " coalesce(account,'acc2') AS account, coalesce(provider,'?') AS provider,"
        " sum(calls)::bigint AS calls, round(sum(cost_usd)::numeric,4) AS cost_usd"
        " FROM u GROUP BY 1,2,3 ORDER BY 5 DESC"
    ),
  "by_stage": U + "SELECT stage, sum(calls)::bigint AS calls, round(sum(cost_usd)::numeric,4) AS cost_usd FROM u GROUP BY 1 ORDER BY 3 DESC LIMIT 25",
  "by_model": U + (
        "SELECT model, coalesce(account,'acc2') AS account, sum(calls)::bigint AS calls,"
        " round(sum(cost_usd)::numeric,4) AS cost_usd FROM u GROUP BY 1,2 ORDER BY 4 DESC LIMIT 20"
    ),
  "by_day": U + "SELECT ts::date AS day, sum(calls)::bigint AS calls, round(sum(cost_usd)::numeric,4) AS cost_usd FROM u GROUP BY 1 ORDER BY 1",
  "published_tours": (
        "SELECT count(*) AS n, count(*) FILTER (WHERE deleted_at IS NULL) AS live"
        " FROM gold_aa_internal.published_tours"
        " WHERE published_at >= ($1::date::timestamp AT TIME ZONE 'UTC')"
        " AND published_at < ($2::date::timestamp AT TIME ZONE 'UTC')"
    ),
  "dfs": (
        "SELECT count(*) AS calls, round(coalesce(sum(cost_usd),0)::numeric,4) AS cost_usd"
        " FROM shared.dfs_call_log"
        " WHERE created_at >= ($1::date::timestamp AT TIME ZONE 'UTC')"
        " AND created_at < ($2::date::timestamp AT TIME ZONE 'UTC')"
    ),
  "geocode": (
        "SELECT provider, count(*) AS calls, round(coalesce(sum(cost_usd),0)::numeric,4) AS cost_usd"
        " FROM geo.geocode_call"
        " WHERE called_at >= ($1::date::timestamp AT TIME ZONE 'UTC')"
        " AND called_at < ($2::date::timestamp AT TIME ZONE 'UTC')"
        " GROUP BY 1"
    ),
  "jev_decision_log": (
        "SELECT count(*) FILTER (WHERE NOT cached) AS calls, round(coalesce(sum(cost_usd),0)::numeric,4) AS cost_usd"
        " FROM shared.decision_log"
        " WHERE created_at >= ($1::date::timestamp AT TIME ZONE 'UTC')"
        " AND created_at < ($2::date::timestamp AT TIME ZONE 'UTC')"
    ),
  "content_pieces": (
        "SELECT coalesce(channel,'?') AS channel, status, count(*) AS n"
        " FROM acp_shared.content_piece"
        " WHERE created_at >= ($1::date::timestamp AT TIME ZONE 'UTC')"
        " AND created_at < ($2::date::timestamp AT TIME ZONE 'UTC')"
        " GROUP BY 1,2"
        " ORDER BY 3 DESC"
    ),
}


def j(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    return v


async def main():
    out = {}
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        await conn.execute("SET default_transaction_read_only = on")
        for m, a, b in MONTHS:
            out[m] = {}
            for k, sql in Q.items():
                try:
                    rows = await conn.fetch(sql, a, b)
                    out[m][k] = [{kk: j(vv) for kk, vv in dict(r).items()} for r in rows]
                except Exception as e:
                    out[m][k] = {"error": type(e).__name__ + ": " + str(e)[:200]}
    finally:
        await conn.close()
    with open("/tmp/aa896_result.json", "w") as f:
        json.dump(out, f)
    boto3.client("s3", region_name="us-west-1").upload_file("/tmp/aa896_result.json", "aa-cis-bronze-005097885195", "scripts/aa896_result.json")
    print("ok", sum(len(v) for v in out.values()))


asyncio.run(main())
