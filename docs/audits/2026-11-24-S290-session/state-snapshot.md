# S290 — state snapshot (24/11/2026, 18:3x +07)

Nguồn: lệnh đọc live lúc chốt phiên (AWS CLI acc2 chỉ đọc, health endpoint, GitHub API, ECS exec đếm bảng job). Chỉ tên và số.

## ECS (cluster aa-cis-dev-cluster, 8 service)

| Service | Task def đang chạy (= mới nhất) | Running/desired | Rollout | Image |
|---|---|---|---|---|
| aa-cis-dev-api | :1271 | 1/1 | COMPLETED | dev-f06e3001 |
| aa-cis-dev-worker | :840 | 1/1 | COMPLETED | dev-f06e3001 (cùng SHA với api) |
| aa-cis-dev-admin | :97 | 1/1 | COMPLETED | dev-f06e3001 |
| aa-booking-dev-api | :174 | 1/1 | COMPLETED | 29407508 |
| aa-booking-dev-admin | :65 | 1/1 | IN_PROGRESS lúc đọc (deploy 29407508 vừa xong) | 29407508 |
| aa-crm-dev-api | :216 | 1/1 | COMPLETED | 1591609a |
| aa-crm-dev-web | :189 | 1/1 | COMPLETED | 28b1c4f6 |
| aa-tripplanner-dev-web | :27 | 1/1 | COMPLETED | 1b8502c3 |

Mỗi family: revision đang chạy = revision mới nhất.

## Endpoint

| Endpoint | HTTP | Trạng thái / schema / git_sha |
|---|---|---|
| CIS /health, /health/ready | 200, 200 | ok, schema 479, f06e3001 |
| Booking /booking/health, /health/ready | 200, 200 | ok, bk-074, 29407508 |
| CRM /crm/health, /crm/health/ready | 200, 200 | ok, crm-087, 1591609a |
| CRM web /healthz | 200 | ok, 28b1c4f6 |
| TripPlanner /api/health | 200 | ok, 1b8502c3 |

## Migration mới nhất mỗi owner

CIS 479 (áp trong phiên: 478, 479), Booking bk-074 (áp: bk-072, bk-073, bk-074), CRM crm-087, TripPlanner tp-037.

## Bảng job

`shared.job` 0 queued/running lúc chốt. Recompute platform (kích hoạt bởi trash tour tay SYNTHETIC lúc 10:04Z) chạy xong ~11:04Z (đã từng chặn DB Migrate apply bk-074 một lần). `booking.job` / `crm.job`: guard deploy của CI không chặn wave nào trong phiên. Không có wave mở.

## Repo (head nhánh mặc định)

| Repo | Head |
|---|---|
| AA-Ecosys | a711b575 (sau đó: root PR chốt phiên) |
| AA-CIS-App | f06e3001 |
| AA-Booking | 29407508 |
| AA-Partner | 1591609a |
| AA-TripPlanner-Web | 1b8502c3 |
| AA-CIS-Infra | d7e979da |

PR còn mở: chỉ PR bot (release-please, kit sync, test durations, schema reference #981 đang merge) và dependabot; AA-Booking #200 (bk-045 xoá bảng B2C, chờ từ trước, có chủ đích); AA-CIS-Infra #935 (WAF geo cho staff host, chờ TOTP chủ DN).

## Hạ tầng / AWS

- Bucket bằng chứng Object Lock (GOVERNANCE 365 ngày) + role `aa-cis-dev-compliance-evidence` (Terraform Apply run 45357390166); 2 secret repo đặt ở root + Infra; thử xoá/ghi đè/bypass đều AccessDenied.
- RDS: xoá 22 snapshot thủ công pre-S1 wave (DRY RUN 22, md5 danh sách 2f550366716c); còn 14 snapshot thủ công; `db-migrate-tp-018` giữ theo tag tới 2027-04-21 → alarm copy-age vẫn đỏ (chủ ý).
- Cognito WORKFORCE: info@ thêm nhóm `booking-custom` (vai Booking "Product, ops & accounting"); E2E pricing maker gắn tạm `booking-contracting` 13:18, gỡ 17:33.

## Cố ý để BẬT / giữ cho phiên sau

- Dữ liệu SYNTHETIC close-out S290 (SUP-000018/19, HTL-000008/9, SVC-000018/19, 2 hợp đồng, plan Thái có thành phần + ghi chú, TC-000040/41, BIL-000002…004, tài khoản ngân hàng pending SUP-000019) giữ tới khi kiểm AA-1158 khoá chi trả 24 h (sau buổi thứ Năm 26/11).
- `price_pax_bands` v4 (= giá trị v2); pilot-rehearsal-01 giữ tour HCMC đã adopt; E2E Lead Proof Travel có crm.core + route e-mail.
- Hai công tắc hai người (`cis.content.publish_two_person`, `cis.settings.two_person_approval`) TẮT trên Dev tới thứ Năm.
