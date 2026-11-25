---
id: FIN-02-2026-11-acc2-history
title: acc2 Cost Explorer history, November 2025 to November 2026 (export before the payer change)
description: "Read-only export of 13 months of acc2 Cost Explorer data (monthly by service, by App tag, by Component tag, by record type) taken before acc2 moves to the company organization by Billing Transfer, so the history does not depend on which payer view stays available."
type: report
status: active
owner: nghiep
audience: [engineer, cto, pm]
applies_to: [ecosystem]
last_reviewed: 2026-11-25
related: [FIN-02, FIN-02-2026-10-prelim, AA-1004]
---

# acc2 cost history, 2025-11 to 2026-11

- **Why:** AA-1004 pre-check "Cost Explorer export" before acc2 (the nonprod infrastructure account) leaves the
  reseller's organization and joins the company organization by Billing Transfer. After a payer change the history
  is read from a different management account; this export keeps the numbers in the repo whatever that view shows.
- **What:** session S294, 2026-11-25, Claude Code, read only. Four `aws ce get-cost-and-usage` requests on acc2
  (profile `aa365-admin`, Cost Explorer endpoint in `us-east-1`), `MONTHLY`, `2025-11-01` to `2026-11-25` (end
  exclusive), metrics `UnblendedCost` and `NetUnblendedCost`, grouped by `SERVICE`, tag `App`, tag `Component` and
  `RECORD_TYPE`. Cost of the export: 4 x 0.01 USD = **0.04 USD**.
- **How to repeat:** [`scripts/fetch_ce.sh`](scripts/fetch_ce.sh) (single-line CLI calls, raw JSON into a scratch
  folder outside the repo), then [`scripts/to_csv.py`](scripts/to_csv.py) (stdlib, local files only) writes the
  CSVs. The raw JSON is not committed; the CSVs hold no account number (the converter refuses a twelve-digit value).
- **November 2026 is open:** 1 to 24 November, flagged `estimated=true` by Cost Explorer. Cost Explorer revises a
  day for about 48 hours, so a final November figure needs a pull after 2026-12-03.

## Files

| File | Rows | Content |
|---|---:|---|
| [`data/acc2-monthly-totals.csv`](data/acc2-monthly-totals.csv) | 13 | Month total (sum of the service rows) |
| [`data/acc2-monthly-by-service.csv`](data/acc2-monthly-by-service.csv) | 164 | Month x service |
| [`data/acc2-monthly-by-app-tag.csv`](data/acc2-monthly-by-app-tag.csv) | 23 | Month x `App` tag value; `(untagged)` = no tag |
| [`data/acc2-monthly-by-component-tag.csv`](data/acc2-monthly-by-component-tag.csv) | 8 | Month x `Component` tag value |
| [`data/acc2-monthly-by-record-type.csv`](data/acc2-monthly-by-record-type.csv) | 15 | Month x record type (Usage, Tax, Other) |

Columns: `month` (YYYY-MM), the group, `estimated` (Cost Explorer's flag), `unblended_usd`, `net_unblended_usd`.

## Totals per month (USD, Unblended)

| Month | Total | Note |
|---|---:|---|
| 2025-11 to 2026-03 | 0.00 | No usage (no groups returned) |
| 2026-04 to 2026-06 | 0.00 | A few S3, Glue, Secrets Manager, KMS rows below 0.01 USD |
| 2026-07 | 105.68 | Infrastructure moved onto acc2 during July |
| 2026-08 | 140.22 | |
| 2026-09 | 134.96 | |
| 2026-10 | 213.87 | Booking, CRM and the separate worker service added; the S248 forecast for October was 187.75 |
| 2026-11 (1 to 24) | 218.34 | Open month, estimated; about 9.10 USD a day so far |
| **13 months** | **813.07** | |

`NetUnblendedCost` equals `UnblendedCost` in every month: acc2 has no credit rows. Tax rows are 0.00 (the reseller
invoices tax outside Cost Explorer). The only `Other` row is 3.00 USD in November, the Amazon Registrar domain renewal.
August and September match the S248 cost report to the cent.

## Top services (13 months, USD)

| Service | Total | Share | Jul | Aug | Sep | Oct | Nov (1 to 24) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Elastic Container Service | 170.77 | 21.0 % | 16.33 | 21.54 | 21.13 | 54.92 | 56.85 |
| Elastic Load Balancing | 170.19 | 20.9 % | 28.37 | 37.61 | 36.41 | 37.82 | 29.98 |
| Relational Database Service | 123.11 | 15.1 % | 16.41 | 20.82 | 20.39 | 30.80 | 34.69 |
| ElastiCache | 71.07 | 8.7 % | 12.96 | 16.37 | 15.84 | 15.77 | 10.14 |
| WAF | 57.71 | 7.1 % | 7.38 | 9.37 | 9.46 | 12.09 | 19.41 |
| CloudWatch | 52.58 | 6.5 % | 5.26 | 6.92 | 7.86 | 19.90 | 12.63 |
| Virtual Private Cloud | 50.62 | 6.2 % | 8.81 | 11.17 | 10.81 | 11.17 | 8.65 |
| Secrets Manager | 39.69 | 4.9 % | 2.66 | 3.61 | 4.42 | 11.72 | 17.28 |
| EC2 - Other | 20.03 | 2.5 % | 3.31 | 3.21 | 3.44 | 7.37 | 2.71 |
| EC2 - Compute | 17.66 | 2.2 % | 2.91 | 3.72 | 3.98 | 4.06 | 2.99 |

Everything else is below 1 % each (Bedrock 6.55, API Gateway 5.98, ECR 5.73, S3 4.62, KMS 4.28, then CloudFront,
Route 53, Cognito, Registrar, Cost Explorer, Location Service, SES, Lambda and a few cents of others). The four
fastest growers from September to November are ECS (worker, Booking and CRM services), Secrets Manager (one secret
per app since the per-app secrets work), WAF and KMS.

## By `App` tag

The `App` tag counts from 15 to 16 October 2026 (Cost Explorer does not re-tag older usage), so July to September
and half of October are all `(untagged)`.

| App | Oct (from about 16/10) | Nov (1 to 24) |
|---|---:|---:|
| shared | 55.21 | 83.62 |
| cis | 36.01 | 55.79 |
| crm | 6.63 | 19.93 |
| booking | 6.11 | 11.31 |
| identity | 2.46 | 8.20 |
| tripplanner | 0.79 | 5.24 |
| ecosystem | 0.15 | 0.36 |
| platform | 0.01 | 0.00 |
| (untagged) | 106.51 | 33.90 (15.5 %) |

`identity`, `platform` and `ecosystem` are values outside the DM-10.1 list (finding F6 of the S248 report, still open).

## By `Component` tag

Every month is `(untagged)`: the Terraform code sets `Component` on resources, but it is not an activated cost
allocation tag. A member account cannot activate tags; the payer's management account does. After the Billing
Transfer, the company management account can activate `Component` (and confirm `App`); from then on both count, with
no history before the activation date.
