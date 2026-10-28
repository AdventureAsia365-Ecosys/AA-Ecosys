# S255 — State snapshot lúc chốt phiên (28/10/2026, 20:08 +07)

Chỉ tên và số; không account ID, ARN hay giá trị secret.

## ECS (cluster aa-cis-dev-cluster) — revision đang chạy = revision mới nhất, 1/1, COMPLETED

| Service | Task def | Image | Ghi chú |
|---|---|---|---|
| aa-cis-dev-api | :890 | `844ce1b1` | CIS #1103 (AA-850 mig 299); trước đó #1102 `9d919f0f` (AA-998) |
| aa-cis-dev-worker | :456 | `844ce1b1` | cùng SHA với api |
| aa-booking-dev-api | :80 | `39a15d27` | Booking #136 (bỏ mã issue UI) |
| aa-crm-dev-api | :72 | `2556d31a` | Partner #110 |
| aa-crm-dev-web | :40 | `2556d31a` | task bị Spot Interruption lúc 19:3x, ECS tự thay — 1/1 lúc chụp |
| aa-crm-dev-portal | :12 | `a33ccf4a` | Partner #109 (AA-671) |

Không còn biến `BEDROCK_ACCT_FALLBACK` trên task CIS (AA-998). PR #1104 (AA-898 EN/VI + Mermaid) đang trong merge queue lúc chụp; deploy của nó sẽ nâng CIS lên revision kế.

## Endpoint

| App | /health | /health/ready |
|---|---|---|
| CIS | ok, 0.13.0, `844ce1b1` | ok, db ok, schema **299** (required 293) |
| Booking | ok, 0.9.0, `39a15d27` | ok, schema **bk-032** |
| CRM api | ok, 0.7.0, `2556d31a` | ok, schema **crm-023**, membership_feed ok, keys kms |
| CRM web | ok, 0.7.0, `2556d31a` | — |
| TripPlanner Lambda | browse + assembly CodeSha256 `RY5lkl0T…` (deploy 12:28Z, TP #174 AA-998) | — |

Migration mới nhất mỗi owner: CIS **299** (áp trong phiên: 293, 294, 295, 296, 299), Booking **bk-032**, TripPlanner **tp-020**,
CRM **crm-023** (áp trong phiên).

## Bảng job / wave

- `shared.job`: 1 `place_relocate` queued — lượt AA-997 Laos dừng vì hết credit Geoapify trong ngày, tự chạy lại 29/10 00:11Z. Có chủ đích.
- `shared.rerun_wave` mở: 0. `booking.job` / `crm.job`: không đọc được bằng cis_app (DB Migrate apply 40691807177 lúc 19:58 chạy được → bảng job rảnh).

## Hạ tầng (Infra) thay đổi trong phiên

- AA-896: budget tổng 300 USD + FORECASTED, budget identity; acc3 SNS `aa3-cost-alerts` (Confirmed) + anomaly IMMEDIATE ≥ 15 USD.
- AA-873: S3 BPA tài khoản (4/4), Access Analyzer ACTIVE, rule cảnh báo IAM/SG/root/trail, CloudTrail đa vùng + KMS + Object Lock
  GOVERNANCE 365 ngày, NAT AMI pin (không đổi instance) + tắt ECS agent trên NAT; **GuardDuty TẮT** (bật nhầm vài phút, đã gỡ).
- AA-838: alarm kết nối crm_app; script probe + dead-table dry run trong `db/scripts/`.
- AA-898: role docs-sync + quyền đọc prefix `docs-reader/`; 2 secret repo gốc.
- AA-998: bỏ grant/env acc1 trên acc2; destroy `accounts/acc1-bedrock` (7) + bucket state; Infra #476 xoá thư mục (đang merge).

## acc1 (tài khoản cá nhân, ngoài hệ sinh thái)

0 role ngoài AWS/SSO, 0 OIDC, 0 bucket, 0 Lambda, 0 log group, 0 KMS khách hàng, 0 EC2/EBS mọi vùng; 1 secret us-east-1 đã lên lịch
xoá (04/11); budget cảnh báo 1 USD; key tĩnh Inactive.

## PR còn mở lúc chụp

- CIS #1104 (AA-898 EN/VI + Mermaid) — merge queue; Infra #476, root #304 — đang merge; root #297, #301 (PR bot docs sinh tự động);
  các release PR (CIS #1093, Booking #133, Partner #106, TripPlanner #173) — gom ở phiên sau.

## Cố ý để BẬT cho phiên sau

- `JOB_TEST_KINDS=1` trên Dev (như S254); writer S1 v2 + `s1_generate` = sonnet-5-5; `PLACE_PIPELINE_AUTO=on`; Writing memory release 0 active.
- Cờ `T8_ANGLE_BRIEF_MODE` TẮT (AA-790 r8 FAIL). GuardDuty TẮT.
- Job `place_relocate` (AA-997) chạy tiếp theo credit mỗi ngày.

## Vercel

Không đọc lại commit Production của từng project Vercel trong phiên này (connector Vercel không được dùng); CIS admin / TripPlanner
deploy theo push main như thường lệ.
