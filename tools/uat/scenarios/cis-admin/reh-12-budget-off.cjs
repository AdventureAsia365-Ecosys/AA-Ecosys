// Pilot rehearsal step 12 / X1 item 5, the staff evidence after the reset (root docs/ops/runbooks/pilot-rehearsal.md
// "X1", and Teardown item 3), read only. The removal is an administrator's write (DELETE
// .../entitlement-overrides/ai.budget_usd_monthly; the orchestrator or the tech lead); record this right after it.
// Given: the E2E CIS admin (read-only session). When: they open the rehearsal agency's Subscription > Overrides and its
// Cost tab. Then: no override of ai.budget_usd_monthly is active any more, and the Cost tab no longer names the
// override as the budget's source. Nothing is written. $0.
const { HOSTS, step, ro, check, openTab } = require('../../lib/dryrun-page.cjs');
const { REHEARSAL } = require('../../lib/rehearsal-admin.cjs');

const KEY = 'ai.budget_usd_monthly';

module.exports = ro({
  id: 'REH-12-budget-off',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Pilot rehearsal, step 12: the AI budget is back to normal',
  titleVi: 'Diễn tập pilot, bước 12: ngân sách AI đã trở lại bình thường',
  baseURL: HOSTS.cisAdmin,
  steps: [
    step('After the test, an administrator removed the tiny budget. We check the agency again.',
      'Sau buổi thử, một quản trị viên đã gỡ ngân sách rất nhỏ. Ta kiểm tra lại đại lý.',
      async (page, h) => {
        await check(page, h, `/admin/tenants/${REHEARSAL.id}?tab=subscription`, { heading: REHEARSAL.name, ready: '[data-testid="tenant360-ready"]' });
        await openTab(page, h, 'Subscription');
        await h.expect(page.getByTestId(`tenant-subscription-${REHEARSAL.id}`)).toBeVisible({ timeout: 30_000 });
      }),
    step('No budget override is active any more.',
      'Không còn mục ghi đè ngân sách nào đang có hiệu lực.',
      async (page, h) => {
        const ovs = page.getByTestId('tenant-overrides');
        await h.scrollTo(ovs, 'center');
        await h.expect(ovs).toBeVisible({ timeout: 30_000 });
        const active = ovs.locator('[data-testid="kit-datatable-row"], tbody tr').filter({ hasText: KEY }).filter({ hasText: 'Active' });
        await h.expect(active).toHaveCount(0, { timeout: 30_000 });
      }),
    step('The Cost tab shows the budget from the plan or from staff again. This is the end of the scenario.',
      'Thẻ Chi phí lại cho thấy ngân sách lấy từ gói dịch vụ hoặc do nhân viên đặt. Kết thúc kịch bản.',
      async (page, h) => {
        await openTab(page, h, 'Cost');
        await h.expect(page.getByText(/AI budget \(this month\)/).first()).toBeVisible({ timeout: 30_000 });
        // The tile label renders before the budget read; the source line only once the effective budget has loaded
        // (Tenant360AiBudget.tsx), so wait for it before asserting what it says.
        const source = page.getByTestId('tenant-ai-budget-source');
        await h.expect(source).toBeVisible({ timeout: 30_000 });
        await h.expect(source).not.toContainText('Set by an override');
        await h.expect(source).toContainText(/^(From the plan's included AI spend|Set here)/);
      }),
  ],
});
