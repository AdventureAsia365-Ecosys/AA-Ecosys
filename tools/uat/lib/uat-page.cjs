// Helpers of the UAT scenarios that are NOT dry-run scenarios (AA-855 round 1): they write on a synthetic tenant (an
// allow-listed write only), or they cost money, so the dry-run manifest never lists them. Each one signs its identity
// in through prepare() (lib/signin.cjs, unrecorded), unless the runner handed it a session (UAT_STORAGE_STATE).
//   const { rw, studioCall } = require('../../lib/uat-page.cjs');
//   module.exports = rw({ id: 'PRT-02', app: 'content-studio', identity: 'studio-editor', allowWrites: ['...'], steps });
// The browser guard stays on: readOnly + allowWrites, so any write outside the scenario's own list is aborted and
// fails the take (record.cjs blocked_writes). The pilot guard (lib/pilot-guard.cjs) runs before the browser opens.
'use strict';
const { ro } = require('./dryrun-page.cjs');

/** A scenario that may write `allowWrites` (regex sources) only; prepare() signs `identity` in, unrecorded. */
function rw({ identity, allowWrites = [], paid = false, ...rest }) {
  const sc = ro({ identity, ...rest });
  sc.allowWrites = allowWrites;
  sc.prepare = async () => {
    if (paid && process.env.UAT_ALLOW_PAID !== '1') {
      throw new Error(`SKIPPED: ${sc.id} calls a paid model; run it only with UAT_ALLOW_PAID=1 (at most one piece per run)`);
    }
    if (process.env.UAT_STORAGE_STATE || identity === 'public') return;
    const { ensureState } = require('./signin.cjs');
    sc.storageState = (await ensureState(identity)).file;
  };
  return sc;
}

/**
 * Same-origin JSON call from a signed-in studio page (the httpOnly studio cookies go along): { status, data }. Writes
 * still pass the browser guard, so only a path in the scenario's allowWrites reaches the app.
 */
async function studioCall(page, method, p, body) {
  return page.evaluate(async ({ method, p, body }) => {
    const res = await fetch(p, {
      method,
      headers: body === undefined ? { Accept: 'application/json' } : { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: 'same-origin',
      cache: 'no-store',
    });
    const text = await res.text();
    let data = text;
    try { data = JSON.parse(text); } catch { /* not JSON */ }
    return { status: res.status, data };
  }, { method, p, body });
}

module.exports = { rw, studioCall };
