"""AA-743 verify: active Masters with no segment / no current ranking / no current route."""
import asyncio, boto3, asyncpg
from urllib.parse import urlparse
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    r = await c.fetchrow("""
      WITH m AS (SELECT tour_id FROM gold_aa_internal.published_tours WHERE master_status='active')
      SELECT count(*) masters,
        count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM acp_contract.atom_segment_member asm JOIN acp_contract.v_active_tour_atoms ta ON ta.atom_id=asm.atom_id WHERE ta.tour_id=m.tour_id)) no_segment,
        count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM acp_contract.atom_ranking ar WHERE ar.tour_id=m.tour_id AND ar.superseded_at IS NULL)) no_ranking,
        count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM acp_contract.route r WHERE r.tour_id=m.tour_id AND r.superseded_at IS NULL)) no_route
      FROM m""")
    print(dict(r))
    await c.close()
asyncio.run(main())
