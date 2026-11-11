// Upstream shim for the local builds: maps the Lambda REST paths the BFF calls back onto the live public BFF
// (/api/browse?resource=...), records each answer once and replays it, so both builds see identical data.
import http from 'node:http';
const LIVE = 'https://tripplanner.lumiguides.it.com/api/browse';
const cache = new Map();
function map(u) {
  const p = u.pathname, q = new URLSearchParams(u.search);
  let m;
  if ((m = p.match(/^\/browse\/tiles\/(.+)$/))) { q.set('resource','tiles'); q.set('tile_id', decodeURIComponent(m[1])); return q; }
  if ((m = p.match(/^\/browse\/destinations\/(.+)$/))) { return new URLSearchParams({resource:'destination', id: decodeURIComponent(m[1])}); }
  const simple = {'/browse/countries':'countries','/browse/routes':'routes','/browse/by-country':'by-country','/browse/shapes':'shapes','/browse/stops':'stops','/browse/catalog/tours':'catalog-tours','/browse/tour-route':'tour-route'};
  if (simple[p]) { q.set('resource', simple[p]); return q; }
  return null;
}
http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://x');
  const q = map(u);
  if (!q) { res.writeHead(404, {'content-type':'application/json'}); res.end('{"error":"not_found"}'); console.log('404', req.method, req.url); return; }
  const key = q.toString();
  if (!cache.has(key)) {
    const r = await fetch(`${LIVE}?${key}`, { headers: { accept: 'application/json' } });
    cache.set(key, { status: r.status, cc: r.headers.get('cache-control') || 'no-store', body: await r.text() });
    console.log('rec', r.status, key.slice(0,100));
  }
  const c = cache.get(key);
  res.writeHead(c.status, {'content-type':'application/json','cache-control':c.cc}); res.end(c.body);
}).listen(8787, '127.0.0.1', () => console.log('shim on 8787'));
