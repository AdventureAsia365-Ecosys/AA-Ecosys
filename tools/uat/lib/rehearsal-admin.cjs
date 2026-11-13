// The pilot rehearsal on Dev, staff side (root docs/ops/runbooks/pilot-rehearsal.md; scenarios REH-* of the CIS admin
// and the Booking staff admin): the synthetic agency's fixed facts, and the run inputs the orchestrator hands over.
// Pure Node, no browser, no network. Cost $0.
//
//   const reh = require('../../lib/rehearsal-admin.cjs');
//   reh.REHEARSAL.id                    the CIS tenant id = the CRM agency id of pilot-rehearsal-01 (public, runbook)
//   reh.bookingFixtures()               the Booking seeder's APPLY output (env UAT_BOOKING_FIXTURES = its JSON file)
//   reh.listEnv('UAT_REH_TOUR_KEYS')    a comma list from the environment
//   reh.markerId()                      the marker tenant's id (env UAT_REH_MARKER_ID), steps 1b / 12b
//   reh.assertMarker(tenant, { pilot }) stop (pilot_guard) unless a read tenant is the invented marker tenant
//
// Inputs (all optional until a scenario needs one; none is a secret, all stay out of git):
//   UAT_BOOKING_FIXTURES  path of the JSON that `python -m app.e2e_fixtures --apply --run <run> --agency-tenant
//                         <rehearsal id>` printed (AA-Booking, ECS exec on aa-booking-dev-api): the trip case, the
//                         pending supplier booking and the issued invoice of the rehearsal agency. Keep it under
//                         tools/uat/work/ (gitignored). A file of another agency is refused (fail closed).
//   UAT_REH_TOUR_KEYS     the Booking trip plan keys (CIS source ids) the price setup made sellable (3 or more).
//   UAT_REH_TP_SLUGS      the TripPlanner tour slugs of the same tours (their public /tours/<slug> pages).
//   UAT_REH_MARKER_ID     the CIS tenant id of pilot-rehearsal-01-marker (printed by the tech lead's provision call).
'use strict';
const fs = require('fs');
const { uuid5, CRM_NAMESPACE, CODE: PILOT_GUARD } = require('./pilot-guard.cjs');

const REHEARSAL = Object.freeze({
  slug: 'pilot-rehearsal-01',
  name: 'E2E Pilot Rehearsal Travel',
  // AA-Partner api/app/seed/catalogue.py: uuid5(ns, "aa-crm-synthetic-agency:pilot-rehearsal-01"); CIS provisions the
  // tenant under the same id (services/tenant_account/e2e_fixtures.py rehearsal-tenant).
  id: uuid5(CRM_NAMESPACE, 'aa-crm-synthetic-agency:pilot-rehearsal-01'),
});
// The marker tenant of steps 1b and 12b (runbook "Fixtures"): kind agency with pilot_weeks 1, no add-ons, provisioned by
// the tech lead under this invented name. It is the Dev pilot while those steps run, so it is never on the pilot guard's
// allow-list; the observation scenarios REH-01b-pilot-on / REH-12b-pilot-off open it by id only after its read answer
// carries this exact name and kind (a real agency never does), and stop with pilot_guard otherwise.
const MARKER = Object.freeze({ slug: 'pilot-rehearsal-01-marker', name: 'E2E Pilot Rehearsal Marker', kind: 'agency' });
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const INVOICE_NO = /^[A-Z]{2,4}-\d{4}-\d{4,8}$/;
const CASE_CODE = /^[A-Z0-9][A-Z0-9-]{2,30}$/;

/** A comma list from the environment, trimmed, empties dropped. */
function listEnv(name, env = process.env) {
  return String(env[name] || '').split(',').map((x) => x.trim()).filter(Boolean);
}

/**
 * The Booking seeder's fixtures for the rehearsal agency: { run, trip_case: { id, code }, supplier_booking: { id, code,
 * status }, invoice: { id, number, status } }. Throws when the file is missing, is not an APPLY output, or belongs to
 * another agency (the reason starts with "pilot_guard:" then: the run never writes on someone else's records).
 */
function bookingFixtures(env = process.env) {
  const file = env.UAT_BOOKING_FIXTURES;
  if (!file) throw new Error('BLOCKED: set UAT_BOOKING_FIXTURES to the Booking seeder APPLY output of the rehearsal agency');
  let parsed;
  try {
    parsed = JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (e) {
    throw new Error(`BLOCKED: UAT_BOOKING_FIXTURES could not be read as JSON (${e.code || 'parse error'})`);
  }
  const f = parsed && parsed.mode === 'APPLY' ? parsed.fixtures : null;
  if (!f || typeof f !== 'object') throw new Error('BLOCKED: UAT_BOOKING_FIXTURES is not the seeder APPLY output ({"mode": "APPLY", "fixtures": ...})');
  const tenant = f.agency && f.agency.tenant_id;
  if (String(tenant || '').toLowerCase() !== REHEARSAL.id) {
    throw new Error(`${PILOT_GUARD}: the Booking fixtures belong to agency ${String(tenant || 'unknown').slice(0, 8)}…, not ${REHEARSAL.slug}`);
  }
  const tc = f.trip_case || {};
  const sb = f.supplier_booking || {};
  const inv = f.invoice || {};
  if (!UUID.test(String(tc.id || '')) || !CASE_CODE.test(String(tc.code || ''))) throw new Error('BLOCKED: the fixtures have no trip case');
  if (!UUID.test(String(sb.id || '')) || !CASE_CODE.test(String(sb.code || ''))) throw new Error('BLOCKED: the fixtures have no supplier booking');
  if (!UUID.test(String(inv.id || '')) || !INVOICE_NO.test(String(inv.number || ''))) throw new Error('BLOCKED: the fixtures have no issued invoice');
  return { run: String(f.run || ''), trip_case: { id: tc.id, code: tc.code }, supplier_booking: { id: sb.id, code: sb.code, status: sb.status },
    invoice: { id: inv.id, number: inv.number, status: inv.status } };
}

/** The marker tenant's id from env UAT_REH_MARKER_ID (lower case); throws BLOCKED when it is missing or not a uuid. */
function markerId(env = process.env) {
  const id = String(env.UAT_REH_MARKER_ID || '').trim().toLowerCase();
  if (!UUID.test(id)) throw new Error('BLOCKED: set UAT_REH_MARKER_ID to the CIS tenant id of pilot-rehearsal-01-marker');
  if (id === REHEARSAL.id) throw new Error('BLOCKED: UAT_REH_MARKER_ID is the rehearsal agency, not the marker tenant');
  return id;
}

/**
 * Throw a pilot-guard stop unless `tenant` (the `tenant` of GET /api/admin/tenants/<id>/subscription) is the invented
 * marker tenant: exact name and kind agency. `pilot` = true / false also requires is_pilot to be that value (with an
 * end date while it is the pilot); a mismatch there is a plain failure (the tech lead's step is not done yet).
 */
function assertMarker(tenant, { pilot } = {}) {
  const t = tenant && typeof tenant === 'object' ? tenant : {};
  if (t.name !== MARKER.name || t.kind !== MARKER.kind) {
    throw new Error(`${PILOT_GUARD}: tenant ${String(t.tenant_id || 'unknown').slice(0, 8)}… is not ${MARKER.slug} (name or kind differ); nothing is shown`);
  }
  if (pilot === true && !(t.is_pilot === true && t.pilot_ends_at)) throw new Error(`${MARKER.slug} is not in pilot mode yet (step 1b not done)`);
  if (pilot === false && t.is_pilot !== false) throw new Error(`${MARKER.slug} is still the pilot (step 12b not done)`);
  return t;
}

/** Throw a pilot-guard stop unless `text` names the rehearsal agency (a page or a record read before a write). */
function assertRehearsalAgency(text, what) {
  if (!String(text || '').includes(REHEARSAL.name)) {
    throw new Error(`${PILOT_GUARD}: ${what} does not name ${REHEARSAL.name}; nothing is written`);
  }
}

module.exports = { REHEARSAL, MARKER, listEnv, bookingFixtures, assertRehearsalAgency, markerId, assertMarker };
