// Dry-run scenario PRT-10 (AA-1009, plan §4): API access and help, read only. The API key itself is never shown on
// this page (it is shown once, when issued), so nothing needs masking. Given: the studio viewer. When: they open API
// Access and the Facebook help page. Then: titles and their sections render; nothing is written. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'PRT-10',
  app: 'content-studio',
  identity: 'studio',
  title: 'API access and the Facebook help page',
  titleVi: 'Truy cập API và trang hướng dẫn Facebook',
  baseURL: HOSTS.partner,
  steps: [
    step('API Access explains how the agency reads its rewritten tours from its own systems.',
      'Trang Truy cập API giải thích cách đại lý đọc các tour đã viết lại từ hệ thống của mình.',
      async (page, h) => {
        await check(page, h, '/portal/account/api', { heading: 'API Access' });
        await h.expect(page.getByText(/Your API key is not shown here/).first()).toBeVisible({ timeout: 30_000 });
      }),
    step('The help page walks through connecting a Facebook Page. This is the end of the scenario.',
      'Trang hướng dẫn chỉ từng bước kết nối một Trang Facebook. Kết thúc kịch bản.',
      async (page, h) => {
        await check(page, h, '/portal/help/facebook', { heading: 'Connect your Facebook Page' });
        await h.expect(page.getByText('Before you start').first()).toBeVisible();
      }),
  ],
});
