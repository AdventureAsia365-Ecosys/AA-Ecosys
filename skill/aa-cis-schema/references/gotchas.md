# Bẫy DB AA-CIS

## Khoá và tên cột

- `silver_aa_internal.raw_tours` PK = `tour_id`.
- `gold_aa_internal.published_tours`: tên tour là `aa_name` (không phải `title`); không có `country` → JOIN `raw_tours` qua `tour_id`.
- `seo_context` không có `country` → JOIN `raw_tours`.
- `shared.schema_versions.version` là varchar → `ORDER BY applied_at`.
- `acp_v2_runs` / `acp_v2_slots`.`tenant_id` là TEXT.
- UUID khi `json.dumps` → `default=str`.

## Ngữ nghĩa dễ hiểu nhầm

- `review_queue.generated_content_id` nullable: luồng A1→A2 có giá trị, luồng T3 dùng `tenant_tour_version_id`. Query tìm "dòng mồ côi" phải loại trường hợp này.
- Review queue chỉ giữ bản lỗi mới nhất mỗi tour (cũ hơn = superseded). Tour đã publish → dòng review tự dismissed.
- `tour_atoms.distinctiveness` / `weight`: giá trị mặc định, không dùng để lọc hay rank (Score thật nằm ở `acp_contract.atom_ranking`).
- `atom_embedding` sinh lười theo thiết kế (chỉ atom vào shortlist PAA), không cần backfill.
- `shared.acp_runs` là tracker A0–A3 đang sống (khác `acp_shared.acp_runs` đã xoá).
- `acp_output_rules.source_hitl_id` không còn FK → có thể trỏ tới giá trị không tồn tại.

## LLM log

- `llm_call_log` ghi cả lời gọi shadow (cùng stage) và lời gọi lỗi (Jev fail-open vẫn ghi cost).
- Model thực sự quyết định: đọc route config + `llm_shadow_log`; quyết định Jev: `shared.decision_log.zone`.

## JOIN hay dùng

```sql
-- country cho published tour
SELECT pt.tour_id, pt.aa_name, rt.country
FROM gold_aa_internal.published_tours pt
JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = pt.tour_id;

-- chuỗi angle → piece → publish của một tenant
SELECT r.request_id, o.name AS angle, p.piece_id, p.status, pl.status AS publish_status, pl.external_url
FROM acp_shared.angle_gate_request r
LEFT JOIN acp_shared.angle_gate_option o ON o.request_id = r.request_id AND o.chosen
LEFT JOIN acp_shared.content_piece p ON p.angle_gate_request_id = r.request_id
LEFT JOIN acp_shared.publish_log pl ON pl.piece_id = p.piece_id
WHERE r.tenant_id = $1;
```
