// Dry-run scenario BK-06 (AA-1009, plan §4): hotels and services, read only.
// Given: the E2E Booking staff (read-only session). When: they open Hotels (photo grid, then the table view) and
// Services. Then: each view renders its items or the empty state; no API call fails; nothing is written. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'BK-06',
  app: 'booking',
  identity: 'booking',
  title: 'Hotels and services',
  titleVi: 'Khách sạn và dịch vụ',
  baseURL: HOSTS.booking,
  steps: [
    step('Hotels opens on a photo grid of the hotels the team can book.',
      'Trang Khách sạn mở ra với lưới ảnh các khách sạn đội có thể đặt.',
      async (page, h) => {
        await check(page, h, '/hotels', { heading: 'Hotels' });
        await h.expect(page.locator('[data-testid="hotel-grid"], [data-testid="kit-empty-state"]').first())
          .toBeVisible({ timeout: 30_000 });
      }),
    step('The table view lists the same hotels with their room types and rates.',
      'Chế độ bảng liệt kê cùng các khách sạn đó, kèm loại phòng và giá.',
      async (page, h) => {
        await check(page, h, '/hotels?view=table', { heading: 'Hotels', table: true });
      }),
    step('Services lists transfers, guides and activities with their net rates. This is the end of the scenario.',
      'Trang Dịch vụ liệt kê đưa đón, hướng dẫn viên và hoạt động kèm giá net. Kết thúc kịch bản.',
      async (page, h) => {
        await check(page, h, '/services', { heading: 'Services', table: true });
      }),
  ],
});
