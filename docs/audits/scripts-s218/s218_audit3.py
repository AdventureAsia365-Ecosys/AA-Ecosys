import asyncio, json, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from datetime import datetime, timezone
from urllib.parse import urlparse
from collections import Counter
S = datetime(2026, 10, 1, tzinfo=timezone.utc)
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    r = await c.fetchrow("""SELECT count(*) n, count(revalidate_passed) reval_set, count(*) FILTER (WHERE fix_pass_applied) fix,
        count(*) FILTER (WHERE fix_pass_applied AND status='approved') fix_ok, count(*) FILTER (WHERE status='approved') ok,
        count(*) FILTER (WHERE metadata ? 'revalidate_passed') md_reval, count(*) FILTER (WHERE (metadata->>'revalidate_passed')::text='true') md_reval_true,
        count(*) FILTER (WHERE metadata ? 'grounding') md_ground
        FROM silver_aa_internal.generated_content WHERE created_at >= $1""", S)
    print("GC", dict(r))
    ff = Counter()
    for x in await c.fetch("SELECT fix_pass_fields FROM silver_aa_internal.generated_content WHERE created_at >= $1 AND fix_pass_applied", S):
        f = x[0]; f = json.loads(f) if isinstance(f, str) else (f or [])
        ff.update(f)
    print("FIX FIELDS", ff.most_common())
    js = Counter()
    for x in await c.fetch("SELECT metadata->'judge'->>'judge_score' FROM silver_aa_internal.generated_content WHERE created_at >= $1", S):
        if x[0] is not None: js[x[0]] += 1
    print("JUDGE raw values", sorted(js.items()))
    print("REVIEW decisions", [dict(x) for x in await c.fetch("""SELECT review_status::text, count(*), count(reviewed_by) by_human FROM silver_aa_internal.review_queue WHERE created_at >= $1 GROUP BY 1""", S)])
    g = Counter(); gv = 0; gr = 0
    for x in await c.fetch("SELECT metadata->'grounding' FROM silver_aa_internal.generated_content WHERE created_at >= $1 AND metadata ? 'grounding'", S):
        d = json.loads(x[0]) if isinstance(x[0], str) else x[0]
        if d.get("violations"): gv += 1
        if d.get("repaired_fields"): gr += 1
        g["found"] += d.get("found") or 0
    print("GROUNDING versions", "with_repair", gr, "with_violation", gv, "found_total", g["found"])
    n = await c.fetch("""SELECT j.id, count(*) n FROM shared.llm_call_log l JOIN shared.job j ON j.id=l.job_id WHERE l.stage='s1_itinerary_nudge' AND l.created_at >= $1 GROUP BY 1""", S)
    print("NUDGE calls per job: jobs", len(n), "avg", round(sum(x[1] for x in n)/max(1,len(n)),1), "max", max([x[1] for x in n] or [0]))
    a = await c.fetch("""SELECT j.id, count(*) n FROM shared.llm_call_log l JOIN shared.job j ON j.id=l.job_id WHERE l.stage='t5_atomize' AND l.created_at >= $1 GROUP BY 1""", S)
    print("ATOMIZE calls per job: jobs", len(a), "avg", round(sum(x[1] for x in a)/max(1,len(a)),1))
    print("ATOMIZE cost per job", round(float(await c.fetchval("SELECT sum(cost_usd) FROM shared.llm_call_log WHERE stage='t5_atomize' AND created_at >= $1", S))/max(1,len(a)),4))
    w = await c.fetch("""SELECT g.tour_id, count(*) FROM shared.llm_call_log l JOIN shared.job j ON j.id=l.job_id JOIN silver_aa_internal.generated_content g ON (j.payload->>'tour_id')::uuid=g.tour_id
        WHERE l.stage='s1_generate' AND l.created_at >= $1 GROUP BY g.tour_id""", S)
    print("WRITER calls per tour (via jobs)", Counter(min(x[1], 6) for x in w).most_common())
    await c.close()
asyncio.run(main())
