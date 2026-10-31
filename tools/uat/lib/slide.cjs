// Video slides (skill aa-uat-video): a full-screen HTML card in the partner kit's look (warm background, white card,
// Fahkwang headings, Poppins body, amber accent), shown in the recorded page between real screens. English only.
// Used for the review's opening / closing cards and the "Not ready yet" cards, which name only what is missing and
// never promise a date. Never a fake screen of the product. Cost $0 (fonts from Google Fonts, no API call).
//
//   const slide = require('../../lib/slide.cjs');
//   await slide.show(page, h, { kicker, title, lead, bullets: [...], tiles: [{ label, value, note }], foot });
//   await slide.notReady(page, h, { screen: 'Tasks', missing: ['...'] });
// Both assert that the card rendered (its heading and every bullet / tile).

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function html({ kicker = '', title, lead = '', bullets = [], tiles = [], foot = '', tone = 'info' }) {
  const accent = tone === 'missing' ? '#9E6E16' : '#DB9628';
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${esc(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fahkwang:wght@500;600&family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#F8F6F2;--card:#FFFFFF;--ink:#1F2933;--body:#3A4453;--muted:#5A6270;--line:#E9E4DB;--accent:${accent}}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);font-family:Poppins,system-ui,sans-serif}
main{min-height:100%;display:grid;place-items:center;padding:clamp(16px,4vw,64px)}
.card{width:min(1120px,100%);background:var(--card);border:1px solid var(--line);border-radius:18px;padding:clamp(22px,4vw,56px);
  box-shadow:0 18px 48px rgba(31,41,51,.08)}
.kicker{display:inline-block;font-size:clamp(12px,1.2vw,14px);font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:var(--accent);border:1px solid var(--accent);border-radius:999px;padding:4px 12px;margin:0 0 18px}
h1{font-family:Fahkwang,Georgia,serif;font-weight:600;font-size:clamp(26px,3.4vw,46px);line-height:1.15;margin:0 0 14px}
.lead{font-size:clamp(15px,1.6vw,20px);line-height:1.55;color:var(--body);margin:0 0 22px;max-width:60ch}
ul{margin:0;padding:0;list-style:none;display:grid;gap:10px}
li{font-size:clamp(14px,1.45vw,18px);line-height:1.45;color:var(--body);padding-left:26px;position:relative}
li::before{content:"";position:absolute;left:4px;top:.55em;width:10px;height:10px;border-radius:3px;background:var(--accent)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,180px),1fr));gap:12px;margin-top:6px}
.tile{border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:#FFFDF9}
.tile b{display:block;font-family:Fahkwang,Georgia,serif;font-size:clamp(20px,2.2vw,30px);font-weight:600;color:var(--ink)}
.tile span{display:block;font-size:13px;color:var(--muted);margin-top:4px}
.tile small{display:block;font-size:12px;color:var(--muted);margin-top:6px}
.foot{margin:24px 0 0;font-size:13px;color:var(--muted)}
</style></head><body><main><section class="card" data-testid="uat-slide" data-tone="${esc(tone)}">
${kicker ? `<p class="kicker">${esc(kicker)}</p>` : ''}<h1>${esc(title)}</h1>
${lead ? `<p class="lead">${esc(lead)}</p>` : ''}
${bullets.length ? `<ul data-testid="uat-slide-bullets">${bullets.map((b) => `<li>${esc(b)}</li>`).join('')}</ul>` : ''}
${tiles.length ? `<div class="tiles" data-testid="uat-slide-tiles">${tiles.map((t) => `<div class="tile"><b>${esc(t.value)}</b><span>${esc(t.label)}</span>${t.note ? `<small>${esc(t.note)}</small>` : ''}</div>`).join('')}</div>` : ''}
${foot ? `<p class="foot">${esc(foot)}</p>` : ''}
</section></main></body></html>`;
}

async function show(page, h, spec) {
  await page.goto('about:blank'); // leave the app's origin: its CSP would block the inline card and the fonts
  await page.setContent(html(spec), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts && document.fonts.ready);
  await h.expect(page.getByRole('heading', { level: 1, name: spec.title })).toBeVisible();
  if (spec.bullets && spec.bullets.length) await h.expect(page.locator('[data-testid="uat-slide-bullets"] li')).toHaveCount(spec.bullets.length);
  if (spec.tiles && spec.tiles.length) await h.expect(page.locator('[data-testid="uat-slide-tiles"] .tile')).toHaveCount(spec.tiles.length);
}

/** The "Not ready yet" card for a screen or feature that is not built: names only what is missing. */
async function notReady(page, h, { screen, missing, foot }) {
  await show(page, h, {
    kicker: 'Not ready yet',
    title: screen,
    lead: 'This part of the CRM is not built yet. What is missing:',
    bullets: missing,
    foot: foot || 'Everything else in this video runs live on the development environment with invented data.',
    tone: 'missing',
  });
}

module.exports = { html, show, notReady };
