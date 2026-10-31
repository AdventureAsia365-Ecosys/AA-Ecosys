// CRM review R04 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): following a trip through the stages.
// Given: A (owner) signed in; the R03 trip (work/crm/state.json r03) still in Inquiry; prep chose the AA departure.
// When:  the owner opens the trip from the board, sets the dates, moves it to Qualifying, then to Proposal with a
//        logged reason (the details came by phone), and checks the board; then opens the Tasks page.
// Then:  the stage badge follows each move, the board shows the card under Proposal, Tasks is the real empty page,
//        followed by a "Not ready yet" card naming what is missing.
// Writes on the invented R03 trip only (dates, two stage moves). No LLM call. Cost $0.
const slide = require('../../lib/slide.cjs');
const { st, base, sha, open, bffOk, choose, day, reuse } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-04', title: 'Pipeline: a trip moves from Inquiry to Proposal', titleVi: 'Pipeline: chuyến đi từ Inquiry sang Proposal' });
let s;
let trip;

const stage = (page) => page.getByTestId('trip-stage');

sc.steps = [
  {
    caption: {
      en: 'The pipeline has one column per stage, from Inquiry to Travelling. Chips filter by who owes the next step.',
      vi: 'Pipeline có một cột cho mỗi giai đoạn, từ Inquiry tới Travelling. Các nút lọc theo ai đang phải làm bước tiếp theo.',
    },
    run: async (page, h) => {
      s = st.load();
      if (!s.r03) throw new Error('no R03 trip: run crm-rev-03 first');
      await sha(page, sc, 'start');
      await page.goto(`${sc.baseURL}/pipeline`, { waitUntil: 'domcontentloaded' }); // a CRM page for the BFF
      let t = await bffOk(page, 'GET', `trips/${s.r03.trip_id}`);
      if (t.trip.stage === 'qualifying') { // a rehearsal stopped half-way: put the trip back (--fast only)
        reuse(h, 'the R03 trip moved to Qualifying', 're-run crm-rev-03 for a fresh trip');
        await bffOk(page, 'POST', `trips/${s.r03.trip_id}/stage`, { to: 'inquiry' });
        t = await bffOk(page, 'GET', `trips/${s.r03.trip_id}`);
      }
      if (t.trip.stage !== 'inquiry') throw new Error(`the R03 trip is at ${t.trip.stage}, not inquiry: run crm-rev-03 again for a fresh trip`);
      await open(page, h, '/pipeline', 'board');
      await h.hover(page.getByTestId('chip-agency'));
      await h.hover(page.getByTestId('owner-me'));
    },
  },
  {
    caption: {
      en: 'The owner opens the new trip. The first task is already there: reply to the inquiry within two hours.',
      vi: 'Chủ đại lý mở chuyến mới. Việc đầu tiên đã có sẵn: trả lời yêu cầu trong vòng hai giờ.',
    },
    run: async (page, h) => {
      const card = page.locator(`[data-testid="column-inquiry"] [data-trip-id="${s.r03.trip_id}"]`);
      await h.scrollTo(card);
      await h.click(card);
      await page.waitForURL(`**/pipeline/${s.r03.trip_id}`);
      await h.expect(page.getByTestId('crm-trip')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
      await h.expect(stage(page)).toHaveAttribute('data-stage', 'inquiry');
      await h.hover(page.locator('[data-testid="trip-task"][data-kind="reply_inquiry"]'));
    },
  },
  {
    caption: {
      en: 'After a first call the dates are clear, so the owner saves them on the trip.',
      vi: 'Sau cuộc gọi đầu tiên ngày đi đã rõ, nên chủ đại lý lưu ngày vào chuyến.',
    },
    run: async (page, h) => {
      const start = day(-1, new Date(`${s.departure.start_date}T12:00:00Z`)); // the AA departure falls on day 2
      const end = day(6, new Date(`${start}T12:00:00Z`));
      const form = page.getByTestId('trip-dates');
      await h.scrollTo(form);
      await h.click(form.locator('input[type="date"]').nth(0));
      await form.locator('input[type="date"]').nth(0).fill(start);
      await h.click(form.locator('input[type="date"]').nth(1));
      await form.locator('input[type="date"]').nth(1).fill(end);
      await h.click(form.getByRole('button', { name: 'Save dates' }));
      await h.expect.poll(async () => (await bffOk(page, 'GET', `trips/${s.r03.trip_id}`)).trip.start_date, { timeout: 15_000 }).toBe(start);
      s.r03.start_date = start;
      s.r03.end_date = end;
      st.save(s);
    },
  },
  {
    caption: {
      en: 'The owner moves the trip to Qualifying.',
      vi: 'Chủ đại lý chuyển chuyến sang Qualifying.',
    },
    run: async (page, h) => {
      await h.scrollTo(page.getByTestId('trip-moves'));
      await h.click(page.getByTestId('trip-move-qualifying').getByRole('button'));
      await h.expect(stage(page)).toHaveAttribute('data-stage', 'qualifying', { timeout: 15_000 });
    },
  },
  {
    caption: {
      en: 'Moving on to Proposal needs the planning details. They came by phone, so the owner records that reason; it is logged.',
      vi: 'Chuyển sang Proposal cần đủ thông tin lên kế hoạch. Thông tin đã có qua điện thoại nên chủ đại lý chọn lý do đó; lý do được ghi lại.',
    },
    run: async (page, h) => {
      await h.click(page.getByTestId('trip-move-proposal').getByRole('button'));
      const gate = page.getByTestId('gate-reason');
      const gated = await Promise.race([
        gate.waitFor({ state: 'visible', timeout: 15_000 }).then(() => true),
        stage(page).and(page.locator('[data-stage="proposal"]')).waitFor({ timeout: 15_000 }).then(() => false),
      ]).catch(() => false);
      if (gated) {
        await h.expect(page.getByTestId('gate-dialog-body')).toBeVisible();
        await h.hover(page.getByTestId('gate-missing').or(page.getByTestId('gate-dialog-body')).first());
        await choose(h, gate, 'info_by_phone');
        await h.click(page.getByTestId('gate-confirm').getByRole('button'));
      }
      await h.expect(stage(page)).toHaveAttribute('data-stage', 'proposal', { timeout: 15_000 });
    },
  },
  {
    caption: {
      en: 'Back on the board, the card now sits under Proposal.',
      vi: 'Quay lại pipeline, thẻ giờ nằm ở cột Proposal.',
    },
    run: async (page, h) => {
      await open(page, h, '/pipeline', 'board');
      const card = page.locator(`[data-testid="column-proposal"] [data-trip-id="${s.r03.trip_id}"]`);
      await h.expect(card).toHaveCount(1);
      await h.scrollTo(card);
      await h.hover(card);
    },
  },
  {
    caption: {
      en: 'Each trip keeps its own tasks. The Tasks page, one list across all trips, is still an empty page.',
      vi: 'Mỗi chuyến giữ danh sách việc riêng. Trang Tasks, nơi gom việc của mọi chuyến, hiện vẫn là trang trống.',
    },
    run: async (page, h) => {
      await open(page, h, '/tasks', 'crm-section-tasks');
      await h.expect(page.getByTestId('kit-empty-state')).toBeVisible();
      await h.pause(2500);
    },
  },
  {
    caption: {
      en: 'Not ready yet: one task list across all trips, and the automations that would create follow-ups.',
      vi: 'Chưa có: một danh sách việc chung cho mọi chuyến, và phần tự động hoá tạo việc nhắc theo dõi.',
    },
    run: async (page, h) => {
      await slide.notReady(page, h, {
        screen: 'Tasks across all trips',
        missing: ['One list of every open task across all trips', 'Automations that create tasks and follow-ups by themselves'],
      });
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
