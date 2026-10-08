import asyncio, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    for r in await c.fetch("""SELECT stage, question_key, count(*) n, count(*) FILTER (WHERE cached) cached, count(*) FILTER (WHERE zone='skipped') skipped,
        count(*) FILTER (WHERE zone='error') err, round(coalesce(sum(cost_usd),0)::numeric,2) cost, count(DISTINCT subject_key) subjects
        FROM shared.decision_log WHERE created_at >= now()-interval '7 days' GROUP BY 1,2 ORDER BY n DESC LIMIT 12"""): print(dict(r))
    for r in await c.fetch("SELECT date_trunc('day',created_at)::date d, count(*) FROM shared.decision_log GROUP BY 1 ORDER BY 1 DESC LIMIT 8"): print(dict(r))
    await c.close()
asyncio.run(main())
