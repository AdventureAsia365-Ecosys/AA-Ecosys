// UAT scenario REH-04-topics (pilot rehearsal step 4, part 1; root docs/ops/runbooks/pilot-rehearsal.md): the agency
// owner updates the topics (timed), checks that every adopted tour has an article topic or a stated reason, picks the
// top article topic, chooses a goal and an angle, and the article starts. Record after REH-03-adopt (three tours done).
// PAID: the topic update (T7 slate, about 0.5-1.5 USD), the three angles and the article it starts (about 0.15-0.2
// USD); CIS LLM ledger. Runs only with --allow-paid, on pilot-rehearsal-01 only (pilot guard). Each write (refresh,
// pick, goal, choose, write) passes at most once (the write twice when the first answers 422 for a missing call to
// action); any other write is aborted and fails the take. The time of the topic update goes to result.json
// (meta.slate_refresh_seconds). Hands the request and piece ids to REH-04-blog / REH-04-edit (lib/write-chain.cjs).
// Given: the rehearsal owner, three adopted tours. When: Articles -> Update topics -> wait -> Pick to write -> goal ->
//        Generate 3 angles -> Write with this angle. Then: the writer panel shows the article being written. 1440 x 900.
const { HOSTS, step, check } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const R = require('./_rehearsal.cjs');

const { reh, W } = R;
const SLUG = reh.TENANT.slug;
const PICK = 'Pick to write';
let counts = null;
let startedAt = 0;

const sc = rw({
  id: 'REH-04-topics',
  app: 'content-studio',
  identity: R.IDENTITY,
  paid: true,
  title: 'Pilot rehearsal: update the topics and start an article',
  titleVi: 'Diễn tập pilot: cập nhật chủ đề và bắt đầu một bài viết',
  baseURL: HOSTS.partner,
  allowWrites: R.allow('refresh', 'pick', 'goal', 'choose', 'write', 'ctaCheck'),
  steps: [
    step('Articles ranks blog topics from what travellers search for and what the agency\'s tours offer.',
      'Mục Bài viết xếp hạng chủ đề blog theo điều khách tìm kiếm và điều các tour của đại lý có.',
      async (page, h) => {
        counts = await limitWrites(page, ['refresh', 'pick', 'goal', 'choose', 'write']
          .map((name) => ({ name, path: R.PATHS[name], max: name === 'write' ? 2 : 1 })));
        sc.meta = sc.meta || {};
        await check(page, h, '/portal/create/article', { heading: 'Articles' });
        await h.expect(page.getByRole('button', { name: /^(Update topics|Updating…)$/ })).toBeVisible({ timeout: 30_000 });
        if ((await R.adopted(page)).length < 1) throw new Error('no adopted tour on the rehearsal agency (record REH-03-adopt first)');
      }),
    step('Update topics asks for new topics from the agency\'s three tours. It runs in the background; the time is recorded.',
      'Cập nhật chủ đề yêu cầu chủ đề mới từ ba tour của đại lý. Việc này chạy nền; thời gian được ghi lại.',
      async (page, h) => {
        const before = await R.slate(page);
        if (before.refresh && before.refresh.refreshing) throw new Error('a topic update is already running: wait for it, then record again');
        const sent = page.waitForResponse((r) => R.isCall(r, R.PATHS.refresh), { timeout: 60_000 });
        startedAt = Date.now();
        await h.click(page.getByRole('button', { name: 'Update topics' }));
        const res = await sent;
        if (res.status() >= 300) throw new Error(`the topic update answered ${res.status()}`);
        await h.expect(page.getByText(/^Updating topics in the background/).first()).toBeVisible({ timeout: 60_000 });
        let after = null;
        for (const until = Date.now() + 1_200_000; ; await page.waitForTimeout(10_000)) {
          after = await R.slate(page);
          const f = after.refresh || {};
          if (!f.refreshing && f.finished_at && Date.parse(f.finished_at) >= startedAt - 5_000) break;
          if (Date.now() > until) throw new Error('the topic update did not finish within 20 minutes');
        }
        sc.meta.slate_refresh_seconds = Math.round((Date.parse(after.refresh.finished_at) - startedAt) / 1000);
        if (after.refresh.status === 'failed') throw new Error('the topic update failed');
        await h.goto('/portal/create/article');
        await h.expect(page.locator('h1').first()).toContainText('Articles', { timeout: 30_000 });
      }, { writes: true }),
    step('Every adopted tour now has an article topic, or the page says in plain words why it has none.',
      'Mỗi tour đã nhận giờ có chủ đề bài viết, hoặc trang ghi rõ bằng lời dễ hiểu vì sao chưa có.',
      async (page, h) => {
        const tours = await R.adopted(page);
        const bt = (await R.slate(page)).blog_topics;
        if (!bt || !Array.isArray(bt.tours)) throw new Error('the slate has no per-tour topic summary');
        const rows = new Map();
        for (const t of bt.tours) rows.set(String(t.tour_id), t);
        const missing = tours.filter((t) => !rows.has(String(t.tour_id)) && !rows.has(String(t.published_tour_id)));
        if (missing.length) throw new Error(`${missing.length} adopted tour(s) are not in the topic summary`);
        const silent = bt.tours.filter((t) => !(t.topics > 0) && !t.reason);
        if (silent.length) throw new Error(`${silent.length} tour(s) have no topic and no reason`);
        const without = bt.tours.filter((t) => !(t.topics > 0)).length;
        const note = page.getByTestId('blog-topics-note');
        if (without) {
          await h.scrollTo(note, 'center');
          await h.expect(note.getByTestId('blog-topics-note-row')).toHaveCount(Math.min(without, 5), { timeout: 30_000 });
        } else {
          await h.expect(note).toHaveCount(0);
        }
        await h.scrollTo(page.locator('h1').first(), 'start');
        await h.expect(page.getByRole('button', { name: PICK }).first()).toBeVisible({ timeout: 30_000 });
      }),
    step('The owner picks the top topic. The writer asks for the goal, then proposes three angles. This takes about a minute.',
      'Chủ đại lý chọn chủ đề đứng đầu. Trình viết hỏi mục tiêu, rồi đề xuất ba góc tiếp cận. Việc này mất khoảng một phút.',
      async (page, h) => {
        const picked = page.waitForResponse((r) => R.isCall(r, R.PATHS.pick), { timeout: 60_000 });
        await h.click(page.getByRole('button', { name: PICK }).first());
        const res = await picked;
        if (res.status() !== 200) throw new Error(`picking the topic answered ${res.status()}`);
        W.chain.write(SLUG, { request_id: (await res.json()).request_id, piece_id: null, channel: 'blog' });
        const p = R.panel(page);
        await h.expect(p).toBeVisible({ timeout: 60_000 });
        const preferred = p.getByTestId('goal-introduction_awareness');
        const goal = (await preferred.count()) ? preferred : p.getByRole('radio').first();
        await h.expect(goal).toBeVisible({ timeout: 60_000 });
        await h.click(goal);
        await h.click(p.getByRole('button', { name: 'Generate 3 angles' }));
        await h.expect(p.getByTestId('angle-2')).toBeVisible({ timeout: 300_000 });
      }, { writes: true }),
    step('Each angle says why it works. One is recommended; the agency always chooses.',
      'Mỗi góc nói vì sao hiệu quả. Một góc được đề xuất; đại lý luôn là người chọn.',
      async (page, h) => {
        for (const i of [0, 1, 2]) {
          const c = R.panel(page).getByTestId(`angle-${i}`);
          await h.scrollTo(c, 'center');
          await h.hover(c);
        }
      }),
    step('Write with this angle starts the article at once. The next scenario follows the writing. This is the end of the scenario.',
      'Viết theo góc này sẽ bắt đầu viết bài ngay. Kịch bản sau theo dõi phần viết. Kết thúc kịch bản.',
      async (page, h) => {
        const p = R.panel(page);
        const recommended = p.locator('[data-testid^="angle-"]').filter({ has: page.getByText('Recommended', { exact: true }) });
        const c = (await recommended.count()) ? recommended.first() : p.getByTestId('angle-0');
        const button = c.getByRole('button', { name: 'Write with this angle' });
        await h.scrollTo(button, 'center');
        const body = await W.startWrite(page, h, p, () => h.click(button));
        W.chain.write(SLUG, { piece_id: body.piece_id });
        await h.expect(p.getByTestId('live-writer-status').first()).toBeVisible({ timeout: 60_000 });
        for (const [k, n] of Object.entries(counts)) if (n > (k === 'write' ? 2 : 1)) throw new Error(`${n} ${k} requests in this run`);
        if (counts.refresh !== 1 || counts.choose !== 1) throw new Error('the topic update or the angle choice did not run exactly once');
      }, { writes: true }),
  ],
});

module.exports = sc;
