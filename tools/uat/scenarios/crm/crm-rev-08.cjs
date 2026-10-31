// CRM review R08 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): the client accepts on a phone.
// Given: R06 published and sent the R03 trip's version; its client link sits in work/crm/.secrets.json (r08_link).
// When:  the invented traveller (C) opens the link on a 390 x 844 phone, reads Before you go and the days, checks the
//        Adventure Asia seats (a short hold on Booking), confirms the rooms, agrees to the booking terms, types her
//        name and accepts.
// Then:  the link leaves the address bar (cookie), day 0 comes first, the hold box turns active with a "held until",
//        the page shows the acceptance; no 429 on the client host (two anonymous writes, >= 14 s apart).
// Writes: one client hold on Booking (one adult on a Dev departure, accepted in the plan, Q5) and the acceptance.
// No sign-in (the link is the credential, never shown or logged). A re-run on an accepted version skips in --fast
// only. No LLM call. Cost $0.
const { crm, st, base, sha, PHONE, type, reuse } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-08', title: 'The client accepts the proposal on a phone', who: null, viewport: PHONE });
let s;
let seen429;
let accepted = false;

sc.steps = [
  {
    caption: {
      en: 'The client opens the agency\'s link on her phone. The page swaps the link for a private cookie, so it never stays in the address bar.',
      vi: 'Khách mở đường dẫn của đại lý trên điện thoại. Trang đổi đường dẫn thành một cookie riêng, nên nó không nằm lại trên thanh địa chỉ.',
    },
    run: async (page, h) => {
      s = st.load();
      const link = st.loadSecrets().r08_link;
      if (!link || !s.r03) throw new Error('no client link: run crm-rev-06 first');
      seen429 = crm.watch429(page);
      await sha(page, sc, 'start');
      await h.goto(link);
      await page.waitForURL(`${crm.CLIENT}/c/p`, { timeout: 20_000 });
      const cp = page.getByTestId('client-proposal');
      await h.expect(cp).toHaveAttribute('data-kind', 'builder', { timeout: 20_000 });
      accepted = (await cp.getAttribute('data-status')) === 'accepted';
      if (accepted) reuse(h, 'the acceptance of this version', 're-run crm-rev-03 to crm-rev-06');
    },
  },
  {
    caption: {
      en: 'It opens with Before you go: the visa link and the insurance reminder. Then come the days, each in the local time zone.',
      vi: 'Trang mở đầu bằng Before you go: link visa và lời nhắc bảo hiểm. Sau đó là từng ngày, theo giờ địa phương.',
    },
    run: async (page, h) => {
      await h.expect(page.getByTestId('client-day').first()).toHaveAttribute('data-day', '0');
      await h.expect(page.getByTestId('client-before-you-go')).toBeVisible();
      await h.hover(page.getByTestId('client-before-you-go'));
      const day1 = page.locator('[data-testid="client-day"][data-day="1"]');
      await h.scrollTo(day1);
      const width = await page.evaluate(() => document.documentElement.scrollWidth);
      h.expect(width, 'no sideways scroll at 390 px').toBeLessThanOrEqual(PHONE.width);
    },
  },
  {
    caption: {
      en: 'Day two holds the Adventure Asia island tour on its fixed departure. The total at the bottom follows every choice.',
      vi: 'Ngày thứ hai có tour đảo của Adventure Asia theo ngày khởi hành cố định. Tổng tiền ở cuối trang thay đổi theo từng lựa chọn.',
    },
    run: async (page, h) => {
      const tour = page.getByTestId('client-block').filter({ hasText: 'Island tour' });
      await h.scrollTo(tour);
      await h.expect(tour.getByTestId('client-option')).toHaveCount(1);
      await h.scrollTo(page.getByTestId('client-total'));
      await h.expect(page.getByTestId('client-total')).toContainText(/\d/);
    },
  },
  {
    caption: {
      en: 'Before accepting, she checks the seats. Adventure Asia holds them for her for a short time.',
      vi: 'Trước khi chấp nhận, khách kiểm tra chỗ. Adventure Asia giữ chỗ cho khách trong một thời gian ngắn.',
    },
    run: async (page, h) => {
      if (accepted) return;
      const box = page.getByTestId('client-hold');
      await h.scrollTo(box);
      if ((await box.getAttribute('data-status')) !== 'active') {
        await h.expect(box).toHaveAttribute('data-status', 'missing');
        await crm.paceClientWrite();
        await h.click(page.getByTestId('client-hold-button'));
      }
      await h.expect(box).toHaveAttribute('data-status', 'active', { timeout: 60_000 });
      await h.expect(page.getByTestId('client-held-until')).toBeVisible();
      crm.assertNo429(seen429);
    },
  },
  {
    caption: {
      en: 'She confirms the rooms, agrees to the agency\'s booking terms and types her full name.',
      vi: 'Khách xác nhận phòng, đồng ý với điều khoản đặt chỗ của đại lý và gõ họ tên đầy đủ.',
    },
    run: async (page, h) => {
      if (accepted) return;
      const form = page.getByTestId('client-accept-form');
      await h.scrollTo(form);
      await h.expect(form.getByTestId('client-groups')).toBeVisible();
      await h.click(form.getByTestId('client-rooms').locator('input'));
      await h.click(form.locator('input[name="accept_terms"]'));
      await h.expect(form.locator('input[name="accept_terms"]')).toBeChecked();
      await type(page, h, form.locator('input[name="full_name"]'), s.r03.lead_name);
    },
  },
  {
    caption: {
      en: 'She accepts. The agency is told at once, and the next step is the deposit.',
      vi: 'Khách bấm chấp nhận. Đại lý được báo ngay, bước tiếp theo là tiền đặt cọc.',
    },
    run: async (page, h) => {
      if (!accepted) {
        await crm.paceClientWrite();
        await h.click(page.getByTestId('client-accept'));
      }
      await h.expect(page.getByTestId('client-accepted')).toBeVisible({ timeout: 20_000 });
      await h.scrollTo(page.getByTestId('client-accepted'));
      crm.assertNo429(seen429);
      s = st.load();
      s.r08 = { trip_id: s.r03.trip_id, accepted_at: s.r08 ? s.r08.accepted_at : new Date().toISOString() };
      st.save(s);
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
