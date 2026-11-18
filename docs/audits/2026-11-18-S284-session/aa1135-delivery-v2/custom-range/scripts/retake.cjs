// AA-1135 custom range retake (read-only): warm-cache Apply flow, success shot, merge-queue Recent entries for CIS
// with a per-row in-range check. The first run's shots are kept (first request 504).
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const OUT = '/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-18-S284-session/aa1135-delivery-v2/custom-range';
const BASE = 'https://aa-cis.lumiguides.it.com/admin/platform/delivery';
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z.]{2,}/;
const MON = { Jan: 0, Feb: 1, Mar: 2, Apr: 3, May: 4, Jun: 5, Jul: 6, Aug: 7, Sep: 8, Oct: 9, Nov: 10, Dec: 11 };
const res = { console: [], network: [], api: [] };
(async () => {
  const { file: state } = await ensureState('cis-admin');
  const b = await chromium.launch();
  const ctx = await b.newContext({ storageState: state, viewport: { width: 1440, height: 900 }, colorScheme: 'light' });
  const p = await ctx.newPage();
  await p.addInitScript(() => { try { localStorage.setItem('theme', 'light'); } catch (e) {} });
  p.on('console', (m) => { if (m.type() === 'error') res.console.push(m.text().slice(0, 300)); });
  p.on('response', (r) => { if (r.status() >= 400) res.network.push(r.status() + ' ' + r.url().slice(0, 200)); });
  p.on('requestfinished', (r) => { if (/\/api\/admin\/platform\/delivery/.test(r.url())) res.api.push(Math.round(r.timing().responseEnd) + 'ms ' + r.url().replace(/^https:\/\/[^/]+/, '')); });
  res.tz = await p.evaluate(() => Intl.DateTimeFormat().resolvedOptions().timeZone).catch(() => null);
  await p.goto(BASE, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(2500);
  res.tz = await p.evaluate(() => Intl.DateTimeFormat().resolvedOptions().timeZone);
  await p.getByTestId('delivery-range-picker').getByRole('radio', { name: 'Custom' }).click();
  for (const [l, v] of [['From', '09/11/2026'], ['To', '15/11/2026']]) {
    const i = p.getByTestId('delivery-range').getByLabel(l, { exact: true });
    await i.click(); await i.fill(''); await i.type(v, { delay: 30 }); await i.press('Tab'); await p.waitForTimeout(300);
  }
  const apply = p.getByTestId('delivery-range').getByRole('button', { name: 'Apply' });
  res.applyEnabled = await apply.isEnabled();
  const t0 = Date.now();
  const w = p.waitForResponse((r) => /\/api\/admin\/platform\/delivery\?.*custom/.test(r.url()), { timeout: 90000 }).then((r) => ({ status: r.status(), ms: Date.now() - t0 }));
  await apply.click();
  res.applyResp = await w;
  await p.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {});
  res.applySettledMs = Date.now() - t0;
  await p.waitForTimeout(1500);
  res.url = p.url();
  res.rangeText = (await p.getByTestId('delivery-range').innerText()).replace(/\n/g, ' | ');
  const body = await p.evaluate(() => document.body.innerText);
  res.builtLine = (body.match(/Built [^\n]*/) || [null])[0];
  res.errorLines = body.split('\n').filter((l) => /could not|timed out|error/i.test(l));
  res.email = EMAIL.test(body);
  await p.evaluate(() => window.scrollTo(0, 0));
  await p.screenshot({ path: path.join(OUT, 'custom-applied-1440-light.png') });
  // Merge queue, CIS repo, Recent entries
  await p.getByRole('tab', { name: 'Merge queue' }).click();
  await p.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(1500);
  await p.getByRole('button', { name: 'CIS', exact: true }).first().click().catch(() => {});
  await p.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(3000);
  res.mqUrl = p.url();
  if (!(await p.getByTestId('queue-recent').count())) {
    const u = new URL(p.url()); u.searchParams.set('repo', 'cis'); await p.goto(u.toString(), { waitUntil: 'networkidle', timeout: 90000 }).catch(() => {}); await p.waitForTimeout(3000);
    res.mqUrl = p.url() + ' (direct)';
  }
  const rec = await p.evaluate(() => {
    const s = document.querySelector('[data-testid="queue-recent"]');
    const rows = [...s.querySelectorAll('[data-testid="kit-datatable-row"]')].map((r) => r.innerText.replace(/\s+/g, ' '));
    const extra = s.innerText.split('\n').filter((l) => /of \d+|more|showing|first \d+|newest/i.test(l));
    return { rows, extra, pager: !!s.querySelector('[aria-label*="page" i], [data-testid*="pager"]') };
  });
  const lo = new Date(2026, 10, 9, 7, 0), hi = new Date(2026, 10, 16, 7, 0); // local (ICT) view of 9 Nov 00:00Z .. 16 Nov 00:00Z
  const stamps = rec.rows.map((r) => { const m = r.match(/(\d{1,2}) (\w{3}) (\d{4}), (\d{2}):(\d{2})\s*$/); return m ? new Date(+m[3], MON[m[2]], +m[1], +m[4], +m[5]) : null; });
  res.recent = { count: rec.rows.length, extra: rec.extra, pager: rec.pager, parsed: stamps.filter(Boolean).length,
    outOfRange: rec.rows.filter((r, i) => !stamps[i] || stamps[i] < lo || stamps[i] >= hi),
    newest: rec.rows[0] && rec.rows[0].slice(-20), oldest: rec.rows.at(-1) && rec.rows.at(-1).slice(-20) };
  await p.getByTestId('queue-recent').first().evaluate((el) => el.scrollIntoView({ block: 'start' }));
  await p.waitForTimeout(800);
  const f = path.join(OUT, 'custom-recent-entries.png');
  await p.screenshot({ path: f });
  res.recentShotKB = Math.round(fs.statSync(f).size / 1024);
  await b.close();
  console.log(JSON.stringify(res, null, 1));
  fs.writeFileSync(path.join(OUT, 'scripts', 'retake-result.json'), JSON.stringify(res, null, 1));
})().catch((e) => { console.error('FATAL', e); process.exit(1); });
