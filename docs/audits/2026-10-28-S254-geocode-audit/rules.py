#!/usr/bin/env python3
"""S254 geocode audit: rule-based flags over CIS geo.place_name (resolved rows).

Stdlib only, read-only. Input: place_names.json (same dir). Output: flags.json,
shard-0..9.json, and a printed summary. No network, no paid calls.
"""
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "place_names.json"

# --- country names -> ISO2 (tour country strings + d_country values) -------
NAME_ISO = {
    "india": "IN", "nepal": "NP", "china": "CN", "laos": "LA", "sri lanka": "LK",
    "south korea": "KR", "korea": "KR", "thailand": "TH", "japan": "JP",
    "philippines": "PH", "pakistan": "PK", "bhutan": "BT", "taiwan": "TW",
    "mongolia": "MN", "vietnam": "VN", "viet nam": "VN", "cambodia": "KH",
    "tanzania": "TZ", "kyrgyzstan": "KG", "russia": "RU", "russian federation": "RU",
    "kazakhstan": "KZ", "bangladesh": "BD", "north korea": "KP", "myanmar": "MM",
    "maldives": "MV", "tibet": "CN", "hong kong": "HK", "macau": "MO",
    "malaysia": "MY", "singapore": "SG", "indonesia": "ID", "kenya": "KE",
    "uzbekistan": "UZ", "tajikistan": "TJ", "afghanistan": "AF",
}

# --- neighbours: land borders + common combined-tour / sea neighbours ------
NEIGH = {
    "IN": {"NP", "BT", "BD", "PK", "CN", "MM", "LK", "MV"},
    "NP": {"IN", "CN", "BT"},
    "CN": {"IN", "NP", "BT", "PK", "MN", "RU", "KZ", "KG", "TJ", "AF", "MM",
           "LA", "VN", "KP", "HK", "MO", "TW"},
    "LA": {"TH", "VN", "KH", "MM", "CN"},
    "LK": {"IN", "MV"},
    "KR": {"KP", "JP", "CN"},
    "TH": {"LA", "KH", "MM", "MY"},
    "JP": {"KR", "CN", "RU"},
    "PH": {"TW"},
    "PK": {"IN", "CN", "AF", "IR"},
    "BT": {"IN", "CN", "NP"},
    "TW": {"CN", "PH", "JP"},
    "MN": {"CN", "RU"},
    "VN": {"CN", "LA", "KH"},
    "KH": {"TH", "LA", "VN"},
    "TZ": {"KE", "UG", "RW", "BI", "CD", "ZM", "MW", "MZ"},
    "KG": {"KZ", "CN", "TJ", "UZ"},
    "RU": {"MN", "CN", "KZ", "KP", "JP"},
    "KZ": {"RU", "CN", "KG", "UZ", "TM"},
    "BD": {"IN", "MM"},
    "KP": {"KR", "CN", "RU"},
    "MM": {"TH", "IN", "CN", "LA", "BD"},
}

# --- rough bounding boxes (lat_min, lat_max, lng_min, lng_max) -------------
BBOX = {
    "IN": (6.5, 35.7, 68.0, 97.5),
    "CN": (18.0, 53.6, 73.4, 135.1),
    "NP": (26.3, 30.5, 80.0, 88.3),
    "LK": (5.9, 9.9, 79.5, 82.0),
    "KR": (33.0, 38.7, 124.5, 131.9),
    "LA": (13.9, 22.6, 100.0, 107.7),
    "JP": (24.0, 45.6, 122.9, 146.0),
    "TH": (5.6, 20.5, 97.3, 105.7),
    "PH": (4.5, 21.2, 116.9, 126.7),
    "PK": (23.6, 37.1, 60.8, 77.9),
    "BT": (26.7, 28.4, 88.7, 92.2),
    "TW": (21.8, 26.4, 118.1, 122.1),
    "VN": (8.4, 23.5, 102.1, 109.6),
    "KH": (10.3, 14.8, 102.3, 107.7),
    "MN": (41.5, 52.2, 87.7, 120.0),
    "TZ": (-11.8, -0.9, 29.3, 40.5),
    "KG": (39.1, 43.3, 69.2, 80.3),
    "KZ": (40.5, 55.5, 46.4, 87.4),
    "RU": (41.1, 82.0, 19.6, 180.0),
    "BD": (20.6, 26.7, 88.0, 92.7),
    "MV": (-0.7, 7.2, 72.6, 73.8),
    "KP": (37.6, 43.0, 124.2, 130.7),
    "MM": (9.8, 28.6, 92.1, 101.2),
}
MARGIN = 0.3

SITE_KW = [
    "temple", "monastery", "museum", "hotel", "station", "bridge", "waterfall",
    "falls", "fort", "palace", "pagoda", "stupa", "shrine", "church", "mosque",
    "cathedral", "gompa", "wat ", "wat", "dzong", "tomb", "mausoleum", "gate",
    "tower", "airport", "market", "cave", "caves", "lodge", "resort", "garden",
    "gardens", "park", "zoo", "square", "monument", "memorial", "castle",
    "observatory", "gallery", "library", "university", "school", "dam",
    "lighthouse", "pier", "jetty", "statue", "buddha", "mandir", "gurudwara",
    "ghat", "haveli", "stepwell", "baori", "mahal", "masjid", "minar", "chorten",
    "lhakhang", "goemba", "jinja", "ji", "dera", "dargah", "kovil", "camp",
    "homestay", "guesthouse", "restaurant", "cafe", "brewery", "winery",
    "factory", "workshop", "village",
]
# 'village' and generic words are noisy; keep a strict set for the flag.
SITE_STRICT = {
    "temple", "monastery", "museum", "hotel", "station", "bridge", "waterfall",
    "falls", "fort", "palace", "pagoda", "stupa", "shrine", "church", "mosque",
    "cathedral", "gompa", "dzong", "tomb", "mausoleum", "tower", "airport",
    "cave", "caves", "lodge", "resort", "zoo", "monument", "memorial", "castle",
    "observatory", "gallery", "statue", "mandir", "gurudwara", "haveli",
    "stepwell", "baori", "mahal", "masjid", "minar", "chorten", "lhakhang",
    "goemba", "dargah", "kovil", "brewery", "winery", "dam", "lighthouse",
    "pier", "jetty", "wat",
}
TOKEN_RE = re.compile(r"[a-z]+")


def haversine(a_lat, a_lng, b_lat, b_lng):
    r = 6371.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = p2 - p1, math.radians(b_lng - a_lng)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, h)))


def tour_isos(country):
    if not country:
        return set()
    parts = re.split(r",| and ", country)
    return {NAME_ISO.get(p.strip().lower()) for p in parts if NAME_ISO.get(p.strip().lower())}


def in_bbox(iso, lat, lng):
    b = BBOX.get(iso)
    if not b:
        return None
    if iso == "RU" and lng < -168:  # Chukotka across the antimeridian
        return b[0] - MARGIN <= lat <= b[1] + MARGIN
    return (b[0] - MARGIN <= lat <= b[1] + MARGIN) and (b[2] - MARGIN <= lng <= b[3] + MARGIN)


def main():
    rows = json.loads(SRC.read_text())
    res = [r for r in rows if r["status"] == "resolved"]
    iso_set = sorted({r["country_iso2"] for r in res if r["country_iso2"]})
    missing_bbox = [i for i in iso_set if i not in BBOX]
    print(f"rows={len(rows)} resolved={len(res)} isos_in_data={iso_set} missing_bbox={missing_bbox}")

    flags = defaultdict(list)   # idx -> [flag]
    detail = defaultdict(dict)  # idx -> {flag: info}

    # 1. country
    for i, r in enumerate(res):
        iso = r["country_iso2"]
        if not iso:
            flags[i].append("country"); detail[i]["country"] = "country_iso2 missing"; continue
        d_iso = NAME_ISO.get((r["d_country"] or "").strip().lower())
        if d_iso and d_iso != iso:
            flags[i].append("country"); detail[i]["country"] = f"d_country={r['d_country']} vs iso={iso}"; continue
        t = tour_isos(r["country"])
        if t and iso not in t:
            near = set().union(*(NEIGH.get(x, set()) for x in t))
            if iso not in near:
                flags[i].append("country")
                detail[i]["country"] = f"place {iso} not tour {sorted(t)} nor neighbour"
            else:
                detail[i]["cross_border_ok"] = f"{iso} neighbour of {sorted(t)}"

    # 2. bbox  3. null island / zero / swapped
    for i, r in enumerate(res):
        lat, lng, iso = r["lat"], r["lng"], r["country_iso2"]
        if lat is None or lng is None:
            flags[i].append("zero_coords"); continue
        if abs(lat) < 1 and abs(lng) < 1:
            flags[i].append("null_island")
        elif lat == 0 or lng == 0:
            flags[i].append("zero_coords")
        ok = in_bbox(iso, lat, lng) if iso else None
        if ok is False:
            flags[i].append("bbox")
            detail[i]["bbox"] = f"({lat},{lng}) outside {iso} {BBOX[iso]}"
            for alt, label in (((lng, lat), "swapped"), ((-lat, lng), "lat_sign"),
                               ((lat, -lng), "lng_sign"), ((-lat, -lng), "both_signs")):
                if in_bbox(iso, *alt):
                    flags[i].append("swapped_sign"); detail[i]["swapped_sign"] = label; break

    # 4. tour spread
    by_tour = defaultdict(list)
    for i, r in enumerate(res):
        by_tour[r["tour_name"]].append(i)
    for tour, idxs in by_tour.items():
        n = len(idxs)
        if n < 2:
            continue
        lim = 300.0 if n <= 3 else 800.0
        for i in idxs:
            others = [j for j in idxs if j != i]
            mlat = statistics.median(res[j]["lat"] for j in others)
            mlng = statistics.median(res[j]["lng"] for j in others)
            d = haversine(res[i]["lat"], res[i]["lng"], mlat, mlng)
            if d > lim:
                flags[i].append("tour_spread")
                detail[i]["tour_spread"] = f"{d:.0f} km from median of {n-1} other places (limit {lim:.0f})"
                detail[i]["spread_km"] = round(d)

    # 5. duplicate coords
    by_pt = defaultdict(list)
    for i, r in enumerate(res):
        by_pt[(round(r["lat"], 5), round(r["lng"], 5))].append(i)
    dup_groups = 0
    for pt, idxs in by_pt.items():
        names = {res[i]["name_norm"] for i in idxs}
        if len(names) < 3:
            continue
        locs = {res[i]["locality"] for i in idxs}
        if len(locs) == 1 and None not in locs:
            continue  # all same named locality: town centroid shared legitimately
        dup_groups += 1
        for i in idxs:
            flags[i].append("dup_coords")
            detail[i]["dup_coords"] = f"{len(names)} names share {pt}"

    # 6. provenance
    prov = [i for i, r in enumerate(res) if r["geocoder_provider"] is None]
    for i in prov:
        flags[i].append("provenance_null")

    # 7. precision area for site-like names
    for i, r in enumerate(res):
        if r["geo_precision"] != "area":
            continue
        toks = set(TOKEN_RE.findall((r["name_norm"] or "").lower()))
        hit = sorted(toks & SITE_STRICT)
        if hit:
            flags[i].append("precision_area_site")
            detail[i]["precision_area_site"] = ",".join(hit)

    # --- output flags.json ---
    out = []
    for i, r in enumerate(res):
        out.append({
            "name_norm": r["name_norm"], "display_name": r["display_name"], "country": r["country"],
            "tour_name": r["tour_name"], "lat": r["lat"], "lng": r["lng"],
            "country_iso2": r["country_iso2"], "flags": flags.get(i, []),
            "detail": detail.get(i, {}),
        })
    (HERE / "flags.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))

    cnt = Counter(f for i in flags for f in set(flags[i]))
    flagged = [i for i in range(len(res)) if flags.get(i)]
    print("\n== counts per flag ==")
    for f, c in cnt.most_common():
        print(f"  {f:22s} {c}")
    print(f"  rows with >=1 flag      {len(flagged)}")
    print(f"  dup_coords groups       {dup_groups}")
    print("\n== overlap (flag combos) ==")
    combo = Counter(tuple(sorted(set(flags[i]))) for i in flagged)
    for k, c in combo.most_common(25):
        print(f"  {c:5d}  {'+'.join(k)}")
    pair = Counter()
    fl = sorted(cnt)
    for i in flagged:
        s = set(flags[i])
        for a in fl:
            for b in fl:
                if a < b and a in s and b in s:
                    pair[(a, b)] += 1
    print("\n== pairwise overlap ==")
    for (a, b), c in pair.most_common():
        print(f"  {a} & {b}: {c}")

    cross = Counter(detail[i]["cross_border_ok"].split()[0] + "<-" + str(sorted(tour_isos(res[i]["country"])))
                    for i in detail if "cross_border_ok" in detail[i])
    print("\n== cross-border accepted (neighbour) ==", sum(cross.values()))
    for k, c in cross.most_common(15):
        print(f"  {c:4d} {k}")

    # provenance summary
    print("\n== provenance: geocoder_provider null ==", len(prov))
    pr = [res[i] for i in prov]
    print("  located_by:", dict(Counter(r["located_by"] for r in pr)))
    print("  geo_precision:", dict(Counter(r["geo_precision"] for r in pr)))
    print("  precision null:", sum(1 for r in pr if r["geo_precision"] is None))
    print("  review_reason:", dict(Counter(r["review_reason"] for r in pr)))
    conf = [r["confidence"] for r in pr if r["confidence"] is not None]
    print("  confidence: n=%d min=%s median=%s max=%s" % (
        len(conf), min(conf) if conf else None, statistics.median(conf) if conf else None, max(conf) if conf else None))
    print("  country_iso2:", dict(Counter(r["country_iso2"] for r in pr).most_common(10)))
    print("  other flags among them:", dict(Counter(f for i in prov for f in set(flags[i]) if f != "provenance_null")))
    print("  precision null overall (resolved):", sum(1 for r in res if r["geo_precision"] is None),
          "of which provider null:", sum(1 for r in pr if r["geo_precision"] is None))

    # --- shards ---
    weight = {"country": 100, "bbox": 100, "tour_spread": 100, "null_island": 100,
              "swapped_sign": 100, "zero_coords": 100, "dup_coords": 10,
              "precision_area_site": 3, "provenance_null": 2}
    def score(i):
        s = sum(weight[f] for f in set(flags[i]))
        return s + min(detail[i].get("spread_km", 0), 5000) / 1000.0

    ranked = sorted(flagged, key=lambda i: (-score(i), res[i]["name_norm"]))
    picked = ranked[:400] if len(ranked) > 400 else ranked
    high = [i for i in flagged if score(i) >= 100]
    print(f"\n== shard selection == flagged={len(flagged)} high-risk(country/bbox/spread/coords)={len(high)} picked={len(picked)}")
    print("  picked flag counts:", dict(Counter(f for i in picked for f in set(flags[i]))))
    rng = random.Random(254)
    unflagged = [i for i in range(len(res)) if not flags.get(i)]
    sample = rng.sample(unflagged, min(200, len(unflagged)))
    items = []
    for i in picked:
        items.append(dict(res[i], flags=flags[i], detail=detail.get(i, {}), sample=False))
    for i in sample:
        items.append(dict(res[i], flags=[], detail=detail.get(i, {}), sample=True))
    rng.shuffle(items)
    sizes = []
    for k in range(10):
        part = items[k::10]
        (HERE / f"shard-{k}.json").write_text(json.dumps(part, ensure_ascii=False, indent=1))
        sizes.append((len(part), sum(1 for x in part if x["sample"])))
    print("  shard sizes (total, sample):", sizes, "total", len(items))


if __name__ == "__main__":
    main()
