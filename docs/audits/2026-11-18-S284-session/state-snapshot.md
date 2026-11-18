# S284 — trạng thái kiểm cuối phiên (18/11/2026 ~16:40 +07)

Nguồn: lệnh live chạy lúc chốt phiên (`aws ecs describe-services` / `describe-task-definition`, health endpoint, `gh api`,
ECS exec đếm bảng job). Chỉ tên và số; không account ID, ARN hay giá trị secret.

## ECS (cluster aa-cis-dev-cluster) — 8 service, tất cả running = desired = 1, rollout COMPLETED, revision đang chạy = revision mới nhất

| Service | Task def | Image (commit) |
|---|---|---|
| aa-cis-dev-api | :1211 | `069a1b1e` (CIS #1589) |
| aa-cis-dev-worker | :780 | `069a1b1e` (cùng api) |
| aa-cis-dev-admin | :67 | `701be528` (CIS #1588) |
| aa-booking-dev-api | :147 | `c2da9fab` |
| aa-booking-dev-admin | :37 | `4b777358` (Booking #273 kit sync) |
| aa-crm-dev-api | :197 | `27b8c56f` (Partner #348) |
| aa-crm-dev-web | :172 | `2d607dc0` (Partner #346 kit sync) |
| aa-tripplanner-dev-web | :20 | `5b5f8e6f` (TripPlanner #280; #281 chỉ CI) |

TripPlanner Lambda browse + assembly: deploy 18/11 06:10Z (cùng CodeSha256).

## Endpoint

| Endpoint | HTTP | git_sha / migration |
|---|---|---|
| CIS `/health/ready` | 200 | `069a1b1e`, schema **454** |
| Booking `/booking/health/ready` | 200 | **bk-059** |
| CRM api `/crm/health/ready` | 200 | **crm-077** |
| CRM web `/healthz` | 200 | `2d607dc0` |
| TripPlanner web `/api/health` | 200 | `5b5f8e6f` |

Migration mới nhất mỗi owner: CIS 454 (447–454 áp trong phiên), bk-059, tp-034 (áp trong phiên), crm-077 (áp trong phiên).
Terraform: Infra #902 (CRM retention floor) và #919 (docs-sync role đọc manifest) đã apply; Infra #904 (security headers)
đã apply.

## Bảng job / wave

`shared.job`: 0 queued/running. `booking.job`: 0. `crm.job`: chỉ các job định kỳ chờ lượt kế (11 kind, 1 dòng mỗi kind;
`crm_stage_date_rule` đang chạy) — bình thường. Không wave mở, không cờ wave bật.

## Cấu hình đổi trong phiên (cố ý giữ)

- Setting `cis.spend.connection_provider_budget_usd` = {acc1 100, acc2 30, acc2-usw2 5, acc3 100, anthropic-direct 150,
  openai-direct 10} (tech lead nhập 14:33). `crm.ai.connection_monthly_cap_usd` = {"acc2": 5} (14:34).
- Connection `acc2`: monthly budget 25 USD, hard stop (agent, tech lead duyệt); ghi chú cũ đã khôi phục.
- `crm.retention.job_dry_run` = off (tech lead), Terraform `JOB_RETENTION_DRY_RUN=false`.
- Tenant giả mới: "E2E Lead Proof Travel" (`e2e-lead-proof`, demo, chỉ TripPlanner), lead route `none`, không override.
- Agency giả "S283 Test Agency": CRM seats trả về 3; AI switch trả về off.

## PR còn mở (cố ý)

- Root #860 bot regenerate infra docs (bot, xem phiên sau).
- CIS #1586 dependabot frontend-security, #1570 release 0.21.0, #1467 CI durations; Booking #270 release, #200 (bk-045
  destructive, giữ); Partner #343 release; TripPlanner #278 release.
- Lane L18 (AA-1135 cold custom range) còn chạy lúc snapshot — xem log phiên.

## Head mặc định mỗi repo

AA-Ecosys `fae82f4d` (#878) · AA-CIS-App `069a1b1e` (#1589) · AA-Booking `4b777358` (#273) · AA-Partner `27b8c56f` (#348) ·
AA-TripPlanner-Web `44aa203b` (#281) · AA-CIS-Infra `72d85ece` (#919).
