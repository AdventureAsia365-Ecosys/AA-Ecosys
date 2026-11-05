// UAT scenario X-04 (AA-855 round 1, catalogue.json): the AI notice and the "AI-assisted" mark on generated content.
// Given: the Content studio VIEWER of the E2E tenant (lib/signin.cjs studio) and at least one written piece on it.
// When:  they open My Content and then one piece.
// Then:  the page carries the AI notice line, every listed piece shows the "AI-assisted" badge, and the opened piece
//        shows the badge in its title and the notice beside its export. Read only, no model call. $0. 1440 x 900.
const { HOSTS, step, ro, check, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');

const ROW = '[data-testid="kit-datatable-row"]';

module.exports = ro({
  id: 'X-04',
  app: 'cross-app',
  identity: 'studio',
  title: 'AI notice and the AI-assisted mark on generated content',
  titleVi: 'Thông báo AI và nhãn "Có AI hỗ trợ" trên nội dung được tạo',
  baseURL: HOSTS.partner,
  steps: [
    step('Content written with AI says so. My Content shows the notice under its title.',
      'Nội dung viết bằng AI luôn ghi rõ điều đó. Mục Nội dung của tôi hiện thông báo ngay dưới tiêu đề.',
      async (page, h) => {
        await check(page, h, '/portal/content', { heading: 'My Content' });
        await h.expect(page.getByTestId('ai-notice').first()).toBeVisible({ timeout: 30_000 });
        await rowsOrEmpty(page, h);
        if (!(await page.locator(ROW).count())) throw new Error('no piece on this tenant (precondition: one written piece)');
      }),
    step('Every piece in the list carries the AI-assisted mark.',
      'Mỗi bài trong danh sách đều mang nhãn có AI hỗ trợ.',
      async (page, h) => {
        const rows = await page.locator(ROW).count();
        const badges = await page.locator(`${ROW} [data-testid="my-content-ai-badge"]`).count();
        if (badges < rows) throw new Error(`${rows - badges} of ${rows} listed piece(s) have no AI-assisted mark`);
        await h.hover(page.getByTestId('my-content-ai-badge').first());
      }),
    step('An opened piece shows the mark in its title and the notice beside its export. This is the end of the scenario.',
      'Khi mở một bài, nhãn nằm ở tiêu đề và thông báo nằm cạnh nút xuất file. Kết thúc kịch bản.',
      async (page, h) => {
        await h.click(page.locator(ROW).first());
        const panel = page.getByRole('dialog').first();
        await h.expect(panel).toBeVisible({ timeout: 30_000 });
        await h.expect(page.getByTestId('review-drawer-ai-badge').first()).toBeVisible({ timeout: 30_000 });
        await h.expect(panel.getByTestId('ai-notice').first()).toBeVisible({ timeout: 30_000 });
      }),
  ],
});
