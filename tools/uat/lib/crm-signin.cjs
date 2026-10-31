// CRM review sign-in helpers (skill aa-uat-video §2.5): agency staff sign in OUTSIDE the recorded context, the
// recording reuses the saved storageState. Cost $0 (reads two Secrets Manager values at run time, AWS read only).
//
//   const crm = require('../../lib/crm-signin.cjs');
//   const file = await crm.ensureState('A');     // A = owner, B = assistant of the synthetic agency "Lữ hành Sen Vàng"
//   node tools/uat/lib/crm-signin.cjs A B         // sign in (or check the saved session) from the shell
//
// Identities (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): A and B sign in through the partner pool's
// managed login with password + authenticator; the secret crm/dev/e2e-test-crm/sen-vang-<role> is read at run time
// with profile aa365-admin and never printed, logged or written. The storageState goes to
// work/crm/.state-<who>.json (chmod 600, gitignored) and is reused while the CRM still accepts it.
// C (the traveller) signs in on the client host with the one-time code; on Dev the code is echoed in the page hint
// (portal-hint), which the scenarios blur with TRAVELLER_MASK. readMailCode() reads a code from the e2e mailbox
// for e2e-mail addresses (the C prospects use @example.invalid, which never receives mail).
// Anonymous client-host writes are limited to 5 per minute per address: paceClientWrite() keeps them >= 14 s apart.
const { execFileSync } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

const PARTNER = (process.env.UAT_CRM_PARTNER || 'https://portal.lumiguides.it.com').replace(/\/+$/, '');
const CLIENT = (process.env.UAT_CRM_CLIENT || 'https://go-dev.lumiguides.it.com').replace(/\/+$/, '');
const BOOKING = (process.env.UAT_BOOKING || 'https://booking.lumiguides.it.com').replace(/\/+$/, '');
const PROFILE = process.env.UAT_AWS_PROFILE || 'aa365-admin';
const REGION = 'us-west-1';
const WORK = path.join(__dirname, '..', 'work', 'crm');
const IDENTITIES = {
  A: { secret: 'crm/dev/e2e-test-crm/sen-vang-owner', role: 'owner' },
  B: { secret: 'crm/dev/e2e-test-crm/sen-vang-assistant', role: 'assistant' },
};
// Blur on screen (every CRM review chunk): the echoed one-time codes and the code boxes (portal sign-in and e-sign),
// the client / portal links the agency copies once (they carry the link token), the calendar feed URL, and the real
// mailbox behind the invented agency (the connected address, the forward-in address and code, the sender line of each
// message). Data and report exports download through a blob (no link on screen). A chunk adds its own with base({ mask }).
const TRAVELLER_MASK = [
  '[data-testid="portal-hint"]', '[data-testid="portal-code"]', '[data-testid="portal-sign-hint"]',
  '[data-testid="portal-sign-code-input"]', '[data-testid="proposal-copy-links"]', '[data-testid="proposal-copy-link"]',
  '[data-testid="calendar-feed-url"]',
  '[data-testid^="mailbox-"][data-testid$="-address"]', '[data-testid="mailbox-forward-code"]',
  '[data-testid="trip-messages"] li > div:first-child > span:first-child',
];

function statePath(who) {
  return path.join(WORK, `.state-${who}.json`);
}

function creds(who) {
  const id = IDENTITIES[who];
  if (!id) throw new Error(`unknown identity ${who}`);
  return secretCreds(id.secret);
}

/**
 * { email, password, totpSecret } of a partner-pool e2e user from its Secrets Manager JSON (read only, profile
 * UAT_AWS_PROFILE or aa365-admin). Also used by lib/signin.cjs for the Content studio user. Never printed.
 */
function secretCreds(secretId) {
  const raw = execFileSync('aws', ['secretsmanager', 'get-secret-value', '--secret-id', secretId, '--profile', PROFILE,
    '--region', REGION, '--query', 'SecretString', '--output', 'text'],
  { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 30_000 });
  let s;
  try {
    s = JSON.parse(raw);
  } catch {
    throw new Error(`secret ${secretId} is not JSON`); // never echo the value (JSON.parse quotes the input)
  }
  if (!s.email || !s.password || !s.totp_secret) throw new Error(`secret ${secretId} lacks email, password or totp_secret`);
  return { email: s.email, password: s.password, totpSecret: s.totp_secret };
}

// RFC 6238 (SHA-1, 6 digits, 30 s), the partner pool's authenticator. Cognito refuses a code replayed in the same
// step, so the last step handed out per secret is kept in a small file keyed by a hash of the secret.
function base32(secret) {
  const A = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  let bits = '';
  for (const ch of secret.replace(/[\s=-]/g, '').toUpperCase()) {
    const v = A.indexOf(ch);
    if (v < 0) throw new Error('not a base32 secret');
    bits += v.toString(2).padStart(5, '0');
  }
  const out = [];
  for (let i = 0; i + 8 <= bits.length; i += 8) out.push(parseInt(bits.slice(i, i + 8), 2));
  return Buffer.from(out);
}

function totp(secret, at = Date.now()) {
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(at / 30_000)));
  const mac = crypto.createHmac('sha1', base32(secret)).update(counter).digest();
  const o = mac[mac.length - 1] & 0x0f;
  return String((mac.readUInt32BE(o) & 0x7fffffff) % 1_000_000).padStart(6, '0');
}

async function freshTotp(secret) {
  const key = crypto.createHash('sha256').update(`aa-e2e-totp:${secret.replace(/[\s=-]/g, '').toUpperCase()}`).digest('hex');
  const file = path.join(os.tmpdir(), `aa-e2e-totp-${key.slice(0, 16)}`);
  for (;;) {
    const at = Date.now();
    const step = Math.floor(at / 30_000);
    let last = -1;
    try { last = parseInt(fs.readFileSync(file, 'utf8'), 10); } catch { /* none yet */ }
    const left = (step + 1) * 30_000 - at;
    if (step > last && left >= 5_000) {
      fs.writeFileSync(file, String(step), { mode: 0o600 });
      return totp(secret, at);
    }
    await new Promise((r) => setTimeout(r, left + 200));
  }
}

async function next(page) {
  await page.getByRole('button', { name: /^(next|sign in|continue|submit|verify)$/i }).first().click();
}

/** Managed login (partner pool): e-mail, password, authenticator code; skip the passkey offer; pick the agency. */
async function managedLogin(page, who) {
  const { expect } = require('@playwright/test');
  const c = creds(who);
  const email = page.getByLabel(/email/i).first();
  await expect(email).toBeVisible({ timeout: 30_000 });
  await email.fill(c.email);
  const password = page.getByLabel(/^password$/i).first();
  if (!(await password.isVisible().catch(() => false))) await next(page);
  await expect(password).toBeVisible({ timeout: 30_000 });
  await password.fill(c.password);
  await next(page);
  const code = page.getByLabel(/code/i).first();
  await expect(code).toBeVisible({ timeout: 30_000 });
  await code.fill(await freshTotp(c.totpSecret));
  await next(page);
  const skip = page.getByRole('button', { name: /skip|not now|later/i }).first();
  if (await skip.isVisible({ timeout: 5_000 }).catch(() => false)) await skip.click();
  await page.waitForURL((u) => u.origin === PARTNER, { timeout: 30_000 });
}

async function landOnAgency(page) {
  if (new URL(page.url()).pathname === '/select-agency') {
    await page.getByTestId('agency-option').first().getByRole('button').click();
    await page.waitForURL((u) => u.pathname !== '/select-agency', { timeout: 30_000 });
  }
}

function onPartnerApp(page) {
  const u = new URL(page.url());
  return u.origin === PARTNER && !/\/(login|signin|sign-in)/.test(u.pathname) && u.pathname !== '/signed-out';
}

/**
 * A valid storageState file for identity A or B: the saved one when the CRM still accepts it, else a fresh managed
 * login. Runs its own headless Chromium, closed before returning (one browser at a time). Returns the file path.
 * `file` (default work/crm/.state-<who>.json) lets the dry run keep its own session file apart from the review set.
 */
async function ensureState(who, file = statePath(who)) {
  const { chromium } = require('@playwright/test');
  const dir = path.dirname(file);
  fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
  fs.chmodSync(dir, 0o700);
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'en-US',
      ...(fs.existsSync(file) ? { storageState: file } : {}) });
    const page = await context.newPage();
    await page.goto(`${PARTNER}/pipeline`, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {});
    let reused = onPartnerApp(page);
    if (reused) {
      await landOnAgency(page);
      const me = await bffCall(page, 'GET', 'members');
      reused = me.status === 200;
    }
    if (!reused) {
      if (new URL(page.url()).origin === PARTNER) {
        const go = page.getByRole('link', { name: /sign in/i }).or(page.getByRole('button', { name: /sign in/i })).first();
        if (await go.isVisible().catch(() => false)) await go.click();
      }
      await managedLogin(page, who);
      await landOnAgency(page);
      await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {});
      if (!onPartnerApp(page)) throw new Error(`sign-in of ${who} did not land on the CRM`);
    }
    // Written by us with mode 600 from the first byte (storageState({ path }) would create it 644 first).
    const state = await context.storageState();
    fs.writeFileSync(file, JSON.stringify(state), { mode: 0o600 });
    fs.chmodSync(file, 0o600);
    await context.close();
    console.log(`crm-signin: ${who} (${IDENTITIES[who].role}) ${reused ? 'saved session still valid' : 'signed in'}`);
    return file;
  } finally {
    await browser.close();
  }
}

/** Same-origin call to the CRM BFF from a signed-in partner page: { status, data }. */
async function bffCall(page, method, p, body) {
  return page.evaluate(async ({ method, p, body }) => {
    const res = await fetch(`/bff/${p}`, {
      method,
      headers: body === undefined ? { Accept: 'application/json' } : { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: 'same-origin',
    });
    const text = await res.text();
    let data = text;
    try { data = JSON.parse(text); } catch { /* not JSON */ }
    return { status: res.status, data };
  }, { method, p, body });
}

// Anonymous client-host writes (intake form, proposal accept, portal code / session): 5 per minute per address.
let lastClientWrite = 0;
async function paceClientWrite(minGapMs = 14_000) {
  const wait = lastClientWrite + minGapMs - Date.now();
  if (wait > 0) await new Promise((r) => setTimeout(r, wait));
  lastClientWrite = Date.now();
}

/** Record every 429 the page gets from the CRM hosts; assertNo429(list) fails the step when one was seen. */
function watch429(page) {
  const seen = [];
  page.on('response', (r) => {
    if (r.status() !== 429) return;
    const u = new URL(r.url());
    if (u.origin === CLIENT || u.origin === PARTNER) seen.push(`${r.request().method()} ${u.pathname.replace(/[A-Za-z0-9_-]{40,}/g, '<token>')}`);
  });
  return seen;
}
function assertNo429(seen) {
  if (seen.length) throw new Error(`rate limited (429): ${seen.join(', ')}`);
}

/** The traveller's one-time code from the Dev echo in the hint (portal-hint). Never logged. */
async function echoedCode(page) {
  const text = (await page.getByTestId('portal-hint').textContent()) || '';
  const m = text.match(/\b(\d{6})\b/);
  if (!m) throw new Error('no echoed code in the portal hint (PORTAL_OTP_DEV_ECHO off?)');
  return m[1];
}

/**
 * The newest sign-in code mailed to an e2e-mail `recipient` after `sinceMs`, from the e2e mailbox bucket (read only,
 * same approach as the AA-Partner e2e helpers). Never logged.
 */
async function readMailCode(recipient, sinceMs, timeoutMs = 90_000) {
  const aws = (args) => execFileSync('aws', [...args, '--profile', PROFILE, '--region', REGION, '--output', 'json'],
    { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 20_000, maxBuffer: 16 * 1024 * 1024 });
  const account = JSON.parse(aws(['sts', 'get-caller-identity'])).Account;
  const bucket = `aa-cis-dev-e2e-mail-${account}`;
  const needle = recipient.toLowerCase();
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const out = aws(['s3api', 'list-objects-v2', '--bucket', bucket, '--prefix', 'inbound/']);
    const keys = ((out.trim() ? JSON.parse(out) : {}).Contents || [])
      .filter((o) => Date.parse(o.LastModified) >= sinceMs - 5_000)
      .sort((x, y) => Date.parse(y.LastModified) - Date.parse(x.LastModified));
    for (const { Key } of keys) {
      const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'uat-mail-'));
      try {
        aws(['s3api', 'get-object', '--bucket', bucket, '--key', Key, path.join(dir, 'm.eml')]);
        const raw = fs.readFileSync(path.join(dir, 'm.eml'), 'utf8');
        const head = raw.split(/\r?\n\r?\n/)[0].replace(/\r?\n[ \t]+/g, ' ').toLowerCase();
        if (!head.split(/\r?\n/).some((l) => /^(to|delivered-to|x-original-to):/.test(l) && l.includes(needle))) continue;
        const body = raw.replace(/=\r?\n/g, '');
        const code = (/(?:code|mã)[^0-9]{0,80}(\d{6,8})/i.exec(body) || /\b(\d{6,8})\b/.exec(body) || [])[1];
        if (code) return code;
      } finally {
        fs.rmSync(dir, { recursive: true, force: true });
      }
    }
    await new Promise((r) => setTimeout(r, 3_000));
  }
  throw new Error('no sign-in code mail arrived in time');
}

module.exports = {
  PARTNER, CLIENT, BOOKING, WORK, IDENTITIES, TRAVELLER_MASK,
  ensureState, statePath, bffCall, paceClientWrite, watch429, assertNo429, echoedCode, readMailCode, totp,
  secretCreds, freshTotp, PROFILE, REGION,
};

if (require.main === module) {
  (async () => {
    for (const who of process.argv.slice(2).length ? process.argv.slice(2) : ['A']) await ensureState(who);
  })().catch((e) => { console.error(String(e.message || e).split('\n')[0]); process.exit(1); });
}
