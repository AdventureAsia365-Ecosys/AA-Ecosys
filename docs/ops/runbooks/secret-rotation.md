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
last_tested: null
tested_where: null
tested_evidence: null
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

There is **no fixed 90-day cycle on Dev** (S243 reconciliation §5.1 item 15). Secrets Manager rotation is enabled on 0 of the
secrets; every rotation below is manual.

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
2. Update every copy the register lists (for `admin-secret`: GitHub `ADMIN_SECRET` on AA-CIS-App and Vercel
   `aa-cis-frontend` Production + Preview) - the tech lead, by hand.
3. Restart the consumers so they read the new value:

   ```bash
   aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-api --force-new-deployment --profile aa365-admin --region us-west-1 --query "service.deployments[0].rolloutState" --output text # WRITE
   aws ecs update-service --cluster aa-cis-dev-cluster --service aa-cis-dev-worker --force-new-deployment --profile aa365-admin --region us-west-1 --query "service.deployments[0].rolloutState" --output text # WRITE
   ```

4. Verify: rollout `COMPLETED`, `/health/ready` 200, an admin page that uses the key works; for `jwt-secret` every
   staff and tenant session is logged out (expected).
5. Rollback: restore the previous version as current (console: **Versions**, or
   `aws secretsmanager update-secret-version-stage --secret-id <name> --version-stage AWSCURRENT --move-to-version-id <previous-version-id> --remove-from-version-id <new-version-id> --profile aa365-admin --region us-west-1`),
   then restart again. Vendor keys: re-enable the old key at the vendor if it was revoked.
6. Revoke the old value at the source once the new one works (vendor keys).

### 2. RDS logins (master `aa-cis/dev/rds`, `cis_app`, `db_migrator`, `crm_app`, `aa_app_user`, Booking and TripPlanner DSNs)

- Master: Terraform ignores password changes, so the rotation is "change the password, then the secret, then every
  reader". Scheduled for prod (D-03); after X1 the master is break-glass only (DM-8.9). Plan it in AA-880, do not
  improvise it on Dev.
- `cis_app`, `db_migrator` and `crm_app` (the `password_roles` of AA-CIS-Infra `db/owners.yaml`; secrets
  `aa-cis/dev/rds-cis-app`, `aa-cis/dev/db-migrator`, `crm/dev/database-url`): the tech lead writes the new DSN into
  the role's secret; then [DB Migrate](db-migrate.md) `mode=set-password` with that role sets the password from the
  secret and test-connects. Then restart the services that read it (`crm_app`: `aa-crm-dev-api`).
- Other logins (`aa_app_user`, Booking, TripPlanner) are not in `set-password`: plan their rotation in AA-880.
- Rollback: write the previous DSN back and run `set-password` again.

### 3. Cognito app client secrets (`cis-admin`, `booking-staff`, their `-preview` clients, `breakglass`, `crm-staff`, `cis-portal`, `partner-web`, M2M clients)

- Every client with a secret is in AA-CIS-Infra `identity.tf` (WORKFORCE and EXTERNAL client maps),
  `identity_partner.tf` or `identity_m2m.tf`. The secrets live in Terraform state and in Vercel env or Secrets
  Manager (register rows). Rotation needs a Cognito client secret rotation and an update of every copy in the same
  window; sign-in breaks in between. UNTESTED, planned with the AA-816 cutover. Rollback:
  the previous client secret stays valid until it is deleted, if the rotation adds a second secret instead of
  replacing it.

### 4. Break-glass (`aa-identity/dev/breakglass`)

- `tools/identity/workforce_bootstrap.py breakglass-init` in AA-CIS-Infra writes a new password and TOTP seed with
  `PutSecretValue` only (it never reads the old value). The secret's resource policy allows only the MFA admin role, and
  any access sends an alert by design. See [break-glass](break-glass.md).

### 5. TripPlanner edge key (`tripplanner/dev/api-key`)

- Terraform `random_password` is the source. Replacing it is a local MFA apply from merged Infra `main`
  (`-replace=random_password.tripplanner_api_key`; the CI apply takes no arguments). The Lambdas read the secret by
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

- Every consumer in the register row works; the register's `last_changed` column is updated (names and dates only);
  the drift check prints `diff = 0` for that row.

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
