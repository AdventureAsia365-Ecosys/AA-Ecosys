// CRM review R13 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): e-mail on the trip.
// Given: A (owner) signed in; the agency mailbox is connected; the Dev "mail probe" trip holds two threads of invented
//        automated probe mails (UAT_CRM_MAIL_TRIP overrides its id).
// When:  the owner reads the trip's threads (sent from the agency's own mailbox, replies matched back by the trip
//        reference), adds a saved reply in Settings, then on the trip starts a new e-mail from that saved reply.
// Then:  both threads show their messages; the saved reply is listed; the draft autosaves ("Saved"); Send is never
//        pressed in this chunk. Microsoft 365 send-as is not built: "Not ready yet" card.
// The real mailbox address and every sender line are blurred (lib/crm-signin.cjs mask), and so is any text with an
// address that is not an invented *.invalid one (quoted "On ... <address> wrote:" lines; _crm.cjs REAL_ADDRESS);
// steps 1-2 assert it. Other chunks do mail clients through this mailbox (see prep.cjs). Writes: one saved reply and
// one draft (ids kept in work/crm/state.json; cleanup.cjs deletes both). No LLM call. Cost $0.
const slide = require('../../lib/slide.cjs');
const { st, base, sha, open, bffOk, type, choose, reuse } = require('./_crm.cjs');

const MAIL_TRIP = process.env.UAT_CRM_MAIL_TRIP || '204b00cc-2122-420a-a217-a2f80ce1b140';
const sc = base({ id: 'CRM-REV-13', title: 'E-mail on the trip: threads, a saved reply and a draft', titleVi: 'E-mail trên chuyến: luồng thư, câu trả lời mẫu và bản nháp' });
let s;
let title;

const panel = (page) => page.getByTestId('trip-messages');

sc.steps = [
  {
    caption: {
      en: 'Every e-mail with a client lives on the trip. It goes out from the agency\'s own mailbox, and replies come back to the right trip.',
      vi: 'Mọi e-mail với khách đều nằm trên chuyến. Thư được gửi từ hộp thư của chính đại lý, và thư trả lời quay về đúng chuyến.',
    },
    run: async (page, h) => {
      s = st.load();
      st.runTag(s);
      await sha(page, sc, 'start');
      const mb = await bffOk(page, 'GET', 'mailbox');
      h.expect((mb.mailboxes || []).some((m) => m.status === 'connected'), 'a connected agency mailbox').toBe(true);
      await open(page, h, `/pipeline/${MAIL_TRIP}`, 'crm-trip');
      const p = panel(page);
      await h.scrollTo(p);
      await h.expect(p.locator('li').first()).toBeVisible({ timeout: 20_000 });
      await h.hover(p.locator('li').first());
      await h.assertMasked(['[data-testid="trip-messages"] li > div:first-child > span:first-child']);
    },
  },
  {
    caption: {
      en: 'This trip has two threads. The client\'s replies land in them, matched by the trip reference in the subject or by the reply headers.',
      vi: 'Chuyến này có hai luồng thư. Thư trả lời của khách nằm trong đó, được ghép nhờ mã chuyến trong tiêu đề hoặc nhờ thông tin trả lời của thư.',
    },
    run: async (page, h) => {
      const p = panel(page);
      const threads = p.getByRole('button', { name: /·\s*\d+$/ });
      h.expect(await threads.count()).toBeGreaterThanOrEqual(2);
      await h.click(threads.nth(1));
      await h.expect(p.locator('li').filter({ hasText: /^.*Re:/ }).first()).toBeVisible({ timeout: 15_000 });
      await h.hover(p.locator('li').filter({ hasText: 'Re:' }).first());
      await h.assertMasked(['[data-testid="trip-messages"] li > div:first-child > span:first-child']);
    },
  },
  {
    caption: {
      en: 'Answers the team writes often are kept as saved replies. The owner adds one in Settings.',
      vi: 'Những câu trả lời hay dùng được lưu thành câu trả lời mẫu. Chủ đại lý thêm một mẫu trong Settings.',
    },
    run: async (page, h) => {
      title = `Deposit received ${s.run}`;
      await open(page, h, '/settings/saved-replies', 'saved-replies');
      const list = page.getByTestId('saved-replies-list');
      if (await list.getByText(title).count()) reuse(h, 'this run\'s saved reply', 'cleanup.cjs deletes it');
      else {
        const form = page.getByTestId('saved-replies-new');
        await h.scrollTo(form);
        await type(page, h, form.locator('input[name="title"]'), title);
        await type(page, h, form.locator('textarea[name="body"]'), 'Thank you, we have received your deposit. Your trip is now booked and your personal travel portal link is on its way.');
        await choose(h, form.locator('select[name="locale"]'), 'en');
        await h.click(form.getByRole('button').last());
      }
      await h.expect(list.getByText(title)).toBeVisible({ timeout: 15_000 });
      const replies = await bffOk(page, 'GET', 'saved-replies');
      const r = (replies.saved_replies || []).find((x) => x.title === title);
      h.expect(r, 'the saved reply').toBeTruthy();
      s = st.load();
      st.remember(s, 'saved_replies', r.saved_reply_id);
      st.save(s);
    },
  },
  {
    caption: {
      en: 'Back on the trip, the owner starts a new e-mail from that saved reply and adds a subject.',
      vi: 'Quay lại chuyến, chủ đại lý soạn e-mail mới từ câu trả lời mẫu đó và thêm tiêu đề.',
    },
    run: async (page, h) => {
      await open(page, h, `/pipeline/${MAIL_TRIP}`, 'crm-trip');
      const composer = panel(page).getByTestId('messages-composer');
      await h.scrollTo(composer);
      if ((await composer.locator('textarea').inputValue()).trim()) reuse(h, 'a saved draft on the mail trip', 'cleanup.cjs deletes it');
      await composer.locator('textarea').fill(''); // --fast only: start the rehearsal from an empty composer
      await composer.locator('input[aria-label]').first().fill('');
      const pick = composer.locator('select[aria-label]').first();
      const id = (st.load().created.saved_replies || []).slice(-1)[0];
      await choose(h, pick, id);
      await h.expect(composer.locator('textarea')).toHaveValue(/received your deposit/);
      const drafted = page.waitForResponse((r) => /\/messages\/drafts\/[0-9a-f-]{36}$/.test(new URL(r.url()).pathname) && r.request().method() === 'PUT', { timeout: 30_000 });
      await type(page, h, composer.locator('input[aria-label]').first(), `Your deposit · ${s.run}`);
      const res = await drafted;
      h.expect(res.status()).toBeLessThan(300);
      s = st.load();
      st.remember(s, 'drafts', new URL(res.url()).pathname.split('/').pop());
      st.save(s);
    },
  },
  {
    caption: {
      en: 'The draft saves by itself. Send is not pressed here; a sent e-mail can still be undone for ten seconds.',
      vi: 'Bản nháp tự lưu. Ở đây không bấm Send; e-mail đã gửi vẫn có thể rút lại trong mười giây.',
    },
    run: async (page, h) => {
      const composer = panel(page).getByTestId('messages-composer');
      await h.expect(composer.getByTestId('messages-save-state')).toHaveText(/saved/i, { timeout: 20_000 });
      const send = composer.getByRole('button', { name: /^send$/i });
      await h.expect(send).toBeEnabled();
      await h.hover(send); // never clicked
      await h.hover(composer.getByTestId('messages-save-state'));
    },
  },
  {
    caption: {
      en: 'Gmail and other mailboxes connect today. Not ready yet: sending as the agency from a Microsoft 365 mailbox.',
      vi: 'Hiện đã kết nối được Gmail và các hộp thư khác. Chưa có: gửi thư với tư cách đại lý từ hộp thư Microsoft 365.',
    },
    run: async (page, h) => {
      await slide.notReady(page, h, {
        screen: 'Microsoft 365 mailbox',
        missing: ['Connecting a Microsoft 365 mailbox and sending as the agency from it (Gmail and SMTP mailboxes work today)'],
      });
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
