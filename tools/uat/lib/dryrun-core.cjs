// Pure logic of the UAT dry-run runner (tools/uat/dryrun.cjs, AA-1009): arguments, scenario selection, the sign-in
// plan per identity, per-step rows from record.cjs output, the app SHA comparison and the result table (Markdown /
// TSV / JSON). No browser, no network, no AWS: unit tests in tools/uat/tests/dryrun.test.cjs (node --test).
'use strict';

// The identities a dry-run scenario may name (lib/signin.cjs signs each one in once, outside the recorded context).
// studio-editor (AA-855): the Content studio EDITOR of the E2E tenant; it can write, so only write scenarios use it.
// studio-audit (AA-855 W-01..W-04): the editor of the four synthetic audit tenants (lib/studio-audit.cjs), one per run.
// booking-staff / booking-maker / booking-checker (root ADR 0006a A10e): the Dev-only Booking E2E writers (supplier
// booking request + confirm; agency payment record; its approval), synthetic agencies only. Write set only.
// traveller (pilot rehearsal, AA-1086): a guest on a public page who WRITES (a trip, a request to an agency, a booking);
// it never signs in, so only write scenarios use it.
// studio-rehearsal (AA-1086 REH-*): the E2E OWNER of the synthetic pilot rehearsal agency (lib/rehearsal.cjs); write only.
const IDENTITIES = ['public', 'cis-admin', 'booking', 'studio', 'studio-editor', 'studio-audit', 'studio-rehearsal', 'crm',
  'booking-staff', 'booking-maker', 'booking-checker', 'traveller'];
// Identities with no sign-in: the runner starts them with no saved session.
const NO_SIGNIN = ['public', 'traveller'];
// Paths that reach a paid model or data provider: aborted in every dry-run scenario (record.cjs UAT_BLOCK_URLS), so a
// dry run can never start one, even by a stray click. TripPlanner free-text search (embedding) and narration (chat
// model), in both spellings (lib/botCheck.ts in AA-TripPlanner-Web); the writes among them are also non-GET.
const PAID_URLS = ['/api/browse/search(?:[?#]|$)', '/api/browse\\?(?:.*&)?resource=search\\b', '/api/trip/narrate(?:[?#]|$)'];
// Identities whose account CAN write (the backend would accept a write): the CRM has no read-only member role yet
// (roles owner / agent / assistant), so the dry run signs in the OWNER of the invented review agency. Only the browser
// guard of record.cjs keeps those scenarios read-only, so they run only on an explicit --include-writable. The other
// signed-in identities are refused writes by their backend too (403 e2e_read_only for the CIS / Booking E2E staff,
// 403 studio_role_forbidden for the Content studio viewer). The studio editor can write too (AA-855), and so can the
// guest traveller of the pilot rehearsal (it sends a trip to an agency, it books).
const WRITABLE_IDENTITIES = ['crm', 'studio-editor', 'studio-audit', 'studio-rehearsal', 'booking-staff', 'booking-maker', 'booking-checker', 'traveller'];
// Identities that only write scenarios sign in: no dry-run scenario uses them.
const WRITE_SET_ONLY_IDENTITIES = ['studio-editor', 'studio-rehearsal', 'booking-staff', 'booking-maker', 'booking-checker', 'traveller'];
// AA staff identities a write-set scenario may sign in: their backend refuses every write of the E2E session except a
// short, named allow-list on synthetic tenants (cis-admin: the tenant offboarding erasure drill, root ADR 0006a A10b-5).
// They stay in every dry run (read only there); a write-set scenario of theirs runs only by id with --include-writable.
const WRITE_SET_STAFF = ['cis-admin'];
// Exit code of a run stopped by the pilot guard (lib/pilot-guard.cjs EXIT_PILOT_GUARD).
const EXIT_PILOT_GUARD = 5;
// Order in which identities sign in: the cheap ones first, so a code-mail wait never delays the public pages.
const SIGNIN_ORDER = ['public', 'studio', 'studio-editor', 'studio-audit', 'studio-rehearsal', 'crm', 'cis-admin', 'booking',
  'booking-staff', 'booking-maker', 'booking-checker'];

/** Parse the runner's argv (without node and the script). Throws on an unknown option or a missing value. */
function parseArgs(argv) {
  const opts = { only: [], apps: [], identities: [], list: false, record: null, keepGoing: true, out: null,
    skipEgress: false, includeWritable: false, allowPaid: false, preview: false };
  const value = (i, name) => {
    const v = argv[i + 1];
    if (v === undefined || v.startsWith('--')) throw new Error(`${name} needs a value`);
    return v;
  };
  const csv = (v) => v.split(',').map((x) => x.trim()).filter(Boolean);
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    switch (a) {
      case '--only': opts.only = csv(value(i, a)).map((x) => x.toUpperCase()); i++; break;
      case '--app': opts.apps = csv(value(i, a)); i++; break;
      case '--identity': opts.identities = csv(value(i, a)); i++; break;
      case '--record': opts.record = value(i, a).toUpperCase(); i++; break;
      case '--out': opts.out = value(i, a); i++; break;
      case '--list': opts.list = true; break;
      case '--stop-on-fail': opts.keepGoing = false; break;
      case '--skip-egress-check': opts.skipEgress = true; break;
      case '--include-writable': opts.includeWritable = true; break;
      // AA-855: run (or record) a scenario of the write set (scenarios/write-set.cjs) that writes and calls a paid model.
      // Implies --include-writable (consent to pay covers consent to sign in a writable identity).
      case '--allow-paid': opts.allowPaid = true; opts.includeWritable = true; break;
      // AA-855: run only the read-only part of write-set scenarios (the steps before the first writing step), $0.
      case '--preview': opts.preview = true; break;
      case '--fast': break; // the dry run is always fast; accepted for symmetry with record.cjs
      default: throw new Error(`unknown option ${a}`);
    }
  }
  for (const id of opts.identities) if (!IDENTITIES.includes(id)) throw new Error(`unknown identity ${id}`);
  if (opts.preview && opts.allowPaid) throw new Error('--preview runs only the read-only part: it never takes --allow-paid');
  if (opts.preview && opts.record) throw new Error('--preview is a dry run, it records nothing');
  return opts;
}

/**
 * Normalise a loaded scenario module into a manifest entry. `identity` defaults to public (the pilot scenarios
 * TP-PUB-01 and PORTAL-PUB-01 carry none). Throws when the scenario is not a valid dry-run scenario.
 */
function describe(sc, file) {
  if (!sc || typeof sc !== 'object') throw new Error(`${file}: not a scenario module`);
  if (!sc.id || !sc.app || !Array.isArray(sc.steps) || !sc.steps.length) throw new Error(`${file}: id, app and steps are required`);
  const identity = sc.identity || 'public';
  if (!IDENTITIES.includes(identity)) throw new Error(`${file}: unknown identity ${identity}`);
  if (sc.fastOnly) throw new Error(`${file}: data steps (fastOnly) are not dry-run scenarios`);
  // Read-only by construction, not only by the runner's guard: a signed-in scenario is built with ro(), no scenario
  // lets a write through, and none runs its own prepare() (the runner signs the identity in; a prepare could write).
  if (!NO_SIGNIN.includes(identity) && sc.readOnly !== true) throw new Error(`${file}: a signed-in dry-run scenario must be readOnly (build it with ro())`);
  if (Array.isArray(sc.allowWrites) ? sc.allowWrites.length : sc.allowWrites) throw new Error(`${file}: allowWrites is not allowed in a dry-run scenario`);
  if (sc.prepare) throw new Error(`${file}: prepare() is not allowed in a dry-run scenario (the runner signs in)`);
  return { id: sc.id, app: sc.app, identity, title: sc.title || '', file, steps: sc.steps.length, readOnly: !!sc.readOnly };
}

/**
 * A scenario of the write set (scenarios/write-set.cjs, AA-855): it writes on a synthetic tenant and may call a paid
 * model, so it is never in a default run. Built with rw() (lib/uat-page.cjs): the browser guard stays on (readOnly)
 * with a narrow allowWrites list, prepare() signs it in. `paid` must be stated (true or false); `preview` = the number
 * of steps before the first step marked `writes` (the part a --preview run may take at $0).
 */
function describeWrite(sc, file) {
  if (!sc || typeof sc !== 'object') throw new Error(`${file}: not a scenario module`);
  if (!sc.id || !sc.app || !Array.isArray(sc.steps) || !sc.steps.length) throw new Error(`${file}: id, app and steps are required`);
  const identity = sc.identity || 'public';
  if (!WRITABLE_IDENTITIES.includes(identity) && !WRITE_SET_STAFF.includes(identity)) {
    throw new Error(`${file}: a write-set scenario signs in a writable identity (${[...WRITABLE_IDENTITIES, ...WRITE_SET_STAFF].join(', ')})`);
  }
  if (sc.readOnly !== true) throw new Error(`${file}: a write-set scenario keeps the browser guard on (build it with rw())`);
  if (!Array.isArray(sc.allowWrites) || !sc.allowWrites.length) throw new Error(`${file}: a write-set scenario names the writes it makes (allowWrites)`);
  if (typeof sc.paid !== 'boolean') throw new Error(`${file}: a write-set scenario states paid: true or false`);
  if (sc.fastOnly) throw new Error(`${file}: data steps (fastOnly) are not write-set scenarios`);
  // A paid take may open a paid path only by naming the exact PAID_URLS entry (record.cjs blockSources).
  for (const u of sc.allowPaidUrls || []) {
    if (!sc.paid) throw new Error(`${file}: allowPaidUrls on a scenario that is not paid`);
    if (!PAID_URLS.includes(u)) throw new Error(`${file}: allowPaidUrls names ${u}, not a PAID_URLS entry`);
  }
  // The steps that may write are marked, so a --preview knows where the read-only part ends.
  if (!sc.steps.some((s) => s && s.writes)) throw new Error(`${file}: a write-set scenario marks the steps that write (step(..., { writes: true }))`);
  return { id: sc.id, app: sc.app, identity, title: sc.title || '', file, steps: sc.steps.length, readOnly: true,
    writeSet: true, paid: sc.paid, preview: previewSteps(sc) };
}

/** How many steps come before the first step that writes (step.writes): the read-only part of a write scenario. */
function previewSteps(sc) {
  const i = sc.steps.findIndex((s) => s && s.writes);
  return i < 0 ? sc.steps.length : i;
}

/**
 * The URL blocks of one take (record.cjs): the scenario's own blockUrls plus the runner's (UAT_BLOCK_URLS, PAID_URLS
 * in every dry-run child). A paid scenario names in `allowPaidUrls` the PAID_URLS entries it needs (the pilot
 * rehearsal's planner search), and only those, only when the take may pay (UAT_ALLOW_PAID=1, never a preview), are
 * dropped from the runner's list; every other paid path stays blocked. A scenario's own block always holds.
 */
function blockSources({ blockUrls = [], allowPaidUrls = [] } = {}, env = process.env) {
  const runner = JSON.parse(env.UAT_BLOCK_URLS || '[]');
  const pays = env.UAT_ALLOW_PAID === '1' && env.UAT_PREVIEW !== '1';
  const open = new Set(pays ? allowPaidUrls : []);
  return [...blockUrls, ...runner.filter((x) => !open.has(x))];
}

// parseArgs upper-cases --only / --record ids; ids with a lower-case part (a split letter REH-08a, a phone variant
// REH-05.m) are matched back to their catalogue spelling here. Unknown ids stay as typed (select() then throws).
function canonicalIds(entries, opts) {
  if (!opts.only || !opts.only.length) return opts;
  const by = new Map(entries.map((e) => [e.id.toUpperCase(), e.id]));
  return { ...opts, only: opts.only.map((id) => by.get(String(id).toUpperCase()) || id) };
}

const matches = (e, opts) => (!opts.only || !opts.only.length || opts.only.includes(e.id))
  && (!opts.apps || !opts.apps.length || opts.apps.includes(e.app))
  && (!opts.identities || !opts.identities.length || opts.identities.includes(e.identity));

/**
 * The entries the options select, in manifest order. Unknown --only ids throw (a typo must not pass as "0 run").
 * Scenarios of a WRITABLE identity are left out unless opts.includeWritable; naming one explicitly (--only its id or
 * --identity crm) without the flag throws, so it is never skipped silently. A write-set id needs the flag too, whatever
 * its identity (a staff identity of WRITE_SET_STAFF writes only there).
 */
function select(entries, opts) {
  opts = canonicalIds(entries, opts);
  const ids = new Set(entries.map((e) => e.id));
  const dup = entries.find((e, i) => entries.findIndex((x) => x.id === e.id) !== i);
  if (dup) throw new Error(`duplicate scenario id ${dup.id}`);
  for (const id of opts.only || []) if (!ids.has(id)) throw new Error(`no scenario ${id} in the manifest`);
  // The write set (AA-855) runs only by id: never in the whole set, never through --app / --identity. A paid one needs
  // --allow-paid (or --preview: its read-only part only, $0); one without a read-only part has nothing to preview.
  const named = (opts.only || []);
  const writes = entries.filter((e) => e.writeSet && named.includes(e.id));
  if (opts.preview) {
    const none = writes.filter((e) => !e.preview).map((e) => e.id);
    if (none.length) throw new Error(`${none.join(', ')}: no read-only part to preview (its first step writes)`);
    if (named.some((id) => !entries.find((e) => e.id === id).writeSet)) throw new Error('--preview takes write-set ids only (--only W-01,...)');
    if (!writes.length) throw new Error('--preview needs --only with write-set ids');
    return writes;
  }
  const paid = writes.filter((e) => e.paid && !opts.allowPaid).map((e) => e.id);
  if (paid.length) {
    throw new Error(`${paid.join(', ')}: writes on a synthetic tenant and calls a paid model; add --allow-paid to run it (or --preview for its read-only part)`);
  }
  if (!opts.includeWritable) {
    const named = [...(opts.identities || []).filter((x) => WRITABLE_IDENTITIES.includes(x)),
      ...entries.filter((e) => (opts.only || []).includes(e.id) && (WRITABLE_IDENTITIES.includes(e.identity) || e.writeSet)).map((e) => e.id)];
    if (named.length) {
      throw new Error(`${named.join(', ')}: signs in an account that can write (no read-only role); add --include-writable to run it`);
    }
  }
  return entries.filter((e) => (!e.writeSet || named.includes(e.id)) && matches(e, opts)
    && (opts.includeWritable || !WRITABLE_IDENTITIES.includes(e.identity)));
}

/** Ids the options would select but leave out because their identity can write (said in the report). */
function skippedWritable(entries, opts) {
  opts = canonicalIds(entries, opts);
  if (opts.includeWritable) return [];
  return entries.filter((e) => !e.writeSet && matches(e, opts) && WRITABLE_IDENTITIES.includes(e.identity)).map((e) => e.id);
}

/** The identities to sign in for the selected entries (public and traveller need none), in SIGNIN_ORDER. */
function signinPlan(entries) {
  const need = new Set(entries.map((e) => e.identity));
  return SIGNIN_ORDER.filter((x) => !NO_SIGNIN.includes(x) && need.has(x));
}

// Link tokens and long opaque values never reach the report (record.cjs uses this same function). The report may be
// copied to the public root repo: AWS ARNs and 12-digit account numbers (an AccessDenied message names both, a bucket
// name may end in one) are masked too. Query values of key-like parameters are masked whatever their length: an
// agency's intake form key (`f=`, 22 characters, the Book now link) is shorter than the 30-character rule.
const SECRET_PARAMS = /([?&](?:f|key|form_key|token|code|secret|sig|signature)=)([^&#\s"'<>]+)/gi;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
function redact(x) {
  if (x == null) return x;
  return String(x)
    .replace(/arn:aws[a-z-]*:[^\s"'`,;)]*/g, '<arn>')
    // A uuid's last group can be 12 digits: the uuid alternative matches first and is kept whole.
    .replace(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|(?<![0-9A-Za-z])\d{12}(?![0-9A-Za-z])/gi,
      (m) => (m.length === 36 ? m : '<account>'))
    .replace(/([/=])([A-Za-z0-9_.~%-]{30,})/g, (m, lead, seg) => (UUID.test(seg) ? m : `${lead}<redacted>`))
    .replace(SECRET_PARAMS, '$1<redacted>');
}

/** One-line, table-safe text (no pipes, no newlines, capped). */
function cell(x, max = 160) {
  const s = redact(x == null ? '' : String(x)).replace(/\s+/g, ' ').replace(/\|/g, '/').trim();
  return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}

/**
 * The outcome of one scenario from record.cjs output. `result` / `timeline` are the parsed JSON files (null when the
 * child crashed before writing them); `blocked` is the sign-in failure reason when the identity could not sign in.
 */
function outcome(entry, { result = null, timeline = null, exitCode = null, blocked = null, pilotGuard = false, ms = null } = {}) {
  const base = { id: entry.id, app: entry.app, identity: entry.identity, title: entry.title, steps_total: entry.steps };
  const notRun = () => Array.from({ length: entry.steps }, (_, i) => ({ n: i + 1, status: 'NOT RUN', error: '' }));
  if (blocked) {
    return { ...base, verdict: 'BLOCKED', reason: cell(blocked), steps_passed: 0, ms: 0, steps: notRun(),
      ...(pilotGuard ? { pilot_guard: true } : {}) };
  }
  // record.cjs refused the session's tenant before any browser page (exit 5, no video).
  if ((result && result.verdict === 'BLOCKED' && result.pilot_guard) || exitCode === EXIT_PILOT_GUARD) {
    const why = (result && result.pilot_guard) || 'pilot_guard: refused by record.cjs';
    return { ...base, verdict: 'BLOCKED', reason: cell(why), steps_passed: 0, ms, steps: notRun(), pilot_guard: true };
  }
  if (!result) {
    return { ...base, verdict: 'CRASH', reason: `record.cjs exited ${exitCode} without result.json`, steps_passed: 0, ms,
      steps: Array.from({ length: entry.steps }, (_, i) => ({ n: i + 1, status: 'NOT RUN', error: '' })) };
  }
  const rows = (timeline || []).map((t) => ({ n: t.n, status: t.status, error: cell(t.error || ''), ms: t.end_ms - t.start_ms }));
  for (let n = rows.length + 1; n <= (result.steps_total || entry.steps); n++) rows.push({ n, status: 'NOT RUN', error: '' });
  const passed = rows.filter((r) => r.status === 'PASS').length;
  const blockedWrites = result.blocked_writes || [];
  let verdict = result.verdict === 'PASS' ? 'PASS' : 'FAIL';
  let reason = result.failed_step ? `step ${result.failed_step}: ${cell(result.failed_error || '')}` : '';
  // A read-only scenario whose page tried to write passed its asserts on a page that was not the real one: say so.
  if (verdict === 'PASS' && blockedWrites.length) {
    verdict = 'FAIL';
    reason = `blocked ${blockedWrites.length} write(s): ${cell(blockedWrites.slice(0, 3).join(', '))}`;
  }
  // A paid model path the page tried to reach was aborted before it left the browser: the asserts still decide the
  // verdict, the report says it happened (a page that calls a model on load is worth knowing about).
  const blockedUrls = result.blocked_urls || [];
  if (blockedUrls.length) {
    const note = `note: aborted ${blockedUrls.length} paid-path request(s): ${cell(blockedUrls.slice(0, 3).join(', '))}`;
    reason = reason ? `${reason}; ${note}` : note;
  }
  return { ...base, verdict, reason, steps_passed: passed, steps_total: rows.length, ms: result.total_ms ?? ms, steps: rows,
    blocked_writes: blockedWrites.map((w) => cell(w)), blocked_urls: blockedUrls.map((w) => cell(w)) };
}

/** Compare the app SHAs read before and after the run: { app: { before, after, changed, source } }. */
function shaTable(before, after) {
  const out = {};
  for (const app of new Set([...Object.keys(before || {}), ...Object.keys(after || {})])) {
    const b = (before || {})[app] || {};
    const a = (after || {})[app] || {};
    const sb = b.sha || null;
    const sa = a.sha || null;
    const error = a.error || b.error || null;
    out[app] = { before: sb, after: sa, source: a.source || b.source || '', changed: !!(sb && sa && sb !== sa),
      error: error && cell(error, 200) };
  }
  return out;
}

function counts(outcomes) {
  const c = { PASS: 0, FAIL: 0, BLOCKED: 0, CRASH: 0 };
  for (const o of outcomes) c[o.verdict] = (c[o.verdict] || 0) + 1;
  return c;
}

/** Exit code of the run: 5 when the pilot guard refused any scenario, 0 every scenario PASS, 2 otherwise. */
function exitCode(outcomes) {
  if (outcomes.some((o) => o.pilot_guard)) return EXIT_PILOT_GUARD;
  return outcomes.length && outcomes.every((o) => o.verdict === 'PASS') ? 0 : 2;
}

const short = (s) => (s ? String(s).slice(0, 7) : '—');
const secs = (ms) => (ms == null ? '—' : `${(ms / 1000).toFixed(1)} s`);

/** The result table as Markdown: summary, app SHAs, one row per scenario, then the per-step detail. */
function renderMarkdown(run) {
  const { outcomes, shas, startedAt, finishedAt, signins = {}, egress = '', skipped = [] } = run;
  const c = counts(outcomes);
  const L = [];
  L.push(`# UAT dry run — ${startedAt.slice(0, 10)}`);
  L.push('');
  L.push(`Started ${startedAt}, finished ${finishedAt}. Mode: fast (asserts only, no video, no TTS). Egress: ${egress || '—'}.`);
  L.push(`Result: **${c.PASS} PASS**, ${c.FAIL} FAIL, ${c.BLOCKED} BLOCKED, ${c.CRASH} CRASH of ${outcomes.length} scenarios.`);
  const paidIds = run.paid || [];
  if (paidIds.length) {
    L.push(`PAID run (--allow-paid): ${paidIds.join(', ')} write on the audit tenant and call the writing model (cost in the LLM ledger). Every other request outside their allow-lists is aborted and listed. Dev only.`);
  } else if (run.preview) {
    L.push('Preview: only the read-only part of the write scenarios ran (the steps before the first write). No writes, no LLM or paid calls, Dev only. Cost $0.');
  } else {
    L.push('No writes (non-GET requests are aborted and listed), no LLM or paid calls, Dev only. Cost $0.');
  }
  if (skipped.length) {
    L.push(`Not run: ${skipped.join(', ')} (their identity can write; run with --include-writable).`);
  }
  L.push('');
  L.push('## App versions');
  L.push('');
  L.push('| App | SHA at start | SHA at end | Source | Note |');
  L.push('|---|---|---|---|---|');
  for (const [app, s] of Object.entries(shas)) {
    const note = s.changed ? 'redeployed during the run' : (s.error ? cell(s.error, 80) : '');
    L.push(`| ${app} | ${short(s.before)} | ${short(s.after)} | ${cell(s.source, 60)} | ${note} |`);
  }
  L.push('');
  if (Object.keys(signins).length) {
    L.push('## Sign-in per identity');
    L.push('');
    L.push('| Identity | Result |');
    L.push('|---|---|');
    for (const [who, r] of Object.entries(signins)) L.push(`| ${who} | ${cell(r, 120)} |`);
    L.push('');
  }
  L.push('## Scenarios');
  L.push('');
  L.push('| Id | App | Identity | Title | Verdict | Steps | Time | Failure / note |');
  L.push('|---|---|---|---|---|---|---|---|');
  for (const o of outcomes) {
    L.push(`| ${o.id} | ${o.app} | ${o.identity} | ${cell(o.title, 70)} | ${o.verdict} | ${o.steps_passed}/${o.steps_total} | ${secs(o.ms)} | ${o.reason || ''} |`);
  }
  L.push('');
  L.push('## Steps');
  L.push('');
  L.push('| Id | Step | Status | Time | Error |');
  L.push('|---|---|---|---|---|');
  for (const o of outcomes) for (const s of o.steps) L.push(`| ${o.id} | ${s.n} | ${s.status} | ${s.ms == null ? '—' : secs(s.ms)} | ${s.error || ''} |`);
  L.push('');
  return L.join('\n');
}

/** One TSV row per step (scenario, app, identity, verdict, step, status, error), plus a header. */
function renderTsv(outcomes) {
  const rows = [['scenario', 'app', 'identity', 'verdict', 'step', 'status', 'error'].join('\t')];
  for (const o of outcomes) for (const s of o.steps) rows.push([o.id, o.app, o.identity, o.verdict, s.n, s.status, (s.error || '').replace(/\t/g, ' ')].join('\t'));
  return `${rows.join('\n')}\n`;
}

/** Folder-safe UTC stamp: 2026-10-31T16-05-09Z. */
function stamp(d = new Date()) {
  return d.toISOString().replace(/\.\d{3}Z$/, 'Z').replace(/:/g, '-');
}

module.exports = {
  IDENTITIES, NO_SIGNIN, WRITABLE_IDENTITIES, WRITE_SET_ONLY_IDENTITIES, WRITE_SET_STAFF, SIGNIN_ORDER, EXIT_PILOT_GUARD, PAID_URLS, blockSources, parseArgs, canonIds: canonicalIds, canonicalIds, describe, describeWrite, previewSteps, select, skippedWritable, signinPlan, redact, cell, outcome, shaTable, counts, exitCode,
  renderMarkdown, renderTsv, stamp,
};
