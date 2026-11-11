// node run.mjs <label> <baseUrl> <outDir> [cookieHeader]
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';
import fs from 'node:fs';
const [label, base, outDir, cookie] = process.argv.slice(2);
const paths = ['/plan?country=Laos', '/plan'];
const RUNS = 3;
fs.mkdirSync(outDir, { recursive: true });
const med = a => { const s = [...a].sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
const summary = { label, base, lighthouse: null, preset: 'mobile (Lighthouse default: Moto G Power emulation, simulated slow 4G throttling); headless Chrome with software WebGL (SwiftShader) so the Mapbox map can start', category: 'performance', runs_per_url: RUNS, urls: {} };
for (const p of paths) {
  const url = base + p;
  const runs = [];
  for (let i = 0; i <= RUNS; i++) { // run 0 = warm-up (server first hit), discarded
    const udd = fs.mkdtempSync(process.cwd() + '/prof-'); const chrome = await chromeLauncher.launch({ userDataDir: udd, chromePath: '/usr/bin/google-chrome', chromeFlags: ['--headless=new', '--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
    const flags = { port: chrome.port, output: 'json', logLevel: 'error', onlyCategories: ['performance'] };
    if (cookie) flags.extraHeaders = { Cookie: cookie };
    const r = await lighthouse(url, flags);
    await chrome.kill(); fs.rmSync(udd, { recursive: true, force: true });
    const lhr = r.lhr;
    summary.lighthouse = lhr.lighthouseVersion;
    const reqs = lhr.audits['network-requests']?.details?.items ?? [];
    const doc = reqs.find(x => x.resourceType === 'Document');
    const mapbox = reqs.filter(x => /mapbox\.com/.test(x.url)).map(x => x.statusCode);
    const a = lhr.audits;
    const row = {
      run: i, warmup: i === 0,
      score: Math.round((lhr.categories.performance.score ?? 0) * 100),
      lcp_ms: Math.round(a['largest-contentful-paint'].numericValue),
      tbt_ms: Math.round(a['total-blocking-time'].numericValue),
      cls: Number(a['cumulative-layout-shift'].numericValue.toFixed(3)),
      fcp_ms: Math.round(a['first-contentful-paint'].numericValue),
      si_ms: Math.round(a['speed-index'].numericValue),
      doc_status: doc?.statusCode ?? null,
      final_url: lhr.finalDisplayedUrl,
      requests: reqs.length,
      transfer_kb: Math.round(reqs.reduce((s, x) => s + (x.transferSize || 0), 0) / 1024),
      script_kb: Math.round(reqs.filter(x => x.resourceType === 'Script').reduce((s, x) => s + (x.transferSize || 0), 0) / 1024),
      mapbox_statuses: [...new Set(mapbox)],
      runtime_error: lhr.runtimeError?.code ?? null,
      lcp_element: a['largest-contentful-paint-element']?.details?.items?.[0]?.items?.[0]?.node?.nodeLabel?.slice(0, 80) ?? null,
      console_errors: (a['errors-in-console']?.details?.items ?? []).length,
      warnings: lhr.runWarnings,
    };
    runs.push(row);
    console.log(label, p, JSON.stringify(row));
  }
  const kept = runs.filter(r => !r.warmup);
  const m = k => med(kept.map(r => r[k]));
  summary.urls[p] = { url, median: { score: m('score'), lcp_ms: m('lcp_ms'), tbt_ms: m('tbt_ms'), cls: m('cls'), fcp_ms: m('fcp_ms'), si_ms: m('si_ms'), transfer_kb: m('transfer_kb'), script_kb: m('script_kb') }, runs };
}
fs.writeFileSync(`${outDir}/${label}.json`, JSON.stringify(summary, null, 2) + '\n');
console.log('wrote', `${outDir}/${label}.json`);
