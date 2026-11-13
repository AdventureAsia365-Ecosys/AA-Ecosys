// Pilot rehearsal step 11, checker half (root docs/ops/runbooks/pilot-rehearsal.md step 11; root ADR 0006a A10e).
// WRITES on Dev, on the synthetic rehearsal agency only: the approval of the payment REH-11-maker recorded.
// Given: the Dev-only Booking finance checker (booking-checker, booking-finance; signed in unrecorded; never the
// recorder) and the same seeder output (env UAT_BOOKING_FIXTURES). When: they open the invoice and approve the payment
// waiting there. Then: the payment reads Approved and the invoice Paid. Only the approval of a payment of that invoice
// goes through, once (limitWrites); Booking refuses its own recordings and any real agency's payment. $0.
const { HOSTS, step } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const { bookingFixtures } = require('../../lib/rehearsal-admin.cjs');

let fx = null;
let counts = null;
const payments = (page) => page.locator('[data-testid="kit-datatable-row"], tbody tr');

module.exports = (() => {
  const sc = rw({
    id: 'REH-11-checker',
    app: 'booking',
    identity: 'booking-checker',
    title: 'Pilot rehearsal, step 11: a second person approves the payment',
    titleVi: 'Diễn tập pilot, bước 11: một người thứ hai duyệt khoản thanh toán',
    baseURL: HOSTS.booking,
    paid: false,
    // The payment id is only known on the page: any payment's approve, and the browser lets one through.
    allowWrites: ['\\/api\\/booking\\/agency-payments\\/[0-9a-f-]{36}\\/approve$'],
    steps: [
      step('A second finance person opens the same invoice. One payment waits for approval.',
        'Một nhân viên tài chính thứ hai mở cùng hoá đơn đó. Có một khoản thanh toán đang chờ duyệt.',
        async (page, h) => {
          counts = await limitWrites(page, [{ name: 'approve', path: /\/agency-payments\/[0-9a-f-]{36}\/approve$/, max: 1, strict: true }]);
          await h.goto(`/agency-billing/invoices/${encodeURIComponent(fx.invoice.number)}`);
          await h.expect(page.locator('h1').first()).toContainText(fx.invoice.number, { timeout: 30_000 });
          const waiting = payments(page).filter({ hasText: 'Waiting for approval' });
          await h.expect(waiting).toHaveCount(1, { timeout: 30_000 });
          await h.scrollTo(waiting.first(), 'center');
          await h.expect(waiting.first().getByRole('button', { name: 'Approve' })).toBeVisible({ timeout: 15_000 });
        }),
      step('They check it against the bank statement and approve it.',
        'Người này đối chiếu với sao kê ngân hàng rồi duyệt.',
        async (page, h) => {
          const row = payments(page).filter({ hasText: 'Waiting for approval' }).first();
          const done = page.waitForResponse((r) => r.request().method() === 'POST' && /\/approve$/.test(new URL(r.url()).pathname), { timeout: 30_000 });
          await h.click(row.getByRole('button', { name: 'Approve' }));
          const res = await done;
          if (res.status() !== 200) throw new Error(`the approval answered ${res.status()}`);
        }, { writes: true }),
      step('The payment counts now: approved, and the invoice is paid. This is the end of the scenario.',
        'Khoản thanh toán giờ đã được tính: đã duyệt, và hoá đơn đã thanh toán xong. Kết thúc kịch bản.',
        async (page, h) => {
          await h.expect(payments(page).filter({ hasText: 'Approved' }).first()).toBeVisible({ timeout: 30_000 });
          await h.expect(page.getByText('Paid', { exact: true }).first()).toBeVisible({ timeout: 30_000 });
          if (counts.approve !== 1) throw new Error(`approvals sent: ${counts.approve} (expected exactly 1)`);
        }),
    ],
  });
  const signIn = sc.prepare;
  sc.prepare = async (o) => { fx = bookingFixtures(); await signIn(o); };
  return sc;
})();
