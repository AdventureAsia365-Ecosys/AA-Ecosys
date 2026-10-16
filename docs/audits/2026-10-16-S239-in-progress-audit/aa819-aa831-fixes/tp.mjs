// S239 AA-819 re-verify after TripPlanner #88 (fb0653a): AI label popover stays inside the viewport,
// site pill copy no longer says "AI-assisted". Public page, no login, no secrets, no API writes.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { writeFileSync } from "node:fs";
const BASE = "https://tripplanner.lumiguides.it.com";
const OUT = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-16-S239-in-progress-audit/aa819-aa831-fixes";
const SLUG = "delhi-agra-jaipur-three-capitals-in-2-days-india-a4966d23";
const log = {};
const b = await chromium.launch();
const geo = (btn) => btn.evaluate((x) => {
  const p = document.getElementById(x.getAttribute("aria-controls"));
  const r = p ? p.getBoundingClientRect() : null;
  const m = document.querySelector("main");
  const vis = p ? getComputedStyle(p).display !== "none" && r.height > 0 : false;
  return {
    label: x.innerText.replace(/\s+/g, " ").trim(),
    expanded: x.getAttribute("aria-expanded"), panel_visible: vis,
    rect: r ? [r.left, r.top, r.right, r.bottom].map((v) => Math.round(v * 10) / 10) : null,
    transform: p ? getComputedStyle(p).transform : null,
    innerWidth, limit: innerWidth - 4,
    right_ok: r ? r.right <= innerWidth - 4 : null, left_ok: r ? r.left >= 0 : null,
    doc_sw: document.documentElement.scrollWidth, doc_cw: document.documentElement.clientWidth,
    main_sw: m ? m.scrollWidth : null, main_cw: m ? m.clientWidth : null,
    explanation: p ? p.textContent.trim() : null,
  };
});
const runs = [[390, "light"], [390, "dark"], [1440, "light"], [1440, "dark"]];
for (const [w, theme] of runs) {
  const key = `${w}-${theme}`; const L = (log[key] = { labels: [], console_errors: [], http_errors: [] });
  const touch = w < 768;
  const ctx = await b.newContext({ viewport: { width: w, height: w < 768 ? 844 : 900 }, colorScheme: theme, hasTouch: touch, locale: "en-US" });
  await ctx.addInitScript((t) => { try { localStorage.setItem("tp_theme", t); } catch {} }, theme);
  const p = await ctx.newPage();
  p.on("console", (m) => { if (m.type() === "error") L.console_errors.push(m.text().slice(0, 200)); });
  p.on("pageerror", (e) => L.console_errors.push("pageerror: " + String(e).slice(0, 200)));
  p.on("response", (r) => { if (r.status() >= 400) L.http_errors.push(r.status() + " " + r.url().replace(BASE, "").slice(0, 140)); });
  await p.goto(`${BASE}/tours/${SLUG}`, { waitUntil: "load" }); await p.waitForTimeout(3000);
  L.data_theme = await p.evaluate(() => document.documentElement.getAttribute("data-theme") || document.documentElement.className);
  const targets = [];
  const hp = p.locator("header button[aria-expanded]");
  for (let i = 0; i < await hp.count(); i++) if (await hp.nth(i).isVisible()) { targets.push(["header-pill", hp.nth(i)]); break; }
  const ml = p.locator("main button[aria-expanded]");
  const n = await ml.count(); L.main_label_count = n;
  const names = ["summary", "highlights", "day-by-day"];
  for (let i = 0; i < n; i++) if (await ml.nth(i).isVisible()) targets.push([names[i] ?? `label${i}`, ml.nth(i)]);
  for (const [name, btn] of targets) {
    await btn.scrollIntoViewIfNeeded();
    if (touch) await btn.tap(); else await btn.click();
    await p.waitForTimeout(500);
    const g = await geo(btn); g.name = name;
    // make sure the open panel is on screen vertically for the screenshot
    await btn.evaluate((x) => { const pn = document.getElementById(x.getAttribute("aria-controls")); const r = pn.getBoundingClientRect(); if (r.bottom > innerHeight) window.scrollBy(0, r.bottom - innerHeight + 16); });
    await p.waitForTimeout(200);
    await p.screenshot({ path: `${OUT}/aa819-tour-${key}-${name}-open.png` });
    L.labels.push(g);
    if (touch) await btn.tap(); else await btn.click();
    await p.waitForTimeout(250);
    g.closed_after = await btn.getAttribute("aria-expanded");
  }
  L.page = await p.evaluate(() => { const m = document.querySelector("main"); return { doc_sw: document.documentElement.scrollWidth, doc_cw: document.documentElement.clientWidth, main_sw: m?.scrollWidth, main_cw: m?.clientWidth }; });
  await ctx.close();
}
await b.close();
// verdicts
const site = [];
for (const [k, L] of Object.entries(log)) {
  L.pass = L.labels.length > 0 && L.labels.every((g) => g.panel_visible && g.right_ok && g.left_ok && g.doc_sw <= g.doc_cw && (g.main_sw ?? 0) <= (g.main_cw ?? 1e9) && g.closed_after === "false");
  for (const g of L.labels) if (g.name === "header-pill") site.push({ run: k, says_ai_assisted: /AI-assisted/i.test(g.explanation), explanation: g.explanation });
}
log.site_pill = site;
writeFileSync("/home/nghiep/projects/AA-Ecosys/.tmp-session/s239/aa819831/tp_out.json", JSON.stringify(log, null, 1));
for (const [k, L] of Object.entries(log)) if (k !== "site_pill") console.log(k, "pass=" + L.pass, "theme=" + L.data_theme, L.labels.map((g) => `${g.name}[${g.label}] r=${g.rect?.[2]}/${g.limit} vis=${g.panel_visible} tf=${g.transform} doc=${g.doc_sw}/${g.doc_cw} main=${g.main_sw}/${g.main_cw}`).join(" | "), "cerr=" + L.console_errors.length, "http=" + L.http_errors.join(","));
console.log(JSON.stringify(site.map((s) => [s.run, s.says_ai_assisted])), site[0]?.explanation);
