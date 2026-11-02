---
id: OPS-02-ecs
title: Roll back any ECS service
description: One parameterised procedure to point an ECS service (CIS api/worker, Booking api, CRM api, web, portal) at an earlier task-definition revision or image SHA and back, with the helper tools/ops/ecs_rollback.sh.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-api, aa-cis-worker, aa-booking-api, aa-crm-api, aa-crm-web, aa-crm-portal]
last_reviewed: 2026-11-02
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [OPS-02-cis, OPS-02-booking, OPS-02-vercel, OPS-02-tp-lambda, OPS-03-gameday, OPS-10-deploy-gate, tools/ops/ecs_rollback.sh, AA-1023]
---

# Roll back any ECS service

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> The same mechanism was drilled on CIS (S241, [rollback-cis](rollback-cis.md)). This page and its helper are run for
> Booking and CRM in the [rollback game day](../drills/rollback-game-day.md) (AA-1023). Set `status: active` after it.

This page is the shared procedure. The per-app pages keep their app facts:
[CIS api + worker](rollback-cis.md) (two services on one image) and [Booking](rollback-booking.md).

## When to use

- Trigger: a deploy finished (rollout `COMPLETED`) but the app is wrong: 5xx on changed routes, wrong data, a broken
  page that depends on the API, a Sentry error burst or a `*-no-healthy-task` alarm right after a deploy.
- Not for:
  - a deploy that never became healthy: the ECS deployment circuit breaker (enabled with rollback on every service)
    already returns the service to the previous revision. Check the rollout state first (step 1).
  - a frontend on Vercel ([rollback-vercel](rollback-vercel.md)) or the TripPlanner Lambdas
    ([rollback-tp-lambda](rollback-tp-lambda.md));
  - a bad migration: the database does not roll back with the app. Migrations only go forward
    ([DB Migrate](db-migrate.md)); the old build must run on the newer schema.

## Parameters

| Parameter | Values |
|---|---|
| `<service>` | `aa-cis-dev-api`, `aa-cis-dev-worker`, `aa-booking-dev-api`, `aa-crm-dev-api`, `aa-crm-dev-web`, `aa-crm-dev-portal`. The task-definition family has the same name. Cluster `aa-cis-dev-cluster` for all. |
| `<target>` | one of: `--previous` (newest older revision with a different real build), `--to <revision>`, `--to-sha <git-sha>` (full or a 7+ character prefix) |
| `<current-revision>` | the revision the service runs now (step 1); it is the way back |

| Service | Image tag | Images kept in ECR | Health (field with the commit) | Job table it runs |
|---|---|---|---|---|
| `aa-cis-dev-api` | `dev-<sha>` | 30 | `https://api-cis.lumiguides.it.com/health` (`git_sha`) | `shared.job` (with the worker) |
| `aa-cis-dev-worker` | `dev-<sha>` (same image as the api) | 30 | none over HTTP: log line `job_worker_started` | `shared.job` |
| `aa-booking-dev-api` | `<sha>` | 10 | `https://api-booking.lumiguides.it.com/booking/health` (`git_sha`) | `booking.job` (in process) |
| `aa-crm-dev-api` | `<sha>` | 10 | `https://partner-dev.lumiguides.it.com/crm/health` (`git_sha`) | `crm.job` (in process) |
| `aa-crm-dev-web` | `<sha>` | 10 | `https://portal.lumiguides.it.com/healthz` (`git_sha`) | none |
| `aa-crm-dev-portal` | `<sha>` | 10 | `https://portal.lumiguides.it.com/api/healthz` (`sha`) | none |

Facts that shape the procedure:

- Each Deploy Dev copies the family's **newest** revision and swaps the image, so Terraform env and secret changes
  reach the task. An older revision therefore carries an **older configuration** (step 4).
- A Terraform apply that touches a task definition registers a **template revision** with a placeholder image tag
  (`bootstrap`, `latest`). It is never a rollback target; the helper skips and refuses those.
- A redeploy of the same commit registers a new revision with the same image, so "current minus one" can be the same
  build; `--previous` skips those too.
- ECR repositories are IMMUTABLE and keep only the newest images (table above). An older revision may have no image.

## Preconditions

- Access: profile `aa365-admin` (MFA session), region `us-west-1`. Orchestrator or tech lead only: agent lanes cannot
  run writes against AWS.
- Jobs: a rollback restarts the container like a deploy. The worker drains and releases running jobs, the new task
  re-claims them (AA-993). Check the app's deploy gate before step 5
  ([deploy-gate override](deploy-gate-override.md) lists the gates). Blocked by a deploy-blocking job during a SEV1:
  the tech lead decides.
- Tools: `bash`, `jq`, `curl`, AWS CLI v2.
- Cost: 0 USD.

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account from the [account map](../../onboarding.md#account-map).

## Steps

1. Read what runs now and the revisions to choose from.

   ```bash
   bash tools/ops/ecs_rollback.sh <service> --list
   ```

   Expected: `running: <service>:<current-revision>  image tag <tag>  rollout COMPLETED  deployments 1`, then the newest
   ACTIVE revisions with their image tag; template revisions are marked "(Terraform template, not a target)".
   Verify: if the rollout is `IN_PROGRESS` or `FAILED`, wait for the circuit breaker before anything else.
   Rollback: none - read-only.
   Without the helper, the same listing in one line:

   ```bash
   for r in $(aws ecs list-task-definitions --family-prefix <service> --sort DESC --profile aa365-admin --region us-west-1 --query "taskDefinitionArns[:8]" --output text); do echo "${r##*/} $(aws ecs describe-task-definition --task-definition $r --profile aa365-admin --region us-west-1 --query 'taskDefinition.containerDefinitions[0].image' --output text | sed 's/.*://')"; done
   ```

2. Pick the target: the commit before the bad PR (`git log --oneline origin/main` in the app repo), as `--to-sha`, or
   `--previous` when the bad deploy is the newest one.

3. Dry run: the helper checks the target and prints the commands. Nothing changes.

   ```bash
   bash tools/ops/ecs_rollback.sh <service> <target>
   ```

   Expected: `target: <service>:<revision>  image tag <tag>`, `image: ... pushed <date>` (still in ECR), the
   configuration line, the `command (WRITE)` line, the `way back (WRITE)` line and `DRY RUN: nothing changed`.
   Verify: the image SHA is the one you want. An `ERROR: image ... is not in ECR any more` means the image expired:
   pick a newer good revision or fix forward.
   Rollback: none - read-only.

4. Read the configuration check in the same output. `config: same environment names and secret references` is the
   normal case. `CONFIG DIFF` lists the environment variables and secrets that exist in only one of the two revisions
   (names only). A variable only in the running revision means the old build runs without it (usually a feature that
   was switched on later is off again); a secret change can undo a security change.
   Expected: no difference, or one you can explain.
   Verify: a difference you cannot explain means the tech lead decides; in a drill on Dev, name the variables in the
   evidence.
   Rollback: none - read-only.

5. Apply. `--allow-config-diff` only when step 4 showed a difference that was accepted.

   ```bash
   bash tools/ops/ecs_rollback.sh <service> <target> --apply # WRITE
   ```

   It runs the printed `aws ecs update-service ... --task-definition <service>:<revision>` line, then
   `aws ecs wait services-stable`, then checks that the service runs the target revision with rollout `COMPLETED`, and
   reads the health endpoint until it reports the target SHA (12 tries, 10 s apart).
   Expected: `DONE: <service> on <service>:<revision> (<tag>) in <n> s.` The time is the drill's RTO.
   Verify: step 6.
   Rollback: `bash tools/ops/ecs_rollback.sh <service> --to <current-revision> --apply` (the `way back` line).
   Without the helper (same effect):

   ```bash
   aws ecs update-service --cluster aa-cis-dev-cluster --service <service> --task-definition <service>:<revision> --profile aa365-admin --region us-west-1 --query "service.deployments[0].rolloutState" --output text # WRITE
   aws ecs wait services-stable --cluster aa-cis-dev-cluster --services <service> --profile aa365-admin --region us-west-1
   ```

6. Verify live with the health row of the table above, plus the readiness endpoint where there is one.

   ```bash
   curl -s https://api-booking.lumiguides.it.com/booking/health
   curl -s https://api-booking.lumiguides.it.com/booking/health/ready
   ```

   Expected: the commit field equals the target SHA; ready answers 200 with `"db":"ok"` (the CRM API:
   `/crm/health/ready`; CIS: `/health/ready`). An old build must still accept the newer schema; if readiness fails on
   the schema, roll forward instead.
   CIS worker: `aws logs tail /ecs/aa-cis-dev --since 10m --filter-pattern job_worker_started --profile aa365-admin --region us-west-1`
   shows a line from the new task. CIS api and worker must end on the **same** image: run step 5 for the other
   service with `--to-sha` of the same commit.
   Rollback: step 5's way back.

7. Fix on `main`: revert the bad PR in the app repo (`Refs AA-xxx`). The next Deploy Dev registers a fresh revision
   from the newest one. Do not move the service back to the bad revision by hand.

## Verify the result

- The service is `COMPLETED` on the target revision, its health endpoint reports the target SHA, readiness is 200.
- The alarm that triggered the rollback is back to `OK`.

## Roll back or abort

- Every write is undone by `bash tools/ops/ecs_rollback.sh <service> --to <current-revision> --apply`.
- Abort at step 3 or 4 (image expired, configuration difference nobody can explain): fix forward with a revert PR.

## Escalation

- [Incident response](../incident-response.md). A rollback of a service that holds customer data (Booking, CRM) is
  reported to the tech lead the same day.

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-11-02 | dev-acc2, dry run of `--list` and `--previous` for `aa-booking-dev-api` and `aa-crm-dev-api` (read-only) | Claude Code | lane notes `docs/implementation-notes/AA-1023.md` | read-only: Booking target needs `--allow-config-diff` (`ALERTS_TOPIC_ARN` only in the running revision); CRM target same configuration |
