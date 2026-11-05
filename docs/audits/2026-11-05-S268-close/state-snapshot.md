# S268 — snapshot trạng thái cuối phiên (05/11/2026 ~02:05Z)

Kiểm trực tiếp lúc chốt phiên; mọi số trong log / memory / backlog lấy từ đây. Không ghi account ID, ARN hay giá trị secret.

## ECS (cluster aa-cis-dev-cluster)

| Service | Task definition | Image | Running/desired | Rollout | Revision mới nhất của family |
|---|---|---|---|---|---|
| aa-cis-dev-api | :1011 | `dev-25142dae` | 1/1 | COMPLETED | :1011 (khớp) |
| aa-cis-dev-worker | :577 | `dev-25142dae` | 1/1 | COMPLETED | :577 (khớp) |
| aa-booking-dev-api | :98 | `3ef1434b` | 1/1 | COMPLETED | :98 (khớp) |
| aa-crm-dev-api | :130 | `0ce28cec` | 1/1 | COMPLETED | :130 (khớp) |
| aa-crm-dev-web | :106 | `0ce28cec` | 1/1 | COMPLETED | :106 (khớp) |
| aa-crm-dev-portal | — | — | — | — | service không còn trả về (đã gỡ từ S267) |

CIS api và worker cùng SHA `25142dae`.

## Endpoint

| App | Kết quả |
|---|---|
| CIS `/health/ready` | ok, schema **374**, git_sha `25142dae` |
| Booking `/booking/health/ready` | ok, **bk-040** |
| CRM api `/crm/health/ready` | ok, **crm-043** |
| CRM web `/healthz` | 200 (sau redirect) |
| Portal (agency app) `/healthz` | 200 |
| TripPlanner Lambdas browse / assembly | CodeSha256 `dsDF/qUp…` (không đổi từ S267); tp-024 |

## Migration áp trong phiên (DB Migrate thủ công)

| Owner | File | Lớp | Áp lúc (UTC) | Ghi chú |
|---|---|---|---|---|
| CIS | 369 drop `shared.tenants.api_key_hash` | destructive | 04/11 14:48 | DRY RUN ready=true, tech lead duyệt; snapshot `db-migrate-369-41850160705-1` |
| Booking | bk-040 grant `v_from_prices` → cis_app | contract | 04/11 14:56 | |
| CIS | 370 route control | contract | 04/11 15:20 | after-guard chứng minh grant hẹp |
| CIS | 371 llm_route_policy | expand | 04/11 16:28 | auto-apply kẹt sau 336 nên áp tay |
| CIS | 372 ai_usage_hourly + saved views | contract | 04/11 ~17:5x | đổi từ expand sang contract (#1305): bảng tenant_id RLS tắt có chủ đích |
| CIS | 373 llm_role_config.pii_class | contract | 04/11 18:34 | |
| CIS | 374 tenant_addon_request | contract | 04/11 23:52 | |

Migration Apply tự động dừng ở CIS 336 (cố ý chờ tới 10/11 ~12:00Z, AA-1024 D8); `DB_AUTO_APPLY_CONTRACT=false`.

## Hạ tầng

- Terraform Apply Dev (Infra #675, AA-969): 6 thêm, 1 sửa tại chỗ, 0 xoá — alarm `aa-crm-dev-api-5xx-rate`, `aa-crm-dev-api-p95-latency` (INSUFFICIENT_DATA), 4 query Logs Insights `aa-crm-dev/slo/*`, rule SES e2e thêm 1 người nhận.
- Identity load test: user Cognito partner `lt agent` + secret `crm/dev/e2e-test-crm/lt-agent` (cần thêm vào secrets register).

## Bảng job (queued/running, không lọc thời gian)

- `shared.job`: 0 · `booking.job`: 0 · `crm.job`: 2 job định kỳ (`crm_booking_sync`, `crm_heartbeat`) đang queued.
- Không có wave mở.

## Vercel / deploy

- CIS admin: Vercel Deploy `25142dae` success, smoke production có đăng nhập xanh (user E2E role content).
- Agency app (CRM web + studio): Deploy Web Dev `0ce28cec`; smoke portal chạy lại tay run 41945555534: **67/67 xanh**.
- TripPlanner: không đổi trong phiên.

## Repo (head nhánh mặc định, PR còn mở)

| Repo | PR mở |
|---|---|
| AA-Ecosys (root) | #542, #538 (bot sinh docs) |
| AA-CIS-App | #1237, #1212 (dependabot), #1179 (release-please) |
| AA-Booking | #161 (release-please) |
| AA-Partner | #200 (dependabot), #133 (release-please) |
| AA-TripPlanner-Web | #213 (dependabot), #196 (release-please) |
| AA-CIS-Infra | #613, #612 (dependabot) |

Không còn PR của phiên mở.

## Cố ý để BẬT / dở cho phiên sau

- Seed load test AA-969 (`python -m app.seed --apply --load-test 50 … --travellers` trong crm-api): tiến trình chết, không output, không tạo job `crm_intake_process`; trạng thái 50 đại lý chưa xác nhận (RLS). Phiên sau: chạy lại seed (idempotent), không `--travellers` trước, rồi load test.
- Không có cờ wave nào bật.
