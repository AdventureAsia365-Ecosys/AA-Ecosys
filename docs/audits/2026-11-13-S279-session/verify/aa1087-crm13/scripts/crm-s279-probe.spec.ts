// S279 verify-only (never committed): the board's AA cancelled filter (ids + the cases), screenshot of the filtered board.
import { test } from "@playwright/test";
import fs from "node:fs";
import { landOnPartner, signIn } from "../helpers/signin";
const PARTNER = (process.env.E2ECRMPARTNER ?? "").replace(/\/+$/, "");
test("probe", async ({ page }) => {
  test.skip(process.env.E2ECRMAACANCEL !== "probe");
  test.setTimeout(240_000);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`${PARTNER}/pipeline`);
  await signIn(page, { email: process.env.E2ECRMEMAIL!, password: process.env.E2ECRMPASSWORD, totpSecret: process.env.E2ECRMTOTP });
  await landOnPartner(page, PARTNER);
  const call = (u: string) => page.evaluate(async (u) => { const r = await fetch(`/bff/${u}`, { headers: { Accept: "application/json" } }); return { status: r.status, body: await r.json().catch(() => null) }; }, u);
  const board = await call("pipeline?issue=aa_cancelled");
  const cards = [...(board.body?.stages ?? []).flatMap((s: any) => (s.cards ?? []).map((c: any) => ({ ...c, stage: s.key ?? s.stage }))), ...(board.body?.closed?.cards ?? [])];
  const out: any = { board_http: board.status, cards: [] };
  for (const c of cards) {
    const t = await call(`trips/${c.trip_id}`);
    out.cards.push({ trip_id: c.trip_id, stage: c.stage, title: c.title ?? c.client_name ?? c.name, cases: (t.body?.aa_cancel?.cases ?? []).map((k: any) => ({ id: k.id ?? k.case_id, departure_id: k.departure_id, active: k.active, status: k.status, can_requote: k.can_requote, tour_source_id: k.tour?.tour_source_id })) });
  }
  fs.writeFileSync(process.env.S279_OUT!, JSON.stringify(out, null, 1));
  await page.goto(`${PARTNER}/pipeline?issue=aa_cancelled`);
  await page.waitForTimeout(4000);
  await page.screenshot({ path: process.env.S279_SHOT!, fullPage: true });
});
