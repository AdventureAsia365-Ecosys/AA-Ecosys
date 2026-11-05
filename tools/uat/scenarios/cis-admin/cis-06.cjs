// Dry-run scenario CIS-06 (AA-1009, plan §4): Tenants and the apps of the platform, read only (no limit change).
// Given: the E2E CIS admin (read-only session). When: they open Tenants, then Platform > Apps.
// Then: each page shows its title and its rows (or the ready marker); no API call fails; nothing is written. $0.
// Pilot guard (AA-855): every tenant row that is not one of the invented synthetic tenants is blurred before the first
// paint (scenario.allowRows, record.cjs), and the step fails if such a row shows unblurred. A real pilot tenant on
// Dev never appears readable in a take.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');
const { syntheticRowPatterns } = require('../../lib/pilot-guard.cjs');

module.exports = ro({
  id: 'CIS-06',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Tenants and the apps of the platform',
  titleVi: 'Danh sách đại lý và các ứng dụng của nền tảng',
  baseURL: HOSTS.cisAdmin,
  allowRows: { rows: '[data-testid="kit-datatable-row"], table tbody tr', allow: syntheticRowPatterns() },
  steps: [
    step('Tenants lists every agency that uses the content platform, with its plan and its activity.',
      'Trang Tenants liệt kê mọi đại lý dùng nền tảng nội dung, kèm gói dịch vụ và hoạt động.',
      async (page, h) => {
        await check(page, h, '/admin/tenants', { heading: 'Tenants', table: true });
        await h.assertRowsFiltered();
      }),
    step('Platform, Apps shows each app of the ecosystem and the version it runs.',
      'Mục Nền tảng, Ứng dụng hiển thị từng ứng dụng của hệ sinh thái và phiên bản đang chạy.',
      async (page, h) => {
        await check(page, h, '/admin/platform/apps', { heading: 'Apps', ready: '[data-testid="platform-apps-ready"]' });
      }),
  ],
});
