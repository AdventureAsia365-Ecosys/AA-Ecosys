// UAT scenario REH-04b-wordpress (pilot rehearsal step 4b; root docs/ops/runbooks/pilot-rehearsal.md): the agency owner
// connects the WordPress test channel (when the agency has none yet), publishes the edited blog article (it links to the agency planner for tour X),
// takes it down and publishes it again; one post only is live at the end.
// The live post page is opened and must carry the planner link and the AI mark on its <article>.
// Writes: the connection save + test (once each, only when not connected), two publishes and one unpublish, on the
// test channel and pilot-rehearsal-01 only (pilot guard). No model call: cost $0. The secret of the test channel
// (Secrets Manager aa-cis/dev/e2e-wordpress-test) is read in memory and typed into masked fields.
// Teardown: REH-04b-takedown removes the live post. Re-record after a takedown only (a live post stops step 1).
// Env: UAT_REH_TOUR_X. Given: the step 4 scenarios ran, REH-04-edit included. 1440 x 900.
const { HOSTS } = require('../../lib/dryrun-page.cjs');
const { rw } = require('../../lib/uat-page.cjs');
const R = require('./_rehearsal.cjs');
const P = require('./_publish.cjs');

const state = {};

module.exports = rw({
  id: 'REH-04b-wordpress',
  app: 'content-studio',
  identity: R.IDENTITY,
  title: 'Pilot rehearsal: publish to WordPress, take down, publish again',
  titleVi: 'Diễn tập pilot: đăng lên WordPress, gỡ xuống rồi đăng lại',
  baseURL: HOSTS.partner,
  allowWrites: P.allowFor('wordpress'),
  mask: P.CH.wordpress.mask,
  steps: P.publishSteps('wordpress', state),
});
