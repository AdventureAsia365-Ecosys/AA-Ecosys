// Pilot rehearsal price setup (AA-1091; root docs/ops/runbooks/pilot-rehearsal.md "Tour X": a sellable plan with a
// price), the result, read only. The workbook DRY RUN, the import and the approval of each draft price version are NOT
// filmed: no Dev-only E2E identity may write prices (the A10a admin is read-only; the A10e writers hold supplier
// bookings and payments only), and a version needs a second person to approve it. The tech lead (maker) and a second
// admin (checker) do them by hand first; then this scenario shows the result.
// Given: the E2E Booking admin (A10a, read-only session); env UAT_REH_TOUR_KEYS (optional) = the tour keys the import
// priced. When: they open Price setup, then the rehearsal agency's tariff. Then: at least 3 tours are priced, sellable
// and carry a from-price (each named tour among them), and the agency's tariff prices at least 3 tours. Nothing is
// written. $0. The TripPlanner "From $X" of the same tours is REH-01-from-price.
const { HOSTS, step, ro, check, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');
const { REHEARSAL, listEnv } = require('../../lib/rehearsal-admin.cjs');

const MIN_PRICED = 3;
const READY = ['priced', 'hand_priced'];
let keys = [];
let partner = null;

async function getJson(page, p) {
  const res = await page.request.get(`${HOSTS.booking}/api/booking/${p}`, { headers: { Accept: 'application/json' }, timeout: 60_000 });
  if (res.status() !== 200) throw new Error(`GET ${p.split('?')[0]} answered ${res.status()}`);
  return res.json();
}

module.exports = ro({
  id: 'REH-01-prices',
  app: 'booking',
  identity: 'booking',
  title: 'Pilot rehearsal: tours priced for the agency',
  titleVi: 'Diễn tập pilot: các tour đã có giá cho đại lý',
  baseURL: HOSTS.booking,
  prepare: async () => { keys = listEnv('UAT_REH_TOUR_KEYS'); },
  steps: [
    step('Price setup shows what each tour still needs before an agency can buy it.',
      'Trang Thiết lập giá cho biết mỗi tour còn thiếu gì trước khi đại lý có thể mua.',
      async (page, h) => {
        await check(page, h, '/pricing/workbench', { heading: 'Price setup', table: true });
        await h.expect(page.getByText('Ready to sell', { exact: true }).first()).toBeVisible({ timeout: 30_000 });
      }),
    step('The customer service team priced at least three tours from a workbook. They are priced and sellable.',
      'Bộ phận chăm sóc khách hàng đã nhập giá cho ít nhất ba tour từ file Excel. Các tour này đã có giá và đang được bán.',
      async (page, h) => {
        const ready = [];
        for (const status of READY) {
          const wb = await getJson(page, `catalog/price-workbench?status=${status}`);
          for (const it of wb.items || []) if (it.sellable && it.from_price) ready.push(it.tour_key);
        }
        if (ready.length < MIN_PRICED) throw new Error(`${ready.length} tours are priced, sellable and have a from-price (need ${MIN_PRICED})`);
        const missing = keys.filter((k) => !ready.includes(k));
        if (missing.length) throw new Error(`not priced and sellable yet: ${missing.join(', ')}`);
        const shown = keys[0] || ready[0];
        await check(page, h, `/pricing/workbench?q=${encodeURIComponent(shown)}`, { heading: 'Price setup', table: true });
        const row = page.locator('[data-testid="kit-datatable-row"], tbody tr').first();
        await h.expect(row).toBeVisible({ timeout: 30_000 });
        await h.expect(row).toContainText('Sellable');
      }),
    step('The rehearsal agency\'s tariff now lists those tours with the agency\'s own price.',
      'Bảng giá của đại lý diễn tập giờ đã có các tour đó, với giá riêng của đại lý.',
      async (page, h) => {
        const terms = await getJson(page, 'pricing/partner-terms');
        const mine = (terms.items || []).filter((p) => p && p.agency_name === REHEARSAL.name);
        if (mine.length !== 1) throw new Error(`Booking lists ${mine.length} partners named ${REHEARSAL.name} (expected 1)`);
        [partner] = mine;
        const tariff = await getJson(page, `pricing/partner-tariffs/${encodeURIComponent(partner.id)}?currency=USD`);
        const tours = new Set((tariff.items || []).map((i) => i.tour && i.tour.source_id).filter(Boolean));
        if (tours.size < MIN_PRICED) throw new Error(`the agency tariff prices ${tours.size} tours (need ${MIN_PRICED})`);
        const missing = keys.filter((k) => !tours.has(k));
        if (missing.length) throw new Error(`not on the agency tariff: ${missing.join(', ')}`);
        await check(page, h, `/pricing/agency-tiers/tariff?partner=${encodeURIComponent(partner.id)}`, { heading: `Tariff: ${REHEARSAL.name}` });
        await rowsOrEmpty(page, h);
        await h.expect(page.locator('[data-testid="kit-datatable-row"], tbody tr').first()).toBeVisible({ timeout: 30_000 });
      }),
    step('Agencies see the same prices in their own tariff and in their quotes. This is the end of the scenario.',
      'Đại lý thấy cùng mức giá này trong bảng giá của mình và trong báo giá. Kết thúc kịch bản.',
      async (page, h) => {
        const rows = page.locator('[data-testid="kit-datatable-row"], tbody tr');
        await h.scrollTo(rows.first(), 'center');
        await h.expect.poll(() => rows.count(), { timeout: 30_000 }).toBeGreaterThanOrEqual(MIN_PRICED);
      }),
  ],
});
