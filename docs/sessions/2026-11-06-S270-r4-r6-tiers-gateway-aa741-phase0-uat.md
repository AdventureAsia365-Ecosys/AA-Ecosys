# S270 (05–06/11/2026): R4 + R6 + bậc giá đóng, gateway dời nấc bị chặn, AA-741 phase 0, chuỗi giá đóng, UAT vòng 1 (23 video)

Tác nhân: **Claude Code (Ultracode)** (VSCode/WSL; lane code trong worktree qua `tools/workflows/lane.js` → review nhiều góc nhìn →
lượt sửa; điều phối merge/deploy/DB Migrate/Terraform/kiểm live). 05/11 ~18:06 → 06/11 ~03:30 +07 (11:06Z → 20:30Z).
Số liệu cuối phiên lấy từ snapshot `docs/audits/2026-11-06-S270-close/state-snapshot.md`.

Môi trường: WSL khởi động lại 1 lần do hết RAM (~19:30 +07: 3 lane + Playwright của điều phối) → từ đó tối đa 2 lane nặng + 1 trình
duyệt. Chạm hạn mức 5 giờ 2 lần (~19:55 và ~00:50 +07) → resume bằng lịch tự đặt (01:04, 01:41). MFA nhập lại 1 lần. 1 cửa sổ tắt
auto mode (H3 AA-1008 + tạo user cs AA-1035). Playwright 1.65.0 phát hành dở trên npm (~01:30 +07) làm đỏ mọi job Visual CIS → ghim 1.64.1.

## Quyết định của Nghiệp (tech lead)

- **~18:20:** "ok làm đi" — danh sách 7 mục (AA-1037, AA-1030, AA-1035, AA-1042+1045, AA-741 phase 0, AA-1039, AA-1008 H3) + Jira gom
  S268–S270 + KAN-20 cuối phiên; Ultracode BẬT. Nhắc cập nhật tracker **đúng link** (`Q4LvqJyX…?sk=…`).
- **~20:30:** "Làm đi" — 5 đề xuất: (1) bảng giá AA trong CRM cho owner + agent; (2) Jira chỉ hỏi chị Thư câu Gold 6 % < sàn hợp đồng
  10 %; (3) đường ghi UAT tách về AA-855/AA-1010; (4) không port maker-checker sang CRM; (5) tạo **AA-1046** (R4b: xoá B2C + API hoá đơn).
- **~22:00:** sửa cách báo: đại lý **luôn** nhận nội dung đã viết; điểm / held chỉ ở Writing Lab. Báo "đại lý nhận X/X" + "tín hiệu Lab",
  không bao giờ "cần duyệt" (memory `tenant-sees-content-only`).
- **~23:00:** tăng tốc nhưng tránh OOM (≤ 2 lane nặng + 1 trình duyệt); **xong việc chính thì kéo thêm việc master plan tới 06:00 +07**.
- **~00:40:** hỏi chi phí mỗi lượt viết (đã trả lời: T2 ≈ 0,19 USD/tour, T9 ≈ 0,11 USD/bài); tự đặt lịch chạy lại sau reset hạn mức.

## Kết quả theo issue

Done (9): **AA-1037**, **AA-1030**, **AA-1035**, **AA-1039**, **AA-1008**, **AA-1045**, **AA-1042**, **AA-1029**, **AA-710** (06/11 ~06:10: tech lead quyết không đăng KAN-20, đóng benchmark). Tạo **AA-1046**.

| Issue | Trạng thái | Kết quả | PR / bằng chứng |
|---|---|---|---|
| AA-1037 R4 | **Done** | Luồng hoá đơn live trên đại lý hư cấu: SaaS + settlement → phát hành → e-invoice DEV → maker-checker → paid; quá hạn → past_due + chặn giữ chỗ + tạm khoá CIS → trả → mở; tắt ghi B2C 34/34 trả 410; đại lý đọc hoá đơn qua CRM 37 PASS; Tenant 360 Billing + nhóm Trade | Booking #194, #195, #196; CIS #1326; root #569, #570, #571 (DRY RUN drop B2C) |
| AA-1030 bậc giá | **Done** | 2 đối tác silver/gold cùng tour; rate card 10 % thay bậc; tariff = quote engine; CRM markup 20 % → 190,25; trang AA prices trong CRM (owner + agent, giới hạn đọc) | Partner #235, #236; Booking #197; ảnh `live-verify/aa1030` |
| AA-1035 R2 | **Done** | User E2E customer_success Dev-only chỉ đọc (A10d): API phạm vi 7/7, Playwright Cognito thật 28 ảnh, view-as + audit; nút ghi ẩn theo vai trò (#1331); badge Review chỉ gọi cho vai trò xem được Review (#1334) | CIS #1323 (378), #1324, #1325, #1331, #1334; Partner #234; Infra #691, #692; root #567 |
| AA-1039 R6 | **Done** | Redirect 15/15, 48 ảnh R6, retire → restore fan-out (mail + chuông, TripPlanner 410 → 308), chuông studio | CIS #1327; ảnh `live-verify/aa1039` |
| AA-1008 H3 | **Done** | Visual + Kit consumers là check bắt buộc trên merge queue 3 repo; verify-h3 xanh | CIS #1322; Partner #233; Booking #193 |
| AA-1045 explorer | **Done** | Explorer 7 ngày, lọc app/tenant, CSV, drill, trace; rollup = ledger (1.058 dòng, 1,98 USD) | CIS #1328, #1329 |
| AA-1042 route | **Done** | Tab Guide; nấc mở circuit vì bị từ chối được dời xuống cuối (không ghi dòng refused riêng); route test FORCED 16/16 (fallback → chuông + mail → primary back), NATURAL 11/11 | CIS #1329, #1332; root #572; tài liệu gateway EN/VI cập nhật trong PR chốt phiên |
| AA-1029 chuỗi giá | **Done** | Import Excel thật 19/19 (rollback sạch); báo cáo sẵn sàng giá: 892 plan, 2 có giá, **890 chưa có thành phần** (việc dữ liệu); AUD 422, Retry-After 5 | Booking #197, #198; Partner #236 |
| AA-741 T-series | In Progress | **Phase 0 xong**: 4 tenant audit; T2 đại lý nhận 8/8 (1,50 USD); T8 lỗi max_tokens → #1330 → chạy lại 8/8; judge thử nấc acc3 bị chặn → #1332; tổng ≈ 2,0 USD | CIS #1330; báo cáo `docs/audits/2026-11-05-S270-aa741-phase0/README.md` |
| AA-1038 R5 | In Progress | Lát 1 live: tp-025 (tenant_id + RLS shadow), Lambda gắn tenant demo mọi request | TripPlanner #226, #227; Infra #693; root #574 |
| AA-855 UAT | In Progress | Harness vòng 1 (catalogue, pilot guard, danh tính editor studio); **23 video PASS** (local `tools/uat/out/`) | root #575, #576, #577 |
| AA-1046 R4b | Backlog (mới) | Xoá bảng B2C (DRY RUN có sẵn) + API hoá đơn điện tử | — |

## Còn mở và vì sao

- **AA-741:** phase 1 (3 tour/thương hiệu, đủ kênh, ≈ 3–4 USD) + phase 2 (48 tour, ≈ 11–12 USD); `system_prompt` không được điền khi nhập .docx (§4.3).
- **AA-1038:** các lát R5 sau (brand theo tenant, lead về CRM tenant, frontend lên ECS).
- **AA-855:** đường ghi (chọn chủ đề, viết lại, đăng) chờ quyền ghi E2E; video chưa lên Drive `03 Duyệt`.
- **AA-1029 (dữ liệu, không phải code):** 890/892 tour chưa có thành phần khách sạn/dịch vụ → CSV sẵn sàng giá là danh sách việc.
- **Gói Growth:** 200 lượt viết lại/tháng ≈ 38 USD, sát trần AI 40 USD → đề xuất xem lại trần hoặc giảm chi phí T2.

## Chi phí phiên

LLM: **≈ 2,0 USD** (AA-741 phase 0: T2 1,50 + T7–T9 + chạy lại T8 0,08), route test + probe vài cent. Chi tiêu tháng 11 tới lúc chốt
2,05 USD. Không dịch vụ AWS mới.

## Trạng thái kiểm cuối phiên

Chi tiết: `docs/audits/2026-11-06-S270-close/state-snapshot.md`.

- ECS 5/5 COMPLETED, mỗi family chạy revision mới nhất: cis-api :1021 + worker :587 `dev-2d9374c4`; booking :108 `5066f753`; crm-api :139 +
  crm-web :112 `8575fada`.
- Migration: CIS **378**; Booking **bk-044**; CRM **crm-046**; TripPlanner **tp-025**.
- Bảng job: `shared.job` 0, `booking.job` 0, `crm.job` 2 job định kỳ. Không wave.
- Gateway: route v6 ưu tiên Anthropic API; acc3 7 model chính vẫn `access_denied`.

## Jira

6 nháp (PR-23, PR-17, PR-18, PR-22, PR-25, PR-26) ở `docs/audits/2026-11-06-S270-close/jira-drafts.md` — **chờ tech lead duyệt**
rồi mới đăng. **KAN-20 không đăng** (tech lead, 06/11 ~06:10). PR-20 kỳ 4 đến hạn thứ Hai 09/11.

## Việc cần làm đầu phiên sau (S271), theo thứ tự

1. Jira: tech lead duyệt 6 nháp → đăng (KAN-20 không đăng).
2. AA-741 phase 1 trên 4 tenant audit (≈ 3–4 USD), rồi phase 2.
3. AA-855: tải 23 video lên Drive; mở đường ghi UAT.
4. AA-1038 R5 lát tiếp theo.
5. **≥10/11 ~12:00Z:** áp 336, bật lại `DB_AUTO_APPLY_CONTRACT` → đóng AA-1024; C4.3 W46 từ 09/11; PR-20 kỳ 4 (09/11).

## Bài học (đã vào `skill/aa-lessons/lessons.md`)

- RAM: Playwright/ecsx của điều phối tính vào tải lane (tối đa 2 lane khi điều phối mở trình duyệt).
- Pool asyncpg `max_size=2` tự khoá khi hàm app lấy connection lồng nhau; MFA 8 giờ hết làm ecsx/as-app im lặng.
- PR xung đột không chạy CI `pull_request`; fixture FK tự tham chiếu vỡ khi chung shard; Playwright không lockfile vỡ khi upstream phát hành dở.
- Poller của shell phải theo luật trang của vai trò; kịch bản UAT có đăng nhập quay bằng `dryrun.cjs --record`.
