// UAT scenario REH-04-blog (pilot rehearsal step 4, part 2; root docs/ops/runbooks/pilot-rehearsal.md): the article
// REH-04-topics started, followed until it is delivered to My Content. Record it right after REH-04-topics.
// PAID only when the angle was chosen but its write never started: the studio starts it on opening (POST .../write, at
// most twice when the first answers 422 for a missing call to action); about 0.1 USD. Runs only with --allow-paid, on
// pilot-rehearsal-01 only (pilot guard); any other write is aborted and fails the take.
// Finds the request in lib/write-chain.cjs (slug pilot-rehearsal-01), else the agency's newest article of the last
// 6 hours on Dev. Given: REH-04-topics ran. When: the owner opens the writer on that request and waits.
// Then: the article is ready and opens in My Content with its export buttons. 1440 x 900.
const { HOSTS, step, check } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const R = require('./_rehearsal.cjs');

const { reh, W } = R;
const SLUG = reh.TENANT.slug;
const READY = /^(Content ready\.|Your content is ready)/;
let counts = null;

const sc = rw({
  id: 'REH-04-blog',
  app: 'content-studio',
  identity: R.IDENTITY,
  paid: true,
  title: 'Pilot rehearsal: the blog article is written and delivered',
  titleVi: 'Diễn tập pilot: bài blog được viết và giao cho đại lý',
  baseURL: HOSTS.partner,
  allowWrites: R.allow('write', 'ctaCheck'),
  steps: [
    step('The writer opens on the article the owner started: the angle, the goal and the channel.',
      'Trình viết mở bài mà chủ đại lý đã bắt đầu: góc tiếp cận, mục tiêu và kênh.',
      async (page, h) => {
        counts = await limitWrites(page, [{ name: 'write', path: R.PATHS.write, max: 2 }]);
        await check(page, h, '/portal/content', { heading: 'My Content' });
        let requestId = (W.chain.read(SLUG) || {}).request_id || null;
        if (!requestId) {
          const latest = W.chain.newest(await W.reviews(page), { channel: 'blog', sinceMs: W.chain.MAX_AGE_MS });
          requestId = latest ? latest.request_id : null;
        }
        if (!requestId) throw new Error('no article started on the rehearsal agency in the last hours: record REH-04-topics first');
        W.chain.write(SLUG, { request_id: requestId, channel: 'blog' });
        const written = page.waitForResponse((r) => R.isCall(r, R.PATHS.write), { timeout: 20_000 }).catch(() => null);
        await h.goto(`/portal/create/write?resume_request_id=${encodeURIComponent(requestId)}`);
        await h.expect(page.getByText('Angle:', { exact: true }).first()).toBeVisible({ timeout: 60_000 });
        let res = await written;
        if (res && res.status() === 422) res = await W.typeCtaAndWrite(page, h, page);
        if (res && res.status() !== 202) throw new Error(`starting the article answered ${res.status()}`);
        if (res) W.chain.write(SLUG, { piece_id: (await res.json()).piece_id });
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
    step('The article is delivered: it is saved in My Content with the AI-assisted label and its export buttons. This is the end of the scenario.',
      'Bài đã được giao: lưu trong Nội dung của tôi, kèm nhãn có AI hỗ trợ và các nút xuất file. Kết thúc kịch bản.',
      async (page, h) => {
        const popup = page.getByRole('button', { name: 'Open in My Content' });
        if (await popup.isVisible().catch(() => false)) await h.click(popup.first());
        else await h.click(page.getByText('View, edit, or export it in My Content').first());
        await page.waitForURL((u) => u.pathname === '/portal/content' && u.searchParams.has('piece'), { timeout: 30_000 });
        W.chain.write(SLUG, { piece_id: new URL(page.url()).searchParams.get('piece') });
        const drawer = page.getByRole('dialog').first();
        await h.expect(drawer).toBeVisible({ timeout: 30_000 });
        await h.expect(page.getByTestId('review-drawer-ai-badge').first()).toBeVisible({ timeout: 30_000 });
        await h.expect(drawer.getByRole('button', { name: 'Export HTML file' })).toBeVisible({ timeout: 30_000 });
      }),
  ],
});

module.exports = sc;
