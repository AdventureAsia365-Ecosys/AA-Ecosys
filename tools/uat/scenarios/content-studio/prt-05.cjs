// UAT scenario PRT-05 (AA-855 round 1, catalogue.json): the slate of topics, read only (no pick, no new plan).
// Given: the Content studio VIEWER of the E2E tenant (lib/signin.cjs studio).
// When:  they open Social Posts, move across two channel tabs, look at the quarter reallocation card, then Articles.
// Then:  the topic slate per channel, the reallocation card and the article topics render; no pick, no "Check for a
//        suggestion" (both are writes), nothing is written, no model is called. $0. Desktop 1440 x 900.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'PRT-05',
  app: 'content-studio',
  identity: 'studio',
  title: 'Slate: topics per channel and the quarter plan',
  titleVi: 'Danh sách chủ đề theo kênh và kế hoạch quý',
  baseURL: HOSTS.partner,
  steps: [
    step('Social Posts ranks topics from the agency\'s tours for each social channel, best first.',
      'Bài mạng xã hội xếp hạng các chủ đề từ tour của đại lý cho từng kênh, tốt nhất ở trên.',
      async (page, h) => {
        await check(page, h, '/portal/create/social', { heading: 'Social Posts' });
        await h.expect(page.getByText('Social topics').first()).toBeVisible({ timeout: 30_000 });
        await h.expect(page.getByTestId('slate-tabstrip')).toBeVisible({ timeout: 30_000 });
      }),
    step('Each channel has its own tab. Picking a topic starts the writer; here the topics are only read.',
      'Mỗi kênh có một thẻ riêng. Chọn một chủ đề sẽ mở trình viết; ở đây chỉ xem các chủ đề.',
      async (page, h) => {
        const tabs = page.getByTestId('slate-tabstrip').locator('button[aria-pressed]');
        await h.expect(tabs.first()).toBeVisible({ timeout: 30_000 });
        if ((await tabs.count()) > 1) {
          const second = tabs.nth(1);
          await h.click(second);
          await h.expect(second).toHaveAttribute('aria-pressed', 'true', { timeout: 15_000 });
        }
      }),
    step('Below the slate, the quarter card shows what would change if the plan were redone now. Nothing changes until the agency approves.',
      'Bên dưới là thẻ theo quý: cho thấy điều gì sẽ đổi nếu lập lại kế hoạch bây giờ. Không có gì thay đổi cho tới khi đại lý đồng ý.',
      async (page, h) => {
        const card = page.getByText(/Reallocation suggestion — Q\d \d{4}/).first();
        await h.scrollTo(card, 'center');
        await h.expect(card).toBeVisible({ timeout: 30_000 });
      }),
    step('Articles ranks blog topics by real search demand. This is the end of the scenario.',
      'Mục Bài viết xếp hạng chủ đề blog theo nhu cầu tìm kiếm thực tế. Kết thúc kịch bản.',
      async (page, h) => {
        await check(page, h, '/portal/create/article', { heading: 'Articles' });
        await h.expect(page.getByText('Article topics').first()).toBeVisible({ timeout: 30_000 });
      }),
  ],
});
