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
  // The pilot rehearsal, CRM part (runbook docs/ops/runbooks/pilot-rehearsal.md steps 6, 7, 8, 10; scenarios/crm/_reh.cjs):
  // the owner (crm-rehearsal) and the agent (crm-rehearsal-agent) of pilot-rehearsal-01, pinned there by the pilot guard.
  // Record in this order, each after the step before it in the whole rehearsal: REH-06 after the TripPlanner send;
  // REH-08c after Adventure Asia confirmed (instant departure, or the Booking staff step). REH-10b-ops-view (crm-staff,
  // read only) is not a write-set entry: record it with run.sh after REH-10.
  // REH-02b-agency-setup first, once per fresh seed (scenarios/crm/REHEARSAL.md): payment instructions, terms, waiver.
  'crm/reh-02b-agency-setup.cjs',
  'crm/reh-06-lead.cjs',
  'crm/reh-07-quote.cjs',
  'crm/reh-07b-approve.cjs',
  'crm/reh-08-accept.cjs',
  'crm/reh-08b-deposit.cjs',
  'crm/reh-08c-aa-confirmed.cjs',
  'crm/reh-10-portal.cjs',
];
