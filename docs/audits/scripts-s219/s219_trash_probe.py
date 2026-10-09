"""AA-743 probe: pick (PICK=1) or measure (TOUR=<id>) a Master's current ranking/route rows."""
import asyncio, os, boto3, asyncpg
from urllib.parse import urlparse
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    t = os.environ.get("TOUR")
    if os.environ.get("PICK"):
        t = await c.fetchval("""
          SELECT p.tour_id::text FROM gold_aa_internal.published_tours p
          JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=p.tour_id
          WHERE p.master_status='active' AND rt.country='Mongolia'
            AND EXISTS (SELECT 1 FROM acp_contract.route r WHERE r.tour_id=p.tour_id AND r.superseded_at IS NULL)
            AND NOT EXISTS (SELECT 1 FROM gold_aa_internal.tenant_tour_versions v WHERE v.published_tour_id=p.id)
          ORDER BY p.published_at LIMIT 1""")
    r = await c.fetchrow("""SELECT p.master_status::text ms, rt.src_name,
        (SELECT count(*) FROM acp_contract.atom_ranking ar WHERE ar.tour_id=$1::uuid AND ar.superseded_at IS NULL) ranking,
        (SELECT count(*) FROM acp_contract.route r WHERE r.tour_id=$1::uuid AND r.superseded_at IS NULL) routes
        FROM gold_aa_internal.published_tours p JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=p.tour_id WHERE p.tour_id=$1::uuid""", t)
    print("TOUR", t, dict(r))
    await c.close()
asyncio.run(main())
