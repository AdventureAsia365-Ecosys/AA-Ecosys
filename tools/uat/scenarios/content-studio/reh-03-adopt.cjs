// UAT scenario REH-03-adopt (pilot rehearsal step 3, part 2; root docs/ops/runbooks/pilot-rehearsal.md): the agency
// owner adopts tour X and two more tours from the Marketplace in one bulk rewrite, follows tour X to its new version and
// exports it as a Word file with the AI mark. Record it right after REH-03-brand (the rewrites follow that brand).
// PAID: one rewrite per tour that is not adopted yet (at most 3, about 0.1-0.3 USD each, CIS LLM ledger, stage T2).
// Runs only with --allow-paid, on pilot-rehearsal-01 only (pilot guard). Writes exactly the rewrite POSTs (a page route
// lets at most 3 through and aborts any further one); every other write is aborted and fails the take. Re-run safe: a
// tour already adopted is not rewritten again; only the missing ones up to three adopted tours are started.
// Env: UAT_REH_TOUR_X = tour X's id (the catalog tour_id or its published id; runbook Fixtures).
// Given: the rehearsal owner, the brand of REH-03-brand saved. When: Marketplace -> search tour X -> tick it -> tick two
//        more -> Rewrite 3 tours -> My Tours -> X ready -> Export DOCX.
// Then:  tour X's card shows a photo and a price; the usage meter rises by the number of rewrites started; the three
//        tours finish; the DOCX answer carries X-AI-Generated: true and "ai-generated" in its properties. 1440 x 900.
const { HOSTS, step, check } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites, downloadBytes, zipEntry, AI_MARK } = require('../../lib/uat-page.cjs');
const R = require('./_rehearsal.cjs');

const TARGET = 3; // tour X and two more (runbook step 3)
let counts = null;
let x = null; // tour X's catalog row
let used0 = 0; // rewrites used before
let toStart = []; // catalog rows ticked for the bulk rewrite
const card = (page, name) => page.getByRole('button', { name: `Open ${name}`, exact: true }).first();
const tick = (page, name) => page.getByRole('checkbox', { name: `Select ${name}`, exact: true }).first();

const sc = rw({
  id: 'REH-03-adopt',
  app: 'content-studio',
  identity: R.IDENTITY,
  paid: true,
  title: 'Pilot rehearsal: adopt three tours and export one as Word',
  titleVi: 'Diễn tập pilot: nhận ba tour và xuất một tour ra file Word',
  baseURL: HOSTS.partner,
  allowWrites: R.allow('rewrite'),
  steps: [
    step('The Marketplace holds every Adventure Asia tour the agency can sell. The owner searches for the first tour to offer.',
      'Kho tour chứa mọi tour của Adventure Asia mà đại lý có thể bán. Chủ đại lý tìm tour đầu tiên muốn chào bán.',
      async (page, h) => {
        counts = await limitWrites(page, [{ name: 'rewrite', path: R.PATHS.rewrite, max: TARGET }]);
        await check(page, h, '/portal/tours', { heading: 'Marketplace', ready: '[data-testid="marketplace-views"]' });
        x = await R.findTourX(page);
        if (x.served_notice || (x.served_status && x.served_status !== 'served')) throw new Error('tour X is not on sale: pick the fallback tour');
        used0 = Number((await R.quota(page)).rewrites_used) || 0;
        const search = page.getByRole('textbox', { name: 'Search tours by name' });
        await h.click(search);
        await search.fill(x.aa_name);
        await h.expect(card(page, x.aa_name)).toBeVisible({ timeout: 30_000 });
      }),
    step('Tour X shows its photo, its length and its price from Adventure Asia. The owner ticks it.',
      'Tour X hiện ảnh, số ngày và giá của Adventure Asia. Chủ đại lý đánh dấu chọn tour này.',
      async (page, h) => {
        const c = card(page, x.aa_name);
        await h.hover(c);
        if (!x.cover_image_url) throw new Error('tour X has no photo in the catalog');
        if (!x.from_price) throw new Error('tour X has no Booking price in the catalog (not sellable)');
        await h.expect(c.locator('img').first()).toBeVisible({ timeout: 30_000 });
        await h.expect(c).toContainText(/per person|From/i);
        const picked = await R.adopted(page);
        const have = new Set(picked.map((t) => t.published_tour_id));
        toStart = have.has(x.id) ? [] : [x];
        if (toStart.length) await h.click(tick(page, x.aa_name));
      }),
    step('Two more tours join it, so the agency starts with three. Each one will be rewritten in the agency\'s voice.',
      'Thêm hai tour nữa để đại lý bắt đầu với ba tour. Mỗi tour sẽ được viết lại theo giọng của đại lý.',
      async (page, h) => {
        const search = page.getByRole('textbox', { name: 'Search tours by name' });
        // The grid's own list read (first page, no search): the two more tours are chosen among the cards on screen.
        const listed = page.waitForResponse((r) => new URL(r.url()).pathname === `${R.T}/tours/pool`
          && !new URL(r.url()).searchParams.get('search') && r.request().method() === 'GET' && r.status() === 200, { timeout: 60_000 });
        await search.fill('');
        const pool = await (await listed).json();
        await h.expect(page.getByTestId('marketplace-grid')).toBeVisible({ timeout: 30_000 });
        const picked = await R.adopted(page);
        const have = new Set(picked.map((t) => t.published_tour_id));
        const room = Math.max(0, TARGET - have.size - toStart.length);
        const free = (pool.data || []).filter((t) => t.id !== x.id && !have.has(t.id) && !t.already_rewritten
          && !t.served_notice && (!t.served_status || t.served_status === 'served')).slice(0, room);
        for (const t of free) {
          const box = tick(page, t.aa_name);
          await h.scrollTo(box, 'center');
          await h.click(box);
          toStart.push(t);
        }
        if (have.size + toStart.length < TARGET) throw new Error(`only ${have.size + toStart.length} tours can be adopted on the first catalog page`);
        if (!toStart.length) throw new Error('the three tours are already adopted: nothing to rewrite (record the export only)');
        await h.expect(page.getByTestId('marketplace-bulk-bar')).toContainText(`${toStart.length} selected`, { timeout: 15_000 });
      }),
    step('Rewrite starts one rewrite per tour in the background. The usage meter counts each one.',
      'Bấm Viết lại để bắt đầu viết lại từng tour ở chế độ nền. Đồng hồ hạn mức tính từng lượt.',
      async (page, h) => {
        const bar = page.getByTestId('marketplace-bulk-bar');
        await h.scrollTo(bar, 'center');
        const label = toStart.length === 1 ? 'Rewrite 1 tour' : `Rewrite ${toStart.length} tours`;
        await h.click(bar.getByRole('button', { name: label }));
        await h.expect(page.getByText(/rewrites? started\. Follow (it|them) here or in My Tours\./).first()).toBeVisible({ timeout: 90_000 });
        if (counts.rewrite !== toStart.length) throw new Error(`${counts.rewrite} rewrite requests for ${toStart.length} tours`);
        await h.expect.poll(async () => Number((await R.quota(page)).rewrites_used) - used0, { timeout: 60_000, intervals: [3_000] })
          .toBe(toStart.length);
      }, { writes: true }),
    step('My Tours follows tour X while the writer works on it. A rewrite takes a few minutes.',
      'Tour của tôi theo dõi tour X trong lúc người viết làm việc. Mỗi lần viết lại mất vài phút.',
      async (page, h) => {
        await h.goto(`/portal/tours/mine?tour_id=${encodeURIComponent(x.tour_id)}`);
        await h.expect(page.locator('h1').first()).toContainText('My Tours', { timeout: 30_000 });
        const open = page.getByRole('button', { name: /^(View progress|Open) →$/ }).first();
        await h.expect(open).toBeVisible({ timeout: 60_000 });
        await h.click(open);
        const ready = page.getByTestId('tour-rewrite-ready');
        const failed = page.getByTestId('tour-rewrite-failed');
        await h.expect(ready.or(failed).or(page.getByRole('button', { name: 'Export DOCX' })).first()).toBeVisible({ timeout: 1_200_000 });
        if (await failed.isVisible().catch(() => false)) throw new Error('the rewrite of tour X did not finish (the panel offers a retry; none is made here)');
      }),
    step('Export DOCX downloads the agency\'s version as a Word file. The file says the text is AI-generated.',
      'Xuất DOCX tải phiên bản của đại lý về dạng file Word. File ghi rõ văn bản do AI tạo.',
      async (page, h) => {
        const answer = page.waitForResponse((r) => /\/export-docx$/.test(new URL(r.url()).pathname), { timeout: 60_000 });
        const download = page.waitForEvent('download', { timeout: 60_000 });
        await h.click(page.getByRole('button', { name: 'Export DOCX' }).first());
        const res = await answer;
        if (res.status() !== 200) throw new Error(`the DOCX export answered ${res.status()}`);
        if ((res.headers()['x-ai-generated'] || '').trim() !== 'true') throw new Error('the DOCX answer has no X-AI-Generated: true header');
        const d = await download;
        if (!/^[^/\\]+\.docx$/.test(d.suggestedFilename())) throw new Error(`unexpected export file name ${d.suggestedFilename()}`);
        const core = zipEntry(await downloadBytes(d), 'docProps/core.xml');
        if (!core || !AI_MARK.docxKeywords.test(core.toString('utf8'))) throw new Error('the DOCX carries no AI mark in its properties');
      }),
    step('The other two tours finish too. The agency now sells three tours in its own voice. This is the end of the scenario.',
      'Hai tour còn lại cũng xong. Giờ đại lý bán ba tour bằng giọng của mình. Kết thúc kịch bản.',
      async (page, h) => {
        await page.keyboard.press('Escape');
        await h.goto('/portal/tours/mine');
        await h.expect(page.locator('h1').first()).toContainText('My Tours', { timeout: 30_000 });
        // A failed rewrite stops the wait at once (the take keeps the evidence); none is retried here.
        for (const until = Date.now() + 1_500_000; ; await page.waitForTimeout(15_000)) {
          const tours = await R.adopted(page);
          if (tours.some((t) => t.status === 'failed')) throw new Error('a rewrite did not finish (My Tours offers a retry; none is made here)');
          if (tours.length >= TARGET && tours.every((t) => t.status !== 'writing')) break;
          if (Date.now() > until) throw new Error('the three rewrites did not finish within 25 minutes');
        }
        await h.expect.poll(() => page.locator('[data-testid="kit-datatable-row"]').count(), { timeout: 60_000 }).toBeGreaterThanOrEqual(TARGET);
      }),
  ],
});

module.exports = sc;
