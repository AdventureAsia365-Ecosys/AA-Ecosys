// AA-995 S256: after-build check of the four measured pages at 390 and 1440 (light): console errors, hydration
// warnings, horizontal overflow, the LCP image's currentSrc and loading attributes, a prefetch test (no other page's
// hero downloaded), and a viewport screenshot. Usage: node verify.cjs <base> <out-dir>
const { chromium } = require('/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright-core');
const base = process.argv[2]; const out = process.argv[3];
const pages = [
  ['home', '/'],
  ['destinations', '/destinations'],
  ['bhutan', '/destinations/bhutan'],
  ['tour', '/tours/sri-lanka-cultural-tour-kandy-dambulla-and-sigiriya-3-days-sri-lanka-28e22489'],
];
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--ignore-certificate-errors'] });
  const report = [];
  for (const w of [390, 1440]) {
    for (const [name, path] of pages) {
      const c = await b.newContext({ viewport: { width: w, height: w === 390 ? 844 : 900 }, deviceScaleFactor: w === 390 ? 2 : 1, isMobile: w === 390, ignoreHTTPSErrors: true, colorScheme: 'light' });
      const p = await c.newPage();
      const errs = []; const imgs = [];
      p.on('console', (m) => { if (m.type() === 'error' || /hydrat/i.test(m.text())) errs.push(m.text().slice(0, 160)); });
      p.on('pageerror', (e) => errs.push('pageerror ' + String(e).slice(0, 160)));
      p.on('request', (r) => { if (r.resourceType() === 'image') imgs.push(r.url().replace(base, '')); });
      await p.goto(base + path, { waitUntil: 'load' });
      await p.waitForTimeout(2500);
      const info = await p.evaluate(() => {
        const hi = [...document.images].filter((i) => i.fetchPriority === 'high' || i.closest('picture'));
        return {
          overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          lcpImgs: hi.slice(0, 2).map((i) => ({ src: (i.currentSrc || '').replace(location.origin, '').slice(0, 90), loading: i.loading, fp: i.fetchPriority, complete: i.complete && i.naturalWidth > 0 })),
        };
      });
      // Other pages' heroes requested here (the prefetch leak S256 fixes): any hero of home/destination not on this page.
      const foreignHero = imgs.filter((u) => (name !== 'home' && /\/hero\/home-/.test(u)) || (name !== 'bhutan' && /bhutan\/1GcwUTa2.*-1600/.test(u)));
      await p.screenshot({ path: `${out}/${name}-${w}-light.png` });
      report.push({ page: name, width: w, errors: errs, ...info, foreignHero });
      await c.close();
    }
  }
  await b.close();
  console.log(JSON.stringify(report, null, 1));
})();
