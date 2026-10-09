"""AA-695 simulation (read-only): regroup live platform atoms by (country, place, activity_type), logistics excluded.
Compare with today's Segments: count, multi-tour share, atoms covered."""
import asyncio, re, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from collections import Counter, defaultdict
from urllib.parse import urlparse
from services.acp_contract.atom_ranking import classify_exclusion
def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())).strip()
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    atoms = await c.fetch("""SELECT ta.atom_id, ta.tour_id, ta.place, ta.action, ta.activity_type, rt.country
        FROM acp_contract.v_active_tour_atoms ta JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=ta.tour_id
        WHERE ta.owner_scope='platform' AND NOT ta.is_empty_marker""")
    print("active atoms", len(atoms), "| activity_type:", Counter(a["activity_type"] for a in atoms).most_common(12))
    excl = Counter(); groups = defaultdict(set)
    for a in atoms:
        why = classify_exclusion(a["place"] or "", a["action"] or "")
        if a["activity_type"] == "transit" or why == "transit": excl["transit"] += 1; continue
        if why == "unnamed_place": excl["unnamed_place"] += 1; continue
        groups[(a["country"], norm(a["place"]), a["activity_type"] or "-")].add(str(a["tour_id"]))
    n = len(groups); multi = sum(len(t) >= 2 for t in groups.values())
    print("excluded atoms", dict(excl))
    print(f"NEW key: segments {n} | multi-tour {multi} ({100*multi//max(1,n)}%) | sizes", Counter(min(len(t), 5) for t in groups.values()))
    cur = await c.fetchrow("""WITH s AS (SELECT m.segment_id, count(DISTINCT ta.tour_id) tours FROM acp_contract.atom_segment_member m
        JOIN acp_contract.v_active_tour_atoms ta ON ta.atom_id=m.atom_id GROUP BY 1) SELECT count(*) n, count(*) FILTER (WHERE tours>=2) multi FROM s""")
    print(f"CURRENT: segments {cur['n']} | multi-tour {cur['multi']} ({100*cur['multi']//max(1,cur['n'])}%)")
    by_place = defaultdict(set); toks = defaultdict(set)
    for (ct, pl, at), t in groups.items():
        by_place[(ct, pl)] |= t
    pm = sum(len(t) >= 2 for t in by_place.values())
    print(f"CEILING place-only exact: places {len(by_place)} | in >=2 tours {pm} ({100*pm//max(1,len(by_place))}%)")
    # how much of the long tail is a variant of a multi-tour place (one name contains the other, same country)?
    multi_names = defaultdict(list)
    for (ct, pl), t in by_place.items():
        if len(t) >= 2: multi_names[ct].append(pl)
    single = [(ct, pl) for (ct, pl), t in by_place.items() if len(t) == 1]
    variant = sum(any(m != pl and (m in pl or pl in m) and len(m) >= 4 for m in multi_names[ct]) for ct, pl in single)
    print(f"single-tour places {len(single)} | contain/are contained by a multi-tour place name: {variant}")
    import random; random.seed(3)
    for ct, pl in random.sample(single, 15): print("     tail:", ct, "|", pl[:60])
    top = sorted(groups.items(), key=lambda kv: -len(kv[1]))[:10]
    for (ct, pl, at), t in top: print("   ", ct, "|", pl[:40], "|", at, "|", len(t), "tours")
    await c.close()
asyncio.run(main())
