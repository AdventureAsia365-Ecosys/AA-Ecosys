// UAT scenario PRT-13 (AA-855 round 1, catalogue.json, status after-lane): one sign-in, Content home, then the app
// switcher opens the CRM of the same agency. Waits for a synthetic tenant that holds Content AND the CRM add-on with
// one member in both (approving the add-on is a staff write); until then the catalogue keeps it after-lane and the dry
// run does not list it. Read only.
// Given: the Content studio member of that synthetic tenant (lib/signin.cjs studio), signed in once, unrecorded.
// When:  they open the Content dashboard, then "Open CRM" in the sidebar's Apps group.
// Then:  the CRM home of the same agency opens without a second sign-in; both sides pass the pilot guard (content and
//        crm scopes). Nothing is written. $0. Desktop 1440 x 900.
const { HOSTS, step, check, assertSignedIn } = require('../../lib/dryrun-page.cjs');
const { rw } = require('../../lib/uat-page.cjs');

// rw() without allowWrites: read only, and prepare() signs the member in (not a dry-run scenario while after-lane).
module.exports = rw({
  id: 'PRT-13',
  app: 'content-studio',
  identity: 'studio',
  pilotGuard: { scopes: ['content', 'crm'] },
  title: 'One sign-in: from Content to the CRM',
  titleVi: 'Một lần đăng nhập: từ Content sang CRM',
  baseURL: HOSTS.partner,
  steps: [
    step('One agency app holds both modules. The member starts in Content.',
      'Một ứng dụng đại lý chứa cả hai phân hệ. Thành viên bắt đầu ở Content.',
      async (page, h) => {
        await check(page, h, '/portal/dashboard', { heading: /Welcome back|Dashboard/ });
        await h.expect(page.getByTestId('portal-nav-group-apps')).toBeVisible({ timeout: 30_000 });
      }),
    step('The Apps group in the sidebar opens the CRM of the same agency.',
      'Nhóm Ứng dụng ở thanh bên mở CRM của cùng đại lý.',
      async (page, h) => {
        const link = page.getByTestId('portal-crm-link');
        await h.expect(link).toBeVisible({ timeout: 30_000 });
        await h.click(link);
        await page.waitForURL((u) => !u.pathname.startsWith('/portal/'), { timeout: 60_000 });
      }),
    step('The CRM opens without a second sign-in. This is the end of the scenario.',
      'CRM mở ra mà không cần đăng nhập lại. Kết thúc kịch bản.',
      async (page, h) => {
        assertSignedIn(page, HOSTS.partner);
        await h.expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible({ timeout: 30_000 });
      }),
  ],
});
