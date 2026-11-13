// UAT scenario REH-04b-facebook (pilot rehearsal step 4b; root docs/ops/runbooks/pilot-rehearsal.md): the agency owner
// connects the Facebook test channel (when the agency has none yet), publishes the Facebook post written in step 4,
// takes it down and publishes it again; one post only is live at the end.
// The Facebook test Page is the tech lead's own test Page: its id is blurred on screen, facebook.com is never opened.
// Writes: the connection save + test (once each, only when not connected), two publishes and one unpublish, on the
// test channel and pilot-rehearsal-01 only (pilot guard). No model call: cost $0. The secret of the test channel
// (Secrets Manager aa-cis/dev/e2e-facebook-test) is read in memory and typed into masked fields.
// Teardown: REH-04b-takedown removes the live post. Re-record after a takedown only (a live post stops step 1).
// Env: UAT_REH_TOUR_X. Given: the step 4 scenarios ran. 1440 x 900.
const { HOSTS } = require('../../lib/dryrun-page.cjs');
const { rw } = require('../../lib/uat-page.cjs');
const R = require('./_rehearsal.cjs');
const P = require('./_publish.cjs');

const state = {};

module.exports = rw({
  id: 'REH-04b-facebook',
  app: 'content-studio',
  identity: R.IDENTITY,
  title: 'Pilot rehearsal: publish to Facebook, take down, publish again',
  titleVi: 'Diễn tập pilot: đăng lên Facebook, gỡ xuống rồi đăng lại',
  baseURL: HOSTS.partner,
  allowWrites: P.allowFor('facebook'),
  mask: P.CH.facebook.mask,
  steps: P.publishSteps('facebook', state),
});
