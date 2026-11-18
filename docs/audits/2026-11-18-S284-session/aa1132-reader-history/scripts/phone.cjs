// AA-1132: phone 390 light, header (Last changed) at top of the doc and the docs list view (What changed link).
const fs = require('fs'); const path = require('path');
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const OUT = '/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-18-S284-session/aa1132-reader-history';
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/;
(async () => {
  const { file: state } = await ensureState('cis-admin');
  const b = await chromium.launch();
  const ctx = await b.newContext({ storageState: state, viewport: { width: 390, height: 844 }, colorScheme: 'light', isMobile: true, hasTouch: true });
  const p = await ctx.newPage();
  const errs = []; const failed = [];
  p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 300)); });
  p.on('pageerror', (e) => errs.push('pageerror: ' + String(e).slice(0, 300)));
  p.on('response', (r) => { if (r.status() >= 400) failed.push(r.status() + ' ' + r.url().slice(0, 200)); });
  await p.addInitScript(() => { try { localStorage.setItem('theme', 'light'); } catch (e) {} });
  const out = {};
  await p.goto('https://aa-cis.lumiguides.it.com/admin/docs?path=docs%2Fengineering-handbook.md', { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(4000);
  await p.locator('h1:has-text("engineering handbook")').first().scrollIntoViewIfNeeded().catch(() => {});
  await p.waitForTimeout(400);
  out.overflowX = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  const f1 = path.join(OUT, 'phone-light-header.png'); await p.screenshot({ path: f1 });
  out.header = { file: path.basename(f1), size: fs.statSync(f1).size, email: EMAIL.test(await p.evaluate(() => document.body.innerText)) };
  await p.goto('https://aa-cis.lumiguides.it.com/admin/docs', { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(4000);
  out.listChangesLink = await p.locator('[data-testid="docs-changes-link"]').count();
  if (out.listChangesLink) { await p.locator('[data-testid="docs-changes-link"]').first().scrollIntoViewIfNeeded(); }
  const f2 = path.join(OUT, 'phone-light-list.png'); await p.screenshot({ path: f2 });
  out.list = { file: path.basename(f2), size: fs.statSync(f2).size, email: EMAIL.test(await p.evaluate(() => document.body.innerText)) };
  if (out.listChangesLink) {
    await p.locator('[data-testid="docs-changes-link"]').first().click(); await p.waitForTimeout(4000);
    out.changesUrl = p.url();
    out.changesRendered = await p.locator('h1:has-text("What changed in docs")').count();
    out.weekHeadings = await p.locator('h2:has-text("Week of")').count();
  }
  out.consoleErrors = errs; out.failed = failed;
  console.log(JSON.stringify(out, null, 2));
  await b.close();
})();
