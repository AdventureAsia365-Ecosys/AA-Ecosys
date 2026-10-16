// S239 AA-857 live T9: read-only admin view of the shared.job rows + LLM cost for this run (same method as AA-668 rerun).
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const TENANT = "20d07d32-ed98-405f-81d5-0c2399c9fcdf";
const RID = "41e94397-aa14-45f6-9e23-337a0362fd19";
const PID = "6925acce-b2ed-49bd-a52b-41a74a2e6d60";
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } }); const p = await ctx.newPage();
const a = JSON.parse(sec("aa-cis/dev/e2e-test-admin"));
await p.goto(`${BASE}/login`, { waitUntil: "load" }); await p.waitForTimeout(2000);
await p.fill('input[placeholder="Username"]', a.username); await p.fill('input[type="password"]', a.password);
await p.locator("button", { hasText: "Login" }).click();
await p.waitForURL((u) => !u.toString().includes("/login"), { timeout: 45000 });
const api = (path) => p.evaluate(async (path) => { const h = {}; const rid = localStorage.getItem("cis_reviewer_id"); if (rid) h["x-reviewer-id"] = rid; const r = await fetch(path, { headers: h }); let j = null; try { j = await r.json(); } catch {} return { status: r.status, j }; }, path);
const list = await api(`/api/admin/job-runner/jobs?created_by=${encodeURIComponent("tenant:" + TENANT)}&since=2026-10-16T08:35:00Z&page_size=50`);
const rows = (list.j?.jobs ?? list.j?.data ?? list.j?.items ?? []);
const mine = rows.filter((j) => { const pl = j.payload || {}; return pl.request_id === RID || pl.piece_id === PID; });
const out = { list_status: list.status, jobs_listed_since_0835: rows.length, jobs: [], total_cost_usd: 0 };
for (const j of mine) {
  const c = await api(`/api/admin/job-runner/jobs/${j.id ?? j.job_id}/llm-calls`);
  const calls = c.j?.calls ?? c.j?.data ?? c.j?.items ?? c.j ?? [];
  const arr = Array.isArray(calls) ? calls : [];
  const sum = arr.reduce((s, x) => s + Number(x.cost_usd || 0), 0);
  out.total_cost_usd += sum;
  out.jobs.push({ id: j.id ?? j.job_id, kind: j.kind, status: j.status, cost_usd_job: j.cost_usd, created_at: j.created_at, finished_at: j.finished_at, attempt: j.attempt, payload_keys: j.payload ? Object.keys(j.payload) : null,
    llm_status: c.status, llm_calls: arr.length, llm_cost_usd: Number(sum.toFixed(6)), calls: arr.map((x) => ({ stage: x.stage, role: x.role, model: x.model, tokens_in: x.tokens_in, tokens_out: x.tokens_out, cost_usd: x.cost_usd })), llm_raw_keys: c.j && !Array.isArray(c.j) ? Object.keys(c.j) : null });
}
out.total_cost_usd = Number(out.total_cost_usd.toFixed(6));
const pc = await api(`/api/admin/content-quality/pieces/${PID}`);
out.admin_piece_probe = { path: `/api/admin/content-quality/pieces/${PID}`, status: pc.status, status_field: pc.j?.status, held_reason: pc.j?.held_reason };
writeFileSync("/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-16-S239-in-progress-audit/aa857/live-t9/raw/12_admin_jobs_llm_cost.json", JSON.stringify(out, null, 1));
console.log(JSON.stringify({ list_status: list.status, n: mine.length, total: out.total_cost_usd, jobs: out.jobs.map((j) => [j.kind, j.status, j.llm_calls, j.llm_cost_usd, j.cost_usd_job]), piece: out.admin_piece_probe }));
await b.close();
