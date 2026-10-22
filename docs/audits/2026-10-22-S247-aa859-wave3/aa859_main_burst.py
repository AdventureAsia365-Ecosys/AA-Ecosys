"""AA-859 wave 4 (S247) — scripted burst against the CIS api MAIN pool (cis_app), to size the shrink 10 -> 5.

Run INSIDE the CIS api container (S3-mediated ECS exec, cwd /app; python3 + asyncpg + boto3 + httpx are in the image):

    python3 /tmp/s.py baseline        # before the shrink (main pool max 10, signal build deployed)
    python3 /tmp/s.py after           # after the shrink is deployed (max 5)

What it does (READ-ONLY on the DB; nothing is written, granted or altered):
  1. One READ ONLY transaction with the container's DATABASE_URL (cis_app, ssl="require"): up to 200 ids of
     shared.place_photo rows that are not rejected and have s3_key_small, plus max_connections. Rolled back.
  2. Load: GET http://127.0.0.1:8000/content/photos/{id}?size=small (public route, no auth, not rate limited;
     one indexed fetchrow on app.state.pool per request; answers 302 to the CDN, redirects NOT followed, so no
     S3/CDN traffic). Warm-up, then concurrency steps 10 -> 50 -> 100, each BURST_STEP_S seconds, BURST_PAUSE_S
     apart. Per step: requests, rps, latency p50/p95/p99/max (ms), status histogram, errors (exceptions + 5xx).
  3. Sampler on its OWN connection (application_name aa859-burst, not counted): every 0.2 s, sessions of
     application_name 'cis-api' in pg_stat_activity (total = pool size, non-idle = in use). cis_app sees its own
     role's sessions. Coarse (0.2 s); the exact per-interval peak is peak_in_use on the aa859_main_pool_gauge
     log line (Logs Insights query printed in the JSON under logs_insights).

Writes ONE JSON to s3://aa-cis-bronze-005097885195/scripts/out/s247/aa859_main_burst_<label>.json and prints one
line: `OK <label> <step summaries>` or `ERR <reason>`. Never prints a DSN or a password.

Outside a container (no ECS metadata env) it writes ./aa859_main_burst_<label>.json instead of S3; set
BURST_BASE=https://api-cis.lumiguides.it.com to go through API Gateway (then the load spreads over every api task,
and without DATABASE_URL the ids are random UUIDs: 404 after the same single main-pool read).

Env knobs: BURST_BASE (default http://127.0.0.1:8000), BURST_STEPS (default "10,50,100"), BURST_STEP_S (45),
BURST_PAUSE_S (15), BURST_WARMUP_S (10).

Caveat: in the container the load generator shares the task's vCPU with uvicorn, so absolute latency is pessimistic;
compare baseline vs after under the same script, not against an SLO.
"""
import asyncio
import json
import os
import random
import sys
import time
import uuid
from datetime import datetime, timezone

BUCKET = "aa-cis-bronze-005097885195"
S3_KEY = "scripts/out/s247/aa859_main_burst_{label}.json"
LOG_GROUP = "/ecs/aa-cis-dev"

BASE = os.environ.get("BURST_BASE", "http://127.0.0.1:8000").rstrip("/")
STEPS = [int(x) for x in os.environ.get("BURST_STEPS", "10,50,100").split(",") if x.strip()]
STEP_S = float(os.environ.get("BURST_STEP_S", "45"))
PAUSE_S = float(os.environ.get("BURST_PAUSE_S", "15"))
WARMUP_S = float(os.environ.get("BURST_WARMUP_S", "10"))
IN_ECS = bool(os.environ.get("ECS_CONTAINER_METADATA_URI_V4") or os.environ.get("ECS_CONTAINER_METADATA_URI"))

SAMPLE_SQL = """SELECT count(*)::int AS total,
                       count(*) FILTER (WHERE state IS DISTINCT FROM 'idle')::int AS in_use
                  FROM pg_stat_activity WHERE application_name = 'cis-api'"""


def _now():
    return datetime.now(timezone.utc)


def _pct(sorted_vals, p):
    if not sorted_vals:
        return None
    k = min(len(sorted_vals) - 1, max(0, int(round(p / 100.0 * len(sorted_vals) + 0.5)) - 1))
    return round(sorted_vals[k], 1)


async def _read_ids_and_settings():
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        return [str(uuid.uuid4()) for _ in range(50)], {"ids": "random_uuid (no DATABASE_URL): 404 path"}
    import asyncpg
    conn = await asyncpg.connect(dsn, ssl="require", server_settings={"application_name": "aa859-burst"})
    try:
        tr = conn.transaction(readonly=True)
        await tr.start()
        try:
            rows = await conn.fetch(
                """SELECT id::text FROM shared.place_photo
                    WHERE status <> 'rejected' AND s3_key_small IS NOT NULL
                    ORDER BY id LIMIT 200""")
            max_conn = await conn.fetchval("SHOW max_connections")
            pre = dict(await conn.fetchrow(SAMPLE_SQL))
        finally:
            await tr.rollback()
    finally:
        await conn.close()
    ids = [r["id"] for r in rows] or [str(uuid.uuid4()) for _ in range(50)]
    return ids, {"ids": f"{len(rows)} real place_photo ids" if rows else "random_uuid (no rows)",
                 "max_connections": int(max_conn), "cis_api_sessions_before": pre}


class Sampler:
    """pg_stat_activity sampler for application_name cis-api on a dedicated connection."""

    def __init__(self):
        self.conn = None
        self.samples = []  # (t_monotonic, total, in_use)
        self._task = None
        self._stop = asyncio.Event()

    async def start(self):
        dsn = os.environ.get("DATABASE_URL")
        if not dsn:
            return
        import asyncpg
        self.conn = await asyncpg.connect(dsn, ssl="require", server_settings={"application_name": "aa859-burst"})
        self._task = asyncio.create_task(self._run())

    async def _run(self):
        while not self._stop.is_set():
            try:
                r = await self.conn.fetchrow(SAMPLE_SQL)
                self.samples.append((time.monotonic(), r["total"], r["in_use"]))
            except Exception:
                pass
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=0.2)
            except asyncio.TimeoutError:
                pass

    def window(self, t0, t1):
        s = [x for x in self.samples if t0 <= x[0] <= t1]
        if not s:
            return None
        return {"samples": len(s), "max_sessions": max(x[1] for x in s), "max_in_use": max(x[2] for x in s),
                "mean_in_use": round(sum(x[2] for x in s) / len(s), 2)}

    async def stop(self):
        self._stop.set()
        if self._task:
            await asyncio.gather(self._task, return_exceptions=True)
        if self.conn:
            await self.conn.close()


async def _step(client, ids, concurrency, duration_s):
    lat, statuses, errors = [], {}, {}
    deadline = time.monotonic() + duration_s

    async def worker(i):
        n = i
        while time.monotonic() < deadline:
            pid = ids[n % len(ids)]
            n += concurrency
            t = time.perf_counter()
            try:
                r = await client.get(f"{BASE}/content/photos/{pid}", params={"size": "small"})
                ms = (time.perf_counter() - t) * 1000.0
                lat.append(ms)
                statuses[str(r.status_code)] = statuses.get(str(r.status_code), 0) + 1
                if r.status_code >= 500:
                    errors["http_5xx"] = errors.get("http_5xx", 0) + 1
            except Exception as e:  # timeouts, resets
                key = type(e).__name__
                errors[key] = errors.get(key, 0) + 1

    t0 = time.monotonic()
    started = _now()
    await asyncio.gather(*(worker(i) for i in range(concurrency)))
    t1 = time.monotonic()
    lat.sort()
    total = len(lat) + sum(v for k, v in errors.items() if k != "http_5xx")
    return t0, t1, {
        "concurrency": concurrency, "start_utc": started.isoformat(), "end_utc": _now().isoformat(),
        "duration_s": round(t1 - t0, 1), "requests": total, "rps": round(total / max(t1 - t0, 0.001), 1),
        "p50_ms": _pct(lat, 50), "p95_ms": _pct(lat, 95), "p99_ms": _pct(lat, 99),
        "max_ms": round(lat[-1], 1) if lat else None, "statuses": statuses,
        "errors": errors, "error_count": sum(errors.values()),
    }


def _logs_insights(start, end):
    s, e = int(start.timestamp()) - 60, int(end.timestamp()) + 120
    q = ("fields @timestamp, event, peak_in_use, in_use, size, max, acquires, waited, max_wait_ms, timeouts, wait_ms "
         "| filter @logStream like /^api\\// and event like /aa859_main_pool_(gauge|wait|acquire_timeout)/ "
         "| sort @timestamp asc | limit 500")
    q_stats = ("filter @logStream like /^api\\// and event like /aa859_main_pool_(gauge|wait|acquire_timeout)/ "
               "| stats count(*) as n, max(peak_in_use) as peak, max(max_wait_ms) as gauge_max_wait, "
               "sum(waited) as waited, sum(timeouts) as timeouts_gauge, max(wait_ms) as max_wait_line "
               "by event, @logStream")

    def cmd(query):
        return (f"aws logs start-query --log-group-name {LOG_GROUP} --start-time {s} --end-time {e} "
                f"--query-string '{query}' --profile aa365-admin --region us-west-1 --query queryId --output text")
    return {"window_epoch": [s, e], "rows": cmd(q), "stats": cmd(q_stats),
            "results": ("aws logs get-query-results --query-id <id> --profile aa365-admin --region us-west-1 "
                        "--output json")}


async def _health_ready(client):
    try:
        r = await client.get(f"{BASE}/health/ready")
        return {"status": r.status_code, "body": r.json() if "json" in r.headers.get("content-type", "") else None}
    except Exception as e:
        return {"error": type(e).__name__}


async def main(label):
    import httpx
    ids, meta = await _read_ids_and_settings()
    random.Random(859).shuffle(ids)
    sampler = Sampler()
    await sampler.start()
    limits = httpx.Limits(max_connections=max(STEPS) + 10, max_keepalive_connections=max(STEPS) + 10)
    began = _now()
    out = {"issue": "AA-859", "session": "S247", "label": label, "base": BASE, "in_ecs": IN_ECS,
           "steps_cfg": {"steps": STEPS, "step_s": STEP_S, "pause_s": PAUSE_S, "warmup_s": WARMUP_S},
           "meta": meta, "steps": []}
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=False, limits=limits) as client:
            out["health_ready_before"] = await _health_ready(client)
            _, _, warm = await _step(client, ids, 5, WARMUP_S)
            out["warmup"] = warm
            for i, c in enumerate(STEPS):
                await asyncio.sleep(PAUSE_S if i else 5)
                t0, t1, res = await _step(client, ids, c, STEP_S)
                res["pg_stat_activity"] = sampler.window(t0, t1)
                out["steps"].append(res)
            out["health_ready_after"] = await _health_ready(client)
    finally:
        await sampler.stop()
    ended = _now()
    out["window_utc"] = [began.isoformat(), ended.isoformat()]
    out["logs_insights"] = _logs_insights(began, ended)
    body = json.dumps(out, indent=2, default=str).encode()
    if IN_ECS:
        import boto3
        key = S3_KEY.format(label=label)
        s3 = boto3.client("s3", region_name="us-west-1")
        s3.put_object(Bucket=BUCKET, Key=key, Body=body, ContentType="application/json")
        where = f"s3://{BUCKET}/{key}"
    else:
        where = os.path.abspath(f"aa859_main_burst_{label}.json")
        with open(where, "wb") as f:
            f.write(body)
    summary = " ".join(
        f"c{s['concurrency']}:p95={s['p95_ms']}ms,p99={s['p99_ms']}ms,rps={s['rps']},err={s['error_count']},"
        f"inuse={(s['pg_stat_activity'] or {}).get('max_in_use')}" for s in out["steps"])
    print(f"OK {label} {summary} -> {where} ({len(body)} B)")


if __name__ == "__main__":
    lbl = sys.argv[1] if len(sys.argv) > 1 else "run"
    if not lbl.replace("-", "").replace("_", "").isalnum():
        print("ERR label must be alphanumeric (- and _ allowed)")
        sys.exit(2)
    try:
        asyncio.run(main(lbl))
    except Exception as e:
        print(f"ERR {type(e).__name__}: {str(e)[:200]}")
        sys.exit(1)
