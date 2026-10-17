"""S241 D-10 restore drill: compare row counts per schema between Dev and the restored drill instance. Read-only."""
import asyncio, asyncpg, boto3, json, time
from urllib.parse import urlparse
DRILL = "<drill-endpoint>"
SQL = """SELECT n.nspname s, c.relname t FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
         WHERE c.relkind='r' AND n.nspname NOT IN ('pg_catalog','information_schema','pg_toast') ORDER BY 1,2"""
async def counts(host, u):
    c = await asyncpg.connect(host=host, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require", timeout=30)
    t0 = time.time(); out = {}
    for r in await c.fetch(SQL):
        out[f"{r['s']}.{r['t']}"] = await c.fetchval(f'SELECT count(*) FROM "{r["s"]}"."{r["t"]}"')
    mig = await c.fetch("SELECT version FROM shared.schema_versions ORDER BY applied_at DESC LIMIT 3")
    await c.close()
    return out, [m["version"] for m in mig], round(time.time() - t0, 1)
async def main():
    u = urlparse(boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"])
    src, src_mig, ts = await counts(u.hostname, u)
    dr, dr_mig, td = await counts(DRILL, u)
    schemas = {}
    for k in src:
        s = k.split(".")[0]; d = schemas.setdefault(s, {"tables": 0, "rows_src": 0, "rows_drill": 0, "missing": 0, "diff_tables": 0})
        d["tables"] += 1; d["rows_src"] += src[k]; d["rows_drill"] += dr.get(k, 0)
        if k not in dr: d["missing"] += 1
        elif dr[k] != src[k]: d["diff_tables"] += 1
    print(json.dumps({"schemas": schemas, "tables_src": len(src), "tables_drill": len(dr), "mig_src": src_mig, "mig_drill": dr_mig, "secs_src": ts, "secs_drill": td}, default=str))
asyncio.run(main())
