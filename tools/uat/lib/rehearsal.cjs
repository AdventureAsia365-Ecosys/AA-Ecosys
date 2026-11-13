// The pilot rehearsal fixtures of the UAT studio scenarios (REH-03..REH-04b; root docs/ops/runbooks/pilot-rehearsal.md):
// the synthetic agency pilot-rehearsal-01 ("E2E Pilot Rehearsal Travel", kind demo, CRM + TripPlanner add-ons; its id
// is the AA-Partner seed catalogue's UUIDv5 of the key, public there), the studio identity that signs in as its E2E
// OWNER (secret crm/dev/e2e-test-crm/pilot-rehearsal-01-owner, read in memory only), tour X (env UAT_REH_TOUR_X), the
// test channel secrets (read in memory only, never printed) and the invented brand guide .docx built in memory.
//   const reh = require('./rehearsal.cjs'); reh.TENANT.slug; reh.tourX(); reh.brandGuideDocx(); reh.channelCreds('wordpress')
// Pure but for the aws CLI read in channelCreds(). Tests: tools/uat/tests/rehearsal.test.cjs (no network).
'use strict';
const { execFileSync } = require('child_process');
const zlib = require('zlib');
const { PROFILE, REGION, secretError } = require('./crm-signin.cjs');

// The rehearsal agency. Same id in CIS (the tenant_provision saga of the CIS fixture) and the CRM (the seed).
const TENANT = { slug: 'pilot-rehearsal-01', name: 'E2E Pilot Rehearsal Travel', id: '41ea21ee-77ee-5474-bd6d-aa738d2da990' };
const SECRET = 'crm/dev/e2e-test-crm/pilot-rehearsal-01-owner';
// The test channels of step 4b (Secrets Manager, acc2): the WordPress test site (site_url, app_user, app_password) and
// the Facebook test Page (page_id, page_access_token). Kept apart from the tenant's own connection secrets.
const CHANNEL_SECRETS = {
  wordpress: { id: 'aa-cis/dev/e2e-wordpress-test', keys: ['site_url', 'app_user', 'app_password'] },
  facebook: { id: 'aa-cis/dev/e2e-facebook-test', keys: ['page_id', 'page_access_token'] },
};
const TRIPPLANNER = (process.env.UAT_TRIPPLANNER || 'https://tripplanner.lumiguides.it.com').replace(/\/+$/, '');

function secretId(env = process.env) {
  return env.UAT_STUDIO_REHEARSAL_SECRET || SECRET;
}

/**
 * Tour X of the runbook (Fixtures): env UAT_REH_TOUR_X = its CIS tour id (the catalog's tour_id or its published id,
 * from the Booking sellable list). Throws when unset or not an id: the scenario never guesses the tour.
 */
function tourX(env = process.env) {
  const v = String(env.UAT_REH_TOUR_X || '').trim();
  if (!v) throw new Error('UAT_REH_TOUR_X is not set: the id of tour X (runbook Fixtures, a sellable Booking trip plan)');
  if (!/^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$/.test(v)) throw new Error('UAT_REH_TOUR_X is not a tour id');
  return v;
}

/** The pool row of tour X among `rows` (GET /v1/tours/pool rows): by tour_id or by published id. */
function findTour(rows, x) {
  const want = String(x).toLowerCase();
  return (Array.isArray(rows) ? rows : []).find((t) => t && (String(t.tour_id || '').toLowerCase() === want
    || String(t.id || '').toLowerCase() === want)) || null;
}

/** The agency's planner link for a tour (the blog piece carries it into WordPress, step 4b). */
function plannerLink(tourId) {
  return `${TRIPPLANNER}/${TENANT.slug}/plan?tour=${encodeURIComponent(tourId)}`;
}

/**
 * The JSON of a test channel secret, in memory only: { site_url, app_user, app_password } or { page_id,
 * page_access_token }. Throws a one-line reason (never the value, never the CLI text).
 */
function channelCreds(channel, run = execFileSync) {
  const spec = CHANNEL_SECRETS[channel];
  if (!spec) throw new Error(`unknown channel ${channel}`);
  let raw;
  try {
    raw = run('aws', ['secretsmanager', 'get-secret-value', '--secret-id', spec.id, '--profile', PROFILE, '--region', REGION,
      '--query', 'SecretString', '--output', 'text'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 30_000 });
  } catch (e) {
    throw new Error(secretError(spec.id, String(e.stderr || e.message || '')));
  }
  let s;
  try {
    s = JSON.parse(raw);
  } catch {
    throw new Error(`secret ${spec.id} is not JSON`);
  }
  const missing = spec.keys.filter((k) => typeof s[k] !== 'string' || !s[k].trim());
  if (missing.length) throw new Error(`secret ${spec.id} lacks ${missing.join(', ')}`);
  return Object.fromEntries(spec.keys.map((k) => [k, s[k].trim()]));
}

// ── the invented brand guide (.docx) ────────────────────────────────────────────────────────────────────────────────
// Paragraphs in the order of the AA brief template (CIS services/brand_intake/brief.py): the first one is the brand
// name, the section headings are its known headings, the labels its inline labels. Every word is invented.
const BRAND = {
  name: TENANT.name,
  type: 'Small-group adventure travel agency',
  cta: 'Ask us to plan this journey with you.',
  forbidden: ['once in a lifetime', 'hidden gem', 'bucket list'],
};
const BRAND_PARAGRAPHS = [
  BRAND.name,
  'Brand identity',
  `Brand type: ${BRAND.type}`,
  'Core idea: Unhurried journeys through mainland Southeast Asia, planned day by day with local guides.',
  'Primary markets: Australia, United Kingdom',
  'Customer segment: Active couples and friends aged 35 to 60 who travel once or twice a year.',
  'Customer mindset: They want real places without rushing, and a plan they can trust.',
  'Tone of voice',
  'Warm',
  'Practical',
  'Curious',
  'Writing style',
  'Short paragraphs and plain words. Name the place first, then what the traveller does there.',
  'Should write',
  'Write about "unhurried days", "local guides" and "small groups".',
  'Should not write',
  ...BRAND.forbidden.map((w) => `"${w}"`),
  'Call to action',
  BRAND.cta,
  'Signature words',
  'unhurried days, local guides, small groups',
];

const xmlEscape = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** A stored-entry ZIP (method 0) of [{ name, data: Buffer }], with CRC-32 (zlib.crc32, Node 22). */
function zipStore(entries) {
  const locals = [];
  const central = [];
  let offset = 0;
  for (const { name, data } of entries) {
    const n = Buffer.from(name, 'utf8');
    const crc = zlib.crc32(data) >>> 0;
    const lh = Buffer.alloc(30);
    lh.writeUInt32LE(0x04034b50, 0); lh.writeUInt16LE(20, 4); lh.writeUInt16LE(0, 8);
    lh.writeUInt32LE(crc, 14); lh.writeUInt32LE(data.length, 18); lh.writeUInt32LE(data.length, 22); lh.writeUInt16LE(n.length, 26);
    const ch = Buffer.alloc(46);
    ch.writeUInt32LE(0x02014b50, 0); ch.writeUInt16LE(20, 4); ch.writeUInt16LE(20, 6); ch.writeUInt16LE(0, 10);
    ch.writeUInt32LE(crc, 16); ch.writeUInt32LE(data.length, 20); ch.writeUInt32LE(data.length, 24); ch.writeUInt16LE(n.length, 28);
    ch.writeUInt32LE(offset, 42);
    locals.push(lh, n, data);
    central.push(ch, n);
    offset += 30 + n.length + data.length;
  }
  const cd = Buffer.concat(central);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0); end.writeUInt16LE(entries.length, 8); end.writeUInt16LE(entries.length, 10);
  end.writeUInt32LE(cd.length, 12); end.writeUInt32LE(offset, 16);
  return Buffer.concat([...locals, cd, end]);
}

/** The invented brand guide as a minimal Word .docx (Buffer): one plain paragraph per BRAND_PARAGRAPHS line. */
function brandGuideDocx(paragraphs = BRAND_PARAGRAPHS) {
  const W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main';
  const body = paragraphs.map((p) => `<w:p><w:r><w:t xml:space="preserve">${xmlEscape(p)}</w:t></w:r></w:p>`).join('');
  const files = {
    '[Content_Types].xml': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      + '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      + '<Default Extension="xml" ContentType="application/xml"/>'
      + '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
      + '</Types>',
    '_rels/.rels': '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
      + '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
      + '</Relationships>',
    'word/document.xml': `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="${W}"><w:body>${body}</w:body></w:document>`,
  };
  return zipStore(Object.entries(files).map(([name, text]) => ({ name, data: Buffer.from(text, 'utf8') })));
}

const BRAND_FILE = 'pilot-rehearsal-brand-guide.docx';
const DOCX_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

module.exports = {
  TENANT, SECRET, CHANNEL_SECRETS, TRIPPLANNER, BRAND, BRAND_PARAGRAPHS, BRAND_FILE, DOCX_TYPE,
  secretId, tourX, findTour, plannerLink, channelCreds, brandGuideDocx, zipStore,
};
