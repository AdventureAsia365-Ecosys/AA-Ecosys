// Unit tests of the UAT scenario catalogue (AA-855): tools/uat/catalogue.json against lib/catalogue.cjs, the scenario
// files and the dry-run manifest. No browser, no network:  node --test tools/uat/tests
// Fixtures use invented ids and names only.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const cat = require('../lib/catalogue.cjs');
const core = require('../lib/dryrun-core.cjs');

const SCEN = path.join(__dirname, '..', 'scenarios');
const MANIFEST = path.join(SCEN, 'dryrun.cjs');

/** Every scenario module under scenarios/ (helpers starting with _ and the manifest excluded). */
function scenarioModules() {
  const out = [];
  for (const dir of fs.readdirSync(SCEN, { withFileTypes: true }).filter((d) => d.isDirectory())) {
    for (const f of fs.readdirSync(path.join(SCEN, dir.name)).filter((x) => x.endsWith('.cjs') && !x.startsWith('_'))) {
      const rel = `${dir.name}/${f}`;
      out.push({ rel, sc: require(path.join(SCEN, rel)) });
    }
  }
  return out;
}

const row = (over = {}) => ({ id: 'ZZ-01', app: 'crm', module: 'demo', story: 'An invented story', roles: ['agency-owner'],
  kinds: ['uat'], covers: [], screens: ['/demo'], status: 'live', round: null, identity: 'crm', writes: false, paid: false, ...over });
const of = (...rows) => ({ version: 1, scenarios: rows });

// ── the real catalogue ──────────────────────────────────────────────────────────────────────────────────────────────

test('catalogue.json is valid: fields, types, unique ids, known apps / statuses / kinds / identities', () => {
  assert.deepEqual(cat.validate(cat.load()), []);
});

test('every scenario file has a catalogue row naming that file, the same app and identity; every named file exists', () => {
  const c = cat.loadValid();
  assert.deepEqual(cat.checkFiles(c, scenarioModules()), []);
});

test('every dry-run manifest entry has a live catalogue row that writes nothing, costs nothing and names the same identity', () => {
  const c = cat.loadValid();
  const entries = require(MANIFEST).map((rel) => core.describe(require(path.resolve(path.dirname(MANIFEST), rel)), rel));
  assert.deepEqual(cat.checkManifest(c, entries), []);
});

test('retired ids are never in the dry-run manifest, never in a round, and stay in the catalogue', () => {
  const c = cat.loadValid();
  const retired = c.scenarios.filter((r) => r.status === 'retired').map((r) => r.id);
  for (const id of ['TP-05', 'X-01', 'BK-02']) assert.ok(retired.includes(id), `${id} is retired (root ADR 0019, B2B-only)`);
  const manifestIds = require(MANIFEST).map((rel) => require(path.resolve(path.dirname(MANIFEST), rel)).id);
  for (const id of retired) assert.ok(!manifestIds.includes(id), `${id} is retired but in the manifest`);
});

test('round 1 (R1-2026-11) covers Content and CRM; the blocked and after-lane channels are named as such', () => {
  const c = cat.loadValid();
  const by = cat.byId(c);
  const r1 = c.scenarios.filter((r) => r.round === 'R1-2026-11');
  assert.ok(r1.every((r) => ['content-studio', 'crm', 'cross-app'].includes(r.app)), 'round 1 is Content + CRM only');
  for (const id of ['PRT-02', 'PRT-04', 'PRT-05', 'PRT-06', 'PRT-08', 'PRT-13', 'PRT-14', 'X-04']) assert.ok(by.has(id), id);
  assert.equal(by.get('PRT-07').status, 'blocked');
  assert.equal(by.get('PRT-07b').status, 'blocked');
  assert.equal(by.get('PRT-11').status, 'after-lane');
  assert.equal(by.get('PRT-12').status, 'after-lane');
  assert.equal(by.get('PRT-06').paid, true);
  assert.equal(by.get('PRT-02').identity, 'studio-editor');
});

test('the paid and the writing scenarios are not dry-run scenarios (no ro()-only build, not in the manifest)', () => {
  const c = cat.loadValid();
  const manifestIds = new Set(require(MANIFEST).map((rel) => require(path.resolve(path.dirname(MANIFEST), rel)).id));
  for (const r of c.scenarios.filter((x) => x.writes || x.paid)) assert.ok(!manifestIds.has(r.id), `${r.id} writes or is paid`);
});

// ── the validator ───────────────────────────────────────────────────────────────────────────────────────────────────

test('validate: a valid fixture passes; a duplicate id, an unknown status / kind / app / identity fail', () => {
  assert.deepEqual(cat.validate(of(row())), []);
  assert.match(cat.validate(of(row(), row())).join(), /duplicate id/);
  assert.match(cat.validate(of(row({ status: 'done' }))).join(), /unknown status/);
  assert.match(cat.validate(of(row({ kinds: ['promo'] }))).join(), /unknown kind/);
  assert.match(cat.validate(of(row({ app: 'shop' }))).join(), /unknown app/);
  assert.match(cat.validate(of(row({ identity: 'root' }))).join(), /unknown identity/);
});

test('validate: missing fields, wrong types and unknown fields are named', () => {
  const r = row();
  delete r.writes;
  assert.match(cat.validate(of(r)).join(), /writes missing/);
  assert.match(cat.validate(of(row({ roles: 'owner' }))).join(), /roles missing or not array/);
  assert.match(cat.validate(of(row({ extra: 1 }))).join(), /unknown field extra/);
  assert.match(cat.validate(of(row({ round: 'round one' }))).join(), /round missing or not round/);
  assert.deepEqual(cat.validate({ version: 2, scenarios: [] }), ['version must be 1', 'scenarios must be a non-empty list']);
});

test('validate: id rules (variants allowed), retired outside rounds and files, safe file paths, no issue ids', () => {
  for (const id of ['ZZ-02', 'ZZ-PUB-01', 'ZZ-07b', 'ZZ-06.m', 'ZZ-18@account-manager', 'CRM-REV-03', 'CRM-REV-PREP']) {
    assert.deepEqual(cat.validate(of(row({ id }))), [], id);
  }
  for (const id of ['zz-01', 'ZZ-1', 'ZZ01', 'ZZ-01@Owner']) assert.match(cat.validate(of(row({ id }))).join(), /id does not follow/, id);
  assert.match(cat.validate(of(row({ status: 'retired', round: 'R1-2026-11' }))).join(), /retired scenario is in no round/);
  assert.match(cat.validate(of(row({ status: 'retired', file: 'demo/zz-01.cjs' }))).join(), /retired scenario keeps no scenario file/);
  assert.match(cat.validate(of(row({ file: '../x.cjs' }))).join(), /file must be/);
  assert.match(cat.validate(of(row({ story: 'Built for AA-1234' }))).join(), /internal issue id/);
});

test('checkManifest: a missing row, a retired / after-lane / writing / paid row and an identity mismatch are refused', () => {
  const c = of(row({ id: 'ZZ-01' }), row({ id: 'ZZ-02', status: 'retired' }), row({ id: 'ZZ-03', status: 'after-lane' }),
    row({ id: 'ZZ-04', writes: true }), row({ id: 'ZZ-05', writes: true, paid: true }));
  assert.deepEqual(cat.checkManifest(c, [{ id: 'ZZ-01', identity: 'crm' }]), []);
  const errs = cat.checkManifest(c, [{ id: 'ZZ-09', identity: 'crm' }, { id: 'ZZ-02', identity: 'crm' }, { id: 'ZZ-03', identity: 'crm' },
    { id: 'ZZ-04', identity: 'crm' }, { id: 'ZZ-05', identity: 'crm' }, { id: 'ZZ-01', identity: 'studio' }]).join('\n');
  assert.match(errs, /ZZ-09: no catalogue row/);
  assert.match(errs, /ZZ-02: retired scenarios never run/);
  assert.match(errs, /ZZ-03: status after-lane/);
  assert.match(errs, /ZZ-04: the catalogue says it writes/);
  assert.match(errs, /ZZ-05: the catalogue says it is paid/);
  assert.match(errs, /ZZ-01: catalogue identity crm, manifest identity studio/);
});

test('checkFiles: a file without a row, a moved file, another app and a dangling file name are refused', () => {
  const c = of(row({ id: 'ZZ-01', file: 'demo/zz-01.cjs' }), row({ id: 'ZZ-02', file: 'demo/gone.cjs' }));
  const errs = cat.checkFiles(c, [
    { rel: 'demo/zz-01.cjs', sc: { id: 'ZZ-01', app: 'booking' } },
    { rel: 'demo/zz-03.cjs', sc: { id: 'ZZ-03', app: 'crm' } },
  ]).join('\n');
  assert.match(errs, /ZZ-01: catalogue app crm, scenario app booking/);
  assert.match(errs, /zz-03\.cjs: scenario ZZ-03 has no catalogue row/);
  assert.match(errs, /ZZ-02: file demo\/gone\.cjs does not exist/);
});
