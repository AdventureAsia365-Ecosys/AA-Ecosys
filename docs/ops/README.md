---
id: OPS-01
title: Operations index
description: Start page for running the ecosystem on Dev - every runbook and playbook across the repos, how each app is deployed and rolled back, and the CI/CD matrix.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-28
review_every_days: 90
related: [CAT-00, OPS-04, APP-01, APP-02, OPS-05, OPS-06, APP-09, skill/aa-ship/SKILL.md, AA-892]
---

# Operations index

Everything runs on **acc2** (us-west-1) except the LLM calls, which run on acc3; see the
[account map](../onboarding.md#account-map). Start every AWS session with
`aws sts get-caller-identity --profile aa365-admin`. The tech lead is on call for everything during the dev phase.

> [!NOTE]
> Runbooks marked `draft` with an UNTESTED banner have not been run end to end. Read every step before using one in an
> incident. Each page's front-matter has `last_tested`, `tested_where` and `tested_evidence`.

## Something is wrong

1. [Incident response](incident-response.md): severity, who to tell, the first 15 minutes.
2. Pick the playbook:

| Symptom | Playbook |
|---|---|
| 5xx, timeouts, an API or ECS service alarm, a broken page | [5xx spike](playbooks/5xx-spike.md) |
| Jobs not starting or never finishing, a deploy blocked by the gate | [Job queue stuck](playbooks/queue-stuck.md) |
| A budget or anomaly e-mail, a job `stopped_budget` | [LLM or paid-API cost spike](playbooks/llm-cost-spike.md) |
| Staff cannot sign in | [Staff cannot sign in (Cognito)](playbooks/cognito-login.md) |
| LLM calls refused, `llm_access_denied`, Bedrock "Error 002" | [LLM calls refused](playbooks/llm-access-denied.md) |
| SES bounce or complaint alarm | [SES bounce or complaint](runbooks/ses-bounce.md) |

## Runbooks

| Runbook | Status | Last tested |
|---|---|---|
| [Roll back any ECS service (parameterised, `tools/ops/ecs_rollback.sh`)](runbooks/rollback-ecs.md) | draft, UNTESTED | read-only dry run 2026-11-02; [game day plan](drills/rollback-game-day.md) |
| [Roll back the CIS API and worker](runbooks/rollback-cis.md) | active | 2026-10-17 drill |
| [Roll back the Booking API](runbooks/rollback-booking.md) | draft, UNTESTED | read-only only |
| [Roll back a Vercel deployment](runbooks/rollback-vercel.md) | superseded by rollback-ecs (no ecosystem Vercel project left, AA-1038) | - |
| [Move the staff frontends from Vercel to ECS (AA-911, ADR 0019 d23)](runbooks/staff-web-ecs-cutover.md) | draft, UNTESTED | - |
| [Move the TripPlanner frontend from Vercel to ECS behind CloudFront (AA-1038, ADR 0019 d23)](runbooks/tripplanner-web-ecs-cutover.md) | draft, UNTESTED | - |
| [Roll back the TripPlanner Lambdas](runbooks/rollback-tp-lambda.md) | draft, UNTESTED | read-only only |
| [Roll back a Terraform change](runbooks/rollback-terraform.md) | draft, UNTESTED | read-only only |
| [Override a deploy or migration gate](runbooks/deploy-gate-override.md) | draft, UNTESTED | - |
| [Query the database through ECS exec and S3](runbooks/ecs-exec-s3-mediated.md) | draft (tested) | 2026-10-17 |
| [Run DB Migrate](runbooks/db-migrate.md) | draft (tested) | 2026-10-18 |
| [Run and read the DB isolation probe](runbooks/isolation-probe.md) | draft (tested) | 2026-10-19 |
| [Restore the shared RDS to a point in time](runbooks/restore-rds-pitr.md) | draft (tested) | 2026-10-17 drill |
| [Restore one schema or table](runbooks/restore-schema.md) | draft, UNTESTED | - (AA-829) |
| [Restore one tenant's CRM data from its nightly export (pilot drill)](runbooks/pilot-tenant-restore-drill.md) | draft (tested) | 2026-11-05 drill (AA-969 d16) |
| [Onboard a pilot agency (provision, owner, brand, add-ons, AI budget, pilot mode, exit)](runbooks/pilot-agency-onboarding.md) | draft, UNTESTED | - (AA-1086) |
| [Rehearse a pilot with a synthetic agency (13 steps across every app)](runbooks/pilot-rehearsal.md) | draft, UNTESTED | - (AA-1086) |
| [Rotate a secret](runbooks/secret-rotation.md) | draft, UNTESTED | two classes once |
| [Switch off the legacy staff password login](runbooks/legacy-login-flag.md) | draft, UNTESTED | readiness read only |
| [Use a break-glass path](runbooks/break-glass.md) | draft, UNTESTED | API path 2026-10-18 |
| [Handle an SES bounce or complaint alarm](runbooks/ses-bounce.md) | draft, UNTESTED | read-only only |
| [Handle a CRM KMS key alarm](runbooks/crm-keys.md) | draft, UNTESTED | rule patterns only (AA-932) |
| [Plug in and probe the Anthropic API key](runbooks/llm-anthropic-api-key.md) | draft, UNTESTED | - (AA-1002 S2) |
| [Re-embed a vector column into another embedding space](runbooks/embedding-re-embed.md) | draft, UNTESTED | - (AA-1026; T-15 test on `question_embedding` pending) |
| Data subject request (manual delete/export) | planned (AA-839, D-11) | - |
| Disaster recovery overview (`dr.md`) | planned (AA-829 / AA-880) | - |

"draft (tested)" = the steps ran on Dev, but the tech lead has not read the page yet ([STYLE](../STYLE.md#runbooks-and-tested)).
Drills and their evidence: [drill index](drills/README.md).

## Registers

- [Database operations index](database-operations.md)
- [Feature-flag register](feature-flags.md)
- [Job-kind register and kill switches](job-kinds.md)
- [Alarm catalog](../generated/alarms.md): every alarm with its condition and runbook link, generated from Terraform by
  AA-CIS-Infra Docs Gen (AA-893). Live state:
  `aws cloudwatch describe-alarms --state-value ALARM --profile aa365-admin --region us-west-1 --query "MetricAlarms[].[AlarmName,StateValue]" --output table`.
  Since the S263 alert diet only the essential alarms stay (no target-tracking alarms on Dev); job, connection and
  log-event signals are in-app checks (bell + alert e-mail): `docs/audits/2026-11-01-S263-alerting-cost/diet.md`.
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
| CIS API + worker | ECS `aa-cis-dev-api` + `aa-cis-dev-worker` (same image, ECR `aa-cis-dev-api`, tag `dev-<sha>`, IMMUTABLE, 30 kept) | push to `main` touching the backend paths of `deploy-dev.yml`, or dispatch | deploy gate (fails closed): blocks only on an open rerun wave or a running or soon-due `deploy_blocking` kind (AA-993 G5, [job kinds](job-kinds.md)) | `/health` `git_sha`, `/health/ready` 200, both services same SHA | [rollback-cis](runbooks/rollback-cis.md) |
| CIS admin frontend | ECS `aa-cis-dev-admin` (Vercel retired, AA-911 S272) | push to `main` touching `frontend/**` (`Deploy Admin Dev`) | none (UI smoke + visual after deploy) | `aa-ui-verify` | [rollback-ecs](runbooks/rollback-ecs.md) |
| Tenant portal (Content studio) | Part of the agency web `aa-crm-dev-web` behind `portal.lumiguides.it.com` since AA-1036 (R3; source AA-Partner `web/app/(studio)`); the separate service `aa-crm-dev-portal` and `portal/` are retired | AA-Partner: push to `main` touching `web/**` (`deploy-web-dev.yml`), or dispatch | none (the web runs no worker) | post-deploy verify (`crm-web` rows incl. `studio-healthz`, edge checks of the studio paths), studio UI smoke (partner sign-in of the e2e studio user) | [rollback-ecs](runbooks/rollback-ecs.md) (previous `aa-crm-dev-web` revision) |
| CRM API (with the `crm.job` worker) | ECS Fargate ARM64 `aa-crm-dev-api` | AA-Partner: push to `main` touching `api/**` (`deploy-dev.yml`), or dispatch | `crm.job` deploy gate; no blocking kind today | post-deploy verify, `/crm/health` and `/crm/health/ready` | [rollback-ecs](runbooks/rollback-ecs.md) |
| CRM web | ECS Fargate ARM64 `aa-crm-dev-web` | AA-Partner: push to `main` touching `web/**` (`deploy-web-dev.yml`), or dispatch | none (the web runs no worker) | post-deploy verify (`crm-web` rows) | [rollback-ecs](runbooks/rollback-ecs.md) |
| Booking API | ECS `aa-booking-dev-api` (ECR `aa-booking-dev-api`, tag = git SHA, IMMUTABLE, 10 kept) | push to `main` touching the backend, or dispatch | `booking.job` gate over GitHub OIDC: blocks only on a running or soon-due retention kind (AA-993 G5) | `/booking/health` `git_sha`, `/booking/health/ready` | [rollback-booking](runbooks/rollback-booking.md) |
| Booking admin frontend | ECS `aa-booking-dev-admin` (Vercel retired, AA-911 S272) | push to `main` touching the frontend (`Deploy Admin Dev`) | none (public smoke after deploy) | page check | [rollback-ecs](runbooks/rollback-ecs.md) |
| TripPlanner Lambdas | `aa-tripplanner-dev-browse`, `aa-tripplanner-dev-assembly` (zip in a versioned S3 bucket, `--publish`, no alias) | push to `main` touching `backend/**`, or dispatch | none | `/api/browse?resource=countries` 200 | [rollback-tp-lambda](runbooks/rollback-tp-lambda.md) |
| TripPlanner frontend | ECS `aa-tripplanner-dev-web` behind CloudFront (Vercel retired, AA-1038 S272) | push to `main` touching `frontend/**` (`Deploy Web Dev`) | none | `/api/health` on the commit through CloudFront, the WAF challenge checks, release verify | [rollback-ecs](runbooks/rollback-ecs.md) |
| Infrastructure | Terraform root `accounts/aa365` (state in S3, versioned) | dispatch `terraform-apply.yml` from `main` after merge | plan on the PR; plan guard; job-idle gate when the plan touches an ECS service or the RDS instance (AA-1023, override `override_busy_jobs`); bootstrap roles by hand with MFA | plan shows no changes | [rollback-terraform](runbooks/rollback-terraform.md) |
| DB migrations | DB Migrate on AA-CIS-Infra `main` | dispatch `check` then `apply` | idle check over every owner job table (DM-11.4; unlike deploys, `apply` still waits) | version in `shared.schema_versions`, `/health/ready` | forward only ([DB Migrate](runbooks/db-migrate.md)) |

Merge rules (DM-11.5, data standards v1.1): during the dev phase the orchestrating agent merges and verifies its own
PRs, including infra and security (D-13); risky PRs get an agent review first. The human gate (Terraform, migrations,
auth, data deletion) starts with prod or the first paying tenant.

## CI/CD matrix (APP-02)

Read from each repo's `.github/workflows/` on `main` on 2026-10-19; the CI rows and required checks re-read on 2026-10-28;
the CI, Visual, copy guard and history scan rows updated on 2026-11-06 (S271, CI minutes).

Since S271 the three merge-queue repos (CIS, Booking, Partner) run `ci.yml` on pull_request, merge_group and dispatch,
not on push to `main`: every commit on `main` is a queue group commit that already passed the full run. On a pull
request only the fast jobs run (lint, security audit, unit tests, migration preflight, frontend lint and type check);
the heavy ones (integration tests, Docker build checks, frontend build, Visual) run in the queue, or on the PR when
it touches their area (migrations or integration tests, image inputs); a skipped job counts as passed for a required
check. A docs-only PR skips the test jobs. Dispatching `ci.yml` on a PR branch runs everything on its head.

| Repo | Workflow | Trigger | Jobs | Notes |
|---|---|---|---|---|
| AA-CIS-App | `ci.yml` | PR to `main` (fast jobs; heavy ones by area); merge_group (all); dispatch (all) | Lint, Quality Paths (report), Security Audit, Unit Tests, Integration Tests, Docker Build Check, Frontend Lint, Frontend Build | required by branch protection: Lint, Security Audit, Unit Tests, Integration Tests, Docker Build Check, Frontend Lint, Frontend Build, plus `gitleaks` from `secret-scan.yml` (Portal Lint / Portal Build went with the frozen `portal/` at the AA-979 P2b clean-up) |
| AA-CIS-App | `deploy-dev.yml` | push to `main` (backend paths); dispatch (`override_running_jobs`) | Pre-deploy job guard, Build and Push ECR, Deploy to ECS Dev | concurrency `deploy-dev-cis`, never cancelled |
| AA-CIS-App | `deploy-admin-dev.yml` | push `main` (`frontend/**`); dispatch | ECS deploy of the admin, verify, UI smoke, visual | `vercel-deploy.yml` deleted at the Vercel retirement (AA-911, S272) |
| AA-CIS-App | `ui-smoke.yml` | called by the deploy workflow; dispatch | Playwright smoke | the portal workflows were deleted by AA-979 (CIS #997); the frozen `portal/` was deleted at the P2b clean-up |
| AA-CIS-App | `eval-regression.yml` | dispatch only | Run eval regression gate | by hand on the golden set (D-23); per-PR trigger only if N-4 is approved |
| AA-Booking | `ci.yml` | PR to `main` (fast jobs; heavy ones by area); merge_group (all); dispatch (all) | Lint (with the vendored CIS copies since S271), Security Audit, Unit Tests, Integration Tests, Docker Build Check, Migration preflight, Frontend Build | required: Lint, Security Audit, Unit Tests, Integration Tests, Docker Build Check, Frontend Build, plus `gitleaks` and Visual |
| AA-Booking | `deploy-dev.yml` | push to `main` (backend paths); dispatch (`override_running_jobs`) | Deploy configuration, Pre-deploy job guard, Deploy to ECS Dev | live smoke on `/booking/health` + `/ready` |
| AA-Booking | `deploy-admin-dev.yml` | push `main` (frontend paths); dispatch | ECS deploy of the admin, verify, public smoke, visual | `vercel-deploy.yml` deleted (AA-911, S272) |
| AA-Partner | `ui-smoke-portal.yml` | called by `deploy-web-dev.yml` (AA-1036; was `deploy-portal-dev.yml`, retired); dispatch | Playwright Content studio smoke | always the agency host; signs in with the partner pool (secrets `E2EPORTALEMAIL`, `E2EPORTALPASSWORD`, `E2EPORTALTOTP`) since the AA-979 P2b clean-up |
| AA-TripPlanner-Web | `ci.yml` | PR to `main`; push `main`, `task/**`, `chore/**`, `feature/**` | Backend (pytest), Security Audit, Migrations (lint, PG 15 replay), Frontend (lint + build) | |
| AA-TripPlanner-Web | `deploy-lambdas.yml` | push to `main` (`backend/**`); dispatch | Build + deploy Lambda code | deploy role trusts `main` only |
| AA-TripPlanner-Web | `deploy-web-dev.yml` | PR (`frontend/**`, preview image check); push `main` (`frontend/**`); dispatch | Preview (image, `next start` in the runner) on PRs; ECS deploy of `aa-tripplanner-dev-web`, post-deploy verify through CloudFront, release verify (`post-deploy-verify.yml`), visual (`visual.yml`, report-only) | `vercel-deploy.yml` deleted at the TripPlanner Vercel retirement (AA-1038, S272) |
| AA-CIS-Infra | `terraform-plan.yml` | PR to `main` | Terraform Plan (dev) | plan comment on the PR |
| AA-CIS-Infra | `terraform-apply.yml` | dispatch from `main` | Terraform Apply (dev) | GitHub environment `dev` = Dev resources (renamed from `prod` in AA-1023, ADR 0012 decision 6) |
| AA-CIS-Infra | `db-migrate.yml` | dispatch from `main` | Migrate | modes check / apply / set-password / run-script |
| AA-CIS-Infra | `db-schema-dump.yml` | nightly 03:43 UTC; after each apply; dispatch | Dump schema, regenerate reference | opens the root PR `bot/db-schema-reference` |
| AA-CIS-Infra | `db-isolation-probe.yml` | nightly 04:13 UTC; after each apply; dispatch | Isolation probe | read-only |
| AA-CIS-Infra | `migration-copy-guard.yml` | every PR (a scope step skips the checks outside the migration paths); nightly 02:17 UTC; dispatch | Copies match owner main (with the scope step since S271), Migration lint and unique numbers, Retention rows for new-app tables, Expand classify | required (ruleset): all but Retention rows (advisory, reads root `master`) |
| AA-CIS-Infra | `secret-scan.yml` | PR to `main` | gitleaks (PR lines) | uses the base commit rules (AA-981) |
| AA-CIS-Infra | `secret-scan-history.yml` | push `main` (that push's commits only, S271); nightly 19:23 UTC and dispatch (full history) | gitleaks full history; gitleaks working tree (dispatch only) | every branch, tag and PR head, baseline in `.gitleaksignore` (AA-981) |
| AA-CIS-Infra | `identity-triggers-test.yml`, `ops-probe-test.yml`, `rds-snapshot-expiry-test.yml`, `secrets-register-check-test.yml` | PR / push `main` (their paths) | unit tests of the Lambdas and tools | |
| AA-Ecosys (root) | `docs-lint.yml` | PR to `master` (docs paths); weekly Monday 01:17 UTC; dispatch | Docs lint, Docs freshness report | AA-888 |
| AA-Ecosys (root) | `contracts.yml` | PR to `master` (contracts, ADR and tool paths); dispatch | Contracts and ADR numbers | |
| AA-Ecosys (root) | `secret-scan.yml` | PR to `master` | gitleaks (PR lines) | same rules as Infra (AA-981) |
| AA-Ecosys (root) | `secret-scan-history.yml` | push `master` (that push's commits only, S271); nightly 19:41 UTC and dispatch (full history) | gitleaks full history | every branch, tag and PR head (AA-981) |

Workflows on `main` on 2026-10-28 that the table above does not describe yet (names only):

| Repo | Workflows |
|---|---|
| AA-CIS-App | `api-contract.yml`, `e2e-cognito.yml`, `post-deploy-verify.yml`, `release-please.yml`, `secret-scan.yml`, `secret-scan-history.yml` |
| AA-Booking | `api-contract.yml`, `docs-lint.yml`, `post-deploy-verify.yml`, `pr-title.yml`, `release-please.yml`, `secret-scan.yml`, `secret-scan-history.yml` |
| AA-TripPlanner-Web | `docs-lint.yml`, `post-deploy-verify.yml`, `pr-title.yml`, `release-please.yml`, `secret-scan.yml`, `secret-scan-history.yml` |
| AA-Partner | `ci.yml`, `deploy-dev.yml`, `deploy-web-dev.yml`, `e2e-dev.yml`, `post-deploy-verify.yml`, `docs-lint.yml`, `pr-title.yml`, `release-please.yml`, `scrub-corpus.yml`, `secret-scan.yml`, `secret-scan-history.yml` |
| AA-CIS-Infra | `alb-rule-order.yml`, `connection-budget.yml`, `contract-copy-guard.yml`, `crm-key-policy-diff.yml`, `db-freshness-probe.yml`, `db-tour-liveness-gate.yml`, `docs-gen.yml`, `docs-gen-test.yml`, `docs-lint.yml`, `managed-login-branding.yml`, `tf-plan-guard-test.yml` |
| AA-Ecosys (root) | `docs-sync.yml` (publishes the `/admin/docs` reader bundle) |

Scheduled jobs outside GitHub: the ops-probe Lambda `aa-cis-dev-dfs-balance-check` (EventBridge schedules; the daily
06:15 UTC run calls the DataForSEO balance check, the Jev canary (a real paid call), the Jev 402 sweep, the wave check and
the staff directory reconcile; a second schedule enqueues the retention kinds) and the snapshot-expiry Lambda
`aa-cis-dev-rds-snapshot-expiry`. Never invoke the ops probe with an empty event by hand: it runs the paid canary.

## Prod

No prod environment exists. [ADR 0012](../adr/0012-environment-model.md) (accepted S257) sets the model: prod on acc2 next to Dev, with its own environment
resources and the compensating controls of decision 4; Terraform root `accounts/aa365-prod` (decision 5); the
GitHub environment `prod` renamed to `dev` first (decision 6, done in AA-1023); releases promote the Dev-verified backend image by
digest through a Deploy Prod workflow that only the tech lead dispatches, frontends rebuilt in Vercel prod projects
(decisions 7–8); personal data never leaves prod (decision 9); the go-live gate of decision 11. The build (phase 3)
starts when the business owner sets a go-live date (D-16, D-17). The prod blueprint, readiness checklist and prod
runbooks (PROD-01) are AA-880.
