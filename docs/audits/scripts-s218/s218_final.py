import asyncio, json, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
from collections import Counter
from services.content_generation.forbidden_words import all_forbidden, has_word
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    tw = await c.fetchval("""SELECT forbidden_words FROM shared.tenant_brand_rules WHERE tenant_id='00000000-0000-0000-0000-000000000001'::uuid AND is_active ORDER BY (brand_name='default') DESC, version DESC LIMIT 1""")
    words = all_forbidden(json.loads(tw) if isinstance(tw, str) else tw)
    for country in ("Nepal", "Sri Lanka"):
        r = await c.fetchrow("""SELECT count(*) n,
            count(*) FILTER (WHERE EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=rt.tour_id AND p.master_status='active')) master,
            count(*) FILTER (WHERE EXISTS (SELECT 1 FROM silver_aa_internal.review_queue q WHERE q.tour_id=rt.tour_id AND q.review_status='pending')
                             AND NOT EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=rt.tour_id AND p.master_status='active')) review,
            count(*) FILTER (WHERE EXISTS (SELECT 1 FROM acp_contract.v_active_tour_atoms a WHERE a.tour_id=rt.tour_id)) atomized,
            count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM silver_aa_internal.generated_content g WHERE g.tour_id=rt.tour_id)) not_run
          FROM silver_aa_internal.raw_tours rt WHERE rt.country=$1 AND rt.source_status='active' AND rt.deleted_at IS NULL""", country)
        rq = await c.fetch("""SELECT q.failure_summary FROM silver_aa_internal.review_queue q JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=q.tour_id
            WHERE rt.country=$1 AND q.review_status='pending' AND rt.source_status='active'
              AND NOT EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=rt.tour_id AND p.master_status='active')""", country)
        cats = Counter()
        for x in rq:
            s = x["failure_summary"] or ""
            if "low_quality" in s: cats["low_quality (judge<7)"] += 1
            elif "FORBIDDEN_WORD" in s: cats["forbidden_word"] += 1
            elif any(k in s for k in ("SEO_META_TOO_LONG", "META_TOO_SHORT", "SEO_TITLE_TOO_LONG")): cats["seo length"] += 1
            elif "UNSUPPORTED_NUMBER" in s or "manual_check" in s: cats["grounding/manual_check"] += 1
            else: cats["other"] += 1
        # forbidden words in body of ACTIVE masters (published content)
        pub = await c.fetch("""SELECT DISTINCT ON (p.tour_id) g.aa_name, g.aa_subtitle, g.aa_summary, g.aa_description, g.aa_highlights, g.aa_itineraries, g.seo_title, g.seo_meta
            FROM gold_aa_internal.published_tours p JOIN silver_aa_internal.generated_content g ON g.id=p.generated_content_id
            JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=p.tour_id
            WHERE rt.country=$1 AND p.master_status='active' ORDER BY p.tour_id, p.published_at DESC""", country)
        bad = Counter()
        for m in pub:
            t = json.dumps([m[k] for k in m.keys()])
            for w in words:
                if has_word(t, w): bad[w] += 1
        print(country, dict(r), "| review by cause", dict(cats), "| masters with forbidden word in body:", sum(1 for m in pub if any(has_word(json.dumps([m[k] for k in m.keys()]), w) for w in words)), dict(bad))
    up = await c.fetchval("""SELECT count(*) FROM shared.llm_call_log WHERE stage='s1_generate' AND model ILIKE '%sonnet%' AND created_at > now() - interval '12 hours'""")
    print("s1_generate sonnet calls since S218 start:", up)
    await c.close()
asyncio.run(main())
