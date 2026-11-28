---
id: OPS-01-no-agent
title: Run the platform without the agent
description: How a person deploys, rolls back, applies a migration, rotates a key and handles an incident on Dev with the GitHub web UI, the AWS console and one-line AWS CLI commands only, built from the existing runbooks, with an honest tested state for each path.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, owner]
applies_to: [ecosystem, aa-cis-api, aa-booking-api, aa-crm-api, aa-tripplanner, tripplanner-lambda, aa-cis-infra]
last_reviewed: 2026-11-28
review_every_days: 90
related: [OPS-01, OPS-02-ecs, OPS-02-cis, OPS-02-booking, OPS-02-tp-lambda, OPS-02-vercel, OPS-02-terraform, OPS-05-db-migrate, OPS-10, OPS-10-deploy-gate, OPS-03-drills, OPS-03-tabletop, OPS-03-runbook-only, OPS-04-chat-alerts, SEC-02-rotation, SEC-05-access-register, SEC-05-second-keyholder, AA-1110]
---

# Run the platform without the agent

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> No person has yet deployed or rolled back from this page alone. The first runbook-only drill is the
> [runbook-only deploy and rollback drill](drills/runbook-only-deploy-rollback.md) (Booking admin); its result goes
> into the [drill index](drills/README.md). Until it passes, treat every path below as unproven for a person working
> alone.

Almost all delivery runs through AI agents today. This page is the short path for the tech lead, the second
key-holder or the engineer on duty when no agent is available. It links the runbooks that hold the detail; it adds no
new procedure, except where a gap had no page yet (rotate a key, handle an incident, who calls whom). Every path uses
the GitHub web UI, the AWS console or one-line AWS CLI commands.

## What you need

| Need | Where it comes from | Check |
|---|---|---|
| A GitHub account in the organization `AdventureAsia365-Ecosys` with write access to the app repos and AA-CIS-Infra | the organization owner; recorded in the [access register](../security/access-register.md) | open a repo's **Actions** tab and see **Run workflow** |
| The AWS admin profile on acc2 with MFA (`aa365-admin`) | the account map in [onboarding](../onboarding.md#account-map); the management account's Identity Center for the second key-holder | `aws sts get-caller-identity --profile aa365-admin` |
| AWS CLI v2 and `curl`; `gh` CLI is optional | your laptop (WSL2 on Windows) | `aws --version` |

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account from the [account map](../onboarding.md#account-map). Stop if it is any other account.

## Tested state of each path

"Agent-run" means an agent ran the steps (often with a helper script) while the tech lead watched. "Runbook-only"
means a person followed the page alone. Only a runbook-only run proves this page.

| Path | Runbook | Agent-run | Runbook-only |
|---|---|---|---|
| Deploy: merge on `main`, the app's deploy workflow runs | this page, section [Deploy](#deploy-a-change) | every merge since S235 | never |
| Roll back CIS api + worker | [rollback-cis](runbooks/rollback-cis.md) | drill 2026-10-17 (S241), pass | never |
| Roll back any other ECS service | [rollback-ecs](runbooks/rollback-ecs.md) | game day 2026-11-02 (S264): Booking API and CRM API with the helper `tools/ops/ecs_rollback.sh`, pass ([evidence](../audits/2026-11-02-S264-rollback-game-day/README.md)); the page itself is still `draft` | never |
| Roll back the Booking API (app facts page) | [rollback-booking](runbooks/rollback-booking.md) | read-only steps only (2026-10-19); the game day used rollback-ecs | never |
| Roll back the TripPlanner Lambdas | [rollback-tp-lambda](runbooks/rollback-tp-lambda.md) | game day 2026-11-02 (S264): path B on `aa-tripplanner-dev-browse`, pass; the page is still `draft` | never |
| Roll back a Vercel deployment | [rollback-vercel](runbooks/rollback-vercel.md) | superseded: no ecosystem frontend runs on Vercel any more | - |
| Roll back a Terraform change | [rollback-terraform](runbooks/rollback-terraform.md) | read-only only | never |
| Apply a migration by hand (DB Migrate) | [db-migrate](runbooks/db-migrate.md) | 2026-10-17 and 2026-10-18, pass | never |
| Sign in when nobody can (break-glass) | [break-glass](runbooks/break-glass.md) | 2026-10-19 (S244) through managed login with the tech lead, pass | never; planned as Part B of the [security tabletop](drills/security-tabletop.md) |
| Rotate a key | [secret rotation](runbooks/secret-rotation.md) | class 4 (break-glass, S242) and the admin secret (2026-10-17) only | never |
| Handle an incident | [incident response](incident-response.md) | real incidents handled by the tech lead with an agent | never; talk-through in the [security tabletop](drills/security-tabletop.md) |

## Before any write

1. Check the deploy gate. Since AA-993 G5 a deploy is held only while a CIS rerun wave is open or a deploy-blocking job
   kind runs; each app's deploy workflow checks it in its preflight step and stops with `blocked_by` in the log. Wait
   for that job, or ask the tech lead for an override ([deploy-gate override](runbooks/deploy-gate-override.md)).
2. Note what runs now, so you can go back. One line per service you will touch:

   ```bash
   aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-api aa-cis-dev-worker aa-booking-dev-api aa-crm-dev-api aa-crm-dev-web --profile aa365-admin --region us-west-1 --query "services[].{n:serviceName,td:taskDefinition,r:deployments[0].rolloutState}" --output table
   ```

   Expected: every service `COMPLETED`. Write the task-definition revisions down; they are your way back.

## Deploy a change

A deploy is a merge on `main`. Each app repo deploys itself from `main` through GitHub Actions; nothing is deployed
from a laptop.

1. Open the pull request on GitHub. Wait until every check is green (about 3 to 5 minutes).
2. Merge it:
   - AA-CIS-App, AA-Booking, AA-Partner and AA-TripPlanner-Web use a merge queue: press **Merge when ready**. The
     queue reruns the required checks on the newest `main` and squashes the PR itself.
   - AA-CIS-Infra and the root repo: press **Squash and merge**.
3. The merge starts the app's deploy workflow when the PR touched its paths:

   | Repo | Workflow (Actions tab) | What it deploys |
   |---|---|---|
   | AA-CIS-App | `Deploy Dev` | ECS `aa-cis-dev-api` and `aa-cis-dev-worker` (same image) |
   | AA-CIS-App | `Deploy Admin Dev` | ECS `aa-cis-dev-admin` |
   | AA-Booking | `Deploy Dev`, `Deploy Admin Dev` | ECS `aa-booking-dev-api`, `aa-booking-dev-admin` |
   | AA-Partner | `Deploy Dev`, `Deploy Web Dev` | ECS `aa-crm-dev-api`, `aa-crm-dev-web` |
   | AA-TripPlanner-Web | `Deploy Lambdas`, `Deploy Web Dev` | Lambdas `aa-tripplanner-dev-browse` and `-assembly`, ECS `aa-tripplanner-dev-web` |

   To redeploy the current `main` without a merge, open the workflow, press **Run workflow**, branch `main`.
4. Verify: the workflow is green, its `verify` job is green, and the health endpoint shows the merged commit.

   ```bash
   curl -s https://api-cis.lumiguides.it.com/health
   curl -s https://api-booking.lumiguides.it.com/booking/health
   curl -s https://partner-dev.lumiguides.it.com/crm/health
   curl -s https://tripplanner.lumiguides.it.com/api/health
   ```

   Expected: `"git_sha"` starts with the merge commit of step 2. `/health/ready` (CIS), `/booking/health/ready` and
   `/crm/health/ready` answer 200.
5. Abort: a deploy that never becomes healthy is rolled back by the ECS circuit breaker by itself. A deploy that is
   healthy but wrong: go to [Roll back](#roll-back).

An AA-CIS-Infra merge deploys nothing. Terraform changes reach AWS only when someone runs the `Terraform Apply Dev`
workflow from `main` after reading the plan on the PR ([rollback-terraform](runbooks/rollback-terraform.md) has the
way back).

## Roll back

Roll back the app first, fix on `main` second. The database does not roll back with the app: migrations only go
forward, so an older build must work on the newer schema.

| What broke | Runbook | Short path |
|---|---|---|
| CIS api or worker | [rollback-cis](runbooks/rollback-cis.md) | point both services at the newest older revision with the same older image; `/health` shows the older SHA |
| Booking, CRM api or web, TripPlanner web, CIS or Booking admin | [rollback-ecs](runbooks/rollback-ecs.md) | `bash tools/ops/ecs_rollback.sh <service> --previous` (dry run), then add `--apply`; or the plain `aws ecs update-service` line in the runbook |
| TripPlanner Lambdas | [rollback-tp-lambda](runbooks/rollback-tp-lambda.md) | path A: revert the PR on `main`, `Deploy Lambdas` runs; path B: the previous zip version from S3 |
| A Terraform apply | [rollback-terraform](runbooks/rollback-terraform.md) | revert the Infra PR, read the plan, run `Terraform Apply Dev` |

The ECS rollback is one line when you know the revision from [Before any write](#before-any-write):

```bash
aws ecs update-service --cluster aa-cis-dev-cluster --service <service> --task-definition <service>:<previous-revision> --profile aa365-admin --region us-west-1 --query "service.deployments[0].rolloutState" --output text # WRITE
```

`<service>` is the ECS service name from the table in [Deploy](#deploy-a-change); `<previous-revision>` is the
revision you wrote down. Expected `IN_PROGRESS`, then `COMPLETED` within about 5 minutes and the older `git_sha` on
health. For CIS move the api and the worker to revisions with the same image (rollback-cis step 2). Then revert the
bad PR on `main`; the next deploy moves the service forward on its own.

## Apply a migration

Normal flow, no person needed: the owner repo merges a migration-only PR, the `Migration Sync (owner copies)` workflow
of AA-CIS-Infra opens the copy PR, and `Migration Apply (expand auto-apply)` (hourly, at :37) applies pending expand
and contract files once every job table is idle.

A person steps in when Migration Apply lists a file as stopped (its summary and the copy PR say why), or for a
`-- migrate: destructive` file:

1. Merge the copy PR on AA-CIS-Infra if it is still open (**Squash and merge** after its checks are green).
2. In AA-CIS-Infra **Actions**, open `DB Migrate (shared RDS)`, **Run workflow** on `main` with `environment` `dev`,
   `mode` `check` and `migration` `<owner>/<NNN>_<name>.sql` (the copy's path under `db/migrations/`). Expected: the
   summary shows the owner's role, the version not registered yet and every job table idle.
3. Run it again with `mode` `apply`. Expected: green; the version key is registered; the DB Schema Dump PR appears in
   the root repo. Merge that PR.
4. Abort: if `check` shows a busy job table or another owner's role, stop. After `apply` there is no rollback, only a
   new forward migration ([db-migrate](runbooks/db-migrate.md), [restore one schema](runbooks/restore-schema.md)).

## Sign in when nobody can

If no staff member can sign in to the CIS admin, use the break-glass admin ([break-glass](runbooks/break-glass.md),
path A). Every use sends an alert by design and is followed by a password rotation
([secret rotation](runbooks/secret-rotation.md), class 4).

## Rotate a key

Rotate first and investigate second when a secret may have leaked; otherwise follow the schedule in the
[secrets register](../security/secrets-register.md) (each row has its class and next due date).

1. Find the row of the secret in the [secrets register](../security/secrets-register.md): its class, its store and
   every copy (`copy_of`). A copy that is not updated breaks the app that reads it.
2. Follow the class in [secret rotation](runbooks/secret-rotation.md):
   - class 1, app keys in Secrets Manager: write the new value in the Secrets Manager console (**Retrieve secret
     value**, **Edit**; never read or paste the old one), then redeploy the app that reads it (its deploy workflow,
     **Run workflow** on `main`), because tasks read secrets at start;
   - class 2, database logins: the new DSN in the console, then AA-CIS-Infra `DB Migrate (shared RDS)` with `mode`
     `set-password` for that role;
   - class 4, break-glass: `breakglass-init` with the MFA admin profile (AA-CIS-Infra `tools/identity/`);
   - class 6, tokens outside AWS: create the new token with the same scope, store it as the GitHub secret (the
     runbook's one-liner reads the value on stdin), run the workflow that uses it, then revoke the old token;
   - class 7, the CRM KMS keys: no manual step (AWS rotates the key material yearly); an agency's data keys are
     rotated only from an operator entry point that does not exist yet (the [security tabletop](drills/security-tabletop.md)
     part C explains why).
3. Verify with the app's health endpoint (section [Deploy](#deploy-a-change)) and, for a database login, a `DB Migrate`
   `mode` `check` run.
4. Write the date into the register row (names and dates, never values).

## Handle an incident

The full page is [incident response](incident-response.md). Without the agent the order stays the same:

1. **Confirm** on the live URL with `curl` and read the alarm e-mail (or the Slack card, once the
   [second alert channel](runbooks/chat-alert-channel.md) is on). Note the start time.
2. **Stop the bleeding** with the matching page of the [operations index](README.md#something-is-wrong): a bad deploy
   is a [rollback](#roll-back); a leaked secret is a [rotation](#rotate-a-key); a runaway job or cost is the
   [queue stuck](playbooks/queue-stuck.md) or [cost spike](playbooks/llm-cost-spike.md) playbook.
3. **Freeze** merges to the affected repo until it is stable.
4. **Write it down** in a Linear issue `[Incident] <short title>` with times; commands and outputs, never secret values.
5. **Tell people** with the table below.

## Who calls whom

The business owner is the second on-call person (root decision sec-Q16). The printable card is in the
[security tabletop](drills/security-tabletop.md#part-a-who-calls-whom-10-minutes).

| When | Who acts | Within |
|---|---|---|
| A page alert arrives | the tech lead acknowledges in the alerts channel and starts | 15 minutes |
| No acknowledgement | the business owner phones the tech lead, then again with a Zalo message | 30 minutes from the alert |
| SEV1 confirmed | the tech lead tells the business owner, who decides on tenant notice | 30 minutes |
| Tenants affected | the business owner words it, the tech lead sends it | 2 hours |

Alerts reach the e-mail inboxes today; the Slack channel and the business owner's page-alert subscription are switched
on with [turn on the second alert channel](runbooks/chat-alert-channel.md).

## What the agent does that you now do yourself

- Read the PR checks and the Terraform plan before merging; merge the DB Schema Dump PR after a migration.
- Check `/health` and `/health/ready` after every deploy; compare `git_sha` with the merge commit.
- Write what you did into the session log or the incident record ([incident response](incident-response.md)).

## Escalation

Severity and who to tell: [incident response](incident-response.md). Account access problems: the
[access register](../security/access-register.md) names the second key-holder of each account by role, and the
[second key-holder checklist](../security/second-key-holder-checklist.md) is how that access is tested.
