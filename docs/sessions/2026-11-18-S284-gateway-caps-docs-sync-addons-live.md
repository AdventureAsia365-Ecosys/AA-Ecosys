# S284 — 18/11/2026 — trần AI mỗi app mỗi connection, docs sync + docs reader, add-on live

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). ~06:30 → ~17:00 +07. Đổi tài khoản Claude 2 lần (lane resume).
**MFA aa365-admin:** hết hạn 18:29.

## Trạng thái

Đóng 8 issue có bằng chứng live: AA-1115, AA-1125, AA-1131 (scope), AA-1112, AA-1113, AA-1132, AA-1133 (scope),
AA-1116 (scope). Tạo mới: AA-1135 (Delivery v2), AA-1136 / AA-1137 (hooks + spec, S285), AA-1138 (so draft CRM),
AA-1139 (module TripPlanner trong app đại lý). Còn In Progress có tiến độ: AA-1111, AA-1126, AA-1127, AA-1128, AA-1051,
AA-1135, AA-1138. Số liệu hạ tầng: [state-snapshot](../audits/2026-11-18-S284-session/state-snapshot.md).

## Thay đổi Codebase (merged)

- **AA-1113** — CIS 451–453 (registry `free_text`, view trần connection, setting `cis.spend.connection_provider_budget_usd`),
  CIS #1579 / #1580 (gateway đọc registry, bảng "Connection budget split"); Partner crm-077 + #345 (CRM trần riêng mỗi
  connection), #348 (serializer ops không bỏ key trong giá trị setting); root #866, #878; Infra #912.
- **AA-1132** — root #875 (A1 lịch sử trang, A2 khối sinh tự động, A4 doc map + docs-impact chỉ cảnh báo) và #877 (A3, A5
  needs_review + freshness, A6 luật agent, A7 kiểm trong backtick, A9 cổng ảnh audit); caller CIS #1585, Booking #274,
  Partner #347, TripPlanner #281, Infra #918; Infra #919 (docs-sync đọc manifest); CIS #1587, #1589 (reader hiện lịch sử
  + nhãn Needs review).
- **AA-1133** — root #870, CIS 454 (#1581), #1582 (reader v2), #1588 (sửa sau verify live: widget feedback, scroll-spy,
  search).
- **AA-1135** — root #861, #874 (collector), CIS 450 + #1578 + #1584 (Delivery v2: date picker, biểu đồ); Kit Sync Booking
  #273, Partner #346.
- **AA-1116** — TripPlanner #280 (tên đại lý làm tên người gửi e-mail lead), CIS #1583 + Booking #272 (dòng chỗ vượt gói),
  root #872 (tool proof lead $0).
- **AA-1112** — CIS #1577, Infra #902 / #911, root #868, Booking #271 (retention live, rule bảng mới cần dòng retention).
- **AA-1111** — Partner #337 / #338 (gate npm audit có allowlist hạn), headers Infra #904, Partner #341, TP #279,
  Booking #268, CIS #1572. **AA-1126 L16**, **AA-1127**, **AA-1128**, **AA-1131**: các PR trong log Linear từng issue.

## Thay đổi Hạ tầng

- Migration áp trong phiên: CIS 447–454, tp-034, crm-077 (bk-059 có sẵn). Terraform apply: Infra #902, #904, #919.
- Cấu hình: setting provider budget + CRM `{"acc2": 5}` (tech lead nhập); connection acc2 monthly budget 25 USD chặn
  (agent, ghi chú cũ khôi phục từ audit log); `crm.retention.job_dry_run` off.
- Dữ liệu Dev: tenant giả mới "E2E Lead Proof Travel"; agency giả S283 seats 5 → 3 và AI on → off (đã trả về).
- Không đổi compute: tech lead chốt không T8i / ARM64 / Spot / Valkey (ổn định > tiết kiệm ~10 USD).

## Bằng chứng verify

- AA-1113: probe scrub `$0` ok; `/admin/llm-config` 14 stage `free_text`; bảng split acc2 Fits 30 = 25 + 5; setting CRM
  hiện `{"acc2":5}` sau #348; 5/5 lượt đọc split không lỗi CRM.
- AA-1116: lead CRM / e-mail / webhook PASS (webhook qua tunnel tạm, tech lead tắt auto mode); quota phiên AI dừng đúng;
  quote 244 USD = bản nháp Booking.
- AA-1132: manifest có 15 trang needs_review + freshness 6 repo + `manifest.previous.json`; API trả 14 trang có lý do.
- AA-1133: layout / search / TOC / feedback PASS (sau #1588); AA-1135: custom range chạy, lần đầu sau rebuild > 29 s.
- Ảnh + JSON: [docs/audits/2026-11-18-S284-session/](../audits/2026-11-18-S284-session/).
- Chi LLM: W5 null run 2,62 USD; AA-1138 nửa Haiku 0,002 USD.

## Jira

Đã đăng sau khi tech lead duyệt: PR-24 comment 10669, PR-25 10670, PR-22 10671
([nháp](../audits/2026-11-18-S284-session/jira-drafts.md)).

## Quyết định của tech lead

Duyệt danh sách S284 + hội tụ WIP; gate npm audit; retention Booking + CRM tắt dry-run; golden 1.5.0; AA-1135 làm ngay có
picker; AA-1113 mỗi app trần riêng, không cho CRM đọc CIS; AWS không đổi; hooks/spec thành AA-1136/1137 cho S285; tắt auto
mode cho tunnel webhook; ngân sách provider (bảng trên); CRM giữ Nova Lite, làm phép so rồi nối Claude cho draft nếu cần;
đăng 3 nháp Jira; bật tạm AI agency giả cho AA-1138; đóng AA-1116 và tách AA-1139.

## Còn lại

- AA-1135: lane L18 (đường lạnh custom range) — ship + verify ở phiên sau nếu chưa xong trong S284.
- AA-1138: nửa Nova Lite qua gateway CRM (output ecsx bị mất ở lần chạy thật, sổ CRM 0 dòng) → chạy lại `ONLY=en-01`
  trước; rồi trang so sánh ẩn tên model.
- AA-1111 (MFA TOTP admin, role agent chỉ đọc, ZAP), AA-1126 (ảnh quota), AA-1127 (C3/C4/D1), AA-1128 (backfill
  notifications cần duyệt, B5, D1), AA-1051 (prereg T9/S1/T2).
- Cảnh báo p95 API CRM (14:30–14:45) do agent verify gọi `/crm/ops/v1/settings` liên tục (~1,5 s/lượt): route chậm + alarm
  cần số request tối thiểu.

## Lưu ý kỹ thuật cho phiên sau

- Bài học mới đã chuyển vào `skill/aa-lessons/lessons.md` (setting registry chỉ Cognito; hợp đồng dữ liệu giữa 2 lane;
  ship ngay sau push đọc check cũ; đo model qua gateway của chính app; PATCH connection ghi đè notes; token GitHub trong
  test subprocess).
- Root #860 (bot regenerate infra docs) còn mở.
