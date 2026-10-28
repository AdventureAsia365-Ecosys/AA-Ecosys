---
id: OPS-10
title: Use a break-glass path
description: The emergency ways in when the normal path is broken - the Cognito break-glass admin, the RDS master, the tenant-pool switch and the deploy-gate override - and what each use must record.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-workforce-dev, aa-cis-frontend, aa-cis-api, aa-cis-dev-db]
last_reviewed: 2026-10-28
review_every_days: 90
last_tested: 2026-10-19
tested_where: dev-acc2
tested_evidence: docs/audits/2026-10-19-S244-aa816-cutover/cutover-report.md (section A end to end through managed login, AA-816 Stage S checklist B3-B7, S244)
related: [OPS-10-deploy-gate, OPS-06, SEC-02-rotation, OPS-05-db-migrate, docs/adr/0006a-identity-phase1-amendments.md, AA-703, AA-816, AA-854]
---

# Use a break-glass path

> [!WARNING]
> Partly tested. Section A passed end to end on 2026-10-19 (AA-816 Stage S, S244): enable, sign-in through the
> managed login page with password + TOTP (token alarm to ALARM as designed), sign-out through the managed-login
> `/logout`, a new sign-in asks for the password again, close, then password + TOTP rotation (`breakglass-init`,
> `breakglass-verify` OK). The API-only check passed on 2026-10-18 (AA-854, S242). Sections B, C and D are untested.

Every use of any path on this page is written in the session log and the Linear issue: who, when, why, what was
done, and when it was closed again (ADR 0006 decision 11, DM-8.9).

## A. Cognito break-glass admin (nobody can sign in to the CIS admin)

Facts: user `admin@adventure.asia` in the WORKFORCE pool `aa-workforce-dev`, groups `cis-admin` + `booking-admin`,
TOTP enrolled, **disabled at rest**. Its `shared.admin_users` row (`admin`) is linked to the Cognito user since the
2026-10-19 managed-login test and has no legacy password any more (`password_hash` cleared by AA-CIS-Infra #224
run-script, with an audit row). Secret `aa-identity/dev/breakglass` (JSON: username, password, TOTP seed, pool
and client IDs) is readable only by the MFA admin role; every read or write sends an alert e-mail by design. Each token
issued fires `aa-identity-dev-breakglass-token-issued`.

```bash
aws sts get-caller-identity --profile aa365-admin
POOL=$(aws cognito-idp list-user-pools --max-results 20 --profile aa365-admin --region us-west-1 --query "UserPools[?Name=='aa-workforce-dev'].Id" --output text)
```

Expected: the acc2 account from the [account map](../../onboarding.md#account-map); `$POOL` is set.

1. Enable the user.

   ```bash
   aws cognito-idp admin-enable-user --user-pool-id $POOL --username admin@adventure.asia --profile aa365-admin --region us-west-1 # WRITE
   ```

   Verify: `aws cognito-idp admin-get-user --user-pool-id $POOL --username admin@adventure.asia --profile aa365-admin --region us-west-1 --query Enabled` is `true`.
   Rollback: step 5.

2. The tech lead reads the secret in the Secrets Manager console (alert e-mail expected) and adds the TOTP seed to an
   authenticator if it is not there yet. The password and the TOTP seed were rotated on 2026-10-19: a seed added
   before that date no longer works.

3. Open `https://aa-cis.lumiguides.it.com/api/auth/signin/cognito-breakglass` and sign in with password + TOTP. The
   token alarm fires; the session refresh window is 1 hour.

4. Do the emergency work. Any `client_id` other than `breakglass` in the token log line is an incident in itself.

5. Close: log out from the Topbar (expected: the browser passes through the managed-login `/logout` and lands on
   `/login`; opening the break-glass sign-in URL again asks for the password again), then revoke and disable.

   ```bash
   aws cognito-idp admin-user-global-sign-out --user-pool-id $POOL --username admin@adventure.asia --profile aa365-admin --region us-west-1 # WRITE
   aws cognito-idp admin-disable-user --user-pool-id $POOL --username admin@adventure.asia --profile aa365-admin --region us-west-1 # WRITE
   ```

   Verify: `Enabled` is `false`; the alarm returns to `OK`.
   Then rotate the password ([secret rotation](secret-rotation.md) class 4).

API-only check without the UI: AA-CIS-Infra `tools/identity/workforce_bootstrap.py breakglass-verify` (enable, sign
in, revoke, disable; fails closed if cleanup fails).

## B. RDS master login

- Since X1 S18 (2026-10-19) the CIS runtime logs in as `cis_app`, and since S19 the CIS task role cannot read the
  master secret. Any use of the master outside DB Migrate counts as break-glass use (DM-8.9).
- The master is break-glass only. The normal master path is a reviewed script through
  [DB Migrate run-script](db-migrate.md), which needs a merged PR. If even that is impossible (GitHub down, SEV1), the
  break-glass path is a one-off run of the migrator task by hand - write down every statement, and rotate the master
  password afterwards (from prod; on Dev per D-03 at prod time).

## C. Tenant-pool emergency switch

- Each tenant route that runs on the RLS tenant pool has its own flag ([feature flags](../feature-flags.md)).
  Fail closed: only an explicit `false` sends a route back to the admin pool.
- Fast, not durable: set the route's Redis key to `false` (lost when Redis restarts).
- Durable: add the flag key to the API's force-admin list (task definition environment, Terraform, edited by hand),
  then deploy. Use only when a tenant route is broken by RLS and the tenant is blocked; it removes a security control
  for that route, so open a SEV2 issue and remove it again after the fix.

## D. Deploy-gate override

- [Override a deploy or migration gate](deploy-gate-override.md).

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-10-18 | dev-acc2 | Claude Code + tech lead | S242 session log, `docs/audits/2026-10-18-S242-cognito-phase1/aa854-evidence.md` (API break-glass verify) | pass (A via API only) |
| 2026-10-19 | dev-acc2 | Claude Code (S243 main session) | `docs/audits/2026-10-19-S243-platform-lanes/aa816-breakglass-otp-probe.json` | pass: with TOTP enrolled, no client offers the email code to break-glass (password only, no token issued by the probe); cleanup clean |
| 2026-10-19 | dev-acc2 | Claude Code (S244 main session) + tech lead | `docs/audits/2026-10-19-S244-aa816-cutover/cutover-report.md` (checklist B3-B7) | pass: managed-login sign-in (password + TOTP, alarm ALARM as designed), sign-out through managed-login `/logout`, re-ask on the next sign-in, close; legacy `password_hash` cleared (Infra #224); password + TOTP rotated by `breakglass-init`, `breakglass-verify` OK |
