// Unit tests of the write allow-lists of the writing UAT scenarios (AA-855): each allowWrites entry is compiled the way
// record.cjs compiles it (new RegExp(source), tested on the full URL) and must match its intended request, and nothing
// else. No browser, no network:   node --test tools/uat/tests/*.test.cjs
// Ids in the URLs are invented.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');

const ORIGIN = 'https://agency.example.invalid';
const ID = '0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d'; // invented
const load = (rel) => require(path.join(__dirname, '..', 'scenarios', 'content-studio', rel));
const allowed = (sc, url) => (sc.allowWrites || []).map((x) => new RegExp(x)).some((r) => r.test(url));

/** Every entry matches at least one of `intended`, every intended URL is allowed, every `refused` URL is not. */
function assertAllowList(sc, intended, refused) {
  for (const src of sc.allowWrites) {
    assert.ok(intended.some((u) => new RegExp(src).test(u)), `${sc.id}: allowWrites entry ${src} matches none of its URLs`);
  }
  for (const u of intended) assert.ok(allowed(sc, u), `${sc.id}: ${u} should be allowed`);
  for (const u of refused) assert.ok(!allowed(sc, u), `${sc.id}: ${u} should be refused`);
}

test('PRT-06: pick, goal / choose and the one write are allowed; nothing else (the write path is not escaped twice)', () => {
  const sc = load('prt-06.cjs');
  const T = `${ORIGIN}/api/tenant/v1`;
  assertAllowList(sc, [
    `${T}/subjects/${ID}/pick`,
    `${T}/angle-gate/requests/${ID}/goal`,
    `${T}/angle-gate/requests/${ID}/choose`,
    `${T}/content-writing/requests/${ID}/write`,
  ], [
    `${T}/content-writing/requests/${ID}/regenerate`,
    `${T}/content-writing/requests/${ID}/write/extra`,
    `${T}/angle-gate/requests/${ID}/reset`,
    `${ORIGIN}/api/tenant/admin/brand-identity`,
    `${T}\\/content-writing/requests/${ID}/write`,
  ]);
  for (const src of sc.allowWrites) assert.ok(!src.includes('\\\\/'), `${src}: a doubled escape matches a literal backslash`);
});

test('PRT-02: only the brand save is allowed', () => {
  assertAllowList(load('prt-02.cjs'), [`${ORIGIN}/api/tenant/admin/brand-identity`],
    [`${ORIGIN}/api/tenant/admin/brand-identity/versions`, `${ORIGIN}/api/tenant/v1/subjects/${ID}/pick`]);
});

test('PRT-14: only the language cookie is allowed', () => {
  assertAllowList(load('prt-14.cjs'), [`${ORIGIN}/prefs/locale`],
    [`${ORIGIN}/prefs/locale/x`, `${ORIGIN}/api/tenant/admin/brand-identity`]);
});

test('PRT-06: a page route in front of the guard lets the first write through and aborts any later one', async () => {
  const sc = load('prt-06.cjs');
  let handler = null;
  let predicate = null;
  const page = { route: async (p, hnd) => { predicate = p; handler = hnd; }, on: () => {} };
  // Stop step 1 right after it registers its route: check() is the next call and needs a real page.
  const h = { goto: async () => { throw new Error('stop'); }, expect: () => { throw new Error('stop'); } };
  await assert.rejects(() => sc.steps[0].run(page, h));
  assert.ok(handler, 'step 1 registers a page route');
  const u = (p) => new URL(`${ORIGIN}${p}`);
  assert.equal(predicate(u(`/api/tenant/v1/content-writing/requests/${ID}/write`)), true);
  assert.equal(predicate(u(`/api/tenant/v1/subjects/${ID}/pick`)), false);
  const seen = [];
  const route = (method) => ({
    request: () => ({ method: () => method }),
    fallback: async () => seen.push('fallback'),
    abort: async (code) => seen.push(`abort:${code}`),
  });
  await handler(route('GET'));
  await handler(route('POST'));
  await handler(route('POST'));
  await handler(route('POST'));
  assert.deepEqual(seen, ['fallback', 'fallback', 'abort:blockedbyclient', 'abort:blockedbyclient']);
});
