// Dry-run scenario BK-07 (AA-1009, plan §4): sellable trip plans and the pricing rules, read only (no "Use for trip
// case", no rule change). Given: the E2E Booking staff (read-only session). When: they open Trip plans, then Pricing
// rules and its FX tab. Then: each list renders its rows or the empty state; nothing is written. $0.
const { HOSTS, step, ro, check, openTab, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'BK-07',
  app: 'booking',
  identity: 'booking',
  title: 'Trip plans and pricing rules',
  titleVi: 'Kế hoạch chuyến đi và quy tắc giá',
  baseURL: HOSTS.booking,
  steps: [
    step('Trip plans are the catalog tours the team can sell, read from the content platform.',
      'Kế hoạch chuyến đi là các tour trong danh mục mà đội có thể bán, đọc từ nền tảng nội dung.',
      async (page, h) => {
        await check(page, h, '/catalog/trip-plans', { heading: 'Trip plans', table: true });
      }),
    step('Pricing rules set the margins applied to every proposal.',
      'Quy tắc giá đặt mức lợi nhuận áp dụng cho mọi đề xuất.',
      async (page, h) => {
        await check(page, h, '/pricing/rules', { heading: 'Pricing rules', table: true });
      }),
    step('The FX tab shows the exchange rates and their buffer. This is the end of the scenario.',
      'Thẻ tỷ giá hiển thị tỷ giá hối đoái và biên an toàn. Kết thúc kịch bản.',
      async (page, h) => {
        await openTab(page, h, /^FX rates/);
        await rowsOrEmpty(page, h);
      }),
  ],
});
