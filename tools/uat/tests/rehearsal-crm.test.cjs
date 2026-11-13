// Unit tests of the pilot rehearsal CRM scenarios (REH-06 .. REH-10b; runbook docs/ops/runbooks/pilot-rehearsal.md):
// the pilot-guard pin of the rehearsal identities, the agency id, the scenario shells (captions, identities, the writes
// each may make) and the write-set order. No browser, no network:  node --test tools/uat/tests/*.test.cjs
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

const g = require('../lib/pilot-guard.cjs');
const core = require('../lib/dryrun-core.cjs');
const cat = require('../lib/catalogue.cjs');
const crm = require('../lib/crm-signin.cjs');
const guard = require('../lib/net-guard.cjs');

const SCEN = path.join(__dirname, '..', 'scenarios');
const REH = fs.readdirSync(path.join(SCEN, 'crm')).filter((f) => /^reh-.*\.cjs$/.test(f)).sort();
const load = (f) => require(path.join(SCEN, 'crm', f));
const OTHER = '0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d'; // invented

test('the rehearsal agency id is the CRM seed id of its key (the fixture id of the runbook)', () => {
  const id = g.uuid5(g.CRM_NAMESPACE, 'aa-crm-synthetic-agency:pilot-rehearsal-01');
  assert.equal(id, '41ea21ee-77ee-5474-bd6d-aa738d2da990');
  assert.equal(require(path.join(SCEN, 'crm', '_reh.cjs')).AGENCY_ID, id);
});

test('pilot guard: the rehearsal identities are pinned to pilot-rehearsal-01, by id only; a scenario cannot widen it', () => {
  const allow = g.buildAllowlist(null);
  const id = g.uuid5(g.CRM_NAMESPACE, 'aa-crm-synthetic-agency:pilot-rehearsal-01');
  for (const who of ['crm-rehearsal', 'crm-rehearsal-agent']) {
    const sc = g.scopesFor({ id: 'REH-99-x', identity: who }, 'state.json');
    assert.deepEqual(sc, { scopes: ['crm'], only: ['pilot-rehearsal-01'] }, who);
    assert.equal(g.evaluate({ tenant_id: id, display_name: 'anything' }, { scope: 'crm', allow, only: sc.only }).ok, true);
    // Another synthetic agency, the agency's name under another id, a pilot marker: all refused.
    const senVang = g.uuid5(g.CRM_NAMESPACE, 'aa-crm-synthetic-agency:sen-vang');
    assert.match(g.evaluate({ tenant_id: senVang }, { scope: 'crm', allow, only: sc.only }).reason, /runs only on pilot-rehearsal-01/);
    assert.match(g.evaluate({ tenant_id: OTHER, display_name: 'E2E Pilot Rehearsal Travel' }, { scope: 'crm', allow, only: sc.only }).reason, /not in the synthetic allow-list/);
    assert.match(g.evaluate({ tenant_id: id, is_pilot: true }, { scope: 'crm', allow, only: sc.only }).reason, /is the pilot/);
    assert.throws(() => g.scopesFor({ id: 'REH-99-x', identity: who, pilotGuard: { scopes: ['crm'] } }, 'f'), /runs on pilot-rehearsal-01 only/);
  }
  assert.deepEqual(g.scopesFor({ id: 'REH-99-x', identity: 'crm-staff' }, 'f'), { scopes: [], only: null });
  assert.ok(g.syntheticRowPatterns().includes('E2E Pilot Rehearsal Travel'));
});

test('identities: the rehearsal ones are writable, never in the read-only dry-run set, and signed in by lib/signin.cjs', () => {
  for (const who of ['crm-rehearsal', 'crm-rehearsal-agent', 'crm-staff']) {
    assert.ok(core.IDENTITIES.includes(who) && core.WRITABLE_IDENTITIES.includes(who) && core.SIGNIN_ORDER.includes(who), who);
    assert.ok(cat.IDENTITIES.includes(who), who);
  }
  assert.equal(crm.IDENTITIES.RO.secret, 'crm/dev/e2e-test-crm/pilot-rehearsal-01-owner');
  assert.equal(crm.IDENTITIES.RA.secret, 'crm/dev/e2e-test-crm/pilot-rehearsal-01-agent');
  const src = fs.readFileSync(path.join(__dirname, '..', 'lib', 'signin.cjs'), 'utf8');
  assert.match(src, /'crm-rehearsal': 'RO', 'crm-rehearsal-agent': 'RA'/);
  assert.match(src, /e2e-crm-staff@e2e-mail\.lumiguides\.it\.com', prefix: 'inbound-admin\/'/);
  assert.ok(!/console\.log\([^)]*(password|totp|creds|code)\b/i.test(src), 'no secret is printed');
});

test('every REH scenario: id REH-<nn>-<slug>, English and Vietnamese captions, no issue ids in captions, rehearsal identity', () => {
  assert.ok(REH.length >= 9, REH.join(', '));
  for (const f of REH) {
    const sc = load(f);
    assert.match(sc.id, cat.ID, f);
    assert.match(sc.id, /^REH-\d{2}[a-z]?-/, f);
    assert.equal(sc.app, 'crm', f);
    assert.ok(['crm-rehearsal', 'crm-rehearsal-agent', 'crm-staff'].includes(sc.identity), f);
    assert.equal(sc.readOnly, true, `${f}: the browser guard stays on`);
    assert.equal(typeof sc.prepare, 'function', `${f}: signs its identity in before the browser starts`);
    for (const [i, s] of sc.steps.entries()) {
      assert.ok(s.caption && s.caption.en && s.caption.vi, `${f} step ${i + 1}`);
      assert.ok(!/\bAA-?\d{3,4}\b/.test(`${s.caption.en} ${s.caption.vi}`), `${f} step ${i + 1}: no issue id in a caption`);
    }
  }
});

test('writes: method + path on the CRM BFF of the agency host and the public proposal / traveller API of the client host', () => {
  const partner = crm.PARTNER.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const client = crm.CLIENT.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  for (const f of REH) {
    const sc = load(f);
    if (sc.identity === 'crm-staff') {
      assert.deepEqual(sc.allowWrites || [], [], `${f}: the staff view writes nothing`);
      continue;
    }
    assert.ok(sc.allowWrites.length > 0, f);
    for (const w of sc.allowWrites) {
      const a = guard.parseAllow(w);
      assert.ok(a.methods && a.methods.length, `${f}: ${w} names its method(s)`);
      const src = w.slice(w.indexOf(' ') + 1); // the regex source after the method list
      assert.ok(src.startsWith(`^${partner}/bff/`) || src.startsWith(`^${client}/crm/public/v1/proposal/`)
        || src.startsWith(`^${client}/crm/public/v1/traveller/`), `${f}: ${w}`);
      assert.ok(src.endsWith('(?:[?#]|$)'), `${f}: ${w} is anchored at the end of the path`);
    }
    assert.equal(sc.paid, false, `${f}: no paid model call`);
    assert.ok(sc.steps.some((s) => s.writes), `${f}: marks its writing steps`);
    // Every writing scenario caps its writes in step 1 (R.cap -> limitWrites), before any page loads.
    assert.match(fs.readFileSync(path.join(SCEN, 'crm', f), 'utf8'), /meta\.writes = await R\.cap\(page, \[/, `${f}: caps its writes`);
  }
  const allowed = (f, method, url) => guard.allowsWrite(guard.compileAllow(load(f).allowWrites), method, url);
  const T = `${crm.PARTNER}/bff/trips/${OTHER}`;
  const P = `${crm.PARTNER}/bff/proposals/${OTHER}`;
  // REH-06: the owner, the dates and the stage, each by its own method only; never a trip DELETE.
  assert.ok(allowed('reh-06-lead.cjs', 'POST', `${T}/owner`) && allowed('reh-06-lead.cjs', 'PATCH', T) && allowed('reh-06-lead.cjs', 'POST', `${T}/stage`));
  assert.ok(!allowed('reh-06-lead.cjs', 'DELETE', T) && !allowed('reh-06-lead.cjs', 'PATCH', `${T}/owner`) && !allowed('reh-06-lead.cjs', 'POST', `${T}/stage/undo`));
  // REH-07: the agent never publishes, sends, deletes or reorders.
  for (const [m, u] of [['POST', `${P}/discount-approval`], ['POST', `${P}/blocks/${OTHER}/aa-options`], ['POST', `${P}/blocks/${OTHER}/options`],
    ['POST', `${P}/days/${OTHER}/blocks`], ['PUT', `${P}/inclusions`], ['PATCH', `${P}/builder`], ['POST', `${T}/builder`]]) {
    assert.ok(allowed('reh-07-quote.cjs', m, u), `REH-07 ${m} ${u}`);
  }
  for (const [m, u] of [['POST', `${P}/publish`], ['POST', `${P}/send`], ['DELETE', `${P}/options/${OTHER}`], ['DELETE', `${P}/blocks/${OTHER}`],
    ['PUT', `${P}/days/order`], ['DELETE', `${P}/days/${OTHER}`], ['POST', `${P}/discount-approval/${OTHER}`], ['PATCH', `${P}/options/${OTHER}`]]) {
    assert.ok(!allowed('reh-07-quote.cjs', m, u), `REH-07 must refuse ${m} ${u}`);
  }
  // Client host: the named actions only, never decline / sign-out / companions / rooming.
  const C = `${crm.CLIENT}/crm/public/v1`;
  assert.ok(allowed('reh-08-accept.cjs', 'POST', `${C}/proposal/hold`) && allowed('reh-08-accept.cjs', 'POST', `${C}/proposal/accept`));
  assert.ok(!allowed('reh-08-accept.cjs', 'POST', `${C}/proposal/change-request`) && !allowed('reh-08-accept.cjs', 'POST', `${crm.PARTNER}/bff/trips/${OTHER}`));
  assert.ok(allowed('reh-10-portal.cjs', 'PUT', `${C}/traveller/stage3`) && !allowed('reh-10-portal.cjs', 'POST', `${C}/traveller/stage3`));
  for (const x of ['sign-out', 'companions', 'rooming', 'switch']) assert.ok(!allowed('reh-10-portal.cjs', 'POST', `${C}/traveller/${x}`), x);
  assert.ok(allowed('reh-08b-deposit.cjs', 'POST', `${C}/proposal/invoices/${OTHER}/claim`) && !allowed('reh-08b-deposit.cjs', 'POST', `${C}/proposal/invoices/${OTHER}/card`));
  // The setup: payment instructions (PUT) and agreements (POST) only; no disconnect.
  assert.ok(allowed('reh-02b-agency-setup.cjs', 'PUT', `${crm.PARTNER}/bff/settings/payment-methods/manual`));
  assert.ok(!allowed('reh-02b-agency-setup.cjs', 'POST', `${crm.PARTNER}/bff/settings/payment-methods/${OTHER}/disconnect`));
  assert.ok(!allowed('reh-02b-agency-setup.cjs', 'PATCH', `${crm.PARTNER}/bff/agreements/${OTHER}`));
});

test('mail guard: invented addresses only; every mail-sending step checks the traveller before its click', () => {
  const R = require(path.join(SCEN, 'crm', '_reh.cjs'));
  for (const a of ['rehearsal.traveller@example.invalid', 'x@sub.example.invalid', 'e2e-traveller@e2e-mail.lumiguides.it.com']) assert.ok(R.inventedAddress(a), a);
  for (const a of ['someone@gmail.com', 'x@invalid.com', 'x@example.invalid.com', 'x@e2e-mail.lumiguides.it.com.evil.io', 'not-an-address', '', null,
    'a@b@example.invalid']) assert.ok(!R.inventedAddress(a), String(a));
  // The step text before each mail-sending click calls R.checkTraveller first.
  const src = (f) => fs.readFileSync(path.join(SCEN, 'crm', f), 'utf8');
  const before = (f, click) => {
    const s = src(f);
    const i = s.indexOf(click);
    assert.ok(i > 0, `${f}: ${click}`);
    assert.ok(s.lastIndexOf('R.checkTraveller(page, s)', i) > s.lastIndexOf('step(', i), `${f}: checkTraveller before ${click}`);
  };
  before('reh-07b-approve.cjs', "tab.getByTestId('builder-send')");
  before('reh-08b-deposit.cjs', "name: 'Record payment'");
  before('reh-08c-aa-confirmed.cjs', 'name: /portal link/i');
  before('reh-10-portal.cjs', "page.getByTestId('portal-send-code')");
  before('reh-10-portal.cjs', "page.getByTestId('portal-sign-code')");
  before('reh-10c-itinerary.cjs', "page.getByTestId('portal-send-code')");
  before('reh-08-accept.cjs', "page.getByTestId('client-accept')");
  assert.match(src('reh-06-lead.cjs'), /R\.checkTraveller\(page, s\)/);
});

test('write set: the rehearsal entries follow the runbook order; the staff view is not in it', () => {
  const ws = require(path.join(SCEN, 'write-set.cjs')).filter((x) => x.startsWith('crm/reh-'));
  assert.deepEqual(ws, ['crm/reh-02b-agency-setup.cjs', 'crm/reh-06-lead.cjs', 'crm/reh-07-quote.cjs', 'crm/reh-07b-approve.cjs', 'crm/reh-08-accept.cjs',
    'crm/reh-08b-deposit.cjs', 'crm/reh-08c-aa-confirmed.cjs', 'crm/reh-10a-show-aa-line.cjs', 'crm/reh-10-portal.cjs',
    'crm/reh-10c-itinerary.cjs']);
  for (const f of ws) assert.doesNotThrow(() => core.describeWrite(require(path.join(SCEN, f)), f));
});
