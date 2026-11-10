"""AA-741 phase 2 (S275): spend of the audit tenants from the ledger + the chunk gate. READ-ONLY, $0, no write.

Run by the orchestrator before every chunk and after the run (CIS api container, DATABASE_URL = cis_app):
    tools/ecs/ecsx.sh /home/nghiep/projects/AA-Ecosys/.tmp-session/S275/aa741-p2/p2_spend.py P2_SINCE=<iso> NEXT_EST=<usd>

Cost source: shared.llm_call_log (ledger v2), non-shadow rows (is_shadow IS NOT TRUE: NULL counts as live), rows of the
4 audit-* tenants, plus rows with tenant_id NULL whose job's payload names an audit tenant (attribution gap, measure.py
S270). Stages are all T-stages the chain writes (t2_*, t7_*, t8_*, t9_*, t10_*, f10_embed); any other stage on these
tenants is listed apart (e.g. writing_memory_eval) and is NOT charged to AA-741.

Env:
  P2_SINCE   ISO time phase 2 started (required for the gate; the first trial's start, e.g. 2026-11-10T03:00:00Z)
  CAP_USD    phase 2 cap (default 13.44 = 20 approved - 6.56 spent in phases 0-1, LEDGER_TOTAL S275 conv-741)
  NEXT_EST   USD the next chunk is expected to cost (default 0): GATE says stop when spent + NEXT_EST > CAP_USD
  PHASE01    USD spent before phase 2 (default 6.5594), for the cross-check against the 20 USD approval
Lines: SPEND_TOTAL / SPEND_STAGE / SPEND_TENANT / SPEND_MODEL / OTHER_STAGE / GAP / BUDGET / CONN / UNIT / GATE.
"""
import asyncio
import os
from datetime import datetime

import asyncpg

AUDIT = ["audit-atlas-hearth", "audit-terra-family", "audit-trail-pulse", "audit-wildkind-travel"]
CHAIN = r"^(t[0-9]+_|f10_embed$)"
TENANT_OF_JOB = "coalesce(j.payload->>'tenant_id', j.payload->'context'->>'tenant_id')"


def iso(name: str, default: str) -> datetime:
    return datetime.fromisoformat(os.environ.get(name, default).replace("Z", "+00:00"))


async def main() -> None:
    if not os.environ.get("P2_SINCE"):
        print("STOP P2_SINCE (phase 2 start, ISO) is required")
        return
    since = iso("P2_SINCE", "")
    cap = float(os.environ.get("CAP_USD", "13.44"))
    nxt = float(os.environ.get("NEXT_EST", "0"))
    phase01 = float(os.environ.get("PHASE01", "6.5594"))
    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        await c.execute("SET default_transaction_read_only = on")
        await c.execute("SET statement_timeout = '60s'")
        ten = await c.fetch("SELECT tenant_id, slug FROM shared.tenants WHERE slug = ANY($1::text[]) ORDER BY slug", AUDIT)
        tids = [t["tenant_id"] for t in ten]
        slug = {t["tenant_id"]: t["slug"] for t in ten}
        base = ("FROM shared.llm_call_log l WHERE l.tenant_id = ANY($1::uuid[]) AND l.created_at >= $2::timestamptz "
                "AND l.is_shadow IS NOT TRUE")

        tot = await c.fetchrow(f"SELECT count(*) AS n, coalesce(sum(l.cost_usd),0) AS usd {base} AND l.stage ~ $3",
                               tids, since, CHAIN)
        gap = await c.fetchrow(
            "SELECT count(*) AS n, coalesce(sum(l.cost_usd),0) AS usd FROM shared.llm_call_log l "
            "WHERE l.tenant_id IS NULL AND l.created_at >= $1::timestamptz AND l.is_shadow IS NOT TRUE "
            f"AND l.job_id IN (SELECT j.id FROM shared.job j WHERE j.created_at >= $1::timestamptz "
            f"AND {TENANT_OF_JOB} = ANY($2::text[]))", since, [str(t) for t in tids])
        spent = float(tot["usd"]) + float(gap["usd"])
        print(f"SPEND_TOTAL since={since:%Y-%m-%dT%H:%MZ} calls={tot['n']} usd={float(tot['usd']):.4f} "
              f"gap_calls={gap['n']} gap_usd={float(gap['usd']):.4f} phase2_usd={spent:.4f} cap={cap:.2f} "
              f"left={cap - spent:.4f} aa741_total={phase01 + spent:.4f}/20")
        for r in await c.fetch(
                f"SELECT l.stage, l.role, count(*) AS n, coalesce(sum(l.cost_usd),0) AS usd, "
                f"count(*) FILTER (WHERE coalesce(l.status,'ok') <> 'ok') AS not_ok, "
                f"count(*) FILTER (WHERE l.stop_reason = 'max_tokens') AS max_tok "
                f"{base} AND l.stage ~ $3 GROUP BY 1,2 ORDER BY usd DESC", tids, since, CHAIN):
            print(f"SPEND_STAGE stage={r['stage']} role={r['role']} calls={r['n']} not_ok={r['not_ok']} "
                  f"max_tokens={r['max_tok']} usd={float(r['usd']):.4f}")
        for r in await c.fetch(
                f"SELECT l.stage, coalesce(l.model,'-') AS model, coalesce(l.connection_key,'-') AS conn, count(*) AS n, "
                f"coalesce(sum(l.cost_usd),0) AS usd, array_agg(DISTINCT l.route_config_version) AS rv, "
                f"array_agg(DISTINCT coalesce(l.prompt_version,'-')) AS pv "
                f"{base} AND l.stage ~ $3 GROUP BY 1,2,3 ORDER BY 1, usd DESC", tids, since, CHAIN):
            print(f"SPEND_MODEL stage={r['stage']} served={r['model']}@{r['conn']} calls={r['n']} "
                  f"usd={float(r['usd']):.4f} route_versions={list(r['rv'])[:4]} prompt_versions={list(r['pv'])[:4]}")
        for r in await c.fetch(
                f"SELECT l.tenant_id, count(*) AS n, coalesce(sum(l.cost_usd),0) AS usd {base} AND l.stage ~ $3 "
                f"GROUP BY 1 ORDER BY 1", tids, since, CHAIN):
            print(f"SPEND_TENANT {slug[r['tenant_id']]} calls={r['n']} usd={float(r['usd']):.4f}")
        for r in await c.fetch(
                f"SELECT l.stage, count(*) AS n, coalesce(sum(l.cost_usd),0) AS usd {base} AND l.stage !~ $3 "
                f"GROUP BY 1 ORDER BY usd DESC", tids, since, CHAIN):
            print(f"OTHER_STAGE stage={r['stage']} calls={r['n']} usd={float(r['usd']):.4f} (not charged to AA-741)")

        # Unit costs from finished pairs (for the next chunk's NEXT_EST): T2 per version, blog per piece.
        t2 = await c.fetchrow(
            "SELECT count(*) AS n, coalesce(sum(x.usd),0) AS usd FROM ("
            "  SELECT v.id, (SELECT coalesce(sum(l.cost_usd),0) FROM shared.llm_call_log l WHERE l.job_id = v.job_id "
            "     AND l.is_shadow IS NOT TRUE) AS usd "
            "  FROM gold_aa_internal.tenant_tour_versions v WHERE v.tenant_id = ANY($1::uuid[]) "
            "  AND v.created_at >= $2::timestamptz AND v.status NOT IN ('pending','failed')) x", tids, since)
        blog = await c.fetchrow(
            "SELECT count(*) AS n, coalesce(sum(x.usd),0) AS usd FROM ("
            "  SELECT cp.piece_id, (SELECT coalesce(sum(l.cost_usd),0) FROM shared.llm_call_log l "
            "     WHERE l.is_shadow IS NOT TRUE AND (l.content_piece_id = cp.piece_id "
            "       OR l.angle_gate_request_id = cp.angle_gate_request_id OR l.job_id = cp.job_id)) AS usd "
            "  FROM acp_shared.content_piece cp WHERE cp.tenant_id = ANY($1::uuid[]) AND cp.channel = 'blog' "
            "  AND cp.created_at >= $2::timestamptz AND cp.status <> 'processing') x", tids, since)
        t7 = await c.fetchrow(f"SELECT count(*) AS n, coalesce(sum(l.cost_usd),0) AS usd {base} AND l.stage ~ '^t7_'",
                              tids, since)
        u_t2 = float(t2["usd"]) / t2["n"] if t2["n"] else None
        u_blog = float(blog["usd"]) / blog["n"] if blog["n"] else None
        print(f"UNIT t2_versions={t2['n']} usd_per_t2={u_t2 if u_t2 is None else round(u_t2, 4)} "
              f"blog_pieces={blog['n']} usd_per_blog={u_blog if u_blog is None else round(u_blog, 4)} "
              f"t7_usd={float(t7['usd']):.4f} (est. if none yet: t2 0.17, blog 0.13; chunk of k new tours x 4 "
              f"= 4k*(t2+blog)*1.15 + 0.05)")

        print("== tenant AI budgets (gateway hard stop at the approval %, plan Growth 40 USD; no row = plan)")
        for t in ten:
            bud = await c.fetchval("SELECT limit_value FROM shared.v_tenant_entitlement_resolved "
                                   "WHERE tenant_id = $1 AND feature_key = 'ai.budget_usd_monthly'", t["tenant_id"])
            row = await c.fetchrow("SELECT monthly_usd, alert_pct, approval_pct, hard_stop FROM shared.tenant_ai_budget "
                                   "WHERE tenant_id = $1", t["tenant_id"])
            mtd = await c.fetchval("SELECT coalesce(sum(cost_usd),0) FROM shared.llm_call_log WHERE tenant_id = $1 "
                                   "AND created_at >= date_trunc('month', now()) AND is_shadow IS NOT TRUE",
                                   t["tenant_id"])
            appr = (row["approval_pct"] if row else 100) or 100
            limit = float(row["monthly_usd"]) if row and row["monthly_usd"] is not None else (float(bud) if bud is not None else None)
            stop_at = None if limit is None else limit * appr / 100.0
            held = await c.fetchval(f"SELECT count(*) FROM shared.job j WHERE j.status = 'stopped_budget' "
                                    f"AND j.created_at >= $1::timestamptz AND {TENANT_OF_JOB} = $2", since,
                                    str(t["tenant_id"]))
            print(f"BUDGET {t['slug']} resolved={bud} row={'yes' if row else 'no'} mtd_usd={float(mtd):.4f} "
                  f"stops_at={stop_at} headroom={None if stop_at is None else round(stop_at - float(mtd), 2)} "
                  f"stopped_budget_jobs={held}")
        for r in await c.fetch("SELECT connection_key, monthly_budget_usd FROM shared.llm_provider_connection "
                               "WHERE connection_key IN ('anthropic-direct', 'openai-direct') ORDER BY 1"):
            mtd = await c.fetchval("SELECT coalesce(sum(cost_usd),0) FROM shared.llm_call_log WHERE connection_key = $1 "
                                   "AND created_at >= date_trunc('month', now()) AND is_shadow IS NOT TRUE",
                                   r["connection_key"])
            print(f"CONN {r['connection_key']} cap={r['monthly_budget_usd']} mtd_usd={float(mtd):.4f}")

        verdict = "ok" if spent + nxt <= cap else "stop"
        print(f"GATE {verdict} spent={spent:.4f} next_est={nxt:.4f} cap={cap:.2f} "
              f"(stop: do not start the next chunk; shrink it to the tours that fit, or end phase 2 and report)")
    finally:
        await c.close()


asyncio.run(main())
