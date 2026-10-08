import asyncio, json, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from datetime import datetime, timezone
from urllib.parse import urlparse
from collections import Counter
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    for label, a, b in (("before AA-740 (01/10-08/10 03:20)", datetime(2026,10,1,tzinfo=timezone.utc), datetime(2026,10,8,3,20,tzinfo=timezone.utc)),
                        ("after AA-740 (India b1 + regen)", datetime(2026,10,8,3,20,tzinfo=timezone.utc), datetime(2026,10,9,tzinfo=timezone.utc))):
        rows = await c.fetch("SELECT fix_pass_applied, fix_pass_fields FROM silver_aa_internal.generated_content WHERE created_at >= $1 AND created_at < $2", a, b)
        ff = Counter(); n = len(rows); fx = 0
        for r in rows:
            if r[0]:
                fx += 1; f = r[1]; ff.update(json.loads(f) if isinstance(f, str) else (f or []))
        print(label, "| versions", n, "| fix pass", fx, f"({100*fx//max(1,n)}%)", "| fields", dict(ff))
    calls = await c.fetch("""SELECT CASE WHEN created_at < '2026-10-08 03:20+00' THEN 'before' ELSE 'after' END p, count(*) FROM shared.llm_call_log
        WHERE stage='s1_flag_fix' AND created_at >= '2026-10-07 23:59+00' GROUP BY 1""")
    print("flag_fix calls today", [tuple(x) for x in calls])
    await c.close()
asyncio.run(main())
