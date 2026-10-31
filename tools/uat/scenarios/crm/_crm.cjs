// Shared helpers of the CRM review scenarios (crm-rev-*.cjs, prep.cjs, cleanup.cjs); not a scenario itself.
// Plan: docs/audits/2026-10-31-S261-crm-progress-video-plan §3-5. Identities: A = owner, B = assistant of the synthetic
// agency "Lữ hành Sen Vàng" (signed in outside the recording, lib/crm-signin.cjs), C = an invented traveller on the client
// host (@example.invalid, per-run suffix), D = Booking E2E staff (read only). Dev only, invented data, no LLM, $0.
const crm = require('../../lib/crm-signin.cjs');
const st = require('../../lib/crm-state.cjs');

const DESKTOP = { width: 1440, height: 900 };
const PHONE = { width: 390, height: 844 };
const REAL_ADDRESS = '[A-Za-z0-9._%+-]+@(?![A-Za-z0-9.-]*\\.invalid\\b)[A-Za-z0-9-]+(\\.[A-Za-z0-9-]+)*\\.[A-Za-z]{2,}';

/** The fields every CRM review scenario shares; `who` signs in before the browser starts (never recorded). */
function base({ id, title, titleVi, who = 'A', viewport = DESKTOP, mask = [] }) {
  const phone = viewport === PHONE;
  const sc = {
    id,
    app: 'crm',
    title,
    ...(titleVi ? { title_vi: titleVi } : {}),
    baseURL: crm.PARTNER,
    viewport,
    // A phone chunk is a real mobile context (mobile meta viewport, touch), not only a narrow desktop window.
    ...(phone ? { isMobile: true, hasTouch: true } : {}),
    mask: [...crm.TRAVELLER_MASK, ...mask],
    // Old Dev test rows carry internal issue ids in names ("E2E AA966 ..."): never on screen in a review video.
    // Any e-mail address that is not an invented one (*.invalid) is blurred wherever it shows as text: the agency's
    // real mailbox in sender lines and quoted "On ... <address> wrote:" lines, a staff sign-in address.
    blurText: ['\\bAA-?\\d{3,4}\\b', REAL_ADDRESS],
    scrollBlock: 'center', // the CRM shell has a sticky top bar
    meta: {},
  };
  if (who) {
    sc.prepare = async () => {
      sc.storageState = await crm.ensureState(who);
    };
  }
  return sc;
}

/** The CRM API's deployed git sha, recorded at the start and the end of a chunk; a deploy in between fails the chunk. */
async function sha(page, sc, which) {
  const res = await page.request.get(`${crm.PARTNER}/crm/health`);
  if (res.status() !== 200) throw new Error(`/crm/health answered ${res.status()}`);
  const body = await res.json();
  if (body.status !== 'ok') throw new Error(`/crm/health status ${body.status}`);
  sc.meta[`git_sha_${which}`] = body.git_sha;
  if (which === 'end' && sc.meta.git_sha_start && sc.meta.git_sha_start !== body.git_sha) {
    throw new Error(`the CRM was redeployed during the chunk (${sc.meta.git_sha_start.slice(0, 7)} -> ${body.git_sha.slice(0, 7)}): record it again`);
  }
  return body.git_sha;
}

/** Open a CRM page and check the session held (no managed-login redirect). */
async function open(page, h, p, testId) {
  await h.goto(p);
  await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {});
  const u = new URL(page.url());
  if (u.origin !== crm.PARTNER || /sign-?in|login|signed-out/.test(u.pathname)) {
    throw new Error(`not signed in on the CRM (landed on ${u.host}${u.pathname}); run node tools/uat/lib/crm-signin.cjs A`);
  }
  if (testId) await h.expect(page.getByTestId(testId).first()).toBeVisible({ timeout: 20_000 });
}

/** Same-origin BFF call; GETs work from any page (context cookies), writes only from a CRM page (CSRF origin). */
async function bff(page, method, p, body) {
  if (new URL(page.url()).origin === crm.PARTNER) return crm.bffCall(page, method, p, body);
  if (method !== 'GET') throw new Error(`BFF write ${p} needs a CRM page`);
  const res = await page.request.get(`${crm.PARTNER}/bff/${p}`, { headers: { Accept: 'application/json' } });
  return { status: res.status(), data: await res.json().catch(() => null) };
}

async function bffOk(page, method, p, body, expected) {
  const r = await bff(page, method, p, body);
  const ok = expected ? [].concat(expected).includes(r.status) : r.status < 300;
  if (!ok) throw new Error(`${method} ${p.split('?')[0].replace(/[0-9a-f]{8}-[0-9a-f-]{27}/g, '<id>')} answered ${r.status} ${JSON.stringify(r.data && r.data.detail !== undefined ? r.data.detail : '').slice(0, 120)}`);
  return r.data;
}

/** The board card of the trip whose lead is `leadName`, polled until the intake job made it (about a minute). */
async function waitForCard(page, leadName, timeoutMs = 120_000) {
  const until = Date.now() + timeoutMs;
  while (Date.now() < until) {
    const pl = await bff(page, 'GET', 'pipeline');
    for (const s of (pl.data && pl.data.stages) || []) for (const c of s.cards || []) if (c.lead_name === leadName) return c;
    await page.waitForTimeout(4_000);
  }
  throw new Error(`no board card for "${leadName}" after ${timeoutMs / 1000} s`);
}

/** The inquiry form answers of an invented prospect (C). */
function prospect(s, key, first, last, extra = {}) {
  const tag = st.runTag(s);
  return { name: `${first} ${last} ${tag}`, email: `${first}.${last}.${key}.${tag}@example.invalid`.toLowerCase(), ...extra };
}

/** Anonymous inquiry through the public API from a client-host page (prep only; the recorded R03 uses the form). */
async function submitInquiryApi(page, formKey, p) {
  if (new URL(page.url()).origin !== crm.CLIENT) await page.goto(`${crm.CLIENT}/c/f/${formKey}`, { waitUntil: 'domcontentloaded' });
  await crm.paceClientWrite();
  const body = {
    destinations: p.destinations || ['vietnam'], nights: p.nights || 3, adults: p.adults || 2, budget_band: p.budget_band || '2000_3500',
    trip_style: p.trip_style || 'balanced', name: p.name, email: p.email, consent_contact: true, consent_marketing: false,
    client_submission_id: require('crypto').randomUUID(),
  };
  const r = await page.evaluate(async ({ key, body }) => {
    const res = await fetch(`/crm/public/v1/forms/${key}/submissions`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(body),
    });
    return res.status;
  }, { key: formKey, body });
  if (r !== 202) throw new Error(`inquiry submission answered ${r}`);
}

/**
 * Type into a field like a person (fill at once in fast mode); `loc` must be an input or textarea. A native date /
 * time field is filled (typing "1986-04-12" into a Chromium date field does not give that ISO value).
 */
async function type(page, h, loc, text) {
  await h.click(loc);
  const native = /^(date|datetime-local|time|month|week)$/.test((await loc.getAttribute('type')) || '');
  await loc.fill('');
  if (h.fast || native) await loc.fill(text);
  else await loc.pressSequentially(text, { delay: 35 });
  await h.expect(loc).toHaveValue(text);
}

/** Choose a <select> option (value or { label }) after moving the cursor to it. */
async function choose(h, loc, option) {
  await h.hover(loc);
  await loc.selectOption(option);
}

/**
 * A step found its work already done by an earlier run. Fine for a --fast rehearsal (it skips the action); a recorded
 * take would narrate an action that is not on screen, so it stops and asks for fresh data.
 */
function reuse(h, what, fresh = 'prep with UAT_CRM_NEW_RUN=1, then the chunks in order') {
  if (!h.fast) throw new Error(`${what} already exists: a recorded take needs a fresh run (${fresh})`);
}

/** Days from today as an ISO date (UTC; enough for trip dates weeks ahead). */
const day = (n, from = new Date()) => new Date(from.getTime() + n * 86_400_000).toISOString().slice(0, 10);

module.exports = { crm, st, DESKTOP, PHONE, REAL_ADDRESS, base, sha, open, bff, bffOk, waitForCard, prospect, submitInquiryApi, type, choose, day, reuse };
