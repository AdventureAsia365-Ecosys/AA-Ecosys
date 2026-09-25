# S196: brand pass, tenant portal, live writing progress, T2 pipeline efficiency, plan quota

- **Ngày:** 24–25/09/2026
- **Tác nhân:** Claude Code
- **Người duyệt:** Nghiệp

## Trạng thái

**Xong, đã verify live:**
- AA-635: tính chi phí LLM đúng.
- AA-310: ECS `stopTimeout` 90s.
- AA-605: đồng bộ brand adventure.asia cho admin và tenant portal.
- AA-636: sửa các điểm làm mất niềm tin trên portal.
- AA-637: hiển thị trực tiếp khi viết (steps + streaming text).
- AA-638: product polish cho portal.
- AA-639: pipeline T2 viết lại tour quá nhiều lần.
- AA-640: hạn mức gói lấy từ một nguồn, vượt hạn mức thì tính phí.

**Đã tạo, chưa làm:** AA-641 — flag_fix không được tạo lỗi cứng mới: fit seo_meta tất định + chặn từ cấm. Backlog, Nghiệp muốn xem kỹ trước.

**Nghiên cứu:** AA-634 (Jev/TypeSafe). Đã cài skill TypeSafe; API key chưa có vì bên đó đóng đăng ký.

## Thay đổi Codebase

**AA-CIS-App** — 18 PR, tất cả merged + CI xanh:

- **AA-635**
  - #431: giá Haiku 4.5, tính cache token, log call search-demand.
- **AA-605**
  - #432–#434: brand tokens chung trong `app/_brand/tokens.ts`, gồm Fahkwang/Poppins, vàng #DB9628, nút pill, logo, cho admin, portal và các trang login.
  - #435: bảng rộng cuộn trong khung (`minWidth:0`).
  - #436: sửa bug đếm lifecycle ở `/admin/tenants` (91,718 = 758×121 do join fan-out); font brand cho các route `(internal)`; emoji → lucide.
  - #437/#438: portal dùng được trên điện thoại (drawer < 900px, grid tự xuống dòng); body font Poppins; modal rotate key.
- **AA-636**
  - #439/#440: portal hiển thị dữ liệu thật.
    - Bỏ các giá trị bịa: "22 days", thẻ re-rewrite 2/3, WanderLux/sara@ hiện cho mọi tenant, 300 RPM / Growth hardcode.
    - Bỏ LLM cost / "Bedrock" khỏi màn tenant.
  - Chuông mở được panel thông báo; các link bấm được; Settings trung thực.
  - Email hỗ trợ → `info@adventure.asia`.
  - `/v1/billing` thêm `rate_limit_rpm` và `plans`.
- **AA-637**
  - #441: live writing progress, xem ADR `docs/adr/0004`.
    - ContextVar stream sink; satellite chỉ stream khi có sink.
    - Tracker Redis `wp:{tenant}:{kind}:{job}` (TTL 1h).
    - Endpoint `GET /v1/progress/{tour|piece}/{id}`, scope theo tenant JWT.
    - Component `LiveWriter.tsx`.
    - Server tự tách JSON dở dang, strip tag `[R:]`/`[F:]`, ẩn `===SUMMARY===`.
- **AA-638**
  - #442/#443: checklist Get started, sparkline usage theo ngày (`/v1/billing.daily`), bảng lệnh ⌘K, skeleton, nhãn trạng thái dễ hiểu.
- **AA-639**
  - #444: truyền feedback vào vòng sửa T3.
  - #445: grounding đọc được số có đơn vị ("4,460m") và chuẩn hoá dấu phẩy nghìn; T3 chỉ chặn `_HARD_BLOCK_CODES`.
  - #447: `fit_seo_title()`.
  - #448: `GENERATE_MAX_TOKENS=8192`.
- **AA-640**
  - #446: tour quota chỉ lấy từ `membership_plans` (starter 50 / growth 200 / business 500).
  - Vượt quota → cho viết, log `rewrite_over_quota`, billing tính overage.
  - `PLAN_LIMITS` chỉ còn RPM.

**AA-CIS-Infra:** #71 (AA-310) — `stopTimeout = 90`, đã apply.

**AA-Ecosys (root):**
- #2: session logs S192–S195 + import steering vào Claude Code.
- #3: ignore `.vscode/`.
- PR phiên này: quy tắc steering "Script gọi LLM chạy tay — PHẢI ghi log chi phí" (từ AA-635) + log S196.

Implementation notes (gitignored): `docs/implementation-notes/AA-635/605/636/637/638/639/640.md`.

## Thay đổi Hạ tầng

- ECS `aa-cis-dev-api` đi từ taskDef :333 (AA-310) tới **:348** qua các lần deploy. Mỗi lần rollout đều COMPLETED.
- Không start/stop NAT/RDS/ECS, theo yêu cầu của Nghiệp: hạ tầng chạy suốt tháng 9 để theo dõi chi phí.
- Không có migration mới.

## Bằng chứng verify

- **AA-605/636/638:** Playwright đăng nhập prod với admin và tenant WanderLux (key xoay qua admin UI, Nghiệp cho phép, không lưu key). Kết quả: 12 trang portal ở 1440px và 400px không bị cắt/tràn, không lỗi JS, không còn chuỗi nội bộ; `/v1/quota` = 200 khớp billing.
- **AA-637:**
  - Tour Everest 16 ngày: stream theo từng field, 106 lần poll thấy chữ tăng, 0 lần lộ tag/JSON; title live = `rewritten_content.name` đã lưu.
  - Bài LinkedIn T9: text live khớp từng byte với `content_text` (1355 ký tự).
- **AA-639:** so trên cùng tour Manaslu 18 ngày.

  | Thời điểm | Số lần gọi writer | Thời gian |
  |---|---|---|
  | Trước sửa | 4 và 4 | ~354s |
  | Sau #445 | 2 | — |
  | Sau #447 | 4 (log cho thấy do truncation) | — |
  | **Sau #448** | **2 và 1** | **207s và 105s** |

  - Writer giờ ra 4256/4402 token với `end_turn`, trước đó bị cắt ở 4096.
  - Kuari Pass và Sacred Circuit: 1 lần gọi mỗi tour.
  - Chi phí tour dài: ~$0.31 → $0.10–0.18.

## Còn lại

1. **Dọn dữ liệu test WanderLux: CHƯA commit.** Bước DELETE trên DB prod bị hệ thống quyền của Claude Code chặn.
   - Script `.tmp-session/wl_clean.py` đã dry-run (ROLLBACK) khớp dự kiến: review_queue 1, content_piece 1, angle_gate_option 3, angle_gate_request 1, subject 17, tenant_tour_versions 8, tenant_rewrite_usage 1.
   - Giữ lại có chủ đích: `llm_call_log` (chi phí thật) và `audit_log`.
   - Nghiệp tự chạy: đổi `DRY_RUN = False`, rồi `bash .tmp-session/ecsrun.sh .tmp-session/wl_clean.py`.
2. **AA-641:** Backlog, chờ Nghiệp đọc mô tả rồi chốt.
3. **Key WanderLux:** đã xoay nhiều lần, không lưu. Cần thì bấm Key ở `/admin/tenants`.
4. **AA-634 Jev:** chờ API key.

## Lưu ý kỹ thuật cho phiên sau

- AWS CLI trong WSL:
  - Đặt `AWS_PAGER=""`, nếu không lệnh treo ở `less`.
  - Khi STS 8h hết hạn, lệnh ngồi chờ nhập MFA; chạy `aws sts get-caller-identity --profile aa365-admin` để làm mới.
- Git Bash làm hỏng `$VAR` và path trong `wsl -- bash -c '...'`: luôn viết script ra file rồi `wsl -d Ubuntu -- bash <file>`.
- `ecsrun.sh`: output của ECS exec bị cắt khoảng 1k ký tự (`Cannot perform start session: EOF`), nên in gọn trên 1 dòng.
- Live progress (AA-637): muốn stream thêm stage nào thì thêm vào `stream_stages` của tracker tương ứng; Redis lỗi thì chỉ mất phần hiển thị, job không bị ảnh hưởng.
- Grounding (`services/acp_shared/grounding.py`) dùng chung cho T3, T9 và N7. Regex số mới chính xác hơn theo cả hai chiều.
- Test `test_aa450` strong-ref: task nền của các test khác có thể còn sống sau khi loop đóng, nên test tự clear set trước khi kiểm.
