# ADR 0008 — New-app integration and data platform rules

- **Status:** Accepted (15/10/2026, S237 — Nghiệp approved every recommendation of the S237
  data-architecture review, "đồng ý duyệt hết", decisions E1–E11 in
  `docs/audits/2026-10-14-S237-lane-backlog/00-orchestrator-journal.md`).
- **Amendment proposed:** [ADR 0008a](0008a-crm-separate-app-exceptions.md) (Proposed 22/10/2026, S247): the
  partner CRM is a separate app (AA-Partner, ADR 0010), with playbook exceptions for traveller OTP (step 8) and an
  own LLM gateway (step 9); decision 8 preconditions and hand-off rewritten.
- **Scope:** AA-Ecosys as a whole: every app that stores data on the shared PostgreSQL 15 RDS
  (`aa-cis-dev-db`, acc2 `005097885195`, us-west-1, and the later prod instance on acc2):
  AA-CIS-App, AA-TripPlanner-Web, AA-Booking, AA-CIS-Infra (instance, roles, DB Migrate), and any app
  that joins later (first candidate: tenant CRM, AA-821).
- **Rule body:** the data standards v1.0 in `docs/architecture/data-standards/`
  ([`README.md`](../architecture/data-standards/README.md) with the golden rules;
  [Part A engineering](../architecture/data-standards/01-engineering.md),
  [Part B data management](../architecture/data-standards/02-data-management.md),
  [Part C operations and scaling](../architecture/data-standards/03-scaling.md)). This ADR records the
  decisions; the standards hold the detailed, enforceable rules.
- **Implements:** ADR 0001 decision 6 (contracts between apps), ADR 0002 (only CIS writes content),
  ADR 0006 (identity), ADR 0007 decision 2 (`catalog.*` views are the contract).
- **Amends / tightens:** ADR 0001 decision 6 and `docs/database/schema-ownership.md` rule 2 (decision 5
  below); ADR 0003 decision 4 through `0003a-per-owner-job-tables.md`.
- **Design:** `docs/audits/2026-10-14-S237-lane-backlog/data-architecture/README.md` ("the review"),
  §4 target architecture, §6 onboarding a new app, §7 roadmap (ids N1–N7, X1–X10, L1–L10). RLS rollout:
  `docs/audits/2026-10-14-S237-lane-backlog/aa817/aa817_design.md` (decision D2).
- **Linear:** project "Data Platform — Schema, Ops & Scale": AA-824 (N3), AA-825 (N4), AA-826 (X7,
  this ADR's tooling), AA-827 (X8), AA-828 (X9), AA-829 (X10); AA-807 (N1, N5, N6, X1, X5), AA-817 (N2,
  N7, X1 CIS runtime, X2), AA-712 (X4), AA-751 (X6), AA-821 / AA-813 (L10).

## Context

Three apps share one RDS instance with a schema per owner. The logical design is mostly right (one
owner per schema, prefixed version keys `NNN` / `tp-NNN` / `bk-NNN`, `catalog.*` views, TripPlanner →
Booking outbox/inbox, no Booking cross-schema FK), but the review found that most of it is convention,
not permission or automation:

- `aa_cis_admin` (the RDS master) is the CIS API pool, the worker, the DB Migrate runner and the owner
  of every object, including `booking.*` and `tripplanner.*`, and inherits `pg_read_all_data` /
  `pg_write_all_data` (P1).
- Tenant isolation lives mostly in WHERE clauses; the 007b default ACL auto-grants new
  `shared`/silver/gold tables to `aa_app_user`; two live RLS policies exist in no migration (P2, P3).
- The instance (`db.t3.micro`, 20 GB, no autoscaling, no Performance Insights) and the connection
  worst case (~235 against ~85) only hold because the Lambda quota is 10 (P4). Nothing is retained or
  rolled up (P5).
- The tour key differs across contracts (P6); TripPlanner still reads CIS tables directly and holds 12
  FKs into `shared.destinations` (P7); customer PII is copied 4 times (P10); four job models and two
  photo-view layers coexist (P11).

A fourth app (the tenant CRM, AA-821) would land in the same blast radius unless the rules exist first.

## Decisions

### 1. Platform shape: one instance per environment, every schema liftable

- Keep **one RDS instance per environment** with a schema per owner. A database per app would double
  cost and add contracts for no benefit at today's volume. Prod is a separate instance on acc2
  (ADR 0001 amendments S235), built by roadmap **L9**.
- Operate every schema **as if it could be lifted into its own database**:
  - no FK between owners; cross-app references are soft keys;
  - cross-app reads only through contract views;
  - cross-app state changes only through outbox → pull job → inbox;
  - writes into another app's domain only through its HTTP API;
  - one NOLOGIN owner role per schema, non-owner runtime roles.
- Existing schema names stay; the conventions bind **new and changed** objects. Legacy exceptions are
  listed once, in Part A §9, each with the roadmap item that retires it.

### 2. Decision gate for a new app (answer before any schema or role)

1. **Does the app own data that nobody else owns?** If not, it is an API client of an existing app: no
   schema, no DB role (a mobile app → TripPlanner/Booking APIs; a supplier portal → Booking, which owns
   suppliers under ADR 0005; a BI tool → exports, never the RDS).
2. **Is it a new capability of an existing domain?** Then it is a module and tables in that owner's
   schema, under that owner's migrations.
3. **Is it a new domain with its own lifecycle?** Then it gets its own schema and the playbook below.

The gate's answer and the owning repo are written in a design doc in
`docs/audits/<date>-S<nnn>-<slug>/` that cites this ADR, and Nghiệp approves it.

### 3. Playbook for a new domain (12 steps)

1. **Design and ADR** (gate answered, owning repo named, Nghiệp's approval).
2. **Register the owner** in `infra/AA-CIS-Infra/db/owners.yaml` (*to build*, **X1**): dir, repo, path,
   key prefix, owner role, runtime role(s), allowed consumer grants, job-kind prefix. Until it exists,
   one Infra PR updates `db-migrate.yml`, `check_migration_copies.py` (`OWNERS`, `PATH_RE`) and
   `schema-ownership.md` together.
3. **Roles in a reviewed bootstrap, never by hand:** `<app>_owner` NOLOGIN, `<app>_app` LOGIN with a
   `CONNECTION LIMIT` and its own `application_name`, optionally `<app>_reader` NOLOGIN owning the
   app's contract views. The DSN goes to Secrets Manager at `<app>/<env>/database-url`, set by Nghiệp by
   hand. ⚠️ This contains underscore env vars — edit manually in VSCode.
4. **First migration `<prefix>-001`** through the D8 flow: `CREATE SCHEMA <app> AUTHORIZATION
   <app>_owner`, per-object grants, self-registration in `shared.schema_versions`, timeout headers.
5. **Tenancy:** every tenant table has `tenant_id uuid NOT NULL` and the RLS template (Part A SEC-6) with
   **FORCE from day one**; the pool fails closed (503), never falls back to another pool; membership is
   checked before `set_config('app.tenant_id', …, true)`.
6. **Reads from other apps** only through contract views granted by the producer (unguarded,
   `schema-ownership.md` rule 5); tours keyed by `(source_system, source_id)`; no FK into another schema.
7. **Events:** outbox table + `<schema>.v_<event>_outbox`, consumer inbox `UNIQUE (source, contract,
   idempotency_key)`; JSON Schema registered in `docs/contracts/` in the same PR as the view; consumer
   copies under a hash guard (*to build*, **X7**).
8. **Identity:** a Cognito app client (ADR 0006); no password, OTP or session tables; authorization is
   the app's own membership/role data keyed by `(iss, sub)`, never token claims alone.
9. **Platform services:** a job table from the shared template with a kind prefix (ADR 0003a); LLM calls
   through the Model Gateway into `shared.llm_call_log` tagged with the app; a retention row for every
   log, event or job table.
10. **PII:** `pii:<class>` column tags (Part B DM-6.1), a retention or redaction rule, minimal payloads,
    no PII in prompts or logs.
11. **Ops:** `App=<app>` tags, a budget alert, a row in the connection budget (Part C C2.2),
    `application_name`, a backlog-age alarm, a regenerated schema reference.
12. **Isolation probe before the first tenant:** an aa817-style matrix as `<app>_app` (own / foreign /
    forged / empty GUC) with 0 cross-tenant rows.

The checklist form of these steps (copied into the epic) is the review §6.3; Part B §11 says who
approves each change.

### 4. The data standards are binding

- Parts A, B and C are the rule body of this ADR. MUST / SHOULD / MAY carry the meanings defined
  there; each rule names how it is enforced, and controls that do not exist yet are marked *to build*
  with their roadmap id (review checklist until then).
- **Precedence:** an accepted ADR wins over the standards; the standards win over skills and session
  notes. A conflict is fixed by PR in the same session and reported to Nghiệp.
- **One home per number:** PII classes and retention windows in Part B; pool sizes, connection limits,
  timeouts and alarm thresholds in Part C; migration mechanics in Part A.
- A change to the standards is a PR to the root repo approved by Nghiệp, with the version in the
  standards README bumped and steering/skills that restate a rule updated in the same PR.

### 5. Contracts: views only, and tenant contract views live in `catalog` (E4)

- **New** cross-app grants are `USAGE` + `SELECT` on contract views only. This **narrows** ADR 0001
  decision 6 ("read published views and `shared.*` golden records") and `schema-ownership.md` rule 2
  ("a column list or a view") to views: new readers use `catalog` views of golden records
  (`catalog.v_destination`, a country view with **X5**). Existing table and column grants (CIS
  173/179/180/201/216, the `published_tours` SELECT) are grandfathered until the **X4** revoke
  migration; the gateway-config SELECT stays until ADR 0009 defines the gateway contract.
- Contract views live in: `catalog` for every CIS contract, including tenant-facing ones (the AA-813
  membership view) and read-backs (ADR 0004a's CIS → Booking supply content view); a non-CIS
  producer's own schema (`booking.v_supply_hotels`); `<schema>.v_<event>_outbox` for events. **No new
  contract schema** (no `platform` or `tenancy` schema).
- The single standing write exception is `INSERT` on `shared.llm_call_log` (ADR 0002), tagged with the
  calling app. Other apps read LLM cost only through the daily rollup (**N4**).
- Views are append-only; a breaking change is a new major served in parallel (default 30 days).

### 6. Ownership becomes a permission: role split order (E2)

- Target per schema: `<app>_owner` NOLOGIN owns objects; `<app>_app` LOGIN runtime (no ownership, no
  CREATEROLE, no BYPASSRLS, not in `rds_superuser`); DB Migrate runs as `db_migrator` from **its own task
  definition** with `SET ROLE <owner>` per directory and an `environment` input.
- Order (**X1**): `booking.*` → `bk_owner` and `tripplanner.*` → `tp_owner` first, with the separate
  migrator; then the CIS runtime moves to `cis_app` behind AA-817 **D2** (role-scoped policies first,
  CIS FORCE only after the split); `aa_cis_admin` becomes break-glass.
- Role attributes live in an Infra role bootstrap in git (**X1**). Until then, **N3** sets
  `CONNECTION LIMIT` and backstop timeouts of `tripplanner`, `booking` and `aa_app_user` in one reviewed
  CIS migration (the single exception in Part A MIG-6, Part C C2.3a).
- The 007b default-ACL auto-grant to `aa_app_user` is removed (**N7**) before any AA-813 membership
  table is created.

### 7. Retention and archival (E3)

- `shared.llm_call_log`: raw 180 days + daily rollup `shared.llm_call_daily`;
  `shared.tenant_api_usage`: raw 90 days + monthly rollup; job tables: succeeded 30 days, failed /
  cancelled 90 days; outbox/inbox payload PII redacted after 90 days (row and idempotency key kept).
- Rows with business or audit value are **archived to S3 as Parquet before delete**. Deletes are
  owner-run, batched TTL job kinds; never `VACUUM FULL`. The full table and the approval mechanics are
  Part B §7; the batch mechanics are Part C C5.4.

### 8. Customer data and the tenant CRM (E8, E9)

- `booking.customers` is the **single customer master**. After ADR 0006 Phase 4, TripPlanner keeps no
  profile of a signed-in traveller, only the guest contact and consent an inquiry needs (ADR 0006
  decision 9 wording, which wins over the shorter E8 phrase "subject + consent").
- **Tenant CRM (AA-821): research first** (build vs HubSpot/Zoho). If built, it is a CIS module with its
  own `crm` schema, `crm_owner` / `crm_app` roles and `crm-NNN` key space, so a later move to its own
  repo needs no renumbering. The tenant is the **data controller** and AA the processor: the CRM never
  reads `booking.customers` or `tripplanner.customers`, no AA app reads `crm.*`, AA support access (if
  any) is a separate read-only role with an explicit policy, and a hand-off to AA is a consented event
  after which Booking creates its own customer. Preconditions before any CRM DSN: this ADR, `owners.yaml`,
  the catalogue guard (**X2**), AA-813 membership + view, and N3. Until the CIS role split,
  `aa_cis_admin` can still read `crm.*`, so the isolation is partial.

### 9. Tour key across contracts (E7)

Tours are referenced across apps by `(source_system, source_id)` exactly as `catalog.v_tour` exposes it;
`tour_id` is a version snapshot. `inquiry.submitted` v1.2 adds `source_system` + `source_id` per leg as
an additive minor, Booking adds the columns to `booking.trip_case_legs`, and TripPlanner normalises its
mixed `source_tour_id` (**X3**).

### 10. Spend and scaling (E5, E6)

- Approved spend: Dev `db.t3.micro` → `db.t4g.small` + Performance Insights (~+$10–15/month, checked in
  the AWS calculator; **X9**); per-app cost allocation tags (Nghiệp activates them in Billing).
- Connection limits, TripPlanner pool max 1 and Lambda reserved concurrency ship and are applied
  **before** the Lambda concurrency quota of 1000 takes effect (**N3**).
- RDS Proxy, read replica, partitioning, a materialized catalog, the S3/Athena query layer, an
  EventBridge relay and an app split happen **only at their measured triggers** (Part C §C3), cheapest
  lever first.

### 11. ADR numbering (E1)

0008 = this ADR. 0009 = AI platform (AA-804; it was planned as "root ADR 0006", which is now ecosystem
identity). The job-model change is the amendment `0003a-per-owner-job-tables.md`. Amendments to an
accepted ADR are separate `<nnnn>a-<slug>.md` files (pattern 0004a).

## Consequences

- **Positive:**
  - a new app has one gate, one playbook and one checklist, and lands outside the CIS blast radius from
    day one (own owner and runtime roles, FORCE RLS, connection limit);
  - every schema stays liftable, so splitting Booking out later is a DSN cut-over, not a redesign;
  - retention, connection budget and scale steps have numbers and triggers instead of guesses.
- **Negative / cost:**
  - more roles, grants and registry entries to maintain; until **N1**, **N5**, **X1** and **X2** exist,
    most checks are review-only (the standards mark each one);
  - the views-only rule makes TripPlanner's remaining direct reads a migration project (**X4**);
  - small spend increases (t4g.small, S3 archive; RDS Proxy later at its trigger).

## Alternatives considered

- **A database (or instance) per app now.** Rejected: about double the DB cost and more contracts, for
  no benefit at Dev volume; the "liftable schema" rules keep the option open (trigger in Part C C3).
- **A new `platform` contract schema plus a `tenancy` schema.** Rejected for a small team: two new
  schemas at once; `catalog` already has the owner role and policy pattern (E4).
- **FORCE RLS on every CIS tenant table now.** Rejected: contradicts AA-817 D2 (the owner-exempt CIS
  worker and admin would read 0 rows); FORCE is for new apps from day one and for CIS after the split.
- **Keep the rules as review knowledge only.** Rejected: P3 and P8 show that unwritten, unchecked rules
  drift on the shared instance.

## Follow-ups

- `docs/database/schema-ownership.md`: rule 2 says "a view" only for new grants (decision 5), the `job`
  row points to ADR 0003a, owners and kind prefixes move to `owners.yaml` with **X1**.
- ADR 0001 decision 6 and ADR 0003: a header line pointing to this ADR / `0003a` (root PR).
- **X7 (AA-826):** `owners.yaml`-driven playbook tooling, role bootstrap template, consumer contract
  hash guard. **X2:** catalogue CI guard. **N1:** generated schema reference with policies, grants and
  `pii:` tags.
- **X1 done (19/10/2026, S244; AA-852 / AA-860):** decision 6 is in force. `booking.*` → `bk_owner` (bk-014),
  `tripplanner.*` → `tp_owner` (tp-013), CIS runtime on `cis_app` (S18), the 12 CIS schemas → `cis_owner` (CIS 245),
  DB Migrate logs in as `db_migrator` from its own task definition (S22), role attributes in the Infra `roles/` dir
  (`rl-001`, `rl-002`); `aa_cis_admin` is break-glass (data standards DM-8.9). One exception recorded in Part A §9:
  XD3 default privileges `FOR ROLE cis_owner … TO cis_app`. Plan and evidence:
  `docs/audits/2026-10-17-S241-x1/x1-plan.md`, isolation probe 58/58 after S22.
- Open items for Nghiệp are listed in the standards README ("Open items").
