---
id: OPS-04-llm-cost-spike
title: LLM or paid-API cost spike
description: Find and stop unexpected spend on Bedrock, OpenAI, Jev, DataForSEO or the geocoder, using the existing ledgers, budgets and job controls.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [aa-cis-worker, aa-cis-api, tripplanner-lambda]
last_reviewed: 2026-10-28
review_every_days: 90
related: [OPS-04, OPS-04-queue-stuck, APP-09, FIN-01, APP-06, AA-649, AA-804, AA-896]
---

# LLM or paid-API cost spike

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> Written from the cost guard, ledgers and budgets; facts re-checked against code and Terraform on 2026-10-28.

## Triggers

- An AWS Budgets alert on **acc2** (alerts topic e-mail). The account budget `aa-cis-dev-monthly-total` is 300 USD.
  Each `App` tag has its own budget, `aa-cis-dev-monthly-app-<app>`: `shared` 120, `cis` 90, `crm` 35, `booking` 25,
  `identity` 10, `tripplanner` 10 USD (AA-CIS-Infra `accounts/aa365`, `var.per_app_monthly_budgets`).
- An AWS Budgets e-mail on **acc3**, the LLM account: `aa3-llm-monthly-total`, 250 USD, credits excluded
  (`accounts/acc3-bedrock/cost_guard.tf`).
- A Cost Anomaly Detection alert. On acc2, monitor `Default-Services-Monitor` sends any anomaly of 5 USD or more to
  the alerts topic at once. On acc3, a daily e-mail covers anomalies from 10 USD, and the topic `aa3-cost-alerts`
  sends anomalies from 15 USD at once (`accounts/acc3-bedrock/cost_anomaly_immediate.tf`).
- Bedrock runs on acc3 only (AA-998; see the [account map](../../onboarding.md#account-map)). Its spend shows in the
  acc3 bill and budget, not in the acc2 budgets. The app ledger below covers every call.
- A job ended `stopped_budget`, or the admin **Budgets** page shows today's spend near a limit.

## Facts (the controls that exist)

| Control | Where | Effect |
|---|---|---|
| Cost guard (AA-649) | `shared.spend_budget` rows per (provider, scope): `per_run_usd`, `per_day_usd`, `hard_stop`, `alert_pct`; providers `dfs`, `bedrock`, `openai`, `jev`, `geocoder` | A job checks before each paid call; a hard limit raises and the job ends `stopped_budget` |
| Admin budgets page | `GET /admin/budgets`, `PUT /admin/budgets/{provider}/{scope}` (admin) | Read today's spend; lower a limit to stop new spend at once |
| TripPlanner daily cap | Lambda setting, code default 5 USD per UTC day for the customer-facing stages (`tripplanner.llm_spend_daily`) | Over the cap, narration falls back to plain text and free-text search answers 503 |
| Ledgers | `shared.llm_call_log` (every call, `stage`, `role`, `model`, `cost_usd`, `job_id`, `account`), `shared.llm_call_daily` (per day, app, stage, model), `shared.dfs_call_log`, `geo.geocode_call` | Who spent what |
| Jobs | admin Jobs page: cancel queued or running jobs; `/admin/job-runner/jobs/{id}/llm-calls` | Stop the spender |
| Model routes | admin LLM config (`/admin/llm-config`) | Switch a stage to a cheaper model (admin, confirm-gated) |

No new Cost Explorer script is needed or wanted. The monthly view is `shared.cost_explorer_snapshot` plus the
ledgers (DM-10.4; see the [FinOps process](../finops.md)).

## Steps

1. Who is spending today (read-only, CIS [ECS exec](../runbooks/ecs-exec-s3-mediated.md)):

   ```sql
   SELECT app, tenant_id, stage, model, account, sum(calls) AS calls, round(sum(cost_usd), 2) AS usd
   FROM shared.llm_call_daily WHERE day >= current_date - 1 GROUP BY 1,2,3,4,5 ORDER BY usd DESC LIMIT 15;
   ```

   For the last hour, by job: `SELECT job_id, stage, count(*), round(sum(cost_usd),2) FROM shared.llm_call_log WHERE created_at > now() - interval '1 hour' GROUP BY 1,2 ORDER BY 4 DESC LIMIT 10;`
   Expected: one stage or one job dominates. `adhoc_<issue>` stages are hand-run scripts: find who runs them.

2. Stop it.
   - A job: cancel it on the Jobs page (and its queued siblings of the same kind).
   - A wave: pause the wave (no new jobs), then cancel the queued ones ([queue stuck](queue-stuck.md)).
   - A provider in general: lower `per_day_usd` (or set `hard_stop`) for that provider on the Budgets page. # WRITE
   - One tenant driving T-series spend (`tenant_id` in step 1, usage in `shared.tenant_rewrite_usage` /
     `shared.tenant_api_usage`): the tech lead contacts the tenant. Suspending a tenant is the tech lead's call.
   - A hand-run script: stop the ECS exec session. Remind the runner of the rule: paid runs start with a trial of
     about 3, then at most about 50.
   Expected: step 1's numbers stop growing within minutes.
   Rollback: restore the previous budget value (the page shows `updated_by` / `updated_at`); re-queue cancelled jobs
   with **Retry** when the cause is fixed.

3. Check the provider side if the ledger looks normal but the bill does not (a call path that does not log is a bug,
   AA-635 rule): the Bedrock and OpenAI consoles' usage per day, and the acc3 bill.

## Close

- Spend back to normal, the cause fixed or a follow-up issue opened, the limit back to its agreed value.
- Tell the business owner when a budget e-mail fired: the amount and the cause, in Vietnamese, with no internal
  issue keys. The threshold for telling the business owner is not decided yet (open point for the
  [FinOps process](../finops.md)).
