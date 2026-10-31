// CRM review R12 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): duty of care and the calendar.
// Given: A (owner) signed in; R10 booked the invoice trip, which starts within 14 days (prep dates it today + 12).
//        Optional: an Adventure Asia incident open on the departure of one of the agency's trips. Only Adventure Asia
//        raises one (on Dev: the reviewed AA-CIS-Infra DB Migrate run-script db/scripts/aa961_incident_seed.py); then
//        `node tools/uat/lib/crm-state.cjs incident open <trip id>` records it in work/crm/state.json, and
//        `node tools/uat/lib/crm-state.cjs incident clear` after it is cleared. The steps are chosen from that state
//        when the file loads, so make the captions (--captions) after setting it.
// When:  the owner opens Travelling now for 14 days (the trip, its region, the "reach travellers" list with names
//        hidden); with an open incident, the incident list at the top and the affected trip's banner and urgent task;
//        then the calendar month of the trip, and creates a personal calendar (ICS) feed.
// Then:  the trip shows under its region with "leaves on"; the reach list is there without names; the incident is
//        shown when state.json says it is open (checked against the API both ways: an open incident the state does
//        not know fails the chunk, so the plain mention never hides a real one); the calendar has the trip's events;
//        the feed is active and its URL is blurred (it is a credential). Two-way sync with Google / Microsoft is not
//        built: "Not ready yet" card.
// Writes: one ICS feed (id kept in work/crm/state.json for cleanup.cjs, which revokes it). No reveal, no LLM call.
// A re-run with an active feed skips the create in --fast only. Cost $0.
const slide = require('../../lib/slide.cjs');
const { st, base, sha, open, bffOk, reuse } = require('./_crm.cjs');

const sc = base({
  id: 'CRM-REV-12',
  title: 'Duty of care and the calendar: who travels where, and a private calendar feed',
  mask: ['[data-testid="trip-answers"]', '[data-testid="trip-history"]'], // the incident trip's page: not part of this story
});
// Chosen once, when the file loads: captions and the recorded take must see the same state (record.cjs checks).
const INCIDENT = (() => {
  const i = st.load().incident;
  return i && i.open && i.trip_id ? i : null;
})();
let s;
let t;

/** Open incidents the CRM API knows on Travelling now (14 days): the truth the state must agree with. */
async function openIncidents(page) {
  const tv = await bffOk(page, 'GET', 'duty/travelling?days=14');
  return tv.incidents || [];
}

function noIncidentStep() {
  return {
    caption: {
      en: 'When Adventure Asia reports an incident on a departure, it shows at the top of this page, and each affected trip gets a banner and an urgent task. None is open today.',
      vi: 'Khi Adventure Asia báo sự cố trên một lịch khởi hành, sự cố hiện ở đầu trang này, và mỗi chuyến bị ảnh hưởng có một biểu ngữ cùng một việc khẩn. Hôm nay không có sự cố nào đang mở.',
    },
    run: async (page, h) => {
      const open_ = await openIncidents(page);
      if (open_.length) {
        throw new Error(`${open_.length} incident(s) open on the agency's departures but work/crm/state.json has none: node tools/uat/lib/crm-state.cjs incident open <trip id>, then the captions again`);
      }
      await h.expect(page.getByTestId('duty-incidents')).toHaveCount(0);
      const heading = page.getByTestId('crm-travelling').getByRole('heading').first();
      await h.scrollTo(heading);
      await h.hover(heading);
    },
  };
}

function incidentSteps() {
  const trip = INCIDENT.trip_id;
  return [
    {
      caption: {
        en: 'Adventure Asia has reported an incident on a departure. It is listed at the top of this page, with the agency trips it touches.',
        vi: 'Adventure Asia vừa báo một sự cố trên một lịch khởi hành. Sự cố được liệt kê ở đầu trang này, cùng các chuyến của đại lý có liên quan.',
      },
      run: async (page, h) => {
        const open_ = await openIncidents(page);
        const mine = open_.find((f) => (f.trips || []).some((x) => x.trip_id === trip));
        if (!mine) {
          throw new Error(`work/crm/state.json says an incident is open on trip ${trip.slice(0, 8)}, the API lists none (${open_.length} open): node tools/uat/lib/crm-state.cjs incident clear, then the captions again`);
        }
        const panel = page.getByTestId('duty-incidents');
        await h.expect(panel).toBeVisible({ timeout: 15_000 });
        const item = panel.getByTestId(`duty-incident-${mine.departure_id}`);
        await h.expect(item.locator(`a[href="/pipeline/${trip}"]`)).toBeVisible();
        await h.scrollTo(panel);
        await h.hover(item.locator(`a[href="/pipeline/${trip}"]`));
      },
    },
    {
      caption: {
        en: 'The affected trip carries a banner and an urgent task for the agent. The agency contacts its own travellers; Adventure Asia does not message them.',
        vi: 'Chuyến bị ảnh hưởng có một biểu ngữ và một việc khẩn cho người phụ trách. Đại lý tự liên hệ khách của mình; Adventure Asia không nhắn cho khách.',
      },
      run: async (page, h) => {
        await open(page, h, `/pipeline/${trip}`, 'crm-trip');
        const banner = page.getByTestId('trip-incident-banner');
        await h.expect(banner).toBeVisible({ timeout: 15_000 });
        await h.expect(banner).toHaveAttribute('role', 'alert');
        await h.scrollTo(banner);
        await h.hover(banner.locator('strong').first());
        const task = page.locator('[data-testid="trip-task"][data-kind="aa_incident"]').first();
        await h.expect(task).toHaveAttribute('data-status', 'open');
        await h.scrollTo(task);
        await h.hover(task);
      },
    },
  ];
}

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
  ...(INCIDENT ? incidentSteps() : [noIncidentStep()]),
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
      en: 'Not ready yet: two-way sync with Google or Microsoft calendars. Today the calendar goes out through the read-only feed.',
      vi: 'Chưa làm xong: đồng bộ hai chiều với lịch Google hoặc Microsoft. Hiện lịch chỉ đi ra qua đường dẫn chỉ đọc ở trên.',
    },
    run: async (page, h) => {
      await slide.notReady(page, h, {
        screen: 'Calendar sync',
        missing: ['Two-way sync with Google or Microsoft calendars (today: the read-only feed shown above)'],
      });
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
