// CRM review R02 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): getting started and the client import.
// Given: A (owner of the invented agency) signed in; prep.cjs wrote work/crm/import-<run>.csv (10 invented clients, two
//        with the same name and different addresses).
// When:  the owner reads the getting-started checklist, previews the CSV (dry run), imports it, reviews the possible
//        duplicate pair and looks at Connections and privacy.
// Then:  three required steps; the preview counts 10 new rows and 1 possible duplicate; the import finishes with 10
//        created; Clients > Duplicates lists the pair. On a second run of the same file every row is "Already imported"
//        (no duplicates created) and the import step is skipped in --fast; a recorded take stops (it needs a new run).
// Writes 10 invented clients (@example.invalid) once per run suffix. Never clicks "I understand and accept". Cost $0.
const path = require('path');
const { st, base, sha, open, reuse } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-02', title: 'Getting started and importing clients from a spreadsheet' });
let s;
let fresh = true;

const count = async (page, outcome) => Number((await page.getByTestId(`onb-count-${outcome}`).first().innerText()).trim());

sc.steps = [
  {
    caption: {
      en: 'Getting started walks a new agency through its setup: three required steps, then the ones it can do when ready.',
      vi: 'Trang Getting started hướng dẫn đại lý mới thiết lập: ba bước bắt buộc, rồi các bước làm khi sẵn sàng.',
    },
    run: async (page, h) => {
      s = st.load();
      if (!s.csv) throw new Error('no import file: run scenarios/crm/prep.cjs --fast first');
      await sha(page, sc, 'start');
      await open(page, h, '/onboarding', 'onb-checklist');
      await h.expect(page.getByTestId('onb-required').locator('li')).toHaveCount(3);
      await h.hover(page.getByTestId('onb-step-embed_form'));
    },
  },
  {
    caption: {
      en: 'The page also states the shared responsibility: the agency owns its client data and its own vendor accounts.',
      vi: 'Trang cũng nêu rõ trách nhiệm chung: đại lý sở hữu dữ liệu khách và các tài khoản dịch vụ của chính mình.',
    },
    run: async (page, h) => {
      await h.scrollTo(page.getByTestId('onb-ack'));
      await h.expect(page.getByTestId('onb-ack')).toBeVisible();
      await h.scrollTo(page.getByTestId('onb-optional'));
      await h.hover(page.getByTestId('onb-step-import_clients'));
    },
  },
  {
    caption: {
      en: 'The owner imports clients from a spreadsheet: ten invented clients, two of them with the same name.',
      vi: 'Chủ đại lý nhập khách từ một bảng tính: mười khách giả lập, trong đó có hai người trùng tên.',
    },
    run: async (page, h) => {
      await open(page, h, '/settings/import', 'onb-import');
      const file = path.join(__dirname, '..', '..', s.csv.file);
      const input = page.getByTestId('onb-import-file');
      await h.hover(input);
      // A file set before React hydrates is dropped silently: set it until the Preview button turns on.
      await h.expect(async () => {
        await input.setInputFiles(file);
        await h.expect(page.getByTestId('onb-import-preview').getByRole('button')).toBeEnabled({ timeout: 800 });
      }).toPass({ timeout: 20_000 });
    },
  },
  {
    caption: {
      en: 'Preview is a dry run: nothing is written yet. It counts the new clients and flags the possible duplicate.',
      vi: 'Preview là chạy thử: chưa ghi gì cả. Nó đếm số khách mới và đánh dấu cặp có thể bị trùng.',
    },
    run: async (page, h) => {
      await h.click(page.getByTestId('onb-import-preview').getByRole('button'));
      await h.expect(page.getByTestId('onb-import-counts')).toBeVisible({ timeout: 30_000 });
      const created = await count(page, 'create');
      const already = await count(page, 'already_imported');
      fresh = created > 0;
      sc.meta.import = fresh ? 'first' : 'rerun';
      if (fresh) {
        h.expect(created).toBe(10);
        await h.expect(page.getByTestId('onb-import').getByText(/share a name with another client/).first()).toBeVisible();
      } else {
        h.expect(already).toBe(10); // the same file again: nothing new (no duplicates on a re-run)
        reuse(h, 'this run\'s import', 'prep with UAT_CRM_NEW_RUN=1 writes a new file');
      }
      await h.hover(page.getByTestId('onb-import-counts'));
    },
  },
  {
    caption: {
      en: 'The owner runs the import. It works in the background and reports when it has finished.',
      vi: 'Chủ đại lý chạy lệnh nhập. Việc nhập chạy nền và báo khi đã xong.',
    },
    run: async (page, h) => {
      if (!fresh) return reuse(h, 'this run\'s import'); // fast rehearsal only
      await h.click(page.getByTestId('onb-import-apply').getByRole('button'));
      await h.expect(page.getByTestId('onb-import-progress')).toContainText(/finished/i, { timeout: 180_000 });
      h.expect(await count(page, 'create')).toBe(10);
      s = st.load();
      s.r02 = { imported_at: new Date().toISOString(), rows: 10 };
      st.save(s);
    },
  },
  {
    caption: {
      en: 'Clients with the same name are not merged blindly. They wait under Duplicates, where the agency decides.',
      vi: 'Khách trùng tên không bị gộp tự động. Họ nằm ở mục Duplicates để đại lý tự quyết định.',
    },
    run: async (page, h) => {
      await open(page, h, '/clients/duplicates', 'crm-duplicates');
      const pair = page.getByTestId('onb-duplicates').getByText(s.csv.duplicate_name);
      await h.expect(pair.first()).toBeVisible({ timeout: 20_000 });
      h.expect(await pair.count()).toBeGreaterThanOrEqual(2);
      await h.hover(pair.first());
    },
  },
  {
    caption: {
      en: 'Connections and privacy shows which outside accounts are linked, such as the mailbox and card payments.',
      vi: 'Trang Connections and privacy cho thấy tài khoản bên ngoài nào đã kết nối, như hộp thư và thanh toán thẻ.',
    },
    run: async (page, h) => {
      await open(page, h, '/settings/connections', 'onb-connections');
      await h.expect(page.getByTestId('onb-conn-mailbox')).toBeVisible();
      await h.hover(page.getByTestId('onb-conn-mailbox'));
      await h.hover(page.getByTestId('onb-conn-card_payments'));
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
