// UAT scenario PRT-04 (AA-855 round 1, catalogue.json): My Tours, a tour the agency already rewrote, read only.
// Given: the Content studio VIEWER of the E2E tenant (lib/signin.cjs studio) and at least one rewritten tour on that
//        tenant (the controlled tenants already hold rewrites from the writer trials; no new rewrite is started).
// When:  they open My Tours, then the first tour.
// Then:  the list shows the rewritten tours; the tour opens in its panel with the agency's own text and the AI notice
//        beside the export; nothing is written, no model is called. $0. Desktop 1440 x 900.
const { HOSTS, step, ro, check, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');

const ROW = '[data-testid="kit-datatable-row"]';

module.exports = ro({
  id: 'PRT-04',
  app: 'content-studio',
  identity: 'studio',
  title: 'My Tours: a tour rewritten in the agency\'s voice',
  titleVi: 'Tour của tôi: một tour đã viết lại theo giọng của đại lý',
  baseURL: HOSTS.partner,
  steps: [
    step('My Tours lists the tours the agency picked and rewrote in its own voice.',
      'Mục Tour của tôi liệt kê các tour đại lý đã chọn và viết lại theo giọng của mình.',
      async (page, h) => {
        await check(page, h, '/portal/tours/mine', { heading: 'My Tours' });
        await rowsOrEmpty(page, h);
        if (!(await page.locator(ROW).count())) throw new Error('no rewritten tour on this tenant (precondition: one rewrite)');
      }),
    step('A tour opens in its panel: the agency\'s rewritten text, ready to review and export.',
      'Một tour mở trong ngăn bên: bản viết lại của đại lý, sẵn sàng để duyệt và xuất file.',
      async (page, h) => {
        await h.click(page.locator(ROW).first());
        const panel = page.getByRole('dialog').first();
        await h.expect(panel).toBeVisible({ timeout: 30_000 });
        await h.expect(panel.getByTestId('ai-notice').first()).toBeVisible({ timeout: 30_000 });
      }),
    step('Every rewritten text carries the AI notice. This is the end of the scenario.',
      'Mọi bản viết lại đều kèm thông báo về AI. Kết thúc kịch bản.',
      async (page, h) => {
        await h.hover(page.getByRole('dialog').first().getByTestId('ai-notice').first());
        await page.keyboard.press('Escape');
        await h.expect(page.getByRole('dialog')).toHaveCount(0, { timeout: 15_000 });
      }),
  ],
});
