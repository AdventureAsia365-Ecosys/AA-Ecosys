---
id: SEC-02-rotation
title: Rotate a secret
description: When a secret is rotated and how, per class (RDS logins, app keys, vendor keys, Cognito clients, break-glass, GitHub and Vercel copies), with verify and rollback for each.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-28
review_every_days: 90
last_tested: 2026-10-18
tested_where: dev-acc2
tested_evidence: "docs/sessions/2026-10-18-S242-cognito-staff-login-x1-network-dependabot.md (class 4 only: the break-glass secret, AA-854 breakglass-init; the other classes never rotated)"
related: [SEC-02, OPS-10, OPS-05-db-migrate, AA-878, AA-880, AA-816]
---

# Rotate a secret

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> Two classes have run once: the break-glass secret (`breakglass-init`, S242) and the admin secret (manual, 2026-10-17,
> per the register). The others are written from the code and Terraform, last checked on 2026-10-28.

## When to rotate (D-02, D-03, DM-8.9)

| Trigger | Rotate |
|---|---|
| Suspected leak (printed in a log or transcript, pasted in chat, a lost laptop, an ex-staff member had it) | **now**, that secret and its copies |
| After a break-glass use | the break-glass password (and the RDS master after its break-glass use, from prod) |
| Going to prod (AA-880) | the RDS master, the GitHub token printed in S240, every secret that will be reused in prod |
| A vendor forces it | that key |

Since register v2 (AA-1183, S296) each register row also has a rotation class with an interval and a next due date
(the [Rotation](../../security/secrets-register.md#rotation) section of the register: scheduled 90, 180, 365 or 730
days; auto; on incident; identifier). The events above still come first: a key ceremony or a suspected leak rotates a
row before its date. Secrets Manager rotation is enabled on 0 of the secrets; every rotation below is manual.

## Where the list lives

The secrets register (AA-878): `docs/security/secrets-register.md` and `.yaml` (names, consumers, copies, status;
never values). Look up the secret's row first: it names every copy (GitHub, Vercel, Lambda) that must change with it.

## Preconditions

- Access: profile `aa365-admin` with MFA. Values are typed or pasted by the tech lead in the console, or generated
  and written by a tool that never prints them. Agents never read a value (`get-secret-value` is not used in any
  step).
- A rotation restarts the consumers, and a restart interrupts the jobs that run (they are retried). Deploys no longer
  wait for idle job tables (AA-993 G5); the [deploy gate](deploy-gate-override.md) only holds while a rerun wave is
  open or a deploy-blocking job kind runs. Check it before restarting ECS services.

```bash
aws sts get-caller-identity --profile aa365-admin
```

Expected: the acc2 account from the [account map](../../onboarding.md#account-map).

## Per class

### 1. App keys in Secrets Manager read at task start (`aa-cis/dev/admin-secret`, `aa-cis/dev/jwt-secret`, vendor keys such as `aa-cis/dev/openai-key`)

1. Generate the new value at the source (vendor console for vendor keys). The tech lead writes it: Secrets Manager console,
   the secret, **Retrieve secret value**, **Edit**. The old version stays as `AWSPREVIOUS`.
2. Update every copy the register lists (for `admin-secret`: GitHub `ADMIN_SECRET` on AA-CIS-App; the CIS admin on
   ECS (`aa-cis-dev-admin`) reads the secret itself at task start, so restart it with the services below; the Vercel
   `aa-cis-frontend` copies went with the project, AA-911 S272) - the tech lead, by hand.
3. Restart the consumers so they read the new value:

   ```bash
   aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-api --force-new-deployment --profile aa365-admin --region us-west-1 --query "service.deployments[0].rolloutState" --output text # WRITE
   aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-worker --force-new-deployment --profile aa365-admin --region us-west-1 --query "service.deployments[0].rolloutState" --output text # WRITE
   aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-admin --force-new-deployment --profile aa365-admin --region us-west-1 --query "service.deployments[0].rolloutState" --output text # WRITE
   ```

4. Verify: rollout `COMPLETED`, `/health/ready` 200, an admin page that uses the key works; for `jwt-secret` every
   staff and tenant session is logged out (expected).
5. Rollback: restore the previous version as current (console: **Versions**, or
   `aws secretsmanager update-secret-version-stage --secret-id <name> --version-stage AWSCURRENT --move-to-version-id <previous-version-id> --remove-from-version-id <new-version-id> --profile aa365-admin --region us-west-1`),
   then restart again. Vendor keys: re-enable the old key at the vendor if it was revoked.
6. Revoke the old value at the source once the new one works (vendor keys).

### 2. RDS logins (the RDS-managed master, `cis_app`, `db_migrator`, `crm_app`, `aa_app_user`, Booking and TripPlanner DSNs)

- Master: since AA-1182 (S297) RDS manages the master password (secret `rds!db-<id>`, rotated every 180 days by RDS;
  no copy anywhere else). An extra rotation is the [key ceremony](key-ceremony.md) step 1a (`modify-db-instance
  --rotate-master-user-password --apply-immediately`); then DB Migrate `mode=run-script` `db/scripts/session_info.py`
  must log the RDS-managed master login. No app logs in as the master (DM-8.9), so nothing restarts. The old hand-kept
  DSN `aa-cis/dev/rds` is a fallback only until it is deleted.
- `cis_app`, `db_migrator`, `crm_app`, `aa_app_user`, `booking` and `tripplanner` (the `password_roles` of
  AA-CIS-Infra `db/owners.yaml`): a new password goes into the role's DSN secret through a pipe
  (`tools/security/dsn_new_password.py`, command in the [key ceremony](key-ceremony.md), group 1b); then
  [DB Migrate](db-migrate.md) `mode=set-password` with that role sets the password from the secret and
  test-connects. Then restart the services that read it (table in the key ceremony, group 1b).
- Rollback: move the secret's `AWSCURRENT` back to the previous version and run `set-password` again.

### 3. Cognito app client secrets (`cis-admin`, `booking-staff`, `breakglass`, `crm-staff`, `cis-portal`, `partner-web`, M2M clients)

- Every client with a secret is in AA-CIS-Infra `identity.tf` (WORKFORCE and EXTERNAL client maps),
  `identity_partner.tf` or `identity_m2m.tf`. The secrets live in Terraform state and in Secrets Manager (register
  rows; the staff admins read `aa-cis/dev/admin-web` / `booking/dev/admin-web`, refilled by AA-CIS-Infra
  `tools/identity/staff_web_secret.py`, then force a new deployment of that admin service). The `-preview` clients
  were deleted with the Vercel retirement (AA-911, S272). Rotation (all seven clients rotated by hand in S296):
  AA-CIS-Infra `tools/identity/client_secret_rotate.py add --client <client> --apply`, which stores the new value from
  the `AddUserPoolClientSecret` response (Describe returns no secret once a client has rotated secrets, lesson S296),
  then the printed restart, a sign-in or M2M check, then `retire --client <client> --keep <new-secret-id> --apply`.
  Rollback: until `retire`, both secrets are valid; move the stored copy back and restart.

### 4. Break-glass (`aa-identity/dev/breakglass`)

- `tools/identity/workforce_bootstrap.py breakglass-init` in AA-CIS-Infra writes a new password and TOTP seed with
  `PutSecretValue` only (it never reads the old value). The secret's resource policy allows only the MFA admin role, and
  any access sends an alert by design. See [break-glass](break-glass.md).

### 5. TripPlanner edge key (`tripplanner/dev/api-key`)

- Terraform `random_password` is the source. Replacing it is a local MFA apply from merged Infra `main`
  (`-replace=module.environment.random_password.tripplanner_api_key`; the CI apply takes no arguments). The Lambdas read the secret by
  name and may cache it per instance: dispatch `deploy-lambdas.yml` from `main` to get fresh instances. The tech lead updates
  the Vercel `aa-tripplanner` copy (register row) on Production, Preview and Development in the same window and
  redeploys the frontend. Requests fail with 401 in between. Verify: `curl -s -o /dev/null -w "%{http_code}\n" "https://tripplanner.lumiguides.it.com/api/browse?resource=countries"` 200.

### 6. Tokens outside AWS (GitHub PATs, Vercel tokens, vendor accounts)

- Create the new token with the same scope, update the GitHub secret (`gh secret set <NAME> -R <repo>` reading from
  stdin, never from an argument), run the workflow that uses it, then revoke the old token.
- GitHub App keys (`aa-agent`, `aa-ecosys-ci-bot`; register rows) replaced the root-repo PAT in S247. Rotate a key on
  a leak or at go-live ([ADR 0011](../../adr/0011-github-app-identity-and-merge-rights.md)): create a new private key
  in the App settings, update its copies, then delete the old key.

### 7. CRM encryption keys (KMS)

- The CRM keys are KMS keys, not secrets. Alarms and key-policy checks: [CRM keys](crm-keys.md).

## Verify the result

- Every consumer in the register row works; the row's `rotation.last_rotated` and `rotation.next_due` (and
  `last_rotated` of each `copy_of` row that was set) are updated in the YAML, then
  `python3 tools/security/secrets_register.py md --write` (names and dates only); the drift check prints `diff = 0`
  for that row.

## Roll back or abort

- Secrets Manager keeps the previous version (`AWSPREVIOUS`): move `AWSCURRENT` back and restart (class 1 step 5).

## Escalation

- A leak is SEV1 until the secret is rotated ([incident response](../incident-response.md): rotate first, investigate
  second).

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-10-18 | dev-acc2 | Claude Code + tech lead | S242 session log (AA-854 break-glass init) | pass (class 4 only) |
| 2026-10-17 | dev-acc2 | tech lead | secrets register row `aa-cis/dev/admin-secret` (manual rotation) | pass (class 1, no written procedure then) |
