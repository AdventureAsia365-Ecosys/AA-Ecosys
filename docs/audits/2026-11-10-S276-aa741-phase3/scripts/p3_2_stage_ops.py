"""AA-741 phase 3, slice 2 (S276): per-stage reconciliation + ops for the 4 audit tenants. READ-ONLY, $0, no write.

Feeds the phase 3 report sections "Reconciliation" (expected vs got per T stage, terminal states), "Per stage" and
"Ops" (jobs per kind/status, durations p50/p90, failures by error class, retries, LLM call health per stage) and the
t2_flag_fix finding (4 of 6 calls ended on max_tokens in phase 2: what those calls were asked to do, their params).

Run by the orchestrator in the CIS api container (DATABASE_URL = cis_app):
    tools/ecs/ecsx.sh docs/audits/2026-11-10-S276-aa741-phase3/scripts/p3_2_stage_ops.py P2_SINCE=2026-11-10T05:49:46Z

Env:
  P2_SINCE      phase 2 start, ISO (required). Window = [P2_SINCE, P2_UNTIL).
  P2_UNTIL      window end, ISO (default: now).
  TOURS8        the 12 phase 2 published_tours.id prefixes, comma-separated (default: the S275 pick list).
  FLAGFIX_DAYS  look-back for the cross-tenant t2_flag_fix / s1_flag_fix comparison (default 30).

Prints counts, 8-char ids, enums, lengths and aggregates only: never tour, piece, prompt or error TEXT (job errors are
reduced to a class name), no e-mail, no secret. Synthetic test pieces (a `*_test` key in content_piece.flags, the
S238 rule) are excluded and counted on the TEST_EXCLUDED line.

Line prefixes (one record per line, then one JSON line `SUMMARY_JSON {...}` for the report):
  TENANT  T0_BRAND  T0_MARKETS  T5_TOUR  T5_SEG  PAIR  FUNNEL
  JOB  JOB_KIND  JOB_ERR  JOB_LLM  JOB_RESULT
  LLM_STAGE  LLM_HEALTH  LLM_NOJOB
  T7_SUBJECTS  T8_REQ  T8_OPTIONS  T9_PIECES  T9_SHAPE  T10_HOLD  EXPORT  TERMINAL
  FLAGFIX_PARAMS  FLAGFIX_CATALOG  FLAGFIX_CALL  FLAGFIX_JOB  FLAGFIX_30D
"""
import asyncio
import collections
import json
import os
import re
import sys
from datetime import datetime, timezone

import asyncpg

sys.path.insert(0, "/app")

AUDIT = ["audit-atlas-hearth", "audit-terra-family", "audit-trail-pulse", "audit-wildkind-travel"]
DEFAULT_TOURS8 = ("8602c1d4,2cf487be,84e392c3,caf4bf16,ac574bfe,56b61f58,"
                  "207e4efa,2d0ee81a,c9716429,a8560125,7fe02d1a,b56704c5")
T_KINDS = ["t2_rewrite", "t7_slate", "t8_angles", "t9_write"]
STAGE_OF_KIND = {"t2_rewrite": "T2+T3 rewrite/QA", "t7_slate": "T7 slate", "t8_angles": "T8 angle",
                 "t9_write": "T9 write + T10 gates"}
CHAIN = r"^(t[0-9]+_|f10_embed$)"
TENANT_OF_JOB = "coalesce(j.payload->>'tenant_id', j.payload->'context'->>'tenant_id')"
TEST_FLAG = r'"[a-z0-9_]*_test"\s*:'
EXPORT_PIECE = "content_piece.exported"
EXPORT_TTV = "tenant_tour_version.exported"
ENUM_RE = re.compile(r"^[A-Za-z0-9_.:/\-]{1,40}$")
UUIDISH = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-")
KEY_RE = re.compile(r"^(?:[a-z][a-z0-9_]{0,47}|[A-Z]{2,3})$")

# Job error -> class. Order matters; only the class is printed, never the message.
ERR_CLASSES = [
    ("approval_wait", r"approval"),
    ("stage_disabled", r"stage[_ ]disabled|kill[_ ]switch|stage is off"),
    ("budget", r"budget"),
    ("deadline_timeout", r"timeout|timed out|deadline"),
    ("lease_reaped", r"lease|reap"),
    ("not_found", r"not found"),
    ("bad_payload", r"payload needs"),
    ("truncated_max_tokens", r"max_tokens|truncat"),
    ("parse_json", r"json|parse|decod"),
    ("throttled_429", r"throttl|rate.?limit|\b429\b|too many requests"),
    ("provider_5xx", r"\b50[0-9]\b|overloaded|service unavailable|bad gateway"),
    ("access_denied", r"access.?denied|forbidden|\b403\b|credential"),
    ("db_error", r"asyncpg|postgres|deadlock|violates|constraint"),
    ("cancelled", r"cancel"),
]


def err_class(msg):
    if not msg:
        return "-"
    low = msg.lower()
    for name, pat in ERR_CLASSES:
        if re.search(pat, low):
            return name
    m = re.match(r"^\s*([A-Z][A-Za-z0-9_]*(?:Error|Exception|Retryable|Timeout))\b", msg)
    return m.group(1) if m else "other"


def f(x, nd=2):
    if x is None:
        return None
    return round(float(x), nd)


def p8(x):
    return str(x)[:8] if x is not None else "-"


def iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def flatten(obj, prefix="", depth=0, out=None):
    """Scalar leaves of a job.result: bools, numbers, enum-like short strings; lists -> '<key>[]' = length.
    Keys ending in _id / text-bearing strings are dropped (no tour/piece text ever leaves the container)."""
    out = {} if out is None else out
    if not isinstance(obj, dict):
        return out
    for k, v in obj.items():
        k = str(k)
        key = f"{prefix}{k}"
        # code keys only: a dict keyed by data (a place, a keyword, a sentence) never leaves the container
        if k.endswith("_id") or k.endswith("_ids") or not KEY_RE.match(k):
            continue
        if isinstance(v, bool) or isinstance(v, (int, float)):
            out[key] = v
        elif isinstance(v, str):
            if ENUM_RE.match(v) and not UUIDISH.match(v):
                out[key] = v
        elif isinstance(v, list):
            out[key + "[]"] = len(v)
        elif isinstance(v, dict) and depth < 1:
            flatten(v, key + ".", depth + 1, out)
        elif v is None:
            out[key] = None
    return out


def agg_results(rows):
    """{key: summary} over many flattened results."""
    vals = collections.defaultdict(list)
    for r in rows:
        for k, v in r.items():
            vals[k].append(v)
    out = {}
    for k, vs in sorted(vals.items()):
        vs2 = [v for v in vs if v is not None]
        if not vs2:
            out[k] = {"n": len(vs), "all_null": True}
        elif all(isinstance(v, bool) for v in vs2):
            out[k] = {"n": len(vs2), "true": sum(1 for v in vs2 if v)}
        elif all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vs2):
            s = sorted(float(v) for v in vs2)
            out[k] = {"n": len(s), "mean": round(sum(s) / len(s), 3), "p50": s[len(s) // 2], "max": s[-1]}
        else:
            out[k] = {"n": len(vs2), "values": dict(collections.Counter(str(v) for v in vs2).most_common(6))}
    return out


async def main() -> None:
    if not os.environ.get("P2_SINCE"):
        print("STOP P2_SINCE (phase 2 start, ISO) is required")
        return
    since = iso(os.environ["P2_SINCE"])
    until = iso(os.environ["P2_UNTIL"]) if os.environ.get("P2_UNTIL") else datetime.now(timezone.utc)
    tours8 = [t.strip().lower()[:8] for t in os.environ.get("TOURS8", DEFAULT_TOURS8).split(",") if t.strip()]
    ff_days = int(os.environ.get("FLAGFIX_DAYS", "30"))
    summary = {"window": [since.isoformat(), until.isoformat()], "tours": len(tours8)}

    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        await c.execute("SET default_transaction_read_only = on")
        await c.execute("SET statement_timeout = '90s'")

        # ---------------------------------------------------------------- tenants + T0 brand
        ten = await c.fetch("SELECT tenant_id, slug, kind, account_status, is_active FROM shared.tenants "
                            "WHERE slug = ANY($1::text[]) ORDER BY slug", AUDIT)
        tids = [t["tenant_id"] for t in ten]
        tids_s = [str(t) for t in tids]
        slug = {t["tenant_id"]: t["slug"] for t in ten}
        slug_s = {str(k): v for k, v in slug.items()}
        for t in ten:
            print(f"TENANT {t['slug']} id={p8(t['tenant_id'])} kind={t['kind']} status={t['account_status']} "
                  f"active={t['is_active']}")
        if len(ten) != 4:
            print(f"WARN audit tenants found={len(ten)}/4")

        t0 = {}
        for t in ten:
            b = await c.fetchrow(
                "SELECT version, brand_name IS NOT NULL AND brand_name <> '' AS has_name, "
                "length(coalesce(system_prompt,'')) AS sp_len, length(coalesce(style_guide,'')) AS sg_len, "
                "CASE WHEN jsonb_typeof(forbidden_words) = 'array' THEN jsonb_array_length(forbidden_words) END AS fw, "
                "CASE WHEN jsonb_typeof(voice_examples) = 'array' THEN jsonb_array_length(voice_examples) END AS ve, "
                "length(coalesce(core_idea,'')) AS ci_len, length(coalesce(good_examples,'')) AS ge_len, "
                "length(coalesce(default_cta,'')) AS cta_len, target_markets, rewrite_language, "
                "source_docx_s3_key IS NOT NULL AS has_docx, updated_at "
                "FROM shared.tenant_brand_rules WHERE tenant_id = $1 AND is_active ORDER BY version DESC LIMIT 1",
                t["tenant_id"])
            nact = await c.fetchval("SELECT count(*) FROM shared.tenant_brand_rules WHERE tenant_id = $1 AND is_active",
                                    t["tenant_id"])
            nver = await c.fetchval("SELECT count(*) FROM shared.tenant_brand_rules WHERE tenant_id = $1",
                                    t["tenant_id"])
            if b:
                print(f"T0_BRAND {t['slug']} expected=1_active got_active={nact} versions={nver} v={b['version']} "
                      f"name={b['has_name']} system_prompt_len={b['sp_len']} style_guide_len={b['sg_len']} "
                      f"forbidden={b['fw']} voice_examples={b['ve']} core_idea_len={b['ci_len']} "
                      f"good_examples_len={b['ge_len']} cta_len={b['cta_len']} markets={list(b['target_markets'] or [])} "
                      f"lang={b['rewrite_language']} docx={b['has_docx']} updated={b['updated_at']:%Y-%m-%dT%H:%MZ}")
            else:
                print(f"T0_BRAND {t['slug']} expected=1_active got_active=0 versions={nver}")
            cfg = await c.fetchrow("SELECT markets, channels FROM acp_shared.tenant_config WHERE tenant_id = $1",
                                   t["tenant_id"])
            seo = await c.fetchrow("SELECT seo_provider::text AS prov, target_market FROM shared.tenant_seo_config "
                                   "WHERE tenant_id = $1", t["tenant_id"])
            tm = seo["target_market"] if seo else None
            tm = json.loads(tm) if isinstance(tm, str) else tm
            print(f"T0_MARKETS {t['slug']} tenant_config.markets={list(cfg['markets']) if cfg else None} "
                  f"channels={len(cfg['channels']) if cfg else None} seo_provider={seo['prov'] if seo else None} "
                  f"seo_target_market={json.dumps(tm)[:120] if tm is not None else None}")
            t0[t["slug"]] = {"active": nact, "system_prompt_len": b["sp_len"] if b else None,
                             "markets": list(cfg["markets"]) if cfg else None,
                             "brand_markets": list(b["target_markets"] or []) if b else []}
        summary["t0"] = t0

        # ---------------------------------------------------------------- tours, T5 atoms + segments (platform)
        pts = await c.fetch("SELECT id, tour_id FROM gold_aa_internal.published_tours "
                            "WHERE left(id::text, 8) = ANY($1::text[])", tours8)
        byp = collections.defaultdict(list)
        for r in pts:
            byp[str(r["id"])[:8]].append(r)
        tours = []
        for x in tours8:
            if len(byp.get(x, [])) != 1:
                print(f"WARN tour={x} matches={len(byp.get(x, []))}")
                continue
            tours.append((x, byp[x][0]["id"], byp[x][0]["tour_id"]))
        raw_ids = [t[2] for t in tours]

        atoms = {r["tour_id"]: r["n"] for r in await c.fetch(
            "SELECT tour_id, count(*) AS n FROM acp_contract.v_active_tour_atoms WHERE tour_id = ANY($1::uuid[]) "
            "GROUP BY 1", raw_ids)}
        seg_rows = await c.fetch(
            "SELECT tour_id, market, count(DISTINCT segment_id) AS segs, "
            "count(DISTINCT segment_id) FILTER (WHERE coalesce(demand_volume,0) >= 1000 AND questions >= 3) AS blog_bar, "
            "max(demand_volume) AS max_demand, max(questions) AS max_q "
            "FROM acp_contract.atom_ranking WHERE tour_id = ANY($1::uuid[]) AND superseded_at IS NULL "
            "AND excluded_reason IS NULL GROUP BY 1, 2 ORDER BY 1, 2", raw_ids)
        seg_by_tour = collections.defaultdict(dict)
        for r in seg_rows:
            seg_by_tour[r["tour_id"]][r["market"]] = r
        t5_ok = 0
        for x, _pub, raw in tours:
            n = atoms.get(raw, 0)
            t5_ok += n > 0
            mk = seg_by_tour.get(raw, {})
            print(f"T5_TOUR tour={x} active_atoms={n} markets_ranked={sorted(mk)} "
                  f"segs_max={max((m['segs'] for m in mk.values()), default=0)}")
            for m, r in sorted(mk.items()):
                print(f"T5_SEG tour={x} market={m} segs={r['segs']} blog_bar_segs={r['blog_bar']} "
                      f"max_demand={r['max_demand']} max_questions={r['max_q']}")
        summary["t5"] = {"tours_with_atoms": t5_ok, "expected": len(tours)}

        # ---------------------------------------------------------------- per pair funnel (tenant x tour)
        win = (since, until)
        ver_rows = await c.fetch(
            "SELECT DISTINCT ON (v.tenant_id, v.published_tour_id) v.tenant_id, v.published_tour_id, v.status, "
            "v.qa_status, v.qa_repair_count, v.qa_auto_passed, v.edit_source, v.created_at >= $3 AS in_window, "
            "j.status AS jst, j.attempt AS jatt, extract(epoch FROM j.finished_at - j.started_at) AS run_s "
            "FROM gold_aa_internal.tenant_tour_versions v LEFT JOIN shared.job j ON j.id = v.job_id "
            "WHERE v.tenant_id = ANY($1::uuid[]) AND v.published_tour_id = ANY($2::uuid[]) "
            "ORDER BY v.tenant_id, v.published_tour_id, v.version_number DESC",
            tids, [t[1] for t in tours], since)
        latest = {(r["tenant_id"], r["published_tour_id"]): r for r in ver_rows}
        nver_win = {(r["tenant_id"], r["published_tour_id"]): r["n"] for r in await c.fetch(
            "SELECT tenant_id, published_tour_id, count(*) AS n FROM gold_aa_internal.tenant_tour_versions "
            "WHERE tenant_id = ANY($1::uuid[]) AND published_tour_id = ANY($2::uuid[]) AND created_at >= $3 "
            "AND created_at < $4 GROUP BY 1, 2", tids, [t[1] for t in tours], *win)}

        seg_cte = ("WITH seg AS (SELECT DISTINCT tour_id, segment_id FROM acp_contract.atom_ranking "
                   "WHERE tour_id = ANY($2::uuid[]) AND superseded_at IS NULL AND excluded_reason IS NULL) ")
        subj = collections.defaultdict(collections.Counter)
        for r in await c.fetch(
                seg_cte + "SELECT s.tenant_id, seg.tour_id, s.channel, s.state, count(DISTINCT s.subject_id) AS n "
                "FROM acp_shared.subject s JOIN seg ON seg.segment_id = s.segment_id "
                "WHERE s.tenant_id = ANY($1::uuid[]) GROUP BY 1, 2, 3, 4", tids, raw_ids):
            subj[(r["tenant_id"], r["tour_id"])][f"{r['channel']}:{r['state']}"] += r["n"]
        reqs = collections.defaultdict(collections.Counter)
        for r in await c.fetch(
                seg_cte + "SELECT s.tenant_id, seg.tour_id, coalesce(r.channel, s.channel) AS ch, r.status, "
                "count(DISTINCT r.request_id) AS n FROM acp_shared.subject s JOIN seg ON seg.segment_id = s.segment_id "
                "JOIN acp_shared.angle_gate_request r ON r.subject_id = s.subject_id "
                "WHERE s.tenant_id = ANY($1::uuid[]) AND r.created_at >= $3 AND r.created_at < $4 "
                "GROUP BY 1, 2, 3, 4", tids, raw_ids, *win):
            reqs[(r["tenant_id"], r["tour_id"])][f"{r['ch']}:{r['status']}"] += r["n"]
        pcs = collections.defaultdict(collections.Counter)
        exp_pairs = collections.defaultdict(int)
        for r in await c.fetch(
                seg_cte + "SELECT s.tenant_id, seg.tour_id, cp.channel, cp.status, count(DISTINCT cp.piece_id) AS n, "
                "count(DISTINCT cp.piece_id) FILTER (WHERE EXISTS (SELECT 1 FROM acp_shared.audit_log a "
                "  WHERE a.action = $5 AND a.resource_id = cp.piece_id::text AND a.created_at >= $3)) AS exported "
                "FROM acp_shared.subject s JOIN seg ON seg.segment_id = s.segment_id "
                "JOIN acp_shared.angle_gate_request r ON r.subject_id = s.subject_id "
                "JOIN acp_shared.content_piece cp ON cp.angle_gate_request_id = r.request_id "
                "WHERE s.tenant_id = ANY($1::uuid[]) AND cp.created_at >= $3 AND cp.created_at < $4 "
                f"AND coalesce(cp.flags::text, '') !~ '{TEST_FLAG}' GROUP BY 1, 2, 3, 4",
                tids, raw_ids, since, until, EXPORT_PIECE):
            pcs[(r["tenant_id"], r["tour_id"])][f"{r['channel']}:{r['status']}"] += r["n"]
            exp_pairs[(r["tenant_id"], r["tour_id"], r["channel"])] += r["exported"]
        ttv_exp = {(r["tenant_id"], r["published_tour_id"]): r["n"] for r in await c.fetch(
            "SELECT v.tenant_id, v.published_tour_id, count(*) AS n FROM acp_shared.audit_log a "
            "JOIN gold_aa_internal.tenant_tour_versions v ON a.resource_id = v.id::text "
            "WHERE a.action = $3 AND a.created_at >= $1 AND a.created_at < $2 AND v.tenant_id = ANY($4::uuid[]) "
            "GROUP BY 1, 2", since, until, EXPORT_TTV, tids)}

        # tenant markets for the blog bar (tenant_config.markets, else brand target_markets)
        tmk = {}
        for t in ten:
            mk = (t0[t["slug"]]["markets"] or t0[t["slug"]]["brand_markets"] or [])
            tmk[t["tenant_id"]] = {m.upper() for m in mk}

        funnel = {}
        for t in ten:
            tid = t["tenant_id"]
            fn = collections.Counter()
            for x, pub, raw in tours:
                v = latest.get((tid, pub))
                sj, rq, pc = subj.get((tid, raw), {}), reqs.get((tid, raw), {}), pcs.get((tid, raw), {})
                mk = seg_by_tour.get(raw, {})
                bar_any = max((m["blog_bar"] for m in mk.values()), default=0)
                bar_ten = max((m["blog_bar"] for k, m in mk.items() if str(k).upper() in tmk[tid]), default=0)
                blog_subj = sum(n for k, n in sj.items() if k.startswith("blog:"))
                blog_req = sum(n for k, n in rq.items() if k.startswith("blog:"))
                blog_pc = {k.split(":", 1)[1]: n for k, n in pc.items() if k.startswith("blog:")}
                blog_term = blog_pc.get("approved", 0) + blog_pc.get("held", 0)
                blog_exp = exp_pairs.get((tid, raw, "blog"), 0)
                v_ok = v is not None and v["status"] not in ("pending", "failed")
                pool = v is not None and v["status"] not in ("pending", "failed", "rejected")
                fn["pairs"] += 1
                fn["t2_version_in_window"] += nver_win.get((tid, pub), 0) > 0
                fn["t2_ok"] += v_ok
                fn["t3_passed"] += bool(v and v["qa_status"] == "passed")
                fn["t3_escalated"] += bool(v and v["qa_status"] == "escalated")
                fn["t4_pool"] += pool
                fn["t5_atoms"] += atoms.get(raw, 0) > 0
                fn["blog_bar_any_market"] += bar_any > 0
                fn["blog_bar_tenant_market"] += bar_ten > 0
                fn["t7_blog_subject"] += blog_subj > 0
                fn["t8_blog_request"] += blog_req > 0
                fn["t9_blog_piece"] += sum(blog_pc.values()) > 0
                fn["t10_blog_terminal"] += blog_term > 0
                fn["t10_blog_approved"] += blog_pc.get("approved", 0) > 0
                fn["export_blog_piece"] += blog_exp > 0
                fn["export_t2_docx"] += ttv_exp.get((tid, pub), 0) > 0
                print(f"PAIR tenant={t['slug']} tour={x} "
                      f"t2={(v['status'] + '/' + v['qa_status']) if v else 'none'} "
                      f"t2_repairs={v['qa_repair_count'] if v else '-'} t2_auto={v['qa_auto_passed'] if v else '-'} "
                      f"t2_job={v['jst'] if v else '-'} t2_job_attempt={v['jatt'] if v else '-'} "
                      f"t2_run_s={f(v['run_s'], 0) if v else '-'} t2_versions_in_window={nver_win.get((tid, pub), 0)} "
                      f"atoms={atoms.get(raw, 0)} blog_bar_segs_any={bar_any} blog_bar_segs_tenant_mkts={bar_ten} "
                      f"subjects={dict(sj)} requests={dict(rq)} pieces={dict(pc)} blog_exported={blog_exp} "
                      f"t2_docx_exports={ttv_exp.get((tid, pub), 0)}")
            funnel[t["slug"]] = dict(fn)
            print("FUNNEL " + t["slug"] + " " + " ".join(f"{k}={v}" for k, v in fn.items()))
        summary["funnel"] = funnel

        # ---------------------------------------------------------------- jobs: per kind x tenant x status
        jobs = await c.fetch(
            f"SELECT j.kind, {TENANT_OF_JOB} AS tid, j.status, count(*) AS n, "
            "count(*) FILTER (WHERE j.attempt > 1) AS retried, max(j.attempt) AS max_att, "
            "percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM j.finished_at - j.started_at)) AS run50, "
            "percentile_cont(0.9) WITHIN GROUP (ORDER BY extract(epoch FROM j.finished_at - j.started_at)) AS run90, "
            "max(extract(epoch FROM j.finished_at - j.started_at)) AS runmax, "
            "percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM j.started_at - j.created_at)) AS wait50, "
            "percentile_cont(0.9) WITHIN GROUP (ORDER BY extract(epoch FROM j.started_at - j.created_at)) AS wait90, "
            "coalesce(sum(j.cost_usd), 0) AS usd "
            f"FROM shared.job j WHERE j.created_at >= $1 AND j.created_at < $2 AND {TENANT_OF_JOB} = ANY($3::text[]) "
            "GROUP BY 1, 2, 3 ORDER BY 1, 2, 3", since, until, tids_s)
        for r in jobs:
            print(f"JOB kind={r['kind']} tenant={slug_s.get(r['tid'], r['tid'])} status={r['status']} n={r['n']} "
                  f"retried={r['retried']} max_attempt={r['max_att']} run_s_p50={f(r['run50'], 1)} "
                  f"run_s_p90={f(r['run90'], 1)} run_s_max={f(r['runmax'], 1)} wait_s_p50={f(r['wait50'], 1)} "
                  f"wait_s_p90={f(r['wait90'], 1)} job_cost_usd={f(r['usd'], 4)}")
        kinds = await c.fetch(
            "SELECT j.kind, count(*) AS n, count(*) FILTER (WHERE j.status = 'succeeded') AS ok, "
            "count(*) FILTER (WHERE j.status = 'failed') AS failed, "
            "count(*) FILTER (WHERE j.status IN ('queued','running')) AS open, "
            "count(*) FILTER (WHERE j.status IN ('cancelled','stopped_budget')) AS stopped, "
            "count(*) FILTER (WHERE j.attempt > 1) AS retried, "
            "count(*) FILTER (WHERE j.error IS NOT NULL AND j.status = 'succeeded') AS ok_after_error, "
            "percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM j.finished_at - j.started_at)) AS run50, "
            "percentile_cont(0.9) WITHIN GROUP (ORDER BY extract(epoch FROM j.finished_at - j.started_at)) AS run90, "
            "percentile_cont(0.5) WITHIN GROUP (ORDER BY extract(epoch FROM j.started_at - j.created_at)) AS wait50, "
            "percentile_cont(0.9) WITHIN GROUP (ORDER BY extract(epoch FROM j.started_at - j.created_at)) AS wait90 "
            f"FROM shared.job j WHERE j.created_at >= $1 AND j.created_at < $2 AND {TENANT_OF_JOB} = ANY($3::text[]) "
            "GROUP BY 1 ORDER BY 1", since, until, tids_s)
        jk = {}
        for r in kinds:
            d = {k: (f(r[k], 1) if k in ("run50", "run90", "wait50", "wait90") else r[k]) for k in r.keys() if k != "kind"}
            jk[r["kind"]] = d
            print(f"JOB_KIND kind={r['kind']} stage={STAGE_OF_KIND.get(r['kind'], 'other')} " +
                  " ".join(f"{k}={v}" for k, v in d.items()))
        summary["jobs"] = jk

        errs = collections.Counter()
        for r in await c.fetch(
                f"SELECT j.kind, j.status, j.attempt, j.error FROM shared.job j WHERE j.created_at >= $1 "
                f"AND j.created_at < $2 AND {TENANT_OF_JOB} = ANY($3::text[]) "
                "AND (j.error IS NOT NULL OR j.status IN ('failed','cancelled','stopped_budget'))",
                since, until, tids_s):
            errs[(r["kind"], r["status"], err_class(r["error"]))] += 1
        for (k, s, e), n in sorted(errs.items()):
            print(f"JOB_ERR kind={k} status={s} class={e} n={n}")
        summary["job_errors"] = [{"kind": k, "status": s, "class": e, "n": n} for (k, s, e), n in sorted(errs.items())]

        for r in await c.fetch(
                "SELECT x.kind, count(*) AS jobs, percentile_cont(0.5) WITHIN GROUP (ORDER BY x.n) AS c50, "
                "percentile_cont(0.9) WITHIN GROUP (ORDER BY x.n) AS c90, max(x.n) AS cmax, "
                "percentile_cont(0.5) WITHIN GROUP (ORDER BY x.usd) AS u50, "
                "percentile_cont(0.9) WITHIN GROUP (ORDER BY x.usd) AS u90, sum(x.usd) AS usd FROM ("
                "  SELECT j.id, j.kind, count(l.id) AS n, coalesce(sum(l.cost_usd), 0) AS usd FROM shared.job j "
                "  LEFT JOIN shared.llm_call_log l ON l.job_id = j.id AND l.is_shadow IS NOT TRUE "
                f"  WHERE j.created_at >= $1 AND j.created_at < $2 AND {TENANT_OF_JOB} = ANY($3::text[]) "
                "  GROUP BY 1, 2) x GROUP BY 1 ORDER BY 1", since, until, tids_s):
            print(f"JOB_LLM kind={r['kind']} jobs={r['jobs']} calls_p50={f(r['c50'], 1)} calls_p90={f(r['c90'], 1)} "
                  f"calls_max={r['cmax']} usd_p50={f(r['u50'], 4)} usd_p90={f(r['u90'], 4)} usd_sum={f(r['usd'], 4)}")

        for kind in T_KINDS:
            res = await c.fetch(
                f"SELECT j.result FROM shared.job j WHERE j.kind = $1 AND j.created_at >= $2 AND j.created_at < $3 "
                f"AND {TENANT_OF_JOB} = ANY($4::text[]) AND j.result IS NOT NULL", kind, since, until, tids_s)
            flat = []
            for r in res:
                v = r["result"]
                v = json.loads(v) if isinstance(v, str) else v
                flat.append(flatten(v))
            for k, s in agg_results(flat).items():
                print(f"JOB_RESULT kind={kind} key={k} {json.dumps(s, default=str)}")

        # ---------------------------------------------------------------- LLM call health per stage
        llm = await c.fetch(
            "SELECT l.stage, l.tenant_id, count(*) AS n, coalesce(sum(l.cost_usd), 0) AS usd, "
            "count(*) FILTER (WHERE coalesce(l.status, 'ok') <> 'ok') AS not_ok, "
            "count(*) FILTER (WHERE l.stop_reason = 'max_tokens') AS max_tok, "
            "count(*) FILTER (WHERE l.attempt_no > 1) AS retry_rows, "
            "count(*) FILTER (WHERE l.quality_signal ? 'truncation_retry') AS trunc_retry, "
            "count(*) FILTER (WHERE l.fallback_used) AS fallback, count(*) FILTER (WHERE l.job_id IS NULL) AS no_job, "
            "percentile_cont(0.5) WITHIN GROUP (ORDER BY l.latency_ms) AS lat50, "
            "percentile_cont(0.9) WITHIN GROUP (ORDER BY l.latency_ms) AS lat90 "
            "FROM shared.llm_call_log l WHERE l.tenant_id = ANY($1::uuid[]) AND l.created_at >= $2 "
            "AND l.created_at < $3 AND l.is_shadow IS NOT TRUE AND l.stage ~ $4 GROUP BY 1, 2 ORDER BY 1, 2",
            tids, since, until, CHAIN)
        st_tot = collections.defaultdict(collections.Counter)
        for r in llm:
            print(f"LLM_STAGE stage={r['stage']} tenant={slug.get(r['tenant_id'])} calls={r['n']} usd={f(r['usd'], 4)} "
                  f"not_ok={r['not_ok']} max_tokens={r['max_tok']} attempt_no_gt1={r['retry_rows']} "
                  f"truncation_retry={r['trunc_retry']} fallback={r['fallback']} no_job_id={r['no_job']} "
                  f"latency_ms_p50={f(r['lat50'], 0)} latency_ms_p90={f(r['lat90'], 0)}")
            for k in ("n", "not_ok", "max_tok", "retry_rows", "trunc_retry", "fallback", "no_job"):
                st_tot[r["stage"]][k] += r[k]
            st_tot[r["stage"]]["usd_x1e4"] += int(float(r["usd"]) * 10000)
        summary["llm_stage"] = {k: dict(v) for k, v in st_tot.items()}
        for r in await c.fetch(
                "SELECT l.stage, coalesce(l.status, 'null') AS st, coalesce(l.error_class, '-') AS ec, "
                "coalesce(l.stop_reason, '-') AS sr, count(*) AS n FROM shared.llm_call_log l "
                "WHERE l.tenant_id = ANY($1::uuid[]) AND l.created_at >= $2 AND l.created_at < $3 "
                "AND l.is_shadow IS NOT TRUE AND l.stage ~ $4 GROUP BY 1, 2, 3, 4 ORDER BY 1, 5 DESC",
                tids, since, until, CHAIN):
            print(f"LLM_HEALTH stage={r['stage']} status={r['st']} error_class={r['ec']} stop_reason={r['sr']} n={r['n']}")
        gap = await c.fetchrow(
            "SELECT count(*) AS n, coalesce(sum(l.cost_usd), 0) AS usd FROM shared.llm_call_log l "
            "WHERE l.tenant_id IS NULL AND l.created_at >= $1 AND l.created_at < $2 AND l.is_shadow IS NOT TRUE "
            f"AND l.job_id IN (SELECT j.id FROM shared.job j WHERE j.created_at >= $1 AND j.created_at < $2 "
            f"AND {TENANT_OF_JOB} = ANY($3::text[]))", since, until, tids_s)
        shadow = await c.fetchval(
            "SELECT count(*) FROM shared.llm_call_log l WHERE l.tenant_id = ANY($1::uuid[]) AND l.created_at >= $2 "
            "AND l.created_at < $3 AND l.is_shadow", tids, since, until)
        print(f"LLM_NOJOB tenant_null_rows_of_audit_jobs={gap['n']} usd={f(gap['usd'], 4)} shadow_rows={shadow}")

        # ---------------------------------------------------------------- T7 / T8 / T9 / T10 / export per tenant
        for r in await c.fetch(
                "SELECT s.tenant_id, s.channel, s.state, count(*) AS n, "
                "count(*) FILTER (WHERE s.created_at >= $2 AND s.created_at < $3) AS n_win, "
                "count(*) FILTER (WHERE s.segment_id IS NULL) AS route_subjects "
                "FROM acp_shared.subject s WHERE s.tenant_id = ANY($1::uuid[]) GROUP BY 1, 2, 3 ORDER BY 1, 2, 3",
                tids, since, until):
            print(f"T7_SUBJECTS tenant={slug[r['tenant_id']]} channel={r['channel']} state={r['state']} total={r['n']} "
                  f"created_in_window={r['n_win']} route_grain={r['route_subjects']}")
        for r in await c.fetch(
                "SELECT r.tenant_id, coalesce(r.channel, '-') AS ch, r.status, coalesce(r.goal, '-') AS goal, "
                "count(*) AS n, count(*) FILTER (WHERE r.subject_id IS NULL) AS no_subject, "
                "count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM acp_shared.content_piece cp "
                "  WHERE cp.angle_gate_request_id = r.request_id)) AS no_piece "
                "FROM acp_shared.angle_gate_request r WHERE r.tenant_id = ANY($1::uuid[]) AND r.created_at >= $2 "
                "AND r.created_at < $3 GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4", tids, since, until):
            print(f"T8_REQ tenant={slug[r['tenant_id']]} channel={r['ch']} status={r['status']} goal={r['goal']} "
                  f"n={r['n']} no_subject={r['no_subject']} no_piece={r['no_piece']}")
        for r in await c.fetch(
                "SELECT x.tenant_id, x.opts, x.chosen, x.recommended, count(*) AS n FROM ("
                "  SELECT r.tenant_id, r.request_id, count(o.option_id) AS opts, "
                "  count(o.option_id) FILTER (WHERE o.chosen) AS chosen, "
                "  count(o.option_id) FILTER (WHERE o.recommended) AS recommended "
                "  FROM acp_shared.angle_gate_request r LEFT JOIN acp_shared.angle_gate_option o "
                "  ON o.request_id = r.request_id WHERE r.tenant_id = ANY($1::uuid[]) AND r.created_at >= $2 "
                "  AND r.created_at < $3 GROUP BY 1, 2) x GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4", tids, since, until):
            print(f"T8_OPTIONS tenant={slug[r['tenant_id']]} options={r['opts']} chosen={r['chosen']} "
                  f"recommended={r['recommended']} requests={r['n']}")

        test_ex = await c.fetchval(
            "SELECT count(*) FROM acp_shared.content_piece cp WHERE cp.tenant_id = ANY($1::uuid[]) "
            f"AND coalesce(cp.flags::text, '') ~ '{TEST_FLAG}'", tids)
        test_ex_win = await c.fetchval(
            "SELECT count(*) FROM acp_shared.content_piece cp WHERE cp.tenant_id = ANY($1::uuid[]) "
            f"AND cp.created_at >= $2 AND cp.created_at < $3 AND coalesce(cp.flags::text, '') ~ '{TEST_FLAG}'",
            tids, since, until)
        print(f"TEST_EXCLUDED test_flagged_pieces_all_time={test_ex} in_window={test_ex_win}")
        piece_where = ("FROM acp_shared.content_piece cp WHERE cp.tenant_id = ANY($1::uuid[]) AND cp.created_at >= $2 "
                       f"AND cp.created_at < $3 AND coalesce(cp.flags::text, '') !~ '{TEST_FLAG}' ")
        t9 = {}
        for r in await c.fetch(
                "SELECT cp.tenant_id, coalesce(cp.channel, '-') AS ch, cp.status, count(*) AS n, "
                "count(*) FILTER (WHERE cp.held_reason IS NOT NULL) AS has_held_reason, "
                "count(*) FILTER (WHERE cp.job_id IS NULL) AS no_job " + piece_where +
                "GROUP BY 1, 2, 3 ORDER BY 1, 2, 3", tids, since, until):
            print(f"T9_PIECES tenant={slug[r['tenant_id']]} channel={r['ch']} status={r['status']} n={r['n']} "
                  f"held_reason_set={r['has_held_reason']} no_job_id={r['no_job']}")
            t9.setdefault(slug[r["tenant_id"]], {})[f"{r['ch']}:{r['status']}"] = r["n"]
        summary["t9_pieces"] = t9
        for r in await c.fetch(
                "SELECT cp.tenant_id, coalesce(cp.channel, '-') AS ch, count(*) AS n, "
                "avg(cp.attempt_number) AS att_avg, max(cp.attempt_number) AS att_max, "
                "avg(CASE WHEN jsonb_typeof(cp.repair_log) = 'array' THEN jsonb_array_length(cp.repair_log) END) AS rep_avg, "
                "max(CASE WHEN jsonb_typeof(cp.repair_log) = 'array' THEN jsonb_array_length(cp.repair_log) END) AS rep_max, "
                "avg(CASE WHEN jsonb_typeof(cp.discarded_attempts) = 'array' "
                "  THEN jsonb_array_length(cp.discarded_attempts) END) AS disc_avg, "
                "avg(CASE WHEN jsonb_typeof(cp.gate_ledger) = 'array' THEN jsonb_array_length(cp.gate_ledger) END) AS gates_avg, "
                "avg(length(cp.content_text)) AS chars_avg " + piece_where + "GROUP BY 1, 2 ORDER BY 1, 2",
                tids, since, until):
            print(f"T9_SHAPE tenant={slug[r['tenant_id']]} channel={r['ch']} pieces={r['n']} "
                  f"attempt_avg={f(r['att_avg'])} attempt_max={r['att_max']} repair_log_avg={f(r['rep_avg'])} "
                  f"repair_log_max={r['rep_max']} discarded_avg={f(r['disc_avg'])} ledger_entries_avg={f(r['gates_avg'])} "
                  f"chars_avg={f(r['chars_avg'], 0)}")

        try:
            from services.acp_content_writing.gate_eval import failing_gates, hold_reason_codes
        except Exception as e:  # noqa: BLE001 — the report still gets every other line
            failing_gates = hold_reason_codes = None
            print(f"WARN gate_eval import failed: {type(e).__name__}")
        if failing_gates:
            hold = collections.defaultdict(collections.Counter)
            for r in await c.fetch(
                    "SELECT cp.tenant_id, coalesce(cp.channel, '-') AS ch, cp.status, cp.held_reason, cp.gate_ledger "
                    + piece_where + "AND cp.status IN ('held', 'failed')", tids, since, until):
                led = r["gate_ledger"]
                led = json.loads(led) if isinstance(led, str) else led
                fg = failing_gates(led)
                key = (slug[r["tenant_id"]], r["ch"], r["status"])
                hold[key]["pieces"] += 1
                for g in fg:
                    if g["may_hold"]:
                        hold[key]["gate:" + g["source"]] += 1
                for code in hold_reason_codes(led, r["held_reason"]):
                    hold[key]["code:" + code] += 1
            for (s, ch, st), cnt in sorted(hold.items()):
                print(f"T10_HOLD tenant={s} channel={ch} status={st} " + " ".join(f"{k}={v}" for k, v in cnt.most_common()))
            summary["t10_hold"] = {f"{s}|{ch}|{st}": dict(cnt) for (s, ch, st), cnt in hold.items()}

        exp = {}
        for r in await c.fetch(
                "SELECT a.tenant_id, a.action, coalesce(a.details->>'channel', '-') AS ch, "
                "coalesce(a.details->>'format', '-') AS fmt, coalesce(a.details->>'mode', '-') AS mode, "
                "count(*) AS n, count(DISTINCT a.resource_id) AS distinct_objects FROM acp_shared.audit_log a "
                "WHERE a.action = ANY($4::text[]) AND a.tenant_id = ANY($1::text[]) AND a.created_at >= $2 "
                "AND a.created_at < $3 GROUP BY 1, 2, 3, 4, 5 ORDER BY 1, 2, 3, 4, 5",
                tids_s, since, until, [EXPORT_PIECE, EXPORT_TTV]):
            print(f"EXPORT tenant={slug_s.get(r['tenant_id'], r['tenant_id'])} action={r['action']} channel={r['ch']} "
                  f"format={r['fmt']} mode={r['mode']} n={r['n']} distinct_objects={r['distinct_objects']}")
            exp.setdefault(slug_s.get(r["tenant_id"], r["tenant_id"]), {})[f"{r['action']}|{r['ch']}|{r['fmt']}"] = r["n"]
        for r in await c.fetch(
                "SELECT ce.tenant_id, ce.format::text AS fmt, ce.status, count(*) AS n FROM gold_aa_internal.content_exports ce "
                "WHERE ce.tenant_id = ANY($1::uuid[]) AND ce.created_at >= $2 AND ce.created_at < $3 GROUP BY 1, 2, 3",
                tids, since, until):
            print(f"EXPORT tenant={slug[r['tenant_id']]} action=content_exports format={r['fmt']} status={r['status']} n={r['n']}")
        summary["exports"] = exp

        term = {
            "pieces_processing": await c.fetchval(
                "SELECT count(*) " + piece_where + "AND cp.status = 'processing'", tids, since, until),
            "versions_pending": await c.fetchval(
                "SELECT count(*) FROM gold_aa_internal.tenant_tour_versions WHERE tenant_id = ANY($1::uuid[]) "
                "AND created_at >= $2 AND created_at < $3 AND status = 'pending'", tids, since, until),
            "requests_pending_goal": await c.fetchval(
                "SELECT count(*) FROM acp_shared.angle_gate_request WHERE tenant_id = ANY($1::uuid[]) "
                "AND created_at >= $2 AND created_at < $3 AND status = 'pending_goal'", tids, since, until),
            "jobs_open": await c.fetchval(
                f"SELECT count(*) FROM shared.job j WHERE j.status IN ('queued','running') "
                f"AND {TENANT_OF_JOB} = ANY($1::text[])", tids_s),
        }
        print("TERMINAL " + " ".join(f"{k}={v}" for k, v in term.items()))
        summary["terminal"] = term

        # ---------------------------------------------------------------- t2_flag_fix evidence
        mk_used = await c.fetch(
            "SELECT DISTINCT model FROM shared.llm_call_log WHERE stage IN ('t2_flag_fix', 's1_flag_fix') "
            "AND created_at >= now() - make_interval(days => $1)", ff_days)
        models = sorted({r["model"] for r in mk_used})
        for r in await c.fetch(
                "SELECT stage, model_key, max_tokens, min_output_tokens, temperature, effort, reasoning_mode, updated_at "
                "FROM shared.stage_model_params WHERE stage IN ('t2_flag_fix', 's1_flag_fix') ORDER BY 1, 2"):
            print(f"FLAGFIX_PARAMS stage={r['stage']} model={r['model_key']} max_tokens={r['max_tokens']} "
                  f"min_output_tokens={r['min_output_tokens']} temperature={r['temperature']} effort={r['effort']} "
                  f"reasoning_mode={r['reasoning_mode']} updated={r['updated_at']:%Y-%m-%d}")
        print("FLAGFIX_PARAMS rows_above_or_none (none = call site value or LLMRequest default 4096; "
              "grounding.repair sends max_tokens=4096; _rerepair_meta sends none)")
        for r in await c.fetch(
                "SELECT model_key, max_output_tokens, capabilities ? 'min_output_tokens' AS has_min, "
                "capabilities->>'min_output_tokens' AS min_out, family FROM shared.llm_model_catalog "
                "WHERE model_key = ANY($1::text[]) ORDER BY 1", models):
            print(f"FLAGFIX_CATALOG model={r['model_key']} family={r['family']} max_output_tokens={r['max_output_tokens']} "
                  f"capabilities.min_output_tokens={r['min_out']}")
        ff_rows = await c.fetch(
            "SELECT l.created_at, l.tenant_id, l.job_id, l.tour_id, l.model, l.connection_key, l.status, l.error_class, "
            "l.stop_reason, l.tokens_in, l.tokens_out, l.reasoning_tokens, l.effort, l.latency_ms, l.attempt_no, "
            "l.cost_usd, l.pricing_mode, l.prompt_version, l.quality_signal, j.payload->>'published_tour_id' AS pub "
            "FROM shared.llm_call_log l LEFT JOIN shared.job j ON j.id = l.job_id "
            "WHERE l.stage = 't2_flag_fix' AND l.tenant_id = ANY($1::uuid[]) AND l.created_at >= $2 "
            "AND l.created_at < $3 ORDER BY l.created_at", tids, since, until)
        ff_jobs, ff_sum = set(), collections.Counter()
        for r in ff_rows:
            qs = r["quality_signal"]
            qs = json.loads(qs) if isinstance(qs, str) else (qs or {})
            if "source" in qs and qs.get("source") == "grounding_repair":
                task = "sentence_repair"
            elif "meta_landed_in_band" in qs or "candidate_len" in qs:
                task = "meta_regenerate"
            else:
                task = "unknown(unusable_or_other)"
            fields = qs.get("fields_changed")
            fields = [x for x in fields if isinstance(x, str) and re.match(r"^[a-z_]{1,32}$", x)] \
                if isinstance(fields, list) else None
            ff_sum[(task, r["stop_reason"] or "-", r["status"] or "-")] += 1
            if r["job_id"]:
                ff_jobs.add(r["job_id"])
            print(f"FLAGFIX_CALL at={r['created_at']:%H:%M:%SZ} tenant={slug.get(r['tenant_id'])} job={p8(r['job_id'])} "
                  f"pub_tour={p8(r['pub'])} task={task} model={r['model']}@{r['connection_key']} status={r['status']} "
                  f"error_class={r['error_class']} stop_reason={r['stop_reason']} tokens_in={r['tokens_in']} "
                  f"tokens_out={r['tokens_out']} reasoning_tokens={r['reasoning_tokens']} effort={r['effort']} "
                  f"latency_ms={r['latency_ms']} attempt_no={r['attempt_no']} usd={f(r['cost_usd'], 5)} "
                  f"pricing={r['pricing_mode']} prompt_v={r['prompt_version']} "
                  f"qs.sentences={qs.get('sentences')} qs.fields_changed={fields} "
                  f"qs.meta_landed={qs.get('meta_landed_in_band')} qs.candidate_len={qs.get('candidate_len')} "
                  f"qs.attempt={qs.get('attempt')} qs.truncation_retry={qs.get('truncation_retry')} "
                  f"qs.max_tokens={qs.get('max_tokens')} qs.retry_reason="
                  f"{qs.get('retry_reason') if isinstance(qs.get('retry_reason'), str) and ENUM_RE.match(qs.get('retry_reason')) else None} "
                  f"qs.keys={sorted(qs.keys())[:16]}")
        summary["flagfix"] = [{"task": t, "stop_reason": s, "status": st, "n": n} for (t, s, st), n in ff_sum.items()]
        t3_key = re.compile(r"(t3|repair|meta|stopped|degraded|attempt|passed|chosen|jev|sentence|em_dash|qa_|score|"
                            r"version_status|orchestrat)")
        for jid in sorted(ff_jobs, key=str):
            j = await c.fetchrow("SELECT kind, status, attempt, result, error FROM shared.job WHERE id = $1", jid)
            if not j:
                continue
            res = j["result"]
            res = json.loads(res) if isinstance(res, str) else (res or {})
            flat = {k: v for k, v in flatten(res).items() if t3_key.search(k)}
            print(f"FLAGFIX_JOB job={p8(jid)} kind={j['kind']} status={j['status']} attempt={j['attempt']} "
                  f"error_class={err_class(j['error'])} result={json.dumps(flat, default=str)[:900]}")
        for r in await c.fetch(
                "SELECT stage, model, coalesce(status, 'null') AS st, coalesce(stop_reason, '-') AS sr, count(*) AS n, "
                "round(avg(tokens_out)) AS out_avg, max(tokens_out) AS out_max, round(avg(reasoning_tokens)) AS rsn_avg, "
                "count(*) FILTER (WHERE quality_signal ? 'meta_landed_in_band') AS meta_calls, "
                "count(*) FILTER (WHERE quality_signal->>'source' = 'grounding_repair') AS sentence_calls, "
                "count(*) FILTER (WHERE tenant_id IS NOT NULL) AS tenant_rows "
                "FROM shared.llm_call_log WHERE stage IN ('t2_flag_fix', 's1_flag_fix') AND is_shadow IS NOT TRUE "
                "AND created_at >= now() - make_interval(days => $1) GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 5 DESC", ff_days):
            print(f"FLAGFIX_30D days={ff_days} stage={r['stage']} model={r['model']} status={r['st']} stop_reason={r['sr']} "
                  f"n={r['n']} tokens_out_avg={r['out_avg']} tokens_out_max={r['out_max']} reasoning_avg={r['rsn_avg']} "
                  f"meta_regenerate_calls={r['meta_calls']} sentence_repair_calls={r['sentence_calls']} "
                  f"tenant_rows={r['tenant_rows']}")

        print("SUMMARY_JSON " + json.dumps(summary, default=str, separators=(",", ":")))
    finally:
        await c.close()


asyncio.run(main())
