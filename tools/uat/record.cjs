// UAT recorder (skill aa-uat-video). One scenario = one user story = one video = one regression test.
//   node record.cjs <scenario.cjs> --captions   -> work/<id>/captions.json (input for tts.py)
//   node record.cjs <scenario.cjs>              -> work/<id>/video.webm + timeline.json + result.json
//   node record.cjs <scenario.cjs> --fast       -> work/<id>/result.json only (no video, no holds; CI / regression)
// UAT mode holds each step at least as long as its longest narration clip (work/<id>/durations.json from tts.py),
// so the voice-over fits without stretching audio. Assertions run inside each step: a failing assertion stops the
// run, marks the step FAIL and still keeps the video as evidence. Exit: 0 PASS, 2 a step FAILed, 1 crash.
// Signed-in scenarios: UAT_STORAGE_STATE=<file> (or scenario.storageState) saved by an unrecorded sign-in run;
// the sign-in screen itself is never recorded. scenario.mask = [CSS selectors] blurs secrets on screen;
// scenario.blurText = [regex sources] blurs any element whose own text matches (e.g. internal ids in old test data).
// Optional scenario hooks: prepare() runs before the browser starts (unrecorded sign-in, e.g. lib/crm-signin.cjs; it
// may set scenario.storageState); fastOnly: true refuses a recorded run (data prep / cleanup scenarios); scenario.meta
// (filled by steps, e.g. the app git_sha at the start and end) is copied into result.json.
// Masks are on before the first paint; a step that shows a secret calls h.assertMasked([selectors]) (each selector on
// screen and blurred). scenario.isMobile / hasTouch make a phone take a real mobile context; scenario.title_vi goes to
// result.json for the Vietnamese chapter list of longform.py. Errors and URLs written to timeline.json / result.json
// have link tokens (path or query segments of 30+ characters, uuids excepted) replaced by <redacted>.
// Dry-run guards (AA-1009, tools/uat/dryrun.cjs): scenario.readOnly aborts every request that is not GET / HEAD / OPTIONS
// (scenario.allowWrites = [regex sources on the URL] lets named ones through) and lists them in result.json
// blocked_writes; scenario.blockUrls = [regex sources] aborts any matching request (e.g. paid model paths) and lists it
// in blocked_urls (env UAT_READ_ONLY=1 / UAT_BLOCK_URLS=<JSON list> add both to any scenario). Telemetry beacons, the
// staff session keep-alive (POST /api/auth/refresh) and third-party posts are aborted but listed in blocked_other
// (lib/net-guard.cjs); a read-only run also refuses non-read page.request / context.request calls (blocked_writes) and
// closes every WebSocket (blocked_other). UAT_HEADED=1 or scenario.headed opens a visible Chromium (WSLg DISPLAY), for pages a headless browser
// cannot pass. scenario.identity (public, cis-admin, booking, studio, crm) is copied into result.json.
// Setup once: bash tools/uat/setup.sh (pins @playwright/test). One Chromium, closed at the end.
const fs = require('fs');
const path = require('path');
const { chromium, expect } = require('@playwright/test');

const MIN_HOLD_MS = 2500;
// Link tokens travel in URL path segments and query values: never write one to timeline.json / result.json / logs.
// (A uuid is an object id, not a credential: kept for debugging.)
// Same rule as the dry-run report (lib/dryrun-core.cjs): also masks AWS ARNs and 12-digit account numbers.
const { redact } = require('./lib/dryrun-core.cjs');
const TAIL_PAD_MS = 600;
// Which aborted request is a write to the app (fails a read-only scenario) and which is telemetry / session upkeep /
// third party (listed apart): lib/net-guard.cjs.
const guard = require('./lib/net-guard.cjs');

async function main() {
  const scenarioPath = path.resolve(process.argv[2]);
  const captionsOnly = process.argv.includes('--captions');
  const fast = process.argv.includes('--fast');
  const sc = require(scenarioPath);
  const work = path.join(__dirname, 'work', sc.id);
  fs.mkdirSync(work, { recursive: true });

  if (captionsOnly) {
    const captions = sc.steps.map((s, i) => ({ n: i + 1, ...s.caption }));
    fs.writeFileSync(path.join(work, 'captions.json'), JSON.stringify({ id: sc.id, title: sc.title, captions }, null, 2));
    console.log(`captions: ${captions.length} -> ${path.join(work, 'captions.json')}`);
    return;
  }

  if (sc.fastOnly && !fast) throw new Error(`${sc.id} is a data step: run it with --fast only`);
  // The narration was made from captions.json: a recorded take whose steps say something else (scenario edited, or
  // steps chosen from run state that changed since) would play the wrong voice-over.
  const cPath = path.join(work, 'captions.json');
  if (!fast && fs.existsSync(cPath)) {
    const made = JSON.parse(fs.readFileSync(cPath, 'utf8')).captions.map((c) => `${c.en}\n${c.vi}`).join('\n');
    const now = sc.steps.map((s) => `${s.caption.en}\n${s.caption.vi}`).join('\n');
    if (made !== now) throw new Error(`${sc.id}: the steps changed since --captions; make the captions and the narration again`);
  }
  // Failure shots of an earlier run are not evidence of this one.
  for (const f of fs.readdirSync(work)) if (/^fail-step-\d+\.png$/.test(f)) fs.rmSync(path.join(work, f));
  if (typeof sc.prepare === 'function') await sc.prepare({ fast });

  let durations = {};
  const dPath = path.join(work, 'durations.json');
  if (!fast && fs.existsSync(dPath)) durations = JSON.parse(fs.readFileSync(dPath, 'utf8'));

  const storageState = process.env.UAT_STORAGE_STATE || sc.storageState;
  const headed = process.env.UAT_HEADED === '1' || !!sc.headed;
  if (headed && !process.env.DISPLAY && !process.env.WAYLAND_DISPLAY) throw new Error(`${sc.id}: a headed run needs a display (WSLg DISPLAY)`);
  const browser = await chromium.launch({ headless: !headed, slowMo: fast ? 0 : 60 });
  const context = await browser.newContext({
    viewport: sc.viewport,
    deviceScaleFactor: 1,
    // A phone scenario sets isMobile + hasTouch: mobile user agent behaviour, meta viewport and touch events.
    ...(sc.isMobile ? { isMobile: true } : {}),
    ...(sc.hasTouch ? { hasTouch: true } : {}),
    ...(fast ? {} : { recordVideo: { dir: work, size: sc.viewport } }),
    ...(storageState ? { storageState } : {}),
    reducedMotion: 'no-preference',
    locale: 'en-US',
  });
  // Network guards before the first page: a read-only scenario never writes, a blocked URL never leaves the browser.
  const blockedWrites = [];
  const blockedUrls = [];
  const blockedOther = [];
  // The dry-run runner forces both for every scenario it starts: UAT_READ_ONLY=1, UAT_BLOCK_URLS=<JSON regex list>.
  const readOnly = !!sc.readOnly || process.env.UAT_READ_ONLY === '1';
  const blockSrc = [...(sc.blockUrls || []), ...JSON.parse(process.env.UAT_BLOCK_URLS || '[]')];
  if (readOnly || blockSrc.length) {
    const allow = (sc.allowWrites || []).map((x) => new RegExp(x));
    const block = blockSrc.map((x) => new RegExp(x));
    await context.route('**/*', (route) => {
      const req = route.request();
      const url = req.url();
      const where = () => { const u = new URL(url); return `${u.host}${u.pathname}`; };
      if (block.some((r) => r.test(url))) {
        blockedUrls.push(redact(`${req.method()} ${where()}`));
        return route.abort('blockedbyclient');
      }
      if (readOnly && !guard.isRead(req.method()) && !allow.some((r) => r.test(url))) {
        // Aborted either way; only a write to the app itself fails the scenario. Telemetry beacons (map events, error
        // reports, Vercel analytics), the staff session keep-alive and third-party posts are listed apart.
        (guard.classify(url, sc.baseURL) === 'write' ? blockedWrites : blockedOther).push(redact(`${req.method()} ${where()}`));
        return route.abort('blockedbyclient');
      }
      return route.continue();
    });
  }
  if (readOnly) {
    // context.route() never sees two other ways out of the browser context: Node-side APIRequestContext calls
    // (page.request / context.request, one shared object) and WebSockets. No app opens a WebSocket today, so every one
    // is closed and listed; a scenario's own non-read request call is refused and counts as a write.
    const allow = (sc.allowWrites || []).map((x) => new RegExp(x));
    guard.guardRequestContext(context.request, { allow,
      onBlocked: (method, url) => {
        let w = url;
        try { const u = new URL(url); w = `${u.host}${u.pathname}`; } catch { /* keep as is */ }
        blockedWrites.push(redact(`${method} ${w} (request API)`));
      } });
    await context.routeWebSocket(/.*/, (ws) => {
      let w = ws.url();
      try { const u = new URL(w); w = `${u.host}${u.pathname}`; } catch { /* keep as is */ }
      blockedOther.push(redact(`WS ${w}`));
      ws.close();
    });
  }
  if (!fast) await context.addInitScript({ path: path.join(__dirname, 'lib', 'overlay.js') });
  // Masks go on before the first paint: the init script runs as soon as the document exists, and a server-rendered
  // page can paint before DOMContentLoaded (a mask added only then leaves a few unmasked frames).
  if (sc.mask && sc.mask.length) {
    await context.addInitScript((sels) => {
      const css = `${sels.join(',')}{filter:blur(10px)!important}`;
      const ensure = () => {
        const root = document.documentElement;
        if (!root || document.getElementById('uat-mask')) return !!root;
        const s = document.createElement('style');
        s.id = 'uat-mask';
        s.textContent = css;
        root.appendChild(s);
        return true;
      };
      ensure();
      // The document element may not exist yet, and a hydration may drop the style: put it back each time.
      new MutationObserver(ensure).observe(document, { childList: true, subtree: true });
    }, sc.mask);
  }
  if (sc.blurText && sc.blurText.length) {
    await context.addInitScript((srcs) => {
      const res = srcs.map((x) => new RegExp(x));
      const hit = (n) => n.parentElement && res.some((r) => r.test(n.nodeValue));
      const scan = (root) => {
        if (!root) return;
        if (root.nodeType === 3) {
          if (hit(root)) root.parentElement.style.setProperty('filter', 'blur(10px)', 'important');
          return;
        }
        const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        for (let n = w.nextNode(); n; n = w.nextNode()) {
          if (hit(n)) n.parentElement.style.setProperty('filter', 'blur(10px)', 'important');
        }
      };
      // Observe the document from the start (parser-inserted nodes included), not only after DOMContentLoaded.
      new MutationObserver((ms) => {
        for (const m of ms) {
          if (m.type === 'characterData') scan(m.target);
          for (const a of m.addedNodes) scan(a);
        }
      }).observe(document, { childList: true, subtree: true, characterData: true });
      scan(document.documentElement);
    }, sc.blurText);
  }
  const page = await context.newPage();
  // The video starts at the first painted frame, and about:blank paints none: without this, every second the first
  // step spends loading its page is cut from the start of the video while timeline.json still counts it, so the
  // narration and the subtitles lag the picture by that much (2-4 s seen, S261). Paint a plain frame, then start t0.
  if (!fast) {
    await page.setContent('<html><body style="margin:0;background:#f8f6f2"></body></html>');
    await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
  }
  const t0 = Date.now();
  let cursor = { x: sc.viewport.width / 2, y: sc.viewport.height / 2 };
  const wait = (ms) => page.waitForTimeout(fast ? Math.min(ms, 150) : ms);

  const h = {
    expect,
    fast,
    baseURL: sc.baseURL,
    pause: (ms) => wait(ms),
    goto: async (p) => {
      await page.goto(new URL(p, sc.baseURL).toString(), { waitUntil: 'load' });
      for (let i = 0; i < 20 && /Security Checkpoint/i.test(await page.title()); i++) await page.waitForTimeout(1000);
      if (/Security Checkpoint/i.test(await page.title())) throw new Error('VERCEL_CHECKPOINT: the host challenged this browser (VPN/datacenter IP?)');
      await page.mouse.move(cursor.x, cursor.y);
    },
    moveTo: async (loc) => {
      await loc.scrollIntoViewIfNeeded();
      const b = await loc.boundingBox();
      if (!b) throw new Error('element has no box');
      const to = { x: b.x + Math.min(b.width / 2, 120), y: b.y + b.height / 2 };
      await page.mouse.move(to.x, to.y, { steps: fast ? 1 : 30 });
      cursor = to;
    },
    hover: async (loc) => { await h.moveTo(loc); await wait(500); },
    click: async (loc) => {
      await h.moveTo(loc);
      await wait(350);
      await page.mouse.down();
      await wait(120);
      await page.mouse.up();
    },
    // scenario.scrollBlock = 'center' for apps with a sticky top bar (a 'start' scroll hides the target under it).
    scrollTo: async (loc, block = sc.scrollBlock || 'start') => {
      await loc.first().evaluate((el, [b, at]) => el.scrollIntoView({ behavior: b, block: at }), [fast ? 'instant' : 'smooth', block]);
      await wait(1400);
    },
    // A step that shows a secret asserts it is blurred on screen: each selector matches at least one visible element
    // (a renamed test id would otherwise unmask it silently) and every match, or an ancestor, has a blur filter.
    // Text that blurText covers is checked the same way. Throws with the selector that is not blurred.
    assertMasked: async (selectors = sc.mask || []) => {
      await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));
      const bad = await page.evaluate(([sels, srcs]) => {
        const blurred = (el) => {
          for (let e = el; e && e.nodeType === 1; e = e.parentElement) if (/blur/.test(getComputedStyle(e).filter)) return true;
          return false;
        };
        const visible = (el) => { const b = el.getBoundingClientRect(); return b.width > 0 && b.height > 0; };
        const out = [];
        for (const sel of sels) {
          const els = [...document.querySelectorAll(sel)].filter(visible);
          if (!els.length) out.push(`${sel}: nothing on screen`);
          else if (!els.every(blurred)) out.push(`${sel}: not blurred`);
        }
        const res = srcs.map((x) => new RegExp(x));
        const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        for (let n = w.nextNode(); n; n = w.nextNode()) {
          if (n.parentElement && visible(n.parentElement) && res.some((r) => r.test(n.nodeValue)) && !blurred(n.parentElement)) {
            out.push('a text the blurText rules cover is not blurred');
            break;
          }
        }
        return out;
      }, [[].concat(selectors), sc.blurText || []]);
      if (bad.length) throw new Error(`MASK: ${bad.join('; ')}`);
    },
    smoothScrollBy: async (dy) => {
      await page.evaluate(([d, b]) => window.scrollBy({ top: d, behavior: b }), [dy, fast ? 'instant' : 'smooth']);
      await wait(1400);
    },
  };

  const timeline = [];
  let failed = null;
  await wait(500);
  for (let i = 0; i < sc.steps.length; i++) {
    const n = i + 1;
    const start = Date.now() - t0;
    const hold = fast ? 0 : Math.max(MIN_HOLD_MS, Math.round((durations[n] || 0) * 1000) + TAIL_PAD_MS);
    let status = 'PASS', error = null;
    try {
      await sc.steps[i].run(page, h);
    } catch (e) {
      status = 'FAIL';
      error = redact(String(e.message || e).split('\n')[0]);
      // The failing screen, for the report (work/ is gitignored; masks apply as on the video).
      await page.screenshot({ path: path.join(work, `fail-step-${n}.png`) }).catch(() => {});
    }
    const remaining = start + hold - (Date.now() - t0);
    if (remaining > 0) await page.waitForTimeout(remaining);
    const end = Date.now() - t0;
    timeline.push({ n, start_ms: start, end_ms: end, status, error, url: redact(page.url()) });
    console.log(`step ${n} ${status} ${((end - start) / 1000).toFixed(1)}s ${error || ''}`);
    if (status === 'FAIL') { failed = n; await wait(1500); break; }
  }
  await wait(800);
  const total = Date.now() - t0;
  const video = fast ? null : page.video();
  await context.close();
  await browser.close();
  if (video) fs.renameSync(await video.path(), path.join(work, 'video.webm'));
  const result = {
    id: sc.id, app: sc.app, ...(sc.identity ? { identity: sc.identity } : {}), title: sc.title, ...(sc.title_vi ? { title_vi: sc.title_vi } : {}), baseURL: sc.baseURL, mode: fast ? 'fast' : 'uat',
    recorded_at: new Date().toISOString(), total_ms: total,
    verdict: failed ? 'FAIL' : 'PASS', failed_step: failed, steps_run: timeline.length, steps_total: sc.steps.length,
    ...(sc.meta ? { meta: sc.meta } : {}),
    ...(readOnly ? { read_only: true, blocked_writes: blockedWrites, blocked_other: [...new Set(blockedOther)] } : {}),
    ...(blockedUrls.length ? { blocked_urls: blockedUrls } : {}),
    ...(failed ? { failed_error: timeline[timeline.length - 1].error } : {}),
  };
  fs.writeFileSync(path.join(work, 'timeline.json'), JSON.stringify(timeline, null, 2));
  fs.writeFileSync(path.join(work, 'result.json'), JSON.stringify(result, null, 2));
  console.log(`verdict ${result.verdict}${video ? `; video ${path.join(work, 'video.webm')}` : ''}`);
  process.exitCode = failed ? 2 : 0;
}

main().catch((e) => { console.error(e); process.exit(1); });
