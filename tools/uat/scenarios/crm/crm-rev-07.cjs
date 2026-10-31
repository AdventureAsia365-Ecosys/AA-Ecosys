// CRM review R07 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): the written (text) proposal and the
// "Before you go" day.
// Given: A (owner) signed in; prep made the side trip at Proposal with a builder draft (agency hotel + an AA tour, a
//        balance date) in work/crm/state.json (side_trip).
// When:  the owner opens the draft, reads the Before you go day (the visa and insurance reminders; AA preparation
//        packs per country, none published for the Philippines yet), publishes version 1, then opens its text form:
//        e-mail in English, the same text in Vietnamese, then the WhatsApp form.
// Then:  day 0 is Before you go; the reminders show; the version is published; the text carries the version's price
//        reference and changes with the language. Nothing is sent (no e-mail, no WhatsApp hand-over).
// Writes on the invented side trip only (publish). A re-run skips what exists in --fast only; a recorded
// take on an already published version stops (prep with UAT_CRM_NEW_RUN=1). No LLM call. Cost $0.
const { st, base, sha, open, bffOk, choose, reuse } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-07', title: 'A written proposal and the Before you go day', titleVi: 'Đề xuất dạng chữ và ngày Before you go' });
let s;
let t;
let enBody;

sc.steps = [
  {
    caption: {
      en: 'Another trip, at the proposal stage. The owner opens its draft; the first entry is day zero, Before you go.',
      vi: 'Một chuyến khác đang ở giai đoạn đề xuất. Chủ đại lý mở bản nháp; mục đầu tiên là ngày số không, Before you go.',
    },
    run: async (page, h) => {
      s = st.load();
      t = s.side_trip;
      if (!t || !t.proposal_id) throw new Error('no side trip draft: run scenarios/crm/prep.cjs --fast first');
      await sha(page, sc, 'start');
      await open(page, h, `/pipeline/${t.trip_id}/proposal/${t.proposal_id}`, 'builder');
      await h.expect(page.getByTestId('builder')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
      const day0 = page.locator('[data-testid="builder-day"][data-day-no="0"]');
      await h.expect(day0).toHaveCount(1);
      await h.click(day0);
      await h.expect(page.getByTestId('builder-before-you-go')).toBeVisible({ timeout: 15_000 });
    },
  },
  {
    caption: {
      en: 'Before you go always carries the visa link and the travel insurance reminder. Adventure Asia\'s preparation packs show here per country once published; the Philippines has none yet.',
      vi: 'Before you go luôn có link visa và lời nhắc bảo hiểm du lịch. Gói chuẩn bị của Adventure Asia hiện ở đây theo từng quốc gia khi đã được phát hành; Philippines hiện chưa có gói nào.',
    },
    run: async (page, h) => {
      const byg = page.getByTestId('builder-before-you-go');
      await h.scrollTo(byg);
      await h.expect(byg.getByTestId('byg-reminders')).toBeVisible();
      await h.expect(byg.getByTestId('byg-reminders').locator('li')).toHaveCount(2); // visa + insurance (no trek)
      // The caption says "none yet": if packs appear for this country, the caption must change with them.
      await h.expect(byg.getByTestId('byg-none')).toContainText('PH');
      await h.hover(byg.getByTestId('byg-reminders'));
    },
  },
  {
    caption: {
      en: 'The owner publishes version one, so it can go to the client.',
      vi: 'Chủ đại lý phát hành phiên bản một để có thể gửi cho khách.',
    },
    run: async (page, h) => {
      const builder = page.getByTestId('builder');
      if ((await builder.getAttribute('data-status')) !== 'draft') {
        reuse(h, 'the published version', 'prep with UAT_CRM_NEW_RUN=1');
      } else {
        const publish = page.getByTestId('builder-header').getByRole('button', { name: /^Publish v\d+$/ });
        await h.scrollTo(publish);
        await h.expect(publish).toBeEnabled({ timeout: 15_000 });
        await h.click(publish);
      }
      await h.expect(builder).toHaveAttribute('data-status', /^(published|sent|accepted)$/, { timeout: 20_000 });
    },
  },
  {
    caption: {
      en: 'Besides the interactive page, any version can go out as plain text. The owner opens the e-mail text.',
      vi: 'Ngoài trang tương tác, phiên bản nào cũng gửi được dưới dạng văn bản. Chủ đại lý mở bản e-mail.',
    },
    run: async (page, h) => {
      const link = page.getByTestId('builder-send-text');
      await h.scrollTo(link);
      await h.click(link);
      await page.waitForURL(/\/text$/, { timeout: 20_000 });
      await h.expect(page.getByTestId('text-proposal')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
      await h.expect(page.locator('input[name="text-format"][value="email"]')).toBeChecked();
      await h.expect(page.getByTestId('text-subject')).toBeVisible();
      enBody = (await page.getByTestId('text-body').innerText()).trim();
      h.expect(enBody.length).toBeGreaterThan(80);
      await h.hover(page.getByTestId('text-body'));
    },
  },
  {
    caption: {
      en: 'The text is written from this exact version and carries its price reference, so the client and the agency talk about the same prices.',
      vi: 'Văn bản được tạo từ đúng phiên bản này và mang mã tham chiếu giá, để khách và đại lý nói về cùng một mức giá.',
    },
    run: async (page, h) => {
      const ref = page.getByTestId('text-reference');
      await h.expect(ref).toContainText(/\S{6,}/);
      await h.hover(ref);
      await h.scrollTo(page.getByTestId('text-body'));
    },
  },
  {
    caption: {
      en: 'The same text in Vietnamese, for a client who prefers it.',
      vi: 'Cùng văn bản đó bằng tiếng Việt, cho khách muốn đọc tiếng Việt.',
    },
    run: async (page, h) => {
      const loaded = page.waitForResponse((r) => /\/text$/.test(new URL(r.url()).pathname.replace(/\/bff/, '')) || /\/text\?/.test(r.url()), { timeout: 30_000 });
      await choose(h, page.getByTestId('text-locale'), 'vi');
      h.expect((await loaded).status()).toBe(200);
      await h.expect.poll(async () => (await page.getByTestId('text-body').innerText()).trim(), { timeout: 15_000 }).not.toBe(enBody);
      await h.hover(page.getByTestId('text-body'));
    },
  },
  {
    caption: {
      en: 'For WhatsApp the agency gets the final text to paste; e-mail goes out from the agency\'s own mailbox. Nothing is sent from this screen.',
      vi: 'Với WhatsApp, đại lý nhận văn bản cuối để dán; e-mail được gửi từ hộp thư của chính đại lý. Ở màn hình này không gửi gì cả.',
    },
    run: async (page, h) => {
      const wa = page.locator('input[name="text-format"][value="whatsapp"]');
      await h.click(wa);
      await h.expect(wa).toBeChecked({ timeout: 15_000 });
      await h.expect(page.getByTestId('text-subject')).toHaveCount(0, { timeout: 15_000 });
      const send = page.getByTestId('text-send').getByRole('button');
      await h.expect(send).toBeEnabled();
      await h.hover(send); // never clicked: no hand-over, no link issued
      await h.expect(page.getByTestId('text-sent')).toHaveCount(0);
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
