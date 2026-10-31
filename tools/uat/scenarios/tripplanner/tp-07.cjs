// Dry-run scenario TP-07 (AA-1009, plan §4): browse on a phone (390 x 844), public. The planning half of TP-07 (the
// map) stays out of the dry run like every AI / map path. Given: a visitor on a phone. When: they open the home page,
// then a tour. Then: the titles render and no page scrolls sideways. $0.
const { HOSTS, PHONE, step, ro, check, assertNoSideScroll } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'TP-07',
  app: 'tripplanner',
  title: 'Browse on a phone',
  titleVi: 'Xem tour trên điện thoại',
  baseURL: HOSTS.tripplanner,
  viewport: PHONE,
  steps: [
    step('On a phone, the trip planner opens on the same home page, sized for the screen.',
      'Trên điện thoại, trang lập kế hoạch mở cùng trang chủ, vừa với màn hình.',
      async (page, h) => {
        await check(page, h, '/', { heading: 'Plan your Asia adventure', signedIn: false });
        await assertNoSideScroll(page);
      }),
    step('The traveller scrolls to the suggested trips and opens one.',
      'Khách cuộn tới các chuyến gợi ý và mở một chuyến.',
      async (page, h) => {
        const tour = page.locator('a[href^="/tours/"]').first();
        await h.scrollTo(tour);
        await h.click(tour);
        await page.waitForURL('**/tours/**', { timeout: 30_000 });
      }),
    step('The tour page fits the phone: title, length and the day-by-day plan. This is the end of the scenario.',
      'Trang tour vừa màn hình điện thoại: tên tour, số ngày và lịch trình từng ngày. Kết thúc kịch bản.',
      async (page, h) => {
        await h.expect(page.locator('h1').first()).toContainText(/\d+\s*Days?/i, { timeout: 30_000 });
        await assertNoSideScroll(page);
      }),
  ],
});
