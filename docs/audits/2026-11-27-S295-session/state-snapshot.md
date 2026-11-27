# S295 — trạng thái live cuối phiên (27/11/2026 ~13:35 +07)

Nguồn: lệnh một dòng chạy lúc chốt phiên (ECS describe-services, list-task-definitions, curl health, ECS exec đếm job, gh). Không ghi account ID, ARN hay secret.

## ECS (cluster aa-cis-dev-cluster) — 8/8 running = desired, rollout COMPLETED; revision đang chạy = revision mới nhất của family

| Service | Task def | Git sha (health) |
|---|---|---|
| aa-cis-dev-api | :1301 | dd1a441d (CIS #1718, DB-01) |
| aa-cis-dev-worker | :870 | cùng image api |
| aa-cis-dev-admin | :110 | e332776f |
| aa-booking-dev-api | :176 | 8844fd00 (không đổi) |
| aa-booking-dev-admin | :70 | không đổi |
| aa-crm-dev-api | :226 | e9e3977e |
| aa-crm-dev-web | :197 | 7a972268 (Partner #404, DB-01 allow-list) |
| aa-tripplanner-dev-web | :32 | 4d6919e7 (không đổi) |

## Endpoint
- CIS `/health` + `/health/ready` 200, schema 494; Booking `/booking/health` + `/ready` 200, bk-075; CRM `/crm/health` + `/ready` 200, crm-090; CRM web `/healthz` 200; TripPlanner `/api/health` 200; CIS admin `/api/healthz` 200.
- Migration mới nhất không đổi trong phiên: CIS 494, bk-075, crm-090, tp không đổi.
- DB-01 kiểm live (host portal, chưa đăng nhập): `/api/tenant/v1/tours/{id}/full` 404, `/api/tenant/v1/tours/{id}` 404, `/api/tenant/openapi.json` 404; `/api/tenant/v1/billing` và `/v1/tours/pool` 401.

## Bảng job, wave, cờ
- `shared.job` 0 queued/running; wave mở 0 (ECS exec 27/11 ~12:32).
- Không có cờ nào cố ý để BẬT thêm trong phiên này. Giữ nguyên từ S294: `cis.llm.fact_instruction_guard` On.
- Mật khẩu master RDS đã xoay 27/11 (N2): secret `aa-cis/dev/rds` có version mới, GitHub `TF_VAR_DB_PASSWORD` đã cập nhật, DB Migrate đăng nhập được.

## AWS ngoài app (đổi trong phiên)
- Well-Architected Tool: workload "AA Ecosystem (Dev)" (3 lens: Framework, Generative AI, SaaS), 98 câu trả lời có ghi chú, milestone "S295 baseline 2026-11-27". 0 USD.
- Không bật dịch vụ trả phí nào. GuardDuty, Security Hub, Inspector, Macie, DNS Firewall: mới ghi kế hoạch (AA-873), chưa bật.

## Máy agent + GitHub
- gh: chỉ `pqnghiep1354`, scopes `gist, project, read:org, repo, workflow` (`admin:org` đã bỏ); `adventure365` (break-glass) đã đăng xuất khỏi gh.
- Token GitHub của MCP chuyển khỏi `~/.zshrc` sang file 600; `~/.zshrc` 600.
- Vercel GitHub App đã gỡ khỏi org. 2 secret `E2E_ADMIN_*` của CIS để nguyên (không workflow nào dùng).

## PR
- Merged trong phiên (sau họp): CIS #1718 `dd1a441d`, Partner #404 `7a972268`, root #1043 `b108667c` (bot infra docs).
- Đang trong hàng merge lúc chụp: CIS #1719 (SEC-11 vào sổ báo cáo, chỉ docs/catalog, không đổi code chạy).
- Còn mở có chủ ý: CIS #1717/#1710/#1709/#1676 (nháp), #1645/#1638/#1467; Booking #336/#331 (nháp), #330/#302/#276; Partner #380/#355; TripPlanner #295; Infra #1043/#1042 (nháp, chuỗi AA-1061 ≥28/11), #935 (chờ MFA admin).
- Chưa commit `.claude/settings.json` (có ID acc2 + e-mail cá nhân; không bao giờ commit).
