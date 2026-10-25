# S250 close — ảnh chụp trạng thái live (25/10/2026, ~05:45–06:00 UTC)

Đọc từ nguồn live (AWS CLI read-only profile `aa365-admin`, curl, `gh`, Vercel CLI), không lấy từ trí nhớ.
Không ghi account id, ARN, hostname nội bộ hay giá trị secret.

STS: profile `aa365-admin` trả về đúng acc2 (us-west-1).

## ⚠️ Phát hiện cần xử lý trước mọi `terraform apply` (AA-CIS-Infra main)

> **Cập nhật 25/10 ~06:15 UTC — ĐÃ KHẮC PHỤC:** Infra **#382** (`581b6c4a`) khôi phục main = main trước #380 (5bdde4d + #379) + chỉ phần của #380; `git diff 5bdde4d..main` không còn file bị xoá; Terraform Plan của #382: **"No changes"** (hạ tầng live chưa từng bị đụng). Bài học: `skill/aa-lessons/lessons.md` (squash bằng merge-base sau fetch).

Infra **#380** (`af8ac53b`, AA-853 schema drift report, squash merge 04:17:12Z bởi `aa-agent`) là commit một cha
(`b1d2e924`) nhưng **xoá ngược nội dung của #372–#378 và #381** (+1532 / −3616). Trên `origin/main` hiện tại:

- MẤT `db/migrations/cis/279_countries_iso3166.sql`, `280_writing_rule.sql`, `db/migrations/crm/015_crm_mail.sql`
  (đã áp lên Dev rồi, chỉ bản copy trong Infra mất).
- MẤT `accounts/aa365/crm_mail.tf` (AA-945: MX crm-in, SES ingest rule, quyền ingest) và phần identity của #374.
- `modules/ecs`: bỏ `S1_WRITER_V2` (#372) và env Redis TLS/AUTH; `modules/elasticache`: `aws_elasticache_cluster.main`
  (node Redis cũ không mã hoá) quay lại; output trỏ về node cũ.
- `accounts/aa365/tripplanner.tf`: mất route `ANY /me/{proxy+}` (#381, AA-908).
- Ghi chú `docs/implementation-notes/AA-874.md`, `AA-908.md`, runbook `crm-mail-ingest.md` bị xoá.

Live **chưa bị ảnh hưởng** (chưa có apply nào sau 04:17Z): route `/me/{proxy+}` vẫn có trên API TripPlanner, node cũ
không tồn tại, worker vẫn `S1_WRITER_V2=on`. Nhưng một `terraform apply` từ main lúc này sẽ tạo lại node Redis cũ, xoá
route `/me/*`, gỡ hạ tầng mail CRM, và đăng ký revision ECS không có `S1_WRITER_V2` / Redis TLS (deploy CIS kế tiếp sẽ
kế thừa). Cần một PR khôi phục (re-apply diff `b1d2e924..af8ac53b` ngược cho các file ngoài phạm vi AA-853) trước
apply/deploy kế tiếp. Các repo khác: quét commit từ 24/10 12:00Z, không thấy commit xoá bất thường (CIS `7d855938`
−1317 là đóng băng portal có chủ đích).

## ECS (cluster aa-cis-dev-cluster)

| Service | Task definition | Image tag | Running | Rollout |
|---|---|---|---|---|
| aa-cis-dev-api | :819 | dev-4ce6a3aa | 1/1 | COMPLETED (05:42Z) |
| aa-cis-dev-worker | :385 | dev-4ce6a3aa | 1/1 | COMPLETED (05:43Z) |
| aa-booking-dev-api | :56 | 174a194c | 1/1 | COMPLETED |
| aa-crm-dev-api | :41 | 88be0b18 | 1/1 | COMPLETED |
| aa-crm-dev-web | :19 | 923e2069 | 1/1 | COMPLETED |

- CIS api và worker cùng SHA `4ce6a3aa` (#998 writing memory P1). Worker :385 env `S1_WRITER_V2=on`.
- Booking live `174a194c` (#90); main `55b8679e` là release 0.6.0 (chỉ CHANGELOG/manifest) → `/booking/health` còn báo 0.5.0.
- CRM api live `88be0b18` (#47); main `923e2069` là release 0.4.0 (chỉ CHANGELOG/manifest/version) — web đã chạy bản release.

## Health

| App | Endpoint | Kết quả |
|---|---|---|
| CIS | `/health` | 200, version 0.9.0, git_sha 4ce6a3aa |
| CIS | `/health/ready` | 200, schema **280** (required 280) |
| Booking | `/booking/health` | 200, version 0.5.0, git_sha 174a194c |
| Booking | `/booking/health/ready` | 200, schema **bk-024** |
| CRM api | `/crm/health` | 200, version 0.3.0, git_sha 88be0b18 |
| CRM api | `/crm/health/ready` | 200, schema **crm-015**, membership_feed ok, keys kms |
| CRM web | `/healthz` | 200, version 0.4.0, git_sha 923e2069, auth_configured true |
| TripPlanner | `/api/browse?resource=countries` | 200 (không có endpoint `/health`) |

TripPlanner Lambdas `aa-tripplanner-dev-browse` / `aa-tripplanner-dev-assembly`: cùng CodeSha256 (`NDIEgpZq…`),
cập nhật 25/10 02:30Z (TripPlanner #147). Route HTTP API: `/browse/*`, `/browse/search`, `/trip/*`, narrate, `/me/*`.

## Migration mới nhất mỗi owner

CIS **280** · Booking **bk-024** · TripPlanner **tp-019** · CRM **crm-015**.
Nguồn: `/health/ready` (CIS, Booking, CRM) + dòng Verified của dump 04:44Z (PR root #249 `bot/db-schema-reference`,
còn mở). Áp trong S250: CIS 275–280, bk-023/bk-024, tp-019, crm-012…crm-015.

## Vercel (production mới nhất)

| Project | Commit | Lúc (UTC) |
|---|---|---|
| aa-cis-frontend (CIS admin) | AA-CIS-App 4ce6a3aa (#998) | 25/10 05:38 |
| aa-booking-admin | AA-Booking f2eedbdf (#86) | 24/10 19:25 |
| aa-tripplanner | AA-TripPlanner-Web 49738c6f (#148) | 25/10 03:05 |
| aa-cis-portal | AA-Partner a90c1c26 (#46) — portal giờ deploy từ AA-Partner | 25/10 02:56 |

Booking #90 chỉ đổi `backend/` nên không có deploy admin mới; release commit các repo không build lại (đúng).

## Bảng job và wave

- `shared.job`: deploy-gate của CIS deploy #998 lúc 05:38Z trả `active 0, safe_to_deploy true`. Không truy vấn trực
  tiếp bảng lúc chụp (không ECS exec trong bước này).
- `booking.job`: không kiểm lúc chụp.
- Wave AA-645: `cw_sri-lanka_2` CLOSED 05:29:23Z; driver dừng bằng cờ STOP lúc 05:43:48Z trước `cw_sri-lanka_3`
  (Nghiệp chọn). Không có wave mở, không GAP đang giữ (`s250/GAP` không còn; gap2 released 05:43Z).
- Tổng S1 S250 (orchestrator tính từ các `cw-*-report.json`): 17 wave theo nước, 578 tour (thêm pilot 3 + wave50 50
  trước đó → 631/810 tour trên v2), 578 publish, 0 review, 0 giữ v1; gate pages 226→26, phủ số liệu 0,422→0,675,
  brand-fit 7,69→7,99; chi phí $42,05 ($0,0728/tour); luỹ kế $46,16 / $120. Còn 179 tour cho S251: Sri Lanka 3 (12) +
  India 1–4 (167).

## Cố ý để BẬT cho S251

- Worker `S1_WRITER_V2=on` (live :385). Lưu ý: nguồn Terraform của công tắc này đang mất trên Infra main do #380 (xem trên).
- Route `s1_generate` = sonnet-5-5 (acc3), đặt 24/10 08:51:15Z (theo file route của driver; không đọc lại DB lúc chụp).
- Quyết định giữ/trả route v2 đang chờ Nghiệp (đề xuất: giữ v2 làm mặc định).
- RDS `aa-cis-dev-db` available (db.t4g.small). Snapshot thủ công `aa-cis-dev-db-pre-s1-*`: 20 bản (pilot → sri-lanka-2),
  hết hạn theo luật 30 ngày AA-869.

## Redis (AA-874)

- Replication group `aa-cis-dev-cache`: available, engine valkey 8.2.0, `cache.t3.micro`, 1 node
  (`aa-cis-dev-cache-001`), TransitEncryption **true** (mode **required**), AtRest **true**, AuthToken **true**;
  không Multi-AZ, không failover, snapshot retention 0.
- Node cũ `aa-cis-dev-redis` **không còn** (`describe-cache-clusters` chỉ thấy `aa-cis-dev-cache-001`), xoá bởi Infra #373.
  Subnet group tên cũ `aa-cis-dev-redis-subnet-group` vẫn được group mới dùng (chỉ là tên).

## Ghi chú chi phí (giá niêm yết us-west-1, đối chiếu Cost Explorer đợt audit đầu tháng 11)

- ElastiCache: Valkey `cache.t3.micro` on-demand $0,0176/giờ ≈ **$12,9/tháng**. Node Redis cũ đã xoá nên không còn chạy
  song song (chỉ trùng trong lúc blue/green ở S250).
- WAF (REGIONAL): `aa-cis-dev-waf` 5 rule ≈ $5 + 5×$1 = **$10/tháng**; `aa-identity-dev-pools` (tạo S250, Infra #360/#374,
  AA-908) 4 rule ≈ $5 + 4×$1 = **$9/tháng**; cộng $0,60 / triệu request (Dev gần như 0).

## Repos (head nhánh mặc định lúc chụp)

| Repo | Head | PR mở |
|---|---|---|
| AA-CIS-App main | 4ce6a3aa (#998) | #999 release 0.10.0 (release-please) |
| AA-Booking main | 55b8679e (#85 release 0.6.0) | không |
| AA-TripPlanner-Web main | 63f0aad3 (#146 release 0.8.0) | không |
| AA-CIS-Infra main | af8ac53b (#380 — xem phát hiện ở đầu) | không |
| AA-Partner main | 923e2069 (#38 release 0.4.0) | không |
| AA-Ecosys master | d79eec7f (#244) | #249 regenerate db-schema-reference (bot) |

## CI đáng chú ý

- DB Schema Dump (Infra) 3 lần gần nhất (03:14Z, 03:15Z, 04:43Z) đều `failure`; lần 04:43Z hỏng ở bước báo cáo
  "Design ERD drift (report)", còn dump + drift report + mở root PR vẫn chạy được (PR #249). Hai lần trước chưa xem log. Lần 04:43Z chạy trên `af8ac53b`
  (thiếu file copy 279/280/crm-015) nên báo cáo drift của lần đó cần đọc lại sau khi khôi phục.
