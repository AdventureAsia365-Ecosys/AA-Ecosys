// Dry-run scenario CRM-02 (AA-1009, plan §4): clients, read only (the list; client 360 is in the review videos).
// Given: the CRM owner (identity A). When: they open Clients. Then: the list or its empty state renders; nothing is
// written. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'CRM-02',
  app: 'crm',
  identity: 'crm',
  title: 'Clients',
  titleVi: 'Khách hàng',
  baseURL: HOSTS.partner,
  scrollBlock: 'center',
  steps: [
    step('Clients lists every traveller the agency works with, with their trips and their consent.',
      'Trang Khách hàng liệt kê mọi khách du lịch đại lý làm việc cùng, kèm chuyến đi và sự đồng ý của họ.',
      async (page, h) => {
        await check(page, h, '/clients', { heading: 'Clients', ready: '[data-testid="crm-clients"]' });
      }),
    step('The list loaded. This is the end of the scenario.',
      'Danh sách đã tải. Kết thúc kịch bản.',
      async (page, h) => {
        await h.expect(page.locator('[data-testid="client-list"], [data-testid="kit-empty-state"]').first())
          .toBeVisible({ timeout: 30_000 });
      }),
  ],
});
