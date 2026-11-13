// UAT scenario REH-04-facebook (pilot rehearsal step 4; root docs/ops/runbooks/pilot-rehearsal.md): the agency owner writes
// one Facebook post from the topics REH-04-topics proposed: the Facebook tab of Social Posts -> the top topic -> a goal -> three
// angles -> Write with this angle -> the finished post with its AI notice.
// The post is the one REH-04b-facebook publishes on the Facebook test Page (the cost table counts it with the blog and
// the LinkedIn post: three pieces).
// PAID: the angles and the post (writing model, about 0.1-0.2 USD, CIS LLM ledger, stage T9). Runs only with
// --allow-paid, on pilot-rehearsal-01 only (pilot guard). Each write (pick, goal, choose) passes at most once and the
// write at most twice (422 asks for a call to action); any other write is aborted and fails the take.
// Given: the rehearsal owner, topics updated by REH-04-topics. Then: one ready Facebook post in My Content. 1440 x 900.
const { HOSTS } = require('../../lib/dryrun-page.cjs');
const { rw } = require('../../lib/uat-page.cjs');
const R = require('./_rehearsal.cjs');

const state = { counts: null };

module.exports = rw({
  id: 'REH-04-facebook',
  app: 'content-studio',
  identity: R.IDENTITY,
  paid: true,
  title: 'Pilot rehearsal: write one Facebook post',
  titleVi: 'Diễn tập pilot: viết một bài Facebook',
  baseURL: HOSTS.partner,
  allowWrites: R.allow('pick', 'goal', 'choose', 'write', 'ctaCheck'),
  steps: R.socialSteps('facebook', 'Facebook', state),
});
