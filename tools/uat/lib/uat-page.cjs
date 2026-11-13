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
  sc.paid = paid;
  sc.prepare = async () => {
    // A preview (UAT_PREVIEW=1) runs only the steps before the first write, with every write aborted: $0.
    if (paid && process.env.UAT_ALLOW_PAID !== '1' && process.env.UAT_PREVIEW !== '1') {
      throw new Error(`SKIPPED: ${sc.id} calls a paid model; run it only with UAT_ALLOW_PAID=1 (at most one piece per run)`);
    }
    if (process.env.UAT_STORAGE_STATE || ['public', 'traveller'].includes(identity)) return; // a guest never signs in
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

// The methods a limitWrites rule counts unless it names its own: every write (a PATCH / PUT / DELETE on a capped path
// is capped too, never let through unchecked).
const WRITE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

/**
 * A page route in front of the browser guard that lets at most `max` requests of each rule through and aborts the rest
 * before they leave the browser (a run never pays twice for the same model call, e.g. a retry click or a re-render).
 * rules = [{ name, path: RegExp on the URL pathname, max, method?, accept? }]:
 *   method  one method or a list (default WRITE_METHODS: POST, PUT, PATCH and DELETE are all counted and capped); a
 *           read that costs money (a search that calls a model) is capped with method 'GET'. Other methods fall through.
 *   accept  (request) => boolean: the requests of the rule's path and methods the scenario may make at all (e.g. one
 *           JSON `op`, or POST only). A refused one is aborted at once, counted in `<name>_refused`, never forwarded.
 * Returns the live counts { name: n } (aborted ones too; `<name>_refused` for a rule with `accept`), so a step can
 * assert "exactly one" or "none refused". Register it in the first step, before any page loads.
 */
async function limitWrites(page, rules) {
  const counts = {};
  for (const r of rules) {
    const methods = (Array.isArray(r.method) ? r.method : r.method ? [r.method] : WRITE_METHODS).map((m) => String(m).toUpperCase());
    counts[r.name] = 0;
    if (r.accept) counts[`${r.name}_refused`] = 0;
    await page.route((u) => r.path.test(u.pathname), (route) => {
      const req = route.request();
      if (!methods.includes(String(req.method()).toUpperCase())) return route.fallback();
      if (r.accept && !r.accept(req)) {
        counts[`${r.name}_refused`] += 1;
        return route.abort('blockedbyclient');
      }
      counts[r.name] += 1;
      return counts[r.name] <= r.max ? route.fallback() : route.abort('blockedbyclient');
    });
  }
  return counts;
}

/** The bytes of a Playwright download (the browser's temp file; Playwright removes it when the context closes). */
async function downloadBytes(download) {
  const file = await download.path();
  if (!file) throw new Error(`the download ${download.suggestedFilename()} did not finish`);
  return require('fs').readFileSync(file);
}

/**
 * One file of a ZIP archive (a .docx is one), read from the central directory: stored or deflated entries only.
 * Returns a Buffer, or null when the archive has no such entry. Throws on a buffer that is not a ZIP.
 */
function zipEntry(buf, name) {
  const zlib = require('zlib');
  // End of central directory: signature 0x06054b50 within the last 64 KiB + 22 bytes.
  let eocd = -1;
  for (let i = buf.length - 22; i >= Math.max(0, buf.length - 65_557); i--) {
    if (buf.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error('not a ZIP archive');
  const count = buf.readUInt16LE(eocd + 10);
  let p = buf.readUInt32LE(eocd + 16);
  for (let k = 0; k < count; k++) {
    if (buf.readUInt32LE(p) !== 0x02014b50) throw new Error('broken ZIP central directory');
    const method = buf.readUInt16LE(p + 10);
    const size = buf.readUInt32LE(p + 20);
    const nameLen = buf.readUInt16LE(p + 28);
    const extraLen = buf.readUInt16LE(p + 30);
    const commentLen = buf.readUInt16LE(p + 32);
    const local = buf.readUInt32LE(p + 42);
    const entry = buf.subarray(p + 46, p + 46 + nameLen).toString('utf8');
    if (entry === name) {
      const start = local + 30 + buf.readUInt16LE(local + 26) + buf.readUInt16LE(local + 28);
      const data = buf.subarray(start, start + size);
      if (method === 0) return Buffer.from(data);
      if (method === 8) return zlib.inflateRawSync(data);
      throw new Error(`ZIP entry ${name}: compression method ${method} is not supported`);
    }
    p += 46 + nameLen + extraLen + commentLen;
  }
  return null;
}

// The machine-readable AI mark of an export (CIS services/acp_content_writing/ai_marking.py, EU AI Act Art. 50(2)):
// the <article> of an HTML export carries data-ai-generated="true", an HTML document also <meta name="ai-generated">;
// a DOCX carries "ai-generated" in its core properties keywords.
const AI_MARK = {
  article: /<article\b[^>]*\bdata-ai-generated="true"/i,
  meta: /<meta\s+name="ai-generated"\s+content="true"/i,
  docxKeywords: /<cp:keywords>[^<]*\bai-generated\b[^<]*<\/cp:keywords>/i,
};

module.exports = { rw, studioCall, limitWrites, WRITE_METHODS, downloadBytes, zipEntry, AI_MARK };
