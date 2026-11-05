# S269 — snapshot trạng thái cuối phiên (05/11/2026 ~11:00Z)

Kiểm trực tiếp lúc chốt phiên; mọi số trong log / memory / backlog lấy từ đây. Không ghi account ID, ARN hay giá trị secret.

## ECS (cluster aa-cis-dev-cluster)

| Service | Task definition | Image | Running/desired | Rollout | Revision mới nhất của family |
|---|---|---|---|---|---|
| aa-cis-dev-api | :1016 | `dev-4aed550d` | 1/1 | COMPLETED | :1016 (khớp) |
| aa-cis-dev-worker | :582 | `dev-4aed550d` | 1/1 | COMPLETED | :582 (khớp) |
| aa-booking-dev-api | :104 | `f81ecac6` | 1/1 | COMPLETED | :104 (khớp) |
| aa-crm-dev-api | :136 | `15c7de1c` | 1/1 | COMPLETED | :136 (khớp) |
| aa-crm-dev-web | :110 | `15c7de1c` | 1/1 | COMPLETED | :110 (khớp) |

api và worker CIS cùng SHA `4aed550d`.

## Health + migration

| App | /health | ready | Migration mới nhất |
|---|---|---|---|
| CIS | ok `4aed550d` | ok | **377** (375, 376, 377 áp trong phiên bằng DB Migrate check → apply) |
| Booking | ok `f81ecac6` | ok | **bk-044** (bk-041 tự áp; bk-042, bk-043, bk-044 áp tay) |
| CRM | ok `15c7de1c` | ok | **crm-046** (crm-044, crm-045, crm-046 áp tay) |
| CRM web | `/healthz` 301 (chuyển hướng, như trước) | | |
| TripPlanner | không đổi | | Lambda browse / assembly `dsDF/qUp…`, tp-024 |

`DB_AUTO_APPLY_CONTRACT=false` vẫn tắt (chờ 336, ≥10/11 ~12:00Z) — mọi file contract phải check → apply tay.

## Bảng job

`shared.job` 0 queued/running · `booking.job` 0 · `crm.job` 3 job định kỳ (`crm_booking_sync`, `crm_heartbeat`, `crm_membership_pull`). Không wave mở.

## AI gateway

- Connection `anthropic-direct` **ON** (secret tạo 05/11, trần 150 USD/tháng hard stop). 13/13 deployment Claude API probe ok sau CIS 376.
- Route control **version 6**, preset `prefer_anthropic_api` (Claude 4.x + 5.x gọi API trước, acc3 sau). Quay về ưu tiên AWS: preset Prefer AWS (revert v3–v5 bị `attempt_cap` chặn sau 376).
- acc3: 7 model chính (Claude 5.x, GPT-6) vẫn `access_denied`. openai-direct ON (trần 10 USD).
- Chi tiêu LLM tháng 11 tới lúc chốt: ~0,03 USD (probe + kiểm).

## Repo (head nhánh mặc định | PR mở | CI cuối)

| Repo | Head | PR mở | CI cuối |
|---|---|---|---|
| AA-Ecosys | `0bce6484` (+ PR chốt phiên này) | — | Docs sync success |
| AA-CIS-App | `4aed550d` | chỉ bot (#1237, #1212 dependabot, #1179 release) | success |
| AA-Booking | `f81ecac6` | chỉ bot (#161 release) | success |
| AA-TripPlanner-Web | `11c7b931` | chỉ bot (#213, #196) | success |
| AA-Partner | `15c7de1c` | chỉ bot (#200, #133) | Visual success |
| AA-CIS-Infra | `5e5e7bbd` | chỉ bot (#613, #612) | DB Isolation Probe success |

## Cố ý để BẬT cho phiên sau

- Route control v6 ưu tiên Anthropic API (tech lead yêu cầu "tạm thời").
- Hook PII `.claude/hooks/pilot-pii-guard.sh` chạy trong mọi phiên agent.
- 50 đại lý tổng hợp `lt-01..lt-50` trong CRM (cho load test sau).
- Membership owner của `harbour-lights` trong tenant canary Atlas & Hearth + add-on Trip planner đã duyệt (bằng chứng AA-1036).
