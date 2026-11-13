// Pilot rehearsal price setup, the traveller side (AA-1091; TripPlanner "From $X" reads Booking's from-prices), public.
// Given: a visitor with no account; env UAT_REH_TP_SLUGS = the TripPlanner slugs of three tours the price setup made
// sellable (REH-01-prices). When: they open each tour page. Then: each shows "From <price> per person" with the note
// that the advisor confirms the final price. Read only, no AI path (the planner and its search are not opened). $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');
const { listEnv } = require('../../lib/rehearsal-admin.cjs');

const SLUG = /^[a-z0-9][a-z0-9-]{1,120}$/;
let slugs = [];

async function fromPrice(page, h, slug) {
  await check(page, h, `/tours/${slug}`, { signedIn: false });
  const box = page.getByTestId('from-price').first();
  await h.scrollTo(box, 'center');
  await h.expect(box).toBeVisible({ timeout: 30_000 });
  await h.expect(box).toContainText(/From\s+\S*\d[\d,.]*\S*\s+per person/);
}

module.exports = ro({
  id: 'REH-01-from-price',
  app: 'tripplanner',
  identity: 'public',
  title: 'Pilot rehearsal: priced tours show a From price to travellers',
  titleVi: 'Diễn tập pilot: tour đã có giá hiện giá "Từ" cho khách du lịch',
  baseURL: HOSTS.tripplanner,
  prepare: async () => {
    slugs = listEnv('UAT_REH_TP_SLUGS');
    if (slugs.length < 3 || slugs.some((s) => !SLUG.test(s))) {
      throw new Error('BLOCKED: set UAT_REH_TP_SLUGS to three TripPlanner tour slugs of the tours priced for the rehearsal');
    }
  },
  steps: [
    step('A traveller opens the first tour that was just priced. It shows a From price per person.',
      'Khách du lịch mở tour đầu tiên vừa được nhập giá. Trang hiện giá "Từ" cho mỗi người.',
      async (page, h) => { await fromPrice(page, h, slugs[0]); }),
    step('The price is a suggestion for two travellers. The agency\'s advisor confirms the final price.',
      'Giá này là gợi ý cho hai khách. Tư vấn viên của đại lý sẽ xác nhận giá cuối cùng.',
      async (page, h) => {
        await h.expect(page.getByTestId('from-price').first()).toContainText('Your advisor confirms the final price');
      }),
    step('The second priced tour shows its From price too.',
      'Tour thứ hai đã có giá cũng hiện giá "Từ".',
      async (page, h) => { await fromPrice(page, h, slugs[1]); }),
    step('And the third one. This is the end of the scenario.',
      'Và tour thứ ba cũng vậy. Kết thúc kịch bản.',
      async (page, h) => { await fromPrice(page, h, slugs[2]); }),
  ],
});
