---
id: OPS-13-yyyy-ww
title: SLO and DB performance check <YYYY>-W<ww>
description: <One sentence - SLIs met or missed this week, any two-week miss, and the query or index to fix.>
type: report
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem, aa-cis-api, aa-booking, tripplanner-lambda, aa-partner]
last_reviewed: 2026-10-29
review_every_days: 30
related: [OPS-08, OPS-12, APP-08]
---

# SLO and DB performance check <YYYY>-W<ww>

<!-- Report family: reliability / SLO + DB performance. Register OPS-13 in docs/README.md before first use. Weekly C4.3 check
(OPS-13) with the job runner summary (OPS-14) and the cross-app reconciliation (DATA-02). The monthly C8 review keeps
docs/templates/capacity-review.md (OPS-08) and links the four weekly runs of the month; the quarterly forecast is OPS-16.
Probe: scheduled Infra workflow on Monday 00:43 UTC; this page is generated at 01:30 UTC.
Write the Markdown in docs/audits/<date>-S<nnn>-c43-w<ww>/ only when an SLI missed; otherwise the S3 JSON is enough.
No account ID, ARN or resource ID; statement text is fine, row values are not. Delete this comment. -->

> [!NOTE]
> Dev objectives are targets that trigger work, not paging promises (docs/architecture/data-standards/03-scaling.md C1).

Week: <Mon dd/mm - Sun dd/mm ICT>. Probe run: <UTC time, workflow run>. pg_stat_statements since: <stats_reset>.
Previous week: <link>. Generated: <UTC time>, run <id>.

## 1. Summary

NARRATIVE: SLIs met n/m; misses and whether any is the second week in a row (C1.2a).

## 2. How to read this report

- p95 from pg_stat_statements is approximated as mean + 2 x stddev (C1.1b); skewed queries overstate it.
- A miss in one week during a wave is noise; two consecutive weeks go to the tech lead with a proposed fix.
- Status: green met, amber within 20 % of objective, red missed.

## 3. SLI table (C1.2)

| App | SLI | Objective | This week | Last week | Status | Second week? |
|---|---|---|---|---|---|---|
| CIS | Tenant API reads DB time p95 | < 150 ms | | | | |
| CIS | Admin list and cost pages p95 | < 1 s | | | | |
| CIS | Job claim mean | < 20 ms | | | | |
| TripPlanner | Browse reads p95 | < 300 ms | | | | |
| TripPlanner | Assembly reads + outbox insert p95 | < 500 ms | | | | |
| Booking | API reads/writes p95 | < 100 ms | | | | |
| Booking | bk_inquiry_pull batch / inquiry lag p95 | < 2 s / < 5 min | | | | |
| All | DB error rate / too many connections | < 0.5 % / 0 | | | | |
| All | DatabaseConnections p95 | < 60 % of max (181) | | | | |

## 4. Top statements

| Role | Statement (short) | Calls | Mean ms | Approx p95 ms | Total share | Change vs last week |
|---|---|---|---|---|---|---|

Statements with calls >= 20 and mean > 200 ms: <n>. Slow log > 500 ms: <n>. Lock waits: <n>.

## 5. Job runners (OPS-14)

| App | Kind | Runs | Failed | Retries | p95 / expected | Queue age p95 (started_at - greatest(created_at, run_after)) |
|---|---|---|---|---|---|---|

## 6. Cross-app flow (DATA-02)

| Flow | Backlog | Oldest age | Unmatched | Status |
|---|---|---|---|---|

## 7. Escalations and proposed fixes

| SLI | Offending query | Proposed fix (index, rewrite, cache) | Expected effect | Owner role |
|---|---|---|---|---|

## 8. Decisions needed

| # | Decision | Context | Options | Recommendation | Owner role | Needed by |
|---|---|---|---|---|---|---|

## Sources

Probe JSON path, Performance Insights window, CloudWatch metric names, run ids.
