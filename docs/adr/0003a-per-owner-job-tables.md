# ADR 0003 — Amendment A1: one job table per owner schema, from a shared DDL template

- **Status:** Accepted (15/10/2026, S237 — Nghiệp approved every recommendation of the S237
  data-architecture review, decision E1). Separate file, following the `0004a` pattern; ADR 0003 itself
  is not edited (follow-up below adds a pointer to it).
- **Amends:** ADR 0003 decision 4 ("A non-CIS repo … enqueues into `shared.job` only when it has real
  deferred work") and its consequence "Nac 6 (grant `shared.job` to a second repo)". The other ADR 0003
  decisions stay: one durable job model (1, read as "the owner's job table + its worker"), the three
  layers trigger / kind registry / write strategy (2), no partially recomputed sets (3), Lambdas as
  triggers (5).
- **Supersedes:** the premise of **AA-751** (a second repo enqueuing into `shared.job`).
- **Consistent with:** ADR 0001 decisions 3 and 6 (durable jobs; apps never write each other's
  schemas), ADR 0004 (Booking's own `booking.job`, bk-002, kinds `bk_*`), ADR 0008 and the data standards
  `docs/architecture/data-standards/` (Part A QRY-8, Part B DM-2.4 / DM-7, Part C C4.1 / C5.1b / C6).
- **Design source:** `docs/audits/2026-10-14-S237-lane-backlog/data-architecture/README.md` (§3 P11,
  §4.3 "Background job", roadmap **X6**).

## Context

ADR 0003 (06/10/2026) assumed one physical queue, `shared.job`, that other repos would join through a
grant once they had real deferred work. Reality went the other way:

- AA-Booking created its own queue `booking.job` in `bk-002` (`apps/AA-Booking/migrations/002_inquiry_intake.sql`),
  with the same claim semantics as CIS (`FOR UPDATE SKIP LOCKED`, lease `locked_by`/`locked_until`,
  reaper, backoff via `run_after`, unique `idempotency_key`), a kind CHECK `^bk_[a-z0-9_]+$`, and its own
  in-process runner (`backend/app/jobs/`). It left out `progress`, `cost_usd`, `cancel_requested`,
  `parent_job_id` and the worker registry.
- A shared `shared.job` would need cross-owner INSERT/UPDATE grants into a CIS table, against ADR 0001
  decision 6 and `schema-ownership.md` rule 1, and would put every app's jobs behind the CIS
  credential and CIS deploys.
- Four job/run models now coexist (`shared.job`, `booking.job`, legacy `shared.pipeline_jobs` /
  `pipeline_runs` / `acp_runs`, `acp_contract.atom_decompose_jobs`), and every new app copies the first
  precedent it finds (review P11).

## Decision

1. **One job table per owner schema.** Each owner with deferred work has exactly one queue,
   `<schema>.job`, in its own schema, written only by that owner's code: `shared.job` (CIS, CIS 174),
   `booking.job` (Booking, bk-002), and `tripplanner.job` or `<app>.job` when needed. **No app enqueues
   into, claims from or reads another owner's job table.** Work requested across apps travels as an
   outbox event (pull job on the consumer side, e.g. `bk_inquiry_pull`) or an HTTP call to the owner's
   API; the receiving owner turns it into its own job row.
2. **One shape, owned by a DDL template.** The shape lives in a reference DDL file in
   `apps/AA-CIS-App/shared/jobs/` (*to build*, **X6**). Each owner instantiates it in its own migration
   (migrations stay owner SQL; the template is not applied cross-owner). The template fixes:
   - columns of CIS 174: `id uuid`, `kind`, `payload`, `status`, `attempt`, `max_attempts`, `run_after`,
     `locked_by`, `locked_until`, `cancel_requested`, `idempotency_key`, `progress`, `result`,
     `cost_usd`, `error`, `parent_job_id` (FK inside the same table), `created_by`, `created_at`,
     `updated_at`, `started_at`, `finished_at`;
   - status set `queued / running / succeeded / failed / cancelled`; an owner MAY add a status in its
     own CHECK (CIS keeps `stopped_budget`);
   - a kind CHECK with the owner's prefix (decision 3), the running-lease CHECK, an `updated_at`
     trigger;
   - indexes: unique partial `idempotency_key`, partial due index (`status = 'queued'`), running/lease
     index, `(kind, created_at DESC)`, parent index, and the retention index on `finished_at`
     (Part A NAM-15, Part C C5.2e);
   - autovacuum settings for a high-churn queue (Part C C5.1b).

   A CI test per owner compares its job table with the template (*to build*, **X6**). Until the
   template exists, a new job table copies the CIS 174 columns (Part A QRY-8).
3. **Kind prefixes per owner**, recorded in `infra/AA-CIS-Infra/db/owners.yaml` (*to build*, **X1**;
   until then in `docs/database/schema-ownership.md`): Booking `bk_` (enforced by `job_kind_chk`),
   TripPlanner `tp_`, a new app `<prefix>_` (e.g. `crm_`). CIS kinds keep their existing unprefixed names
   (`a3_atomize`, `place_extract`, …); `shared.job` holds only CIS kinds, so no prefix is needed there.
4. **Runners.** `shared/jobs/` stays shared library code that any repo MAY reuse (the first sentence of
   ADR 0003 decision 4 stands). An owner MAY run its own runner (Booking `backend/app/jobs/`) as long as
   it keeps the claim semantics above and releases or re-queues running jobs on shutdown (Booking's
   release-on-shutdown is part of **X6**, Part C C6.2c). A Lambda-only owner (TripPlanner) runs its
   worker as a scheduled Lambda that claims from its own table; the EventBridge Scheduler rule only
   wakes or enqueues (ADR 0003 decision 5). TripPlanner creates `tripplanner.job` from the template
   before its first deferred kind; the first expected one is the outbox payload PII redaction
   (Part B DM-6.6 / DM-7.2).
5. **Operations are per owner, with one shared contract** (Part C C4.1, C6):
   - each owner shows its own jobs on its own admin page (ADR 0003 "visible on the Jobs page", per app);
   - retention: succeeded 30 days, failed / cancelled 90 days, queued / running never (E3; Part B DM-7);
   - a backend deploy waits until the **deploying owner's** job table is idle; DB Migrate `apply` and
     instance changes wait until **all** job tables are idle (Part C C6.3a/b);
   - a backlog-age alarm per owner (Part C C4.1).
6. **Booking catches up additively** (*to build*, **X6**): a `bk-NNN` adds `cancel_requested`,
   `progress`, `cost_usd`, `parent_job_id` and the `finished_at` index to `booking.job`, and the Booking
   deploy workflow gets its job guard (`deploy-dev.yml` still says "No job guard").
7. **Legacy models converge, they are not extended:** `shared.pipeline_jobs` stays history only (no new
   writes, archive in **L1**); `acp_runs` readers move to `shared.job`; `shared.pipeline_runs` stays as
   the upload-batch entity (FK parent of `raw_tours.batch_id`), not a job model;
   `acp_contract.atom_decompose_jobs` (0 rows) goes to the Dead Table Registry (**N6**).
8. **AA-751:** its premise (grant `shared.job` to a second repo) is superseded. The recommended path is to
   re-scope it to deliver **X6** (template, Booking catch-up, guard); Nghiệp decides re-scope or close
   when the X6 work is cut.

## Consequences

- **Positive:**
  - no cross-owner writes and no CIS grant for queues; each app's jobs survive another app's deploy,
    credential change or later split into its own database;
  - one shape means one admin view pattern, one retention job pattern, one guard pattern;
  - Booking's existing table becomes the conforming second instance instead of an exception.
- **Negative / cost:**
  - N job tables to watch instead of one: the deploy guard, DB Migrate idle check, retention and alarms
    must loop over every owner (C6.3b);
  - the template is copied, not imported, so drift is caught only by the X6 CI comparison;
  - no single cross-app "Jobs" page; a cross-app view, if ever needed, reads each owner's admin API.

## Alternatives considered

- **One shared `shared.job` with an `app` column and RLS** (ADR 0003 decision 4 as written). Rejected:
  cross-owner writes into a CIS table, CIS-owned DDL for everyone's jobs, and the CIS master credential
  in the blast radius of every queue (review P1).
- **Per-owner tables with no common shape.** Rejected: `booking.job` already shows the drift (missing
  cancel, progress and cost columns), and every new app would invent its own.
- **An external queue (SQS) instead of DB tables.** Not now: the outbox/inbox and job tables are
  transactional with the state they change; an EventBridge/SQS relay is trigger-based (**L8**).

## Follow-ups

- ADR 0003: add a header line "Amended by `0003a-per-owner-job-tables.md`" (root PR).
- `docs/database/schema-ownership.md`: the `job, job_worker` row ("A second repo enqueuing is deferred
  (AA-751)") points to this amendment; add the kind prefixes.
- **X6**: template file + per-owner CI comparison, Booking catch-up `bk-NNN`, Booking deploy job guard,
  `acp_runs` readers. **X1**: kind prefixes in `owners.yaml`.
