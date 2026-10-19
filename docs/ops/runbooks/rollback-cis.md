---
id: OPS-02-cis
title: Roll back the CIS API and worker
description: Point aa-cis-dev-api and aa-cis-dev-worker back to the last good task-definition revision when a deploy is healthy to ECS but wrong for users.
type: how-to
status: active
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-api, aa-cis-worker]
last_reviewed: 2026-10-19
review_every_days: 90
last_tested: 2026-10-17
tested_where: drill
tested_evidence: docs/sessions/2026-10-17-S241-sdlc-admin-console-x1-security.md (AA-869 rollback drill)
related: [OPS-04, OPS-10-deploy-gate, OPS-02-vercel, skill/aa-ship/SKILL.md, AA-869, AA-892]
---

# Roll back the CIS API and worker

Moved here from `skill/aa-ship/SKILL.md` §5 (AA-869, S241). The skill now links to this page.

## When to use

- Trigger: a CIS deploy finished (rollout `COMPLETED`) but the app is wrong: 5xx on changed routes, wrong data,
  a broken admin page that depends on the API, or the `aa-cis-dev-api-5xx` alarm right after a deploy.
- Not for:
  - a deploy that never became healthy. The ECS deployment circuit breaker (enabled, with rollback) already
    returns the service to the previous revision by itself. Check the rollout state first.
  - frontend-only problems: see [roll back a Vercel deployment](rollback-vercel.md).
  - a bad migration: the DB does not roll back with the app. Migrations only go forward; the fix is a new
    migration. The old app must run on the new schema (see [DB Migrate](db-migrate.md)).

## Preconditions

- Access: profile `aa365-admin` (MFA session), region `us-west-1`.
- Jobs: a rollback restarts the api and worker containers, like a deploy. Check the deploy gate first. If jobs
  are running and the incident is SEV1, Nghiệp decides whether to roll back anyway
  ([deploy-gate override](deploy-gate-override.md)).
- Image: CIS ECR `aa-cis-dev-api` is IMMUTABLE and keeps the last 30 `dev-<sha>` images, so any revision in
  that window still has its image.
- Cost: 0 USD.

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account from the [account map](../../onboarding.md#account-map).

## Steps

1. Read the revision and image each service runs now.

   ```bash
   aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-api aa-cis-dev-worker --profile aa365-admin --region us-west-1 --query "services[].{n:serviceName,td:taskDefinition,r:deployments[0].rolloutState}" --output table
   ```

   Expected: both services `COMPLETED`, api and worker on the same image SHA (step 2 shows the image).
   Verify: if the state is `IN_PROGRESS` or `FAILED`, wait for the circuit breaker before doing anything.
   Rollback: none - read-only.

2. List the recent api revisions with their image tags and pick the newest one with a **different** image.
   A deploy that reuses an image still registers a new revision, so "current minus one" can be the same build.

   ```bash
   for r in $(aws ecs list-task-definitions --family-prefix aa-cis-dev-api --sort DESC --profile aa365-admin --region us-west-1 --query "taskDefinitionArns[:6]" --output text); do echo "${r##*/} $(aws ecs describe-task-definition --task-definition $r --profile aa365-admin --region us-west-1 --query 'taskDefinition.containerDefinitions[0].image' --output text | sed 's/.*://')"; done
   ```

   Run the same line with `aa-cis-dev-worker` and pick the worker revision with the **same** `dev-<sha>` as the
   chosen api revision.
   Expected: lines like `aa-cis-dev-api:<rev> dev-<sha>`.
   Verify: the target SHA is the commit before the bad PR (`git log --oneline origin/main` in AA-CIS-App).
   Rollback: none - read-only.

3. Check that the target image still exists in ECR.

   ```bash
   aws ecr describe-images --repository-name aa-cis-dev-api --image-ids imageTag=dev-<good-sha> --profile aa365-admin --region us-west-1 --query "imageDetails[0].imagePushedAt" --output text
   ```

   Expected: a timestamp. `ImageNotFoundException` means the image expired: pick a newer good revision or fix
   forward.
   Verify: the tag matches step 2.
   Rollback: none - read-only.

4. Compare the configuration. A task-definition revision carries its own environment and secret references. If
   Terraform changed them between the two revisions (for example the X1 move of the DB login to `cis_app`), the
   old revision brings the old configuration back.

   ```bash
   aws ecs describe-task-definition --task-definition aa-cis-dev-api:<target-rev> --profile aa365-admin --region us-west-1 --query "taskDefinition.containerDefinitions[0].[environment[].name, secrets[].valueFrom]" --output json
   ```

   Expected: the same names and secret references as the current revision.
   Verify: run it for the current revision and compare. A difference means Nghiệp decides (rolling back may undo
   a security change).
   Rollback: none - read-only.

5. Point the api at the target revision.

   ```bash
   aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-api --task-definition aa-cis-dev-api:<target-rev> --profile aa365-admin --region us-west-1 --query "service.deployments[0].rolloutState" --output text # WRITE
   ```

   Expected: `IN_PROGRESS`.
   Verify: step 7.
   Rollback: the same command with the revision from step 1.

6. Point the worker at the revision with the same image, then wait for both.

   ```bash
   aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-worker --task-definition aa-cis-dev-worker:<target-rev> --profile aa365-admin --region us-west-1 --query "service.deployments[0].rolloutState" --output text # WRITE
   aws ecs wait services-stable --cluster aa-cis-dev-cluster --services aa-cis-dev-api aa-cis-dev-worker --profile aa365-admin --region us-west-1
   ```

   Expected: the wait returns with no output (it gives up after about 10 minutes with an error).
   Verify: step 7.
   Rollback: the same command with the worker revision from step 1.

7. Verify live.

   ```bash
   aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-api aa-cis-dev-worker --profile aa365-admin --region us-west-1 --query "services[].{n:serviceName,td:taskDefinition,r:deployments[0].rolloutState}" --output table
   curl -s https://api-cis.lumiguides.it.com/health
   curl -s -o /dev/null -w "%{http_code}\n" https://api-cis.lumiguides.it.com/health/ready
   aws logs tail /ecs/aa-cis-dev --since 10m --filter-pattern job_worker_started --profile aa365-admin --region us-west-1
   ```

   Expected: both `COMPLETED`; `/health` shows `"git_sha":"<good-sha>"`; `/health/ready` 200; a
   `job_worker_started` line from the new worker task.
   Rollback: steps 5-6 with the revisions from step 1.

8. Fix on `main`. Revert the bad PR (`gh pr create` from a revert branch, `Refs AA-xxx`). The normal Deploy Dev
   run then moves both services to a new revision. Do not move the services back to the bad revision by hand.

## Verify the result

- Both services `COMPLETED` on the same `dev-<sha>`, `/health` reports that SHA, `/health/ready` 200.
- The alarm that triggered the rollback is back to `OK` (alarms e-mail on OK too, D-20).

## Roll back or abort

- Every write step is undone by pointing the service at the revision noted in step 1.
- Abort point: if step 4 shows a configuration difference you cannot explain, stop and ask Nghiệp.

## Escalation

- Severity and who to tell: [incident response](../incident-response.md). SEV1 means Ms. Thư is told within 30 minutes.

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-10-17 | drill (Dev acc2) | Claude Code + Nghiệp | S241 session log, AA-869 comment: api and worker moved two revisions back to an older SHA, `/health` 200, then forward again | pass |
| 2026-10-19 | dev-acc2, read-only steps 1-3 | Claude Code | `docs/audits/2026-10-19-S243-ops-runbooks/readonly-checks.md` | pass (listing and ECR policy checked; no write) |
