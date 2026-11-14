// S279 verify-only (never committed): CRM Settings > Proposal lines (/settings/inclusions) renders, read only.
import { test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { landOnPartner, signIn, skipPasskeyOffer } from "../helpers/signin";
const PARTNER = (process.env.E2ECRMPARTNER ?? "").replace(/\/+$/, "");
const OUT = process.env.S279_OUT!;
test("inclusions", async ({ page }) => {
  test.skip(process.env.E2ECRMINCL !== "probe");
  test.setTimeout(240_000);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`${PARTNER}/settings/inclusions`);
  await signIn(page, { email: process.env.E2ECRMEMAIL!, password: process.env.E2ECRMPASSWORD, totpSecret: process.env.E2ECRMTOTP });
  await skipPasskeyOffer(page).catch(() => {});
  await landOnPartner(page, PARTNER);
  await page.waitForLoadState("networkidle").catch(() => {});
  const lib = async () => page.evaluate(async () => {
    const r = await fetch(`/bff/inclusion-items?archived=true`, { headers: { Accept: "application/json" } });
    const b: any = await r.json().catch(() => null);
    const items = (b?.items ?? []).map((i: any) => ({ id: i.id, kind: i.kind, archived: i.archived ?? i.archived_at ?? null, updated_at: i.updated_at ?? null, text: (i.text ?? i.label ?? "").length }));
    return { status: r.status, count: items.length, items };
  });
  const before = await lib();
  let consoleErr: string[] = [];
  let bad: { url: string; status: number; method: string }[] = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErr.push(m.text().slice(0, 300)); });
  page.on("pageerror", (e) => consoleErr.push(`pageerror: ${String(e).slice(0, 300)}`));
  page.on("response", (r) => { const u = r.url(); if (u.startsWith(PARTNER) && r.status() >= 400) bad.push({ url: u.slice(PARTNER.length, PARTNER.length + 160), status: r.status(), method: r.request().method() }); });
  const results: any[] = [];
  for (const scheme of ["light", "dark"] as const) {
    for (const w of [1440, 390]) {
      consoleErr = []; bad = [];
      await page.emulateMedia({ colorScheme: scheme });
      await page.setViewportSize({ width: w, height: w === 390 ? 844 : 900 });
      const resp = await page.goto(`${PARTNER}/settings/inclusions`, { waitUntil: "networkidle" }).catch(() => null);
      await page.waitForTimeout(1500);
      const r = await page.evaluate(() => ({
        path: location.pathname,
        testid: !!document.querySelector('[data-testid="crm-inclusion-settings"]'),
        couldntLoad: document.body.innerText.includes("This page couldn't load") || document.body.innerText.includes("This page couldn’t load"),
        errorState: !!document.querySelector('[data-testid="error-state"], [role="alert"]'),
        dataTheme: document.documentElement.getAttribute("data-theme"),
        scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth,
        bodyScrollW: document.body.scrollWidth,
        title: (document.querySelector("h1")?.textContent ?? "").trim().slice(0, 80),
      }));
      const shot = `inclusions-${w}-${scheme}.png`;
      await page.screenshot({ path: path.join(OUT, "shots", shot), fullPage: true });
      results.push({ width: w, scheme, http: resp?.status() ?? null, ...r, sideways: r.scrollW > r.clientW, consoleErrors: consoleErr, badResponses: bad, shot });
    }
  }
  const after = await lib();
  fs.writeFileSync(path.join(OUT, "raw", "inclusions-checks.json"), JSON.stringify({ results, library_before: before, library_after: after, unchanged: JSON.stringify(before.items) === JSON.stringify(after.items) }, null, 1));
});
