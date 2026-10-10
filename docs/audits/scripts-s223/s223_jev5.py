"""AA-756: live act-rate (enforce, 30 days, latest decision per subject) at current vs proposed thresholds."""
import asyncio, boto3, asyncpg
from urllib.parse import urlparse
P = {  # q: (cur_reject, new_reject, cur_accept, new_accept)
 "a1_claim_supported": (None, 0.30, 0.90, 0.85),
 "a3_demand_belongs": (0.40, 0.70, None, None),
 "a3_landing_belongs": (0.30, 0.40, None, None),
 "a3_keyword_belongs": (0.30, 0.45, 0.95, 0.85),
 "a3_same_place": (0.10, 0.10, None, 0.70),
 "a3_atom_in_text": (0.30, 0.30, None, None),
}
async def main():
    u = urlparse(boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"])
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    for q, (cr, nr, ca, na) in P.items():
        r = await c.fetchrow("""WITH last AS (SELECT DISTINCT ON (subject_key) probability p FROM shared.decision_log
              WHERE question_key=$1 AND created_at > now()-interval '30 days' AND probability IS NOT NULL ORDER BY subject_key, created_at DESC)
            SELECT count(*) n,
              count(*) FILTER (WHERE $2::numeric IS NOT NULL AND p <= $2) cur_rej, count(*) FILTER (WHERE $3::numeric IS NOT NULL AND p <= $3) new_rej,
              count(*) FILTER (WHERE $4::numeric IS NOT NULL AND p >= $4) cur_acc, count(*) FILTER (WHERE $5::numeric IS NOT NULL AND p >= $5) new_acc
            FROM last""", q, cr, nr, ca, na)
        n = r["n"] or 1
        print(f"{q:22} subjects {r['n']:6} | reject {cr}->{nr}: {r['cur_rej']/n:.1%} -> {r['new_rej']/n:.1%} | accept {ca}->{na}: {r['cur_acc']/n:.1%} -> {r['new_acc']/n:.1%}")
    await c.close()
asyncio.run(main())
