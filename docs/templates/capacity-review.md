---
id: OPS-08-yyyy-mm
title: Capacity review <YYYY-MM>
description: <One sentence - headroom of the shared RDS and ECS services, the C3 triggers that fired, and the decisions waiting for the tech lead.>
type: report
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem, aa-cis-api, aa-booking, tripplanner-lambda, aa-partner, aa-cis-infra]
last_reviewed: 2026-10-28
review_every_days: 30
related: [OPS-08, FIN-02, AA-838]
---

# Capacity review <YYYY-MM>

<!-- The monthly review of data standards Part C, C8 (docs/architecture/data-standards/03-scaling.md).
Save it as docs/audits/<date>-S<nnn>-capacity-review/README.md with a root PR (C8a). Claude Code drafts,
The tech lead approves. The body MAY be written in Vietnamese (audits for the tech lead, language convention N-7).
The cost half (FinOps) uses templates/cost-report.md; item (9) below links to it instead of repeating it.
Worked example and scripts: docs/audits/2026-10-28-S255-aa838-capacity/ (copy scripts/ into the new folder,
change START/END, run the probe through DB Migrate run-script for full statement text).
No account ID, ARN, resource ID, DSN or row value on this page. Delete this comment. -->

Date: <DD/MM/YYYY> (S<nnn>). Agent: <Claude Code / Kiro>. Cost: <USD, e.g. ~0 (CloudWatch GetMetricData + PI API)>.
Window: **<start> → <end> UTC (30 days)**. Previous review: <link>. Next: first session of <month> (C8a), or earlier
if a wave doubles a ledger.

Sources: CloudWatch (`scripts/gen_cw_queries*.py`, `scripts/analyze_cw.py`), Performance Insights (7 days),
`scripts/capacity_probe.py` (<ECS exec as `cis_app` | DB Migrate run-script>, run at <UTC time>, raw output
`data/probe-<date>.txt`), AA-CIS-Infra `db/check_connection_budget.py` (commit <sha>), the month's cost report.
`pg_stat_statements` accumulated since <stats_reset>.

## 1. Summary

- **Instance:** <CPU avg / hours above the T baseline, DB load, connection peak vs `max_connections`, memory min>.
  <Resize trigger fired or not → decision.>
- **Storage:** <used / allocated, growth per day (30 d and 7 d), when the `FreeStorageSpace` alarm would fire>.
- **Ledgers and retention:** <row counts, growth, retention mode per kind, date each first ages past its window>.
- **Connection budget C2.2:** <worst case vs ceiling, accepted overages and their expiry, measured peak>.
- **Slow paths / SLIs:** <SLIs missed, which role / statement>.
- **Monitoring gaps:** <alarms C4.1 requires that do not exist>.

## 2. The nine C8b items

### (1) CloudWatch RDS — 30 days

| Metric | 30 days | <sub-window, e.g. after a resize> | Threshold / note |
|---|---|---|---|
| CPU (hourly average) | | | T baseline 20 %: <n / hours> above |
| CPU (hourly max) | | | alarm > 80 % / 15′ |
| `CPUSurplusCreditsCharged` | | | trigger > ~10 USD/month |
| `FreeableMemory` (hourly min) | | | alarm < 200 MiB; trigger < 300 MB > 1 h/day × 3 days/week |
| `SwapUsage` max | | | |
| `DatabaseConnections` | max, p95, p99 | | `max_connections` <n>; alarm > <n> |
| `FreeStorageSpace` | first → last (min) | | alarm < <n> GB |
| Storage growth | GB/day | GB/day (7 d) | trigger > 1 GB/day for a week |
| Read / Write IOPS | | | gp3 baseline 3000 |
| Read / Write latency | | | alarm > 20 ms / 15′ |
| `DiskQueueDepth` max | | | alarm > 10 |
| `MaximumUsedTransactionIDs` | | | alarm 1 billion |

Performance Insights (7 days): `db.load.avg` mean / p95 / max; top wait events; load by user and by
`application_name`; top SQL. Sessions without `application_name` (C1.1a): <who>.

### (2) `pg_stat_statements` / PI top 20 per role, C1.2 SLIs

Share of total execution time per role:

| Role | Statements | Calls | Total | Share | Mean |
|---|---:|---:|---:|---:|---:|

Top statements by total and by mean (`[pgss_total]`, `[pgss_mean]`, `[pgss_role_*]` in the data file): <short list>.
Statements with `calls ≥ 20` and mean > 200 ms: <n>. `pg_stat_statements` fill: <stored / max, dealloc>.
p95 is approximated as `mean + 2 × stddev` (C1.1b); say so where a skewed distribution inflates it.

| SLI C1.2 | Dev objective | Measured | Result |
|---|---|---|---|
| CIS tenant reads p95 | < 150 ms | | |
| CIS admin list / cost pages p95 | < 1 s | | |
| CIS job claim mean | < 20 ms | | |
| TripPlanner browse (`catalog.v_*`) p95 | < 300 ms | | |
| TripPlanner assembly + outbox p95 | < 500 ms | | |
| Booking API p95 | < 100 ms | | |
| Connection saturation p95 | < 60 % `max_connections`, each role < 80 % of its limit | | |

### (3) Tables and indexes

Total DB size; size per schema; top 20 tables by total size (heap / index / toast, rows, 30-day growth); dead-tuple
ratios over 20 % (C5.2b); unused indexes (C5.2d, count and size, largest few); cache hit ratio (measure the delta
between two probes, not the cumulative figure); temp files and bytes.

| Table | ~rows | Size | Note |
|---|---:|---:|---|

### (4) Ledgers vs retention (C5.4 / DM-7)

| Ledger | Rows | Rows 7 d / 30 d | Oldest | Window (code) | Retention mode (dry_run / live / held) and last run |
|---|---:|---|---|---|---|

Forecast: date each ledger passes 1 M rows and its steady-state size once the window is full.

### (5) Lambda (TripPlanner)

| Function | Reserved | Invocations | Throttles | Errors | Concurrency max | Duration p95 |
|---|---:|---:|---:|---:|---:|---|

### (6) Job backlog and duration per owner

Oldest due queued job, overdue running jobs, queue-age alarms per owner (`shared.job`, `booking.job`, `crm.job`);
duration per kind (p50 / p95 / failures) for the 30 days.

### (7) C2.2 budget recomputed from live Terraform

`python3 db/check_connection_budget.py` (AA-CIS-Infra `main` <sha>):

| Pool | Role | max_size × processes | Worst case |
|---|---|---|---:|
| **Total** | | | **<n> / ceiling <n>** |

Per role: <sum / limit>. Accepted overages and their expiry: <list>. Measured: <instance peak, per-role peak>.
If any value differs from the C2.2 table in `03-scaling.md`, fix the table in the same root PR (C8c).

### (8) C3 triggers — measured, fired or not

| C3 row | Trigger | Measured | Result |
|---|---|---|---|
| t4g.small → t4g.medium | CPU / credits / memory / C2.2 total | | |
| t4g.medium → m7g.large | > 5 primary-path statements with mean > 200 ms | | |
| m7g → r7g | cache hit < 99 % for a week; `FreeableMemory` < 10 % RAM | | |
| Storage | > 80 % of `max_allocated_storage`, or > 1 GB/day for a week | | |
| Retention | log table **without a retention job kind** > 1 M rows, or `FreeStorageSpace` < 10 GB before its retention exists (a ledger with a retention kind: Partitioning row) | | |
| RDS Proxy | Lambda need > 20; `DatabaseConnections` p95 > 60 % for a week | | |
| Materialized catalog read model | a `catalog.*` view p95 > 500 ms | | |
| Read replica | reads > 30 % of primary CPU, or CPU > 60 % sustained | | |
| Partitioning | table > 10 M rows / > 5 GB; retention DELETE > 5′; dead > 20 % | | |
| App split | DB > 200 GB; conn p95 > 70 %; Booking p95 ×2 during waves twice a month | | |

### (9) RDS cost vs budget

<RDS line this month and last, budget of the `shared` app, credits charged; link to the month's cost report.>

### ECS services

| Service | Task size | Desired / autoscale | CPU avg | CPU hourly max | Mem avg | Mem max |
|---|---|---|---:|---:|---:|---:|

## 3. Risks (ranked)

1. <risk — evidence — consequence>

## 4. Decision list (C8c) — proposed, waiting for the tech lead

| # | Proposed decision | Type (no action / tune / scale / investigate / docs) | C3 row or rule | Who / size / cost |
|---|---|---|---|---|

Cheaper levers first (C3b): query/index → retention → pool budget → materialized read model → resize → proxy →
replica → split. Ask the tech lead before creating any Linear issue.

## 5. Weekly check of this week (C4.3)

<One "C4.3 week W<nn>" paragraph: top statements by total and mean per role, statements with mean > 200 ms, each C1.2
SLI met / missed (first or second consecutive miss, C1.2a), locks and long transactions, slow log > 500 ms read or
not. A second consecutive miss goes to the tech lead with the statement text and a proposed fix.>

## 6. How to reproduce / steps for the orchestrator

- Probe: <how it was run, which login, PROBE_TOP (50 when a `pg_stat_statements_reset()` is planned, C4.3a)>.
- CloudWatch / PI commands (single-line AWS CLI only).
- Read-only checks left for the orchestrator session: <scripts under .tmp-session/S<nnn>/>.

## 7. Appendix — probe output

Raw output: `data/probe-<date>.txt` (checked before commit: no DSN, password, token, account ID, ARN, UUID or string
literal).
