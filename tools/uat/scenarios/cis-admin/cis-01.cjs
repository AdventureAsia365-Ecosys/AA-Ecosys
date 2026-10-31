// Dry-run scenario CIS-01 (AA-1009, plan §4): the CIS admin shell, read only.
// Given: the Dev-only E2E CIS admin signed in outside the run (read-only session, lib/signin.cjs cis-admin).
// When:  they open the overview, look at the sidebar, then the review queue.
// Then:  each page shows its title and its data (or the empty state); no API call fails; nothing is written. $0.
const { HOSTS, step, ro, check, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'CIS-01',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Admin shell: overview, navigation and the review queue',
  titleVi: 'Khung trang quản trị: tổng quan, điều hướng và hàng chờ duyệt',
  baseURL: HOSTS.cisAdmin,
  steps: [
    step('A staff admin opens the CIS admin. The overview shows how the business and the content pipeline are doing.',
      'Quản trị viên mở trang quản trị CIS. Trang tổng quan cho thấy tình hình kinh doanh và quy trình nội dung.',
      async (page, h) => {
        await check(page, h, '/admin/overview', { heading: 'Overview' });
        await h.expect(page.getByRole('button', { name: 'Account menu' })).toBeVisible({ timeout: 20_000 });
      }),
    step('The sidebar groups every admin area: content, operations and the platform.',
      'Thanh bên nhóm mọi khu vực quản trị: nội dung, vận hành và nền tảng.',
      async (page, h) => {
        await h.expect(page.getByTestId('admin-sidebar')).toBeVisible();
        await h.expect(page.locator('[data-testid^="nav-section-"]').first()).toBeVisible();
        await h.hover(page.getByTestId('sidebar-logo'));
      }),
    step('The review queue lists the tours waiting for a human check.',
      'Hàng chờ duyệt liệt kê các tour đang chờ người kiểm tra.',
      async (page, h) => {
        await check(page, h, '/admin/review', { heading: 'Review Queue', table: true });
      }),
    step('The queue loaded with its rows. Nothing was changed. This is the end of the scenario.',
      'Hàng chờ đã tải xong. Không có gì bị thay đổi. Kết thúc kịch bản.',
      async (page, h) => {
        await rowsOrEmpty(page, h);
      }),
  ],
});
