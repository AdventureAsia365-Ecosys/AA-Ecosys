// Dry-run scenario CIS-01 (AA-1009, plan §4): the CIS admin shell, read only.
// Given: the Dev-only E2E CIS admin signed in outside the run (read-only session, lib/signin.cjs cis-admin).
// When:  they open the overview, look at the sidebar, then the review queue.
// Then:  each page shows its title and its data (or the empty state); no API call fails; nothing is written. $0.
// Pilot guard (AA-855): the overview's Tenants section lists the tenants near their quota by name; each of its rows
// that does not name an invented synthetic tenant is blurred before the first paint (scenario.allowRows, record.cjs).
// The selector reaches only that section (its header links to /admin/tenants), not the pipeline table or the queue.
const { HOSTS, step, ro, check, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');
const { syntheticRowPatterns } = require('../../lib/pilot-guard.cjs');

const TENANTS_SECTION = 'section:has(> div > a[href="/admin/tenants"])';

module.exports = ro({
  id: 'CIS-01',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Admin shell: overview, navigation and the review queue',
  titleVi: 'Khung trang quản trị: tổng quan, điều hướng và hàng chờ duyệt',
  baseURL: HOSTS.cisAdmin,
  allowRows: {
    rows: `${TENANTS_SECTION} [data-testid="kit-datatable-row"], ${TENANTS_SECTION} table tbody tr`,
    allow: syntheticRowPatterns(),
  },
  steps: [
    step('A staff admin opens the CIS admin. The overview shows how the business and the content pipeline are doing.',
      'Quản trị viên mở trang quản trị CIS. Trang tổng quan cho thấy tình hình kinh doanh và quy trình nội dung.',
      async (page, h) => {
        await check(page, h, '/admin/overview', { heading: 'Overview' });
        await h.expect(page.getByRole('button', { name: 'Account menu' })).toBeVisible({ timeout: 20_000 });
        await h.assertRowsFiltered();
      }),
    step('The sidebar groups every admin area: tenants, the AA catalogue, tenant content checks, AI spend and the platform.',
      'Thanh bên nhóm mọi khu vực quản trị: đại lý, danh mục AA, kiểm tra nội dung đại lý, chi phí AI và nền tảng.',
      async (page, h) => {
        await h.expect(page.getByTestId('admin-sidebar')).toBeVisible();
        // Each titled group of the kit NavGroup (_kit/core/NavGroup.tsx) has a disclosure button, test id
        // nav-group-<id>-toggle (id = navGroupId(label), e.g. nav-group-aa-catalogue-toggle). The role decides which
        // groups show, so the step asserts several, not a fixed list.
        const groups = page.getByTestId('admin-nav').locator('[data-testid^="nav-group-"][data-testid$="-toggle"]');
        await h.expect(groups.first()).toBeVisible({ timeout: 20_000 });
        await h.expect.poll(() => groups.count(), { timeout: 10_000 }).toBeGreaterThan(2);
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
