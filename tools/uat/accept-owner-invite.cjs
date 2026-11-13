// Accept a Content studio OWNER invitation as an E2E person who already has a partner-pool account (AA-1086, root
// docs/ops/runbooks/pilot-rehearsal.md step 2): the tech lead invites the owner on CIS Tenant 360 > Members > Invite
// (role owner), the AA system mail lands in the e2e mailbox, and this script claims it, signs the owner in (own password
// + authenticator code from the identity's secret) and accepts. Then it checks that the studio opens on the agency
// (lib/signin.cjs ensureState, polled while the activation is "being set up") and saves that session for the REH
// scenarios. Unrecorded, headless, no screenshot, no trace: the join pages carry the invitation token.
//
//   node tools/uat/accept-owner-invite.cjs --since 2026-11-13T09:00:00Z            identity studio-rehearsal
//   node tools/uat/accept-owner-invite.cjs --since <ISO> --identity studio-rehearsal --ready-min 5
//
// --since = a time taken just BEFORE the invitation was sent (only newer mail is read). Reads: the identity's secret
// (Secrets Manager, in memory only) and the e2e mailbox (S3 inbound/, read only), profile UAT_AWS_PROFILE or
// aa365-admin. Writes on Dev: the invitation claim and accept of that one person (no model call, cost $0). Same join
// steps as AA-Partner e2e/phase2 (claim -> sign in -> accept) but for an EXISTING account: a claim that shows a
// one-time password means the person has no account yet, and the script stops (the CRM seed's E2E users make it; the
// phase 2 spec is the path for a brand-new invitee). The link, the token, the address and the codes are never printed.
// Exit: 0 accepted and the studio opens on the agency | 1 any failure (one-line reason).
'use strict';
const fs = require('fs');

// Identities this script may accept an owner invitation for: the E2E owner of a synthetic agency only.
const OWNER_INVITEES = {
  'studio-rehearsal': () => {
    const reh = require('./lib/rehearsal.cjs');
    return { secret: reh.secretId(), tenantName: reh.TENANT.name };
  },
};
// The join link must point at the AA Dev hosts: the token never goes anywhere else.
const JOIN_HOST = /(^|\.)lumiguides\.it\.com$/;

function parseArgs(argv) {
  const out = { identity: 'studio-rehearsal', since: null, readyMin: 5 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const val = () => {
      if (i + 1 >= argv.length) throw new Error(`${a} needs a value`);
      return argv[++i];
    };
    if (a === '--identity') out.identity = val();
    else if (a === '--since') out.since = val();
    else if (a === '--ready-min') out.readyMin = Number(val());
    else throw new Error(`unknown argument ${a}`);
  }
  if (!OWNER_INVITEES[out.identity]) throw new Error(`--identity must be one of ${Object.keys(OWNER_INVITEES).join(', ')}`);
  const t = out.since ? Date.parse(out.since) : NaN;
  if (!Number.isFinite(t)) throw new Error('--since <ISO time taken just before the invitation was sent> is required');
  if (t > Date.now() + 60_000) throw new Error('--since is in the future');
  out.since = new Date(t);
  if (!(out.readyMin > 0 && out.readyMin <= 30)) throw new Error('--ready-min must be between 1 and 30');
  return out;
}

/** The join link's origin when it is an https AA Dev host with the /join path; throws otherwise (never echoes it). */
function joinOrigin(link) {
  let u;
  try { u = new URL(link); } catch { throw new Error('the invitation link is not a URL'); }
  if (u.protocol !== 'https:' || !JOIN_HOST.test(u.hostname) || u.pathname !== '/join') {
    throw new Error('the invitation link does not point at the AA join page');
  }
  return u.origin;
}

/** Claim -> sign in (existing account) -> accept, in an unrecorded browser. Returns "activated" or "accepted". */
async function claimAndAccept(link, creds) {
  const { chromium, expect } = require('@playwright/test');
  const { partnerLogin } = require('./lib/signin.cjs');
  const origin = joinOrigin(link);
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'en-US' });
    const page = await context.newPage();
    await page.goto(link, { waitUntil: 'domcontentloaded' });
    await page.waitForURL(`${origin}/join/invite`, { timeout: 30_000 });
    const error = page.getByTestId('join-error');
    if (await error.isVisible().catch(() => false)) throw new Error(`the invitation page says: ${(await error.innerText()).trim()}`);
    await page.getByTestId('join-open').click();
    await expect(page.getByTestId('join-claimed').or(error).first()).toBeVisible({ timeout: 30_000 });
    if (await error.isVisible().catch(() => false)) throw new Error(`the claim was refused: ${(await error.innerText()).trim()}`);
    const shown = ((await page.getByTestId('join-email').textContent()) || '').trim().toLowerCase();
    if (shown !== creds.email.toLowerCase()) throw new Error('the invitation is for another address than the identity');
    if (await page.getByTestId('join-temporary-password').isVisible().catch(() => false)) {
      throw new Error('the invitee has no partner account yet (a one-time password was issued): create the E2E users '
        + 'with the CRM seed first, or use AA-Partner e2e/phase2 for a new invitee');
    }
    await page.getByTestId('join-sign-in').click();
    let signedIn = false;
    for (let hops = 0; hops < 20; hops++) {
      await page.waitForLoadState('domcontentloaded');
      const u = new URL(page.url());
      if (u.origin === origin && u.pathname === '/join/accept') break;
      if (u.origin !== origin) {
        if (signedIn) throw new Error(`sent to the sign-in again (${u.host}): check the identity's password and authenticator`);
        await partnerLogin(page, creds);
        signedIn = true;
        await page.waitForURL((x) => x.origin === origin, { timeout: 60_000 });
        continue;
      }
      await page.waitForURL((x) => x.href !== u.href, { timeout: 30_000 });
    }
    if (new URL(page.url()).pathname !== '/join/accept') throw new Error('the sign-in did not come back to the accept page');
    await page.getByTestId('join-accept').click();
    await page.waitForURL((x) => x.origin === origin && x.pathname === '/join/accept' && x.searchParams.has('studio'), { timeout: 30_000 });
    const status = new URL(page.url()).searchParams.get('studio') === 'activated' ? 'activated' : 'accepted';
    await expect(page.getByTestId('join-studio-status')).toContainText(status === 'activated' ? /access is ready/i : /being set up/i);
    await context.close();
    return status;
  } finally {
    await browser.close();
  }
}

/** The studio opens on the agency for `identity` (fresh sign-in, saved session); polls while the activation lands. */
async function studioOpens(identity, readyMs) {
  const { ensureState, statePath } = require('./lib/signin.cjs');
  fs.rmSync(statePath(identity), { force: true }); // a session from before the membership would hide it
  const until = Date.now() + readyMs;
  for (;;) {
    try {
      return await ensureState(identity);
    } catch (e) {
      const msg = String(e.message || e);
      if (!/no active Content studio membership/.test(msg) || Date.now() > until) throw e;
      await new Promise((r) => setTimeout(r, 20_000));
    }
  }
}

async function main(argv) {
  const args = parseArgs(argv);
  const who = OWNER_INVITEES[args.identity]();
  const crm = require('./lib/crm-signin.cjs');
  const mailbox = require('./lib/mailbox.cjs');
  const creds = crm.secretCreds(who.secret); // { email, password, totpSecret }, in memory only
  const link = await mailbox.waitForInviteLink({ recipient: creds.email, since: args.since });
  const status = await claimAndAccept(link, creds);
  console.log(JSON.stringify({ event: 'owner_invite_accepted', identity: args.identity, studio_status: status }));
  await studioOpens(args.identity, args.readyMin * 60_000);
  console.log(JSON.stringify({ event: 'owner_studio_open', identity: args.identity, tenant: who.tenantName }));
}

module.exports = { parseArgs, joinOrigin, OWNER_INVITEES };

if (require.main === module) {
  main(process.argv.slice(2)).catch((e) => {
    const { redact } = require('./lib/dryrun-core.cjs');
    console.error(`accept-owner-invite: ${redact(String(e.message || e).split('\n')[0])}`);
    process.exit(1);
  });
}
