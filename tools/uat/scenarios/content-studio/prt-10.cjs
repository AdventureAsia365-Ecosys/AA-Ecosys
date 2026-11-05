// Dry-run scenario PRT-10 (AA-1009, plan §4; AA-855 round 1): Integrations and the Facebook help page, read only. The
// tenant API key page went with the tenant API keys (one agency app, AA-1036 R3): the publishing connections replace it.
// Given: the studio viewer. When: they open Integrations and the Facebook help page. Then: titles and their sections
// render; no secret is shown (a connection lists its status only); nothing is written. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'PRT-10',
  app: 'content-studio',
  identity: 'studio',
  title: 'Integrations and the Facebook help page',
  titleVi: 'Kết nối và trang hướng dẫn Facebook',
  baseURL: HOSTS.partner,
  steps: [
    step('Integrations lists the agency\'s publishing channels, its WordPress site and its Facebook Page, with the health of each.',
      'Trang Kết nối liệt kê các kênh đăng bài của đại lý, website WordPress và Trang Facebook, kèm tình trạng của từng kênh.',
      async (page, h) => {
        await check(page, h, '/portal/account/integrations', { heading: 'Integrations' });
        await h.expect(page.getByRole('heading', { name: /WordPress/ }).first()).toBeVisible({ timeout: 30_000 });
      }),
    step('The help page walks through connecting a Facebook Page. This is the end of the scenario.',
      'Trang hướng dẫn chỉ từng bước kết nối một Trang Facebook. Kết thúc kịch bản.',
      async (page, h) => {
        await check(page, h, '/portal/help/facebook', { heading: 'Connect your Facebook Page' });
        await h.expect(page.getByText('Before you start').first()).toBeVisible();
      }),
  ],
});
