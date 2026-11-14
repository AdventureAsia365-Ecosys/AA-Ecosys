# S280 — Snapshot trạng thái thật lúc chốt phiên (14/11/2026 ~21:35 +07)

Lấy bằng `.tmp-session/S280/snap.sh` + ECS exec (bảng job, gateway). Chỉ tên, revision, SHA, mã HTTP.

## ECS (cluster `aa-cis-dev-cluster`)

| Service | Task def đang chạy | Image | Rollout | Running/Desired | Revision mới nhất |
|---|---|---|---|---|---|
| aa-cis-dev-api | :1147 | `dev-f8cb2d8c` | COMPLETED | 1/1 | :1147 |
| aa-cis-dev-worker | :716 | `dev-f8cb2d8c` | COMPLETED | 1/1 | :716 |
| aa-booking-dev-api | :137 | `3eb67741` | COMPLETED | 1/1 | :137 |
| aa-crm-dev-api | :172 | `ffd5caea` | COMPLETED | 1/1 | :172 |
| aa-crm-dev-web | :151 | `f2909cf6` | COMPLETED | 1/1 | :151 |

- CIS api và worker cùng SHA `f8cb2d8c` (#1508). Mọi service chạy đúng revision mới nhất của family.
- CRM web :151 chép từ revision mẫu :150 do Terraform Apply AA-1105 S2 tạo; deploy tay sau khi ghi 2 key academy vào
  `crm/dev/web` → chứng minh task nạp được secret mới.
- CIS admin (ECS `aa-cis-dev-admin`): Deploy Admin Dev `307f9133` (#1507) success sau khi chạy lại smoke signed-in (lần
  đầu đỏ hàng loạt cả trang công khai `/login`, lần chạy lại xanh: sự cố tạm lúc rollout).

## Endpoint

| URL | HTTP | SHA |
|---|---|---|
| CIS `/health`, `/health/ready` | 200, 200 (schema_version 420, required 322) | `f8cb2d8c` |
| Booking `/booking/health`, `/booking/health/ready` | 200, 200 | `3eb67741` |
| CRM `/crm/health`, `/crm/health/ready` (host `portal.`) | 200, 200 | `ffd5caea` |
| CRM web `/healthz` | 200 | `f2909cf6` |
| TripPlanner `/api/health`, `/api/browse?resource=countries` | 200, 200 | `566dee62` |
| Academy `academy.lumiguides.it.com/healthz` | 200 (auth_configured=True) | `f2909cf6` |

TripPlanner Lambda browse + assembly cùng CodeSha256, sửa lần cuối 14/11 07:16Z.
Edge check `crm_edge_live_check.py --academy-host`: 13/13 PASS (academy-healthz 200, academy-no-crm 404).

## Migration mới nhất mỗi owner

CIS **420** (AA-1105 learn schema, Migration Apply tự chạy 14:29Z, key đăng ký), Booking **bk-058**, TripPlanner tp-031,
CRM crm-065. DB Isolation Probe + DB Schema Dump tự chạy sau apply (kết quả: xem log phiên).

## Bảng job / wave

`shared.job` 0 mở, `booking.job` 0 mở, `crm.job` 2 queued định kỳ (`crm_booking_sync`, `crm_heartbeat`). Không wave mở.
Không có cờ nào cố ý để BẬT cho phiên sau. Công tắc xoá dữ liệu AA-1093 đã TẮT (Infra #839).

## AI gateway

Route control v11 (12/11). Chi tiêu tháng tới giờ 34,32 USD (đầu phiên 34,01): anthropic-direct 28,61/150,
openai-direct 1,97/10, acc1 0,06/100 (24 h 11 ok/2 err), acc3 1,07/100 (24 h 5 ok/7 err), acc2 0,44, typesafe 2,18.

## Repo (head nhánh mặc định, PR mở)

| Repo | Head | PR mở |
|---|---|---|
| AA-Ecosys (root) | `b7a1af5d` (#781) | #766 bot infra docs; root close PR của phiên này |
| AA-CIS-App | `f8cb2d8c` (#1508) | #1467 bot test durations, #1179 release |
| AA-Booking | `3eb67741` (#257) | #200 bk-045 (destructive, chờ ≥28/11), #161 release |
| AA-TripPlanner-Web | `d8d1de2a` (#267) | #196 release |
| AA-Partner | `f2909cf6` (#312) | #133 release |
| AA-CIS-Infra | `563195b2` (#842) | không |

## Lệch / ghi chú

- Phiên MFA hết sớm (21:01, giờ tool báo 21:14) → các bước AWS dừng ~15 phút tới khi tech lead nhập lại.
- RDS snapshot `tenant-erase-20261114-pre` (AA-1093) còn: xoá sau khi root close PR (bằng chứng) merge.
