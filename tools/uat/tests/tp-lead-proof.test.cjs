// Unit tests of the TripPlanner lead / AI sessions live proof (AA-1116, tools/uat/tp-lead-proof.cjs; root runbook
// docs/ops/runbooks/pilot-rehearsal.md step 6b, gap G14). No browser, no network, no AWS:
//   node --test tools/uat/tests/*.test.cjs
// Every name, address, id and key below is invented.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');

const proof = require('../tp-lead-proof.cjs');
const mailbox = require('../lib/mailbox.cjs');

const TENANT = '1a2b3c4d-5e6f-4a70-8b8c-9d0e1f2a3b4c';
const LEAD = '7a2b3c4d-5e6f-4a70-8b8c-9d0e1f2a3b4d';
const AGENCY = 'E2E Lantern Coast Travel';
const BASE = ['--slug', 'lantern-coast', '--tenant', TENANT, '--agency', AGENCY];

test('parseArgs: modes, channels and the synthetic-agency guard', () => {
  const a = proof.parseArgs(['lead', '--channel', 'crm', ...BASE]);
  assert.equal(a.mode, 'lead');
  assert.equal(a.channel, 'crm');
  assert.equal(a.webhookPort, 8787);
  assert.throws(() => proof.parseArgs(['lead', ...BASE]), /--channel/);
  assert.throws(() => proof.parseArgs(['send', ...BASE]), /first argument/);
  // a real agency's name never carries a synthetic marker word: refused before anything runs
  assert.throws(() => proof.parseArgs(['lead', '--channel', 'crm', '--slug', 'x', '--tenant', TENANT, '--agency', 'Lantern Coast Travel']),
    /pilot_guard/);
  assert.throws(() => proof.parseArgs(['lead', '--channel', 'crm', '--slug', 'x', '--tenant', 'not-a-uuid', '--agency', AGENCY]),
    /--tenant/);
  // e-mail leads only to the E2E inbound domain
  assert.throws(() => proof.parseArgs(['lead', '--channel', 'email', ...BASE, '--lead-email', 'desk@example.invalid']),
    /E2E mail domain/);
  const e = proof.parseArgs(['lead', '--channel', 'email', ...BASE, '--lead-email', 'Lead-Desk@E2E-mail.lumiguides.it.com']);
  assert.equal(e.leadEmail, 'lead-desk@e2e-mail.lumiguides.it.com');
  assert.throws(() => proof.parseArgs(['lead', '--channel', 'webhook', ...BASE, '--webhook-port', '80']), /--webhook-port/);
  // the sessions check runs only once the quota is known to be 0 (no model call)
  assert.throws(() => proof.parseArgs(['sessions-cap', ...BASE]), /--quota-zero/);
  assert.equal(proof.parseArgs(['sessions-cap', ...BASE, '--quota-zero']).quotaZero, true);
});

test('leadBody: the planner\'s LeadBody with an invented traveller and the contact consent', () => {
  const b = proof.leadBody('ab12cd34');
  assert.match(b.traveller.email, /@example\.invalid$/);
  assert.equal(b.consent.contact, true);
  assert.equal(b.consent.marketing, false);
  assert.deepEqual(b.party, { adults: 2, child_ages: [] });
});

function signed(master, body, t) {
  const key = proof.webhookKey(master, TENANT);
  return { key, header: `t=${t},v1=${proof.signatureOf(key, body, t)}` };
}

test('verifySignature: TripPlanner\'s X-AA-Signature over "<t>." + body with the tenant key', () => {
  const master = Buffer.from('invented-master-key');
  const body = Buffer.from('{"lead_id":"x"}');
  const { key, header } = signed(master, body, 1_700_000_000);
  // the tenant key is the hex text of HMAC(master, label + tenant), as TripPlanner's leads.webhook_key
  const want = crypto.createHmac('sha256', master).update(`aa-tripplanner lead webhook v1:${TENANT}`).digest('hex');
  assert.equal(key.toString('ascii'), want);
  assert.equal(proof.verifySignature(header, body, key, 1_700_000_100), null);
  assert.match(proof.verifySignature(header, body, key, 1_700_000_400), /more than 300 s/);
  assert.match(proof.verifySignature(header, Buffer.from('{"lead_id":"y"}'), key, 1_700_000_000), /does not match/);
  assert.match(proof.verifySignature('v1=abc', body, key, 1_700_000_000), /malformed/);
  assert.match(proof.verifySignature(header, body, proof.webhookKey(Buffer.from('other'), TENANT), 1_700_000_000), /does not match/);
});

test('webhookProblems: [] for the expected lead, every mismatch named', () => {
  const master = Buffer.from('invented-master-key');
  const lead = { lead_id: LEAD, idempotency_key: `lead.submitted:${LEAD}`, tenant: { tenant_id: TENANT },
    traveller: { email: 'lead-proof-ab12cd34@example.invalid' } };
  const body = Buffer.from(JSON.stringify(lead));
  const { key, header } = signed(master, body, 1_700_000_000);
  const headers = { 'x-aa-signature': header, 'x-aa-contract': 'lead.submitted.v1', 'idempotency-key': lead.idempotency_key };
  const expect = { key, nowS: 1_700_000_010, leadId: LEAD, tenantId: TENANT, travellerEmail: lead.traveller.email };
  assert.deepEqual(proof.webhookProblems(headers, body, expect), []);
  const wrong = proof.webhookProblems({ ...headers, 'x-aa-contract': 'other', 'idempotency-key': 'k' }, body,
    { ...expect, leadId: '00000000-0000-4000-8000-000000000000', travellerEmail: 'someone@example.invalid' });
  assert.equal(wrong.length, 4);
  assert.deepEqual(proof.webhookProblems(headers, Buffer.from('not json'), expect).slice(-1), ['the body is not JSON']);
});

function leadMail({ from = `${AGENCY} <planner@e2e-mail.lumiguides.it.com>`, replyTo = 'lead-proof-ab12cd34@example.invalid',
  text = `New trip request from your ${AGENCY} trip planner.\r\nLead ${LEAD}.` } = {}) {
  return [`From: ${from}`, 'To: lead-desk@e2e-mail.lumiguides.it.com', `Reply-To: ${replyTo}`,
    'Subject: Trip request: 1 day(s) in Laos', 'Content-Type: text/plain; charset=utf-8', '', text].join('\r\n');
}
const MAIL_EXPECT = { mailbox, leadId: LEAD, agency: AGENCY, leadEmail: 'lead-desk@e2e-mail.lumiguides.it.com',
  travellerEmail: 'lead-proof-ab12cd34@example.invalid' };

test('leadMailProblems: To the lead address, Reply-To the traveller, the agency as the sender\'s name', () => {
  assert.deepEqual(proof.leadMailProblems(leadMail(), MAIL_EXPECT), []);
  // the sender name RFC 2047 encoded (a non-ASCII trading name) and quoted forms decode to the name
  const encoded = `=?utf-8?b?${Buffer.from(AGENCY).toString('base64')}?= <planner@e2e-mail.lumiguides.it.com>`;
  assert.deepEqual(proof.leadMailProblems(leadMail({ from: encoded }), MAIL_EXPECT), []);
  assert.deepEqual(proof.leadMailProblems(leadMail({ from: `"${AGENCY}" <planner@e2e-mail.lumiguides.it.com>` }), MAIL_EXPECT), []);
  // AA's bare sender address (before the TripPlanner fix) is a failure
  const bare = proof.leadMailProblems(leadMail({ from: 'planner@e2e-mail.lumiguides.it.com' }), MAIL_EXPECT);
  assert.equal(bare.length, 1);
  assert.match(bare[0], /display name/);
  assert.match(proof.leadMailProblems(leadMail({ replyTo: 'other@example.invalid' }), MAIL_EXPECT)[0], /Reply-To/);
  assert.match(proof.leadMailProblems(leadMail({ text: 'no id here' }), MAIL_EXPECT).join(';'), /lead id/);
});

test('decodeWords / splitAddress', () => {
  assert.equal(proof.decodeWords('=?utf-8?b?RHUgbOG7i2No?='), 'Du lịch');
  assert.equal(proof.decodeWords('=?UTF-8?Q?Du_l=E1=BB=8Bch?='), 'Du lịch');
  assert.deepEqual(proof.splitAddress('"Lantern, \\"Coast\\"" <A@Example.invalid>'),
    { name: 'Lantern, "Coast"', address: 'a@example.invalid' });
  assert.deepEqual(proof.splitAddress('a@example.invalid'), { name: '', address: 'a@example.invalid' });
});

test('findLogLine: the JSON line of observability.emit for this tenant, with the extra fields', () => {
  const lines = [
    'START RequestId: 1',
    JSON.stringify({ evt: 'lead_delivered', channel: 'email', tenant_id: TENANT }),
    `2026-11-18T00:00:00Z ${JSON.stringify({ evt: 'lead_delivered', channel: 'crm', tenant_id: TENANT })}`,
    JSON.stringify({ evt: 'lead_delivered', channel: 'crm', tenant_id: '00000000-0000-4000-8000-000000000000' }),
  ];
  assert.equal(proof.findLogLine(lines, 'lead_delivered', TENANT, { channel: 'crm' }).channel, 'crm');
  assert.equal(proof.findLogLine(lines, 'lead_delivered', TENANT, { channel: 'webhook' }), null);
  assert.equal(proof.findLogLine(['{"evt":"tenant_ai_sessions_stop","reason":"tenant_sessions_cap","tenant_id":"' + TENANT + '"}'],
    'tenant_ai_sessions_stop', TENANT, { reason: 'tenant_sessions_cap' }).reason, 'tenant_sessions_cap');
});

test('pickLogGroup: the one TripPlanner assembly group of the environment', () => {
  const names = ['/aws/lambda/aa-tripplanner-dev-assembly', '/aws/lambda/aa-tripplanner-dev-browse',
    '/aws/lambda/aa-tripplanner-stg-assembly', '/aws/lambda/aa-cis-dev-thing'];
  assert.equal(proof.pickLogGroup(names, 'dev'), '/aws/lambda/aa-tripplanner-dev-assembly');
  assert.equal(proof.pickLogGroup(names, 'prod'), null);
});
