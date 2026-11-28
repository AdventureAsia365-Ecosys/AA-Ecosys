---
id: OPS-08-s297-state-snapshot
title: "S297 state snapshot (28/11/2026, session close)"
description: "Live state read at the S297 close: ECS revisions and builds, health and readiness, migrations, job tables, repo heads and open PRs, what is left switched on."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-28
review_every_days: 30
related: [AA-1182, AA-1183, AA-1185, AA-1191, AA-1193]
---

# S297 — snapshot trạng thái cuối phiên (28/11/2026, ~10:00 UTC)

Đọc live bằng `aws ecs describe-services`, `curl` health/ready, `gh`. Không ghi account ID, ARN hay giá trị secret.

## ECS (cluster aa-cis-dev-cluster) — 8/8 COMPLETED, 1/1

| Service | Revision đang chạy | Revision mới nhất | Build |
|---|---|---|---|
| aa-cis-dev-api | :1312 | :1312 | 380515a8 |
| aa-cis-dev-worker | :881 | :881 | 380515a8 (cùng image api) |
| aa-cis-dev-admin | :117 | :117 | (không đọc SHA; deploy admin cuối của phiên, sau CIS #1729/#1731) |
| aa-booking-dev-api | :185 | :185 | 26882665 |
| aa-booking-dev-admin | :79 | :79 | (không đọc SHA; deploy admin cùng Booking #347) |
| aa-crm-dev-api | :232 | :232 | 1e49ce19 |
| aa-crm-dev-web | :203 | :203 | 1e49ce19 |
| aa-tripplanner-dev-web | :33 | :33 | 6349be4c |

Revision mới nhất = đang chạy cho mọi family. Drill rollback (AA-1193) để lại revision CIS :1311/:880 → đã deploy lại main thường (run 46131402113) để căn lại (:1312/:881).

## Endpoint

| App | Kết quả |
|---|---|
| CIS `/health`, `/health/ready` | ok, git_sha 380515a8, schema 498 |
| Booking `/booking/health`, `/booking/health/ready` | ok, git_sha 26882665, migration bk-075 |
| CRM `/crm/health`, `/crm/health/ready` | ok, git_sha 1e49ce19, migration crm-090 |
| CRM web `/healthz` | ok, git_sha 1e49ce19 (deploy lại sau rollback tạm thời, run 46130679381 xanh kể cả UI smoke) |
| TripPlanner web `/api/health` | ok, git_sha 6349be4c |
| TripPlanner Lambda browse / assembly | CodeSha256 cùng một bản, sửa lần cuối 27/11 11:06Z (không đổi trong phiên) |

Migration mới nhất mỗi owner (db-schema-reference, root #1064 `7c394e93`, Verified 28/11 07:40 UTC): CIS **498**, bk-075, crm-090, tp-037.

## RDS / NAT / IAM (thay đổi trong phiên)

- `aa-cis-dev-db`: mật khẩu master do RDS quản (`manage_master_user_password`), xoay tự động 180 ngày; secret cũ `aa-cis/dev/rds` lên lịch xoá (còn khôi phục được tới 05/12), GitHub `TF_VAR_DB_PASSWORD` đã xoá.
- NAT: swap 1 GB bền (association `aa-ecosys-dev-nat-swap`, CN 20:45 UTC), vá xong 28/11 05:21Z (79 cài, 0 thiếu, 0 lỗi); lượt vá kế CN 29/11 21:00 UTC.
- Bootstrap `tf_apply_sec` (NatSwapDocument + chatbot), 3 policy `sns:Publish` của role deploy; role compliance-evidence đọc metadata secret (13 lệnh).
- Key CI bot: key mới trong environment `ci-bot` ở 6 repo, 6 bản cũ đã xoá; key cũ trong App settings chờ tech lead xoá.

## Bảng job

- `shared.job`: 0 queued/running (succeeded 9805, failed 21, cancelled 7).
- `booking.job`: 0 queued/running.
- `crm.job`: chỉ job định kỳ (2 queued lúc đầu phiên).
- Không có wave mở.

## Repo (head nhánh mặc định, PR mở)

| Repo | Head | PR mở |
|---|---|---|
| AA-Ecosys | 7c394e93 | #1048 (bot infra docs) |
| AA-CIS-App | 380515a8 | #1717 / #1710 / #1709 (nháp, có chủ đích), #1645 (release), #1638 (deps), #1467 |
| AA-Booking | 26882665 | #336 (nháp bk-076), #330, #302 (release) |
| AA-Partner | 1e49ce19 | #380 (release) |
| AA-TripPlanner-Web | 1575cfa3 | #295 (release) |
| AA-CIS-Infra | e1341573 | #1043 / #1042 (nháp chuỗi bk-076), #935 |

Chưa mở PR (worktree local, chờ bk-076): lane l3 AA-1187 (Booking `feat/aa-1187-supplier-pack`, `feat/aa-1187-import-record-grant` bk-077, root guide).

## Cố ý để BẬT / đang chạy cho phiên sau

- AA-873 trial Security Hub / Inspector / Macie: 4 lịch tự tắt 29/11 09:17–09:32 UTC.
- Rào pilot `cis.platform.pilot_e2e_fence` = **tắt** (chỉ bật ngày pilot).
- `cis.billing.enabled_currencies` = `["USD"]`.
- Kênh Slack báo động: Terraform có sẵn, `chat_alerts_enabled = false` (tech lead: chưa cần).

## Lệch so với điều phiên tưởng

- Lượt cron E2E CRM 03:17Z không chạy (GitHub bỏ lượt); lượt sau deploy xanh.
- CRM web của Partner #411 tự rollback một lần (503 từ CIS khi drill CIS chạy trùng) → deploy lại xanh.
