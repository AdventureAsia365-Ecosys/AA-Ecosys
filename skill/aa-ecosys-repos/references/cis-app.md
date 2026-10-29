# AA-CIS-App

> Ảnh chụp từ `origin/main`. Khi nghi lệch, sinh lại bằng các lệnh ở mục "Tìm nhanh" của `SKILL.md`. Nguồn sự thật:
> `CONTEXT.md` ở gốc repo.

## Thư mục

| Thư mục | Vai trò |
|---|---|
| `api/` | FastAPI app (`main.py`), `routers/`, `core/` (identity, M2M auth), `services/`, `migrations/*.sql` (key `NNN`) |
| `services/` | Logic theo miền/stage: `content_generation` (A1/A2), `export` (A3), `acp_shared` (atom, segment, slate, grounding), `acp_angle_gate`, `acp_content_writing`, `acp_publish`, `brand_intake`, `places`, `waves`, `writing_memory`, `supply_content`, `catalog_http`, `tenant_membership`, `erasure`, `retention`, `jobs` (mỗi file một kind) … |
| `shared/` | `llm_client` (Model Gateway, satellite Bedrock), `jobs` (queue, worker, registry), `secrets.py`, `cost_guard.py`, `log_config.py`, `ops_alerts.py`, `tour_liveness.py` |
| `worker/` | `python -m worker` — shim gọi `shared.jobs.worker`; chạy trên service `aa-cis-dev-worker` |
| `frontend/` | Next.js admin: `app/admin/*`, `app/login`, `app/trip`, `app/api` (BFF), `app/_kit/`, `app/_brand/` |
| `portal/` | Bản copy **đóng băng, không deploy** của tenant portal (AA-979): nguồn thật ở AA-Partner `portal/`; test `test_portal_copy_is_frozen` chặn mọi thay đổi; xoá ở P2b |
| `docs/` | `adr/`, `api/`, `contracts/`, `runbooks/`, `implementation-notes/` (`CONTEXT.md` ở gốc repo; `db-schema-reference.md` và log phiên ở repo gốc AA-Ecosys) |

## Router prefixes

| Prefix | Nhóm |
|---|---|
| `/v1/tours`, `/v1/marketplace`, `/v1/planning`, `/v1/angle-gate`, `/v1/content-writing` | Tenant pipeline T* (Content studio API) |
| `/v1`, `/v1/pipeline`, `/v1/integrations`, `/v1/rules`, `/v1/social`, `/v1/publish-log`, `/v1/notifications` | Tenant hỗ trợ / tài khoản |
| `/v1/trip`, `/v1/progress`, `/content/photos` | Public / live progress / ảnh |
| `/catalog/v1`, `/tenant/membership/v1` | Hợp đồng HTTP cho AA-Partner (token M2M) |
| `/admin`, `/admin/dashboard`, `/admin/overview`, `/admin/seo-intelligence`, `/admin/content-quality` | Admin tổng quan |
| `/admin/a4`, `/admin/segment-research`, `/admin/decisions`, `/admin/photos`, `/admin/places`, `/admin/trip-pages`, `/admin/writing-memory` | Admin A4 + ops nội dung |
| `/admin/aa-content`, `/admin/supply-content` | Nội dung AA tự viết, nội dung supply cho Booking |
| `/admin/tenants`, `/admin/platform`, `/admin/platform/crm` | Tenant, staff, nền tảng, CRM console |
| `/admin/job-runner`, `/admin/budgets`, `/admin/waves` | Jobs, cost guard, wave chạy lại |
| `/auth` | Login tenant, xác minh token staff/tenant, JWKS |

## Trang admin (`frontend/app/admin/*`)

`overview`, `upload` (A0), `s1-rewrite` (A1), `review` (A2 review queue), `master-content` (A3), `atom-curation`
(Social Content, các tab QA/held của tenant), `content-quality`, `writing-memory`, `places`, `aa-content`,
`tenant-activity`, `platform-stats`, `platform` (staff, agencies, alert recipients…), `seo-intelligence`, `llm-usage`
(External Spend), `tenants`, `jobs`, `decisions` (Jev), `photos`, `data-erasure`, `data-model`, `api-docs`, `settings`
(gates, Brand Identity, LLM route, UI kit).

## Trang portal tenant — ở AA-Partner

UI portal nằm ở AA-Partner `portal/app/portal/*` (ECS `aa-crm-dev-portal` trên `portal.`); API phía sau vẫn là router `/v1/*` +
`/auth` của repo này. Slug (AA-759, slug `t*` trước AA-759 trả 308): `dashboard`, `brand`, `tours` (`mine`, `marketplace`),
`create` (`social`, `article`, `write`), `content` (+ `publish`), `account` (`activity`, `api`, `billing`,
`integrations`, `settings`), `help/facebook`; ngoài gate: `/tenant-login`, `/privacy`, `/terms`.

## Job kinds (worker, `shared.job`)

Nhóm chính (danh sách đầy đủ + cap: lệnh `@job_kind` trong `SKILL.md`; cap đổi theo thời gian):

- Admin pipeline: `s1_batch_ingest`, `s1_seo_prefetch`, `s1_rewrite`, `revalidate`, `a3_atomize`, `recompute`,
  `segment_research`, `tour_graph_build`.
- Tenant pipeline: `t2_rewrite`, `t7_slate`, `t8_angles`, `t9_write`.
- Địa danh / ảnh: `place_extract`, `place_geocode`, `place_shape`, `place_dedupe`, `place_cards_build`, `photo_sync`.
- Writing memory (`writing_*`), `supply_content_draft`, retention / `data_erasure` / purge (`tripplanner_purge`, `supply_media_purge`), email ops (`ops_alert_email`, staff invite), `staff_directory_reconcile`.

## Hành vi cần biết

- Mọi tác vụ nền chạy qua `shared.job` + worker; không còn asyncio task in-process rời (AA-723). API không chạy
  worker loop trừ khi `JOB_WORKER_IN_API` bật rõ (chỉ local/dev).
- Cap theo kind là toàn cục qua mọi worker; tổng cap `s1_rewrite` + `a3_atomize` phải nhỏ hơn slot của worker
  (`JOB_WORKER_MAX_PARALLEL`) — có test chặn.
- A1 writer v2 (AA-645) đi qua `services/content_generation/s1_writer_v2_live.py`, bật bằng env `S1_WRITER_V2` trên
  worker; model là route của stage `s1_generate` trong Model Gateway. Env đặt tay trên task def có thể mất sau một
  Terraform apply chạm task def (xem `infra.md`).
- Live streaming S1: sink WritingProgress → redis, endpoint `/admin/progress/s1/{job}`.
- Deploy: pre-deploy guard `GET /admin/job-runner/deploy-gate` chỉ chặn khi có wave mở hoặc job kind `deploy_blocking`
  (`data_erasure`, `s1_batch_ingest`) đang chạy / queued đến hạn trong 15 phút (C6.3a, AA-993 G5); job khác được
  release và claim lại. Post-deploy verify (CI).
