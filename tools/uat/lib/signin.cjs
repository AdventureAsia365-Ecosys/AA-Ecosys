// Sign-in per identity for the UAT dry run (AA-1009, skill aa-uat-video §2.5): each identity signs in ONCE, in its own
// unrecorded headless Chromium, and the scenarios start from the saved storageState (UAT_STORAGE_STATE). A saved state
// is reused while the app still accepts it, so a run asks for at most one code per identity. Cost $0 (AWS reads only).
//
//   node tools/uat/lib/signin.cjs cis-admin booking studio crm    sign in (or check the saved session) from the shell
//   const { ensureState } = require('./signin.cjs'); const file = await ensureState('booking');
//
// Identities (skill aa-ui-verify §3 / §3a; plan docs/audits/2026-10-30-S260-uat-video-plan §1):
//   public     no sign-in.
//   cis-admin  Dev-only E2E CIS admin e2e-cis-admin@e2e-mail… on the CIS admin production host: managed login with an
//              e-mail code read from the e2e mailbox prefix inbound-admin/ (MFA admin profile only). Read-only session
//              (the API refuses writes with 403 e2e_read_only).
//   booking    WORKFORCE E2E staff e2e-booking@e2e-mail… (booking-admin) on the Booking admin: e-mail code from inbound/.
//              Read-only session (403 e2e_read_only on every write).
//   studio     Content studio VIEWER of the E2E tenant (partner pool, password + authenticator), secret
//              crm/dev/e2e-test-studio/viewer (UAT_STUDIO_SECRET overrides).
//   crm        Owner of the invented agency of the CRM review set: lib/crm-signin.cjs identity A (same state file).
// Secrets and codes are read at run time and never printed, logged or written; the state files go to
// work/dryrun/.state-<identity>.json (chmod 600, gitignored). No screenshot or trace is ever taken here.
'use strict';
const fs = require('fs');
const path = require('path');
const crm = require('./crm-signin.cjs');
const mailbox = require('./mailbox.cjs');
const { redact } = require('./dryrun-core.cjs');

const CIS = (process.env.UAT_CIS_ADMIN || 'https://aa-cis.lumiguides.it.com').replace(/\/+$/, '');
const BOOKING = crm.BOOKING;
const PARTNER = crm.PARTNER;
const STAFF_AUTH_HOST = 'staff-auth.lumiguides.it.com';
const WORK = path.join(__dirname, '..', 'work', 'dryrun');
const STUDIO_SECRET = process.env.UAT_STUDIO_SECRET || 'crm/dev/e2e-test-studio/viewer';

const STAFF = {
  'cis-admin': { origin: CIS, email: 'e2e-cis-admin@e2e-mail.lumiguides.it.com', prefix: 'inbound-admin/' },
  booking: { origin: BOOKING, email: 'e2e-booking@e2e-mail.lumiguides.it.com', prefix: 'inbound/' },
};

function statePath(who) {
  return who === 'crm' ? crm.statePath('A') : path.join(WORK, `.state-${who}.json`);
}

/** Fill a managed-login field once its page settled; refill until the value is kept (lesson S253, AA-979). */
async function fillSettled(page, loc, value) {
  const { expect } = require('@playwright/test');
  await expect(loc).toBeVisible({ timeout: 30_000 });
  await page.waitForLoadState('load', { timeout: 15_000 }).catch(() => {});
  await expect(async () => {
    await loc.fill(value);
    await page.waitForTimeout(250);
    await expect(loc).toHaveValue(value, { timeout: 1_000 });
  }).toPass({ timeout: 15_000 });
}

/** After "Next": the code field directly (passwordless user) or the method choice first (pick the e-mail code). */
async function reachCodeStep(page) {
  const { expect } = require('@playwright/test');
  const code = page.getByLabel(/verification code|sign-in code|^code$/i).first();
  await expect.poll(async () => {
    if (await code.isVisible().catch(() => false)) return 'code';
    const choice = page.getByRole('button', { name: /email|one-time code/i }).or(page.getByRole('radio', { name: /email/i })).first();
    if (await choice.isVisible().catch(() => false)) {
      await choice.click({ timeout: 5_000 }).catch(() => {});
      const next = page.getByRole('button', { name: /^(next|continue)$/i }).first();
      if (await next.isVisible().catch(() => false)) await next.click({ timeout: 5_000 }).catch(() => {});
    }
    return 'waiting';
  }, { timeout: 30_000, intervals: [500, 1000, 2000] }).toBe('code');
  return code;
}

/** Staff app (CIS admin or Booking admin): /login -> "Sign in with company email" -> e-mail code -> back on the app. */
async function staffLogin(page, cfg) {
  await page.goto(`${cfg.origin}/login`, { waitUntil: 'domcontentloaded' });
  const go = page.getByRole('link', { name: /sign in with company email/i })
    .or(page.getByRole('button', { name: /sign in with company email/i })).first();
  await go.waitFor({ state: 'visible', timeout: 20_000 });
  await go.click();
  await page.waitForURL((u) => u.host === STAFF_AUTH_HOST, { timeout: 30_000 });
  await fillSettled(page, page.getByLabel(/email/i).first(), cfg.email);
  const before = await mailbox.baseline(cfg.prefix);
  const since = new Date();
  await page.getByRole('button', { name: /^next$/i }).click({ timeout: 10_000 });
  const field = await reachCodeStep(page);
  const code = await mailbox.waitForCode({ recipient: cfg.email, prefix: cfg.prefix, before, since });
  await field.fill(code);
  await page.getByRole('button', { name: /^(continue|sign in|next)$/i }).first().click({ timeout: 10_000 });
  await page.waitForURL((u) => u.origin === cfg.origin && !u.pathname.startsWith('/login'), { timeout: 45_000 });
}

/** Is the CIS admin session alive? /admin/overview opens (admin only) without a bounce to /login. */
async function cisAlive(page) {
  await page.goto(`${CIS}/admin/overview`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1_500);
  const u = new URL(page.url());
  if (u.origin !== CIS || u.pathname !== '/admin/overview') return false;
  return page.getByRole('button', { name: 'Account menu' }).isVisible({ timeout: 15_000 }).catch(() => false);
}

/** Is the Booking session alive? The BFF's staff/me answers 200 for the E2E staff. */
async function bookingAlive(page) {
  await page.goto(`${BOOKING}/`, { waitUntil: 'domcontentloaded' });
  if (new URL(page.url()).pathname.startsWith('/login')) return false;
  const res = await page.context().request.get(`${BOOKING}/api/booking/staff/me`, { timeout: 20_000 });
  return res.status() === 200;
}

/** Partner pool managed login with password + authenticator code (the studio user; never logged). */
async function partnerLogin(page, c) {
  const { expect } = require('@playwright/test');
  const next = () => page.getByRole('button', { name: /^(next|sign in|continue|submit|verify)$/i }).first().click();
  await fillSettled(page, page.getByLabel(/email/i).first(), c.email);
  const password = page.getByLabel(/^password$/i).first();
  if (!(await password.isVisible().catch(() => false))) await next();
  await expect(password).toBeVisible({ timeout: 30_000 });
  await password.fill(c.password);
  await next();
  const code = page.getByLabel(/code/i).first();
  await expect(code).toBeVisible({ timeout: 30_000 });
  await code.fill(await crm.freshTotp(c.totpSecret));
  await next();
  const skip = page.getByRole('button', { name: /skip|not now|later/i }).first();
  if (await skip.isVisible({ timeout: 5_000 }).catch(() => false)) await skip.click();
}

/** The studio flow of AA-Partner e2e/smoke-portal/auth.setup.ts: hop until the studio dashboard renders. */
async function studioLogin(page, alreadyThere) {
  const origin = PARTNER;
  let signedIn = false;
  if (!alreadyThere) await page.goto(`${origin}/portal/dashboard`, { waitUntil: 'domcontentloaded' });
  for (let hops = 0; hops < 30; hops++) {
    await page.waitForLoadState('domcontentloaded');
    const u = new URL(page.url());
    if (u.origin !== origin) {
      if (signedIn) throw new Error(`sent to the sign-in again (${u.host}): check the studio user's password and authenticator`);
      await partnerLogin(page, crm.secretCreds(STUDIO_SECRET));
      signedIn = true;
      await page.waitForURL((x) => x.origin === origin, { timeout: 60_000 });
      continue;
    }
    if (u.pathname.startsWith('/portal/')) {
      await page.getByTestId('portal-sidebar').waitFor({ state: 'visible', timeout: 30_000 });
      return;
    }
    if (u.pathname === '/portal-access/select') {
      await page.getByTestId('studio-option').first().getByRole('button').click();
      await page.waitForURL((x) => x.pathname !== '/portal-access/select', { timeout: 30_000 });
      continue;
    }
    if (u.pathname === '/portal-access/none') throw new Error('the studio user has no active Content studio membership');
    if (u.pathname === '/select-agency') {
      await page.getByTestId('agency-option').first().getByRole('button').click();
      await page.waitForURL((x) => x.pathname !== '/select-agency', { timeout: 30_000 });
      continue;
    }
    if (signedIn && !u.pathname.startsWith('/auth/')) {
      await page.goto(`${origin}/portal/dashboard`, { waitUntil: 'domcontentloaded' });
      continue;
    }
    await page.waitForURL((x) => x.href !== u.href, { timeout: 30_000 });
  }
  throw new Error('too many hops on the way to the studio');
}

async function studioAlive(page) {
  await page.goto(`${PARTNER}/portal/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1_500);
  const u = new URL(page.url());
  if (u.origin !== PARTNER || !u.pathname.startsWith('/portal/')) return false;
  return page.getByTestId('portal-sidebar').isVisible({ timeout: 15_000 }).catch(() => false);
}

/**
 * A valid storageState file for `who` (null for public): the saved one when the app still accepts it, else a fresh
 * sign-in. Returns { file, reused }. Throws with a one-line, redacted reason.
 */
async function ensureState(who) {
  if (who === 'public') return { file: null, reused: true };
  if (who === 'crm') {
    const existed = fs.existsSync(crm.statePath('A'));
    const file = await crm.ensureState('A');
    return { file, reused: existed };
  }
  if (!['cis-admin', 'booking', 'studio'].includes(who)) throw new Error(`unknown identity ${who}`);
  const { chromium } = require('@playwright/test');
  fs.mkdirSync(WORK, { recursive: true, mode: 0o700 });
  fs.chmodSync(WORK, 0o700);
  const file = statePath(who);
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'en-US',
      ...(fs.existsSync(file) ? { storageState: file } : {}) });
    const page = await context.newPage();
    let reused = false;
    try {
      if (who === 'cis-admin') {
        reused = await cisAlive(page);
        if (!reused) {
          await staffLogin(page, STAFF['cis-admin']);
          if (!(await cisAlive(page))) throw new Error('signed in, but /admin/overview did not open (is the user still cis-admin?)');
        }
      } else if (who === 'booking') {
        reused = await bookingAlive(page);
        if (!reused) {
          await staffLogin(page, STAFF.booking);
          if (!(await bookingAlive(page))) throw new Error('signed in, but /api/booking/staff/me did not answer 200');
        }
      } else {
        reused = await studioAlive(page);
        if (!reused) {
          await studioLogin(page, true);
          if (!(await studioAlive(page))) throw new Error('signed in, but the studio dashboard did not render');
        }
      }
    } catch (e) {
      const where = (() => { try { const u = new URL(page.url()); return `${u.host}${u.pathname}`; } catch { return '?'; } })();
      throw new Error(`${who}: ${redact(String(e.message || e).split('\n')[0])} (at ${redact(where)})`);
    }
    // Written by us with mode 600 from the first byte.
    fs.writeFileSync(file, JSON.stringify(await context.storageState()), { mode: 0o600 });
    fs.chmodSync(file, 0o600);
    await context.close();
    return { file, reused };
  } finally {
    await browser.close();
  }
}

module.exports = { ensureState, statePath, CIS, BOOKING, PARTNER, STAFF_AUTH_HOST };

if (require.main === module) {
  (async () => {
    const who = process.argv.slice(2);
    for (const w of who.length ? who : ['cis-admin', 'booking', 'studio', 'crm']) {
      const r = await ensureState(w);
      console.log(`signin: ${w} ${r.reused ? 'saved session still valid' : 'signed in'}`);
    }
  })().catch((e) => { console.error(String(e.message || e).split('\n')[0]); process.exit(1); });
}
