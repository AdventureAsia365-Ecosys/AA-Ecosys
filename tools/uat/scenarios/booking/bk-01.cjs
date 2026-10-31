// Dry-run scenario BK-01 (AA-1009, plan §4): the Booking dashboard and notifications, read only.
// Given: the WORKFORCE E2E Booking staff signed in outside the run (read-only session, lib/signin.cjs booking).
// When:  they open the dashboard, then the notifications. Then: titles, KPI sections and the feed (or its empty state)
// render; no API call fails; nothing is written. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'BK-01',
  app: 'booking',
  identity: 'booking',
  title: 'Booking dashboard and notifications',
  titleVi: 'Bảng điều khiển Booking và thông báo',
  baseURL: HOSTS.booking,
  steps: [
    step('A Booking staff member opens the staff admin. The dashboard shows what needs attention today.',
      'Nhân viên Booking mở trang quản trị. Bảng điều khiển cho biết việc cần chú ý hôm nay.',
      async (page, h) => {
        await check(page, h, '/', { heading: 'Dashboard' });
        await h.expect(page.getByText('Recent trip cases').first()).toBeVisible({ timeout: 30_000 });
      }),
    step('The pipeline by phase counts the open trip cases at each step.',
      'Mục quy trình theo giai đoạn đếm các hồ sơ chuyến đi đang mở ở từng bước.',
      async (page, h) => {
        const pipe = page.getByText('Pipeline by phase').first();
        await h.scrollTo(pipe);
        await h.expect(pipe).toBeVisible();
      }),
    step('Notifications collect invoices, payments and trip checks in one feed. This is the end of the scenario.',
      'Thông báo gom hoá đơn, thanh toán và kiểm tra chuyến đi vào một luồng. Kết thúc kịch bản.',
      async (page, h) => {
        await check(page, h, '/notifications', { heading: 'Notifications' });
      }),
  ],
});
