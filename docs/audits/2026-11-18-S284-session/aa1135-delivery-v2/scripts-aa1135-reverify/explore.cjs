// AA-1135 re-verify: read-only structure probe of Platform > Delivery (no screenshots).
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
(async () => {
  const { file: state } = await ensureState('cis-admin');
  const b = await chromium.launch();
  const ctx = await b.newContext({ storageState: state, viewport: { width: 1440, height: 900 }, colorScheme: 'light' });
  const p = await ctx.newPage();
  await p.addInitScript((s) => { try { localStorage.setItem('theme', s); } catch (e) {} }, 'light');
  await p.goto('https://aa-cis.lumiguides.it.com/admin/platform/delivery', { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(4000);
  console.log('URL', p.url());
  const info = await p.evaluate(() => ({
    testids: [...new Set([...document.querySelectorAll('[data-testid]')].map((e) => e.getAttribute('data-testid')))],
    tabs: [...document.querySelectorAll('[role=tab]')].map((e) => e.textContent.trim() + ' sel=' + e.getAttribute('aria-selected')),
    radios: [...document.querySelectorAll('[role=radio]')].map((e) => e.textContent.trim()),
    h: [...document.querySelectorAll('h1,h2,h3')].map((e) => e.textContent.trim()).slice(0, 40),
    links: [...document.querySelectorAll('a[href*="delivery"]')].map((a) => a.textContent.trim() + ' -> ' + a.getAttribute('href')).slice(0, 30),
  }));
  console.log(JSON.stringify(info, null, 1));
  const txt = await p.evaluate(() => document.body.innerText);
  console.log(txt.slice(0, 3000));
  await b.close();
})();
