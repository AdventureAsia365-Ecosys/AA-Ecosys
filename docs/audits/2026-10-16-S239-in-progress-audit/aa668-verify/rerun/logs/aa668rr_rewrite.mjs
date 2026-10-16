// S239 AA-668 RE-VERIFY after CIS #759 (api :631 / worker :188, image dev-2090bb22): tour rewrite through the
// Writer panel, tenant terra-family. ONE paid T2 rewrite (~$0.13); a route guard aborts any second POST.
// A (1440, table rows): Request Rewrite on a finished version → panel → close mid-write → "View progress" with the
//   panel's progress answers HELD for 3 s (so any text shown comes from the remembered snapshot) → keep the panel
//   open to the end → ready state → "Open in My Catalog" opens the new version.
// B (390, cards): "View progress" on the writing card → panel at 390 → close mid-write → success toast at 390.
// A script poller reads GET /api/tenant/v1/progress/tour/{version_id} every ~0.5 s (APIRequestContext, not routed)
// and saves every response. Final sections are compared with the tenant API version's rewritten_content.
// Secrets read in-process, never printed.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const OUT = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-16-S239-in-progress-audit/aa668-verify/rerun";
const LOGS = `${OUT}/logs`;
const SLUG = "terra-family";
const TOUR = "Laos to Vietnam by Bicycle";
mkdirSync(`${OUT}/video/rewrite-A-1440`, { recursive: true }); mkdirSync(`${OUT}/video/rewrite-B-390`, { recursive: true }); mkdirSync(LOGS, { recursive: true });
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const log = { started: new Date().toISOString(), tenant: SLUG, A: { console_errors: [], http_errors: [] }, B: { console_errors: [], http_errors: [] }, events: [] };
const ev = (m) => { const e = `${new Date().toISOString()} ${m}`; log.events.push(e); console.log(e); };
const save = () => writeFileSync(`${LOGS}/rewrite.json`, JSON.stringify(log, null, 1));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const b = await chromium.launch();
const pagePolls = {}; // version id -> panel's own progress responses (A and B)

async function tenantCtx(tag, vp) {
  const ctx = await b.newContext({ viewport: vp, recordVideo: { dir: `${OUT}/video/rewrite-${tag}-${vp.width}`, size: vp } });
  const p = await ctx.newPage();
  const L = log[tag];
  p.on("console", (m) => { if (m.type() === "error") L.console_errors.push(m.text().slice(0, 200)); });
  p.on("pageerror", (e) => L.console_errors.push("pageerror: " + String(e).slice(0, 200)));
  p.on("response", (r) => { if (r.status() >= 400 && r.url().startsWith(BASE)) L.http_errors.push(`${r.status()} ${r.request().method()} ${r.url().replace(BASE, "").slice(0, 120)}`); });
  p.on("response", async (r) => {
    const m = r.url().match(/\/api\/tenant\/v1\/progress\/tour\/([^/?]+)/);
    if (!m) return;
    try { (pagePolls[m[1]] ??= []).push({ ctx: tag, t: new Date().toISOString(), status: r.status(), body: await r.text() }); } catch {}
  });
  await p.goto(`${BASE}/tenant-login`); await p.fill('input[type="password"]', sec(`aa-cis/dev/e2e-tenant/${SLUG}`));
  await Promise.all([p.waitForURL(/\/portal/, { timeout: 30000 }), p.click('button:has-text("Access Portal")')]);
  return { ctx, p };
}
const layout = (p) => p.evaluate(() => {
  const d = [...document.querySelectorAll('[role="dialog"]')].pop(); const r = d?.getBoundingClientRect();
  return { vw: innerWidth, vh: innerHeight, dialog: r ? { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } : null,
    dialog_fits: r ? r.y >= 0 && r.y + r.height <= innerHeight + 1 && r.x >= 0 && r.x + r.width <= innerWidth + 1 : null,
    page_overflow_x: document.documentElement.scrollWidth - innerWidth, scrollY: scrollY };
});
const shot = (p, n) => p.screenshot({ path: `${OUT}/${n}.png` });
const row = (p) => p.locator('[data-testid="kit-datatable-row"]', { hasText: TOUR }).first();
const secText = (j) => (j?.sections ?? []).map((s) => s.text ?? "").join("\n\n");
const progSummary = (j) => j && j.found ? { found: true, status: j.status, revision: j.revision, steps: (j.steps ?? []).map((s) => `${s.key}:${s.state}`), text_chars: secText(j).length, keys: (j.sections ?? []).map((s) => s.key) } : { found: j?.found ?? null };

// Expected sections from the saved rewritten_content, mirroring services/acp_shared/writing_progress.py
// (_TOUR_LABELS, _sections_from_values, strip_tags_streaming) for a complete JSON document.
const LABELS = ["name", "subtitle", "summary", "description", "highlights", "itineraries", "seo_title", "seo_meta"];
const stripTags = (t) => String(t).replace(/\s?\[(?:R|F):[^\]\n]{0,120}\]/g, "").replace(/\s?\[(?:[RF](?::[^\]\n]{0,120})?)?$/, "");
function expectedSections(rc) {
  const out = [];
  for (const [k, v] of Object.entries(rc ?? {})) {
    if (!LABELS.includes(k) || v == null) continue;
    const parts = [];
    if (k === "highlights" && Array.isArray(v)) { for (const h of v) if (h != null && typeof h !== "object") parts.push(`• ${stripTags(h)}`); }
    else if (k === "itineraries" && Array.isArray(v)) {
      v.forEach((it, idx) => {
        if (!it || typeof it !== "object") return; let day = null;
        for (const [f, fv] of Object.entries(it)) {
          if (fv == null || typeof fv === "object") continue;
          if (f === "day") day = stripTags(fv);
          else if (f === "title") parts.push(`Day ${day ?? idx + 1} — ${stripTags(fv)}`);
          else if (f === "body" || f === "description") parts.push(stripTags(fv));
        }
      });
    } else if (typeof v !== "object") parts.push(stripTags(v));
    const text = parts.filter(Boolean).join(k === "highlights" ? "\n" : "\n\n");
    if (parts.some(Boolean)) out.push({ key: k, text });
  }
  return out;
}
function analysePolls(polls, label) {
  let withReplacements = 0, braceStart = 0, jsonLooking = 0, maxChars = 0; const statuses = {}, revisions = new Set(), bad = [];
  for (const x of polls) {
    if (/replacements/.test(x.body)) { withReplacements++; bad.push({ t: x.t, why: "replacements" }); }
    let j = null; try { j = JSON.parse(x.body); } catch {}
    if (!j) continue;
    const st = j.status ?? (j.found === false ? "not_found" : "?"); statuses[st] = (statuses[st] ?? 0) + 1;
    if (j.revision != null) revisions.add(j.revision);
    for (const s of j.sections ?? []) {
      const t = (s.text ?? "").trimStart();
      if (t.startsWith("{")) { braceStart++; bad.push({ t: x.t, why: "section starts with {", key: s.key }); }
      if (/"[a-z_]+"\s*:/.test(t)) { jsonLooking++; bad.push({ t: x.t, why: "json key in text", key: s.key }); }
    }
    maxChars = Math.max(maxChars, secText(j).length);
  }
  return { label, responses: polls.length, statuses, revisions: [...revisions], max_chars: maxChars, with_replacements: withReplacements, section_starts_with_brace: braceStart, json_key_in_text: jsonLooking, bad: bad.slice(0, 10) };
}

let A, B, VID;
const poll = { polls: [], stop: false };
try {
  // B logs in first (390) so it is ready while the job runs.
  B = await tenantCtx("B", { width: 390, height: 844 });
  A = await tenantCtx("A", { width: 1440, height: 900 });
  const pa = A.p, pb = B.p;
  let rewritePosts = 0;
  for (const p of [pa, pb]) await p.route("**/api/tenant/v1/tours/pool/*/rewrite", (route) => {
    if (route.request().method() !== "POST") return route.continue();
    if (++rewritePosts > 1) { log.blocked_second_rewrite = true; return route.abort(); }
    return route.continue();
  });

  // ── A: My Catalog (table at 1440) → finished version → Request Rewrite ──
  await pa.goto(`${BASE}/portal/t4-pool`, { waitUntil: "networkidle" }); await pa.waitForTimeout(2500);
  log.A.list_mode = await pa.locator("table").count() ? "table" : "cards";
  await shot(pa, "r01-my-catalog-table-1440");
  log.A.row_before = (await row(pa).innerText()).replace(/\s+/g, " ").slice(0, 200);
  await row(pa).getByRole("button", { name: /Open/ }).click();
  await pa.getByRole("button", { name: "Request Rewrite" }).waitFor({ timeout: 20000 });
  await pa.waitForTimeout(1500);
  log.A.source_drawer = (await pa.getByRole("dialog").last().innerText()).replace(/\s+/g, " ").slice(0, 300);
  await shot(pa, "r02-finished-version-drawer-1440");
  const [resp] = await Promise.all([
    pa.waitForResponse((r) => /\/tours\/pool\/[^/]+\/rewrite$/.test(r.url()) && r.request().method() === "POST", { timeout: 30000 }),
    pa.getByRole("button", { name: "Request Rewrite" }).click(),
  ]);
  const rw = await resp.json().catch(() => null);
  log.rewrite_post = { status: resp.status(), path: resp.url().replace(BASE, ""), body: rw, at: new Date().toISOString() };
  VID = rw?.version_id; log.version_id = VID; log.job_id = rw?.job_id ?? null;
  ev(`A: POST rewrite ${resp.status()} version=${VID} v${rw?.version_number} job=${rw?.job_id}`);
  save();
  if (!VID) throw new Error("no version_id");

  // script poller ~0.5 s
  const pollerRun = (async () => {
    const t0 = Date.now(); let doneAt = null;
    while (!poll.stop && Date.now() - t0 < 25 * 60000) {
      let rec;
      try { const r = await A.ctx.request.get(`${BASE}/api/tenant/v1/progress/tour/${VID}`, { headers: { "cache-control": "no-store" } }); rec = { t: new Date().toISOString(), status: r.status(), body: await r.text() }; }
      catch (e) { rec = { t: new Date().toISOString(), status: -1, body: String(e).slice(0, 200) }; }
      poll.polls.push(rec);
      let st = null; try { st = JSON.parse(rec.body).status; } catch {}
      if ((st === "done" || st === "failed") && doneAt === null) doneAt = poll.polls.length;
      if (doneAt !== null && poll.polls.length >= doneAt + 3) break;
      await sleep(500);
    }
  })();
  const lastFound = () => { for (const x of [...poll.polls].reverse()) { try { const j = JSON.parse(x.body); if (j.found) return j; } catch {} } return null; };

  await pa.getByTestId("writer-panel").waitFor({ timeout: 20000 });
  await pa.waitForTimeout(1500);
  log.A.panel_header = { title: await pa.getByTestId("writer-panel-title").innerText(), context: await pa.getByTestId("writer-panel-context").innerText() };
  log.A.dialogs_after_request = await pa.getByRole("dialog").count();
  log.A.layout_start_1440 = await layout(pa);
  await shot(pa, "r03-panel-started-1440");

  // wait for a good amount of live text, then close mid-write
  { const t0 = Date.now(); while (Date.now() - t0 < 300000) { const j = lastFound(); if (j && (j.status !== "running" || secText(j).length > 1200)) break; await sleep(400); } }
  await pa.waitForTimeout(1200);
  log.A.progress_before_close = progSummary(lastFound());
  log.A.layout_writing_1440 = await layout(pa);
  await shot(pa, "r04-panel-live-writing-1440");
  if (log.A.progress_before_close.status !== "running") throw new Error("job finished before the mid-write close: " + JSON.stringify(log.A.progress_before_close));
  await pa.getByRole("button", { name: "Close" }).first().click();
  await pa.getByTestId("writer-panel").waitFor({ state: "detached", timeout: 5000 });
  const lastPage = (pagePolls[VID] ?? []).filter((x) => x.ctx === "A").map((x) => { try { return JSON.parse(x.body); } catch { return null; } }).filter((j) => j?.found).pop();
  const remembered = secText(lastPage);
  log.A.closed_mid_write = { at: new Date().toISOString(), remembered_chars: remembered.length, remembered_revision: lastPage?.revision };
  await pa.waitForTimeout(1500);
  log.A.row_after_close = (await row(pa).innerText()).replace(/\s+/g, " ").slice(0, 200);
  await shot(pa, "r05-closed-mid-write-row-1440");
  ev(`A: closed mid-write; row="${log.A.row_after_close}" remembered=${remembered.length} chars`);

  // ── A: "View progress" with the panel's progress answers HELD 3 s ──
  let held = 0;
  const holder = async (route) => { held++; await sleep(3000); try { await route.continue(); } catch {} };
  await pa.route("**/api/tenant/v1/progress/tour/**", holder);
  const tClick = Date.now();
  await row(pa).getByRole("button", { name: /View progress/ }).click();
  await pa.getByTestId("writer-panel").waitFor({ timeout: 5000 });
  const tPanel = Date.now() - tClick;
  const snippet = remembered.replace(/\s+/g, " ").trim().slice(0, 50);
  const tail = remembered.replace(/\s+/g, " ").trim().slice(-40);
  let firstTextMs = null, startingSeen = 0, samples = [];
  for (let i = 0; i < 25; i++) { // ~2.5 s, all inside the 3 s hold of the first progress answer
    const txt = (await pa.getByTestId("writer-panel").innerText()).replace(/\s+/g, " ");
    const st = await pa.getByTestId("writer-panel").getByText(/Starting…|Starting\.\.\./).count();
    startingSeen += st;
    const has = snippet && txt.includes(snippet);
    samples.push({ ms: Date.now() - tClick, chars: txt.length, has_snippet: has, starting: st });
    if (has && firstTextMs === null) { firstTextMs = Date.now() - tClick; await shot(pa, "r06-view-progress-reopened-held-1440"); }
    await sleep(100);
  }
  const reopenTxt = (await pa.getByTestId("writer-panel").innerText()).replace(/\s+/g, " ");
  log.A.reopen = { panel_ms: tPanel, first_text_ms: firstTextMs, progress_requests_held_so_far: held, starting_seen: startingSeen,
    remembered_snippet: snippet, remembered_tail_shown: tail ? reopenTxt.includes(tail) : null, text_shown_at_once: firstTextMs !== null, samples: samples.filter((_, i) => i % 3 === 0) };
  if (firstTextMs === null) await shot(pa, "r06-view-progress-reopened-held-1440");
  ev(`A: reopen ${JSON.stringify({ ...log.A.reopen, samples: undefined })}`);
  await sleep(1000);
  await pa.unroute("**/api/tenant/v1/progress/tour/**", holder);
  save();

  // ── B (390, cards): View progress → panel at 390 → close mid-write → wait for the toast ──
  const bFlow = (async () => {
    await pb.goto(`${BASE}/portal/t4-pool`, { waitUntil: "networkidle" }); await pb.waitForTimeout(2500);
    log.B.list_mode = await pb.locator("table").count() ? "table" : "cards";
    log.B.card_text = (await row(pb).innerText()).replace(/\s+/g, " ").slice(0, 200);
    log.B.layout_list_390 = await layout(pb);
    await shot(pb, "r07-my-catalog-cards-writing-390");
    await row(pb).getByRole("button", { name: /View progress/ }).click();
    await pb.getByTestId("writer-panel").waitFor({ timeout: 15000 });
    await pb.waitForTimeout(2500);
    log.B.layout_writing_390 = await layout(pb);
    log.B.panel_header = { title: await pb.getByTestId("writer-panel-title").innerText(), context: await pb.getByTestId("writer-panel-context").innerText() };
    log.B.progress_at_view = progSummary(lastFound());
    await shot(pb, "r08-panel-writing-390");
    if (log.B.progress_at_view.status !== "running") ev("B: WARNING job no longer running when B closed — toast path may differ");
    await pb.getByRole("button", { name: "Close" }).first().click();
    log.B.closed_at = new Date().toISOString();
    ev(`B: panel at 390 ${JSON.stringify(log.B.layout_writing_390)}; closed mid-write, waiting for toast`);
    const loc = pb.getByText(/is ready — find it in My Catalog Tours|didn.t finish — open it in My Catalog Tours|is still being written — it will show up in My Catalog Tours/);
    const deadline = Date.now() + 25 * 60000; log.B.toasts = [];
    while (Date.now() < deadline) {
      await loc.first().waitFor({ timeout: Math.max(1000, deadline - Date.now()) });
      const t = await loc.first().innerText();
      if (!log.B.toasts.includes(t)) { log.B.toasts.push(t); ev(`B: toast "${t}"`); }
      if (/is ready|didn.t finish/.test(t)) { log.B.toast = { text: t, at: new Date().toISOString() }; await shot(pb, "r10-toast-ready-390"); break; }
      await pb.waitForTimeout(2000);
    }
    await pb.waitForTimeout(6000);
    log.B.card_after_toast = (await row(pb).innerText()).replace(/\s+/g, " ").slice(0, 200);
    await shot(pb, "r10b-cards-after-ready-390");
  })().catch(async (e) => { log.B.error = String(e).slice(0, 300); ev("B ERROR " + log.B.error); await shot(pb, "r99-B-error-390").catch(() => {}); });

  // ── A: keep the panel open to the end ──
  const aFlow = (async () => {
    await pa.waitForTimeout(2000);
    await shot(pa, "r06b-panel-writing-after-hold-1440");
    const r = pa.getByTestId("tour-rewrite-ready").or(pa.getByTestId("tour-rewrite-failed"));
    await r.first().waitFor({ timeout: 25 * 60000 });
    log.A.final_state = (await pa.getByTestId("tour-rewrite-ready").count()) ? "ready" : "failed";
    log.A.final_at = new Date().toISOString();
    await pa.waitForTimeout(2500);
    log.A.layout_ready_1440 = await layout(pa);
    const dlg = pa.getByRole("dialog").last();
    log.A.ready_buttons = (await dlg.getByRole("button").allInnerTexts()).map((t) => t.trim()).filter(Boolean);
    log.A.ready_text_head = (await dlg.innerText()).slice(0, 500);
    log.A.toast_while_open = await pa.getByText(/is ready — find it in My Catalog Tours/).count();
    await shot(pa, "r09-panel-ready-1440");
    await pa.setViewportSize({ width: 390, height: 844 }); await pa.waitForTimeout(1500);
    log.A.layout_ready_390 = await layout(pa);
    await shot(pa, "r09b-panel-ready-390");
    await pa.setViewportSize({ width: 1440, height: 900 }); await pa.waitForTimeout(1500);
    ev(`A: ${log.A.final_state}; buttons=${JSON.stringify(log.A.ready_buttons)}`);
    if (log.A.final_state === "ready") {
      await pa.getByRole("button", { name: /Open in My Catalog/ }).click();
      await pa.getByRole("button", { name: "Request Rewrite" }).waitFor({ timeout: 20000 });
      await pa.waitForTimeout(2500);
      const d = (await pa.getByRole("dialog").last().innerText()).replace(/\s+/g, " ");
      log.A.opened_in_catalog = { dialogs: await pa.getByRole("dialog").count(), writer_panel_open: await pa.getByTestId("writer-panel").count(), text: d.slice(0, 400) };
      await shot(pa, "r11-open-in-my-catalog-new-version-1440");
    }
  })().catch(async (e) => { log.A.flow_error = String(e).slice(0, 300); ev("A ERROR " + log.A.flow_error); await shot(pa, "r99-A-error-1440").catch(() => {}); });

  await Promise.all([aFlow, bFlow]);
  await pollerRun;

  // ── Evidence: every progress response, final text vs saved version ──
  writeFileSync(`${LOGS}/rewrite-progress-polls.json`, JSON.stringify({ version_id: VID, poller: poll.polls, panel: pagePolls[VID] ?? [] }, null, 1));
  log.progress_poller = analysePolls(poll.polls, "script poller ~0.5 s");
  log.progress_panel_A = analysePolls((pagePolls[VID] ?? []).filter((x) => x.ctx === "A"), "panel polls (A)");
  log.progress_panel_B = analysePolls((pagePolls[VID] ?? []).filter((x) => x.ctx === "B"), "panel polls (B)");
  const vr = await A.ctx.request.get(`${BASE}/api/tenant/v1/tours/versions/${VID}`); const vj = await vr.json().catch(() => null);
  let rc = vj?.rewritten_content; if (typeof rc === "string") { try { rc = JSON.parse(rc); } catch {} }
  const finalJ = lastFound();
  const exp = expectedSections(rc);
  const got = (finalJ?.sections ?? []).map((s) => ({ key: s.key, text: s.text }));
  const per = exp.map((e) => { const g = got.find((x) => x.key === e.key); const a = g?.text ?? null; let i = 0; if (a != null) while (i < a.length && i < e.text.length && a[i] === e.text[i]) i++;
    return { key: e.key, expected_chars: e.text.length, progress_chars: a?.length ?? null, equal: a === e.text, first_diff: a === e.text ? null : { i, progress: a?.slice(i, i + 80), saved: e.text.slice(i, i + 80) } }; });
  log.final_compare = {
    version_status: vr.status(), version_number: vj?.version_number, version_state: vj?.status, job_status: vj?.job_status, edit_source: vj?.edit_source,
    rewritten_keys: rc && typeof rc === "object" ? Object.keys(rc) : null,
    progress_status: finalJ?.status, progress_revision: finalJ?.revision, steps: (finalJ?.steps ?? []).map((s) => `${s.key}:${s.state}`),
    expected_keys: exp.map((e) => e.key), progress_keys: got.map((g) => g.key), extra_progress_keys: got.filter((g) => !exp.find((e) => e.key === g.key)).map((g) => g.key),
    all_equal: per.length > 0 && per.every((x) => x.equal) && got.length === exp.length, per_section: per,
  };
  writeFileSync(`${LOGS}/rewrite-version-and-final-progress.json`, JSON.stringify({ version: vj, final_progress: finalJ, expected_sections: exp }, null, 1));
  const myv = await A.ctx.request.get(`${BASE}/api/tenant/v1/tours/my-versions?page_size=50`); const mj = await myv.json().catch(() => null);
  const mine = (mj?.data ?? []).find((x) => x.id === VID);
  log.after = { my_versions_status: myv.status(), row: mine ? { id: mine.id, version_number: mine.version_number, status: mine.status, job_status: mine.job_status } : null,
    quota: await A.ctx.request.get(`${BASE}/api/tenant/v1/quota`).then((r) => r.json()).catch(() => null) };
  log.rewrite_posts = rewritePosts;
  ev(`final compare all_equal=${log.final_compare.all_equal} poller=${JSON.stringify(log.progress_poller)}`);
} catch (e) {
  log.error = String(e).slice(0, 600); ev("ERROR " + log.error);
  if (A) await shot(A.p, "r99-error-1440").catch(() => {});
} finally {
  poll.stop = true;
  log.finished = new Date().toISOString(); save();
  if (A) await A.ctx.close(); if (B) await B.ctx.close(); await b.close();
}
