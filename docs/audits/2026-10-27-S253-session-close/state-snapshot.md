# S253: snapshot trạng thái live lúc chốt phiên (27/10/2026, ~15:30 UTC)

Tác nhân: Claude Code. Mọi số dưới đây đọc từ nguồn thật lúc chốt phiên, không chép từ trí nhớ của phiên.

## AWS acc2 (STS ok)

| Service ECS | Task def đang chạy | Rollout | Chạy / mong muốn | Image | Revision mới nhất của family |
|---|---|---|---|---|---|
| aa-cis-dev-api | :867 | COMPLETED | 1/1 | `dev-960dafda` | :867 (khớp) |
| aa-cis-dev-worker | :433 | COMPLETED | 1/1 | `dev-960dafda` | :433 (khớp) |
| aa-booking-dev-api | :66 | COMPLETED | 1/1 | `ac540fc9` | :66 (khớp) |
| aa-crm-dev-api | :64 | COMPLETED | 1/1 | `d452d4d8` | :64 (khớp) |
| aa-crm-dev-web | :33 | COMPLETED | 1/1 | `76b53da3` | :33 (khớp) |
| aa-crm-dev-portal | :9 | COMPLETED | 1/1 | `76b53da3` | :9 (khớp) |

- CIS api và worker cùng SHA `960dafda` (#1072). Các commit sau đó trên CIS main (#1070 test, #1071 frontend S1b) không đổi backend.
- Env của worker CIS (Infra #440): `JOB_WORKER_GRACE_SECONDS=100`; `JOB_TEST_KINDS=1` trên api và worker, chỉ Dev.

## Endpoint

- CIS `/health/ready`: ok, `schema_version` **290**, git_sha `960dafda`.
- Booking `/booking/health/ready`: ok, schema **bk-028**; `/booking/health` git_sha `ac540fc9`.
- TripPlanner `/api/health`: ok, git_sha `3d0840b8` (ribbon lấy 40 tour, chạy với 25 ảnh).
- Migration mới nhất (dump schema lúc 15:17 UTC, root #285): CIS 290, Booking bk-028; CRM và TripPlanner không đổi trong phiên.

## Vercel (production)

- CIS admin: `51d2a65a` (#1071 S1b). UI smoke production có đăng nhập xanh.
- Booking admin: deploy đi theo push main tới `ac540fc9`. Vercel Deploy xanh lại sau #108 (ghim runner `ubuntu-24.04`).
- TripPlanner: `3d0840b8`.
- Portal: chạy Fargate (`aa-crm-dev-portal:9`). Project Vercel `aa-cis-portal` vẫn giữ làm đường rollback tới đợt dọn 03/11 (AA-979 §4.5).

## Bảng job và wave

- `shared.job`: 1 job queued, 0 running. 0 wave mở.
- Booking: job nhắc nhở do run-script S3 tạo đã vào `booking.job` (2 job `bk_ops_reminders`).

## Repo (head nhánh mặc định; PR còn mở)

| Repo | Head | PR mở |
|---|---|---|
| AA-CIS-App | `51d2a65a` | #1049 (release) |
| AA-Booking | `ac540fc9` | #95 (release) |
| AA-TripPlanner-Web | `3d0840b8` | #155 (release) |
| AA-Partner | `d452d4d8` | #64 (release) |
| AA-CIS-Infra | `f7786cd9` | #411, #412 (cũ, có từ trước phiên) |
| AA-Ecosys (gốc) | sau #284, #285 | 0 (root PR S253 mở lúc chốt) |

Soát revert ngầm: hôm nay đã gặp một lần (#1061 revert #1059/#1060) và đã khôi phục ở #1064. Lần dựng nhánh code S3 (#114) cũng suýt revert Dockerfile của #112; mình phát hiện bằng phép so `merge-base` trước khi commit và đã sửa.

## Cố ý để BẬT cho phiên sau

- `JOB_TEST_KINDS=1` trên Dev (CIS api và worker): loại job `noop_sleep` dùng cho các bài chứng minh drain (G4/G5).
- Dữ liệu tổng hợp trên Dev:
  - AA-682 S2: TC-000018, TC-000019;
  - AA-682 S3: TC-000022 / INV-000003, TC-000023 / INV-000004.
  - Tất cả gắn nhãn `SYNTHETIC S253`; khách hàng có email `example.invalid`.
- Run-script Infra `aa682_s2_live_check` và `aa682_s3_live_check` đều để ở chế độ `dry_run`.
