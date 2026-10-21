#!/usr/bin/env python3
"""AA-847 — HTTP parity, AA-674 pin sets and the post-flip burst, through the TripPlanner BFF (no secret needed).

The orchestrator runs it from a laptop against the Dev site (the BFF adds the edge key itself), once with
PLACES_SOURCE=legacy before the flip and once with cis after it, then compares the two runs:

    python3 http_parity.py run --base https://<tripplanner site> --label legacy --out legacy.json
    python3 http_parity.py run --base https://<tripplanner site> --label cis --out cis.json
    python3 http_parity.py compare legacy.json cis.json
    python3 http_parity.py burst --base https://<tripplanner site> --seconds 120 --concurrency 6 --out burst.json

Rules (AA-847 plan, slice H):
  * every browse GET carries a unique cache-buster `_cb=<run>-<n>` so the Vercel CDN and browser caches are missed and
    the Lambda answers (lesson S239: a burst through the BFF otherwise hits the CDN);
  * search: at most SEARCHES fixed queries (Cohere Embed v4 on acc2 allows 20 requests/minute, shared with the CIS
    a3_place_embed of the paid run: never run both at the same time); the burst never calls search;
  * assembly: AA-674 pin sets (seeded) on fresh guest drafts: add components, then coverage, suggestions and one
    stop's activities. **Never** send-to-advisor / inquiry (they write tripplanner.outbox → Booking inbox data).
    Narration only with `--narrate N` (spends against the TripPlanner 5 USD/day cap; cache misses after the flip);
  * every draft this script creates is listed in the output (`drafts`: trip_id, session_id) for the cleanup
    (DRY RUN procedure, skill aa-cis-schema references/destructive-ops.md; Nghiệp approves a delete).

Output: one JSON file per run with, per call, the reader, status, ms, a count and the response's top-level keys;
`compare` prints per reader: status agreement, shape (keys) agreement, counts and the ms ratio, and the parity
verdict with the S237 aggregation (target = max(1.5 × legacy, 200 ms)). Standard library only.
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import random
import statistics
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

COUNTRIES = ("Laos", "Vietnam")
SEARCHES = ("waterfall swim", "night market food", "temple at sunrise", "cycling through villages",
            "boat trip on the river", "caves", "trekking hill tribes", "cooking class")
ROUTE_DAYS = range(3, 22)
TILE_CAP = 80
DETAIL_CAP = 60
TOUR_ROUTE_CAP = 30
PIN_SETS = 20
SEED = 674
TIMEOUT = 30


class Client:
    def __init__(self, base: str, label: str):
        self.base = base.rstrip("/")
        self.run_id = f"{label}-{uuid.uuid4().hex[:6]}"
        self.n = 0
        self.lock = threading.Lock()
        self.calls: list[dict] = []
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def _cb(self) -> str:
        with self.lock:
            self.n += 1
            return f"{self.run_id}-{self.n}"

    def request(self, reader: str, method: str, path: str, params: dict | None = None, body: dict | None = None,
                record: bool = True) -> tuple[int, object]:
        q = dict(params or {})
        if method == "GET" and path.startswith("/api/browse"):
            q["_cb"] = self._cb()
        url = f"{self.base}{path}" + (f"?{urllib.parse.urlencode(q)}" if q else "")
        headers = {"accept": "application/json", "origin": self.base, "referer": f"{self.base}/plan"}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["content-type"] = "application/json"
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        t0 = time.monotonic()
        try:
            with self.opener.open(req, timeout=TIMEOUT) as r:
                status, raw = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, raw = e.code, e.read()
        except Exception as e:  # noqa: BLE001 — a network error is a result too
            status, raw = 0, str(type(e).__name__).encode()
        ms = (time.monotonic() - t0) * 1000.0
        try:
            payload = json.loads(raw or b"null")
        except ValueError:
            payload = None
        if record:
            with self.lock:
                self.calls.append({"reader": reader, "status": status, "ms": round(ms, 1),
                                   "count": _count(payload), "keys": _keys(payload),
                                   "params": {k: v for k, v in q.items() if k != "_cb"}})
        return status, payload


def _count(p) -> int | None:
    if isinstance(p, dict):
        for k in ("destinations", "countries", "proposals", "components", "suggestions", "activities", "legs",
                  "itinerary"):
            if isinstance(p.get(k), list):
                return len(p[k])
        if isinstance(p.get("proposal"), dict):
            return len(p["proposal"].get("days") or [])
    return len(p) if isinstance(p, list) else None


def _keys(p) -> list[str]:
    return sorted(p) if isinstance(p, dict) else []


def browse(c: Client, args) -> dict:
    """Every browse reader for COUNTRIES; returns {country: [destination ids]} for the pin sets."""
    c.request("countries", "GET", "/api/browse", {"resource": "countries"})
    dests: dict[str, list[dict]] = {}
    for country in args.countries:
        _, body = c.request("by_country", "GET", "/api/browse", {"resource": "by-country", "country": country})
        pins = (body or {}).get("destinations") or [] if isinstance(body, dict) else []
        dests[country] = pins
        cells = sorted({(int(p["lat"] // 1), int(p["lng"] // 1)) for p in pins if "lat" in p})[:TILE_CAP]
        for lat, lng in cells:
            c.request("tiles", "GET", "/api/browse", {"resource": "tiles", "tile_id": f"{lat}_{lng}"})
        if pins:
            lat10 = int(statistics.mean(p["lat"] for p in pins) // 10 * 10)
            lng10 = int(statistics.mean(p["lng"] for p in pins) // 10 * 10)
            c.request("tiles", "GET", "/api/browse", {"resource": "tiles", "tile_id": f"{lat10}_{lng10}_10"})
        for p in pins[:DETAIL_CAP]:
            c.request("detail", "GET", "/api/browse", {"resource": "destination", "id": p["id"]})
        for days in ROUTE_DAYS:
            c.request("routes", "GET", "/api/browse", {"resource": "routes", "country": country, "days": days})
        _, tours = c.request("catalog_tours", "GET", "/api/browse",
                             {"resource": "catalog-tours", "country": country, "limit": TOUR_ROUTE_CAP})
        for t in ((tours or {}).get("tours") or [])[:TOUR_ROUTE_CAP] if isinstance(tours, dict) else []:
            params = {"resource": "tour-route", "tour_id": t.get("tour_id")}
            if t.get("source_id"):
                params["source_id"] = t["source_id"]
            c.request("tour_route", "GET", "/api/browse", params)
    for q in SEARCHES[:args.searches]:
        c.request("search", "GET", "/api/browse", {"resource": "search", "q": q})
        time.sleep(3.5)          # stay under the 20 requests/minute Cohere quota
    return dests


def pin_sets(c: Client, dests: dict, args) -> list[dict]:
    """AA-674: seeded sets of 1–4 components on fresh guest drafts; coverage, suggestions, activities."""
    rng = random.Random(SEED)
    out, drafts = [], []
    pool: list[tuple[str, str]] = []           # (destination id, component id) from destination details
    for country in args.countries:
        for p in dests.get(country, [])[:DETAIL_CAP]:
            _, d = c.request("detail", "GET", "/api/browse", {"resource": "destination", "id": p["id"]},
                             record=False)
            for comp in ((d or {}).get("components") or [])[:3] if isinstance(d, dict) else []:
                pool.append((p["id"], comp["id"]))
    if not pool:
        return out
    for i in range(args.pinsets):
        picked = rng.sample(pool, min(len(pool), rng.randint(1, 4)))
        trip, session = str(uuid.uuid4()), str(uuid.uuid4())
        drafts.append({"trip_id": trip, "session_id": session})
        statuses = []
        for _, cid in picked:
            s, _ = c.request("assembly_add", "POST", "/api/trip",
                             body={"op": "add", "trip_id": trip, "session_id": session, "component_id": cid})
            statuses.append(s)
        s_cov, cov = c.request("assembly_coverage", "GET", "/api/trip", {"trip_id": trip, "resource": "coverage"})
        c.request("assembly_suggestions", "GET", "/api/trip", {"trip_id": trip, "resource": "suggestions"})
        c.request("assembly_activities", "GET", "/api/trip",
                  {"trip_id": trip, "resource": "activities", "destination_id": picked[0][0]})
        if i < args.narrate:
            c.request("assembly_narrate", "POST", "/api/trip",
                      body={"op": "narrate", "trip_id": trip, "session_id": session, "mode": "compose"})
        verdict = None
        if isinstance(cov, dict) and s_cov == 200:
            legs = [p for leg in cov.get("legs") or [] for p in leg.get("pins") or []]
            ok_chain = len(legs) == len(set(legs)) == len(picked)
            gaps = cov.get("gaps") or []
            ok_gaps = cov.get("coverable") == (not gaps) and all(g.get("reason") for g in gaps)
            verdict = {"coverable": cov.get("coverable"), "chain_ok": ok_chain, "gaps_ok": ok_gaps}
        out.append({"set": i, "pins": [cid for _, cid in picked], "add_status": statuses, "coverage": verdict})
    c.drafts = drafts
    return out


def cmd_run(args) -> int:
    c = Client(args.base, args.label)
    c.drafts = []
    t0 = time.monotonic()
    dests = browse(c, args)
    sets = pin_sets(c, dests, args) if args.pinsets else []
    out = {"label": args.label, "base": args.base, "run_id": c.run_id, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "elapsed_s": round(time.monotonic() - t0, 1), "calls": c.calls, "pin_sets": sets, "drafts": c.drafts}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    bad = [x for x in c.calls if x["status"] != 200]
    print(f"{len(c.calls)} calls, {len(bad)} not 200, {len(sets)} pin sets, {len(c.drafts)} drafts -> {args.out}")
    for s in sets:
        if s["coverage"] and not (s["coverage"]["chain_ok"] and s["coverage"]["gaps_ok"]):
            print(f"AA-674 property broken: set {s['set']}: {s['coverage']}")
    return 1 if bad else 0


def _series(run: dict) -> dict:
    by: dict[str, list[dict]] = {}
    for x in run["calls"]:
        by.setdefault(x["reader"], []).append(x)
    return by


def cmd_compare(args) -> int:
    a, b = (json.load(open(p)) for p in (args.legacy, args.cis))
    sa, sb = _series(a), _series(b)
    fails = 0
    print(f"{'reader':24} {'n':>4} {'200':>9} {'keys':>5} {'legacy':>10} {'cis':>10} {'target':>10}  verdict")
    for reader in sorted(set(sa) | set(sb)):
        la, lb = sa.get(reader, []), sb.get(reader, [])
        ok_a, ok_b = sum(x["status"] == 200 for x in la), sum(x["status"] == 200 for x in lb)
        shape_a = {tuple(x["keys"]) for x in la if x["status"] == 200}
        keys = shape_a == {tuple(x["keys"]) for x in lb if x["status"] == 200}
        agg = sum if reader in ("tiles", "detail") else (lambda v: statistics.mean(v) if v else 0.0)
        lv = agg([x["ms"] for x in la]) if la else 0.0
        cv = agg([x["ms"] for x in lb]) if lb else 0.0
        target = max(1.5 * lv, 200.0)
        ok = bool(lb) and ok_b == len(lb) and cv <= target
        fails += not ok
        print(f"{reader:24} {len(lb):>4} {ok_a:>4}/{ok_b:<4} {'=' if keys else '≠':>5} {lv:>10.1f} {cv:>10.1f} "
              f"{target:>10.1f}  {'PASS' if ok else 'FAIL'}")
    print(f"parity: {fails} reader(s) failing")
    return 1 if fails else 0


def cmd_burst(args) -> int:
    """Post-flip burst (Done-when 5 replacement): unique keys, no search, a few readers in rotation."""
    c = Client(args.base, "burst")
    _, body = c.request("by_country", "GET", "/api/browse", {"resource": "by-country", "country": args.countries[0]})
    pins = (body or {}).get("destinations") or [] if isinstance(body, dict) else []
    jobs = [("countries", {"resource": "countries"})]
    jobs += [("by_country", {"resource": "by-country", "country": k}) for k in args.countries]
    jobs += [("detail", {"resource": "destination", "id": p["id"]}) for p in pins[:20]]
    jobs += [("routes", {"resource": "routes", "country": args.countries[0], "days": d}) for d in (5, 8, 12)]
    stop = time.monotonic() + args.seconds

    pace = args.concurrency / float(args.rps)      # seconds between two calls of one worker (overall <= rps)

    def worker(seed):
        rng = random.Random(seed)
        while time.monotonic() < stop:
            t = time.monotonic()
            reader, params = rng.choice(jobs)
            c.request(reader, "GET", "/api/browse", params)
            time.sleep(max(0.0, pace - (time.monotonic() - t)))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(args.concurrency)]
    t0 = time.strftime("%Y-%m-%dT%H:%M:%S")
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    codes: dict[int, int] = {}
    for x in c.calls:
        codes[x["status"]] = codes.get(x["status"], 0) + 1
    out = {"started": t0, "seconds": args.seconds, "concurrency": args.concurrency, "rps": args.rps, "codes": codes,
           "p95_ms": round(statistics.quantiles([x["ms"] for x in c.calls], n=20)[-1], 1) if len(c.calls) > 20
           else None, "calls": len(c.calls)}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out))
    print("check: aa-tripplanner-dev-browse-throttles and Lambda Errors = 0 over this window (CloudWatch)")
    return 0 if set(codes) <= {200} else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--base", required=True)
    r.add_argument("--label", required=True, choices=("legacy", "cis"))
    r.add_argument("--out", required=True)
    r.add_argument("--countries", type=lambda s: s.split(","), default=list(COUNTRIES))
    r.add_argument("--searches", type=int, default=len(SEARCHES))
    r.add_argument("--pinsets", type=int, default=PIN_SETS)
    r.add_argument("--narrate", type=int, default=0, help="narrate the first N pin sets (model spend)")
    c = sub.add_parser("compare")
    c.add_argument("legacy")
    c.add_argument("cis")
    b = sub.add_parser("burst")
    b.add_argument("--base", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--seconds", type=int, default=120)
    b.add_argument("--concurrency", type=int, default=6)
    b.add_argument("--rps", type=float, default=20.0, help="overall request rate cap")
    b.add_argument("--countries", type=lambda s: s.split(","), default=list(COUNTRIES))
    a = ap.parse_args(argv)
    if a.cmd == "run" and a.searches > len(SEARCHES):
        ap.error(f"at most {len(SEARCHES)} searches (Cohere quota)")
    return {"run": cmd_run, "compare": cmd_compare, "burst": cmd_burst}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
