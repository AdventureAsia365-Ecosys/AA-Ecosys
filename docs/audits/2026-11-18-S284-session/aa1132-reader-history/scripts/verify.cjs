// AA-1132 reader part: live read-only check of /admin/docs page history, "Last changed", "What changed in docs".
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const OUT = '/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-18-S284-session/aa1132-reader-history';
const PRIV = '/home/nghiep/projects/AA-Ecosys/.tmp-session/S284/private-shots';
const BASE = 'https://aa-cis.lumiguides.it.com/admin/docs';
const DOC = 'docs/engineering-handbook.md';
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/;
const results = {};

async function shot(p, name, opts = {}) {
  let f = path.join(OUT, name + '.png');
  await p.screenshot({ path: f, ...opts });
  if (fs.statSync(f).size > 400 * 1024) {
    fs.unlinkSync(f);
    f = path.join(OUT, name + '.jpg');
    await p.screenshot({ path: f, type: 'jpeg', quality: 70, ...opts });
  }
  const txt = await p.evaluate(() => document.body.innerText);
  if (EMAIL.test(txt)) {
    const dest = path.join(PRIV, path.basename(f));
    fs.renameSync(f, dest);
    return { file: dest, email: txt.match(EMAIL)[0].replace(/^[^@]+/, '***'), size: fs.statSync(dest).size };
  }
  return { file: path.basename(f), size: fs.statSync(f).size };
}

(async () => {
  let { file: state } = await ensureState('cis-admin');
  const b = await chromium.launch();
  const runs = [
    { name: 'desktop-light', w: 1440, h: 900, scheme: 'light', mobile: false },
    { name: 'desktop-dark', w: 1440, h: 900, scheme: 'dark', mobile: false },
    { name: 'phone-light', w: 390, h: 844, scheme: 'light', mobile: true },
  ];
  for (const r of runs) {
    for (let attempt = 0; attempt < 2; attempt++) {
      const ctx = await b.newContext({ storageState: state, viewport: { width: r.w, height: r.h }, colorScheme: r.scheme,
        isMobile: r.mobile, hasTouch: r.mobile });
      const p = await ctx.newPage();
      const consoleErr = []; const failed = [];
      p.on('console', (m) => { if (m.type() === 'error') consoleErr.push(m.text().slice(0, 300)); });
      p.on('pageerror', (e) => consoleErr.push('pageerror: ' + String(e).slice(0, 300)));
      p.on('response', (res) => { if (res.status() >= 400) failed.push(res.status() + ' ' + res.url().slice(0, 200)); });
      p.on('requestfailed', (req) => { const e = req.failure()?.errorText || ''; if (!/ERR_ABORTED/.test(e)) failed.push('FAILED ' + e + ' ' + req.url().slice(0, 200)); });
      await p.addInitScript((s) => { try { localStorage.setItem('theme', s); } catch (e) {} }, r.scheme);
      await p.goto(`${BASE}?path=${encodeURIComponent(DOC)}`, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
      await p.waitForTimeout(4000);
      if (p.url().includes('/login') || p.url().includes('staff-auth')) {
        await ctx.close();
        if (attempt === 0) { ({ file: state } = await ensureState('cis-admin')); continue; }
        results[r.name] = { error: 'login page' }; break;
      }
      const res = { url: p.url() };
      const body = await p.evaluate(() => document.body.innerText);
      res.lastChanged = (body.match(/Last changed [^\n·|]+/) || [null])[0];
      res.needsReviewBadges = await p.locator('[data-testid="docs-needs-review"]').count();
      res.needsReviewText = body.includes('Needs review');
      const hist = p.locator('[data-testid="docs-history"]');
      res.historyCount = await hist.count();
      if (res.historyCount) {
        res.historySummary = (await hist.locator('summary').innerText()).trim();
        await hist.locator('summary').click();
        await p.waitForTimeout(500);
        res.historyOpen = await hist.evaluate((d) => d.open);
        const items = hist.locator('[data-testid="docs-history-item"]');
        res.items = await items.evaluateAll((els) => els.map((e) => e.innerText.replace(/\n/g, ' | ')));
        res.commitHrefs = await p.locator('[data-testid="docs-history-commit"]').evaluateAll((els) => els.map((e) => e.getAttribute('href')));
        res.prHrefs = await p.locator('[data-testid="docs-history-pr"]').evaluateAll((els) => els.map((e) => e.getAttribute('href')));
        res.linkTargets = await p.locator('[data-testid="docs-history-commit"],[data-testid="docs-history-pr"]').evaluateAll((els) => els.map((e) => e.getAttribute('target') + '/' + e.getAttribute('rel')));
        await hist.scrollIntoViewIfNeeded();
      }
      res.changesLinkCount = await p.locator('[data-testid="docs-changes-link"]').count();
      if (res.changesLinkCount) res.changesHref = await p.locator('[data-testid="docs-changes-link"]').first().getAttribute('href');
      // Position of the changes link relative to the first topic group (should be above).
      res.shot = await shot(p, `${r.name}-history`, r.mobile ? { fullPage: false } : { fullPage: false });
      if (r.mobile) {
        await p.evaluate(() => window.scrollTo(0, 0));
        await p.waitForTimeout(300);
        res.shotTop = await shot(p, `${r.name}-top`, { fullPage: false });
      }
      // Open one commit/PR link in a new tab briefly, then close it.
      if (r.name === 'desktop-light' && res.commitHrefs && (res.commitHrefs.length || res.prHrefs.length)) {
        const href = res.prHrefs[0] || res.commitHrefs[0];
        const t = await ctx.newPage();
        const rr = await t.goto(href, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch((e) => ({ status: () => 'ERR ' + e.message.slice(0, 80) }));
        res.linkOpen = { href, status: rr.status(), title: (await t.title().catch(() => '')).slice(0, 120) };
        await t.close();
      }
      // The changes page (desktop light only).
      if (r.name === 'desktop-light' && res.changesLinkCount) {
        await p.evaluate(() => window.scrollTo(0, 0));
        await p.locator('[data-testid="docs-changes-link"]').first().click();
        await p.waitForTimeout(4000);
        await p.waitForLoadState('networkidle').catch(() => {});
        const cb = await p.evaluate(() => document.body.innerText);
        res.changes = { url: p.url(), hasTitle: /What changed in docs/i.test(cb),
          h1: await p.locator('main h1, article h1, h1').first().innerText().catch(() => null),
          tables: await p.locator('main table, article table').count(),
          snippet: cb.slice(cb.indexOf('What changed'), cb.indexOf('What changed') + 600).replace(/\n+/g, ' | ') };
        res.changes.shot = await shot(p, 'changes-page-desktop-light', { fullPage: false });
      }
      res.consoleErrors = consoleErr; res.failedRequests = failed;
      results[r.name] = res;
      await ctx.close();
      break;
    }
  }
  await b.close();
  fs.writeFileSync(path.join(OUT, 'scripts', 'results.json'), JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));
})();
