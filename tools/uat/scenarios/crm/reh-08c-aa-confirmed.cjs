// Pilot rehearsal step 8, part 3 (runbook docs/ops/runbooks/pilot-rehearsal.md, "AA confirms; CRM /aa-bookings shows
// confirmed"), and the hand-over to step 10: the lead traveller's portal link.
// Given: REH-08b-deposit booked the trip and the CRM asked Adventure Asia to confirm the held tour; Adventure Asia
//        confirmed it (instant departure, or the Booking staff in the Booking group's step 8); the owner (crm-rehearsal)
//        is signed in outside the recording.
// When:  the owner opens "Bookings with AA", finds the trip's tour as confirmed with its AA booking reference and the
//        quoted B2B price, opens the trip's bookings, then makes the lead traveller's portal link (shown once, blurred).
// Then:  the row is confirmed with a booking id, its quoted price equals the net of the AA option the agent added
//        (the Booking quote for the agency's tier); the trip line is confirmed; the portal link is kept in
//        work/rehearsal/.crm-secrets.json (r10_link with its trip id) for REH-10-portal.
// Writes (method and path allowed, capped at 1): POST trips/<id>/portal-access (one portal access link for the lead
// traveller, which mails the lead), plus the address search, on the rehearsal trip only; step 4 first proves the lead's
// address is the invented hand-off one (R.checkTraveller). Everything else reads. A tour that
// AA has not confirmed yet stops the step with that reason (record again after the Booking step). No LLM call. $0.
const R = require('./_reh.cjs');

const { step } = R;
let s;
let row;

module.exports = R.scenario({
  id: 'REH-08c-aa-confirmed',
  title: 'Rehearsal: Adventure Asia confirms the tour and the agency sees it',
  titleVi: 'Diễn tập: Adventure Asia xác nhận tour và đại lý thấy kết quả',
  allowWrites: R.bffWrites(['POST', `trips/${R.UUID}/portal-access`], R.searchWrite),
  steps: [
    step('The owner opens Bookings with AA: every Adventure Asia booking of the agency, read live from Adventure Asia.',
      'Chủ đại lý mở Bookings with AA: mọi đặt chỗ của đại lý với Adventure Asia, đọc trực tiếp từ Adventure Asia.',
      async (page, h) => {
        module.exports.meta.writes = await R.cap(page, [
          ['portal_access', 'POST', R.bffPath(`trips/${R.UUID}/portal-access`), 1],
          ['search', 'POST', R.bffPath('travelers/search'), R.SEARCH_CAP],
        ]);
        s = R.need(R.load(), ['trip_id', 'lead_name', 'aa_line', 'aa_option', 'r08b_done_at'], 'REH-08b-deposit');
        await R.sha(page, module.exports, 'start');
        await R.open(page, h, '/aa-bookings', 'crm-aa-bookings');
        await R.me(page, 'owner');
        const v = await R.bffOk(page, 'GET', 'aa-bookings');
        h.expect(v.source, 'read live from AA, not the last copy').not.toBe('cache');
        row = (v.bookings || []).find((b) => b.trip_id === s.trip_id);
        if (!row) throw new Error('the rehearsal trip is not among the agency\'s AA bookings yet');
        if (row.status !== 'confirmed') throw new Error(`Adventure Asia has not confirmed the tour yet (${row.status}/${row.aa_sub_status}): record after the Booking staff step`);
        await h.expect(page.getByTestId('aa-bookings-count')).toBeVisible();
        await h.hover(page.getByTestId('aa-bookings-count'));
      }),
    step('The trip\'s tour is confirmed, with Adventure Asia\'s booking reference and the price Adventure Asia quoted the agency.',
      'Tour của chuyến đã được xác nhận, có mã đặt chỗ của Adventure Asia và giá Adventure Asia báo cho đại lý.',
      async (page, h) => {
        h.expect(row.booking_id, 'an AA booking id').toBeTruthy();
        h.expect(row.quoted_b2b, 'the quoted B2B price').toBeTruthy();
        if (row.quoted_b2b.currency === s.aa_option.currency) {
          h.expect(Number(row.quoted_b2b.amount), 'quoted B2B = the net of the builder AA option').toBeCloseTo(Number(s.aa_option.net_amount), 2);
        }
        const table = page.getByTestId('aa-bookings-table');
        const line = table.getByRole('row').filter({ hasText: row.booking_id.slice(0, 8) }).or(table.getByText(row.booking_id.slice(0, 8))).first();
        await h.scrollTo(line);
        await h.expect(line).toBeVisible();
        await h.hover(line);
        R.save({ aa_booking: { booking_id: row.booking_id, quoted_b2b: row.quoted_b2b, status: row.status } });
        module.exports.meta.aa_booking = { status: row.status, quoted_b2b: row.quoted_b2b, net_in_builder: s.aa_option.net_amount };
      }),
    step('On the trip the Adventure Asia line reads confirmed as well.',
      'Trên trang chuyến, dòng Adventure Asia cũng hiện đã xác nhận.',
      async (page, h) => {
        await R.openTrip(page, h, s.trip_id);
        const lines = await R.aaLines(page, s.trip_id);
        const l = lines.find((x) => x.booking_line_id === s.aa_line.booking_line_id) || lines[0];
        h.expect(l && l.status).toBe('confirmed');
        const ledger = page.getByTestId('ledger-lines').or(page.getByTestId('ledger-cards')).first();
        await h.scrollTo(ledger);
        await h.expect(ledger).toContainText('Confirmed');
        await h.hover(ledger);
        R.save({ aa_line: { ...s.aa_line, status: l.status, title: l.title } });
      }),
    step('The trip is booked, so each traveller gets a personal portal. The owner copies the lead traveller\'s link; it is hidden here.',
      'Chuyến đã đặt, nên mỗi khách có một cổng riêng. Chủ đại lý sao chép đường dẫn của khách đứng tên; ở đây nó được che.',
      async (page, h) => {
        const tab = page.getByTestId('trip-proposal');
        const prow = tab.getByTestId('portal-row').filter({ hasText: s.lead_name }).first();
        await h.scrollTo(prow);
        await R.checkTraveller(page, s); // mail guard: the portal link is mailed to the lead
        await h.click(prow.getByRole('button', { name: /portal link/i }));
        const link = await tab.getByTestId('proposal-copy-link').first().inputValue({ timeout: 20_000 });
        if (!/\/c\/[a-z]+\/[A-Za-z0-9_-]{30,}$/.test(link)) throw new Error('the portal link has an unexpected shape');
        R.saveLink('r10_link', link, s.trip_id);
        await h.hover(tab.getByTestId('proposal-copy-links'));
        await h.assertMasked(['[data-testid="proposal-copy-links"]']);
        R.save({ r08c_done_at: new Date().toISOString() });
        await R.sha(page, module.exports, 'end');
      }, { writes: true }),
  ],
});
