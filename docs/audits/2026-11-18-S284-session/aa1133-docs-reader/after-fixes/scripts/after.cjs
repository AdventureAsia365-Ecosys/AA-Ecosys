// AA-1133 after-fixes live check (CIS PR #1588, API + admin at 701be528). Read-only: no vote, no save.
// (1) manifest can_feedback=false for the E2E session + no feedback widget; (2) side TOC scroll-spy at 1920;
// (3) search 'runbook' at 1440: count bar hidden, EN above VI, no empty-snippet rows, section hit lands on heading.
const { chromium } = require('playwright');
const { openPage, goto, shot, BASE } = require('./common.cjs');
const which = process.argv[2] || 'feedback,toc,search';
const HANDBOOK = `${BASE}?path=${encodeURIComponent('docs/engineering-handbook.md')}`;
const curToc = (page) => page.evaluate(() => {
  const c = document.querySelector('[data-testid=docs-toc] a[aria-current]');
  return c && c.innerText.trim();
});
const headingTop = (page, slug) => page.evaluate((s) => {
  const el = document.getElementById('doc-' + s);
  return el ? { top: Math.round(el.getBoundingClientRect().top), text: el.innerText.slice(0, 80), y: Math.round(window.scrollY) } : null;
}, slug);

(async () => {
  const b = await chromium.launch();
  const report = {};

  if (which.includes('feedback')) {
    const { ctx, page, log } = await openPage(b, { width: 1440, height: 900, scheme: 'light' });
    let manifestSeen = null;
    page.on('response', async (r) => {
      if (r.url().includes('/admin/docs/manifest') && r.request().method() === 'GET') {
        try { const j = await r.json(); manifestSeen = { status: r.status(), url: r.url().replace(/^https:\/\/[^/]+/, ''), can_feedback: j.can_feedback }; } catch (e) {}
      }
    });
    await goto(page, HANDBOOK);
    const direct = await page.evaluate(async () => {
      const r = await fetch('/api/admin/docs/manifest', { credentials: 'include' });
      let j = null; try { j = await r.json(); } catch (e) {}
      return { status: r.status, has_field: j ? Object.prototype.hasOwnProperty.call(j, 'can_feedback') : null, can_feedback: j && j.can_feedback };
    });
    await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
    await page.waitForTimeout(1500);
    const r = { manifestDirect: direct, manifestByPage: manifestSeen,
      feedbackEls: await page.locator('[data-testid=docs-feedback]').count(),
      helpfulText: await page.evaluate(() => /was this page helpful/i.test(document.body.innerText)) };
    r.shot = await shot(page, 'feedback-e2e-hidden');
    r.console = log.console; r.failed = log.failed;
    report.feedback = r;
    await ctx.close();
  }

  if (which.includes('toc')) {
    const { ctx, page, log } = await openPage(b, { width: 1920, height: 1080, scheme: 'light' });
    await goto(page, HANDBOOK);
    const mode = await page.getAttribute('[data-testid=docs-reader-columns]', 'data-toc');
    const all = await page.locator('[data-testid=docs-toc] a').allInnerTexts();
    const texts = all.map((t) => t.trim());
    const pickIdx = ['2.1', '4.8', '7.3'].map((p, k) => {
      const i = texts.findIndex((t) => t.startsWith(p + ' ') || t.startsWith(p + '.') || t.startsWith(p));
      return i >= 0 ? i : [6, 20, 40][k];
    });
    const r = { mode, items: texts.length, clicks: [] };
    for (const i of pickIdx) {
      const a = page.locator('[data-testid=docs-toc] a').nth(i);
      const text = (await a.innerText()).trim();
      const href = await a.getAttribute('href');
      await a.click();
      await page.waitForTimeout(1800); const at18 = await curToc(page);
      await page.waitForTimeout(3000); const at48 = await curToc(page);
      const slug = decodeURIComponent((href || '').split('#doc-')[1] || '');
      r.clicks.push({ clicked: text, href, at1_8s: at18, at4_8s: at48, pass: at18 === text && at48 === text,
        urlHash: decodeURIComponent(new URL(page.url()).hash), heading: slug ? await headingTop(page, slug) : null });
    }
    r.shot = await shot(page, 'toc-click-1920-side-after');
    r.console = log.console; r.failed = log.failed;
    report.toc = r;
    await ctx.close();
  }

  if (which.includes('search')) {
    const { ctx, page, log } = await openPage(b, { width: 1440, height: 900, scheme: 'light' });
    await goto(page, BASE);
    const box = page.locator('input[placeholder^="Search the docs"]').or(page.getByRole('textbox', { name: /search the docs|search docs/i })).first();
    await box.fill('runbook');
    const res = await page.waitForResponse((x) => x.url().includes('/docs/search'), { timeout: 20000 }).catch(() => null);
    await page.waitForSelector('[data-testid=docs-search-hit]', { timeout: 20000 }).catch(() => {});
    await page.waitForTimeout(1000);
    const view = await page.evaluate(() => {
      const vis = (el) => { const s = getComputedStyle(el); const r = el.getBoundingClientRect(); return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0; };
      // visible element whose own text is exactly "N of M pages" (the list page-count bar)
      const countBars = [...document.querySelectorAll('span,div')].filter((e) => /^\d+ of \d+ pages$/.test((e.innerText || '').trim()) && vis(e)).map((e) => e.innerText.trim());
      const countBarsHidden = [...document.querySelectorAll('span')].filter((e) => /^\d+ of \d+ pages$/.test((e.textContent || '').trim()) && !vis(e)).map((e) => e.textContent.trim());
      const root = document.querySelector('[data-testid=docs-search-results]');
      const hits = [...document.querySelectorAll('[data-testid=docs-search-hit]')].map((it, idx) => {
        const as = [...it.querySelectorAll(':scope > a')];
        const href = as[0].getAttribute('href') || '';
        const p = decodeURIComponent((href.split('path=')[1] || '').split('#')[0].split('&')[0]);
        const sections = as.slice(1).map((a) => {
          const spans = [...a.children];
          return { href: a.getAttribute('href'), head: spans[0] && spans[0].innerText.trim(), snippet: spans[1] ? spans[1].innerText.trim().slice(0, 80) : '' };
        });
        return { idx, title: as[0].innerText.trim(), path: p, sections };
      });
      return { status: root && (root.querySelector('[role=status]') || {}).innerText, countBars, countBarsHidden, hits };
    });
    const idxOf = Object.fromEntries(view.hits.map((h) => [h.path, h.idx]));
    const pairs = view.hits.filter((h) => /\.vi\.md$/.test(h.path)).map((h) => {
      const en = h.path.replace(/\.vi\.md$/, '.md');
      return { vi: h.path, viIdx: h.idx, en, enIdx: idxOf[en] ?? null, ok: idxOf[en] === undefined ? 'no-EN-hit' : idxOf[en] < h.idx };
    });
    const emptyRows = view.hits.flatMap((h) => h.sections.filter((s) => !s.snippet).map((s) => ({ path: h.path, head: s.head })));
    report.search = { api: res ? `${res.status()} ${res.url().replace(/^https:\/\/[^/]+/, '')}` : null,
      status: view.status, visibleCountBars: view.countBars, hiddenCountBars: view.countBarsHidden,
      hitCount: view.hits.length, order: view.hits.map((h) => h.path), pairs, emptyRows,
      sectionRows: view.hits.reduce((n, h) => n + h.sections.length, 0) };
    report.search.shot = await shot(page, 'search-runbook-results-after');
    // PICK_RE (env): the heading text of the section hit to open; default = the first section hit.
    const target = await page.evaluate((re) => {
      const rx = re ? new RegExp(re) : null;
      const a = [...document.querySelectorAll('[data-testid=docs-search-hit] > a')].find((x) => (x.getAttribute('href') || '').includes('#doc-')
        && (!rx || rx.test(((x.children[0] || {}).innerText || '').trim())));
      if (!a) return null; a.setAttribute('data-aa-pick', '1'); return a.getAttribute('href');
    }, process.env.PICK_RE || '');
    report.search.clicked = target;
    if (target) {
      await page.click('[data-aa-pick="1"]');
      await page.waitForTimeout(4500);
      const slug = decodeURIComponent(target.split('#doc-')[1]);
      const u = new URL(page.url());
      report.search.landed = { path: u.searchParams.get('path'), hash: decodeURIComponent(u.hash), wantSlug: slug,
        hashOk: decodeURIComponent(u.hash) === '#doc-' + slug, heading: await headingTop(page, slug), tocCurrent: await curToc(page) };
      report.search.landedShot = await shot(page, 'search-runbook-landed-after');
    }
    report.search.console = log.console; report.search.failed = log.failed;
    await ctx.close();
  }
  console.log(JSON.stringify(report, null, 1));
  await b.close();
})().catch((e) => { console.error('ERR', e.message); process.exit(1); });
