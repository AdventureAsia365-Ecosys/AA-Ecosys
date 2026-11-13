// Pilot rehearsal step 7, part 1 (runbook docs/ops/runbooks/pilot-rehearsal.md, "Quote"): the agent builds the quote.
// Given: REH-06-lead put the planner's trip at Proposal, dates around a fixed departure of tour X, assigned to the agent;
//        the agent (crm-rehearsal-agent) is signed in outside the recording.
// When:  the agent starts the day-by-day builder in USD, adds the agency's own hotel on night 1, puts tour X (an
//        Adventure Asia line, live quote from Booking) on day 2 for the chosen departure, writes what is included and not
//        included, sets the balance date, gives a discount above the agency's limit and asks the owner to approve it.
// Then:  the AA option comes back with a net cost (the Booking quote for the agency's tier) and its availability; the
//        inclusion lists are saved; the discount needs the owner (badge, "discount_needs_approval" blocks Publish, the
//        Publish button is disabled for the agent); the request is pending and the owner has an urgent task.
// Writes: one builder draft on the rehearsal trip (start, two options, one block, inclusions, settings, the discount)
// and one discount approval request. Adding an AA option takes no seat (only a client hold does). REH-07b-approve
// follows. No LLM call, no AI button. Cost $0.
const R = require('./_reh.cjs');

const { step } = R;
let s;
let pid;
const HOTEL = 'Riverside boutique hotel (agency)';
const BLOCK = 'Adventure Asia tour';

const view = (page) => R.builderView(page, pid);
const tourBlock = (page) => page.getByTestId('builder-block').filter({ hasText: BLOCK });

module.exports = R.scenario({
  id: 'REH-07-quote',
  identity: 'crm-rehearsal-agent',
  title: 'Rehearsal: the agent quotes an Adventure Asia tour with the agency\'s own services',
  titleVi: 'Diễn tập: nhân viên tư vấn báo giá tour Adventure Asia cùng dịch vụ riêng của đại lý',
  // Start the builder, then the draft's own writes: builder (PATCH: settings, discount), blocks, options, aa-options,
  // inclusions, discount-approval (the request). Never publish or send (the agent cannot publish this one anyway).
  allowWrites: R.bffWrites(`trips/${R.UUID}/builder`, `proposals/${R.UUID}/(?:builder|blocks|options|days|inclusions|discount-approval)(?:/[a-z0-9/_-]*)?`),
  steps: [
    step('The agent opens the trip the owner handed over. It is at Proposal, with the dates set.',
      'Nhân viên tư vấn mở chuyến chủ đại lý vừa giao. Chuyến đang ở Proposal, đã có ngày đi.',
      async (page, h) => {
        s = R.need(R.load(), ['trip_id', 'departure', 'adults', 'r06_done_at'], 'REH-06-lead');
        await R.sha(page, module.exports, 'start');
        await R.openTrip(page, h, s.trip_id);
        const m = await R.me(page, 'agent');
        await h.expect(page.getByTestId('trip-stage')).toHaveAttribute('data-stage', 'proposal');
        const t = await R.bffOk(page, 'GET', `trips/${s.trip_id}`);
        h.expect(t.trip.owner_member_id, 'the trip is the agent\'s').toBe(m.member_id);
      }),
    step('She starts the day-by-day proposal builder, in US dollars.',
      'Chị mở trình dựng đề xuất theo từng ngày, tính bằng đô la Mỹ.',
      async (page, h) => {
        if (s.proposal_id) {
          R.reuse(h, 'the builder draft of the rehearsal trip', 'run REH-06-lead on a new planner lead');
          pid = s.proposal_id;
          await R.open(page, h, `/pipeline/${s.trip_id}/proposal/${pid}`, 'builder');
        } else {
          const section = page.getByTestId('proposal-builder');
          await h.scrollTo(section);
          await R.type(page, h, section.getByTestId('builder-currency'), 'USD');
          await h.click(section.getByRole('button', { name: 'Start the builder' }));
          await page.waitForURL(/\/proposal\/[0-9a-f-]{36}$/, { timeout: 30_000 });
          pid = page.url().split('/').pop();
          s = R.save({ proposal_id: pid });
        }
        await h.expect(page.getByTestId('builder')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
        const v = await view(page);
        h.expect(v.status).toBe('draft');
        await h.expect(page.getByTestId('builder-day')).toHaveCount(v.days.length);
      }, { writes: true }),
    step('For the first night she adds the agency\'s own hotel, with its selling price and net cost.',
      'Cho đêm đầu, chị thêm khách sạn riêng của đại lý, với giá bán và giá vốn.',
      async (page, h) => {
        await h.click(page.getByTestId('builder-day').filter({ hasText: /^Day 1\b/ }).first());
        const block = page.getByTestId('builder-block').first();
        if (await block.getByTestId('builder-option').filter({ hasText: HOTEL }).count()) return R.reuse(h, 'the hotel option');
        await h.click(block.getByRole('button', { name: '+ Add' }));
        const drawer = block.getByTestId('builder-drawer');
        await h.click(drawer.getByRole('button', { name: 'Agency item' }));
        await R.type(page, h, drawer.getByTestId('builder-agency-title'), HOTEL);
        await R.type(page, h, drawer.getByTestId('builder-agency-sell'), '300');
        await R.type(page, h, drawer.getByTestId('builder-agency-net'), '180');
        const saved = page.waitForResponse((r) => r.url().includes('/options') && r.request().method() === 'POST', { timeout: 30_000 });
        await h.click(drawer.getByRole('button', { name: 'Add item' }));
        h.expect((await saved).status()).toBe(201);
        await h.expect(block.getByTestId('builder-option').filter({ hasText: HOTEL })).toHaveCount(1, { timeout: 15_000 });
      }, { writes: true }),
    step('On day two, the day the tour departs, she adds a block for the Adventure Asia tour.',
      'Ở ngày thứ hai, ngày tour khởi hành, chị thêm một nhóm cho tour Adventure Asia.',
      async (page, h) => {
        await h.click(page.getByTestId('builder-day').filter({ hasText: /^Day 2\b/ }).first());
        if (await tourBlock(page).count()) return R.reuse(h, 'the tour block');
        const form = page.getByTestId('builder-add-block');
        await h.scrollTo(form);
        await R.type(page, h, form.locator('input[name="title"]'), BLOCK);
        await R.choose(h, form.locator('select[name="type"]'), 'activity');
        await h.click(form.getByRole('button', { name: 'Add block' }));
        await h.expect(tourBlock(page)).toHaveCount(1, { timeout: 15_000 });
      }, { writes: true }),
    step('She searches the Adventure Asia catalogue and picks the tour, the whole trip plan and the fixed departure.',
      'Chị tìm trong danh mục Adventure Asia và chọn tour, cả hành trình và ngày khởi hành cố định.',
      async (page, h) => {
        const block = tourBlock(page);
        await h.scrollTo(block);
        if (await block.getByTestId('builder-option').count()) return R.reuse(h, 'the AA option');
        await h.click(block.getByRole('button', { name: '+ Add' }));
        const drawer = block.getByTestId('builder-drawer');
        await h.click(drawer.getByRole('button', { name: 'AA inventory' }));
        const words = String(s.departure.tour_title || '').split(/\s+/).filter(Boolean).slice(0, 3).join(' ');
        await R.type(page, h, drawer.getByTestId('builder-aa-search'), words || s.departure.tour_source_id);
        await h.click(drawer.getByRole('button', { name: 'Search', exact: true }));
        const tour = drawer.getByTestId('builder-aa-tour');
        await h.expect(tour.locator(`option[value="${s.departure.tour_source_id}"]`)).toHaveCount(1, { timeout: 30_000 });
        await R.choose(h, tour, s.departure.tour_source_id);
        const comp = drawer.getByTestId('builder-aa-component');
        await h.expect(comp).toBeVisible({ timeout: 30_000 });
        const tp = await comp.locator('option').evaluateAll((os) => (os.find((o) => o.value.startsWith('tp:')) || {}).value);
        if (!tp) throw new Error('tour X has no trip plan component');
        await R.choose(h, comp, tp);
        const dep = drawer.getByLabel('Fixed departure');
        await h.expect(dep.locator(`option[value="${s.departure.departure_id}"]`)).toBeEnabled();
        await R.choose(h, dep, s.departure.departure_id);
        await R.type(page, h, drawer.getByTestId('builder-aa-sell'), String(1500 * s.adults));
      }, { writes: true }),
    step('Adding it asks Adventure Asia for a live quote. The net cost for this agency and the availability come back on the option.',
      'Khi thêm, hệ thống hỏi giá trực tiếp từ Adventure Asia. Giá vốn dành cho đại lý này và tình trạng chỗ hiện ngay trên lựa chọn.',
      async (page, h) => {
        const block = tourBlock(page);
        if (!(await block.getByTestId('builder-option').count())) {
          const drawer = block.getByTestId('builder-drawer');
          const saved = page.waitForResponse((r) => /\/aa-options$/.test(new URL(r.url()).pathname) && r.request().method() === 'POST', { timeout: 60_000 });
          await h.click(drawer.getByRole('button', { name: 'Add AA item' }));
          const res = await saved;
          if (res.status() !== 201) throw new Error(`AA option answered ${res.status()} ${(await res.text()).slice(0, 160)}`);
        } else R.reuse(h, 'the AA option');
        await h.expect(block.getByTestId('builder-option')).toHaveCount(1, { timeout: 20_000 });
        const v = await view(page);
        const aa = v.days.flatMap((d) => d.blocks).flatMap((b) => b.options).find((o) => o.source === 'aa');
        h.expect(aa, 'an AA option').toBeTruthy();
        h.expect(aa.net_amount, 'the Booking quote (net) is on the option').not.toBeNull();
        h.expect(['instant', 'on_request']).toContain(aa.availability);
        s = R.save({ aa_option: { option_id: aa.option_id || aa.proposal_option_id || null, net_amount: aa.net_amount, currency: v.currency || 'USD', availability: aa.availability } });
        module.exports.meta.aa_option = s.aa_option;
        await h.hover(block.getByTestId('builder-option').first());
      }, { writes: true }),
    step('She lists what the price includes and what it does not: the airport pick-up is in, flights and insurance are not.',
      'Chị ghi rõ giá đã gồm gì và chưa gồm gì: có đón sân bay, chưa gồm vé máy bay và bảo hiểm.',
      async (page, h) => {
        const panel = page.getByTestId('builder-inclusions');
        await h.scrollTo(panel);
        const lines = [
          ['included', 'Airport pick-up on arrival', 'Đón sân bay khi đến'],
          ['not_included', 'International flights', 'Vé máy bay quốc tế'],
          ['not_included', 'Travel insurance', 'Bảo hiểm du lịch'],
        ];
        const has = async (k, en) => (await panel.getByTestId(`incl-list-${k}`).getByTestId('incl-line').filter({ hasText: en }).count()) > 0;
        if (await has('included', lines[0][1])) return R.reuse(h, 'the inclusion lines');
        const form = panel.getByTestId('incl-typed-form');
        for (const [k, en, vi] of lines) {
          await R.choose(h, form.locator('select').first(), k);
          await R.type(page, h, form.locator('input').nth(0), en);
          await R.type(page, h, form.locator('input').nth(1), vi);
          await h.click(form.getByRole('button', { name: 'Add to this proposal' }));
        }
        const saved = page.waitForResponse((r) => /\/inclusions$/.test(new URL(r.url()).pathname) && r.request().method() === 'PUT', { timeout: 30_000 });
        await h.click(panel.getByTestId('incl-save').getByRole('button'));
        h.expect((await saved).status()).toBeLessThan(300);
        for (const [k, en] of lines) await h.expect(panel.getByTestId(`incl-list-${k}`).getByTestId('incl-line').filter({ hasText: en })).toHaveCount(1, { timeout: 15_000 });
      }, { writes: true }),
    step('She sets the date the balance is due.',
      'Chị đặt ngày khách thanh toán phần còn lại.',
      async (page, h) => {
        const settings = page.getByTestId('builder-settings');
        await h.scrollTo(settings);
        const due = settings.getByTestId('date-input').nth(1);
        const balanceOn = R.day(10);
        if ((await due.inputValue().catch(() => '')) === balanceOn) return R.reuse(h, 'the balance date');
        await R.type(page, h, due, balanceOn);
        const saved = page.waitForResponse((r) => /\/builder$/.test(new URL(r.url()).pathname) && r.request().method() === 'PATCH', { timeout: 30_000 });
        await h.click(settings.getByRole('button', { name: 'Save', exact: true }));
        h.expect((await saved).status()).toBeLessThan(300);
      }, { writes: true }),
    step('To win the client she offers a discount above the agency\'s limit. The builder says the owner must approve it first.',
      'Để chốt khách, chị đưa mức giảm giá cao hơn giới hạn của đại lý. Trình dựng báo rằng chủ đại lý phải duyệt trước.',
      async (page, h) => {
        let v = await view(page);
        const limit = Number(v.pricing.discount.limit_pct);
        const pct = Math.min(limit + 5, 50);
        if (pct <= limit) throw new Error(`the agency's discount limit is ${limit} %: no discount above it can be rehearsed`);
        const box = page.getByTestId('builder-discount');
        await h.scrollTo(box);
        if (Number(v.pricing.discount.discount_pct || 0) !== pct) {
          await R.type(page, h, box.locator('input').first(), String(pct));
          const saved = page.waitForResponse((r) => /\/builder$/.test(new URL(r.url()).pathname) && r.request().method() === 'PATCH', { timeout: 30_000 });
          await h.click(box.getByTestId('builder-discount-save').getByRole('button'));
          h.expect((await saved).status()).toBeLessThan(300);
        } else R.reuse(h, 'the discount');
        await h.expect(page.getByTestId('builder-discount')).toHaveAttribute('data-needs-approval', 'true', { timeout: 15_000 });
        v = await view(page);
        h.expect(v.pricing.discount.above_limit).toBe(true);
        s = R.save({ discount_pct: pct, discount_limit_pct: limit });
        module.exports.meta.discount = { pct, limit };
      }, { writes: true }),
    step('She asks the owner to approve. Publishing stays locked for her until the owner says yes.',
      'Chị gửi chủ đại lý duyệt. Chị chưa thể phát hành báo giá cho tới khi chủ đại lý đồng ý.',
      async (page, h) => {
        const box = page.getByTestId('builder-discount');
        if (!(await box.getByTestId('builder-discount-pending').count())) {
          const asked = page.waitForResponse((r) => /\/discount-approval$/.test(new URL(r.url()).pathname) && r.request().method() === 'POST', { timeout: 30_000 });
          await h.click(box.getByTestId('builder-discount-request').getByRole('button'));
          h.expect((await asked).status()).toBeLessThan(300);
        } else R.reuse(h, 'the approval request');
        await h.expect(box.getByTestId('builder-discount-pending')).toBeVisible({ timeout: 15_000 });
        const v = await view(page);
        h.expect(v.pricing.discount.pending, 'a pending request').toBeTruthy();
        h.expect(v.checks.blocking).toContain('discount_needs_approval');
        const publish = page.getByTestId('builder-header').getByRole('button', { name: /^Publish v\d+$/ });
        await h.expect(publish).toBeDisabled();
        await h.hover(box.getByTestId('builder-discount-pending'));
        R.save({ discount_approval_id: v.pricing.discount.pending.discount_approval_id, r07_done_at: new Date().toISOString() });
        module.exports.meta.blocking = v.checks.blocking;
        await R.sha(page, module.exports, 'end');
      }, { writes: true }),
  ],
});
