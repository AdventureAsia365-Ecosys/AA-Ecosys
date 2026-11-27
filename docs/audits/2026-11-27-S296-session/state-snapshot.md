---
id: AUD-S296-state-snapshot
title: "S296 trạng thái kiểm cuối phiên (27/11/2026)"
description: "Snapshot live cuối phiên S296: ECS, health, migration, bảng job, repo, PR mở, thứ đang bật."
type: audit
status: final
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-27
---

# S296 — trạng thái kiểm cuối phiên (27/11/2026, ~21:10 +07)

Tác nhân: Claude Code. Mọi số dưới đây đọc live lúc chốt phiên, không chép từ trí nhớ phiên.

## ECS (cluster Dev, 8 service, 1/1, rollout COMPLETED, revision mới nhất = đang chạy)

| Service | Task def | Image |
|---|---|---|
| cis-api | :1305 | dev-5ea44b66 |
| cis-worker | :874 | dev-5ea44b66 (cùng SHA với api) |
| cis-admin | :114 | dev-db8c3f66 |
| booking-api | :180 | 6dacf911 |
| booking-admin | :77 | 52ee56a7 (1 container, sidecar test-wp đã gỡ) |
| crm-api | :229 | 4d55e829 (URL TripPlanner = custom domain) |
| crm-web | :201 | b27b68ae |
| tripplanner-web | :33 | 6349be4c |

## Endpoint

- CIS `/health` 5ea44b66, `/health/ready` ok, schema 494.
- Booking `/booking/health` 6dacf911, ready ok, bk-075.
- CRM api `/crm/health` 4d55e829, ready ok, crm-090; CRM web `/healthz` b27b68ae.
- TripPlanner web `/api/health` 6349be4c; `/api/browse?resource=countries` 200; Lambda deploy lại sau đổi mật khẩu DB (post-deploy verify xanh).
- URL execute-api mặc định đã tắt: CIS 403, Booking 403, TripPlanner 404; custom domain đều 200.

## Bảng job

- `shared.job`: 0 queued/running (succeeded 9424, failed 21, cancelled 7 — số luỹ kế).
- `booking.job`: 0 queued/running.
- `crm.job`: 3 queued = job định kỳ (heartbeat, membership_pull) — bình thường.
- Không wave mở, không cờ wave nào bật.

## Repo (head nhánh mặc định) và PR còn mở

| Repo | Head | PR mở |
|---|---|---|
| AA-Ecosys | 490636bc (trước root PR chốt phiên) | bot infra docs #1048 |
| AA-CIS-App | db8c3f66 | #1717 (chuỗi bk-076), #1709/#1710 (gỡ T10, chờ AA-1169), release 0.22.0, dependabot, bot test durations |
| AA-Booking | 52ee56a7 | #336 (bk-076, chờ ≥ 28/11 23:50Z), dependabot, release 0.18.0 |
| AA-Partner | 99b1af7a | release 0.15.0 |
| AA-TripPlanner-Web | 6349be4c | release 0.18.0 |
| AA-CIS-Infra | 896b15a7 | #1042/#1043 (chuỗi bk-076), #935 (WAF geo, chờ MFA admin) |

## Hạ tầng đổi trong phiên (Terraform Apply CI + 3 apply local MFA có -target, đều từ main)

- AA-1182: bucket state khoá (4 Sid), managed policy `aa-cis-dev-ecs-task-data-access`, task role CIS không còn quyền trên `*` (trừ ListFoundationModels); task role đọc state = 403.
- AA-1183: 2 rule cảnh báo ACM (us-west-1 + forward us-east-1).
- AA-1185: test-wp tắt, EBS mã hoá mặc định, snapshot BPA, rule AWS Health + nhóm admin + enable-user, CAA, DMARC rua, ALB/NLB deletion protection, execute-api mặc định tắt, SG cũ `sg-app` xoá (2 ENI mồ côi xoá tay), egress 10 SG thu hẹp (rollback `sg_egress_narrowed = false`).
- Xoay (P6 AA-1182): 7 client secret Cognito, mật khẩu DB TripPlanner, 3 khoá TripPlanner. CI Terraform Apply sau cùng: "No changes".

## Đang cố ý BẬT cho phiên sau

- AA-873 chạy thử: Security Hub CSPM (chỉ FSBP) + bản hợp nhất, Inspector (ECR + Lambda), Macie. 4 lịch EventBridge Scheduler tự tắt 29/11 09:17 / 09:22 / 09:27 / 09:32 UTC; role `aa873-trial-auto-off` xoá sau khi kiểm.
- E2E Dev CRM chạy hằng đêm 03:17 UTC và sau mỗi Deploy Web Dev / Deploy Dev (AA-1196).
- Lệnh vá NAT (`AWS-RunPatchBaseline`, association `aa-ecosys-dev-nat-patch`) chạy lần đầu lúc 13:47Z, lúc chụp snapshot vẫn đang chạy; app ready 200 suốt quá trình.

## Lệch / ghi chú

- Lần xoay secret M2M đầu tiên mất giá trị (Describe không trả secret sau khi xoay) → CRM gọi M2M lỗi vài phút, đã khôi phục bằng secret mới; bài học ghi ở lessons.md.
- Partner E2E Dev đỏ từ 11/11 (phát hiện phụ) → AA-1196, đã xanh lại trong phiên.
