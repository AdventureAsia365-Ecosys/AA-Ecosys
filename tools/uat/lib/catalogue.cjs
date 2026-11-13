// The UAT scenario catalogue (AA-855; plan docs/audits/2026-11-05-S268-video-plan, "Một danh mục duy nhất"):
// tools/uat/catalogue.json holds one row per scenario id; this module validates it and checks it against the scenario
// files and the dry-run manifest. Pure: no browser, no network. Tests: tools/uat/tests/catalogue.test.cjs.
//
//   node tools/uat/lib/catalogue.cjs            validate, then print the rows: id, status, round, identity, file
//   node tools/uat/lib/catalogue.cjs --round R1-2026-11   only that round's rows
'use strict';
const fs = require('fs');
const path = require('path');

const FILE = path.join(__dirname, '..', 'catalogue.json');
const APPS = ['tripplanner', 'cis-admin', 'content-studio', 'partner-portal', 'crm', 'booking', 'cross-app'];
const STATUSES = ['live', 'after-lane', 'blocked', 'retired'];
// uat (acceptance), guide (training), release (milestone clip), regression (dry run / smoke); data = a never-recorded
// data step (CRM review prep and cleanup).
const KINDS = ['uat', 'guide', 'release', 'regression', 'data'];
// The dry-run identities (lib/dryrun-core.cjs) plus the ones only plans name yet: the CRM assistant, a traveller on the
// client host, several identities in one story, and a story recorded by hand.
const IDENTITIES = ['public', 'cis-admin', 'booking', 'studio', 'studio-editor', 'studio-audit', 'studio-rehearsal', 'crm', 'crm-assistant', 'traveller', 'multi', 'manual'];
const REQUIRED = { id: 'string', app: 'string', module: 'string', story: 'string', roles: 'array', kinds: 'array', covers: 'array',
  screens: 'array', status: 'string', round: 'round', identity: 'string', writes: 'boolean', paid: 'boolean' };
const OPTIONAL = { file: 'string', note: 'string', issues: 'array' };
// <APP>-<NN>, <APP>-PUB-<NN>, a split letter (PRT-07b), a phone variant (.m), a role variant (@account-manager); the CRM
// review chapters CRM-REV-<NN> and its two data steps; the pilot rehearsal REH-<nn>[letter]-<slug> (one per runbook step).
const ID = /^(?:[A-Z]+(?:-PUB)?-\d{2}[a-z]?(?:\.m)?(?:@[a-z][a-z-]*)?|CRM-REV-(?:\d{2}|PREP|CLEANUP)|REH-\d{2}[a-z]?-[a-z][a-z0-9]*(?:-[a-z0-9]+)*)$/;
const ROUND = /^R\d+[a-z]?-\d{4}-\d{2}$/;
const ISSUE_ID = /\bAA-?\d{3,4}\b/;

function typeOk(v, t) {
  if (t === 'array') return Array.isArray(v) && v.every((x) => typeof x === 'string' && x.length > 0);
  if (t === 'round') return v === null || (typeof v === 'string' && ROUND.test(v));
  return typeof v === t && (t !== 'string' || v.length > 0);
}

/** Every problem of a parsed catalogue, as one-line strings (empty = valid). */
function validate(cat) {
  const errs = [];
  if (!cat || typeof cat !== 'object') return ['catalogue is not an object'];
  if (cat.version !== 1) errs.push('version must be 1');
  if (!Array.isArray(cat.scenarios) || !cat.scenarios.length) return [...errs, 'scenarios must be a non-empty list'];
  const seen = new Set();
  cat.scenarios.forEach((row, i) => {
    const at = row && row.id ? row.id : `row ${i + 1}`;
    if (!row || typeof row !== 'object') { errs.push(`${at}: not an object`); return; }
    for (const [k, t] of Object.entries(REQUIRED)) if (!(k in row) || !typeOk(row[k], t)) errs.push(`${at}: ${k} missing or not ${t}`);
    for (const k of Object.keys(row)) {
      if (!(k in REQUIRED) && !(k in OPTIONAL)) errs.push(`${at}: unknown field ${k}`);
      else if (k in OPTIONAL && !typeOk(row[k], OPTIONAL[k])) errs.push(`${at}: ${k} is not ${OPTIONAL[k]}`);
    }
    if (typeof row.id === 'string') {
      if (!ID.test(row.id)) errs.push(`${at}: id does not follow <APP>-<NN> (variants .m, @role, a letter)`);
      if (seen.has(row.id)) errs.push(`${at}: duplicate id`);
      seen.add(row.id);
    }
    if (row.app && !APPS.includes(row.app)) errs.push(`${at}: unknown app ${row.app}`);
    if (row.status && !STATUSES.includes(row.status)) errs.push(`${at}: unknown status ${row.status}`);
    if (Array.isArray(row.kinds)) {
      if (!row.kinds.length) errs.push(`${at}: kinds is empty`);
      for (const k of row.kinds) if (!KINDS.includes(k)) errs.push(`${at}: unknown kind ${k}`);
    }
    if (Array.isArray(row.roles) && !row.roles.length) errs.push(`${at}: roles is empty`);
    if (row.identity && !IDENTITIES.includes(row.identity)) errs.push(`${at}: unknown identity ${row.identity}`);
    if (row.status === 'retired' && row.round) errs.push(`${at}: a retired scenario is in no round`);
    if (row.status === 'retired' && row.file) errs.push(`${at}: a retired scenario keeps no scenario file`);
    if (typeof row.file === 'string' && (!/^[a-z0-9-]+\/[a-z0-9.-]+\.cjs$/.test(row.file) || row.file.includes('..'))) {
      errs.push(`${at}: file must be <folder>/<name>.cjs under scenarios/`);
    }
    // Story and note can reach captions, the public index and the owner's page: no internal issue ids there.
    for (const k of ['story', 'note']) if (typeof row[k] === 'string' && ISSUE_ID.test(row[k])) errs.push(`${at}: ${k} names an internal issue id`);
  });
  return errs;
}

function load(file = FILE) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

/** The catalogue loaded and validated; throws with every problem listed. */
function loadValid(file = FILE) {
  const cat = load(file);
  const errs = validate(cat);
  if (errs.length) throw new Error(`catalogue.json:\n  ${errs.join('\n  ')}`);
  return cat;
}

const byId = (cat) => new Map(cat.scenarios.map((r) => [r.id, r]));

/**
 * Problems between the catalogue and the scenario modules: `modules` = [{ rel, sc }] (rel relative to scenarios/).
 * Every module's id has a row naming that file and the same app; every row's file exists among the modules.
 */
function checkFiles(cat, modules) {
  const errs = [];
  const rows = byId(cat);
  const rels = new Set(modules.map((m) => m.rel));
  for (const { rel, sc } of modules) {
    const row = rows.get(sc.id);
    if (!row) { errs.push(`${rel}: scenario ${sc.id} has no catalogue row`); continue; }
    if (row.file !== rel) errs.push(`${sc.id}: catalogue file is ${row.file || 'missing'}, the scenario lives in ${rel}`);
    if (row.app !== sc.app) errs.push(`${sc.id}: catalogue app ${row.app}, scenario app ${sc.app}`);
    if (sc.identity && row.identity !== sc.identity) errs.push(`${sc.id}: catalogue identity ${row.identity}, scenario identity ${sc.identity}`);
  }
  for (const row of cat.scenarios) if (row.file && !rels.has(row.file)) errs.push(`${row.id}: file ${row.file} does not exist`);
  return errs;
}

/**
 * Problems between the catalogue and the dry-run manifest entries ({ id, identity }): every entry has a row that is
 * live, not retired, writes nothing and costs nothing, with the same identity.
 */
function checkManifest(cat, entries) {
  const errs = [];
  const rows = byId(cat);
  for (const e of entries) {
    const row = rows.get(e.id);
    if (!row) { errs.push(`manifest ${e.id}: no catalogue row`); continue; }
    if (row.status === 'retired') errs.push(`manifest ${e.id}: retired scenarios never run`);
    else if (row.status !== 'live') errs.push(`manifest ${e.id}: status ${row.status}, only live scenarios run`);
    if (row.writes) errs.push(`manifest ${e.id}: the catalogue says it writes`);
    if (row.paid) errs.push(`manifest ${e.id}: the catalogue says it is paid`);
    if (row.identity !== e.identity) errs.push(`manifest ${e.id}: catalogue identity ${row.identity}, manifest identity ${e.identity}`);
  }
  return errs;
}

/**
 * Problems between the catalogue and the write set (scenarios/write-set.cjs entries { id, identity, paid }): every
 * entry has a live row that writes, with the same identity and the same paid flag (a paid scenario is marked paid in
 * both places, so the runner's --allow-paid gate and the catalogue never disagree).
 */
function checkWriteSet(cat, entries) {
  const errs = [];
  const rows = byId(cat);
  for (const e of entries) {
    const row = rows.get(e.id);
    if (!row) { errs.push(`write set ${e.id}: no catalogue row`); continue; }
    if (row.status !== 'live') errs.push(`write set ${e.id}: status ${row.status}, only live scenarios run`);
    if (!row.writes) errs.push(`write set ${e.id}: the catalogue says it writes nothing (then it belongs in the dry-run set)`);
    if (row.paid !== e.paid) errs.push(`write set ${e.id}: catalogue paid ${row.paid}, scenario paid ${e.paid}`);
    if (row.identity !== e.identity) errs.push(`write set ${e.id}: catalogue identity ${row.identity}, scenario identity ${e.identity}`);
  }
  return errs;
}

module.exports = { FILE, APPS, STATUSES, KINDS, IDENTITIES, ID, validate, load, loadValid, byId, checkFiles, checkManifest, checkWriteSet };

if (require.main === module) {
  const i = process.argv.indexOf('--round');
  const round = i > 0 ? process.argv[i + 1] : null;
  const cat = loadValid();
  for (const r of cat.scenarios.filter((x) => !round || x.round === round)) {
    console.log([r.id, r.status, r.round || '-', r.identity, r.writes ? 'writes' : '', r.paid ? 'paid' : '', r.file || ''].join('\t'));
  }
}
