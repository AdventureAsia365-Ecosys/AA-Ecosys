# S258 (29–30/10/2026): quy hoạch AWS gọn + danh mục báo cáo, migration tự áp lần đầu, LLM gateway nhiều nguồn, ảnh bìa, LCP

Tác nhân: **Claude Code** (Ultracode; workflow nhiều lane, tối đa 2–3 agent cùng lúc vì RAM/swap). 29/10 20:13 →
30/10 ~07:30 +07. MFA làm mới 20:35 (hạn 08:21). Hạn mức phiên reset 03:10, không chạm trần. Số liệu cuối: 
`docs/audits/2026-10-30-S258-session-close/state-snapshot.md`.

## Quyết định của tech lead (trong phiên)

- 20:13: agent tự chọn 20 việc, coi như đã duyệt; việc cần duyệt thì duyệt theo kế hoạch; chạy liên tục.
- ~20:50: chị Thư (qua Zalo) hỏi email liệt kê nhu cầu AWS + bộ câu hỏi đại lý; Sunny Cloud chào gói (4 %, miễn phí
  dịch vụ, hoá đơn VAT); chị xin Claude for Startups 500 USD. Tech lead: làm **một trang báo cáo** (không trả lời lắt
  nhắt), số Dev không ổn định, tư vấn hạ tầng lâu dài; thêm **bảng so sánh đại lý**.
- 21:26: tạo issue + tư vấn danh mục báo cáo (AA-1001).
- 22:1x: tư vấn như kiến trúc sư AWS (tài khoản quản trị mới + thành viên, OU/SCP/Identity Center, Terraform, dev/stg/
  prod, profile, bảng); LLM gateway cắm API/Bedrock không code thêm; ghi vào 1 issue (AA-1002).
- 23:0x: tắt auto mode → Partner env `release` chỉ main; `DB_AUTO_APPLY=true`.
- 23:1x: duyệt xây toàn bộ 63 báo cáo (AA-1003). **Hạ tầng phải gọn: 2 môi trường (dev+stg chung / prod), 3–4 tài
  khoản**; kế hoạch gọn OK → issue triển khai AA-1004.
- 30/10: tin nhắn eCloudvalley theo ý sếp (văn thường, không nêu tên chị Thư; bỏ các ý họ đã trả lời 2/6/8).
- ~06:00: tắt auto mode lần 2 → Terraform apply IAM (Infra #508).

## Done / ship

| Việc | Kết quả |
|---|---|
| AA-1001 **Done** | Tư vấn danh mục báo cáo: kiểm kê 145 mục, **63 báo cáo / 14 nhóm** (P0 7), 11 mẫu, kế hoạch tự động, lộ trình R0–R7 ~107 ngày công. Root #345; trang https://claude.ai/artifact/Jiz8KaJiWrpdrvi5eJWWJ4 |
| AA-1002 (In Progress) | Quy hoạch AWS: bản đầy đủ (14 phần, ~70 bảng, phản biện 28 điểm) + **bản gọn khuyến nghị** (4 tài khoản, 2 môi trường, ~5–8 ngày công; +0–3 USD/tháng trước go-live) + LLM gateway nhiều nguồn (12 lát, phản biện 22 điểm). Root #346; trang https://claude.ai/artifact/6XpQ8YUU7w7HsZ9AoGfnRb (riêng tư, bảng so sánh 7 bên × 18 tiêu chí điền được, 63 ô điền sẵn; email + 30 câu hỏi đại lý dạng bảng). Gateway **S1** CIS #1158 (mig 304, DB Migrate) + #1159 live; **S2** mig 306 CIS #1163 (copy Infra #512, apply chờ job queued) + adapter Anthropic #1164 (chờ CI sau sửa CodeQL) + runbook cắm khoá root #352 |
| AA-1003 (In Progress) | R0 CIS #1157 (ngân sách acc2 300). R1 root #348 (registry 63 báo cáo / 235 KPI) + CIS #1161 (mig 305 tự áp; kpi_daily, report_run, 2 job kind, /admin/reports). R2 CIS #1162 (digest OPS-12, TP-03, DATA-01) + root #351 (postmortem đầu: sự cố acc3 29/10) + #353; theo sau: tp-022 TP #193 / bk-035 Booking #152 (contract, DB Migrate), CIS #1166, Infra #508 (IAM, apply 40975065381: 1 changed), Infra #509 (chờ) |
| AA-1004 (Todo) | Issue triển khai mô hình gọn; chờ ID tài khoản quản trị |
| AA-993 | Chuông không dựa cron: Infra #499 + 4 app (#1156, #148, #191, #124) + root #344. **Tự áp lần đầu**: bk-034 (Booking #149 → copy #501 → áp) và CIS 305 (copy #506 bot mở 1,5′ sau merge, bot merge 2′ sau). Sửa: Infra #503 (test header), #505 (404 ẩn danh), **#507 (probe tự áp không có role → secrets: inherit)**; drift job Infra #502 (lần đầu xanh, exit 0) |
| AA-997 | aa997.3 CIS #1147 + root #340: P4 sai-từ-chối 34/251 → **3/251 (1,2 %)**; census 3.842 dòng: aa997.2 từ chối 259, **aa997.3 33** |
| AA-900 | CIS #1148 (phân loại lỗi, dừng sớm `llm_access_denied`, thẻ khả dụng LLM) + #1160 (cũ > 6 h → unknown); probe live: gpt-6-luna → LLMAccessDenied 0,5 s |
| AA-814 theo sau | CIS #1149 (T2 đọc facts sau cờ `T2_FACTS`, nhãn `Source:`); thử live fact platform admin **PASS 26/26** |
| AA-789 | tier 0 CIS #1151 (golden text 169 → 0), seed alignment CIS #1152 (mặc định tắt) |
| Ảnh bìa (AA-671 theo sau) | CIS #1153 + apply live: pool **302 → 444/892**, ảnh 1.593 → 1.919, điểm đến 283 → 336 |
| LCP | TP #188: Bhutan **3,95 → 2,49 s**, /destinations 2,46 → 1,38 s (Lighthouse prod 5 lần) |
| AA-994 | TP #189 (token kit, Visual: sửa nhận SSO redirect), CIS #1155 (S6a form controls) |
| Eval prep | CIS #1154 + root #341 (AA-919 cặp hiệu chuẩn, AA-790 mẫu ≥ 20 bài; chạy cần LLM) |
| Mốc | C-M2 **PASS** (Inquiry → Completed, supplier riêng, trợ lý 7 route không lộ lãi); C-M3 PASS quote/hold/accept + 409 hold_expired (thiếu bước confirm); P-M1 P2b **PASS 8/8**, P1 một phần; Partner #123 test lọc lãi; M1b phần B drift xanh, phần A 6 lệch (root #343) |
| Khác | Booking gap Figma 23/25 (root #342); Partner pool MFA đã có; tin eCloudvalley (nháp) |

## Sự cố / bài học

1. Guard repo public chặn ARN mẫu `000000000000` trong test (2 lần: #1148, #1159) → dùng `<account>`.
2. Visual TP: `curl -L` theo 302 sang vercel.com → tưởng preview công khai.
3. Test Infra mặc định "chưa copy nào có header expand" → copy expand đầu tiên làm đỏ (#503).
4. Probe trong reusable workflow không nhận secret của environment → probe đỏ sau 2 lần tự áp (#507).
5. Bot `merge-check` coi gitleaks bị huỷ (đã có lần xanh) là đỏ → merge tay copy tp-022 #510.
6. PR migration và PR code tách đôi: test của migration nằm ở PR code → merge queue rơi (#1163) 2 lần.
7. Cổng schema-gate CIS: lần tự áp có file gần nhất (305) đỏ probe → **deploy CIS bị chặn** tới lần tự áp expand mới.
8. Auto mode chặn: force-push (thay bằng PR mới #1166), huỷ job queued (chờ job tự hết), Terraform apply (cửa sổ tắt).

## Jira

Nháp PR-22, PR-24, PR-26 ở `docs/audits/2026-10-30-S258-session-close/jira-drafts.md`, **chưa đăng**: tech lead bảo gom sang phiên sau cùng ngày (S259). Bỏ PR-27 (hạ tầng là việc kỹ thuật tech lead quyết).

## Chi phí

LLM: **$0** (acc3 bị chặn; probe bị từ chối không tính tiền). AWS mới: ~0 (IAM, workflow). Không dịch vụ trả phí mới.

## Việc cần làm đầu phiên sau (S259)

1. **Cổng deploy CIS**: chọn (a) sửa `schema_gate` chấp nhận probe độc lập mới hơn và xanh trên cùng DB, hoặc (b) chờ
   lần tự áp expand kế tiếp; rồi chạy lại Deploy Dev và verify #1160/#1161/#1162/#1166 live (`/admin/reports`, R1 chạy EX-04).
2. CIS 306: apply nếu chưa xong; merge #1164 (adapter) khi CI xanh; Infra #509.
3. AA-1004: khi có ID tài khoản quản trị → Organizations + Identity Center (ngày 1).
4. AA-997: đọc 33 mẫu → bật aa997.3 → chuỗi relocate → AA-990 recheck_14.
5. AA-1003 R3 (tiền), chạy R2 live sau deploy; C-M3 bước confirm (lát mới); P-M1 P1 cần mời user studio.
6. Chờ: chị Thư chọn đường AI (credit 500 USD / đại lý); trả lời đại lý; share trang cho chị Thư.
