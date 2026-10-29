---
name: aa-ecosys-repos
description: Bản đồ repo và kiến trúc AA_Ecosys (org AdventureAsia365-Ecosys) — repo nào sở hữu gì (AA-CIS-App, AA-Booking, AA-TripPlanner-Web, AA-Partner, AA-CIS-Infra, repo gốc), service ECS và bảng job của từng app, pipeline Admin A0–A4 / Tenant T0–T11, router/page/job kind nằm ở file nào, auth staff/tenant/M2M, Terraform roots. Dùng khi cần tìm code, chọn repo đích hoặc viết brief giao task cho Claude Code/Kiro/subagent, cần biết code admin / portal tenant / CRM nằm ở repo nào, hoặc gặp các từ A0–A4, T0–T11, atom, segment, slate, Content studio. Không dùng cho quy trình merge/deploy (aa-ship), kiểm/sửa giao diện (aa-ui-verify) hay tên bảng/cột và migration (aa-cis-schema).
---

# aa-ecosys-repos

Skill này giữ **cấu trúc ổn định**. Danh sách router/page/job kind trong `references/` là ảnh chụp; khi nghi lệch,
chạy lại lệnh sinh ở mục "Tìm nhanh" thay vì tin bảng. Chi tiết từng repo: `CONTEXT.md` của repo đó (đọc trước khi
thiết kế hoặc sửa code — luật steering); cả hệ: `docs/ecosystem-architecture.md`.

## Repo

Workspace local: `~/projects/AA-Ecosys/` — mỗi repo một `.git` riêng. Repo gốc `AA-Ecosys` (branch `master`) chứa
`docs/`, `skill/`, `.kiro/`, `tools/`; các repo con nằm trong `apps/` + `infra/`. **Mọi repo đều public** (repo gốc và
Infra từ 22/10/2026, ADR 0014 amendment): không ghi account ID, ARN, SG/VPC ID, báo cáo bảo mật vào repo app.

| Repo | Vai trò | Chạy ở đâu (acc2) | Chi tiết |
|---|---|---|---|
| `AA-CIS-App` | FastAPI API (gồm Content studio API `/v1/*`, `/auth/tenant-login`, `/catalog/v1`, `/tenant/membership/v1`) + job worker + Next.js admin. `portal/` ở đây là bản copy **đóng băng, không deploy** (AA-979) | ECS `aa-cis-dev-api` + `aa-cis-dev-worker` (cùng image); Vercel admin `aa-cis.lumiguides.it.com` | `references/cis-app.md` |
| `AA-Booking` | Booking back office (AAA): khách, trip case, đề xuất, nhà cung cấp, B2B API `/booking/b2b/v1` | ECS `aa-booking-dev-api` (worker `booking.job` chạy trong process API); Vercel `aa-booking-admin` | `references/booking.md` |
| `AA-TripPlanner-Web` | B2C map-first planner: Next.js + 2 Lambda (browse, assembly) | Vercel + Lambda | `references/tripplanner.md` |
| `AA-Partner` | CRM cho đại lý (ADR 0010): `api/` (worker `crm.job` trong process API) + `web/`; **tenant portal / Content studio** `portal/` (chuyển từ CIS kèm lịch sử, AA-979 P2a; logic vẫn ở CIS API) | ECS ARM64 `aa-crm-dev-api` + `aa-crm-dev-web` + `aa-crm-dev-portal` (studio, `deploy-portal-dev.yml`), cùng host `portal.lumiguides.it.com`; `partner-dev.` chỉ còn `/crm` và `/crm/*`, còn lại 301 sang `portal.` (AA-979 dọn dẹp) | `CONTEXT.md` của repo |
| `AA-CIS-Infra` | Terraform (`accounts/aa365` + satellite `accounts/acc3-bedrock`), DB Migrate, DB Schema Dump, bản copy migration | GitHub Actions (apply chỉ qua workflow_dispatch) | `references/infra.md` |

Cùng cluster `aa-cis-dev-cluster`. `AA-ACP-App` / `AA-ACP-Core` đã xoá/archive — không tìm code ở đó. Mọi task UI ghi rõ
repo đích: admin CIS ở `AA-CIS-App/frontend/`, portal tenant ở `AA-Partner/portal/`, CRM web ở `AA-Partner/web/`,
staff Booking ở `AA-Booking/frontend/`.

## Bảng job (mỗi owner một bảng, template ADR 0003a)

| App | Bảng | Worker chạy ở | Tiền tố kind |
|---|---|---|---|
| CIS | `shared.job` | service riêng `aa-cis-dev-worker` | không tiền tố |
| Booking | `booking.job` | trong process API | `bk_` |
| AA-Partner | `crm.job` | trong process API | `crm_` |

Pre-deploy guard của mỗi app chặn deploy khi bảng job của chính nó còn bận; DB Migrate `apply` chờ **mọi** bảng job
rảnh. Số kind và cap đổi theo thời gian — đọc từ code (lệnh dưới) hoặc `/admin/job-runner/summary`, không nhớ số.

## Pipeline (tóm tắt)

**Admin / platform-wide** — không đọc brand voice của tenant:
A0 ingest → A1 generic rewrite + DFS → A2 QA (review queue) → A3 Master Content → Atomize → Segment → Research/Search
demand → Score → Route/Hub. A4 = giám sát cross-tenant, hậu kiểm, không chặn.

**Tenant** — đọc brand voice:
T0 brand → T1 chọn tour → T2 rewrite → T3 QA (auto-pass sau 2 vòng, có badge) → T4 pool → Slate → Goal → Angle
(chọn 1/3) → Write → Gate F1–F10 → Publish.

Nguyên tắc phân tầng: **bước nào đọc brand voice thì per-tenant**; các bước còn lại dùng chung.

**Atomize chỉ ở A3 platform** (Nghiệp chốt S224): mỗi tour atomize **1 lần khi lên Master** (job `a3_atomize` từ
publish) hoặc khi admin chạy lại. **Tenant không bao giờ atomize** — tenant viết lại tour (T2/T3) rồi dùng
atom/Segment/route/hub **của platform**. Thêm/bỏ tour chỉ **recompute** Segment/Score/Route/Hub, không atomize lại.
Tên `run_t5_atomize`, `tenant_pipeline.py`, stage `t5_atomize` là di tích trước AA-526 — kiểm người gọi thật, đừng
suy từ tên. Bảng stage → file → bảng DB: `references/pipeline.md`. Model của từng stage là route của Model Gateway
(`shared.llm_role_config`), không ghi trong skill.

## Quy ước chung

- Trunk-based: chỉ `main` (repo gốc `master`); branch `feat|fix|chore|docs/aa-xxx-…`; PR ghi `Refs AA-xxx`.
  Merge, deploy, verify, Done: skill `aa-ship`.
- CIS, Booking, AA-Partner: merge vào `main` chạm đường backend → tự deploy Dev. Infra: merge **không** tự apply.
- DB: mỗi app một role chủ NOLOGIN + role runtime; key migration theo owner. Sổ đăng ký: Infra `db/owners.yaml`;
  giải thích: `docs/database/schema-ownership.md`; tên bảng/cột: `docs/architecture/db-schema-reference.md`;
  cách viết migration và thứ tự copy → DB Migrate: skill `aa-cis-schema`.

  | App | Schema | Key | Owner | Runtime |
  |---|---|---|---|---|
  | CIS | `silver_aa_internal`, `gold_aa_internal`, `acp_*`, `geo`, `catalog`, phần lớn `shared` | `NNN` | `cis_owner` | `cis_app` (api + worker), `aa_app_user` (tenant pool) |
  | Booking | `booking` | `bk-NNN` | `bk_owner` | `booking` |
  | TripPlanner | `tripplanner` | `tp-NNN` | `tp_owner` | `tripplanner` |
  | AA-Partner | `crm` | `crm-NNN` | `crm_owner` | `crm_app` |

  Role/extension chỉ ở Infra `db/migrations/roles/` (`rl-NNN`). Master `aa_cis_admin` là break-glass.
- Ranh giới dữ liệu: app khác đọc CIS qua view `catalog.*` (Booking, TripPlanner) hoặc HTTP `catalog.http.v1` +
  `tenant.membership.v1` bằng token M2M (AA-Partner — CRM không có grant trên schema CIS). Không app nào ghi schema
  của app khác (ADR 0002: chỉ CIS ghi nội dung).
- Frontend: Next 16 + React Compiler, UI kit `app/_kit/`, react-query, inline style + brand token. Xem `aa-ui-verify`.
- Auth (chi tiết: mục sign-in trong `CONTEXT.md` mỗi repo, ADR 0006/0006a/0006b):
  - Staff: Cognito WORKFORCE (email OTP, managed login `staff-auth.lumiguides.it.com`); CIS xác minh access token ở
    `api/core/staff_identity.py`; `verify_admin_secret` (header `x-admin-secret`) vẫn nhận secret cho gọi
    server-to-server. Booking nhận cùng pool (client `booking-staff`).
  - Tenant: API key → `/auth/tenant-login` → JWT tenant (`_create_jwt` / `verify_jwt` trong `api/routers/auth.py`).
  - M2M: pool `aa-m2m-<env>` client-credentials (`api/core/m2m_auth.py`) cho `/catalog/v1`, `/tenant/membership/v1`,
    Booking `/booking/b2b/v1`.

## Brief giao việc cho subagent / Kiro

- Subagent không push, merge, Terraform apply, DB Migrate, `gh workflow run`, và **không ECS exec** (hook
  `.claude/hooks/subagent-guardrails.sh`). Mọi bước live (query DB qua ECS exec, deploy, verify) là của điều phối:
  brief lane kết thúc bằng mục "post-merge steps cho orchestrator" (runbook/script để điều phối chạy).
- Điều phối push / PR / merge bằng GitHub App `aa-agent` qua `tools/github/as-app.sh` (cách gọi: `aa-ship` §1).
- Worktree luôn ở đường dẫn tuyệt đối `/home/nghiep/projects/AA-Ecosys/.tmp-session/wt/<tên>`.
- Bẫy khi chạy song song (scratch riêng theo lane, cổng Postgres test riêng, giữ chỗ số migration): `aa-lessons`
  mục "Cách làm việc".

## Tìm nhanh

```bash
# router backend CIS
git -C ~/projects/AA-Ecosys/apps/AA-CIS-App grep -hoE 'APIRouter\(prefix="[^"]*"' origin/main -- api/routers | sort -u
# trang admin CIS / trang portal tenant
git -C ~/projects/AA-Ecosys/apps/AA-CIS-App ls-tree -d --name-only origin/main frontend/app/admin/
git -C ~/projects/AA-Ecosys/apps/AA-Partner ls-tree -r --name-only origin/main portal/app | grep page.tsx
# job kinds — CIS: services/jobs/*_job.py, decorator @job_kind
git -C ~/projects/AA-Ecosys/apps/AA-CIS-App grep -n "@job_kind(" origin/main -- services/jobs
# Booking (runner backend/app/jobs) / AA-Partner (runner api/app/jobs): hằng KIND = "bk_…" / "crm_…"
git -C ~/projects/AA-Ecosys/apps/AA-Booking grep -n 'KIND = "bk_' origin/main -- backend/app
```
