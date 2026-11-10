"""AA-741 phase 3 slice 4 (S276): cost of the T-series chain on the 4 audit tenants. READ-ONLY, $0, no write.

Feeds the report section "Cost" (per stage, per tenant, per unit, held share, phase 1 vs phase 2, Growth cap headroom).

Run by the orchestrator (CIS api container, DATABASE_URL = cis_app):
    tools/ecs/ecsx.sh docs/audits/2026-11-10-S276-aa741-phase3/scripts/p3_4_cost.py P2_SINCE=2026-11-10T05:49:46Z

Sources: shared.llm_call_log (ledger v2, non-shadow: is_shadow IS NOT TRUE) and shared.dfs_call_log, rows of the 4 audit
tenants plus rows with tenant_id NULL whose job (or parent job) payload names an audit tenant (attribution gap, same rule
as p2_spend.py). Experiment rows (is_experiment true, e.g. the AA-900 R2 eval) are counted apart and kept out of the
units. Units:
  - T2 version: ledger rows whose job (or parent job, up to 3 levels) is a tenant_tour_versions.job_id;
  - piece: t8_*/t9_*/t10_*/f10_embed rows by content_piece_id, else the piece's job_id, else the final piece
    (highest attempt_number) of the row's angle_gate_request_id; rows of a request without a piece = "no_piece" spend;
  - t7_* (slate / debate judge) = per-tenant overhead, spread over the pieces only in the "loaded" unit.
Memory: every query is bounded by the time window and the 4 tenants; rows carry ids and numbers only (no text, no
piece/tour content); MAX_ROWS caps each fetch and the script stops if a window exceeds it.

Env:
  P2_SINCE   phase 2 start, ISO (required)                         e.g. 2026-11-10T05:49:46Z
  P2_UNTIL   phase 2 end, ISO (default: now)
  P1_SINCE   phase 1 start (default 2026-11-05T23:44:00Z, phase 1 README)
  P1_UNTIL   phase 1 end (default 2026-11-07T00:00:00Z; check the DAY lines and rerun with a better bound if needed)
  P1_README_USD  phase 1 total in the phase 1 README (default 3.6671), reconciliation only
  PHASE01    USD before phase 2 used by p2_spend.py (default 6.5594), reconciliation only
  EXCLUDE8   comma list of 8-char piece ids left out of the units (default d67e3178, synthetic piece, S238 rule)
  GROWTH_CAP Growth plan AI budget USD/month (default 40); GROWTH_T2 rewrites/month in the plan (default 200)
  MAX_ROWS   per-fetch row cap (default 100000)
Lines (label P2 / P1): TOTAL STAGE VENDOR TENANT KIND DFS UNIT_T2 T2_TOP UNIT_PIECE UNIT_BLOG HELD_SHARE HELD_HEAD
HELD_GATESET (P2) WASTE EXPERIMENT, then COMPARE_STAGE COMPARE_UNIT DAY RECON PROJECTION and one JSON_SUMMARY line.
"""
import asyncio
import collections
import json
import os
import re
import statistics
import sys
from datetime import datetime, timezone

import asyncpg

sys.path.insert(0, "/app")

AUDIT = ["audit-atlas-hearth", "audit-terra-family", "audit-trail-pulse", "audit-wildkind-travel"]
CHAIN = re.compile(r"^(t[0-9]+_|f10_embed$)")
TENANT_OF_JOB = "coalesce(j.payload->>'tenant_id', j.payload->'context'->>'tenant_id')"
LCOLS = ("l.tenant_id, l.stage, l.role, l.model, l.connection_key, l.tokens_in, l.tokens_out, l.cache_read_tokens, "
         "l.cache_write_tokens, l.reasoning_tokens, l.cost_usd, l.status, l.stop_reason, l.job_id, l.content_piece_id, "
         "l.angle_gate_request_id, l.is_experiment")


def iso(v: str) -> datetime:
    return datetime.fromisoformat(v.replace("Z", "+00:00"))


def f(x) -> float:
    return float(x or 0)


def r4(x):
    return None if x is None else round(float(x), 4)


def div(a, b):
    return None if not b else a / b


def bucket(stage: str) -> str:
    if stage.startswith("t2_"):
        return "t2"
    if stage.startswith("t7_"):
        return "t7"
    if stage.startswith(("t8_", "t9_", "t10_")) or stage == "f10_embed":
        return "piece"
    return "chain_other" if CHAIN.match(stage) else "other"


class Agg:
    __slots__ = ("calls", "usd", "tin", "tout", "cread", "cwrite", "reason", "not_ok", "not_ok_usd", "max_tok")

    def __init__(self):
        self.calls = self.tin = self.tout = self.cread = self.cwrite = self.reason = self.not_ok = self.max_tok = 0
        self.usd = self.not_ok_usd = 0.0

    def add(self, r) -> None:
        self.calls += 1
        u = f(r["cost_usd"])
        self.usd += u
        self.tin += r["tokens_in"] or 0
        self.tout += r["tokens_out"] or 0
        self.cread += r["cache_read_tokens"] or 0
        self.cwrite += r["cache_write_tokens"] or 0
        self.reason += r["reasoning_tokens"] or 0
        if (r["status"] or "ok") != "ok":
            self.not_ok += 1
            self.not_ok_usd += u
        if r["stop_reason"] == "max_tokens":
            self.max_tok += 1

    def line(self) -> str:
        return (f"calls={self.calls} usd={self.usd:.4f} tok_in={self.tin} tok_out={self.tout} cache_read={self.cread} "
                f"cache_write={self.cwrite} reasoning={self.reason} not_ok={self.not_ok} "
                f"not_ok_usd={self.not_ok_usd:.4f} max_tokens={self.max_tok} "
                f"usd_per_call={r4(div(self.usd, self.calls))} avg_out={round(div(self.tout, self.calls) or 0)}")


async def fetch_capped(c, q, *args, max_rows: int, what: str):
    rows = await c.fetch(f"{q} LIMIT {max_rows + 1}", *args)
    if len(rows) > max_rows:
        raise SystemExit(f"STOP {what} has more than MAX_ROWS={max_rows} rows in the window; narrow it")
    return rows


async def window(c, label, tids, slug, since, until, max_rows, exclude8, want_gates):
    """Load one window, attribute every ledger / DFS row to a unit, print the lines, return the summary dict."""
    tid_txt = [str(t) for t in tids]
    jobs = await fetch_capped(
        c,
        f"WITH tj AS (SELECT j.id, {TENANT_OF_JOB} AS t FROM shared.job j WHERE j.created_at >= $1 "
        f"  AND j.created_at < $2 AND {TENANT_OF_JOB} = ANY($3::text[])) "
        f"SELECT j.id, j.kind, j.status, j.cost_usd, j.parent_job_id, coalesce(tj.t, p.t) AS t "
        f"FROM shared.job j LEFT JOIN tj ON tj.id = j.id LEFT JOIN tj p ON p.id = j.parent_job_id "
        f"WHERE j.created_at >= $1 AND j.created_at < $2 AND (tj.id IS NOT NULL OR p.id IS NOT NULL)",
        since, until, tid_txt, max_rows=max_rows, what=f"{label} jobs")
    job = {r["id"]: r for r in jobs}
    job_ids = list(job)
    rows = list(await fetch_capped(
        c, f"SELECT {LCOLS}, false AS gap FROM shared.llm_call_log l WHERE l.tenant_id = ANY($1::uuid[]) "
           f"AND l.created_at >= $2 AND l.created_at < $3 AND l.is_shadow IS NOT TRUE",
        tids, since, until, max_rows=max_rows, what=f"{label} ledger"))
    if job_ids:
        rows += await fetch_capped(
            c, f"SELECT {LCOLS}, true AS gap FROM shared.llm_call_log l WHERE l.tenant_id IS NULL "
               f"AND l.job_id = ANY($1::uuid[]) AND l.created_at >= $2 AND l.created_at < $3 AND l.is_shadow IS NOT TRUE",
            job_ids, since, until, max_rows=max_rows, what=f"{label} ledger gap")
    pieces = await fetch_capped(
        c, "SELECT cp.piece_id, cp.tenant_id, cp.angle_gate_request_id, cp.attempt_number, cp.status, cp.channel, "
           "cp.job_id, cp.created_at, substring(cp.held_reason from '^\\s*([A-Za-z0-9_]{1,40})') AS hr_tok, "
           "CASE WHEN jsonb_typeof(cp.discarded_attempts) = 'array' THEN jsonb_array_length(cp.discarded_attempts) "
           "ELSE 0 END AS n_disc FROM acp_shared.content_piece cp WHERE cp.tenant_id = ANY($1::uuid[]) "
           "AND cp.created_at >= $2 AND cp.created_at < $3",
        tids, since, until, max_rows=max_rows, what=f"{label} pieces")
    pieces = [dict(p) for p in pieces if str(p["piece_id"])[:8] not in exclude8]
    for p in pieces:  # S276 review: only a code token of held_reason (F4_extreme_length / degraded), never prose
        tok = p.pop("hr_tok") or ""
        p["hr_head"] = tok if tok and ("_" in tok or tok.islower()) else ("free_text" if tok else None)
    versions = await fetch_capped(
        c, "SELECT v.id, v.tenant_id, v.published_tour_id, v.version_number, v.status, v.qa_status, v.edit_source, "
           "v.job_id FROM gold_aa_internal.tenant_tour_versions v WHERE v.tenant_id = ANY($1::uuid[]) "
           "AND v.created_at >= $2 AND v.created_at < $3",
        tids, since, until, max_rows=max_rows, what=f"{label} versions")
    reqs = await fetch_capped(
        c, "SELECT r.request_id, r.channel FROM acp_shared.angle_gate_request r WHERE r.tenant_id = ANY($1::uuid[])",
        tids, max_rows=max_rows, what=f"{label} requests")
    req_channel = {r["request_id"]: r["channel"] or "-" for r in reqs}
    dfs = await fetch_capped(
        c, "SELECT d.tenant_id, coalesce(d.stage, '-') AS stage, d.endpoint, d.cost_usd, d.cache_hit, d.fetched_live, "
           "coalesce(d.status, '-') AS status, d.job_id FROM shared.dfs_call_log d WHERE d.created_at >= $2 "
           "AND d.created_at < $3 AND (d.tenant_id = ANY($1::uuid[]) OR (d.tenant_id IS NULL AND d.job_id = ANY($4::uuid[])))",
        tids, since, until, job_ids, max_rows=max_rows, what=f"{label} dfs")

    # ---- unit maps
    def job_tenant(jid):
        j = job.get(jid)
        return j["t"] if j else None

    def resolve(jid, mapping):
        for _ in range(4):
            if jid is None:
                return None
            if jid in mapping:
                return mapping[jid]
            j = job.get(jid)
            jid = j["parent_job_id"] if j else None
        return None

    vby = {v["id"]: v for v in versions}
    job_to_version = {}
    for v in sorted(versions, key=lambda v: v["version_number"]):
        if v["job_id"]:
            job_to_version[v["job_id"]] = v["id"]
    pby = {p["piece_id"]: p for p in pieces}
    job_to_piece, req_to_piece = {}, {}
    for p in sorted(pieces, key=lambda p: (p["attempt_number"], p["created_at"])):
        if p["job_id"]:
            job_to_piece[p["job_id"]] = p["piece_id"]
        req_to_piece[p["angle_gate_request_id"]] = p["piece_id"]

    tslug = {str(t): slug[t] for t in tids}
    stage_agg = collections.defaultdict(Agg)
    vendor_agg = collections.defaultdict(Agg)
    tenant_b = collections.defaultdict(lambda: collections.defaultdict(float))
    tenant_calls = collections.Counter()
    kind_usd = collections.defaultdict(float)
    v_usd, v_calls = collections.defaultdict(float), collections.Counter()
    p_usd, p_calls = collections.defaultdict(float), collections.Counter()
    noreq_usd, noreq_n = collections.defaultdict(float), collections.Counter()
    t7_jobs = set()
    un = collections.defaultdict(float)
    exp = Agg()
    gap = Agg()
    other = collections.defaultdict(Agg)
    total = Agg()
    for r in rows:
        if r["is_experiment"]:
            exp.add(r)
            continue
        ten = str(r["tenant_id"]) if r["tenant_id"] else job_tenant(r["job_id"])
        s = tslug.get(ten, "unknown")
        b = bucket(r["stage"])
        u = f(r["cost_usd"])
        if r["gap"]:
            gap.add(r)
        if b == "other":
            other[r["stage"]].add(r)
            continue
        total.add(r)
        stage_agg[(r["stage"], r["role"])].add(r)
        vendor_agg[(r["connection_key"] or "-", r["model"])].add(r)
        tenant_b[s][b] += u
        tenant_calls[s] += 1
        j = job.get(r["job_id"])
        kind_usd[j["kind"] if j else "-"] += u
        if b == "t2":
            vid = resolve(r["job_id"], job_to_version)
            if vid:
                v_usd[vid] += u
                v_calls[vid] += 1
            else:
                un["t2"] += u
        elif b == "piece":
            pid = r["content_piece_id"] if r["content_piece_id"] in pby else None
            pid = pid or resolve(r["job_id"], job_to_piece) or req_to_piece.get(r["angle_gate_request_id"])
            if pid:
                p_usd[pid] += u
                p_calls[pid] += 1
            elif r["angle_gate_request_id"]:
                ch = req_channel.get(r["angle_gate_request_id"], "-")
                noreq_usd[ch] += u
                noreq_n[r["angle_gate_request_id"]] += 1
            else:
                un["piece"] += u
        elif b == "t7":
            if r["job_id"]:
                t7_jobs.add(r["job_id"])
        else:
            un["chain_other"] += u

    # DFS
    dfs_agg = collections.defaultdict(lambda: [0, 0, 0, 0.0, collections.Counter()])
    dfs_tenant = collections.defaultdict(float)
    v_dfs, p_dfs = collections.defaultdict(float), collections.defaultdict(float)
    dfs_un = 0.0
    dfs_total = [0, 0, 0.0]
    for d in dfs:
        a = dfs_agg[(d["stage"], d["endpoint"])]
        u = f(d["cost_usd"])
        a[0] += 1
        a[1] += bool(d["fetched_live"])
        a[2] += bool(d["cache_hit"])
        a[3] += u
        a[4][d["status"]] += 1
        dfs_total[0] += 1
        dfs_total[1] += bool(d["fetched_live"])
        dfs_total[2] += u
        ten = str(d["tenant_id"]) if d["tenant_id"] else job_tenant(d["job_id"])
        s = tslug.get(ten, "unknown")
        dfs_tenant[s] += u
        vid = resolve(d["job_id"], job_to_version)
        pid = None if vid else resolve(d["job_id"], job_to_piece)
        if vid:
            v_dfs[vid] += u
        elif pid:
            p_dfs[pid] += u
        else:
            dfs_un += u

    print(f"TOTAL {label} window={since:%Y-%m-%dT%H:%MZ}..{until:%Y-%m-%dT%H:%MZ} chain {total.line()} "
          f"gap_calls={gap.calls} gap_usd={gap.usd:.4f} other_usd={sum(a.usd for a in other.values()):.4f} "
          f"dfs_calls={dfs_total[0]} dfs_live={dfs_total[1]} dfs_usd={dfs_total[2]:.4f} "
          f"chain_plus_dfs_usd={total.usd + dfs_total[2]:.4f}")
    for (st, role), a in sorted(stage_agg.items(), key=lambda kv: -kv[1].usd):
        share = div(a.usd, total.usd)
        print(f"STAGE {label} stage={st} role={role} {a.line()} share_pct={round(100 * share, 1) if share else 0}")
    for (conn, model), a in sorted(vendor_agg.items(), key=lambda kv: -kv[1].usd):
        print(f"VENDOR {label} conn={conn} model={model} calls={a.calls} usd={a.usd:.4f} not_ok={a.not_ok}")
    for s in sorted(tenant_b):
        tb = tenant_b[s]
        print(f"TENANT {label} {s} calls={tenant_calls[s]} usd={sum(tb.values()):.4f} t2={tb['t2']:.4f} "
              f"t7={tb['t7']:.4f} piece={tb['piece']:.4f} chain_other={tb['chain_other']:.4f} dfs={dfs_tenant[s]:.4f}")
    kind_jobs = collections.defaultdict(lambda: [0, 0.0, collections.Counter()])
    for j in jobs:
        k = kind_jobs[j["kind"]]
        k[0] += 1
        k[1] += f(j["cost_usd"])
        k[2][j["status"]] += 1
    for k in sorted(set(kind_jobs) | set(kind_usd)):
        kj = kind_jobs.get(k, [0, 0.0, {}])
        print(f"KIND {label} kind={k} jobs={kj[0]} statuses={dict(kj[2])} ledger_usd={kind_usd.get(k, 0):.4f} "
              f"job_cost_usd={kj[1]:.4f}")
    for (st, ep), a in sorted(dfs_agg.items(), key=lambda kv: -kv[1][3]):
        print(f"DFS {label} stage={st} endpoint={ep} calls={a[0]} live={a[1]} cache_hit={a[2]} usd={a[3]:.4f} "
              f"statuses={dict(a[4])}")
    for s in sorted(dfs_tenant):
        print(f"DFS_TENANT {label} {s} usd={dfs_tenant[s]:.4f}")

    # ---- T2 unit
    vstat = collections.Counter(f"{v['status']}/{v['qa_status']}" for v in versions)
    delivered = [v for v in versions if v["status"] not in ("pending", "failed")]
    t2_attr = sum(v_usd.values())
    t2_dfs = sum(v_dfs.values())
    per_v = [v_usd.get(v["id"], 0.0) for v in delivered]
    pairs = {(v["tenant_id"], v["published_tour_id"]) for v in versions}
    vs_per_pair = collections.Counter(collections.Counter((v["tenant_id"], v["published_tour_id"]) for v in versions).values())
    u_t2 = div(t2_attr, len(delivered))
    print(f"UNIT_T2 {label} versions={len(versions)} delivered={len(delivered)} by_status={dict(vstat)} "
          f"edit_source={dict(collections.Counter(v['edit_source'] for v in versions))} pairs={len(pairs)} "
          f"versions_per_pair={dict(vs_per_pair)} attributed_usd={t2_attr:.4f} unattributed_t2_usd={un['t2']:.4f} "
          f"usd_per_delivered_version={r4(u_t2)} usd_per_pair={r4(div(t2_attr, len(pairs)))} "
          f"min={r4(min(per_v) if per_v else None)} median={r4(statistics.median(per_v) if per_v else None)} "
          f"max={r4(max(per_v) if per_v else None)} calls_per_version={r4(div(sum(v_calls.values()), len(versions)))} "
          f"dfs_usd={t2_dfs:.4f} dfs_per_version={r4(div(t2_dfs, len(delivered)))}")
    for vid in sorted(v_usd, key=lambda k: -v_usd[k])[:5]:
        v = vby[vid]
        print(f"T2_TOP {label} v={str(vid)[:8]} tenant={tslug.get(str(v['tenant_id']))} "
              f"tour={str(v['published_tour_id'])[:8]} n={v['version_number']} st={v['status']}/{v['qa_status']} "
              f"calls={v_calls[vid]} usd={v_usd[vid]:.4f}")

    # ---- piece units
    by_cs = collections.defaultdict(lambda: [0, 0.0, 0.0])
    for p in pieces:
        k = by_cs[(p["channel"] or "-", p["status"])]
        k[0] += 1
        k[1] += p_usd.get(p["piece_id"], 0.0)
        k[2] += p_dfs.get(p["piece_id"], 0.0)
    for (ch, st), k in sorted(by_cs.items()):
        print(f"UNIT_PIECE {label} channel={ch} status={st} pieces={k[0]} usd={k[1]:.4f} usd_per_piece={r4(div(k[1], k[0]))} "
              f"dfs_usd={k[2]:.4f}")
    piece_usd = sum(p_usd.values())
    t7_usd = sum(tenant_b[s]["t7"] for s in tenant_b)
    noreq_total = sum(noreq_usd.values())
    st = collections.Counter(p["status"] for p in pieces)
    blog = [p for p in pieces if p["channel"] == "blog"]
    bst = collections.Counter(p["status"] for p in blog)
    blog_usd = sum(p_usd.get(p["piece_id"], 0.0) for p in blog)
    held_usd = sum(p_usd.get(p["piece_id"], 0.0) for p in pieces if p["status"] == "held")
    appr, held = st.get("approved", 0), st.get("held", 0)
    loaded = piece_usd + t7_usd + noreq_total
    print(f"UNIT_BLOG {label} blog_pieces={len(blog)} by_status={dict(bst)} blog_usd={blog_usd:.4f} "
          f"usd_per_blog={r4(div(blog_usd, len(blog)))} usd_per_approved_blog={r4(div(blog_usd, bst.get('approved', 0)))} "
          f"usd_per_delivered_blog={r4(div(blog_usd, bst.get('approved', 0) + bst.get('held', 0)))}")
    print(f"UNIT_ALL {label} pieces={len(pieces)} by_status={dict(st)} piece_usd={piece_usd:.4f} t7_overhead_usd={t7_usd:.4f} "
          f"t7_jobs={len(t7_jobs)} no_piece_request_usd={noreq_total:.4f} loaded_usd={loaded:.4f} "
          f"usd_per_piece={r4(div(piece_usd, len(pieces)))} usd_per_approved={r4(div(piece_usd, appr))} "
          f"loaded_per_piece={r4(div(loaded, len(pieces)))} loaded_per_approved={r4(div(loaded, appr))} "
          f"loaded_per_delivered={r4(div(loaded, appr + held))} "
          f"discarded_attempts={sum(p['n_disc'] for p in pieces)}")
    held_share = div(held_usd, piece_usd)
    print(f"HELD_SHARE {label} held_pieces={held} held_usd={held_usd:.4f} piece_usd={piece_usd:.4f} "
          f"held_share_pct={round(100 * held_share, 1) if held_share is not None else None} "
          f"held_piece_share_pct={round(100 * div(held, len(pieces)), 1) if pieces else None} "
          f"failed_usd={sum(p_usd.get(p['piece_id'], 0.0) for p in pieces if p['status'] == 'failed'):.4f}")
    hh = collections.defaultdict(lambda: [0, 0.0])
    for p in pieces:
        if p["status"] == "held":
            hh[p["hr_head"] or "-"][0] += 1
            hh[p["hr_head"] or "-"][1] += p_usd.get(p["piece_id"], 0.0)
    for h, (n, u) in sorted(hh.items(), key=lambda kv: -kv[1][1]):
        print(f"HELD_HEAD {label} head={h} pieces={n} usd={u:.4f}")
    gate_sets = {}
    if want_gates and held:
        try:
            from services.acp_content_writing.gate_eval import failing_gates  # noqa: E402
            held_ids = [p["piece_id"] for p in pieces if p["status"] == "held"]
            gs = collections.defaultdict(lambda: [0, 0.0, 0])
            for g in await c.fetch("SELECT piece_id, gate_ledger FROM acp_shared.content_piece "
                                   "WHERE piece_id = ANY($1::uuid[])", held_ids):
                led = g["gate_ledger"]
                led = json.loads(led) if isinstance(led, str) else led
                key = ",".join(sorted({x["source"] for x in failing_gates(led) if x["may_hold"]})) or "-"
                gs[key][0] += 1
                gs[key][1] += p_usd.get(g["piece_id"], 0.0)
                gs[key][2] += p_calls.get(g["piece_id"], 0)
                del led
            for k, (n, u, cl) in sorted(gs.items(), key=lambda kv: -kv[1][1]):
                print(f"HELD_GATESET {label} gates={k} pieces={n} usd={u:.4f} calls={cl} usd_per_piece={r4(div(u, n))}")
                gate_sets[k] = {"pieces": n, "usd": round(u, 4)}
        except Exception as e:  # noqa: BLE001 - report and keep the rest of the output
            print(f"WARN {label} gate sets skipped: {type(e).__name__}")
    noreq_by_ch = {k: round(v, 4) for k, v in noreq_usd.items()}
    print(f"WASTE {label} not_ok_calls={total.not_ok} not_ok_usd={total.not_ok_usd:.4f} max_tokens={total.max_tok} "
          f"no_piece_requests={len(noreq_n)} no_piece_usd={noreq_total:.4f} by_channel={noreq_by_ch} "
          f"unattributed_piece_usd={un['piece']:.4f} "
          f"unattributed_chain_other_usd={un['chain_other']:.4f} dfs_unattributed_usd={dfs_un:.4f}")
    print(f"EXPERIMENT {label} {exp.line()} (kept out of every number above)")
    for stg, a in sorted(other.items(), key=lambda kv: -kv[1].usd):
        print(f"OTHER_STAGE {label} stage={stg} calls={a.calls} usd={a.usd:.4f} (not charged to AA-741)")

    by_stage = {}
    for (stg, _role), a in stage_agg.items():
        d = by_stage.setdefault(stg, {"calls": 0, "usd": 0.0, "tok_in": 0, "tok_out": 0, "not_ok": 0, "max_tokens": 0})
        d["calls"] += a.calls
        d["usd"] = round(d["usd"] + a.usd, 4)
        d["tok_in"] += a.tin
        d["tok_out"] += a.tout
        d["not_ok"] += a.not_ok
        d["max_tokens"] += a.max_tok
    return {
        "window": [since.isoformat(), until.isoformat()],
        "chain_usd": round(total.usd, 4), "chain_calls": total.calls, "dfs_usd": round(dfs_total[2], 4),
        "dfs_calls": dfs_total[0], "experiment_usd": round(exp.usd, 4), "gap_usd": round(gap.usd, 4),
        "stage": by_stage,
        "tenant": {s: {k: round(v, 4) for k, v in tenant_b[s].items()} for s in tenant_b},
        "t2": {"versions": len(versions), "delivered": len(delivered), "usd": round(t2_attr, 4),
               "usd_per_version": r4(u_t2), "unattributed_usd": round(un["t2"], 4)},
        "pieces": {"n": len(pieces), "by_status": dict(st), "usd": round(piece_usd, 4),
                   "usd_per_piece": r4(div(piece_usd, len(pieces))), "usd_per_approved": r4(div(piece_usd, appr)),
                   "loaded_per_approved": r4(div(loaded, appr)), "t7_usd": round(t7_usd, 4),
                   "no_piece_usd": round(noreq_total, 4)},
        "blog": {"n": len(blog), "by_status": dict(bst), "usd": round(blog_usd, 4),
                 "usd_per_blog": r4(div(blog_usd, len(blog))),
                 "usd_per_approved_blog": r4(div(blog_usd, bst.get("approved", 0)))},
        "held": {"pieces": held, "usd": round(held_usd, 4),
                 "share_pct": round(100 * held_share, 1) if held_share is not None else None, "gate_sets": gate_sets},
        "waste": {"not_ok_usd": round(total.not_ok_usd, 4), "max_tokens": total.max_tok},
    }


async def main() -> None:
    if not os.environ.get("P2_SINCE"):
        print("STOP P2_SINCE (phase 2 start, ISO) is required")
        return
    now = datetime.now(timezone.utc)
    p2s = iso(os.environ["P2_SINCE"])
    p2u = iso(os.environ["P2_UNTIL"]) if os.environ.get("P2_UNTIL") else now
    p1s = iso(os.environ.get("P1_SINCE", "2026-11-05T23:44:00Z"))
    p1u = iso(os.environ.get("P1_UNTIL", "2026-11-07T00:00:00Z"))
    p1_readme = float(os.environ.get("P1_README_USD", "3.6671"))
    phase01 = float(os.environ.get("PHASE01", "6.5594"))
    exclude8 = {x.strip().lower()[:8] for x in os.environ.get("EXCLUDE8", "d67e3178").split(",") if x.strip()}
    cap = float(os.environ.get("GROWTH_CAP", "40"))
    plan_t2 = int(os.environ.get("GROWTH_T2", "200"))
    max_rows = int(os.environ.get("MAX_ROWS", "100000"))
    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        await c.execute("SET default_transaction_read_only = on")
        await c.execute("SET statement_timeout = '90s'")
        ten = await c.fetch("SELECT tenant_id, slug, created_at FROM shared.tenants WHERE slug = ANY($1::text[]) "
                            "ORDER BY slug", AUDIT)
        tids = [t["tenant_id"] for t in ten]
        slug = {t["tenant_id"]: t["slug"] for t in ten}
        print(f"TENANTS n={len(ten)} {[(t['slug'], str(t['tenant_id'])[:8]) for t in ten]} exclude8={sorted(exclude8)}")
        if len(ten) != 4:
            print("WARN expected 4 audit tenants")
        p2 = await window(c, "P2", tids, slug, p2s, p2u, max_rows, exclude8, True)
        p1 = await window(c, "P1", tids, slug, p1s, p1u, max_rows, exclude8, False)

        # ---- phase 1 vs phase 2
        for st in sorted(set(p1["stage"]) | set(p2["stage"])):
            a, b = p1["stage"].get(st), p2["stage"].get(st)

            def pc(x):
                return r4(div(x["usd"], x["calls"])) if x else None

            def po(x):
                return round(div(x["tok_out"], x["calls"]) or 0) if x else None
            ch = None if not (a and b and pc(a)) else round(100 * (pc(b) - pc(a)) / pc(a), 1)
            print(f"COMPARE_STAGE stage={st} p1_calls={a['calls'] if a else 0} p1_usd={a['usd'] if a else 0} "
                  f"p1_usd_per_call={pc(a)} p1_avg_out={po(a)} p2_calls={b['calls'] if b else 0} "
                  f"p2_usd={b['usd'] if b else 0} p2_usd_per_call={pc(b)} p2_avg_out={po(b)} usd_per_call_change_pct={ch}")
        for k, a, b in (("usd_per_t2_version", p1["t2"]["usd_per_version"], p2["t2"]["usd_per_version"]),
                        ("usd_per_blog", p1["blog"]["usd_per_blog"], p2["blog"]["usd_per_blog"]),
                        ("usd_per_approved_blog", p1["blog"]["usd_per_approved_blog"], p2["blog"]["usd_per_approved_blog"]),
                        ("usd_per_piece_all_channels", p1["pieces"]["usd_per_piece"], p2["pieces"]["usd_per_piece"]),
                        ("loaded_per_approved_piece", p1["pieces"]["loaded_per_approved"], p2["pieces"]["loaded_per_approved"]),
                        ("held_share_pct", p1["held"]["share_pct"], p2["held"]["share_pct"])):
            print(f"COMPARE_UNIT {k} p1={a} p2={b}")

        # ---- per day (to check the window bounds) and reconciliation
        first = min(t["created_at"] for t in ten) if ten else p1s
        for r in await c.fetch(
                "SELECT date_trunc('day', l.created_at) AS d, count(*) AS n, coalesce(sum(l.cost_usd), 0) AS usd, "
                "count(*) FILTER (WHERE l.is_experiment) AS n_exp, "
                "coalesce(sum(l.cost_usd) FILTER (WHERE l.is_experiment), 0) AS usd_exp "
                "FROM shared.llm_call_log l WHERE l.tenant_id = ANY($1::uuid[]) AND l.created_at >= $2 "
                "AND l.is_shadow IS NOT TRUE AND l.stage ~ $3 GROUP BY 1 ORDER BY 1",
                tids, first, CHAIN.pattern):
            print(f"DAY {r['d']:%Y-%m-%d} chain_calls={r['n']} chain_usd={f(r['usd']):.4f} "
                  f"experiment_calls={r['n_exp']} experiment_usd={f(r['usd_exp']):.4f}")
        pre = await c.fetchrow(
            "SELECT count(*) AS n, coalesce(sum(l.cost_usd), 0) AS usd, "
            "coalesce(sum(l.cost_usd) FILTER (WHERE l.stage ~ $4), 0) AS chain FROM shared.llm_call_log l "
            "WHERE l.tenant_id = ANY($1::uuid[]) AND l.created_at >= $2 AND l.created_at < $3 AND l.is_shadow IS NOT TRUE",
            tids, first, p2s, CHAIN.pattern)
        print(f"RECON pre_phase2 from={first:%Y-%m-%dT%H:%MZ} all_stage_usd={f(pre['usd']):.4f} "
              f"chain_usd={f(pre['chain']):.4f} phase01_used_by_p2_spend={phase01} "
              f"p1_window_chain_usd={p1['chain_usd']} p1_readme_usd={p1_readme} "
              f"p1_window_minus_readme={round(p1['chain_usd'] - p1_readme, 4)} "
              f"p2_chain_usd={p2['chain_usd']} aa741_total_ledger={round(f(pre['usd']) + p2['chain_usd'], 4)}/20")

        # ---- Growth plan headroom from the phase 2 units
        u_t2, u_blog = p2["t2"]["usd_per_version"], p2["blog"]["usd_per_blog"]
        t2_month = None if u_t2 is None else round(u_t2 * plan_t2, 2)
        print(f"PROJECTION growth_cap={cap} plan_t2_per_month={plan_t2} usd_per_t2={u_t2} t2_month_usd={t2_month} "
              f"t2_share_of_cap_pct={None if t2_month is None else round(100 * t2_month / cap, 1)} "
              f"blogs_left_after_full_t2={None if (t2_month is None or not u_blog) else int(max(cap - t2_month, 0) / u_blog)} "
              f"blogs_for_cap_alone={None if not u_blog else int(cap / u_blog)} "
              f"approved_blogs_for_cap_alone={None if not p2['blog']['usd_per_approved_blog'] else int(cap / p2['blog']['usd_per_approved_blog'])}")
        print("JSON_SUMMARY " + json.dumps({"p2": p2, "p1": p1, "t2_month_usd": t2_month}, default=str,
                                           separators=(",", ":")))
    finally:
        await c.close()


asyncio.run(main())
