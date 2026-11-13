// Unit tests of the pilot rehearsal studio scenarios (AA-1086, REH-03-* .. REH-04b-*) and their helpers: the invented
// brand guide .docx, tour X and the planner link, the test channel secret reader, the studio-rehearsal pilot-guard pin,
// the allow-lists, captions and the catalogue / write-set agreement. No browser, no network:
//   node --test tools/uat/tests/*.test.cjs
// Ids other than the rehearsal agency's public seed id are invented.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const reh = require('../lib/rehearsal.cjs');
const g = require('../lib/pilot-guard.cjs');
const cat = require('../lib/catalogue.cjs');
const core = require('../lib/dryrun-core.cjs');
const { zipEntry } = require('../lib/uat-page.cjs');

const SCEN = path.join(__dirname, '..', 'scenarios');
const FILES = ['reh-03-brand', 'reh-03-adopt', 'reh-04-topics', 'reh-04-blog', 'reh-04-linkedin', 'reh-04-facebook',
  'reh-04-edit', 'reh-04b-wordpress', 'reh-04b-facebook', 'reh-04b-takedown'];
const load = (f) => require(path.join(SCEN, 'content-studio', `${f}.cjs`));
const ORIGIN = 'https://agency.example.invalid';
const T = `${ORIGIN}/api/tenant/v1`;
const ID = '0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d'; // invented

// ── fixtures ────────────────────────────────────────────────────────────────────────────────────────────────────────

test('rehearsal agency: the seed catalogue id of the key pilot-rehearsal-01 (UUIDv5), its slug and invented name', () => {
  assert.equal(g.uuid5(g.CRM_NAMESPACE, 'aa-crm-synthetic-agency:pilot-rehearsal-01'), reh.TENANT.id);
  assert.equal(reh.TENANT.slug, 'pilot-rehearsal-01');
  assert.equal(reh.secretId({}), 'crm/dev/e2e-test-crm/pilot-rehearsal-01-owner');
  assert.equal(reh.secretId({ UAT_STUDIO_REHEARSAL_SECRET: 'x/y' }), 'x/y');
});

test('brand guide .docx: a valid stored ZIP whose document holds every paragraph, XML-escaped, CRC-32 right', () => {
  const buf = reh.brandGuideDocx();
  const doc = zipEntry(buf, 'word/document.xml').toString('utf8');
  for (const p of reh.BRAND_PARAGRAPHS) {
    const esc = p.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    assert.ok(doc.includes(`<w:t xml:space="preserve">${esc}</w:t>`), p);
  }
  assert.ok(zipEntry(buf, '[Content_Types].xml').toString('utf8').includes('/word/document.xml'));
  assert.ok(zipEntry(buf, '_rels/.rels').toString('utf8').includes('officeDocument'));
  // Each local header's CRC matches its data (python-docx / zipfile check it).
  let p = 0;
  for (let n = 0; n < 3; n++) {
    assert.equal(buf.readUInt32LE(p), 0x04034b50);
    const crc = buf.readUInt32LE(p + 14);
    const size = buf.readUInt32LE(p + 18);
    const nameLen = buf.readUInt16LE(p + 26);
    const data = buf.subarray(p + 30 + nameLen, p + 30 + nameLen + size);
    assert.equal(zlib.crc32(data) >>> 0, crc);
    p += 30 + nameLen + size;
  }
  assert.ok(buf.length < 5 * 1024 * 1024);
  // The guide names the brand first and carries the parser's headings and labels.
  assert.equal(reh.BRAND_PARAGRAPHS[0], reh.BRAND.name);
  for (const head of ['Brand identity', 'Tone of voice', 'Writing style', 'Should not write', 'Call to action', 'Signature words']) {
    assert.ok(reh.BRAND_PARAGRAPHS.includes(head), head);
  }
  assert.ok(reh.BRAND_PARAGRAPHS.includes(reh.BRAND.cta));
});

test('tour X: env required, an id only; found by tour_id or published id; the planner link stays on the agency', () => {
  assert.throws(() => reh.tourX({}), /UAT_REH_TOUR_X is not set/);
  assert.throws(() => reh.tourX({ UAT_REH_TOUR_X: 'x; rm -rf' }), /not a tour id/);
  assert.equal(reh.tourX({ UAT_REH_TOUR_X: ` ${ID} ` }), ID);
  const rows = [{ id: 'p-1', tour_id: 'LA-0001' }, { id: ID, tour_id: 'LA-0002' }];
  assert.equal(reh.findTour(rows, 'la-0001').id, 'p-1');
  assert.equal(reh.findTour(rows, ID).tour_id, 'LA-0002');
  assert.equal(reh.findTour(rows, 'none'), null);
  assert.equal(reh.findTour(null, 'x'), null);
  assert.match(reh.plannerLink('LA-0002'), /^https:\/\/[^/]+\/pilot-rehearsal-01\/plan\?tour=LA-0002$/);
});

test('channelCreds: reads the test channel JSON in memory; names a missing key or bad JSON, never the value', () => {
  const run = (out) => () => out;
  assert.deepEqual(reh.channelCreds('facebook', run('{"page_id":"1","page_access_token":"tok-secret","x":1}')),
    { page_id: '1', page_access_token: 'tok-secret' });
  assert.throws(() => reh.channelCreds('wordpress', run('{"site_url":"https://a.example.invalid"}')), /lacks app_user, app_password/);
  assert.throws(() => reh.channelCreds('wordpress', run('not json tok-secret')), (e) => /is not JSON/.test(e.message) && !/tok-secret/.test(e.message));
  assert.throws(() => reh.channelCreds('wordpress', () => { const e = new Error('x'); e.stderr = 'ResourceNotFoundException arn:aws:x'; throw e; }),
    (e) => /does not exist/.test(e.message) && !/arn:/.test(e.message));
  assert.throws(() => reh.channelCreds('mastodon', run('{}')), /unknown channel/);
});

// ── pilot guard ─────────────────────────────────────────────────────────────────────────────────────────────────────

test('pilot guard: studio-rehearsal is pinned to pilot-rehearsal-01, matched by its id only', () => {
  const allow = g.buildAllowlist(null);
  const s = g.scopesFor({ id: 'REH-91-x', identity: 'studio-rehearsal' }, 'state.json');
  assert.deepEqual(s, { scopes: ['content'], only: ['pilot-rehearsal-01'] });
  const on = (a) => g.evaluate(a, { scope: 'content', allow, only: s.only });
  assert.equal(on({ tenant_id: reh.TENANT.id, tenant_name: reh.TENANT.name }).ok, true);
  assert.equal(on({ tenant_id: reh.TENANT.id, tenant_name: reh.TENANT.name }).matched_by, 'id');
  // The name alone (another id) is refused: the slug is pinned to its id.
  assert.match(on({ tenant_id: ID, tenant_name: reh.TENANT.name }).reason, /not its pinned id/);
  // Another synthetic tenant, and any pilot marker, are refused.
  assert.match(on({ tenant_id: ID, tenant_name: 'Atlas & Hearth (Audit)' }).reason, /runs only on pilot-rehearsal-01/);
  assert.match(on({ tenant_id: reh.TENANT.id, tenant_name: reh.TENANT.name, is_pilot: true }).reason, /is the pilot/);
  // The CRM scope of the same agency accepts its id (the CRM review specs run on it too).
  assert.equal(g.evaluate({ tenant_id: reh.TENANT.id, display_name: 'Renamed' }, { scope: 'crm', allow }).ok, true);
  assert.throws(() => g.scopesFor({ id: 'REH-91-x', identity: 'studio-rehearsal', pilotGuard: { scopes: ['content'] } }, 'f'), /runs on pilot-rehearsal-01 only/);
  assert.ok(core.IDENTITIES.includes('studio-rehearsal') && core.WRITABLE_IDENTITIES.includes('studio-rehearsal'));
  assert.ok(cat.IDENTITIES.includes('studio-rehearsal'));
});

test('signin: studio-rehearsal reads the owner secret and opens the studio on the rehearsal agency by name', () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'lib', 'signin.cjs'), 'utf8');
  assert.match(src, /'studio-rehearsal': rehearsal\.secretId\(\)/);
  assert.match(src, /who === 'studio-rehearsal' \? rehearsal\.TENANT\.name/);
});

// ── the scenarios ───────────────────────────────────────────────────────────────────────────────────────────────────

const guard = require('../lib/net-guard.cjs');
// Compiled the way record.cjs compiles allowWrites (lib/net-guard.cjs: "<METHOD> <regex>" entries pin the method).
const allowed = (sc, method, url) => guard.allowMatches(guard.compileAllow(sc.allowWrites), method, url);
const P = (u) => ['POST', u];

test('REH scenarios allow exactly their writes, each for its own method only', () => {
  const pub = [P(`${T}/publish-log/${ID}/publish`), ['DELETE', `${T}/publish-log/${ID}`]];
  const cases = {
    'reh-03-brand': [[P(`${ORIGIN}/api/tenant/admin/brand-identity`), P(`${ORIGIN}/api/tenant/admin/brand-identity/upload`),
      P(`${ORIGIN}/api/tenant/admin/brand-identity/parse`), P(`${T}/content-writing/cta-check`)],
    [P(`${T}/tours/pool/${ID}/rewrite`), ...pub, P(`${ORIGIN}/api/tenant/admin/brand-identity/other`),
      ['DELETE', `${ORIGIN}/api/tenant/admin/brand-identity`], ['PUT', `${ORIGIN}/api/tenant/admin/brand-identity`]]],
    'reh-03-adopt': [[P(`${T}/tours/pool/${ID}/rewrite`)], [P(`${T}/tours/versions/${ID}/retry`), P(`${T}/slate/refresh`), ...pub,
      ['DELETE', `${T}/tours/pool/${ID}/rewrite`]]],
    'reh-04-topics': [[P(`${T}/slate/refresh`), P(`${T}/subjects/${ID}/pick`), P(`${T}/angle-gate/requests/${ID}/goal`),
      P(`${T}/angle-gate/requests/${ID}/choose`), P(`${T}/content-writing/requests/${ID}/write`)], [P(`${T}/tours/pool/${ID}/rewrite`), ...pub]],
    'reh-04-blog': [[P(`${T}/content-writing/requests/${ID}/write`)], [P(`${T}/slate/refresh`), P(`${T}/angle-gate/requests/${ID}/choose`), ...pub]],
    'reh-04-linkedin': [[P(`${T}/subjects/${ID}/pick`), P(`${T}/content-writing/requests/${ID}/write`)], [P(`${T}/slate/refresh`), ...pub]],
    'reh-04-facebook': [[P(`${T}/subjects/${ID}/pick`), P(`${T}/angle-gate/requests/${ID}/choose`)], [P(`${T}/tours/pool/${ID}/rewrite`), ...pub]],
    'reh-04-edit': [[['PATCH', `${T}/content-writing/pieces/${ID}`]], [P(`${T}/content-writing/pieces/${ID}`),
      ['DELETE', `${T}/content-writing/pieces/${ID}`], ['PUT', `${T}/content-writing/pieces/${ID}`],
      ['PATCH', `${T}/content-writing/pieces/${ID}/export`], P(`${T}/content-writing/requests/${ID}/write`), ...pub]],
    'reh-04b-wordpress': [[P(`${T}/integrations/wordpress`), P(`${T}/integrations/wordpress/test`), ['DELETE', `${T}/integrations/wordpress`], ...pub],
      [P(`${T}/integrations/facebook`), ['DELETE', `${T}/integrations/facebook`], P(`${T}/publish-log/${ID}`),
        ['DELETE', `${T}/publish-log/${ID}/publish`], ['PATCH', `${T}/content-writing/pieces/${ID}`], P(`${T}/content-writing/requests/${ID}/write`)]],
    'reh-04b-facebook': [[P(`${T}/integrations/facebook`), P(`${T}/integrations/facebook/test`), ['DELETE', `${T}/integrations/facebook`], ...pub],
      [P(`${T}/integrations/wordpress`), ['DELETE', `${T}/integrations/wordpress`], P(`${T}/content-writing/requests/${ID}/write`)]],
    'reh-04b-takedown': [[['DELETE', `${T}/publish-log/${ID}`]], [P(`${T}/publish-log/${ID}`), P(`${T}/publish-log/${ID}/publish`),
      ['DELETE', `${T}/integrations/wordpress`]]],
  };
  for (const [f, [ok, no]] of Object.entries(cases)) {
    const sc = load(f);
    for (const [m, u] of ok) assert.ok(allowed(sc, m, u), `${sc.id}: ${m} ${u} should be allowed`);
    for (const [m, u] of no) assert.ok(!allowed(sc, m, u), `${sc.id}: ${m} ${u} should be refused`);
    for (const src of sc.allowWrites) {
      assert.match(src, /^(POST|PATCH|DELETE) [^^]/, `${sc.id}: ${src} names its method and matches the full URL`);
      assert.ok(!src.includes('\\\\/'), `${sc.id}: ${src} has a doubled escape`);
    }
    assert.equal(sc.identity, 'studio-rehearsal');
    assert.equal(sc.pilotGuard, undefined, `${sc.id} takes the rehearsal pin`);
  }
  assert.deepEqual(Object.keys(cases).sort(), [...FILES].sort());
});

test('REH-04-edit, the publish pair and the takedown cap their PATCH / DELETE writes with limitWrites', () => {
  const src = (f) => fs.readFileSync(path.join(SCEN, 'content-studio', `${f}.cjs`), 'utf8');
  assert.match(src('reh-04-edit'), /limitWrites\(page, R\.capRules\(\['piece'\]\)\)/);
  assert.match(src('reh-04-edit'), /counts\.piece !== 1/);
  assert.match(src('_publish'), /name: 'unpublish', path: R\.PATHS\.unpublish, method: R\.methodOf\('unpublish'\), max: 1/);
  assert.match(src('_publish'), /n\.unpublish !== 1/);
  assert.match(src('reh-04b-takedown'), /method: R\.methodOf\('unpublish'\), max: 0/);
  assert.match(src('reh-04b-takedown'), /cap\[0\]\.max = Math\.min\(live\.length, MAX_POSTS\)/);
  const R = require(path.join(SCEN, 'content-studio', '_rehearsal.cjs'));
  assert.equal(R.methodOf('piece'), 'PATCH');
  assert.equal(R.methodOf('unpublish'), 'DELETE');
  assert.equal(R.methodOf('publish'), 'POST');
  assert.deepEqual(R.capRules(['piece']).map((r) => [r.name, r.method, r.max]), [['piece', 'PATCH', 1]]);
});

test('REH-04-edit writes the planner line as a Markdown link (CIS does not autolink a bare URL)', () => {
  const src = fs.readFileSync(path.join(SCEN, 'content-studio', 'reh-04-edit.cjs'), 'utf8');
  assert.match(src, /const plannerLine = \(url\) => `\[\$\{TEXT\}\]\(\$\{url\}\)`/);
  // The old bare-URL line of an earlier take is replaced too.
  assert.match(src, /l\.startsWith\(`\$\{TEXT\}:`\)/);
});

test('REH-03-adopt: the rewrite toast matches one tour and several; the catalog page is read, not awaited', () => {
  const src = fs.readFileSync(path.join(SCEN, 'content-studio', 'reh-03-adopt.cjs'), 'utf8');
  const re = /rewrites? started\. Follow (it|them) here or in My Tours\./i;
  assert.ok(re.test('Rewrite started. Follow it here or in My Tours.'));
  assert.ok(re.test('3 rewrites started. Follow them here or in My Tours.'));
  assert.ok(src.includes(re.source), 'the scenario uses the case-insensitive toast pattern');
  assert.doesNotMatch(src, /waitForResponse\(\(r\) => new URL\(r\.url\(\)\)\.pathname === `\$\{R\.T\}\/tours\/pool`/);
});

test('REH captions never read the fixture name "tour X" aloud', () => {
  for (const f of FILES) {
    for (const s of load(f).steps) {
      for (const t of [s.caption.en, s.caption.vi]) assert.doesNotMatch(t, /\btour X\b|Trình viết/i, `${f}: ${t}`);
    }
  }
});

test('REH scenarios: both titles, en + vi captions, the last step ends the scenario, no issue ids, a writing step', () => {
  for (const f of FILES) {
    const sc = load(f);
    assert.ok(sc.title && sc.title_vi, `${sc.id} has both titles`);
    assert.ok(sc.steps.some((s) => s.writes), `${sc.id} marks its writing steps`);
    for (const [i, s] of sc.steps.entries()) {
      assert.ok(s.caption.en && s.caption.vi, `${sc.id} step ${i + 1}`);
      for (const t of [s.caption.en, s.caption.vi, sc.title, sc.title_vi]) assert.ok(!/\bAA-?\d{3,4}\b/.test(t), `${sc.id} names an issue id`);
    }
    const last = sc.steps[sc.steps.length - 1].caption;
    assert.match(last.en, /This is the end of the scenario\.$/);
    assert.match(last.vi, /Kết thúc kịch bản\.$/);
  }
});

test('REH publish scenarios blur the channel secrets; the Facebook one also the Page id card', () => {
  const wp = load('reh-04b-wordpress');
  const fb = load('reh-04b-facebook');
  assert.ok(wp.mask.includes('input[type="password"]') && wp.mask.some((m) => /username/.test(m)));
  assert.ok(fb.mask.includes('input[type="password"]') && fb.mask.includes('input[inputmode="numeric"]'));
  assert.ok(fb.mask.includes('[data-testid="publish-fb-summary"]'));
});

test('catalogue + write set: every REH scenario is a live writing row of studio-rehearsal; paid flags agree', () => {
  const c = cat.loadValid();
  const by = cat.byId(c);
  const ws = path.join(SCEN, 'write-set.cjs');
  const rels = require(ws);
  const paid = new Set(['REH-03-adopt', 'REH-04-topics', 'REH-04-blog', 'REH-04-linkedin', 'REH-04-facebook']);
  for (const f of FILES) {
    const sc = load(f);
    assert.ok(rels.includes(`content-studio/${f}.cjs`), `${sc.id} is in the write set`);
    const d = core.describeWrite(sc, `content-studio/${f}.cjs`);
    const row = by.get(sc.id);
    assert.ok(row && row.writes && row.status === 'live' && row.identity === 'studio-rehearsal', sc.id);
    assert.equal(row.paid, paid.has(sc.id), `${sc.id} paid in the catalogue`);
    assert.equal(d.paid, paid.has(sc.id), `${sc.id} paid in the scenario`);
  }
  // The upper-cased --only / --record argument finds the slug id.
  const entries = rels.map((rel) => core.describeWrite(require(path.resolve(path.dirname(ws), rel)), rel));
  assert.deepEqual(core.select(entries, { only: ['REH-03-BRAND'], includeWritable: true }).map((e) => e.id), ['REH-03-brand']);
  assert.throws(() => core.select(entries, { only: ['REH-04-TOPICS'], includeWritable: true }), /calls a paid model/);
  assert.deepEqual(core.select(entries, { only: ['REH-04-TOPICS'], allowPaid: true, includeWritable: true }).map((e) => e.id), ['REH-04-topics']);
});

test('catalogue id rule: REH-<nn>[letter]-<slug> accepted; other spellings refused', () => {
  const row = (id) => ({ version: 1, scenarios: [{ id, app: 'content-studio', module: 'm', story: 's', roles: ['agency-owner'],
    kinds: ['uat'], covers: [], screens: [], status: 'live', round: null, identity: 'studio-rehearsal', writes: true, paid: false }] });
  for (const id of ['REH-03-brand', 'REH-04b-wordpress', 'REH-12b-end-pilot', 'REH-04-x2']) assert.deepEqual(cat.validate(row(id)), [], id);
  for (const id of ['REH-3-brand', 'REH-03-Brand', 'REH-03-', 'REH-03--x', 'REH-03_brand']) assert.match(cat.validate(row(id)).join(), /id does not follow/, id);
});

test('publish scenarios blur the Facebook Page summary whatever channel they record (S279)', () => {
  const P = require('../scenarios/content-studio/_publish.cjs');
  for (const ch of ['wordpress', 'facebook']) assert.ok(P.CH[ch].mask.includes('[data-testid="publish-fb-summary"]'), ch);
});

test('publish scenarios cap the disconnect at 0 unless the stored connection is stale (S279)', () => {
  const src = require('fs').readFileSync(require('path').join(__dirname, '..', 'scenarios', 'content-studio', '_publish.cjs'), 'utf8');
  assert.match(src, /state\.disconnectRule = \{ name: 'disconnect', path: R\.PATHS\[c\.disconnect\], method: 'DELETE', max: 0 \}/);
  assert.match(src, /last_verify_error\) \{[\s\S]{0,400}state\.disconnectRule\.max = 1;/);
  assert.match(src, /n\.disconnect !== \(state\.reconnected \? 1 : 0\)/);
  assert.ok(!src.includes('portal/account/integrations'), 'never opens the integrations page (Page id in clear there)');
});
