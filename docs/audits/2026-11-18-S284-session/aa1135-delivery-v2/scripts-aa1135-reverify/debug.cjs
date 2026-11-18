// AA-1135 re-verify: debug probes (y-axis DOM, old wording context, custom-URL error state). Read-only, no shots.
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const BASE = 'https://aa-cis.lumiguides.it.com/admin/platform/delivery';
(async () => {
  const { file: state } = await ensureState('cis-admin');
  const b = await chromium.launch();
  const ctx = await b.newContext({ storageState: state, viewport: { width: 1440, height: 900 } });
  const p = await ctx.newPage();
  await p.goto(BASE + '?app=merge-queue&repo=cis&range=90d', { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(4000);
  console.log(await p.evaluate(() => {
    const s = document.querySelector('[data-testid="queue-histogram"] svg.recharts-surface');
    if (!s) return 'no svg';
    const gs = [...s.querySelectorAll('g')].map((g) => g.getAttribute('class')).filter(Boolean);
    const texts = [...s.querySelectorAll('text')].slice(0, 12).map((t) => `${t.closest('g[class*=axis], g[class*=Axis]')?.getAttribute('class')}::${t.textContent}`);
    return JSON.stringify({ gs: [...new Set(gs)].slice(0, 30), texts }, null, 1);
  }));
  await p.goto(BASE + '?app=cis', { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(3500);
  const body = await p.evaluate(() => document.body.innerText);
  for (const m of body.matchAll(/[^\n]*12 weeks[^\n]*/gi)) console.log('12w:', m[0].slice(0, 300));
  const html = await p.evaluate(() => { const r = []; document.querySelectorAll('*').forEach((e) => { if (e.childElementCount === 0 && /12 weeks/i.test(e.textContent)) r.push(e.closest('[data-testid]')?.getAttribute('data-testid') + ' :: ' + e.tagName); }); return r; });
  console.log(html);
  await p.goto(BASE + '?app=cis&range=custom&from=2026-11-09&to=2026-11-15', { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(3500);
  const t2 = await p.evaluate(() => document.body.innerText);
  const i = t2.indexOf('Delivery\nDEV NUMBERS'); console.log('CUSTOM-URL:', p.url(), '\n', t2.slice(Math.max(0, i), i + 1200).replace(/[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z.]+/g, '<email>'));
  await b.close();
})();
