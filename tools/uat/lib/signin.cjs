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
//   studio-editor  Content studio EDITOR of the E2E tenant (AA-855; the A10b-1 invitee e2e-test-studio-editor@), same
//              flow, secret crm/dev/e2e-test-studio/editor (UAT_STUDIO_EDITOR_SECRET overrides). It CAN write: only
//              write scenarios use it (PRT-02, PRT-06). No secret yet = BLOCKED with that reason, not a crash.
//   studio-audit  the partner E2E person who is an EDITOR in the four synthetic audit tenants (AA-855 W-01..W-04;
//              lib/studio-audit.cjs): secret crm/dev/e2e-test-crm/harbour-lights-owner (UAT_STUDIO_AUDIT_SECRET), same
//              partner flow; the studio opens on THIS run's audit tenant (env UAT_STUDIO_TENANT, default
//              audit-atlas-hearth), chosen on the studio chooser by its invented display name and checked through
//              GET /api/tenant/me. One state file per audit tenant. It CAN write: only the write scenarios use it.
//   studio-rehearsal  the E2E OWNER of the synthetic pilot rehearsal agency pilot-rehearsal-01 (AA-1086 REH-*;
//              lib/rehearsal.cjs): secret crm/dev/e2e-test-crm/pilot-rehearsal-01-owner (UAT_STUDIO_REHEARSAL_SECRET), same
//              partner flow; the studio opens on "E2E Pilot Rehearsal Travel". Needs the owner's Content studio
//              membership (runbook step 2: the tech lead's owner invitation, accepted from the e2e inbox by
//              tools/uat/accept-owner-invite.cjs). It CAN write and pay: only the REH write scenarios use it.
//   crm        Owner of the invented agency of the CRM review set: lib/crm-signin.cjs identity A, with its own state
//              file (work/dryrun/.state-crm.json, never the review set's). This account CAN write (the CRM has no
//              read-only role yet): the runner leaves its scenarios out unless --include-writable (dryrun-core.cjs).
// Secrets and codes are read at run time and never printed, logged or written; the state files go to
// work/dryrun/.state-<identity>.json (chmod 600, gitignored). No screenshot or trace is ever taken here.
'use strict';
const fs = require('fs');
const path = require('path');
const crm = require('./crm-signin.cjs');
const mailbox = require('./mailbox.cjs');
const { redact } = require('./dryrun-core.cjs');
const studioAudit = require('./studio-audit.cjs');
const rehearsal = require('./rehearsal.cjs');

const CIS = (process.env.UAT_CIS_ADMIN || 'https://aa-cis.lumiguides.it.com').replace(/\/+$/, '');
const BOOKING = crm.BOOKING;
const PARTNER = crm.PARTNER;
const STAFF_AUTH_HOST = 'staff-auth.lumiguides.it.com';
const WORK = path.join(__dirname, '..', 'work', 'dryrun');
const STUDIO_SECRETS = {
  studio: process.env.UAT_STUDIO_SECRET || 'crm/dev/e2e-test-studio/viewer',
  'studio-editor': process.env.UAT_STUDIO_EDITOR_SECRET || 'crm/dev/e2e-test-studio/editor',
  'studio-audit': studioAudit.secretId(),
  'studio-rehearsal': rehearsal.secretId(),
};
const STUDIO_IDENTITIES = Object.keys(STUDIO_SECRETS);

const STAFF = {
  'cis-admin': { origin: CIS, email: 'e2e-cis-admin@e2e-mail.lumiguides.it.com', prefix: 'inbound-admin/' },
  booking: { origin: BOOKING, email: 'e2e-booking@e2e-mail.lumiguides.it.com', prefix: 'inbound/' },
};

function statePath(who) {
  // studio-audit: one session per audit tenant (the studio cookies name the tenant they were exchanged for).
  if (who === 'studio-audit') return path.join(WORK, `.state-studio-audit-${studioAudit.auditTenant().slug}.json`);
  return path.join(WORK, `.state-${who}.json`);
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

/** The studio option of `tenantName` on the chooser (/portal-access/select), never just the first one. */
async function chooseStudio(page, tenantName) {
  if (!tenantName) {
    await page.getByTestId('studio-option').first().getByRole('button').click();
    return;
  }
  const option = page.getByTestId('studio-option').filter({ has: page.getByText(tenantName, { exact: true }) });
  await option.first().waitFor({ state: 'visible', timeout: 30_000 });
  if ((await option.count()) !== 1) throw new Error('the studio chooser does not list the audit tenant exactly once');
  await option.getByRole('button').click();
}

/** The studio flow of AA-Partner e2e/smoke-portal/auth.setup.ts: hop until the studio dashboard renders. */
async function studioLogin(page, alreadyThere, creds, tenantName = null) {
  const origin = PARTNER;
  let signedIn = false;
  if (!alreadyThere) await page.goto(`${origin}/portal/dashboard`, { waitUntil: 'domcontentloaded' });
  for (let hops = 0; hops < 30; hops++) {
    await page.waitForLoadState('domcontentloaded');
    const u = new URL(page.url());
    if (u.origin !== origin) {
      if (signedIn) throw new Error(`sent to the sign-in again (${u.host}): check the studio user's password and authenticator`);
      await partnerLogin(page, creds);
      signedIn = true;
      await page.waitForURL((x) => x.origin === origin, { timeout: 60_000 });
      continue;
    }
    if (u.pathname.startsWith('/portal/')) {
      await page.getByTestId('portal-sidebar').waitFor({ state: 'visible', timeout: 30_000 });
      return;
    }
    if (u.pathname === '/portal-access/select') {
      await chooseStudio(page, tenantName);
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

/** The active studio tenant's display name (GET /api/tenant/me, the pilot guard's own read), or null. */
async function studioTenantName(page) {
  const res = await page.context().request.get(`${PARTNER}/api/tenant/me`, { headers: { Accept: 'application/json' }, timeout: 20_000, maxRedirects: 0 });
  if (res.status() !== 200) return null;
  const body = await res.json().catch(() => null);
  return body && typeof body.tenant_name === 'string' ? body.tenant_name : null;
}

/**
 * Put the signed-in studio on `tenantName`: nothing when it is already there, else the chooser (the person holds
 * several studio memberships; the chooser exchanges the partner session for the chosen tenant). Throws when the
 * studio does not land on it.
 */
async function ensureStudioTenant(page, tenantName) {
  if ((await studioTenantName(page)) === tenantName) return;
  await page.goto(`${PARTNER}/portal-access/select?next=${encodeURIComponent('/portal/dashboard')}`, { waitUntil: 'domcontentloaded' });
  if (new URL(page.url()).pathname !== '/portal-access/select') throw new Error('the studio chooser did not open (one membership only?)');
  await chooseStudio(page, tenantName);
  await page.waitForURL((x) => x.pathname.startsWith('/portal/'), { timeout: 30_000 });
  await page.getByTestId('portal-sidebar').waitFor({ state: 'visible', timeout: 30_000 });
  if ((await studioTenantName(page)) !== tenantName) throw new Error('the studio did not open on the audit tenant');
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
    const target = statePath('crm');
    const existed = fs.existsSync(target);
    let file;
    try {
      file = await crm.ensureState('A', target);
    } catch (e) {
      throw new Error(`crm: ${redact(String(e.message || e).split('\n')[0])}`);
    }
    return { file, reused: existed };
  }
  if (!['cis-admin', 'booking', ...STUDIO_IDENTITIES].includes(who)) throw new Error(`unknown identity ${who}`);
  // A studio identity's secret is read before any browser starts: a missing one (the editor not enrolled yet) is a
  // clear BLOCKED reason, not a crash half-way through a sign-in. Never printed.
  let studioCreds = null;
  if (STUDIO_IDENTITIES.includes(who) && !fs.existsSync(statePath(who))) {
    try {
      studioCreds = crm.secretCreds(STUDIO_SECRETS[who]);
    } catch (e) {
      throw new Error(`${who}: BLOCKED: ${redact(String(e.message || e).split('\n')[0])}`);
    }
  }
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
        const tenantName = who === 'studio-audit' ? studioAudit.auditTenant().name
          : who === 'studio-rehearsal' ? rehearsal.TENANT.name : null;
        reused = await studioAlive(page);
        if (!reused) {
          if (!studioCreds) studioCreds = crm.secretCreds(STUDIO_SECRETS[who]);
          await studioLogin(page, true, studioCreds, tenantName);
          if (!(await studioAlive(page))) throw new Error('signed in, but the studio dashboard did not render');
        }
        if (tenantName) await ensureStudioTenant(page, tenantName);
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

module.exports = { ensureState, statePath, partnerLogin, CIS, BOOKING, PARTNER, STAFF_AUTH_HOST, STUDIO_SECRETS };

if (require.main === module) {
  (async () => {
    const who = process.argv.slice(2);
    for (const w of who.length ? who : ['cis-admin', 'booking', 'studio', 'crm']) {
      const r = await ensureState(w);
      console.log(`signin: ${w} ${r.reused ? 'saved session still valid' : 'signed in'}`);
    }
  })().catch((e) => { console.error(String(e.message || e).split('\n')[0]); process.exit(1); });
}
