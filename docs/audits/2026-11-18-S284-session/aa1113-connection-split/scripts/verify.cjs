// AA-1113 live check (read-only): AI gateway > Budgets "Connection budget split" + Platform > Settings CRM share.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const OUT = '/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-18-S284-session/aa1113-connection-split';
const PRIV = '/home/nghiep/projects/AA-Ecosys/.tmp-session/S284/private-shots';
const HOST = 'https://aa-cis.lumiguides.it.com';
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/;
const log = { console: [], failed: [], shots: [], api: {} };

async function shot(p, name, full) {
  let f = path.join(OUT, name + '.png');
  await p.screenshot({ path: f, fullPage: full });
  if (fs.statSync(f).size > 400 * 1024) {
    fs.unlinkSync(f); f = path.join(OUT, name + '.jpg');
    await p.screenshot({ path: f, fullPage: full, type: 'jpeg', quality: 70 });
  }
  const txt = await p.evaluate(() => document.body.innerText);
  const m = txt.match(EMAIL);
  if (m) { const dst = path.join(PRIV, path.basename(f)); fs.renameSync(f, dst); f = dst; }
  log.shots.push({ file: f, kb: Math.round(fs.statSync(f).size / 1024), email: !!m });
}

async function ctxFor(b, state, w, h, scheme, mobile) {
  const ctx = await b.newContext({ storageState: state, viewport: { width: w, height: h }, colorScheme: scheme,
    isMobile: mobile, hasTouch: mobile });
  const p = await ctx.newPage();
  await p.addInitScript((s) => { try { localStorage.setItem('theme', s); } catch (e) {} }, scheme);
  p.on('console', (m) => { if (m.type() === 'error') log.console.push(`${p.url()} :: ${m.text().slice(0, 300)}`); });
  p.on('response', async (r) => {
    if (r.status() >= 400) log.failed.push(`${r.status()} ${r.request().method()} ${r.url()}`);
    const u = r.url();
    if (u.includes('/connection-split') || u.includes('/settings/registry')) {
      try { log.api[`${r.request().method()} ${u}`] = await r.json(); } catch (e) {}
    }
  });
  p.on('requestfailed', (r) => log.failed.push(`FAILED ${r.method()} ${r.url()} ${r.failure()?.errorText}`));
  return { ctx, p };
}

(async () => {
  let { file: state } = await ensureState('cis-admin');
  const b = await chromium.launch();
  const results = {};
  // Check 1: budgets tab
  for (const [name, w, h, scheme, mobile] of [
    ['budgets-split-desktop-light', 1440, 900, 'light', false],
    ['budgets-split-desktop-dark', 1440, 900, 'dark', false],
    ['budgets-split-mobile-light', 390, 844, 'light', true]]) {
    let { ctx, p } = await ctxFor(b, state, w, h, scheme, mobile);
    await p.goto(`${HOST}/admin/ai-gateway?tab=budgets`, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
    if (p.url().includes('/login')) {
      await ctx.close(); ({ file: state } = await ensureState('cis-admin'));
      ({ ctx, p } = await ctxFor(b, state, w, h, scheme, mobile));
      await p.goto(`${HOST}/admin/ai-gateway?tab=budgets`, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
    }
    const sec = p.getByTestId('ai-gateway-budgets-connection-split');
    await sec.waitFor({ timeout: 30000 }).catch(() => {});
    await p.waitForTimeout(4000);
    const info = await sec.evaluate((el) => ({
      notices: [...el.querySelectorAll('[role=status]')].map((n) => n.innerText),
      header: [...el.querySelectorAll('thead th')].map((t) => t.innerText.trim()),
      rows: [...el.querySelectorAll('tbody tr')].map((tr) => [...tr.querySelectorAll('td')].map((td) => td.innerText.replace(/\s+/g, ' ').trim())),
      text: el.innerText.slice(0, 3000),
    })).catch((e) => ({ error: String(e) }));
    results[name] = { url: p.url(), ...info };
    await sec.scrollIntoViewIfNeeded().catch(() => {});
    await p.waitForTimeout(500);
    if (mobile) await shot(p, name, false);
    else { // shot the section itself plus a little context
      const bb = await sec.boundingBox().catch(() => null);
      if (bb) {
        let f = path.join(OUT, name + '.png');
        await sec.screenshot({ path: f });
        if (fs.statSync(f).size > 400 * 1024) { fs.unlinkSync(f); f = path.join(OUT, name + '.jpg'); await sec.screenshot({ path: f, type: 'jpeg', quality: 70 }); }
        const txt = await sec.innerText(); const m = txt.match(EMAIL);
        if (m) { const dst = path.join(PRIV, path.basename(f)); fs.renameSync(f, dst); f = dst; }
        log.shots.push({ file: f, kb: Math.round(fs.statSync(f).size / 1024), email: !!m });
      } else await shot(p, name, true);
    }
    await ctx.close();
  }
  // Check 2: settings CRM tab, two loads (initial + reload)
  {
    const { ctx, p } = await ctxFor(b, state, 1440, 900, 'light', false);
    const url = `${HOST}/admin/platform/settings?app=crm&area=ai&key=crm.ai.connection_monthly_cap_usd`;
    for (const pass of ['first', 'reload']) {
      if (pass === 'first') await p.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
      else await p.reload({ waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
      await p.waitForTimeout(5000);
      const search = await p.getByTestId('settings-search').inputValue().catch(() => null);
      const rows = await p.evaluate(() => [...document.querySelectorAll('tbody tr')]
        .map((tr) => [...tr.querySelectorAll('td')].map((td) => td.innerText.replace(/\s+/g, ' ').trim()))
        .filter((r) => r.join(' ').includes('connection_monthly_cap_usd') || r.join(' ').toLowerCase().includes('connection')));
      const headers = await p.evaluate(() => [...document.querySelectorAll('thead th')].map((t) => t.innerText.trim()));
      results['settings-' + pass] = { url: p.url(), search, headers, rows,
        count: await p.getByTestId('settings-search-count').innerText().catch(() => null) };
    }
    await shot(p, 'settings-crm-connection-cap', false);
    await ctx.close();
  }
  await b.close();
  fs.writeFileSync(path.join(OUT, 'scripts', 'result.json'), JSON.stringify({ results, log }, null, 2));
  console.log(JSON.stringify({ results, shots: log.shots, console: log.console, failed: log.failed }, null, 2));
})();
