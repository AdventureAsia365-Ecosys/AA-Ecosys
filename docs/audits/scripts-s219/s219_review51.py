"""AA-745: list every pending review_queue tour without an active Master, classify by cause.
Read-only. Writes the classified list to s3 scripts/s219_review51.json."""
import asyncio, json, re, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
from collections import Counter

B = "aa-cis-bronze-005097885195"
ELE = re.compile(r"\belephant", re.I)

def j(v):
    return json.loads(v) if isinstance(v, str) else (v or [])

async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    rows = await c.fetch("""
      SELECT rq.id rq_id, rq.tour_id, rq.created_at, rq.failure_summary, rq.score_overall, rq.generated_content_id,
        rt.country, rt.src_name, rt.duration, length(coalesce(rt.src_itineraries,'')) srclen, rt.src_itineraries,
        g.status gstatus, g.model_editorial model_tier, g.metadata->'judge'->>'judge_score' js, g.metadata->'judge'->>'feedback' fb,
        g.metadata->'grounding'->'violations' gv, length(g.seo_meta) ml, g.seo_meta,
        q.failure_codes, q.brand_audit_codes
      FROM silver_aa_internal.review_queue rq
      JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = rq.tour_id
      LEFT JOIN silver_aa_internal.generated_content g ON g.id = rq.generated_content_id
      LEFT JOIN LATERAL (SELECT * FROM silver_aa_internal.quality_scores qq WHERE qq.generated_content_id = g.id
                         ORDER BY qq.evaluated_at DESC LIMIT 1) q ON true
      WHERE rq.review_status = 'pending'
        AND NOT EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id = rq.tour_id AND p.master_status = 'active')
      ORDER BY rt.country, rt.src_name""")
    out = []; cat = Counter()
    for r in rows:
        fc = j(r["failure_codes"]); bac = j(r["brand_audit_codes"]); gv = j(r["gv"])
        js = float(r["js"]) if r["js"] else None
        src_ele = bool(ELE.search(r["src_itineraries"] or ""))
        if "FACT_CHECK_MANUAL_CHECK" in bac or "FACT_CHECK_MANUAL_CHECK" in fc:
            k = "elephant" if src_ele else "fact_check_other"
        elif js is not None and js < 7:
            k = "low_judge"
        elif gv or "UNSUPPORTED_NUMBER" in fc:
            k = "grounding"
        elif set(fc) & {"SEO_META_TOO_LONG", "META_TOO_SHORT", "SEO_TITLE_TOO_LONG"}:
            k = "length"
        elif "FORBIDDEN_WORD" in fc:
            k = "forbidden"
        else:
            k = "other"
        cat[k] += 1
        d = dict(rq_id=str(r["rq_id"]), tour_id=str(r["tour_id"]), country=r["country"], name=r["src_name"],
                 duration=r["duration"], srclen=r["srclen"], cat=k, judge=js, score=float(r["score_overall"] or 0),
                 model_tier=r["model_tier"], codes=fc, ba_codes=bac, meta_len=r["ml"],
                 fb=(r["fb"] or "")[:400], gv=gv[:4], summary=(r["failure_summary"] or "")[-220:],
                 created=r["created_at"].isoformat())
        out.append(d)
    for d in out:
        print(f"[{d['cat']}] {d['country']} | {d['name'][:60]} | dur={d['duration']} src={d['srclen']} | judge={d['judge']} score={d['score']} tier={d['model_tier']}")
        print(f"    codes={d['codes']} ba={d['ba_codes']}")
        if d["cat"] in ("low_judge", "other", "fact_check_other"): print(f"    fb: {d['fb'][:300]}")
        if d["gv"]: print(f"    gv: {json.dumps(d['gv'], ensure_ascii=False)[:300]}")
        if d["cat"] == "length": print(f"    meta_len={d['meta_len']} summary={d['summary']}")
    print("\nTOTAL", len(out), dict(cat))
    print("BY COUNTRY", Counter(d["country"] for d in out))
    boto3.client("s3", region_name="us-west-1").put_object(Bucket=B, Key="scripts/s219_review51.json", Body=json.dumps(out, ensure_ascii=False).encode())
    await c.close()

asyncio.run(main())
