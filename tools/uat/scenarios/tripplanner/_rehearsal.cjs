// Shared helpers of the pilot rehearsal scenarios on the traveller side (runbook docs/ops/runbooks/pilot-rehearsal.md,
// steps 5, 6 and the Book now check): the synthetic agency, the tour the rehearsal follows ("tour X"), the planner's
// way in through the web ACL, and the write allow-lists. Not a scenario (the leading underscore keeps it out of the
// catalogue checks). Pure but for the page helpers; no secret, no account id.
//
// Env (all optional but UAT_REH_TOUR_X, which the rehearsal sets to its tour X):
//   UAT_REH_TOUR_X           tour X on the agency's planner: its TripPlanner slug, its source id or a part of its title
//                            (unset: the agency's first tour, written to result.json meta as "not named")
//   UAT_REH_TRAVELLER_EMAIL  the invented traveller's address (default on example.invalid, as the runbook says)
//   UAT_TRIPPLANNER, UAT_CLIENT_HOST, UAT_CIS_API   host overrides (Dev by default)
'use strict';
const { HOSTS } = require('../../lib/dryrun-page.cjs');

// The rehearsal agency (runbook "Fixtures"): a demo tenant with the CRM and TripPlanner add-ons. Its id is the
// AA-Partner seed catalogue's fixed id for the key pilot-rehearsal-01 (uuid5, public there), the same in the CIS.
const SLUG = 'pilot-rehearsal-01';
const AGENCY = 'E2E Pilot Rehearsal Travel';
const TENANT_ID = '41ea21ee-77ee-5474-bd6d-aa738d2da990';
const PLAN = `/${SLUG}/plan`;

const host = (env, dflt) => (process.env[env] || dflt).replace(/\/+$/, '');
const CLIENT = host('UAT_CLIENT_HOST', 'https://go-dev.lumiguides.it.com');
const CIS_API = host('UAT_CIS_API', 'https://api-cis.lumiguides.it.com');
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

// The kit's own accent (tokens.css): a planner still on it shows no agency colours.
const KIT_ACCENT = '#db9628';

// Writes, as regex sources on the full URL (record.cjs allowWrites). The web ACL's silent challenge on a planner
// document load POSTs its proof to AWS WAF's token host: the recorder's guard always lets that through (no app data,
// lib/net-guard.cjs isChallengeProof), so it is not listed here.
const TP = esc(HOSTS.tripplanner);
const WRITES = {
  trip: `^${TP}/api/trip(?:[?#]|$)`, // the guest trip: apply-route, reorder (no model call)
  chat: `^${TP}/api/trip/chat(?:[?#]|$)`, // one planning chat turn: a paid model call
  send: `^${TP}/api/trip/send(?:[?#]|$)`, // the request to the agency (lead.submitted.v1)
};
// Pathnames for limitWrites (lib/uat-page.cjs).
const PATHS = { trip: /^\/api\/trip$/, chat: /^\/api\/trip\/chat$/, send: /^\/api\/trip\/send$/ };
// Paths no rehearsal take may reach: narration (a paid model call none of these steps asks for).
const NO_NARRATION = ['/api/trip/narrate(?:[?#]|$)'];

/** The invented traveller of the hand-off and the booking (no real person; the address never receives mail). */
function traveller(env = process.env) {
  return {
    name: 'Rehearsal Traveller',
    email: (env.UAT_REH_TRAVELLER_EMAIL || 'rehearsal.traveller@example.invalid').trim(),
    message: 'Synthetic pilot rehearsal request. Please ignore.',
  };
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
async function openPlanner(page, h) {
  await h.goto(PLAN);
  await h.expect(page).toHaveTitle(new RegExp(`^Trip planner · ${esc(AGENCY)}\\b`), { timeout: 60_000 });
  if (new URL(page.url()).pathname !== PLAN) throw new Error(`the planner moved to ${new URL(page.url()).pathname}`);
  await h.expect(page.locator('header').first()).toContainText(AGENCY, { timeout: 30_000 });
}

/** The agency's own brand block is on the page and moves the kit accent off its default. Returns the accent. */
async function assertBrand(page, h) {
  // Server-rendered with the page: present at load or never (the agency's TripPlanner site has no theme stored).
  if ((await page.locator('style[data-testid="tenant-brand"]').count()) !== 1) {
    throw new Error('no agency brand block on the planner: the agency has no TripPlanner theme stored, so it shows the kit colours');
  }
  const accent = (await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--aa-accent'))).trim().toLowerCase();
  if (!accent || accent === KIT_ACCENT) throw new Error(`the planner still uses the kit accent (${accent || 'none'}): no agency colours`);
  return accent;
}

/**
 * Open the list of the agency's tours, find tour X and pin its route ("Plan this route"). Returns the tour card.
 * The list must be the agency's own (source "tenant"), never the AA catalogue.
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
  const tour = pickTour(body.tours);
  if (!tour) throw new Error(process.env.UAT_REH_TOUR_X ? 'tour X (UAT_REH_TOUR_X) is not among the agency\'s tours' : 'the agency has no tour yet (adopt tour X first, step 3)');
  if (meta) {
    meta.tour_x = { slug: tour.slug, source_id: tour.source_id, named: !!process.env.UAT_REH_TOUR_X };
    meta.agency_tours = body.total;
  }
  const pane = page.locator('[aria-label="Tours list"]');
  await h.expect(pane).toContainText('All tours', { timeout: 30_000 });
  const card = pane.locator('li').filter({ has: page.getByRole('link', { name: tour.title, exact: true }) }).first();
  await h.scrollTo(card, 'center');
  await h.click(card.getByRole('button', { name: 'Plan this route' }));
  await h.expect(card).toContainText('Added to your trip.', { timeout: 60_000 });
  return tour;
}

/** The stops of the trip panel (at least `min`), as their text, in order. */
async function tripStops(page, h, min = 1) {
  const days = page.getByTestId('day-list').filter({ visible: true }).first().getByTestId('day');
  await h.expect.poll(() => days.count(), { timeout: 30_000 }).toBeGreaterThanOrEqual(min);
  return days.allInnerTexts();
}

module.exports = {
  SLUG, AGENCY, TENANT_ID, PLAN, CLIENT, CIS_API, KIT_ACCENT, WRITES, PATHS, NO_NARRATION, esc,
  traveller, pickTour, openPlanner, assertBrand, addTourX, tripStops,
};
