// Check 4 follow-up: does the side table of contents mark the clicked entry once the smooth scroll has settled?
const { chromium } = require('playwright');
const { openPage, goto, BASE } = require('./common.cjs');
(async () => {
  const b = await chromium.launch();
  const { ctx, page, log } = await openPage(b, { width: 1920, height: 1080, scheme: 'light' });
  await goto(page, `${BASE}?path=${encodeURIComponent('docs/engineering-handbook.md')}`);
  const cur = () => page.evaluate(() => { const c = document.querySelector('[data-testid=docs-toc] a[aria-current=location]'); return c && c.innerText.trim(); });
  const out = [];
  for (const i of [6, 20, 40]) {
    const a = page.locator('[data-testid=docs-toc] a').nth(i);
    const text = (await a.innerText()).trim();
    await a.click();
    await page.waitForTimeout(1800); const at18 = await cur();
    await page.waitForTimeout(3000); const at48 = await cur();
    await page.mouse.wheel(0, 1); await page.waitForTimeout(800); const afterNudge = await cur();
    out.push({ clicked: text, at1_8s: at18, at4_8s: at48, afterNudge });
  }
  console.log(JSON.stringify({ out, console: log.console, failed: log.failed }, null, 1));
  await ctx.close(); await b.close();
})();
