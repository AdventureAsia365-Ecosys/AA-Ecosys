// UAT scenario REH-10a-show-aa-line (pilot rehearsal step 10 setup; root docs/ops/runbooks/pilot-rehearsal.md): the
// agency owner shows the trip's confirmed Adventure Asia line to the travellers, from the trip's Bookings panel (the
// "Show to travellers" switch of AA-Partner crm-065 / #307). A line confirmed after that release is shown by default;
// the rehearsal trip's line was confirmed before it, so it starts hidden and the traveller portal (REH-10-portal)
// would list no tour. Re-run safe: an already shown line is only read.
// Given: the owner (crm-rehearsal), the trip of REH-06..REH-08c with its AA line confirmed (work/rehearsal/crm.json).
// When:  the owner opens the trip, finds the AA line in Bookings and presses Show to travellers when it is hidden.
// Then:  the line reads Shown (data-shown "yes") and the CRM answers visible_to_travelers true for it.
// Writes: at most one PATCH /bff/lines/<the AA line> (visible_to_travelers true), capped and allowed for PATCH only.
// No mail, no LLM call. Cost $0. 1440 x 900.
const R = require('./_reh.cjs');

const { step } = R;
let s;
let line;

module.exports = R.scenario({
  id: 'REH-10a-show-aa-line',
  title: 'Rehearsal: the agency shows the confirmed Adventure Asia tour to its travellers',
  titleVi: 'Diễn tập: đại lý cho khách xem tour Adventure Asia đã xác nhận',
  allowWrites: R.bffWrites(['PATCH', `lines/${R.UUID}`]),
  steps: [
    step('The owner opens the rehearsal trip. Its Bookings panel lists the Adventure Asia tour, confirmed.',
      'Chủ đại lý mở chuyến diễn tập. Mục Bookings liệt kê tour Adventure Asia đã được xác nhận.',
      async (page, h) => {
        module.exports.meta.writes = await R.cap(page, [['show', 'PATCH', R.bffPath(`lines/${R.UUID}`), 1]]);
        s = R.need(R.load(), ['trip_id', 'aa_line'], 'REH-08c-aa-confirmed');
        await R.sha(page, module.exports, 'start');
        await R.openTrip(page, h, s.trip_id);
        await R.me(page, 'owner');
        const v = await R.bffOk(page, 'GET', `trips/${s.trip_id}/lines`);
        line = (v.lines || []).find((l) => l.booking_line_id === s.aa_line.booking_line_id);
        if (!line) throw new Error('the trip has no Adventure Asia line (record REH-07 to REH-08c first)');
        if (line.status !== 'confirmed') throw new Error(`the Adventure Asia line is ${line.status}, not confirmed`);
        module.exports.meta.shown_before = !!line.visible_to_travelers;
        const sw = page.getByTestId('line-shown').first();
        await h.scrollTo(sw, 'center');
        await h.expect(sw).toBeVisible({ timeout: 20_000 });
      }),
    step('It is hidden from the travellers, so their portal would not list it. The owner presses Show to travellers.',
      'Tour đang bị ẩn với khách, nên cổng khách sẽ không hiện tour này. Chủ đại lý bấm Show to travellers.',
      async (page, h) => {
        const sw = page.getByTestId('line-shown').first();
        if (line.visible_to_travelers) {
          await h.expect(sw).toHaveAttribute('data-shown', 'yes');
          return R.reuse(h, 'the line already shown to travellers');
        }
        await h.expect(sw).toHaveAttribute('data-shown', 'no');
        const saved = page.waitForResponse((r) => r.request().method() === 'PATCH'
          && new URL(r.url()).pathname === R.bffPath(`lines/${line.booking_line_id}`), { timeout: 30_000 });
        await h.click(sw.getByRole('button', { name: 'Show to travellers', exact: true }));
        const res = await saved;
        if (res.status() !== 200) throw new Error(`showing the line answered ${res.status()}`);
        await h.expect(page.getByTestId('line-shown').first()).toHaveAttribute('data-shown', 'yes', { timeout: 20_000 });
      }, { writes: true }),
    step('The line now reads Shown: the travellers see the tour in their portal. This is the end of the scenario.',
      'Dòng tour giờ hiện là Shown: khách thấy tour trong cổng của mình. Kết thúc kịch bản.',
      async (page, h) => {
        const v = await R.bffOk(page, 'GET', `trips/${s.trip_id}/lines`);
        const now = (v.lines || []).find((l) => l.booking_line_id === s.aa_line.booking_line_id);
        if (!now || !now.visible_to_travelers) throw new Error('the CRM does not report the line as shown to travellers');
        const n = module.exports.meta.writes;
        if (n.show !== (module.exports.meta.shown_before ? 0 : 1)) throw new Error(`unexpected write counts ${JSON.stringify(n)}`);
        await h.hover(page.getByTestId('line-shown').first());
        await R.sha(page, module.exports, 'end');
      }),
  ],
});
