"""AA-741 phase 2 (S275): per (tenant x tour) pair, where T2 and the Blog piece stand. READ-ONLY, $0, no write.

Run by the orchestrator after each step and at the end (CIS api container, DATABASE_URL = cis_app):
    tools/ecs/ecsx.sh /home/nghiep/projects/AA-Ecosys/.tmp-session/S275/aa741-p2/p2_status.py TOURS8=<PICK_LIST> P2_SINCE=<iso>

TOURS8   the 12 8-char published_tours.id prefixes (PICK_LIST of p2_pick.py)
P2_SINCE phase 2 start (ISO); a Blog piece counts for phase 2 only from then (phase 0/1 pieces predate CIS #1341/#1342)
Lines:
  PAIR tenant=<slug> tour=<p8> t2=<latest version status>/<qa_status> t2_job=<status> blog=<piece status>
       held=<held_reason class or -> blog_job=<status> blog_subject=<s8 or ->
  TOTAL pairs=<n>/48 t2_ok=<n> blog_ok=<n> (ok = T2 non-failed, blog piece approved or held = delivered or Lab-held)
  JOBS  non-terminal / stopped_budget / failed jobs of the audit tenants since P2_SINCE, per kind
  WAVES open rerun waves (phase 2 never opens one; a non-zero count here is someone else's and blocks CIS deploys)
Done for a pair (Done-when 2): T2 version not failed AND a Blog piece in a terminal state (approved | held).
"""
import asyncio
import os
from datetime import datetime

import asyncpg

AUDIT = ["audit-atlas-hearth", "audit-terra-family", "audit-trail-pulse", "audit-wildkind-travel"]
TENANT_OF_JOB = "coalesce(j.payload->>'tenant_id', j.payload->'context'->>'tenant_id')"


async def main() -> None:
    tours8 = [t.strip().lower()[:8] for t in os.environ.get("TOURS8", "").split(",") if t.strip()]
    if not tours8 or not os.environ.get("P2_SINCE"):
        print("STOP TOURS8 and P2_SINCE are required")
        return
    since = datetime.fromisoformat(os.environ["P2_SINCE"].replace("Z", "+00:00"))
    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        await c.execute("SET default_transaction_read_only = on")
        await c.execute("SET statement_timeout = '60s'")
        ten = await c.fetch("SELECT tenant_id, slug FROM shared.tenants WHERE slug = ANY($1::text[]) ORDER BY slug", AUDIT)
        pts = await c.fetch("SELECT id, tour_id FROM gold_aa_internal.published_tours WHERE left(id::text, 8) = ANY($1::text[])",
                            tours8)
        byp = {}
        for r in pts:
            byp.setdefault(str(r["id"])[:8], []).append(r)
        n_pairs = t2_ok = blog_ok = 0
        for t in ten:
            for p8 in tours8:
                if len(byp.get(p8, [])) != 1:
                    print(f"WARN tour={p8} matches={len(byp.get(p8, []))}")
                    continue
                p = byp[p8][0]
                n_pairs += 1
                v = await c.fetchrow(
                    "SELECT v.status, v.qa_status, j.status AS jst FROM gold_aa_internal.tenant_tour_versions v "
                    "LEFT JOIN shared.job j ON j.id = v.job_id WHERE v.tenant_id = $1 AND v.published_tour_id = $2 "
                    "ORDER BY v.version_number DESC LIMIT 1", t["tenant_id"], p["id"])
                b = await c.fetchrow(
                    "SELECT cp.status, cp.held_reason IS NOT NULL AS has_held, s.subject_id, j.status AS jst "
                    "FROM acp_shared.content_piece cp "
                    "JOIN acp_shared.angle_gate_request r ON r.request_id = cp.angle_gate_request_id "
                    "JOIN acp_shared.subject s ON s.subject_id = r.subject_id "
                    "LEFT JOIN shared.job j ON j.id = cp.job_id "
                    "WHERE cp.tenant_id = $1 AND cp.channel = 'blog' AND cp.created_at >= $3::timestamptz "
                    "AND s.segment_id IS NOT NULL AND EXISTS (SELECT 1 FROM acp_contract.atom_ranking ar "
                    "  WHERE ar.segment_id = s.segment_id AND ar.tour_id = $2 AND ar.excluded_reason IS NULL "
                    "  AND ar.superseded_at IS NULL) "
                    "ORDER BY (cp.status IN ('approved','held')) DESC, cp.created_at DESC LIMIT 1",
                    t["tenant_id"], p["tour_id"], since)
                ok2 = v is not None and v["status"] not in ("failed", "pending")
                okb = b is not None and b["status"] in ("approved", "held")
                t2_ok += ok2
                blog_ok += okb
                print(f"PAIR tenant={t['slug']} tour={p8} "
                      f"t2={(v['status'] + '/' + v['qa_status']) if v else 'none'} t2_job={v['jst'] if v else '-'} "
                      f"blog={b['status'] if b else 'none'} held={'yes' if b and b['has_held'] else '-'} "
                      f"blog_job={b['jst'] if b else '-'} blog_subject={str(b['subject_id'])[:8] if b else '-'} "
                      f"pair_done={'yes' if ok2 and okb else 'no'}")
        print(f"TOTAL pairs={n_pairs}/48 t2_ok={t2_ok} blog_ok={blog_ok}")
        for r in await c.fetch(
                f"SELECT j.kind, j.status, count(*) AS n FROM shared.job j "
                f"WHERE (j.status IN ('queued','running') OR (j.created_at >= $1::timestamptz "
                f"  AND j.status IN ('stopped_budget','failed','cancelled'))) "
                f"AND {TENANT_OF_JOB} = ANY($2::text[]) GROUP BY 1,2 ORDER BY 1,2",
                since, [str(t["tenant_id"]) for t in ten]):
            print(f"JOBS kind={r['kind']} status={r['status']} n={r['n']}")
        allopen = await c.fetchval("SELECT count(*) FROM shared.job WHERE status IN ('queued','running')")
        print(f"JOBS_OPEN_ALL {allopen} (must be 0 before a CIS deploy, DM-11.4)")
        waves = await c.fetchval("SELECT count(*) FROM shared.rerun_wave WHERE status = 'open'")
        print(f"WAVES open={waves}")
    finally:
        await c.close()


asyncio.run(main())
