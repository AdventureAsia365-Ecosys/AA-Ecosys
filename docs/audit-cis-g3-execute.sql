-- G3 EXECUTE (AA-598) — transaction thật. Chạy: psql ... -v ON_ERROR_STOP=1 -f này
-- ON_ERROR_STOP=1 + BEGIN/COMMIT: bất kỳ lỗi nào → toàn bộ rollback tự động.
\set ON_ERROR_STOP on
BEGIN;

-- Tenant / social (con → cha)
DELETE FROM acp_shared.publish_log;
DELETE FROM acp_shared.content_metric_snapshot;
DELETE FROM acp_deliver.pieces;
DELETE FROM acp_deliver.packets;
DELETE FROM acp_deliver.tenant_tour_pages;
DELETE FROM acp_shared.content_piece;
DELETE FROM acp_shared.angle_gate_option;
DELETE FROM acp_shared.angle_gate_request;
DELETE FROM acp_shared.subject;
DELETE FROM acp_shared.acp_v2_slots;
DELETE FROM acp_shared.acp_v2_runs;
DELETE FROM acp_shared.tenant_atom_state;
DELETE FROM acp_contract.route_pick;

-- Atom / segment / route / hub (con → cha)
DELETE FROM acp_contract.atom_ranking;
DELETE FROM acp_contract.route;
DELETE FROM acp_contract.hub;
DELETE FROM acp_contract.atom_segment_member;
DELETE FROM acp_contract.atom_segment_alias;
DELETE FROM acp_contract.atom_segment;
DELETE FROM acp_contract.atomize_day_fingerprint;
DELETE FROM acp_contract.s1_from_atom_runs;
DELETE FROM acp_contract.tour_atoms;

-- Master content (con → cha) — review_queue trỏ FK tới tenant_tour_versions VÀ generated_content
-- nên phải xóa TRƯỚC; tenant_tour_versions trỏ published_tours; published_tours trỏ generated_content.
DELETE FROM silver_aa_internal.review_queue;
DELETE FROM silver_aa_internal.quality_scores;
DELETE FROM silver_aa_internal.seo_context;
DELETE FROM gold_aa_internal.tenant_tour_versions;
DELETE FROM gold_aa_internal.published_tours;
DELETE FROM silver_aa_internal.generated_content;

-- Planning (nhóm D) — circular FK: quarter_plan.current_version_id <-> quarter_plan_version.quarter_plan_id
-- Gỡ con trỏ current_version trước, rồi xóa version, rồi quarter_plan.
UPDATE acp_shared.quarter_plan SET current_version_id = NULL;
DELETE FROM acp_shared.quarter_plan_version;
DELETE FROM acp_shared.quarter_plan;
DELETE FROM acp_shared.year_plan;

-- Reset raw_tours (KHÔNG xóa row)
UPDATE silver_aa_internal.raw_tours SET pipeline_status = 'ingested' WHERE pipeline_status <> 'ingested';

-- DROP bảng dead cô lập
DROP TABLE acp_shared.unknown_ledger;

-- Post-delete verify (phải = 0)
\echo '===== POST-DELETE (phai = 0) ====='
SELECT 'tour_atoms' AS tbl, count(*) FROM acp_contract.tour_atoms
UNION ALL SELECT 'published_tours', count(*) FROM gold_aa_internal.published_tours
UNION ALL SELECT 'generated_content', count(*) FROM silver_aa_internal.generated_content
UNION ALL SELECT 'content_piece', count(*) FROM acp_shared.content_piece
UNION ALL SELECT 'subject', count(*) FROM acp_shared.subject
UNION ALL SELECT 'atom_segment', count(*) FROM acp_contract.atom_segment
UNION ALL SELECT 'route', count(*) FROM acp_contract.route
UNION ALL SELECT 'tenant_tour_versions', count(*) FROM gold_aa_internal.tenant_tour_versions
UNION ALL SELECT 'acp_deliver.pieces', count(*) FROM acp_deliver.pieces
UNION ALL SELECT 'acp_v2_slots', count(*) FROM acp_shared.acp_v2_slots;

\echo '===== raw_tours status (phai deu ingested = 793) ====='
SELECT pipeline_status, count(*) FROM silver_aa_internal.raw_tours GROUP BY 1 ORDER BY 2 DESC;

\echo '===== GIU nguyen (phai khac 0) ====='
SELECT 'raw_tours' AS keep, count(*) FROM silver_aa_internal.raw_tours
UNION ALL SELECT 'destinations', count(*) FROM shared.destinations
UNION ALL SELECT 'search_demand', count(*) FROM acp_contract.search_demand
UNION ALL SELECT 'tenants', count(*) FROM shared.tenants;

COMMIT;
