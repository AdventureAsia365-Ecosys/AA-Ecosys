// UAT scenario PRT-06 (AA-855 round 1, catalogue.json): write ONE social piece with AI. PAID: the angle step and the
// write call the writing model (a few cents per piece, logged by CIS in its LLM ledger). Never part of the dry run.
// Runs only with UAT_ALLOW_PAID=1 (prepare() refuses otherwise) and writes at most one piece per run: the browser guard
// lets the write path through (allowWrites), and a page route in front of it passes only the FIRST write request; a
// second is aborted before it leaves the browser and fails the take. The default for round 1 is to show the pieces
// already written (PRT-04, PRT-08, X-04) at no cost.
// Given: the Content studio EDITOR of the E2E tenant (lib/signin.cjs studio-editor), a slate with at least one topic.
// When:  they pick the first topic of the first channel, choose the first goal and the first angle.
// Then:  the writer panel shows the live steps, then the finished piece with the AI notice. Desktop 1440 x 900.
const { HOSTS, step, check } = require('../../lib/dryrun-page.cjs');
const { rw } = require('../../lib/uat-page.cjs');

const T = '/api/tenant/v1';
const WRITE = /\/api\/tenant\/v1\/content-writing\/requests\/[^/]+\/write$/;
let writes = 0;

const sc = rw({
  id: 'PRT-06',
  app: 'content-studio',
  identity: 'studio-editor',
  paid: true,
  title: 'Write a social piece with AI',
  titleVi: 'Viết một bài mạng xã hội bằng AI',
  baseURL: HOSTS.partner,
  // Pick a topic, choose a goal (angles are generated), choose an angle, write: nothing else may be written. Only the
  // template strings are escaped here: WRITE.source is a regex source already (escaping it again would match "\\/").
  allowWrites: [
    ...[`${T}/subjects/[^/]+/pick$`, `${T}/angle-gate/requests/[^/]+/(goal|choose)$`].map((x) => x.replace(/\//g, '\\/')),
    WRITE.source,
  ],
  steps: [
    step('Social Posts ranks topics for each channel. The editor picks the first one to write about.',
      'Bài mạng xã hội xếp hạng chủ đề cho từng kênh. Biên tập viên chọn chủ đề đầu tiên để viết.',
      async (page, h) => {
        // In front of the browser guard (a page route runs before the context's): the first write goes on to the guard,
        // any later one is aborted here, so a run never pays for a second piece. Each one is counted.
        await page.route((u) => WRITE.test(u.pathname), (route) => {
          if (route.request().method() !== 'POST') return route.fallback();
          writes++;
          return writes === 1 ? route.fallback() : route.abort('blockedbyclient');
        });
        await check(page, h, '/portal/create/social', { heading: 'Social Posts' });
        const pick = page.getByRole('button', { name: 'Pick to write' }).first();
        await h.expect(pick).toBeVisible({ timeout: 30_000 });
        await h.click(pick);
        await h.expect(page.getByTestId('writer-panel').first()).toBeVisible({ timeout: 60_000 });
      }, { writes: true }),
    step('The writer asks for the goal of the post, then offers three angles. The agency always chooses.',
      'Trình viết hỏi mục tiêu của bài, rồi đưa ra ba góc tiếp cận. Đại lý luôn là người chọn.',
      async (page, h) => {
        const panel = page.getByTestId('writer-panel').first();
        const goal = panel.getByRole('radio').or(panel.locator('[role="button"][aria-pressed], button[aria-pressed]')).first();
        await h.expect(goal).toBeVisible({ timeout: 60_000 });
        await h.click(goal);
        await h.expect(panel.getByRole('button', { name: 'Write with this angle' }).first()).toBeVisible({ timeout: 180_000 });
      }, { writes: true }),
    step('Choosing an angle starts the writing at once. The steps show while the piece is written.',
      'Chọn một góc là bắt đầu viết ngay. Các bước hiện ra trong lúc bài được viết.',
      async (page, h) => {
        if (writes) throw new Error('a piece was already requested in this run (one paid piece per run)');
        await h.click(page.getByTestId('writer-panel').first().getByRole('button', { name: 'Write with this angle' }).first());
        await h.expect(page.getByTestId('live-writer-status').first()).toBeVisible({ timeout: 60_000 });
      }, { writes: true }),
    step('The finished piece carries the AI notice and can be exported or opened in My Content. This is the end of the scenario.',
      'Bài hoàn thành kèm thông báo về AI, có thể xuất file hoặc mở trong Nội dung của tôi. Kết thúc kịch bản.',
      async (page, h) => {
        await h.expect(page.getByTestId('writer-panel-result').first()).toBeVisible({ timeout: 300_000 });
        await h.expect(page.getByTestId('writer-panel').first().getByTestId('ai-notice').first()).toBeVisible({ timeout: 30_000 });
        if (writes !== 1) throw new Error(`${writes} write requests in this run (exactly one expected)`);
      }),
  ],
});

module.exports = sc;
