// Pilot rehearsal step 1, the CRM side (root docs/ops/runbooks/pilot-rehearsal.md, step 1 "CRM agency projected"),
// read only. Given: the E2E CIS admin (read-only session; the CRM console reads need tenant.read only). When: they open
// Platform > Tenants > Agencies (CRM), filter on the rehearsal agency and open its drawer. Then: the CRM holds the
// agency, marked synthetic, and its drawer shows its usage and its first owner. Nothing is written (the console's
// actions need crm-platform-admin and stay hidden). $0.
// Pilot guard (AA-855): the agency list names every CRM agency; each row that is not one of the invented synthetic
// agencies is blurred before the first paint, and the steps fail if one shows unblurred.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');
const { syntheticRowPatterns } = require('../../lib/pilot-guard.cjs');
const { REHEARSAL } = require('../../lib/rehearsal-admin.cjs');

module.exports = ro({
  id: 'REH-01-crm-agency',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Pilot rehearsal, step 1: the CRM holds the rehearsal agency',
  titleVi: 'Diễn tập pilot, bước 1: CRM đã có đại lý diễn tập',
  baseURL: HOSTS.cisAdmin,
  allowRows: { rows: '[data-testid="kit-datatable-row"], table tbody tr', allow: syntheticRowPatterns() },
  steps: [
    step('CRM agencies lists the agencies of the partner CRM, as AA support sees them.',
      'Trang Đại lý CRM liệt kê các đại lý của CRM đối tác, theo góc nhìn của bộ phận hỗ trợ AA.',
      async (page, h) => {
        await check(page, h, '/admin/tenants/agencies', { heading: 'CRM agencies', table: true });
        await h.assertRowsFiltered();
      }),
    step('We filter on the rehearsal agency. The CRM received it from the content platform, marked synthetic.',
      'Ta lọc theo đại lý diễn tập. CRM đã nhận đại lý này từ nền tảng nội dung, được đánh dấu là giả lập.',
      async (page, h) => {
        const filter = page.getByPlaceholder('Filter the loaded agencies');
        await h.click(filter);
        await filter.fill(REHEARSAL.name);
        const row = page.locator('[data-testid="kit-datatable-row"], table tbody tr').filter({ hasText: REHEARSAL.name }).first();
        await h.expect(row).toBeVisible({ timeout: 30_000 });
        await h.expect(row).toContainText('Synthetic');
        await h.assertRowsFiltered();
      }),
    step('Its drawer shows the usage meters and the first owner of the agency. This is the end of the scenario.',
      'Ngăn chi tiết cho biết mức sử dụng và chủ sở hữu đầu tiên của đại lý. Kết thúc kịch bản.',
      async (page, h) => {
        await h.click(page.locator('[data-testid="kit-datatable-row"], table tbody tr').filter({ hasText: REHEARSAL.name }).first());
        const drawer = page.getByTestId('crm-agency-drawer');
        await h.expect(drawer).toBeVisible({ timeout: 30_000 });
        await h.expect(drawer.getByTestId('crm-usage')).toBeVisible({ timeout: 30_000 });
        await h.expect(drawer.getByTestId('crm-first-owner')).toBeVisible({ timeout: 30_000 });
      }),
  ],
});
