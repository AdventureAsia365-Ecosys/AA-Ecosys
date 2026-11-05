// UAT scenario PRT-08 (AA-855 round 1, catalogue.json): My Content, export one piece, read only.
// Given: the Content studio VIEWER of the E2E tenant (lib/signin.cjs studio) and at least one written piece on it.
// When:  they open My Content, open the first piece and press its first Export button.
// Then:  the browser receives one download whose file name ends in .txt or .html (the export GET; the file is built in
//        the page through a blob, so no link shows); only the file name is checked, the file is not kept. Nothing is
//        written by the page, no model is called. $0. Desktop 1440 x 900.
const { HOSTS, step, ro, check, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');

const ROW = '[data-testid="kit-datatable-row"]';
let fileName = '';

module.exports = ro({
  id: 'PRT-08',
  app: 'content-studio',
  identity: 'studio',
  title: 'My Content: export a piece',
  titleVi: 'Nội dung của tôi: xuất một bài',
  baseURL: HOSTS.partner,
  steps: [
    step('My Content lists every piece the agency wrote, where it came from and whether it is ready.',
      'Mục Nội dung của tôi liệt kê mọi bài đại lý đã viết, nguồn gốc và trạng thái sẵn sàng.',
      async (page, h) => {
        await check(page, h, '/portal/content', { heading: 'My Content' });
        await rowsOrEmpty(page, h);
        if (!(await page.locator(ROW).count())) throw new Error('no piece on this tenant (precondition: one written piece)');
      }),
    step('A piece opens with its text and its export buttons.',
      'Một bài mở ra với nội dung và các nút xuất file.',
      async (page, h) => {
        await h.click(page.locator(ROW).first());
        const panel = page.getByRole('dialog').first();
        await h.expect(panel).toBeVisible({ timeout: 30_000 });
        await h.expect(panel.getByRole('button', { name: /^Export/ }).first()).toBeVisible({ timeout: 30_000 });
      }),
    step('Export downloads the piece as a file named after its title, ready for the agency\'s own site or tools. This is the end of the scenario.',
      'Xuất file tải bài viết về dưới tên theo tiêu đề, dùng ngay cho website hay công cụ của đại lý. Kết thúc kịch bản.',
      async (page, h) => {
        const download = page.waitForEvent('download', { timeout: 30_000 });
        await h.click(page.getByRole('dialog').first().getByRole('button', { name: /^Export/ }).first());
        const d = await download;
        fileName = d.suggestedFilename();
        await d.cancel().catch(() => {});
        if (!/^[^/\\]+\.(txt|html)$/.test(fileName)) throw new Error(`unexpected export file name ${fileName}`);
      }),
  ],
});
