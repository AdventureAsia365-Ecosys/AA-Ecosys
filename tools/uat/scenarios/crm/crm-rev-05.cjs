// CRM review R05 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): the client profile (Client 360).
// Given: A (owner) signed in; the R03 trip and its lead (work/crm/state.json r03).
// When:  the owner opens the lead's profile from the trip, reveals the e-mail with a reason, reads consent and the
//        banded profile, and checks the access log.
// Then:  identity fields are masked until revealed; the reveal shows the address; the access log lists the reveal.
// One reveal (an audit event) on an invented client; no LLM call. Cost $0.
const { st, base, sha, open, choose } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-05', title: 'Client profile: masked by default, every reveal logged', titleVi: 'Hồ sơ khách: che sẵn, mỗi lần xem đều được ghi lại' });
let s;
let travelerId;

sc.steps = [
  {
    caption: {
      en: 'From the trip, the owner opens the profile of the lead traveller.',
      vi: 'Từ trang chuyến, chủ đại lý mở hồ sơ của khách đứng tên.',
    },
    run: async (page, h) => {
      s = st.load();
      if (!s.r03) throw new Error('no R03 trip: run crm-rev-03 first');
      await sha(page, sc, 'start');
      await open(page, h, `/pipeline/${s.r03.trip_id}`, 'crm-trip');
      const link = page.getByTestId('trip-party').getByRole('link', { name: s.r03.lead_name });
      await h.scrollTo(link);
      await h.click(link);
      await page.waitForURL(/\/clients\/[0-9a-f-]{36}$/);
      travelerId = page.url().split('/').pop();
      await h.expect(page.getByTestId('client-name')).toHaveText(s.r03.lead_name);
    },
  },
  {
    caption: {
      en: 'Identity and contact details are masked by default, even for the owner.',
      vi: 'Thông tin danh tính và liên hệ được che theo mặc định, kể cả với chủ đại lý.',
    },
    run: async (page, h) => {
      const id = page.getByTestId('client-identity');
      await h.expect(id).toBeVisible();
      await h.expect(id).not.toContainText(s.r03.email);
      await h.hover(page.getByTestId('reveal-email'));
    },
  },
  {
    caption: {
      en: 'To see the e-mail, the owner picks a reason first. Only then is the address shown, and the view is logged.',
      vi: 'Muốn xem e-mail, chủ đại lý phải chọn lý do trước. Sau đó địa chỉ mới hiện ra, và lần xem được ghi lại.',
    },
    run: async (page, h) => {
      const email = page.getByTestId('reveal-email').first();
      await h.click(email.getByTestId('show-email').getByRole('button'));
      await choose(h, email.getByTestId('reveal-reason-email'), 'contact_client');
      await h.click(email.getByTestId('reveal-show-email').getByRole('button'));
      await h.expect(page.getByTestId('revealed-email')).toHaveText(s.r03.email, { timeout: 15_000 });
    },
  },
  {
    caption: {
      en: 'Consent is recorded per channel, and the travel profile keeps only bands, not raw personal details.',
      vi: 'Sự đồng ý được ghi theo từng kênh, và hồ sơ du lịch chỉ giữ các mức khoảng, không giữ chi tiết cá nhân thô.',
    },
    run: async (page, h) => {
      await h.scrollTo(page.getByTestId('client-consent'));
      await h.expect(page.getByTestId('client-consent')).toBeVisible();
      await h.scrollTo(page.getByTestId('client-profile'));
      await h.expect(page.getByTestId('client-profile')).toBeVisible();
    },
  },
  {
    caption: {
      en: 'The profile links every trip of this client.',
      vi: 'Hồ sơ liên kết tới mọi chuyến của khách này.',
    },
    run: async (page, h) => {
      const trips = page.getByTestId('client-trips');
      await h.scrollTo(trips);
      await h.expect(trips.locator(`a[href$="/pipeline/${s.r03.trip_id}"]`)).toHaveCount(1);
      await h.hover(trips.locator(`a[href$="/pipeline/${s.r03.trip_id}"]`));
    },
  },
  {
    caption: {
      en: 'In Settings, the access log shows who opened what and why, including the reveal a moment ago.',
      vi: 'Trong Settings, nhật ký truy cập cho biết ai đã mở gì và vì sao, gồm cả lần xem e-mail vừa rồi.',
    },
    run: async (page, h) => {
      await open(page, h, '/settings/access-log', 'access-log-list');
      const row = page.getByTestId('access-log-row').filter({ hasText: travelerId.slice(0, 8) }).filter({ hasText: /reveal|contact_client/i });
      await h.expect(row.first()).toBeVisible({ timeout: 15_000 });
      await h.hover(row.first());
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
