// Pilot rehearsal step 10 (runbook docs/ops/runbooks/pilot-rehearsal.md, "Traveller portal"): the lead traveller's
// portal on her phone at go-dev.lumiguides.it.com/c/t.
// Given: REH-08c-aa-confirmed: the trip is booked, tour X confirmed by Adventure Asia, and the lead's portal link is in
//        work/rehearsal/.crm-secrets.json (r10_link). The run signs the owner in (crm-rehearsal) only for the pilot
//        guard; the traveller has no account and the client host gets none of the agency host's cookies. The agency
//        published booking terms and a waiver (REH-02b-agency-setup; scenarios/crm/REHEARSAL.md): without a published
//        waiver the portal builds no signing envelope (portal/public.py WAIVER_SQL) and step 5 fails.
// When:  she opens the link on a 390 x 844 phone, signs in with a one-time code (echoed on Dev, blurred), fills her
//        passport details (invented), adds her arrival flight, signs the agency's documents with a second code, then
//        reads her day-by-day itinerary and the voucher of the Adventure Asia tour.
// Then:  portal home as lead; details done; flight saved in airport time; envelope signed; the itinerary lists the
//        trip's days (tour X's days + the arrival day, the same count as the builder) and the confirmed AA line; one
//        voucher (or more) for the confirmed tour, released once the trip is booked and the line confirmed. The AA ops
//        side of the same trip (the release AA ground operations read) is REH-10b-ops-view.
// Writes (method and path allowed, each capped): POST traveller/code (2: sign-in, signing), POST traveller/session (2:
// the code, the lead pick), PUT traveller/stage3 (1), PUT traveller/flights (1), POST traveller/sign (1): the lead's
// portal data on the rehearsal trip. Mail: both codes are mailed to the lead, so steps 1 and 5 first require the
// address check of the agency steps for this trip (R.checkTraveller). Anonymous writes (code, session) >= 14 s apart
// (crm.paceClientWrite, for the registry's crm.rate.intake_per_minute of 5); signed-in portal writes stay far under
// the per-minute limit. Masks: hint, code boxes and signing code asserted
// blurred. No LLM call. Cost $0.
const R = require('./_reh.cjs');

const { step, crm } = R;
let s;
let seen429;
const portalPause = (h) => h.pause(2000);

module.exports = R.scenario({
  id: 'REH-10-portal',
  title: 'Rehearsal: the traveller portal, from sign-in to the voucher',
  titleVi: 'Diễn tập: cổng khách, từ đăng nhập tới phiếu dịch vụ',
  viewport: R.PHONE,
  allowWrites: R.clientWrites(['POST', 'traveller/(?:code|session|sign)'], ['PUT', 'traveller/(?:stage3|flights)']),
  steps: [
    step('The lead traveller opens her personal portal link on her phone and asks for a one-time sign-in code.',
      'Khách đứng tên mở đường dẫn cổng riêng trên điện thoại và xin một mã đăng nhập dùng một lần.',
      async (page, h) => {
        module.exports.meta.writes = await R.cap(page, [
          ['code', 'POST', R.clientPath('traveller/code'), 2],
          ['session', 'POST', R.clientPath('traveller/session'), 2],
          ['stage3', 'PUT', R.clientPath('traveller/stage3'), 1],
          ['flights', 'PUT', R.clientPath('traveller/flights'), 1],
          ['sign', 'POST', R.clientPath('traveller/sign'), 1],
        ]);
        s = R.need(R.load(), ['trip_id', 'lead_name', 'start_date', 'trip_days', 'aa_line', 'r08c_done_at'], 'REH-08c-aa-confirmed');
        const link = R.link('r10_link', s.trip_id);
        if (!link) throw new Error('no portal link of the rehearsal trip: run REH-08c-aa-confirmed first');
        seen429 = crm.watch429(page);
        await R.sha(page, module.exports, 'start');
        await h.goto(link);
        await h.expect(page.getByTestId('portal-sign-in').or(page.getByTestId('portal-home'))).toBeVisible({ timeout: 20_000 });
        if (await page.getByTestId('portal-home').isVisible()) return R.reuse(h, 'a signed-in portal session');
        await R.checkTraveller(page, s); // mail guard: the sign-in code is mailed to the lead
        await crm.paceClientWrite();
        await h.click(page.getByTestId('portal-send-code'));
        await h.expect(page.getByTestId('portal-hint')).toBeVisible({ timeout: 20_000 });
        await h.assertMasked(['[data-testid="portal-hint"]']);
      }, { writes: true }),
    step('The code goes to her e-mail; on this test system it also shows on the page, blurred here. She types it and is in.',
      'Mã được gửi vào e-mail của khách; trên hệ thống thử nghiệm này mã cũng hiện trên trang, ở đây đã được che. Khách nhập mã và vào cổng.',
      async (page, h) => {
        if (!(await page.getByTestId('portal-home').isVisible())) {
          const code = await crm.echoedCode(page);
          await h.click(page.getByTestId('portal-code'));
          await page.getByTestId('portal-code').fill(code); // never typed slowly, never logged
          await h.assertMasked(['[data-testid="portal-hint"]', '[data-testid="portal-code"]']);
          await crm.paceClientWrite();
          await h.click(page.getByTestId('portal-verify'));
          const pick = page.getByTestId('portal-pick-lead');
          await h.expect(pick.or(page.getByTestId('portal-home'))).toBeVisible({ timeout: 20_000 });
          if (await pick.isVisible()) await h.click(pick);
        }
        await h.expect(page.getByTestId('portal-home')).toHaveAttribute('data-role', 'lead', { timeout: 20_000 });
        await h.hover(page.getByTestId('portal-me'));
        crm.assertNo429(seen429);
      }, { writes: true }),
    step('First her passport details. Every value here is invented for the rehearsal.',
      'Đầu tiên là thông tin hộ chiếu. Mọi giá trị ở đây đều là dữ liệu giả lập cho buổi diễn tập.',
      async (page, h) => {
        const s3 = page.getByTestId('portal-stage3');
        await h.scrollTo(s3);
        await h.expect(s3).toHaveAttribute('data-locked', 'false');
        if ((await s3.getAttribute('data-done')) === 'true') return R.reuse(h, 'the travel details');
        const [given, ...rest] = s.lead_name.split(' ');
        const fields = { given_name: given, family_name: rest[0] || 'Rehearsal', dob: '1988-03-21', nationality: 'NL', passport_no: 'SPEC67890',
          passport_expiry: '2033-01-31', passport_country: 'NL', emergency_contact: 'Invented contact +31 6 0000 0000' };
        for (const [k, v] of Object.entries(fields)) {
          const f = page.getByTestId(`portal-field-${k}`);
          if (await f.count()) await R.type(page, h, f, v);
        }
        await portalPause(h);
        await h.click(page.getByTestId('portal-stage3-save'));
        await h.expect(s3).toHaveAttribute('data-done', 'true', { timeout: 20_000 });
      }, { writes: true }),
    step('She adds her arrival flight. Times are kept in the airport\'s own time zone.',
      'Khách thêm chuyến bay đến. Giờ được lưu theo múi giờ của chính sân bay.',
      async (page, h) => {
        const fl = page.getByTestId('portal-flights');
        await h.scrollTo(fl);
        if (await page.getByTestId('portal-flight-arrival-saved').count()) return R.reuse(h, 'the arrival flight');
        await R.type(page, h, page.getByTestId('portal-flight-arrival-no'), 'VN321');
        await R.type(page, h, page.getByTestId('portal-flight-arrival-airport'), 'HAN');
        await page.getByTestId('portal-flight-arrival-time').fill(`${s.start_date}T10:15`);
        await R.choose(h, page.getByTestId('portal-flight-arrival-tz'), 'Asia/Ho_Chi_Minh');
        await portalPause(h);
        await h.click(page.getByTestId('portal-flight-arrival-save'));
        await h.expect(page.getByTestId('portal-flight-arrival-saved')).toContainText('VN321', { timeout: 20_000 });
      }, { writes: true }),
    step('She signs the agency\'s documents in one go, confirmed with a second code.',
      'Khách ký các giấy tờ của đại lý một lần, xác nhận bằng mã thứ hai.',
      async (page, h) => {
        const env = page.getByTestId('portal-waiver');
        await h.scrollTo(env);
        if ((await env.getAttribute('data-signed')) === 'true') return R.reuse(h, 'the signed envelope');
        await h.expect(env.getByTestId('portal-doc-booking_terms')).toBeVisible();
        if (await page.getByTestId('portal-insurance-insured').count()) await h.click(page.getByTestId('portal-insurance-insured'));
        await portalPause(h);
        await R.checkTraveller(page, s); // mail guard: the signing code is mailed to the lead
        await h.click(page.getByTestId('portal-sign-code'));
        const hint = page.getByTestId('portal-sign-hint');
        await h.expect(hint).toBeVisible({ timeout: 20_000 });
        const code = ((await hint.textContent()) || '').match(/\b(\d{6})\b/);
        if (!code) throw new Error('no echoed signing code (PORTAL_OTP_DEV_ECHO off?)');
        await h.click(page.getByTestId('portal-sign-agree'));
        await R.type(page, h, page.getByTestId('portal-sign-name'), s.lead_name);
        await page.getByTestId('portal-sign-code-input').fill(code[1]);
        await h.assertMasked(['[data-testid="portal-sign-hint"]', '[data-testid="portal-sign-code-input"]']);
        await portalPause(h);
        await h.click(page.getByTestId('portal-sign'));
        await h.expect(env).toHaveAttribute('data-signed', 'true', { timeout: 20_000 });
        await h.expect(env.getByTestId('portal-signed')).toBeVisible();
      }, { writes: true }),
    step('Her itinerary lists the trip day by day, the Adventure Asia tour included.',
      'Lịch trình của khách liệt kê chuyến đi theo từng ngày, có cả tour Adventure Asia.',
      async (page, h) => {
        const day1 = page.getByTestId('portal-day-1');
        await h.scrollTo(day1);
        await h.expect(day1).toBeVisible({ timeout: 20_000 });
        // Same tour at every stage: the trip's days (tour X's days + the arrival day), no more, no fewer.
        const days = page.locator('[data-testid^="portal-day-"]:not([data-testid="portal-day-0"])');
        await h.expect(days).toHaveCount(s.trip_days);
        await h.expect(page.getByTestId(`portal-day-${s.trip_days}`)).toBeVisible();
        // The confirmed Adventure Asia line is among the trip's services.
        const services = page.getByTestId('portal-services');
        await h.expect(services).toBeVisible();
        if (s.aa_line.title) await h.expect(services).toContainText(s.aa_line.title);
        await h.hover(page.getByTestId('portal-day-2'));
      }),
    step('The voucher of the confirmed tour is there to show on the day, or to print.',
      'Phiếu dịch vụ của tour đã xác nhận có sẵn để xuất trình hôm đi, hoặc in ra.',
      async (page, h) => {
        const box = page.getByTestId('portal-vouchers');
        await h.scrollTo(box);
        const v = box.getByTestId('portal-voucher');
        await h.expect(v.first()).toBeVisible({ timeout: 20_000 });
        if (s.aa_line.title) await h.expect(v.filter({ hasText: s.aa_line.title })).toHaveCount(1);
        await h.expect(v.first().getByTestId('portal-voucher-head')).toBeVisible();
        await h.hover(v.first());
        crm.assertNo429(seen429);
        R.save({ r10_done_at: new Date().toISOString() });
        await R.sha(page, module.exports, 'end');
      }),
  ],
});
