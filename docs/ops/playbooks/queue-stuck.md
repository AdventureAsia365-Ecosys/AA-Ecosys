---
id: OPS-04-queue-stuck
title: Job queue stuck
description: Diagnose a starved or stuck job queue in CIS shared.job, Booking booking.job or Partner CRM crm.job, and cancel or retry jobs safely.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-worker, aa-cis-api, aa-booking-api, aa-partner]
last_reviewed: 2026-10-28
review_every_days: 90
related: [OPS-04, APP-09, OPS-10-deploy-gate, OPS-04-llm-cost-spike, AA-650, AA-687, AA-751]
---

# Job queue stuck

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> Written from the alarm definitions and the job-runner code; re-checked against them on 2026-10-28.

## Triggers

Each job owner has the same three alarms. `<prefix>` is `aa-cis-dev` (CIS, `shared.job`), `aa-booking-dev`
(Booking, `booking.job`) or `aa-crm-dev` (Partner CRM, `crm.job`).

| Alarm | Means |
|---|---|
| `<prefix>-jobs-queue-age` | a due queued job has waited more than 15 minutes (no live worker, an unregistered kind, or a free slot that does not claim it) |
| `<prefix>-jobs-overdue-running` | a running job has run longer than twice its kind's expected time |
| `<prefix>-jobs-sampling-stopped` | the sampler that feeds the two alarms above is silent for 45 minutes; expected while the service is scaled to 0 or its worker is off |

Also: a deploy blocked by the [deploy gate](../runbooks/deploy-gate-override.md), or a UI that waits forever. Since
AA-993 G5 a busy queue no longer blocks a deploy: only an open rerun wave or a deploy-blocking kind does.

## Facts

- CIS: one table `shared.job`, worker service `aa-cis-dev-worker` (the api runs no worker loop). Kinds, concurrency and
  expected times: [job-kind register](../job-kinds.md). Statuses: `queued`, `running`, `succeeded`, `failed`,
  `stopped_budget`, `cancelled`.
- Booking: `booking.job`, worker inside the api process (on by default on Dev); `bk_inquiry_pull` is always queued by
  design.
- Partner CRM: `crm.job`, worker inside the `aa-crm-dev-api` process. `crm_heartbeat`, `crm_membership_pull` and
  `crm_booking_sync` are recurring, so one row of each is always queued. The CIS admin reads per-kind counts through
  the CRM ops contract (`GET /crm/ops/v1/jobs/summary`); one agency's failed jobs are listed and retried through
  `/crm/ops/v1/tenants/{id}/jobs`.
- Admin endpoints (CIS, staff session): `GET /admin/job-runner/summary`, `/jobs`, `/workers`, `/jobs/{id}`,
  `POST /admin/job-runner/jobs/{id}/cancel` (queued or running), `POST .../retry` (failed, stopped_budget, cancelled),
  and `GET /admin/job-runner/released?since=` (jobs a worker released back to the queue on shutdown, AA-993).
  The admin **Jobs** page shows the same, with worker health.
- A retired kind (no handler) is cancelled automatically by the api sampler.

## Steps

1. Look (read-only): admin Jobs page, or `GET /admin/job-runner/summary` and `/workers`.
   Expected: which kind is queued or running, since when, and whether a live worker heartbeats.

2. Is a worker alive?

   ```bash
   aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-worker --profile aa365-admin --region us-west-1 --query "services[0].{desired:desiredCount,running:runningCount,r:deployments[0].rolloutState}" --output table
   aws logs tail /ecs/aa-cis-dev --since 30m --log-stream-name-prefix worker --filter-pattern '?job_worker_started ?ERROR ?Traceback' --profile aa365-admin --region us-west-1
   ```

   - `running` 0 or crash loop: fix the worker first (a bad deploy: [rollback-cis](../runbooks/rollback-cis.md)).
   - Worker started without the kind: an unregistered kind (deploy mismatch between api and worker: both must run the
     same SHA).
   - Booking or CRM: run the same `describe-services` line for `aa-booking-dev-api` or `aa-crm-dev-api`, and read
     the log groups `/ecs/aa-booking-dev` or `/ecs/aa-crm-dev`.

3. A running job that is overdue: read its progress and LLM calls (`GET /admin/job-runner/jobs/{id}` and
   `/jobs/{id}/llm-calls`). If it is really stuck or burning money, cancel it.

   Admin Jobs page, the job, **Cancel** (or `POST /admin/job-runner/jobs/{id}/cancel` with a staff session). # WRITE

   Expected: `cancel_requested` set; the handler stops at its next check and the row ends `cancelled`; the kind's
   `on_terminal` hook marks the domain row (for example a tour version) so no UI waits forever.
   Rollback: **Retry** the job (re-queues it from scratch).

4. A queued job that never starts while a worker is idle: check the kind's concurrency and `background` flag (background
   kinds never take the last free slots). A wave or many queued pipeline jobs can starve background kinds by design.

5. Stopped on budget (`stopped_budget`): a cost guard limit was hit; see [LLM cost spike](llm-cost-spike.md) before
   retrying.

## Close

- Queue age back under 15 minutes, both alarms `OK`, no `running` row past twice its expected time.
- Lessons: a kind whose expected time is wrong gets a code fix (`expected_seconds` on the kind).
