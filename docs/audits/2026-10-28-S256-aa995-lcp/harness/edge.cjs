// AA-995 S256 measurement harness: a stand-in for the Vercel edge in front of `next start`.
// - /photo-cdn/<path>  → served from a local disk cache, filled once from the photo CDN (what the Vercel CDN does with
//   `x-vercel-enable-rewrite-caching: 1` and the CDN's one-year Cache-Control). Without it every Lighthouse run would
//   pay a fresh Vietnam → CloudFront round trip inside `next start`'s rewrite proxy, which production does not.
// - everything else    → piped to next start on :3995 unchanged.
// Usage: node edge.cjs [port=3997] [h2]  — with "h2": HTTP/2 over TLS (self-signed edge-cert.pem; Chrome needs
// --ignore-certificate-errors), the protocol the Vercel edge speaks; `next start` alone is HTTP/1.1, where Lighthouse's
// simulation queues same-origin requests behind its six-connection limit and production never does.
const http = require("http");
const http2 = require("http2");
const https = require("https");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const CACHE = path.join(__dirname, "edge-cache");
fs.mkdirSync(CACHE, { recursive: true });
const CDN = "https://img.lumiguides.it.com";

function fromCdn(p) {
  return new Promise((resolve, reject) => {
    https.get(CDN + p, (r) => {
      const chunks = [];
      r.on("data", (c) => chunks.push(c));
      r.on("end", () => resolve({ status: r.statusCode, type: r.headers["content-type"], body: Buffer.concat(chunks) }));
    }).on("error", reject);
  });
}

async function handler(req, res) {
  if (req.url.startsWith("/photo-cdn/")) {
    const p = req.url.slice("/photo-cdn".length);
    const key = path.join(CACHE, crypto.createHash("sha1").update(p).digest("hex"));
    try {
      if (!fs.existsSync(key)) {
        const r = await fromCdn(p);
        if (r.status !== 200) { res.writeHead(r.status); return res.end(); }
        fs.writeFileSync(key, r.body);
        fs.writeFileSync(key + ".type", r.type || "application/octet-stream");
      }
      res.writeHead(200, { "content-type": fs.readFileSync(key + ".type", "utf8"), "cache-control": "public, max-age=31536000" });
      return res.end(fs.readFileSync(key));
    } catch (e) {
      res.writeHead(502); return res.end(String(e));
    }
  }
  const headers = {};
  for (const [k, v] of Object.entries(req.headers)) if (!k.startsWith(":")) headers[k] = v;
  headers.host = "localhost:3995";
  const up = http.request({ host: "127.0.0.1", port: 3995, path: req.url, method: req.method, headers }, (r) => {
    const out = {};
    for (const [k, v] of Object.entries(r.headers)) if (!["connection", "keep-alive", "transfer-encoding"].includes(k)) out[k] = v;
    res.writeHead(r.statusCode, out);
    r.pipe(res);
  });
  up.on("error", (e) => { res.writeHead(502); res.end(String(e)); });
  req.pipe(up);
}

const port = Number(process.argv[2] || 3997);
if (process.argv[3] === "h2") {
  http2.createSecureServer({ key: fs.readFileSync(path.join(__dirname, "edge-key.pem")), cert: fs.readFileSync(path.join(__dirname, "edge-cert.pem")), allowHTTP1: true }, handler)
    .listen(port, "127.0.0.1", () => console.log("edge h2 up"));
} else {
  http.createServer(handler).listen(port, "127.0.0.1", () => console.log("edge up"));
}
