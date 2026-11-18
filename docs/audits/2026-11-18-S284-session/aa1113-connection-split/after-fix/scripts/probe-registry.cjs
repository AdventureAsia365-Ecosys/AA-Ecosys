// AA-1113 after-fix (read-only): re-read the CRM settings registry list 5 times to see whether the 503 seen on the first
// page load repeats.
const fs = require('fs');
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const HOST = 'https://aa-cis.lumiguides.it.com';
(async () => {
  const { file: state } = await ensureState('cis-admin');
  const b = await chromium.launch();
  const ctx = await b.newContext({ storageState: state });
  const p = await ctx.newPage();
  await p.goto(`${HOST}/admin`, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
  const out = [];
  for (let i = 0; i < 5; i++) {
    const t = Date.now();
    const r = await p.request.get(`${HOST}/api/admin/settings/registry?app=crm`);
    let body = null; try { body = await r.json(); } catch (e) {}
    const items = body && (body.items || body.settings || body.rows || (Array.isArray(body) ? body : null));
    const row = Array.isArray(items) ? items.find((x) => (x.key || (x.definition && x.definition.key)) === 'crm.ai.connection_monthly_cap_usd') : null;
    out.push({ i: i + 1, status: r.status(), ms: Date.now() - t, detail: r.status() >= 400 ? JSON.stringify(body).slice(0, 300) : undefined,
      value: row ? JSON.stringify(row.value ?? row.current_value ?? row.effective_value ?? null) : undefined });
    await p.waitForTimeout(1500);
  }
  await b.close();
  fs.writeFileSync(__dirname + '/probe-registry-result.json', JSON.stringify(out, null, 2));
  console.log(JSON.stringify(out, null, 2));
})();
