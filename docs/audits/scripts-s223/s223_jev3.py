import asyncio, json, boto3, asyncpg
from urllib.parse import urlparse
async def main():
    u = urlparse(boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"])
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    for q in ("a1_claim_supported", "a3_atom_in_text", "a3_same_place"):
        print("==", q, dict(await c.fetchrow("SELECT mode, accept_floor, reject_ceiling, threshold_version, calibration_ref, kind FROM shared.decision_question WHERE question_key=$1", q) or {}))
        for r in await c.fetch("""SELECT zone, choice, probability, outcome, subject_key FROM shared.decision_log WHERE question_key=$1 AND mode='enforce'
                                   ORDER BY created_at DESC LIMIT 4""", q):
            print("  ", r["zone"], r["choice"], r["probability"], "| outcome:", json.dumps(r["outcome"])[:160] if r["outcome"] else None, "| subj:", (r["subject_key"] or "")[:50])
        print("  outcome filled:", await c.fetchval("SELECT round(100.0*count(*) FILTER (WHERE outcome IS NOT NULL)/count(*)) FROM shared.decision_log WHERE question_key=$1 AND created_at > now()-interval '30 days'", q), "%")
    print("all questions:", [(r["question_key"], r["mode"], r["accept_floor"], r["reject_ceiling"]) for r in await c.fetch("SELECT question_key, mode, accept_floor, reject_ceiling FROM shared.decision_question ORDER BY 1")])
    await c.close()
asyncio.run(main())
