// Unit tests of the UAT write scenarios W-01..W-04 (AA-855 round 1) and their helpers: the studio-audit tenant choice,
// the pilot-guard pin, the write limiter, the ZIP reader and AI mark, the W-02 -> W-03 -> W-04 hand-over file, the
// allow-lists and the catalogue / write-set agreement. No browser, no network:  node --test tools/uat/tests/*.test.cjs
// Ids, names and texts are invented.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const zlib = require('zlib');

const audit = require('../lib/studio-audit.cjs');
const g = require('../lib/pilot-guard.cjs');
const chain = require('../lib/write-chain.cjs');
const { limitWrites, zipEntry, AI_MARK } = require('../lib/uat-page.cjs');
const cat = require('../lib/catalogue.cjs');
const core = require('../lib/dryrun-core.cjs');

const SCEN = path.join(__dirname, '..', 'scenarios');
const load = (rel) => require(path.join(SCEN, 'content-studio', rel));
const ORIGIN = 'https://agency.example.invalid';
const ID = '0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d'; // invented
const ID2 = '1b2c3d4e-5f60-4b7c-8d9e-0f1a2b3c4d5e'; // invented

// ── studio-audit tenant ─────────────────────────────────────────────────────────────────────────────────────────────

test('auditTenant: default audit-atlas-hearth; only the four audit slugs; anything else throws', () => {
  assert.deepEqual(audit.auditTenant({}), { slug: 'audit-atlas-hearth', name: 'Atlas & Hearth (Audit)' });
  assert.equal(audit.auditTenant({ UAT_STUDIO_TENANT: ' audit-trail-pulse ' }).slug, 'audit-trail-pulse');
  for (const bad of ['atlas-hearth', 'sen-vang', 'audit-atlas-hearth;x', 'AUDIT-TRAIL-PULSE', '__proto__']) {
    assert.throws(() => audit.auditTenant({ UAT_STUDIO_TENANT: bad }), /UAT_STUDIO_TENANT must be one of/);
  }
  assert.equal(audit.secretId({}), audit.SECRET);
  assert.equal(audit.secretId({ UAT_STUDIO_AUDIT_SECRET: 'x/y' }), 'x/y');
});

test('pilot guard: the audit tenants are synthetic by their invented names; studio-audit is pinned to the run tenant', () => {
  const allow = g.buildAllowlist(null);
  for (const [slug, name] of Object.entries(audit.AUDIT_TENANTS)) {
    const v = g.evaluate({ tenant_id: ID, tenant_name: name }, { scope: 'content', allow });
    assert.equal(v.ok, true, slug);
    assert.equal(v.slug, slug);
  }
  const prev = process.env.UAT_STUDIO_TENANT;
  try {
    process.env.UAT_STUDIO_TENANT = 'audit-terra-family';
    const s = g.scopesFor({ id: 'W-91', identity: 'studio-audit' }, 'state.json');
    assert.deepEqual(s, { scopes: ['content'], only: ['audit-terra-family'] });
    // Another audit tenant, an E2E tenant, a real-looking name: all refused for this run.
    const on = (name) => g.evaluate({ tenant_id: ID, tenant_name: name }, { scope: 'content', allow, only: s.only });
    assert.equal(on('Terra Family Expeditions (Audit)').ok, true);
    assert.match(on('Atlas & Hearth (Audit)').reason, /runs only on audit-terra-family/);
    assert.match(on('Terra Family Expeditions').reason, /runs only on audit-terra-family/);
    assert.match(on('Lotus Lantern Journeys').reason, /not in the synthetic allow-list/);
    // A scenario cannot widen the pin with its own pilotGuard.
    assert.throws(() => g.scopesFor({ id: 'W-91', identity: 'studio-audit', pilotGuard: { scopes: ['content'] } }, 'f'), /takes the run's audit tenant/);
    process.env.UAT_STUDIO_TENANT = 'someone-else';
    assert.throws(() => g.scopesFor({ id: 'W-91', identity: 'studio-audit' }, 'f'), /UAT_STUDIO_TENANT must be one of/);
  } finally {
    if (prev === undefined) delete process.env.UAT_STUDIO_TENANT; else process.env.UAT_STUDIO_TENANT = prev;
  }
  assert.ok(core.IDENTITIES.includes('studio-audit') && core.WRITABLE_IDENTITIES.includes('studio-audit'));
  assert.ok(g.syntheticRowPatterns().includes('audit-wildkind-travel'));
});

test('signin: studio-audit keeps one state file per audit tenant, chooses the studio by name, reads the secret only', () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'lib', 'signin.cjs'), 'utf8');
  assert.match(src, /\.state-studio-audit-\$\{studioAudit\.auditTenant\(\)\.slug\}\.json/);
  assert.match(src, /getByText\(tenantName, \{ exact: true \}\)/);
  assert.match(src, /ensureStudioTenant\(page, tenantName\)/);
  assert.ok(!/console\.log\([^)]*(password|totp|creds)/i.test(src), 'no secret is printed');
});

// ── write limiter ───────────────────────────────────────────────────────────────────────────────────────────────────

test('limitWrites: at most `max` POSTs of each rule go on to the guard, later ones are aborted and still counted', async () => {
  const routes = [];
  const page = { route: async (pred, handler) => routes.push({ pred, handler }) };
  const counts = await limitWrites(page, [{ name: 'pick', path: /^\/x\/pick$/, max: 1 }, { name: 'write', path: /^\/x\/write$/, max: 2 }]);
  const seen = [];
  const fire = async (p, method = 'POST') => {
    const r = routes.find((x) => x.pred(new URL(`${ORIGIN}${p}`)));
    if (!r) { seen.push('none'); return; }
    await r.handler({ request: () => ({ method: () => method }), fallback: async () => seen.push(`go ${p}`),
      abort: async (code) => seen.push(`abort ${p} ${code}`) });
  };
  await fire('/x/pick', 'GET');
  await fire('/x/pick');
  await fire('/x/pick');
  await fire('/x/write');
  await fire('/x/write');
  await fire('/x/write');
  await fire('/x/other');
  assert.deepEqual(seen, ['go /x/pick', 'go /x/pick', 'abort /x/pick blockedbyclient', 'go /x/write', 'go /x/write',
    'abort /x/write blockedbyclient', 'none']);
  assert.deepEqual(counts, { pick: 2, write: 3 });
});

// ── ZIP reader + AI mark ────────────────────────────────────────────────────────────────────────────────────────────

/** A minimal ZIP with the given entries (method 8 = deflated, 0 = stored), built the way a DOCX writer lays it out. */
function makeZip(entries) {
  const locals = [];
  const central = [];
  let offset = 0;
  for (const { name, text, method = 8 } of entries) {
    const raw = Buffer.from(text, 'utf8');
    const data = method === 8 ? zlib.deflateRawSync(raw) : raw;
    const n = Buffer.from(name, 'utf8');
    const lh = Buffer.alloc(30);
    lh.writeUInt32LE(0x04034b50, 0); lh.writeUInt16LE(method, 8); lh.writeUInt32LE(data.length, 18);
    lh.writeUInt32LE(raw.length, 22); lh.writeUInt16LE(n.length, 26);
    const ch = Buffer.alloc(46);
    ch.writeUInt32LE(0x02014b50, 0); ch.writeUInt16LE(method, 10); ch.writeUInt32LE(data.length, 20);
    ch.writeUInt32LE(raw.length, 24); ch.writeUInt16LE(n.length, 28); ch.writeUInt32LE(offset, 42);
    locals.push(lh, n, data);
    central.push(ch, n);
    offset += 30 + n.length + data.length;
  }
  const cd = Buffer.concat(central);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0); end.writeUInt16LE(entries.length, 8); end.writeUInt16LE(entries.length, 10);
  end.writeUInt32LE(cd.length, 12); end.writeUInt32LE(offset, 16);
  return Buffer.concat([...locals, cd, end]);
}

test('zipEntry: reads a deflated and a stored entry, null for a missing one, throws on a non-ZIP', () => {
  const core1 = '<cp:coreProperties><cp:keywords>ai-generated</cp:keywords></cp:coreProperties>';
  const zip = makeZip([{ name: '[Content_Types].xml', text: '<Types/>', method: 0 }, { name: 'docProps/core.xml', text: core1 }]);
  assert.equal(zipEntry(zip, 'docProps/core.xml').toString('utf8'), core1);
  assert.equal(zipEntry(zip, '[Content_Types].xml').toString('utf8'), '<Types/>');
  assert.equal(zipEntry(zip, 'word/document.xml'), null);
  assert.throws(() => zipEntry(Buffer.from('not a zip at all, just some text bytes'), 'x'), /not a ZIP archive/);
  assert.ok(AI_MARK.docxKeywords.test(core1));
  assert.ok(!AI_MARK.docxKeywords.test('<cp:keywords>travel</cp:keywords>'));
});

test('AI_MARK: the HTML export marks of CIS (data-ai-* on the article, the ai-generated meta), nothing looser', () => {
  const doc = '<head><meta name="ai-generated" content="true"><meta name="ai-generator" content="x"></head>'
    + '<body><article data-ai-generated="true" data-ai-generator="x"><h1>Lantern Bay</h1></article></body>';
  assert.ok(AI_MARK.article.test(doc));
  assert.ok(AI_MARK.meta.test(doc));
  assert.ok(!AI_MARK.article.test('<article class="post"><p>data-ai-generated="true"</p></article>'));
  assert.ok(!AI_MARK.meta.test('<meta name="ai-generated" content="false">'));
});

// ── hand-over file ──────────────────────────────────────────────────────────────────────────────────────────────────

test('write-chain: merge per tenant, uuids only, stale or future entries ignored, file mode 600', () => {
  const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'uat-chain-')), 'chain.json');
  const now = new Date('2026-11-06T02:00:00Z');
  chain.write('audit-trail-pulse', { request_id: ID, piece_id: null, channel: 'blog' }, { now, file });
  chain.write('audit-trail-pulse', { piece_id: ID2 }, { now, file });
  chain.write('audit-terra-family', { request_id: ID2 }, { now, file });
  const e = chain.read('audit-trail-pulse', { now: now.getTime() + 60_000, file });
  assert.deepEqual({ ...e }, { request_id: ID, piece_id: ID2, channel: 'blog', at: now.toISOString() });
  assert.equal(chain.read('audit-trail-pulse', { now: now.getTime() + chain.MAX_AGE_MS + 1, file }), null);
  assert.equal(chain.read('audit-trail-pulse', { now: now.getTime() - 3_600_000, file }), null);
  assert.equal(chain.read('audit-wildkind-travel', { now: now.getTime(), file }), null);
  assert.equal(fs.statSync(file).mode & 0o777, 0o600);
  assert.throws(() => chain.write('audit-trail-pulse', { request_id: 'drop table' }, { file }), /not an id/);
  assert.throws(() => chain.write('audit-trail-pulse', { channel: '../x' }, { file }), /not a channel key/);
  fs.writeFileSync(file, 'not json');
  assert.equal(chain.read('audit-trail-pulse', { file }), null);
});

test('write-chain newest: by channel ("!blog" = any other), ready only, created within a window, newest first', () => {
  const now = Date.parse('2026-11-06T02:00:00Z');
  const row = (piece_id, channel, ready_state, created_at) => ({ piece_id, request_id: ID, channel, ready_state, created_at });
  const items = [
    row(ID, 'blog', 'ready', '2026-11-05T10:00:00Z'),
    row(ID2, 'blog', 'in_progress', '2026-11-06T01:50:00Z'),
    row('2c3d4e5f-6071-4c8d-9eaf-1a2b3c4d5e6f', 'linkedin', 'ready', '2026-11-06T01:00:00Z'),
    row('not-an-id', 'blog', 'ready', '2026-11-06T01:59:00Z'),
  ];
  assert.equal(chain.newest(items, { channel: 'blog', now }).piece_id, ID2);
  assert.equal(chain.newest(items, { channel: 'blog', ready: true, now }).piece_id, ID);
  assert.equal(chain.newest(items, { channel: 'blog', sinceMs: 3_600_000, now }).piece_id, ID2);
  assert.equal(chain.newest(items, { channel: 'blog', ready: true, sinceMs: 3_600_000, now }), null);
  assert.equal(chain.newest(items, { channel: '!blog', ready: true, now }).channel, 'linkedin');
  assert.equal(chain.newest(null, {}), null);
});

// ── the scenarios ───────────────────────────────────────────────────────────────────────────────────────────────────

const allowed = (sc, url) => (sc.allowWrites || []).map((x) => new RegExp(x)).some((r) => r.test(url));
const T = `${ORIGIN}/api/tenant/v1`;

test('W-01..W-03 allow exactly their writes; W-04 writes nothing', () => {
  const cases = {
    'w-01.cjs': [[`${T}/tours/pool/${ID}/rewrite`], [`${T}/tours/versions/${ID}/retry`, `${T}/tours/versions/${ID}`, `${T}/subjects/${ID}/pick`]],
    'w-02.cjs': [[`${T}/slate/refresh`, `${T}/subjects/${ID}/pick`, `${T}/angle-gate/requests/${ID}/goal`,
      `${T}/angle-gate/requests/${ID}/choose`, `${T}/content-writing/requests/${ID}/write`],
    [`${T}/subjects/${ID}/cut`, `${T}/angle-gate/requests/${ID}/reopen`, `${T}/content-writing/pieces/${ID}`,
      `${T}/tours/pool/${ID}/rewrite`, `${T}/publish-log/${ID}/publish`, `${ORIGIN}/api/tenant/admin/brand-identity`]],
    'w-03.cjs': [[`${T}/content-writing/requests/${ID}/write`], [`${T}/angle-gate/requests/${ID}/choose`,
      `${T}/content-writing/requests/${ID}/write/extra`, `${T}/publish-log/${ID}/publish`]],
  };
  for (const [f, [ok, no]] of Object.entries(cases)) {
    const sc = load(f);
    for (const u of ok) assert.ok(allowed(sc, u), `${sc.id}: ${u} should be allowed`);
    for (const u of no) assert.ok(!allowed(sc, u), `${sc.id}: ${u} should be refused`);
    for (const src of sc.allowWrites) assert.ok(!src.startsWith('^') && !src.includes('\\\\/'), `${sc.id}: ${src} matches the full URL`);
    assert.equal(sc.paid, true, `${sc.id} is paid`);
    assert.equal(sc.identity, 'studio-audit');
    assert.equal(sc.pilotGuard, undefined, `${sc.id} takes the run's audit tenant`);
  }
  const w4 = load('w-04.cjs');
  assert.equal(w4.readOnly, true);
  assert.equal(w4.allowWrites, undefined);
  assert.equal(w4.prepare, undefined);
});

test('W-01..W-04: English and Vietnamese captions on every step, the last one ends the scenario, no issue ids', () => {
  for (const f of ['w-01.cjs', 'w-02.cjs', 'w-03.cjs', 'w-04.cjs']) {
    const sc = load(f);
    assert.ok(sc.title && sc.title_vi, `${sc.id} has both titles`);
    for (const [i, s] of sc.steps.entries()) {
      assert.ok(s.caption.en && s.caption.vi, `${sc.id} step ${i + 1}`);
      for (const t of [s.caption.en, s.caption.vi]) assert.ok(!/\bAA-?\d{3,4}\b/.test(t), `${sc.id} step ${i + 1} names an issue id`);
    }
    const last = sc.steps[sc.steps.length - 1].caption;
    assert.match(last.en, /This is the end of the scenario\.$/);
    assert.match(last.vi, /Kết thúc kịch bản\.$/);
  }
});

test('W-02 / W-03 limit every paid call: one goal, one choice, the write at most twice (a 422 asks for a call to action)', () => {
  const src = fs.readFileSync(path.join(SCEN, 'content-studio', 'w-02.cjs'), 'utf8');
  assert.match(src, /max: name === 'write' \? 2 : 1/);
  assert.match(fs.readFileSync(path.join(SCEN, 'content-studio', 'w-03.cjs'), 'utf8'), /name: 'write', path: PATHS\.write, max: 2/);
  assert.match(fs.readFileSync(path.join(SCEN, 'content-studio', 'w-01.cjs'), 'utf8'), /name: 'rewrite', path: PATHS\.rewrite, max: 1/);
});

test('_write freeTour: the first catalog tour not in My Tours and still sold', () => {
  const { freeTour } = require(path.join(SCEN, 'content-studio', '_write.cjs'));
  const t = (id, over = {}) => ({ id, tour_id: `${id}-t`, aa_name: `Tour ${id}`, already_rewritten: false, served_notice: null, served_status: 'served', ...over });
  assert.equal(freeTour({ data: [t('a', { already_rewritten: true }), t('b', { served_notice: 'paused' }), t('c', { served_status: 'retired' }), t('d')] }).id, 'd');
  assert.equal(freeTour({ data: [t('a', { already_rewritten: true })] }), null);
  assert.equal(freeTour(null), null);
});

test('catalogue: the write set agrees with the catalogue (live, writes, same paid flag and identity)', () => {
  const c = cat.loadValid();
  const ws = path.join(SCEN, 'write-set.cjs');
  const entries = require(ws).map((rel) => core.describeWrite(require(path.resolve(path.dirname(ws), rel)), rel));
  assert.deepEqual(cat.checkWriteSet(c, entries), []);
  const by = cat.byId(c);
  for (const id of ['W-01', 'W-02', 'W-03']) assert.ok(by.get(id).paid && by.get(id).writes, `${id} paid and writing in the catalogue`);
  assert.equal(by.get('W-04').paid, false);
  assert.equal(by.get('W-04').writes, false);
  // The checker itself: a write-set entry marked free while the catalogue says paid, or writing nothing, is a problem.
  const fake = { version: 1, scenarios: [{ ...by.get('W-01') }, { ...by.get('W-04') }] };
  assert.match(cat.checkWriteSet(fake, [{ id: 'W-01', identity: 'studio-audit', paid: false }]).join(), /catalogue paid true, scenario paid false/);
  assert.match(cat.checkWriteSet(fake, [{ id: 'W-04', identity: 'studio-audit', paid: false }]).join(), /writes nothing/);
  assert.match(cat.checkWriteSet(fake, [{ id: 'W-09', identity: 'studio-audit', paid: true }]).join(), /no catalogue row/);
});

test('record.cjs preview: only the steps before the first write, allowWrites emptied, fast only', () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'record.cjs'), 'utf8');
  assert.match(src, /UAT_PREVIEW === '1'/);
  assert.match(src, /steps\.findIndex\(\(s\) => s && s\.writes\)/);
  assert.match(src, /sc\.allowWrites = \[\]/);
  assert.match(src, /a preview is a fast dry run/);
  assert.match(src, /for \(let i = 0; i < steps\.length; i\+\+\)/);
  const dry = fs.readFileSync(path.join(__dirname, '..', 'dryrun.cjs'), 'utf8');
  assert.match(dry, /delete env\.UAT_ALLOW_PAID/);
  assert.match(dry, /paid: !!\(e\.writeSet && e\.paid && opts\.allowPaid\)/);
});
