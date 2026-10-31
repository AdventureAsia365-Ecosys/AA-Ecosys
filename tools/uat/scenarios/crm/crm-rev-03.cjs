// CRM review R03 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): a new inquiry reaches the board.
// Given: the agency's public inquiry form on the client host (no account); A (owner) signed in on the CRM.
// When:  an invented traveller (C) fills the form and sends it; the owner opens the pipeline.
// Then:  the form thanks the traveller (202, no 429); within about a minute the trip card is in the Inquiry column.
// Writes one invented prospect (@example.invalid, run suffix) through the public form; the trip id goes to
// work/crm/state.json (r03) for R04-R06. One anonymous write, so the 5-per-minute limit is never reached. Cost $0.
const { crm, st, base, sha, open, waitForCard, prospect, type, choose } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-03', title: 'A traveller sends an inquiry and the trip lands on the board', titleVi: 'Khách gửi yêu cầu và chuyến xuất hiện trên bảng' });
let s;
let who;
let seen429;

sc.steps = [
  {
    caption: {
      en: 'A traveller finds the agency\'s website and opens its inquiry form. No account is needed.',
      vi: 'Một khách du lịch vào website của đại lý và mở form yêu cầu tư vấn. Không cần tài khoản.',
    },
    run: async (page, h) => {
      s = st.load();
      st.runTag(s);
      const attempt = ((s.r03 && s.r03.attempt) || 0) + 1;
      who = prospect(s, attempt > 1 ? `r03a${attempt}` : 'r03', 'Hanna', 'Berg');
      if (attempt > 1) who.name = `${who.name}-${attempt}`;
      who.attempt = attempt;
      seen429 = crm.watch429(page);
      await sha(page, sc, 'start');
      await h.goto(`${crm.CLIENT}/c/f/${s.form_key}`);
      await h.expect(page.getByTestId('intake-form')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
      await h.expect(page.getByRole('heading', { level: 1 })).toContainText('Lữ hành Sen Vàng');
    },
  },
  {
    caption: {
      en: 'She picks Vietnam, six nights for one adult (one seat on the Adventure Asia tour), a budget band and a balanced pace.',
      vi: 'Chị chọn Việt Nam, sáu đêm cho một người lớn (một chỗ trên tour của Adventure Asia), một mức ngân sách và nhịp độ vừa phải.',
    },
    run: async (page, h) => {
      await h.click(page.getByTestId('intake-dest-vietnam'));
      await type(page, h, page.locator('input[name="nights"]'), '6');
      await type(page, h, page.locator('input[name="adults"]'), '1');
      await choose(h, page.locator('select[name="budget_band"]'), '2000_3500');
      await choose(h, page.locator('select[name="trip_style"]'), 'balanced');
    },
  },
  {
    caption: {
      en: 'She adds her name, her e-mail and a short message, and agrees to be contacted.',
      vi: 'Chị điền tên, e-mail, một lời nhắn ngắn và đồng ý để đại lý liên hệ.',
    },
    run: async (page, h) => {
      await type(page, h, page.locator('input[name="name"]'), who.name);
      await type(page, h, page.locator('input[name="email"]'), who.email);
      await type(page, h, page.locator('textarea[name="message"]'), 'Hoi An and the central coast, slow pace, good food.');
      await h.click(page.getByTestId('intake-consent'));
      await h.expect(page.getByTestId('intake-consent')).toBeChecked();
    },
  },
  {
    caption: {
      en: 'She sends the inquiry and gets a thank-you page straight away.',
      vi: 'Chị gửi yêu cầu và thấy ngay trang cảm ơn.',
    },
    run: async (page, h) => {
      await crm.paceClientWrite();
      const answer = page.waitForResponse((r) => r.request().method() === 'POST' && /\/crm\/public\/v1\/forms\/[^/]+\/submissions$/.test(new URL(r.url()).pathname), { timeout: 30_000 });
      await h.click(page.getByTestId('intake-submit').getByRole('button'));
      const res = await answer;
      h.expect(res.status()).toBe(202);
      await h.expect(page.getByTestId('intake-thanks')).toBeVisible({ timeout: 15_000 });
      crm.assertNo429(seen429);
    },
  },
  {
    caption: {
      en: 'At the agency, the owner opens the pipeline. The new trip arrives in the Inquiry column within about a minute.',
      vi: 'Ở đại lý, chủ đại lý mở pipeline. Chuyến mới xuất hiện ở cột Inquiry trong khoảng một phút.',
    },
    run: async (page, h) => {
      await open(page, h, '/pipeline', 'board');
      const card = await waitForCard(page, who.name);
      const loc = page.locator(`[data-testid="column-inquiry"] [data-testid="trip-card"][data-trip-id="${card.trip_id}"]`);
      for (let i = 0; i < 3 && !(await loc.count()); i++) await open(page, h, '/pipeline', 'board');
      await h.expect(loc).toHaveCount(1);
      await h.scrollTo(loc);
      await h.hover(loc);
      s = st.load();
      s.r03 = { trip_id: card.trip_id, lead_name: who.name, email: who.email, attempt: who.attempt, at: new Date().toISOString() };
      st.remember(s, 'trips', card.trip_id);
      st.save(s);
    },
  },
  {
    caption: {
      en: 'The card shows who the trip is for, the party size and that the agency owes the next reply.',
      vi: 'Thẻ cho biết chuyến của ai, số người và việc trả lời tiếp theo đang thuộc về đại lý.',
    },
    run: async (page, h) => {
      const loc = page.locator(`[data-testid="trip-card"][data-trip-id="${s.r03.trip_id}"]`);
      await h.expect(loc).toHaveAttribute('data-waiting', 'agency');
      await h.expect(loc.getByTestId('trip-card-party')).toBeVisible();
      await h.pause(1500);
      crm.assertNo429(seen429);
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
