---
id: FIN-01
title: FinOps process
description: How spend is tagged, budgeted, watched and reviewed across acc2, the acc3 LLM account and external APIs; the rules themselves are data standards DM-10.
type: explanation
status: draft
owner: nghiep
audience: [engineer, devops, cto, cio, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 90
related: [FIN-02, OPS-08, SEC-01, APP-06-ai-register, docs/adr/0009-ai-platform-and-provider-gateway.md, AA-896, AA-884, AA-838, AA-828, AA-1004]
---

# FinOps process

The spending **rules** are data standards Part B, section 10 (DM-10.1 to DM-10.7), plus the session rule that
ad-hoc LLM scripts log their cost. This page does not restate them; it explains how they are applied: tags,
budgets, alerts, where to read the numbers and the monthly review.

## The rules, by reference

| Rule | Source |
|---|---|
| Every AWS resource carries `App` (and the existing `Project`, `Environment`, `ManagedBy`) | [DM-10.1](../architecture/data-standards/02-data-management.md#10-cost-ownership) |
| A budget per app next to the account total | DM-10.2 |
| The shared RDS is paid by Infra (`App=shared`) | DM-10.3 |
| Every paid call goes through its seam and lands in its ledger; ad-hoc scripts use `stage = adhoc_<issue>` | DM-10.4; the session rule that hand-run LLM scripts must log their cost (`.kiro/steering/session-workflow.md`) |
| Per-app LLM spend from the rollup; every external spend checks a DB budget | DM-10.5 |
| Paid batch runs on Dev: trial of ~3, then at most ~50 tours, never the whole catalog without approval | DM-10.6 |
| Spend changes need the tech lead's approval | DM-10.7 |
| Quote the monthly cost of a new paid service, resource or feature (AWS or outside) and get the tech lead's explicit yes **for that item** before it is applied. Approval of a plan or a batch of work does not cover a paid item inside it (S255: a security plan approval did not cover GuardDuty) | S241 D-19. Proposed as an explicit line of DM-10.7 in data standards v1.1 (N-1) |
| Paid run ladder: trial of about 3 items, check the cost per item, then at most about 50, then per country; a wave report states the cost per stage, the wave total and $/tour from the ledger | DM-10.6; runbook skill `aa-wave-rerun` |

A change to a rule is a PR to the data standards, not an edit here. Every AI and paid-data stage, with its budget and
kill switch, is listed in the [AI use register](../architecture/ai-use-register.md).

## Where the money is

| Where | What is billed | Ledger or source |
|---|---|---|
| acc2 (infra) | ECS, RDS, ALB, NAT, ElastiCache, Lambda, API Gateway, S3, CloudWatch, Bedrock embeddings | Cost Explorer, stored daily in `shared.cost_explorer_app_snapshot` (by `App` tag) and `shared.cost_explorer_snapshot` (by service) |
| acc3 (LLM account) | Bedrock calls through the satellite role | Cost Explorer per account in `shared.cost_explorer_snapshot`; per call in `shared.llm_call_log` |
| OpenAI, Jev, DataForSEO, geocoder | External APIs | `shared.llm_call_log`, `shared.decision_log`, `shared.dfs_call_log`, `geo.geocode_call` |

acc1 (a personal account) was removed from the ecosystem on 2026-10-28 (AA-998): no LLM call goes there and there is
no cross-account fallback. Its older rows stay in the ledgers and snapshots as history. Account IDs and profiles: the
[account map](../onboarding.md#account-map).

## Tags

- `App` (`cis`, `booking`, `tripplanner`, `crm`, `identity`, `shared`) is active as a cost allocation tag since 2026-10-15
  (AA-828). Untagged spend shows as its own row and is a finding in the monthly review.
- `Environment` already exists on every Terraform resource through the provider `default_tags`
  (`Environment = var.environment`). No new `Env` key is added. To report by environment, the tag must be
  activated as a cost allocation tag. acc2 is a member account, and a member account cannot activate tags
  (Cost Explorer answers "Linked account doesn't have access to cost allocation tags"), so **the tech lead asks the
  payer to activate `Environment`**, as was done for `App`. Cost: 0 USD.
- Tags count only from the day they are set; Cost Explorer does not re-tag older usage.

Where the keys come from in Terraform (INF):

| Root | Provider `default_tags` | `App` |
|---|---|---|
| `accounts/aa365` (acc2) | `Project`, `Environment`, `ManagedBy`, `Account` | Set per resource through `local.common_tags` (`cis`), `local.shared_tags` (`shared`) and the per-app maps, never in `default_tags`, so a resource that forgets its own `App` shows as untagged instead of being billed to `cis` (`main.tf`) |
| `accounts/acc3-bedrock` | `Project`, `Environment`, `ManagedBy`, `Account`, `Issue` | None: Bedrock usage carries no resource tag. Per-app LLM spend comes from the ledger (`app` column), not from tags |
| `accounts/management` | Same keys plus `App = shared` | Every governance resource is `shared` |

No AWS Organizations tag policy exists. Bedrock calls are attributed per app by the gateway ledger, and the
capacity plan (S261) adds one invoker role per app and environment on the LLM account, which AWS bills per IAM
principal without any tag.

## Budgets and alerts

| Guard | Threshold | Goes to | Defined in |
|---|---|---|---|
| Account budget `aa-cis-dev-monthly-total` | 300 USD/month (`var.total_monthly_budget_usd`, raised from 250 in S255); 80 % and 100 % actual, 100 % forecast | Alert e-mail | INF `accounts/aa365/observability.tf` |
| Per-App budgets `aa-cis-dev-monthly-app-*` | cis 90, tripplanner 10, booking 25, crm 35, identity 10, shared 120 USD (S255: crm up from 25, identity new, shared up from 100 so it does not forecast-alert every month); their sum must stay at or under the account budget (Terraform precondition); 80 % actual, 100 % forecast | Alert e-mail | Same file, `var.per_app_monthly_budgets` |
| Cost Anomaly Detection, AWS services monitor | Total impact of an anomaly at least 5 USD | Alerts SNS topic (e-mail, immediate) | INF `accounts/aa365/cost_anomaly.tf` (AA-896) |
| Same monitor, AWS default subscription | Daily summary when impact is at least 100 USD and 40 % | Account e-mail | Created by AWS, not in Terraform |
| acc3 budget `aa3-llm-monthly-total` | 250 USD/month gross of credits (= AWS Lift tier 1); 80 % and 100 % actual, 100 % forecast | E-mail to the bootstrap alert inbox | INF `accounts/acc3-bedrock/cost_guard.tf` (AA-896, applied locally with MFA) |
| acc3 anomaly subscription `aa3-cost-anomaly-daily` | Daily summary of anomalies with total impact at least 10 USD, on the AWS services monitor | Same e-mail | Same file |
| acc3 anomaly subscription `aa3-cost-anomaly-immediate` | Total impact of an anomaly at least 15 USD | acc3 SNS topic `aa3-cost-alerts` (e-mail, immediate) | INF `accounts/acc3-bedrock/cost_anomaly_immediate.tf` (S255) |
| acc3 AWS default subscription | Daily summary when impact is at least 100 USD and 40 % | Account e-mail | Created by AWS, not in Terraform |
| Organization budget `aa-org-monthly` | 300 USD/month gross (`var.org_budget_usd`); 50 %, 80 % and 100 % actual, 100 % forecast | Budget alert e-mails (tech lead and business owner role mailboxes) | INF `accounts/management/budgets.tf` (AA-1004) |
| Per-account budgets `<account name>-monthly` | Management account 10 USD; each member account its `budget_usd` once it is listed in `member_accounts`; 80 % and 100 % actual, 100 % forecast | Same e-mails | Same file |
| Per-account anomaly monitors `<account name>-spend` + `<account name>-anomaly-daily` | Daily summary of anomalies with total impact at least 15 USD (`var.anomaly_threshold_usd`) | Same e-mails | Same file |
| Per-`App` anomaly monitors `aa-app-<app>-spend` | Daily summary, impact at least 15 USD; **prepared, off** (`app_tag_anomaly_monitors_enabled = false`) | Same e-mails | INF `accounts/management/cost_anomaly_app_tag.tf` (AA-896, S262) |
| LLM and external API caps | Per provider and scope, DB-configured (next section) | Refused calls + admin console | `shared.spend_budget` (DM-10.5) |
| LLM connection budgets | Monthly per connection; alert 80 %, hard stop 100 % by default | Refused calls (hard stop) + admin console | `shared.llm_provider_connection.monthly_budget_usd` + `shared.llm_connection_cost_policy` (next section) |

**Per-`App` anomaly monitor: why it is off.** AWS creates tag, cost category and linked-account monitors only in the
management (payer) account. Today acc2 is billed by the reseller's organization, not ours, so a monitor in our
management account would see none of its spend; the per-App budgets on acc2 cover the need meanwhile. Switch it on
(one variable, then the Infra Terraform Apply workflow for the management root) when both are true: the nonprod
account (acc2) has joined our organization (ADR 0018 timeline), and `App` is an active cost allocation tag in the
management account (Billing, Cost allocation tags; activation is not retroactive and takes up to 24 hours). acc3
alerts go to its own SNS topic and e-mail, not to the acc2 alerts topic: an IMMEDIATE subscription needs an SNS topic
in the same account, which is also why the management monitors send daily e-mails.

Cost of these guards: 0 USD/month. Budgets without actions are free (AWS Budgets pricing page, read
2026-10-19; none of ours has actions), Cost Anomaly Detection is free, and SNS e-mail stays inside the free tier.
Each Cost Explorer API request costs 0.01 USD.

## Spend caps in the database

The gateway refuses a call before it is made when a cap is reached (ADR 0009 decision 6, "budgets at every layer").
The live values are on the admin console, Cost Operations, Budgets tab; this table is the seeded state.

| Layer | Where | Seeded values |
|---|---|---|
| Provider and job (`provider`, `scope` = `global` or `job:<kind>`) | `shared.spend_budget` (`per_run_usd`, `per_day_usd`, `hard_stop`, `alert_pct`) | Jev `global`: 5.00 USD per UTC day, hard stop, alert at 80 % (migration 318; rule max(1.00, 2 × p95 daily spend)). DataForSEO `job:s1_rewrite`: 0.50 USD per run (one run = one tour), hard stop (migration 318; rule max(0.50, 2 × p99 per tour)). DataForSEO `global`: 10.00 USD per day, alert only. Bedrock and geocoder rows from earlier migrations |
| LLM connection (monthly) | `shared.llm_provider_connection.monthly_budget_usd` + optional `shared.llm_connection_cost_policy` row (migration 317) | No policy row = alert at 80 %, hard stop at 100 %. Anthropic API connection: 150 USD/month approved 2026-10-31 (a cap, not money paid in). The OpenAI API connection's cap is stated and approved before any purchase |
| Reconciliation | Job `llm_cost_reconcile` (nightly, 0 USD) writes `shared.llm_cost_reconcile`: the ledger next to the provider's own figure per connection and day | Compares gross amounts; Cost Explorer `UnblendedCost` is net of credits |
| Tenant | CRM `ai_budget_usd` per agency (hard, root ADR 0008a); Content studio tenants alert at 100 % and need staff approval from 150 % (AA-1016) | Amounts from the business owner's plan prices |

Over a Jev cap, `decide()` makes no call and the stage keeps its own rule; over the DataForSEO run cap, the rest of
that tour's SEO calls are skipped. Neither fails a job. Every stage with its cap and kill switch:
[AI use register](../architecture/ai-use-register.md).

## Where to read the numbers

- **Admin console, Cost per app** (page `/admin/platform/cost`, API `GET /admin/platform/cost?month=YYYY-MM`, AA-884): acc2 spend by `App`
  tag and service, LLM spend by app, acc3 Bedrock from Cost Explorer next to the gateway estimate (older months also show
  the retired account). The page
  refreshes a stale month by itself at most about once a day (one Cost Explorer request, about 0.30 USD/month in
  the worst case). Add `refresh_if_stale=false` to read stored data only.
- **Admin console, Cost Operations** (page `/admin/cost-ops`, was External Spend at `/admin/llm-usage`, which now
  redirects): tabs Overview, LLM, DataForSEO, AWS bill, Jev and Budgets, plus a month-end forecast per provider and per
  AWS account (`GET /admin/cost-ops/forecast`). The AWS bill tab reads `GET /admin/cost-explorer`; "Refresh from AWS"
  (`POST /admin/cost-explorer/check`) calls Cost Explorer (a few cents).
- **AWS console**: Billing and Cost Management → Cost Explorer (group by tag `App`) and Cost Anomaly Detection.

The overview card (AA-858) and the cost page read the same CIS module, so the numbers agree. Do not write a
new script that calls Cost Explorer (DM-10.4): extend the CIS client if a new grouping is needed.

## Monthly review

One monthly report covers both the C8 capacity review and the cost report (FIN-02 = OPS-08). How to produce it:
[monthly cost report](cost/README.md). It is saved as `docs/audits/<date>-S<nnn>-capacity-review/README.md`
from the template [`templates/cost-report.md`](../templates/cost-report.md), drafted by Claude Code and approved by
the tech lead (C8a). A preliminary August / September / October (month to date) comparison per account, `App` tag, service
and usage type was made on 2026-10-23 (S248): [`docs/audits/2026-10-23-S248-cost-report/`](../audits/2026-10-23-S248-cost-report/README.md).
The final October report is made in the first session on or after 2026-11-03 (Cost Explorer revises a day for about
48 hours). Since S262 the inputs come from `tools/finops/collect_month.py`, run once per app container through
`tools/ecs/ecsx.sh` (cost per app for August to October, LLM by app and stage, tour and trip case counts), and
`tools/finops/monthly_cost_report.py --bundle` drafts every cost section, the month-over-month table and the
five-line Vietnamese summary. The S248 `scripts/fetch_ce.sh` stays a one-off audit pull (usage types, which the stored
snapshots do not hold).

## Unit costs

| Unit | Numerator | Denominator |
|---|---|---|
| USD per published tour | `cis` total for the month | Tours published or republished in the month, counted right after the month ends |
| USD LLM per published tour | `cis` LLM spend | Same |
| USD per trip plan | `tripplanner` total | Trip plans created |
| USD per trip case | `booking` total | Trip cases created in the month (`booking.trip_cases`, not deleted) |
| USD per booking | `booking` total | Of those trip cases, the ones confirmed or later now (0 during the dev phase) |

Denominators come from the read-only counts of `collect_month.py` (trip plans: a manual `--units` value, TripPlanner
runs in Lambda); Dev numbers are for trend only.

The published-tour count is a snapshot. `gold_aa_internal.published_tours` keeps one row per tour and a republish
overwrites `published_at` (no table keeps one row per publish of a tour), so a tour published in September and
republished in October counts only in October, and a past month counted later is too low. The report therefore uses
the counts of the report month from the run right after the month ends, and takes last month's from the CIS bundle
saved with last month's report (`--prev-units`); without it, last month's per-tour cost shows `n/a`. Trip cases are
counted by `created_at`, which does not move.

Per-model LLM unit costs (USD per 1,000 calls, USD per 1M tokens, tokens per call) need no DB: join the Cost
Explorer service line of each model with the CloudWatch `AWS/Bedrock` metrics `Invocations`, `InputTokenCount`,
`OutputTokenCount` and `InvocationClientErrors` (daily sums, us-west-1, acc3; months before November 2026 also have calls on the retired account). The 2026-10-23 report keeps
the pull (`scripts/fetch_cw_bedrock.sh`, about 0.001 USD) and the join (`scripts/bedrock_units.py`). Price per token
is stable per model, so a month-over-month LLM jump is explained by calls and tokens per call; check both.

## When an alert fires

1. Open the anomaly link in the e-mail (Cost Anomaly Detection shows the service, usage type and Region).
2. Check what changed that day: Terraform applies (AA-CIS-Infra Actions), deploys, waves or batch runs
   (`shared.job`, session log).
3. LLM spend: follow the [LLM cost spike playbook](playbooks/llm-cost-spike.md) (AA-892).
4. Infrastructure: find the resource by its `App` tag; stop or scale it only after telling the tech lead (DM-10.7).
5. Write what happened in the session log; a SEV1-2 cost incident gets a postmortem (OPS-04).
