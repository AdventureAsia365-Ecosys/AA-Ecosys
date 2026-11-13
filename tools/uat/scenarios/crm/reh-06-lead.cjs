// Pilot rehearsal step 6 (runbook docs/ops/runbooks/pilot-rehearsal.md, "Send to the agency"): the planner's lead
// reaches the agency's pipeline, and the owner hands it on for a quote.
// Given: the agency setup of scenarios/crm/REHEARSAL.md (REH-02b-agency-setup); the TripPlanner step 6 sent the
//        traveller's plan (tour X) to pilot-rehearsal-01 with consent, clicking twice, from an invented address; the
//        hand-off names the lead (UAT_REH_LEAD_NAME / work/rehearsal/handoff.json lead_name), its address
//        (UAT_REH_TRAVELLER_EMAIL / traveller_email, default on example.invalid) and tour X; the owner (crm-rehearsal)
//        is signed in outside the recording.
// When:  the owner opens the pipeline, finds the lead, opens the trip, hands it to the agent, saves the dates around a
//        fixed departure of tour X (arrival the day before; the trip ends the day the tour ends, so the trip has tour
//        X's days + 1), and moves it through Qualifying to Proposal (the planning details came by phone).
// Then:  exactly one card for the lead (one hand-off for the double click) in Inquiry, source "trip planner"
//        (crm_tp_lead_pull, about a minute); the lead's address is the invented hand-off address (checkTraveller, before
//        any later step mails); the trip's owner is the agent; dates saved (end = departure + days - 1); stage Proposal.
// Writes (method and path allowed, each capped): the trip's owner (POST owner, 1), its dates (PATCH trip, 1), the stage
// moves (POST stage, 3: the gate may answer the first Proposal move with its reason form) and the address search (POST
// travelers/search), on the rehearsal agency only (pilot guard pin). The checks
// "not visible to the audit tenants" and "TripPlanner outbox redacted" are cross-tenant / database reads of the
// orchestrator, not on this screen. No LLM call. Cost $0.
const R = require('./_reh.cjs');

const { step } = R;
let s;
let card;

module.exports = R.scenario({
  id: 'REH-06-lead',
  title: 'Rehearsal: the trip planner lead reaches the agency pipeline',
  titleVi: 'Diễn tập: yêu cầu từ trang lập kế hoạch chuyến đi về tới pipeline của đại lý',
  allowWrites: R.bffWrites(['POST', `trips/${R.UUID}/owner`], ['PATCH', `trips/${R.UUID}`], ['POST', `trips/${R.UUID}/stage`], R.searchWrite),
  steps: [
    step('The agency owner opens the pipeline. The plan the traveller sent from the agency\'s trip planner is in the Inquiry column.',
      'Chủ đại lý mở pipeline. Lịch trình khách gửi từ trang lập kế hoạch chuyến đi của đại lý đã nằm ở cột Inquiry.',
      async (page, h) => {
        module.exports.meta.writes = await R.cap(page, [
          ['owner', 'POST', R.bffPath(`trips/${R.UUID}/owner`), 1],
          ['dates', 'PATCH', R.bffPath(`trips/${R.UUID}`), 1],
          ['stage', 'POST', R.bffPath(`trips/${R.UUID}/stage`), 3],
          ['search', 'POST', R.bffPath('travelers/search'), R.SEARCH_CAP],
        ]);
        const hand = R.handoff();
        if (!hand.lead_name) throw new Error('no lead name: set UAT_REH_LEAD_NAME or work/rehearsal/handoff.json lead_name (TripPlanner step 6)');
        await R.sha(page, module.exports, 'start');
        await R.open(page, h, '/pipeline', 'board');
        await R.me(page, 'owner');
        card = await R.waitForCard(page, hand.lead_name, 180_000);
        const loc = page.locator(`[data-testid="column-inquiry"] [data-testid="trip-card"][data-trip-id="${card.trip_id}"]`);
        for (let i = 0; i < 3 && !(await loc.count()); i++) await R.open(page, h, '/pipeline', 'board');
        await h.expect(loc).toHaveCount(1);
        await h.scrollTo(loc);
        await h.hover(loc);
        s = R.save({ trip_id: card.trip_id, lead_name: hand.lead_name, tour_x: hand.tour_x, lead_at: new Date().toISOString() });
      }),
    step('There is one card, even though the traveller pressed send twice. It came from the trip planner and the agency owes the first reply.',
      'Chỉ có một thẻ, dù khách bấm gửi hai lần. Thẻ đến từ trang lập kế hoạch chuyến đi và đại lý đang phải trả lời trước.',
      async (page, h) => {
        const pl = await R.bffOk(page, 'GET', 'pipeline');
        const all = (pl.stages || []).flatMap((x) => x.cards || []).filter((c) => c.lead_name === s.lead_name);
        h.expect(all.length, 'one card for the lead (one hand-off for the double click)').toBe(1);
        h.expect(card.lead_source).toBe('tripplanner');
        h.expect(card.stage).toBe('inquiry');
        const loc = page.locator(`[data-testid="trip-card"][data-trip-id="${card.trip_id}"]`);
        await h.expect(loc).toHaveAttribute('data-waiting', 'agency');
        await h.expect(loc.getByTestId('trip-card-party')).toBeVisible();
        await h.hover(loc.getByTestId('trip-card-party'));
      }),
    step('The owner opens the trip. The source says trip planner, and the party and budget come from the traveller\'s plan.',
      'Chủ đại lý mở chuyến. Nguồn ghi là trang lập kế hoạch chuyến đi, số người và ngân sách lấy từ lịch trình của khách.',
      async (page, h) => {
        const loc = page.locator(`[data-testid="column-inquiry"] [data-trip-id="${card.trip_id}"]`);
        await h.click(loc);
        await page.waitForURL(`**/pipeline/${card.trip_id}`, { timeout: 20_000 });
        await h.expect(page.getByTestId('crm-trip')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
        await h.expect(page.getByTestId('trip-stage')).toHaveAttribute('data-stage', 'inquiry');
        const src = page.getByTestId('trip-source');
        await h.scrollTo(src);
        await h.expect(src).toContainText(/planner/i);
        await h.hover(src);
        const t = await R.bffOk(page, 'GET', `trips/${card.trip_id}`);
        h.expect(t.trip.party_adults, 'party adults from the plan').toBeGreaterThanOrEqual(1);
        s = R.save({ adults: t.trip.party_adults });
        // Mail guard (no screen part): later steps mail this lead; its address must be the invented hand-off one.
        await R.checkTraveller(page, s);
      }),
    step('The owner hands the trip to the agency\'s agent, who will build the quote.',
      'Chủ đại lý giao chuyến cho nhân viên tư vấn của đại lý, người sẽ làm báo giá.',
      async (page, h) => {
        const members = (await R.bffOk(page, 'GET', 'members')).members || [];
        const agent = members.find((m) => m.role === 'agent' && m.status === 'active');
        if (!agent) throw new Error('the rehearsal agency has no active agent (seed --member pilot-rehearsal-01:agent:<sub>)');
        const sel = page.getByTestId('trip-owner');
        await h.scrollTo(sel);
        await R.choose(h, sel, agent.member_id);
        await h.expect.poll(async () => (await R.bffOk(page, 'GET', `trips/${card.trip_id}`)).trip.owner_member_id, { timeout: 15_000 })
          .toBe(agent.member_id);
        s = R.save({ agent_member_id: agent.member_id });
      }, { writes: true }),
    step('After a call, the owner saves the dates: arrival the day before the tour\'s fixed departure, home when the tour ends.',
      'Sau cuộc gọi, chủ đại lý lưu ngày đi: khách đến trước ngày khởi hành cố định của tour một ngày, về khi tour kết thúc.',
      async (page, h) => {
        const tour = await R.tourX(page);
        const dep = R.pickDeparture(tour, s.adults);
        const at = (d) => new Date(`${d}T12:00:00Z`);
        const start = R.day(-1, at(dep.start_date)); // the departure falls on day 2
        const tourEnd = R.day(tour.days - 1, at(dep.start_date)); // runbook: end = start + days - 1
        const end = tourEnd; // the trip ends with the tour: tour X's days + the arrival day
        const form = page.getByTestId('trip-dates');
        await h.scrollTo(form);
        await h.click(form.locator('input[type="date"]').nth(0));
        await form.locator('input[type="date"]').nth(0).fill(start);
        await h.click(form.locator('input[type="date"]').nth(1));
        await form.locator('input[type="date"]').nth(1).fill(end);
        await h.click(form.getByRole('button', { name: 'Save dates' }));
        await h.expect.poll(async () => (await R.bffOk(page, 'GET', `trips/${card.trip_id}`)).trip.start_date, { timeout: 15_000 }).toBe(start);
        h.expect((await R.bffOk(page, 'GET', `trips/${card.trip_id}`)).trip.end_date, 'the trip ends the day tour X ends').toBe(end);
        const tripDays = tour.days + 1;
        s = R.save({
          start_date: start, end_date: end, trip_days: tripDays,
          departure: { tour_source_id: tour.source_id, tour_title: tour.title, days: tour.days, departure_id: dep.departure_id,
            start_date: dep.start_date, end_date: tourEnd, auto_confirm: !!dep.auto_confirm },
        });
        module.exports.meta.departure = { start_date: dep.start_date, end_date: tourEnd, days: tour.days, trip_days: tripDays, auto_confirm: !!dep.auto_confirm };
      }, { writes: true }),
    step('The owner moves the trip to Qualifying.',
      'Chủ đại lý chuyển chuyến sang Qualifying.',
      async (page, h) => {
        await h.scrollTo(page.getByTestId('trip-moves'));
        await h.click(page.getByTestId('trip-move-qualifying').getByRole('button'));
        await h.expect(page.getByTestId('trip-stage')).toHaveAttribute('data-stage', 'qualifying', { timeout: 15_000 });
      }, { writes: true }),
    step('Then to Proposal. The planning details came by phone, so the owner records that reason; it is logged.',
      'Rồi sang Proposal. Thông tin lên kế hoạch đã có qua điện thoại nên chủ đại lý chọn lý do đó; lý do được ghi lại.',
      async (page, h) => {
        await h.click(page.getByTestId('trip-move-proposal').getByRole('button'));
        const gate = page.getByTestId('gate-reason');
        const gated = await Promise.race([
          gate.waitFor({ state: 'visible', timeout: 15_000 }).then(() => true),
          page.getByTestId('trip-stage').and(page.locator('[data-stage="proposal"]')).waitFor({ timeout: 15_000 }).then(() => false),
        ]).catch(() => false);
        if (gated) {
          await R.choose(h, gate, 'info_by_phone');
          await h.click(page.getByTestId('gate-confirm').getByRole('button'));
        }
        await h.expect(page.getByTestId('trip-stage')).toHaveAttribute('data-stage', 'proposal', { timeout: 15_000 });
      }, { writes: true }),
    step('On the board the card now sits under Proposal, assigned to the agent.',
      'Trên bảng, thẻ giờ nằm ở cột Proposal và đã giao cho nhân viên tư vấn.',
      async (page, h) => {
        await R.open(page, h, '/pipeline', 'board');
        const loc = page.locator(`[data-testid="column-proposal"] [data-trip-id="${card.trip_id}"]`);
        await h.expect(loc).toHaveCount(1, { timeout: 15_000 });
        await h.scrollTo(loc);
        await h.hover(loc);
        R.save({ r06_done_at: new Date().toISOString() });
        await R.sha(page, module.exports, 'end');
      }),
  ],
});
