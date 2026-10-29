// AA-995 S256: the Bhutan hero at 412 px @1.75x with the 1600 w file and with the 600 w file, side by side.
const { chromium } = require('/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--ignore-certificate-errors'] });
  const c = await b.newContext({ viewport: { width: 412, height: 823 }, deviceScaleFactor: 1.75, isMobile: true, ignoreHTTPSErrors: true });
  const p = await c.newPage();
  await p.goto('https://localhost:3998/destinations/bhutan', { waitUntil: 'load' }); await p.waitForTimeout(1500);
  const out = process.argv[2];
  await p.screenshot({ path: `${out}/bhutan-hero-1600w-412.png`, clip: { x: 0, y: 0, width: 412, height: 480 } });
  await p.evaluate(() => { const i = document.querySelector('img.tp-hero-img'); i.removeAttribute('srcset'); i.src = i.src.replace('-1600.webp', '-600.webp'); });
  await p.waitForTimeout(1500);
  await p.screenshot({ path: `${out}/bhutan-hero-600w-412.png`, clip: { x: 0, y: 0, width: 412, height: 480 } });
  await b.close();
})();
