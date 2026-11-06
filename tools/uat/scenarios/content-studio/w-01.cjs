// UAT scenario W-01 (AA-855 round 1, catalogue.json): rewrite one Adventure Asia tour for the agency's brand.
// PAID: one tour rewrite by the writing model (about 0.2 USD, in the CIS LLM ledger). Runs only with --allow-paid
// (dryrun.cjs; prepare() refuses otherwise) on the ONE audit tenant of the run (lib/studio-audit.cjs, pilot guard).
// Writes exactly one thing: POST .../tours/pool/<id>/rewrite, once (a page route aborts any second one); every other
// write is aborted by the browser guard and fails the take. Idempotent enough to re-run: it picks a tour the tenant
// has not rewritten yet, and never deletes anything (each run adds one version to My Tours).
// Given: the studio-audit editor on the audit tenant, a catalog with at least one tour not yet in My Tours.
// When:  they open the tour in the Marketplace, press Rewrite this tour, follow it in My Tours, export the DOCX.
// Then:  the new version is ready in My Tours; the DOCX download carries the AI mark in its properties. 1440 x 900.
const { HOSTS, step, check } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites, downloadBytes, zipEntry, AI_MARK } = require('../../lib/uat-page.cjs');
const { PATHS, allow, isPost, freeTour } = require('./_write.cjs');

let counts = null;
let tour = null; // the catalog row chosen in step 1

const sc = rw({
  id: 'W-01',
  app: 'content-studio',
  identity: 'studio-audit',
  paid: true,
  title: 'Rewrite an Adventure Asia tour for the agency brand',
  titleVi: 'Viết lại một tour của Adventure Asia theo thương hiệu đại lý',
  baseURL: HOSTS.partner,
  allowWrites: allow('rewrite'),
  steps: [
    step('The Marketplace holds every Adventure Asia tour the agency can sell. The editor looks for one that is not in My Tours yet.',
      'Kho tour chứa mọi tour của Adventure Asia mà đại lý có thể bán. Biên tập viên tìm một tour chưa có trong Tour của tôi.',
      async (page, h) => {
        counts = await limitWrites(page, [{ name: 'rewrite', path: PATHS.rewrite, max: 1 }]);
        const poolRes = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/tenant/v1/tours/pool'
          && r.request().method() === 'GET' && r.status() === 200, { timeout: 60_000 });
        await check(page, h, '/portal/tours', { heading: 'Marketplace' });
        tour = freeTour(await (await poolRes).json());
        if (!tour) throw new Error('no tour on the first catalog page is free to rewrite (all in My Tours or closed)');
        await h.expect(page.getByTestId('marketplace-grid')).toBeVisible({ timeout: 30_000 });
      }),
    step('A tour opens with its summary, its highlights and the day-by-day itinerary.',
      'Mở một tour sẽ thấy tóm tắt, điểm nổi bật và lịch trình từng ngày.',
      async (page, h) => {
        const card = page.getByRole('button', { name: `Open ${tour.aa_name}`, exact: true }).first();
        await h.scrollTo(card, 'center');
        await h.click(card);
        await h.expect(page.getByTestId('marketplace-drawer')).toBeVisible({ timeout: 30_000 });
        await h.expect(page.getByRole('button', { name: 'Rewrite this tour' })).toBeVisible({ timeout: 30_000 });
      }),
    step('Rewrite this tour asks the writer for the agency\'s own version, in the agency\'s brand voice. It runs in the background.',
      'Viết lại tour này yêu cầu người viết tạo phiên bản riêng của đại lý, theo giọng thương hiệu của đại lý. Việc này chạy nền.',
      async (page, h) => {
        const started = page.waitForResponse((r) => isPost(r, PATHS.rewrite), { timeout: 60_000 });
        await h.click(page.getByRole('button', { name: 'Rewrite this tour' }));
        const res = await started;
        if (res.status() >= 300) throw new Error(`the rewrite request answered ${res.status()}`);
        await h.expect(page.getByText('Rewrite started').first()).toBeVisible({ timeout: 30_000 });
        if (counts.rewrite !== 1) throw new Error(`${counts.rewrite} rewrite requests in this run (exactly one expected)`);
      }, { writes: true }),
    step('My Tours follows the new version while the writer works on it.',
      'Tour của tôi theo dõi phiên bản mới trong lúc người viết làm việc.',
      async (page, h) => {
        const follow = page.getByRole('button', { name: 'Follow it in My Tours' });
        if (await follow.isVisible({ timeout: 30_000 }).catch(() => false)) {
          await h.click(follow);
          await page.waitForURL((u) => u.pathname === '/portal/tours/mine', { timeout: 30_000 });
        } else {
          await h.goto(`/portal/tours/mine?tour_id=${encodeURIComponent(tour.tour_id)}`);
        }
        await h.expect(page.locator('h1').first()).toContainText('My Tours', { timeout: 30_000 });
        const progress = page.getByRole('button', { name: 'View progress' }).first();
        await h.expect(progress).toBeVisible({ timeout: 60_000 });
        await h.click(progress);
        await h.expect(page.getByTestId('writer-panel')).toBeVisible({ timeout: 30_000 });
      }),
    step('The writer shows its steps live. When it finishes, the agency\'s version is saved in My Tours.',
      'Người viết hiện từng bước trực tiếp. Khi xong, phiên bản của đại lý được lưu trong Tour của tôi.',
      async (page, h) => {
        const ready = page.getByTestId('tour-rewrite-ready');
        const failed = page.getByTestId('tour-rewrite-failed');
        await h.expect(ready.or(failed).first()).toBeVisible({ timeout: 900_000 });
        if (await failed.isVisible().catch(() => false)) throw new Error('the rewrite did not finish (the panel offers a retry; none is made here)');
      }),
    step('Export DOCX downloads the new version as a Word file. Its properties say the text is AI-generated.',
      'Xuất DOCX tải phiên bản mới về dạng file Word. Thuộc tính của file ghi rõ văn bản do AI tạo.',
      async (page, h) => {
        const download = page.waitForEvent('download', { timeout: 60_000 });
        await h.click(page.getByRole('button', { name: 'Export DOCX' }).first());
        const d = await download;
        if (!/^[^/\\]+\.docx$/.test(d.suggestedFilename())) throw new Error(`unexpected export file name ${d.suggestedFilename()}`);
        const core = zipEntry(await downloadBytes(d), 'docProps/core.xml');
        if (!core || !AI_MARK.docxKeywords.test(core.toString('utf8'))) throw new Error('the DOCX carries no AI mark in its properties');
      }),
    step('Open in My Tours shows the agency version, ready to edit or export. This is the end of the scenario.',
      'Mở trong Tour của tôi hiện phiên bản của đại lý, sẵn sàng để sửa hoặc xuất file. Kết thúc kịch bản.',
      async (page, h) => {
        await h.click(page.getByRole('button', { name: 'Open in My Tours' }).first());
        await h.expect(page.getByRole('dialog').filter({ hasText: tour.aa_name }).first()).toBeVisible({ timeout: 30_000 });
      }),
  ],
});

module.exports = sc;
