# S288 — trạng thái kiểm cuối phiên (23/11/2026, ~21:15 +07)

Nguồn: lệnh đọc live lúc chốt phiên (AWS CLI acc2, health endpoint, GitHub API, bảng job qua ECS exec chỉ đếm).

## ECS (cluster aa-cis-dev-cluster)

| Service | Task def | Running/desired | Rollout | Image |
|---|---|---|---|---|
| aa-cis-dev-api | :1256 | 1/1 | COMPLETED | dev-8019c841 (#1649) |
| aa-cis-dev-worker | :825 | 1/1 | IN_PROGRESS → cùng SHA | dev-8019c841 |
| aa-cis-dev-admin | :89 | 1/1 | COMPLETED | dev-b8d040cb (#1647) |
| aa-booking-dev-api | :163 | 1/1 | COMPLETED | 79a8b389 (#307) |
| aa-booking-dev-admin | :58 | 1/1 | COMPLETED | 79a8b389 |
| aa-crm-dev-api | :214 | 1/1 | COMPLETED | 6dce1f2c (#381) |
| aa-crm-dev-web | :187 | 1/1 | COMPLETED | d9831356 |

## Health và migration

- CIS `/health/ready`: ok, schema **473**, git_sha 8019c841.
- Booking `/booking/health/ready`: ok, schema **bk-066**.
- CRM `/crm/health/ready`: ok, **crm-085**; CRM web `/healthz` ok (d9831356, 0.14.0).
- TripPlanner `/api/health`: ok (35ad6b11, 0.17.0).
- Migration áp trong phiên: CIS 470, 471, 472, 473; Booking bk-064, bk-065, bk-066.

## Bảng job

shared.job 0, booking.job 0, crm.job 0 (queued/running, không lọc thời gian).

## Repo (head nhánh mặc định)

| Repo | Head | PR còn mở |
|---|---|---|
| AA-Ecosys | bab23af3 (schema reference tự sinh #957) | #958 dependabot |
| AA-CIS-App | 8019c841 (#1649) | #1645 release 0.22.0, #1638 / #1586 dependabot, #1467 bot |
| AA-Booking | 79a8b389 (#307) | #305 dependabot, #302 release 0.18.0, #276 kit sync, #200 bk-045 (cũ, chờ ≥ 28/11) |
| AA-TripPlanner-Web | 35ad6b11 | #293 dependabot |
| AA-Partner | 6dce1f2c (#381) | #380 release 0.15.0, #355 kit sync |
| AA-CIS-Infra | 0a13dd10 (copy CIS 473) | #977 dependabot, #935 (cũ, WAF geo sau MFA admin) |

## Thứ cố ý để BẬT / TẮT cho phiên sau

- Guard dữ kiện T9 `cis.llm.fact_instruction_guard`: **TẮT** (mặc định), chờ tech lead quyết.
- Bậc số khách `price_pax_bands` v2 (1, 2, 3, 4, 5–7, 8–10, 11+) có hiệu lực từ 23/11; bảng giá tính đổi ở lần tính lại kế tiếp.
- Tài khoản owner E2E trên Dev (A10h) đang hoạt động; gỡ theo ADR 0006a A10h.
- Không có wave mở.

## Lệch so với điều phiên tưởng

- CIS admin vẫn ở b8d040cb: #1649 không đổi file trong đường deploy của admin (chỉ api/worker), nên đúng.
- CI CIS đỏ cả chiều do `sentry-sdk` 3.0.0 và `redis` 8.2.0 phát hành cùng ngày, cộng một test view-as có NOW cố định: sửa ở CIS #1650 (merged 495a715b).
