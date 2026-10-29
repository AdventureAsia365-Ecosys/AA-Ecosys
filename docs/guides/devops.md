---
id: GUIDE-05
title: DevOps guide
description: For whoever runs AA-Ecosys day to day - environments, how each app deploys, DB Migrate, the deploy gate, alarms and runbooks, incidents, backups, secrets, cost guardrails and a light on-call routine.
type: tutorial
status: draft
owner: nghiep
audience: [devops, engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-28
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
| Prod | acc2, its own VPC, RDS instance, cluster, Cognito pools, secrets and roles (ADR 0001, C7.2a, D-17; [ADR 0012](../adr/0012-environment-model.md) decisions 2–3) | Real | Not created; built when a go-live date is set ([ADR 0012](../adr/0012-environment-model.md), accepted S257; AA-880) |

The GitHub environment that gates Terraform apply is called `prod` but applies Dev. ADR 0012 decision 6 renames it
to `dev` in phase 1, before any prod role exists, in a fixed four-step order (C7.2d); until that Infra PR lands, the
name stays `prod`. Prod Terraform will be its own root, `accounts/aa365-prod` (decision 5, C7.2c).

Live components on Dev (checked 2026-10-28): ECS cluster `aa-cis-dev-cluster` with services `aa-cis-dev-api`,
`aa-cis-dev-worker`, `aa-booking-dev-api`, `aa-crm-dev-api`, `aa-crm-dev-web` and `aa-crm-dev-portal`; RDS
`aa-cis-dev-db` (PostgreSQL, `db.t4g.small`, single-AZ, 7-day PITR); Lambdas `aa-tripplanner-dev-browse` and
`aa-tripplanner-dev-assembly`; four Cognito trigger Lambdas (`aa-identity-dev-*`); the daily probe Lambda
`aa-cis-dev-dfs-balance-check`; the snapshot expiry Lambda `aa-cis-dev-rds-snapshot-expiry`. The AI models run on
Amazon Bedrock in acc3; acc1 (a personal account) was removed from the ecosystem on 2026-10-28 (AA-998).

## How each app deploys

| App | Backend path | Frontend path | Gate |
|---|---|---|---|
| CIS | Merge to `main` → `Deploy Dev` (`deploy-dev.yml`): image `dev-<sha>` to ECR (immutable tags), new task definitions for api **and** worker on the same image | `vercel-deploy.yml` (admin, `aa-cis-frontend`), followed by a Playwright UI smoke. The portal is no longer deployed from here (AA-979, CIS #997) | Refuses only while a rerun wave is open or a deploy-blocking kind (`data_erasure`, `s1_batch_ingest`, `writing_memory_r2`, `writing_memory_shadow`) runs or is due within 15 min (C6.3a, AA-993 G5); other queued/running jobs are released and re-claimed by the new task |
| Booking | Merge to `main` → `Deploy Dev`: image tagged with the git SHA, role `aa-booking-dev-app-deploy`, smoke `/booking/health` (same `git_sha`) and `/booking/health/ready` | `vercel-deploy.yml` (`aa-booking-admin`) | Asks `/booking/ops/deploy-gate`; refuses only while a retention job (`bk_retention_job`, `bk_retention_inbox_redact`) runs or is due within 15 min (C6.3a, AA-993 G5) |
| TripPlanner | Merge to `main` touching `backend/**` → `deploy-lambdas.yml`: zip to the artifacts bucket, `UpdateFunctionCode` on both Lambdas | `vercel-deploy.yml` | None (no job table yet, AA-861) |
| Partner | Merge to `main` touching `api/**` → `Deploy Dev`: image tagged with the git SHA (native arm64), service `aa-crm-dev-api`; `web/**` → `Deploy Web Dev`, service `aa-crm-dev-web` | `portal/**` → `Deploy Portal Dev` (`deploy-portal-dev.yml`): the tenant portal (Content studio) to the Fargate service `aa-crm-dev-portal` behind `portal.lumiguides.it.com`, then post-deploy verify and the portal UI smoke. The Vercel project `aa-cis-portal` and `vercel-deploy-portal.yml` were removed at the AA-979 clean-up (S256): no portal PR preview | The API deploy has the same guard, but no Partner kind blocks a deploy today (`crm_dispatch` stopped blocking in AA-993 G4b); web and portal deploys have no job gate |
| Infra | PR → **Terraform Plan** (read it; Infra has no required checks) → merge → **Terraform Apply Prod** run by hand (`workflow_dispatch` on `main`) | - | Plan read in the PR; OIDC trust only for `refs/heads/main` |

Boundary: *apps own code, Infra owns resources*. Infra creates the ECS services, Lambdas and roles; the apps ship
code into them. Bootstrap IAM roles and policies and the `accounts/acc3-bedrock` root are applied by a human with the
MFA profile, never by CI.

Vercel's Git integration is off in every repo; CI creates deploys with `VERCEL_TOKEN`, and only when frontend files
change.

The full pre-merge checklist and the live verify are in `skill/aa-ship/SKILL.md`. Rollback steps per app are runbooks
in [`ops/runbooks/`](../ops/runbooks/), listed on the [operations index](../ops/README.md) (AA-892).

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
The input `override_busy_jobs=<reason>` is the tech lead's call only. After `apply`, **DB Schema Dump** regenerates
[`db-schema-reference.md`](../architecture/db-schema-reference.md) through a root PR; **DB Isolation Probe** runs nightly
and on demand.

## Alarms, runbooks and incidents

- CloudWatch alarms (94 on acc2, counted 2026-10-28) e-mail through SNS on ALARM **and** on OK (D-20) to the
  recipients on CIS admin → Platform → Alert recipients. Main ones: CIS API 5xx and p95 latency, ECS health, RDS
  connections and storage, Booking, TripPlanner Lambda errors, the CRM api, web and portal, job health, SES, Cognito
  and its WAF, log-write failures of the cost ledgers. The generated list is [alarms](../generated/alarms.md).
- `TargetTracking-...-AlarmLow` alarms belong to ECS auto scaling and sit in ALARM on an idle Dev; that is normal.
- Sentry: CIS backend and frontend errors, one uptime monitor on CIS `/health` (free plan). Booking and TripPlanner
  also report errors to Sentry (AA-871, DSN set on Dev); AA-Partner has the code but no DSN yet.
- Start at the operations index [`ops/README.md`](../ops/README.md) (AA-892): rollback per app, restore, break-glass,
  isolation probe, feature flags, job kinds. Rows of the generated alarm list link the runbook their alarm e-mail
  names, where one is set (AA-893).
- Incidents: [incident response](../ops/incident-response.md) - severity, first 15 minutes, who is told. The tech lead
  is on call for everything during the dev phase.

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
- Full PITR restore drills passed on 2026-10-17 (about 22 minutes, `docs/audits/2026-10-17-S241-restore-drill/`)
  and on 2026-10-23 (about 21 minutes, with a single-schema restore and a repoint of `db.dev.internal`,
  `docs/audits/2026-10-24-S249-restore-drill/`). Runbooks: [PITR restore](../ops/runbooks/restore-rds-pitr.md),
  [single-schema restore](../ops/runbooks/restore-schema.md).
- Drill cadence (DM-9.3): on Dev, again when the procedure changes and once before prod; quarterly from prod.
  Evidence goes to `docs/audits/<date>-S<nnn>-<slug>/`.

## Secrets

- Secrets Manager names follow `<app>/<env>/<purpose>` (`booking/dev/database-url`); legacy CIS names such as
  `aa-cis/dev/rds` stay (DM-8.6). Each app's role reads only its own prefix.
- The secrets register (owner, consumer, rotation trigger) is `docs/security/secrets-register.md` (AA-878, in
  review), with a monthly drift check.
- Rotate when a secret may be exposed, at go-live and after break-glass use (D-02, D-03, DM-8.9). There is no
  90-day rotation cycle on Dev.
- Never print a secret value. Environment variable names with underscores are edited by the tech lead by hand.

## Cost guardrails

Rules: data standards [DM-10](../architecture/data-standards/02-data-management.md#10-cost-ownership). In practice:

- AWS Budgets on acc2: 300 USD per month total, plus per `App` tag (shared 120, CIS 90, CRM 35, Booking 25,
  identity 10, TripPlanner 10; read live 2026-10-28; [FinOps](../ops/finops.md#budgets-and-alerts)).
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
| How to deploy or roll back an app | `skill/aa-ship/SKILL.md`; rollback runbooks on [`ops/README.md`](../ops/README.md) |
| Migrations | Infra `README.md`, `db/README.md` |
| Data rules | [Data standards](../architecture/data-standards/README.md) |
| What is due | [Live backlog](../backlog/README.md) |

## Escalation

Everything goes to the tech lead during the dev phase. The business owner is told per the severity table in
[incident response](../ops/incident-response.md).

## Related

- [Onboarding](../onboarding.md), [new engineer guide](new-engineer.md), [CIO guide](cio.md)
- [Glossary](../glossary.md)
