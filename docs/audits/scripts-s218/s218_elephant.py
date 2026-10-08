import asyncio, json, sys, re
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
async def main():
    ids = json.loads(boto3.client("s3", region_name="us-west-1").get_object(Bucket="aa-cis-bronze-005097885195", Key="scripts/s218_india_b1.json")["Body"].read())
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    rows = await c.fetch("""SELECT DISTINCT ON (g.tour_id) rt.src_name, rt.src_itineraries, rt.src_highlights, g.aa_highlights, g.aa_itineraries, g.aa_summary,
        q.brand_audit_status, q.brand_audit_codes, q.brand_audit_issues, q.brand_audit_fields
        FROM silver_aa_internal.generated_content g JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=g.tour_id
        JOIN silver_aa_internal.quality_scores q ON q.generated_content_id=g.id
        WHERE g.tour_id = ANY($1::uuid[]) ORDER BY g.tour_id, g.created_at DESC, q.evaluated_at DESC""", ids)
    E = re.compile(r"[^.\n]*\belephant[^.\n]*", re.I)
    for r in rows:
        codes = r["brand_audit_codes"]; codes = json.loads(codes) if isinstance(codes, str) else (codes or [])
        if "FACT_CHECK_MANUAL_CHECK" not in codes: continue
        out = json.dumps([r["aa_highlights"], r["aa_itineraries"], r["aa_summary"]], ensure_ascii=False)
        src = json.dumps([r["src_itineraries"], r["src_highlights"]], ensure_ascii=False)
        print("==", r["src_name"], "| status", r["brand_audit_status"], "| codes", codes, "| fields", r["brand_audit_fields"])
        iss = r["brand_audit_issues"]; iss = json.loads(iss) if isinstance(iss, str) else (iss or [])
        print("   issues:", [i for i in iss if "fact" in str(i).lower() or "elephant" in str(i).lower() or "wildlife" in str(i).lower()][:3])
        print("   OUT elephant:", [m.strip()[:160] for m in E.findall(out)][:3])
        print("   SRC elephant:", [m.strip()[:160] for m in E.findall(src)][:2])
    await c.close()
asyncio.run(main())
