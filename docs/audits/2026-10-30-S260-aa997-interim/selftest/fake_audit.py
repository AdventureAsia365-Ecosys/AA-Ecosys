"""Local self-test of audit_relocated.py / recheck_14.py with a fake asyncpg connection (no DB, no AWS).
Usage: apps/AA-CIS-App/.venv/bin/python .tmp-session/S260/aa997/selftest/fake_audit.py audit|r14
Exercises the Python paths (classification, routes, flags, sample, labelled re-score, gate line) on canned rows;
the SQL text itself is only checked by reading it against docs/architecture/db-schema-reference.md."""
import asyncio  # noqa: F401
import json
import os
import sys
from datetime import datetime, timezone

ROOT = "/home/nghiep/projects/AA-Ecosys"
sys.path.insert(0, f"{ROOT}/apps/AA-CIS-App")
import asyncpg  # noqa: E402

T0 = datetime(2026, 10, 30, 0, 12, tzinfo=timezone.utc)
CALLS = []


def stamp(o, **kw):
    return {"v": "aa997.2", "outcome": o, "at": "2026-10-30T01:00:00.000000+00:00", "accept_rule": "aa997.3", **kw}


def dest(i, name, country, lat, lng, o, meta=None, **kw):
    m = dict(meta or {})
    m["relocate"] = o
    base = {"id": f"0000000{i}-0000-0000-0000-000000000000", "name": name, "country": country, "country_iso2": None,
            "lat": lat, "lng": lng, "located_by": "geoapify" if o["outcome"] == "confirmed" else "llm",
            "geo_status": "ok", "geo_precision": "point", "review_reason": None, "geocoder_meta": json.dumps(m),
            "dup": None, "s_lat": None, "s_lng": None, "s_lb": None, "pt_names": 1}
    base.update(kw)
    return base


ROWS = [
    dest(1, "Lijiang", "China", 26.8721, 100.2299, stamp("confirmed", moved_km=48.2, prev=[26.5, 100.0, "llm"]),
         {"name": "Lijiang", "result_type": "city", "strategy": "v2", "reference": "route"}, country_iso2="CN"),
    dest(2, "Black Dragon Pool", "China", 26.8836, 100.2335, stamp("confirmed", moved_km=0.3,
         prev=[26.8810, 100.2330, "llm"]), {"name": "Black Dragon Pool", "result_type": "amenity", "strategy": "v2"}),
    dest(3, "Hanoi airport", "Vietnam", 21.2187, 105.8042, stamp("off_route", route_km=900.0, geocoder="no_match"),
         review_reason="off_route"),
    dest(4, "Tiger Leaping Gorge", "China", 27.1890, 100.1110, stamp("llm_point", route_km=20.0, geocoder="no_match"),
         review_reason="llm_point"),
    dest(5, "free time", "China", 26.87, 100.23, {"v": "aa997.2", "outcome": "non_place", "cause": "generic",
                                                   "at": "2026-10-30T01:00:00+00:00"}),
    dest(6, "Kirov Square", "Russian Federation", 52.2891, 104.2798,
         stamp("confirmed", moved_km=2.1, prev=[52.28, 104.29, "llm"]),
         {"name": "Irkutsk", "result_type": "city", "strategy": "v2"}, pt_names=4),
    dest(7, "Old Town Lijiang", "China", 26.87, 100.23, stamp("confirmed", moved_km=3.0, prev=[26.85, 100.2, "llm"]),
         {"name": "Old Town", "result_type": "suburb"}, dup="00000009-0000-0000-0000-000000000000",
         s_lat=26.8700, s_lng=100.2350, s_lb="geoapify"),
]
TOWN = "0000000a-0000-0000-0000-000000000000"


class Tr:
    async def start(self):
        pass

    async def rollback(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class C:
    def transaction(self, **kw):
        return Tr()

    async def fetchval(self, sql, *a):
        CALLS.append(sql[:40])
        if "now()" in sql:
            return T0
        return 1005

    async def execute(self, sql, *a):
        CALLS.append(sql[:40])

    async def fetch(self, sql, *a):
        CALLS.append(" ".join(sql.split())[:60])
        if "kind = 'place_relocate' AND created_at" in sql:
            return [{"id": "11111111-x", "status": "succeeded", "created_at": T0, "started_at": T0, "finished_at": T0,
                     "run_after": T0, "payload": json.dumps({"mode": "apply", "accept_rule": "aa997.3", "strategy": "v2",
                                                             "rule_version": "aa997.2"}),
                     "result": json.dumps({"status": "stopped_credit_limit", "rows": 400, "done": 400, "confirmed": 120,
                                           "llm_point": 200, "off_route": 50, "non_place": 30,
                                           "geocoder_requests": 900, "remaining": 1005, "next_job": "2222"}),
                     "error": ""},
                    {"id": "33333333-x", "status": "queued", "created_at": T0, "started_at": None, "finished_at": None,
                     "run_after": T0, "payload": json.dumps({"mode": "apply", "accept_rule": "aa997.3"}),
                     "result": None, "error": None}]
        if "GROUP BY 1, 2, 3, 4, 5" in sql:
            return [{"v": "aa997.2", "ar": "aa997.3", "day": "2026-10-30", "o": "confirmed", "merged": False, "n": 3}]
        if "coalesce(located_by, '-')" in sql:
            return [{"l": "geoapify", "n": 5000}]
        if "split_part(review_reason" in sql:
            return [{"r": "-", "n": 6000}]
        if "WITH pts AS" in sql:
            assert a[0] == "aa997.2" and a[1] == "2026-10-30T00:12:00", a
            return ROWS
        if "FROM geo.place_name WHERE destination_id" in sql:
            return [{"d": r["id"], "name_norm": r["name"].lower(), "country_norm": r["country"].lower(),
                     "locality_norm": "", "tour_name": "Yunnan Discovery 8 Days"} for r in ROWS]
        if "anchor_day" in sql:
            out = []
            for r in ROWS:
                k = {"n": r["name"].lower(), "c": r["country"].lower(), "l": ""}
                if r["name"] == "Hanoi airport":     # last day: only the night before (unanchored)
                    out.append({**k, "source_id": "bbbbbbbb01", "day_index": 8, "anchor_day": 7, "aid": TOWN,
                                "lat": 20.25, "lng": 105.97})
                    continue
                out.append({**k, "source_id": "aaaaaaaa01", "day_index": 3, "anchor_day": 3, "aid": TOWN,
                            "lat": r["lat"] + 0.05, "lng": r["lng"]})
                out.append({**k, "source_id": "aaaaaaaa01", "day_index": 3, "anchor_day": 3, "aid": r["id"],
                            "lat": r["lat"], "lng": r["lng"]})     # the row itself: must be left out
            return out
        if "'place' AS kind" in sql and "UNION ALL" not in sql:
            return [{"n": r["name"].lower(), "c": r["country"].lower(), "l": "", "source_id": "aaaaaaaa01",
                     "day_index": 3, "kind": "place"} for r in ROWS]
        if "pn.last_error" in sql:
            import __main__
            V = __main__.VERIFIED
            return [{"name_norm": v["nn"], "country_norm": v["cn"], "locality_norm": v["loc"] or "",
                     "tour_name": v["tour"], "status": "resolved", "last_error": None, "lat": v["lat"],
                     "lng": v["lng"], "located_by": "geoapify", "geo_status": "ok", "review_reason": None,
                     "country_iso2": v["iso"], "did0": ROWS[0]["id"] if i == 0 else f"x{i}", "did": f"x{i}",
                     "reloc": json.dumps(stamp("confirmed")) if i < 3 else None} for i, v in enumerate(V)]
        if "pn.status = 'resolved' GROUP BY 1, 2" in sql:
            return [{"lb": "geoapify", "o": None, "n": 4000}, {"lb": "llm", "o": None, "n": 2000},
                    {"lb": "geoapify", "o": "confirmed", "n": 500}]
        # S260 L11 served-pins section
        if "FROM catalog.v_tour_stop" in sql:
            raise asyncpg.InsufficientPrivilegeError("permission denied for view v_tour_stop")
        if "FROM catalog.v_tour_component" in sql:
            return [{"d": f"x{i}"} for i in range(0, 500)]
        if "FROM catalog.v_tour_place" in sql:
            return [{"d": f"x{i}"} for i in range(450, 560)]
        if "AS linked" in sql:
            assert a[0] == ["llm_point", "off_route"] and a[1] == [] and a[2] is None, a
            return [{"id": f"x{i}", "name": f"n{i}", "country": "India" if i % 2 else "Nepal", "lat": 1.0, "lng": 2.0,
                     "review_reason": "llm_point", "located_by": "llm", "outcome": "llm_point" if i % 3 else "off_route",
                     "stamp_v": "aa997.2", "accept_rule": "aa997.3", "route_km": None, "linked": i % 5 != 0}
                    for i in range(10, 130)]
        if "LIKE 'non_place:%'" in sql:
            return [{"id": f"x{i}"} for i in range(130, 140)]
        if "AS did, d.located_by AS lb" in sql:
            return ([{"did": f"x{i}", "lb": "geoapify", "o": None} for i in range(0, 4000)]
                    + [{"did": f"x{i}", "lb": "llm", "o": "llm_point"} for i in range(10, 130)])
        # recheck_14
        if "graph_build" in sql:
            return [{"source_id": "229f2c60xx", "status": "ok", "max_day": 3, "stop_days": 2, "pinned_days": 2},
                    {"source_id": "0c608efdxx", "status": "ok", "max_day": 4, "stop_days": 1, "pinned_days": 1}]
        if "UNION ALL" in sql:
            return [{"source_id": "229f2c60xx", "day_index": 1, "kind": "place", "label": "Kumbum Monastery",
                     "did": "d1", "name": "Kumbum", "located_by": "llm", "geo_status": "ok", "review_reason": "llm_point",
                     "lat": 36.48, "lng": 101.57, "ro": "llm_point", "rv": "aa997.2", "rar": "aa997.3"},
                    {"source_id": "229f2c60xx", "day_index": 2, "kind": "night", "label": "Xining", "did": None,
                     "name": None, "located_by": None, "geo_status": None, "review_reason": None, "lat": None,
                     "lng": None, "ro": None, "rv": None, "rar": None},
                    {"source_id": "0c608efdxx", "day_index": 1, "kind": "night", "label": "Seoul", "did": "d2",
                     "name": "Seoul", "located_by": "geoapify", "geo_status": "ok", "review_reason": None,
                     "lat": 37.5, "lng": 127.0, "ro": None, "rv": None, "rar": None},
                    {"source_id": "0c608efdxx", "day_index": 2, "kind": "place", "label": "Bukchon", "did": "d3",
                     "name": "Bukchon", "located_by": "llm", "geo_status": "ok", "review_reason": None,
                     "lat": 37.58, "lng": 126.98, "ro": None, "rv": None, "rar": None}]
        if "published_tours" in sql:
            return [{"source_id": "229f2c60xx", "duration": "4 Days", "aa_itineraries": ""}]
        raise AssertionError("unexpected SQL: " + sql[:200])

    async def close(self):
        pass


async def connect(*a, **k):
    return C()


asyncpg.connect = connect
os.environ["DATABASE_URL"] = "x"
which = sys.argv[1] if len(sys.argv) > 1 else "audit"
path = {"audit": f"{ROOT}/.tmp-session/S260/aa997/audit_relocated.py",
        "r14": f"{ROOT}/.tmp-session/S260/aa997/recheck_14.py"}[which]
exec(compile(open(path).read(), path, "exec"))
