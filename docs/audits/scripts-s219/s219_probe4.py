"""Read-only: for routes rewritten 00:46-00:51 with different segments — set change or order only? Which segments flip?"""
import asyncio, json, boto3, asyncpg
from collections import Counter
from urllib.parse import urlparse
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    rows = await c.fetch("""
      SELECT n.ordered_segment_ids n_s, o.ordered_segment_ids o_s
      FROM acp_contract.route n
      JOIN LATERAL (SELECT * FROM acp_contract.route o WHERE o.tour_id=n.tour_id AND o.first_day=n.first_day
                    AND o.last_day=n.last_day AND o.version < n.version ORDER BY o.version DESC LIMIT 1) o ON true
      WHERE n.created_at BETWEEN '2026-10-09 00:46:00+00' AND '2026-10-09 00:51:00+00'
        AND n.ordered_segment_ids <> o.ordered_segment_ids""")
    kind = Counter(); added = Counter(); removed = Counter()
    for r in rows:
        a = json.loads(r["n_s"]) if isinstance(r["n_s"], str) else r["n_s"]
        b = json.loads(r["o_s"]) if isinstance(r["o_s"], str) else r["o_s"]
        if set(a) == set(b): kind["order only"] += 1
        else:
            kind["set changed"] += 1; added.update(set(a) - set(b)); removed.update(set(b) - set(a))
    print(dict(kind), "| distinct segs added", len(added), "removed", len(removed))
    flips = list((added | removed).keys())[:400]
    ex = await c.fetch("""SELECT s.segment_id, s.canonical_place, s.canonical_action, s.created_at,
          (SELECT string_agg(DISTINCT coalesce(ar.excluded_reason,'-'), ',') FROM acp_contract.atom_ranking ar WHERE ar.segment_id=s.segment_id AND ar.superseded_at IS NULL) cur_excl,
          (SELECT string_agg(DISTINCT coalesce(ar.excluded_reason,'-'), ',') FROM acp_contract.atom_ranking ar WHERE ar.segment_id=s.segment_id AND ar.superseded_at IS NOT NULL) old_excl
        FROM acp_contract.atom_segment s WHERE s.segment_id = ANY($1::text[])""", flips)
    print(Counter((r["cur_excl"], r["old_excl"]) for r in ex).most_common(10))
    print("created during S219:", sum(r["created_at"].isoformat() >= "2026-10-08T23:00" for r in ex), "/", len(ex))
    for r in ex[:8]: print("  ", r["canonical_place"][:40], "|", r["canonical_action"][:30], "| cur", r["cur_excl"], "| old", r["old_excl"])
    await c.close()
asyncio.run(main())
