// Shared parts of the pilot rehearsal studio scenarios REH-03-* .. REH-04b-* (AA-1086; root
// docs/ops/runbooks/pilot-rehearsal.md steps 3, 4 and 4b): the studio-rehearsal identity (the E2E OWNER of the
// synthetic agency pilot-rehearsal-01, lib/rehearsal.cjs), the studio API paths those scenarios write to, the reads
// they assert on (quota, adopted tours, slate, My Content, publish log) and the social-piece steps REH-04-linkedin and
// REH-04-facebook share. Not a scenario (leading underscore). The blog request and piece travel from REH-04-topics to
// REH-04-blog and REH-04-edit through lib/write-chain.cjs under the slug pilot-rehearsal-01; every reader falls back
// to the tenant's own data on Dev (the newest matching piece of My Content).
'use strict';
const { step } = require('../../lib/dryrun-page.cjs');
const { studioCall } = require('../../lib/uat-page.cjs');
const reh = require('../../lib/rehearsal.cjs');
const W = require('./_write.cjs');

const IDENTITY = 'studio-rehearsal';
const T = '/api/tenant/v1';
const BRAND = '/api/tenant/admin/brand-identity';
// Pathname patterns of the writes the rehearsal scenarios make (each one capped per run with limitWrites, except the
// free call-to-action check). _write.cjs PATHS cover the slate, angle and write calls.
const PATHS = {
  ...W.PATHS,
  brandSave: /^\/api\/tenant\/admin\/brand-identity$/,
  brandUpload: /^\/api\/tenant\/admin\/brand-identity\/upload$/,
  brandParse: /^\/api\/tenant\/admin\/brand-identity\/parse$/,
  piece: /^\/api\/tenant\/v1\/content-writing\/pieces\/[^/]+$/,
  publish: /^\/api\/tenant\/v1\/publish-log\/[^/]+\/publish$/,
  unpublish: /^\/api\/tenant\/v1\/publish-log\/[^/]+$/,
  wpSave: /^\/api\/tenant\/v1\/integrations\/wordpress$/,
  wpTest: /^\/api\/tenant\/v1\/integrations\/wordpress\/test$/,
  fbSave: /^\/api\/tenant\/v1\/integrations\/facebook$/,
  fbTest: /^\/api\/tenant\/v1\/integrations\/facebook\/test$/,
};
// allowWrites sources: record.cjs tests them on the full URL (origin + path, no query), so no leading ^.
const allow = (...names) => names.map((n) => PATHS[n].source.replace(/^\^/, ''));
const isCall = (res, re, method = 'POST') => res.request().method() === method && re.test(new URL(res.url()).pathname);

async function getJson(page, p, what) {
  const r = await studioCall(page, 'GET', p);
  if (r.status !== 200 || !r.data || typeof r.data !== 'object') throw new Error(`reading ${what} answered ${r.status}`);
  return r.data;
}

/** GET /v1/quota: { rewrites_used, rewrites_remaining, tours_per_month, ... }. */
const quota = (page) => getJson(page, `${T}/quota`, 'the rewrite quota');
/** GET /v1/marketplace tours: the agency's adopted tours, latest version each ({ published_tour_id, tour_id, status }). */
async function adopted(page) {
  const d = await getJson(page, `${T}/marketplace`, 'the adopted tours');
  return Array.isArray(d.tours) ? d.tours : [];
}
/** GET /v1/slate: topics per channel, refresh state ({ refreshing, finished_at, status }) and blog_topics. */
const slate = (page) => getJson(page, `${T}/slate`, 'the topic slate');
/** GET /v1/publish-log rows ({ publish_id, piece_id, channel, status, external_url }). */
async function publishLog(page) {
  const d = await getJson(page, `${T}/publish-log`, 'the publish log');
  return Array.isArray(d.data) ? d.data : [];
}

/**
 * Tour X's catalog row, read page by page from GET /v1/tours/pool (newest first, 100 a page, at most 20 pages).
 * Throws when X is not in the agency's catalog (retired, paused or a wrong id).
 */
async function findTourX(page) {
  const x = reh.tourX();
  for (let p = 1; p <= 20; p++) {
    const d = await getJson(page, `${T}/tours/pool?page=${p}&page_size=100`, 'the tour catalog');
    const hit = reh.findTour(d.data, x);
    if (hit) return hit;
    const pages = (d.pagination && d.pagination.pages) || 1;
    if (p >= pages) break;
  }
  throw new Error('tour X (UAT_REH_TOUR_X) is not in the agency catalog: check the id, or pick the fallback tour');
}

/** The newest ready piece of `channel` in My Content (from the hand-over file first for the blog). */
async function readyPiece(page, channel) {
  const items = await W.reviews(page);
  if (channel === 'blog') {
    const fromChain = (W.chain.read(reh.TENANT.slug) || {}).piece_id;
    const hit = items.find((i) => i.piece_id === fromChain && i.channel === 'blog' && i.ready_state === 'ready');
    if (hit) return hit;
  }
  return W.chain.newest(items, { channel, ready: true });
}

const panel = (page) => page.getByTestId('writer-panel').first();

/**
 * The steps of one social piece (REH-04-linkedin, REH-04-facebook): open Social Posts on the channel's tab, pick its
 * top topic, choose a goal, see the three angles, write with the recommended one and wait for the finished piece with
 * its AI notice. `counts` = the limitWrites counter of the scenario (registered in its first step).
 */
function socialSteps(channel, label, state) {
  const { check } = require('../../lib/dryrun-page.cjs');
  const tab = (page) => page.getByTestId('slate-tabstrip').locator('button[aria-pressed]').filter({ hasText: new RegExp(`^\\s*${label}`) }).first();
  return [
    step(`Social Posts holds a topic list for each channel. The owner opens the ${label} tab.`,
      `Mục Bài mạng xã hội có danh sách chủ đề cho từng kênh. Chủ đại lý mở thẻ ${label}.`,
      async (page, h) => {
        state.counts = await require('../../lib/uat-page.cjs').limitWrites(page, ['pick', 'goal', 'choose', 'write']
          .map((name) => ({ name, path: PATHS[name], max: name === 'write' ? 2 : 1 })));
        await check(page, h, '/portal/create/social', { heading: 'Social Posts' });
        await h.expect(page.getByRole('button', { name: /^(Update topics|Updating…)$/ })).toBeVisible({ timeout: 30_000 });
        await h.expect(page.locator('[aria-busy="true"]')).toHaveCount(0, { timeout: 30_000 });
        const t = tab(page);
        await h.expect(t).toBeVisible({ timeout: 30_000 });
        await h.click(t);
        await h.expect(t).toHaveAttribute('aria-pressed', 'true', { timeout: 15_000 });
        const pick = page.getByRole('button', { name: 'Pick to write' }).first();
        if (!(await pick.isVisible({ timeout: 30_000 }).catch(() => false))) {
          throw new Error(`no ${label} topic on the rehearsal agency (run the topic update of the article scenario first)`);
        }
      }),
    step('The owner picks the top topic. The writer asks for the goal of the post.',
      'Chủ đại lý chọn chủ đề đứng đầu. Trình viết hỏi mục tiêu của bài.',
      async (page, h) => {
        const picked = page.waitForResponse((r) => isCall(r, PATHS.pick), { timeout: 60_000 });
        await h.click(page.getByRole('button', { name: 'Pick to write' }).first());
        const res = await picked;
        if (res.status() !== 200) throw new Error(`picking the topic answered ${res.status()}`);
        await h.expect(panel(page)).toBeVisible({ timeout: 60_000 });
      }, { writes: true }),
    step('After the goal, the writer proposes three angles. This takes about a minute.',
      'Sau khi chọn mục tiêu, trình viết đề xuất ba góc tiếp cận. Việc này mất khoảng một phút.',
      async (page, h) => {
        const p = panel(page);
        const preferred = p.getByTestId('goal-introduction_awareness');
        const goal = (await preferred.count()) ? preferred : p.getByRole('radio').first();
        await h.expect(goal).toBeVisible({ timeout: 60_000 });
        await h.click(goal);
        const gen = p.getByRole('button', { name: 'Generate 3 angles' });
        if (await gen.isVisible({ timeout: 5_000 }).catch(() => false)) await h.click(gen);
        await h.expect(p.getByTestId('angle-2')).toBeVisible({ timeout: 300_000 });
      }, { writes: true }),
    step('Write with this angle starts the post at once. The steps show while it is written.',
      'Viết theo góc này sẽ bắt đầu viết bài ngay. Các bước hiện ra trong lúc bài được viết.',
      async (page, h) => {
        const p = panel(page);
        const recommended = p.locator('[data-testid^="angle-"]').filter({ has: page.getByText('Recommended', { exact: true }) });
        const card = (await recommended.count()) ? recommended.first() : p.getByTestId('angle-0');
        const button = card.getByRole('button', { name: 'Write with this angle' });
        await h.scrollTo(button, 'center');
        await W.startWrite(page, h, p, () => h.click(button));
        await h.expect(p.getByTestId('live-writer-status').first()).toBeVisible({ timeout: 60_000 });
      }, { writes: true }),
    step(`The finished ${label} post carries the AI notice and is saved in My Content. This is the end of the scenario.`,
      `Bài ${label} hoàn thành kèm thông báo về AI và được lưu trong Nội dung của tôi. Kết thúc kịch bản.`,
      async (page, h) => {
        await h.expect(page.getByTestId('writer-panel-result').first()).toBeVisible({ timeout: 900_000 });
        await h.expect(panel(page).getByTestId('ai-notice').first()).toBeVisible({ timeout: 30_000 });
        const c = state.counts;
        if (c.pick !== 1 || c.choose !== 1 || c.write < 1 || c.write > 2) throw new Error(`unexpected write counts ${JSON.stringify(c)}`);
      }),
  ];
}

module.exports = {
  IDENTITY, T, BRAND, PATHS, allow, isCall, getJson, quota, adopted, slate, publishLog, findTourX, readyPiece, panel,
  socialSteps, reh, W,
};
