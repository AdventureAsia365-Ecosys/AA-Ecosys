// Pilot rehearsal step 0 (root docs/ops/runbooks/pilot-rehearsal.md "Step 0: baseline"), read only.
// Given: the E2E CIS admin (read-only session). When: they open Platform > Apps, Jobs > Queue & workers and
// AI gateway > Budgets. Then: every app shows the version it runs, the job queue renders, and the platform caps and the
// tenant AI budgets render (each tenant row that is not one of the invented synthetic tenants is blurred before the
// first paint and the step fails if one shows unblurred). Nothing is written. $0.
// Not on camera (orchestrator, read only, in baseline.json): sts get-caller-identity, the ECS image per service, the
// CIS / Booking / CRM / TripPlanner job tables (idle; the queue page is filmed as the starting state, not asserted
// idle: recurring pulls may run at any moment), the pilot slot (SELECT slug FROM shared.tenants WHERE is_pilot: no row), the
// WordPress test site JSON check and the SES sandbox state. No page shows the pilot slot today.
const { HOSTS, step, ro, check, openTab, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');
const { syntheticRowPatterns } = require('../../lib/pilot-guard.cjs');

const TENANT_TIER = '[data-testid="ai-gateway-budgets-tenant-tier"]';

module.exports = ro({
  id: 'REH-00-baseline',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Pilot rehearsal, step 0: the baseline before the run',
  titleVi: 'Diễn tập pilot, bước 0: kiểm tra nền trước khi chạy',
  baseURL: HOSTS.cisAdmin,
  // Only the tenant budget table names tenants on these pages.
  allowRows: { rows: `${TENANT_TIER} [data-testid="kit-datatable-row"], ${TENANT_TIER} table tbody tr`, allow: syntheticRowPatterns() },
  steps: [
    step('Before the rehearsal, we check the platform. Apps shows each app and the version it runs.',
      'Trước buổi diễn tập, ta kiểm tra nền tảng. Trang Ứng dụng cho biết từng ứng dụng và phiên bản đang chạy.',
      async (page, h) => {
        await check(page, h, '/admin/platform/apps', { heading: 'Apps', ready: '[data-testid="platform-apps-ready"]' });
      }),
    step('The job queue shows what waits and which workers run: the starting state of the background work.',
      'Hàng đợi tác vụ cho biết việc nào đang chờ và worker nào đang chạy: trạng thái ban đầu của các tác vụ nền.',
      async (page, h) => {
        await check(page, h, '/admin/jobs', { heading: 'Jobs' });
        await openTab(page, h, 'Queue & workers', {
          url: /[?&]tab=queue\b/,
          shows: (p) => p.getByText('Queue by kind', { exact: true }),
        });
        await rowsOrEmpty(page, h);
      }),
    step('AI gateway, Budgets: the platform caps and each agency\'s AI budget, with this month\'s spend so far.',
      'Cổng AI, mục Ngân sách: các mức trần của nền tảng và ngân sách AI của từng đại lý, kèm mức chi từ đầu tháng.',
      async (page, h) => {
        await check(page, h, '/admin/ai-gateway?tab=budgets', { heading: 'AI gateway' });
        await h.expect(page.getByTestId('ai-gateway-budgets-central-tier')).toBeVisible({ timeout: 30_000 });
        const tenants = page.locator(TENANT_TIER);
        await h.scrollTo(tenants, 'center');
        await h.expect(tenants).toBeVisible({ timeout: 30_000 });
        await h.assertRowsFiltered();
      }),
    step('The spend caps and the call sites are in place. The baseline is recorded. This is the end of the scenario.',
      'Các mức trần chi tiêu và điểm gọi AI đã sẵn sàng. Mốc nền đã được ghi lại. Kết thúc kịch bản.',
      async (page, h) => {
        const sites = page.getByTestId('ai-gateway-budgets-call-sites');
        await h.scrollTo(sites, 'center');
        await h.expect(sites).toBeVisible({ timeout: 30_000 });
        await h.assertRowsFiltered();
      }),
  ],
});
