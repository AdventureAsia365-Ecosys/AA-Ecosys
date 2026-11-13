// Unit tests of the pilot rehearsal's staff-side helpers (lib/rehearsal-admin.cjs) and of the rehearsal agency on the
// pilot guard's allow-list. No browser, no network:  node --test tools/uat/tests/*.test.cjs
// Fixture files use invented ids only (the rehearsal agency's id is public: root docs/ops/runbooks/pilot-rehearsal.md).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const reh = require('../lib/rehearsal-admin.cjs');
const g = require('../lib/pilot-guard.cjs');

const ID = reh.REHEARSAL.id;
const OTHER = '00000000-0000-4000-8000-0000000000aa';
const U = (n) => `00000000-0000-4000-8000-${String(n).padStart(12, '0')}`;

function fixturesFile(over = {}) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'reh-'));
  const file = path.join(dir, 'fixtures.json');
  const fixtures = {
    run: 'reh-test', agency: { tenant_id: ID, name: reh.REHEARSAL.name },
    trip_case: { id: U(1), code: 'TC-2026-0001' },
    supplier_booking: { id: U(2), code: 'SB-2026-0001', status: 'pending' },
    invoice: { id: U(3), number: 'AAS-2026-000001', status: 'issued' },
    ...over,
  };
  fs.writeFileSync(file, JSON.stringify({ mode: 'APPLY', fixtures }));
  return file;
}

test('REHEARSAL: the id is the CRM seed id of pilot-rehearsal-01 named in the runbook', () => {
  assert.equal(ID, '41ea21ee-77ee-5474-bd6d-aa738d2da990');
  assert.equal(reh.REHEARSAL.slug, 'pilot-rehearsal-01');
});

test('pilot guard: the rehearsal agency passes in both scopes by id, never by its name alone', () => {
  const allow = g.buildAllowlist(null);
  for (const scope of ['content', 'crm']) {
    const ok = g.evaluate({ tenant_id: ID, tenant_name: reh.REHEARSAL.name, display_name: reh.REHEARSAL.name }, { scope, allow });
    assert.equal(ok.ok, true, scope);
    assert.equal(ok.slug, 'pilot-rehearsal-01');
  }
  const impostor = g.evaluate({ tenant_id: OTHER, tenant_name: reh.REHEARSAL.name }, { scope: 'content', allow });
  assert.equal(impostor.ok, false);
  assert.equal(g.evaluate({ tenant_id: ID, display_name: 'x', is_pilot: true }, { scope: 'crm', allow }).ok, false);
  assert.ok(g.syntheticRowPatterns().some((x) => new RegExp(x, 'i').test(reh.REHEARSAL.name)));
  for (const who of ['booking-staff', 'booking-maker', 'booking-checker']) {
    assert.deepEqual(g.scopesFor({ id: 'REH-99-x', identity: who }, 'state.json'), { scopes: [], only: null });
  }
});

test('bookingFixtures: the rehearsal agency only; missing, malformed or foreign files stop the run', () => {
  const ok = reh.bookingFixtures({ UAT_BOOKING_FIXTURES: fixturesFile() });
  assert.equal(ok.invoice.number, 'AAS-2026-000001');
  assert.equal(ok.supplier_booking.id, U(2));
  assert.throws(() => reh.bookingFixtures({}), /BLOCKED: set UAT_BOOKING_FIXTURES/);
  assert.throws(() => reh.bookingFixtures({ UAT_BOOKING_FIXTURES: fixturesFile({ agency: { tenant_id: OTHER } }) }), /^Error: pilot_guard:/);
  assert.throws(() => reh.bookingFixtures({ UAT_BOOKING_FIXTURES: fixturesFile({ invoice: { id: 'x', number: 'drop table' } }) }), /no issued invoice/);
  const notApply = fixturesFile();
  fs.writeFileSync(notApply, JSON.stringify({ mode: 'DRY RUN', plan: {} }));
  assert.throws(() => reh.bookingFixtures({ UAT_BOOKING_FIXTURES: notApply }), /not the seeder APPLY output/);
});

test('listEnv: trims and drops empties; assertRehearsalAgency stops on another name', () => {
  assert.deepEqual(reh.listEnv('X', { X: ' a, ,b ,' }), ['a', 'b']);
  assert.deepEqual(reh.listEnv('X', {}), []);
  assert.doesNotThrow(() => reh.assertRehearsalAgency(`Case for ${reh.REHEARSAL.name}`, 'the case'));
  assert.throws(() => reh.assertRehearsalAgency('Lotus Lantern Journeys', 'the case'), /^Error: pilot_guard:/);
});

test('rehearsal write scenarios: narrow allowWrites, every write step marked, $0', () => {
  for (const rel of ['booking/reh-09-supplier.cjs', 'booking/reh-11-maker.cjs', 'booking/reh-11-checker.cjs']) {
    const sc = require(path.join(__dirname, '..', 'scenarios', rel));
    assert.equal(sc.paid, false, rel);
    assert.equal(sc.readOnly, true, rel);
    assert.ok(sc.allowWrites.length === 1 && sc.allowWrites.every((x) => !x.startsWith('^') && x.endsWith('$')), rel);
    assert.ok(sc.steps.some((s) => s.writes) && !sc.steps[0].writes, `${rel}: a read-only first step, then marked writes`);
  }
});

test('markerId: a uuid from UAT_REH_MARKER_ID, never the rehearsal agency; assertMarker stops on any other tenant', () => {
  const M = '0f0e0d0c-0b0a-4908-8706-050403020100'; // invented
  assert.equal(reh.markerId({ UAT_REH_MARKER_ID: ` ${M.toUpperCase()} ` }), M);
  assert.throws(() => reh.markerId({}), /^Error: BLOCKED: set UAT_REH_MARKER_ID/);
  assert.throws(() => reh.markerId({ UAT_REH_MARKER_ID: 'pilot-rehearsal-01-marker' }), /^Error: BLOCKED/);
  assert.throws(() => reh.markerId({ UAT_REH_MARKER_ID: ID }), /is the rehearsal agency/);
  const marker = { tenant_id: M, name: reh.MARKER.name, kind: 'agency', is_pilot: true, pilot_ends_at: '2026-11-20T00:00:00Z' };
  assert.equal(reh.assertMarker(marker, { pilot: true }), marker);
  assert.doesNotThrow(() => reh.assertMarker({ ...marker, is_pilot: false, pilot_ends_at: null }, { pilot: false }));
  // Another name or kind is a pilot_guard stop, whatever its pilot state (a real pilot is never opened).
  for (const other of [{ ...marker, name: 'Lotus Lantern Journeys' }, { ...marker, kind: 'demo' }, null, {}]) {
    assert.throws(() => reh.assertMarker(other, { pilot: true }), /^Error: pilot_guard:/);
  }
  // The right tenant in the wrong state is a plain failure: the tech lead's step is not done yet.
  assert.throws(() => reh.assertMarker({ ...marker, is_pilot: false }, { pilot: true }), /not in pilot mode yet/);
  assert.throws(() => reh.assertMarker({ ...marker, pilot_ends_at: null }, { pilot: true }), /not in pilot mode yet/);
  assert.throws(() => reh.assertMarker(marker, { pilot: false }), /still the pilot/);
});

test('rehearsal write scenarios cap their writes per method (limitWrites rules name no PUT / PATCH / DELETE)', () => {
  for (const rel of ['booking/reh-09-supplier.cjs', 'booking/reh-11-maker.cjs', 'booking/reh-11-checker.cjs']) {
    const src = fs.readFileSync(path.join(__dirname, '..', 'scenarios', rel), 'utf8');
    assert.match(src, /limitWrites\(page, \[/, `${rel} registers limitWrites`);
    assert.ok(!/method: '(?:PUT|PATCH|DELETE)'/i.test(src), `${rel}: POST writes only`);
    assert.ok(/strict: true/.test(src), `${rel}: a stray method on a capped path is aborted (strict)`);
  }
});

test('pilot observation scenarios: read only, marker id from the environment, not in the dry run', () => {
  const manifest = require('../scenarios/dryrun.cjs');
  for (const rel of ['cis-admin/reh-01b-pilot-on.cjs', 'cis-admin/reh-12b-pilot-off.cjs']) {
    const sc = require(path.join(__dirname, '..', 'scenarios', rel));
    assert.equal(sc.readOnly, true, rel);
    assert.ok(!sc.allowWrites || !sc.allowWrites.length, rel);
    assert.ok(!manifest.includes(rel), `${rel} is not in the dry run`);
  }
  // The rehearsal-fixture scenarios stay out of the routine dry run (they fail until the fixture exists).
  for (const rel of ['cis-admin/reh-01-provisioned.cjs', 'cis-admin/reh-01-crm-agency.cjs', 'booking/reh-01-booking-partner.cjs']) {
    assert.ok(!manifest.includes(rel), `${rel} is not in the dry run`);
  }
});
