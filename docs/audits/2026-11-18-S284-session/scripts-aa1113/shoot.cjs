// AA-1113 live check: AI gateway > Budgets "Connection budget split" + Routing "data class" + the two Settings links.
// Read-only: opens tabs and links only.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const OUT = '/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-18-S284-session/aa1113-connection-split';
const PRIV = '/home/nghiep/projects/AA-Ecosys/.tmp-session/S284/private-shots';
const BASE = 'https://aa-cis.lumiguides.it.com';
const NOISE = /google-analytics|googletagmanager|vercel-insights|_vercel\/insights|speed-insights|sentry|fonts\.g/;
const report = { pages: [] };

async function open(b, state, { vw, scheme }) {
  const [w, h] = vw === 'mobile' ? [390, 844] : [1440, 900];
  const ctx = await b.newContext({ storageState: state, viewport: { width: w, height: h }, colorScheme: scheme,
    isMobile: vw === 'mobile', hasTouch: vw === 'mobile' });
  const p = await ctx.newPage();
  await p.addInitScript((s) => { try { localStorage.setItem('theme', s); } catch (e) {} }, scheme);
  const log = { console: [], network: [] };
  p.on('console', (m) => { if (m.type() === 'error') log.console.push(m.text().slice(0, 300)); });
  p.on('pageerror', (e) => log.console.push('pageerror: ' + String(e).slice(0, 300)));
  p.on('response', (r) => { if (r.status() >= 400 && !NOISE.test(r.url())) log.network.push(`${r.status()} ${r.request().method()} ${r.url().slice(0, 200)}`); });
  p.on('requestfailed', (r) => { if (!NOISE.test(r.url())) log.network.push(`FAILED ${r.failure()?.errorText} ${r.url().slice(0, 200)}`); });
  return { ctx, p, log };
}

async function shot(target, name, opts = {}) {
  let f = path.join(OUT, name + '.png');
  await target.screenshot({ path: f, ...opts });
  if (fs.statSync(f).size >= 400 * 1024) {
    fs.unlinkSync(f); f = path.join(OUT, name + '.jpg');
    await target.screenshot({ path: f, type: 'jpeg', quality: 70, ...opts });
  }
  return f;
}

async function guardEmail(p, f) {
  const txt = await p.evaluate(() => document.body.innerText);
  if (/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}/.test(txt)) {
    // the e-mail may be off-shot; be conservative only if it is visible in the viewport/element shot
    const vis = await p.evaluate(() => {
      const re = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}/;
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      const hits = [];
      while (walker.nextNode()) {
        const n = walker.currentNode; if (!re.test(n.textContent)) continue;
        const r = n.parentElement.getBoundingClientRect(); const cs = getComputedStyle(n.parentElement);
        if (r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none') hits.push({ t: n.textContent.trim().replace(re, '<email>').slice(0, 80), top: Math.round(r.top) });
      }
      return hits;
    });
    if (vis.length) { const dst = path.join(PRIV, path.basename(f)); fs.renameSync(f, dst); return { moved: dst, hits: vis }; }
  }
  return { moved: null };
}

async function budgets(b, state, vw, scheme, withLinks) {
  const { ctx, p, log } = await open(b, state, { vw, scheme });
  const r = { page: `budgets ${vw} ${scheme}` };
  await p.goto(`${BASE}/admin/ai-gateway?tab=budgets`, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  r.url = p.url(); r.login = /\/login|signin|auth/.test(p.url());
  const sec = p.getByTestId('ai-gateway-budgets-connection-split').first();
  try { await sec.waitFor({ timeout: 30000 }); } catch (e) { r.sectionMissing = true; }
  if (!r.sectionMissing) {
    await p.waitForFunction(() => {
      const s = document.querySelector('[data-testid="ai-gateway-budgets-connection-split"]');
      return s && /acc1|No LLM connection|Could not load/.test(s.innerText);
    }, null, { timeout: 30000 }).catch(() => {});
    await p.waitForTimeout(1500);
    await sec.scrollIntoViewIfNeeded();
    r.sectionText = (await sec.innerText()).slice(0, 4000);
    r.headers = await sec.locator('th, [role=columnheader]').allInnerTexts();
    r.keys = ['acc1', 'acc2', 'acc2-usw2', 'acc3', 'anthropic-direct', 'bedrock-llm-org', 'openai-direct']
      .map((k) => [k, new RegExp(`(^|\\s)${k}(\\s|$)`).test(r.sectionText)]);
    r.rowCount = await sec.locator('tbody tr').count();
    r.noProviderBudgetCount = (r.sectionText.match(/No provider budget/g) || []).length;
    r.crmNotice = (r.sectionText.match(/The CRM share could not be read[^\n]*/) || [null])[0];
    r.links = await sec.locator('a').evaluateAll((as) => as.map((a) => ({ t: a.innerText, href: a.getAttribute('href') })));
    const f = await shot(sec, `budgets-split-${vw}-${scheme}`);
    r.shot = path.basename(f); r.email = await guardEmail(p, f);
  }
  if (withLinks && !r.sectionMissing) {
    for (const [label, name, key] of [['Provider budgets', 'settings-provider-budget-row', 'cis.spend.connection_provider_budget_usd'],
      ['CRM shares', 'settings-crm-share-row', 'crm.ai.connection_monthly_cap_usd']]) {
      const l = { link: label };
      await p.goto(`${BASE}/admin/ai-gateway?tab=budgets`, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
      const a = p.getByTestId('ai-gateway-budgets-connection-split').getByRole('link', { name: label, exact: true });
      await a.waitFor({ timeout: 30000 });
      await a.click();
      await p.waitForURL(/platform\/settings/, { timeout: 30000 }).catch(() => {});
      await p.waitForLoadState('networkidle').catch(() => {});
      await p.waitForTimeout(3500);
      l.url = p.url();
      l.keyInUrl = l.url.includes(encodeURIComponent(key)) || l.url.includes(key);
      l.activeTab = await p.getByTestId('settings-apps').locator('[aria-selected=true]').allInnerTexts().catch(() => []);
      l.search = await p.getByTestId('settings-search').inputValue().catch(() => null);
      l.count = await p.getByTestId('settings-search-count').innerText().catch(() => null);
      const body = await p.evaluate(() => document.body.innerText);
      l.keyVisible = body.includes(key);
      const idx = body.indexOf(key);
      l.rowText = idx >= 0 ? body.slice(Math.max(0, idx - 300), idx + 500) : body.slice(0, 600);
      const keyEl = p.getByText(key, { exact: false }).first();
      if (await keyEl.count()) await keyEl.scrollIntoViewIfNeeded().catch(() => {});
      await p.evaluate(() => window.scrollBy(0, -120));
      const f = await shot(p, name);
      l.shot = path.basename(f); l.email = await guardEmail(p, f);
      (r.linkChecks ||= []).push(l);
    }
  }
  r.console = log.console; r.network = log.network;
  await ctx.close();
  return r;
}

async function routing(b, state) {
  const { ctx, p, log } = await open(b, state, { vw: 'desktop', scheme: 'light' });
  const r = { page: 'routing desktop light' };
  await p.goto(`${BASE}/admin/ai-gateway?tab=routing`, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  r.url = p.url();
  const dc = p.getByTestId('ai-gateway-data-class').first();
  try { await dc.waitFor({ timeout: 40000 }); } catch (e) { r.missing = true; }
  if (!r.missing) {
    await p.waitForTimeout(2500);
    r.text = (await dc.innerText()).slice(0, 3000);
    r.freeTextBlock = await p.getByTestId('ai-gateway-data-class-free-text').innerText().catch(() => null);
    const card = dc.locator('xpath=ancestor::section[1]');
    const target = (await card.count()) ? card : dc;
    await target.scrollIntoViewIfNeeded();
    const f = await shot(target, 'routing-data-class-desktop-light');
    r.shot = path.basename(f); r.email = await guardEmail(p, f);
  }
  r.console = log.console; r.network = log.network;
  await ctx.close();
  return r;
}

(async () => {
  const { file: state } = await ensureState('cis-admin');
  const b = await chromium.launch();
  report.pages.push(await budgets(b, state, 'desktop', 'light', true));
  report.pages.push(await budgets(b, state, 'desktop', 'dark', false));
  report.pages.push(await budgets(b, state, 'mobile', 'light', false));
  report.pages.push(await routing(b, state));
  await b.close();
  fs.writeFileSync(path.join(__dirname, 'result.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
})().catch((e) => { console.error(e); process.exit(1); });
