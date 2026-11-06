// UAT scenario W-02 (AA-855 round 1, catalogue.json): pick an article topic from the Slate and choose an angle.
// PAID: the three angles (writing model) and, because choosing an angle starts the write at once (one click, no
// confirm step in the studio), the article itself; about 0.15-0.2 USD a run, in the CIS LLM ledger. When the tenant
// has no article topic left, Update topics asks for new ones first (a ranking call, about 0.01 USD). Runs only with
// --allow-paid on the ONE audit tenant of the run. Each of its writes (refresh, pick, goal, choose, write) passes at
// most once (a page route aborts a second one); any other write is aborted by the browser guard and fails the take.
// Idempotent enough to re-run: it always picks a topic still proposed (never one already used), deletes nothing.
// Hands the request and piece ids to W-03 / W-04 (lib/write-chain.cjs).
// Given: the studio-audit editor on the audit tenant. When: Articles -> Pick to write -> a goal -> Generate 3 angles ->
// Write with this angle. Then: the writer panel shows the article being written. 1440 x 900.
const { HOSTS, step, check } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const { PATHS, allow, isPost, startWrite, chain, auditTenant } = require('./_write.cjs');

let counts = null;
let hasTopic = false;
const PICK = 'Pick to write';
const panel = (page) => page.getByTestId('writer-panel').first();

const sc = rw({
  id: 'W-02',
  app: 'content-studio',
  identity: 'studio-audit',
  paid: true,
  title: 'Pick an article topic and choose an angle',
  titleVi: 'Chọn một chủ đề bài viết và chọn góc tiếp cận',
  baseURL: HOSTS.partner,
  allowWrites: allow('refresh', 'pick', 'goal', 'choose', 'write', 'ctaCheck'),
  steps: [
    step('Articles ranks topics from what travellers search for and what the agency\'s tours offer.',
      'Mục Bài viết xếp hạng chủ đề theo điều khách tìm kiếm và điều các tour của đại lý có.',
      async (page, h) => {
        // The write may be sent twice only when the first answered 422 (no call to action yet): see startWrite().
        counts = await limitWrites(page, ['refresh', 'pick', 'goal', 'choose', 'write']
          .map((name) => ({ name, path: PATHS[name], max: name === 'write' ? 2 : 1 })));
        await check(page, h, '/portal/create/article', { heading: 'Articles' });
        const pick = page.getByRole('button', { name: PICK }).first();
        const empty = page.getByText(/No new topics right now|Nothing here yet/).first();
        await h.expect(pick.or(empty).first()).toBeVisible({ timeout: 60_000 });
        hasTopic = await pick.isVisible();
      }),
    step('The editor picks the top topic. When none is left, Update topics proposes new ones first.',
      'Biên tập viên chọn chủ đề đứng đầu. Khi không còn chủ đề nào, bấm Cập nhật chủ đề để có chủ đề mới trước.',
      async (page, h) => {
        const pick = page.getByRole('button', { name: PICK }).first();
        if (!hasTopic) {
          // Update topics runs in the background (a banner says so); wait until a topic shows or the update ends.
          await h.click(page.getByRole('button', { name: 'Update topics' }));
          const updating = page.getByText(/^Updating topics in the background/).first();
          await h.expect(updating.or(pick).first()).toBeVisible({ timeout: 60_000 });
          await h.expect.poll(async () => ((await pick.isVisible()) || !(await updating.isVisible()) ? 'settled' : 'updating'),
            { timeout: 900_000, intervals: [5_000] }).toBe('settled');
          if (!(await pick.isVisible({ timeout: 15_000 }).catch(() => false))) {
            throw new Error(`no article topic on ${auditTenant().slug} even after Update topics: run again with another UAT_STUDIO_TENANT`);
          }
        }
        const picked = page.waitForResponse((r) => isPost(r, PATHS.pick), { timeout: 60_000 });
        await h.click(pick);
        const res = await picked;
        if (res.status() !== 200) throw new Error(`picking the topic answered ${res.status()}`);
        const body = await res.json();
        chain.write(auditTenant().slug, { request_id: body.request_id, piece_id: null, channel: 'blog' });
        await h.expect(panel(page)).toBeVisible({ timeout: 60_000 });
      }, { writes: true }),
    step('The writer asks for the goal of the article, then proposes three angles. This takes about a minute.',
      'Trình viết hỏi mục tiêu của bài, rồi đề xuất ba góc tiếp cận. Việc này mất khoảng một phút.',
      async (page, h) => {
        const p = panel(page);
        const preferred = p.getByTestId('goal-introduction_awareness');
        const goal = (await preferred.count()) ? preferred : p.getByRole('radio').first();
        await h.expect(goal).toBeVisible({ timeout: 60_000 });
        await h.click(goal);
        await h.click(p.getByRole('button', { name: 'Generate 3 angles' }));
        await h.expect(p.getByTestId('angle-2')).toBeVisible({ timeout: 300_000 });
      }, { writes: true }),
    step('Each angle says why it works and how it fits the topic. One is recommended; the agency always chooses.',
      'Mỗi góc nói vì sao hiệu quả và hợp với chủ đề thế nào. Một góc được đề xuất; đại lý luôn là người chọn.',
      async (page, h) => {
        const p = panel(page);
        for (const i of [0, 1, 2]) {
          const card = p.getByTestId(`angle-${i}`);
          await h.scrollTo(card, 'center');
          await h.hover(card);
        }
      }),
    step('Write with this angle chooses it and starts the article at once; a brand without a call to action is asked for one. The next scenario follows the writing. This is the end of the scenario.',
      'Viết theo góc này sẽ chọn góc đó và bắt đầu viết bài ngay; thương hiệu chưa có lời kêu gọi hành động sẽ được hỏi một câu. Kịch bản sau theo dõi phần viết. Kết thúc kịch bản.',
      async (page, h) => {
        const p = panel(page);
        const recommended = p.locator('[data-testid^="angle-"]').filter({ has: page.getByText('Recommended', { exact: true }) });
        const card = (await recommended.count()) ? recommended.first() : p.getByTestId('angle-0');
        const button = card.getByRole('button', { name: 'Write with this angle' });
        await h.scrollTo(button, 'center');
        const body = await startWrite(page, h, p, () => h.click(button));
        chain.write(auditTenant().slug, { piece_id: body.piece_id });
        await h.expect(p.getByTestId('live-writer-status').first()).toBeVisible({ timeout: 60_000 });
        for (const [k, n] of Object.entries(counts)) if (n > (k === 'write' ? 2 : 1)) throw new Error(`${n} ${k} requests in this run`);
        if (counts.choose !== 1) throw new Error('the angle was not chosen exactly once');
      }, { writes: true }),
  ],
});

module.exports = sc;
