"""AA-695 baseline (read-only): the 3 agreed metrics + empty / excluded Segments."""
import asyncio, re, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from collections import defaultdict
from urllib.parse import urlparse
from services.acp_contract.atom_ranking import classify_exclusion
def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())).strip()
async def main():
    u = urlparse(boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"])
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
    live = [r for r in rows if r["atoms"] > 0]
    excl = [r for r in live if classify_exclusion(r["canonical_place"] or "", r["canonical_action"] or "")]
    real = [r for r in live if r not in excl]
    single = [r for r in real if r["tours"] == 1]
    print(f"segments {len(rows)} | empty {len(rows)-len(live)} | live {len(live)} | excluded (transit/unnamed) {len(excl)} | real {len(real)}")
    print(f"M1 single-tour share (real): {len(single)}/{len(real)} = {100*len(single)/max(1,len(real)):.1f}%  (all live: {100*sum(r['tours']==1 for r in live)/max(1,len(live)):.1f}%)")
    # M2: place-name variants same country — exact norm match or token containment between distinct place strings
    by_c = defaultdict(set)
    for r in real: by_c[r["country"]].add(norm(r["canonical_place"]))
    variant_places = 0; examples = []
    for ctry, places in by_c.items():
        toks = {p: set(p.split()) for p in places if p}
        plist = sorted(toks, key=len)
        for i, a in enumerate(plist):
            for b in plist[i+1:]:
                if toks[a] and toks[a] < toks[b]:
                    variant_places += 1
                    if len(examples) < 6: examples.append(f"{ctry}: '{a}' ⊂ '{b}'")
                    break
    print(f"M2 place-name variants (same country, token containment): {variant_places} places | e.g. {examples}")
    # M3: multi-tour segments / places appearing in >= 2 tours
    atoms = await c.fetch("""SELECT ta.place, ta.action, ta.tour_id, rt.country FROM acp_contract.v_active_tour_atoms ta
        JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = ta.tour_id""")
    place_tours = defaultdict(set)
    for a in atoms:
        if classify_exclusion(a["place"] or "", a["action"] or ""): continue
        place_tours[(a["country"], norm(a["place"]))].add(a["tour_id"])
    groupable = sum(1 for v in place_tours.values() if len(v) >= 2)
    multi = sum(1 for r in real if r["tours"] >= 2)
    print(f"M3 multi-tour segments {multi} / places in >=2 tours {groupable} = {multi/max(1,groupable):.2f} | multi-tour share of real {100*multi/max(1,len(real)):.1f}%")
    await c.close()
asyncio.run(main())
