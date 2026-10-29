// AA-995 S256: a local stand-in for the browse Lambda's /browse/catalog/* reads, serving fixtures built from public
// production answers (build_fixtures.py). Usage: node server.cjs [port=3996]; BROWSE_API_URL=http://127.0.0.1:3996
const http = require("http");
const fs = require("fs");
const path = require("path");
const F = path.join(__dirname, "fixtures");
const load = (f) => JSON.parse(fs.readFileSync(path.join(F, f), "utf8"));
const cards = load("cards.json"); // production featured order
const countries = load("destinations.json");
const dests = load("destination_pages.json");
const tours = load("tours.json");
const sitemap = load("sitemap.json");

function tourFromCard(c) {
  const photos = c.cover_url && c.cover_source === "tour"
    ? [{ photo_id: c.slug, place_label: c.cover_place, width: 1600, height: 900, url: c.cover_url, url_small: c.cover_url_small, position: 0 }]
    : [];
  return { ...c, description: c.summary, activities: [], inclusions: null, exclusions: null, group_size: null,
    itinerary_text: c.summary, days: [], places: [], photos };
}

http.createServer((req, res) => {
  const u = new URL(req.url, "http://x");
  const send = (code, body) => {
    res.writeHead(code, { "content-type": "application/json", "cache-control": "public, max-age=300" });
    res.end(JSON.stringify(body));
  };
  const p = u.pathname;
  let m;
  if (p === "/browse/catalog/tours") {
    let list = cards;
    const country = u.searchParams.get("country");
    if (country) list = list.filter((c) => c.country_slug === country || (c.country || "").toLowerCase() === country.toLowerCase());
    const sort = u.searchParams.get("sort") || "featured";
    if (sort === "title") list = [...list].sort((a, b) => a.title.localeCompare(b.title));
    if (sort === "duration_asc") list = [...list].sort((a, b) => (a.duration_days ?? 99) - (b.duration_days ?? 99));
    if (sort === "duration_desc") list = [...list].sort((a, b) => (b.duration_days ?? 0) - (a.duration_days ?? 0));
    const limit = Number(u.searchParams.get("limit") || 24);
    const offset = Number(u.searchParams.get("offset") || 0);
    return send(200, { total: list.length, limit, offset, tours: list.slice(offset, offset + limit) });
  }
  if ((m = /^\/browse\/catalog\/tours\/([^/]+)$/.exec(p))) {
    const slug = decodeURIComponent(m[1]);
    if (tours[slug]) return send(200, tours[slug]);
    const c = cards.find((x) => x.slug === slug);
    return c ? send(200, tourFromCard(c)) : send(404, { error: "not found" });
  }
  if (p === "/browse/catalog/destinations") return send(200, countries);
  if ((m = /^\/browse\/catalog\/destinations\/([^/]+)$/.exec(p))) {
    const d = dests[decodeURIComponent(m[1])];
    return d ? send(200, d) : send(404, { error: "not found" });
  }
  if (p === "/browse/catalog/sitemap") return send(200, sitemap);
  if (p === "/browse/catalog/retired") return send(200, { suffixes: [] });
  return send(404, { error: "mock: unknown path " + p });
}).listen(Number(process.argv[2] || 3996), "127.0.0.1", () => console.log("mock browse up"));
