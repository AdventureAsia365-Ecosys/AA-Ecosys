# S286 — Snapshot trạng thái live cuối phiên

Chụp lúc **2026-11-20 02:20–02:25 UTC (09:20–09:25 giờ VN)**, Claude Code (subagent chỉ đọc). Nguồn: AWS CLI một dòng
(profile `aa365-admin`, us-west-1), `gh` (chỉ đọc), `curl`. Bảng job (`shared.job`, `booking.job`, `crm.job`) và các giá trị
lưu trong DB (trần connection, công tắc MFA) **không** truy vấn ở đây — điều phối tự kiểm.

## 1. STS

- `aa365-admin` → **acc2** (đúng tài khoản hạ tầng chính), role `nghiep-admin-12h`.

## 2. ECS — cluster `aa-cis-dev-cluster` (8 service, không có service nào khác)

| Service | Task def đang chạy | Image tag | Rollout | Running/Desired | Revision mới nhất của family |
|---|---|---|---|---|---|
| aa-cis-dev-api | aa-cis-dev-api:1236 | `dev-daec5413…` | COMPLETED | 1/1 | 1236 = đang chạy |
| aa-cis-dev-worker | aa-cis-dev-worker:805 | `dev-daec5413…` (repo aa-cis-dev-api) | COMPLETED | 1/1 | 805 = đang chạy |
| aa-cis-dev-admin | aa-cis-dev-admin:77 | `dev-87cbdb2b…` | COMPLETED | 1/1 | 77 = đang chạy |
| aa-booking-dev-api | aa-booking-dev-api:154 | `b71fca9c…` | COMPLETED | 1/1 | 154 = đang chạy |
| aa-booking-dev-admin | aa-booking-dev-admin:48 | `b71fca9c…` (+ container `test-wp`, wordpress ghim digest) | COMPLETED (lúc 02:19Z đang IN_PROGRESS, 2 deployment — deploy #291 vừa chạy; 02:23Z đã COMPLETED, 1 deployment) | 1/1 | 48 = đang chạy |
| aa-crm-dev-api | aa-crm-dev-api:208 | `1f7d1cf9…` | COMPLETED | 1/1 | 208 = đang chạy |
| aa-crm-dev-web | aa-crm-dev-web:182 | `b163d81a…` | COMPLETED | 1/1 | 182 = đang chạy |
| aa-tripplanner-dev-web | aa-tripplanner-dev-web:21 | `0d626f61…` | COMPLETED | 1/1 | 21 = đang chạy |

- CIS api và worker **cùng SHA** `daec5413` (= head `main` CIS, #1619).
- Revision mới nhất mỗi family đều là revision đang chạy.
- Capacity provider (live): api/worker CIS, Booking api, CRM api = `FARGATE_SPOT` weight 3 + `FARGATE` base 1 weight 1;
  bốn staff/web service (CIS admin, Booking admin, CRM web, TripPlanner web) = **chỉ `FARGATE_SPOT`** (đúng quyết định).

## 3. Endpoint

| Endpoint | HTTP | Kết quả |
|---|---|---|
| CIS `api-cis.…/health` | 200 | version 0.20.0, git_sha `daec5413` (khớp ECS) |
| CIS `/health/ready` | 200 | db ok, schema_version **462**, required 322 |
| Booking `api-booking.…/booking/health` | 200 | version 0.16.0, git_sha `b71fca9c` (khớp ECS) |
| Booking `/booking/health/ready` | 200 | db ok, schema_version **bk-062**, storage supply_media + ops_docs configured |
| CRM api `portal.…/crm/health` | 200 | version 0.13.0, git_sha `1f7d1cf9` (khớp ECS) |
| CRM api `/crm/health/ready` | 200 | db ok, schema_version **crm-082** |
| CRM web `portal.…/healthz` | 200 | version 0.13.0, git_sha `b163d81a` (khớp ECS), auth/staff_auth/academy_auth configured |
| TripPlanner web `tripplanner.…/api/health` | 200 | version 0.16.0, git_sha `0d626f61` (khớp image tag) |
| TripPlanner `/api/browse?resource=countries` | 200 | 21 nước, tổng 844 tour |
| CIS admin `aa-cis.…` | 307 → `/admin/upload` | image `dev-87cbdb2b` = run `Deploy Admin Dev` cuối (#1620, 01:24Z, success) |
| Booking admin `booking.…` | 307 → `/login` | image `b71fca9c` = run `Deploy Admin Dev` cuối (#291, 02:15Z — xem mục 7) |

Lambda TripPlanner (LastUpdateStatus Successful, cập nhật 19/11 13:52Z bởi Deploy Lambdas của TP `1498c1ab`, không đổi
trong phiên):

- `aa-tripplanner-dev-browse` CodeSha256 `OIIqbRG39fSmo6q1xW4rtdNQLfDyUPRK1RTxr/4TOeI=`
- `aa-tripplanner-dev-assembly` CodeSha256 `OIIqbRG39fSmo6q1xW4rtdNQLfDyUPRK1RTxr/4TOeI=` (cùng gói)

SHA cũ hơn head nhưng đúng:

- CRM api vẫn `1f7d1cf9`: 3 commit Partner sau đó (#367 smoke, #368 lean guard, #369 export AI columns) không đụng `api/`
  (diff `api/` rỗng), nên Deploy Dev không chạy lại.
- TripPlanner web vẫn `0d626f61`: commit sau đó không đụng `web/` (diff rỗng); Deploy Web Dev cuối `0d626f61` success.

## 4. Migration mới nhất mỗi owner

| Owner | Live (health/ready) | Dòng "Verified" db-schema-reference (20/11 00:48 UTC, origin/master) |
|---|---|---|
| CIS | 462 | 462 |
| Booking | bk-062 | bk-062 |
| CRM | crm-082 | crm-082 |
| TripPlanner | (không có health/ready) | tp-035 |

Tổng 618 version đã đăng ký. **Không có** PR `bot/db-schema-reference` đang mở (bản dump 00:48 đã merge ở root #916).
Infra DB Migrate + Migration Apply + DB Schema Dump + DB Isolation Probe 00:44–00:47Z đều success.

## 5. Repo

"Commit" = số commit trên nhánh mặc định sau snapshot S285 (19/11 15:44Z).

| Repo (nhánh) | Head | Commit | PR mở (checks) | CI cuối trên nhánh mặc định |
|---|---|---|---|---|
| AA-Ecosys (master) | `1b2cd959` #917 AI Use Register v1.15 (01:13Z) | 9 | #860 bot infra docs (SUCCESS 7, SKIPPED 3, CANCELLED 1; cập nhật 00:15Z) | Docs sync + Secret Scan `1b2cd959` success; **Catalogue (schedule) failure** 17/11, 18/11, 19/11 (xem mục 7) |
| AA-CIS-App (main) | `daec5413` #1619 AI disclosure WordPress/Facebook/export (01:32Z) | 10 | #1586 dependabot frontend-security (**FAILURE 4**); #1570 release 0.21.0; #1467 CI test durations | Deploy Dev, CodeQL, Release Please, Secret Scan `daec5413` success; Deploy Admin Dev `87cbdb2b` success; Nightly integration success |
| AA-Booking (main) | `b71fca9c` #291 My work band + stop-sales review (02:08Z) | 5 | #276 kit sync; #270 release 0.17.0; #200 draft bk-045 (FAILURE 2, cố ý chưa làm) | Deploy Dev, CodeQL, Release Please, Secret Scan `b71fca9c` success; Deploy Admin Dev `b71fca9c` deploy + verify + smoke success, job Visual còn chạy lúc chụp |
| AA-TripPlanner-Web (main) | `6be0d0e5` #289 lean repo guard (19/11 23:53Z) | 1 | #278 release 0.17.0 | CI, CodeQL, Release Please, Secret Scan `6be0d0e5` success; Deploy Lambdas `1498c1ab` success |
| AA-Partner (main) | `b163d81a` #369 AI columns trên export My Content (01:14Z) | 3 | #355 kit sync; #343 release 0.14.0 | Deploy Web Dev `b163d81a` **success** (đã hết đỏ), Visual + CodeQL success; Deploy Dev `1f7d1cf9` success; **Scrub corpus (schedule) failure** 01:50Z (xem mục 7) |
| AA-CIS-Infra (main) | `f2f0d948` #949 allowlist cột role label bk-062 trong PII report (00:48Z) | 9 | **#935** WAF geo staff host (SUCCESS 12, SKIPPED 5) — cố ý mở | Terraform Apply Dev 00:12Z success; **Terraform Drift 00:10Z success**; DB Migrate/Schema Dump 00:45Z success; Secret Scan `f2f0d948` success |

Soát commit xoá nhiều file (từ 19/11 15:44Z, ngưỡng ≥ 3 file xoá): chỉ **Infra `c3b9fc9c` (#945)** xoá 9/16 file — toàn bộ là
`dist/lambdas/*.zip` của Lambda đã nghỉ (đúng mục đích PR "drop the retired Lambda zips"), **không phải revert âm thầm**.
Năm repo còn lại không có commit nào xoá ≥ 3 file.

## 6. Cố ý để BẬT / để nguyên cho phiên sau

- Connection `openai-direct`: trần tháng 11 **25 USD**, hạ về **10 USD ngày 01/12** — theo điều phối; snapshot này **chưa
  kiểm live** (giá trị nằm trong DB).
- Công tắc bắt buộc MFA admin: **CRM = On**, **CIS = Off**, **Booking = Off** (chờ business owner đăng ký TOTP) — theo điều
  phối; **chưa kiểm live** ở đây.
- Infra **PR #935** (staff web hosts rời luật WAF geo khi MFA admin đã bắt buộc) **mở có chủ đích**, checks xanh, chờ TOTP.
- Bốn staff/web service chạy **chỉ Fargate Spot** theo quyết định — đã kiểm live (mục 2).
- Release PR mở theo lệ tuần (CIS #1570, Booking #270, TP #278, Partner #343) và kit sync (Booking #276, Partner #355):
  không phải việc dở của phiên.

## 7. Lệch giữa live và checklist / điều cần lưu ý

1. **Booking `Deploy Admin Dev` (`b71fca9c`, #291) còn `in_progress` lúc 02:24Z** (bắt đầu 02:15Z), nhưng các job chính
   đã **success**: deploy ECS, post-deploy verify (ALB host rule), public smoke (production), "Deploy Admin Dev result".
   Chỉ còn job **Visual (deployed host, public pages)** đang chạy. ECS: rollout COMPLETED, rev 48 chạy `b71fca9c`,
   `booking.…` 307 → `/login`. Điều phối kiểm kết luận job Visual một lần.
2. **AA-Partner `Scrub corpus` (Guardrails, schedule) đỏ 01:50Z** trên `b163d81a`: 260 mẫu, **12 leak**
   (`vi-099`, `en-246`, `vi-247`, `en-249`, `vi-250`, `en-251`…). Các ngày 16–19/11 đều xanh → lần đỏ đầu, trùng sau khi
   merge #369 (export AI columns) / thêm mẫu corpus mới (id 246–251). Cần xem: mẫu mới hay guardrail đổi hành vi.
3. **Root `Catalogue` (schedule, job "Surface snapshot is current", bước "Surface drift") đỏ 3 ngày liền** (17/11, 18/11,
   19/11 12:xxZ trên master). Các run trên nhánh PR hôm nay xanh — nghĩa là snapshot surface trên master lệch với live/code
   theo lịch đêm. S285 snapshot không ghi việc này.
4. Terraform Drift: đỏ 19/11 14:38Z, 15:51Z, 22:31Z → **xanh 22:45Z và 00:10Z** (đã sạch trong phiên). Terraform Apply Dev
   00:12Z (`ebc8c1db`) chạy **sau** run drift xanh cuối; chưa có run drift nào sau apply đó (lịch đêm sẽ xác nhận).
5. AA-Partner Deploy Web Dev (đỏ ở S285 vì Studio UI smoke 1/69) **đã xanh** từ #367 — mục 7.1 của S285 đã giải quyết.
6. Root `Docs sync` đỏ 19/11 17:49Z (`9523da1e`) nhưng các run sau (tới `1b2cd959`) xanh — không còn tồn đọng.
7. CIS PR #1586 (dependabot frontend-security) vẫn đỏ 4 check — chưa ai xử lý (đã ghi ở S285).
8. Mục 6 (trần openai-direct, công tắc MFA) chưa kiểm live trong snapshot này.

## Bảng job

Điều phối kiểm qua ecsx lúc 02:20Z (đếm queued/running, không lọc thời gian): `shared.job` 0, `booking.job` 0, `crm.job` 2 job định kỳ đang queued (`crm_heartbeat`, `crm_booking_sync`). Không wave mở, không cờ wave nào để BẬT.

## 9. Cập nhật cuối phiên (~04:40Z)

| Service | Task def | Image | Rollout | Ghi chú |
|---|---|---|---|---|
| aa-crm-dev-api | aa-crm-dev-api:209 | `e70b106d…` | COMPLETED 1/1 | Partner #371 (lớp kiểm tên người cục bộ cho scrubber); `/crm/health` git_sha khớp |
| aa-booking-dev-admin | aa-booking-dev-admin:49 | `a4762dfa…` | COMPLETED | Booking #292 (F4/F5, chỉ frontend) |
| aa-booking-dev-api | aa-booking-dev-api:154 | `b71fca9c…` | COMPLETED | không đổi (#292 không đụng api) |

- AA-Partner `Scrub corpus` trên main `e70b106d` (run 44667781727): **success** — hết đỏ từ 01:50Z.
- Deploy Dev Partner `e70b106d` (run 44667781693): success.

## 10. Sau lane l11 (~05:10Z)

| Service | Task def | Image | Rollout |
|---|---|---|---|
| aa-cis-dev-api | aa-cis-dev-api:1238 | `e29ee061…` | COMPLETED 1/1 |
| aa-cis-dev-worker | aa-cis-dev-worker:807 | `e29ee061…` (cùng SHA api) | COMPLETED 1/1 |
| aa-crm-dev-web | aa-crm-dev-web:183 | `44daca2e…` | COMPLETED 1/1 |

- CIS `/health/ready`: schema_version **464**, git_sha `e29ee061`. Migration CIS 463 + 464 applied (contract); PR
  schema-reference #919 tự merge (CIS 464).
- Còn lại không đổi so với mục 9: Booking api :154 `b71fca9c`, admin :49 `a4762dfa`; CRM api :209 `e70b106d`; bk-062,
  crm-082, tp-035. `shared.job` 0 job (kiểm 04:06Z); không wave, không cờ để BẬT.
