// S239 AA-802 (b) read-only: for atlas-hearth + terra-family, compare T11 /pending with My Content items that have no live publish.
import { chromium } from "/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright/index.mjs";
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
const BASE = "https://aa-cis.lumiguides.it.com";
const OUT = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-16-S239-in-progress-audit/aa802-verify/rest";
const PUBLISHABLE = new Set(["blog", "facebook"]); // v1_publish.py _SUPPORTED_CHANNELS
const sec = (id) => execFileSync("aws", ["secretsmanager", "get-secret-value", "--secret-id", id, "--profile", "aa365-admin", "--region", "us-west-1", "--query", "SecretString", "--output", "text"], { encoding: "utf8" }).trim();
const b = await chromium.launch(); const out = {};
for (const slug of ["atlas-hearth", "terra-family"]) {
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } }); const p = await ctx.newPage();
  await p.goto(`${BASE}/tenant-login`); await p.fill('input[type="password"]', sec(`aa-cis/dev/e2e-tenant/${slug}`));
  await Promise.all([p.waitForURL(/\/portal/, { timeout: 30000 }), p.click('button:has-text("Access Portal")')]);
  const r = await p.evaluate(async () => {
    const g = async (u) => { const r = await fetch(u); let j = null; try { j = await r.json(); } catch {} return { status: r.status, j }; };
    return { reviews: await g("/api/tenant/v1/content-writing/reviews"), pending: await g("/api/tenant/v1/publish-log/pending"), plog: await g("/api/tenant/v1/publish-log?limit=200") };
  });
  const rv = r.reviews.j?.data ?? [], pd = r.pending.j?.data ?? [], pl = r.plog.j?.data ?? [];
  const live = new Set(pl.filter((x) => x.status === "published").map((x) => x.piece_id));
  const items = rv.map((x) => {
    const rows = pl.filter((y) => y.piece_id === x.piece_id);
    const state = live.has(x.piece_id) ? "published (live)" : rows.length ? `unpublished (${rows.length} earlier publish row${rows.length > 1 ? "s" : ""}, all removed)` : "never published";
    return { piece_id: x.piece_id, request_id: x.request_id, channel: x.channel, ready_state: x.ready_state, title: x.angle?.name, publish_state: state, publishable_channel: PUBLISHABLE.has(x.channel), in_pending: pd.some((y) => y.piece_id === x.piece_id) };
  });
  const expected = items.filter((x) => x.ready_state === "ready" && x.publishable_channel && !live.has(x.piece_id));
  const reqOf = Object.fromEntries(rv.map((x) => [x.piece_id, x.request_id]));
  const pendReq = pd.map((x) => reqOf[x.piece_id] ?? `UNKNOWN:${x.piece_id}`);
  out[slug] = {
    http: { reviews: r.reviews.status, pending: r.pending.status, publish_log: r.plog.status },
    my_content_total: rv.length, my_content_no_live_publish: items.filter((x) => !live.has(x.piece_id)).length,
    my_content_no_live_publish_publishable_channel: expected.length, pending_cards: pd.length,
    equal_on_publishable_channels: expected.length === pd.length && expected.every((x) => x.in_pending),
    pending_piece_ids_unique: new Set(pd.map((x) => x.piece_id)).size === pd.length,
    pending_request_ids: pendReq, pending_request_ids_unique: new Set(pendReq).size === pendReq.length,
    pending_pieces_all_in_my_content: pd.every((x) => reqOf[x.piece_id]),
    items, publish_log_rows: pl.map((x) => ({ piece_id: x.piece_id, channel: x.channel, status: x.status, published_at: x.published_at, unpublished_at: x.unpublished_at })),
  };
  await p.goto(`${BASE}/portal/t10-review`, { waitUntil: "networkidle" }); await p.waitForTimeout(2500);
  await p.screenshot({ path: `${OUT}/b-${slug}-1440-my-content-list.png` });
  await p.goto(`${BASE}/portal/t11-publish`, { waitUntil: "networkidle" }); await p.waitForTimeout(3000);
  out[slug].t11_ui_text_has_titles = await p.evaluate((titles) => titles.map((t) => document.body.innerText.includes(t)), pd.map((x) => x.title));
  await p.screenshot({ path: `${OUT}/b-${slug}-1440-t11-publish.png`, fullPage: true });
  await ctx.close();
}
await b.close();
writeFileSync(`${OUT}/b-pending-vs-my-content.json`, JSON.stringify(out, null, 1));
console.log(JSON.stringify(Object.fromEntries(Object.entries(out).map(([k, v]) => [k, { ...v, items: v.items.map((i) => `${i.channel} ${i.publish_state} pend=${i.in_pending} ${i.title}`), publish_log_rows: v.publish_log_rows.length }])), null, 1));
