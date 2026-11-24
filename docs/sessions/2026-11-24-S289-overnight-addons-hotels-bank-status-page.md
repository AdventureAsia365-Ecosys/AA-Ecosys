# S289 — 23→24/11/2026 — chạy qua đêm: hoạt động tuỳ chọn, khách sạn qua nhiều DMC, tài khoản ngân hàng NCC, trang Ecosystem status

**Tác nhân:** Claude Code (VS Code/WSL, Ultracode). 23/11 22:55 → 24/11 ~11:30 +07, chạy qua đêm khi Nghiệp vắng tới 07:00.
Chia 2 đợt tránh trần 5 giờ (chạm ~03:05, reset 03:50, resume 03:56 bằng `resumeFromRunId`, không mất việc) và OOM (tối đa
2 lane nặng, một `next build` mỗi lúc, watchdog RAM). MFA hết hạn 06:48 → 8 PR của AA-1152 nằm local tới khi Nghiệp nhập lại.

## Trạng thái

- **Done (2):** AA-1140 trang Ecosystem status (6/6 Done-when live), AA-1151 hoạt động tuỳ chọn (Done-when live đủ).
- **In Review (3):** AA-1152 (live 2/3, còn add-on đi theo lead), AA-1158 phần 2 (live 4/5 + kiểm ciphertext, chủ DN duyệt),
  AA-1160 (live màu/dark/Tenant 360 xong, còn lead dự phòng + ảnh locale vi).
- **In Progress (1):** AA-1153 phần 1 ship + live 3/4; phần 2 (allotment, Excel hai chiều) → S290.
- Mỗi lane qua 2 reviewer độc lập + 1 lượt sửa (~22 lỗi blocking/major sửa trước merge); lane h (quyết định sáng) 2 review approve.
- Không chạy lượt LLM trả phí; 5 job nháp nội dung CIS của AA-1151 ≤ 0,015 USD.
- Snapshot: [state-snapshot](../audits/2026-11-24-S289-session/state-snapshot.md).

## Quyết định của Nghiệp

- 23/11 tối: "lọc việc coding làm tới 7h"; "phân phối tránh limit 5h và OOM"; "xong sớm thì kéo thêm việc".
- 24/11 ~09:20:
  - #1 KMS: "chạy luôn" (một khoá dùng chung cho dữ liệu ngân hàng NCC).
  - #2 đồng ý cho agent tự làm: gắn lại nhóm `booking-contracting` cho tài khoản E2E pricing maker để kiểm (gỡ sau), mở
    allow-list E2E cho liên kết DMC thứ hai + báo giá SYNTHETIC (ADR 0006a A10e-5).
  - #3 ok chi phí CloudWatch (GetMetricData ~0,07 USD/ngày khi trang status mở).
  - #4 chỉ chủ DN duyệt tài khoản ngân hàng NCC (tech lead dự phòng).
- 24/11 ~09:35: "làm xong hết thì dừng phiên, nháp Jira chuyển phiên sau cùng ngày".

## Thay đổi Codebase (merged)

- **AA-1158 phần 2 — tài khoản ngân hàng NCC** — root #961 `17c3f5b1`; Infra #984 `de617246` (khoá KMS, quyền task role,
  biến môi trường); Booking #309 (bk-067) `5b9b45e7`, #311 `a84c4793` (mã hoá envelope, duyệt có gọi lại, khoá chi 24 h,
  hồ sơ NCC); sau quyết định #4: Booking #317 (bk-071, trigger chỉ chủ DN / tech lead duyệt) `3c71dccd`, #318 `094d678d`
  (403 `bank_approver_not_allowed`, allow-list E2E A10e-5); root #974 `0a8486a6` (ADR 0006a A10e-5).
- **AA-1151 — hoạt động tuỳ chọn** — root #960; Infra #983; CIS #1653 `96b76c34` (publish hai người cho nội dung cung
  ứng); Booking #310 (bk-068) `c5b46e82`, #313 `4cdfc718` (API offer, import danh mục, cảnh báo hợp đồng sắp hết, trang Add-ons).
- **AA-1153 phần 1 — khách sạn qua nhiều DMC** — root #964 `dee840f6`; Booking #312 (bk-069) `769bc2a8`, #314 `ef1cf756`
  (một DMC mỗi dòng phòng, so giá theo USD, board basis trên báo giá, giá trẻ em khách sạn, bảng giá có giới hạn dòng,
  board mặc định thành giá trị Policy).
- **AA-1152 — add-on theo ngày + giá đại lý làm tròn** — root #969 `c2b07a9e` (contract, ADR 0019 b5 amendment, DM-7.1);
  Booking #315 (bk-070) `aa625e10`, #316 `1c32a10d`; Partner #384 (crm-086) `4ee25a8e`, #385 (crm-087) `28b1c4f6`;
  TripPlanner #297 (tp-036/037) `da1b01f3`, #298 `12b6a4d2`; CIS #1659 (476) `4fc24809`.
- **AA-1160 — planner theo locale/theme đại lý + lead dự phòng** — root #966; CIS #1654 (474) `982232cc`, #1655 `f0324a70`;
  Infra #988, #989; TripPlanner #294 `fee1447a`, #296 `002b73a7` (accent tối của đại lý ở dark mode, tìm ra khi kiểm live);
  Partner #382 `e0cf2cd9`.
- **AA-1140 — trang Ecosystem status** — root #968; CIS #1656 (475) `69fb2ce9`, #1657 `eb85befc` (endpoint + job lấy mẫu
  5 phút), #1658 `ff86cb60` (trang), #1660 `3a0f604a` (headroom theo series, bấm chip nhanh, lý do health, ô số liệu);
  sau khi Nghiệp xem trang VI 09:51: CIS #1661 (477) `914380e8` (ngưỡng RDS trống theo % dung lượng cấp, 20 % / 10 %),
  #1662 `7b1c8afd` (lọc mã issue khỏi text ngoài, mục EN/VI, không cắt giữa chữ).
- **Nhỏ:** CIS #1652 `a773ebda` ghim 14 dòng `>=` cuối cùng của `requirements.txt` + guard ghim chính xác.
- Infra copy migration: #985–#987, #989–#998.

## Thay đổi Hạ tầng / dữ liệu Dev

- Migration áp Dev (DB Migrate): Booking bk-067, bk-068, bk-069, bk-070, bk-071; CIS 474, 475, 476, 477; CRM crm-086,
  crm-087; TripPlanner tp-036, tp-037.
- Khoá KMS `alias/aa-booking-dev-supplier-bank`: bootstrap IAM apply từ checkout main Infra (plan 0/2/0, 09:16); CI
  terraform-apply tạo khoá fail (lockout check, CI không được `PutKeyPolicy`) → apply local có MFA (khoá Enabled, rotation
  bật, alias, role policy, task def Booking :168 có biến khoá) → deploy Booking api :169 (09:38).
- Cognito WORKFORCE: nhóm `booking-contracting` gắn cho tài khoản E2E pricing maker 09:18, **gỡ** 11:05 (còn
  `cis-customer_success`).
- Dữ liệu SYNTHETIC ghi bởi live check: SUP-000015…17, HTL-000007, 1 hợp đồng + 5 add-on offer HCMC (published), tài khoản
  ngân hàng pending trên SUP-000017, desk entry TC-000039 (chưa huỷ).

## Bằng chứng verify

- Thư mục: `docs/audits/2026-11-24-S289-session/live/` (aa-1140, aa-1151-1152, aa-1151-1153, aa-1153-1158, aa-1160).
- AA-1140: 6/6 Done-when (1440/390, sáng/tối, EN/VI; trạng thái URL giữ sau reload). RDS "Free storage 14,83 GiB" là báo
  động giả (20 GB cấp, autoscaling tới 100 GB, dữ liệu thật ~5 GiB) → ngưỡng theo %.
- AA-1151: import 5 hoạt động SYNTHETIC → 5 nháp + 1 hợp đồng; checker publish hợp đồng, owner E2E publish 5 offer; view chỉ
  trả ngày còn giá (dừng 15/01/2027, Mon/Wed/Fri đúng); cảnh báo 60 ngày = Policy.
- AA-1152: 5 add-on hiện ở ngày HCMC trên planner AA (1440/390); "From $110 per person" hiện/ẩn theo công tắc
  (pilot-rehearsal-01). Chưa: add-on đi theo lead (chưa đại lý Dev nào bán tour HCMC).
- AA-1153: HTL-000007 qua SUP-000016 + SUP-000017; "70 USD, 20 %" → 56 net giữ 2 số gốc; báo giá HB 3 đêm 2 NL + 1 trẻ
  7 tuổi = 198 USD (DMC A sẽ là 216). Một phần: dòng chi phí đúng DMC B nhưng danh sách on-request desk B2B ghi DMC A.
- AA-1158: tài khoản nhập ở pending; owner E2E duyệt → 403 `bank_approver_not_allowed`; che 4 số cuối; không response nào
  trả số đầy đủ. Chưa: chặn chi trả khi pending (Dev không có hoá đơn NCC), ciphertext tại DB (cần run-script master).
- AA-1160: map + dải màu theo đại lý (pilot-rehearsal-01, audit-terra-family; AA vẫn vàng), sáng/tối; Tenant 360 ghi chú
  "chưa có đại lý CRM"; `shared.tenant_crm_agency` 9 dòng sau lượt kéo CRM hằng giờ (10:54).
- Nghi vấn rò rỉ tenant TripPlanner (lane live báo): 3 agent độc lập bác — chuyến do lane tự tạo không kèm header nên thuộc
  tenant demo; FORCE RLS + `app.tenant_id` giữ cách ly. Còn follow-up nhỏ 500 thay 403.

## Jira

- Chưa đăng gì. Nháp Jira của S289 chuyển sang phiên kế tiếp cùng ngày (quyết định 24/11 ~09:35);
  `docs/audits/2026-11-24-S289-session/jira-drafts.md`.

## Việc đầu phiên sau (S290, cùng ngày 24/11)

1. Soạn nháp Jira gộp S289 (AA-1140, AA-1151, AA-1152, AA-1153 p1, AA-1158 p2, AA-1160) → Nghiệp duyệt → đăng.
2. Merge PR bot schema reference #973 (CIS 477, tp-037, bk-071, crm-087) nếu vẫn mở.
3. Huỷ desk entry TC-000039; kiểm ciphertext `supplier_bank_account` bằng DB Migrate run-script master.
4. AA-1153 phần 2 (allotment / release days, Excel hai chiều) + sửa nhãn DMC ở danh sách on-request desk B2B.
5. Mục live còn lại: AA-1152 (đại lý Dev nhận tour HCMC → add-on vào lead), AA-1160 (tenant SYNTHETIC có route e-mail/webhook
   + locale vi), AA-1158 (chủ DN duyệt tài khoản pending; chặn chi trả khi pending).

## Còn lại

- AA-1153 phần 2; AA-1148 (lane E), AA-1119, AA-1118 chưa làm.
- Follow-up (không tạo issue Linear): Infra `PII_ALLOWLIST` thiếu bk-069 / bk-070; CRM kéo ~13 tenant CIS không còn (404
  hằng giờ); desk B2B on-request ghi nhầm DMC; phiên mới ở tenant B + mã chuyến tenant A trả 500 thay 403 (TripPlanner);
  test CIS `test_aa875_safe_http` lệch giờ trên runner; test frontend `tenantLeadRoute` 902 đỏ local; huỷ TC-000039;
  kiểm ciphertext `supplier_bank_account`; `tools/workflows/lane.js` COMMON thêm 3 dòng (không mã issue trong text route,
  `x-tp-tenant-slug` khi live check, Postgres UTC); trang status nên tách 401 kiểm phiên khỏi tỉ lệ lỗi client.
- Từ S288 vẫn chờ người: AA-1157, AA-1158 phần 1, AA-1149, AA-1172, AA-1174, AA-1175, AA-1176; AA-1173 chờ GitHub App chỉ đọc.

## Lưu ý kỹ thuật cho phiên sau

- Push từ máy: đặt `AA_GITLEAKS=<workspace>/.tmp-session/gitleaks-8301/gitleaks` (shim mise chặn push).
- Khoá KMS mới: tạo bằng apply local MFA `-target`, không dispatch CI (boundary cấm `PutKeyPolicy`).
- PR frontend phụ thuộc API: khai `@after=<PR API>` khi ship wave.
- Live check API TripPlanner của planner đại lý luôn kèm `x-tp-tenant-slug`.
- Bài học chi tiết đã chuyển vào `skill/aa-lessons/lessons.md` (9 dòng S289).

## Session block cho memory Notion

```
## S289 (24/11/2026, Claude Code — VS Code/WSL): qua đêm — add-on, khách sạn qua nhiều DMC, tài khoản ngân hàng NCC, trang Ecosystem status
**Quyết định của Nghiệp** — "lọc việc coding làm tới 7h", "phân phối tránh limit 5h và OOM", "xong sớm thì kéo thêm việc"; 24/11: #1 KMS "chạy luôn" (một khoá chung); #2 đồng ý tự làm (gắn tạm booking-contracting cho E2E pricing maker, allow-list E2E DMC thứ hai + báo giá SYNTHETIC, ADR 0006a A10e-5); #3 ok chi phí CloudWatch (~0,07 USD/ngày); #4 chỉ chủ DN duyệt tài khoản ngân hàng NCC (tech lead dự phòng); "làm xong hết thì dừng phiên, nháp Jira chuyển phiên sau cùng ngày".
**Kết quả chính** — Done: AA-1140 trang Ecosystem status (CIS #1656–#1658, #1660–#1662; 6/6 live), AA-1151 hoạt động tuỳ chọn (Booking #310/#313, CIS #1653; import 5 → publish người thứ hai → view chỉ ngày có giá). In Review: AA-1152 (Booking #315/#316, Partner #384/#385, TP #297/#298, CIS #1659; live 2/3), AA-1158 p2 (Booking #309/#311/#317/#318, Infra #984 KMS; live 4/5), AA-1160 (CIS #1654/#1655, TP #294/#296, Partner #382). In Progress: AA-1153 p1 (Booking #312/#314; live 3/4), p2 → S290. CIS #1652 ghim requirements. Không LLM trả phí.
**Trạng thái kiểm cuối phiên** — ECS 8/8 1/1 COMPLETED, revision mới nhất: cis-api :1265 / worker :834 / admin :94 (7b1c8afd), booking-api :170 / admin :62 (094d678d), crm-api :215 / web :189 (28b1c4f6), tp-web :26 (12b6a4d2). Migration CIS 477, bk-071, crm-087, tp-037 (áp trong phiên: bk-067…071, CIS 474…477, crm-086/087, tp-036/037). shared.job 0. KMS alias/aa-booking-dev-supplier-bank Enabled, rotation bật. Root head 0a8486a6, bot schema #973 mở. Jira: chưa đăng, chuyển phiên sau.
**Việc cần làm đầu phiên sau (S290)** — (1) nháp Jira gộp S289 → duyệt → đăng; (2) merge bot #973; (3) huỷ TC-000039 + kiểm ciphertext supplier_bank_account (run-script master); (4) AA-1153 phần 2; (5) live còn lại AA-1152 / AA-1160 / AA-1158.
**Lưu ý kỹ thuật** — KMS key có boundary cấm PutKeyPolicy → tạo bằng apply local MFA, không CI; push cần AA_GITLEAKS trỏ bản 8.30.1 trong .tmp-session; PR frontend phụ thuộc API khai @after khi ship wave; live check API TripPlanner luôn kèm x-tp-tenant-slug; Postgres lane nên chạy UTC.
```
