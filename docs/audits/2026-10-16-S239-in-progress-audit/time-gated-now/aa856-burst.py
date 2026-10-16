"""AA-856 search burst (S239): N concurrent workers for D seconds against the public TripPlanner
browse BFF, search only, with a DIFFERENT query text on every request.

Why not aa833-burst.py: that one repeats `q=hanoi`. With the AA-856 query-embedding cache each warm
Lambda container embeds `hanoi` once and serves every later search from its cache, so "0 HTTP 500"
holds whatever the global profile, the IAM grant, the quota or the fallback do. Here every request
is a cache miss (place word + request number), so above the Cohere quota (20 rpm until
L-7089DC7D rises) the miss / throttle / keyword-fallback paths really run. `--repeat-share` sends
that share of requests as the fixed query `hanoi` to see cache hits too.

Usage:  python3 -I aa856-burst.py 15 60 aa856-burst-result.json [--repeat-share 0.2]
Expect: status 200 only (no 500/503 except the AA-805 daily cap), a mix of
"ranking": "semantic" and "keyword" until the quota rises (semantic only after), and in Logs
Insights on the browse log group:
  filter evt = "search_embed" | stats count(*) by outcome, reason
with outcome=fallback reason=throttle / throttle_cooldown during the burst.

Each miss is one real Bedrock embed (about $0.0000004) on the quota shared with CIS f10_embed /
a3_place_embed: run it when shared.job has nothing queued/running.
Stdlib only. Writes a JSON summary (status and ranking counts, latency p50/p95/max, start/end UTC).
"""
import argparse
import collections
import datetime
import json
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://tripplanner.lumiguides.it.com/api/browse?"
WORDS = [
    "hanoi", "hoi an", "sapa", "ha long bay", "mekong delta", "hue", "da lat", "phu quoc",
    "kyoto", "osaka", "hakone", "nara", "hokkaido", "okinawa", "takayama", "nikko",
    "kathmandu", "pokhara", "annapurna", "everest base camp", "chitwan", "lumbini",
    "bangkok", "chiang mai", "phuket", "krabi", "luang prabang", "siem reap", "angkor wat",
    "bali", "ubud", "komodo", "yogyakarta", "bhutan", "paro", "thimphu", "ladakh", "kerala",
    "street food", "rice terraces", "temple", "trekking", "kayaking", "homestay", "cooking class",
    "cycling", "beach", "night market", "hot spring", "monastery", "tea plantation", "cave",
]

ap = argparse.ArgumentParser()
ap.add_argument("concurrency", type=int)
ap.add_argument("duration_s", type=float)
ap.add_argument("out")
ap.add_argument("--repeat-share", type=float, default=0.0,
                help="share of requests sent as the fixed query 'hanoi' (cache hits)")
args = ap.parse_args()

lock = threading.Lock()
results = []
counter = [0]
start = time.time()
run_id = format(int(start), "x")


def next_query():
    with lock:
        counter[0] += 1
        n = counter[0]
    if random.random() < args.repeat_share:
        return n, "hanoi", "repeat"
    return n, f"{random.choice(WORDS)} {run_id} {n}", "unique"


def worker():
    while time.time() - start < args.duration_s:
        n, q, kind = next_query()
        url = BASE + urllib.parse.urlencode({"resource": "search", "q": q, "_cb": f"{run_id}-{n}"})
        t0 = time.time()
        ranking = None
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "aa856-burst-S239"})
            with urllib.request.urlopen(req, timeout=35) as r:
                body = r.read()
                code = r.status
            try:
                ranking = json.loads(body).get("ranking")
            except ValueError:
                ranking = "unparsed"
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception as e:  # network error / timeout
            code = "ERR:" + type(e).__name__
        with lock:
            results.append((kind, code, ranking, time.time() - t0))


started = datetime.datetime.now(datetime.timezone.utc).isoformat()
threads = [threading.Thread(target=worker) for _ in range(args.concurrency)]
for t in threads:
    t.start()
for t in threads:
    t.join()
ended = datetime.datetime.now(datetime.timezone.utc).isoformat()

codes = collections.Counter(str(c) for _, c, _, _ in results)
rankings = collections.defaultdict(collections.Counter)
for kind, c, rk, _ in results:
    if str(c) == "200":
        rankings[kind][str(rk)] += 1
lat = sorted(x for *_, x in results) or [0.0]
summary = {
    "started_utc": started,
    "ended_utc": ended,
    "run_id": run_id,
    "concurrency": args.concurrency,
    "duration_s": args.duration_s,
    "repeat_share": args.repeat_share,
    "requests": len(results),
    "rpm": round(len(results) * 60 / args.duration_s, 1),
    "status_counts": dict(codes),
    "count_5xx": sum(v for k, v in codes.items() if k.startswith("5")),
    "count_err": sum(v for k, v in codes.items() if k.startswith("ERR")),
    "ranking_on_200_by_query_kind": {k: dict(v) for k, v in rankings.items()},
    "latency_s": {
        "p50": round(lat[len(lat) // 2], 3),
        "p95": round(lat[int(len(lat) * 0.95)], 3),
        "max": round(lat[-1], 3),
    },
}
with open(args.out, "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
