// Dry-run scenario CIS-06 (AA-1009, plan §4): Tenants and the apps of the platform, read only (no limit change).
// Given: the E2E CIS admin (read-only session). When: they open Tenants, then Platform > Apps.
// Then: each page shows its title and its rows (or the ready marker); no API call fails; nothing is written. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'CIS-06',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Tenants and the apps of the platform',
  titleVi: 'Danh sách đại lý và các ứng dụng của nền tảng',
  baseURL: HOSTS.cisAdmin,
  steps: [
    step('Tenants lists every agency that uses the content platform, with its plan and its activity.',
      'Trang Tenants liệt kê mọi đại lý dùng nền tảng nội dung, kèm gói dịch vụ và hoạt động.',
      async (page, h) => {
        await check(page, h, '/admin/tenants', { heading: 'Tenants', table: true });
      }),
    step('Platform, Apps shows each app of the ecosystem and the version it runs.',
      'Mục Nền tảng, Ứng dụng hiển thị từng ứng dụng của hệ sinh thái và phiên bản đang chạy.',
      async (page, h) => {
        await check(page, h, '/admin/platform/apps', { heading: 'Apps', ready: '[data-testid="platform-apps-ready"]' });
      }),
  ],
});
