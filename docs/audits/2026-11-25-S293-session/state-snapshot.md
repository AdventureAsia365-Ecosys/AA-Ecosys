# S293: state snapshot cuối phiên (25/11/2026, ~16:55 +07)

Kiểm trực tiếp (lệnh một dòng, profile aa365-admin). Chỉ tên và số, không account ID, ARN hay secret.

## ECS (cluster aa-cis-dev-cluster), tất cả running = desired = 1, rollout COMPLETED

| Service | Task def | Image / SHA |
|---|---|---|
| aa-cis-dev-api | :1295 | 7886cb4c (`/health` git_sha 7886cb4c) |
| aa-cis-dev-worker | :864 | 7886cb4c (cùng SHA với api) |
| aa-cis-dev-admin | :106 | dev-deeb3e2e |
| aa-booking-dev-api | :175 | 591d7397 (không đổi) |
| aa-booking-dev-admin | :69 | không đổi |
| aa-crm-dev-api | :220 | 1f7c0136 (không đổi) |
| aa-crm-dev-web | :191 | không đổi |
| aa-tripplanner-dev-web | :29 | aa78d945 (không đổi) |

## Endpoint

- CIS `/health` 200 (7886cb4c), `/health/ready` status ok, schema_version 494.
- Booking `/booking/health` 200, CRM `/crm/health` 200, TripPlanner `/api/health` 200.

## Migration

- CIS: 490, 491 (AA-1154), 492, 493 (AA-1142 follow-up), 494 (AA-1180) áp trong phiên. Mới nhất 494. bk / crm / tp không đổi.
- Root #1014 (bot db-schema-reference) đã merge.

## Bảng job

- `shared.job`: 0 queued/running lúc chốt. Job `writing_memory_r0` baseline (0 USD, dùng kiểm AA-1178) đã xong trước apply.
- Job mới chạy đều: `ops_external_check` (làn monitor, 15′), phần `assist` của `ops_status_sample`.

## PR còn mở (cố ý)

- CIS #1702 (chỉ test: admin evidence) đang ship; #1676 savepoint, #1645 release, #1638 dependabot actions, #1586 dependabot frontend, #1467 bot: **giữ tới sau thứ Năm** (trừ #1702).
- Booking #331, #330, #302, #276, #200; Partner #380, #355; TP #295; Infra #935: **giữ tới sau thứ Năm** (Booking #200 = drop bảng, ≥ 28/11).
- Root: PR chốt phiên S293.

## Smoke thứ Năm (sau deploy cuối 7886cb4c / admin deeb3e2e)

- 4/4 luồng đạt, đọc thôi: đăng nhập CIS, Content workspace (danh sách, tour, tạo mới 390), Compliance readiness 5 tab, Booking SUP-000019 tab Bank accounts ("Waiting for approval", chi tạm dừng) + Bills.
- Đăng xuất từ `/admin/overview` OK; `/admin` gốc (không có trang) đẩy về `/login`: có từ trước, không phải đường demo (ghi follow-up sau thứ Năm).
- Ảnh: `live/thu-smoke-*.png`.

## Cố ý để BẬT

- `cis.t9.blog_claim_rule` On, hook warn (từ S292).
- External checks từ worker (`cis.ops.external_check_sources` = worker, github).

## Ghi chú

- Đổi tài khoản Claude ~13:10 (giới hạn 5 giờ). Lane a, d, e chạy lại bằng resumeFromRunId, không mất việc.
- Đăng Jira bị auto mode chặn (nháp chưa hiện nguyên văn cho tech lead). Nháp: `jira-drafts.md`.
