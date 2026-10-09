"""AA-742 scope 4 — old cached=true decision_log rows.
MODE=dry: counts + rollup preview + gzip CSV export of every cached row to S3 (restore file). No writes.
MODE=apply: in ONE transaction, fold the rows into shared.decision_cache_hits_daily (so the summary
counts do not change), delete them, check the counts match the dry run."""
import asyncio, gzip, json, os, boto3, asyncpg
from urllib.parse import urlparse
B = "aa-cis-bronze-005097885195"
MODE = os.environ.get("MODE", "dry")
FOLD = """
    INSERT INTO shared.decision_cache_hits_daily (day, stage, question_key, mode, zone, hits)
    SELECT created_at::date, stage, question_key, mode, zone, count(*)
    FROM shared.decision_log WHERE cached
    GROUP BY 1, 2, 3, 4, 5
    ON CONFLICT (day, stage, question_key, mode, zone)
    DO UPDATE SET hits = shared.decision_cache_hits_daily.hits + excluded.hits, updated_at = now()
"""
async def main():
    s3 = boto3.client("s3", region_name="us-west-1")
    dsn = s3 and boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    kw = dict(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    c = await asyncpg.connect(**kw)
    tot = await c.fetchrow("SELECT count(*) total, count(*) FILTER (WHERE cached) cached, min(created_at) FILTER (WHERE cached) first, max(created_at) FILTER (WHERE cached) last, pg_size_pretty(pg_total_relation_size('shared.decision_log')) size FROM shared.decision_log")
    print("decision_log", dict(tot))
    by = await c.fetch("SELECT stage, question_key, count(*) n FROM shared.decision_log WHERE cached GROUP BY 1,2 ORDER BY 3 DESC LIMIT 8")
    print("top cached", [tuple(r) for r in by])
    groups = await c.fetchval("SELECT count(*) FROM (SELECT 1 FROM shared.decision_log WHERE cached GROUP BY created_at::date, stage, question_key, mode, zone) g")
    print("rollup groups to fold", groups)
    if MODE == "dry":
        path = "/tmp/aa742_cached_rows.csv"
        await c.copy_from_query("SELECT * FROM shared.decision_log WHERE cached ORDER BY id", output=path, format="csv", header=True)
        with open(path, "rb") as f, gzip.open(path + ".gz", "wb") as g:
            g.writelines(f)
        key = "scripts/restore/aa742_decision_log_cached_rows_20261009.csv.gz"
        s3.upload_file(path + ".gz", B, key)
        print("export", f"s3://{B}/{key}", os.path.getsize(path + ".gz"), "bytes gz")
        s3.put_object(Bucket=B, Key="scripts/s219_aa742_dry.json", Body=json.dumps({"cached": tot["cached"], "groups": groups}).encode())
    if MODE == "apply":
        exp = json.loads(s3.get_object(Bucket=B, Key="scripts/s219_aa742_dry.json")["Body"].read())
        async with c.transaction():
            await c.execute(FOLD)
            r = await c.execute("DELETE FROM shared.decision_log WHERE cached")
            n = int(r.split()[-1])
            print("deleted", n, "expected >=", exp["cached"])
            assert n >= exp["cached"] and n - exp["cached"] < 1000, "count differs from dry run — rolling back"
        await c.execute("VACUUM (ANALYZE) shared.decision_log")
        c2 = await asyncpg.connect(**kw)
        print("after", dict(await c2.fetchrow("SELECT count(*) total, count(*) FILTER (WHERE cached) cached, pg_size_pretty(pg_total_relation_size('shared.decision_log')) size FROM shared.decision_log")),
              "rollup hits", await c2.fetchval("SELECT sum(hits) FROM shared.decision_cache_hits_daily"))
        await c2.close()
    await c.close()
asyncio.run(main())
