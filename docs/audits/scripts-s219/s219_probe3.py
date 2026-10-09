"""Read-only: route churn of the 00:46-00:51 recompute — were the prior versions superseded in an earlier run (flip-flop)?"""
import asyncio, boto3, asyncpg
from collections import Counter
from urllib.parse import urlparse
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    rows = await c.fetch("""
      SELECT n.route_id, n.version, rt.country, n.ordered_segment_ids = o.ordered_segment_ids same_segs,
             n.hub_id IS NOT DISTINCT FROM o.hub_id AND n.hub_name = o.hub_name same_hub,
             o.superseded_at o_sup, o.created_at o_created,
             (SELECT count(*) FROM acp_contract.route x WHERE x.tour_id=n.tour_id AND x.first_day=n.first_day AND x.last_day=n.last_day) versions
      FROM acp_contract.route n
      JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = n.tour_id
      JOIN LATERAL (SELECT * FROM acp_contract.route o WHERE o.tour_id=n.tour_id AND o.first_day=n.first_day
                    AND o.last_day=n.last_day AND o.version < n.version ORDER BY o.version DESC LIMIT 1) o ON true
      WHERE n.created_at BETWEEN '2026-10-09 01:10:40+00' AND '2026-10-09 01:13:00+00'""")
    def bucket(r):
        s = r["o_sup"]
        return "prior superseded in THIS run" if s and s.isoformat() >= "2026-10-09T01:10" else f"prior superseded earlier ({s:%m-%d %H:%M})" if s else "prior still current?!"
    print("rewritten", len(rows))
    print(Counter((bucket(r)[:40], r["same_segs"], r["same_hub"]) for r in rows).most_common(12))
    print("by country", Counter(r["country"] for r in rows).most_common(8))
    print("versions per identity", Counter(min(r["versions"], 6) for r in rows))
    tot = await c.fetchrow("SELECT count(*) total, count(*) FILTER (WHERE superseded_at IS NULL) cur, max(version) maxv FROM acp_contract.route")
    print("route table", dict(tot))
    await c.close()
asyncio.run(main())
