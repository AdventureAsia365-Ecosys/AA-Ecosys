# Audits — AA-CIS pipeline

| Ngày | Phạm vi | Bản xem | Ghi chú |
|---|---|---|---|
| 08/10/2026 | A-series (A1 viết Master + A3 atom/segment/route), 9 nước + India đợt 1, từ reset 01/10 | [HTML](2026-10-08-S218-a-series-pipeline-audit.html) · artifact `claude.ai/artifact/BuaUQnyYeNYn9LSBxxyY1m` | Cập nhật lần 2 sau khi chạy hết mọi nước (India, Japan, Philippines, Pakistan) |

Script đo (chỉ đọc, chạy trên API task qua ECS exec, ghi kết quả ra S3): `scripts-s218/`.
`run_script.sh <script.py> [ENV=VAL]` → upload, presign, ECS exec, in kết quả.
