// Pilot rehearsal step 2, the staff side (root docs/ops/runbooks/pilot-rehearsal.md, step 2; onboarding Step 3),
// read only. The owner invitation itself is the tech lead's (only the admin role grants "owner"; the Dev-only E2E admin
// may invite a viewer or an editor on a synthetic tenant only, root ADR 0006a A10b-1), so it is not filmed here: the
// tech lead sends it from Tenant 360 > Members, the owner accepts it (agency-side scenarios), then this one is recorded.
// Given: the E2E CIS admin (read-only session). When: they open Members of the rehearsal agency and the Invite dialog,
// then close it unsent. Then: the dialog offers Viewer and Editor but not Owner to this session, and the members list
// shows the owner active. Nothing is written (no invitation is sent: the dialog is cancelled). $0.
// Run it after the owner accepted: before that the last step fails, which is the evidence that step 2 is not done.
const { HOSTS, step, ro, check, openTab } = require('../../lib/dryrun-page.cjs');
const { REHEARSAL } = require('../../lib/rehearsal-admin.cjs');

module.exports = ro({
  id: 'REH-02-members',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Pilot rehearsal, step 2: the agency owner is a member',
  titleVi: 'Diễn tập pilot, bước 2: chủ đại lý đã là thành viên',
  baseURL: HOSTS.cisAdmin,
  steps: [
    step('Members lists who can sign in to the agency\'s Content studio, and with which role.',
      'Trang Thành viên liệt kê ai được đăng nhập Content studio của đại lý, với vai trò nào.',
      async (page, h) => {
        await check(page, h, `/admin/tenants/${REHEARSAL.id}?tab=members`, { heading: REHEARSAL.name, ready: '[data-testid="tenant360-ready"]' });
        await openTab(page, h, 'Members');
        await h.expect(page.getByTestId('tenant360-members')).toBeVisible({ timeout: 30_000 });
      }),
    step('The test admin may invite a viewer or an editor, never an owner. The owner invitation is the tech lead\'s.',
      'Tài khoản quản trị thử nghiệm chỉ mời được người xem hoặc biên tập viên, không mời được chủ sở hữu. Lời mời chủ sở hữu do trưởng nhóm kỹ thuật gửi.',
      async (page, h) => {
        const invite = page.getByTestId('tenant360-members-invite').getByRole('button');
        await h.expect(invite).toBeVisible({ timeout: 30_000 });
        await h.click(invite);
        const dialog = page.getByTestId('tenant360-member-invite');
        await h.expect(dialog).toBeVisible({ timeout: 15_000 });
        const role = dialog.getByTestId('tenant360-member-role');
        await h.expect(role).toBeVisible({ timeout: 10_000 });
        await h.expect(role.locator('option', { hasText: 'Viewer' })).toHaveCount(1);
        await h.expect(role.locator('option', { hasText: 'Editor' })).toHaveCount(1);
        await h.expect(role.locator('option', { hasText: 'Owner' })).toHaveCount(0);
        await h.click(dialog.getByRole('button', { name: 'Cancel', exact: true }));
        await h.expect(dialog).toHaveCount(0, { timeout: 10_000 });
      }),
    step('After the tech lead\'s invitation, the owner is listed and active. This is the end of the scenario.',
      'Sau lời mời của trưởng nhóm kỹ thuật, chủ sở hữu đã có trong danh sách và đang hoạt động. Kết thúc kịch bản.',
      async (page, h) => {
        const owner = page.getByTestId('tenant360-members').locator('[data-testid="kit-datatable-row"], tbody tr')
          .filter({ hasText: 'Owner' }).filter({ hasText: 'Active' }).first();
        await h.expect(owner).toBeVisible({ timeout: 30_000 });
      }),
  ],
});
