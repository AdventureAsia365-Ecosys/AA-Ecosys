// AA-1135 re-verify (S284) of Platform > Delivery after AA-CIS-App PR #1584 (admin deploy cb775ec7).
// Read-only: opens tabs, pickers and the custom range fields; never clicks Save/Approve/Delete. Apply is only clicked
// when enabled (it changes the URL view, writes nothing).
// Run: cd tools/uat && NODE_PATH=$PWD/node_modules node <this file>
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');

const OUT = '/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-18-S284-session/aa1135-delivery-v2/reverify';
const PRIV = '/home/nghiep/projects/AA-Ecosys/.tmp-session/S284/private-shots';
const BASE = 'https://aa-cis.lumiguides.it.com/admin/platform/delivery';
const HOST_OK = /lumiguides\.it\.com/;
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]+/;
const OLD_WORDING = [/last 4 weeks/i, /last 12 weeks/i, /4 tuần gần nhất/i, /12 tuần gần nhất/i];
const report = { shots: [], pages: [], custom: {}, recent: [] };

// ── colour maths ─────────────────────────────────────────────────────────────────────────────────────────────────
function parseColor(s) {
  if (!s) return null;
  let m = s.match(/^#([0-9a-f]{6})$/i);
  if (m) return [0, 2, 4].map((i) => parseInt(m[1].slice(i, i + 2), 16));
  m = s.match(/^#([0-9a-f]{3})$/i);
  if (m) return [...m[1]].map((c) => parseInt(c + c, 16));
  m = s.match(/rgba?\(([^)]+)\)/);
  if (m) { const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return p.slice(0, 3); }
  return null;
}
function lum(rgb) {
  const c = rgb.map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
function contrast(a, b) { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); }
function lab(rgb) {
  const c = rgb.map((v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
  let x = (c[0] * 0.4124 + c[1] * 0.3576 + c[2] * 0.1805) / 0.95047;
  let y = c[0] * 0.2126 + c[1] * 0.7152 + c[2] * 0.0722;
  let z = (c[0] * 0.0193 + c[1] * 0.1192 + c[2] * 0.9505) / 1.08883;
  const f = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
  [x, y, z] = [f(x), f(y), f(z)];
  return [116 * y - 16, 500 * (x - y), 200 * (y - z)];
}
function dE(a, b) { const p = lab(a), q = lab(b); return Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]); }

// ── in-page probes ───────────────────────────────────────────────────────────────────────────────────────────────
async function probeCharts(page) {
  return page.evaluate(() => {
    const ctx = (el) => { const s = el.closest('[data-testid]'); return s ? s.getAttribute('data-testid') : '?'; };
    const bgOf = (el) => {
      for (let e = el; e; e = e.parentElement) {
        const b = getComputedStyle(e).backgroundColor;
        if (b && b !== 'transparent' && !/rgba\(0, 0, 0, 0\)/.test(b)) return b;
      }
      return getComputedStyle(document.body).backgroundColor;
    };
    return [...document.querySelectorAll('svg.recharts-surface')].filter((s) => s.getBoundingClientRect().width > 0)
      .map((svg) => {
        const box = svg.getBoundingClientRect();
        const wrap = svg.closest('.recharts-wrapper') || svg;
        // clipping ancestor (overflow hidden) box
        let clip = null;
        for (let e = wrap.parentElement; e && e !== document.body; e = e.parentElement) {
          const o = getComputedStyle(e);
          if (/(hidden|clip|auto|scroll)/.test(o.overflowX)) { clip = e.getBoundingClientRect(); break; }
        }
        const cut = [];
        for (const t of svg.querySelectorAll('.recharts-yAxis-tick-labels text, .recharts-yAxis text')) {
          const r = t.getBoundingClientRect(); if (!r.width) continue;
          if (r.left < box.left - 0.5 || r.right > box.right + 0.5 || (clip && r.left < clip.left - 0.5))
            cut.push(`y "${t.textContent}" left=${r.left.toFixed(1)} svgLeft=${box.left.toFixed(1)}`);
        }
        for (const t of svg.querySelectorAll('.recharts-xAxis-tick-labels text, .recharts-xAxis text')) {
          const r = t.getBoundingClientRect(); if (!r.width) continue;
          if (r.bottom > box.bottom + 0.5 || r.left < box.left - 0.5 || r.right > box.right + 2)
            cut.push(`x "${t.textContent}" l=${r.left.toFixed(0)} r=${r.right.toFixed(0)} b=${r.bottom.toFixed(0)} svg=${box.left.toFixed(0)}-${box.right.toFixed(0)}/${box.bottom.toFixed(0)}`);
        }
        const yTicks = [...svg.querySelectorAll('.recharts-yAxis-tick-labels text, .recharts-yAxis text')].map((t) => t.textContent);
        const lines = [...svg.querySelectorAll('.recharts-line-curve')].map((p) => p.getAttribute('stroke'));
        const bars = [...svg.querySelectorAll('.recharts-bar')].map((g) => {
          const r = g.querySelector('.recharts-bar-rectangle path, .recharts-rectangle');
          return r ? (r.getAttribute('fill') || getComputedStyle(r).fill) : null;
        }).filter(Boolean);
        const cells = [...new Set([...svg.querySelectorAll('.recharts-bar-rectangle path, .recharts-rectangle')]
          .map((r) => r.getAttribute('fill')).filter(Boolean))];
        const legend = [...(wrap.querySelectorAll('.recharts-legend-item') || [])].map((li) => {
          const sw = li.querySelector('path, line, rect');
          return `${li.textContent.trim()}=${sw ? (sw.getAttribute('fill') !== 'none' ? sw.getAttribute('fill') : sw.getAttribute('stroke')) : '?'}`;
        });
        return { ctx: ctx(svg), w: Math.round(box.width), h: Math.round(box.height), cut, yTicks, lines, bars, cells,
          legend, bg: bgOf(wrap) };
      });
  });
}

function colourVerdict(charts) {
  const out = [];
  for (const c of charts) {
    const series = c.lines.length > 1 ? c.lines : (c.bars.length > 1 ? c.bars : []);
    if (series.length < 2) continue;
    const rgbs = series.map(parseColor);
    const bg = parseColor(c.bg);
    let minDE = Infinity, pair = '';
    for (let i = 0; i < rgbs.length; i++) for (let j = i + 1; j < rgbs.length; j++) {
      if (!rgbs[i] || !rgbs[j]) continue;
      const d = dE(rgbs[i], rgbs[j]); if (d < minDE) { minDE = d; pair = `${series[i]} vs ${series[j]}`; }
    }
    const minCr = bg ? Math.min(...rgbs.filter(Boolean).map((x) => contrast(x, bg))) : null;
    const dup = new Set(series).size !== series.length;
    out.push({ ctx: c.ctx, kind: c.lines.length > 1 ? 'lines' : 'bars', series, legend: c.legend,
      distinct: !dup, minDeltaE: +minDE.toFixed(1), closestPair: pair, minContrastVsBg: minCr && +minCr.toFixed(2), bg: c.bg });
  }
  return out;
}

async function wording(page) {
  return page.evaluate(() => {
    const desc = (id) => { const s = document.querySelector(`[data-testid="${id}"]`); return s ? s.innerText.split('\n').slice(0, 3).join(' | ') : null; };
    return { intro: desc('delivery-queue-intro'), ci: desc('delivery-ci'), failed: desc('delivery-failed'),
      recent: desc('queue-recent'), body: document.body.innerText };
  });
}

// ── run ──────────────────────────────────────────────────────────────────────────────────────────────────────────
(async () => {
  const { file: state } = await ensureState('cis-admin');
  const browser = await chromium.launch();

  async function open(name, url, { scheme = 'light', w = 1440, h = 900, full = false, shot = true, clip = null, act = null, expectWhen = null, focus = null, elem = null } = {}) {
    const mobile = w < 600;
    const ctx = await browser.newContext({ storageState: state, viewport: { width: w, height: h }, colorScheme: scheme,
      isMobile: mobile, hasTouch: mobile });
    const page = await ctx.newPage();
    await page.addInitScript((s) => { try { localStorage.setItem('theme', s); } catch (e) {} }, scheme);
    const cons = [], net = [], api = [];
    page.on('console', (m) => { if (m.type() === 'error') cons.push(m.text().slice(0, 240)); });
    page.on('pageerror', (e) => cons.push('pageerror: ' + String(e).slice(0, 240)));
    page.on('requestfailed', (r) => { if (HOST_OK.test(r.url())) net.push(`FAILED ${r.failure()?.errorText} ${r.url().slice(0, 160)}`); });
    page.on('response', async (r) => {
      const u = r.url();
      if (r.status() >= 400 && HOST_OK.test(u)) net.push(`${r.status()} ${r.request().method()} ${u.slice(0, 180)}`);
      if (/delivery/.test(u) && /json/.test(r.headers()['content-type'] || '')) {
        try { api.push({ url: u, status: r.status(), body: await r.json() }); } catch (e) {}
      }
    });
    await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(3500);
    const login = /\/login|signin|auth\./.test(page.url()) || !(await page.getByTestId('delivery-range').count());
    let extra = null;
    if (!login && act) extra = await act(page);
    if (!login && extra === null) await page.waitForTimeout(500);
    const charts = login ? [] : await probeCharts(page);
    const words = login ? {} : await wording(page);
    let file = null;
    if (shot) {
      file = path.join(OUT, `${name}.png`);
      const opts = { path: file, fullPage: full && !clip };
      if (clip) opts.clip = clip;
      const target = elem ? page.getByTestId(elem).first() : null;
      if (focus) {
        await page.getByTestId(focus).first().evaluate((el) => el.scrollIntoView({ block: 'start' })).catch(() => {});
        await page.waitForTimeout(800);
      }
      const snap = (o) => (target ? target.screenshot({ ...o, fullPage: undefined, clip: undefined }) : page.screenshot(o));
      await snap(opts);
      if (fs.statSync(file).size > 400 * 1024) {
        fs.unlinkSync(file); file = path.join(OUT, `${name}.jpg`);
        await snap({ ...opts, path: file, type: 'jpeg', quality: 70 });
      }
      if (EMAIL.test(words.body || '')) {
        const dest = path.join(PRIV, path.basename(file)); fs.renameSync(file, dest); file = 'PRIVATE:' + dest;
      }
      report.shots.push({ name: path.basename(file), kb: Math.round(fs.statSync(file.replace('PRIVATE:', '')).size / 1024) });
    }
    const old = OLD_WORDING.filter((re) => re.test(words.body || '')).map(String);
    const rec = { name, url: page.url(), scheme, login, file: file && path.basename(file),
      axisCuts: charts.flatMap((c) => c.cut.map((x) => `${c.ctx}: ${x}`)), chartCount: charts.length,
      yTicks: charts.map((c) => `${c.ctx}[${c.yTicks.join(',')}]`),
      colours: colourVerdict(charts), oldWording: old,
      wording: { intro: words.intro, ci: words.ci, failed: words.failed, recent: words.recent },
      expectWhen, whenOk: expectWhen ? ['intro', 'ci', 'failed', 'recent'].filter((k) => words[k]).every((k) => words[k].includes(expectWhen)) : null,
      emailInText: EMAIL.test(words.body || ''), console: cons, network: net, extra };
    report.pages.push(rec);
    await ctx.close();
    return { rec, api };
  }

  // 1-2 overview (DORA trend colours, cards), default range
  await open('overview-trend-1440-light', BASE, { scheme: 'light', elem: 'delivery-trend' });
  await open('overview-trend-1440-dark', BASE, { scheme: 'dark', elem: 'delivery-trend' });

  // 3-4 custom range picker: geometry + Apply hit test (+ click only when enabled)
  const customAct = async (page) => {
    await page.getByTestId('delivery-range-picker').getByRole('radio', { name: 'Custom' }).click();
    await page.waitForTimeout(800);
    const apply = page.getByTestId('delivery-range-apply').getByRole('button');
    const geo = await page.locator('[data-testid="delivery-range"] [data-kit-field="date"]').evaluateAll((els) => els.map((w) => {
      const i = w.querySelector('input[type="text"]'); const a = w.getBoundingClientRect(); const b = i.getBoundingClientRect();
      return { label: i.getAttribute('aria-label'), value: i.value, wrap: [a.left, a.right].map(Math.round), box: [b.left, b.right].map(Math.round) };
    }));
    const ab = await apply.boundingBox();
    const hit = await page.evaluate(({ x, y }) => {
      const el = document.elementFromPoint(x, y); const host = document.querySelector('[data-testid="delivery-range-apply"]');
      return { inside: !!el && !!host && host.contains(el), tag: el && el.tagName, label: el && el.getAttribute('aria-label') };
    }, { x: ab.x + ab.width / 2, y: ab.y + ab.height / 2 });
    const enabled = await apply.isEnabled();
    const notes = await page.getByTestId('delivery-range').innerText();
    const urlBefore = page.url();
    let urlAfter = null, headAfter = null;
    if (enabled) {
      await apply.click({ timeout: 10000 });
      await page.waitForTimeout(3000);
      urlAfter = page.url();
      headAfter = await page.getByTestId('delivery-range').innerText();
    }
    return { geo, applyBox: [Math.round(ab.x), Math.round(ab.x + ab.width)], hit, enabled, notes, urlBefore, urlAfter, headAfter };
  };
  const rangeClip = { x: 0, y: 0, width: 1440, height: 900 };
  const c1 = await open('custom-picker-1440-light', BASE, { scheme: 'light', full: false, clip: rangeClip, act: customAct });
  report.custom.light = c1.rec.extra;
  report.custom.meta = c1.api.map((a) => ({ url: a.url.replace(/^https:\/\/[^/]+/, ''), status: a.status,
    range: a.body && (a.body.range || a.body.meta || a.body.range_meta) })).slice(0, 4);
  const c2 = await open('custom-picker-1440-dark', BASE, { scheme: 'dark', full: false, clip: rangeClip, act: customAct });
  report.custom.dark = c2.rec.extra;

  // custom range given in the URL (text only): what the wording and the API say
  const lastDay = (() => { for (const a of c1.api) { const m = JSON.stringify(a.body || {}).match(/"last_day":"(\d{4}-\d{2}-\d{2})"/); if (m) return m[1]; } return '2026-11-17'; })();
  const shift = (d, n) => new Date(Date.parse(d + 'T00:00:00Z') + n * 864e5).toISOString().slice(0, 10);
  const cf = shift(lastDay, -9), ct = shift(lastDay, -3);
  const cu = await open('custom-url-mq-cis', `${BASE}?app=merge-queue&repo=cis&range=custom&from=${cf}&to=${ct}`, { shot: false });
  report.custom.urlRange = { from: cf, to: ct, wording: cu.rec.wording,
    rangeText: (await (async () => null)()), api: cu.api.map((a) => ({ url: a.url.replace(/^https:\/\/[^/]+/, ''), status: a.status,
      note: a.status >= 400 ? JSON.stringify(a.body).slice(0, 300) : undefined })) };
  const cu2 = await open('custom-url-cis', `${BASE}?app=cis&range=custom&from=${cf}&to=${ct}`, { shot: false });
  report.custom.urlRangeApp = { wording: cu2.rec.wording, api: cu2.api.map((a) => ({ url: a.url.replace(/^https:\/\/[^/]+/, ''), status: a.status,
    note: a.status >= 400 ? JSON.stringify(a.body).slice(0, 300) : undefined })) };

  // recent entries: per repo and range, from the API answer the tab used
  const recentOf = (api, repo, range) => {
    for (const a of api) {
      const apps = a.body && a.body.apps; if (!Array.isArray(apps)) continue;
      for (const ap of apps) {
        if (!ap.queue || !Array.isArray(ap.queue.recent)) continue;
        if (repo && ap.id !== repo) continue;
        const r = ap.queue.recent; const left = r.map((e) => e.left_at).filter(Boolean).sort();
        const win = ap.window || ap.queue.window || {};
        report.recent.push({ repo: ap.id, range, n: r.length, inQueue: r.filter((e) => !e.left_at).length,
          window: [win.start, win.end].join('..'), oldestLeft: left[0], newestLeft: left[left.length - 1],
          outside: left.filter((d) => (win.start && d < win.start) || (win.end && d.slice(0, 10) > win.end.slice(0, 10))).length });
      }
    }
  };

  // 5-7 merge queue (histogram / throughput axes, recent list)
  const mq1 = await open('mq-cis-90d-charts-1440-light', `${BASE}?app=merge-queue&repo=cis&range=90d`, { scheme: 'light', focus: 'queue-histogram', expectWhen: 'over the last 90 days' });
  recentOf(mq1.api, 'cis', '90d');
  await open('mq-cis-90d-throughput-1440-dark', `${BASE}?app=merge-queue&repo=cis&range=90d`, { scheme: 'dark', focus: 'queue-throughput', expectWhen: 'over the last 90 days' });
  await open('mq-cis-90d-recent-1440-light', `${BASE}?app=merge-queue&repo=cis&range=90d`, { scheme: 'light', focus: 'queue-recent', expectWhen: 'over the last 90 days' });
  const mq3 = await open('mq-booking-7d-recent-1440-dark', `${BASE}?app=merge-queue&repo=booking&range=7d`, { scheme: 'dark', focus: 'queue-recent', expectWhen: 'over the last 7 days' });
  recentOf(mq3.api, 'booking', '7d');
  for (const [repo, range] of [['partner', '28d'], ['booking', '90d'], ['cis', '7d']]) {
    const r = await open(`mq-${repo}-${range}`, `${BASE}?app=merge-queue&repo=${repo}&range=${range}`, { shot: false, expectWhen: `over the last ${range.slice(0, -1)} days` });
    recentOf(r.api, repo, range);
  }
  recentOf(cu.api, 'cis', `custom ${cf}..${ct}`);

  // 8-9 git map
  await open('git-map-cis-weekly-1440-light', `${BASE}?app=git-map&repo=cis`, { scheme: 'light', focus: 'git-weekly' });
  await open('git-map-cis-weekly-1440-dark', `${BASE}?app=git-map&repo=cis`, { scheme: 'dark', focus: 'git-weekly' });

  // 10-15 app tabs (CI health / failed deploys wording, segment colours, trend axis)
  await open('cis-trend-1440-light', `${BASE}?app=cis`, { scheme: 'light', focus: 'delivery-app-trend', expectWhen: 'over the last 28 days' });
  await open('cis-segments-1440-dark', `${BASE}?app=cis`, { scheme: 'dark', focus: 'delivery-segments', expectWhen: 'over the last 28 days' });
  await open('booking-90d-ci-1440-light', `${BASE}?app=booking&range=90d`, { scheme: 'light', focus: 'delivery-ci', expectWhen: 'over the last 90 days' });
  await open('partner-7d-trend-1440-dark', `${BASE}?app=partner&range=7d`, { scheme: 'dark', focus: 'delivery-app-trend', expectWhen: 'over the last 7 days' });
  await open('tripplanner-segments-1440-light', `${BASE}?app=tripplanner`, { scheme: 'light', focus: 'delivery-segments', expectWhen: 'over the last 28 days' });
  await open('infra', `${BASE}?app=infra`, { shot: false, expectWhen: 'over the last 28 days' });
  await open('root-tab', `${BASE}?app=root`, { shot: false, expectWhen: 'over the last 28 days' });

  // 16 mobile
  const mob = await open('custom-picker-390-light', BASE, { scheme: 'light', w: 390, h: 844, focus: 'delivery-range', act: customAct });
  report.custom.mobile = mob.rec.extra;

  await browser.close();
  fs.writeFileSync(path.join(path.dirname(__filename), 'reverify-result.json'), JSON.stringify(report, null, 1));
  console.log(JSON.stringify(report, null, 1));
})();
