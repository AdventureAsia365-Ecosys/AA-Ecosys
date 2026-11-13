// Shared helpers of the pilot rehearsal CRM scenarios (REH-06 .. REH-10b; runbook docs/ops/runbooks/pilot-rehearsal.md
// steps 6, 7, 8 and 10; skill aa-uat-video). Not a scenario itself (the leading _ keeps it out of the catalogue tests).
//
// Identities (signed in outside the recording, lib/signin.cjs):
//   crm-rehearsal        owner of the synthetic agency pilot-rehearsal-01 "E2E Pilot Rehearsal Travel" (crm-signin RO)
//   crm-rehearsal-agent  its agent (crm-signin RA)
//   crm-staff            the AA staff console's E2E user (root ADR 0006a A10c), read only here (REH-10b)
// The pilot guard pins both rehearsal identities to pilot-rehearsal-01 (lib/pilot-guard.cjs REHEARSAL_IDENTITIES): a
// session on any other agency stops the run before the browser opens. The traveller has no account: the client and
// portal links are the credential; those steps run in the owner's browser context on the client host (no cookie of
// the agency host goes there).
//
// Writes: every scenario is built with rw() (lib/uat-page.cjs): the browser guard stays on and only the scenario's own
// allowWrites (BFF paths of the agency host, public paths of the client host) reach the app. No LLM call, no AI button.
// Cost $0.
//
// Hand-off from the orchestrator (before REH-06), env first, else work/rehearsal/handoff.json (gitignored):
//   UAT_REH_TOUR_X     / tour_x      the CIS source id of tour X (runbook "Tour X": a sellable trip plan with an open
//                                    fixed departure); the CRM looks it up through AA (GET /bff/aa/products/<id>)
//   UAT_REH_LEAD_NAME  / lead_name   the invented traveller name the TripPlanner step 6 sent to the agency
//   UAT_REH_TRAVELLER_EMAIL / traveller_email   the invented address the TripPlanner step 6 sent (the TripPlanner
//                                    group's variable and default, rehearsal.traveller@example.invalid)
// Agency setup on the fresh pilot-rehearsal-01 seed (scenarios/crm/REHEARSAL.md): the seed adds the agency and its
// members only. Before REH-06, REH-02b-agency-setup (owner, in the UI) saves the bank-transfer instructions and
// publishes booking terms and a waiver; REH-08b step 3 and REH-10 step 5 fail without them.
// Mail guard: before any step that makes the CRM mail the traveller (proposal send, the deposit's portal invites, the
// portal link, the portal sign-in and signing codes), checkTraveller() proves the trip's lead address is the hand-off
// address and that it is on an invented domain (*.invalid, or the E2E mailbox domain), and that no other traveller of
// the trip has an address; otherwise the step stops before the click.
// Run state between the scenarios: work/rehearsal/crm.json (ids only). The client and portal links: work/rehearsal/
// .crm-secrets.json (chmod 600), each kept with its trip id; never in a log, a caption or result.json.
'use strict';
const fs = require('fs');
const path = require('path');
const crm = require('../../lib/crm-signin.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const { step, DESKTOP, PHONE } = require('../../lib/dryrun-page.cjs');
const { REHEARSAL_AGENCY, CRM_NAMESPACE, uuid5 } = require('../../lib/pilot-guard.cjs');
const { REAL_ADDRESS, sha, bff, bffOk, waitForCard, type, choose, day, reuse } = require('./_crm.cjs');

const AGENCY_NAME = 'E2E Pilot Rehearsal Travel';
// The CRM seed's fixed id of the key (AA-Partner api/app/seed/catalogue.py): the same id as the CIS tenant.
const AGENCY_ID = uuid5(CRM_NAMESPACE, `aa-crm-synthetic-agency:${REHEARSAL_AGENCY}`);
const DIR = path.join(__dirname, '..', '..', 'work', 'rehearsal');
const STATE = path.join(DIR, 'crm.json');
const SECRETS = path.join(DIR, '.crm-secrets.json');
const HANDOFF = path.join(DIR, 'handoff.json');
const UUID = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}';
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

// ── run state ───────────────────────────────────────────────────────────────────────────────────────────────────────

function ensureDir() {
  fs.mkdirSync(DIR, { recursive: true, mode: 0o700 });
  fs.chmodSync(DIR, 0o700);
}

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    return {};
  }
}

const load = () => readJson(STATE);

/** Merge `patch` into work/rehearsal/crm.json (ids, dates and amounts only; never a link or a name of a real person). */
function save(patch) {
  ensureDir();
  const s = { ...load(), ...patch, updated_at: new Date().toISOString() };
  fs.writeFileSync(STATE, JSON.stringify(s, null, 2));
  return s;
}

/** Keep a link token with the trip it opens (chmod 600). */
function saveLink(name, link, tripId) {
  ensureDir();
  const v = readJson(SECRETS);
  v[name] = link;
  v[`${name}_trip`] = tripId;
  fs.writeFileSync(SECRETS, JSON.stringify(v, null, 1), { mode: 0o600 });
  fs.chmodSync(SECRETS, 0o600);
}

/** The link `name` of trip `tripId`, or null (none, or one of another trip: an earlier run). */
function link(name, tripId) {
  const v = readJson(SECRETS);
  return v[name] && tripId && v[`${name}_trip`] === tripId ? v[name] : null;
}

/** The orchestrator's hand-off: tour X and the planner lead's name (env wins over work/rehearsal/handoff.json). */
function handoff() {
  const f = readJson(HANDOFF);
  return {
    tour_x: (process.env.UAT_REH_TOUR_X || f.tour_x || '').trim() || null,
    lead_name: (process.env.UAT_REH_LEAD_NAME || f.lead_name || '').trim() || null,
    // Same variable and default as the TripPlanner group's step 6 (scenarios/tripplanner/_rehearsal.cjs).
    traveller_email: (process.env.UAT_REH_TRAVELLER_EMAIL || f.traveller_email || 'rehearsal.traveller@example.invalid').trim(),
  };
}

// ── mail guard: the traveller's address must be an invented one ──────────────────────────────────────────────────

// Domains that never reach a person: the reserved .invalid TLD (RFC 2606; the runbook's example.invalid) and the E2E
// mailbox domain, whose mail lands only in the E2E S3 bucket.
const INVENTED_DOMAINS = [/(^|\.)invalid$/, /^e2e-mail\.lumiguides\.it\.com$/];

/** True when `addr` is one e-mail address on an invented domain. */
function inventedAddress(addr) {
  const m = /^[^@\s]+@([^@\s]+)$/.exec(String(addr || '').trim().toLowerCase());
  return !!m && INVENTED_DOMAINS.some((r) => r.test(m[1]));
}

/**
 * Stop before a step that makes the CRM mail the trip's travellers unless every address it would mail is invented.
 * On a CRM page (live): the hand-off address is invented, a blind-index search for it (POST travelers/search, an exact
 * e-mail match; the address itself is never revealed or logged) finds the trip's lead, and no other traveller of the
 * trip has an address. Off the agency host (the client and portal steps): the live check of an earlier step of the same
 * trip must exist (work/rehearsal/crm.json traveller_check). Each scenario that calls it live allows and caps
 * POST travelers/search (searchWrite / CAP.search).
 */
async function checkTraveller(page, s) {
  const addr = handoff().traveller_email;
  if (!inventedAddress(addr)) {
    throw new Error('the hand-off traveller address is not on an invented domain (*.invalid or the E2E mailbox): stop before any mail');
  }
  if (new URL(page.url()).origin !== crm.PARTNER) {
    const c = load().traveller_check;
    if (!c || c.trip_id !== s.trip_id) throw new Error('no traveller address check for this trip: run the agency steps (REH-06 onwards) first');
    return c;
  }
  const t = await bffOk(page, 'GET', `trips/${s.trip_id}`);
  const lead = (t.party || []).find((p) => p.role === 'lead');
  if (!lead) throw new Error('the trip has no lead traveller');
  const others = (t.party || []).filter((p) => p.has_email && p.traveler_id !== lead.traveler_id);
  if (others.length) throw new Error(`${others.length} other traveller(s) of the trip have an e-mail address the run cannot check: stop before any mail`);
  const r = await bffOk(page, 'POST', 'travelers/search', { q: addr });
  if (!(r.items || []).some((x) => x.traveler_id === lead.traveler_id)) {
    throw new Error('the lead traveller\'s address is not the invented hand-off address: stop before any mail');
  }
  const check = { trip_id: s.trip_id, traveler_id: lead.traveler_id, at: new Date().toISOString() };
  save({ traveller_check: check });
  return check;
}

/** The state a step needs, or a clear "run X first" error. */
function need(s, keys, before) {
  const missing = keys.filter((k) => s[k] === undefined || s[k] === null);
  if (missing.length) throw new Error(`rehearsal state lacks ${missing.join(', ')}: run ${before} first`);
  return s;
}

// ── writes the scenarios may make ───────────────────────────────────────────────────────────────────────────────────

// Each entry is [method, path regex source]: the method is matched too (lib/net-guard.cjs parseAllow), so an allowed
// create path never lets a DELETE or a PATCH of the same path through.
/** allowWrites entries for CRM BFF paths on the agency host ([method, regex source after /bff/], anchored at the end). */
const bffWrites = (...pairs) => pairs.map(([m, p]) => `${m} ^${esc(crm.PARTNER)}/bff/${p}(?:[?#]|$)`);
/** allowWrites entries for the client host's public API ([method, path after /crm/public/v1/], anchored at the end). */
const clientWrites = (...pairs) => pairs.map(([m, p]) => `${m} ^${esc(crm.CLIENT)}/crm/public/v1/${p}(?:[?#]|$)`);
/** The traveller address check of checkTraveller() (a search, no data written; the API logs a list view). */
const searchWrite = ['POST', 'travelers/search'];

/**
 * Cap every write of a scenario (lib/uat-page.cjs limitWrites, every method): rules [name, method, pathname regex
 * source, max]; a retry, a double click or a re-render never creates, mails or deletes twice. Call it first thing in
 * step 1, before any page loads. Returns the live counts.
 */
const cap = (page, rules) => limitWrites(page, rules.map(([name, method, p, max]) => ({ name, method, path: new RegExp(`^${p}$`), max })));
/** The pathname regex source of a BFF path (for cap()). */
const bffPath = (p) => `/bff/${p}`;
/** The pathname regex source of a client-host public API path (for cap()). */
const clientPath = (p) => `/crm/public/v1/${p}`;
/** checkTraveller()'s search: at most this many per scenario (one per mail-sending step plus a re-run). */
const SEARCH_CAP = 3;

// ── the scenario shell ──────────────────────────────────────────────────────────────────────────────────────────────

/**
 * A rehearsal scenario: rw() with the CRM review masks (one-time codes, client / portal links, the agency's real
 * mailbox), internal issue ids and any real e-mail address blurred, the CRM's sticky top bar, and meta for the git sha.
 */
function scenario({ id, title, titleVi, identity = 'crm-rehearsal', viewport = DESKTOP, allowWrites, mask = [], steps }) {
  return rw({
    id, app: 'crm', identity, title, titleVi, baseURL: crm.PARTNER, viewport, steps, allowWrites, paid: false,
    mask: [...crm.TRAVELLER_MASK, ...mask],
    blurText: ['\\bAA-?\\d{3,4}\\b', REAL_ADDRESS],
    scrollBlock: 'center',
    meta: { agency: REHEARSAL_AGENCY },
  });
}

/** Open a CRM page and check the session held (no managed-login redirect); `testId` waits for the page's root. */
async function open(page, h, p, testId) {
  await h.goto(p);
  await page.waitForLoadState('networkidle', { timeout: 15_000 }).catch(() => {});
  const u = new URL(page.url());
  if (u.origin !== crm.PARTNER || /sign-?in|login|signed-out|select-agency/.test(u.pathname)) {
    throw new Error(`not signed in on the rehearsal agency (landed on ${u.host}${u.pathname})`);
  }
  if (testId) await h.expect(page.getByTestId(testId).first()).toBeVisible({ timeout: 20_000 });
}

/** The trip workspace, hydrated. */
async function openTrip(page, h, tripId) {
  await open(page, h, `/pipeline/${tripId}`, 'crm-trip');
  await h.expect(page.getByTestId('crm-trip')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
}

/** The signed-in member as the CRM sees it ({ member_id, member_role, tenant_id, ... }); `role` must match. */
async function me(page, role) {
  const m = await bffOk(page, 'GET', 'me');
  if (m.tenant_id !== AGENCY_ID) throw new Error('the session is not on the rehearsal agency');
  if (role && m.member_role !== role) throw new Error(`signed in as ${m.member_role}, this step needs the ${role}`);
  return m;
}

/**
 * Tour X as AA sells it to this agency: { source_id, title, days, departures, from_price }. GET aa/products/<id>
 * (AA-Partner api/app/routers/aa.py get_product) answers Booking's product and departures plus `tour`, the CRM's
 * catalogue row (title, duration_days); a tour the CRM catalogue does not hold cannot be searched in the builder.
 */
async function tourX(page) {
  const { tour_x: id } = handoff();
  if (!id) throw new Error('no tour X: set UAT_REH_TOUR_X or work/rehearsal/handoff.json tour_x (runbook "Tour X")');
  const prod = await bffOk(page, 'GET', `aa/products/${encodeURIComponent(id)}?currency=USD`);
  const tour = prod.tour || null;
  if (!tour || !tour.title) throw new Error('tour X is not in the CRM\'s AA catalogue (no title): wait for the catalogue sync or pick X\'');
  if (!(Number(tour.duration_days) >= 1)) throw new Error('tour X has no number of days in the CRM\'s AA catalogue: pick X\'');
  return { source_id: id, title: tour.title, days: Number(tour.duration_days), departures: prod.departures || [], from_price: prod.from_price || null };
}

// Booking departure states a client can book (AA-Booking backend/app/b2b/departures.py STATUSES minus cancelled).
const BOOKABLE = ['scheduled', 'guaranteed'];

/** The first open fixed departure of tour X with seats for `adults`, at least `minDays` days ahead. */
function pickDeparture(tour, adults, minDays = 3) {
  const earliest = day(minDays);
  const deps = tour.departures
    .filter((d) => BOOKABLE.includes(d.status) && d.available >= adults && d.start_date >= earliest)
    .sort((a, b) => a.start_date.localeCompare(b.start_date) || a.departure_id.localeCompare(b.departure_id));
  if (!deps.length) {
    throw new Error(`tour X has no open departure with ${adults} free seat(s) (${tour.departures.map((d) => `${d.start_date}:${d.status}:${d.available}`).join(', ') || 'no departures'}): pick X' (runbook "Tour X")`);
  }
  return deps[0];
}

/** The builder view of a proposal (GET, from any CRM page). */
const builderView = (page, pid) => bffOk(page, 'GET', `proposals/${pid}/builder`);

/** The AA line(s) of a trip from the ledger (GET trips/<id>/lines): [{ booking_line_id, status, title, aa: {...} }]. */
async function aaLines(page, tripId) {
  const r = await bffOk(page, 'GET', `trips/${tripId}/lines`);
  return (r.lines || []).filter((l) => l.supplier_kind === 'aa' || l.aa);
}

module.exports = {
  crm, AGENCY_NAME, AGENCY_ID, REHEARSAL_AGENCY, DESKTOP, PHONE, UUID, step, scenario, open, openTrip, me, tourX, pickDeparture,
  BOOKABLE, builderView, aaLines, bffWrites, clientWrites, searchWrite, cap, bffPath, clientPath, SEARCH_CAP, load, save,
  saveLink, link, handoff, need, inventedAddress, checkTraveller,
  sha, bff, bffOk, waitForCard, type, choose, day, reuse,
};
