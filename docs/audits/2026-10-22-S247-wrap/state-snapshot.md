# S247 — trạng thái kiểm cuối phiên (22/10/2026, ~14:45 UTC)

Tác nhân: Claude Code. Chỉ tên/số, không giá trị secret. Kiểm bằng lệnh live (AWS CLI, curl, gh, Vercel), không chép từ chat.

Bản lưu trong repo (public từ 22/10): bỏ account ID khỏi tiêu đề mục AWS; nội dung khác giữ nguyên bản `.tmp-session/s247/wrap/state-snapshot.md`.

## AWS acc2 (us-west-1)
| Service | Task def | Image | Rollout | desired/running |
|---|---|---|---|---|
| aa-cis-dev-api | aa-cis-dev-api:775 | dev-5a54bd2 | COMPLETED | 1/1 |
| aa-cis-dev-worker | aa-cis-dev-worker:334 | dev-5a54bd2 (`T9_FAQ_LLM_FILTER=on`) | COMPLETED | 1/1 |
| aa-booking-dev-api | aa-booking-dev-api:42 | 466ad8e | COMPLETED | 1/1 |

- CIS `/health`: version **0.5.0**, git_sha 5a54bd2; `/health/ready`: schema **268** (required 257). api và worker cùng SHA.
- Booking `/booking/health`: version 0.2.0, git_sha 466ad8e; ready: schema **bk-018**.
- Migration mới nhất mỗi owner (db-schema-reference Verified 22/10 13:28 UTC): CIS **268**, TripPlanner **tp-017**, Booking **bk-018** (278 version).
- Lambda TripPlanner `aa-tripplanner-dev-browse` / `-assembly`: cùng CodeSha256 `GnQiiXfG…aMM4=`, cập nhật 22/10 06:47 UTC.
- `shared.job` queued/running: **0**. Cờ AA-859 đợt 4: 6/6 `"true"`.

## Vercel Production (commit)
- aa-cis-frontend: 51415e2 (#936) — các merge sau chỉ đổi backend.
- aa-tripplanner: 0e9fdcf (release 0.4.0).

## Repo (default branch, visibility)
| Repo | Visibility | HEAD | CI cuối | PR mở |
|---|---|---|---|---|
| AA-Ecosys | **public** (từ 22/10, Nghiệp) | master 998bc0a (#180) | xanh | 0 (sau root PR đóng phiên) |
| AA-CIS-App | public | main 5a54bd2 (release 0.5.0) | Deploy Dev xanh | #908 (meal claims, của phiên khác, chưa đụng) |
| AA-Booking | public | main 466ad8e (release 0.2.0) | xanh | 0 |
| AA-TripPlanner-Web | public | main 0e9fdcf (release 0.4.0) | xanh | 0 |
| AA-CIS-Infra | **public** (từ 22/10, Nghiệp) | main 62d0f79 (#291) | Isolation Probe 58/58 xanh | 0 |

## Lệch / ghi chú
- AA-CIS-Infra từng public ~6 phút rồi private rồi public lại (Nghiệp quyết); 0 fork. Lịch sử Infra có credential DataForSEO còn dùng — Nghiệp giữ nguyên (AA-841 S239, nhắc lại S247).
- Phút GitHub Actions cho repo private đã hết tháng 10; khi trả repo về private cần budget hoặc runner riêng (ADR 0014 amendment).
