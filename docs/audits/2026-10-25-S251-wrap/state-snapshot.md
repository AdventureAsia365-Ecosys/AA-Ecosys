# S251 close — ảnh chụp trạng thái live (25/10/2026, ~16:30 UTC)

Đọc từ nguồn live (AWS CLI read-only profile `aa365-admin`, curl, `gh`) lúc đóng phiên, chép lại từ mục Snapshot của
`.tmp-session/s251/SESSION-FACTS.md`. Chỉ tên/số — không ghi account id, ARN, hostname nội bộ hay giá trị secret.
Mục nào không kiểm lúc chụp ghi rõ "chưa kiểm".

STS: profile `aa365-admin` trả về đúng acc2 (us-west-1).

## ECS (cluster aa-cis-dev-cluster)

| Service | Task definition | Image tag | Running | Rollout |
|---|---|---|---|---|
| aa-cis-dev-api | :829 | dev-55e24026 | 1/1 | COMPLETED |
| aa-cis-dev-worker | :395 | dev-55e24026 | 1/1 | COMPLETED |
| aa-booking-dev-api | :58 | 8d00c76d | 1/1 | COMPLETED |
| aa-crm-dev-api | :48 | e83aef55 | 1/1 | COMPLETED |
| aa-crm-dev-web | :22 | e83aef55 | 1/1 | COMPLETED |

- CIS api và worker cùng SHA `55e24026` (CIS #1016, AA-835: gateway giữ schema trên key cũ).

## Health

| App | Endpoint | Kết quả |
|---|---|---|
| CIS | `/health` | git_sha 55e24026 |
| CIS | `/health/ready` | schema **282** (required 280) |
| Booking | `/booking/health` | git_sha 8d00c76d |
| Booking | `/booking/health/ready` | schema **bk-024** |
| CRM api / CRM web | `/crm/health`, `/healthz` | chưa kiểm lúc chụp (ECS 1/1 COMPLETED) |

- Booking main `76259f79` là commit chỉ đổi cấu hình gitleaks, không deploy → live vẫn `8d00c76d`; không phải lệch.
- TripPlanner Lambdas browse / assembly: CodeSha256 `rFXJi1TS…`, LastModified 25/10/2026 11:40Z.

## Migration mới nhất mỗi owner

- CIS **282** (`/health/ready`). Áp trong S251: 281 (AA-853, DB Migrate run 40186864048), 282 (AA-835, route
  `supply_content_writer` → sonnet-5-5, DB Migrate apply 40204566298).
- Booking **bk-024** (`/booking/health/ready`).
- CRM: crm-016 (AA-946) và crm-018 (AA-978) áp trong phiên; `/crm/health/ready` chưa đọc lúc chụp.
- TripPlanner: chưa kiểm lúc chụp (nguồn sự kiện phiên không ghi migration TripPlanner nào).
- DB Schema Dump run 40191477074: "Drift verdict: clean" (0 open, 343 file replay, 0 failed).

## Vercel

Chưa chụp commit Production từng project trong snapshot này.

## Bảng job và wave

- `shared.job`: không còn job.
- `booking.job`: queued 1 (job theo lịch).
- `crm.job`: chưa kiểm.
- Wave S1 (AA-645): xong toàn bộ (810/810 tour trên v2) — không còn wave mở, không cờ GAP.

## Cố ý để BẬT cho S252

- Writer v2 + route `s1_generate` = sonnet-5-5 giữ làm mặc định (quyết định của Nghiệp từ S250).
- Probe AA-991 (DB Freshness Probe) chạy hằng đêm 05:13 UTC ở chế độ report (chưa ENFORCE).
- Hotel tổng hợp `HTL-000003` để active + published v3 (dữ liệu giả của AA-835).

## Repos (head nhánh mặc định lúc chụp)

| Repo | Head | PR mở |
|---|---|---|
| AA-Ecosys master | sau #261 | — |
| AA-CIS-App main | 55e24026 | #1017 (AA-790 vòng 2), #1010 merged sau snapshot (`520199cd`, 16 cảnh báo đóng → 96/96), #1009 release 0.11.0 |
| AA-Booking main | 76259f79 | #92 release 0.7.0 |
| AA-Partner main | b26d4a11 | #52 release 0.5.0 |
| AA-TripPlanner-Web main | f024a396 | #153 release 0.8.2 |
| AA-CIS-Infra main | 7f7b226d | không |

## Chi phí (ngoài các con số theo issue trong log phiên)

- Ngân sách AWS acc3 tháng 10: $201,69 / $250, dự báo $215–225.
