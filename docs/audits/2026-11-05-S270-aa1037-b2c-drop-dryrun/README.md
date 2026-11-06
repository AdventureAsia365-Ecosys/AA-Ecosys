---
id: ARCH-09-aa1037-b2c-drop
title: B2C table drop, DRY RUN (AA-1037, S270)
description: What retiring the B2C half of AA-Booking drops, archives and keeps on Dev, who still reads it, the draft destructive migration (tested locally, not applied) and the order of work.
type: report
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-booking, aa-cis-dev-db]
last_reviewed: 2026-11-05
related: [ARCH-09, docs/architecture/db-schema-reference.md, docs/database/schema-ownership.md]
---

# B2C table drop — DRY RUN (AA-1037, S270, 05/11/2026)

Scope lines of AA-1037 (S265 re-scope): "frozen B2C tables get a DRY RUN drop" and "Booking CHECK limits work to b2b".
Procedure: skill `aa-cis-schema` `references/destructive-ops.md` (STEP0, then five steps). **Nothing destructive ran in
S270**: this folder holds step 1 (the DRY RUN script; its one read-only run on Dev is done by the orchestrator, section
6, and its numbers go into section 7), the draft migration that will do steps 3 and 4 later, and the plan. The drop
itself is follow-up work (see "Order of work").

**Status of this report: partial until section 7 is filled.** STEP0, the readers, the draft and its local tests are
done; the Dev counts of step 1 need one run of the DRY RUN script in the `aa-booking-dev-api` container, which a lane
subagent cannot start (ECS exec is blocked for subagents). Until that run is pasted into section 7 and the dead-table
registry, the counts in section 3 are estimates.

| File | What |
|---|---|
| [`scripts/aa1037_b2c_dry_run.py`](scripts/aa1037_b2c_dry_run.py) | The DRY RUN, read-only: aggregate counts, write times and one md5 per dropped table, never a row value. Runs in the `aa-booking-dev-api` container (role `booking`) or as a DB Migrate run-script. Prints `DRYRUN_PINS` for the migration. |
| [`migrations/bk_NNN_aa1037_retire_b2c.sql`](migrations/bk_NNN_aa1037_retire_b2c.sql) | Draft Booking migration, `-- migrate: destructive`, not in any app repo yet (so nothing copies or applies it). |
| [`scripts/test_bk_b2c_drop_draft.py`](scripts/test_bk_b2c_drop_draft.py) | Local harness (13 tests): builds a B2C graph with the Booking integration helpers, runs the DRY RUN, then the draft. |

Repos read for this report (`origin/main`, 05/11/2026): AA-Booking `b30f633`, AA-CIS-App `7495a53d`,
AA-TripPlanner-Web `11c7b93`, AA-CIS-Infra `290d4e0`, AA-Partner `a1082a9f`, root `162aa6ad`. Table and column names
come from `db-schema-reference.md` (dump of 2026-11-05 10:07 UTC, Booking at bk-044) and a local replay of every Booking
migration on PostgreSQL 16.

## 1. Result in one paragraph

The B2C half is eight tables, one table of profile pictures, four views, three sequences, nine guard functions, one
column (`trip_cases.customer_id`) and the `b2c` branch of `trip_cases_channel_chk`; b2c trip cases also carry rows of
kept tables (versions, supplier bookings, bills, payouts, operations files, status history, audit and notification
rows, inquiry inbox rows). The draft migration **drops** the customer master and credential tables, **archives then
drops** the four customer money tables (every row copied whole into a new owner-only table
`booking.retired_b2c_record`, kept 10 years under the DM-7.1 accounting exception), and **keeps** every b2c trip case
and every row about it in place, so no row under a "kept" or "proposed" DM-7.1 retention row is deleted. New trip cases
are b2b only. `inbox_events`, `inbox_cursor` and `invoice_sequence` are not B2C (the CIS catalog feed and the agency
invoice numbers use them). The draft runs in one transaction and refuses while any B2C row (the dropped tables and the
kept b2c graph alike) was written in the last 30 days, while the inquiry intake runs, or while a dropped table's rows
differ in count or content from the DRY RUN. It passes on a local replay (11 harness tests, an empty-schema apply, the
Booking migration preflight with the pinned AA-CIS-Infra lint: class **destructive**, lint ok, and the DRY RUN script
as role `booking`). It cannot ship before the readers outside Booking and the Booking B2C code are removed (section 4).
Exact Dev counts need one read-only run of the DRY RUN script (section 6).

## 2. What goes, what stays

| Object | Kind | Decision | Why |
|---|---|---|---|
| `booking.customers` | table | drop (no archive) | B2C customer master (E8); no B2B use, no DM-7.1 "kept" row; the accounting copy of the person is the invoice `bill_to` snapshot, archived. `trip_cases.customer_id`, `invoices.customer_id`, identities / OTPs / sessions and `customers.merge_candidate_id` point at it. |
| `booking.customer_identities`, `customer_otps`, `customer_sessions` | tables | drop (no archive) | traveller sign-in (bk-001, bk-024); `ON DELETE CASCADE` from customers; DM-7.1 already plans to drop the OTP and session tables, identities follow their customer. |
| `booking.media_files` | table | drop | only `customers.profile_media_id` points at it; no code reads or writes it (git grep: migrations only); 0 inserts since stats began. |
| `booking.invoices`, `invoice_items`, `payment_schedule`, `payments` | tables | **archive, then drop** | the customer proforma invoice and its payments (bk-028); agency money is `agency_invoice` / `agency_payment` (bk-041..044). Their rows fall under the DM-7.1 accounting exception (kept 10 years, also through erasure), so every row is copied whole (`to_jsonb`) into `booking.retired_b2c_record` with `retain_until`, and the copy is checked equal before the tables drop. |
| `booking.v_customer_summary`, `v_invoice_balance`, `v_payment_schedule_status` | views | drop | read only by the B2C Booking code. |
| `booking.v_ops_inquiry_inbox` | view | drop | bk-035 TP-03 key view; CIS stopped reading it on 2026-11-03 (AA-1003, ADR 0019). Still granted to `cis_app` and named by the Infra isolation probe. |
| `booking.v_trip_check_board` | view | rewrite | same columns; `payment_verified` NULL on every case (it read `invoices`). |
| `booking.v_ops_data_totals` | view | rewrite | same columns; the `customers` metric goes (it read `customers`). CIS data coverage row `bk.customers` reads that metric. |
| `booking.retired_b2c_record` | table | **new** | the archive of the four money tables (source table, source id, whole row as jsonb, last write, `retain_until`); owner-only (the default `booking` grant is revoked), append-only; its DM-7.1 row is in this root PR. |
| `trip_cases_post_sale_guard()`, `ops_files_guard()` | functions | rewrite | their invoice / payment branches go; a money status (`invoice_sent`, `payment_pending`, `paid`) is refused on every case; customer payment evidence files can no longer change and no new one is accepted. |
| `invoice_settle`, `invoice_money_state`, `invoice_net_paid`, `invoices_guard`, `invoice_items_guard`, `invoice_items_settle`, `payment_schedule_guard`, `payments_guard`, `payments_settle` | functions | drop | the guards of the dropped tables. |
| `customer_code_seq`, `invoice_number_seq`, `payment_ref_seq` | sequences | drop | `CUS-` / `INV-` / `PMT-` numbers. `invoice_sequence` (AAS / AAT) stays. |
| `trip_cases.customer_id` | column | drop | with its index; `trip_cases_channel_chk` becomes `(channel = 'b2b' AND party_tenant_id IS NOT NULL) OR (channel = 'b2c' AND party_tenant_id IS NULL AND created_at < <apply time>)`: no new b2c case, the kept ones stay valid and redactable. |
| b2c trip cases and their rows (versions, legs, checks, status history, supplier bookings, bills, bill lines, payouts, operations files and their S3 objects) | rows | **keep** | DM-7.1: supplier money and its documents are under the accounting exception, `trip_case_status_history` is "kept (audit evidence)", supplier bookings and checks are "kept with the trip case". Counted under `kept` in the DRY RUN, not pinned. |
| `booking.audit_logs`, `booking.notifications` rows about B2C objects | rows | **keep** | audit is "kept (append-only)" and redacted, not deleted, on erasure (DM-6.7); notifications have a proposed window only, so nothing is deleted before it is approved. Their CHECKs keep the `customer` values. |
| `inbox_events` rows with `contract = 'inquiry.submitted'`, the `tripplanner` cursor row | rows | **keep** | DM-6.6: the row and its key stay, the payload is redacted after 90 days by `bk_retention_inbox_redact`; b2c cases still point at them (`inbox_event_id`). |
| `ops_transitions` (entity `invoice`), money edges of `trip_case_status_transitions` | config rows | delete | the invoice workflow and the money track of a case. |
| CHECKs of `ops_files` (payment kind), `notifications.recipient_type` (customer), `audit_logs.actor_type` (customer) | constraints | keep | the kept rows use these values; the rewritten `ops_files_guard` refuses new payment evidence. |
| `booking.inbox_events`, `inbox_cursor` | tables | **keep** | `app/catalog/lifecycle.py` pulls the CIS catalog feed through them (`source = 'cis'`, `contract = 'catalog.tour'`); `v_ops_funnel_daily` reads them. |
| `booking.invoice_sequence` | table | **keep** | AAS / AAT agency invoice series (bk-041). |
| `settings` rows `deposit_due_days`, `balance_due_days_before_start`, `payment_due_soon_days`, `payment_overdue_reminder_days`, `invoice_issuer` | config rows | keep for now | B2C-only keys, removed with their code later; `payment_instructions` is read by agency billing. |
| statuses `invoice_sent` / `payment_pending` / `paid` in `trip_cases_status_chk` | constraint values | keep | unreachable once the edges are gone; narrowing the CHECK is optional. |

## 3. STEP0: is it really dead

1. **Has the new path taken over?** Yes. Root ADR 0019 (B2B-only model): agencies are the only customers; AA money is
   agency billing (bk-041..044, deployed, AA-1037 Done-when row 1). The TripPlanner hand-off answers 410 `b2b_only`
   (AA-1034 L6); Booking refuses every B2C staff write while `B2C_INTAKE_ENABLED` is off (AA-1037 lane b2c-writes-off,
   Booking #194, root #569 "read-only B2C part"); bk-036 revoked INSERT on the customer tables from role `booking`. What
   is still live is **reading**: My Payments in TripPlanner, the Booking staff pages and `booking.customer.v1`.
2. **Foreign keys** (pg_constraint, replay): `customer_identities/otps/sessions.customer_id → customers` (CASCADE),
   `customers.merge_candidate_id → customers`, `customers.profile_media_id → media_files`,
   `trip_cases.customer_id → customers`, `invoices.customer_id → customers`, `invoices.trip_case_id → trip_cases`,
   `invoices.version_id → trip_case_versions`, `invoice_items / payment_schedule / payments.invoice_id → invoices`,
   `payments.evidence_file_id → ops_files`, and the `*_by` columns to `staff_users`. Nothing outside the drop set points
   at a dropped table (the draft re-checks this at apply and the DRY RUN lists it).
3. **Rows and counters** (`db-schema-reference.md` activity table, never reset, as of 2026-11-05 10:07 UTC):

   | table | ~rows (estimate) | inserts / updates / deletes | note |
   |---|---|---|---|
   | `customers` | 1 (stale) | 17 / 0 / 0 | up to 17 rows |
   | `customer_identities` | — | 0 / 0 / 0 | never written on Dev |
   | `customer_otps`, `customer_sessions`, `media_files` | — | 0 / 0 / 0 | never written on Dev |
   | `invoices` | — | 4 / 14 / 0 | |
   | `invoice_items` | — | 4 / 0 / 0 | |
   | `payment_schedule` | — | 6 / 0 / 0 | |
   | `payments` | — | 8 / 8 / 0 | |
   | `trip_cases` (all channels) | 10 | 31 / 30 / 0 | b2c share unknown until the DRY RUN |
   | `trip_case_versions` (all) | — | 21 / 21 / 0 | |
   | `supplier_bookings` / `supplier_bills` / `supplier_payouts` / `ops_files` (all) | — | 9/12/0, 1/3/0, 3/1/0, 1/1/0 | b2c share unknown |
   | `inbox_events` (all) | 5 | 17 / 22 / 0 | inquiry rows + catalog feed rows |

   Estimates only: the exact numbers come from the DRY RUN (section 6), and the migration pins them.
4. **`git ls-files`**: every reader in section 4 is a tracked file on `origin/main`.
5. **Dependent views** (replay, pg_depend): `v_customer_summary`, `v_ops_data_totals` (customers);
   `v_invoice_balance`, `v_payment_schedule_status`, `v_trip_check_board` (invoices); `v_ops_funnel_daily`,
   `v_ops_inquiry_inbox` (inbox_events, kept). Functions naming the tables: the nine invoice / payment guards plus
   `trip_cases_post_sale_guard`, `ops_files_guard` (rewritten) and `agency_invoice_guard` (only an error text says
   "payments"; untouched).
6. **Integration tests that name the tables** (CI replays every migration): 24 files under Booking
   `tests/integration/` (the `ops.py` helpers included) and 9 unit files (`test_bk001`, `test_bk002_intake`, `test_bk003_workflow`, `test_bk005_w1`, `test_bk024_*`, `test_bk028_*`,
   `test_bk035_ops_inquiry_inbox`, `test_bk036_schema`, `test_aa1034_intake_off`, `test_aa1037_b2c_writes_off`, the
   `tests/integration/ops.py` helpers, …). They go or change in the Booking code PR, and the re-apply tests of bk-001,
   bk-028 and the other B2C files need a "superseded by bk-NNN" rule like TripPlanner's `test_replay_twice_pg.py` has
   for tp-024, otherwise re-running an old file after the drop recreates the tables. A local replay with the draft as
   `045` also shows `test_bk014_owner.py` failing on the dropped tables and sequence (18 of 70; its object lists change
   in the same Booking PR).
7. **Same folder, not same fate**: each object is decided on its own in section 2.

## 4. Readers to remove first

Nothing below may still run when the drop applies. Order matters (lesson 164, MIG-4): readers outside Booking, then the
Booking code, then the migration-only PR.

| Repo | Where | What it reads | Change |
|---|---|---|---|
| AA-TripPlanner-Web | `frontend/app/api/me/payments/route.ts`, `frontend/lib/myPayments.ts`, `frontend/components/MyPayments.tsx`, `frontend/components/MyTrips.tsx:9,126` | `GET /booking/customer/v1/payments` (My Payments on `/trips`) | remove the BFF route, the component and its tests; CONTEXT.md rows at lines 453 and 918 |
| AA-Booking | `app/routers/customer.py`, `app/auth/customer.py`, `app/ops/my_payments.py` | `booking.customer.v1` (identities, invoices, payments, schedule) | remove |
| AA-Booking | `app/b2c.py`, `app/customers/`, `app/routers/customers.py`, `app/routers/billing.py`, `app/ops/invoices.py`, `app/ops/payments.py`, `app/ops/files.py` (payment evidence), `app/ops/lifecycle.py` / `app/ops/track.py` (invoice reminders, money track), `app/ops/trip_checks.py` (`payment_verified`), `app/trip_cases/service.py` + `versions.py` (customer join, customer-facing send / approve), `app/inquiry/` (intake jobs), `app/notifications/staff_email.py`, `app/auth/admin.py`, `app/pricing/engine.py` (b2c branch), `app/jobs/worker.py` (disabled kinds) | every B2C table | remove or narrow to b2b; drop the `customer_id` field from trip case shapes |
| AA-Booking | `frontend/app/(staff)/customers/**`, `frontend/app/(staff)/billing/**` (customer invoices and payments; the supplier bills part stays), `frontend/app/(staff)/cases/[code]/BillingTab.tsx`, `frontend/app/(staff)/cases/new/CustomerPicker.tsx`, `frontend/lib/api/billing.ts`, `frontend/ui/booking/invoiceTotals.ts`, `paymentEvidence.ts` | the routes above | remove; visual baselines that show these pages need an accept |
| AA-CIS-App | `api/services/data_coverage/registry.py:556` (row `bk.customers`, metric `customers` of `booking.v_ops_data_totals`) | `booking.v_ops_data_totals` | remove the row (the view keeps its columns) |
| AA-CIS-App | `services/reports/registry/kpis.yaml`: K-AR-AGING, K-AR-OVERDUE, K-AR-UNVERIFIED, K-BK-CASH, K-BK-INVOICED, K-BK-UNVERIFIED, K-MKT-CUSTSRC, K-PRIV-CONSENT (sources `v_payment_schedule_status`, `v_invoice_balance`, `payments`, `invoices`, `customers`); `catalog.yaml:975` | definitions only (`cis_app` has no grant on these tables) | retire the KPIs or move them to `agency_invoice` / `agency_payment`; root `tools/docs/report_registry.py check` checks KPI sources against the schema reference, so this must merge before the dump PR that drops the tables |
| AA-CIS-App | `services/erasure/inventory.py:335` (checklist line "booking.customers, customer_otps, customer_sessions, inbox_events.payload, …") | text of the erasure checklist | keep `inbox_events.payload`, drop the customer tables |
| AA-CIS-App | `api/migrations/244_x1_cis_app_runtime.sql:452`, `245_x1_cis_owner.sql:793` | probe `SELECT 1 FROM booking.customers` | no change: both already skip with a NOTICE when the table is absent |
| AA-CIS-Infra | `db/isolation_probe.py:183` (`cis_app` USAGE / SELECT on `booking.v_ops_inquiry_inbox`, bk-035) and `:258-267` (cross-app cells on `booking.customers`) | the dropped view and table | move the cross-app cells to `booking.trip_cases` (or another Booking table), remove the bk-035 cell; `db/README.md:544` |
| root | `docs/contracts/booking.customer.v1.openapi.yaml`, `docs/contracts/README.md:72`, `docs/contracts/ops.overview.v1.md:6,31` | contract and contract view | mark `booking.customer.v1` retired, drop the `v_ops_inquiry_inbox` row |
| root | `docs/architecture/data-standards/02-data-management.md` rows 106, 183, 224, 227, 229, 231, 298, 309, 310 (E8 customer master, DM-6.2/6.5/6.7/6.9, the DM-7.1 retention rows of the customer, OTP, session, identity, invoice and payment tables) | standards text | rewrite for the B2B-only model in the same root PR as the dead-table registry update after the apply |
| AA-CIS-Infra | `db/owners.yaml` `runtime_privileges.booking`, `db/isolation_probe.py` `RUNTIME_MISSING_SQL` (S271 review) | SELECT for role `booking` on every relation of schema `booking` | the archive `booking.retired_b2c_record` is owner-only (bk-045 revokes `booking`): list it under `owner_only_relations` (left out of `runtime_grants.booking`; cell `owner_only.booking` asserts no privilege), or the probe goes red on the apply and every night after |
| AA-CIS-Infra | `db/scripts/dm65_consent_capture.py` + `db/tests/test_dm65_consent_capture.py` (S271 review) | `booking.customers` (DM-6.5 consent check, run-script) | read `tripplanner.customers` and its unredacted `booking.inbox_events` hand-off only |
| root | `docs/legal/dsar-erasure-runbook.md` sections 2 and 3 (S271 review) | lookup and delete order on `booking.customers`, `trip_cases.customer_id`, OTPs, sessions, identities, `media_files` | B2B-only lookup: b2c cases through the hand-off row and the TripPlanner trip id (`trip_cases.source_id`), the archive by `bill_to_email` / `trip_case_id`, redact in place |
| root | `docs/legal/consent-capture-query.md` (S271 review; KPI K-PRIV-CONSENT cites it) | `booking.customers` | same text as the Infra script; CRM part on `crm.consent` |
| root | `tools/uat/scenarios/booking/bk-08.cjs`, `bk-10.cjs`, `tools/uat/catalogue.json` (S271 review) | the Booking pages `/customers` and the customer tabs of `/billing` | BK-08 on Supplier bills, Agency billing and Trip checks; BK-10 on the audit log and staff |
| AA-Partner | — | nothing (git grep: no reader) | — |

## 5. The draft migration

`migrations/bk_NNN_aa1037_retire_b2c.sql`, header `-- migrate: destructive` (DB Migrate takes the RDS snapshot; Migration
Apply never auto-applies it, ADR 0017a). One transaction, as `bk_owner`:

- **Guards** (RAISE, nothing changes): running as `bk_owner`; no `bk_inquiry_pull` / `bk_inquiry_process` job queued or
  running (the B2C switch already cancels them; a queued one means an old build); **no B2C row written in the last 30
  days**, read over every write-time column of the dropped tables (OTP `used_at`, session `revoked_at`, media
  `deleted_at` included) and of the kept b2c graph: b2c cases and versions, their supplier bookings, bills, bill lines,
  payouts, operations files (`created_at`, `updated_at`, `removed_at`) and the inquiry inbox rows. The block sits
  between `-- last-write:begin` / `-- last-write:end` and is word for word the DRY RUN's `LAST_WRITE_SQL` (a harness
  test compares them). **Pins**: for each of the nine dropped tables, the DRY RUN's row count and an md5 over the
  **non-personal columns** of every row (`PIN_COLUMNS` / `-- pin-columns:begin`: the key, the write times and the
  status-like codes, one `jsonb_build_array` per row, sorted, newline-joined; the settings that shape timestamp text
  are pinned by `SET LOCAL` in both). A moved count, or the same count with other content (an app UPDATE moves
  `updated_at`, a delete plus an insert moves the id and `created_at`, a code changed by hand with the triggers off),
  refuses the apply. No personal column is read, not even into the hash: the pilot PII guard
  (`.claude/hooks/pilot_pii_guard.py`, AA-969) refuses a whole-row read (`t::text`) of a table with `pii:` columns,
  which the first S270 draft did (S271 fix, AA-1046). Known limit: a hand edit of a personal column alone with the
  triggers off keeps the pin (only `bk_owner` can do that). The pins bind only when a dropped table has a row, so the
  Integration Tests' replay on an empty schema passes. Last: no view or foreign key outside the file on a dropped
  object.
- **Order inside**: create `booking.retired_b2c_record` (owner-only) → copy every row of `invoices`, `invoice_items`,
  `payment_schedule`, `payments` into it (`to_jsonb`, `retain_until` = 31 December of the last-write year in Vietnam
  time + 10) and check the copy equals the source → rewrite the two views and two guard functions → drop the B2C views,
  the four money tables and their nine functions → drop `trip_cases.customer_id`, new `trip_cases_channel_chk` (b2b,
  or b2c created before the apply) → drop the customer tables, `media_files`, the sequences → delete the invoice
  workflow edges and the money edges (reference data) → register `bk-NNN`.
- **Deletes no row of a kept table**: no b2c case, version, supplier booking, bill, payout, file, status history,
  check, notification, audit or inbox row is touched (section 2, DM-7.1).
- **Re-runnable**: after a full apply the guards return early, the archive step skips the absent tables, the CHECK swap
  skips (the column is gone, so the cut-off is not moved) and every other statement is `IF EXISTS` or matches no row.
- **Undo**: none in SQL; the pre-apply snapshot (`aa:retain-until` = apply + 180 days) is the rollback copy, not a
  retention copy: what must be kept is kept in the database (archive table and the untouched rows).

### Local verification (05/11/2026, PostgreSQL 16, every Booking migration replayed as `bk_owner`)

| Check | Result |
|---|---|
| `test_bk_b2c_drop_draft.py` (13 tests, S271: the 30-day block, pinned table list, pinned columns, pin statements, pins placeholder and timestamp-text settings equal the DRY RUN's; no pinned column is tagged `pii:` in the schema reference; the pilot PII guard passes the ECS exec of the script (exit 0) and refuses a whole-row probe (exit 2); the DRY RUN pins and counts the graph; refuses fresh rows, fresh writes on kept b2c rows (a payout, a bill line, an OTP use, a payment evidence file), missing pins, a moved count, a same-count change of a pinned code, a delete-plus-insert (moved ids), a queued intake job; ready once frozen; apply archives every money row whole with `retain_until` 10 years on, drops the B2C objects, keeps the b2c cases with their supplier bookings, bill, line, payout, evidence file, status history, audit and inquiry rows, keeps the B2B case, its supplier booking, the CIS feed inbox row, agency billing, `invoice_sequence`; a kept b2c case can still be redacted; a new b2c case, a change to payment evidence and new payment evidence are refused; money edge refused; guards name no dropped table; the archive is not readable by `booking` or `cis_app`; second run is a no-op and keeps the CHECK) | 13 passed (S271, PostgreSQL 16, Booking `5066f75`) |
| Empty-schema apply (the CI replay case: all Booking migrations, then the draft as `045` with null pins) | applied: tables gone, `retired_b2c_record` empty, `bk-045` registered, new CHECK in place |
| DRY RUN script as role `booking` (the container login) on the replayed schema (bk-044) | every table readable; nine pins (`n` 0, md5 of the empty string), `kept` all 0; verdict `ready` with one note: `v_ops_inquiry_inbox` is granted to `cis_app` (its reader, the Infra probe cell, must go first) |
| Booking `.github/scripts/migration_preflight.py --infra-tools` (AA-CIS-Infra `290d4e0` lint) with the draft as `045_…` | lint ok, class **destructive**, "copied by the bot, never auto-applied" |

## 6. DRY RUN on Dev (step 1): to run, read-only

Not run in S270: a lane subagent cannot start ECS exec. The orchestrator runs it once, read-only, **before this root PR
merges** (or, if that cannot happen in S270, the PR merges as a partial delivery and the run is the first follow-up):

```
ECSX_SERVICE=aa-booking-dev-api tools/ecs/ecsx.sh docs/audits/2026-11-05-S270-aa1037-b2c-drop-dryrun/scripts/aa1037_b2c_dry_run.py
```

Expected: `DRYRUN login "booking"`, `latest_booking_migration "bk-044"` (or later), `DRYRUN kept {…}` with 7 counts,
a `DRYRUN_PINS {…}` line with nine `{"md5", "n"}` objects, and `DRYRUN verdict`. Today the verdict will most likely be
`ready: false` with the 30-day reason: B2C rows were written on Dev recently (writes were open until Booking #194).
That is the expected state, not a failure; the drop waits for the 30 days anyway. The output holds counts, codes, md5
digests and timestamps only (the pilot PII guard passes the script since S271: no pin reads a personal column). Paste the row counts, the kept counts, the last write time and the verdict into section 7
and the dead-table registry rows. **Do not paste the pins into the draft migration now**: they are taken again by the
fresh DRY RUN of step 6 of the order of work, at least 30 days after the last B2C write.

## 7. Exact counts (fill in from the Dev run)

Dropped tables (pins, `n`; the md5 values stay in the run output, they only matter for the apply):

| Pin | Dev rows | Pin | Dev rows |
|---|---|---|---|
| customers | _pending_ | invoices (archived) | _pending_ |
| customer_identities | _pending_ | invoice_items (archived) | _pending_ |
| customer_otps | _pending_ | payment_schedule (archived) | _pending_ |
| customer_sessions | _pending_ | payments (archived) | _pending_ |
| media_files | _pending_ | | |

Kept b2c rows (`kept`):

| Count | Dev rows | Count | Dev rows |
|---|---|---|---|
| b2c_trip_cases | _pending_ | b2c_supplier_payouts | _pending_ |
| b2c_versions | _pending_ | b2c_ops_files | _pending_ |
| b2c_supplier_bookings | _pending_ | inquiry_inbox_events | _pending_ |
| b2c_supplier_bills | _pending_ | | |

Last B2C write: _pending_. Verdict: _pending_. Run: _pending_ (date, task, login).

## 8. Order of work (follow-up issue AA-1046)

**S271 status (AA-1046 R4b part 1, lane l2-r4b-b2c-drop).** Steps 1 to 5 and 7 are done as PRs: TripPlanner (My
Payments retired), CIS (coverage row, KPIs moved to agency billing, erasure checklist), AA-CIS-Infra (isolation probe
cells on `booking.trip_cases`, the bk-035 cell removed), the Booking code PR (no reader or writer of a dropped object
is left), the root PRs (this fix of the pins; the contract, standards and registry text), and the Booking
migration-only PR with this draft as `migrations/045_aa1037_retire_b2c.sql` (stacked on the code PR, its integration
test `tests/integration/test_bk045_retire_b2c.py`, the DRY RUN script copied to `tests/integration/b2c_dry_run.py`). The
pins stay `null` in that PR until step 6: the orchestrator pastes the fresh `DRYRUN_PINS` into its `pins jsonb := '…'`
line before it merges (a merged file is copied to AA-CIS-Infra and never edited again). The draft here keeps the same
text with `bk-NNN` (the S271 fix pass also added the two view REVOKEs and dropped a `;` from the registration text,
both for the Booking migration guard).

### Steps

1. TripPlanner PR: remove My Payments (BFF route, component, lib, tests, CONTEXT.md).
2. CIS PR: remove the `bk.customers` data coverage row, retire or move the eight KPIs, fix the erasure checklist line.
3. AA-CIS-Infra PR: move the isolation probe cells off `booking.customers` and `v_ops_inquiry_inbox`.
4. Booking code PR: remove every B2C reader and writer (section 4), filter trip case lists and reports to
   `channel = 'b2b'` where the kept b2c cases would otherwise show, the B2C integration tests, add the "superseded by
   bk-NNN" rule to the replay tests, update `test_bk014_owner.py`; deploy; `/booking/health/ready` unchanged.
5. Root PR: retire `booking.customer.v1`; DM rows (E8, DM-6.7 erasure list: the archive table replaces the four money
   tables); dead-table registry rows move to "approved" with the DRY RUN numbers.
6. Fresh DRY RUN (section 6) at least 30 days after the last B2C write; the tech lead approves the numbers.
7. Booking migration-only PR: the draft as `NNN_aa1037_retire_b2c.sql` (NNN = main max + 1 then), pins pasted; the
   harness becomes its integration test. Adversarial review before merge (lesson 42).
8. Infra copy (bot) → DB Migrate `check`, then `apply` with the snapshot, when every job table is idle.
9. Independent verify (a new DB Migrate run-script or the DRY RUN again: tables absent, archive count = the pinned
   money rows, b2b and kept b2c counts unchanged); purge the S3 objects of the dropped `media_files` rows only (0 on
   Dev; the ops-docs objects stay with their rows); merge the `bot/db-schema-reference` PR; registry rows to
   "dropped"; Booking CONTEXT.md "The B2C part is read-only" becomes "B2C is retired".

## 9. Risks and open points for the tech lead

- **30-day wait.** The guard follows the scope ("RAISE if any b2c row was written in the last 30 days") and reads the
  kept b2c graph too. An automatic update on a b2c row (for example a status job touching `updated_at`) restarts the
  clock; the DRY RUN shows the last write time so it can be traced.
- **Data rules (review finding, S270 fix pass).** The first draft deleted the b2c case graph, the supplier money rows,
  their documents and the audit / notification rows about B2C objects, which DM-7.1 (rows "kept (append-only)",
  accounting exception "10 years, also through erasure", "proposed: nothing deleted until approved") and DM-6.7 ("audit
  … redacted, not deleted") do not allow, and no exception was recorded. The draft now deletes none of them and archives
  the customer money rows before their tables drop, so no exception is needed. What it still drops without an archive
  (customer master, identities, OTPs, sessions, profile pictures) has no "kept" row in DM-7.1.
- **The archive is in the database, not in S3.** DM-7.3 asks for an S3 Parquet archive before a delete; it does not exist
  yet (N4). `booking.retired_b2c_record` keeps the rows instead (owner-only, append-only, its own DM-7.1 row) and moves
  to S3 with the other accounting rows when N4 lands. If the tech lead prefers to keep the four money tables as they
  are (read-only) until N4, the draft loses its step 1 and the four drops; say so before step 7.
- **Kept b2c cases stay visible to B2B code** that does not filter on `channel`. The Booking code PR (order of work,
  step 4) filters them; the new CHECK only stops new b2c cases.
- **S3 objects** of the kept `ops_files` rows stay; only `media_files` objects are purged after the apply (0 inserts on
  Dev).
- **DM-3.9 quarantine is skipped** for the dropped tables (exception, as tp-018 and tp-024 did): the drop goes straight
  from candidate to dropped, the RDS snapshot is the rollback copy. Needs the tech lead's written approval in the
  migration PR and session log (step 6 of the order of work).
- **TripPlanner's own B2C tables** (`tripplanner.customers`, `tripplanner.sessions`, the inquiry outbox rows) are
  TripPlanner's schema and need a TripPlanner migration of their own; not in this draft.
- **Proposed follow-up issue** (ask before creating, Linear rule): "R4b: B2C drop (readers, Booking code, destructive
  migration) + e-invoice provider API", milestone R4, as already proposed in the S270 scope review. Its first step is
  the Dev DRY RUN of section 6 if it did not run before this PR merged.
