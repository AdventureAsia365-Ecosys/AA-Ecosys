---
id: GUIDE-05
title: DevOps guide
description: For whoever runs AA-Ecosys day to day - environments, how each app deploys, DB Migrate, the deploy gate, alarms and runbooks, incidents, backups, secrets, cost guardrails and a light on-call routine.
type: tutorial
status: draft
owner: nghiep
audience: [devops, engineer]
applies_to: [ecosystem]
last_reviewed: 2026-11-01
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
| Prod | `aa-prod`, its own AWS account in us-west-1, with its own VPC, RDS instance, cluster, Cognito pools, secrets and roles ([ADR 0018](../adr/0018-lean-aws-account-model.md), accepted S262; C7.2a, D-17; [ADR 0012](../adr/0012-environment-model.md) decision 3) | Real | Not created; built when a go-live date is set ([ADR 0012](../adr/0012-environment-model.md), accepted S257; AA-880) |

The GitHub environment that gates Terraform apply, DB Migrate, the schema dump and the DB probes is `dev` (it was
named `prod` until AA-1023, ADR 0012 decision 6, C7.2d); the Dev apply role trusts only `environment:dev`, so the name
`prod` is free for a future prod apply role. Prod Terraform will be its own root, `accounts/prod`, in the `aa-prod` account (ADR 0018 decision
5, replacing the `accounts/aa365-prod` of ADR 0012; C7.2c).

Live components on Dev. The ECS services, generated from the Terraform state (`tools/docs/gen_sections.py`; never
edit the block by hand):

<!-- gen:ecs-services -->

Cluster `aa-cis-dev-cluster`, 8 services:

| Service | App |
|---|---|
| `aa-booking-dev-admin` | AA-Booking |
| `aa-booking-dev-api` | AA-Booking |
| `aa-cis-dev-admin` | AA-CIS-App |
| `aa-cis-dev-api` | AA-CIS-App |
| `aa-cis-dev-worker` | AA-CIS-App |
| `aa-crm-dev-api` | AA-Partner |
| `aa-crm-dev-web` | AA-Partner |
| `aa-tripplanner-dev-web` | AA-TripPlanner-Web |

From the Terraform state at AA-CIS-Infra `ddf1e36c` (resource inventory, AA-CIS-Infra Docs Gen).

<!-- /gen -->

The rest (checked 2026-11-01): RDS `aa-cis-dev-db` (PostgreSQL, `db.t4g.small`, single-AZ; backup days under [Backups and restore](#backups-and-restore)); Lambdas `aa-tripplanner-dev-browse`,
`aa-tripplanner-dev-assembly` and `aa-tripplanner-dev-jobs` (the `tripplanner.job` worker, woken by a daily
EventBridge Scheduler entry); four Cognito trigger Lambdas (`aa-identity-dev-*`); the daily probe Lambda
`aa-cis-dev-dfs-balance-check`; the snapshot expiry Lambda `aa-cis-dev-rds-snapshot-expiry`. Chat models run behind
the [AI gateway](../architecture/ai-gateway.md), in this provider order (generated from `docs/catalogue/platform.yaml`;
the account roles are in the [ecosystem architecture](../ecosystem-architecture.md)):

<!-- gen:llm-route-order -->

| Model family | Route order (first to last) | Note |
|---|---|---|
| Claude | Anthropic API → acc1 (Bedrock) → acc3 (Bedrock) | acc3 is skipped while Bedrock refuses it |
| GPT | acc1 (Bedrock) → acc3 (Bedrock) → OpenAI API | the OpenAI API serves the twin model last |
| Embeddings | acc2 (Bedrock, Cohere Embed v4) | - |

Decision: ADR 0009 (one gateway for every provider) with ADR 0001a Note S278 (acc1 before acc3). The live routes per stage are in the [LLM routes table](../generated/llm-routes.md) and CIS admin AI providers.

<!-- /gen -->

The management account (ADR 0018) holds the AA organization: OUs, three SCPs on the OUs, the organization trail,
budgets and IAM Identity Center. It runs no workload, and no workload account has joined yet. Its Terraform root is
`accounts/management` in AA-CIS-Infra (bootstrap and apply order in that root's README). Read it with the Identity
Center profile `aa-mgmt` after `aws sso login --sso-session aa-mgmt-sso`; an apply runs only through the GitHub
environment `org` with the tech lead as reviewer.

## How each app deploys

| App | Backend path | Frontend path | Gate |
|---|---|---|---|
| CIS | Merge to `main` → `Deploy Dev` (`deploy-dev.yml`): image `dev-<sha>` to ECR (immutable tags), new task definitions for api **and** worker on the same image | `deploy-admin-dev.yml` (admin on ECS `aa-cis-dev-admin`), followed by a Playwright UI smoke and the visual run. The portal is no longer deployed from here (AA-979, CIS #997) | Refuses only while a rerun wave is open or a deploy-blocking kind (`data_erasure`, `s1_batch_ingest`, `writing_memory_r2`, `writing_memory_shadow`) runs or is due within 15 min (C6.3a, AA-993 G5); other queued/running jobs are released and re-claimed by the new task |
| Booking | Merge to `main` → `Deploy Dev`: image tagged with the git SHA, role `aa-booking-dev-app-deploy`, smoke `/booking/health` (same `git_sha`) and `/booking/health/ready` | `deploy-admin-dev.yml` (admin on ECS `aa-booking-dev-admin`), followed by the public smoke and the visual run | Asks `/booking/ops/deploy-gate`; refuses only while a retention job (`bk_retention_job`, `bk_retention_inbox_redact`) runs or is due within 15 min (C6.3a, AA-993 G5) |
| TripPlanner | Merge to `main` touching `backend/**` → `deploy-lambdas.yml`: zips to the artifacts bucket, `UpdateFunctionCode` on the three Lambdas (browse, assembly, jobs) | `deploy-web-dev.yml` (web on ECS `aa-tripplanner-dev-web` behind CloudFront: verify through the distribution, then the release verify and the visual run) | None: `tripplanner.job` (tp-021) has no deploy-blocking kind, and a Lambda deploy does not interrupt a running invocation |
| Partner | Merge to `main` touching `api/**` → `Deploy Dev`: image tagged with the git SHA (native arm64), service `aa-crm-dev-api`; `web/**` → `Deploy Web Dev`, service `aa-crm-dev-web` | The tenant Content studio is part of the web since AA-1036 (`web/app/(studio)`): `Deploy Web Dev` verifies its paths on `portal.lumiguides.it.com` and runs its UI smoke; `portal/`, `Deploy Portal Dev` and the service `aa-crm-dev-portal` are retired. The Vercel project `aa-cis-portal` went at the AA-979 clean-up (S256) | The API deploy has the same guard, but no Partner kind blocks a deploy today (`crm_dispatch` stopped blocking in AA-993 G4b); the web deploy has no job gate |
| Infra | PR → **Terraform Plan** (read it; the ruleset's required checks are listed below) → merge → **Terraform Apply Dev** run by hand (`workflow_dispatch` on `main`) | - | Plan read in the PR; OIDC trust only for `refs/heads/main` |

Boundary: *apps own code, Infra owns resources*. Infra creates the ECS services, Lambdas and roles; the apps ship
code into them. Bootstrap IAM roles and policies and the `accounts/acc3-bedrock` root are applied by a human with the
MFA profile, never by CI; the `accounts/management` root applies only through its gated GitHub environment.

No frontend deploys to Vercel any more. The CIS and Booking admins left Vercel in S272 (AA-911) and deploy to ECS
with `deploy-admin-dev.yml`; the TripPlanner frontend left in S272 too (AA-1038) and deploys to ECS behind CloudFront
with `deploy-web-dev.yml`.

Release versions on `main` (release-please):

<!-- gen:app-versions -->

| Repo | Release version |
|---|---|
| AA-Booking | `0.17.0` |
| AA-CIS-App | `0.21.0` |
| AA-Partner | `0.14.0` |
| AA-TripPlanner-Web | `0.17.0` |

From each repo's `.release-please-manifest.json` on main (AA-Booking `094d678d`, AA-CIS-App `7b1c8afd`, AA-Partner `28b1c4f6`, AA-TripPlanner-Web `12b6a4d2`); release-please raises it when its release PR merges.

<!-- /gen -->

Required checks before a merge, per repo:

<!-- gen:required-checks -->

| Repo | Branch | Required checks |
|---|---|---|
| AA-Booking | `main` | `Docker Build Check`, `Frontend Build`, `Integration Tests`, `Lint`, `Security Audit`, `Settings Lint`, `Unit Tests`, `Visual (next start, mocked API + kit gallery)`, `gitleaks` |
| AA-CIS-App | `main` | `Docker Build Check`, `Frontend Build`, `Frontend Lint`, `Integration Tests`, `Kit consumers`, `Lint`, `Security Audit`, `Unit Tests`, `Visual (next start, public pages + kit gallery)`, `gitleaks` |
| AA-CIS-Infra | `main` | `Copies match owner main`, `Expand classify`, `Migration lint and unique numbers`, `Terraform Plan (dev)`, `gitleaks` |
| AA-Ecosys | `master` | `Catalogue guard` |
| AA-Partner | `main` | `Docker Build Check`, `Docs lint`, `Integration Tests`, `Lint`, `PR title`, `Security Audit`, `Settings Lint`, `Unit Tests`, `Visual (built in the runner, public pages + kit gallery)`, `Web Build`, `gitleaks` |
| AA-TripPlanner-Web | `main` | `Backend (pytest)`, `Frontend (lint + build)`, `Migrations (lint, PG 15 replay)`, `Security Audit`, `Settings Lint`, `gitleaks` |

Read from GitHub (branch protection and rulesets of the default branch) with `gen_sections.py --write --github`. A check skipped by a path filter counts as passed only where the workflow says so; the merge-queue repos run every required check in the queue.

<!-- /gen -->

The full pre-merge checklist and the live verify are in `skill/aa-ship/SKILL.md`. Rollback steps per app are runbooks
in [`ops/runbooks/`](../ops/runbooks/), listed on the [operations index](../ops/README.md) (AA-892).
The four web frontends (CIS admin, Booking admin, CRM web, TripPlanner web) roll back by themselves when their
post-deploy verify or smoke is red, and open a `deploy-smoke-red` issue (AA-1119,
[rollback-ecs](../ops/runbooks/rollback-ecs.md#automatic-rollback-after-a-red-post-deploy-check)). Since AA-1193
the three API deploys do too (CIS api + worker together, Booking API, CRM API): Deploy Dev re-asks the deploy gate,
rolls back to the revision that ran before the deploy, checks `/health` answers the previous commit and alerts the ops
topic with the failing checks; the dispatch input `drill_force_smoke_fail` runs the drill. TripPlanner merges
through the GitHub merge queue like CIS, Booking and Partner once its ruleset is on (AA-1119).

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

<!-- gen:latest-migrations -->

| Owner | Migration key | Latest applied on Dev |
|---|---|---|
| CIS | `NNN` | `477` |
| TripPlanner | `tp-NNN` | `tp-037` |
| Booking | `bk-NNN` | `bk-071` |
| CRM | `crm-NNN` | `crm-087` |

From the live schema dump of 2026-11-24 ([DB schema reference](../architecture/db-schema-reference.md), refreshed by the DB Schema Dump bot PR). A new migration takes the next number on its owner's main; the owner list is in [schema ownership](../database/schema-ownership.md).

<!-- /gen -->

## Alarms, runbooks and incidents

- CloudWatch alarms e-mail through SNS to the recipients on CIS admin → Platform → Alerts → Recipients: state alarms
  (service down, RDS, NAT recover and instance check, SES, backup copy age, worker liveness, API 5xx rate) on ALARM and
  OK, event alarms (Lambda errors, break-glass token, KMS decrypt anomaly, failed alert delivery) on ALARM only. Each
  carries a `Severity` tag (`page` / `ticket`, [incident response](../ops/incident-response.md#alert-severity-page--ticket));
  page alarms also notify the page topic. The generated list is [alarms](../generated/alarms.md); the full live list
  (alarms, rules, budgets and the in-app checks of CIS, Booking and the CRM, with where each threshold is changed) is
  Platform → Alerts → Catalogue (AA-1171).
- In-app check thresholds are settings (AA-1171): CIS `cis.ops.*` and CRM `crm.ops.*` on Platform → Settings, Booking
  `ops_jobs_*` on its Pricing › Policy page; CloudWatch alarm thresholds stay in Terraform (S287 decision D2).
- S263 alert diet: CloudWatch keeps service down, RDS CPU / storage / connections, Lambda errors, SES and the security
  signals only AWS sees; job queues, per-role connections and log events are in-app checks that e-mail the same topic
  (table: `docs/audits/2026-11-01-S263-alerting-cost/diet.md`). No target-tracking autoscaling on Dev.
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

<!-- gen:backup-days -->

| Backup window (Dev RDS) | Days | Set in AA-CIS-Infra |
|---|---|---|
| Automated backups, point-in-time recovery | 14 | `modules/rds/main.tf` (`backup_retention_period`) |
| Longest any backup copy may live (alarm above it) | 30 | `accounts/aa365/rds_snapshot_expiry.tf` (`rds_backup_copy_max_age_days`) |

Read statically from AA-CIS-Infra main at `8422045d` (tools/docs/repo_facts.py).

<!-- /gen -->

- Prod targets (Multi-AZ, cross-region copy, RPO / RTO): data standards DM-9.6.
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
