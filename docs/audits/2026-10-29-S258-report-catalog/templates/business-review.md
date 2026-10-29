---
id: PLAT-03-yyyy-ww
title: Business review <period>
description: <One sentence - what was delivered, what it cost, how demand moved and which decisions wait for the business owner.>
type: report
status: draft
owner: nghiep
audience: [owner, cto, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-29
review_every_days: 90
related: [PLAT-01, FIN-02, OPS-08, APP-07]
---

# Business review <period>

<!-- Report family: executive. Register PLAT-03 in docs/README.md before first use. One template, three cadences:
- EX-01 weekly pack: id PLAT-03-yyyy-ww, window Mon 00:00 - Sun 23:59 ICT, drafted Monday 01:30 UTC, posted to the weekly report epic in Jira.
- EX-02 monthly review: id PLAT-03-yyyy-mm, drafted on business day 2, approved by business day 5.
- EX-05 quarterly review: id PLAT-03-yyyy-qn, drafted with the January/April/July/October monthly pack, approved by business day 10.
report_generate fills every number from shared.kpi_daily and the other report runs (registry docs/reports/catalog.yaml).
Never type a number by hand. The agent writes only the lines marked NARRATIVE.
Storage: S3 + shared.report_run. Commercial or tenant numbers never go into git while the root repo is public.
The Jira comment is Vietnamese and follows skill/aa-jira-update (no Linear IDs). Delete this comment. -->

> [!NOTE]
> Dev data. There are no real customers yet. Numbers show trends only until the first production month; thresholds marked (Dev) are not targets.

Period: <Mon dd/mm - Sun dd/mm ICT | YYYY-MM | YYYY-Qn>. Generated: <UTC time> by run <report_run id>.
Data as of: <snapshot day>. KPI definitions: `docs/reports/kpis.yaml` v<n>. Approved by: <role>, <date>.

## 1. Summary

NARRATIVE: three lines (weekly) or five lines (monthly, quarterly) - delivered, money, demand, risks, decisions.

## 2. How to read this report

- Status: green = on target, amber = watch, red = act now. Grey = no target yet (Dev).
- Trend compares with the previous period of the same length: up, down or flat (change under 2 %).
- Each KPI ID links to its definition. A KPI whose definition changed this period shows the new version and no trend.
- Commercial lines show `not live (Dev)` until the first real booking.

## 3. Scorecard

| KPI (ID@version) | Definition | Target | Actual | Previous | Trend | Status |
|---|---|---|---|---|---|---|
| K-DEL-SHIPPED@1 | Issues Done with live verify in the period | trend; 0 with planned work = red | | | | |
| K-COST-MTD@1 | Spend month to date / prorated budget | <= 1.0 | | | | |
| K-LLM-COST-WEEK@1 | LLM spend in the period, shadow split | <= 1.3 x 4-period average | | | | |
| K-CAT-LIVE@1 | Tours live | drop < 2 % | | | | |
| K-DEM-INQ@1 | TripPlanner inquiries sent / Booking inquiries received | trend (Dev) | | | | |
| K-REL-SEV@1 | SEV1-SEV2 incidents | 0 | | | | |
| K-PART-PAYING@1 (monthly) | Active paying partners | business owner goal | | | | |
| K-BK-CONV@1 (monthly) | Inquiry to confirmed, cohort month | set at go-live | | | | |
| K-CX-NPS@1 (monthly, after first trips) | Traveller NPS | set after first quarter | | | | |

## 4. Delivered per app

| App | Versions released | What changed for users (plain words) | Evidence |
|---|---|---|---|
| CIS | | | |
| TripPlanner | | | |
| Booking | | | |
| Partner / CRM | | | |
| Infra | | | |

## 5. Money

| Line | This period | Previous | Budget | Forecast month end | Status |
|---|---|---|---|---|---|
| acc2 (AWS) | | | 300 USD | | |
| acc3 (LLM, gross) | | | 250 USD | | |
| Vendors (Jev, DataForSEO, Geoapify, OpenAI) | | | | | |

NARRATIVE: one line per mover above 20 %, with the reason.

## 6. Demand, acquisition and commercial (monthly and quarterly)

Funnel: sessions -> trips started -> inquiries -> Booking cases -> proposals -> confirmed, with conversion per step.
Top sources (MKT-01). Commercial aggregates from FI-07 (GMV, margin, cash) or `not live (Dev)`.

## 7. Partners (monthly and quarterly)

Active, new, churned by product; MRR bridge; onboarding funnel and stuck partners (EX-07); at-risk and upsell lists (EX-03).

## 8. Customers (monthly, after the first completed trips)

Response rate, CSAT, NPS, complaints closed on time (CX-01).

## 9. Reliability, security and readiness

| Item | Count | Link |
|---|---|---|
| Incidents SEV1 / SEV2 / SEV3 | | OPS-04 records |
| SLO misses (two weeks running) | | OPS-13 |
| Security alerts past SLA | | SEC-03 |
| Open legal readiness topics | | SEC-10 |
| Reports overdue | | EX-06 |

## 10. Risks

| Risk | Likelihood | Impact | Mitigation | Owner role |
|---|---|---|---|---|

## 11. Decisions needed

| # | Decision | Context in plain words | Options | Recommendation | Owner role | Needed by |
|---|---|---|---|---|---|---|

One decision per row. Several decisions -> one clickable decision page linked here.

## 12. Next period

Top 3-5 items from `docs/backlog/README.md`, each with the expected outcome.

## 13. Quarterly only: plan, forecast and budget

Goals vs results, budget vs actual (FI-06), capacity and cost forecast (OPS-16), next-quarter roadmap, Q4: next-year budget per app.

## Sources

List each report run used (ID, period, run id) and each snapshot day.
