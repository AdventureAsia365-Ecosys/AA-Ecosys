// Pilot rehearsal step 8, part 2 (runbook docs/ops/runbooks/pilot-rehearsal.md, "pays the deposit ('I've paid')"):
// the deposit invoice, the client's "I have paid", the payment and the trip booked.
// Given: REH-08-accept: the client accepted version 1 under a live Adventure Asia hold; the owner (crm-rehearsal) is
//        signed in outside the recording; the client link is in work/rehearsal/.crm-secrets.json (r08_link).
// When:  the owner raises the deposit invoice from the accepted payment plan and issues it; the client (same browser,
//        client host) opens her link and says "I have paid" by bank transfer; the owner sees the claim and records the
//        payment with a bank reference.
// Then:  the invoice moves open -> payment_claimed -> paid; the trip is Booked; the CRM asks Adventure Asia to confirm
//        the held tour (crm_booking_sync: one confirm request for the hold set). An instant departure confirms at once;
//        an on-request one waits for Booking staff (the Booking group's step 8), then REH-08c-aa-confirmed reads it.
// Writes: one deposit invoice (create, issue), the client's claim, one payment, on the rehearsal trip only. VNPay /
// card payment is not used (the runbook: stub only). Mail: the paid deposit makes the CRM invite each traveller to the
// portal through the agency's connected mailbox (the planner traveller's invented address). No LLM call. Cost $0.
const R = require('./_reh.cjs');

const { step, crm } = R;
let s;
let inv;
let seen429;

const invoiceRow = (page) => page.getByTestId('trip-invoices').getByTestId('invoice-row').filter({ hasText: inv.number });

module.exports = R.scenario({
  id: 'REH-08b-deposit',
  title: 'Rehearsal: the deposit is claimed, checked and recorded, and the trip is booked',
  titleVi: 'Diễn tập: khách báo đã cọc, đại lý kiểm tra và ghi nhận, chuyến được đặt',
  allowWrites: [
    ...R.bffWrites(`trips/${R.UUID}/invoices`, `invoices/${R.UUID}/(?:issue|payments)`),
    ...R.clientWrites('proposal'),
  ],
  steps: [
    step('Back at the agency, the trip shows the accepted proposal and its payment plan: the deposit is not invoiced yet.',
      'Ở đại lý, chuyến hiện đề xuất đã được chấp nhận và kế hoạch thanh toán: khoản cọc chưa được lập hoá đơn.',
      async (page, h) => {
        s = R.need(R.load(), ['trip_id', 'proposal_id', 'accepted_at'], 'REH-08-accept');
        seen429 = crm.watch429(page);
        await R.sha(page, module.exports, 'start');
        await R.openTrip(page, h, s.trip_id);
        await R.me(page, 'owner');
        const row = page.getByTestId('schedule-row').and(page.locator('[data-kind="deposit"]')).first();
        await h.scrollTo(row);
        await h.expect(row).toBeVisible({ timeout: 20_000 });
        await h.hover(row);
      }),
    step('The owner raises the deposit invoice from the plan and issues it. It gets its number and due date.',
      'Chủ đại lý lập hoá đơn cọc từ kế hoạch và phát hành. Hoá đơn có số và hạn trả.',
      async (page, h) => {
        const life = await R.bffOk(page, 'GET', `trips/${s.trip_id}/lifecycle`);
        const dep = (life.schedule || []).find((x) => x.kind === 'deposit' && x.proposal_id === s.proposal_id);
        if (!dep) throw new Error('the accepted version has no deposit row');
        const panel = page.getByTestId('trip-invoices');
        await h.scrollTo(panel);
        if (s.deposit_invoice_id) {
          R.reuse(h, 'the deposit invoice');
        } else {
          const create = panel.getByTestId('invoice-from-schedule').getByRole('button', { name: 'Create invoice' }).first();
          const made = page.waitForResponse((r) => /\/trips\/[0-9a-f-]{36}\/invoices$/.test(new URL(r.url()).pathname) && r.request().method() === 'POST', { timeout: 30_000 });
          await h.click(create);
          const res = await made;
          h.expect(res.status()).toBe(201);
          const body = await res.json();
          s = R.save({ deposit_invoice_id: body.invoice_id });
        }
        let cur = await R.bffOk(page, 'GET', `invoices/${s.deposit_invoice_id}`);
        if (cur.status === 'draft') {
          const draftRow = panel.getByTestId('invoice-row').and(page.locator('[data-status="draft"]')).first();
          await h.expect(draftRow).toBeVisible({ timeout: 15_000 });
          await h.click(draftRow.getByRole('button', { name: 'Issue' }));
          await h.expect.poll(async () => (await R.bffOk(page, 'GET', `invoices/${s.deposit_invoice_id}`)).status, { timeout: 20_000 }).toBe('open');
          cur = await R.bffOk(page, 'GET', `invoices/${s.deposit_invoice_id}`);
        }
        inv = cur;
        h.expect(['open', 'payment_claimed', 'paid']).toContain(inv.status);
        await h.expect(invoiceRow(page)).toBeVisible({ timeout: 15_000 });
        await h.hover(invoiceRow(page));
        module.exports.meta.deposit = { amount: inv.total || inv.amount || null, currency: inv.currency || null };
      }, { writes: true }),
    step('The client opens her link. The payment box shows the agency\'s bank details. She pays by transfer and taps "I have paid".',
      'Khách mở đường dẫn của mình. Ô thanh toán hiện thông tin ngân hàng của đại lý. Khách chuyển khoản và bấm "I have paid".',
      async (page, h) => {
        const link = R.link('r08_link', s.trip_id);
        if (!link) throw new Error('no client link of the rehearsal trip: run REH-07b-approve first');
        await h.goto(link);
        await page.waitForURL(`${crm.CLIENT}/c/p`, { timeout: 20_000 });
        await h.expect(page.getByTestId('client-proposal')).toHaveAttribute('data-status', 'accepted', { timeout: 20_000 });
        const item = page.getByTestId('client-pay-invoice').first();
        await h.scrollTo(item);
        await h.expect(item.getByTestId('client-pay-details')).toBeVisible();
        if (inv.status !== 'open') return R.reuse(h, `the client's claim (${inv.status})`);
        await crm.paceClientWrite();
        await h.click(item.getByTestId('client-pay-claim'));
        await h.expect(item).toHaveAttribute('data-state', 'claimed', { timeout: 20_000 });
        crm.assertNo429(seen429);
      }, { writes: true }),
    step('At the agency the invoice now says the client has paid, with the time by which the transfer should be checked.',
      'Ở đại lý, hoá đơn giờ ghi khách báo đã trả, kèm thời hạn cần kiểm tra khoản chuyển.',
      async (page, h) => {
        await R.openTrip(page, h, s.trip_id);
        const row = invoiceRow(page);
        await h.scrollTo(row);
        await h.expect(row).toHaveAttribute('data-status', /^(payment_claimed|paid)$/, { timeout: 15_000 });
        if ((await row.getAttribute('data-status')) === 'payment_claimed') {
          await h.expect(row.getByTestId('invoice-claim-note')).toBeVisible();
          await h.hover(row.getByTestId('invoice-claim-note'));
        }
      }),
    step('The money is in the bank, so the owner records the payment with its date and bank reference.',
      'Tiền đã về tài khoản, nên chủ đại lý ghi nhận thanh toán kèm ngày và mã tham chiếu ngân hàng.',
      async (page, h) => {
        const row = invoiceRow(page);
        if ((await row.getAttribute('data-status')) === 'paid') return R.reuse(h, 'the recorded payment');
        await h.click(row.getByRole('button', { name: 'Record payment' }));
        const form = row.getByTestId('payment-form');
        await h.expect(form).toBeVisible();
        await h.expect(form.locator('input[name="amount"]')).not.toHaveValue('');
        await R.type(page, h, form.getByTestId('date-input'), R.day(0));
        await R.type(page, h, form.locator('input[name="reference"]'), `TRF-REH-${s.trip_id.slice(0, 8)}`);
        await h.click(form.getByRole('button', { name: 'Save payment' }));
        await h.expect(row).toHaveAttribute('data-status', 'paid', { timeout: 20_000 });
      }, { writes: true }),
    step('The paid deposit books the trip, and the CRM asks Adventure Asia to confirm the held tour.',
      'Tiền cọc đã trả nên chuyến chuyển sang Booked, và CRM đề nghị Adventure Asia xác nhận tour đang được giữ chỗ.',
      async (page, h) => {
        await R.openTrip(page, h, s.trip_id);
        await h.expect(page.getByTestId('trip-stage')).toHaveAttribute('data-stage', /^(booked|pre_departure)$/, { timeout: 20_000 });
        // The sync writes the accepted hold set's AA lines, then one confirm for the set once the deposit is in.
        let lines = [];
        await h.expect.poll(async () => {
          lines = await R.aaLines(page, s.trip_id);
          const l = lines[0];
          if (!l || !l.aa) return 'no AA line yet';
          if (l.status === 'confirmed' || l.aa.sub_status === 'confirmed') return 'confirmed';
          return l.aa.pending && l.aa.pending.kind === 'confirm' ? 'confirm asked' : `${l.aa.sub_status || '-'}`;
        }, { timeout: 120_000, intervals: [3_000, 5_000, 10_000] }).toMatch(/^(confirmed|confirm asked|held)$/);
        const l = lines[0];
        R.save({ aa_line: { booking_line_id: l.booking_line_id, title: l.title, status: l.status, sub_status: l.aa.sub_status }, r08b_done_at: new Date().toISOString() });
        module.exports.meta.aa_line = { status: l.status, sub_status: l.aa.sub_status, pending: l.aa.pending ? l.aa.pending.kind : null };
        const ledger = page.getByTestId('ledger-lines').or(page.getByTestId('ledger-cards')).first();
        await h.scrollTo(ledger);
        await h.expect(page.getByTestId(`line-${l.booking_line_id}`).or(ledger.getByText(l.title).first()).first()).toBeVisible({ timeout: 15_000 });
        await h.hover(ledger);
        crm.assertNo429(seen429);
        await R.sha(page, module.exports, 'end');
      }),
  ],
});
