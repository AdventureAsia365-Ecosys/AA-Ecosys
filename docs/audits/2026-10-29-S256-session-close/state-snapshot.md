# S256 — trạng thái kiểm cuối phiên (29/10/2026 09:25 +07)

Nguồn: lệnh một dòng AWS (acc2), `/health` + `/health/ready` các app, `gh`. Không ghi account ID, ARN hay giá trị secret.

## ECS (cluster aa-cis-dev-cluster)

| Service | Task def đang chạy | Image | Rollout | Revision mới nhất = đang chạy |
|---|---|---|---|---|
| aa-cis-dev-api | :906 | dev-`3994a1a8` | COMPLETED | có |
| aa-cis-dev-worker | :472 | dev-`3994a1a8` (cùng SHA với api) | COMPLETED | có |
| aa-booking-dev-api | :84 | `5a115023` | COMPLETED | có |
| aa-crm-dev-api | :76 | `a6d6f282` | COMPLETED | có |
| aa-crm-dev-web | :47 | `1e32e7f1` (release 0.9.0) | IN_PROGRESS lúc chụp | có |

RDS `aa-cis-dev-db`: available, parameter group in-sync (`pg_stat_statements.max` = 10000 sau reboot 06:40).

## Endpoint

| Endpoint | Kết quả |
|---|---|
| CIS `/health/ready` | ok, schema 301, required 301, git `3994a1a8`, registered_keys 264…301 (baseline 263) |
| Booking `/booking/health/ready` | ok, `bk-033`, storage supply_media + ops_docs configured |
| CRM `/crm/health/ready` | ok, `crm-023` |
| Portal `/healthz` | ok, `87f8bb47` (0.8.0) |
| TripPlanner `/api/health` | ok, `0aead2b7` (0.11.0) |
| Lambda browse / assembly | CodeSha256 `RY5lkl0T…` (không đổi trong phiên) |

## Migration mới nhất mỗi owner

CIS 301 (297, 298, 300, 301 áp trong phiên), Booking bk-033, CRM crm-023, TripPlanner tp-020 (không đổi).

## Vercel

CIS admin production `f80429a9` (#1126; chứa #1127, #1128, #1129); TripPlanner `0aead2b7`; Booking admin theo main Booking; project `aa-cis-portal` đã xoá (404).

## Bảng job / wave

`shared.job`: chỉ chuỗi `place_relocate` (AA-997) queued có chủ đích, chạy theo credit Geoapify mỗi đêm (~31/10 xong); 0 wave mở. `booking.job` rỗng. `crm.job` đọc gián tiếp qua guard DB Migrate (rảnh lúc apply 301).

## Cố ý để BẬT

- Chuỗi relocate AA-997 (job tự nối tiếp mỗi ngày).
- Membership E2E studio (Atlas & Hearth) ở role owner (portal smoke cần đủ quyền); thông tin đăng nhập ở `crm/dev/e2e-test-studio/viewer`.

## Cờ giữ TẮT

`T9_BRIEF_GROUNDING_MODE` (AA-790 r9 FAIL), `DB_AUTO_APPLY` (AA-993 M3 chưa build), GuardDuty (chờ quyết định).

## PR còn mở lúc chụp

Booking #143 (đồng bộ kit, CI), Booking #138 + CIS #1113 (release) — xem log phiên cho kết quả cuối.
