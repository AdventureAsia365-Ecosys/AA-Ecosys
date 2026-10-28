---
id: OPS-10-deploy-gate
title: Override a deploy or migration gate
description: When and how the tech lead lets a CIS, Booking or Partner deploy through while a rerun wave is open or a deploy-blocking job runs, or a DB Migrate apply while jobs are busy.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-api, aa-cis-worker, aa-booking-api, aa-partner, aa-cis-infra]
last_reviewed: 2026-10-28
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

**Only the tech lead decides an override** (session-workflow rule). Agents never override to "go faster". A deploy
override restarts containers while a deploy-blocking job works. That job then starts again from the beginning, or,
for a `data_erasure` apply, is refused and needs a new DRY RUN and approval. A DB Migrate override runs DDL next to
busy jobs.

## When to use

- The deploy **is the fix** for a SEV1, and a deploy-blocking job is stuck or cannot finish, or the gate cannot
  answer (for example the API is down; the CIS guard fails closed and blocks).
- A migration must go out and a long, safe-to-retry job is running.
- Not for: a normal busy queue in front of DB Migrate. Wait for the jobs, or cancel the stuck one first
  ([queue stuck](../playbooks/queue-stuck.md)). Since AA-993 G5 a busy queue no longer blocks an app deploy.

## The gates

| Gate | Asks | Exempt kinds | Override input |
|---|---|---|---|
| CIS Deploy Dev (`deploy-dev.yml`, job "Pre-deploy job guard") | `GET https://api-cis.lumiguides.it.com/admin/job-runner/deploy-gate` (admin secret). Since AA-993 G5: blocks only while a rerun wave is open or a `deploy_blocking` kind runs or is queued due within 15 min. `GET /admin/job-runner/summary` lists the flag per kind; on 2026-10-28: `data_erasure`, `s1_batch_ingest`, `writing_memory_r2`, `writing_memory_shadow`. Other queued or running jobs are drained and re-claimed | not needed (other queued rows no longer block); `deploy_gate_exempt` only trims the info counts | `override_running_jobs` (workflow_dispatch) |
| Booking Deploy Dev (`deploy-dev.yml`) | `GET https://api-booking.lumiguides.it.com/booking/ops/deploy-gate` with the run's GitHub OIDC token; skipped when the service runs 0 tasks. Since AA-993 G5: blocks only while a retention job (`bk_retention_job`, `bk_retention_inbox_redact`) runs or is queued due within 15 min | info counts leave out `bk_inquiry_pull`, `bk_noop_sleep` | `override_running_jobs` (workflow_dispatch) |
| Partner Deploy Dev (`deploy-dev.yml`) | `GET /crm/ci/deploy-gate` with the run's GitHub OIDC token; passes when the service runs 0 tasks. Since AA-993 G4b no CRM kind is deploy-blocking (`DEPLOY_BLOCKING_KINDS` is empty), so the gate passes unless it cannot answer or a task is starting | info counts leave out `crm_heartbeat`, `crm_membership_pull`, `crm_booking_sync` | `override_running_jobs` (workflow_dispatch) |
| DB Migrate (`db-migrate.yml`, apply and writing run-script) | every owner job table and open `shared.rerun_wave`, 3 checks 20 s apart | `owners.yaml` idle-exempt kinds | `override_busy_jobs` (one line, at most 200 characters) |

All of them fail closed: an unreachable gate or an unreadable answer blocks. The deploy gates name the reason in
`blocked_by` (the `deploy-gate: {...}` log line).

## Preconditions

- The tech lead has decided, and the reason is written in the Linear issue (incident issue for a SEV1).
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

   Booking or Partner: the same with `--repo AdventureAsia365-Ecosys/AA-Booking` or
   `--repo AdventureAsia365-Ecosys/AA-Partner`. DB Migrate: add
   `-f override_busy_jobs="<reason>"` to the apply or run-script dispatch ([DB Migrate](db-migrate.md)).
   Expected: the guard step shows `::warning::Deploy guard OVERRIDDEN (...) Reason: ...` and the deploy continues.
   Verify: the rollout and live checks of [rollback-cis](rollback-cis.md) step 7 (or Booking's `/booking/health`).
   Rollback: none for the override itself; roll the app back with the rollback runbook if the deploy is bad.

3. Check the interrupted jobs (CIS). On a deploy the old worker drains: running jobs get its stop timeout, the rest
   are released back to the queue, and the new revision re-claims them. A release during a deploy does not count
   against the job (AA-993). `GET /admin/job-runner/released?since=<iso-time>` lists them; `<iso-time>` is the
   start of the deploy. A `deploy_blocking` job has no checkpoint, so a re-claimed one starts again from the
   beginning (`s1_batch_ingest` would ingest every tour again). A re-claimed `data_erasure` apply refuses its used
   approval: run a new DRY RUN and approve it. Cancel a job on the Jobs page if a second run is wrong, or let it
   re-run on purpose, and note which in the issue.
   A DB Migrate override restarts nothing: a lock conflict with a busy job fails the migration after its
   `lock_timeout` (5 s).
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
