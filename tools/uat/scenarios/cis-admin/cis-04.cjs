// Dry-run scenario CIS-04 (AA-1009, plan §4): Content Quality, the read part (no Cut / Edit: the dry run never writes).
// Given: the E2E CIS admin (read-only session). When: they open Content Quality.
// Then: the quality signals render (ready marker, rows or the empty state); no API call fails; nothing is written. $0.
const { HOSTS, step, ro, check, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'CIS-04',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Content Quality: the quality signals of tenant content',
  titleVi: 'Chất lượng nội dung: các tín hiệu chất lượng của nội dung đại lý',
  baseURL: HOSTS.cisAdmin,
  steps: [
    step('Content Quality collects the quality signals of every tenant\'s content. Tenants never see them.',
      'Trang Chất lượng nội dung gom các tín hiệu chất lượng của nội dung mọi đại lý. Đại lý không bao giờ thấy trang này.',
      async (page, h) => {
        await check(page, h, '/admin/content-quality', { heading: 'Content Quality', ready: '[data-testid="content-quality-ready"]' });
      }),
    step('The list of pieces loaded. The admin only reads here. This is the end of the scenario.',
      'Danh sách nội dung đã tải. Ở đây quản trị viên chỉ đọc. Kết thúc kịch bản.',
      async (page, h) => {
        await rowsOrEmpty(page, h);
      }),
  ],
});
