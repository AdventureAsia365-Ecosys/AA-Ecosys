"""Read-only: T-series readiness for AA-741 — test tenants, brand rules, adoptions, pieces, costs per T stage."""
import asyncio, boto3, asyncpg
from urllib.parse import urlparse
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    print("tenants:", [tuple(r) for r in await c.fetch("""SELECT t.slug, t.is_active, t.country,
        (SELECT count(*) FROM shared.tenant_brand_rules b WHERE b.tenant_id=t.tenant_id AND b.is_active) brand,
        (SELECT count(*) FROM gold_aa_internal.tenant_tour_versions v WHERE v.tenant_id=t.tenant_id) versions,
        (SELECT count(*) FROM acp_shared.content_piece p WHERE p.tenant_id=t.tenant_id) pieces,
        EXISTS (SELECT 1 FROM shared.jev_tenant_allowlist a WHERE a.tenant_id=t.tenant_id) jev
        FROM shared.tenants t ORDER BY versions DESC LIMIT 10""")])
    print("cost by T stage (30d):", [tuple(r) for r in await c.fetch("""SELECT stage, count(*), round(sum(cost_usd)::numeric,3), round(avg(cost_usd)::numeric,4)
        FROM shared.llm_call_log WHERE created_at > now()-interval '30 days' AND (stage LIKE 't%' OR stage LIKE 'acp%')
        GROUP BY 1 ORDER BY 3 DESC LIMIT 15""")])
    print("job kinds (30d):", [tuple(r) for r in await c.fetch("""SELECT kind, status, count(*), round(avg(cost_usd)::numeric,4)
        FROM shared.job WHERE created_at > now()-interval '30 days' AND kind LIKE 't%' GROUP BY 1,2 ORDER BY 1,2""")])
    await c.close()
asyncio.run(main())
