# Read-only (S239 AA-668 rerun, defect D1): Slate subject -> segment -> member atoms vs the request's atom.
# Run via the S3-mediated ECS exec pattern (orchestrator only). Writes JSON to S3 scripts/out/.
import asyncio, json, boto3, asyncpg
from urllib.parse import urlparse
SUBJECTS = ["b54e9058-b057-4690-bb28-2976ac9fe363", "766e9956-4d29-4d0a-8fdf-187f4158ad5b", "f886d436-4d2e-4ec1-b413-05d7ee1229e7"]
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"].strip()
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    out = {}
    for sid in SUBJECTS:
        s = await c.fetchrow("SELECT s.subject_id::text, s.segment_id, s.route_id, s.channel, s.state, g.canonical_place, g.canonical_action FROM acp_shared.subject s LEFT JOIN acp_contract.atom_segment g ON g.segment_id = s.segment_id WHERE s.subject_id = $1::uuid", sid)
        mem = await c.fetch("""SELECT m.atom_id, m.is_alias, ta.place, ta.action, ta.owner_scope, ta.deleted, ta.is_empty_marker, rt.country, left(ta.text, 90) AS text
            FROM acp_contract.atom_segment_member m JOIN acp_contract.tour_atoms ta ON ta.atom_id = m.atom_id
            LEFT JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = ta.tour_id
            WHERE m.segment_id = $1 ORDER BY m.atom_id""", s["segment_id"]) if s and s["segment_id"] else []
        reqs = await c.fetch("SELECT request_id::text, atom_id, status, created_at::text FROM acp_shared.angle_gate_request WHERE subject_id = $1::uuid ORDER BY created_at", sid)
        out[sid] = {"subject": dict(s) if s else None, "members": [dict(r) for r in mem], "requests": [dict(r) for r in reqs]}
    await c.close()
    boto3.client("s3", region_name="us-west-1").put_object(Bucket="aa-cis-bronze-005097885195", Key="scripts/out/s239_aa668_subject_atoms.json", Body=json.dumps(out, default=str, ensure_ascii=False).encode())
    print("OK")
asyncio.run(main())
