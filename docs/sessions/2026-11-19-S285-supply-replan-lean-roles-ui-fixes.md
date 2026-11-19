# S285 — 19/11/2026 — quyết định nguồn cung + kế hoạch phân quyền gọn, sửa UI 4 app, nhãn golden AA-1051

**Tác nhân:** Claude Code (VS Code/WSL, Ultracode). ~06:15 → ~23:30 +07. Đổi tài khoản claude.ai nhiều lần (lane resume).
**Sự cố:** WSL sập vì hết RAM lúc 17:16 (3 lane code + workflow panel 78 agent + Playwright + ship_wave cùng lúc). Khôi
phục: lane chạy lại bằng resume, workflow resume từ cache, không mất việc nào đã làm. Luật mới: tối đa 2 lane code + 1
workflow nhẹ, kiểm RAM trống (`free -m`) trước mỗi lần mở.

## Trạng thái

Done có bằng chứng live (Linear): AA-1130, AA-1138, AA-1128, AA-1129, AA-1143, AA-1126, AA-1144, AA-1139.
In Review / còn mở có tiến độ: AA-1127, AA-1111, AA-1136, AA-1137, AA-1110, AA-1134, AA-1145, AA-1146, AA-1051 (In
Progress). Kế hoạch lại (tech lead duyệt Q1–Q12): milestone M-ROLES, issue mới AA-1155…AA-1159, AA-1150 thu hẹp thành
bước 1, AA-1121 gộp vào AA-1103; AA-1160 tạo từ quyết định E5 buổi tối. Issue tạo giữa phiên cho kế hoạch nguồn cung
(M-SUP): AA-1143…AA-1154. Số liệu hạ tầng: [state-snapshot](../audits/2026-11-19-S285-session/state-snapshot.md).

## Thay đổi Codebase (merged)

- **AA-1130** — TripPlanner #282 `0d626f61` (trang planner đại lý theo audit UI S283), deploy Lambda + web.
- **AA-1129** — Partner #349 (dịch, client host, Academy) + #350 (Needs you, tên thành viên, inbox) + các PR lane l10 / l18
  (nhật ký truy cập bằng câu dễ đọc, 2.050 dòng, 0 id hex).
- **AA-1138** — root #882 `6a7000de` (ecsx tự giảm chunk đọc output, tắt Sentry cho script ecsx), Partner #354 `8f255db6`
  (crm-078, `crm_draft_reply` sang Claude Haiku 5.5), Infra #921 (trần acc1 cho CRM).
- **AA-1128** — Booking #277 `eb093350`, #278 `31719fae`, #279 `bb7bab6a`, #280 (trang staff Booking tiếng Việt + B0).
- **AA-1143** — root #890 `233b56e0`, CIS #1596 (455–456), Partner #356 (crm-079) + 3 PR khác (6 PR); copy ngân sách AI sang
  CRM.
- **AA-1144** — root #895, Partner #358 (crm-080) + #359, CIS #1605 + Partner #365 (khoá sự thật T2: đại lý chỉ còn dòng
  vé máy bay / visa / bảo hiểm / phí; tên mục của AA bị khoá).
- **AA-1145** — root #893, Booking #281 (bk-060) + #282 (mô hình nguồn cung chung, luật dừng bán R6).
- **AA-1146** — phần 1 (D1, D5, CIS 457–458): sửa tour có phiên bản, khoá, một cổng duyệt.
- **AA-1127** — CIS #1594, #1604 (sửa 5 chỗ tràn ngang 390 px).
- **AA-1111** — Booking #286 `e329c9eb` (công tắc bắt buộc MFA admin), TripPlanner #286, Infra #934, crm-082.
- **AA-1139** — TripPlanner #288 `1498c1ab` (tp-035) + Partner #366 `1f7d1cf9` (module TripPlanner trong CRM web và Content
  studio).
- **AA-1136 / AA-1137** — root #885 `6ca6f982` (hooks log mode, p95 79 ms), root #884 `9b494bdb` (Spec trace), TripPlanner
  #286 (caller).
- **AA-1051** — CIS #1591, #1593 `c86f6b22` (đăng ký T9), #1606 (null gate mang theo golden), #1607 (soạn lại prereg), #1609
  (CIS 460, trần T2 6,5 USD), #1610 `33e87ec7` (đo tỷ lệ fire a1); #1611 (đăng ký S1/T2) đang ship lúc ghi log.
- **Công cụ / CI** — root #881 `7757ff45` (vệ sinh CI WL8), #883 (ship_open_prs nhận base `origin/<branch>`), Infra #920
  (AA-1134), Infra #941 (copy CIS 460). Infra #926 / #927 đóng (trùng).

## Thay đổi Hạ tầng

- Migration áp trong phiên: CIS 455–460, bk-060–bk-061, crm-078–crm-082, tp-035.
- Terraform: Infra #921 (acc1, chạy với credential tạm), #934 (MFA admin), apply hai lần cho AA-1139 (lần thứ hai mới gán
  scope `tripplanner.leads/manage` cho client M2M của CRM); Terraform Apply Dev cuối 14:47Z success.
- Cấu hình: công tắc bắt buộc MFA admin **CRM = On**, **CIS = Off**, **Booking = Off** (chờ business owner đăng ký TOTP);
  Infra #935 (bỏ luật WAF geo cho host staff) **mở có chủ đích**.
- Tiền AI: connection `openai-direct` trần tháng 11 nâng 10 → **25 USD** (trả về 10 ngày 01/12); CRM `crm_draft_reply` trần
  5 USD/tháng (CIS 150 → 145).
- Dữ liệu Dev: key v1 TripPlanner trên một tenant giả (AA-1139); AI agency giả bật cho AA-1138 rồi tắt lại; override quota
  AA-1126 đã gỡ.
- Key IAM cũ của AA-1111 đã xoá (chỉ còn key mới 17/11).

## Trạng thái kiểm cuối phiên (snapshot 22:44 +07)

- ECS 8 service COMPLETED 1/1, revision mới nhất = revision đang chạy: CIS api :1229 / worker :798 cùng `33e87ec7`, CIS admin
  :73 `dda98445`, Booking api :151 + admin :45 `e329c9eb`, CRM api :208 + web :180 `1f7d1cf9`, TripPlanner web :21
  `0d626f61`; Lambda browse / assembly cùng CodeSha256 (TP `1498c1ab`).
- Migration: CIS **460**, Booking **bk-061**, CRM **crm-082**, TripPlanner **tp-035**; không có PR `bot/db-schema-reference`
  mở.
- Lệch ghi nhận: Partner **Deploy Web Dev đỏ** từ 01:14Z (deploy + verify thành công, chỉ "Studio UI smoke" trượt 1/69 —
  `aa761-account-pages.spec.ts:124` pager Activity; nghi từ Partner #349/#350); Infra **Terraform Drift 14:38Z đỏ** (chưa có
  run drift sau apply 14:47Z); CIS #1586 (dependabot) đỏ 4 check.
- Bảng job và giá trị DB (trần connection, công tắc MFA) không nằm trong snapshot; điều phối tự kiểm.

## Bằng chứng verify

- AA-1143: tech lead bấm "Send to CRM" 17:23 → CIS POST 200 + CRM PUT 200, dòng audit khớp `crm_copy`, in_sync 8/8.
- AA-1126: ảnh thông báo quota ở 3 app; đường hết lượt AI của TripPlanner live (`tenant_sessions_cap` → outbox → chuông
  studio 18:02); override đã gỡ.
- AA-1144: sửa "seven-day" thành "ten-day" và thêm "flights included" → 422; studio lưu vẫn giữ trường riêng; `/tours/mine`
  404; re-check 6/6 PASS, tour trả về v6 (v9).
- AA-1139: route module TripPlanner trong CRM web và Content studio 200 sau lần apply thứ hai; key v1 trên tenant giả.
- AA-1127: 390 px 12/12 PASS nền sáng + tối (CIS #1604 live).
- AA-1138: Nova Lite 10/10 ok (0,00176 USD), chấm mù Haiku 7 / Nova 3; nháp thật Haiku 5.5 @acc1 0,000321 USD.
- AA-1130: API live đạt, 8 ảnh không còn chữ AA.
- Ảnh + JSON: [docs/audits/2026-11-19-S285-session/](../audits/2026-11-19-S285-session/).

## AA-1051 (W5 proofs)

- T9: job `167e485b` succeeded 2,83 USD (trần 15); verdict non_inferior (4,67 → 3,50 lỗi/tour); first_pass_yield 0,08 < 0,30
  trượt.
- Golden aa729 **1.7.0** đã import (218 mẫu: +22 S1, +48 T2; gate a1 26 / 25 dùng được, t2 20). Nhãn panel agent: S1 15 pass /
  7 fail ([aa1051-s1-labels](../audits/2026-11-19-S285-session/aa1051-s1-labels.md)), T2 27 pass / 21 fail
  ([aa1051-t2-labels](../audits/2026-11-19-S285-session/aa1051-t2-labels.md)); tranh chấp theo luật điều phối, tech lead chấp
  nhận (E4).
- Ứng viên T2 sinh 18/18 (0,882 USD). Tỷ lệ fire a1 đo 0,24 (0,28 USD). Judge trên nhãn 0,77 USD.
- DRY plan: S1 5,63 USD / trần 8, power 0,964; T2 5,98 USD / trần 6,5, power 0,95.
- Proof trả phí (tech lead duyệt chạy, 19/11 ~23:00): giám khảo GPT-6 Luna qua OpenAI API (ghim theo thước đo AA-1048 v7, không tự fallback — trả lời từ đường khác bị từ chối thành dòng lỗi), bên viết Claude Sonnet 5.5 qua Anthropic API.
  - CIS #1611 đăng ký w5-s1 / w5-t2 (status registered + lock); plan ready_for_live true, blocking [].
  - **S1 xong** (job 4c706730, 16:41Z → 18:33Z, run e76e1145): verdict **non_inferior** trên 25 cặp — lỗi/tour 11,16 →
    0,76 (cận trên −6,79 < biên 4); writer 0,062 USD/tour ≤ 0,065 đạt, hard_stops 0 đạt; serious_error_rate + day_loss
    còn pending. Sổ chi phí 3,11 USD (judge 1,40, s1_generate 1,65, grounding 0,07); item_fail_rate 0,44, first_pass_yield 0,56.
    Báo cáo: [w5-s1-report.json](../audits/2026-11-19-S285-session/aa1051/w5-s1-report.json).
  - **T2 xong** (job cb7afcc0, 18:35Z → 20:11Z, run dfdcb43d): verdict **non_inferior** trên 20 cặp nhưng sát biên — lỗi/tour
    8,3 → 7,7, cận trên 3,81 so với biên 4; writer 1 lượt/tour, 0,058 USD/tour, hard_stops 0 (ba mục đạt);
    enforce_findings_after_repair pending. item_fail_rate 1,0, first_pass_yield 0 (tour nào cũng còn ít nhất một claim
    lỗi). Sổ chi phí 2,50 USD (judge 1,40, t2_generate 1,08). Báo cáo:
    [w5-t2-report.json](../audits/2026-11-19-S285-session/aa1051/w5-t2-report.json).
  - Tổng hai proof 5,60 USD (trần 7,6 + 6,35). **Lệch phát hiện:** `shared.job.cost_usd` ghi đúng gấp đôi sổ chi phí
    (S1 6,22 so với 3,11; T2 4,99 so với 2,50) → bộ cộng chi phí job đếm hai lần, sửa ở S286.
- Sau đó trong phiên: CIS #1612 (CIS 461) + #1613 (Cost Explorer hằng ngày + nhãn số cũ) live `2e6070a6`; Partner #367 sửa smoke, Deploy Web Dev 88db5880 xanh lại; Infra #943 quy tắc bucket `audit-assets/` tự xoá sau 60 ngày (apply 16:38Z, kiểm live); tạo AA-1161 (giữ repo gọn, guard ảnh / file build / file chạy, viết lại lịch sử khi tech lead duyệt).

## Kế hoạch lại (M-ROLES) và tư vấn

- Tech lead duyệt Q1–Q12 ([plan-audit-roles-trang](../audits/2026-11-19-S285-session/plan-audit-roles-trang.md),
  [nháp issue](../audits/2026-11-19-S285-session/plan-audit-issue-drafts.md)): nhân viên content+ops làm Content trước, vào
  Booking bằng vai trò tuỳ chỉnh (không giao `contracting` tạm); Booking đọc vai trò tuỳ chỉnh qua contract view CIS
  (phương án A, bổ sung ADR 0006); My work hai nửa nối nhau; không editor vai trò CRM.
- Issue mới: AA-1155 (vai trò tuỳ chỉnh Booking + CIS), AA-1156 (CIS My work), AA-1157 (xem như vai trò thấp hơn), AA-1158
  (luật duyệt đội 3 người + tài khoản ngân hàng NCC), AA-1159 (Booking My work); AA-1150 → bước 1; AA-1121 → AA-1103; AA-1160
  (locale / theme TripPlanner + fallback lead) từ E5.
- Lịch: S286–S289 M-ROLES, M-SUP xong ~S290 (hết phiên dự phòng).
- Tư vấn trong thư mục audit: gateway AI + tên người dùng (13 quyết định), nguồn cung vòng 1–2 (32 quyết định, 5 nhóm + phản
  biện), vòng 3 (việc chờ duyệt, phân quyền xuyên app, vai trò T13), trang phân quyền toàn hệ (`access-map/`), trợ lý AI
  admin, ops overview v2, hoạt động tuỳ chọn, khách sạn, chỉnh nội dung tour.
- Trang quyết định đã publish (chỉ ghi tên): gateway + tên người dùng, nguồn cung, phân quyền + chi phí + việc chờ, vai trò
  gọn, kế hoạch lại, chi phí proof, quyết định buổi tối.

## Jira

Đã đăng sau khi tech lead duyệt ([nháp](../audits/2026-11-19-S285-session/jira-drafts.md)):

- Sáng: PR-30 comment 10672 (bảng dữ liệu khách sạn, nói rõ dữ liệu giả lập); tin Zalo PR-29 + PR-30 tech lead tự gửi.
- Vòng 2: PR-29 comment 10673, PR-30 comment 10674.
- Tối (~23:20, "đăng hết"): PR-23 10675, PR-24 10680 (lần đầu lỗi 400 vì bảng nằm trong list, đăng lại), PR-25 10677,
  PR-26 10678, PR-22 10679.
- Không có báo cáo tuần PR-20 tối nay: kỳ 6 (17–23/11) đến hạn cuối tuần.

## Quyết định của tech lead

- Duyệt danh sách S285; 13 quyết định gateway / tên người dùng (G5 làm luôn; G6 giữ 1 key Anthropic, hướng chính Bedrock; I4
  sửa: đại lý không ghi tên vào Cognito, staff Cognito `name` là gốc).
- PR-29 (business owner xác nhận): hoạt động tuỳ chọn có tính tiền theo địa điểm, gắn ngày lịch trình, chỉ hoạt động có NCC
  của AA, đại lý không sửa; 32 quyết định nguồn cung (31 + B2 bấm lại); trang phân quyền: 27 đồng ý, A8 không (giữ Done-when
  AA-1110).
- AA-1138: `crm_draft_reply` sang Claude Haiku 5.5, trần CRM 5 USD/tháng.
- AA-1051: chạy trả phí theo trần (T9 ≤ 15, S1 ≤ 8, T2 ≤ 6,5 USD); chấp nhận nhãn tranh chấp theo luật điều phối (E4).
- Trần `openai-direct` tháng 11 lên 25 USD, về 10 USD ngày 01/12.
- MFA admin: business owner đăng ký TOTP "để sau" — CIS / Booking giữ Off, không ảnh hưởng Dev; WAF geo bỏ cùng lúc bật MFA.
- Q1–Q12 kế hoạch lại; E2 (kiểm Cost Explorer hằng ngày) và E3 (dọn dữ liệu Dev) duyệt; E5 → AA-1160.
- acc3: hai case AWS đều Resolved nhưng 7 model vẫn bị từ chối (probe) → để nguyên, acc1 phục vụ mọi model.
- Tech lead tự làm B5: tắt quyền tạo repo của member + Infra env dev chỉ `main`; đăng mọi nháp Jira.

## Còn lại

- AA-1127: E2 (kiểm Cost Explorer hằng ngày) + E3 (dọn dữ liệu Dev) — lane l28 đang chạy, đã duyệt.
- AA-1111: CIS + Booking bật MFA admin khi business owner có TOTP; rồi merge + apply Infra #935.
- AA-1136: đọc kết quả một tuần log mode ~26/11. AA-1137: pilot spec trên AA-1155 ở S286.
- AA-1110: kênh cảnh báo thứ hai + người giữ khoá thứ hai ≥ 01/12. AA-1134, AA-1145, AA-1146: verify live rồi đóng.
- AA-1051: kết quả proof S1 + T2 và báo cáo (nếu chưa xong tối nay).
- Partner Studio UI smoke đỏ 1/69; Infra Terraform Drift đỏ; CIS #1586 dependabot đỏ.

## Việc cần làm đầu phiên sau (S286)

1. AA-1150 (bước 1: preset vai trò trên trang Staff, bỏ `content_creator`, finance đọc, tách quyền làm / duyệt) và AA-1156
   (CIS My work) — hai lane đầu, không đụng cùng file.
2. AA-1155 (vai trò tuỳ chỉnh) kèm pilot spec của AA-1137: PR Infra + migration CIS / bk-; phần CIS chỉ sau khi PR CIS của
   AA-1150 merge; apply khi cả 3 bảng job rảnh.
3. AA-1051: kết quả proof S1 + T2 + báo cáo nếu chưa xong trong S285.
4. AA-1127 E2 / E3: bước live (Cost Explorer hằng ngày, dọn dữ liệu Dev theo DRY RUN).
5. Business owner đăng ký TOTP khi rảnh → bật MFA admin CIS + Booking, merge + apply Infra #935.
6. Sửa Partner Studio UI smoke (`aa761-account-pages.spec.ts:124`) nếu chưa merge.
7. CIS dependabot #1586 (4 check đỏ).
8. Đóng có bằng chứng: AA-1145 (R6 live), AA-1146 phần 1, AA-1134; đọc lại Terraform Drift sau apply.

## Lưu ý kỹ thuật cho phiên sau

- Bài học S285 đã chuyển vào `skill/aa-lessons/lessons.md` (cùng root PR chốt phiên): số migration trùng giữa lane →
  `migStart` cho mọi owner + sổ giữ số; ship_open_prs mở lại PR đã squash-merge; hai lượt ship_wave trên cùng PR; ecsx dài
  chặn deploy CIS; merge PR Infra không tự apply; scope Cognito mới cần apply hai lần; Jira từ chối bảng trong `<li>`; zsh
  `echo ===`; WSL hết RAM.
- Skill `aa-session`: MFA chỉ báo khi thật sự hết hạn (không nhắc sớm).
- Sentry connector giữ registry cũ trong phiên → mở phiên mới để đọc issue.
- Root #860 (bot infra docs) vẫn mở; release PR tuần (CIS #1570, Booking #270, TP #278, Partner #343) và kit sync (Booking
  #276, Partner #355) mở theo lệ.
