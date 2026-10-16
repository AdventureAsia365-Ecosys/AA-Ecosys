// S239 AA-668 live verify, part 2 (Done-when a): Social Content on CIS Dev, tenant terra-family, LinkedIn.
// Slate → Pick to write → Goal → Generate 3 angles (ONE t8_angles job) → Write with this angle (ONE t9_write job)
// → streamed text → piece saved → Open in My Content. Route guards abort any second pick / goal / write POST.
// Step "brand" first sets the tenant brand's Default Call to Action through the Brand page (test edit on a test
// tenant, approved S239) because terra-family had none. Secrets read in-process, never printed.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const OUT = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-16-S239-in-progress-audit/aa668-verify";
const JSON_OUT = "/home/nghiep/projects/AA-Ecosys/.tmp-session/s239/aa668_social_out.json";
const SLUG = "terra-family";
const SUBJECT = process.env.SUBJECT || "Punakha Dzong — visit";
const CTA = "Message us to start planning your family trip.";
mkdirSync(`${OUT}/video`, { recursive: true });
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const log = { started: new Date().toISOString(), tenant: SLUG, subject: SUBJECT, console_errors: [], http_errors: [], posts: {}, events: [] };
const ev = (m) => { const e = `${new Date().toISOString()} ${m}`; log.events.push(e); console.log(e); };
const save = () => writeFileSync(JSON_OUT, JSON.stringify(log, null, 1));
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, recordVideo: { dir: `${OUT}/video/social-run2`, size: { width: 1440, height: 900 } } });
const p = await ctx.newPage();
p.on("console", (m) => { if (m.type() === "error") log.console_errors.push(m.text().slice(0, 200)); });
p.on("pageerror", (e) => log.console_errors.push("pageerror: " + String(e).slice(0, 200)));
p.on("response", (r) => { if (r.status() >= 400 && r.url().startsWith(BASE)) log.http_errors.push(`${r.status()} ${r.request().method()} ${r.url().replace(BASE, "").slice(0, 120)}`); });
const tget = (path) => p.evaluate(async (u) => { const r = await fetch(u, { cache: "no-store" }); let j = null; try { j = await r.json(); } catch {} return { status: r.status, j }; }, path);
const layout = () => p.evaluate(() => {
  const d = [...document.querySelectorAll('[role="dialog"]')].pop(); const r = d?.getBoundingClientRect();
  return { vw: innerWidth, vh: innerHeight, dialog: r ? { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } : null,
    dialog_fits: r ? r.y >= 0 && r.y + r.height <= innerHeight + 1 && r.x >= 0 && r.x + r.width <= innerWidth + 1 : null,
    page_overflow_x: document.documentElement.scrollWidth - innerWidth, scrollY: scrollY };
});
const shot = (n) => p.screenshot({ path: `${OUT}/${n}.png` });
const guard = (pattern, key) => p.route(pattern, (route) => {
  if (route.request().method() !== "POST") return route.continue();
  log.posts[key] = (log.posts[key] ?? 0) + 1;
  if (log.posts[key] > 1) { log.posts[`${key}_blocked`] = true; return route.abort(); }
  return route.continue();
});
const progressSummary = (j) => j && j.found ? { found: true, status: j.status, revision: j.revision, steps: (j.steps ?? []).map((s) => `${s.label}:${s.state}`), text_chars: (j.sections ?? []).reduce((a, s) => a + (s.text?.length ?? 0), 0) } : { found: j?.found ?? null };

try {
  await p.goto(`${BASE}/tenant-login`); await p.fill('input[type="password"]', sec(`aa-cis/dev/e2e-tenant/${SLUG}`));
  await Promise.all([p.waitForURL(/\/portal/, { timeout: 30000 }), p.click('button:has-text("Access Portal")')]);

  // ── brand default CTA (test edit) ──
  const br0 = await tget("/api/tenant/admin/brand-identity");
  log.brand_before = { status: br0.status, version: br0.j?.version, default_cta: br0.j?.default_cta };
  if (!br0.j?.default_cta) {
    await p.goto(`${BASE}/portal/t0-brand`, { waitUntil: "networkidle" }); await p.waitForTimeout(2500);
    const input = p.getByText("Default Call to Action", { exact: true }).locator("xpath=following::input[1]");
    await input.fill(CTA);
    await p.waitForTimeout(800);
    const [sr] = await Promise.all([
      p.waitForResponse((r) => r.url().includes("/brand-identity") && r.request().method() === "POST", { timeout: 30000 }),
      p.getByRole("button", { name: /Save as New Version/ }).click(),
    ]);
    log.brand_save = { status: sr.status() };
    await p.waitForTimeout(2000);
    await shot("s00-brand-default-cta-saved-1440");
    const br1 = await tget("/api/tenant/admin/brand-identity");
    log.brand_after = { status: br1.status, version: br1.j?.version, default_cta: br1.j?.default_cta };
    ev(`brand default_cta set: v${log.brand_before.version} -> v${log.brand_after.version}`);
  }
  save();

  // ── Slate → LinkedIn → Pick to write ──
  await guard("**/api/tenant/v1/subjects/*/pick", "pick");
  await guard("**/api/tenant/v1/angle-gate/requests/*/goal", "goal");
  await guard("**/api/tenant/v1/content-writing/requests/*/write", "write");
  await p.goto(`${BASE}/portal/t7-planning`, { waitUntil: "networkidle" }); await p.waitForTimeout(2500);
  await p.getByRole("button", { name: /^LinkedIn/ }).click();
  await p.getByText(SUBJECT, { exact: true }).first().waitFor({ timeout: 30000 });
  await p.waitForTimeout(1000);
  await shot("s01-slate-linkedin-1440");
  const [pickR] = await Promise.all([
    p.waitForResponse((r) => /\/subjects\/[^/]+\/pick/.test(r.url()) && r.request().method() === "POST", { timeout: 30000 }),
    p.getByText(SUBJECT, { exact: true }).first().locator("xpath=ancestor::div[3]").getByRole("button", { name: /Pick to write/ }).click(),
  ]);
  const pick = await pickR.json().catch(() => null);
  log.pick = { status: pickR.status(), path: pickR.url().replace(BASE, "").replace("/api/tenant", ""), body: pick };
  const REQ = pick?.request_id; log.request_id = REQ;
  ev(`pick ${pickR.status()} request=${REQ}`);
  await p.getByTestId("writer-panel").waitFor({ timeout: 20000 });
  await p.locator('[data-testid^="goal-"]').first().waitFor({ timeout: 20000 });
  log.goal_testids = await p.locator('[data-testid^="goal-"]').evaluateAll((els) => els.map((e) => e.getAttribute("data-testid")));
  await p.waitForTimeout(1000);
  log.panel_header = { title: await p.getByTestId("writer-panel-title").innerText(), context: await p.getByTestId("writer-panel-context").innerText() };
  log.layout_goal = await layout();
  await shot("s02-panel-goal-1440");

  // ── Goal → Generate 3 angles (t8_angles) ──
  await p.locator('[data-testid^="goal-"]', { hasText: "Introduction / Awareness" }).first().click();
  const [goalR] = await Promise.all([
    p.waitForResponse((r) => r.url().includes("/goal") && r.request().method() === "POST", { timeout: 30000 }),
    p.getByRole("button", { name: /Generate 3 angles/ }).click(),
  ]);
  const gj = await goalR.json().catch(() => null);
  log.goal_post = { status: goalR.status(), goal: gj?.goal, generating: gj?.generating, status_field: gj?.status, cta: gj?.cta, keys: gj ? Object.keys(gj) : null };
  ev(`goal ${goalR.status()}`);
  await p.waitForTimeout(2500);
  await shot("s03-panel-generating-angles-1440");
  await p.getByTestId("angle-0").waitFor({ timeout: 300000 });
  await p.waitForTimeout(1500);
  log.angles = await p.locator('[data-testid^="angle-"]').allInnerTexts().then((a) => a.map((t) => t.replace(/\s+/g, " ").slice(0, 160)));
  log.layout_angles = await layout();
  await shot("s04-panel-angles-1440");
  ev(`angles ready (${log.angles.length})`);

  // ── Write with this angle (t9_write) ──
  let writeBody = null;
  p.on("request", (r) => { if (/\/content-writing\/requests\/[^/]+\/write$/.test(r.url()) && r.method() === "POST") writeBody = r.postData(); });
  const [writeR] = await Promise.all([
    p.waitForResponse((r) => /\/content-writing\/requests\/[^/]+\/write$/.test(r.url()) && r.request().method() === "POST", { timeout: 60000 }),
    p.getByTestId("angle-0").getByRole("button", { name: /Write with this angle/ }).click(),
  ]);
  const wj = await writeR.json().catch(() => null);
  log.write_post = { status: writeR.status(), request_body: writeBody, body: wj };
  const PIECE = wj?.piece_id; log.piece_id = PIECE; log.t9_job_id = wj?.job_id ?? null;
  ev(`write ${writeR.status()} piece=${PIECE} job=${wj?.job_id}`);
  save();
  const t0 = Date.now(); let prog = null;
  while (PIECE && Date.now() - t0 < 180000) {
    prog = progressSummary((await tget(`/api/tenant/v1/progress/piece/${PIECE}`)).j);
    if (prog.found && (prog.text_chars > 250 || prog.status !== "running")) break;
    await p.waitForTimeout(3000);
  }
  await p.waitForTimeout(1500);
  log.cta_prompt_seen_during_write = await p.getByText(/needs a call to action/).count();
  log.progress_streaming = prog;
  log.panel_text_writing = (await p.getByTestId("writer-panel").innerText()).slice(0, 700);
  log.layout_writing = await layout();
  await shot("s05-panel-streaming-1440");
  await p.setViewportSize({ width: 390, height: 844 }); await p.waitForTimeout(1200);
  log.layout_writing_390 = await layout();
  await shot("s06-panel-streaming-390");
  await p.setViewportSize({ width: 1440, height: 900 }); await p.waitForTimeout(1000);
  ev(`streaming ${JSON.stringify(prog)}`);

  await p.getByTestId("writer-panel-result").waitFor({ timeout: 600000 });
  await p.waitForTimeout(2000);
  log.cta_prompt_seen_final = await p.getByText(/needs a call to action/).count();
  log.layout_result = await layout();
  log.result_actions = await p.getByRole("dialog").last().getByRole("button").allInnerTexts().then((a) => a.map((t) => t.trim()).filter(Boolean));
  log.result_text_preview = (await p.getByTestId("writer-panel-result").innerText()).slice(0, 400);
  await shot("s07-panel-piece-saved-1440");
  await p.setViewportSize({ width: 390, height: 844 }); await p.waitForTimeout(1200);
  log.layout_result_390 = await layout();
  await shot("s08-panel-piece-saved-390");
  await p.setViewportSize({ width: 1440, height: 900 }); await p.waitForTimeout(1000);
  ev("result shown");

  // ── API evidence (tenant API) ──
  const piece = await tget(`/api/tenant/v1/content-writing/pieces/${PIECE}`);
  log.api_piece = { status: piece.status, keys: piece.j ? Object.keys(piece.j) : null, ready_state: piece.j?.ready_state, channel: piece.j?.channel, job_id: piece.j?.job_id, version: piece.j?.version ?? piece.j?.version_number ?? null,
    angle_gate_request_id: piece.j?.angle_gate_request_id, content_chars: (piece.j?.content_text ?? "").length, created_at: piece.j?.created_at };
  const latest = await tget(`/api/tenant/v1/content-writing/requests/${REQ}/latest-piece`);
  log.api_latest_piece = { status: latest.status, piece_id: latest.j?.piece?.piece_id ?? latest.j?.piece_id, ready_state: latest.j?.piece?.ready_state };
  const req = await tget(`/api/tenant/v1/angle-gate/requests/${REQ}`);
  log.api_request = { status: req.status, req_status: req.j?.status, goal: req.j?.goal, channel: req.j?.channel, cta: req.j?.cta, chosen: (req.j?.angles ?? []).filter((a) => a.chosen).map((a) => a.name), angle_count: (req.j?.angles ?? []).length, subject_id: req.j?.subject_id };
  const rev = await tget(`/api/tenant/v1/content-writing/requests/${REQ}/review`);
  log.api_review = { status: rev.status, keys: rev.j ? Object.keys(rev.j) : null };
  const reviews = await tget(`/api/tenant/v1/content-writing/reviews`);
  const rows = Array.isArray(reviews.j) ? reviews.j : reviews.j?.data ?? reviews.j?.items ?? reviews.j?.rows ?? [];
  const mine = rows.find((r) => JSON.stringify(r).includes(REQ));
  log.api_reviews = { status: reviews.status, total_rows: rows.length, has_request: !!mine, row: mine ? Object.fromEntries(Object.entries(mine).filter(([k]) => !/text|content|body/i.test(k))) : null };
  log.api_progress_final = progressSummary((await tget(`/api/tenant/v1/progress/piece/${PIECE}`)).j);
  save();

  // ── Open in My Content ──
  await p.getByRole("button", { name: /Open in My Content/ }).click();
  await p.waitForURL(/t10-review/, { timeout: 20000 });
  await p.waitForLoadState("networkidle"); await p.waitForTimeout(3000);
  log.my_content_url = p.url().replace(BASE, "");
  log.my_content_text = (await p.locator("main").innerText().catch(() => "")).slice(0, 500);
  await shot("s09-my-content-1440");
  ev("my content opened");
} catch (e) {
  log.error = String(e).slice(0, 500); ev("ERROR " + log.error);
  await shot("s99-error-1440").catch(() => {});
} finally {
  log.finished = new Date().toISOString(); save(); await ctx.close(); await b.close();
}
