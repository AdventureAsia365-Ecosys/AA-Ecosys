---
id: FIN-02-yyyy-mm
title: Cost and capacity review <YYYY-MM>
description: <One sentence - month total vs last month and the one decision needed, if any.>
type: report
status: draft
owner: nghiep
audience: [owner, engineer, cto, cio, pm]
applies_to: [ecosystem]
last_reviewed: 2026-10-19
related: [FIN-01, OPS-08, AA-896, AA-838]
---

# Cost and capacity review <YYYY-MM>

<!-- One monthly report = the C8 capacity review + the FinOps cost report (reconciliation K-05).
Save it as docs/audits/<date>-S<nnn>-capacity-review/README.md with a root PR (C8a). Claude Code drafts,
The tech lead approves.
Sources (DM-10.4, no new Cost Explorer script): shared.cost_explorer_snapshot (daily per account and service;
add the App tag group-by in the existing CIS client), shared.llm_call_log (by stage, role, app), CloudWatch.
Tags: App and Environment (DM-10.1); untagged spend is a finding. Delete this comment. -->

## Tóm tắt cho chủ doanh nghiệp (VI)

<Năm dòng: tổng tháng (USD), so với tháng trước (+/- %), lý do chính, ngân sách còn bao nhiêu, có cần chị quyết gì không.>

## Totals by account

| Account | This month (USD) | Last month (USD) | Change | Note |
|---|---|---|---|---|
| acc2 (infra) | | | | |
| acc3 (LLM satellite) | | | | |

## By app (tag `App`)

| App | This month | Last month | Change | Note |
|---|---|---|---|---|
| cis | | | | |
| booking | | | | |
| tripplanner | | | | |
| shared | | | | |
| untagged | | | | <finding if > 0> |

## Top 5 services and changes over 20 %

| Service | This month | Last month | Change | Reason |
|---|---|---|---|---|

## LLM spend

<From shared.llm_call_log: by stage and role, by account; ad-hoc stages (adhoc_<issue>) listed separately.>

## Unit costs

| Unit | Value | Last month |
|---|---|---|
| USD per published tour | | |
| USD LLM per tour | | |
| USD per trip plan | | |
| USD per booking | | |

## Budgets and anomalies

| Budget / monitor | Limit | Actual | Alerts fired |
|---|---|---|---|

## Capacity (C8b checklist)

1. CloudWatch 30-day CPU, FreeableMemory, DatabaseConnections p95/max, storage and growth, IOPS, credits.
2. Top queries per role (Performance Insights / pg_stat_statements) with C1.2 SLIs.
3. Top 20 tables and indexes by size and growth, dead tuples, unused indexes.
4. Ledger row counts vs C5.4 retention.
5. Lambda concurrency peaks and throttles.
6. Job backlog and duration per owner.
7. C2.2 connection budget recomputed from live Terraform values.
8. Every C3 trigger with its measured value (fired / not fired).
9. RDS cost line vs budget.

## Actions

| Finding | Action | Issue | Cost impact |
|---|---|---|---|
