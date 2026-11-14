---
id: FIN-00-cost-sheet-replace-me
title: Cost sheet - <project>
description: <One sentence - the monthly running cost forecast, the unit cost and every paid item with its approval.>
type: reference
status: draft
owner: replace-me
audience: [owner, cto, pm, engineer, agent]
applies_to: [replace-me]
last_reviewed: 2026-11-14
review_every_days: 30
related: []
---

# Cost sheet - <project>

<!-- New-project playbook, phase 1 (quote at gate G1), then phase 7 (monthly review). FinOps Framework at crawl / walk:
inform (tags, one cost source), optimise (cheapest lever first), operate (monthly review, budgets). Prices from the
cloud provider's pricing pages or calculator for the real region, with the date read. No account IDs here. Delete
this comment. -->

## 1. Monthly forecast

| Item | Shape (size, count, hours) | USD per month | Source and date read |
|---|---|---|---|
| Containers | <2 small tasks, always on> | <...> | <pricing page, YYYY-MM-DD> |
| Database | <smallest instance, 20 GB> | <...> | <...> |
| Load balancer, NAT, public IPv4 | <shared or own> | <...> | <...> |
| Logs, secrets, image registry | <...> | <...> | <...> |
| LLM and paid APIs | <stage, calls per day, unit price> | <...> | <...> |
| **Total Dev** | | **<...>** | |
| **Total at first prod** | | **<...>** | |

## 2. Unit cost

<USD per tenant, per booking, per generated page, ...> = <formula from the ledger or the bill>.

## 3. Paid items and their approval

Each new paid service or feature needs its own yes after its quote; a blanket approval does not count.

| Item | Monthly cost | Quoted on | Approved by and on | Tracker link |
|---|---|---|---|---|
| <service> | <...> | <YYYY-MM-DD> | <business owner, YYYY-MM-DD> | <issue> |

## 4. Guards

| Guard | Threshold | Goes to |
|---|---|---|
| Account or app budget | <USD per month; 80 % and 100 % actual, 100 % forecast> | <e-mail, chat> |
| Anomaly alert | <impact in USD> | <...> |
| Spend cap per provider or stage | <USD per day or run; hard stop or alert> | <admin page> |

## 5. Monthly review

| Month | Forecast | Actual | Difference and cause | Decision |
|---|---|---|---|---|
| <YYYY-MM> | <...> | <...> | <...> | <...> |
