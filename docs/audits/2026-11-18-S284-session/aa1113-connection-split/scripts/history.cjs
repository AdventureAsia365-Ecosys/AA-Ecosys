// AA-1113 follow-up (read-only): open the History drawer of crm.ai.connection_monthly_cap_usd and sample the
// connection-split read 6 times to see how often the CRM relay answers crm_unavailable.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const OUT = '/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-18-S284-session/aa1113-connection-split';
const PRIV = '/home/nghiep/projects/AA-Ecosys/.tmp-session/S284/private-shots';
const HOST = 'https://aa-cis.lumiguides.it.com';
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/;
(async () => {
  const { file: state } = await ensureState('cis-admin');
  const b = await chromium.launch();
  const ctx = await b.newContext({ storageState: state, viewport: { width: 1440, height: 900 }, colorScheme: 'light' });
  const p = await ctx.newPage();
  await p.addInitScript(() => { try { localStorage.setItem('theme', 'light'); } catch (e) {} });
  const errs = []; const hist = [];
  p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 300)); });
  p.on('response', async (r) => {
    if (r.status() >= 400) errs.push(`${r.status()} ${r.url()}`);
    if (r.url().includes('/history')) { try { hist.push({ url: r.url(), body: await r.json() }); } catch (e) {} }
  });
  await p.goto(`${HOST}/admin/platform/settings?app=crm&area=ai&key=crm.ai.connection_monthly_cap_usd`, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(4000);
  await p.getByRole('button', { name: 'History' }).first().click();
  await p.waitForTimeout(4000);
  let f = path.join(OUT, 'settings-crm-connection-cap-history.png');
  await p.screenshot({ path: f });
  const txt = await p.evaluate(() => document.body.innerText);
  if (EMAIL.test(txt)) { const d = path.join(PRIV, path.basename(f)); fs.renameSync(f, d); f = d; }
  const drawer = await p.locator('[role=dialog]').first().innerText().catch(() => null);
  const samples = [];
  for (let i = 0; i < 6; i++) {
    const r = await p.request.get(`${HOST}/api/admin/ai-gateway/connection-split`);
    let j = null; try { j = await r.json(); } catch (e) {}
    const a2 = j && j.rows ? j.rows.find((x) => x.connection_key === 'acc2') : null;
    samples.push({ status: r.status(), crm_error: j && j.crm_error, acc2_crm: a2 && a2.crm_share_usd, acc2_known: a2 && a2.crm_known });
    await p.waitForTimeout(1500);
  }
  await b.close();
  const res = { shot: f, kb: Math.round(fs.statSync(f).size / 1024), drawer: drawer && drawer.slice(0, 2000), history: hist, samples, errs };
  fs.writeFileSync(path.join(OUT, 'scripts', 'history-result.json'), JSON.stringify(res, null, 2));
  console.log(JSON.stringify(res, null, 2).slice(0, 6000));
})();
