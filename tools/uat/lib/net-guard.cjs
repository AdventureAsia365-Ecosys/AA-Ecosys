// Read-only network guard of record.cjs (AA-1009 dry run): which aborted request counts as a write to the app, and the
// wrapper that keeps Node-side APIRequestContext calls (page.request / context.request, which context.route() never
// sees) read-only too. Pure: no browser, unit tests in tools/uat/tests/dryrun.test.cjs.
'use strict';

const READ_METHODS = ['GET', 'HEAD', 'OPTIONS'];
// Beacons a read-only run aborts without failing (not a write to the app's data): Vercel analytics / BotID internals,
// a Sentry tunnel or ingest, the map provider's usage events.
const TELEMETRY = [/\/_vercel\//, /\/monitoring(?:[?#]|$)/, /sentry/i, /^https:\/\/events\.mapbox\.com\//];
// Session upkeep, not data: the staff shells' keep-alive (AA-CIS-App _kit/SessionKeepAlive.tsx POSTs
// /api/auth/refresh on every admin page load). Still aborted (a refresh could rotate the saved session's refresh token);
// the page keeps its session (the keep-alive retries in a minute, navigations refresh through GET in proxy.ts).
const SESSION = [/\/api\/auth\/refresh(?:[?#]|$)/];
// Hosts that count as the app itself, besides the scenario's own base URL host.
const FIRST_PARTY = /(^|\.)lumiguides\.it\.com$/;

const isRead = (method) => READ_METHODS.includes(String(method || 'GET').toUpperCase());

// An allowWrites entry is a regex source tested on the full URL (any write method), or "<METHOD> <regex source>" to
// allow that one method only (e.g. "DELETE /api/tenant/v1/publish-log/[^/]+$": a POST on the same path stays refused).
const METHOD_ENTRY = /^(POST|PUT|PATCH|DELETE) (\S.*)$/s;

/** Compile allowWrites entries: [{ method: 'PATCH' | null, re }]. */
function compileAllow(list = []) {
  return (list || []).map((src) => {
    const m = METHOD_ENTRY.exec(String(src));
    return m ? { method: m[1], re: new RegExp(m[2]) } : { method: null, re: new RegExp(src) };
  });
}

/** True when a compiled entry (or a bare RegExp, any method) allows `method` on `url`. */
function allowMatches(allow, method, url) {
  const M = String(method || 'GET').toUpperCase();
  return (allow || []).some((a) => (a instanceof RegExp ? a.test(url) : (!a.method || a.method === M) && a.re.test(url)));
}

/**
 * Kind of an aborted non-read request: 'write' (a write to the app: fails a read-only scenario) or 'other'
 * (telemetry, session upkeep or a third-party post: listed apart, verdict unchanged).
 */
function classify(url, baseURL) {
  let u;
  let app;
  try {
    u = new URL(url);
    app = new URL(baseURL);
  } catch {
    return 'write'; // an unparsable URL is never waved through as harmless
  }
  const firstParty = u.host === app.host || FIRST_PARTY.test(u.hostname);
  if (!firstParty) return 'other';
  if (TELEMETRY.some((r) => r.test(url)) || SESSION.some((r) => r.test(url))) return 'other';
  return 'write';
}

/**
 * Make an APIRequestContext read-only in place: any fetch / post / put / patch / delete whose method is not GET / HEAD /
 * OPTIONS (and that no `allow` entry allows: compileAllow() entries or bare regexes) is refused before it leaves Node:
 * onBlocked(method, url) is called and the call throws. Every helper of APIRequestContext goes through this.fetch(), so wrapping fetch covers them all.
 */
function guardRequestContext(rq, { allow = [], onBlocked = () => {} } = {}) {
  if (!rq || typeof rq.fetch !== 'function' || rq.__uatReadOnly) return rq;
  const inner = rq.fetch.bind(rq);
  rq.fetch = async (urlOrRequest, options = {}) => {
    const isStr = typeof urlOrRequest === 'string';
    const url = isStr ? urlOrRequest : (urlOrRequest && typeof urlOrRequest.url === 'function' ? urlOrRequest.url() : String(urlOrRequest));
    const method = String(options.method || (!isStr && urlOrRequest && typeof urlOrRequest.method === 'function'
      ? urlOrRequest.method() : 'GET')).toUpperCase();
    if (!isRead(method) && !allowMatches(allow, method, url)) {
      onBlocked(method, url);
      throw new Error(`read-only run: ${method} request from the scenario code refused`);
    }
    return inner(urlOrRequest, options);
  };
  Object.defineProperty(rq, '__uatReadOnly', { value: true });
  return rq;
}

module.exports = { READ_METHODS, TELEMETRY, SESSION, isRead, classify, compileAllow, allowMatches, guardRequestContext };
