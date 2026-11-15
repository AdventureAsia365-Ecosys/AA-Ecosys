---
id: AUD-S281-snapshot
title: S281 state snapshot at session close
description: Live state read at the S281 close (15/11/2026, ~07:40 UTC) - ECS revisions and images, health, migrations, job tables, repo heads and open PRs, what is left on.
type: reference
status: active
owner: nghiep
audience: [engineer, agent]
last_reviewed: 2026-11-15
review_every_days: 365
---

# Snapshot trạng thái cuối phiên S281 (15/11/2026, ~07:40 UTC)

Đọc live, chỉ tên và số (không account ID, ARN hay giá trị secret).

## AWS

- STS: acc2 (profile `aa365-admin`). Phiên MFA mới tới 21:11 +07.

## ECS (`aa-cis-dev-cluster`)

| Service | Revision đang chạy | Image | Running/desired | Rollout |
|---|---|---|---|---|
| aa-cis-dev-api | :1170 | dev-6393fd75 | 1/1 | COMPLETED |
| aa-cis-dev-worker | :739 | dev-6393fd75 (cùng SHA với api) | 1/1 | COMPLETED |
| aa-booking-dev-api | :141 | 8019cb88 | 1/1 | COMPLETED |
| aa-booking-dev-admin | :29 | — | 1/1 | COMPLETED |
| aa-crm-dev-api | :182 | 7e24a4c5 | 1/1 | COMPLETED |
| aa-crm-dev-web | :156 | 7e24a4c5 (gồm host academy) | 1/1 | COMPLETED |

Revision mới nhất của từng family trỏ cùng image với revision đang chạy (Terraform AA-1090 bước 2 đã apply rồi mới
deploy CIS, nên task definition mới có env của custom domain).

## Endpoint

| Endpoint | HTTP | Kết quả |
|---|---|---|
| CIS `/health/ready` | 200 | ok, schema 429, git 6393fd75 |
| Booking `/booking/health/ready` | 200 | ok, bk-058 |
| CRM `/crm/health/ready` (portal.) | 200 | ok, crm-070 |
| CRM web `/healthz` (portal.) | 200 | ok, 7e24a4c5 |
| Academy `/healthz` | 200 | ok, 7e24a4c5 |
| TripPlanner web `/api/health` | 200 | ok, 766d728d |
| TripPlanner Lambda browse | — | cập nhật 05:11Z (TP #269) |

Migration mới nhất: CIS 429, bk-058, tp-031, crm-070.

## Bảng job

- `shared.job`: rảnh. `booking.job`: rảnh. `crm.job`: 2 job định kỳ đang chờ (`crm_booking_sync`, `crm_heartbeat`).
- Không wave mở. Lượt fire R1 của AA-1048 (ECS exec trong worker CIS) đang chạy lúc chụp, xem dưới.

## Repo

| Repo | Head | PR còn mở |
|---|---|---|
| AA-Ecosys | master b9e75e04 | #766 bot (generated infra docs) + root PR chốt phiên S281 |
| AA-CIS-App | main 6393fd75 | #1528 (sửa chứng chỉ edge AA-1090, CI xanh, chờ fire xong), bot #1467, release-please #1179 |
| AA-Booking | main 8019cb88 | #200 (bk-045, chờ ≥ 28/11), release-please #161 |
| AA-TripPlanner-Web | main 766d728d | release-please #196 |
| AA-Partner | main 7e24a4c5 | release-please #133 |
| AA-CIS-Infra | main 3ca25a9b | — |

## Cố ý để BẬT / còn lại

- Công tắc xoá dữ liệu: **tắt hết** (AWS off, saga setting off v4, retention 30).
- `cis.t9.blog_extend_material = with_background` cho tenant audit `audit-atlas-hearth` (trial AA-1077, giữ).
- Domain test `trip-domain-test.click` (Route 53, 3 USD/năm, không tự gia hạn) và host thử
  `trip-test.trip-domain-test.click` trên tenant tổng hợp `pilot-rehearsal-01` (AA-1090, đang test lúc chụp).
- RDS snapshot `tenant-erase-20261115-erase02`: xoá sau khi root PR chốt phiên merge.
- Request xoá của tenant marker pilot (chế độ live, hẹn ≥ 14/12, CRM ≥ 12/02/2027): để nguyên.

## Bổ sung sau khi chụp

(điền khi lượt fire AA-1048 và test host AA-1090 xong)
