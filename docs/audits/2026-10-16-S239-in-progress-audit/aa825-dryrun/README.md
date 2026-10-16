# AA-825 — manual DRY RUN of the 5 CIS retention kinds (S239, 16/10/2026)

Agent: Claude Code (S239 subagent). Environment: Dev, acc2 `005097885195`, `https://api-cis.lumiguides.it.com`,
API task def `aa-cis-dev-api:630` (image `dev-802b5920…`). Retention code last changed in CIS `50bd4882` (15/10).

**DRY RUN only.** Every request was `POST /admin/job-runner/retention/run` with body `{"kind": <k>, "dry_run": true}`
(the API turns it into payload `{"trigger": "manual", "dry_run": true}`). The script asserts that body shape before
it sends. No live run, no `max_rows`, no `/retention/schedule` call, no deletes, no S3 writes, no rollup writes.
The admin secret (`aa-cis/dev/admin-secret`, the ARN the ECS task def injects as `ADMIN_SECRET`) was read from
Secrets Manager at run time and sent as `X-Admin-Secret`, the same header the BFF (`frontend/app/api/admin/[...path]/route.ts`)
sets. It was never printed or saved; all evidence files were checked and do not contain it.
Nothing was posted on Linear.

## Preflight (01_preflight.json)

- `GET /admin/job-runner/deploy-gate` at 03:18Z: `active 0`, `safe_to_deploy true`, so `shared.job` was idle (no queued/running).
- `GET /admin/job-runner/summary`: no queued/running rows; all 5 `retention_*` kinds registered (concurrency 1, max_attempts 2).
- `GET /admin/job-runner/retention` before: every kind `last = {}`, `scheduled_mode = dry_run`, both rollup tables at 0 rows.
- One worker alive (`ip-10-2-10-165`, `retention_job` cap 1).

## Results (02_runs.json, 03_after.json)

All 5 jobs `succeeded` with `mode = dry_run` and reason `manual dry run`. Cutoff = UTC midnight minus the window (runner.cutoff).

| Kind | Table (est. rows) | Part / window | Cutoff (UTC) | Rows that would be removed | Archive target | Rollup pending | Job id | Runtime (queue wait / run) |
|---|---|---|---|---|---|---|---|---|
| retention_llm_call_log | shared.llm_call_log (~252,375) | raw / 180 d | 2026-04-19 00:00 | **0** | s3://aa-cis-bronze-005097885195/archive/llm_call_log/yyyy/mm/ (Parquet) | 0 rows to `shared.llm_call_daily` | ba11ec53-3a20-4650-95ec-27f21d176cb2 | 2.1 s / 0.07 s |
| retention_tenant_api_usage | shared.tenant_api_usage (~126,367) | raw / 90 d | 2026-07-18 00:00 | **0** | s3://…/archive/tenant_api_usage/yyyy/mm/ | 0 rows to `shared.tenant_api_usage_monthly` | 13cb13c9-1267-44a1-86fa-8e2fce8dc800 | 0.9 s / 0.03 s |
| retention_job | shared.job (~2,533) | succeeded / 30 d | 2026-09-16 00:00 | **0** | none (delete only) | n/a | e83f37ac-9b33-4424-bc6e-d442c42d77a1 | 4.7 s / 0.06 s |
| | | failed+cancelled+stopped_budget / 90 d | 2026-07-18 00:00 | **0** | s3://…/archive/job/yyyy/mm/ | | | |
| retention_decision_log | shared.decision_log (~280,310) | unlabelled (`outcome IS NULL`) / 180 d | 2026-04-19 00:00 | **0** | s3://…/archive/decision_log/yyyy/mm/ | n/a | d0eec71e-5791-4a16-ae30-05b7a0798670 | 3.2 s / 0.03 s |
| retention_cost_explorer_snapshot | shared.cost_explorer_snapshot (~7,876) | superseded (newer fetch of same account/service/period_start exists) / 1 d | 2026-10-15 00:00 | **5,991** (fetched 2026-09-23 11:06 → 2026-10-12 09:24) | **none — hard delete, no archive** | n/a | d909a01e-6bc7-4831-b737-c8dcfddd11de | 1.9 s / 0.03 s |

Row estimates are `pg_class.reltuples` from `GET /retention` (approximate). FK guard: `shared.job` rows referenced by
`acp_shared.content_piece.job_id`, `gold_aa_internal.tenant_tour_versions.job_id` or `shared.job.parent_job_id` are never
candidates; the other four tables have no inbound FK.

After the run, `GET /retention` shows each kind with a `last.dry_run` entry and `scheduled_mode` still `dry_run`
(correct: no live run exists yet). `deploy-gate` after: `active 0`.

## Why four kinds have 0 candidates (04_job_age_context.json)

The candidate SQL is `count(*) … WHERE ts_col < cutoff [AND part predicate] [AND NOT EXISTS fk]`, so 0 means no row is
older than the window, not a broken query.

- `shared.job`: the oldest job of any status was created 2026-09-28 16:34Z (18 days ago); nothing is older than the
  30 d / 90 d cutoffs. The table is young because the job runner (AA-650) only started writing then.
  First `succeeded` candidates appear on the **29/10/2026** run (cutoff passes 28/09); first failed/cancelled ones
  (oldest finished 01/10) around **30/12/2026**, minus any FK-protected rows.
- `llm_call_log`, `tenant_api_usage`, `decision_log`: no row older than 19/04 (180 d) or 18/07 (90 d). I could not read the
  exact oldest timestamp per table: ECS exec is blocked for subagents in this session, and no admin endpoint exposes it.
  If needed, the orchestrator can run `.tmp-session/s239/aa825_ctx.py` (read-only, `SELECT min/max`, read-only transaction) through the
  usual S3 + ECS exec pattern.

## Surprising / worth knowing

1. **Only cost_explorer_snapshot has anything to delete today, and it is not archived.** 5,991 of ~7,876 rows (~76%) are
   superseded fetches. The policy deletes them without an S3 copy (`archive=False`, by design: a newer fetch of the same
   key exists, and readers only use the newest one). A live run would still need Nghiệp's approval with `max_rows = 5991`.
2. **AA-825 done-when "first TTL run logged with rows archived/deleted per table; S3 objects present" cannot be met yet.**
   The only kind with candidates does not archive, so a live run today writes **no** S3 object under `archive/` and **no**
   rollup rows (`rollup_pending = 0` for both rollups). The archive and rollup paths stay untested on real data until
   `shared.job` failed rows (~end of Dec) or the 90/180-day tables age past their windows. Options for Nghiệp: accept the
   cost_explorer live run + unit tests as proof, keep AA-825 open until data ages, or shorten a window on Dev only for a test
   (a DM-7.5 decision).
3. Each DRY RUN count took 30–70 ms on tables up to ~280 k rows, so the count queries use the indexes. This is
   not the EXPLAIN evidence the issue asks for: the `v_tenant_monthly_usage` EXPLAIN is still open.
4. No daily scheduler is wired yet (`POST /admin/job-runner/retention/schedule` has no caller in AA-CIS-Infra). The runs above
   are `trigger: manual`; scheduled runs stay DRY RUN until a live run of the same windows succeeds.
5. Audit trail: the jobs are recorded as `created_by = admin:claude-code-s239`.

## Files

- `01_preflight.json` — deploy-gate, summary, workers, retention status before.
- `02_runs.json` — enqueue response + final job row (payload, result with per-part cutoff/candidates/oldest/newest) per kind.
- `03_after.json` — retention status + deploy-gate after.
- `04_job_age_context.json` — oldest jobs per status (read-only `GET /admin/job-runner/jobs`).
- `aa825_dryrun.py`, `aa825_jobage.py` — the scripts (secret read at run time; DRY RUN body asserted).
