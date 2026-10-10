import asyncio, boto3, asyncpg
from urllib.parse import urlparse
async def main():
    u = urlparse(boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"])
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    for r in await c.fetch("""SELECT question_key q, mode, count(*) n, round(100.0*count(*) FILTER (WHERE zone='grey')/count(*)) grey_pct,
        round(100.0*count(*) FILTER (WHERE cached)/count(*)) cached_pct, round(sum(coalesce(cost_usd,0))::numeric,3) cost
        FROM shared.decision_log WHERE created_at > now()-interval '30 days' AND question_key NOT LIKE 'adhoc%'
        GROUP BY 1,2 HAVING count(*) > 100 ORDER BY 3 DESC"""): print(dict(r))
    print("s1_grounding LLM fallback calls 30d:", await c.fetchval("SELECT count(*) FROM shared.llm_call_log WHERE stage='s1_grounding' AND created_at > now()-interval '30 days'"),
          "cost", await c.fetchval("SELECT round(sum(cost_usd)::numeric,2) FROM shared.llm_call_log WHERE stage='s1_grounding' AND created_at > now()-interval '30 days'"))
    dq = [r["column_name"] for r in await c.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='shared' AND table_name='decision_question'")]
    print("decision_question cols:", dq)
    await c.close()
asyncio.run(main())
