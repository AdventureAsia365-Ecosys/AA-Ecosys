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

## Lưu ý kỹ thuật

- ECS exec: dùng `python3 -u` + `timeout` (`.tmp-session/ecsrun.sh`). Không có `-u` thì output bị
  buffer, session treo không in gì.
- Output ECS exec bị cắt khoảng 1k ký tự → chia nhỏ query.
- asyncpg `dict(record)` gộp các cột trùng tên (`count`) → phải đặt alias.
- Git Bash không ghi được file qua UNC `//wsl.localhost` → dùng công cụ Write rồi chạy qua
  `wsl -d Ubuntu -- bash <file>`.
- Token SSO profile AAA (`aa-sso`) chưa có → cần `aws sso login`.
