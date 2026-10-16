// S239 AA-802 (a) live verify on CIS Dev: "already exported -> admin sees the tenant has an older copy".
// Approved by Nghiệp (S239): Dev writes on a test tenant. Flow: tenant terra-family exports ONE piece (portal My Content
// drawer, Export) -> admin e2e-claude-code applies ONE Edit (manual, no LLM) on its flagged sentence -> admin drawer must show
// "The tenant has an older copy" -> tenant view after (repaired text, no flags / notice keys). Secrets read in-process, never printed.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync, mkdirSync, readFileSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const OUT = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-16-S239-in-progress-audit/aa802-verify/rest";
const VID = `${OUT}/video`; mkdirSync(VID, { recursive: true });
const SLUG = "terra-family";
const PIECE = "c54260a5-e154-4f10-b850-fc40676402b7";
const REQ = "9e957fac-596a-4238-8b89-4aa775dab78f";
const TARGET = "Pawangka Monastery, built in the seventh century by Tibetan King Songtsen Gampo, holds weight that children sense before they can name it.";
const NEWTEXT = "Pawangka Monastery holds weight that children sense before they can name it.";
const STEP = process.argv[2] || "all"; // export | apply | after | all
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const BAD = /gate|score|held|flag|repair|ledger|violation|quality|blocking|problem|older|tenant_copy|exported|admin_edit|audit/i;
const OKKEY = new Set(["angle_gate_request_id"]);
const keyWalk = (o, path = "$", hits = []) => {
  if (Array.isArray(o)) o.forEach((v, i) => keyWalk(v, `${path}[${i}]`, hits));
  else if (o && typeof o === "object") for (const [k, v] of Object.entries(o)) { if (BAD.test(k) && !OKKEY.has(k)) hits.push(`${path}.${k}`); keyWalk(v, `${path}.${k}`, hits); }
  return hits;
};
const b = await chromium.launch();
const log = { step: STEP, tenant: SLUG, piece: PIECE, request: REQ };
const shot = (p, name, full = false) => p.screenshot({ path: `${OUT}/${name}.png`, fullPage: full });
const newCtx = () => b.newContext({ viewport: { width: 1440, height: 900 }, acceptDownloads: true, recordVideo: { dir: VID, size: { width: 1440, height: 900 } } });

async function tenantLogin(ctx) {
  const p = await ctx.newPage();
  await p.goto(`${BASE}/tenant-login`); await p.fill('input[type="password"]', sec(`aa-cis/dev/e2e-tenant/${SLUG}`));
  await Promise.all([p.waitForURL(/\/portal/, { timeout: 30000 }), p.click('button:has-text("Access Portal")')]);
  return p;
}
const tenantApi = (p) => p.evaluate(async ({ PIECE, REQ }) => {
  const g = async (u) => { const r = await fetch(u); let j = null; try { j = await r.json(); } catch {} return { status: r.status, j }; };
  return { piece: await g(`/api/tenant/v1/content-writing/pieces/${PIECE}`), latest: await g(`/api/tenant/v1/content-writing/requests/${REQ}/latest-piece`),
    reviews: await g(`/api/tenant/v1/content-writing/reviews`), pending: await g(`/api/tenant/v1/publish-log/pending`) };
}, { PIECE, REQ });
const sumTenant = (api) => {
  const T = {}; for (const [k, v] of Object.entries(api)) T[k] = { status: v.status, forbidden_keys: keyWalk(v.j) };
  const rv = (api.reviews.j?.data ?? []).find((x) => x.piece_id === PIECE);
  const pt = api.piece.j?.content_text ?? "";
  T.summary = { piece_len: pt.length, piece_has_old: pt.includes(TARGET), piece_has_new: pt.includes(NEWTEXT),
    my_content_has_piece: !!rv, my_content_len: rv?.content_text?.length ?? null, my_content_has_old: rv?.content_text?.includes(TARGET) ?? null,
    latest_piece_id: api.latest.j?.piece?.piece_id ?? null, latest_has_old: (api.latest.j?.piece?.content_text ?? "").includes(TARGET),
    piece_top_keys: Object.keys(api.piece.j ?? {}) };
  return { T, text: rv?.content_text ?? pt };
};
async function drawerScan(p, tag) {
  await p.goto(`${BASE}/portal/t10-review?piece=${PIECE}`, { waitUntil: "networkidle" }); await p.waitForTimeout(3000);
  const dlg = p.getByRole("dialog").last();
  const t = (await dlg.innerText().catch(() => "")) || "";
  await shot(p, `tenant-${tag}-1440-my-content-drawer`);
  return { drawer_open: (await dlg.count()) > 0, has_old: t.includes(TARGET), has_new: t.includes(NEWTEXT),
    bad_words: [...t.matchAll(/\b(held|flag(ged|s)?|gate|F\d{1,2}_\w+|blocked|quality score|needs review|older (copy|version)|updated version|admin)\b/gi)].map((m) => t.slice(Math.max(0, m.index - 40), m.index + 40)) };
}

async function tenantExport() {
  const ctx = await newCtx(); const p = await tenantLogin(ctx);
  const errs = []; p.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });
  const s0 = sumTenant(await tenantApi(p)); log.tenant_before = s0.T; writeFileSync(`${OUT}/tenant-before-content_text.txt`, s0.text ?? "");
  log.tenant_before.ui = await drawerScan(p, "before");
  const dlg = p.getByRole("dialog").last();
  const btn = dlg.getByRole("button", { name: "Export", exact: true });
  log.export_button_found = (await btn.count()) > 0;
  const respP = p.waitForResponse((r) => r.url().includes(`/pieces/${PIECE}/export`), { timeout: 30000 }); respP.catch(() => {});
  const dlP = p.waitForEvent("download", { timeout: 30000 }); dlP.catch(() => {});
  await btn.click();
  const resp = await respP; const dl = await dlP;
  const file = `${OUT}/tenant-exported-${dl.suggestedFilename()}`; await dl.saveAs(file);
  const body = readFileSync(file, "utf8");
  log.export = { http: resp.status(), url_qs: resp.url().split("?")[1], content_type: resp.headers()["content-type"], filename: dl.suggestedFilename(), bytes: body.length, file_has_old: body.includes(TARGET), at: new Date().toISOString() };
  await p.waitForTimeout(1500); await shot(p, "tenant-export-1440-after-click");
  log.tenant_export_console_errors = errs;
  await ctx.close();
}

async function adminLogin(ctx) {
  const a = JSON.parse(sec("aa-cis/dev/e2e-test-admin"));
  const ap = await ctx.newPage();
  await ap.goto(`${BASE}/login`, { waitUntil: "load" }); await ap.waitForTimeout(2000);
  await ap.fill('input[placeholder="Username"]', a.username); await ap.fill('input[type="password"]', a.password);
  await ap.locator("button", { hasText: "Login" }).click();
  await ap.waitForURL((u) => !u.toString().includes("/login"), { timeout: 45000 });
  return ap;
}
const adminDetail = (ap) => ap.evaluate(async (id) => { const r = await fetch(`/api/admin/content-quality/pieces/${id}`, { headers: { "x-reviewer-id": localStorage.getItem("cis_reviewer_id") || "" } }); return { status: r.status, j: await r.json().catch(() => null) }; }, PIECE);
const sumAdmin = (d) => ({ http: d.status, piece_status: d.j?.status, published: d.j?.published, exported: d.j?.exported, tenant_copy: d.j?.tenant_copy, admin_edits: d.j?.admin_edits?.length, len: d.j?.content_text?.length, has_old: d.j?.content_text?.includes(TARGET), has_new: d.j?.content_text?.includes(NEWTEXT), flagged: d.j?.flagged_sentences?.length });

async function adminApply() {
  const ctx = await newCtx(); const ap = await adminLogin(ctx);
  const A = (log.admin = {});
  const errs = []; ap.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });
  const d0 = await adminDetail(ap); A.before = sumAdmin(d0);
  writeFileSync(`${OUT}/admin-before-content_text.txt`, d0.j?.content_text ?? "");
  if (!d0.j?.exported || d0.j?.published) { A.aborted = "piece not exported (or published) — stop"; await ctx.close(); return; }
  await ap.goto(`${BASE}/admin/content-quality?tab=pieces&piece=${PIECE}`, { waitUntil: "networkidle" }); await ap.waitForTimeout(3500);
  A.before_ui = { older_copy_notice: await ap.getByTestId("cq-older-copy").count() };
  await shot(ap, "admin-before-1440-piece-drawer");
  const row = ap.getByTestId("cq-flag-row").filter({ hasText: "Songtsen Gampo" }).first();
  A.row_found = (await row.count()) > 0;
  if (!A.row_found) { A.aborted = "flag row not found"; await ctx.close(); return; }
  await row.scrollIntoViewIfNeeded(); await ap.waitForTimeout(400);
  const exportedNote = ap.getByText(/The tenant already exported this piece/).first();
  A.before_ui.already_exported_note = await exportedNote.innerText().catch(() => null);
  await shot(ap, "admin-before-1440-flagged-sentence-exported-note");
  await row.getByRole("button", { name: "Edit", exact: true }).click(); await ap.waitForTimeout(500);
  const ta = row.locator("textarea").first();
  A.draft_prefilled_matches = (await ta.inputValue()) === TARGET;
  await ta.fill(NEWTEXT); await ap.waitForTimeout(300);
  await shot(ap, "admin-edit-1440-replacement-typed");
  const respP = ap.waitForResponse((r) => r.url().includes(`/content-quality/pieces/${PIECE}/sentences/apply`), { timeout: 60000 }); respP.catch(() => {});
  await row.getByRole("button", { name: "Apply", exact: true }).click();
  const resp = await respP; const body = await resp.json().catch(() => null); const req = JSON.parse(resp.request().postData() || "{}");
  A.apply = { http: resp.status(), method: resp.request().method(), mode: req.mode, gate: req.gate, warnings: body?.warnings ?? null, error_detail: resp.status() >= 400 ? body?.detail : undefined, len_after: body?.content_text?.length, tenant_copy_in_response: body?.tenant_copy, at: new Date().toISOString() };
  await ap.waitForTimeout(2500);
  await shot(ap, "admin-after-1440-toast-drawer");
  const d1 = await adminDetail(ap); A.after = sumAdmin(d1);
  const e = d1.j?.admin_edits?.[0] ?? null;
  A.after.audit_row = e ? { action: e.action, actor: e.actor, created_at: e.created_at, details: { ...e.details, before: e.details?.before, after: e.details?.after } } : null;
  writeFileSync(`${OUT}/admin-after-content_text.txt`, d1.j?.content_text ?? "");
  await ap.reload({ waitUntil: "networkidle" }); await ap.waitForTimeout(3500);
  const notice = ap.getByTestId("cq-older-copy").first();
  A.after_ui = { older_copy_notice_count: await ap.getByTestId("cq-older-copy").count(), notice_text: await notice.innerText().catch(() => null) };
  if (await notice.count()) { await notice.scrollIntoViewIfNeeded(); }
  await shot(ap, "admin-after-1440-older-copy-notice");
  const sec2 = ap.getByText(/Admin edits · \d+/).first();
  A.after_ui.admin_edits_heading = await sec2.innerText().catch(() => null);
  if (await sec2.count()) { await sec2.scrollIntoViewIfNeeded(); await ap.waitForTimeout(400); }
  await shot(ap, "admin-after-1440-admin-edits-audit-row");
  A.console_errors = errs;
  await ctx.close();
}

async function tenantAfter() {
  const ctx = await newCtx(); const p = await tenantLogin(ctx);
  const errs = []; p.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });
  const s1 = sumTenant(await tenantApi(p)); log.tenant_after = s1.T; writeFileSync(`${OUT}/tenant-after-content_text.txt`, s1.text ?? "");
  log.tenant_after.ui = await drawerScan(p, "after");
  log.tenant_after.ui.console_errors = errs;
  await ctx.close();
}

try {
  if (STEP === "all" || STEP === "export") await tenantExport();
  if (STEP === "all" || STEP === "apply") await adminApply();
  if ((STEP === "all" && !log.admin?.aborted) || STEP === "after") await tenantAfter();
} catch (e) { log.error = String(e).slice(0, 600); }
await b.close();
writeFileSync(`${OUT}/run-${STEP}.json`, JSON.stringify(log, null, 1));
console.log(JSON.stringify(log, null, 1));
