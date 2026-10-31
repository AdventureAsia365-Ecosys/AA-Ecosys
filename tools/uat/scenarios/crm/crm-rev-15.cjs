// CRM review R15 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): reports.
// Given: A (owner) signed in; the agency's Dev data (counts drift, so only the structure is asserted).
// When:  the owner opens Reports: the tiles, the funnel, money and payments (what clients still owe), the team, the
//        "how the CRM is working for you" list, and downloads one section as CSV.
// Then:  every panel renders; the CSV download arrives with a report-*.csv name; the not-built measures say "Coming
//        later"; a "Not ready yet" card names what is missing (the measures of unbuilt modules, AA insights in CIS).
// Read only (one CSV download, kept in memory and dropped; an access-log event per download). No LLM call. Cost $0.
const slide = require('../../lib/slide.cjs');
const { base, sha, open, choose } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-15', title: 'Reports: funnel, money, what clients owe, the team and CSV export' });

sc.steps = [
  {
    caption: {
      en: 'Reports starts with the same tiles as Home, then the funnel: how many inquiries become proposals and bookings.',
      vi: 'Trang Reports mở đầu bằng các ô như ở Home, rồi tới phễu: bao nhiêu yêu cầu thành đề xuất và thành booking.',
    },
    run: async (page, h) => {
      await sha(page, sc, 'start');
      await open(page, h, '/reports', 'crm-reports');
      await h.expect(page.getByTestId('reports-tiles')).toBeVisible({ timeout: 15_000 });
      const funnel = page.getByTestId('reports-funnel');
      await h.scrollTo(funnel);
      await h.hover(funnel);
    },
  },
  {
    caption: {
      en: 'Money shows sales, costs and margin. Payments shows what clients have paid and what they still owe.',
      vi: 'Phần Money cho thấy doanh số, chi phí và biên lợi nhuận. Phần Payments cho thấy khách đã trả bao nhiêu và còn nợ bao nhiêu.',
    },
    run: async (page, h) => {
      for (const id of ['reports-money', 'reports-payments']) {
        const p = page.getByTestId(id);
        await h.scrollTo(p);
        await h.expect(p).toBeVisible();
        await h.hover(p);
      }
    },
  },
  {
    caption: {
      en: 'The team view compares each person\'s trips, replies and bookings.',
      vi: 'Phần Team so sánh số chuyến, số lần trả lời và số booking của từng người.',
    },
    run: async (page, h) => {
      const team = page.getByTestId('reports-team');
      await h.scrollTo(team);
      await h.expect(team).toBeVisible();
      await h.hover(team);
    },
  },
  {
    caption: {
      en: 'Any section downloads as a spreadsheet file. Every download is logged.',
      vi: 'Phần nào cũng tải về được dưới dạng file bảng tính. Mỗi lần tải đều được ghi lại.',
    },
    run: async (page, h) => {
      const menu = page.getByTestId('reports-export');
      await h.scrollTo(menu);
      await choose(h, menu.locator('select'), 'funnel');
      const dl = page.waitForEvent('download', { timeout: 30_000 });
      await h.click(menu.getByRole('button'));
      const file = await dl;
      h.expect(file.suggestedFilename()).toMatch(/^report-funnel-.+\.csv$/);
      await file.cancel().catch(() => {});
    },
  },
  {
    caption: {
      en: 'How the CRM is working for you: each measure has a target. Measures of parts not built yet say Coming later.',
      vi: 'Mục How the CRM is working for you: mỗi chỉ số có mục tiêu. Chỉ số của các phần chưa làm ghi Coming later.',
    },
    run: async (page, h) => {
      const ok = page.getByTestId('reports-success');
      await h.scrollTo(ok);
      h.expect(await ok.locator('li').count()).toBeGreaterThan(3);
      await h.expect(ok.getByText('Coming later').first()).toBeVisible();
      await h.hover(ok.getByText('Coming later').first());
    },
  },
  {
    caption: {
      en: 'Not ready yet: the measures of the modules still to build, and the Adventure Asia insights page that gathers agencies\' anonymous numbers.',
      vi: 'Chưa có: chỉ số của các phần chưa làm, và trang thống kê của Adventure Asia gom số liệu ẩn danh của các đại lý.',
    },
    run: async (page, h) => {
      await slide.notReady(page, h, {
        screen: 'More reports',
        missing: [
          'Measures for workflows, commissions and AI help, which are not built yet',
          'The Adventure Asia insights page, built from the anonymous totals agencies choose to share',
        ],
      });
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
