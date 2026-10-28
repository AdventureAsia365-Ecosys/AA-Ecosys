---
id: ARCH-08-scaling
title: "Data platform standards — Part C: Operations and scaling"
description: "Part C of the data standards: connection budget, timeouts, retention mechanics, scale triggers and the job guard for running and growing the shared RDS."
type: reference
status: active
owner: nghiep
audience: [engineer, devops, cto, cio, agent]
applies_to: [ecosystem, aa-cis-dev-db]
last_reviewed: 2026-10-28
review_every_days: 90
related: [ARCH-08, ARCH-08-engineering, ARCH-08-data-management, ARCH-08-schema-ownership]
---

# Data platform standards — Part C: Operations and scaling

**Purpose:** binding rules for running, monitoring and growing the shared PostgreSQL 15 RDS
(`aa-cis-dev-db`, acc2, us-west-1; account IDs: the account map in [onboarding](../../onboarding.md)) that
AA-CIS-App, AA-TripPlanner-Web, AA-Booking and AA-Partner (the partner CRM) share, so that one app's load never
takes the other apps down and every scale step is taken on a measured trigger, not a guess.

**Status:** Accepted with the S237 data-architecture review
([`docs/audits/2026-10-14-S237-lane-backlog/data-architecture/README.md`](../../audits/2026-10-14-S237-lane-backlog/data-architecture/README.md),
"the review"; the tech lead approved every recommendation, 15/10/2026). Version 1.6 (28/10/2026, S255; changes in the README changelog), part of the rule body
of [ADR 0008](../../adr/0008-new-app-integration-and-data-platform-rules.md) (new-app integration and
data platform rules, accepted 15/10/2026); index and golden rules in [`README.md`](README.md). Roadmap
ids (N1..N7, X1..X10, L1..L10) are the review's section 7.

**Keywords:** MUST / MUST NOT = binding; SHOULD = default, deviation needs a written reason in the
PR; MAY = allowed. Every rule says **why** (one line) and **how it is enforced**. "To build (id)"
means the enforcement does not exist yet and is delivered by that roadmap item.

**Precedence:** an accepted ADR wins over this file; Part B
([`02-data-management.md`](02-data-management.md)) is the single registry for retention windows
(DM-7), roles and grants (DM-8) and backup/DR targets (DM-9); Part A
([`01-engineering.md`](01-engineering.md)) owns migration mechanics (MIG-*, incl. runner defaults
and index builds). This part is the single home of pool sizes, connection limits, timeouts and alarm
thresholds; it adds the operational and scaling rules and links to the other parts instead of
repeating their values. A conflict is fixed by PR and
reported to the tech lead, never ignored.

## Contents

- [C1. SLOs and SLIs](#c1-slos-and-slis)
- [C2. Capacity model and connection budget](#c2-capacity-model-and-connection-budget)
- [C3. Thresholds and triggers](#c3-thresholds-and-triggers)
- [C4. Monitoring and alerting baseline](#c4-monitoring-and-alerting-baseline)
- [C5. Maintenance](#c5-maintenance)
- [C6. Job runner scaling](#c6-job-runner-scaling)
- [C7. Environments (Dev now, prod blueprint)](#c7-environments-dev-now-prod-blueprint)
- [C8. Capacity review cadence](#c8-capacity-review-cadence)
- [C9. Scale-up runbook outline](#c9-scale-up-runbook-outline)
- [Appendix: facts this part relies on](#appendix-facts-this-part-relies-on)

---

## C1. SLOs and SLIs

Dev objectives are **targets that trigger work**, not paging promises. They become prod SLOs
unchanged unless the prod ADR (L9) says otherwise.

### C1.1 Measurement rules

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C1.1a | Every pool MUST set `application_name` (`cis-api`, `cis-worker`, `cis-tenant`, `cis-job`, `tp-browse`, `tp-assembly`, `booking-api`, `crm-api`, `db-migrate`). A new app adds `<app>-<process>`. One-off connections are named too: CIS `get_database_url()` appends `cis-direct` (an explicit pool name wins; AA-838 D9), and S3-mediated ECS-exec scripts pass `server_settings={"application_name": "cis-exec"}` (asyncpg ignores `PGAPPNAME`). | Without it, `pg_stat_activity` and Performance Insights cannot attribute load to an app. | Review checklist; to build (N3): a nightly check in the N1 dump that flags sessions with an empty `application_name`. |
| C1.1b | DB latency SLIs MUST be read from Performance Insights (sliced by `db.application.name`) when enabled, else from `pg_stat_statements` (sliced by role). p95 from `pg_stat_statements` is approximated as `mean_exec_time + 2 × stddev_exec_time`. | `pg_stat_statements` groups by role, not by `application_name`, and has no percentiles. | Capacity review (C8). |
| C1.1c | Per-app attribution by role is exact since the role split (X1, 19/10/2026): `cis_app` carries the CIS API, the CIS worker and ECS exec scripts; `db_migrator` carries DB Migrate, the schema dump and the isolation probe; `tripplanner`, `booking`, `crm_app` and `aa_app_user` are separate. Split CIS API from worker load by `application_name`. | Reports must not blame CIS for Migrate or ECS exec load. | Capacity review (C8). |
| C1.1d | Apps SHOULD log DB time per request (`db_ms`) in their structured logs. | App-side p95 includes pool wait, which the DB cannot see. | To build (N3). |

### C1.2 Objectives

| App | SLI (key query or signal) | Dev objective | Source |
|---|---|---|---|
| CIS | Tenant API reads (`/v1/*` on `acp_shared.*`, `gold_aa_internal.tenant_tour_versions`, `catalog.*`): DB time p95 | < 150 ms | PI / `pg_stat_statements` (role `cis_app`; `aa_app_user` for canary routes) |
| CIS | Admin list and cost pages (`shared.v_tenant_monthly_usage`, `llm_call_log` aggregates, job list): p95 | < 1 s (after N4a sargable rewrite) | same |
| CIS | Job claim (`shared/jobs/queue.py` claim under `pg_advisory_xact_lock(650001)`): mean | < 20 ms | `pg_stat_statements` |
| TripPlanner | Browse reads (`catalog.v_tour`, `v_tour_day`, `v_destination`, photo views): DB time p95 | < 300 ms | PI / role `tripplanner` |
| TripPlanner | Assembly reads + `tripplanner.outbox` insert: p95 | < 500 ms | same |
| Booking | API reads/writes (`booking.trip_cases`, `booking.customers`): p95 | < 100 ms | PI / role `booking` |
| Booking | `bk_inquiry_pull` batch (read `tripplanner.v_inquiry_outbox` → insert `booking.inbox_events`): duration | < 2 s per batch; inquiry lag p95 < 5 min | `booking.job` rows |
| All | DB error rate (connection refused, `too many connections`, statement timeout, deadlock, serialization failure) | < 0.5 % of requests per app per day; **0** `too many connections` | CloudWatch log export (`postgresql`), app logs |
| All | Connection saturation: `DatabaseConnections` p95 | < 60 % of `max_connections`; each role < 80 % of its `CONNECTION LIMIT` | CloudWatch; `pg_stat_activity` in the N1 dump |
| All | Replication | **None yet** (no replica, single-AZ). RPO = PITR window (restorable to within ~5 min); RTO = measured in the X10 restore drill, target < 1 h on Dev | AWS RDS; X10 record |

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C1.2a | An objective missed in **two consecutive weekly checks** MUST be raised to the tech lead with the offending query and a proposed fix (ask before creating a Linear issue). | One bad week during a wave is noise; two is a trend. | Capacity review (C8) and weekly `pg_stat_statements` check (C4.3). |
| C1.2b | A new primary-path query SHOULD state its expected p95 and index in the PR when it touches a table > 100k rows. | Most regressions are a missing index on a growing ledger. | Review checklist. |

---

## C2. Capacity model and connection budget

### C2.1 Model

`worst case = Σ over pools (pool max_size × max concurrent processes)`, counting ECS autoscaling
max, rolling-deploy overlap (ECS starts the new task before stopping the old one) and Lambda
concurrency. Ceiling = **75 % of `max_connections`**; the rest is headroom for ops, RDS internals and
`superuser_reserved_connections`.

Deploy overlap: the CIS API service runs with `deployment_maximum_percent = 200`
(`modules/ecs/main.tf:348`), so a deploy taken while autoscaling is at its max can briefly double
the API tasks. The table below counts autoscaling max once; the per-role `CONNECTION LIMIT` is the
backstop that makes such an overflow fail on the new tasks (health check, rollback) instead of on
the instance. TP Lambda deploys behave the same way: frozen environments of the old version keep
their connection until Lambda reclaims them (see C2.3h).

Approximate `max_connections` by class (RDS default `LEAST(DBInstanceClassMemory/9531392, 5000)`;
always confirm with `SHOW max_connections` after a resize):

| Class | RAM | `max_connections` (approx.) | 75 % ceiling |
|---|---|---|---|
| db.t3.micro (until 15/10/2026) | 1 GiB | ~85 (review: 80-110) | ~64 |
| db.t4g.small (today, since 15/10/2026) | 2 GiB | **181** (measured 16/10/2026, AA-832; 3 superuser-reserved) | **~135** |
| db.t4g.medium | 4 GiB | ~400 | ~300 |
| db.m7g.large | 8 GiB | ~850 | ~640 |

Before the resize (code and Terraform as of 15/10/2026) the worst case was ~235 against ~85: CIS API 10 tasks ×
(10 main + 5 tenant), worker 3 × 10, TripPlanner 10 Lambda instances × 5, Booking 5. Only the
account Lambda quota of 10 and `desired_count = 1` hid it. The current budget is C2.2.

### C2.2 Budget (target, on db.t4g.small)

**Re-checked 16/10/2026 (AA-832)** against the measured `max_connections` = 181 (75 % ceiling ≈ 135): the target total below (~136) sits at the ceiling, so any pool increase needs an offsetting cut (AA-859 sizing: tenant pool 2/task with api `max_capacity` 7). Live `CONNECTION LIMIT`s: `tripplanner` 30, `booking` **15** (migration 234; the row below still shows the target 10), `aa_app_user` 15. Per-role usage is now a CloudWatch metric (`AA/RDS RoleConnections` / `RoleConnectionLimitPct`, every 5 min).

**Re-checked 28/10/2026 (AA-838, first capacity review):** TripPlanner reserved concurrency is **15 / 5** in live Terraform (browse / assembly), not 10 / 10; the `tripplanner` role total is still 20 of its limit 30 and the target total is **133** (≤ 135). With today's `cis-api` pool of 10 the worst case is 168 (`cis_app` 100 of 90), carried as `accepted_overages` in AA-CIS-Infra `db/connection_budget.json` until 15/12/2026; measured instance peak 30 (review: [`docs/audits/2026-10-28-S255-aa838-capacity/`](../../audits/2026-10-28-S255-aa838-capacity/README.md)).

**Re-checked 28/10/2026 (S256, AA-838 decision D2, tech lead approved):** the `cis-api` main pool **stays 10**: its `aa859_main_pool_gauge` baseline (16–28/10, acquire waits ≥ 50 ms with the in-use count) shows one task at 5–10 connections in use about ten times a day on ordinary admin traffic and the full 10 in the AA-859 burst, so a pool of 5 would queue those and time a burst out. The budget is met with the process count instead: api `max_capacity` **7 → 3** (autoscaling never went above 3 tasks since late September). Worst case **120 of 135**, `cis_app` 60 of 90, `aa_app_user` 6 of 15; the two `accepted_overages` are removed (AA-CIS-Infra `db/connection_budget.json`, `check_connection_budget.py --verify-sources` clean). Raising `max_capacity` again needs an offsetting cut (C2.3c).

| Pool (`application_name`) | DB role (live since X1, 19/10/2026) | Pool `max_size` | Max processes | Worst case | `CONNECTION LIMIT` | Statement timeout (pool-level, C2.3f) | Lock timeout (pool-level) |
|---|---|---|---|---|---|---|---|
| `cis-api` (main) | `cis_app` (X1 S18; was `aa_cis_admin`) | **10** (`api/main.py`; kept from the `aa859_main_pool_gauge` baseline, AA-838 D2) | **3** (`modules/ecs/main.tf` `max_capacity`: 10 → 7 in AA-CIS-Infra #156, AA-859; 7 → 3, AA-838 D2) | 30 | `cis_app` **90** (shared with worker and the per-job pools; `rl-001`) | 30 s | 5 s |
| `cis-tenant` | `aa_app_user` | **2** (`aa544_tenant_pool.py` `TENANT_POOL_MAX_SIZE`, AA-859 PR-S #774, 16/10/2026; sized as `floor(15 / 7)` when the api max was 7) | 3 | 6 | **15** (25 when AA-544 Stage 2 widens) | 15 s (also the role backstop) | 5 s |
| `cis-worker` | `cis_app` (X1 S18) | `max(5, max_parallel + 2)` = 10 (`shared/jobs/worker.py:323`, default `max_parallel` 8) | 3 (`worker_max_count`) | 30 | in `cis_app` 90 | none at pool level; per job kind | per job kind (`SET LOCAL`) |
| `tp-browse` | `tripplanner` | **1** (today 5, `backend/shared/db.py:60`) | reserved concurrency **15** (`tripplanner_browse_reserved_concurrency`, `accounts/aa365/tripplanner_variables.tf`) | 15 | **30** (both TP pools + 10 for backfills and Lambda deploy overlap) | 10 s (Lambda timeout 30 s) | 3 s |
| `tp-assembly` | `tripplanner` | **1** | reserved concurrency **5** (`tripplanner_lambda_reserved_concurrency`) | 5 | (in 30) | 20 s (Lambda timeout 60 s; also the role backstop) | 5 s |
| `booking-api` (+ in-process `booking.job` worker) | `booking` | 5 (`backend/app/db.py:54`) | 2 (1 task + deploy overlap, `booking.tf` `deployment_maximum_percent = 200`) | 10 | **10** | 15 s (also the role backstop) | 5 s |
| `crm-api` (+ in-process `crm.job` worker; AA-Partner) | `crm_app` (Infra `roles/` file rl-003, C2.3a; v1.3, AA-929) | **3** (`api/app/db.py`) | 2 (1 task + deploy overlap) | 6 | **6** | none at pool level yet (only `command_timeout`; C2.3f gap) | none at pool level yet |
| `db-migrate`, DB Schema Dump, DB Isolation Probe | `db_migrator` (X1 S22) | 1 | 3 (three workflow concurrency groups can overlap) | 3 | `db_migrator` **5** (`rl-002`) | 15 min (N5 runner default, set per session) | 5 s (MIG-9 runner default) |
| ECS exec scripts (S3-mediated, container `DATABASE_URL`, `application_name` `cis-exec`) | `cis_app` | — | — | (inside the 90) | (in `cis_app` 90) | per session | per session |
| `roles/` files, DB Migrate `set-password` / `run-script`, DB Tour Liveness Gate (nightly READ_ONLY run-script, seconds), break-glass | `aa_cis_admin` (master; its DSN is read only inside the migrator task, or for break-glass) | — | — | 10 (reserve) | none (break-glass, C2.3b) | per session | per session |
| RDS internal + `superuser_reserved_connections` | `rdsadmin` | — | — | ~5 | — | — | — |
| **Total** | | | | **120** (api 30 + tenant 6 + worker 30 + TP 15 + 5 + Booking 10 + CRM 6 + `db_migrator` 3 + master reserve 10 + `rdsadmin` 5; AA-838 D2, 28/10/2026) | | ≤ 135 ceiling (75 % of 181) | |

The partner CRM's NOLOGIN roles (`crm_owner`, `crm_ai_reader`, `crm_insights`, `crm_support_reader`, `crm_eraser`) open no connection: `crm_app` reaches them with `SET LOCAL ROLE` inside its own sessions. With limit 6 and pool 3 the total stays under the ceiling; a larger CRM pool needs an offsetting cut or the next trigger row (C3).

`cis_app` connection sites besides the two pools (X1 S15 inventory, XD6; AA-CIS-App
`docs/implementation-notes/AA-860-S15.md`): per-job pools `cis-job` (export / recompute 5, S1 Jev gates 4,
grounding 2 per in-flight rewrite), the eval pool 2 (eval workflow only) and short-lived ad-hoc `asyncpg.connect`
calls. Theoretical worst case per api + worker task set ≈ 63 (× 2 during a deploy overlap); measured instance-wide
`DatabaseConnections` daily max 28 (05–18/10/2026). The limit stays 90 (S15c); 53300 on `cis_app` is a CloudWatch log
alarm (S18) next to `RoleConnectionLimitPct` > 80 %. Raise it only by an Infra `roles/` file, never a CIS migration.

### C2.3 Rules

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C2.3a | Every LOGIN role except the RDS master MUST have a `CONNECTION LIMIT`, set by `ALTER ROLE` in a reviewed SQL file in git, never by hand. Home: the X1 role bootstrap, AA-CIS-Infra `db/migrations/roles/` (with `db_migrator`, `cis_app`, `crm_app` and every new `<app>_app`). Before X1, N3 set the limits of `tripplanner`, `booking` and `aa_app_user` in **one CIS migration** (234) applied through D8 (CIS created `aa_app_user` in `007b_create_app_user.sql`, and DB Migrate then ran as the master, which has CREATEROLE), with the TP and Booking owners approving their rows in that PR. That was the single exception to Part A MIG-6 ("no `ALTER ROLE` in an owner migration"). Booking files MUST NOT carry it: Booking's own guard rejects `ALTER ROLE` (`AA-Booking/backend/tests/migration_guard.py`, rule `no-alter-role`). | A per-role cap turns one app's burst into its own connection errors instead of an instance-wide outage; role attributes are instance-level, not schema DDL. | Exists (N3, X1): every LOGIN role except the master has a limit (schema reference *Roles*); to build (X2): a catalogue rule that flags a LOGIN role with `rolconnlimit = -1` other than the master. |
| C2.3b | `aa_cis_admin` MUST NOT get a `CONNECTION LIMIT` or a role-level `statement_timeout`. | It is the only break-glass login (before X1 it was also the DB Migrate and worker role); a cap or a short timeout could lock out the rescue session or kill a long `run-script` or `roles/` session. | Review checklist. |
| C2.3c | For every pool whose role has a `CONNECTION LIMIT`, the sum of `max_size × max processes` over the role's pools MUST be ≤ that limit, and the C2.2 total MUST be ≤ 75 % of `max_connections`. Any PR that changes a pool size, ECS `max_capacity` / `worker_max_count`, `JOB_WORKER_MAX_PARALLEL`, Lambda reserved concurrency or the instance class MUST update the C2.2 table in the same PR (or a linked root PR). | The budget is only true if every input is changed together. | Review checklist; CI: AA-CIS-Infra `connection-budget.yml` (`db/check_connection_budget.py` reads the Terraform values and `db/connection_budget.json`, checks each pool `max_size` in the owner app, and fails on an over-budget sum). |
| C2.3d | Lambda pools MUST use `max_size = 1` per instance. | One Lambda instance serves one request at a time; extra connections are idle waste multiplied by concurrency. | Review checklist (TP `backend/shared/db.py`). |
| C2.3e | `CONNECTION LIMIT` on `tripplanner` and TP pool max 1 MUST be merged **and applied** before the Lambda quota increase to 1000 takes effect. `reserved_concurrent_executions` on `aws_lambda_function.tripplanner_browse` / `tripplanner_assembly` (`accounts/aa365/tripplanner.tf`) MUST be merged as a variable that stays unset while the quota is 10 and is set to 10 in the first Terraform apply after the quota lands, before any load test. | AWS keeps at least 100 unreserved concurrency, so a reservation fails on a quota of 10; Terraform Apply is one manual workflow over all of `accounts/aa365`, so a hard-coded reservation on `main` would break every unrelated apply. S236 already saw 1,591 throttles on `/plan` tiles; without caps the quota raise converts throttles into a DB outage for every app on the instance. | Approved decision E6; review checklist on the quota case; N3. |
| C2.3f | Every pool MUST set its own `statement_timeout` (asyncpg `server_settings`) below its caller's timeout (table C2.2). A role-level `ALTER ROLE … SET statement_timeout` is only a backstop, set to the **largest** pool value of that role, and only on single-purpose roles (`aa_app_user`, `tripplanner`, `booking`, `crm_app`, `db_migrator` with the runner override). `idle_in_transaction_session_timeout = 60s` is set in the parameter group; before it is enabled, a week of N1 `pg_stat_activity` samples MUST show no app session idle in transaction for > 60 s (a job handler holding a transaction across an LLM call would be killed). | A runaway query must die before the Lambda or HTTP caller gives up and retries on a new connection; shared roles (`cis_app` for API + worker, `tripplanner` for browse + assembly) cannot carry two role-level values. | Parameter group: exists (C4.2a). Role-level backstops: not set yet (the schema reference *Roles* table shows no role settings). Pool settings: review checklist on pool creation. |
| C2.3g | Pools MUST fail fast on exhaustion (bounded acquire timeout, ≤ 5 s) and MUST NOT fall back to another role's pool. A missing or exhausted tenant pool gives 503. The CIS tenant-pool flags fail closed globally (S241 D-12, CIS #792): an unreadable or missing flag means the tenant pool; only an explicit `"false"` moves that one route to the admin pool. Rollback path (DM-8.4): `SET <flag key> false` in Redis for one route, or the emergency task-definition variable `TENANT_POOL_FORCE_ADMIN_FLAGS` (survives a Redis restart; needs a redeploy). New apps fail closed from day one. | Silent fallback to the master pool hides saturation and breaks isolation (review P2). | Review checklist; CIS `aa544_tenant_pool.py` (fail closed since D-12). |
| C2.3h | The `tripplanner` role SHOULD set `idle_session_timeout` (PostgreSQL 14+, start 10 min) so connections held by frozen or retired Lambda environments are reaped; the TP pool MUST tolerate a server-closed connection (retry the acquire once). Verify on Dev with a thawed Lambda before enabling. | Frozen environments keep their connection open, and after a TP deploy the old version's environments still count against the `CONNECTION LIMIT`. | To build (N3); TP smoke after the change. |

---

## C3. Thresholds and triggers

Each action happens **only** when its trigger fires (measured, written down in the capacity review),
except rows marked **Now** (approved for immediate delivery).

| Area | Action | Trigger (metric and threshold) | Roadmap | Approx. cost |
|---|---|---|---|---|
| Guardrails | Storage autoscaling (`max_allocated_storage = 100`), custom parameter group, `pg_stat_statements`, log export, final snapshot, alarms (C4), `application_name`, connection budget (C2) | **Now** (before the Lambda quota) | N3 | $0 |
| Instance: t3.micro → **t4g.small** + Performance Insights | Resize in Terraform (C9.1) | **Now** (approved). If PI is not supported on t4g.small (check `terraform plan`), PI becomes a trigger for t4g.medium | X9 | ~+$10-15/mo |
| Instance: t4g.small → **t4g.medium** | Resize (C9.1) | Any of: `CPUUtilization` above the T baseline (20 %) for > 50 % of hours in a week; `CPUSurplusCreditsCharged` > ~$10/mo; `FreeableMemory` < 300 MB for > 1 h/day on 3 days of a week; C2.2 total > 75 % of `max_connections` | — | ~2x small |
| Instance: t4g.medium → **m7g.large** | Leave burstable class (C9.1) | Any of: CPU above baseline most of a week (credits charged > ~30 % of instance price); > 5 primary-path statements with mean > 200 ms in `pg_stat_statements`; before prod (prod starts on Multi-AZ t4g.medium, C7.2) | — | — |
| Instance: m7g → **r7g** | Memory-optimised class | Working set > ~70 % of RAM: buffer cache hit ratio (`pg_stat_database` `blks_hit / (blks_hit + blks_read)`) < 99 % on the hot tables for a week, `ReadIOPS` rising with flat traffic, `FreeableMemory` < 10 % of RAM | — | — |
| Storage | Raise `max_allocated_storage` | Used storage > 80 % of `max_allocated_storage`, or growth > 1 GB/day for a week | — | gp3 per GB |
| Retention | TTL job kinds + rollups + S3 Parquet archive (C5.4) | **Now** (approved). Hard stop if a log table **without a retention job kind** passes 1M rows, or `FreeStorageSpace` < 10 GB before its retention lands. A ledger whose retention kind exists (CIS AA-825, Booking, CRM) is watched by the Partitioning row instead: with a 180-day window it legitimately holds several million rows (AA-838 D3) | N4 | $0 + S3 cents |
| Connection pooling | **RDS Proxy** in front of the TP Lambdas (IAM auth); test pinning with asyncpg prepared statements and `set_config(..., true)`; watch `DatabaseConnectionsCurrentlySessionPinned` | Any of: Lambda concurrency need > 20 (reserved concurrency raised above 10 per function); `DatabaseConnections` p95 > 60 % of `max_connections` for a week; before prod | L7 | ~$20-25/mo |
| Catalog latency | **Materialized catalog read model**: tables behind the heavy `catalog.*` views, refreshed by a CIS `catalog_refresh` job kind on publish / geo build, with `refreshed_at` exposed | A `catalog.*` view p95 > 500 ms (C1.1b approximation, or PI), or TP browse fully cut over to `catalog.*` (X4) | L4 | $0 |
| Read scaling | **Read replica** | Read-dominated DB load > 30 % of primary CPU (PI by SQL type), or primary CPU > 60 % sustained with reads dominating, **after** L4 and query tuning | — | ~instance cost |
| Table size | **Partitioning** with pg_partman (or native partitions pre-created by a job); convert by CHECK NOT VALID → VALIDATE → ATTACH the old table as one partition | Any of: a table > 10M rows or > 5 GB; a retention DELETE taking > 5 min; `n_dead_tup / n_live_tup` > 20 % after autovacuum. First candidates: `shared.llm_call_log`, `shared.decision_log`, `shared.tenant_api_usage` | L5 | $0, 2-4 days per table |
| Analytics | **S3 Parquet export + Glue + Athena** (bytes-scanned limit); BI never queries the primary | The archive half starts **now** with N4 (archive before delete). Athena/Glue at the first cross-app BI request | N4 (archive), L6 (query) | cents to a few $/mo |
| Event relay | **Outbox → EventBridge → SQS + DLQ** per consumer | The first consumer outside the DB/VPC (HubSpot sync, mobile push), or an event with a 3rd consumer | L8 | small |
| App split | **Booking first** to its own instance: logical replication of the materialized catalog tables (L4), DSN cut-over through a private CNAME (X10) | Any of: Booking p95 > 2x its baseline during CIS waves ≥ 2 times a month; Booking needs its own PITR/RPO; total DB size > 200 GB; `DatabaseConnections` p95 > 70 % | — | ~2x DB cost |
| Prod | Separate instance (C7.2) | A prod go-live date is set | L9 | ~$110-130/mo + storage |

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C3a | A scale action MUST cite the trigger row and the measured value (screenshot or query output) in its PR. | Prevents speculative spend and keeps the threshold table honest. | Review checklist. |
| C3b | Cheaper levers MUST be tried first, in this order: query/index fix → retention → pool budget → materialized read model → instance resize → proxy → replica → split. | Each step costs more money or operational surface than the one before. | Capacity review (C8). |
| C3c | Cost figures are rough us-west-1 estimates and MUST be checked in the AWS pricing calculator before the spend is approved by the tech lead. | Review 7 ("dropped or downgraded"). | Review checklist. |

---

## C4. Monitoring and alerting baseline

### C4.1 CloudWatch alarms (in `accounts/aa365/observability_ecosys.tf`, all to `aws_sns_topic.alerts` defined in `accounts/aa365/observability.tf`)

CIS has no recurring job scheduler today (Booking has recurring kinds in its worker). Every
"nightly" or "custom metric" item in this part (N1 dump, per-role connection metric, retention
kinds, backlog age) is triggered by an EventBridge Scheduler rule that only **enqueues** a job
(ADR 0003 decision 5; existing pattern `accounts/aa365/dfs_balance.tf` `aws_scheduler_schedule`).
Built for the per-role metric (AA-832). CIS daily kinds (retention, photo sync, staff reconcile) are enqueued through
admin schedule endpoints such as `POST /admin/job-runner/retention/schedule` (AA-825), which only enqueue; the N1
dump runs as a nightly GitHub Actions workflow instead (DB Schema Dump). Publishing a custom metric needs `cloudwatch:PutMetricData` on the CIS
task role (shared by api and worker), scoped by `cloudwatch:namespace`, added in the same Infra PR.

| Alarm | Threshold | Status |
|---|---|---|
| `rds-connections-high` (`DatabaseConnections`) | > 60 for 5 min on t3.micro; after a resize, 60 % of `max_connections` for 5 min | **Exists**: > 108 (60 % of 181) for 5 min, `local.rds_max_connections` (AA-832, Infra #155) |
| `rds-free-storage-low` (`FreeStorageSpace`) | < 50 % of allocated storage | **Exists** (AA-824, Infra #121) |
| `FreeableMemory` | < 100 MB (t3.micro), < 200 MB (t4g.small), < 10 % of RAM (larger) | **Exists**: < 200 MiB for 10 min (AA-824 #121, raised by AA-832 #155; live floor 523 MB) |
| `CPUUtilization` | > 80 % for 15 min | **Exists** (#121; `notBreaching` since #155) |
| `CPUSurplusCreditsCharged` | > 0 (T-class runs Unlimited, so the symptom is cost) | **Exists** (AA-824, #121) |
| `ReadLatency` / `WriteLatency` | > 20 ms for 15 min | **Exists** (AA-832, Infra #155) |
| `DiskQueueDepth` | > 10 for 15 min | **Exists** (AA-832, Infra #155) |
| `MaximumUsedTransactionIDs` | > 1,000,000,000 | **Exists** (AA-832, Infra #155) — wraparound guard |
| Per-role connections | > 80 % of `CONNECTION LIMIT` | **Exists** (AA-832): CIS job `ops_rds_role_connections` (CIS #771) every 5 min → `AA/RDS RoleConnectionLimitPct{Role}`, one alarm per limited role, 1 of 2 periods (Infra #155). SNS fire + recover tested 16/10/2026 |
| Per-role sampling stopped | no `RoleConnections` sample for 45 min | **Exists** (AA-832, Infra #155). The one alarm that treats missing data as **breaching** (exception to C4.1a): its job is to notice missing data |
| Job backlog age, per owner (`shared.job`, `booking.job`, later `<schema>.job`) | oldest **claimable** `queued` row (due: `run_after <= now()`, by `run_after`) > 15 min, capacity-aware (CIS: starved while workers are full; Booking: 0 while a healthy job of the owner runs), or any `running` past 2 × the kind's `expected_seconds` (a registry attribute, not a column, so the owner's app computes it) | **Exists** (AA-751): in-process samplers every 5 min, CIS `api/ops_metrics_sampler` (CIS #786) → `AA/Jobs/CIS`, Booking `JobMetricsSampler` (Booking #26) → `AA/Jobs/Booking`; alarms `aa-<owner>-dev-jobs-queue-age` / `-overdue-running` / `-sampling-stopped` (Infra #160). Fired and recovered: CIS 16/10 (S240), Booking 17/10 (S241). |
| Existing app alarms (Lambda errors/throttles, Booking health/5xx/CPU, NAT status) | as defined | Keep |

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C4.1a | Every alarm in C4.1 MUST exist in Terraform (no console-only alarms) and treat missing data as not breaching. | Dev is stopped on purpose at times; console alarms drift. | Review checklist on `observability_ecosys.tf`. |
| C4.1b | An alarm threshold tied to `max_connections` or RAM MUST be updated in the same PR as an instance resize. | A stale absolute threshold silently stops protecting. | C9.1 runbook step; review checklist. |

### C4.2 Logs

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C4.2a | The parameter group MUST set `log_min_duration_statement = 500ms`, `log_lock_waits = on`, `track_io_timing = on`, `rds.force_ssl = 1`, and preload `pg_stat_statements` with `pg_stat_statements.max = 10000` (static, applied at a planned reboot; 5,000 filled in three weeks with 1,466 deallocations, AA-838 D13) (`CREATE EXTENSION` in a CIS migration; extensions are instance-level and only CIS migrations create them, like `vector` and `pgcrypto` today). Before `rds.force_ssl = 1` is applied, `pg_stat_ssl` joined to `pg_stat_activity` MUST show `ssl = true` for every app session (Booking enforces `DB_SSL=require`; CIS and TP rely on the asyncpg default). | Slow-query and lock-wait evidence must exist before an incident, not after; a non-TLS client would be cut off by the flip. | Exists (v1.1): parameter group `aa-cis-dev-pg15` in `infra/AA-CIS-Infra/modules/rds/main.tf` (AA-824; also `log_connections`/`log_disconnections` per D-08, `log_parameter_max_length = 0`, `idle_in_transaction_session_timeout`); extension by CIS 234. |
| C4.2b | `enabled_cloudwatch_logs_exports = ["postgresql"]` with **365-day** retention (security/audit class: connection logs, S241 D-09, AA-872; Part B §7). | Logs survive instance events and are searchable for a year. | Exists (v1.1): `modules/rds/main.tf` (`log_retention_days` default 365); live log group checked 19/10/2026. |
| C4.2c | Logs MUST NOT contain PII or secrets: no `log_statement = all`, no parameter logging on PII tables. | `booking.customers` and inbox payloads are personal data. | Review checklist on the parameter group. |

### C4.3 Review cadence

| Check | Cadence | Output |
|---|---|---|
| `pg_stat_statements` top 20 by `total_exec_time` and by `mean_exec_time`, per role | Weekly (and after every wave) | Note in the session log; regressions to the tech lead (C1.2a) |
| Slow-query log (> 500 ms) and lock waits | Weekly | Same |
| Performance Insights top SQL / wait events by `db.application.name` | Weekly once PI is on | Same |
| Table/index sizes, `pg_stat_user_tables` activity, dead tuples | Nightly in the N1 dump; read monthly | Capacity review (C8) |

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C4.3a | `pg_stat_statements_reset()` MAY be run only right after a capacity review, and only after the top-50 snapshot is saved under the review folder. | A reset destroys the history the trend depends on. | C8 checklist. |

---

## C5. Maintenance

### C5.1 Autovacuum

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C5.1a | Instance-level autovacuum SHOULD stay at RDS defaults; tuning is per table through `ALTER TABLE … SET (autovacuum_…)` in the **owner's** migration. | Per-table tuning is reviewable and owner-scoped; global changes hit every app on the instance. | Review checklist; schema-ownership rule 1. |
| C5.1b | High-churn queue tables (`shared.job`: a heartbeat UPDATE every 20 s per running job, `shared/jobs/worker.py:71`; `booking.job`: every `lease_seconds / 3` = 100 s plus a claim poll per tick) MUST use `autovacuum_vacuum_scale_factor = 0.02` (or lower) and `autovacuum_vacuum_threshold = 50`. *Amended S241 (AA-751, F17):* the earlier "~1000" threshold would vacuum **later** than the default (50 + 0.2 N) below ~5,300 rows, and with retention both job tables stay at a few thousand rows; 0.02 / 50 is never later than the default at any size. | Default 20 % lets dead tuples pile up on a small hot table and slows the claim query. | **Exists**: job-table DDL template `apps/AA-CIS-App/shared/jobs/job_table_template.sql`; CIS migration 242 (CIS #784), Booking bk-013 (Booking #24); the template comparison test checks `reloptions`. |
| C5.1c | Append-only ledgers (`shared.llm_call_log`, `shared.decision_log`, `shared.tenant_api_usage`, outboxes, inboxes, audit logs) SHOULD set `autovacuum_vacuum_insert_scale_factor = 0.05` and `autovacuum_analyze_scale_factor = 0.02`. | Keeps the visibility map and stats fresh, so index-only scans and plans stay good as they grow. | To build (N4). |
| C5.1d | After a bulk load or a migration that rewrites > 10 % of a table, the migration MUST end with `ANALYZE <table>`. | Stale statistics cause bad plans right after deploy. | Review checklist. |

### C5.2 Bloat and index maintenance

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C5.2a | The N1 nightly dump MUST record per table `n_live_tup`, `n_dead_tup`, `last_autovacuum`, size, and per index `idx_scan` and size. | Bloat and unused indexes are invisible without a time series. | Exists for tables (*Table activity* of the schema reference, N1); to build: per-index `idx_scan` and size. |
| C5.2b | A table with `n_dead_tup / n_live_tup` > 20 % after autovacuum, or an index > 2x its expected size, MUST be listed in the monthly capacity review with a fix (vacuum tuning, `REINDEX CONCURRENTLY`, or partitioning per C3). `pgstattuple_approx` MAY be used for the top 10 tables. | Catches bloat before it becomes a VACUUM FULL temptation. | C8 checklist. |
| C5.2c | `REINDEX` and `CREATE INDEX` on tables > 100k rows MUST use `CONCURRENTLY` in a `-- migrate: no-transaction` file once N5 ships; what is allowed until then is Part A MIG-10 (one rule, not repeated here). | A plain build takes a lock that blocks writes for every app. | To build (N5: runner no-transaction mode; lint). |
| C5.2d | An index with `idx_scan = 0` for 30 days that is not a PK, UNIQUE or constraint index is a drop candidate; it is dropped through expand/contract (review 5.3), never in the same PR that finds it. | Unused indexes cost write amplification and disk, but a 30-day window can miss monthly jobs. | C8 checklist; DRY RUN per `skill/aa-cis-schema/references/destructive-ops.md`. |
| C5.2e | Every FK column and every column used in a retention predicate MUST be indexed: `shared.llm_call_log.created_at` (it has no `called_at`), `shared.decision_log.created_at`, `shared.tenant_api_usage.called_at`, `shared.job.finished_at` / `booking.job.finished_at`, `tripplanner.outbox.created_at`, `booking.inbox_events.received_at`. A retention column MUST be `NOT NULL` before its TTL job ships (`tenant_api_usage.called_at` is nullable today: backfill, then `SET NOT NULL` in the owner's migration). | Retention DELETEs and FK checks otherwise seq-scan the ledger; a NULL timestamp never ages out. | Review checklist; to build (N4; X2 catalogue guard can check FK indexes). The `finished_at` index on `shared.job` / `booking.job` exists (CIS 242, bk-013; AA-751). |
| C5.2f | Time-range filters on ledgers MUST be sargable: a range on the raw column (`called_at >= $1 AND called_at < $2`), never `date_trunc(...) = ...`. N4a rewrites `shared.v_tenant_monthly_usage` (`223_tenant_usage_real_llm_cost.sql:100,111,129`) and adds `(tenant_id, called_at)` on `shared.tenant_api_usage`; history pages read the rollups (DM-7.4). | A function on the column defeats the index, so admin cost and usage pages get slower every day (review P5). | Review checklist; weekly `pg_stat_statements` check (C4.3). |
| C5.2g | DDL on a hot table (`shared.job`, `booking.job`, the ledgers in C5.1c, `catalog.*` base tables) MUST run with the runner's `lock_timeout` (Part A MIG-9) outside a wave, and is retried rather than given a longer lock timeout. | An ALTER queued behind a job transaction blocks every reader of that table, for every app on the instance (review P9). | To build (N5 runner defaults); C6.3b idle check. |

### C5.3 Never VACUUM FULL on hot tables

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C5.3a | `VACUUM FULL`, `CLUSTER` and plain `REINDEX` (non-concurrent) MUST NOT run on a table any app reads or writes on a request or job path. | They take ACCESS EXCLUSIVE locks; on one shared instance that is an outage for every app. | To build (N5 lint: reject these statements in migration files without a `-- migrate: destructive` header and a named approval). |
| C5.3b | To reclaim space, use (in order) retention DELETE + regular vacuum, `REINDEX CONCURRENTLY`, partition-and-drop (L5). `pg_repack` MAY be considered only with the tech lead's approval; it is not set up in the repo. | Reclaiming disk is rarely urgent once storage autoscaling is on. | Review checklist. |

### C5.4 Retention and batched deletes

The windows (approved decision E3: `llm_call_log` raw 180 d + daily rollup,
`tenant_api_usage` 90 d + monthly rollup, jobs succeeded 30 d / failed 90 d, outbox/inbox payload PII redacted after 90 d,
archive to S3 Parquet before delete) and the per-table "archive before delete" choice live **only**
in the Part B retention table (DM-7). This section adds how the deletes run on a shared instance.
Existing pruning to keep: `shared.job_worker` (`shared/jobs/queue.py:440`) and Booking's recurring
kinds (`AA-Booking/backend/app/jobs/queue.py` `prune`, succeeded/cancelled rows older than
`keep_days`).

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C5.4a | Where DM-7 says "archive before delete", rows MUST be written to S3 as Parquet (partitioned by table / year / month) first; the job records the object key and row count, and the delete runs only after the count matches. | Approved E3: delete only what is recoverable for audit and cost history. | To build (N4). |
| C5.4b | Retention runs as an **owner-run job kind** in the owner's job table (never a cross-owner script). Approval mechanics are Part B DM-7.2: the first run of each kind and the first run after a window change go through DRY RUN with the tech lead's approval; later runs stop and report when they would touch more than 2x the previous run's count. | Owners delete only their own rows (schema-ownership rule 1); DRY RUN is the destructive-ops procedure. | To build (N4); review checklist. |
| C5.4c | Deletes MUST be batched: ≤ 10,000 rows per transaction, selected by keyset on the indexed retention column (`WHERE created_at < $cutoff AND (created_at, id) > ($last_ts, $last_id) ORDER BY created_at, id LIMIT n`), commit per batch, 100-500 ms pause, `statement_timeout` 30 s per batch, resumable from the last `(ts, id)` stored in the job's `progress`. Never page by `id` alone: `shared.llm_call_log.id` and `shared.tenant_api_usage.id` are random `uuid`s. | A single large DELETE holds locks, bloats WAL and stalls autovacuum on the shared instance; a uuid order scatters the batches across the table. | Review checklist on the job kind. |
| C5.4d | Retention kinds MUST be declared `concurrency=1` and, in CIS, `background=True` (so `BACKGROUND_MAX_RUNNING = 1` keeps them from crowding foreground jobs), are enqueued nightly (C4.1 scheduler note), and are not enqueued while a wave runs (aa-wave-rerun runbook). | Keeps retention I/O off the hot path. | `registry.py` review; runbook. |
| C5.4e | Every new log, event or job table MUST ship with its DM-7 retention row in the same PR (DM-7.1). | Unbounded growth is the default without one (review P5). | Playbook checklist (ADR 0008); review checklist. |

### C5.5 Engine versions

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C5.5a | Minor upgrades MUST go through Terraform (`engine_version`, today `15.17`) in the maintenance window (`mon:04:00-mon:05:00` UTC, `modules/rds/main.tf`), after the job guard (C6.3) shows all job tables idle. | An unplanned restart interrupts every app and running jobs. | Review checklist; aa-ship. |
| C5.5b | A major upgrade MUST first be rehearsed on a restored snapshot (X10 drill path) with every app's smoke checks; plan it before PostgreSQL 15 community end of life (Nov 2027). | Major upgrades change planner and extension behaviour. | Capacity review flags it 6 months ahead. |

---

## C6. Job runner scaling

Current facts: CIS `shared.job` runs on `aa-cis-dev-worker` (`JOB_WORKER_IN_API=false`),
`JOB_WORKER_MAX_PARALLEL` default 8, `BACKGROUND_MAX_RUNNING = 1`, per-kind DB-wide `concurrency`
in `shared/jobs/registry.py`, claims serialized by `pg_advisory_xact_lock(650001)` + `FOR UPDATE
SKIP LOCKED`, autoscaling 1..`worker_max_count` (3) on CPU 70 % / memory 80 %, drain `grace_seconds`
20 s inside an ECS `stopTimeout` of 120 s, lease 90 s. Booking runs its `booking.job` worker inside
the API process when `WORKER_ENABLED` is on: one job at a time, lease 300 s, on shutdown it stops the
loop and waits `WORKER_STOP_TIMEOUT_S` = 20 s (`app/main.py`) inside an ECS `stopTimeout` of 30 s
(`accounts/aa365/booking.tf:293`); an unfinished job is released back to `queued` on shutdown (Booking #25, S240), so it no longer waits for the lease to expire.
AA-Partner runs its `crm.job` worker inside the API process (`aa-crm-dev-api`).

⚠️ The knobs below are underscore env vars (`JOB_WORKER_MAX_PARALLEL`, `WORKER_ENABLED`, …): edit
them manually in VSCode, never through a generated script.

### C6.1 Caps

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C6.1a | Concurrency is bounded at three levels and MUST stay bounded at all three: per-kind DB-wide `concurrency` (heavy kinds such as `a3_atomize` stay 1), per-worker `max_parallel`, and worker task count (`worker_max_count`). | Autoscaling adds tasks; only the per-kind cap bounds DB and LLM load. | `registry.py` review; C2.3c. |
| C6.1b | Raising `max_parallel`, `worker_max_count` or a kind's `concurrency` MUST update the C2.2 budget (worker pool = `max(5, max_parallel + 2)` per task) and, for LLM kinds, respect the paid-run rule (trial ~3, then ≤ ~50 tours). | Each slot is a connection and possibly Bedrock spend. | Review checklist. |
| C6.1c | If job claim mean exceeds 20 ms or worker count needs to exceed ~10, the claim design (single advisory lock) MUST be revisited before adding workers. | One global claim lock serializes every worker. | C1.2 SLI; capacity review. |
| C6.1d | Every owner's job table MUST be created from the shared DDL template ([ADR 0003a](../../adr/0003a-per-owner-job-tables.md): one job table per owner schema, kind prefix per app in `owners.yaml`), including `cancel_requested`, `progress`, `cost_usd`, `parent_job_id`, the retention index on `finished_at`, and the C5.1b autovacuum settings. | One shape means one admin view, one guard and one retention job per owner. | **Exists** (AA-751): template `apps/AA-CIS-App/shared/jobs/job_table_template.sql` + comparator `shared/jobs/job_table_shape.py` (byte copy in Booking, "Job template copy" CI check); `shared.job` (CIS 242) and `booking.job` (bk-013) match it in CI. `tripplanner.job` is created from it with AA-861. |

### C6.2 Drain windows

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C6.2a | A worker MUST stop claiming on SIGTERM, give running handlers `grace_seconds`, then release them to the queue; `grace_seconds` + release MUST stay below the ECS `stopTimeout` (120 s, Fargate max). | A job killed mid-flight without release waits for lease expiry (90 s) and may double-run. | `shared/jobs/worker.py` (`shutdown`); `modules/ecs/main.tf:490`. |
| C6.2b | Job kinds longer than the drain window MUST be resumable (checkpoint in `progress`, idempotent stages). | A deploy or scale-in will interrupt them. | ADR 0003 decisions 1-3 (durable, retryable, versioned swap); review checklist. |
| C6.2c | Booking's in-process worker MUST keep its stop wait below the container `stopTimeout` (today 20 s < 30 s) and each handler one short transaction. An unfinished job MUST be released on shutdown (CIS `queue.release` behaviour). | Booking API restarts on every deploy; without release an interrupted job waits up to the 300 s lease. | Review checklist on `apps/AA-Booking/backend/app/main.py` / `app/jobs/worker.py`; release-on-shutdown **exists** (Booking #25, integration test). |

### C6.3 Deploy guard

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C6.3a | A backend deploy MUST be blocked while (1) a CIS rerun wave is open (`shared.rerun_wave.status = 'open'`; CIS deploys only) or (2) a job of a **deploy-blocking kind** of the deploying owner is `running`, or `queued` and due within 15 minutes (the guard runs before the image build; the old task would claim it before its SIGTERM). Every other `queued` or `running` job MUST NOT block: the worker drains on SIGTERM and releases a job still running (C6.2a/c), and the new revision re-claims it; a queued row is claimed by whichever image is live. A kind is deploy-blocking when a release cannot re-run it safely (C6.2b not met): CIS `deploy_blocking` registry flag (today `data_erasure`, `s1_batch_ingest`), Booking `DEPLOY_BLOCKING_KINDS` (the retention kinds), Partner `DEPLOY_BLOCKING_KINDS` (`crm_dispatch`, until its send marker, AA-993 G4b). Override only by the tech lead with a written reason. | Waves and non-re-runnable jobs must not be split across two images; blocking on every busy queue made deploys wait for work a drain already handles (AA-993 design D1, S252). | AA-993 G5: CIS `deploy-dev.yml` guard → `GET /admin/job-runner/deploy-gate` (`open_waves`, `blocking_running`, `blocking_due`, `blocked_by`); Booking `deploy-dev.yml` preflight (`.github/scripts/booking-deploy-preflight.sh`) → `GET /booking/ops/deploy-gate`, GitHub OIDC token (AA-751); Partner `deploy-dev.yml` preflight → `GET /crm/ci/deploy-gate`. Booking and Partner do not read CIS waves. Proof: AA-993 G5 live checks (queued + running jobs, no wave → passes; open wave → blocks; running retention / `crm_dispatch` row → blocks; a due queued row of a deploy-blocking kind blocks too, unit + integration tests). |
| C6.3b | Instance-level changes (reboot, parameter group, resize, minor upgrade) and DB Migrate `apply` MUST check **all** job tables (`shared.job`, `booking.job`, any `<schema>.job`) are idle and no wave is running. | These affect every app, not just the deploying one. | Runbook C9.1; DB Migrate idle check **exists** (Infra #158, S240): `apply` refuses with exit 7 while any `<schema>.job` has non-exempt queued/running rows (exempt: `bk_inquiry_pull`; override input `override_busy_jobs`, the tech lead only). Instance-level changes: runbook. |

---

## C7. Environments (Dev now, prod blueprint)

### C7.1 Dev (today → target)

| Setting | Today (`modules/rds/main.tf`) | Target | Roadmap |
|---|---|---|---|
| Class | `db.t4g.small` + Performance Insights (v1.1, checked live 19/10/2026) | `db.t4g.small` + PI | X9 (done) |
| Storage | 20 GB gp3, `max_allocated_storage = 100` | `max_allocated_storage = 100` | N3 (done) |
| Multi-AZ | false | false (Dev) | — |
| PITR | 7 days, window 03:00-04:00 UTC | 7 days | — |
| Final snapshot | `skip_final_snapshot = false`, `copy_tags_to_snapshot = true` | `false`, `copy_tags_to_snapshot = true` | N3 (done) |
| Deletion protection | true | true | — |
| Parameter group | custom `aa-cis-dev-pg15` | custom (C4.2a, C2.3f) | N3 (done) |
| Restore drill | done on 17/10/2026 (S241 D-10: PITR, about 22 minutes; evidence `docs/audits/2026-10-17-S241-restore-drill/`) and 24/10/2026 (`docs/audits/2026-10-24-S249-restore-drill/`) | once now, record the RTO; again before prod (DM-9.3) | X10 |
| DSN host | private CNAME `db.dev.internal` in every DSN secret since 23/10/2026 (AA-829, Part B DM-9.5) | private CNAME | X10 (done) |
| Real-data dumps | `docs/backups/2026-09-16` on a laptop | moved to an encrypted private S3 prefix, then removed locally (E10) | X10 |

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C7.1a | Production personal data MUST NOT be copied to Dev; Dev seed data MUST be synthetic or masked. | Dev has weaker controls and public repos describe its schema. | Review checklist; PII tags (`COMMENT 'pii:<class>'`). |
| C7.1b | Dev MAY be stopped to save cost; every alarm treats missing data as not breaching (C4.1a). | Stopping must not page. | Terraform. |

### C7.2 Prod blueprint (L9, built when a go-live date is set)

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C7.2a | Prod MUST be a separate RDS instance in acc2 (ADR 0001 as amended S235; no new account), Multi-AZ, starting at `db.t4g.medium`, gp3 with storage autoscaling. | Isolation from Dev experiments; Multi-AZ gives a 1-2 min failover. | Terraform review. |
| C7.2b | Prod MUST have 14-day PITR, `skip_final_snapshot = false`, `deletion_protection = true`, AWS Backup daily with a **cross-region copy** (region chosen in the prod ADR), and a quarterly restore drill with a recorded RTO; RPO/RTO targets are those of DM-9.6. | Same-region same-account PITR is not DR. | Terraform; drill record in `docs/audits/`. |
| C7.2c | Prod MUST live in its own Terraform root (`infra/AA-CIS-Infra/envs/prod/`, does not exist yet) with its own security group, secrets prefix (`<app>/prod/...`), parameter group and alarms (C4.1 with prod thresholds and a paging route). | A shared root lets a Dev change reach prod. | Terraform review. |
| C7.2d | DB Migrate MUST take an `environment` input (`dev` / `prod`) that selects cluster, task definition, log group and secret; prod applies require the GitHub `prod` environment approval. Today `db-migrate.yml` has the `environment` input with one choice, `dev` (from `db/owners.yaml`), and still runs in the GitHub environment named `prod`. | One workflow must not be able to apply to the wrong database. | Partly built (X1: own migrator task definition, `db_migrator`, the `environment` input); to build (L9 for prod). |
| C7.2e | Prod runtime roles MUST be the split roles from day one (`cis_app`, `bk_owner`/`booking`, `tp_owner`/`tripplanner`, `db_migrator`); `aa_cis_admin` is break-glass only. Prod SHOULD enable Enhanced Monitoring (60 s) and pgaudit for forensics. | Prod must not inherit the Dev master-credential blast radius (review P1). | X1 Done is a prerequisite of L9. |
| C7.2f | Prod DSNs MUST point at a private CNAME, not the RDS endpoint. | A split or restore then needs a DNS change, not a secret rotation in every app. | X10 pattern; Terraform. |

---

## C8. Capacity review cadence

| # | Rule | Why | Enforced by |
|---|---|---|---|
| C8a | A capacity review MUST run **monthly** (and after any wave that doubled a ledger), drafted by an agent, approved by the tech lead, saved to `docs/audits/<date>-S<nnn>-capacity-review/` with a root PR. | Triggers in C3 only work if someone measures them on a schedule. | Session ritual; save-audits rule. |
| C8b | The review MUST cover: (1) CloudWatch 30-day CPU, `FreeableMemory`, `DatabaseConnections` p95/max, storage used and growth per day, IOPS/latency, credits charged; (2) PI / `pg_stat_statements` top 20 per role with C1.2 SLIs; (3) top 20 tables and indexes by size and 30-day growth, dead-tuple ratios, unused indexes (from the N1 dump); (4) ledger row counts vs C5.4 retention; (5) Lambda concurrency peaks and throttles; (6) job backlog and duration per owner; (7) the C2.2 budget recomputed from live Terraform values; (8) every C3 trigger with its measured value (fired / not fired); (9) RDS cost line vs budget. | A fixed checklist makes reviews comparable month to month. | This list is the review template. |
| C8c | The review MUST end with a decision list (no action / tune / scale per C3 with the trigger row cited) and update this file's tables if a value changed. | Keeps the standard and reality in sync. | Review checklist. |

---

## C9. Scale-up runbook outline

Full runbooks are written when first used; each must keep these steps.

### C9.1 Instance resize (any step of t4g.small → t4g.medium → m7g → r7g)

1. **Trigger:** cite the C3 row and the measured value.
2. **Plan:** change `instance_class` in Terraform; `terraform plan` (MFA env per steering) and check: PI support for the class, parameter group family unchanged (`postgres15`), new `max_connections`, and that the alarm thresholds of C4.1b are changed in the same PR. Recompute C2.2.
3. **Price:** confirm in the AWS pricing calculator; the tech lead approves the spend.
4. **Pre-checks:** all job tables idle (C6.3b), no wave, no pending DB Migrate; take a manual snapshot.
5. **Window:** announce a short outage for every app (single-AZ class change restarts the instance, several minutes; Multi-AZ fails over in ~1-2 min); apply in the maintenance window or with `apply_immediately` by explicit decision.
6. **Verify:** `SHOW max_connections`; `DatabaseConnections` back to normal; CIS `/health` and worker `job_worker_started`, `/booking/health`, TripPlanner browse smoke; no `too many connections` in the log export.
7. **Record:** session log, capacity review folder, updated C2.2 / C4.1 values. **Rollback:** modify back to the previous class (same outage profile); the snapshot is the last resort.

### C9.2 Other scale steps (outline)

| Step | Must-have stages |
|---|---|
| RDS Proxy (L7) | Proxy + IAM auth in Terraform → point **one** TP Lambda at it in Dev → watch `DatabaseConnectionsCurrentlySessionPinned` and latency for a week (prepared statements, `set_config(..., true)` GUC) → move the second Lambda → only then raise reserved concurrency and the `tripplanner` `CONNECTION LIMIT` budget. |
| Materialized catalog (L4) | Owner migration creates tables behind the heavy `catalog.*` views → `catalog_refresh` job kind fills them (versioned swap, ADR 0003 decision 3) → views switch to read the tables, contract shape unchanged, `refreshed_at` exposed → parity check vs the old view for 7 days. |
| Partition a ledger (L5) | Retention (N4) running first → the PK becomes `(id, <partition column>)` because a partitioned table's unique keys must include the partition key (`shared.llm_call_log` today has `id uuid` alone; new ledgers use `bigint` identity + `created_at`, review 4.4) → create the partitioned parent + future partitions (pg_partman or job) → CHECK NOT VALID / VALIDATE on the old table → ATTACH it as one partition in a short lock window → retention switches from DELETE to DROP PARTITION after archive. |
| Read replica | Create replica → route only read-only reporting/admin pools (new `application_name`) → monitor `ReplicaLag` (alarm > 30 s) → never route writes or read-your-writes paths. |
| Split Booking out | L4 done → new instance + `bk_owner` objects restored → logical replication of the catalog tables Booking reads → read-only freeze window → DSN cut-over by private CNAME (X10) → keep the old schema read-only 14 days → contract under DRY RUN. |
| Event relay (L8) | Outbox stays the source of truth → relay publishes to EventBridge → per-consumer SQS + DLQ → consumer inbox keeps its idempotency key → pull job retired only after 14 days of parity. |

---

## Appendix: facts this part relies on

These are the facts of the S237 review baseline (15/10/2026, S236 dump). Several have changed since (instance class,
final snapshot, alarms, pool sizes, reserved concurrency); the current values are in the sections above.

| Fact | Source |
|---|---|
| Instance `db.t3.micro`, 20 GB gp3, single-AZ, PITR 7 d, PI off, `skip_final_snapshot = true` | `infra/AA-CIS-Infra/modules/rds/main.tf` |
| Connections alarm > 70 for 10 min; storage alarm < 4 GiB; SNS topic `alerts` | `infra/AA-CIS-Infra/accounts/aa365/observability_ecosys.tf`; `accounts/aa365/observability.tf:45` |
| CIS API pool 10 + tenant pool 5; API autoscaling max 10; API `deployment_maximum_percent` 200 | `apps/AA-CIS-App/api/main.py:78`, `api/core/aa544_tenant_pool.py:62`, `modules/ecs/main.tf:348,391` |
| Worker pool `max(5, max_parallel + 2)`, `max_parallel` 8, heartbeat 20 s, lease 90 s, autoscaling max 3, `stopTimeout` 120 s | `apps/AA-CIS-App/shared/jobs/worker.py:71,282,323`, `modules/ecs/main.tf:490,548`, `modules/ecs/variables.tf:144` |
| `expected_seconds` is a job-kind attribute (default 600), not a `shared.job` column | `apps/AA-CIS-App/shared/jobs/registry.py:36` |
| TripPlanner pool max 5 (`command_timeout=30`); Lambda timeouts 30 s / 60 s, no reserved concurrency | `apps/AA-TripPlanner-Web/backend/shared/db.py:60`, `accounts/aa365/tripplanner.tf` |
| Terraform Apply is one manual (`workflow_dispatch`) run over `accounts/aa365` | `infra/AA-CIS-Infra/.github/workflows/terraform-apply.yml` |
| Booking pool max 5, in-process `booking.job` worker (lease 300 s, stop wait 20 s, release on shutdown, ECS `stopTimeout` 30 s), deploy job guard via GitHub OIDC (S241); Booking migration guard forbids `ALTER ROLE` | `apps/AA-Booking/backend/app/db.py:54`, `app/main.py`, `app/jobs/worker.py`, `app/routers/ops.py`, `infra/AA-CIS-Infra/accounts/aa365/booking.tf:293`, `.github/workflows/deploy-dev.yml`, `backend/tests/migration_guard.py` |
| `shared.llm_call_log` timestamp is `created_at` (no `called_at`), `id uuid`; `shared.tenant_api_usage.called_at` nullable, `id uuid`; `booking.inbox_events` timestamp is `received_at` | `docs/architecture/db-schema-reference.md` (S236 dump) |
| No recurring scheduler in CIS; EventBridge Scheduler pattern exists | `accounts/aa365/dfs_balance.tf` (`aws_scheduler_schedule.dfs_balance_daily`) |
| D8 migration flow, AA-807 copy guard, DB Migrate on the CIS task def | `infra/AA-CIS-Infra/db/README.md`, `.github/workflows/db-migrate.yml` |
| RLS rollout D2 (ENABLE without FORCE until the role split) | `docs/audits/2026-10-14-S237-lane-backlog/aa817/aa817_design.md` |
| Ownership rules, version keys | `docs/database/schema-ownership.md` |
