// Checks 2-4: full-text search for 'runbook' and opening a hit; the feedback vote on docs/guides/crm-runbook.md (one
// vote, the only write); two table-of-contents clicks (side column at 1920, disclosure at 1440).
const { chromium } = require('playwright');
const { openPage, goto, shot, BASE } = require('./common.cjs');
const which = process.argv[2] || 'search,toc,feedback';
const headingTop = (page, slug) => page.evaluate((s) => {
  const el = document.getElementById('doc-' + s);
  return el ? { top: Math.round(el.getBoundingClientRect().top), text: el.innerText.slice(0, 80), y: Math.round(window.scrollY) } : null;
}, slug);
(async () => {
  const b = await chromium.launch();
  const report = {};
  if (which.includes('search')) {
    const { ctx, page, log } = await openPage(b, { width: 1440, height: 900, scheme: 'light' });
    await goto(page, BASE);
    const box = page.getByRole('textbox', { name: /search the docs|search docs/i }).or(page.locator('input[placeholder^="Search the docs"]')).first();
    await box.fill('runbook');
    const res = await page.waitForResponse((r) => r.url().includes('/docs/search'), { timeout: 20000 }).catch(() => null);
    await page.waitForSelector('[data-testid=docs-search-results]', { timeout: 20000 }).catch(() => {});
    await page.waitForTimeout(800);
    const hits = await page.evaluate(() => {
      const root = document.querySelector('[data-testid=docs-search-results]');
      if (!root) return null;
      const items = [...root.querySelectorAll('[data-testid=docs-search-hit]')];
      return {
        status: (root.querySelector('[role=status]') || {}).innerText,
        count: items.length,
        marks: root.querySelectorAll('mark').length,
        markTexts: [...new Set([...root.querySelectorAll('mark')].map((m) => m.innerText.toLowerCase()))].slice(0, 6),
        first: items.slice(0, 4).map((it) => ({ title: it.querySelector('a').innerText.trim(),
          sections: [...it.querySelectorAll('a')].slice(1).map((a) => ({ href: a.getAttribute('href'), head: (a.querySelector('span') || {}).innerText })) })),
      };
    });
    report.search = { api: res ? `${res.status()} ${res.url().replace(/^https:\/\/[^/]+/, '')}` : null, hits };
    report.search.shot = await shot(page, 'search-runbook-results');
    // open the first section hit that has a heading anchor
    await page.evaluate((w) => { window.__pick = w; }, process.env.PICK || '#doc-');
    const target = await page.evaluate(() => {
      const want = window.__pick || '#doc-';
      const a = [...document.querySelectorAll('[data-testid=docs-search-hit] a')].find((x) => (x.getAttribute('href') || '').includes(want));
      if (!a) return null; a.setAttribute('data-aa-pick', '1'); return a.getAttribute('href');
    });
    report.search.clicked = target;
    if (target) {
      await page.click('[data-aa-pick="1"]');
      await page.waitForTimeout(4500);
      const slug = decodeURIComponent(target.split('#doc-')[1]);
      const wantPath = decodeURIComponent(target.split('path=')[1].split('#')[0].split('&')[0]);
      report.search.landed = { url: decodeURIComponent(page.url().replace(/^https:\/\/[^/]+/, '')), wantPath, slug,
        heading: await headingTop(page, slug),
        ids: await page.evaluate(() => [...document.querySelectorAll('[id^="doc-"]')].slice(0, 4).map((e) => e.tagName + '#' + e.id)),
        tocCurrent: await page.evaluate(() => { const c = document.querySelector('[data-testid=docs-toc] a[aria-current=location]'); return c && c.innerText.trim(); }),
        title: await page.evaluate(() => { const h = document.querySelector('[data-testid=docs-header] h1, [data-testid=docs-header] h2'); return h && h.innerText; }) };
      report.search.landedShot = await shot(page, 'search-runbook-landed');
    }
    report.search.console = log.console; report.search.failed = log.failed;
    await ctx.close();
  }
  if (which.includes('toc')) {
    report.toc = [];
    for (const [w, h, label] of [[1920, 1080, 'side'], [1440, 900, 'top']]) {
      const { ctx, page, log } = await openPage(b, { width: w, height: h, scheme: 'light' });
      await goto(page, `${BASE}?path=${encodeURIComponent('docs/engineering-handbook.md')}`);
      const links = page.locator('[data-testid=docs-toc] a');
      const n = await links.count();
      const picks = label === 'side' ? [6, 20] : [12];
      const r = { w, mode: await page.getAttribute('[data-testid=docs-reader-columns]', 'data-toc'), items: n, clicks: [] };
      for (const i of picks) {
        const a = links.nth(i);
        const href = await a.getAttribute('href');
        const text = (await a.innerText()).trim();
        await a.click();
        await page.waitForTimeout(1800);
        const slug = decodeURIComponent(href.replace('#doc-', ''));
        const ht = await headingTop(page, slug);
        const current = await page.evaluate(() => { const c = document.querySelector('[data-testid=docs-toc] a[aria-current=location]'); return c && c.innerText.trim(); });
        r.clicks.push({ entry: text, href, heading: ht, ariaCurrent: current });
      }
      r.shot = await shot(page, `toc-click-${w}-${label}`);
      r.console = log.console; r.failed = log.failed;
      report.toc.push(r);
      await ctx.close();
    }
  }
  if (which.includes('feedback')) {
    const { ctx, page, log } = await openPage(b, { width: 1440, height: 900, scheme: 'light' });
    await goto(page, `${BASE}?path=${encodeURIComponent('docs/guides/crm-runbook.md')}`);
    const fb = page.locator('[data-testid=docs-feedback]');
    await fb.scrollIntoViewIfNeeded().catch(() => {});
    await page.waitForTimeout(800);
    const r = { present: await fb.count(), question: (await fb.count()) ? (await fb.innerText()).replace(/\s+/g, ' ').trim() : null };
    r.beforeShot = await shot(page, 'feedback-crm-runbook-before');
    const [resp] = await Promise.all([
      page.waitForResponse((x) => x.url().includes('/docs/feedback') && x.request().method() === 'POST', { timeout: 20000 }).catch(() => null),
      page.click('[data-testid=docs-feedback-yes]'),
    ]);
    r.post = resp ? { status: resp.status(), body: (await resp.text().catch(() => '')).slice(0, 200), sent: resp.request().postData() } : null;
    await page.waitForSelector('[data-testid=docs-feedback-done]', { timeout: 15000 }).catch(() => {});
    r.done = await page.evaluate(() => { const d = document.querySelector('[data-testid=docs-feedback-done]'); return d && d.innerText.replace(/\s+/g, ' ').trim(); });
    await page.locator('[data-testid=docs-feedback-done]').scrollIntoViewIfNeeded().catch(() => {});
    r.afterShot = await shot(page, 'feedback-crm-runbook-after');
    r.console = log.console; r.failed = log.failed;
    report.feedback = r;
    await ctx.close();
  }
  console.log(JSON.stringify(report, null, 1));
  await b.close();
})().catch((e) => { console.error('ERR', e.message); process.exit(1); });
