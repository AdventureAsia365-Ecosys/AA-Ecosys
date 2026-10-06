# Dead Table Registry

> Nguồn: trích từ skill `aa-cis-schema` cũ (bản 27/08/2026), chuyển ra đây làm tài liệu lịch sử
> trong AA-733 (06/10/2026). 21 bảng dưới đây đã bị `DROP` THẬT ngày 27/08/2026 16:55:09 UTC trong
> cùng một transaction (migration 121 + 122). Đọc file này trước khi nghi một bảng "biến mất".
>
> Bằng chứng đầy đủ: `docs/claude_audit/AA-258-259-acpv1-tables-audit.md` +
> `docs/claude_audit/AA-479-schema-audit.md` trong AA-CIS-App. Verify post-commit: mọi bảng dưới
> đây confirm `UndefinedTableError` / absent khỏi `information_schema.tables` qua 2 lượt query độc
> lập (pre-commit SAVEPOINT-wrapped + post-commit fresh connection).

## Migration 121 (AA-477) — 15 bảng — cụm ACPv1 stage-chain S1→S4.2

| # | Bảng | Lý do | Code cũ từng dùng |
|---|---|---|---|
| 1 | `acp_shared.acp_runs` | Root của cả cụm ACPv1 stage-chain. PRD §10: kiến trúc S2→S4.2 cũ "đập đi làm lại", 20 issue liên quan Canceled ở S104, chưa từng chạy production. | `services/acp_s3/`, `services/acp_s4/`, `services/acp_s4_evaluate/`, routers `v1_s1/v1_s3/v1_acp_gate/v1_s4_blog/v1_acp/admin_acp_proxy.py` — tất cả đã xoá ở AA-477 |
| 2 | `acp_shared.acp_stage_runs` | Con trực tiếp `acp_runs`, per-stage run tracking cho stage-chain cũ. | cùng cụm router/service trên |
| 3 | `acp_shared.acp_hitl_requests` | HITL gate per-stage của kiến trúc cũ (3 gate/stage, EventBridge chain) — thay bởi T-series gate mới (Gate A/Gate B). | `v1_acp_gate.py` (đã xoá) |
| 4 | `acp_silver_s4.blog_drafts` | Con của `acp_hitl_requests` (`hitl_request_id` FK) — draft blog của S4 cũ, khác hẳn `acp_shared.content_piece` (T9/T10 mới). | `services/acp_s4_blog/models.py`/`validator.py` (đã xoá; `cms/wordpress.py`+`cms/base.py` GIỮ vì T11 dùng) |
| 5 | `acp_shared.acp_lessons_agency` | Lesson-extraction per-agency của stage-chain cũ, không có đường sống tới T-series mới. | `services/acp_s4/` (đã xoá) |
| 6 | `acp_shared.acp_lessons_shared` | Lesson-extraction shared-pool của stage-chain cũ. | `services/acp_s4/` (đã xoá) |
| 7 | `acp_shared.acp_run_context` | Context state per-run của stage-chain cũ (1:1 với `acp_runs`). | `services/acp_s3/`, `services/acp_s4/` (đã xoá) |
| 8 | `acp_shared.acp_stage_checkpoints` | Checkpoint per-stage của stage-chain cũ — khác `public.checkpoints` (LangGraph runtime). | `services/acp_s3/`, `services/acp_s4/` (đã xoá) |
| 9 | `acp_shared.pipeline_checkpoints` | Checkpoint tổng của `acp_runs`, cùng cụm với #8. | cùng cụm trên |
| 10 | `acp_silver_s3.ads_plan` | Output S3 cũ (ads planning) — Lambda `aa-cis-dev-acp-s3-campaign-planner` đã xoá cùng đợt. | `services/acp_s3/` (đã xoá) |
| 11 | `acp_silver_s3.content_calendars` | Output S3 cũ (content calendar), cùng cụm #10. | `services/acp_s3/` (đã xoá) |
| 12 | `acp_silver_s4.social_content` | Output S4 cũ (social content), khác hẳn `content_piece` T9/T10 mới. | `services/acp_s4/` (đã xoá) |
| 13 | `acp_gold_output.published_content` | Output cuối stage-chain cũ — thay bởi `acp_shared.publish_log` (T11, migration 116, thiết kế mới, không kế thừa dữ liệu). | `services/acp_s4_evaluate/` (đã xoá) |
| 14 | `acp_silver_s2.visibility_reports` | Output S2 cũ (visibility/SEO report) — S2 source (`services/acp/s2/`) đã không còn tồn tại. | `services/acp/s2/` (source đã mất, chỉ còn bytecode) |
| 15 | `silver_aa_internal.tour_content_versions` | Version snapshot gắn với `acp_run_id` (FK vào `acp_runs`) — versioning cũ, thay bởi `gold_aa_internal.tenant_tour_versions` (T2 mới). | `services/acp_s3/`, `services/acp_s4/` (đã xoá) |

**Constraint-only, KHÔNG phải table drop:** migration 121 cũng `ALTER TABLE acp_shared.acp_output_rules DROP CONSTRAINT acp_output_rules_source_hitl_id_fkey` — bảng `acp_output_rules` VẪN SỐNG (N7/N8), chỉ mất 1 FK trỏ vào `acp_hitl_requests` (đã xoá ở #3).

## Migration 122 (AA-481) — 6 bảng — phát hiện thêm ở AA-479 (0 FK constraint)

| # | Bảng | Lý do | Code cũ từng dùng |
|---|---|---|---|
| 16 | `acp_shared.acp_cms_publish_queue` | CMS publish queue của `v1_s4_blog.py::hitl_decision()` cũ (migration 039). `publish_log` (mig 116) chỉ kế thừa ý tưởng thiết kế, không kế thừa dữ liệu. | `v1_s4_blog.py` (đã xoá ở AA-477) |
| 17 | `acp_shared.idempotency_keys` | Tạo riêng "for S2 run dedup" (migration 029). S2 source đã mất hoàn toàn. | `services/acp/s2/` (source đã mất) |
| 18 | `shared.lessons_registry` | Bảng cũ nhất còn sót (migration 002/003, trước cả ACP). 0 caller trong `api/`/`services/`. | Không tìm thấy caller thật |
| 19 | `public.checkpoints` | LangGraph `AsyncPostgresSaver` runtime table, tạo bởi S2's graph checkpointing. 0 caller hiện tại. | `services/acp/s2/graph.py` (source đã mất) |
| 20 | `public.checkpoint_blobs` | Cùng cụm LangGraph checkpoint với #19. | cùng trên |
| 21 | `public.checkpoint_writes` | Cùng cụm LangGraph checkpoint với #19. | cùng trên |

**`public.checkpoint_migrations` (10 row) KHÔNG bị xoá** — LangGraph library's own internal migration counter, cố ý giữ (bookkeeping do thư viện quản lý, không phải app tự tạo).
