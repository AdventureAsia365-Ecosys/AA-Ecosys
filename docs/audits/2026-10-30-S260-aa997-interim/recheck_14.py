"""AA-990 recheck_14 (S260, AA-997 lane) — READ-ONLY re-check of the 14 N1 tours that waited on geocode plus the two
leg-rule tours (S255 .tmp-session/S255/aa990/recheck_14.py), on current data, with the S258 v2 logic
(.tmp-session/S258/aa997/recheck_14_v2.py) updated for the aa997.3 + v2 relocate chain of 30/10.

Per tour:
  route          TripPlanner's bar: stop days present on the current Tour Graph, and pinned days (geo.tour_place rows
                 with an embedding) >= 0.5 x days; days = pipeline.tour_day_count (TripPlanner's denominator) when the
                 deployed code has it, else the highest geo.tour_day day (as S255 recheck_14 did);
  all_confirmed  every place (each geo.tour_place component and each geo.tour_day night with an anchor) is linked, its
                 destination (after duplicate_of) is located_by geoapify / manual, not suspect, and has no
                 review_reason (S258 v2, strict). `loose` = S257 P3's rule (linked ones geoapify / manual, not suspect,
                 review_reason allowed) for comparison with the S257 numbers;
  NEED lines     every unconfirmed place with its relocate stamp (v / outcome) and the next step for it.
Last lines: RECHECK14 route ok x/16 · all-confirmed y/16 (loose z/16), then SUMMARY {json}.

Run inside the CIS api container (orchestrator only): tools/ecs/ecsx.sh .tmp-session/S260/aa997/recheck_14.py
DATABASE_URL (cis_app), ssl='require', read-only transaction (rolled back), no write, no paid call.
"""
import asyncio
import json
import os
import sys
from collections import Counter, defaultdict

import asyncpg

if "/app" not in sys.path:
    sys.path.insert(0, "/app")

PENDING_14 = ["ac1d5f9b", "b5c3c908", "e864ec99", "0c608efd", "a423e72e", "b9b39260", "b7188d60", "3eda85ad",
              "a44bf9c4", "c99a1434", "229f2c60", "56e78342", "c6b24380", "2d9ccb23"]
LEG_RULE_2 = ["90b88118", "2020d00f"]          # Seoul-Busan, Oze-Nikko (tour-level transit rule)
SHARE = 0.5
OK_LOC = ("geoapify", "manual")

TOURS_SQL = """
WITH t AS (SELECT b.source_id, b.status FROM geo.tour_build b WHERE left(b.source_id, 8) = ANY($1::text[])),
     g AS (SELECT build_id FROM geo.graph_build WHERE is_current)
SELECT t.source_id, t.status,
       (SELECT max(d.day_index) FROM geo.tour_day d WHERE d.source_id = t.source_id) AS max_day,
       (SELECT count(DISTINCT s.day_index) FROM geo.tour_stop s, g
         WHERE s.build_id = g.build_id AND s.source_id = t.source_id) AS stop_days,
       (SELECT count(DISTINCT p.day_index) FROM geo.tour_place p
         WHERE p.source_id = t.source_id AND p.embedding IS NOT NULL) AS pinned_days
  FROM t ORDER BY t.source_id
"""
PLACES_SQL = """
WITH pl AS (
    SELECT tp.source_id, tp.day_index, 'place' AS kind, tp.name AS label, tp.destination_id
      FROM geo.tour_place tp WHERE left(tp.source_id, 8) = ANY($1::text[])
    UNION ALL
    SELECT td.source_id, td.day_index, 'night', coalesce(td.anchor_place, td.anchor_norm), td.overnight_destination_id
      FROM geo.tour_day td WHERE left(td.source_id, 8) = ANY($1::text[]) AND td.anchor_norm IS NOT NULL)
SELECT pl.source_id, pl.day_index, pl.kind, pl.label, d.id::text AS did, d.name, d.located_by, d.geo_status,
       d.review_reason, d.lat, d.lng,
       d.geocoder_meta -> 'relocate' ->> 'outcome' AS ro, d.geocoder_meta -> 'relocate' ->> 'v' AS rv,
       d.geocoder_meta -> 'relocate' ->> 'accept_rule' AS rar
  FROM pl
  LEFT JOIN shared.destinations d0 ON d0.id = pl.destination_id
  LEFT JOIN shared.destinations d ON d.id = coalesce(d0.duplicate_of, d0.id)
 ORDER BY pl.source_id, pl.day_index, pl.kind
"""


def route_of(p: dict, rule_version: str) -> str:
    """Where an unconfirmed place goes next (the leading words, before ' (' or ':', are the SUMMARY bucket)."""
    if p["did"] is None:
        return "unlinked (name not resolved: place_geocode / admin)"
    if p["geo_status"] == "suspect":
        return "hidden (suspect): admin fix or unhide"
    lb, ro, rv = p["located_by"], p["ro"], p["rv"]
    if lb == "llm" and ro is None:
        return "relocate chain pending (untouched llm: the queued chain takes it)"
    if lb == "llm" and ro == "non_place":
        return "non_place (flagged by relocate): admin review / hide"
    if lb == "llm" and ro in ("llm_point", "off_route"):
        if rv == rule_version:
            return f"chain flagged {ro} (current chain, no geocoder match): admin fix in /admin/places or hide"
        return f"old-rule flagged {ro} ({rv}): relocate recheck {ro} (strategy v2, aa997.3) or admin fix"
    if lb == "mapbox":
        return "mapbox point (relocate located_by mapbox, dry run first) or keep"
    if p["review_reason"]:
        return f"flagged {p['review_reason']}: admin review"
    return f"other ({lb})"


async def main():
    from services.places import relocate
    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require", server_settings={
        "application_name": "aa990-recheck14-s260", "statement_timeout": "60000",
        "default_transaction_read_only": "on"})
    tr = c.transaction(readonly=True)
    await tr.start()
    try:
        now = await c.fetchval("SELECT now()")
        print(f"RECHECK14 at {str(now)[:16]} deployed relocate RULE_VERSION={relocate.RULE_VERSION}")
        ids = PENDING_14 + LEG_RULE_2
        tours = await c.fetch(TOURS_SQL, ids)
        days_tp = {}
        try:            # TripPlanner's denominator (AA-990 review fix), when the deployed code has it
            from services.places import pipeline, store
            if hasattr(pipeline, "tour_day_count") and hasattr(store, "_LIVE_SQL"):
                async with c.transaction():      # savepoint: a failed read does not abort the rest
                    live = await c.fetch(f"SELECT * FROM ({store._LIVE_SQL}) x WHERE left(x.source_id, 8) = "
                                         "ANY($1::text[])", ids)
                mx = {t["source_id"]: t["max_day"] or 0 for t in tours}
                for lv in live:
                    days_tp[lv["source_id"]] = pipeline.tour_day_count(lv["duration"], lv["aa_itineraries"] or "",
                                                                       mx.get(lv["source_id"], 0))
        except Exception as e:  # noqa: BLE001 — fall back to the highest day record
            print(f"NOTE TripPlanner denominator unavailable: {type(e).__name__}: {str(e)[:120]}")
        places = defaultdict(list)
        for p in await c.fetch(PLACES_SQL, ids):
            places[p["source_id"]].append(dict(p))
        left = await relocate.count_candidates(c, located_by=["llm"], country=None)
        seen, ok_route, all_conf, loose_conf = set(), 0, 0, 0
        need, per_tour = Counter(), []
        for t in tours:
            sid = t["source_id"]
            seen.add(sid[:8])
            days = days_tp.get(sid) or t["max_day"] or 0
            route = bool(t["stop_days"]) and days > 0 and t["pinned_days"] >= SHARE * days
            ps = places.get(sid, [])
            bad = [p for p in ps if p["did"] is None or p["located_by"] not in OK_LOC or p["geo_status"] == "suspect"
                   or p["review_reason"]]
            linked = [p for p in ps if p["did"] is not None]
            loose = bool(linked) and all(p["located_by"] in OK_LOC and p["geo_status"] != "suspect" for p in linked)
            conf = bool(ps) and not bad
            ok_route += route
            all_conf += conf
            loose_conf += loose
            pending_chain = sum(1 for p in bad if p["did"] is not None and p["located_by"] == "llm" and p["ro"] is None)
            print(f"TOUR {sid[:8]} {'leg' if sid[:8] in LEG_RULE_2 else 'p14'} build={t['status']} days={days}"
                  f"{'(tp)' if sid in days_tp else '(max_day)'} stop_days={t['stop_days']} pinned={t['pinned_days']}"
                  f" route={'Y' if route else 'N'} places={len(ps) - len(bad)}/{len(ps)} all_confirmed="
                  f"{'Y' if conf else 'N'} loose={'Y' if loose else 'N'} pending_chain={pending_chain}")
            per_tour.append({"tour": sid[:8], "route": route, "all_confirmed": conf, "loose": loose,
                             "confirmed": len(ps) - len(bad), "places": len(ps), "pending_chain": pending_chain})
            for p in bad:
                nxt = route_of(p, relocate.RULE_VERSION)
                need[nxt.split(" (")[0].split(":")[0]] += 1
                pt = f"{p['lat']:.4f},{p['lng']:.4f}" if p["lat"] is not None else "-"
                print(f"  NEED d{p['day_index']} {p['kind']} {(p['label'] or '')[:60]!r} -> {p['name'] or '-'} "
                      f"lb={p['located_by']} pt={pt} reason={p['review_reason']} "
                      f"stamp={p['rv']}/{p['ro']}/{p['rar']} => {nxt}")
        n = len(tours)
        print(f"RECHECK14 route ok {ok_route}/{n} · all-confirmed {all_conf}/{n} (loose {loose_conf}/{n}) "
              f"missing={sorted(set(ids) - seen)} llm_rows_left_for_chain={left}")
        print("SUMMARY " + json.dumps({"route_ok": f"{ok_route}/{n}", "all_confirmed": f"{all_conf}/{n}",
                                       "all_confirmed_loose": f"{loose_conf}/{n}", "missing": sorted(set(ids) - seen),
                                       "next_steps": dict(need.most_common()), "llm_rows_left_for_chain": left,
                                       "s257_baseline": {"route": "13/16", "all_confirmed": "1/16"},
                                       "tours": per_tour}, default=str))
    finally:
        await tr.rollback()
        await c.close()


asyncio.run(main())
