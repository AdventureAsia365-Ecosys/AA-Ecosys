"""AA-712 slice 6b parity — the browse readers on PLACES_SOURCE=legacy vs PLACES_SOURCE=cis, for Laos.

READ-ONLY. Runs the real TripPlanner browse code (route() of backend/browse/handler.py, bundled into the
runner) twice against Dev, as the `tripplanner` DB role (SET ROLE, default_transaction_read_only = on):
once on the frozen TripPlanner tables, once on the CIS catalog views of migration 228. No Bedrock call:
search uses fixed query vectors (embeddings of existing Laos components, read from the frozen table).

Two steps:
  1. local:  python3 aa712-6b-parity.py build <TripPlanner repo root> <runner.zip>
             writes a runnable zip: this file as __main__.py + the TripPlanner backend modules it needs.
  3. local:  python3 aa712-6b-parity.py report <runner output.json>   prints the Markdown result tables.
  2. remote: python3 runner.zip   inside the CIS api container (python3 + asyncpg + boto3 + pydantic), which
             reads the DSN from Secrets Manager aa-cis/dev/rds and prints exactly ONE JSON line.

Compared per reader: /browse/countries (Laos components), /browse/by-country (destinations, components),
/browse/tiles over the Laos box (1-degree cells + one 10-degree cell), /browse/destinations/{id} (component
count per destination), /browse/search (8 query vectors, with and without country=Laos: result count, top-10
overlap), /browse/routes (Laos, several durations: proposals, whole tours, tour sets compared by catalog
source_id) and /browse/tour-route (every live Laos catalog tour: status and match). Legacy tour keys are a
published tour_id for some tours and a source_id for others; they are mapped to the catalog source_id
(raw_tours.source_group_id) before comparing.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import zipfile
from contextlib import asynccontextmanager

MODULES = [
    "backend/__init__.py", "backend/config.py",
    "backend/browse/__init__.py", "backend/browse/handler.py",
    "backend/browse/countries.py", "backend/browse/destinations.py", "backend/browse/filters.py",
    "backend/browse/routes.py", "backend/browse/search.py", "backend/browse/tiles.py",
    "backend/shared/__init__.py", "backend/shared/places_source.py", "backend/shared/catalog_rls.py",
    "backend/shared/vector_topk.py", "backend/shared/schemas.py",
]
# Imported by handler.py / search.py but not exercised here (the /browse/catalog/* reads are not part of
# the place switch; search gets an injected embedder, so the Model Gateway is never called). Stubbed to
# keep the runner small enough to send through ECS exec without a file upload.
STUBS = {
    "backend/browse/catalog.py": "class QueryError(ValueError):\n    pass\n",
    "backend/shared/llm_gateway.py": "",
}
COUNTRY = "Laos"
DAYS = (3, 5, 7, 9, 10, 12, 14, 16, 21)
SECRET_ID = "aa-cis/dev/rds"
MASTER_TENANT = "00000000-0000-0000-0000-000000000001"  # AA master-content tenant (MASTER_CONTENT_TENANT_ID)
REGION = "us-west-1"


def build(repo: str, out: str) -> None:
    """A runnable zip: this file as __main__.py next to the TripPlanner backend package."""
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(__file__, "__main__.py")
        for m in MODULES:
            z.write(os.path.join(repo, m), m)
        for m, body in STUBS.items():
            z.writestr(m, body)
    print(f"wrote {out} ({os.path.getsize(out)} bytes)")


class Pool:
    """The asyncpg connection, shaped like the pool route() expects."""

    def __init__(self, conn):
        self.c = conn

    async def fetch(self, q, *a):
        return await self.c.fetch(q, *a)

    async def fetchrow(self, q, *a):
        return await self.c.fetchrow(q, *a)

    async def fetchval(self, q, *a):
        return await self.c.fetchval(q, *a)

    async def execute(self, q, *a):
        return await self.c.execute(q, *a)

    def transaction(self):
        return self.c.transaction()

    @asynccontextmanager
    async def acquire(self):
        yield self.c


async def main() -> None:
    import asyncpg
    try:
        import boto3
    except ImportError:  # local dry run (PARITY_DSN)
        boto3 = None
    from urllib.parse import unquote, urlparse

    from backend import config  # from the runner zip (python3 runner.zip puts it on sys.path)
    from backend.browse import handler, search as search_mod
    from backend.browse.filters import BrowseFilters

    # PARITY_DSN: a local dry run of this script against a throwaway database (role = PARITY_ROLE or none)
    dsn = os.environ.get("PARITY_DSN") or boto3.client(
        "secretsmanager", region_name=REGION).get_secret_value(SecretId=SECRET_ID)["SecretString"]
    role = os.environ.get("PARITY_ROLE", "tripplanner" if "PARITY_DSN" not in os.environ else "")
    u = urlparse(dsn)
    kw = dict(host=u.hostname, port=u.port or 5432, user=unquote(u.username or ""),
              password=unquote(u.password or ""), database=u.path.lstrip("/"),
              ssl=None if "PARITY_DSN" in os.environ else "require")
    admin = await asyncpg.connect(**kw)
    tp = await asyncpg.connect(**kw)
    await admin.execute("SET default_transaction_read_only = on")
    # raw_tours has RLS ENABLED + FORCED (policy tenant_isolation, migration 225 header): the runner
    # (aa_cis_admin, owner, no BYPASSRLS) sees no row without app.tenant_id, which would leave the
    # tour_id -> source_id map empty and every re-uploaded legacy key unmapped. Scope it to the AA master
    # tenant for this session (read-only connection; nothing else runs on it).
    await admin.execute("SELECT set_config('app.tenant_id', $1, false)", MASTER_TENANT)
    if role:
        await tp.execute(f"SET ROLE {role}")
    await tp.execute("SET default_transaction_read_only = on")
    await tp.execute("SET statement_timeout = '120s'")
    pool = Pool(tp)
    out: dict = {"country": COUNTRY, "role": await tp.fetchval("SELECT current_user")}

    # legacy tour key -> catalog source_id (raw_tours.source_group_id); a key that is no raw tour_id
    # is already a source_id
    src_of = {r[0]: r[1] for r in await admin.fetch(
        "SELECT tour_id::text, COALESCE(source_group_id, tour_id)::text FROM silver_aa_internal.raw_tours")}
    live = [dict(r) for r in await tp.fetch(
        "SELECT tour_id::text AS tour_id, source_id FROM catalog.v_tour WHERE country = $1 ORDER BY source_id",
        COUNTRY)]
    live_src = {r["source_id"] for r in live}

    def to_src(key):
        return src_of.get(key, key)

    legacy_keys = [r[0] for r in await tp.fetch(
        "SELECT DISTINCT source_tour_id FROM tripplanner.tour_leg WHERE $1 = ANY(countries)", COUNTRY)]
    cis_keys = [r[0] for r in await tp.fetch(
        "SELECT DISTINCT source_id FROM catalog.v_tour_leg WHERE $1 = ANY(countries)", COUNTRY)]
    out["coverage"] = {
        "raw_tours_mapped": len(src_of),   # 0 on Dev = the tenant GUC did not take (mapping is broken)
        "catalog_live_tours": len(live),
        "legacy_graph_tours": len(legacy_keys),
        # key == a live catalog source_id (includes tours whose source_id is their own first tour_id)
        "legacy_key_is_live_source_id": sum(1 for k in legacy_keys if k in live_src),
        # key is a (re-uploaded) tour_id whose source_id is live: found only after mapping
        "legacy_key_is_tour_id_mapped": sum(1 for k in legacy_keys if k not in live_src and to_src(k) in live_src),
        "legacy_key_not_live": sum(1 for k in legacy_keys if to_src(k) not in live_src),
        "legacy_graph_live": len({to_src(k) for k in legacy_keys} & live_src),
        "cis_graph_tours": len(cis_keys),
        "cis_graph_live": len(set(cis_keys) & live_src),
        "in_both": len({to_src(k) for k in legacy_keys} & set(cis_keys)),
    }

    qvecs = [[float(x) for x in r[0].strip("[]").split(",")] for r in await tp.fetch(
        "SELECT c.embedding::text FROM tripplanner.itinerary_components c "
        "JOIN shared.destinations d ON d.id = c.destination_id "
        "WHERE d.country = $1 AND c.embedding IS NOT NULL ORDER BY md5(c.id::text) LIMIT 8", COUNTRY)]

    async def call(path, query=None):
        t = time.perf_counter()
        resp = await handler.route("GET", path, query or {}, pool=pool)
        return resp["statusCode"], json.loads(resp["body"]), round((time.perf_counter() - t) * 1000), \
            resp["headers"].get("x-places-source")

    res: dict = {}
    for mode in ("legacy", "cis"):
        config.PLACES_SOURCE = mode
        r: dict = {}
        st, body, ms, served = await call("/browse/countries")
        r["served_by"] = served
        r["countries"] = {"status": st, "ms": ms, "n_countries": len(body.get("countries", [])),
                          "laos_components": next((c["component_count"] for c in body.get("countries", [])
                                                   if c["country"] == COUNTRY), 0)}
        st, body, ms, _ = await call("/browse/by-country", {"country": COUNTRY})
        dests = body.get("destinations", [])
        r["by_country"] = {"status": st, "ms": ms, "destinations": len(dests),
                           "components": sum(d["component_count"] for d in dests),
                           "located_by": _hist(d.get("located_by") for d in dests),
                           "precision": _hist(d.get("precision") for d in dests)}
        r["_dest_ids"] = {d["id"]: d["component_count"] for d in dests}
        tiles_ms, tile_dests, tile_comps, tile_err = 0, set(), 0, []
        for lat in range(13, 23):
            for lng in range(100, 108):
                st, body, ms, _ = await call(f"/browse/tiles/{lat}_{lng}")
                tiles_ms += ms
                if st != 200:
                    tile_err.append(f"{lat}_{lng}:{st}")
                for d in body.get("destinations", []):
                    tile_dests.add(d["id"])
                    tile_comps += d["component_count"]
        st, body, ms, _ = await call("/browse/tiles/10_100_10")
        r["tiles"] = {"cells": 80, "errors": tile_err, "ms_total": tiles_ms, "destinations": len(tile_dests),
                      "components": tile_comps, "coarse_10_100_10": {"status": st, "ms": ms,
                                                                      "destinations": len(body.get("destinations", []))}}
        searches = []
        for i, v in enumerate(qvecs):
            for flt in ({}, {"country": COUNTRY}):
                t = time.perf_counter()
                body = await search_mod.search("parity", BrowseFilters.from_query(flt), pool=pool,
                                               embedder=lambda q, v=v: v)
                searches.append({"q": i, "country": bool(flt), "n": len(body["destinations"]),
                                 "ms": round((time.perf_counter() - t) * 1000),
                                 "top10": [d["id"] for d in body["destinations"][:10]]})
        r["_search"] = searches
        routes = {}
        for days in DAYS:
            st, body, ms, _ = await call("/browse/routes", {"country": COUNTRY, "days": str(days)})
            props = body.get("proposals", [])
            routes[days] = {"status": st, "ms": ms, "proposals": len(props),
                            "whole": sum(1 for p in props if p["whole_tour"]),
                            "chains": sum(1 for p in props if p["transfers"]),
                            "pinned_days": sum(1 for p in props for d in p["days"] if d.get("component_id")),
                            "days_total": sum(len(p["days"]) for p in props),
                            "tour_sets": sorted("+".join(sorted(to_src(s.get("source_id") or s["tour_id"])
                                                                for s in p["segments"])) for p in props)}
        r["routes"] = routes
        tr = {}
        t0 = time.perf_counter()
        for t in live:
            st, body, ms, _ = await call("/browse/tour-route", {"tour_id": t["tour_id"], "source_id": t["source_id"]})
            p = body.get("proposal") or {}
            tr[t["source_id"]] = {"status": st, "match": p.get("match"), "days": len(p.get("days", [])),
                                  "pinned": sum(1 for d in p.get("days", []) if d.get("component_id")), "ms": ms}
        r["_tour_route"] = tr
        r["tour_route_ms_total"] = round((time.perf_counter() - t0) * 1000)
        res[mode] = r

    # destination detail on the union of both by-country lists
    ids = sorted(set(res["legacy"]["_dest_ids"]) | set(res["cis"]["_dest_ids"]))
    detail = {}
    for mode in ("legacy", "cis"):
        config.PLACES_SOURCE = mode
        for did in ids:
            st, body, ms, _ = await call(f"/browse/destinations/{did}")
            detail.setdefault(did, {})[mode] = (st, len(body.get("components", [])) if st == 200 else None, ms)
    eq = sum(1 for d in detail.values() if d["legacy"][1] == d["cis"][1])
    more = sum(1 for d in detail.values() if (d["cis"][1] or 0) > (d["legacy"][1] or 0))
    out["destination_detail"] = {
        "destinations": len(ids), "same_count": eq, "cis_more": more, "cis_fewer": len(ids) - eq - more,
        "legacy_only": sum(1 for i in ids if i not in res["cis"]["_dest_ids"]),
        "cis_only": sum(1 for i in ids if i not in res["legacy"]["_dest_ids"]),
        "ms_legacy": sum(d["legacy"][2] for d in detail.values()),
        "ms_cis": sum(d["cis"][2] for d in detail.values()),
        "largest_diffs": sorted(([i, d["legacy"][1], d["cis"][1]] for i, d in detail.items()),
                                key=lambda x: -abs((x[2] or 0) - (x[1] or 0)))[:8],
    }
    # search overlap per query
    pairs = []
    for a, b in zip(res["legacy"]["_search"], res["cis"]["_search"]):
        pairs.append({"q": a["q"], "country": a["country"], "n_legacy": a["n"], "n_cis": b["n"],
                      "ms_legacy": a["ms"], "ms_cis": b["ms"],
                      "top10_overlap": len(set(a["top10"]) & set(b["top10"])),
                      "top1_same": bool(a["top10"] and b["top10"] and a["top10"][0] == b["top10"][0])})
    out["search"] = pairs
    # tour-route per live tour
    trl, trc = res["legacy"]["_tour_route"], res["cis"]["_tour_route"]
    out["tour_route"] = {
        "tours": len(live),
        "legacy": _hist(f'{v["status"]}:{v["match"]}' for v in trl.values()),
        "cis": _hist(f'{v["status"]}:{v["match"]}' for v in trc.values()),
        "legacy_200_cis_404": sorted(s for s in trl if trl[s]["status"] == 200 and trc[s]["status"] != 200),
        "legacy_404_cis_200": len([s for s in trl if trl[s]["status"] != 200 and trc[s]["status"] == 200]),
        "same_days_when_both_200": sum(1 for s in trl if trl[s]["status"] == trc[s]["status"] == 200
                                       and trl[s]["days"] == trc[s]["days"]),
        "both_200": sum(1 for s in trl if trl[s]["status"] == trc[s]["status"] == 200),
    }
    for mode in ("legacy", "cis"):
        for k in [k for k in res[mode] if k.startswith("_")]:
            del res[mode][k]
    out["readers"] = res
    print(json.dumps(out, default=str, separators=(",", ":")))
    await admin.close()
    await tp.close()


def report(json_path: str) -> str:
    """Markdown tables from the runner's JSON line (pasted into aa712-6b-parity.md)."""
    d = json.loads(open(json_path).read().strip().splitlines()[-1])
    L, C = d["readers"]["legacy"], d["readers"]["cis"]
    o = [f"Role: `{d['role']}`, country: {d['country']}.", "", "### Coverage (tour graph)", "",
         "| | value |", "|---|---|"]
    o += [f"| {k} | {v} |" for k, v in d["coverage"].items()]
    o += ["", "### Readers", "", "| Reader | legacy | cis |", "|---|---|---|",
          f"| /browse/countries: {d['country']} components | {L['countries']['laos_components']} "
          f"({L['countries']['ms']} ms) | {C['countries']['laos_components']} ({C['countries']['ms']} ms) |",
          f"| /browse/by-country: destinations / components | {L['by_country']['destinations']} / "
          f"{L['by_country']['components']} ({L['by_country']['ms']} ms) | {C['by_country']['destinations']} / "
          f"{C['by_country']['components']} ({C['by_country']['ms']} ms) |",
          f"| /browse/tiles, 80 one-degree cells: destinations / components / total ms | "
          f"{L['tiles']['destinations']} / {L['tiles']['components']} / {L['tiles']['ms_total']} | "
          f"{C['tiles']['destinations']} / {C['tiles']['components']} / {C['tiles']['ms_total']} |",
          f"| /browse/tiles/10_100_10: destinations (ms) | {L['tiles']['coarse_10_100_10']['destinations']} "
          f"({L['tiles']['coarse_10_100_10']['ms']}) | {C['tiles']['coarse_10_100_10']['destinations']} "
          f"({C['tiles']['coarse_10_100_10']['ms']}) |",
          f"| /browse/tour-route over {d['tour_route']['tours']} live tours: status:match | "
          f"{d['tour_route']['legacy']} ({L['tour_route_ms_total']} ms) | {d['tour_route']['cis']} "
          f"({C['tour_route_ms_total']} ms) |",
          f"| cis located_by / precision (by-country) | | {C['by_country']['located_by']} / "
          f"{C['by_country']['precision']} |"]
    dd = d["destination_detail"]
    o += ["", "### Destination detail (union of both by-country lists)", "",
          f"{dd['destinations']} destinations: same component count {dd['same_count']}, cis more "
          f"{dd['cis_more']}, cis fewer {dd['cis_fewer']}; only in legacy {dd['legacy_only']}, only in cis "
          f"{dd['cis_only']}. Time legacy {dd['ms_legacy']} ms, cis {dd['ms_cis']} ms. Largest differences "
          f"(id, legacy, cis): {dd['largest_diffs']}.", "",
          "### Routes (/browse/routes, country = " + d["country"] + ")", "",
          "| days | legacy proposals (whole / chains) | cis proposals (whole / chains) | same tour sets | "
          "pinned days legacy / cis | ms legacy / cis |", "|---|---|---|---|---|---|"]
    for k in L["routes"]:
        a, b = L["routes"][k], C["routes"][k]
        o.append(f"| {k} | {a['proposals']} ({a['whole']} / {a['chains']}) | {b['proposals']} ({b['whole']} / "
                 f"{b['chains']}) | {a['tour_sets'] == b['tour_sets']} | {a['pinned_days']}/{a['days_total']} / "
                 f"{b['pinned_days']}/{b['days_total']} | {a['ms']} / {b['ms']} |")
    o += ["", "### Search (8 fixed query vectors = embeddings of Laos components; no Bedrock call)", "",
          "| q | country filter | results legacy / cis | top-10 overlap | same top-1 | ms legacy / cis |",
          "|---|---|---|---|---|---|"]
    o += [f"| {x['q']} | {x['country']} | {x['n_legacy']} / {x['n_cis']} | {x['top10_overlap']} | "
          f"{x['top1_same']} | {x['ms_legacy']} / {x['ms_cis']} |" for x in d["search"]]
    tr = d["tour_route"]
    o += ["", f"Tour-route: both 200 on {tr['both_200']} tours ({tr['same_days_when_both_200']} with the same day "
              f"count); legacy 200 but cis 404: {len(tr['legacy_200_cis_404'])} {tr['legacy_200_cis_404']}; "
              f"legacy 404 but cis 200: {tr['legacy_404_cis_200']}."]
    return "\n".join(o)


def _hist(values) -> dict:
    h: dict = {}
    for v in values:
        h[str(v)] = h.get(str(v), 0) + 1
    return h


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3 and sys.argv[1] == "report":
        print(report(sys.argv[2]))
    else:
        asyncio.run(main())
