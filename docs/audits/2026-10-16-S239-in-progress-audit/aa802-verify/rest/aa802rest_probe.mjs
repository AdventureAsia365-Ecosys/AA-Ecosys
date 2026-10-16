// S239 AA-802 rest probe (read-only): tenant My Content, /pending, /publish-log for both test tenants; admin detail of candidate pieces.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const CAND = ["c54260a5-e154-4f10-b850-fc40676402b7", "26a20425-95e7-48c1-9c80-01e76948a38e"];
const b = await chromium.launch(); const out = { tenants: {}, admin: {} };
for (const slug of ["atlas-hearth", "terra-family"]) {
  const ctx = await b.newContext(); const p = await ctx.newPage();
  await p.goto(`${BASE}/tenant-login`); await p.fill('input[type="password"]', sec(`aa-cis/dev/e2e-tenant/${slug}`));
  await Promise.all([p.waitForURL(/\/portal/, { timeout: 30000 }), p.click('button:has-text("Access Portal")')]);
  const r = await p.evaluate(async () => {
    const g = async (u) => { const r = await fetch(u); let j = null; try { j = await r.json(); } catch {} return { status: r.status, j }; };
    return { reviews: await g("/api/tenant/v1/content-writing/reviews"), pending: await g("/api/tenant/v1/publish-log/pending"), plog: await g("/api/tenant/v1/publish-log?limit=200") };
  });
  out.tenants[slug] = { st: [r.reviews.status, r.pending.status, r.plog.status], reviews_keys: Object.keys(r.reviews.j || {}),
    reviews: (r.reviews.j?.data ?? []).map((x) => ({ piece_id: x.piece_id, request_id: x.request_id, channel: x.channel, ready: x.ready_state, angle: x.angle?.name })),
    pending: (r.pending.j?.data ?? []).map((x) => ({ piece_id: x.piece_id, title: x.title, channel: x.channel, keys: Object.keys(x) })),
    plog: r.plog.j };
  await ctx.close();
}
const a = JSON.parse(sec("aa-cis/dev/e2e-test-admin"));
const ctx = await b.newContext(); const ap = await ctx.newPage();
await ap.goto(`${BASE}/login`, { waitUntil: "load" }); await ap.waitForTimeout(2000);
await ap.fill('input[placeholder="Username"]', a.username); await ap.fill('input[type="password"]', a.password);
await ap.locator("button", { hasText: "Login" }).click();
await ap.waitForURL((u) => !u.toString().includes("/login"), { timeout: 45000 });
for (const id of CAND) {
  const d = await ap.evaluate(async (id) => { const r = await fetch(`/api/admin/content-quality/pieces/${id}`, { headers: { "x-reviewer-id": localStorage.getItem("cis_reviewer_id") || "" } }); let j = null; try { j = await r.json(); } catch {} return { status: r.status, j }; }, id);
  const j = d.j || {};
  out.admin[id] = { status: d.status, piece_status: j.status, tenant: j.tenant_name, channel: j.channel, created_at: j.created_at, published: j.published, exported: j.exported, tenant_copy: j.tenant_copy, len: j.content_text?.length, request_id: j.request_id, admin_edits: j.admin_edits?.length, others: j.other_pieces_for_request, flagged: (j.flagged_sentences || []).map((s) => ({ gates: s.gates, blocking: s.blocking, sentence: s.sentence })) };
}
await ctx.close(); await b.close();
writeFileSync("/home/nghiep/projects/AA-Ecosys/.tmp-session/s239/aa802rest_probe_out.json", JSON.stringify(out, null, 1));
console.log(JSON.stringify(out, null, 1));
