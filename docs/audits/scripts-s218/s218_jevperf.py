import asyncio, sys, time
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
from api.routers import admin_decisions as m
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    for t in ("shared.decision_log", "shared.llm_call_log"):
        print(t, await c.fetchval(f"SELECT count(*) FROM {t}"), await c.fetchval(f"SELECT count(*) FROM {t} WHERE created_at >= now()-interval '7 days'"),
              await c.fetchval(f"SELECT pg_size_pretty(pg_total_relation_size('{t}'))"))
        for r in await c.fetch("SELECT indexdef FROM pg_indexes WHERE schemaname||'.'||tablename=$1", t): print("   ", r[0])
    for name in ("_SUMMARY_SQL", "_ORPHAN_SQL", "_CALLS_SQL", "_DAILY_SQL", "_STAGE_SQL"):
        t0 = time.time(); await c.fetch(getattr(m, name), 7); print(name, round(time.time()-t0, 2), "s")
    plan = await c.fetch("EXPLAIN (ANALYZE, BUFFERS) " + m._SUMMARY_SQL.replace("$1", "7"))
    print("\n".join(r[0] for r in plan[:25]))
    await c.close()
asyncio.run(main())
