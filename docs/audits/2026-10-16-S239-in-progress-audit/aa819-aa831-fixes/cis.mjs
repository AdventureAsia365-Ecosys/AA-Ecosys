// S239 AA-831 re-verify after CIS #758 (802b592): portal top-bar breadcrumb ends in an ellipsis at 390.
// Tenant key read from Secrets Manager at run time, never printed or saved. Read-only page visits.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const OUT = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-16-S239-in-progress-audit/aa819-aa831-fixes";
const key = execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", "aa-cis/dev/e2e-tenant/terra-family", "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const b = await chromium.launch(); const out = {};
const measure = (p) => p.evaluate(() => {
  const c = document.querySelector('[data-testid="topbar-breadcrumb"]');
  const t = document.querySelector('[data-testid="topbar-breadcrumb-title"]');
  if (!c || !t) return { found: false };
  const cs = getComputedStyle(t); const cr = c.getBoundingClientRect(); const tr = t.getBoundingClientRect();
  const header = c.closest("header"); const hr = header?.getBoundingClientRect();
  const nextBtn = header ? Array.from(header.querySelectorAll("button")).map((x) => x.getBoundingClientRect()).filter((r) => r.width > 0 && r.left >= cr.left + 1).map((r) => Math.round(r.left))[0] ?? null : null;
  const m = document.querySelector("main");
  return {
    found: true, text: t.textContent, title_attr: t.getAttribute("title"),
    textOverflow: cs.textOverflow, whiteSpace: cs.whiteSpace, overflowX: cs.overflowX,
    title_scrollWidth: t.scrollWidth, title_clientWidth: t.clientWidth, truncated: t.scrollWidth > t.clientWidth,
    title_rect: [tr.left, tr.right].map(Math.round), crumb_right: Math.round(cr.right), next_control_left: nextBtn,
    header_rect: hr ? [hr.left, hr.right].map(Math.round) : null,
    hamburger: !!document.querySelector('button[aria-label="Open menu"]'),
    doc_sw: document.documentElement.scrollWidth, doc_cw: document.documentElement.clientWidth,
    main_sw: m?.scrollWidth, main_cw: m?.clientWidth, innerWidth,
    theme: document.documentElement.getAttribute("data-theme"),
  };
});
const runs = [["help-facebook", "/portal/help/facebook", 390, "light"], ["help-facebook", "/portal/help/facebook", 390, "dark"], ["billing", "/portal/billing", 390, "light"], ["billing", "/portal/billing", 1440, "light"], ["help-facebook", "/portal/help/facebook", 1440, "light"]];
for (const [name, path, w, theme] of runs) {
  const k = `${name}-${w}-${theme}`; const L = (out[k] = { console_errors: [], api_errors: [] });
  const ctx = await b.newContext({ viewport: { width: w, height: w < 768 ? 844 : 900 }, colorScheme: theme });
  await ctx.addInitScript((t) => { try { localStorage.setItem("cis_theme", t); } catch {} }, theme);
  const p = await ctx.newPage();
  p.on("console", (m) => { if (m.type() === "error") L.console_errors.push(m.text().slice(0, 200)); });
  p.on("response", (r) => { if (r.url().includes("/api/") && r.status() >= 400) L.api_errors.push(r.status() + " " + r.url().replace(BASE, "").slice(0, 120)); });
  await p.goto(`${BASE}/tenant-login`); await p.fill('input[type="password"]', key);
  await Promise.all([p.waitForURL(/\/portal/, { timeout: 30000 }), p.click('button:has-text("Access Portal")')]);
  await p.waitForLoadState("networkidle"); await p.waitForTimeout(1000);
  await p.goto(`${BASE}${path}`, { waitUntil: "networkidle" });
  if (w < 768) await p.getByRole("button", { name: "Open menu" }).waitFor({ timeout: 15000 }).catch(() => {});
  await p.waitForTimeout(1500);
  Object.assign(L, await measure(p));
  await p.screenshot({ path: `${OUT}/aa831-${k}.png` });
  await p.screenshot({ path: `${OUT}/aa831-${k}-topbar.png`, clip: { x: 0, y: 0, width: w, height: 72 } });
  await ctx.close();
}
await b.close();
for (const [k, L] of Object.entries(out)) {
  const noOverflow = L.doc_sw <= L.doc_cw && (L.main_sw ?? 0) <= (L.main_cw ?? 1e9);
  L.no_page_overflow = noOverflow;
  L.no_overlap = L.next_control_left == null || L.crumb_right <= L.next_control_left;
  if (k.startsWith("help-facebook-390")) L.pass = L.found && L.textOverflow === "ellipsis" && L.truncated && L.hamburger && noOverflow && L.no_overlap && L.title_attr === "Connect your Facebook Page";
  else L.pass = L.found && !L.truncated && noOverflow && L.no_overlap;
  console.log(k, "pass=" + L.pass, JSON.stringify({ text: L.text, to: L.textOverflow, sw: L.title_scrollWidth, cw: L.title_clientWidth, trunc: L.truncated, crumbR: L.crumb_right, next: L.next_control_left, doc: `${L.doc_sw}/${L.doc_cw}`, main: `${L.main_sw}/${L.main_cw}`, ham: L.hamburger, theme: L.theme, cerr: L.console_errors.length, apierr: L.api_errors }));
}
writeFileSync("/home/nghiep/projects/AA-Ecosys/.tmp-session/s239/aa819831/cis_out.json", JSON.stringify(out, null, 1));
