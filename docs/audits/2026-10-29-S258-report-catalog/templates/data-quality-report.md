---
id: APP-14-yyyy-ww
title: Data quality report <period>
description: <One sentence - integrity probes passed or failed, stale or drifting data, and the fix needed.>
type: report
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-29
review_every_days: 90
related: [APP-04, OPS-11, PLAT-01]
---

# Data quality report <period>

<!-- Report family: data quality. Register APP-14 in docs/README.md before first use. Covers DATA-01 (nightly probes, shown
daily in OPS-12 and weekly here), DATA-02 (cross-app reconciliation), DATA-03 (schema and contract changes), DATA-04
(retention, monthly), TP-03 (inquiry handoff) and CIS-02 (place quality, monthly). Table and column names only from
docs/architecture/db-schema-reference.md. Counts only: never paste row values or personal data. Delete this comment. -->

> [!NOTE]
> Dev data. Completeness thresholds apply to the catalog now; transactional checks become meaningful with real traffic.

Period: <ISO week | month>. Generated: <UTC time>, run <id>. Schema reference verified: <timestamp in its header>.

## 1. Summary

NARRATIVE: probes passed n/m; the dimension that failed (freshness, completeness, consistency, validity) and the fix.

## 2. How to read this report

- Freshness: data updated within its window. Completeness: required fields present. Consistency: the same fact agrees across apps. Validity: values in allowed ranges.
- A failed nightly probe is shown once per night; three nights in a row is red.
- Reconciliation gaps are counted per closed ICT day; outbox tables have no processed flag, so gaps are matched by idempotency_key and feed position.

## 3. KPIs

| KPI (ID@version) | Dimension | Definition | Target | Actual | Previous | Status |
|---|---|---|---|---|---|---|
| K-DATA-PROBES@1 | all | Nightly probes passed / run | all | | | |
| K-DATA-STALE@1 | freshness | Downstream rows aged > 24 h | 0 | | | |
| K-DATA-LIVENESS@1 | consistency | Tour liveness gate violations | 0 | | | |
| K-DATA-DRIFT@1 | validity | Unexplained schema drift | 0 | | | |
| K-TP-HANDOFFGAP@1 | consistency | Inquiries in the TripPlanner outbox with no Booking inbox row | 0 | | | |
| K-REC-UNMATCHED@1 | consistency | Events without receipt after 24 h | 0 | | | |
| K-REC-FEEDLAG@1 | freshness | Booking feed position not yet read by CRM | 0 after 15 min | | | |
| K-CAT-COVER@1 | completeness | Tours with a cover photo | >= 95 % | | | |
| K-RET-OVERDUE@1 (monthly) | validity | Ledger rows past retention window | 0 | | | |

## 4. Nightly probes (UTC run times)

| Probe (workflow) | Runs at | Nights run | Failed | Last failure | Cause | Follow-up |
|---|---|---|---|---|---|---|
| migration-copy-guard | 02:17 | | | | | |
| contract-copy-guard | 02:29 | | | | | |
| connection-budget | 02:43 | | | | | |
| db-schema-dump | 03:43 | | | | | |
| db-isolation-probe | 04:13 | | | | | |
| crm-key-policy-diff | 04:29 | | | | | |
| db-tour-liveness-gate | 04:43 | | | | | |
| db-freshness-probe | 05:13 | | | | | |

## 5. Freshness by layer

| Layer | Stale rows | Aged > 24 h | Oldest | Status |
|---|---|---|---|---|

## 6. Cross-app reconciliation

| Flow | Sent | Received | Gap | Oldest unmatched | Status |
|---|---|---|---|---|---|
| TripPlanner inquiry -> Booking inbox | | | | | |
| Booking supply feed -> CRM | | | | | |
| CIS tour lifecycle -> Booking pull | | | | | |

## 7. Schema and contract changes

Migrations applied per owner, schema-reference PRs, contract changes and their consumers.

## 8. Monthly: places, retention and growth

| Ledger | Rows | Growth / day | Window | Rows past window |
|---|---|---|---|---|

Place quality (CIS-02): sample accuracy, outliers present and observed this month, geocode spend.

## 9. Decisions needed

| # | Decision | Context | Options | Recommendation | Owner role | Needed by |
|---|---|---|---|---|---|---|

## Sources

Workflow run ids, probe JSON paths, views read, schema reference timestamp.
