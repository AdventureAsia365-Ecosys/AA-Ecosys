---
id: SEC-04-retention
title: Retention and erasure run log
description: One row per retention, redaction or erasure run on AA-Ecosys data, with window, rows, job id and the DRY RUN approver; the windows themselves live in the data standards retention table.
type: reference
status: draft
owner: nghiep
audience: [cio, engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-21
review_every_days: 90
related: [SEC-04, SEC-04-dsar, AA-825, AA-839, AA-861]
---

# Retention and erasure run log

This page records **runs**, not rules. The windows are set in the
[§7 retention table](../architecture/data-standards/02-data-management.md#7-retention-and-archival) of the data
standards, which is the registry (DM-7.1). A window change is a DM-7.5 decision (the tech lead approves) and lands there, not
here. Part of the [compliance and privacy register](register.md).

## Summary on 2026-10-21

- **No retention, redaction or erasure run has changed a row in a table holding personal data yet (2026-10-21).** The
  only run on such a table (`booking.inbox_events`) was a DRY RUN with 0 candidates, and no traveller or tenant erasure
  has run (the [DSAR and erasure runbook](dsar-erasure-runbook.md) is untested).
- The CIS retention kinds (AA-825, AA-CIS-App `services/jobs/retention_job.py`) cover non-personal log tables
  (`llm_call_log`, `tenant_api_usage`, `job`, `decision_log`, the cost snapshot). Their runs are logged in `shared.job`;
  the first live runs are below. Whether the daily schedule has run live since is `[to be confirmed]` (read `shared.job`).

What is built and what is not:

| Window (§7) | State on 2026-10-21 | Evidence |
|---|---|---|
| `booking.inbox_events` payload PII, 90 days (DM-6.6) | Job kind `bk_retention_inbox_redact` deployed; DRY RUN only, 0 candidates; no real run yet | AA-Booking `backend/app/retention/policy.py:9-15`, `:83-90`; run below |
| `tripplanner.outbox` payload PII, 90 days (DM-6.6) | **Not built**: TripPlanner has no job table yet (AA-861, blocked on `tripplanner.job`) | Linear AA-825 comment of 2026-10-16 |
| `booking.job` succeeded 30 days / failed 90 days | Job kind `bk_retention_job` deployed; DRY RUN only, 0 candidates | run below |
| `shared.llm_call_log` 180 days, `shared.tenant_api_usage` 90 days, `shared.job`, `shared.decision_log`, `shared.cost_explorer_snapshot` | CIS retention kinds deployed with a daily schedule (EventBridge `aa-cis-dev-retention-daily`); scheduled runs stay DRY RUN until a live run of the same window exists; Dev live runs used the Dev-only override | Linear AA-825 comment of 2026-10-16; `docs/audits/2026-10-16-S239-in-progress-audit/aa825-*` |
| Log tables follow-up and the real Booking run | AA-825 was reopened on 2026-10-19: it waits for one real Booking run | Linear AA-825 comment of 2026-10-19 |
| Every row marked "proposed" in §7 | Nothing is deleted until the data owner and the tech lead approve the window | §7 note |

## Runs

| Date (UTC) | Table | Window | Mode | Rows | Job id | DRY RUN approver | Evidence |
|---|---|---|---|---|---|---|---|
| 2026-10-16 | `shared.cost_explorer_snapshot` (superseded intra-day rows) | latest snapshot per day kept | live | 5,991 deleted | `5fb98b63-efb8-4e6a-9d78-d19b9ed1f34e` | tech lead (S239, `aa825-override/README.md:9`) | [`aa825-dryrun/05_live_cost_explorer.json`](../audits/2026-10-16-S239-in-progress-audit/aa825-dryrun/05_live_cost_explorer.json) |
| 2026-10-16 | `booking.inbox_events` payload | 90 days | DRY RUN | 0 candidates | `d71f24cb-a963-41c5-abde-dbc12763593f` | — (DRY RUN) | [`aa825-booking/03_result_bk_retention_inbox_redact.json`](../audits/2026-10-16-S239-in-progress-audit/aa825-booking/03_result_bk_retention_inbox_redact.json) |
| 2026-10-16 | `booking.job` | 30 / 90 days | DRY RUN | 0 candidates | `8f8d34e5-7ae4-4b56-9853-970a3eb999c0` | — (DRY RUN) | [`aa825-booking/03_result_bk_retention_job.json`](../audits/2026-10-16-S239-in-progress-audit/aa825-booking/03_result_bk_retention_job.json) |
| 2026-10-16 | `shared.llm_call_log` | Dev override, cutoff 2026-09-18, `max_rows` 200 | live | 200 deleted, 200 archived to S3 | `a309a2c4-9602-4711-8c51-218fb89765d1` | tech lead (S239, Dev override, `aa825-override/README.md:9`) | [`aa825-override/12_live_runs.json`](../audits/2026-10-16-S239-in-progress-audit/aa825-override/12_live_runs.json) |
| 2026-10-16 | `shared.tenant_api_usage` | Dev override, cutoff 2026-09-17, `max_rows` 200 | live | 200 deleted, 200 archived to S3 | `0609cb2b-d87c-4cee-9570-9be1b3edba15` | tech lead (S239, Dev override, `aa825-override/README.md:9`) | [`aa825-override/12_live_runs.json`](../audits/2026-10-16-S239-in-progress-audit/aa825-override/12_live_runs.json) |

The DRY RUN counts that preceded the two override runs (2,676 and 260 candidates) are in
[`aa825-override/11_dry_runs.json`](../audits/2026-10-16-S239-in-progress-audit/aa825-override/11_dry_runs.json).

How to add a row: after each first run of a kind, each first run after a window change, and each erasure, add the
date, table, window, mode, row count from the job result, the job id, who approved the DRY RUN (DM-7.2) and a link to
the evidence folder `docs/audits/<date>-S<nnn>-<slug>/`. Scheduled runs that repeat an approved window need no row.

## Test data kept for the erasure test

The DM-6.5 consent check of 2026-10-20 left three linked test rows in place for the first erasure test (AA-839).
Do not delete them by hand; the [DSAR and erasure runbook](dsar-erasure-runbook.md) test removes them.

| Table | Id prefix |
|---|---|
| `tripplanner.customers` | `08c1831a…` |
| `booking.inbox_events` | `a939e12a…` |
| `booking.customers` | `b7f8649d…` |

Source: AA-886 Linear comment of 2026-10-20 (DB Migrate run-script run 39363696312).
