// AA-1135 re-verify: probe the custom range picker and the merge-queue tab (read-only, no screenshots).
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const base = 'https://aa-cis.lumiguides.it.com/admin/platform/delivery';
(async () => {
  const { file: state } = await ensureState('cis-admin');
  const b = await chromium.launch();
  const ctx = await b.newContext({ storageState: state, viewport: { width: 1440, height: 900 }, colorScheme: 'light' });
  const p = await ctx.newPage();
  await p.goto(base, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(3000);
  await p.getByTestId('delivery-range-picker').getByRole('radio', { name: 'Custom' }).click();
  await p.waitForTimeout(1500);
  console.log('URL after custom', p.url());
  const r = await p.evaluate(() => {
    const el = document.querySelector('[data-testid="delivery-range"]');
    return { html: el.outerHTML.slice(0, 4000), text: el.innerText };
  });
  console.log(r.text); console.log(r.html.replace(/class="[^"]*"/g, ''));
  await p.goto(base + '?app=merge-queue', { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(4000);
  const q = await p.evaluate(() => ({
    testids: [...new Set([...document.querySelectorAll('[data-testid]')].map((e) => e.getAttribute('data-testid')))].filter((t) => !t.startsWith('nav-') && !t.startsWith('sidebar')),
    recent: [...document.querySelectorAll('[data-testid="queue-recent"]')].map((s) => s.innerText.slice(0, 1500)),
  }));
  console.log(JSON.stringify(q, null, 1));
  await b.close();
})();
