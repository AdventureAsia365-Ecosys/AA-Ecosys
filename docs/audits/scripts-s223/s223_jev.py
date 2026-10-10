import asyncio, boto3, asyncpg
from urllib.parse import urlparse
async def main():
    u = urlparse(boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"])
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    tabs = [r["t"] for r in await c.fetch("SELECT table_schema||'.'||table_name t FROM information_schema.tables WHERE table_name ILIKE '%decision%' OR table_name ILIKE '%jev%' OR table_name ILIKE '%question%'")]
    print("tables:", tabs)
    cols = [r["column_name"] for r in await c.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='shared' AND table_name='decision_log'")]
    print("decision_log cols:", cols)
    qcol = "question_id" if "question_id" in cols else ("question" if "question" in cols else cols[2])
    zcol = "zone" if "zone" in cols else None
    q = f"SELECT {qcol} q, count(*) n" + (f", count(*) FILTER (WHERE {zcol}='grey') grey" if zcol else "") + f", max(created_at) last FROM shared.decision_log WHERE created_at > now()-interval '30 days' GROUP BY 1 ORDER BY 2 DESC"
    for r in await c.fetch(q): print(dict(r))
    await c.close()
asyncio.run(main())
