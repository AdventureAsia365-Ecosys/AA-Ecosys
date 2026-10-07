# DB Schema — nguồn sự thật (Nghiệp chốt 03/10/2026, S209)

Shared RDS acc2 (`aa-cis/dev/rds`, `005097885195`, us-west-1) dùng chung bởi CIS và TripPlanner,
schema tách bạch. Tên bảng/cột thay đổi theo migration nên **không nhớ bằng đầu, không đoán**.

## Quy tắc BẮT BUỘC
- **Trước khi viết query / dùng tên bảng-cột, ĐỌC `docs/architecture/db-schema-reference.md`** —
  file này là dump thật từ `information_schema` (mọi schema, mọi cột, enum, FK, migration mới nhất).
  Nó là nguồn sự thật về tên bảng/cột cho CẢ Kiro và Claude Code. KHÔNG introspect cột lại từ đầu
  nếu file đã có — chỉ introspect khi file thiếu bảng mới hoặc nghi file lỗi thời.
- Skill `skill/aa-cis-schema/SKILL.md` giữ phần GIẢI THÍCH (vai trò bảng, Dead Table Registry, gotcha,
  ECS exec pattern) — nhưng danh sách cột trong skill là tóm tắt lịch sử, có thể lệch. Khi lệch,
  `db-schema-reference.md` thắng (nó là dump live).

## Khi nào regenerate file reference
Sau MỖI migration đổi cấu trúc (CREATE/ALTER/DROP TABLE/VIEW, thêm cột). Cách làm:
1. Chạy dump: `.tmp-session/s209_schema_dump.py` (asyncpg + `information_schema`, ghi JSON ra S3,
   chạy qua ECS exec vì RDS private — xem `skill/aa-cis-schema/references/ecs-exec.md`).
2. Sinh lại Markdown: `.tmp-session/s209_gen_schema_md.py` (đọc JSON → ghi
   `docs/architecture/db-schema-reference.md`).
3. Cập nhật dòng "Verified / Latest migration" ở đầu file.

## Gotcha hay quên (đã verify S209)
- `silver_aa_internal.raw_tours` PK = `tour_id` (KHÔNG phải `id`); trạng thái raw ở
  `source_status` / `pipeline_status` / `review_status` / `lifecycle_stage` / `deleted_at`
  (KHÔNG có cột `status`).
- `silver_aa_internal.quality_scores` có `evaluated_at` (KHÔNG phải `created_at`); bản được chấp
  nhận lấy qua `published_tours.quality_score_id`.
- `gold_aa_internal.published_tours` + `silver_aa_internal.seo_context`: KHÔNG có `country` → JOIN `raw_tours`.
- Atom đọc qua `acp_contract.v_active_tour_atoms` (mig 203, lọc theo `published_tours.master_status`),
  KHÔNG đọc thẳng `acp_contract.tour_atoms` ở các read A3.
- LLM gateway: `shared.llm_call_log` (có cả shadow dưới cùng stage — đọc route thật ở
  `shared.llm_role_config` + `shared.llm_shadow_log`), `shared.llm_model_catalog`.
- Job runner: mọi tác vụ nền ở `shared.job` (số kind đổi theo thời gian — đọc `/admin/job-runner/summary`
  hoặc `shared.job`, không nhớ số cứng); `shared.pipeline_jobs` chỉ còn dữ liệu lịch sử, KHÔNG ghi mới.
