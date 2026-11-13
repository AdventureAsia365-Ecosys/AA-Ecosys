// Pilot guard of the UAT recorder (AA-855, root ADR 0019 d16; plan docs/audits/2026-11-05-S268-video-plan "Chặn tenant
// pilot"): before any signed-in scenario starts its browser, read the tenant or agency the session is on through the
// app's own API, and continue only when it is a synthetic one. Fail closed: an unknown tenant, a missing field, an
// answer that is not 200, or any pilot / real marker stops the run with exit 5 (pilot_guard) and no video is started.
//
//   const guard = require('./pilot-guard.cjs');
//   const v = await guard.check(browser, storageStateFile, guard.scopesFor(sc, storageState));   // { ok, reason, ... }
//   node tools/uat/lib/pilot-guard.cjs studio|studio-editor|studio-audit|studio-rehearsal|crm|crm-rehearsal|crm-rehearsal-agent
//                                                                  read the saved session's tenant, ok / refused
//
// Where the active tenant is read (AA-Partner web, one agency host since AA-1036):
//   content  GET /api/tenant/me  -> { tenant_id, tenant_name, ... }   the Content studio session (web/app/api/tenant/me)
//   crm      GET /bff/me         -> { tenant_id, display_name, ... }  the CRM API /crm/v1/me through the BFF allow-list
// Neither answer carries is_pilot today; the rule still reads it (and kind, is_synthetic, pilot_ends_at) so a later API
// field tightens the guard without a change here. The allow-list is what keeps the pilot out today.
//
// Allow-list (synthetic tenants only, all invented):
//   built in   the four E2E Content tenants and the four audit tenants (AA-855 write scenarios) by their invented
//              display name; the three CRM review agencies and the pilot rehearsal agency by id only
//              (a UUIDv5 of their key, AA-Partner api/app/seed/catalogue.py, public there): their slugs are pinned to
//              those ids, so an agency that merely renames itself "Lữ hành Sen Vàng" is refused.
//   by scope   the CRM scope never matches by name: an agency sets its own display_name. A Content tenant checked in the
//              CRM scope (it holds the CRM add-on) must be pinned by id in the local file below.
//   local      work/uat-allowlist.json (gitignored; env UAT_ALLOWLIST names another file): ids that must not be public,
//              { "content": { "<tenant uuid>": "atlas-hearth" }, "crm": { "<uuid>": "sen-vang" }, "builtin": true }.
//              An id pinned for a slug makes that slug match by id only. "builtin": false turns the built-in names and
//              ids off (the negative check: every tenant is then refused).
// A refusal names the tenant by the first 8 characters of its id, never by its name (the pilot's name is real data).
'use strict';
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const EXIT_PILOT_GUARD = 5;
const CODE = 'pilot_guard';
const PARTNER = (process.env.UAT_CRM_PARTNER || 'https://portal.lumiguides.it.com').replace(/\/+$/, '');
const ALLOWLIST_FILE = process.env.UAT_ALLOWLIST || path.join(__dirname, '..', 'work', 'uat-allowlist.json');

// AA-Partner api/app/seed/catalogue.py SYNTHETIC_NAMESPACE: agency_id(key) = uuid5(ns, "aa-crm-synthetic-agency:<key>").
const CRM_NAMESPACE = '6f1d3c2e-9a7b-5c4d-8e2f-a935c0de0007';

/** RFC 4122 UUIDv5 (SHA-1) of `name` in `namespace`, lower case. */
function uuid5(namespace, name) {
  const ns = Buffer.from(namespace.replace(/-/g, ''), 'hex');
  const h = crypto.createHash('sha1').update(Buffer.concat([ns, Buffer.from(name, 'utf8')])).digest();
  h[6] = (h[6] & 0x0f) | 0x50;
  h[8] = (h[8] & 0x3f) | 0x80;
  const x = h.subarray(0, 16).toString('hex');
  return `${x.slice(0, 8)}-${x.slice(8, 12)}-${x.slice(12, 16)}-${x.slice(16, 20)}-${x.slice(20, 32)}`;
}

// The synthetic tenants, all invented (CIS migration 018 slugs; AA-Partner seed catalogue). A CIS tenant that also holds
// the CRM add-on is the same tenant in the CRM, so both scopes accept every entry; `only` narrows a check to some slugs.
const SYNTHETIC = [
  { slug: 'atlas-hearth', name: 'Atlas & Hearth' },
  { slug: 'terra-family', name: 'Terra Family Expeditions', aliases: ['terra-family-expeditions'] },
  { slug: 'trail-pulse', name: 'Trail Pulse' },
  { slug: 'wildkind-travel', name: 'WildKind Travel' },
  { slug: 'sen-vang', name: 'Lữ hành Sen Vàng', crmSlug: 'sen-vang' },
  { slug: 'southern-cross', name: 'Southern Cross Journeys', crmSlug: 'southern-cross' },
  { slug: 'harbour-lights', name: 'Harbour Lights Travel Co.', crmSlug: 'harbour-lights' },
  // AA-855 write scenarios (W-01..W-04): the four synthetic audit tenants of the T-series audit (kind demo, invented
  // brands). Only the studio-audit identity writes there, and always on exactly one of them (lib/studio-audit.cjs).
  { slug: 'audit-atlas-hearth', name: 'Atlas & Hearth (Audit)' },
  { slug: 'audit-terra-family', name: 'Terra Family Expeditions (Audit)' },
  { slug: 'audit-trail-pulse', name: 'Trail Pulse (Audit)' },
  { slug: 'audit-wildkind-travel', name: 'WildKind Travel (Audit)' },
  // The synthetic pilot rehearsal agency (root docs/ops/runbooks/pilot-rehearsal.md, Fixtures): kind demo, is_canary
  // true, invented name. Its CIS tenant id is the CRM seed's id for the key (public in the runbook), so both scopes
  // match it by id only; the marker tenant of steps 1b / 12b is the pilot and is never on this list.
  { slug: 'pilot-rehearsal-01', name: 'E2E Pilot Rehearsal Travel', crmSlug: 'pilot-rehearsal-01' },
];
const SCOPES = {
  // nameMatch: whether an unpinned invented display name is enough. Content: yes (the studio session returns no slug and
  // the ids stay private); CRM: no (the agency edits display_name, and the review agencies have public ids).
  content: { path: '/api/tenant/me', nameField: 'tenant_name', what: 'Content studio tenant', nameMatch: true },
  crm: { path: '/bff/me', nameField: 'display_name', what: 'CRM agency', nameMatch: false },
};
// Identities whose session has no tenant (AA staff): their list pages are masked per scenario (allowRows), not here.
// The Booking E2E writers (A10e: staff, finance maker, finance checker) are AA staff too: their writes are held to
// synthetic agencies by Booking itself, and each write scenario checks its record's agency before the first write.
// crm-staff (root ADR 0006a A10c): the AA staff console's E2E user; the CRM itself keeps it to synthetic agencies.
const STAFF_IDENTITIES = ['cis-admin', 'booking', 'booking-staff', 'booking-maker', 'booking-checker', 'crm-staff'];
// The pilot rehearsal's owner and agent: the studio owner (studio-rehearsal) and the CRM owner / agent (lib/crm-signin.cjs
// RO / RA) are pinned to the rehearsal agency, whatever the scenario says (they write and may pay).
const REHEARSAL_SLUG = 'pilot-rehearsal-01';
const REHEARSAL_AGENCY = REHEARSAL_SLUG;
const REHEARSAL_IDENTITIES = ['crm-rehearsal', 'crm-rehearsal-agent'];
const IDENTITY_SCOPES = { studio: ['content'], 'studio-editor': ['content'], 'studio-audit': ['content'], 'studio-rehearsal': ['content'], crm: ['crm'],
  'crm-rehearsal': ['crm'], 'crm-rehearsal-agent': ['crm'] };
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const norm = (s) => String(s).normalize('NFC').trim();
const slugOf = (s) => {
  const e = SYNTHETIC.find((x) => x.slug === s || (x.aliases || []).includes(s));
  return e ? e.slug : s;
};
const shortId = (id) => (typeof id === 'string' && id ? `${id.slice(0, 8)}…` : 'unknown');

/**
 * The allow-list: { ids: Map<id, slug>, pinned: Map<slug, Set<id>>, names: Map<name, slug>, builtin }. `local` is the
 * parsed work/uat-allowlist.json (or null). Throws on a malformed file (fail closed: a typo must not widen the list).
 */
function buildAllowlist(local = null) {
  if (local !== null && (typeof local !== 'object' || Array.isArray(local))) throw new Error('allow-list file: not a JSON object');
  const builtin = !local || local.builtin !== false;
  const ids = new Map();
  const pinned = new Map();
  const names = new Map();
  if (builtin) {
    for (const e of SYNTHETIC) {
      names.set(norm(e.name), e.slug);
      if (e.crmSlug) {
        // A built-in agency id pins its slug: that slug then matches by id only, never by its (agency-set) name.
        const id = uuid5(CRM_NAMESPACE, `aa-crm-synthetic-agency:${e.crmSlug}`);
        ids.set(id, e.slug);
        pinned.set(e.slug, new Set([id]));
      }
    }
  }
  for (const scope of ['content', 'crm']) {
    const m = local && local[scope];
    if (m === undefined || m === null) continue;
    if (typeof m !== 'object' || Array.isArray(m)) throw new Error(`allow-list file: "${scope}" must map tenant ids to slugs`);
    for (const [id, slug] of Object.entries(m)) {
      if (!UUID.test(id)) throw new Error(`allow-list file: "${scope}" has a key that is not a tenant id`);
      if (typeof slug !== 'string' || !slug) throw new Error(`allow-list file: "${scope}" id ${shortId(id)} has no slug`);
      const s = slugOf(slug);
      ids.set(id.toLowerCase(), s);
      if (!pinned.has(s)) pinned.set(s, new Set());
      pinned.get(s).add(id.toLowerCase());
    }
  }
  return { ids, pinned, names, builtin };
}

/** The local allow-list file parsed (null when there is none). A file that is not JSON throws (fail closed). */
function loadLocal(file = ALLOWLIST_FILE) {
  let raw;
  try {
    raw = fs.readFileSync(file, 'utf8');
  } catch (e) {
    if (e.code === 'ENOENT') return null;
    throw e;
  }
  try {
    return JSON.parse(raw);
  } catch {
    throw new Error(`allow-list file ${path.basename(file)} is not JSON`);
  }
}

const refuse = (reason, extra = {}) => ({ ok: false, code: CODE, reason: `${CODE}: ${reason}`, ...extra });

/**
 * Decide on one API answer. `answer` = the parsed JSON body of the scope's "me" call; `allow` = buildAllowlist();
 * `only` = slugs this check accepts (default: every synthetic tenant). Returns { ok, slug, matched_by } or
 * { ok: false, code: 'pilot_guard', reason }. Pure: no I/O.
 */
function evaluate(answer, { scope, allow, only = null } = {}) {
  const sc = SCOPES[scope];
  if (!sc) return refuse(`unknown scope ${scope}`);
  if (!allow) return refuse('no allow-list');
  if (!answer || typeof answer !== 'object' || Array.isArray(answer)) return refuse(`the ${sc.what} answer is not an object`);
  const id = answer.tenant_id;
  if (typeof id !== 'string' || !UUID.test(id)) return refuse(`the ${sc.what} answer has no tenant id`);
  const who = shortId(id);
  // (b) markers: any pilot / real marker the API returns refuses, whatever the allow-list says.
  if ('is_pilot' in answer && answer.is_pilot !== false) {
    return refuse(answer.is_pilot === true ? `${sc.what} ${who} is the pilot (is_pilot=true)` : `${sc.what} ${who}: is_pilot is not false`);
  }
  if (answer.pilot_ends_at != null) return refuse(`${sc.what} ${who} has a pilot end date`);
  if ('is_synthetic' in answer && answer.is_synthetic !== true) return refuse(`${sc.what} ${who} is not synthetic`);
  if ('kind' in answer && ['pilot', 'real'].includes(String(answer.kind).toLowerCase())) {
    return refuse(`${sc.what} ${who} is of kind ${String(answer.kind).toLowerCase()}`);
  }
  // (a) the allow-list: by id first, else (Content scope only) by the invented display name, unless that slug is
  // pinned to other ids. The CRM scope is id only: an agency sets its own display_name.
  let slug = allow.ids.get(id.toLowerCase()) || null;
  let matchedBy = 'id';
  if (!slug && !sc.nameMatch) return refuse(`${sc.what} ${who} is not in the synthetic allow-list (this scope matches by id only)`);
  if (!slug) {
    const name = answer[sc.nameField];
    if (typeof name !== 'string' || !name.trim()) return refuse(`${sc.what} ${who} is not in the synthetic allow-list (no name in the answer)`);
    const byName = allow.names.get(norm(name)) || null;
    if (!byName) return refuse(`${sc.what} ${who} is not in the synthetic allow-list`);
    if (allow.pinned.has(byName)) return refuse(`${sc.what} ${who} carries the name of ${byName}, but not its pinned id`);
    slug = byName;
    matchedBy = 'name';
  }
  if (only && !only.map(slugOf).includes(slug)) return refuse(`${sc.what} ${who} is ${slug}; this step runs only on ${only.join(', ')}`);
  return { ok: true, scope, slug, matched_by: matchedBy, tenant: who };
}

/**
 * The guard scopes of a scenario: scenario.pilotGuard ({ scopes, only } or a list of scopes) wins; else by identity
 * (studio, studio-editor -> content; crm -> crm; AA staff -> none); else a CRM-app scenario with a session -> crm.
 * Returns { scopes, only }. Throws (fail closed) for a signed-in scenario whose scope cannot be told.
 */
function scopesFor(sc, storageState) {
  // A scenario's own pilotGuard never widens the studio-audit pin (checked first).
  if (sc.identity === 'studio-audit' && sc.pilotGuard) throw new Error(`${CODE}: ${sc.id}: a studio-audit scenario takes the run's audit tenant, not its own pilotGuard`);
  if (sc.identity === 'studio-rehearsal' && sc.pilotGuard) throw new Error(`${CODE}: ${sc.id}: a studio-rehearsal scenario runs on ${REHEARSAL_SLUG} only, not its own pilotGuard`);
  if (REHEARSAL_IDENTITIES.includes(sc.identity) && sc.pilotGuard) throw new Error(`${CODE}: ${sc.id}: a rehearsal scenario runs on ${REHEARSAL_AGENCY} only, not its own pilotGuard`);
  const pg = sc.pilotGuard;
  if (pg) {
    const scopes = Array.isArray(pg) ? pg : pg.scopes;
    if (!Array.isArray(scopes) || !scopes.length || scopes.some((s) => !SCOPES[s])) throw new Error(`${CODE}: ${sc.id}: pilotGuard needs scopes from ${Object.keys(SCOPES).join(', ')}`);
    return { scopes, only: Array.isArray(pg) ? null : pg.only || null };
  }
  const identity = sc.identity || 'public';
  // The audit editor writes and may pay: it is pinned to the ONE audit tenant of this run, whatever the scenario says.
  if (identity === 'studio-audit') return { scopes: IDENTITY_SCOPES[identity], only: [require('./studio-audit.cjs').auditTenant().slug] };
  // The rehearsal owner (AA-1086) writes and pays on the synthetic rehearsal agency only.
  if (identity === 'studio-rehearsal') return { scopes: IDENTITY_SCOPES[identity], only: [REHEARSAL_SLUG] };
  if (REHEARSAL_IDENTITIES.includes(identity)) return { scopes: IDENTITY_SCOPES[identity], only: [REHEARSAL_AGENCY] };
  if (IDENTITY_SCOPES[identity]) return { scopes: IDENTITY_SCOPES[identity], only: null };
  if (STAFF_IDENTITIES.includes(identity)) return { scopes: [], only: null };
  if (!storageState) return { scopes: [], only: null };
  if (sc.app === 'crm') return { scopes: ['crm'], only: null };
  throw new Error(`${CODE}: ${sc.id} is signed in but names no identity or pilotGuard scope`);
}

/** GET the scope's "me" through a context's request API (its cookies); one renewal through /auth/refresh on a 401. */
async function readActive(request, scope, origin = PARTNER) {
  const sc = SCOPES[scope];
  const get = () => request.get(`${origin}${sc.path}`, { headers: { Accept: 'application/json' }, timeout: 20_000, maxRedirects: 0 });
  let res = await get();
  if (res.status() === 401 && scope === 'crm') {
    await request.get(`${origin}/auth/refresh?next=${encodeURIComponent('/home')}`, { timeout: 20_000 }).catch(() => {});
    res = await get();
  }
  let body = null;
  try { body = await res.json(); } catch { /* not JSON: refused below */ }
  return { status: res.status(), body };
}

/**
 * Check every scope with a NEW, unrecorded context of `browser` on `storageState`; closed before returning.
 * Returns { ok: true, checked: [...] } or the first refusal. Never throws for an answer (fail closed = a refusal).
 */
async function check(browser, storageState, { scopes, only = null }, { origin = PARTNER, local } = {}) {
  if (!scopes.length) return { ok: true, checked: [] };
  if (!storageState) return refuse('a guarded scenario has no signed-in session');
  let allow;
  try {
    allow = buildAllowlist(local === undefined ? loadLocal() : local);
  } catch (e) {
    return refuse(String(e.message || e));
  }
  const context = await browser.newContext({ storageState });
  try {
    const checked = [];
    for (const scope of scopes) {
      let r;
      try {
        r = await readActive(context.request, scope, origin);
      } catch (e) {
        return refuse(`could not read the ${SCOPES[scope].what} (${String(e.message || e).split('\n')[0].slice(0, 80)})`);
      }
      if (r.status !== 200) return refuse(`could not read the ${SCOPES[scope].what} (HTTP ${r.status})`);
      const v = evaluate(r.body, { scope, allow, only });
      if (!v.ok) return v;
      checked.push(v);
    }
    return { ok: true, checked };
  } finally {
    await context.close().catch(() => {});
  }
}

/** check() with its own headless Chromium (the dry-run runner, once per identity). */
async function checkState(storageState, guardScopes, opts) {
  const { chromium } = require('@playwright/test');
  const browser = await chromium.launch({ headless: true });
  try {
    return await check(browser, storageState, guardScopes, opts);
  } finally {
    await browser.close();
  }
}

/** One line for logs and reports: "ok: content atlas-hearth (id)" or the refusal reason. */
function describeVerdict(v) {
  if (!v.ok) return v.reason;
  if (!v.checked || !v.checked.length) return 'ok: no tenant scope';
  return `ok: ${v.checked.map((c) => `${c.scope} ${c.slug} (by ${c.matched_by})`).join(', ')}`;
}

// The row filter of AA staff list pages that show tenants (record.cjs scenario.allowRows): the invented names and
// slugs of every synthetic tenant, as regex sources (escaped).
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
function syntheticRowPatterns() {
  return SYNTHETIC.flatMap((e) => [e.name, e.slug, ...(e.aliases || [])]).map((s) => esc(norm(s)));
}

module.exports = {
  EXIT_PILOT_GUARD, CODE, SYNTHETIC, REHEARSAL_SLUG, SCOPES, STAFF_IDENTITIES, REHEARSAL_AGENCY, REHEARSAL_IDENTITIES, CRM_NAMESPACE, ALLOWLIST_FILE,
  uuid5, buildAllowlist, loadLocal, evaluate, scopesFor, readActive, check, checkState, describeVerdict, syntheticRowPatterns,
};

if (require.main === module) {
  (async () => {
    const who = process.argv[2];
    if (!IDENTITY_SCOPES[who]) throw new Error(`usage: node tools/uat/lib/pilot-guard.cjs ${Object.keys(IDENTITY_SCOPES).join('|')}`);
    const { ensureState } = require('./signin.cjs');
    const { file } = await ensureState(who);
    const v = await checkState(file, scopesFor({ id: who, identity: who }, file));
    console.log(`${who}: ${describeVerdict(v)}`);
    process.exitCode = v.ok ? 0 : EXIT_PILOT_GUARD;
  })().catch((e) => { console.error(String(e.message || e).split('\n')[0]); process.exitCode = 1; });
}
