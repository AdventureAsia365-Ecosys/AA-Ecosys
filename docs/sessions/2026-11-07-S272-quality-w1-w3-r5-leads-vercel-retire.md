# S272 — Chất lượng viết W1/W2/W3, R5 lead → CRM đại lý, gỡ Vercel staff, guard bài học

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). 07/11 ~08:00 → 08/11 ~10:00 +07 (nghỉ đêm chạy lane tự động).
WSL hết RAM 1 lần buổi sáng (pre-push CIS đầy đủ + 5 lane), chạm hạn mức 5 giờ 3 lần (lần cuối ~03:00 08/11, chạy lại
09:00), MFA nhập lại 2 lần, 2 cửa sổ tắt auto mode. Snapshot: `docs/audits/2026-11-07-S272-close/state-snapshot.md`.

## Trạng thái
- Danh sách đầu phiên (duyệt "ok"): guard lane l22, **AA-1047 W1**, **AA-1048 W2**, **AA-1040** header X-AI,
  **AA-900** W0 kiểm cassette, guard bài học còn lại (AA-1024).
- Thêm theo yêu cầu: **AA-911** gỡ Vercel staff (duyệt 07/11); sơ đồ Gantt trong master plan; kiểm mail/chi phí acc1;
  **AA-1038 R5** lát 3 (lead → CRM đại lý, thương hiệu, trần AI) + lát hosting TripPlanner; kéo trước từ S273:
  **AA-1049 W3** (chuỗi T9 và T2) và **panel W2 lượt 1**.

## Quyết định của tech lead
- AA-911: duyệt gỡ Vercel cho app staff ("duyệt"), rồi "duyệt hết" 7 mục: dọn secret/GitHub, xoá Vercel
  `aa-booking-admin` + `VERCEL_TOKEN` Booking, chạy thử trả phí W1 (3 bài ~0,50 USD + 1 T2 ~0,2 USD), panel W2 ở S273,
  tạo issue cho 2 mâu thuẫn W1, apply LOCAL MFA Infra #721 sau khi app R5 lên (S273), nháp Jira.
- **Nháp Jira S272 gom sang phiên sau** (không đăng).
- Không xoá Vercel `aa-tripplanner` khi TripPlanner chưa chạy trên ECS.
- Làm xuyên đêm tới 6h, chú ý OOM; "tăng tốc".

## Thay đổi Codebase (đã merge, live trên Dev)
- **CIS:** #1361 sửa review guard; #1362 mig 386 FactSheet; #1363 FactSheet + fs_id + đo đầu vào; #1364 cassette ghi
  lượt trả lời hỏng có tính tiền; #1365 gỡ deploy Vercel admin; #1366 header X-AI cho DOCX T2; #1367 mig 387 + #1374
  mig 389 (phiên bản prompt); #1368 registry chính sách viết (`writing_policy.yaml` v1, compiler, lint, bộ fixture mâu
  thuẫn; gate giữ fail-closed như main); #1369 `final_contract` REPORT mọi lối ra; #1370 sửa đo drift; #1371 guard
  wave/deploy/gitleaks/workflow lint; #1372 mig 388 + #1373 công cụ ground truth W2; #1375 mig 390 lead route + view
  ngân sách AI; #1376 kit brand theme; **#1377 W3 T9** (bảng định tuyến 0-diff, PieceStore + replay, prespend báo
  cáo; guard khoá ổn định + seo_builder sau cờ opt-in); #1378 editor lead route Tenant 360 + chặn URL webhook nội bộ;
  **#1380 W3 T2** (bộ điều phối tuyến tính sau cờ `T2_ORCHESTRATOR`, mặc định = main, parity golden 8 kịch bản).
- **Partner** #242 BFF chuyển header X-AI + tên file; #243, #244 guard; #245 `crm_tp_lead_pull`; #247 giữ lời nhắn khách
  (NFC); #246 kit sync (đang merge lúc ghi log).
- **Booking** #206, #208 guard; #207 gỡ deploy Vercel admin; #209 kit sync (đang merge lúc ghi log).
- **TripPlanner** #234, #235 guard; #237 tp-026; #238 kit sync; #239 lead.submitted.v1 + kéo qua M2M + trần AI + thương
  hiệu tenant. Nháp: #236 (web lên ECS sau CloudFront).
- **Infra** #713 apex sang ALB, #715 gỡ Preview staff, #718 guard; copy mig #714/#716/#719/#720/#723/#724. Nháp: #721
  (kênh lead: scope M2M, URL, khoá webhook), #722 (TripPlanner web: ECR, ECS, CloudFront, WAF; DNS vẫn ở Vercel).
- **Root** #605/#613 DM-7.1; #606 + #618 công cụ PR (wrapper hook bỏ `GIT_DIR`, giới hạn 900 s, in bước pre-push lỗi);
  #607 ADR 0020 d8; #611 tài liệu gỡ Vercel; #612 guard bài học còn lại; #617 runbook cut-over TripPlanner web;
  #619 hợp đồng `lead.submitted.v1`; bot schema dump #609/#610/#614/#615/#620/#621, infra docs #608.

## Thay đổi Hạ tầng
- Apex `lumiguides.it.com` → ALB (301 → aa-cis.); host/client Preview staff đã gỡ; Vercel `aa-cis-frontend` và
  `aa-booking-admin` đã xoá; secret khoá ký cầu nối lên lịch xoá 07/11 (hồi phục tới 14/11).
- Migration apply trên Dev: CIS 386–390 (389, 390 apply vượt thứ tự vì 336 cố ý hoãn tới ≥ 10/11), tp-026.
- Không tạo tài nguyên AWS mới trong phiên (Infra #721/#722 còn nháp, chờ apply LOCAL MFA).

## Bằng chứng verify
- Theo snapshot: CIS api :1051 / worker :617 cùng `dev-f251917e`, schema 390; Booking :111 bk-044; CRM api :142
  crm-046, web :116; staff admin trên ECS; TripPlanner web `ffca93c6`; `shared.job` rảnh, 0 wave.
- W1 chạy thử trả phí (T2 + 3 bài T9 trên tenant audit): Playwright 10/10; 4 FactSheet mới, mọi bài có `fs_id`, meta
  blog 147 ký tự; ≈ 0,21 USD (t9_write 0,104, t2_generate 0,074). Báo cáo `final_contract` trên 814 Master: 797 đạt,
  17 lật (9 cưỡi voi, 6 lệch ngày nguồn, 3 thiếu ngày) — `aa1047-final-contract-report.json`. Đo đầu vào: atom không
  neo 3,4%, master_drift 232/892 = 26% (> 15% → chỉnh provenance trước W3 S1).
- W3: replay T9 trên fixture-1.2.0 mặc định vs main 0 khác biệt chưa khai báo (23/30 khớp cassette, 7 hụt SEO-fit không
  so); T2 parity golden 8/8 = main, replay mặc định 0/0/0 (9/9 cassette). Log CIS sau deploy: 0 `RouteTableError`.
- AA-1038 lát 3: lead pull CRM chạy mỗi phút, `not_configured` (chờ #721); CIS route lead trả 403 khi chưa đăng nhập.
- AA-911: `POST /auth/booking-token` 404; `booking.staff_users` active_unlinked=0 (S271).
- acc1: 0 tài nguyên tính tiền; mail là cảnh báo budget DỰ BÁO (3,01 USD), thực tế tháng 11 = 0.

## Còn lại (việc chưa xong)
- **Chờ anh (LOCAL MFA):** apply Infra #721 rồi #722 → biến repo TripPlanner → merge TP #236 → scale 1 → kiểm qua
  CloudFront → (duyệt) chuyển DNS → gỡ Vercel `aa-tripplanner`; root #616 (dòng secrets register) sau #721.
- **W2:** import 450 nhãn panel (`.tmp-session/aa1048/panel1/panel.jsonl`, không vào repo) — CLI `scripts/aa1048` không
  có trong image CIS và PII guard chặn đẩy gói dữ liệu lên S3 → chọn đường (DB Migrate run-script hoặc đưa CLI vào
  image). Export CL-1 chỉ có 24/1.602 claim held-out → cần thêm bài/tour để đo gate.
- **W1 trước Done:** chạy thử S1; xác nhận bộ fixture mâu thuẫn 100%; D1/D13 chờ W2.
- **W3:** S1 sau nhãn W2; bật cờ opt-in (T9, T2) chỉ sau replay dữ liệu thật + chạy thử ~1 USD + tech lead duyệt.
- `T9_FAQ_LLM_FILTER=on` trên worker — tech lead quyết giữ/tắt.
- AA-911: tách phần A10 (ngoại lệ E2E tới go-live) sang issue riêng rồi đóng.
- Nháp Jira S272 → S273 (cập nhật số liệu theo snapshot mới).

## Lưu ý kỹ thuật cho phiên sau
- Thay đổi hành vi luồng viết: kiểm chéo không hội tụ sau 2 vòng → ship sau cờ, mặc định = main, kèm test parity.
- Agent thử nghiệm không chạy cả thư mục test TripPlanner (> 5 GB RAM); pre-push TP dùng wrapper chạy tuần tự.
- Push Infra cần python có pytest/boto3 (`AA_PREPUSH_PYTHON`); `ship_open_prs` giờ in lý do.
- `gh pr edit` qua as-app có thể không đổi body (GraphQL Projects classic) → dùng `gh api -X PATCH`.
- Panel agent: kiểm đủ dòng; dùng số dòng thay hash.
- Lane mới cần venv CIS ghim (`.tmp-session/S272/cis-venv`, fastapi 0.161.1 / pydantic 2.14.1); venv CIS chính còn lệch.
