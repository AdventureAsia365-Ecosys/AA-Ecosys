# S289 — trạng thái kiểm cuối phiên (24/11/2026, ~11:40 +07)

Nguồn: lệnh đọc live lúc chốt phiên (AWS CLI acc2 chỉ đọc, health endpoint, GitHub API). Bảng job do agent điều phối
đếm lúc 11:25 (ECS exec chỉ đếm).

## ECS (cluster aa-cis-dev-cluster)

Mọi service 1/1, rollout COMPLETED, một deployment; revision đang chạy = revision mới nhất của family (không còn revision mẫu lạc).

| Service | Task def | Running/desired | Rollout | Image | Revision mới nhất của family |
|---|---|---|---|---|---|
| aa-cis-dev-api | :1265 | 1/1 | COMPLETED | dev-7b1c8afd (#1662) | :1265 ✓ |
| aa-cis-dev-worker | :834 | 1/1 | COMPLETED | dev-7b1c8afd (cùng SHA api) | :834 ✓ |
| aa-cis-dev-admin | :94 | 1/1 | COMPLETED | dev-7b1c8afd | :94 ✓ |
| aa-booking-dev-api | :170 | 1/1 | COMPLETED | 094d678d (#318) | :170 ✓ |
| aa-booking-dev-admin | :62 | 1/1 | COMPLETED | 094d678d | :62 ✓ |
| aa-crm-dev-api | :215 | 1/1 | COMPLETED | 28b1c4f6 (#385) | :215 ✓ |
| aa-crm-dev-web | :189 | 1/1 | COMPLETED | 28b1c4f6 | :189 ✓ |
| aa-tripplanner-dev-web | :26 | 1/1 | COMPLETED | 12b6a4d2 (#298) | :26 ✓ |

Đầu phiên (23/11 22:55): cis-api :1256, worker :825, cis-admin :90, booking-api :163, booking-admin :58, crm-api :214,
crm-web :187, tp-web :23.

## Health và migration

- CIS `/health` + `/health/ready`: ok, schema **477**, git_sha 7b1c8afd (khớp ECS), version 0.21.0.
- Booking `/booking/health` + `/booking/health/ready`: ok, schema **bk-071**, git_sha 094d678d (khớp ECS);
  storage `supplier_bank_key` = configured.
- CRM `/crm/health` + `/crm/health/ready`: ok, **crm-087**, git_sha 28b1c4f6; CRM web `/healthz` ok (28b1c4f6, 0.14.0).
- TripPlanner web `/api/health`: ok, git_sha 12b6a4d2 (khớp image tp-web), 0.17.0. Lambda `aa-tripplanner-dev-browse` /
  `-assembly` cập nhật 24/11 01:38 UTC (cùng CodeSha256); `/api/browse?resource=countries` 200.
- TripPlanner **tp-037**: theo PR bot schema dump #973 (sau DB Migrate apply cis/477): CIS 477, tp-037, bk-071, crm-087.
  Dòng "Verified" trên master còn ở bản 00:53 UTC (CIS 475, tp-035, bk-069) vì #973 chưa merge.
- Migration áp Dev trong phiên: Booking bk-067, bk-068, bk-069, bk-070, bk-071; CIS 474, 475, 476, 477; CRM crm-086,
  crm-087; TripPlanner tp-036, tp-037.

## Bảng job

- `shared.job` 0 queued/running (agent điều phối kiểm 11:25).
- `booking.job` / `crm.job`: không đếm riêng lúc chốt; guard deploy của CI tự chặn khi còn job. Không có wave mở.

## Khoá KMS (AA-1158)

- `alias/aa-booking-dev-supplier-bank`: Enabled, CUSTOMER, SYMMETRIC_DEFAULT, rotation **bật**.
- Tạo bằng apply local có MFA (CI không được `PutKeyPolicy`); Booking api :169 trở đi có biến khoá.

## Repo (head nhánh mặc định)

| Repo | Head | PR còn mở |
|---|---|---|
| AA-Ecosys | 0a8486a6 (#974, ADR 0006a A10e-5) | #973 bot schema reference (chưa merge), #958 dependabot |
| AA-CIS-App | 7b1c8afd (#1662) | #1645 release 0.22.0, #1638 / #1586 dependabot, #1467 bot test durations |
| AA-Booking | 094d678d (#318) | #305 dependabot, #302 release 0.18.0, #276 kit sync, #200 bk-045 (cũ, chờ ≥ 28/11) |
| AA-Partner | 28b1c4f6 (#385) | #383 dependabot, #380 release 0.15.0, #355 kit sync |
| AA-TripPlanner-Web | 12b6a4d2 (#298) | #295 release 0.18.0, #293 dependabot |
| AA-CIS-Infra | 8422045d (#998, copy CIS 477) | #977 dependabot, #935 (cũ, WAF geo sau MFA admin) |

PR merge trong phiên: root #960, #961, #964, #966, #968, #969, #974 (+ bot schema #962, #963, #965, #967, #970–#972);
CIS #1652–#1662; Booking #309–#318; Partner #382, #384, #385; TripPlanner #294, #296, #297, #298; Infra #983–#998.

## Thứ cố ý để BẬT / giữ lại cho phiên sau

- Không có wave mở, không cờ nào bật cho wave.
- Bản ghi SYNTHETIC giữ lại trên Dev: nhà cung cấp SUP-000015, SUP-000016, SUP-000017; khách sạn HTL-000007 (bán qua
  SUP-000016 + SUP-000017); 5 add-on offer SYNTHETIC đã publish (HCMC); tài khoản ngân hàng SYNTHETIC **pending** trên
  SUP-000017 (để chủ DN duyệt thử).
- Desk entry **TC-000039** (báo giá SYNTHETIC qua DMC thứ hai) còn đó: phải huỷ khi dọn (ADR 0006a A10e-5).
- Cognito: nhóm `booking-contracting` đã gắn cho tài khoản E2E pricing maker lúc 09:18 và **đã gỡ** lúc 11:05 (còn
  `cis-customer_success`).
- Trang Ecosystem status đọc CloudWatch GetMetricData (~0,07 USD/ngày khi trang mở), tech lead đã chấp nhận.

## Lệch so với điều phiên tưởng

- CIS admin đã ở 7b1c8afd (#1662), mới hơn `3a0f604a` (#1660) ghi trong checklist.
- PR bot schema reference #973 chưa merge, nên dòng "Verified" trên master chưa có tp-037 / bk-071 / CIS 477.
- `tools/docs/gen_sections.py` / `docs_freshness.py` / `doc_impact.py` không chạy trong lượt chốt này (như S288).
