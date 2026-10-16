// S239 AA-668 live verify, part 1: tour rewrite through the Writer panel on CIS Dev, tenant terra-family.
// ONE paid T2 rewrite (route guard aborts a second POST). Approved by Nghiệp in S239 (small paid runs on test tenants).
// Two browser contexts on the same tenant: A requests the rewrite, closes the panel mid-write, reopens it with
// "View progress", closes again and waits for the toast; B opens the same running version (View progress) at 390,
// keeps the panel open to the ready state, then "Open in My Catalog". Secrets read in-process, never printed.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const OUT = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-16-S239-in-progress-audit/aa668-verify";
const JSON_OUT = "/home/nghiep/projects/AA-Ecosys/.tmp-session/s239/aa668_rewrite_out.json";
const SLUG = "terra-family";
const TOUR = "Laos to Vietnam by Bicycle";
mkdirSync(`${OUT}/video`, { recursive: true });
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const log = { started: new Date().toISOString(), tenant: SLUG, A: { console_errors: [], http_errors: [] }, B: { console_errors: [], http_errors: [] }, events: [] };
const ev = (m) => { const e = `${new Date().toISOString()} ${m}`; log.events.push(e); console.log(e); };
const save = () => writeFileSync(JSON_OUT, JSON.stringify(log, null, 1));
const b = await chromium.launch();

async function tenantCtx(tag, vp) {
  const ctx = await b.newContext({ viewport: vp, recordVideo: { dir: `${OUT}/video/rewrite-${tag}`, size: vp } });
  const p = await ctx.newPage();
  const L = log[tag];
  p.on("console", (m) => { if (m.type() === "error") L.console_errors.push(m.text().slice(0, 200)); });
  p.on("pageerror", (e) => L.console_errors.push("pageerror: " + String(e).slice(0, 200)));
  p.on("response", (r) => { if (r.status() >= 400 && r.url().startsWith(BASE)) L.http_errors.push(`${r.status()} ${r.request().method()} ${r.url().replace(BASE, "").slice(0, 120)}`); });
  await p.goto(`${BASE}/tenant-login`); await p.fill('input[type="password"]', sec(`aa-cis/dev/e2e-tenant/${SLUG}`));
  await Promise.all([p.waitForURL(/\/portal/, { timeout: 30000 }), p.click('button:has-text("Access Portal")')]);
  return { ctx, p };
}
const tget = (p, path) => p.evaluate(async (u) => { const r = await fetch(u, { cache: "no-store" }); let j = null; try { j = await r.json(); } catch {} return { status: r.status, j }; }, path);
const layout = (p) => p.evaluate(() => {
  const d = document.querySelector('[role="dialog"]'); const r = d?.getBoundingClientRect();
  return { vw: innerWidth, vh: innerHeight, dialog: r ? { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } : null,
    dialog_fits: r ? r.y >= 0 && r.y + r.height <= innerHeight + 1 && r.x >= 0 && r.x + r.width <= innerWidth + 1 : null,
    page_overflow_x: document.documentElement.scrollWidth - innerWidth, scrollY: scrollY };
});
const shot = (p, n) => p.screenshot({ path: `${OUT}/${n}.png` });
const progressSummary = (j) => j && j.found ? { found: true, status: j.status, revision: j.revision, steps: (j.steps ?? []).map((s) => `${s.label}:${s.state}`), text_chars: (j.sections ?? []).reduce((a, s) => a + (s.text?.length ?? 0), 0) } : { found: j?.found ?? null };
const rowOf = async (p, vid) => { const r = await tget(p, "/api/tenant/v1/tours/my-versions?page_size=50"); const v = (r.j?.data ?? []).find((x) => x.id === vid); return v ? { status_code: r.status, id: v.id, version_number: v.version_number, status: v.status, edit_source: v.edit_source, job_status: v.job_status, rewrite_language: v.rewrite_language } : { status_code: r.status, missing: true }; };

try {
  // ── A: open a finished version, Request Rewrite ──
  const A = await tenantCtx("A", { width: 1440, height: 900 });
  const pa = A.p;
  let rewritePosts = 0;
  await pa.route("**/api/tenant/v1/tours/pool/*/rewrite", (route) => {
    if (route.request().method() === "POST" && ++rewritePosts > 1) { log.A.blocked_second_rewrite = true; return route.abort(); }
    return route.continue();
  });
  await pa.goto(`${BASE}/portal/t4-pool`, { waitUntil: "networkidle" }); await pa.waitForTimeout(2500);
  await shot(pa, "r01-my-catalog-list-1440");
  const row = pa.locator("tr", { hasText: TOUR });
  await row.getByRole("button", { name: /Open/ }).first().click();
  await pa.getByRole("button", { name: "Request Rewrite" }).waitFor({ timeout: 20000 });
  await pa.waitForTimeout(1500);
  log.A.before_drawer_text = (await pa.getByRole("dialog").last().innerText()).slice(0, 200);
  await shot(pa, "r02-finished-version-drawer-1440");
  ev("A: version drawer open, requesting rewrite");
  const [resp] = await Promise.all([
    pa.waitForResponse((r) => r.url().includes("/rewrite") && r.request().method() === "POST", { timeout: 30000 }),
    pa.getByRole("button", { name: "Request Rewrite" }).click(),
  ]);
  const rw = await resp.json().catch(() => null);
  log.rewrite_post = { status: resp.status(), path: resp.url().replace(BASE, ""), body: rw };
  const VID = rw?.version_id; log.version_id = VID; log.job_id = rw?.job_id ?? null;
  ev(`A: POST rewrite ${resp.status()} version=${VID} job=${rw?.job_id}`);
  save();
  if (!VID) throw new Error("no version_id");
  await pa.getByTestId("writer-panel").waitFor({ timeout: 20000 });
  await pa.waitForTimeout(2000);
  log.A.panel_header = { title: await pa.getByTestId("writer-panel-title").innerText(), context: await pa.getByTestId("writer-panel-context").innerText() };
  log.A.dialog_count_after_request = await pa.getByRole("dialog").count();
  log.A.layout_starting = await layout(pa);
  await shot(pa, "r03-panel-starting-1440");
  // wait for live text
  const t0 = Date.now(); let prog = null;
  while (Date.now() - t0 < 300000) {
    const r = await tget(pa, `/api/tenant/v1/progress/tour/${VID}`);
    prog = progressSummary(r.j);
    if (prog.found && prog.text_chars > 300) break;
    if (prog.found && prog.status && prog.status !== "running") break;
    await pa.waitForTimeout(5000);
  }
  await pa.waitForTimeout(3000);
  log.A.progress_writing = prog;
  log.A.panel_text_writing = (await pa.getByTestId("writer-panel").innerText()).slice(0, 600);
  log.A.layout_writing = await layout(pa);
  await shot(pa, "r04-panel-live-writing-1440");
  ev(`A: live progress ${JSON.stringify(prog)}`);
  // close mid-write
  await pa.getByRole("button", { name: "Close" }).first().click();
  await pa.waitForTimeout(2500);
  log.A.after_close = { dialogs: await pa.getByRole("dialog").count(), row: await rowOf(pa, VID), progress: progressSummary((await tget(pa, `/api/tenant/v1/progress/tour/${VID}`)).j),
    row_text: (await pa.locator("tr", { hasText: TOUR }).first().innerText().catch(() => "")).replace(/\s+/g, " ").slice(0, 200) };
  await shot(pa, "r05-closed-mid-write-row-writing-1440");
  ev(`A: closed mid-write ${JSON.stringify(log.A.after_close.row)}`);
  // View progress reopens it (A), then close again so the watcher toasts
  await pa.locator("tr", { hasText: TOUR }).first().getByRole("button", { name: /View progress/ }).click();
  await pa.getByTestId("writer-panel").waitFor({ timeout: 15000 });
  await pa.waitForTimeout(2500);
  log.A.reopened = { title: await pa.getByTestId("writer-panel-title").innerText(), context: await pa.getByTestId("writer-panel-context").innerText(), text: (await pa.getByTestId("writer-panel").innerText()).slice(0, 300) };
  await shot(pa, "r06-view-progress-reopened-1440");
  await pa.getByRole("button", { name: "Close" }).first().click();
  await pa.waitForTimeout(1500);
  log.A.closed_again_at = new Date().toISOString();
  ev("A: reopened via View progress and closed again; waiting for toast");
  save();

  // ── B: same running version at 390, panel kept open to ready ──
  // FIX after run 1: on a 390 viewport My Catalog renders cards, not <tr> rows, so B opens the panel at 1440 and
  // then resizes to 390 (the panel itself is what the 390 check is about).
  const B = await tenantCtx("B", { width: 1440, height: 900 });
  const pb = B.p;
  await pb.goto(`${BASE}/portal/t4-pool`, { waitUntil: "networkidle" }); await pb.waitForTimeout(3000);
  await pb.locator("tr", { hasText: TOUR }).first().getByRole("button", { name: /View progress/ }).click();
  await pb.getByTestId("writer-panel").waitFor({ timeout: 15000 });
  await pb.setViewportSize({ width: 390, height: 844 });
  await pb.waitForTimeout(3000);
  log.B.layout_writing_390 = await layout(pb);
  await shot(pb, "r07-panel-writing-390");
  ev(`B: panel open at 390 ${JSON.stringify(log.B.layout_writing_390)}`);

  const waitToast = (async () => {
    const loc = pa.getByText(/is ready — find it in My Catalog Tours|didn.t finish — open it in My Catalog Tours|is still being written — it will show up in My Catalog Tours/);
    await loc.first().waitFor({ timeout: 25 * 60000 });
    log.A.toast = { text: await loc.first().innerText(), at: new Date().toISOString() };
    await shot(pa, "r08-toast-after-close-1440");
    ev(`A: toast "${log.A.toast.text}"`);
    await pa.waitForTimeout(6000);
    log.A.row_after_toast = (await pa.locator("tr", { hasText: TOUR }).first().innerText().catch(() => "")).replace(/\s+/g, " ").slice(0, 200);
  })().catch((e) => { log.A.toast_error = String(e).slice(0, 200); });

  const waitReady = (async () => {
    await pb.setViewportSize({ width: 1440, height: 900 }); await pb.waitForTimeout(1500);
    await shot(pb, "r07b-panel-writing-1440-B");
    const r = pb.getByTestId("tour-rewrite-ready").or(pb.getByTestId("tour-rewrite-failed"));
    await r.first().waitFor({ timeout: 25 * 60000 });
    log.B.final_state = await pb.getByTestId("tour-rewrite-ready").count() ? "ready" : "failed";
    log.B.ready_at = new Date().toISOString();
    await pb.waitForTimeout(3000);
    log.B.layout_ready_1440 = await layout(pb);
    log.B.panel_ready_text = (await pb.getByRole("dialog").last().innerText()).slice(0, 800);
    await shot(pb, "r09-panel-ready-1440");
    await pb.setViewportSize({ width: 390, height: 844 }); await pb.waitForTimeout(1500);
    log.B.layout_ready_390 = await layout(pb);
    await shot(pb, "r10-panel-ready-390");
    await pb.setViewportSize({ width: 1440, height: 900 }); await pb.waitForTimeout(1500);
    ev(`B: ${log.B.final_state}`);
    if (log.B.final_state === "ready") {
      await pb.getByRole("button", { name: /Open in My Catalog/ }).click();
      await pb.getByRole("button", { name: "Request Rewrite" }).waitFor({ timeout: 20000 });
      await pb.waitForTimeout(2500);
      log.B.opened_in_catalog = { dialogs: await pb.getByRole("dialog").count(), text: (await pb.getByRole("dialog").last().innerText()).slice(0, 300) };
      await shot(pb, "r11-open-in-my-catalog-drawer-1440");
    }
  })().catch((e) => { log.B.ready_error = String(e).slice(0, 200); });

  await Promise.all([waitToast, waitReady]);
  // API evidence after the run
  log.after = { row: await rowOf(pb, VID), detail: await tget(pb, `/api/tenant/v1/tours/versions/${VID}`).then((r) => ({ status: r.status, keys: r.j ? Object.keys(r.j) : null, version_number: r.j?.version_number, state: r.j?.status, edit_source: r.j?.edit_source, job_status: r.j?.job_status, aa_name: r.j?.aa_name, rewritten_chars: (r.j?.rewritten_content ?? "").length })),
    progress: progressSummary((await tget(pb, `/api/tenant/v1/progress/tour/${VID}`)).j), quota: (await tget(pb, "/api/tenant/v1/quota")).j };
  log.A.rewrite_posts = rewritePosts;
  ev(`after: ${JSON.stringify(log.after.row)}`);
  await A.ctx.close(); await B.ctx.close();
} catch (e) {
  log.error = String(e).slice(0, 500); ev("ERROR " + log.error);
} finally {
  log.finished = new Date().toISOString(); save(); await b.close();
}
