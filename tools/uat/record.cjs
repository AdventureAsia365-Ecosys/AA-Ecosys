// UAT recorder (skill aa-uat-video). One scenario = one user story = one video = one regression test.
//   node record.cjs <scenario.cjs> --captions   -> work/<id>/captions.json (input for tts.py)
//   node record.cjs <scenario.cjs>              -> work/<id>/video.webm + timeline.json + result.json
//   node record.cjs <scenario.cjs> --fast       -> work/<id>/result.json only (no video, no holds; CI / regression)
// UAT mode holds each step at least as long as its longest narration clip (work/<id>/durations.json from tts.py),
// so the voice-over fits without stretching audio. Assertions run inside each step: a failing assertion stops the
// run, marks the step FAIL and still keeps the video as evidence. Exit: 0 PASS, 2 a step FAILed, 1 crash.
// Signed-in scenarios: UAT_STORAGE_STATE=<file> (or scenario.storageState) saved by an unrecorded sign-in run;
// the sign-in screen itself is never recorded. scenario.mask = [CSS selectors] blurs secrets on screen.
// Optional scenario hooks: prepare() runs before the browser starts (unrecorded sign-in, e.g. lib/crm-signin.cjs; it
// may set scenario.storageState); fastOnly: true refuses a recorded run (data prep / cleanup scenarios); scenario.meta
// (filled by steps, e.g. the app git_sha at the start and end) is copied into result.json.
// Setup once: bash tools/uat/setup.sh (pins @playwright/test). One Chromium, closed at the end.
const fs = require('fs');
const path = require('path');
const { chromium, expect } = require('@playwright/test');

const MIN_HOLD_MS = 2500;
const TAIL_PAD_MS = 600;

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
  if (typeof sc.prepare === 'function') await sc.prepare({ fast });

  let durations = {};
  const dPath = path.join(work, 'durations.json');
  if (!fast && fs.existsSync(dPath)) durations = JSON.parse(fs.readFileSync(dPath, 'utf8'));

  const storageState = process.env.UAT_STORAGE_STATE || sc.storageState;
  const browser = await chromium.launch({ headless: true, slowMo: fast ? 0 : 60 });
  const context = await browser.newContext({
    viewport: sc.viewport,
    deviceScaleFactor: 1,
    ...(fast ? {} : { recordVideo: { dir: work, size: sc.viewport } }),
    ...(storageState ? { storageState } : {}),
    reducedMotion: 'no-preference',
    locale: 'en-US',
  });
  if (!fast) await context.addInitScript({ path: path.join(__dirname, 'lib', 'overlay.js') });
  if (sc.mask && sc.mask.length) {
    await context.addInitScript((sels) => {
      const add = () => {
        const s = document.createElement('style');
        s.textContent = `${sels.join(',')}{filter:blur(10px)!important}`;
        document.documentElement.appendChild(s);
      };
      if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', add);
      else add();
    }, sc.mask);
  }
  const page = await context.newPage();
  const t0 = Date.now();
  let cursor = { x: sc.viewport.width / 2, y: sc.viewport.height / 2 };
  const wait = (ms) => page.waitForTimeout(fast ? Math.min(ms, 150) : ms);

  const h = {
    expect,
    fast,
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
    scrollTo: async (loc) => {
      await loc.first().evaluate((el, b) => el.scrollIntoView({ behavior: b, block: 'start' }), fast ? 'instant' : 'smooth');
      await wait(1400);
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
      error = String(e.message || e).split('\n')[0];
    }
    const remaining = start + hold - (Date.now() - t0);
    if (remaining > 0) await page.waitForTimeout(remaining);
    const end = Date.now() - t0;
    timeline.push({ n, start_ms: start, end_ms: end, status, error, url: page.url() });
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
    id: sc.id, app: sc.app, title: sc.title, baseURL: sc.baseURL, mode: fast ? 'fast' : 'uat',
    recorded_at: new Date().toISOString(), total_ms: total,
    verdict: failed ? 'FAIL' : 'PASS', failed_step: failed, steps_run: timeline.length, steps_total: sc.steps.length,
    ...(sc.meta ? { meta: sc.meta } : {}),
    ...(failed ? { failed_error: timeline[timeline.length - 1].error } : {}),
  };
  fs.writeFileSync(path.join(work, 'timeline.json'), JSON.stringify(timeline, null, 2));
  fs.writeFileSync(path.join(work, 'result.json'), JSON.stringify(result, null, 2));
  console.log(`verdict ${result.verdict}${video ? `; video ${path.join(work, 'video.webm')}` : ''}`);
  process.exitCode = failed ? 2 : 0;
}

main().catch((e) => { console.error(e); process.exit(1); });
