// CRM review R11 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): the traveller portal, per person.
// Given: R10 booked the invoice trip (2 adults) and copied the lead's portal link to work/crm/.secrets.json (r11_link).
// When:  the lead (C) opens it on a 390 x 844 phone, signs in with a one-time code (echoed on Dev, blurred), fills her
//        travel details (invented passport data), adds her arrival flight, uploads a SPECIMEN passport scan (a PDF made
//        here, marked as not a real document), signs the documents (terms, waiver, insurance choice) with a second
//        code, and invites the second traveller to his own portal at an @example.invalid address.
// Then:  portal home as lead; details done; flight saved in airport time; scan on file (never shown back); envelope
//        signed; the invite answered without showing a link. Offline use is not built: "Not ready yet" card.
// Writes: the lead's portal data on an invented trip; one companion invite to an address that never receives mail.
// Anonymous writes (code, session) >= 14 s apart; signed-in portal writes stay far under 30/min. No 429 asserted.
// A re-run skips what is done in --fast only. No LLM call. Cost $0.
const slide = require('../../lib/slide.cjs');
const { crm, st, base, sha, PHONE, type, choose, reuse } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-11', title: 'The traveller portal: details, flights, passport scan, signing and inviting', who: null, viewport: PHONE });
let s;
let t;
let seen429;

/** A one-page PDF that says SPECIMEN: an invented stand-in for a passport scan (never a real document). */
function specimenPdf(name) {
  const text = `SPECIMEN - invented passport scan for a CRM review. Not a real document. ${name}`.replace(/[()\\]/g, '');
  const objs = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 297] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
    null,
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
  ];
  const stream = `BT /F1 28 Tf 40 200 Td (SPECIMEN) Tj /F1 9 Tf 0 -40 Td (${text}) Tj ET`;
  objs[3] = `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`;
  let out = '%PDF-1.4\n';
  const offs = [];
  objs.forEach((o, i) => { offs.push(out.length); out += `${i + 1} 0 obj\n${o}\nendobj\n`; });
  const xref = out.length;
  out += `xref\n0 ${objs.length + 1}\n0000000000 65535 f \n${offs.map((o) => `${String(o).padStart(10, '0')} 00000 n \n`).join('')}`;
  out += `trailer\n<< /Size ${objs.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(out, 'latin1');
}

const portalPause = (h) => h.pause(2000); // signed-in portal writes: 30 per minute per address

sc.steps = [
  {
    caption: {
      en: 'The lead traveller opens her personal portal link on her phone and asks for a one-time sign-in code.',
      vi: 'Khách đứng tên mở đường dẫn cổng riêng trên điện thoại và xin một mã đăng nhập dùng một lần.',
    },
    run: async (page, h) => {
      s = st.load();
      t = s.invoice_trip;
      const link = st.loadSecrets().r11_link;
      if (!link || !s.r10 || s.r10.trip_id !== t.trip_id) throw new Error('no portal link of the booked R10 trip: run crm-rev-10 first');
      seen429 = crm.watch429(page);
      await sha(page, sc, 'start');
      await h.goto(link);
      await h.expect(page.getByTestId('portal-sign-in').or(page.getByTestId('portal-home'))).toBeVisible({ timeout: 20_000 });
      if (await page.getByTestId('portal-home').isVisible()) return reuse(h, 'a signed-in portal session');
      await crm.paceClientWrite();
      await h.click(page.getByTestId('portal-send-code'));
      await h.expect(page.getByTestId('portal-hint')).toBeVisible({ timeout: 20_000 });
    },
  },
  {
    caption: {
      en: 'The code goes to her e-mail; on this test system it also shows on the page, blurred here. She types it and is in.',
      vi: 'Mã được gửi vào e-mail của khách; trên hệ thống thử nghiệm này mã cũng hiện trên trang, ở đây đã được che. Khách nhập mã và vào cổng.',
    },
    run: async (page, h) => {
      if (!(await page.getByTestId('portal-home').isVisible())) {
        const code = await crm.echoedCode(page);
        await h.click(page.getByTestId('portal-code'));
        await page.getByTestId('portal-code').fill(code); // never typed slowly, never logged
        await crm.paceClientWrite();
        await h.click(page.getByTestId('portal-verify'));
        const pick = page.getByTestId('portal-pick-lead');
        await h.expect(pick.or(page.getByTestId('portal-home'))).toBeVisible({ timeout: 20_000 });
        if (await pick.isVisible()) await h.click(pick);
      }
      await h.expect(page.getByTestId('portal-home')).toHaveAttribute('data-role', 'lead', { timeout: 20_000 });
      await h.hover(page.getByTestId('portal-me'));
      crm.assertNo429(seen429);
    },
  },
  {
    caption: {
      en: 'First her travel details. The passport fields here are invented for this review.',
      vi: 'Đầu tiên là thông tin chuyến đi của khách. Các trường hộ chiếu ở đây đều là dữ liệu giả lập cho video này.',
    },
    run: async (page, h) => {
      const s3 = page.getByTestId('portal-stage3');
      await h.scrollTo(s3);
      await h.expect(s3).toHaveAttribute('data-locked', 'false');
      if ((await s3.getAttribute('data-done')) === 'true') return reuse(h, 'the travel details');
      const [given, family] = [t.lead_name.split(' ')[0], 'Lindqvist'];
      const fields = { given_name: given, family_name: family, dob: '1986-04-12', nationality: 'SE', passport_no: 'SPEC12345',
        passport_expiry: '2032-06-30', passport_country: 'SE', emergency_contact: 'Invented contact +46 70 000 0000' };
      for (const [k, v] of Object.entries(fields)) {
        const f = page.getByTestId(`portal-field-${k}`);
        if (await f.count()) await type(page, h, f, v);
      }
      await portalPause(h);
      await h.click(page.getByTestId('portal-stage3-save'));
      await h.expect(s3).toHaveAttribute('data-done', 'true', { timeout: 20_000 });
    },
  },
  {
    caption: {
      en: 'She adds her arrival flight. Times are kept in the airport\'s own time zone.',
      vi: 'Khách thêm chuyến bay đến. Giờ được lưu theo múi giờ của chính sân bay.',
    },
    run: async (page, h) => {
      const fl = page.getByTestId('portal-flights');
      await h.scrollTo(fl);
      if (await page.getByTestId('portal-flight-arrival-saved').count()) return reuse(h, 'the arrival flight');
      await type(page, h, page.getByTestId('portal-flight-arrival-no'), 'VN123');
      await type(page, h, page.getByTestId('portal-flight-arrival-airport'), 'DAD');
      await page.getByTestId('portal-flight-arrival-time').fill(`${t.start_date}T09:40`);
      await choose(h, page.getByTestId('portal-flight-arrival-tz'), 'Asia/Ho_Chi_Minh');
      await portalPause(h);
      await h.click(page.getByTestId('portal-flight-arrival-save'));
      await h.expect(page.getByTestId('portal-flight-arrival-saved')).toContainText('VN123', { timeout: 20_000 });
    },
  },
  {
    caption: {
      en: 'The passport scan is upload-only: once sent, it is never shown back on the page. This file is a specimen.',
      vi: 'Bản scan hộ chiếu chỉ tải lên: gửi xong thì không bao giờ hiện lại trên trang. File này là bản mẫu.',
    },
    run: async (page, h) => {
      const scan = page.getByTestId('portal-scan');
      await h.scrollTo(scan);
      if ((await scan.getAttribute('data-on-file')) === 'true') return reuse(h, 'the passport scan');
      await h.hover(page.getByTestId('portal-scan-file'));
      await page.getByTestId('portal-scan-file').setInputFiles({ name: 'SPECIMEN-passport.pdf', mimeType: 'application/pdf', buffer: specimenPdf(s.run) });
      await portalPause(h);
      await h.click(page.getByTestId('portal-scan-upload'));
      await h.expect(scan).toHaveAttribute('data-on-file', 'true', { timeout: 30_000 });
    },
  },
  {
    caption: {
      en: 'She signs the agency\'s documents in one go: booking terms, waiver and her insurance choice, confirmed with a second code.',
      vi: 'Khách ký các giấy tờ của đại lý một lần: điều khoản đặt chỗ, bản miễn trừ và lựa chọn bảo hiểm, xác nhận bằng mã thứ hai.',
    },
    run: async (page, h) => {
      const env = page.getByTestId('portal-waiver');
      await h.scrollTo(env);
      if ((await env.getAttribute('data-signed')) === 'true') return reuse(h, 'the signed envelope');
      await h.expect(env.getByTestId('portal-doc-booking_terms')).toBeVisible();
      await h.expect(env.getByTestId('portal-doc-waiver')).toBeVisible();
      if (await page.getByTestId('portal-insurance-insured').count()) await h.click(page.getByTestId('portal-insurance-insured'));
      await portalPause(h);
      await h.click(page.getByTestId('portal-sign-code'));
      const hint = page.getByTestId('portal-sign-hint');
      await h.expect(hint).toBeVisible({ timeout: 20_000 });
      const code = ((await hint.textContent()) || '').match(/\b(\d{6})\b/);
      if (!code) throw new Error('no echoed signing code (PORTAL_OTP_DEV_ECHO off?)');
      await h.click(page.getByTestId('portal-sign-agree'));
      await type(page, h, page.getByTestId('portal-sign-name'), t.lead_name);
      await page.getByTestId('portal-sign-code-input').fill(code[1]);
      await portalPause(h);
      await h.click(page.getByTestId('portal-sign'));
      await h.expect(env).toHaveAttribute('data-signed', 'true', { timeout: 20_000 });
      await h.expect(env.getByTestId('portal-signed')).toBeVisible();
    },
  },
  {
    caption: {
      en: 'The second traveller gets his own portal. She types his e-mail and the invitation goes to him, never through her.',
      vi: 'Người đi cùng có cổng riêng. Khách gõ e-mail của anh ấy và lời mời được gửi thẳng cho anh, không qua khách.',
    },
    run: async (page, h) => {
      const party = page.getByTestId('portal-party');
      await h.scrollTo(party);
      await h.expect(party.getByTestId('portal-party-member')).toHaveCount(2);
      const open = party.locator('[data-testid^="portal-invite-open-"]');
      if (!(await open.count())) return reuse(h, 'the companion invite');
      await h.click(open.first());
      const form = party.getByTestId('portal-invite-form');
      const email = form.getByTestId('portal-invite-email');
      if (await email.count()) await type(page, h, email, `erik.lindqvist.r11.${s.run}@example.invalid`);
      await portalPause(h);
      await h.click(form.getByTestId('portal-invite-send'));
      await h.expect(page.getByTestId('portal-note')).toBeVisible({ timeout: 20_000 });
      await h.expect(page.getByTestId('portal-note')).not.toContainText('/c/'); // no link shown to the lead
      crm.assertNo429(seen429);
    },
  },
  {
    caption: {
      en: 'Not ready yet: using the portal offline during the trip.',
      vi: 'Chưa có: dùng cổng khách khi không có mạng trong chuyến đi.',
    },
    run: async (page, h) => {
      await slide.notReady(page, h, {
        screen: 'Offline traveller portal',
        missing: ['Installing the portal on the phone and reading the trip, documents and contacts without a connection'],
      });
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
