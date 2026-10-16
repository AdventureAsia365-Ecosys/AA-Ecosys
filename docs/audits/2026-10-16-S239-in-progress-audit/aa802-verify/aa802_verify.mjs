// S239 AA-802 live verify (T9 silent correction) on CIS Dev. Approved by Nghiệp (S239) as a Dev write on a test tenant.
// One admin Cut on one flagged sentence of a held, unpublished atlas-hearth blog piece. Secrets read in-process, never printed.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const OUT = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-16-S239-in-progress-audit/aa802-verify";
const SLUG = "atlas-hearth";
const PIECE = "1f02cecb-efd6-4f9c-bf32-1c6efbf3c77b";
const REQ = "41e41098-ffa7-472a-bdb2-da0922f80c0a";
const TARGET = "The shift from museum to market is not a step down in cultural seriousness";
const STEP = process.argv[2] || "all"; // before | apply | after | all
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const BAD = /gate|score|held|flag|repair|ledger|violation|quality|blocking|problem/i;
const OKKEY = new Set(["angle_gate_request_id"]); // an id, not a gate verdict
const keyWalk = (o, path = "$", hits = []) => {
  if (Array.isArray(o)) o.forEach((v, i) => keyWalk(v, `${path}[${i}]`, hits));
  else if (o && typeof o === "object") for (const [k, v] of Object.entries(o)) { if (BAD.test(k) && !OKKEY.has(k)) hits.push(`${path}.${k}`); keyWalk(v, `${path}.${k}`, hits); }
  return hits;
};
const b = await chromium.launch();
const log = { step: STEP, piece: PIECE, request: REQ, tenant: SLUG };
const shot = (p, name, full = false) => p.screenshot({ path: `${OUT}/${name}.png`, fullPage: full });

async function tenantView(tag) {
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } }); const p = await ctx.newPage();
  const errs = []; p.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });
  await p.goto(`${BASE}/tenant-login`); await p.fill('input[type="password"]', sec(`aa-cis/dev/e2e-tenant/${SLUG}`));
  await Promise.all([p.waitForURL(/\/portal/, { timeout: 30000 }), p.click('button:has-text("Access Portal")')]);
  const api = await p.evaluate(async ({ PIECE, REQ }) => {
    const g = async (u) => { const r = await fetch(u); let j = null; try { j = await r.json(); } catch {} return { status: r.status, j }; };
    return {
      piece: await g(`/api/tenant/v1/content-writing/pieces/${PIECE}`),
      latest: await g(`/api/tenant/v1/content-writing/requests/${REQ}/latest-piece`),
      review: await g(`/api/tenant/v1/content-writing/requests/${REQ}/review`),
      reviews: await g(`/api/tenant/v1/content-writing/reviews`),
      pending: await g(`/api/tenant/v1/publish-log/pending`),
    };
  }, { PIECE, REQ });
  const T = {};
  for (const [k, v] of Object.entries(api)) T[k] = { status: v.status, forbidden_keys: keyWalk(v.j) };
  const pieceText = api.piece.j?.content_text ?? api.piece.j?.data?.content_text ?? null;
  const rv = (api.reviews.j?.data ?? []).find((x) => x.piece_id === PIECE);
  const pend = api.pending.j?.data ?? [];
  const sameAngle = pend.filter((x) => x.title === (rv?.angle?.name ?? "The Market as Cultural Decoder"));
  T.summary = {
    piece_keys: api.piece.j ? Object.keys(api.piece.j) : null,
    piece_text_len: pieceText?.length ?? null, piece_text_has_target: pieceText ? pieceText.includes(TARGET) : null,
    my_content_items: (api.reviews.j?.data ?? []).length, my_content_has_piece: !!rv, my_content_text_len: rv?.content_text?.length ?? null,
    my_content_text_has_target: rv?.content_text ? rv.content_text.includes(TARGET) : null,
    latest_piece_id: api.latest.j?.piece?.piece_id ?? api.latest.j?.piece_id ?? null, latest_text_has_target: (api.latest.j?.piece?.content_text ?? "").includes(TARGET),
    review_piece_id: api.review.j?.piece_id ?? api.review.j?.data?.piece_id ?? null, review_text_has_target: JSON.stringify(api.review.j ?? "").includes(TARGET),
    pending_total: pend.length, pending_cards_same_angle: sameAngle.length, pending_piece_ids_same_angle: sameAngle.map((x) => x.piece_id),
    pending_card_preview_has_target: sameAngle.map((x) => x.content_preview?.includes(TARGET)),
  };
  writeFileSync(`${OUT}/tenant-${tag}-content_text.txt`, rv?.content_text ?? pieceText ?? "");
  // UI: My Content drawer deep link
  await p.goto(`${BASE}/portal/t10-review?piece=${PIECE}`, { waitUntil: "networkidle" }); await p.waitForTimeout(3000);
  const dlg = p.getByRole("dialog").last();
  const dlgText = (await dlg.innerText().catch(() => "")) || "";
  T.ui = { drawer_open: (await dlg.count()) > 0, drawer_has_target: dlgText.includes(TARGET),
    drawer_bad_words: [...dlgText.matchAll(/\b(held|flag(ged|s)?|gate|F\d{1,2}_\w+|blocked|quality score|needs review)\b/gi)].map((m) => dlgText.slice(Math.max(0, m.index - 40), m.index + 40)),
    console_errors: errs };
  await shot(p, `tenant-${tag}-1440-my-content-drawer-top`);
  // scroll to the edit point: before = the target sentence; after = the sentence that followed it
  const anchor = tag === "before" ? TARGET : log.after_anchor;
  if (anchor) {
    await p.evaluate((a) => { const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n; while ((n = w.nextNode())) { const i = n.textContent.indexOf(a); if (i >= 0) { const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + a.length); const el = n.parentElement; el.scrollIntoView({ block: "start" }); const rect = r.getBoundingClientRect(); const sc = el.closest('[role="dialog"] *') ; let s = el; while (s && s !== document.body) { if (s.scrollHeight > s.clientHeight + 5 && /(auto|scroll)/.test(getComputedStyle(s).overflowY)) { s.scrollTop += rect.top - s.getBoundingClientRect().top - 120; break; } s = s.parentElement; } return true; } } return false; }, anchor.slice(0, 60));
    await p.waitForTimeout(600);
    await shot(p, `tenant-${tag}-1440-my-content-drawer-edit-point`);
  }
  await p.goto(`${BASE}/portal/t11-publish`, { waitUntil: "networkidle" }); await p.waitForTimeout(3000);
  await shot(p, `tenant-${tag}-1440-t11-ready-to-publish`, true);
  await ctx.close();
  log[`tenant_${tag}`] = T;
  return { text: rv?.content_text ?? pieceText };
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

async function adminApply() {
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } }); const ap = await adminLogin(ctx);
  const A = (log.admin = {});
  const errs = []; ap.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });
  const d0 = await adminDetail(ap);
  A.before = { status: d0.status, piece_status: d0.j?.status, published: d0.j?.published, exported: d0.j?.exported, tenant_copy: d0.j?.tenant_copy, admin_edits: d0.j?.admin_edits?.length, len: d0.j?.content_text?.length, flagged: d0.j?.flagged_sentences?.length };
  await ap.goto(`${BASE}/admin/content-quality?tab=pieces&piece=${PIECE}`, { waitUntil: "networkidle" }); await ap.waitForTimeout(3000);
  await shot(ap, "admin-before-1440-piece-drawer");
  const row = ap.getByTestId("cq-flag-row").filter({ hasText: TARGET }).first();
  A.row_found = (await row.count()) > 0;
  await row.scrollIntoViewIfNeeded(); await ap.waitForTimeout(500);
  await shot(ap, "admin-before-1440-flagged-sentence");
  const cutBtn = row.getByTestId("cq-cut").locator("button");
  A.cut_enabled = await cutBtn.isEnabled().catch(() => false);
  if (!A.row_found || !A.cut_enabled) { A.aborted = "row or Cut not available"; await ctx.close(); return; }
  await cutBtn.click(); await ap.waitForTimeout(800);
  const modal = ap.locator('[role="dialog"]:has-text("Cut this sentence?")').last();
  await shot(ap, "admin-confirm-1440-cut-modal");
  const respP = ap.waitForResponse((r) => r.url().includes(`/content-quality/pieces/${PIECE}/sentences/apply`), { timeout: 60000 }); respP.catch(() => {});
  await modal.getByRole("button", { name: "Cut", exact: true }).click();
  const resp = await respP; const body = await resp.json().catch(() => null);
  A.apply = { status: resp.status(), method: resp.request().method(), mode: JSON.parse(resp.request().postData() || "{}").mode, warnings: body?.warnings ?? null, len_after: body?.content_text?.length ?? null, piece_status_after: body?.status };
  await ap.waitForTimeout(2500);
  await shot(ap, "admin-after-1440-toast-drawer");
  const d1 = await adminDetail(ap);
  const e = d1.j?.admin_edits?.[0] ?? null;
  A.after = { status: d1.status, piece_status: d1.j?.status, admin_edits: d1.j?.admin_edits?.length, tenant_copy: d1.j?.tenant_copy, len: d1.j?.content_text?.length, has_target: d1.j?.content_text?.includes(TARGET), flagged: d1.j?.flagged_sentences?.length,
    audit_row: e ? { keys: Object.keys(e), action: e.action, actor: e.actor, created_at: e.created_at, mode: e.details?.mode ?? e.mode, gate: e.details?.gate ?? e.gate, before: (e.details?.before ?? e.before)?.slice(0, 120), after: e.details?.after ?? e.after, length_before: e.details?.length_before, length_after: e.details?.length_after, published: e.details?.published ?? e.published } : null };
  // after-anchor: the text right after the cut point in the new text
  const t0 = d0.j?.content_text ?? ""; const t1 = d1.j?.content_text ?? "";
  const i = t0.indexOf(TARGET); log.cut_offset = i;
  log.after_anchor = t1.slice(Math.max(0, i - 70), i).trim();
  writeFileSync(`${OUT}/admin-before-content_text.txt`, t0); writeFileSync(`${OUT}/admin-after-content_text.txt`, t1);
  // Admin edits section
  await ap.reload({ waitUntil: "networkidle" }); await ap.waitForTimeout(3000);
  const sec2 = ap.getByText(/Admin edits · \d+/).first();
  A.admin_edits_heading = await sec2.innerText().catch(() => null);
  if (await sec2.count()) { await sec2.scrollIntoViewIfNeeded(); await ap.waitForTimeout(500); }
  await shot(ap, "admin-after-1440-admin-edits-audit-row");
  A.console_errors = errs;
  await ctx.close();
}

try {
  if (STEP === "all" || STEP === "before") await tenantView("before");
  if (STEP === "all" || STEP === "apply") await adminApply();
  if (STEP === "all" || STEP === "after") {
    if (!log.after_anchor) { const t1 = (await import("node:fs")).readFileSync(`${OUT}/admin-after-content_text.txt`, "utf8"); const t0 = (await import("node:fs")).readFileSync(`${OUT}/admin-before-content_text.txt`, "utf8"); const i = t0.indexOf(TARGET); log.after_anchor = t1.slice(Math.max(0, i - 70), i).trim(); }
    await tenantView("after");
  }
} catch (e) { log.error = String(e).slice(0, 500); }
await b.close();
writeFileSync(`/home/nghiep/projects/AA-Ecosys/.tmp-session/s239/aa802_verify_${STEP}_out.json`, JSON.stringify(log, null, 1));
console.log(JSON.stringify(log, null, 1));
