// AA-995 S256: list image/font requests of one page at Lighthouse's mobile viewport (412x823 @1.75), plus the
// image preload links in the DOM after load. Usage: node reqs.cjs <url>
const { chromium } = require('/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const c = await b.newContext({ viewport: { width: 412, height: 823 }, deviceScaleFactor: 1.75, isMobile: true, hasTouch: true });
  const p = await c.newPage(); const t0 = Date.now(); if (process.env.BLOCK_RSC) await p.route(/_rsc=/, (r) => r.abort());
  p.on('request', (r) => { const rt = r.resourceType(); if (rt === 'image' || rt === 'font') console.log(String(Date.now() - t0).padStart(5), rt.padEnd(5), r.url().slice(0, 130)); });
  await p.goto(process.argv[2], { waitUntil: 'load' }); await p.waitForTimeout(2500);
  const links = await p.evaluate(() => [...document.querySelectorAll('link[rel=preload][as=image]')].map((l) => ({ href: l.getAttribute('href'), srcset: (l.getAttribute('imagesrcset') || '').slice(0, 60), sizes: l.getAttribute('imagesizes'), inBody: !document.head.contains(l) })));
  console.log(JSON.stringify(links, null, 1));
  const lcp = await p.evaluate(() => new Promise((res) => new PerformanceObserver((l) => { const e = l.getEntries().at(-1); res({ url: e.url, size: e.size, t: Math.round(e.startTime) }); }).observe({ type: 'largest-contentful-paint', buffered: true })));
  console.log('LCP', JSON.stringify(lcp));
  const cur = await p.evaluate(() => [...document.images].filter((i) => i.fetchPriority === 'high').map((i) => i.currentSrc));
  console.log('high imgs currentSrc', cur);
  await b.close();
})();
