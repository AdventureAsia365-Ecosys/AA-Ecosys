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
// Output: <out>/results.md (the table to copy to docs/audits/<date>-S<nnn>-uat-dry-run/), results.json, results.tsv.
// Before: bash tools/uat/setup.sh once; egress VN (VPN off; Vercel challenges VPN IPs); for cis-admin / booking a fresh
// MFA session of the admin profile (the code mail is read from the e2e mailbox), aws sts get-caller-identity.
// RAM guard before each Chromium: >= 2500 MB available, waits 2 min up to 5 times.
// Exit: 0 all PASS | 2 a scenario FAILed, was BLOCKED (its identity could not sign in) or crashed | 3 egress not VN |
// 4 RAM too low | 1 usage / runner error.
'use strict';
const { execFileSync, spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const core = require('./lib/dryrun-core.cjs');

const HERE = __dirname;
const MANIFEST = path.join(HERE, 'scenarios', 'dryrun.cjs');
const PARTNER = (process.env.UAT_CRM_PARTNER || 'https://portal.lumiguides.it.com').replace(/\/+$/, '');
const TRIPPLANNER = (process.env.UAT_TRIPPLANNER || 'https://aa-tripplanner.vercel.app').replace(/\/+$/, '');
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
  const files = require(MANIFEST);
  return files.map((rel) => {
    const abs = path.resolve(path.dirname(MANIFEST), rel);
    return { ...core.describe(require(abs), rel), abs };
  });
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

function childEnv(state) {
  const env = { ...process.env, UAT_READ_ONLY: '1', UAT_BLOCK_URLS: JSON.stringify(core.PAID_URLS) };
  delete env.UAT_STORAGE_STATE;
  delete env.UAT_BASE_URL; // one base URL for every app would send each scenario to the wrong host
  if (state) env.UAT_STORAGE_STATE = state;
  return env;
}

async function signIn(who) {
  const { ensureState } = require('./lib/signin.cjs');
  return ensureState(who);
}

async function record(entries, id) {
  const e = entries.find((x) => x.id === id);
  if (!e) throw new Error(`no scenario ${id} in the manifest`);
  let state = null;
  if (e.identity !== 'public') {
    await ramGuard();
    state = (await signIn(e.identity)).file;
  }
  const r = spawnSync('bash', [path.join(HERE, 'run.sh'), e.abs], { stdio: 'inherit', env: childEnv(state) });
  return r.status == null ? 1 : r.status;
}

async function main() {
  const opts = core.parseArgs(process.argv.slice(2));
  const entries = loadEntries();
  core.select(entries, { only: [] }); // duplicate ids fail even for --list
  if (opts.list) {
    for (const e of entries) console.log([e.id, e.app, e.identity, `${e.steps} steps`, e.file].join('\t'));
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
  if (opts.record) return record(entries, opts.record);

  const sel = core.select(entries, opts);
  if (!sel.length) throw new Error('no scenario matches the options');
  const startedAt = new Date().toISOString();
  const out = path.resolve(opts.out || path.join(HERE, 'work', 'dryrun', core.stamp(new Date(startedAt))));
  fs.mkdirSync(out, { recursive: true });
  console.log(`dry run: ${sel.length} scenario(s), out ${out}`);
  const before = await readVersions();

  const states = {};
  const signins = {};
  for (const who of core.signinPlan(sel)) {
    await ramGuard();
    try {
      const r = await signIn(who);
      states[who] = r.file;
      signins[who] = r.reused ? 'saved session still valid' : 'signed in';
    } catch (e) {
      signins[who] = `BLOCKED: ${core.cell(String(e.message || e).split('\n')[0], 200)}`;
    }
    console.log(`signin ${who}: ${signins[who]}`);
  }

  const outcomes = [];
  for (const e of sel) {
    let o;
    if (e.identity !== 'public' && !states[e.identity]) {
      o = core.outcome(e, { blocked: signins[e.identity] || 'not signed in' });
    } else {
      await ramGuard();
      const work = path.join(HERE, 'work', e.id);
      for (const f of ['result.json', 'timeline.json']) fs.rmSync(path.join(work, f), { force: true });
      console.log(`=== ${e.id} (${e.app}, ${e.identity})`);
      const t0 = Date.now();
      const r = spawnSync(process.execPath, [path.join(HERE, 'record.cjs'), e.abs, '--fast'],
        { stdio: 'inherit', env: childEnv(states[e.identity] || null), timeout: 600_000 });
      o = core.outcome(e, { result: readJson(path.join(work, 'result.json')), timeline: readJson(path.join(work, 'timeline.json')),
        exitCode: r.status == null ? (r.signal || 'timeout') : r.status, ms: Date.now() - t0 });
    }
    outcomes.push(o);
    console.log(`--> ${o.id} ${o.verdict} ${o.steps_passed}/${o.steps_total}${o.reason ? ` (${o.reason})` : ''}`);
    if (!opts.keepGoing && o.verdict !== 'PASS') break;
  }

  const after = await readVersions();
  const run = { startedAt, finishedAt: new Date().toISOString(), egress: country, signins, shas: core.shaTable(before, after), outcomes };
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
