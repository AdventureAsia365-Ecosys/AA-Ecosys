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
  // AA-1086 pilot rehearsal, steps 3-4b (root docs/ops/runbooks/pilot-rehearsal.md): the E2E OWNER of the synthetic
  // agency pilot-rehearsal-01 (studio-rehearsal, pinned to that agency). Record in this order; the paid ones need
  // --allow-paid; env UAT_REH_TOUR_X names tour X. REH-04b-takedown is the teardown of the two publish scenarios.
  'content-studio/reh-03-brand.cjs',
  'content-studio/reh-03-adopt.cjs',
  'content-studio/reh-04-topics.cjs',
  'content-studio/reh-04-blog.cjs',
  'content-studio/reh-04-linkedin.cjs',
  'content-studio/reh-04-facebook.cjs',
  'content-studio/reh-04-edit.cjs',
  'content-studio/reh-04b-wordpress.cjs',
  'content-studio/reh-04b-facebook.cjs',
  'content-studio/reh-04b-takedown.cjs',
];
