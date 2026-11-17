# S283 — 17/11/2026 — Audit giao diện + docs, kiểm soát chi AI theo môi trường, add-on trọn vòng, tab Delivery

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). **Thời gian:** 17/11 ~06:15 → ~16:30 +07. Hết giới hạn 5 giờ tài khoản
Claude 2 lần (đổi tài khoản, lane chạy tiếp bằng resume). MFA `aa365-admin` tới 18:27. LLM trả phí phiên: **0 USD**
(null run W5 bị DRY plan chặn trước khi tiêu).

## Trạng thái

- **Done (bằng chứng live):** AA-1108 (lịch Delivery chạy), AA-1114 (subject_gate + ReDoS + CodeQL Partner), AA-1003 (R5–R7,
  Done-with-scope), AA-922 (lỗi KPI tuần sửa + chạy lại, Done-with-scope), AA-1123 (audit giao diện), AA-1124 (audit docs).
- **Tiến lớn, còn mở:**
  - **AA-1116** add-on: giảm giá contract 1.10 live (CIS 443/444, Booking 409,50 USD đúng báo giá), saga tạo đại lý CRM +
    mời chủ đại lý (tech lead thử thật), cổng CSV/Stripe theo gói, launcher TripPlanner. Còn: lead TripPlanner + trần phiên
    AI thử live, dòng phí vượt seat.
  - **AA-1115** thương hiệu đại lý trên TripPlanner live (0 chữ AA trên trang đại lý); còn ảnh chụp launcher → In Review.
  - **AA-1111** rà quyền Q4 xong (DB 7/7 đạt), allowed_account_ids, xoay key IAM user gốc, ZAP 0 High; còn MFA admin + role
    agent chỉ đọc.
  - **AA-1126** (mới) kiểm soát chi AI theo môi trường: L15 live (CIS 446: chế độ trần failover_continue, cầu dao bất
    thường, trần mỗi lượt S1/eval/adhoc, mọi giá trị trên Settings + trang AI gateway); L16 (thông báo hết quota + Upgrade)
    còn 447 vướng guard ranh giới → S284.
  - **AA-1125** (mới) tab Merge queue + Git map live; còn kiểm queue Booking/Partner + ảnh → In Review.
  - AA-1112 (DM-7.1 duyệt 64 dòng, retention_job live xoá 2.392), AA-1113 (che PII live, budget acc3 100), AA-1110 (trang
    chạy không cần agent, tabletop, SNS kênh 2 tắt sẵn), AA-1103 (module Academy L8 bản nháp), AA-1051 (W5 v7 live; null run
    chặn), AA-1004 (kiểm chuyển org 1.2–1.5/1.7 đạt, liên hệ BILLING đã thêm).

## Quyết định của tech lead (trong phiên)

- 06:4x duyệt danh sách; "kéo thêm việc, đánh giá toàn bộ issue Linear để xếp thứ tự".
- 07:10–07:19 chốt 19 câu (`docs/audits/2026-11-17-S283-session/decisions/decisions.json`): MFA admin = TOTP nhóm admin;
  role agent chỉ đọc mặc định; người giữ khoá 2 = chủ doanh nghiệp (đầu tháng 12); kênh cảnh báo 2 = chưa cần; xoá 2.392
  job (live); DM-7.1 duyệt theo nhóm; ADR 0009 d10 chấp nhận; budget acc3 100; null run v7 ≤ 5 USD; pilot AA-788 ≤ 5 USD
  từ 19/11; TL-11 gỡ cho $0; WAF lúc prod; go-live chưa hỏi; engine bản đồ dùng chung + báo giá; App template + L8; ruleset TP.
- 07:3x mở 2 issue audit chỉ đọc (AA-1123 giao diện, AA-1124 docs). ~09:xx: gom đề xuất về cuối phiên; giữ docs-as-code
  (docs đồng bộ cùng code, quản lý phiên bản bằng git); tư vấn /admin/docs giống trang docs thị trường.
- ~10:0x thêm tab Merge queue + Git map trên Delivery (AA-1125).
- ~12:xx nguyên tắc chi AI: dev trần cứng; prod dùng nhiêu tính nhiêu, quota theo gói, cầu dao bất thường; **code sẵn ngay
  ở dev, chỉ khác setting**; mọi ngưỡng chỉnh trên trang admin Settings (AA-1126).
- Bước tay tech lead làm trong phiên: tạo tenant thử qua saga, Generate now 3 báo cáo, xoay key IAM user gốc, liên hệ
  BILLING acc2, thêm ZAP vào allow-list Actions của org.

## Kết quả theo nhóm

- **Hội tụ + guard:** root #843 (catalogue snapshot + gitleaks allow-list, review độc lập); CIS #1551 (nightly random:
  cache gateway sống qua module + lỗi nửa đêm UTC); AA-1108 Done.
- **Đánh giá 35 issue Linear:** workflow 5 nhóm → xếp hạng → phản biện (17 vấn đề) → `.tmp-session/S283/triage.json`.
- **Add-on (AA-1116):** root #848 (contract 1.10), CIS #1554 (443/444), #1557, #1556 (saga CRM), #1558, #1562; Booking #262;
  Partner #332, #334, #335 (crm-076).
- **TripPlanner (AA-1115):** #273 (gỡ đăng nhập B2C, brand đại lý), #274 (404 gốc lọt vào payload; guard render HTML trong CI).
- **Báo cáo (AA-1003):** root #844, #845 (L8), CIS #1553; EX-06 65 báo cáo.
- **Bảo mật:** Infra #890 (script rà quyền DB), #891 (allowed_account_ids), #892 (SNS kênh 2 tắt), #895 (budget acc3),
  root #846 (run-without-agent, tabletop), #851 (ZAP), Partner #333 (guard ledger AI CRM), CIS #1559 (che PII).
- **AA-922:** CIS #1552. **AA-1051:** CIS #1560. **DM-7.1:** root #847. **AA-1125:** root #852, CIS #1563 (445), #1564.
- **AA-1126:** CIS #1565 (446), #1566.
- **Audit:** giao diện 225 trang (1 cao: rule giá test Booking hiệu lực 01/01/2027), docs 361 trang (24 sai, 35 cao),
  tư vấn docs-as-code, ZAP 0 High, AI caps gap.

## Bằng chứng

Snapshot: `docs/audits/2026-11-17-S283-session/state-snapshot.md`. Audit: `docs/audits/2026-11-17-S283-{fe-audit,docs-audit,
docs-advisory,access-review,session}/`. Trang duyệt: phiên 19 câu https://claude.ai/artifact/7Rrd1NysnLdw2oaEwDA8eS, cuối
phiên 24 câu https://claude.ai/artifact/FFHgg1Bm4A5n6odz8rvkRb.

## Jira

Đã đăng (tech lead duyệt): PR-25 10665, PR-26 10666, PR-24 10667, PR-22 10668.

## Còn lại / phiên sau (S284)

1. Trang duyệt cuối phiên: tech lead trả lời đủ 24/24 (`decisions-close/answers.json`). Làm trong S283: B0 (xoá rule
   giá test), sửa đổi ADR 0009 quyết định 6. Sang S284: dọn F-20…F-24, B1 lịch mùa, docs batch 1–5 (reader cho mọi
   staff sau khi sửa, tìm kiếm FTS5 phía server, sidebar theo front-matter, cổng docs-impact chỉ cảnh báo, DVC chưa
   dùng), FE batch top 6 với issue theo app, 1 issue cho 19 việc code từ audit docs, security headers, W5 (gán nhãn 6 mục
   GATE, margin 4,0, reverify t9_blog ≤ 5 USD rồi null run).
2. AA-1126 L16: thiết kế lại đường báo đại lý của TripPlanner (không cấp quyền vào `shared.notifications`), rồi ship 447,
   CIS #1568, TP #276, PR code Partner.
3. Booking B0 (rule giá test hiệu lực 01/01/2027) + B1 (lịch mùa báo thành công giả) nếu tech lead duyệt.
4. Xoá key IAM cũ đã Inactive + file sao lưu credentials (≥ 18/11). Kiểm Merge queue Booking/Partner trên Delivery.
5. AA-788 pilot từ 19/11 (đã duyệt ≤ 5 USD). AA-1061 từ 28/11. AA-1122 ≥ 02/12.

## Lưu ý kỹ thuật

- Root Terraform acc3 sau #891 cần `init -reconfigure -backend-config=…` + `terraform.tfvars` không commit (account_id, aws_profile).
- Release-please W47 đã merge (CIS #1538, Booking #261, Partner #329, TripPlanner #272).
- Root console session sinh cảnh báo AA-873 cho mỗi lệnh root; đề xuất gom theo phiên (trang duyệt).
