// CRM review R10 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): invoices and payments.
// Given: A (owner) signed in; prep made the invoice trip: an accepted proposal with an issued deposit invoice due on
//        prep's day (work/crm/state.json invoice_trip; client link path in .secrets.json r10_link_path). R09 published
//        newer booking terms, so the client re-accepts first.
// When:  the owner reads the trip's invoice and the overdue reminder (a task for the agent); the client (C, same browser, client host) re-accepts the terms and says "I have paid" by
//        bank transfer; the owner sees the claim, records the payment; the deposit books the trip; the owner makes the
//        lead's portal link (shown once, blurred; R11 opens it).
// Then:  the invoice moves open -> payment_claimed -> paid, the trip is Booked, no 429 on the client host. Card
//        payments (Stripe) are not built: "Not ready yet" card.
// The overdue step is chosen when the file loads, from state.json and the agency's day: due date passed -> the
// reminder task is shown (a recorded take stops if the hourly reminder has not run yet: the caption would be false);
// not passed yet (prep the same day) -> the open invoice with its due date, no reminder task asserted, and the
// caption says what will happen. Either way result.json meta.overdue notes what was there. Make the captions on the
// recording day: record.cjs refuses a take whose steps changed since. Booking staff (D) is not shown, unlike plan §3:
// this trip has no Adventure Asia item (the AA hold is shown in R08 and R12). Writes on invented data only. Mail: the
// paid deposit makes the CRM invite each traveller to the portal by e-mail, sent through the agency's connected mailbox
// to the invented @example.invalid addresses (undeliverable: the bounce comes back to that mailbox). Cost $0.
const slide = require('../../lib/slide.cjs');
const { crm, st, base, sha, open, bffOk, type, reuse } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-10', title: 'Invoices and payments: a deposit claimed, checked and recorded', titleVi: 'Hoá đơn và thanh toán: khách báo đã cọc, đại lý kiểm và ghi nhận' });
let s;
let t;
let seen429;
// Chosen once, when the file loads: captions and the recorded take must see the same state (record.cjs checks).
const DUE_PASSED = (() => {
  const t0 = st.load().invoice_trip;
  return !!(t0 && t0.due_on && st.today() > t0.due_on.replace(/-/g, ''));
})();

const invoiceRow = (page) => page.getByTestId('trip-invoices').getByTestId('invoice-row').filter({ hasText: t.number });

sc.steps = [
  {
    caption: {
      en: 'A trip the client has already accepted. Its deposit invoice was issued with a due date, and it is still open.',
      vi: 'Một chuyến khách đã chấp nhận trước đó. Hoá đơn đặt cọc đã phát hành kèm hạn trả, và vẫn đang mở.',
    },
    run: async (page, h) => {
      s = st.load();
      t = s.invoice_trip;
      if (!t || !t.invoice_id) throw new Error('no invoice trip: run scenarios/crm/prep.cjs --fast first');
      seen429 = crm.watch429(page);
      await sha(page, sc, 'start');
      await open(page, h, `/pipeline/${t.trip_id}`, 'crm-trip');
      await h.expect(page.getByTestId('crm-trip')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
      const inv = await bffOk(page, 'GET', `invoices/${t.invoice_id}`);
      if (inv.status !== 'open') {
        reuse(h, `the deposit invoice (${inv.status})`, 'prep.cjs makes a new invoice trip');
        sc.meta.skipped = inv.status;
        return;
      }
      const row = invoiceRow(page);
      await h.scrollTo(row);
      await h.expect(row).toHaveAttribute('data-status', 'open');
    },
  },
  DUE_PASSED
    ? {
      caption: {
        en: 'The due date has passed. The CRM reminds the agent, with a task on the trip and an item in the bell.',
        vi: 'Đã quá hạn trả. CRM nhắc đại lý bằng một việc trên chuyến và một mục trong chuông.',
      },
      run: async (page, h) => {
        if (sc.meta.skipped) return;
        const task = page.locator('[data-testid="trip-task"][data-kind="invoice_overdue"]');
        if (!(await task.count())) {
          if (!h.fast) throw new Error(`the deposit (due ${t.due_on}) is not reminded as overdue yet: the reminder runs hourly, record again later`);
          sc.meta.overdue = 'due passed, reminder not run yet';
          return;
        }
        await h.scrollTo(task.first());
        await h.expect(task.first()).toHaveAttribute('data-status', 'open');
        await h.hover(task.first());
        sc.meta.overdue = 'reminded';
      },
    }
    : {
      caption: {
        en: 'The deposit is due today. Once the date passes, the CRM reminds the agent, with a task on the trip and an item in the bell.',
        vi: 'Hạn trả cọc là hôm nay. Khi qua ngày đó, CRM nhắc đại lý bằng một việc trên chuyến và một mục trong chuông.',
      },
      run: async (page, h) => {
        if (sc.meta.skipped) return;
        if (st.today() !== t.due_on.replace(/-/g, '')) throw new Error(`the deposit is due ${t.due_on}, the agency day is ${st.today()}: make the captions again`);
        const row = invoiceRow(page);
        await h.expect(row).toHaveAttribute('data-status', 'open');
        await h.expect(page.locator('[data-testid="trip-task"][data-kind="invoice_overdue"]')).toHaveCount(0);
        await h.hover(row);
        sc.meta.overdue = `not overdue yet (due ${t.due_on})`;
      },
    },
  {
    caption: {
      en: 'The client opens her link. The terms changed after she accepted, so she accepts the new version first.',
      vi: 'Khách mở đường dẫn của mình. Điều khoản đã đổi sau khi khách chấp nhận, nên khách chấp nhận bản mới trước.',
    },
    run: async (page, h) => {
      if (sc.meta.skipped) return;
      const linkPath = st.link('r10_link_path', t.trip_id);
      if (!linkPath) throw new Error('no client link of this run\'s invoice trip: run scenarios/crm/prep.cjs --fast');
      await h.goto(`${crm.CLIENT}${linkPath}`);
      await page.waitForURL(`${crm.CLIENT}/c/p`, { timeout: 20_000 });
      await h.expect(page.getByTestId('client-proposal')).toHaveAttribute('data-status', 'accepted', { timeout: 20_000 });
      const box = page.getByTestId('client-terms-reaccept');
      if (!(await box.isVisible().catch(() => false))) return reuse(h, 'the re-accept of the new terms', 'run crm-rev-09 first');
      await h.scrollTo(box);
      await h.click(box.getByTestId('client-reaccept-agree'));
      await type(page, h, box.getByTestId('client-reaccept-name'), t.lead_name);
      await crm.paceClientWrite();
      await h.click(page.getByTestId('client-reaccept'));
      await h.expect(box).toHaveCount(0, { timeout: 20_000 });
    },
  },
  {
    caption: {
      en: 'The payment box shows the agency\'s bank details. She pays by transfer and taps "I have paid".',
      vi: 'Ô thanh toán hiện thông tin ngân hàng của đại lý. Khách chuyển khoản và bấm "I have paid".',
    },
    run: async (page, h) => {
      if (sc.meta.skipped) return;
      const item = page.getByTestId('client-pay-invoice').first();
      await h.scrollTo(item);
      await h.expect(item.getByTestId('client-pay-details')).toBeVisible();
      await crm.paceClientWrite();
      await h.click(item.getByTestId('client-pay-claim'));
      await h.expect(item).toHaveAttribute('data-state', 'claimed', { timeout: 20_000 });
      crm.assertNo429(seen429);
    },
  },
  {
    caption: {
      en: 'At the agency the invoice now says the client has paid, with the time by which the transfer should be checked.',
      vi: 'Ở đại lý, hoá đơn giờ ghi khách báo đã trả, kèm thời hạn cần kiểm tra khoản chuyển.',
    },
    run: async (page, h) => {
      if (sc.meta.skipped) return;
      await open(page, h, `/pipeline/${t.trip_id}`, 'crm-trip');
      await h.expect(page.getByTestId('crm-trip')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
      const row = invoiceRow(page);
      await h.scrollTo(row);
      await h.expect(row).toHaveAttribute('data-status', 'payment_claimed', { timeout: 15_000 });
      await h.expect(row.getByTestId('invoice-claim-note')).toBeVisible();
      await h.hover(row.getByTestId('invoice-claim-note'));
    },
  },
  {
    caption: {
      en: 'The money is in the bank, so the owner records the payment with its date and bank reference.',
      vi: 'Tiền đã về tài khoản, nên chủ đại lý ghi nhận thanh toán kèm ngày và mã tham chiếu ngân hàng.',
    },
    run: async (page, h) => {
      if (sc.meta.skipped) return;
      const row = invoiceRow(page);
      await h.click(row.getByRole('button', { name: 'Record payment' }));
      const form = row.getByTestId('payment-form');
      await h.expect(form).toBeVisible();
      await h.expect(form.locator('input[name="amount"]')).toHaveValue(/^540(\.00)?$/);
      await type(page, h, form.getByTestId('date-input'), st.today().replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'));
      await type(page, h, form.locator('input[name="reference"]'), `TRF-${s.run}`);
      await h.click(form.getByRole('button', { name: 'Save payment' }));
      await h.expect(row).toHaveAttribute('data-status', 'paid', { timeout: 20_000 });
    },
  },
  {
    caption: {
      en: 'The paid deposit books the trip. Each traveller gets a personal portal link; the owner copies the lead\'s, hidden here.',
      vi: 'Tiền cọc đã trả nên chuyến chuyển sang Booked. Mỗi khách có một đường dẫn cổng riêng; chủ đại lý sao chép đường dẫn của khách đứng tên, được che ở đây.',
    },
    run: async (page, h) => {
      await open(page, h, `/pipeline/${t.trip_id}`, 'crm-trip');
      await h.expect(page.getByTestId('crm-trip')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
      await h.expect(page.getByTestId('trip-stage')).toHaveAttribute('data-stage', /^(booked|pre_departure)$/, { timeout: 20_000 });
      const tab = page.getByTestId('trip-proposal');
      const row = tab.getByTestId('portal-row').filter({ hasText: t.lead_name }).first();
      await h.scrollTo(row);
      await h.click(row.getByRole('button', { name: /portal link/i }));
      const link = await tab.getByTestId('proposal-copy-link').first().inputValue({ timeout: 20_000 });
      if (!/\/c\/[a-z]+\/[A-Za-z0-9_-]{30,}$/.test(link)) throw new Error('the portal link has an unexpected shape');
      st.saveLink('r11_link', link, t.trip_id);
      s = st.load();
      s.r10 = { trip_id: t.trip_id, booked_at: (s.r10 && s.r10.booked_at) || new Date().toISOString() };
      st.save(s);
      await h.hover(tab.getByTestId('proposal-copy-links'));
      await h.assertMasked(['[data-testid="proposal-copy-links"]']);
    },
  },
  {
    caption: {
      en: 'Not ready yet: card payments through the agency\'s own Stripe account. Today the agency records transfers by hand.',
      vi: 'Chưa có: thanh toán thẻ qua tài khoản Stripe của chính đại lý. Hiện đại lý ghi nhận chuyển khoản bằng tay.',
    },
    run: async (page, h) => {
      await slide.notReady(page, h, {
        screen: 'Card payments',
        missing: ['Card payments through the agency\'s own Stripe account (Stripe Connect)', 'A card payment link in the client\'s payment box, confirmed automatically'],
      });
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
