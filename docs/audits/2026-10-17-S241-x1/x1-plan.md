# X1 execution plan: per-app DB owner/runtime roles, `db_migrator`, per-app security groups (Dev)

- **Session:** S241 (17/10/2026). **Author:** Claude Code (plan only, nothing applied).
- **Mandate:** Nghiệp, S241: "làm luôn khi chưa có khách". Dev holds test data only (checked 17/10, roadmap
  D-01 = A). This plan takes roadmap **D-05 = B** (the whole X1 chain now, in ADR 0008 decision 6 order) and
  **D-06 = A** (per-app security groups on Dev now, ADR 0004b).
- **Implements:** ADR 0008 decision 6 (role split order E2), data standards SEC-1, SEC-2, SEC-11, MIG-6,
  DM-1.2, DM-1.3, DM-8.1, DM-8.2, DM-8.5, DM-8.6, DM-8.9, C2.2/C2.3; S241 SDLC review P0-9 steps 2–4;
  unified roadmap U-33 (X1 chain), U-18 (SGs), U-16 (isolation probe).
- **Linear:** AA-860 (CIS runtime split, Waves 4–5); AA-826 (owners.yaml + role bootstrap, Wave 1). Waves
  1–3 (Booking/TripPlanner owners, migrator task def, SGs) have no open issue since AA-807 closed:
  **ask Nghiệp before creating one** (steering rule).
- **S243 (19/10):** the "S243 amendments" block below corrects §1.4 / S16 (FORCE RLS does not filter the
  master: 244 adds parity policies TO cis_app on all 16 RLS tables) and records Wave 4's build state.
- **Revision 2 (17/10):** two review passes (19 points) checked against the code and folded in; the biggest
  change is that the runner's `SET ROLE` is keyed on the **live schema owner** (XD8), which removes the
  default-privilege gap windows and the separate "flip" steps. What was accepted, adapted or rejected is in §9.
  A third pass (code review of the S2/S3 branches, 8 points C1–C8, 17/10) added XD9 (catalog view freeze until
  S22), the probe's runtime-grant cells and a working rl-001 undo (§9 Pass C).
- **Not in scope:** rotating the RDS master password (D-03, default A = at prod), `manage_master_user_password`
  (D-04, after this plan, U-41), FORCE RLS on CIS tables (SEC-7 follow-up after the split), Redis AUTH/TLS
  (P0-8), X4 TripPlanner decoupling.

Every number below was read on 17/10/2026 from the code at `main`, the schema reference dump of 16/10
(CIS 242, tp-012, bk-013), the AA-817 probe output (`docs/audits/2026-10-14-S237-lane-backlog/aa817/probe-after-229.json`)
and read-only AWS calls (security groups, ENIs, Lambda VPC config, connection metrics).

---

## S243 amendments (19/10/2026)

Wave 4 (AA-860) built in S243. Where this block and a step below (or the S242 block) differ, this block wins.
Implementation notes: AA-CIS-App `docs/implementation-notes/AA-860-S15.md`, `AA-860-S16.md`; AA-CIS-Infra
`docs/implementation-notes/AA-860-S15.md`, `AA-860-S16.md`, `AA-860-S18.md`, `AA-860-S19.md`.

**Status of Wave 4**

| Step | State | Branch |
|---|---|---|
| S15a photo sync on `geo`, docstring, connection inventory | Built | AA-CIS-App `feat/x1-s15-cis-runtime-prep` |
| S15b read-only run-scripts (connection snapshot, photo parity) | Built | AA-CIS-Infra `feat/x1-s15-scripts` |
| S16a CIS `244` + tests | Built | AA-CIS-App `feat/x1-s16-migration-244` |
| S16b-i Infra byte copy of 244 | Built (Copy Guard red until S16a merges) | AA-CIS-Infra `chore/x1-s16-copy-244` |
| S16b-ii probe cell `rls.force_parity.cis_app` | Built | AA-CIS-Infra `feat/x1-probe-force-parity` |
| S17 cis_app DSN + set-password | Nghiệp + main session | — |
| S18a `DATABASE_URL` → cis_app, 53300 alarm | Staged, merge only in the freeze window | AA-CIS-Infra `feat/x1-s18-cis-app-dsn` |
| S19a task-role Deny | Staged, apply last | AA-CIS-Infra `feat/x1-s19-task-role-deny` + root `docs/x1-s19-ecs-exec` |

**§1.4 and S16 item 3 were wrong: FORCE RLS does not filter the master.**
- The AA-817 probe v2 (`docs/audits/2026-10-16-S239-in-progress-audit/aa817-done-evidence/probe_v2_after_239.json`)
  shows, for `aa_cis_admin`, `rls_active = false` and `foreign_guc == total` on every FORCE table
  (published_tours 892/892, raw_tours 987/987, generated_content 1481/1481, quality_scores 1481/1481,
  seo_context 918/918, pipeline_runs 46/46). The master is in `rds_superuser`; lesson S236. About 69 CIS files
  read these tables without setting `app.tenant_id`.
- So 244 gives `cis_app` a permissive `<table>_cis_app_all FOR ALL TO cis_app USING (true) WITH CHECK (true)`
  on **all 16** RLS tables: the 8 ENABLE-only ones (D2) **and** the 8 FORCE ones. This reproduces today's
  runtime behaviour exactly; tenant isolation stays on the tenant pool (`aa_app_user`). Without it, `cis_app`
  would read 0 rows and be refused writes on raw_tours, published_tours, generated_content, … after S18.
- The 244 guard is inverted: not "published_tours without GUC = 0" but **parity**: for every FORCE table and
  tenant_tour_versions, `cis_app`'s `count(*)` without a GUC and under a forged GUC equals the master's.
  The master's counts are taken **before** the policies are created: the master is a member of `cis_app`
  (rl-001) and a policy `TO cis_app` applies to members too, so measured afterwards the master would always
  match. CI test: a filtered master (the old premise) makes the guard refuse.
- Probe: new cell `rls.force_parity.cis_app` (cis_app's own DSN vs the catalog login), owners.yaml
  `cis.rls_parity_tables`.
- **S21 / 245 must handle `cis_owner` the same way** (policies `TO cis_owner` or `NO FORCE` on the 8 FORCE
  tables). DB Migrate runs CIS files as `cis_owner` (not a member of `cis_app`), and the owner-rights views
  `acp_contract.v_active_tour_atoms`, `v_trip_registry`, `shared.v_tour_photos`, `shared.v_destination_photos`
  (read by TripPlanner and `catalog_owner`) read their base tables as their owner: once `cis_owner` owns
  them without the `rds_superuser` bypass they would return 0 rows, and so would old-style data migrations.
  Needs its own design pass before 245.
- **AA-860 Done-when (1)** ("a forged foreign `app.tenant_id` on the main pool returns 0 rows from every RLS
  table") contradicts parity: admin needs cross-tenant reads and the code sets no GUC. Proposed wording
  (Nghiệp decides): "cis_app owns nothing, is in no role and has no BYPASSRLS; CIS runtime → booking /
  tripplanner 42501; tenant isolation proven on the tenant pool (aa_app_user matrix 0 cross-tenant rows); the
  main pool keeps platform parity on RLS tables (policies TO cis_app)". A GUC-aware main pool is a separate
  project (~69 files); a follow-up issue needs Nghiệp's OK first.

**244 on Dev after 247–249 (S243 migration numbers: 248 = AA-884, 249 = AA-878, X1 keeps 244–246).**
244 is applied after them. `GRANT … ON ALL` covers every object that exists then (incl.
`shared.staff_app_grant`, 248's `shared.cost_explorer_app_snapshot`); EXECUTE is revoked again on all trigger
functions (243's key guard, 248's audit triggers, `shared.job_set_updated_at`; owners.yaml already excludes
them); default privileges `FOR ROLE aa_cis_admin` cover later objects. Tested in AA-CIS-App
`test_aa860_migration_244.py` (objects before 244, after 244 as the master, after 244 as a superuser).
A later migration that adds an RLS table in a CIS runtime schema must add a policy `TO cis_app` in the same
file (CI standing check `test_x1_cis_app_privileges.py`); none of 248/249/bk-017/tp-015 does.

**CI replay (S242 amendment changed):** the conftest replay now **skips 244** (like 001/002/007b/008): its
policies make the exact-policy guards of 229/237/239/241, which their tests re-apply, refuse. The X1 tests
apply 244 themselves in the Dev order (after the full replay, CI DB first brought to Dev's RLS shape:
`conftest.x1_244_ci_shape`) and remove it at teardown. Any new migration that asserts an exact policy set on
one of the 16 tables must allow `<table>_cis_app_all`.

**S15:**
- `services/photos/sync.py` `itinerary_places` reads `geo.tour_place` ∪ `geo.tour_stop` of the **current**
  graph build (mapped to the live tour by the `services/places/store.py` liveness SQL), fail-open logged at
  ERROR. No CIS code reads `tripplanner.*` after it. The Infra run-script `x1_photo_itinerary_parity.py`
  compares old vs new per country (S15c).
- Connection budget (XD6): inventory in AA-CIS-App `AA-860-S15.md`. Worst case per api + worker task set ≈ 63
  (api 16, worker 47 with 8 slots of per-job pools and executor-thread ad-hoc connects), ≈ 126 with the 200 %
  deploy overlap; measured instance max 28 (05–18/10). **Proposal: keep 90**; raise (Infra `roles/003`,
  ceiling ≈ 105 = 181 − 30 − 15 − 15 − 5 − reserved) only if the S15c snapshots show more than 45 sessions, or
  better move the grounding / Jev / export per-job pools onto the worker pool. `shared/repository/database.py`
  is dead (nothing imports it).
- The snapshot is 2–3 dispatches of a read-only run-script, not a per-minute series (30-minute run-script
  ceiling).
- D7 (s4_trigger Lambda) is void: no such function on acc2 (list-functions). `services/acp_produce/sweeper_lambda.py`
  (the only code naming the master secret) is not deployed and not imported.

**S17 (Nghiệp, Console; ⚠️ underscore names, edit by hand, never paste the value into chat):**
- Secrets Manager → `aa-cis/dev/rds-cis-app` (the placeholder exists, no value yet) → "Set secret value" →
  Plaintext. Take the **format of the master DSN `aa-cis/dev/rds`** (the value api and worker read as
  `DATABASE_URL` today), keep scheme, host, port, database and any query string exactly, and change only:
  user → `cis_app`, password → a new random password of **≥ 32 printable ASCII characters**. Shape:
  `postgresql://cis_app:<new password>@<same host>:<same port>/aa_cis_dev<same ?query, if any>`.
  Percent-encode `@ : / ? # %` in the password (or generate one without them). The runner refuses a DSN whose
  user is not `cis_app`, a shorter password, or a host/port/database different from the master's.
- Then the main session dispatches DB Migrate `mode=set-password`, `role=cis_app`, `environment=dev`. The
  runner (master login) sends only a SCRAM verifier, test-logs in with the DSN and prints
  `current_user=cis_app rolconnlimit=90`, then `COMMENT ON ROLE cis_app IS 'x1:password-set …'`. Exit 11 =
  secret refused (nothing changed), 12 = password set but test login failed.
- Then the probe: `cis_app_secret_ready`, `cis_app_password_set` true; `login.cis_app`, `cross.cis_app.*`,
  `rls.force_parity.cis_app` pass.

**S18:** the Terraform line is now `accounts/aa365/main.tf:185` (module "ecs" `secret_rds_arn`) →
`aws_secretsmanager_secret.rds_cis_app.arn` (H4: Nghiệp reviews it). Same PR: log metric filter on
`/ecs/aa-cis-dev` for `"too many connections for role" "cis_app"` → `AA/RDS CisAppTooManyConnections`, alarm Sum ≥ 1 / 5 min,
ALARM + OK to the alerts topic (≈ $0.10–0.40/month). Expected plan: 2 task-definition revisions, 1 filter,
1 alarm, no `aws_ecs_service` change. Preconditions: S15 deployed, 244 applied, S17 done, CIS merge freeze.

**S19:** Deny `secretsmanager:GetSecretValue` on `${project}/${environment}/rds-??????`, `db-migrator-??????`,
`booking/*`, `tripplanner/*` in `ecs_task_policy`. Checked against the live secret ARNs: the master,
db-migrator, every booking/ and tripplanner/ secret denied; rds-app-user, rds-cis-app, gdrive-photo-reader,
booking-jwt-signing-key allowed. Skills `aa-cis-schema/references/ecs-exec.md` and `ai-nghiep/references/aws.md`:
ECS-exec scripts use the container `DATABASE_URL`; master work via DB Migrate `run-script` (root branch
`docs/x1-s19-ecs-exec`, merge with the S19 apply). H7 (Nghiệp's `~/.claude/CLAUDE.md`) unchanged.

---

## S242 amendments (18/10/2026)

What shipping S9–S14 changed in this plan. Where this block and a step below differ, this block wins.
Implementation notes: AA-CIS-Infra `docs/implementation-notes/AA-852-s11-sg-expand.md`, `AA-852-s12-migrator-workflows.md`,
`AA-852-s13a.md`, `-s13b.md`, `-s13c.md`, `AA-852-s14.md`.

**Status of Wave 2 end and Wave 3**

| Step | State | Where |
|---|---|---|
| S9 probe files `bk-015`, `tp-014` | Done | Infra #179 (copies) |
| S10 ADR 0004b | Done | root #95 |
| S11 expand: SGs, migrator task def, secret placeholders | Done, applied | Infra #180 |
| S12 workflows on the migrator task def, `set-password` + `run-script` | Done | Infra #182 |
| S13 a/b/c callers on their own SGs (Booking → TP + dfs Lambdas → CIS api + worker) | Done, applied | Infra #187, #188, #189 |
| S14 `sg-app` out of RDS/Redis/EFS ingress, self-443 dropped | Done, applied | Infra #190 |

**S11 (item 3, item 4):**
- The secret placeholders `aa-cis/dev/rds-cis-app` and `aa-cis/dev/db-migrator` follow the `booking_db` pattern
  (secret container, **no** `aws_secretsmanager_secret_version`), not `tripplanner_db`. A version resource would
  make Terraform read the DSN on every refresh and would need a bootstrap change to `tf_plan_secret_arns`. Nghiệp
  writes each value in the Console (H3, H5 unchanged).
- **No S3 grant for the probe.** `db/isolation_probe.py` returns its results as `PROBE …` lines in the task log,
  and the workflow builds probe.json from them. The migrator task role has `s3:PutObject` on the
  `db-schema-dump/*` prefix only.
- H1 (DSN env var name in the migrator task def) was done by hand before the S11 merge. A plan precondition
  blocked the placeholder name.

**S12:**
- **No new environment variable, no hand edit, no IAM change.** H2 is void.
  - The role and script travel in the value of the existing `MIGRATION_MODE` (`set-password:<role>`,
    `run-script:db/scripts/<name>.py`).
  - The workflow inputs fold into the existing job variable `MIGRATION`.
  - The apply role already had register/deregister/run-task and `iam:PassRole` on `aa-*-dev-*`.
- **One temporary task-definition revision per run.** `.github/scripts/migrator-task.sh prepare` copies the
  newest Terraform-shaped revision (`:latest` placeholder image, fixed roles and secret), swaps in the image the
  api service runs and registers it. The run uses it by ARN, and `deregister` runs in an `always()` step.
  Terraform never sees these revisions as drift.
- S12 depended on the S11 apply (family, SG and RDS ingress must exist). That condition was met before the
  merge.
- `READ_ONLY = True` scripts run with `default_transaction_read_only = on`, and their idle check is
  report-only. Plan S15's sampler is such a script, one snapshot per dispatch.

**S14:**
- Done. `aa-cis-dev-sg-app` itself is kept. The two ENIs of the deleted `aa-cis-dev-ingestion` Lambda still
  reference it (owned by the Lambda service). Delete the group in a later cleanup once AWS releases them.
- Rolling back any S13 sub-step now needs S14 reverted and applied first.

**S22:**
- The runner must open a **master connection** read in-task from `aa-cis/dev/rds` for `roles/` files,
  `mode=set-password` **and** `mode=run-script`. Both new modes refuse any login other than `aa_cis_admin`
  (exit 8). The step text above names only `roles/`, set-password and extensions.
- S22's check "set-password … exits 0 (master path)" depends on this. `check-base` already accepts the
  `aa-cis/dev/db-migrator` secret, so the task-def switch needs no script change.

**Before S20:**
- The CIS task role still grants `secretsmanager:GetSecretValue` on `*` (`modules/ecs/main.tf`). Narrow it during
  S18/S19, before the `db_migrator` DSN is written (S11 notes).

**Identity Phase 1 overlap (CIS 247, root ADR 0006a):**
- CIS 247 (`admin_users` identity columns + `shared.staff_app_grant`) was applied before 244–246. 245 (ownership
  to `cis_owner`) and the 246 probe must cover `shared.staff_app_grant` and the new `admin_users` columns.
- After 244 merges, CI applies 247 after 244 as a superuser. So 244's default privileges do not reach
  `staff_app_grant` in CI, while on Dev they do. `test_x1_cis_app_privileges` must model the runner.

---

## 1. Current state

### 1.1 Who connects as what today

| Caller | DB role | Secret (DSN) | How it gets it | Role attributes |
|---|---|---|---|---|
| CIS api main pool (`api/main.py:78`, max 10, `cis-api`) | `aa_cis_admin` | `aa-cis/dev/rds` | task def `aa-cis-dev-api`, `DATABASE_URL` ← `var.secret_rds_arn` (`modules/ecs/main.tf:317`) | RDS master: CREATEROLE, CREATEDB, member of `rds_superuser` → `pg_read_all_data`, `pg_write_all_data`; no BYPASSRLS; no connection limit (C2.3b) |
| CIS worker (`shared/jobs/worker.py:340`, max 10, `cis-worker`) and every ad-hoc `asyncpg.connect(get_database_url())` (catalog, role_config, call_log, jobs_repo, admin_pipeline, export, grounding, jev_gates, photo_sync, …) | `aa_cis_admin` | `aa-cis/dev/rds` | task def `aa-cis-dev-worker`, same `DATABASE_URL` (`modules/ecs/main.tf:519`) | same |
| CIS tenant pool (`api/core/aa544_tenant_pool.py`, max 2, `cis-tenant`) | `aa_app_user` | `aa-cis/dev/rds-app-user` | boto3 at boot | LOGIN, NOINHERIT, limit 15, RLS-filtered |
| DB Migrate (`db-migrate.yml` + `db/run_migration.py`) | `aa_cis_admin` | `aa-cis/dev/rds` | one-off task **from the api task def** (`describe-services aa-cis-dev-api`), `DATABASE_URL` | same as api |
| DB Schema Dump (`db-schema-dump.yml`), aa817 probe, ECS-exec scripts (CLAUDE.md pattern) | `aa_cis_admin` | `aa-cis/dev/rds` | api task def / api container | same |
| Booking API + in-process `booking.job` worker (`backend/app/db.py:62`, max 5, `booking-api`) | `booking` | `booking/dev/database-url` | task def `aa-booking-dev-api` | LOGIN, limit 15; execution role reads `booking/dev/*` only |
| TripPlanner Lambdas browse + assembly (`backend/shared/db.py:63`, max 1 each) | `tripplanner` | `tripplanner/dev/database-url` | boto3 via `TRIPPLANNER_DATABASE_URL_ARN` | LOGIN, limit 30; Lambda role reads its own secrets only |
| `aa-cis-dev-dfs-balance-check` Lambda | none (HTTP only) | — | — | — |
| `catalog_owner` | NOLOGIN | — | — | owns the 14 `catalog.*` views |

Live peaks (CloudWatch, 10–17/10): instance `DatabaseConnections` max 28; `tripplanner` 4, `booking` 3,
`aa_app_user` 3 (`aa_cis_admin` publishes no `AA/RDS RoleConnections`, no limit).

### 1.2 Who owns what today

- **Every schema** (`acp_*`, `booking`, `catalog`, `geo`, `gold_aa_internal`, `shared`, `silver_aa_internal`,
  `tripplanner`) is owned by `aa_cis_admin`; `public` by `pg_database_owner`.
- **Every object** is owned by `aa_cis_admin`, except the 14 `catalog.*` views (`catalog_owner`). That
  includes all 34 `booking.*` objects (customers PII, pricing, supplier rates, 12 trigger functions, 2 views)
  and all 16 `tripplanner.*` objects (incl. view `v_inquiry_outbox`).
- **Functions:** 15, none `SECURITY DEFINER` (12 Booking trigger functions, `geo.name_norm`,
  `shared.create_tenant_schemas` (unused by code), `shared.job_set_updated_at`).
- **Types:** enums only in `acp_shared`, `gold_aa_internal`, `public`, `shared`, `silver_aa_internal`; none in
  `booking` / `tripplanner`.

### 1.3 Grants and default privileges that matter

- `booking` role: USAGE on `booking`; DML on booking tables (from bk-001 grants + default privileges);
  SELECT on `catalog.*` views (225/228); USAGE `tripplanner` + SELECT `tripplanner.v_inquiry_outbox` (tp-009);
  EXECUTE `geo.name_norm` (228).
- `tripplanner` role: DML on its 16 objects (default privileges + tp-008/010 grants); grandfathered reads into
  CIS (173 gateway config SELECT + `llm_call_log` INSERT, 179 `raw_tours` columns, 180/216 atoms, 201
  destinations + photo views, `published_tours` SELECT); `catalog.*` SELECT.
- `aa_app_user`: after 241 only RLS tables + `catalog.*` (+ `published_tours`/`raw_tours`/`seo_context`
  master-read policies, 239).
- **Default privileges live (dump 16/10):** only `FOR ROLE aa_cis_admin IN SCHEMA booking` (tables DML,
  sequences, functions → `booking`) and `FOR ROLE aa_cis_admin IN SCHEMA tripplanner` (tables DML, sequences
  → `tripplanner`). The 007b default ACL to `aa_app_user` is **no longer live** (N7 effectively done).
- **Cross-owner dependencies that break on an owner change if nobody grants them:**
  - `booking.v_schema_versions` reads `shared.schema_versions` (Booking readiness, `backend/app/db.py:99`).
    A view runs with its **owner's** rights, so `bk_owner` needs SELECT on `shared.schema_versions`.
  - Migrations self-register with `INSERT INTO shared.schema_versions`; once DB Migrate runs a Booking/TP file
    as `bk_owner`/`tp_owner`, those owners need INSERT (and SELECT for the runner's check).
  - CIS `services/photos/sync.py:101` reads frozen `tripplanner.itinerary_components` / `tripplanner.tour_stop`
    (works today only because the CIS runtime owns them; it swallows errors and returns `{}`).
  - 10 FKs `tripplanner.* → shared.destinations` (dump 16/10; 12 in revision 2 was wrong): RI checks run as the
    owner of the referenced table, so an owner change on the TP side is safe for DML; a **new** cross-owner FK
    would need REFERENCES (forbidden anyway). **But** re-adding one of these 10 (ALTER COLUMN … TYPE on the FK
    column, DROP + ADD CONSTRAINT, NOT VALID included) checks REFERENCES for the current role, which from tp-014
    is `tp_owner` → "permission denied for table destinations" (reproduced on PG16, review 17/10). No grant: a TP
    lint/inspect rule from tp-014 (S7) refuses those statements and points to X4 decoupling or a `roles/` file.

### 1.4 RLS policies that reference role names

| Table(s) | RLS | Policies | Effect when the CIS runtime stops being the owner |
|---|---|---|---|
| `published_tours`, `raw_tours`, `seo_context`, `generated_content`, `quality_scores`, `content_exports`, `webhook_deliveries`, `shared.pipeline_runs` | ENABLE **+ FORCE** | `tenant_isolation` **TO public** (NULLIF GUC); `catalog_owner_aa_master_read`, `aa_app_user_aa_master_read` | **none**: FORCE already filters the owner, so a non-owner `cis_app` sees exactly what `aa_cis_admin` sees today (code pins `app.tenant_id` = master, `services/places/store.py`) |
| `tenant_tour_versions`, `content_piece`, `angle_gate_request`, `angle_gate_option`, `publish_log`, `facts`, `tenant_integrations`, `acp_output_rules` | ENABLE, **no FORCE** (D2) | only `TO aa_app_user` (or none: `acp_output_rules`) | **breaks**: today the runtime is owner-exempt; a non-owner `cis_app` matches no policy → 0 rows, writes refused. Needs AA-817 D2 "role-scoped policies first": `… TO cis_app USING (true) WITH CHECK (true)` on exactly these tables |

Membership warning (lesson S236, `catalog_owner` revoke in 225): a policy `TO r` also applies to members of
`r`. **Never** make `aa_cis_admin`, `cis_owner` or `cis_app` a member of `aa_app_user` or `catalog_owner`
(master-read policies on FORCE tables would start returning master rows without the GUC).

### 1.5 Network

One app SG `sg-038383acb15660582` (`aa-cis-dev-sg-app`) is used by: CIS api + worker services, Booking
service (`booking.tf:401`), both TripPlanner Lambdas (`tripplanner.tf:326/366`), the dfs-balance Lambda
(`dfs_balance.tf:155`), every DB Migrate / Schema Dump task, and 2 orphan Lambda ENIs of the deleted function
`aa-cis-dev-ingestion`. The RDS SG `sg-055c18ce0bd00b5e3`, Redis SG `sg-0f5a810c884fd15bc` and EFS SG
`sg-085fa83fd09be7fe7` admit only that SG (inline `ingress {}` blocks in `modules/vpc`, `modules/elasticache`,
`modules/efs`). The app SG also has a vestigial self-ingress on 443 ("Secrets Manager VPC endpoint"): there are
**no** VPC endpoints (checked), AWS APIs go through the NAT instance. Booking and TripPlanner therefore reach
Redis (no AUTH) and every port of each other's tasks.

### 1.6 IAM hole that makes a DB role split cosmetic

`aws_iam_role_policy.ecs_task_policy` (`modules/ecs/main.tf:105`) grants the CIS task role
`secretsmanager:GetSecretValue` on `Resource = "*"`. A compromised CIS runtime can read `aa-cis/dev/rds` (master),
`booking/dev/database-url` and `tripplanner/dev/database-url`. Step S19 closes it; without S19, P0-9 is not met.

---

## 2. Target state (end of this plan)

| Schema(s) | Owner (NOLOGIN) | Runtime LOGIN role(s) | Consumer grants |
|---|---|---|---|
| `booking` | `bk_owner` | `booking` (name kept) | unchanged |
| `tripplanner` | `tp_owner` | `tripplanner` (name kept) | `booking`: SELECT `v_inquiry_outbox` (unchanged) |
| CIS schemas (`acp_*`, `shared`, `silver_aa_internal`, `gold_aa_internal`, `geo`, schema `catalog`) | `cis_owner` | `cis_app` (api + worker), `aa_app_user` (tenant pool) | unchanged |
| `catalog.*` views | `catalog_owner` (unchanged) | — | unchanged |
| `public` leftovers (`checkpoint_migrations`, legacy enums) | `aa_cis_admin` (left; dead/legacy, registry note) | — | — |

- `db_migrator` LOGIN, `CONNECTION LIMIT 5`, member of `bk_owner`, `tp_owner`, `cis_owner`, `catalog_owner`,
  `pg_read_all_stats`; runs from its **own** task definition `aa-cis-dev-db-migrate` with its own SG;
  `SET ROLE <live owner of the dir's schema>` per file (XD8).
- `aa_cis_admin` (master) = break-glass + three automated uses only, all read in-task from `aa-cis/dev/rds`:
  the Infra-native `roles/` dir, DB Migrate `mode=set-password` (`ALTER ROLE … PASSWORD` needs CREATEROLE), and
  extensions (`public` extensions `vector`, `pg_stat_statements` stay master-owned; `CREATE/ALTER EXTENSION` lives
  in `roles/`).
- `cis_app`: no ownership, not in `rds_superuser`, no `pg_read_all_data`, no BYPASSRLS, no write on
  `shared.schema_versions`, connection limit set from a measured peak (XD6, ≥ 90), **cannot read `booking.*` or
  `tripplanner.*`** (P0-9 probe).
- One SG per caller: `cis-api`, `cis-worker`, `booking-api`, `tp-lambda`, `db-migrate`, `ops-lambda`; RDS SG
  lists each DB caller; Redis SG lists only `cis-api` + `cis-worker`.

---

## 3. Decisions taken by this plan (defaults; Nghiệp can flip any before its step)

| # | Decision | Default (why) | Alternative |
|---|---|---|---|
| XD1 | Runtime role names | **Keep** `booking`, `tripplanner`, `aa_app_user` (no DSN, secret or app change; `<app>_app` naming is cosmetic). Record as legacy names in `owners.yaml` | Rename → `bk_app`/`tp_app`: new DSNs, 2 more hand edits, deploys |
| XD2 | Password of a new LOGIN role (`cis_app`, `db_migrator`) | **Nghiệp writes the DSN in the Console** (SEC-2), then DB Migrate `mode=set-password` reads that secret **inside the task**, sends only a SCRAM verifier (`ALTER ROLE … PASSWORD 'SCRAM-SHA-256$…'`), test-connects, logs no secret | The task generates the password and `PutSecretValue` (zero hand edits, but contradicts SEC-2 wording) |
| XD3 | Grants to `cis_app` on future CIS objects | **Default privileges `FOR ROLE <CIS owner>` in CIS schemas → `cis_app` only** (a CIS migration that forgets a grant would 500 the runtime after deploy; `cis_app` is CIS's own runtime, not a consumer). Needs an explicit exception row in Part A §9 / DM-8.3 (standards PR, Nghiệp approves) | Per-object grants in every CIS migration + a CI test that every CIS table has a `cis_app` grant |
| XD4 | When `db_migrator` exists | **Wave 5** (with `cis_owner`). Waves 1–4 run DB Migrate as the master from the new migrator task def; the runner switches to `bk_owner`/`tp_owner` per XD8 and a lint forbids role switching in owner files. Reason: without `cis_owner`, `db_migrator` could not run CIS files, so it would add a password and a secret for no gain | Create it in Wave 1 and keep the master for `cis/` only (two DSNs in the migrator task) |
| XD5 | Close the CIS task-role secret hole (S19) | **Yes**: explicit Deny on master, `booking/*`, `tripplanner/*`, `aa-cis/dev/db-migrator*`. ECS-exec scripts keep working for CIS-scope work as `cis_app`; master-level scripts run through the migrator task (`db/run_script` mode, S19). Roadmap D-07 stays A (exec is still the normal path) | Skip S19: the split stays bypassable (P0-9 not met) |
| XD6 | `cis_app` connection budget | **Measured, not assumed.** The master has no limit today, so a limit on `cis_app` is a new failure mode (SQLSTATE 53300). The main and worker pools are not the only sites: export pool (`services/export/handler.py:82`, `JOB_POOL_MAX`), `jev_gates` pool 4 (`services/ingestion/jev_gates.py:112`), grounding pool (`services/content_generation/grounding.py:266`), `shared/repository/database.py` pool 10, eval pool 2, and 37 ad-hoc `asyncpg.connect(…)` calls in `api/`, `services/`, `shared/`; rolling deploys run up to 200 % tasks. S15 lists every site in C2.2 and samples `pg_stat_activity` (master sessions by `application_name`, empty included) every minute across one busy wave; limit = max(90, 2 × measured peak + one extra api+worker task set for deploy overlap), written into C2.2 in the same PR. Plus a CloudWatch alarm on 53300 for `cis_app` (S18) | Fixed 90 (rejected: unproven) |
| XD7 | Probe-only migrations to prove `SET ROLE` | **Yes**, tiny files (`bk-015`, `tp-014`, CIS `246`) that assert `current_user` and register (cheap, permanent evidence). Undo files never take these keys: they are `roles/` files (XD8) | Wait for the next natural migration of each owner |
| XD8 | How the runner picks the role for a file | **Live schema owner.** For `booking/`, `tripplanner/`, `cis/` the runner reads the owner of the dir's anchor schema (`booking`, `tripplanner`, `shared`) just before the file. Owner = login role → run as is; owner ≠ login role → `SET ROLE <owner>` (refuse if the session user is not a member). `roles/` always runs as the master and is refused under any other login. Shipped in S1, a no-op until a transfer. The switch is then atomic with the transfer: the very next file of that owner runs as the new owner, so there is no window in which the master creates objects that no default privilege covers, and no separate "flip" PR | A per-dir constant flipped in a later PR (rejected: leaves gap windows S8→S9 and S21→S22, see §9 A2/B3) |
| XD9 | `catalog.*` view changes between S1 and S22 (review C1, S241) | **Frozen.** Since 225:426 the master is not a member of `catalog_owner` and must never become one (§1.4); the S1 lint refuses the old 225/235 `GRANT catalog_owner TO CURRENT_USER` dance in files ≥ 243, and the S22 recipe needs `db_migrator` (member of `catalog_owner`) as the login. So no `CREATE/ALTER/DROP VIEW catalog.*` from the S1 merge until S22 (≈ 2.5–3 weeks, Dev only). Enforced in S3: lint — catalog view DDL only after `SET LOCAL ROLE catalog_owner`, the membership-grant error names the freeze; runner — a linted owner file whose `SET LOCAL ROLE` target the login role is not a member of is refused with exit 8 at `check` (PostgreSQL checks the session user), so a catalog-recipe file fails before apply while the master is the login and passes from S22 with no change. Recorded in AA-CIS-App `CONTEXT.md` and the backlog | (b) a reviewed Infra-native `roles/` catalog file with the 225 dance + closing "master not a member" guard (rejected as default: the view SQL leaves AA-CIS-App, its CI replay tests a stale view, Copy Guard does not cover it); (c) `db_migrator` before Wave 2 (needs S11/S12 first). Either stays Nghiệp's call if a catalog change cannot wait |

---

## 4. Plan at a glance

Each step = one PR, or one migration + one apply. Steps inside a wave run in order; a wave starts when the
previous one is verified. "Train" = several migration PRs whose Infra copies go in **one** Infra PR and are
applied back-to-back the same day (simpler process, still one file per apply).

| Wave | Step | Repo(s) | What | Key | Effort (focused hours) |
|---|---|---|---|---|---|
| 1 Tooling | S1 | Infra | `owners.yaml`, `roles/` dir in DB Migrate, live-owner role switch (XD8, no-op today), ownership post-check, role/extension lint, `environment` input | — | 8 |
| | S2 | Infra | Isolation probe workflow (U-16), pending cells keyed to live state | — | 6 |
| 2 Booking/TP owners | S3 | Infra | Role bootstrap `rl-001`: `bk_owner`, `tp_owner`, `cis_app` (no password), N3 limits restated | `rl-001` | 2 |
| | S4 | CIS | `243`: USAGE `shared` + `shared.schema_versions` SELECT/INSERT → `bk_owner`, `tp_owner`; prefix trigger | `243` | 3 |
| | S5 | Booking | Guard + non-superuser CI + tests ready for `bk_owner` (no migration) | — | 5 |
| | S6 | Booking | `bk-014`: booking objects → `bk_owner`, default privileges restated | `bk-014` | 3 |
| | S7 | TripPlanner | `tp-013`: tripplanner objects → `tp_owner`, default privileges restated; TP lint for `tp_owner` | `tp-013` | 3 |
| | S8 | Infra | Train: copies of 243, bk-014, tp-013 + rl-001; apply `rl-001 → 243 → bk-014 → tp-013` | — | 2 (+ waits) |
| | S9 | Booking + TP + Infra copy | Probe files `bk-015`, `tp-014` (prove the automatic `SET ROLE`) | `bk-015`, `tp-014` | 2 |
| 3 Network + migrator | S10 | root | ADR 0004b (per-app SGs) | — | 2 |
| | S11 | Infra (TF) | Expand: 6 SGs + RDS/Redis/EFS ingress lists; migrator task def + roles (incl. S3 put on the dump prefix) + log stream; secret placeholders | — | 6 |
| | S12 | Infra (workflows) | DB Migrate + Schema Dump + probe use the migrator task def and SG; `set-password` + `run-script` modes | — | 4 |
| | S13 | Infra (TF) | Switch callers to their own SGs, **three applies**: Booking → TP + dfs Lambdas → CIS api + worker, each behind a manual idle gate | — | 4 |
| | S14 | Infra (TF) | Contract: drop `sg-app` from RDS/Redis/EFS ingress, after an ENI gate | — | 1 |
| 4 CIS runtime (AA-860) | S15 | CIS | Code prep: photo_sync on `geo`, connection-site inventory + peak measurement (XD6), standing ENABLE-only check, non-superuser CI, docstring | — | 6 |
| | S16 | CIS | `244`: grants + default privileges + D2 policies `TO cis_app` | `244` | 6 |
| | S17 | Nghiệp + Infra | `aa-cis/dev/rds-cis-app` value (hand) + `set-password cis_app` | — | 1 |
| | S18 | Infra (TF) + CIS deploy | Switch api + worker `DATABASE_URL` to `cis_app` | — | 3 |
| | S19 | Infra (TF) | Deny CIS task role on master / other-app secrets | — | 3 |
| 5 CIS owner + migrator | S20 | Infra | `rl-002`: `cis_owner`, `db_migrator` (limit 5, `pg_read_all_stats`), alarm row; staggered crons | `rl-002` | 2 |
| | S21 | CIS | `245`: CIS objects → `cis_owner`, default privileges restated | `245` | 6 |
| | S22 | Infra (+ hand) | Migrator logs in as `db_migrator` (master only for `roles/`, `set-password`); probe `246` | `246` | 4 |
| | S23 | root + all | Docs, standards §9, C2.2, skills, CONTEXT.md, backlog, Linear, lessons, CLAUDE.md (Nghiệp) | — | 4 |

**Total ≈ 91 focused hours ≈ 12 working days**, plus CI/apply waits (CI 3–5′, Terraform Apply ~5′, ECS rollout
2–5′, DB Migrate ~3′ per apply, ~22 applies/dispatches). Realistic wall clock: **2.5–3 weeks part-time**.
Waves 1–3 alone (Booking/TP isolation + SGs) ≈ 5 days and already deliver "Booking/TP objects not owned by the
CIS runtime" and network separation; Wave 4 delivers the P0-9 probe ("CIS runtime `SELECT booking.customers`
fails").

**Planned downtime: none.** Every switch is a rolling ECS deployment or a Lambda config update. Note the real
deployment settings: CIS api/worker use `deployment_minimum_healthy_percent = 50`, maximum 200 %
(`modules/ecs/main.tf:377/561`), circuit breaker on; at ≥ 2 tasks a roll can briefly halve capacity, and the
worker's 120 s drain releases running jobs (they re-run, repeated LLM spend). Booking's in-process `booking.job`
worker gets stopTimeout 30 s. So every ECS/Lambda change runs only when the job tables are idle (gate below).
`ALTER … OWNER` takes a brief ACCESS EXCLUSIVE lock per object: applies only run when every job table is idle
(DB Migrate idle check, C6.3b) and with `lock_timeout 5s`.

### Standing rules for every step
- `aws sts get-caller-identity --profile aa365-admin` before any write (DM-8.7); expect `005097885195`.
- D8 flow for migrations (MIG-4): owner migration-only PR → merge → Infra copy PR (Copy Guard) → merge →
  DB Migrate `check` → `apply` → schema-dump PR merged → probe run.
- Before each `apply` and each deploy: `shared.job` and `booking.job` idle, no open `rerun_wave`; never use
  `override_busy_jobs`. **Only DB Migrate and CIS Deploy Dev enforce this.** Terraform Apply has no busy check
  (plan + apply only), so before every Terraform Apply that touches `aws_ecs_service`, `aws_ecs_task_definition`
  or `aws_lambda_function` (S11 migrator task def excepted: unused; S13, S18, S19 if it rolls) run the
  **manual idle gate**: `GET /admin/job-runner/deploy-gate` → `safe_to_deploy=true` **and** a DB Migrate
  `mode=check` run whose busy lines show `booking.job` queued/running = 0. Paste both in the session log.
- **Per-owner migration freeze** around every ownership/runtime switch (S8 train, S18, S21–S22): from the first
  apply of the step until its verify passes, no other owner migration is copied into Infra (Copy Guard PRs wait)
  and, for S18, no CIS merge to `main` (Deploy Dev would redeploy). Announce start and end in the session log.
- Merges: Nghiệp asked S241 for code + push + merge + full verification; merge after CI green. If a hook blocks
  an agent merge, stop and ask.
- Commits: `feat|fix|chore|docs: …` + `Refs AA-xxx`; implementation notes in each repo's
  `docs/implementation-notes/<ISSUE>.md` while working.
- Every step ends with the probe (S2) run and its JSON summary pasted in the session log.

---

## 5. Steps in detail

### Wave 1 — tooling

#### S1. Infra: owner registry, `roles/` dir, live-owner role switch, ownership post-check, lint
- **Repo:** AA-CIS-Infra. One PR, no apply.
- **Change:**
  1. `db/owners.yaml` (DM-1.2): one entry per owner — `cis` (repo AA-CIS-App, path `api/migrations`, prefix
     `""`, anchor schema `shared`, owner role `aa_cis_admin` → later `cis_owner`, runtime `cis_app` +
     `aa_app_user`, job table `shared.job`, **schema list**: `acp_contract`, `acp_deliver`, `acp_gold_output`,
     `acp_shared`, `acp_silver_s2`, `acp_silver_s3`, `acp_silver_s4`, `catalog`, `geo`, `gold_aa_internal`,
     `shared`, `silver_aa_internal`), `booking` (`bk-`, anchor `booking`, `bk_owner`, `booking`, `booking.job`,
     exempt kind `bk_inquiry_pull`, kind prefix `bk_`), `tripplanner` (`tp-`, anchor `tripplanner`, `tp_owner`,
     `tripplanner`, kind prefix `tp_`), `roles` (Infra-native, prefix `rl-`, runs as the master; also owns
     extensions and `public.*` leftovers). Allowed consumer grants per owner (input for the later X2 guard). 244,
     245 and the probe take their CIS schema list from here (a test asserts the SQL files list the same set).
  2. `db-migrate.yml` input regex `^(cis|tripplanner|booking|roles)/…`, prefix `rl-` for `roles`.
  3. `check_migration_copies.py`: `roles/` files are Infra-native (no owner-repo comparison) but must carry
     `rl-NNN` registration; `check_migration_files.py` unique numbers covers `roles/`.
  4. `run_migration.py` role switch (XD8): before each file, `SELECT nspowner::regrole FROM pg_namespace WHERE
     nspname = <anchor>`. Owner = login role → no switch (today, for every dir). Otherwise
     `pg_has_role(session_user, owner, 'MEMBER')` or refuse, then `SET ROLE <owner>` before the file; the idle check
     runs as the login role before that, and `RESET ROLE` (runner only) precedes the post-check. `roles/` is refused
     unless the login role is the master. Step summary prints `ran as: <role>`.
  5. Ownership post-check inside the file's transaction, before COMMIT (after the runner's `RESET ROLE`):
     0 objects (`pg_class`, `pg_proc`, `pg_type` non-array) in the `owners.yaml` schemas owned by `session_user`
     when the file ran under a switch → else ROLLBACK with the object names. This catches a stray role reset inside
     a file creating objects as the login role (the S22 `RESET ROLE` → `db_migrator` case).
  6. Lint (applies to files above today's heads: CIS > 242, bk > 013, tp > 012; applied files never re-run, and
     225/235 legitimately use the old catalog dance): in every owner dir reject `RESET ROLE`, `SET ROLE` without
     `LOCAL`, `SET SESSION AUTHORIZATION`, `set_config('role'`, `CREATE/ALTER/DROP EXTENSION`,
     `CREATE/ALTER/DROP ROLE` (→ `roles/`). `booking/`, `tripplanner/`: no `SET LOCAL ROLE` at all. `cis/`: only
     `SET LOCAL ROLE catalog_owner`, `SET LOCAL ROLE cis_owner` (the way back, catalog recipe in S22) and
     `SET LOCAL ROLE cis_app` (guard blocks). Tests: the 244 and 245 drafts pass; a booking file with
     `RESET ROLE`, a cis file with `CREATE EXTENSION` and one with `SET LOCAL ROLE aa_app_user` are refused; the
     switch picks `bk_owner` when a fake catalog row says so.
  7. A unit test that `owners.yaml`, `OWNERS`/`PATH_RE`, the workflow regex and `IDLE_EXEMPT_KINDS` agree.
  8. `environment` input (choice `dev` only, DM-8.2) shown in the step summary.
- **Underscore env vars:** none new (the role map is read from the DB and `owners.yaml`, no new env var).
- **Verify:** `python3 -m unittest discover -s db/tests` green; DB Migrate `mode=check` on
  `cis/242_job_table_template_conformance.sql` → exit 0, "already applied", summary `ran as: aa_cis_admin`.
- **Rollback:** revert the PR. **Downtime:** none. **Effort:** 8 h.

#### S2. Infra: isolation probe workflow (U-16)
- **Repo:** AA-CIS-Infra. `db/isolation_probe.py` + `.github/workflows/db-isolation-probe.yml` (dispatch,
  nightly, and dispatched after every DB Migrate apply like the schema dump).
- **Change:** read-only (`BEGIN READ ONLY`, rolled back). Logs in **as each role with its own DSN secret**
  (no role memberships for the master, see §1.4 warning): `aa-cis/dev/rds-app-user`, `booking/dev/database-url`,
  `tripplanner/dev/database-url`, and later `aa-cis/dev/rds-cis-app`; master for the catalog part. Cells:
  - every runtime role: `rolsuper`, `rolbypassrls`, membership chain (must not contain `rds_superuser`,
    `pg_read_all_data`, `pg_write_all_data`, any `*_owner`), owns 0 objects, has a connection limit;
  - cross-app: `booking` → `SELECT 1 FROM tripplanner.sessions`, `shared.tenants` must raise 42501;
    `tripplanner` → `booking.customers` 42501; CIS runtime → `booking.customers`, `tripplanner.sessions` 42501;
  - ownership: no object in `booking` not owned by `bk_owner`, same for `tripplanner`/`tp_owner`, CIS
    schemas/`cis_owner`;
  - owner roles: `bk_owner`/`tp_owner` have USAGE on `shared` and SELECT+INSERT on `shared.schema_versions`;
    `cis_app` has no INSERT/UPDATE/DELETE on it;
  - standing RLS cell: every table in the CIS schemas with `relrowsecurity AND NOT relforcerowsecurity` has a
    permissive policy `TO cis_app` (or is on an allowlist in `owners.yaml`);
  - tenant matrix (aa817): `aa_app_user` own/foreign/forged/empty GUC on the RLS tables (0 cross-tenant rows);
    CIS runtime sees all rows of `tenant_tour_versions` (no GUC).
  - connections: sessions of `db_migrator` < its limit − 1; `aa_cis_admin` sessions other than this probe's own
    and `rdsadmin` listed (warning until S22, fail after).
  - **Isolation evidence only from the role under test.** RLS and count cells run through that role's own DSN,
    never as the master or `db_migrator` (members of owner roles and, for `db_migrator`, of `catalog_owner`,
    whose `catalog_owner_aa_master_read` policies apply to members: results there are not tenant-isolation
    evidence; the probe says so in its header).
  - **Runtime grants (review C4, S241):** `runtime_grants.<owner>` — the runtime role (`booking`, `tripplanner`,
    `cis_app` over the 11 CIS schemas without `catalog`) has USAGE on each schema, SELECT on every relation, USAGE
    on every non-identity sequence, EXECUTE on every non-trigger function (catalog facts via `has_*_privilege`);
    `default_acl.<owner>` — `pg_default_acl` FOR ROLE <live owner of the anchor schema> IN SCHEMA s grants it the
    `owners.yaml` table / sequence / function sets, and no FOR ROLE master row is left once transferred (a
    bk-014/tp-013/245 that forgets the restated rows fails here, not as 42501 on the first bk-015+/tp-014+/246+
    table after deploy); `consumer.contract_grants` — contract grants on single objects (`booking` →
    `tripplanner.v_inquiry_outbox`, `geo.name_norm`; `tripplanner` → `shared.llm_call_log` INSERT). Mirrored in
    `owners.yaml` `runtime_privileges` / `runtime_privileges_from` (test_owners_registry).
  - **Role attributes:** runtime and owner roles must have no SUPERUSER, BYPASSRLS, **CREATEROLE**, CREATEDB,
    REPLICATION (review C5: on PG 15 a CREATEROLE role can grant itself any owner role).
  - **Pending cells keyed to live state, not to a PR.** Each not-yet-true cell carries a state key read at run
    time: ownership / runtime-grant / default-privilege cells of `booking` expected iff `bk-014` is in
    `shared.schema_versions` **and** schema `booking` is owned by `bk_owner` (`tripplanner` ↔ `tp-013` +
    `tp_owner`, CIS ↔ `245` + `shared` owned by `cis_owner`; review C7: registry rows are never deleted, so after a
    planned rollback through a `roles/` undo file the cells go back to pending instead of failing every night);
    `cis_app` grant cells from `244`; CIS-runtime cross-app cells iff the api task definition's `DATABASE_URL` secret is
    `aa-cis/dev/rds-cis-app` (`describe-task-definition` of the running service revision); `cis_app` login and
    cross cells iff its secret holds a `cis_app` DSN **and** the role carries the `x1:password-set` comment
    written by `set-password` (review C8: between Nghiệp's Console edit and set-password the login fails with
    28P01 → pending + warning, not red); `db_migrator` cells iff `rl-002` is registered. So the probe stays green
    between the applies of a train with no expectation PRs. The "fails when a pending cell already passes" rule
    remains only for cells without a state key.
  - Output: one JSON summary + a step-summary table; the job fails on any mismatch.
- **Runs where:** from the api task def until S12, then from the migrator task def. Cron staggered from the
  schema dump (dump 03:43 UTC, probe 04:13 UTC) so the two never hold `db_migrator` sessions together.
- **Verify:** first dispatch green with the pending cells listed. **Rollback:** revert. **Effort:** 6 h.

### Wave 2 — Booking and TripPlanner owners

#### S3. Infra: role bootstrap `rl-001`
- **Repo:** AA-CIS-Infra, file `db/migrations/roles/001_x1_owner_roles.sql` (key `rl-001`). Applied in the S8
  train, first.
- **Change (idempotent, guarded `DO` blocks, no password anywhere):**
  - `CREATE ROLE bk_owner NOLOGIN`, `CREATE ROLE tp_owner NOLOGIN`; `GRANT bk_owner, tp_owner TO aa_cis_admin`
    (needed for `ALTER … OWNER TO` in PG 15 and for break-glass).
  - `CREATE ROLE cis_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS CONNECTION LIMIT 90` without a
    password (cannot log in until S17; 90 is the floor, raised before S18 if the XD6 measurement says so); `GRANT cis_app TO aa_cis_admin` (only so 244's guard can
    `SET LOCAL ROLE cis_app`; harmless: policies `TO cis_app` exist only on ENABLE-only tables where the master
    is owner-exempt). Never grant `aa_app_user` or `catalog_owner` to anyone here. Static test (all `roles/`
    files, scoped by grantee, review C2): `aa_app_user` to nobody, `catalog_owner` only `TO db_migrator` (so
    rl-002 passes); `owners.yaml` `migrator_member_of` lists what `db_migrator` must reach.
  - Restate the N3 attributes (move them into the bootstrap, MIG-6): `ALTER ROLE tripplanner CONNECTION LIMIT 30`,
    `booking 15`, `aa_app_user 15` (same values as 234, no behaviour change).
  - Guard: after the file, `bk_owner`/`tp_owner` NOLOGIN, `cis_app` not member of anything, no BYPASSRLS.
  - `INSERT INTO shared.schema_versions ('rl-001', …) ON CONFLICT DO NOTHING`.
- **Secrets:** none yet (placeholder for `cis_app` comes in S11).
- **Verify:** schema reference "Roles" table shows the 3 new roles; probe green (pending cells unchanged).
- **Rollback (review C6):** a bare `DROP ROLE` fails as soon as 243 (right after rl-001 in the train) or 244
  reference the roles. Prepared (unmerged) `roles/` undo `s3-undo/0NN_x1_rl001_undo.sql` (this folder): refuses
  while any of the three roles owns an object (`pg_shdepend` owner rows: after bk-014/tp-013 their undo files run
  first) or `cis_app` has a session; drops 243's key-guard trigger + function; `DROP OWNED BY cis_app, tp_owner,
  bk_owner` (revokes privileges, default-privilege entries and policy role references); `DROP ROLE`. Dry-run on
  PG 16 after rl-001 → 243 → a 244 stand-in: bare `DROP ROLE` fails with 6 dependencies, the undo commits.
  **Downtime:** none. **Effort:** 2 h.

#### S4. CIS `243`: what the new owners need from CIS
- **Repo:** AA-CIS-App, `api/migrations/243_x1_owner_role_grants.sql` (re-check the next free number at PR time;
  `main` ends at 242, open PR #791 has no migration).
- **Change:**
  1. `GRANT USAGE ON SCHEMA shared TO bk_owner, tp_owner;` (the dump gives USAGE on `shared` only to
     `aa_app_user`, `catalog_owner`, `tripplanner`; without it the first file run as `bk_owner` fails on its own
     `INSERT INTO shared.schema_versions` with "permission denied for schema shared").
  2. `GRANT SELECT, INSERT ON shared.schema_versions TO bk_owner, tp_owner;` unguarded (rule 5, roles exist after
     rl-001).
  3. Registry integrity: `shared.schema_versions_key_guard()` (plpgsql, not SECURITY DEFINER) + `BEFORE INSERT`
     trigger: `current_user = 'bk_owner'` and `NEW.version NOT LIKE 'bk-%'` → RAISE; same for `tp_owner`/`tp-%`.
     A Booking/TP file can then never register a CIS or `rl-` key and make DB Migrate skip the real file
     (`run_migration.py:448` matches by version only). No UPDATE/DELETE granted to anyone but the owner.
  4. Header + `SET LOCAL lock_timeout`. CI: `tests/integration/conftest.py` creates `bk_owner`, `tp_owner` (and
     `cis_app` for S16) before the migration loop; a test inserts `'246'` as `bk_owner` and expects the RAISE.
- **Verify:** dump shows the grants and the trigger; `booking.v_schema_versions` still readable after S8 (Booking
  readiness); probe owner-role cells pass.
- **Rollback:** forward REVOKE/DROP TRIGGER file. **Downtime:** none. **Effort:** 3 h.

#### S5. Booking prep PR (no migration)
- **Repo:** AA-Booking.
- **Change:**
  1. `backend/tests/migration_guard.py`: allow `ALTER … OWNER TO bk_owner` on `booking.*` objects and
     `ALTER SCHEMA booking OWNER TO bk_owner` (bk-014 only). `MIGRATION_ROLE` (`:28`, used at `:209-215`) becomes a
     per-file value: `aa_cis_admin` for bk-001…bk-014, **`bk_owner` from bk-015 on**. From bk-015, every
     `ALTER DEFAULT PRIVILEGES` must read `FOR ROLE bk_owner IN SCHEMA booking`, and `FOR ROLE aa_cis_admin` is
     rejected except the `REVOKE` in bk-014 (otherwise a new file following today's rule fails as `bk_owner` with
     "must be member of role aa_cis_admin", or recreates the revoked rows). `CREATE ROLE` rule unchanged.
  2. CI as the real RDS shape, not a superuser (`ci.yml:118` today makes `aa_cis_admin` the container
     superuser, which skips membership, ownership, schema-CREATE and all RLS checks, so bk-014 would pass CI and
     fail only on Dev): container bootstrap user `postgres`; a setup step creates `aa_cis_admin NOSUPERUSER
     CREATEROLE CREATEDB LOGIN`, makes it owner of the test database, creates `bk_owner` NOLOGIN, `booking`,
     `GRANT bk_owner TO aa_cis_admin` (simulates rl-001) and gives `bk_owner` the 243 grants on the stand-in
     `shared.schema_versions` (USAGE `shared`, SELECT, INSERT); the replay runs as `aa_cis_admin` and, like the runner
     (XD8), does `SET ROLE bk_owner` before each file once `booking` is owned by `bk_owner`. The superuser is used
     only for that bootstrap.
  3. `conftest.py:34` keeps `aa_cis_admin` as the admin DSN user (now non-superuser); `test_bk001.py:43` owner
     assertion → `{aa_cis_admin, bk_owner}` until bk-014 is in the replay, then `bk_owner`;
     `tests/integration/supply.py` disables triggers via `SET ROLE bk_owner`.
- **Verify:** Booking CI green (replays bk-001…013 twice, as non-superuser). **Effort:** 5 h.

#### S6. Booking `bk-014`: ownership to `bk_owner`
- **Repo:** AA-Booking, `migrations/014_x1_bk_owner.sql` (migration-only PR after S5 merges).
- **Change (explicit statements generated from a live introspection, MIG-4, no dynamic SQL):**
  1. Guard: `bk_owner` exists, `pg_has_role(current_user, 'bk_owner', 'MEMBER')`; snapshot of
     `has_table_privilege('booking', t, 'SELECT,INSERT,UPDATE,DELETE')` per table into a temp table.
  2. `ALTER SCHEMA booking OWNER TO bk_owner;` (first: the new owner needs CREATE on the schema).
  3. `ALTER TABLE booking.<t> OWNER TO bk_owner;` for every table (owned sequences and indexes follow);
     `ALTER VIEW booking.v_customer_summary / v_schema_versions OWNER TO bk_owner;`; `ALTER SEQUENCE` only for
     sequences with no `pg_depend` deptype `a`/`i` (an owned/identity sequence refuses a separate owner change);
     `ALTER FUNCTION booking.<f>() OWNER TO bk_owner;` for the 12 trigger functions.
  4. `ALTER DEFAULT PRIVILEGES FOR ROLE bk_owner IN SCHEMA booking GRANT SELECT, INSERT, UPDATE, DELETE ON
     TABLES TO booking;` + sequences `USAGE, SELECT` + functions `EXECUTE` (bk-001 restated, Part A §9 row);
     `ALTER DEFAULT PRIVILEGES FOR ROLE aa_cis_admin IN SCHEMA booking REVOKE … FROM booking` (the old rows).
  5. Guard: 0 objects in `booking` not owned by `bk_owner` (else RAISE: a new object appeared, regenerate);
     `booking`'s privileges equal the snapshot; `has_schema_privilege('bk_owner', 'shared', 'USAGE')` and
     `has_table_privilege('bk_owner', 'shared.schema_versions', 'SELECT,INSERT')` (243 applied first;
     `has_table_privilege` alone ignores schema USAGE). The view read as `booking` itself is checked live (readiness), because the
     master is not a member of `booking`.
  6. Register `bk-014`.
- **Deploy order:** S5 merged → bk-014 PR merged → S8 train.
- **Verify (after apply):** `GET https://api-booking.lumiguides.it.com/booking/health/ready` → 200 with
  `schema_version` list; staff API smoke (list customers with the CIS staff token); one `bk_inquiry_pull` claim
  in `booking.job` after the next TripPlanner inquiry (or the periodic pull row moving to `succeeded`); probe
  ownership cell `booking` flips to pass.
- **Rollback:** prepared (unmerged) Infra-native `db/migrations/roles/0xx_x1_bk_owner_undo.sql` (key `rl-0xx`,
  next free number at the time) that alters everything back to `aa_cis_admin` and restores the old default
  privileges. It must be a `roles/` file: once `booking` is owned by `bk_owner` the runner runs `booking/` files
  as `bk_owner` (XD8), and `ALTER … OWNER TO aa_cis_admin` needs membership in `aa_cis_admin`, which `bk_owner`
  does not have. Applying it also turns the runner back to the master for `booking/` automatically, and the S2
  probe's ownership / runtime-grant cells back to pending (they key on the live owner of `booking` + `bk-014`,
  review C7). The probe key `bk-015` is never used for the undo.
- **Downtime:** none, but Booking requests wait while the file runs: every lock is held until COMMIT, all taken up
  front by one `LOCK TABLE` (hot tables first, app inbox order; all or none within `lock_timeout` 5 s), and
  `bk_inquiry_pull` is exempt from the idle check, so the worker and staff API may be live (review 17/10).
  **Effort:** 3 h.
- **Ownership only (review 17/10):** `aa_cis_admin` inherits `bk_owner` (rl-001; per-grant `INHERIT FALSE` is PG 16),
  so the CIS runtime keeps owner rights on `booking.*` until S18 + S19. P0-9 is **not** met at S8: the probe cell
  "CIS runtime → `booking.customers` 42501" stays pending, and no SEC-1 / P0-9 item closes on bk-014.

#### S7. TripPlanner `tp-013`: ownership to `tp_owner`
- **Repo:** AA-TripPlanner-Web, `migrations/013_x1_tp_owner.sql`.
- **Change:** same pattern as bk-014 for the 16 objects (15 tables incl. the frozen place read models,
  `v_inquiry_outbox`) and their standalone sequences; `ALTER DEFAULT PRIVILEGES FOR ROLE tp_owner IN SCHEMA
  tripplanner GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO tripplanner` + sequences; revoke the
  `FOR ROLE aa_cis_admin` rows. The view keeps `booking`'s SELECT grant (ACLs are rewritten to the new owner) and
  runs as `tp_owner` over `tripplanner.outbox`, which it now owns.
- **Testing:** TripPlanner has no migration replay CI: dry-run the file locally on a throwaway PostgreSQL 15
  container with stand-in roles (`aa_cis_admin` non-superuser + CREATEROLE, `tp_owner`, `tripplanner`,
  `booking`) and the tp-001…012 files, run as the non-superuser stand-in and then, for a test file after tp-013,
  with `SET ROLE tp_owner`; `run_migration.py --inspect` for the lint. TP lint/inspect mirrors S5: from tp-014,
  `ALTER DEFAULT PRIVILEGES` must read `FOR ROLE tp_owner`, `FOR ROLE aa_cis_admin` rejected (except tp-013's
  `REVOKE`).
- **Verify:** TripPlanner browse + assembly Lambdas answer (open `aa-tripplanner.vercel.app`, plan a trip;
  CloudWatch `Errors` = 0 on both functions for 15 min); submit one test inquiry → new `tripplanner.outbox` row →
  Booking pull creates the trip case (end-to-end through `v_inquiry_outbox`); probe cell `tripplanner` passes.
- **Guard** also asserts `has_schema_privilege('tp_owner', 'shared', 'USAGE')`.
- **Rollback:** prepared (unmerged) `roles/` undo file, key `rl-0xx` (same reason as S6; `tp-014` stays the
  probe key). **Downtime:** none. **Effort:** 3 h.

#### S8. Infra train: copies + applies
- **Repo:** AA-CIS-Infra, one PR: `db/migrations/roles/001_x1_owner_roles.sql` (native) + byte copies
  `cis/243_…`, `booking/014_…`, `tripplanner/013_…` (Copy Guard green).
- **Apply order (DB Migrate `check` then `apply` each):** `roles/001` → `cis/243` → `booking/014` →
  `tripplanner/013`. All four run as the master from the api task def (S12 not yet done): each file runs as the
  login role because the anchor schema is still master-owned when it starts (XD8). From the moment bk-014
  commits, the next `booking/` file runs as `bk_owner` with no further PR; same for `tripplanner/` after tp-013.
  The old `FOR ROLE aa_cis_admin` default privileges can therefore be revoked inside bk-014/tp-013 without a gap.
- **Freeze:** Booking and TP migration freeze (Standing rules) from the merge of this PR until S9's probes pass.
- **Verify:** each apply exit 0; schema-dump PR shows owners `bk_owner`/`tp_owner`; S6 + S7 live checks; probe
  green at every point of the train (state-keyed cells). In the S8 session log and probe summary the "CIS runtime →
  `booking.customers` 42501" cell stays **pending** (ownership only, see S6); do not close SEC-1 / P0-9 on it.
- **Effort:** 2 h + waits (~20 min).

#### S9. Probe files that prove the automatic `SET ROLE`
- **Repos:** AA-Booking `migrations/015_x1_set_role_probe.sql`; AA-TripPlanner-Web
  `migrations/014_x1_set_role_probe.sql`; one Infra copy PR. Each probe file:
  `DO $$ BEGIN IF current_user <> 'bk_owner' THEN RAISE EXCEPTION …; END IF; END $$;` + registration. No runner
  change (XD8 already switches).
- **Verify:** both probe applies exit 0 and the step summary says `ran as: bk_owner` / `tp_owner` (proves the
  switch, USAGE `shared`, the 243 INSERT grant and the prefix trigger); end of the Booking/TP freeze.
- **Rollback:** none needed (assert-only files). **Downtime:** none. **Effort:** 2 h.

### Wave 3 — per-app security groups and the migrator task definition

#### S10. Root: ADR 0004b
- **Repo:** AA-Ecosys root, `docs/adr/0004b-per-app-security-groups.md` (amends ADR 0004 decision 5 "existing
  … app security group" and its "no module edit" boundary for `modules/vpc`, `modules/ecs`,
  `modules/elasticache`, `modules/efs`). Content: one SG per caller (§2), RDS/Redis/EFS ingress by SG, no
  self-443 rule, Booking/TP never reach Redis, migrator SG, orphan ENI cleanup, prod uses the same shape (C7.2c).
  ADR README index row. **Effort:** 2 h.

#### S11. Terraform expand: SGs, migrator task def, secret placeholders (no service change)
- **Repo:** AA-CIS-Infra, then the manual **Terraform Apply** workflow.
- **Change:**
  1. New `accounts/aa365/app_security_groups.tf`: `aa-cis-dev-sg-cis-api` (ingress tcp 8000 from the ALB SG),
     `aa-cis-dev-sg-cis-worker` (no ingress), `aa-cis-dev-sg-booking-api` (tcp 8000 from the ALB SG),
     `aa-cis-dev-sg-tp-lambda`, `aa-cis-dev-sg-db-migrate`, `aa-cis-dev-sg-ops-lambda` (no ingress). All egress
     `0.0.0.0/0` (NAT for AWS APIs, Bedrock, Mapbox).
  2. Ingress lists: the RDS, Redis and EFS SGs use **inline** `ingress {}` blocks, which are authoritative —
     adding separate `aws_vpc_security_group_ingress_rule` resources would be deleted on the next apply. So add a
     list variable per module (`modules/vpc` `rds_ingress_sg_ids`, `modules/elasticache` `ingress_sg_ids`,
     `modules/efs` `ingress_sg_ids`) used inside the inline block, defaulting to `[sg_app_id]`. Set: RDS =
     `[sg-app, cis-api, cis-worker, booking-api, tp-lambda, db-migrate]`; Redis = `[sg-app, cis-api,
     cis-worker]`; EFS = `[sg-app, cis-api, cis-worker]`.
  3. Migrator: task def family `aa-cis-dev-db-migrate` (CIS api image, same tag the api runs; command supplied
     per run), own execution role (GetSecretValue on `aa-cis/dev/rds` only, later `aa-cis/dev/db-migrator`), own
     task role (GetSecretValue on the DSN secrets the probe and `set-password` need: `aa-cis/dev/rds`,
     `aa-cis/dev/rds-app-user`, `aa-cis/dev/rds-cis-app`, `aa-cis/dev/db-migrator`, `booking/dev/database-url`,
     `tripplanner/dev/database-url`; no Bedrock; S3 only `s3:PutObject` on the schema-dump key prefix and the
     probe-output prefix, because `db/schema_dump.py:366` uploads its JSON with boto3 `put_object` under the task
     role — anything else via presigned URLs), log stream prefix `migrate` in
     `/ecs/aa-cis-dev`, 0.25 vCPU / 0.5 GB. The task-def container `secrets` line maps the env var that
     `run_migration.py` reads to `aa-cis/dev/rds` (master) — ⚠️ **underscore env var, Nghiệp edits by hand**.
     Role names inside `aa-*-dev-*` so the apply role may pass them (workload boundary applies).
  4. Secret placeholders with `ignore_changes = [secret_string]` (the `tripplanner_db` pattern):
     `aa-cis/dev/rds-cis-app`, `aa-cis/dev/db-migrator`. Under `aa-cis/dev/*` so the existing CIS execution-role
     pattern can inject `rds-cis-app` in S18.
  5. `observability_ecosys.tf` `rds_role_connection_limits`: add `cis_app = 90` (alarm; updated with the XD6 limit), `db_migrator = 5` in S20.
- **Cost:** SGs, roles, task def and 2 secrets: ≈ $0.80/month (2 × $0.40 secrets); no new compute.
- **Verify:** `terraform plan` shows only additions + 3 in-place SG rule changes; after apply,
  `aws ec2 describe-security-groups --group-ids sg-055c18ce0bd00b5e3 --profile aa365-admin --region us-west-1 --query 'SecurityGroups[0].IpPermissions[0].UserIdGroupPairs[].GroupId'`
  lists 6 sources; all apps unchanged (still on `sg-app`).
- **Rollback:** revert PR + apply (nothing uses the new objects yet). **Downtime:** none. **Effort:** 6 h.

#### S12. Workflows on the migrator task def; `set-password` and `run-script` modes
- **Repo:** AA-CIS-Infra.
- **Change:** `db-migrate.yml`, `db-schema-dump.yml`, `db-isolation-probe.yml`: `run-task --task-definition
  aa-cis-dev-db-migrate`; subnets still read from the api service; security group looked up inline by name
  `aa-cis-dev-sg-db-migrate` (no new env var); log stream `migrate/migrate/<task id>`; container name
  `migrate`. New `mode` choices:
  - `set-password` (input `role`, allowlisted from `owners.yaml`: `cis_app`, `db_migrator`): the runner reads the
    role's DSN secret in-task, checks the DSN user equals the role, computes a SCRAM-SHA-256 verifier locally,
    runs `ALTER ROLE <role> PASSWORD '<verifier>'` as the master, then connects with the DSN and prints only
    `current_user` and `rolconnlimit`; after that test connection succeeds it runs `COMMENT ON ROLE <role> IS
    'x1:password-set <UTC time> by DB Migrate set-password (run <id>)'` as the master (the S2 probe expects the
    role's login only once this marker exists, review C8). Nothing secret is logged; RDS statement logging sees
    only the verifier.
  - `run-script` (input: path of a reviewed script under `db/scripts/` on `main`): replaces master-level ECS-exec
    scripts after S19 (XD5). Same presigned-URL plumbing as migrations.
  - ⚠️ The task needs the target role name: one new env var in the run-task override and its read in
    `run_migration.py` — **underscore env var, Nghiệp writes those two lines by hand** (proposed name in the PR
    description).
- **Verify:** DB Migrate `check` on `cis/242` from the new task def → exit 0; Schema Dump dispatch **finishes
  green and a new JSON object exists at the dump key in S3** (`aws s3 ls` on the dump prefix, timestamp after the
  run) — the dispatch from DB Migrate is `continue-on-error: true`, so a broken dump would otherwise stay invisible
  behind green applies; probe dispatch green; RDS `pg_stat_activity` shows `db-migrate` from the new SG's ENI.
- **Rollback:** revert the PR (api task def path still works until S18). **Effort:** 4 h.

#### S13. Terraform switch: each caller on its own SG
- **Repo:** AA-CIS-Infra, Terraform Apply.
- **Change:** `modules/ecs`: new optional variables `sg_api_id`, `sg_worker_id` (`coalesce(…, var.sg_app_id)`) for
  the two `network_configuration` blocks (`main.tf:398`, `:571`); `booking.tf:401` → booking SG;
  `tripplanner.tf:326/366` → tp-lambda SG; `dfs_balance.tf:155` → ops-lambda SG.
- **Deploy order: three PRs, three applies, each behind the manual idle gate (Standing rules) and verified
  before the next:** (a) Booking service → booking SG; (b) TP browse + assembly + dfs Lambdas → their SGs (wait for
  `LastUpdateStatus = Successful` on each); (c) CIS api + worker → their SGs. ECS services roll (a network change
  creates a new deployment with the current task def; `ignore_changes` covers only
  `desired_count`/`task_definition`; CIS min healthy 50 %, see §4); Lambdas get a new VPC config (one cold start
  each).
- **Verify:** `aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-api aa-cis-dev-worker aa-booking-dev-api --profile aa365-admin --region us-west-1 --query 'services[].{s:serviceName,sg:networkConfiguration.awsvpcConfiguration.securityGroups,r:deployments[0].rolloutState}'`
  → own SGs, `COMPLETED`; CIS admin smoke (e2e admin login → `GET /admin/job-runner/jobs?limit=1` 200, a Redis
  flag read works); a worker claim (any due job, or the 300 s ops sampler line); Booking ready 200; TP plan page +
  Lambda `Errors` 0; dfs Lambda next scheduled run succeeds; **negative:** from the Booking container (ECS exec,
  python socket connect to the Redis endpoint:6379 with 3 s timeout) → timeout.
- **Rollback:** revert the sub-step PR + apply (that caller back on `sg-app`, still allowed **only until S14**).
  **Downtime:** none (rolling, circuit breaker rolls back a task that fails health). **Effort:** 4 h.

#### S14. Terraform contract: `sg-app` out of RDS/Redis/EFS
- **Gate before merging the S14 PR** (it stays unmerged until S13 a–c are verified; Terraform Apply applies all
  of Infra `main`, so a merged S14 would ride along with any apply):
  `aws ec2 describe-network-interfaces --filters Name=group-id,Values=sg-038383acb15660582 --profile aa365-admin --region us-west-1 --query 'NetworkInterfaces[].{id:NetworkInterfaceId,d:Description,s:Status}'`
  → only the 2 orphan `aa-cis-dev-ingestion` ENIs, status `available`; and for each VPC Lambda
  `aws lambda get-function-configuration --function-name <fn> --profile aa365-admin --region us-west-1 --query '{s:LastUpdateStatus,sg:VpcConfig.SecurityGroupIds}'`
  → `Successful` with the new SG (old hyperplane ENIs stay on `sg-app` until then). Plus the manual idle gate.
- **Change:** drop `sg-app` from the three ingress lists; drop the vestigial self-443 rule; keep `sg-app` itself
  (orphan ENIs of `aa-cis-dev-ingestion` still reference it — delete those ENIs by hand when `available`, then
  remove the SG in a later cleanup PR).
- **Verify:** RDS SG lists the 5 per-app sources only; repeat the S13 smoke; probe green.
- **Rollback:** revert + apply. After S14, rolling back any S13 sub-step (or an ECS circuit-breaker rollback to a
  deployment on `sg-app`) needs `sg-app` re-added to the ingress lists **first** (revert S14, apply), else the
  tasks cannot reach RDS. **Effort:** 1 h.

### Wave 4 — CIS runtime on `cis_app` (AA-860)

#### S15. CIS code prep (deployable on its own)
- **Repo:** AA-CIS-App, normal deploy.
- **Change:** `services/photos/sync.py` `itinerary_places` reads `geo.tour_place` (`tour_id`, `destination_id`)
  `UNION geo.tour_stop` joined to `silver_aa_internal.raw_tours` on `source_id` instead of the frozen
  `tripplanner.*` tables (ADR 0007; removes the last CIS read of the TP schema); `aa544_tenant_pool.py:26`
  docstring ("BYPASSRLS" → "owner + ENABLE without FORCE").
  - **Connection budget (XD6):** list every connection site (`create_pool(`, `asyncpg.connect(`) with its max in
    the C2.2 row (root PR); a read-only `db/scripts/` sampler (run through the migrator, S12 `run-script`)
    records `count(*)` of master sessions by `application_name` (empty included) every minute during one busy
    wave or batch; set the `cis_app` limit from it (rl-file `ALTER ROLE cis_app CONNECTION LIMIT n` if it differs
    from 90) before S18. If the peak is high, first move per-job pools and ad-hoc connects onto the worker pool.
  - **CI as the RDS shape** (`ci.yml:141` today: `cistest SUPERUSER`, which skips membership, ownership,
    schema-CREATE and RLS checks): for the X1 replays (243–246) the loop runs as `aa_cis_admin NOSUPERUSER
    CREATEROLE CREATEDB`, owner of the test database, created by the superuser bootstrap; 245+ run with the XD8
    switch (`SET ROLE cis_owner`); a second job runs 246 as a `NOSUPERUSER` `db_migrator` with the runner's switch.
    Superuser stays only for bootstrapping the container. CI `conftest.py` creates `cis_app`, `bk_owner`,
    `tp_owner`, later `cis_owner`.
  - New test `test_x1_cis_app_privileges.py` (applies after 244 in CI: as `cis_app`, every CIS table is readable,
    ENABLE-only RLS tables return all tenants' rows without a GUC, FORCE tables return 0 rows without the master
    GUC, writes on `shared.job` work, INSERT/DELETE on `shared.schema_versions` raise 42501,
    `booking`/`tripplanner` stand-ins raise 42501), plus the **standing ENABLE-only check**: enumerate
    `relrowsecurity AND NOT relforcerowsecurity` across the `owners.yaml` CIS schemas and assert each has a
    permissive policy `TO cis_app` or is on the allowlist, so a later migration from any lane that adds an
    ENABLE-only table without the policy fails CI instead of silently returning 0 rows to the runtime.
- **Verify:** CI green; deploy rollout COMPLETED; photo sync dry run on one country returns the same matches as
  before (compare counts); measured peak and chosen limit in the session log. **Effort:** 6 h.

#### S16. CIS `244`: everything `cis_app` needs, D2 policies
- **Repo:** AA-CIS-App, `api/migrations/244_x1_cis_app_runtime.sql`; Infra copy; apply.
- **Change:**
  1. For **every CIS schema in `owners.yaml` except `catalog`** (11: `acp_contract`, `acp_deliver`,
     `acp_gold_output`, `acp_shared`, `acp_silver_s2`, `acp_silver_s3`, `acp_silver_s4`, `geo`,
     `gold_aa_internal`, `shared`, `silver_aa_internal`; the four `acp_gold_output`/`acp_silver_s*` are empty today
     but CIS code already targets `acp_silver_s4.social_content`, `api/routers/v1_social.py:79/157/221/247`):
     `GRANT USAGE ON SCHEMA … TO cis_app;` `GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA … TO
     cis_app;` `GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA … TO cis_app;` `GRANT EXECUTE ON ALL
     FUNCTIONS IN SCHEMA … TO cis_app;` Then `REVOKE INSERT, UPDATE, DELETE ON shared.schema_versions FROM
     cis_app;` (the runtime must not edit the migration registry; DB Migrate would re-apply or skip files).
     Nothing in `booking`, `tripplanner`, `catalog` (CIS code reads no `catalog.*` view; checked), `public`
     (`checkpoint_migrations` unused: no LangGraph saver in code).
  2. XD3: `ALTER DEFAULT PRIVILEGES FOR ROLE aa_cis_admin IN SCHEMA <the same 11 schemas> GRANT … TO cis_app`
     (tables DML, sequences, functions). Restated `FOR ROLE cis_owner` in 245. Default privileges do not touch
     the existing `shared.schema_versions`, so the REVOKE above holds.
  3. D2 role-scoped policies on **exactly** the ENABLE-without-FORCE tables (`relrowsecurity AND NOT
     relforcerowsecurity` in CIS schemas; today 8: `tenant_tour_versions`, `content_piece`, `angle_gate_request`,
     `angle_gate_option`, `publish_log`, `facts`, `tenant_integrations`, `acp_output_rules`):
     `CREATE POLICY <table>_cis_app_all ON <t> AS PERMISSIVE FOR ALL TO cis_app USING (true) WITH CHECK (true);`
     This reproduces today's owner exemption for the runtime only. **No** policy on FORCE tables: `cis_app` must
     stay under `tenant_isolation TO public` exactly like the master today (a `USING (true)` there would return
     every tenant's rows to code that relies on the master GUC).
  4. Register `244`.
  5. Guards (RAISE on failure), **placed last, after the registration** so the role switch below never precedes
     other statements; the runner's own `RESET ROLE` precedes its post-check: the ENABLE-only set equals the 8
     names (a new one fails loudly → add it); `cis_app` is not member of any role, not BYPASSRLS;
     `has_schema_privilege('cis_app', s, 'USAGE')` for all 11 schemas; `NOT has_table_privilege('cis_app',
     'shared.schema_versions', 'INSERT')` / `'DELETE'`; behavioural block with `SET LOCAL ROLE cis_app` (allowed by
     the S1 lint in `cis/`; membership from rl-001): `count(*)` of `tenant_tour_versions` under a forged GUC = the
     master's count; `count(*)` of `published_tours` without GUC = 0 (FORCE still filters); `SELECT FROM
     booking.customers` raises `insufficient_privilege` (caught and asserted).
- **Verify:** apply exit 0; schema dump shows the policies and grants; probe (still expected-fail on the
  cross-app cells: runtime not switched yet). **Rollback:** forward file dropping the 8 policies and revoking.
  **Downtime:** none (CIS still runs as master). **Effort:** 6 h (incl. CI conftest + test).

#### S17. Password for `cis_app`
- ⚠️ **Nghiệp, by hand, in the AWS Console** (Secrets Manager → `aa-cis/dev/rds-cis-app` → Retrieve → Edit
  plaintext): copy the DSN format of `aa-cis/dev/rds-app-user`, change the user to `cis_app` and set a new
  random password (≥ 32 chars). The DSN contains underscores (`cis_app`, `aa_cis_dev`): edit by hand, never
  paste into chat.
- Then dispatch DB Migrate `mode=set-password`, role `cis_app`.
- **Verify:** run log shows `current_user=cis_app rolconnlimit=<XD6 limit>`; probe cell "CIS runtime login works" passes.
- **Rollback:** none needed (unused credential). **Effort:** 1 h (incl. Nghiệp's 5 min).

#### S18. Switch api + worker to `cis_app`
- **Repo:** AA-CIS-Infra (Terraform) + AA-CIS-App deploy (workflow_dispatch, no code change).
- **Change:** `accounts/aa365/main.tf:177` `secret_rds_arn = aws_secretsmanager_secret.cis_app_db.arn` (module
  input that feeds the `DATABASE_URL` env var of api and worker) — ⚠️ **changes what `DATABASE_URL` resolves to;
  Nghiệp reviews the one-line diff in VSCode before merge**. Root PR: C2.2 row `cis-api`/`cis-worker` "today →
  `cis_app`".
- **Why the order is strict:** Deploy Dev copies the family's LATEST revision and runs on every CIS push to
  `main` touching `api/**`, `shared/**`, `services/**`. As soon as Terraform registers the `cis_app` revisions,
  the next CIS merge from any lane switches `DATABASE_URL`, planned or not. The Terraform-registered revision
  (N+1) also carries image `:latest` (`modules/ecs/main.tf:295/496`), so only the revision running before the
  apply (N) is a safe rollback target.
- **Deploy order:**
  1. Record the running task-definition ARNs of `aa-cis-dev-api` and `aa-cis-dev-worker` in the session log:
     `aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-api aa-cis-dev-worker --profile aa365-admin --region us-west-1 --query 'services[].{s:serviceName,td:taskDefinition}'`.
  2. Start the CIS merge freeze (Standing rules). Merge the S18 Infra PR **only right before its own apply** (no
     other Terraform Apply in between).
  3. Manual idle gate → Terraform Apply (registers the new revisions; services ignore them) → dispatch
     AA-CIS-App **Deploy Dev** on current `main` (it copies LATEST and swaps in the current SHA, AA-651) → both
     rollouts COMPLETED.
  4. Same PR: CloudWatch metric filter + alarm on `too many connections for role "cis_app"` (SQLSTATE 53300) in
     the api/worker log groups.
- **Verify (all must pass before calling it done):**
  - `pg_stat_activity`: `cis-api`, `cis-worker`, `cis-tenant` sessions; the first two as `cis_app` (probe or
    schema dump "Connections" table);
  - admin smoke with the e2e admin login: `GET /admin/job-runner/jobs?limit=1` 200; Content Quality tour-versions
    list returns the same row count as before (ENABLE-only table through the new policy); one tenant `/v1`
    read on the e2e tenant;
  - worker: one cheap job claimed and `succeeded` (e.g. a single-tour T2 rewrite on the trial tour, or the next
    scheduled retention job) — report job vs ECS-exec;
  - **P0-9 probe:** CIS runtime `SELECT 1 FROM booking.customers` → 42501; `tripplanner.sessions` → 42501;
    membership chain of `cis_app` empty; these cells become expected automatically (state key: the running api
    task def's `DATABASE_URL` secret) and pass;
  - Booking ready 200, TP plan page (unaffected, but the instance is shared);
  - CloudWatch `AA/RDS RoleConnections Role=cis_app` appears within 10 min.
- **Rollback:**
  - Fast (~5 min): `aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-api --task-definition <recorded api ARN> --profile aa365-admin --region us-west-1`
    (same for `aa-cis-dev-worker` with its recorded ARN). Keep the CIS merge freeze: LATEST still points at
    `cis_app`, so any Deploy Dev would undo the rollback.
  - Durable: revert the Terraform line → manual idle gate → Terraform Apply → dispatch Deploy Dev (LATEST is back
    on the master DSN) → rollouts COMPLETED. Lift the freeze only after that.
- The freeze ends when the verify list above passes.
- **Downtime:** none (rolling). Risk window: a code path needing a grant 244 missed → 500 on that route; the
  smoke list above and CloudWatch 5xx for 30 min catch it. **Effort:** 3 h.

#### S19. Close the secret hole; master scripts through the migrator
- **Repo:** AA-CIS-Infra (Terraform) + root docs.
- **Change:** `modules/ecs/main.tf` `ecs_task_policy`: add a `Deny secretsmanager:GetSecretValue` statement on
  `arn:aws:secretsmanager:us-west-1:005097885195:secret:aa-cis/dev/rds-??????`,
  `…:secret:aa-cis/dev/db-migrator-??????`, `…:secret:booking/*`, `…:secret:tripplanner/*`. (The execution
  role still injects secrets; only code in the container loses access.) Document the new path for master-level
  scripts: DB Migrate `mode=run-script` (S12). Skill `aa-cis-schema` `references/ecs-exec.md`: CIS-scope scripts
  keep the S3-mediated ECS-exec pattern and now run as `cis_app` through `DATABASE_URL`; anything needing
  `booking.*`, `tripplanner.*` or role/catalog work uses `run-script`.
- **Verify:** from the api container (ECS exec, python boto3) `get_secret_value('aa-cis/dev/rds')` →
  AccessDenied; `aa-cis/dev/rds-app-user`, `booking-jwt-signing-key`, `e2e-tenant/*`, `gdrive-photo-reader`
  still readable (tenant pool, Booking JWT, e2e sync, photos work: smoke one of each); probe green.
- **Rollback:** revert + apply. **Downtime:** none. **Effort:** 3 h.

### Wave 5 — CIS owner, `db_migrator`, master as break-glass

#### S20. Infra `rl-002`: `cis_owner`, `db_migrator`
- **Change:** `CREATE ROLE cis_owner NOLOGIN`; `GRANT CREATE ON DATABASE aa_cis_dev TO cis_owner` (CIS creates
  schemas); `GRANT cis_owner TO aa_cis_admin`. `CREATE ROLE db_migrator LOGIN NOCREATEROLE NOBYPASSRLS
  CONNECTION LIMIT 5` (no password; 5, not 3: DB Migrate (group `db-migrate`, also `run-script`/`set-password`),
  Schema Dump (group `db-schema-dump`) and the probe have separate concurrency groups and can overlap; one shared
  group was rejected because GitHub keeps only one pending run per group and would drop a queued apply);
  `GRANT bk_owner, tp_owner, cis_owner, catalog_owner, cis_app TO db_migrator` (`catalog_owner` so CIS view
  migrations can `SET LOCAL ROLE catalog_owner`: `SET ROLE` checks the **session** user's membership, so
  `cis_owner` itself never joins `catalog_owner` — §1.4 warning; `cis_app` for the same reason, so a CIS file
  with a 244-style guard block (`SET LOCAL ROLE cis_app`) still runs after S22 — review C3; harmless: its only
  policies are `USING (true)` on ENABLE-only tables, where `db_migrator` is already exempt through `cis_owner`,
  and `db_migrator` results are never tenant evidence). The list equals `owners.yaml` `migrator_member_of`
  (S3 static test); guard asserts `pg_has_role('db_migrator', r, 'MEMBER')` for each and **not** for
  `aa_app_user`; `GRANT pg_read_all_stats TO db_migrator` (without it
  `pg_stat_activity` hides `state`/`query` of other roles' sessions and the dump's Connections table and the
  probe's session cells go blank; guard asserts `pg_has_role('db_migrator','pg_read_all_stats','USAGE')`). The
  master keeps `CREATEROLE` for `roles/` and `set-password`. Register `rl-002`.
  Terraform (same train, applied before S22 switches any workflow): alarm row `db_migrator = 5` in
  `rds_role_connection_limits`; probe cron staggered from the dump cron (S2).
- ⚠️ **Nghiệp by hand:** value of `aa-cis/dev/db-migrator` (DSN, user `db_migrator`, new password) in the
  Console; then DB Migrate `mode=set-password`, role `db_migrator`.
- **Verify:** set-password log `current_user=db_migrator rolconnlimit=5`; dump Roles table; CloudWatch
  `AA/RDS RoleConnections Role=db_migrator` alarm exists.
- **Rollback:** forward drop file, prepared (unmerged) `roles/` undo `s20-undo/0NN_x1_rl002_undo.sql` (this
  folder): refuses while `cis_owner` owns anything (245 undo first, S21), `db_migrator` holds any privilege or
  has a session (roll S22 back first); `DROP OWNED BY cis_owner` (revokes CREATE on the database), `DROP ROLE
  db_migrator, cis_owner`. Dry-run on PG 16 (S244, AA-CIS-Infra `docs/implementation-notes/AA-860-S20.md`).
  **Effort:** 2 h.

#### S21. CIS `245`: CIS objects to `cis_owner`
- **Repo:** AA-CIS-App, `api/migrations/245_x1_cis_owner.sql`; apply as the master (member of `cis_owner`).
- **Change (explicit statements generated from a live introspection; ~120 objects):** `ALTER SCHEMA … OWNER TO
  cis_owner` for `acp_contract`, `acp_deliver`, `acp_gold_output`, `acp_shared`, `acp_silver_s2/s3/s4`, `catalog`
  (the schema only), `geo`, `gold_aa_internal`, `shared`, `silver_aa_internal`; every table/view/matview, standalone
  sequence, function and enum in those schemas except the `catalog_owner` views and extension-owned objects
  (deptype `e`); leave `public.*` and the extensions (`vector`, `pg_stat_statements`) on the master (registry
  note in `owners.yaml`: they belong to `roles/`). Restate `ALTER DEFAULT PRIVILEGES FOR ROLE cis_owner IN SCHEMA
  <the 11 owners.yaml CIS schemas except catalog> GRANT … TO cis_app` and revoke the `FOR ROLE aa_cis_admin` rows
  from 244 — safe with no gap, because from the commit of 245 the runner runs `cis/` files as `cis_owner` (XD8;
  the master is a member after rl-002). Grants (to `aa_app_user`, `tripplanner`, `booking`, `catalog_owner`,
  `cis_app`) carry over with the owner change; the `schema_versions` REVOKE from 244 is restated.
- **Freeze:** CIS migration freeze from the 245 Infra copy until S22's `246` probe passes.
- **RLS effect:** ENABLE-only tables: `cis_app` keeps its policy; the master stays exempt as a member of
  `cis_owner`. FORCE tables: unchanged for everyone.
- **Guards:** 0 objects in CIS schemas owned by `aa_cis_admin` (outside `public`); no SECURITY DEFINER function;
  behavioural counts as in 244 (runtime, `aa_app_user` via its own policies) unchanged; catalog views still
  work: `has_table_privilege('catalog_owner', t, 'SELECT')` for every base table the 14 views read, plus
  `count(*)` of `catalog.v_tour` **as the master directly** (no `SET ROLE`: the master is not a member of
  `catalog_owner` since 225:426 and must not become one; a non-security-invoker view checks its base tables and RLS
  as its owner `catalog_owner` anyway). The final behavioural block (`SET LOCAL ROLE cis_app`) comes last, after
  the registration, as in 244.
- **Verify:** apply exit 0 with all job tables idle; probe ownership cell for CIS passes; CIS admin + tenant
  smoke (as S18); Booking `catalog.v_tour` read in the staff e-mail path; TP browse (reads `published_tours` +
  `catalog`). **Rollback:** prepared (unmerged) `roles/` undo file, key `rl-0xx` (owners back to
  `aa_cis_admin`; a `cis/` file would run as `cis_owner` and could not give objects back); applying it returns the
  runner to the master for `cis/` automatically. **Downtime:** none. **Effort:** 6 h.

#### S22. Migrator logs in as `db_migrator`
- **Repo:** AA-CIS-Infra (+ AA-CIS-App probe file `246`).
- **Change:** migrator task def DB secret → `aa-cis/dev/db-migrator` (⚠️ the `secrets` line naming the env var:
  **Nghiệp edits by hand**); execution role GetSecretValue on that secret only. The runner needs no role map
  change: with `db_migrator` as login, every owner dir is switched by XD8 (`SET ROLE bk_owner/tp_owner/cis_owner`),
  and a dir whose anchor schema is still master-owned is refused. Three things keep the master, read in-task from
  `aa-cis/dev/rds` (constant, task role only): `roles/` files, `mode=set-password` (`ALTER ROLE … PASSWORD` needs
  CREATEROLE; `db_migrator` is NOCREATEROLE), and extension changes (they live in `roles/`, the S1 lint rejects
  them elsewhere). `owners.yaml` and the registry say so.
- **CIS catalog-view recipe** (replaces the 225 `GRANT catalog_owner TO CURRENT_USER` dance; documented in
  AA-CIS-App `CONTEXT.md` migration notes and the `aa-cis-schema` skill). From this step the DB Migrate login is a
  member of `catalog_owner`, so the runner's reach check lets recipe files through: **end of the XD9 freeze**
  (announce it in the session log and the AA-CIS-App `CONTEXT.md` note). After 245, `cis_owner` owns schema
  `catalog` and `catalog_owner` has only USAGE on it, so `CREATE OR REPLACE VIEW catalog.*` fails both as
  `cis_owner` ("must be owner") and as plain `catalog_owner` ("permission denied for schema catalog"):
  ```sql
  GRANT CREATE ON SCHEMA catalog TO catalog_owner;
  SET LOCAL ROLE catalog_owner;
  CREATE OR REPLACE VIEW catalog.v_… AS …;
  SET LOCAL ROLE cis_owner;        -- the way back; never RESET ROLE (it returns to the login role)
  REVOKE CREATE ON SCHEMA catalog FROM catalog_owner;
  ```
  A `RESET ROLE` would return to `db_migrator`, which inherits CREATE on every CIS schema through `cis_owner`;
  objects created after it would be owned by `db_migrator`, outside `FOR ROLE cis_owner` default privileges, so
  `cis_app` would get 42501. The S1 lint rejects `RESET ROLE`, and the S1 post-check rejects any object owned by
  `session_user` before COMMIT. `246` CI test includes one view created with this recipe.
- CIS `246_x1_set_role_probe.sql` asserts `current_user = 'cis_owner'`.
- Schema dump runs as `db_migrator` (INHERIT: member of every owner, sees every object in `information_schema`;
  `pg_read_all_stats` for the Connections table). The probe's role-isolation cells keep using each runtime
  role's own DSN (S2); only its catalog/ownership/session cells run as `db_migrator`.
- **Verify:** DB Migrate `check` on `cis/242` and `booking/013` → exit 0; apply `cis/246` → exit 0 with
  `ran as: cis_owner`; schema dump green with a new S3 object and non-blank `state` in its Connections table for
  `cis_app`/`booking`/`tripplanner`/`aa_app_user`; RDS `pg_stat_activity` shows `db-migrate` as `db_migrator`;
  a `set-password` run for `cis_app` with the unchanged secret (idempotent) exits 0 (master path); no session of `aa_cis_admin` except break-glass over 24 h
  (`AA/RDS` has no master metric: the nightly probe's session cell). End of the CIS migration freeze.
- **Rollback:** revert the PR (task def back to master). **Effort:** 4 h.

#### S23. Close-out
- **Root PR:** `docs/database/schema-ownership.md` (owner roles column, `rl-` key space, booking row now
  `bk_owner`), standards Part A §9 rows retired (`aa_cis_admin` everything; bk-001 default privileges; Booking/TP
  objects owned by the migrator) + XD3 exception row, SEC-6 note "runtime role `cis_app`", C2.2 roles column,
  DM-8.9 break-glass text; ADR 0008 follow-up line; backlog (AA-860 → §5 when done); session log; skills
  `aa-cis-schema` (ECS exec, DB connection, catalog-view recipe), `aa-ship` (verify list, manual idle gate before
  Terraform applies that roll services), `aa-ecosys-repos`; each repo's `CONTEXT.md` (AA-CIS-App migration notes:
  every new ENABLE-without-FORCE table needs a policy `TO cis_app`; never `RESET ROLE`; catalog recipe; no
  EXTENSION/ROLE statements outside `roles/`); `skill/aa-lessons/lessons.md` line "ENABLE-only RLS table without a
  `cis_app` policy = 0 rows for the runtime (S241, AA-860). Caught by: CI standing check + probe cell".
- ⚠️ **Nghiệp by hand:** `~/.claude/CLAUDE.md` section "S3-MEDIATED ECS EXEC PATTERN" → "DB connection: Secret:
  aa-cis/dev/rds" becomes "the container's `DATABASE_URL` (`cis_app`); master scripts via DB Migrate
  `run-script`" (only Nghiệp edits CLAUDE.md; underscore names).
- Linear: AA-860 Done only with the S18/S22 evidence (aa-ship); comment the probe JSON. **Effort:** 4 h.

---

## 6. Hand edits for Nghiệp (underscore env vars and secret values)

⚠️ This contains underscore env vars — edit manually in VSCode / the AWS Console. Claude prepares everything
else and lists the exact file and line in each PR description.

| # | Step | Where | Edit |
|---|---|---|---|
| H1 | S11 | `infra/AA-CIS-Infra` migrator task def (new resource) | the container `secrets` entry naming the DB env var the runner reads → `aa-cis/dev/rds` ARN |
| ~~H2~~ | S12 | — | **Void (S242):** the role travels in the existing `MIGRATION_MODE` value; no new env var |
| H3 | S17 | Secrets Manager `aa-cis/dev/rds-cis-app` | DSN for `cis_app` with a new password (Console) |
| H4 | S18 | `accounts/aa365/main.tf:177` | `secret_rds_arn` → `cis_app` secret (feeds `DATABASE_URL` of api + worker): review/confirm the one-line diff |
| H5 | S20 | Secrets Manager `aa-cis/dev/db-migrator` | DSN for `db_migrator` with a new password (Console) |
| H6 | S22 | migrator task def `secrets` entry | DB env var → `aa-cis/dev/db-migrator` ARN |
| H7 | S23 | `~/.claude/CLAUDE.md` | ECS-exec / DB connection section |

Not needed: no change to `booking/dev/database-url`, `tripplanner/dev/database-url`, `aa-cis/dev/rds-app-user`,
GitHub secrets (`TF_VAR_DB_PASSWORD` stays until U-41), Vercel env.

---

## 7. Risks and how the plan handles them

| Risk | Where | Handling |
|---|---|---|
| ENABLE-only RLS tables return 0 rows to a non-owner runtime | S18 | 244 D2 policies `TO cis_app` on exactly those 8 tables + guard that the set did not grow; S18 Content Quality count check |
| A **later** migration adds an ENABLE-only table without a `cis_app` policy | after S18 | standing CI check (S15) + nightly probe cell (S2) enumerate `relrowsecurity AND NOT relforcerowsecurity`; lessons + CONTEXT note (S23) |
| Gap window: master creates owner-dir objects after a transfer, no default privilege covers them → runtime 42501 | S8, S21 | XD8 live-owner switch: the next file after a transfer runs as the new owner; per-owner freeze |
| Stray `RESET ROLE` in a file run by `db_migrator` creates mis-owned objects | S22+ | S1 lint rejects `RESET ROLE`; S1 post-check rejects objects owned by `session_user` before COMMIT; catalog recipe returns with `SET LOCAL ROLE cis_owner` |
| CI replays as superuser hide membership/ownership/RLS failures | S5, S15 | X1 replays run as `NOSUPERUSER CREATEROLE` `aa_cis_admin` and a NOSUPERUSER `db_migrator` |
| Registry corrupted by a wrong key or a runtime DELETE | S4, S16 | 243 prefix trigger for `bk_owner`/`tp_owner`; 244 revokes INSERT/UPDATE/DELETE on `shared.schema_versions` from `cis_app` |
| `bk_owner`/`tp_owner` lack USAGE on `shared` → registration INSERT fails | S9 | 243 grants USAGE; bk-014/tp-013 guards use `has_schema_privilege`; probe cell |
| Schema dump silently stops (S3 put denied, dispatch is continue-on-error) | S12 | migrator task role `s3:PutObject` on the dump/probe prefixes; S12 verify requires a new S3 object |
| `cis_app` limit hit (53300) by pools outside main/worker | S18 | XD6 inventory + measured peak before S18; 53300 metric filter + alarm |
| S18 rollback undone by the next CIS merge (Deploy Dev copies LATEST) | S18 | recorded ARNs, CIS merge freeze, durable rollback via Terraform revert + Deploy Dev |
| Terraform Apply rolls services mid-job (no busy check, min healthy 50 %) | S13, S18, S19 | manual idle gate; S13 split into three applies |
| S14 merged before S13 verified, or S13 rolled back after S14 | S14 | S14 PR stays unmerged until the ENI + Lambda gate; re-add `sg-app` before any S13 rollback |
| `db_migrator` connection limit exhausted by overlapping workflows | S22 | limit 5, staggered crons, alarm row in S20 |
| Probe red for hours during a train | S8, S18, S21 | pending cells keyed to live state |
| Probe red every night after a planned rollback (registry rows stay) | S6, S7, S21 | ownership/grant cells key on transfer key **and** live anchor owner (review C7) |
| A runtime role loses a grant on the owner's next object (missing/old default privileges) → 42501 after deploy | S6, S7, S16, S21 | probe `runtime_grants.<owner>` + `default_acl.<owner>` cells (review C4) |
| A `catalog.*` view change between S1 and S22 fails at apply (master not in `catalog_owner`) | S1–S22 | XD9 freeze; lint + runner refuse it at `check` (exit 8) |
| `db_migrator` cannot `SET LOCAL ROLE cis_app` after S22 | S20, S22 | rl-002 grants `cis_app`; `migrator_member_of` test; runner reach check at `check` (review C3) |
| A runtime role with CREATEROLE grants itself any owner role | all | probe attribute cells refuse CREATEROLE/CREATEDB/REPLICATION (review C5) |
| `cis_app` login red between the Console edit and `set-password` | S17 | login expected only after the `x1:password-set` comment (review C8) |
| A `USING (true)` policy on a FORCE table would widen CIS reads | S16 | explicitly none on FORCE tables; guard counts `published_tours` without GUC = 0 |
| Policies `TO r` apply to members of `r` (S236 lesson) | S3, S20 | never grant `aa_app_user`/`catalog_owner` to the master, `cis_owner` or `cis_app`; `catalog_owner` only to `db_migrator` (session user), whose own query results are therefore never tenant-isolation evidence (probe uses each runtime role's DSN) |
| `booking.v_schema_versions` (view, owner rights) loses `shared.schema_versions` | S6 | 243 grants SELECT to `bk_owner` before bk-014; readiness 200 is the verify |
| Registration INSERT fails once files run as `bk_owner`/`tp_owner` | S9 | 243 INSERT grant; probe files prove it |
| Default privileges bound to the old creator | S6, S7, S21 | restated `FOR ROLE <owner>`; old `FOR ROLE aa_cis_admin` rows revoked; XD3 for `cis_app` |
| Owned/identity sequences reject `ALTER SEQUENCE … OWNER` | S6, S7, S21 | only standalone sequences altered; table owner change carries the rest |
| New object created between writing and applying an owner-transfer file | S6, S7, S21 | final guard "0 objects not owned by X" raises → regenerate the list |
| SECURITY DEFINER functions changing meaning with the owner | all | none exist (dump); 245 guard asserts none |
| Views owned by `catalog_owner` read CIS tables through grants | S21 | grants carry over (grantor becomes `cis_owner`); 245 guard checks `has_table_privilege('catalog_owner', …)` and counts `catalog.v_tour` as the master (no membership) |
| DB Migrate currently runs from the api task def → would run as `cis_app` after S18 | S12 | migrator task def before S18 (hard dependency) |
| Schema dump / probe lose visibility as non-master | S12, S22 | run from the migrator task; `db_migrator` INHERIT member of every owner + `pg_read_all_stats` |
| Prepared undo files cannot run once the dir runs as its owner | S6, S7, S21 | undos are `roles/` files (`rl-0xx`), run as the master; probe keys stay `bk-015`/`tp-014`/`246` |
| Routine master needs after S22 (password rotation, extensions, `public.*`) | S22 | `set-password` and `roles/` read the master DSN in-task; lint routes EXTENSION/ROLE statements to `roles/`; `owners.yaml` note |
| CIS task role reads every secret (`Resource "*"`) | S19 | explicit Deny; without S19 the split is bypassable (P0-9 not met) |
| Inline SG `ingress {}` blocks are authoritative | S11 | ingress via module list variables, not separate rule resources |
| ECS network change and Lambda VPC change during jobs | S13 | manual idle gate before each of the three applies; rolling deploy, circuit breaker |
| Orphan ENIs of a deleted Lambda keep `sg-app` alive | S14 | keep `sg-app`, delete ENIs when `available`, drop SG later |
| Booking CI and tests assume `aa_cis_admin` owns `booking.*` | S5 | guard + tests updated before bk-014 |
| TripPlanner has no migration replay CI | S7 | local throwaway PG 15 dry run, lint, careful verify |
| `run-script` and `set-password` widen what DB Migrate can do | S12 | allowlisted roles/scripts from `main` only, `environment: prod` gate as today, scripts reviewed in PR |
| Master still exists with CREATEROLE + `pg_read_all_data` | S22 | only `roles/`, `set-password` and break-glass; password rotation and RDS-managed secret are U-17/U-41 after this plan |

---

## 8. Verification summary (what "done" means)

1. Probe JSON (S2) all green, no pending cell left: runtime roles have no ownership/membership/BYPASSRLS, each has a
   connection limit; cross-app reads raise 42501 (`cis_app` → `booking.customers`, `tripplanner.sessions`;
   `booking` → `tripplanner.sessions`, `shared.tenants`; `tripplanner` → `booking.customers`); every object owned
   by its schema owner; aa817 tenant matrix 0 cross-tenant rows.
2. Each app live: CIS admin + tenant smoke 200, a worker job claimed and succeeded; Booking
   `/booking/health/ready` 200 and an inquiry pulled end to end; TripPlanner plan page and Lambda `Errors` 0.
3. `pg_stat_activity` / schema dump "Connections": `cis-api`/`cis-worker` as `cis_app`, `db-migrate` as
   `db_migrator`, no routine `aa_cis_admin` session.
4. Network: each service/Lambda on its own SG; RDS SG lists 5 per-app sources; Redis only CIS api/worker; a
   Booking-to-Redis connect times out.
5. CIS task role cannot read `aa-cis/dev/rds`, `booking/*`, `tripplanner/*`.
6. Migrations: the probe files `bk-015`, `tp-014`, `246` show `ran as: <owner>`; 0 objects in any owner schema
   owned by a login role; `shared.schema_versions` writable only by the owners (prefix trigger) and not by
   `cis_app`; every ENABLE-only CIS table has a `cis_app` policy (CI + probe).
7. Schema dump fresh in S3 after the last apply, Connections table with non-blank states.
8. Docs and standards updated (S23); AA-860 closed with evidence.

---

## 9. Review handled (revision 2, 17/10)

Two review passes, 19 points. Each was checked against the code before editing; references are to the files read.

### Pass A

| # | Point | Verdict | Where in the plan |
|---|---|---|---|
| A1 | `RESET ROLE` after `SET LOCAL ROLE catalog_owner` returns to `db_migrator` and creates mis-owned objects; catalog views fail as `cis_owner` and as `catalog_owner` | **Accepted, except (a).** Confirmed: 225:77-78 and 235:139-141 use `RESET ROLE`; 225:378/386 grant CREATE on `catalog` only for that file. Done: (b) lint rejects `RESET ROLE`, allows `SET LOCAL ROLE cis_owner` as the way back (S1); (c) catalog-view recipe (S22, CONTEXT.md, skill); (d) ownership post-check before COMMIT (S1). **(a) `db_migrator NOINHERIT` rejected:** NOINHERIT also cuts inherited rights from `pg_read_all_stats` (needed for A10) and from the owner roles, so `information_schema` (which the schema dump reads) would show nothing as `db_migrator`; (b)+(d) already make a stray reset fail loudly | S1 items 5–6, S22 |
| A2 | Grants missing between ownership transfer and runner flip (S8→S9, S21→S22) | **Accepted, different fix:** the runner's switch is keyed on the live schema owner (XD8), so it is atomic with the transfer and needs no flip PR; per-owner freeze added | XD8, S1 item 4, S8, S9, S21 |
| A3 | 245 guard cannot `SET LOCAL ROLE catalog_owner` (master not a member since 225:426); 244 `SET LOCAL ROLE cis_app` rejected by the S1 lint | **Accepted.** 245 uses `has_table_privilege('catalog_owner', …)` + counts `catalog.v_tour` as the master (a view checks its base tables as its owner); lint allows `SET LOCAL ROLE cis_app` in `cis/`, lint tests run the 244/245 drafts | S1 item 6, S16 item 5, S21 |
| A4 | `cis_app` limit 90 ignores other pools and ad-hoc connects; deploys double tasks | **Accepted.** Confirmed: export, `jev_gates` (4), grounding, `shared/repository/database.py` (10), eval (2) pools and 37 ad-hoc `asyncpg.connect` in `api/`, `services/`, `shared/`; max 200 %. Limit now measured (≥ 90) + 53300 alarm | XD6, S15, S18 |
| A5 | CI replays run as superuser (Booking `ci.yml:118`, CIS `ci.yml:141`) | **Accepted.** X1 replays as NOSUPERUSER CREATEROLE `aa_cis_admin`, S22 path as NOSUPERUSER `db_migrator`; superuser only for bootstrap | S5, S15 |
| A6 | Registry integrity: any key from `bk_owner`/`tp_owner`; `cis_app` can DELETE rows | **Accepted.** BEFORE INSERT prefix trigger (chosen over RLS: RLS on the registry would also filter every non-owner reader, e.g. `cis_app` after S18); 244 revokes INSERT/UPDATE/DELETE from `cis_app` + guard | S4, S16 |
| A7 | Master still needed for `set-password`, extensions, `public.*` | **Accepted.** `set-password` and `roles/` read the master DSN in-task; lint routes EXTENSION/ROLE statements to `roles/`; `owners.yaml` note | §2, S1 item 6, S21, S22 |
| A8 | 244 covers 7 schemas, 245 transfers 11 (+`catalog`); `acp_silver_s4.social_content` used by `v1_social.py` | **Accepted.** Confirmed in the dump (4 empty schemas) and `api/routers/v1_social.py:79/157/221/247`. 244/245 use the `owners.yaml` list (11, `catalog` excluded); the standing ENABLE-only check covers all of them | S1 item 1, S16, S21 |
| A9 | Booking guard pins `MIGRATION_ROLE = "aa_cis_admin"` (`migration_guard.py:28/209-215`) | **Accepted.** Per-file role: `bk_owner` from bk-015, `FOR ROLE aa_cis_admin` rejected except bk-014's REVOKE; TP mirrored | S5, S7 |
| A10 | Dump/probe blind as `db_migrator` (`pg_stat_activity`), `catalog_owner` membership skews RLS results | **Accepted.** `GRANT pg_read_all_stats TO db_migrator`; isolation cells only through each runtime role's own DSN; probe header states `db_migrator` results are not tenant-isolation evidence | S2, S20, S22 |

### Pass B

| # | Point | Verdict | Where in the plan |
|---|---|---|---|
| B1 | `bk_owner`/`tp_owner` lack USAGE on schema `shared` | **Accepted.** Confirmed in the dump Schemas table. 243 grants USAGE; bk-014/tp-013 guards use `has_schema_privilege`; probe cell | S4, S6, S7, S2 |
| B2 | Schema dump `put_object` (`db/schema_dump.py:366`) denied after S11; dispatch is `continue-on-error` | **Accepted.** Migrator task role gets `s3:PutObject` on the dump/probe prefixes; S12 verify requires a new S3 object | S11, S12, S22 |
| B3 | Default-privilege gap windows | **Accepted** (same as A2): XD8 live-owner switch; freezes | XD8, S8, S21 |
| B4 | Undo files cannot run after the switch; key collision with probe files | **Accepted.** Undos are `roles/` files `rl-0xx`; probe keys fixed | S6, S7, S9, S21 |
| B5 | S18 rollback undone by the next Deploy Dev; ambiguous `<previous rev>`; unplanned cutover | **Accepted.** Confirmed: Deploy Dev on push to `api/**`, `shared/**`, `services/**`, copies LATEST; images `:latest` at `main.tf:295/496`. Recorded ARNs, merge-just-before-apply, CIS merge freeze, fast vs durable rollback | S18 |
| B6 | S13 has no idle guard; min healthy is 50 %, not 100 % | **Accepted.** Confirmed: Terraform Apply workflow has no busy check; `main.tf:377/561` = 50. Manual idle gate (standing rule), S13 split into three applies, §4 text corrected. Adding the gate inside the Terraform Apply workflow is left as a follow-up (needs DB access from that workflow) | §4, S13 |
| B7 | S14 has no "nothing uses `sg-app`" gate | **Accepted.** ENI + Lambda `LastUpdateStatus` gate, PR unmerged until S13 verified, rollback-after-S14 order documented | S14 |
| B8 | `pending:Sx` cells make the probe red between applies | **Accepted.** Cells keyed to live state (`schema_versions` rows, running task def secret) | S2, S18 |
| B9 | ENABLE-without-FORCE checked only once | **Accepted.** Standing CI check + nightly probe cell + lessons/CONTEXT note | S2, S15, S23 |
| B10 | `db_migrator` limit 3 vs overlapping workflows | **Accepted, option 2.** Limit 5 + staggered crons + alarm before S22. One shared concurrency group rejected: GitHub keeps one pending run per group and cancels older pending runs, which could drop a queued apply | S2, S20 |

### Pass C (code review of the S2 / S3 branches, 17/10)

| # | Point | Verdict | Where |
|---|---|---|---|
| C1 | No `catalog.*` view migration can run from S1 until S22 (master not in `catalog_owner`; lint refuses the 225 dance) | **Accepted, option (a) freeze**, enforced by lint + a runner membership check at `check` time; (b)/(c) rejected as default (XD9) | XD9, S3 branch `run_migration.py`, AA-CIS-App `CONTEXT.md`, backlog |
| C2 | S3 static test would turn the planned rl-002 red (`catalog_owner TO db_migrator`) | **Accepted.** Rule scoped by grantee: `aa_app_user` to nobody, `catalog_owner` only to `db_migrator`; the planned rl-002 line is a test case | S3, S20 |
| C3 | `SET LOCAL ROLE cis_app` fails after S22 (`db_migrator` not a member) | **Accepted.** rl-002 grants `cis_app` to `db_migrator`; `owners.yaml` `migrator_member_of` + test that it covers every owner role and `set_local_roles`; runner reach check | S3, S20 |
| C4 | Probe never checks that a runtime role can use its own objects / default privileges | **Accepted.** `runtime_grants.<owner>`, `default_acl.<owner>`, `consumer.contract_grants` cells | S2 |
| C5 | Probe ignores CREATEROLE | **Accepted.** Runtime + owner role cells refuse CREATEROLE, CREATEDB, REPLICATION | S2 |
| C6 | rl-001 rollback (`DROP ROLE`) fails once 243/244 exist | **Accepted.** Prepared `roles/` undo with `DROP OWNED BY` after an ownership guard; dry-run on PG 16 | S3, `s3-undo/` |
| C7 | Ownership cells keyed on registry rows stay red after a planned rollback | **Accepted.** Keyed on transfer key **and** live anchor owner | S2, S6 |
| C8 | `login.cis_app` red between the Console edit and `set-password` | **Accepted, marker option.** `set-password` writes `COMMENT ON ROLE … 'x1:password-set …'`; probe expects the login only then (pending + warning before) | S2, S12, S17 |
