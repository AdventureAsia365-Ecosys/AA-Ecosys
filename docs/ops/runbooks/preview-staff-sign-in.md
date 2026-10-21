---
id: OPS-06-preview-signin
title: Sign staff in on a Vercel preview (fixed Preview host)
description: How the fixed Preview host of each staff app is pointed at the preview under test, how to check which deployment it serves, and what to do when sign-in fails there.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-booking-admin, aa-cis-frontend]
last_reviewed: 2026-10-21
review_every_days: 90
last_tested: never
tested_where: none
tested_evidence: none
related: [OPS-06-legacy-login, OPS-02-vercel, docs/adr/0006a-identity-phase1-amendments.md, AA-911, AA-816]
---

# Sign staff in on a Vercel preview (fixed Preview host)

> [!WARNING]
> UNTESTED. Written with AA-911 (S246) before the first alias. Fill in "What check V1 found" after the first run.

ADR 0006a A11 gives each staff app **one** fixed Preview host. It is a registered Cognito WORKFORCE callback, so
staff sign in there with an email code, exactly as on Production. A per-deployment preview URL
(`https://<project>-<hash>.vercel.app`) has no staff sign-in.

## Host map

| App | Preview host | Vercel project | Cognito client | Production hosts |
|---|---|---|---|---|
| AA-Booking staff admin | `booking-preview.lumiguides.it.com` | `aa-booking-admin` | `booking-staff` | `booking.lumiguides.it.com`, `aa-booking-admin.vercel.app` |
| AA-CIS admin | `aa-cis-preview.lumiguides.it.com` | `aa-cis-frontend` | `cis-admin` (break-glass: Production only) | `aa-cis.lumiguides.it.com` |

Pieces: Vercel project domain (bound to the never-pushed branch `preview-signin`), Route 53 CNAME (AA-CIS-Infra
`custom_domain_vercel_hosts`), callback and sign-out URL (AA-CIS-Infra `identity_client_urls`), the Preview target of
the client-secret env var in Vercel (set by hand), and the frontend allowlist (a preview build accepts only its
Preview host, `VERCEL_ENV`).

## Point the host at a preview (opt-in)

The host moves only when someone asks for it. Two ways, both in the app repo's **Vercel Deploy** workflow:

1. **PR label.** Add the label `preview-signin` to a same-repo PR. The run deploys the preview (one deployment
   against the Hobby cap) and then aliases it. Later pushes to that PR keep moving the host while the label stays.
   The PR gets a comment line saying the host now serves that commit.
2. **Alias-only dispatch (preferred when the preview already exists).** No deployment, so no cap use. Run it **from
   `main`** (a run on any other ref is refused):
   `gh workflow run vercel-deploy.yml --repo AdventureAsia365-Ecosys/AA-Booking --ref main -f target=preview -f alias_only_url=https://aa-booking-admin-<hash>.vercel.app`
   (CIS: `--repo AdventureAsia365-Ecosys/AA-CIS-App` and `https://aa-cis-frontend-<hash>.vercel.app`).
   The job checks over the Vercel API that the URL is a READY, non-production deployment of the same project.

CLI fallback (a person with the team's Vercel token, one line):
`npx vercel@60.0.1 alias set <deployment-url> booking-preview.lumiguides.it.com --scope <team> --token $VERCEL_TOKEN`

Only one preview at a time can be signed in to per app. Point the host back at the PR you are testing before each
check.

## Check which deployment it serves

- `npx vercel@60.0.1 alias ls --scope <team> --token $VERCEL_TOKEN` and find the Preview host, or
- the PR comment line ("Staff sign-in: … points at …"), or the alias job's step summary.

## The alias must point at a build made after the env var was set

A Preview env var reaches only deployments **built after** it was set (lesson S237). If the host serves an older
build, `/login` says "Company e-mail sign-in is not set up on this build". Fix: redeploy the PR (push, or re-run
the workflow), then alias the new deployment.

## Sign-in checks

- **Accept:** a person with a `booking-*` group (Booking) or a `cis-*` group (CIS) signs in with the email code and
  lands in the app. A CIS session on the Preview host has the person's **real** role (not the C9 viewer cap).
- **Refuse (Booking):** dispatch AA-CIS-App `e2e-cognito.yml` with `booking_base_url=https://booking-preview.lumiguides.it.com`.
  The E2E Cognito user (no `booking-*` group) must land on `/login?reason=no_booking_role`. Then run AA-CIS-Infra
  `db/scripts/aa680_staff_users_readonly_check.py` (DB Migrate `mode=run-script`): `e2e_has_no_booking_row=true`.
- Agents cannot sign in to the Booking UI (the E2E user may not hold a `booking-*` group, ADR 0006a A10). Booking UI
  checks are Nghiệp's.

## What check V1 found (Vercel protection)

To fill in after the first alias:
`curl -s -o /dev/null -w '%{http_code} %{redirect_url}' https://booking-preview.lumiguides.it.com/login`

- **401, or a redirect to vercel.com:** the host sits behind Vercel Authentication (Standard Protection). On Hobby
  only the team owner passes; share a Vercel link with other staff. The refusal E2E needs the CIS `e2e` secret
  `BOOKING_PREVIEW_BYPASS` (aa-booking-admin Protection Bypass for Automation).
- **200:** the host is public. Anyone can load the aliased preview's code, data still needs an email code and a
  staff group. The host never offers the legacy password form, and preview builds send `X-Robots-Tag: noindex`.

## When it goes wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| Cognito says `redirect_mismatch` | Callback not applied, or a host typo | `aws cognito-idp describe-user-pool-client --user-pool-id <pool> --client-id <id> --query 'UserPoolClient.CallbackURLs' --profile aa365-admin --region us-west-1` |
| "not set up on this build" | Alias points at a build older than the Preview env var | Redeploy, then alias the new build |
| The host shows another PR | Someone else re-pointed it | Re-point it (dispatch), check the PR comment |
| Alias job: "accepted only on refs/heads/main" | Dispatch from a branch | Dispatch with `--ref main` |
| Vercel 404 "deployment not found" on the host | Domain removed from the project or never added | Vercel project → Domains; check the CNAME with `dig CNAME <host>` |
