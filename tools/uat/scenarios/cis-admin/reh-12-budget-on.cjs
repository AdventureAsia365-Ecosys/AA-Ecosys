// Pilot rehearsal step 12 / X1, the staff evidence while the budget override is in force (root
// docs/ops/runbooks/pilot-rehearsal.md "X1: AI budget fails closed in three apps", item 1), read only.
// The override itself is an administrator's write (PUT .../entitlement-overrides/ai.budget_usd_monthly, 0.05 USD, reason
// and expiry; admin role, so the orchestrator through the admin route or the tech lead): the Dev-only E2E admin may not
// set it (root ADR 0006a A10b; gap G8). Record this right after it was set and before the studio, planner and CRM refusals are filmed (their own scenarios).
// Given: the E2E CIS admin (read-only session). When: they open the rehearsal agency's Subscription > Overrides and
// its Cost tab. Then: the override of ai.budget_usd_monthly is listed and active, and the Cost tab says the budget comes
// from that override. Nothing is written. $0.
const { HOSTS, step, ro, check, openTab } = require('../../lib/dryrun-page.cjs');
const { REHEARSAL } = require('../../lib/rehearsal-admin.cjs');

const KEY = 'ai.budget_usd_monthly';

module.exports = ro({
  id: 'REH-12-budget-on',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Pilot rehearsal, step 12: a tiny AI budget is in force for the agency',
  titleVi: 'Diễn tập pilot, bước 12: đại lý đang chịu một ngân sách AI rất nhỏ',
  baseURL: HOSTS.cisAdmin,
  steps: [
    step('To test that AI stops at the budget, an administrator set the agency\'s monthly AI budget to five cents.',
      'Để thử việc AI dừng khi chạm ngân sách, một quản trị viên đã đặt ngân sách AI hằng tháng của đại lý là năm xu.',
      async (page, h) => {
        await check(page, h, `/admin/tenants/${REHEARSAL.id}?tab=subscription`, { heading: REHEARSAL.name, ready: '[data-testid="tenant360-ready"]' });
        await openTab(page, h, 'Subscription');
        await h.expect(page.getByTestId(`tenant-subscription-${REHEARSAL.id}`)).toBeVisible({ timeout: 30_000 });
      }),
    step('The override is listed with its reason, who set it, and its end date. It is active.',
      'Mục ghi đè hiện trong danh sách, kèm lý do, người đặt và ngày kết thúc. Mục này đang có hiệu lực.',
      async (page, h) => {
        const ovs = page.getByTestId('tenant-overrides');
        await h.scrollTo(ovs, 'center');
        const row = ovs.locator('[data-testid="kit-datatable-row"], tbody tr').filter({ hasText: KEY }).first();
        await h.expect(row).toBeVisible({ timeout: 30_000 });
        await h.expect(row).toContainText('Active');
        await h.expect(row).toContainText(/0\.05/);
        // Columns (Tenant360Subscription.tsx ovCols): feature, value, reason, granted by, ends + Active/Ended badge.
        // The runbook (X1 item 1) asks for a reason and an expiry: the reason and "by" cells are not empty, and the
        // end cell holds a date, not the "—" of an override without an end.
        const cells = (await row.locator('td').allTextContents()).map((s) => s.replace(/\s+/g, ' ').trim());
        if (cells.length < 5) throw new Error(`the override row has ${cells.length} cells (expected 5)`);
        if (!cells[2]) throw new Error('the override has no reason');
        if (!cells[3]) throw new Error('the override does not say who set it');
        const ends = cells[4].replace(/\b(Active|Ended)\b/g, '').trim();
        if (!ends || ends === '—' || !/\d/.test(ends)) throw new Error('the override has no end date');
      }),
    step('The Cost tab says the budget now comes from that override. This is the end of the scenario.',
      'Thẻ Chi phí cho biết ngân sách hiện lấy từ mục ghi đè đó. Kết thúc kịch bản.',
      async (page, h) => {
        await openTab(page, h, 'Cost');
        const source = page.getByTestId('tenant-ai-budget-source');
        await h.expect(source).toBeVisible({ timeout: 30_000 });
        await h.expect(source).toContainText('Set by an override on the Subscription tab: it wins over the budget set here');
      }),
  ],
});
