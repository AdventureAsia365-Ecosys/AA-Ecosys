// Dry-run scenario BK-05 (AA-1009, plan §4): suppliers and their contracts, read only.
// Given: the E2E Booking staff (read-only session). When: they open Suppliers, then the first supplier and its
// Contracts tab. Then: the list, the detail heading and the contracts (or the empty state) render; nothing is written.
// No supplier on Dev: the scenario checks the empty state and stops there (still a PASS). $0.
const { HOSTS, step, ro, check, openTab, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');

let hasRows = false;

module.exports = ro({
  id: 'BK-05',
  app: 'booking',
  identity: 'booking',
  title: 'Suppliers and contracts',
  titleVi: 'Nhà cung cấp và hợp đồng',
  baseURL: HOSTS.booking,
  steps: [
    step('Suppliers lists the hotels, guides and transport companies the team books with.',
      'Trang Nhà cung cấp liệt kê khách sạn, hướng dẫn viên và nhà xe mà đội đặt dịch vụ.',
      async (page, h) => {
        await check(page, h, '/suppliers', { heading: 'Suppliers', table: true });
        hasRows = (await page.getByTestId('kit-datatable-row').count()) > 0;
      }),
    step('The staff member opens one supplier to see its profile.',
      'Nhân viên mở một nhà cung cấp để xem hồ sơ.',
      async (page, h) => {
        if (!hasRows) return h.expect(page.getByTestId('kit-empty-state').first()).toBeVisible();
        await h.click(page.getByTestId('kit-datatable-row').first());
        await page.waitForURL((u) => /^\/suppliers\/[^/]+$/.test(u.pathname), { timeout: 30_000 });
        await h.expect(page.locator('h1').first()).toBeVisible({ timeout: 30_000 });
      }),
    step('The contracts tab lists the supplier\'s contracts and their validity. This is the end of the scenario.',
      'Thẻ hợp đồng liệt kê các hợp đồng của nhà cung cấp và thời hạn hiệu lực. Kết thúc kịch bản.',
      async (page, h) => {
        if (!hasRows) return;
        await openTab(page, h, /^Contracts/);
        await rowsOrEmpty(page, h);
      }),
  ],
});
