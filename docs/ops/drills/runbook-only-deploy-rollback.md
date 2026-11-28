---
id: OPS-03-runbook-only
title: Runbook-only deploy and rollback drill
description: Numbered literal steps, expected outputs and a timing table for one deploy, one rollback and one roll-forward of the Booking admin on Dev, done by a person with only GitHub, the AWS CLI and the runbooks.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, owner]
applies_to: [aa-booking-admin, ecosystem]
last_reviewed: 2026-11-28
review_every_days: 90
related: [OPS-03-drills, OPS-01-no-agent, OPS-02-ecs, OPS-03-gameday, OPS-03-tabletop, SEC-05-access-register, AA-1110]
---

# Runbook-only deploy and rollback drill

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> This is the script of the first run. After the run, fill the timing table, put the evidence in
> `docs/audits/<date>-S<nnn>-runbook-only-drill/` and change the "to fill" row of the [drill index](README.md).

The drill proves that a person can deploy, roll back and roll forward one service with only the GitHub web UI, one-line
AWS CLI commands and the pages linked here: [run without the agent](../run-without-agent.md) and
[roll back any ECS service](../runbooks/rollback-ecs.md). It uses no helper script on purpose (the helper
`tools/ops/ecs_rollback.sh` was proven by the agent-run [game day](rollback-game-day.md)). Cost: 0 USD (a few
Fargate task-minutes inside the existing service).

## Why the Booking admin

The drill target is the ECS service `aa-booking-dev-admin` (the Booking staff admin, host `booking.lumiguides.it.com`).
The other candidate was the CRM web (`aa-crm-dev-web`).

| | Booking admin (chosen) | CRM web |
|---|---|---|
| Who sees a bad minute | AA staff only, on Dev | agency users of the CRM and the tenant portal host as well (synthetic agencies on Dev, real ones from the pilot) |
| State | none: a Next.js frontend, no job table, no migration, no worker | none in the web, but it fronts the tenant portal and the CRM sign-in that the E2E logins use |
| Health that names the build | `/api/healthz` answers `status`, `app` and `sha` | `/healthz` answers `git_sha` |
| Deploy without a code change | `Deploy Admin Dev` **Run workflow** on `main` reuses the image already in ECR (no build) | the same pattern |
| Drilled before | only on Vercel (game day 2026-11-02, since retired): the ECS path is new | never |

Both are low risk; the Booking admin has the smaller audience and nothing a tenant can see, and its ECS path has never
been drilled, so the drill adds the most proof for the least risk.

## Roles

| Role | Does |
|---|---|
| Operator (the second key-holder, or the tech lead) | Runs every step on their own laptop and GitHub account; reads the expected output aloud |
| Observer (the tech lead or the agent) | Does not touch the keyboard; writes times and outputs into the timing table; stops the drill if an abort condition is met |

A run where the agent types the commands counts as **agent-run (rehearsal)**, not runbook-only (the [drill index](README.md)
rule).

## Before you start

1. A laptop with AWS CLI v2, `curl` and a browser. The operator's GitHub account has write access to `AA-Booking`
   (needed for **Run workflow**).
2. The operator's AWS session on acc2 with MFA (profile `aa365-admin`, or the operator's Identity Center profile into
   acc2). Every command below says `--profile aa365-admin`; replace it with your own profile name if it differs.
3. No `Deploy Admin Dev` run is in progress on AA-Booking (Actions tab, filter the workflow; nothing yellow), and no
   Booking pull request touching `frontend/` is about to merge (a merge would deploy during the drill).
4. Open the timing table at the end of this page (copy it into the evidence `README.md`). Write every time in UTC:
   `date -u +%FT%TZ`.

## Steps

### Part 0: baseline (read-only)

1. Check the account.

   ```bash
   aws sts get-caller-identity --profile aa365-admin
   ```

   Expected: `"Account"` is the acc2 account from the [account map](../../onboarding.md#account-map). Any other
   account: stop.

2. Read what runs now.

   ```bash
   aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-booking-dev-admin --profile aa365-admin --region us-west-1 --query "services[0].{td:taskDefinition,desired:desiredCount,running:runningCount,rollout:deployments[0].rolloutState,deployments:length(deployments)}" --output table
   ```

   Expected: `desired` 1, `running` 1, `rollout` `COMPLETED`, `deployments` 1. Write the revision number at the end of
   `td` (`...task-definition/aa-booking-dev-admin:<R0>`) as **R0**. `desired` 0 means the service is scaled down:
   stop, the drill needs a running task.

3. Read the build it serves.

   ```bash
   curl -s https://booking.lumiguides.it.com/api/healthz
   curl -s -o /dev/null -w "%{http_code}\n" https://booking.lumiguides.it.com/login
   ```

   Expected: `{"status":"ok","app":"booking-admin","sha":"<S0>",...}` and `200`. Write the first 7 characters of the
   `sha` as **S0**.

4. List the newest revisions and their image tags (the tag is the git SHA of the build).

   ```bash
   for r in $(aws ecs list-task-definitions --family-prefix aa-booking-dev-admin --sort DESC --profile aa365-admin --region us-west-1 --query "taskDefinitionArns[:8]" --output text); do echo "${r##*/} $(aws ecs describe-task-definition --task-definition $r --profile aa365-admin --region us-west-1 --query "taskDefinition.containerDefinitions[?name=='booking-admin'].image | [0]" --output text | sed 's/.*://')"; done
   ```

   Expected: eight lines `aa-booking-dev-admin:<revision> <tag>`, newest first; R0 shows S0. Pick the **rollback
   target R1**: the newest revision below R0 whose tag is a git SHA different from S0. Skip a tag that is `bootstrap`
   or `latest` (a Terraform template revision, never a target) and a revision with the same tag as R0 (a redeploy of
   the same build). Write its tag as **S1**.

5. Check that the image of R1 is still in ECR (the repository keeps the newest 10 images).

   ```bash
   aws ecr describe-images --repository-name aa-booking-dev-admin --image-ids imageTag=<S1-full-tag> --profile aa365-admin --region us-west-1 --query "imageDetails[0].imagePushedAt" --output text
   ```

   Expected: a date. `ImageNotFoundException`: pick the next older revision of step 4 and check again.

6. Compare the configuration of R0 and R1 (names only, never values).

   ```bash
   aws ecs describe-task-definition --task-definition aa-booking-dev-admin:<R0> --profile aa365-admin --region us-west-1 --query "taskDefinition.containerDefinitions[?name=='booking-admin'] | [0].[environment[].name, secrets[].name]" --output text
   aws ecs describe-task-definition --task-definition aa-booking-dev-admin:<R1> --profile aa365-admin --region us-west-1 --query "taskDefinition.containerDefinitions[?name=='booking-admin'] | [0].[environment[].name, secrets[].name]" --output text
   ```

   Expected: the same names. A name only in R0 means R1 runs without it (a feature switched on later is off again
   for the drill). Write the difference down; if nobody can explain it, pick a revision closer to R0.

### Part 1: deploy by the GitHub web UI

7. In GitHub, open `AdventureAsia365-Ecosys/AA-Booking`, tab **Actions**, workflow **Deploy Admin Dev**, button
   **Run workflow**, branch `main`, **Run workflow**. Write the start time (**T1 start**).

   Expected: a new run appears within a few seconds.

8. Open the run and wait (about 5 to 10 minutes). Do not refresh the AWS console meanwhile; one look at the end is
   enough.

   Expected: jobs `Deploy configuration`, `Deploy Booking admin to ECS Dev`, `Post-deploy verify (ALB host rule)`,
   `Public smoke (production)` and `result` are green; `rollback` and `report` are skipped. In the deploy job, step
   "Build and push image" prints `image <sha> already in ECR: reusing it (no build, no push)` when `main` has no new
   frontend commit since S0 (otherwise it builds the new commit, which is fine). Write the end time (**T1 end**) and
   the run link.

9. Verify the new revision and build.

   ```bash
   aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-booking-dev-admin --profile aa365-admin --region us-west-1 --query "services[0].{td:taskDefinition,running:runningCount,rollout:deployments[0].rolloutState}" --output table
   curl -s https://booking.lumiguides.it.com/api/healthz
   ```

   Expected: a revision **R2** greater than R0, `COMPLETED`, `running` 1; `sha` equals the head commit of `main` in
   AA-Booking (the run's commit). Write R2 and its 7-character SHA **S2**. R2 is the way forward in Part 3.

   Abort: the run is red. Since AA-1119 a red verify or smoke rolls the service back to R0 by itself and opens a
   `deploy-smoke-red` issue; read the failed job, write the outcome down and stop the drill (the drill found a gap).

### Part 2: roll back by the AWS CLI

10. Write the start time (**T2 start**), then point the service at R1.

    ```bash
    aws ecs update-service --cluster aa-cis-dev-cluster --service aa-booking-dev-admin --task-definition aa-booking-dev-admin:<R1> --profile aa365-admin --region us-west-1 --query "service.deployments[0].rolloutState" --output text # WRITE
    ```

    Expected: `IN_PROGRESS`.

11. Wait until the service is stable.

    ```bash
    aws ecs wait services-stable --cluster aa-cis-dev-cluster --services aa-booking-dev-admin --profile aa365-admin --region us-west-1
    ```

    Expected: the prompt comes back with no output (up to 10 minutes). `Waiter ServicesStable failed`: go to the abort
    line of this part.

12. Verify the rollback.

    ```bash
    aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-booking-dev-admin --profile aa365-admin --region us-west-1 --query "services[0].{td:taskDefinition,running:runningCount,rollout:deployments[0].rolloutState,deployments:length(deployments)}" --output table
    curl -s https://booking.lumiguides.it.com/api/healthz
    curl -s -o /dev/null -w "%{http_code}\n" https://booking.lumiguides.it.com/login
    ```

    Expected: `td` ends in `:<R1>`, `COMPLETED`, `deployments` 1; `sha` starts with S1; `/login` answers `200`. Write
    the end time (**T2 end**). The healthz answer can lag by up to a minute behind the ECS state while the load
    balancer drains the old task: repeat the `curl` once after 30 seconds before calling it a failure.

    Abort: the service does not settle, or `/login` is not 200 after two minutes. Go straight to Part 3 (forward to R2).

### Part 3: roll forward by the AWS CLI

13. Write the start time (**T3 start**), then point the service back at R2.

    ```bash
    aws ecs update-service --cluster aa-cis-dev-cluster --service aa-booking-dev-admin --task-definition aa-booking-dev-admin:<R2> --profile aa365-admin --region us-west-1 --query "service.deployments[0].rolloutState" --output text # WRITE
    aws ecs wait services-stable --cluster aa-cis-dev-cluster --services aa-booking-dev-admin --profile aa365-admin --region us-west-1
    ```

    Expected: `IN_PROGRESS`, then the wait returns with no output.

14. Verify.

    ```bash
    aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-booking-dev-admin --profile aa365-admin --region us-west-1 --query "services[0].{td:taskDefinition,running:runningCount,rollout:deployments[0].rolloutState,deployments:length(deployments)}" --output table
    curl -s https://booking.lumiguides.it.com/api/healthz
    curl -s -o /dev/null -w "%{http_code}\n" https://booking.lumiguides.it.com/login
    ```

    Expected: `td` ends in `:<R2>`, `COMPLETED`, `deployments` 1; `sha` starts with S2; `/login` `200`. Write the end
    time (**T3 end**). The service is where Part 1 left it; nothing else to undo.

### Part 4: close

15. Sign in to the Booking admin in a browser once (staff sign-in) and open one list page. Expected: the page loads
    with data. This catches a build that answers healthz but cannot reach the Booking API.
16. Write the evidence `README.md` (timing table, the run link, the outputs of steps 2, 3, 9, 12 and 14 as printed;
    no token, no presigned URL), then change the drill index row from "to fill" to the result.
17. Every step that was unclear, wrong or needed help is a finding: list it in the evidence and fix the page in the
    same root PR, or open a follow-up issue (ask the tech lead first).

## Timing record

Targets on Dev (no SLO yet): deploy within 15 minutes, rollback within 10 minutes, roll-forward within 10 minutes,
measured from the start time to the verified end time.

| Part | Start (UTC) | End (UTC) | Minutes | Result (pass / fail / abort) | Values (revision, SHA) | Notes (help needed, unclear step) |
|---|---|---|---|---|---|---|
| 0 Baseline | | | | | R0 = , S0 = , R1 = , S1 = | |
| 1 Deploy (GitHub Run workflow) | | | | | R2 = , S2 = , run link: | |
| 2 Rollback (CLI, to R1) | | | | | | |
| 3 Roll forward (CLI, to R2) | | | | | | |
| 4 Close (browser check) | | | | | | |

Run kind: runbook-only (operator: ______ role) / agent-run (rehearsal). Observer: ______ role.

## Abort at any point

- Point the service at R2 (or at R0 if Part 1 never finished) with the step 13 commands; that is the whole undo.
- A Fargate Spot interruption during the drill (the staff web services run on Spot) restarts the task on the same
  revision; wait for `COMPLETED` and repeat the current verify step.
- Escalation: [incident response](../incident-response.md). A drill on Dev is SEV3 even if it fails.
