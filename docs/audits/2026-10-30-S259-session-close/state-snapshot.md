---
id: OPS-08-s259-state-snapshot
title: "S259 state snapshot (30/10/2026)"
description: "Trạng thái live cuối phiên S259: ECS, health, migration, PR mở, việc cố ý để bật."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-30
review_every_days: 30
related: [AA-993, AA-1002, AA-1003, AA-1004, AA-952, AA-997]
---

# S259 — state snapshot (chụp 30/10/2026 13:24 +07, 06:24Z)

STS acc2 OK (MFA làm mới 08:46, hạn ~16:45 +07).

## ECS (cluster aa-cis-dev-cluster), tất cả COMPLETED 1/1; revision mới nhất mỗi family = revision đang chạy

| Service | Task definition | Image |
|---|---|---|
| aa-cis-dev-api | :928 | `dev-1878349b` (CIS #1176) |
| aa-cis-dev-worker | :494 | `dev-1878349b` (cùng SHA) |
| aa-booking-dev-api | :89 | `45de0368` (Booking #156) |
| aa-crm-dev-api | :79 | `c572c6e1` (Partner #128) |
| aa-crm-dev-web | :51 | `55978689` (không đổi trong phiên) |

## Health

- CIS `/health/ready`: ok, schema **310**, git `1878349b`.
- Booking `/booking/health/ready`: ok, **bk-035**.
- CRM `/crm/health/ready` (portal host): ok, **crm-023**; CRM web `/healthz` ok 0.10.0.
- TripPlanner `/api/health`: ok 0.13.0 `8d5e18f1`.

## Migration mới nhất mỗi owner

| Owner | Mới nhất | Cách áp trong phiên |
|---|---|---|
| CIS | 310 | 307 tự áp (Infra #516 bot → 40997477090); 308 contract (Infra #517, DB Migrate 40999510605 / 40999747238); 309 tự áp (Infra #518); 310 contract (Infra #519, DB Migrate 41013419921 / 41013624854) |
| Booking | bk-035 | không đổi |
| TripPlanner | tp-022 | không đổi |
| CRM | crm-023 | không đổi |

## Bảng job / wave

- `shared.job`: chuỗi `place_relocate` AA-997 (aa997.3 + v2, dòng `llm`) — 830 / 2.221 dòng xong hôm nay, job kế
  `dac718c6` queued cho 31/10 00:12Z (credit Geoapify ngày; không chặn deploy, DB Migrate tính là "later").
- `booking.job` / `crm.job`: chỉ job định kỳ. Không wave mở.

## Repo (head nhánh mặc định lúc chụp)

| Repo | Head | PR mở |
|---|---|---|
| AA-CIS-App | `1878349b` gateway S4 | — (release 0.18.0 #1170 merged `2dc937b3` sau khi chụp) |
| AA-Booking | `45de0368` S6d + Figma gaps | — (release 0.14.0 #154 merged `675a74d1` sau khi chụp) |
| AA-TripPlanner-Web | `cc19a9a6` release 0.14.0 | — |
| AA-Partner | `c572c6e1` C-M3 confirm | — (release 0.11.0 #127 merged `2e5c4f61` sau khi chụp) |
| AA-CIS-Infra | `823a3824` copy 310 | — |
| AA-Ecosys | `8a9c8bef` schema dump | #328 (AA-993 M5, cố ý) + PR chốt phiên này |

## Tài khoản quản trị AWS mới (AA-1004)

Organization (feature ALL), 3 OU, 3 SCP gắn OU, org CloudTrail, 2 budget + anomaly, Identity Center (Single-Region,
us-west-1) với user tech lead (AA-Admin đăng nhập được), CI OIDC (`aa-terraform-plan` / `aa-terraform-apply`,
environment `org` có người duyệt). Drift CI 40995976788: management `plan exit 0`. Role bootstrap đã xoá.
Chi phí ~1–1,5 USD/tháng (KMS + S3 trail).

## LLM (probe 30/10 11:20)

Mọi model sinh văn bản FAIL: Bedrock acc3 Error 002; OpenAI trực tiếp 429 "no credits remaining" (gateway S4 test
connection: `quota_exhausted`). Chỉ Cohere Embed v4 (acc2) chạy.

## Cố ý để BẬT / lưu ý cho phiên sau

- `DB_AUTO_APPLY=true` trên AA-CIS-Infra (từ S258).
- Chuỗi relocate AA-997 tự chạy tiếp 31/10 (không cần thao tác).
- Membership studio-editor (E2E) trên agency tổng hợp Atlas & Hearth giữ lại để dùng lại (P-M1).
- Connection `anthropic-direct`, `bedrock-llm-org` tắt; `LLM_LEGACY_ALIASES` tắt; T10 tier-2 (`T10_ADJ_MODE`) tắt.
