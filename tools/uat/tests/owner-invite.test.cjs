// Unit tests of the owner invitation acceptance (AA-1086, root docs/ops/runbooks/pilot-rehearsal.md step 2): the
// invitation link read from an e2e mail (lib/mailbox.cjs extractInviteLink) and the argument / link checks of
// tools/uat/accept-owner-invite.cjs. No browser, no network, no AWS:   node --test tools/uat/tests/*.test.cjs
// The token and the addresses below are invented.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');

const mailbox = require('../lib/mailbox.cjs');
const inv = require('../accept-owner-invite.cjs');

const TOKEN = 'AbCdEfGhIjKlMnOpQrStUvWxYz0123456789_-AbCdE'; // 43 characters, invented
const LINK = `https://portal.lumiguides.it.com/join?t=${TOKEN}`;

function mail(body, { cte = '7bit', type = 'text/plain' } = {}) {
  return ['From: AA <no-reply@example.invalid>', 'To: e2e-owner@e2e-mail.example.invalid', 'Subject: You are invited',
    `Content-Type: ${type}; charset=utf-8`, `Content-Transfer-Encoding: ${cte}`, '', body].join('\r\n');
}

test('extractInviteLink: the join link from a plain, a quoted-printable and an HTML mail', () => {
  assert.equal(TOKEN.length, 43);
  assert.equal(mailbox.extractInviteLink(mail(`Open your invitation: ${LINK}\r\nThanks`)), LINK);
  // Quoted-printable: a soft line break inside the link and "=" written as =3D.
  const enc = LINK.replace('=', '=3D');
  const qp = `Open: ${enc.slice(0, 50)}=\r\n${enc.slice(50)}\r\n`;
  assert.equal(mailbox.extractInviteLink(mail(qp, { cte: 'quoted-printable' })), LINK);
  assert.equal(mailbox.extractInviteLink(mail(`<p><a href="${LINK}">Open invitation</a></p>`, { type: 'text/html' })), LINK);
  assert.equal(mailbox.isAddressedTo(mail('x'), 'E2E-OWNER@e2e-mail.example.invalid'), true);
});

test('extractInviteLink: no link, a short token or a longer one -> null', () => {
  assert.equal(mailbox.extractInviteLink(mail('Your code is 123456')), null);
  assert.equal(mailbox.extractInviteLink(mail(`https://portal.lumiguides.it.com/join?t=${TOKEN.slice(1)}`)), null);
  assert.equal(mailbox.extractInviteLink(mail(`https://portal.lumiguides.it.com/join?t=${TOKEN}X`)), null);
  assert.equal(mailbox.extractInviteLink(mail(`http://portal.lumiguides.it.com/join?t=${TOKEN}`)), null);
});

test('accept-owner-invite: --since is required, in the past; identity limited to the rehearsal owner', () => {
  const since = '2026-11-13T09:00:00Z';
  const a = inv.parseArgs(['--since', since]);
  assert.equal(a.identity, 'studio-rehearsal');
  assert.equal(a.since.toISOString(), '2026-11-13T09:00:00.000Z');
  assert.equal(a.readyMin, 5);
  assert.equal(inv.parseArgs(['--since', since, '--ready-min', '10']).readyMin, 10);
  assert.throws(() => inv.parseArgs([]), /--since/);
  assert.throws(() => inv.parseArgs(['--since', 'yesterday']), /--since/);
  assert.throws(() => inv.parseArgs(['--since', new Date(Date.now() + 3_600_000).toISOString()]), /future/);
  assert.throws(() => inv.parseArgs(['--since', since, '--identity', 'studio-audit']), /--identity must be one of studio-rehearsal/);
  assert.throws(() => inv.parseArgs(['--since', since, '--ready-min', '0']), /ready-min/);
  assert.throws(() => inv.parseArgs(['--since']), /needs a value/);
  assert.throws(() => inv.parseArgs(['--since', since, '--x']), /unknown argument/);
  assert.deepEqual(Object.keys(inv.OWNER_INVITEES), ['studio-rehearsal']);
});

test('accept-owner-invite: the link must be the https /join page of an AA Dev host (the token goes nowhere else)', () => {
  assert.equal(inv.joinOrigin(LINK), 'https://portal.lumiguides.it.com');
  for (const bad of [`http://portal.lumiguides.it.com/join?t=${TOKEN}`, `https://evil.example.invalid/join?t=${TOKEN}`,
    `https://lumiguides.it.com.evil.invalid/join?t=${TOKEN}`, `https://portal.lumiguides.it.com/other?t=${TOKEN}`, 'not a url']) {
    assert.throws(() => inv.joinOrigin(bad), /invitation link/, bad);
  }
});

test('accept-owner-invite: never prints the link, the token, the address or a code', () => {
  const src = require('fs').readFileSync(require('path').join(__dirname, '..', 'accept-owner-invite.cjs'), 'utf8');
  for (const line of src.split('\n').filter((l) => /console\.(log|error)/.test(l))) {
    assert.doesNotMatch(line, /\b(link|creds|email|password|totp)\b/, line.trim());
  }
});
