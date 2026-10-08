import asyncio, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    rows = await c.fetch("""SELECT coalesce(rt.country,'<null>') country,
        count(*) FILTER (WHERE rt.source_status='active' AND rt.deleted_at IS NULL) active,
        count(*) FILTER (WHERE rt.source_status='active' AND rt.deleted_at IS NULL AND trim(coalesce(rt.src_itineraries,''))<>'') ready,
        count(*) FILTER (WHERE rt.source_status='active' AND rt.deleted_at IS NULL AND EXISTS (SELECT 1 FROM silver_aa_internal.generated_content g WHERE g.tour_id=rt.tour_id)) has_gc,
        count(*) FILTER (WHERE EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=rt.tour_id AND p.master_status='active')) master,
        count(*) FILTER (WHERE rt.source_status='active' AND rt.deleted_at IS NULL AND trim(coalesce(rt.src_itineraries,''))<>''
            AND NOT EXISTS (SELECT 1 FROM silver_aa_internal.generated_content g WHERE g.tour_id=rt.tour_id)) not_run,
        count(*) FILTER (WHERE rt.source_status='trashed') trashed,
        count(*) FILTER (WHERE rt.source_status='superseded') superseded
        FROM silver_aa_internal.raw_tours rt GROUP BY 1 ORDER BY 2 DESC""")
    print(f"{'country':22}{'active':>7}{'ready':>7}{'has_gc':>7}{'master':>7}{'notrun':>7}{'trash':>7}{'super':>7}")
    for r in rows: print(f"{r['country'][:22]:22}{r['active']:7}{r['ready']:7}{r['has_gc']:7}{r['master']:7}{r['not_run']:7}{r['trashed']:7}{r['superseded']:7}")
    await c.close()
asyncio.run(main())
