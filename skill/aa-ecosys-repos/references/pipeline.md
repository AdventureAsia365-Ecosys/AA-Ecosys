# Pipeline A0–A4 / T0–T11 — stage → code → bảng

Mỗi stage một dòng, đường dẫn trong `AA-CIS-App`. Không ghi trạng thái "đang làm" (thuộc Linear/memory) và không ghi
model (route của Model Gateway, `shared.llm_role_config`). Tên bảng đầy đủ + cột: `docs/architecture/db-schema-reference.md`.

| Stage | Tier | Code chính | Bảng ghi | Ghi chú |
|---|---|---|---|---|
| A0 Ingest | admin | `services/ingestion/handler.py`, job `s1_batch_ingest` | `silver_aa_internal.raw_tours` | Gate Jev ingest |
| A1 Generic rewrite | admin | `services/content_generation/graph.py` (writer v2: `s1_writer_v2_live.py`), job `s1_rewrite` | `silver_aa_internal.generated_content` | DFS keyword (`s1_seo_prefetch`), grounding |
| A2 QA / review | admin | `services/content_generation/flag_fix_node.py`, `brand_audit_node.py` | `silver_aa_internal.review_queue` | ≤2 vòng repair |
| A3 Master | admin | `services/export/handler.py` | `gold_aa_internal.published_tours` | `master_status` điều khiển atom |
| Atomize | admin | `services/acp_contract/a3_atomize.py` + `services/acp_shared/atom_extraction.py`, job `a3_atomize` | `acp_contract.tour_atoms` | platform-wide; đọc qua `acp_contract.v_active_tour_atoms` |
| Segment / Score / Route / Hub | admin | `services/acp_contract/` (`segment_matching.py`, `atom_ranking.py`, `route_detection.py`), điều phối bởi `services/recompute/stages.py`, job `recompute` | `acp_contract.*` | platform-wide (một lần cho cả pool, scope `tour_id`) |
| Research / Search demand | admin | `services/jobs/segment_research_job.py` | `acp_contract.search_demand` (cache dùng chung) | tái dùng theo TTL, có cost guard |
| A4 Oversight | admin | trang `atom-curation` (Social Content) | — | hậu kiểm, không chặn |
| T0 Brand | tenant | `services/brand_intake/` (`brief.py`, `markets.py`) | `shared.tenant_brand_rules` | kèm đối thủ |
| T1–T4 Rewrite → QA → Pool | tenant | `services/jobs/t2_rewrite_job.py` | `gold_aa_internal.tenant_tour_versions` | T3 auto-pass + badge |
| Slate | tenant | `services/acp_shared/slate.py`, job `t7_slate` | `acp_shared.subject` | Bar theo kênh + Debate |
| Goal / Angle | tenant | `services/acp_angle_gate/`, job `t8_angles` | `acp_shared.angle_gate_request`, `angle_gate_option` | chọn 1/3 angle |
| Write | tenant | `services/jobs/t9_write_job.py` | `acp_shared.content_piece` | theo cấu trúc từng kênh |
| Gate F1–F10 | tenant | `services/acp_shared/grounding.py` + gate checks (`services/acp_content_writing/`) | `acp_shared.content_piece.gate_ledger` | severity block/warn/note |
| Publish | tenant | `api/routers/v1_publish.py`, `services/acp_publish/` (idempotency) | `acp_shared.publish_log` | WordPress + kênh social |
