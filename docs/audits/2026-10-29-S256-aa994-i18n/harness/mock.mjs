// Local mock of the CIS API for AA-994 screenshots (no AWS, no real data). Sample values only.
import http from "node:http";
import { OPS_FIXTURE } from "/home/nghiep/projects/AA-Ecosys/.tmp-session/wt/aa994-i18n/frontend/app/admin/overview/_components/opsFixture.ts";

const NOW = Date.parse("2026-10-29T01:30:00Z");
const iso = (minAgo) => new Date(NOW - minAgo * 60_000).toISOString();
const T1 = "11111111-1111-4111-8111-111111111111", T2 = "22222222-2222-4222-8222-222222222222";
const tenants = { tenants: [
  { tenant_id: T1, name: "Lotus Travel", slug: "lotus-travel", status: "active" },
  { tenant_id: T2, name: "Mekong Journeys", slug: "mekong-journeys", status: "active" },
] };
const funnel = [["VN", 412, 6, 398, 5, 21, 360, 4, 352], ["TH", 288, 3, 270, 2, 14, 241, 3, 238], ["KH", 131, 1, 126, 0, 9, 110, 1, 108], ["LA", 74, 0, 70, 0, 4, 63, 0, 61]]
  .map(([country, raw_active, raw_7d, generated, generated_7d, in_review, published, published_7d, atomized]) =>
    ({ country, raw_active, raw_7d, generated, generated_7d, in_review, published, published_7d, atomized }));
const overview = {
  pipeline_funnel: funnel,
  intelligence: { atom_count: 18432, segment_count: 2210, route_count: 640, hub_count: 85, score_count: 15120,
    research: { places_researched: 3120, places_stale: 140, demand_rows: 9800, last_researched: iso(300) } },
  tenants: { active_tenants: 2, rewrites_7d: 46, pieces_7d: 120, published_pieces_7d: 88,
    quota_outliers: [{ tenant_name: "Lotus Travel", plan_tier: "growth", quota_tours_pct: 92, quota_calls_pct: 71 }] },
  jobs: { counts: { queued: 3, running: 2, succeeded: 412, failed: 4 }, workers_alive: 2, queue_depth: 3, running_now: 2 },
  cost: { spent_today_usd: { bedrock: 1.84, openai: 0.62 }, month_to_date_usd: { bedrock: 48.2, openai: 17.9 },
    ai_month_to_date_usd: 66.1, budgets: [{ provider: "bedrock", scope: "daily", per_day_usd: 10, alert_pct: 80 }],
    dfs_balance: { balance_usd: 42.5, below_threshold: false, threshold_usd: 10, has_data: true } },
  alerts: [{ event_type: "job_failed", entity_type: "job", entity_id: "a1b2c3d4", payload: {}, created_at: iso(45) }],
};
const reviewRows = [
  ["Hoi An Lantern Evening Walk", "VN", 0.71, "needs_human", "F1_grounding: Number not in source"],
  ["Mekong Delta Floating Market Day", "VN", 0.64, "low_quality", "F2_banned_patterns: Cliché / banned phrase"],
  ["Chiang Mai Old City by Bicycle", "TH", 0.82, null, ""],
  ["Angkor Sunrise and Temples", "KH", 0.58, "hard", "F0_complete: Text cut off"],
  ["Luang Prabang Alms and Kuang Si Falls", "LA", 0.77, null, ""],
  ["Bangkok Canals Long-tail Boat", "TH", 0.69, "low_quality", "F4_extreme_length: Length out of range"],
].map(([aa_name, country, score_overall, kind, failure_summary], i) => ({
  id: 9100 + i, tour_id: `t-${i}`, generated_content_id: `g-${i}`, aa_name, country, score_overall,
  created_at: iso(60 * (i + 2)), version_num: 2, failure_summary, human_edited: i === 2,
  failures: failure_summary ? [{ code: failure_summary.split(":")[0] }] : [],
  block: kind ? { kind, label: kind } : null, failure_class: kind, retryable: kind !== "hard",
}));
const pieces = ["F1_grounding", "F2_banned_patterns", null, "F4_extreme_length", null, "F11_brand_name"].map((g, i) => ({
  piece_id: `p-${i}`, tenant_id: i % 2 ? T2 : T1, tenant_name: i % 2 ? "Mekong Journeys" : "Lotus Travel",
  channel: ["facebook", "blog", "instagram", "blog", "linkedin", "facebook"][i], status: g ? "held" : "approved",
  held_reason: g ? "gate_failed" : null, attempt_number: 1, created_at: iso(30 * (i + 1)), job_id: `j-${i}`,
  title: ["Lantern nights in Hoi An", "A morning on the Mekong", "Pedal the old city", "Angkor at first light", "Waterfalls near Luang Prabang", "Bangkok from the water"][i],
  angle_name: "Local life", goal: "engagement", content_chars: 900 + i * 120, has_writer_input: true,
  failed_gates: g ? [g] : [], flag_gates: i === 2 ? ["F5_atom_density"] : [], cost_usd: 0.012 + i * 0.002,
}));
const stats = { gates: [["F1_grounding", 120, 9, 6], ["F2_banned_patterns", 120, 5, 5], ["F4_extreme_length", 120, 3, 1], ["F11_brand_name", 120, 1, 1]]
  .map(([gate, runs, failed, blocking_failed]) => ({ gate, channel: "blog", runs, failed, blocking_failed })),
  tenants: [{ tenant_name: "Lotus Travel", tenant_id: T1, pieces: 70, approved: 61, held: 7, failed: 2, cost_usd: 0.94 },
    { tenant_name: "Mekong Journeys", tenant_id: T2, pieces: 50, approved: 44, held: 5, failed: 1, cost_usd: 0.71 }] };
const kinds = ["s1_rewrite", "atomize", "t2_generate", "photo_sync", "seo_research"];
const jobs = Array.from({ length: 8 }, (_, i) => ({
  id: `0c1d2e3f-0000-4000-8000-00000000000${i}`, kind: kinds[i % 5], status: ["running", "queued", "succeeded", "succeeded", "failed", "succeeded", "cancelled", "succeeded"][i],
  attempt: 1, max_attempts: 3, payload: { tour_id: `t-${i}` }, progress: null, result: null, cost_usd: 0.02 * i, error: i === 4 ? "Timed out waiting for the model" : null,
  cancel_requested: false, created_by: "local-admin", run_after: null, created_at: iso(20 * i + 5), started_at: i === 1 ? null : iso(20 * i + 4),
  finished_at: i < 2 ? null : iso(20 * i), links: null,
}));
const summary = { counts: [{ kind: "s1_rewrite", status: "succeeded", n: 210, cost_usd: 8.4 }, { kind: "atomize", status: "succeeded", n: 180, cost_usd: 2.1 },
  { kind: "t2_generate", status: "failed", n: 4, cost_usd: 0.1 }, { kind: "photo_sync", status: "running", n: 2, cost_usd: 0 }, { kind: "seo_research", status: "queued", n: 3, cost_usd: 0 }],
  kinds: kinds.map((kind) => ({ kind, concurrency: 2, max_attempts: 3, expected_seconds: 120 })) };
const workers = { workers: [{ worker_id: "worker-a", host: "ip-10-0-1-11", started_at: iso(600), last_seen_at: iso(0.2), stopped_at: null, max_parallel: 4,
  caps: { s1_rewrite: 2 }, task_revision: 112, running_jobs: 2, reaped_requeued: 0, reaped_failed: 0, last_reap_at: null, last_reaped: null, alive: true }],
  running: [{ worker_id: "worker-a", kind: "photo_sync", n: 1, oldest_started_at: iso(4) }], queued: [{ kind: "seo_research", n: 3, ready: 3, oldest_created_at: iso(25) }], alive_seconds: 90 };

const routes = [
  [/^\/auth\/verify-admin$/, () => ({ admin_id: "local-admin", role: "admin", display_name: "Local Admin", email: "admin@example.test" })],
  [/^\/admin\/overview\/ops/, () => OPS_FIXTURE],
  [/^\/admin\/overview/, () => overview],
  [/^\/admin\/notifications\/count/, () => ({ unread: 2 })],
  [/^\/admin\/notifications/, () => []],
  [/^\/admin\/tenants/, () => tenants],
  [/^\/admin\/review-queue\?.*page_size=1(&|$)/, () => ({ data: reviewRows.slice(0, 1), pagination: { page: 1, page_size: 1, total: reviewRows.length } })],
  [/^\/admin\/review-queue/, () => ({ data: reviewRows, pagination: { page: 1, page_size: 25, total: reviewRows.length },
    facets: { countries: [{ country: "VN", n: 2 }, { country: "TH", n: 2 }, { country: "KH", n: 1 }, { country: "LA", n: 1 }] } })],
  [/^\/admin\/content-quality\/pieces/, () => ({ data: pieces, total: pieces.length, limit: 50, offset: 0, labels_enabled: true })],
  [/^\/admin\/content-quality\/stats/, () => stats],
  [/^\/admin\/job-runner\/jobs/, () => ({ jobs, total: jobs.length, pagination: { page: 1, page_size: 25, total: jobs.length, pages: 1 } })],
  [/^\/admin\/job-runner\/summary/, () => summary],
  [/^\/admin\/job-runner\/workers/, () => workers],
];
http.createServer((req, res) => {
  req.resume();
  req.on("end", () => {
    const hit = routes.find(([re]) => re.test(req.url));
    console.log(hit ? "200" : "404", req.method, req.url);
    res.writeHead(hit ? 200 : 404, { "content-type": "application/json" });
    res.end(JSON.stringify(hit ? hit[1]() : { detail: "not mocked" }));
  });
}).listen(4010, "127.0.0.1", () => console.log("mock on 4010"));
