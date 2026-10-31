// Dry-run scenario TP-PUB-02 (AA-1009): the trip planner's privacy notice and terms of use, public.
// Given: a visitor with no account. When: they open the privacy notice, then follow its link to the terms.
// Then: each page shows its title and its first numbered section. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'TP-PUB-02',
  app: 'tripplanner',
  title: 'Read the privacy notice and the terms of use',
  titleVi: 'Đọc thông báo quyền riêng tư và điều khoản sử dụng',
  baseURL: HOSTS.tripplanner,
  steps: [
    step('A traveller opens the privacy notice of the trip planner.',
      'Khách du lịch mở thông báo quyền riêng tư của trang lập kế hoạch chuyến đi.',
      async (page, h) => {
        await check(page, h, '/privacy', { heading: 'Privacy notice', signedIn: false });
        await h.expect(page.getByRole('heading', { name: /1\. Who we are/ })).toBeVisible();
      }),
    step('They follow the link to the terms of use. This is the end of the scenario.',
      'Khách bấm liên kết sang điều khoản sử dụng. Kết thúc kịch bản.',
      async (page, h) => {
        await h.click(page.locator('main a[href="/terms"], a[href="/terms"]').first());
        await page.waitForURL('**/terms', { timeout: 30_000 });
        await h.expect(page.locator('h1').first()).toContainText('Terms of use');
        await h.expect(page.getByRole('heading', { name: /1\. What the Trip Planner is/ })).toBeVisible();
      }),
  ],
});
