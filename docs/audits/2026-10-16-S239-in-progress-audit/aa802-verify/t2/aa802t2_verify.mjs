// S239 AA-802 live verify, T2 path (silent correction of a tenant tour version) on CIS Dev. Approved by Nghiệp (S239) as a Dev write on a test tenant.
// One admin Edit (mode manual, no LLM) on one flagged sentence of an unexported ai_generated WildKind Travel version. Secrets read in-process, never printed.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync, readFileSync, existsSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const OUT = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-16-S239-in-progress-audit/aa802-verify/t2";
const TMP = "/home/nghiep/projects/AA-Ecosys/.tmp-session/s239";
const SLUG = "wildkind-travel";
const VID = "b0c7a857-e15c-4ffd-832d-fbf01ecfc5fc";
const PTID = "2cf487be-2a9a-4a64-b1d0-1cceaebd9361";
const TARGET = "Dien Bien Phu in the Muong Thanh Valley — site of the 1954 battle that ended French colonial rule in Indochina";
const NEWTEXT = "Dien Bien Phu in the Muong Thanh Valley — site of the battle that ended French colonial rule in Indochina";
// sanitize_replacement turned the typed " — " into ": " (stored text, read back from the apply response)
const STORED = "Dien Bien Phu in the Muong Thanh Valley: site of the battle that ended French colonial rule in Indochina";
const STEP = process.argv[2] || "all";
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const BAD = /gate|score|held|flag|repair|ledger|violation|quality|blocking|problem|qa_|review|escalat|admin/i;
const keyWalk = (o, path = "$", hits = []) => {
  if (Array.isArray(o)) o.forEach((v, i) => keyWalk(v, `${path}[${i}]`, hits));
  else if (o && typeof o === "object") for (const [k, v] of Object.entries(o)) { if (BAD.test(k)) hits.push(`${path}.${k}`); keyWalk(v, `${path}.${k}`, hits); }
  return hits;
};
const valWalk = (o, re, path = "$", hits = []) => {
  if (Array.isArray(o)) o.forEach((v, i) => valWalk(v, re, `${path}[${i}]`, hits));
  else if (o && typeof o === "object") for (const [k, v] of Object.entries(o)) valWalk(v, re, `${path}.${k}`, hits);
  else if (typeof o === "string" && re.test(o)) hits.push(`${path}=${o.slice(0, 40)}`);
  return hits;
};
const parse = (x) => { if (typeof x !== "string") return x; try { return JSON.parse(x); } catch { return x; } };
const b = await chromium.launch();
const log = { step: STEP, version: VID, tenant: SLUG };
const shot = (p, name, full = false) => p.screenshot({ path: `${OUT}/${name}.png`, fullPage: full });

async function tenantView(tag) {
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } }); const p = await ctx.newPage();
  const errs = []; p.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });
  await p.goto(`${BASE}/tenant-login`); await p.fill('input[type="password"]', sec(`aa-cis/dev/e2e-tenant/${SLUG}`));
  await Promise.all([p.waitForURL(/\/portal/, { timeout: 30000 }), p.click('button:has-text("Access Portal")')]);
  const api = await p.evaluate(async ({ VID }) => {
    const g = async (u) => { const r = await fetch(u); let j = null; try { j = await r.json(); } catch {} return { status: r.status, j }; };
    return { list: await g(`/api/tenant/v1/tours/my-versions?page_size=50`), detail: await g(`/api/tenant/v1/tours/versions/${VID}`) };
  }, { VID });
  const T = {};
  for (const [k, v] of Object.entries(api)) T[k] = { status: v.status, forbidden_keys: keyWalk(v.j), forbidden_status_values: valWalk(v.j, /^(needs_review|held|flagged|blocked)$/i) };
  const d = api.detail.j || {}; const rc = parse(d.rewritten_content) || {};
  const li = (api.list.j?.data ?? []).find((x) => x.id === VID); const lrc = parse(li?.rewritten_content) || {};
  const sameTour = (api.list.j?.data ?? []).filter((x) => x.published_tour_id === PTID);
  T.summary = {
    detail_keys: Object.keys(d), status: d.status, version_number: d.version_number, edit_source: d.edit_source, edited_at: d.edited_at,
    history: (d.version_history ?? []).map((h) => `v${h.version_number}:${h.status}:${h.edit_source}`),
    highlights_len: Array.isArray(rc.highlights) ? rc.highlights.length : null, highlight4: Array.isArray(rc.highlights) ? rc.highlights[4] : null,
    detail_has_target: JSON.stringify(rc).includes(TARGET), detail_has_new: Array.isArray(rc.highlights) && rc.highlights.includes(STORED),
    list_total: api.list.j?.pagination?.total, list_has_version: !!li, list_has_target: JSON.stringify(lrc).includes(TARGET), list_has_new: JSON.stringify(lrc).includes(STORED),
    list_versions_same_tour: sameTour.map((x) => `v${x.version_number}:${x.status}:${x.id.slice(0, 8)}`),
  };
  writeFileSync(`${OUT}/tenant-${tag}-rewritten_content.json`, JSON.stringify(rc, null, 1));
  // UI: My Catalog Tours filtered to this tour, open the drawer
  await p.goto(`${BASE}/portal/t4-pool?tour_id=${encodeURIComponent(d.tour_id ?? "")}`, { waitUntil: "networkidle" }); await p.waitForTimeout(2500);
  await shot(p, `tenant-${tag}-1440-my-catalog-list`);
  const open = p.getByRole("button", { name: /Open/ }).first();
  T.ui = { open_buttons: await p.getByRole("button", { name: /Open/ }).count() };
  if (T.ui.open_buttons > 0) {
    await open.click(); await p.waitForTimeout(3500);
    const dlg = p.getByRole("dialog").last();
    const hasDlg = (await dlg.count()) > 0;
    const root = hasDlg ? dlg : p.locator("body");
    const txt = (await root.innerText().catch(() => "")) || "";
    const vals = await root.evaluate((el) => [...el.querySelectorAll("input,textarea")].map((e) => e.value)).catch(() => []);
    const all = txt + "\n" + vals.join("\n");
    T.ui = { ...T.ui, drawer_open: hasDlg, drawer_has_target: all.includes(TARGET), drawer_has_new: all.includes(STORED),
      drawer_has_1954_highlight_prefix: all.includes("site of the 1954 battle that ended French colonial rule in Indochina"),
      drawer_edited_label: /Edited:/.test(txt),
      drawer_bad_words: [...all.matchAll(/\b(held|flag(ged|s)?|gate|F\d{1,2}_\w+|T3_\w+|blocked|quality score|score|needs.review|admin|grounding|corrected|updated version)\b/gi)].map((m) => all.slice(Math.max(0, m.index - 40), m.index + 40)),
      console_errors: errs };
    writeFileSync(`${OUT}/tenant-${tag}-drawer-text.txt`, all);
    await shot(p, `tenant-${tag}-1440-my-catalog-drawer-top`);
    const anchor = "Dien Bien Phu in the Muong Thanh Valley";
    const found = await p.evaluate((a) => {
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) { if (n.textContent.includes(a)) { n.parentElement.scrollIntoView({ block: "center" }); return "text"; } }
      for (const e of document.querySelectorAll("input,textarea")) if (e.value.includes(a)) { e.scrollIntoView({ block: "center" }); return "input"; }
      return null;
    }, anchor);
    T.ui.highlight_anchor_found = found;
    await p.waitForTimeout(600);
    await shot(p, `tenant-${tag}-1440-my-catalog-drawer-highlight`);
  }
  await ctx.close();
  log[`tenant_${tag}`] = T;
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
const adminDetail = (ap) => ap.evaluate(async (id) => { const r = await fetch(`/api/admin/content-quality/tour-versions/${id}`, { headers: { "x-reviewer-id": localStorage.getItem("cis_reviewer_id") || "" } }); return { status: r.status, j: await r.json().catch(() => null) }; }, VID);
const sum = (j) => ({ status: j?.status, version_number: j?.version_number, latest: j?.latest_version_number, edit_source: j?.edit_source, editable: j?.editable, block: j?.edit_block_reason,
  tenant_copy: j?.tenant_copy, admin_edits: j?.admin_edits?.length, flagged: j?.flagged_sentences?.map((f) => `${f.field}:${f.index ?? "-"}:${f.gates.join("+")}`),
  highlight4: j?.rewritten_content?.highlights?.[4], highlights_len: j?.rewritten_content?.highlights?.length });

async function adminApply() {
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } }); const ap = await adminLogin(ctx);
  const A = (log.admin = {});
  const errs = []; ap.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });
  const d0 = await adminDetail(ap); A.before = { http: d0.status, ...sum(d0.j) };
  writeFileSync(`${OUT}/admin-before-rewritten_content.json`, JSON.stringify(d0.j?.rewritten_content, null, 1));
  if (!d0.j?.editable || d0.j?.tenant_copy?.exported_at) { A.aborted = "not editable or exported"; await ctx.close(); return; }
  await ap.goto(`${BASE}/admin/content-quality?tab=versions&version=${VID}`, { waitUntil: "networkidle" }); await ap.waitForTimeout(3500);
  await shot(ap, "admin-before-1440-version-drawer");
  const row = ap.getByTestId("cq-tv-flag-row").filter({ hasText: TARGET }).first();
  A.row_found = (await row.count()) > 0;
  if (!A.row_found) { A.aborted = "flag row not found"; await ctx.close(); return; }
  await row.scrollIntoViewIfNeeded(); await ap.waitForTimeout(400);
  await shot(ap, "admin-before-1440-flagged-sentence");
  A.row_buttons = await row.getByRole("button").allInnerTexts();
  await row.getByRole("button", { name: "Edit", exact: true }).click(); await ap.waitForTimeout(500);
  const ta = row.getByLabel("Replacement sentence");
  A.draft_prefilled = await ta.inputValue();
  await ta.fill(NEWTEXT); await ap.waitForTimeout(300);
  await shot(ap, "admin-edit-1440-replacement-typed");
  const respP = ap.waitForResponse((r) => r.url().includes(`/tour-versions/${VID}/sentences/apply`), { timeout: 60000 }); respP.catch(() => {});
  await row.getByRole("button", { name: "Apply", exact: true }).click();
  const resp = await respP; const body = await resp.json().catch(() => null); const req = JSON.parse(resp.request().postData() || "{}");
  A.apply = { http: resp.status(), method: resp.request().method(), mode: req.mode, field: req.field, index: req.index, gate: req.gate, warnings: body?.warnings ?? null, error_detail: resp.status() >= 400 ? body?.detail : undefined, highlight4_after: body?.rewritten_content?.highlights?.[4] };
  await ap.waitForTimeout(2000);
  await shot(ap, "admin-after-1440-toast-drawer");
  const d1 = await adminDetail(ap); A.after = { http: d1.status, ...sum(d1.j) };
  const e = d1.j?.admin_edits?.[0] ?? null;
  if (e) {
    const dt = e.details || {};
    A.audit_row = { keys: Object.keys(e), action: e.action, actor: e.actor, created_at: e.created_at, resource_type: e.resource_type, resource_id: e.resource_id,
      details_keys: Object.keys(dt), mode: dt.mode, field: dt.field, index: dt.index, gate: dt.gate, before: dt.before, after: dt.after, version_number: dt.version_number, status: dt.status, exported: dt.exported,
      has_content_before: !!dt.content_before, has_content_after: !!dt.content_after,
      content_before_h4: dt.content_before?.highlights?.[4], content_after_h4: dt.content_after?.highlights?.[4],
      content_before_equals_admin_before: JSON.stringify(dt.content_before) === JSON.stringify(d0.j?.rewritten_content),
      content_after_equals_admin_after: JSON.stringify(dt.content_after) === JSON.stringify(d1.j?.rewritten_content) };
  }
  writeFileSync(`${OUT}/admin-after-rewritten_content.json`, JSON.stringify(d1.j?.rewritten_content, null, 1));
  await ap.reload({ waitUntil: "networkidle" }); await ap.waitForTimeout(3500);
  const s2 = ap.getByText(/Admin edits · \d+/).first();
  A.admin_edits_heading = await s2.innerText().catch(() => null);
  if (await s2.count()) { await s2.scrollIntoViewIfNeeded(); await ap.waitForTimeout(500); }
  await shot(ap, "admin-after-1440-admin-edits-audit-row");
  A.console_errors = errs;
  await ctx.close();
}

try {
  if (STEP === "all" || STEP === "before") await tenantView("before");
  if (STEP === "all" || STEP === "apply") await adminApply();
  if (STEP === "all" || STEP === "after") await tenantView("after");
} catch (e) { log.error = String(e).slice(0, 600); }
await b.close();
writeFileSync(`${TMP}/aa802t2_verify_${STEP}_out.json`, JSON.stringify(log, null, 1));
console.log(JSON.stringify(log, null, 1));
