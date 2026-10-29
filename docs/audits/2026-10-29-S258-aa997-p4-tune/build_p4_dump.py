#!/usr/bin/env python3
"""AA-997 S258: build aa997_p4_dump.py — the READ-ONLY dump of the S257 P4 sample for the offline tune (p4_tune.py).

Source: the committed S257 interim audit script (../2026-10-29-S257-aa997-interim/aa997_interim_audit.py, which embeds
the 600 S254 verified rows and re-scores them on today's data). Text patches, each asserted to apply once:
  - part2 keeps the current destination id of each verified row (`did`);
  - main runs part2 (the re-score: correct / wrong today) and then P4D instead of P1 / P2 / P3;
  - P4D: the verified rows that are correct or wrong today AND located by Geoapify (the P4 set of the S257 v2
    re-audit), with
      * the destination row as relocate.rejudge reads it (geocoder_meta reduced to the keys rejudge uses),
      * its name keys (geo.place_name rows resolved to it — relocate._keys_by_destination, deployed code),
      * the RAW overnight anchors of days d-1..d+1 of every (tour, day) using a key — every anchor, with its
        located_by / suspect / merged / line flags and whether it is one of the dumped rows, so the tune script can
        rebuild store.route_anchors exactly and try variants (only the day's own stop, per tour, …),
      * the routes and the re-judge outcome of the DEPLOYED code (relocate.routes_by_destination + rejudge), so the
        tune script proves its rebuild reproduces production before it tries anything else.
    Output: gzip + base64 JSON in `P4DUMP i/n <chunk>` lines, then `P4DUMP_SHA256 <hex> bytes=<n>`.
No write, no paid call, cis_app login, one REPEATABLE READ READ ONLY transaction rolled back.

Run (orchestrator):
  python3 docs/audits/2026-10-29-S258-aa997-p4-tune/build_p4_dump.py
  tools/ecs/ecsx.sh docs/audits/2026-10-29-S258-aa997-p4-tune/aa997_p4_dump.py > .tmp-session/S258/aa997/p4-dump-out.txt
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "2026-10-29-S257-aa997-interim" / "aa997_interim_audit.py"
OUT = HERE / "aa997_p4_dump.py"

PATCHES = [
    ('"application_name": "aa997-interim-audit"', '"application_name": "aa997-p4-dump"'),
    ('print(f"AA-997 interim audit (read-only) at {str(now)[:16]} rule {RULE_VERSION}")',
     'print(f"AA-997 P4 dump (read-only) at {str(now)[:16]}")'),
    ("d.geocoder_meta -> 'relocate' AS reloc", "d.geocoder_meta -> 'relocate' AS reloc, d.id::text AS did"),
    ('        v["now_lb"] = cur["located_by"] if cur is not None else None\n',
     '        v["now_lb"] = cur["located_by"] if cur is not None else None\n'
     '        v["did"] = cur["did"] if cur is not None else None\n'),
    ('for name, fn in (("P1", part1), ("P2", part2), ("P3", part3)):',
     'for name, fn in (("P2", part2), ("P4D", p4_dump)):'),
]

DUMP = '''

# ── AA-997 S258: P4 sample dump (build_p4_dump.py) ────────────────────────────────────────────────────────────────
RAW_ANCHORS_SQL = """
    WITH k AS (SELECT * FROM unnest($1::text[], $2::text[], $3::text[]) AS k(n, c, l)),
         uses AS (
           SELECT k.n, k.c, k.l, tp.source_id, tp.day_index
             FROM geo.tour_place tp JOIN k ON (tp.name_norm, tp.country_norm, tp.locality_norm) = (k.n, k.c, k.l)
           UNION
           SELECT k.n, k.c, k.l, td.source_id, td.day_index
             FROM geo.tour_day td JOIN k ON (td.anchor_norm, td.anchor_country_norm, td.anchor_locality_norm)
                                            = (k.n, k.c, k.l))
    SELECT u.n, u.c, u.l, u.source_id, u.day_index, td.day_index AS anchor_day, td.is_transit_day AS transit,
           td.anchor_norm IS NOT NULL AS has_anchor, d.id::text AS aid, d.lat, d.lng, d.located_by,
           d.geo_status = 'suspect' AS suspect, d.duplicate_of IS NOT NULL AS merged,
           d.geo_precision IS NOT DISTINCT FROM 'line' AS line,
           (SELECT max(t2.day_index) FROM geo.tour_day t2 WHERE t2.source_id = u.source_id) AS last_day
      FROM uses u
      LEFT JOIN geo.tour_day td ON td.source_id = u.source_id AND td.day_index BETWEEN u.day_index - 1 AND u.day_index + 1
      LEFT JOIN shared.destinations d ON d.id = td.overnight_destination_id
     ORDER BY u.n, u.c, u.l, u.source_id, u.day_index, td.day_index
"""
META_KEYS = ("name", "query", "judged", "result_type", "match_type", "confidence", "source", "strategy", "hint", "rule",
             "reference", "sim", "km", "relocate", "provider", "outcome")


async def p4_dump(c):
    import base64
    import gzip
    import hashlib
    import sys
    if "/app" not in sys.path:
        sys.path.insert(0, "/app")
    from services.places import relocate
    vs = [v for v in VERIFIED if v.get("did") and v.get("now_lb") == "geoapify" and v["state"] in ("C", "E")]
    ids = sorted({v["did"] for v in vs})
    rows = [dict(r) for r in await c.fetch("""
        SELECT d.id::text AS id, d.name, d.country, d.lat, d.lng, d.located_by, d.geo_status, d.geo_precision,
               d.review_reason, d.name_norm, d.locality_norm, d.geocoder_meta
          FROM shared.destinations d WHERE d.id = ANY($1::uuid[]) AND d.lat IS NOT NULL""", ids)]
    routes = await relocate.routes_by_destination(c, rows)
    keys_by = await relocate._keys_by_destination(c, [r["id"] for r in rows])
    all_keys = sorted({k for ks in keys_by.values() for k in ks})
    raw = []
    if all_keys:
        a, b, cc = (list(x) for x in zip(*all_keys))
        raw = await c.fetch(RAW_ANCHORS_SQL, a, b, cc)
    anchors = {}
    for r in raw:
        anchors.setdefault("\\x1f".join((r["n"], r["c"], r["l"])), []).append([
            r["source_id"], r["day_index"], r["anchor_day"], r["transit"], r["has_anchor"], r["aid"],
            None if r["lat"] is None else round(float(r["lat"]), 6), None if r["lng"] is None else round(float(r["lng"]), 6),
            r["located_by"], r["suspect"], r["merged"], r["line"], r["last_day"]])
    by_id = {r["id"]: r for r in rows}
    out_rows, tally = [], Counter()
    for v in vs:
        r = by_id.get(v["did"])
        if r is None:
            continue
        jd = relocate.rejudge(r, routes.get(r["id"], ()))
        o = relocate.rejudge_outcome(jd)
        tally[(v["state"], o)] += 1
        meta = j(r["geocoder_meta"])
        out_rows.append({
            "id": r["id"], "name": r["name"], "country": r["country"], "lat": float(r["lat"]), "lng": float(r["lng"]),
            "located_by": r["located_by"], "geo_status": r["geo_status"], "geo_precision": r["geo_precision"],
            "review_reason": r["review_reason"], "name_norm": r["name_norm"], "locality_norm": r["locality_norm"],
            "geocoder_meta": {k: meta[k] for k in META_KEYS if k in meta},
            "verified": {"state": v["state"], "v": v["v"], "tag": v["tag"], "nn": v["nn"], "random": v["s"],
                         "site": v["site"], "exp": v["exp"]},
            "keys": ["\\x1f".join(k) for k in keys_by.get(r["id"], [])],
            "deployed": {"reason": jd["reason"], "unjudged": jd["unjudged"], "outcome": o,
                         "routes": [[list(p) for p in rt] for rt in routes.get(r["id"], ())]},
        })
    blob = json.dumps({"rows": out_rows, "anchors": anchors, "batch_ids": [r["id"] for r in rows],
                       "rule_version": relocate.RULE_VERSION}, separators=(",", ":"), default=str).encode()
    nc = sum(n for (st, _), n in tally.items() if st == "C")
    ne = sum(n for (st, _), n in tally.items() if st == "E")
    print(f"P4D rows={len(out_rows)} correct={nc} refused={tally[('C', 'refused')]} wrong={ne} "
          f"refused={tally[('E', 'refused')]} keys={len(all_keys)} anchor_rows={len(raw)} json_bytes={len(blob)}")
    enc = base64.b64encode(gzip.compress(blob, 9)).decode()
    size = 3000
    parts = [enc[i:i + size] for i in range(0, len(enc), size)]
    for i, part in enumerate(parts, 1):
        print(f"P4DUMP {i}/{len(parts)} {part}")
    print(f"P4DUMP_SHA256 {hashlib.sha256(blob).hexdigest()} bytes={len(blob)}")
'''


def main():
    s = SRC.read_text()
    for old, new in PATCHES:
        assert s.count(old) == 1, f"patch does not apply once: {old[:60]!r} ({s.count(old)})"
        s = s.replace(old, new)
    anchor = "\n\nasync def main():"
    assert s.count(anchor) == 1
    s = s.replace(anchor, DUMP + anchor)
    OUT.write_text(s)
    compile(s, str(OUT), "exec")
    print(f"wrote {OUT} ({len(s)} B)")


if __name__ == "__main__":
    main()
