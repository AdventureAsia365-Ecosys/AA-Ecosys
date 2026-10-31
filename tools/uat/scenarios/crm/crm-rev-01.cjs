// CRM review R01 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): Home after sign-in.
// Given: A, the owner of the invented agency "Lữ hành Sen Vàng", already signed in (sign-in not recorded).
// When:  the owner lands on Home, reads the KPI tiles, the getting-started checklist and opens the bell.
// Then:  the welcome heading names the agency, five KPI tiles and the checklist progress show, the bell opens a list.
// Read only: no write, no LLM call. Cost $0.
const { base, sha, open } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-01', title: 'Home: KPIs, getting started and the bell', titleVi: 'Trang chủ: chỉ số, bước bắt đầu và chuông thông báo' });

sc.steps = [
  {
    caption: {
      en: 'The agency owner is signed in and lands on Home, which greets the agency by name.',
      vi: 'Chủ đại lý đã đăng nhập và vào trang Home, trang chào đúng tên đại lý.',
    },
    run: async (page, h) => {
      await sha(page, sc, 'start');
      await open(page, h, '/', 'crm-home');
      await h.expect(page.getByRole('heading', { level: 1 })).toContainText('Welcome · Lữ hành Sen Vàng');
    },
  },
  {
    caption: {
      en: 'Five tiles sum up the last twelve months: inquiries, win rate, sales, margin and the Adventure Asia share.',
      vi: 'Năm ô tóm tắt mười hai tháng qua: số yêu cầu, tỉ lệ chốt, doanh số, biên lợi nhuận và phần của Adventure Asia.',
    },
    run: async (page, h) => {
      const tiles = page.getByTestId('crm-home-tiles');
      await h.expect(tiles.locator('[data-testid^="reports-tile-"]')).toHaveCount(5);
      for (const k of ['inquiries', 'win_rate', 'revenue']) await h.hover(page.getByTestId(`reports-tile-${k}`));
    },
  },
  {
    caption: {
      en: 'Each tile explains how it is counted, so the numbers are never a guess.',
      vi: 'Mỗi ô có giải thích cách tính, nên con số không bao giờ là phỏng đoán.',
    },
    run: async (page, h) => {
      const info = page.getByTestId('reports-tile-win_rate').getByTestId('kpi-info-button');
      await h.hover(info); // hover shows the bubble (kit InfoTip)
      await h.expect(page.getByTestId('reports-tile-win_rate').getByTestId('kpi-info-text')).toBeVisible();
      await h.pause(1500);
      await page.mouse.move(700, 120);
    },
  },
  {
    caption: {
      en: 'Getting started lists the setup steps. The three required ones are done; the optional ones link to their setup pages.',
      vi: 'Mục Getting started liệt kê các bước thiết lập. Ba bước bắt buộc đã xong; các bước tuỳ chọn có link tới trang thiết lập.',
    },
    run: async (page, h) => {
      const list = page.getByTestId('crm-home-checklist');
      await h.scrollTo(list);
      await h.expect(page.getByTestId('crm-home-progress')).toContainText(/3\D+3/);
      await h.hover(page.getByTestId('crm-home-onboarding'));
    },
  },
  {
    caption: {
      en: 'The bell collects what happened while the team was away, such as a client opening or accepting a proposal.',
      vi: 'Chiếc chuông gom những việc xảy ra khi cả nhóm vắng mặt, ví dụ khách mở hoặc chấp nhận một đề xuất.',
    },
    run: async (page, h) => {
      await h.click(page.getByTestId('crm-bell').getByRole('button').first());
      await h.expect(page.getByTestId('crm-bell-list')).toBeVisible();
      await h.pause(2000);
      await page.keyboard.press('Escape');
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
