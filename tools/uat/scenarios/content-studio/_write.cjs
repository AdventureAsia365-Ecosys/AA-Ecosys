// Shared parts of the write scenarios W-01..W-04 (AA-855 round 1): the studio-audit identity on this run's audit tenant
// (lib/studio-audit.cjs, env UAT_STUDIO_TENANT), the studio API paths they use, and the reads that pick an unused
// subject or find the piece the previous scenario left (lib/write-chain.cjs). Not a scenario (leading underscore).
'use strict';
const { studioCall } = require('../../lib/uat-page.cjs');
const chain = require('../../lib/write-chain.cjs');
const { auditTenant } = require('../../lib/studio-audit.cjs');

const T = '/api/tenant/v1';
// Pathname patterns of the writes the scenarios make (each one limited to one POST per run, lib/uat-page.cjs).
const PATHS = {
  rewrite: /^\/api\/tenant\/v1\/tours\/pool\/[^/]+\/rewrite$/,
  refresh: /^\/api\/tenant\/v1\/slate\/refresh$/,
  pick: /^\/api\/tenant\/v1\/subjects\/[^/]+\/pick$/,
  goal: /^\/api\/tenant\/v1\/angle-gate\/requests\/[^/]+\/goal$/,
  choose: /^\/api\/tenant\/v1\/angle-gate\/requests\/[^/]+\/choose$/,
  write: /^\/api\/tenant\/v1\/content-writing\/requests\/[^/]+\/write$/,
};
// The same writes as allowWrites sources: record.cjs tests them on the full URL (origin + path, no query).
const allow = (...names) => names.map((n) => `${PATHS[n].source.replace(/^\^/, '')}`);

const isPost = (res, re) => res.request().method() === 'POST' && re.test(new URL(res.url()).pathname);

/** The tour the editor rewrites: the first one on the catalog page that is not in My Tours and is still sold. */
function freeTour(pool) {
  const rows = pool && Array.isArray(pool.data) ? pool.data : [];
  return rows.find((t) => t && t.id && t.tour_id && t.aa_name && !t.already_rewritten && !t.served_notice
    && (!t.served_status || t.served_status === 'served')) || null;
}

// Invented call to action, typed only when the brand has none (the studio then asks for one: POST .../write 422).
const CTA = 'Ask us to plan this journey with you';

/**
 * The studio asked for a call to action (POST .../write answered 422: none on the request or the brand): the editor
 * types CTA in the field it shows and presses Write content. Returns that second write's response.
 * `scope` = the page or the locator the wizard renders in.
 */
async function typeCtaAndWrite(page, h, scope) {
  const field = scope.getByPlaceholder(/Book a consultation/);
  await h.expect(field).toBeVisible({ timeout: 30_000 });
  await h.click(field);
  await field.fill(CTA);
  const again = page.waitForResponse((r) => isPost(r, PATHS.write), { timeout: 120_000 });
  await h.click(scope.getByRole('button', { name: 'Write content' }));
  return again;
}

/**
 * Start the write and wait for its 202, the way the studio does it: the first POST .../write (fired by `start`), and
 * on 422 typeCtaAndWrite(). Returns the 202 body (the placeholder piece).
 */
async function startWrite(page, h, scope, start) {
  const first = page.waitForResponse((r) => isPost(r, PATHS.write), { timeout: 120_000 });
  await start();
  let res = await first;
  if (res.status() === 422) res = await typeCtaAndWrite(page, h, scope);
  if (res.status() !== 202) throw new Error(`starting the article answered ${res.status()}`);
  return res.json();
}

/** My Content's rows (the page's own list read, GET only). */
async function reviews(page) {
  const r = await studioCall(page, 'GET', `${T}/content-writing/reviews`);
  if (r.status !== 200 || !r.data || !Array.isArray(r.data.data)) throw new Error(`reading My Content answered ${r.status}`);
  return r.data.data;
}

module.exports = { T, PATHS, CTA, allow, isPost, freeTour, typeCtaAndWrite, startWrite, reviews, chain, auditTenant };
