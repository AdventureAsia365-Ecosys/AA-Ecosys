// CRM review R16 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): a client's data request, export and
// erasure.
// Given: A (owner) signed in; Dev runs with deletion switched off (LIFECYCLE_DRY_RUN=true, the environment's safety
//        switch, never changed for the review).
// When:  the owner adds a new invented client without a trip, logs the client's request for their data in a file,
//        exports it (built in the background, then ready with a checksum), logs an erasure request, checks what the
//        erasure would remove, and confirms.
// Then:  the export is ready; the erasure preview lists counts; the confirm answers "deletion is switched off" (409
//        deletion_dry_run): nothing is deleted on Dev. Requests forwarded by Adventure Asia: "Not ready yet" card.
// Writes: one invented client (@example.invalid), two data requests, one client export (ids kept in state.json:
// cleanup.cjs closes the requests as withdrawn and moves the client to the trash). No download, no LLM call. Cost $0.
const slide = require('../../lib/slide.cjs');
const { st, base, sha, open, bffOk, type, choose } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-16', title: 'A client asks for their data: export, and erasure checked safely' });
let s;
let who;
let clientId;
const SCOPE_LABEL = 'One client'; // data.exp.scope.traveler

const requests = (page) => page.getByTestId('data-requests');

async function logRequest(page, h, kind) {
  const panel = requests(page);
  const form = panel.locator('form').last();
  await h.scrollTo(form);
  await choose(h, form.getByLabel('Request'), kind);
  await choose(h, form.getByLabel('Received by'), 'email');
  await form.getByLabel('Received on').fill(st.today().replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'));
  await type(page, h, form.getByLabel('Client id (optional)'), clientId);
  const made = page.waitForResponse((r) => /\/data\/requests$/.test(new URL(r.url()).pathname) && r.request().method() === 'POST', { timeout: 30_000 });
  await h.click(form.getByRole('button', { name: 'Log request' }));
  const res = await made;
  h.expect(res.status()).toBeLessThan(300);
  const body = await res.json();
  s = st.load();
  st.remember(s, 'data_requests', body.data_request_id);
  st.save(s);
  const row = panel.getByTestId('data-request').filter({ hasText: clientId.slice(0, 8) }).filter({ hasText: kind === 'erasure' ? 'Erase their data' : 'Their data in a file' });
  await h.expect(row.first()).toBeVisible({ timeout: 15_000 });
  return row.first();
}

sc.steps = [
  {
    caption: {
      en: 'A new client, added by name and e-mail. No trip yet.',
      vi: 'Một khách mới, chỉ thêm tên và e-mail. Chưa có chuyến nào.',
    },
    run: async (page, h) => {
      s = st.load();
      const n = ((s.r16 && s.r16.n) || 0) + 1;
      who = { name: `Noah Weber ${st.runTag(s)}${n > 1 ? `-${n}` : ''}`, email: `noah.weber.r16.${s.run}.${n}@example.invalid` };
      s.r16 = { n };
      st.save(s);
      await sha(page, sc, 'start');
      await open(page, h, '/clients');
      await h.click(page.getByRole('button', { name: '+ New client' }));
      const form = page.getByTestId('new-client');
      await type(page, h, form.getByLabel('Name'), who.name);
      await type(page, h, form.getByLabel('E-mail (optional)'), who.email);
      await h.click(form.getByRole('button', { name: 'Add client' }));
      await page.waitForURL(/\/clients\/[0-9a-f-]{36}$/, { timeout: 20_000 });
      clientId = page.url().split('/').pop();
      await h.expect(page.getByTestId('client-name')).toHaveText(who.name);
      s = st.load();
      st.remember(s, 'clients', clientId);
      s.r16.traveler_id = clientId;
      st.save(s);
    },
  },
  {
    caption: {
      en: 'The client asks by e-mail for all their data in a file. In Settings, Data, the owner logs the request with its reply-by date.',
      vi: 'Khách gửi e-mail xin toàn bộ dữ liệu của mình trong một file. Trong Settings, mục Data, chủ đại lý ghi nhận yêu cầu kèm hạn trả lời.',
    },
    run: async (page, h) => {
      await open(page, h, '/settings/data', 'data-requests');
      const row = await logRequest(page, h, 'portability');
      await h.hover(row);
    },
  },
  {
    caption: {
      en: 'The export is built in the background. When it is ready, it carries a checksum and downloads through a single-use link.',
      vi: 'File xuất được tạo chạy nền. Khi xong, file có mã kiểm tra và được tải qua một đường dẫn dùng một lần.',
    },
    run: async (page, h) => {
      const row = requests(page).getByTestId('data-request').filter({ hasText: clientId.slice(0, 8) }).filter({ hasText: 'Their data in a file' }).first();
      const made = page.waitForResponse((r) => /\/data\/exports$/.test(new URL(r.url()).pathname) && r.request().method() === 'POST', { timeout: 30_000 });
      await h.click(row.getByRole('button', { name: 'Export client data' }));
      const res = await made;
      h.expect(res.status()).toBeLessThan(300);
      const exportId = (await res.json()).export_id;
      await h.expect.poll(async () => {
        const all = await bffOk(page, 'GET', 'data/exports');
        return ((all.exports || []).find((e) => e.export_id === exportId) || {}).status;
      }, { timeout: 120_000, intervals: [3_000, 5_000] }).toBe('ready');
      await open(page, h, '/settings/data', 'data-exports');
      const ready = page.getByTestId('data-export').filter({ hasText: 'Ready' }).filter({ hasText: SCOPE_LABEL }).first();
      await h.scrollTo(ready);
      await h.expect(ready).toContainText('SHA-256');
      await h.hover(ready);
    },
  },
  {
    caption: {
      en: 'Later the client asks to be erased. The owner logs that request too, then checks what an erasure would remove.',
      vi: 'Sau đó khách yêu cầu xoá dữ liệu. Chủ đại lý cũng ghi nhận yêu cầu này, rồi kiểm tra việc xoá sẽ gỡ những gì.',
    },
    run: async (page, h) => {
      const row = await logRequest(page, h, 'erasure');
      await h.click(row.getByRole('button', { name: 'Check erasure' }));
      const preview = row.getByTestId('data-erasure-preview');
      await h.expect(preview).toBeVisible({ timeout: 20_000 });
      await h.hover(preview);
    },
  },
  {
    caption: {
      en: 'The owner confirms. On this test system deletion is switched off on purpose, so the CRM only reports what it would remove.',
      vi: 'Chủ đại lý xác nhận. Trên hệ thống thử nghiệm này việc xoá được tắt có chủ đích, nên CRM chỉ báo những gì sẽ bị xoá.',
    },
    run: async (page, h) => {
      const row = requests(page).getByTestId('data-request').filter({ hasText: clientId.slice(0, 8) }).filter({ hasText: 'Erase their data' }).first();
      const answer = page.waitForResponse((r) => /\/erasure$/.test(new URL(r.url()).pathname) && r.request().method() === 'POST', { timeout: 30_000 });
      await h.click(row.getByRole('button', { name: 'Erase this client now' }));
      const res = await answer;
      h.expect(res.status(), 'deletion stays off on Dev').toBe(409);
      h.expect((await res.json()).detail).toBe('deletion_dry_run');
      const alert = page.getByRole('alert').filter({ hasText: 'Deletion is switched off' });
      await h.expect(alert.first()).toBeVisible({ timeout: 15_000 });
      await h.hover(alert.first());
      await h.expect(page.getByTestId('data-erasure-done')).toHaveCount(0);
    },
  },
  {
    caption: {
      en: 'Not ready yet: requests that reach Adventure Asia and are forwarded to the agency automatically.',
      vi: 'Chưa có: yêu cầu gửi tới Adventure Asia được tự động chuyển sang đại lý.',
    },
    run: async (page, h) => {
      await slide.notReady(page, h, {
        screen: 'Requests forwarded by Adventure Asia',
        missing: ['A client\'s request that reaches Adventure Asia arriving in the agency\'s list by itself (today the agency logs it)'],
      });
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
