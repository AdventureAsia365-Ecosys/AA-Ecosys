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
// (filled by steps, e.g. the app git_sha at the start and end) is copied into result.json; after(page, h) runs once
// after the steps, also after a FAIL (restore what the scenario changed on its synthetic tenant).
// Masks are on before the first paint; a step that shows a secret calls h.assertMasked([selectors]) (each selector on
// screen and blurred). scenario.isMobile / hasTouch make a phone take a real mobile context; scenario.title_vi goes to
// result.json for the Vietnamese chapter list of longform.py. Errors and URLs written to timeline.json / result.json
// have link tokens (path or query segments of 30+ characters, uuids excepted) replaced by <redacted>.
// Dry-run guards (AA-1009, tools/uat/dryrun.cjs): scenario.readOnly aborts every request that is not GET / HEAD / OPTIONS
// (scenario.allowWrites = [regex sources on the URL, or "<METHOD> <regex>" for one method only] lets named ones through) and lists them in result.json
// blocked_writes; scenario.blockUrls = [regex sources] aborts any matching request (e.g. paid model paths) and lists it
// in blocked_urls (env UAT_READ_ONLY=1 / UAT_BLOCK_URLS=<JSON list> add both to any scenario). Telemetry beacons, the
// staff session keep-alive (POST /api/auth/refresh) and third-party posts are aborted but listed in blocked_other
// (lib/net-guard.cjs); a read-only run also refuses non-read page.request / context.request calls (blocked_writes) and
// closes every WebSocket (blocked_other). UAT_HEADED=1 or scenario.headed opens a visible Chromium (WSLg DISPLAY), for pages a headless browser
// cannot pass. scenario.identity (public, cis-admin, booking, studio, crm) is copied into result.json.
// UAT_DEBUG=1 prints a failing step's whole error (redacted, one line "Error detail: ..."): result.json keeps only its
// first line, which hides the reason (a strict mode violation reads "expect(locator).toBeVisible() failed").
// Pilot guard (AA-855, lib/pilot-guard.cjs, fail closed): before the recorded context exists, a signed-in scenario reads
// its tenant / agency through the app's own API in a separate, unrecorded context; anything but a synthetic tenant on the
// allow-list stops the run with exit 5 (pilot_guard), result.json verdict BLOCKED, and no video. --guard-only runs
// prepare() and the guard only (run.sh calls it before the TTS). scenario.pilotGuard = { scopes, only } narrows it.
// scenario.allowRows = { rows: CSS selector, allow: [regex sources] } blurs, before the first paint, every matching row
// whose text matches none of `allow` (AA staff pages that list tenants); h.assertRowsFiltered() fails a step when such a
// row is on screen unblurred.
// Preview (AA-855, env UAT_PREVIEW=1, set by dryrun.cjs --preview, fast only): only the steps before the first step
// marked `writes` (lib/dryrun-page.cjs step(..., { writes: true })) run, and allowWrites is emptied, so any write is
// aborted and fails the run. result.json says preview: true and counts only those steps. Cost $0.
// Setup once: bash tools/uat/setup.sh (pins @playwright/test). One Chromium, closed at the end.
// Exit: 0 PASS, 2 a step FAILed, 5 pilot_guard (no video), 1 crash.
const fs = require('fs');
const path = require('path');
const { chromium, expect } = require('@playwright/test');

const MIN_HOLD_MS = 2500;
// Link tokens travel in URL path segments and query values: never write one to timeline.json / result.json / logs.
// (A uuid is an object id, not a credential: kept for debugging.)
// Same rule as the dry-run report (lib/dryrun-core.cjs): also masks AWS ARNs and 12-digit account numbers.
const { redact, blockSources } = require('./lib/dryrun-core.cjs');
const TAIL_PAD_MS = 600;
// Which aborted request is a write to the app (fails a read-only scenario) and which is telemetry / session upkeep /
// third party (listed apart): lib/net-guard.cjs.
const guard = require('./lib/net-guard.cjs');
const pilotGuard = require('./lib/pilot-guard.cjs');

async function main() {
  const scenarioPath = path.resolve(process.argv[2]);
  const captionsOnly = process.argv.includes('--captions');
  const fast = process.argv.includes('--fast');
  const guardOnly = process.argv.includes('--guard-only');
  const sc = require(scenarioPath);
  const work = path.join(__dirname, 'work', sc.id);
  fs.mkdirSync(work, { recursive: true });

  if (captionsOnly) {
    const captions = sc.steps.map((s, i) => ({ n: i + 1, ...s.caption }));
    fs.writeFileSync(path.join(work, 'captions.json'), JSON.stringify({ id: sc.id, title: sc.title, captions }, null, 2));
    console.log(`captions: ${captions.length} -> ${path.join(work, 'captions.json')}`);
    return;
  }

  if (sc.fastOnly && !fast && !guardOnly) throw new Error(`${sc.id} is a data step: run it with --fast only`);
  const preview = process.env.UAT_PREVIEW === '1';
  if (preview && !fast && !guardOnly) throw new Error(`${sc.id}: a preview is a fast dry run, never a recorded take`);
  let steps = sc.steps;
  if (preview) {
    const n = steps.findIndex((s) => s && s.writes);
    steps = n < 0 ? steps : steps.slice(0, n);
    if (!steps.length) throw new Error(`${sc.id}: no read-only part to preview (its first step writes)`);
    sc.allowWrites = []; // nothing is written in a preview: every write is aborted and fails the run
  }
  // The narration was made from captions.json: a recorded take whose steps say something else (scenario edited, or
  // steps chosen from run state that changed since) would play the wrong voice-over.
  const cPath = path.join(work, 'captions.json');
  if (!fast && !guardOnly && fs.existsSync(cPath)) {
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
  // The pilot guard runs in its own unrecorded context, before the recorded one exists (no frame of a refused tenant).
  let verdict;
  try {
    verdict = await pilotGuard.check(browser, storageState, pilotGuard.scopesFor(sc, storageState));
  } catch (e) {
    verdict = { ok: false, code: pilotGuard.CODE, reason: String(e.message || e).split('\n')[0] };
  }
  console.log(`pilot guard ${sc.id}: ${redact(pilotGuard.describeVerdict(verdict))}`);
  if (!verdict.ok || guardOnly) {
    await browser.close();
    if (!verdict.ok) {
      if (!guardOnly) {
        fs.writeFileSync(path.join(work, 'timeline.json'), '[]');
        fs.writeFileSync(path.join(work, 'result.json'), JSON.stringify({ id: sc.id, app: sc.app,
          ...(sc.identity ? { identity: sc.identity } : {}), title: sc.title, mode: fast ? 'fast' : 'uat',
          recorded_at: new Date().toISOString(), total_ms: 0, verdict: 'BLOCKED', pilot_guard: redact(verdict.reason),
          failed_step: null, steps_run: 0, steps_total: sc.steps.length }, null, 2));
      }
      process.exitCode = pilotGuard.EXIT_PILOT_GUARD;
    }
    return;
  }
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
  // A paid take may open only the paid paths its scenario names (allowPaidUrls); the rest of the runner's list holds.
  const blockSrc = blockSources(sc);
  if (readOnly || blockSrc.length) {
    const allow = guard.compileAllow(sc.allowWrites);
    const block = blockSrc.map((x) => new RegExp(x));
    await context.route('**/*', (route) => {
      const req = route.request();
      const url = req.url();
      const where = () => { const u = new URL(url); return `${u.host}${u.pathname}`; };
      if (block.some((r) => r.test(url))) {
        blockedUrls.push(redact(`${req.method()} ${where()}`));
        return route.abort('blockedbyclient');
      }
      // The AWS WAF challenge proof carries no app data (lib/net-guard.cjs): it always goes on, preview included.
      if (readOnly && !guard.isRead(req.method()) && !guard.allowMatches(allow, req.method(), url) && !guard.isChallengeProof(url)) {
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
    const allow = guard.compileAllow(sc.allowWrites);
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
  if (sc.allowRows) {
    await context.addInitScript(({ rows, allow }) => {
      const res = allow.map((x) => new RegExp(x, 'i'));
      const scan = () => {
        for (const r of document.querySelectorAll(rows)) {
          if (!res.some((x) => x.test(r.textContent || ''))) r.style.setProperty('filter', 'blur(10px)', 'important');
        }
      };
      new MutationObserver(scan).observe(document, { childList: true, subtree: true, characterData: true });
      scan();
    }, sc.allowRows);
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
    // scenario.allowRows: every visible row outside the allow-list is blurred (or there is none). Returns the counts.
    assertRowsFiltered: async () => {
      if (!sc.allowRows) throw new Error('assertRowsFiltered needs scenario.allowRows');
      await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));
      const c = await page.evaluate(({ rows, allow }) => {
        const res = allow.map((x) => new RegExp(x, 'i'));
        const out = { allowed: 0, blurred: 0, open: 0 };
        for (const r of document.querySelectorAll(rows)) {
          const b = r.getBoundingClientRect();
          if (!b.width || !b.height) continue;
          if (res.some((x) => x.test(r.textContent || ''))) out.allowed++;
          else if (/blur/.test(getComputedStyle(r).filter)) out.blurred++;
          else out.open++;
        }
        return out;
      }, sc.allowRows);
      if (c.open) throw new Error(`MASK: ${c.open} row(s) outside the synthetic allow-list are not blurred`);
      return c;
    },
    smoothScrollBy: async (dy) => {
      await page.evaluate(([d, b]) => window.scrollBy({ top: d, behavior: b }), [dy, fast ? 'instant' : 'smooth']);
      await wait(1400);
    },
  };

  const timeline = [];
  let failed = null;
  await wait(500);
  for (let i = 0; i < steps.length; i++) {
    const n = i + 1;
    const start = Date.now() - t0;
    const hold = fast ? 0 : Math.max(MIN_HOLD_MS, Math.round((durations[n] || 0) * 1000) + TAIL_PAD_MS);
    let status = 'PASS', error = null;
    try {
      await steps[i].run(page, h);
    } catch (e) {
      status = 'FAIL';
      error = redact(String(e.message || e).split('\n')[0]);
      if (process.env.UAT_DEBUG) console.log(`Error detail: ${redact(String(e.message || e)).replace(/\x1b\[[0-9;]*m/g, '').replace(/\s*\n\s*/g, ' | ').slice(0, 2500)}`);
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
  // scenario.after(page, h): runs once after the steps, also after a FAIL (e.g. put a synthetic tenant's old values
  // back). Its failure does not change the verdict; it is kept in result.json after_error and fails the exit code.
  let afterError = null;
  if (typeof sc.after === 'function') {
    try {
      await sc.after(page, h);
    } catch (e) {
      afterError = redact(String(e.message || e).split('\n')[0]);
      console.log(`after: FAIL ${afterError}`);
    }
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
    verdict: failed ? 'FAIL' : 'PASS', failed_step: failed, steps_run: timeline.length, steps_total: steps.length,
    ...(preview ? { preview: true, steps_in_scenario: sc.steps.length } : {}),
    ...(sc.meta ? { meta: sc.meta } : {}),
    ...(readOnly ? { read_only: true, blocked_writes: blockedWrites, blocked_other: [...new Set(blockedOther)] } : {}),
    ...(blockedUrls.length ? { blocked_urls: blockedUrls } : {}),
    ...(failed ? { failed_error: timeline[timeline.length - 1].error } : {}),
    ...(afterError ? { after_error: afterError } : {}),
  };
  fs.writeFileSync(path.join(work, 'timeline.json'), JSON.stringify(timeline, null, 2));
  fs.writeFileSync(path.join(work, 'result.json'), JSON.stringify(result, null, 2));
  console.log(`verdict ${result.verdict}${video ? `; video ${path.join(work, 'video.webm')}` : ''}`);
  // A step that refused its tenant (scenarios/crm/_crm.cjs assertReviewAgency) is a pilot-guard stop too.
  const guardStop = failed && String(result.failed_error || '').startsWith(`${pilotGuard.CODE}:`);
  process.exitCode = guardStop ? pilotGuard.EXIT_PILOT_GUARD : (failed || afterError ? 2 : 0);
}

main().catch((e) => { console.error(e); process.exit(1); });
