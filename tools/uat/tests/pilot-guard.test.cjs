// Unit tests of the pilot guard (AA-855, lib/pilot-guard.cjs): the allow-list decision, the scopes of a scenario, the
// check against a fake browser, and exit code 5 in the dry-run report. No browser, no network, no AWS:
//   node --test tools/uat/tests
// Fixtures use invented tenants only (made-up ids and names; the synthetic names are the invented E2E ones).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const g = require('../lib/pilot-guard.cjs');
const core = require('../lib/dryrun-core.cjs');

const ID_A = '11111111-2222-4333-8444-555555555555'; // invented
const ID_B = '99999999-8888-4777-8666-555555555555'; // invented
const allow = (local = null) => g.buildAllowlist(local);
const senVangId = g.uuid5(g.CRM_NAMESPACE, 'aa-crm-synthetic-agency:sen-vang');

// ── uuid5 / allow-list ──────────────────────────────────────────────────────────────────────────────────────────────

test('uuid5 matches the RFC 4122 reference value (namespace DNS, "python.org")', () => {
  assert.equal(g.uuid5('6ba7b810-9dad-11d1-80b4-00c04fd430c8', 'python.org'), '886313e1-3b8a-5372-9b90-0c9aee199e5d');
});

test('buildAllowlist: built-in names and CRM ids; a local file pins ids; builtin false empties it; bad files throw', () => {
  const a = allow();
  assert.equal(a.ids.get(senVangId), 'sen-vang');
  assert.equal(a.names.get('Atlas & Hearth'), 'atlas-hearth');
  const b = allow({ content: { [ID_A]: 'terra-family-expeditions' } });
  assert.equal(b.ids.get(ID_A), 'terra-family');
  assert.ok(b.pinned.get('terra-family').has(ID_A));
  const off = allow({ builtin: false });
  assert.equal(off.ids.size + off.names.size, 0);
  assert.throws(() => allow([]), /not a JSON object/);
  assert.throws(() => allow({ content: ['x'] }), /must map tenant ids/);
  assert.throws(() => allow({ crm: { 'not-an-id': 'sen-vang' } }), /not a tenant id/);
  assert.throws(() => allow({ crm: { [ID_A]: '' } }), /has no slug/);
});

test('loadLocal: no file is null, a file that is not JSON throws (fail closed)', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'uat-allow-'));
  try {
    assert.equal(g.loadLocal(path.join(dir, 'none.json')), null);
    fs.writeFileSync(path.join(dir, 'bad.json'), '{ not json');
    assert.throws(() => g.loadLocal(path.join(dir, 'bad.json')), /not JSON/);
    fs.writeFileSync(path.join(dir, 'ok.json'), JSON.stringify({ content: { [ID_A]: 'atlas-hearth' } }));
    assert.deepEqual(g.loadLocal(path.join(dir, 'ok.json')), { content: { [ID_A]: 'atlas-hearth' } });
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

// ── evaluate ────────────────────────────────────────────────────────────────────────────────────────────────────────

test('evaluate: allow-list hit by id (CRM agency) and by invented name (Content tenant)', () => {
  const v1 = g.evaluate({ tenant_id: senVangId, display_name: 'anything' }, { scope: 'crm', allow: allow() });
  assert.deepEqual([v1.ok, v1.slug, v1.matched_by], [true, 'sen-vang', 'id']);
  const v2 = g.evaluate({ tenant_id: ID_A, tenant_name: 'Atlas & Hearth' }, { scope: 'content', allow: allow() });
  assert.deepEqual([v2.ok, v2.slug, v2.matched_by], [true, 'atlas-hearth', 'name']);
  const v3 = g.evaluate({ tenant_id: ID_A, tenant_name: 'x' }, { scope: 'content', allow: allow({ content: { [ID_A]: 'trail-pulse' } }) });
  assert.deepEqual([v3.ok, v3.slug], [true, 'trail-pulse']);
});

test('evaluate: allow-list miss refuses, and the refusal never carries the tenant name', () => {
  const v = g.evaluate({ tenant_id: ID_B, tenant_name: 'Lotus Bay Real Travel' }, { scope: 'content', allow: allow() });
  assert.equal(v.ok, false);
  assert.equal(v.code, 'pilot_guard');
  assert.match(v.reason, /^pilot_guard: Content studio tenant 99999999… is not in the synthetic allow-list$/);
  assert.ok(!v.reason.includes('Lotus'));
});

test('evaluate: is_pilot=true refuses even on an allow-listed tenant; other pilot / real markers refuse too', () => {
  const base = { tenant_id: senVangId, display_name: 'Lữ hành Sen Vàng' };
  assert.match(g.evaluate({ ...base, is_pilot: true }, { scope: 'crm', allow: allow() }).reason, /is the pilot \(is_pilot=true\)/);
  assert.match(g.evaluate({ ...base, is_pilot: 'yes' }, { scope: 'crm', allow: allow() }).reason, /is_pilot is not false/);
  assert.match(g.evaluate({ ...base, is_pilot: null }, { scope: 'crm', allow: allow() }).reason, /is_pilot is not false/);
  assert.match(g.evaluate({ ...base, pilot_ends_at: '2027-01-01' }, { scope: 'crm', allow: allow() }).reason, /pilot end date/);
  assert.match(g.evaluate({ ...base, is_synthetic: false }, { scope: 'crm', allow: allow() }).reason, /is not synthetic/);
  assert.match(g.evaluate({ ...base, kind: 'Real' }, { scope: 'crm', allow: allow() }).reason, /of kind real/);
  assert.match(g.evaluate({ ...base, kind: 'pilot' }, { scope: 'crm', allow: allow() }).reason, /of kind pilot/);
  assert.equal(g.evaluate({ ...base, is_pilot: false, kind: 'demo', is_synthetic: true }, { scope: 'crm', allow: allow() }).ok, true);
});

test('evaluate: a missing field fails closed (no tenant id, no name, not an object, unknown scope, no allow-list)', () => {
  assert.match(g.evaluate({ tenant_name: 'Atlas & Hearth' }, { scope: 'content', allow: allow() }).reason, /has no tenant id/);
  assert.match(g.evaluate({ tenant_id: 'abc', tenant_name: 'Atlas & Hearth' }, { scope: 'content', allow: allow() }).reason, /has no tenant id/);
  assert.match(g.evaluate({ tenant_id: ID_A }, { scope: 'content', allow: allow() }).reason, /no name in the answer/);
  assert.match(g.evaluate({ tenant_id: ID_A, display_name: 'Atlas & Hearth' }, { scope: 'content', allow: allow() }).reason, /no name in the answer/);
  assert.match(g.evaluate(null, { scope: 'crm', allow: allow() }).reason, /not an object/);
  assert.match(g.evaluate([], { scope: 'crm', allow: allow() }).reason, /not an object/);
  assert.match(g.evaluate({ tenant_id: ID_A }, { scope: 'billing', allow: allow() }).reason, /unknown scope/);
  assert.match(g.evaluate({ tenant_id: ID_A }, { scope: 'crm' }).reason, /no allow-list/);
});

test('evaluate: a pinned slug matches by id only; `only` narrows to some slugs; builtin false refuses every tenant', () => {
  const pinned = allow({ content: { [ID_A]: 'atlas-hearth' } });
  assert.match(g.evaluate({ tenant_id: ID_B, tenant_name: 'Atlas & Hearth' }, { scope: 'content', allow: pinned }).reason,
    /carries the name of atlas-hearth, but not its pinned id/);
  const southern = g.uuid5(g.CRM_NAMESPACE, 'aa-crm-synthetic-agency:southern-cross');
  assert.match(g.evaluate({ tenant_id: southern }, { scope: 'crm', allow: allow(), only: ['sen-vang'] }).reason,
    /is southern-cross; this step runs only on sen-vang/);
  assert.equal(g.evaluate({ tenant_id: senVangId }, { scope: 'crm', allow: allow(), only: ['sen-vang'] }).ok, true);
  assert.equal(g.evaluate({ tenant_id: senVangId, display_name: 'Lữ hành Sen Vàng' }, { scope: 'crm', allow: allow({ builtin: false }) }).ok, false);
});

// ── scopes ──────────────────────────────────────────────────────────────────────────────────────────────────────────

test('scopesFor: by identity, by pilotGuard, CRM review chunks by app; a signed-in scenario without a scope throws', () => {
  assert.deepEqual(g.scopesFor({ id: 'A', identity: 'studio' }, null), { scopes: ['content'], only: null });
  assert.deepEqual(g.scopesFor({ id: 'A', identity: 'studio-editor' }, 'f'), { scopes: ['content'], only: null });
  assert.deepEqual(g.scopesFor({ id: 'A', identity: 'crm' }, 'f'), { scopes: ['crm'], only: null });
  assert.deepEqual(g.scopesFor({ id: 'A', identity: 'cis-admin' }, 'f'), { scopes: [], only: null });
  assert.deepEqual(g.scopesFor({ id: 'A', app: 'crm' }, 'f'), { scopes: ['crm'], only: null });
  assert.deepEqual(g.scopesFor({ id: 'A', app: 'crm' }, null), { scopes: [], only: null });
  assert.deepEqual(g.scopesFor({ id: 'A', identity: 'studio', pilotGuard: { scopes: ['content', 'crm'] } }, 'f'),
    { scopes: ['content', 'crm'], only: null });
  assert.deepEqual(g.scopesFor({ id: 'A', app: 'crm', pilotGuard: { scopes: ['crm'], only: ['sen-vang'] } }, 'f'),
    { scopes: ['crm'], only: ['sen-vang'] });
  assert.throws(() => g.scopesFor({ id: 'A', app: 'tripplanner' }, 'f'), /pilot_guard: A is signed in but names no identity/);
  assert.throws(() => g.scopesFor({ id: 'A', pilotGuard: { scopes: ['shop'] } }, 'f'), /pilotGuard needs scopes/);
});

test('the CRM review data steps run only on the invented sen-vang', () => {
  for (const f of ['prep.cjs', 'cleanup.cjs']) {
    const sc = require(path.join(__dirname, '..', 'scenarios', 'crm', f));
    assert.deepEqual(sc.pilotGuard, { scopes: ['crm'], only: ['sen-vang'] }, f);
  }
});

// ── check() against a fake browser ──────────────────────────────────────────────────────────────────────────────────

function fakeBrowser(answers) {
  const calls = [];
  let closed = 0;
  return {
    calls,
    closed: () => closed,
    newContext: async () => ({
      request: {
        get: async (url) => {
          calls.push(new URL(url).pathname);
          const a = answers.shift() || { status: 500, body: null };
          return { status: () => a.status, json: async () => { if (a.body === null) throw new Error('no json'); return a.body; } };
        },
      },
      close: async () => { closed++; },
    }),
  };
}

test('check: a synthetic tenant passes, the context is closed; no scope needs no session', async () => {
  const b = fakeBrowser([{ status: 200, body: { tenant_id: ID_A, tenant_name: 'Trail Pulse' } }]);
  const v = await g.check(b, 'state.json', { scopes: ['content'] }, { origin: 'https://agency.example.invalid', local: null });
  assert.equal(v.ok, true);
  assert.deepEqual(b.calls, ['/api/tenant/me']);
  assert.equal(b.closed(), 1);
  assert.deepEqual(await g.check(fakeBrowser([]), null, { scopes: [] }), { ok: true, checked: [] });
});

test('check: a pilot, a non-200 answer, a non-JSON body and a missing session all refuse', async () => {
  const opts = { origin: 'https://agency.example.invalid', local: null };
  const pilot = await g.check(fakeBrowser([{ status: 200, body: { tenant_id: senVangId, is_pilot: true } }]), 's', { scopes: ['crm'] }, opts);
  assert.match(pilot.reason, /is_pilot=true/);
  assert.match((await g.check(fakeBrowser([{ status: 403, body: {} }]), 's', { scopes: ['content'] }, opts)).reason, /HTTP 403/);
  assert.match((await g.check(fakeBrowser([{ status: 200, body: null }]), 's', { scopes: ['content'] }, opts)).reason, /not an object/);
  assert.match((await g.check(fakeBrowser([]), null, { scopes: ['crm'] }, opts)).reason, /no signed-in session/);
  assert.match((await g.check(fakeBrowser([]), 's', { scopes: ['crm'] }, { ...opts, local: [] })).reason, /not a JSON object/);
});

test('check: a CRM 401 renews once through /auth/refresh, then reads /bff/me again; both scopes must pass', async () => {
  const b = fakeBrowser([{ status: 401, body: {} }, { status: 200, body: '' }, { status: 200, body: { tenant_id: senVangId } }]);
  const v = await g.check(b, 's', { scopes: ['crm'] }, { origin: 'https://agency.example.invalid', local: null });
  assert.equal(v.ok, true);
  assert.deepEqual(b.calls, ['/bff/me', '/auth/refresh', '/bff/me']);
  const two = fakeBrowser([{ status: 200, body: { tenant_id: ID_A, tenant_name: 'Atlas & Hearth' } },
    { status: 200, body: { tenant_id: ID_B, display_name: 'Lotus Bay Real Travel' } }]);
  const w = await g.check(two, 's', { scopes: ['content', 'crm'] }, { origin: 'https://agency.example.invalid', local: null });
  assert.match(w.reason, /CRM agency 99999999… is not in the synthetic allow-list/);
});

test('describeVerdict and syntheticRowPatterns', () => {
  assert.equal(g.describeVerdict({ ok: true, checked: [{ scope: 'crm', slug: 'sen-vang', matched_by: 'id' }] }), 'ok: crm sen-vang (by id)');
  assert.equal(g.describeVerdict({ ok: false, reason: 'pilot_guard: x' }), 'pilot_guard: x');
  const res = g.syntheticRowPatterns().map((x) => new RegExp(x, 'i'));
  assert.ok(res.some((r) => r.test('Atlas & Hearth · growth')));
  assert.ok(!res.some((r) => r.test('Lotus Bay Real Travel')));
});

// ── exit code 5 in the dry-run report ───────────────────────────────────────────────────────────────────────────────

test('dry run: a refused identity is BLOCKED with pilot_guard and the run exits 5, before any FAIL counts', () => {
  const e = { id: 'ZZ-01', app: 'content-studio', identity: 'studio', title: 'T', steps: 2 };
  const blocked = core.outcome(e, { blocked: 'BLOCKED: pilot_guard: tenant 99999999… is not in the synthetic allow-list', pilotGuard: true });
  assert.equal(blocked.verdict, 'BLOCKED');
  assert.equal(blocked.pilot_guard, true);
  const fromRecord = core.outcome(e, { result: { verdict: 'BLOCKED', pilot_guard: 'pilot_guard: refused' }, exitCode: 5 });
  assert.deepEqual([fromRecord.verdict, fromRecord.pilot_guard, fromRecord.reason], ['BLOCKED', true, 'pilot_guard: refused']);
  const byCode = core.outcome(e, { result: null, exitCode: 5 });
  assert.equal(byCode.pilot_guard, true);
  const fail = core.outcome(e, { result: { verdict: 'FAIL', failed_step: 1, failed_error: 'x', steps_total: 2 }, timeline: [] });
  assert.equal(core.exitCode([fail, blocked]), 5);
  assert.equal(core.exitCode([fail]), 2);
  assert.equal(g.EXIT_PILOT_GUARD, 5);
  assert.equal(core.EXIT_PILOT_GUARD, 5);
});

test('record.cjs and run.sh stop on the guard before any video: exit 5, guard before the recorded context', () => {
  const rec = fs.readFileSync(path.join(__dirname, '..', 'record.cjs'), 'utf8');
  const guardAt = rec.indexOf('pilotGuard.check(browser');
  const contextAt = rec.indexOf('recordVideo');
  assert.ok(guardAt > 0 && guardAt < contextAt, 'the guard runs before the recorded context is created');
  assert.match(rec, /process\.exitCode = pilotGuard\.EXIT_PILOT_GUARD/);
  const run = fs.readFileSync(path.join(__dirname, '..', 'run.sh'), 'utf8');
  assert.ok(run.indexOf('--guard-only') < run.indexOf('tts.py'), 'run.sh checks the guard before the TTS');
  assert.match(run, /\[ "\$rc" = 5 \] && .*exit 5/);
});
