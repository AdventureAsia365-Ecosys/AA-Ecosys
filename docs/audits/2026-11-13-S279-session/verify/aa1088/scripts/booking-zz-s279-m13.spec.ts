// S279 verify lane (not committed). As e2e-booking-staff (GET only): AA-1088 M13 after the legacy-case backfill —
// case header + Trip details at 1440/390 light, confirmation + vouchers JSON/HTML of each case.
import { test, type Page } from "@playwright/test";
import fs from "node:fs";
import { STAFF_AUTH_HOST, signInByEmailCode } from "../signed-in/helpers/cognitoSignIn";

const D = "/home/nghiep/projects/AA-Ecosys/.tmp-session/S279/verify/aa1088";
const CASES = (process.env.CASES ?? "TC-000028,TC-000033,TC-000035,TC-000036").split(",");
const out: Record<string, unknown> = {};

async function j(page: Page, p: string) {
  return page.evaluate(async (url) => {
    const r = await fetch(url, { headers: { Accept: "application/json" }, credentials: "same-origin" });
    const t = await r.text();
    let body: unknown = t.slice(0, 400); try { body = JSON.parse(t); } catch { /* html */ }
    return { status: r.status, body };
  }, `/api/booking${p}`);
}

test("m13 after backfill (read-only)", async ({ page, context }) => {
  test.skip(process.env.M13 !== "1", "opt-in");
  test.setTimeout(500_000);
  await page.emulateMedia({ colorScheme: "light" });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/login", { waitUntil: "domcontentloaded" });
  await page.getByRole("link", { name: /sign in with company email/i }).click({ timeout: 15_000 });
  await page.waitForURL((u) => u.host === STAFF_AUTH_HOST, { timeout: 20_000 });
  await signInByEmailCode(page, { email: "e2e-booking-staff@e2e-mail.lumiguides.it.com", prefix: "inbound-admin/" });
  await page.waitForURL((u) => !u.host.startsWith("staff-auth") && !u.pathname.startsWith("/login") && !u.pathname.startsWith("/api/auth"), { timeout: 30_000 });
  out.at = new Date().toISOString();

  for (const c of CASES) {
    const rec: Record<string, unknown> = {};
    const tc = await j(page, `/trip-cases/${c}`);
    const b = tc.body as Record<string, unknown>;
    rec.case = { status: tc.status, trip_title: b?.trip_title, title: b?.title, status_value: b?.status, start_date: b?.start_date, end_date: b?.end_date, party_tenant_id: b?.party_tenant_id };
    for (const kind of ["confirmation", "vouchers"]) {
      const r = await j(page, `/b2b-desk/bookings/${c}/${kind}?format=json`);
      const rb = r.body as Record<string, unknown>;
      rec[`${kind}_json`] = r.status === 200 ? { status: 200, start_date: rb.start_date, end_date: rb.end_date, trip_title: rb.trip_title ?? rb.title,
        lines: ((rb.lines as Record<string, unknown>[]) ?? []).map((l) => ({ title: l.title ?? l.label, kind: l.kind, service_date: l.service_date })),
        vouchers: ((rb.vouchers as Record<string, unknown>[]) ?? []).length } : r;
      const html = await page.evaluate(async (url) => {
        const res = await fetch(url, { headers: { Accept: "text/html" }, credentials: "same-origin" });
        return { status: res.status, ct: res.headers.get("content-type"), text: await res.text() };
      }, `/api/booking/b2b-desk/bookings/${c}/${kind}?format=html`);
      rec[`${kind}_html_status`] = [html.status, html.ct];
      if (html.status === 200 && (html.ct ?? "").includes("html")) {
        fs.writeFileSync(`${D}/raw/m13-${c}-${kind}.html`, html.text);
        const p = await context.newPage();
        await p.setViewportSize({ width: 1440, height: 900 });
        await p.setContent(html.text, { waitUntil: "load" });
        await p.pdf({ path: `${D}/raw/m13-${c}-${kind}.pdf`, format: "A4", printBackground: true });
        await p.screenshot({ path: `${D}/shots/m13-${c}-${kind}-1440-light.png`, fullPage: true });
        rec[`${kind}_text`] = await p.evaluate(() => document.body.innerText.split("\n").map((s) => s.trim()).filter(Boolean).slice(0, 60));
        rec[`${kind}_has_trip_plan_ref`] = await p.evaluate(() => /trip_plan tp:|crm-proposal:/.test(document.body.innerText));
        await p.close();
      } else if (html.status !== 200) {
        rec[`${kind}_html_body`] = html.text.slice(0, 300);
      }
    }
    for (const [w, h] of [[1440, 900], [390, 844]] as const) {
      await page.setViewportSize({ width: w, height: h });
      await page.goto(`/cases/${c}`, { waitUntil: "domcontentloaded" });
      await page.waitForLoadState("networkidle", { timeout: 15_000 }).catch(() => {});
      await page.waitForTimeout(2500);
      await page.screenshot({ path: `${D}/shots/case-${c}-${w}-light.png`, fullPage: false });
      const td = page.getByText("Trip details", { exact: true }).first();
      if (await td.count()) {
        await td.scrollIntoViewIfNeeded().catch(() => {});
        await page.waitForTimeout(500);
        await page.screenshot({ path: `${D}/shots/case-${c}-tripdetails-${w}-light.png`, fullPage: false });
      }
      if (w === 1440) {
        rec.case_page = await page.evaluate(() => {
          const t = document.body.innerText;
          const i = t.indexOf("Trip details");
          return { h1: document.querySelector("h1")?.textContent?.trim(), header: t.slice(0, 900),
            trip_details: i >= 0 ? t.slice(i, i + 700) : null, oneDay: /\(1 day\)/.test(t), b2bRef: /crm-proposal:/.test(t) };
        });
      } else rec.case_page_390_sideways = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
    }
    out[c] = rec;
  }
  fs.writeFileSync(`${D}/raw/m13-after-backfill.json`, JSON.stringify(out, null, 2));
});
