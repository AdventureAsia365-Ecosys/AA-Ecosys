// UAT scenario PRT-14 (AA-855 round 1, catalogue.json): the Content studio in Vietnamese, then back.
// Given: the Content studio VIEWER of the E2E tenant (lib/signin.cjs studio). The studio opens in English.
// When:  they open My Content, pick Tiếng Việt in the account menu's language switch, read the page, then switch back
//        to the language they had.
// Then:  the heading reads "Nội dung của tôi", then "My Content" again. The one request the browser lets through is
//        POST /prefs/locale, which sets only the person's language cookie (no app data). No model call. $0. 1440 x 900.
const { HOSTS, step, check } = require('../../lib/dryrun-page.cjs');
const { rw } = require('../../lib/uat-page.cjs');

let original = null;

async function pickLocale(page, h, value) {
  const select = page.getByTestId('portal-locale').getByTestId('locale-select');
  // Right after the language reload the menu button can render before it is interactive: click until the menu shows
  // (never a second click while it is open, which would close it again).
  await h.expect(async () => {
    if (!(await select.isVisible())) await h.click(page.getByRole('button', { name: /^(Account menu|Menu tài khoản)$/ }));
    await h.expect(select).toBeVisible({ timeout: 2_000 });
  }).toPass({ timeout: 20_000 });
  if (original === null) original = await select.inputValue();
  await Promise.all([
    page.waitForResponse((r) => new URL(r.url()).pathname === '/prefs/locale', { timeout: 30_000 }),
    select.selectOption(value),
  ]);
  await page.waitForLoadState('load');
}

const sc = rw({
  allowWrites: ['\\/prefs\\/locale$'],
  id: 'PRT-14',
  app: 'content-studio',
  identity: 'studio',
  title: 'The Content studio in Vietnamese',
  titleVi: 'Content studio bằng tiếng Việt',
  baseURL: HOSTS.partner,
  steps: [
    step('The studio opens in English for everyone. Each person can choose their own language.',
      'Studio mở bằng tiếng Anh cho mọi người. Mỗi người có thể chọn ngôn ngữ của riêng mình.',
      async (page, h) => {
        await check(page, h, '/portal/content', { heading: 'My Content' });
      }),
    step('In the account menu, the member picks Tiếng Việt. The whole studio switches, dates included.',
      'Trong menu tài khoản, thành viên chọn Tiếng Việt. Toàn bộ studio chuyển ngôn ngữ, kể cả ngày tháng.',
      async (page, h) => {
        await pickLocale(page, h, 'vi-VN');
        await h.expect(page.locator('h1').first()).toContainText('Nội dung của tôi', { timeout: 30_000 });
      }),
    step('Switching back is the same two clicks. This is the end of the scenario.',
      'Chuyển lại cũng chỉ hai lần bấm. Kết thúc kịch bản.',
      async (page, h) => {
        await pickLocale(page, h, original && original !== 'vi-VN' ? original : 'en-AU');
        await h.expect(page.locator('h1').first()).toContainText('My Content', { timeout: 30_000 });
      }),
  ],
});
// A failed step must not leave the viewer's browser session in Vietnamese for the next scenario of the same state.
sc.after = async (page, h) => {
  const h1 = await page.locator('h1').first().textContent().catch(() => '');
  if (/Nội dung của tôi/.test(h1 || '')) await pickLocale(page, h, original && original !== 'vi-VN' ? original : 'en-AU');
};

module.exports = sc;
