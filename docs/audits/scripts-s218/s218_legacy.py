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
    pub = await c.fetch("""SELECT DISTINCT ON (p.tour_id) p.tour_id::text tid, rt.country, g.aa_name, g.aa_subtitle, g.aa_summary, g.aa_description, g.aa_highlights, g.aa_itineraries, g.seo_title, g.seo_meta
        FROM gold_aa_internal.published_tours p JOIN silver_aa_internal.generated_content g ON g.id=p.generated_content_id
        JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=p.tour_id
        WHERE p.master_status='active' AND rt.source_status='active' ORDER BY p.tour_id, p.published_at DESC""")
    per = Counter(); tot = Counter(); wc = Counter(); fields = Counter(); ids = {}
    for m in pub:
        tot[m["country"]] += 1
        hit = False
        for k in ("aa_name","aa_subtitle","aa_summary","aa_description","aa_highlights","aa_itineraries","seo_title","seo_meta"):
            v = m[k]; t = v if isinstance(v, str) else json.dumps(v)
            ws = [w for w in words if t and has_word(t, w)]
            if ws: hit = True; fields[k] += 1; wc.update(ws)
        if hit: per[m["country"]] += 1; ids.setdefault(m["country"], []).append(m["tid"])
    print("active masters with a forbidden word in copy, by country:")
    for k in sorted(tot): print(f"  {k}: {per[k]}/{tot[k]}")
    print("total", sum(per.values()), "/", sum(tot.values()))
    print("top words", wc.most_common(12)); print("fields", dict(fields))
    boto3.client("s3", region_name="us-west-1").put_object(Bucket="aa-cis-bronze-005097885195", Key="scripts/s218_legacy_ids.json", Body=json.dumps(ids).encode())
    await c.close()
asyncio.run(main())
