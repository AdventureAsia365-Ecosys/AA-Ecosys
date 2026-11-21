# S287 — Snapshot trạng thái live cuối phiên

Chụp lúc **2026-11-21 11:17–11:25 UTC (18:17–18:25 giờ VN)**, Claude Code (subagent chỉ đọc). Nguồn: AWS CLI một dòng
(profile `aa365-admin`, us-west-1), `gh` (chỉ đọc), `curl`, `git fetch` các repo local. Bảng job (`shared.job`,
`booking.job`, `crm.job`) và các giá trị lưu trong DB (trần connection, công tắc MFA, cờ wave) **không** truy vấn ở đây —
điều phối tự kiểm.

## 1. STS

- `aa365-admin` → **acc2** (đúng tài khoản hạ tầng chính), role `nghiep-admin-12h`.

## 2. ECS — cluster `aa-cis-dev-cluster` (8 service, không có service nào khác)

| Service | Task def đang chạy | Image tag | Rollout | Running/Desired | Revision mới nhất của family |
|---|---|---|---|---|---|
| aa-cis-dev-api | aa-cis-dev-api:1248 | `dev-1be86655…` | COMPLETED (11:12Z) | 1/1 | 1248 = đang chạy |
| aa-cis-dev-worker | aa-cis-dev-worker:817 | `dev-1be86655…` (repo aa-cis-dev-api) | COMPLETED (11:12Z) | 1/1 | 817 = đang chạy |
| aa-cis-dev-admin | aa-cis-dev-admin:82 | `dev-1be86655…` | COMPLETED (11:11Z) | 1/1 | 82 = đang chạy |
| aa-booking-dev-api | aa-booking-dev-api:157 | `cac94b28…` | COMPLETED (10:19Z) | 1/1 | 157 = đang chạy |
| aa-booking-dev-admin | aa-booking-dev-admin:53 | `cac94b28…` (+ container `test-wp`, wordpress ghim digest) | COMPLETED (10:19Z) | 1/1 | 53 = đang chạy |
| aa-crm-dev-api | aa-crm-dev-api:211 | `52ec4413…` | COMPLETED (09:55Z) | 1/1 | 211 = đang chạy |
| aa-crm-dev-web | aa-crm-dev-web:185 | `bf663b9e…` | COMPLETED (10:04Z) | 1/1 | 185 = đang chạy |
| aa-tripplanner-dev-web | aa-tripplanner-dev-web:22 | `cc7a905b…` | COMPLETED (06:06Z) | 1/1 | 22 = đang chạy |

- CIS api và worker **cùng SHA** `1be86655` (= head `main` CIS, #1636). CIS admin cũng `1be86655`.
- Revision mới nhất mỗi family đều là revision đang chạy; mỗi service chỉ 1 deployment PRIMARY.
- So với cuối S286 (mục 10): CIS api 1238→1248, worker 807→817, admin 77→82; Booking api 154→157, admin 49→53;
  CRM api 209→211, web 183→185; TripPlanner web 21→22.
- Capacity provider (live): api/worker CIS, Booking api, CRM api = `FARGATE_SPOT` weight 3 + `FARGATE` base 1 weight 1;
  bốn staff/web service (CIS admin, Booking admin, CRM web, TripPlanner web) = **chỉ `FARGATE_SPOT`** (đúng quyết định,
  không đổi so với S286).

## 3. Endpoint

| Endpoint | HTTP | Kết quả |
|---|---|---|
| CIS `api-cis.…/health` | 200 | version 0.20.0, git_sha `1be86655` (khớp ECS) |
| CIS `/health/ready` | 200 | db ok, schema_version **469**, required 322, 206 key đã đăng ký |
| Booking `api-booking.…/booking/health` | 200 | version 0.16.0, git_sha `cac94b28` (khớp ECS) |
| Booking `/booking/health/ready` | 200 | db ok, schema_version **bk-063**, storage supply_media + ops_docs configured |
| CRM api `portal.…/crm/health` | 200 | version 0.13.0, git_sha `52ec4413` (khớp ECS) |
| CRM api `/crm/health/ready` | 200 | db ok, schema_version **crm-085** |
| CRM web `portal.…/healthz` | 200 | version 0.13.0, git_sha `bf663b9e` (khớp ECS), auth/staff_auth/academy_auth configured |
| TripPlanner web `tripplanner.…/api/health` | 200 | version 0.16.0, git_sha `cc7a905b` (khớp image tag) |
| TripPlanner `/api/browse?resource=countries` | 200 | 21 nước, tổng 844 tour (không đổi so với S286) |
| CIS admin `aa-cis.…` | 307 → `/admin/upload` | image `dev-1be86655` = run `Deploy Admin Dev` cuối (#1636, 11:06Z, success) |
| Booking admin `booking.…` | 307 → `/login` | image `cac94b28` = run `Deploy Admin Dev` cuối (#298, 10:14Z — **failure ở bước smoke**, xem mục 7.1) |

Header bảo mật (kiểm tay lúc chụp): `booking.…/login`, `/robots.txt`, `/api/auth/session`, `aa-cis.…`, `portal.…/login`,
`tripplanner.…/` đều có HSTS, `x-content-type-options`, `referrer-policy`, `x-frame-options`, `permissions-policy`, CSP.

Lambda TripPlanner (LastUpdateStatus Successful, cập nhật 19/11 13:52Z bởi Deploy Lambdas của TP `1498c1ab`, **không đổi**
từ S286; `backend/` không đổi giữa `1498c1ab` và head `cc7a905b`):

- `aa-tripplanner-dev-browse` CodeSha256 `OIIqbRG39fSmo6q1xW4rtdNQLfDyUPRK1RTxr/4TOeI=`
- `aa-tripplanner-dev-assembly` CodeSha256 `OIIqbRG39fSmo6q1xW4rtdNQLfDyUPRK1RTxr/4TOeI=` (cùng gói)

SHA cũ hơn head nhưng đúng:

- CRM web vẫn `bf663b9e` (#375): commit Partner sau đó (#378, crm-085 ops check settings) không đụng `web/` (diff `web/`
  rỗng), nên Deploy Web Dev không chạy lại. CRM api = head `52ec4413`.

## 4. Migration mới nhất mỗi owner

| Owner | Live (health/ready) | Dòng "Verified" db-schema-reference (21/11 10:27 UTC, origin/master) |
|---|---|---|
| CIS | 469 | 469 |
| Booking | bk-063 | bk-063 |
| CRM | crm-085 | crm-085 |
| TripPlanner | (không có health/ready) | tp-035 |

Tổng 629 version đã đăng ký (S286: 618 → +11: CIS 463–469, bk-063, crm-083/084/085). **Không có** PR
`bot/db-schema-reference` đang mở (bản dump 10:27 đã merge ở root #939). Infra DB Migrate 10:24Z + Migration Apply 10:23Z +
DB Schema Dump + DB Isolation Probe 10:26Z đều success.

## 5. Repo

"Commit" = số commit trên nhánh mặc định sau snapshot S286 (20/11 02:25Z), **đếm theo ngày merge** (commit date trên
GitHub). Repo gốc và Infra đã **viết lại lịch sử + force-push hôm nay** (AA-1161 phase 2): head S286 cũ (`1b2cd959`,
`f2f0d948`) không còn trong lịch sử mới (#917 nay là `1d4ffa22`, #949 là `9c327f66`); đếm từ các commit tương ứng trong lịch
sử mới cho cùng kết quả như đếm theo ngày (23 và 21).

| Repo (nhánh) | Head | Commit | PR mở (checks) | CI cuối trên nhánh mặc định |
|---|---|---|---|---|
| AA-Ecosys (master) | `b3632949` #940 November vulnerability triage decisions (10:42Z) | 23 | #936 bot infra docs (SUCCESS 11, SKIPPED 3; cập nhật 09:45Z) | CodeQL, Docs sync, Secret Scan `b3632949` success; Compliance evidence 08:06Z success; **Catalogue (schedule) failure** 20/11 12:10Z (ngày thứ 4 liên tiếp, xem mục 7) |
| AA-CIS-App (main) | `1be86655` #1636 Platform > Alerts catalogue (11:00Z) | 15 | #1626 dependabot ecr-login 2.2.0 (SUCCESS 25, CANCELLED 2); #1586 dependabot frontend-security (**FAILURE 4**); #1570 release 0.21.0; #1467 CI test durations | Deploy Dev, Deploy Admin Dev, CodeQL, Release Please, Secret Scan `1be86655` success; Nightly integration 00:57Z success |
| AA-Booking (main) | `cac94b28` #298 job check thresholds từ pricing policy + check registry (10:07Z) | 6 | #296 dependabot ecr-login (SUCCESS 17, CANCELLED 2); #276 kit sync; #270 release 0.17.0; #200 draft bk-045 (FAILURE 2, cố ý chưa làm) | Deploy Dev, CodeQL, Release Please, Secret Scan `cac94b28` success; **Deploy Admin Dev `cac94b28` failure** (Public smoke, xem mục 7.1) |
| AA-TripPlanner-Web (main) | `cc7a905b` #291 pin Node base image by digest (06:02Z) | 2 | #292 dependabot ecr-login (SUCCESS 12, CANCELLED 2); #278 release 0.17.0 | CI, CodeQL, Deploy Web Dev, Release Please, Secret Scan `cc7a905b` success; Deploy Lambdas `1498c1ab` (19/11) success |
| AA-Partner (main) | `52ec4413` #378 CRM ops check thresholds (crm-085) + check registry (09:47Z) | 7 | #377 dependabot ecr-login (SUCCESS 19, CANCELLED 1); #355 kit sync; #343 release 0.14.0 | Deploy Dev, CodeQL, Release Please, Secret Scan `52ec4413` success; Deploy Web Dev + Visual `bf663b9e` success; Scrub corpus (schedule) 01:39Z **success** |
| AA-CIS-Infra (main) | `f035317a` #971 copy CIS migration 469 (10:23Z) | 21 | **#935** WAF geo staff host (SUCCESS 16, SKIPPED 5) — cố ý mở | Terraform Apply Dev 09:42Z (#968) success; Terraform Drift 20/11 14:17Z success (chưa có run nào sau 5 lần apply hôm nay); DB Migrate/Schema Dump/Isolation Probe 10:24–10:26Z success; Secret Scan `f035317a` success |

Soát commit xoá nhiều file (từ 20/11 02:25Z, ngưỡng > 20 file xoá / PR merge): **không có** ở cả sáu repo. Commit duy nhất có
xoá file là root `ca1dce75` (#922, xoá 1 file — exemption lean một lần). Lưu ý: root `3b018637` (#921 "move full media sets
to the S3 archive") trong lịch sử mới **chỉ thêm** 1.734 ảnh đã nén (1.471 png, 263 jpg) + sửa 2 file — bộ ảnh gốc đã bị gỡ
khỏi lịch sử bằng lần viết lại, không phải bằng commit xoá; không phải squash từ base cũ.

Vercel: như S286, snapshot không có mục Vercel — mọi admin/web (CIS admin, Booking admin, CRM web, TripPlanner web) chạy trên
ECS (mục 2).

## 6. Cố ý để BẬT / để nguyên cho phiên sau

- **Không có** cờ wave hay công tắc nào được biết là cố ý để BẬT cho phiên sau (snapshot không truy vấn DB).
- Mang từ S286, **chưa kiểm live** ở đây (giá trị nằm trong DB): trần tháng 11 connection `openai-direct` 25 USD (hạ về
  10 USD ngày 01/12); công tắc bắt buộc MFA admin CRM = On, CIS = Off, Booking = Off (chờ business owner đăng ký TOTP).
- Infra **PR #935** (staff web hosts rời luật WAF geo khi MFA admin đã bắt buộc) **vẫn mở có chủ đích**, checks xanh, chờ TOTP.
- Bốn staff/web service chạy **chỉ Fargate Spot** theo quyết định — đã kiểm live (mục 2).
- Release PR mở theo lệ tuần (CIS #1570, Booking #270, TP #278, Partner #343), kit sync (Booking #276, Partner #355) và bốn PR
  dependabot `amazon-ecr-login` 2.2.0 mới hôm nay (CIS #1626, Booking #296, TP #292, Partner #377): không phải việc dở của phiên.

## 7. Lệch giữa live và checklist / điều cần lưu ý

1. **Booking `Deploy Admin Dev` (`cac94b28`, #298, run 10:14Z) = failure.** Deploy ECS + post-deploy verify (ALB host rule)
   **success**, job Visual (deployed host) success 10:20–10:21Z, nhưng **Public smoke (production)** đỏ: 4 test nhận
   **HTTP 403** trên `booking.…` (`GET /login`, `/robots.txt`, trang 404, `/api/auth/session`; lỗi header là hệ quả của
   403). CloudWatch WAF `aa-cis-dev-waf`: rule **`GeoBlockNonAllowed` chặn 12 request trong khung 10:20Z** (các rule khác
   0) → runner GitHub của smoke bị luật geo chặn. Các run Deploy Admin Dev Booking trước đó hôm nay (04:45Z, 06:09Z) xanh.
   Live lúc chụp: rev 53 chạy `cac94b28`, `booking.…` 307 → `/login`, header đủ. Điều phối quyết định chạy lại run
   (liên quan PR #935 về luật geo cho staff host).
2. **Root `Catalogue` (schedule, job "Surface snapshot is current", bước "Surface drift") đỏ ngày thứ 4** (17, 18, 19,
   20/11 12:10Z trên master). Run lịch hôm nay (~12Z) chưa chạy lúc chụp. Vẫn chưa ai xử lý từ S286 mục 7.3.
3. **Infra `Migration Sync (owner copies)` đỏ 3 lần** (20/11 04:41Z, 21/11 06:44Z, 09:54Z), bước "Open or update one PR per
   missing file". Không chặn: các bản copy migration vẫn vào (#951–#971) và live khớp (CIS 469, bk-063, crm-085). Lặp lại
   → nên xem nguyên nhân.
4. Đỏ đã tự hết trong phiên (không tồn đọng): Secret Scan root 03:28Z (`3b018637`) và Infra 03:23Z (gitleaks fingerprint
   sau lần viết lại lịch sử, xanh từ #922/#953); Infra DB Migrate run-script dry run 05:09Z (`aa1155_custom_maker_grants`,
   xanh lại ở #957/#958); Infra Image Scan (running images) 06:03Z "Fail on the gate" lần chạy đầu, xanh 06:16Z.
5. **Terraform Drift**: run cuối 20/11 14:17Z success; hôm nay đã có 5 lần Terraform Apply Dev (04:53Z, 05:13Z, 05:58Z,
   06:01Z, 09:42Z — lần cuối là #968: 26 add / 49 change / 3 destroy theo điều phối) mà **chưa có run drift nào sau đó**
   (lịch 05:37Z nhưng thực tế GitHub chạy ~14Z).
6. Deploy CIS `1be86655` (#1636): run Deploy Dev tạo 11:06Z, ECS rollout COMPLETED 11:12Z (sớm hơn mốc ~11:20Z trong
   checklist); health git_sha khớp.
7. CIS PR #1586 (dependabot frontend-security) vẫn đỏ 4 check — chưa ai xử lý (ghi từ S285, S286).
8. AA-Partner `Scrub corpus` đỏ ở S286 (02:32Z 20/11) đã xanh: run lịch 21/11 01:39Z success.
9. Mục 6 (trần openai-direct, công tắc MFA) chưa kiểm live trong snapshot này.

## Bảng job

Điều phối kiểm qua ECS exec (`tools/ecs/ecsx.sh`, chỉ đọc) lúc 11:17–11:18 UTC:

- `shared.job` queued/running: **0**.
- `booking.job` queued/running: **0**.
- `crm.job`: **3 job định kỳ queued** vừa tạo 11:18:10Z (`crm_heartbeat`, `crm_booking_sync`, `crm_membership_pull`), bình thường.
- Không có wave mở.

## Xử lý sau snapshot (điều phối, 11:25–11:40 UTC)

- Booking `Deploy Admin Dev` (#298, run 44893352921): job Public smoke đỏ vì rule WAF geo chặn runner GitHub → chạy lại
  job lỗi → **success** (smoke + result xanh).
- Infra `Terraform Drift` chạy tay sau 5 lần apply trong ngày: run 44899056663 **success** (không lệch).
- Infra `Migration Sync (owner copies)` đỏ 09:54Z: chạy trùng lúc điều phối tự mở PR copy; các lượt sau (10:20–10:23Z) xanh.
  Không phải lỗi cấu hình.
- Root `Catalogue` (schedule) đỏ 17–20/11: snapshot surface cũ (13 trang/route + 34 setting mới S286–S287). Sửa trong root PR
  chốt phiên: `surface.snapshot.json` làm mới, `features.yaml` gắn mọi mục (thêm CIS-F051 My work, CIS-F052 Compliance
  readiness); `surface.py check` + `catalogue.py check` xanh trên bản clone `main` của 5 repo app.
- Root #936 (infra docs tự sinh) merge `b81ab55f`: `alarms.md` hết đuôi ID ALB / target group.
- CIS #1637 (bỏ mã issue khỏi mô tả trên Catalogue, timeout CRM 5 s, cache peer 30 s): đang ship lúc ghi.
- CIS #1637 merge `15814d6e`, deploy COMPLETED ~12:20 UTC: api `aa-cis-dev-api:1249`, worker `:818`, admin `:83`, cả ba
  `15814d6e` (`/health` khớp). Đây là SHA CIS cuối phiên (thay `1be86655` ở mục 2–3).
