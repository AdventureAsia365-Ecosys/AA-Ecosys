# S282 — 16/11/2026 — Giá phương án B toàn hệ thống, DFS sẵn sàng bán, Sentry đủ dịch vụ, CRM W6/W7, audit toàn hệ thống

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). **Thời gian:** 16/11 ~06:30 → ~21:30 +07. Đổi tài khoản Claude 2 lần
(lane chết giữa chừng, chạy lại bằng resume). MFA `aa365-admin` hết 18:30 rồi làm mới (tới 06:16 ngày 17/11). Trần LLM
trả phí phiên 5 USD; đã tiêu ≈ 0,8 USD (research địa điểm 0,65 + AA-1048 v6/v7 ≈ 0,15).

## Trạng thái

- **Done (có bằng chứng live), 7 issue:** AA-963, AA-968, AA-970, AA-1107, AA-1109, AA-1048 (Done-with-scope),
  AA-1120 (Done-with-scope). AA-1090 đã Done từ trước (dọn domain thử đầu phiên).
- **Còn mở:**
  - **AA-1122 (In Review):** CIS 440–442 đã áp, CIS #1547 / #1548 / #1549 live; tab Research chạy; PAA tour 99,4 %.
    Còn 2 điều kiện: lượt tự chạy theo lịch (tháng 11 đã vượt trần 5 USD) và bảng lịch sử có dòng 12 tháng → kiểm
    ≥ 02/12 sau khi tech lead bật `cis.seo.research_auto_enabled` hiệu lực 01/12.
  - **AA-1116 (In Progress):** giá B xong ở mọi app; còn saga khởi tạo đại lý không bước tay, module TripPlanner trong app
    đại lý, cổng CRM còn lại, lead TripPlanner + trần phiên AI thử live, contract 1.10.
  - **AA-1111 (In Progress):** Sentry đủ 5 dịch vụ; còn MFA admin, rà quyền Q4, account guard Terraform, ZAP.
  - **AA-1108 (In Review):** trang Delivery live; lịch hằng giờ chưa chạy lần nào → root PR này lưu lại cron.
  - **AA-1003 (In Review):** R6 chờ Generate now; R7. **AA-1103 (In Progress):** template v1.0.0 phát hành; pilot + khoá
    Academy còn lại; phần v1.1 ở **AA-1121** (mới).
- Bài học S282 đã vào `skill/aa-lessons/lessons.md` (commit trong root PR này).

## Quyết định của tech lead (trong phiên)

- 06:40 duyệt danh sách đầu phiên. 07:20 AA-1048 làm v6 + tạo AA-1107; ~09:00 duyệt v7.
- ~09:10 yêu cầu báo cáo tiến độ theo app, audit toàn hệ thống (AA-1109 → duyệt 10 issue mới), sơ đồ tài khoản AWS.
- 07:50 / 08:10 trang Delivery (AA-1108) + xuất kiến thức cho Academy/kit.
- **Giá: chọn phương án B**; mọi giá/điều khoản chỉnh được trong admin, không code cứng; không bán lẻ add-on;
  TripPlanner chỉ Hosted 49 / Pro 99, gỡ embed + API khỏi Pro.
- **Template:** "ok template", tạo repo project-template (tắt auto mode), mở AA-1121 "Project kit v1.1".
- **DFS:** duyệt mục 1–5 (lịch sử mùa vụ, nhóm biến thể, làm mới 90–180 ngày, tự nghiên cứu có trần tháng + tab
  Research, bù PAA tour); **không** làm 6–7 (GSC/rank/SEO riêng từng đại lý, từ khoá tiếng bản địa).
- Research địa điểm còn thiếu: chạy, dùng AI Anthropic API.
- acc1 → mail công ty info@adventure.asia cuối 11 / đầu 12 (ghi memory billing-transfer-timeline). Role
  OrganizationAccountAccessRole trên acc2: giữ tới khi ký phụ lục TrueIDC.
- AA-968 / AA-970: tech lead tự gắn add-on CRM Core (trial) + override cho Sen Vàng trên Tenant 360.
- ~20:45 duyệt "đăng" 3 nháp Jira; "ok đề xuất": bật tự nghiên cứu DFS từ 01/12, trần 5 USD/tháng (bước tay đã gửi).

## Kết quả theo issue

- **Giá B (AA-1116):** root #832 (ADR 0019 amendment, contract 1.9), CIS #1543 (435–439) + #1544, dữ liệu 8 gói qua Plans
  API; lane l17: root #836, TripPlanner #270 (tp-032/033) + #271, Booking #260, Partner #331 (crm-075). Review độc lập
  tìm 4 lỗi (lập hoá đơn trùng tháng khi đổi tiền tệ, thiếu cờ ưu đãi, xoá tenant bỏ sót bảng mới, allowlist CI) — sửa
  trước merge. Live: studio đại lý audit 409,50 USD = báo giá CIS (349 + 3×19 + 49 − 10 %); Settings CRM 3/500; Booking
  Agency billing ô USD/VND.
- **DFS (AA-1120, AA-1122):** "5.589 địa điểm thiếu" là đo sai đơn vị → gap thật 215; research 3 job (DFS 0,64 + LLM
  0,012 USD, Anthropic API), 5.877 địa điểm, 0 stale. AA-1122: CIS #1546/#1547 (440–442), #1548 (preview PAA 77 s →
  4,7 s, chỉ mục keyword trong bộ nhớ), #1549 (link Settings `?app=cis&key=research` + guard test); bù PAA miễn phí
  239 tour → 99,4 % (839/844).
- **Sentry (AA-1111 phần 1):** triage 16 lỗi, CIS #1541; 5 dịch vụ báo lỗi (CIS #1545, Booking #259, Infra #877/#878,
  Partner #330).
- **CRM W6/W7:** AA-963 (Partner #324/#328), AA-968 (root #822, #326, #327), AA-970 (#325).
- **AA-1107:** EXPLAIN 606 → 143,9 ms. **AA-1048:** v7 ghim (FP 68 % / TP 88 %).
- **AA-1108:** trang Delivery (CIS #1536, #1542). **AA-1109:** artifact audit 3,2/5.
- **Template:** project-template v1.0.0 (CI xanh, smoke copier).
- **Công cụ:** root #829 (gate lượt chạy trùng giây), #831 (ship_wave tự dò gitleaks của mise). Sửa thêm CIS #1550
  (trang Settings hiện "đang tải" thay vì trắng — tech lead gặp lúc cuối phiên).

## Bằng chứng verify

Snapshot: `docs/audits/2026-11-16-S282-session/state-snapshot.md` (8 service COMPLETED, CIS 442 / bk-058 / tp-033 /
crm-075, `shared.job` rảnh). Ảnh: tab Research, Settings CRM, studio Billing, Booking Agency billing (`.tmp-session/S282/`).

## Jira

Đã đăng (tech lead duyệt "đăng"): PR-26 comment 10662 (2 ảnh), PR-27 comment 10663 (1 ảnh), PR-22 comment 10664 (1 ảnh).
Bản lưu: `docs/audits/2026-11-16-S282-session/jira-drafts.md`.

## Còn lại / phiên sau (S283)

1. Kiểm lịch Delivery (`event=schedule`); chưa chạy → CI hygiene dispatch (AA-1108).
2. AA-1116 phần còn lại (saga khởi tạo, module TripPlanner, cổng CRM, lead TP live, contract 1.10).
3. AA-1111 phần 2 (MFA admin, Q4 access review, account guard, ZAP).
4. AA-1003 R6 Generate now + R7; AA-1103 pilot / khoá Academy; AA-1086 G8, AA-1089, driver T9.
5. ≥ 02/12: lượt tự nghiên cứu đêm đầu + history (AA-1122).
6. `done_audit` còn báo gạch Done-when chưa trích trong comment ở các issue Done-with-scope (AA-1120 replay < 50 %,
   AA-1048, AA-970/968/963 chi tiết R/E) — rà lại từng gạch, không mở lại hàng loạt.

## Lưu ý kỹ thuật cho phiên sau

- Migration Sync Infra lỗi "rule did not run because of a timeout (HTTP 403)" là lỗi tạm của GitHub → `gh run rerun --failed`.
- `ship_wave` chạy contract `tp-033` ngay sau khi copy mà không chờ expand `tp-032` do Migration Apply tự áp → tp-033
  từ chối (RaiseError "tp-032 not applied"), không ghi gì; chạy lại sau khi Migration Apply xong. Guard đề xuất: ship_wave
  chờ expand cùng chuỗi đã áp.
- Job "Migration preflight" của Booking kẹt "in_progress" trong một run đã success, run không cho rerun → commit rỗng.
- Log task DB Migrate nằm ở CloudWatch `/ecs/aa-cis-dev` stream `migrate/…`, không ở log job GitHub.
- Ghi setting registry cần Cognito người thật (E2E chỉ đọc) → bước tay cho tech lead, có `Effective from`.
