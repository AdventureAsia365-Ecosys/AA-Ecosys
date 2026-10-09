"""AA-695 follow-up (read-only): why are Segments fragmented? Size distribution, singletons that share
a normalised place with another Segment in the same country, empty Segments."""
import asyncio, boto3, asyncpg, re
from collections import Counter, defaultdict
from urllib.parse import urlparse
def norm(s): return re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    rows = await c.fetch("""
      SELECT s.segment_id, s.canonical_place, s.canonical_action,
             count(DISTINCT ta.atom_id) atoms, count(DISTINCT ta.tour_id) tours,
             (array_remove(array_agg(DISTINCT rt.country), NULL))[1] country
      FROM acp_contract.atom_segment s
      LEFT JOIN acp_contract.atom_segment_member m ON m.segment_id = s.segment_id
      LEFT JOIN acp_contract.v_active_tour_atoms ta ON ta.atom_id = m.atom_id
      LEFT JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = ta.tour_id
      GROUP BY 1, 2, 3""")
    n = len(rows); sizes = Counter(min(r["atoms"], 5) for r in rows)
    print("segments", n, "| atoms per segment (5=5+):", dict(sorted(sizes.items())))
    print("tours per segment: 1 =", sum(r["tours"] == 1 for r in rows), "| >=2 =", sum(r["tours"] >= 2 for r in rows))
    live = [r for r in rows if r["atoms"] > 0]
    by_place = defaultdict(list)
    for r in live:
        by_place[(r["country"], norm(r["canonical_place"]))].append(r)
    single = [r for r in live if r["tours"] == 1]
    share_place = [r for r in single if len(by_place[(r["country"], norm(r["canonical_place"]))]) > 1]
    print("live", len(live), "| single-tour", len(single), f"({100*len(single)//max(1,len(live))}%)",
          "| single-tour sharing exact place with another segment (same country):", len(share_place))
    groups = [v for v in by_place.values() if len(v) > 1]
    print("place groups with >1 segment:", len(groups), "| segments in them:", sum(len(v) for v in groups))
    groups.sort(key=len, reverse=True)
    for g in groups[:8]:
        print("  ", g[0]["country"], "|", g[0]["canonical_place"], "|", [(x["canonical_action"][:30], x["tours"]) for x in g[:6]])
    pl = Counter(len(norm(r["canonical_place"]).split()) for r in single)
    print("single-tour place length (words):", dict(sorted(pl.items())[:8]))
    import random; random.seed(1)
    for r in random.sample(single, 12):
        print("   sample:", r["country"], "|", r["canonical_place"][:60], "|", r["canonical_action"][:40])
    await c.close()
asyncio.run(main())
