// Dry-run scenario TP-02 (AA-1009, plan §4): a destination page, public.
// Given: a visitor with no account. When: they open Destinations, pick the first country, look at its tours and the
// places they visit. Then: titles, tour links and the "plan" link render. The plan link is only checked, never
// followed: the map planner and the AI paths (search, narration) are outside the dry run (paid model calls, and
// Vercel BotID refuses headless Chromium there). $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'TP-02',
  app: 'tripplanner',
  title: 'A destination page: its tours and the places they visit',
  titleVi: 'Trang điểm đến: các tour và những nơi tour đi qua',
  baseURL: HOSTS.tripplanner,
  steps: [
    step('A traveller opens the list of destinations. Each country shows how many tours it has.',
      'Khách du lịch mở danh sách điểm đến. Mỗi quốc gia cho biết có bao nhiêu tour.',
      async (page, h) => {
        await check(page, h, '/destinations', { heading: 'Destinations', signedIn: false });
        await h.expect(page.locator('main a[href^="/destinations/"]').first()).toBeVisible({ timeout: 30_000 });
      }),
    step('They pick a country and land on its destination page.',
      'Khách chọn một quốc gia và mở trang điểm đến của quốc gia đó.',
      async (page, h) => {
        await h.click(page.locator('main a[href^="/destinations/"]').first());
        await page.waitForURL((u) => /^\/destinations\/[^/]+$/.test(u.pathname), { timeout: 30_000 });
        await h.expect(page.locator('h1').first()).toBeVisible({ timeout: 30_000 });
      }),
    step('The page lists the tours of that country and offers to plan a trip there.',
      'Trang liệt kê các tour của quốc gia đó và mời khách lập kế hoạch chuyến đi.',
      async (page, h) => {
        const tour = page.locator('main a[href^="/tours/"]').first();
        await h.scrollTo(tour);
        await h.expect(tour).toBeVisible({ timeout: 30_000 });
        await h.expect(page.locator('main a[href^="/plan"]').first()).toBeAttached();
      }),
    step('Further down are the places those tours visit. This is the end of the scenario.',
      'Phía dưới là những địa điểm các tour đó đi qua. Kết thúc kịch bản.',
      async (page, h) => {
        const places = page.getByRole('heading', { name: /Places our tours visit/i });
        await h.scrollTo(places);
        await h.expect(places).toBeVisible();
      }),
  ],
});
