# AA-CIS-App

> Các bảng dưới sinh từ repo. Khi nghi lệch, chạy lại: `grep -rhoE 'APIRouter\(prefix=' api/routers`, `find frontend/app -name page.tsx`, `grep -rE '@job_kind' services/jobs`.

## Thư mục

| Thư mục | Vai trò |
|---|---|
| `api/` | FastAPI app, routers, migrations (`api/migrations/*.sql`) |
| `services/` | Logic pipeline theo stage (content_generation, acp_shared, jobs, …) |
| `shared/` | llm_client (gateway, satellite), jobs (queue, worker, registry), secrets, config |
| `worker/` | `python -m worker` — job runner trên ECS worker |
| `frontend/` | Next.js: `app/admin/*`, `app/(tenant)/portal/*`, `app/_kit/` |
| `docs/` | `CONTEXT.md`, `adr/`, `sessions/` (db-schema-reference ở repo gốc AA-Ecosys) |
| `skill/` | Nguồn gốc các skill (version-controlled ở repo gốc AA-Ecosys) |

## Router prefixes

| Prefix | Nhóm |
|---|---|
| `/v1/tours`, `/v1/marketplace`, `/v1/planning`, `/v1/angle-gate`, `/v1/content-writing` | Tenant pipeline T* |
| `/v1/pipeline`, `/v1/competitors`, `/v1/publish-log`, `/v1/integrations`, `/v1/rules`, `/v1/social` | Tenant hỗ trợ |
| `/v1/trip`, `/v1/progress`, `/content/photos` | Public / live progress / ảnh |
| `/admin`, `/admin/dashboard`, `/admin/overview`, `/admin/seo-intelligence` | Admin tổng quan |
| `/admin/a4`, `/admin/segment-research`, `/admin/decisions`, `/admin/photos`, `/admin/trip-pages` | Admin A4 + ops |
| `/admin/job-runner`, `/admin/budgets` | Jobs + cost guard |
| `/auth` | Login (tenant + admin) |

## Trang admin

`overview` (dashboard tổng), `upload` (A0), `s1-rewrite` (A1), `review` (A2 review queue), `master-content` (A3), `atom-curation` (Social Content), `tenant-activity`, `platform-stats`, `seo-intelligence`, `llm-usage` (External Spend), `tenants` (có panel 360 inline), `jobs`, `decisions` (Jev), `photos`, `settings` (gates, Brand Identity, LLM route, UI kit tab), `dashboard` (cũ).

## Trang portal (tenant)

`dashboard`, `t0-brand`, `t1-rewrite`, `t4-pool` (My Catalog), `t7-planning` (Social Content/Slate), `t8-angle-gate` (T8+T9), `t10-review` (My Content), `t11-publish` (+ `/connection`), `marketplace`, `billing`, `activity`, `api`, `settings`.

## Job kinds (worker)

| Kind | Cap | Vai trò |
|---|---|---|
| `s1_rewrite` | 4 | A1 rewrite một tour |
| `s1_seo_prefetch` | 1 | Mua SEO gom cho một wave trước rewrite |
| `s1_batch_ingest` | 1 | Nạp batch tour thô |
| `revalidate` | 2 | Chạy lại gate/QA |
| `recompute` | 1 | Segment/score/route/hub recompute (debounce) |
| `a3_atomize` | 1 | Tách atom một tour |
| `segment_research` | 1 | DFS research cho segment (có cost guard) |
| `t2_rewrite` | 4 | Tenant rewrite |
| `t9_write` | 4 | Tenant write content piece |
| `photo_sync` | 1 | Sync ảnh Drive → S3 |

## Hành vi cần biết

- Mọi tác vụ nền chạy qua `shared.job` + worker (S1 rewrite, revalidate, recompute, T2, T9, A3 atomize, research, photo sync). Không còn asyncio task in-process rời (AA-723). Worker loop cũng chạy trong api process (env `JOB_WORKER_IN_API`).
- Live streaming S1: sink WritingProgress → redis key `wp:{master}:tour:{job_id}`, endpoint `/admin/progress/s1/{job}`.
- Deploy: pre-deploy guard chặn khi `shared.job` còn queued/running + post-deploy live smoke (CI). Thêm module top-level → `COPY` trong Dockerfile + path filter `deploy-dev.yml` (có test chặn).
