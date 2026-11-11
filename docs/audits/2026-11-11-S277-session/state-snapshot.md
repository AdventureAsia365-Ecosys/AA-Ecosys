---
title: S277 state snapshot
lang: vi
---

# S277: snapshot trạng thái cuối phiên (11/11/2026, ~20:45 +07, tác nhân: Claude Code)

Chỉ tên và số; không account ID, ARN hay giá trị secret.

## ECS (cluster aa-cis-dev-cluster)
| service | task def | image tag | rollout | running/desired |
|---|---|---|---|---|
| aa-cis-dev-api | aa-cis-dev-api:1097 (latest aa-cis-dev-api:1097) | dev-318a7982ee7a | COMPLETED | 1/1 |
| aa-cis-dev-worker | aa-cis-dev-worker:666 (latest aa-cis-dev-worker:666) | dev-318a7982ee7a | COMPLETED | 1/1 |
| aa-booking-dev-api | aa-booking-dev-api:117 (latest aa-booking-dev-api:117) | 69c4ffb0d552240d | COMPLETED | 1/1 |
| aa-booking-dev-admin | aa-booking-dev-admin:18 (latest aa-booking-dev-admin:18) | d7ea134136a9baf3 | COMPLETED | 1/1 |
| aa-crm-dev-api | aa-crm-dev-api:156 (latest aa-crm-dev-api:156) | 066560e711126e0e | COMPLETED | 1/1 |
| aa-crm-dev-web | aa-crm-dev-web:136 (latest aa-crm-dev-web:136) | 066560e711126e0e | COMPLETED | 1/1 |
| aa-tripplanner-dev-web | aa-tripplanner-dev-web:11 (latest aa-tripplanner-dev-web:11) | 63a2aa2a56f843aa | COMPLETED | 1/1 |

## Endpoints
- CIS /health: status=ok git_sha=318a7982ee7a
- CIS /health/ready: status=ok schema_version=398 git_sha=318a7982ee7a
- Booking /booking/health: status=ok git_sha=69c4ffb0d552
- Booking /booking/health/ready: status=ok schema_version=bk-048
- CRM /crm/health: status=ok git_sha=066560e71112
- CRM /crm/health/ready: status=ok schema_version=crm-058
- TripPlanner web /api/health: status=ok git_sha=63a2aa2a56f8

## Open PRs
- AA-Ecosys: #698 bot/generated-infra-docs;#697 bot/db-schema-reference;
- AA-CIS-App: #1179 release-please--branches--main--components--aa-cis-app;
- AA-Booking: #200 feat/aa1046-bk045-retire-b2c;#161 release-please--branches--main--components--aa-booking;
- AA-Partner: #133 release-please--branches--main--components--aa-partner;
- AA-TripPlanner-Web: #196 release-please--branches--main--components--aa-tripplanner-web;
- AA-CIS-Infra: none

## Bảng job và wave

- `shared.job`: không có job queued/running (đọc lúc chốt).
- Wave: hai wave thử recompose (beb7b307, 8a3c0f28) đã đóng; không wave nào mở.

## Cố ý để BẬT

- `T7_BLOG_MIN_SEED_WORDS=600` trên worker CIS (AA-1077, quyết định của tech lead).
- `S1_CONTROL=contract`, `T2_ORCHESTRATOR=linear`, `T9_SEO_BUILDER=on` (như cũ). `T9_LENGTH_EXTEND` để tắt (thử 0/3).
- Chat lập kế hoạch TripPlanner: trần 2 USD/tháng cho app và mỗi tenant.

## Lệch / ghi chú

- Root `db-schema-reference.md` cập nhật bk-048 qua bot PR #697 (đang merge lúc chốt).
- Booking #200 (AA-1046, bk-045 retire B2C) là PR cũ, chưa thuộc phiên này, để nguyên.
- acc3 vào org của acc1 (payer) 11/11; xem ADR 0001a Note S277.
