# Audits — AA-CIS pipeline

| Ngày | Phạm vi | Bản xem | Ghi chú |
|---|---|---|---|
| 20/10/2026 | AA-805 (TripPlanner AI Phase 0) bằng chứng đóng: throttle 429 trên /narrate (bắt được, giới hạn lỏng hơn cấu hình), ownership 401/403, chạy lại 30 query search (30/30 200, semantic), cache chưa chứng minh được qua HTTP (mọi narration là master) | [MD](2026-10-20-S245-tp-ai-phase0/aa805-closing-evidence.md) | Phần DB (spend cap, cache, join inactive-tour) chờ DB Migrate run-script `aa805_ai_guards_read.py` |
| 20/10/2026 | AA-865: tỉ lệ retry thêm lỗi chặn (F9_cta_fact và mọi gate) gộp r5–r7 (n ≥ 60, Wilson 95%), phân loại từng ca C1/C2/C3 | [README](2026-10-20-S245-f9-pooled/README.md) | Khung (skeleton): script `script/s245_f9_pool.py` chỉ đọc, $0, chưa chạy; số liệu sơ bộ từ readout đã commit |
| 19/10/2026 | Kế hoạch tổng thể S244: audit toàn bộ 84 issue mở (4 project Linear), mốc, đường găng, kế hoạch theo phiên S244–S252, đề xuất đổi trạng thái đã verify | [README](2026-10-19-S244-master-plan/README.md) · [issues.md](2026-10-19-S244-master-plan/issues.md) · [backlog-proposal.md](2026-10-19-S244-master-plan/backlog-proposal.md) | Chỉ đọc. Không đổi Linear/Jira. Backlog sống §3/§3a/§4 thay theo bản này cuối S244 (trạng thái cập nhật) |
| 19/10/2026 | AA-816 Stage S: báo cáo cutover (S1 Production tắt đăng nhập mật khẩu, C9 Preview credential, I6 xoay admin secret, break-glass qua managed login + xoay; readiness 7 dòng; còn N-F, S2, A10, AA-680) | [MD](2026-10-19-S244-aa816-cutover/cutover-report.md) | Bằng chứng từng bước checklist A–F của cutover-prep.md |
| 19/10/2026 | AA-816 Stage S: kế hoạch chuẩn bị cutover Cognito (từng tài khoản staff, S1/S2 hỏng gì, checklist A–G, quyết định N-A…N-F) | [MD](2026-10-19-S244-aa816-cutover/cutover-prep.md) | Chỉ là kế hoạch, chưa chạy gì. Chuyển từ AA-CIS-App (repo public) sang đây khi review S244 |
| 10/10/2026 | Jev toàn hệ thống (24 câu hỏi, 30 ngày): hiệu quả, ngưỡng v2, thêm/giữ/bỏ (AA-756) | [HTML](2026-10-10-S223-jev-audit.html) · artifact `claude.ai/artifact/8A5XBeeUU5n7B8potPMt5q` | Script: `scripts-s223/`. Ngưỡng v2 đã áp Dev; shadow reject `a1_claim_supported` đo offline |
| 08/10/2026 | A-series (A1 viết Master + A3 atom/segment/route), 9 nước + India đợt 1, từ reset 01/10 | [HTML](2026-10-08-S218-a-series-pipeline-audit.html) · artifact `claude.ai/artifact/BuaUQnyYeNYn9LSBxxyY1m` | Cập nhật lần 2 sau khi chạy hết mọi nước (India, Japan, Philippines, Pakistan) |

Script đo (chỉ đọc, chạy trên API task qua ECS exec, ghi kết quả ra S3): `scripts-s218/`.
`run_script.sh <script.py> [ENV=VAL]` → upload, presign, ECS exec, in kết quả.
