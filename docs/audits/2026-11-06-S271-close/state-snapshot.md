# S271 — Snapshot trạng thái chốt phiên (07/11/2026, ~01:50 +07)

Kiểm live bằng lệnh, không chép từ chat. Chỉ tên và số, không giá trị secret.

## Tài khoản
- STS `aa365-admin`: role `nghiep-admin-8h-session` trên acc2, MFA hết hạn 09:01 +07 07/11.
- Tài khoản Claude chuyển trong phiên: info → admin → info. Sổ link artifact ở `docs/artifacts/registry.json`.

## ECS (cluster `aa-cis-dev-cluster`), tất cả COMPLETED, 1/1
| Service | Task def |
|---|---|
| aa-cis-dev-api | aa-cis-dev-api:1037 |
| aa-cis-dev-worker | aa-cis-dev-worker:603 |
| aa-booking-dev-api | aa-booking-dev-api:110 |
| aa-crm-dev-api | aa-crm-dev-api:139 |
| aa-crm-dev-web | aa-crm-dev-web:114 |
| aa-cis-dev-admin | aa-cis-dev-admin:5 |
| aa-booking-dev-admin | aa-booking-dev-admin:4 |

api và worker CIS cùng SHA `51b6b150` (`/health` = `/health/ready` = `51b6b150`).

## Endpoint
- CIS `/health` 200, version 0.18.0, `git_sha` 51b6b150; `/health/ready` schema_version **385**.
- Booking `/booking/health` 200, version 0.14.0, `git_sha` c7223d5a; `/health/ready` schema **bk-044**.
- `POST /auth/booking-token` → **404** (cầu đăng nhập CIS → Booking đã gỡ, #1339).

## Migration mới nhất theo owner
CIS **385** (383 route, 384 prompt eval v2, 385 llm_cassette — đều apply trong S271), TripPlanner tp-025, Booking bk-044, CRM crm-046. File reference (Verified 06/11 10:25 UTC) còn ghi CIS 382 → chờ PR bot `bot/db-schema-reference`.

## Lambda TripPlanner
`aa-tripplanner-dev-browse` và `-assembly`: LastModified 2026-11-06 08:29 UTC, cùng CodeSha256 `wrS3zT8D…`.

## Bảng job
`shared.job` 0 queued/running · `booking.job` 0 queued/running · không wave.

## Repo (nhánh mặc định, commit cuối)
| Repo | Commit | PR còn mở |
|---|---|---|
| AA-CIS-App | 51b6b150 | bot: #1237, #1212 (deps), #1179 release 0.19.0 |
| AA-Booking | 9383744c | #200 bk-045 (destructive, từ 28/11), #161 release |
| AA-Partner | ab86d355 | #238 sync aa_llm (đang merge), #240/#200 deps, #133 release |
| AA-TripPlanner-Web | 8e5f81c6 (#232 merged) | #213 deps, #196 release |
| AA-CIS-Infra | 75ddf666 | #613, #612 (deps bot) |
| AA-Ecosys (gốc) | 2bdb70d5 | #602 guard (đang merge), #589/#588/#591 (đang merge), PR chốt phiên |

## AI gateway (cuối phiên)
- Route version 7 sau migration 383: writer không còn GPT-6, judge không còn nova-lite (0 vi phạm, kiểm live).
- acc3: 5 model ok / 7 bị từ chối; lượt từ chối hiển thị là "từ chối dự kiến" (#1348), không còn tính là lỗi.
- Chi tháng 11 (tới 06/11): khoảng 11,3 USD trên mọi connection; R2 rerun 2,46 USD (invalid, đã tìm ra nguyên nhân gốc).

## W0 (ADR 0020) live check, 0 USD
- R2 chạy thử t9_blog: đối chứng **18/18** cặp (trước 0/15), ước tính từ ledger 0,175 USD/bài, không có lý do từ chối.
- Job `quality_funnel_watch` đã đăng ký (60 kind).
- `shared.llm_cassette`: 0 dòng lúc kiểm — chưa có lần gọi model nào sau deploy; probe 05:02Z 07/11 sẽ ghi dòng đầu → kiểm ở S272.
- Funnel baseline 8 tuần: blog T9 đạt lần đầu 10,4% / giữ 35,7% / 0,079 USD mỗi bài; S1 47,8%; T2 64%.

## Lệch / còn dở (ghi rõ, không giả định)
- Lane l22 (guard test ở app) đang chạy khi chụp snapshot; PR của nó (nếu có) ship ở cuối phiên hoặc S272.
- AA-911 phần còn lại (xoá project Vercel `aa-cis-frontend`, hẹn xoá secret khoá ký cũ) cần tech lead duyệt → S272.
- Partner main: check Visual đỏ trên `912b4f8f` (chưa điều tra).
