---
id: OPS-02-booking
title: Roll back the Booking API
description: Point aa-booking-dev-api back to the last good task-definition revision when a Booking deploy is healthy to ECS but wrong for users.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-booking-api]
last_reviewed: 2026-10-19
review_every_days: 90
last_tested: null
tested_where: null
tested_evidence: null
related: [OPS-02-cis, OPS-04, OPS-10-deploy-gate, AA-869, AA-892]
---

# Roll back the Booking API

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> The same procedure was drilled on CIS (S241, [rollback-cis](rollback-cis.md)); on Booking only the read-only
> steps 1-3 were run (19/10/2026). Set `status: active` after the first real run.

## When to use

- Trigger: a Booking deploy finished (rollout `COMPLETED`) but `/booking/*` routes misbehave, or
  `aa-booking-dev-api-5xx` fires right after a deploy.
- Not for:
  - a deploy that never became healthy: the ECS circuit breaker (enabled, with rollback) handles it;
  - the Booking admin frontend: [roll back a Vercel deployment](rollback-vercel.md);
  - a bad `bk-NNN` migration: migrations only go forward (see [DB Migrate](db-migrate.md)).

## Preconditions

- Access: profile `aa365-admin` (MFA session), region `us-west-1`.
- Jobs: Booking has its own gate over `booking.job` (`GET /booking/ops/deploy-gate`). `bk_inquiry_pull` is
  always queued and is exempt. A rollback restarts the container like a deploy.
- Image: ECR `aa-booking-dev-api` is IMMUTABLE, tags are the full git SHA, and the lifecycle rule keeps only the
  **last 10 images**. Older revisions may have no image.
- Booking has one service (`aa-booking-dev-api`, container `api`); its worker runs in the same process.
- Cost: 0 USD.

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account from the [account map](../../onboarding.md#account-map).

## Steps

1. Read the running revision and SHA.

   ```bash
   aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-booking-dev-api --profile aa365-admin --region us-west-1 --query "services[0].{td:taskDefinition,r:deployments[0].rolloutState}" --output table
   curl -s https://api-booking.lumiguides.it.com/booking/health
   ```

   Expected: `COMPLETED`; `/booking/health` shows `git_sha`.
   Rollback: none - read-only.

2. List recent revisions with their image SHA and pick the newest one with a different, good SHA.

   ```bash
   for r in $(aws ecs list-task-definitions --family-prefix aa-booking-dev-api --sort DESC --profile aa365-admin --region us-west-1 --query "taskDefinitionArns[:6]" --output text); do echo "${r##*/} $(aws ecs describe-task-definition --task-definition $r --profile aa365-admin --region us-west-1 --query 'taskDefinition.containerDefinitions[0].image' --output text | sed 's/.*://')"; done
   ```

   Expected: lines like `aa-booking-dev-api:<rev> <40-char sha>`.
   Verify: the SHA is the commit before the bad PR in AA-Booking `main`.
   Rollback: none - read-only.

3. Check the image still exists.

   ```bash
   aws ecr describe-images --repository-name aa-booking-dev-api --image-ids imageTag=<good-sha> --profile aa365-admin --region us-west-1 --query "imageDetails[0].imagePushedAt" --output text
   ```

   Expected: a timestamp. `ImageNotFoundException`: the image expired (10-image rule); fix forward instead.
   Rollback: none - read-only.

4. Compare configuration. Booking Deploy Dev copies the family's **latest** revision (so Terraform env and
   secrets changes reach the task), which means an older revision can carry an older configuration.

   ```bash
   aws ecs describe-task-definition --task-definition aa-booking-dev-api:<target-rev> --profile aa365-admin --region us-west-1 --query "taskDefinition.containerDefinitions[0].[environment[].name, secrets[].valueFrom]" --output json
   ```

   Expected: same names and secret references as the current revision. A difference: Nghiệp decides.
   Rollback: none - read-only.

5. Point the service at the target revision and wait.

   ```bash
   aws ecs update-service --cluster aa-cis-dev-cluster --service aa-booking-dev-api --task-definition aa-booking-dev-api:<target-rev> --profile aa365-admin --region us-west-1 --query "service.deployments[0].rolloutState" --output text # WRITE
   aws ecs wait services-stable --cluster aa-cis-dev-cluster --services aa-booking-dev-api --profile aa365-admin --region us-west-1
   ```

   Expected: `IN_PROGRESS`, then the wait returns.
   Verify: step 6.
   Rollback: the same command with the revision from step 1.

6. Verify live.

   ```bash
   curl -s https://api-booking.lumiguides.it.com/booking/health
   curl -s https://api-booking.lumiguides.it.com/booking/health/ready
   ```

   Expected: `git_sha` = the good SHA; ready shows `"db":"ok"` and the current `schema_version` (an old build must
   still accept the newer `bk-NNN`; if ready fails on the schema, roll forward instead).
   Rollback: step 5 with the revision from step 1.

7. Revert the bad PR on AA-Booking `main`; Deploy Dev then registers a fresh revision from the latest one.

## Verify the result

- Service `COMPLETED`, `/booking/health` reports the good SHA, `/booking/health/ready` 200,
  `aa-booking-dev-api-5xx` back to `OK`.

## Roll back or abort

- Step 5 is undone by pointing the service at the revision from step 1.
- Abort when step 3 or 4 fails: fix forward with a revert PR instead.

## Escalation

- [Incident response](../incident-response.md). Booking holds customer records (test data only on Dev, D-01).

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-10-19 | dev-acc2, read-only steps 1-3 | Claude Code | `docs/audits/2026-10-19-S243-ops-runbooks/readonly-checks.md` | read-only only; write steps untested |
