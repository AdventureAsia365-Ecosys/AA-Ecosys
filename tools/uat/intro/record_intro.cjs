// TripPlanner intro video recorder (skill aa-uat-video), derived from ../record.cjs (cursor + click overlay, step held to its
// narration length). One run = one language, because English and Vietnamese narration differ in length.
//   node intro/record_intro.cjs <en|vi>
//     reads  work/TripPlanner-intro-<LANG>/durations.json   (from intro/tts_intro.py)
//     writes work/TripPlanner-intro-<LANG>/seg-<n>.webm + timeline.json + result.json
// Segments: desktop 1440x900 (main tour), mobile 390x844 (one short phone segment), closing 1440x900.
// Safety (no real inquiry, no paid call): every "send" to an advisor is answered locally with the same
// 422 registration_required the live service gives a guest without contact details (live config
// REQUIRE_REGISTRATION_BEFORE_HANDOFF=true), so the contact form appears and nothing is submitted;
// narration (AI) and free-text search (embedding) requests are aborted; sign-in calls are aborted.
// The demo form is filled with obviously fake data and never submitted. One Chromium, closed at the end.
const fs = require('fs');
const path = require('path');
const { chromium, expect } = require('@playwright/test');

const LEAD_MS = 250;      // narration starts this long after the step starts (build_intro.py uses the same)
const TAIL_PAD_MS = 900;  // breathing room after the last sentence of a step
const BASE = process.env.UAT_BASE_URL || 'https://aa-tripplanner.vercel.app';
const TOUR = '/tours/western-bhutan-thimphu-punakha-and-paro-7-days-bhutan-8b6ce67b';

const VIEWPORTS = {
  desktop: { width: 1440, height: 900 },
  mobile: { width: 390, height: 844 },
  closing: { width: 1440, height: 900 },
};

function helpers(page, state) {
  const h = {
    expect,
    pause: (ms) => page.waitForTimeout(ms),
    goto: async (p) => {
      await page.goto(new URL(p, BASE).toString(), { waitUntil: 'load' });
      for (let i = 0; i < 20 && /Security Checkpoint/i.test(await page.title()); i++) await page.waitForTimeout(1000);
      if (/Security Checkpoint/i.test(await page.title())) throw new Error('VERCEL_CHECKPOINT (VPN/datacenter IP?)');
      await page.mouse.move(state.cursor.x, state.cursor.y);
    },
    moveXY: async (x, y, steps = 30) => { await page.mouse.move(x, y, { steps }); state.cursor = { x, y }; },
    moveTo: async (loc, dx = null) => {
      await loc.scrollIntoViewIfNeeded();
      const b = await loc.boundingBox();
      if (!b) throw new Error('element has no box');
      const to = { x: b.x + (dx ?? Math.min(b.width / 2, 120)), y: b.y + b.height / 2 };
      await h.moveXY(to.x, to.y);
    },
    hover: async (loc, ms = 600) => { await h.moveTo(loc); await page.waitForTimeout(ms); },
    clickXY: async (x, y) => {
      await h.moveXY(x, y);
      await page.waitForTimeout(300);
      await page.mouse.down(); await page.waitForTimeout(110); await page.mouse.up();
    },
    click: async (loc) => {
      await h.moveTo(loc);
      await page.waitForTimeout(350);
      await page.mouse.down(); await page.waitForTimeout(120); await page.mouse.up();
    },
    tap: async (loc) => { await h.moveTo(loc); await page.waitForTimeout(300); await loc.tap(); },
    // Eased page scroll over `ms` (smoother and slower than behavior:'smooth').
    glide: async (dy, ms = 1800) => {
      await page.evaluate(([d, t]) => new Promise((res) => {
        const y0 = window.scrollY, t0 = performance.now();
        const ease = (x) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2);
        const tick = (now) => {
          const k = Math.min(1, (now - t0) / t);
          window.scrollTo(0, y0 + d * ease(k));
          if (k < 1) requestAnimationFrame(tick); else res();
        };
        requestAnimationFrame(tick);
      }), [dy, ms]);
      await page.waitForTimeout(250);
    },
    glideTo: async (loc, offset = 90, ms = 1800) => {
      const el = loc.first();
      await el.waitFor({ state: 'attached' });
      const top = await el.evaluate((e) => e.getBoundingClientRect().top);
      await h.glide(top - offset, ms);
    },
    typeSlow: async (loc, text) => { await h.click(loc); await page.keyboard.type(text, { delay: 70 }); },
  };
  return h;
}

// Step actions, keyed like narration.json. Each run() does the on-screen action; narration plays over it.
const ACTIONS = {
  open: async (page, h) => {
    await h.expect(page.locator('h1')).toContainText('Plan your Asia adventure');
    await h.pause(2500);
    await h.moveXY(520, 330, 60);
    await h.pause(2500);
    await h.moveXY(760, 520, 60);
  },
  search: async (page, h) => {
    const dest = page.getByLabel('Destination');
    await h.hover(dest, 500);
    await dest.selectOption({ label: 'Bhutan (32 tours)' });
    await h.pause(1400);
    await h.click(page.getByRole('button', { name: '7 days' }));
    await h.pause(1200);
    await h.click(page.getByRole('button', { name: 'More travellers' }));
    await h.pause(900);
    await h.click(page.getByRole('button', { name: 'Fewer travellers' }));
    await h.pause(1200);
    await h.hover(page.getByRole('button', { name: /plan my trip/i }), 900);
  },
  featured: async (page, h) => {
    await h.glideTo(page.getByText('Find by destination'), 260, 1600);
    await h.pause(1200);
    await h.glideTo(page.getByRole('heading', { name: 'Trips to start from' }), 110, 1800);
    await h.hover(page.locator('a[href^="/tours/"] h3').first(), 1200);
    await h.click(page.getByRole('button', { name: 'Next tours' }));
    await h.pause(1500);
  },
  where: async (page, h) => {
    await h.glideTo(page.getByRole('heading', { name: 'Where to go' }), 140, 2200);
    await h.expect(page.locator('a[href="/destinations/bhutan"]').first()).toContainText('tours');
    await h.hover(page.locator('a[href="/destinations/bhutan"]').first(), 800);
  },
  country: async (page, h) => {
    await h.click(page.locator('a[href="/destinations/bhutan"]').first());
    await page.waitForURL('**/destinations/bhutan');
    await h.expect(page.locator('h1')).toContainText(/bhutan/i);
    await h.pause(1200);
    await h.hover(page.locator('h1').first(), 800);
  },
  'country-tours': async (page, h) => {
    await h.glideTo(page.getByRole('heading', { name: /Tours in Bhutan/i }), 110, 1800);
    await h.hover(page.locator('main a[href^="/tours/"] h3').first(), 900);
    await h.click(page.getByRole('button', { name: 'Next tours' }));
    await h.pause(1600);
    await h.click(page.getByRole('button', { name: 'Previous tours' }));
    await h.pause(800);
  },
  'country-places': async (page, h) => {
    await h.glideTo(page.getByRole('heading', { name: /Places our tours visit/i }), 110, 1800);
    await h.pause(800);
    await h.hover(page.getByText('Paro Taktsang', { exact: false }).first(), 900);
  },
  'open-tour': async (page, h) => {
    await h.glideTo(page.getByRole('heading', { name: /Tours in Bhutan/i }), 110, 1400);
    const card = page.locator(`main a[href="${TOUR}"]`).first();
    await h.click(card);
    await page.waitForURL(`**${TOUR}`);
    await h.expect(page.locator('h1')).toContainText(/7 Days/);
  },
  'tour-top': async (page, h) => {
    await h.pause(1200);
    await h.hover(page.locator('h1').first(), 900);
    await h.glide(380, 1600);
    await h.hover(page.getByText('Best time to go').first(), 800);
  },
  'tour-days': async (page, h) => {
    await h.glideTo(page.getByRole('heading', { name: 'Highlights' }), 110, 1500);
    await h.pause(1200);
    await h.glideTo(page.getByRole('heading', { name: 'Day by day' }), 110, 1500);
    await h.click(page.getByText('Thimphu to Punakha via Dochula Pass').first());
    await h.pause(900);
  },
  'tour-map': async (page, h) => {
    await h.glideTo(page.getByRole('heading', { name: 'Where you go' }), 100, 1800);
    await h.pause(2200);
    await h.glideTo(page.getByRole('heading', { name: 'Included', exact: true }), 120, 1600);
  },
  customise: async (page, h) => {
    await h.glide(-(await page.evaluate(() => window.scrollY)), 1800);
    const btn = page.getByRole('link', { name: /customise this trip/i }).first();
    await h.hover(btn, 1800);
    await h.hover(page.getByText('No payment to send a draft').first(), 1200);
  },
  planner: async (page, h) => {
    await h.click(page.getByRole('link', { name: /customise this trip/i }).first());
    await page.waitForURL('**/plan**');
    await h.expect(page.getByText('Built from 1 Adventure Asia tour')).toBeVisible({ timeout: 25000 });
    await h.pause(1000);
    await h.hover(page.getByText('KM BY ROAD', { exact: false }).first(), 1200);
    await h.hover(page.getByText('Getting there').first(), 900);
  },
  map: async (page, h) => {
    const ok = page.getByRole('button', { name: 'OK', exact: true });
    if (await ok.count()) await h.click(ok.first()).catch(() => {});
    await h.hover(page.getByRole('button', { name: 'Trekking' }), 800);
    await h.hover(page.getByRole('button', { name: 'Cultural Heritage' }), 600);
    await h.hover(page.getByRole('button', { name: 'Culinary' }), 900);
    await h.click(page.getByRole('button', { name: /^Filters/ }));
    await h.pause(900);
    await h.clickXY(314, 278); // the Bhutan cluster on the starting view of the map
    await h.pause(2600);
    await h.moveXY(552, 488, 25);
    for (let i = 0; i < 4; i++) { await page.mouse.wheel(0, -250); await h.pause(450); }
    await h.pause(1500);
  },
  suggest: async (page, h) => {
    const box = page.locator('div', { has: page.getByText('You might also like', { exact: true }) }).last();
    const first = box.getByRole('button').first();
    await first.scrollIntoViewIfNeeded();
    await h.hover(first, 900);
    await h.click(first);
    const add = page.getByRole('button', { name: '+ Add to trip' }).first();
    await add.waitFor({ state: 'visible', timeout: 15000 });
    await h.pause(1200);
    await h.click(add);
    await h.pause(1800);
  },
  days: async (page, h) => {
    const close = page.getByRole('button', { name: 'Close', exact: true }).first();
    if (await close.count() && await close.isVisible().catch(() => false)) await h.click(close).catch(() => {});
    const panelTop = page.getByText('Built from', { exact: false }).first();
    await panelTop.scrollIntoViewIfNeeded();
    await h.click(page.getByRole('button', { name: '+ extra night' }).nth(1));
    await h.pause(1500);
    await h.click(page.getByRole('button', { name: 'Activities here' }).first());
    await h.pause(2200);
    await h.click(page.getByRole('button', { name: 'Hide activities' }).first());
    await h.pause(700);
    await h.hover(page.getByRole('button', { name: '+ free day' }), 1200);
  },
  list: async (page, h) => {
    await h.click(page.getByRole('button', { name: 'List of tours' }));
    await h.pause(2200);
    await h.hover(page.getByText('Plan this route').nth(1), 900);
    await h.moveXY(520, 520, 20);
    for (let i = 0; i < 3; i++) { await page.mouse.wheel(0, 220); await h.pause(400); }
    await h.pause(800);
    await h.click(page.getByRole('button', { name: 'Map', exact: true }));
    await h.pause(800);
  },
  send: async (page, h) => {
    await h.click(page.getByRole('button', { name: 'Send to an advisor' }));
    const name = page.getByPlaceholder('Full name');
    await name.waitFor({ state: 'visible', timeout: 10000 });
    await h.pause(600);
    await h.typeSlow(name, 'Demo Traveller');
    await h.typeSlow(page.getByPlaceholder('Phone'), '+00 000 000 000');
    await h.typeSlow(page.getByPlaceholder('Email'), 'demo@example.com');
    await h.click(page.getByRole('checkbox').last());
    await h.pause(600);
    await h.hover(page.getByRole('button', { name: /Register & send/ }), 1200);
    await h.moveXY(1240, 600, 25); // move away: nothing is submitted
  },
  saved: async (page, h) => {
    await h.hover(page.getByText('An advisor confirms logistics before anything is booked.').first(), 2500);
    await h.hover(page.getByRole('link', { name: 'Sign in' }).first(), 2500);
  },
  mobile: async (page, h) => {
    await h.pause(1200);
    await h.tap(page.getByRole('button', { name: 'Open menu' }));
    await h.pause(2000);
    await h.tap(page.getByRole('button', { name: 'Close menu' }).first());
    await h.pause(300);
    await h.goto(TOUR);
  },
  'mobile-tour': async (page, h) => {
    await h.pause(600);
    await h.glide(900, 2200);
    await h.pause(500);
    await h.hover(page.getByRole('link', { name: /customise this trip/i }).last(), 1200);
  },
  'value-leads': async (page, h) => {
    await h.pause(700);
    await h.glideTo(page.getByRole('heading', { name: 'How it works' }), 120, 2600);
    await h.hover(page.getByText('Step 1', { exact: false }).first(), 1200);
    await h.hover(page.getByText('Step 3', { exact: false }).first(), 800);
  },
  'value-sync': async (page, h) => {
    await h.glideTo(page.getByRole('heading', { name: 'Talk it through with an advisor' }), 260, 2400);
    await h.pause(1200);
    await h.moveXY(720, 450, 40);
  },
};

async function guard(context, counts) {
  await context.route('**/api/trip**', async (route) => {
    const body = route.request().postData() || '';
    if (/"op"\s*:\s*"send"/.test(body)) {
      counts.send_local_422++;
      return route.fulfill({ status: 422, contentType: 'application/json',
        body: JSON.stringify({ error: 'registration_required', detail: 'name and phone or email required before sending' }) });
    }
    if (/"op"\s*:\s*"narrate"/.test(body)) { counts.narrate_aborted++; return route.abort(); }
    return route.continue();
  });
  await context.route('**/api/browse?resource=search**', (r) => { counts.search_aborted++; return r.abort(); });
  await context.route('**/api/auth/start**', (r) => { counts.auth_aborted++; return r.abort(); });
  await context.route('**/api/auth/verify**', (r) => { counts.auth_aborted++; return r.abort(); });
}

async function main() {
  const lang = process.argv[2];
  if (!['en', 'vi'].includes(lang)) throw new Error('usage: record_intro.cjs <en|vi>');
  const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'narration.json'), 'utf8'));
  const work = path.join(__dirname, '..', 'work', `${data.id}-${lang.toUpperCase()}`);
  const durations = JSON.parse(fs.readFileSync(path.join(work, 'durations.json'), 'utf8'));
  for (const f of fs.readdirSync(work)) if (/^seg-\d+\.webm$/.test(f)) fs.unlinkSync(path.join(work, f));

  const segs = [];
  for (const [i, s] of data.steps.entries()) {
    if (!segs.length || segs[segs.length - 1].name !== s.segment) segs.push({ name: s.segment, steps: [] });
    segs[segs.length - 1].steps.push({ n: i + 1, ...s });
  }

  const browser = await chromium.launch({
    headless: true, slowMo: 50,
    args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'],
  });
  const counts = { send_local_422: 0, narrate_aborted: 0, search_aborted: 0, auth_aborted: 0 };
  const timeline = [];
  let failed = null;
  for (const [si, seg] of segs.entries()) {
    const vp = VIEWPORTS[seg.name];
    const mobile = seg.name === 'mobile';
    const context = await browser.newContext({
      viewport: vp, deviceScaleFactor: 1, isMobile: mobile, hasTouch: mobile,
      recordVideo: { dir: work, size: vp }, reducedMotion: 'no-preference', locale: 'en-US',
    });
    await guard(context, counts);
    await context.addInitScript({ path: path.join(__dirname, '..', 'lib', 'overlay.js') });
    const page = await context.newPage();
    const t0 = Date.now();
    const state = { cursor: { x: vp.width / 2, y: vp.height / 2 } };
    const h = helpers(page, state);
    // Every segment opens on the loaded home page; build_intro.py cuts the video before trim_ms (blank load).
    await h.goto('/');
    await page.waitForTimeout(1200);
    seg.trim_ms = Date.now() - t0;
    for (const st of seg.steps) {
      const start = Date.now() - t0;
      const hold = Math.round((durations[st.n] || 0) * 1000) + LEAD_MS + TAIL_PAD_MS;
      let status = 'PASS', error = null;
      try { await ACTIONS[st.key](page, h); } catch (e) { status = 'FAIL'; error = String(e.message || e).split('\n')[0]; }
      const remaining = start + hold - (Date.now() - t0);
      if (remaining > 0) await page.waitForTimeout(remaining);
      const end = Date.now() - t0;
      timeline.push({ n: st.n, key: st.key, segment: si + 1, start_ms: start, end_ms: end, status, error, url: page.url() });
      console.log(`seg ${si + 1} step ${st.n} ${st.key} ${status} ${((end - start) / 1000).toFixed(1)}s ${error || ''}`);
      if (status === 'FAIL') { failed = st.n; break; }
    }
    await page.waitForTimeout(600);
    const segTotal = Date.now() - t0;
    const video = page.video();
    await context.close();
    fs.renameSync(await video.path(), path.join(work, `seg-${si + 1}.webm`));
    seg.total_ms = segTotal;
    if (failed) break;
  }
  await browser.close();
  const result = {
    id: data.id, lang, baseURL: BASE, recorded_at: new Date().toISOString(),
    verdict: failed ? 'FAIL' : 'PASS', failed_step: failed,
    segments: segs.map((s, i) => ({ n: i + 1, name: s.name, viewport: VIEWPORTS[s.name], total_ms: s.total_ms || null, trim_ms: s.trim_ms ?? 0 })),
    guards: counts,
  };
  fs.writeFileSync(path.join(work, 'timeline.json'), JSON.stringify(timeline, null, 2));
  fs.writeFileSync(path.join(work, 'result.json'), JSON.stringify(result, null, 2));
  console.log(`verdict ${result.verdict}; guards ${JSON.stringify(counts)}`);
  process.exitCode = failed ? 2 : 0;
}

main().catch((e) => { console.error(e); process.exit(1); });
