"""AA-746 dry run: stuck 'ingesting' batches and how many tours stay unsettled under the new rule."""
import asyncio, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
UNSETTLED = """
    rt.batch_id = $1::uuid
    AND rt.pipeline_status NOT IN ('published', 'hitl_rejected', 'failed', 'hitl_required')
    AND rt.source_status = 'active'
    AND rt.deleted_at IS NULL
    AND NOT EXISTS (SELECT 1 FROM silver_aa_internal.review_queue q
                    WHERE q.tour_id = rt.tour_id AND q.review_status = 'pending')
"""
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    runs = await c.fetch("SELECT batch_id, started_at, tours_total, tours_passed FROM shared.pipeline_runs WHERE status='ingesting' ORDER BY started_at")
    print("stuck", len(runs))
    for r in runs:
        n = await c.fetchval(f"SELECT count(*) FROM silver_aa_internal.raw_tours rt WHERE {UNSETTLED}", r["batch_id"])
        old = await c.fetchval("SELECT count(*) FROM silver_aa_internal.raw_tours WHERE batch_id=$1 AND pipeline_status NOT IN ('published','hitl_rejected','failed')", r["batch_id"])
        st = await c.fetch("SELECT pipeline_status::text ps, source_status::text ss, (deleted_at IS NOT NULL) del, count(*) FROM silver_aa_internal.raw_tours rt WHERE batch_id=$1 AND pipeline_status NOT IN ('published','hitl_rejected','failed') GROUP BY 1,2,3", r["batch_id"])
        print(r["batch_id"], r["started_at"].date(), f"total={r['tours_total']} passed={r['tours_passed']} | pending old={old} new={n} |", [tuple(x) for x in st])
    await c.close()
asyncio.run(main())
