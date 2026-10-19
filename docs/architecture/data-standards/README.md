---
id: ARCH-08
title: "AA_Ecosys data standards"
description: "Index, golden rules, version and changelog of the binding data standards (Parts A, B and C) for the shared PostgreSQL RDS and every app that uses it."
type: reference
status: active
owner: nghiep
audience: [engineer, devops, cto, cio, agent]
applies_to: [ecosystem, aa-cis-dev-db]
last_reviewed: 2026-10-19
review_every_days: 90
related: [ARCH-08-engineering, ARCH-08-data-management, ARCH-08-scaling, ARCH-08-schema-ownership, ARCH-01, docs/adr/0008-new-app-integration-and-data-platform-rules.md]
---

# AA_Ecosys data standards

**Version 1.2** · S244 · 19/10/2026 · **v1.0 and v1.1 approved by Nghiệp** (v1.0: S237 data-architecture review,
"đồng ý duyệt hết", decisions E1–E11; v1.1: S243 N-1; v1.2: X1 close-out, Nghiệp approves its root PR, see the
changelog below) · Host ADR:
[ADR 0008 — New-app integration and data platform rules](../../adr/0008-new-app-integration-and-data-platform-rules.md)
(accepted 15/10/2026), with [ADR 0003a — one job table per owner](../../adr/0003a-per-owner-job-tables.md).

## Purpose

Binding rules for designing, changing, operating and scaling data on the shared PostgreSQL 15 RDS
(`aa-cis-dev-db`, acc2 `005097885195`, us-west-1) that AA-CIS-App, AA-TripPlanner-Web and AA-Booking
share, so that:

- every schema has one owner in fact (permissions), not only in convention;
- one app's bug, burst or migration cannot take the other two down or read their data;
- a new app (first candidate: the tenant CRM, AA-821) joins through one gate and one playbook;
- each scale step is taken on a measured trigger, cheapest lever first.

## Scope

- **Who:** anyone, human or agent (Claude Code, Kiro), who writes a table, migration, policy, grant,
  view, contract, query, pool setting, retention job or RDS/Terraform change in any AA_Ecosys repo.
- **What:** new and changed objects. Existing names stay; legacy objects that break a rule are listed
  once in [Part A §9](01-engineering.md#9-grandfathered-exceptions), each with the roadmap item that
  retires it. New code never copies a grandfathered pattern.
- **Where:** Dev today; the prod instance (also on acc2, roadmap L9) inherits the same rules plus the
  prod rows of Part B §9 and Part C §C7.2.

## The three parts

| Part | File | Owns (single home of these rules and numbers) |
|---|---|---|
| A — Engineering | [`01-engineering.md`](01-engineering.md) | Naming and types (NAM), keys (KEY), migrations and the runner defaults (MIG), roles/grants/RLS template (SEC), views and contracts (CON), queries and indexes (QRY), testing (TST), the PR review checklist (§8), grandfathered exceptions (§9) |
| B — Data management | [`02-data-management.md`](02-data-management.md) | Ownership and stewards (DM-1), entity source of truth and canonical patterns (DM-2), catalog, dead-table registry and glossary (DM-3), quality (DM-4), lineage (DM-5), **PII classes** (DM-6), **retention windows** (DM-7), access (DM-8), backup/DR targets (DM-9), cost (DM-10), change management and approvals (DM-11) |
| C — Operations and scaling | [`03-scaling.md`](03-scaling.md) | SLOs (C1), **connection budget, pool sizes, connection limits, timeouts** (C2), scale triggers (C3), **alarms and thresholds** (C4), maintenance and batched deletes (C5), job runner and deploy guard (C6), environments and prod blueprint (C7), capacity review (C8), scale-up runbooks (C9) |

**Precedence:** an accepted ADR wins over these parts; the parts win over skills, steering summaries
and session notes. Each number lives in one part; the others cite it. A conflict found anywhere is
fixed by PR in the same session and reported to Nghiệp.

## How the standard is enforced

Keywords: **MUST / MUST NOT** = the reviewer blocks the PR (an exception needs Nghiệp's written
approval in the PR and the session log); **SHOULD** = default, a deviation is explained in the PR;
**MAY** = allowed. Every rule names its enforcement:

| Layer | Exists today | To build (roadmap id, Linear) |
|---|---|---|
| **CI** | Migration Copy Guard (`infra/AA-CIS-Infra/db/check_migration_copies.py`); DB Migrate exit 3 when a file did not register (`db/run_migration.py`); Booking migration guard (`apps/AA-Booking/backend/tests/migration_guard.py`); CIS and Booking migration replay on `postgres:15`; CIS RLS tests (`test_007_rls_isolation.py`, `test_tenant_rls.py`, `test_aa679_catalog_views.py`); CIS gateway seam test (`tests/unit/test_aa685_no_raw_model_calls.py`); CIS deploy job guard on `shared.job`; job-table template comparison (CIS + Booking) and the Booking deploy guard by GitHub OIDC (X6, AA-751, S240–S241); DB Migrate idle check on every `<schema>.job` (exit 7) | generated schema reference + nightly drift check (N1, AA-807); safe runner defaults, `-- migrate:` headers, SQL lint, unique-number check (N5, AA-807); catalogue guard for RLS, grants, cross-owner FKs (X2, AA-817/AA-807); consumer contract hash guard (X7, AA-826); connection-budget check (N3, AA-824) |
| **Database** | `catalog_owner` + role-scoped policy pattern (CIS 225); `UNIQUE` idempotency keys | `CONNECTION LIMIT` per role (N3, AA-824); owner/runtime roles, `db_migrator` (X1, AA-807/AA-817) |
| **Alarm** | Part C C4.1 RDS baseline: connections > 60 % of `max_connections`, free storage, memory, CPU, CPU credits, read/write latency, disk queue, XID wraparound, per-role connections vs `CONNECTION LIMIT` + sampling-stopped (AA-824, AA-832); per-app budgets (AA-828); account budget $250 | Part C C4.1 baseline incl. memory, CPU credits, per-role connections, job backlog age (N3, AA-824; X6); per-app budgets (X9, AA-828) |
| **Review** | the PR checklist in [Part A §8](01-engineering.md#8-review-checklist-for-any-pr-that-touches-sql) (copy into every PR that touches SQL); the new-app checklist (ADR 0008 / review §6.3, copy into the epic); the approval table in [Part B §11](02-data-management.md#11-change-management) | — |
| **Runbook** | DRY RUN for destructive work (`skill/aa-cis-schema/references/destructive-ops.md`); S3-mediated ECS exec; aa-ship job guard queries; aa817 isolation probe | restore drill + single-schema restore (X10, AA-829); retention first-run DRY RUN (N4, AA-825); monthly capacity review (Part C C8) |

Until a *to build* control lands, the review checklist carries its check. The full map of rules to
roadmap items is [Part B §12](02-data-management.md#12-enforcement-still-to-build).

## Golden rules (one page)

1. **One instance per environment, one owner per schema, every schema liftable.** Only the owner repo
   migrates a schema and only the owner app writes its rows. (A §1–3, B DM-1.1, ADR 0008 d1)
2. **Schema changes only through D8:** migration-only PR → byte copy in Infra → Copy Guard → DB Migrate
   `check`/`apply` → code PR. Never DDL from a laptop, ECS exec or app start-up. Trust the generated
   schema reference; if an object is newer than its "Verified" line, introspect it live. (MIG-4, MIG-5)
3. **No foreign key between owners.** Cross-app references are indexed soft keys; a tour is
   `(source_system, source_id)`, never `tour_id`. (KEY-1–3, DM-2.2–2.3)
4. **Cross-app reads only through contract views** (`catalog.*`, a producer's `<schema>.v_<entity>`, or
   `<schema>.v_<event>_outbox`). New grants are `SELECT` on views only, per object, from the producer's
   migration; no default ACL to an app role; nothing to `PUBLIC`. (CON-1, SEC-3–5)
5. **Cross-app state changes only through outbox → pull job → inbox** with an idempotency key; writes
   into another app only through its HTTP API. (CON-7, DM-5.4)
6. **Contracts are versioned and append-only:** JSON Schema + registry row in the same PR as the view;
   additive = minor; breaking = a new major served in parallel ≥ 30 days. (CON-3–5)
7. **Every tenant table:** `tenant_id uuid NOT NULL`, ENABLE RLS, the one policy template
   (`app.tenant_id`, `NULLIF`, explicit `WITH CHECK`, `TO <runtime role>`); FORCE from day one for new
   apps, for CIS only after the role split (AA-817 D2). (SEC-6–9)
8. **The tenant context is set transaction-locally after a membership check;** a new app's tenant pool
   fails closed (503); no app sets the tenant GUC to read another owner's tables. (SEC-10, DM-8.4)
9. **Ownership is a permission:** NOLOGIN `<app>_owner`, LOGIN `<app>_app` with `CONNECTION LIMIT` and
   `application_name`, a separate `db_migrator`; Booking and TripPlanner first, CIS behind D2;
   `aa_cis_admin` becomes break-glass. Role attributes live in git, never by hand. (SEC-1, SEC-11,
   DM-8.1–8.2, ADR 0008 d6)
10. **The connection budget stays ≤ 75 % of `max_connections`** and lives in Part C C2.2; any PR that
    changes a pool, task count, Lambda concurrency or instance class updates it. Limits and reserved
    concurrency ship **before** the Lambda quota of 1000 is applied. (QRY-6, C2)
11. **Migrations are expand/contract, idempotent, self-registering and lock-safe:** wait ≥ 14 days
    before contract, `lock_timeout` / `statement_timeout` set, no down files, all job tables idle
    before `apply`; destructive work under DRY RUN with a snapshot. (MIG-2–14, C6.3b)
12. **Every log, event, outbox or job table ships with a retention row and a TTL index.** Owner-run,
    batched TTL jobs; archive to S3 Parquet before delete; never `VACUUM FULL`. Approved windows:
    `llm_call_log` 180 d + daily rollup, `tenant_api_usage` 90 d + monthly rollup, jobs succeeded 30 d /
    failed 90 d, outbox/inbox payload PII redacted after 90 d. (NAM-15, DM-7, C5.4)
13. **`booking.customers` is the single customer master.** No parallel customer profile; PII columns
    tagged `pii:<class>`; payloads and logs carry ids, not personal details; no identifying data in
    prompts, Jev or LLM ledgers. (KEY-5, DM-6.1–6.4)
14. **Identity is Cognito `(iss, sub)`.** No password, OTP, session or clear-text token tables in a new
    schema; tokens are random and stored hashed. (NAM-13–14, DM-6.9, ADR 0006)
15. **One job table per owner** (`<schema>.job`) from the shared DDL template with the owner's kind
    prefix; no app enqueues into another owner's queue. (ADR 0003a, QRY-8, C6.1d)
16. **One canonical pattern per concept** — jobs, audit, notifications, places (`shared.destinations` +
    `geo.place_name`), photos (`catalog.v_*_photo`), countries (`shared.countries`); new objects never in
    `public`, no new CIS-private tables in `shared`. (DM-1.5, DM-2.4, NAM-2, KEY-9)
17. **Every paid call goes through its seam into its ledger** with `cost_usd` (LLM → gateway →
    `llm_call_log`; Jev → `decision_log`; DataForSEO → `dfs_call_log`; geocoder → `geo.geocode_call`);
    other apps read cost only through the rollup. (DM-10.4–10.5, CON-8)
18. **Queries are sargable and indexed, with `EXPLAIN (ANALYZE, BUFFERS)` in the PR;** no LLM, HTTP or
    S3 call inside a transaction or while holding a connection; never share one connection between
    concurrent tasks. (QRY-1–4, QRY-11)
19. **Scale only on a measured trigger, cheapest lever first** (query/index → retention → pool budget
    → materialized read model → resize → proxy → replica → split), cite the trigger row in the PR, and
    run the monthly capacity review. (C3, C8)
20. **A new app passes the ADR 0008 decision gate first;** a new domain follows the 12-step playbook and
    passes the isolation probe (0 cross-tenant rows) before its first tenant. (ADR 0008 d2–d3, DM-1.6,
    TST-4)

## Changing this standard

A PR to the root repo, approved by Nghiệp. A rule change bumps the version below; steering
(`.kiro/steering/*.md`) and skills that restate a rule are updated in the same PR. A change to an
accepted decision (role order, retention windows, contract schema, customer master) also amends
ADR 0008.

| Version | Date | Session | Change |
|---|---|---|---|
| 1.0 | 15/10/2026 | S237 | First version: Parts A–C, ADR 0008, ADR 0003a. Approved by Nghiệp. |
| 1.1 | 19/10/2026 | S243 | Approved by Nghiệp (S243 N-1; the decisions are S241's, `docs/sessions/2026-10-17-S241-decisions.md`). **D-13:** DM-11.5 merge rights by phase (dev: agents merge after green CI; from prod / first paying tenant: Nghiệp approves Terraform/IAM, migration, auth/security and data-deletion PRs), enforcement "subagent hook; review" instead of "Branch protection"; Part B §11 "Who approves what" note and rows (new table/column; role, RLS or default-ACL change). **D-12:** C2.3g, DM-8.4, Part A SEC-10 and §9: tenant-pool flags fail closed globally (unreadable flag = tenant pool, explicit `"false"` = admin pool for that route, emergency `TENANT_POOL_FORCE_ADMIN_FLAGS`), with the rollback path (CIS #792). **D-09 (AA-872):** DM-7 rows for CloudWatch security/audit logs (VPC flow, WAF, ECS Exec, Cognito triggers; `postgresql` already listed) 365 days and application logs 30 days; C4.2b 14 → 365 days. **Facts (AA-889):** DM-11.2 schema reference regenerated by `db-schema-dump.yml` (nightly + after every DB Migrate apply); DM-1.2 `owners.yaml` exists (X1 S1) and is the single registry, `docs/database/schema-ownership.md` explains it (Part A tooling table and MIG-1 follow); status moved to "Exists" after a Terraform read: C4.2a, C4.2b, C7.1 (class, storage, final snapshot, parameter group, restore drill), DM-9.1. |
| 1.2 | 19/10/2026 | S244 | X1 close-out (AA-852 / AA-860, X1 plan S23). **Exception (needs Nghiệp's approval in the PR):** Part A §9 row XD3, default privileges `FOR ROLE cis_owner … TO cis_app` in the 11 CIS runtime schemas, also cited in DM-8.3. **Facts:** Part A §9 rows retired (`aa_cis_admin` as runtime + migrator + owner; bk-001 `FOR ROLE aa_cis_admin`; Booking/TP objects owned by the migrator) into a "Retired rows" table, the Booking/TP owner default privileges listed; SEC-6 note on the runtime role `cis_app` and its `<table>_cis_app_all` policy; DM-8.2 in force (`db_migrator`); DM-8.9 break-glass text (master only for `roles/`, `set-password`, `run-script`); C2.2 role column, `db_migrator` limit 5, `cis_app` connection sites. |

## Open items for Nghiệp

Decisions the parts follow for now, which Nghiệp may change by PR:

1. **N3 interim:** `CONNECTION LIMIT` of `tripplanner`, `booking`, `aa_app_user` set by one CIS
   migration (the single MIG-6 exception) until the X1 Infra role bootstrap exists. Alternative: build
   the bootstrap directory first (needs `db-migrate.yml`, `check_migration_copies.py` changes).
2. **TripPlanner traveller data:** the parts follow ADR 0006 decision 9 ("guest contact data only")
   over the E8 phrase "subject + consent".
3. **TripPlanner job runner:** `tripplanner.job` + a scheduled Lambda worker (ADR 0003a decision 4)
   before its first TTL kind; until then the TripPlanner outbox redaction waits.
4. **AA-751:** re-scope to X6 (recommended) or close.
5. **TripPlanner migration CI** (apply all `tp-NNN` on `postgres:15`) has no roadmap id: fold into X1
   or give it its own issue.
6. **No automated PII check** on prompts or logs is on the roadmap (DM-6.4 stays review-only).
7. **Proposed extensions** beyond the review's scope (marked `+` in Part B §12): orphan-rate query and
   dump-based quality measures (N1+), PII tag lint and kernel-list guard (X2+), read-only ops role (X1+).
8. **Proposed retention rows** in Part B §7 (DFS/geocoder ledgers, superseded rankings/routes,
   notifications, Booking OTP/session rows, TripPlanner sessions/events, `decision_log`) and the
   "stop at 2x the previous run" rule need owner confirmation in N4 / L3.
9. **Unverified facts to check during delivery:** Performance Insights support on `db.t4g.small`
   (`terraform plan`, X9); whether any CIS job holds a transaction across an LLM call (before
   `idle_in_transaction_session_timeout = 60s`, C2.3f); real `max_connections` after the resize
   (recompute C2.2); the reference dump is stale (no 228 / 230 / bk-007) until N1.
10. **Follow-up edits outside these files:** `schema-ownership.md` rule 2 → views only and the `job` row
    → ADR 0003a; header pointers in ADR 0001 and ADR 0003; Booking `deploy-dev.yml:16` stale "No job
    guard" comment; a `docs/adr/` index (none exists today).
