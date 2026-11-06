// The hand-over between the write scenarios W-02 -> W-03 -> W-04 (AA-855 round 1): W-02 picks a topic and chooses an
// angle (the write starts), W-03 follows that write to the finished article, W-04 exports it. Each is its own video,
// so the ids travel in a small local file, one entry per audit tenant:
//   tools/uat/work/uat-write-chain.json (gitignored; env UAT_WRITE_CHAIN names another file)
//   { "<audit slug>": { "request_id": "...", "piece_id": "...", "channel": "blog", "at": "<ISO time>" } }
// The file is a convenience, never the source of truth: every reader falls back to the tenant's own data on Dev (the
// newest matching piece of My Content), so a run from another checkout or a later session still finds its piece
// (lesson S262: run state kept only in a local file goes stale). Ids are object ids, not credentials. Pure but for fs.
'use strict';
const fs = require('fs');
const path = require('path');

const FILE = () => process.env.UAT_WRITE_CHAIN || path.join(__dirname, '..', 'work', 'uat-write-chain.json');
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
// An entry older than this is not "the article W-02 just started" any more.
const MAX_AGE_MS = 6 * 3600_000;

function readAll(file = FILE()) {
  try {
    const d = JSON.parse(fs.readFileSync(file, 'utf8'));
    return d && typeof d === 'object' && !Array.isArray(d) ? d : {};
  } catch {
    return {}; // none yet, or unreadable: the readers fall back to Dev
  }
}

/** This tenant's entry when it is recent (`maxAgeMs`) and its ids are uuids, else null. */
function read(slug, { now = Date.now(), maxAgeMs = MAX_AGE_MS, file = FILE() } = {}) {
  const e = readAll(file)[slug];
  if (!e || typeof e !== 'object') return null;
  const at = Date.parse(e.at || '');
  if (!Number.isFinite(at) || now - at > maxAgeMs || at - now > 60_000) return null;
  for (const k of ['request_id', 'piece_id']) if (e[k] != null && !UUID.test(String(e[k]))) return null;
  return e;
}

/** Merge `patch` into this tenant's entry and stamp it (mode 600). Only uuid ids and a channel key are kept. */
function write(slug, patch, { now = new Date(), file = FILE() } = {}) {
  const all = readAll(file);
  const next = { ...(all[slug] || {}) };
  for (const k of ['request_id', 'piece_id']) {
    if (patch[k] === undefined) continue;
    if (patch[k] !== null && !UUID.test(String(patch[k]))) throw new Error(`write-chain: ${k} is not an id`);
    next[k] = patch[k];
  }
  if (patch.channel !== undefined) {
    if (!/^[a-z_]{2,20}$/.test(String(patch.channel))) throw new Error('write-chain: channel is not a channel key');
    next.channel = patch.channel;
  }
  next.at = now.toISOString();
  all[slug] = next;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(all, null, 2)}\n`, { mode: 0o600 });
  return next;
}

/**
 * The newest My Content item (GET /api/tenant/v1/content-writing/reviews rows) that matches: `channel` ('blog', or
 * '!blog' for any other channel), `ready` (ready_state 'ready' only), `sinceMs` (created at most that long ago).
 * Pure: the caller fetched the rows.
 */
function newest(items, { channel = null, ready = false, sinceMs = null, now = Date.now() } = {}) {
  const ok = (it) => {
    if (!it || typeof it !== 'object' || !UUID.test(String(it.piece_id || ''))) return false;
    if (channel === '!blog' ? it.channel === 'blog' : channel && it.channel !== channel) return false;
    if (ready && it.ready_state !== 'ready') return false;
    if (sinceMs != null) {
      const at = Date.parse(it.created_at || '');
      if (!Number.isFinite(at) || now - at > sinceMs) return false;
    }
    return true;
  };
  const at = (it) => Date.parse(it.created_at || '') || 0;
  return (Array.isArray(items) ? items : []).filter(ok).sort((a, b) => at(b) - at(a))[0] || null;
}

module.exports = { FILE, MAX_AGE_MS, read, write, newest, readAll };
