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
| The RDS-managed master password is live (AA-CIS-Infra `modules/rds`, `manage_master_user_password`, 180-day rotation) and the old master DSN secret and its GitHub copy are deleted | group 1 rotates the master through RDS | `aws rds describe-db-instances --db-instance-identifier aa-cis-dev-db --profile aa365-admin --region us-west-1 --query "DBInstances[0].MasterUserSecret.SecretStatus" --output text` prints `active` |
| CIS issues JWTs with `iss` / `aud` and separate staff and tenant signing keys | group 2 otherwise signs out every staff and tenant session with one key and keeps one key for two audiences | the CIS auth code reads two key secrets; until then skip group 2 and record "blocked" |
| The CI bot private key copies are consolidated (secrets register follow-up) | group 7 otherwise has to update one copy per repo environment | the register lists one primary and its copies for `aa-ecosys-ci-bot` |
| Two Infra PRs prepared, not merged: Redis AUTH (`auth_token_update_strategy = "ROTATE"` and `auth_token_version` + 1 in `modules/elasticache`) and the lead webhook key (`local.tp_lead_webhook_key_version` + 1 in `modules/environment/tripplanner.tf`) | groups 5 and 6 are Terraform applies | both PRs green, waiting |
| No pilot traffic expected in the window; staff told that they will sign in again | groups 2, 4 and 5 sign people out | message sent |

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
- Verify: the run logs `set-password: test login current_user=<role>`; after the restart `/health/ready` of the app is 200 (CIS `https://api-cis.lumiguides.it.com/health/ready`, Booking `https://api-booking.lumiguides.it.com/booking/health/ready`, CRM `/crm/health/ready`, TripPlanner per its runbook).
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
- Verify: a machine route answers 200 with the new value and 403 with the old one (same check as the S244 rotation),
  and the next Deploy Dev run passes its gate.
- Rollback: move `AWSCURRENT` back, set the GitHub copy from the previous version, restart.

## Group 4: Cognito client secrets (two-secret overlap)

AA-CIS-Infra `tools/identity/client_secret_rotate.py`, one client at a time, in this order: `crm-m2m`, `partner-web`,
`crm-staff`, `academy-web`, `cis-admin`, `breakglass`, `booking-staff`. The tool takes the new value from the
`AddUserPoolClientSecret` response (Describe no longer returns it after a rotation, lesson S296), stores it in the
client's Secrets Manager key, checks the stored hash and prints the restart command.

- Precheck: `python3 tools/identity/client_secret_rotate.py --profile '' status --client <client>` (credentials exported from the MFA session): one secret on the client, the key set.
- Command: `python3 tools/identity/client_secret_rotate.py --profile '' add --client <client> --apply # WRITE`, then the printed restart.
- Verify: `crm-m2m`: a CRM job that calls Booking / CIS with M2M succeeds (`booking_sync`, `membership_pull`); web clients: a sign-in on that surface works (E2E sign-in for the staff hosts); `breakglass`: `workforce_bootstrap.py breakglass-verify` (raises the break-glass alarm by design).
- Then: `python3 tools/identity/client_secret_rotate.py --profile '' retire --client <client> --keep <new-secret-id> --apply # WRITE`
- Rollback before `retire`: both secrets are valid; move `AWSCURRENT` of the Secrets Manager secret back and restart. After `retire` there is no way back: run `add` again.

## Group 5: TripPlanner keys

| Key | Command | Verify |
|---|---|---|
| Session key (`tripplanner/dev/web` `session_secret`) | `python3 tools/identity/tripplanner_web_secret.py --profile '' --rotate-session --apply # WRITE`, restart `aa-tripplanner-dev-web` | travellers are signed out; a new sign-in works |
| Tenant assertion key (`tripplanner/dev/tenant-assertion-key`) | `python3 tools/identity/tripplanner_assertion_key.py --profile '' --rotate --apply # WRITE` (the previous key stays valid up to 7 days), restart `aa-tripplanner-dev-web` | an agency page on the TripPlanner host loads tenant data |
| Lead webhook master key (`tripplanner/dev/lead-webhook-key`) | merge the prepared Infra PR, then the Terraform apply of AA-CIS-Infra (dispatch `terraform-apply.yml`) # WRITE | the Lambdas pick the new key up within 10 minutes; hand the re-derived agency keys out in the same window |
| Revalidate HMAC (`aa-cis/dev/tripplanner-revalidate-hmac` + its copy in `tripplanner/dev/web`) | new value into the CIS secret through a pipe (group 2 command with `--secret-id aa-cis/dev/tripplanner-revalidate-hmac`), then `python3 tools/identity/tripplanner_web_secret.py --profile '' --apply # WRITE`, restart `aa-tripplanner-dev-web`, `aa-cis-dev-worker` | the next `tripplanner_purge` job succeeds |
| Edge keys (`random_password.tp_web_site_marker`, `random_password.crm_origin_verify`, S296 rows 8 and 9) | local MFA apply from AA-CIS-Infra `main` with `-replace=random_password.tp_web_site_marker` and `-replace=random_password.crm_origin_verify[0]` # WRITE | a short 403 window while CloudFront and the ALB rules switch; then the TripPlanner and agency hosts answer 200 |

- Precheck: `tripplanner_web_secret.py` and `tripplanner_assertion_key.py` dry runs (without `--apply`) name only the keys you expect.
- Rollback: Secrets Manager rows: move `AWSCURRENT` back and restart; Terraform rows: none (apply again).

## Group 6: Redis AUTH

- Precheck: the prepared Infra PR sets `auth_token_update_strategy = "ROTATE"` and bumps `auth_token_version`
  (AA-CIS-Infra `docs/implementation-notes/AA-874.md`).
- Command: merge it and apply (dispatch `terraform-apply.yml`) # WRITE; restart `aa-cis-dev-api` and `aa-cis-dev-worker`;
  then a second PR sets `auth_token_update_strategy = "SET"` and apply # WRITE, so only the new token is valid.
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
