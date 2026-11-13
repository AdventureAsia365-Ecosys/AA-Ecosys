// Unit tests of the UAT dry-run runner (AA-1009): the pure logic in lib/dryrun-core.cjs and the scenario manifest.
// No browser, no network, no AWS, no Playwright install needed:  node --test tools/uat/tests/dryrun.test.cjs (or npm test)
// Fixtures use invented ids and names only.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');
const fs = require('fs');
const core = require('../lib/dryrun-core.cjs');
const guard = require('../lib/net-guard.cjs');
const mailbox = require('../lib/mailbox.cjs');

const entry = (id, identity = 'public', app = 'tripplanner', steps = 3) => ({ id, app, identity, title: `Title ${id}`, steps });

// ── parseArgs ───────────────────────────────────────────────────────────────────────────────────────────────────────

test('parseArgs: defaults keep going, check egress, select everything', () => {
  const o = core.parseArgs([]);
  assert.deepEqual(o, { only: [], apps: [], identities: [], list: false, record: null, keepGoing: true, out: null, skipEgress: false,
    includeWritable: false, allowPaid: false, preview: false });
  assert.equal(core.parseArgs(['--include-writable']).includeWritable, true);
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

test('describe: a signed-in scenario must be read-only; allowWrites and prepare() are refused', () => {
  assert.throws(() => core.describe({ id: 'X', app: 'a', identity: 'booking', steps: [{}] }, 'a.cjs'), /must be readOnly/);
  assert.throws(() => core.describe({ id: 'X', app: 'a', identity: 'crm', readOnly: false, steps: [{}] }, 'a.cjs'), /must be readOnly/);
  assert.throws(() => core.describe({ id: 'X', app: 'a', identity: 'crm', readOnly: true, allowWrites: ['/bff/notes'], steps: [{}] }, 'a.cjs'),
    /allowWrites is not allowed/);
  assert.throws(() => core.describe({ id: 'X', app: 'a', readOnly: true, allowWrites: ['/x'], steps: [{}] }, 'a.cjs'), /allowWrites/);
  assert.throws(() => core.describe({ id: 'X', app: 'a', identity: 'studio', readOnly: true, prepare: () => {}, steps: [{}] }, 'a.cjs'),
    /prepare\(\) is not allowed/);
  // A public pilot without the flag stays valid: the runner forces the guard and a public page has no session to write with.
  assert.equal(core.describe({ id: 'X', app: 'a', steps: [{}] }, 'a.cjs').readOnly, false);
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

test('select: no filter keeps the manifest order and leaves the writable identity out', () => {
  assert.deepEqual(core.select(SET, {}).map((e) => e.id), ['TP-01', 'BK-01', 'CIS-01', 'PRT-01', 'BK-02']);
  assert.deepEqual(core.skippedWritable(SET, {}), ['CRM-01']);
  assert.deepEqual(core.select(SET, { includeWritable: true }).map((e) => e.id), ['TP-01', 'BK-01', 'CIS-01', 'CRM-01', 'PRT-01', 'BK-02']);
  assert.deepEqual(core.skippedWritable(SET, { includeWritable: true }), []);
  assert.deepEqual(core.skippedWritable(SET, { apps: ['booking'] }), []);
});

test('select: naming a writable-identity scenario without --include-writable throws, never a silent skip', () => {
  assert.throws(() => core.select(SET, { only: ['CRM-01'] }), /CRM-01: signs in an account that can write.*--include-writable/);
  assert.throws(() => core.select(SET, { identities: ['crm'] }), /crm: signs in an account that can write/);
  assert.deepEqual(core.select(SET, { only: ['CRM-01'], includeWritable: true }).map((e) => e.id), ['CRM-01']);
  assert.deepEqual(core.WRITABLE_IDENTITIES, ['crm', 'studio-editor', 'studio-audit', 'traveller']);
});

test('select: an id with a lower-case part (split letter, phone variant) is found from the upper-cased --only', () => {
  const set = [entry('REH-08a', 'public'), entry('REH-05.m', 'public'), entry('TP-01')];
  const o = core.parseArgs(['--only', 'reh-08a,REH-05.m']);
  assert.deepEqual(core.select(set, o).map((e) => e.id), ['REH-08a', 'REH-05.m']);
  assert.throws(() => core.select(set, { only: ['REH-09A'] }), /no scenario REH-09A/);
});

test('select: --only, --app and --identity combine (AND)', () => {
  assert.deepEqual(core.select(SET, { only: ['BK-02', 'TP-01'] }).map((e) => e.id), ['TP-01', 'BK-02']);
  assert.deepEqual(core.select(SET, { apps: ['booking'] }).map((e) => e.id), ['BK-01', 'BK-02']);
  assert.deepEqual(core.select(SET, { apps: ['booking'], only: ['BK-02'] }).map((e) => e.id), ['BK-02']);
  assert.deepEqual(core.select(SET, { identities: ['public', 'crm'], includeWritable: true }).map((e) => e.id), ['TP-01', 'CRM-01']);
});

test('select: an unknown --only id and a duplicate id throw', () => {
  assert.throws(() => core.select(SET, { only: ['NOPE-9'] }), /no scenario NOPE-9/);
  assert.throws(() => core.select([...SET, entry('TP-01')], {}), /duplicate scenario id TP-01/);
});

test('signinPlan: one sign-in per identity, public needs none, cheap ones first', () => {
  assert.deepEqual(core.signinPlan(SET), ['studio', 'crm', 'cis-admin', 'booking']);
  assert.deepEqual(core.signinPlan([entry('TP-01')]), []);
  assert.deepEqual(core.signinPlan([entry('BK-01', 'booking'), entry('BK-02', 'booking')]), ['booking']);
  // The pilot rehearsal's guest traveller writes but never signs in.
  assert.deepEqual(core.signinPlan([entry('REH-06', 'traveller')]), []);
  assert.ok(core.NO_SIGNIN.includes('traveller') && core.WRITABLE_IDENTITIES.includes('traveller'));
});

// ── the write set (AA-855) ──────────────────────────────────────────────────────────────────────────────────────────

const wstep = (writes = false) => ({ caption: { en: 'e', vi: 'v' }, run: async () => {}, ...(writes ? { writes: true } : {}) });
const wsc = (over = {}) => ({ id: 'W-91', app: 'content-studio', identity: 'studio-audit', readOnly: true, allowWrites: ['\\/x$'],
  paid: true, steps: [wstep(), wstep(true), wstep()], ...over });

test('parseArgs: --allow-paid implies --include-writable; --preview is $0 and never pays or records', () => {
  const o = core.parseArgs(['--allow-paid', '--record', 'w-01']);
  assert.equal(o.allowPaid, true);
  assert.equal(o.includeWritable, true);
  assert.equal(o.record, 'W-01');
  assert.equal(core.parseArgs(['--preview', '--only', 'W-01']).preview, true);
  assert.throws(() => core.parseArgs(['--preview', '--allow-paid']), /never takes --allow-paid/);
  assert.throws(() => core.parseArgs(['--preview', '--record', 'W-01']), /records nothing/);
});

test('describeWrite: a writable identity, the guard on, a named allow-list, paid stated, writing steps marked', () => {
  const d = core.describeWrite(wsc(), 'content-studio/w-91.cjs');
  assert.deepEqual(d, { id: 'W-91', app: 'content-studio', identity: 'studio-audit', title: '', file: 'content-studio/w-91.cjs',
    steps: 3, readOnly: true, writeSet: true, paid: true, preview: 1 });
  assert.throws(() => core.describeWrite(wsc({ identity: 'studio' }), 'a.cjs'), /writable identity/);
  assert.throws(() => core.describeWrite(wsc({ readOnly: false }), 'a.cjs'), /browser guard on/);
  assert.throws(() => core.describeWrite(wsc({ allowWrites: [] }), 'a.cjs'), /names the writes/);
  assert.throws(() => core.describeWrite(wsc({ paid: undefined }), 'a.cjs'), /states paid/);
  assert.throws(() => core.describeWrite(wsc({ steps: [wstep(), wstep()] }), 'a.cjs'), /marks the steps that write/);
  assert.throws(() => core.describeWrite(wsc({ fastOnly: true }), 'a.cjs'), /fastOnly/);
  assert.equal(core.previewSteps(wsc({ steps: [wstep(true), wstep()] })), 0);
});

const WSET = [...SET, { ...entry('W-91', 'studio-audit', 'content-studio'), writeSet: true, paid: true, preview: 2 },
  { ...entry('W-92', 'studio-audit', 'content-studio'), writeSet: true, paid: true, preview: 0 },
  { ...entry('W-93', 'studio-editor', 'content-studio'), writeSet: true, paid: false, preview: 1 }];

test('select: the write set is never in the whole set, nor reached by --app / --identity, even with --allow-paid', () => {
  const ids = (o) => core.select(WSET, o).map((e) => e.id);
  assert.ok(!ids({}).some((x) => x.startsWith('W-')));
  assert.ok(!ids({ includeWritable: true, allowPaid: true }).some((x) => x.startsWith('W-')));
  assert.ok(!ids({ apps: ['content-studio'], includeWritable: true, allowPaid: true }).some((x) => x.startsWith('W-')));
  assert.ok(!ids({ identities: ['studio-audit'], includeWritable: true, allowPaid: true }).some((x) => x.startsWith('W-')));
  assert.deepEqual(core.skippedWritable(WSET, {}), ['CRM-01']);
});

test('select: a paid write-set id needs --allow-paid; a free one needs --include-writable', () => {
  assert.throws(() => core.select(WSET, { only: ['W-91'] }), /W-91: writes on a synthetic tenant and calls a paid model; add --allow-paid/);
  assert.throws(() => core.select(WSET, { only: ['W-91'], includeWritable: true }), /add --allow-paid/);
  assert.deepEqual(core.select(WSET, { only: ['W-91'], includeWritable: true, allowPaid: true }).map((e) => e.id), ['W-91']);
  assert.throws(() => core.select(WSET, { only: ['W-93'] }), /W-93: signs in an account that can write/);
  assert.deepEqual(core.select(WSET, { only: ['W-93'], includeWritable: true }).map((e) => e.id), ['W-93']);
});

test('select: --preview takes write-set ids with a read-only part only', () => {
  assert.deepEqual(core.select(WSET, { only: ['W-91', 'W-93'], preview: true }).map((e) => e.id), ['W-91', 'W-93']);
  assert.throws(() => core.select(WSET, { only: ['W-92'], preview: true }), /W-92: no read-only part to preview/);
  assert.throws(() => core.select(WSET, { only: ['TP-01'], preview: true }), /write-set ids only/);
  assert.throws(() => core.select(WSET, { preview: true }), /needs --only/);
});

test('renderMarkdown: a paid run and a preview say so instead of "Cost $0"', () => {
  const base = { startedAt: '2026-11-06T01:00:00Z', finishedAt: '2026-11-06T01:30:00Z', shas: {}, outcomes: [] };
  const paid = core.renderMarkdown({ ...base, paid: ['W-91'] });
  assert.match(paid, /PAID run \(--allow-paid\): W-91/);
  assert.doesNotMatch(paid, /Cost \$0/);
  assert.match(core.renderMarkdown({ ...base, preview: true }), /Preview: only the read-only part/);
  assert.match(core.renderMarkdown(base), /No writes .*Cost \$0/);
});

test('write set manifest: every entry loads as a write-set scenario, ids unique and apart from the dry-run set', () => {
  const ws = path.join(__dirname, '..', 'scenarios', 'write-set.cjs');
  const manifest = path.join(__dirname, '..', 'scenarios', 'dryrun.cjs');
  const w = require(ws).map((rel) => core.describeWrite(require(path.resolve(path.dirname(ws), rel)), rel));
  const d = require(manifest).map((rel) => core.describe(require(path.resolve(path.dirname(manifest), rel)), rel));
  core.select([...d, ...w], {}); // throws on a duplicate id across both sets
  for (const id of ['W-01', 'W-02', 'W-03']) {
    const e = w.find((x) => x.id === id);
    assert.ok(e && e.paid && e.identity === 'studio-audit', `${id} is a paid studio-audit write scenario`);
  }
  assert.ok(d.find((x) => x.id === 'W-04' && x.identity === 'studio-audit'), 'W-04 (read only) is in the dry-run set');
  assert.ok(w.find((x) => x.id === 'W-01').preview >= 1 && w.find((x) => x.id === 'W-02').preview >= 1, 'W-01 / W-02 have a read-only part');
  assert.equal(w.find((x) => x.id === 'W-03').preview, 0);
});

// ── redact / cell ───────────────────────────────────────────────────────────────────────────────────────────────────

test('redact: long opaque path and query segments go, uuids stay', () => {
  const token = 'Zx9'.repeat(12);
  assert.equal(core.redact(`GET /c/s/${token}?k=${token}`), 'GET /c/s/<redacted>?k=<redacted>');
  const uuid = '0f1e2d3c-4b5a-4968-8776-655443322110';
  assert.equal(core.redact(`/trips/${uuid}`), `/trips/${uuid}`);
  assert.equal(core.redact(null), null);
});

test('redact: AWS ARNs and 12-digit account numbers are masked, longer numbers and hex ids are not', () => {
  const acct = '4'.repeat(6) + '7'.repeat(6); // invented
  const msg = `aws s3api failed: User: arn:aws:sts::${acct}:assumed-role/Demo-Role/demo-session is not authorized `
    + `on resource arn:aws:s3:::demo-mail-${acct}/inbound/`;
  const r = core.redact(msg);
  assert.ok(!r.includes(acct), r);
  assert.ok(!/arn:aws/.test(r), r);
  assert.match(r, /User: <arn> is not authorized on resource <arn>/);
  assert.equal(core.redact(`bucket demo-mail-${acct}`), 'bucket demo-mail-<account>');
  assert.equal(core.redact('took 1761904000123 ms'), 'took 1761904000123 ms'); // 13 digits: a timestamp, kept
  assert.equal(core.redact('sha a123456789012b'), 'sha a123456789012b');
  const uuid = '0f1e2d3c-4b5a-4968-8776-655443322110'; // last group is 12 digits
  assert.equal(core.redact(`/trips/${uuid}`), `/trips/${uuid}`);
});

test('an AccessDenied sign-in failure reaches cell() and the Markdown report without the ARN or the account', () => {
  const acct = '1'.repeat(4) + '2'.repeat(4) + '3'.repeat(4); // invented
  const err = `cis-admin: aws s3api list-objects-v2 failed: An error occurred (AccessDenied) when calling the ListObjectsV2 `
    + `operation: User: arn:aws:sts::${acct}:assumed-role/Demo-Admin/s is not authorized to perform: s3:ListBucket on `
    + `resource: "arn:aws:s3:::demo-e2e-mail-${acct}"`;
  const c = core.cell(`BLOCKED: ${err}`, 200);
  assert.ok(!c.includes(acct) && !c.includes('arn:'), c);
  const md = core.renderMarkdown({ ...RUN_BASE(), signins: { 'cis-admin': c },
    outcomes: [core.outcome(entry('CIS-01', 'cis-admin', 'cis-admin', 1), { blocked: c })] });
  assert.ok(!md.includes(acct) && !md.includes('arn:aws'), md);
  assert.match(md, /AccessDenied/);
});

test('mailbox awsErrorCode: the error code only, never the CLI text', () => {
  const acct = '9'.repeat(12);
  const stderr = `\nAn error occurred (AccessDenied) when calling the ListObjectsV2 operation: User: arn:aws:sts::${acct}:assumed-role/X/y`;
  assert.equal(mailbox.awsErrorCode({ stderr, code: 254 }), 'AccessDenied');
  assert.equal(mailbox.awsErrorCode({ stderr: 'An error occurred (ExpiredToken) when calling ...', code: 254 }), 'ExpiredToken');
  assert.equal(mailbox.awsErrorCode({ killed: true, signal: 'SIGTERM' }), 'timeout');
  assert.match(mailbox.awsErrorCode({ stderr: 'Error when retrieving token from sso: Token has expired', code: 255 }), /credentials expired/);
  assert.equal(mailbox.awsErrorCode({ stderr: `boom ${acct}`, code: 1 }), 'exit 1');
  assert.equal(mailbox.awsErrorCode({ code: 'ENOENT' }), 'aws CLI not found');
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

test('outcome: a CIS admin page whose only aborted request is the session keep-alive stays PASS', () => {
  const base = 'https://admin.example.lumiguides.it.com';
  const keepAlive = `${base}/api/auth/refresh`;
  assert.equal(guard.classify(keepAlive, base), 'other');
  // record.cjs puts an 'other' request in blocked_other, never in blocked_writes.
  const o = core.outcome(entry('CIS-01', 'cis-admin', 'cis-admin', 2), {
    result: { verdict: 'PASS', steps_total: 2, blocked_writes: [], blocked_other: ['POST admin.example.lumiguides.it.com/api/auth/refresh'] },
    timeline: timeline(['PASS', 'PASS']) });
  assert.equal(o.verdict, 'PASS');
  assert.equal(o.reason, '');
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

const RUN_BASE = () => ({
  startedAt: '2026-10-31T10:00:00.000Z', finishedAt: '2026-10-31T10:05:00.000Z', egress: 'VN', shas: {}, signins: {}, outcomes: [],
});

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

test('renderMarkdown: names the scenarios left out because their identity can write', () => {
  const md = core.renderMarkdown({ ...RUN_BASE(), skipped: ['CRM-01', 'CRM-02'] });
  assert.match(md, /Not run: CRM-01, CRM-02 \(their identity can write; run with --include-writable\)\./);
  assert.ok(!/Not run:/.test(core.renderMarkdown(RUN_BASE())));
});

test('shaTable: a version-read error is redacted', () => {
  const t = core.shaTable({ x: { sha: null, source: '/h', error: `denied for arn:aws:iam::${'5'.repeat(12)}:role/R` } }, {});
  assert.equal(t.x.error, 'denied for <arn>');
});

// ── net-guard (record.cjs read-only guard) ──────────────────────────────────────────────────────────────────────────

test('net-guard isChallengeProof: only the AWS WAF token host, never the app or a look-alike', () => {
  assert.ok(guard.isChallengeProof('https://abc123.def456.us-west-1.token.awswaf.com/abc123/x/y/mp_verify'));
  for (const u of ['https://tripplanner.example.invalid/api/trip/send', 'https://token.awswaf.com.example.invalid/verify',
    'http://abc.us-west-1.token.awswaf.com/verify', 'https://example.invalid/?u=https://a.token.awswaf.com/']) {
    assert.equal(guard.isChallengeProof(u), false, u);
  }
});

test('net-guard classify: app writes fail, telemetry / session keep-alive / third party are listed apart', () => {
  const base = 'https://admin.example.lumiguides.it.com';
  assert.equal(guard.classify(`${base}/api/admin/tours/7/notes`, base), 'write');
  assert.equal(guard.classify('https://api-demo.lumiguides.it.com/v1/items', base), 'write'); // other first-party host
  assert.equal(guard.classify(`${base}/api/auth/refresh`, base), 'other');
  assert.equal(guard.classify(`${base}/api/auth/refresh?x=1`, base), 'other');
  assert.equal(guard.classify(`${base}/api/auth/refresh-token-rotate`, base), 'write');
  assert.equal(guard.classify(`${base}/api/auth/logout`, base), 'write');
  assert.equal(guard.classify(`${base}/_vercel/insights/event`, base), 'other');
  assert.equal(guard.classify(`${base}/monitoring`, base), 'other');
  assert.equal(guard.classify('https://events.mapbox.com/events/v2', base), 'other');
  assert.equal(guard.classify('https://third.example.invalid/collect', base), 'other');
  assert.equal(guard.classify('not a url', base), 'write');
  assert.ok(guard.isRead('get') && guard.isRead('HEAD') && guard.isRead('OPTIONS') && !guard.isRead('POST'));
});

test('net-guard guardRequestContext: Node-side writes are refused and reported, reads pass, allow-list honoured', async () => {
  const calls = [];
  const rq = { async fetch(u, o = {}) { calls.push(`${o.method || 'GET'} ${u}`); return { ok: true }; } };
  // The real APIRequestContext helpers all go through this.fetch(): mirror that.
  for (const m of ['get', 'post', 'put', 'patch', 'delete', 'head']) rq[m] = function (u, o) { return this.fetch(u, { ...o, method: m.toUpperCase() }); };
  const blocked = [];
  guard.guardRequestContext(rq, { allow: [/\/allowed$/], onBlocked: (m, u) => blocked.push(`${m} ${u}`) });
  await rq.get('https://a.example.invalid/list');
  await rq.head('https://a.example.invalid/list');
  await rq.post('https://a.example.invalid/allowed');
  await assert.rejects(rq.post('https://a.example.invalid/notes', { data: {} }), /read-only run: POST/);
  await assert.rejects(rq.delete('https://a.example.invalid/notes/1'), /read-only run: DELETE/);
  await assert.rejects(rq.fetch('https://a.example.invalid/x', { method: 'patch' }), /read-only run: PATCH/);
  const req = { url: () => 'https://a.example.invalid/r', method: () => 'PUT' };
  await assert.rejects(rq.fetch(req), /read-only run: PUT/);
  assert.deepEqual(calls, ['GET https://a.example.invalid/list', 'HEAD https://a.example.invalid/list', 'POST https://a.example.invalid/allowed']);
  assert.deepEqual(blocked, ['POST https://a.example.invalid/notes', 'DELETE https://a.example.invalid/notes/1',
    'PATCH https://a.example.invalid/x', 'PUT https://a.example.invalid/r']);
  assert.equal(guard.guardRequestContext(rq), rq); // wrapping twice is a no-op
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
  // The studio editor and the guest traveller write, so only write scenarios use them (AA-855, pilot rehearsal): the
  // read-only set covers every other identity.
  for (const who of core.IDENTITIES.filter((x) => !['studio-editor', 'traveller'].includes(x))) assert.ok(identities.has(who), `the set covers identity ${who}`);
  assert.ok(!identities.has('studio-editor'), 'no dry-run scenario signs in the studio editor');
  // The default run leaves the writable identity's scenarios out and says so.
  const def = core.select(entries, {});
  assert.ok(def.length >= 20 && def.every((e) => !core.WRITABLE_IDENTITIES.includes(e.identity)));
  assert.ok(core.skippedWritable(entries, {}).length > 0);
});

test('manifest: dry-run scenario code makes no Node-side request, new context or process of its own', () => {
  const manifest = path.join(__dirname, '..', 'scenarios', 'dryrun.cjs');
  const sources = [path.join(__dirname, '..', 'lib', 'dryrun-page.cjs'),
    ...require(manifest).map((rel) => path.resolve(path.dirname(manifest), rel))];
  const banned = [/\.request\s*\.\s*(post|put|patch|delete|fetch)\b/, /\brequest\.newContext\b/, /\bnewContext\s*\(/,
    /require\(['"](?:node:)?child_process['"]\)/, /require\(['"][^'"]*crm-signin/, /\bbffCall\b/];
  for (const f of sources) {
    const src = fs.readFileSync(f, 'utf8');
    for (const re of banned) assert.ok(!re.test(src), `${path.basename(f)} matches ${re}`);
  }
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
