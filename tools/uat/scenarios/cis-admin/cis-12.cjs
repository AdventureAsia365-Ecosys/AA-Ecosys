// Dry-run scenario CIS-12 (AA-1009, plan §4): Writing memory, read only (no new run: that needs a model).
// Given: the E2E CIS admin (read-only session). When: they open Writing memory and walk its tabs.
// Then: each tab shows its rows or the empty state; no API call fails; nothing is written. $0.
// Pilot guard (AA-855): the lists name their owner, "Platform" or a tenant (a short id on Signals / Candidates, the
// tenant's name on Releases). Each row that is neither a platform row nor names an invented synthetic tenant is blurred
// before the first paint (scenario.allowRows, record.cjs), and each step fails if such a row shows unblurred.
const { HOSTS, step, ro, check, openTab, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');
const { syntheticRowPatterns } = require('../../lib/pilot-guard.cjs');

// The owner label of a platform row (AA-CIS-App frontend/lib/writingMemory.ts OWNER_TEXT, and its Vietnamese text).
// A row that carries a tenant owner label ("Tenant" + 8 hex) never passes on the word alone (e.g. inside a rule text).
const NO_TENANT_LABEL = '^(?![\\s\\S]*Tenant [0-9a-f]{8})[\\s\\S]*';
const PLATFORM_OWNER = [`${NO_TENANT_LABEL}\\bPlatform\\b`, `${NO_TENANT_LABEL}Nền tảng`];

module.exports = ro({
  id: 'CIS-12',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Writing memory: signals, candidate rules and releases',
  titleVi: 'Bộ nhớ viết: tín hiệu, quy tắc ứng viên và bản phát hành',
  baseURL: HOSTS.cisAdmin,
  allowRows: { rows: '[data-testid="kit-datatable-row"], table tbody tr', allow: [...syntheticRowPatterns(), ...PLATFORM_OWNER] },
  steps: [
    step('Writing memory collects what reviewers changed, so the writer learns from it.',
      'Bộ nhớ viết gom những gì người duyệt đã sửa để người viết học từ đó.',
      async (page, h) => {
        await check(page, h, '/admin/writing-memory', { heading: 'Writing memory', table: true });
        await h.assertRowsFiltered();
      }),
    step('Candidates are the rules drafted from repeated signals, waiting for a decision.',
      'Ứng viên là các quy tắc được soạn từ những tín hiệu lặp lại, đang chờ quyết định.',
      async (page, h) => {
        // Track tabs (no aria-selected, not in the URL): only the Candidates table has the rule "Status" filter.
        await openTab(page, h, 'Candidates', { shows: (p) => p.getByRole('combobox', { name: 'Status', exact: true }) });
        await rowsOrEmpty(page, h);
        await h.assertRowsFiltered();
      }),
    step('Releases list the rule sets the writer used over time. This is the end of the scenario.',
      'Bản phát hành liệt kê các bộ quy tắc người viết đã dùng theo thời gian. Kết thúc kịch bản.',
      async (page, h) => {
        // Only the Releases tab has the "Writers" section (memory switch and train close per writer).
        await openTab(page, h, 'Releases', { shows: (p) => p.getByRole('heading', { name: 'Writers', exact: true }) });
        await rowsOrEmpty(page, h);
        await h.assertRowsFiltered();
      }),
  ],
});
