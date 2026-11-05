// Dry-run scenario CIS-04 (AA-1009, plan §4): Content quality, the read part (no Cut / Edit: the dry run never writes).
// Given: the E2E CIS admin (read-only session). When: they open Tenant content QA › Content quality
// (/admin/tenant-qa/quality since the R6 admin IA; the old /admin/content-quality answers 307 there).
// Then: the quality signals render (ready marker, rows or the empty state); no API call fails; nothing is written. $0.
// Pilot guard (AA-855): the pieces table has a tenant column and lists every tenant's pieces; each row that does not
// name one of the invented synthetic tenants is blurred before the first paint (scenario.allowRows, record.cjs), and
// the step fails if such a row shows unblurred.
const { HOSTS, step, ro, check, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');
const { syntheticRowPatterns } = require('../../lib/pilot-guard.cjs');

module.exports = ro({
  id: 'CIS-04',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Content quality: the quality signals of tenant content',
  titleVi: 'Chất lượng nội dung: các tín hiệu chất lượng của nội dung đại lý',
  baseURL: HOSTS.cisAdmin,
  allowRows: { rows: '[data-testid="kit-datatable-row"], table tbody tr', allow: syntheticRowPatterns() },
  steps: [
    step('Content quality collects the quality signals of every tenant\'s content. Tenants never see them.',
      'Trang Chất lượng nội dung gom các tín hiệu chất lượng của nội dung mọi đại lý. Đại lý không bao giờ thấy trang này.',
      async (page, h) => {
        await check(page, h, '/admin/tenant-qa/quality', { heading: 'Content quality', ready: '[data-testid="content-quality-ready"]' });
      }),
    step('The list of pieces loaded. The admin only reads here. This is the end of the scenario.',
      'Danh sách nội dung đã tải. Ở đây quản trị viên chỉ đọc. Kết thúc kịch bản.',
      async (page, h) => {
        await rowsOrEmpty(page, h);
        await h.assertRowsFiltered();
      }),
  ],
});
