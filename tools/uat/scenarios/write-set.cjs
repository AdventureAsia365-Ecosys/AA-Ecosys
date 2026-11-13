// The UAT write set (AA-855 round 1, tools/uat/dryrun.cjs): scenarios that WRITE on a synthetic tenant and may call a
// paid model. Never part of a default dry run: each one runs or records only by id, and a paid one only with
// --allow-paid (dryrun-core.cjs select). --preview --only <ids> runs the read-only part (the steps before the first
// step marked `writes`) at $0. Paths are relative to this folder; every id has a catalogue row that writes or is paid
// (tests/catalogue.test.cjs). Built with rw() (lib/uat-page.cjs): narrow allowWrites, the browser guard stays on.
module.exports = [
  // The audit editor (studio-audit) on the ONE audit tenant of the run (env UAT_STUDIO_TENANT). Record in this order:
  // W-01 stands alone; W-02 starts the article W-03 follows and W-04 (dry-run set, read only) exports.
  'content-studio/w-01.cjs',
  'content-studio/w-02.cjs',
  'content-studio/w-03.cjs',
  // The E2E tenant's studio editor (its identity must be enrolled first).
  'content-studio/prt-02.cjs',
  'content-studio/prt-06.cjs',
  // The E2E CIS admin (cis-admin, a staff identity: lib/dryrun-core.cjs WRITE_SET_STAFF) on one synthetic audit tenant:
  // the tenant offboarding erasure drill (offboard, drill, Run now, Stop for good, restore; never approved). $0, about
  // 15 min (the DRY RUN reports). Record it alone: --record DRILL-01 --include-writable.
  'cis-admin/drill-01.cjs',
  // Pilot rehearsal (root docs/ops/runbooks/pilot-rehearsal.md), the Booking E2E writers (root ADR 0006a A10e) on the
  // synthetic rehearsal agency only, each with the run's Booking seeder output (env UAT_BOOKING_FIXTURES). $0. Record
  // in this order, after the agency's trip is booked (step 8): REH-09-supplier; REH-11-maker, then REH-11-checker.
  'booking/reh-09-supplier.cjs',
  'booking/reh-11-maker.cjs',
  'booking/reh-11-checker.cjs',
  // The pilot rehearsal's guest traveller (identity traveller, no sign-in) on the synthetic agency pilot-rehearsal-01
  // (runbook docs/ops/runbooks/pilot-rehearsal.md). Record in this order, each after its runbook prerequisite:
  // REH-05 (paid) and REH-05.m after step 3 (tour X adopted); REH-06 after them; REH-08a after the CRM read of step 6.
  'tripplanner/reh-05.cjs',
  'tripplanner/reh-05-phone.cjs',
  'tripplanner/reh-06.cjs',
  'crm-web/reh-08a.cjs',
];
