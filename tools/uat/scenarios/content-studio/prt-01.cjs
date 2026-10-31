// Dry-run scenario PRT-01 (AA-1009, plan §4): the Content studio after sign-in, read only.
// Given: the Content studio VIEWER of the E2E tenant signed in outside the run (lib/signin.cjs studio).
// When:  they open the dashboard, then My Content. Then: the sidebar, the dashboard title and the content list (or its
// empty state) render, in English; no API call fails; nothing is written. $0.
const { HOSTS, step, ro, check, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'PRT-01',
  app: 'content-studio',
  identity: 'studio',
  title: 'Content studio: dashboard and my content',
  titleVi: 'Content studio: bảng điều khiển và nội dung của tôi',
  baseURL: HOSTS.partner,
  steps: [
    step('An agency member opens the Content studio. The dashboard shows the membership, the quota and recent activity.',
      'Thành viên đại lý mở Content studio. Bảng điều khiển hiển thị gói thành viên, hạn mức và hoạt động gần đây.',
      async (page, h) => {
        await check(page, h, '/portal/dashboard', { heading: /Welcome back|Dashboard/ });
        await h.expect(page.getByTestId('portal-sidebar')).toBeVisible();
        await h.expect(page.getByText('Quota Usage').first()).toBeVisible({ timeout: 30_000 });
      }),
    step('My Content lists the pieces the agency wrote from its tours. This is the end of the scenario.',
      'Mục Nội dung của tôi liệt kê các bài đại lý đã viết từ tour của mình. Kết thúc kịch bản.',
      async (page, h) => {
        await check(page, h, '/portal/content', { heading: 'My Content' });
        await rowsOrEmpty(page, h);
      }),
  ],
});
