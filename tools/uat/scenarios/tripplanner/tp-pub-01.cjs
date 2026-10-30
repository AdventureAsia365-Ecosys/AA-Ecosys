// UAT scenario TP-PUB-01 (skill aa-uat-video): a traveller browses the public TripPlanner site.
// Given: a visitor with no account on the production host.
// When:  they open the home page, look at the destinations, open Bhutan and then one Bhutan tour.
// Then:  every page shows its main heading and real catalog data (tour cards, tour counts, a tour title).
// Each step: caption (en/vi) is the subtitle and the narration text; run() does the action AND the assertion.
// Public pages only: no sign-in, no form submit, no LLM call. Cost $0.
module.exports = {
  id: 'TP-PUB-01',
  app: 'tripplanner',
  title: 'Browse destinations and open a tour',
  baseURL: process.env.UAT_BASE_URL || 'https://aa-tripplanner.vercel.app',
  viewport: { width: 1440, height: 900 },
  steps: [
    {
      caption: {
        en: 'A traveller opens the Adventure Asia trip planner. No account is needed to browse.',
        vi: 'Khách du lịch mở trang lập kế hoạch chuyến đi của Adventure Asia. Không cần tài khoản để xem.',
      },
      run: async (page, h) => {
        await h.goto('/');
        await h.expect(page.locator('h1')).toContainText('Plan your Asia adventure');
      },
    },
    {
      caption: {
        en: 'The home page starts with real tours from the catalog, each with its country and length.',
        vi: 'Trang chủ hiển thị các tour thật từ danh mục, mỗi tour có quốc gia và số ngày.',
      },
      run: async (page, h) => {
        const section = page.getByRole('heading', { name: 'Trips to start from' });
        await h.scrollTo(section);
        await h.expect(page.locator('a[href^="/tours/"]').first()).toBeVisible();
        await h.hover(page.locator('a[href^="/tours/"] h3').first());
      },
    },
    {
      caption: {
        en: 'Further down, every destination shows how many tours it has and how long they run.',
        vi: 'Phía dưới, mỗi điểm đến cho biết có bao nhiêu tour và độ dài các tour.',
      },
      run: async (page, h) => {
        await h.scrollTo(page.getByRole('heading', { name: 'Where to go' }));
        await h.expect(page.locator('a[href="/destinations/bhutan"]').first()).toContainText('tours');
      },
    },
    {
      caption: {
        en: 'The traveller picks Bhutan and lands on its destination page.',
        vi: 'Khách chọn Bhutan và mở trang điểm đến của Bhutan.',
      },
      run: async (page, h) => {
        await h.click(page.locator('a[href="/destinations/bhutan"]').first());
        await page.waitForURL('**/destinations/bhutan');
        await h.expect(page.locator('h1')).toContainText(/bhutan/i);
      },
    },
    {
      caption: {
        en: 'The page lists the Bhutan tours and the places those tours visit.',
        vi: 'Trang liệt kê các tour ở Bhutan và những địa điểm mà các tour đó đi qua.',
      },
      run: async (page, h) => {
        await h.scrollTo(page.getByRole('heading', { name: /Tours in Bhutan/i }));
        await h.expect(page.locator('main a[href^="/tours/"]').first()).toBeVisible();
        await h.pause(1200);
        await h.scrollTo(page.getByRole('heading', { name: /Places our tours visit/i }));
      },
    },
    {
      caption: {
        en: 'They open one tour to read the day-by-day plan.',
        vi: 'Khách mở một tour để đọc lịch trình từng ngày.',
      },
      run: async (page, h) => {
        await h.scrollTo(page.getByRole('heading', { name: /Tours in Bhutan/i }));
        await h.click(page.locator('main a[href^="/tours/"]').first());
        await page.waitForURL('**/tours/**');
        await h.expect(page.locator('h1')).toBeVisible();
      },
    },
    {
      caption: {
        en: 'The tour page shows the title, the length and the itinerary. This is the end of the browse flow.',
        vi: 'Trang tour hiển thị tên tour, số ngày và lịch trình. Kết thúc luồng xem tour.',
      },
      run: async (page, h) => {
        await h.expect(page.locator('h1')).toContainText(/\d+\s*Days?/i);
        await h.smoothScrollBy(700);
      },
    },
  ],
};
