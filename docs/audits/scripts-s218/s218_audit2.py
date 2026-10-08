import asyncio, json, sys, re
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
from collections import Counter
from services.content_generation.forbidden_words import all_forbidden, has_word
from services.content_generation.seo_meta_utils import tour_days
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    rows = await c.fetch("""SELECT rt.tour_id, rt.duration, EXISTS (SELECT 1 FROM acp_contract.route r WHERE r.tour_id=rt.tour_id AND r.superseded_at IS NULL) has_route
        FROM silver_aa_internal.raw_tours rt WHERE EXISTS (SELECT 1 FROM acp_contract.v_active_tour_atoms a WHERE a.tour_id=rt.tour_id)""")
    b = Counter()
    for r in rows:
        d = tour_days(r["duration"]) or 0
        k = "1 day" if d <= 1 else "2-3 days" if d <= 3 else "4-7 days" if d <= 7 else "8+ days"
        b[(k, r["has_route"])] += 1
    print("ROUTE by length", sorted(b.items()))
    # segments: singleton segments whose canonical place appears in another segment (fragmentation signal)
    seg = await c.fetch("""SELECT s.segment_id, lower(s.canonical_place) place, lower(s.canonical_action) action, count(m.atom_id) n
        FROM acp_contract.atom_segment s LEFT JOIN acp_contract.atom_segment_member m ON m.segment_id=s.segment_id GROUP BY 1,2,3""")
    by_place = Counter(r["place"] for r in seg)
    single = [r for r in seg if r["n"] == 1]
    frag = sum(1 for r in single if by_place[r["place"]] > 1)
    print("SEGMENTS total", len(seg), "| singletons", len(single), "| singletons sharing a place with another segment", frag,
          "| empty segments", sum(1 for r in seg if r["n"] == 0))
    print("top places with most segments", by_place.most_common(8))
    # same-place segments: action spread example
    top = by_place.most_common(1)[0][0]
    print("actions for", top, Counter(r["action"] for r in seg if r["place"] == top).most_common(10))
    tw = await c.fetchval("""SELECT forbidden_words FROM shared.tenant_brand_rules WHERE tenant_id='00000000-0000-0000-0000-000000000001'::uuid AND is_active ORDER BY (brand_name='default') DESC, version DESC LIMIT 1""")
    words = all_forbidden(json.loads(tw) if isinstance(tw, str) else tw)
    at = await c.fetch("SELECT text FROM acp_contract.v_active_tour_atoms")
    wc = Counter(w for x in at for w in words if has_word(x["text"] or "", w))
    print("ATOM forbidden words", wc.most_common(10))
    await c.close()
asyncio.run(main())
