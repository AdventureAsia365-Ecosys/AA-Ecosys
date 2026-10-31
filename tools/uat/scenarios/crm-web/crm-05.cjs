// Dry-run scenario CRM-05 (AA-1009, plan §4): suppliers and bookings, read only.
// Given: the CRM owner (identity A). When: they open Suppliers, then Bookings. Then: both render with their sections;
// no BFF call fails; nothing is written. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'CRM-05',
  app: 'crm',
  identity: 'crm',
  title: 'Suppliers and bookings',
  titleVi: 'Nhà cung cấp và đặt chỗ',
  baseURL: HOSTS.partner,
  scrollBlock: 'center',
  steps: [
    step('Suppliers lists the agency\'s own suppliers next to the Adventure Asia tours it resells.',
      'Trang Nhà cung cấp liệt kê nhà cung cấp riêng của đại lý bên cạnh các tour Adventure Asia mà đại lý bán lại.',
      async (page, h) => {
        await check(page, h, '/suppliers', { heading: 'Suppliers', ready: '[data-testid="crm-suppliers"]' });
      }),
    step('Bookings totals what was sold, the margin and every booked line. This is the end of the scenario.',
      'Trang Đặt chỗ tổng hợp doanh số, lợi nhuận và từng dòng đã đặt. Kết thúc kịch bản.',
      async (page, h) => {
        await check(page, h, '/bookings', { heading: 'Bookings', ready: '[data-testid="crm-bookings"]' });
        await h.expect(page.getByTestId('bookings-totals').first()).toBeVisible({ timeout: 30_000 });
      }),
  ],
});
