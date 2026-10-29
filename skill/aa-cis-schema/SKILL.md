---
name: aa-cis-schema
description: Làm việc với database dùng chung trên RDS acc2 (schema CIS, TripPlanner, AA-Booking, CRM của AA-Partner) — nguồn tên bảng/cột, login DB và pattern query qua ECS exec + S3, các bẫy hay gặp, cách viết migration theo role chủ, và quy trình bắt buộc khi xoá bảng hoặc dữ liệu. Dùng khi query DB, viết script ECS exec hay DB Migrate run-script, debug dữ liệu pipeline, viết migration, kiểm schema drift / ERD drift, hoặc gặp tên bảng như raw_tours, published_tours, tour_atoms, review_queue, shared.job, crm.job, content_piece, publish_log, itinerary_components (đã xoá, tp-018).
---

# aa-cis-schema

## Nguồn tên bảng và cột

**Không chép schema vào skill.** Nguồn duy nhất là `docs/architecture/db-schema-reference.md` ở repo gốc AA-Ecosys
(KHÔNG trong repo app), kèm steering `.kiro/steering/db-schema.md`. File là dump live từ catalog, sinh lại mỗi đêm và
sau mỗi DB Migrate `apply` (workflow **DB Schema Dump** của AA-CIS-Infra, PR `bot/db-schema-reference`).

- Trước khi viết query: đọc file đó hoặc grep tên bảng. Trong file còn có: ERD theo schema (`docs/architecture/erd/`),
  mục *Latest migrations* (key mới nhất mỗi owner), *Schema drift* (AA-853: object trên Dev không migration nào tạo).
- Không có trong file (object mới hơn dòng "Verified") → chạy tay workflow DB Schema Dump (`publish=true`) rồi merge PR
  bot; không tự viết script dump.
- Migration mới nhất live: `SELECT version, applied_at FROM shared.schema_versions ORDER BY applied_at DESC LIMIT 5;`
  — `version` là varchar và chứa key của mọi owner (`NNN`, `tp-`, `bk-`, `crm-`, `rl-`), không `ORDER BY version::int`.
- Chủ schema, prefix key, role: `docs/database/schema-ownership.md` + Infra `db/owners.yaml`. Bảng đã xoá:
  `docs/architecture/dead-table-registry.md` — đọc trước khi nghi một bảng "biến mất".

## Truy cập DB

- Chỉ acc2 (`aa365-admin`, us-west-1). RDS trong private subnet → **ECS exec + script Python (asyncpg) + S3**. Không psql
  local, không RDS Query Editor. Pattern + log + port-forward: `references/ecs-exec.md`.
- **Chỉ phiên điều phối (orchestrator) chạy ECS exec.** Hook `.claude/hooks/subagent-guardrails.sh` chặn subagent gọi
  `aws ecs execute-command`; subagent chỉ soạn script + runbook rồi trả về cho điều phối chạy.
- Login của script = `DATABASE_URL` của container CIS = **`cis_app`**: đọc/ghi mọi bảng CIS (kể cả bảng RLS), không DDL.
  `booking.*` / `tripplanner.*` chỉ được `SELECT` vài view hợp đồng (`booking.v_ops_*`, `booking.v_supply_*`,
  `tripplanner.v_ops_traffic_daily`); bảng gốc → 42501. Không role AA nào có `USAGE` trên `crm` (cách ly hai chiều,
  ADR 0008a). Luôn `ssl="require"`. Task role CIS bị Deny secret master `aa-cis/dev/rds`, `aa-cis/dev/db-migrator`,
  `booking/*`, `tripplanner/*` → đừng `get_secret_value` master.
- Việc cần master (đọc/ghi bảng `booking.*` / `tripplanner.*` / `crm.*`, role, catalog, ownership) → AA-CIS-Infra
  **DB Migrate `mode=run-script`** với file `db/scripts/<name>.py` đã review (`db/scripts/README.md`; script chỉ đọc khai
  `READ_ONLY = True`). Không qua ECS exec.
- Master `aa_cis_admin` là break-glass (DM-8.9): chỉ tự động trong task migrator cho file `roles/`, `set-password`,
  `run-script` (kể cả DB Tour Liveness Gate hằng đêm, READ_ONLY). Dùng khác → ghi lý do vào session log + Linear.
- Mặc định **read-only**. Ghi hoặc xoá → mục cuối.

## Bối cảnh dữ liệu cần nhớ (ổn định)

- Schema CIS (chủ `cis_owner`): `silver_aa_internal` (raw, generated), `gold_aa_internal` (published, tenant versions,
  nội dung AA cho CRM), `shared` (tenant, job, destinations, schema_versions, LLM log, rerun_wave), `acp_contract`
  (atom, segment, route), `acp_shared` (content_piece, angle gate, publish_log, facts), `acp_deliver`, `geo` (place,
  tour graph), `catalog` (view hợp đồng cho app khác, chủ view `catalog_owner`).
- App khác: `tripplanner` (`tp_owner`), `booking` (`bk_owner`), `crm` (`crm_owner`, AA-Partner; login `crm_app`,
  mọi trao đổi với app AA qua HTTP contract).
- Job: mỗi owner một bảng theo template ADR 0003a — `shared.job` (CIS, chạy trên `aa-cis-dev-worker`), `booking.job`,
  `crm.job` (worker chạy trong process api CRM). `shared.pipeline_jobs` chỉ còn lịch sử, không ghi mới.
- Atom **platform-wide** và đi theo trạng thái Master qua view `acp_contract.v_active_tour_atoms`. Đọc qua view.
- Quyền ghi nội dung: chỉ CIS ghi; app khác đọc `catalog.*` (ADR 0002, ADR 0007). Role `tripplanner` không đọc trực
  tiếp bảng CIS nào từ CIS 270, không ghi `shared.destinations`.
- Địa điểm/tour graph ở `geo.*`, đọc qua `catalog.v_tour_component`, `v_tour_day`, `v_tour_stop`, `v_tour_leg`,
  `v_tour_junction`, `v_graph_node`, `v_graph_edge`. 8 bảng place cũ của TripPlanner (`tripplanner.itinerary_components`,
  `tour_day`, `tour_stop`, `tour_graph_*`, `tour_leg`, `tour_junction`) đã DROP bằng tp-018: query còn nhắc chúng là
  sai. Còn giữ `tripplanner.component_id_map` (id cũ → id catalog).

## Bẫy hay gặp

Xem `references/gotchas.md`. Năm bẫy hay dính nhất:
1. `raw_tours` PK là `tour_id`, không phải `id`; không có cột `status` (dùng `source_status`, `deleted_at`…).
2. `published_tours` và `seo_context` không có `country` → JOIN `raw_tours`.
3. `review_queue.generated_content_id` nullable: dòng T3 dùng `tenant_tour_version_id`.
4. Kiểu `tenant_id` không đồng nhất giữa các bảng → đọc kiểu cột trong reference trước khi cast `::uuid`.
5. `llm_call_log` ghi cả lời gọi lỗi và shadow → đọc route + `llm_shadow_log` / `decision_log` để biết model nào thực
   sự quyết định.

Script asyncpg ad-hoc: tham số ngày bind `$1::date` phải là `datetime.date` (`date.fromisoformat`), không phải chuỗi.

## Viết migration

- Hai luồng (ADR 0017, Part A MIG-4; chi tiết skill `aa-ship`): file **expand** (header `-- migrate: expand`) đi cùng
  code + nâng readiness trong một PR app, bot migration-sync copy, Migration Apply tự apply (khi `DB_AUTO_APPLY=true`),
  `schema-gate` của Deploy Dev chờ key; file **contract / destructive** giữ luồng D8 (PR chỉ migration → bot copy →
  DB Migrate `check` → `apply` bằng tay → PR schema dump → PR code). File ở repo chủ; bản copy byte-identical ở Infra
  `db/migrations/<owner>/` (Migration Copy Guard đòi PR của repo chủ đã vào `main`; bot copy, không mở PR copy tay).
- Expand chỉ được: tạo object mới (bảng mới trong schema bắt RLS phải `ENABLE` + `FORCE`), thêm cột nullable / default
  không volatile, index không unique (bảng > 100k dòng: `CONCURRENTLY` trong file `no-transaction` riêng). Không `DO`
  block, không `CREATE OR REPLACE`, không INSERT/UPDATE/DELETE vào bảng có sẵn, không đụng bảng nóng (`shared.job`,
  `booking.job`, `crm.job`, `shared.job_worker`, ledger, `catalog.*`). Kiểm trước khi mở PR: Infra
  `python3 db/run_migration.py --inspect db/migrations/<owner>/<file>` (exit 0, `"expand": true`); check "Migration
  preflight" của app ghi kết quả classify.
  Input `migration` của DB Migrate có tiền tố owner (`cis/281_x.sql`). `apply` chờ **mọi** bảng job rảnh và không có
  wave mở (`shared.rerun_wave`), trừ khi Nghiệp override có lý do (file expand do Migration Apply chạy thì bỏ qua chờ
  bảng job, nhưng file nhắc bảng nóng vẫn chờ wave đóng).
- DB Migrate đăng nhập **`db_migrator`** và chạy mỗi file bằng role chủ sống của schema neo: `cis/` → `cis_owner`,
  `booking/` → `bk_owner`, `tripplanner/` → `tp_owner`, `crm/` → `crm_owner` (không cần `OWNER TO`). File `roles/`
  (key `rl-NNN`) chạy bằng master.
- Lint của DB Migrate từ chối `RESET ROLE`, `SET ROLE` không `LOCAL`, `CREATE/ALTER/DROP ROLE|EXTENSION`, DROP/TRUNCATE
  thiếu header `-- migrate: destructive`. Quay về sau khi đổi role: `SET LOCAL ROLE cis_owner`. Role/extension, `ALTER TYPE
  public.<enum>` → file Infra `roles/`. Không `SECURITY DEFINER` trong file CIS.
- Bảng CIS mới bật RLS → cùng file thêm `<t>_cis_app_all … TO cis_app USING (true) WITH CHECK (true)`; bảng FORCE thêm
  `<t>_cis_owner_all … TO cis_owner`. Thiếu → runtime đọc 0 dòng (CI: `tests/integration/test_x1_cis_app_privileges.py`).
  Grant cho `cis_app` tự có qua default privileges `FOR ROLE cis_owner` trong 11 schema runtime CIS; `catalog` không.
- **Đổi view `catalog.*`** (trong `BEGIN … COMMIT`; view thuộc `catalog_owner`, schema thuộc `cis_owner`):

  ```sql
  GRANT CREATE ON SCHEMA catalog TO catalog_owner;
  SET LOCAL ROLE catalog_owner;
  CREATE OR REPLACE VIEW catalog.v_... AS ...;
  SET LOCAL ROLE cis_owner;          -- đường về; không RESET ROLE
  REVOKE CREATE ON SCHEMA catalog FROM catalog_owner;
  ```

  Lint từ chối `GRANT` thiếu `REVOKE` đi kèm. Ví dụ + CI: AA-CIS-App `tests/integration/test_aa860_migration_246.py`;
  chi tiết: AA-CIS-App `CONTEXT.md` (Deploy & CI).
- **ERD thiết kế:** schema có trang `docs/architecture/erd/design/<schema>.md` ở repo gốc với `enforce=true` → migration
  thêm/xoá bảng, đổi khoá hoặc FK phải sửa trang đó trong cùng đợt thay đổi (PR root đi kèm), nếu không bước "Design ERD
  drift" của DB Schema Dump đỏ.
- Giá trị code mới ghi vào cột có CHECK phải có trong CHECK trước khi code đó deploy. Code cần file **contract** mới →
  PR migration riêng, apply trước khi merge code; code cần file **expand** → cùng PR, `schema-gate` giữ deploy tới khi
  key được apply (tối đa `SCHEMA_GATE_TIMEOUT_S`, mặc định 40′; quá hạn → đỏ, apply xong thì chạy lại Deploy Dev).
- Bài học chi tiết vùng DB/migration: `skill/aa-lessons/lessons.md` mục "Dữ liệu" và "Vận hành" — đọc trước khi sửa.

## Xoá bảng hoặc dữ liệu vĩnh viễn

**Bắt buộc** làm theo `references/destructive-ops.md` (STEP0 → DRY RUN → snapshot → SAVEPOINT → COMMIT khi Nghiệp đồng
ý → verify độc lập). Không có ngoại lệ "chỉ vài dòng".
