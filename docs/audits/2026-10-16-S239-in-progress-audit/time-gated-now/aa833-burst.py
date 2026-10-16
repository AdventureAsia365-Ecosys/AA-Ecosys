"""AA-833 controlled burst (S239): N concurrent workers for D seconds against the public
TripPlanner browse BFF, using the query shapes from frontend/lib/api.ts and lib/catalog.ts.

Usage: python3 -I aa833-burst.py 15 60 aa833-burst-result.json
Stdlib only. Writes a JSON summary (status counts per resource, latency p50/p95/max, start/end UTC).
"""
import collections
import datetime
import json
import sys
import threading
import time
import urllib.error
import urllib.request

BASE = "https://tripplanner.lumiguides.it.com/api/browse?"
PATHS = [
    "resource=countries",
    "resource=catalog-tours&limit=12&sort=featured",
    "resource=catalog-tours&country=Vietnam&limit=24",
    "resource=catalog-tours&country=Nepal&limit=24",
    "resource=by-country&country=Vietnam",
    "resource=by-country&country=Japan",
    "resource=by-country&country=Nepal",
    "resource=tiles&tile_id=10_100_10",
    "resource=tiles&tile_id=20_100_10",
    "resource=tiles&tile_id=20_80_10",
    "resource=tiles&tile_id=30_130_10",
    "resource=tiles&tile_id=21_105",
    "resource=search&q=hanoi",
    "resource=routes&country=Vietnam&days=7",
]

CONC, DUR, OUT = int(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
lock = threading.Lock()
results = []
idx = [0]
start = time.time()


def worker():
    while time.time() - start < DUR:
        with lock:
            p = PATHS[idx[0] % len(PATHS)]
            idx[0] += 1
        t0 = time.time()
        try:
            req = urllib.request.Request(BASE + p, headers={"User-Agent": "aa833-burst-S239"})
            with urllib.request.urlopen(req, timeout=35) as r:
                r.read()
                code = r.status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception as e:  # network error / timeout
            code = "ERR:" + type(e).__name__
        with lock:
            results.append((p.split("&")[0], code, time.time() - t0))


started = datetime.datetime.now(datetime.timezone.utc).isoformat()
threads = [threading.Thread(target=worker) for _ in range(CONC)]
for t in threads:
    t.start()
for t in threads:
    t.join()
ended = datetime.datetime.now(datetime.timezone.utc).isoformat()

codes = collections.Counter(str(c) for _, c, _ in results)
by_res = collections.defaultdict(collections.Counter)
for r, c, _ in results:
    by_res[r][str(c)] += 1
lat = sorted(x for _, _, x in results) or [0.0]
summary = {
    "started_utc": started,
    "ended_utc": ended,
    "concurrency": CONC,
    "duration_s": DUR,
    "requests": len(results),
    "rps": round(len(results) / DUR, 1),
    "status_counts": dict(codes),
    "count_4xx": sum(v for k, v in codes.items() if k.startswith("4")),
    "count_429": codes.get("429", 0),
    "count_5xx": sum(v for k, v in codes.items() if k.startswith("5")),
    "count_err": sum(v for k, v in codes.items() if k.startswith("ERR")),
    "by_resource": {k: dict(v) for k, v in by_res.items()},
    "latency_s": {
        "p50": round(lat[len(lat) // 2], 3),
        "p95": round(lat[int(len(lat) * 0.95)], 3),
        "max": round(lat[-1], 3),
    },
}
with open(OUT, "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
