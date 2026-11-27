# S295 — Họp chủ DN, tư vấn tổng hợp, sửa lộ dữ liệu NCC (DB-01), Well-Architected

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). **Thời gian:** 26/11 ~08:10 → 27/11 ~13:40 +07 (qua đêm, đổi tài khoản claude.ai 1 lần, chạm trần 5 giờ 1 lần rồi resume).
**Snapshot cuối phiên:** [state-snapshot.md](../audits/2026-11-27-S295-session/state-snapshot.md) · **Jira:** [jira-drafts.md](../audits/2026-11-27-S295-session/jira-drafts.md)

## Trạng thái

- Họp chủ DN 26/11 11:00 theo runbook (PLMXb7Y3…, sửa 15 điểm trước họp). Chiều 26/11: AI Security Roadshow (Bitexco), debrief 32 ảnh slide.
- 27/11: 8 yêu cầu sau họp → trang tư vấn tổng hợp **AaSXbEqqRiir2478cj5GTq** (bản 14, 20 tab, 58 thẻ quyết định, db). Tech lead đã chọn 54/58; còn 4 thẻ "Ask AA (chi tiết)".
- Linear: tạo **AA-1182…AA-1195** (14 issue), 15 issue chuyển Todo/Backlog, In Progress 20 → 5; master plan S296–S300 chia lại.
- DB-01 (đại lý đọc được tên NCC + giá nguồn qua devtools) **sửa + deploy + kiểm live** trong phiên.
- Đánh giá Well-Architected đầu tiên (6 trụ + SaaS + GenAI lens): 8 HRI / 46 MRI; ghi vào AWS WA Tool + sổ báo cáo (SEC-11).

## Thay đổi Codebase

| Repo | PR | Nội dung |
|---|---|---|
| AA-CIS-App | #1713 | AA-1181 (a) sau họp (merged, verify live) |
| AA-CIS-App | #1718 `dd1a441d` | DB-01: projection tenant của `raw_tours` thành allowlist, regex chặn khoá thương mại, bỏ `price_raw` khỏi SQL tenant, giá "In my catalog" lấy từ Booking `price.from.v1`, fact-lock không đọc `price_raw` |
| AA-CIS-App | #1719 | Sổ báo cáo thêm SEC-11 (review Well-Architected hằng năm) — lúc chụp snapshot đang trong hàng merge |
| AA-Partner | #403 | Cookie `__Secure-` (merged, verify live) |
| AA-Partner | #404 `7a972268` | DB-01: BFF `/api/tenant/*` chỉ chuyển tiếp 64 đường studio thật sự dùng, còn lại 404 |
| AA-CIS-Infra | #1041, #1044 | Luật mật khẩu pool partner; drift WAF_FILTERED (apply 2/2/2) |
| AA-Ecosys | #1043 `b108667c` | Bot tái sinh infra docs |
| Root (PR cuối phiên) | — | audits S295 (meeting prep, roadshow, advisory, well-architected, session), ARCH-11, SEC-11 trong `docs/reports/catalog.yaml`, plan.json + tracker, registry artifact, lessons |

## Thay đổi Hạ tầng

- Mật khẩu master RDS xoay 27/11 (N2): RDS + secret `aa-cis/dev/rds` + GitHub `TF_VAR_DB_PASSWORD`; DB Migrate run-script đăng nhập được; 3 app `/health/ready` 200.
- AWS Well-Architected Tool: workload "AA Ecosystem (Dev)", 98 câu trả lời, milestone "S295 baseline 2026-11-27" (0 USD).
- Không bật dịch vụ trả phí nào. GuardDuty (sau 01/12), Security Hub / Inspector / Macie chạy thử 1 lần rồi tự tắt (S296), DNS Firewall: đã duyệt, ghi ở AA-873.
- Máy agent: gh bỏ `admin:org`; break-glass `adventure365` đăng xuất khỏi gh; token MCP GitHub ra khỏi `~/.zshrc` (file 600). GitHub: gỡ Vercel App.
- Drive: 4 template Excel (T02/T06/T07/T08) chỉ còn USD.

## Bằng chứng verify

- DB-01 live (host portal): `/api/tenant/v1/tours/{id}/full` 404, `/api/tenant/v1/tours/{id}` 404, `/openapi.json` 404, `/v1/billing` + `/v1/tours/pool` 401. CIS `/health` `dd1a441d`, CRM web `/healthz` `7a972268`.
- Đếm live trước khi sửa (aggregate): 919/944 tour live có `provider` (60 giá trị khác nhau), 668 có `price_raw`, 2 có `supplier_id`. Chưa có đại lý thật nên không lộ thực tế.
- Test: CIS 912 unit + 17 integration; Partner 90+ test matcher + e2e smoke; 2 review độc lập + probe lách đường dẫn.
- ECS 8/8 COMPLETED, revision chạy = revision mới nhất; `shared.job` 0 active, 0 wave mở.

## Quyết định của Nghiệp (chính)

- Q1: không thu tiền / không dữ liệu thật trước khi luật sư duyệt hợp đồng. Q3/Q4 GuardDuty + Backup đã gật; 27/11 đổi: **GuardDuty bật cùng bước Organizations sau 01/12**.
- Key LLM **không xoay đợt này**; cần nhắc lịch tự động cho mọi khoá kể cả bên thứ ba (N1).
- Q9 CRM web base=1: bật đúng ngày go-live pilot. Q14: giữ D5 (không pentest), sửa 4 câu trước khi gửi DPA, SHIP xin sau 01/12, xét lại pentest khi đại lý lớn/EU yêu cầu hoặc trước prod.
- Trang bán hàng: duyệt hết com-1…9, **chỉ tiếng Anh, chỉ USD**. Toàn hệ thống **chỉ USD** (AA-1191).
- VPC endpoint (~96 USD/tháng) bỏ; thu hẹp egress, vá NAT, lọc tên miền trên NAT, DNS Firewall: duyệt.
- Security Hub / Inspector / Macie: chạy thử 1 lần, tắt ngay.
- Well-Architected: ghi vào WA Tool + sổ báo cáo, lịch hằng năm; tạo AA-1193/1194/1195.
- Việc của chị Thư (họp, TrueIDC, trần Anthropic, hạn mức OpenAI): tech lead tự làm, **không nhắc**.

## Còn lại

- 4 thẻ "Ask AA (chi tiết)": tech lead duyệt cuối phiên (58/58 quyết định). Jira PR-23 đã đăng (10711).
- S296 theo master plan: AA-1182 (khoá state, trần vendor), AA-1183 (sổ secret + nhắc tự động), AA-1185 (sweep 0 USD + egress + EBS encryption + Access Analyzer CI + Health), AA-1187, AA-1190 (My work lát 1), AA-873 chạy thử Security Hub/Inspector/Macie, Prowler, AA-1166.
- ≥ 28/11: chuỗi AA-1061 (bk-076) sau khi tech lead duyệt pins DRY RUN.
- 30/11: kéo Cost Explorer acc2 tháng 11. 01/12: Billing Transfer acc2 → acc4, rồi GuardDuty + SCP/RCP.
- Cắt allow-list quyền agent (agent soạn, tech lead áp) — AA-1182.

## Lưu ý kỹ thuật cho phiên sau

- Báo cáo định kỳ phải vào `docs/reports/catalog.yaml` (+ bản chép CIS), `/admin/docs` không hiện `docs/audits`.
- Lệnh `! ...` tech lead gửi giữa lượt (VSCode) không chạy: luôn kiểm lại bằng lệnh đọc.
- WA Tool: mô tả workload ≤ 250 ký tự; SaaS Lens không có trong `list-lenses` nhưng `get-lens --lens-alias softwareasaservice` có; script nhập câu trả lời (`apply.py`, `build_answers.py`, `answers.json`) lưu ở kho ISMS, thư mục `2026-11-27-S295-well-architected/watool/`, dùng lại cho lần review sau.
- `gh auth refresh` trên WSL mở Chrome WSL có thể đang đăng nhập tài khoản khác.
