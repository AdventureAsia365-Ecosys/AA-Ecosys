// Pilot rehearsal step 1, the result (root docs/ops/runbooks/pilot-rehearsal.md, step 1 and "Fixtures"), read only.
// The create itself is not filmed: no E2E identity may create a tenant (root ADR 0006a A10b-4); the fixture
// `e2e_fixtures rehearsal-tenant` (CIS) and the CRM seed made pilot-rehearsal-01 before the run.
// Given: the E2E CIS admin (read-only session). When: they open Tenant 360 of the synthetic rehearsal agency, its
// Subscription tab, then its Billing tab. Then: the tenant is kind demo and not the pilot, in service, with the Content
// plan and the CRM and TripPlanner add-ons live; Booking answers for it (its partner row, or "no invoice terms yet",
// never "cannot be read"). Nothing is written. $0. The CRM agency is REH-01-crm-agency, the Booking side
// REH-01-booking-partner.
const { HOSTS, step, ro, check, openTab } = require('../../lib/dryrun-page.cjs');
const { REHEARSAL } = require('../../lib/rehearsal-admin.cjs');

// The status badge's own text (the row text runs the cells together).
const LIVE = /^\s*(active|trialing)\s*$/i;

module.exports = ro({
  id: 'REH-01-provisioned',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Pilot rehearsal, step 1: the rehearsal agency is provisioned',
  titleVi: 'Diễn tập pilot, bước 1: đại lý diễn tập đã được khởi tạo',
  baseURL: HOSTS.cisAdmin,
  steps: [
    step('Tenant 360 of the rehearsal agency. It is an invented agency, made for this rehearsal only.',
      'Trang Tenant 360 của đại lý diễn tập. Đây là một đại lý giả lập, chỉ tạo cho buổi diễn tập này.',
      async (page, h) => {
        await check(page, h, `/admin/tenants/${REHEARSAL.id}`, { heading: REHEARSAL.name, ready: '[data-testid="tenant360-ready"]' });
      }),
    step('The Subscription tab: kind demo, in service, and not marked as the pilot.',
      'Thẻ Gói dịch vụ: loại demo, đang hoạt động, và không bị đánh dấu là pilot.',
      async (page, h) => {
        await openTab(page, h, 'Subscription');
        const box = page.getByTestId(`tenant-subscription-${REHEARSAL.id}`);
        await h.expect(box).toBeVisible({ timeout: 30_000 });
        await h.expect(box.getByText('Kind: demo', { exact: true })).toBeVisible({ timeout: 30_000 });
        await h.expect(box.getByText('In service', { exact: true })).toBeVisible();
        await h.expect(box.getByText(/Pilot until/)).toHaveCount(0);
      }),
    step('It holds the Content plan and two add-ons, the CRM and TripPlanner, all live.',
      'Đại lý có gói Nội dung và hai tiện ích bổ sung là CRM và TripPlanner, tất cả đang hoạt động.',
      async (page, h) => {
        const subs = page.getByTestId('tenant-subscriptions');
        await h.scrollTo(subs, 'center');
        for (const product of ['Content', 'CRM', 'TripPlanner']) {
          // The first cell is the product name (the row text runs the cells together, so no word boundary after it).
          const row = subs.locator('[data-testid="kit-datatable-row"], tbody tr')
            .filter({ has: page.locator('td:first-child', { hasText: new RegExp(`^\\s*${product}\\s*$`) }) }).first();
          await h.expect(row, `${product} subscription`).toBeVisible({ timeout: 30_000 });
          await h.expect(row.getByText(LIVE).first(), `${product} is live`).toBeVisible();
        }
        await h.expect(subs).toContainText('crm.core');
        await h.expect(subs).toContainText('tripplanner.hosted');
      }),
    step('The Billing tab reads the agency from Booking: Booking already knows it. This is the end of the scenario.',
      'Thẻ Thanh toán đọc đại lý từ Booking: Booking đã biết đại lý này. Kết thúc kịch bản.',
      async (page, h) => {
        await openTab(page, h, 'Billing');
        const panel = page.getByTestId('t360-booking-billing');
        await h.expect(panel).toBeVisible({ timeout: 30_000 });
        await h.expect(page.getByTestId('t360-booking-status').or(page.getByTestId('t360-booking-no-row')).first())
          .toBeVisible({ timeout: 30_000 });
        await h.expect(page.getByTestId('t360-booking-unavailable')).toHaveCount(0);
      }),
  ],
});
