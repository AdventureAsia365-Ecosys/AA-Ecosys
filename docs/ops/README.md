---
id: OPS-01
title: Operations index
description: Start page for running the ecosystem on Dev - every runbook and playbook across the repos, how each app is deployed and rolled back, and the CI/CD matrix.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-19
review_every_days: 90
related: [CAT-00, OPS-04, APP-01, APP-02, OPS-05, OPS-06, APP-09, skill/aa-ship/SKILL.md, AA-892]
---

# Operations index

Everything runs on **acc2** (us-west-1) except the LLM satellite accounts; see the
[account map](../onboarding.md#account-map). Start every AWS session with
`aws sts get-caller-identity --profile aa365-admin`. Nghiệp is on call for everything during the dev phase.

> [!NOTE]
> Runbooks marked `draft` with an UNTESTED banner have not been run end to end. Read every step before using one in an
> incident. Each page's front-matter has `last_tested`, `tested_where` and `tested_evidence`.

## Something is wrong

1. [Incident response](incident-response.md): severity, who to tell, the first 15 minutes.
2. Pick the playbook:

| Symptom | Playbook |
|---|---|
| 5xx, timeouts, an API alarm, a broken page | [5xx spike](playbooks/5xx-spike.md) |
| Jobs not starting or never finishing, a deploy blocked by the gate | [Job queue stuck](playbooks/queue-stuck.md) |
| A budget or anomaly e-mail, a job `stopped_budget` | [LLM or paid-API cost spike](playbooks/llm-cost-spike.md) |
| Staff cannot sign in | [Staff cannot sign in (Cognito)](playbooks/cognito-login.md) |
| SES bounce or complaint alarm | [SES bounce or complaint](runbooks/ses-bounce.md) |

## Runbooks

| Runbook | Status | Last tested |
|---|---|---|
| [Roll back the CIS API and worker](runbooks/rollback-cis.md) | active | 2026-10-17 drill |
| [Roll back the Booking API](runbooks/rollback-booking.md) | draft, UNTESTED | read-only only |
| [Roll back a Vercel deployment](runbooks/rollback-vercel.md) | draft, UNTESTED | - |
| [Roll back the TripPlanner Lambdas](runbooks/rollback-tp-lambda.md) | draft, UNTESTED | read-only only |
| [Roll back a Terraform change](runbooks/rollback-terraform.md) | draft, UNTESTED | read-only only |
| [Override a deploy or migration gate](runbooks/deploy-gate-override.md) | draft, UNTESTED | - |
| [Query the database through ECS exec and S3](runbooks/ecs-exec-s3-mediated.md) | draft (tested) | 2026-10-17 |
| [Run DB Migrate](runbooks/db-migrate.md) | draft (tested) | 2026-10-18 |
| [Run and read the DB isolation probe](runbooks/isolation-probe.md) | draft (tested) | 2026-10-19 |
| [Restore the shared RDS to a point in time](runbooks/restore-rds-pitr.md) | draft (tested) | 2026-10-17 drill |
| [Restore one schema or table](runbooks/restore-schema.md) | draft, UNTESTED | - (AA-829) |
| [Rotate a secret](runbooks/secret-rotation.md) | draft, UNTESTED | two classes once |
| [Switch off the legacy staff password login](runbooks/legacy-login-flag.md) | draft, UNTESTED | readiness read only |
| [Use a break-glass path](runbooks/break-glass.md) | draft, UNTESTED | API path 2026-10-18 |
| [Handle an SES bounce or complaint alarm](runbooks/ses-bounce.md) | draft, UNTESTED | read-only only |
| Data subject request (manual delete/export) | planned (AA-839, D-11) | - |
| Disaster recovery overview (`dr.md`) | planned (AA-829 / AA-880) | - |

"draft (tested)" = the steps ran on Dev, but Nghiệp has not read the page yet ([STYLE](../STYLE.md#runbooks-and-tested)).
Drills and their evidence: [drill index](drills/README.md).

## Registers

- [Database operations index](database-operations.md)
- [Feature-flag register](feature-flags.md)
- [Job-kind register and kill switches](job-kinds.md)
- Alarm catalog: generated in AA-CIS-Infra (AA-893, planned). Until then:
  `aws cloudwatch describe-alarms --profile aa365-admin --region us-west-1 --query "MetricAlarms[].[AlarmName,StateValue]" --output table`
  (65 alarms on 19/10/2026; the `TargetTracking-…-AlarmLow-…` ones are autoscaling signals and sit in ALARM normally).
- Secrets register: `docs/security/secrets-register.md` (AA-878).

## Runbooks in other places

| Where | What |
|---|---|
| `skill/aa-ship/SKILL.md` | PR to Done: checks before merge, deploy guard, live verify, Done evidence (rollback moved here) |
| `skill/aa-cis-schema/references/destructive-ops.md` | DRY RUN procedure for deleting tables or data |
| `skill/aa-wave-rerun/SKILL.md` | Re-running the A1-A3 pipeline for a country (waves, pilot, counting) |
| `skill/aa-ui-verify/SKILL.md` | UI verification on a Vercel preview |
| AA-CIS-Infra `db/README.md`, `db/scripts/README.md` | DB Migrate internals, owners registry, run-script contract |
| AA-CIS-Infra `tools/identity/` | Cognito bootstrap and break-glass tool |
| AA-CIS-Infra `docs/ci-role-split.md` | CI roles: which workflow assumes which IAM role |

## How each app is deployed (APP-01)

| App | Runs on | Deploys when | Gate | Verify | Roll back |
|---|---|---|---|---|---|
| CIS API + worker | ECS `aa-cis-dev-api` + `aa-cis-dev-worker` (same image, ECR `aa-cis-dev-api`, tag `dev-<sha>`, IMMUTABLE, 30 kept) | push to `main` touching the backend paths of `deploy-dev.yml`, or dispatch | `shared.job` deploy gate (fails closed) | `/health` `git_sha`, `/health/ready` 200, both services same SHA | [rollback-cis](runbooks/rollback-cis.md) |
| CIS admin frontend | Vercel `aa-cis-frontend` | PR (preview) / push to `main` (production) touching `frontend/**` | none (UI smoke after deploy) | `aa-ui-verify` | [rollback-vercel](runbooks/rollback-vercel.md) |
| CIS tenant portal | Vercel project for the portal (AA-885, being set up) | `vercel-deploy-portal.yml` | none | portal UI smoke | [rollback-vercel](runbooks/rollback-vercel.md) |
| Booking API | ECS `aa-booking-dev-api` (ECR `aa-booking-dev-api`, tag = git SHA, IMMUTABLE, 10 kept) | push to `main` touching the backend, or dispatch | `booking.job` gate over GitHub OIDC | `/booking/health` `git_sha`, `/booking/health/ready` | [rollback-booking](runbooks/rollback-booking.md) |
| Booking admin frontend | Vercel `aa-booking-admin` | PR / push to `main` touching the frontend | none | page check | [rollback-vercel](runbooks/rollback-vercel.md) |
| TripPlanner Lambdas | `aa-tripplanner-dev-browse`, `aa-tripplanner-dev-assembly` (zip in a versioned S3 bucket, `--publish`, no alias) | push to `main` touching `backend/**`, or dispatch | none | `/api/browse?resource=countries` 200 | [rollback-tp-lambda](runbooks/rollback-tp-lambda.md) |
| TripPlanner frontend | Vercel `aa-tripplanner` | PR / push to `main` touching `frontend/**` | none | home page 200 | [rollback-vercel](runbooks/rollback-vercel.md) |
| Infrastructure | Terraform root `accounts/aa365` (state in S3, versioned) | dispatch `terraform-apply.yml` from `main` after merge | plan on the PR; bootstrap roles by hand with MFA | plan shows no changes | [rollback-terraform](runbooks/rollback-terraform.md) |
| DB migrations | DB Migrate on AA-CIS-Infra `main` | dispatch `check` then `apply` | idle check over every owner job table | version in `shared.schema_versions`, `/health/ready` | forward only ([DB Migrate](runbooks/db-migrate.md)) |

Merge rules: during the dev phase the agent merges and verifies its own PRs, including infra and security (D-13
addendum); the risk-based human gate (Terraform, migrations, auth, data deletion) starts with prod or the first paying
tenant. The written standard DM-11.5 still says otherwise until data standards v1.1 (AA-889, N-1).

## CI/CD matrix (APP-02)

Read from each repo's `.github/workflows/` on `main`, 19/10/2026.

| Repo | Workflow | Trigger | Jobs | Notes |
|---|---|---|---|---|
| AA-CIS-App | `ci.yml` | PR to `main`; push to `main`, `feature/**` | Lint, Security Audit, Unit Tests, Integration Tests, Docker Build Check, Frontend Lint, Portal Lint | the first five are required by branch protection |
| AA-CIS-App | `deploy-dev.yml` | push to `main` (backend paths); dispatch (`override_running_jobs`) | Pre-deploy job guard, Build and Push ECR, Deploy to ECS Dev | concurrency `deploy-dev-cis`, never cancelled |
| AA-CIS-App | `vercel-deploy.yml` | PR / push `main` (`frontend/**`); dispatch | Vercel deploy, UI smoke | Git integration off; Hobby cap about 100 deployments a day for the team |
| AA-CIS-App | `vercel-deploy-portal.yml` | PR / push `main` (portal paths); dispatch | Vercel deploy (portal), UI smoke (portal) | AA-885 |
| AA-CIS-App | `ui-smoke.yml`, `ui-smoke-portal.yml` | called by the deploy workflows; dispatch | Playwright smoke | |
| AA-CIS-App | `eval-regression.yml` | dispatch only | Run eval regression gate | by hand on the golden set (D-23); per-PR trigger only if N-4 is approved |
| AA-Booking | `ci.yml` | PR to `main`; push `main` | Lint, Security Audit, Unit Tests, Integration Tests, Docker Build Check, Vendored CIS copies, Frontend Build | |
| AA-Booking | `deploy-dev.yml` | push to `main` (backend paths); dispatch (`override_running_jobs`) | Deploy configuration, Pre-deploy job guard, Deploy to ECS Dev | live smoke on `/booking/health` + `/ready` |
| AA-Booking | `vercel-deploy.yml` | PR / push `main` (frontend paths); dispatch | Vercel deploy | |
| AA-TripPlanner-Web | `ci.yml` | PR to `main`; push `main`, `task/**`, `chore/**`, `feature/**` | Backend (pytest), Migrations (lint, PG 15 replay), Frontend (lint + build) | |
| AA-TripPlanner-Web | `deploy-lambdas.yml` | push to `main` (`backend/**`); dispatch | Build + deploy Lambda code | deploy role trusts `main` only |
| AA-TripPlanner-Web | `vercel-deploy.yml` | PR / push `main` (`frontend/**`); dispatch | Vercel deploy | |
| AA-CIS-Infra | `terraform-plan.yml` | PR to `main` | Terraform Plan (dev) | plan comment on the PR |
| AA-CIS-Infra | `terraform-apply.yml` | dispatch from `main` | Terraform Apply (prod) | GitHub environment `prod` = Dev resources (rename: AA-880, D-16) |
| AA-CIS-Infra | `db-migrate.yml` | dispatch from `main` | Migrate | modes check / apply / set-password / run-script |
| AA-CIS-Infra | `db-schema-dump.yml` | nightly 03:43 UTC; after each apply; dispatch | Dump schema, regenerate reference | opens the root PR `bot/db-schema-reference` |
| AA-CIS-Infra | `db-isolation-probe.yml` | nightly 04:13 UTC; after each apply; dispatch | Isolation probe | read-only |
| AA-CIS-Infra | `migration-copy-guard.yml` | PR (migration paths); nightly 02:17 UTC; dispatch | Copies match owner main, Migration lint and unique numbers | |
| AA-CIS-Infra | `secret-scan.yml` | PR to `main`; push `main`; nightly 19:23 UTC; dispatch | gitleaks (PR lines), gitleaks full history | full history: every branch, tag and PR head, baseline in `.gitleaksignore`; PR scan uses the base commit rules (AA-981) |
| AA-CIS-Infra | `identity-triggers-test.yml`, `ops-probe-test.yml`, `rds-snapshot-expiry-test.yml`, `secrets-register-check-test.yml` | PR / push `main` (their paths) | unit tests of the Lambdas and tools | |
| AA-Ecosys (root) | `docs-lint.yml` | PR to `master` (docs paths); weekly Monday 01:17 UTC; dispatch | Docs lint, Docs freshness report | AA-888 |
| AA-Ecosys (root) | `contracts.yml` | PR to `master` (contracts, ADR and tool paths); dispatch | Contracts and ADR numbers | |
| AA-Ecosys (root) | `secret-scan.yml` | PR to `master`; push `master`; nightly 19:41 UTC; dispatch | gitleaks (PR lines), gitleaks full history | same rules as Infra (AA-981) |

Scheduled jobs outside GitHub: the ops-probe Lambda `aa-cis-dev-dfs-balance-check` (EventBridge schedules; the daily
06:15 UTC run calls the DataForSEO balance check, the Jev canary (a real paid call), the Jev 402 sweep, the wave check and
the staff directory reconcile; a second schedule enqueues the retention kinds) and the snapshot-expiry Lambda
`aa-cis-dev-rds-snapshot-expiry`. Never invoke the ops probe with an empty event by hand: it runs the paid canary.

## Prod

No prod environment exists. The prod blueprint, readiness checklist and environment naming (PROD-01) belong to AA-880 /
ADR 0012 (D-16, D-17: prod on acc2 when go-live is dated).
