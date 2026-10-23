---
id: OPS-06-legacy-login
title: Switch off the legacy staff password login (AA-816 cutover)
description: Readiness checks, the flag change and the rollback for turning off the CIS username/password staff login once every active staff row signs in through Cognito.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-frontend, aa-cis-api]
last_reviewed: 2026-10-23
review_every_days: 90
last_tested: 2026-10-23
tested_where: dev-acc2
tested_evidence: docs/audits/2026-10-19-S244-aa816-cutover/cutover-report.md (S1, S244); Linear AA-816 S247 comment + S248 live check (S2)
related: [OPS-06, OPS-10, SEC-02-rotation, docs/adr/0006a-identity-phase1-amendments.md, AA-816, AA-680]
---

# Switch off the legacy staff password login (AA-816 cutover)

> [!IMPORTANT]
> **Both stages are done.** S1 (19/10/2026, S244): Vercel `aa-cis-frontend` Production holds `false`. S2
> (22/10/2026, S247, CIS #922): the **code default is now off** in the API and the BFF, so every host refuses
> password sessions, Preview included; previews sign in through Cognito on the fixed Preview host (ADR 0006a A11,
> A12). Live check 23/10/2026 (S248): api task definition without the variable, `POST /api/auth/login` → 404,
> an HS256-shaped token on `/auth/verify-admin` → 401 "Password sessions are switched off; sign in again".
> This page is now the **rollback** reference; steps 1-3 below are the history of S1.
<!-- callout break -->
> [!NOTE]
> The flag is the legacy admin login flag, `LEGACY_ADMIN_LOGIN_ENABLED`. Its name contains underscores: Nghiệp edits
> it by hand (Vercel dashboard, or Terraform in VSCode). Agents do not write commands that set it.

## What the flag does (ADR 0006a A6)

- Values (since S2, ADR 0006a A12): **off by default**. Only `1`, `true`, `yes` or `on` (case and spaces ignored)
  turn it on; unset, empty or a typo keeps the legacy login off. The API and the BFF parse it the same way. Before
  S2 the rule was the reverse (on unless explicitly off).
- It gates the CIS UI password form, the BFF route `/api/auth/login` (404 when off) and the HS256 path of
  `/auth/verify-admin`.
- It does **not** gate `/auth/admin-login` or `/auth/booking-token`: Booking staff still sign in through them until
  AA-680 (Phase 2).
- It is read in two places: the BFF (Vercel `aa-cis-frontend` environment, per target; Production holds `false`)
  and the API (ECS task definition; not set, so off). The API serves Production and Preview alike.
- History: S1 turned off only the Production BFF (Nghiệp's call N5); S2 flipped the code default once Preview had
  a Cognito sign-in (ADR 0006a A11).

## Preconditions (readiness)

- Every active `shared.admin_users` row that a person uses has an email and its own `cognito_sub`. Check on the
  admin **Staff** page (cutover readiness block) or `GET /admin/platform/staff-directory/health`.
- Accounts without a person (`e2e-claude-code*`) have a decision: disabled, or kept with Preview-only use (AA-878 D4).
- The break-glass path through managed login (`/api/auth/signin/cognito-breakglass`) was tested
  ([break-glass](break-glass.md)), so there is a way in if Cognito sign-in breaks.
- Ms. Thư and every other staff member signed in once with the email code. S243/S244 (decision N-A): a row with no
  password, an email and a CONFIRMED Cognito user (Ms. Thư) counts as ready, because the flag cannot lock it out; it
  links itself on the first email-code sign-in.
- Cost: 0 USD.

## Steps

1. Snapshot readiness (read-only). Staff page, or a CIS [ECS exec](ecs-exec-s3-mediated.md) script:
   `SELECT username, is_active, email IS NOT NULL AS has_email, cognito_sub IS NOT NULL AS linked FROM shared.admin_users ORDER BY username`.
   Expected: every active human row `has_email` and `linked`.
   Verify: save the output under `docs/audits/<date>-S<nnn>-aa816-cutover/`.
   Rollback: none - read-only.

2. Nghiệp sets the flag to `false` on Vercel `aa-cis-frontend`, **Production** target only (dashboard, Settings,
   Environment Variables), then redeploys production (Vercel env changes apply only to new deployments): dispatch
   `vercel-deploy.yml` on AA-CIS-App with target production, or **Redeploy** in the dashboard. # WRITE
   Expected: a new production deployment `READY`.
   Rollback: step 5.

3. Verify the cutover.

   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" -X POST https://aa-cis.lumiguides.it.com/api/auth/login
   ```

   Expected: `404` (the BFF route is off). The login page shows only "Sign in with company email".
   Verify: one staff member signs in with the email code and opens an admin page; the API log shows
   `staff_bearer_verified`.

4. Watch for one working day: no staff member locked out, `aa-identity-dev-workforce-pre-token-errors` stays OK.
   Two login paths coexist on the API for the legacy window (30 days after cutover, ADR 0006a).

5. Rollback (any time): Nghiệp deletes the Production value or sets it to `true`, then redeploys production.
   Expected: the password form is back and `/api/auth/login` no longer answers 404.
   **Since S2 this alone is not enough** (unset = off, and the API refuses HS256): see Roll back below.

6. The principal-aware admin-secret check, the Preview credential and the admin-secret rotation (AA-816 C9 + I6,
   [secret rotation](secret-rotation.md)) did not wait for AA-680 (decision N-C): done on 19/10/2026 right after S1.
7. S2 (22/10/2026, S247): CIS #922 flipped the default to off in `api/core/staff_identity.py` and
   `frontend/lib/staffSession.ts`, after the Preview Cognito sign-in (CIS #911) and the smoke split (CIS #912) were
   live. No Terraform change: the api task definition never set the variable. Then Nghiệp disabled the legacy
   account `e2e-claude-code` on the Staff page.
   Verify (any time, read-only):

   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" -X POST https://aa-cis.lumiguides.it.com/api/auth/login
   curl -s -X POST https://api-cis.lumiguides.it.com/auth/verify-admin -H 'content-type: application/json' -d '{"token":"a.b.c"}'
   ```

   Expected: `404`, then `{"detail":"Password sessions are switched off; sign in again"}`. The CIS Cognito E2E
   (`e2e-cognito.yml`, dispatch from `main`) stays green.

## Verify the result

- Production and the fixed Preview host: password route 404, Cognito sign-in works (Preview capped at viewer).
- Per-deployment previews: no staff sign-in; their UI smoke runs the public specs only.
- AA-Booking: unaffected (`/auth/admin-login` and `/auth/booking-token` are not gated, until AA-911 P6b).

## Roll back or abort

- Since S2, unset means off, so deleting the Vercel value no longer brings the password form back. Two ways:
  - **Revert** CIS #922 (`30b64228`) through a PR, then Deploy Dev (api + worker) and a Vercel production deploy.
    Simplest; restores the old default everywhere.
  - **Flag on:** set the variable to `true` on the api task definition (AA-CIS-Infra, hand edit in VSCode, Terraform
    apply of the api service) **and** on the Vercel target (Production and/or Preview), then redeploy both. Both
    sides are needed: a BFF form whose sessions the API refuses bounces at the first verify.
  - Either way, a legacy account must be active to use the form: `e2e-claude-code*` are disabled (Staff page).
- Step 5 above describes the pre-S2 rollback of S1 and no longer works alone.

## Escalation

- Staff locked out of the admin: SEV2; use step 5 first, then [break-glass](break-glass.md) if nobody can sign in.

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-10-19 | dev-acc2, step 1 only (S243 main session) | Claude Code | `docs/audits/2026-10-19-S243-platform-lanes/aa816-readiness-snapshot.json`: Nghiệp linked; break-glass and Ms. Thư not linked yet; two e2e accounts without email | not ready |
| 2026-10-19 | dev-acc2, steps 1-3 on Production (S244 main session) | Claude Code + Nghiệp | `docs/audits/2026-10-19-S244-aa816-cutover/cutover-report.md`: readiness snapshot (7 active rows; no email: the three `e2e-claude-code*` rows; no `cognito_sub` before the break-glass link: `admin`, the three e2e rows, `thu` — `thu` ready per N-A, `admin` linked by the break-glass test), Production flag `false` + redeploy, `POST /api/auth/login` 404, login page email-only, Cognito E2E 7/7 | pass (S1 done; rollback step 5 not run) |
| 2026-10-22 | dev-acc2, S2 (S247 main session) | Claude Code + Nghiệp | Linear AA-816 S247 comment: HS256 on `/auth/verify-admin` 200 → 401 after CIS #922; `/auth/booking-token` unchanged; BFF `/api/auth/login` 404; Cognito E2E green (run 39720383620); `e2e-claude-code` disabled | pass |
| 2026-10-23 | dev-acc2, step 7 verify, read-only (S248 lane) | Claude Code | api task definition `aa-cis-dev-api:775`, image `dev-5a54bd26…`, no `LEGACY_*` env; `POST /api/auth/login` 404; HS256-shaped token → 401 "Password sessions are switched off" | pass |
