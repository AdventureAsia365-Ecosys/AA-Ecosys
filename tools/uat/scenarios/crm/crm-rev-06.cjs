// CRM review R06 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): the day-by-day proposal builder with an
// Adventure Asia tour on a real departure.
// Given: A (owner) signed in; the R03 trip at Proposal with dates (R04); prep chose an AA departure with >= 2 seats.
// When:  the owner starts the builder, adds an agency hotel on night 1, adds an activity block on day 2 and puts the
//        AA tour on it for the chosen departure (live quote from Booking), reads the totals, sets the balance date,
//        publishes version 1 and sends it from the trip (the link is shown once, blurred; R08 opens it).
// Then:  the skeleton has one day per night plus arrival, the agency option shows, the AA option comes back priced
//        (net present) with its availability, the version is published then sent; the map is not built yet
//        ("Not ready yet" card). The client link goes to work/crm/.secrets.json (r08_link with its trip id, chmod 600), never a log.
// Writes a proposal on the invented R03 trip; adding an AA option takes no seat (only a client hold does). A re-run
// skips what exists in --fast only; a recorded take on an old draft stops (re-run crm-rev-03 and crm-rev-04).
// No LLM call, never clicks an AI button. Cost $0.
const slide = require('../../lib/slide.cjs');
const { st, base, sha, open, bffOk, type, choose, day, reuse } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-06', title: 'Proposal builder: day by day, with an Adventure Asia tour at a live price', titleVi: 'Trình dựng đề xuất: từng ngày, kèm tour Adventure Asia giá trực tiếp' });
let s;
let pid;

const view = (page) => bffOk(page, 'GET', `proposals/${pid}/builder`);

sc.steps = [
  {
    caption: {
      en: 'On the trip, the owner starts the day-by-day proposal builder in US dollars.',
      vi: 'Trên trang chuyến, chủ đại lý mở trình dựng đề xuất theo từng ngày, tính bằng đô la Mỹ.',
    },
    run: async (page, h) => {
      s = st.load();
      if (!s.r03 || !s.departure) throw new Error('run prep, crm-rev-03 and crm-rev-04 first');
      await sha(page, sc, 'start');
      await open(page, h, `/pipeline/${s.r03.trip_id}`, 'crm-trip');
      await h.expect(page.getByTestId('trip-stage')).toHaveAttribute('data-stage', 'proposal');
      await h.expect(page.getByTestId('crm-trip')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
      if (s.r06 && s.r06.trip_id === s.r03.trip_id) {
        reuse(h, 'the builder draft of the R03 trip', 're-run crm-rev-03 and crm-rev-04 for a fresh trip');
        pid = s.r06.proposal_id; // a --fast rehearsal: open the same draft
        await open(page, h, `/pipeline/${s.r03.trip_id}/proposal/${pid}`, 'builder');
      } else {
        const section = page.getByTestId('proposal-builder');
        await h.scrollTo(section);
        await type(page, h, section.getByTestId('builder-currency'), 'USD');
        await h.click(section.getByRole('button', { name: 'Start the builder' }));
        await page.waitForURL(/\/proposal\/[0-9a-f-]{36}$/, { timeout: 30_000 });
        pid = page.url().split('/').pop();
        s.r06 = { trip_id: s.r03.trip_id, proposal_id: pid };
        st.save(s);
      }
      await h.expect(page.getByTestId('builder')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
    },
  },
  {
    caption: {
      en: 'The builder lays out the trip from the dates and the inquiry: one day per night, each with a place to stay.',
      vi: 'Trình dựng tự dàn chuyến từ ngày đi và yêu cầu ban đầu: mỗi ngày ứng với một đêm nghỉ, ngày nào cũng có chỗ ở.',
    },
    run: async (page, h) => {
      const v = await view(page);
      h.expect(v.status).toBe('draft');
      h.expect(v.days.length).toBeGreaterThanOrEqual(3);
      await h.expect(page.getByTestId('builder-day')).toHaveCount(v.days.length);
      await h.hover(page.getByTestId('builder-day').nth(1));
      await h.hover(page.getByTestId('builder-rooms-line').first());
    },
  },
  {
    caption: {
      en: 'For the first night the agency adds its own hotel, with the selling price and its net cost.',
      vi: 'Cho đêm đầu, đại lý thêm khách sạn của mình, với giá bán và giá vốn.',
    },
    run: async (page, h) => {
      const title = 'Hoi An riverside boutique';
      await h.click(page.getByTestId('builder-day').filter({ hasText: /^Day 1\b/ }).first());
      const block = page.getByTestId('builder-block').first();
      if (await block.getByTestId('builder-option').filter({ hasText: title }).count()) reuse(h, 'the hotel option');
      else {
        await h.click(block.getByRole('button', { name: '+ Add' }));
        const drawer = block.getByTestId('builder-drawer');
        await h.click(drawer.getByRole('button', { name: 'Agency item' }));
        await type(page, h, drawer.getByTestId('builder-agency-title'), title);
        await type(page, h, drawer.getByTestId('builder-agency-sell'), '300');
        await type(page, h, drawer.getByTestId('builder-agency-net'), '180');
        const saved = page.waitForResponse((r) => r.url().includes('/options') && r.request().method() === 'POST', { timeout: 30_000 });
        await h.click(drawer.getByRole('button', { name: 'Add item' }));
        h.expect((await saved).status()).toBe(201);
      }
      await h.expect(block.getByTestId('builder-option').filter({ hasText: title })).toHaveCount(1, { timeout: 15_000 });
    },
  },
  {
    caption: {
      en: 'On day two the owner adds an activity block for an island tour.',
      vi: 'Ở ngày thứ hai, chủ đại lý thêm một nhóm hoạt động cho tour đảo.',
    },
    run: async (page, h) => {
      await h.click(page.getByTestId('builder-day').filter({ hasText: /^Day 2\b/ }).first());
      const block = page.getByTestId('builder-block').filter({ hasText: 'Island tour' });
      if (await block.count()) reuse(h, 'the Island tour block');
      else {
        const form = page.getByTestId('builder-add-block');
        await h.scrollTo(form);
        await type(page, h, form.locator('input[name="title"]'), 'Island tour');
        await choose(h, form.locator('select[name="type"]'), 'activity');
        await h.click(form.getByRole('button', { name: 'Add block' }));
      }
      await h.expect(block).toHaveCount(1, { timeout: 15_000 });
    },
  },
  {
    caption: {
      en: 'Into that block goes an Adventure Asia tour: the owner searches the AA catalogue and picks the tour.',
      vi: 'Vào nhóm đó, chủ đại lý đưa một tour của Adventure Asia: tìm trong danh mục AA và chọn tour.',
    },
    run: async (page, h) => {
      const block = page.getByTestId('builder-block').filter({ hasText: 'Island tour' });
      await h.scrollTo(block);
      if (await block.getByTestId('builder-option').count()) return reuse(h, 'the AA option'); // --fast only
      await h.click(block.getByRole('button', { name: '+ Add' }));
      const drawer = block.getByTestId('builder-drawer');
      await h.click(drawer.getByRole('button', { name: 'AA inventory' }));
      await type(page, h, drawer.getByTestId('builder-aa-search'), 'Tropical Jewels');
      await h.click(drawer.getByRole('button', { name: 'Search', exact: true }));
      const tour = drawer.getByTestId('builder-aa-tour');
      await h.expect(tour.locator(`option[value="${s.departure.tour_source_id}"]`)).toHaveCount(1, { timeout: 30_000 });
      await choose(h, tour, s.departure.tour_source_id);
      await h.expect(drawer.getByTestId('builder-aa-component')).toBeVisible({ timeout: 30_000 });
    },
  },
  {
    caption: {
      en: 'The owner picks the whole trip plan on a fixed departure that still has seats, and sets the selling price.',
      vi: 'Chủ đại lý chọn cả hành trình theo một ngày khởi hành cố định còn chỗ, rồi nhập giá bán.',
    },
    run: async (page, h) => {
      const block = page.getByTestId('builder-block').filter({ hasText: 'Island tour' });
      if (await block.getByTestId('builder-option').count()) return reuse(h, 'the AA option');
      const drawer = block.getByTestId('builder-drawer');
      const comp = drawer.getByTestId('builder-aa-component');
      const tp = await comp.locator('option').evaluateAll((os) => (os.find((o) => o.value.startsWith('tp:')) || {}).value);
      if (!tp) throw new Error('the AA tour has no trip plan component');
      await choose(h, comp, tp);
      const dep = drawer.getByLabel('Fixed departure');
      await h.expect(dep.locator(`option[value="${s.departure.departure_id}"]`)).toBeEnabled();
      await choose(h, dep, s.departure.departure_id);
      await type(page, h, drawer.getByTestId('builder-aa-sell'), '1500');
    },
  },
  {
    caption: {
      en: 'Adding it asks Adventure Asia for a live quote. The net cost and the availability come back on the option.',
      vi: 'Khi thêm, hệ thống hỏi giá trực tiếp từ Adventure Asia. Giá vốn và tình trạng chỗ hiện ngay trên lựa chọn.',
    },
    run: async (page, h) => {
      const block = page.getByTestId('builder-block').filter({ hasText: 'Island tour' });
      if (await block.getByTestId('builder-option').count()) reuse(h, 'the AA option');
      else {
        const drawer = block.getByTestId('builder-drawer');
        const saved = page.waitForResponse((r) => /\/aa-options$/.test(new URL(r.url()).pathname) && r.request().method() === 'POST', { timeout: 60_000 });
        await h.click(drawer.getByRole('button', { name: 'Add AA item' }));
        const res = await saved;
        if (res.status() !== 201) throw new Error(`AA option answered ${res.status()} ${(await res.text()).slice(0, 160)}`);
      }
      await h.expect(block.getByTestId('builder-option')).toHaveCount(1, { timeout: 20_000 });
      const v = await view(page);
      const aa = v.days.flatMap((d) => d.blocks).flatMap((b) => b.options).find((o) => o.source === 'aa');
      h.expect(aa, 'an AA option').toBeTruthy();
      h.expect(aa.net_amount).not.toBeNull();
      h.expect(['instant', 'on_request']).toContain(aa.availability);
      sc.meta.aa_option = { availability: aa.availability, departure: s.departure.start_date };
      await h.hover(block.getByTestId('builder-option').first());
    },
  },
  {
    caption: {
      en: 'The totals show the selling price, the net cost and the margin of the whole proposal.',
      vi: 'Phần tổng cho thấy giá bán, giá vốn và biên lợi nhuận của cả đề xuất.',
    },
    run: async (page, h) => {
      const totals = page.getByTestId('builder-totals');
      await h.scrollTo(totals);
      await h.expect(totals).toContainText('%');
      await h.hover(totals);
    },
  },
  {
    caption: {
      en: 'The owner sets when the balance is due and publishes version one. Only a published version can go to the client.',
      vi: 'Chủ đại lý đặt ngày thanh toán phần còn lại rồi phát hành phiên bản một. Chỉ bản đã phát hành mới gửi được cho khách.',
    },
    run: async (page, h) => {
      const builder = page.getByTestId('builder');
      if ((await builder.getAttribute('data-status')) !== 'draft') {
        reuse(h, 'the published version');
      } else {
        const settings = page.getByTestId('builder-settings');
        await h.scrollTo(settings);
        const due = settings.getByTestId('date-input').nth(1);
        await type(page, h, due, day(10));
        const saved = page.waitForResponse((r) => /\/builder$/.test(new URL(r.url()).pathname) && r.request().method() === 'PATCH', { timeout: 30_000 });
        await h.click(settings.getByRole('button', { name: 'Save', exact: true }));
        h.expect((await saved).status()).toBeLessThan(300);
        const publish = page.getByTestId('builder-header').getByRole('button', { name: /^Publish v\d+$/ });
        await h.scrollTo(publish);
        await h.expect(publish).toBeEnabled({ timeout: 15_000 });
        await h.click(publish);
      }
      await h.expect(builder).toHaveAttribute('data-status', /^(published|sent)$/, { timeout: 20_000 });
    },
  },
  {
    caption: {
      en: 'On the trip, the owner sends it to the client. The private link is shown once; it is hidden in this video.',
      vi: 'Trên trang chuyến, chủ đại lý gửi đề xuất cho khách. Đường dẫn riêng chỉ hiện một lần; trong video này nó được che đi.',
    },
    run: async (page, h) => {
      await open(page, h, `/pipeline/${s.r03.trip_id}`, 'crm-trip');
      await h.expect(page.getByTestId('crm-trip')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
      const tab = page.getByTestId('trip-proposal');
      const send = tab.getByTestId('builder-send').getByRole('button');
      if (await send.count()) {
        await h.scrollTo(send);
        await h.click(send);
      } else {
        reuse(h, 'the sent version'); // --fast: a new link for R08 (the old one stops working)
        const again = tab.getByTestId('builder-reissue').getByRole('button');
        await h.scrollTo(again);
        await h.click(again);
      }
      const link = await tab.getByTestId('proposal-copy-link').first().inputValue({ timeout: 20_000 });
      if (!/\/c\/p\/[A-Za-z0-9_-]{43}$/.test(link)) throw new Error('the client link has an unexpected shape');
      st.saveLink('r08_link', link, s.r03.trip_id);
      await h.hover(tab.getByTestId('proposal-copy-links'));
      await h.assertMasked(['[data-testid="proposal-copy-links"]']);
      const v = await view(page);
      h.expect(v.status).toBe('sent');
    },
  },
  {
    caption: {
      en: 'Not ready yet: a map of each day\'s places inside the builder.',
      vi: 'Chưa có: bản đồ các điểm của từng ngày ngay trong trình dựng.',
    },
    run: async (page, h) => {
      await slide.notReady(page, h, {
        screen: 'Map in the proposal builder',
        missing: ['A map that shows the places of each day while the agency builds the proposal'],
      });
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
