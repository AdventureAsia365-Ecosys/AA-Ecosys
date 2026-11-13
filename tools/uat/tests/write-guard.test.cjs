// Unit tests of the two write guards of the writing UAT scenarios (AA-1086 review): allowWrites entries that name their
// method (lib/net-guard.cjs parseAllow / compileAllow / allowsWrite, used by record.cjs for the browser and the request
// API) and the per-rule cap of lib/uat-page.cjs limitWrites for every write method, not only POST.
// No browser, no network:  node --test tools/uat/tests/*.test.cjs   (URLs and ids invented)
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const guard = require('../lib/net-guard.cjs');
const { limitWrites } = require('../lib/uat-page.cjs');

const ORIGIN = 'https://agency.example.invalid';

test('parseAllow: a leading method list is split off; a plain source admits every write method (the original form)', () => {
  const a = guard.parseAllow(`POST ^${ORIGIN}/bff/x$`);
  assert.deepEqual(a.methods, ['POST']);
  assert.equal(a.re.source, `^${ORIGIN}/bff/x$`.replace(/\//g, '\\/'));
  assert.deepEqual(guard.parseAllow('PUT|PATCH ^/y$').methods, ['PUT', 'PATCH']);
  assert.equal(guard.parseAllow('^/y$').methods, null);
  // Only write methods count as a prefix: anything else stays part of the regex source.
  assert.equal(guard.parseAllow('GET ^/y$').methods, null);
  assert.equal(guard.parseAllow('post ^/y$').methods, null);
});

test('allowsWrite: method and URL must both match; RegExp items and plain sources admit any method', () => {
  const allow = guard.compileAllow([`POST ^${ORIGIN}/bff/trips/1/owner$`, `PATCH ^${ORIGIN}/bff/trips/1$`, '^https://other\\.invalid/x$', /\/legacy$/]);
  assert.ok(guard.allowsWrite(allow, 'POST', `${ORIGIN}/bff/trips/1/owner`));
  assert.ok(guard.allowsWrite(allow, 'post', `${ORIGIN}/bff/trips/1/owner`));
  assert.ok(!guard.allowsWrite(allow, 'DELETE', `${ORIGIN}/bff/trips/1/owner`));
  assert.ok(guard.allowsWrite(allow, 'PATCH', `${ORIGIN}/bff/trips/1`));
  assert.ok(!guard.allowsWrite(allow, 'DELETE', `${ORIGIN}/bff/trips/1`));
  assert.ok(guard.allowsWrite(allow, 'DELETE', 'https://other.invalid/x'));
  assert.ok(guard.allowsWrite(allow, 'PUT', 'https://z.invalid/legacy'));
  assert.ok(!guard.allowsWrite(allow, 'POST', `${ORIGIN}/bff/trips/2/owner`));
});

test('guardRequestContext: a scenario request call is refused when its method is not the allowed one', async () => {
  const sent = [];
  const blocked = [];
  const rq = { fetch: async (u, o = {}) => { sent.push(`${o.method || 'GET'} ${u}`); return { ok: true }; } };
  guard.guardRequestContext(rq, { allow: guard.compileAllow([`POST ^${ORIGIN}/bff/x$`]), onBlocked: (m, u) => blocked.push(`${m} ${u}`) });
  await rq.fetch(`${ORIGIN}/bff/x`, { method: 'POST' });
  await rq.fetch(`${ORIGIN}/bff/x`);
  await assert.rejects(rq.fetch(`${ORIGIN}/bff/x`, { method: 'DELETE' }), /read-only run/);
  assert.deepEqual(sent, [`POST ${ORIGIN}/bff/x`, `GET ${ORIGIN}/bff/x`]);
  assert.deepEqual(blocked, [`DELETE ${ORIGIN}/bff/x`]);
});

/** A fake page that keeps the routes limitWrites registers; fire() plays one request through them, newest first. */
function fakePage() {
  const routes = [];
  const seen = [];
  const page = { route: async (pred, handler) => routes.push({ pred, handler }) };
  const fire = async (p, method) => {
    const matching = routes.filter((x) => x.pred(new URL(`${ORIGIN}${p}`))).reverse(); // Playwright: last registered first
    for (const r of matching) {
      let fell = false;
      await r.handler({ request: () => ({ method: () => method }), fallback: async () => { fell = true; },
        abort: async (code) => seen.push(`abort ${method} ${p} ${code}`) });
      if (!fell) return;
    }
    seen.push(`go ${method} ${p}`);
  };
  return { page, seen, fire };
}

test('limitWrites: PUT, PATCH and DELETE rules cap their own method; POST stays the default; reads pass', async () => {
  const { page, seen, fire } = fakePage();
  const counts = await limitWrites(page, [
    { name: 'create', path: /^\/x$/, max: 1 },
    { name: 'edit', path: /^\/x$/, method: 'PATCH', max: 1 },
    { name: 'save', path: /^\/y$/, method: ['PUT', 'delete'], max: 1 },
    { name: 'any', path: /^\/z$/, method: '*', max: 2 },
  ]);
  await fire('/x', 'GET');
  await fire('/x', 'POST');
  await fire('/x', 'POST');
  await fire('/x', 'PATCH');
  await fire('/x', 'PATCH');
  await fire('/x', 'DELETE'); // no rule caps DELETE on /x: it goes on to the browser guard (which refuses it unless allowed)
  await fire('/y', 'PUT');
  await fire('/y', 'DELETE');
  await fire('/z', 'POST');
  await fire('/z', 'PUT');
  await fire('/z', 'DELETE');
  await fire('/z', 'HEAD');
  assert.deepEqual(seen, [
    'go GET /x', 'go POST /x', 'abort POST /x blockedbyclient', 'go PATCH /x', 'abort PATCH /x blockedbyclient', 'go DELETE /x',
    'go PUT /y', 'abort DELETE /y blockedbyclient',
    'go POST /z', 'go PUT /z', 'abort DELETE /z blockedbyclient', 'go HEAD /z',
  ]);
  assert.deepEqual(counts, { create: 2, edit: 2, save: 2, any: 3 });
});

test('limitWrites: a rule naming a read method is refused (it would cap nothing)', async () => {
  await assert.rejects(limitWrites({ route: async () => {} }, [{ name: 'r', path: /x/, method: 'GET', max: 1 }]), /method must be/);
});
