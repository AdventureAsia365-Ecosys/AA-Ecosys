// Pilot rehearsal step 8, part 1 (runbook docs/ops/runbooks/pilot-rehearsal.md, "The client accepts"): the traveller
// accepts the quote on her phone at go-dev.lumiguides.it.com/c/p.
// Given: REH-07b-approve sent version 1; its client link sits in work/rehearsal/.crm-secrets.json (r08_link, with the
//        trip id). The run signs the owner in (crm-rehearsal) only for the pilot guard; the traveller has no account and
//        the client host gets none of the agency host's cookies.
// When:  the traveller opens the link on a 390 x 844 phone, reads Before you go, the days with tour X on day 2, what is
//        included and the discount; asks Adventure Asia to hold the seats; confirms the rooms, agrees to the booking
//        terms, types her name and accepts.
// Then:  the link leaves the address bar (cookie); the hold box turns active with a "held until"; the page shows the
//        acceptance; no 429 on the client host (two anonymous writes, >= 14 s apart).
// Writes: one client hold on Booking (the party on tour X's departure) and the acceptance, on the rehearsal trip only.
// No LLM call. Cost $0.
const R = require('./_reh.cjs');

const { step, crm } = R;
let s;
let seen429;
let accepted = false;

module.exports = R.scenario({
  id: 'REH-08-accept',
  title: 'Rehearsal: the client accepts the quote on her phone',
  titleVi: 'Diễn tập: khách chấp nhận báo giá trên điện thoại',
  viewport: R.PHONE,
  allowWrites: R.clientWrites('proposal'),
  steps: [
    step('The client opens the agency\'s link on her phone. The page swaps the link for a private cookie, so it never stays in the address bar.',
      'Khách mở đường dẫn của đại lý trên điện thoại. Trang đổi đường dẫn thành một cookie riêng, nên nó không nằm lại trên thanh địa chỉ.',
      async (page, h) => {
        s = R.need(R.load(), ['trip_id', 'proposal_id', 'lead_name', 'r07b_done_at'], 'REH-07b-approve');
        const link = R.link('r08_link', s.trip_id);
        if (!link) throw new Error('no client link of the rehearsal trip: run REH-07b-approve first');
        seen429 = crm.watch429(page);
        await R.sha(page, module.exports, 'start');
        await h.goto(link);
        await page.waitForURL(`${crm.CLIENT}/c/p`, { timeout: 20_000 });
        const cp = page.getByTestId('client-proposal');
        await h.expect(cp).toHaveAttribute('data-kind', 'builder', { timeout: 20_000 });
        accepted = (await cp.getAttribute('data-status')) === 'accepted';
        if (accepted) R.reuse(h, 'the acceptance of this version', 'run REH-06-lead to REH-07b-approve on a new planner lead');
      }),
    step('It opens with Before you go. Then come the days; day two holds the Adventure Asia tour on its fixed departure.',
      'Trang mở đầu bằng Before you go. Sau đó là từng ngày; ngày thứ hai có tour Adventure Asia theo ngày khởi hành cố định.',
      async (page, h) => {
        await h.expect(page.getByTestId('client-day').first()).toHaveAttribute('data-day', '0');
        await h.expect(page.getByTestId('client-before-you-go')).toBeVisible();
        const tour = page.getByTestId('client-block').filter({ hasText: 'Adventure Asia tour' });
        await h.scrollTo(tour);
        await h.expect(tour.getByTestId('client-option')).toHaveCount(1);
        const width = await page.evaluate(() => document.documentElement.scrollWidth);
        h.expect(width, 'no sideways scroll at 390 px').toBeLessThanOrEqual(R.PHONE.width);
      }),
    step('She reads what the price includes and what it does not, and sees the agency\'s discount on the total.',
      'Khách đọc giá đã gồm gì, chưa gồm gì, và thấy mức giảm giá của đại lý trên tổng tiền.',
      async (page, h) => {
        const incl = page.getByTestId('client-inclusions');
        await h.scrollTo(incl);
        await h.expect(incl).toContainText('Airport pick-up on arrival');
        await h.expect(incl).toContainText('International flights');
        await h.scrollTo(page.getByTestId('client-total'));
        await h.expect(page.getByTestId('client-discount')).toBeVisible();
        await h.expect(page.getByTestId('client-total')).toContainText(/\d/);
      }),
    step('Before accepting, she checks the seats. Adventure Asia holds them for her for a short time.',
      'Trước khi chấp nhận, khách kiểm tra chỗ. Adventure Asia giữ chỗ cho khách trong một thời gian ngắn.',
      async (page, h) => {
        if (accepted) return;
        const box = page.getByTestId('client-hold');
        await h.scrollTo(box);
        if ((await box.getAttribute('data-status')) !== 'active') {
          await h.expect(box).toHaveAttribute('data-status', 'missing');
          await crm.paceClientWrite();
          await h.click(page.getByTestId('client-hold-button'));
        }
        const err = page.getByTestId('client-error');
        await h.expect(box.locator('xpath=self::*[@data-status="active"]').or(err)).toBeVisible({ timeout: 60_000 });
        if (await err.isVisible()) throw new Error(`the hold was refused: ${((await err.textContent()) || '').trim()}`);
        await h.expect(page.getByTestId('client-held-until')).toBeVisible();
        crm.assertNo429(seen429);
      }, { writes: true }),
    step('She confirms the rooms, agrees to the agency\'s booking terms and types her full name.',
      'Khách xác nhận phòng, đồng ý với điều khoản đặt chỗ của đại lý và gõ họ tên đầy đủ.',
      async (page, h) => {
        if (accepted) return;
        const form = page.getByTestId('client-accept-form');
        await h.scrollTo(form);
        await h.expect(form.getByTestId('client-groups')).toBeVisible();
        await h.click(form.getByTestId('client-rooms').locator('input'));
        await h.click(form.locator('input[name="accept_terms"]'));
        await h.expect(form.locator('input[name="accept_terms"]')).toBeChecked();
        await R.type(page, h, form.locator('input[name="full_name"]'), s.lead_name);
      }),
    step('She accepts. The agency is told at once; the next step is the deposit.',
      'Khách bấm chấp nhận. Đại lý được báo ngay; bước tiếp theo là tiền đặt cọc.',
      async (page, h) => {
        if (!accepted) {
          await crm.paceClientWrite();
          await h.click(page.getByTestId('client-accept'));
        }
        await h.expect(page.getByTestId('client-accepted')).toBeVisible({ timeout: 20_000 });
        await h.scrollTo(page.getByTestId('client-accepted'));
        crm.assertNo429(seen429);
        R.save({ accepted_at: s.accepted_at || new Date().toISOString() });
        await R.sha(page, module.exports, 'end');
      }, { writes: true }),
  ],
});
