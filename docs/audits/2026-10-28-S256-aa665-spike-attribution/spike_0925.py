"""AA-665 close-out — attribute the 25/09/2026 cost spike (READ ONLY).

Runs inside aa-cis-dev-api / aa-cis-dev-worker (S3-mediated ECS exec, .tmp-session/S256/exec_svc.sh).
Uses the container DATABASE_URL (cis_app), ssl="require". Only SELECTs; no writes, no paid calls.

Window: UTC day 2026-09-25 and the +07 day (2026-09-24 17:00Z .. 2026-09-25 17:00Z); every section reads the union
(2026-09-24 17:00Z .. 2026-09-26 00:00Z) and labels hours in UTC with the +07 hour next to it.

Sections (each guarded: a missing table / grant prints one ERR line and the script goes on):
  T  totals per table and per day definition (which table holds the $49.02 / ~1,170 calls)
  H  hourly buckets: LLM (calls, $, top stage) and DFS (calls, live, $)
  S  top LLM stages (stage/role/model/account, tenant, job-linked share)
  D  DFS by endpoint, tenant/tour/meta coverage, last paid call (= failure point)
  B  bursts of a3_search_demand LLM calls and of live DFS calls (gap > 10 min splits a burst)
  R  tenant rewrites before each burst: tenant_tour_versions, tenant LLM stages, tenant_api_usage POSTs
  J  jobs in the window: shared.job and shared.pipeline_jobs (kind, status, starter)
  C  what is left of the research cache for 25/09 (segment_research_log, search_demand) after the S199 repair
"""
import asyncio
import os
from datetime import datetime, timedelta, timezone

import asyncpg

UTC = timezone.utc
D0 = datetime(2026, 9, 25, tzinfo=UTC)                 # UTC day
D1 = D0 + timedelta(days=1)
L0 = datetime(2026, 9, 24, 17, tzinfo=UTC)             # +07 day 25/09
L1 = L0 + timedelta(days=1)
U0, U1 = L0, D1                                        # union read window
GAP_MIN = 10


def p(tag, *parts):
    print(tag + " " + " | ".join(str(x) for x in parts), flush=True)


def hh(ts):
    return f"{ts:%H:%M:%S}Z(+07 {(ts + timedelta(hours=7)):%H:%M})" if ts else "-"


def money(v):
    return f"${float(v or 0):.4f}"


async def section(name, fn, conn):
    try:
        await fn(conn)
    except Exception as e:  # keep going; one line per failure
        p("ERR", name, type(e).__name__, str(e)[:200])


async def totals(conn):
    for label, a, b in (("utc_day", D0, D1), ("plus07_day", L0, L1)):
        r = await conn.fetchrow(
            "SELECT count(*) n, coalesce(sum(cost_usd),0) c, count(*) FILTER (WHERE job_id IS NOT NULL) linked,"
            " count(*) FILTER (WHERE tenant_id IS NOT NULL) with_tenant"
            " FROM shared.llm_call_log WHERE created_at >= $1 AND created_at < $2", a, b)
        p("T", "llm", label, r["n"], money(r["c"]), f"job_linked={r['linked']}", f"tenant={r['with_tenant']}")
        r = await conn.fetchrow(
            "SELECT count(*) n, count(*) FILTER (WHERE fetched_live) live, coalesce(sum(cost_usd),0) c,"
            " count(*) FILTER (WHERE tenant_id IS NOT NULL) with_tenant, count(*) FILTER (WHERE tour_id IS NOT NULL) with_tour"
            " FROM shared.dfs_call_log WHERE created_at >= $1 AND created_at < $2", a, b)
        p("T", "dfs", label, r["n"], f"live={r['live']}", money(r["c"]), f"tenant={r['with_tenant']}",
          f"tour={r['with_tour']}")
    # the daily rollup (if 25/09 was ever rolled up the raw rows may be gone)
    rows = await conn.fetch(
        "SELECT day, sum(calls) n, sum(cost_usd) c FROM shared.llm_call_daily"
        " WHERE day BETWEEN '2026-09-24' AND '2026-09-26' GROUP BY day ORDER BY day")
    for r in rows:
        p("T", "llm_call_daily", r["day"], r["n"], money(r["c"]))
    # context: the days around (is 25/09 an outlier?)
    rows = await conn.fetch(
        "SELECT date_trunc('day', created_at) d, count(*) n, coalesce(sum(cost_usd),0) c FROM shared.llm_call_log"
        " WHERE created_at >= '2026-09-20' AND created_at < '2026-09-30' GROUP BY 1 ORDER BY 1")
    p("T", "llm_by_day_20_29", "; ".join(f"{r['d']:%d/%m} {r['n']} {money(r['c'])}" for r in rows))
    rows = await conn.fetch(
        "SELECT date_trunc('day', created_at) d, count(*) n, coalesce(sum(cost_usd),0) c FROM shared.dfs_call_log"
        " WHERE created_at >= '2026-09-20' AND created_at < '2026-09-30' GROUP BY 1 ORDER BY 1")
    p("T", "dfs_by_day_20_29", "; ".join(f"{r['d']:%d/%m} {r['n']} {money(r['c'])}" for r in rows))


async def hourly(conn):
    rows = await conn.fetch("""
        WITH h AS (SELECT date_trunc('hour', created_at) hr, stage, count(*) n, coalesce(sum(cost_usd),0) c
                     FROM shared.llm_call_log WHERE created_at >= $1 AND created_at < $2 GROUP BY 1, 2),
             t AS (SELECT hr, sum(n) n, sum(c) c FROM h GROUP BY hr),
             top AS (SELECT DISTINCT ON (hr) hr, stage, n, c FROM h ORDER BY hr, c DESC)
        SELECT t.hr, t.n, t.c, top.stage, top.n tn, top.c tc FROM t JOIN top USING (hr) ORDER BY t.hr""", U0, U1)
    for r in rows:
        p("H", "llm", hh(r["hr"]), r["n"], money(r["c"]), f"top={r['stage']} {r['tn']} {money(r['tc'])}")
    rows = await conn.fetch("""
        SELECT date_trunc('hour', created_at) hr, count(*) n, count(*) FILTER (WHERE fetched_live) live,
               count(*) FILTER (WHERE cache_hit) hits, coalesce(sum(cost_usd),0) c,
               coalesce(sum(keyword_count),0) kw
          FROM shared.dfs_call_log WHERE created_at >= $1 AND created_at < $2 GROUP BY 1 ORDER BY 1""", U0, U1)
    for r in rows:
        p("H", "dfs", hh(r["hr"]), r["n"], f"live={r['live']}", f"hits={r['hits']}", money(r["c"]), f"kw={r['kw']}")


async def stages(conn):
    rows = await conn.fetch("""
        SELECT l.stage, l.role, l.model, coalesce(l.provider,'-') prov, coalesce(l.account,'-') acct,
               coalesce(t.slug, l.tenant_id::text, '-') tenant,
               count(*) n, coalesce(sum(l.cost_usd),0) c, count(*) FILTER (WHERE l.job_id IS NOT NULL) linked,
               count(*) FILTER (WHERE l.fallback_used) fb, min(l.created_at) a, max(l.created_at) b
          FROM shared.llm_call_log l LEFT JOIN shared.tenants t ON t.tenant_id = l.tenant_id
         WHERE l.created_at >= $1 AND l.created_at < $2
         GROUP BY 1,2,3,4,5,6 ORDER BY c DESC LIMIT 25""", U0, U1)
    for r in rows:
        p("S", r["stage"], r["role"], r["model"], r["prov"], r["acct"], r["tenant"], r["n"], money(r["c"]),
          f"job_linked={r['linked']}", f"fallback={r['fb']}", hh(r["a"]), hh(r["b"]))


async def dfs(conn):
    rows = await conn.fetch("""
        SELECT endpoint, coalesce(t.slug, d.tenant_id::text, '-') tenant, count(*) n,
               count(*) FILTER (WHERE fetched_live) live, coalesce(sum(cost_usd),0) c,
               round(avg(keyword_count) FILTER (WHERE fetched_live), 1) avg_kw, max(keyword_count) max_kw,
               count(DISTINCT location_code) locs, count(*) FILTER (WHERE d.tour_id IS NOT NULL) with_tour,
               min(created_at) a, max(created_at) b
          FROM shared.dfs_call_log d LEFT JOIN shared.tenants t ON t.tenant_id = d.tenant_id
         WHERE created_at >= $1 AND created_at < $2 GROUP BY 1, 2 ORDER BY c DESC""", U0, U1)
    for r in rows:
        p("D", r["endpoint"], r["tenant"], r["n"], f"live={r['live']}", money(r["c"]), f"avg_kw={r['avg_kw']}",
          f"max_kw={r['max_kw']}", f"locs={r['locs']}", f"with_tour={r['with_tour']}", hh(r["a"]), hh(r["b"]))
    rows = await conn.fetch("""
        SELECT location_code, count(*) n, coalesce(sum(cost_usd),0) c FROM shared.dfs_call_log
         WHERE created_at >= $1 AND created_at < $2 GROUP BY 1 ORDER BY c DESC""", U0, U1)
    p("D", "by_location", "; ".join(f"{r['location_code']} {r['n']} {money(r['c'])}" for r in rows))
    r = await conn.fetchrow("""
        SELECT max(created_at) FILTER (WHERE cost_usd > 0) last_paid, min(created_at) FILTER (WHERE cost_usd > 0) first_paid,
               max(created_at) last_any FROM shared.dfs_call_log WHERE created_at >= $1 AND created_at < $2""", U0, U1)
    p("D", "first_paid", hh(r["first_paid"]), "last_paid(failure point)", hh(r["last_paid"]), "last_row", hh(r["last_any"]))
    rows = await conn.fetch("""
        SELECT k, count(*) n FROM shared.dfs_call_log d, LATERAL jsonb_object_keys(coalesce(d.meta,'{}'::jsonb)) k
         WHERE created_at >= $1 AND created_at < $2 GROUP BY k ORDER BY n DESC LIMIT 15""", U0, U1)
    p("D", "meta_keys", "; ".join(f"{r['k']}={r['n']}" for r in rows) or "none")
    # the DataForSEO balance read (AA-627 Lambda) around the spike
    rows = await conn.fetch(
        "SELECT fetched_at, balance_usd, below_threshold FROM shared.dfs_balance_snapshot"
        " WHERE fetched_at >= '2026-09-23' AND fetched_at < '2026-09-29' ORDER BY fetched_at")
    p("D", "balance", "; ".join(f"{r['fetched_at']:%d/%m %H:%M}Z ${float(r['balance_usd']):.2f}"
                                 f"{' LOW' if r['below_threshold'] else ''}" for r in rows) or "none 23-28/09")


def bursts_of(times):
    out, cur = [], []
    for t in times:
        if cur and (t - cur[-1]) > timedelta(minutes=GAP_MIN):
            out.append(cur)
            cur = []
        cur.append(t)
    if cur:
        out.append(cur)
    return out


async def bursts(conn):
    rows = await conn.fetch(
        "SELECT created_at, cost_usd FROM shared.llm_call_log WHERE stage = 'a3_search_demand'"
        " AND created_at >= $1 AND created_at < $2 ORDER BY created_at", U0, U1)
    llm_b = bursts_of([r["created_at"] for r in rows])
    cost_at = {}
    for r in rows:
        cost_at[r["created_at"]] = cost_at.get(r["created_at"], 0) + float(r["cost_usd"] or 0)
    for i, b in enumerate(llm_b):
        p("B", f"llm_a3_search_demand#{i+1}", hh(b[0]), hh(b[-1]), f"calls={len(b)}",
          money(sum(cost_at.get(t, 0) for t in set(b))))
    rows = await conn.fetch(
        "SELECT created_at, cost_usd, endpoint FROM shared.dfs_call_log WHERE fetched_live"
        " AND created_at >= $1 AND created_at < $2 ORDER BY created_at", U0, U1)
    dfs_b = bursts_of([r["created_at"] for r in rows])
    for i, b in enumerate(dfs_b):
        lo, hi = b[0], b[-1]
        sel = [r for r in rows if lo <= r["created_at"] <= hi]
        p("B", f"dfs_live#{i+1}", hh(lo), hh(hi), f"calls={len(sel)}",
          money(sum(float(r["cost_usd"] or 0) for r in sel)),
          "endpoints=" + ",".join(sorted({r["endpoint"] for r in sel})))
    starts = sorted({b[0] for b in llm_b} | {b[0] for b in dfs_b})
    await rewrites(conn, starts)


async def rewrites(conn, starts):
    # 1) tenant_tour_versions written in the window (RLS: cis_app has an all-rows policy)
    rows = await conn.fetch("""
        SELECT v.id, coalesce(t.slug, v.tenant_id::text) tenant, v.published_tour_id, pt.aa_name,
               v.version_number, v.status, v.qa_status, v.edit_source, v.job_id, v.created_at, v.qa_checked_at
          FROM gold_aa_internal.tenant_tour_versions v
          LEFT JOIN shared.tenants t ON t.tenant_id = v.tenant_id
          LEFT JOIN gold_aa_internal.published_tours pt ON pt.id = v.published_tour_id
         WHERE v.created_at >= $1 AND v.created_at < $2 ORDER BY v.created_at""", U0, U1)
    p("R", "tenant_tour_versions_in_window", len(rows))
    for r in rows:
        p("R", "ttv", r["tenant"], (r["aa_name"] or str(r["published_tour_id"]))[:60], f"v{r['version_number']}",
          r["status"], r["qa_status"], r["edit_source"], f"job={r['job_id']}", "created", hh(r["created_at"]),
          "qa_checked", hh(r["qa_checked_at"]))
    # 2) tenant-scoped LLM stages (the T2 writer survives any test-data cleanup: S196 kept llm_call_log on purpose)
    rows = await conn.fetch("""
        SELECT coalesce(t.slug, l.tenant_id::text) tenant, l.stage, count(*) n, coalesce(sum(l.cost_usd),0) c,
               min(l.created_at) a, max(l.created_at) b
          FROM shared.llm_call_log l LEFT JOIN shared.tenants t ON t.tenant_id = l.tenant_id
         WHERE l.tenant_id IS NOT NULL AND l.created_at >= $1 AND l.created_at < $2
         GROUP BY 1, 2 ORDER BY min(l.created_at)""", U0, U1)
    for r in rows:
        p("R", "tenant_llm", r["tenant"], r["stage"], r["n"], money(r["c"]), hh(r["a"]), hh(r["b"]))
    # 3) the tenant rewrite request itself (tenant_api_usage keeps 90 days raw)
    rows = await conn.fetch("""
        SELECT coalesce(t.slug, u.tenant_id::text, 'admin') who, u.actor_type, u.method, u.endpoint, u.status_code,
               u.response_ms, u.called_at
          FROM shared.tenant_api_usage u LEFT JOIN shared.tenants t ON t.tenant_id = u.tenant_id
         WHERE u.called_at >= $1 AND u.called_at < $2 AND u.method <> 'GET'
         ORDER BY u.called_at""", U0, U1)
    p("R", "non_get_api_calls", len(rows))
    for r in rows[:60]:
        p("R", "api", r["who"], r["actor_type"], r["method"], r["endpoint"], r["status_code"], f"{r['response_ms']}ms",
          hh(r["called_at"]))
    # 4) nearest tenant writer activity before each burst start (lag in seconds)
    for s in starts:
        r = await conn.fetchrow("""
            SELECT coalesce(t.slug, l.tenant_id::text) tenant, l.stage, l.created_at
              FROM shared.llm_call_log l LEFT JOIN shared.tenants t ON t.tenant_id = l.tenant_id
             WHERE l.tenant_id IS NOT NULL AND l.created_at <= $1 AND l.created_at > $1 - interval '30 minutes'
             ORDER BY l.created_at DESC LIMIT 1""", s)
        v = await conn.fetchrow("""
            SELECT coalesce(t.slug, v.tenant_id::text) tenant, coalesce(v.qa_checked_at, v.created_at) ts, v.id
              FROM gold_aa_internal.tenant_tour_versions v LEFT JOIN shared.tenants t ON t.tenant_id = v.tenant_id
             WHERE coalesce(v.qa_checked_at, v.created_at) <= $1
               AND coalesce(v.qa_checked_at, v.created_at) > $1 - interval '30 minutes'
             ORDER BY 2 DESC LIMIT 1""", s)
        p("R", "before_burst", hh(s),
          f"last_tenant_llm={r['tenant']}/{r['stage']} lag={(s - r['created_at']).total_seconds():.0f}s" if r else "last_tenant_llm=none",
          f"last_version={v['tenant']} {v['id']} lag={(s - v['ts']).total_seconds():.0f}s" if v else "last_version=none")


async def jobs(conn):
    for sql, label in (
        ("SELECT kind k, status, coalesce(created_by,'-') who, count(*) n, min(created_at) a, max(coalesce(finished_at, updated_at)) b"
         " FROM shared.job WHERE created_at < $2 AND coalesce(finished_at, updated_at) >= $1 GROUP BY 1,2,3 ORDER BY a", "job"),
        ("SELECT job_type k, status, coalesce(tenant,'-') who, count(*) n, min(created_at) a, max(coalesce(finished_at, heartbeat_at, created_at)) b"
         " FROM shared.pipeline_jobs WHERE created_at < $2 AND coalesce(finished_at, heartbeat_at, created_at) >= $1"
         " GROUP BY 1,2,3 ORDER BY a", "pipeline_jobs"),
    ):
        try:
            rows = await conn.fetch(sql, U0, U1)
            p("J", label, "rows", len(rows))
            for r in rows:
                p("J", label, r["k"], r["status"], r["who"], r["n"], hh(r["a"]), hh(r["b"]))
        except Exception as e:
            p("J", label, "ERR", type(e).__name__, str(e)[:160])
    try:
        r = await conn.fetchrow("SELECT min(created_at) a FROM shared.job")
        p("J", "shared.job_first_row_ever", r["a"])
    except Exception as e:
        p("J", "shared.job", "ERR", type(e).__name__)


async def cache(conn):
    rows = await conn.fetch("""
        SELECT market, count(*) n, min(researched_at) a, max(researched_at) b FROM acp_contract.segment_research_log
         WHERE researched_at >= $1 AND researched_at < $2 GROUP BY 1 ORDER BY 1""", U0, U1)
    p("C", "segment_research_log_25_09_left", "; ".join(f"{r['market']} {r['n']} {hh(r['a'])}..{hh(r['b'])}" for r in rows) or "0 rows")
    rows = await conn.fetch("""
        SELECT market, count(*) n, count(*) FILTER (WHERE search_volume IS NULL) nul FROM acp_contract.search_demand
         WHERE retrieved_on >= $1 AND retrieved_on < $2 GROUP BY 1 ORDER BY 1""", U0, U1)
    p("C", "search_demand_25_09_left", "; ".join(f"{r['market']} {r['n']} null={r['nul']}" for r in rows) or "0 rows")
    r = await conn.fetchrow("SELECT count(DISTINCT canonical_place) places, count(*) segs FROM acp_contract.atom_segment"
                            " WHERE created_at < '2026-09-25 05:00+00'")
    p("C", "atom_segment_before_spike", f"places={r['places']}", f"segments={r['segs']}")


async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        await conn.execute("SET statement_timeout = '60s'")
        await conn.execute("SET TIME ZONE 'UTC'")  # date_trunc buckets in UTC
        await conn.execute("SET default_transaction_read_only = on")
        p("#", "AA-665 spike 25/09", f"union window {U0:%Y-%m-%d %H:%M}Z..{U1:%Y-%m-%d %H:%M}Z", f"gap={GAP_MIN}min")
        for name, fn in (("totals", totals), ("hourly", hourly), ("stages", stages), ("dfs", dfs),
                         ("bursts", bursts), ("jobs", jobs), ("cache", cache)):
            await section(name, fn, conn)
    finally:
        await conn.close()


asyncio.run(main())
