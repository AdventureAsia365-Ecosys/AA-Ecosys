// CRM review R09 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): contracts and e-sign.
// Given: A (owner) signed in; the R03 trip's version accepted in R08 (client link in work/crm/.secrets.json r08_link).
// When:  the owner reads Settings > Agreements (booking terms, waiver, insurance declination), saves and publishes new
//        booking terms "<run>-<n>" (rv<yyyymmdd><n>-<n>); the trip then asks the client to re-accept; the client (C, same browser, client
//        host) reads the new version, ticks it and types her name; the owner sees the trip clear again and the signing
//        panel per traveller (the waiver envelope is signed in the traveller portal after the deposit, R11).
// Then:  the new version is published; the trip shows the re-accept warning, then not; the client's re-accept is
//        answered without a 429. The signed PDF (PAdES) is not built: "Not ready yet" card.
// Writes: one booking-terms version per run (invented text; it also asks R10's client to re-accept, which R10 shows)
// and one client re-accept. No LLM call. Cost $0.
const slide = require('../../lib/slide.cjs');
const { crm, st, base, sha, open, bffOk, type, choose } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-09', title: 'Contracts: new booking terms, re-accept and e-sign' });
let s;
let label;
let seen429;

sc.steps = [
  {
    caption: {
      en: 'Settings, Agreements holds the agency\'s own documents: booking terms, a waiver and an insurance declination, each versioned.',
      vi: 'Trong Settings, mục Agreements chứa giấy tờ riêng của đại lý: điều khoản đặt chỗ, bản miễn trừ và bản từ chối bảo hiểm, mỗi loại có phiên bản.',
    },
    run: async (page, h) => {
      s = st.load();
      if (!s.r08 || !st.loadSecrets().r08_link) throw new Error('no accepted R08 version: run crm-rev-08 first');
      seen429 = crm.watch429(page);
      await sha(page, sc, 'start');
      await open(page, h, '/settings/agreements', 'agreements-view');
      await h.expect(page.getByTestId('agreements-view')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
      for (const kind of ['booking_terms', 'waiver']) {
        await h.expect(page.locator(`[data-testid="agreement-row"][data-kind="${kind}"][data-status="published"]`).first()).toBeVisible({ timeout: 15_000 });
      }
      await h.hover(page.locator('[data-testid="agreement-row"][data-kind="booking_terms"][data-status="published"]').first());
    },
  },
  {
    caption: {
      en: 'The owner writes a new version of the booking terms and saves it as a draft.',
      vi: 'Chủ đại lý viết phiên bản mới của điều khoản đặt chỗ và lưu nháp.',
    },
    run: async (page, h) => {
      const rows = await page.locator('[data-testid="agreement-row"][data-kind="booking_terms"]').allInnerTexts();
      let n = 1;
      while (rows.some((r) => r.includes(`${s.run}-${n}`))) n += 1;
      label = `${s.run}-${n}`; // rv<yyyymmdd><run>-<n>
      const form = page.getByTestId('agreement-form');
      await h.scrollTo(form);
      await choose(h, form.locator('select[name="kind"]'), 'booking_terms');
      await type(page, h, form.locator('input[name="version_label"]'), label);
      await type(page, h, form.locator('textarea[name="body_text"]'), 'Deposit 30% on acceptance; balance 14 days before departure. Free changes until 30 days before. Invented terms for the CRM review.');
      await h.click(form.getByRole('button', { name: /save draft/i }));
      const row = page.locator('[data-testid="agreement-row"][data-kind="booking_terms"]').filter({ hasText: label });
      await h.expect(row).toHaveAttribute('data-status', 'draft', { timeout: 15_000 });
      s.r09 = { label };
      st.save(s);
    },
  },
  {
    caption: {
      en: 'Publishing it is a real decision: every client who accepted the old terms must accept the new ones before paying.',
      vi: 'Phát hành là một quyết định thật: mọi khách đã chấp nhận điều khoản cũ phải chấp nhận bản mới trước khi thanh toán.',
    },
    run: async (page, h) => {
      const row = page.locator('[data-testid="agreement-row"][data-kind="booking_terms"]').filter({ hasText: label });
      await h.scrollTo(row);
      await h.click(row.getByRole('button', { name: /publish/i }));
      await h.expect(row).toHaveAttribute('data-status', 'published', { timeout: 15_000 });
    },
  },
  {
    caption: {
      en: 'On the trip from this morning, the signing panel now warns that the client has to accept the new terms.',
      vi: 'Trên chuyến lúc sáng, bảng chữ ký giờ báo khách phải chấp nhận điều khoản mới.',
    },
    run: async (page, h) => {
      await open(page, h, `/pipeline/${s.r08.trip_id}`, 'crm-trip');
      const panel = page.getByTestId('trip-agreements');
      await h.scrollTo(panel);
      await h.expect(panel.getByTestId('esign-reaccept')).toBeVisible({ timeout: 15_000 });
      await h.hover(panel.getByTestId('esign-reaccept'));
    },
  },
  {
    caption: {
      en: 'The client opens her link again. Above the payment box she reads the new version, ticks it and types her name.',
      vi: 'Khách mở lại đường dẫn của mình. Phía trên ô thanh toán, khách đọc bản mới, đánh dấu đồng ý và gõ tên.',
    },
    run: async (page, h) => {
      await h.goto(st.loadSecrets().r08_link);
      await page.waitForURL(`${crm.CLIENT}/c/p`, { timeout: 20_000 });
      const box = page.getByTestId('client-terms-reaccept');
      await h.expect(box).toBeVisible({ timeout: 20_000 });
      await h.expect(box).toContainText(label);
      await h.scrollTo(box);
      await h.click(box.getByTestId('client-reaccept-agree'));
      await type(page, h, box.getByTestId('client-reaccept-name'), s.r03.lead_name);
    },
  },
  {
    caption: {
      en: 'She confirms. The new terms are accepted and recorded with the exact text she saw.',
      vi: 'Khách xác nhận. Điều khoản mới được chấp nhận và lưu kèm đúng văn bản khách đã đọc.',
    },
    run: async (page, h) => {
      await crm.paceClientWrite();
      const answer = page.waitForResponse((r) => r.request().method() === 'POST' && /\/crm\/public\/v1\/proposal\/.*terms/.test(new URL(r.url()).pathname), { timeout: 30_000 });
      await h.click(page.getByTestId('client-reaccept'));
      const res = await answer;
      h.expect(res.status()).toBeLessThan(300);
      await h.expect(page.getByTestId('client-terms-reaccept')).toHaveCount(0, { timeout: 20_000 });
      crm.assertNo429(seen429);
    },
  },
  {
    caption: {
      en: 'Back at the agency the warning is gone. The panel also lists each traveller\'s signature: the waiver is signed in the traveller portal after the deposit.',
      vi: 'Quay lại đại lý, cảnh báo đã hết. Bảng cũng liệt kê chữ ký của từng khách: bản miễn trừ được ký trong cổng khách sau khi đặt cọc.',
    },
    run: async (page, h) => {
      await open(page, h, `/pipeline/${s.r08.trip_id}`, 'crm-trip');
      const panel = page.getByTestId('trip-agreements');
      await h.scrollTo(panel);
      await h.expect(panel.getByTestId('esign-reaccept')).toHaveCount(0, { timeout: 15_000 });
      await h.expect(panel.getByTestId('esign-row').first()).toHaveAttribute('data-signed', 'false');
      await h.hover(panel.getByTestId('esign-row').first());
      const terms = await bffOk(page, 'GET', 'agreements');
      h.expect((terms.agreements || []).some((d) => d.kind === 'booking_terms' && d.status === 'published' && d.version_label === label)).toBe(true);
    },
  },
  {
    caption: {
      en: 'Not ready yet: a signed PDF of the documents with a standard digital signature.',
      vi: 'Chưa có: bản PDF đã ký của các giấy tờ, với chữ ký số theo chuẩn.',
    },
    run: async (page, h) => {
      await slide.notReady(page, h, {
        screen: 'Signed PDF of the agreements',
        missing: ['A PDF of the signed documents, sealed with a standard (PAdES) digital signature, to download and keep'],
        foot: 'Today each signature is kept as a sealed record with the exact text, the time and the one-time code check.',
      });
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
