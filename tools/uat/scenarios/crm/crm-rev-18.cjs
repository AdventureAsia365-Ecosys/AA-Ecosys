// CRM review R18 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): the assistant's view.
// Given: B, the assistant of the invented agency "Lữ hành Sen Vàng", signed in outside the recording.
// When:  the assistant opens Home, looks at the menu, opens Commissions by its address, then Bookings and Team.
// Then:  the shell names the role; Commissions and Marketing are not in the menu and the page says "not available for
//        your role"; Bookings shows no cost or margin; Team says only the owner manages it. (The API enforces the same
//        rules; the screens only follow them.)
// Read only: no write, no LLM call. Cost $0.
const { base, sha, open } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-18', title: 'The assistant\'s view: what a role cannot see', titleVi: 'Góc nhìn của trợ lý: những gì một vai trò không thấy', who: 'B' });

sc.steps = [
  {
    caption: {
      en: 'Now the same agency through the eyes of its assistant, who handles clients and trips but not money decisions.',
      vi: 'Giờ là cùng đại lý đó dưới góc nhìn của trợ lý, người lo khách và chuyến đi nhưng không quyết các việc về tiền.',
    },
    run: async (page, h) => {
      await sha(page, sc, 'start');
      await open(page, h, '/', 'crm-home');
      await h.expect(page.getByTestId('crm-agency')).toContainText(/assistant/i);
      await h.hover(page.getByTestId('crm-agency'));
    },
  },
  {
    caption: {
      en: 'The menu has no Commissions and no Marketing for this role.',
      vi: 'Với vai trò này, menu không có Commissions và Marketing.',
    },
    run: async (page, h) => {
      const nav = page.locator('[data-crm="nav-item"]');
      await h.expect(nav.filter({ hasText: 'Pipeline' }).first()).toBeVisible();
      await h.expect(nav.filter({ hasText: /^Commissions$/ })).toHaveCount(0);
      await h.expect(nav.filter({ hasText: /^Marketing$/ })).toHaveCount(0);
      await h.hover(nav.filter({ hasText: 'Payments' }).first());
    },
  },
  {
    caption: {
      en: 'Typing the address of Commissions directly only shows that it is not available for this role.',
      vi: 'Gõ thẳng địa chỉ trang Commissions cũng chỉ thấy thông báo trang này không dành cho vai trò này.',
    },
    run: async (page, h) => {
      await open(page, h, '/commissions', 'crm-section-forbidden');
      await h.expect(page.getByTestId('crm-section-forbidden')).toContainText(/not available|role/i);
      await h.pause(1500);
    },
  },
  {
    caption: {
      en: 'Bookings shows the services and the selling prices, but no cost and no margin.',
      vi: 'Trang Bookings hiện dịch vụ và giá bán, nhưng không có giá vốn và biên lợi nhuận.',
    },
    run: async (page, h) => {
      await open(page, h, '/bookings', 'crm-bookings');
      await h.expect(page.getByTestId('bookings-lines')).toBeVisible({ timeout: 15_000 });
      await h.expect(page.getByTestId('bookings-margin')).toHaveCount(0);
      await h.hover(page.getByTestId('bookings-lines').locator('tbody tr').first());
    },
  },
  {
    caption: {
      en: 'Team and roles are the owner\'s to manage. The rules shown here are enforced by the server too, not only hidden on screen.',
      vi: 'Nhóm và vai trò do chủ đại lý quản lý. Các quy tắc này được máy chủ kiểm tra, chứ không chỉ ẩn đi trên màn hình.',
    },
    run: async (page, h) => {
      await open(page, h, '/settings/team', 'team-owner-only');
      await h.hover(page.getByTestId('team-owner-only'));
      // The same rule on the server: the team list (owner only) is refused to the assistant.
      const r = await page.request.get(`${sc.baseURL}/bff/team`, { headers: { Accept: 'application/json' } });
      h.expect(r.status(), 'GET /team as the assistant').toBe(403);
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
