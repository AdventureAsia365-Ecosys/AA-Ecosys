# DB Schema — nguồn sự thật (Nghiệp chốt 03/10/2026, S209)

Shared RDS acc2 (`aa-cis-dev-db`, `005097885195`, us-west-1) dùng chung bởi **CIS, TripPlanner, AA-Booking và AA-Partner (CRM)**,
mỗi app một schema riêng: CIS (`silver_aa_internal`, `gold_aa_internal`, `acp_*`, `geo`, `catalog`, phần lớn `shared`),
TripPlanner (`tripplanner`, key `tp-NNN`), Booking (`booking`, key `bk-NNN`; role `booking`, DSN `booking/dev/database-url`), CRM (`crm`, key `crm-NNN`, role `crm_app`, chạy `crm_owner` qua DB Migrate).
Tên bảng/cột thay đổi theo migration nên **không nhớ bằng đầu, không đoán**.

## Quy tắc BẮT BUỘC
- **Chủ sở hữu schema** (repo nào được viết migration cho schema/bảng nào, key version `NNN`/`tp-NNN`/`bk-NNN`):
  `docs/database/schema-ownership.md`. App không bao giờ migrate schema của app khác. Migration áp lên Dev qua
  workflow **DB Migrate** của AA-CIS-Infra (bản copy y hệt ở `db/migrations/<owner>/`), không chạy từ máy cá nhân.
- **Trước khi viết query / dùng tên bảng-cột, ĐỌC `docs/architecture/db-schema-reference.md`** —
  file SINH TỰ ĐỘNG từ catalog live (mọi schema của cả 4 app: cột, index, FK, policy RLS, grant, owner, role,
  migration mới nhất mỗi owner). Nó là nguồn sự thật về tên bảng/cột cho CẢ Kiro và Claude Code. KHÔNG sửa tay,
  KHÔNG introspect cột lại từ đầu — dòng "Verified" ở đầu file cho biết bản dump mới tới đâu.
- Skill `skill/aa-cis-schema/SKILL.md` giữ phần GIẢI THÍCH (vai trò bảng, Dead Table Registry, gotcha,
  ECS exec pattern) — nhưng danh sách cột trong skill là tóm tắt lịch sử, có thể lệch. Khi lệch,
  `db-schema-reference.md` thắng (nó là dump live).

## File reference được sinh lại thế nào (tự động từ AA-807 N1)
CI làm, không ai chạy tay: workflow **DB Schema Dump** của AA-CIS-Infra (`.github/workflows/db-schema-dump.yml`)
chạy **mỗi đêm** và **sau mỗi lần DB Migrate `apply` thành công**. Nó chạy `db/schema_dump.py` (chỉ đọc catalog, không
đọc dữ liệu dòng) trong một ECS task tạm, sinh Markdown bằng `db/gen_schema_reference.py`, và khi CẤU TRÚC đổi thì
mở/cập nhật PR trên repo gốc (nhánh `bot/db-schema-reference`). Việc của agent:
1. Sau một migration: chờ PR `bot/db-schema-reference` (hoặc chạy tay workflow `DB Schema Dump`). Sau một DB Migrate
   `apply`, PR đó tự merge (ci-bot, AA-993 M1, ADR 0017 d9 / 0011a) khi sạch: run này mở PR, drift không đổi, design
   ERD xanh, chỉ file sinh tự động, mọi check root xanh. Không tự merge (run summary ghi lý do) → agent merge tay. Chỉ
   sau khi PR đã merge mới viết code dựa trên cột mới (D8 bước 5, Part A MIG-4).
2. Nghi file lỗi thời mà chưa có PR: chạy tay workflow (input `publish=true`), không tự viết script dump.
Script cũ `.tmp-session/s209_*` đã thôi dùng.

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
- Job runner: mỗi owner một bảng job theo template chung (ADR 0003a) — CIS `shared.job`, Booking `booking.job`
  (số kind đổi theo thời gian — đọc `/admin/job-runner/summary` hoặc bảng job, không nhớ số cứng);
  `shared.pipeline_jobs` chỉ còn dữ liệu lịch sử, KHÔNG ghi mới. DB Migrate `apply` chờ MỌI bảng job rảnh (DM-11.4).
