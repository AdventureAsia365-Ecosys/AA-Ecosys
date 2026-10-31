// CRM review R14 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): suppliers and the bookings ledger.
// Given: A (owner) signed in; the agency has Adventure Asia (built in) and its own suppliers, and booking lines on its
//        trips (Dev data of earlier checks; names of old test rows that carry internal ids are blurred).
// When:  the owner opens Suppliers, then Bookings.
// Then:  Adventure Asia is pinned first and cannot be edited; own suppliers list without contact details; Bookings
//        lists every booked service with its supplier, status and confirmation, and the totals with the margin.
// Read only: no write, no reveal, no LLM call. Cost $0.
const { base, sha, open } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-14', title: 'Suppliers and the bookings ledger', titleVi: 'Nhà cung cấp và sổ đặt chỗ' });

sc.steps = [
  {
    caption: {
      en: 'Suppliers lists who the agency books with. Adventure Asia is built in and pinned first; the agency adds its own.',
      vi: 'Suppliers liệt kê các nhà cung cấp đại lý đặt dịch vụ. Adventure Asia có sẵn và luôn đứng đầu; đại lý tự thêm nhà cung cấp của mình.',
    },
    run: async (page, h) => {
      await sha(page, sc, 'start');
      await open(page, h, '/suppliers', 'suppliers-view');
      const aa = page.getByTestId('supplier-aa').first();
      await h.expect(aa).toBeVisible({ timeout: 15_000 });
      await h.expect(aa).toContainText('Adventure Asia');
      await h.hover(aa);
    },
  },
  {
    caption: {
      en: 'Contact names and e-mails are not in the list. Opening one asks for a reason and is logged, like client details.',
      vi: 'Tên và e-mail liên hệ không hiện trong danh sách. Muốn xem phải chọn lý do và được ghi lại, giống thông tin khách.',
    },
    run: async (page, h) => {
      const own = page.getByTestId('supplier-own');
      h.expect(await own.count()).toBeGreaterThan(0);
      await h.expect(page.getByTestId('suppliers-view')).not.toContainText('@');
      await h.scrollTo(own.first());
      await h.hover(own.first());
    },
  },
  {
    caption: {
      en: 'Bookings is the ledger of every service booked on the agency\'s trips: supplier, dates, status and confirmation number.',
      vi: 'Bookings là sổ ghi mọi dịch vụ đã đặt trên các chuyến của đại lý: nhà cung cấp, ngày, trạng thái và số xác nhận.',
    },
    run: async (page, h) => {
      await open(page, h, '/bookings', 'crm-bookings');
      const lines = page.getByTestId('bookings-lines');
      await h.expect(lines).toBeVisible({ timeout: 15_000 });
      h.expect(await lines.locator('tbody tr').count()).toBeGreaterThan(0);
      await h.scrollTo(lines);
      await h.hover(lines.locator('tbody tr').first());
    },
  },
  {
    caption: {
      en: 'The totals add up what is owed to suppliers and what the agency earns on top.',
      vi: 'Phần tổng cộng cộng dồn số tiền phải trả nhà cung cấp và phần đại lý được hưởng.',
    },
    run: async (page, h) => {
      const totals = page.getByTestId('bookings-totals');
      await h.scrollTo(totals);
      await h.expect(page.getByTestId('bookings-margin')).toBeVisible();
      await h.hover(page.getByTestId('bookings-margin'));
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
