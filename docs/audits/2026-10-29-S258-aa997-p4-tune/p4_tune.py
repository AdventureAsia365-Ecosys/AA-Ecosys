#!/usr/bin/env python3
"""AA-997 S258 — offline ($0) tune of the strict acceptance rule on the S257 P4 sample.

P4 (S257 v2 re-audit): the S254 verified rows that are correct / wrong today and located by Geoapify, re-judged by
relocate.rejudge with live routes. aa997.2 refused 34 / 251 correct rows (13.5 %, gate <= 2 %) and 5 / 30 wrong rows.
This script re-runs that re-judge OFFLINE on a dump of the sample (build_p4_dump.py → aa997_p4_dump.py, read-only ECS
exec) with the CIS code of a checkout, proves it reproduces the deployed result, then sweeps the knobs of
geomatch.StrictParams (aa997.3, CIS branch feat/aa997-rule-v3-tune) and reports, per variant: correct rows refused
(gate <= 2 %) and wrong rows still refused (the catch rate to keep). No DB, no network, no paid call.

Usage (CIS venv python, it imports services.places from --cis):
  python3 p4_tune.py --decode <ecsx output file> --sample p4_sample.json          # ecsx P4DUMP lines → JSON
  <cis>/.venv/bin/python p4_tune.py --sample p4_sample.json --cis <CIS checkout> [--json-out summary.json]
  <cis>/.venv/bin/python p4_tune.py --selftest --cis <CIS checkout>                # synthetic sample, code paths only
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import itertools
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

GATE = 0.02
TRUSTED = ("geoapify", "manual", "mapbox")
SEP = "\x1f"
GRID = {
    "anchored_only": (False, True),
    "per_tour": (False, True),
    "ambiguous_km": (300.0, 500.0, 1000.0),
    "ambiguous_miss_div": (5, 3, 2),
    "rejudge_off_route_km": (150.0, 300.0, 500.0, 1e9),
    "rejudge_v1_checks": (True, False),
    "site_admin_named": (False, True),
}


# ── dump decoding ──────────────────────────────────────────────────────────────────────────────────────────────────

def decode(path: Path) -> dict:
    parts, sha = {}, None
    for line in path.read_text().splitlines():
        m = re.match(r"^P4DUMP (\d+)/(\d+) (\S+)$", line.strip())
        if m:
            parts[int(m.group(1))] = (int(m.group(2)), m.group(3))
        m = re.match(r"^P4DUMP_SHA256 ([0-9a-f]{64}) bytes=(\d+)$", line.strip())
        if m:
            sha = m.group(1)
    if not parts:
        raise SystemExit("no P4DUMP lines in " + str(path))
    n = next(iter(parts.values()))[0]
    missing = [i for i in range(1, n + 1) if i not in parts]
    if missing:
        raise SystemExit(f"missing P4DUMP chunks {missing[:10]} of {n}")
    blob = gzip.decompress(base64.b64decode("".join(parts[i][1] for i in range(1, n + 1))))
    if sha and hashlib.sha256(blob).hexdigest() != sha:
        raise SystemExit("P4DUMP sha256 mismatch")
    return json.loads(blob)


# ── route rebuild (store.route_anchors + relocate.routes_by_destination, from the raw anchors) ─────────────────────

def build_routes(sample: dict, guards) -> dict:
    """{destination id: routes} exactly as the deployed code builds them (trusted anchors of days d-1..d+1, the batch's
    rows excluded, consecutive duplicate stops dropped), each a guards.TourRoute with `tour` / `anchored`."""
    exclude = set(sample["batch_ids"])
    by_key = {}
    for key, rows in sample["anchors"].items():
        uses: dict = {}
        anchored = set()
        for src, day, aday, _transit, _has, aid, lat, lng, lb, suspect, merged, line, _last in rows:
            if lat is None or lb not in TRUSTED or suspect or merged or line or aid in exclude:
                continue
            pts = uses.setdefault((src, day), [])
            p = (float(lat), float(lng))
            if not pts or pts[-1] != p:
                pts.append(p)
            if aday == day:
                anchored.add((src, day))
        by_key[key] = tuple(guards.TourRoute(v, tour=u[0], anchored=u in anchored) for u, v in uses.items())
    return {r["id"]: tuple(rt for k in r["keys"] for rt in by_key.get(k, ())) for r in sample["rows"]}


# ── evaluation ─────────────────────────────────────────────────────────────────────────────────────────────────────

def evaluate(sample, routes, relocate, rule, params=None) -> dict:
    tally, refused_by, refused_rows = Counter(), Counter(), []
    for r in sample["rows"]:
        st = r["verified"]["state"]
        j = relocate.rejudge(r, routes[r["id"]], rule, params=params)
        o = relocate.rejudge_outcome(j)
        tally[(st, o)] += 1
        if o == "refused":
            refused_by[f"{st}:{j['reason']}"] += 1
            refused_rows.append((st, r["name"], r["country"], j["reason"]))
    nc = sum(n for (s, _), n in tally.items() if s == "C")
    ne = sum(n for (s, _), n in tally.items() if s == "E")
    rc, rw = tally[("C", "refused")], tally[("E", "refused")]
    return {"nc": nc, "rc": rc, "ne": ne, "rw": rw, "kept_unjudged_c": tally[("C", "kept_unjudged")],
            "pass": bool(nc) and rc <= GATE * nc, "refused_by": dict(refused_by.most_common()),
            "refused_rows": refused_rows}


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "n/a"


def line(label, m):
    return (f"{label:<44} correct refused {m['rc']:>3}/{m['nc']} ({pct(m['rc'], m['nc']):>6}) "
            f"wrong refused {m['rw']:>2}/{m['ne']} ({pct(m['rw'], m['ne']):>6}) "
            f"{'PASS' if m['pass'] else 'FAIL'} by {json.dumps(m['refused_by'])}")


def _same_routes(a, b, tol: float = 1e-5) -> bool:
    """Routes equal up to coordinate rounding (the dump carries 6 decimals, the DB 7: < 1 m)."""
    if len(a) != len(b):
        return False
    for ra, rb in zip(a, b):
        if len(ra) != len(rb):
            return False
        for pa, pb in zip(ra, rb):
            if any(abs(x - y) > tol for x, y in zip(pa, pb)):
                return False
    return True


def check_reproduction(sample, routes, relocate) -> tuple[int, int]:
    """(route mismatches, outcome mismatches) of the rebuild vs the deployed code's own result in the dump."""
    rmis = omis = 0
    for r in sample["rows"]:
        dep = r["deployed"]
        mine = [[list(p) for p in rt] for rt in routes[r["id"]]]
        if not _same_routes(mine, dep["routes"]):
            rmis += 1
            if rmis <= 5:
                print(f"REPRO route mismatch {r['name']}|{r['country']} mine={len(mine)} deployed={len(dep['routes'])}")
        j = relocate.rejudge(r, routes[r["id"]], "aa997.2")
        o = relocate.rejudge_outcome(j)
        if (o, j["reason"]) != (dep["outcome"], dep["reason"]):
            omis += 1
            if omis <= 5:
                print(f"REPRO outcome mismatch {r['name']}|{r['country']} mine={o}/{j['reason']} "
                      f"deployed={dep['outcome']}/{dep['reason']}")
    return rmis, omis


def diagnose(sample, routes, guards, relocate, gm):
    """Why aa997.2 refuses each correct row: route evidence (anchored / all), nearest route km."""
    print("DIAG correct rows refused by aa997.2 (name|country|reason|routes anchored/all|km all/anchored)")
    for r in sample["rows"]:
        if r["verified"]["state"] != "C":
            continue
        j = relocate.rejudge(r, routes[r["id"]], "aa997.2")
        if j["ok"]:
            continue
        rts = routes[r["id"]]
        anch = [rt for rt in rts if getattr(rt, "anchored", True)]
        k_all = guards.route_km(r["lat"], r["lng"], rts)
        k_anc = guards.route_km(r["lat"], r["lng"], anch)
        meta = r["geocoder_meta"]
        print(f"DIAG {r['name']}|{r['country']}|{j['reason']}|{len(anch)}/{len(rts)}|"
              f"{'-' if k_all is None else round(k_all)}/{'-' if k_anc is None else round(k_anc)}|"
              f"cand={meta.get('name')}|{meta.get('result_type')}|{meta.get('match_type')}|"
              f"judged={meta.get('judged') or meta.get('query')}")


def sweep(sample, routes, relocate, gm) -> list:
    base = gm.StrictParams()
    out = []
    keys = list(GRID)
    for combo in itertools.product(*(GRID[k] for k in keys)):
        kw = dict(zip(keys, combo))
        p = gm.StrictParams(**kw)
        m = evaluate(sample, routes, relocate, "aa997.2", params=p)
        changed = sorted(k for k in keys if getattr(p, k) != getattr(base, k))
        out.append((kw, changed, m))
    return out


def run(sample: dict, cis: Path, json_out: Path | None) -> int:
    sys.path.insert(0, str(cis))
    os.environ.setdefault("ENVIRONMENT", "test")
    from services.places import geomatch as gm  # noqa: E402
    from services.places import guards, relocate  # noqa: E402
    if not hasattr(gm, "StrictParams"):
        raise SystemExit("the CIS checkout has no geomatch.StrictParams (needs branch feat/aa997-rule-v3-tune)")
    routes = build_routes(sample, guards)
    rows = sample["rows"]
    print(f"SAMPLE rows={len(rows)} correct={sum(r['verified']['state'] == 'C' for r in rows)} "
          f"wrong={sum(r['verified']['state'] == 'E' for r in rows)} keys={len(sample['anchors'])} "
          f"routes={sum(len(v) for v in routes.values())} anchored="
          f"{sum(getattr(rt, 'anchored', True) for v in routes.values() for rt in v)}")
    if all("deployed" in r for r in rows):
        rmis, omis = check_reproduction(sample, routes, relocate)
        print(f"REPRO route mismatches={rmis} outcome mismatches={omis} "
              f"({'OK' if not rmis and not omis else 'DIFFERS: fix the rebuild before trusting the sweep'})")
    diagnose(sample, routes, guards, relocate, gm)
    m2 = evaluate(sample, routes, relocate, "aa997.2")
    m3 = evaluate(sample, routes, relocate, "aa997.3")
    print(line("aa997.2 (deployed)", m2))
    print(line("aa997.3 (branch preset)", m3))
    lost = sorted({(n, c) for st, n, c, _ in m2["refused_rows"] if st == "E"}
                  - {(n, c) for st, n, c, _ in m3["refused_rows"] if st == "E"})
    print("aa997.3 correct still refused " + json.dumps(
        [f"{n}|{c}|{w}" for st, n, c, w in m3["refused_rows"] if st == "C"], ensure_ascii=False))
    print("aa997.3 wrong catches lost vs aa997.2 " + json.dumps([f"{n}|{c}" for n, c in lost], ensure_ascii=False))
    res = sweep(sample, routes, relocate, gm)
    passing = [x for x in res if x[2]["pass"]]
    passing.sort(key=lambda x: (-x[2]["rw"], x[2]["rc"], len(x[1])))
    print(f"SWEEP variants={len(res)} passing={len(passing)} (gate correct refused <= {GATE:.0%})")
    for kw, changed, m in passing[:15]:
        print(line("  " + (",".join(f"{k}={kw[k]}" for k in changed) or "aa997.2"), m))
    best = passing[0] if passing else None
    if best:
        print("BEST " + json.dumps({k: best[0][k] for k in best[1]}) + f" wrong refused {best[2]['rw']}/{best[2]['ne']}"
              f" correct refused {best[2]['rc']}/{best[2]['nc']}")
    print(f"P4 GATE aa997.3 {'PASS' if m3['pass'] else 'FAIL'} (correct refused {m3['rc']}/{m3['nc']} = "
          f"{pct(m3['rc'], m3['nc'])}, wrong refused {m3['rw']}/{m3['ne']} vs aa997.2 {m2['rw']}/{m2['ne']})")
    if json_out:
        strip = lambda m: {k: v for k, v in m.items() if k != "refused_rows"}  # noqa: E731
        json_out.write_text(json.dumps({
            "aa997.2": m2, "aa997.3": m3,
            "passing": [{"changed": {k: kw[k] for k in ch}, **strip(m)} for kw, ch, m in passing[:50]],
            "variants": len(res)}, indent=1, ensure_ascii=False, default=str))
    return 0 if m3["pass"] else 1


# ── self-test: a synthetic sample in the dump's shape (no live data) ───────────────────────────────────────────────

def synthetic() -> dict:
    """Four rows of the P4 refusal classes (coordinates approximate, candidates synthetic) in the dump's shape."""
    def anchor(src, day, aday, lat, lng, aid="a", lb="geoapify", last=10):
        return [src, day, aday, False, True, aid, lat, lng, lb, False, False, False, last]

    rows, anchors = [], {}

    def add(rid, name, country, lat, lng, meta, state, key, anc):
        k = SEP.join(key)
        rows.append({"id": rid, "name": name, "country": country, "lat": lat, "lng": lng, "located_by": "geoapify",
                     "geo_status": "ok", "geo_precision": "point", "review_reason": None, "name_norm": key[0],
                     "locality_norm": "", "geocoder_meta": meta, "keys": [k],
                     "verified": {"state": state, "v": "C" if state == "C" else "WP", "tag": "kept", "nn": key[0],
                                  "random": 1, "site": 0, "exp": []}})
        anchors[k] = anc

    add("hk", "Hong Kong", "Hong Kong", 22.32, 114.17, {"query": "Hong Kong", "name": "Hong Kong",
                                                      "result_type": "city"}, "C", ("hong kong", "hong kong", ""),
        [anchor("t1", 3, 2, 39.90, 116.40), anchor("t1", 3, 3, 22.32, 114.17, aid="hk"),
         anchor("t1", 3, 4, 31.23, 121.47), anchor("t2", 1, 2, 25.27, 110.29)])
    add("del", "Delhi Airport", "India", 28.556, 77.100, {"query": "Delhi Airport",
                                                          "name": "Indira Gandhi International Airport",
                                                          "result_type": "amenity"}, "C",
        ("delhi airport", "india", ""), [anchor("t3", 8, 7, 26.91, 75.79, last=8)])
    add("bell", "Bell Tower", "China", 34.261, 108.943, {"query": "Bell Tower", "name": "Bell Tower",
                                                         "result_type": "amenity"}, "E", ("bell tower", "china", ""),
        [anchor("t4", 2, 2, 34.26, 108.94), anchor("t4", 2, 3, 37.20, 112.18),
         anchor("t5", 4, 4, 39.90, 116.40), anchor("t5", 4, 5, 40.43, 116.57)])
    add("anna", "Mt Annapurna", "Nepal", 28.42, 83.74, {"query": "Mt Annapurna", "name": "Annapurna",
                                                        "result_type": "district"}, "E", ("mt annapurna", "nepal", ""),
        [])
    return {"rows": rows, "anchors": anchors, "batch_ids": [r["id"] for r in rows], "rule_version": "aa997.2"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--decode", type=Path, help="ecsx output with P4DUMP lines; writes --sample")
    ap.add_argument("--sample", type=Path, help="the decoded P4 sample JSON")
    ap.add_argument("--cis", type=Path, help="AA-CIS-App checkout with geomatch.StrictParams")
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.decode:
        if not a.sample:
            raise SystemExit("--decode needs --sample (the JSON to write)")
        a.sample.write_text(json.dumps(decode(a.decode), ensure_ascii=False, indent=0))
        print(f"wrote {a.sample}")
        return 0
    if not a.cis:
        raise SystemExit("--cis <AA-CIS-App checkout> is required")
    if a.selftest:
        return run(synthetic(), a.cis.resolve(), a.json_out)
    return run(json.loads(a.sample.read_text()), a.cis.resolve(), a.json_out)


if __name__ == "__main__":
    sys.exit(main())
