// Dry-run scenario PRT-09 (AA-1009, plan §4): the agency's own facts, read only (no add, no edit).
// Given: the studio viewer (lib/signin.cjs studio). When: they open Brand > Facts.
// Then: the title and the facts table (or its empty state) render; no API call fails; nothing is written. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'PRT-09',
  app: 'content-studio',
  identity: 'studio',
  title: 'Tenant facts the writer cites',
  titleVi: 'Dữ kiện của đại lý mà người viết trích dẫn',
  baseURL: HOSTS.partner,
  steps: [
    step('Facts are the agency\'s own sourced statements, which the writer may cite in its content.',
      'Dữ kiện là những thông tin có nguồn của chính đại lý, người viết có thể trích dẫn trong nội dung.',
      async (page, h) => {
        await check(page, h, '/portal/facts', { heading: 'Facts', table: true });
      }),
    step('The list loaded. A viewer only reads it. This is the end of the scenario.',
      'Danh sách đã tải. Người xem chỉ đọc. Kết thúc kịch bản.',
      async (page, h) => {
        await h.smoothScrollBy(400);
        await h.expect(page.locator('h1').first()).toContainText('Facts');
      }),
  ],
});
