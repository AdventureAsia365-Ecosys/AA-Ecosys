// S239 AA-668: read-only admin view of the shared.job rows + LLM cost for the terra-family jobs of this run.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const TENANT = "20d07d32-ed98-405f-81d5-0c2399c9fcdf";
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } }); const p = await ctx.newPage();
const a = JSON.parse(sec("aa-cis/dev/e2e-test-admin"));
await p.goto(`${BASE}/login`, { waitUntil: "load" }); await p.waitForTimeout(2000);
await p.fill('input[placeholder="Username"]', a.username); await p.fill('input[type="password"]', a.password);
await p.locator("button", { hasText: "Login" }).click();
await p.waitForURL((u) => !u.toString().includes("/login"), { timeout: 45000 });
const api = (path) => p.evaluate(async (path) => { const h = {}; const rid = localStorage.getItem("cis_reviewer_id"); if (rid) h["x-reviewer-id"] = rid; const r = await fetch(path, { headers: h }); let j = null; try { j = await r.json(); } catch {} return { status: r.status, j }; }, path);
const list = await api(`/api/admin/job-runner/jobs?created_by=${encodeURIComponent("tenant:" + TENANT)}&since=2026-10-16T02:20:00Z&page_size=50`);
const rows = (list.j?.jobs ?? list.j?.data ?? list.j?.items ?? []);
const out = { list_status: list.status, list_keys: list.j ? Object.keys(list.j) : null, jobs: [] };
for (const j of rows) {
  const c = await api(`/api/admin/job-runner/jobs/${j.id ?? j.job_id}/llm-calls`);
  out.jobs.push({ id: j.id ?? j.job_id, kind: j.kind, status: j.status, created_at: j.created_at, finished_at: j.finished_at ?? j.completed_at, attempts: j.attempts, payload_keys: j.payload ? Object.keys(j.payload) : null,
    payload_ids: j.payload ? Object.fromEntries(Object.entries(j.payload).filter(([k]) => /id$/.test(k))) : null, llm: { status: c.status, totals: c.j?.totals, calls: (c.j?.calls ?? []).map((x) => `${x.stage}/${x.role}/${x.model_id ?? x.model}:${x.cost_usd ?? x.cost}`) } });
}
writeFileSync("/home/nghiep/projects/AA-Ecosys/.tmp-session/s239/aa668_jobs_out.json", JSON.stringify(out, null, 1));
console.log(JSON.stringify(out, null, 1).slice(0, 6000));
await b.close();
