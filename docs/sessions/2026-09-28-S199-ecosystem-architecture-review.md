# S199: Review kiến trúc toàn hệ sinh thái, model trên acc3, nguyên nhân DFS hết tiền

- **Ngày:** 28/09/2026
- **Tác nhân:** Claude Code (VSCode/WSL)
- **Người duyệt:** Nghiệp
- **Đầu vào:** nội dung họp với chị Thư 28/09 (CIS-App, TripPlanner, AA-Booking, tích hợp hệ sinh thái),
  kiểm model GPT-6 Astra / GPT-5.6 Luna / Sonnet 5 / Opus 5.5 trên acc3.

## Trạng thái

Phiên audit + tư vấn kiến trúc. **Không đổi code app, không đổi hạ tầng.** Chỉ chạy query đọc qua
ECS exec, và lệnh AWS chỉ đọc (list/get, không gọi model).

- Repo gốc: nhánh `docs/s199-ecosystem-architecture-review`, gồm:
  - `docs/architecture/ecosystem-review-2026-09.md` (tiếng Anh, bản review đầy đủ);
  - `docs/adr/0001-ecosystem-target-architecture.md` (ADR cấp hệ sinh thái đầu tiên, trạng thái Proposed);
  - log này;
  - `.gitignore` thêm `secret_manager/` (Nghiệp sửa local, chưa commit — đưa vào PR này).
- Linear: comment cập nhật state cho AA-642/643/644/645, AA-624/621, AA-634. **Chưa tạo issue mới:**
  danh sách đề xuất chờ Nghiệp duyệt (xem mục Còn lại).

## Phát hiện chính (bằng chứng)

1. **DFS hết tiền là do bug, không phải cron.**
   - `_run_research_only()` (`api/routers/v1_tours.py`) chạy sau MỖI lần tenant rewrite T2.
   - `run_segment_research()` đọc `SELECT … FROM acp_contract.atom_segment` KHÔNG lọc gì. Từ AA-545
     segment thành platform-wide, nên query này quét toàn bộ 2.222 địa điểm × các market của tenant
     (AU/US/UK).
   - Ngày 25/09: 1.169 lệnh gọi DFS thật, **$49.02**, chia 2 đợt 05h và 08h UTC (12h và 15h giờ VN),
     trùng lúc test rewrite WanderLux ở S196:
     - `search_volume_bulk` $39.24;
     - `keywords_for_keywords` $9.00;
     - thêm khoảng 7.9k lệnh gọi Haiku `a3_search_demand`.
   - Không có budget guard. Lambda hằng ngày chỉ đọc số dư.
2. **Model mới chỉ dùng được ở acc3** (kiểm bằng `get-foundation-model-availability`, không gọi model):
   - GPT-6 Astra, GPT-5.6 Luna, Sonnet 5, Opus 5.5: acc3 ✅; acc1 và acc2 chưa chấp nhận agreement.
   - GPT-6 Luna (S198 định dùng) chưa chấp nhận agreement ở cả acc3 → đổi mục tiêu sang **GPT-5.6 Luna / GPT-6 Astra** trên Bedrock.
   - Chặn thêm:
     - IAM `AA3-Bedrock-Invoker` chỉ cho Sonnet 4.6 + Haiku 4.5;
     - LLMClient chỉ gửi body Anthropic, chưa có Converse API cho model OpenAI trên Bedrock;
     - fallback sang acc1 sẽ lỗi với mọi model mới.
3. **Việc chạy nền dùng `asyncio.create_task` trong container API** (T2, T9, research, atomize):
   - không có hàng đợi bền, không retry, không reaper;
   - deploy giữa chừng làm chết job (`stopTimeout` 90s < tour dài 105–207s).
   - Giả thuyết cho bug "tour viết xong vẫn hiện Writing" của chị Thư: dòng `tenant_tour_versions`
     kẹt `pending`/`ai_generated`. DB hiện không còn dòng kẹt vì WanderLux đã được dọn → cần tái hiện.
4. **Số liệu DB Dev:**
   - raw 793; generated_content 185; published 121 (11 nước); atoms 9.208;
   - segments 3.463 (2.222 địa điểm); route 325; search_demand 19.785; 4 tenant.
5. **UI:**
   - Admin có 2 mục Dashboard trùng nhau.
   - Route cũ `(internal)/{catalog,upload,brand,review}` trùng với `/admin/*`.
   - Brand Identity tách khỏi Settings.
   - Platform Stats và Tenant Activity chồng chéo nhau.
   - Tag "ADMIN" không còn ý nghĩa.
   - Role `content` không có JWT (AA-253).
   - Trang tenant chỉ có 6 tab mỏng.
   - Portal: các trang Account nằm chung trong `PlaceholderTabs.tsx`; My Content là danh sách; wizard
     viết mở inline dưới Slate; T9 trả 422 để hỏi CTA.
6. **TripPlanner:**
   - Gợi ý = 0.6 taste + 0.4 khoảng cách, không ràng buộc theo tour thật → khách tạo được trip mà
     không tour nào đáp ứng.
   - Đã có sẵn `itinerary_components.source_tour_id/source_day_index` để dựng Tour Graph.
7. **AAA:**
   - PRD/ERD Quanskill còn các gap P0 (media, supplier_bookings, multi-country, audit…).
   - AAA ở ap-southeast-1, account riêng → không bàn giao qua DB chung được.
   - Chưa kiểm được account AAA (thiếu token SSO `aa-sso`).
8. **Tài liệu:**
   - README của App và Infra chỉ có 1 dòng.
   - Docs gốc viết tiếng Việt (vi phạm quy ước).
   - `apps/AA-CIS-App/.claude/CLAUDE.md` LIVE STATE dừng ở 25/08.

## Thay đổi Codebase

Chỉ tài liệu ở repo gốc (xem Trạng thái). Không đổi code App, TripPlanner hay Infra.

## Thay đổi Hạ tầng

Không có.

## Bằng chứng verify

- `aws bedrock list-foundation-models` / `list-inference-profiles` / `get-foundation-model-availability`
  trên acc3 (`nghiep_aa365`), acc1 (`pqnghiep-admin`), acc2 (`aa365-admin`).
- 3 script đọc DB qua ECS exec (`.tmp-session/s199_audit*.py`, đã xoá khỏi S3 sau khi chạy).
- Đọc code: `segment_research.py:517+`, `v1_tours.py:39-58, 730-760`, `client.py`,
  `acc3-bedrock/main.tf:54-110`, `suggestions.py`, `AdminSidebar.tsx`, `Sidebar.tsx`, `middleware.ts`.

## Còn lại

1. **Nghiệp chạy smoke test Jev** (auto mode chặn agent gửi key ra API ngoài): `bash .tmp-session/jev_run.sh`.
2. **Nghiệp chốt các quyết định** ở §10 của bản review:
   - judge chọn Luna hay Astra;
   - fallback trong acc3 hay chấp nhận agreement ở acc1;
   - Postgres queue hay SQS;
   - TripPlanner: 1 tour hay tổ hợp tour;
   - stack AAA;
   - ngưỡng Jev;
   - nhà cung cấp billing.
3. **Duyệt tạo issue Linear** theo 7 phase P0–P6 (3 project mới + khoảng 25 issue — danh sách ở phần
   trả lời trong chat).
4. `aws sso login --profile aa-dev-admin` để audit các account AAA.
5. Merge PR docs của repo gốc (Nghiệp merge tay).

## Phần 2 — Quyết định của Nghiệp, Jev chạy thật, DFS điều tra sâu, tạo issue

**Quyết định (28/09):**
- Judge = **GPT-5.6 Luna**; lớp model tách riêng, điều hướng theo stage (AA-642).
- acc3 là account chính cho model mới.
- TripPlanner **cho ghép nhiều tour** để ra Trip Case hoàn chỉnh.
- AA-Booking **code từ đầu**, dùng hạ tầng acc2 hiện tại (cùng RDS, schema `booking`). Account/profile AAA cũ đã đóng.

**Jev chạy thật** (Nghiệp duyệt, model `jev-1.13.0`, ~270 ms/lần gọi):
- F9 bài tốt: brand_fit 0.79, generic_ai 0.09. Bài xấu: 0.04 / 0.97.
- Phân loại atom → trek 1.00; TripPlanner → trekking 0.84 / strenuous 0.91.

**DFS điều tra sâu** (trả lời chị Thư: "batch có chạy đàng hoàng không?"):
1. **Batch gần như không có tác dụng.**
   - 678 task volume, trung bình 4,5 keyword/task (tối đa 13).
   - Giá DFS tính theo task (~$0.057–0.059/task, không đổi theo số keyword; 1 task nhận tới 1.000 keyword).
   - Nguyên nhân: `CONCURRENCY=4` + linger 5s, trong khi repo chị Thư chạy 16 worker dạng batch riêng.
2. **Cache bị hỏng.**
   - DFS hết tiền khoảng 09h UTC. Giờ 09–10 ghi **14.691 dòng `search_volume` NULL** (0 dòng có volume), và 1.795 địa điểm bị đánh dấu "đã research" trong 182 ngày.
   - Tổng cộng 18.214/19.305 dòng của ngày 25/09 là NULL.
   - Nguyên nhân: `fetch_volumes_bulk()` nuốt lỗi.
3. `keywords_for_keywords` mỗi địa điểm tốn 1 task ($0.09). Nếu chạy cho khoảng 1.800 địa điểm không có volume thì có thể vượt $150/lượt.
4. Đề xuất:
   - chuyển research sang job admin;
   - chia 2 pha để gom bulk thật;
   - dùng chế độ Standard (queue) của DFS vì việc không gấp;
   - thêm budget guard;
   - sửa dữ liệu 25/09.

**Linear:** tạo 3 project mới:
- P-AA-12 Ecosystem Foundation;
- P-AA-13 CIS UI v2;
- P-AA-14 AA-Booking Foundation.

Thêm **38 issue AA-646 → AA-683**, có gắn quan hệ blocked-by. AA-644 đổi tiêu đề sang GPT-5.6 Luna (kèm comment đính chính agreement acc3). Bản đồ issue ở §10.3 của bản review.

**Jira:** chị Thư muốn nhận báo cáo trên Jira. Connector Atlassian chưa được authorize trong phiên này → Nghiệp dán tay bản báo cáo (tiếng Việt) em soạn trong chat.

## Phần 3 — Code P0 DFS: AA-646 / 647 / 648 / 649 (đều Done, verify live)

| Issue | PR App | Nội dung | Verify live (Dev) |
|---|---|---|---|
| AA-646 | #451 | Tenant rewrite không còn tự mua DFS. Research chỉ admin chạy: `/admin/segment-research/{preview,run,status}`, bắt buộc chọn market + phạm vi, tối đa 200 địa điểm/lượt | taskdef :349; preview 200; 0 lệnh gọi DFS sau deploy |
| AA-647 | #451 | `DFSCallError` (401/402/403, status 401xx/402xx là lỗi nghiêm trọng), không ghi cache khi DFS lỗi, circuit breaker dừng cả lượt | **Repair data 25/09** (Nghiệp duyệt): xoá 16.311 dòng NULL `search_demand` + 5.859 dòng `research_log` (1.953 địa điểm), reset cache 2.870 segment. Bhutan cần research 0 → 141 |
| AA-649 | #452 (+ #454 mở) | **Migration 168** `shared.spend_budget` (DFS $10/ngày; research $5 DFS + $2 Bedrock mỗi lượt), `shared/cost_guard.py`, `/admin/budgets`, kiểm số dư trước khi chạy, cảnh báo admin | taskdef :350; migration 168 đã apply; **test trần $0.20: dừng sau $0.18, 0 địa điểm bị đánh dấu, có cảnh báo** |
| AA-648 | #453 | Research theo lô (5 pha): 15 địa điểm/lần gọi Haiku, ≤1.000 từ khoá/task volume, SERP chỉ cho từ khoá có volume, 20 seed/task gợi ý. `strategy=batch` mặc định | taskdef :351; **pilot Bhutan 50 địa điểm: $0.55 DFS (ước tính ≤ $0.80) + $0.015 Haiku; 3 task × 152 từ khoá** (trước đây 4,5); ~$0.011/địa điểm, rẻ hơn khoảng 10 lần |

**Kết luận điều tra:** DFS bị kích hoạt từ **tenant portal**, không phải admin.
- WanderLux rewrite xong lúc 05:04:21, và 35 giây sau có lần gọi research đầu tiên.
- Chỉ có 3 market (US/UK/AU) vì research lấy market của tenant đã kích hoạt.
- Luồng A3 của admin không mua DFS.

**Chi phí test trong ngày:** DFS $0.73, Haiku khoảng $0.03. Số dư DFS còn khoảng $49.1.

**Khác trong phần 3:**
- AA-665 nhận thêm yêu cầu UI của Nghiệp: lịch sử research runs, filter/sort cho các bảng, Search demand explorer (keyword / PAA / SERP), hiện tên tenant thay vì UUID.
- AA-650 ghi chú: `segment_research` là loại job đầu tiên phải chuyển sang job runner.
- PR #454 (sửa nhỏ AA-649): nâng ước tính giá task volume lên $0.09 và thêm log cho task gợi ý từ khoá. CI xanh, **chờ merge**.
- Jira KAN-90: connector Atlassian chưa authorize nên chưa đọc được.

## Lưu ý kỹ thuật (bổ sung phần 3)
- **Merge kiểu squash làm hỏng PR xếp chồng.** #453 bị conflict sau khi #452 được squash. Cách xử lý: `git rebase --onto origin/main <nhánh cũ>` rồi `push --force-with-lease`.
- `gh pr edit --base` lỗi vì GitHub đã bỏ Projects classic → dùng `gh api -X PATCH repos/.../pulls/N -f base=main`.
- Script chạy trong container dùng `ADMIN_SECRET` từ biến môi trường (không in ra) để gọi endpoint admin qua `localhost:8000`.
- asyncpg: tham số kiểu `date` phải truyền `datetime.date`, không nhận chuỗi.
- Auto mode trên extension VSCode (Windows/UNC) đôi khi không trả kết quả kiểm quyền, và chặn `gh pr merge` / gửi key ra ngoài. Nên mở VSCode trong WSL và dùng chế độ quyền hỏi-duyệt.

## Lưu ý kỹ thuật

- ECS exec: dùng `python3 -u` + `timeout` (`.tmp-session/ecsrun.sh`). Không có `-u` thì output bị
  buffer, session treo không in gì.
- Output ECS exec bị cắt khoảng 1k ký tự → chia nhỏ query.
- asyncpg `dict(record)` gộp các cột trùng tên (`count`) → phải đặt alias.
- Git Bash không ghi được file qua UNC `//wsl.localhost` → dùng công cụ Write rồi chạy qua
  `wsl -d Ubuntu -- bash <file>`.
- Token SSO profile AAA (`aa-sso`) chưa có → cần `aws sso login`.
