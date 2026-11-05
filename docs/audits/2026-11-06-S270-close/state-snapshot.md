# S270 — snapshot trạng thái cuối phiên (06/11/2026 ~03:10 +07, tức 05/11 ~20:10Z)

Kiểm trực tiếp lúc chốt phiên; mọi số trong log / memory / backlog lấy từ đây. Không ghi account ID, ARN hay giá trị secret.

## ECS (cluster aa-cis-dev-cluster)

| Service | Task definition | Image | Running/desired | Rollout | Revision mới nhất của family |
|---|---|---|---|---|---|
| aa-cis-dev-api | :1021 | `dev-2d9374c4` | 1/1 | COMPLETED | :1021 (khớp) |
| aa-cis-dev-worker | :587 | `dev-2d9374c4` | 1/1 | COMPLETED | :587 (khớp) |
| aa-booking-dev-api | :108 | `5066f753` | 1/1 | COMPLETED | :108 (khớp) |
| aa-crm-dev-api | :139 | `8575fada` | 1/1 | COMPLETED | :139 (khớp) |
| aa-crm-dev-web | :112 | `8575fada` | 1/1 | COMPLETED | :112 (khớp) |

api và worker CIS cùng SHA `2d9374c4` (#1332). `main` CIS đã tới `590796a3` (#1331 + #1334, chỉ frontend → Vercel deploy success, không đổi image).

## Health + migration

| App | /health | ready | Migration mới nhất |
|---|---|---|---|
| CIS | ok 0.18.0 `2d9374c4` | ok | **378** (áp tay `--allow-out-of-order` vì 336 còn chờ) |
| Booking | ok 0.14.0 `5066f753` | ok | **bk-044** (không đổi) |
| CRM api | ok 0.11.0 `8575fada` | ok | **crm-046** (không đổi) |
| CRM web (portal) | `/api/healthz` ok, `studio: merged`, `8575fada` | | |
| TripPlanner | Lambda browse / assembly / jobs cập nhật 05/11 19:20Z (TP #227, cùng code hash) | | **tp-025** (tenant_id + RLS shadow, DB Migrate apply) |

`DB_AUTO_APPLY_CONTRACT=false` vẫn tắt (chờ 336, ≥10/11 ~12:00Z).

## Bảng job

`shared.job` 0 queued/running · `booking.job` 0 · `crm.job` 2 job định kỳ (`crm_heartbeat` queued, `crm_booking_sync` running). Không wave mở.

## AI gateway

- Route control **version 6**, preset `prefer_anthropic_api` (không đổi).
- Connection: acc2 ON ok · acc3 ON (7 model chính vẫn `access_denied`: Claude 5.x, GPT-6, GPT-5.6) · anthropic-direct ON
  (trần 150 USD, MTD 1,96 USD) · openai-direct ON (trần 10 USD, MTD 0,06 USD) · typesafe, dataforseo, geoapify ON.
- **Chi tiêu LLM tháng 11 tới lúc chốt: 2,05 USD** (gần hết là AA-741 phase 0 ≈ 2,0 USD).
- Lỗi 24 h theo stage: `t7_debate_judge` 306, `t2_judge` 121, `t10_judge` 12 `access_denied` — **trước** khi #1332 deploy; sau
  deploy các nấc acc3 mở circuit bị dời xuống cuối, không ghi dòng refused riêng (route test NATURAL t2_judge 11/11).

## Repo (head nhánh mặc định | PR mở)

| Repo | Head | PR mở |
|---|---|---|
| AA-Ecosys | `24bbfdfb` (+ PR chốt phiên này) | — |
| AA-CIS-App | `590796a3` (#1334 merged 20:14Z) | bot (#1237, #1212, #1179) |
| AA-Booking | `5066f753` | bot (#161) |
| AA-TripPlanner-Web | `954b9257` | bot (#213, #196) |
| AA-Partner | `8575fada` | bot (#200, #133) |
| AA-CIS-Infra | `955b2373` | bot (#613, #612) |

## Cố ý để BẬT / giữ lại cho phiên sau

- Route control v6 ưu tiên Anthropic API.
- 4 tenant audit `audit-atlas-hearth`, `audit-terra-family`, `audit-trail-pulse`, `audit-wildkind-travel` (AA-741 phase 1–2)
  + agency CRM tổng hợp của chúng; danh tính partner E2E là editor ở cả 4.
- User E2E customer_success (Dev-only, chỉ đọc, book = atlas-hearth) — bằng chứng AA-1035.
- Đại lý demo hư cấu `aa1037-ledger-lane` + hoá đơn AAS/AAT mẫu (bằng chứng AA-1037).
- 23 video UAT vòng 1 ở `tools/uat/out/` (local, chưa lên Drive).
- Hook PII `.claude/hooks/pilot-pii-guard.sh`; H3 (AA-1008): Visual + Kit consumers là check bắt buộc trên merge queue.
