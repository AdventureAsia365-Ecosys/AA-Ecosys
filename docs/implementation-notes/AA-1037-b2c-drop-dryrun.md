# AA-1037 lane b2c-drop-dryrun: DRY RUN of the B2C table drop

Lane of S270. Scope lines "frozen B2C tables get a DRY RUN drop" and "Booking CHECK limits work to b2b" (final form).
This session delivers the DRY RUN and the prepared migration only; nothing destructive runs. Report:
`docs/audits/2026-11-05-S270-aa1037-b2c-drop-dryrun/README.md`.

## Decisions

- **Everything lives in the root audit folder, no Booking PR.** A destructive migration in AA-Booking `migrations/`
  would be replayed by the Booking Integration Tests (24 files there still read the B2C tables, so CI goes red) and
  copied to Infra by the bot once merged. Following the AA-850 precedent, the draft is
  `migrations/bk_NNN_aa1037_retire_b2c.sql` in the audit folder; it moves into AA-Booking with the next free number as
  a migration-only PR after the readers are gone.
- **Class destructive**, not contract: it drops tables and a column (Infra lint `DESTRUCTIVE_RES`), so DB Migrate takes
  the RDS snapshot and Migration Apply never auto-applies it.
- **`inbox_events`, `inbox_cursor`, `invoice_sequence` stay.** The scope listed `inbox_events`, but
  `app/catalog/lifecycle.py` uses it for the CIS catalog feed (`source = 'cis'`), and `invoice_sequence` holds the
  AAS / AAT agency series. Only the inquiry rows (`contract = 'inquiry.submitted'`) and the TripPlanner cursor row go.
- **`media_files` is added to the drop**: only `customers.profile_media_id` references it and no code uses it.
- **b2c trip cases are kept, not deleted (fix pass, review finding "data rules").** The first draft deleted the b2c
  case graph with its supplier bookings, bills, payouts, documents, audit and notification rows; DM-7.1 keeps those
  (accounting exception, "kept (append-only)", "kept (audit evidence)", proposed windows delete nothing) and DM-6.7
  redacts audit rows instead of deleting them. Now no row of a kept table is touched; `trip_cases_channel_chk` becomes
  `(b2b AND party_tenant_id) OR (b2c AND no party AND created_at < apply time)` so the kept cases stay valid and
  redactable and no new b2c case gets in. The cut-off is written as a literal at apply; the swap runs only while
  `customer_id` exists, so a re-run does not move it.
- **Customer money rows archived in the database** (`booking.retired_b2c_record`: source table, id, `to_jsonb` row, last
  write, `retain_until` = 31 Dec of the last-write year in Vietnam time + 10), checked equal to the source before the
  four tables drop. DM-7.3 wants S3 Parquet, which does not exist yet (N4); an in-DB, owner-only table with its own
  DM-7.1 row (added in this root PR) is the stand-in. The schema's default privileges grant `booking` arwd on a new
  table, so the migration revokes it.
- **Pins = row count + md5 of the sorted row text**, nine keys (the dropped tables only). A same-count UPDATE that left
  `updated_at` alone, or a delete plus insert, now refuses (review finding "pins compare counts only"). Row text
  depends on TimeZone / DateStyle / IntervalStyle / extra_float_digits / bytea_output, so both the migration and the
  DRY RUN `SET LOCAL` the same values. The check binds only when a dropped table has a row (empty-schema replay).
- **30-day guard** reads every write time of the dropped tables (OTP `used_at`, session `revoked_at`, media
  `deleted_at` added) and of the kept b2c graph (cases, versions, supplier bookings, bills, bill lines, payouts,
  operations files with `removed_at`, inquiry inbox rows). The block is marked `last-write:begin/end` in the migration
  and is word for word the script's `LAST_WRITE_SQL`; the harness compares them, and the pinned table list.
- **Intake guard**: a queued or running `bk_inquiry_pull` / `bk_inquiry_process` refuses the apply (the Infra idle check
  exempts `bk_inquiry_pull`, so the migration checks it itself).
- **Views rewritten in place, not dropped**: `v_trip_check_board` (`payment_verified` always NULL) and
  `v_ops_data_totals` (no `customers` metric) keep their columns and grants (`cis_app` reads the totals view).
- **`ops_files_guard`**: evidence files of the retired customer payments can no longer change (no removal), and the
  INSERT path refuses entity type `payment`. The `ops_files` / `notifications` / `audit_logs` CHECKs keep the
  `payment` / `customer` values the kept rows use.
- **DRY RUN grants are notes, not blockers**: the `cis_app` grant on `v_ops_inquiry_inbox` disappears with the view;
  the DRY RUN lists it so the Infra probe cell is removed first.
- **DRY RUN search_path**: role `booking` has `booking` on its search_path, so `regclass::text` printed bare names and
  the verdict mismatched; the measure runs in a transaction with `SET LOCAL search_path = pg_catalog`.

## Changed

- Scope (c) said "drop the FK columns first, tighten the CHECK, then drop the tables". The draft drops the invoice /
  payment tables before deleting the b2c cases (their FKs to trip cases and versions go with the tables, and their
  guard triggers would refuse the deletes), then drops `trip_cases.customer_id` and swaps the CHECK, then drops the
  customer tables.
- Added beyond the scope list: the config rows of the invoice workflow and the money edges.
- Fix pass (S270 review): scope (c) "drop the B2C tables" is now "drop the customer tables; archive, then drop, the
  customer money tables; keep the b2c case graph". `inbox_events` inquiry rows and the TripPlanner cursor row stay
  (DM-6.6: row and key kept, payload redacted after 90 days).

## Tradeoffs

- Archive table vs. keeping the four money tables read-only until N4: the archive lets the tables, nine functions and
  three views go now and keeps every value; reading an archived row is a jsonb read. If the tech lead prefers the
  tables kept, the draft drops its step 1 and the four drops (README section 9).
- Keeping the b2c case graph means B2B code must filter `channel = 'b2b'` where it lists cases (Booking code PR).
- Whole-row md5 vs. md5 of ids (the reviewer's suggestion): the row hash also catches an UPDATE that kept the write
  time, at the cost of pinning the row-text settings.
- Skipping the DM-3.9 quarantine step (as tp-018 / tp-024 did) needs the tech lead's written exception.

## Should know

- Exact Dev counts are not in this PR: the lane cannot run ECS exec (subagent hook). One read-only run of
  `scripts/aa1037_b2c_dry_run.py` in the Booking container, by the orchestrator before merge, fills README section 7
  and the registry rows; otherwise the PR is a partial delivery and that run is the first follow-up step.
- Verified locally only: PostgreSQL 16, every Booking migration replayed as `bk_owner` (bootstrap roles in RDS shape),
  the harness `scripts/test_bk_b2c_drop_draft.py` (11 tests) run from a Booking checkout, the empty-schema apply, the
  DRY RUN as role `booking`, and the Booking migration preflight with the AA-CIS-Infra lint (class destructive, lint
  ok). With the draft as `045`, `test_bk014_owner.py` fails on the dropped objects (expected; Booking code PR).
- When the draft becomes a Booking migration, the re-apply tests of bk-001 / bk-028 / other B2C files need a
  "superseded by bk-NNN" rule (TripPlanner `test_replay_twice_pg.py` does this for tp-024), and the root KPI registry
  check (`tools/docs/report_registry.py check`) will fail until the CIS KPIs on these tables are retired.
