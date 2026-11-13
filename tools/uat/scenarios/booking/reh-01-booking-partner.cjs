// Pilot rehearsal step 1, the Booking side (root docs/ops/runbooks/pilot-rehearsal.md, step 1 "Booking partner within
// about 5 minutes (bk_tenant_pull)"), read only.
// Given: the E2E Booking admin (A10a, read-only session). When: they open Agency tiers, then the rehearsal agency's
// tariff, found by its name through the same read the Agencies tab uses (the list itself is not shown: it names every
// agency). Then: Booking holds the agency as an active partner projected from CIS, with a tier, and its tariff page
// opens. Nothing is written. $0. The priced tours on that tariff are REH-01-prices.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');
const { REHEARSAL } = require('../../lib/rehearsal-admin.cjs');

let partner = null;

module.exports = ro({
  id: 'REH-01-booking-partner',
  app: 'booking',
  identity: 'booking',
  title: 'Pilot rehearsal, step 1: Booking knows the rehearsal agency',
  titleVi: 'Diễn tập pilot, bước 1: Booking đã biết đại lý diễn tập',
  baseURL: HOSTS.booking,
  steps: [
    step('Booking takes each agency from the content platform by itself, with a price tier.',
      'Booking tự nhận từng đại lý từ nền tảng nội dung, kèm một hạng giá.',
      async (page, h) => {
        await check(page, h, '/pricing/agency-tiers', { heading: 'Agency tiers', table: true });
        const res = await page.request.get(`${HOSTS.booking}/api/booking/pricing/partner-terms`, { headers: { Accept: 'application/json' }, timeout: 30_000 });
        if (res.status() !== 200) throw new Error(`the agency list answered ${res.status()}`);
        const items = ((await res.json()) || {}).items || [];
        const mine = items.filter((p) => p && p.agency_name === REHEARSAL.name);
        if (mine.length !== 1) throw new Error(`Booking lists ${mine.length} partners named ${REHEARSAL.name} (expected 1)`);
        [partner] = mine;
        if (partner.status !== 'active') throw new Error(`the rehearsal partner is ${partner.status}, not active`);
        if (partner.projected !== true) throw new Error('the rehearsal partner was not projected from CIS');
      }),
    step('The rehearsal agency has its own tariff page: the price it pays, per tour and group size.',
      'Đại lý diễn tập có trang bảng giá riêng: giá đại lý trả theo từng tour và cỡ nhóm.',
      async (page, h) => {
        await check(page, h, `/pricing/agency-tiers/tariff?partner=${encodeURIComponent(partner.id)}`, { heading: `Tariff: ${REHEARSAL.name}` });
        await h.expect(page.getByText(`${partner.tier_label} tier.`, { exact: false }).first()).toBeVisible({ timeout: 30_000 });
      }),
    step('The partner is active and follows the content platform. This is the end of the scenario.',
      'Đối tác đang hoạt động và đồng bộ theo nền tảng nội dung. Kết thúc kịch bản.',
      async (page, h) => {
        const prices = page.getByText('Prices', { exact: true }).first();
        await h.scrollTo(prices, 'center');
        await h.expect(prices).toBeVisible({ timeout: 30_000 });
      }),
  ],
});
