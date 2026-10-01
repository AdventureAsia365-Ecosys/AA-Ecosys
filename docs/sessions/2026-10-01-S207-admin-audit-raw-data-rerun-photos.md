# S207 — Audit UI admin, dữ liệu thô từ Jira CON, chạy lại Korea/Taiwan, ảnh AA (AA-708), ADR 0002 (01/10/2026)

**Tác nhân:** Claude Code (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:426` COMPLETED (PR #540) · **Migration mới nhất:** CIS 202

## Trạng thái
- **Dữ liệu thô sạch, chạy lại đã bắt đầu.** Reset dữ liệu dẫn xuất (giữ raw_tours), upload các tour còn thiếu từ
  Jira CON, dọn trùng. 919 tour active.
- **Đợt chạy lại:** pilot Bhutan 3 → **Korea 30/30 (27 publish, 3 HITL thật)** → **Taiwan 36/36: 32 approved + 1 qua Regenerate (Eastern Trails v2 8.0) + Ancient Trails giữ bản trial → 34 trên Master; 2 HITL (Hehuanshan, Snow Mountain), 1 rejected (Ancient Trails bản viết lại 6.0, Master vẫn giữ bản 8.0 publish từ trial)**. Master Content = **64 tour** (Bhutan 3, Korea 27, Taiwan 34), 64/64 đã atom hoá.
  Thứ tự tiếp (chị Thư, PR-15): Mongolia, China, Thailand, Bhutan, Laos, Nepal, Sri Lanka, India; Japan chờ chị Thư + Trang;
  Pakistan/Philippines hỏi chị Thư xếp sau India.
- **Ảnh (AA-708):** sync Drive → S3 chạy thật; trang Admin › Photos 4 tab. **Sync xong: 3.232 ảnh / 7 nước (Bhutan 753, China 1.156, Mongolia 230, Philippines 113, South Korea 360, Sri Lanka 54, Taiwan 566), 0 lỗi; 2.658 ảnh khớp tour, 162 tour có ảnh, 574 ảnh chưa khớp; 234 gán tay (12 thư mục Korea).** S3 `photos/`: gốc 3,18 GB + WebP 1600 0,94 GB + WebP 600 0,21 GB = **4,33 GB** (~$0,10/tháng S3 Standard).
- **ADR 0002 (root): chỉ CIS ghi nội dung**; role DB `tripplanner` đã bị thu quyền ghi `shared.destinations`.
- Issue: AA-653 In Progress (các đợt chạy lại + review queue #540); AA-708 In Progress; AA-711 Done (deploy + worker ghi revision);
  AA-712 Backlog (chuyển pipeline địa danh sang CIS — cần trước khi bật cover ảnh địa danh). **Mới:** project Linear `CIS Pipeline Rerun — Phase 2` (project cũ đủ 50 issue); **AA-713** (High) atom đi theo trạng thái Master; **AA-714** judge sang GPT Luna (Jira PR-16).

## Thay đổi Codebase
**AA-CIS-App** (#520–#540):
| PR | Nội dung |
|---|---|
| #520 | **AA-702** sửa audit UI admin: notifications 500, chi phí tenant, cây LLM ops gộp aa_internal, metrics, s1-rewrite model, atom score |
| #521 | Migration 195: `v_trip_registry` chỉ nguồn active; S1 ý tưởng keyword có volume thật |
| #522 | Lọc liên quan keyword (bỏ seed "{country} tours"), activity seed dùng thật |
| #523 | Runbook `docs/runbooks/clean-rerun.md` + script reset |
| #524 | **S1 prefetch DFS**: gom seed theo nước (≤20/task), dùng research cache, giữ `seo_context` 180 ngày |
| #525 | conftest: env giả như CI → test local khớp CI |
| #526 | **AA-706** Jev cho keyword S1 (shadow, mig 196); **AA-707** T2 dùng keyword theo market tenant; forbidden word nguyên từ |
| #527 | Parser ngày (ký hiệu, số chữ, khoảng ngày), loại keyword lưu trú, Jev xem mọi ứng viên, seed đơn dùng lại |
| #528 | Mig 197: thêm Pakistan, Philippines vào CHECK nước |
| #529 | Seed: tên có gạch nối / viết hoa toàn bộ / lặp tên nước |
| #530 | **AA-708** job `photo_sync`, bảng `shared.place_photo` (mig 198), trang Photos, `/content/photos/{id}` |
| #531 | Keyword: khớp nguyên từ, bỏ tên nước khác, bỏ điểm xuất phát "from X", bỏ airport transfer |
| #532 | Ảnh: thư mục chứa ảnh = tour, bỏ đuôi số ngày / mã, so tên thô + aa_name, gán cả thư mục |
| #533 | **AA-711** worker của task cũ đang drain ngừng nhận job khi có revision mới (mig 199) |
| #534 | Ảnh: match địa danh chỉ trong lịch trình của tour; view `v_tour_photos` / `v_destination_photos` (mig 200); **mig 201 thu quyền ghi `shared.destinations` của role tripplanner** |
| #535 | Drive key qua header (không lộ trong lỗi/log), giãn tốc độ, thử lại, dừng khi lỗi liên tiếp |
| #536 | **Judge + brand audit thấy mọi ngày lịch trình** (trước: 600 / 300 ký tự đầu) |
| #537 | Bỏ keyword nêu địa danh nước khác (`foreign_places`); tải ảnh qua `thumbnailLink` |
| #538 | Trang Photos 4 tab (Overview / Tours / Folders / Gallery); giữ ảnh gốc `=s0` + S3 (mig 202), WebP q85 |
| #539 | **Sự cố OOM:** decode JPEG lớn ở scale nhỏ (`im.draft`) — ảnh 8256×5504 peak RSS 594 MB → 54 MB |
| #540 | **Review queue:** publish → dismiss mọi bản pending của tour; bản lỗi của tour đã publish vào `dismissed`; bản lỗi mới `superseded` bản cũ (mỗi tour 1 dòng); nút Regenerate chính; bỏ supersede phía FE (tìm review row approved — không bao giờ tồn tại) |

**AA-TripPlanner-Web:** PR #64 (docs CONTEXT: hợp đồng đọc ảnh, ADR 0002, extraction đóng băng) — **chờ Nghiệp merge**.
**Root:** ADR 0002 `docs/adr/0002-only-cis-writes-content.md`; `ecosystem-architecture.md` §4.0 (quy tắc ghi) + §4.5 (ảnh);
steering: luôn tag chị Thư trên Jira, số phiên S207.

## Thay đổi Hạ tầng / dữ liệu (Dev)
- Migration 195–202 apply tay trước merge (202, 199 bắt buộc trước deploy).
- **Reset** dữ liệu dẫn xuất theo runbook (66.831 dòng; raw_tours 793 + search_demand + log giữ nguyên; có snapshot RDS).
- **Dữ liệu thô từ Jira CON** (`apps/AA-CIS-App/data/jira_con_raw_2026-10-01/`, gitignored, có xlsx đầy đủ):
  upload Sri Lanka 106, Philippines 46, Pakistan 18, Nepal 16 (Tibet + Cross Country), Bhutan 4 (Blue Poppy), China 3.
  Trash 4 tour giáo dục Laos (studentvillage), 6 dòng test Blue Poppy đổi tên "[test file]", 5 staging trùng bypass,
  BUTANDING TAP-10 trash, Cycle Beijing bản cũ superseded, sửa 84 tên xuống dòng (Philippines mã TAP-xx → `tour_id_external`).
- **Secret mới** `aa-cis/dev/gdrive-photo-reader` (Google API key, Drive API, project AdventureAsia). **Key từng lộ trong
  lỗi/log (URL `?key=`) trước #535 → nên tạo key mới thay thế.**
- Role DB `tripplanner`: REVOKE INSERT/UPDATE/DELETE trên `shared.destinations`; GRANT SELECT 2 view ảnh.
- Chi phí ngày 01/10 (dfs_call_log / llm_call_log): **DFS $2,34; LLM $7,21** (gồm S1, judge, Jev, atomize, segment). LLM S1 ≈ $0.08/tour.
- **Sự cố 10:12 UTC:** photo_sync OOM-kill task API (1 GB, exit 137) → job d6dbba18 huỷ, keyword prefetch tự chạy lại OK; sửa #539.
- Dev data: review queue — dismiss 11 dòng của tour đã publish, supersede 3 bản cũ Korea → còn 5 dòng pending (mỗi tour 1).

## Bằng chứng verify
- Korea: sau #536, 12 tour HITL chạy lại → 27/30 approved (judge thấy đủ ngày). 3 HITL còn lại là vấn đề nội dung nguồn.
- Keyword: các ca sai thật ("village life bhutan", "seoul airport transfer", "paro hot stone bath"…) có test hồi quy;
  kiểm trong container trước khi kết luận.
- AA-711: worker mới ghi `task_revision`=419; nguyên nhân gốc chứng minh bằng `job_worker` (job 06:04 chạy trên worker :416 đang drain).
- Ảnh: `/content/photos/{id}` trả 200 image/webp; đo chất lượng: ảnh gốc tới 8256×5504 / 14 MB, `=s0` = byte-for-byte bản gốc.
- Unit suite 2.306 pass; flake8, eslint, `next build` sạch.

## Jira (đều tag chị Thư)
- PR-15: báo cáo dữ liệu thô + hỏi Bhutan 2 NCC (Druk Path 8N, Jomolhari/Yaksa 11N) + Pakistan/Philippines thứ tự.
- PR-14: bảng giá dịch vụ đăng nhập (đề xuất Cognito). KAN-20: benchmark Asian Trails (Leigh + Thư), để mở.
- PR-11: báo ảnh đã sync tự động từ Drive CON (3.232 ảnh, 7 nước, 162 tour) + hỏi: quyền dùng ảnh public/credit; thẻ LAOS chưa có link thư mục; thư mục "Seoul to Seorak" thuộc tour nào.
- **PR-16 (mới, chị Thư):** đổi "gpt-4.0-mini" sang GPT-5.6/6 Luna. Hệ thống không dùng gpt-4o-mini; judge mặc định gpt-4.1, `s1_judge` route DB đã sang gpt-5.6-luna nhưng còn lẫn gpt-4.1 (146/391 lời gọi 2 ngày). Temperature đã xử lý (AA-659). → AA-714, chưa comment Jira.

## Còn lại
- Các đợt tiếp: Mongolia → China → Thailand → Bhutan (chờ chị Thư về 2 NCC) → Laos → Nepal → Sri Lanka → India.
- AA-712: chuyển pipeline địa danh (trích xuất lịch trình, geocode, tour graph) sang CIS → rồi bật "Match places + covers".
- Ảnh: thư mục "South Korea: Seoul to Seorak, Seven Days" chưa có tour khớp (hỏi chị Thư); các nước khác gán tay thư mục còn lại.
- Thay Google API key (đã lộ trong log trước #535).
- Merge TripPlanner PR #64. Root PR (branch `docs/s207-jira-mention-rule`).
- Jev a1_seo (shadow) toàn grey — cần nhãn để hiệu chỉnh trước khi enforce.
- **AA-713** (High): atom của tour inactive/trashed vẫn được segment/ranking/slate dùng — đầu phiên sau.
- **AA-714**: judge sang GPT Luna + tìm đường gpt-4.1 còn sót; A/B gpt-6-luna.
- AA-651: viết lại S1 (`run-tour-async`) vẫn là task trong process API, không bền — deploy/OOM giữa chừng làm mất lần chạy.

## Jev ở đâu (kiểm llm_call_log 2 ngày)
- S1: `s1_grounding` (6.140 lời gọi — mỗi câu có căn cứ trong nguồn), `a1_seo` (1.595, shadow — keyword liên quan tour), `s1_judge_tiebreak` (3). Judge chính vẫn là GPT.
- Atom hoá/A3: `a3_atomize` 1.217, `a3_segment_type` 4.671, `a3_segment_match` 1.165, `a3_demand` 7.479, `a3_question_scope/landing`.
- Review queue: Jev không chạy trực tiếp; Re-validate sau khi sửa tay chạy lại các gate (có grounding Jev).

## Lưu ý kỹ thuật cho phiên sau
- **Sau mỗi deploy:** worker cũ giờ tự nhường (AA-711); vẫn không chạy đợt S1 lúc deploy vì run-tour-async còn chạy trong process.
- **Không `git add -f` cả thư mục** (đã 2 lần kéo `__pycache__` vào repo); add từng file.
- Chuỗi chờ deploy: đợi run Deploy Dev **mới** bắt đầu (so headSha) — tránh đọc nhầm run cũ.
- MFA aa365-admin hết hạn sau 8 giờ → lệnh AWS treo chờ mã; nhờ Nghiệp nhập mã (`echo <mã> | aws sts get-caller-identity --profile aa365-admin`).
- **Deploy khi có job:** đợi `shared.job` không còn queued/running rồi mới merge (`.tmp-session/s207_merge540.sh`).
- Script chạy đợt: `.tmp-session/s207_wave.mjs` (COUNTRY, OFFSET, LIMIT, CONC, PREFETCH, NAMES).
