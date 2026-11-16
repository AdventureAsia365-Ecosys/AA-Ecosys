# Snapshot trạng thái cuối phiên S282 (16/11/2026, ~13:30 UTC)

Đọc live, chỉ tên và số (không account ID, ARN hay giá trị secret).

## AWS

- STS: acc2 (profile `aa365-admin`). Phiên MFA tới 06:16 +07 ngày 17/11.

## ECS (`aa-cis-dev-cluster`)

| Service | Revision đang chạy | Image | Running/desired | Rollout |
|---|---|---|---|---|
| aa-cis-dev-api | :1185 | dev-45790f6b | 1/1 | COMPLETED |
| aa-cis-dev-worker | :754 | dev-45790f6b (cùng SHA với api) | 1/1 | COMPLETED |
| aa-cis-dev-admin | :50 | dev-1359b612 | 1/1 | COMPLETED |
| aa-booking-dev-api | :142 | abbf00e9 | 1/1 | COMPLETED |
| aa-booking-dev-admin | :31 | abbf00e9 | 1/1 | COMPLETED |
| aa-crm-dev-api | :189 | 183a98c8 | 1/1 | COMPLETED |
| aa-crm-dev-web | :164 | 183a98c8 | 1/1 | COMPLETED |
| aa-tripplanner-dev-web | :15 | 766d728d | 1/1 | COMPLETED |

Revision mới nhất của mỗi family (cis api/worker, crm api/web, booking api) chính là revision đang chạy.

## Endpoint

| Endpoint | HTTP | Kết quả |
|---|---|---|
| CIS `/health/ready` | 200 | ok, schema 442, git 45790f6b |
| Booking `/booking/health/ready` | 200 | ok, bk-058 (git abbf00e9 ở `/booking/health`) |
| CRM `/crm/health/ready` (portal.) | 200 | ok, crm-075 |
| CRM web `/healthz` (portal.) | 200 | ok, 183a98c8 |
| TripPlanner web `/api/health` | 200 | ok, 766d728d (PR #271 chỉ đổi Lambda) |
| TripPlanner browse `/api/browse?resource=countries` | 200 | Lambda browse cập nhật 12:41Z (Deploy Lambdas 27e84bf7 success) |

Migration mới nhất: CIS 442, bk-058, tp-033, crm-075.

## Bảng job

- `shared.job`: rảnh lúc chụp. Không wave mở.
- Lượt bù PAA miễn phí (job `tour_paa_backfill`, paid=false) đã xong: 239 tour bù từ kho, 0 SERP, 0 lỗi; độ phủ PAA
  839/844 (99,4 %).

## Repo

| Repo | Head | PR còn mở |
|---|---|---|
| AA-Ecosys | master a0ab2ef0 | #766 bot (infra docs) + root PR chốt phiên S282 |
| AA-CIS-App | main 1359b612 | release-please #1538, bot #1467 |
| AA-Booking | main abbf00e9 | release-please #261, #200 (bk-045, chờ ≥ 28/11) |
| AA-TripPlanner-Web | main 27e84bf7 | release-please #272 |
| AA-Partner | main 183a98c8 | release-please #329 |
| AA-CIS-Infra | main 39b2d353 | dependabot #876 |

Release-please tuần W47 đã merge cả 4 sáng nay; các PR release mới để tuần W48.

## Cố ý để BẬT / còn lại

- Sen Vàng (đại lý thử): add-on CRM Core trial tới 30/11, override campaigns, `crm.search.enabled`,
  `crm.release.preview` bật — giữ để thử tiếp.
- Research tự động (AA-1122): **tắt**; tháng 11 đã tiêu 12,53 USD > trần 5 USD nên mọi lượt trả phí bị chặn tới 01/12.
- Lịch hằng giờ của Delivery (AA-1108) chưa lần nào chạy: root PR này lưu lại cron (phút 17) để GitHub đăng ký lại.
- acc2 OrganizationAccountAccessRole: giữ tới khi ký phụ lục TrueIDC.
