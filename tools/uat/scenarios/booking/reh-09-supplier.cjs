// Pilot rehearsal step 9, the supplier booking (root docs/ops/runbooks/pilot-rehearsal.md step 9; root ADR 0006a A10e).
// WRITES on Dev, on the synthetic rehearsal agency only: the request and the confirm of ONE supplier booking.
// Given: the Dev-only Booking staff writer (booking-staff, booking-sales; signed in unrecorded) and the Booking seeder
// output of this run for the rehearsal agency (env UAT_BOOKING_FIXTURES: its B2B trip case and a supplier booking
// "to request"; a file of another agency stops the run before the browser opens). When: they open the case's Suppliers
// tab, mark the booking as requested, then confirm it with the supplier's reference. Then: the booking reads
// Confirmed with that reference. The browser lets through only those two writes, for that one booking, at most once
// each (limitWrites); Booking itself refuses any other write of this identity and any record of a real agency. $0.
// Not here (gap G6: the A10e staff may not issue them): the agency voucher details, the purchase order and the supplier
// bill. They stay a tech-lead step; the rehearsal README records them as a gap.
const { HOSTS, step } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const { bookingFixtures } = require('../../lib/rehearsal-admin.cjs');

const esc = (s) => s.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&');
let fx = null;
let counts = null;

const rowOf = (page) => page.locator('[data-testid="kit-datatable-row"], tbody tr').filter({ hasText: fx.supplier_booking.code }).first();
const openMenu = async (page, h) => {
  await h.click(page.getByRole('button', { name: `Actions for ${fx.supplier_booking.code}` }));
};

const sc = rw({
  id: 'REH-09-supplier',
  app: 'booking',
  identity: 'booking-staff',
  title: 'Pilot rehearsal, step 9: staff book the supplier for the agency\'s trip',
  titleVi: 'Diễn tập pilot, bước 9: nhân viên đặt nhà cung cấp cho chuyến đi của đại lý',
  baseURL: HOSTS.booking,
  paid: false,
  // Narrowed to the run's own supplier booking in prepare(); this shape is what the write-set check reads.
  allowWrites: ['\\/api\\/booking\\/supplier-bookings\\/[0-9a-f-]{36}\\/(?:request|confirm)$'],
  steps: [
    step('The agency\'s trip is booked. Staff open its Suppliers tab: one hotel or service waits to be requested.',
      'Chuyến đi của đại lý đã được đặt. Nhân viên mở thẻ Nhà cung cấp: có một khách sạn hoặc dịch vụ đang chờ gửi yêu cầu.',
      async (page, h) => {
        counts = await limitWrites(page, [
          { name: 'request', path: new RegExp(`/supplier-bookings/${fx.supplier_booking.id}/request$`), max: 1, strict: true },
          { name: 'confirm', path: new RegExp(`/supplier-bookings/${fx.supplier_booking.id}/confirm$`), max: 1, strict: true },
        ]);
        await h.goto(`/cases/${encodeURIComponent(fx.trip_case.code)}?tab=suppliers`);
        await h.expect(page.locator('h1').first()).toBeVisible({ timeout: 30_000 });
        const row = rowOf(page);
        await h.expect(row).toBeVisible({ timeout: 30_000 });
        await h.expect(row).toContainText(/To request|Requested/);
      }),
    step('Staff send the request to the supplier. The booking now reads Requested.',
      'Nhân viên gửi yêu cầu cho nhà cung cấp. Đặt chỗ chuyển sang trạng thái Đã yêu cầu.',
      async (page, h) => {
        const row = rowOf(page);
        if (/To request/.test((await row.textContent()) || '')) {
          await openMenu(page, h);
          const sent = page.waitForResponse((r) => r.request().method() === 'POST' && /\/request$/.test(new URL(r.url()).pathname), { timeout: 30_000 });
          await h.click(page.getByRole('menuitem', { name: 'Mark as requested' }));
          const res = await sent;
          if (res.status() !== 200) throw new Error(`the request answered ${res.status()}`);
        }
        await h.expect(rowOf(page)).toContainText('Requested', { timeout: 30_000 });
      }, { writes: true }),
    step('The supplier answers. Staff confirm the booking with the supplier\'s reference.',
      'Nhà cung cấp trả lời. Nhân viên xác nhận đặt chỗ kèm mã tham chiếu của nhà cung cấp.',
      async (page, h) => {
        await openMenu(page, h);
        await h.click(page.getByRole('menuitem', { name: 'Confirm…' }));
        const dialog = page.getByRole('dialog').filter({ hasText: `Confirm ${fx.supplier_booking.code}` });
        await h.expect(dialog).toBeVisible({ timeout: 15_000 });
        const ref = dialog.getByPlaceholder('e.g. HTL-48213');
        await h.click(ref);
        await ref.fill(`REH-${(fx.run || 'run').slice(0, 20)}`);
        const done = page.waitForResponse((r) => r.request().method() === 'POST' && /\/confirm$/.test(new URL(r.url()).pathname), { timeout: 30_000 });
        await h.click(dialog.getByRole('button', { name: 'Confirm booking' }));
        const res = await done;
        if (res.status() !== 200) throw new Error(`the confirm answered ${res.status()}`);
      }, { writes: true }),
    step('The booking is confirmed and keeps the supplier\'s reference. This is the end of the scenario.',
      'Đặt chỗ đã được xác nhận và giữ mã tham chiếu của nhà cung cấp. Kết thúc kịch bản.',
      async (page, h) => {
        const row = rowOf(page);
        await h.expect(row).toContainText('Confirmed', { timeout: 30_000 });
        await h.expect(row).toContainText(`Ref REH-`);
        if (counts.request > 1 || counts.confirm !== 1) throw new Error(`writes sent: request ${counts.request}, confirm ${counts.confirm} (expected at most 1 and exactly 1)`);
      }),
  ],
});

const signIn = sc.prepare;
sc.prepare = async (o) => {
  fx = bookingFixtures(); // fail closed before the browser: missing file, or another agency's records
  // A preview (UAT_PREVIEW=1) emptied allowWrites before prepare(): keep it empty then.
  if (sc.allowWrites.length) sc.allowWrites = [`\\/api\\/booking\\/supplier-bookings\\/${esc(fx.supplier_booking.id)}\\/(?:request|confirm)$`];
  await signIn(o);
};
module.exports = sc;
