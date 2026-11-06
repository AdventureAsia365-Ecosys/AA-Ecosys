# S271 — Pilot gate, tag chuẩn, chất lượng viết (ADR 0020, W0), tối ưu CI, bài học thành guard

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). 06/11 ~06:36 → 07/11 ~02:00 +07. Đổi tài khoản Claude 3 lần
(info → admin → info), chạm hạn mức 5 giờ 2 lần, MFA nhập lại 2 lần, 3 cửa sổ tắt auto mode.
Snapshot: `docs/audits/2026-11-06-S271-close/state-snapshot.md`.

## Trạng thái
- Danh sách đầu phiên: M-P1 pilot gate 6/6 + backup RDS 14 ngày; AA-820 DPA v0.3 + trang pháp lý v0.5; AA-741 phase 1;
  AA-1038 R5 lát 2; AA-1046 gỡ B2C (bk-045 từ 28/11); AA-911 staff web lên ECS (phase 1 live, #1339 gỡ cầu
  CIS→Booking live); AA-855 dừng quay video định kỳ; hygiene (apt upgrade CIS).
- Ngoài danh sách (tech lead yêu cầu): tag chuẩn 8 khoá + guard CI; sơ đồ kiến trúc AWS (icon chính thức); lịch Billing
  Transfer theo ngày; form AWS Sales cho acc3; gateway token budget và thinking; **chất lượng viết** (3 audit + đánh giá
  thiết kế 4 workflow → 16 quyết định → ADR 0020 → W0 ship đủ); **tối ưu CI** 5 repo (~−50% phút); **bài học thành guard**.

## Quyết định của tech lead
- Duyệt R2 rerun (trần 2,5 USD); "điều tra kỹ hết" trước khi chạy lại; rà toàn bộ bước viết blog và đường viết tour.
- 16 quyết định chất lượng viết (D1–D16), **chọn A cả 16** (`docs/audits/2026-11-06-S271-writing-quality-audit/decisions.md`).
- Linear: 1 issue mỗi đợt; W0 theo AA-900, W1–W6 = AA-1047 … AA-1052.
- Cho tới khi acc3 dùng được: ưu tiên API trực tiếp (route v6 đã đúng; GPT không đảo được do luật S235).
- Làm hết W0, tăng tốc; sửa CI ("lãng phí vô lý"); bài học phải thành guard.
- Master plan giữ link Q4Lv…; artifact khác sang tài khoản đang dùng; sổ link `docs/artifacts/`.
- Interface endpoint chỉ ghi chú, hỏi trước khi làm. Nháp Jira lưu lại, gom sang S272.

## Thay đổi Codebase (đã merge, live trên Dev)
- **CIS:** #1344 token budget gateway; #1345 mig 381 effort; #1346 thinking mode; #1347 mig 382 floor GPT-6;
  #1348 từ chối dự kiến; #1349 mig 383 route (bỏ GPT-6 khỏi writer, nova-lite khỏi judge); #1350 gateway giữ retry
  cut rỗng + dấu degraded; #1351 mig 384 prompt eval v2; #1352 R2 ghép đối chứng + từ chối ở $0 + ghim judge;
  #1353 mig 385 llm_cassette; #1354 cassette recorder; #1355 S1/T2 an toàn (cưỡi voi, hitl, approve gate, T2 judge
  chỉ báo cáo, S1 judge khỏi luồng thật); #1356 T9 lượt 3 dừng và gắn nhãn; #1357 fingerprint rộng + đóng băng
  mining tới R1; #1358 funnel CIS-08 + watchdog; #1359 CI gọn; #1339 gỡ cầu CIS→Booking; #1335 apt upgrade; #1343.
- **Partner** #239 CI gọn (+ chép lại `sameOrigin.ts`, sửa test hẹn giờ); **Booking** #204 CI gọn, #203;
  **TripPlanner** #229/#231/#232.
- **Infra** #694 backup 14 ngày, #702/#704 staff web, #708/#709 copy, #711 quét secret theo khoảng commit, #712 guard
  (Terraform lock, kiểm trust IAM, workflow lint).
- **Root** #593 gateway_status, #598 retention cassette, #600 CIS-08, #601 quét secret, #602 guard bài học (đang merge
  lúc ghi log), ADR 0020 + sửa đổi ADR 0009 (PR chốt phiên).

## Thay đổi Hạ tầng
- RDS backup 14 ngày; staff web (CIS admin, Booking admin) trên ECS, DNS cut-over, Cognito 7/7; tag chuẩn áp dụng.
- Migration CIS 381–385 apply trên Dev; route config version 7.

## Bằng chứng verify
- Snapshot cuối phiên (ECS, health, migration, bảng job, repo): file snapshot ở trên.
- Route sau 383: 0 vi phạm (writer không GPT-6, judge không nova-lite).
- R2 chạy thử: đối chứng 18/18 (trước 0/15); funnel baseline T9 10,4% / S1 47,8% / T2 64%.
- `POST /auth/booking-token` → 404. acc3 0 lỗi / 31 từ chối dự kiến trong 24 giờ.
- GitHub Actions tháng 11 tới 06/11: 733,5 giờ (0 USD vì repo public).

## Còn lại
- **AA-900 / W0:** kiểm cassette có dòng sau probe 05:02Z; chấm thử judge-only (vài cent) rồi R2 một lần (đợi W1/W2
  theo kế hoạch ADR 0020).
- **W1 (AA-1047)** làm đầu S272, kèm các lỗi nhỏ từ review W0 đã ghi trên issue.
- **Lane l22** (guard test app): đang chạy lúc ghi log → ship ở S272 nếu chưa xong.
- **AA-911:** xoá project Vercel `aa-cis-frontend`, hẹn xoá secret khoá ký cũ → cần tech lead duyệt.
- **AA-1040** (header AI ở bản xuất studio, hạn 02/12) → S272.
- 12 guard còn lại (ECS exec, nguồn chi phí, Linear Done, gitleaks trước push…) → S272.
- Hẹn giờ: tag TrueIDC chiều 07/11; mig 336 sau 10/11 12:00Z; bk-045 từ 28/11; Billing Transfer theo lịch AA-1004.
- Nháp Jira (PR-22, PR-17, PR-25, PR-20) chưa đăng: `docs/audits/2026-11-06-S271-writing-quality-audit/jira-drafts.md`.

## Lưu ý kỹ thuật cho phiên sau
- Sau #602: `gh pr merge` trần bị chặn — dùng `tools/github/ship_merge.py` hoặc `ship_wave.py`; hook chặn `pkill -f`,
  vòng zsh `for x in $VAR`, `export $(...)`, lệnh nặng khi RAM thấp; mở lane cần slot plan.json đúng phiên.
- Bài học mới phải có trường `Guard:` (lint ở Docs lint). Lỗi lặp lại → làm guard, không ghi gộp.
- PR chỉ có code: xếp merge queue song song (queue CIS kiểm 4, merge 5 một lượt); chỉ chuỗi migration mới tuần tự.
- CI mới: PR chạy phần nhanh; integration, Docker, frontend build chạy trong merge queue; push lên main không chạy CI.
- Chạy test ở máy: ẩn cấu hình AWS (`AWS_CONFIG_FILE=/dev/null` …) để import app không bật lời nhắc MFA.
