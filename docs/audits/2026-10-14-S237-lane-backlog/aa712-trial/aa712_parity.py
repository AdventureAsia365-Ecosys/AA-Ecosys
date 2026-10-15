"""AA-712 trial run (a) parity report — READ-ONLY.

Compares the CIS place pipeline output (geo.*, migration 226) for 3 Laos tours with the frozen
TripPlanner tables (tripplanner.* + shared.destinations), per design 03-design.md §7 run (a):
overnight ids, stop count, geocode distance vs TP <= 25 km, embeddings present, cost per tour.

Runs inside the CIS api container (python3 + asyncpg + boto3). Prints exactly ONE JSON line.
No writes: the session is set to default_transaction_read_only and only SELECTs are issued.

Note on TP coordinates: CIS place_geocode may overwrite shared.destinations lat/lng of rows TP
created (may_overwrite llm/mapbox -> geoapify). The frozen TP point is therefore taken from
tripplanner.tour_graph_node (written by the TP graph build) when present; otherwise the live
shared.destinations row is used and flagged (tp_point_src = 'destinations_live', plus
'overwritten_since_trial' when geocoded_at >= TRIAL_START).
"""
import asyncio
import json
import math
import re
import sys
import unicodedata
from datetime import datetime, timezone
from urllib.parse import unquote, urlparse

TRIAL_START = datetime(2026, 10, 14, 15, 30, tzinfo=timezone.utc)
KM_LIMIT = 25.0
SECRET_ID = "aa-cis/dev/rds"
REGION = "us-west-1"

TOURS = [
    {"tour_id": "fde65bf0-e521-4ca5-8c4a-f0e6cc28b76e", "source_id": "664086a9-df2d-481c-a4fa-af67f782a6a8"},
    {"tour_id": "2bc45c55-fb32-4ca1-818a-62c3353ec556", "source_id": "bd183835-73ef-494e-baf7-fb88e74b57f4"},
    {"tour_id": "16548cba-a702-483d-bbe5-33349c77fdfe", "source_id": "87f71e29-a38b-4c66-9be3-2ead018f8ff8"},
]


def norm(s):
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"\(.*?\)", " ", s)          # CIS may qualify a clashing name: "Name (Locality, Country)"
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def haversine_km(lat1, lng1, lat2, lng2):
    if None in (lat1, lng1, lat2, lng2):
        return None
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 2)


def err(e):
    return f"{type(e).__name__}: {e}"[:500]


def get_dsn():
    import boto3
    raw = boto3.client("secretsmanager", region_name=REGION).get_secret_value(SecretId=SECRET_ID)["SecretString"]
    raw = raw.strip()
    if raw.startswith("{"):  # defensive: plain DSN expected, but accept a JSON wrapper
        obj = json.loads(raw)
        raw = obj.get("dsn") or obj.get("url") or obj.get("DATABASE_URL") or raw
    return raw


async def connect():
    import asyncpg
    u = urlparse(get_dsn())
    conn = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=unquote(u.username or ""),
                                 password=unquote(u.password or ""), database=(u.path or "/").lstrip("/"),
                                 ssl="require", timeout=30)
    await conn.execute("SET default_transaction_read_only = on")
    await conn.execute("SET statement_timeout = '60s'")
    return conn


async def table_exists(conn, fq):
    return bool(await conn.fetchval("SELECT to_regclass($1) IS NOT NULL", fq))


async def column_exists(conn, schema, table, col):
    return bool(await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_schema=$1 AND table_name=$2 AND column_name=$3)", schema, table, col))


def rows(rs):
    return [dict(r) for r in rs]


async def dest_map(conn, ids):
    ids = [str(i) for i in ids if i]
    if not ids:
        return {}
    rs = await conn.fetch(
        """SELECT id::text AS id, name, country, lat, lng, located_by, geo_status, geo_precision,
                  geocoder_provider, geocoded_at, duplicate_of::text AS duplicate_of, review_reason
             FROM shared.destinations WHERE id = ANY($1::uuid[])""", list(set(ids)))
    return {r["id"]: dict(r) for r in rs}


async def tp_frozen_points(conn, ids):
    """destination_id -> (lat, lng, name) from tripplanner.tour_graph_node (frozen TP graph)."""
    ids = [str(i) for i in ids if i]
    if not ids or not await table_exists(conn, "tripplanner.tour_graph_node"):
        return {}
    rs = await conn.fetch(
        "SELECT destination_id::text AS id, lat, lng, name FROM tripplanner.tour_graph_node "
        "WHERE destination_id = ANY($1::uuid[])", list(set(ids)))
    return {r["id"]: dict(r) for r in rs}


def tp_point(did, frozen, dests):
    if did in frozen:
        f = frozen[did]
        return f["lat"], f["lng"], "tp_graph_node"
    d = dests.get(did)
    if d:
        src = "destinations_live"
        ga = d.get("geocoded_at")
        if ga is not None and ga >= TRIAL_START:
            src += "_overwritten_since_trial"
        return d["lat"], d["lng"], src
    return None, None, "missing"


async def tour_report(conn, t):
    out = {"tour_id": t["tour_id"], "source_id": t["source_id"]}
    keys = [t["source_id"], t["tour_id"]]

    # ── CIS build ─────────────────────────────────────────────────────────────
    cis_src = None
    try:
        b = await conn.fetch(
            """SELECT source_id, tour_id::text AS tour_id, country, status, rule_version, counts, cost_usd,
                      built_at, job_id::text AS job_id, days_hash IS NOT NULL AS has_days_hash
                 FROM geo.tour_build WHERE source_id = ANY($1::text[]) OR tour_id = $2::uuid""",
            keys, t["tour_id"])
        out["cis_build"] = rows(b)
        for r in out["cis_build"]:
            if isinstance(r.get("counts"), str):
                try:
                    r["counts"] = json.loads(r["counts"])
                except Exception:  # noqa: BLE001
                    pass
        cis_src = b[0]["source_id"] if b else None
        if cis_src and cis_src != t["source_id"]:
            out["cis_build_note"] = f"geo keyed by {cis_src}, expected source_id {t['source_id']}"
    except Exception as e:  # noqa: BLE001
        out["cis_build_error"] = err(e)
    cis_keys = [cis_src] if cis_src else keys

    # ── TP key resolution ─────────────────────────────────────────────────────
    tp_key = None
    try:
        r = await conn.fetch(
            "SELECT source_tour_id, count(*)::int AS n FROM tripplanner.itinerary_components "
            "WHERE source_tour_id = ANY($1::text[]) GROUP BY 1", keys)
        out["tp_component_keys"] = {x["source_tour_id"]: x["n"] for x in r}
        if r:
            tp_key = max(r, key=lambda x: x["n"])["source_tour_id"]
        else:
            r2 = await conn.fetch("SELECT DISTINCT source_tour_id FROM tripplanner.tour_day "
                                  "WHERE source_tour_id = ANY($1::text[])", keys)
            tp_key = r2[0]["source_tour_id"] if r2 else None
        out["tp_key"] = tp_key
        out["tp_key_kind"] = ("source_id" if tp_key == t["source_id"] else
                              "tour_id" if tp_key == t["tour_id"] else None)
    except Exception as e:  # noqa: BLE001
        out["tp_key_error"] = err(e)
    tp_keys = [tp_key] if tp_key else keys

    # ── days ──────────────────────────────────────────────────────────────────
    cis_days, tp_days = [], []
    try:
        cis_days = rows(await conn.fetch(
            """SELECT day_index, title, overnight_place, anchor_place, overnight_destination_id::text AS dest,
                      extracted_by, is_transit_day, places
                 FROM geo.tour_day WHERE source_id = ANY($1::text[]) ORDER BY day_index""", cis_keys))
    except Exception as e:  # noqa: BLE001
        out["cis_days_error"] = err(e)
    try:
        tp_days = rows(await conn.fetch(
            """SELECT day_index, title, overnight_place, overnight_destination_id::text AS dest, extracted_by, places
                 FROM tripplanner.tour_day WHERE source_tour_id = ANY($1::text[]) ORDER BY day_index""", tp_keys))
    except Exception as e:  # noqa: BLE001
        out["tp_days_error"] = err(e)
    out["days"] = {
        "cis": len(cis_days), "tp": len(tp_days),
        "cis_index_range": [cis_days[0]["day_index"], cis_days[-1]["day_index"]] if cis_days else None,
        "tp_index_range": [tp_days[0]["day_index"], tp_days[-1]["day_index"]] if tp_days else None,
        "cis_extracted_by": {},
        "cis_transit_days": sum(1 for d in cis_days if d.get("is_transit_day")),
    }
    for d in cis_days:
        k = d.get("extracted_by") or "?"
        out["days"]["cis_extracted_by"][k] = out["days"]["cis_extracted_by"].get(k, 0) + 1

    # ── places / components ───────────────────────────────────────────────────
    cis_places, tp_comps = [], []
    try:
        cis_places = rows(await conn.fetch(
            """SELECT component_id::text AS component_id, day_index, name, name_norm, country_norm, locality_norm,
                      destination_id::text AS dest, place_card_id::text AS card, activity,
                      (embedding IS NOT NULL) AS has_emb
                 FROM geo.tour_place WHERE source_id = ANY($1::text[]) ORDER BY day_index, name""", cis_keys))
    except Exception as e:  # noqa: BLE001
        out["cis_places_error"] = err(e)
    try:
        tp_comps = rows(await conn.fetch(
            """SELECT source_day_index AS day_index, name, destination_id::text AS dest, activity,
                      (embedding IS NOT NULL) AS has_emb
                 FROM tripplanner.itinerary_components WHERE source_tour_id = ANY($1::text[])
                ORDER BY source_day_index, name""", tp_keys))
    except Exception as e:  # noqa: BLE001
        out["tp_components_error"] = err(e)

    all_ids = ({p["dest"] for p in cis_places} | {c["dest"] for c in tp_comps}
               | {d["dest"] for d in cis_days} | {d["dest"] for d in tp_days})
    all_ids.discard(None)
    dests, frozen = {}, {}
    try:
        dests = await dest_map(conn, all_ids)
        frozen = await tp_frozen_points(conn, all_ids)
    except Exception as e:  # noqa: BLE001
        out["destinations_error"] = err(e)

    cis_dest_ids = {p["dest"] for p in cis_places if p["dest"]}
    tp_dest_ids = {c["dest"] for c in tp_comps if c["dest"]}
    out["places"] = {
        "cis_components": len(cis_places), "tp_components": len(tp_comps),
        "cis_distinct_destinations": len(cis_dest_ids), "tp_distinct_destinations": len(tp_dest_ids),
        "shared_destination_ids": len(cis_dest_ids & tp_dest_ids),
        "cis_unlinked_components": sum(1 for p in cis_places if not p["dest"]),
        "cis_with_place_card": sum(1 for p in cis_places if p["card"]),
        "cis_activity": {}, "tp_activity": {},
    }
    for p in cis_places:
        out["places"]["cis_activity"][p["activity"]] = out["places"]["cis_activity"].get(p["activity"], 0) + 1
    for c in tp_comps:
        out["places"]["tp_activity"][c["activity"]] = out["places"]["tp_activity"].get(c["activity"], 0) + 1

    # ── embeddings ────────────────────────────────────────────────────────────
    out["embeddings"] = {
        "cis_present": sum(1 for p in cis_places if p["has_emb"]), "cis_total": len(cis_places),
        "tp_present": sum(1 for c in tp_comps if c["has_emb"]), "tp_total": len(tp_comps),
    }

    # ── located_by / precision / geo_status of CIS destinations ───────────────
    lb, prec, gs = {}, {}, {}
    for did in cis_dest_ids:
        d = dests.get(did) or {}
        for bucket, key in ((lb, "located_by"), (prec, "geo_precision"), (gs, "geo_status")):
            v = d.get(key) or "null"
            bucket[v] = bucket.get(v, 0) + 1
    out["cis_located_by"] = lb
    out["cis_precision"] = prec
    out["cis_geo_status"] = gs
    out["cis_suspect_destinations"] = sorted(
        {dests[i]["name"] for i in cis_dest_ids if dests.get(i, {}).get("geo_status") == "suspect"})
    out["cis_review_reasons"] = sorted(
        {f"{dests[i]['name']}: {dests[i]['review_reason']}" for i in cis_dest_ids
         if dests.get(i, {}).get("review_reason")})

    # ── geo.place_name status for this tour's names ───────────────────────────
    try:
        if cis_places:
            pn = await conn.fetch(
                """SELECT DISTINCT pn.display_name, pn.status, pn.tries, pn.last_error
                     FROM geo.place_name pn
                     JOIN geo.tour_place tp ON tp.name_norm = pn.name_norm AND tp.country_norm = pn.country_norm
                                           AND tp.locality_norm = pn.locality_norm
                    WHERE tp.source_id = ANY($1::text[])""", cis_keys)
            st = {}
            for r in pn:
                st[r["status"]] = st.get(r["status"], 0) + 1
            out["place_name_status"] = st
            out["place_name_not_resolved"] = [
                {"name": r["display_name"], "status": r["status"], "tries": r["tries"],
                 "last_error": (r["last_error"] or "")[:160] or None}
                for r in pn if r["status"] != "resolved"]
    except Exception as e:  # noqa: BLE001
        out["place_name_error"] = err(e)

    # ── overnight per day: CIS vs TP ──────────────────────────────────────────
    try:
        tp_by_day = {d["day_index"]: d for d in tp_days}
        offset = 0
        if cis_days and tp_days and cis_days[0]["day_index"] != tp_days[0]["day_index"]:
            offset = tp_days[0]["day_index"] - cis_days[0]["day_index"]
        per_day, same_id, same_name, both_null = [], 0, 0, 0
        for d in cis_days:
            tp = tp_by_day.get(d["day_index"] + offset)
            cd, td = d["dest"], (tp or {}).get("dest")
            cname = (dests.get(cd) or {}).get("name") if cd else None
            tname = (dests.get(td) or {}).get("name") if td else None
            match = None
            if cd and td and cd == td:
                match, same_id = "id", same_id + 1
            elif not cd and not td:
                match, both_null = "both_null", both_null + 1
            else:
                c_names = {norm(cname), norm(d["overnight_place"]), norm(d.get("anchor_place"))} - {""}
                t_names = {norm(tname), norm((tp or {}).get("overnight_place"))} - {""}
                if c_names & t_names:
                    match, same_name = "name", same_name + 1
            km = None
            if cd and td:
                c = dests.get(cd) or {}
                tla, tln, src = tp_point(td, frozen, dests)
                km = haversine_km(c.get("lat"), c.get("lng"), tla, tln)
            per_day.append({"day": d["day_index"], "cis": cname or d["overnight_place"], "cis_id": cd,
                            "tp": tname or (tp or {}).get("overnight_place"), "tp_id": td,
                            "match": match, "km": km})
        compared = [x for x in per_day if x["km"] is not None]
        out["overnight"] = {
            "day_index_offset_applied": offset,
            "same_id": same_id, "same_name_diff_id": same_name, "both_null": both_null,
            "mismatch": len(per_day) - same_id - same_name - both_null,
            "cis_null": sum(1 for x in per_day if not x["cis_id"]),
            "tp_null": sum(1 for x in per_day if not x["tp_id"]),
            "km_compared": len(compared),
            "km_le_25": sum(1 for x in compared if x["km"] <= KM_LIMIT),
            "km_gt_25": [x for x in compared if x["km"] > KM_LIMIT],
            "per_day": per_day,
        }
    except Exception as e:  # noqa: BLE001
        out["overnight_error"] = err(e)

    # ── place geocode distance: CIS point vs TP frozen point ──────────────────
    try:
        tp_index = {}   # norm name -> tp destination id
        for c in tp_comps:
            if not c["dest"]:
                continue
            for n in (norm((dests.get(c["dest"]) or {}).get("name")), norm(c["name"])):
                if n:
                    tp_index.setdefault(n, c["dest"])
        pairs, unmatched, seen, matched_tp = [], [], set(), set()
        for p in cis_places:
            cd = p["dest"]
            if not cd or cd in seen:
                continue
            seen.add(cd)
            cdest = dests.get(cd) or {}
            if cd in tp_dest_ids:
                td, how = cd, "id"
            else:
                td = tp_index.get(norm(cdest.get("name"))) or tp_index.get(norm(p["name"]))
                how = "name" if td else None
            if not td:
                unmatched.append(cdest.get("name") or p["name"])
                continue
            matched_tp.add(td)
            tla, tln, src = tp_point(td, frozen, dests)
            km = haversine_km(cdest.get("lat"), cdest.get("lng"), tla, tln)
            pairs.append({"cis": cdest.get("name"), "tp": (dests.get(td) or {}).get("name"), "match": how,
                          "km": km, "tp_point_src": src, "located_by": cdest.get("located_by"),
                          "precision": cdest.get("geo_precision"), "geo_status": cdest.get("geo_status")})
        compared = [x for x in pairs if x["km"] is not None]
        src_counts = {}
        for x in pairs:
            src_counts[x["tp_point_src"]] = src_counts.get(x["tp_point_src"], 0) + 1
        tp_only = sorted({(dests.get(i) or {}).get("name") or i for i in tp_dest_ids - matched_tp})
        out["geocode_distance"] = {
            "matched": len(pairs), "matched_by_id": sum(1 for x in pairs if x["match"] == "id"),
            "matched_by_name": sum(1 for x in pairs if x["match"] == "name"),
            "km_compared": len(compared), "km_le_25": sum(1 for x in compared if x["km"] <= KM_LIMIT),
            "km_gt_25": sorted([x for x in compared if x["km"] > KM_LIMIT], key=lambda x: -x["km"]),
            "max_km": max((x["km"] for x in compared), default=None),
            "tp_point_src": src_counts,
            "cis_only_places": sorted(set(unmatched)),
            "tp_only_places": tp_only,
        }
    except Exception as e:  # noqa: BLE001
        out["geocode_distance_error"] = err(e)

    # ── graph rows ────────────────────────────────────────────────────────────
    g = {}
    try:
        build = await conn.fetchrow(
            "SELECT build_id::text AS build_id, built_at, stats FROM geo.graph_build WHERE is_current LIMIT 1")
        g["cis_current_build"] = build["build_id"] if build else None
        g["cis_build_at"] = build["built_at"] if build else None
        if build:
            bid = build["build_id"]
            g["cis_stops"] = await conn.fetchval(
                "SELECT count(*)::int FROM geo.tour_stop WHERE build_id=$1::uuid AND source_id = ANY($2::text[])",
                bid, cis_keys)
            g["cis_stops_by_source"] = {r["source"]: r["n"] for r in await conn.fetch(
                "SELECT source, count(*)::int AS n FROM geo.tour_stop WHERE build_id=$1::uuid "
                "AND source_id = ANY($2::text[]) GROUP BY 1", bid, cis_keys)}
            g["cis_legs"] = await conn.fetchval(
                "SELECT count(*)::int FROM geo.tour_leg WHERE build_id=$1::uuid AND source_id = ANY($2::text[])",
                bid, cis_keys)
            g["cis_nodes"] = await conn.fetchval(
                "SELECT count(*)::int FROM geo.graph_node WHERE build_id=$1::uuid AND source_ids && $2::text[]",
                bid, cis_keys)
            g["cis_edges"] = await conn.fetchval(
                "SELECT count(*)::int FROM geo.graph_edge WHERE build_id=$1::uuid AND source_ids && $2::text[]",
                bid, cis_keys)
            g["cis_stop_ids"] = [r["d"] for r in await conn.fetch(
                "SELECT destination_id::text AS d FROM geo.tour_stop WHERE build_id=$1::uuid "
                "AND source_id = ANY($2::text[]) ORDER BY day_index", bid, cis_keys)]
    except Exception as e:  # noqa: BLE001
        g["cis_error"] = err(e)
    try:
        if await table_exists(conn, "tripplanner.tour_stop"):
            g["tp_stops"] = await conn.fetchval(
                "SELECT count(*)::int FROM tripplanner.tour_stop WHERE source_tour_id = ANY($1::text[])", tp_keys)
            g["tp_stops_by_source"] = {r["source"]: r["n"] for r in await conn.fetch(
                "SELECT source, count(*)::int AS n FROM tripplanner.tour_stop WHERE source_tour_id = ANY($1::text[]) "
                "GROUP BY 1", tp_keys)}
            g["tp_stop_ids"] = [r["d"] for r in await conn.fetch(
                "SELECT destination_id::text AS d FROM tripplanner.tour_stop WHERE source_tour_id = ANY($1::text[]) "
                "ORDER BY day_index", tp_keys)]
        if await table_exists(conn, "tripplanner.tour_leg"):
            g["tp_legs"] = await conn.fetchval(
                "SELECT count(*)::int FROM tripplanner.tour_leg WHERE source_tour_id = ANY($1::text[])", tp_keys)
        if await table_exists(conn, "tripplanner.tour_graph_node"):
            g["tp_nodes"] = await conn.fetchval(
                "SELECT count(*)::int FROM tripplanner.tour_graph_node WHERE tour_ids && $1::text[]", tp_keys)
        if await table_exists(conn, "tripplanner.tour_graph_edge"):
            g["tp_edges"] = await conn.fetchval(
                "SELECT count(*)::int FROM tripplanner.tour_graph_edge WHERE tour_ids && $1::text[]", tp_keys)
        if "cis_stop_ids" in g and "tp_stop_ids" in g:
            a, b = set(g["cis_stop_ids"]), set(g["tp_stop_ids"])
            g["stop_ids_shared"] = len(a & b)
            g["stop_ids_cis_only"] = sorted({(dests.get(i) or {}).get("name") or i for i in a - b})
            g["stop_ids_tp_only"] = sorted({(dests.get(i) or {}).get("name") or i for i in b - a})
    except Exception as e:  # noqa: BLE001
        g["tp_error"] = err(e)
    out["graph"] = g

    # ── per-tour LLM cost via the build's job + jobs for this tour ────────────
    try:
        jobs = rows(await conn.fetch(
            """SELECT id::text AS id, kind, status, cost_usd, created_at, finished_at,
                      left(coalesce(error, ''), 200) AS error, result->>'status' AS result_status
                 FROM shared.job
                WHERE created_at >= $1::timestamptz AND kind IN ('place_extract', 'place_geocode', 'tour_graph_build')
                  AND (payload->>'tour_id' = ANY($2::text[]) OR payload->>'source_id' = ANY($2::text[]))
                ORDER BY created_at""", TRIAL_START, keys))
        out["jobs"] = jobs
        job_ids = [j["id"] for j in jobs]
        if job_ids:
            cr = await conn.fetch(
                """SELECT stage, count(*)::int AS calls, coalesce(sum(cost_usd), 0) AS cost_usd,
                          count(*) FILTER (WHERE cost_usd IS NULL)::int AS unpriced
                     FROM shared.llm_call_log WHERE job_id = ANY($1::uuid[]) GROUP BY stage ORDER BY stage""",
                job_ids)
            out["llm_cost_by_job"] = rows(cr)
            out["llm_cost_by_job_total"] = sum(float(r["cost_usd"]) for r in cr)
    except Exception as e:  # noqa: BLE001
        out["jobs_error"] = err(e)

    return out


async def overall(conn):
    o = {}
    try:
        rs = await conn.fetch(
            """SELECT stage, role, count(*)::int AS calls, coalesce(sum(cost_usd), 0) AS cost_usd,
                      coalesce(sum(tokens_in), 0)::bigint AS tokens_in, coalesce(sum(tokens_out), 0)::bigint AS tokens_out,
                      count(*) FILTER (WHERE cost_usd IS NULL)::int AS unpriced,
                      count(*) FILTER (WHERE fallback_used)::int AS fallbacks,
                      array_agg(DISTINCT model) AS models
                 FROM shared.llm_call_log
                WHERE stage LIKE 'a3_place%' AND created_at >= $1::timestamptz
                GROUP BY stage, role ORDER BY stage, role""", TRIAL_START)
        o["llm_by_stage"] = rows(rs)
        total = sum(float(r["cost_usd"]) for r in rs)
        o["llm_total_usd"] = round(total, 6)
        o["llm_cost_per_tour_usd"] = round(total / len(TOURS), 6)
        o["llm_calls"] = sum(r["calls"] for r in rs)
    except Exception as e:  # noqa: BLE001
        o["llm_error"] = err(e)
    try:
        cols = "provider, count(*)::int AS rows, coalesce(sum(requests), 0)::int AS requests"
        if await column_exists(conn, "geo", "geocode_call", "cost_usd"):
            cols += ", coalesce(sum(cost_usd), 0) AS cost_usd"
        rs = await conn.fetch(
            f"SELECT {cols} FROM geo.geocode_call WHERE called_at >= $1::timestamptz GROUP BY provider ORDER BY provider",
            TRIAL_START)
        o["geocoder_since_trial"] = rows(rs)
        rs2 = await conn.fetch(f"SELECT {cols} FROM geo.geocode_call GROUP BY provider ORDER BY provider")
        o["geocoder_all_time"] = rows(rs2)
    except Exception as e:  # noqa: BLE001
        o["geocoder_error"] = err(e)
    try:
        bc = await conn.fetchrow(
            "SELECT count(*)::int AS builds, coalesce(sum(cost_usd), 0) AS cost_usd FROM geo.tour_build "
            "WHERE source_id = ANY($1::text[]) OR tour_id = ANY($2::uuid[])",
            [t["source_id"] for t in TOURS] + [t["tour_id"] for t in TOURS], [t["tour_id"] for t in TOURS])
        o["tour_build_cost"] = dict(bc)
    except Exception as e:  # noqa: BLE001
        o["tour_build_cost_error"] = err(e)
    try:
        o["place_name_status_all"] = {r["status"]: r["n"] for r in await conn.fetch(
            "SELECT status, count(*)::int AS n FROM geo.place_name GROUP BY 1")}
        o["destinations_written_since_trial"] = {f"{r['located_by']}/{r['geo_precision']}/{r['geo_status']}": r["n"]
                                                 for r in await conn.fetch(
            "SELECT located_by, geo_precision, geo_status, count(*)::int AS n FROM shared.destinations "
            "WHERE geocoded_at >= $1::timestamptz OR located_at >= $1::timestamptz GROUP BY 1, 2, 3", TRIAL_START)}
    except Exception as e:  # noqa: BLE001
        o["status_error"] = err(e)
    return o


async def main():
    report = {"report": "aa712_parity_trial_a", "trial_start": TRIAL_START.isoformat(), "km_limit": KM_LIMIT}
    conn = None
    try:
        conn = await connect()
        report["db_now"] = await conn.fetchval("SELECT now()")
        report["tours"] = []
        for t in TOURS:
            try:
                report["tours"].append(await tour_report(conn, t))
            except Exception as e:  # noqa: BLE001
                report["tours"].append({"tour_id": t["tour_id"], "error": err(e)})
        report["overall"] = await overall(conn)
    except Exception as e:  # noqa: BLE001
        report["fatal"] = err(e)
    finally:
        if conn is not None:
            try:
                await conn.close()
            except Exception:  # noqa: BLE001
                pass
    sys.stdout.write(json.dumps(report, default=str, ensure_ascii=False, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
