// UAT dry run (AA-1009, skill aa-uat-video §3): every read-only scenario of scenarios/dryrun.cjs in fast mode (asserts
// only: no video, no TTS), each identity signed in ONCE outside the scenarios (lib/signin.cjs), one result table with
// pass / fail per step and the git SHA of every app at the start and the end. Dev only, $0: every non-GET request is
// aborted (UAT_READ_ONLY=1) and the paid model paths are blocked (UAT_BLOCK_URLS), no LLM, no paid API.
//
//   node tools/uat/dryrun.cjs                         the whole set
//   node tools/uat/dryrun.cjs --list                  the set: id, app, identity, steps, file
//   node tools/uat/dryrun.cjs --only BK-05,CIS-08     just these ids (also --app booking,crm / --identity public)
//   node tools/uat/dryrun.cjs --stop-on-fail          stop at the first scenario that does not PASS
//   node tools/uat/dryrun.cjs --record TP-02          record mode for one scenario: sign its identity in, then run.sh
//                                                     (captions -> local TTS -> take -> build -> sync check)
//   --out <dir> (default work/dryrun/<UTC stamp>/)    --skip-egress-check (only for a run that opens no Vercel host)
//   --include-writable                                also run the scenarios whose identity CAN write (crm: the CRM
//                                                     has no read-only role; only the browser guard keeps them
//                                                     read-only). Left out by default and named in the report.
// Write set (AA-855, scenarios/write-set.cjs): scenarios that write on a synthetic tenant and may call a paid model.
// Never in the whole set; only by id. A paid one runs or records only with --allow-paid (implies --include-writable):
//   node tools/uat/dryrun.cjs --record W-01 --allow-paid        record one (the env UAT_STUDIO_TENANT picks the audit
//                                                               tenant of studio-audit, default audit-atlas-hearth)
//   node tools/uat/dryrun.cjs --only W-01,W-02 --preview        their read-only part only (steps before the first
//                                                               write; every write aborted), $0
// Output: <out>/results.md (the table to copy to docs/audits/<date>-S<nnn>-uat-dry-run/), results.json, results.tsv.
// Before: bash tools/uat/setup.sh once; egress VN (VPN off; Vercel challenges VPN IPs); for cis-admin / booking a fresh
// MFA session of the admin profile (the code mail is read from the e2e mailbox), aws sts get-caller-identity.
// RAM guard before each Chromium: >= 2500 MB available, waits 2 min up to 5 times.
// Pilot guard (AA-855, lib/pilot-guard.cjs): after each identity signs in, its tenant / agency is read through the app's
// own API; a tenant outside the synthetic allow-list (or any pilot marker) blocks every scenario of that identity, and
// record.cjs checks again before each scenario. Fail closed.
// Exit: 0 all PASS | 2 a scenario FAILed, was BLOCKED (its identity could not sign in) or crashed | 3 egress not VN |
// 4 RAM too low | 5 pilot_guard refused a session (no scenario of it ran) | 1 usage / runner error.
'use strict';
const { execFileSync, spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const core = require('./lib/dryrun-core.cjs');
const pilotGuard = require('./lib/pilot-guard.cjs');

const HERE = __dirname;
const MANIFEST = path.join(HERE, 'scenarios', 'dryrun.cjs');
const WRITE_SET = path.join(HERE, 'scenarios', 'write-set.cjs');
const PARTNER = (process.env.UAT_CRM_PARTNER || 'https://portal.lumiguides.it.com').replace(/\/+$/, '');
const TRIPPLANNER = (process.env.UAT_TRIPPLANNER || 'https://tripplanner.lumiguides.it.com').replace(/\/+$/, '');
const ORG = 'https://github.com/AdventureAsia365-Ecosys';
// Where each app says which commit it runs. The two Vercel staff frontends expose no version: the head of the repo's
// main stands in for them (both deploy from main), marked as such in the table.
const VERSIONS = [
  { app: 'cis-api', url: 'https://api-cis.lumiguides.it.com/health', field: 'git_sha' },
  { app: 'cis-admin (Vercel)', repo: `${ORG}/AA-CIS-App.git` },
  { app: 'booking-api', url: 'https://api-booking.lumiguides.it.com/booking/health', field: 'git_sha' },
  { app: 'booking-admin (Vercel)', repo: `${ORG}/AA-Booking.git` },
  { app: 'crm-api', url: `${PARTNER}/crm/health`, field: 'git_sha' },
  { app: 'crm-web', url: `${PARTNER}/healthz`, field: 'git_sha' },
  { app: 'content-studio', url: `${PARTNER}/api/healthz`, field: 'sha' },
  { app: 'tripplanner', url: `${TRIPPLANNER}/api/health`, field: 'git_sha' },
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function loadEntries() {
  const load = (manifest, describe) => require(manifest).map((rel) => {
    const abs = path.resolve(path.dirname(manifest), rel);
    return { ...describe(require(abs), rel), abs };
  });
  return [...load(MANIFEST, core.describe), ...load(WRITE_SET, core.describeWrite)];
}

function egress() {
  try {
    return execFileSync('curl', ['-s', '--max-time', '10', 'https://ipinfo.io/country'], { encoding: 'utf8' }).trim();
  } catch {
    return '';
  }
}

function availableMb() {
  const m = /MemAvailable:\s+(\d+) kB/.exec(fs.readFileSync('/proc/meminfo', 'utf8'));
  return m ? Math.floor(Number(m[1]) / 1024) : Infinity;
}

async function ramGuard() {
  for (let i = 0; i <= 5; i++) {
    const a = availableMb();
    if (a >= 2500) return;
    if (i === 5) break;
    console.log(`RAM low (${a} MB available), waiting 2 min`);
    await sleep(120_000);
  }
  console.error('RAM too low');
  process.exit(4);
}

async function readVersions() {
  const out = {};
  for (const v of VERSIONS) {
    try {
      if (v.repo) {
        const line = execFileSync('git', ['ls-remote', v.repo, 'refs/heads/main'], { encoding: 'utf8', timeout: 20_000 });
        out[v.app] = { sha: line.split(/\s/)[0] || null, source: 'repo main head (no version endpoint)' };
      } else {
        const res = await fetch(v.url, { signal: AbortSignal.timeout(15_000), headers: { Accept: 'application/json' } });
        const body = await res.json();
        out[v.app] = { sha: body[v.field] || null, source: new URL(v.url).pathname };
      }
    } catch (e) {
      out[v.app] = { sha: null, source: v.repo ? 'repo main head' : new URL(v.url).pathname, error: String(e.message || e).split('\n')[0] };
    }
  }
  return out;
}

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    return null;
  }
}

function childEnv(state, { paid = false, preview = false } = {}) {
  // A paid write-set run (--allow-paid) may reach the paid paths its own scenario needs (the pilot rehearsal's planner
  // search); the scenario's own blockUrls and limitWrites still keep the rest out.
  const env = { ...process.env, UAT_READ_ONLY: '1', UAT_BLOCK_URLS: JSON.stringify(paid ? [] : core.PAID_URLS) };
  delete env.UAT_STORAGE_STATE;
  delete env.UAT_BASE_URL; // one base URL for every app would send each scenario to the wrong host
  delete env.UAT_ALLOW_PAID; // only an explicit --allow-paid on a paid write-set scenario sets it
  delete env.UAT_PREVIEW;
  if (state) env.UAT_STORAGE_STATE = state;
  if (paid) env.UAT_ALLOW_PAID = '1';
  if (preview) env.UAT_PREVIEW = '1';
  return env;
}

/** The child env of one entry: the write set's paid ones get UAT_ALLOW_PAID only with --allow-paid. */
const envFor = (e, state, opts) => childEnv(state, { paid: !!(e.writeSet && e.paid && opts.allowPaid), preview: !!(e.writeSet && opts.preview) });

async function signIn(who) {
  const { ensureState } = require('./lib/signin.cjs');
  return ensureState(who);
}

async function record(entries, id, opts) {
  const [e] = core.select(entries, { only: [id], includeWritable: opts.includeWritable, allowPaid: opts.allowPaid });
  let state = null;
  if (!core.NO_SIGNIN.includes(e.identity)) {
    await ramGuard();
    state = (await signIn(e.identity)).file;
  }
  if (e.writeSet) console.log(`record ${e.id}: write-set scenario${e.paid ? ', PAID (--allow-paid)' : ''}`);
  const r = spawnSync('bash', [path.join(HERE, 'run.sh'), e.abs], { stdio: 'inherit', env: envFor(e, state, opts) });
  return r.status == null ? 1 : r.status;
}

async function main() {
  const opts = core.parseArgs(process.argv.slice(2));
  const entries = loadEntries();
  core.select(entries, { only: [] }); // duplicate ids fail even for --list
  if (opts.list) {
    for (const e of entries) {
      const note = e.writeSet ? (e.paid ? `write set, PAID: only by id with --allow-paid (preview: ${e.preview} step(s))` : 'write set: only by id')
        : core.WRITABLE_IDENTITIES.includes(e.identity) ? 'only with --include-writable' : '';
      console.log([e.id, e.app, e.identity, `${e.steps} steps`, e.file, note].filter(Boolean).join('\t'));
    }
    return 0;
  }
  if (!fs.existsSync(path.join(HERE, 'node_modules', '@playwright', 'test'))) {
    console.error('STOP: run bash tools/uat/setup.sh first');
    return 1;
  }
  const country = opts.skipEgress ? 'not checked' : egress();
  if (!opts.skipEgress && country !== 'VN') {
    console.error(`STOP: public IP country is '${country}', not VN (Vercel blocks VPN IPs). Turn the VPN off.`);
    return 3;
  }
  if (opts.record) return record(entries, opts.record, opts);

  // A preview counts only the read-only part of each write-set scenario (the steps before its first write).
  const sel = core.select(entries, opts).map((e) => (opts.preview ? { ...e, steps: e.preview } : e));
  const skipped = core.skippedWritable(entries, opts);
  if (skipped.length) console.log(`not run (identity can write, add --include-writable): ${skipped.join(', ')}`);
  if (!sel.length) throw new Error('no scenario matches the options');
  const startedAt = new Date().toISOString();
  const out = path.resolve(opts.out || path.join(HERE, 'work', 'dryrun', core.stamp(new Date(startedAt))));
  fs.mkdirSync(out, { recursive: true });
  console.log(`dry run: ${sel.length} scenario(s), out ${out}`);
  const before = await readVersions();

  const states = {};
  const signins = {};
  const refused = {};
  for (const who of core.signinPlan(sel)) {
    await ramGuard();
    try {
      const r = await signIn(who);
      signins[who] = r.reused ? 'saved session still valid' : 'signed in';
      const v = await pilotGuard.checkState(r.file, pilotGuard.scopesFor({ id: who, identity: who }, r.file));
      if (v.ok) {
        states[who] = r.file;
        signins[who] += `; ${pilotGuard.describeVerdict(v)}`;
      } else {
        refused[who] = true;
        signins[who] = `BLOCKED: ${core.cell(v.reason, 200)}`;
      }
    } catch (e) {
      signins[who] = `BLOCKED: ${core.cell(String(e.message || e).split('\n')[0], 200)}`;
    }
    console.log(`signin ${who}: ${signins[who]}`);
  }

  const outcomes = [];
  for (const e of sel) {
    let o;
    if (!core.NO_SIGNIN.includes(e.identity) && !states[e.identity]) {
      o = core.outcome(e, { blocked: signins[e.identity] || 'not signed in', pilotGuard: !!refused[e.identity] });
    } else {
      await ramGuard();
      const work = path.join(HERE, 'work', e.id);
      for (const f of ['result.json', 'timeline.json']) fs.rmSync(path.join(work, f), { force: true });
      console.log(`=== ${e.id} (${e.app}, ${e.identity})`);
      const t0 = Date.now();
      // A paid write-set scenario waits for the writer (a tour rewrite or an article: up to ~20 min).
      const r = spawnSync(process.execPath, [path.join(HERE, 'record.cjs'), e.abs, '--fast'],
        { stdio: 'inherit', env: envFor(e, states[e.identity] || null, opts), timeout: e.writeSet && !opts.preview ? 2_400_000 : 600_000 });
      o = core.outcome(e, { result: readJson(path.join(work, 'result.json')), timeline: readJson(path.join(work, 'timeline.json')),
        exitCode: r.status == null ? (r.signal || 'timeout') : r.status, ms: Date.now() - t0 });
    }
    outcomes.push(o);
    console.log(`--> ${o.id} ${o.verdict} ${o.steps_passed}/${o.steps_total}${o.reason ? ` (${o.reason})` : ''}`);
    if (!opts.keepGoing && o.verdict !== 'PASS') break;
  }

  const after = await readVersions();
  const run = { startedAt, finishedAt: new Date().toISOString(), egress: country, signins, shas: core.shaTable(before, after),
    skipped, outcomes, paid: opts.allowPaid ? sel.filter((e) => e.writeSet && e.paid).map((e) => e.id) : [], preview: opts.preview };
  fs.writeFileSync(path.join(out, 'results.json'), `${JSON.stringify(run, null, 2)}\n`);
  fs.writeFileSync(path.join(out, 'results.md'), core.renderMarkdown(run));
  fs.writeFileSync(path.join(out, 'results.tsv'), core.renderTsv(outcomes));
  const c = core.counts(outcomes);
  console.log(`--- ${c.PASS} PASS, ${c.FAIL} FAIL, ${c.BLOCKED} BLOCKED, ${c.CRASH} CRASH -> ${path.join(out, 'results.md')}`);
  return core.exitCode(outcomes);
}

main().then((rc) => { process.exitCode = rc; }).catch((e) => {
  console.error(core.redact(String(e.message || e).split('\n')[0]));
  process.exitCode = 1;
});
