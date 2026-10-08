import asyncio, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    print("segments by created day", [tuple(r) for r in await c.fetch("SELECT created_at::date, count(*) FROM acp_contract.atom_segment GROUP BY 1 ORDER BY 1 DESC LIMIT 8")])
    print("routes by created day", [tuple(r) for r in await c.fetch("SELECT created_at::date, count(*) FILTER (WHERE superseded_at IS NULL), count(*) FROM acp_contract.route GROUP BY 1 ORDER BY 1 DESC LIMIT 8")])
    rows = await c.fetch("""SELECT rt.country, count(DISTINCT a.tour_id) tours, count(*) atoms,
        count(*) FILTER (WHERE EXISTS (SELECT 1 FROM acp_contract.atom_segment_member m WHERE m.atom_id=a.atom_id)) in_segment,
        count(DISTINCT a.tour_id) FILTER (WHERE EXISTS (SELECT 1 FROM acp_contract.route r WHERE r.tour_id=a.tour_id AND r.superseded_at IS NULL)) tours_route,
        count(DISTINCT a.tour_id) FILTER (WHERE EXISTS (SELECT 1 FROM acp_contract.atom_ranking k WHERE k.tour_id=a.tour_id)) tours_ranked
        FROM acp_contract.v_active_tour_atoms a JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=a.tour_id GROUP BY 1 ORDER BY 2 DESC""")
    for r in rows: print(dict(r))
    print("recompute jobs", [dict(r) for r in await c.fetch("SELECT kind, status, created_at, finished_at FROM shared.job WHERE kind ILIKE '%recompute%' OR kind ILIKE '%segment%' ORDER BY created_at DESC LIMIT 8")])
    print("job kinds", [tuple(r) for r in await c.fetch("SELECT kind, count(*), max(created_at) FROM shared.job GROUP BY 1 ORDER BY 3 DESC")])
    await c.close()
asyncio.run(main())
