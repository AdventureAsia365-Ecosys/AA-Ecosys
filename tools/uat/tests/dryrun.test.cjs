// Unit tests of the UAT dry-run runner (AA-1009): the pure logic in lib/dryrun-core.cjs and the scenario manifest.
// No browser, no network, no AWS, no Playwright install needed:  node --test tools/uat/tests/dryrun.test.cjs (or npm test)
// Fixtures use invented ids and names only.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');
const core = require('../lib/dryrun-core.cjs');

const entry = (id, identity = 'public', app = 'tripplanner', steps = 3) => ({ id, app, identity, title: `Title ${id}`, steps });

// ── parseArgs ───────────────────────────────────────────────────────────────────────────────────────────────────────

test('parseArgs: defaults keep going, check egress, select everything', () => {
  const o = core.parseArgs([]);
  assert.deepEqual(o, { only: [], apps: [], identities: [], list: false, record: null, keepGoing: true, out: null, skipEgress: false });
});

test('parseArgs: lists are comma separated, ids upper-cased, flags set', () => {
  const o = core.parseArgs(['--only', 'bk-05, cis-08', '--app', 'booking,crm', '--identity', 'public', '--stop-on-fail',
    '--skip-egress-check', '--out', 'x/y', '--fast']);
  assert.deepEqual(o.only, ['BK-05', 'CIS-08']);
  assert.deepEqual(o.apps, ['booking', 'crm']);
  assert.deepEqual(o.identities, ['public']);
  assert.equal(o.keepGoing, false);
  assert.equal(o.skipEgress, true);
  assert.equal(o.out, 'x/y');
});

test('parseArgs: --record takes one id', () => {
  assert.equal(core.parseArgs(['--record', 'tp-02']).record, 'TP-02');
});

test('parseArgs: refuses an unknown option, a missing value and an unknown identity', () => {
  assert.throws(() => core.parseArgs(['--bogus']), /unknown option --bogus/);
  assert.throws(() => core.parseArgs(['--only']), /--only needs a value/);
  assert.throws(() => core.parseArgs(['--only', '--list']), /--only needs a value/);
  assert.throws(() => core.parseArgs(['--identity', 'root']), /unknown identity root/);
});

// ── describe ────────────────────────────────────────────────────────────────────────────────────────────────────────

test('describe: identity defaults to public; readOnly and step count are kept', () => {
  const d = core.describe({ id: 'X-01', app: 'demo', title: 'Demo', readOnly: true, steps: [{}, {}] }, 'demo/x-01.cjs');
  assert.deepEqual(d, { id: 'X-01', app: 'demo', identity: 'public', title: 'Demo', file: 'demo/x-01.cjs', steps: 2, readOnly: true });
});

test('describe: refuses a module without id / app / steps, an unknown identity and a data-step scenario', () => {
  assert.throws(() => core.describe(null, 'a.cjs'), /not a scenario module/);
  assert.throws(() => core.describe({ id: 'X', app: 'a', steps: [] }, 'a.cjs'), /id, app and steps are required/);
  assert.throws(() => core.describe({ id: 'X', app: 'a', identity: 'nobody', steps: [{}] }, 'a.cjs'), /unknown identity nobody/);
  assert.throws(() => core.describe({ id: 'X', app: 'a', fastOnly: true, steps: [{}] }, 'a.cjs'), /fastOnly/);
});

// ── select / signinPlan ─────────────────────────────────────────────────────────────────────────────────────────────

const SET = [entry('TP-01'), entry('BK-01', 'booking', 'booking'), entry('CIS-01', 'cis-admin', 'cis-admin'),
  entry('CRM-01', 'crm', 'crm'), entry('PRT-01', 'studio', 'content-studio'), entry('BK-02', 'booking', 'booking')];

test('select: no filter keeps the manifest order', () => {
  assert.deepEqual(core.select(SET, {}).map((e) => e.id), ['TP-01', 'BK-01', 'CIS-01', 'CRM-01', 'PRT-01', 'BK-02']);
});

test('select: --only, --app and --identity combine (AND)', () => {
  assert.deepEqual(core.select(SET, { only: ['BK-02', 'TP-01'] }).map((e) => e.id), ['TP-01', 'BK-02']);
  assert.deepEqual(core.select(SET, { apps: ['booking'] }).map((e) => e.id), ['BK-01', 'BK-02']);
  assert.deepEqual(core.select(SET, { apps: ['booking'], only: ['BK-02'] }).map((e) => e.id), ['BK-02']);
  assert.deepEqual(core.select(SET, { identities: ['public', 'crm'] }).map((e) => e.id), ['TP-01', 'CRM-01']);
});

test('select: an unknown --only id and a duplicate id throw', () => {
  assert.throws(() => core.select(SET, { only: ['NOPE-9'] }), /no scenario NOPE-9/);
  assert.throws(() => core.select([...SET, entry('TP-01')], {}), /duplicate scenario id TP-01/);
});

test('signinPlan: one sign-in per identity, public needs none, cheap ones first', () => {
  assert.deepEqual(core.signinPlan(SET), ['studio', 'crm', 'cis-admin', 'booking']);
  assert.deepEqual(core.signinPlan([entry('TP-01')]), []);
  assert.deepEqual(core.signinPlan([entry('BK-01', 'booking'), entry('BK-02', 'booking')]), ['booking']);
});

// ── redact / cell ───────────────────────────────────────────────────────────────────────────────────────────────────

test('redact: long opaque path and query segments go, uuids stay', () => {
  const token = 'Zx9'.repeat(12);
  assert.equal(core.redact(`GET /c/s/${token}?k=${token}`), 'GET /c/s/<redacted>?k=<redacted>');
  const uuid = '0f1e2d3c-4b5a-4968-8776-655443322110';
  assert.equal(core.redact(`/trips/${uuid}`), `/trips/${uuid}`);
  assert.equal(core.redact(null), null);
});

test('cell: one line, no pipes, capped', () => {
  assert.equal(core.cell('a |\n b'), 'a / b');
  assert.equal(core.cell('x'.repeat(10), 5), 'xxxx…');
  assert.equal(core.cell(undefined), '');
});

// ── outcome ─────────────────────────────────────────────────────────────────────────────────────────────────────────

const timeline = (statuses) => statuses.map((s, i) => ({ n: i + 1, status: s, start_ms: i * 1000, end_ms: i * 1000 + 500,
  ...(s === 'FAIL' ? { error: 'expected heading "Lotus Bay"\nlong trace' } : {}) }));

test('outcome: PASS with every step', () => {
  const o = core.outcome(entry('TP-01'), { result: { verdict: 'PASS', steps_total: 3, total_ms: 1500, blocked_writes: [] },
    timeline: timeline(['PASS', 'PASS', 'PASS']), exitCode: 0 });
  assert.equal(o.verdict, 'PASS');
  assert.equal(o.steps_passed, 3);
  assert.equal(o.steps_total, 3);
  assert.equal(o.ms, 1500);
  assert.equal(o.reason, '');
  assert.deepEqual(o.steps.map((s) => s.ms), [500, 500, 500]);
});

test('outcome: FAIL names the step, the steps after it are NOT RUN', () => {
  const o = core.outcome(entry('TP-01', 'public', 'tripplanner', 4), {
    result: { verdict: 'FAIL', failed_step: 2, failed_error: 'expected heading "Lotus Bay"', steps_total: 4, total_ms: 900 },
    timeline: timeline(['PASS', 'FAIL']), exitCode: 2 });
  assert.equal(o.verdict, 'FAIL');
  assert.equal(o.steps_passed, 1);
  assert.match(o.reason, /^step 2: expected heading "Lotus Bay"/);
  assert.deepEqual(o.steps.map((s) => s.status), ['PASS', 'FAIL', 'NOT RUN', 'NOT RUN']);
  assert.equal(o.steps[1].error, 'expected heading "Lotus Bay" long trace');
});

test('outcome: a PASS that tried to write is a FAIL, with the writes listed', () => {
  const o = core.outcome(entry('CRM-09', 'crm', 'crm', 1), {
    result: { verdict: 'PASS', steps_total: 1, blocked_writes: ['POST portal.example.invalid/bff/notes'] },
    timeline: timeline(['PASS']) });
  assert.equal(o.verdict, 'FAIL');
  assert.match(o.reason, /^blocked 1 write\(s\): POST portal\.example\.invalid\/bff\/notes/);
  assert.deepEqual(o.blocked_writes, ['POST portal.example.invalid/bff/notes']);
});

test('outcome: an aborted paid-path request keeps the PASS and adds a note', () => {
  const o = core.outcome(entry('TP-09'), {
    result: { verdict: 'PASS', steps_total: 3, blocked_urls: ['POST trip.example.invalid/api/trip/narrate'] },
    timeline: timeline(['PASS', 'PASS', 'PASS']) });
  assert.equal(o.verdict, 'PASS');
  assert.match(o.reason, /^note: aborted 1 paid-path request\(s\)/);
});

test('outcome: no result.json is a CRASH; a refused sign-in is BLOCKED', () => {
  const crash = core.outcome(entry('BK-01', 'booking', 'booking', 2), { result: null, exitCode: 'timeout', ms: 600000 });
  assert.equal(crash.verdict, 'CRASH');
  assert.match(crash.reason, /exited timeout without result\.json/);
  assert.deepEqual(crash.steps.map((s) => s.status), ['NOT RUN', 'NOT RUN']);
  const blocked = core.outcome(entry('BK-01', 'booking', 'booking', 2), { blocked: 'BLOCKED: booking: no code mail in 90 s' });
  assert.equal(blocked.verdict, 'BLOCKED');
  assert.equal(blocked.steps_passed, 0);
  assert.equal(blocked.steps.length, 2);
});

// ── shaTable / counts / exitCode ────────────────────────────────────────────────────────────────────────────────────

test('shaTable: flags a SHA that changed during the run, keeps errors and missing apps', () => {
  const t = core.shaTable(
    { api: { sha: 'aaaaaaa1', source: '/health' }, web: { sha: 'bbbbbbb1', source: '/healthz' }, down: { sha: null, source: '/h', error: 'fetch failed' } },
    { api: { sha: 'aaaaaaa1', source: '/health' }, web: { sha: 'bbbbbbb2', source: '/healthz' }, late: { sha: 'ccccccc1', source: '/x' } },
  );
  assert.equal(t.api.changed, false);
  assert.equal(t.web.changed, true);
  assert.equal(t.down.error, 'fetch failed');
  assert.equal(t.down.changed, false);
  assert.equal(t.late.before, null);
  assert.equal(t.late.after, 'ccccccc1');
});

test('counts and exitCode: 0 only when every scenario passed', () => {
  const pass = { verdict: 'PASS' };
  assert.deepEqual(core.counts([pass, { verdict: 'FAIL' }, { verdict: 'BLOCKED' }]), { PASS: 1, FAIL: 1, BLOCKED: 1, CRASH: 0 });
  assert.equal(core.exitCode([pass, pass]), 0);
  assert.equal(core.exitCode([pass, { verdict: 'BLOCKED' }]), 2);
  assert.equal(core.exitCode([]), 2);
});

// ── render ──────────────────────────────────────────────────────────────────────────────────────────────────────────

const RUN = {
  startedAt: '2026-10-31T10:00:00.000Z',
  finishedAt: '2026-10-31T10:05:00.000Z',
  egress: 'VN',
  signins: { booking: 'signed in', crm: 'BLOCKED: crm: secret lacks email' },
  shas: core.shaTable({ api: { sha: '1234567890', source: '/health' } }, { api: { sha: '1234567899', source: '/health' } }),
  outcomes: [
    core.outcome(entry('TP-01', 'public', 'tripplanner', 1), { result: { verdict: 'PASS', steps_total: 1, total_ms: 2000 }, timeline: timeline(['PASS']) }),
    core.outcome(entry('CRM-01', 'crm', 'crm', 1), { blocked: 'BLOCKED: crm: secret lacks email' }),
  ],
};

test('renderMarkdown: summary, versions (redeploy flagged), sign-ins, one row per scenario, per-step detail', () => {
  const md = core.renderMarkdown(RUN);
  assert.match(md, /^# UAT dry run — 2026-10-31/);
  assert.match(md, /Result: \*\*1 PASS\*\*, 0 FAIL, 1 BLOCKED, 0 CRASH of 2 scenarios\./);
  assert.match(md, /\| api \| 1234567 \| 1234567 \| \/health \| redeployed during the run \|/);
  assert.match(md, /\| crm \| BLOCKED: crm: secret lacks email \|/);
  assert.match(md, /\| TP-01 \| tripplanner \| public \| Title TP-01 \| PASS \| 1\/1 \| 2\.0 s \|  \|/);
  assert.match(md, /\| CRM-01 \| crm \| crm \| Title CRM-01 \| BLOCKED \| 0\/1 \|/);
  assert.match(md, /\| CRM-01 \| 1 \| NOT RUN \| — \|  \|/);
  // Every table row has the same number of cells as its header (no stray pipe from a cell).
  for (const block of md.split('\n\n').filter((b) => b.startsWith('|'))) {
    const rows = block.split('\n').filter(Boolean);
    const n = rows[0].split('|').length;
    for (const r of rows) assert.equal(r.split('|').length, n, r);
  }
});

test('renderTsv: one row per step plus the header, tabs in errors replaced', () => {
  const o = core.outcome(entry('TP-02', 'public', 'tripplanner', 1), { result: { verdict: 'FAIL', failed_step: 1, steps_total: 1 },
    timeline: [{ n: 1, status: 'FAIL', start_ms: 0, end_ms: 10, error: 'a\tb' }] });
  const tsv = core.renderTsv([o]);
  const lines = tsv.trim().split('\n');
  assert.equal(lines[0], 'scenario\tapp\tidentity\tverdict\tstep\tstatus\terror');
  assert.equal(lines[1], 'TP-02\ttripplanner\tpublic\tFAIL\t1\tFAIL\ta b');
});

test('stamp: folder-safe UTC stamp', () => {
  assert.equal(core.stamp(new Date('2026-10-31T16:05:09.123Z')), '2026-10-31T16-05-09Z');
});

// ── the dry-run manifest ────────────────────────────────────────────────────────────────────────────────────────────

test('manifest: every listed scenario loads, is a read-only dry-run scenario, ids are unique, about 20 of them', () => {
  const manifest = path.join(__dirname, '..', 'scenarios', 'dryrun.cjs');
  const files = require(manifest);
  const entries = files.map((rel) => {
    const sc = require(path.resolve(path.dirname(manifest), rel));
    const d = core.describe(sc, rel);
    // The pilot scenarios carry no readOnly flag (the runner forces the guard); every scenario written for the dry
    // run uses ro() from lib/dryrun-page.cjs.
    if (!/-pub-01\.cjs$/.test(rel)) assert.equal(d.readOnly, true, `${rel} is built with ro()`);
    for (const [i, s] of sc.steps.entries()) {
      assert.equal(typeof s.run, 'function', `${rel} step ${i + 1} has run()`);
      assert.ok(s.caption && s.caption.en && s.caption.vi, `${rel} step ${i + 1} has en and vi captions (record mode)`);
    }
    assert.ok(/^https:\/\//.test(sc.baseURL), `${rel} has an https baseURL`);
    return d;
  });
  assert.ok(entries.length >= 20, `at least 20 scenarios (${entries.length})`);
  core.select(entries, {}); // throws on a duplicate id
  const identities = new Set(entries.map((e) => e.identity));
  for (const who of core.IDENTITIES) assert.ok(identities.has(who), `the set covers identity ${who}`);
});

test('manifest: the paid model paths are blocked in both spellings, the free browse path is not', () => {
  const re = core.PAID_URLS.map((x) => new RegExp(x));
  const hit = (u) => re.some((r) => r.test(u));
  assert.ok(hit('https://trip.example.invalid/api/browse/search?q=lotus'));
  assert.ok(hit('https://trip.example.invalid/api/browse?resource=search&q=lotus'));
  assert.ok(hit('https://trip.example.invalid/api/browse?lang=en&resource=search'));
  assert.ok(hit('https://trip.example.invalid/api/trip/narrate'));
  assert.ok(!hit('https://trip.example.invalid/api/browse?resource=countries'));
  assert.ok(!hit('https://trip.example.invalid/api/browse/searchable-places'));
});
