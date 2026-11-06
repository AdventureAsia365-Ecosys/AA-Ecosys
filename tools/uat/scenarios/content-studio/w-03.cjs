// UAT scenario W-03 (AA-855 round 1, catalogue.json): the blog article written from the angle chosen in W-02, followed
// to delivery. Record it right after W-02 (the write is still running then; later it simply shows the finished piece).
// PAID only in one case: when W-02 chose the angle but its write never started, the studio starts it on opening
// (POST .../write, at most once, or twice when the first answers 422 for a missing call to action); about 0.1 USD.
// Runs only with --allow-paid on the ONE audit tenant of the run; any other write is aborted and fails the take.
// Finds W-02's request in lib/write-chain.cjs, else the tenant's newest article of the last 6 hours on Dev.
// Given: W-02 ran on this audit tenant. When: the editor opens the writer on that request and waits.
// Then:  the article is ready and opens in My Content. 1440 x 900.
const { HOSTS, step, check } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const { PATHS, allow, isPost, typeCtaAndWrite, reviews, chain, auditTenant } = require('./_write.cjs');

let counts = null;
const READY = /^(Content ready\.|Your content is ready)/;

const sc = rw({
  id: 'W-03',
  app: 'content-studio',
  identity: 'studio-audit',
  paid: true,
  title: 'Write the blog article from the chosen angle and see it delivered',
  titleVi: 'Viết bài blog theo góc đã chọn và nhận bài hoàn chỉnh',
  baseURL: HOSTS.partner,
  allowWrites: allow('write', 'ctaCheck'),
  steps: [
    step('The writer opens on the article the editor started from the chosen angle: the angle, the goal and the channel.',
      'Trình viết mở bài mà biên tập viên đã bắt đầu theo góc đã chọn: góc tiếp cận, mục tiêu và kênh.',
      async (page, h) => {
        counts = await limitWrites(page, [{ name: 'write', path: PATHS.write, max: 2 }]);
        const slug = auditTenant().slug;
        // Open My Content first (signed in, the studio's own list), then find the request.
        await check(page, h, '/portal/content', { heading: 'My Content' });
        let requestId = (chain.read(slug) || {}).request_id || null;
        if (!requestId) {
          const latest = chain.newest(await reviews(page), { channel: 'blog', sinceMs: chain.MAX_AGE_MS });
          requestId = latest ? latest.request_id : null;
        }
        if (!requestId) throw new Error(`no article started on ${slug} in the last hours: run W-02 first`);
        chain.write(slug, { request_id: requestId, channel: 'blog' });
        // The studio starts the write itself when the chosen angle has none yet: wait for that answer in that case.
        const written = page.waitForResponse((r) => isPost(r, PATHS.write), { timeout: 20_000 }).catch(() => null);
        await h.goto(`/portal/create/write?resume_request_id=${encodeURIComponent(requestId)}`);
        await h.expect(page.getByText('Angle:', { exact: true }).first()).toBeVisible({ timeout: 60_000 });
        let res = await written;
        if (res && res.status() === 422) res = await typeCtaAndWrite(page, h, page);
        if (res && res.status() !== 202) throw new Error(`starting the article answered ${res.status()}`);
        if (res) chain.write(slug, { piece_id: (await res.json()).piece_id });
      }, { writes: true }),
    step('While the article is being written, each step shows live. A blog article takes a few minutes.',
      'Trong lúc bài đang được viết, từng bước hiện ra trực tiếp. Một bài blog mất vài phút.',
      async (page, h) => {
        const ready = page.getByText(READY).first();
        const broken = page.getByText('Something went wrong while writing this content').first();
        await h.expect(ready.or(broken).first()).toBeVisible({ timeout: 1_200_000 });
        if (await broken.isVisible().catch(() => false)) throw new Error('the article did not finish (the page offers a retry; none is made here)');
        if (counts.write > 2) throw new Error(`${counts.write} write requests in this run`);
      }),
    step('The article is delivered to the agency: it is saved in My Content with its text and the AI-assisted label. This is the end of the scenario.',
      'Bài được giao cho đại lý: lưu trong Nội dung của tôi, kèm nội dung và nhãn có AI hỗ trợ. Kết thúc kịch bản.',
      async (page, h) => {
        const popup = page.getByRole('button', { name: 'Open in My Content' });
        if (await popup.isVisible().catch(() => false)) await h.click(popup.first());
        else await h.click(page.getByText('View, edit, or export it in My Content').first());
        await page.waitForURL((u) => u.pathname === '/portal/content' && u.searchParams.has('piece'), { timeout: 30_000 });
        const pieceId = new URL(page.url()).searchParams.get('piece');
        chain.write(auditTenant().slug, { piece_id: pieceId });
        const drawer = page.getByRole('dialog').first();
        await h.expect(drawer).toBeVisible({ timeout: 30_000 });
        await h.expect(drawer.getByRole('button', { name: 'Export HTML file' })).toBeVisible({ timeout: 30_000 });
      }),
  ],
});

module.exports = sc;
