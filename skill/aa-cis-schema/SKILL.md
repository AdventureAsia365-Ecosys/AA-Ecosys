---
name: aa-cis-schema
description: Làm việc với database AA-CIS (PostgreSQL trên RDS acc2, dùng chung với TripPlanner và AA-Booking) — nguồn tên bảng/cột, pattern query qua ECS exec + S3, các bẫy hay gặp, và quy trình bắt buộc khi xoá bảng hoặc dữ liệu. Dùng khi query DB, viết script ECS exec, debug pipeline, viết migration, hoặc gặp tên bảng như raw_tours, published_tours, tour_atoms, review_queue, shared.job, content_piece, publish_log, itinerary_components.
---

# aa-cis-schema

## Nguồn tên bảng và cột

**Không chép schema vào skill.** Nguồn duy nhất là `docs/architecture/db-schema-reference.md` ở repo gốc AA-Ecosys (KHÔNG trong AA-CIS-App), kèm steering `.kiro/steering/db-schema.md`. File reference là dump live từ `information_schema`, regenerate sau mỗi migration đổi cấu trúc.

- Trước khi viết query: đọc file đó, hoặc grep tên bảng trong file.
- Không có trong file (object mới hơn dòng "Verified") → chạy tay workflow **DB Schema Dump** của AA-CIS-Infra (`publish=true`) rồi merge PR `bot/db-schema-reference`; không tự viết script dump (steering `db-schema.md`).
- Migration mới nhất: `SELECT version, applied_at FROM shared.schema_versions ORDER BY applied_at DESC LIMIT 5;` — không `ORDER BY version::int`, vì có version dạng text cũ.

## Truy cập DB

- Chỉ acc2 (`aa365-admin`, us-west-1). RDS nằm trong private subnet → **ECS exec + script Python (asyncpg) + S3** để lấy kết quả. Không psql local, không RDS Query Editor.
- **Login DB (X1 xong 19/10/2026, AA-860):** script ECS exec dùng `DATABASE_URL` của container = **`cis_app`** (mọi bảng CIS, kể cả bảng RLS; `booking.*` / `tripplanner.*` → 42501; không DDL). Task role CIS bị Deny secret master `aa-cis/dev/rds`, `aa-cis/dev/db-migrator`, `booking/*`, `tripplanner/*` → đừng `get_secret_value` master. Luôn `ssl="require"`.
- Việc cần master (đọc/ghi `booking.*` / `tripplanner.*`, role, catalog, ownership) → AA-CIS-Infra **DB Migrate `mode=run-script`** với file `db/scripts/<name>.py` đã review. Không qua ECS exec.
- Master `aa_cis_admin` là break-glass: chỉ tự động trong task migrator cho file `roles/`, `set-password`, `run-script`. Dùng khác → ghi lý do vào session log + Linear (DM-8.9).
- Pattern đầy đủ: `references/ecs-exec.md`. Mỗi phiên thường có runner tạm trong `.tmp-session/` (ví dụ `sNNN_run.sh`) — tái dùng nếu còn, hoặc viết mới (không giả định file phiên cũ còn).
- Đọc output qua S3, không tin output terminal SSM (hay bị cắt giữa chừng).
- Script import code app → `sys.path.insert(0, "/app")`.
- Mặc định **read-only**. Ghi hoặc xoá → mục cuối.

## Bối cảnh dữ liệu cần nhớ (ổn định)

- Schema chính: `silver_aa_internal` (raw, generated), `gold_aa_internal` (published, tenant versions), `shared` (tenant, job, destinations, schema_versions), `acp_contract` (atom, segment, route), `acp_shared` (content_piece, angle gate, publish_log, facts), `tripplanner`, `booking` (khi có AA-Booking).
- Atom **platform-wide** (AA-526) và đi theo trạng thái Master qua view `acp_contract.v_active_tour_atoms` (AA-713). Đọc qua view, không đọc thẳng bảng.
- Job: mọi tác vụ nền nằm ở `shared.job` (AA-723). `shared.pipeline_jobs` chỉ còn dữ liệu lịch sử; không ghi mới vào đó. Trang Jobs đọc `shared.job`.
- Quyền ghi nội dung: chỉ CIS ghi. App khác chỉ đọc (ADR 0002). Role `tripplanner` không ghi `shared.destinations`.

## Bẫy hay gặp

Xem `references/gotchas.md`. Năm bẫy hay dính nhất:
1. `raw_tours` PK là `tour_id`, không phải `id`.
2. `published_tours` và `seo_context` không có `country` → JOIN `raw_tours`.
3. `review_queue.generated_content_id` nullable: dòng T3 dùng `tenant_tour_version_id`.
4. Một số `tenant_id` là TEXT, không phải UUID → không cast `::uuid` bừa.
5. `llm_call_log` ghi cả lời gọi lỗi và shadow → đọc route + `llm_shadow_log` / `decision_log` để biết model nào thực sự quyết định.

## Viết migration (X1, từ 19/10/2026)

- DB Migrate đăng nhập **`db_migrator`** và chạy mỗi file với role chủ sống của schema neo: `cis/` → `cis_owner`, `booking/` → `bk_owner`, `tripplanner/` → `tp_owner` (không cần `OWNER TO`). File `roles/` (key `rl-NNN`) chạy bằng master. Freeze migration CIS và freeze view `catalog.*` (XD9) đã **hết** từ khi 246 áp (S22).
- **Không bao giờ `RESET ROLE`** (về `db_migrator` → object mới thuộc `db_migrator`, `cis_app` bị 42501; lint từ chối, post-check rollback exit 9). Quay lại bằng `SET LOCAL ROLE cis_owner`.
- Không `CREATE/ALTER/DROP ROLE|EXTENSION`, không `ALTER TYPE public.<enum>` trong file app → file Infra `roles/`. Không `SECURITY DEFINER`.
- Bảng CIS mới bật RLS (ENABLE-only hoặc FORCE) → cùng file thêm `<t>_cis_app_all … TO cis_app USING (true) WITH CHECK (true)`; bảng FORCE thêm cả `<t>_cis_owner_all … TO cis_owner`. Thiếu → runtime đọc 0 dòng (CI standing check `tests/integration/test_x1_cis_app_privileges.py`, probe cell `rls.enable_only_has_cis_app_policy`).
- Grant cho `cis_app` trên object mới: tự có qua default privileges `FOR ROLE cis_owner` (XD3) trong 11 schema runtime CIS; `catalog` không.
- **Công thức đổi view `catalog.*`** (trong `BEGIN … COMMIT` của file; view thuộc `catalog_owner`, schema thuộc `cis_owner`):

  ```sql
  GRANT CREATE ON SCHEMA catalog TO catalog_owner;
  SET LOCAL ROLE catalog_owner;
  CREATE OR REPLACE VIEW catalog.v_... AS ...;
  SET LOCAL ROLE cis_owner;          -- đường về; không RESET ROLE
  REVOKE CREATE ON SCHEMA catalog FROM catalog_owner;
  ```

  Lint từ chối `GRANT` thiếu `REVOKE` đi kèm. Ví dụ + CI: AA-CIS-App `tests/integration/test_aa860_migration_246.py`; chi tiết: AA-CIS-App `CONTEXT.md` (Deploy & CI).

## Xoá bảng hoặc dữ liệu vĩnh viễn

**Bắt buộc** làm theo `references/destructive-ops.md` (STEP0 → DRY RUN → SAVEPOINT → COMMIT → verify độc lập). Không có ngoại lệ "chỉ vài dòng".

Bảng đã xoá và lý do: `docs/architecture/dead-table-registry.md` (repo gốc AA-Ecosys). Đọc trước khi nghi một bảng "biến mất".
