// Interleaved confirmation: ROUNDS rounds, each round measures before then after (order alternates per round),
// so machine load hits both builds alike. node interleave.mjs <outFile>
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';
import fs from 'node:fs';
const ROUNDS = Number(process.env.ROUNDS || 5);
const targets = { 'before-0d6b5eb': 'http://127.0.0.1:3101', 'after-60e5db1': 'http://127.0.0.1:3102' };
const paths = ['/plan?country=Laos', '/plan'];
const med = a => { const s = [...a].sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
async function one(url) {
  const udd = fs.mkdtempSync(process.cwd() + '/prof-');
  const chrome = await chromeLauncher.launch({ userDataDir: udd, chromePath: '/usr/bin/google-chrome', chromeFlags: ['--headless=new', '--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const r = await lighthouse(url, { port: chrome.port, logLevel: 'error', onlyCategories: ['performance'] });
  await chrome.kill(); fs.rmSync(udd, { recursive: true, force: true });
  const a = r.lhr.audits;
  return { score: Math.round(r.lhr.categories.performance.score * 100), lcp_ms: Math.round(a['largest-contentful-paint'].numericValue), tbt_ms: Math.round(a['total-blocking-time'].numericValue), cls: Number(a['cumulative-layout-shift'].numericValue.toFixed(3)), fcp_ms: Math.round(a['first-contentful-paint'].numericValue), si_ms: Math.round(a['speed-index'].numericValue) };
}
const out = { method: `interleaved, ${ROUNDS} rounds, order alternates each round, same local servers and data as the 3-run set`, urls: {} };
for (const p of paths) {
  const rows = { 'before-0d6b5eb': [], 'after-60e5db1': [] };
  for (let i = 0; i < ROUNDS; i++) {
    const order = i % 2 ? ['after-60e5db1', 'before-0d6b5eb'] : ['before-0d6b5eb', 'after-60e5db1'];
    for (const t of order) { const row = await one(targets[t] + p); rows[t].push(row); console.log(p, t, JSON.stringify(row)); }
  }
  out.urls[p] = {};
  for (const t of Object.keys(rows)) {
    const m = k => med(rows[t].map(r => r[k]));
    out.urls[p][t] = { median: { score: m('score'), lcp_ms: m('lcp_ms'), tbt_ms: m('tbt_ms'), cls: m('cls'), fcp_ms: m('fcp_ms'), si_ms: m('si_ms') }, runs: rows[t] };
  }
}
fs.writeFileSync(process.argv[2], JSON.stringify(out, null, 2) + '\n');
console.log('wrote');
