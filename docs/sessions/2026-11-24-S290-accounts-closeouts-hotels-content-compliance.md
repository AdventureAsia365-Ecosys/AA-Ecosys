# S290 — 24/11/2026 — tài khoản chủ DN + Trang, đóng In Review, khách sạn allotment, Content workspace, bằng chứng compliance niêm phong

**Tác nhân:** Claude Code (VS Code/WSL, Ultracode). 24/11 ~12:00 → ~18:30 +07, cùng ngày sau S289. MFA aa365-admin làm
mới một lần (hết hạn 18:55); một cửa sổ tắt auto mode ~16:2x cho 2 secret repo của AA-1173. Lane code song song (a AA-1153,
b AA-1148, c guards, d AA-1173, e A10e-6, f AA-1177, g follow-up S289) + lane live check đóng In Review; mỗi lane qua review
độc lập + re-review approve trước merge.

## Trạng thái

- **Done (7):** AA-1177 (nhắc hợp đồng NCC sắp hết hạn: ô My work, trang NCC, e-mail mỗi hợp đồng; issue mới trong phiên theo Jira PR-31), AA-1149 (tour bán → 10 booking NCC, kiểm can-operate, ngoại lệ bán), AA-1176 (owner E2E Dev), AA-1175 (bậc số
  khách qua hai người), AA-1152 (add-on theo ngày tới lead đại lý + báo giá CRM), AA-1153 (khách sạn qua nhiều DMC, phần 2
  allotment + Excel hai chiều), AA-1160 (lead dự phòng e-mail + planner vi).
- **In Review (3):** AA-1148 Content workspace (ship + live; còn publish hai người), AA-1173 compliance phase 2–3 (bằng chứng
  niêm phong Object Lock live; còn maker-checker ngoại lệ, review tháng đầu, GitHub App chỉ đọc), AA-1158 (mọi probe agent
  PASS kể cả ciphertext; còn chủ DN duyệt TK ngân hàng SUP-000019 → khoá chi 24 h).
- AA-1177: bk-074 áp sau khi recompute platform (do trash tour tay SYNTHETIC) xong; Booking #325 29407508 + root #985 deploy; live: job r1 gửi 21 e-mail (7 người nhận × 3 hợp đồng SYNTHETIC, 0 bị từ chối), 1 thông báo; r2 không gửi gì.
- AA-1155 vẫn In Review: info@ đã có vai trò Booking tuỳ chỉnh; T12 đóng khi hai người đăng nhập lần đầu.
- Guard đỏ đầu phiên (Secret Scan full history root + Infra, Catalogue) → xanh, không có secret mới.
- C4.3 tuần W48 xong. Lượt LLM trả phí duy nhất: T2 cho AA-1152 = **0,1481 USD** (cap 0,50).
- Snapshot: [state-snapshot](../audits/2026-11-24-S290-session/state-snapshot.md).

## Quyết định của Nghiệp

- Đầu phiên: duyệt danh sách 8 việc (tài khoản, AA-1153 phần 2, đóng In Review, guard đỏ, AA-1173, AA-1148, follow-up S289 +
  C4.3 W48, Jira gộp S289 + S290).
- Chị Thư là chủ doanh nghiệp, làm được cả content + booking (preset Business owner đã gồm).
- Trang dùng hộp thư info@, vai Content + Contracting + Sales (Booking `custom_product_ops_accounting`, không quyền duyệt).
- Chị Thư và Trang được nhập **dữ liệu kinh doanh thật** trên Dev (nhà cung cấp, khách sạn, giá, hoạt động), trừ dữ liệu cá
  nhân (khách / traveller thật); số tài khoản ngân hàng thật để sau prod.
- Đóng In Review: duyệt **D1** (gắn tạm `booking-contracting` cho E2E pricing maker, 13:18, gỡ khi dọn), **D2/D3 = A10e-6**
  (E2E pricing checker duyệt đổi bậc của owner E2E; maker nhập + checker duyệt hoá đơn SYNTHETIC), **D4** (1 lượt T2 trả phí
  ≤ 0,50 USD), **D5** (tenant SYNTHETIC cho AA-1160: E2E Lead Proof Travel, bước 1–4), D0 tour giả lập = key catalogue chưa
  đại lý nào dùng + dòng thương mại SYNTHETIC + trả nguyên.
- Key Anthropic cũ (tháng 4, trong lịch sử Infra) **đã được thay bằng key tháng 10** — không hỏi lại.
- 16:2x: các bước của chủ DN (đăng nhập lần đầu → Make business owner → duyệt TK ngân hàng SUP-000019 → AA-1158) gom vào
  **buổi gặp thứ Năm 26/11**.
- ~16:2x: một cửa sổ tắt auto mode để đặt 2 secret `COMPLIANCE_EVIDENCE_*` ở root + Infra.
- Xoá 22 snapshot RDS `pre-s1-*` (tháng 10), **giữ `db-migrate-tp-018`**.
- 16:5x: tạo **AA-1177** (PR-31, chị Thư thêm 24/11 10:03: nhắc admin khi giá NCC gần hết hạn) và làm luôn trong phiên.
- "cứ làm bình thường, hết MFA thì kêu nhập mới".

## Thay đổi Codebase (merged)

- **Tài khoản + dữ liệu thật** — root #976 `e975c991` (runbook: Dev cho phép dữ liệu kinh doanh AA thật, dữ liệu cá nhân
  vẫn bịa).
- **Guard đỏ** — root #977 `fd8b752d` + Infra #999 `12dc7c29` (giữ pin gitleaks trước rewrite S287, guard chặn mất pin); root
  #978 `4f0916bb` (làm mới snapshot Catalogue surface, khối docs).
- **A10e-6 (D2/D3)** — root #979 `c779431c` (ADR 0006a A10e-6); Booking #319 `32a49292`.
- **AA-1153 phần 2** — Booking #320 (bk-072) `5683eb41`, #321 `0182e15c` (allotment / free sale theo DMC, Excel hai chiều,
  nhãn DMC đúng trên danh sách on-request); Infra #1000 copy; root #980 `113738f0` (guide giá).
- **AA-1158 ciphertext** — Infra #1001 `ecb0e7db` (run-script chỉ đọc chứng minh TK ngân hàng là ciphertext).
- **AA-1148 Content workspace** — Booking #322 (bk-073) `4ca6154b`, #323 `400d07c8` (category dmc, view NCC chỉ đọc cho CIS);
  Infra #1003 copy, #1004 `53e43d74` (grant `booking.v_supply_suppliers` cho `cis_app`); CIS #1663 (478) `cf90a9a3`, #1664
  `161deddd`, sửa live #1666 `dc8bbf15` (tour tay có dòng `pipeline_runs` riêng, hết 500 FK); Infra #1005 copy 478; root #984
  `8efaa52c` (contract `supply.supplier.v1`, ownership, runbook CIS admin).
- **AA-1173 compliance phase 2–3** — root #982 `926cdbc6` (niêm phong bằng chứng hằng ngày, dòng retention); Infra #1002
  `306da64b` (bucket Object Lock GOVERNANCE 365 ngày, role `aa-cis-dev-compliance-evidence`, `compliance-aws.yml` + Prowler);
  CIS #1665 (479) `b4aa82e1`, #1667 `5a9f52d0` (đọc bundle niêm phong, job kiểm DB hằng ngày, ngoại lệ maker-checker, review
  tháng); Infra #1006 copy 479.
- **AA-1177** — Booking #324 (bk-074) `74b5c041` (vai nhận e-mail = tham số Pricing policy), Infra #1008 copy. Mở lúc viết
  nháp: Booking #325 (e-mail mỗi hợp đồng, ô My work, danh sách sắp hết hạn trên trang NCC), root #985 (guide EN/VI).
- **Follow-up S289 (lane g)** — CIS #1668 `f06e3001` (401 kiểm phiên tách khỏi tỉ lệ 4xx trang status), Partner #386
  `1591609a` (kéo entitlement CRM bỏ tenant CIS không còn), Infra #1007 `d7e979da` (`PII_ALLOWLIST` bk-069 / bk-070),
  TripPlanner #299 `1b8502c` (403 cho mã chuyến tenant khác dưới phiên mới; tiêu đề route finder vi); root #986 `5909372e`
  (implementation note).
- **Docs sinh tự động** — root #983 `187621fa` (alarms, network, inventory, IAM, env config).

## Thay đổi Hạ tầng / dữ liệu Dev

- Migration áp Dev (DB Migrate): bk-072, bk-073, bk-074, CIS 478, CIS 479.
- ECS (revision đang chạy = mới nhất): cis-api :1271 / worker :840 / admin :97 (f06e3001), booking-api :174 / admin :65 (29407508), crm-api :216 (1591609a), crm-web :189 (28b1c4f6), tp-web :27 (1b8502c3). Migration mới nhất: CIS 479, bk-074, crm-087, tp-037. shared.job 0 lúc chốt.
- Terraform Apply (dev) run 45357390166: bucket bằng chứng Object Lock (GOVERNANCE, 365 ngày) + role compliance-evidence
  (< 0,05 USD/tháng). 2 secret repo `COMPLIANCE_EVIDENCE_ROLE_ARN` / `_BUCKET` ở root + Infra (09:22Z).
- RDS: xoá 22 snapshot thủ công `aa-cis-dev-db-pre-s1-*` (24–25/10); còn `db-migrate-tp-018-…` theo quyết định (kiểm 18:0x:
  không còn snapshot `pre-s1-*`).
- Cognito / Booking staff: info@ (Trang) → Booking `custom_product_ops_accounting`, nhóm `booking-custom` (12:26); gửi lại lời
  mời chị Thư + info@ (job succeeded 12:29). E2E pricing maker gắn `booking-contracting` 13:18 (D1), đã gỡ 17:33
  close-out.
- Dữ liệu SYNTHETIC còn trên Dev (dọn sau AA-1158): SUP-000018/19, HTL-000008/9, SVC-000018/19, 2 hợp đồng published, plan
  Thái 5 ngày `cbfc127e-…` sellable có 10 thành phần + ghi chú SYNTHETIC, TC-000040 (10 booking NCC) + TC-000041, TK ngân hàng
  pending trên SUP-000019, BIL-000002…004. Đã dọn: TC-000042…047 huỷ, hợp đồng c2/c3 expired, ngoại lệ bán revoked, billing
  entity `SYN-S290` + NCC probe deactivated, ngoại lệ compliance `SYNTHETIC-S290-AA1173-PROBE` revoked, tour tay SYNTHETIC
  trashed, locale `pilot-rehearsal-01` về en.
- Tenant: `pilot-rehearsal-01` adopt tour HCMC (T2 job `0a2d5f33`, 0,1481 USD); E2E Lead Proof Travel gắn crm.core (onboarding
  CRM lỗi 403 `missing_group` có chủ đích → không có CRM agency) + route lead e-mail, owner E2E được mời và đã nhận.
- Pricing policy: v3 bậc 5–6 / 7–10 rồi trả về v4 (= v2: 1, 2, 3, 4, 5–7, 8–10, 11+) — đang dùng v4.

## Bằng chứng verify

- Thư mục: `docs/audits/2026-11-24-S290-session/live/closeouts/evidence.md` (§4–§7, AA-1153, AA-1148) và
  `live/aa-1173/evidence.md`; C4.3: `c43-w48/README.md`.
- **AA-1149 / AA-1176:** 108 PASS / 1 FAIL (lỗi thiết kế test, đã tách bước). Generate tạo 10 booking (SUP-000018 ×4 đêm,
  SUP-000019 ×5 transfer + 1 guide); sửa tour rồi Generate → 0 mới, 10 cũ giữ nguyên; thiếu đêm 2 → bán B2B 422 (N1); ngoại lệ
  14 ngày → TC-000041 201; revoke → blocked lại; thiếu transfer chỉ cảnh báo (N4).
- **AA-1175:** v3 đề xuất → owner tự duyệt 403 `own_row` → checker duyệt; tariff 6 → 5–6, 9 → 7–10; trả về v4 qua người thứ
  hai, 5–7 tính giá 5 khách, 8–10 giá 8 khách; audit đủ.
- **AA-1152:** planner đại lý hiện 5 add-on SYNTHETIC "From $X" (45/50/60/65/75); lead → CRM `sent` kèm ghi chú `sv:`; thêm AA
  add-on vào proposal 201 (90 USD cho 2).
- **AA-1160:** lead `sent` qua kênh e-mail; trang Trip planner leads của đại lý ghi `delivered`, "NOW: E-MAIL"; planner vi ở
  1440/390. `tp_lead_pull_summary` skipped_agency=4 không đổi trước/sau (4 thuộc tenant khác).
- **AA-1153 phần 2:** desk ghi đúng DMC B (SUP-000017); allotment 2 phòng / release 7 ngày: 3 phòng → on_request, 2 →
  confirmed, trong 7 ngày → on_request (released); Excel 80 → 84 diff +5 %, giá mới thắng (103,90 → 109,10); allotment không
  nhân đôi.
- **AA-1158:** người viết hợp đồng không publish được (403); sellable không giá duyệt 409; NCC tự kích hoạt 403; hoá đơn
  maker/checker, người duyệt không ghi chi (403); chi khi TK pending 409 `bank_account_pending`; billing entity đổi text chờ
  duyệt; ciphertext tại DB `ciphertext_at_rest=true` (run 45352277094: 2 dòng AES-256-GCM, 0 cột giống plaintext).
- **AA-1148:** options/picker/Supplier links PASS; tạo tour tay 201 sau #1666; completeness 85 % → 100 %; publish 409
  `required_missing` rồi `revalidate_required`; drawer raw 409 `manual_tour_use_workspace`; Supplier links 917 tour chưa nối, gợi
  ý 0 (DRY RUN); trash 200.
- **AA-1173:** run root 45364700766 + Infra 45364721985 ghi bundle niêm phong; 4 kiểu xoá/ghi đè (kể cả
  `--bypass-governance-retention`) AccessDenied, object khoá tới 2027-11-24; trang CIS: root_daily 17 dòng, aws_nightly 11
  dòng, docs-reader `superseded`; ngoại lệ SYNTHETIC đề xuất → rút; tab Reviews 0 (đúng); 5 setting mới.
- **C4.3 W48:** tenant read p95 ~155 ms (> 150, tuần trượt đầu, `REQUEST_TOURS_SQL` tour_liveness; W49 quyết định); AA-1107
  places 536 → ~140 ms; anomaly breaker baseline 145 ms + ~3 GB temp/tuần; CRM 35 % thời gian DB (proposal lookup ~1/s),
  8.927/9.888 entry `pg_stat_statements` là `crm_app`; season-sync Booking đọc lại plan không có điểm đến.

## Jira

Đã đăng 8/8 sau khi Nghiệp duyệt ("Duyệt hết", ~19:10): PR-27 10691, PR-25 10692, PR-30 10693, PR-31 10698, PR-29 10694, PR-24 10695, PR-26 10696, PR-22 10697 (27 ảnh nhúng; ảnh PR-31 chụp lại vì 2 ảnh nháp trùng nhau). Gộp cả nháp S289. Subagent bị hook chặn ghi Jira nên điều phối tự đăng. Bản lưu: `docs/audits/2026-11-24-S290-session/jira-drafts.md`.

Nháp gộp S289 + S290 (7 nháp J1–J7: PR-27, PR-25, PR-30, PR-31, PR-29, PR-24, PR-26):
`docs/audits/2026-11-24-S290-session/jira-drafts.md`.

## Việc đầu phiên sau (S291)

1. Follow-up nhỏ của S290 (danh sách ở backlog §5): ẩn tour tay khỏi Upload › Tours Ready for Rewrite; trash tour tay chưa publish không kích hoạt recompute platform; AA-1177 minor (bỏ data.mail khỏi API thông báo, ghi mail theo từng lần gửi).
2. Thứ Năm 26/11 (buổi với chủ DN): đăng nhập lần đầu → Make business owner → chủ DN duyệt TK ngân hàng SYNTHETIC SUP-000019 →
   agent thử chi trong 24 h → 409 `bank_payout_locked` (AA-1158); bật hai công tắc hai người + người thứ hai thật cho publish
   AA-1148 và ngoại lệ AA-1173; review bảo mật tháng đầu; Trang đăng nhập info@ (AA-1155 T12).
3. Sau AA-1158: dọn dữ liệu SYNTHETIC close-out S290 (README §9 của `.tmp-session/S290/closeouts/`; nhóm `booking-contracting` của E2E pricing maker
   đã gỡ 17:33).
4. AA-1136 đọc kết quả một tuần hook (~26/11); follow-up nhỏ (mục Còn lại).
5. Slot kế: AA-1154, AA-1141, AA-1119, AA-1103, AA-1142, AA-1118.

## Còn lại

- AA-1148: publish hai người end to end (công tắc `cis.content.publish_two_person` tắt trên Dev, cần người thứ hai thật).
- AA-1173: maker-checker ngoại lệ (cần `cis.settings.two_person_approval` + người thứ hai), review tháng đầu (tech lead), GitHub
  App chỉ đọc (bước tay trong implementation notes AA-1173), lượt Prowler tuần đầu; phase 3 (upload tay, risk register, SoA,
  CSV) là follow-up.
- AA-1158: chủ DN duyệt TK SUP-000019 → khoá chi 24 h; tự duyệt của chủ DN có đánh dấu.
- Follow-up (không tạo issue Linear):
  - Upload › "Tours Ready for Rewrite" liệt kê tour tay chưa từng publish (có nút Rewrite) → ẩn hoặc gắn nhãn "Content workspace".
  - Trash một tour tay chưa từng publish kích hoạt recompute phạm vi platform (~50 phút, chặn DB Migrate apply bk-074).
  - AA-1177 minor: bỏ `data.mail` khỏi API notifications (lộ khoá staff cho mọi người đọc queue); ghi mail theo từng lần gửi
    (tránh gửi lại cả hợp đồng khi lỗi giữa chừng).
  - AA-1153 minor: diff import chưa có phần Inventory (thu hẹp allotment không báo); base diff có thể chọn nhầm hợp đồng cùng
    DMC cùng ngày bắt đầu; `taken` hơi thận trọng trong một lượt `many()`.
  - `skipped_agency=4` của các tenant khác trong `tp_lead_pull_summary`.
  - Tab Suppliers ghi booking sinh từ tour là "extra item".
  - Alarm tuổi bản copy RDS vẫn đỏ vì giữ snapshot tp-018.
  - C4.3: `REQUEST_TOURS_SQL` (W49 quyết), baseline anomaly breaker sargable, CRM proposal poll + job retention `DELETE`,
    churn `pg_stat_statements`, season-sync nhớ kết quả mỗi plan.
  - AA-1152: drawer add-on CRM nên đòi đúng tour có nơi của add-on.
- Từ trước vẫn chờ người: AA-1157 (H0–H6 view-as), AA-1172 bật/tắt guard dữ kiện T9, AA-1174 chấp nhận "not met" trên Dev,
  AA-1111 TOTP chủ DN, AA-1110 (≥01/12), AA-1122 lượt DFS tự động 01/12.

## Lưu ý kỹ thuật cho phiên sau

- Phiên E2E (Cognito) sống ~1 giờ: live check dài phải đăng nhập lại giữa chừng.
- Hai công tắc hai người đang TẮT trên Dev: `cis.content.publish_two_person`, `cis.settings.two_person_approval` — khi tắt,
  người đề xuất ngoại lệ compliance tự duyệt được (ghi `self_approved`), nên live check không gửi lệnh tự duyệt.
- Secret Scan full history quét cả ref PR cũ sau rewrite: giữ pin gitleaks trước rewrite; guard mới chặn baseline mất pin.
- Không merge/apply khi job recompute platform đang chạy (deploy giữa chừng làm job bị nhả và chạy lại).
- Đề xuất ngoại lệ compliance không trả `id` trong response — lấy id từ danh sách.
- Bài học chi tiết đã chuyển vào `skill/aa-lessons/lessons.md` (5 dòng S290).

## Session block cho memory Notion

```
## S290 (24/11/2026, Claude Code — VS Code/WSL): tài khoản chủ DN + Trang, đóng In Review, khách sạn allotment, Content workspace, compliance niêm phong
**Quyết định của Nghiệp** — duyệt 8 việc; chị Thư = chủ DN (content + booking); Trang dùng info@, vai Content + Contracting + Sales; Dev được nhập dữ liệu kinh doanh thật trừ dữ liệu cá nhân (TK ngân hàng thật sau prod); D0–D5 đóng In Review + A10e-6 (D1 gắn tạm booking-contracting cho E2E pricing maker); T2 trả phí ≤ 0,50 USD; key Anthropic đã thay tháng 10 — không hỏi lại; bước chủ DN gom vào buổi thứ Năm 26/11; một cửa sổ tắt auto mode (2 secret compliance); xoá 22 snapshot pre-S1, giữ tp-018; tạo AA-1177 và làm trong phiên; "cứ làm bình thường, hết MFA thì kêu nhập mới".
**Kết quả chính** — Done: AA-1149, AA-1176 (Generate 10 booking NCC, N1 chặn/ngoại lệ/revoke), AA-1175 (bậc qua hai người, v4 = v2), AA-1152 (add-on → lead CRM sv: → AA add-on; T2 0,1481 USD), AA-1153 (Booking #320 bk-072, #321; allotment/release, Excel 80→84), AA-1160 (lead dự phòng e-mail delivered, planner vi), AA-1177 (Booking #324 bk-074, #325, root #985; job thật gửi 21 thông báo, chạy lần 2 gửi 0). In Review: AA-1148 (Booking #322/#323 bk-073, CIS #1663 478/#1664/#1666, Infra #1004, root #984; còn publish hai người), AA-1173 (root #982, Infra #1002 Object Lock, CIS #1665 479/#1667; xoá/ghi đè AccessDenied), AA-1158 (mọi probe agent PASS + ciphertext Infra #1001; còn chủ DN duyệt TK SUP-000019). Guard đỏ xanh (root #977/#978, Infra #999). A10e-6 (root #979, Booking #319). Follow-up S289 (CIS #1668, Partner #386, Infra #1007, TP #299). C4.3 W48: tenant read p95 ~155 ms (trượt tuần 1).
**Trạng thái kiểm cuối phiên** — ECS 8/8 1/1: cis-api :1271 / worker :840 / admin :97 (f06e3001), booking-api :174 / admin :65 (29407508), crm-api :216 (1591609a), crm-web :189 (28b1c4f6), tp-web :27 (1b8502c3). Migration CIS 479, bk-074, crm-087, tp-037 (áp trong phiên: bk-072/073/074, CIS 478/479). shared.job 0. Bucket bằng chứng Object Lock + role compliance-evidence (Terraform CI apply). Xoá 22 snapshot pre-S1, giữ tp-018. Jira: 8/8 đã đăng (PR-22, 24, 25, 26, 27, 29, 30, 31).
**Việc cần làm đầu phiên sau (S291)** — (1) thứ Năm 26/11 với chủ DN: đăng nhập → Make business owner → duyệt TK SUP-000019 → thử chi 24 h 409 (AA-1158); bật công tắc hai người + người thứ hai thật (AA-1148 publish, AA-1173 ngoại lệ); review bảo mật tháng đầu; Trang đăng nhập info@; (2) dọn dữ liệu SYNTHETIC close-out S290 sau AA-1158; (3) AA-1136 readout ~26/11; (4) slot AA-1154 / AA-1141 / AA-1119.
**Lưu ý kỹ thuật** — phiên E2E sống ~1 giờ; hai công tắc hai người đang tắt trên Dev; Secret Scan full history quét ref PR cũ → giữ pin trước rewrite; trash tour tay chưa publish kích hoạt recompute platform ~50 phút chặn DB Migrate; lane song song phải có migStart khác nhau cho mọi owner có thể chạm.
```
