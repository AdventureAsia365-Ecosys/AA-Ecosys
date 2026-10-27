---
id: OPS-10-deploy-gate
title: Override a deploy or migration gate
description: When and how Nghiệp lets a CIS, Booking or Partner deploy through while a wave is open or a deploy-blocking job runs, or a DB Migrate apply while jobs are busy.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-api, aa-cis-worker, aa-booking-api, aa-cis-infra]
last_reviewed: 2026-10-19
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [OPS-10, OPS-02-cis, OPS-05-db-migrate, OPS-04-queue-stuck, AA-725, AA-751, AA-868]
---

# Override a deploy or migration gate

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> The gates themselves are proven (CIS S215, Booking S241: a seeded job blocked the deploy). No override run is on
> record yet.
<!-- callout break -->
> [!CAUTION]
> Only Nghiệp decides an override (session-workflow rule). An override restarts containers or runs DDL while a job
> works; that job is interrupted and retried, or left half done. Agents never override to "go faster".

## When to use

- The deploy **is the fix** for a SEV1 and a job is stuck or cannot finish (for example the API is down, so the gate
  cannot answer; the CIS guard fails closed and blocks).
- A migration must go out and a long, safe-to-retry job is running.
- Not for: a normal busy queue. Wait for the jobs, or cancel the stuck one first ([queue stuck](../playbooks/queue-stuck.md)).

## The three gates

| Gate | Asks | Exempt kinds | Override input |
|---|---|---|---|
| CIS Deploy Dev (`deploy-dev.yml`, job "Pre-deploy job guard") | `GET https://api-cis.lumiguides.it.com/admin/job-runner/deploy-gate` (admin secret). Since AA-993 G5: blocks only while a rerun wave is open or a `deploy_blocking` kind runs (`data_erasure`, `s1_batch_ingest`); other queued / running jobs are drained and re-claimed | not needed (queued rows no longer block); `deploy_gate_exempt` only trims the info counts | `override_running_jobs` (workflow_dispatch) |
| Booking Deploy Dev (`deploy-dev.yml`) | `GET https://api-booking.lumiguides.it.com/booking/ops/deploy-gate` with the run's GitHub OIDC token; skipped when the service runs 0 tasks. Since AA-993 G5: blocks only while a retention job (`bk_retention_job`, `bk_retention_inbox_redact`) runs | info counts leave out `bk_inquiry_pull`, `bk_noop_sleep` | `override_running_jobs` (workflow_dispatch) |
| Partner Deploy Dev (`deploy-dev.yml`) | `GET /crm/ci/deploy-gate` with the run's GitHub OIDC token. Since AA-993 G5: blocks only while `crm_dispatch` runs (until the G4b send marker) | info counts leave out the Recurring kinds | `override_running_jobs` (workflow_dispatch) |
| DB Migrate (`db-migrate.yml`, apply and writing run-script) | every owner job table and open `shared.rerun_wave`, 3 checks 20 s apart | `owners.yaml` idle-exempt kinds | `override_busy_jobs` (one line, at most 200 characters) |

All of them fail closed: an unreachable gate or an unreadable answer blocks. The deploy gates name the reason in
`blocked_by` (the `deploy-gate: {...}` log line).

## Preconditions

- Nghiệp has decided, and the reason is written in the Linear issue (incident issue for a SEV1).
- You know which jobs will be interrupted (step 1).
- Cost: 0 USD.

## Steps

1. See what is running. CIS: admin UI **Jobs** page, or from a CIS ECS exec script
   (`SELECT kind, status, count(*) FROM shared.job WHERE status IN ('queued','running') GROUP BY 1,2`). Booking:
   the same on `booking.job` through a reviewed read-only `run-script`. Or read the gate run's log line
   `deploy-gate: {...}`.
   Expected: the kinds and counts that block.
   Rollback: none - read-only.

2. Dispatch with the reason. CIS:

   ```bash
   gh workflow run deploy-dev.yml --repo AdventureAsia365-Ecosys/AA-CIS-App --ref main -f override_running_jobs="SEV1 <incident issue>: <why the deploy cannot wait>" # WRITE
   ```

   Booking: the same with `--repo AdventureAsia365-Ecosys/AA-Booking`. DB Migrate: add
   `-f override_busy_jobs="<reason>"` to the apply or run-script dispatch ([DB Migrate](db-migrate.md)).
   Expected: the guard step shows `::warning::Deploy guard OVERRIDDEN (...) Reason: ...` and the deploy continues.
   Verify: the rollout and live checks of [rollback-cis](rollback-cis.md) step 7 (or Booking's `/booking/health`).
   Rollback: none for the override itself; roll the app back with the rollback runbook if the deploy is bad.

3. Check the interrupted jobs. A running row whose worker was replaced is reclaimed after its lease expires and
   retried while it has attempts left; a kind with `max_attempts=1` (`s1_rewrite`, `s1_batch_ingest`) ends
   `failed`. Re-queue on purpose from the Jobs page (**Retry**) or leave it failed.
   Expected: no row stays `running` past twice its kind's expected time (`aa-cis-dev-jobs-overdue-running` stays OK).

## Verify the result

- The deploy or apply finished, the service is healthy, and every interrupted job is either finished, retried or
  consciously left failed with a note in the issue.

## Roll back or abort

- Cancel the dispatched run (`gh run cancel <id> -R <repo>`) before the deploy step starts if the reason no longer holds.

## Escalation

- Record the override (who, why, which jobs) in the session log and the issue. [Incident response](../incident-response.md).

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| - | - | - | - | not run yet (gates without override: S215, S241) |
