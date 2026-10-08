"""S218 reconciliation S0 -> S1 -> Master -> atoms/segments, per country, plus status-consistency checks. Read-only."""
import asyncio, json, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
MASTER = "00000000-0000-0000-0000-000000000001"
async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    out = {}
    out["raw_by_tenant"] = [dict(r) for r in await c.fetch("SELECT tenant_id::text, count(*) n FROM silver_aa_internal.raw_tours GROUP BY 1")]
    out["sources"] = [dict(r) for r in await c.fetch("""SELECT rs.filename, rs.row_count, rs.parsed_at::date d,
        count(t.tour_id) raw_rows, count(t.tour_id) FILTER (WHERE t.source_status='active' AND t.deleted_at IS NULL) active,
        string_agg(DISTINCT coalesce(t.country,'<null>'), ',') countries
        FROM silver_aa_internal.raw_sources rs LEFT JOIN silver_aa_internal.raw_tours t ON t.source_id=rs.id
        GROUP BY rs.id ORDER BY rs.parsed_at""")]
    out["raw_no_source"] = await c.fetchval("SELECT count(*) FROM silver_aa_internal.raw_tours WHERE source_id IS NULL")
    # per-country funnel
    out["funnel"] = [dict(r) for r in await c.fetch(f"""
      WITH m AS (SELECT tour_id, count(*) FILTER (WHERE master_status='active') act, count(*) n FROM gold_aa_internal.published_tours GROUP BY 1),
           g AS (SELECT tour_id, count(*) n FROM silver_aa_internal.generated_content GROUP BY 1),
           q AS (SELECT DISTINCT tour_id FROM silver_aa_internal.review_queue WHERE review_status='pending'),
           a AS (SELECT tour_id, count(*) n FROM acp_contract.v_active_tour_atoms GROUP BY 1),
           s AS (SELECT DISTINCT ta.tour_id FROM acp_contract.atom_segment_member asm JOIN acp_contract.v_active_tour_atoms ta ON ta.atom_id=asm.atom_id),
           k AS (SELECT DISTINCT tour_id FROM acp_contract.atom_ranking),
           r AS (SELECT DISTINCT tour_id FROM acp_contract.route WHERE superseded_at IS NULL)
      SELECT coalesce(t.country,'<null>') country, count(*) raw_all,
        count(*) FILTER (WHERE t.source_status='active' AND t.deleted_at IS NULL) active,
        count(*) FILTER (WHERE t.source_status='trashed') trashed,
        count(*) FILTER (WHERE t.source_status='superseded') superseded,
        count(*) FILTER (WHERE t.source_status='active' AND t.deleted_at IS NULL AND trim(coalesce(t.src_itineraries,''))='') active_no_itin,
        count(*) FILTER (WHERE t.pipeline_status='ingested' AND t.source_status='active' AND t.deleted_at IS NULL AND trim(coalesce(t.src_itineraries,''))<>'') s0_ready,
        count(*) FILTER (WHERE t.source_status='active' AND t.deleted_at IS NULL AND g.n IS NOT NULL) written,
        count(*) FILTER (WHERE m.act > 0) master_active,
        count(*) FILTER (WHERE m.act > 1) master_dup_active,
        count(*) FILTER (WHERE q.tour_id IS NOT NULL AND coalesce(m.act,0)=0) review_pending,
        count(*) FILTER (WHERE a.n IS NOT NULL) with_atoms, coalesce(sum(a.n),0) atoms,
        count(*) FILTER (WHERE s.tour_id IS NOT NULL) with_segment,
        count(*) FILTER (WHERE k.tour_id IS NOT NULL) ranked,
        count(*) FILTER (WHERE r.tour_id IS NOT NULL) with_route
      FROM silver_aa_internal.raw_tours t
      LEFT JOIN m ON m.tour_id=t.tour_id LEFT JOIN g ON g.tour_id=t.tour_id LEFT JOIN q ON q.tour_id=t.tour_id
      LEFT JOIN a ON a.tour_id=t.tour_id LEFT JOIN s ON s.tour_id=t.tour_id LEFT JOIN k ON k.tour_id=t.tour_id LEFT JOIN r ON r.tour_id=t.tour_id
      WHERE t.tenant_id='{MASTER}'
      GROUP BY 1 ORDER BY 2 DESC""")]
    out["pipeline_status_x_outcome"] = [dict(r) for r in await c.fetch(f"""
      SELECT t.pipeline_status::text ps, t.source_status::text ss,
        CASE WHEN EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=t.tour_id AND p.master_status='active') THEN 'master'
             WHEN EXISTS (SELECT 1 FROM silver_aa_internal.review_queue q WHERE q.tour_id=t.tour_id AND q.review_status='pending') THEN 'review'
             WHEN EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=t.tour_id) THEN 'master_inactive_or_trashed'
             WHEN EXISTS (SELECT 1 FROM silver_aa_internal.generated_content g WHERE g.tour_id=t.tour_id) THEN 'written_no_outcome'
             ELSE 'not_written' END outcome, count(*) n
      FROM silver_aa_internal.raw_tours t WHERE t.tenant_id='{MASTER}' GROUP BY 1,2,3 ORDER BY 1,2,3""")]
    checks = {}
    async def chk(name, sql):
        rows = await c.fetch(sql)
        checks[name] = {"n": len(rows), "sample": [dict(r) for r in rows[:15]]}
    await chk("ready_but_master_active", f"""SELECT t.tour_id::text, t.country, t.src_name, t.pipeline_status::text FROM silver_aa_internal.raw_tours t
        WHERE t.tenant_id='{MASTER}' AND t.pipeline_status='ingested' AND EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=t.tour_id AND p.master_status='active')""")
    await chk("ready_but_written", f"""SELECT t.tour_id::text, t.country, t.src_name FROM silver_aa_internal.raw_tours t
        WHERE t.tenant_id='{MASTER}' AND t.pipeline_status='ingested' AND t.source_status='active' AND EXISTS (SELECT 1 FROM silver_aa_internal.generated_content g WHERE g.tour_id=t.tour_id)""")
    await chk("master_active_not_published_status", f"""SELECT t.tour_id::text, t.country, t.src_name, t.pipeline_status::text FROM silver_aa_internal.raw_tours t
        WHERE t.tenant_id='{MASTER}' AND t.pipeline_status <> 'published' AND EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=t.tour_id AND p.master_status='active')""")
    await chk("published_status_no_active_master", f"""SELECT t.tour_id::text, t.country, t.src_name, t.source_status::text,
        (SELECT string_agg(DISTINCT p.master_status::text, ',') FROM gold_aa_internal.published_tours p WHERE p.tour_id=t.tour_id) ms,
        EXISTS (SELECT 1 FROM silver_aa_internal.review_queue q WHERE q.tour_id=t.tour_id AND q.review_status='pending') in_review
        FROM silver_aa_internal.raw_tours t
        WHERE t.tenant_id='{MASTER}' AND t.pipeline_status='published' AND NOT EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=t.tour_id AND p.master_status='active')""")
    await chk("master_active_source_not_active", f"""SELECT t.tour_id::text, t.country, t.src_name, t.source_status::text FROM silver_aa_internal.raw_tours t
        WHERE t.tenant_id='{MASTER}' AND (t.source_status <> 'active' OR t.deleted_at IS NOT NULL) AND EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=t.tour_id AND p.master_status='active')""")
    await chk("review_pending_and_master_active", f"""SELECT DISTINCT t.tour_id::text, t.country, t.src_name FROM silver_aa_internal.raw_tours t
        JOIN silver_aa_internal.review_queue q ON q.tour_id=t.tour_id AND q.review_status='pending'
        WHERE EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=t.tour_id AND p.master_status='active')""")
    await chk("review_pending_multiple_rows", """SELECT tour_id::text, count(*) n FROM silver_aa_internal.review_queue WHERE review_status='pending' GROUP BY 1 HAVING count(*)>1""")
    await chk("written_no_master_no_review", f"""SELECT t.tour_id::text, t.country, t.src_name, t.pipeline_status::text FROM silver_aa_internal.raw_tours t
        WHERE t.tenant_id='{MASTER}' AND t.source_status='active' AND t.deleted_at IS NULL
          AND EXISTS (SELECT 1 FROM silver_aa_internal.generated_content g WHERE g.tour_id=t.tour_id)
          AND NOT EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=t.tour_id AND p.master_status='active')
          AND NOT EXISTS (SELECT 1 FROM silver_aa_internal.review_queue q WHERE q.tour_id=t.tour_id AND q.review_status='pending')""")
    await chk("master_active_no_atoms", f"""SELECT t.tour_id::text, t.country, t.src_name FROM silver_aa_internal.raw_tours t
        WHERE EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=t.tour_id AND p.master_status='active')
          AND NOT EXISTS (SELECT 1 FROM acp_contract.v_active_tour_atoms a WHERE a.tour_id=t.tour_id)""")
    await chk("master_active_dup_rows", """SELECT tour_id::text, count(*) n FROM gold_aa_internal.published_tours WHERE master_status='active' GROUP BY 1 HAVING count(*)>1""")
    await chk("master_score_mismatch", """SELECT p.tour_id::text, p.quality_score, qs.score_overall FROM gold_aa_internal.published_tours p
        JOIN silver_aa_internal.quality_scores qs ON qs.id=p.quality_score_id WHERE p.master_status='active' AND p.quality_score IS DISTINCT FROM qs.score_overall""")
    await chk("master_below_7", """SELECT p.tour_id::text, p.quality_score FROM gold_aa_internal.published_tours p WHERE p.master_status='active' AND p.quality_score < 7""")
    await chk("atoms_on_inactive_masters", """SELECT ta.tour_id::text, count(*) n FROM acp_contract.tour_atoms ta
        WHERE ta.owner_scope='platform' AND NOT ta.deleted AND NOT EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=ta.tour_id AND p.master_status='active') GROUP BY 1""")
    await chk("ranking_rows_for_non_active_tours", """SELECT DISTINCT k.tour_id::text FROM acp_contract.atom_ranking k
        WHERE NOT EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=k.tour_id AND p.master_status='active')""")
    await chk("route_for_non_active_tours", """SELECT DISTINCT r.tour_id::text FROM acp_contract.route r WHERE r.superseded_at IS NULL
        AND NOT EXISTS (SELECT 1 FROM gold_aa_internal.published_tours p WHERE p.tour_id=r.tour_id AND p.master_status='active')""")
    await chk("pipeline_runs_stuck", """SELECT id::text, status::text, tours_total, tours_passed, started_at::date FROM shared.pipeline_runs WHERE status::text NOT IN ('completed','failed','cancelled')""")
    out["checks"] = checks
    out["table_counts"] = {t: await c.fetchval(f"SELECT count(*) FROM {t}") for t in [
        "silver_aa_internal.raw_sources", "silver_aa_internal.raw_tours", "silver_aa_internal.generated_content", "silver_aa_internal.quality_scores",
        "silver_aa_internal.seo_context", "silver_aa_internal.review_queue", "gold_aa_internal.published_tours", "acp_contract.tour_atoms",
        "acp_contract.atom_segment", "acp_contract.atom_segment_member", "acp_contract.atom_ranking", "acp_contract.route", "acp_contract.hub", "shared.pipeline_runs"]}
    out["review_status_counts"] = [dict(r) for r in await c.fetch("SELECT review_status::text, count(*) FROM silver_aa_internal.review_queue GROUP BY 1")]
    out["master_status_counts"] = [dict(r) for r in await c.fetch("SELECT master_status::text, count(*), count(DISTINCT tour_id) tours FROM gold_aa_internal.published_tours GROUP BY 1")]
    s = json.dumps(out, default=str, indent=1)
    boto3.client("s3", region_name="us-west-1").put_object(Bucket="aa-cis-bronze-005097885195", Key="scripts/s218_recon.json", Body=s.encode())
    print(s)
    await c.close()
asyncio.run(main())
