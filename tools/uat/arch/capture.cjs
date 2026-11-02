// Keyframe capture for the architecture videos (AA-1021), with the gate's layer 2 (DOM) check before every shot.
//
//   node capture.cjs <stage.html> <keyframes.json> <out_dir> <aspect> <patterns.json>
//     keyframes.json: [{n, visual}, ...]  (make_episode.py writes it)  ->  <out_dir>/kf-NN.png + dom/kf-NN.json
//   exit 0 = every keyframe captured | 4 = a DOM text hit (nothing captured for that frame) | 5 = a network request
//
// The page is local and inline (page.py); every request other than file:/data: is refused and fails the run.
// Before each screenshot the visible and hidden strings of the page are checked with the gate patterns
// (gate.py patterns-json): body text, SVG <text>/<title>/<desc>, alt / aria-label / title / data-* attributes, every
// href/src (inline data: payloads are not text). A hit stops the run before the frame exists. Screenshots are taken at
// deviceScaleFactor 2 (keyframes, not a screen recording); make_episode.py scales them to the frame size.
// One Chromium at a time (RAM rule); cost $0.
'use strict';
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const SIZES = { '16:9': [1920, 1080], '1:1': [1080, 1080], '4:5': [1080, 1350], '9:16': [1080, 1920] };

function compile(patterns) {
  return patterns.map((p) => ({ category: p.category, re: new RegExp(p.source, `g${p.flags || ''}`) }));
}

function scan(text, compiled) {
  const clean = String(text).replace(/data:[a-z/+.-]+;base64,[A-Za-z0-9+/=\s]*/gi, 'data:;base64,');
  const hits = [];
  for (const p of compiled) {
    p.re.lastIndex = 0;
    let m;
    while ((m = p.re.exec(clean)) !== null) {
      hits.push({ category: p.category, match: m[0] });
      if (m[0] === '') p.re.lastIndex += 1;
    }
  }
  return hits;
}

async function domStrings(page) {
  return page.evaluate(() => {
    const out = { title: document.title, body: document.body.innerText, svg: [], attrs: [], refs: [] };
    for (const el of document.querySelectorAll('#frame svg text, #frame svg title, #frame svg desc')) out.svg.push(el.textContent);
    for (const el of document.querySelectorAll('#frame *')) {
      for (const a of el.attributes) {
        if (a.name === 'alt' || a.name === 'aria-label' || a.name === 'title' || a.name.startsWith('data-')) out.attrs.push(`${a.name}=${a.value}`);
        if (a.name === 'href' || a.name === 'src' || a.name === 'xlink:href') out.refs.push(a.value.slice(0, 200));
      }
    }
    return out;
  });
}

async function main() {
  const [htmlPath, kfPath, outDir, aspect, patPath] = process.argv.slice(2);
  if (!patPath || !SIZES[aspect]) {
    console.error('usage: node capture.cjs <stage.html> <keyframes.json> <out_dir> <aspect> <patterns.json>');
    process.exit(2);
  }
  const keyframes = JSON.parse(fs.readFileSync(kfPath, 'utf8'));
  const compiled = compile(JSON.parse(fs.readFileSync(patPath, 'utf8')));
  fs.mkdirSync(path.join(outDir, 'dom'), { recursive: true });
  const [width, height] = SIZES[aspect];
  const browser = await chromium.launch();
  let blocked = [];
  try {
    const ctx = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 2 });
    const page = await ctx.newPage();
    await page.route('**/*', (route) => {
      const u = route.request().url();
      if (u.startsWith('file:') || u.startsWith('data:')) return route.continue();
      blocked.push(u.slice(0, 80));
      return route.abort();
    });
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    await page.goto('file://' + path.resolve(htmlPath), { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    for (const kf of keyframes) {
      const name = `kf-${String(kf.n).padStart(2, '0')}`;
      await page.evaluate((v) => window.show(v), kf.visual);
      await page.evaluate(() => document.fonts.ready);
      await page.waitForTimeout(60);
      if (errors.length) throw new Error(`page error at ${name}: ${errors.join(' | ')}`);
      const dump = await domStrings(page);
      fs.writeFileSync(path.join(outDir, 'dom', `${name}.json`), JSON.stringify(dump));
      const text = [dump.title, dump.body, ...dump.svg, ...dump.attrs, ...dump.refs].join('\n');
      const hits = scan(text, compiled);
      if (hits.length) {
        for (const h of hits) console.error(`GATE HIT [L2] ${h.category} in ${name}: ${JSON.stringify(h.match)}`);
        process.exitCode = 4;
        return;
      }
      if (blocked.length) {
        console.error(`network request refused: ${blocked.join(', ')}`);
        process.exitCode = 5;
        return;
      }
      await page.screenshot({ path: path.join(outDir, `${name}.png`) });
      console.log(`${name} ok`);
    }
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error(e.stack || String(e));
  process.exit(1);
});
