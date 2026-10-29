"""AA-997 S258 — local harness (no DB): python selftest_fake_dump.py <CIS checkout> aa997_p4_dump.py > out.txt
then p4_tune.py --decode out.txt --sample s.json and p4_tune.py --sample s.json --cis <CIS checkout> (expect REPRO OK).
Local harness: run the generated aa997_p4_dump.p4_dump against an in-memory fake of the tables it reads, with the
CIS code of the branch as 'deployed' code, so the dump → decode → tune REPRO path is checked before the live run."""
import asyncio, io, json, sys, contextlib
from collections import Counter
CIS, DUMP = sys.argv[1], sys.argv[2]
sys.path.insert(0, CIS)
from services.places import relocate, store

D = {  # destinations: id -> lat, lng, located_by, suspect, merged, line
 "hk": (22.32, 114.17, "geoapify", False, False, False), "bj": (39.90, 116.40, "geoapify", False, False, False),
 "sh": (31.23, 121.47, "geoapify", False, False, False), "gl": (25.27, 110.29, "geoapify", False, False, False),
 "jp": (26.91, 75.79, "geoapify", False, False, False), "xa": (34.26, 108.94, "geoapify", False, False, False),
 "py": (37.20, 112.18, "llm", False, False, False), "mu": (40.43, 116.57, "geoapify", False, False, False),
 "del": (28.556, 77.100, "geoapify", False, False, False), "bell": (34.261, 108.943, "geoapify", False, False, False)}
KEYS = {"hk": [("hong kong", "hong kong", "")], "del": [("delhi airport", "india", "")],
        "bell": [("bell tower", "china", ""), ("bell and drum tower", "china", "")]}
DAY = {("t1", 2): "bj", ("t1", 3): "hk", ("t1", 4): "sh", ("t2", 1): "hk", ("t2", 2): "gl", ("t3", 7): "jp",
       ("t3", 8): None, ("t4", 2): "xa", ("t4", 3): "py", ("t5", 4): "bj", ("t5", 5): "mu", ("t5", 3): "xa"}
ANCH = {("t1", 3): ("hong kong", "hong kong", ""), ("t2", 1): ("hong kong", "hong kong", "")}
TP = [(("delhi airport", "india", ""), "t3", 8), (("bell tower", "china", ""), "t4", 2),
      (("bell tower", "china", ""), "t5", 4), (("bell and drum tower", "china", ""), "t5", 4)]
META = {"hk": {"query": "Hong Kong", "name": "Hong Kong", "result_type": "city"},
        "del": {"query": "Delhi Airport", "name": "Indira Gandhi International Airport", "result_type": "amenity"},
        "bell": {"query": "Bell Tower", "name": "Bell Tower", "result_type": "amenity"}}

def uses(keys):
    out = []
    for k in keys:
        s = {(src, d) for (kk, src, d) in TP if kk == k} | {sd for sd, kk in ANCH.items() if kk == k}
        out += [(k, src, d) for src, d in sorted(s)]
    return out

class Conn:
    async def fetch(self, sql, *a):
        if "FROM shared.destinations d WHERE d.id = ANY" in sql:
            return [{"id": i, "name": META[i]["query"], "country": "China", "lat": D[i][0], "lng": D[i][1],
                     "located_by": "geoapify", "geo_status": "ok", "geo_precision": "point", "review_reason": None,
                     "name_norm": KEYS[i][0][0], "locality_norm": "", "geocoder_meta": json.dumps(META[i])} for i in a[0]]
        if sql.strip().startswith("SELECT destination_id::text AS d"):
            return [{"d": i, "name_norm": k[0], "country_norm": k[1], "locality_norm": k[2]} for i in a[0] for k in KEYS[i]]
        keys = list(zip(a[0], a[1], a[2]))
        raw = "has_anchor" in sql
        out = []
        for k, src, d in uses(keys):
            for ad in (d - 1, d, d + 1):
                if (src, ad) not in DAY:
                    continue
                oid = DAY[(src, ad)]
                if oid is None:
                    if raw:
                        out.append({"n": k[0], "c": k[1], "l": k[2], "source_id": src, "day_index": d, "anchor_day": ad,
                                    "transit": False, "has_anchor": False, "aid": None, "lat": None, "lng": None,
                                    "located_by": None, "suspect": None, "merged": None, "line": None, "last_day": 8})
                    continue
                lat, lng, lb, sus, mg, ln = D[oid]
                if raw:
                    out.append({"n": k[0], "c": k[1], "l": k[2], "source_id": src, "day_index": d, "anchor_day": ad,
                                "transit": False, "has_anchor": True, "aid": oid, "lat": lat, "lng": lng,
                                "located_by": lb, "suspect": sus, "merged": mg, "line": ln, "last_day": 8})
                elif lb in ("geoapify", "manual", "mapbox") and not sus and not mg and not ln and oid not in a[3]:
                    out.append({"n": k[0], "c": k[1], "l": k[2], "source_id": src, "day_index": d, "anchor_day": ad,
                                "lat": lat, "lng": lng})
        return out

src = open(DUMP).read().rsplit("asyncio.run(main())", 1)[0]
ns = {"__name__": "dumpmod"}
exec(compile(src, DUMP, "exec"), ns)
for v in ns["VERIFIED"]:
    v["did"] = None
ex = ns["VERIFIED"][:3]
for v, did, st in zip(ex, ("hk", "del", "bell"), ("C", "C", "E")):
    v.update(did=did, now_lb="geoapify", state=st, tag="kept")
asyncio.run(ns["p4_dump"](Conn()))
