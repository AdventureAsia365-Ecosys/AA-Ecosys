---
id: GUIDE-05
title: DevOps guide
description: For whoever runs AA-Ecosys day to day - environments, how each app deploys, DB Migrate, the deploy gate, alarms and runbooks, incidents, backups, secrets, cost guardrails and a light on-call routine.
type: tutorial
status: draft
owner: nghiep
audience: [devops, engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-19
review_every_days: 90
related: [GUIDE-01, OPS-01, OPS-04, OPS-03, SEC-02, FIN-01, AA-897, AA-892]
---

# DevOps guide

How the whole delivery system works: [engineering handbook](../engineering-handbook.md).

## Who this is for

You keep AA-Ecosys running: deploys, migrations, alarms, incidents, backups, secrets and cost. You know AWS, GitHub
Actions and Terraform. After this page you know how each app reaches Dev, which gates protect it, where each
runbook lives and what to check every day, week and month. Exact steps live in the runbooks; this page only routes
you to them.

First get your access from [Onboarding](../onboarding.md) (account map, AWS profile with MFA, single-line CLI).

## Environments

| Environment | Where | Data | State |
|---|---|---|---|
| **Dev** | acc2, us-west-1 (see [account map](../onboarding.md#account-map)) | **Test data only** (D-01) | Live; the only environment |
| Prod | acc2, separate RDS instance (ADR 0001, C7.2a, D-17) | Real | Not created; dated at go-live (AA-880, ADR 0012 to come) |

The GitHub environment that gates Terraform apply is called `prod` but applies Dev. Renaming it belongs to the prod
blueprint (AA-880, D-16, C7.2d), not to now.

Live components on Dev (checked 2026-10-19): ECS cluster `aa-cis-dev-cluster` with services `aa-cis-dev-api`,
`aa-cis-dev-worker` and `aa-booking-dev-api`; RDS `aa-cis-dev-db` (PostgreSQL, `db.t4g.small`, single-AZ, 7-day
PITR); Lambdas `aa-tripplanner-dev-browse` and `aa-tripplanner-dev-assembly`; Cognito trigger Lambdas; the daily
probe Lambda `aa-cis-dev-dfs-balance-check`; the snapshot expiry Lambda `aa-cis-dev-rds-snapshot-expiry`.

## How each app deploys

| App | Backend path | Frontend path | Gate |
|---|---|---|---|
| CIS | Merge to `main` → `Deploy Dev` (`deploy-dev.yml`): image `dev-<sha>` to ECR (immutable tags), new task definitions for api **and** worker on the same image | `vercel-deploy.yml` (admin, `aa-cis-frontend`) and `vercel-deploy-portal.yml` (portal, `aa-cis-portal`), each followed by a Playwright UI smoke | Refuses while `shared.job` has queued or running work |
| Booking | Merge to `main` → `Deploy Dev`: image tagged with the git SHA, role `aa-booking-dev-app-deploy`, smoke `/booking/health` (same `git_sha`) and `/booking/health/ready` | `vercel-deploy.yml` (`aa-booking-admin`) | Asks `/booking/ops/deploy-gate` whether `booking.job` is idle |
| TripPlanner | Merge to `main` touching `backend/**` → `deploy-lambdas.yml`: zip to the artifacts bucket, `UpdateFunctionCode` on both Lambdas | `vercel-deploy.yml` | None (no job table yet, AA-861) |
| Infra | PR → **Terraform Plan** (required) → merge → **Terraform Apply Prod** run by hand (`workflow_dispatch` on `main`) | - | Plan read in the PR; OIDC trust only for `refs/heads/main` |

Boundary: *apps own code, Infra owns resources*. Infra creates the ECS services, Lambdas and roles; the apps ship
code into them. Bootstrap IAM roles and policies, and the `accounts/acc1-bedrock` and `accounts/acc3-bedrock` roots,
are applied by a human with the MFA profile, never by CI.

Vercel's Git integration is off in every repo; CI creates deploys with `VERCEL_TOKEN`, and only when frontend files
change.

The full pre-merge checklist, the live verify and the rollback commands are in `skill/aa-ship/SKILL.md` until the
rollback runbooks move to `docs/ops/runbooks/` (AA-892).

## DB Migrate

The RDS is private, so migrations run as a one-off Fargate task started by Infra's `db-migrate.yml`. Order and
rules: Infra `README.md` "DB Migrate" and [schema ownership](../database/schema-ownership.md).

| Mode | Does | Who runs it |
|---|---|---|
| `check` | Report only for one file (input `migration`): owner, busy job tables | Anyone, before `apply` |
| `apply` | Runs that one file as the live owner role of its schema and checks its version is registered; RDS snapshot first when the header says `-- migrate: destructive` | After the Infra copy PR merges |
| `set-password` | Sets the password of `cis_app` or `db_migrator` from its DSN secret and tests the login, without printing it | X1 role work |
| `run-script` | Runs a reviewed `db/scripts/<name>.py` from `main` inside the VPC, as the master | Reviewed one-off tasks |

`apply` waits, then refuses (exit 7) while any owner job table has queued or running work or a rerun wave is open.
The input `override_busy_jobs=<reason>` is Nghiệp's call only. After `apply`, **DB Schema Dump** regenerates
[`db-schema-reference.md`](../architecture/db-schema-reference.md) through a root PR; **DB Isolation Probe** runs nightly
and on demand.

## Alarms, runbooks and incidents

- CloudWatch alarms (about 65 on acc2) e-mail through SNS on ALARM **and** on OK (D-20). Main ones: CIS API 5xx and
  p95 latency, ECS health, RDS connections and storage, Booking, TripPlanner Lambda errors, job health, SES, Cognito
  (14), log-write failures of the cost ledgers.
- `TargetTracking-...-AlarmLow` alarms belong to ECS auto scaling and sit in ALARM on an idle Dev; that is normal.
- Sentry: CIS backend and frontend errors, one uptime monitor on CIS `/health` (free plan). Booking and TripPlanner
  rely on AWS alarms until AA-871.
- Every alarm will name its runbook (AA-893). Start at the operations index [`ops/README.md`](../ops/README.md)
  (AA-892): rollback per app, restore, break-glass, isolation probe, feature flags, job kinds.
- Incidents: [incident response](../ops/incident-response.md) - severity, first 15 minutes, who is told. Nghiệp is on
  call for everything during the dev phase.

Logs: `/ecs/aa-cis-dev` (api stream prefix `api/`), `/ecs/aa-booking-dev`, `/aws/lambda/<function>`. App logs are
kept 30 days; security logs (VPC flow, WAF, ECS exec sessions, PostgreSQL) 365 days (D-09, AA-872).

```bash
aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-api aa-cis-dev-worker aa-booking-dev-api --profile aa365-admin --region us-west-1 --query "services[].[serviceName,deployments[0].rolloutState,runningCount]" --output text
aws cloudwatch describe-alarms --state-value ALARM --profile aa365-admin --region us-west-1 --query "MetricAlarms[].AlarmName" --output text
```

## Database access

Humans and agents reach the database only through the **S3-mediated ECS exec** pattern over SSM: upload a Python
script to the scripts bucket, presign it, run it in the CIS `api` container with `python3` and `asyncpg`
(`skill/aa-cis-schema/references/ecs-exec.md`). Never SSH, never a public endpoint, never a laptop `psql`. Every
session is logged for 365 days. Deleting data follows the DRY RUN procedure
(`skill/aa-cis-schema/references/destructive-ops.md`).

## Backups and restore

- RDS automated backups: 7-day point-in-time recovery on Dev (prod will keep 14, data standards DM-9.6).
- Manual snapshots expire after 30 days (daily Lambda at 22:00 UTC), unless named `keep-` or tagged to retain.
- A full PITR restore drill passed on 2026-10-17 in about 22 minutes
  (`docs/audits/2026-10-17-S241-restore-drill/`). The single-schema restore runbook is still open (AA-829).
- Drill cadence (DM-9.3): on Dev, again when the procedure changes and once before prod; quarterly from prod.
  Evidence goes to `docs/audits/<date>-S<nnn>-<slug>/`.

## Secrets

- Secrets Manager names follow `<app>/<env>/<purpose>` (`booking/dev/database-url`); legacy CIS names such as
  `aa-cis/dev/rds` stay (DM-8.6). Each app's role reads only its own prefix.
- The secrets register (owner, consumer, rotation trigger) is `docs/security/secrets-register.md` (AA-878, in
  review), with a monthly drift check.
- Rotate when a secret may be exposed, at go-live and after break-glass use (D-02, D-03, DM-8.9). There is no
  90-day rotation cycle on Dev.
- Never print a secret value. Environment variable names with underscores are edited by Nghiệp by hand.

## Cost guardrails

Rules: data standards [DM-10](../architecture/data-standards/02-data-management.md#10-cost-ownership). In practice:

- AWS Budgets on acc2: 250 USD per month total, plus per `App` tag (CIS 150, shared 50, Booking 25, TripPlanner 25).
- Every paid model or data call goes through its ledger (`shared.llm_call_log`, `decision_log`, `dfs_call_log`);
  ad-hoc scripts use `stage=adhoc_<issue>`.
- Paid batches: trial about 3 items, then at most about 50 tours, never the whole catalog without approval.
- New AWS resources: state the monthly cost in the PR and get approval first (D-19); tag `App` and the existing
  `Environment` tag.
- Process and the monthly cost and capacity review: `docs/ops/finops.md` (AA-896).

## On-call light routine

| Cadence | Check | Where |
|---|---|---|
| Daily (start of session) | `aws sts get-caller-identity`; api and worker run the same commit; `shared.job` queued/running; alarm e-mails since yesterday | CIS admin → Platform → Apps; commands above |
| Daily | Time-gated checks due today | [Live backlog](../backlog/README.md) §1 |
| Weekly | Merge grouped Dependabot PRs; look at open CodeQL alerts; Sentry new issues | GitHub, Sentry |
| Weekly | Snapshot expiry e-mails (only sent when it deletes or finds a problem) | SNS mail |
| Monthly (first session) | Cost and capacity review, secrets register drift check, `pip-audit` ignore-list expiry dates | `docs/audits/<date>-S<nnn>-capacity-review/`, AA-878 |
| Quarterly (first session) | Access review: DB roles and grants, IAM roles that read DB secrets, Cognito staff users (DM-8.10) | `docs/audits/<date>-S<nnn>-access-review/` |
| Before prod | Prod readiness checklist: token and RDS master rotation, restore drill, SLOs, second alert channel | AA-880 |

## Where truth lives

| Question | Open |
|---|---|
| What runs where, which roles | [Ecosystem architecture](../ecosystem-architecture.md), Infra `CONTEXT.md` |
| How to deploy or roll back an app | `skill/aa-ship/SKILL.md`; later [`ops/README.md`](../ops/README.md) |
| Migrations | Infra `README.md`, `db/README.md` |
| Data rules | [Data standards](../architecture/data-standards/README.md) |
| What is due | [Live backlog](../backlog/README.md) |

## Escalation

Everything goes to Nghiệp during the dev phase. Ms. Thư is told per the severity table in
[incident response](../ops/incident-response.md).

## Related

- [Onboarding](../onboarding.md), [new engineer guide](new-engineer.md), [CIO guide](cio.md)
- [Glossary](../glossary.md)
