# AA-817: remaining plan to Done (S239, 16/10/2026)

Agent: Claude Code (subagent). The plan comes from reading code only. Nothing was run against AWS or the DB.
Code read: AA-CIS-App main = origin/main `90387fb4` (includes #760 / migration 237).
DB names come from `docs/architecture/db-schema-reference.md`, verified 15/10 15:29Z. That dump predates 237, so
`shared.tenant_integrations` still shows "RLS off" there. The live state of 237 is in
`.tmp-session/s239/aa817_flags_out.json`.

Pools:
- **MAIN**: `request.app.state.pool`. It connects as `aa_cis_admin`, the owner of every table, so RLS exempts it (D2).
- **TENANT**: `acquire_scoped_conn` (`api/core/aa544_tenant_pool.py:97`). It connects as `aa_app_user` with a LOCAL
  `app.tenant_id`, and only when the route's own Redis flag is `"true"`.

## 0. RLS tables (what "every RLS table" means today)

| group | tables | policy | aa_app_user grant |
|---|---|---|---|
| 229 template (TO aa_app_user, NULLIF, WITH CHECK, no FORCE) | `acp_shared.angle_gate_request`, `acp_shared.content_piece`, `acp_shared.publish_log`, `acp_shared.facts` (+ `facts_platform_read`), `gold_aa_internal.tenant_tour_versions` | `tenant_isolation` | S/I/U |
| 237 template | `shared.tenant_integrations` | `tenant_isolation` | S/D |
| Legacy FORCE, `TO public`, NULLIF | `gold_aa_internal.published_tours`, `silver_aa_internal.raw_tours` (+ `catalog_owner_aa_master_read`, 225) | `tenant_isolation` | S |
| Legacy FORCE, `TO public`, **no NULLIF** (`''` raises 22P02) | `silver_aa_internal.generated_content`, `quality_scores`, `seo_context`, `gold_aa_internal.content_exports`, `webhook_deliveries`, `shared.pipeline_runs` | `tenant_isolation` (004/008) | S (pipeline_runs S/I/U) |
| RLS on, no policy | `acp_shared.acp_output_rules` (deny-all for non-owners; read only by admin `/v1/rules`) | none | none |

Tables that have a tenant key, no RLS, and are read by tenant routes. These must get RLS before their routes move:
- `acp_shared.subject`, `acp_contract.tour_atoms` (`owner_scope` text), `acp_contract.route_pick`, `acp_shared.quarter_plan`,
  `acp_shared.year_plan`, `acp_shared.tenant_atom_state`, `acp_deliver.tenant_tour_pages` (tenant_id **text**),
  `acp_shared.audit_log`, `shared.tenant_rewrite_usage`, `shared.job`.
- `acp_shared.angle_gate_option` has no tenant_id. It is isolated only through its parent `angle_gate_request`.

## 1. Inventory: tenant-facing route groups and their pool

The BFF is a single generic proxy, `frontend/app/api/tenant/[...path]/route.ts`. It sends the tenant JWT as Bearer, or
`X-Admin-Secret` on the staff branch. So every `/v1/*` route below can be reached from the portal, and every staff/admin
branch (for example `is_admin` in `/v1/tours/{id}/full`) must stay on MAIN.

### 1A. Routes already on the tenant-pool code path

| # | route | code | RLS tables | flag | live |
|---|---|---|---|---|---|
| 1 | GET `/v1/content-writing/requests/{id}/latest-piece` | `v1_content_writing.py:220-232` → `services/acp_content_writing/service.py:2050`, `:2075` (`fail_closed=True`) | content_piece, angle_gate_request (+ angle_gate_option) | `aa817:content_piece_reads_pool` | **ON** since 16/10 morning. Live proof not yet collected |
| 2 | DELETE `/v1/integrations/{wordpress,facebook}` | `v1_integrations.py:540,545` → `_disconnect` `:501`, `:506`, `:523` (not fail_closed, `used_tenant_pool` thrown away as `_`) | tenant_integrations | `aa544:integration_disconnect_pool` | **ON**. Live proof not yet collected, and the Dev table has 0 rows |
| 3 | GET `/v1/content-writing/pieces/{id}` and `/pieces/{id}/export` | `v1_content_writing.py:128-133`, `:160-175` → `service.py:2103`, `:2113` | content_piece | `aa544:stage5:get_piece_pool` | OFF (canary flipped on and off on 10/09, AA-544-stage5 notes) |
| 4 | GET `/v1/publish-log/pending` | `v1_publish.py:286`, `:322` | content_piece, angle_gate_request, publish_log | `aa544:stage1:publish_pending_pool` | OFF |
| 5 | GET `/v1/publish-log` | `v1_publish.py:89`, `:97` (query `:102-104`) | publish_log, content_piece, angle_gate_request | `aa544:publish_log_list_pool` | OFF (AA-815 default) |

Before writing any evidence, check the live state of flags 3–5 with `GET` (they are not in today's ON list). No test
references `STAGE1_*`, `STAGE5_*`, `PUBLISH_LOG_LIST_FLAG` or `INTEGRATION_DISCONNECT_FLAG` (grep of `tests/`).

### 1B. MAIN pool. Only RLS tables that are already granted. No migration needed

| # | route | code | tables | blocker |
|---|---|---|---|---|
| 6 | PATCH `/v1/content-writing/pieces/{id}` | `v1_content_writing.py:142-155` → `service.py:2139-2158` | content_piece UPDATE | `write_audit_log` runs on the **same conn** (`service.py:2153`), and `acp_shared.audit_log` has no aa_app_user grant |
| 7 | DELETE `/v1/publish-log/{publish_id}` | `v1_publish.py:160-245` (`:176` publish_log, `:193` tenant_integrations, `:222` UPDATE publish_log, audit via pool `:233`) | publish_log, tenant_integrations | none (SELECT on ti, UPDATE on publish_log). The external Graph/WP call sits between blocks. The AA-815 lane owns unpublish |
| 8 | POST `/v1/angle-gate/requests/{id}/choose` | `v1_angle_gate.py:87` → `acp_angle_gate/service.py:366` (`:386-399`) | angle_gate_request, **angle_gate_option** (no RLS) | needs a parent-scoped policy on angle_gate_option |
| 9 | POST `/v1/angle-gate/requests/{id}/reopen` | `v1_angle_gate.py:104` → `service.py:340` (`:359`) | angle_gate_request | none |

### 1C. MAIN pool. Needs grants or RLS on tables without RLS first

| # | route | code | missing |
|---|---|---|---|
| 10 | GET `/v1/angle-gate/requests/{id}` | `v1_angle_gate.py:77` → `service.py:405` (`:412` option, `:423-426` subject/atom_segment/route, `:432` shared.job) | subject (tenant_id, no RLS, no grant). atom_segment and route are platform tables with no grant. shared.job is SELECT with no RLS |
| 11 | GET `/v1/content-writing/requests/{id}/review` | `v1_content_writing.py:248` → `service.py:2215` (`fetch_request`, `:2179`, `_fetch_atom_context` `:2197` tour_atoms, `fetch_tenant_trips` `:2260`) | #10 + tour_atoms + master read (§3) + tenant_tour_pages |
| 12 | GET `/v1/content-writing/reviews` | `v1_content_writing.py:236` → `service.py:2348` (`_TENANT_REVIEWS_QUERY` `:2307` joins tour_atoms, trips `:2359`) | tour_atoms + master read + tenant_tour_pages |
| 13 | GET/POST `/v1/integrations/{wordpress,facebook}`, POST `.../test` | `v1_integrations.py:126,145,208,329,346,400` (upsert `:175-178`) | INSERT/UPDATE on tenant_integrations (237's FOR ALL policy already holds the WITH CHECK), audit_log |
| 14 | POST `/v1/publish-log/{piece_id}/publish` | `v1_publish.py:399-560` (`:428-439`, ti `:479`, `claim/finish` `services/acp_publish/*` → publish_log, shared.tenants) | external side effects + idempotency; audit_log. Coordinate with AA-815/AA-819 |

### 1D. MAIN pool. Enqueue a job in the same transaction, so these stay on MAIN (document as exceptions)

| # | route | code |
|---|---|---|
| 15 | POST `/v1/angle-gate/requests/{id}/goal` | `v1_angle_gate.py:56` → `service.py:283` (`:304-318` UPDATE + enqueue, one tx) |
| 16 | POST `/v1/content-writing/requests/{id}/write` | `v1_content_writing.py:51-111` (enqueue `:89`, UPDATE content_piece.job_id `:95-97`) |
| 17 | POST `/v1/tours/pool/{id}/rewrite` | `v1_tours.py:389-492` (one tx at `:407`: master read, ttv INSERT `:449`, quota upsert `shared.tenant_rewrite_usage`, audit `:467`; enqueue `:483`; UPDATE job_id `:491`) |
| 18 | POST `/v1/slate/refresh` | `v1_planning.py:97-101` |

### 1E. MAIN pool. Blocked on the master-read path (§3): published_tours/raw_tours/seo_context hold AA master rows only

| # | route | code | other needs |
|---|---|---|---|
| 19 | GET `/v1/tours/pool` | `v1_tours.py:51-160` (master filter `:91-95`, ttv EXISTS `:135-139`) | none |
| 20 | GET `/v1/tours/my-versions` | `v1_tours.py:506-560` (`:537-555`) | none |
| 21 | POST `/v1/tours/versions/{id}/retry` | `v1_tours.py:569-605` | re-enqueue → stays MAIN |
| 22 | GET `/v1/tours/{tour_id}/full` (tenant branch only) | `v1_tours.py:610-700` (`:646` pt⋈ttv, `:656` raw_tours, `:678` seo_context) | the admin branch `:634` stays MAIN |
| 23 | GET `/v1/tours/{tour_id}` | `v1_tours.py:720-748` | none |
| 24 | GET `/v1/tours/versions/{id}` | `v1_tours.py:750-800` | none |
| 25 | GET `/v1/tours/versions/{id}/export-docx` | `v1_tours.py:801-955` | none |
| 26 | PATCH `/v1/tours/versions/{id}` | `v1_tours.py:957-1018` (ttv SELECT/INSERT/UPDATE, granted by 229) | none |
| 27 | GET `/v1/billing` | `v1_tours.py:276-300` | `shared.v_tenant_monthly_usage` has no aa_app_user grant (owner-rights view) |
| 28 | GET `/v1/marketplace` | `v1_marketplace.py:97-111` (`_MARKETPLACE_QUERY` `:69`) | tour_atoms |
| 29 | GET `/v1/routes`, `/v1/hubs`, GET/POST `/v1/route-picks` | `v1_route_hub.py:74,124,166,185` (`_tenant_tour_ids` `:40`) | route_pick (tenant_id, no RLS), route/atom_segment grants |
| 30 | GET `/v1/slate`, POST `/v1/subjects/{id}/pick`, `/cut` | `v1_planning.py:71,105,122` → `services/acp_shared/slate.py:167` (`_tenant_tour_ids`), subject, pick INSERT agr `:806` | subject RLS |
| 31 | GET `/v1/planning/trip-reallocation/suggest`, POST `/confirm` | `v1_planning.py:152,168` → `services/acp_planning/tenant_pool.py:142` + quarter_plan | quarter_plan/year_plan RLS, tenant_tour_pages |

### 1F. Not RLS-relevant or out of scope
- GET `/v1/quota` (`v1_tours.py:238`; tenant_rewrite_usage + tenants), GET `/v1/progress/*` (Redis only, `v1_progress.py:20`),
  POST `/v1/content-writing/cta-check` and GET `/v1/angle-gate/goals` (no DB).
- PATCH `/v1/tours/{tour_id}/approve` (`v1_tours.py:1020-1045`): a tenant-JWT route that UPDATEs **published_tours**
  `WHERE tenant_id = caller`. For any real tenant it touches 0 rows, because the table holds master rows only. Retire it,
  or check that no tenant login carries the master tenant id. Never move it.
- Admin only: `/v1/pipeline/*` (router dependency `_require_admin`), `/v1/rules` (acp_output_rules), `/v1/social`
  (empty `acp_silver_s4`). Public: `/v1/trip/{id}` (no tenant context). Never move these.

**Already on the tenant pool and live: 2 route groups (#1, #2). Code-ready but OFF: 3 (#3–#5). Everything else is on MAIN.**

## 2. Moves, ordered by risk

All new flags follow the `fail_closed=True` pattern: flag ON plus a missing pool, tenant id or GUC returns 503 and never
falls back to MAIN. Each move adds a named constant in `aa544_tenant_pool.py` and logs `used_tenant_pool`.
Size: S ≤ 2 h, M 2–4 h, L > 4 h.

| order | group | flag (new unless noted) | grants / migration | size |
|---|---|---|---|---|
| W0 | #1, #2: live proof of the 2 ON flags. Code: `_disconnect` → `fail_closed=True` + log `used_tenant_pool`; fix the stale "Do NOT turn on yet" comment (`aa544_tenant_pool.py:47-50`) and the docstring list of live routes (`:8-12`) | existing | none | S |
| W1 | #3, #4, #5 (read-only, granted). Move each to `fail_closed=True` (one line each), then flip | existing `aa544:stage5:get_piece_pool`, `aa544:stage1:publish_pending_pool`, `aa544:publish_log_list_pool` | none | S |
| W2 | #6 PATCH piece: move `write_audit_log` out to MAIN after the tenant UPDATE, best effort like `_disconnect`. It is not transactional today anyway (no `conn.transaction()`) | `aa817:content_piece_edit_pool` | none. Do **not** grant INSERT on audit_log: without RLS, a tenant role could write rows for any tenant | S |
| W3 | #9 reopen, #8 choose | `aa817:angle_gate_writes_pool` | migration: RLS on `angle_gate_option`, `FOR ALL TO aa_app_user USING (EXISTS (SELECT 1 FROM acp_shared.angle_gate_request r WHERE r.request_id = angle_gate_option.request_id))` (the parent's RLS filters the subquery). Owner stays exempt | M |
| W4 | #7 unpublish | `aa817:unpublish_pool` | none | S–M (AA-815 lane) |
| W5 | **migration 238: master read (§3)**, then #19, #20, #22 (tenant branch), #23, #24, #25 | `aa817:t2_version_reads_pool` | 238 | M (migration) + M (code) |
| W6 | #26 PATCH version | `aa817:t2_version_edit_pool` | none after 238 (229 granted S/I/U) | S–M |
| W7 | #10, #11, #12, #28: tour_atoms, subject, segment/route reads | `aa817:angle_gate_reads_pool`, `aa817:content_review_reads_pool`, `aa817:marketplace_pool` | migration: RLS on `tour_atoms` (owner-exempt) with `FOR SELECT TO aa_app_user USING (owner_scope = 'platform' OR owner_scope = NULLIF(current_setting('app.tenant_id', true), ''))` **plus** keep-alive policies for `tripplanner` (column grant, 180) and `catalog_owner` (grant). Without them, ENABLE silently gives TP 0 rows. 229 template + grant on `acp_shared.subject`; GRANT SELECT on `acp_contract.atom_segment`, `acp_contract.route`; 229-style text policy + GRANT SELECT on `acp_deliver.tenant_tour_pages` | L |
| W8 | #29, #30, #31: route hub, slate, planning | `aa817:route_hub_pool`, `aa817:slate_pool`, `aa817:planning_pool` | 229 template + grants on `route_pick`, `quarter_plan`, `year_plan` (`tenant_atom_state` if read) | L |
| W9 | #13 connect/test, #14 publish | `aa817:integration_connect_pool`, `aa817:publish_pool` | GRANT INSERT, UPDATE on tenant_integrations. audit stays on MAIN | M–L (AA-815/AA-819) |
| — | #15–#18, #21, admin branches, public trip page | stay MAIN | X1 gives MAIN an explicit `cis_app` policy | — |

Bug found while reading (fix it with W7, or earlier as a tiny PR): `services/acp_planning/tenant_pool.py:70`
`LEFT JOIN acp_deliver.tenant_tour_pages ttp ON ttp.tour_id = rt.tour_id` has no tenant filter, but the PK is
`(tenant_id, tour_id)`. Once two tenants have a page for the same tour, a tenant gets duplicate trips and **another
tenant's page URL** in T7/T8/T9. The table has about 0 rows today. Fix: `AND ttp.tenant_id = $1::text`.

Other leaks that only matter once a route moves:
- Owner-rights views granted to aa_app_user (`acp_contract.v_active_tour_atoms`, `catalog.*`, `shared.v_destination_photos`, …)
  run as their owner, so RLS does not filter them. For tenant data, read the base table or set `security_invoker=true` (PG15).
- `shared.job` SELECT to aa_app_user has no RLS, and `fetch_request` (`service.py:432`) reads job status by payload.

## 3. Master-read path for aa_app_user

**Meaning (design §2, T2 row):** tenant routes join the tenant's own rows to **AA master rows**:
- `published_tours`, `raw_tours` and `seo_context` have `tenant_id = 00000000-0000-0000-0000-000000000001`.
- Platform facts are `scope='platform'`. Platform atoms are `owner_scope='platform'`.

Under aa_app_user with the tenant GUC, `tenant_isolation` hides every master row, so every join returns nothing.
The AA-578 comments "KHÔNG BAO GIỜ chuyển sang RLS pool" sit at `v1_marketplace.py:65-68`, `v1_route_hub.py:44-47`,
`tenant_pool.py:50-55` and `slate.py:171-174`.

**What exists**
- `acp_shared.facts`: `facts_platform_read FOR SELECT TO aa_app_user USING (scope='platform')` (229). Platform rows are
  readable and cannot be written (WITH CHECK `scope='tenant'`).
- `catalog.v_tour*` / `v_destination*` / graph views (225/228): owner `catalog_owner`, read through the
  `catalog_owner_aa_master_read` policy, SELECT to aa_app_user. They lack `published_tours.id` (the key in
  `tenant_tour_versions.published_tour_id`) and the `aa_*` / SEO columns that the T2 routes return.
- Post-229 probe (`probe-after-229.json`): aa_app_user with GUC = master already reads 892 published_tours, 987 raw_tours
  and 918 seo_context rows. With a real tenant GUC it reads 0.

**What is missing**
1. Migration **238**, the next free number (CIS main ends at 237; re-check at write time). It mirrors 225: one policy per master table,
   `aa_app_user_aa_master_read FOR SELECT TO aa_app_user USING (tenant_id = '00000000-0000-0000-0000-000000000001'::uuid)` on
   `gold_aa_internal.published_tours`, `silver_aa_internal.raw_tours` and `silver_aa_internal.seo_context`. Do not filter
   on `master_status` (a tenant's version of a tour that was later deactivated must still render; the queries filter
   themselves). Leave generated_content and quality_scores out: AA-796 made them admin-only on the tenant side.
2. In the same migration, or a sibling, rewrite the 6 no-NULLIF legacy policies to `NULLIF(...,'')::uuid`. Keep them
   `TO public` and FORCE, because TripPlanner and catalog_owner read through them (the 229 decision). This is P3 from the review.
3. Guards (229/237 style, behavioural):
   - runner `foreign == total` (exempt);
   - aa_app_user under a foreign GUC sees exactly the master rows on the 3 tables and 0 tenant rows (seed one fake
     non-master row in the tx);
   - `''` is 0 rows, not an error, on all 8 legacy tables;
   - tripplanner and catalog_owner counts are unchanged before and after;
   - the policy set per table equals the expected set.
4. Platform atoms (`tour_atoms` `owner_scope='platform'`): W7 above. This is a separate migration because tour_atoms is
   230 MB, worker-hot and read by tripplanner/catalog_owner.

Option (b), reading through `catalog.v_tour*`, is rejected for T2: the views would need a new major version adding
`published_tour_id` plus the aa_/seo_ columns (views are append-only, ADR 0008 §5), and they apply the 225 master filter
with catalog_owner rights. That is larger than option (a) for no isolation gain.

## 4. X1: CIS runtime role split

**Source.** `aa817_design.md` has **no** X1 section (§5 says only "Neither 229 nor this slice changes the runtime role").
The steps below come from:
- ADR 0008 §6 (`docs/adr/0008-new-app-integration-and-data-platform-rules.md:140-151`);
- review roadmap row X1 (`docs/audits/2026-10-14-S237-lane-backlog/data-architecture/README.md:333`);
- the Infra wiring as read: `modules/ecs/main.tf:317` (api) and `:515` (worker) `DATABASE_URL ← var.secret_rds_arn`,
  `accounts/aa365/main.tf:177`, DB Migrate reusing the api task def (`.github/workflows/db-migrate.yml:130-144`),
  and deploy-dev copying secrets from the latest revision (`deploy-dev.yml:137-155`).

**Order (ADR 0008 §6):** booking/TP owners plus the separate migrator first (AA-807 / AA-826), then the CIS runtime
(AA-817), then FORCE on CIS tenant tables (a later decision).

| step | what | repo | needs Nghiệp |
|---|---|---|---|
| X1.0 prerequisites | `bk_owner` / `tp_owner` own `booking.*` / `tripplanner.*` (otherwise anything that reassigns from aa_cis_admin also moves them). `db_migrator` exists with its own ECS task def, is a member of `catalog_owner` (225/228 `SET ROLE catalog_owner`), and has ADMIN on `aa_app_user` (229/237 transaction-scoped GRANT). DB Migrate takes an `environment` input. Role bootstrap lives in git. | Infra (AA-807 / AA-826) | approve the issue and order |
| X1.1 roles | `CREATE ROLE cis_owner NOLOGIN`; `CREATE ROLE cis_app LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB CONNECTION LIMIT <api max + worker max + margin>` (pool sizes `api/main.py:78`, `shared/jobs/worker.py:323`). **Not** in `rds_superuser`, so no `pg_read_all_data` / `pg_write_all_data`. | Infra role bootstrap | **create the passwords and secrets**: new `aa-cis/dev/rds-cis-app` (and `aa-cis/dev/rds-migrator`), DSN strings, entered by hand, never printed |
| X1.2 role-scoped policies + grants (migration N) | On every RLS table (§0, 15 tables, plus any added by W3/W7/W8): `cis_app_platform_all FOR ALL TO cis_app USING (true) WITH CHECK (true)`. A non-owner is filtered even without FORCE, and silently, with 0 rows. GRANT USAGE on all CIS schemas (`acp_*`, `catalog`, `geo`, `gold_aa_internal`, `shared`, `silver_aa_internal`), ALL on tables, USAGE/SELECT on sequences, EXECUTE on functions, TEMP on the database. Guard: as cis_app under a foreign GUC, `count == total` on each RLS table; a privilege check per table. | CIS migration + Infra byte copy | approve the Infra PR / DB Migrate apply |
| X1.3 switch runtime | Terraform: split `secret_rds_arn` into an app secret (api :317, worker :515 → `aa-cis/dev/rds-cis-app`) and a migrator secret (migrator task def). Lambdas `services/acp_produce/sweeper_lambda.py:37`, `services/acp_canary/lambda_handler.py:36` (`RDS_SECRET_ID` default `aa-cis/dev/rds`) point to the app secret. `terraform apply` registers new revisions, then deploy-dev keeps them. | Infra + CIS | ⚠️ This contains underscore env vars — edit manually in VSCode (`DATABASE_URL`, `RDS_SECRET_ID`, `SECRET_DB_ARN`, `secret_rds_arn`). Local MFA `terraform apply` |
| X1.4 smoke (Dev, no waiting) | one T2 rewrite, one T9 write, slate refresh, admin Content Quality list, `/admin/overview`, DB Migrate `check`. CloudWatch: no `42501` / `InsufficientPrivilege`. Rerun the probe with a `cis_app` matrix (foreign == total). | — | none |
| X1.5 ownership | Per-object `ALTER … OWNER TO cis_owner` for CIS schemas, tables, views, sequences and functions (not `REASSIGN OWNED BY aa_cis_admin`: that is the RDS master and may still own other objects). `ALTER DEFAULT PRIVILEGES FOR ROLE cis_owner … TO cis_app`. DB Migrate `SET ROLE cis_owner` for `db/migrations/cis/`. 229/237-style guards assert "runner owns" and must change to "cis_owner owns, runner is a member". | CIS migration + Infra runner | approve; RDS snapshot first |
| X1.6 break-glass | `aa_cis_admin` used only for humans / ECS exec scripts. Rotate its password. Update CLAUDE.md, the `aa-cis-schema` skill and the ECS-exec pattern docs. | root docs | rotate password |
| X1.7 later | FORCE on CIS tenant tables (ADR 0008 §6: "CIS FORCE only after the split"); tighten `cis_app_platform_all` to the tables the worker and admin really need. | — | decision |

Record the decision in a root ADR (`0008a-cis-runtime-role-split.md`). Reversing it touches CIS + Infra, so it belongs in
the root repo per `skill/ai-nghiep/references/adr.md`.

**Risk.**
- Silent 0 rows: a missed `cis_app` policy on an RLS table empties worker/admin reads without any error. The behavioural
  guard in X1.2 is mandatory.
- `42501` on a missed grant (sequence, function, temp table). Smoke every job kind (`/admin/job-runner/summary`).
- Owner-rights views change owner in X1.5. They stay owner-exempt as long as `cis_owner` owns the base tables.
- Migrations that `SET ROLE catalog_owner` or GRANT aa_app_user break if the migrator lacks those memberships (X1.0).
- The connection limit on `cis_app` can starve api+worker if it is set below the pool max.

**Rollback.**
- X1.3: `aws ecs update-service … --task-definition <previous revision>` for api and worker (and revert the Lambda env).
  It is instant, and aa_cis_admin still owns everything until X1.5.
- X1.2: `DROP POLICY cis_app_platform_all` + REVOKE (harmless while unused).
- X1.5: generated reverse script (`ALTER … OWNER TO aa_cis_admin`) built from a catalog snapshot taken in the same
  migration run, plus the RDS snapshot.

## 5. Done-when evidence

### 5.1 Per-table forged-GUC probe (Dev)
- **Script.** Extend `docs/audits/2026-10-14-S237-lane-backlog/aa817/aa817_probe.py`:
  - add `shared.tenant_integrations` and every table that W3/W7/W8 adds to the matrix targets;
  - add a **seeded rollback mode**: one READ WRITE transaction that always ROLLBACKs. Inside it, insert 1 row per table
    for 2 test tenants, GRANT aa_app_user to the runner for the transaction (the 229/237 guard-3 pattern), then
    `SET LOCAL ROLE aa_app_user`.

  Several Dev tables are empty: tenant_integrations has 0 rows, publish_log `own 0/0`, content_exports and
  webhook_deliveries have 0. On those, foreign = 0 proves nothing.
- **Role.**
  - The real tenant-pool login (secret `aa-cis/dev/rds-app-user`) for the unseeded matrix.
  - `SET LOCAL ROLE aa_app_user` for the seeded matrix.
  - The runner `aa_cis_admin` as the control: its count under a foreign GUC must equal the total.
  - After X1: a `cis_app` row as well.
- **Query shape**, per table and per GUC:

  ```sql
  SELECT set_config('app.tenant_id', $guc, true);
  SELECT count(*), count(DISTINCT tenant_id) FROM <table>;  -- WHERE-less
  ```

  GUC ∈ {unset, `''`, random uuid (foreign), master, own (busiest tenant)}. Also run, in savepoints, a WHERE-less
  `UPDATE … SET tenant_id = tenant_id` and `DELETE` under the foreign GUC, both expecting 0.
- **Expected.**
  - Tenant tables: foreign 0/0, `''` 0/0, own n/1.
  - facts: platform rows only (tenant_id NULL).
  - pt/rt/sc after 238: master rows under any GUC, 0 rows of the seeded fake tenant B under tenant A.
  - The 6 legacy tables: `''` gives 0/0 after 238. Today it raises 22P02.
  - acp_output_rules: permission denied.
- **Run.** S3-mediated ECS exec, output JSON in `docs/audits/<date>-S<nnn>-aa817-done/`. Do not use `/tmp` on the host.
- **API path, per route moved.**
  - Tenant A JWT on its own resource: 200, same shape as with the flag OFF.
  - Tenant B JWT on A's resource id: 404 / `{"piece": null}` / no row.
  - CloudWatch shows `used_tenant_pool=true` and no `aa817_tenant_context_unavailable`.
  - Test tenants: `aa-cis/dev/e2e-tenant/*`. For #2, first connect the E2E WordPress test site
    (`aa-cis/dev/...` E2E secrets), then DELETE: expect 200, row gone, secret tombstoned.

**Proposed reading of the Done-when (Nghiệp to confirm).**
- Tables read by a tenant route: API-path evidence plus a probe row.
- Tables no tenant route reads (`generated_content`, `quality_scores`, `content_exports`, `webhook_deliveries`,
  `pipeline_runs`, `acp_output_rules`): a probe row as the aa_app_user login.

An API request cannot forge `app.tenant_id`, because the GUC comes from the verified JWT. A "forgotten WHERE" is proved
in CI and by the probe.

### 5.2 CI coverage gap (`tests/integration/test_aa817_rls_tenant_isolation.py`)
`TENANT_TABLES` (`:41-47`) covers: angle_gate_request, content_piece, publish_log, facts, tenant_tour_versions,
tenant_integrations (since #760, with the DELETE-only checks at `:228-250`).

**Missing:**
- **published_tours, raw_tours, seo_context, generated_content, quality_scores, content_exports, webhook_deliveries,
  pipeline_runs.**
  - `test_tenant_rls.py` covers raw_tours, published_tours and pipeline_runs only, as the CI-only `app_user` (wider
    grants than Dev), never under `''`.
  - `test_007_rls_isolation.py` is `--ignore`d in CI (`ci.yml:162`).
  - Add a `LEGACY_FORCE_TABLES` parametrized test as aa_app_user, with the 6 no-NULLIF tables as **strict xfail on `''`**
    until 238 lands.
  - After 238, add master-row visibility on pt/rt/sc and 0 rows of a seeded fake tenant B.
- `acp_output_rules`: assert aa_app_user has no privilege.
- Route-level "forgotten WHERE" tests exist only for latest-piece (`test_aa817_tenant_pool_content.py:131`). Add one
  per moved route: disconnect, pending, get_piece, publish_log list, then W2+.
- New RLS tables from W3/W7/W8 join `TENANT_TABLES` in the PR of their migration.

The catalogue-wide "tenant_id table without RLS" guard is X2 → **AA-848**, not here.

## 6. This session vs follow-up

**This session, in order, each a PR-sized chunk:**
1. **PR-1 (S, about 1.5 h, CIS code):**
   - W0 code: `_disconnect` fail_closed, `used_tenant_pool` log, stale comment and docstring;
   - W1: `fail_closed=True` on #3–#5;
   - unit tests per flag (none exist today) and route-level forgotten-WHERE tests for disconnect and pending.

   Then merge, deploy Dev (rollout COMPLETED), and collect the **live proof for #1 and #2**: connect the E2E WP test site,
   tenant A/B curls, CloudWatch. Flip #3–#5 (AA-544 report-then-confirm, so tell Nghiệp the order first) and curl each.
2. **PR-2 (S–M, about 2 h, CIS tests + audit script):**
   - the CI gap in §5.2 (legacy FORCE tables, strict xfail on `''`, acp_output_rules);
   - probe v2 with tenant_integrations and seeded rollback mode.

   Run it on Dev (the first per-table evidence set) and save it in `docs/audits/2026-10-16-S239-…/aa817-done-evidence/`.
3. **PR-3 (M, about 3 h): migration 238 (master read + NULLIF).** File-only CIS PR → Infra byte copy → DB Migrate
   `check`/`apply` with `shared.job` idle (Nghiệp approves the Infra PR) → schema dump → the PR-2 xfails turn into passes in
   the same PR → rerun the probe.
4. **Stretch, PR-4 (M, about 3 h):** W5 T2 version reads behind `aa817:t2_version_reads_pool`, only if 238 is applied
   with time left, plus the `tenant_tour_pages` join fix (`tenant_pool.py:70`) as its own tiny PR.

**Split into follow-up issues** (ask Nghiệp before creating any; check the project quota of 100, since "CIS Core" is at about 97):
- **F1 "Tenant pool wave 2: tenant writes"** (W2, W3 + angle_gate_option RLS, W4, W6). M–L.
- **F2 "Tenant pool wave 3: atoms/subject/planning RLS + reads"** (W7, W8: tour_atoms with TP/catalog_owner keep-alive
  policies, subject, route_pick, quarter_plan/year_plan, tenant_tour_pages; marketplace, reviews, angle-gate GET, route hub,
  slate, planning). L.
- **F3 "Integrations connect/test + publish on the tenant pool"** (W9). Coordinate with AA-815/AA-819. M–L.
- **F4 "X1 CIS runtime role split (cis_owner / cis_app)"** (§4). Depends on AA-807/AA-826 (bk/tp owners + db_migrator).
  Needs Nghiệp for secrets, MFA Terraform and approvals. L.

**Recommendation:** after PR-1 to PR-3, plus PR-4 if it fits, and the §5.1 evidence, close AA-817 on the re-scoped
Done-when in §5.1:
- every RLS table probed as aa_app_user;
- every route on the tenant pool proven on the API path;
- the CI test covering all 14 RLS tables.

Move the remaining route waves and X1 to F1–F4. Otherwise AA-817 stays an L umbrella that cannot leave In Progress.

**Housekeeping (next root/CIS PR, no issue needed):**
- delete the stale branches `chore/aa-817-role-matrix`, `feat/aa-817-mig-229`, `feat/aa-817-mig-229-rls`,
  `feat/aa-817-tenant-pool-content`, `feat/aa-817-tenant-pool-reads`, `feat/aa817-mig237-tenant-integrations-rls`
  (local and origin, all merged);
- the DM-8.4 doc line from the 237 README;
- regenerate `db-schema-reference.md` (the nightly dump should pick up 237).
