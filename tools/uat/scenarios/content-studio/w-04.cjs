// UAT scenario W-04 (AA-855 round 1, catalogue.json): export the article as an HTML page with the AI mark, and a
// social post as text. Read only and $0: every export is a GET (the studio builds the file in the page; CIS logs the
// export in its audit trail), no model is called, every other write is aborted. It is in the dry-run set (identity
// studio-audit can write, so only with --include-writable).
// The article is the one W-03 delivered (lib/write-chain.cjs), else the audit tenant's newest ready article; the social
// post is its newest ready piece of any other channel (the T-series audit wrote several on each audit tenant).
// Given: the studio-audit editor on the audit tenant, one ready article and one ready social post.
// When:  they open the article in My Content and press Export HTML file, then open a social post and press Export.
// Then:  an .html file whose <article> and <meta> say the text is AI-generated, and a non-empty .txt file. 1440 x 900.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');
const { downloadBytes, AI_MARK } = require('../../lib/uat-page.cjs');
const { reviews, chain, auditTenant } = require('./_write.cjs');

let items = null;

/** Open My Content on one piece (the deep link the write-done popup and the command palette use). */
async function openPiece(page, h, pieceId) {
  await check(page, h, `/portal/content?piece=${encodeURIComponent(pieceId)}`, { heading: 'My Content' });
  const drawer = page.getByRole('dialog').first();
  await h.expect(drawer).toBeVisible({ timeout: 30_000 });
  return drawer;
}

async function exported(page, h, button) {
  const download = page.waitForEvent('download', { timeout: 60_000 });
  await h.click(button);
  const d = await download;
  return { name: d.suggestedFilename(), bytes: await downloadBytes(d) };
}

module.exports = ro({
  id: 'W-04',
  app: 'content-studio',
  identity: 'studio-audit',
  title: 'Export the article as HTML with the AI mark, and a social post',
  titleVi: 'Xuất bài viết dạng HTML có dấu AI, và một bài mạng xã hội',
  baseURL: HOSTS.partner,
  steps: [
    step('My Content opens the new article with its text and its export buttons.',
      'Nội dung của tôi mở bài viết mới cùng nội dung và các nút xuất file.',
      async (page, h) => {
        await check(page, h, '/portal/content', { heading: 'My Content' });
        items = await reviews(page);
        const fromChain = (chain.read(auditTenant().slug) || {}).piece_id;
        const article = items.find((i) => i.piece_id === fromChain && i.channel === 'blog' && i.ready_state === 'ready')
          || chain.newest(items, { channel: 'blog', ready: true });
        if (!article) throw new Error('no ready article on this audit tenant (run W-02 and W-03 first)');
        const drawer = await openPiece(page, h, article.piece_id);
        await h.expect(drawer.getByRole('button', { name: 'Export HTML file' })).toBeVisible({ timeout: 30_000 });
      }),
    step('Export HTML file downloads a web page with the article. The page carries a machine-readable mark that the text is AI-generated.',
      'Xuất file HTML tải về một trang web chứa bài viết. Trang mang dấu hiệu máy đọc được cho biết văn bản do AI tạo.',
      async (page, h) => {
        const f = await exported(page, h, page.getByRole('dialog').first().getByRole('button', { name: 'Export HTML file' }));
        if (!/^[^/\\]+\.html$/.test(f.name) || /\.fragment\.html$/.test(f.name)) throw new Error(`unexpected export file name ${f.name}`);
        const html = f.bytes.toString('utf8');
        if (!AI_MARK.article.test(html)) throw new Error('the HTML export has no AI mark on its <article>');
        if (!AI_MARK.meta.test(html)) throw new Error('the HTML export has no ai-generated <meta> tag');
      }),
    step('A social post exports as plain text, ready to paste into the agency\'s own channel. This is the end of the scenario.',
      'Bài mạng xã hội xuất ra văn bản thuần, dán ngay vào kênh của đại lý. Kết thúc kịch bản.',
      async (page, h) => {
        const social = chain.newest(items, { channel: '!blog', ready: true });
        if (!social) throw new Error('no ready social post on this audit tenant');
        await page.keyboard.press('Escape');
        const drawer = await openPiece(page, h, social.piece_id);
        const f = await exported(page, h, drawer.getByRole('button', { name: 'Export', exact: true }));
        if (!/^[^/\\]+\.txt$/.test(f.name)) throw new Error(`unexpected export file name ${f.name}`);
        if (!f.bytes.toString('utf8').trim()) throw new Error('the text export is empty');
      }),
  ],
});
