// Dry-run scenario CRM-07 (AA-1009, plan §4): settings, reports and the calendar, read only (no setting changed).
// Given: the CRM owner (identity A). When: they open Settings, Reports and Calendar. Then: each renders its title and
// its first section; no BFF call fails; nothing is written. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'CRM-07',
  app: 'crm',
  identity: 'crm',
  title: 'Settings, reports and calendar',
  titleVi: 'Cài đặt, báo cáo và lịch',
  baseURL: HOSTS.partner,
  scrollBlock: 'center',
  steps: [
    step('Settings hold the agency profile, the team and the connections.',
      'Cài đặt chứa hồ sơ đại lý, đội ngũ và các kết nối.',
      async (page, h) => {
        await check(page, h, '/settings', { heading: 'Settings', ready: '[data-testid="crm-settings"]' });
        await h.expect(page.getByTestId('settings-agency-name').first()).toBeVisible({ timeout: 30_000 });
      }),
    step('Reports show the funnel, the outcomes and the money of the period.',
      'Báo cáo hiển thị phễu bán hàng, kết quả và doanh thu của kỳ.',
      async (page, h) => {
        await check(page, h, '/reports', { heading: 'Reports', ready: '[data-testid="crm-reports"]' });
      }),
    step('The calendar shows departures and tasks by month. This is the end of the scenario.',
      'Lịch hiển thị chuyến khởi hành và công việc theo tháng. Kết thúc kịch bản.',
      async (page, h) => {
        await check(page, h, '/calendar', { heading: 'Calendar', ready: '[data-testid="crm-calendar"]' });
      }),
  ],
});
