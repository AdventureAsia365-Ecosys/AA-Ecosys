# S243 AA-892 — read-only checks behind the ops runbooks (19/10/2026)

Agent: Claude Code (subagent, AA-892 lane). Profile `aa365-admin`, us-west-1; `sts get-caller-identity` = acc2 (role
`nghiep-admin-8h-session`). Every command below is read-only (describe/list/get, `curl` GETs, `gh run list/view`). No
secret value was read; `get-secret-value` was not called. ARNs, account IDs and security-group IDs are left out.

## ECS (rollback-cis, rollback-booking)

- Circuit breaker `enable: true, rollback: true` on `aa-cis-dev-api`, `aa-cis-dev-worker`, `aa-booking-dev-api`.
- At the time of the check a CIS deploy was `IN_PROGRESS` (api and worker on the image of CIS `main` 743e99d1);
  Booking `COMPLETED`, image b3ad02f1 (Booking `main` has two later commits that did not touch deploy paths).
- Recent revisions list with images (newest three): api and worker revisions carry matching `dev-<sha>` tags
  (743e99d1, 2a19d981, fd066d7c); Booking revisions carry full-SHA tags.
- ECR: `aa-cis-dev-api` IMMUTABLE, lifecycle "untagged 7 days" + "keep last 30 `dev-*`"; `aa-booking-dev-api`
  IMMUTABLE, lifecycle "keep last 10 images" (any tag).
- Live task definition env names: CIS api has `JOB_WORKER_IN_API` and no legacy-login or force-admin variable; its
  `DATABASE_URL` secret reference is still the master secret `aa-cis/dev/rds` (X1 S18 not live). Booking api has no
  `WORKER_ENABLED` (default on).
- Autoscaling: api min 1 / max 7, worker min 1 / max 3.
- Live checks: `https://api-cis.lumiguides.it.com/health` 200 (`git_sha` 743e99d1), `/health/ready` 200;
  `https://api-booking.lumiguides.it.com/booking/health/ready` `{"status":"ok","db":"ok","schema_version":"bk-017"}`;
  `https://tripplanner.lumiguides.it.com/api/browse?resource=countries` 200.

## RDS (restore-rds-pitr, database-operations)

- `aa-cis-dev-db`: available, PostgreSQL 15.17, `db.t4g.small`, 20 GB, encrypted, deletion protection on, single-AZ,
  backup retention 7 days, backup window 03:00-04:00, maintenance Mon 04:00-05:00, log export `postgresql`, subnet group
  `aa-cis-dev-db-subnet-group`, parameter group `aa-cis-dev-pg15`, one security group (`aa-cis-dev-sg-rds`), tags
  `App=shared`, `Environment=dev`. `LatestRestorableTime` about 5 minutes behind now.
- Snapshots: 8 automated, 3 manual (`…pre-bhutan-rerun-20261005`, `…pre-rerun-20261001`, one DB Migrate
  destructive-apply snapshot from 16/10).
- Isolation probe: AA-CIS-Infra run 39196200689 (dispatch, 19/10 03:45 UTC) success.

## Alarms and logs (playbooks)

- 65 metric alarms: 61 OK, 4 ALARM - all four are `TargetTracking-…-AlarmLow-…` autoscaling scale-in alarms of the CIS
  api and worker (normal).
- Thresholds read for the playbooks: CIS and Booking API 5XX >= 5 in 5 min; CIS p95 integration latency > 5 s for
  15 min; job queue age > 900 s (2 x 5 min); overdue running > 0; sampling stopped (no sample 45 min); SES bounce rate
  > 2.5 %, complaint rate > 0.05 % (1 h); TP Lambda errors >= 3 in 5 min; break-glass token issued >= 1.
- Alarm actions go to the SNS topic `aa-cis-dev-acp-alerts` (one e-mail subscription).
- Log retention: `/ecs/aa-cis-dev` 30, `/ecs/aa-booking-dev` 30, `/ecs/aa-cis-dev/exec-sessions` 365, VPC flow logs
  365, WAF 365, RDS postgresql 365, TP and ops Lambdas 30, identity trigger Lambdas 365, API Gateway execution logs 30,
  `/aws/apigateway/welcome` never expires (a default group). Matches D-09 / AA-872 (security 365, app 30).

## TripPlanner Lambdas (rollback-tp-lambda)

- Both HTTP API integrations target the functions unqualified (`$LATEST`); no aliases.
- Published versions exist per deploy (latest 65, 19/10 02:08 UTC), same number and `CodeSha256` on both functions;
  `$LATEST` hash = version 65 hash.
- Code size about 44.7 MB per function.
- Artifacts bucket `aa-tripplanner-dev-lambda-artifacts-…` versioning Enabled (66 versions of `browse.zip`).
- Env keys: browse `ENVIRONMENT`, `TRIPPLANNER_DATABASE_URL_ARN`, `BEDROCK_REGION`; assembly adds the Bedrock satellite
  settings and `REQUIRE_REGISTRATION_BEFORE_HANDOFF`. No plaintext edge key any more (AA-878 I2 applied).

## Terraform state (rollback-terraform)

- `aa-cis-tfstate-…` versioning Enabled, 206 versions of `dev/terraform.tfstate`. Bronze bucket versioning Enabled;
  lifecycle rules only for `raw-archive/` and `archive/` (nothing for `scripts/`).

## SES (ses-bounce, cognito-login)

- Account: production access true, sending enabled, enforcement `HEALTHY`, suppression BOUNCE + COMPLAINT, 0 suppressed
  destinations. Identity `lumiguides.it.com` (domain).
- Configuration sets `aa-email-dev-external`, `-transactional`, `-workforce`, each with event destination
  `feedback-sns` (BOUNCE, COMPLAINT, REJECT) to the topic `aa-email-dev-feedback`. **That topic has 0 subscriptions**
  (by design, `ses.tf`: "No subscription yet").
- Per-set reputation metrics exist for workforce and transactional only (external has not sent mail yet).

## Other

- Cognito pools: `aa-workforce-dev`, `aa-external-dev`.
- Secrets Manager names listed (27 live; the four AA-878 orphans no longer appear in a plain listing). Rotation enabled
  on none.
- AWS Budgets (us-east-1 API): `aa-cis-dev-monthly-total` 250, `-app-cis` 150, `-app-shared` 50, `-app-booking` 25,
  `-app-tripplanner` 25 USD. Cost Anomaly Detection monitor `Default-Services-Monitor`.
- Vercel team (Hobby): projects `aa-cis-frontend`, `aa-booking-admin`, `aa-tripplanner` (no portal project yet).
- GitHub: Booking Deploy Dev last run 19/10 02:03 UTC success (b3ad02f); CIS Deploy Dev run for 702ef9a in progress.
