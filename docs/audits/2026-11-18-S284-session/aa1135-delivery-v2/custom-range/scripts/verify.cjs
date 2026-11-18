// AA-1135 custom range verify (read-only): pick 9-15 Nov 2026 in the range picker, Apply (view only),
// check URL + wording, merge-queue Recent entries bounded and inside the range, time the custom request.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const OUT = '/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-18-S284-session/aa1135-delivery-v2/custom-range';
const PRIV = '/home/nghiep/projects/AA-Ecosys/.tmp-session/S284/private-shots';
const BASE = 'https://aa-cis.lumiguides.it.com/admin/platform/delivery';
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z.]{2,}/;
const result = { shots: [], checks: {}, console: [], network: [], apiTimings: [] };

async function newPage(b, state, scheme) {
  const ctx = await b.newContext({ storageState: state, viewport: { width: 1440, height: 900 }, colorScheme: scheme });
  const p = await ctx.newPage();
  await p.addInitScript((s) => { try { localStorage.setItem('theme', s); } catch (e) {} }, scheme);
  p.on('console', (m) => { if (m.type() === 'error') result.console.push({ scheme, url: p.url(), text: m.text().slice(0, 300) }); });
  p.on('pageerror', (e) => result.console.push({ scheme, url: p.url(), text: 'pageerror ' + String(e).slice(0, 300) }));
  p.on('requestfailed', (r) => result.network.push({ scheme, status: 'failed ' + (r.failure() || {}).errorText, url: r.url().slice(0, 250) }));
  p.on('response', (r) => { if (r.status() >= 400) result.network.push({ scheme, status: r.status(), url: r.url().slice(0, 250) }); });
  p.on('requestfinished', (r) => {
    if (/\/api\/admin\/platform\/delivery/.test(r.url())) {
      const t = r.timing();
      r.response().then((resp) => result.apiTimings.push({ scheme, url: r.url().replace(/^https:\/\/[^/]+/, ''), status: resp && resp.status(),
        ms: Math.round(t.responseEnd >= 0 ? t.responseEnd : -1), ttfbMs: Math.round(t.responseStart) })).catch(() => {});
    }
  });
  return { ctx, p };
}

async function shot(p, name) {
  const txt = await p.evaluate(() => document.body.innerText);
  const priv = EMAIL.test(txt);
  let f = path.join(priv ? PRIV : OUT, name + '.png');
  await p.screenshot({ path: f });
  if (fs.statSync(f).size > 300 * 1024) { fs.unlinkSync(f); f = f.replace(/\.png$/, '.jpg'); await p.screenshot({ path: f, type: 'jpeg', quality: 70 }); }
  result.shots.push({ file: f, kb: Math.round(fs.statSync(f).size / 1024), emailInText: priv });
}

async function fillDate(p, label, value) {
  const inp = p.getByTestId('delivery-range').getByLabel(label, { exact: true });
  await inp.click();
  await inp.fill('');
  await inp.type(value, { delay: 30 });
  await inp.press('Tab');
  await p.waitForTimeout(400);
  return inp.inputValue();
}

(async () => {
  let { file: state } = await ensureState('cis-admin');
  const b = await chromium.launch();
  // ---- (1) + (3) light: pick the range and Apply
  {
    const { ctx, p } = await newPage(b, state, 'light');
    await p.goto(BASE, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
    await p.waitForTimeout(3000);
    if (p.url().includes('/login')) { ({ file: state } = await ensureState('cis-admin')); throw new Error('login page, rerun'); }
    await p.getByTestId('delivery-range-picker').getByRole('radio', { name: 'Custom' }).click();
    await p.waitForTimeout(800);
    const fromVal = await fillDate(p, 'From', '09/11/2026');
    const toVal = await fillDate(p, 'To', '15/11/2026');
    const apply = p.getByTestId('delivery-range').getByRole('button', { name: 'Apply' });
    const applyEnabled = await apply.isEnabled();
    const hintBefore = await p.getByTestId('delivery-range').innerText();
    const t0 = Date.now();
    let apiResp = null;
    const waitApi = p.waitForResponse((r) => /\/api\/admin\/platform\/delivery/.test(r.url()) && /custom/.test(r.url()), { timeout: 90000 })
      .then((r) => { apiResp = { status: r.status(), url: r.url().replace(/^https:\/\/[^/]+/, ''), ms: Date.now() - t0 }; }).catch((e) => { apiResp = { error: String(e).slice(0, 200), ms: Date.now() - t0 }; });
    if (applyEnabled) await apply.click();
    await waitApi;
    await p.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {});
    const settledMs = Date.now() - t0;
    await p.waitForTimeout(1500);
    const body = await p.evaluate(() => document.body.innerText);
    const lines = body.split('\n').filter((l) => /9 Nov|15 Nov|09\/11|15\/11|2026-11-09|2026-11-15|custom/i.test(l)).slice(0, 15);
    const h = await p.evaluate(() => [...document.querySelectorAll('h1,h2,h3')].map((e) => e.textContent.trim()).slice(0, 12));
    const errText = body.split('\n').filter((l) => /error|failed|could not|timed out|try again|not available|unavailable/i.test(l)).slice(0, 8);
    result.checks.c1 = { fromVal, toVal, applyEnabled, hintBefore: hintBefore.replace(/\n/g, ' | '), url: p.url(), apiResp, settledMs, headings: h, rangeLines: lines, errText };
    await p.evaluate(() => window.scrollTo(0, 0));
    await shot(p, 'custom-applied-1440-light');
    // ---- (2) merge-queue tab for the same range
    const mq = p.getByRole('tab', { name: /merge queue/i });
    if (await mq.count()) { await mq.first().click(); } else {
      const u = new URL(p.url()); u.searchParams.set('app', 'merge-queue'); await p.goto(u.toString(), { waitUntil: 'networkidle', timeout: 90000 }).catch(() => {});
    }
    await p.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {});
    await p.waitForTimeout(3000);
    const mqUrl = p.url();
    const repos = await p.evaluate(() => [...document.querySelectorAll('[role=radiogroup] [role=radio], [role=tab]')].map((e) => e.textContent.trim()));
    const readRecent = () => p.evaluate(() => {
      const s = document.querySelector('[data-testid="queue-recent"]');
      if (!s) return null;
      const rows = [...s.querySelectorAll('[data-testid="kit-datatable-row"]')].map((r) => r.innerText.replace(/\n/g, ' | '));
      return { head: s.innerText.split('\n').slice(0, 3).join(' | '), rows };
    });
    const recent = await readRecent();
    result.checks.c2 = { mqUrl, repos, recent };
    const sec = p.getByTestId('queue-recent').first();
    if (await sec.count()) { await sec.evaluate((el) => el.scrollIntoView({ block: 'start' })); await p.waitForTimeout(800); }
    await shot(p, 'custom-recent-entries');
    // other repos in the merge queue picker
    result.checks.c2.otherRepos = [];
    for (const repo of ['cis', 'booking', 'partner']) {
      const u = new URL(mqUrl); u.searchParams.set('repo', repo);
      const t1 = Date.now();
      await p.goto(u.toString(), { waitUntil: 'networkidle', timeout: 90000 }).catch(() => {});
      await p.waitForTimeout(2500);
      result.checks.c2.otherRepos.push({ repo, url: p.url(), ms: Date.now() - t1, recent: await readRecent() });
    }
    await ctx.close();
  }
  // ---- dark shot of the custom view (direct URL)
  {
    const { ctx, p } = await newPage(b, state, 'dark');
    const t0 = Date.now();
    await p.goto(BASE + '?range=custom&from=2026-11-09&to=2026-11-15', { waitUntil: 'networkidle', timeout: 90000 }).catch(() => {});
    result.checks.darkLoadMs = Date.now() - t0;
    await p.waitForTimeout(2500);
    result.checks.darkUrl = p.url();
    await shot(p, 'custom-dark');
    await ctx.close();
  }
  await b.close();
  fs.writeFileSync(path.join(OUT, 'scripts', 'verify-result.json'), JSON.stringify(result, null, 1).replace(new RegExp(EMAIL.source, 'g'), '<email>'));
  console.log(JSON.stringify(result, null, 1).replace(new RegExp(EMAIL.source, 'g'), '<email>'));
})().catch((e) => { console.error('FATAL', e); process.exit(1); });
