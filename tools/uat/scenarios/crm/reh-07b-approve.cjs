// Pilot rehearsal step 7, part 2 (runbook docs/ops/runbooks/pilot-rehearsal.md, "Quote"): the owner approves the
// discount, publishes the quote and sends it to the client.
// Given: REH-07-quote left a builder draft on the rehearsal trip with a discount above the agency's limit and a pending
//        approval request; the owner (crm-rehearsal) is signed in outside the recording.
// When:  the owner sees the urgent approval task on the trip, opens the builder, approves the discount, publishes
//        version 1 and sends it from the trip (the client link is shown once, blurred).
// Then:  the task closes, the discount reads approved, Publish is enabled and the version goes published then sent;
//        the client link is kept in work/rehearsal/.crm-secrets.json (r08_link with its trip id) for REH-08-accept.
// Writes: the owner's decision, the publish and the send, on the rehearsal trip only. Mail: sending makes the CRM mail
// the planner traveller's invented address through the agency's connected mailbox (undeliverable, *.invalid expected
// from the planner step). No LLM call. Cost $0.
const R = require('./_reh.cjs');

const { step } = R;
let s;

module.exports = R.scenario({
  id: 'REH-07b-approve',
  title: 'Rehearsal: the owner approves the discount and sends the quote',
  titleVi: 'Diễn tập: chủ đại lý duyệt mức giảm giá và gửi báo giá',
  // The decision (discount-approval/<id>), publish, send and reissue-link of this trip's proposal.
  allowWrites: R.bffWrites(`proposals/${R.UUID}/(?:discount-approval/${R.UUID}|publish|send|reissue-link)`),
  steps: [
    step('The owner opens the trip. An urgent task waits for her: approve the agent\'s discount.',
      'Chủ đại lý mở chuyến. Một việc gấp đang chờ: duyệt mức giảm giá của nhân viên tư vấn.',
      async (page, h) => {
        s = R.need(R.load(), ['trip_id', 'proposal_id', 'discount_pct', 'r07_done_at'], 'REH-07-quote');
        await R.sha(page, module.exports, 'start');
        await R.openTrip(page, h, s.trip_id);
        await R.me(page, 'owner');
        const task = page.locator('[data-testid="trip-task"][data-kind="discount_approval"]');
        const v = await R.builderView(page, s.proposal_id);
        if (!v.pricing.discount.pending) return R.reuse(h, `the decision (${v.status})`, 'run REH-07-quote on a new trip');
        await h.expect(task.first()).toBeVisible({ timeout: 20_000 });
        await h.expect(task.first()).toHaveAttribute('data-status', 'open');
        await h.scrollTo(task.first());
        await h.hover(task.first());
      }),
    step('In the builder she sees the discount, the agency limit and who asked for it.',
      'Trong trình dựng, chị thấy mức giảm, giới hạn của đại lý và người đã gửi yêu cầu.',
      async (page, h) => {
        await R.open(page, h, `/pipeline/${s.trip_id}/proposal/${s.proposal_id}`, 'builder');
        await h.expect(page.getByTestId('builder')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
        const box = page.getByTestId('builder-discount');
        await h.scrollTo(box);
        const v = await R.builderView(page, s.proposal_id);
        if (v.pricing.discount.pending) {
          await h.expect(box.getByTestId('builder-discount-pending')).toBeVisible();
          h.expect(Number(v.pricing.discount.pending.discount_pct)).toBe(Number(s.discount_pct));
        }
        await h.expect(page.getByTestId('builder-totals-discount')).toBeVisible();
        await h.hover(box);
      }),
    step('She approves it. The task closes and the discount now reads approved.',
      'Chị duyệt. Việc được đóng và mức giảm hiện là đã duyệt.',
      async (page, h) => {
        const box = page.getByTestId('builder-discount');
        if (await box.getByTestId('builder-discount-approve').count()) {
          const decided = page.waitForResponse((r) => /\/discount-approval\/[0-9a-f-]{36}$/.test(new URL(r.url()).pathname) && r.request().method() === 'POST', { timeout: 30_000 });
          await h.click(box.getByTestId('builder-discount-approve').getByRole('button'));
          h.expect((await decided).status()).toBeLessThan(300);
        } else R.reuse(h, 'the approval');
        await h.expect(box).not.toHaveAttribute('data-needs-approval', 'true', { timeout: 15_000 });
        const v = await R.builderView(page, s.proposal_id);
        h.expect(v.pricing.discount.needs_approval).toBe(false);
        h.expect(Number(v.pricing.discount.approved_pct)).toBeGreaterThanOrEqual(Number(s.discount_pct));
        h.expect(v.checks.blocking).not.toContain('discount_needs_approval');
      }, { writes: true }),
    step('She publishes version one. Only a published version can go to the client.',
      'Chị phát hành phiên bản một. Chỉ bản đã phát hành mới gửi được cho khách.',
      async (page, h) => {
        const builder = page.getByTestId('builder');
        if ((await builder.getAttribute('data-status')) === 'draft') {
          const publish = page.getByTestId('builder-header').getByRole('button', { name: /^Publish v\d+$/ });
          await h.scrollTo(publish);
          await h.expect(publish).toBeEnabled({ timeout: 15_000 });
          await h.click(publish);
        } else R.reuse(h, 'the published version');
        await h.expect(builder).toHaveAttribute('data-status', /^(published|sent)$/, { timeout: 20_000 });
        const v = await R.builderView(page, s.proposal_id);
        const totals = page.getByTestId('builder-totals');
        await h.scrollTo(totals);
        await h.hover(totals);
        R.save({ published_version: v.version, totals: { sell: v.totals && v.totals.sell, discount_pct: v.totals && v.totals.discount_pct } });
      }, { writes: true }),
    step('On the trip she sends it to the client. The private link is shown once; it is hidden in this video.',
      'Trên trang chuyến, chị gửi báo giá cho khách. Đường dẫn riêng chỉ hiện một lần; trong video này nó được che đi.',
      async (page, h) => {
        await R.openTrip(page, h, s.trip_id);
        const tab = page.getByTestId('trip-proposal');
        const send = tab.getByTestId('builder-send').getByRole('button');
        if (await send.count()) {
          await h.scrollTo(send);
          await h.click(send);
        } else {
          R.reuse(h, 'the sent version');
          const again = tab.getByTestId('builder-reissue').getByRole('button');
          await h.scrollTo(again);
          await h.click(again);
        }
        const link = await tab.getByTestId('proposal-copy-link').first().inputValue({ timeout: 20_000 });
        if (!/\/c\/p\/[A-Za-z0-9_-]{43}$/.test(link)) throw new Error('the client link has an unexpected shape');
        R.saveLink('r08_link', link, s.trip_id);
        await h.hover(tab.getByTestId('proposal-copy-links'));
        await h.assertMasked(['[data-testid="proposal-copy-links"]']);
        const v = await R.builderView(page, s.proposal_id);
        h.expect(v.status).toBe('sent');
        R.save({ r07b_done_at: new Date().toISOString() });
        await R.sha(page, module.exports, 'end');
      }, { writes: true }),
  ],
});
