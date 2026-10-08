"""Per-tour reasons for tours of an id set that are NOT on Master: judge score + feedback, codes,
fix fields, grounding violations, source size. IDS env = S3 key of the ids json."""
import asyncio, json, os, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
from collections import Counter
async def main():
    ids = json.loads(boto3.client("s3", region_name="us-west-1").get_object(Bucket="aa-cis-bronze-005097885195", Key=os.environ["IDS"])["Body"].read())
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    rows = await c.fetch("""
      SELECT DISTINCT ON (rt.tour_id) rt.src_name, rt.duration, length(coalesce(rt.src_itineraries,'')) srclen,
        g.status, g.fix_pass_fields, g.metadata->'judge'->>'judge_score' js, g.metadata->'judge'->>'feedback' fb,
        g.metadata->'grounding'->'violations' gv, length(g.seo_meta) ml, length(g.seo_title) tl,
        q.failure_codes, q.score_overall, rq.failure_summary,
        EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=rt.tour_id AND p.master_status='active') master
      FROM silver_aa_internal.raw_tours rt
      LEFT JOIN silver_aa_internal.generated_content g ON g.tour_id=rt.tour_id
      LEFT JOIN silver_aa_internal.quality_scores q ON q.generated_content_id=g.id
      LEFT JOIN silver_aa_internal.review_queue rq ON rq.generated_content_id=g.id
      WHERE rt.tour_id = ANY($1::uuid[]) ORDER BY rt.tour_id, g.created_at DESC NULLS LAST, q.evaluated_at DESC""", ids)
    bad = [r for r in rows if not r["master"]]
    print(f"ids {len(ids)} | master {len(rows)-len(bad)} | not master {len(bad)}")
    cat = Counter(); codes = Counter()
    for r in bad:
        fc = r["failure_codes"]; fc = json.loads(fc) if isinstance(fc, str) else (fc or [])
        codes.update(fc)
        js = float(r["js"]) if r["js"] else None
        k = ("low_judge" if (js is not None and js < 7) else
             "length" if set(fc) & {"SEO_META_TOO_LONG", "META_TOO_SHORT", "SEO_TITLE_TOO_LONG"} else
             "forbidden" if "FORBIDDEN_WORD" in fc else
             "grounding" if (r["gv"] and r["gv"] != "[]") or "UNSUPPORTED_NUMBER" in fc else
             "no_version" if r["status"] is None else "other")
        cat[k] += 1
        gv = json.loads(r["gv"]) if isinstance(r["gv"], str) else (r["gv"] or [])
        print(f"\n- [{k}] {r['src_name'][:55]} | dur={r['duration']} src={r['srclen']} | score={r['score_overall']} judge={r['js']} meta={r['ml']} title={r['tl']} fix={r['fix_pass_fields']}")
        print(f"    codes={fc}")
        if r["failure_summary"]: print(f"    summary: {r['failure_summary'][-160:]}")
        if js is not None and js < 7: print(f"    judge: {(r['fb'] or '')[:330]}")
        if gv: print(f"    grounding: {json.dumps(gv, ensure_ascii=False)[:300]}")
    print("\nCATEGORIES", dict(cat)); print("CODES", codes.most_common(15))
    await c.close()
asyncio.run(main())
