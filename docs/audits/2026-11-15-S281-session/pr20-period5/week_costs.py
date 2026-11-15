"""S281 PR-20 period 5: AI and DataForSEO spend per day, 01-15/11/2026 (aggregates only, read-only)."""
import asyncio
import os

import asyncpg

QUERIES = [
    ("llm.by_day_nov",
     """SELECT to_char(date_trunc('day', created_at), 'MM-DD') AS day, count(*) AS calls,
               round(sum(coalesce(cost_usd, 0))::numeric, 2) AS usd
        FROM shared.llm_call_log WHERE created_at >= '2026-11-01' GROUP BY 1 ORDER BY 1"""),
    ("llm.week_by_stage_family",
     """SELECT split_part(coalesce(stage, '-'), '_', 1) AS family, count(*) AS calls,
               round(sum(coalesce(cost_usd, 0))::numeric, 2) AS usd
        FROM shared.llm_call_log WHERE created_at >= '2026-11-09 17:00+00' GROUP BY 1 ORDER BY 3 DESC"""),
    ("dfs.by_day_nov",
     """SELECT to_char(date_trunc('day', created_at), 'MM-DD') AS day, endpoint, count(*) AS calls,
               round(sum(coalesce(cost_usd, 0))::numeric, 3) AS usd
        FROM shared.dfs_call_log WHERE created_at >= '2026-11-01' GROUP BY 1, 2 ORDER BY 1, 2"""),
]


async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require", timeout=30)
    try:
        await conn.execute("SET statement_timeout = '60s'")
        await conn.execute("SET default_transaction_read_only = on")
        for name, sql in QUERIES:
            try:
                rows = await conn.fetch(sql)
                print(f"## {name} ({len(rows)} rows)")
                for r in rows:
                    print("  " + " | ".join(str(v) for v in r.values()))
            except Exception as exc:
                print(f"ERR {name} {type(exc).__name__}: {str(exc)[:200]}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
