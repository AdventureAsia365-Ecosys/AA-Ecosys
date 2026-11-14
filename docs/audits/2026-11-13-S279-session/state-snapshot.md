# S279 — snapshot trạng thái live cuối phiên (14/11/2026 ~02:40 UTC)

Tác nhân: Claude Code. Chỉ tên, revision, SHA và mã HTTP; không account ID, ARN hay giá trị secret.

## ECS (cluster aa-cis-dev-cluster)

| Service | Task def đang chạy | Image | Rollout | Running | Revision mới nhất |
|---|---|---|---|---|---|
| aa-cis-dev-api | aa-cis-dev-api:1130 | dev-489a6165 | COMPLETED | 1/1 | 1130 (khớp) |
| aa-cis-dev-worker | aa-cis-dev-worker:699 | dev-489a6165 | COMPLETED | 1/1 | 699 (khớp) |
| aa-booking-dev-api | aa-booking-dev-api:130 (sau Deploy Dev 43546406937; trước đó :128) | 98e98078 | COMPLETED | 1/1 | 130 (khớp; dựng từ mẫu :129 của Infra #834) |
| aa-crm-dev-api | aa-crm-dev-api:170 | 3ed93c89 | COMPLETED | 1/1 | 170 (khớp) |
| aa-crm-dev-web | aa-crm-dev-web:147 | 3ed93c89 | COMPLETED | 1/1 | 147 (khớp) |

CIS api và worker cùng SHA 489a6165.

## Endpoint

| Endpoint | HTTP | SHA / migration |
|---|---|---|
| CIS `/health`, `/health/ready` | 200, 200 | 489a6165; schema 417 |
| Booking `/booking/health`, `/booking/health/ready` | 200, 200 | 98e98078; bk-057 |
| CRM api `/crm/health`, `/crm/health/ready` | 200, 200 | 3ed93c89; crm-065 |
| CRM web `/healthz` (partner-dev → portal host) | 200 sau chuyển hướng | |
| TripPlanner web `/api/health` | 200 | 566dee62 |
| TripPlanner `/api/browse?resource=countries` | 200 | Lambda browse + assembly cùng CodeSha256 `UV2tDY…`, sửa lần cuối 13/11 16:20 UTC (Infra #832 bỏ 2 env) |

Migration mới nhất: CIS 417, Booking bk-057, CRM crm-065, TripPlanner tp-031.

## Bảng job

- `shared.job`: 0 queued / running.
- `crm.job`: 3 job định kỳ queued (crm_booking_sync, crm_heartbeat, crm_membership_pull) — bình thường.
- `booking.job`: 0 queued / running (sau deploy).
- Không wave nào mở.

## Repo (head nhánh mặc định, PR còn mở)

| Repo | Head | PR mở |
|---|---|---|
| AA-Ecosys | #722 + #749 (bot) đã merge sau #762 | PR chốt phiên S279 |
| AA-CIS-App | 489a6165 (#1490) | #1467 (bot durations), #1179 (release-please) |
| AA-Booking | 98e98078 (#249) | #200 (bk-045, chờ ≥ 28/11), #161 (release-please) |
| AA-TripPlanner-Web | d5103a73 (#265) | #196 (release-please) |
| AA-Partner | 3ed93c89 (#307) | #133 (release-please) |
| AA-CIS-Infra | 09ea0c48 (#834) | không |

## Cố ý để BẬT / để lại cho phiên sau

- Tenant tổng hợp `aa1093-erase-01` (`9310c702…`, demo/canary) — giữ cho lần xoá thật AA-1093 (B–F) phiên sau.
- Danh tính E2E `e2e-booking-pricing-checker@` (booking-contracting) — cho AA-1091 phiên sau; preset Pricing team của
  `e2e-cis-cs@` CHƯA cấp (owner cấp khi chạy, gỡ sau khi xong).
- Công tắc xoá: Booking `TENANT_ERASE_APPLY_ENABLED=false`, CIS `cis.erasure.saga_apply_enabled` off, TP apply off.
- Writer v2 + s1_generate giữ nguyên (S250). Không cờ wave nào bật.

## Lệch đã xử lý trong lúc chụp

- Booking chạy :128 trong khi mẫu mới nhất là :129 (Terraform apply #834 sau deploy #249) → Deploy Dev Booking lại.
- Hai PR bot của repo gốc (#749 schema dump, #722 infra docs) chưa merge → ship_wave.
