// Pure logic of the UAT dry-run runner (tools/uat/dryrun.cjs, AA-1009): arguments, scenario selection, the sign-in
// plan per identity, per-step rows from record.cjs output, the app SHA comparison and the result table (Markdown /
// TSV / JSON). No browser, no network, no AWS: unit tests in tools/uat/tests/dryrun.test.cjs (node --test).
'use strict';

// The identities a dry-run scenario may name (lib/signin.cjs signs each one in once, outside the recorded context).
const IDENTITIES = ['public', 'cis-admin', 'booking', 'studio', 'crm'];
// Paths that reach a paid model or data provider: aborted in every dry-run scenario (record.cjs UAT_BLOCK_URLS), so a
// dry run can never start one, even by a stray click. TripPlanner free-text search (embedding) and narration (chat
// model), in both spellings (lib/botCheck.ts in AA-TripPlanner-Web); the writes among them are also non-GET.
const PAID_URLS = ['/api/browse/search(?:[?#]|$)', '/api/browse\\?(?:.*&)?resource=search\\b', '/api/trip/narrate(?:[?#]|$)'];
// Identities whose account CAN write (the backend would accept a write): the CRM has no read-only member role yet
// (roles owner / agent / assistant), so the dry run signs in the OWNER of the invented review agency. Only the browser
// guard of record.cjs keeps those scenarios read-only, so they run only on an explicit --include-writable. The other
// signed-in identities are refused writes by their backend too (403 e2e_read_only for the CIS / Booking E2E staff,
// 403 studio_role_forbidden for the Content studio viewer).
const WRITABLE_IDENTITIES = ['crm'];
// Order in which identities sign in: the cheap ones first, so a code-mail wait never delays the public pages.
const SIGNIN_ORDER = ['public', 'studio', 'crm', 'cis-admin', 'booking'];

/** Parse the runner's argv (without node and the script). Throws on an unknown option or a missing value. */
function parseArgs(argv) {
  const opts = { only: [], apps: [], identities: [], list: false, record: null, keepGoing: true, out: null,
    skipEgress: false, includeWritable: false };
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
      case '--fast': break; // the dry run is always fast; accepted for symmetry with record.cjs
      default: throw new Error(`unknown option ${a}`);
    }
  }
  for (const id of opts.identities) if (!IDENTITIES.includes(id)) throw new Error(`unknown identity ${id}`);
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
  if (identity !== 'public' && sc.readOnly !== true) throw new Error(`${file}: a signed-in dry-run scenario must be readOnly (build it with ro())`);
  if (Array.isArray(sc.allowWrites) ? sc.allowWrites.length : sc.allowWrites) throw new Error(`${file}: allowWrites is not allowed in a dry-run scenario`);
  if (sc.prepare) throw new Error(`${file}: prepare() is not allowed in a dry-run scenario (the runner signs in)`);
  return { id: sc.id, app: sc.app, identity, title: sc.title || '', file, steps: sc.steps.length, readOnly: !!sc.readOnly };
}

const matches = (e, opts) => (!opts.only || !opts.only.length || opts.only.includes(e.id))
  && (!opts.apps || !opts.apps.length || opts.apps.includes(e.app))
  && (!opts.identities || !opts.identities.length || opts.identities.includes(e.identity));

/**
 * The entries the options select, in manifest order. Unknown --only ids throw (a typo must not pass as "0 run").
 * Scenarios of a WRITABLE identity are left out unless opts.includeWritable; naming one explicitly (--only its id or
 * --identity crm) without the flag throws, so it is never skipped silently.
 */
function select(entries, opts) {
  const ids = new Set(entries.map((e) => e.id));
  const dup = entries.find((e, i) => entries.findIndex((x) => x.id === e.id) !== i);
  if (dup) throw new Error(`duplicate scenario id ${dup.id}`);
  for (const id of opts.only || []) if (!ids.has(id)) throw new Error(`no scenario ${id} in the manifest`);
  if (!opts.includeWritable) {
    const named = [...(opts.identities || []).filter((x) => WRITABLE_IDENTITIES.includes(x)),
      ...entries.filter((e) => (opts.only || []).includes(e.id) && WRITABLE_IDENTITIES.includes(e.identity)).map((e) => e.id)];
    if (named.length) {
      throw new Error(`${named.join(', ')}: signs in an account that can write (no read-only role); add --include-writable to run it`);
    }
  }
  return entries.filter((e) => matches(e, opts) && (opts.includeWritable || !WRITABLE_IDENTITIES.includes(e.identity)));
}

/** Ids the options would select but leave out because their identity can write (said in the report). */
function skippedWritable(entries, opts) {
  if (opts.includeWritable) return [];
  return entries.filter((e) => matches(e, opts) && WRITABLE_IDENTITIES.includes(e.identity)).map((e) => e.id);
}

/** The identities to sign in for the selected entries (public needs none), in SIGNIN_ORDER. */
function signinPlan(entries) {
  const need = new Set(entries.map((e) => e.identity));
  return SIGNIN_ORDER.filter((x) => x !== 'public' && need.has(x));
}

// Link tokens and long opaque values never reach the report (record.cjs uses this same function). The report may be
// copied to the public root repo: AWS ARNs and 12-digit account numbers (an AccessDenied message names both, a bucket
// name may end in one) are masked too.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
function redact(x) {
  if (x == null) return x;
  return String(x)
    .replace(/arn:aws[a-z-]*:[^\s"'`,;)]*/g, '<arn>')
    // A uuid's last group can be 12 digits: the uuid alternative matches first and is kept whole.
    .replace(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|(?<![0-9A-Za-z])\d{12}(?![0-9A-Za-z])/gi,
      (m) => (m.length === 36 ? m : '<account>'))
    .replace(/([/=])([A-Za-z0-9_.~%-]{30,})/g, (m, lead, seg) => (UUID.test(seg) ? m : `${lead}<redacted>`));
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
function outcome(entry, { result = null, timeline = null, exitCode = null, blocked = null, ms = null } = {}) {
  const base = { id: entry.id, app: entry.app, identity: entry.identity, title: entry.title, steps_total: entry.steps };
  if (blocked) {
    return { ...base, verdict: 'BLOCKED', reason: cell(blocked), steps_passed: 0, ms: 0,
      steps: Array.from({ length: entry.steps }, (_, i) => ({ n: i + 1, status: 'NOT RUN', error: '' })) };
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

/** Exit code of the run: 0 every scenario PASS, 2 otherwise (FAIL, BLOCKED or CRASH). */
function exitCode(outcomes) {
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
  L.push('No writes (non-GET requests are aborted and listed), no LLM or paid calls, Dev only. Cost $0.');
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
  IDENTITIES, WRITABLE_IDENTITIES, SIGNIN_ORDER, PAID_URLS, parseArgs, describe, select, skippedWritable, signinPlan, redact, cell, outcome, shaTable, counts, exitCode,
  renderMarkdown, renderTsv, stamp,
};
