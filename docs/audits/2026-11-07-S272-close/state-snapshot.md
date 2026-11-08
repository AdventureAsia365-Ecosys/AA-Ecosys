# S272 — Snapshot trạng thái cuối phiên (08/11/2026 ~09:50 +07)

Kiểm live bằng lệnh một dòng (STS acc2, ECS, endpoint, Lambda, GitHub API, ecsx đọc `shared.job`). Chỉ tên và số; không
account ID, ARN hay giá trị secret.

## AWS / ECS (cluster `aa-cis-dev-cluster`)

| Service | Task def đang chạy (= revision mới nhất) | Rollout | Running/desired | Image |
|---|---|---|---|---|
| aa-cis-dev-api | :1051 | COMPLETED | 1/1 | `dev-f251917e` |
| aa-cis-dev-worker | :617 | COMPLETED | 1/1 | `dev-f251917e` (cùng SHA với api) |
| aa-booking-dev-api | :111 | COMPLETED | 1/1 | `a76de8c0` |
| aa-crm-dev-api | :142 | COMPLETED | 1/1 | `bfc8eb04` |
| aa-crm-dev-web | :116 | COMPLETED | 1/1 | `a317d79e` |
| aa-cis-dev-admin | :10 | COMPLETED | 1/1 | `dev-dd07872b` |
| aa-booking-dev-admin | :5 | COMPLETED | 1/1 | `a76de8c0` |

`aa-crm-dev-portal` không còn (portal gộp vào crm-web từ R3; CLAUDE.md đã sửa danh sách service trong PR chốt phiên).
Booking `main` = `f7f435d6`, ECS `a76de8c0`: commit giữa hai bản chỉ là CI (#208), không cần deploy.

## Endpoint

- CIS `/health` 200; `/health/ready` ok, schema **390**, git_sha `f251917e`.
- Booking `/booking/health` 200; ready ok, schema **bk-044**.
- CRM `/crm/health/ready` ok, schema **crm-046**; CRM web `/healthz` 200.
- TripPlanner web `/api/health` ok, git_sha `ffca93c6` (Vercel); browse countries 200. Lambda browse + assembly cùng
  CodeSha256, sửa lúc 07/11 18:28 UTC (deploy của #239).
- Staff web: `aa-cis.` → cis-admin sha `dd07872b`; `booking.` → booking-admin sha `a76de8c0`.
- `POST /auth/booking-token` → 404 (cầu CIS → Booking đã gỡ).

## Migration mới nhất mỗi owner

CIS **390** (389, 390 apply trong phiên; 336 cố ý hoãn tới ≥ 10/11 nên 389/390 apply vượt thứ tự) · Booking **bk-044** ·
TripPlanner **tp-026** (apply trong phiên) · CRM **crm-046**.

## Vercel

Chỉ còn project `aa-tripplanner` (Production `ffca93c6`). `aa-cis-frontend` và `aa-booking-admin` đã xoá (AA-911).

## Bảng job và wave

`shared.job`: 0 nhóm queued/running; 0 wave mở; 24 giờ qua 270 job succeeded. `booking.job` / `crm.job`: không kiểm
trong snapshot này (cần DB Migrate `mode=check`); các deploy Booking/CRM trong phiên đều qua cổng job của CI.

## Cờ / thứ cố ý để nguyên

- Worker CIS: `T9_FAQ_LLM_FILTER=on` (đã có từ trước, quyết định của tech lead — không đổi).
- Cờ mới của W3 đều **không đặt** (= hành vi main): `T9_REGRESSION_GUARD_MODE`, `T9_SEO_BUILDER`, `T2_ORCHESTRATOR`.
- CRM job `crm_tp_lead_pull` chạy mỗi phút, trả `not_configured` cho tới khi Infra #721 apply (M2M route + secret).
- Secret `aa-cis/dev/booking-jwt-signing-key` đã lên lịch xoá 07/11 (hồi phục tới 14/11).
- Log CIS 15 phút sau deploy #1380: 0 `RouteTableError` / lỗi import `t2_orchestrator`.

## Repo (nhánh mặc định, PR còn mở)

| Repo | Head | PR còn mở |
|---|---|---|
| AA-Ecosys | `4c580ecb` | #616 (nháp, chờ Infra #721), #608 (bot docs infra, đang ship) + PR chốt phiên |
| AA-CIS-App | `f251917e` | #1237, #1212, #1179 (cũ, từ trước phiên) |
| AA-Booking | `f7f435d6` | #209 (bot kit sync, đang ship), #200 (nháp), #161 |
| AA-TripPlanner-Web | `ffca93c6` | #236 (nháp, chờ Infra #722), #213 (dependabot), #196 (release-please) |
| AA-Partner | `bfc8eb04` | #246 (bot kit sync, đang ship), #240, #200, #133 |
| AA-CIS-Infra | `efd75354` | #722 (nháp), #721 (nháp) — cần apply LOCAL MFA; #613, #612 (dependabot) |
