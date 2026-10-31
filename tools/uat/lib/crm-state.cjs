// CRM review run state (skill aa-uat-video; plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): the ids the
// prep scenario and the chunks share, in work/crm/state.json (gitignored). Link tokens and other credentials go to
// work/crm/.secrets.json (chmod 600), never into state.json, logs or captions. Cost $0, local files only.
//
//   const st = require('../../lib/crm-state.cjs');
//   const s = st.load();  s.r03 = { trip_id }; st.save(s);
//   st.runTag(s)          -> "rv202610311": the per-run suffix of every synthetic name and @example.invalid address
//   st.newRun()           -> a fresh run (next <n> for today), keeping none of the previous run's ids (only `incident`)
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

function save(s) {
  fs.mkdirSync(DIR, { recursive: true });
  fs.writeFileSync(STATE, JSON.stringify(s, null, 2));
  return s;
}

function newRun() {
  const prev = load();
  const day = today();
  const n = prev.run && prev.run.startsWith(`rv${day}`) ? Number(prev.run.slice(10)) + 1 : 1;
  // An Adventure Asia incident belongs to a departure, not to a run: it survives a new run.
  const keep = prev.incident ? { incident: prev.incident } : {};
  return save({ run: `rv${day}${n}`, run_day: day, created_at: new Date().toISOString(), created: {}, ...keep });
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
  fs.mkdirSync(DIR, { recursive: true });
  fs.writeFileSync(SECRETS, JSON.stringify(v, null, 1), { mode: 0o600 });
  fs.chmodSync(SECRETS, 0o600);
}

module.exports = { DIR, STATE, today, load, save, newRun, runTag, remember, loadSecrets, saveSecrets };

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
