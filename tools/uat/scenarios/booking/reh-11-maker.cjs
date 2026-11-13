// Pilot rehearsal step 11, maker half (root docs/ops/runbooks/pilot-rehearsal.md step 11; root ADR 0006a A10e).
// WRITES on Dev, on the synthetic rehearsal agency only: ONE payment recorded on its issued invoice.
// Given: the Dev-only Booking finance maker (booking-maker, booking-finance; signed in unrecorded) and the Booking seeder
// output of this run for the rehearsal agency (env UAT_BOOKING_FIXTURES: an issued agency invoice; a file of another
// agency stops the run before the browser opens). When: they open the invoice, record the open amount as a bank
// transfer with an invented evidence reference. Then: the payment is listed "Waiting for approval" and the maker sees
// that another person approves it. Only that one POST goes through (limitWrites); Booking refuses any other write of
// this identity and any invoice of a real agency. $0. The approval is REH-11-checker (another identity), recorded next.
// Not here (gap G7): an overdue synthetic invoice and the 409 on a hold while it is overdue.
const { HOSTS, step } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const { bookingFixtures } = require('../../lib/rehearsal-admin.cjs');

const esc = (s) => s.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&');
let fx = null;
let counts = null;
const payments = (page) => page.locator('[data-testid="kit-datatable-row"], tbody tr');

const sc = rw({
  id: 'REH-11-maker',
  app: 'booking',
  identity: 'booking-maker',
  title: 'Pilot rehearsal, step 11: finance records the agency\'s payment',
  titleVi: 'Diễn tập pilot, bước 11: bộ phận tài chính ghi nhận khoản thanh toán của đại lý',
  baseURL: HOSTS.booking,
  paid: false,
  allowWrites: ['\\/api\\/booking\\/agency-invoices\\/[0-9a-f-]{36}\\/payments$'],
  steps: [
    step('AA invoiced the rehearsal agency. Finance opens the invoice: it is issued and has an amount left to pay.',
      'AA đã xuất hoá đơn cho đại lý diễn tập. Bộ phận tài chính mở hoá đơn: hoá đơn đã phát hành và còn số tiền phải trả.',
      async (page, h) => {
        counts = await limitWrites(page, [{ name: 'record', path: new RegExp(`/agency-invoices/${fx.invoice.id}/payments$`), max: 1 }]);
        await h.goto(`/agency-billing/invoices/${encodeURIComponent(fx.invoice.number)}`);
        await h.expect(page.locator('h1').first()).toContainText(fx.invoice.number, { timeout: 30_000 });
        await h.expect(page.getByText('Issued', { exact: true }).first()).toBeVisible({ timeout: 30_000 });
        await h.expect(page.getByRole('button', { name: 'Record payment' })).toBeVisible({ timeout: 30_000 });
      }),
    step('The agency paid by bank transfer. Finance records the payment with the bank statement line as evidence.',
      'Đại lý đã chuyển khoản. Bộ phận tài chính ghi nhận khoản thanh toán, kèm dòng sao kê ngân hàng làm bằng chứng.',
      async (page, h) => {
        await h.click(page.getByRole('button', { name: 'Record payment' }));
        const drawer = page.getByRole('dialog').filter({ hasText: `Record payment · ${fx.invoice.number}` });
        await h.expect(drawer).toBeVisible({ timeout: 15_000 });
        const evidence = drawer.getByLabel(/^Evidence/);
        await h.click(evidence);
        await evidence.fill(`Synthetic rehearsal statement line ${String(fx.run || '').slice(0, 20)}`);
        const done = page.waitForResponse((r) => r.request().method() === 'POST' && /\/payments$/.test(new URL(r.url()).pathname), { timeout: 30_000 });
        await h.click(drawer.getByRole('button', { name: 'Record payment' }));
        const res = await done;
        if (res.status() !== 201) throw new Error(`recording the payment answered ${res.status()}`);
      }, { writes: true }),
    step('The payment waits for approval. Another person must approve it. This is the end of the scenario.',
      'Khoản thanh toán đang chờ duyệt. Phải có một người khác duyệt. Kết thúc kịch bản.',
      async (page, h) => {
        const row = payments(page).filter({ hasText: 'Waiting for approval' }).first();
        await h.scrollTo(row, 'center');
        await h.expect(row).toBeVisible({ timeout: 30_000 });
        await h.expect(row).toContainText('Another person approves');
        if (counts.record !== 1) throw new Error(`payment records sent: ${counts.record} (expected exactly 1)`);
      }),
  ],
});

const signIn = sc.prepare;
sc.prepare = async (o) => {
  fx = bookingFixtures();
  // A preview (UAT_PREVIEW=1) emptied allowWrites before prepare(): keep it empty then.
  if (sc.allowWrites.length) sc.allowWrites = [`\\/api\\/booking\\/agency-invoices\\/${esc(fx.invoice.id)}\\/payments$`];
  await signIn(o);
};
module.exports = sc;
