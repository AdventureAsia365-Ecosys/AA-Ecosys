"""S281 PR-20 period 5: current ranking rows with a positive search volume, per market (aggregates only)."""
import asyncio
import os

import asyncpg

SQL = """SELECT market, count(*) AS rows,
       count(*) FILTER (WHERE demand_volume IS NOT NULL) AS not_null,
       count(*) FILTER (WHERE demand_volume > 0) AS positive,
       count(*) FILTER (WHERE demand_volume = 0) AS zero
  FROM acp_contract.atom_ranking WHERE superseded_at IS NULL GROUP BY 1 ORDER BY 1"""


async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require", timeout=30)
    try:
        await conn.execute("SET statement_timeout = '60s'")
        await conn.execute("SET default_transaction_read_only = on")
        for r in await conn.fetch(SQL):
            print("COV " + " | ".join(f"{k}={v}" for k, v in r.items()))
    except Exception as exc:
        print(f"ERR {type(exc).__name__}: {str(exc)[:200]}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
