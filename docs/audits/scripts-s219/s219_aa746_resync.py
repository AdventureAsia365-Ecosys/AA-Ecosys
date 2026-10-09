"""AA-746 one-off: run the deployed sync_batch_completion() on every batch stuck in 'ingesting'."""
import asyncio, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
from services.export.handler import sync_batch_completion
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    kw = dict(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    c = await asyncpg.connect(**kw)
    ids = [r["batch_id"] for r in await c.fetch("SELECT batch_id FROM shared.pipeline_runs WHERE status='ingesting'")]
    print("stuck before", len(ids))
    for b in ids:
        print(b, await sync_batch_completion(c, b))
    await c.close()
    c2 = await asyncpg.connect(**kw)
    print("ingesting after", await c2.fetchval("SELECT count(*) FROM shared.pipeline_runs WHERE status='ingesting'"))
    await c2.close()
asyncio.run(main())
