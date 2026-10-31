// Dry-run scenario CRM-01 (AA-1009, plan §4): CRM home and the pipeline board, read only.
// Given: the owner of the invented review agency signed in outside the run (lib/crm-signin.cjs identity A).
// When:  they open the home page, then the pipeline. Then: both render with their sections; no BFF call fails; nothing
// is written (the read-only guard aborts any non-GET request and fails the scenario on one). $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'CRM-01',
  app: 'crm',
  identity: 'crm',
  title: 'CRM home and the pipeline board',
  titleVi: 'Trang chủ CRM và bảng quy trình bán',
  baseURL: HOSTS.partner,
  scrollBlock: 'center', // the CRM shell has a sticky top bar
  steps: [
    step('The agency owner opens the CRM. Home shows what needs attention and the setup progress.',
      'Chủ đại lý mở CRM. Trang chủ cho biết việc cần chú ý và tiến độ thiết lập.',
      async (page, h) => {
        await check(page, h, '/', { heading: 'Welcome', ready: '[data-testid="crm-home"]' });
      }),
    step('The pipeline board shows every trip by stage, from inquiry to travelling. This is the end of the scenario.',
      'Bảng quy trình bán hiển thị mọi chuyến theo giai đoạn, từ yêu cầu đến khi đang đi. Kết thúc kịch bản.',
      async (page, h) => {
        await check(page, h, '/pipeline', { heading: 'Pipeline', ready: '[data-testid="crm-pipeline"]' });
        await h.expect(page.getByTestId('board').first()).toBeVisible({ timeout: 30_000 });
      }),
  ],
});
