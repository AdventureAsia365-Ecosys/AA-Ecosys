// S239 AA-668 RE-VERIFY after CIS #759 (api :631 / worker :188, image dev-2090bb22): Social Content, LinkedIn,
// tenant terra-family. ONE paid T9 write (~$0.03), plus ONE more only if no sentence repair ran in the first.
// Polls GET /api/tenant/v1/progress/piece/{piece} every ~0.5 s (APIRequestContext, same cookies) and records the
// panel's own progress responses; asserts no "replacements" and no section starting with "{"; final text == piece.
// Close mid-write → Continue: the reopened view is checked while its progress requests are HELD for 3 s, so any
// text it shows comes from the remembered snapshot (no "Starting…"). Secrets read in-process, never printed.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const OUT = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-16-S239-in-progress-audit/aa668-verify/rerun";
const LOGS = `${OUT}/logs`;
const SLUG = "terra-family";
const USED = ["Uran Togoo — walk into the volcanic crater", "Punakha Dzong — visit"];
mkdirSync(`${OUT}/video`, { recursive: true }); mkdirSync(LOGS, { recursive: true });
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const log = { started: new Date().toISOString(), tenant: SLUG, console_errors: [], http_errors: [], posts: {}, events: [], runs: [] };
const ev = (m) => { const e = `${new Date().toISOString()} ${m}`; log.events.push(e); console.log(e); };
const save = () => writeFileSync(`${LOGS}/social.json`, JSON.stringify(log, null, 1));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, recordVideo: { dir: `${OUT}/video/social`, size: { width: 1440, height: 900 } } });
const p = await ctx.newPage();
p.on("console", (m) => { if (m.type() === "error") log.console_errors.push(m.text().slice(0, 200)); });
p.on("pageerror", (e) => log.console_errors.push("pageerror: " + String(e).slice(0, 200)));
p.on("response", (r) => { if (r.status() >= 400 && r.url().startsWith(BASE)) log.http_errors.push(`${r.status()} ${r.request().method()} ${r.url().replace(BASE, "").slice(0, 120)}`); });
const tget = async (path) => { const r = await ctx.request.get(BASE + path, { headers: { "cache-control": "no-store" } }); const txt = await r.text(); let j = null; try { j = JSON.parse(txt); } catch {} return { status: r.status(), j, txt }; };
const layout = () => p.evaluate(() => {
  const d = [...document.querySelectorAll('[role="dialog"]')].pop(); const r = d?.getBoundingClientRect();
  return { vw: innerWidth, vh: innerHeight, dialog: r ? { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } : null,
    dialog_fits: r ? r.y >= 0 && r.y + r.height <= innerHeight + 1 && r.x >= 0 && r.x + r.width <= innerWidth + 1 : null,
    page_overflow_x: document.documentElement.scrollWidth - innerWidth, scrollY: scrollY };
});
const shot = (n) => p.screenshot({ path: `${OUT}/${n}.png` });
const MAX = { pick: 2, goal: 2, write: 2 };
const guard = (pattern, key) => p.route(pattern, (route) => {
  if (route.request().method() !== "POST") return route.continue();
  log.posts[key] = (log.posts[key] ?? 0) + 1;
  if (log.posts[key] > MAX[key]) { log.posts[`${key}_blocked`] = true; return route.abort(); }
  return route.continue();
});
const stripTags = (t) => t.replace(/\s?\[(?:R|F):[^\]\n]{0,120}\]/g, "");

// Page's own progress responses (the panel's polls), per piece.
const pagePolls = {};
p.on("response", async (r) => {
  const m = r.url().match(/\/api\/tenant\/v1\/progress\/piece\/([^/?]+)/);
  if (!m) return;
  try { (pagePolls[m[1]] ??= []).push({ t: new Date().toISOString(), status: r.status(), body: await r.text() }); } catch {}
});

function startPoller(piece) {
  const polls = []; let stop = false; let doneAt = null;
  const run = (async () => {
    const t0 = Date.now();
    while (!stop && Date.now() - t0 < 600000) {
      const r = await tget(`/api/tenant/v1/progress/piece/${piece}`).catch((e) => ({ status: -1, txt: String(e) }));
      polls.push({ t: new Date().toISOString(), status: r.status, body: r.txt });
      const st = r.j?.status;
      if ((st === "done" || st === "failed") && doneAt === null) doneAt = polls.length;
      if (doneAt !== null && polls.length >= doneAt + 2) break;
      await sleep(500);
    }
  })();
  return { polls, finish: async () => { await run; }, stop: () => { stop = true; } };
}
const bodyText = (j) => (j?.sections ?? []).map((s) => s.text ?? "").join("\n\n");
function analysePolls(polls, label) {
  let withReplacements = 0, sectionStartsBrace = 0, statuses = {}, maxChars = 0, revisions = new Set();
  const bad = [];
  for (const x of polls) {
    if (/replacements/.test(x.body)) { withReplacements++; bad.push({ t: x.t, why: "replacements" }); }
    let j = null; try { j = JSON.parse(x.body); } catch {}
    if (!j) continue;
    statuses[j.status ?? (j.found === false ? "not_found" : "?")] = (statuses[j.status ?? (j.found === false ? "not_found" : "?")] ?? 0) + 1;
    if (j.revision != null) revisions.add(j.revision);
    for (const s of j.sections ?? []) if ((s.text ?? "").trimStart().startsWith("{")) { sectionStartsBrace++; bad.push({ t: x.t, why: "section starts with {", key: s.key }); }
    maxChars = Math.max(maxChars, bodyText(j).length);
  }
  return { label, responses: polls.length, statuses, revisions: [...revisions], max_chars: maxChars, with_replacements: withReplacements, section_starts_with_brace: sectionStartsBrace, bad: bad.slice(0, 10) };
}

async function openLinkedInSlate() {
  await p.goto(`${BASE}/portal/t7-planning`, { waitUntil: "networkidle" }); await p.waitForTimeout(2500);
  await p.getByRole("button", { name: /^LinkedIn/ }).click();
  await p.getByRole("button", { name: /Pick to write/ }).first().waitFor({ timeout: 30000 });
  await p.waitForTimeout(1000);
}

async function oneWrite(n, { closeReopen }) {
  const R = { n, close_reopen: closeReopen };
  log.runs.push(R);
  await openLinkedInSlate();
  if (n === 1) await shot("s01-slate-linkedin-1440");
  // first proposed subject not used before
  const btns = p.getByRole("button", { name: /Pick to write/ });
  const count = await btns.count(); let idx = -1, title = null;
  for (let i = 0; i < count; i++) {
    const t = (await btns.nth(i).locator("xpath=ancestor::div[3]").innerText()).split("\n").map((s) => s.trim()).filter(Boolean)[0];
    if (!USED.includes(t)) { idx = i; title = t; break; }
  }
  if (idx < 0) throw new Error("no unused proposed LinkedIn subject");
  R.subject_card_title = title;
  const [pickR] = await Promise.all([
    p.waitForResponse((r) => /\/subjects\/[^/]+\/pick/.test(r.url()) && r.request().method() === "POST", { timeout: 30000 }),
    btns.nth(idx).click(),
  ]);
  const pick = await pickR.json().catch(() => null);
  R.pick = { status: pickR.status(), subject_id: pick?.subject_id, request_id: pick?.request_id, channel: pick?.channel };
  USED.push(title);
  ev(`run${n}: pick ${pickR.status()} subject="${title}" request=${pick?.request_id}`);
  await p.getByTestId("writer-panel").waitFor({ timeout: 20000 });
  await p.locator('[data-testid^="goal-"]').first().waitFor({ timeout: 20000 });
  R.panel_header = { title: await p.getByTestId("writer-panel-title").innerText(), context: await p.getByTestId("writer-panel-context").innerText() };
  await p.locator('[data-testid^="goal-"]', { hasText: "Introduction / Awareness" }).first().click();
  const [goalR] = await Promise.all([
    p.waitForResponse((r) => r.url().includes("/goal") && r.request().method() === "POST", { timeout: 30000 }),
    p.getByRole("button", { name: /Generate 3 angles/ }).click(),
  ]);
  R.goal_post = goalR.status();
  await p.getByTestId("angle-0").waitFor({ timeout: 300000 });
  await p.waitForTimeout(1200);
  if (n === 1) await shot("s02-panel-angles-1440");
  const [writeR] = await Promise.all([
    p.waitForResponse((r) => /\/content-writing\/requests\/[^/]+\/write$/.test(r.url()) && r.request().method() === "POST", { timeout: 60000 }),
    p.getByTestId("angle-0").getByRole("button", { name: /Write with this angle/ }).click(),
  ]);
  const wj = await writeR.json().catch(() => null);
  const PIECE = wj?.piece_id; R.write_post = { status: writeR.status(), piece_id: PIECE, ready_state: wj?.ready_state };
  ev(`run${n}: write ${writeR.status()} piece=${PIECE}`);
  save();
  if (!PIECE) throw new Error("no piece_id");
  const poller = startPoller(PIECE);

  // Write card label
  await p.waitForTimeout(1500);
  const ptxt = await p.getByTestId("writer-panel").innerText();
  const m = ptxt.match(/Angle:[^\n]*?Goal:\s*([^\n·]+?)\s*·\s*Channel:\s*([^\n·]+)/);
  R.write_card = m ? { line: m[0].replace(/\s+/g, " ").trim(), goal: m[1].trim(), channel: m[2].trim() } : { line: null, panel_head: ptxt.slice(0, 400) };
  R.write_card_ok = !!m && m[1].trim() === "Introduction / Awareness" && m[2].trim() === "LinkedIn";
  ev(`run${n}: write card ${JSON.stringify(R.write_card)}`);

  if (closeReopen) {
    // wait for some live text, then close mid-write
    const t0 = Date.now(); let lastBody = "";
    while (Date.now() - t0 < 120000) {
      const last = [...poller.polls].reverse().find((x) => { try { return JSON.parse(x.body).found; } catch { return false; } });
      const j = last ? JSON.parse(last.body) : null;
      if (j && j.status !== "running") break;
      if (j && bodyText(j).length > 120) { lastBody = bodyText(j); break; }
      await sleep(250);
    }
    await p.waitForTimeout(900); // let the panel's own poll (0.8 s) catch up
    const panelBefore = await p.getByTestId("writer-panel").innerText();
    R.before_close = { panel_chars: panelBefore.length, poll_body_chars: lastBody.length };
    await shot("s03-panel-streaming-before-close-1440");
    await p.getByRole("button", { name: "Close" }).first().click();
    await p.getByTestId("writer-panel").waitFor({ state: "detached", timeout: 5000 });
    R.closed_at = new Date().toISOString();
    const lastPage = (pagePolls[PIECE] ?? []).filter((x) => { try { return JSON.parse(x.body).found; } catch { return false; } }).pop();
    const remembered = lastPage ? bodyText(JSON.parse(lastPage.body)) : "";
    R.remembered_chars = remembered.length;
    await p.waitForTimeout(1200);
    await shot("s04-closed-mid-write-continue-1440");
    // HOLD the reopened view's progress answers for 3 s
    let held = 0;
    const holder = async (route) => { held++; await sleep(3000); try { await route.continue(); } catch {} };
    await p.route("**/api/tenant/v1/progress/piece/**", holder);
    const tClick = Date.now();
    await p.getByRole("button", { name: /Continue/ }).first().click();
    await p.getByTestId("writer-panel").waitFor({ timeout: 5000 });
    await p.waitForTimeout(500);
    const snippet = remembered.slice(0, 60);
    const reopenText = await p.getByTestId("writer-panel").innerText();
    R.reopen = {
      ms_after_click: Date.now() - tClick, progress_requests_held: held,
      starting_count: await p.getByTestId("writer-panel").getByText("Starting…").count(),
      remembered_snippet: snippet,
      text_shown_at_once: snippet.length > 0 && reopenText.replace(/\s+/g, " ").includes(snippet.replace(/\s+/g, " ")),
      panel_chars: reopenText.length,
      // goal/angle screen must not come back: the wizard should resume the write
      shows_goal_cards: await p.locator('[data-testid^="goal-"]').count(),
    };
    await shot("s05-reopened-via-continue-held-1440");
    ev(`run${n}: reopen ${JSON.stringify(R.reopen)}`);
    await p.unroute("**/api/tenant/v1/progress/piece/**", holder);
  }

  await p.getByTestId("writer-panel-result").waitFor({ timeout: 600000 });
  await p.waitForTimeout(2000);
  await poller.finish();
  R.layout_result_1440 = await layout();
  R.result_actions = await p.getByRole("dialog").last().getByRole("button").allInnerTexts().then((a) => a.map((t) => t.trim()).filter(Boolean));
  await shot(`s0${n === 1 ? 6 : 8}-panel-piece-saved-1440${n === 1 ? "" : "-run2"}`);
  await p.setViewportSize({ width: 390, height: 844 }); await p.waitForTimeout(1200);
  R.layout_result_390 = await layout();
  await shot(`s0${n === 1 ? 7 : 9}-panel-piece-saved-390${n === 1 ? "" : "-run2"}`);
  await p.setViewportSize({ width: 1440, height: 900 }); await p.waitForTimeout(1000);

  // Assertions over every progress response (own poller + the panel's own polls)
  writeFileSync(`${LOGS}/social-run${n}-progress-polls.json`, JSON.stringify({ piece_id: PIECE, poller: poller.polls, panel: pagePolls[PIECE] ?? [] }, null, 1));
  R.progress_poller = analysePolls(poller.polls, "script poller ~0.5 s");
  R.progress_panel = analysePolls(pagePolls[PIECE] ?? [], "panel's own polls");
  const piece = await tget(`/api/tenant/v1/content-writing/pieces/${PIECE}`);
  const content = piece.j?.content_text ?? "";
  const finalJ = (() => { for (const x of [...poller.polls].reverse()) { try { const j = JSON.parse(x.body); if (j.found) return j; } catch {} } return null; })();
  const finalText = bodyText(finalJ);
  const expect = stripTags(content).trimEnd();
  R.final = {
    progress_status: finalJ?.status, revision: finalJ?.revision, steps: (finalJ?.steps ?? []).map((s) => `${s.key}:${s.state}`),
    section_keys: (finalJ?.sections ?? []).map((s) => s.key), final_chars: finalText.length,
    piece_status: piece.status, ready_state: piece.j?.ready_state, channel: piece.j?.channel, content_chars: content.length,
    equal_exact: finalText === content, equal_after_tagstrip_rstrip: finalText === expect,
    first_diff_at: (() => { const a = finalText, c = expect; let i = 0; while (i < a.length && i < c.length && a[i] === c[i]) i++; return i === a.length && i === c.length ? null : { i, progress: a.slice(i, i + 80), piece: c.slice(i, i + 80) }; })(),
  };
  R.piece_id = PIECE;
  writeFileSync(`${LOGS}/social-run${n}-piece.json`, JSON.stringify({ piece: piece.j, final_progress: finalJ }, null, 1));
  ev(`run${n}: final ${JSON.stringify(R.final)} poller=${JSON.stringify(R.progress_poller)}`);
  save();
  await p.getByRole("button", { name: "Close" }).first().click().catch(() => {});
  await p.waitForTimeout(1000);
  return PIECE;
}

async function repairLog(piece) {
  const actx = await b.newContext({ viewport: { width: 1440, height: 900 } }); const ap = await actx.newPage();
  try {
    const a = JSON.parse(sec("aa-cis/dev/e2e-test-admin"));
    await ap.goto(`${BASE}/login`, { waitUntil: "load" }); await ap.waitForTimeout(2000);
    await ap.fill('input[placeholder="Username"]', a.username); await ap.fill('input[type="password"]', a.password);
    await ap.locator("button", { hasText: "Login" }).click();
    await ap.waitForURL((u) => !u.toString().includes("/login"), { timeout: 45000 });
    const r = await ap.evaluate(async (path) => { const h = {}; const rid = localStorage.getItem("cis_reviewer_id"); if (rid) h["x-reviewer-id"] = rid; const r = await fetch(path, { headers: h }); let j = null; try { j = await r.json(); } catch {} return { status: r.status, j }; }, `/api/admin/content-quality/pieces/${piece}`);
    const d = r.j?.piece ?? r.j;
    const rl = d?.repair_log ?? [];
    return { status: r.status, piece_status: d?.status, attempt_number: d?.attempt_number, repair_log: rl.map((x) => ({ attempt: x.attempt, repair_mode: x.repair_mode, sentences_repaired: x.sentences_repaired, failed: x.failed_gates ?? x.failures ?? undefined })),
      sentence_repair_ran: rl.some((x) => /sentences/.test(x.repair_mode ?? "")), keys: d ? Object.keys(d) : null };
  } finally { await actx.close(); }
}

try {
  await p.goto(`${BASE}/tenant-login`); await p.fill('input[type="password"]', sec(`aa-cis/dev/e2e-tenant/${SLUG}`));
  await Promise.all([p.waitForURL(/\/portal/, { timeout: 30000 }), p.click('button:has-text("Access Portal")')]);
  await guard("**/api/tenant/v1/subjects/*/pick", "pick");
  await guard("**/api/tenant/v1/angle-gate/requests/*/goal", "goal");
  await guard("**/api/tenant/v1/content-writing/requests/*/write", "write");
  const p1 = await oneWrite(1, { closeReopen: true });
  log.runs[0].repair = await repairLog(p1);
  ev(`run1 repair: ${JSON.stringify(log.runs[0].repair)}`);
  save();
  if (!log.runs[0].repair.sentence_repair_ran) {
    ev("run1: no sentence repair ran → ONE more write on another subject");
    const p2 = await oneWrite(2, { closeReopen: false });
    log.runs[1].repair = await repairLog(p2);
    ev(`run2 repair: ${JSON.stringify(log.runs[1].repair)}`);
  }
} catch (e) {
  log.error = String(e).slice(0, 600); ev("ERROR " + log.error);
  await shot("s99-error-1440").catch(() => {});
} finally {
  log.finished = new Date().toISOString(); save(); await ctx.close(); await b.close();
}
