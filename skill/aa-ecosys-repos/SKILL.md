---
name: aa-ecosys-repos
description: Bản đồ repo và kiến trúc AA_Ecosys (org AdventureAsia365-Ecosys) — repo nào làm gì, đường pipeline Admin A0–A4 và Tenant T0–T11, file/router/page nằm ở đâu, Terraform, TripPlanner, AA-Booking, deploy và auth. Dùng khi cần tìm code, giao task cho Claude Code/Kiro, hoặc gặp AA-CIS-App, AA-CIS-Infra, AA-TripPlanner-Web, AA-Booking, A0–A4, T0–T11, atom, segment, slate, admin, portal, Vercel, Lambda.
---

# aa-ecosys-repos

Skill này giữ **cấu trúc ổn định**. Danh sách router/page chi tiết sinh từ repo (`references/`); khi nghi ngờ, chạy lại lệnh sinh thay vì tin bảng.

## Repo

Workspace local: `~/projects/AA-Ecosys/` — mỗi repo một `.git` riêng. Bản đồ chung: `~/projects/AA-Ecosys/docs/ecosystem-architecture.md`.

| Repo | Vai trò | Chạy ở đâu | Chi tiết |
|---|---|---|---|
| `AA-CIS-App` | FastAPI backend + Next.js admin + tenant portal + worker | ECS api + worker (acc2), Vercel | `references/cis-app.md` |
| `AA-CIS-Infra` | Terraform `accounts/aa365` (ECS, RDS, S3, IAM, TripPlanner BE) | GitHub Actions (apply chỉ qua workflow_dispatch) | `references/infra.md` |
| `AA-TripPlanner-Web` | B2C map-first planner: Next.js + 2 Lambda | Vercel + Lambda | `references/tripplanner.md` |
| `AA-Booking` | AAA: trip case, booking, ops (đang bootstrap) | ECS service trên acc2 | `references/booking.md` |

`AA-ACP-App` / `AA-ACP-Core` đã archive và xoá. Không tìm code ở đó. Mọi task UI ghi rõ repo đích.

AA-Booking repo CHƯA tồn tại (local hay GitHub) — còn đang bootstrap (AA-678). Repo gốc workspace là `AA-Ecosys` (chứa `docs/`, `skill/`, `.kiro/`, và các repo con trong `apps/` + `infra/`).

## Pipeline (tóm tắt)

**Admin / platform-wide** — không đọc brand voice của tenant:
A0 ingest → A1 generic rewrite + DFS → A2 QA (review queue) → A3 Master Content → Atomize → Segment → Research/Search demand → Score → Route/Hub. A4 = giám sát cross-tenant, hậu kiểm, không chặn.

**Tenant** — đọc brand voice:
T0 brand → T1 chọn tour → T2 rewrite → T3 QA (auto-pass sau 2 vòng, có badge) → T4 pool → Slate → Goal → Angle (chọn 1/3) → Write → Gate F1–F10 → Publish.

Nguyên tắc phân tầng: **bước nào đọc brand voice thì per-tenant**; các bước còn lại dùng chung.
Bảng đầy đủ stage → file → bảng DB: `references/pipeline.md`.

## Quy ước chung

- Trunk-based: chỉ `main`; branch `feature|fix|chore/aa-xxx-…`; PR ghi `Refs AA-xxx`.
- CIS: merge vào `main` → tự deploy Dev (api + worker cùng image). Infra: merge không tự apply.
- Thêm module top-level vào AA-CIS-App → `COPY` trong Dockerfile + path filter `deploy-dev.yml`.
- Frontend: Next 16 + React Compiler, UI kit `app/_kit/`, react-query, inline style + brand token. Xem `aa-ui-verify`.
- Auth: admin dùng header `x-admin-secret` (`verify_admin_secret`); tenant dùng JWT (`/auth/tenant-login` → `_create_jwt`/`verify_jwt`). Hardening (JWT thật cho staff role, passwordless) còn ở backlog (AA-656/AA-703).

## Tìm nhanh

```bash
# router backend
git -C ~/projects/AA-Ecosys/apps/AA-CIS-App grep -n "APIRouter(" -- api/routers
# trang frontend
find ~/projects/AA-Ecosys/apps/AA-CIS-App/frontend/app -name page.tsx | sort
# job kinds (mỗi file services/jobs/*_job.py = một kind, decorator @job_kind)
git -C ~/projects/AA-Ecosys/apps/AA-CIS-App grep -n "@job_kind" -- services/jobs
```
