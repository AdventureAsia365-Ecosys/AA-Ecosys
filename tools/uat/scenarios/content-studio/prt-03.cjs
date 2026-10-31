// Dry-run scenario PRT-03 (AA-1009, plan §4): the Marketplace, read only (no pick, no rewrite).
// Given: the studio viewer (lib/signin.cjs studio). When: they open the Marketplace, open one tour's drawer, close it,
// then the "in my catalog" view. Then: the grid, the drawer and the second view render; nothing is written. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

const CARD = '[data-testid="marketplace-grid"] [role="button"][aria-label^="Open "]';
let cards = 0;

module.exports = ro({
  id: 'PRT-03',
  app: 'content-studio',
  identity: 'studio',
  title: 'Marketplace: browse the catalog and open a tour',
  titleVi: 'Marketplace: xem danh mục và mở một tour',
  baseURL: HOSTS.partner,
  steps: [
    step('The Marketplace shows the published Adventure Asia tours the agency can pick and rewrite in its own voice.',
      'Marketplace hiển thị các tour đã xuất bản của Adventure Asia mà đại lý có thể chọn và viết lại theo giọng của mình.',
      async (page, h) => {
        await check(page, h, '/portal/tours', { heading: 'Marketplace', ready: '[data-testid="marketplace-views"]' });
        // The loading skeleton is a separate aria-busy grid: wait for real cards or the empty state.
        const card = page.locator(CARD);
        await h.expect.poll(async () => ((await card.count()) > 0 || (await page.getByTestId('kit-empty-state').count()) > 0 ? 'ready' : 'waiting'),
          { timeout: 30_000, intervals: [500, 1000, 2000] }).toBe('ready');
        cards = await card.count();
      }),
    step('A tour opens in a drawer with its route, its activities and its price.',
      'Một tour mở trong ngăn bên, kèm lộ trình, hoạt động và giá.',
      async (page, h) => {
        if (!cards) return h.expect(page.getByTestId('kit-empty-state').first()).toBeVisible();
        await h.click(page.locator(CARD).first());
        await h.expect(page.getByTestId('marketplace-drawer')).toBeVisible({ timeout: 30_000 });
        await page.keyboard.press('Escape');
        await h.expect(page.getByTestId('marketplace-drawer')).toHaveCount(0, { timeout: 15_000 });
      }),
    step('The second view lists the tours already in the agency\'s catalog. This is the end of the scenario.',
      'Chế độ thứ hai liệt kê các tour đã có trong danh mục của đại lý. Kết thúc kịch bản.',
      async (page, h) => {
        await check(page, h, '/portal/tours?view=mine', { heading: 'Marketplace' });
        await h.expect(page.locator('[data-testid="marketplace-mine-grid"], [data-testid="marketplace-mine-stats"], [data-testid="kit-empty-state"], [data-testid="empty-state-cta"]').first())
          .toBeVisible({ timeout: 30_000 });
      }),
  ],
});
