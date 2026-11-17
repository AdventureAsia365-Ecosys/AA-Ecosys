# S283 — trạng thái kiểm cuối phiên (17/11/2026 ~15:50 +07)

Nguồn: lệnh live chạy lúc chốt phiên (ECS describe-services, health endpoint, `gh pr list`, ECS exec đọc `shared.job`).
Chỉ tên và số; không account ID, ARN hay giá trị secret.

## ECS (cluster aa-cis-dev-cluster) — 8 service, tất cả running = desired, rollout COMPLETED

| Service | Task def | Ghi chú |
|---|---|---|
| aa-cis-dev-api | :1196 | image `c0f8a2ee` (CIS #1566) |
| aa-cis-dev-worker | :765 | cùng image với api |
| aa-cis-dev-admin | :55 | CIS #1566 (trang Spend controls) |
| aa-booking-dev-api | :143 | Booking #262 `31b61227` (dòng giảm giá) |
| aa-booking-dev-admin | :31 | không đổi trong phiên |
| aa-crm-dev-api | :191 | Partner #335 `24722bc8` (crm-076) |
| aa-crm-dev-web | :166 | Partner #334 `b6e770b9` (cổng CSV/Stripe) |
| aa-tripplanner-dev-web | :17 | TripPlanner #274 `58eace37` (brand đại lý) |

Service `aa-crm-dev-portal` không còn (đã gộp vào `aa-crm-dev-web`); skill aa-session còn ghi 9 service → sửa skill.

## Endpoint

| Endpoint | HTTP | git_sha / migration |
|---|---|---|
| CIS `/health/ready` | 200 | `c0f8a2ee`, schema **446** |
| Booking `/booking/health/ready` | 200 | **bk-058** |
| CRM api `/crm/health/ready` | 200 | **crm-076** |
| CRM web `/healthz` | 200 | `b6e770b9` |
| TripPlanner web `/api/health` | 200 | `58eace37` |

Migration mới nhất mỗi owner: CIS 446 (443, 444, 445, 446 áp trong phiên), bk-058, tp-033, crm-076 (áp trong phiên).

## Bảng job / wave

`shared.job`: 0 queued/running. `booking.job`, `crm.job`: rảnh theo kiểm idle của DB Migrate (lần apply cuối 15:3x).
Không wave mở. Không cờ wave nào bật.

## PR còn mở (cố ý)

- CIS #1567 (migration 447) + #1568 (studio 402 / thông báo), TripPlanner #276, PR code Partner (chưa push):
  AA-1126 L16 — chờ thiết kế lại đường báo đại lý của TripPlanner (447 đụng guard 274/351). Đầu S284.
- Bot / dependabot: root #766 (infra docs), CIS #1561, #1467, Booking #263, TripPlanner #275, Infra #876; Booking #200
  (bk-045 B2C drop, AA-1061, từ 28/11).
- Release-please tuần W47 (CIS #1538, Booking #261, Partner #329, TripPlanner #272): đang merge lúc chốt.

## Thứ cố ý để bật / theo dõi cho phiên sau

- Key cũ của IAM user gốc **Inactive** (xoá từ 18/11) + file sao lưu credentials `.bak-s283-*` (xoá cùng lúc).
- Collector Delivery: kiểm Merge queue của Booking/Partner sau lượt hằng giờ (lượt đầu 0 entry).
- Budget acc3 = 100 USD (apply local, plan 0/1/0).

## Kiểm lại sau release-please (17/11 ~16:20 +07)

- Release PR đã merge: CIS #1538 (114c0c1b), Booking #261 (71407286), Partner #329 (7a5c2b98), TripPlanner #272 (6c5ec5ac).
- ECS: 8 service COMPLETED, running = desired; chỉ `aa-crm-dev-web` đổi :166 → :167 (deploy 7a5c2b98, `/healthz` 0.13.0).
  CIS api :1196 / worker :765 / admin :55, booking-api :143, booking-admin :31, crm-api :191, tp-web :17 không đổi.
- Health 200: CIS c0f8a2ee (0.19.0), Booking 31b61227 (0.15.0), CRM api 24722bc8 (0.12.0), CRM web 7a5c2b98 (0.13.0),
  TripPlanner 58eace37 (0.15.0). Release PR của CIS / Booking / TripPlanner chỉ đổi CHANGELOG, không deploy lại API.
