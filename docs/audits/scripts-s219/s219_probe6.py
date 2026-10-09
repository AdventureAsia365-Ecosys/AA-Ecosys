"""Read-only: for flipped transit segments — rule, atom types now, and every original Jev verdict for the moment."""
import asyncio, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
from services.acp_contract.atom_ranking import classify_exclusion, atoms_say_transit, landing_moment
NAMES = [("Delhi to Agra", "road transfer"), ("Islamabad", "airport transfer"), ("Mount Data", "pass through"), ("Gairibans", "cross border checkpoint")]
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    for place, action in NAMES:
        segs = await c.fetch("""SELECT s.segment_id, s.created_at, array_agg(ta.activity_type) types, array_agg(ta.updated_at ORDER BY ta.updated_at DESC) upd
            FROM acp_contract.atom_segment s JOIN acp_contract.atom_segment_member m ON m.segment_id=s.segment_id
            JOIN acp_contract.v_active_tour_atoms ta ON ta.atom_id=m.atom_id
            WHERE s.canonical_place=$1 AND s.canonical_action=$2 GROUP BY 1,2""", place, action)
        moment = landing_moment(place, action)
        log = await c.fetch("""SELECT created_at, zone, choice, round(probability::numeric,3) p, question_hash, cached
            FROM shared.decision_log WHERE subject_key=$1 ORDER BY created_at""", f"type:{moment[:300]}")
        print("==", place, "|", action, "| rule:", classify_exclusion(place, action))
        for s in segs: print("   seg", s["segment_id"][:20], "types", s["types"], "atoms_say_transit", atoms_say_transit(s["types"]), "latest atom upd", s["upd"][0])
        for l in log: print("   jev", l["created_at"].strftime("%m-%d %H:%M"), l["zone"], l["choice"], l["p"], l["question_hash"][:6] if l["question_hash"] else None, "cached" if l["cached"] else "")
    await c.close()
asyncio.run(main())
