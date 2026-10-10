import asyncio, boto3, asyncpg
from urllib.parse import urlparse
async def main():
    u = urlparse(boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"])
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    for r in await c.fetch("""SELECT stage, model, provider, role, count(*) n, round(sum(cost_usd)::numeric,3) cost FROM shared.llm_call_log
        WHERE created_at > now()-interval '30 days' AND (stage LIKE '%grounding%' OR model ILIKE '%jev%' OR provider ILIKE '%typesafe%' OR provider ILIKE '%jev%')
        GROUP BY 1,2,3,4 ORDER BY n DESC LIMIT 12"""): print(dict(r))
    print("jev total 30d in llm_call_log:", await c.fetchval("SELECT round(sum(cost_usd)::numeric,2) FROM shared.llm_call_log WHERE created_at > now()-interval '30 days' AND (model ILIKE '%jev%' OR provider ILIKE '%typesafe%')"))
    print("decision_log total cost 30d:", await c.fetchval("SELECT round(sum(cost_usd)::numeric,2) FROM shared.decision_log WHERE created_at > now()-interval '30 days'"))
    print("all LLM 30d:", await c.fetchval("SELECT round(sum(cost_usd)::numeric,2) FROM shared.llm_call_log WHERE created_at > now()-interval '30 days'"))
    await c.close()
asyncio.run(main())
