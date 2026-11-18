// Check 1: reader columns at 1280 / 1440 / 1920 (light), 1440 dark, phone 390x844, on a long page.
const { chromium } = require('playwright');
const { openPage, goto, shot, BASE } = require('./common.cjs');
const DOC = process.argv[2] || 'docs/ecosystem-architecture.md';
(async () => {
  const b = await chromium.launch();
  const runs = [[1280, 900, 'light'], [1440, 900, 'light'], [1920, 1080, 'light'], [1440, 900, 'dark'], [390, 844, 'light', true]];
  for (const [w, h, scheme, mobile] of runs) {
    const { ctx, page, log } = await openPage(b, { width: w, height: h, scheme, mobile });
    await goto(page, `${BASE}?path=${encodeURIComponent(DOC)}`);
    await page.waitForSelector('[data-testid=docs-reader-columns]', { timeout: 20000 }).catch(() => {});
    const m = await page.evaluate(() => {
      const c = document.querySelector('[data-testid=docs-reader-columns]');
      if (!c) return null;
      const text = c.querySelector(':scope > div:not([data-testid=docs-toc])');
      const toc = c.querySelector('[data-testid=docs-toc]');
      const nav = document.querySelector('aside, nav');
      return {
        dataToc: c.getAttribute('data-toc'), readerWidth: Math.round(c.getBoundingClientRect().width),
        textWidth: text ? Math.round(text.getBoundingClientRect().width) : null,
        tocTag: toc ? toc.tagName : null, tocWidth: toc ? Math.round(toc.getBoundingClientRect().width) : null,
        tocItems: toc ? toc.querySelectorAll('a').length : 0,
        firstNav: nav ? `${nav.tagName} ${Math.round(nav.getBoundingClientRect().width)}px` : null,
        h1: (document.querySelector('h1') || {}).innerText,
        scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth,
        bg: getComputedStyle(document.body).backgroundColor,
      };
    });
    const s = await shot(page, `layout-${w}-${scheme}`);
    console.log(JSON.stringify({ w, scheme, url: page.url().replace(/^https:\/\/[^/]+/, ''), m, shot: s, console: log.console, failed: log.failed }));
    await ctx.close();
  }
  await b.close();
})().catch((e) => { console.error('ERR', e.message); process.exit(1); });
