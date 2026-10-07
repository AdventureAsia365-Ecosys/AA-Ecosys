# Pipeline A0–A4 / T0–T11 — stage → code → bảng

Mỗi stage một dòng. Không ghi trạng thái "đang làm" (thuộc Linear/memory).

| Stage | Tier | Code chính | Bảng ghi | Ghi chú |
|---|---|---|---|---|
| A0 Ingest | admin | `services/ingestion/handler.py` | `silver_aa_internal.raw_tours` | Gate Jev ingest |
| A1 Generic rewrite | admin | `services/content_generation/graph.py` | `generated_content` | DFS keyword, grounding |
| A2 QA / review | admin | `services/content_generation/flag_fix_node.py`, `brand_audit_node.py` | `review_queue` | ≤2 vòng repair |
| A3 Master | admin | `services/export/handler.py` | `gold_aa_internal.published_tours` | master_status điều khiển atom |
| Atomize | admin | `services/acp_shared/atom_extraction.py` | `acp_contract.tour_atoms` | platform-wide; đọc qua `v_active_tour_atoms` |
| Segment / Score / Route / Hub | admin | `services/acp_shared/` (segment, ranking, route_detection) | `acp_contract.*` | platform-wide (một lần cho cả pool, scope `tour_id`) |
| Research / Search demand | admin | `services/jobs/segment_research_job.py` | cache `search_demand` dùng chung | tái dùng theo TTL |
| A4 Oversight | admin | trang Social Content | — | hậu kiểm, không chặn |
| T0 Brand | tenant | `services/acp_brand_brief_parser/` | `tenant_brand_rules` | kèm đối thủ |
| T1–T4 Rewrite → QA → Pool | tenant | `services/jobs/t2_rewrite_job.py` | `tenant_tour_versions` | T3 auto-pass + badge |
| Slate | tenant | `services/acp_shared/slate.py` | `acp_shared.subject` | Bar theo kênh + Debate |
| Goal / Angle | tenant | `services/acp_shared/` (angle gate) | `angle_gate_*` | chọn 1/3 angle |
| Write | tenant | `services/jobs/t9_write_job.py` | `content_piece` | theo cấu trúc từng kênh |
| Gate F1–F10 | tenant | `services/acp_shared/grounding.py` + gate checks | `content_piece.gate_ledger` | severity block/warn/note |
| Publish | tenant | `api/routers/v1_publish.py` | `publish_log` | WordPress + 6 kênh; idempotency còn ở AA-726 |
