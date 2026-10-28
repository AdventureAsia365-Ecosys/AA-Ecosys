"""AA-896 (S255) — READ-ONLY unit-cost query for the Aug/Sep/Oct 2026 cost report.

Runs inside the CIS api/worker container (S3-mediated ECS exec) with the container's DATABASE_URL
(role cis_app). SELECT only, ssl="require". Prints one JSON document to stdout.

Tables/columns from docs/architecture/db-schema-reference.md (verified 2026-10-28 04:28 UTC):
  shared.llm_call_log   (created_at, stage, role, model, provider, account, cost_usd, quality_signal, job_id)
  shared.llm_call_daily (day, app, stage, provider, account, is_shadow, calls, cost_usd)  -- rolled days
  shared.dfs_call_log   (created_at, endpoint, cost_usd, fetched_live, cache_hit)
  shared.decision_log   (created_at, stage, cost_usd, error)
  gold_aa_internal.published_tours (published_at, updated_at, master_status, deleted_at)
A day is either rolled into llm_call_daily or still raw in llm_call_log, never both (AA-825), so the two
sources are added. Shadow rows: llm_call_daily.is_shadow; raw rows carry quality_signal->>'shadow'.
"""
import asyncio
import json
import os

import asyncpg

START, END = "2026-08-01", "2026-11-01"

Q = {
    "llm_by_month_provider_account": """
        WITH raw AS (
            SELECT date_trunc('month', created_at)::date AS m, coalesce(provider, '?') AS provider,
                   coalesce(account, '?') AS account, count(*)::bigint AS calls,
                   coalesce(sum(cost_usd), 0)::float AS usd
              FROM shared.llm_call_log
             WHERE created_at >= $1::date AND created_at < $2::date
             GROUP BY 1, 2, 3
        ), rolled AS (
            SELECT date_trunc('month', day)::date AS m, coalesce(provider, '?') AS provider,
                   coalesce(account, '?') AS account, sum(calls)::bigint AS calls,
                   coalesce(sum(cost_usd), 0)::float AS usd
              FROM shared.llm_call_daily
             WHERE day >= $1::date AND day < $2::date
             GROUP BY 1, 2, 3
        )
        SELECT m::text, provider, account, sum(calls)::bigint AS calls, round(sum(usd)::numeric, 2)::float AS usd
          FROM (SELECT * FROM raw UNION ALL SELECT * FROM rolled) x
         GROUP BY 1, 2, 3 ORDER BY 1, 5 DESC""",
    "llm_by_month_stage_top": """
        WITH raw AS (
            SELECT date_trunc('month', created_at)::date AS m, stage, coalesce(sum(cost_usd), 0)::float AS usd
              FROM shared.llm_call_log WHERE created_at >= $1::date AND created_at < $2::date GROUP BY 1, 2
        ), rolled AS (
            SELECT date_trunc('month', day)::date AS m, stage, coalesce(sum(cost_usd), 0)::float AS usd
              FROM shared.llm_call_daily WHERE day >= $1::date AND day < $2::date GROUP BY 1, 2
        ), s AS (
            SELECT m, stage, sum(usd) AS usd FROM (SELECT * FROM raw UNION ALL SELECT * FROM rolled) x GROUP BY 1, 2
        )
        SELECT m::text, stage, round(usd::numeric, 2)::float AS usd
          FROM (SELECT *, row_number() OVER (PARTITION BY m ORDER BY usd DESC) rn FROM s) r
         WHERE rn <= 12 ORDER BY 1, 3 DESC""",
    "dfs_by_month": """
        SELECT date_trunc('month', created_at)::date::text AS m, count(*) FILTER (WHERE fetched_live) AS live_calls,
               count(*) FILTER (WHERE cache_hit) AS cache_hits, round(coalesce(sum(cost_usd), 0)::numeric, 2)::float AS usd
          FROM shared.dfs_call_log WHERE created_at >= $1::date AND created_at < $2::date GROUP BY 1 ORDER BY 1""",
    "jev_by_month": """
        SELECT date_trunc('month', created_at)::date::text AS m, count(*) AS decisions,
               count(*) FILTER (WHERE error IS NOT NULL) AS errors,
               round(coalesce(sum(cost_usd), 0)::numeric, 2)::float AS usd
          FROM shared.decision_log WHERE created_at >= $1::date AND created_at < $2::date GROUP BY 1 ORDER BY 1""",
    "tours_touched_by_month": """
        SELECT date_trunc('month', updated_at)::date::text AS m, count(*) AS tours_updated,
               count(*) FILTER (WHERE published_at >= date_trunc('month', updated_at)) AS first_published_in_month
          FROM gold_aa_internal.published_tours
         WHERE deleted_at IS NULL AND updated_at >= $1::date AND updated_at < $2::date GROUP BY 1 ORDER BY 1""",
    "tours_live_now": """
        SELECT master_status::text AS status, count(*) AS n FROM gold_aa_internal.published_tours
         WHERE deleted_at IS NULL GROUP BY 1 ORDER BY 2 DESC""",
}


async def main() -> None:
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        await conn.execute("SET default_transaction_read_only = on")
        out = {}
        for name, sql in Q.items():
            args = (START, END) if "$1" in sql else ()
            out[name] = [dict(r) for r in await conn.fetch(sql, *args)]
        print(json.dumps(out, default=str, indent=1))
    finally:
        await conn.close()


asyncio.run(main())
