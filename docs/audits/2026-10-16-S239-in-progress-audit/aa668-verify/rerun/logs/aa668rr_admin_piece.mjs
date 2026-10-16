// Read-only: admin view of two T9 pieces (subject/atom mismatch check). Secrets read in-process, never printed.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const pieces = process.argv.slice(3); const out = process.argv[2];
const b = await chromium.launch(); const ctx = await b.newContext(); const ap = await ctx.newPage();
const a = JSON.parse(sec("aa-cis/dev/e2e-test-admin"));
await ap.goto(`${BASE}/login`, { waitUntil: "load" }); await ap.waitForTimeout(2000);
await ap.fill('input[placeholder="Username"]', a.username); await ap.fill('input[type="password"]', a.password);
await ap.locator("button", { hasText: "Login" }).click();
await ap.waitForURL((u) => !u.toString().includes("/login"), { timeout: 45000 });
const res = {};
for (const id of pieces) {
  res[id] = await ap.evaluate(async (path) => { const h = {}; const rid = localStorage.getItem("cis_reviewer_id"); if (rid) h["x-reviewer-id"] = rid; const r = await fetch(path, { headers: h }); let j = null; try { j = await r.json(); } catch {} return { status: r.status, j }; }, `/api/admin/content-quality/pieces/${id}`);
}
writeFileSync(out, JSON.stringify(res, null, 1));
for (const [id, r] of Object.entries(res)) { const d = r.j?.piece ?? r.j; console.log(id, r.status, JSON.stringify({ route_hub_name: d?.route_hub_name, atom_id: d?.atom_id, angle: d?.angle_name, goal: d?.goal, wi: JSON.stringify(d?.writer_input ?? null).slice(0, 600) })); }
await b.close();
