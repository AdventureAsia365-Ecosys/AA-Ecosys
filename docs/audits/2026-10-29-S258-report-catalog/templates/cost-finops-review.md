---
id: FIN-02-yyyy-mm
title: Cost review <YYYY-MM>
description: <One sentence - month total vs last month and budget, the biggest mover and the one decision needed, if any.>
type: report
status: draft
owner: nghiep
audience: [owner, engineer, cto, cio, pm]
applies_to: [ecosystem]
last_reviewed: 2026-10-29
review_every_days: 30
related: [FIN-01, OPS-08, PLAT-01, AA-896]
---

# Cost review <YYYY-MM>

<!-- Report family: cost and FinOps. Replaces docs/templates/cost-report.md. Covers FI-01 (monthly, with FI-03, FI-05,
FI-06 sections) and, as Part B, the Booking commercial close FI-07 / BK-03.
Part A is platform cost: save as docs/audits/<date>-S<nnn>-capacity-review/cost.md with a root PR, next to the OPS-08
capacity README. Part B holds commercial numbers: it is generated inside AA-Booking, stored under the booking/ prefix
of the reports bucket and never committed to git.
Sources (DM-10.4, no new Cost Explorer script): shared.cost_explorer_snapshot, shared.cost_explorer_app_snapshot,
shared.llm_call_daily, vendor ledgers. Budgets: infra/AA-CIS-Infra/accounts/aa365/variables.tf and accounts/acc3-bedrock/cost_guard.tf.
Drafted on business day 2; cost is provisional before day 3 (Cost Explorer settles about 48 h).
No account ID, ARN or resource ID on this page. Delete this comment. -->

> [!NOTE]
> Dev account. Spend reflects development and test runs, not customer load.

Month: <YYYY-MM>. Generated: <UTC time>, run <report_run id>. Cost data as of: <date> (<provisional | final>).
KPI definitions: `docs/reports/kpis.yaml` v<n>. Previous: <link>. Approved by: <role>, <date>.

## Summary for the business owner

NARRATIVE (Vietnamese, five lines, copied into the monthly business review): total, vs budget, biggest mover, unit cost, decision.

## How to read this report

- Budgets are monthly and per App tag; a red line means actual or forecast above budget.
- acc3 is shown gross (before credits) so credit expiry does not hide real cost.
- A mover is a service whose cost changed more than 20 % and more than 2 USD; every mover needs a reason.

## Part A - Platform cost

### A1. KPIs

| KPI (ID@version) | Definition | Target | Actual | Last month | 3-month avg | Status |
|---|---|---|---|---|---|---|
| K-COST-ACC2@1 | acc2 month total / 300 USD | <= 100 % | | | | |
| K-COST-APP@1 | Per-App actual / per-App budget (worst App shown) | each <= 100 % | | | | |
| K-COST-UNTAGGED@1 | Untagged / acc2 total | < 5 % | | | | |
| K-COST-EXPLAINED@1 | Movers with a written reason | 100 % | | | | |
| K-LLM-RECON@1 | Gateway ledger vs Cost Explorer (acc3) | <= 10 % gap | | | | |
| K-UNIT-TOUR@1 | USD per published tour | MoM <= +20 % | | | | |

### A2. Totals by account

| Account | Total | Credits | Net | Budget | Variance |
|---|---|---|---|---|---|
| acc2 | | | | 300 | |
| acc3 (gross) | | | | 250 | |
| acc1 (retired, must be 0) | | | | 0 | |

### A3. By App tag

| App | Actual | Budget | Variance | Forecast next month | Note |
|---|---|---|---|---|---|
| cis | | 90 | | | |
| tripplanner | | 10 | | | |
| booking | | 25 | | | |
| crm | | 35 | | | |
| identity | | 10 | | | |
| shared | | 120 | | | |
| untagged | | - | | | |

### A4. Top services and movers

| Service | This month | Last month | Change | Reason |
|---|---|---|---|---|

### A5. LLM spend (FI-03)

By app and stage, by model and account, shadow share, ad hoc stages, fallback rate, outage days.

| Tenant (internal view only) | AI cost (K-LLM-TENANT) | Plan price | Share | Status |
|---|---|---|---|---|

### A6. Vendors and credits (FI-04)

| Vendor | Spend | Balance / credit | Runway days | Expiry | Plan headroom |
|---|---|---|---|---|---|

### A7. Unit costs (FI-05)

| Unit | Numerator | Denominator | This month | Last month | 3-month avg |
|---|---|---|---|---|---|
| per published tour | | | | | |
| per trip plan | | | | | |
| per confirmed booking | | | | | |
| per active agency | | | | | |

### A8. Budgets, alerts and hard stops (FI-06)

Alerts fired, anomalies, `shared.spend_budget` hard stops, proposed budget changes with reasons.

## Part B - Commercial close (Booking, after the first real booking)

| KPI (ID@version) | Definition | Target | Actual | Last month | Status |
|---|---|---|---|---|---|
| K-BK-CONFIRMED@1 | Cases first confirmed in the month | set at go-live | | | |
| K-BK-GMV@1 | Approved version totals at fx_rate_locked | set at go-live | | | |
| K-BK-MARGIN@1 | (GMV - supplier net) / GMV | >= pricing floor | | | |
| K-BK-CASH@1 | Verified payments received | matches bank | | | |
| K-AR-OVERDUE@1 | Overdue / open receivables | < 10 % | | | |
| K-AP-OVERDUE@1 | Overdue supplier balance | 0 | | | |

Close checklist: unverified payments, unmatched supplier bills, voided items, FX rates locked.

## Decisions needed

| # | Decision | Context | Options | Recommendation | Owner role | Needed by |
|---|---|---|---|---|---|---|

## Actions

| Action | Owner role | Due | Status |
|---|---|---|---|

## Sources

Run ids, snapshot dates, endpoints (`/admin/platform/cost?month=`, `/admin/cost-ops/forecast`), and the exported JSON path.
