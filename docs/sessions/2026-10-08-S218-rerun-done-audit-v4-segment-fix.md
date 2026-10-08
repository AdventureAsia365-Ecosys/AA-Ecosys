# S218 — Hoàn tất rerun 14 nước + audit A-series v4 + sửa lỗi segment âm thầm (08/10/2026)

**Tác nhân:** Claude Code (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:477` / `worker:32` (cùng SHA `4a1d472`, COMPLETED) · **Migration mới:** 205 (index phủ `decision_log`, đã apply) · **Branch cuối:** 3 repo con về `main` sạch; repo gốc qua PR · **Job queue:** sạch (`safe_to_deploy:true`).

## Trạng thái
Phiên rất dài. Thứ tự Nghiệp chốt: Group 1 quick fixes → India đợt 2–5 → các nước còn lại → cập nhật audit → Group 2. Đã xong tới bước "cập nhật audit" (bản v4). Trong lúc làm audit v4 phát hiện thêm 3 lỗi thật, đều đã sửa và verify live. Group 2 (A3) chuyển sang phiên sau, đã có issue đầy đủ.

## Quyết định của Nghiệp (chỉ điều Nghiệp nói)
- Thứ tự: AA-738 → AA-737 → Sri Lanka → Nepal review → AA-739; rồi Group 1 → India 2–5 → các nước còn lại → audit → Group 2 A3 → Group 3.
- Tạo cơ chế lesson log (`skill/aa-lessons`), merge root PR #31; zip skill cho Claude Chat (Nghiệp đã upload).
- Lưu báo cáo audit, cập nhật sau khi chạy hết các nước; áp cùng phương pháp cho T-series (AA-741).
- Cưỡi voi: chị Thư chốt qua Zalo — giữ nguyên tour, cho người duyệt.
- Làm AA-739 trước rồi chạy tiếp; tự tạo tài khoản test admin mới (`e2e-claude-code`, mật khẩu chỉ ở Secrets Manager) và giữ dùng cho các lần sau.
- Japan: 3 cặp trùng đã có hướng → đưa vào chạy; bản lặp không nhà cung cấp → **trash** để tiện thống kê.
- Chạy các nước còn lại nếu cần để hoàn tất rerun.
- Tạo issue AA-742 (decision_log), đồng ý đưa vào Group 2.
- Tối ưu gom segment: **làm bước 1 ngay** (scope theo nước, không so segment cũ với nhau); bước 2–3 ghi issue (AA-743).
- Audit phải có đối soát số liệu S0 → S1 → Master → A3 (trạng thái đúng, số khớp mọi bảng).
- Đăng PR-15 bảng kết quả cuối; dừng phiên.

## Kết quả chính
**Code (AA-CIS-App, tất cả merged + deployed + verify live):**
- #583–#590: AA-738 (strip từ cấm tất định, prompt), AA-737 (8 slot worker), AA-740 (fit độ dài meta/title), #589 (quick fixes audit: atom strip, status judge-path, revalidate_passed, HARD_CODE_REPAIR), AA-739 (Review Queue + Master Content phân trang/filter server).
- **#591** — trang Jev Decisions 504: đọc song song + migration 205 (index phủ). Truy vấn chính 16,1 → 0,77 s (cần `count(l.created_at)` thay `count(l.id)` mới index-only). Verify: days 7/30/90 → 200; UI desktop/mobile.
- **#592/#594/#595** — **lỗi segment âm thầm** (AA-695): từ 30/09 (#510) re-point member bằng UPDATE đụng PK → transaction hủy, warning bị nuốt; lần gộp hỏng lặp lại mọi tour → từ 05/10 không segment mới; 566 tour không segment/ranking/route. Lỗi thứ 2 (FK: target mới chưa tạo) lộ ra khi chạy bù. Perf: chỉ nạp segment cùng nước + chỉ so atom mới với segment cũ → 36 s → 0,5 s/tour.
- **#593** — trạng thái S1: reject bản cũ không ghi đè tour đã có Master; badge Rejected/Failed/In review; filter "In review". Sửa data 2 tour (Taiwan "Ancient Trails & Hot Springs", Korea "Uncover Korea") `hitl_rejected` → `published`.

**Rerun:** India 203/236, Philippines 43/46, Pakistan 18/18, Japan 78/79 (2 đợt), Vietnam 1/1 (tour sót trong file LAOS). Tổng 14 nước: **917 active / 866 Master / 51 chờ duyệt** (23 cưỡi voi, ~18 judge thấp, 9 grounding, 1 độ dài). 0/866 Master có từ cấm.

**Chạy bù segment:** 633 tour (3 lượt, lượt cuối 239 tour 0 lỗi) + recompute toàn nền tảng 813 s → **866/866 Master có segment + ranking**, 713 có route (trước: 300 / 174). Segment 3.871 → 14.340.

**Audit v4** (artifact `BuaUQnyYeNYn9LSBxxyY1m` version 4 + `docs/audits/2026-10-08-S218-a-series-pipeline-audit.html`): đối soát S0→A3 (46 file → 987 raw → 917 active → 866 Master + 51 review, mọi kiểm tra chéo = 0), 3 lỗi mới, đính chính v3 (tour 8+ ngày có route 99,5% — "60% thiếu route" là do lỗi segment), segment phân mảnh 79%, chi phí $98,6 ≈ $0,114/Master.

**Jira PR-15:** comment 10464 — bảng 14 nước (raw / active / đã viết / Master / atom / segment / route / hub), tag @thule.

**Linear:** Done: AA-738, AA-737, AA-739, AA-740 (verified live). Comment: AA-660 (504 fix verified), AA-695 (regression + backfill verified), AA-728, AA-743. Issue mới: **AA-741** (T-series audit), **AA-742** (decision_log ghi dòng cho mỗi lần đọc cache, Todo), **AA-743** (recompute theo phạm vi + gộp 1 lần/wave), **AA-744** (sửa 927 atom từ cấm + 32 seo_meta cũ), **AA-745** (xử lý 51 tour chờ duyệt), **AA-746** (batch treo ingesting), **AA-747** (bớt lời gọi LLM/tour), **AA-748** (writer nhận dữ kiện có cấu trúc), **AA-749** (distinctiveness luôn MED).

**Repo gốc:** `skill/aa-lessons` (PR #31), `docs/audits` + scripts (PR #32), lessons mới, Zalo style chị Thư (`stakeholders-english.md`), `aa-ui-verify` (chỗ lấy login test), `db-schema-reference.md` regenerate (migration 205).

## Bằng chứng verify
- ECS api :477 / worker :32 cùng SHA 4a1d472, COMPLETED; deploy-gate `active:0`.
- `/admin/decisions/summary` days=7/30/90 → 200 (5–6,6 s); Playwright `/admin/decisions` 0 console error.
- `/admin/tours` → 917 tour, in_review 51, 2 tour Taiwan/Korea = published; Playwright S1 filter "In review" hiện badge đúng, "Ready" = 0.
- `s218_recon.py` sau chạy bù: mọi check = 0 trừ `pipeline_runs_stuck` 10 (AA-746).
- CI integration test `test_s218_segment_alias_repoint.py` PASS (tái hiện đúng lỗi PK); unit 2450 passed.

## Còn lại (chuyển phiên sau — đề xuất S219)
1. **AA-745** — 51 tour chờ duyệt theo nguyên nhân (23 cưỡi voi cần Nghiệp/chị Thư duyệt tay).
2. **AA-744** — sửa tất định 927 atom + 32 seo_meta (DRY RUN → duyệt).
3. **AA-742 + AA-743** — log cache Jev + recompute theo phạm vi/gộp wave (trước khi chạy wave lớn tiếp).
4. **AA-695** — gộp segment (79% 1 atom), sau AA-743.
5. **AA-741** — audit T-series khi A3 ổn.
6. Đóng **AA-653** (runbook clean-rerun; đã chạy hết 14 nước) — Nghiệp xác nhận.

## Lưu ý kỹ thuật / BÀI HỌC (đã ghi `skill/aa-lessons/lessons.md`)
- Bước "best-effort" nuốt lỗi phải để dấu vết trong kết quả job; báo cáo wave đếm sản phẩm đầu ra (segment/ranking/route theo tour), không chỉ trạng thái job.
- UPDATE đổi khoá con trên PK ghép → dùng INSERT … ON CONFLICT DO NOTHING + DELETE.
- Index phủ chỉ có tác dụng khi truy vấn không chạm cột ngoài index (kể cả `count(id)`); EXPLAIN lại, phải thấy `Index Only Scan` + `Heap Fetches: 0`.
- Script dài chạy trong api task bị deploy giết → chạy bằng `setsid nohup` (xem `docs/audits/scripts-s218/run_detached.sh`) và viết idempotent (tự chạy tiếp tour còn thiếu); lâu dài nên là job kind (AA-743 comment).
- Atlassian: connector `claude_ai_Atlassian` (v1) trả 403 "app not installed"; dùng `claude_ai_Atlassian_MCP` (`addOrEditJiraIssueComment`, `contentFormat: html`).
- Tài khoản UI test: `e2e-claude-code`, secret `aa-cis/dev/e2e-test-admin` (không in mật khẩu).
