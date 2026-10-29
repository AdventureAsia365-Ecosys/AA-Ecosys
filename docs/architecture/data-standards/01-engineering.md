---
id: ARCH-08-engineering
title: "AA_Ecosys data standards — Part A: Engineering"
description: "Part A of the data standards: naming, keys, migration mechanics (MIG-*), the RLS template and query rules for anyone who designs a table or writes a migration on the shared RDS."
type: reference
status: active
owner: nghiep
audience: [engineer, devops, cto, cio, agent]
applies_to: [ecosystem, aa-cis-dev-db]
last_reviewed: 2026-10-29
review_every_days: 90
related: [ARCH-08, ARCH-08-data-management, ARCH-08-scaling, ARCH-08-schema-ownership]
---

# AA_Ecosys data standards — Part A: Engineering

**Purpose:** binding rules for anyone (human or agent) who designs a table, writes a migration, a policy, a
view, a contract or a query against the shared PostgreSQL 15 RDS (`aa-cis-dev-db`, acc2 ([account map](../../onboarding.md#account-map)),
us-west-1) used by AA-CIS-App, AA-TripPlanner-Web, AA-Booking and AA-Partner (the partner CRM, schema `crm`), and by
any app that joins later.

- **Status:** Accepted 2026-10-15 (v1.0, S237); version 1.1 on 2026-10-19 (S243), 1.2 (S244, X1 close-out) and 1.3 (S247, partner CRM; changelog in [`README.md`](README.md)). The tech lead approved every recommendation of the S237
  data-architecture review (`docs/audits/2026-10-14-S237-lane-backlog/data-architecture/README.md`,
  "the review"). This page is part of the rule body that
  [ADR 0008](../../adr/0008-new-app-integration-and-data-platform-rules.md) (new-app integration and
  data platform rules, accepted 2026-10-15) cites; the index and golden rules are in
  [`README.md`](README.md).
- **Consistent with:** ADR 0001–0007 incl. 0004a, `docs/database/schema-ownership.md`,
  `docs/contracts/README.md`, `infra/AA-CIS-Infra/db/README.md` (D8 flow, copy guard), the AA-817 design
  (`docs/audits/2026-10-14-S237-lane-backlog/aa817/aa817_design.md`, decision D2) and
  `.kiro/steering/*.md`. When this page and an accepted ADR disagree, the ADR wins and this page is
  fixed in the same PR.
- **Scope:** rules bind **new** objects and **changed** objects. Existing legacy objects are
  grandfathered only where section 9 lists them, each with its retirement item.
- **Sister parts:** Part B `02-data-management.md` (ownership, PII classes, retention windows, backup)
  and Part C `03-scaling.md` (connection budget C2.2, timeouts, monitoring, job runner). Where this
  page needs a number that Part B or C owns (PII classes, retention windows, pool sizes, role
  timeouts, connection limits), it cites that part instead of repeating the value, so the three
  cannot drift apart.
- **Tightenings of earlier text (approved with the review, recorded in ADR 0008):** CON-1/SEC-5 narrow
  ADR 0001 decision 6 ("read … `shared.*` golden records") and `schema-ownership.md` rule 2 ("a
  column list or a view") to **views only** for new grants; existing table and column grants are
  grandfathered in section 9 until **X4**.

## Contents

0. [How to read this page](#0-how-to-read-this-page)
1. [Naming and types](#1-naming-and-types)
2. [Keys and relationships](#2-keys-and-relationships)
3. [Migrations](#3-migrations)
4. [Roles, grants and RLS](#4-roles-grants-and-rls)
5. [Views and contracts](#5-views-and-contracts)
6. [Queries, indexes and connections](#6-queries-indexes-and-connections)
7. [Testing](#7-testing)
8. [Review checklist for any PR that touches SQL](#8-review-checklist-for-any-pr-that-touches-sql)
9. [Grandfathered exceptions](#9-grandfathered-exceptions)

---

## 0. How to read this page

**Keywords.** MUST / MUST NOT = a reviewer blocks the PR. SHOULD / SHOULD NOT = allowed to deviate only
with the reason written in the PR description (or in the migration header). MAY = permitted, no reason needed.

**Rule format.** `ID (level)` — the rule. *Why:* one line. *Enforced:* where it is checked.
Rule IDs use 3-letter prefixes (`NAM`, `KEY`, `MIG`, `SEC`, `CON`, `QRY`, `TST`). Bold ids such as
**N3** or **X1** are items of the review's roadmap (section 7 of the review), not rule ids.

**Enforcement tools.** Only the first block exists today. Anything else is marked *to build* with its
roadmap id; until it lands, the review checklist (section 8) carries the check.

| Tool | Status | What it checks |
|---|---|---|
| Migration Copy Guard — `infra/AA-CIS-Infra/db/check_migration_copies.py`, `.github/workflows/migration-copy-guard.yml` (AA-807) | exists | path pattern, owner key prefix, file on the owner's `main`, byte identity; nightly over all copies; ownership lint (AA-853, `db/check_migration_ownership.py`, static): an owner dir touches only its own schemas (MIG-6) |
| DB Migrate — `.github/workflows/db-migrate.yml` + `db/run_migration.py` | exists | sha256 of the file, `check`/`apply`, fails (exit 3) if the version is not registered after the run |
| Booking migration guard — `apps/AA-Booking/backend/tests/migration_guard.py` | exists | BEGIN/COMMIT, `bk-NNN` self-registration, nothing outside schema `booking`, no login/password/extension/SECURITY DEFINER/PUBLIC grant, views revoke writes |
| Booking Integration Tests (`postgres:15`, login `aa_cis_admin`, re-apply for idempotency, no skips) | exists | every Booking migration applies twice on PG15 |
| CIS Integration Tests (`postgres:15`, superuser `cistest`, `apps/AA-CIS-App/tests/integration/`) | exists | migration replay + feature tests; RLS tests `test_007_rls_isolation.py`, `test_tenant_rls.py`, `test_aa544_stage1_tenant_pool_leak.py`, `test_aa679_catalog_views.py` (`rds_like_225` fixture) |
| AA-817 tenant isolation test `tests/integration/test_aa817_rls_tenant_isolation.py` | exists (landed with AA-817 / migration 229) | WHERE-less reads and writes as `aa_app_user` under own / foreign / forged / empty GUC |
| Live probe `docs/audits/2026-10-14-S237-lane-backlog/aa817/aa817_probe.py` | exists (manual, read-only, ECS exec) | role chain, owners, RLS/FORCE, policies, privileges, isolation matrix on Dev |
| CloudWatch alarm `DatabaseConnections` > 70 for 10 min (`accounts/aa365/observability_ecosys.tf`) | exists | connection saturation |
| Schema dump + nightly drift check, policies/indexes/grants/owners/default ACLs/sizes | dump exists (**N1**, AA-807: `db-schema-dump.yml`, nightly + after every apply); drift report exists (AA-853: replay of every migration, *Schema drift* section), **report only, not failing**; fail-on-unmanaged deferred until the replay baseline and the owner decisions exist | live vs a replay of the repos: unmanaged / missing / changed objects, owner decision or open |
| Instance guardrails, parameter group, `pg_stat_statements`, new alarms, `CONNECTION LIMIT`, `application_name`, Lambda reserved concurrency | *to build* **N3** | slow queries, lock waits, idle-in-transaction, connection budget |
| Safe runner defaults, `-- migrate:` headers, pre-snapshot, SQL lint (squawk or grep rules), unique-number check | *to build* **N5** | lock/statement timeouts, CONCURRENTLY, destructive snapshot |
| Infra role bootstrap (role attributes: LOGIN, `CONNECTION LIMIT`, role-level backstop timeouts, `application_name`) in git, applied through a reviewed Infra path | exists (X1, v1.2): AA-CIS-Infra `db/migrations/roles/` (key `rl-NNN`, runs as the master): `rl-001` (`bk_owner`, `tp_owner`, `cis_app` limit 90, the N3 limits restated from CIS 234), `rl-002` (`cis_owner`, `db_migrator` limit 5), `rl-003` / `rl-004` (CRM roles: `crm_owner`, `crm_app` and the CRM NOLOGIN roles). Role-level backstop timeouts: later `rl-` files | roles are Infra-owned (`schema-ownership.md` rule 3); DB Migrate accepts `cis`/`tripplanner`/`booking`/`crm`/`roles` dirs and the Booking guard rejects `ALTER ROLE` |
| `infra/AA-CIS-Infra/db/owners.yaml` + owner roles + `db_migrator` | `owners.yaml` exists (X1 S1, AA-CIS-Infra #163; v1.1); owner roles `cis_owner` / `bk_owner` / `tp_owner`, runtime `cis_app` and login `db_migrator` exist (X1, done 2026-10-19; v1.2) | one registry of owners, prefixes, roles, allowed grants |
| Shared job-table DDL template in `shared/jobs` ([ADR 0003a](../../adr/0003a-per-owner-job-tables.md)) | *to build* **X6** | one job shape per owner schema |
| Retention/rollup job kinds, `shared.llm_call_daily` | *to build* **N4** | TTL deletes after S3 archive; rollups other apps read |
| [`docs/architecture/dead-table-registry.md`](../dead-table-registry.md) | exists (**N6**, AA-850, S255) | every quarantined or dropped object |
| Catalogue CI guard | *to build* **X2** | tenant table without RLS, PUBLIC policy, `app.current_tenant`, missing NULLIF, cross-owner FK, grants vs allowlist |
| Consumer contract-copy hash guard | *to build* **X7** | consumer copies of `docs/contracts/*.json` equal the producer's |

---

## 1. Naming and types

**NAM-1 (MUST)** A new schema is named after its domain noun (`geo`, `booking`, `crm`): lower
snake_case, no codename, no medallion layer (`silver_`, `gold_`), no version suffix.
*Why:* names outlive pipelines; existing names stay because a rename touches hundreds of SQL sites.
*Enforced:* review; ADR or design doc required for every new schema (playbook step 1, review §6.2).

**NAM-2 (MUST NOT)** Create new objects in `public`, or new CIS-private tables in `shared`. `shared` holds
only the platform kernel; the kernel list and where a new CIS-private table goes instead are Part B
**DM-1.5** (one list, not repeated here).
*Why:* `shared` already mixes kernel and CIS ops tables (`decision_log`, `tenant_api_usage`, …), which
makes ownership and grants unreadable. *Enforced:* review; **X2** will list objects in `public`/`shared`
not in the `owners.yaml` allowlist.

**NAM-3 (MUST)** Identifiers are lower snake_case, unquoted, ASCII. A new schema picks singular or plural
table names in its first migration and keeps it (existing schemas keep their mix). Suffix conventions:
`_id` for keys, `_at` for `timestamptz`, `is_`/`has_` for booleans, `_iso2` for ISO-3166 alpha-2, `_hash`
for content digests. Contract views are `v_<entity>`; outbox views are `v_<event>_outbox` (CON-1).
*Why:* agents and reviewers infer meaning from names. *Enforced:* review; squawk/grep lint (*to build*, **N5**).

**NAM-4 (MUST)** Entity tables use `id uuid PRIMARY KEY DEFAULT gen_random_uuid()`. Deterministic ids
MAY use uuid5 when the identity is derived (ADR 0007 `component_id`).
*Why:* ids are safe to expose across apps and to merge between environments; no sequence coupling.
*Enforced:* review.

**NAM-5 (MUST)** Append-only log, ledger and event tables use `id bigint GENERATED ALWAYS AS IDENTITY`
plus `created_at timestamptz NOT NULL DEFAULT now()`. New tables MUST NOT use `serial`/`bigserial`.
*Why:* cheap later range partitioning on `created_at` (review §5.2) and no sequence ownership quirks.
*Enforced:* review; lint (*to build*, **N5**).

**NAM-6 (MUST)** Time columns are `timestamptz`. Entities carry `created_at` and `updated_at`
`timestamptz NOT NULL DEFAULT now()`. Never `timestamp without time zone`. Soft delete uses
`deleted_at timestamptz NULL`. `updated_at` is never a change cursor for consumers (CON-6).
*Why:* several apps, several runtimes and UTC/ICT users; a naive timestamp is ambiguous.
*Enforced:* review; lint (*to build*, **N5**).

**NAM-7 (MUST NOT)** Create new enum types. Use `text NOT NULL CHECK (col IN (...))`, with the constraint
named `<table>_<col>_check`. Legacy enums in `public` stay.
*Why:* an enum value can never be removed and adding one has transaction caveats; a CHECK is replaced
with `NOT VALID` + `VALIDATE` without a rewrite. *Enforced:* review; Booking migration guard style lint
(*to build* for CIS/TP, **N5**).

**NAM-8 (SHOULD)** Use `text` (with a `CHECK (length(col) <= n)` when a limit matters) over `varchar(n)`;
`numeric(p,s)` for money, never `real`/`double precision`, with a separate `currency char(3)` ISO-4217
column (ADR 0005); `jsonb` only for open-ended payloads.
*Why:* `varchar(n)` changes need a type ALTER; float money drifts. *Enforced:* review.

**NAM-9 (MUST)** A field that queries filter, group or join on is a real column, not a `jsonb` key.
*Why:* `llm_call_log` keeps `app` and the shadow flag only in jsonb, so per-app rollups scan the table
(review P5; AA-804 adds the columns). *Enforced:* review; EXPLAIN in the PR (QRY-3).

**NAM-10 (MUST)** Every tenant-owned table has `tenant_id uuid NOT NULL` on the table itself, even when a
parent already has it. New tables MUST NOT mix platform rows (`tenant_id IS NULL`) and tenant rows; if
that is unavoidable, add `scope text NOT NULL CHECK (scope IN ('platform','tenant'))` and separate
SELECT and write policies (SEC-9).
*Why:* `acp_shared.angle_gate_option` ("isolated via its parent") and `acp_shared.facts` (tenant role can
write platform facts) are the two RLS gaps found in AA-817 §5. *Enforced:* review; **X2** guard.

**NAM-11 (MUST)** New country columns are `country_iso2 char(2)` keyed to `shared.countries` (**X5**),
added next to any existing free-text country (additive). Free text stays display-only.
*Why:* free-text country is the only key today outside `booking.countries`. *Enforced:* review.

**NAM-12 (MUST)** Every column that holds personal data carries
`COMMENT ON COLUMN … IS 'pii:<class>; <free text>'`, and every commercial secret or credential
`conf:commercial` / `conf:credential`, with the classes defined only in Part B **DM-6.1**. This page
does not keep its own class list.
*Why:* PII is copied 4 times today with no tags, so erasure and consent audits rely on memory (review P10).
*Enforced:* review; the **N1** dump lists `pii:` columns (*to build*).

**NAM-13 (MUST NOT)** Store a secret or a guessable bearer token in clear. Tokens are random
(≥ 128 bits) and stored hashed (pattern: `booking.customer_sessions.refresh_token_hash`; the AA-813
invitation token, ADR 0006 Phase 3).
*Why:* `tripplanner.sessions.guest_token = id::text` is guessable (review P10, fix **X8**). *Enforced:* review.

**NAM-14 (MUST NOT)** Create tables for passwords, OTPs, login sessions or refresh tokens of staff,
tenant users or travellers in a new schema. Sign-in is Cognito (ADR 0006); an app stores only the
`(iss, sub)` link and its own authorization data (membership, role). **One exception:** the partner CRM
keeps hashed client-link tokens and email-code challenges for an agency's travellers (`crm.client_link`,
`crm.otp_challenge`), as [ADR 0008a](../../adr/0008a-crm-separate-app-exceptions.md) decision 4 allows. It never
stores passwords.
*Why:* ADR 0006 retires the home-made stacks (`shared.admin_users.password_hash`, Phase 1;
`booking.customer_otps` / `customer_sessions`, Phase 4). *Enforced:* review; grandfathered rows in section 9.

**NAM-15 (MUST)** A new append-only log, ledger, event, outbox/inbox or job table ships, in the same PR,
with (a) its row in the Part B §7 retention table (raw window, rollup, archive-to-S3 yes/no) and (b) an
index that serves the TTL predicate (`created_at`, or `finished_at` for jobs).
*Why:* nothing is retained or rolled up today and the disk does not autoscale (review P5); a TTL job
without an index scans the table it is trying to shrink. *Enforced:* review checklist; the **N4**
job kinds (*to build*) refuse a table with no retention row.

---

## 2. Keys and relationships

**KEY-1 (MUST NOT)** Create a foreign key from one owner's schema into another owner's schema (owner as in
`schema-ownership.md`). Within one owner, FKs SHOULD be used.
*Why:* a cross-app FK blocks the other owner's deletes, dedupes and any later split into its own
database (review §4.1). *Enforced:* Booking migration guard (nothing outside `booking`); **X2** guard
(*to build*); review.

**KEY-2 (MUST)** A cross-app reference is a **soft key**: a plain column holding the owner's public
identifier, indexed (QRY-2), and the consumer code handles the referenced row disappearing (it reads
liveness from the contract view, e.g. `catalog.v_tour`).
*Why:* this is the Booking pattern (ADR 0004/0004a) that keeps every schema liftable. *Enforced:* review.

**KEY-3 (MUST)** A tour is referenced across apps by `(source_system text, source_id text)` with
`source_system = 'cis'` and `source_id = COALESCE(raw_tours.source_group_id, tour_id)` exactly as
`catalog.v_tour` exposes it. `tour_id` is a version snapshot and MAY be stored only as an attribute
(e.g. `built_from_tour_id`). Never join on `silver_aa_internal.raw_tours.source_id` (a uuid FK to
`raw_sources`, a homonym).
*Why:* `tour_id` changes on every re-upload, so trip cases keyed by it silently orphan (review P6;
ADR 0005 decision 1, ADR 0007 decision 3). *Enforced:* contract `catalog.tour.v1.1` (root PR
`docs/s237-catalog-graph-228`) and `inquiry.submitted` v1.2 (*to build*, **X3**); review.

**KEY-4 (MUST)** Other shared identifiers: place = `shared.destinations.id` (`destination_id`, read through
`catalog.v_destination`); tenant = `shared.tenants.id` (`tenant_id uuid`); country = `iso2`; staff and
traveller identity = Cognito `(iss, sub)` (ADR 0006); customer = `booking.customers.id`.
*Why:* one key per entity (review §4.3). *Enforced:* review.

**KEY-5 (MUST)** `booking.customers` is the single customer master. Another app stores only a soft key
(`customer_id`) or the Cognito `(iss, sub)` plus what its contract requires, never its own copy of
contact details. After ADR 0006 Phase 4, TripPlanner keeps no profile of a signed-in traveller and only
the guest contact + consent an inquiry needs (Part B **DM-6.2**, ADR 0006 decision 9; **L3**).
*Why:* one place to answer erasure and consent requests. *Enforced:* review; NAM-12 tags.

**KEY-6 (MUST NOT)** The partner CRM (AA-Partner, schema `crm`, AA-821) reads `booking.customers` or
`tripplanner.customers`, and no other AA app (CIS, Booking, TripPlanner) reads `crm.*`. No cross-schema grant
exists in either direction: `crm_app` gets nothing outside `crm`, and no other app role gets anything on `crm`.
Everything between AA-Partner and the other apps goes over versioned HTTP contracts. AA support access is the
NOLOGIN role `crm_support_reader`, reached only by `SET LOCAL ROLE` during an owner-granted support window; there
is no AA database login on `crm`. This is [ADR 0008a](../../adr/0008a-crm-separate-app-exceptions.md) decision 1,
which replaced the earlier "CIS module" plan.
*Why:* the agency (tenant) is the data controller there and AA is the processor; AA's own customers are under a
different controller, and AA sales must not see an agency's clients. *Enforced:* no grant exists or may be
issued (SEC-5); the isolation probe expects 42501 for `cis_app`, `booking`, `tripplanner` and `aa_app_user` on
every `crm.*` object; **X2** grant allowlist (*to build*). Since **X1** (2026-10-19) `aa_cis_admin` is
break-glass only (SEC-12).

**KEY-7 (MUST)** Natural uniqueness and idempotency are database constraints (`UNIQUE`), not
application checks: e.g. `booking.inbox_events UNIQUE (source, contract, idempotency_key)`.
*Why:* concurrent workers and retries race an application-level check. *Enforced:* review; integration test.

**KEY-8 (SHOULD)** Within an owner, `ON DELETE` is chosen explicitly: `RESTRICT` by default, `CASCADE` only
for pure child rows that have no meaning alone, `SET NULL` only for optional links.
*Why:* an implicit `NO ACTION` hides the intent; a broad CASCADE turns one DELETE into a wave.
*Enforced:* review.

**KEY-9 (MUST)** A new table for a concept that already has a canonical form (jobs, audit,
notifications, places, photos, countries) reuses the form listed in Part B **DM-2.4** instead of
inventing a parallel one; for jobs see also QRY-8 and ADR 0003a. Audit tables are append-only for the
runtime role (`INSERT`/`SELECT` only, pattern `booking.audit_logs`, bk-001). A genuinely new variant
needs a design note saying why the canonical one does not fit.
*Why:* 4 job models, 2 audit tables, 2 notification tables, 2 photo-view layers and 5 place layers
exist today, and every new app copies whichever precedent it finds first (review P11).
*Enforced:* review.

---

## 3. Migrations

**MIG-1 (MUST)** Every schema has one owner repo and one key space: CIS `NNN`
(`apps/AA-CIS-App/api/migrations/`), TripPlanner `tp-NNN` (`apps/AA-TripPlanner-Web/migrations/`),
Booking `bk-NNN` (`apps/AA-Booking/migrations/`), CRM `crm-NNN` (`apps/AA-Partner/api/migrations/`), a new app
`<prefix>-NNN`. A new owner is registered in
`infra/AA-CIS-Infra/db/owners.yaml` (the single registry, Part B DM-1.2); the same Infra PR updates the files
that mirror it (`db-migrate.yml`, `run_migration.py`, `check_migration_copies.py`, `isolation_probe.py`;
`db/tests/test_owners_registry.py` fails when they disagree) and `schema-ownership.md`.
*Why:* without prefixes two owners' `007` collide and the second silently does not register.
*Enforced:* Copy Guard (prefix and path); DB Migrate path regex.

**MIG-2 (MUST)** Every file is wrapped in its own `BEGIN; … COMMIT;` (except `-- migrate: no-transaction` files, MIG-10) and registers itself:
`INSERT INTO shared.schema_versions … ON CONFLICT (version) DO NOTHING`.
*Why:* registration is how DB Migrate knows a file ran. *Enforced:* `run_migration.py` exit 3; Copy
Guard; Booking migration guard.

**MIG-3 (MUST)** Numbers are unique per owner, three digits, no letter suffix, never reused. Existing CIS
duplicates (007, 008, 019 and `007b`) are resolved in the registry, not renumbered.
*Why:* duplicate numbers make "which file is version X" ambiguous. *Enforced:* `PATH_RE`
(`[0-9]{3}_[a-z0-9_]+\.sql`); unique-number check (*to build*, **N5**).

**MIG-4 (MUST)** Two flows, chosen by the file's class (root ADR 0017, AA-993):

- **Expand file** (header `-- migrate: expand`; only additions: new objects, a new nullable column or one with a
  non-volatile default, a new non-unique index; never a hot table; ADR 0017 d3): **one app PR** holds the file, the
  code that needs it and the readiness raise to its key. After the merge the AA-CIS-Infra migration-sync bot copies it
  byte for byte and merges the copy PR; Migration Apply (environment `dev-db-auto`, repo variable `DB_AUTO_APPLY`)
  re-classifies and applies it in strict number order, runs the blocking Isolation Probe and dispatches DB Schema
  Dump, whose root PR merges itself when clean; the app's Deploy Dev `schema-gate` holds the rollout until the key is
  registered and that run's apply and probe are green, for at most `SCHEMA_GATE_TIMEOUT_S` (default 40 min), then
  fails before the rollout. While `DB_AUTO_APPLY` is not `true` (or AA-CIS-Infra is private) a person applies the
  copied file with DB Migrate `check` then `apply` within that window, or re-runs Deploy Dev after the apply.
- **Contract or destructive file** (no expand header): the D8 flow, in order: (1) migration-file-only PR merged to the
  owner's `main`; (2) the byte copy in `infra/AA-CIS-Infra/db/migrations/<owner>/` (opened and merged by the
  migration-sync bot since AA-993 M3; Copy Guard green); (3) DB Migrate `mode=check` then `mode=apply` on `main`, by
  a person; (4) the app code that reads the new objects in a later PR; (5) regenerate
  `docs/architecture/db-schema-reference.md` (automated by **N1**). App CI "Migration preflight" refuses a PR that
  adds such a file **and** raises readiness to it.
In both flows a copied file is immutable (fix forward with a new file; a revert of the app PR is code-only), and a new
file takes the owner `main` max + 1 (a deliberate lower number needs the label `migration:out-of-order` and is never
auto-applied).
Before a contract `apply`, every job table (`shared.job`, `booking.job`, `crm.job`, any `<schema>.job`) is idle and no
wave runs (Part C **C6.3b**; the aa-ship guard). This idle rule is for DB Migrate only: since AA-993 G5 an app
deploy waits only for an open wave or a deploy-blocking job kind (Part C **C6.3a**). The reference is
regenerated by the DB Schema Dump workflow (**N1**) after every apply. A migration or query that depends on an
object newer than the reference's "Verified" line waits for that PR, or is written against a live
introspection of that object, not the stale dump (steering `db-schema.md`).
*Why:* the schema exists before code depends on it; one reviewed path for all owners; additive changes need no
second PR and no hand step; the reference is trusted by agents, so a stale row becomes a wrong design (review P8).
*Enforced:* app CI "Migration preflight" (class, number, copied = immutable, readiness raise); Copy Guard (fails if the
file is not on the owner's `main` or differs) and its "Expand classify"; Migration Apply (strict prefix, runtime
post-check exit 14, lock risk exit 15); Deploy Dev `schema-gate`; DB Migrate; review.

**MIG-5 (MUST NOT)** Apply DDL to Dev or prod from a laptop, an ECS exec session or app start-up code.
Every live object (table, view, policy, grant, role) is created by an owner migration or the Infra role
bootstrap. One-off **data** fixes through the S3-mediated ECS exec pattern are DML on the owner's own
tables only, follow DRY RUN when they delete or overwrite, and keep the script in
`docs/audits/<date>-S<nnn>-<slug>/`.
*Why:* S225 rule; an unreviewed DDL on the shared instance hits every app, and live-only objects
(two RLS policies and `acp_shared.acp_output_rules`, review P3) are invisible to review.
*Enforced:* review; the DB Schema Dump drift report (AA-853), **report only, it fails nothing**: each night it replays
every applied migration into a scratch PostgreSQL and lists, in the *Schema drift* section of
`db-schema-reference.md`, the live objects no migration creates (unmanaged), the ones a migration creates that Dev
lacks (missing) and changed definitions, each with its owner decision from AA-CIS-Infra
`db/schema_drift_decisions.json` or marked **open**. The first runs are dominated by replay gaps (the `acp_*` history
of the AA-ACP-Core lineage is in no repo); the replay baseline file and the owner decisions are pending, and failing
on unmanaged objects waits for them.

**MIG-6 (MUST)** A migration touches only its owner's schemas, its own `schema_versions` row, and grants
on its own objects to consumer roles. It MAY create its own NOLOGIN roles idempotently (bk-001 pattern
`CREATE ROLE booking NOLOGIN` inside a guarded `DO` block). It MUST NOT create LOGIN roles, `ALTER ROLE`,
set passwords, or create SECURITY DEFINER functions (the only exception is SEC-4's, and never in Booking,
whose guard rejects them). Role attributes (LOGIN, `CONNECTION LIMIT`, role-level backstop timeouts)
live in the Infra role bootstrap (*to build*, **X1**; `schema-ownership.md` rule 3: Infra owns DB
roles); passwords never enter git. **Single interim exception (N3):** until X1 exists, one reviewed CIS
migration sets `CONNECTION LIMIT` and backstop timeouts on the existing runtime roles `tripplanner`,
`booking` and `aa_app_user`, with the TripPlanner and Booking owners approving their rows in that PR
(Part C **C2.3a**); the attributes move to the bootstrap with X1. Booking and TripPlanner files never
carry `ALTER ROLE`. Instance-level extensions (e.g. `pg_stat_statements`, **N3**) are created only
in a CIS migration (or by the bootstrap once the migrator no longer holds `rds_superuser`).
*Why:* ownership is a convention until **X1**; the migration review is the boundary.
*Enforced:* Booking migration guard (`no-login`, `no-alter-role`, `no-password`, `no-security-definer`,
`no-extension`, `create-role`); review for CIS/TP; **X2** (*to build*). The schema boundary is linted at copy time
for every owner by the Migration Copy Guard ownership lint (AA-853, AA-CIS-Infra `db/check_migration_ownership.py`):
a copy that creates, alters, drops, comments on, grants on or writes to an object outside its owner's schemas
(`db/owners.yaml`) fails, apart from its own `shared.schema_versions` row. It is a static lint: function bodies and
dynamic SQL (`EXECUTE`) are not read. The runtime boundary is the X1 owner-role switch of DB Migrate (a file runs as
its owner role, which holds no rights on other owners' objects).

**MIG-7 (MUST)** Expand/contract for every shape change: expand (add) → ship readers and writers on the
new shape → wait ≥ 14 days → contract (drop) in a separate migration under DRY RUN.
A rename is add + copy + switch + drop. One migration MUST NOT drop or rename something that deployed code still reads.
*Why:* there is no per-app rollback; PITR rolls back every app. *Enforced:* review; lint
(*to build*, **N5**).

**MIG-8 (MUST)** Files are idempotent: `IF NOT EXISTS`, `CREATE OR REPLACE` (views only append columns),
guarded `DO` blocks. A guard MUST `RAISE EXCEPTION` when a precondition is missing rather than no-op. A
cross-owner grant is **not** wrapped in `IF EXISTS (role)` (schema-ownership rule 5).
*Why:* a guarded no-op still registers its version, so the step is never retried (tp-008).
*Enforced:* Booking CI re-applies every migration; review.

**MIG-9 (MUST)** Every file starts with a header comment: `-- Migration <key>: <AA-xxx> — <what and why>`,
the lock-sensitive tables it touches, and its directives. Runner defaults (*to build*, **N5**):
`lock_timeout = '5s'`, `statement_timeout = '15min'`, `application_name = 'db-migrate'`, overridable by a
`-- migrate:` header. **Until N5 ships**, a file that ALTERs or indexes an existing table MUST start with
`SET LOCAL lock_timeout = '5s'; SET LOCAL statement_timeout = '15min';` right after `BEGIN;`.
*Why:* an ALTER queued behind a job-runner transaction blocks every reader of a hot table for all apps
(review P9). *Enforced:* review (grep); runner (*to build*, **N5**).

**MIG-10 (MUST)** `CREATE INDEX CONCURRENTLY`, `REINDEX CONCURRENTLY` and other statements that cannot run
in a transaction go in their own file with the header `-- migrate: no-transaction` (*to build*, **N5**):
one concern per file, every statement idempotent (`IF NOT EXISTS`), registration last, and the runner
executes the statements one by one. Once N5 ships, an index build or rebuild on a table > 100k rows
MUST use `CONCURRENTLY` (Part C C5.2c points here). **Until N5, DB Migrate cannot apply `CONCURRENTLY`
at all:** `run_migration.py` sends the whole file as one simple-protocol query, which PostgreSQL runs as
one implicit transaction block, so the statement fails ("cannot run inside a transaction block"). Until
then a plain `CREATE INDEX` is allowed on a table ≤ 100k rows, and on a table of 100k-1M rows only when
the build time was measured on Dev first (seconds) and the PR says so; both only with the MIG-9
`lock_timeout` and all job tables idle (MIG-4). An index on a table ≥ 1M rows waits for N5.
*Why:* a plain index build blocks writes for its whole duration. *Enforced:* review; aa-ship guard.

**MIG-11 (MUST)** Lock-safe DDL on existing tables with data: add `NOT NULL` via `CHECK (…) NOT VALID` →
`VALIDATE` → `SET NOT NULL`; add FKs and CHECKs `NOT VALID` then `VALIDATE` in a second statement; avoid
column type changes that rewrite the table (use expand/contract); a new column's default MUST be
non-volatile.
*Why:* each of these otherwise takes an ACCESS EXCLUSIVE lock for a full scan or rewrite.
*Enforced:* review; squawk lint (*to build*, **N5**).

**MIG-12 (MUST)** Destructive files (DROP TABLE/COLUMN/SCHEMA, DELETE or TRUNCATE of real data) carry
`-- migrate: destructive`, so DB Migrate takes a manual RDS snapshot first (*to build*, **N5**). Until then,
a manual snapshot is taken and named in the PR. All destructive work follows the DRY RUN procedure
(`skill/aa-cis-schema/references/destructive-ops.md`): exact counts shown to the tech lead, snapshot,
savepoint check, commit on approval, independent re-verify, a row in
`docs/architecture/dead-table-registry.md` (**N6**). A first step SHOULD be reversible quarantine
(`ALTER … SET SCHEMA retired`).
*Why:* a snapshot is the only undo that does not roll back every app. *Enforced:* review; DB Migrate
(*to build*); the destructive-ops skill.

**MIG-13 (SHOULD NOT)** Backfill or delete more than ~10k rows inside a migration. Large backfills and all
retention deletes run as owner job kinds, in batches.
*Why:* long transactions hold locks, bloat the table and hit `statement_timeout`. *Enforced:* review.

**MIG-14 (MUST)** There are no down migrations. An undo is a new forward migration; a destructive undo is
the snapshot from MIG-12.
*Why:* a down file that never ran in CI is untested code against the shared instance. *Enforced:* review.

---

## 4. Roles, grants and RLS

**SEC-1 (MUST)** Target role model per owner schema (review §4.1, **X1**): `<app>_owner` NOLOGIN owns every
object; `<app>_app` LOGIN is the runtime (no ownership, no `CREATEROLE`, no `BYPASSRLS`, not a member of
`rds_superuser`), with `CONNECTION LIMIT` and its own `application_name`; optional `<app>_reader` NOLOGIN
owns the contract views (the `catalog_owner` pattern); DB Migrate runs as `db_migrator` from its own task
definition and `SET ROLE <owner>` per directory. Order: `booking.*` → `bk_owner` and `tripplanner.*` →
`tp_owner` first; the CIS runtime moves to `cis_app` behind AA-817 D2; `aa_cis_admin` becomes break-glass.
New apps start in the target model.
*Why:* today `aa_cis_admin` is CIS API pool, worker, migrator and owner of every object, and inherits
`pg_read_all_data`/`pg_write_all_data` (review P1). *Enforced:* live probe (`aa817_probe.py`); **X2** guard;
review.

**SEC-2 (MUST)** The DSN of a runtime role lives in Secrets Manager at `<app>/<env>/database-url` and is set
by the tech lead by hand. ⚠️ This contains underscore env vars — edit manually in VSCode.
*Why:* secrets never enter git or agent output. *Enforced:* review.

**SEC-3 (MUST)** Grants are per object, issued by the owner in its own migration. New schemas MUST NOT use
`ALTER DEFAULT PRIVILEGES … GRANT … TO` any role; existing exceptions are in section 9. **Until N7
lands**, a CIS migration that creates a table in `shared`, `silver_aa_internal` or `gold_aa_internal`
that `aa_app_user` must not read (every tenant table without RLS, and all AA-813 membership tables)
MUST `REVOKE ALL ON <table> FROM aa_app_user` in the same file, then grant explicitly what is needed.
*Why:* the 007b default ACL auto-grants SELECT on every new `shared`/silver/gold table to `aa_app_user`,
including tenant tables with no RLS (review P2; removal **N7**, before AA-813 tables exist).
*Enforced:* review; **X2** default-ACL check and **N1** dump (*to build*).

**SEC-4 (MUST NOT)** Grant anything to `PUBLIC`. A function that must be SECURITY DEFINER (only with a
reason in the header) sets `search_path = pg_catalog, <schema>` and has `EXECUTE` revoked from `PUBLIC`.
*Why:* PUBLIC reaches every login, including other apps. *Enforced:* Booking migration guard; review.

**SEC-5 (MUST)** New consumer grants are `SELECT` on contract views only (CON-1), never on tables or
column lists and never write rights in another schema. The only standing write exception is `INSERT`
on `shared.llm_call_log` (ADR 0002 decisions 3-4), tagged with the calling app: today
`quality_signal.app` (CIS 173), the `app` column once AA-804 adds it. Views revoke
`INSERT/UPDATE/DELETE` from the app role (a simple view is auto-updatable). Existing table and column
grants (CIS 173/179/180/201/216, the `published_tours` SELECT) are grandfathered in section 9.
*Why:* a view is a contract the owner can keep while changing tables (ADR 0002 decision 2).
*Enforced:* Booking migration guard (views); **X2** grant allowlist from `owners.yaml` (*to build*).

**SEC-6 (MUST)** Every tenant table uses this template (review §4.4):

```sql
ALTER TABLE <schema>.<table> ENABLE ROW LEVEL SECURITY;
ALTER TABLE <schema>.<table> FORCE ROW LEVEL SECURITY;  -- new apps: always; CIS: only after the AA-817 D2 role split
CREATE POLICY <table>_tenant_isolation ON <schema>.<table>
    AS PERMISSIVE FOR ALL TO <app>_app
    USING      (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);
```

- `app.tenant_id` is the only GUC name. `app.current_tenant` (CIS 019/031) MUST NOT appear in new SQL.
- `NULLIF(…, '')` is mandatory: a pooled connection holds `''` after any `set_config(..., true)`
  transaction, and `''::uuid` raises instead of returning 0 rows.
- `WITH CHECK` is written out, never left implicit.
- `TO <role>` is mandatory; a policy without `TO` applies to `PUBLIC`. On CIS tables the tenant
  runtime role is `aa_app_user` (the tenant pool; 229 adds `TO aa_app_user`). The platform runtime role
  is `cis_app` (CIS api + worker since X1 S18, AA-860): it is not a tenant role and reads every row
  through `<table>_cis_app_all AS PERMISSIVE FOR ALL TO cis_app USING (true) WITH CHECK (true)` (CIS 244).
  A CIS migration that enables RLS on a table, ENABLE-only or FORCE, adds that policy in the same file,
  and on a FORCE table also `<table>_cis_owner_all TO cis_owner` (CIS 245: the owner is not exempt under
  FORCE and owns the views that read the table); without it the runtime reads 0 rows. *Enforced:* CIS CI
  standing checks (`tests/integration/test_x1_cis_app_privileges.py`) and the isolation probe cells
  `rls.enable_only_has_cis_app_policy` and `rls.force_parity.cis_app`.
- New policies are named `<table>_tenant_isolation`; a migration that replaces an existing policy MAY
  keep its old name.

*Why:* 6 live policies cast without NULLIF, 2 GUC names exist, `acp_shared.facts` has no WITH CHECK
(review P3). *Enforced:* AA-817 isolation test; **X2** guard (*to build*); review.

**SEC-7 (MUST)** FORCE is on from day one for new apps. On CIS tables FORCE waits for the role split
(D2: migration 229 = ENABLE without FORCE, owner stays exempt).
*Why:* without FORCE the owner is exempt; on CIS today FORCE would make the worker and admin read 0 rows.
*Enforced:* review; **X2**.

**SEC-8 (MUST)** Permissive policies OR together. A table has one tenant policy; any extra read path
(AA master rows, admin, support) is a separate policy scoped `TO` a different role (pattern
`catalog_owner_aa_master_read`, CIS 225) or a `RESTRICTIVE` policy. When a migration replaces a policy, it
`DROP POLICY IF EXISTS` every old name explicitly, including live-only ones. Every live policy exists in a
migration.
*Why:* draft 229 would have left `tenant_tour_versions_isolation` in place to OR with the new policy; two
live policies exist in no migration (review P3, fix **N2**). *Enforced:* review; drift check (*to build*, **N1**).

**SEC-9 (MUST)** Where platform and tenant rows share a table (NAM-10), SELECT may include platform rows,
but INSERT/UPDATE/DELETE policies check `scope = 'tenant' AND tenant_id = NULLIF(...)::uuid`.
*Why:* the `acp_shared.facts` write gap lets a tenant session write facts every tenant cites.
*Enforced:* isolation test write cases (TST-4).

**SEC-10 (MUST)** The tenant context is set only after the app has checked the caller's active membership,
inside a transaction, with `set_config('app.tenant_id', $1, true)` (transaction-local), never a
session-level `SET` on a pooled connection. A request path that needs the tenant pool **fails closed**
(503) when that pool or its tenant context is missing; it never falls back to another role's pool. A
non-owner app MUST NOT set the AA master tenant id on its own connection to read master content; it
reads `catalog.*`.
*Why:* a self-asserted GUC is not an authorization boundary (TripPlanner `backend/shared/catalog_rls.py`
`set_catalog_tenant`, review P7), and a silent fallback to the master pool turns RLS off (review P2).
*Enforced:* review; isolation probe. The transaction-local GUC pattern is
`apps/AA-CIS-App/api/core/aa544_tenant_pool.py` (`acquire_scoped_conn`). Its flags fail closed globally since S241 D-12
(an unreadable flag means the tenant pool): only an explicit `"false"`, or the emergency variable
`TENANT_POOL_FORCE_ADMIN_FLAGS`, moves one route to the admin pool, as an operator rollback (Part B DM-8.4)
that section 9 still lists until the last route's flag is retired.

**SEC-11 (MUST)** Every LOGIN role except the RDS master `aa_cis_admin` (break-glass, Part C C2.3b) has a
`CONNECTION LIMIT` set in git and changed only through review: for `tripplanner`, `booking` and
`aa_app_user` by the N3 interim CIS migration (MIG-6), for every later role in the Infra role bootstrap
(**X1**). The values live only in the Part C **C2.2** budget table (a new `<app>_app` gets a C2.2 row in
its playbook PR).
*Why:* one app's burst must not exhaust `max_connections` for all three (review P4).
*Enforced:* PostgreSQL itself; the connection alarms of Part C **C4.1** (*to build*, **N3**).

**SEC-12 (SHOULD)** Until the role split lands, document in the design that new-schema isolation is
partial: `aa_cis_admin` can still read and write it through `pg_read_all_data`/`pg_write_all_data`.
The split landed with **X1** (2026-10-19): `aa_cis_admin` is break-glass only (Part B DM-8.9), so a new design
names the master as break-glass instead (ADR 0008a decision 1).
*Why:* honest blast radius for reviewers (review §6.4). *Enforced:* review.

---

## 5. Views and contracts

**CON-1 (MUST)** Cross-app reads go only through contract views:

- the CIS read model in `catalog` (`catalog.v_<entity>`, owner `catalog_owner`). New CIS contract
  views of any kind go here, including tenant-facing ones (e.g. the AA-813 membership view) and
  read-backs such as ADR 0004a's CIS → Booking supply content view (named `shared.v_supply_content`
  there only as an example). No new contract schema is created;
- a non-CIS producer's current-state views in its own schema, `<schema>.v_<entity>` (ADR 0004a:
  `booking.v_supply_hotels`, `booking.v_supply_services`);
- event views `<schema>.v_<event>_outbox` (e.g. `tripplanner.v_inquiry_outbox`; planned
  `booking.v_supply_outbox`, `booking.v_trip_case_status_outbox`).

This narrows ADR 0001 decision 6, which also allowed direct reads of `shared.*` golden records: new
readers use `catalog` views of them (`catalog.v_destination`, a country view with **X5**); existing
direct reads are grandfathered in section 9.
*Why:* one place per producer to keep a contract stable (ADR 0001 decision 1, ADR 0002 decision 2,
ADR 0007 decision 2). *Enforced:* SEC-5 grants; **X2** grant allowlist (*to build*).

**CON-2 (MUST)** A contract view is owned by a NOLOGIN role (CIS: `catalog_owner`; other producers: their
`<app>_owner` or `<app>_reader` from **X1**; until X1 the migrator `aa_cis_admin` owns Booking and
TripPlanner views, grandfathered in section 9), is created `WITH (security_barrier)` when it
filters rows, lists its columns explicitly (no `SELECT *`), and derives liveness by joining the
authoritative view (`catalog.v_tour`) instead of a stored flag. A view over FORCE-RLS tables needs its
owner role plus a role-scoped policy (CIS 225 pattern).
*Why:* `aa_cis_admin` is not BYPASSRLS, and `SELECT *` silently changes the contract when a table changes.
*Enforced:* review; `test_aa679_catalog_views.py` (`rds_like_225`).

**CON-3 (MUST)** A published view only appends columns (`CREATE OR REPLACE VIEW` cannot reorder or retype).
Remove, rename, retype or narrow means a new major: a second view (SHOULD be `v_<entity>_v<major>`),
both served for the agreed window (default 30 days), the old one dropped after every consumer confirms.
*Why:* `docs/contracts/README.md` rule 2. *Enforced:* PostgreSQL rejects reorder/retype; review.

**CON-4 (MUST)** Every contract has a JSON Schema `docs/contracts/<name>.v<major>[.<minor>].json` and a
registry row in `docs/contracts/README.md`, added in the **same** PR as its view or outbox. A published
file is never edited except for a description typo. Payloads that could leak internal data use
`additionalProperties: false` (ADR 0004a decision 3).
*Why:* the registry is how consumers find the current version. *Enforced:* review; producer CI validates a
sample payload, consumer CI parses the same sample (README rule 7); hash guard on consumer copies, e.g.
`apps/AA-TripPlanner-Web/backend/tests/contracts/catalog.tour.v1.json` (*to build*, **X7**).

**CON-5 (MUST)** Versioning:

- **Minor (additive):** a new field the consumer may ignore, a wider enum, a field becoming nullable.
  The producer may send it at once; consumers accept every minor of their major.
  Approved example: `inquiry.submitted` v1.2 adds `source_system` + `source_id` per leg (**X3**).
- **Major (breaking):** removing, renaming or narrowing a field, changing its type or meaning, or changing
  the key or idempotency semantics. Dual-write two majors (CON-3).

*Why:* consumers deploy on their own schedule. *Enforced:* review against README rule 2.

**CON-6 (MUST)** Consumers detect catalog changes by `content_hash`, not `updated_at`; event pulls do not
use the producer's BIGSERIAL id as the only cursor (anti-join against the inbox, or a lag window).
*Why:* in-place edits do not move `updated_at`; out-of-order commits skip ids (README rules 4 and catalog row).
*Enforced:* review; consumer integration tests.

**CON-7 (MUST)** Outbox rows are written in the same transaction as the state change. An outbox view
selects only the rows of its own contract (ADR 0004a decision 4, `booking.v_supply_outbox`, planned). Payloads carry
ids, not PII, wherever the consumer can resolve the id; every event has an `idempotency_key`; the consumer
inbox has `UNIQUE (source, contract, idempotency_key)` and processes each key once; the pull job kind is
`<prefix>_<event>_pull` (e.g. `bk_inquiry_pull`). Status flows back as the consumer's own event, never a
write into the producer's schema.
*Why:* outbox → pull → inbox is the approved transport (ADR 0001 decision 6). *Enforced:* review; Booking
inquiry intake tests.

**CON-8 (MUST)** Another app reads LLM cost only through the shared rollup (`shared.llm_call_daily`,
*to build*, **N4**) filtered by `app`, never `shared.llm_call_log` rows; it does not build its own spend
table (`tripplanner.llm_spend_daily` retires once the rollup exists). The gateway contract itself
(config reads, `app` and shadow columns) belongs to ADR 0009 (AI platform, AA-804).
*Why:* the raw ledger is CIS-private and keeps raw rows for 180 days, then only the daily rollup (approved
retention, Part B §7). *Enforced:* SEC-5 grants.

---

## 6. Queries, indexes and connections

**QRY-1 (MUST)** Predicates on indexed columns are sargable: `called_at >= $1 AND called_at < $2`, never
`date_trunc('month', called_at) = $1`; no function or cast on the column side unless a matching expression
index exists; normalised lookups use a stored `*_norm` column (`shared.destinations.name_norm`).
*Why:* `v_tenant_monthly_usage` (CIS 223) scans `tenant_api_usage` twice per tenant (review P5, fix **N4**).
*Enforced:* EXPLAIN in the PR (QRY-3); review.

**QRY-2 (MUST)** Every FK column, every soft key, and every column used in a hot-path filter, join or sort
has an index. Composite indexes put equality columns first, then the range (`(tenant_id, called_at)`).
Queue and status lookups SHOULD use partial indexes (`WHERE status = 'queued'`).
*Why:* PostgreSQL does not index the referencing side of an FK. *Enforced:* review; unused/missing index
report in the **N1** dump (*to build*).

**QRY-3 (MUST)** A new or changed view, and any new query on a table with > 10k rows, has
`EXPLAIN (ANALYZE, BUFFERS)` from Dev (or a realistic seed) pasted in the PR. A covering index counts only
when the plan shows `Index Only Scan` and `Heap Fetches: 0`.
*Why:* lesson S218/AA-660 (`skill/aa-lessons/lessons.md`): a covering index did nothing because of
`count(l.id)`. *Enforced:* review checklist.

**QRY-4 (MUST NOT)** Call an LLM, Jev, an HTTP API or S3 while a transaction is open or while holding a
pooled connection. Pattern: read and release → call → write in a new short transaction that re-checks its
precondition (ADR 0007: re-check the live version under `SELECT … FOR UPDATE` before persisting).
*Why:* a seconds-long call holds locks and a scarce connection; `idle_in_transaction_session_timeout = 60s`
(**N3**) will kill it. *Enforced:* review; the `idle_in_transaction` timeout (*to build*, **N3**).

**QRY-5 (MUST)** Every pool sets an `application_name` (Part C C1.1a) and, in its own asyncpg
`server_settings`, a `statement_timeout` below its caller's timeout and a `lock_timeout`, with the
per-pool values only in the Part C **C2.2** table. Job workers use per-kind `SET LOCAL` instead of a
pool value. A role-level `ALTER ROLE … SET` is only a backstop on single-purpose roles (Part C
**C2.3f**), set where MIG-6 allows role attributes. Pools also keep a client-side `command_timeout`
(TripPlanner `backend/shared/db.py` already uses 30 s) and fail fast on exhaustion (Part C C2.3g).
*Why:* no pool sets a server timeout today; one runaway query can hold a connection indefinitely.
*Enforced:* review; slow-query log at 500 ms (*to build*, **N3**).

**QRY-6 (MUST)** Connection budget: worst case `Σ pool max_size × max tasks or instances` (with deploy
overlap) stays within the Part C **C2.1** ceiling, and a PR that changes a pool size, ECS
`max_capacity`/`worker_max_count`, Lambda reserved concurrency or the instance class updates the C2.2
table in the same PR (C2.3c). Lambda pools use max 1 per instance (C2.3d); the `tripplanner` limit, pool
max 1 and the reserved-concurrency Terraform ship **before** the Lambda concurrency quota of 1000 is
applied (approved, C2.3e). RDS Proxy is added only at its trigger (**L7**). Today's worst case breaks
this rule and is grandfathered until **N3** (C2.1).
*Why:* worst-case pool demand already exceeds `max_connections` (review P4). *Enforced:* SEC-11 limits;
C2.2 table and an over-budget CI script (*to build*, **N3**); alarm.

**QRY-7 (SHOULD NOT)** Rely on session state (session-level `SET`, temp tables, session advisory locks,
`LISTEN`) in request paths.
*Why:* keeps RDS Proxy possible without pinning, and pooled connections clean. *Enforced:* review.

**QRY-8 (MUST)** Job queues claim with `FOR UPDATE SKIP LOCKED` (as `shared/jobs/queue.py`). Each owner
has its own job table in its own schema (`shared.job` for CIS, `booking.job`, `crm.job`, a new app's `<app>.job`)
with a kind prefix per app; no app enqueues into another owner's job table. This is
[ADR 0003a](../../adr/0003a-per-owner-job-tables.md) (accepted 2026-10-15), which supersedes ADR 0003
decision 4 ("non-CIS repos enqueue into `shared.job`") and the premise of AA-751; the shared DDL
template in `shared/jobs` is *to build* (**X6**). Until the template exists, a new job table copies the
`shared.job` columns of CIS 174 (including `cancel_requested`, `progress`, `cost_usd`, `parent_job_id`).
*Why:* one job model shape, per-owner isolation. *Enforced:* review; job runner tests.

**QRY-9 (MUST)** Bulk writes use `executemany`, `unnest` or `COPY`; large lists use keyset pagination on
`(created_at, id)`, not `OFFSET`; retention and cleanup DELETEs run in batches (Part C C5.4c) inside owner
job kinds, only after the S3 Parquet archive where Part B §7 requires one, and never use `VACUUM FULL`.
*Why:* row-by-row writes and deep OFFSETs grow with the table; `VACUUM FULL` takes an exclusive lock.
*Enforced:* review.

**QRY-10 (MUST)** Application SQL names its columns (no `SELECT *` against another owner's view, and SHOULD
NOT against own tables in request paths), and is plain parameterised SQL (no string-built identifiers from
input).
*Why:* contract columns are append-only, so `*` drifts; injection safety. *Enforced:* review; a SQL
lint is *to build* (**N5**).

**QRY-11 (MUST NOT)** Share one connection between concurrent tasks (`asyncio.gather`, a semaphore of
workers, parallel stages). A job that fans out opens a real pool (pattern `open_job_pool`,
`apps/AA-CIS-App/services/export/handler.py`), sized inside the Part C C2.2 budget.
*Why:* S219: A3/recompute ran on `_SingleConnAsPool` while the Jev gate called `decide()` on 8 tasks,
which raised "another operation is in progress" thousands of times and lost cost and cache writes
(`skill/aa-lessons/lessons.md`, Job runner section; AA-756). *Enforced:* review; CloudWatch
`decide_config_unavailable` and `*_log_write_failed` = 0 after each recompute.

---

## 7. Testing

**TST-1 (MUST)** Every owner's CI applies **all** its migrations in order to a real `postgres:15` service
(the RDS major version) on each PR: CIS as superuser `cistest` (`apps/AA-CIS-App/tests/integration/`),
Booking as `aa_cis_admin` (a superuser in CI) with a second apply for idempotency and no skips allowed.
TripPlanner has no migration integration job today: a gap the review's roadmap does not cover (no
N/X/L id), so it is an open item for the tech lead; until it exists, a TripPlanner migration PR states in its
description how it was applied to a local `postgres:15`.
*Why:* a migration that never ran on PG15 in CI is first tested on the shared instance. *Enforced:* CI.

**TST-2 (MUST)** A PR that adds a migration adds a test asserting its objects, constraints and policies
exist and behave. Tables that exist only live are pre-created in `conftest.py` in their live shape rather
than letting the migration fail.
*Why:* the CIS `_apply_schema` swallows migration errors, so 107/108/109/128/175/223 always failed silently
in CI (AA-817 §3). *Enforced:* review; the new test fails without the migration.

**TST-3 (MUST)** A test that depends on RLS, ownership or grants also runs as an RDS-like role
(NOSUPERUSER, NOBYPASSRLS, owner), following the `rds_like_225` fixture in `test_aa679_catalog_views.py`.
*Why:* a superuser bypasses RLS, so superuser-only tests prove nothing about isolation.
*Enforced:* review.

**TST-4 (MUST)** Isolation tests for every tenant table reachable by a runtime role: as that role, a
**WHERE-less** SELECT, UPDATE and INSERT under own / foreign / forged / empty `app.tenant_id` returns or
touches only the own tenant's rows (0 for forged or empty), and cross-tenant INSERT or hand-over is refused.
A mutation check (`USING (true)` or `WITH CHECK (true)`) must make the test fail. A new app also runs the
live probe (`aa817_probe.py`-style matrix) on Dev as `<app>_app` before its first tenant, with 0
cross-tenant rows.
*Why:* WHERE clauses are the only isolation on most routes today (review P2).
*Enforced:* `test_aa817_rls_tenant_isolation.py` pattern; playbook step 12.

**TST-5 (MUST)** The catalogue guard runs in CI and against Dev in the dump step (*to build*, **X2**; until
then the section 8 checklist): no tenant table without RLS unless in `NO_RLS_ALLOWLIST = {table: reason}`;
no PUBLIC policy in new schemas; no `app.current_tenant`; NULLIF present; no cross-owner FK; non-owner
grants match the `owners.yaml` allowlist; no default ACL to an app role in new schemas.
*Why:* a new tenant table must choose RLS or justify itself in review (AA-817 §4). *Enforced:* CI (*to build*).

**TST-6 (MUST)** Contract tests: the producer validates a sample payload against the JSON Schema; the
consumer parses the same sample; consumer copies pass the hash guard (*to build*, **X7**).
*Why:* `docs/contracts/README.md` rule 7. *Enforced:* CI in both repos.

**TST-7 (SHOULD)** After a deploy that adds hot queries, check `pg_stat_statements` (**N3**) for statements
over 200 ms mean on the primary path, and record the result in the PR or session log.
*Why:* QRY-3 covers the plan, not real load. *Enforced:* aa-ship live verify.

---

## 8. Review checklist for any PR that touches SQL

Copy into the PR description and tick or answer "n/a + reason".

**Placement and ownership:**

- [ ] The file is in the owner repo of every schema it touches; nothing outside the owner's schemas (MIG-6)
- [ ] Expand file (`-- migrate: expand`): file + code + readiness raise in one PR, Migration preflight green; otherwise migration-only PR (D8) and the code in a later PR (MIG-4)
- [ ] Number unique for the owner, 3 digits, correct key prefix, self-registers with `ON CONFLICT DO NOTHING` (MIG-1–3)

**Shape:**

- [ ] New objects not in `public`; no new CIS-private table in `shared` (NAM-2)
- [ ] `uuid` PK for entities / identity PK for logs; `timestamptz`; text + CHECK, no new enum (NAM-4–7)
- [ ] Filter/group fields are columns, not jsonb keys (NAM-9)
- [ ] Tenant tables: `tenant_id uuid NOT NULL` on the table itself; no NULL-tenant mixing without `scope` (NAM-10)
- [ ] PII columns tagged `pii:<class>; …` (Part B DM-6.1 classes); no clear-text tokens; no password/OTP/session tables (NAM-12–14)
- [ ] Log/event/outbox/job table: retention row in Part B §7 + TTL index (NAM-15)
- [ ] No cross-owner FK; tours keyed by `(source_system, source_id)`; canonical job/audit/place/country form reused (KEY-1, KEY-3, KEY-9)

**Safety:**

- [ ] Header with issue, purpose, touched tables; `SET LOCAL lock_timeout/statement_timeout` until **N5** (MIG-9)
- [ ] Expand/contract respected; nothing dropped that deployed code reads (MIG-7)
- [ ] Idempotent; guards raise; cross-owner grants unguarded (MIG-8)
- [ ] Lock-safe DDL (NOT VALID → VALIDATE; no rewrite; CONCURRENTLY only after **N5**, until then plain index on a small table with jobs idle) (MIG-10, MIG-11)
- [ ] No LOGIN role, `ALTER ROLE`, password or SECURITY DEFINER in the migration (only the N3 interim CIS limits file may `ALTER ROLE`); role attributes in the Infra bootstrap (MIG-6)
- [ ] Contract file: all job tables idle before the manual `apply` (expand files skip it); reference introspected live if older than the objects used (MIG-4)
- [ ] Destructive: snapshot named, DRY RUN counts shown to the tech lead, dead-table registry row (MIG-12)
- [ ] No large backfill or retention delete in the migration (MIG-13)

**Security:**

- [ ] Per-object grants only; no default ACL to an app role; nothing to PUBLIC; until **N7**, `REVOKE ALL … FROM aa_app_user` on new shared/silver/gold tables it must not read (SEC-3, SEC-4)
- [ ] Consumers get SELECT on views only, no table or column grants (SEC-5)
- [ ] RLS template exactly: `app.tenant_id`, NULLIF, explicit WITH CHECK, `TO <role>`; FORCE for new apps (SEC-6, SEC-7)
- [ ] Replaced policies dropped by every old name; extra read paths role-scoped or RESTRICTIVE (SEC-8)
- [ ] Tenant context set transaction-locally after a membership check; pool fails closed, no fallback pool (SEC-10)
- [ ] New LOGIN role has a `CONNECTION LIMIT` and a row in Part C C2.2 (SEC-11, QRY-6)

**Contracts:**

- [ ] View in `catalog` (CIS), `<schema>.v_<entity>` (non-CIS producer) or `<schema>.v_<event>_outbox`; NOLOGIN owner; explicit columns; append-only change (CON-1–3)
- [ ] JSON Schema + registry row in the same PR; minor vs major decided (CON-4, CON-5)

**Queries:**

- [ ] Sargable predicates; index for every FK, soft key and hot filter (QRY-1, QRY-2)
- [ ] `EXPLAIN (ANALYZE, BUFFERS)` pasted for new/changed views and queries on > 10k-row tables (QRY-3)
- [ ] No LLM/HTTP/S3 call inside a transaction or while holding a connection; no connection shared by concurrent tasks (QRY-4, QRY-11)
- [ ] Pool timeouts and connection budget unchanged, or Part C C2.2 updated in the same PR (QRY-5, QRY-6)

**Tests and docs:**

- [ ] Migration test asserting the new objects; RDS-like role for RLS/grant tests (TST-2, TST-3)
- [ ] Isolation cases for every new tenant table (TST-4)
- [ ] `db-schema-reference.md` regenerated after apply: the DB Schema Dump PR is merged (MIG-4 contract step 5 or the Migration Apply dump, **N1**)
- [ ] `schema-ownership.md`, `CONTEXT.md` and the contracts registry updated if ownership or a contract changed

---

## 9. Grandfathered exceptions

Each row is allowed to stay until its item lands. New code MUST NOT copy any of them.

| Legacy state | Rule it breaks | Retired by |
|---|---|---|
| CIS 007b `ALTER DEFAULT PRIVILEGES` in `shared`/silver/gold to `aa_app_user` | SEC-3 | **N7** (before AA-813 tables) |
| Booking default privileges `FOR ROLE bk_owner IN SCHEMA booking … TO booking` (bk-001's rows, restated by bk-014) and TripPlanner `FOR ROLE tp_owner IN SCHEMA tripplanner … TO tripplanner` (tp-013, restating rows that existed `FOR ROLE aa_cis_admin`); the Booking migration guard requires its rows | SEC-3 | stay until per-object grants replace them (no roadmap id) |
| **XD3:** CIS default privileges `FOR ROLE cis_owner IN SCHEMA <the 11 CIS runtime schemas> … TO cis_app` (tables DML, sequences, functions; CIS 244 for the master, restated by 245) | SEC-3, Part B DM-8.3 | stays: approved exception (X1 plan XD3, S241). `cis_app` is CIS's own runtime, not a consumer; a CIS migration that forgot a per-object grant would give the runtime 42501 after deploy. Never `catalog`, never another owner's schema or role; `shared.schema_versions` stays read-only for `cis_app` (244 REVOKE). Reviewed in the DM-8.10 access review |
| Live-only policies `gold_aa_internal.tenant_tour_versions_isolation`, `acp_shared.acp_output_rules.output_rules_rls` | SEC-8 | **N2** (229 drops the first explicitly) |
| Policies on `app.current_tenant` (CIS 019/031); `::uuid` casts without NULLIF (CIS 004/008); `acp_shared.facts` without WITH CHECK | SEC-6, SEC-9 | **AA-817** follow-up migrations |
| CIS tenant tables with ENABLE but no FORCE (D2) | SEC-7 (new apps only) | after the CIS role split |
| `acp_shared.angle_gate_option` without `tenant_id` | NAM-10 | when its route moves to the tenant pool (AA-817 §5) |
| TripPlanner: 12 FKs into `shared.destinations`; direct reads of `published_tours` (self-set master GUC), `raw_tours`, `shared.destinations`; CIS `photo_sync` reading frozen TP tables | KEY-1, SEC-10, CON-1 | **X4** (AA-712) |
| Table/column grants to `tripplanner`: CIS 173 (gateway tables), 179 (`raw_tours` columns), 180/216 (atoms), 201 (destinations, photo views), the `published_tours` SELECT | SEC-5 (`schema-ownership.md` rule 2 allowed them) | **X4** revoke migration; the gateway-config SELECT (`llm_role_config`, `llm_model_catalog`) stays until ADR 0009 (AA-804) defines the gateway contract |
| Contract views in `shared`: `shared.v_tour_photos`, `shared.v_destination_photos` (ADR 0002, CIS 200) | CON-1 | retired once TripPlanner reads `catalog.v_*_photo` (**X4**) |
| CIS tenant pool: an explicit `"false"` flag value (Redis, immediate) or the emergency variable `TENANT_POOL_FORCE_ADMIN_FLAGS` (task definition, durable, needs a redeploy) moves one route to the admin pool (operator rollback, Part B DM-8.4). Missing or unreadable flags and a missing pool fail closed since S241 D-12 (CIS #792) | SEC-10 | AA-817 / AA-859 (retire the flags route by route) |
| CIS 007b creates login role `aa_app_user` in a migration | MIG-6 | **X1** (role definitions moved to the Infra bootstrap) |
| `shared.admin_users.password_hash`; `booking.customer_otps`, `booking.customer_sessions` | NAM-14 | ADR 0006 Phase 1 (AA-816) / Phase 4 (a later `bk-NNN` drop) |
| `tripplanner.llm_spend_daily` (own spend table) | CON-8 | after `shared.llm_call_daily` (**N4**) |
| Connection worst case above the C2.1 ceiling; no `CONNECTION LIMIT` on any role | QRY-6, SEC-11 | **N3** (before the Lambda quota of 1000) |
| `inquiry.submitted` v1/v1.1 carry `tour_id`; TP `source_tour_id` mixes key types | KEY-3 | **X3** (v1.2) |
| CIS duplicate numbers 007, 008, 019 and the `007b` suffix | MIG-3 | registry note (no renumbering) |
| `run_migration.py` without timeouts, no-transaction mode or snapshot | MIG-9–12 | **N5** |
| `v_tenant_monthly_usage` `date_trunc` predicates; `llm_call_log` app/shadow in jsonb | QRY-1, NAM-9 | **N4**, **AA-804** |
| Legacy enum types in `public`; `varchar`/`text` `tenant_id` on retirement candidates | NAM-7, NAM-10 | stay / **L1** retirement |
| CIS-private ops tables in `shared` (`decision_log`, `tenant_api_usage`, cost snapshots, `job`) | NAM-2 | stay; no new ones |
| `tripplanner.sessions.guest_token = id::text` | NAM-13 | **X8** (before ADR 0006 Phase 4) |
| PII copied across `tripplanner.customers`, outbox/inbox payloads and `booking.customers`, untagged | KEY-5, NAM-12 | **L3** (redaction after 90 days per the approved retention) |
| No TripPlanner migration integration test | TST-1 | open item for the tech lead (not in the review roadmap; no N/X/L id) |

**Retired rows** (kept here so a reader of an old link finds where they went):

| Legacy state | Retired by (evidence) |
|---|---|
| `aa_cis_admin` is CIS API pool + worker + DB Migrate + owner of every object, incl. `booking.*` and `tripplanner.*` (SEC-1) | **X1**, done 2026-10-19 (AA-852 / AA-860): CIS api + worker log in as `cis_app` (S18), the CIS task role is denied the master secret (S19), the 12 CIS schemas belong to `cis_owner` (CIS 245, S21), DB Migrate / DB Schema Dump / DB Isolation Probe log in as `db_migrator` (S22). The master is break-glass plus `roles/`, `set-password` and `run-script` (Part B DM-8.9). Probe after S22: 58/58 cells pass |
| Booking `bk-001` default privileges `FOR ROLE aa_cis_admin IN SCHEMA booking … TO booking` (SEC-3) | **X1** S6/S8: bk-014 restates them `FOR ROLE bk_owner` and revokes the `aa_cis_admin` rows; the Booking guard takes the role per file. The `bk_owner` rows stay as a grandfathered row above |
| Booking job table: no deploy job guard in `deploy-dev.yml` (MIG-4) | AA-751 B3/B4: the Booking Deploy Dev `preflight` job calls `/booking/ops/deploy-gate`; since AA-993 G5 it blocks only on deploy-blocking `booking.job` kinds (Part C C6.3a) |
| Booking and TripPlanner objects and views owned by `aa_cis_admin` (the migrator), not a NOLOGIN owner (SEC-1, CON-2) | **X1** S6–S8: bk-014 → `bk_owner`, tp-013 → `tp_owner` (live dump: schema `booking` owner `bk_owner`, `tripplanner` owner `tp_owner`) |
