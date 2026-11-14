// AA-1094 S279: /audit-atlas-hearth/plan at 1440 light, the "List of tours" pane; records the tenant-tours BFF answer. Read only.
import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire("/home/nghiep/projects/AA-Ecosys/.tmp-session/wt/s279-verify-cis/package.json");
const { chromium } = require("@playwright/test");
const OUT = "/home/nghiep/projects/AA-Ecosys/.tmp-session/S279/verify/aa1094";
const browser = await chromium.launch();
const log = { ran_at: new Date().toISOString() };
try {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: "light" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("response", (r) => { if (r.status() >= 400) errors.push(`${r.status()} ${new URL(r.url()).pathname}`); });
  let lr = null;
  page.on("response", (r) => { if (!lr && r.url().includes("/api/browse") && /resource=(tenant-tours|catalog-tours)/.test(r.url())) lr = r; });
  const resp = await page.goto("https://tripplanner.lumiguides.it.com/audit-atlas-hearth/plan", { waitUntil: "load" });
  log.status = resp?.status();
  await page.waitForTimeout(8000);
  log.title = await page.title();
  log.agency_header = await page.locator('[data-testid="agency-header"]').count();
  log.agency_name = (await page.evaluate(() => document.body.innerText)).includes("Atlas & Hearth");
  await page.screenshot({ path: `${OUT}/shots/aa1094-atlas-plan-1440-light.png` });
  try {
    await page.getByRole("button", { name: "List of tours" }).first().click({ timeout: 15000 });
    await page.waitForTimeout(6000);
    if (lr) { const j = await lr.json().catch(() => null); log.list = { url: new URL(lr.url()).search, status: lr.status(), source: j?.source, total: j?.total, first: j?.tours?.[0]?.title }; }
    await page.screenshot({ path: `${OUT}/shots/aa1094-atlas-tourlist-1440-light.png` });
  } catch (e) { log.list_error = String(e).slice(0, 300); }
  log.errors = errors.slice(0, 20);
} finally { await browser.close(); }
fs.writeFileSync(`${OUT}/raw/aa1094-atlas-plan.json`, JSON.stringify(log, null, 2));
console.log(JSON.stringify(log));
