// Shared helpers of the read-only dry-run scenarios (AA-1009; scenarios listed in tools/uat/scenarios/dryrun.cjs).
// A scenario built with ro() is read-only (record.cjs aborts every non-GET request and lists it) and names the identity
// it needs; the dry-run runner signs that identity in before the browser starts. Cost $0.
//   const { ro, check } = require('../../lib/dryrun-page.cjs');
//   module.exports = ro({ id: 'BK-05', app: 'booking', identity: 'booking', baseURL, title, titleVi, steps: [...] });
//   await check(page, h, '/suppliers', { heading: /Suppliers/, table: true });
'use strict';

const DESKTOP = { width: 1440, height: 900 };
const PHONE = { width: 390, height: 844 };

/** A read-only scenario: identity + readOnly + the usual record.cjs fields. */
function ro({ id, app, identity = 'public', title, titleVi, baseURL, viewport = DESKTOP, steps, ...rest }) {
  const phone = viewport === PHONE;
  return {
    id, app, identity, title, ...(titleVi ? { title_vi: titleVi } : {}),
    baseURL: process.env.UAT_BASE_URL || baseURL,
    viewport,
    ...(phone ? { isMobile: true, hasTouch: true } : {}),
    readOnly: true,
    // Old Dev test rows carry internal issue ids in names: never on screen in a recorded take.
    blurText: ['\\bAA-?\\d{3,4}\\b'],
    ...rest,
    steps,
  };
}

// Responses a page check counts as broken: the page's own API answered 5xx, or 401 / 403 (the session was lost or the
// identity lacks a right the page needs). Collected per page from the first check() on.
const watched = new WeakMap();
function watch(page) {
  if (watched.has(page)) return watched.get(page);
  const seen = [];
  page.on('response', (r) => {
    const s = r.status();
    if (s < 500 && s !== 401 && s !== 403) return;
    let u;
    try { u = new URL(r.url()); } catch { return; }
    if (u.origin !== new URL(page.url()).origin) return;
    if (!/^\/(api|bff|crm|booking|portal\/api)\//.test(u.pathname)) return;
    seen.push(`${r.request().method()} ${u.pathname.replace(/[A-Za-z0-9_-]{30,}/g, '<token>')} ${s}`);
  });
  watched.set(page, seen);
  return seen;
}

function assertNoApiErrors(page) {
  const seen = watch(page);
  if (seen.length) {
    const list = seen.splice(0).slice(0, 4).join(', ');
    throw new Error(`the page's API failed: ${list}`);
  }
}

/** Signed in? A bounce to a sign-in page, the managed login or the partner refresh means the saved session is gone. */
function assertSignedIn(page, baseURL) {
  const u = new URL(page.url());
  const home = new URL(baseURL);
  if (u.origin !== home.origin || /^\/(login|sign-?in|signed-out|auth\/refresh|tenant-login)\b/.test(u.pathname)) {
    throw new Error(`not signed in (landed on ${u.host}${u.pathname}); the identity's saved session was refused`);
  }
}

/**
 * Open `p` and check it rendered: same origin and not a sign-in page (signedIn), the first h1 (contains `heading`
 * when given), the `ready` selector, and with `table` a data row or the kit empty state. Every wait has its own cap.
 */
async function check(page, h, p, { heading, ready, table = false, signedIn = true, timeout = 30_000 } = {}) {
  const seen = watch(page);
  seen.length = 0;
  await h.goto(p);
  if (signedIn) assertSignedIn(page, new URL(p, h.baseURL).origin);
  const h1 = page.locator('h1').first();
  if (heading) await h.expect(h1).toContainText(heading, { timeout });
  else await h.expect(h1).toBeVisible({ timeout });
  if (ready) await h.expect(page.locator(ready).first()).toBeVisible({ timeout });
  if (table) await rowsOrEmpty(page, h, timeout);
  assertNoApiErrors(page);
}

/** A data row (table body row or role=row) or the kit empty state, and no skeleton left. */
async function rowsOrEmpty(page, h, timeout = 30_000) {
  await h.expect.poll(async () => {
    const rows = await page.locator('table tbody tr, [role="row"]').count().catch(() => 0);
    const empty = await page.getByText(/no (results|data|items|records|matches)|nothing (here|yet)|empty/i).first()
      .isVisible().catch(() => false);
    const loading = await page.locator('[aria-busy="true"], .aa-skeleton').count().catch(() => 0);
    return (rows > 0 || empty) && loading === 0 ? 'ready' : 'waiting';
  }, { timeout, intervals: [500, 1000, 2000] }).toBe('ready');
}

/** At a phone width, nothing scrolls sideways (document, and `main` when the shell scrolls inside it). */
async function assertNoSideScroll(page) {
  const m = await page.evaluate(() => {
    const d = document.documentElement;
    const main = document.querySelector('main');
    return { doc: d.scrollWidth - d.clientWidth, main: main ? main.scrollWidth - main.clientWidth : 0 };
  });
  if (m.doc > 1 || m.main > 1) throw new Error(`the page scrolls sideways at this width (document +${m.doc}px, main +${m.main}px)`);
}

module.exports = { DESKTOP, PHONE, ro, check, rowsOrEmpty, watch, assertNoApiErrors, assertSignedIn, assertNoSideScroll };
