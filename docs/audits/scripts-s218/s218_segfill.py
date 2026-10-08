"""S218 backfill (Refs AA-695): fold every active tour that has atoms but no Segment membership into
the platform Segment set (run_segment_matching per tour), then one platform Score + Route recompute.
env LIMIT (tours, default all), RECOMPUTE=1 to run the Score/Route pass. Progress -> s3 scripts/s218_segfill_progress.json"""
import asyncio, json, os, sys, time
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse

S3 = boto3.client("s3", region_name="us-west-1")
def put(obj):
    S3.put_object(Bucket="aa-cis-bronze-005097885195", Key="scripts/s218_segfill_progress.json", Body=json.dumps(obj, default=str, indent=1).encode())

async def main():
    from services.acp_contract.segment_matching import run_segment_matching
    from services.export.handler import recompute_rankings_and_routes
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    pool = await asyncpg.create_pool(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password,
                                     database=u.path.lstrip("/"), ssl="require", min_size=1, max_size=6)
    limit = int(os.environ.get("LIMIT") or 100000)
    tours = [r["tour_id"] for r in await pool.fetch("""
        SELECT a.tour_id::text FROM acp_contract.v_active_tour_atoms a
        GROUP BY a.tour_id
        HAVING count(*) FILTER (WHERE EXISTS (SELECT 1 FROM acp_contract.atom_segment_member m WHERE m.atom_id = a.atom_id)) = 0
        ORDER BY a.tour_id LIMIT $1""", limit)]
    seg0 = await pool.fetchval("SELECT count(*) FROM acp_contract.atom_segment")
    st = {"started": time.strftime("%FT%TZ", time.gmtime()), "todo": len(tours), "done": 0, "failed": [], "segments_before": seg0, "results": []}
    put(st)
    for i, tid in enumerate(tours, 1):
        t0 = time.time()
        try:
            res = await run_segment_matching(tid, pool)
            st["results"].append({"tour": tid, "s": round(time.time() - t0, 1), **{k: res.get(k) for k in ("segments_written", "atoms", "aliases")}})
        except Exception as exc:
            st["failed"].append({"tour": tid, "error": f"{type(exc).__name__}: {str(exc)[:300]}"})
        st["done"] = i
        if i % 10 == 0 or i == len(tours):
            st["segments_now"] = await pool.fetchval("SELECT count(*) FROM acp_contract.atom_segment")
            put(st)
    if os.environ.get("RECOMPUTE") == "1":
        t0 = time.time(); st["phase"] = "recompute"; put(st)
        try:
            r = await recompute_rankings_and_routes(pool, log_reason="s218_segment_backfill")
            st["recompute"] = {"s": round(time.time() - t0, 1), "route": r.get("route")}
        except Exception as exc:
            st["recompute"] = {"error": f"{type(exc).__name__}: {str(exc)[:300]}"}
    st["finished"] = time.strftime("%FT%TZ", time.gmtime()); st["phase"] = "done"
    put(st)
    await pool.close()
asyncio.run(main())
