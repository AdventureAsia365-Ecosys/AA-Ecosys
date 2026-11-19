# S285 — Snapshot trạng thái live cuối phiên

Chụp lúc **2026-11-19 15:44 UTC (22:44 giờ VN)**, Claude Code (subagent chỉ đọc). Nguồn: AWS CLI một dòng
(profile `aa365-admin`, us-west-1), `gh` (chỉ đọc), `curl`. Bảng job (`shared.job`, `booking.job`, `crm.job`) và các giá trị
lưu trong DB (trần connection, công tắc MFA) **không** truy vấn ở đây — điều phối tự kiểm.

## 1. STS

- `aa365-admin` → **acc2** (đúng tài khoản hạ tầng chính), role `nghiep-admin-12h`.

## 2. ECS — cluster `aa-cis-dev-cluster` (8 service, không có service nào khác)

| Service | Task def đang chạy | Image tag | Rollout | Running/Desired | Revision mới nhất của family |
|---|---|---|---|---|---|
| aa-cis-dev-api | aa-cis-dev-api:1229 | `dev-33e87ec7…` | COMPLETED | 1/1 | 1229 = đang chạy |
| aa-cis-dev-worker | aa-cis-dev-worker:798 | `dev-33e87ec7…` (repo aa-cis-dev-api) | COMPLETED | 1/1 | 798 = đang chạy |
| aa-cis-dev-admin | aa-cis-dev-admin:73 | `dev-dda98445…` | COMPLETED | 1/1 | 73 = đang chạy |
| aa-booking-dev-api | aa-booking-dev-api:151 | `e329c9eb…` | COMPLETED | 1/1 | 151 = đang chạy |
| aa-booking-dev-admin | aa-booking-dev-admin:45 | `e329c9eb…` (+ container `wordpress`, ghim digest) | COMPLETED | 1/1 | 45 = đang chạy |
| aa-crm-dev-api | aa-crm-dev-api:208 | `1f7d1cf9…` | COMPLETED | 1/1 | 208 = đang chạy |
| aa-crm-dev-web | aa-crm-dev-web:180 | `1f7d1cf9…` | COMPLETED | 1/1 | 180 = đang chạy |
| aa-tripplanner-dev-web | aa-tripplanner-dev-web:21 | `0d626f61…` | COMPLETED | 1/1 | 21 = đang chạy |

- CIS api và worker **cùng SHA** `33e87ec7` (= head `main` CIS, #1610).
- Mỗi service chỉ có 1 deployment (không rollout dở). Revision mới nhất mỗi family đều là revision đang chạy.

## 3. Endpoint

| Endpoint | HTTP | Kết quả |
|---|---|---|
| CIS `api-cis.…/health` | 200 | version 0.20.0, git_sha `33e87ec7` (khớp ECS) |
| CIS `/health/ready` | 200 | db ok, schema_version **460**, required 322 |
| Booking `api-booking.…/booking/health` | 200 | version 0.16.0, git_sha `e329c9eb` (khớp ECS) |
| Booking `/booking/health/ready` | 200 | db ok, schema_version **bk-061**, storage supply_media + ops_docs configured |
| CRM api `portal.…/crm/health` | 200 | version 0.13.0, git_sha `1f7d1cf9` (khớp ECS) |
| CRM api `/crm/health/ready` | 200 | db ok, schema_version **crm-082**, membership_feed ok, entitlement_feed ok, keys kms |
| CRM web `portal.…/healthz` | 200 | version 0.13.0, git_sha `1f7d1cf9`, auth/staff_auth/academy_auth configured |
| TripPlanner web `tripplanner.…/api/health` | 200 | version 0.16.0, git_sha `0d626f61` (khớp image tag) |
| TripPlanner `/api/browse?resource=countries` | 200 | 21 nước, tổng 844 tour |
| CIS admin `aa-cis.…` | 307 → `/admin/upload` | image `dev-dda98445` = run `deploy-admin-dev` cuối (10:42Z, success) |
| Booking admin `booking.…` | 307 → `/login` | image `e329c9eb` = Deploy Admin Dev cuối (10:29Z, success) |

Lambda TripPlanner (LastUpdateStatus Successful, cập nhật 13:52Z bởi Deploy Lambdas của TP `1498c1ab`):

- `aa-tripplanner-dev-browse` CodeSha256 `OIIqbRG39fSmo6q1xW4rtdNQLfDyUPRK1RTxr/4TOeI=`
- `aa-tripplanner-dev-assembly` CodeSha256 `OIIqbRG39fSmo6q1xW4rtdNQLfDyUPRK1RTxr/4TOeI=` (cùng gói)

TripPlanner web vẫn `0d626f61` là đúng: 6 commit sau đó (#283–#288) chỉ đụng backend/docs/migration/CI, không đụng web,
nên Deploy Web Dev không chạy lại.

## 4. Migration mới nhất mỗi owner

| Owner | Live (health/ready) | Dòng "Verified" db-schema-reference (14:05 UTC) |
|---|---|---|
| CIS | 460 | 460 |
| Booking | bk-061 | bk-061 |
| CRM | crm-082 | crm-082 |
| TripPlanner | (không có health/ready) | tp-035 |

Tổng 615 version đã đăng ký. **Không có** PR `bot/db-schema-reference` đang mở (bản dump 14:05 đã merge ở root #908).

## 5. Repo

| Repo (nhánh) | Head | Commit hôm nay | PR mở (checks) | CI cuối trên nhánh mặc định |
|---|---|---|---|---|
| AA-Ecosys (master) | `ccf40ca0` #908 db-schema-reference (14:09Z) | 25 | #860 bot infra docs (SUCCESS 6, SKIPPED 3, CANCELLED 1; cập nhật 14:50Z) | Secret Scan + Docs sync `ccf40ca0` success |
| AA-CIS-App (main) | `33e87ec7` #1610 (15:25Z) | 20 | #1586 dependabot frontend-security (**FAILURE 4**); #1570 release 0.21.0; #1467 CI test durations | Deploy Dev, CodeQL, Secret Scan, Release Please `33e87ec7` success |
| AA-Booking (main) | `e329c9eb` #286 MFA admin policy switch (10:18Z) | 11 | #276 kit sync; #270 release 0.17.0; #200 draft bk-045 (FAILURE 2, cố ý chưa làm) | Deploy Dev + Deploy Admin Dev `e329c9eb` success |
| AA-TripPlanner-Web (main) | `1498c1ab` #288 module TripPlanner app đại lý (13:49Z) | 7 | #278 release 0.17.0 | CI, Deploy Lambdas, CodeQL `1498c1ab` success |
| AA-Partner (main) | `1f7d1cf9` #366 module Trip planner (14:24Z) | 17 | #355 kit sync; #343 release 0.14.0 | Deploy Dev success; **Deploy Web Dev failure** (xem mục 7) |
| AA-CIS-Infra (main) | `f6f18f16` #941 copy cis 460 (14:01Z) | 19 | **#935** WAF geo staff host (SUCCESS 12, SKIPPED 5) — cố ý mở | Terraform Apply Dev 14:47Z success; Docs Gen 14:48Z success; **Terraform Drift 14:38Z failure** (xem mục 7) |

Soát commit xoá nhiều file: **không** có commit nào hôm nay (từ 00:00 UTC) trên nhánh mặc định của 6 repo xoá ≥ 5 file.

## 6. Cố ý để BẬT / để nguyên cho phiên sau

- Connection `openai-direct`: trần tháng 11 nâng lên **25 USD**, phải hạ về **10 USD ngày 01/12** — theo điều phối; snapshot
  này **chưa kiểm live** (giá trị nằm trong DB).
- Công tắc bắt buộc MFA admin: **CRM = On**, **CIS = Off**, **Booking = Off** (chờ business owner đăng ký TOTP) — theo điều
  phối; **chưa kiểm live** ở đây. Code công tắc đã live: Booking #286 (`e329c9eb`), crm-082 đã áp.
- Infra **PR #935** (staff web hosts rời luật WAF geo khi MFA admin đã bắt buộc) **mở có chủ đích**, checks xanh, chờ TOTP.
- Release PR mở theo lệ tuần (CIS #1570, Booking #270, TP #278, Partner #343) và kit sync (Booking #276, Partner #355):
  không phải việc dở của phiên.

## 7. Lệch giữa live và checklist / điều cần lưu ý

1. **AA-Partner Deploy Web Dev đỏ liên tục từ 19/11 01:14Z** (≥ 8 run, mới nhất `1f7d1cf9` 14:29Z): deploy ECS + post-deploy
   verify **thành công** (web đang chạy đúng `1f7d1cf9`), chỉ job "Studio UI smoke" trượt **1/69**:
   `smoke-portal/aa761-account-pages.spec.ts:124` "Activity: the pager asks the server for the next page" (element not
   found, cả retry). Lần đỏ đầu trùng lúc merge Partner #349 + #350 (01:14Z) → nghi hồi quy từ hai PR đó. Checklist
   không ghi việc này.
2. **AA-CIS-Infra Terraform Drift 14:38Z đỏ** (root `accounts/aa365`: plan 10 thay đổi, 11 đổi ngoài Terraform); hôm qua
   18/11 cũng đỏ. Sau đó Terraform Apply Dev 14:47Z success — chưa có run drift nào sau apply để xác nhận đã sạch.
   Checklist không ghi.
3. Checklist còn ghi ⏳ cho việc thực ra đã xong trên live: AA-1128 #280 (merged 06:31Z), AA-1145 Booking #281/#282
   (merged, bk-060 → live bk-061), AA-1144 Partner #359 (merged 07:00Z), AA-1129 Partner #349/#350 (merged 01:14Z),
   AA-1139 (TP #288 `1498c1ab` + Partner #366 `1f7d1cf9` đã merge và deploy). Cần cập nhật checklist theo số này.
4. SHA CIS đầu phiên `43d288c5` → cuối phiên `33e87ec7` (đổi đúng theo các deploy trong phiên, không phải lệch).
5. CIS PR #1586 (dependabot frontend-security) đỏ 4 check — chưa ai xử lý.
6. Mục 6 (trần openai-direct, công tắc MFA) chưa kiểm live trong snapshot này.
