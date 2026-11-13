// Pilot rehearsal step 10, second take (runbook docs/ops/runbooks/pilot-rehearsal.md, "Traveller portal"): the lead
// traveller signs in to her portal again and reads her itinerary and the voucher of the Adventure Asia tour. REH-10-portal
// recorded the first visit (sign-in, passport details, flight, e-sign); its itinerary step failed because the confirmed
// AA line was hidden from travellers and the proposal days had no content (fixed in AA-Partner #306/#307; REH-10a-show-
// aa-line shows the line). A recorded take never narrates a step whose work is already done, so the details, flight and
// signature are not repeated here.
// Given: REH-10-portal ran on the rehearsal trip (details, flight and signature saved); REH-10a-show-aa-line showed the
//        AA line; the lead's portal link is in work/rehearsal/.crm-secrets.json (r10_link).
// When:  she opens the link on a 390 x 844 phone, signs in with a one-time code (echoed on Dev, blurred), then reads the
//        itinerary and the voucher.
// Then:  portal home as lead; the itinerary lists the trip's days (tour X's days + the arrival day) with the tour's day
//        content and the confirmed AA line among the services; one voucher (or more) for the confirmed tour.
// Writes: POST traveller/code (1) and POST traveller/session (2: the code, the lead pick). The code is mailed to the lead,
// so the address check of the agency steps comes first (R.checkTraveller). No LLM call. Cost $0.
const R = require('./_reh.cjs');

const { step, crm } = R;
let s;
let seen429;

module.exports = R.scenario({
  id: 'REH-10c-itinerary',
  title: 'Rehearsal: the traveller reads her itinerary and the tour voucher',
  titleVi: 'Diễn tập: khách xem lịch trình và phiếu dịch vụ của tour',
  viewport: R.PHONE,
  allowWrites: R.clientWrites(['POST', 'traveller/(?:code|session)']),
  steps: [
    step('The lead traveller opens her portal link on her phone again and asks for a one-time sign-in code.',
      'Khách đứng tên mở lại đường dẫn cổng riêng trên điện thoại và xin một mã đăng nhập dùng một lần.',
      async (page, h) => {
        module.exports.meta.writes = await R.cap(page, [
          ['code', 'POST', R.clientPath('traveller/code'), 1],
          ['session', 'POST', R.clientPath('traveller/session'), 2],
        ]);
        s = R.need(R.load(), ['trip_id', 'lead_name', 'trip_days', 'aa_line', 'r08c_done_at'], 'REH-08c-aa-confirmed');
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
    step('She types the code, blurred here, and is in.',
      'Khách nhập mã, ở đây đã được che, và vào cổng.',
      async (page, h) => {
        const code = await crm.echoedCode(page);
        await h.click(page.getByTestId('portal-code'));
        await page.getByTestId('portal-code').fill(code); // never typed slowly, never logged
        await h.assertMasked(['[data-testid="portal-hint"]', '[data-testid="portal-code"]']);
        await crm.paceClientWrite();
        await h.click(page.getByTestId('portal-verify'));
        const pick = page.getByTestId('portal-pick-lead');
        await h.expect(pick.or(page.getByTestId('portal-home'))).toBeVisible({ timeout: 20_000 });
        if (await pick.isVisible()) await h.click(pick);
        await h.expect(page.getByTestId('portal-home')).toHaveAttribute('data-role', 'lead', { timeout: 20_000 });
        await h.hover(page.getByTestId('portal-me'));
      }, { writes: true }),
    step('Her itinerary lists the trip day by day, with the Adventure Asia tour\'s days and the tour among her services.',
      'Lịch trình của khách liệt kê chuyến đi theo từng ngày, có các ngày của tour Adventure Asia và tour nằm trong danh sách dịch vụ.',
      async (page, h) => {
        const day1 = page.getByTestId('portal-day-1');
        await h.scrollTo(day1);
        await h.expect(day1).toBeVisible({ timeout: 20_000 });
        const days = page.locator('[data-testid^="portal-day-"]:not([data-testid="portal-day-0"])');
        await h.expect(days).toHaveCount(s.trip_days);
        // The tour's days carry their own content (a title or a place after the date), not the date alone.
        const texts = await days.allInnerTexts();
        module.exports.meta.days_with_content = texts.filter((t) => t.split('·').length > 2).length;
        if (!module.exports.meta.days_with_content) throw new Error('no itinerary day carries a title or a place');
        const services = page.getByTestId('portal-services');
        await h.scrollTo(services);
        await h.expect(services).toBeVisible();
        if (s.aa_line.title) await h.expect(services).toContainText(s.aa_line.title);
        await h.hover(page.getByTestId('portal-day-2'));
      }),
    step('The voucher of the confirmed tour is there to show on the day, or to print. This is the end of the scenario.',
      'Phiếu dịch vụ của tour đã xác nhận có sẵn để xuất trình hôm đi, hoặc in ra. Kết thúc kịch bản.',
      async (page, h) => {
        const box = page.getByTestId('portal-vouchers');
        await h.scrollTo(box);
        const v = box.getByTestId('portal-voucher');
        await h.expect(v.first()).toBeVisible({ timeout: 20_000 });
        if (s.aa_line.title) await h.expect(v.filter({ hasText: s.aa_line.title })).toHaveCount(1);
        await h.expect(v.first().getByTestId('portal-voucher-head')).toBeVisible();
        await h.hover(v.first());
        crm.assertNo429(seen429);
        await R.sha(page, module.exports, 'end');
      }),
  ],
});
