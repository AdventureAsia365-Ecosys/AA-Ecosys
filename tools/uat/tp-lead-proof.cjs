// The $0 live proof of TripPlanner lead delivery and of the AI sessions quota on a SYNTHETIC agency (AA-1116; root
// docs/ops/runbooks/pilot-rehearsal.md step 6b, gap G14, and the AI sessions check of step 12). Headless Chromium on the
// agency's real planner (/{slug}/plan), so the web ACL challenge and the BFF's tenant assertion are the real ones; the
// trip and the request are made from the page with the planner's own /api/trip calls (no model call: search, narration
// and, in lead mode, the planning chat are blocked).
//
//   node tools/uat/tp-lead-proof.cjs lead --channel webhook --slug <slug> --tenant <uuid> --agency "<name>" --webhook-port 8787
//   node tools/uat/tp-lead-proof.cjs lead --channel email   --slug <slug> --tenant <uuid> --agency "<name>" --lead-email e2e@e2e-mail.lumiguides.it.com
//   node tools/uat/tp-lead-proof.cjs lead --channel crm     --slug <slug> --tenant <uuid> --agency "<name>"
//   node tools/uat/tp-lead-proof.cjs sessions-cap --slug <slug> --tenant <uuid> --agency "<name>" --quota-zero
//
// lead: one guest trip (one free day, `add_day`) and one "Send to <agency>" with the contact consent ticked. The send
//   answers 200 with `lead.channel` = --channel, then the channel is checked:
//   webhook  this script listens on 127.0.0.1:--webhook-port (the orchestrator exposes it on a public https URL and
//            sets it as the tenant's lead route first) and checks the POST: X-AA-Signature (HMAC-SHA256 with the
//            tenant key derived from the master secret tripplanner/<env>/lead-webhook-key, read in memory only),
//            a timestamp within 5 minutes, X-AA-Contract, Idempotency-Key, the lead id, tenant and traveller. It
//            answers 200 only when every check passes (else 401, so TripPlanner records a failed attempt);
//   email    the lead e-mail lands in the E2E mailbox (S3 inbound/, read only): To the agency's lead address (an
//            address on the E2E mail domain only; SES receives only the recipients AA-CIS-Infra
//            accounts/aa365/e2e_mailbox.tf lists, e.g. e2e@<that domain>), Reply-To the traveller, the agency's name as the sender's display
//            name, the lead id in the text;
//   crm      the CRM pulls and acknowledges the lead (crm_tp_lead_pull): TripPlanner's `lead_delivered` line with
//            channel crm for this tenant (CloudWatch Logs of the assembly Lambda, read only).
//   Every channel also waits for that `lead_delivered` line.
// sessions-cap: the tenant's `tp.ai_sessions` must be 0 (a Tenant 360 override the orchestrator set and read back:
//   --quota-zero says so). One new guest session asks the planning chat once: the answer must be `paused` / `budget`
//   and TripPlanner's `tenant_ai_sessions_stop` line must say `tenant_sessions_cap` for this tenant. With the quota at 0
//   no model is called ($0); if the quota were not enforced, the one chat turn would cost a few cents at most.
//
// Writes on Dev (synthetic agency only; the agency name must carry E2E / Test / Synthetic / Rehearsal): one guest
// session and trip, one lead (lead mode) or one refused chat turn. Reads: the webhook master secret (webhook only),
// the E2E mailbox (email only), the assembly Lambda's log lines. Profile UAT_AWS_PROFILE or aa365-admin. The traveller
// is invented (an address on .invalid). The result JSON (ids, checks, no secret) goes to --out (default
// tools/uat/work/tp-lead-proof-<mode>-<time>.json). Exit 0 = every check passed, 1 = a failure (one-line reason).
'use strict';
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const MODES = ['lead', 'sessions-cap'];
const CHANNELS = ['crm', 'webhook', 'email'];
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SLUG = /^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$/;
// The agency must be a synthetic one: its trading name carries one of these words (real agencies never do).
const SYNTHETIC = /\b(E2E|Test|Synthetic|Rehearsal)\b/i;
// Lead e-mails only go to the E2E inbound domain (its mail lands in the E2E mailbox bucket, never a person's inbox).
const E2E_MAIL_DOMAIN = /@e2e-mail\.lumiguides\.it\.com$/i;
const WEBHOOK_KEY_LABEL = 'aa-tripplanner lead webhook v1:'; // AA-TripPlanner-Web backend/assembly/leads.py
const CONTRACT = 'lead.submitted.v1';
const SIGNATURE_TOLERANCE_S = 300; // technical-constant: replay window of this verifier, not a product setting
const DEFAULTS = { webhookPort: 8787, timeoutS: 300, mailPrefix: 'inbound/', env: 'dev' };

function parseArgs(argv) {
  const [mode, ...rest] = argv;
  if (!MODES.includes(mode)) throw new Error(`first argument must be one of ${MODES.join(', ')}`);
  const out = { mode, channel: null, slug: null, tenant: null, agency: null, leadEmail: null, quotaZero: false,
    webhookPort: DEFAULTS.webhookPort, timeoutS: DEFAULTS.timeoutS, mailPrefix: DEFAULTS.mailPrefix, logGroup: null,
    out: null, env: DEFAULTS.env };
  for (let i = 0; i < rest.length; i++) {
    const a = rest[i];
    const val = () => {
      if (i + 1 >= rest.length) throw new Error(`${a} needs a value`);
      return rest[++i];
    };
    if (a === '--channel') out.channel = val();
    else if (a === '--slug') out.slug = val();
    else if (a === '--tenant') out.tenant = val().toLowerCase();
    else if (a === '--agency') out.agency = val();
    else if (a === '--lead-email') out.leadEmail = val().toLowerCase();
    else if (a === '--webhook-port') out.webhookPort = Number(val());
    else if (a === '--timeout-s') out.timeoutS = Number(val());
    else if (a === '--mail-prefix') out.mailPrefix = val();
    else if (a === '--log-group') out.logGroup = val();
    else if (a === '--out') out.out = val();
    else if (a === '--env') out.env = val();
    else if (a === '--quota-zero') out.quotaZero = true;
    else throw new Error(`unknown argument ${a}`);
  }
  if (!out.slug || !SLUG.test(out.slug)) throw new Error('--slug <the agency TripPlanner slug> is required');
  if (!out.tenant || !UUID.test(out.tenant)) throw new Error('--tenant <the agency CIS tenant id> is required');
  if (!out.agency || !SYNTHETIC.test(out.agency)) {
    throw new Error('pilot_guard: --agency must be the synthetic agency\'s exact name (with E2E, Test, Synthetic or Rehearsal)');
  }
  if (!/^[a-z]{2,12}$/.test(out.env)) throw new Error('--env is a short environment name (dev)');
  if (!(out.timeoutS >= 30 && out.timeoutS <= 1800)) throw new Error('--timeout-s must be between 30 and 1800');
  if (mode === 'lead') {
    if (!CHANNELS.includes(out.channel)) throw new Error(`--channel must be one of ${CHANNELS.join(', ')}`);
    if (out.channel === 'email' && !(out.leadEmail && E2E_MAIL_DOMAIN.test(out.leadEmail))) {
      throw new Error('--lead-email must be the agency\'s lead address on the E2E mail domain (the tenant\'s lead route)');
    }
    if (out.channel === 'webhook' && !(Number.isInteger(out.webhookPort) && out.webhookPort >= 1024 && out.webhookPort <= 65535)) {
      throw new Error('--webhook-port must be a port between 1024 and 65535');
    }
  } else if (!out.quotaZero) {
    throw new Error('--quota-zero is required: set the tenant\'s tp.ai_sessions override to 0 on Tenant 360 and read it back first');
  }
  return out;
}

/** The invented traveller of one run: an address on .invalid, never a person. */
function traveller(run) {
  return { name: `E2E Lead Proof ${run}`, email: `lead-proof-${run}@example.invalid` };
}

/** The planner's LeadBody (AA-TripPlanner-Web frontend/lib/leadForm.ts) for one run. */
function leadBody(run) {
  const t = traveller(run);
  return {
    traveller: { name: t.name, email: t.email, phone: null, locale: 'en' },
    party: { adults: 2, child_ages: [] },
    trip: { start_date: null, budget_band: null, message: `Synthetic lead proof ${run}. Please ignore.` },
    consent: { contact: true, marketing: false },
  };
}

/** The tenant's webhook key: the hex text of HMAC-SHA256(master, label + tenant id), used as ASCII bytes. */
function webhookKey(master, tenantId) {
  return Buffer.from(crypto.createHmac('sha256', master).update(WEBHOOK_KEY_LABEL + tenantId).digest('hex'), 'ascii');
}

function signatureOf(key, rawBody, t) {
  return crypto.createHmac('sha256', key).update(Buffer.concat([Buffer.from(`${t}.`), rawBody])).digest('hex');
}

/** Check `X-AA-Signature: t=<unix s>,v1=<hex>` over the raw body. Returns null when valid, else the reason. */
function verifySignature(header, rawBody, key, nowS, tolerance = SIGNATURE_TOLERANCE_S) {
  const m = /^t=(\d{1,12}),v1=([0-9a-f]{64})$/.exec(String(header || '').trim());
  if (!m) return 'signature header missing or malformed';
  const t = Number(m[1]);
  if (Math.abs(nowS - t) > tolerance) return `signature timestamp ${t} is more than ${tolerance} s from now`;
  const want = Buffer.from(signatureOf(key, rawBody, t), 'hex');
  const got = Buffer.from(m[2], 'hex');
  return want.length === got.length && crypto.timingSafeEqual(want, got) ? null : 'signature does not match';
}

/** Every problem of one webhook POST (headers lower-case, raw body Buffer); [] = it is the expected, valid lead. */
function webhookProblems(headers, rawBody, { key, nowS, leadId, tenantId, travellerEmail }) {
  const problems = [];
  const bad = verifySignature(headers['x-aa-signature'], rawBody, key, nowS);
  if (bad) problems.push(bad);
  if (headers['x-aa-contract'] !== CONTRACT) problems.push(`X-AA-Contract is not ${CONTRACT}`);
  let body;
  try {
    body = JSON.parse(rawBody.toString('utf8'));
  } catch {
    return [...problems, 'the body is not JSON'];
  }
  if (!headers['idempotency-key'] || headers['idempotency-key'] !== body.idempotency_key) {
    problems.push('Idempotency-Key does not equal the body\'s idempotency_key');
  }
  if (leadId && body.lead_id !== leadId) problems.push('the lead id is not the one this run sent');
  if (JSON.stringify(body).indexOf(tenantId) === -1) problems.push('the body does not name the tenant');
  if (!body.traveller || body.traveller.email !== travellerEmail) problems.push('the traveller is not this run\'s');
  return problems;
}

/** RFC 2047 encoded words (=?charset?B|Q?...?=) of a header value, decoded. */
function decodeWords(value) {
  return String(value || '').replace(/=\?([^?]+)\?([bqBQ])\?([^?]*)\?=(\s+(?==\?))?/g, (_, charset, enc, text) => {
    let bytes;
    if (enc.toUpperCase() === 'B') bytes = Buffer.from(text, 'base64');
    else bytes = Buffer.from(text.replace(/_/g, ' ').replace(/=([0-9a-f]{2})/gi, (__, h) => String.fromCharCode(parseInt(h, 16))), 'latin1');
    try {
      return new TextDecoder(charset.toLowerCase()).decode(bytes);
    } catch {
      return bytes.toString('utf8');
    }
  });
}

/** (display name, address) of an address header value. */
function splitAddress(value) {
  const v = decodeWords(String(value || '').replace(/\r?\n[ \t]+/g, ' ')).trim();
  const m = /^(.*?)\s*<([^<>\s]+)>\s*$/.exec(v);
  if (!m) return { name: '', address: v.toLowerCase() };
  let name = m[1].trim();
  if (name.startsWith('"') && name.endsWith('"')) name = name.slice(1, -1).replace(/\\(.)/g, '$1');
  return { name, address: m[2].toLowerCase() };
}

/**
 * Every problem of the lead e-mail (raw RFC 822 text, already matched to the lead id); [] = as expected: To the lead
 * address, Reply-To the traveller, the agency's name as the sender's display name, the lead id and the agency in
 * the text. Uses the mailbox reader's header / body parsing.
 */
function leadMailProblems(raw, { mailbox, leadId, agency, leadEmail, travellerEmail }) {
  const problems = [];
  const head = mailbox.parseHeaders(mailbox.splitHeadBody(raw).head);
  const one = (k) => (head.get(k) || [])[0] || '';
  if (!mailbox.isAddressedTo(raw, leadEmail)) problems.push('the mail is not addressed to the lead address');
  const replyTo = splitAddress(one('reply-to'));
  if (replyTo.address !== travellerEmail) problems.push('Reply-To is not the traveller');
  const from = splitAddress(one('from'));
  if (from.name !== agency) problems.push(`the sender's display name is "${from.name}", not the agency's name`);
  const text = mailbox.textBodies(raw).join('\n');
  if (!text.includes(leadId)) problems.push('the text does not carry the lead id');
  if (!text.includes(agency)) problems.push('the text does not name the agency');
  if (!/^Trip request: /.test(decodeWords(one('subject')))) problems.push('the subject is not a trip request');
  return problems;
}

/**
 * The TripPlanner log line of an event for this tenant among CloudWatch messages: the JSON line printed by
 * backend/shared/observability.py emit ({"evt": ..., fields...}), matched on evt, tenant_id and the extra fields.
 */
function findLogLine(messages, evt, tenantId, fields = {}) {
  for (const msg of messages) {
    const start = String(msg).indexOf('{');
    if (start < 0) continue;
    let line;
    try {
      line = JSON.parse(String(msg).slice(start));
    } catch {
      continue;
    }
    if (line && line.evt === evt && line.tenant_id === tenantId
        && Object.entries(fields).every(([k, v]) => line[k] === v)) return line;
  }
  return null;
}

/** The assembly Lambda's log group among names: /aws/lambda/<tripplanner prefix>-assembly. */
function pickLogGroup(names, env) {
  const hits = names.filter((n) => /^\/aws\/lambda\/.*tripplanner.*-assembly$/i.test(n)
    && new RegExp(`(^|[-_/])${env}([-_/]|$)`, 'i').test(n));
  return hits.length === 1 ? hits[0] : null;
}

function stamp(d = new Date()) {
  return d.toISOString().replace(/[-:]/g, '').replace(/\.\d+Z$/, 'Z');
}

// ── Live part (browser, AWS CLI, local listener) ─────────────────────────────────────────────────────────────────

const PROFILE = process.env.UAT_AWS_PROFILE || 'aa365-admin';
const REGION = 'us-west-1';

async function awsJson(args) {
  const { execFile } = require('child_process');
  const { promisify } = require('util');
  const mailbox = require('./lib/mailbox.cjs');
  try {
    const { stdout } = await promisify(execFile)('aws', [...args, '--profile', PROFILE, '--region', REGION,
      '--output', 'json'], { timeout: 30_000, maxBuffer: 16 * 1024 * 1024 });
    return stdout.trim() ? JSON.parse(stdout) : {};
  } catch (e) {
    throw new Error(`aws ${args.slice(0, 2).join(' ')} failed: ${mailbox.awsErrorCode(e)}`);
  }
}

async function logGroup(o) {
  if (o.logGroup) return o.logGroup;
  const out = await awsJson(['logs', 'describe-log-groups', '--log-group-name-prefix', '/aws/lambda/']);
  const g = pickLogGroup((out.logGroups || []).map((x) => x.logGroupName), o.env);
  if (!g) throw new Error('the TripPlanner assembly log group was not found (pass --log-group)');
  return g;
}

/** Poll the assembly log group for one event line of this tenant since `since` (ms), up to the deadline. */
async function waitForLogLine(group, evt, o, since, fields, deadline) {
  for (;;) {
    const out = await awsJson(['logs', 'filter-log-events', '--log-group-name', group, '--start-time', String(since),
      '--filter-pattern', `"${evt}" "${o.tenant}"`, '--max-items', '50']);
    const line = findLogLine((out.events || []).map((e) => e.message), evt, o.tenant, fields);
    if (line) return line;
    if (Date.now() > deadline) return null;
    await new Promise((r) => setTimeout(r, 10_000));
  }
}

/** The webhook listener: resolves with the first POST's check result; answers 200 only to a valid lead. */
function listen(o, key, expect) {
  const http = require('http');
  let done;
  const result = new Promise((r) => { done = r; });
  const server = http.createServer((req, res) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => {
      if (req.method !== 'POST') {
        res.writeHead(405).end();
        return;
      }
      const problems = webhookProblems(req.headers, Buffer.concat(chunks), { key, nowS: Math.floor(Date.now() / 1000),
        tenantId: o.tenant, ...expect() });
      res.writeHead(problems.length ? 401 : 200, { 'content-type': 'application/json' }).end('{}');
      done({ at: new Date().toISOString(), problems });
    });
  });
  server.listen(o.webhookPort, '127.0.0.1');
  return { result, close: () => server.close() };
}

async function webhookMaster(o) {
  const out = await awsJson(['secretsmanager', 'get-secret-value', '--secret-id', `tripplanner/${o.env}/lead-webhook-key`]);
  const v = String(out.SecretString || '').trim();
  if (!v || v === 'REPLACE_ME') throw new Error('the lead webhook master secret is empty: the webhook channel is off');
  return Buffer.from(v);
}

/** Open the agency's planner (the web ACL's silent challenge passes in the page) and check it is this agency's. */
async function openPlanner(page, o, base) {
  await page.goto(`${base}/${o.slug}/plan`, { waitUntil: 'domcontentloaded', timeout: 90_000 });
  const deadline = Date.now() + 90_000;
  const title = `Trip planner · ${o.agency}`;
  while (!(await page.title()).startsWith(title)) {
    if (Date.now() > deadline) throw new Error(`the planner title is not "${title}" (wrong slug or agency name?)`);
    await page.waitForTimeout(1000);
  }
}

/** One guest trip (one free day) and then `op` from inside the page: the planner's own BFF calls and cookies. */
async function tripCall(page, o, op) {
  return page.evaluate(async ({ slug, op }) => {
    const headers = { 'content-type': 'application/json', 'x-tp-tenant-slug': slug };
    const ids = { trip_id: crypto.randomUUID(), session_id: crypto.randomUUID() };
    const post = async (p, body) => {
      const r = await fetch(p, { method: 'POST', headers, credentials: 'same-origin', body: JSON.stringify({ ...ids, ...body }) });
      return { status: r.status, waf: r.headers.get('x-amzn-waf-action'), body: await r.json().catch(() => ({})) };
    };
    const day = await post('/api/trip', { op: 'add_day', kind: 'free_day' });
    if (day.status !== 200) return { step: 'add_day', ...day };
    return { step: op.op, ...(await post(op.path, op.body)) };
  }, { slug: o.slug, op });
}

async function main(argv) {
  const o = parseArgs(argv);
  const { chromium } = require('@playwright/test');
  const { HOSTS } = require('./lib/dryrun-page.cjs');
  const mailbox = require('./lib/mailbox.cjs');
  const run = crypto.randomBytes(4).toString('hex');
  const startedAt = Date.now();
  const report = { mode: o.mode, channel: o.channel, slug: o.slug, tenant_id: o.tenant, run, started_at: new Date(startedAt).toISOString(),
    checks: {}, ok: false };
  const outFile = o.out || path.join(__dirname, 'work', `tp-lead-proof-${o.mode}-${stamp()}.json`);
  const deadline = startedAt + o.timeoutS * 1000;
  const group = await logGroup(o);
  let receiver = null;
  let leadId = null;
  if (o.mode === 'lead' && o.channel === 'webhook') {
    receiver = listen(o, webhookKey(await webhookMaster(o), o.tenant),
      () => ({ leadId, travellerEmail: traveller(run).email }));
  }
  const browser = await chromium.launch({ headless: process.env.UAT_HEADED !== '1' });
  try {
    const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
    // $0: no search, no narration; the chat only in sessions-cap mode (its one refused turn).
    const blocked = ['/api/browse/search', '/api/trip/narrate', ...(o.mode === 'lead' ? ['/api/trip/chat'] : [])];
    await page.route((u) => blocked.some((p) => u.pathname === p) || /resource=search\b/.test(u.search), (r) => r.abort());
    await openPlanner(page, o, HOSTS.tripplanner);
    if (o.mode === 'lead') {
      const ans = await tripCall(page, o, { op: 'send', path: '/api/trip/send', body: { op: 'send', lead: leadBody(run) } });
      report.checks.send = { step: ans.step, status: ans.status, channel: ans.body && ans.body.lead ? ans.body.lead.channel : null };
      if (ans.status !== 200) throw new Error(`${ans.step} answered ${ans.status}${ans.waf ? ` (web ACL ${ans.waf})` : ''} ${ans.body.error || ''}`.trim());
      leadId = ans.body.lead && ans.body.lead.lead_id;
      if (!leadId || ans.body.lead.channel !== o.channel) throw new Error(`the lead went to channel ${report.checks.send.channel}, not ${o.channel}`);
      report.lead_id = leadId;
      report.handoff_id = ans.body.handoff_id;
      if (receiver) {
        const got = await Promise.race([receiver.result, new Promise((r) => setTimeout(() => r(null), Math.max(0, deadline - Date.now())))]);
        report.checks.webhook = got || { problems: ['no webhook POST arrived'] };
        if (!got || got.problems.length) throw new Error(`webhook: ${report.checks.webhook.problems.join('; ')}`);
      }
      if (o.channel === 'email') {
        const t = traveller(run);
        const raw = await mailbox.waitForMail({ recipient: o.leadEmail, prefix: o.mailPrefix, before: new Set(),
          since: new Date(startedAt), timeoutMs: Math.max(30_000, deadline - Date.now()),
          extract: (r) => (r.includes(leadId) ? r : null), what: 'lead e-mail' });
        const problems = leadMailProblems(raw, { mailbox, leadId, agency: o.agency, leadEmail: o.leadEmail, travellerEmail: t.email });
        report.checks.email = { problems };
        if (problems.length) throw new Error(`email: ${problems.join('; ')}`);
      }
      const line = await waitForLogLine(group, 'lead_delivered', o, startedAt, { channel: o.channel }, deadline);
      report.checks.lead_delivered_log = Boolean(line);
      if (!line) throw new Error(`no lead_delivered line (channel ${o.channel}) for the tenant within ${o.timeoutS} s`);
    } else {
      const ans = await tripCall(page, o, { op: 'chat', path: '/api/trip/chat', body: { op: 'chat', message: 'Hello', history: [] } });
      report.checks.chat = { step: ans.step, status: ans.status, answer: ans.body && ans.body.status, reason: ans.body && ans.body.reason };
      if (ans.status !== 200 || ans.body.status !== 'paused' || ans.body.reason !== 'budget') {
        throw new Error(`the chat was not stopped by the quota (${ans.step} ${ans.status} ${ans.body.status || ''} ${ans.body.reason || ''})`.trim());
      }
      const line = await waitForLogLine(group, 'tenant_ai_sessions_stop', o, startedAt, { reason: 'tenant_sessions_cap' }, deadline);
      report.checks.sessions_stop_log = Boolean(line);
      if (!line) throw new Error('no tenant_ai_sessions_stop line with reason tenant_sessions_cap for the tenant');
    }
    report.ok = true;
  } catch (e) {
    report.error = String(e.message || e).slice(0, 300);
  } finally {
    await browser.close();
    if (receiver) receiver.close();
    fs.mkdirSync(path.dirname(outFile), { recursive: true });
    fs.writeFileSync(outFile, `${JSON.stringify(report, null, 2)}\n`);
  }
  console.log(`${report.ok ? 'PASS' : 'FAIL'} ${o.mode}${o.channel ? ` ${o.channel}` : ''} ${report.ok ? '' : report.error} (${outFile})`.replace(/\s+\(/, ' ('));
  return report.ok ? 0 : 1;
}

module.exports = { parseArgs, traveller, leadBody, webhookKey, signatureOf, verifySignature, webhookProblems,
  decodeWords, splitAddress, leadMailProblems, findLogLine, pickLogGroup, SYNTHETIC, E2E_MAIL_DOMAIN };

if (require.main === module) {
  main(process.argv.slice(2)).then((code) => process.exit(code), (e) => {
    console.error(`FAIL ${String(e.message || e).slice(0, 300)}`);
    process.exit(1);
  });
}
