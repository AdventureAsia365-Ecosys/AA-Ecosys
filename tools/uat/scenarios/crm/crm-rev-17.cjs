// CRM review R17 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): settings, language and dark mode.
// Given: A (owner) signed in.
// When:  the owner walks Settings: the overview, the team, the inquiry forms, the mailbox (its address blurred) and
//        payment methods; switches the interface to Vietnamese and back; switches to dark mode and back.
// Then:  each settings page renders its main block; the shell turns Vietnamese (html lang="vi", "Quy trình bán") and
//        back to English; <html data-theme> becomes dark and returns to the starting choice.
// Read only on the server (no invite sent, no setting saved); the locale is a cookie of this browser only. No LLM
// call. Cost $0.
const { base, sha, open, choose } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-17', title: 'Settings, Vietnamese and dark mode', titleVi: 'Cài đặt, tiếng Việt và giao diện tối' });
let startTheme;

const themeButton = (page) => page.getByRole('button', { name: /^Theme: |^Giao diện: / });

sc.steps = [
  {
    caption: {
      en: 'Settings gathers the agency\'s setup on one page: team, agreements, forms, mailbox, payments, data and the access log.',
      vi: 'Settings gom mọi thiết lập của đại lý vào một trang: nhóm, giấy tờ, form, hộp thư, thanh toán, dữ liệu và nhật ký truy cập.',
    },
    run: async (page, h) => {
      await sha(page, sc, 'start');
      await open(page, h, '/settings', 'crm-settings');
      await h.expect(page.getByTestId('settings-agency-name')).toContainText('Lữ hành Sen Vàng');
      for (const id of ['settings-team', 'settings-payments']) await h.hover(page.getByTestId(id));
    },
  },
  {
    caption: {
      en: 'The team: the owner and an assistant, each with a role that decides what they can see and do. Invitations go out from here.',
      vi: 'Nhóm làm việc: chủ đại lý và một trợ lý, mỗi người một vai trò quyết định họ được xem và làm gì. Lời mời được gửi từ đây.',
    },
    run: async (page, h) => {
      await open(page, h, '/settings/team', 'team-admin');
      const rows = page.getByTestId('team-member-row');
      h.expect(await rows.count()).toBeGreaterThanOrEqual(2);
      await h.hover(rows.first());
      await h.scrollTo(page.getByTestId('team-invite'));
      await h.hover(page.getByTestId('team-invite-role')); // never sent
    },
  },
  {
    caption: {
      en: 'Inquiry forms: the agency puts this form on its own website. A link per form, and the planning questions it sends later.',
      vi: 'Form yêu cầu tư vấn: đại lý đặt form này trên website của mình. Mỗi form một đường dẫn, kèm câu hỏi lên kế hoạch gửi sau.',
    },
    run: async (page, h) => {
      await open(page, h, '/settings/forms');
      const item = page.getByTestId('forms-item').first();
      await h.expect(item).toBeVisible({ timeout: 15_000 });
      await h.hover(item);
    },
  },
  {
    caption: {
      en: 'Mailbox: the agency connects its own e-mail account, and pays its own provider. The address is hidden here.',
      vi: 'Hộp thư: đại lý kết nối tài khoản e-mail của chính mình và tự trả phí cho nhà cung cấp. Địa chỉ được che ở đây.',
    },
    run: async (page, h) => {
      await open(page, h, '/settings/mailbox', 'mailbox-settings');
      await h.expect(page.getByTestId('mailbox-billing')).toBeVisible();
      await h.hover(page.getByTestId('mailbox-settings').locator('[data-testid$="-address"]').first());
      await h.assertMasked(['[data-testid^="mailbox-"][data-testid$="-address"]']);
    },
  },
  {
    caption: {
      en: 'Payments: the bank details clients see, and the payment providers. Card payments are not available yet.',
      vi: 'Thanh toán: thông tin ngân hàng khách nhìn thấy, và các nhà cung cấp thanh toán. Thanh toán thẻ hiện chưa có.',
    },
    run: async (page, h) => {
      await open(page, h, '/settings/payments', 'crm-payments-settings');
      const providers = page.getByTestId('payment-providers');
      await h.scrollTo(providers);
      await h.expect(providers).toBeVisible();
      await h.hover(providers);
    },
  },
  {
    caption: {
      en: 'The whole interface also works in Vietnamese. Each person picks their language at the top.',
      vi: 'Toàn bộ giao diện cũng dùng được bằng tiếng Việt. Mỗi người tự chọn ngôn ngữ ở thanh trên cùng.',
    },
    run: async (page, h) => {
      const sel = page.getByTestId('locale-select').first();
      await choose(h, sel, 'vi-VN');
      await page.waitForLoadState('load');
      await h.expect(page.locator('html')).toHaveAttribute('lang', 'vi', { timeout: 20_000 });
      await h.expect(page.getByRole('link', { name: 'Quy trình bán' }).first()).toBeVisible();
      await h.pause(2500);
      await choose(h, page.getByTestId('locale-select').first(), 'en-AU');
      await page.waitForLoadState('load');
      await h.expect(page.locator('html')).toHaveAttribute('lang', 'en', { timeout: 20_000 });
    },
  },
  {
    caption: {
      en: 'And a dark mode for late evenings, then back to light.',
      vi: 'Và chế độ tối cho những buổi làm việc khuya, rồi quay lại chế độ sáng.',
    },
    run: async (page, h) => {
      const theme = () => page.evaluate(() => document.documentElement.getAttribute('data-theme'));
      startTheme = ((await themeButton(page).getAttribute('aria-label')) || '').split(': ')[1];
      for (let i = 0; i < 3 && (await theme()) !== 'dark'; i++) await h.click(themeButton(page));
      h.expect(await theme()).toBe('dark');
      await h.pause(2500);
      for (let i = 0; i < 3 && !((await themeButton(page).getAttribute('aria-label')) || '').endsWith(`: ${startTheme}`); i++) await h.click(themeButton(page));
      h.expect(await themeButton(page).getAttribute('aria-label')).toMatch(new RegExp(`: ${startTheme}$`));
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
