"""AA-997 interim audit (S257) — READ-ONLY. Run inside the CIS api container: tools/ecs/ecsx.sh <this file>.

DATABASE_URL (cis_app), ssl='require', application_name 'aa997-interim-audit', statement_timeout 60 s, one
REPEATABLE READ READ ONLY transaction (rolled back). No write, no paid call. Prints aggregates only (< 150 lines).

1. place_relocate job results so far (shared.job kind place_relocate) + per-country outcome from the row stamps
   (shared.destinations.geocoder_meta.relocate = {v, outcome, at, moved_km?}) and rows still to do.
2. S254 metric on the CURRENT data: the 600 rows verified in S254 (docs/audits/2026-10-28-S254-geocode-audit/
   verified.json, embedded below) re-scored against today's point. Rule: a row judged correct stays correct while its
   point stays within the S254 tolerance (4 km site / 5 km other) of the old point; a row judged wrong becomes correct
   when its point is now within that tolerance of one `expected` point (or, for a Hong Kong / Macao ISO error, when the
   ISO is now HK / MO); a not-a-place row is correct when it is flagged non_place / hidden / gone; unsure stays unsure;
   a moved wrong row with no expected point is unsure. Weights = S254 strata (flag status, provenance x flag).
   Plus the S254 rules.py flags (dup_coords, precision_area_site, provenance_null, tour_spread) on today's rows.
3. Tours whose places are all geocoder-confirmed (located_by geoapify / manual, not suspect), and the 14 + 2 tours of
   AA-990 recheck_14 (.tmp-session/S255/aa990/recheck_14.py) with the same route bar (pinned days >= 0.5 x days).
"""
import asyncio
import json
import math
import os
import re
import statistics
from collections import Counter, defaultdict

import asyncpg

RULE_VERSION = "aa997.1"
SAME_KM = 0.05
SITE_TOL_KM, OTHER_TOL_KM = 4.0, 5.0
# S254 populations (flags-summary.json): resolved 7,924 = flagged 2,321 + unflagged 5,603; provenance x flagged cells
S254_T, S254_NF, S254_NU = 7924, 2321, 5603
S254_PROV = {("l", 1): 1664, ("l", 0): 2106, ("m", 1): 210, ("g", 0): 3497, ("g", 1): 447}
S254_RULES = {"dup_coords": 927, "precision_area_site": 755, "provenance_null": 652, "tour_spread": 260}
PENDING_14 = ["ac1d5f9b", "b5c3c908", "e864ec99", "0c608efd", "a423e72e", "b9b39260", "b7188d60", "3eda85ad",
              "a44bf9c4", "c99a1434", "229f2c60", "56e78342", "c6b24380", "2d9ccb23"]
LEG_RULE_2 = ["90b88118", "2020d00f"]
SITE_STRICT = set(("temple monastery museum hotel station bridge waterfall falls fort palace pagoda stupa shrine church "
                   "mosque cathedral gompa dzong tomb mausoleum tower airport cave caves lodge resort zoo monument "
                   "memorial castle observatory gallery statue mandir gurudwara haveli stepwell baori mahal masjid "
                   "minar chorten lhakhang goemba dargah kovil brewery winery dam lighthouse pier jetty wat").split())
OK_LOC = ("geoapify", "manual")

# nn name_norm, cn country_norm, loc locality_norm, tour tour-name prefix, lat/lng/iso S254 point, v verdict
# (C correct, TC too_coarse, WP wrong_place, WC wrong_country, NP not_a_place, U unsure), exp [[lat, lng], ...],
# xi expected ISO (HK/MO ISO errors), s random sample, f flagged, lb S254 located_by (g/l/m), site site-type name
F = ("nn", "cn", "loc", "tour", "lat", "lng", "iso", "v", "exp", "xi", "s", "f", "lb", "site")
VERIFIED_JSON = "__VERIFIED__"
VERIFIED = [dict(zip(F, r)) for r in json.loads(VERIFIED_JSON)]
ERR = ("TC", "WP", "WC")


def j(x):
    return json.loads(x) if isinstance(x, str) else (x or {})


def km(a_lat, a_lng, b_lat, b_lng):
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b_lng - a_lng) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(min(1.0, h)))


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "n/a"


# ---------------------------------------------------------------- 1. relocate jobs
async def part1(c):
    jobs = await c.fetch("SELECT status, payload, result, created_at, finished_at, run_after FROM shared.job"
                         " WHERE kind = 'place_relocate' ORDER BY created_at")
    by = Counter()
    keys = ("rows", "done", "errors", "confirmed", "non_place", "off_route", "llm_point", "country_fixed", "skipped",
            "geocoder_requests")
    tot, last, moved_max, waiting = Counter(), None, 0.0, []
    for r in jobs:
        p, res = j(r["payload"]), j(r["result"])
        mode = p.get("mode") or "dry_run"
        by[(mode, r["status"], res.get("status") or "-")] += 1
        if mode == "apply" and res:
            for k in keys:
                tot[k] += int(res.get(k) or 0)
            moved_max = max(moved_max, float(res.get("moved_km_max") or 0))
            tot["cost_usd_x1e6"] += int(round(float(res.get("geocoder_cost_usd") or 0) * 1e6))
            if r["finished_at"] and "remaining" in res:
                last = (r["finished_at"], res["remaining"])
        if r["status"] in ("queued", "running"):
            waiting.append((r["status"], str(r["run_after"])[:16]))
    print(f"P1 jobs={len(jobs)} by(mode,status,result)=" + json.dumps({"/".join(k): n for k, n in sorted(by.items())}))
    print("P1 apply sums " + json.dumps({k: tot[k] for k in keys}) +
          f" cost_usd={tot['cost_usd_x1e6'] / 1e6:.4f} moved_km_max={moved_max:.0f}")
    print(f"P1 last apply finished={str(last[0])[:16] if last else None} remaining={last[1] if last else None}"
          f" waiting={waiting[:4]}")
    stamps = await c.fetch("""
        SELECT coalesce(country_iso2, '??') AS iso, geocoder_meta -> 'relocate' ->> 'outcome' AS o, count(*) AS n
          FROM shared.destinations WHERE geocoder_meta ? 'relocate' GROUP BY 1, 2""")
    left = await c.fetch("""
        SELECT coalesce(country_iso2, '??') AS iso, count(*) AS n FROM shared.destinations d
         WHERE located_by = 'llm' AND duplicate_of IS NULL AND geo_status <> 'manual'
           AND (geocoder_meta -> 'relocate' ->> 'v') IS DISTINCT FROM $1 GROUP BY 1""", RULE_VERSION)
    per = defaultdict(Counter)
    for s in stamps:
        per[s["iso"]][s["o"]] += s["n"]
    for lft in left:
        per[lft["iso"]]["left"] += lft["n"]
    allc = Counter()
    for v in per.values():
        allc.update(v)
    print("P1 stamped outcomes (all) " + json.dumps({k: allc[k] for k in
          ("confirmed", "non_place", "off_route", "llm_point")}) + f" left_llm={allc['left']}")
    order = sorted(per, key=lambda k: -sum(per[k].values()))
    other = Counter()
    for iso in order:
        v = per[iso]
        if order.index(iso) >= 15:
            other.update(v)
            continue
        print(f"P1 {iso} conf={v['confirmed']} np={v['non_place']} off={v['off_route']} llm={v['llm_point']}"
              f" left={v['left']}")
    if other:
        print(f"P1 other conf={other['confirmed']} np={other['non_place']} off={other['off_route']}"
              f" llm={other['llm_point']} left={other['left']}")
    mv = await c.fetch("""
        SELECT width_bucket((geocoder_meta -> 'relocate' ->> 'moved_km')::float8, ARRAY[1, 5, 25, 100]::float8[]) AS b,
               count(*) AS n FROM shared.destinations
         WHERE geocoder_meta -> 'relocate' ->> 'outcome' = 'confirmed' GROUP BY 1 ORDER BY 1""")
    lab = {0: "<1", 1: "1-5", 2: "5-25", 3: "25-100", 4: ">100", None: "?"}
    print("P1 confirmed moved_km " + json.dumps({lab[m["b"]]: m["n"] for m in mv}))
    rr = await c.fetch("""
        SELECT coalesce(split_part(review_reason, ':', 1), '-') AS r, count(*) AS n FROM shared.destinations
         WHERE duplicate_of IS NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 9""")
    lb = await c.fetch("SELECT coalesce(located_by, '-') AS l, count(*) AS n FROM shared.destinations"
                       " WHERE duplicate_of IS NULL GROUP BY 1 ORDER BY 2 DESC")
    print("P1 destinations review_reason " + json.dumps({x["r"]: x["n"] for x in rr}) +
          " located_by " + json.dumps({x["l"]: x["n"] for x in lb}))


# ---------------------------------------------------------------- 2. S254 metric now
def rescore(v, cur):
    """(state C/E/U/M, tag) for one verified row against its current row (module docstring)."""
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
    """Stratified correct / error rate with finite-population correction (S254 build_report.strat)."""
    T = sum(pops.values())
    est = {"C": 0.0, "E": 0.0}
    var = {"C": 0.0, "E": 0.0}
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


async def part2(c):
    names = sorted({v["nn"] for v in VERIFIED})
    rows = await c.fetch("""
        SELECT pn.name_norm, pn.country_norm, pn.locality_norm, coalesce(pn.tour_name, '') AS tour_name, pn.status,
               pn.last_error, d.lat, d.lng, d.located_by, d.geo_status, d.review_reason, d.country_iso2,
               d.geocoder_meta -> 'relocate' AS reloc
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
        o = j(cur["reloc"]).get("outcome") if cur is not None and cur["reloc"] else None
        v["touched"] = o
        v["now_lb"] = cur["located_by"] if cur is not None else None
    V = VERIFIED
    tags = Counter(v["tag"] for v in V)
    print(f"P2 verified={len(V)} matched={sum(v['found'] for v in V)} tags=" + json.dumps(dict(tags)))
    for name, g in (("random200", [v for v in V if v["s"]]), ("flagged400", [v for v in V if not v["s"]])):
        b, a = Counter(v["before"] for v in g), Counter(v["state"] for v in g)
        print(f"P2 {name} before C={b['C']} E={b['E']} U={b['U']} | now C={a['C']} E={a['E']} U={a['U']}"
              f" M={a['M']} | correct {pct(b['C'], len(g))} -> {pct(a['C'], len(g))}")
    for v in V:
        v["_s"] = v["state"]
    for label, fld in (("S254", "before"), ("now", "_s")):
        for v in V:
            v["state"] = v[fld]
        ef = strat(V, lambda r: 0 if r["s"] else 1, {0: S254_NU, 1: S254_NF})
        ep = strat(V, lambda r: (r["lb"], r["f"]), S254_PROV)
        print(f"P2 overall {label}: flag-strat correct {ef['C'][0]:.1%} ±{ef['C'][1]:.1%} error {ef['E'][0]:.1%}"
              f" | prov-strat correct {ep['C'][0]:.1%} ±{ep['C'][1]:.1%}")
    for v in V:
        v["state"] = v["_s"]
    t = [v for v in V if v["touched"]]
    u = [v for v in V if not v["touched"] and v["found"]]
    for name, g in (("touched", t), ("untouched", u)):
        b, a = Counter(v["before"] for v in g), Counter(v["state"] for v in g)
        print(f"P2 {name} n={len(g)} (random {sum(v['s'] for v in g)}) correct {pct(b['C'], len(g))} ->"
              f" {pct(a['C'], len(g))}  err {pct(b['E'], len(g))} -> {pct(a['E'], len(g))}")
    print("P2 touched by outcome " + json.dumps({o: f"{sum(v['state'] == 'C' for v in t if v['touched'] == o)}/"
          f"{sum(1 for v in t if v['touched'] == o)}" for o in sorted({v['touched'] for v in t})}))
    print("P2 touched transitions " + json.dumps(dict(Counter(f"{v['v']}>{v['tag']}" for v in t).most_common(12))))
    ul = [v for v in u if v["lb"] == "l"]
    print(f"P2 untouched S254-llm n={len(ul)} correct now {pct(sum(v['state'] == 'C' for v in ul), len(ul))}"
          f" | untouched S254-geoapify n={sum(v['lb'] == 'g' for v in u)} correct now"
          f" {pct(sum(v['state'] == 'C' for v in u if v['lb'] == 'g'), sum(v['lb'] == 'g' for v in u))}")
    # projection: current cells x weighted (S254 inclusion) correct rate of the verified rows now in the cell
    def cell(lb, o):
        if o:
            return "rl_confirmed" if o == "confirmed" else ("rl_non_place" if o == "non_place" else "rl_flagged")
        return {"geoapify": "geoapify", "llm": "llm_untouched", "mapbox": "mapbox", "manual": "manual"}.get(lb, "other")
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
    est, known = 0.0, 0
    parts = []
    for k, n in N.most_common():
        a = acc.get(k)
        rate = a[0] / a[1] if a and a[1] else None
        parts.append(f"{k}={n}" + (f"@{rate:.0%}(n{a[2]})" if rate is not None else "@?"))
        if rate is not None:
            est += n * rate
            known += n
    print("P2 projection cells " + " ".join(parts))
    print(f"P2 projection correct now ~{pct(est, known)} over {known} of {sum(N.values())} resolved rows")
    st = await c.fetch("SELECT status, count(*) AS n FROM geo.place_name GROUP BY 1 ORDER BY 1")
    print("P2 place_name status " + json.dumps({s["status"]: s["n"] for s in st}) +
          " (S254: resolved 7924 pending 1203 unknown 418)")
    await rules_now(c)


async def rules_now(c):
    """rules.py flags 4-7 on today's resolved rows (country/bbox need the S254 maps; 38 / 0 rows then)."""
    rs = await c.fetch("""
        SELECT pn.name_norm, pn.locality, coalesce(pn.tour_name, '') AS tour, d.lat, d.lng, d.geo_precision,
               d.geocoder_provider
          FROM geo.place_name pn JOIN shared.destinations d0 ON d0.id = pn.destination_id
          JOIN shared.destinations d ON d.id = coalesce(d0.duplicate_of, d0.id)
         WHERE pn.status = 'resolved'""")
    fl = defaultdict(set)
    by_pt, by_tour = defaultdict(list), defaultdict(list)
    for i, r in enumerate(rs):
        by_pt[(round(r["lat"], 5), round(r["lng"], 5))].append(i)
        by_tour[r["tour"]].append(i)
        if r["geocoder_provider"] is None:
            fl[i].add("provenance_null")
        if r["geo_precision"] == "area" and set(re.findall(r"[a-z]+", r["name_norm"] or "")) & SITE_STRICT:
            fl[i].add("precision_area_site")
    for idxs in by_pt.values():
        if len({rs[i]["name_norm"] for i in idxs}) >= 3:
            locs = {rs[i]["locality"] for i in idxs}
            if not (len(locs) == 1 and None not in locs):
                for i in idxs:
                    fl[i].add("dup_coords")
    for idxs in by_tour.values():
        if len(idxs) < 2:
            continue
        lim = 300.0 if len(idxs) <= 3 else 800.0
        for i in idxs:
            o = [k for k in idxs if k != i]
            if km(rs[i]["lat"], rs[i]["lng"], statistics.median(rs[k]["lat"] for k in o),
                  statistics.median(rs[k]["lng"] for k in o)) > lim:
                fl[i].add("tour_spread")
    cnt = Counter(f for s in fl.values() for f in s)
    print(f"P2 rules now (resolved {len(rs)}): " + " ".join(f"{k}={cnt[k]}(S254 {S254_RULES[k]})" for k in S254_RULES)
          + f" any4={sum(1 for s in fl.values() if s)}(S254 ~2286)")


# ---------------------------------------------------------------- 3. tours all geocoder-confirmed
TOURS_SQL = """
WITH live AS (SELECT source_id, country FROM geo.tour_build WHERE status <> 'retired'),
links AS (
    SELECT p.source_id, p.destination_id AS did FROM geo.tour_place p JOIN live USING (source_id)
     WHERE p.destination_id IS NOT NULL
    UNION
    SELECT t.source_id, t.overnight_destination_id FROM geo.tour_day t JOIN live USING (source_id)
     WHERE t.overnight_destination_id IS NOT NULL),
canon AS (
    SELECT l.source_id, d.id, d.located_by, d.geo_status, d.review_reason
      FROM links l JOIN shared.destinations d0 ON d0.id = l.did
      JOIN shared.destinations d ON d.id = coalesce(d0.duplicate_of, d0.id)),
per AS (
    SELECT source_id, count(DISTINCT id) AS n,
           count(DISTINCT id) FILTER (WHERE located_by = ANY($1::text[]) AND geo_status <> 'suspect') AS ok,
           count(DISTINCT id) FILTER (WHERE located_by = 'llm') AS llm,
           count(DISTINCT id) FILTER (WHERE located_by = 'mapbox') AS mapbox,
           count(DISTINCT id) FILTER (WHERE review_reason IS NOT NULL) AS flagged
      FROM canon GROUP BY 1),
unl AS (SELECT p.source_id, count(*) AS n FROM geo.tour_place p JOIN live USING (source_id)
         WHERE p.destination_id IS NULL GROUP BY 1)
SELECT live.source_id, coalesce(live.country, '?') AS country, coalesce(per.n, 0) AS n, coalesce(per.ok, 0) AS ok,
       coalesce(per.llm, 0) AS llm, coalesce(per.mapbox, 0) AS mapbox, coalesce(per.flagged, 0) AS flagged,
       coalesce(unl.n, 0) AS unlinked
  FROM live LEFT JOIN per USING (source_id) LEFT JOIN unl USING (source_id)
"""
RECHECK_SQL = """
WITH g AS (SELECT build_id FROM geo.graph_build WHERE is_current)
SELECT b.source_id, b.status,
       (SELECT max(d.day_index) FROM geo.tour_day d WHERE d.source_id = b.source_id) AS days,
       (SELECT count(*) FROM geo.tour_day d JOIN geo.place_name pn ON pn.name_norm = d.anchor_norm
          AND pn.country_norm = d.anchor_country_norm AND pn.locality_norm = d.anchor_locality_norm
         WHERE d.source_id = b.source_id AND pn.status IN ('pending', 'unknown')) AS anchors_unresolved,
       (SELECT count(DISTINCT s.day_index) FROM geo.tour_stop s, g
         WHERE s.build_id = g.build_id AND s.source_id = b.source_id) AS stop_days,
       (SELECT count(DISTINCT p.day_index) FROM geo.tour_place p
         WHERE p.source_id = b.source_id AND p.embedding IS NOT NULL) AS pinned_days
  FROM geo.tour_build b WHERE left(b.source_id, 8) = ANY($1::text[]) ORDER BY b.source_id
"""


async def part3(c):
    rows = await c.fetch(TOURS_SQL, list(OK_LOC))
    strict = [r for r in rows if r["n"] and r["ok"] == r["n"] and r["unlinked"] == 0]
    linked = [r for r in rows if r["n"] and r["ok"] == r["n"]]
    print(f"P3 live tours={len(rows)} all_confirmed(strict: linked all geoapify/manual + 0 unlinked)={len(strict)}"
          f" all_linked_confirmed={len(linked)} with_llm={sum(1 for r in rows if r['llm'])}"
          f" with_mapbox={sum(1 for r in rows if r['mapbox'])} with_flagged={sum(1 for r in rows if r['flagged'])}"
          f" no_places={sum(1 for r in rows if not r['n'])}")
    linked_ids = {r["source_id"] for r in linked}
    share = Counter()
    for r in rows:
        if r["n"]:
            q = r["ok"] / r["n"]
            share["100%" if q == 1 else ">=90%" if q >= .9 else ">=75%" if q >= .75 else "<75%"] += 1
    print("P3 tours by confirmed share " + json.dumps(dict(share)))
    byc = defaultdict(lambda: [0, 0])
    for r in rows:
        byc[r["country"]][0] += 1
        byc[r["country"]][1] += r["source_id"] in linked_ids
    top = sorted(byc.items(), key=lambda kv: -kv[1][0])[:14]
    print("P3 all_linked_confirmed/tours by country " + " ".join(f"{k}={v[1]}/{v[0]}" for k, v in top))
    per = {r["source_id"][:8]: r for r in rows}
    rc = await c.fetch(RECHECK_SQL, PENDING_14 + LEG_RULE_2)
    seen, ok_route, all_conf = set(), 0, 0
    for r in rc:
        sid = r["source_id"][:8]
        seen.add(sid)
        t = per.get(sid)
        days = r["days"] or 0
        route = bool(r["stop_days"]) and days > 0 and r["pinned_days"] >= 0.5 * days
        conf = bool(t and t["n"] and t["ok"] == t["n"])
        ok_route += route
        all_conf += conf
        print(f"P3 {sid} {'leg' if sid in LEG_RULE_2 else 'p14'} build={r['status']} days={days}"
              f" stop_days={r['stop_days']} pinned={r['pinned_days']} route={'Y' if route else 'N'}"
              f" places={t['ok'] if t else '-'}/{t['n'] if t else '-'} llm={t['llm'] if t else '-'}"
              f" flagged={t['flagged'] if t else '-'} unlinked={t['unlinked'] if t else '-'}"
              f" anchors_unresolved={r['anchors_unresolved']} all_confirmed={'Y' if conf else 'N'}")
    print(f"P3 recheck_14 summary: route={ok_route}/{len(rc)} all_confirmed={all_conf}/{len(rc)}"
          f" missing={sorted(set(PENDING_14 + LEG_RULE_2) - seen)}")


async def main():
    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require", server_settings={
        "application_name": "aa997-interim-audit", "statement_timeout": "60000",
        "default_transaction_read_only": "on"})
    tr = c.transaction()
    await tr.start()
    try:
        await c.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        now = await c.fetchval("SELECT now()")
        print(f"AA-997 interim audit (read-only) at {str(now)[:16]} rule {RULE_VERSION}")
        for name, fn in (("P1", part1), ("P2", part2), ("P3", part3)):
            try:
                async with c.transaction():      # savepoint: a failed part does not abort the others
                    await fn(c)
            except Exception as e:  # noqa: BLE001 — report and go on with the next part
                print(f"{name} FAILED {type(e).__name__}: {str(e)[:300]}")
    finally:
        await tr.rollback()
        await c.close()


asyncio.run(main())
