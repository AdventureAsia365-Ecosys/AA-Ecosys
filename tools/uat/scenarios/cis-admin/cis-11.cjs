// Dry-run scenario CIS-11 (AA-1009, plan §4): the docs reader with its English / Vietnamese switch, read only.
// Given: the E2E CIS admin (read-only session). When: they open the glossary, switch it to Vietnamese and back.
// Then: the article renders in each language (article[lang]); no API call fails; nothing is written (the language
// choice lives in the browser only; "Reload" is never clicked). $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

const GLOSSARY = '/admin/docs?path=docs%2Fglossary.md';

module.exports = ro({
  id: 'CIS-11',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Docs reader: a page in English and in Vietnamese',
  titleVi: 'Trình đọc tài liệu: một trang bằng tiếng Anh và tiếng Việt',
  baseURL: HOSTS.cisAdmin,
  steps: [
    step('The admin opens the company docs inside the admin and picks the glossary.',
      'Quản trị viên mở tài liệu công ty ngay trong trang quản trị và chọn trang thuật ngữ.',
      async (page, h) => {
        await check(page, h, GLOSSARY, { heading: 'Docs', ready: 'article' });
      }),
    step('The page has a Vietnamese copy: one click switches the language.',
      'Trang này có bản tiếng Việt: một cú bấm là đổi ngôn ngữ.',
      async (page, h) => {
        const sw = page.getByTestId('docs-lang-switch');
        await h.expect(sw).toBeVisible({ timeout: 15_000 });
        await h.click(sw.getByRole('button', { name: /^Vietnamese/ }));
        await h.expect(page.locator('article[lang="vi"]')).toBeVisible({ timeout: 30_000 });
      }),
    step('Back to English. This is the end of the scenario.',
      'Chuyển lại tiếng Anh. Kết thúc kịch bản.',
      async (page, h) => {
        await h.click(page.getByTestId('docs-lang-switch').getByRole('button', { name: /^English/ }));
        await h.expect(page.locator('article[lang="en"]')).toBeVisible({ timeout: 30_000 });
      }),
  ],
});
