// The UAT dry-run set (AA-1009, tools/uat/dryrun.cjs): every public or read-only scenario, in run order. Paths are
// relative to this folder. A scenario here must be read-only: the runner forces the read-only guard (every non-GET
// request aborted and listed) and blocks the paid model paths, but a step that clicks a write button still fails.
// Add a scenario = add one line here and its id to the plan's §4 "Dry-run set"
// (docs/audits/2026-10-30-S260-uat-video-plan/README.md). Ids are unique (the runner checks). Every id here has a row
// in tools/uat/catalogue.json that is live, writes nothing and costs nothing (tests/catalogue.test.cjs).
module.exports = [
  // TripPlanner, public (no sign-in). The AI paths and the map planner are not in the dry run.
  'tripplanner/tp-pub-01.cjs',
  'tripplanner/tp-02.cjs',
  'tripplanner/tp-07.cjs',
  'tripplanner/tp-pub-02.cjs',
  // Agency host, public legal pages.
  'partner-portal/portal-pub-01.cjs',
  // Content studio, the E2E tenant's viewer (password + authenticator).
  'content-studio/prt-01.cjs',
  'content-studio/prt-03.cjs',
  'content-studio/prt-09.cjs',
  'content-studio/prt-10.cjs',
  // AA-855 round 1, read only (the write and paid ones, PRT-02 / PRT-06 / PRT-14, and the after-lane PRT-13 are not here).
  'content-studio/prt-04.cjs',
  'content-studio/prt-05.cjs',
  'content-studio/prt-08.cjs',
  'content-studio/x-04.cjs',
  // AA-855 W-04: the audit editor exports the article and a social post (GET only, $0). studio-audit can write, so the
  // runner leaves it out unless --include-writable; the paid W-01..W-03 are in write-set.cjs, never here.
  'content-studio/w-04.cjs',
  // CRM web, the owner of the invented review agency. That account CAN write (the CRM has no read-only role): the runner
  // leaves these out unless --include-writable, and only its browser guard keeps them read-only.
  'crm-web/crm-01.cjs',
  'crm-web/crm-02.cjs',
  'crm-web/crm-05.cjs',
  'crm-web/crm-07.cjs',
  // CIS admin, the Dev-only E2E CIS admin (read-only session; e-mail code, MFA admin profile).
  'cis-admin/cis-01.cjs',
  'cis-admin/cis-03.cjs',
  'cis-admin/cis-04.cjs',
  'cis-admin/cis-05.cjs',
  'cis-admin/cis-06.cjs',
  'cis-admin/cis-08.cjs',
  'cis-admin/cis-11.cjs',
  'cis-admin/cis-12.cjs',
  // Booking staff admin, the WORKFORCE E2E Booking staff (read-only session; e-mail code).
  'booking/bk-01.cjs',
  'booking/bk-05.cjs',
  'booking/bk-06.cjs',
  'booking/bk-07.cjs',
  'booking/bk-08.cjs',
  'booking/bk-10.cjs',
  // Pilot rehearsal (root docs/ops/runbooks/pilot-rehearsal.md), the staff evidence that holds while the synthetic
  // rehearsal agency is kept as a fixture: step 0 baseline and the step 1 results in CIS, the CRM console and Booking.
  // The state-dependent ones (prices, members, the budget override) are recorded with run.sh, not in the dry run.
  'cis-admin/reh-00-baseline.cjs',
  'cis-admin/reh-01-provisioned.cjs',
  'cis-admin/reh-01-crm-agency.cjs',
  'booking/reh-01-booking-partner.cjs',
];
