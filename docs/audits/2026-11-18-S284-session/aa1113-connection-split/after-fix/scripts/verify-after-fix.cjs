// AA-1113 after-fix live check (read-only): Platform > Settings CRM connection cap (value + History) and
// AI gateway > Budgets "Connection budget split" (desktop light + dark), plus 5 reads of the connection-split API.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const OUT = '/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-18-S284-session/aa1113-connection-split/after-fix';
const PRIV = '/home/nghiep/projects/AA-Ecosys/.tmp-session/S284/private-shots';
const HOST = 'https://aa-cis.lumiguides.it.com';
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/;
const log = { console: [], failed: [], shots: [], api: {} };

function finalize(f, txt) {
  if (fs.statSync(f).size > 300 * 1024) return 'big';
  const m = (txt || '').match(EMAIL);
  if (m) { const dst = path.join(PRIV, path.basename(f)); fs.renameSync(f, dst); f = dst; }
  log.shots.push({ file: f, kb: Math.round(fs.statSync(f).size / 1024), email: !!m });
  return f;
}
async function shot(target, p, name, opts = {}) {
  let f = path.join(OUT, name + '.png');
  await target.screenshot({ path: f, ...opts });
  const txt = await p.evaluate(() => document.body.innerText);
  if (finalize(f, txt) === 'big') {
    fs.unlinkSync(f); f = path.join(OUT, name + '.jpg');
    await target.screenshot({ path: f, ...opts, type: 'jpeg', quality: 70 });
    finalize(f, txt);
  }
}
async function ctxFor(b, state, w, h, scheme) {
  const ctx = await b.newContext({ storageState: state, viewport: { width: w, height: h }, colorScheme: scheme });
  const p = await ctx.newPage();
  await p.addInitScript((s) => { try { localStorage.setItem('theme', s); } catch (e) {} }, scheme);
  p.on('console', (m) => { if (m.type() === 'error') log.console.push(`${p.url()} :: ${m.text().slice(0, 300)}`); });
  p.on('response', async (r) => {
    if (r.status() >= 400) log.failed.push(`${r.status()} ${r.request().method()} ${r.url()}`);
    const u = r.url();
    if (u.includes('/connection-split') || u.includes('connection_monthly_cap_usd')) {
      try { log.api[`${r.request().method()} ${u}`] = await r.json(); } catch (e) {}
    }
  });
  p.on('requestfailed', (r) => log.failed.push(`FAILED ${r.method()} ${r.url()} ${r.failure()?.errorText}`));
  return { ctx, p };
}
async function open(b, stateRef, w, h, scheme, url) {
  let { ctx, p } = await ctxFor(b, stateRef.file, w, h, scheme);
  await p.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  if (p.url().includes('/login') || p.url().includes('auth')) {
    await ctx.close(); stateRef.file = (await ensureState('cis-admin')).file;
    ({ ctx, p } = await ctxFor(b, stateRef.file, w, h, scheme));
    await p.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  }
  return { ctx, p };
}

(async () => {
  const stateRef = { file: (await ensureState('cis-admin')).file };
  const b = await chromium.launch();
  const results = {};
  // Check 1: settings CRM tab + History
  {
    const { ctx, p } = await open(b, stateRef, 1440, 900, 'light',
      `${HOST}/admin/platform/settings?app=crm&area=ai&key=crm.ai.connection_monthly_cap_usd`);
    await p.waitForTimeout(5000);
    results.settings = { url: p.url(),
      headers: await p.evaluate(() => [...document.querySelectorAll('thead th')].map((t) => t.innerText.trim())),
      rows: await p.evaluate(() => [...document.querySelectorAll('tbody tr')]
        .map((tr) => [...tr.querySelectorAll('td')].map((td) => td.innerText.replace(/\s+/g, ' ').trim()))
        .filter((r) => r.join(' ').includes('connection_monthly_cap_usd') || /per model connection/i.test(r.join(' ')))) };
    await shot(p, p, '01-settings-crm-connection-cap-light');
    await p.getByRole('button', { name: 'History' }).first().click().catch((e) => { results.historyClickErr = String(e); });
    await p.waitForTimeout(4000);
    results.historyDrawer = await p.locator('[role=dialog]').first().innerText().catch(() => null);
    await shot(p, p, '02-settings-crm-connection-cap-history-light');
    // five reads of the split API on the same session
    const samples = [];
    for (let i = 0; i < 5; i++) {
      const r = await p.request.get(`${HOST}/api/admin/ai-gateway/connection-split`);
      let j = null; try { j = await r.json(); } catch (e) {}
      const a2 = j && j.rows ? j.rows.find((x) => x.connection_key === 'acc2') : null;
      samples.push({ i: i + 1, status: r.status(), crm_error: j && j.crm_error, errors: j && j.errors,
        acc2: a2 || null });
      if (i === 0) log.api['sample1'] = j;
      await p.waitForTimeout(1500);
    }
    results.samples = samples;
    await ctx.close();
  }
  // Check 2: budgets split desktop light + dark
  for (const scheme of ['light', 'dark']) {
    const { ctx, p } = await open(b, stateRef, 1440, 900, scheme, `${HOST}/admin/ai-gateway?tab=budgets`);
    const sec = p.getByTestId('ai-gateway-budgets-connection-split');
    await sec.waitFor({ timeout: 30000 }).catch(() => {});
    await p.waitForTimeout(4000);
    results['budgets-' + scheme] = await sec.evaluate((el) => ({
      notices: [...el.querySelectorAll('[role=status],[role=alert]')].map((n) => n.innerText),
      header: [...el.querySelectorAll('thead th')].map((t) => t.innerText.trim()),
      rows: [...el.querySelectorAll('tbody tr')].map((tr) => [...tr.querySelectorAll('td')].map((td) => td.innerText.replace(/\s+/g, ' ').trim())),
      text: el.innerText.slice(0, 3000),
    })).catch((e) => ({ error: String(e) }));
    await sec.scrollIntoViewIfNeeded().catch(() => {});
    await p.waitForTimeout(500);
    if (await sec.boundingBox().catch(() => null)) await shot(sec, p, `0${scheme === 'light' ? 3 : 4}-budgets-split-desktop-${scheme}`);
    else await shot(p, p, `0${scheme === 'light' ? 3 : 4}-budgets-split-desktop-${scheme}`, { fullPage: true });
    await ctx.close();
  }
  await b.close();
  fs.writeFileSync(path.join(OUT, 'scripts', 'result.json'), JSON.stringify({ results, log }, null, 2));
  console.log(JSON.stringify({ results, shots: log.shots, console: log.console, failed: log.failed }, null, 2));
})();
