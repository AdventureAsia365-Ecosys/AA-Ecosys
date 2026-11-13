// UAT scenario REH-04-edit (pilot rehearsal step 4, part 3; root docs/ops/runbooks/pilot-rehearsal.md): the agency
// owner opens the delivered blog article in My Content, sees only the agency's own text (no writer brief, no search
// context), edits it to end with the agency's planner link for tour X, and saves. REH-04b-wordpress then publishes that
// text, so the live post links to /pilot-rehearsal-01/plan?tour=<X>.
// Writes ONE thing: PATCH /v1/content-writing/pieces/<the article> (the edit; no model call). Cost $0. Re-run safe:
// an earlier planner line is replaced, never added twice. Runs on pilot-rehearsal-01 only (pilot guard).
// Env: UAT_REH_TOUR_X (tour X's id). Given: REH-04-blog delivered the article (lib/write-chain.cjs, else the newest
// ready article). Then: the saved text ends with the planner link; the viewer holds no internal writer input. 1440 x 900.
const { HOSTS, step, check } = require('../../lib/dryrun-page.cjs');
const { rw } = require('../../lib/uat-page.cjs');
const R = require('./_rehearsal.cjs');

const { reh } = R;
const LINE = 'Plan this trip with us:';
// Writer input the agency must never see in its viewer (the old "Where this came from" block of the drawer).
const INTERNAL = /Where this came from|People also ask|Related keywords|Writer brief|Search context|formula fit/i;
let piece = null;
let link = '';
const patches = [];
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
        page.on('request', (q) => { if (q.method() === 'PATCH' && R.PATHS.piece.test(new URL(q.url()).pathname)) patches.push(q.url()); });
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
        const kept = (await box.inputValue()).split('\n').filter((l) => !l.startsWith(LINE)).join('\n').trimEnd();
        await box.fill(`${kept}\n\n${LINE} ${link}`);
        await h.scrollTo(box, 'end');
        await box.press('End');
      }),
    step('Save keeps the edited text. This is the version that will be published. This is the end of the scenario.',
      'Bấm Lưu để giữ bản đã sửa. Đây là bản sẽ được đăng. Kết thúc kịch bản.',
      async (page, h) => {
        const saved = page.waitForResponse((r) => R.isCall(r, R.PATHS.piece, 'PATCH'), { timeout: 30_000 });
        await h.click(drawer(page).getByRole('button', { name: 'Save', exact: true }));
        const res = await saved;
        if (res.status() !== 200) throw new Error(`saving the edit answered ${res.status()}`);
        await h.expect(drawer(page).locator('textarea')).toHaveCount(0, { timeout: 15_000 });
        await h.expect(drawer(page)).toContainText(link, { timeout: 15_000 });
        const items = await R.W.reviews(page);
        const now = items.find((i) => i.piece_id === piece.piece_id);
        if (!now || !String(now.content_text || '').includes(link)) throw new Error('the saved article does not carry the planner link');
        if (patches.length !== 1) throw new Error(`${patches.length} edit saves in this run (exactly one expected)`);
      }, { writes: true }),
  ],
});

module.exports = sc;
