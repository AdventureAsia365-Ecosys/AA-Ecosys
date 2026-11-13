// UAT scenario REH-05.m (pilot rehearsal step 5, the phone half; runbook docs/ops/runbooks/pilot-rehearsal.md): on a
// phone (390 x 844, a real mobile context), a guest pins tour X on the synthetic agency's planner and reorders its stops
// with the handle's move menu (the single-pointer way of the planner's drag and drop). $0: no search, no chat, no
// narration (paid paths blocked). Writes: the guest trip only (POST /api/trip, ops apply_route and reorder, at most
// four with the planner's cookie retries; any other op or method is aborted and fails the take).
// Needs: tour X adopted by the agency (step 3), with a planner route of at least two stops; env UAT_REH_TOUR_X
// (scenarios/tripplanner/_rehearsal.cjs).
// Given: a guest on a phone. When: they pin tour X from the agency's tour list, open Your trip and move the first stop
// down. Then: the planner fits the screen, the order changes and is saved ("New order saved."), with an undo.
const { HOSTS, PHONE, step, assertNoSideScroll } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const R = require('./_rehearsal.cjs');

const meta = {};
let before = null;
let counts = null;

module.exports = rw({
  id: 'REH-05.m',
  app: 'tripplanner',
  identity: 'traveller',
  paid: false,
  title: 'On a phone: add the agency\'s tour and reorder its stops',
  titleVi: 'Trên điện thoại: thêm tour của đại lý và sắp xếp lại các điểm dừng',
  baseURL: HOSTS.tripplanner,
  viewport: PHONE,
  allowWrites: [R.WRITES.trip],
  blockUrls: [...R.paidBlocks(), '/api/trip/chat(?:[?#]|$)'],
  meta,
  steps: [
    step('On a phone, the agency\'s planner opens under the agency\'s name and fits the screen.',
      'Trên điện thoại, trang lập kế hoạch của đại lý mở với tên đại lý và vừa màn hình.',
      async (page, h) => {
        // One apply-route POST and one reorder POST, each with the planner's one retry (cookies refreshed): at most four.
        counts = await limitWrites(page, [{ name: 'trip', path: R.PATHS.trip, max: 4, accept: R.tripOps('apply_route', 'reorder') }]);
        await R.openPlanner(page, h, meta);
        await h.expect(page.locator('nav').getByRole('button', { name: /Explore/ })).toBeVisible({ timeout: 30_000 });
        await assertNoSideScroll(page);
      }),
    step('The traveller opens the list of the agency\'s tours and pins the route of the rehearsal tour.',
      'Khách mở danh sách tour của đại lý và thêm lộ trình của tour diễn tập vào chuyến đi.',
      async (page, h) => {
        await R.addTourX(page, h, meta);
      }, { writes: true }),
    step('Your trip shows the tour\'s days. Each stop has a handle to move it.',
      'Mục Chuyến đi của bạn hiện các ngày của tour. Mỗi điểm dừng có một tay nắm để di chuyển.',
      async (page, h) => {
        await h.click(page.locator('nav').getByRole('button', { name: /Your trip/ }));
        meta.stops = await R.tripStopCount(page, h, 2);
        before = await R.tripDays(page, h, 1);
        meta.days = before.length;
        await h.expect(page.getByTestId('stop-handle').first()).toBeVisible({ timeout: 30_000 });
        await assertNoSideScroll(page);
      }),
    step('A tap on the first stop\'s handle opens its moves. The traveller picks Move down.',
      'Chạm vào tay nắm của điểm dừng đầu tiên để mở menu di chuyển. Khách chọn Move down.',
      async (page, h) => {
        await h.click(page.getByTestId('stop-handle').first());
        const menu = page.getByTestId('reorder-menu');
        await h.expect(menu).toBeVisible({ timeout: 10_000 });
        const saved = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/trip' && r.request().method() === 'POST', { timeout: 30_000 });
        await h.click(menu.getByTestId('move-down'));
        const res = await saved;
        if (res.status() !== 200) throw new Error(`the reorder answered ${res.status()}`);
      }, { writes: true }),
    step('The new order is saved, with an undo. Nothing scrolls sideways. This is the end of the scenario.',
      'Thứ tự mới đã được lưu, có nút hoàn tác. Trang không bị cuộn ngang. Kết thúc kịch bản.',
      async (page, h) => {
        await h.expect(page.getByTestId('reorder-saved')).toContainText('New order saved.', { timeout: 30_000 });
        await h.expect(page.getByTestId('reorder-failed')).toHaveCount(0);
        const after = await R.tripDays(page, h, 1);
        if (after.join('\n') === before.join('\n')) throw new Error('the stop order did not change after Move down');
        if (counts.trip_refused) throw new Error(`the page tried ${counts.trip_refused} trip write(s) this take does not make (aborted)`);
        await h.hover(page.getByTestId('reorder-undo'));
        await assertNoSideScroll(page);
      }),
  ],
});
