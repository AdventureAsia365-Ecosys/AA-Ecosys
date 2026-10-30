---
id: OPS-08-s258-state-snapshot
title: "S258 state snapshot (30/10/2026)"
description: "Trạng thái live cuối phiên S258: ECS, health, migration, PR mở, việc cố ý để bật."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-30
review_every_days: 30
related: [AA-993, AA-1002, AA-1003, AA-997]
---

# S258 — state snapshot (chụp 30/10/2026 06:55 +07, 23:55Z 29/10)

STS acc2 OK (MFA tới 08:21 +07).

## ECS (cluster aa-cis-dev-cluster), tất cả COMPLETED 1/1

| Service | Task definition | Image / SHA |
|---|---|---|
| aa-cis-dev-api | :921 | `2cc3cc52` (CIS #1159) |
| aa-cis-dev-worker | :487 | `2cc3cc52` |
| aa-booking-dev-api | :86 | không đổi trong phiên |
| aa-crm-dev-api | :77 | không đổi |
| aa-crm-dev-web | :50 | không đổi |

CIS main đã có thêm #1160, #1161, #1162, #1163, #1166 nhưng **Deploy Dev bị cổng schema-gate chặn** (xem dưới).

## Health

- CIS `/health/ready`: ok, schema **305**, git `2cc3cc52`.
- Booking `/booking/health/ready`: ok, **bk-035** (bk-034 tự áp, bk-035 DB Migrate).
- TripPlanner web `/api/health`: ok, 0.13.0, `0665c092` (TP #189).

## Migration mới nhất mỗi owner

| Owner | Mới nhất | Cách áp |
|---|---|---|
| CIS | 306 | 304 DB Migrate (contract); 305 tự áp (expand, chuỗi bot); 306 DB Migrate apply 40978746621 (07:2x, sau khi job queued cũ tự kết thúc) |
| Booking | bk-035 | bk-034 tự áp (bằng chứng AA-993); bk-035 DB Migrate (contract) |
| TripPlanner | tp-022 | DB Migrate (contract) |
| CRM | crm-023 | không đổi |

## Bảng job

`shared.job`: 0 queued/running sau 00:16Z (job aa997.1 cũ đã kết thúc); 2 job census AA-997 succeeded. Không wave mở.

## PR còn mở lúc chụp

- root #328 (AA-993 M5, cố ý), #356 (bot docs, đang merge)
- CIS #1164 (adapter Anthropic, chờ CI sau sửa CodeQL), #1150 (release 0.17.0)
- Booking #150 (kit sync), #151 (release) — đang merge
- TripPlanner #190 (release), #192 (kit sync) — đang merge
- Partner #125 (kit sync) — đang merge
- Infra #509 (consumer grants cho probe; chờ check sau khi CIS #1166 merge)

## Cố ý để BẬT / lưu ý cho phiên sau

- `DB_AUTO_APPLY=true` trên AA-CIS-Infra (tech lead duyệt S258).
- Cổng schema-gate CIS: lần tự áp có file gần nhất (305, run 40922869610) có probe đỏ vì probe không nhận role (đã sửa Infra #507); cổng chỉ mở khi một lần tự áp expand MỚI xanh cả probe.
- Connection `anthropic-direct` (304/306) mặc định tắt; chưa có khoá.
- Terraform apply 40975065381: 1 thay đổi (IAM logs:FilterLogEvents), drift job đêm 05:37 UTC.

## Cập nhật 07:25 +07

- Infra #509 merged; bot PRs merged: root #356, TP #190 #192, Booking #150 #151, Partner #125.
- CIS #1164 (adapter Anthropic) trong merge queue; CIS #1150 (release 0.17.0) để phiên sau (deploy CIS đang bị cổng).
- PR còn mở cố ý: root #328 (AA-993 M5).
