# S254: snapshot trạng thái live lúc chốt phiên (28/10/2026, 11:40 +07 = 04:40 UTC)

Tác nhân: Claude Code. Mọi số dưới đây đọc từ nguồn thật lúc chốt phiên (`snapshot.sh` 11:40:05 +07, STS acc2 ok),
không chép từ trí nhớ của phiên. Chỗ ghi «ORCH» là việc điều phối điền sau (không có trong lần chụp này).

## AWS acc2 (STS ok)

| Service ECS | Task def đang chạy | Rollout | Chạy / mong muốn | Image | Revision mới nhất của family |
|---|---|---|---|---|---|
| aa-cis-dev-api | :877 | COMPLETED | 1/1 | `dev-8aabaf0a` | :877 (khớp) |
| aa-cis-dev-worker | :443 | COMPLETED | 1/1 | `dev-8aabaf0a` | :443 (khớp) |
| aa-booking-dev-api | :76 | COMPLETED | 1/1 | `d78ae200` | :76 (khớp) |
| aa-crm-dev-api | :69 | COMPLETED | 1/1 | `c35ad2d5` | :69 (khớp) |
| aa-crm-dev-web | :37 | COMPLETED | 1/1 | `3d338504` | :37 (khớp) |
| aa-crm-dev-portal | :10 | COMPLETED | 1/1 | `8af302ee` | :10 (khớp) |

- CIS api và worker cùng SHA `8aabaf0a` (#1089, giữ chặng tự di chuyển trong place build) = head CIS main.
- Booking `d78ae200` = #130 (AA-996 lát 2: Supplier + ma trận giá + picker). **#130 gây regression:**
  `GET /catalog/trip-plans` → 503 `catalog_unavailable` (truy vấn LATERAL đọc view/cột CIS chưa grant cho role
  `booking`; stub CI che lỗi). Hotfix **Booking #131** (fail-soft + log SQLSTATE + stub khớp live) đang merge lúc chụp:
  SHA merge «ORCH: SHA #131», task def Booking sau deploy «ORCH: :77?», verify `/catalog/trip-plans` 200 «ORCH».
- CRM: api `c35ad2d5` (#101 bỏ bridge `cis-portal`, redeploy sau Infra #452: 0 biến bridge); web `3d338504` (#104
  hotfix import kit); portal `8af302ee` (#102 S2a vendor kit core). Check trên head Partner main `3d338504` xanh hết,
  gồm "Vendored CIS copies", Portal Build, Web Build, Post-deploy verify.

## Endpoint

| App | `/health` | `/health/ready` |
|---|---|---|
| CIS | ok, 0.12.0, git_sha `8aabaf0a` | ok, db ok, `schema_version` **292** (required 287) |
| Booking | ok, 0.8.0, git_sha `d78ae200` | ok, db ok, schema **bk-032** |
| CRM (partner-dev) | ok, 0.6.0, git_sha `c35ad2d5` | ok, db ok, schema **crm-022**, membership_feed ok, keys kms |
| TripPlanner | ok, 0.9.0, git_sha `be5cbc41` (#171) | — |

Migration mới nhất mỗi owner (dòng "Verified" của `docs/architecture/db-schema-reference.md`, dump 04:28 UTC 28/10,
root #294): CIS **292**, TripPlanner **tp-020** (không đổi trong phiên), Booking **bk-032**; CRM **crm-022** (theo
`/crm/health/ready`, không đổi trong phiên).

Migration áp trong phiên: Booking bk-029 (AA-996), bk-030 (AA-682 S4), bk-031 (AA-996 compact), bk-032 (AA-996 lát 2,
DB Migrate check 40632088145 / apply 40632244244, root bot #294); CIS 291/292 (AA-919 WM-19/WM-21, Infra #453).

## Vercel (production)

- TripPlanner: `be5cbc41` (#171, đọc từ `/api/health`).
- CIS admin (`aa-cis-frontend`): `3e5976dc` (#1088 TenantSelect, Vercel Deploy run xanh 00:21Z 28/10; các commit CIS
  sau đó không đổi `frontend/**`).
- Booking admin (`aa-booking-admin`): `d78ae200` (#130, Vercel Deploy xanh 04:35Z 28/10); sẽ đi tiếp theo #131.
- Portal: chạy Fargate (`aa-crm-dev-portal:10`), không qua Vercel.
- `aa-cis-portal`: chỉ còn là đường rollback (301 sang `portal.`) tới đợt dọn từ 03/11 (AA-979 §4.5).
- Region function `sfo1` cho CIS admin, Booking admin, TripPlanner (hiệu lực từ deploy kế). Retention 4 project
  (06:35): preview 2 tuần, production 1 tháng, canceled/errored 1 tuần.

## Bảng job và wave

- `shared.job`: **0** queued/running (`BUSY 0 []`, 11:40).
- `booking.job`, `crm.job`, wave mở: «ORCH: xác nhận — snapshot 11:40 chỉ đếm `shared.job`».

## Repo (head nhánh mặc định; PR còn mở)

| Repo | Head | PR mở |
|---|---|---|
| AA-CIS-App | `8aabaf0a` (#1089) | #1075 (release) |
| AA-Booking | `d78ae200` (#130) | #116 (release); #131 hotfix đang merge «ORCH» |
| AA-TripPlanner-Web | `be5cbc41` (#171) | #166 (release) |
| AA-Partner | `3d338504` (#104) | #103 (release) |
| AA-CIS-Infra | `82400b9e` (#458, copy bk-032) | 0 |
| AA-Ecosys (gốc) | `a3888057` (#294) | #291 (bot infra docs); root PR S254 mở lúc chốt |

Chỉ còn PR release / bot; mọi PR code của phiên đã merge (trừ #131 đang merge).

## Cố ý để BẬT cho phiên sau

- `JOB_TEST_KINDS=1` trên Dev: CIS api + worker (`noop_sleep`) và **Booking** (Infra #449: `bk_noop_sleep`) — cho bài
  chứng minh nhả/nhận lại job (AA-993 G4/G5). Worker CIS `JOB_WORKER_GRACE_SECONDS=100` như trước.
- Vercel deployment retention đã đặt cho 4 project (preview 2w, production 1m, canceled/errored 1w).
- Branch protection: **H1** (AA-Partner main bắt buộc Portal Build + Web Build), **H2** (AA-CIS-App main bắt buộc
  Frontend Lint). H3 (Kit provenance) chưa làm.
- Writer S1 v2 + route `s1_generate` = sonnet-5-5 (mặc định cố định từ S250).
- `PLACE_PIPELINE_AUTO=on` trên CIS api + worker (tour mới/đổi tự có địa điểm).
- Writing memory: release 0 active lại sau vòng thử WM-22 (draft #2 → active → rollback).
- Run-script Infra: G4 proof về `dry_run` (Infra #455); `aa682_s4_live_check` chạy `dry_run` (rolled back, TC-000024 /
  BIL-000001 không giữ lại). Dữ liệu tổng hợp S253 (TC-000018/19/22/23, nhãn `SYNTHETIC S253`) giữ nguyên.
