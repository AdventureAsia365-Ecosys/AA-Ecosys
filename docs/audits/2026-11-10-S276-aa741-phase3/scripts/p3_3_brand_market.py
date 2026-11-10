"""AA-741 phase 3 (S276), slice 3: brand distinctness and unfamiliar markets. READ-ONLY, $0, no LLM / DFS call, no write.

Run by the orchestrator (CIS api container, DATABASE_URL = cis_app):
    tools/ecs/ecsx.sh docs/audits/2026-11-10-S276-aa741-phase3/scripts/p3_3_brand_market.py P2_SINCE=2026-11-10T05:49:46Z

Env:
  P2_SINCE  phase 2 start, ISO (required). Only T2 versions / blog pieces / judge rows created since then count.
  TOURS8    the 12 phase 2 tours as 8-char published_tours.id prefixes (default: the S275 pick list below).
  FOCUS8    the tour to show per tenant in full (default a8560125, escalated for several tenants).
  PROBE     1 (default) = per tour x DFS market keyword probe from the research cache (search_demand, read only), 0 = skip.
  SHINGLE   word n-gram size for the cross-brand similarity (default 5).

Prints counts, code constants, 8-char ids and aggregates only: never tour, piece, judge-feedback or claim text, no
e-mail, no secret. Computations that read text (word hits, brand-name leaks, similarity) run here and print numbers.
Section lines (report section in brackets):
  BRAND        per tenant brand pack: fields filled, forbidden count, signature words (POSITIONING constants) [brand]
  T2 / T2_CLAIMS / T2_CODES / T2_WORDS / T2_LEAK / T2_LEN   per tenant T2 judge scores, brand-claim fidelity, final
               contract + T3 codes, word layers (platform truth, undeclared positioning, own forbidden list,
               superlatives, signature use, unsupported service claims), persona / brand leaks [brand]
  T2_NR        one line per needs_review version: typed reasons (score under the pass line, T3 codes, fallback, policy)
  FOCUS        the FOCUS8 tour per tenant [brand, needs_review case]
  T2_SIM / T2_SIM_PAIR   the same tour written for the 4 brands: pairwise word-shingle Jaccard (distinctness) and
               overlap with the Master source [brand distinctness]
  BLOG / BLOG_GATES / BLOG_WORDS / BLOG_LEAK / BLOG_F9 / BLOG_SIM   the same for the phase 2 blog pieces [brand]
  MARKET / MARKET_T2 / MARKET_SLATE / MARKET_BLOG   per tenant declared vs DFS-supported markets, the market T2 used,
               the AA-629 banner flag, keyword counts / quality signals [markets]
  DEMAND       search_demand coverage per market (DFS 6 + the unsupported codes the brands declare) [markets]
  PROBE        per tour x DFS market: keyword ideas / PAA the research cache would give (tenant_market_seo's rule) [markets]
  JSON         one line with every aggregate above.
"""
import asyncio
import collections
import itertools
import json
import os
import re
import sys
from datetime import datetime
from statistics import mean

import asyncpg

sys.path.insert(0, "/app")

AUDIT = ["audit-atlas-hearth", "audit-terra-family", "audit-trail-pulse", "audit-wildkind-travel"]
DEFAULT_TOURS8 = ("8602c1d4,2cf487be,84e392c3,caf4bf16,ac574bfe,56b61f58,207e4efa,2d0ee81a,c9716429,a8560125,"
                  "7fe02d1a,b56704c5")
DFS6 = ("US", "UK", "AU", "DE", "FR", "NL")
UNSUPPORTED_PROBE = ("AE", "SA", "SG", "HK", "CA", "NZ")
BRAND_GATES = ("F2_brand_forbidden", "F2_platform_truth", "F2_superlatives", "F2_banned_patterns", "F2_style_warn",
               "F11_brand_name", "F9_brand_style", "F15_voice", "F15_voice_warn", "F19_authenticity",
               "F10_cannibalization_cross_tenant", "F9_cta_fact", "F17_trip_fact")
EXCLUDE_PIECES8 = {"d67e3178"}  # synthetic piece (S238 rule), as slices 1 and 4
OUT: dict = {}


def jl(v):
    """jsonb arrives as text (no codec registered)."""
    if isinstance(v, str):
        try:
            return json.loads(v) if v.strip() else None
        except ValueError:
            return None
    return v


def p8(x) -> str:
    return str(x)[:8] if x else "-"


def has_test_flag(obj) -> bool:
    """S238 rule: a synthetic piece carries a `*_test` key somewhere in content_piece.flags (a list of gate
    entries, or a dict)."""
    if isinstance(obj, dict):
        return any(str(k).endswith("_test") for k in obj) or any(has_test_flag(v) for v in obj.values())
    if isinstance(obj, list):
        return any(has_test_flag(v) for v in obj)
    return False


def quiet_logs() -> None:
    """Drop the structlog events of the imported app modules: the run prints only this script's own lines."""
    try:
        import structlog

        def _drop(_logger, _name, _event):
            raise structlog.DropEvent

        structlog.configure(processors=[_drop])
    except Exception:  # noqa: BLE001
        pass


def r2(x):
    return None if x is None else round(float(x), 2)


def stats(vals):
    vals = [float(v) for v in vals if v is not None]
    if not vals:
        return {"n": 0}
    return {"n": len(vals), "mean": round(mean(vals), 2), "min": round(min(vals), 2), "max": round(max(vals), 2)}


def strings(obj) -> list[str]:
    """Every string value of a nested jsonb value (dict keys skipped)."""
    out: list[str] = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("status", "trip_type"):
                continue
            out += strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            out += strings(v)
    return out


def shingles(text: str, n: int) -> set:
    w = re.findall(r"[a-z0-9']+", (text or "").lower())
    return {tuple(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def jacc(a: set, b: set):
    return None if not a or not b else len(a & b) / len(a | b)


def contain(a: set, b: set):
    """Share of a's shingles that also sit in b (how much of a is copied from b)."""
    return None if not a or not b else len(a & b) / len(a)


def line(tag: str, **kv) -> None:
    print(tag + " " + " ".join(f"{k}={json.dumps(v, default=str, separators=(',', ':')) if not isinstance(v, (int, float, str)) or isinstance(v, bool) else v}" for k, v in kv.items()))


def word_layers(text: str, pack: dict, sv, source: str, own_brand: str, other_brands: dict, bp) -> dict:
    """Counts only: the AA-800 word layers, signature use, unsupported service claims and brand-name leaks."""
    low = (text or "").lower()
    cnt = lambda w: len(list(sv._word_re(w).finditer(low)))  # noqa: E731 — the module's own match rule
    platform = {w: cnt(w) for w in sv.PLATFORM_TRUTH if cnt(w)}
    undeclared = {w: cnt(w) for w in sv.undeclared_positioning(pack, include_prompt_only=True) if cnt(w)}
    own_forbidden = [w for w in sv._lower_list(pack.get("forbidden_words")) if cnt(w)]
    sig = sv.signature_words(pack)
    sig_use = {w: cnt(w) for w in sig}
    sup = sv.superlative_hits(text)
    claims = sv.service_level_claims(text, source)
    foreign = bp.foreign_brand_mentions(text, own_brand, source)
    others_norm = {bp._norm(n): s for s, n in other_brands.items() if n}
    f_other_audit = sum(1 for m in foreign if bp._norm(m) in others_norm or any(o and o in bp._norm(m) for o in others_norm))
    f_platform = sum(1 for m in foreign if bp._PLATFORM_NAMES_RE.fullmatch(m.strip()))
    other_name_hits = {s: len(re.findall(r"(?<!\w)" + re.escape(n.lower()) + r"(?!\w)", low))
                       for s, n in other_brands.items() if n}
    own_hits = len(re.findall(r"(?<!\w)" + re.escape(own_brand.lower()) + r"(?!\w)", low)) if own_brand else 0
    return {"platform": platform, "undeclared": undeclared, "own_forbidden_hits": sum(cnt(w) for w in own_forbidden),
            "own_forbidden_words": len(own_forbidden), "superlatives": len(sup),
            "over_cap": len(sup) > sv.SUPERLATIVE_CAP, "sig_use": sig_use, "sig_used": any(sig_use.values()),
            "service_claims_unsupported": len(claims),
            "service_claim_words": dict(collections.Counter(c["word"] for c in claims)),
            "foreign_mentions": len(foreign), "foreign_platform": f_platform, "foreign_other_audit": f_other_audit,
            "foreign_other": len(foreign) - f_platform - f_other_audit,
            "other_audit_name_hits": sum(other_name_hits.values()), "own_name_hits": own_hits,
            "words": len(re.findall(r"\w+", low))}


def fold_layers(rows: list[dict]) -> dict:
    agg = {"n": len(rows), "platform": collections.Counter(), "undeclared": collections.Counter(),
           "sig_use": collections.Counter(), "service_claim_words": collections.Counter()}
    for k in ("own_forbidden_hits", "superlatives", "service_claims_unsupported", "foreign_mentions",
              "foreign_platform", "foreign_other_audit", "foreign_other", "other_audit_name_hits", "own_name_hits"):
        agg[k] = sum(r[k] for r in rows)
    for k in ("over_cap", "sig_used"):
        agg["n_" + k] = sum(1 for r in rows if r[k])
    agg["n_own_forbidden"] = sum(1 for r in rows if r["own_forbidden_hits"])
    agg["n_leak"] = sum(1 for r in rows if r["foreign_mentions"] or r["other_audit_name_hits"])
    for r in rows:
        for k in ("platform", "undeclared", "sig_use", "service_claim_words"):
            agg[k].update(r[k])
    for k in ("platform", "undeclared", "sig_use", "service_claim_words"):
        agg[k] = dict(agg[k])
    agg["words"] = stats([r["words"] for r in rows])
    return agg


def sim_block(tag: str, texts_by_tour: dict, n: int, src_by_tour: dict | None) -> dict:
    """texts_by_tour: {tour8: {slug: text}}. Pairwise Jaccard per tour and per brand pair; containment in the source."""
    per_pair = collections.defaultdict(list)
    per_tour = {}
    for t8, by in sorted(texts_by_tour.items()):
        sh = {s: shingles(tx, n) for s, tx in by.items() if tx}
        vals = []
        for a, b in itertools.combinations(sorted(sh), 2):
            j = jacc(sh[a], sh[b])
            if j is not None:
                vals.append(j)
                per_pair[f"{a.replace('audit-', '')}~{b.replace('audit-', '')}"].append(j)
        src = shingles(src_by_tour.get(t8, ""), n) if src_by_tour else set()
        cont = [contain(v, src) for v in sh.values()] if src else []
        rec = {"brands": len(sh), "pairs": len(vals), "jaccard": stats(vals),
               **({"src_containment": stats(cont)} if src else {})}
        per_tour[t8] = rec
        line(tag, tour=t8, brands=len(sh), pairs=len(vals), jaccard=stats(vals),
             **({"src_containment": stats(cont)} if src else {}))
    pairs = {k: stats(v) for k, v in sorted(per_pair.items())}
    for k, v in pairs.items():
        line(tag + "_PAIR", pair=k, jaccard=v)
    allv = [j for v in per_pair.values() for j in v]
    line(tag + "_ALL", shingle=n, jaccard=stats(allv))
    return {"per_tour": per_tour, "per_pair": pairs, "all": stats(allv)}


async def main() -> None:
    if not os.environ.get("P2_SINCE"):
        print("STOP P2_SINCE (phase 2 start, ISO) is required")
        return
    since = datetime.fromisoformat(os.environ["P2_SINCE"].replace("Z", "+00:00"))
    tours8 = [t.strip().lower()[:8] for t in os.environ.get("TOURS8", DEFAULT_TOURS8).split(",") if t.strip()]
    focus8 = os.environ.get("FOCUS8", "a8560125").strip().lower()[:8]
    probe = os.environ.get("PROBE", "1") != "0"
    n_sh = int(os.environ.get("SHINGLE", "5"))

    from services.acp_shared import brand_pack as bp
    from services.acp_shared import signature_vocabulary as sv
    from services.acp_content_writing.quality_gates import expand_ledger
    from services.brand_intake.markets import SUPPORTED, normalize_markets
    from services.content_generation import t2_brand_claims
    try:  # S276 review (OOM): the job module pulls in the job runner + LLM client stack; opt in with T2_IMPORT=1.
        if os.environ.get("T2_IMPORT") != "1":
            raise ImportError("light path")
        from services.jobs.t2_rewrite_job import _PT_SQL, _T2_STATUS_PASS, source_tour_dict
    except Exception as e:  # noqa: BLE001
        # same columns source_tour_dict reads, same function body (t2_rewrite_job at CIS main 5cc016cd)
        print(f"NOTE t2_rewrite_job not imported ({type(e).__name__}); light source read (same fields)")
        from services.quality.registry import threshold
        _T2_STATUS_PASS = threshold("t2.status_pass")
        _PT_SQL = ("SELECT pt.id, pt.tour_id, pt.aa_name, pt.aa_subtitle, pt.aa_summary, pt.aa_description, "
                   "pt.aa_highlights, pt.aa_itineraries, pt.seo_title, pt.seo_meta, rt.country, rt.duration "
                   "FROM gold_aa_internal.published_tours pt LEFT JOIN silver_aa_internal.raw_tours rt "
                   "ON rt.tour_id = pt.tour_id WHERE pt.id = $1::uuid")

        def source_tour_dict(pt) -> dict:  # t2_rewrite_job.source_tour_dict, same keys
            return {"name": pt["aa_name"], "subtitle": pt.get("aa_subtitle") or "", "summary": pt.get("aa_summary") or "",
                    "description": pt.get("aa_description") or "", "highlights": pt.get("aa_highlights") or "",
                    "itineraries": pt.get("aa_itineraries") or "", "seo_title": pt.get("seo_title") or "",
                    "seo_meta": pt.get("seo_meta") or "", "country": pt.get("country") or "",
                    "duration": pt.get("duration") or ""}
    from services.seo_intelligence import s1_prefetch as sp
    from services.seo_intelligence.seed_builder import (LOCATION_CODE_TO_MARKET, resolve_buyer_market,
                                                        resolve_buyer_markets, unmatched_countries)
    quiet_logs()

    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        await c.execute("SET default_transaction_read_only = on")
        await c.execute("SET statement_timeout = '90s'")
        print(f"RUN since={since.isoformat()} tours={len(tours8)} focus={focus8} shingle={n_sh} "
              f"t2_pass_line={_T2_STATUS_PASS}")
        ten = await c.fetch("SELECT tenant_id, slug FROM shared.tenants WHERE slug = ANY($1::text[]) ORDER BY slug",
                            AUDIT)
        tids = [t["tenant_id"] for t in ten]
        slug_of = {t["tenant_id"]: t["slug"] for t in ten}
        pts = await c.fetch("SELECT id, tour_id FROM gold_aa_internal.published_tours "
                            "WHERE left(id::text, 8) = ANY($1::text[])", tours8)
        pt_by8 = {p8(r["id"]): r for r in pts}
        print(f"SCOPE tenants={len(ten)} tours_found={len(pt_by8)}/{len(tours8)} "
              f"missing={[t for t in tours8 if t not in pt_by8]}")

        # ------------------------------------------------------------------ brand packs
        packs, brands = {}, {}
        for t in ten:
            row = await c.fetchrow(bp._PACK_QUERY, str(t["tenant_id"]))
            pk = bp.pack_from_row(row)
            packs[t["slug"]] = pk
            brands[t["slug"]] = pk.get("brand_name") or ""
            sig = sv.signature_words(pk)
            rec = {"version": pk.get("version"), "has_brand_name": bool(pk.get("brand_name")),
                   "system_prompt": bool(pk.get("system_prompt")), "style_guide_chars": len(pk.get("style_guide") or ""),
                   "core_idea": bool(pk.get("core_idea")), "voice_n": len(pk.get("voice") or []),
                   "forbidden_n": len(pk.get("forbidden_words") or []), "good_examples": bool(pk.get("good_examples")),
                   "default_cta": bool(pk.get("default_cta")), "signature_words": sig,
                   "signature_explicit_n": len(pk.get("signature_words") or []),
                   "undeclared_positioning": sv.undeclared_positioning(pk, include_prompt_only=True),
                   "rewrite_language": (row or {}).get("rewrite_language") if row else None,
                   "target_markets_n": len((row or {}).get("target_markets") or []) if row else 0}
            OUT.setdefault("brand", {})[t["slug"]] = rec
            line("BRAND", tenant=t["slug"], **rec)

        # ------------------------------------------------------------------ T2 versions (latest per pair, phase 2)
        vers = await c.fetch(
            "SELECT DISTINCT ON (v.tenant_id, v.published_tour_id) v.id, v.tenant_id, v.published_tour_id, "
            "v.version_number, v.status, v.qa_status, v.quality_score::float AS score, v.qa_repair_count, "
            "v.rewritten_content, v.judge_breakdown, v.generation_meta, v.job_id, v.created_at, j.result AS job_result "
            "FROM gold_aa_internal.tenant_tour_versions v LEFT JOIN shared.job j ON j.id = v.job_id "
            "WHERE v.tenant_id = ANY($1::uuid[]) AND v.created_at >= $2::timestamptz "
            "AND left(v.published_tour_id::text, 8) = ANY($3::text[]) "
            "ORDER BY v.tenant_id, v.published_tour_id, v.version_number DESC", tids, since, tours8)
        print(f"T2_SCOPE versions={len(vers)} (expected {len(ten) * len(pt_by8)})")
        src_cache: dict = {}

        async def source_of(pub_id) -> str:
            k = p8(pub_id)
            if k not in src_cache:
                row = await c.fetchrow(_PT_SQL, pub_id)
                src_cache[k] = t2_brand_claims.source_text(source_tour_dict(row)) if row else ""
            return src_cache[k]

        rq = {}
        if vers:
            for r in await c.fetch("SELECT tenant_tour_version_id AS vid, escalate_detail FROM "
                                   "silver_aa_internal.review_queue WHERE tenant_tour_version_id = ANY($1::uuid[])",
                                   [v["id"] for v in vers]):
                det = jl(r["escalate_detail"]) or []
                rq.setdefault(r["vid"], collections.Counter()).update(
                    str(d.get("check_id")) for d in det if isinstance(d, dict))

        t2_by_tenant = collections.defaultdict(list)
        t2_texts = collections.defaultdict(dict)
        src_by_tour = {}
        for v in vers:
            slug, t8 = slug_of[v["tenant_id"]], p8(v["published_tour_id"])
            content = jl(v["rewritten_content"]) or {}
            text = "\n".join(strings(content))
            src = await source_of(v["published_tour_id"])
            src_by_tour[t8] = src
            t2_texts[t8][slug] = text
            others = {s: n for s, n in brands.items() if s != slug}
            layers = word_layers(text, packs[slug], sv, src, brands[slug], others, bp)
            jb = jl(v["judge_breakdown"]) or {}
            gm = jl(v["generation_meta"]) or {}
            orch = gm.get("t2_orchestrator") or {}
            jr = jl(v["job_result"]) or {}
            fc = jb.get("final_contract") or {}
            claims = jb.get("brand_claims") or {}
            reasons = []
            if v["status"] == "needs_review":
                if jb.get("policy_hold"):
                    reasons.append("policy_hold")
                if (jb.get("fallback_writer") or {}).get("held"):
                    reasons.append("fallback_writer_held")
                if v["score"] is None or v["score"] < float(_T2_STATUS_PASS):
                    reasons.append("score_below_pass_line")
                codes = list((orch.get("chosen") or {}).get("codes") or [])
                if codes:
                    reasons.append("t3_enforce_codes")
                if v["qa_status"] == "escalated" and not codes:
                    reasons.append("qa_escalated_no_chosen_codes")
                if not reasons:
                    reasons.append("unexplained")
            t2_by_tenant[slug].append({
                "t8": t8, "vid": p8(v["id"]), "status": v["status"], "qa": v["qa_status"], "score": v["score"],
                "repairs": v["qa_repair_count"], "jb": jb, "orch": orch, "jr": jr, "fc": fc, "claims": claims,
                "layers": layers, "rq": dict(rq.get(v["id"], {})), "reasons": reasons})

        for slug in sorted(t2_by_tenant):
            rows = t2_by_tenant[slug]
            jbs = [r["jb"] for r in rows]
            judged = [j for j in jbs if j.get("judged")]
            t2 = {"n": len(rows), "status": dict(collections.Counter(r["status"] for r in rows)),
                  "qa": dict(collections.Counter(r["qa"] for r in rows)),
                  "score": stats([r["score"] for r in rows]),
                  "repairs": stats([r["repairs"] for r in rows]),
                  "judged": len(judged), "brand_fit": stats([j.get("brand_fit") for j in judged]),
                  "cross_brand_distinct": stats([j.get("cross_brand_distinct") for j in judged]),
                  "judge_score": stats([j.get("judge_score") for j in judged]),
                  "validate_score": stats([j.get("validate_score") for j in jbs]),
                  "mission_present": dict(collections.Counter(str(j.get("mission_present")) for j in judged)),
                  "binding": dict(collections.Counter(str(j.get("binding")) for j in jbs)),
                  "gate": dict(collections.Counter(str(j.get("gate")) for j in judged)),
                  "brand_fit_by_status": {s: stats([r["jb"].get("brand_fit") for r in rows if r["status"] == s])
                                          for s in sorted({r["status"] for r in rows})}}
            line("T2", tenant=slug, **t2)
            cl_kinds = collections.Counter()
            in_pack = checked = 0
            for r in rows:
                checked += int(r["claims"].get("checked") or 0)
                for u in r["claims"].get("unsupported") or []:
                    cl_kinds[u.get("kind")] += 1
                    in_pack += 1 if u.get("in_brand_pack") else 0
            claims = {"versions_with_check": sum(1 for r in rows if r["claims"]), "checked": checked,
                      "unsupported": dict(cl_kinds), "unsupported_in_brand_pack": in_pack,
                      "versions_with_unsupported": sum(1 for r in rows if r["claims"].get("unsupported"))}
            line("T2_CLAIMS", tenant=slug, **claims)
            codes = {"chosen_codes": dict(collections.Counter(c for r in rows for c in (r["orch"].get("chosen") or {}).get("codes") or [])),
                     "brand_precheck": dict(collections.Counter(c for r in rows for c in r["orch"].get("brand_precheck") or [])),
                     "orch_status": dict(collections.Counter(str(r["orch"].get("status")) for r in rows)),
                     "fc_verdict": dict(collections.Counter(str(r["fc"].get("verdict")) for r in rows)),
                     "fc_agrees": dict(collections.Counter(str(r["fc"].get("agrees")) for r in rows)),
                     "fc_findings": dict(collections.Counter(f.get("code") for r in rows for f in r["fc"].get("findings") or [] if isinstance(f, dict))),
                     "review_queue_checks": dict(sum((collections.Counter(r["rq"]) for r in rows), collections.Counter())),
                     "fallback_writer": sum(1 for r in rows if r["jb"].get("fallback_writer")),
                     "route_degraded": sum(1 for r in rows if r["jb"].get("route_degraded")),
                     "policy_hold": sum(1 for r in rows if r["jb"].get("policy_hold"))}
            line("T2_CODES", tenant=slug, **codes)
            lay = fold_layers([r["layers"] for r in rows])
            line("T2_WORDS", tenant=slug, n=lay["n"], platform_truth=lay["platform"], undeclared_positioning=lay["undeclared"],
                 own_forbidden_hits=lay["own_forbidden_hits"], versions_own_forbidden=lay["n_own_forbidden"],
                 superlatives=lay["superlatives"], versions_over_cap=lay["n_over_cap"], sig_use=lay["sig_use"],
                 versions_sig_used=lay["n_sig_used"], service_claims_unsupported=lay["service_claims_unsupported"],
                 service_claim_words=lay["service_claim_words"])
            line("T2_LEAK", tenant=slug, versions_with_leak=lay["n_leak"], foreign_mentions=lay["foreign_mentions"],
                 platform=lay["foreign_platform"], other_audit_brand=lay["foreign_other_audit"],
                 other=lay["foreign_other"], other_audit_name_hits=lay["other_audit_name_hits"],
                 own_name_hits=lay["own_name_hits"])
            line("T2_LEN", tenant=slug, words=lay["words"])
            for r in rows:
                if r["status"] == "needs_review":
                    line("T2_NR", tenant=slug, tour=r["t8"], v=r["vid"], status=f"{r['status']}/{r['qa']}",
                         score=r2(r["score"]), pass_line=_T2_STATUS_PASS, reasons=r["reasons"],
                         chosen_codes=(r["orch"].get("chosen") or {}).get("codes") or [],
                         fc=r["fc"].get("verdict"), fc_findings=[f.get("code") for f in r["fc"].get("findings") or [] if isinstance(f, dict)],
                         rq=r["rq"], brand_fit=r2(r["jb"].get("brand_fit")), claims_unsupported=len(r["claims"].get("unsupported") or []),
                         budget=(r["orch"].get("budget") or {}))
            OUT.setdefault("t2", {})[slug] = {**t2, "claims": claims, "codes": codes, "words": lay,
                                              "needs_review": [{k: r[k] for k in ("t8", "vid", "status", "qa", "score", "reasons", "rq")}
                                                               for r in rows if r["status"] == "needs_review"]}

        for slug in sorted(t2_by_tenant):
            for r in t2_by_tenant[slug]:
                if r["t8"] != focus8:
                    continue
                rec = {"v": r["vid"], "status": f"{r['status']}/{r['qa']}", "score": r2(r["score"]), "repairs": r["repairs"],
                       "reasons": r["reasons"], "chosen": {k: (r["orch"].get("chosen") or {}).get(k) for k in ("attempt", "via", "codes", "score")},
                       "steps": [{"a": s.get("attempt"), "via": s.get("via"), "codes": s.get("codes"), "score": s.get("score")}
                                 for s in (r["orch"].get("steps") or [])][:8],
                       "budget": r["orch"].get("budget"), "fc": r["fc"].get("verdict"),
                       "fc_findings": [f.get("code") for f in r["fc"].get("findings") or [] if isinstance(f, dict)],
                       "rq": r["rq"], "brand_fit": r2(r["jb"].get("brand_fit")), "binding": r["jb"].get("binding"),
                       "claims_unsupported_kinds": dict(collections.Counter(u.get("kind") for u in r["claims"].get("unsupported") or [])),
                       "policy_hold": bool(r["jb"].get("policy_hold")), "fallback_writer": bool(r["jb"].get("fallback_writer")),
                       "t3_degraded": len(((r["jr"].get("t3") or {}).get("degraded") or [])),
                       "seo": {k: r["jr"].get(k) for k in ("seo_source", "market")},
                       "words": {k: r["layers"][k] for k in ("platform", "undeclared", "own_forbidden_hits", "superlatives",
                                                             "service_claims_unsupported", "foreign_mentions")}}
                OUT.setdefault("focus", {})[slug] = rec
                line("FOCUS", tour=focus8, tenant=slug, **rec)

        OUT["t2_sim"] = sim_block("T2_SIM", t2_texts, n_sh, src_by_tour)

        # ------------------------------------------------------------------ T9 blog pieces (phase 2)
        pieces = await c.fetch(
            "SELECT cp.piece_id, cp.tenant_id, cp.status, cp.content_text, cp.gate_ledger, cp.flags, cp.writer_input, "
            "cp.created_at, s.segment_id, s.route_id, s.cleared_bar_reason, r.route_segment_ids, r.dfs_paa_snapshot, "
            "r.subject_id FROM acp_shared.content_piece cp "
            "JOIN acp_shared.angle_gate_request r ON r.request_id = cp.angle_gate_request_id "
            "LEFT JOIN acp_shared.subject s ON s.subject_id = r.subject_id "
            "WHERE cp.tenant_id = ANY($1::uuid[]) AND cp.channel = 'blog' AND cp.created_at >= $2::timestamptz "
            "ORDER BY cp.created_at", tids, since)
        excluded = []
        keep = []
        for pc in pieces:
            fl = jl(pc["flags"])
            if has_test_flag(fl) or p8(pc["piece_id"]) in EXCLUDE_PIECES8:
                excluded.append(p8(pc["piece_id"]))
            else:
                keep.append(pc)
        print(f"BLOG_SCOPE pieces={len(pieces)} kept={len(keep)} excluded_test={excluded}")
        segs = set()
        for pc in keep:
            if pc["segment_id"]:
                segs.add(pc["segment_id"])
            for sid in jl(pc["route_segment_ids"]) or []:
                segs.add(str(sid))
        seg_tours = collections.defaultdict(set)
        if segs:
            for r in await c.fetch(
                    "SELECT DISTINCT ar.segment_id, ar.tour_id FROM acp_contract.atom_ranking ar "
                    "WHERE ar.segment_id = ANY($1::text[]) AND ar.tour_id = ANY($2::uuid[]) "
                    "AND ar.excluded_reason IS NULL AND ar.superseded_at IS NULL",
                    list(segs), [r["tour_id"] for r in pts]):
                seg_tours[r["segment_id"]].add(r["tour_id"])
        t8_of_tour = {r["tour_id"]: p8(r["id"]) for r in pts}
        f9_rows = await c.fetch(
            "SELECT l.tenant_id, l.content_piece_id, l.quality_signal FROM shared.llm_call_log l "
            "WHERE l.tenant_id = ANY($1::uuid[]) AND l.created_at >= $2::timestamptz AND l.stage = 't10_judge' "
            "AND l.is_shadow IS NOT TRUE", tids, since)

        blog_by_tenant = collections.defaultdict(list)
        blog_texts = collections.defaultdict(dict)
        best = {}
        for pc in keep:
            slug = slug_of[pc["tenant_id"]]
            wi = jl(pc["writer_input"]) or {}
            seed_src = "\n".join([str(wi.get("seed") or ""), str(wi.get("facts") or "")] +
                                 [str((m or {}).get("seed") or "") for m in wi.get("route_moments") or [] if isinstance(m, dict)])
            others = {s: n for s, n in brands.items() if s != slug}
            layers = word_layers(pc["content_text"], packs[slug], sv, seed_src, brands[slug], others, bp)
            led = jl(pc["gate_ledger"]) or []
            exp = expand_ledger([g for g in led if isinstance(g, dict) and "gate" in g])
            ran = {g["gate"] for g in exp}
            failed = collections.Counter(g["gate"] for g in exp if not g.get("passed"))
            viol = collections.Counter()
            for g in exp:
                if not g.get("passed"):
                    viol[g["gate"]] += len(g.get("violations") or [])
            bar = jl(pc["cleared_bar_reason"]) or {}
            snap = jl(pc["dfs_paa_snapshot"]) or {}
            seg_ids = ([pc["segment_id"]] if pc["segment_id"] else []) + [str(s) for s in jl(pc["route_segment_ids"]) or []]
            tours = sorted({t8_of_tour[t] for s in seg_ids for t in seg_tours.get(s, ())})
            rec = {"p8": p8(pc["piece_id"]), "status": pc["status"], "layers": layers, "ran": ran, "failed": failed,
                   "viol": viol, "grain": "segment" if pc["segment_id"] else ("route" if pc["route_id"] else "none"),
                   "demand": bar.get("demand"), "questions": bar.get("questions"),
                   "keyword": bool(wi.get("keyword")), "search_q": len(wi.get("search_questions") or []),
                   "q_sources": wi.get("question_sources") or {}, "faq_q": len(wi.get("faq_questions") or []),
                   "snap_rel": str(snap.get("relevance")) if snap else "none",
                   "snap_paa": len(snap.get("people_also_ask") or []) if snap else 0,
                   "snap_related": len(snap.get("related_keywords") or []) if snap else 0,
                   "snap_tour_paa": len(snap.get("tour_people_also_ask") or []) if snap else 0, "tours": tours}
            blog_by_tenant[slug].append(rec)
            for t8 in tours:
                rank = (pc["status"] in ("approved", "held"), pc["created_at"])
                if (slug, t8) not in best or rank > best[(slug, t8)][0]:
                    best[(slug, t8)] = (rank, pc["content_text"])
        for (slug, t8), (_, tx) in best.items():
            blog_texts[t8][slug] = tx

        for slug in sorted(blog_by_tenant):
            rows = blog_by_tenant[slug]
            st = dict(collections.Counter(r["status"] for r in rows))
            line("BLOG", tenant=slug, n=len(rows), status=st, grain=dict(collections.Counter(r["grain"] for r in rows)),
                 tours_mapped=len({t for r in rows for t in r["tours"]}))
            gates = {}
            for g in BRAND_GATES:
                ran_n = sum(1 for r in rows if g in r["ran"])
                if ran_n:
                    gates[g] = {"ran": ran_n, "failed": sum(1 for r in rows if r["failed"].get(g)),
                                "violations": sum(r["viol"].get(g, 0) for r in rows)}
            all_failed = sum((r["failed"] for r in rows), collections.Counter())
            line("BLOG_GATES", tenant=slug, brand_gates=gates, all_failed_gates=dict(all_failed.most_common()))
            lay = fold_layers([r["layers"] for r in rows])
            line("BLOG_WORDS", tenant=slug, n=lay["n"], platform_truth=lay["platform"], undeclared_positioning=lay["undeclared"],
                 own_forbidden_hits=lay["own_forbidden_hits"], pieces_own_forbidden=lay["n_own_forbidden"],
                 superlatives=lay["superlatives"], pieces_over_cap=lay["n_over_cap"], sig_use=lay["sig_use"],
                 pieces_sig_used=lay["n_sig_used"], service_claims_unsupported=lay["service_claims_unsupported"],
                 service_claim_words=lay["service_claim_words"])
            line("BLOG_LEAK", tenant=slug, pieces_with_leak=lay["n_leak"], foreign_mentions=lay["foreign_mentions"],
                 platform=lay["foreign_platform"], other_audit_brand=lay["foreign_other_audit"], other=lay["foreign_other"],
                 other_audit_name_hits=lay["other_audit_name_hits"], own_name_hits=lay["own_name_hits"], words=lay["words"])
            tid = next(t for t, s in slug_of.items() if s == slug)
            f9 = [jl(r["quality_signal"]) or {} for r in f9_rows if r["tenant_id"] == tid]
            bv = [q for q in f9 if q.get("gate") == "F9_brand_voice"]
            f9rec = {"t10_judge_rows": len(f9), "brand_voice_rows": len(bv),
                     "passed": dict(collections.Counter(str(q.get("passed")) for q in bv)),
                     "status": dict(collections.Counter(str(q.get("status")) for q in bv)),
                     "failure_codes": dict(collections.Counter(c for q in bv for c in (q.get("failure_codes") or []))),
                     "reasonless": sum(1 for q in bv if q.get("reasonless")),
                     "other_gates": dict(collections.Counter(str(q.get("gate") or q.get("f9_gate")) for q in f9 if q not in bv))}
            line("BLOG_F9", tenant=slug, **f9rec)
            mk = {"subjects_demand_null": sum(1 for r in rows if r["demand"] is None),
                  "demand": stats([r["demand"] for r in rows]), "questions": stats([r["questions"] for r in rows]),
                  "with_keyword": sum(1 for r in rows if r["keyword"]), "search_questions": stats([r["search_q"] for r in rows]),
                  "question_sources": dict(sum((collections.Counter({k: int(v) for k, v in (r["q_sources"] or {}).items()
                                                                     if isinstance(v, (int, float))}) for r in rows), collections.Counter())),
                  "faq_questions": stats([r["faq_q"] for r in rows]),
                  "paa_snapshot_relevance": dict(collections.Counter(r["snap_rel"] for r in rows)),
                  "snap_paa": stats([r["snap_paa"] for r in rows]), "snap_related": stats([r["snap_related"] for r in rows]),
                  "snap_tour_paa": stats([r["snap_tour_paa"] for r in rows])}
            line("MARKET_BLOG", tenant=slug, **mk)
            OUT.setdefault("blog", {})[slug] = {"n": len(rows), "status": st, "brand_gates": gates,
                                                "all_failed_gates": dict(all_failed), "words": lay, "f9": f9rec,
                                                "market_signals": mk}
        OUT["blog_sim"] = sim_block("BLOG_SIM", blog_texts, n_sh, None)

        # ------------------------------------------------------------------ markets
        for t in ten:
            slug, tid = t["slug"], t["tenant_id"]
            br = await c.fetchrow(
                "SELECT target_markets, rewrite_language FROM shared.tenant_brand_rules WHERE tenant_id = $1 "
                "AND is_active ORDER BY (brand_name = 'default') DESC, version DESC LIMIT 1", tid)
            seo = await c.fetchrow("SELECT seo_provider::text AS provider, target_market, custom_keywords "
                                   "FROM shared.tenant_seo_config WHERE tenant_id = $1", tid)
            tc = await c.fetchrow("SELECT markets, channels FROM acp_shared.tenant_config WHERE tenant_id = $1", tid)
            um = await c.fetch("SELECT country_code, resolved_at IS NOT NULL AS resolved FROM "
                               "shared.unmapped_market_requests WHERE tenant_id = $1 ORDER BY country_code", tid)
            tm = jl(seo["target_market"]) if seo else None
            tm = tm if isinstance(tm, dict) else {}
            declared = list((br or {}).get("target_markets") or []) if br else []
            norm = normalize_markets(declared)
            countries = tm.get("countries") or []
            loc, _n, lang = resolve_buyer_market(tm)
            unmatched = unmatched_countries(tm)
            supported = [x for x in countries if x in SUPPORTED]
            first_supported = next((x for x in countries if x in SUPPORTED), None)
            t2_market = LOCATION_CODE_TO_MARKET.get(loc, "US")
            rec = {"declared": declared, "normalized_countries": norm["countries"], "seo_countries": countries,
                   "supported": supported, "unsupported": [x for x in countries if x not in SUPPORTED],
                   "unknown": tm.get("unknown") or norm["unknown"], "language": lang,
                   "brand_rewrite_language": (br or {}).get("rewrite_language") if br else None,
                   "first_declared_supported": first_supported, "t2_market": t2_market,
                   "t2_market_is_first": t2_market == first_supported,
                   "slate_markets": [LOCATION_CODE_TO_MARKET[l] for l, _x, _y in resolve_buyer_markets(tm)],
                   "aa629_banner": bool(unmatched), "unmatched": unmatched,
                   "partial_unsupported_no_banner": bool([x for x in countries if x not in SUPPORTED]) and not unmatched,
                   "tenant_config_markets": list(tc["markets"]) if tc else None,
                   "channels": list(tc["channels"]) if tc else None,
                   "unmapped_requests": [f"{r['country_code']}{'(resolved)' if r['resolved'] else ''}" for r in um],
                   "custom_keywords_n": len(jl(seo["custom_keywords"]) or []) if seo else 0,
                   "seo_provider": seo["provider"] if seo else None}
            line("MARKET", tenant=slug, **rec)
            OUT.setdefault("market", {})[slug] = rec
            rows = t2_by_tenant.get(slug, [])
            jr = [r["jr"] for r in rows]
            kw = [j.get("seo_keywords") or {} for j in jr]
            mt2 = {"versions": len(rows),
                   "market_source": dict(collections.Counter(f"{j.get('market')}:{j.get('seo_source')}" for j in jr)),
                   "kw_in": stats([k.get("in") for k in kw]), "kw_kept": stats([k.get("kept") for k in kw]),
                   "kept_zero": sum(1 for k in kw if k and not k.get("kept")), "no_kw_record": sum(1 for k in kw if not k),
                   "language_blocked": sum(1 for k in kw if k.get("language_blocked")),
                   "brand_loaded_false": sum(1 for j in jr if j.get("brand_loaded") is False),
                   "seo_error": sum(1 for j in jr if j.get("seo_source") == "error")}
            line("MARKET_T2", tenant=slug, **mt2)
            js = await c.fetchrow("SELECT id, status, finished_at, result FROM shared.job WHERE kind = 't7_slate' "
                                  "AND payload->>'tenant_id' = $1 AND status = 'succeeded' ORDER BY finished_at DESC LIMIT 1",
                                  str(tid))
            res = (jl(js["result"]) or {}) if js else {}
            bs = res.get("bar_status") or {}
            sl = {"job": p8(js["id"]) if js else "-", "finished": js["finished_at"].isoformat() if js and js["finished_at"] else None,
                  "unmatched_markets": res.get("unmatched_markets"), "segments_seen": res.get("segments_seen"),
                  "routes_seen": res.get("routes_seen"), "proposed_per_channel": res.get("proposed_per_channel"),
                  "bar_status_blog": bs.get("blog") if isinstance(bs, dict) else None}
            line("MARKET_SLATE", tenant=slug, **sl)
            OUT["market"][slug].update({"t2": mt2, "slate": sl})

        for r in await c.fetch(
                "SELECT market, count(*) AS n, count(*) FILTER (WHERE search_volume > 0) AS vol, "
                "count(*) FILTER (WHERE jsonb_typeof(people_also_ask) = 'array' AND jsonb_array_length(people_also_ask) > 0) AS paa, "
                "max(retrieved_on) AS last FROM acp_contract.search_demand WHERE market = ANY($1::text[]) "
                "GROUP BY market ORDER BY market", list(DFS6 + UNSUPPORTED_PROBE)):
            rec = {"rows": r["n"], "vol_gt0": r["vol"], "paa_rows": r["paa"], "last": r["last"].date().isoformat() if r["last"] else None}
            line("DEMAND", market=r["market"], **rec)
            OUT.setdefault("demand", {})[r["market"]] = rec
        missing = [m for m in DFS6 + UNSUPPORTED_PROBE if m not in OUT.get("demand", {})]
        line("DEMAND_ABSENT", markets=missing)

        # ------------------------------------------------------------------ probe: what each DFS market would give T2
        if probe:
            foreign_cache: dict = {}
            for t8 in tours8:
                pt = pt_by8.get(t8)
                if not pt:
                    continue
                row = await c.fetchrow("SELECT tour_id, src_name, country, activities FROM silver_aa_internal.raw_tours "
                                       "WHERE tour_id = $1::uuid", pt["tour_id"])
                if not row:
                    line("PROBE", tour=t8, error="no raw_tours row")
                    continue
                spec = sp.tour_spec(dict(row))
                if spec["country"] not in foreign_cache:  # shared.destinations (~8k rows) read once per country
                    foreign_cache[spec["country"]] = await sp.foreign_places(c, spec["country"])
                spec["foreign"] = foreign_cache[spec["country"]]
                spec["places"] = list(dict.fromkeys(spec["places"] + await sp.atom_places(c, str(pt["tour_id"]))))
                terms = sp.strong_terms(spec["places"]) + spec["activity"]
                res = {}
                # S276 review (speed): ONE search_demand scan per tour for the 6 markets (the table has no market
                # index: 6 scans -> 1), split per market here; same WHERE as tenant_market_seo
                by_market = collections.defaultdict(list)
                if terms:
                    for d in await c.fetch(
                            "SELECT market, keyword, search_volume, people_also_ask FROM acp_contract.search_demand "
                            "WHERE market = ANY($1::text[]) AND search_volume > 0 AND keyword ILIKE ANY($2::text[])",
                            list(DFS6), [f"%{x}%" for x in terms]):
                        by_market[d["market"]].append({"keyword": d["keyword"], "search_volume": d["search_volume"],
                                                       "people_also_ask": d["people_also_ask"]})
                for m in DFS6:
                    if not terms:
                        res[m] = {"terms": 0}
                        continue
                    demand = by_market.get(m, [])
                    for d in demand:
                        d["people_also_ask"] = jl(d["people_also_ask"]) or []
                    ideas, paa = sp.cached_ideas(spec, demand)
                    if not ideas:
                        ideas = sp.rank_keyword_ideas([{"keyword": d["keyword"], "search_volume": d["search_volume"]}
                                                       for d in demand], spec["places"], activity_words=spec["activity"],
                                                      country=spec["country"], foreign_places=spec.get("foreign"))
                    top = [i for i in ideas if sp._vol(i) > 0][:10]
                    res[m] = {"demand_rows": len(demand), "ideas": len(top), "paa": len(paa),
                              "top_vol_sum": sum(sp._vol(i) for i in top)}
                line("PROBE", tour=t8, country=spec["country"], places=len(spec["places"]), terms=len(terms), **res)
                OUT.setdefault("probe", {})[t8] = res
    finally:
        await c.close()
    print("JSON " + json.dumps(OUT, default=str, separators=(",", ":")))


asyncio.run(main())
