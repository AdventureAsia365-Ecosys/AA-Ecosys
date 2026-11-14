// S279 verify-only (never committed): read back the e2e-writers results (A10a read-only admin) and the negative check
// (staff identity PATCH {"status":"cancelled"} on a staff-made catalogue departure -> 403 e2e_synthetic_only, unchanged).
import { readFileSync, writeFileSync } from "node:fs";
import { expect, test, type Browser, type Page } from "@playwright/test";
import { STAFF_AUTH_HOST, signInByEmailCode } from "../signed-in/helpers/cognitoSignIn";
import { baseUrl } from "../signed-in/helpers/env";

const OUT = process.env.S279_OUT ?? "";
const F = JSON.parse(readFileSync(process.env.BOOKING_E2E_FIXTURES ?? "", "utf-8")).fixtures;
const out: Record<string, unknown> = {};
const pick = (o: any, keys: string[]) => Object.fromEntries(keys.filter((k) => o && k in o).map((k) => [k, o[k]]));
const DEP_KEYS = ["id", "status", "start_date", "capacity", "held", "sold", "updated_at", "created_by"];

async function signedIn(browser: Browser, email: string, prefix: string): Promise<Page> {
  const origin = new URL(baseUrl()).origin;
  const context = await browser.newContext({ baseURL: baseUrl() });
  const page = await context.newPage();
  await page.goto("/login", { waitUntil: "domcontentloaded" });
  await page.getByRole("link", { name: /sign in with company email/i }).click();
  await page.waitForURL((u) => u.host === STAFF_AUTH_HOST, { timeout: 20_000 });
  await signInByEmailCode(page, { email, prefix });
  await page.waitForURL((u) => u.origin === origin && !u.pathname.startsWith("/login") && !u.pathname.startsWith("/api/auth"), { timeout: 30_000 });
  return page;
}
async function get(page: Page, path: string) {
  const r = await page.request.get(`/api/booking${path}`, { headers: { Accept: "application/json" } });
  return { status: r.status(), body: (await r.json().catch(() => null)) as any };
}

test.describe.configure({ mode: "serial" });
let target = "";

test("read back + pick a staff-made departure", async ({ browser }) => {
  test.setTimeout(240_000);
  const page = await signedIn(browser, "e2e-booking@e2e-mail.lumiguides.it.com", "inbound/");
  const sb = await get(page, `/supplier-bookings/${F.supplier_booking.id}`);
  out.supplier_booking = { http: sb.status, ...pick(sb.body, ["id", "code", "status", "confirmation_ref", "confirmed_at"]) };
  const inv = await get(page, `/agency-invoices/${F.invoice.number}`);
  out.invoice = { http: inv.status, ...pick(inv.body, ["id", "number", "status", "currency", "total", "paid", "waiting"]) };
  const pays = await get(page, `/agency-payments?invoice_id=${F.invoice.id}&limit=20`);
  out.payments = { http: pays.status, items: (pays.body?.items ?? []).filter((p: any) => !p.invoice_id || p.invoice_id === F.invoice.id || p.invoice_number === F.invoice.number).map((p: any) => pick(p, ["id", "status", "amount", "invoice_number", "recorded_by", "approved_by", "decided_by"])) };
  const list = await get(page, `/catalog/trip-plans/${F.tour_source_id}/departures`);
  const items = (list.body?.items ?? []) as any[];
  out.departures_http = list.status;
  out.seeded_departure = pick(items.find((d) => d.id === F.departure_id), DEP_KEYS);
  const today = new Date().toISOString().slice(0, 10);
  const cands = items.filter((d) => d.id !== F.departure_id && d.status === "scheduled" && d.start_date > today);
  cands.sort((a, b) => (a.sold ?? 0) + (a.held ?? 0) - ((b.sold ?? 0) + (b.held ?? 0)) || (a.start_date < b.start_date ? 1 : -1));
  out.candidates_count = cands.length;
  target = cands[0]?.id ?? "";
  out.real_departure_before = pick(cands[0], DEP_KEYS);
  const audit = await get(page, `/audit-logs?entity_id=${F.departure_id}&limit=20`);
  out.audit_departure = { http: audit.status, items: (audit.body?.items ?? []).map((i: any) => ({ at: i.at, action: i.action, actor_id: i.actor?.id, actor_name: i.actor?.name })) };
  expect(target, "a staff-made scheduled departure on this plan").not.toBe("");
  await page.context().close();
});

test("staff PATCH cancel on the staff-made departure is refused 403 e2e_synthetic_only and leaves it unchanged", async ({ browser }) => {
  test.setTimeout(240_000);
  test.skip(!target);
  const page = await signedIn(browser, "e2e-booking-staff@e2e-mail.lumiguides.it.com", "inbound-admin/");
  const res = await page.evaluate(async (url) => {
    const r = await fetch(url, { method: "PATCH", headers: { Accept: "application/json", "Content-Type": "application/json" }, body: JSON.stringify({ status: "cancelled" }), credentials: "same-origin" });
    return { status: r.status, body: await r.json().catch(() => null) };
  }, `/api/booking/catalog/departures/${target}`);
  out.negative_patch = { departure_id: target, http: res.status, detail: (res.body as any)?.detail };
  const list = await get(page, `/catalog/trip-plans/${F.tour_source_id}/departures`);
  out.real_departure_after = pick(((list.body?.items ?? []) as any[]).find((d) => d.id === target), DEP_KEYS);
  if (OUT) writeFileSync(OUT, JSON.stringify(out, null, 1));
  expect([res.status, (res.body as any)?.detail]).toEqual([403, "e2e_synthetic_only"]);
  expect(out.real_departure_after).toEqual(out.real_departure_before);
  await page.context().close();
});

test.afterAll(() => { if (OUT) writeFileSync(OUT, JSON.stringify(out, null, 1)); });
