// UAT scenario REH-03-brand (pilot rehearsal step 3, part 1; root docs/ops/runbooks/pilot-rehearsal.md): the agency
// owner imports an invented brand guide (.docx built in memory, lib/rehearsal.cjs) on Brand identity, checks the fields
// it filled and saves them as the agency's brand. Writes on the synthetic agency pilot-rehearsal-01 only (pilot guard):
// the guide upload (the original file is archived), the brief reading (nothing stored) and ONE brand save; the free
// call-to-action check may run while the form fills. No model call (the brief is read by a parser). Cost $0.
// Kept on purpose (no restore): the rewrites and pieces of the next steps are written in this brand.
// Given: the rehearsal owner signed in (studio-rehearsal; the owner's studio membership from runbook step 2).
// When:  Brand identity -> drop the brand guide -> review the filled fields -> Save as New Version.
// Then:  the form holds the guide's brand name, call to action and words to avoid; the active version is one higher
//        ("brand rules +1"). Desktop 1440 x 900.
const { HOSTS, step } = require('../../lib/dryrun-page.cjs');
const { rw, studioCall, limitWrites, stubFreeChecksInPreview } = require('../../lib/uat-page.cjs');
const R = require('./_rehearsal.cjs');

const { reh } = R;
let before = null; // the brand record before the import
let counts = null;

const sc = rw({
  id: 'REH-03-brand',
  app: 'content-studio',
  identity: R.IDENTITY,
  title: 'Pilot rehearsal: import the agency brand guide',
  titleVi: 'Diễn tập pilot: nhập cẩm nang thương hiệu của đại lý',
  baseURL: HOSTS.partner,
  allowWrites: R.allow('brandUpload', 'brandParse', 'brandSave', 'ctaCheck'),
  steps: [
    step('The new agency opens Brand identity. It tells the writer who the agency is and who it writes for.',
      'Đại lý mới mở mục Nhận diện thương hiệu. Mục này cho người viết biết đại lý là ai và viết cho ai.',
      async (page, h) => {
        counts = await limitWrites(page, [
          { name: 'upload', path: R.PATHS.brandUpload, max: 1 },
          { name: 'parse', path: R.PATHS.brandParse, max: 1 },
          { name: 'save', path: R.PATHS.brandSave, max: 1 },
        ]);
        // The brand page runs the free call-to-action check on load when the saved brand has one (a re-run): in a
        // preview, where no write may leave the browser, that check is answered in the browser instead.
        await stubFreeChecksInPreview(page, [R.PATHS.ctaCheck]);
        await h.goto('/portal/brand');
        await h.expect(page.getByRole('heading', { name: 'Brand Identity' })).toBeVisible({ timeout: 30_000 });
        const r = await studioCall(page, 'GET', R.BRAND);
        if (r.status !== 200 || !r.data || typeof r.data !== 'object') throw new Error(`reading the brand answered ${r.status}`);
        before = r.data;
      }),
    step('The owner drops the agency\'s brand guide, a Word file, into the upload box. The studio reads it.',
      'Chủ đại lý thả cẩm nang thương hiệu, một file Word, vào ô tải lên. Studio đọc nội dung file.',
      async (page, h) => {
        const box = page.getByText('Drag PDF or DOCX brand guide here').first();
        await h.scrollTo(box, 'center');
        const chooser = page.waitForEvent('filechooser', { timeout: 15_000 });
        const parsed = page.waitForResponse((r) => R.isCall(r, R.PATHS.brandParse), { timeout: 60_000 });
        await h.click(box);
        await (await chooser).setFiles({ name: reh.BRAND_FILE, mimeType: reh.DOCX_TYPE, buffer: reh.brandGuideDocx() });
        const res = await parsed;
        if (res.status() !== 200) throw new Error(`reading the brand guide answered ${res.status()}`);
        await h.expect(page.getByText('Brief read — review the fields above, then save').first()).toBeVisible({ timeout: 30_000 });
      }, { writes: true }),
    step('The guide filled the form: the brand name, the call to action and the words to avoid. The owner checks them.',
      'Cẩm nang đã điền sẵn biểu mẫu: tên thương hiệu, lời kêu gọi hành động và các từ cần tránh. Chủ đại lý kiểm lại.',
      async (page, h) => {
        const name = page.getByLabel('Brand Name', { exact: true });
        await h.scrollTo(name, 'center');
        await h.expect(name).toHaveValue(reh.BRAND.name, { timeout: 15_000 });
        const cta = page.getByLabel('Default Call to Action', { exact: true });
        await h.scrollTo(cta, 'center');
        await h.expect(cta).toHaveValue(reh.BRAND.cta);
        const forbidden = page.getByPlaceholder('cheap, budget, bargain, amazing, incredible, stunning');
        await h.hover(forbidden);
        for (const w of reh.BRAND.forbidden) await h.expect(forbidden).toHaveValue(new RegExp(w));
        await h.expect(page.getByText('● Unsaved changes').first()).toBeVisible({ timeout: 10_000 });
      }),
    step('Save as New Version makes it the agency\'s brand. Everything written from now on follows it. This is the end of the scenario.',
      'Lưu thành phiên bản mới để đây là thương hiệu của đại lý. Mọi bài viết từ giờ đều theo phiên bản này. Kết thúc kịch bản.',
      async (page, h) => {
        const saved = page.waitForResponse((r) => R.isCall(r, R.PATHS.brandSave), { timeout: 30_000 });
        await h.click(page.getByRole('button', { name: 'Save as New Version' }));
        const res = await saved;
        if (res.status() >= 300) throw new Error(`the brand save answered ${res.status()}`);
        await h.expect(page.getByText('Saved — used for everything we write from now on').first()).toBeVisible({ timeout: 30_000 });
        const next = Number(before.version || 0) + 1;
        await h.expect(page.getByText(`Active — Version ${next}`).first()).toBeVisible({ timeout: 30_000 });
        const after = await studioCall(page, 'GET', R.BRAND);
        if (after.status !== 200 || Number(after.data.version) !== next) throw new Error('the saved brand is not one version higher');
        if (after.data.brand_name !== reh.BRAND.name) throw new Error('the saved brand does not carry the guide\'s brand name');
        if (counts.save !== 1 || counts.upload > 1 || counts.parse !== 1) throw new Error(`unexpected write counts ${JSON.stringify(counts)}`);
      }, { writes: true }),
  ],
});

module.exports = sc;
