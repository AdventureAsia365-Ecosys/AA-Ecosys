"""AA-695 (read-only): within the same (country, place), how many Segments would merge at segment-centroid cosine >= 0.80?"""
import asyncio, re, sys, json
sys.path.insert(0, "/app")
import boto3, asyncpg
import numpy as np
from collections import defaultdict
from urllib.parse import urlparse
from services.acp_contract.atom_ranking import classify_exclusion
def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())).strip()
async def main():
    u = urlparse(boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"])
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    print("embedded active atoms:", await c.fetchval("SELECT count(*) FROM acp_contract.v_active_tour_atoms ta JOIN acp_contract.atom_embedding e USING (atom_id)"),
          "/", await c.fetchval("SELECT count(*) FROM acp_contract.v_active_tour_atoms"))
    rows = await c.fetch("""SELECT m.segment_id, s.canonical_place p, s.canonical_action a, rt.country, ta.tour_id, e.embedding::text emb
        FROM acp_contract.atom_segment s JOIN acp_contract.atom_segment_member m USING (segment_id)
        JOIN acp_contract.v_active_tour_atoms ta ON ta.atom_id = m.atom_id
        JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = ta.tour_id
        LEFT JOIN acp_contract.atom_embedding e ON e.atom_id = ta.atom_id""")
    seg = defaultdict(lambda: {"vec": [], "tours": set(), "key": None, "a": None})
    for r in rows:
        if classify_exclusion(r["p"] or "", r["a"] or ""): continue
        s = seg[r["segment_id"]]; s["key"] = (r["country"], norm(r["p"])); s["a"] = r["a"]; s["tours"].add(r["tour_id"])
        if r["emb"]: s["vec"].append(np.array(json.loads(r["emb"]), dtype=np.float32))
    by_place = defaultdict(list)
    for sid, s in seg.items():
        if s["vec"]:
            v = np.mean(s["vec"], axis=0); s["c"] = v / (np.linalg.norm(v) or 1); by_place[s["key"]].append(sid)
    covered = sum(1 for s in seg.values() if s["vec"]); multi_places = [k for k, v in by_place.items() if len(v) >= 2]
    print(f"real segments {len(seg)} | with embedding {covered} | places with >=2 embedded segments {len(multi_places)}")
    for th in (0.80, 0.85, 0.90):
        merged = 0; ex = []
        for k in multi_places:
            ids = by_place[k]; parent = {i: i for i in ids}
            def f(x):
                while parent[x] != x: x = parent[x]
                return x
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    if float(seg[ids[i]]["c"] @ seg[ids[j]]["c"]) >= th:
                        if f(ids[i]) != f(ids[j]):
                            parent[f(ids[i])] = f(ids[j]); merged += 1
                            if len(ex) < 5: ex.append(f"{k[1]}: '{seg[ids[i]]['a']}' + '{seg[ids[j]]['a']}'")
        print(f"cos>={th}: {merged} merges among {covered} embedded segments | e.g. {ex}")
    await c.close()
asyncio.run(main())
