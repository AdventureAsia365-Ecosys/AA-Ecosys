// UAT scenario REH-04-edit (pilot rehearsal step 4, part 3; root docs/ops/runbooks/pilot-rehearsal.md): the agency
// owner opens the delivered blog article in My Content, sees only the agency's own text (no writer brief, no search
// context), edits it to end with the agency's planner link for tour X, and saves. REH-04b-wordpress then publishes that
// text, so the live post links to /pilot-rehearsal-01/plan?tour=<X>.
// The line is a Markdown link, [Plan this trip with us](<link>): CIS renders the blog with Python-Markdown (no bare-URL
// autolink), so only this form becomes an <a href> on WordPress; the studio viewer shows the link text, underlined.
// Writes ONE thing: PATCH /v1/content-writing/pieces/<the article> (the edit; no model call), capped at one by
// limitWrites and allowed for PATCH only. Cost $0. Re-run safe: an earlier planner line (either form) is replaced,
// never added twice. Runs on pilot-rehearsal-01 only (pilot guard).
// Env: UAT_REH_TOUR_X (tour X's id). Given: REH-04-blog delivered the article (lib/write-chain.cjs, else the newest
// ready article). Then: the saved text ends with the planner link; the viewer holds no internal writer input. 1440 x 900.
const { HOSTS, step, check } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const R = require('./_rehearsal.cjs');

const { reh } = R;
const TEXT = 'Plan this trip with us';
// The closing line, and the spellings an earlier take may have left (the old bare-URL form included).
const plannerLine = (url) => `[${TEXT}](${url})`;
const isPlannerLine = (l) => l.startsWith(`[${TEXT}](`) || l.startsWith(`${TEXT}:`);
// Writer input the agency must never see in its viewer (the old "Where this came from" block of the drawer).
const INTERNAL = /Where this came from|People also ask|Related keywords|Writer brief|Search context|formula fit/i;
let piece = null;
let link = '';
let counts = null;
const drawer = (page) => page.getByRole('dialog').first();

const sc = rw({
  id: 'REH-04-edit',
  app: 'content-studio',
  identity: R.IDENTITY,
  title: 'Pilot rehearsal: edit the article in the viewer',
  titleVi: 'Diễn tập pilot: sửa bài viết ngay trong trình xem',
  baseURL: HOSTS.partner,
  allowWrites: R.allow('piece'),
  steps: [
    step('My Content opens the new article. The viewer shows only the agency\'s own text and the AI notice.',
      'Nội dung của tôi mở bài viết mới. Trình xem chỉ hiện nội dung của đại lý và thông báo về AI.',
      async (page, h) => {
        counts = await limitWrites(page, R.capRules(['piece']));
        await check(page, h, '/portal/content', { heading: 'My Content' });
        piece = await R.readyPiece(page, 'blog');
        if (!piece) throw new Error('no ready article on the rehearsal agency (record REH-04-blog first)');
        link = reh.plannerLink((await R.findTourX(page)).tour_id);
        await check(page, h, `/portal/content?piece=${encodeURIComponent(piece.piece_id)}`, { heading: 'My Content' });
        await h.expect(drawer(page)).toBeVisible({ timeout: 30_000 });
        await h.expect(drawer(page).getByTestId('ai-notice').first()).toBeVisible({ timeout: 30_000 });
        const text = await drawer(page).innerText();
        if (INTERNAL.test(text)) throw new Error('the viewer shows internal writer input (brief or search context)');
      }),
    step('Edit opens the text. The owner adds a closing line with the agency\'s own trip planner link for this tour.',
      'Bấm Sửa để mở nội dung. Chủ đại lý thêm một dòng cuối có đường dẫn tới trang lập kế hoạch chuyến đi của đại lý.',
      async (page, h) => {
        await h.click(drawer(page).getByRole('button', { name: 'Edit', exact: true }));
        const box = drawer(page).locator('textarea').first();
        await h.expect(box).toBeVisible({ timeout: 15_000 });
        const kept = (await box.inputValue()).split('\n').filter((l) => !isPlannerLine(l.trim())).join('\n').trimEnd();
        if (!kept) throw new Error('the article text is empty in the editor');
        const edited = `${kept}\n\n${plannerLine(link)}`;
        await box.fill(edited);
        await h.scrollTo(box, 'end');
        await box.press('End');
        await h.expect(box).toHaveValue(edited);
      }),
    step('Save keeps the edited text. This is the version that will be published. This is the end of the scenario.',
      'Bấm Lưu để giữ bản đã sửa. Đây là bản sẽ được đăng. Kết thúc kịch bản.',
      async (page, h) => {
        const saved = page.waitForResponse((r) => R.isCall(r, R.PATHS.piece, 'PATCH'), { timeout: 30_000 });
        await h.click(drawer(page).getByRole('button', { name: 'Save', exact: true }));
        const res = await saved;
        if (res.status() !== 200) throw new Error(`saving the edit answered ${res.status()}`);
        await h.expect(drawer(page).locator('textarea')).toHaveCount(0, { timeout: 15_000 });
        // The viewer renders the Markdown: the link shows as its text, never as the raw [..](..) line.
        await h.expect(drawer(page)).toContainText(TEXT, { timeout: 15_000 });
        await h.expect(drawer(page)).not.toContainText(`](${link})`);
        const items = await R.W.reviews(page);
        const now = items.find((i) => i.piece_id === piece.piece_id);
        const lines = String((now && now.content_text) || '').trimEnd().split('\n');
        if (lines[lines.length - 1] !== plannerLine(link)) throw new Error('the saved article does not end with the planner link');
        if (lines.filter((l) => isPlannerLine(l.trim())).length !== 1) throw new Error('the saved article carries the planner line more than once');
        if (counts.piece !== 1) throw new Error(`${counts.piece} edit saves in this run (exactly one expected)`);
      }, { writes: true }),
  ],
});

module.exports = sc;
