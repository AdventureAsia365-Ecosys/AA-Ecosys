// AA-1135 custom range: read-only probe of the range picker after Custom is chosen (no screenshots).
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const BASE = 'https://aa-cis.lumiguides.it.com/admin/platform/delivery';
(async () => {
  const { file: state } = await ensureState('cis-admin');
  const b = await chromium.launch();
  const ctx = await b.newContext({ storageState: state, viewport: { width: 1440, height: 900 }, colorScheme: 'light' });
  const p = await ctx.newPage();
  p.on('response', (r) => { if (/api-cis|delivery/.test(r.url()) && r.request().resourceType() !== 'script') console.log('RESP', r.status(), r.url().slice(0, 200)); });
  await p.goto(BASE, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(3000);
  console.log('URL', p.url());
  await p.getByTestId('delivery-range-picker').getByRole('radio', { name: 'Custom' }).click();
  await p.waitForTimeout(1500);
  const r = await p.evaluate(() => {
    const el = document.querySelector('[data-testid="delivery-range"]');
    return { text: el.innerText, html: el.outerHTML.replace(/class="[^"]*"/g, '').slice(0, 5000) };
  });
  console.log(r.text); console.log(r.html);
  await b.close();
})();
