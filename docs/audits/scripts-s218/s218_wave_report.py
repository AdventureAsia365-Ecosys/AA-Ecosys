"""S218 wave report: per expected tour -> master / review / atomized + job stats + cost.
IDS env = S3 key of the ids json (scripts/<name>)."""
import asyncio, json, os, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse

async def main():
    s3 = boto3.client("s3", region_name="us-west-1")
    ids = json.loads(s3.get_object(Bucket="aa-cis-bronze-005097885195", Key=os.environ["IDS"])["Body"].read())
    from datetime import datetime
    since = datetime.fromisoformat(os.environ["SINCE"].replace("Z", "+00:00"))
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    rows = await c.fetch("""
      SELECT rt.tour_id, rt.src_name, rt.pipeline_status, rt.source_status,
        (SELECT p.master_status FROM gold_aa_internal.published_tours p WHERE p.tour_id=rt.tour_id ORDER BY p.published_at DESC LIMIT 1) master,
        (SELECT q.score_overall FROM silver_aa_internal.quality_scores q
           WHERE q.tour_id=rt.tour_id ORDER BY q.evaluated_at DESC LIMIT 1) score,
        (SELECT rq.failure_summary FROM silver_aa_internal.review_queue rq WHERE rq.tour_id=rt.tour_id AND rq.review_status='pending'
           ORDER BY rq.created_at DESC LIMIT 1) review,
        (SELECT count(*) FROM acp_contract.v_active_tour_atoms a WHERE a.tour_id=rt.tour_id) atoms,
        (SELECT g.model_editorial FROM silver_aa_internal.generated_content g WHERE g.tour_id=rt.tour_id ORDER BY g.created_at DESC LIMIT 1) model
      FROM silver_aa_internal.raw_tours rt WHERE rt.tour_id = ANY($1::uuid[]) ORDER BY rt.src_name""", ids)
    n = len(ids)
    master = [r for r in rows if r["master"] == "active"]
    review = [r for r in rows if r["review"] and r["master"] != "active"]
    print(f"expected {n} | rows {len(rows)} | master {len(master)} | review {len(review)} | atomized {sum(1 for r in rows if r['atoms'])}")
    for r in rows:
        print(f"  {r['src_name'][:50]:50} | master={r['master']} score={r['score']} atoms={r['atoms']} model={r['model']}"
              + (f"\n      REVIEW: {r['review'][:220]}" if r["review"] else ""))
    j = await c.fetch("""SELECT kind, status, count(*) n,
        round(percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM finished_at-started_at))::numeric) p50_run,
        round(max(extract(epoch FROM started_at-created_at))::numeric) max_wait, min(created_at) t0, max(finished_at) t1
      FROM shared.job WHERE created_at >= $1 AND kind IN ('s1_rewrite','a3_atomize','s1_seo_prefetch')
      GROUP BY 1,2 ORDER BY 1""", since)
    for x in j: print(" job", dict(x))
    cost = await c.fetch("""SELECT l.stage, l.model, count(*) n, round(sum(l.cost_usd)::numeric,3) cost
      FROM shared.llm_call_log l WHERE l.created_at >= $1 GROUP BY 1,2 ORDER BY cost DESC NULLS LAST LIMIT 12""", since)
    tot = sum(float(x["cost"] or 0) for x in cost)
    for x in cost: print(" llm", dict(x))
    print(" llm total ~", round(tot, 2))
    sonnet = await c.fetchval("""SELECT count(*) FROM shared.llm_call_log WHERE created_at >= $1
                                 AND stage='s1_generate' AND model ILIKE '%sonnet%'""", since)
    print(" s1_generate on sonnet (upgrade runs):", sonnet)
    await c.close()
asyncio.run(main())
