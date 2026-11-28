---
id: SEC-02-ceremony
title: Run the pre-pilot key ceremony
description: One planned session that rotates every long-lived secret the ecosystem controls, in nine fixed groups, before the first real pilot data; per step a precheck, the command, a verify and a rollback, and a dated record.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-28
review_every_days: 90
last_tested: untested
related: [SEC-02-rotation, SEC-02, OPS-05-db-migrate, OPS-10, AA-1182]
---

# Run the pre-pilot key ceremony

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.

One session of 2 to 3 hours, before the first real pilot data enters the system (tech lead decision S295). Every
long-lived secret the ecosystem controls is rotated once, in the order below, and each step gets a line in the
[record](#record). For a single secret outside the ceremony (a leak, a person leaving), use
[rotate a secret](secret-rotation.md).

**Not in the ceremony: LLM vendor keys** (OpenAI, Anthropic and other gateway providers). They rotate on an event only
(exposure, staff change, vendor alert); instead each vendor account has a hard spend limit slightly above the gateway
caps, with alerts (secrets register, `on-incident` rows).

## Roles and rules

- The tech lead runs the session with a fresh MFA session (`aws sts get-caller-identity --profile aa365-admin`); the
  orchestrating agent may run the scripted steps in the same window. Steps that need a browser (GitHub App keys,
  vendor consoles) are the tech lead's.
- A new value never appears in a terminal, a chat or a file in git. It passes from the generator to Secrets Manager
  through a pipe, or through a `0600` file under `.tmp-session/` that is shredded in the same step.
- One group at a time. A group is finished when its verify line passes; a failed verify means its rollback, then stop
  and write the finding in the record.
- Every command is one line. Lines that change state end with `# WRITE`.

## Before the day

| Prerequisite | Why | Check |
|---|---|---|
| The RDS-managed master password is live (AA-CIS-Infra `modules/rds`, `manage_master_user_password`, 180-day rotation) and the old master DSN secret and its GitHub copy are deleted: [switch the master to RDS management](#before-the-day-switch-the-master-to-rds-management) | group 1 rotates the master through RDS | `aws rds describe-db-instances --db-instance-identifier aa-cis-dev-db --profile aa365-admin --region us-west-1 --query "DBInstances[0].MasterUserSecret.SecretStatus" --output text` prints `active` |
| CIS issues JWTs with `iss` / `aud` and separate staff and tenant signing keys | group 2 otherwise signs out every staff and tenant session with one key and keeps one key for two audiences | the CIS auth code reads two key secrets; until then skip group 2 and record "blocked" |
| The CI bot private key copies are consolidated (secrets register follow-up) | group 7 otherwise has to update one copy per repo environment | the register lists one primary and its copies for `aa-ecosys-ci-bot` |
| Three Infra PRs prepared, not merged: Redis AUTH (`auth_token_update_strategy = "ROTATE"` and `auth_token_version` + 1 in `modules/elasticache`), the lead webhook key (`local.tp_lead_webhook_key_version` + 1 in `modules/environment/tripplanner.tf`) and the edge keys (`keepers = { ceremony = "<yyyy-mm>" }` on `random_password.tp_web_site_marker` in `accounts/aa365/tripplanner_web_edge.tf` and on `random_password.crm_origin_verify` in `accounts/aa365/crm_edge.tf`; a changed keeper replaces the value) | groups 5 and 6 are Terraform applies through the CI apply (its TF_VARs and plan guard) | all three PRs green, their Terraform Plan check shows only the expected lines (group 5 and 6 prechecks) |
| No pilot traffic expected in the window; staff told that they will sign in again | groups 2, 4 and 5 sign people out | message sent |

## Before the day: switch the master to RDS management

Done once, days before the ceremony, after the AA-CIS-Infra PR that sets `manage_master_user_password` is merged
(the DB Migrate runner reads the RDS-managed secret first and falls back to the old DSN secret `aa-cis/dev/rds` until
then). Two targeted local MFA applies, because the managed secret does not exist in the Terraform state before the
first one: apply 1 turns the management on and gives the DB Migrate task role a grant on the managed secret by name
pattern and instance tag; apply 2 sets the 180-day schedule and names the exact secret ARN. Run every command from
the workspace root, with `infra/AA-CIS-Infra` on the latest `main` (`git -C infra/AA-CIS-Infra pull --ff-only`).

| Step | Precheck | Command | Verify | Rollback |
|---|---|---|---|---|
| S1 Idle and init | `aws sts get-caller-identity --profile aa365-admin` prints acc2 | idle gate as in [step 0](#step-0-job-tables-idle) (point 2); then `bash -c 'C=$(aws configure export-credentials --profile aa365-admin --format env-no-export </dev/null) ; grep -q "^AWS_ACCESS_KEY_ID=" <<<"$C" || exit 1 ; env -u AWS_PROFILE $(tr "\n" " " <<<"$C") terraform -chdir=infra/AA-CIS-Infra/accounts/aa365 init -input=false'` | the idle gate is green; init prints "Terraform has been successfully initialized" | none |
| S2 Plan 1 | no DB Migrate run in progress (`gh run list -R AdventureAsia365-Ecosys/AA-CIS-Infra --workflow db-migrate.yml --limit 3`) | `bash -c 'C=$(aws configure export-credentials --profile aa365-admin --format env-no-export </dev/null) ; grep -q "^AWS_ACCESS_KEY_ID=" <<<"$C" || exit 1 ; env -u AWS_PROFILE $(tr "\n" " " <<<"$C") terraform -chdir=infra/AA-CIS-Infra/accounts/aa365 plan -input=false -lock-timeout=10m -target=module.rds.aws_db_instance.main -target=aws_iam_role_policy.db_migrate_task -out=aa1182-apply1.tfplan'` | `Plan: 0 to add, 2 to change, 0 to destroy`: `module.rds.aws_db_instance.main` in place with only `manage_master_user_password = true` (and `master_user_secret` unchanged in the plan), `aws_iam_role_policy.db_migrate_task` in place with the new statements `ReadManagedMasterSecret` and `DescribeMasterInstance`. Any replace, any other instance attribute, `aws_db_parameter_group.main` or any other address: stop, do not apply | none (nothing applied) |
| S3 Apply 1 | S2 verify passed, the idle gate still green | `bash -c 'C=$(aws configure export-credentials --profile aa365-admin --format env-no-export </dev/null) ; grep -q "^AWS_ACCESS_KEY_ID=" <<<"$C" || exit 1 ; env -u AWS_PROFILE $(tr "\n" " " <<<"$C") terraform -chdir=infra/AA-CIS-Infra/accounts/aa365 apply -input=false aa1182-apply1.tfplan' # WRITE` | `aws rds describe-db-instances --db-instance-identifier aa-cis-dev-db --profile aa365-admin --region us-west-1 --query "DBInstances[0].MasterUserSecret.[SecretArn,SecretStatus]" --output text` prints an `rds!db-` ARN and `active` | [recovery](#recovery-after-the-switch) |
| S4 Plan and apply 2 | S3 verify passed | `bash -c 'C=$(aws configure export-credentials --profile aa365-admin --format env-no-export </dev/null) ; grep -q "^AWS_ACCESS_KEY_ID=" <<<"$C" || exit 1 ; env -u AWS_PROFILE $(tr "\n" " " <<<"$C") terraform -chdir=infra/AA-CIS-Infra/accounts/aa365 plan -input=false -lock-timeout=10m -target=module.rds.aws_secretsmanager_secret_rotation.master -target=aws_iam_role_policy.db_migrate_task -out=aa1182-apply2.tfplan'`, then the same wrapper with `terraform -chdir=infra/AA-CIS-Infra/accounts/aa365 apply -input=false aa1182-apply2.tfplan` # WRITE | the plan says `Plan: 1 to add, 1 to change, 0 to destroy` (`module.rds.aws_secretsmanager_secret_rotation.master[0]` with `automatically_after_days = 180`, the policy in place with the exact `rds!db-` ARN added); after the apply: `aws secretsmanager describe-secret --secret-id <SecretArn from S3> --profile aa365-admin --region us-west-1 --query "[RotationEnabled,RotationRules.AutomaticallyAfterDays]" --output text` prints `True 180` | apply 2 again; until it runs the RDS default schedule (7 days) applies, nothing breaks |
| S5 Evidence | S4 verify passed | `gh workflow run db-migrate.yml -R AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f mode=run-script -f script=db/scripts/aa1182_master_switch_check.py`, then `gh run watch <run-id> -R AdventureAsia365-Ecosys/AA-CIS-Infra --exit-status` | the log has `MIGRATE master login: aa_cis_admin (in-task RDS-managed secret of aa-cis-dev-db)`, `SCRIPT session_user=aa_cis_admin`, `SCRIPT managed_secret status=active` and `SCRIPT legacy_master=refused` (`STILL-LOGS-IN` = exit 13: stop, the old password still works) | [recovery](#recovery-after-the-switch) |
| S6 Delete the old copies | S5 printed `legacy_master=refused` | `aws secretsmanager delete-secret --secret-id aa-cis/dev/rds --recovery-window-in-days 7 --profile aa365-admin --region us-west-1 --query DeletionDate --output text # WRITE` and `gh secret delete TF_VAR_DB_PASSWORD -R AdventureAsia365-Ecosys/AA-CIS-Infra # WRITE` | S5 run again prints `legacy_master=absent`; `gh secret list -R AdventureAsia365-Ecosys/AA-CIS-Infra` has no `TF_VAR_DB_PASSWORD` | within 7 days: `aws secretsmanager restore-secret --secret-id aa-cis/dev/rds --profile aa365-admin --region us-west-1 # WRITE` (the value is dead anyway; restore only if a reader still needs the name) |

Shred the two plan files after S4: `shred -u infra/AA-CIS-Infra/accounts/aa365/aa1182-apply1.tfplan infra/AA-CIS-Infra/accounts/aa365/aa1182-apply2.tfplan`
(a saved plan holds sensitive values).

### Recovery after the switch

- **No app outage is possible from the switch:** no app logs in as the master (CIS api and worker use `cis_app`,
  Booking `booking`, the CRM `crm_app`, TripPlanner `tripplanner`). Only DB Migrate master modes (roles/ files,
  `set-password`, `run-script`) and the restore drill scripts use it.
- **There is deliberately no revert to a hand-kept password.** Turning management off needs a new password value on a
  command line, against the rule that a value never appears in a terminal, and would bring a CI copy of the master
  back. Recovery goes forward.
- **DB Migrate cannot log in as the master after apply 1:** (1) `aws rds describe-db-instances --db-instance-identifier aa-cis-dev-db --profile aa365-admin --region us-west-1 --query "DBInstances[0].MasterUserSecret.SecretStatus" --output text`
  must print `active` (not `creating` or `impaired`); (2) `aws iam get-role-policy --role-name aa-cis-dev-db-migrate-task-role --policy-name aa-cis-dev-db-migrate-task --profile aa365-admin --query "PolicyDocument.Statement[].Sid" --output text`
  must list `ReadManagedMasterSecret` and `DescribeMasterInstance`; if not, plan and apply S2 again with only
  `-target=aws_iam_role_policy.db_migrate_task`; (3) if the secret is `impaired` or its value does not log in, let RDS
  set and store a fresh password (no value on the command line):
  `aws rds modify-db-instance --db-instance-identifier aa-cis-dev-db --rotate-master-user-password --apply-immediately --profile aa365-admin --region us-west-1 --query "DBInstance.MasterUserSecret.SecretStatus" --output text # WRITE`, then S5 again.
- **Break-glass access:** the MFA admin profile reads the managed secret like any other secret.
- **The old secret `aa-cis/dev/rds` is deleted only after S5 prints `legacy_master=refused`**, always with a recovery
  window, never without one.

## Step 0: job tables idle

1. Check the account: `aws sts get-caller-identity --profile aa365-admin` prints the acc2 account (account map in
   [onboarding](../../onboarding.md)).
2. Run the idle gate (no Terraform): `gh workflow run terraform-apply.yml -R AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f idle_gate_check=true`, then `gh run watch <run-id> -R AdventureAsia365-Ecosys/AA-CIS-Infra --exit-status`.
   - Verify: green = `shared.job`, `booking.job`, `crm.job` and `tripplanner.job` idle and no rerun wave open.
   - Abort: red = busy. Wait, or end the session; never rotate DB logins under a running job.
3. Note in the record the image SHA of every ECS service before the first step (rollback reference):
   `aws ecs describe-services --cluster aa-cis-dev-cluster --services aa-cis-dev-api aa-cis-dev-worker aa-cis-dev-admin aa-booking-dev-api aa-booking-dev-admin aa-crm-dev-api aa-crm-dev-web aa-tripplanner-dev-web --profile aa365-admin --region us-west-1 --query "services[].[serviceName,taskDefinition]" --output text`

A restart below means: `aws ecs update-service --cluster aa-cis-dev-cluster --service <service> --force-new-deployment --profile aa365-admin --region us-west-1 --query service.deployments[0].id --output text # WRITE`, then wait for `aws ecs wait services-stable --cluster aa-cis-dev-cluster --services <service> --profile aa365-admin --region us-west-1`.

## Group 1: DB passwords (master + six app logins)

Logins: the master `aa_cis_admin` (RDS-managed), and `cis_app`, `aa_app_user`, `db_migrator`, `crm_app`, `booking`,
`tripplanner` (DB Migrate `set-password`, AA-CIS-Infra `db/owners.yaml` `password_roles`).

**1a. Master.**

- Precheck: `MasterUserSecret.SecretStatus` is `active` (table above).
- Command: `aws rds modify-db-instance --db-instance-identifier aa-cis-dev-db --rotate-master-user-password --apply-immediately --profile aa365-admin --region us-west-1 --query "DBInstance.MasterUserSecret.SecretStatus" --output text # WRITE`
- Verify: after the status is back to `active`, DB Migrate `mode=run-script` with `script=db/scripts/session_info.py` logs `MIGRATE master login: aa_cis_admin (in-task RDS-managed secret of aa-cis-dev-db)` and `SCRIPT session_user=aa_cis_admin`.
- Rollback: none needed; RDS keeps the secret and the password in step. If the run-script fails with a login error, run the rotate command once more and re-check.

**1b. Each app login, one at a time** (`<dsn-secret>` / `<role>` / services to restart):

| Role | DSN secret | Restart |
|---|---|---|
| `db_migrator` | `aa-cis/dev/db-migrator` | none (DB Migrate reads it per run) |
| `cis_app` | `aa-cis/dev/rds-cis-app` | `aa-cis-dev-api`, `aa-cis-dev-worker` |
| `aa_app_user` | `aa-cis/dev/rds-app-user` | `aa-cis-dev-api` |
| `booking` | `booking/dev/database-url` | `aa-booking-dev-api` |
| `crm_app` | `crm/dev/database-url` | `aa-crm-dev-api` |
| `tripplanner` | `tripplanner/dev/database-url` | TripPlanner Lambdas: dispatch `deploy-lambdas.yml` from `main` |

- Precheck: the secret holds a `postgresql://` DSN of that role (`aws secretsmanager describe-secret --secret-id <dsn-secret> --profile aa365-admin --region us-west-1 --query "[Name,LastChangedDate]"`).
- Command (new password into the DSN, through a pipe only; AA-Ecosys `tools/security/dsn_new_password.py`):
  `aws secretsmanager get-secret-value --secret-id <dsn-secret> --query SecretString --output text --profile aa365-admin --region us-west-1 | python3 tools/security/dsn_new_password.py | aws secretsmanager put-secret-value --secret-id <dsn-secret> --secret-string file:///dev/stdin --profile aa365-admin --region us-west-1 --query VersionId --output text # WRITE`
  then DB Migrate `mode=set-password` with `role=<role>`: `gh workflow run db-migrate.yml -R AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f mode=set-password -f role=<role> # WRITE`, then the restart.
- Verify: the run logs `set-password: test login current_user=<role>`; after the restart `/health/ready` of the app is 200 (CIS `https://api-cis.lumiguides.it.com/health/ready`, Booking `https://api-booking.lumiguides.it.com/booking/health/ready`, CRM `https://partner-dev.lumiguides.it.com/crm/health/ready`; TripPlanner: after the `deploy-lambdas.yml` run is green, `curl -s -o /dev/null -w "%{http_code}\n" "https://tripplanner.lumiguides.it.com/api/browse?resource=countries"` prints `200`, the browse Lambda reading the database with the new password).
- Rollback: the old DSN is the secret's `AWSPREVIOUS` version: `aws secretsmanager update-secret-version-stage --secret-id <dsn-secret> --version-stage AWSCURRENT --move-to-version-id <previous-version-id> --remove-from-version-id <new-version-id> --profile aa365-admin --region us-west-1 # WRITE`, run `set-password` again, restart.

## Group 2: JWT signing key

- Precheck: the "before the day" JWT prerequisite is shipped; otherwise record `blocked` and go on with group 3.
- Command: write a new random value in the same format as the current one (plain string, or the JSON key the task
  definition's `valueFrom` names) into each signing-key secret (today `aa-cis/dev/jwt-secret`), through a pipe:
  `python3 -c "import secrets,sys; sys.stdout.write(secrets.token_urlsafe(64))" | aws secretsmanager put-secret-value --secret-id <jwt-secret> --secret-string file:///dev/stdin --profile aa365-admin --region us-west-1 --query VersionId --output text # WRITE`
  then restart `aa-cis-dev-api` and `aa-cis-dev-worker` (and every other service that verifies the key).
- Verify: an old staff session gets 401 and a fresh sign-in on CIS, Booking and the CRM staff console works.
- Rollback: move `AWSCURRENT` back to the previous version (group 1 rollback command), restart.

## Group 3: admin machine secrets, including the CI copy

Secret `aa-cis/dev/admin-secret`; copy: GitHub `AA-CIS-App` environment `dev` secret `ADMIN_SECRET` (Deploy Dev gate
and smoke). Readers: CIS api, worker and admin, the DataForSEO balance Lambda (reads it per run).

- Precheck: no Deploy Dev run in progress (`gh run list -R AdventureAsia365-Ecosys/AA-CIS-App --workflow deploy-dev.yml --limit 3`).
- Command: generate once into a `0600` file, write both copies, shred:
  `umask 077 && python3 -c "import secrets,sys; sys.stdout.write(secrets.token_urlsafe(48))" > .tmp-session/kc-admin.txt`
  `aws secretsmanager put-secret-value --secret-id aa-cis/dev/admin-secret --secret-string file://.tmp-session/kc-admin.txt --profile aa365-admin --region us-west-1 --query VersionId --output text # WRITE`
  `gh secret set ADMIN_SECRET -R AdventureAsia365-Ecosys/AA-CIS-App --env dev < .tmp-session/kc-admin.txt # WRITE`
  `shred -u .tmp-session/kc-admin.txt`
  then restart `aa-cis-dev-api`, `aa-cis-dev-worker`, `aa-cis-dev-admin`.
- Verify: the CI deploy gate route `GET https://api-cis.lumiguides.it.com/admin/job-runner/deploy-gate` (header
  `x-admin-secret`) answers 200 with the new value and 403 with the old one. The value goes from Secrets Manager into
  the header through a pipe, never echoed:
  `aws secretsmanager get-secret-value --secret-id aa-cis/dev/admin-secret --query SecretString --output text --profile aa365-admin --region us-west-1 | sed 's/^/x-admin-secret: /' | curl -s -o /dev/null -w "%{http_code}\n" -H @- https://api-cis.lumiguides.it.com/admin/job-runner/deploy-gate` prints `200`;
  the same line with `--version-stage AWSPREVIOUS` after `get-secret-value` prints `403`. Then the next Deploy Dev run
  passes its gate (`gh run list -R AdventureAsia365-Ecosys/AA-CIS-App --workflow deploy-dev.yml --limit 1`).
- Rollback: move `AWSCURRENT` back, set the GitHub copy from the previous version, restart.

## Group 4: Cognito client secrets (two-secret overlap)

AA-CIS-Infra `tools/identity/client_secret_rotate.py`, one client at a time, in this order: `crm-m2m`, `partner-web`,
`crm-staff`, `academy-web`, `cis-admin`, `breakglass`, `booking-staff`. The tool takes the new value from the
`AddUserPoolClientSecret` response (Describe no longer returns it after a rotation, lesson S296), stores it in the
client's Secrets Manager key, checks the stored hash and prints the restart command.

- Precheck: `python3 tools/identity/client_secret_rotate.py --profile '' status --client <client>` (credentials exported from the MFA session): one secret on the client, the key set.
- Command: `python3 tools/identity/client_secret_rotate.py --profile '' add --client <client> --apply # WRITE`, then the printed restart.
- Verify: `crm-m2m`: the CRM membership pull calls CIS with the M2M token every 20 to 35 seconds; 2 minutes after the restart is stable, `curl -s https://partner-dev.lumiguides.it.com/crm/health/ready | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('membership_feed'), d.get('entitlement_feed'))"` prints `ok ok` (`failing` = the token is refused: roll back). Web clients: a sign-in on that surface works (E2E sign-in for the staff hosts). `breakglass`: `workforce_bootstrap.py breakglass-verify` (raises the break-glass alarm by design).
- Then: `python3 tools/identity/client_secret_rotate.py --profile '' retire --client <client> --keep <new-secret-id> --apply # WRITE`
- Rollback before `retire`: both secrets are valid; move `AWSCURRENT` of the Secrets Manager secret back and restart. After `retire` there is no way back: run `add` again.

## Group 5: TripPlanner keys

| Key | Command | Verify |
|---|---|---|
| Session key (`tripplanner/dev/web` `session_secret`) | `python3 tools/identity/tripplanner_web_secret.py --profile '' --rotate-session --apply # WRITE`, restart `aa-tripplanner-dev-web` | travellers are signed out; a new sign-in works |
| Tenant assertion key (`tripplanner/dev/tenant-assertion-key`) | `python3 tools/identity/tripplanner_assertion_key.py --profile '' --rotate --apply # WRITE` (the previous key stays valid up to 7 days), restart `aa-tripplanner-dev-web` | an agency page on the TripPlanner host loads tenant data |
| Lead webhook master key (`tripplanner/dev/lead-webhook-key`) | merge the prepared Infra PR, then `gh workflow run terraform-apply.yml -R AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f allow_guarded=true -f allow_reason="key ceremony group 5: lead webhook key rotation" # WRITE` and `gh run watch <run-id> -R AdventureAsia365-Ecosys/AA-CIS-Infra --exit-status` | the run's plan shows only `aws_secretsmanager_secret_version.tripplanner_lead_webhook_key` replaced; the Lambdas pick the new key up within 10 minutes; hand the re-derived agency keys out in the same window |
| Revalidate HMAC (`aa-cis/dev/tripplanner-revalidate-hmac` + its copy in `tripplanner/dev/web`) | new value into the CIS secret through a pipe (group 2 command with `--secret-id aa-cis/dev/tripplanner-revalidate-hmac`), then `python3 tools/identity/tripplanner_web_secret.py --profile '' --apply # WRITE`, restart `aa-tripplanner-dev-web`, `aa-cis-dev-worker` | the next `tripplanner_purge` job succeeds |
| Edge keys (`random_password.tp_web_site_marker[0]`, `random_password.crm_origin_verify[0]`, S296 rows 8 and 9) | merge the prepared Infra PR (new `keepers` on both), then `gh workflow run terraform-apply.yml -R AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f allow_guarded=true -f allow_reason="key ceremony group 5: edge keys rotation" # WRITE` and `gh run watch <run-id> -R AdventureAsia365-Ecosys/AA-CIS-Infra --exit-status`. Not a local apply: the CI apply carries the root's TF_VARs (without them a local plan drops the acc1 Bedrock grant) and runs the plan guard | the run's plan replaces only the two `random_password` resources (the only destroys) and updates in place the resources that carry the values (CloudFront distributions, ALB listener rules, the regional web ACL); nothing in bedrock or org access. A short 403 window while CloudFront and the ALB rules switch; then `curl -s -o /dev/null -w "%{http_code}\n" https://tripplanner.lumiguides.it.com/api/health` and `curl -s -o /dev/null -w "%{http_code}\n" https://partner-dev.lumiguides.it.com/crm/health` print `200` |

- Precheck: `tripplanner_web_secret.py` and `tripplanner_assertion_key.py` dry runs (without `--apply`) name only the keys you expect; the Terraform Plan check of each prepared PR shows only the lines the Verify column names.
- `terraform-apply.yml` runs on dispatch only, never on merge; a run without `allow_guarded=true` is refused by the
  plan guard when it changes a secret version or a `random_password`.
- Rollback: Secrets Manager rows: move `AWSCURRENT` back and restart; Terraform rows: none (apply again).

## Group 6: Redis AUTH

- Precheck: the prepared Infra PR sets `auth_token_update_strategy = "ROTATE"` and bumps `auth_token_version`
  (AA-CIS-Infra `docs/implementation-notes/AA-874.md`).
- Precheck (plan): the PR's Terraform Plan check shows `aws_elasticache_replication_group` updated in place (auth token)
  and `aws_secretsmanager_secret_version.redis_auth` replaced, nothing else.
- Command: merge it, then `gh workflow run terraform-apply.yml -R AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f allow_guarded=true -f allow_reason="key ceremony group 6: Redis AUTH ROTATE" # WRITE` and `gh run watch <run-id> -R AdventureAsia365-Ecosys/AA-CIS-Infra --exit-status`;
  restart `aa-cis-dev-api` and `aa-cis-dev-worker`; then a second PR sets `auth_token_update_strategy = "SET"`, merge it and
  `gh workflow run terraform-apply.yml -R AdventureAsia365-Ecosys/AA-CIS-Infra --ref main -f allow_guarded=true -f allow_reason="key ceremony group 6: Redis AUTH SET" # WRITE`, watched the same way, so only the new token is valid.
- Verify: after each step `/health/ready` of CIS is 200 and the cache check in it is ok.
- Rollback: between the two applies both tokens work; after the `SET` apply, bump the version again (no way back to
  the old token).

## Group 7: GitHub App private keys

`aa-agent` (primary: Secrets Manager `aa-ecosys/github/aa-agent-app-key`) and `aa-ecosys-ci-bot` (GitHub secret
`AA_CI_BOT_PRIVATE_KEY` and its copies, after the consolidation prerequisite).

- Precheck: the App settings page lists the current key's fingerprint; note it.
- Command (tech lead, browser): generate a new private key in the App settings; store it from the downloaded file:
  `aws secretsmanager put-secret-value --secret-id aa-ecosys/github/aa-agent-app-key --secret-string file://<downloaded-pem> --profile aa365-admin --region us-west-1 --query VersionId --output text # WRITE`
  or `gh secret set AA_CI_BOT_PRIVATE_KEY -R AdventureAsia365-Ecosys/<repo> [--env <env>] < <downloaded-pem> # WRITE`
  for each copy; then `shred -u <downloaded-pem>`.
- Verify: `aa-agent`: `tools/github/as-app.sh` mints a token (the next push / PR works); ci-bot: the next DB Schema Dump
  or Docs Gen run opens its PR.
- Then delete the old key in the App settings.
- Rollback: before the delete, the old key still works: put it back as current.

## Group 8: hand-held tokens

| Token | Command | Verify |
|---|---|---|
| Linear API key (`aa-ecosys/ops/linear-api-key`) | new key in Linear settings; store it from stdin (`... --secret-string file:///dev/stdin ... # WRITE`); revoke the old key | `tools/linear/linear_export.py` (dry run) reads issues |
| Notion MCP token (agent machine) | new internal integration token, update the local MCP config, revoke the old one | a Notion read through the connector works |
| GitHub tokens (agent machine `gh` token, MCP plugin PAT) | `gh auth refresh` / a new fine-grained PAT; revoke the old ones | `gh auth status` |
| Break-glass account | `python3 tools/identity/workforce_bootstrap.py breakglass-init` # WRITE, then `breakglass-verify` | the verify prints the claim summary; the user ends DISABLED |
| E2E full-admin users (`aa-cis/dev/e2e-test-admin`, `-2`) | disable them on the Staff page for the pilot (register `go-live` event) # WRITE | their sign-in fails |

- Rollback: the old token stays valid until it is revoked; revoke only after the verify passed.

## Group 9: plaintext key files on the agent machine

- Precheck: list the key files kept outside the repos (secrets register row `local:agent-machine`, "key files outside
  the repos") and confirm each value now lives in Secrets Manager or a vendor console.
- Command: `shred -u <file>` for each # WRITE.
- Verify: the folder holds no key file; the register row is flipped to `deleted`.
- Rollback: none (the values were rotated in groups 1 to 8, so the old files are worthless).

## After the ceremony

1. `/health` and `/health/ready` are 200 on every app; staff sign-in works on CIS, Booking and the CRM.
2. Every job table is idle again and the next scheduled jobs succeed.
3. The secrets register: `last_rotated` and `next_due` of every row touched, from this record.
4. The record below is complete and committed in the same PR as the register update.

## Record

One line per step. Result: `ok`, `rolled back` or `blocked (<why>)`. Evidence: the run URL, a log line or an audit
file under `docs/audits/<date>-S<nnn>-key-ceremony/` (never a value).

| Step | Date (UTC) | Who | Result | Evidence |
|---|---|---|---|---|
| B Master switch: apply 1 (management on) | | | | |
| B Master switch: apply 2 (180-day schedule) | | | | |
| B Master switch: evidence run (`legacy_master=refused`) | | | | |
| B Old master DSN secret deleted (7-day window) | | | | |
| B GitHub `TF_VAR_DB_PASSWORD` deleted | | | | |
| 0 Job tables idle, service SHAs noted | | | | |
| 1a Master (RDS-managed) | | | | |
| 1b `db_migrator` | | | | |
| 1b `cis_app` | | | | |
| 1b `aa_app_user` | | | | |
| 1b `booking` | | | | |
| 1b `crm_app` | | | | |
| 1b `tripplanner` | | | | |
| 2 JWT signing key | | | | |
| 3 Admin secret + CI copy | | | | |
| 4 `crm-m2m` | | | | |
| 4 `partner-web` | | | | |
| 4 `crm-staff` | | | | |
| 4 `academy-web` | | | | |
| 4 `cis-admin` | | | | |
| 4 `breakglass` | | | | |
| 4 `booking-staff` | | | | |
| 5 TripPlanner session key | | | | |
| 5 Tenant assertion key | | | | |
| 5 Lead webhook key | | | | |
| 5 Revalidate HMAC | | | | |
| 5 Edge keys | | | | |
| 6 Redis AUTH (ROTATE, SET) | | | | |
| 7 `aa-agent` key | | | | |
| 7 `aa-ecosys-ci-bot` key | | | | |
| 8 Linear, Notion, GitHub tokens | | | | |
| 8 Break-glass | | | | |
| 8 E2E full-admin users | | | | |
| 9 Local key files | | | | |
| After: health, sign-in, register | | | | |
