// Unit tests of the write caps of the UAT write scenarios (AA-1086 review): limitWrites counts and caps one method per
// rule (POST, PUT, PATCH or DELETE), and an allowWrites entry "<METHOD> <regex>" allows that method only (record.cjs and
// the Node-side request guard compile them through lib/net-guard.cjs). Also the preview stub of the free checks.
// No browser, no network:   node --test tools/uat/tests/*.test.cjs
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');

const guard = require('../lib/net-guard.cjs');
const { limitWrites, stubFreeChecksInPreview } = require('../lib/uat-page.cjs');

const ORIGIN = 'https://agency.example.invalid';

/** A fake page that keeps its routes in Playwright's order: the last registered matching handler runs first. */
function fakePage() {
  const routes = [];
  return {
    routes,
    route: async (match, handler) => { routes.unshift({ match, handler }); },
    /** Send one request through the page routes; returns 'continue' (left the page), 'abort' or 'fulfill'. */
    async send(method, pathname) {
      const u = new URL(`${ORIGIN}${pathname}`);
      for (const r of routes.filter((x) => x.match(u))) {
        let out = null;
        const route = {
          request: () => ({ method: () => method }),
          fallback: async () => { out = 'fallback'; },
          abort: async () => { out = 'abort'; },
          fulfill: async () => { out = 'fulfill'; },
        };
        await r.handler(route);
        if (out !== 'fallback') return out;
      }
      return 'continue';
    },
  };
}

test('limitWrites: a rule caps its own method only; reads and other methods fall through', async () => {
  const page = fakePage();
  const counts = await limitWrites(page, [
    { name: 'edit', path: /^\/pieces\/[^/]+$/, method: 'PATCH', max: 1 },
    { name: 'publish', path: /^\/log\/[^/]+\/publish$/, max: 2 }, // POST by default
    { name: 'unpublish', path: /^\/log\/[^/]+$/, method: 'delete', max: 1 },
  ]);
  assert.equal(await page.send('GET', '/pieces/a'), 'continue');
  assert.equal(await page.send('PATCH', '/pieces/a'), 'continue');
  assert.equal(await page.send('PATCH', '/pieces/a'), 'abort');
  // A DELETE / PUT / POST on the edit path is not this rule's: it goes on to the browser guard (which refuses it unless
  // allowWrites names that method), and it is not counted as an edit.
  assert.equal(await page.send('DELETE', '/pieces/a'), 'continue');
  assert.equal(await page.send('POST', '/pieces/a'), 'continue');
  assert.equal(await page.send('POST', '/log/a/publish'), 'continue');
  assert.equal(await page.send('POST', '/log/a/publish'), 'continue');
  assert.equal(await page.send('POST', '/log/a/publish'), 'abort');
  assert.equal(await page.send('DELETE', '/log/a'), 'continue');
  assert.equal(await page.send('DELETE', '/log/b'), 'abort');
  assert.deepEqual({ ...counts }, { edit: 2, publish: 3, unpublish: 2 });
});

test('limitWrites: max is read when a request arrives (a step may set it after a read); 0 refuses all', async () => {
  const page = fakePage();
  const rule = { name: 'unpublish', path: /^\/log\/[^/]+$/, method: 'DELETE', max: 0 };
  const counts = await limitWrites(page, [rule]);
  assert.equal(await page.send('DELETE', '/log/a'), 'abort');
  rule.max = 3; // e.g. the number of live posts read in step 1
  assert.equal(await page.send('DELETE', '/log/a'), 'continue');
  assert.equal(await page.send('DELETE', '/log/b'), 'continue');
  assert.equal(await page.send('DELETE', '/log/c'), 'abort');
  assert.equal(counts.unpublish, 4);
});

test('limitWrites: a rule with a read method is refused (it would cap nothing)', async () => {
  await assert.rejects(() => limitWrites(fakePage(), [{ name: 'x', path: /x/, method: 'GET', max: 1 }]), /GET is not a write/);
});

test('allowWrites: "<METHOD> <regex>" allows that method only; a bare regex any write method', () => {
  const allow = guard.compileAllow([
    'PATCH /api/tenant/v1/content-writing/pieces/[^/]+$',
    'DELETE /api/tenant/v1/publish-log/[^/]+$',
    '/api/tenant/v1/slate/refresh$',
  ]);
  const T = `${ORIGIN}/api/tenant/v1`;
  assert.ok(guard.allowMatches(allow, 'PATCH', `${T}/content-writing/pieces/p1`));
  assert.ok(guard.allowMatches(allow, 'patch', `${T}/content-writing/pieces/p1`));
  assert.ok(!guard.allowMatches(allow, 'DELETE', `${T}/content-writing/pieces/p1`));
  assert.ok(!guard.allowMatches(allow, 'POST', `${T}/content-writing/pieces/p1`));
  assert.ok(guard.allowMatches(allow, 'DELETE', `${T}/publish-log/l1`));
  assert.ok(!guard.allowMatches(allow, 'POST', `${T}/publish-log/l1`));
  assert.ok(!guard.allowMatches(allow, 'DELETE', `${T}/publish-log/l1/publish`));
  assert.ok(guard.allowMatches(allow, 'POST', `${T}/slate/refresh`));
  assert.ok(guard.allowMatches(allow, 'PUT', `${T}/slate/refresh`)); // a bare entry: any method (older scenarios)
  // A bare RegExp (older callers of guardRequestContext) still allows by URL.
  assert.ok(guard.allowMatches([/\/x$/], 'DELETE', `${ORIGIN}/x`));
  assert.deepEqual(guard.compileAllow([]), []);
  assert.deepEqual(guard.compileAllow(undefined), []);
});

test('record.cjs compiles allowWrites through net-guard for the browser route and the request API', () => {
  const src = require('fs').readFileSync(require('path').join(__dirname, '..', 'record.cjs'), 'utf8');
  assert.equal((src.match(/guard\.compileAllow\(sc\.allowWrites\)/g) || []).length, 2);
  assert.match(src, /guard\.allowMatches\(allow, req\.method\(\), url\)/);
  assert.doesNotMatch(src, /sc\.allowWrites \|\| \[\]\)\.map\(\(x\) => new RegExp\(x\)\)/);
});

test('guardRequestContext honours method entries: a DELETE on a PATCH-only path is refused', async () => {
  const sent = [];
  const blocked = [];
  const rq = { fetch: async (u, o) => { sent.push(`${(o && o.method) || 'GET'} ${u}`); return { ok: true }; } };
  guard.guardRequestContext(rq, { allow: guard.compileAllow(['PATCH /p/[^/]+$']), onBlocked: (m, u) => blocked.push(`${m} ${u}`) });
  await rq.fetch(`${ORIGIN}/p/1`, { method: 'PATCH' });
  await assert.rejects(() => rq.fetch(`${ORIGIN}/p/1`, { method: 'DELETE' }), /refused/);
  assert.deepEqual(sent, [`PATCH ${ORIGIN}/p/1`]);
  assert.deepEqual(blocked, [`DELETE ${ORIGIN}/p/1`]);
});

test('stubFreeChecksInPreview: answers the free check in the browser in a preview only', async () => {
  const before = process.env.UAT_PREVIEW;
  try {
    delete process.env.UAT_PREVIEW;
    const off = fakePage();
    assert.equal(await stubFreeChecksInPreview(off, [/^\/cta-check$/]), false);
    assert.equal(off.routes.length, 0);
    process.env.UAT_PREVIEW = '1';
    const on = fakePage();
    assert.equal(await stubFreeChecksInPreview(on, [/^\/cta-check$/]), true);
    assert.equal(await on.send('POST', '/cta-check'), 'fulfill');
    assert.equal(await on.send('GET', '/cta-check'), 'continue');
    assert.equal(await on.send('POST', '/other'), 'continue');
  } finally {
    if (before === undefined) delete process.env.UAT_PREVIEW; else process.env.UAT_PREVIEW = before;
  }
});
