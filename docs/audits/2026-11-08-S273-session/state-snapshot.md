# S273 — snapshot trạng thái cuối phiên (09/11/2026 ~06:15 +07)

Kiểm live, chỉ tên/số, không giá trị secret.

## AWS / ECS (acc2, cluster aa-cis-dev-cluster)

- STS: role `nghiep-admin-12h` còn hạn (tới ~07:15 +07).
- Mọi service `rolloutState` COMPLETED, 1/1:
  - `aa-cis-dev-api:1064`, `aa-cis-dev-worker:630` (cùng SHA `70f4d80e`), `aa-cis-dev-admin:12`
  - `aa-booking-dev-api:112` (`76140cdf`), `aa-booking-dev-admin:8`
  - `aa-crm-dev-api:146`, `aa-crm-dev-web:118` (Partner main `ead01570`)
- Lambda TripPlanner `aa-tripplanner-dev-{browse,assembly,jobs}`: sửa lần cuối 08/11 14:48Z (train ghim SHA).

## Endpoint

- CIS `/health` git_sha `70f4d80e`; `/health/ready` ok, schema_version **391** (cis/336 vẫn chờ hẹn giờ ≥10/11 12:00Z).
- Booking `/booking/health` `76140cdf`; ready ok, schema **bk-044**.

## Bảng job

- `shared.job`: 0 queued / 0 running.

## Repo (main / master)

| Repo | Head | PR còn mở |
|---|---|---|
| root | `ba1a5e49` | #644 bot schema-ref (check PR title bị cancel, chờ chạy lại), #641 dependabot actions |
| CIS | `70f4d80e` | #1400 (CIS 392) + #1401 (AA-1052 fan-out/edit gate), mỗi PR 1 check đỏ chưa xem; #1397 dependabot; #1212, #1179 cũ |
| Booking | `76140cdf` | #214 dependabot; #210 docs AA-820; #200 bk-045 (hẹn ≥28/11); #161 release |
| Partner | `ead01570` | #255 dependabot; #240; #133 release |
| TripPlanner | `245595cb` | #248 dependabot; #196 release |
| Infra | `96c82537` | #741, #729 dependabot |

Dependabot PR: không tự merge (ADR 0021 lớp 4), cần review.

## Chi phí trả phí trong phiên (từ ledger)

- W2 đợt 1 (tenant audit, RUN_START 15:48:14Z): 2,58 USD / trần 5.
- Research tenant audit (job 287e1c14): DFS 0,508 + LLM 0,039 USD. Số dư DFS 27,41 → khoảng 26,9 USD.
- T2 linear thử lại 0,064; SEO builder thử 0,126; route-test 0,00028 USD.
- Management (acc4): apply 3 mục (OU Transitional, SCP 1, `aa-org-member-access`), plan lại sạch.
