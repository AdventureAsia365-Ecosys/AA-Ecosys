// Dry-run scenario CIS-08 (AA-1009, plan §4): Jobs and Cost Operations, read only.
// Given: the E2E CIS admin (read-only session). When: they open Jobs (two tabs), then Cost Operations (two tabs).
// Then: each tab shows its rows or its ready marker; no API call fails; nothing is written. The live Cost Explorer
// check is a POST, so the read-only guard would stop it: only stored snapshots are read. $0.
const { HOSTS, step, ro, check, openTab, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'CIS-08',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Jobs and Cost Operations',
  titleVi: 'Tác vụ nền và vận hành chi phí',
  baseURL: HOSTS.cisAdmin,
  steps: [
    step('Jobs lists the background work of the content platform, newest first.',
      'Trang Jobs liệt kê các tác vụ nền của nền tảng nội dung, mới nhất trước.',
      async (page, h) => {
        await check(page, h, '/admin/jobs', { heading: 'Jobs', table: true });
      }),
    step('The queue tab shows what is waiting and which workers are running.',
      'Thẻ hàng đợi cho biết việc nào đang chờ và worker nào đang chạy.',
      async (page, h) => {
        // Track tabs (no aria-selected): the tab is in the URL and only it renders the queue-by-kind table.
        await openTab(page, h, 'Queue & workers', {
          url: /[?&]tab=queue\b/,
          shows: (p) => p.getByText('Queue by kind', { exact: true }),
        });
        await rowsOrEmpty(page, h);
      }),
    step('Cost Operations shows what the platform spends, per provider and per day.',
      'Trang Vận hành chi phí cho biết nền tảng chi bao nhiêu, theo từng nhà cung cấp và từng ngày.',
      async (page, h) => {
        await check(page, h, '/admin/cost-ops', { heading: 'Cost Operations' });
      }),
    step('The AI and data spend tab shows the spend caps of the trip planner. This is the end of the scenario.',
      'Thẻ chi phí AI và dữ liệu hiển thị mức trần chi phí của trang lập kế hoạch chuyến đi. Kết thúc kịch bản.',
      async (page, h) => {
        // The merged spend tab (?tab=spend&view=llm|dfs|jev): its panel opens with the trip planner's caps.
        await openTab(page, h, 'AI & data spend', {
          url: /[?&]tab=spend\b/,
          shows: (p) => p.getByTestId('cost-spend-tab'),
        });
        await h.expect(page.getByTestId('cost-tp-caps')).toBeVisible({ timeout: 30_000 });
      }),
  ],
});
