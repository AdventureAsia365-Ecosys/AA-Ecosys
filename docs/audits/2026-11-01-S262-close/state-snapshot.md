# S262 — snapshot trạng thái thật lúc chốt phiên

Chụp: 01/11/2026 ~11:00 +07 (03:55–04:07Z), Claude Code (subagent chốt phiên, chỉ đọc). Nguồn: AWS CLI đọc
(`aa365-admin`, us-west-1), curl endpoint, `gh`, Vercel MCP, Linear (đọc). Không account ID / ARN / giá trị secret.

## 1. AWS

- STS `aa365-admin`: còn hạn — assumed-role `nghiep-admin-8h-session` (acc2). MFA refresh 07:34 +07, hạn ~19:32 +07.
- RDS `aa-cis-dev-db`: `available`, db.t4g.small, PostgreSQL 15.17.

## 2. ECS (`aa-cis-dev-cluster`)

| Service | Task def đang chạy | Image tag (SHA) | Rollout | Running/Desired | Revision mới nhất của family |
|---|---|---|---|---|---|
| aa-cis-dev-api | aa-cis-dev-api:956 | dev-0982cbd9 (CIS #1213) | COMPLETED | 1/1 | 956 = đang chạy |
| aa-cis-dev-worker | aa-cis-dev-worker:522 | dev-0982cbd9 (cùng SHA với api) | COMPLETED | 1/1 | 522 = đang chạy |
| aa-booking-dev-api | aa-booking-dev-api:91 | 16fbed68 (Booking #163) | COMPLETED | 1/1 | 91 = đang chạy |
| aa-crm-dev-api | aa-crm-dev-api:107 | f2f72e92 (Partner #171) | COMPLETED | 1/1 | 107 = đang chạy |
| aa-crm-dev-web | aa-crm-dev-web:81 | d395b7ac (Partner #172) | COMPLETED | 1/1 | 81 = đang chạy |
| aa-crm-dev-portal | aa-crm-dev-portal:25 | 7e452205 (Partner #164) | COMPLETED | 1/1 | 25 = đang chạy |

- Mỗi service chỉ có 1 deployment PRIMARY, không còn deployment cũ.
- **Revision mẫu sau Terraform Apply:** apply AA-1019 (run 41261471772, 08:31 +07) đăng ký task def web mới có
  `STAFF_*`; các deploy sau đó (web :79 2787b451 → :80 f2f72e92 → :81 d395b7ac, đăng ký 10:58 +07) đã chép đè.
  Revision mới nhất = đang chạy ở cả 6 family → **không còn revision mẫu treo**. `aa-crm-dev-web:81` có đủ 4 tên
  `STAFF_COGNITO_CLIENT_ID`, `STAFF_COGNITO_CLIENT_SECRET`, `STAFF_COGNITO_DOMAIN`, `STAFF_SESSION_SECRET`.
- `LLM_DAILY_PROBE=on` có trong env của cả `aa-cis-dev-api:956` và `aa-cis-dev-worker:522`.

## 3. Endpoint (tất cả HTTP 200)

| Endpoint | Kết quả | git_sha | Khớp ECS/Vercel |
|---|---|---|---|
| CIS `/health` | ok, v0.18.0 | 0982cbd9 | khớp api :956 |
| CIS `/health/ready` | db ok, schema_version **324**, required 322 | 0982cbd9 | khớp |
| Booking `/booking/health` | ok, v0.14.0 | 16fbed68 | khớp :91 |
| Booking `/booking/health/ready` | db ok, schema **bk-035**, storage supply_media + ops_docs configured | — | — |
| CRM api `portal.lumiguides.it.com/crm/health` | ok, v0.11.0 | f2f72e92 | khớp :107 |
| CRM api `/crm/health/ready` | db ok, schema **crm-035**, membership_feed ok, keys kms | — | — |
| CRM web `portal.lumiguides.it.com/healthz` | ok, v0.11.0, auth_configured true, **staff_auth_configured true** | d395b7ac | khớp web :81 |
| TripPlanner `aa-tripplanner.vercel.app/api/health` (và `tripplanner.lumiguides.it.com`) | ok, v0.14.0 | 4fd7dcab | khớp Vercel Production |
| TripPlanner `/api/browse?resource=countries` | 200, danh sách nước | — | Lambda browse sống |
| TripPlanner `/api/browse/search?q=temple` (curl, không BotID) | **403 bot_check_failed** | — | BotID Basic đang chặn đúng |

Lambda TripPlanner (`CodeSha256`, cả 3 cùng gói, LastUpdateStatus Successful):

| Function | CodeSha256 | LastModified |
|---|---|---|
| aa-tripplanner-dev-browse | `oY/+0WcGOh/TZSaeDeHC9IiAv/2z54bipVzSneGH93A=` | 31/10 16:30:49Z |
| aa-tripplanner-dev-assembly | `oY/+0WcGOh/TZSaeDeHC9IiAv/2z54bipVzSneGH93A=` | 31/10 16:30:52Z |
| aa-tripplanner-dev-jobs | `oY/+0WcGOh/TZSaeDeHC9IiAv/2z54bipVzSneGH93A=` | 31/10 16:30:55Z |

Lambda deploy theo run "Deploy Lambdas" trên TP c845b623 (#203, AA-642 S8) — xanh.

## 4. Migration mới nhất mỗi owner

| Owner | Live (`/health/ready`) | db-schema-reference.md "Verified" (31/10 19:56Z) |
|---|---|---|
| CIS | 324 | 324 |
| Booking | bk-035 | bk-035 |
| TripPlanner | (không có ready) | tp-023 |
| CRM | crm-035 | crm-035 |

Khớp nhau; file reference không lỗi thời.

## 5. Vercel Production

| Project | Commit Production (READY) | Head nhánh mặc định | Ghi chú |
|---|---|---|---|
| aa-cis-frontend (CIS admin) | 67668f85 (CIS #1211) | 0982cbd9 | #1213 chỉ đổi `api/`, `services/`, `tests/`, `docs/` → không cần build FE, đúng |
| aa-booking-admin | 16fbed68 (Booking #163) | 16fbed68 | khớp |
| aa-tripplanner | 4fd7dcab (TP #201) | c845b623 | #202/#203 chỉ đổi `backend/` + docs → không build FE, đúng |
| portal (Content studio) | — | — | không còn project Vercel; chạy ECS `aa-crm-dev-portal` (mục 2) |

Team Vercel chỉ còn 3 project.

## 6. Bảng job + wave

- `shared.job` / `booking.job` / `crm.job`: **chưa kiểm (cần ECS exec — điều phối)**. `/admin/job-runner/summary`
  cần admin secret (403 khi không có), subagent không gọi được.
- Theo checklist: chuỗi geocode AA-997 (`aa997.4`: dc260ef8 400 + 3625eac5 400 + b1e780e8 224 = 1.024 dòng, 0 lỗi)
  đã ĐÓNG lúc 00:30Z; job `place_relocate` hẹn giờ đầu phiên đã chạy xong. Không có wave A1→A3 mở trong phiên.
- `crm.job`: alarm `aa-crm-dev-jobs-queue-age`, `-jobs-overdue-running`, `-jobs-sampling-stopped` đều **OK**.

## 7. Repo

| Repo | Nhánh mặc định | Head origin | Commit từ 31/10 06Z | PR mở | CI run cuối trên nhánh mặc định |
|---|---|---|---|---|---|
| root AA-Ecosys | master | 4a4f32c3 (#423) | 29 | #374 bot infra docs, #328 AA-993 M5 (cũ) | Secret Scan success (4a4f32c3) |
| AA-CIS-App | main | 0982cbd9 (#1213) | 19 | #1212 dependabot follow-redirects, #1179 release 0.19.0 | CI + Deploy Dev + CodeQL success (0982cbd9) |
| AA-Booking | main | 16fbed68 (#163) | 2 | #164 bot kit-sync cc03473, #161 release 0.15.0 | CI + Deploy Dev + Vercel Deploy success (16fbed68) |
| AA-TripPlanner-Web | main | c845b623 (#203) | 6 | #196 release 0.15.0 | CI + Deploy Lambdas success (c845b623) |
| AA-Partner | main | d395b7ac (#172) | 23 | #159 bot kit-sync cc03473, #133 release 0.12.0 | CI (run 41271153487) + Deploy Web Dev + Docs lint success (d395b7ac; CI xong ~04:08Z) |
| AA-CIS-Infra | main | 1370c7b5 (#578) | 29 | 0 | Migration Apply (expand) success 02:31Z; Terraform Apply Prod (workflow name) success 01:31Z |

- Dependabot Updates (CIS, TP) lần cuối `failure` — workflow của dependabot, không phải CI sản phẩm.
- **Soát commit xoá file trên main từ 31/10:** chỉ 3 commit có xoá, đều cố ý: root 6ed19817 (#407, 2 file `.pyc`
  lỡ commit); CIS 7f6e3c2a (#1199, 4 tab Settings/Cost Ops cũ được chuyển hướng); CIS 3cfba249 (#1197,
  `dataforseo.py` cũ + test). Booking/TP/Partner/Infra: 0 commit xoá. Không thấy squash revert âm thầm.
- **Checkout chính chưa pull** (local nhánh mặc định sau origin): root ab2fd3c4, CIS cc034731, Booking 636df62c,
  TP 4c6b3414, Partner 9bf771e3 (Infra khớp). Root có 34 dòng `git status` (5 file sửa + audit/evidence chưa track
  của phiên) → vào root PR chốt phiên.
- **Worktree:** `.tmp-session/wt/` có **72** thư mục; git ghi nhận 72 worktree liên kết (root 15, CIS 19, Booking 1,
  TP 5, Partner 19, Infra 13). Nhánh local: root 73, CIS 131, Booking 33, TP 24, Partner 58, Infra 87 (phần lớn là
  nhánh lane S261/S262 đã merge) → dọn ở bước 7 chốt phiên.
- S3 `aa-cis-bronze-…/scripts/`: 26 object, 12 cái từ 31/10 → dọn ở bước 7.

## 8. Linear (đọc)

- Done trong phiên (completedAt 31/10 14:07Z → 01/11 03:22Z): **17** — AA-964, AA-1013, AA-971, AA-1015, AA-1017,
  AA-804, AA-642, AA-1018, AA-1016, AA-952, AA-956, AA-954, AA-1009, AA-997, AA-1019, AA-957, AA-1014.
- In Progress còn **3**: AA-896 (FinOps, báo cáo tháng 10 SƠ BỘ, chính thức ≥ 03/11), AA-820 (luật sư + báo tenant,
  chị Thư), AA-900 (nhãn 40 mẫu + chạy thử trả phí).
- Chuyển Backlog trong phiên: AA-873, AA-1004, AA-922 (track đóng băng TL-11). Issue mới: AA-1019 (đã Done),
  AA-1020 (docs kiến trúc, slot S263), AA-1021 (content series, details private).

## 9. Cố ý để BẬT cho phiên sau

- `LLM_DAILY_PROBE=on` trên CIS api :956 + worker :522 (Infra #574; ~0,05–0,20 USD/tháng, trong mức duyệt S261).
- `hide_flagged` đã **confirm** (report f54cdf77 → confirm 4919a61f, 2.517 dòng ẩn, 1.187 gắn tour) — AA-997
  Done-with-scope (TL-25). Nguồn: checklist 08:23; snapshot này không kiểm lại DB.
- CRM staff console live: `staff_auth_configured=true` trên web :81; user Cognito `e2e-crm-staff` (crm-ops +
  crm-support); release live 74c05c77 (trip 7a63a728, departure auto_confirm 27/11).
- TripPlanner BotID Basic chặn search/narrate khi không qua bot check (403 xác nhận); Lambda
  `TP_DAILY_SPEND_CAP_USD=5.0` (Infra #553).
- Alarm: 50 alarm CloudWatch; 22 alarm `aa-crm-dev-*` đều OK, ActionsEnabled — gồm 4 alarm mới phiên này
  (`breakglass-opened`, `breakglass-owner-not-mailed`, `ops-release-incomplete-t21`, `ops-release-withdrawn`).
  Alarm ở trạng thái ALARM: chỉ 4 alarm `TargetTracking … AlarmLow` của autoscaling CIS api/worker (bình thường khi
  tải thấp).
- Model ứng viên acc2 (mig 324: nova-lite, nova-2-lite, llama4-maverick, llama4-scout, kimi-k3) đã probe OK nhưng
  **chưa route**.
- Lượt dữ liệu video CRM `rv202610317` giữ lại (--keep-run).

## 10. Lệch / cần điều phối xử lý

1. Bảng job 3 app chưa kiểm được trong snapshot này (cần ECS exec).
2. CI Partner main trên d395b7ac: đang chạy lúc chụp, kiểm lại 04:08Z → success.
3. Root PR #328 (AA-993 M5, cũ) và #374 (bot infra docs) còn mở; 2 PR bot kit-sync (Booking #164, Partner #159)
   cho CIS cc03473 còn mở.
4. Nháp Jira (7 đích) **chưa đăng: dời S263 theo Nghiệp** (quyết định 09:00) — xem `jira-drafts.md` cùng thư mục.
5. Không có lệch nào giữa ECS / endpoint / Vercel / migration với điều checklist ghi.
