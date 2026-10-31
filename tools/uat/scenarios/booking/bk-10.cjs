// Dry-run scenario BK-10 (AA-1009, plan §4): customers, the audit log and the staff list, read only.
// Given: the E2E Booking staff (read-only session). When: they open each list. Then: each renders its rows or the
// empty state; no API call fails; nothing is written. $0.
const { HOSTS, step, ro, check, assertNoApiErrors } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'BK-10',
  app: 'booking',
  identity: 'booking',
  title: 'Customers, audit log and staff',
  titleVi: 'Khách hàng, nhật ký kiểm toán và nhân viên',
  baseURL: HOSTS.booking,
  steps: [
    step('Customers lists every traveller and agency the team works with.',
      'Trang Khách hàng liệt kê mọi khách du lịch và đại lý mà đội làm việc cùng.',
      async (page, h) => {
        await check(page, h, '/customers', { heading: 'Customers', table: true });
      }),
    step('The audit log records who changed what, and when.',
      'Nhật ký kiểm toán ghi lại ai đã thay đổi gì và khi nào.',
      async (page, h) => {
        // The audit log is a list (li[data-testid=audit-row]), not a table: an entry, or the real "nothing yet" /
        // "no match" empty state. The no-access empty state is a failure, not an empty list.
        await check(page, h, '/audit-log', { heading: 'Audit log' });
        await h.expect(page.getByTestId('audit-row')
          .or(page.getByText(/^(No audited actions yet|No entries match these filters)$/)).first())
          .toBeVisible({ timeout: 30_000 });
        await h.expect(page.getByText('You do not have access to the audit log')).toHaveCount(0);
        assertNoApiErrors(page);
      }),
    step('The staff list shows each team member and their role. Sign-in is managed in CIS. This is the end of the scenario.',
      'Danh sách nhân viên hiển thị từng thành viên và vai trò. Việc đăng nhập do CIS quản lý. Kết thúc kịch bản.',
      async (page, h) => {
        await check(page, h, '/staff', { heading: 'Staff', table: true });
      }),
  ],
});
