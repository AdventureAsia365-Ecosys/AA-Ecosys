"""AA-997 S260 — READ-ONLY audit of the rows the current place_relocate chain processed (aa997.3 accept rule +
strategy v2 on `located_by = llm` rows, started 30/10/2026), plus the S254/S257 labelled accuracy on today's data.

Run inside the CIS api container (orchestrator only): tools/ecs/ecsx.sh .tmp-session/S260/aa997/audit_relocated.py
Optional VAR=value: SINCE=2026-10-30T00:00:00 (stamp time floor; default = start of the first aa997.3 apply job created
since JOBS_SINCE), JOBS_SINCE=2026-10-28 (job listing floor), STAMP_V=aa997.2 (default: deployed relocate.RULE_VERSION),
ACCEPT=aa997.3 (accept rule that identifies the chain's jobs), SAMPLE_N=40, FULL=1 (one ROW line per processed row),
MOVE_KM=1.0 (a confirmed row moved more than this = "moved"), SEED=s260; served-pins section (L11): HIDE_OUTCOMES=
llm_point,off_route (the relocate outcomes a hide_flagged pass would hide; add weak_confirm to include it),
HIDE_STAMP_V= (comma list of stamp versions, empty = any), HIDE_ACCEPT= (stamp accept rule, empty = any).

DATABASE_URL (cis_app), ssl='require', application_name 'aa997-audit-relocated', statement_timeout 120 s, one
REPEATABLE READ READ ONLY transaction (rolled back). No write, no geocoder or model call: $0. Names are public places.

Where the per-row outcome lives (schema reference: `shared.destinations` ... `geocoder_meta jsonb`): every row the job
processes is stamped `geocoder_meta.relocate = {v, outcome, at, ...}` by services/places/relocate.py `_stamp` —
confirmed: {moved_km, prev: [lat, lng, located_by], accept_rule}; off_route / llm_point: {route_km, geocoder,
accept_rule}; non_place: {cause}; weak_confirm: {refused, geocoder, accept_rule, candidate?}. `v` is the module's
RULE_VERSION (still "aa997.2" while the accept rule is aa997.3). shared.job.result only has counts + <= 25 samples.

Sections (each in its own savepoint; a failed one prints "<tag> FAILED" and the next runs):
  J   the place_relocate jobs since JOBS_SINCE (mode, status, accept rule, strategy, counters) and the chain sums;
  S   census of every relocate stamp by (v, accept_rule, day, outcome, merged);
  R   the chain rows (stamp v = STAMP_V, at >= SINCE): outcome class moved / confirmed / rejected / non_place /
      unchanged, and the accuracy proxies of the S258 method on the CURRENT point:
        route   distance to the routes of the tours using the name (located overnight stops of days d-1..d+1, the row
                itself left out, as store.route_anchors), anchored routes only (the use day has its own stop: aa997.3
                evidence) and all routes; on <= guards.route_radius(name), day_trip <= 150 km, off beyond;
        geo_km  distance model point -> geocoder point (confirmed: the stamp's moved_km; weak_confirm: the refused
                candidate; llm_point / off_route keep no geocoder coordinate);
        country guards.point_ok on the current point (the place's own ISO country: bbox + polygon, 10 km buffer);
        flags   admin_answer (a site name answered by a city / suburb / district: "Urumqi airport" -> Urumqi),
                collapse (>= 3 distinct names on the same 5-decimal point: the Irkutsk centroid), reject_unanchored
                (off_route with no anchored route: the flight / arrival-day false rejection), reject_on_route (kept
                model point lies on the route), big_move (> 100 km), airport, area_site, country_off;
        px      ok / doubt / unjudged per row, from the above (a proxy, not a label);
      then a deterministic stratified SAMPLE (~SAMPLE_N rows by outcome) and WATCH lines (moved / confirmed rows the
      proxy doubts), each with tour, day, name, old / new point, geocoder label, distances;
  L   the S254 labelled metric (600 verified rows, embedded) re-scored on today's points exactly as the S257 interim
      audit did: overall flag-stratified and provenance-stratified accuracy, the projection over today's cells, and
      the verified rows inside the chain set. The AA-997 bar is >= 90 %.
  V   (S260 L11) SERVED PINS vs ALL ROWS. "All rows" is the L metric: every labelled row on today's point, where a
      wrong point that carries a flag still counts wrong and a flagged non-place counts right. "Served pins" is what
      customers, TripPlanner, the CRM and Booking actually see: a destination is served when a live tour's reader
      view shows it (catalog.v_tour_component / v_tour_stop / v_tour_place: those views drop suspect and merged rows),
      and a served non-place name is an error (a pin on the map that is not a place). A hidden row is not served: it
      leaves the denominator (coverage drops), it is not counted right. Printed for three states: served now, served
      if the hide_flagged pass ran (rows stamped HIDE_OUTCOMES by a relocate run, still flagged, still on the model's
      point — the predicate of services/places/relocate.py _HIDE_FLAGGED_SQL, used from the deployed module when it
      has it), and the same plus the opt-in non_place hide. Each: the labelled accuracy (flag-stratified, weights
      scaled by the served share of each stratum), coverage (served share of the labelled rows), and the cell
      projection over the served population. The bar is still read on L; V shows the effect of the hide BEFORE it
      is applied (no write here).
Last line: SUMMARY {json}.
"""
import asyncio
import hashlib
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from datetime import timezone

import asyncpg

if "/app" not in sys.path:
    sys.path.insert(0, "/app")

from services.places import geomatch, guards, relocate  # noqa: E402

ENV = {k: v for k, v in os.environ.items() if k.isupper()}
JOBS_SINCE = ENV.get("JOBS_SINCE", "2026-10-28")
STAMP_V = ENV.get("STAMP_V") or relocate.RULE_VERSION
ACCEPT = ENV.get("ACCEPT", "aa997.3")
SAMPLE_N = int(ENV.get("SAMPLE_N", "40"))
FULL = ENV.get("FULL") == "1"
MOVE_KM = float(ENV.get("MOVE_KM", "1.0"))
SEED = ENV.get("SEED", "s260")
HIDE_OUTCOMES = [x.strip() for x in ENV.get("HIDE_OUTCOMES", "llm_point,off_route").split(",") if x.strip()]
HIDE_STAMP_V = [x.strip() for x in ENV.get("HIDE_STAMP_V", "").split(",") if x.strip()]
HIDE_ACCEPT = ENV.get("HIDE_ACCEPT") or None
BAR = 0.90
DAY_TRIP_KM = guards.DAY_TRIP_KM
ADMIN_TYPES = ("city", "suburb", "district", "county", "state")
CONFIRMED_O = ("confirmed", "reconfirmed")
REJECTED_O = ("llm_point", "off_route", "weak_confirm")
UNCHANGED_O = ("kept", "kept_unjudged")
# stratified sample quotas (outcome stratum -> rows); unfilled quota goes to the biggest strata left
QUOTA = {"moved": 12, "confirmed": 6, "off_route": 7, "llm_point": 9, "weak_confirm": 2, "non_place": 3,
         "unchanged": 1}

# ---- S254 labelled sample (built from docs/audits/2026-10-28-S254-geocode-audit/verified.json, S257 builder) ----
S254_NF, S254_NU = 2321, 5603
S254_PROV = {("l", 1): 1664, ("l", 0): 2106, ("m", 1): 210, ("g", 0): 3497, ("g", 1): 447}
SAME_KM = 0.05
SITE_TOL_KM, OTHER_TOL_KM = 4.0, 5.0
F = ("nn", "cn", "loc", "tour", "lat", "lng", "iso", "v", "exp", "xi", "s", "f", "lb", "site")
VERIFIED_JSON = "__VERIFIED__"
VERIFIED = [dict(zip(F, r)) for r in json.loads(VERIFIED_JSON)]


def j(x):
    if isinstance(x, str):
        try:
            x = json.loads(x)
        except ValueError:
            return {}
    return x if isinstance(x, dict) else {}


def km(a_lat, a_lng, b_lat, b_lng):
    return guards.km(float(a_lat), float(a_lng), float(b_lat), float(b_lng))


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "n/a"


def r1(x):
    return None if x is None else round(float(x), 1)


def hkey(s):
    return hashlib.md5(f"{SEED}:{s}".encode()).hexdigest()


def out(tag, obj):
    print(f"{tag} " + json.dumps(obj, default=str, ensure_ascii=False, separators=(",", ":")))


SUMMARY: dict = {"stamp_v": STAMP_V, "accept": ACCEPT, "bar": BAR}


# ---------------------------------------------------------------- J. jobs
async def part_jobs(c):
    rows = await c.fetch("""
        SELECT id::text AS id, status, created_at, started_at, finished_at, run_after, payload, result,
               left(coalesce(error, ''), 160) AS error
          FROM shared.job WHERE kind = 'place_relocate' AND created_at >= $1::text::timestamptz ORDER BY created_at""",
                         JOBS_SINCE)
    keys = ("rows", "done", "errors", "skipped") + relocate.OUTCOMES + ("geocoder_requests",)
    sums, chain_start, open_jobs = Counter(), None, []
    for r in rows:
        p, res = j(r["payload"]), j(r["result"])
        mode = p.get("mode") or "dry_run"
        ar = p.get("accept_rule") or "v1"
        line = {"id": r["id"][:8], "mode": mode, "status": r["status"], "result": res.get("status"),
                "accept_rule": ar, "strategy": p.get("strategy") or "v1", "rule_version": p.get("rule_version"),
                "created": str(r["created_at"])[:16], "finished": str(r["finished_at"])[:16] if r["finished_at"] else None}
        if mode == "apply":
            line.update({k: res.get(k) for k in keys if res.get(k)})
            line["remaining"] = res.get("remaining")
            line["next"] = (res.get("next_job") or "")[:8] or None
            if ar == ACCEPT and r["status"] == "succeeded":
                for k in keys:
                    sums[k] += int(res.get(k) or 0)
                sums["cost_usd_x1e6"] += int(round(float(res.get("geocoder_cost_usd") or 0) * 1e6))
            if ar == ACCEPT:
                t0 = r["started_at"] or r["created_at"]
                chain_start = t0 if chain_start is None or t0 < chain_start else chain_start
        if r["status"] in ("queued", "running"):
            open_jobs.append({"id": r["id"][:8], "status": r["status"], "mode": mode,
                              "run_after": str(r["run_after"])[:16]})
            line["run_after"] = str(r["run_after"])[:16]
        if r["error"]:
            line["error"] = r["error"]
        out("JOB", line)
    s = {k: sums[k] for k in keys if sums[k]}
    s["cost_usd"] = sums["cost_usd_x1e6"] / 1e6
    out("J chain_sums", {"accept_rule": ACCEPT, "succeeded_apply_jobs_sum": s})
    out("J open", open_jobs)
    SUMMARY["jobs"] = {"chain_sums": s, "open": open_jobs,
                       "chain_start": str(chain_start) if chain_start else None}
    return chain_start


# ---------------------------------------------------------------- S. stamp census
async def part_stamps(c):
    rows = await c.fetch("""
        SELECT geocoder_meta -> 'relocate' ->> 'v' AS v,
               coalesce(geocoder_meta -> 'relocate' ->> 'accept_rule', '-') AS ar,
               left(geocoder_meta -> 'relocate' ->> 'at', 10) AS day,
               geocoder_meta -> 'relocate' ->> 'outcome' AS o, duplicate_of IS NOT NULL AS merged, count(*) AS n
          FROM shared.destinations WHERE geocoder_meta ? 'relocate'
         GROUP BY 1, 2, 3, 4, 5 ORDER BY 1, 2, 3, 4, 5""")
    for r in rows:
        print(f"S stamp v={r['v']} accept={r['ar']} day={r['day']} outcome={r['o']} merged={r['merged']} n={r['n']}")
    left = await relocate.count_candidates(c, located_by=["llm"], country=None)
    lb = await c.fetch("SELECT coalesce(located_by, '-') AS l, count(*) AS n FROM shared.destinations"
                       " WHERE duplicate_of IS NULL GROUP BY 1 ORDER BY 2 DESC")
    rr = await c.fetch("""SELECT coalesce(split_part(review_reason, ':', 1), '-') AS r, count(*) AS n
                            FROM shared.destinations WHERE duplicate_of IS NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 10""")
    out("S left_for_chain", {"llm_rows_not_stamped_by_" + relocate.RULE_VERSION: left})
    out("S located_by", {x["l"]: x["n"] for x in lb})
    out("S review_reason", {x["r"]: x["n"] for x in rr})
    SUMMARY["left_for_chain"] = left


# ---------------------------------------------------------------- R. chain rows + proxies
ROWS_SQL = """
WITH pts AS (
    SELECT round(lat::numeric, 5) AS la, round(lng::numeric, 5) AS lo,
           count(DISTINCT coalesce(name_norm, lower(name))) AS n
      FROM shared.destinations WHERE duplicate_of IS NULL GROUP BY 1, 2)
SELECT d.id::text AS id, d.name, d.country, d.country_iso2, d.lat, d.lng, d.located_by, d.geo_status,
       d.geo_precision, d.review_reason, d.geocoder_meta, d.duplicate_of::text AS dup,
       s.lat AS s_lat, s.lng AS s_lng, s.located_by AS s_lb, coalesce(p.n, 0) AS pt_names
  FROM shared.destinations d
  LEFT JOIN shared.destinations s ON s.id = d.duplicate_of
  LEFT JOIN pts p ON p.la = round(coalesce(s.lat, d.lat)::numeric, 5) AND p.lo = round(coalesce(s.lng, d.lng)::numeric, 5)
 WHERE (d.geocoder_meta -> 'relocate' ->> 'v') = $1
   AND (d.geocoder_meta -> 'relocate' ->> 'at') >= $2
"""
KEYS_SQL = """
SELECT destination_id::text AS d, name_norm, country_norm, locality_norm, coalesce(tour_name, '') AS tour_name
  FROM geo.place_name WHERE destination_id = ANY($1::uuid[])
"""
_K = "WITH k AS (SELECT * FROM unnest($1::text[], $2::text[], $3::text[]) AS k(n, c, l))"
USES_SQL = _K + """
SELECT k.n, k.c, k.l, tp.source_id, tp.day_index, 'place' AS kind
  FROM geo.tour_place tp JOIN k ON (tp.name_norm, tp.country_norm, tp.locality_norm) = (k.n, k.c, k.l)
UNION
SELECT k.n, k.c, k.l, td.source_id, td.day_index, 'night'
  FROM geo.tour_day td JOIN k ON (td.anchor_norm, td.anchor_country_norm, td.anchor_locality_norm) = (k.n, k.c, k.l)
"""
# store._ROUTE_ANCHORS_SQL without the exclusion (done per row below, so a row is left out of ITS OWN route only)
ANCHORS_SQL = _K + """,
     uses AS (
       SELECT k.n, k.c, k.l, tp.source_id, tp.day_index
         FROM geo.tour_place tp JOIN k ON (tp.name_norm, tp.country_norm, tp.locality_norm) = (k.n, k.c, k.l)
       UNION
       SELECT k.n, k.c, k.l, td.source_id, td.day_index
         FROM geo.tour_day td JOIN k ON (td.anchor_norm, td.anchor_country_norm, td.anchor_locality_norm)
                                        = (k.n, k.c, k.l))
SELECT u.n, u.c, u.l, u.source_id, u.day_index, td.day_index AS anchor_day, d.id::text AS aid, d.lat, d.lng
  FROM uses u
  JOIN geo.tour_day td ON td.source_id = u.source_id AND td.day_index BETWEEN u.day_index - 1 AND u.day_index + 1
  JOIN shared.destinations d ON d.id = td.overnight_destination_id
 WHERE d.located_by IN ('geoapify', 'manual', 'mapbox') AND d.geo_status <> 'suspect' AND d.duplicate_of IS NULL
   AND d.geo_precision IS DISTINCT FROM 'line'
 ORDER BY u.n, u.c, u.l, u.source_id, u.day_index, td.day_index
"""


def routes_for(row_id, keys, anchors_by_key):
    """guards.TourRoute per (tour, day) use of the row's keys, the row itself left out (store.route_anchors)."""
    routes = []
    for k in keys:
        by_use, anchored = {}, set()
        for a in anchors_by_key.get(k, ()):
            if a["aid"] == row_id:
                continue
            use = (a["source_id"], a["day_index"])
            pts = by_use.setdefault(use, [])
            p = (float(a["lat"]), float(a["lng"]))
            if not pts or pts[-1] != p:
                pts.append(p)
            if a["anchor_day"] == a["day_index"]:
                anchored.add(use)
        routes += [guards.TourRoute(v, tour=use[0], anchored=use in anchored) for use, v in by_use.items()]
    return tuple(routes)


def route_verdict(lat, lng, routes, name):
    ev = geomatch.evidence_routes(routes, geomatch.strict_params(ACCEPT))
    r_all = guards.route_km(lat, lng, routes) if guards.has_route(routes) else None
    r_anch = guards.route_km(lat, lng, ev) if guards.has_route(ev) else None
    radius = guards.route_radius(name)
    if r_anch is not None:
        v = "on" if r_anch <= radius else ("day_trip" if r_anch <= DAY_TRIP_KM else "off")
    elif r_all is not None:
        v = "unanchored_only"
    else:
        v = "no_route"
    return {"route": v, "r_anch": r1(r_anch), "r_all": r1(r_all), "radius": radius, "n_routes": len(routes),
            "n_anch": len(ev)}


def classify(o, moved_km):
    if o in CONFIRMED_O:
        return "moved" if (moved_km or 0.0) > MOVE_KM else "confirmed"
    if o in REJECTED_O:
        return "rejected"
    if o == "non_place":
        return "non_place"
    if o in UNCHANGED_O:
        return "unchanged"
    return "other"


def assess(d, rv):
    """Flags + proxy verdict for one row (module docstring)."""
    flags = []
    name = d["name"]
    meta, st = d["_meta"], d["_stamp"]
    cls = d["cls"]
    if d["country_bad"]:
        flags.append("country_off")
    # a site / street / square answered by a city, suburb or district of another name (Urumqi airport -> Urumqi,
    # Kirov Square -> Irkutsk): the town's point stands in for the site
    if cls in ("moved", "confirmed") and meta.get("result_type") in ADMIN_TYPES and (
            geomatch.is_site(name) or not geomatch.is_settlement(name)
            or geomatch.name_sim(name, meta.get("name") or "") < 0.5):
        flags.append("admin_answer")
    if d["pt_names"] >= 3:
        flags.append("collapse")
    if (d["moved_km"] or 0) > 100:
        flags.append("big_move")
    if "airport" in name.lower():
        flags.append("airport")
    if d["geo_precision"] == "area" and geomatch.is_site(name):
        flags.append("area_site")
    if cls == "rejected" and rv["route"] == "on":
        flags.append("reject_on_route")
    if st.get("outcome") == "off_route" and rv["n_anch"] == 0:
        flags.append("reject_unanchored")
    if cls == "non_place":
        return flags, "n/a"
    if d["country_bad"] or "admin_answer" in flags or "collapse" in flags or rv["route"] == "off":
        return flags, "doubt"
    if rv["route"] in ("on", "day_trip"):
        return flags, "ok"
    if rv["route"] == "unanchored_only" and rv["r_all"] is not None and rv["r_all"] <= DAY_TRIP_KM:
        return flags, "ok"
    return flags, "unjudged"


def stratum(d):
    if d["cls"] == "rejected":
        return d["_stamp"].get("outcome")
    return d["cls"]


def pick_sample(rows):
    by = defaultdict(list)
    for d in rows:
        by[stratum(d)].append(d)
    for g in by.values():
        g.sort(key=lambda d: hkey(d["id"]))
    take = {k: min(q, len(by.get(k, ()))) for k, q in QUOTA.items()}
    spare = SAMPLE_N - sum(take.values())
    while spare > 0:
        room = sorted(((len(g) - take.get(k, 0), k) for k, g in by.items() if len(g) > take.get(k, 0)), reverse=True)
        if not room:
            break
        take[room[0][1]] = take.get(room[0][1], 0) + 1
        spare -= 1
    return [d for k, n in take.items() for d in by.get(k, [])[:n]]


def line_of(d):
    st, meta = d["_stamp"], d["_meta"]
    use = d["use"]
    o = {"id": d["id"][:8], "tour": use[0] if use else None, "tour_name": use[3] if use else None,
         "day": use[1] if use else None, "kind": use[2] if use else None, "uses": d["n_uses"],
         "name": d["name"], "iso": d["iso"], "outcome": st.get("outcome"), "cls": d["cls"],
         "old": d["old"], "new": d["new"], "moved_km": d["moved_km"],
         "geocoder": ({"name": meta.get("name"), "type": meta.get("result_type"), "match": meta.get("match_type"),
                       "sim": meta.get("sim"), "ref": meta.get("reference"), "judged": meta.get("judged")}
                      if d["cls"] in ("moved", "confirmed") else {"outcome": st.get("geocoder"),
                                                                  "candidate": st.get("candidate")}),
         "geo_km": d["geo_km"], **{k: d["rv"][k] for k in ("route", "r_anch", "r_all", "n_routes", "n_anch")},
         "country": d["country_bad"] or "ok", "flags": d["flags"], "px": d["px"],
         "review_reason": d["review_reason"], "geo_status": d["geo_status"], "merged": bool(d["dup"])}
    if d["new"]:
        o["osm"] = f"https://www.openstreetmap.org/?mlat={d['new'][0]}&mlon={d['new'][1]}#map=13/{d['new'][0]}/{d['new'][1]}"
    return o


async def part_rows(c, since):
    rows = [dict(r) for r in await c.fetch(ROWS_SQL, STAMP_V, since)]
    ids = [r["id"] for r in rows]
    keys_by, tour_name = defaultdict(list), {}
    for k in await c.fetch(KEYS_SQL, ids):
        key = (k["name_norm"], k["country_norm"], k["locality_norm"])
        keys_by[k["d"]].append(key)
        tour_name[key] = k["tour_name"]
    all_keys = list(dict.fromkeys(k for ks in keys_by.values() for k in ks))
    anchors, uses = defaultdict(list), defaultdict(list)
    if all_keys:
        a, b, cc = (list(x) for x in zip(*all_keys))
        for r in await c.fetch(ANCHORS_SQL, a, b, cc):
            anchors[(r["n"], r["c"], r["l"])].append(r)
        for r in await c.fetch(USES_SQL, a, b, cc):
            uses[(r["n"], r["c"], r["l"])].append((r["source_id"][:8], r["day_index"], r["kind"],
                                                   tour_name.get((r["n"], r["c"], r["l"]), "")[:48]))
    for d in rows:
        d["_meta"] = j(d["geocoder_meta"])
        d["_stamp"] = d["_meta"].get("relocate") if isinstance(d["_meta"].get("relocate"), dict) else {}
        st = d["_stamp"]
        lat = float(d["s_lat"] if d["dup"] and d["s_lat"] is not None else d["lat"])
        lng = float(d["s_lng"] if d["dup"] and d["s_lng"] is not None else d["lng"])
        d["new"] = [round(lat, 5), round(lng, 5)]
        prev = st.get("prev") if isinstance(st.get("prev"), list) and len(st.get("prev")) >= 2 else None
        d["old"] = [round(float(prev[0]), 5), round(float(prev[1]), 5)] if prev and prev[0] is not None else d["new"]
        try:
            d["moved_km"] = r1(st.get("moved_km")) if st.get("moved_km") is not None else None
        except (TypeError, ValueError):
            d["moved_km"] = None
        d["moved_now_km"] = r1(km(d["old"][0], d["old"][1], lat, lng))
        d["cls"] = classify(st.get("outcome"), d["moved_km"])
        cand = st.get("candidate")
        if d["cls"] in ("moved", "confirmed"):
            d["geo_km"] = d["moved_km"]
        elif isinstance(cand, list) and len(cand) >= 2:
            d["geo_km"] = r1(km(lat, lng, cand[0], cand[1]))
        else:
            d["geo_km"] = None
        d["iso"] = (d["country_iso2"] or guards.iso2(d["country"]).upper() or "??").strip()
        try:
            d["country_bad"] = guards.point_ok(lat, lng, d["country"])
        except Exception as e:  # noqa: BLE001 — the polygon data may be missing: report, do not stop
            d["country_bad"] = f"check_failed:{type(e).__name__}"
        ks = keys_by.get(d["id"], [])
        d["rv"] = route_verdict(lat, lng, routes_for(d["id"], ks, anchors), d["name"])
        if d["cls"] in ("moved", "confirmed"):
            d["rv_old"] = route_verdict(d["old"][0], d["old"][1], routes_for(d["id"], ks, anchors), d["name"])
        u = sorted({x for k in ks for x in uses.get(k, ())})
        d["use"], d["n_uses"] = (u[0] if u else None), len(u)
        d["flags"], d["px"] = assess(d, d["rv"])
    # ---- summary
    cls_n = Counter(d["cls"] for d in rows)
    out_n = Counter(d["_stamp"].get("outcome") for d in rows)
    out("R rows", {"since": since, "stamp_v": STAMP_V, "n": len(rows), "merged": sum(1 for d in rows if d["dup"]),
                   "by_class": dict(cls_n), "by_outcome": dict(out_n),
                   "accept_rule_in_stamp": dict(Counter(d["_stamp"].get("accept_rule") or "-" for d in rows)),
                   "strategy_in_meta": dict(Counter(d["_meta"].get("strategy") or "-" for d in rows
                                                    if d["cls"] in ("moved", "confirmed")))})
    px = {k: dict(Counter(d["px"] for d in rows if d["cls"] == k)) for k in cls_n}
    out("R proxy_by_class", px)
    out("R route_by_class", {k: dict(Counter(d["rv"]["route"] for d in rows if d["cls"] == k)) for k in cls_n})
    out("R flags_by_class", {k: dict(Counter(f for d in rows if d["cls"] == k for f in d["flags"])) for k in cls_n})
    mv = [d["moved_km"] for d in rows if d["cls"] in ("moved", "confirmed") and d["moved_km"] is not None]
    buckets = Counter("<1" if m < 1 else "1-5" if m < 5 else "5-25" if m < 25 else "25-100" if m < 100 else ">100"
                      for m in mv)
    gain = [d["rv_old"]["r_anch"] - d["rv"]["r_anch"] for d in rows
            if d["cls"] == "moved" and d["rv"]["r_anch"] is not None and d["rv_old"]["r_anch"] is not None]
    out("R moved_km", {"buckets": dict(buckets), "median": r1(statistics.median(mv)) if mv else None,
                       "max": r1(max(mv)) if mv else None,
                       "moved_closer_to_anchored_route": f"{sum(g > 0 for g in gain)}/{len(gain)}",
                       "median_route_gain_km": r1(statistics.median(gain)) if gain else None})
    # a confirmed row whose point moved again after its stamp (admin fix, later geocode); merged rows counted apart
    drift = [d for d in rows if d["cls"] in ("moved", "confirmed") and d["moved_km"] is not None and not d["dup"]
             and abs((d["moved_now_km"] or 0) - d["moved_km"]) > 1.0]
    out("R changed_since_stamp", {"n": len(drift), "ids": [d["id"][:8] for d in drift[:12]],
                                  "merged_since": sum(1 for d in rows if d["dup"])})
    per_iso = defaultdict(Counter)
    for d in rows:
        per_iso[d["iso"]][d["cls"]] += 1
    out("R by_country", {k: dict(v) for k, v in sorted(per_iso.items(), key=lambda kv: -sum(kv[1].values()))[:14]})
    # proxy accuracy: pins whose point the proxy finds plausible / judged (non_place excluded)
    pins = [d for d in rows if d["cls"] != "non_place"]
    judged = [d for d in pins if d["px"] in ("ok", "doubt")]
    conf = [d for d in judged if d["cls"] in ("moved", "confirmed")]
    rej = [d for d in judged if d["cls"] == "rejected"]
    proxy = {"pins": len(pins), "judged": len(judged), "unjudged": len(pins) - len(judged),
             "plausible_all": pct(sum(d["px"] == "ok" for d in judged), len(judged)),
             "plausible_confirmed_or_moved": pct(sum(d["px"] == "ok" for d in conf), len(conf)),
             "plausible_rejected_kept_model_point": pct(sum(d["px"] == "ok" for d in rej), len(rej)),
             "confirmed_share_of_pins": pct(sum(d["cls"] in ("moved", "confirmed") for d in pins), len(pins))}
    out("R proxy", proxy)
    SUMMARY["chain_rows"] = {"n": len(rows), "by_class": dict(cls_n), "by_outcome": dict(out_n), "proxy": proxy}
    # ---- sample + watch
    sample = pick_sample(rows)
    out("R sample_strata", dict(Counter(stratum(d) for d in sample)))
    for d in sample:
        out("SAMPLE", line_of(d))
    watch = sorted((d for d in rows if d["cls"] in ("moved", "confirmed") and d["px"] == "doubt"),
                   key=lambda d: hkey(d["id"]))
    out("R watch", {"n": len(watch), "shown": min(30, len(watch))})
    for d in watch[:30]:
        out("WATCH", line_of(d))
    if FULL:
        for d in rows:
            out("ROW", line_of(d))
    return {d["id"] for d in rows}


# ---------------------------------------------------------------- L. S254 labelled metric (S257 method)
def rescore(v, cur):
    """(state C/E/U/M, tag) for one verified row against its current row (S257 interim audit, unchanged)."""
    V = v["v"]
    if cur is None or cur["lat"] is None:
        return ("C", "np_gone") if V == "NP" else ("M", "missing")
    hidden = cur["status"] != "resolved" or cur["geo_status"] == "suspect"
    nonplace = (cur["review_reason"] or "").startswith("non_place") or (cur["last_error"] or "").startswith("non_place")
    if V == "NP":
        return ("C", "np_flagged") if (nonplace or hidden) else ("E", "np_still_pinned")
    moved = km(v["lat"], v["lng"], cur["lat"], cur["lng"])
    tol = SITE_TOL_KM if v["site"] else OTHER_TOL_KM
    if V == "C":
        if moved <= SAME_KM:
            return "C", ("kept_np_flag" if nonplace else "kept")
        return ("C", "moved_ok") if moved <= tol else ("E", "regressed")
    if V == "U":
        return "U", "unsure"
    if moved <= SAME_KM:
        if V == "WC" and v["xi"] and cur["country_iso2"] == v["xi"]:
            return "C", "iso_fixed"
        return "E", ("unchanged_flagged" if (cur["review_reason"] or hidden) else "unchanged")
    if not v["exp"]:
        return "U", "moved_no_ref"
    if min(km(e[0], e[1], cur["lat"], cur["lng"]) for e in v["exp"]) <= tol:
        if V == "WC" and v["xi"] and cur["country_iso2"] != v["xi"]:
            return "E", "point_fixed_iso_wrong"
        return "C", "fixed"
    return "E", "moved_still_wrong"


def strat(rows, key, pops):
    T = sum(pops.values())
    est, var = {"C": 0.0, "E": 0.0}, {"C": 0.0, "E": 0.0}
    for k, Nk in pops.items():
        g = [r for r in rows if key(r) == k]
        if not g:
            continue
        t, W = len(g), Nk / T
        for m in ("C", "E"):
            p = sum(r["state"] == m for r in g) / t
            est[m] += W * p
            var[m] += W * W * p * (1 - p) / t * (1 - t / Nk) if Nk > t else 0
    return {m: (est[m], 1.96 * math.sqrt(var[m])) for m in ("C", "E")}


def cell(lb, o):
    if o:
        if o in CONFIRMED_O or o in UNCHANGED_O:
            return "rl_confirmed"
        return "rl_non_place" if o == "non_place" else "rl_flagged"
    return {"geoapify": "geoapify", "llm": "llm_untouched", "mapbox": "mapbox", "manual": "manual"}.get(lb, "other")


async def part_labels(c, chain_ids):
    names = sorted({v["nn"] for v in VERIFIED})
    rows = await c.fetch("""
        SELECT pn.name_norm, pn.country_norm, pn.locality_norm, coalesce(pn.tour_name, '') AS tour_name, pn.status,
               pn.last_error, d.lat, d.lng, d.located_by, d.geo_status, d.review_reason, d.country_iso2,
               d0.id::text AS did0, d.id::text AS did, d.geocoder_meta -> 'relocate' AS reloc
          FROM geo.place_name pn
          LEFT JOIN shared.destinations d0 ON d0.id = pn.destination_id
          LEFT JOIN shared.destinations d ON d.id = coalesce(d0.duplicate_of, d0.id)
         WHERE pn.name_norm = ANY($1::text[])""", names)
    by_name = defaultdict(list)
    for r in rows:
        by_name[r["name_norm"]].append(r)
    for v in VERIFIED:
        cands = [r for r in by_name[v["nn"]] if r["country_norm"] == v["cn"]]
        if len(cands) > 1:
            cands = ([r for r in cands if r["locality_norm"] == v["loc"]] or
                     [r for r in cands if r["tour_name"].startswith(v["tour"])] or cands)
        if not cands:
            cands = [r for r in by_name[v["nn"]] if r["tour_name"].startswith(v["tour"])]
        cur = cands[0] if cands else None
        v["found"] = cur is not None
        v["state"], v["tag"] = rescore(v, cur)
        v["before"] = "C" if v["v"] == "C" else ("U" if v["v"] == "U" else "E")
        st = j(cur["reloc"]) if cur is not None and cur["reloc"] else {}
        v["touched"] = st.get("outcome")
        v["chain"] = cur is not None and (cur["did0"] in chain_ids or cur["did"] in chain_ids)
        v["now_lb"] = cur["located_by"] if cur is not None else None
        v["_cur"] = cur
    V = VERIFIED
    out("L tags", {"verified": len(V), "matched": sum(v["found"] for v in V), "tags": dict(Counter(v["tag"] for v in V))})
    for v in V:
        v["_s"] = v["state"]
    res = {}
    for label, fld in (("S254", "before"), ("now", "_s")):
        for v in V:
            v["state"] = v[fld]
        ef = strat(V, lambda r: 0 if r["s"] else 1, {0: S254_NU, 1: S254_NF})
        ep = strat(V, lambda r: (r["lb"], r["f"]), S254_PROV)
        res[label] = {"flag_strat": f"{ef['C'][0]:.1%} ±{ef['C'][1]:.1%}", "error": f"{ef['E'][0]:.1%}",
                      "prov_strat": f"{ep['C'][0]:.1%} ±{ep['C'][1]:.1%}", "_c": ef["C"][0], "_ci": ef["C"][1]}
    for v in V:
        v["state"] = v["_s"]
    out("L overall", {k: {x: y for x, y in r.items() if not x.startswith("_")} for k, r in res.items()})
    groups = (("chain", [v for v in V if v["chain"]]), ("touched_any", [v for v in V if v["touched"]]),
              ("untouched", [v for v in V if not v["touched"] and v["found"]]))
    for name, g in groups:
        b, a = Counter(v["before"] for v in g), Counter(v["state"] for v in g)
        out("L group", {"group": name, "n": len(g), "random": sum(v["s"] for v in g),
                        "correct_before": pct(b["C"], len(g)), "correct_now": pct(a["C"], len(g)),
                        "err_before": pct(b["E"], len(g)), "err_now": pct(a["E"], len(g))})
    ch = [v for v in V if v["chain"]]
    out("L chain_by_outcome", {o: f"{sum(v['state'] == 'C' for v in ch if v['touched'] == o)}/"
                                  f"{sum(1 for v in ch if v['touched'] == o)}" for o in sorted({v['touched'] for v in ch})})
    out("L chain_transitions", dict(Counter(f"{v['v']}>{v['tag']}" for v in ch).most_common(14)))
    for v in [v for v in ch if v["tag"] in ("regressed", "moved_still_wrong")][:15]:
        out("L chain_wrong", {"name": v["nn"], "tour": v["tour"], "verdict": v["v"], "tag": v["tag"],
                              "s254_point": [v["lat"], v["lng"]], "expected": v["exp"][:2]})
    w = {0: S254_NU / 200, 1: S254_NF / 400}
    acc = defaultdict(lambda: [0.0, 0.0, 0])
    for v in V:
        if v["state"] in ("C", "E"):
            k = cell(v["now_lb"], v["touched"])
            acc[k][0] += w[0 if v["s"] else 1] * (v["state"] == "C")
            acc[k][1] += w[0 if v["s"] else 1]
            acc[k][2] += 1
    pop = await c.fetch("""
        SELECT d.located_by AS lb, d.geocoder_meta -> 'relocate' ->> 'outcome' AS o, count(*) AS n
          FROM geo.place_name pn JOIN shared.destinations d0 ON d0.id = pn.destination_id
          JOIN shared.destinations d ON d.id = coalesce(d0.duplicate_of, d0.id)
         WHERE pn.status = 'resolved' GROUP BY 1, 2""")
    N = Counter()
    for p in pop:
        N[cell(p["lb"], p["o"])] += p["n"]
    est, known, parts = 0.0, 0, {}
    for k, n in N.most_common():
        a = acc.get(k)
        rate = a[0] / a[1] if a and a[1] else None
        parts[k] = {"rows": n, "rate": f"{rate:.0%}" if rate is not None else "?", "labelled": a[2] if a else 0}
        if rate is not None:
            est += n * rate
            known += n
    proj = est / known if known else None
    out("L projection", {"cells": parts, "correct": pct(est, known), "over": known, "of": sum(N.values())})
    now_c = res["now"]["_c"]
    # the headline metric is the S257 one (600 labelled rows, flag-stratified); the projection is a cross-check
    gate = {"flag_strat_now": f"{now_c:.1%}", "projection": f"{proj:.1%}" if proj is not None else None,
            "bar": f"{BAR:.0%}", "pass": bool(now_c >= BAR)}
    print(f"GATE AA-997 accuracy flag-strat {now_c:.1%} {'PASS' if gate['pass'] else 'FAIL'} (bar {BAR:.0%}); "
          f"projection {gate['projection']} (cross-check)")
    SUMMARY["labelled"] = {"overall": {k: {x: y for x, y in r.items() if not x.startswith("_")} for k, r in res.items()},
                           "chain_n": len(ch), "chain_correct_now": pct(sum(v["state"] == "C" for v in ch), len(ch)),
                           "projection": parts, "gate": gate}
    SUMMARY["_all_rows_now"] = f"{now_c:.1%} ±{res['now']['_ci']:.1%}"


# ---------------------------------------------------------------- V. served pins vs all rows (S260 L11)
# the catalog views readers use; each drops suspect and merged destinations (CIS 253 / 256 / 258)
SERVED_SQLS = (
    ("v_tour_component", "SELECT DISTINCT destination_id::text AS d FROM catalog.v_tour_component"
                         " WHERE destination_id IS NOT NULL"),
    ("v_tour_stop", "SELECT DISTINCT destination_id::text AS d FROM catalog.v_tour_stop WHERE destination_id IS NOT NULL"),
    ("v_tour_place", "SELECT DISTINCT destination_id::text AS d FROM catalog.v_tour_place WHERE destination_id IS NOT NULL"),
)
# fallback when cis_app cannot read the views: every linked destination (any build, live or not), same row filter
SERVED_FALLBACK_SQL = """
    SELECT DISTINCT d.id::text AS d FROM shared.destinations d
     WHERE d.geo_status <> 'suspect' AND d.duplicate_of IS NULL
       AND (EXISTS (SELECT 1 FROM geo.tour_place tp WHERE tp.destination_id = d.id)
            OR EXISTS (SELECT 1 FROM geo.tour_day td WHERE td.overnight_destination_id = d.id))
"""
# a copy of services/places/relocate.py _HIDE_FLAGGED_SQL (S260 L11) for a container that does not have it yet
HIDE_FLAGGED_SQL_COPY = """
    SELECT d.id::text AS id, d.name, d.country, d.lat, d.lng, d.review_reason, d.located_by,
           d.geocoder_meta -> 'relocate' ->> 'outcome' AS outcome, d.geocoder_meta -> 'relocate' ->> 'v' AS stamp_v,
           d.geocoder_meta -> 'relocate' ->> 'accept_rule' AS accept_rule,
           d.geocoder_meta -> 'relocate' ->> 'route_km' AS route_km,
           (EXISTS (SELECT 1 FROM geo.tour_place tp WHERE tp.destination_id = d.id)
            OR EXISTS (SELECT 1 FROM geo.tour_day td WHERE td.overnight_destination_id = d.id)) AS linked,
           coalesce((d.geocoder_meta -> 'hidden' ->> 'unhidden_at') IS NOT NULL
            AND coalesce(d.geocoder_meta -> 'hidden' ->> 'unhidden_by', '') LIKE 'restore:%'
            AND CASE WHEN (d.geocoder_meta -> 'relocate' ->> 'at') IS NULL THEN true
                     ELSE (d.geocoder_meta -> 'relocate' ->> 'at')::timestamptz
                          <= (d.geocoder_meta -> 'hidden' ->> 'unhidden_at')::timestamptz END, false) AS restored
      FROM shared.destinations d
     WHERE d.duplicate_of IS NULL AND d.geo_status = 'ok'
       AND d.review_reason IS NOT NULL AND d.review_reason <> 'linear_feature'
       AND (d.geocoder_meta -> 'relocate' ->> 'outcome') = ANY($1::text[])
       AND (cardinality($2::text[]) = 0 OR (d.geocoder_meta -> 'relocate' ->> 'v') = ANY($2::text[]))
       AND ($3::text IS NULL OR (d.geocoder_meta -> 'relocate' ->> 'accept_rule') = $3)
       AND (d.located_by = ANY($4::text[])
            OR ((d.geocoder_meta -> 'relocate' ->> 'outcome') = 'weak_confirm' AND d.located_by = 'geoapify'))
       AND ($5::text IS NULL OR lower(btrim(d.country)) = lower(btrim($5)))
     ORDER BY lower(btrim(d.country)), d.id
"""
NON_PLACE_SQL = """
    SELECT d.id::text AS id FROM shared.destinations d
     WHERE d.duplicate_of IS NULL AND d.geo_status = 'ok' AND d.review_reason LIKE 'non_place:%'
"""
# every resolved name on its keeper destination (the L projection's population, per row so served / hidden can be
# applied in Python)
POP_ROWS_SQL = """
    SELECT d.id::text AS did, d.located_by AS lb, d.geocoder_meta -> 'relocate' ->> 'outcome' AS o
      FROM geo.place_name pn JOIN shared.destinations d0 ON d0.id = pn.destination_id
      JOIN shared.destinations d ON d.id = coalesce(d0.duplicate_of, d0.id)
     WHERE pn.status = 'resolved'
"""


async def served_ids(c):
    """(ids of destinations a reader shows, source label). Each view in its own savepoint: a missing grant or view
    falls back to the linked-destination rule on the base tables."""
    ids, used, failed = set(), [], []
    for name, sql in SERVED_SQLS:
        try:
            async with c.transaction():
                ids |= {r["d"] for r in await c.fetch(sql)}
            used.append(name)
        except Exception as e:  # noqa: BLE001 — report, fall back below
            failed.append(f"{name}:{type(e).__name__}")
    if not used:
        ids = {r["d"] for r in await c.fetch(SERVED_FALLBACK_SQL)}
        used = ["fallback_linked_rows"]
    return ids, {"views": used, "failed": failed}


def served_state(v):
    """The served-pin state of a verified row whose destination is served: a non-place on the map is wrong; any
    other row keeps its L state (C / E / U / M)."""
    return "E" if v["v"] == "NP" else v["state"]


def strat_subset(rows, keep):
    """Flag-stratified C / E share over the rows `keep` selects, each stratum weighted by its population times the
    share of its labelled rows kept (the served population of the stratum); 95 % half-width, ratio term ignored."""
    pops = {0: S254_NU, 1: S254_NF}
    est_w, est = 0.0, {"C": 0.0, "E": 0.0}
    var = {"C": 0.0, "E": 0.0}
    kept_n = 0
    parts = []
    for k, Nk in pops.items():
        g = [r for r in rows if (0 if r["s"] else 1) == k]
        gk = [r for r in g if keep(r)]
        if not g or not gk:
            continue
        kept_n += len(gk)
        W = Nk * len(gk) / len(g)
        parts.append((W, gk))
        est_w += W
    for W, gk in parts:
        t = len(gk)
        for m in ("C", "E"):
            p = sum(r["_vs"] == m for r in gk) / t
            est[m] += W / est_w * p
            var[m] += (W / est_w) ** 2 * p * (1 - p) / t
    return {"C": est["C"], "E": est["E"], "ci": 1.96 * math.sqrt(var["C"]), "n": kept_n,
            "share": (est_w / (S254_NU + S254_NF)) if est_w else 0.0}


async def part_served(c):
    ids, src = await served_ids(c)
    sql = getattr(relocate, "_HIDE_FLAGGED_SQL", None)
    sql_src = "deployed relocate._HIDE_FLAGGED_SQL" if sql else "audit copy (relocate has no _HIDE_FLAGGED_SQL yet)"
    loc = list(getattr(relocate, "LOCATED_BY_ALLOWED", ("llm", "mapbox")))
    cands = [dict(r) for r in await c.fetch(sql or HIDE_FLAGGED_SQL_COPY, HIDE_OUTCOMES, HIDE_STAMP_V, HIDE_ACCEPT,
                                            loc, None)]
    # a row a person restored (unhide) is never hidden by hide_flagged (`restored`, AA-997 S260 review fix)
    restored_skipped = sum(1 for r in cands if r.get("restored"))
    cands = [r for r in cands if not r.get("restored")]
    hide = {r["id"] for r in cands}
    np_ids = {r["id"] for r in await c.fetch(NON_PLACE_SQL)}
    served_hidden = hide & ids
    out("V served", {"source": src, "served_destinations": len(ids), "hide_sql": sql_src,
                     "hide_selection": {"outcomes": HIDE_OUTCOMES, "stamp_versions": HIDE_STAMP_V,
                                        "stamp_accept": HIDE_ACCEPT}})
    by_c = Counter(r["country"] for r in cands)
    out("V hide_candidates", {"rows": len(cands), "restored_skipped": restored_skipped,
                              "served_now": len(served_hidden),
                              "linked": sum(1 for r in cands if r.get("linked")),
                              "by_outcome": dict(Counter(r["outcome"] for r in cands)),
                              "by_reason": dict(Counter(r["review_reason"] for r in cands).most_common(8)),
                              "by_stamp_version": dict(Counter(r["stamp_v"] for r in cands)),
                              "by_country": dict(by_c.most_common(14)),
                              "non_place_served": len(np_ids & ids)})
    # ---- labelled: all rows (L) vs served now / if hide / if hide + non_place
    V = VERIFIED
    for v in V:
        cur = v.get("_cur")
        v["_did"] = cur["did"] if cur is not None and cur["lat"] is not None else None
        v["_vs"] = served_state(v)
    scen = {"served_now": lambda v: v["_did"] in ids,
            "served_if_hide": lambda v: v["_did"] in ids and v["_did"] not in hide,
            "served_if_hide_np": lambda v: v["_did"] in ids and v["_did"] not in hide and v["_did"] not in np_ids}
    acc = {"all_rows": SUMMARY.get("_all_rows_now")}
    for name, keep in scen.items():
        r = strat_subset(V, keep)
        acc[name] = {"correct": f"{r['C']:.1%} ±{r['ci']:.1%}", "error": f"{r['E']:.1%}", "labelled": r["n"],
                     "coverage": f"{r['share']:.1%}"}
    out("V accuracy", acc)
    # ---- projection over the served population of each state (cells as L, rates from the served labelled rows)
    w = {0: S254_NU / 200, 1: S254_NF / 400}
    pop = [dict(r) for r in await c.fetch(POP_ROWS_SQL)]
    proj = {}
    for name, keep in scen.items():
        a = defaultdict(lambda: [0.0, 0.0, 0])
        for v in V:
            if v["_vs"] in ("C", "E") and keep(v):
                k = cell(v["now_lb"], v["touched"])
                a[k][0] += w[0 if v["s"] else 1] * (v["_vs"] == "C")
                a[k][1] += w[0 if v["s"] else 1]
                a[k][2] += 1
        keep_did = {"served_now": lambda d: d in ids, "served_if_hide": lambda d: d in ids and d not in hide,
                    "served_if_hide_np": lambda d: d in ids and d not in hide and d not in np_ids}[name]
        N = Counter(cell(p["lb"], p["o"]) for p in pop if keep_did(p["did"]))
        est, known, cells = 0.0, 0, {}
        for k, n in N.most_common():
            x = a.get(k)
            rate = x[0] / x[1] if x and x[1] else None
            cells[k] = {"rows": n, "rate": f"{rate:.0%}" if rate is not None else "?", "labelled": x[2] if x else 0}
            if rate is not None:
                est += n * rate
                known += n
        proj[name] = {"correct": pct(est, known), "over": known, "of": sum(N.values()), "cells": cells}
    out("V projection", proj)
    print(f"SERVED AA-997 served-pins accuracy now {acc['served_now']['correct']} (coverage "
          f"{acc['served_now']['coverage']}); if hide_flagged {acc['served_if_hide']['correct']} (coverage "
          f"{acc['served_if_hide']['coverage']}, {len(served_hidden)} served pins hidden); + non_place "
          f"{acc['served_if_hide_np']['correct']}; all rows {acc['all_rows']}; projection served "
          f"{proj['served_now']['correct']} -> if hide {proj['served_if_hide']['correct']} (bar {BAR:.0%})")
    SUMMARY["served"] = {"accuracy": acc, "projection": {k: {x: y for x, y in v.items() if x != "cells"}
                                                         for k, v in proj.items()},
                         "hide_candidates": len(cands), "served_pins_hidden": len(served_hidden),
                         "served_destinations": len(ids), "source": src}


async def main():
    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require", server_settings={
        "application_name": "aa997-audit-relocated", "statement_timeout": "120000",
        "default_transaction_read_only": "on"})
    tr = c.transaction(isolation="repeatable_read", readonly=True)
    await tr.start()
    try:
        now = await c.fetchval("SELECT now()")
        print(f"AA-997 audit_relocated (read-only) at {str(now)[:16]} deployed RULE_VERSION={relocate.RULE_VERSION} "
              f"stamp_v={STAMP_V} accept={ACCEPT} strict_params={geomatch.strict_params(ACCEPT)}")
        SUMMARY["at"] = str(now)[:16]
        chain_start = None
        try:
            async with c.transaction():
                chain_start = await part_jobs(c)
        except Exception as e:  # noqa: BLE001
            print(f"J FAILED {type(e).__name__}: {str(e)[:300]}")
        # stamps are UTC isoformat strings ("2026-10-30T00:12:03.123+00:00"): compared as text, so SINCE is UTC
        since = ENV.get("SINCE") or (chain_start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
                                     if chain_start is not None else JOBS_SINCE)
        SUMMARY["since"] = since
        chain_ids = set()
        for tag, fn in (("S", part_stamps), ("R", part_rows)):
            try:
                async with c.transaction():
                    r = await (fn(c) if tag == "S" else fn(c, since))
                    if tag == "R":
                        chain_ids = r
            except Exception as e:  # noqa: BLE001
                print(f"{tag} FAILED {type(e).__name__}: {str(e)[:300]}")
        labelled = False
        try:
            async with c.transaction():
                await part_labels(c, chain_ids)
            labelled = True
        except Exception as e:  # noqa: BLE001
            print(f"L FAILED {type(e).__name__}: {str(e)[:300]}")
        if labelled:
            try:
                async with c.transaction():
                    await part_served(c)
            except Exception as e:  # noqa: BLE001
                print(f"V FAILED {type(e).__name__}: {str(e)[:300]}")
        SUMMARY.pop("_all_rows_now", None)
    finally:
        await tr.rollback()
        await c.close()
    out("SUMMARY", SUMMARY)


asyncio.run(main())
