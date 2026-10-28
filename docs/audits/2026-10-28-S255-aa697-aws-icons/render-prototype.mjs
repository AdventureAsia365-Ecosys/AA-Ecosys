import { chromium } from 'playwright';
import fs from 'fs';
const [src, icons, out] = process.argv.slice(2).map((p, i) => i < 2 ? fs.readFileSync(p, 'utf8') : p);
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1400, height: 1000 } });
await p.setContent('<html><body style="margin:0;background:#fff"><div id=x></div></body></html>');
await p.addScriptTag({ url: 'https://cdn.jsdelivr.net/npm/mermaid@12.2.0/dist/mermaid.min.js' });
await p.addScriptTag({ url: 'https://cdn.jsdelivr.net/npm/dompurify@3.4.17/dist/purify.min.js' });
const r = await p.evaluate(async ([src, icons]) => {
  const out = {};
  mermaid.registerIconPacks([{ name: 'logos', icons: JSON.parse(icons) }]);
  mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'default', htmlLabels: false, suppressErrorRendering: true });
  try {
    const { svg } = await mermaid.render('a1', src);
    const clean = DOMPurify.sanitize(svg, { USE_PROFILES: { svg: true, svgFilters: true }, FORBID_TAGS: ['foreignObject','image','use'] });
    out.raw = svg.length; out.clean = clean.length;
    out.foreignObjectInRaw = (svg.match(/<foreignObject/g) || []).length;
    const re = /url\(\s*(?!['"]?#)|@import|\s(?:xlink:)?href\s*=\s*["'](?!#)|\ssrc\s*=\s*["']/i;
    out.external = re.test(clean);
    document.getElementById('x').innerHTML = clean;
  } catch (e) { out.error = String(e.message || e).slice(0, 300); }
  return out;
}, [src, icons]);
console.log(JSON.stringify(r));
await p.locator('#x svg').screenshot({ path: out }).catch(e => console.log('shot', e.message));
await b.close();
