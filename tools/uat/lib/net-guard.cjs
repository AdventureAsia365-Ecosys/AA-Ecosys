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
// The AWS WAF silent JavaScript Challenge (pilot rehearsal, S279): a planner page of TripPlanner answers its first
// document load with the web ACL's challenge page, whose script POSTs its proof to AWS WAF's token host and reloads
// with the aws-waf-token cookie. No app data: let it through in a read-only run too, or no planner page ever loads.
const CHALLENGE_PROOF = [/^https:\/\/[a-z0-9-]+(?:\.[a-z0-9-]+)*\.token\.awswaf\.com\//];
// Hosts that count as the app itself, besides the scenario's own base URL host.
const FIRST_PARTY = /(^|\.)lumiguides\.it\.com$/;

const isRead = (method) => READ_METHODS.includes(String(method || 'GET').toUpperCase());
/** A web ACL challenge proof (not a write to any app): passed through by the read-only guard. */
const isChallengeProof = (url) => CHALLENGE_PROOF.some((r) => r.test(String(url)));

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

// An allowWrites entry is a regex source on the full URL, optionally led by the write methods it admits:
//   '^https://host/bff/trips/<id>/owner$'          any write method (the original form)
//   'POST ^https://host/bff/trips/<id>/owner$'     POST only
//   'PUT|PATCH ^https://host/bff/x$'               PUT or PATCH
// (allowMatches is the same function under the name the studio scenarios use.)
const ALLOW_METHOD = /^((?:POST|PUT|PATCH|DELETE)(?:\|(?:POST|PUT|PATCH|DELETE))*) (\S.*)$/;

/** One allowWrites entry -> { methods: [..] | null (any write method), re: RegExp on the URL, source }. */
function parseAllow(src) {
  const m = ALLOW_METHOD.exec(String(src));
  return m ? { methods: m[1].split('|'), re: new RegExp(m[2]), source: src } : { methods: null, re: new RegExp(src), source: src };
}

/** allowWrites (strings) -> matchers; RegExp items (older callers) pass as "any write method". */
const compileAllow = (list) => (list || []).map((x) => (x instanceof RegExp ? { methods: null, re: x, source: x.source } : parseAllow(x)));

/** True when a `method` request to `url` is admitted by one of the compiled allowWrites matchers. */
function allowsWrite(allow, method, url) {
  const m = String(method || 'GET').toUpperCase();
  return (allow || []).some((a) => (a instanceof RegExp ? a.test(url) : (!a.methods || a.methods.includes(m)) && a.re.test(url)));
}

/**
 * Make an APIRequestContext read-only in place: any fetch / post / put / patch / delete whose method is not GET / HEAD /
 * OPTIONS (and that no `allow` matcher admits: method and URL, see compileAllow) is refused before it leaves Node:
 * onBlocked(method, url) is called and the call throws. Every helper of APIRequestContext goes through this.fetch(), so
 * wrapping fetch covers them all.
 */
function guardRequestContext(rq, { allow = [], onBlocked = () => {} } = {}) {
  if (!rq || typeof rq.fetch !== 'function' || rq.__uatReadOnly) return rq;
  const inner = rq.fetch.bind(rq);
  rq.fetch = async (urlOrRequest, options = {}) => {
    const isStr = typeof urlOrRequest === 'string';
    const url = isStr ? urlOrRequest : (urlOrRequest && typeof urlOrRequest.url === 'function' ? urlOrRequest.url() : String(urlOrRequest));
    const method = String(options.method || (!isStr && urlOrRequest && typeof urlOrRequest.method === 'function'
      ? urlOrRequest.method() : 'GET')).toUpperCase();
    if (!isRead(method) && !allowsWrite(allow, method, url)) {
      onBlocked(method, url);
      throw new Error(`read-only run: ${method} request from the scenario code refused`);
    }
    return inner(urlOrRequest, options);
  };
  Object.defineProperty(rq, '__uatReadOnly', { value: true });
  return rq;
}

module.exports = { READ_METHODS, TELEMETRY, SESSION, CHALLENGE_PROOF, isRead, isChallengeProof, classify, guardRequestContext,
  parseAllow, compileAllow, allowsWrite, allowMatches: allowsWrite };
