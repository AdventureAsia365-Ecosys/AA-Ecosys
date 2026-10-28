---
id: FIN-01
title: FinOps process
description: How spend is tagged, budgeted, watched and reviewed across acc2, the acc3 LLM account and external APIs; the rules themselves are data standards DM-10.
type: explanation
status: draft
owner: nghiep
audience: [engineer, devops, cto, cio, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-28
review_every_days: 90
related: [FIN-02, OPS-08, SEC-01, AA-896, AA-884, AA-838, AA-828]
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
| Quote the monthly cost of a new AWS service or resource before it is applied | S241 D-19. Proposed as an explicit line of DM-10.7 in data standards v1.1 (N-1) |

A change to a rule is a PR to the data standards, not an edit here.

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
| LLM and external API caps | Per stage or provider, DB-configured | Refused calls + admin console | `shared.spend_budget` (DM-10.5) |

Not available: an anomaly monitor per `App` tag. AWS allows tag and linked-account monitors only in the
management account; the per-App budgets cover that need. acc3 alerts go to its own SNS topic and e-mail, not to the
acc2 alerts topic: an IMMEDIATE subscription needs an SNS topic in the same account.

Cost of these guards: 0 USD/month. Budgets without actions are free (AWS Budgets pricing page, read
2026-10-19; none of ours has actions), Cost Anomaly Detection is free, and SNS e-mail stays inside the free tier.
Each Cost Explorer API request costs 0.01 USD.

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
48 hours): it re-runs that folder's `scripts/fetch_ce.sh` with the month end and its read-only unit-cost SQL, then
follows the how-to.

## Unit costs

| Unit | Numerator | Denominator |
|---|---|---|
| USD per published tour | `cis` total for the month | Tours published or republished in the month |
| USD LLM per published tour | `cis` LLM spend | Same |
| USD per trip plan | `tripplanner` total | Trip plans created |
| USD per booking | `booking` total | Bookings created (0 during the dev phase) |

Denominators come from read-only counts in the monthly review; Dev numbers are for trend only.

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
