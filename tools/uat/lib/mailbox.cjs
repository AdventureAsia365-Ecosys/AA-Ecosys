// E2E mailbox reader for staff sign-in codes (AA-1009 dry run; CommonJS copy of AA-CIS-App
// tests/e2e/helpers/mailbox.ts, as AA-Booking frontend/e2e/SIGNED-IN-SMOKE.md asks: copy, do not import across repos).
// Cognito mails a one-time code to an e2e address of the SES inbound test domain -> S3 bucket
// aa-cis-dev-e2e-mail-<account>, prefix inbound/ (CIS reviewer, Booking E2E staff) or inbound-admin/ (Dev-only E2E CIS
// admin, readable by the MFA admin role only). Read only (list + get through the AWS CLI, profile UAT_AWS_PROFILE or
// aa365-admin); the bucket lifecycle deletes. The code is a live credential: never logged, printed or written.
//   const mb = require('./mailbox.cjs');
//   const before = await mb.baseline('inbound/');  ...ask for a code...  const code = await mb.waitForCode({ ... });
'use strict';
const { execFile } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { promisify } = require('util');

const run = promisify(execFile);
const PROFILE = process.env.UAT_AWS_PROFILE || 'aa365-admin';
const REGION = 'us-west-1';
const BUCKET_PREFIX = 'aa-cis-dev-e2e-mail-';
const CLI_TIMEOUT_MS = 20_000;
const POLL_MS = 3_000;
const CLOCK_SKEW_MS = 60_000;
const MAX_BYTES = 1_000_000;
const RECIPIENT_HEADERS = ['to', 'cc', 'delivered-to', 'x-original-to', 'x-forwarded-to', 'envelope-to'];

async function aws(args) {
  try {
    const { stdout } = await run('aws', [...args, '--profile', PROFILE, '--region', REGION, '--output', 'json'],
      { timeout: CLI_TIMEOUT_MS, maxBuffer: 16 * 1024 * 1024 });
    return stdout;
  } catch (e) {
    // stderr carries AccessDenied / ExpiredToken, never a message body.
    throw new Error(`aws ${args.slice(0, 2).join(' ')} failed: ${String(e.stderr || e.message || e).trim().split('\n')[0]}`);
  }
}

let bucketName = null;
async function bucket() {
  if (!bucketName) {
    const account = String(JSON.parse(await aws(['sts', 'get-caller-identity'])).Account || '');
    if (!/^\d{12}$/.test(account)) throw new Error('sts get-caller-identity returned no account');
    bucketName = `${BUCKET_PREFIX}${account}`;
  }
  return bucketName;
}

async function list(prefix) {
  const out = await aws(['s3api', 'list-objects-v2', '--bucket', await bucket(), '--prefix', prefix]);
  return ((out.trim() ? JSON.parse(out) : {}).Contents || [])
    .map((o) => ({ key: o.Key, lastModified: new Date(o.LastModified), size: o.Size }));
}

async function read(key) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'uat-mail-'));
  try {
    const file = path.join(dir, 'm.eml');
    await aws(['s3api', 'get-object', '--bucket', await bucket(), '--key', key, file]);
    return fs.readFileSync(file, 'utf8');
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

// ── MIME (just enough for a Cognito code mail) ──
function splitHeadBody(raw) {
  const m = /\r?\n\r?\n/.exec(raw);
  return m ? { head: raw.slice(0, m.index), body: raw.slice(m.index + m[0].length) } : { head: raw, body: '' };
}

function parseHeaders(head) {
  const h = new Map();
  for (const line of head.replace(/\r?\n[ \t]+/g, ' ').split(/\r?\n/)) {
    const i = line.indexOf(':');
    if (i <= 0) continue;
    const k = line.slice(0, i).trim().toLowerCase();
    h.set(k, [...(h.get(k) || []), line.slice(i + 1).trim()]);
  }
  return h;
}

function param(v, name) {
  const m = new RegExp(`(?:^|;)\\s*${name}\\s*=\\s*(?:"([^"]*)"|([^;\\s]+))`, 'i').exec(v);
  return m ? (m[1] !== undefined ? m[1] : m[2]) : undefined;
}

function decode(body, cte, charset) {
  const enc = (cte || '').toLowerCase();
  let buf;
  if (enc === 'base64') buf = Buffer.from(body.replace(/\s+/g, ''), 'base64');
  else if (enc === 'quoted-printable') {
    const soft = body.replace(/=\r?\n/g, '');
    const bytes = [];
    for (let i = 0; i < soft.length; i++) {
      if (soft[i] === '=' && /^[0-9A-Fa-f]{2}$/.test(soft.slice(i + 1, i + 3))) { bytes.push(parseInt(soft.slice(i + 1, i + 3), 16)); i += 2; } else bytes.push(...Buffer.from(soft[i], 'utf8'));
    }
    buf = Buffer.from(bytes);
  } else return body;
  const cs = (charset || 'utf-8').toLowerCase();
  return buf.toString(['iso-8859-1', 'latin1', 'us-ascii'].includes(cs) ? 'latin1' : 'utf8');
}

function htmlToText(html) {
  const ent = { nbsp: ' ', amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", '#39': "'" };
  return html.replace(/<(style|script|head)\b[\s\S]*?<\/\1>/gi, ' ')
    .replace(/<br\s*\/?>|<\/(p|div|tr|td|h\d|li)>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&(#\d+|#x[0-9a-f]+|[a-z]+);/gi, (w, e) => {
      const k = e.toLowerCase();
      if (k in ent) return ent[k];
      const cp = k.startsWith('#x') ? parseInt(k.slice(2), 16) : k.startsWith('#') ? parseInt(k.slice(1), 10) : NaN;
      return cp >= 0 && cp <= 0x10ffff ? String.fromCodePoint(cp) : w;
    })
    .replace(/[ \t ]+/g, ' ');
}

/** Decoded text bodies: plain parts first, HTML parts (as text) after. */
function textBodies(raw) {
  const plain = [];
  const html = [];
  const walk = (part, depth) => {
    if (depth > 8) return;
    const { head, body } = splitHeadBody(part);
    const h = parseHeaders(head);
    const ct = (h.get('content-type') || ['text/plain'])[0];
    const type = ct.split(';')[0].trim().toLowerCase();
    if (type.startsWith('multipart/')) {
      const b = param(ct, 'boundary');
      if (!b) return;
      for (const chunk of body.split(`--${b}`).slice(1)) {
        if (chunk.startsWith('--')) break;
        walk(chunk.replace(/^[ \t]*\r?\n/, ''), depth + 1);
      }
      return;
    }
    if (type === 'message/rfc822') { walk(body, depth + 1); return; }
    if (!type.startsWith('text/')) return;
    const text = decode(body, (h.get('content-transfer-encoding') || ['7bit'])[0], param(ct, 'charset'));
    if (type === 'text/html') html.push(htmlToText(text)); else plain.push(text);
  };
  walk(raw, 0);
  return [...plain, ...html];
}

/** True when a recipient-carrying header of the top-level message names `address`. */
function isAddressedTo(raw, address) {
  const h = parseHeaders(splitHeadBody(raw).head);
  const needle = address.toLowerCase();
  return RECIPIENT_HEADERS.some((k) => (h.get(k) || []).some((v) => v.toLowerCase().includes(needle)));
}

/**
 * The 6-8 digit code in the bodies (never the headers): a number shortly after the word "code", else the single
 * distinct standalone 6-8 digit number (a # before it is a CSS colour). Null when ambiguous.
 */
function extractCode(raw) {
  const bodies = textBodies(raw);
  for (const t of bodies) {
    const m = /\bcode\b[^0-9]{0,80}?(?<![\d#])(\d{6,8})(?!\d)/i.exec(t);
    if (m) return m[1];
  }
  for (const t of bodies) {
    const all = new Set([...t.matchAll(/(?<![\d#\w])(\d{6,8})(?![\d\w])/g)].map((x) => x[1]));
    if (all.size === 1) return [...all][0];
  }
  return null;
}

/** The keys under `prefix` before the code is asked for (never read again). */
async function baseline(prefix) {
  return new Set((await list(prefix)).map((o) => o.key));
}

/**
 * Poll `prefix` until a NEW message (not in `before`, written after `since`) to `recipient` yields a code.
 * Hard cap `timeoutMs` (default 90 s). The error never carries mail content.
 */
async function waitForCode({ recipient, prefix, before, since, timeoutMs = 90_000 }) {
  const deadline = Date.now() + timeoutMs;
  const notBefore = since.getTime() - CLOCK_SKEW_MS;
  const checked = new Set(before);
  let lastError = '';
  while (Date.now() < deadline) {
    try {
      const fresh = (await list(prefix))
        .filter((o) => !checked.has(o.key) && o.lastModified.getTime() >= notBefore && o.size <= MAX_BYTES)
        .sort((a, b) => b.lastModified - a.lastModified);
      for (const o of fresh) {
        const raw = await read(o.key);
        checked.add(o.key);
        if (!isAddressedTo(raw, recipient)) continue;
        const code = extractCode(raw);
        if (code) return code;
      }
      lastError = '';
    } catch (e) {
      lastError = String(e.message || e);
    }
    await new Promise((r) => setTimeout(r, Math.min(POLL_MS, Math.max(0, deadline - Date.now()))));
  }
  throw new Error(`no sign-in code for ${recipient} under ${prefix} within ${Math.round(timeoutMs / 1000)} s${lastError ? ` (${lastError})` : ''}`);
}

module.exports = { baseline, waitForCode, extractCode, isAddressedTo, textBodies, parseHeaders };
