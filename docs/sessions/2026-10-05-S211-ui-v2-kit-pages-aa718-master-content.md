# S211 — UI v2 rebuild: kit→Settings tab, AA-669 My Content, AA-718 Master Content (6-bug + redesign), fix worker deploy (05/10/2026)

**Tác nhân:** Kiro (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:447` + `aa-cis-dev-worker:2` (worker vừa nhận deploy lần đầu sau fix) · **Migration mới nhất:** CIS 203 (không có migration mới phiên này; chỉ backfill dữ liệu + đổi code API)

## Trạng thái
Tiếp nối S210 (AA-662 UI kit mới ở thiết kế). Phiên này **hoàn thành AA-662 + AA-719 + AA-669 + AA-718** và sửa 2 bug ops. Làm tuần tự từng issue = 1 PR, verify (next build + eslint + render Dev + endpoint live cho backend), merge tuần tự, main sạch. **10 PR merged** phiên này.

## Thay đổi Codebase (AA-CIS-App)
| PR | Issue | Nội dung |
|---|---|---|
| #551 | AA-662 PR1 | UI kit `app/_kit/` (DataTable TanStack + Drawer/Modal/Toast/PageHeader/Tabs/Badge/StatusBadge/EmptyState/ErrorState/Skeleton + apiGet/apiSend) + react-query QueryClientProvider app-wide (root layout). Thêm `@tanstack/react-table`. |
| #552 | AA-662 PR2 + AA-719 | Review Queue → kit DataTable + react-query (useQuery/useMutation); **AA-719** bulk multi-select regenerate + **non-blocking regenerate** (run-tour-async đã trả 202+job_id → bỏ await pollJob, đóng modal ngay, mark row regenerating, refetchInterval 5s tới khi rời queue). Tách reviewApi/reviewModel/ReviewEditor/RegenerateModal. |
| #553 | AA-662 PR3 | My Content (CatalogTab, t4-pool) → kit DataTable + Drawer + react-query; bỏ 2 setInterval poll → 1 refetchInterval. Tách CatalogDrawer/catalogApi. |
| #554 | AA-662 | middleware allow-list cho `/admin/kit-demo` (sau đó bỏ ở #557). |
| #555 | AA-662 | (ban đầu) sidebar nav item UI Kit + bỏ mã "AA-662" khỏi text UI kit-demo. |
| #556 | AA-669 | My Content t10-review (ReviewList, content pieces — KHÁC t4-pool) → kit DataTable + Drawer + bulk export/publish + react-query. Giữ copy-lock + tenant-safe + ready_state. |
| #557 | AA-662 | **UI kit → tab trong Settings** (`SettingsKitTab.tsx`, `/admin/settings?tab=ui-kit`); bỏ route standalone `/admin/kit-demo` + nav item + middleware entry (sửa đúng ý Nghiệp: kit là tab Settings, không phải mục nav riêng). |
| #558 | AA-718 BE | `admin.py::get_tenant_details` internal branch: server-side page/page_size/sort/sort_dir/country/master_status/score/search + COUNT thật + filter-aware avg_quality + windowed cost 30d + derived display_status pipeline run. |
| #559 | AA-718 | **Hotfix**: #558 chèn helper `_derive_run_display_status` GIỮA `@router.get` và `async def` → decorator bind nhầm helper → endpoint 422 trên Dev. Đưa helper lên trước decorator. |
| #560 | AA-718 FE | master-content/page.tsx → react-query + server-side (sortable headers, server pagination theo pagination.total, filter-aware stat cards, windowed cost label, kit StatusBadge display_status). Giữ nguyên version expand/compare modals/trash/restore/activate/export. |
| #561 | AA-651 + AA-718 | Fix deploy worker (lệch tên) + mark stale run 'stalled'. |

## Thay đổi dữ liệu / điều tra (ECS exec, không migration)
- **AA-718 backfill** (an toàn, chỉ counter): điều tra pipeline_runs qua ECS exec — 46 run (29 completed, 17 ingesting). 15/17 ingesting là **chưa chạy thật** (751 tour còn `pipeline_status='ingested'`) → KHÔNG flip status (sẽ sai). Chỉ recompute `tours_passed` = COUNT published: **26 run sai → 0** (`UPDATE 26`). KHÔNG đụng status/content/publish.

## Fix 2 bug ops (phát hiện khi Nghiệp xem deploy log + pipeline panel)
- **AA-651 worker deploy (bug thật, đã verify live):** `deploy-dev.yml` tìm `${ECS_SERVICE}-worker` = `aa-cis-dev-api-worker` (ECS_SERVICE=`aa-cis-dev-api`) nhưng service thật là `aa-cis-dev-worker` → describe-services không khớp → **mọi deploy skip worker** → worker kẹt task-def `:1` từ S210 (chạy code cũ) trong khi api ở `:446`. Fix: derive `ECS_WORKER_SERVICE=${ECS_SERVICE%-api}-worker` qua step `$GITHUB_ENV`. **Verify sau fix: worker lên `:2`** (api `:447`).
- **AA-718 display_status cho run cũ bỏ dở:** run `ingesting` + partial progress hiển thị "running" kể cả batch 2 tháng trước (vd 20/07, 1/12 passed). Thêm ngưỡng tuổi: partial + started_at > 24h → **"stalled"**, mới → "running". Thêm tone `stalled`/`ingested` vào kit StatusBadge.

## Bằng chứng verify
- Mỗi PR: next build pass + eslint 0 errors (vài warning pre-existing untouched) + 5 CI jobs xanh + Vercel SUCCESS; merge tuần tự main sạch.
- **AA-718 endpoint live** (sau deploy): `GET /admin/tenants/{aa_internal}/details` HTTP 200 — không filter `catalog_total:207`, filter China `catalog_total:121` + `avg_quality:7.76`, `pagination.total` đúng, `display_status:ingested`, `llm_cost_window_usd` + "last 30 days".
- **Worker deploy fix:** ECS describe-services xác nhận `aa-cis-dev-api:447` + `aa-cis-dev-worker:2` (trước fix worker kẹt `:1`).
- Render Dev headless (middleware fail-open-in-dev + env API_URL chết): kit-demo/review/my-content/master-content mount sạch (0 pageerror), stat cards + toolbar + states render đúng brand. (Data thật cần admin login; render-bot 401 → error/empty state hợp lệ.)

## Jira / Linear
- **PR-15** (chị Thư comment mới nhất 05/10): Bhutan 2 NCC >30 tour, lấy file `Bhutan (Newtemplate)` ở cột Raw trip. Đã **note vào AA-653** (comment) + yêu cầu khi trả lời phải lập **bảng thống kê per-country** (số nước, tour/nước, thứ tự chạy, kết quả tách raw→Master→review→atomized); Bhutan 3 tour là ĐÚNG (pilot ban đầu, đổi kế hoạch nên chưa chạy hết, sẽ chạy sau theo thứ tự với 2 NCC). **Làm sau** — soạn nháp duyệt trước khi đăng.
- **AA-718 set Done** trên Linear + comment bằng chứng (3 PR + verify live).

## Còn lại (việc chưa xong — THỨ TỰ CHO PHIÊN SAU)
**Làm ADMIN pages trước, TENANT sau** (Nghiệp chốt S211). Mỗi issue = 1 PR, thiết kế theo kit + chuẩn thống nhất (KHÔNG có design note đính kèm — tự thiết kế).
1. **AA-664** (admin) — Overview dashboard: toàn hệ (pipeline A0→A3, intelligence, tenants, jobs, cost vs budget, alerts).
2. **AA-705** (admin) — SEO Intelligence: demand by market, keyword table, PAA coverage, gaps, spend.
3. **AA-667** (admin) — S1 Rewrite: live streaming khi viết (reuse LiveWriter/ADR 0004) + job-based progress.
4. **AA-666** (admin, High) — Tenant 360: trang chi tiết 1 tenant (profile/brand/content/channels/usage/billing/quality/audit/settings). Route `/admin/tenants/[id]`. Nhiều mảng cần endpoint — cân nhắc khung kit + dữ liệu đã có endpoint trước, placeholder phần thiếu.
5. **AA-668** (portal, High) — Writer panel: segment/topic → right-panel Goal→Angle→auto-write live streaming (social + tour rewrite), CTA từ brand defaults.
6. **AA-671** (portal) — Marketplace redesign: catalog grid + filters + detail drawer + add-to-catalog state.
7. **AA-672** (portal) — Account pages: Billing, Activity log, Team & Settings, Integrations.
8. **AA-670** (portal) — IA + page-by-page UI audit: fix trạng thái không nhất quán (vd finished tour vẫn "Writing…").

Ngoài UI: **AA-653** rerun — Bhutan trước (lấy `Bhutan (Newtemplate)`, 2 NCC >30 tour), pilot 3 tour, báo cáo PR-15 bằng bảng thống kê (nháp duyệt trước). **Có thể chạy rerun SONG SONG với build UI** (hai việc độc lập; chỉ tránh merge PR backend-pipeline giữa một wave đang chạy; UI PR thuần FE vô hại).

## Lưu ý kỹ thuật cho phiên sau
- **BÀI HỌC decorator (FastAPI):** KHÔNG chèn helper function GIỮA `@router.get(...)` và `async def <route>` — decorator sẽ bind vào helper, route biến mất, endpoint 422. Đặt helper TRƯỚC cả comment+decorator. (Gây 422 Dev, hotfix #559.)
- **Next 16 / React Compiler (frontend/AGENTS.md):** lint ERROR `react-hooks/set-state-in-effect`. KHÔNG setState trong useEffect. Dùng: lazy initial state (đọc URL/cookie), key-remount để reset state theo prop, useMemo cho derived, react-query thay fetch-in-effect, `refetchInterval` dạng function đọc `query.state.data` để tự dừng poll. Hydration: lazy-init đọc cookie có thể mismatch SSR → giữ pattern cũ + scoped eslint-disable khi cần (vd AdminSidebar).
- **Kit vs legacy primitive:** kit `EmptyState` dùng prop `description` (KHÁC portal `sub`), `Badge` dùng `tone` (KHÁC admin `color` / portal `variant`). next build (tsc) bắt lỗi prop; eslint/tsc-noEmit có thể miss → luôn chạy full `npm run build`.
- **`_kit` là private folder** (underscore, Next 16 không routable) — library ở đó OK; trang hiển thị phải ở folder non-underscore (hoặc tab trong trang có sẵn như Settings).
- **deploy-dev.yml:** api + worker CHUNG 1 image; mỗi deploy đăng ký task-def revision mới cho CẢ HAI (image ghim theo sha, không theo tag động) → đổi code api vẫn phải roll worker (chạy chung `shared/`). ECS_SERVICE=`aa-cis-dev-api`; worker service=`aa-cis-dev-worker`.
- **ECS exec điều tra/backfill:** runner `.tmp-session/s211_run.sh` (STS env session; `--region us-west-1` không cần `--profile` khi session còn; script đọc `DATABASE_URL` trong container; chạy nền + poll S3 `scripts/out/`). STS 8h hết → `eval "$(aws configure export-credentials --profile aa365-admin --format env)"` + MFA (chỉ Nghiệp). Cả `aws ecs ...` lẫn profile đều hỏi MFA khi session hết.
- **render Dev headless:** `.env.development.local` (gitignored) trỏ API_URL=`http://127.0.0.1:9` → middleware fail-open-in-dev cho trang trong allow-list; set cookie `cis_role`+token giả; playwright `--no-save`. Dọn env+playwright sau. Trang cần backend data sẽ hiện error/empty (render-bot không auth thật) — đủ để xác nhận mount sạch, KHÔNG đủ xem data thật (cần admin login Vercel).
- Log local: file này. ECS: api :447 / worker :2.
