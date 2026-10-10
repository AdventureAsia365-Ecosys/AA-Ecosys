# Audits — AA-CIS pipeline

| Ngày | Phạm vi | Bản xem | Ghi chú |
|---|---|---|---|
| 10/10/2026 | Jev toàn hệ thống (24 câu hỏi, 30 ngày): hiệu quả, ngưỡng v2, thêm/giữ/bỏ (AA-756) | [HTML](2026-10-10-S223-jev-audit.html) · artifact `claude.ai/artifact/8A5XBeeUU5n7B8potPMt5q` | Script: `scripts-s223/`. Ngưỡng v2 đã áp Dev; shadow reject `a1_claim_supported` đo offline |
| 08/10/2026 | A-series (A1 viết Master + A3 atom/segment/route), 9 nước + India đợt 1, từ reset 01/10 | [HTML](2026-10-08-S218-a-series-pipeline-audit.html) · artifact `claude.ai/artifact/BuaUQnyYeNYn9LSBxxyY1m` | Cập nhật lần 2 sau khi chạy hết mọi nước (India, Japan, Philippines, Pakistan) |

Script đo (chỉ đọc, chạy trên API task qua ECS exec, ghi kết quả ra S3): `scripts-s218/`.
`run_script.sh <script.py> [ENV=VAL]` → upload, presign, ECS exec, in kết quả.
