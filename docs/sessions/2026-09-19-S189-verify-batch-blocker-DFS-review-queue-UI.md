# S189 — Verify Bedrock Batch acc3 (blocker) + DFS refill + DFS TTL + Review Queue UI redesign (Kiro, 2026-09-19)

Tác nhân: **Kiro**. Tiếp nối S188. Phiên dài, nhiều điều tra + 3 PR merged.

## Trạng thái
- **Ưu tiên đầu phiên: AA-621 (batch atomize)** — nhưng verify bước 0 phát hiện **Bedrock Batch acc3 chưa được AWS enable** → chặn cả AA-621/606/G4/G5. Mở AWS support case, tạo blocker AA-624. KHÔNG build AA-621 (build trên nền chưa entitlement = vô nghĩa).
- Xoay sang các việc không phụ thuộc batch: **AA-625 (DFS TTL) + AA-626 (Review Queue UI)** — cả 2 Done, merged, verify live Dev.
- Dọn 2 trạng thái Linear In Progress giả: **AA-615→Backlog**, **AA-612→Done**.

## Thay đổi Codebase (3 PR merged vào main)

### AA-625 — DFS cache TTL 24h → 7 ngày (PR #405, `184a57e`)
- `services/seo_intelligence/handler.py`: thêm hằng số `_SEO_CACHE_TTL_SECONDS = 7*24*3600`, dùng cho 2 `cache.set()` (nhánh fetched + custom_keywords) + `seo_context.expires_at`. KHÔNG đổi cache key/scope.
- `tests/integration/test_seo_integration.py::test_cache_ttl_is_set` cập nhật 7 ngày.
- Lý do: rerun rải nhiều ngày → cache 24h hết hạn giữa chừng → tốn lại tiền DFS cho cùng seed/market. Search volume travel keyword đổi chậm (tuần/tháng).

### AA-626 — Review Queue table redesign + dismiss (PR #406, `f54d593`) + follow-up (PR #407, `33ff7cd`)
**Backend:**
- Migration `158_review_status_dismissed.sql`: `ALTER TYPE review_status_enum ADD VALUE 'dismissed'`. **Applied Dev DB** (verify enum: pending/approved/rejected/skipped/superseded/dismissed).
- `POST /admin/review-queue/{id}/dismiss` (admin_pipeline.py) — copy mẫu supersede: flip pending→dismissed, KHÔNG đụng generated_content, KHÔNG export. **Cách A** (Nghiệp chốt): chỉ ẩn row hiện tại; guard `_enqueue_review` vẫn scoped 'pending' nên fail thật tương lai vẫn enqueue lại. 'dismissed' ẩn khỏi view status=all.
- GET /admin/review-queue: +`gc.version_num`, +`qs.brand_audit_status`.
- `get_tenant_details` (admin.py): +subquery `pending_review_count` (nhánh internal) cho badge; nhánh tenant default 0 (tránh KeyError).

**Frontend Review Queue (làm lại) — `frontend/app/admin/review/page.tsx`:**
- Card → BẢNG (`ReviewRow` thay `ReviewCard`), cột: Tour/Country/Version/Written/Score/Reasons/Actions. Row click → expand `ReviewEditor` cũ (xem chi tiết nội dung + edit/save/re-validate).
- Giữ 100% chức năng cũ: approve/reject/regenerate/supersede/pollJob/RegenerateModal. Thêm nút **Dismiss** (icon Ban).
- Chip lỗi phân màu (`ReasonChips` + `codeSeverity`): đỏ=product-truth (`PRODUCT_TRUTH_CODES`), cam=brand/style (`BRAND_STYLE_CODES`), xám=khác + legend.
- **Follow-up (#407):** sticky header (thead position:sticky, Card overflow visible); sort thêm Tour+Version (đủ 5 cột + mũi tên); deep-link `?tour_id=` (đọc window.location.search, lọc client-side, banner "Showing failed versions for X" + Clear).
- UI TOÀN tiếng Anh (Nghiệp yêu cầu — verify grep 0 dấu tiếng Việt).

**Frontend Master Content (CHỈ THÊM) — `frontend/app/admin/master-content/page.tsx`:**
- Badge "⚠ N failed" ở cột Versions (khi `pending_review_count>0`) link `/admin/review?tour_id=<id>`. KHÔNG đổi layout (Nghiệp dặn trang này đang ổn).

## Thay đổi Hạ tầng
- **KHÔNG terraform.** 1 migration DB `158_review_status_dismissed.sql` applied Dev (ALTER TYPE ADD VALUE, idempotent, không đụng data) qua ECS task container `api` + admin secret `aa-cis/dev/rds`.
- **AWS support case `178979743800653`** mở cho acc3 (786888028788) enable Bedrock Batch Inference — Service limit increase → General (Basic Support không mở được Technical case). Chờ AWS.
- **DFS refill:** chị Thư nạp $50 (tài khoản `thu@adventure.asia`), balance -$0.04 → $49.96 (tổng nạp $201). Verify search_volume/live HTTP 200 (hết 402).

## Bằng chứng verify
- **AA-621 bước 0 (điều tra + submit thật):** Terraform acc3 (accounts/acc3-bedrock/main.tf+batch.tf, modules/s3) khai báo ĐẦY ĐỦ Batch perm; submit S1 batch 100 tour chưa viết trong container → IAM assume acc3 OK, S3 manifest upload OK (1.93MB), **CreateModelInvocationJob FAIL: ValidationException "account is not authorized... create a support case"** (service-level entitlement, KHÔNG phải IAM). ListModelInvocationJobs cũng AccessDenied (policy read live thiếu). → AA-606 cũng chưa từng chạy batch job thật.
- **AA-625:** py_compile + flake8 OK; 19 SEO unit test pass; CI PR #405 6/6; `git show origin/main` xác nhận hằng số.
- **AA-626:** py_compile + flake8 OK (fix 1 E501); `next build` EXIT=0 (TS pass cả 2 trang); CI #406+#407 đều pass; **verify LIVE domain Dev** (api-cis.lumiguides.it.com): GET review-queue trả version_num+brand_audit_status; POST dismiss id giả → **409 không 500** (chứng minh enum 'dismissed' nhận); get_tenant_details có pending_review_count (116/116 row, 41 pending). Deploy Dev + Vercel SUCCESS trên f54d593 + 33ff7cd.

## DB thật (query S189, admin secret bypass RLS)
- raw_tours: 647 ingested + 116 published (not trashed); 124 tour distinct có generated_content (180 version: 122 approved/116 tour + 58 hitl/44 tour).
- published_tours (Master Content) = 116, 1 row/tour (UPSERT khi publish).
- review_queue pending = 58 version / 44 tour. **Toàn bộ rớt 17/09 sáng (gate CŨ trước AA-608 fix), 52/58 là manual_check điểm 8-9** — data test cũ, sẽ dọn khi G4/G5 rerun.

## Còn lại (việc chưa xong)
- **AA-627** (DFS balance daily alert — chỉ DFS, đọc user_data 1 lần/ngày, cảnh báo dưới ngưỡng; OpenAI để platform tự quản) — Backlog, CHƯA code.
- **AA-624** blocker — chờ AWS enable Batch cho acc3 (case 178979743800653). Khi xong: test batch nhỏ + `terraform apply` acc3 fix ListModelInvocationJobs + build AA-621 + G4/G5.
- **AA-621** batch atomize — chặn bởi AA-624.
- G4/G5 (AA-599/600) rerun 763 tour — chặn bởi AA-621. Lưu ý: nếu rerun sync thì DFS đã có tiền lại; nên gom theo country tận dụng cache 7 ngày mới.
- AA-613/614/615 (redesign social tenant) chưa làm.
- Review Queue: chưa làm "toggle gộp theo tour" + "summary strip nhóm theo lý do" (ngoài scope AA-626, bổ sung sau nếu Nghiệp thấy cần).

## Lưu ý kỹ thuật (cho phiên sau)
- **Bedrock Batch acc3 = service-level entitlement, KHÔNG phải IAM.** IAM/S3/inference-profile đã đúng hết. `ValidationException "not authorized...create a support case"` ≠ `AccessDeniedException`. Chỉ AWS support mở được. Basic Support plan → chỉ mở "Service limit increase → General" (Technical bị chặn).
- **DFS user_data MIỄN PHÍ** (`GET /appendix/user_data`, cost 0) → dùng cho balance alert AA-627. **OpenAI KHÔNG có API đọc số dư** (chỉ usage/costs = đã tiêu) → để platform OpenAI tự chặn.
- DFS `fetch_all` = 3 request tính phí/lần MISS (search_volume + SERP advanced + keyword_ideas). Cache Redis theo (seed, location_code) TTL giờ 7 ngày.
- **Shell WSL cực lag khi tích tụ nhiều control_bash_process nền chưa stop** — nhớ stop process sau mỗi lần dùng; nhiều process running đọng làm execute_bash nuốt lệnh/không tạo file. gh pr checks --watch hay treo → dùng `gh pr view --json mergeStateStatus` (CLEAN=merge được) + `timeout 60 gh ...`. gh pr merge --squash --auto. Verify merge bằng `git log origin/main --oneline`.
- **cwd param = WSL path bị convert thành Windows `\home\...`** làm cd fail → BỎ cwd, dùng `cd /home/... &&` trong lệnh + `--repo` cho gh.
- Verify FE PHẢI `next build` đầy đủ + kiểm Vercel deploy status (GitHub "Deploy Dev" = ECS backend). Live verify domain Dev = gọi thẳng `https://api-cis.lumiguides.it.com/admin/*` với header `X-Admin-Secret` (secret trong frontend/.env.local, KHÔNG echo value).
- Migration apply THỦ CÔNG (không auto deploy) qua ECS exec container `api` + admin secret aa-cis/dev/rds.

Log local này: `docs/sessions/2026-09-19-S189-verify-batch-blocker-DFS-review-queue-UI.md`.
