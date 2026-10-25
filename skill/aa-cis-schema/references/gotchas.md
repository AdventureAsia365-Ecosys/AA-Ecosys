# Bẫy DB dùng chung (CIS là chính)

Tên cột chính xác luôn đọc ở `docs/architecture/db-schema-reference.md`; file này chỉ giữ bẫy về ngữ nghĩa.

## Khoá và tên cột

- `silver_aa_internal.raw_tours` PK = `tour_id`; trạng thái raw ở `source_status` / `pipeline_status` / `review_status`
  / `lifecycle_stage` / `deleted_at` (không có `status`).
- `gold_aa_internal.published_tours`: tên tour là `aa_name` (không phải `title`); không có `country` → JOIN `raw_tours`
  qua `tour_id`. `published_at` là lần publish ĐẦU (giữ nguyên khi rewrite); lần publish/promote gần nhất xem `updated_at`.
- `seo_context` không có `country` → JOIN `raw_tours`.
- `silver_aa_internal.quality_scores` dùng `evaluated_at` (không `created_at`); bản được chấp nhận qua
  `published_tours.quality_score_id`.
- `shared.schema_versions.version` là varchar, chứa key mọi owner → `ORDER BY applied_at`.
- `tenant_id` không cùng kiểu ở mọi bảng (đa số uuid, vài bảng text như `acp_deliver.tenant_tour_pages`) → đọc kiểu cột
  trước khi cast.
- UUID khi `json.dumps` → `default=str`.

## Ngữ nghĩa dễ hiểu nhầm

- `review_queue.generated_content_id` nullable: luồng A1→A2 có giá trị, luồng T3 dùng `tenant_tour_version_id`. Query tìm
  "dòng mồ côi" phải loại trường hợp này.
- Review queue chỉ giữ bản lỗi mới nhất mỗi tour (cũ hơn = superseded). Tour đã publish → dòng review tự dismissed.
- `acp_contract.v_active_tour_atoms` được tạo bằng `SELECT ta.*` — Postgres bung `*` lúc tạo view, nên thêm/xoá cột ở
  `tour_atoms` phải DROP + tạo lại view trong cùng migration (mẫu: CIS 208).
- `tour_atoms.weight`: giá trị mặc định, không dùng để lọc hay rank (Score thật ở `acp_contract.atom_ranking`).
  `distinctiveness` đã bị xoá (CIS 208).
- `acp_contract.atom_embedding` sinh lười theo thiết kế (chỉ atom vào shortlist PAA), không cần backfill.
- `shared.acp_runs` là tracker A0–A3 đang sống (khác `acp_shared.acp_runs` đã xoá).
- `acp_shared.acp_output_rules.source_hitl_id` không có FK → có thể trỏ tới giá trị không tồn tại.
- `shared.rerun_wave` (wave object, `/admin/waves`): wave `open` làm DB Migrate `apply` coi là bận.
- Bảng 0 dòng không chứng minh "chưa từng dùng" — kiểm `git ls-files`, caller và log.

## LLM log

- `shared.llm_call_log` ghi cả lời gọi shadow (cùng stage) và lời gọi lỗi (Jev fail-open vẫn ghi cost).
- Model thực sự quyết định: route ở `shared.llm_role_config` + `shared.llm_shadow_log`; quyết định Jev:
  `shared.decision_log.zone` (dòng `error IS NULL` mới là verdict thật).

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
