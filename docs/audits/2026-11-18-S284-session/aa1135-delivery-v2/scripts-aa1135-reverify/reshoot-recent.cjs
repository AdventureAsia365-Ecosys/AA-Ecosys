// AA-1135 re-verify: re-take the two "Recent entries" shots (the first try hit a 404 chunk during an admin redeploy).
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const OUT = '/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-18-S284-session/aa1135-delivery-v2/reverify';
const BASE = 'https://aa-cis.lumiguides.it.com/admin/platform/delivery';
(async () => {
  const { file: state } = await ensureState('cis-admin');
  const b = await chromium.launch();
  for (const [name, q, scheme] of [['mq-cis-90d-recent-1440-light', 'repo=cis&range=90d', 'light'], ['mq-booking-7d-recent-1440-dark', 'repo=booking&range=7d', 'dark']]) {
    const ctx = await b.newContext({ storageState: state, viewport: { width: 1440, height: 900 }, colorScheme: scheme });
    const p = await ctx.newPage();
    await p.addInitScript((s) => { try { localStorage.setItem('theme', s); } catch (e) {} }, scheme);
    const errs = [];
    p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
    p.on('response', (r) => { if (r.status() >= 400 && /lumiguides/.test(r.url())) errs.push(r.status() + ' ' + r.url().slice(0, 150)); });
    await p.goto(`${BASE}?app=merge-queue&${q}`, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
    await p.waitForTimeout(3500);
    const ok = await p.getByTestId('queue-recent').count();
    await p.getByTestId('queue-recent').first().evaluate((el) => el.scrollIntoView({ block: 'start' })).catch(() => {});
    await p.waitForTimeout(800);
    const info = await p.evaluate(() => {
      const s = document.querySelector('[data-testid="queue-recent"]');
      return s ? { rows: s.querySelectorAll('[data-testid="kit-datatable-row"]').length, desc: s.innerText.split('\n').slice(0, 2).join(' | '),
        email: /[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z.]+/.test(document.body.innerText) } : null;
    });
    const f = path.join(OUT, name + '.png');
    await p.screenshot({ path: f });
    console.log(name, 'section', ok, JSON.stringify(info), Math.round(fs.statSync(f).size / 1024) + 'KB', 'errors', JSON.stringify(errs));
    await ctx.close();
  }
  await b.close();
})();
