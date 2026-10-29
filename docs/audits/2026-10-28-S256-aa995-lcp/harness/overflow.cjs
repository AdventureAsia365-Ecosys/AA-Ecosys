// AA-995 S256: which elements stick out past the viewport on one page at 390 px. Usage: node overflow.cjs <url>
const { chromium } = require('/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--ignore-certificate-errors'] });
  const c = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, ignoreHTTPSErrors: true });
  const p = await c.newPage(); await p.goto(process.argv[2], { waitUntil: 'load' }); await p.waitForTimeout(Number(process.env.WAIT || 2500));
  console.log(await p.evaluate(() => {
    const vw = document.documentElement.clientWidth;
    const out = [];
    for (const el of document.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect();
      if (r.right > vw + 0.5 && getComputedStyle(el).position !== 'fixed') {
        let a = el.parentElement, clipped = false;
        while (a) { const o = getComputedStyle(a).overflowX; if (o === 'hidden' || o === 'auto' || o === 'scroll' || o === 'clip') { clipped = true; break; } a = a.parentElement; }
        if (!clipped) out.push(`${el.tagName.toLowerCase()}.${String(el.className).slice(0, 60)} right=${r.right.toFixed(1)}`);
      }
    }
    return { sw: document.documentElement.scrollWidth, vw, out: out.slice(0, 8) };
  }));
  await b.close();
})();
