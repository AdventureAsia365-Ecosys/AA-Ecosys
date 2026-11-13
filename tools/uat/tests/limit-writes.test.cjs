// Unit tests of limitWrites (lib/uat-page.cjs): every write method on a rule's path is capped, not only POST.
// No browser, no network:   node --test tools/uat/tests/*.test.cjs
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { limitWrites } = require('../lib/uat-page.cjs');

const ORIGIN = 'https://booking.example.invalid';

/** A fake page that keeps the routes; fire(path, method) runs the first matching handler and logs what it did. */
async function harness(rules) {
  const routes = [];
  const page = { route: async (pred, handler) => routes.push({ pred, handler }) };
  const counts = await limitWrites(page, rules);
  const seen = [];
  const fire = async (p, method) => {
    const r = routes.find((x) => x.pred(new URL(`${ORIGIN}${p}`)));
    if (!r) { seen.push(`none ${method} ${p}`); return; }
    await r.handler({ request: () => ({ method: () => method }), fallback: async () => seen.push(`go ${method} ${p}`),
      abort: async (code) => seen.push(`abort ${method} ${p} ${code}`) });
  };
  return { counts, seen, fire };
}

test('limitWrites: PUT, PATCH and DELETE on a POST rule are aborted and counted; reads pass uncounted', async () => {
  const first = await harness([{ name: 'record', path: /^\/x\/payments$/, max: 1 }]);
  await first.fire('/x/payments', 'POST');
  await first.fire('/x/payments', 'POST');
  assert.deepEqual(first.seen, ['go POST /x/payments', 'abort POST /x/payments blockedbyclient']);

  const { counts, seen, fire } = await harness([{ name: 'record', path: /^\/x\/payments$/, max: 1 }]);
  for (const m of ['GET', 'HEAD', 'OPTIONS']) await fire('/x/payments', m);
  await fire('/x/payments', 'DELETE');
  await fire('/x/payments', 'patch');
  await fire('/x/payments', 'PUT');
  await fire('/x/payments', 'POST');
  await fire('/x/payments', 'POST');
  assert.deepEqual(seen, [
    'go GET /x/payments', 'go HEAD /x/payments', 'go OPTIONS /x/payments',
    'abort DELETE /x/payments blockedbyclient', 'abort patch /x/payments blockedbyclient',
    'abort PUT /x/payments blockedbyclient',
    // a stray method uses up the rule's slots too (fail closed): the POSTs after it are aborted as well
    'abort POST /x/payments blockedbyclient', 'abort POST /x/payments blockedbyclient',
  ]);
  assert.deepEqual(counts, { record: 5 });
});

test('limitWrites: a rule with method PATCH (or DELETE) caps that method and refuses the others', async () => {
  const { counts, seen, fire } = await harness([
    { name: 'edit', path: /^\/x\/pieces\/1$/, max: 1, method: 'PATCH' },
    { name: 'unpublish', path: /^\/x\/log\/1$/, max: 1, method: 'delete' },
  ]);
  await fire('/x/pieces/1', 'PATCH');
  await fire('/x/pieces/1', 'PATCH');
  await fire('/x/pieces/1', 'POST');
  await fire('/x/log/1', 'DELETE');
  await fire('/x/log/1', 'DELETE');
  await fire('/x/other', 'POST');
  assert.deepEqual(seen, [
    'go PATCH /x/pieces/1', 'abort PATCH /x/pieces/1 blockedbyclient', 'abort POST /x/pieces/1 blockedbyclient',
    'go DELETE /x/log/1', 'abort DELETE /x/log/1 blockedbyclient', 'none POST /x/other',
  ]);
  assert.deepEqual(counts, { edit: 3, unpublish: 2 });
});
