// CRM review run state (skill aa-uat-video; plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): the ids the
// prep scenario and the chunks share, in work/crm/state.json (gitignored). Link tokens and other credentials go to
// work/crm/.secrets.json (chmod 600), never into state.json, logs or captions. Cost $0, local files only.
//
//   const st = require('../../lib/crm-state.cjs');
//   const s = st.load();  s.r03 = { trip_id }; st.save(s);
//   st.runTag(s)          -> "rv202610311": the per-run suffix of every synthetic name and @example.invalid address
//   st.newRun()           -> a fresh run (next <n> for today). The previous run's ids are dropped only when cleanup.cjs
//                            ran after it; otherwise its `created` ids (and its prep / R03 trips) are carried into the
//                            new run, so the next cleanup still closes them. Old link tokens are wiped either way.
//   st.saveLink(name, link, tripId) / st.link(name, tripId)  -> a client / portal link kept in .secrets.json together
//                            with the trip it belongs to; link() refuses a link of another trip (an earlier run's)
// CLI (an Adventure Asia incident is raised outside the CRM; crm-rev-12 shows it only when this says it is open):
//   node tools/uat/lib/crm-state.cjs incident open <trip id>   -> state.json incident = { trip_id, open: true }
//   node tools/uat/lib/crm-state.cjs incident clear            -> incident.open = false
const fs = require('fs');
const path = require('path');

const DIR = path.join(__dirname, '..', 'work', 'crm');
const STATE = path.join(DIR, 'state.json');
const SECRETS = path.join(DIR, '.secrets.json');

/** Today's date as yyyymmdd in the agency's time zone (the synthetic agency runs on Asia/Ho_Chi_Minh). */
function today(tz = 'Asia/Ho_Chi_Minh') {
  const p = new Intl.DateTimeFormat('en-CA', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
  return p.replace(/-/g, '');
}

function load() {
  try {
    return JSON.parse(fs.readFileSync(STATE, 'utf8'));
  } catch {
    return {};
  }
}

/** The run folder holds .secrets.json and the sign-in states: owner-only (700), whoever creates it first. */
function ensureDir() {
  fs.mkdirSync(DIR, { recursive: true, mode: 0o700 });
  fs.chmodSync(DIR, 0o700);
}

function save(s) {
  ensureDir();
  fs.writeFileSync(STATE, JSON.stringify(s, null, 2));
  return s;
}

/** The previous run's objects that cleanup.cjs has not closed yet (empty when it ran after the run started). */
function uncleaned(prev) {
  if (!prev.run || (prev.cleaned_at && prev.created_at && prev.cleaned_at > prev.created_at)) return {};
  const created = JSON.parse(JSON.stringify(prev.created || {}));
  const trips = new Set(created.trips || []);
  for (const t of [prev.r03, prev.side_trip, prev.invoice_trip]) if (t && t.trip_id) trips.add(t.trip_id);
  if (trips.size) created.trips = [...trips];
  return Object.values(created).some((v) => v && v.length) ? created : {};
}

function newRun() {
  const prev = load();
  const day = today();
  const n = prev.run && prev.run.startsWith(`rv${day}`) ? Number(prev.run.slice(10)) + 1 : 1;
  // An Adventure Asia incident belongs to a departure, not to a run: it survives a new run.
  const keep = prev.incident ? { incident: prev.incident } : {};
  const carried = uncleaned(prev);
  if (Object.keys(carried).length) console.warn(`crm-state: ${prev.run} was not cleaned up; its ids move into the new run for cleanup.cjs`);
  clearSecrets(); // the old run's link tokens are never valid for the new run's trips
  return save({
    run: `rv${day}${n}`, run_day: day, created_at: new Date().toISOString(), created: carried, ...keep,
    ...(Object.keys(carried).length ? { carried_from: prev.run } : {}),
  });
}

function runTag(s) {
  if (!s || !s.run) throw new Error('no CRM review run yet: node tools/uat/record.cjs scenarios/crm/prep.cjs --fast');
  return s.run;
}

/** Remember an object created for the review so cleanup.cjs can undo it (kind: trips, saved_replies, drafts, ...). */
function remember(s, kind, id) {
  s.created = s.created || {};
  s.created[kind] = s.created[kind] || [];
  if (id && !s.created[kind].includes(id)) s.created[kind].push(id);
  return s;
}

function loadSecrets() {
  try {
    return JSON.parse(fs.readFileSync(SECRETS, 'utf8'));
  } catch {
    return {};
  }
}

function saveSecrets(v) {
  ensureDir();
  fs.writeFileSync(SECRETS, JSON.stringify(v, null, 1), { mode: 0o600 });
  fs.chmodSync(SECRETS, 0o600);
}

/** Wipe the link tokens, keeping the named entries (cleanup keeps the R10 link when it keeps prep's invoice trip). */
function clearSecrets(keepNames = []) {
  const cur = loadSecrets();
  const kept = {};
  for (const k of keepNames) {
    if (cur[k] !== undefined) kept[k] = cur[k];
    if (cur[`${k}_trip`] !== undefined) kept[`${k}_trip`] = cur[`${k}_trip`];
  }
  if (Object.keys(kept).length) saveSecrets(kept);
  else fs.rmSync(SECRETS, { force: true });
}

/** Keep a link token together with the trip it opens. */
function saveLink(name, link, tripId) {
  const v = loadSecrets();
  v[name] = link;
  v[`${name}_trip`] = tripId;
  saveSecrets(v);
}

/** The link `name` of trip `tripId`, or null when there is none or it belongs to another trip (an earlier run). */
function link(name, tripId) {
  const v = loadSecrets();
  if (!v[name] || !tripId || v[`${name}_trip`] !== tripId) return null;
  return v[name];
}

module.exports = { DIR, STATE, today, load, save, newRun, runTag, remember, loadSecrets, saveSecrets, clearSecrets, saveLink, link };

if (require.main === module) {
  const [what, mode, tripId] = process.argv.slice(2);
  if (what !== 'incident' || !['open', 'clear'].includes(mode)) {
    console.error('usage: node tools/uat/lib/crm-state.cjs incident open <trip id> | incident clear');
    process.exit(64);
  }
  const s = load();
  if (mode === 'open') {
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(tripId || '')) {
      console.error('incident open needs the affected CRM trip id (a uuid)');
      process.exit(64);
    }
    s.incident = { trip_id: tripId, open: true, set_at: new Date().toISOString() };
  } else {
    s.incident = { ...(s.incident || {}), open: false, set_at: new Date().toISOString() };
  }
  save(s);
  console.log(`incident ${mode === 'open' ? `open on trip ${tripId.slice(0, 8)}` : 'cleared'} in ${path.relative(process.cwd(), STATE)}; make the CRM-REV-12 captions again`);
}
