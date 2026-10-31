// CRM review R12 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): duty of care and the calendar.
// Given: A (owner) signed in; R10 booked the invoice trip, which starts within 14 days (prep dates it today + 12).
// When:  the owner opens Travelling now for 14 days (the trip, its region, the "reach travellers" list with names
//        hidden), the calendar month of the trip, and creates a personal calendar (ICS) feed.
// Then:  the trip shows under its region with "leaves on"; the reach list is there without names; the calendar has the
//        trip's events; the feed is active and its URL is blurred (it is a credential). The AA incident banner and
//        calendar sync with Google / Microsoft are not built for this review: "Not ready yet" card.
// Writes: one ICS feed (id kept in work/crm/state.json for cleanup.cjs, which revokes it). No reveal, no LLM call.
// A re-run with an active feed skips the create in --fast only. Cost $0.
const slide = require('../../lib/slide.cjs');
const { st, base, sha, open, bffOk, reuse } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-12', title: 'Duty of care and the calendar: who travels where, and a private calendar feed' });
let s;
let t;

sc.steps = [
  {
    caption: {
      en: 'Travelling now lists every booked trip in the next two weeks, grouped by region, with the day each group is on.',
      vi: 'Travelling now liệt kê mọi chuyến đã đặt trong hai tuần tới, nhóm theo khu vực, kèm ngày thứ mấy của mỗi đoàn.',
    },
    run: async (page, h) => {
      s = st.load();
      t = s.invoice_trip;
      if (!s.r10 || s.r10.trip_id !== t.trip_id) throw new Error('no booked R10 trip: run crm-rev-10 first');
      await sha(page, sc, 'start');
      await open(page, h, '/travelling?days=14', 'crm-travelling');
      const trip = page.getByTestId(`duty-trip-${t.trip_id}`);
      await h.expect(trip).toBeVisible({ timeout: 15_000 });
      await h.scrollTo(trip);
      await h.hover(trip.getByRole('link').first());
    },
  },
  {
    caption: {
      en: 'Reach travellers here gathers the people in a region. Their names stay hidden until the agency opens them, with the reason logged.',
      vi: 'Mục Reach travellers here gom những người đang ở một khu vực. Tên được ẩn cho tới khi đại lý mở ra, và lý do được ghi lại.',
    },
    run: async (page, h) => {
      const region = page.locator('[data-testid^="duty-region-"]').filter({ has: page.getByTestId(`duty-trip-${t.trip_id}`) });
      const summary = region.locator('summary').first();
      await h.scrollTo(summary);
      await h.click(summary);
      const reach = region.getByTestId('duty-reach');
      await h.expect(reach).toBeVisible();
      await h.expect(reach.getByTestId('duty-revealed-name')).toHaveCount(0);
      const hidden = reach.getByText(/^Hidden\b/).first(); // the reach list rows before any reveal
      await h.expect(hidden).toBeVisible();
      await h.hover(hidden);
    },
  },
  {
    caption: {
      en: 'The calendar shows the same trip day by day, together with tasks and payment dates.',
      vi: 'Lịch hiển thị cùng chuyến đó theo từng ngày, cùng với các việc cần làm và ngày thanh toán.',
    },
    run: async (page, h) => {
      await open(page, h, `/calendar?month=${t.start_date.slice(0, 7)}`, 'crm-calendar');
      const ev = page.getByTestId('calendar-agenda').locator(`a[href="/pipeline/${t.trip_id}"]`);
      await h.expect(ev.first()).toBeVisible({ timeout: 15_000 });
      await h.scrollTo(ev.first());
      await h.hover(ev.first());
    },
  },
  {
    caption: {
      en: 'Each person can subscribe to their own calendar feed from Google or Outlook. The address is private, so it is hidden here.',
      vi: 'Mỗi người có thể đăng ký lịch riêng của mình từ Google hoặc Outlook. Địa chỉ này là riêng tư nên được che ở đây.',
    },
    run: async (page, h) => {
      const panel = page.getByTestId('calendar-feed-panel');
      await h.scrollTo(panel);
      const active = panel.getByTestId('calendar-feed-active');
      if (await active.count()) {
        reuse(h, 'an active calendar feed', 'node tools/uat/record.cjs scenarios/crm/cleanup.cjs --fast revokes it');
      } else {
        const made = page.waitForResponse((r) => /\/calendar\/feed$/.test(new URL(r.url()).pathname) && r.request().method() === 'POST', { timeout: 30_000 });
        await h.click(panel.getByTestId('calendar-feed-create').getByRole('button'));
        h.expect((await made).status()).toBeLessThan(300);
        await h.expect(panel.getByTestId('calendar-feed-url')).toBeVisible({ timeout: 15_000 });
        await h.hover(panel.getByTestId('calendar-feed-url'));
      }
      await h.expect(active).toBeVisible({ timeout: 15_000 });
      const feeds = await bffOk(page, 'GET', 'calendar/feeds');
      s = st.load();
      for (const f of feeds.feeds || []) if (!f.revoked_at && f.calendar_feed_id) st.remember(s, 'ics_feeds', f.calendar_feed_id);
      st.save(s);
    },
  },
  {
    caption: {
      en: 'Not ready yet here: the Adventure Asia incident banner on affected trips, and two-way sync with Google or Microsoft calendars.',
      vi: 'Chưa có trong video này: biểu ngữ sự cố của Adventure Asia trên các chuyến bị ảnh hưởng, và đồng bộ hai chiều với lịch Google hoặc Microsoft.',
    },
    run: async (page, h) => {
      await slide.notReady(page, h, {
        screen: 'Incidents and calendar sync',
        missing: [
          'The incident banner on affected trips is built, but it is raised by Adventure Asia staff and was not recorded for this review',
          'Two-way sync with Google or Microsoft calendars (today: the read-only feed shown above)',
        ],
      });
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
