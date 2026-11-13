// UAT scenario REH-05 (pilot rehearsal step 5, runbook docs/ops/runbooks/pilot-rehearsal.md): a traveller plans on the
// synthetic agency's own planner, tripplanner.<dev host>/pilot-rehearsal-01/plan, as a guest (no sign-in). 1440 x 900.
// PAID: the experience search (one embedding call) and three planning chat turns (a chat model call each, about
// 0.03-0.07 USD together, CIS LLM ledger rows with the agency's tenant id). Runs only with UAT_ALLOW_PAID=1 (or
// dryrun.cjs --allow-paid); a --preview stops before the search.
// Writes: the guest trip (POST /api/trip: apply the tour's route) and exactly three chat turns (a page route aborts a
// fourth). Narration is blocked. The web ACL's silent challenge posts its proof to AWS WAF's token host (allowed).
// Needs (in this order in the rehearsal): the agency provisioned with the TripPlanner add-on (step 1) and tour X
// adopted by the agency (step 3); its brand colours set on its TripPlanner site (see the rehearsal README: the planner
// shows the kit colours until a theme is stored). Env UAT_REH_TOUR_X names tour X (scenarios/tripplanner/_rehearsal.cjs).
// Given: a guest on the agency's planner. When: they search "Laos", pin tour X from the agency's tour list and ask the
// planning chat three questions. Then: the planner carries the agency's name and colours, lists only the agency's
// tours, holds tour X's days, and the chat answers each turn.
// The phone half of step 5 (reorder at 390 px) is REH-05.m.
const { HOSTS, step } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const R = require('./_rehearsal.cjs');

const meta = {};
let counts = null;
// Three short questions that fit any tour: the chat may answer with a proposal card, which is not applied here.
const QUESTIONS = [
  'We are two adults travelling in March. Is the pace of this trip relaxed enough?',
  'Could we add a rest day somewhere in the middle?',
  'What should we pack for this trip?',
];

module.exports = rw({
  id: 'REH-05',
  app: 'tripplanner',
  identity: 'traveller',
  paid: true,
  title: 'Plan on the agency\'s own trip planner: search, add a tour, chat',
  titleVi: 'Lập kế hoạch trên trang của đại lý: tìm kiếm, thêm tour, trò chuyện',
  baseURL: HOSTS.tripplanner,
  allowWrites: [R.WRITES.trip, R.WRITES.chat],
  blockUrls: R.NO_NARRATION,
  meta,
  steps: [
    step('A traveller opens the trip planner on the agency\'s own address. It carries the agency\'s name and brand colours.',
      'Khách du lịch mở trang lập kế hoạch trên địa chỉ riêng của đại lý. Trang mang tên và màu thương hiệu của đại lý.',
      async (page, h) => {
        counts = await limitWrites(page, [{ name: 'chat', path: R.PATHS.chat, max: QUESTIONS.length }]);
        await R.openPlanner(page, h);
        meta.accent = await R.assertBrand(page, h);
        await h.hover(page.locator('header').first().getByText(R.AGENCY).first());
      }),
    step('They search for Laos. The map shows the places that match, best first.',
      'Khách tìm "Laos". Bản đồ hiện các địa điểm phù hợp, phù hợp nhất ở trên.',
      async (page, h) => {
        const input = page.getByRole('textbox', { name: 'Search experiences' });
        const searched = page.waitForResponse((r) => {
          const u = new URL(r.url());
          return u.pathname === '/api/browse/search' && u.searchParams.get('q') === 'Laos';
        }, { timeout: 60_000 });
        await h.click(input);
        await input.pressSequentially('Laos', { delay: h.fast ? 0 : 120 });
        const res = await searched;
        if (res.status() !== 200) throw new Error(`the search answered ${res.status()} (202 = the web ACL challenged it)`);
        await h.expect(page.getByText(/\d+ places? match “Laos”, best first\./)).toBeVisible({ timeout: 30_000 });
      }, { writes: true }), // paid (an embedding call): a --preview stops here
    step('The list of tours holds only this agency\'s own tours. The traveller pins the route of the rehearsal tour.',
      'Danh sách tour chỉ gồm các tour của chính đại lý. Khách thêm lộ trình của tour diễn tập vào chuyến đi.',
      async (page, h) => {
        await R.addTourX(page, h, meta);
      }, { writes: true }),
    step('Back on the map, Your trip now holds the tour\'s days, stop by stop.',
      'Quay lại bản đồ, mục Chuyến đi của bạn giờ có các ngày của tour, từng điểm dừng.',
      async (page, h) => {
        await h.click(page.getByRole('button', { name: 'Map', exact: true }));
        await h.expect(page.getByRole('tab', { name: 'Your trip' })).toHaveAttribute('aria-selected', 'true');
        meta.stops = (await R.tripStops(page, h, 2)).length;
        await h.hover(page.getByTestId('day').first());
      }),
    step('The traveller opens Plan with chat and asks about the pace of the trip.',
      'Khách mở mục Lập kế hoạch bằng trò chuyện và hỏi về nhịp độ của chuyến đi.',
      async (page, h) => ask(page, h, 0), { writes: true }),
    step('A second question: a rest day in the middle. The answer can propose a change, which the traveller may apply.',
      'Câu hỏi thứ hai: thêm một ngày nghỉ ở giữa. Câu trả lời có thể đề xuất thay đổi để khách áp dụng nếu muốn.',
      async (page, h) => ask(page, h, 1), { writes: true }),
    step('A third question about packing. Every answer the model wrote carries the AI label. This is the end of the scenario.',
      'Câu hỏi thứ ba về hành lý cần mang. Mọi câu trả lời do mô hình viết đều có nhãn AI. Kết thúc kịch bản.',
      async (page, h) => {
        await ask(page, h, 2);
        if (counts.chat !== QUESTIONS.length) throw new Error(`${counts.chat} chat requests in this run (exactly ${QUESTIONS.length} expected)`);
        meta.chat_turns = counts.chat;
        // The model answered at least once (a paid turn really ran), and each model answer carries its AI notice.
        const written = page.getByTestId('chat-assistant').filter({ has: page.locator('[data-ai-generated="true"]') });
        meta.ai_answers = await written.count();
        if (!meta.ai_answers) throw new Error('no chat answer was written by the model (all three were server sentences)');
        await h.expect(written.getByTestId('chat-ai-notice')).toHaveCount(meta.ai_answers);
      }, { writes: true }),
  ],
});

/** Send question `i` and wait for its answer: a real reply, never a notice (paused, budget, limit or bot check). */
async function ask(page, h, i) {
  const tab = page.getByRole('tab', { name: 'Plan with chat' });
  if ((await tab.getAttribute('aria-selected')) !== 'true') {
    await h.click(tab);
    await h.expect(page.getByTestId('plan-chat')).toBeVisible({ timeout: 30_000 });
  }
  const input = page.getByTestId('chat-input');
  await h.click(input);
  await input.pressSequentially(QUESTIONS[i], { delay: h.fast ? 0 : 25 });
  const answered = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/trip/chat' && r.request().method() === 'POST', { timeout: 120_000 });
  await h.click(page.getByTestId('chat-send'));
  const res = await answered;
  if (res.status() !== 200) throw new Error(`chat turn ${i + 1} answered ${res.status()}`);
  const answers = page.getByTestId('chat-assistant');
  await h.expect(answers).toHaveCount(i + 1, { timeout: 60_000 });
  const last = answers.nth(i);
  const notice = last.locator('[role="status"]');
  if (await notice.count()) throw new Error(`chat turn ${i + 1} got a notice, not an answer: ${(await notice.innerText()).slice(0, 120)}`);
  await h.scrollTo(last, 'end');
}
