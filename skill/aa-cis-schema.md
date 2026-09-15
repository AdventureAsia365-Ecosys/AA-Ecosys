---
name: aa-cis-schema
description: AA-CIS database schema reference và ECS exec patterns cho CIS platform. Dùng skill này bất cứ khi nào làm việc với CIS database, query PostgreSQL, viết ECS execute-command scripts, debug pipeline issues, hoặc cần biết table/column names. Trigger khi thấy: raw_tours, published_tours, seo_context, pipeline_runs, ECS exec, S3-mediated query, gold_aa_internal, silver_aa_internal, shared schema, acp_shared, acp_contract, acp_deliver, tenant_atom_state, content_piece, publish_log, angle_gate, CIS DB, T-series, T0-T11, audit bugs.
---

# AA-CIS Schema Reference (verified 27/08/2026 post-migration, AA-477+479+480+481 — live DB dump, 55 tables, 735 columns, 63 FK, 4 views, 11 schema)

Bản viết lại toàn bộ lần 2 (lần 1 là bản 27/08/2026 pre-migration — 76 bảng/81 FK — đã lỗi thời
ngay trong cùng ngày sau khi migration 121+122 chạy thật). Tổng hợp 4 việc:
- **AA-479** — audit schema đầy đủ từ dữ liệu thật, xác nhận lại phạm vi migration 121 (AA-477).
- **AA-480** — section "FK Reference" qua `pg_constraint`.
- **AA-481** — phát hiện + draft migration 6 bảng chết bổ sung (`122_drop_orphaned_
  acpv1_extras.sql`), ngoài phạm vi 121.
- **AA-477 (chạy thật, 27/08/2026 16:55:09 UTC)** — migration 121 + 122 COMMIT thật, xoá vật lý
  21 bảng (15 từ 121 + 6 từ 122). Đây là bản skill PHẢN ÁNH TRẠNG THÁI SAU khi apply — số liệu 76
  bảng/81 FK ở bản trước giờ chỉ còn giá trị lịch sử, xem "Dead Table Registry" bên dưới.

Xem `docs/claude_audit/AA-479-schema-audit.md` + `docs/claude_audit/AA-258-259-acpv1-tables-audit.md`
trong `AA-CIS-App` cho toàn bộ bằng chứng/phương pháp điều tra đằng sau quyết định xoá — skill chỉ
giữ kết luận + số liệu sau cùng, không lặp lại quá trình điều tra.

## AWS Context
- **Account:** `005097885195` | **Region:** `us-west-1` | **Profile:** `aa365-admin`
- **ECS cluster:** `aa-cis-dev-cluster` | **Service:** `aa-cis-dev-api` | **Container:** `api`
- **S3 script bucket:** `aa-cis-bronze-005097885195`
- **Task def:** verify live: `aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-api --profile aa365-admin --region us-west-1` (KHÔNG hard-code số ở skill — đổi mỗi deploy)
- **DB:** `aa_cis_dev` | **User:** `aa_cis_admin` | **DB secret:** `aa-cis/dev/rds` (Secrets Manager, plain DSN string)
- ⚠️ Account cũ `867490540162`/`pqnghiep-admin` — KHÔNG decommission hẳn (giữ lại có chủ đích làm
  Bedrock cross-account satellite, AA-296/397/398/399). Compute/network hạ tầng cũ ĐÃ xoá (AA-271).
  Đừng coi account này "đã đóng" khi audit hạ tầng mới, nhưng cũng đừng tạo resource compute mới
  ở đây.

## Schema Update Rule
⚠️ **KHÔNG còn "mỗi thứ Hai"** — re-audit lại skill này sau MỖI đợt dọn dẹp DB lớn (migration DROP
TABLE, xoá cụm bảng, đổi kiến trúc) — không theo lịch cố định. Dấu hiệu cần re-audit ngay: vừa
chạy migration DROP TABLE nào, vừa merge PR đổi ≥5 bảng, hoặc lần cuối audit đã >1 tháng và sắp
cần dùng số liệu bảng để quyết định gì quan trọng (VD: có nên xoá bảng X không). Bản này tự nó là
ví dụ — chỉ 1 ngày sau bản trước đã lỗi thời hoàn toàn vì DROP TABLE thật chạy.

Dump lại bằng script ở mục "S3-Mediated ECS Exec" bên dưới (không có `scripts/dump_schema2.py`
sẵn trong repo — viết script mới mỗi lần cần, không giả định file cũ còn tồn tại).

---

## Schema Overview (số liệu thật SAU migration 121+122, 27/08/2026)

| Schema | Bảng | View | Vai trò |
|---|---|---|---|
| `silver_aa_internal` | 7 (−1) | 0 | CIS S1 input + generated content (aa_internal, KHÔNG phải ACP) |
| `gold_aa_internal` | 4 | 0 | CIS S1 published output |
| `shared` | 17 (−1) | 3 | Cross-tenant config, pipeline tracking, tenant-facing tables |
| `acp_shared` | 19 (−10) | 0 | T-series state (N1-N11/T0-T11) — ACPv1 tàn dư ĐÃ XOÁ hết |
| `acp_contract` | 3 | 1 | Atom pipeline (N2/T5/T6) + `v_trip_registry` view |
| `acp_deliver` | 3 | 0 | N7/N8 weekly flywheel (packets/pieces/tenant_tour_pages) |
| `acp_gold_output` | **0 (−1)** | 0 | Schema rỗng — ACPv1 tàn dư cuối cùng đã xoá (`published_content`), xem lưu ý dưới |
| `acp_silver_s2` | 1 (−1) | 0 | Chỉ còn `competitor_inputs` (B4 CompetitorIndex, sống thật) |
| `acp_silver_s3` | **0 (−2)** | 0 | Schema rỗng — ACPv1 S3 tàn dư đã xoá hết |
| `acp_silver_s4` | **0 (−2)** | 0 | Schema rỗng — ACPv1 S4 tàn dư đã xoá hết |
| `public` | 1 (−3) | 0 | Chỉ còn `checkpoint_migrations` (LangGraph bookkeeping, cố ý giữ) |

**Không có schema per-tenant nào tồn tại** (`silver_{slug}`/`gold_{slug}` — thiết kế trong
migration 003 nhưng chưa từng được kích hoạt thật, kể cả cho 13 tenant B2B hiện có). Toàn bộ dữ
liệu tenant nằm trong `shared.*`/`acp_shared.*`/`gold_aa_internal.*` có cột `tenant_id`.

⚠️ **Quan sát mới (chưa phải quyết định, chưa có ticket):** `acp_gold_output`, `acp_silver_s3`,
`acp_silver_s4` giờ là schema RỖNG (0 bảng, 0 view) — namespace vẫn còn tồn tại trên Postgres
nhưng không còn object gì bên trong. Việc `DROP SCHEMA` 3 namespace này (khác với DROP TABLE đã
làm) là bước dọn dẹp riêng, chưa nằm trong phạm vi AA-477/480/481 — cờ lại đây cho lần audit sau,
không tự ý làm.

## Migrations — trạng thái apply thật (27/08/2026)

`shared.schema_versions` mới nhất **122** (AA-481), applied_at `2026-08-27 16:55:09.226010+00:00`.
Đọc trực tiếp `ORDER BY applied_at` — không cast `version::int` (có version dạng text cũ: `v1.0`/
`v1.1`/`v2.0`/`v3.0` từ trước khi đánh số thuần túy bắt đầu ở `027`).

- ✅ **`121_drop_acpv1_stage_chain.sql` (AA-477) — ĐÃ APPLY** `2026-08-27 16:55:09 UTC`. Xoá thật
  15 bảng + 1 constraint (`acp_output_rules_source_hitl_id_fkey`). Verify post-commit: cả 15 bảng
  raise `UndefinedTableError` qua `information_schema.tables` re-query độc lập; `acp_output_rules`
  còn nguyên 13 cột, FK count = 0; `apply_output_rules()` chạy thật (không mock) trên schema đã
  đổi, hành vi đúng (rule match, `run_count` tăng, `OutputRuleViolation` raise chính xác).
- ✅ **`122_drop_orphaned_acpv1_extras.sql` (AA-481) — ĐÃ APPLY** `2026-08-27 16:55:09 UTC` (cùng
  1 transaction với 121, cùng timestamp). Xoá thật 6 bảng.
- ⚠️ **`120_drop_gate_a.sql` (AA-473) — VẪN CHƯA APPLY**, KHÔNG bundle cùng 121/122 lần này (quyết
  định riêng, cần xác nhận riêng của Nghiệp). `acp_shared.tenant_onboarding` vẫn còn sống thật (2
  row) tính tới 27/08.

Full 21-bảng đã xoá + lý do từng bảng: xem "Dead Table Registry" (Nhóm 4) bên dưới.

Muốn xem full history: `SELECT version, applied_at, description FROM shared.schema_versions ORDER BY applied_at ASC` — KHÔNG dùng `ORDER BY version` (sai kiểu dữ liệu, sẽ lỗi
`invalid input syntax for type integer` nếu ai đó cast).

---

## Phân loại bảng theo trạng thái dùng thật (thay "Medallion Architecture" cũ)

### Nhóm 1 — T-series đang dùng thật (T0-T11 / N1-N8)

| Bảng | T-stage | PK/cột đáng chú ý |
|---|---|---|
| `acp_shared.tenant_atom_state` | N1/T6 | `(tenant_id, tour_id)`, `assigned_angle`, `starred`, `cooldown_until`, `usage_log` jsonb |
| `acp_shared.tenant_onboarding` | N1 (Gate A — đã xoá code AA-473, bảng chưa drop, chờ migration 120) | 2 row |
| `acp_shared.marketplace_portfolios` | Marketplace/N1 seed | giữ làm seed source cho N1 (AA-472), KHÔNG phải Marketplace view thật (đó là `GET /v1/marketplace`) |
| `acp_shared.competitor_index_cache` + `acp_silver_s2.competitor_inputs` | B4 CompetitorIndex | `v1_competitors.py`, `competitor_index.py` |
| `acp_shared.quarter_plan` / `quarter_plan_version` | Gate B / N5 | `plan_id`, `year`, `quarter`, `current_version_id` |
| `acp_shared.year_plan` / `content_metric_snapshot` | T7/N4 | `services/acp_shared/content_metrics.py` |
| `acp_shared.tenant_config` | N4-N6 markets/channels | |
| `acp_shared.angle_gate_request` (10 cols) / `angle_gate_option` (9 cols) | T8 | `request_id`→`option_id` (1:3, `idx` 0-2), `cta` nullable, `chosen`/`recommended` bool |
| `acp_shared.content_piece` (10 cols) | T9/T10 | `piece_id`, `angle_gate_request_id`, `attempt_number`, `status`, `gate_ledger`/`repair_log` jsonb |
| `acp_shared.publish_log` (12 cols) | T11 | `piece_id`→`content_piece`, `channel`, `external_id`/`external_url`, `unpublished_at`/`unpublished_by` |
| `acp_shared.acp_v2_runs` (8 cols) / `acp_v2_slots` (15 cols) | N7/N8 weekly flywheel | `run_id`, `(year,month,week)`, `tenant_id` là TEXT không phải UUID trong 2 bảng này |
| `acp_shared.unknown_ledger` | N7 C3 demand-law | TOPIC REJECTED tracking |
| `acp_deliver.packets` (9 cols) / `pieces` (21 cols) / `tenant_tour_pages` | N7/N8 | `pieces.repair_budget`/`repair_log`/`review_status` (AA-396/AA-412 follow-up) |
| `acp_contract.tour_atoms` (22 cols) / `atom_decompose_jobs` / `s1_from_atom_runs` | N2/T5/T6 | `owner_scope` free-text (tenant_id hoặc `'platform'`), `distinctiveness`+`weight` là default chết — đừng dùng để lọc |
| `acp_contract.v_trip_registry` (view) | Contract cho N4-N6 | JOIN silver+gold, lọc `deleted_at IS NULL` (mig 090) |
| `shared.tenant_integrations` | T11 WordPress | 0 row — chưa tenant nào connect thật, KHÔNG phải bảng chết |
| `shared.tenant_brand_rule_versions` / `tenant_brand_rules` | T0 Brand | `services/acp_brand_brief_parser/db.py` |
| `shared.tenant_export_config` / `tenant_seo_config` | tenant config | |
| `gold_aa_internal.tenant_tour_versions` | T2 rewrite output | |
| `acp_shared.acp_quota_ledger` | GDPR/quota | `admin.py`, 0 row nhưng có caller |
| `acp_shared.acp_output_rules` | N7/N8 output rules | ⚠️ mất 1 FK constraint (`source_hitl_id`) do migration 121, KHÔNG bị DROP — xem gotcha bên dưới |

### Nhóm 2 — CIS S1 core (aa_internal, KHÁC ACPv1 hoàn toàn, sống độc lập)

| Bảng | Cột chính |
|---|---|
| `silver_aa_internal.raw_tours` (36 cols, 793 row) | PK=`tour_id` (KHÔNG phải `id`), `pipeline_status`/`review_status`/`source_status`/`lifecycle_stage` đều enum, `deleted_at`/`deleted_by` |
| `silver_aa_internal.generated_content` (35 cols, 228 row) | `aa_*` content cols, `satellite_used`/`satellite_account` (acc1/acc3), `human_edited`/`revalidate_passed` |
| `silver_aa_internal.quality_scores` (21 cols, 206 row) | `score_overall`, `brand_audit_status`/`brand_audit_codes`, `lessons_extracted` |
| `silver_aa_internal.seo_context` (14 cols, 50 row) | KHÔNG có `country` — luôn JOIN `raw_tours` |
| `silver_aa_internal.review_queue` (15 cols, 42 row) | `generated_content_id` nullable (mig 107 — T3 QA-gate reuse, xem gotcha bên dưới), `tenant_tour_version_id` |
| `silver_aa_internal.raw_sources` (37 row) / `upload_staging` (4 row) | S0 ingest |
| `gold_aa_internal.published_tours` (24 cols, 71 row) | Content col = `aa_name` (KHÔNG phải `title`), KHÔNG có `country` — JOIN `raw_tours` |
| `gold_aa_internal.content_exports` (0 row) | `v1_exports.py` — **đính chính:** CLAUDE.md ghi "table does not exist in shared schema" — SAI, bảng CÓ tồn tại, chỉ ở `gold_aa_internal` không phải `shared` |
| `gold_aa_internal.webhook_deliveries` (0 row) | Tech debt biết trước, deferred P2 — đúng như CLAUDE.md ghi |
| `shared.acp_runs` (0 row) | **"Naming trap" — KHÁC `acp_shared.acp_runs`** (bảng ACPv1 ĐÃ XOÁ ở migration 121). Đây là tracker A0-A3 admin pipeline thật, batch-keyed, `services/export/handler.py` ghi vào. KHÔNG đụng |
| `shared.pipeline_jobs` (46 row) / `pipeline_runs` (38 row) / `pipeline_lessons` (0 row, có caller `flag_fix_node.py`) | A0-A3 async job lifecycle + lesson mechanism |

### Nhóm 3 — Hạ tầng chung

`shared.schema_versions` (90, sau 121+122), `audit_log` (2), `tenants` (17 cols, 3 row —
`posts_per_week`, `is_canary`/`skip_hitl`, KHÔNG có cột `country` trong bảng gốc trước mig 054,
giờ có), `admin_users` (4), `membership_plans` (5), `notifications` (39), `tenant_api_usage` (3100
— rate-limit + admin traffic tracking, mig 110), `prompt_eval_runs` (3), 3 view (`v_batch_stats`,
`v_pipeline_summary`, `v_tenant_monthly_usage`), `public.checkpoint_migrations` (10 row — LangGraph
internal migration counter, cố ý giữ, xem Dead Table Registry).

### Nhóm 4 — Dead Table Registry (21 bảng, DROP THẬT 27/08/2026 16:55:09 UTC, cùng 1 transaction)

Bằng chứng đầy đủ: `docs/claude_audit/AA-258-259-acpv1-tables-audit.md` +
`docs/claude_audit/AA-479-schema-audit.md` trong `AA-CIS-App`. Verify post-commit: mọi bảng dưới
đây confirm `UndefinedTableError`/absent từ `information_schema.tables` qua 2 lượt query độc lập
(pre-commit SAVEPOINT-wrapped + post-commit fresh connection).

**Migration 121 (AA-477) — 15 bảng — cụm ACPv1 stage-chain S1→S4.2:**

| # | Bảng | Ngày xoá | Lý do | Code cũ từng dùng |
|---|---|---|---|---|
| 1 | `acp_shared.acp_runs` | 27/08/2026 | Root của cả cụm ACPv1 stage-chain. PRD §10: kiến trúc S2→S4.2 cũ "đập đi làm lại", 20 issue liên quan Canceled ở S104, chưa từng chạy production. | `services/acp_s3/`, `services/acp_s4/`, `services/acp_s4_evaluate/`, routers `v1_s1/v1_s3/v1_acp_gate/v1_s4_blog/v1_acp/admin_acp_proxy.py` — tất cả đã xoá ở AA-477 build |
| 2 | `acp_shared.acp_stage_runs` | 27/08/2026 | Con trực tiếp `acp_runs`, per-stage run tracking cho stage-chain cũ. | cùng cụm router/service trên |
| 3 | `acp_shared.acp_hitl_requests` | 27/08/2026 | HITL gate per-stage của kiến trúc cũ (3 gate/stage, EventBridge chain) — thay thế bởi T-series gate mới (Gate A/Gate B). | `v1_acp_gate.py` (đã xoá) |
| 4 | `acp_silver_s4.blog_drafts` | 27/08/2026 | Con của `acp_hitl_requests` (`hitl_request_id` FK) — draft blog content của S4 cũ, khác hoàn toàn `acp_shared.content_piece` (T9/T10 mới). | `services/acp_s4_blog/models.py`/`validator.py` (đã xoá, `cms/wordpress.py`+`cms/base.py` GIỮ LẠI vì T11 dùng thật) |
| 5 | `acp_shared.acp_lessons_agency` | 27/08/2026 | Lesson-extraction per-agency của stage-chain cũ, không có đường sống nào tới T-series mới. | `services/acp_s4/` (đã xoá) |
| 6 | `acp_shared.acp_lessons_shared` | 27/08/2026 | Lesson-extraction shared-pool của stage-chain cũ, tương tự trên. | `services/acp_s4/` (đã xoá) |
| 7 | `acp_shared.acp_run_context` | 27/08/2026 | Context state per-run của stage-chain cũ (1:1 với `acp_runs`). | `services/acp_s3/`, `services/acp_s4/` (đã xoá) |
| 8 | `acp_shared.acp_stage_checkpoints` | 27/08/2026 | Checkpoint per-stage của stage-chain cũ — khác `public.checkpoints` (LangGraph runtime, xem #19-21). | `services/acp_s3/`, `services/acp_s4/` (đã xoá) |
| 9 | `acp_shared.pipeline_checkpoints` | 27/08/2026 | Checkpoint tổng của `acp_runs`, cùng cụm với #8. | cùng cụm trên |
| 10 | `acp_silver_s3.ads_plan` | 27/08/2026 | Output S3 cũ (ads planning) — Lambda `aa-cis-dev-acp-s3-campaign-planner` đã xoá cùng đợt (Terraform draft AA-477). | `services/acp_s3/` (đã xoá — nguồn thật của Lambda, phát hiện giữa build) |
| 11 | `acp_silver_s3.content_calendars` | 27/08/2026 | Output S3 cũ (content calendar), cùng cụm #10. | `services/acp_s3/` (đã xoá) |
| 12 | `acp_silver_s4.social_content` | 27/08/2026 | Output S4 cũ (social content), khác hoàn toàn `content_piece` T9/T10 mới (channel='blog' hoặc social đều qua content_piece giờ). | `services/acp_s4/` (đã xoá) |
| 13 | `acp_gold_output.published_content` | 27/08/2026 | Output cuối cùng của stage-chain cũ — thay thế bởi `acp_shared.publish_log` (T11, migration 116, thiết kế MỚI hoàn toàn không kế thừa dữ liệu). | `services/acp_s4_evaluate/` (đã xoá) |
| 14 | `acp_silver_s2.visibility_reports` | 27/08/2026 | Output S2 cũ (visibility/SEO report) — S2 source (`services/acp/s2/`) đã không còn tồn tại thật (chỉ `__pycache__` rác, xác nhận `git ls-files` rỗng). | `services/acp/s2/` (source đã mất từ trước, chỉ còn bytecode rác) |
| 15 | `silver_aa_internal.tour_content_versions` | 27/08/2026 | Version snapshot gắn với `acp_run_id` (FK vào `acp_runs`) — cơ chế versioning cũ, thay thế bởi `gold_aa_internal.tenant_tour_versions` (T2 mới). | `services/acp_s3/`, `services/acp_s4/` (đã xoá) |

⚠️ **Constraint-only, KHÔNG phải table drop:** migration 121 cũng `ALTER TABLE
acp_shared.acp_output_rules DROP CONSTRAINT acp_output_rules_source_hitl_id_fkey` — bảng
`acp_output_rules` **VẪN SỐNG** (N7/N8, sản xuất thật), chỉ mất đúng 1 FK trỏ vào
`acp_hitl_requests` (đã xoá ở #3). Verify thật: insert 1 row mồ côi (`source_hitl_id` trỏ
`hitl_id` không tồn tại) → gọi `apply_output_rules()` thật (không mock) → hành vi đúng (rule
match, `run_count` tăng, `OutputRuleViolation` raise chính xác) — chứng minh logic ứng dụng chưa
bao giờ phụ thuộc constraint này.

**Migration 122 (AA-481) — 6 bảng — phát hiện thêm ở AA-479, ngoài phạm vi 121 (0 FK constraint):**

| # | Bảng | Ngày xoá | Lý do | Code cũ từng dùng |
|---|---|---|---|---|
| 16 | `acp_shared.acp_cms_publish_queue` | 27/08/2026 | CMS publish queue của `v1_s4_blog.py::hitl_decision()` cũ (migration 039, AA-100). T11's `publish_log` (mig 116) chỉ kế thừa Ý TƯỞNG thiết kế, KHÔNG kế thừa dữ liệu — migration 116 tự ghi rõ "mirrors the real precedent" trong comment. | `v1_s4_blog.py` (đã xoá ở AA-477) |
| 17 | `acp_shared.idempotency_keys` | 27/08/2026 | Tạo riêng "for S2 run dedup" (migration 029, AA-43). S2 source đã mất hoàn toàn (chỉ `__pycache__` rác). | `services/acp/s2/` (source đã mất từ trước) |
| 18 | `shared.lessons_registry` | 27/08/2026 | Bảng cũ nhất còn sót (migration 002/003, trước cả ACP). 0 caller bất kỳ đâu trong `api/`/`services/`. | Không tìm thấy caller thật nào — có thể chưa từng có, hoặc chết từ rất sớm |
| 19 | `public.checkpoints` | 27/08/2026 | LangGraph `AsyncPostgresSaver` runtime table, historically tạo bởi S2's graph checkpointing. 0 caller `checkpointer`/`AsyncPostgresSaver`/`PostgresSaver` nào trong code hiện tại. | `services/acp/s2/graph.py` (source đã mất) |
| 20 | `public.checkpoint_blobs` | 27/08/2026 | Cùng cụm LangGraph checkpoint với #19. | cùng trên |
| 21 | `public.checkpoint_writes` | 27/08/2026 | Cùng cụm LangGraph checkpoint với #19. | cùng trên |

⚠️ `public.checkpoint_migrations` (10 row) **KHÔNG bị xoá** — LangGraph library's own internal
migration counter, cố ý giữ (không cần thiết phải xoá để dọn 3 bảng data rỗng ở trên, và đây là
bookkeeping do thư viện quản lý chứ không phải app tự tạo).

Companion cleanup cùng đợt (không phải DB, nhưng cùng nguyên nhân gốc — code/test chết theo bảng):
7 file test xoá/sửa vì import `services.acp.s2.*` (module không còn source thật) — 6 file xoá
nguyên (`tests/acp_s2/` cả thư mục + `tests/acp/test_confidence_scorer.py`/
`test_s2_cannibalization.py`/`test_s2_keyword_cap.py`), 1 file sửa surgical
(`tests/acp/test_s1_state_bridge.py` — xoá `TestS2Guard`, giữ `TestS1CommitBeforePublish`). Bonus
tìm thấy giữa lúc verify migration 122 (không nằm trong danh sách 7 file gốc): xoá
`test_all_29_lessons_in_registry` khỏi `tests/integration/test_validation_integration.py` — test
này INSERT vào `shared.lessons_registry`, sẽ FAIL thật trên CI (Integration Tests job replay toàn
bộ `api/migrations/*.sql` trên Postgres container thật) nếu để nguyên sau khi migration 122 merge.

---

## Reference cột — các bảng dùng thường xuyên nhất khi debug/viết query

```
silver_aa_internal.raw_tours (PK=tour_id): tenant_id, batch_id, src_name, src_summary,
  src_highlights(jsonb), src_itineraries(text), country, duration, pipeline_status,
  review_status, source_status, lifecycle_stage, deleted_at

silver_aa_internal.generated_content (PK=id): tour_id, tenant_id, version_num, aa_name,
  aa_subtitle, aa_summary, aa_description, aa_highlights(jsonb), aa_itineraries, seo_title,
  seo_meta, model_editorial, status, satellite_used, satellite_account, human_edited,
  revalidate_passed, metadata(jsonb)

gold_aa_internal.published_tours (PK=id): tour_id, generated_content_id, tenant_id, aa_name,
  aa_subtitle, quality_score, s3_gold_path, master_status, deleted_at — KHÔNG có country, title

silver_aa_internal.seo_context: tour_id, keyword_search, top_keywords(jsonb),
  keyword_ideas(jsonb), people_also_ask(jsonb), related_keywords(jsonb) — KHÔNG có country

silver_aa_internal.review_queue: tour_id, generated_content_id(nullable — xem gotcha),
  tenant_id, review_status, tenant_tour_version_id, escalate_detail(jsonb)

shared.tenants (PK=tenant_id): slug, plan_tier, api_key_hash, rate_limit_rpm, is_active,
  country, posts_per_week, is_canary, skip_hitl

acp_contract.tour_atoms (PK=atom_id text): tour_id, owner_scope(text, tenant_id hoặc
  'platform'), text, distinctiveness(default chết), weight(hằng số), starred, deleted,
  source_hash, is_empty_marker, itinerary_day

acp_shared.angle_gate_request (PK=request_id): tenant_id, atom_id, trip_id, channel, goal,
  status, cta(nullable)
acp_shared.angle_gate_option (PK=option_id): request_id(FK), idx(0-2), name, why_it_works,
  formula_fit, best_final_style, recommended, chosen

acp_shared.content_piece (PK=piece_id): tenant_id, angle_gate_request_id(FK), attempt_number,
  content_text, status, held_reason, gate_ledger(jsonb), repair_log(jsonb)

acp_shared.publish_log (PK=publish_id): piece_id(FK), tenant_id, channel, status, external_id,
  external_url, unpublished_at, unpublished_by, last_error

acp_shared.acp_v2_runs (PK=run_id): tenant_id(TEXT không phải UUID!), year, month, week, status
acp_shared.acp_v2_slots (PK=slot_id text): run_id(FK), tenant_id(TEXT), channel, kind, tour_id,
  status, payload(jsonb)

acp_deliver.pieces (PK=piece_id text): run_id, tenant_id(TEXT), channel, body_tagged, status,
  gate_ledger(jsonb), repair_budget, review_status, reviewed_by

shared.schema_versions: version(varchar — CÓ giá trị non-numeric 'v1.0' etc, đừng cast ::int),
  applied_at, description
```

---

## FK Reference (63 quan hệ còn sống, `pg_constraint` — verify post-commit 27/08/2026)

Định dạng: `schema.bảng_con.cột_FK` → `schema.bảng_cha.cột_tham_chiếu` (cardinality). Cardinality
suy từ việc cột FK có đồng thời là PK/UNIQUE trên bảng con không (`1:1` nếu có, `N:1` nếu không —
không đoán ngoài 2 trường hợp này). 18 quan hệ cũ (17 do bảng bị DROP ở migration 121 + 1
constraint-only cũng ở migration 121) đã bị xoá khỏi phần này — xem "Dead Table Registry" ở trên
cho danh sách lịch sử đầy đủ nếu cần tra cứu.

**`acp_contract`**
- `acp_contract.s1_from_atom_runs.tour_id` → `silver_aa_internal.raw_tours.tour_id` (N:1)
- `acp_contract.tour_atoms.tour_id` → `silver_aa_internal.raw_tours.tour_id` (N:1)

**`acp_deliver`**
- `acp_deliver.pieces.packet_id` → `acp_deliver.packets.packet_id` (N:1)
- `acp_deliver.pieces.run_id` → `acp_shared.acp_v2_runs.run_id` (N:1)

**`acp_shared`** (20 quan hệ — mất 9 so với trước migration, xem Dead Table Registry cho 9 dòng đã xoá)
- `acp_shared.acp_quota_ledger.tenant_id` → `shared.tenants.tenant_id` (1:1)
- `acp_shared.acp_v2_slots.run_id` → `acp_shared.acp_v2_runs.run_id` (N:1)
- `acp_shared.angle_gate_option.request_id` → `acp_shared.angle_gate_request.request_id` (N:1)
- `acp_shared.angle_gate_request.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `acp_shared.competitor_index_cache.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `acp_shared.content_metric_snapshot.piece_id` → `acp_deliver.pieces.piece_id` (N:1)
- `acp_shared.content_metric_snapshot.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `acp_shared.content_piece.angle_gate_request_id` → `acp_shared.angle_gate_request.request_id` (N:1)
- `acp_shared.content_piece.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `acp_shared.publish_log.piece_id` → `acp_shared.content_piece.piece_id` (N:1)
- `acp_shared.publish_log.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `acp_shared.quarter_plan.current_version_id` → `acp_shared.quarter_plan_version.version_id` (N:1)
- `acp_shared.quarter_plan.year_plan_id` → `acp_shared.year_plan.year_plan_id` (N:1)
- `acp_shared.quarter_plan_version.plan_id` → `acp_shared.quarter_plan.plan_id` (N:1)
- `acp_shared.tenant_atom_state.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `acp_shared.tenant_atom_state.tour_id` → `silver_aa_internal.raw_tours.tour_id` (N:1)
- `acp_shared.tenant_config.tenant_id` → `shared.tenants.tenant_id` (1:1)
- `acp_shared.tenant_onboarding.portfolio_id` → `acp_shared.marketplace_portfolios.portfolio_id` (N:1)
- `acp_shared.tenant_onboarding.tenant_id` → `shared.tenants.tenant_id` (1:1)
- `acp_shared.year_plan.tenant_id` → `shared.tenants.tenant_id` (N:1)

**`acp_silver_s2`** (chỉ còn 1 bảng, 1 quan hệ)
- `acp_silver_s2.competitor_inputs.tenant_id` → `shared.tenants.tenant_id` (N:1)

**`gold_aa_internal`**
- `gold_aa_internal.content_exports.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `gold_aa_internal.published_tours.generated_content_id` → `silver_aa_internal.generated_content.id` (N:1)
- `gold_aa_internal.published_tours.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `gold_aa_internal.published_tours.tour_id` → `silver_aa_internal.raw_tours.tour_id` (1:1)
- `gold_aa_internal.tenant_tour_versions.parent_version_id` → `gold_aa_internal.tenant_tour_versions.id` (N:1)
- `gold_aa_internal.tenant_tour_versions.published_tour_id` → `gold_aa_internal.published_tours.id` (N:1)
- `gold_aa_internal.tenant_tour_versions.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `gold_aa_internal.webhook_deliveries.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `gold_aa_internal.webhook_deliveries.tour_id` → `silver_aa_internal.raw_tours.tour_id` (N:1)

**`shared`**
- `shared.acp_runs.batch_id` → `shared.pipeline_runs.batch_id` (1:1) — `shared.acp_runs` KHÁC
  `acp_shared.acp_runs` (naming trap, bảng kia đã xoá), KHÔNG đụng
- `shared.pipeline_runs.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `shared.tenant_api_usage.admin_user_id` → `shared.admin_users.id` (N:1)
- `shared.tenant_api_usage.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `shared.tenant_brand_rule_versions.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `shared.tenant_brand_rules.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `shared.tenant_export_config.tenant_id` → `shared.tenants.tenant_id` (1:1)
- `shared.tenant_integrations.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `shared.tenant_seo_config.tenant_id` → `shared.tenants.tenant_id` (1:1)
- `shared.tenants.plan_id` → `shared.membership_plans.id` (N:1)

**`silver_aa_internal`** (19 quan hệ — mất 2 so với trước migration, `tour_content_versions` đã xoá)
- `silver_aa_internal.generated_content.reviewed_by` → `shared.admin_users.id` (N:1)
- `silver_aa_internal.generated_content.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `silver_aa_internal.generated_content.tour_id` → `silver_aa_internal.raw_tours.tour_id` (N:1)
- `silver_aa_internal.quality_scores.generated_content_id` → `silver_aa_internal.generated_content.id` (N:1)
- `silver_aa_internal.quality_scores.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `silver_aa_internal.quality_scores.tour_id` → `silver_aa_internal.raw_tours.tour_id` (N:1)
- `silver_aa_internal.raw_sources.batch_id` → `shared.pipeline_runs.batch_id` (N:1)
- `silver_aa_internal.raw_sources.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `silver_aa_internal.raw_tours.batch_id` → `shared.pipeline_runs.batch_id` (N:1)
- `silver_aa_internal.raw_tours.reviewed_by` → `shared.admin_users.id` (N:1)
- `silver_aa_internal.raw_tours.source_id` → `silver_aa_internal.raw_sources.id` (N:1)
- `silver_aa_internal.raw_tours.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `silver_aa_internal.review_queue.generated_content_id` → `silver_aa_internal.generated_content.id` (N:1)
- `silver_aa_internal.review_queue.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `silver_aa_internal.review_queue.tenant_tour_version_id` → `gold_aa_internal.tenant_tour_versions.id` (N:1)
- `silver_aa_internal.review_queue.tour_id` → `silver_aa_internal.raw_tours.tour_id` (N:1)
- `silver_aa_internal.seo_context.tenant_id` → `shared.tenants.tenant_id` (N:1)
- `silver_aa_internal.seo_context.tour_id` → `silver_aa_internal.raw_tours.tour_id` (1:1)
- `silver_aa_internal.upload_staging.matched_tour_id` → `silver_aa_internal.raw_tours.tour_id` (N:1)

(`acp_gold_output`, `acp_silver_s3`, `acp_silver_s4`, `public` — 0 quan hệ, schema rỗng/gần rỗng
sau migration, không liệt kê.)

---

## CloudWatch Log Groups
| Service | Log Group |
|---------|-----------|
| ECS API | `/ecs/aa-cis-dev` ← đúng (stream prefix: `api/api/...`) |
| ECS API (rỗng) | `/ecs/aa-cis-dev-api` ← sai, luôn rỗng |
| Lambda ingestion/seo/content/validation/export/brand-brief-parser | `/aws/lambda/aa-cis-dev-{name}` |
| ECS log retention thật | **14 ngày** (xác nhận trực tiếp qua `describe-log-groups`, KHÔNG phải 30 như config từng tưởng — AA-385/AA-477) |

## Useful CLI Commands (single-line, WSL2-safe)
```bash
TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile aa365-admin --region us-west-1 --query 'taskArns[0]' --output text)
aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-api --desired-count 1 --profile aa365-admin --region us-west-1
aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-api --desired-count 0 --profile aa365-admin --region us-west-1
aws rds start-db-instance --db-instance-identifier aa-cis-dev-db --profile aa365-admin --region us-west-1
aws rds stop-db-instance --db-instance-identifier aa-cis-dev-db --profile aa365-admin --region us-west-1
```

---

## S3-Mediated ECS Exec (canonical — dùng asyncpg, KHÔNG psycopg2, container không có sẵn cả 2 nên tự chọn asyncpg cho pattern async chuẩn của repo)

```bash
cat > /tmp/script.py << 'PYEOF'
import asyncio, json, boto3, asyncpg
from urllib.parse import urlparse

async def main():
    sm = boto3.client("secretsmanager", region_name="us-west-1")
    secret = sm.get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    dsn = secret.strip()
    if dsn.startswith("{"):
        d = json.loads(dsn)
        dsn = d.get("dsn") or d.get("DATABASE_URL") or list(d.values())[0]
    u = urlparse(dsn)
    conn = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username,
        password=u.password, database=u.path.lstrip("/"), ssl="require")
    rows = await conn.fetch("SELECT ...")  # luôn schema-qualify
    with open("/tmp/result.json", "w") as f:
        json.dump([dict(r) for r in rows], f, indent=2, default=str)
    await conn.close()

asyncio.run(main())
PYEOF

aws s3 cp /tmp/script.py s3://aa-cis-bronze-005097885195/scripts/script.py --profile aa365-admin --region us-west-1
URL=$(aws s3 presign s3://aa-cis-bronze-005097885195/scripts/script.py --profile aa365-admin --region us-west-1 --expires-in 300)
TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile aa365-admin --region us-west-1 --query 'taskArns[0]' --output text)
aws ecs execute-command --cluster aa-cis-dev-cluster --task $TASK_ARN --container api --interactive --command "sh -c 'curl -s \"$URL\" -o /tmp/s.py && python3 /tmp/s.py; python3 -c \"import boto3; boto3.client(\\\"s3\\\", region_name=\\\"us-west-1\\\").upload_file(\\\"/tmp/result.json\\\", \\\"aa-cis-bronze-005097885195\\\", \\\"scripts/result.json\\\")\" && echo UPLOAD_OK'" --profile aa365-admin --region us-west-1
aws s3 cp s3://aa-cis-bronze-005097885195/scripts/result.json /tmp/result.json --profile aa365-admin --region us-west-1 && cat /tmp/result.json
```
Ghi chú thực chiến (27/08): SSM interactive session hay bị cắt output giữa chừng (`Cannot perform
start session: EOF`) khi script in nhiều dòng — luôn ghi kết quả ra file rồi upload lên S3 rồi
`aws s3 cp` tải về đọc, ĐỪNG tin output trực tiếp trong terminal SSM cho việc quan trọng.

## DBeaver (SSM Tunnel via ECS container)
```bash
TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile aa365-admin --region us-west-1 --query 'taskArns[0]' --output text)
TASK_ID=$(echo $TASK_ARN | cut -d'/' -f3)
RUNTIME_ID=$(aws ecs describe-tasks --cluster aa-cis-dev-cluster --tasks $TASK_ARN --profile aa365-admin --region us-west-1 --query 'tasks[0].containers[0].runtimeId' --output text)
aws ssm start-session --target "ecs:aa-cis-dev-cluster_${TASK_ID}_${RUNTIME_ID}" --document-name AWS-StartPortForwardingSessionToRemoteHost --parameters "{\"host\":[\"<RDS_ENDPOINT — verify live>\"],\"portNumber\":[\"5432\"],\"localPortNumber\":[\"15432\"]}" --profile aa365-admin --region us-west-1
```
DBeaver: host=`localhost`, port=`15432`, db=`aa_cis_dev`, user=`aa_cis_admin`.

---

## Critical JOIN Patterns (CIS S1 core — vẫn đúng)

```sql
-- country cho published_tours (không có cột country)
SELECT pt.id, pt.aa_name, rt.country
FROM gold_aa_internal.published_tours pt
JOIN silver_aa_internal.raw_tours rt ON pt.tour_id = rt.tour_id

-- country cho seo_context (không có cột country)
SELECT sc.keyword_search, rt.country
FROM silver_aa_internal.seo_context sc
JOIN silver_aa_internal.raw_tours rt ON sc.tour_id = rt.tour_id

-- Full tour pipeline status
SELECT rt.src_name, rt.country, gc.aa_name, qs.score_overall, pt.published_at
FROM silver_aa_internal.raw_tours rt
JOIN silver_aa_internal.generated_content gc ON gc.tour_id = rt.tour_id
JOIN silver_aa_internal.quality_scores qs ON qs.tour_id = rt.tour_id
JOIN gold_aa_internal.published_tours pt ON pt.tour_id = rt.tour_id

-- T8→T9→T11 full chain cho 1 tenant (T-series, thay cho ACP run status cũ đã xoá)
SELECT r.request_id, o.name AS chosen_angle, p.piece_id, p.status AS piece_status,
       pl.status AS publish_status, pl.external_url
FROM acp_shared.angle_gate_request r
LEFT JOIN acp_shared.angle_gate_option o ON o.request_id = r.request_id AND o.chosen = TRUE
LEFT JOIN acp_shared.content_piece p ON p.angle_gate_request_id = r.request_id
LEFT JOIN acp_shared.publish_log pl ON pl.piece_id = p.piece_id
WHERE r.tenant_id = $1
```

## ⚠️ Common Gotchas
- `raw_tours` PK = `tour_id` (KHÔNG phải `id`)
- `published_tours` KHÔNG có `country` → luôn JOIN `raw_tours`
- `seo_context` KHÔNG có `country` → luôn JOIN `raw_tours`
- `published_tours` cột tên = `aa_name` (KHÔNG phải `title`)
- Tất cả UUID cần `default=str` trong `json.dumps()`
- `acp_shared.acp_runs` ≠ `shared.acp_runs` — 2 bảng KHÁC NHAU (naming trap, AA-438 #15).
  `acp_shared.acp_runs` **ĐÃ XOÁ** (migration 121, 27/08/2026, ACPv1 chết); `shared.acp_runs` là
  tracker A0-A3 thật, KHÔNG đụng, vẫn sống.
- `review_queue.generated_content_id` **nullable** từ migration 107 (AA-425) — bảng này giờ dùng
  chung cho CẢ luồng A1→A2 admin gốc (luôn có `generated_content_id`) LẪN luồng T3 QA-gate
  tenant-facing mới (dùng `tenant_tour_version_id` thay thế, `generated_content_id=NULL` là ĐÚNG
  THIẾT KẾ, không phải mồ côi). Đừng viết lại query "orphan-detection" kiểu cũ mà quên điều kiện
  loại `tenant_tour_version_id IS NOT NULL`.
- `acp_v2_runs`/`acp_v2_slots`.`tenant_id` là **TEXT**, không phải UUID (khác hầu hết bảng khác)
  — không `::uuid` cast khi so sánh, so trực tiếp string.
- `acp_contract.tour_atoms.distinctiveness`/`weight` — tên gợi ý chất lượng nhưng là default
  chết/hằng số cứng, ĐỪNG dùng để lọc/rank atom.
- `shared.schema_versions.version` là `character varying`, KHÔNG phải integer — có giá trị cũ
  dạng `v1.0`/`v2.0` — `ORDER BY version::int` sẽ LỖI, dùng `ORDER BY applied_at`.
- `acp_shared.acp_output_rules.source_hitl_id` **không còn FK constraint** (mất ở migration 121,
  bảng đích `acp_hitl_requests` đã xoá) — cột vẫn tồn tại, giờ có thể trỏ tới giá trị không tồn
  tại thật (mồ côi hợp lệ), đừng viết code/query giả định integrity được DB enforce ở cột này nữa.

---

## Phương pháp luận đã đúc kết (đọc trước khi audit/xoá bảng bất kỳ)

1. **FK-graph-first qua `pg_constraint`, KHÔNG phải `information_schema`** (bài học AA-473/477)
   — nhưng `pg_constraint` chỉ bắt được FK CÓ constraint thật ở tầng DB. Cột đặt tên `run_id`/
   `tenant_id` KHÔNG có FK constraint (`acp_cms_publish_queue` là ví dụ thật, AA-479) sẽ KHÔNG
   hiện trong FK-graph traversal dù liên hệ ở tầng ứng dụng có thật — luôn bổ sung quét "0 row +
   0 caller code" độc lập, đừng chỉ tin FK-graph.
2. **Cùng thư mục/package KHÔNG có nghĩa cùng số phận** (bài học STEP0 lần 2, AA-477) —
   `services/acp_s4_blog/cms/wordpress.py` sống thật (T11) trong khi `publisher.py` cùng thư mục
   đã chết. Xóa file, không xóa thư mục, luôn grep từng file riêng.
3. **0 row không chứng minh "chưa từng dùng"** — kiểm tra `git ls-files` cho thư mục source liên
   quan trước khi kết luận "0 caller" (bài học `services/acp/s2/` — source đã xoá thật, chỉ còn
   `__pycache__` rác không track git, dễ nhầm "còn code" nếu chỉ nhìn `find`/`ls`).
4. **Migration comment tự ghi lại quan hệ thiết kế** — đọc comment của migration MỚI NHẤT liên
   quan tới 1 bảng nghi chết trước khi kết luận độc lập (VD migration 116 tự ghi rõ nó "mirrors"
   `acp_cms_publish_queue` — xác nhận đây là kế thừa THIẾT KẾ, không phải bảng cũ còn dùng).
5. **Test file cũ có thể đang test module đã xoá** — 1 pytest FAIL không tự động nghĩa là "DB
   không có sẵn trong sandbox"; đọc traceback thật trước khi gộp vào nhóm "pre-existing DB-
   dependent failures" mặc định.
6. **CI replay migration thật → test cũ tham chiếu bảng sắp DROP là lỗi CI thật, không phải rủi ro
   lý thuyết** (bài học AA-481, phát hiện giữa lúc verify migration 122) — CI's Integration Tests
   job dựng `postgres:15` container thật và chạy lại TOÀN BỘ `api/migrations/*.sql` trước khi test
   — bất kỳ test nào INSERT/SELECT vào bảng nằm trong migration DROP sắp merge sẽ FAIL thật trên
   CI, không phải flaky sandbox. Luôn `grep` tên bảng sắp DROP trong `tests/integration/` (không
   chỉ `tests/unit/` hay thư mục cùng tên module) trước khi coi migration DROP là "chỉ ảnh hưởng
   DB, không ảnh hưởng test".
