// Dry-run scenario CIS-03 (AA-1009, plan §4): Master content and the S1 rewrite results, read only.
// Given: the E2E CIS admin (read-only session). When: they open Master Content.
// Then: the title and the list of master tours (or the empty state) render; no API call fails; nothing is written. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'CIS-03',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Master content: the rewritten tours',
  titleVi: 'Master content: các tour đã viết lại',
  baseURL: HOSTS.cisAdmin,
  steps: [
    step('Master Content lists every tour after the rewrite, with its review and audit state.',
      'Master Content liệt kê mọi tour sau khi viết lại, kèm trạng thái duyệt và kiểm tra.',
      async (page, h) => {
        await check(page, h, '/admin/master-content', { heading: 'Master Content', table: true });
      }),
    step('The admin scrolls the list. Nothing is changed. This is the end of the scenario.',
      'Quản trị viên cuộn danh sách. Không thay đổi gì. Kết thúc kịch bản.',
      async (page, h) => {
        await h.smoothScrollBy(500);
        await h.expect(page.locator('h1').first()).toContainText('Master Content');
      }),
  ],
});
