// UAT scenario PRT-02 (AA-855 round 1, catalogue.json): Brand identity (T0), an editor saves a change, then the old
// values come back. Writes on the synthetic E2E tenant only (the pilot guard refuses any other tenant before the
// browser opens); the one write the browser lets through is the brand save (allowWrites), anything else is aborted.
// Given: the Content studio EDITOR of the E2E tenant (lib/signin.cjs studio-editor, signed in unrecorded).
// When:  they open Brand identity, change the default call to action, save it as a new version, then the old values
//        are saved back.
// Then:  the saved notice and the next version number show; at the end the field holds its old text again (after()
//        restores it even when a step failed). No LLM call (the brand save stores text). Cost $0. Desktop 1440 x 900.
const { HOSTS, step } = require('../../lib/dryrun-page.cjs');
const { rw, studioCall } = require('../../lib/uat-page.cjs');

const BRAND = '/api/tenant/admin/brand-identity';
// Invented text, shown on screen: no real agency wording.
const NEW_CTA = 'Ask us for the full day-by-day plan and the next free dates';
// The fields the brand form saves (BrandTab.tsx save()), rebuilt from the GET answer to put the old values back.
const LIST_FIELDS = ['target_markets', 'tone_of_voice'];
const TEXT_FIELDS = ['system_prompt', 'style_guide', 'brand_name', 'brand_type', 'core_idea', 'customer_segment',
  'customer_mindset', 'good_examples', 'default_cta'];

let before = null; // the brand record read at the start
let changed = false; // a save of NEW_CTA went through
let restored = false;

function bodyFrom(d) {
  const out = {};
  for (const k of TEXT_FIELDS) out[k] = d[k] ?? '';
  for (const k of LIST_FIELDS) out[k] = Array.isArray(d[k]) ? d[k] : [];
  let fw = d.forbidden_words;
  if (typeof fw === 'string') { try { fw = JSON.parse(fw || '[]'); } catch { fw = []; } }
  out.forbidden_words = Array.isArray(fw) ? fw : [];
  return out;
}

async function restore(page) {
  const r = await studioCall(page, 'POST', BRAND, bodyFrom(before));
  if (r.status >= 300) throw new Error(`putting the old brand values back answered ${r.status}`);
  restored = true;
}

const ctaField = (page) => page.getByLabel('Default Call to Action', { exact: true });

const sc = rw({
  id: 'PRT-02',
  app: 'content-studio',
  identity: 'studio-editor',
  title: 'Brand identity: an editor saves a new version',
  titleVi: 'Nhận diện thương hiệu: biên tập viên lưu một phiên bản mới',
  baseURL: HOSTS.partner,
  allowWrites: [`${BRAND.replace(/\//g, '\\/')}$`],
  steps: [
    step('Brand identity tells the writer who the agency is and who it writes for. Every piece follows the active version.',
      'Nhận diện thương hiệu cho người viết biết đại lý là ai và viết cho ai. Mọi bài viết theo phiên bản đang dùng.',
      async (page, h) => {
        await h.goto('/portal/brand');
        await h.expect(page.getByRole('heading', { name: 'Brand Identity' })).toBeVisible({ timeout: 30_000 });
        await h.expect(page.getByText(/Active — Version \d+/).first()).toBeVisible({ timeout: 30_000 });
        const r = await studioCall(page, 'GET', BRAND);
        if (r.status !== 200 || !r.data || typeof r.data !== 'object') throw new Error(`reading the brand answered ${r.status}`);
        before = r.data;
        if ((before.default_cta || '') === NEW_CTA) throw new Error('the call to action already holds the test text: an earlier run did not restore it');
      }),
    step('The editor changes the default call to action, the closing line of every piece.',
      'Biên tập viên đổi lời kêu gọi hành động mặc định, câu kết của mọi bài viết.',
      async (page, h) => {
        const f = ctaField(page);
        await h.scrollTo(f, 'center');
        await h.click(f);
        await f.fill(NEW_CTA);
        await h.expect(page.getByText('● Unsaved changes').first()).toBeVisible({ timeout: 10_000 });
      }),
    step('Saving makes a new version. From now on the writer uses it.',
      'Lưu sẽ tạo một phiên bản mới. Từ giờ người viết dùng phiên bản này.',
      async (page, h) => {
        changed = true; // from the click on, after() restores (saving the old values again is harmless)
        const saved = page.waitForResponse((r) => new URL(r.url()).pathname === BRAND && r.request().method() === 'POST', { timeout: 30_000 });
        await h.click(page.getByRole('button', { name: 'Save as New Version' }));
        const res = await saved;
        if (res.status() >= 300) throw new Error(`the brand save answered ${res.status()}`);
        await h.expect(page.getByText('Saved — used for everything we write from now on').first()).toBeVisible({ timeout: 30_000 });
        await h.expect(page.getByText(`Active — Version ${Number(before.version) + 1}`).first()).toBeVisible({ timeout: 30_000 });
        await h.expect(ctaField(page)).toHaveValue(NEW_CTA);
      }),
    step('The test puts the agency\'s previous values back as one more version. This is the end of the scenario.',
      'Bài kiểm thử lưu lại các giá trị cũ của đại lý thành một phiên bản nữa. Kết thúc kịch bản.',
      async (page, h) => {
        await restore(page);
        await h.goto('/portal/brand');
        await h.expect(ctaField(page)).toHaveValue(before.default_cta || '', { timeout: 30_000 });
      }),
  ],
});

// Safety net: a step failed after the save went through -> the old values are saved back all the same.
sc.after = async (page) => {
  if (changed && !restored && before) await restore(page);
};

module.exports = sc;
