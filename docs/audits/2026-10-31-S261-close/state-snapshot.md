---
id: OPS-08-s261-state-snapshot
title: "S261 state snapshot (31/10/2026)"
description: "Trạng thái live cuối phiên S261 (kiểm ~10:59–11:05Z): ECS, health, migration, Lambda, Vercel, bảng job, repo, CI đỏ, việc cố ý để bật; mỗi số kèm lệnh kiểm, chỗ không kiểm ghi 'chưa kiểm'."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-997, AA-952, AA-1002, AA-1014, AA-804, AA-873, AA-961, AA-967]
---

# Ảnh chụp trạng thái live — kết thúc S261 (31/10/2026, kiểm lúc ~10:59–11:05Z)

Tác nhân: Claude Code (subagent). Chỉ đọc, không ghi file, không push/merge/deploy, không ECS exec. Luật S261
(memory `verify-live-before-claiming`): mỗi số dưới đây đến từ một lần kiểm live, có ghi lệnh; chỗ không kiểm ghi
"chưa kiểm".

## Cần biết trước

1. **CI quét secret của repo gốc đỏ trên `master` từ 02:48Z** (5 lần chạy liên tiếp failure, gần nhất ở head
   `b7779bfb`). gitleaks báo `aws-access-token` (giá trị đã bị che) trong `tools/docs/test_docs_reader.py`, đến từ commit
   `97a3c2b8` (#302, 28/10). Có thể là dữ liệu giả trong test (chuỗi `...ghij.execute-api`), nhưng **chưa kiểm**. Phiên
   sau xem lại rồi ghim vào `.gitleaksignore` hoặc xoay khoá. Lệnh:
   `gh run view <id> -R AdventureAsia365-Ecosys/AA-Ecosys --log-failed`.
2. **Infra "DB Freshness Probe" đỏ 4 đêm liền (28/10 → 31/10)**: `place_card_links_missing` có 111 link của tour đã đổi
   hơn 24 giờ. Lần xanh cuối 27/10. Lệnh: `gh run view <id> -R AdventureAsia365-Ecosys/AA-CIS-Infra --log-failed`.
3. `docs/architecture/db-schema-reference.md` ghi CRM **crm-027**, live đã là **crm-031**. File cũ (Verified 30/10
   15:16 UTC).
4. Host `crm.lumiguides.it.com/healthz` trả **000** (không kết nối được). CRM thật chạy qua `portal.lumiguides.it.com`.

## AWS / ECS (acc2)

- STS: account acc2, role assumed. Lệnh: `aws sts get-caller-identity --profile aa365-admin`
- Task def + rollout: `aws ecs describe-services --cluster aa-cis-dev-cluster --services <svc> --query 'services[0].[taskDefinition,runningCount,desiredCount,deployments[0].rolloutState]'`
- Image: `aws ecs describe-task-definition --task-definition <fam:rev> --query ...image`
- Rev mới nhất: `aws ecs list-task-definitions --family-prefix <fam> --sort DESC --max-items 1`

| Service | Task def đang chạy | Rev mới nhất | Image tag | Rollout | running/desired |
|---|---|---|---|---|---|
| aa-cis-dev-api | :940 | :940 | dev-1b6e9448f0c8… | COMPLETED (1 deployment) | 1/1 |
| aa-cis-dev-worker | :506 | :506 | dev-1b6e9448f0c8… (cùng SHA với api) | COMPLETED | 1/1 |
| aa-booking-dev-api | :90 | :90 | 636df62c8286… | COMPLETED | 1/1 |
| aa-crm-dev-api | :94 | :94 | bc5f9280dd0b… | COMPLETED | 1/1 |
| aa-crm-dev-web | :66 | :66 | ba225e4bf909… | COMPLETED | 1/1 |

## Endpoint (lệnh: `curl -s <url>`)

| Endpoint | HTTP | git_sha / version | Migration |
|---|---|---|---|
| api-cis …/health | 200 | 1b6e9448, v0.18.0 | — |
| api-cis …/health/ready | 200 | 1b6e9448 | schema_version **317** (required 315), db ok |
| api-booking …/booking/health | 200 | 636df62c, v0.14.0 | — |
| api-booking …/booking/health/ready | 200 | — | **bk-035**, storage configured |
| portal …/crm/health | 200 | bc5f9280, v0.11.0 | — |
| portal …/crm/health/ready | 200 | — | **crm-031**, membership_feed ok, keys kms |
| portal …/healthz (CRM web) | 200 | ba225e4b, v0.11.0, env dev | — |
| crm.lumiguides.it.com/healthz | **000** | — | — |
| tripplanner.lumiguides.it.com/api/health | 200 | 02dd9f1c, v0.14.0 | — |
| aa-tripplanner.vercel.app/api/health | 200 | 02dd9f1c | — |

- Lambda TripPlanner. Lệnh: `aws lambda get-function --function-name <f> --query Configuration.CodeSha256`
  - `aa-tripplanner-dev-browse`: `yu3v9xeV…` (8 ký tự đầu) (sửa lúc 30/10 12:27Z, Active)
  - `aa-tripplanner-dev-assembly`: cùng CodeSha256 (sửa lúc 30/10 12:28Z, Active)

## Migration mới nhất mỗi owner

CIS **317**, Booking **bk-035**, CRM **crm-031** (cả ba từ ready endpoint). TripPlanner **tp-022** chỉ lấy từ dòng
Verified của `db-schema-reference.md` (30/10); không có ready endpoint, live **chưa kiểm**.

## Bảng job

- `shared.job`: 1 queued, 0 running; rerun wave mở: 0. Nguồn: ECS exec của điều phối 31/10 ~11:00Z. Probe Infra lúc
  10:55Z cũng thấy `kind=place_relocate status=queued n=1` (chuỗi AA-997 `dc260ef8`, cố ý), khớp.
- `booking.job`: **chưa kiểm**.
- `crm.job`: **chưa kiểm**.

## Repo

Lệnh: `gh api repos/…/commits/<br>`, `gh pr list --state open`, `gh run list --branch <br>`.

| Repo (nhánh) | Head | PR mở | CI gần nhất trên nhánh mặc định |
|---|---|---|---|
| AA-Ecosys (master) | b7779bfb `docs: AI and data provider gateway v2 (root ADR 0009, design approved S261) (#397)` | #374 regenerate infra docs; #328 migration rules expand auto-apply (AA-993 M5) | Docs sync success; **Secret Scan (full history) failure** |
| AA-CIS-App (main) | 1b6e9448 `fix: strict accept rule aa997.4 … (#1193)` | #1179 release 0.19.0 | CI, Secret Scan, Kit Sync success |
| AA-Booking (main) | 636df62c `feat: mark CIS places hidden from customers … (#160)` | #161 release 0.15.0 | Secret Scan, Vercel Deploy success |
| AA-TripPlanner-Web (main) | 02dd9f1c `fix: planner map flies to a country … (#197)` | #196 release 0.14.1 | CI, CodeQL, Vercel Deploy success |
| AA-Partner (main) | bc5f9280 `fix: never hand mail for a .invalid address to a provider (#150)` | #133 release 0.12.0 | CI success, Deploy Dev success (10:52Z) |
| AA-CIS-Infra (main) | 3ccdc1f8 `chore: AA-1002 Dev road script in apply mode (#550)` | không có | **DB Freshness Probe failure**; Tour Liveness, CRM Key Policy Diff, Docs Gen success |

Commit xoá nhiều trong 8 commit gần nhất mỗi repo (removed > 5 hoặc deletions > 500):

- AA-CIS-App `0928e759` (#1188, 30/10): xoá 8 file, −1828 dòng. Có chủ đích: bỏ `/v1/rules`, lessons loop,
  post-processor và test liên quan.
- AA-Booking `048c4981` (#158, −589) và `45de0368` (#156, −562): refactor kit, không xoá file nào.

## Vercel production

Lệnh: Vercel MCP `list_deployments target=production`.

- aa-cis-frontend: 041ba9a2 (#1191), READY. Head main 1b6e9448 không đổi file `frontend/`, nên không có bản build mới
  là bình thường (lệnh `gh api …/compare/041ba9a2...1b6e9448`, frontend_files = 0).
- aa-tripplanner: 02dd9f1c (#197), READY, khớp head.
- aa-booking-admin: 636df62c (#160), READY, khớp head.
- Portal Vercel (`aa-cis-portal`): **chưa kiểm** (MCP trả 404 với tên project này).

## Những gì cố ý để BẬT cho phiên sau

- **AA-1002 Dev road** (anthropic-direct tắt, 2 stage scoped `vendor_direct`, budget 150 USD/tháng): Infra #549 + #550
  (apply mode, merge 07:22Z). Trạng thái route/budget trong DB **chưa kiểm** (cần ECS exec).
- **CRM `LIFECYCLE_DRY_RUN=true`**: có trên task def :93 và :94; :94 đang chạy. Lệnh:
  `aws ecs describe-task-definition --task-definition aa-crm-dev-api:94 --query "…environment[?name=='LIFECYCLE_DRY_RUN']"`
- **Chuỗi AA-997 `dc260ef8`** (place_relocate, queued, chạy lại ~00:12Z 01/11 trên credit Geoapify ngày mới): không huỷ.
- **Worktree video** `.tmp-session/wt/s261-video-a`: còn, head `ff65c0b docs: fast-run page names the video plan by
  path until it lands`, cây sạch (0 file đổi), giữ cho Session B của AA-1014.
- **Nháp Jira**: chưa viết, chưa đăng; chuyển sang phiên tiếp theo cùng ngày (S262), xem `jira-drafts.md`.
