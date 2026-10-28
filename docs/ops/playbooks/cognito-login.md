---
id: OPS-04-cognito-login
title: Staff cannot sign in (Cognito)
description: Diagnose a staff member or everyone failing to sign in to the CIS admin with the company e-mail code, and the ways back in.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-workforce-dev, aa-cis-frontend, aa-cis-api]
last_reviewed: 2026-10-28
review_every_days: 90
related: [OPS-04, OPS-10, OPS-06-legacy-login, OPS-04-ses-bounce, docs/adr/0006a-identity-phase1-amendments.md, AA-703, AA-816]
---

# Staff cannot sign in (Cognito)

> [!WARNING]
> UNTESTED - written from ADR 0006a and the S242 evidence; not yet used in a real incident.

## How sign-in works (one paragraph)

The admin login page sends staff to the managed login on `https://staff-auth.lumiguides.it.com` (WORKFORCE pool
`aa-workforce-dev`, client `cis-admin`, authorization code + PKCE). Cognito e-mails a code through SES
(`no-reply@lumiguides.it.com`, configuration set `aa-email-dev-workforce`). The pre token trigger refuses anyone without
a verified `@adventure.asia` address or a staff group. The BFF exchanges the code and sends the Bearer token to the API,
which binds the token to a row in `shared.admin_users` (first sign-in by e-mail, then by `cognito_sub`). The legacy
password login is off since AA-816 S2 (2026-10-22) ([legacy login flag](../runbooks/legacy-login-flag.md)).

## Triggers

- A staff member reports "no code", "not authorised", or a loop back to the login page.
- Alarms: `aa-identity-dev-workforce-pre-token-errors` (20 or more refusals or errors in 5 minutes),
  `…-pre-token-throttles`, `…-pre-token-duration-p99`, the same three for `…-workforce-pre-sign-up`,
  `aa-identity-dev-trigger-unexpected-error`, `aa-identity-dev-waf-blocked` and `aa-email-dev-bounce-rate`. The
  `aa-identity-dev-external-*` alarms (the EXTERNAL pool, no live staff sign-in) link here too. Conditions: the
  [alarm catalog](../../generated/alarms.md).
- Chrome shows "Dangerous site" for lumiguides.it.com (Safe Browsing review of 2026-10-18; backlog §1).

## Steps (one person)

```bash
POOL=$(aws cognito-idp list-user-pools --max-results 20 --profile aa365-admin --region us-west-1 --query "UserPools[?Name=='aa-workforce-dev'].Id" --output text)
aws cognito-idp admin-get-user --user-pool-id $POOL --username <their-email> --profile aa365-admin --region us-west-1 --query "{enabled:Enabled,status:UserStatus,mfa:UserMFASettingList}" --output json
aws cognito-idp admin-list-groups-for-user --user-pool-id $POOL --username <their-email> --profile aa365-admin --region us-west-1 --query "Groups[].GroupName" --output text
```

| Finding | Cause and fix |
|---|---|
| `UserNotFoundException` | Not created. Create them on the admin **Staff** page (owner only); the invite e-mail follows. |
| `enabled: false` | Disabled on the Staff page (left the company, or by mistake). Owner re-enables on the Staff page. |
| No group | The pre token trigger refuses ("Not authorised for AA staff sign-in"). Set the role on the Staff page (it writes the Cognito group). |
| Signed in at Cognito but the admin answers 401/403 | No active `admin_users` row, or the row is bound to another `sub` (never rebound automatically, ADR 0006a A7). Owner fixes it on the Staff page; the reconcile job lists such drift. |
| No code e-mail | Check spam; then SES: [SES bounce](../runbooks/ses-bounce.md) step 2 (is the address suppressed?) and `aws sesv2 get-account --profile aa365-admin --region us-west-1 --query EnforcementStatus` (expect `HEALTHY`). |
| The break-glass user | It never gets an e-mail code (TOTP enrolled, probe 2026-10-19); it uses password + TOTP ([break-glass](../runbooks/break-glass.md)). |

## Steps (everyone)

1. Is the managed login up? `curl -s -o /dev/null -w "%{http_code}\n" https://staff-auth.lumiguides.it.com/login` and
   the Cognito service health in the AWS Health dashboard. Expected: `400` (the page answers, but the request has no
   client parameters; checked 2026-10-28). A 5xx or no answer means the managed login is down.
2. Trigger errors: `aws logs tail /aws/lambda/aa-identity-dev-workforce-pre-token --since 30m --profile aa365-admin --region us-west-1`.
   A broken trigger release: roll back its Terraform change ([rollback-terraform](../runbooks/rollback-terraform.md)).
3. The custom domain fails but Cognito works: the tech lead points the BFF back at the pool's prefix domain with the
   workforce-domain override (a Vercel env value on `aa-cis-frontend`). ADR 0006a A5 calls this the zero-deploy
   rollback because no code changes; Vercel still needs a production redeploy to pick up the value.
4. Get in while it is broken: [break-glass](../runbooks/break-glass.md). The legacy password login is off since
   AA-816 S2 (2026-10-22); bringing it back is a deploy, not a switch ([legacy login flag](../runbooks/legacy-login-flag.md), Roll back).

## Close

- The person signs in; their row shows `last_login_at`. Write the cause in the issue; a gap in alarms becomes an issue.
