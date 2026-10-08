"""S218 full audit of the A1 write + A3 atom pipeline since the clean rerun (01/10/2026). Read-only.
Writes JSON to s3 scripts/s218_audit.json and prints a summary."""
import asyncio, json, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from datetime import datetime, timezone
from urllib.parse import urlparse
from collections import Counter, defaultdict
from services.content_generation.forbidden_words import all_forbidden, has_word, copy_text

SINCE = datetime(2026, 10, 1, tzinfo=timezone.utc)
OUT = {}

def j(v):
    return json.loads(v) if isinstance(v, str) else (v or [])

async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    # A. per country
    A = await c.fetch("""
      WITH r AS (SELECT * FROM silver_aa_internal.raw_tours),
      act AS (SELECT * FROM r WHERE source_status='active' AND deleted_at IS NULL),
      m AS (SELECT DISTINCT ON (p.tour_id) p.tour_id, p.quality_score, p.generated_content_id, p.published_at FROM gold_aa_internal.published_tours p
            WHERE p.master_status='active' ORDER BY p.tour_id, p.published_at DESC)
      SELECT coalesce(r.country,'(none)') country, count(*) raw_all,
        count(*) FILTER (WHERE r.source_status='active' AND r.deleted_at IS NULL) active,
        count(*) FILTER (WHERE NOT (r.source_status='active' AND r.deleted_at IS NULL)) inactive_or_trashed,
        count(m.tour_id) FILTER (WHERE r.source_status='active' AND r.deleted_at IS NULL) master,
        count(*) FILTER (WHERE r.source_status='active' AND r.deleted_at IS NULL AND m.tour_id IS NULL
            AND EXISTS (SELECT 1 FROM silver_aa_internal.review_queue q WHERE q.tour_id=r.tour_id AND q.review_status='pending')) review,
        count(*) FILTER (WHERE r.source_status='active' AND r.deleted_at IS NULL
            AND NOT EXISTS (SELECT 1 FROM silver_aa_internal.generated_content g WHERE g.tour_id=r.tour_id)) not_run,
        count(*) FILTER (WHERE r.source_status='active' AND r.deleted_at IS NULL
            AND EXISTS (SELECT 1 FROM acp_contract.v_active_tour_atoms a WHERE a.tour_id=r.tour_id)) atomized,
        round(avg(m.quality_score) FILTER (WHERE r.source_status='active'),2) avg_master_score,
        (SELECT count(*) FROM silver_aa_internal.generated_content g JOIN r r2 ON r2.tour_id=g.tour_id WHERE r2.country=r.country AND g.created_at>=$1) versions_since,
        (SELECT min(g.created_at)::date FROM silver_aa_internal.generated_content g JOIN r r2 ON r2.tour_id=g.tour_id WHERE r2.country=r.country AND g.created_at>=$1) first_run,
        (SELECT max(g.created_at)::date FROM silver_aa_internal.generated_content g JOIN r r2 ON r2.tour_id=g.tour_id WHERE r2.country=r.country AND g.created_at>=$1) last_run
      FROM r LEFT JOIN m ON m.tour_id=r.tour_id GROUP BY r.country ORDER BY active DESC""", SINCE)
    OUT["countries"] = [dict(x) for x in A]
    # per-country model of master + versions per master tour + judge dist
    B = await c.fetch("""
      SELECT rt.country, g.model_editorial, g.metadata->'judge'->>'judge_score' js, g.fix_pass_applied,
        (SELECT count(*) FROM silver_aa_internal.generated_content g2 WHERE g2.tour_id=p.tour_id AND g2.created_at>=$1) nver,
        (SELECT count(*) FROM acp_contract.v_active_tour_atoms a WHERE a.tour_id=p.tour_id) atoms
      FROM (SELECT DISTINCT ON (tour_id) * FROM gold_aa_internal.published_tours WHERE master_status='active' ORDER BY tour_id, published_at DESC) p
      JOIN silver_aa_internal.generated_content g ON g.id=p.generated_content_id
      JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=p.tour_id WHERE rt.source_status='active'""", SINCE)
    mm = defaultdict(lambda: {"models": Counter(), "judge": Counter(), "versions": Counter(), "fix_pass": 0, "atoms": []})
    for x in B:
        d = mm[x["country"]]; d["models"][("sonnet" if "sonnet" in (x["model_editorial"] or "") else "haiku" if "haiku" in (x["model_editorial"] or "") else x["model_editorial"] or "?")] += 1
        if x["js"]: d["judge"][round(float(x["js"]))] += 1
        d["versions"][min(x["nver"], 4)] += 1; d["fix_pass"] += 1 if x["fix_pass_applied"] else 0; d["atoms"].append(x["atoms"])
    OUT["master_detail"] = {k: {"models": dict(v["models"]), "judge": dict(sorted(v["judge"].items())), "versions_since_0110(4=4+)": dict(sorted(v["versions"].items())),
                                "fix_pass": v["fix_pass"], "atoms_min_med_max": [min(v["atoms"]), sorted(v["atoms"])[len(v["atoms"])//2], max(v["atoms"])] if v["atoms"] else None,
                                "atoms_total": sum(v["atoms"])} for k, v in mm.items()}
    # C. failure codes: first evaluation per gc vs latest gc per tour (since 01/10)
    Q = await c.fetch("""SELECT rt.country, q.failure_codes, q.brand_audit_status, q.score_overall, q.evaluated_at, g.tour_id, g.created_at
        FROM silver_aa_internal.quality_scores q JOIN silver_aa_internal.generated_content g ON g.id=q.generated_content_id
        JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=g.tour_id WHERE q.evaluated_at >= $1""", SINCE)
    codes_all = Counter(); codes_by_country = defaultdict(Counter); audit = Counter(); n_eval = 0
    latest = {}
    for x in Q:
        n_eval += 1
        for k in set(j(x["failure_codes"])):
            codes_all[k] += 1; codes_by_country[x["country"]][k] += 1
        audit[x["brand_audit_status"]] += 1
        if x["tour_id"] not in latest or x["evaluated_at"] > latest[x["tour_id"]]["evaluated_at"]:
            latest[x["tour_id"]] = x
    OUT["evaluations_since"] = n_eval
    OUT["codes_all_evaluations"] = codes_all.most_common(25)
    OUT["brand_audit_status_all"] = dict(audit)
    OUT["codes_by_country"] = {k: v.most_common(8) for k, v in codes_by_country.items()}
    lc = Counter()
    for x in latest.values():
        lc.update(set(j(x["failure_codes"])))
    OUT["codes_latest_version_per_tour"] = lc.most_common(20)
    OUT["tours_evaluated"] = len(latest)
    # D. review queue history since 01/10
    R = await c.fetch("""SELECT rt.country, q.review_status::text st, count(*) n FROM silver_aa_internal.review_queue q
        JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=q.tour_id WHERE q.created_at >= $1 GROUP BY 1,2""", SINCE)
    rv = defaultdict(dict)
    for x in R: rv[x["country"]][x["st"]] = x["n"]
    OUT["review_queue_since"] = rv
    pend = await c.fetch("""SELECT rt.country, q.failure_summary FROM silver_aa_internal.review_queue q JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=q.tour_id
        WHERE q.review_status='pending' AND rt.source_status='active'
          AND NOT EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=q.tour_id AND p.master_status='active')""")
    pc = defaultdict(Counter)
    for x in pend:
        s = x["failure_summary"] or ""
        k = ("low_quality" if "low_quality" in s else "forbidden" if "FORBIDDEN_WORD" in s else
             "seo_length" if any(t in s for t in ("SEO_META_TOO_LONG", "META_TOO_SHORT", "SEO_TITLE_TOO_LONG")) else
             "grounding/manual" if ("UNSUPPORTED_NUMBER" in s or "manual_check" in s) else "other")
        pc[x["country"]][k] += 1
    OUT["pending_review_by_cause"] = {k: dict(v) for k, v in pc.items()}
    # E. atoms + A3 graph
    at = await c.fetchrow("""SELECT count(*) n, count(DISTINCT tour_id) tours, count(*) FILTER (WHERE is_empty_marker) empty,
        count(*) FILTER (WHERE itinerary_day IS NULL) no_day, count(*) FILTER (WHERE coalesce(evidence,'')='') no_evidence,
        count(*) FILTER (WHERE coalesce(place,'')='') no_place, count(*) FILTER (WHERE coalesce(action,'')='') no_action,
        round(avg(length(text))) avg_len FROM acp_contract.v_active_tour_atoms""")
    OUT["atoms_active"] = dict(at)
    OUT["atoms_all_rows"] = await c.fetchval("SELECT count(*) FROM acp_contract.tour_atoms")
    OUT["atoms_deleted_flag"] = await c.fetchval("SELECT count(*) FROM acp_contract.tour_atoms WHERE deleted")
    OUT["atom_activity_type"] = Counter({x[0] or "(null)": x[1] for x in await c.fetch("SELECT activity_type, count(*) FROM acp_contract.v_active_tour_atoms GROUP BY 1")}).most_common(12)
    OUT["atom_distinctiveness"] = {x[0]: x[1] for x in await c.fetch("SELECT distinctiveness, count(*) FROM acp_contract.v_active_tour_atoms GROUP BY 1")}
    OUT["atom_owner_scope"] = {x[0]: x[1] for x in await c.fetch("SELECT owner_scope, count(*) FROM acp_contract.v_active_tour_atoms GROUP BY 1")}
    OUT["atoms_by_country"] = {x[0]: [x[1], x[2]] for x in await c.fetch("""SELECT rt.country, count(*), count(DISTINCT a.tour_id) FROM acp_contract.v_active_tour_atoms a
        JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=a.tour_id GROUP BY 1""")}
    # atoms with a day beyond the tour's own day count (A3-1 sanity)
    words = all_forbidden(j(await c.fetchval("""SELECT forbidden_words FROM shared.tenant_brand_rules WHERE tenant_id='00000000-0000-0000-0000-000000000001'::uuid AND is_active ORDER BY (brand_name='default') DESC, version DESC LIMIT 1""")))
    atxt = await c.fetch("SELECT text FROM acp_contract.v_active_tour_atoms")
    OUT["atoms_with_forbidden_word"] = sum(1 for x in atxt if any(has_word(x["text"] or "", w) for w in words))
    seg = await c.fetchrow("""SELECT (SELECT count(*) FROM acp_contract.atom_segment) segments,
        (SELECT count(*) FROM acp_contract.atom_segment_member) members,
        (SELECT count(DISTINCT segment_id) FROM acp_contract.atom_segment_member) segments_with_members,
        (SELECT count(*) FROM acp_contract.route WHERE superseded_at IS NULL) routes_current,
        (SELECT count(DISTINCT tour_id) FROM acp_contract.route WHERE superseded_at IS NULL) tours_with_route,
        (SELECT count(*) FROM acp_contract.hub) hubs,
        (SELECT count(*) FROM acp_contract.atom_ranking) ranking_rows,
        (SELECT count(*) FROM acp_contract.atom_ranking WHERE excluded_reason IS NOT NULL) ranking_excluded,
        (SELECT count(*) FROM acp_contract.atom_segment WHERE questions_count > 0) segments_with_questions,
        (SELECT count(*) FROM acp_contract.search_demand) search_demand_rows""")
    OUT["a3_graph"] = dict(seg)
    seg_sz = await c.fetch("SELECT n, count(*) FROM (SELECT segment_id, count(*) n FROM acp_contract.atom_segment_member GROUP BY 1) s GROUP BY n ORDER BY n")
    OUT["segment_size_dist"] = [(x[0], x[1]) for x in seg_sz][:15]
    OUT["ranking_excluded_reasons"] = {x[0]: x[1] for x in await c.fetch("SELECT excluded_reason, count(*) FROM acp_contract.atom_ranking WHERE excluded_reason IS NOT NULL GROUP BY 1")}
    # F. jobs
    Jb = await c.fetch("""SELECT kind, status, count(*) n, round(avg(extract(epoch FROM finished_at-started_at))::numeric) avg_s,
        round(percentile_cont(0.9) WITHIN GROUP (ORDER BY extract(epoch FROM finished_at-started_at))::numeric) p90_s, round(sum(cost_usd)::numeric,2) cost
        FROM shared.job WHERE created_at >= $1 GROUP BY 1,2 ORDER BY 1,2""", SINCE)
    OUT["jobs"] = [dict(x) for x in Jb]
    OUT["job_errors"] = [dict(x) for x in await c.fetch("""SELECT kind, left(coalesce(error,''),140) err, count(*) n FROM shared.job WHERE created_at >= $1 AND status IN ('failed','cancelled','stopped_budget')
        GROUP BY 1,2 ORDER BY n DESC LIMIT 15""", SINCE)]
    OUT["pipeline_runs_by_day"] = [(str(x[0]), x[1], x[2]) for x in await c.fetch("""SELECT created_at::date, kind, count(*) FROM shared.job WHERE created_at >= $1
        AND kind IN ('s1_rewrite','a3_atomize') GROUP BY 1,2 ORDER BY 1,2""", SINCE)]
    # G. cost
    OUT["llm_cost_by_stage"] = [(x[0], x[1], x[2], float(x[3] or 0)) for x in await c.fetch("""SELECT stage, model, count(*), round(sum(cost_usd)::numeric,3)
        FROM shared.llm_call_log WHERE created_at >= $1 GROUP BY 1,2 ORDER BY 4 DESC NULLS LAST LIMIT 30""", SINCE)]
    OUT["llm_cost_total"] = float(await c.fetchval("SELECT coalesce(sum(cost_usd),0) FROM shared.llm_call_log WHERE created_at >= $1", SINCE))
    OUT["llm_cost_by_day"] = [(str(x[0]), float(x[1] or 0)) for x in await c.fetch("SELECT created_at::date, round(sum(cost_usd)::numeric,2) FROM shared.llm_call_log WHERE created_at >= $1 GROUP BY 1 ORDER BY 1", SINCE)]
    OUT["dfs_cost"] = [dict(x) for x in await c.fetch("""SELECT endpoint, count(*) n, count(*) FILTER (WHERE cache_hit) cache_hits, round(sum(cost_usd)::numeric,3) cost
        FROM shared.dfs_call_log WHERE created_at >= $1 GROUP BY 1 ORDER BY cost DESC NULLS LAST""", SINCE)]
    OUT["sonnet_s1_generate_by_day"] = [(str(x[0]), x[1]) for x in await c.fetch("""SELECT created_at::date, count(*) FROM shared.llm_call_log WHERE stage='s1_generate' AND model ILIKE '%sonnet%' AND created_at >= $1 GROUP BY 1 ORDER BY 1""", SINCE)]
    # H. Jev
    OUT["jev"] = [dict(x) for x in await c.fetch("""SELECT stage, mode, zone, count(*) n, count(*) FILTER (WHERE error IS NOT NULL) errors, count(*) FILTER (WHERE cached) cached
        FROM shared.decision_log WHERE created_at >= $1 GROUP BY 1,2,3 ORDER BY 1,2,3""", SINCE)]
    # I. platform forbidden in masters (should be 0 after S218)
    pub = await c.fetch("""SELECT DISTINCT ON (p.tour_id) p.aa_name, p.aa_subtitle, p.aa_summary, p.aa_description, p.aa_highlights, p.aa_itineraries, p.seo_title, p.seo_meta
        FROM gold_aa_internal.published_tours p JOIN silver_aa_internal.raw_tours rt ON rt.tour_id=p.tour_id WHERE p.master_status='active' AND rt.source_status='active' ORDER BY p.tour_id, p.published_at DESC""")
    OUT["masters_with_forbidden"] = sum(1 for m in pub if any(has_word(copy_text([m[k] for k in m.keys()]), w) for w in words))
    OUT["masters_meta_out_of_band"] = sum(1 for m in pub if m["seo_meta"] and not (140 <= len(m["seo_meta"]) <= 155))
    boto3.client("s3", region_name="us-west-1").put_object(Bucket="aa-cis-bronze-005097885195", Key="scripts/s218_audit.json", Body=json.dumps(OUT, default=str, ensure_ascii=False, indent=1).encode())
    print(json.dumps(OUT, default=str, ensure_ascii=False, indent=1))
    await c.close()
asyncio.run(main())
