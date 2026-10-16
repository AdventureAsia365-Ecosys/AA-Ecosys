// S239 AA-802 T2 probe (read-only): find an editable, unexported T2 version of a test tenant with flagged sentences.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const b = await chromium.launch();
const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
const a = JSON.parse(sec("aa-cis/dev/e2e-test-admin"));
const ap = await ctx.newPage();
await ap.goto(`${BASE}/login`, { waitUntil: "load" }); await ap.waitForTimeout(2000);
await ap.fill('input[placeholder="Username"]', a.username); await ap.fill('input[type="password"]', a.password);
await ap.locator("button", { hasText: "Login" }).click();
await ap.waitForURL((u) => !u.toString().includes("/login"), { timeout: 45000 });
const out = await ap.evaluate(async () => {
  const h = { "x-reviewer-id": localStorage.getItem("cis_reviewer_id") || "" };
  const g = async (u) => { const r = await fetch(u, { headers: h }); return { status: r.status, j: await r.json().catch(() => null) }; };
  const all = [];
  for (const st of ["ai_generated", "needs_review"]) {
    for (let off = 0; off < 600; off += 200) {
      const r = await g(`/api/admin/content-quality/tour-versions?limit=200&offset=${off}&status=${st}`);
      if (r.status !== 200) { all.push({ err: r.status, st }); break; }
      all.push(...r.j.data); if (r.j.data.length < 200) break;
    }
  }
  const cands = all.filter((x) => x.tenant_name && /terra|atlas|trail|wild/i.test(x.tenant_name));
  const details = [];
  for (const c of cands.slice(0, 80)) {
    const d = await g(`/api/admin/content-quality/tour-versions/${c.id}`);
    const j = d.j || {};
    details.push({ id: c.id, tenant: c.tenant_name, tenant_id: c.tenant_id, tour: c.tour_name, v: c.version_number, latest: j.latest_version_number, status: c.status, edit_source: c.edit_source,
      editable: j.editable, block: j.edit_block_reason, exported_at: j.tenant_copy?.exported_at, older_copy: j.tenant_copy?.older_copy, admin_edits: j.admin_edits?.length,
      flagged: (j.flagged_sentences || []).map((f) => ({ field: f.field, index: f.index, gates: f.gates, s: f.sentence.slice(0, 160), p: f.problems.map((p) => p.problem).join("; ") })),
      sections: (j.sections || []).map((s) => `${s.field}:${s.index ?? "-"}`).join(","), published_tour_id: j.published_tour_id });
  }
  const tenants = [...new Set(all.map((x) => x.tenant_name))];
  return { total: all.length, tenants, cand_count: cands.length, details };
});
writeFileSync("/home/nghiep/projects/AA-Ecosys/.tmp-session/s239/aa802t2_probe_out.json", JSON.stringify(out, null, 1));
const ed = out.details.filter((d) => d.editable);
console.log(JSON.stringify({ total: out.total, tenants: out.tenants, cand: out.cand_count, editable: ed.length,
  editable_flagged: ed.filter((d) => d.flagged.length).map((d) => ({ id: d.id, tenant: d.tenant, tour: d.tour, v: d.v, status: d.status, exp: d.exported_at, n: d.flagged.length, f0: d.flagged[0] })),
  editable_noflag: ed.filter((d) => !d.flagged.length).map((d) => `${d.tenant}|${d.tour}|v${d.v}|${d.status}|exp=${d.exported_at}`) }, null, 1));
await b.close();
