// Shared helpers of the pilot rehearsal scenarios on the traveller side (runbook docs/ops/runbooks/pilot-rehearsal.md,
// steps 5, 6 and the Book now check): the synthetic agency, the tour the rehearsal follows ("tour X"), the planner's
// way in through the web ACL, and the write allow-lists. Not a scenario (the leading underscore keeps it out of the
// catalogue checks). Pure but for the page helpers; no secret, no account id.
//
// Env (all optional but UAT_REH_TOUR_X, which the rehearsal sets to its tour X):
//   UAT_REH_TOUR_X           tour X on the agency's planner: its TripPlanner slug, its source id or a part of its title
//                            (unset: the agency's first tour, written to result.json meta as "not named"). Tour X needs
//                            a planner route of at least two stops (REH-05.m moves one) and two days (REH-05).
//   UAT_REH_TRAVELLER_EMAIL  the invented traveller's address (default on example.invalid, as the runbook says)
//   UAT_TRIPPLANNER, UAT_CLIENT_HOST, UAT_CIS_API   host overrides (Dev by default)
'use strict';
const { HOSTS } = require('../../lib/dryrun-page.cjs');
const { PAID_URLS } = require('../../lib/dryrun-core.cjs');
const { CHALLENGE_PROOF } = require('../../lib/net-guard.cjs');

// The rehearsal agency (runbook "Fixtures"): a demo tenant with the CRM and TripPlanner add-ons.
const SLUG = 'pilot-rehearsal-01';
const AGENCY = 'E2E Pilot Rehearsal Travel';
const PLAN = `/${SLUG}/plan`;

const host = (env, dflt) => (process.env[env] || dflt).replace(/\/+$/, '');
const CLIENT = host('UAT_CLIENT_HOST', 'https://go-dev.lumiguides.it.com');
const CIS_API = host('UAT_CIS_API', 'https://api-cis.lumiguides.it.com');
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

// Writes, as regex sources on the full URL (record.cjs allowWrites). The web ACL's silent challenge on a planner
// document load POSTs its proof to AWS WAF's token host: the recorder's guard always lets that through (no app data,
// lib/net-guard.cjs isChallengeProof), so it is not listed here.
const TP = esc(HOSTS.tripplanner);
const WRITES = {
  trip: `^${TP}/api/trip(?:[?#]|$)`, // the guest trip: apply-route, reorder (no model call)
  chat: `^${TP}/api/trip/chat(?:[?#]|$)`, // one planning chat turn: a paid model call
  send: `^${TP}/api/trip/send(?:[?#]|$)`, // the request to the agency (lead.submitted.v1)
};
// Pathnames for limitWrites (lib/uat-page.cjs). search is a GET that calls the embedding model (capped as a read).
const PATHS = { trip: /^\/api\/trip$/, chat: /^\/api\/trip\/chat$/, send: /^\/api\/trip\/send$/, search: /^\/api\/browse\/search$/ };
// The PAID_URLS entry of the planner search (its protected path, lib/botCheck.ts SEARCH_PATH): the only paid path REH-05
// opens (allowPaidUrls). The older spelling ?resource=search and narration stay blocked by the runner's list.
const SEARCH_PAID = PAID_URLS.find((u) => u.startsWith('/api/browse/search'));
// Paths no rehearsal take may reach, whoever runs it (run.sh sets no runner list): every paid path but the ones a
// scenario opens itself, and narration in both spellings.
const NO_NARRATION = ['/api/trip/narrate(?:[?#]|$)'];
const paidBlocks = (open = []) => [...new Set([...PAID_URLS.filter((u) => !open.includes(u)), ...NO_NARRATION])];

/**
 * limitWrites `accept` for POST /api/trip: only POST, and only the JSON ops a take makes (e.g. apply_route, reorder).
 * Anything else on the path (another op such as narrate or send in the older spelling, or a PUT / PATCH / DELETE) is
 * aborted and counted as refused.
 */
function tripOps(...ops) {
  return (req) => {
    if (req.method() !== 'POST') return false;
    try { return ops.includes(JSON.parse(req.postData() || '{}').op); } catch { return false; }
  };
}

// The admin-editable limits a take can meet (TripPlanner backend/shared/settings.py, CIS settings registry, edited on
// the CIS admin page Platform > Settings > TripPlanner). The scenarios never copy their values: a 429 names the key.
const REGISTRY = {
  search: ['tripplanner.rate.search_per_minute'],
  chat: ['tripplanner.rate.chat_per_hour', 'tripplanner.rate.chat_ip_per_hour', 'tripplanner.spend.plan_chat_monthly_cap_usd'],
  send: ['tripplanner.rate.send_per_hour', 'tripplanner.rate.send_ip_per_hour'],
  lead_cap_reached: ['tripplanner.leads.tenant_daily_cap'],
};
/** " (registry setting ...)" for a refused call: a take needs more than the setting in force allows. */
function registryHint(kind, status, error) {
  if (status !== 429) return '';
  const keys = REGISTRY[error === 'lead_cap_reached' ? 'lead_cap_reached' : kind] || [];
  return keys.length ? ` (limit reached: registry setting ${keys.join(' / ')}, CIS admin Platform > Settings)` : '';
}

/**
 * The invented traveller of the hand-off and the booking (no real person; the address never receives mail). The
 * address must be on the reserved .invalid domain (RFC 2606): the later steps mail the lead traveller (proposal,
 * deposit invite, portal codes), so any other address stops the take before anything is sent.
 */
function traveller(env = process.env) {
  const email = (env.UAT_REH_TRAVELLER_EMAIL || 'rehearsal.traveller@example.invalid').trim();
  if (!/^[^@\s]+@[A-Za-z0-9.-]+\.invalid$/i.test(email)) throw new Error('UAT_REH_TRAVELLER_EMAIL must be an invented address on .invalid (later steps mail it)');
  return { name: 'Rehearsal Traveller', email, message: 'Synthetic pilot rehearsal request. Please ignore.' };
}

/** Tour X among the agency's tours (TripPlanner tenant tour cards): by slug, source id, tour id, then a title part. */
function pickTour(tours, wanted = (process.env.UAT_REH_TOUR_X || '').trim()) {
  const list = Array.isArray(tours) ? tours : [];
  if (!wanted) return list[0] || null;
  const k = wanted.toLowerCase();
  return list.find((t) => [t.slug, t.source_id, t.tour_id].some((v) => String(v || '').toLowerCase() === k))
    || list.find((t) => String(t.title || '').toLowerCase().includes(k))
    || null;
}

/**
 * Open the agency's planner and prove it is the rehearsal agency before anything is written: the web ACL's challenge
 * page runs first and reloads into the planner, whose title and top bar carry the agency's trading name.
 */
async function openPlanner(page, h, meta) {
  // Evidence of the web ACL's silent challenge in this browser (headless unless UAT_HEADED=1): its proof POSTs.
  let proofs = 0;
  const onRequest = (r) => { if (CHALLENGE_PROOF.some((x) => x.test(r.url()))) proofs += 1; };
  page.on('request', onRequest);
  await h.goto(PLAN);
  await h.expect(page).toHaveTitle(new RegExp(`^Trip planner · ${esc(AGENCY)}\\b`), { timeout: 60_000 });
  if (new URL(page.url()).pathname !== PLAN) throw new Error(`the planner moved to ${new URL(page.url()).pathname}`);
  await h.expect(page.locator('header').first()).toContainText(AGENCY, { timeout: 30_000 });
  page.off('request', onRequest);
  if (meta) meta.waf = { headed: process.env.UAT_HEADED === '1', challenge_proofs: proofs };
}

/**
 * The agency's own brand block is on the page and its accent is the one the planner draws with. TripPlanner renders
 * brandThemeCss(site.theme) (ui/core/brandTheme.ts) as <style data-testid="tenant-brand">, whose rules set the tokens
 * on `body` ("html:not([data-theme]) body,html[data-theme=light] body{--aa-accent:#...}"), while tokens.css keeps the
 * kit default on :root. So the agency colour is read from body (custom properties inherit down, never up), and the
 * kit's value is read from :root, not copied here. Returns the accent.
 */
async function assertBrand(page, h) {
  // Server-rendered with the page: present at load or never (the agency's TripPlanner site has no theme stored).
  const block = page.locator('style[data-testid="tenant-brand"]');
  if ((await block.count()) !== 1) {
    throw new Error('no agency brand block on the planner: the agency has no TripPlanner theme stored, so it shows the kit colours');
  }
  const declared = [...(await block.textContent() || '').matchAll(/--aa-accent:(#[0-9a-f]{6})/gi)].map((m) => m[1].toLowerCase());
  if (!declared.length) throw new Error('the agency brand block sets no accent (its theme accent was dropped or never stored)');
  const { body, root } = await page.evaluate(() => ({
    body: getComputedStyle(document.body).getPropertyValue('--aa-accent'),
    root: getComputedStyle(document.documentElement).getPropertyValue('--aa-accent'),
  }));
  const accent = body.trim().toLowerCase();
  const kit = root.trim().toLowerCase();
  if (!accent || accent === kit) throw new Error(`the planner still draws with the kit accent (${accent || 'none'}): no agency colours`);
  if (!declared.includes(accent)) throw new Error(`the planner accent ${accent} is not the agency's (${declared.join(', ')})`);
  return accent;
}

/**
 * Open the list of the agency's tours, find tour X and pin its route ("Plan this route"). Returns the tour card.
 * The list must be the agency's own (source "tenant"), never the AA catalogue. The pane loads pages of 24
 * (TourListPane PAGE_SIZE): when tour X is not on the first page, "Show more" loads the next until it is (reads only).
 */
async function addTourX(page, h, meta) {
  const listed = page.waitForResponse((r) => {
    const u = new URL(r.url());
    return u.pathname === '/api/browse' && u.searchParams.get('resource') === 'tenant-tours' && r.request().method() === 'GET';
  }, { timeout: 60_000 });
  await h.click(page.getByRole('button', { name: 'List of tours', exact: true }));
  const res = await listed;
  if (res.status() !== 200) throw new Error(`the agency's tour list answered ${res.status()}`);
  const body = await res.json();
  if (body.source !== 'tenant') throw new Error(`the planner listed "${body.source}" tours, not the agency's own`);
  const pane = page.locator('[aria-label="Tours list"]');
  await h.expect(pane).toContainText('All tours', { timeout: 30_000 });
  const tours = Array.isArray(body.tours) ? [...body.tours] : [];
  let tour = pickTour(tours);
  // Further pages, only while tour X is named and not found yet (unnamed: the first tour of the first page).
  for (let pageNo = 1; !tour && process.env.UAT_REH_TOUR_X && tours.length < (body.total || 0) && pageNo < 20; pageNo += 1) {
    const more = page.waitForResponse((r) => {
      const u = new URL(r.url());
      return u.pathname === '/api/browse' && u.searchParams.get('resource') === 'tenant-tours' && u.searchParams.has('offset');
    }, { timeout: 60_000 });
    await h.click(pane.getByRole('button', { name: /^Show more \(/ }));
    const r = await more;
    if (r.status() !== 200) throw new Error(`the agency's tour list (page ${pageNo + 1}) answered ${r.status()}`);
    const next = (await r.json()).tours || [];
    if (!next.length) break;
    tours.push(...next);
    tour = pickTour(next);
  }
  if (!tour) throw new Error(process.env.UAT_REH_TOUR_X ? `tour X (UAT_REH_TOUR_X) is not among the agency's ${body.total} tours` : 'the agency has no tour yet (adopt tour X first, step 3)');
  if (meta) {
    meta.tour_x = { slug: tour.slug, source_id: tour.source_id, named: !!process.env.UAT_REH_TOUR_X };
    meta.agency_tours = body.total;
  }
  const card = pane.locator('li').filter({ has: page.getByRole('link', { name: tour.title, exact: true }) }).first();
  await h.scrollTo(card, 'center');
  await h.click(card.getByRole('button', { name: 'Plan this route' }));
  await h.expect(card).toContainText('Added to your trip.', { timeout: 60_000 });
  return tour;
}

/** The day groups of the trip panel (DayList data-testid "day"; at least `min`), as their text, in order. */
async function tripDays(page, h, min = 1) {
  const days = page.getByTestId('day-list').filter({ visible: true }).first().getByTestId('day');
  await h.expect.poll(() => days.count(), { timeout: 30_000 }).toBeGreaterThanOrEqual(min);
  return days.allInnerTexts();
}

/** The number of stops of the trip panel (one move handle each; at least `min`). */
async function tripStopCount(page, h, min = 1) {
  const stops = page.getByTestId('day-list').filter({ visible: true }).first().getByTestId('stop-handle');
  await h.expect.poll(() => stops.count(), { timeout: 30_000 }).toBeGreaterThanOrEqual(min);
  return stops.count();
}

module.exports = {
  SLUG, AGENCY, PLAN, CLIENT, CIS_API, WRITES, PATHS, SEARCH_PAID, NO_NARRATION, REGISTRY, esc,
  paidBlocks, tripOps, registryHint, traveller, pickTour, openPlanner, assertBrand, addTourX, tripDays, tripStopCount,
};
