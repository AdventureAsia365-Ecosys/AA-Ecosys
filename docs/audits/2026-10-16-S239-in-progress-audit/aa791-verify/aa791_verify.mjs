// S239 AA-791 live verify (CIS #755): label form starts with no verdict; LABEL column next to Status.
// Dev write approved by Nghiệp (S239): one test label "ZZ S239 test label" as admin e2e-claude-code. Secrets in-process only.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const OUT = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-16-S239-in-progress-audit/aa791-verify";
mkdirSync(OUT, { recursive: true });
const CANDS = ["dde74641-455f-4d9d-9c8e-696dc3a456c8", "a7e18faf-4b68-4453-8020-000e38109674"];
const REASON = "ZZ S239 test label";
const STEP = process.argv[2] || "all"; // probe | all
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const log = { step: STEP, console_errors: [], net_errors: [] };
const b = await chromium.launch({ ignoreDefaultArgs: ["--hide-scrollbars"] });
const shot = (p, name, full = false) => p.screenshot({ path: `${OUT}/${name}.png`, fullPage: full });
const settle = async (p, ms = 2500) => { try { await p.waitForLoadState("networkidle", { timeout: 15000 }); } catch {} await p.waitForTimeout(ms); };

async function newCtx({ w = 1440, theme = "light" } = {}) {
  const ctx = await b.newContext({ viewport: w === 1440 ? { width: 1440, height: 900 } : { width: 390, height: 844 }, colorScheme: theme, deviceScaleFactor: 1 });
  await ctx.addInitScript((t) => { try { localStorage.setItem("cis_theme", t); } catch {} }, theme);
  return ctx;
}
async function adminLogin(ctx, tag) {
  const a = JSON.parse(sec("aa-cis/dev/e2e-test-admin"));
  const p = await ctx.newPage();
  p.on("console", (m) => { if (m.type() === "error") log.console_errors.push(`[${tag}] ${m.text().slice(0, 200)}`); });
  p.on("response", (r) => { if (r.status() >= 400 && r.url().includes("/api/")) log.net_errors.push(`[${tag}] ${r.status()} ${r.request().method()} ${r.url().replace(BASE, "")}`); });
  await p.goto(`${BASE}/login`, { waitUntil: "load" }); await p.waitForTimeout(2000);
  await p.fill('input[placeholder="Username"]', a.username); await p.fill('input[type="password"]', a.password);
  await p.locator("button", { hasText: "Login" }).click();
  await p.waitForURL((u) => !u.toString().includes("/login"), { timeout: 45000 });
  log.admin_username = a.username;
  return p;
}
const api = (p, path, init) => p.evaluate(async ({ path, init }) => {
  const h = { "content-type": "application/json" }; const rid = localStorage.getItem("cis_reviewer_id"); if (rid) h["x-reviewer-id"] = rid;
  const r = await fetch(path, { ...(init || {}), headers: h }); let j = null; try { j = await r.json(); } catch {} return { status: r.status, j };
}, { path, init });
const layout = (p) => p.evaluate(() => {
  const d = document.documentElement;
  const th = [...document.querySelectorAll("th")].map((t) => ({ t: t.innerText.trim().split("\n")[0], l: Math.round(t.getBoundingClientRect().left), r: Math.round(t.getBoundingClientRect().right) }));
  return { doc_scroll: [d.scrollWidth, d.clientWidth], body_scroll: [document.body.scrollWidth, document.body.clientWidth], headers: th, theme: d.getAttribute("data-theme"), vw: innerWidth };
});

try {
  // ── 1440 light: probe, form, save ──
  const ctx = await newCtx(); const p = await adminLogin(ctx, "1440");
  await p.goto(`${BASE}/admin/content-quality?tab=pieces`, { waitUntil: "load" }); await settle(p);
  log.probe = {};
  for (const id of CANDS) {
    const lab = await api(p, `/api/admin/content-quality/pieces/${id}/label`);
    const det = await api(p, `/api/admin/content-quality/pieces/${id}`);
    log.probe[id] = { label_status: lab.status, labels: lab.j?.labels?.length ?? null, mine: lab.j?.mine ?? null, label_err: lab.status >= 400 ? lab.j : undefined,
      detail_status: det.status, piece_status: det.j?.status, tenant: det.j?.tenant_name ?? det.j?.tenant_id, channel: det.j?.channel, title: det.j?.title ?? det.j?.seo_title };
  }
  const PIECE = CANDS.find((id) => log.probe[id].label_status === 200 && log.probe[id].labels === 0 && ["approved", "held"].includes(log.probe[id].piece_status));
  log.piece = PIECE ?? null;
  if (STEP === "probe" || !PIECE) { if (!PIECE) log.aborted = "no unlabelled approved/held candidate"; throw new Error("stop"); }

  await p.goto(`${BASE}/admin/content-quality?tab=pieces&piece=${PIECE}`, { waitUntil: "load" }); await settle(p, 3000);
  const form = p.getByTestId("cq-label-form");
  await form.waitFor({ timeout: 30000 });
  await form.scrollIntoViewIfNeeded(); await p.waitForTimeout(500);
  const save = p.getByTestId("cq-label-save").getByRole("button");
  log.before = {
    aria_checked: Object.fromEntries(await Promise.all(["as_is", "light", "heavy", "reject"].map(async (l) => [l, await p.getByTestId(`cq-label-${l}`).getAttribute("aria-checked")]))),
    save_disabled: await save.isDisabled(), save_text: await save.innerText(),
    pick_hint_visible: await p.getByTestId("cq-label-pick-hint").isVisible().catch(() => false),
  };
  await shot(p, "01-unlabelled-no-verdict-save-disabled-1440-light");
  await p.getByTestId("cq-label-light").click();
  await p.getByLabel("Voice defects").selectOption("light");
  await p.getByLabel("Minutes to fix").fill("5");
  await p.getByLabel("Reason").fill(REASON);
  log.after_pick = { light_checked: await p.getByTestId("cq-label-light").getAttribute("aria-checked"), save_enabled: await save.isEnabled(), pick_hint_count: await p.getByTestId("cq-label-pick-hint").count() };
  await shot(p, "02-light-voice-5min-reason-filled-1440-light");
  const respP = p.waitForResponse((r) => r.url().includes(`/content-quality/pieces/${PIECE}/label`) && r.request().method() === "POST", { timeout: 30000 });
  await save.click();
  const resp = await respP; const rb = await resp.json().catch(() => null);
  log.post = { status: resp.status(), request_body: JSON.parse(resp.request().postData() || "{}"), mine: rb?.mine ?? null };
  await p.waitForTimeout(700);
  log.toast = await p.getByText(/Labelled Light/).first().innerText().catch(() => null);
  await shot(p, "03-saved-toast-1440-light");
  await p.waitForTimeout(1500);
  log.after_save_form = { save_text: await save.innerText().catch(() => null), light_checked: await p.getByTestId("cq-label-light").getAttribute("aria-checked") };
  const g = await api(p, `/api/admin/content-quality/pieces/${PIECE}/label`);
  log.get_label = { status: g.status, labels: g.j?.labels?.map((l) => ({ labelled_by: l.labelled_by, label: l.label, defects: l.defects, minutes_to_fix: l.minutes_to_fix, reason: l.reason, labelled_at: l.labelled_at, text_changed_since_label: l.text_changed_since_label })), mine: g.j?.mine ?? null };

  // ── table at 1440: Labelled filter + LABEL column position ──
  const lf = await api(p, `/api/admin/content-quality/pieces?label=labelled&limit=200`);
  const lfRow = (lf.j?.data ?? []).find((r) => r.piece_id === PIECE);
  log.api_labelled_filter = { status: lf.status, total: lf.j?.total, has_piece: !!lfRow, row_label: lfRow?.label, row_label_count: lfRow?.label_count };
  const lx = await api(p, `/api/admin/content-quality/pieces?label=light&limit=200`);
  log.api_light_filter = { status: lx.status, total: lx.j?.total, has_piece: !!(lx.j?.data ?? []).find((r) => r.piece_id === PIECE) };
  await p.goto(`${BASE}/admin/content-quality?tab=pieces&label=labelled`, { waitUntil: "load" }); await settle(p, 3000);
  const L1 = await layout(p);
  const labelTh = L1.headers.find((h) => /^label/i.test(h.t));
  const statusIdx = L1.headers.findIndex((h) => /^status/i.test(h.t));
  const titleText = log.probe[PIECE].title || "";
  const rowsInfo = await p.evaluate(({ titleText }) => {
    const rows = [...document.querySelectorAll("tbody tr")];
    const ths = [...document.querySelectorAll("th")].map((t) => t.innerText.trim().split("\n")[0]);
    const li = ths.findIndex((t) => /^label/i.test(t));
    return { rows: rows.length, label_filter_value: document.querySelector('select[aria-label="Label"]')?.value ?? null,
      match: rows.filter((r) => titleText && r.innerText.includes(titleText.slice(0, 40))).map((r) => { const c = r.querySelectorAll("td")[li]; const b = c?.getBoundingClientRect(); return { label_cell: c?.innerText.trim(), cell_left: b && Math.round(b.left), cell_right: b && Math.round(b.right) }; }) };
  }, { titleText });
  log.table_1440 = { doc_scroll: L1.doc_scroll, body_scroll: L1.body_scroll, theme: L1.theme, header_order: L1.headers.map((h) => h.t), label_th: labelTh, label_index: L1.headers.indexOf(labelTh), status_index: statusIdx,
    label_th_in_viewport: !!labelTh && labelTh.r <= 1440, page_hscroll: L1.doc_scroll[0] > L1.doc_scroll[1], ...rowsInfo };
  await shot(p, "04-labelled-filter-label-badge-1440-light");
  await ctx.close();

  // ── 390 dark ──
  const c2 = await newCtx({ w: 390, theme: "dark" }); const q = await adminLogin(c2, "390d");
  await q.goto(`${BASE}/admin/content-quality?tab=pieces&label=labelled`, { waitUntil: "load" }); await settle(q, 3000);
  const L2 = await layout(q);
  log.table_390_dark = { theme: L2.theme, doc_scroll: L2.doc_scroll, page_hscroll: L2.doc_scroll[0] > L2.doc_scroll[1] };
  await shot(q, "05-labelled-filter-390-dark");
  await q.goto(`${BASE}/admin/content-quality?tab=pieces&piece=${PIECE}`, { waitUntil: "load" }); await settle(q, 3000);
  const f2 = q.getByTestId("cq-label-form"); await f2.waitFor({ timeout: 30000 }); await f2.scrollIntoViewIfNeeded(); await q.waitForTimeout(500);
  log.drawer_390_dark = { light_checked: await q.getByTestId("cq-label-light").getAttribute("aria-checked"), save_text: await q.getByTestId("cq-label-save").getByRole("button").innerText(),
    theme: await q.evaluate(() => document.documentElement.getAttribute("data-theme")), doc_scroll: await q.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]) };
  await shot(q, "06-drawer-saved-label-390-dark");
  await c2.close();
} catch (e) { if (String(e) !== "Error: stop") log.error = String(e).slice(0, 600); }
await b.close();
writeFileSync(`${OUT}/run-${STEP}.json`, JSON.stringify(log, null, 1));
console.log(JSON.stringify(log, null, 1));
