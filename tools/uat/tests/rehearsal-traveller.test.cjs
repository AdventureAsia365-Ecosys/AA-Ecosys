// Unit tests of the pilot rehearsal's traveller-side scenarios (REH-05, REH-05.m, REH-06, REH-08a) and the harness
// pieces they lean on: the per-method write cap (lib/uat-page.cjs limitWrites), the paid-path safety net
// (lib/dryrun-core.cjs blockSources), the form-key mask (redact) and the brand-colour check (_rehearsal.cjs
// assertBrand). No browser, no network.
//   node --test tools/uat/tests/rehearsal-traveller.test.cjs
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');

const core = require('../lib/dryrun-core.cjs');
const { limitWrites, WRITE_METHODS } = require('../lib/uat-page.cjs');
const R = require('../scenarios/tripplanner/_rehearsal.cjs');

const SCEN = path.join(__dirname, '..', 'scenarios');
const ORIGIN = 'https://planner.example.invalid';

/** A fake page whose route() keeps the handlers; fire() sends one request through them. */
function fakePage() {
  const routes = [];
  const seen = [];
  const page = { route: async (pred, handler) => routes.push({ pred, handler }) };
  const fire = async (p, method = 'POST', body = null) => {
    const r = routes.find((x) => x.pred(new URL(`${ORIGIN}${p}`)));
    if (!r) { seen.push('none'); return; }
    await r.handler({
      request: () => ({ method: () => method, postData: () => body }),
      fallback: async () => seen.push(`go ${method} ${p}`),
      abort: async () => seen.push(`abort ${method} ${p}`),
    });
  };
  return { page, seen, fire };
}

// ── limitWrites: every write method, a capped read, a refused shape ─────────────────────────────────────────────────

test('limitWrites: method \'*\' counts PUT, PATCH and DELETE against the cap like POST', async () => {
  assert.deepEqual(WRITE_METHODS, ['POST', 'PUT', 'PATCH', 'DELETE']);
  const { page, seen, fire } = fakePage();
  const counts = await limitWrites(page, [{ name: 'piece', path: /^\/x\/piece$/, method: '*', max: 2 }]);
  await fire('/x/piece', 'GET');
  await fire('/x/piece', 'PATCH');
  await fire('/x/piece', 'DELETE');
  await fire('/x/piece', 'PUT');
  await fire('/x/piece', 'POST');
  assert.deepEqual(seen, ['go GET /x/piece', 'go PATCH /x/piece', 'go DELETE /x/piece', 'abort PUT /x/piece', 'abort POST /x/piece']);
  assert.deepEqual(counts, { piece: 4 });
});

test('limitWrites: a rule with method GET caps a paid read and leaves writes to the guard', async () => {
  const { page, seen, fire } = fakePage();
  const counts = await limitWrites(page, [{ name: 'search', path: /^\/api\/browse\/search$/, method: 'GET', read: true, max: 1 }]);
  await fire('/api/browse/search', 'GET');
  await fire('/api/browse/search', 'GET');
  await fire('/api/browse/search', 'POST');
  assert.deepEqual(seen, ['go GET /api/browse/search', 'abort GET /api/browse/search', 'go POST /api/browse/search']);
  assert.deepEqual(counts, { search: 2 });
});

test('limitWrites accept + tripOps: only POST of the named ops reaches the guard; the rest is refused and counted', async () => {
  const { page, seen, fire } = fakePage();
  const counts = await limitWrites(page, [{ name: 'trip', path: R.PATHS.trip, max: 1, method: '*', accept: R.tripOps('apply_route', 'reorder') }]);
  await fire('/api/trip', 'POST', JSON.stringify({ op: 'apply_route' }));
  await fire('/api/trip', 'POST', JSON.stringify({ op: 'narrate' })); // the older paid spelling
  await fire('/api/trip', 'DELETE');
  await fire('/api/trip', 'POST', 'not json');
  await fire('/api/trip', 'POST', JSON.stringify({ op: 'reorder' })); // over the cap of 1
  assert.deepEqual(seen, ['go POST /api/trip', 'abort POST /api/trip', 'abort DELETE /api/trip', 'abort POST /api/trip', 'abort POST /api/trip']);
  assert.deepEqual(counts, { trip: 2, trip_refused: 3 });
});

// ── the paid-path safety net ────────────────────────────────────────────────────────────────────────────────────────

test('blockSources: a paid take opens only the PAID_URLS entries its scenario names, never in a preview', () => {
  const runner = { UAT_BLOCK_URLS: JSON.stringify(core.PAID_URLS) };
  const sc = { blockUrls: ['/own(?:[?#]|$)'], allowPaidUrls: [R.SEARCH_PAID] };
  assert.deepEqual(core.blockSources(sc, runner), ['/own(?:[?#]|$)', ...core.PAID_URLS]);
  const paid = core.blockSources(sc, { ...runner, UAT_ALLOW_PAID: '1' });
  assert.ok(!paid.includes(R.SEARCH_PAID));
  for (const u of core.PAID_URLS.filter((x) => x !== R.SEARCH_PAID)) assert.ok(paid.includes(u), `${u} stays blocked`);
  assert.deepEqual(core.blockSources(sc, { ...runner, UAT_ALLOW_PAID: '1', UAT_PREVIEW: '1' }), ['/own(?:[?#]|$)', ...core.PAID_URLS]);
  assert.deepEqual(core.blockSources({}, {}), []);
});

test('REH scenarios: REH-05 opens only the protected search path; the others block every paid path', () => {
  const reh05 = require(path.join(SCEN, 'tripplanner', 'reh-05.cjs'));
  assert.deepEqual(reh05.allowPaidUrls, [R.SEARCH_PAID]);
  assert.ok(core.PAID_URLS.includes(R.SEARCH_PAID));
  assert.ok(!reh05.blockUrls.includes(R.SEARCH_PAID));
  assert.ok(reh05.blockUrls.some((u) => /resource=search/.test(u)), 'the older search spelling stays blocked');
  assert.ok(reh05.blockUrls.some((u) => /narrate/.test(u)), 'narration stays blocked');
  for (const f of ['reh-05-phone.cjs', 'reh-06.cjs']) {
    const sc = require(path.join(SCEN, 'tripplanner', f));
    for (const u of core.PAID_URLS) assert.ok(sc.blockUrls.includes(u), `${f} blocks ${u}`);
    assert.equal(sc.allowPaidUrls, undefined);
  }
  for (const f of ['tripplanner/reh-05.cjs', 'tripplanner/reh-05-phone.cjs', 'tripplanner/reh-06.cjs', 'crm-web/reh-08a.cjs']) {
    assert.doesNotThrow(() => core.describeWrite(require(path.join(SCEN, f)), f));
  }
});

test('describeWrite: allowPaidUrls must be PAID_URLS entries on a paid scenario', () => {
  const base = { id: 'W-99', app: 'tripplanner', identity: 'traveller', readOnly: true, allowWrites: ['^x$'],
    steps: [{ writes: true, caption: { en: 'a', vi: 'a' }, run: async () => {} }] };
  assert.throws(() => core.describeWrite({ ...base, paid: false, allowPaidUrls: [R.SEARCH_PAID] }, 'x.cjs'), /not paid/);
  assert.throws(() => core.describeWrite({ ...base, paid: true, allowPaidUrls: ['/anything'] }, 'x.cjs'), /not a PAID_URLS entry/);
  assert.doesNotThrow(() => core.describeWrite({ ...base, paid: true, allowPaidUrls: [R.SEARCH_PAID] }, 'x.cjs'));
});

// ── redact: the Book now form key ───────────────────────────────────────────────────────────────────────────────────

test('redact: a short form key in f= is masked; the decoy p= and the tour uuid stay', () => {
  const uuid = '0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d';
  const key = 'abcDEF0123456789_-xyzQ'; // 22 characters, under the 30-character rule
  assert.equal(core.redact(`https://go.example.invalid/trip/${uuid}?f=${key}&p=rehearsal-decoy-tour-key`),
    `https://go.example.invalid/trip/${uuid}?f=<redacted>&p=rehearsal-decoy-tour-key`);
  assert.equal(core.redact(`/c/p?token=short&x=1`), '/c/p?token=<redacted>&x=1');
});

// ── the invented traveller, the registry hint ───────────────────────────────────────────────────────────────────────

test('traveller: only an address on .invalid; anything else stops the take', () => {
  assert.equal(R.traveller({}).email, 'rehearsal.traveller@example.invalid');
  assert.equal(R.traveller({ UAT_REH_TRAVELLER_EMAIL: ' x@rehearsal.invalid ' }).email, 'x@rehearsal.invalid');
  assert.throws(() => R.traveller({ UAT_REH_TRAVELLER_EMAIL: 'someone@example.com' }), /\.invalid/);
  assert.throws(() => R.traveller({ UAT_REH_TRAVELLER_EMAIL: 'a@invalid.example.com' }), /\.invalid/);
});

test('registryHint: a 429 names the registry setting, never a value; other statuses say nothing', () => {
  assert.match(R.registryHint('send', 429, 'rate_limited'), /tripplanner\.rate\.send_per_hour/);
  assert.match(R.registryHint('send', 429, 'lead_cap_reached'), /tripplanner\.leads\.tenant_daily_cap/);
  assert.match(R.registryHint('chat', 429, 'rate_limited'), /tripplanner\.rate\.chat_per_hour/);
  assert.match(R.registryHint('search', 429), /tripplanner\.rate\.search_per_minute/);
  assert.equal(R.registryHint('send', 403, 'bot_check_failed'), '');
});

// ── assertBrand: the agency colour is read from body, as brandThemeCss sets it ──────────────────────────────────────

function brandPage({ blocks = 1, css = '', body = '', root = '#db9628' }) {
  return {
    locator: () => ({ count: async () => blocks, textContent: async () => css }),
    evaluate: async () => ({ body, root }),
  };
}
const CSS = 'html:not([data-theme]) body,html[data-theme=light] body{--aa-accent:#1f6f8b;--aa-on-accent:#ffffff;}';

test('assertBrand: passes when body carries the declared accent while :root keeps the kit value', async () => {
  assert.equal(await R.assertBrand(brandPage({ css: CSS, body: ' #1F6F8B' }), {}), '#1f6f8b');
});

test('assertBrand: fails with no block, no accent, the kit accent on body, or an accent the block does not declare', async () => {
  await assert.rejects(R.assertBrand(brandPage({ blocks: 0 }), {}), /no agency brand block/);
  await assert.rejects(R.assertBrand(brandPage({ css: 'html body{--aa-accent-deep:#123456;}', body: '#db9628' }), {}), /sets no accent/);
  await assert.rejects(R.assertBrand(brandPage({ css: CSS, body: '#db9628' }), {}), /kit accent/);
  await assert.rejects(R.assertBrand(brandPage({ css: CSS, body: '#abcdef' }), {}), /not the agency's/);
});

// ── REH-06: the repeated send is recorded once (S279 fix) ───────────────────────────────────────────────────────────

test('REH-06 replay: headers keep content type and x-tp-*, add the marker; answers parse or stay empty', () => {
  const h = R.replayHeaders({ 'content-type': 'application/json', 'x-tp-tenant': 'pilot-rehearsal-01', cookie: 'no', 'user-agent': 'no' });
  assert.deepEqual(h, { 'content-type': 'application/json', 'x-tp-tenant': 'pilot-rehearsal-01', [R.REPLAY_HEADER]: '1' });
  assert.deepEqual(R.sendAnswer(200, '{"already_sent":true,"handoff_id":"h1"}'), { status: 200, already_sent: true, handoff_id: 'h1', error: undefined });
  assert.deepEqual(R.sendAnswer(202, '<html>challenge</html>'), { status: 202, already_sent: undefined, handoff_id: null, error: undefined });
});

test('REH-06 replay: the listener skips the marked repeat and replaySend records its own answer', () => {
  const src = require('fs').readFileSync(path.join(SCEN, 'tripplanner', 'reh-06.cjs'), 'utf8');
  assert.match(src, /headers\(\)\[R\.REPLAY_HEADER\]\) return;/);
  assert.match(src, /answers\.push\(R\.sendAnswer\(res\.status, res\.text\)\)/);
  assert.ok(!/waitForResponse\([^)]*\/api\/trip\/send[^)]*\)[\s\S]{0,200}fetch\('\/api\/trip\/send'/.test(src), 'no listener-dependent wait for the repeat');
});
