-- ============================================================================
-- G3 — CIS Data Reset (AA-598)  |  S183, 2026-09-16
-- ============================================================================
-- Chạy qua SSM tunnel: psql -h 127.0.0.1 -p 15432 -U aa_cis_admin -d aa_cis_dev
-- BỌC TRANSACTION. Chạy DRY-RUN (phần 1) trước, xem count, rồi mới chạy phần 2 (BEGIN...).
--
-- Nguyên tắc: giữ raw_tours (chỉ reset pipeline_status), giữ config/cache
-- (search_demand, segment_research_log, destinations, facts, tenants, brand_rules,
--  tenant_config, competitor_index_cache, acp_output_rules, marketplace_portfolios,
--  raw_sources). Xóa DATA toàn bộ dẫn xuất A-series + T-series + N7/N8 (dead).
-- DROP: chỉ unknown_ledger (0 FK, 0 reader sống). Cụm N7 còn lại tách issue.
-- Thứ tự DELETE = con → cha theo FK graph thật (query pg_constraint 16/09).
-- ============================================================================

-- ############################################################################
-- PHẦN 1 — DRY RUN (read-only, in số row SẼ bị đụng). KHÔNG thay đổi gì.
-- ############################################################################
\echo '===== DRY RUN: số row sẽ XÓA / cập nhật ====='
SELECT 'publish_log' AS tbl, count(*) FROM acp_shared.publish_log
UNION ALL SELECT 'content_metric_snapshot', count(*) FROM acp_shared.content_metric_snapshot
UNION ALL SELECT 'acp_deliver.pieces', count(*) FROM acp_deliver.pieces
UNION ALL SELECT 'acp_deliver.packets', count(*) FROM acp_deliver.packets
UNION ALL SELECT 'acp_deliver.tenant_tour_pages', count(*) FROM acp_deliver.tenant_tour_pages
UNION ALL SELECT 'content_piece', count(*) FROM acp_shared.content_piece
UNION ALL SELECT 'angle_gate_option', count(*) FROM acp_shared.angle_gate_option
UNION ALL SELECT 'angle_gate_request', count(*) FROM acp_shared.angle_gate_request
UNION ALL SELECT 'subject', count(*) FROM acp_shared.subject
UNION ALL SELECT 'acp_v2_slots', count(*) FROM acp_shared.acp_v2_slots
UNION ALL SELECT 'acp_v2_runs', count(*) FROM acp_shared.acp_v2_runs
UNION ALL SELECT 'unknown_ledger (DROP)', count(*) FROM acp_shared.unknown_ledger
UNION ALL SELECT 'tenant_atom_state', count(*) FROM acp_shared.tenant_atom_state
UNION ALL SELECT 'route_pick', count(*) FROM acp_contract.route_pick
UNION ALL SELECT 'atom_ranking', count(*) FROM acp_contract.atom_ranking
UNION ALL SELECT 'route', count(*) FROM acp_contract.route
UNION ALL SELECT 'hub', count(*) FROM acp_contract.hub
UNION ALL SELECT 'atom_segment_member', count(*) FROM acp_contract.atom_segment_member
UNION ALL SELECT 'atom_segment_alias', count(*) FROM acp_contract.atom_segment_alias
UNION ALL SELECT 'atom_segment', count(*) FROM acp_contract.atom_segment
UNION ALL SELECT 'atomize_day_fingerprint', count(*) FROM acp_contract.atomize_day_fingerprint
UNION ALL SELECT 's1_from_atom_runs', count(*) FROM acp_contract.s1_from_atom_runs
UNION ALL SELECT 'tour_atoms', count(*) FROM acp_contract.tour_atoms
UNION ALL SELECT 'tenant_tour_versions', count(*) FROM gold_aa_internal.tenant_tour_versions
UNION ALL SELECT 'review_queue', count(*) FROM silver_aa_internal.review_queue
UNION ALL SELECT 'quality_scores', count(*) FROM silver_aa_internal.quality_scores
UNION ALL SELECT 'seo_context', count(*) FROM silver_aa_internal.seo_context
UNION ALL SELECT 'published_tours', count(*) FROM gold_aa_internal.published_tours
UNION ALL SELECT 'generated_content', count(*) FROM silver_aa_internal.generated_content
UNION ALL SELECT 'quarter_plan_version', count(*) FROM acp_shared.quarter_plan_version
UNION ALL SELECT 'quarter_plan', count(*) FROM acp_shared.quarter_plan
UNION ALL SELECT 'year_plan', count(*) FROM acp_shared.year_plan
UNION ALL SELECT 'raw_tours (UPDATE status, KHÔNG xóa)', count(*) FROM silver_aa_internal.raw_tours WHERE pipeline_status <> 'ingested'
ORDER BY 1;

-- ############################################################################
-- PHẦN 2 — RESET THẬT (transaction). Bỏ comment khối BEGIN..COMMIT khi Nghiệp duyệt.
-- ############################################################################
-- BEGIN;

-- --- Tenant / social (con → cha) ---
-- DELETE FROM acp_shared.publish_log;
-- DELETE FROM acp_shared.content_metric_snapshot;
-- DELETE FROM acp_deliver.pieces;
-- DELETE FROM acp_deliver.packets;
-- DELETE FROM acp_deliver.tenant_tour_pages;
-- DELETE FROM acp_shared.content_piece;
-- DELETE FROM acp_shared.angle_gate_option;
-- DELETE FROM acp_shared.angle_gate_request;
-- DELETE FROM acp_shared.subject;
-- DELETE FROM acp_shared.acp_v2_slots;
-- DELETE FROM acp_shared.acp_v2_runs;
-- DELETE FROM acp_shared.tenant_atom_state;
-- DELETE FROM acp_contract.route_pick;

-- --- Atom / segment / route / hub (con → cha) ---
-- DELETE FROM acp_contract.atom_ranking;
-- DELETE FROM acp_contract.route;
-- DELETE FROM acp_contract.hub;
-- DELETE FROM acp_contract.atom_segment_member;
-- DELETE FROM acp_contract.atom_segment_alias;
-- DELETE FROM acp_contract.atom_segment;
-- DELETE FROM acp_contract.atomize_day_fingerprint;
-- DELETE FROM acp_contract.s1_from_atom_runs;
-- DELETE FROM acp_contract.tour_atoms;

-- --- Master content (con → cha) — review_queue TRƯỚC tenant_tour_versions (FK) ---
-- DELETE FROM silver_aa_internal.review_queue;
-- DELETE FROM silver_aa_internal.quality_scores;
-- DELETE FROM silver_aa_internal.seo_context;
-- DELETE FROM gold_aa_internal.tenant_tour_versions;
-- DELETE FROM gold_aa_internal.published_tours;
-- DELETE FROM silver_aa_internal.generated_content;

-- --- Planning (nhóm D — Nghiệp chốt xóa) ---
-- DELETE FROM acp_shared.quarter_plan_version;
-- DELETE FROM acp_shared.quarter_plan;
-- DELETE FROM acp_shared.year_plan;

-- --- Reset raw_tours (KHÔNG xóa row) ---
-- UPDATE silver_aa_internal.raw_tours SET pipeline_status = 'ingested' WHERE pipeline_status <> 'ingested';

-- --- DROP bảng dead cô lập (0 FK, 0 reader sống) ---
-- DROP TABLE acp_shared.unknown_ledger;

-- --- KIỂM TRA sau khi xóa (count phải = 0 cho các bảng đã DELETE) ---
-- \echo '===== POST-DELETE verify (phải = 0) ====='
-- SELECT 'tour_atoms' AS tbl, count(*) FROM acp_contract.tour_atoms
-- UNION ALL SELECT 'published_tours', count(*) FROM gold_aa_internal.published_tours
-- UNION ALL SELECT 'generated_content', count(*) FROM silver_aa_internal.generated_content
-- UNION ALL SELECT 'content_piece', count(*) FROM acp_shared.content_piece
-- UNION ALL SELECT 'subject', count(*) FROM acp_shared.subject
-- UNION ALL SELECT 'atom_segment', count(*) FROM acp_contract.atom_segment;
-- \echo '===== raw_tours còn nguyên + status ingested ====='
-- SELECT pipeline_status, count(*) FROM silver_aa_internal.raw_tours GROUP BY 1 ORDER BY 2 DESC;
-- \echo '===== GIỮ nguyên (phải khác 0) ====='
-- SELECT 'raw_tours' AS keep, count(*) FROM silver_aa_internal.raw_tours
-- UNION ALL SELECT 'destinations', count(*) FROM shared.destinations
-- UNION ALL SELECT 'search_demand', count(*) FROM acp_contract.search_demand
-- UNION ALL SELECT 'tenants', count(*) FROM shared.tenants;

-- COMMIT;   -- <-- chỉ COMMIT khi count đúng; nếu sai: ROLLBACK;
