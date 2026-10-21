---
id: OPS-06-legacy-login
title: Switch off the legacy staff password login (AA-816 cutover)
description: Readiness checks, the flag change and the rollback for turning off the CIS username/password staff login once every active staff row signs in through Cognito.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [aa-cis-frontend, aa-cis-api]
last_reviewed: 2026-10-19
review_every_days: 90
last_tested: 2026-10-19
tested_where: dev-acc2
tested_evidence: docs/audits/2026-10-19-S244-aa816-cutover/cutover-report.md (S1, Production BFF flag off, S244)
related: [OPS-06, OPS-10, SEC-02-rotation, docs/adr/0006a-identity-phase1-amendments.md, AA-816, AA-680]
---

# Switch off the legacy staff password login (AA-816 cutover)

> [!WARNING]
> Partly tested. Steps 1-3 ran on Dev on 19/10/2026 (AA-816 Stage S, S244): **S1 is done on Production** — Vercel
> `aa-cis-frontend` Production holds the flag `false`, `POST /api/auth/login` answers 404, the login page shows only
> "Sign in with company email", Cognito E2E 7/7 after the change. The rollback (step 5) has not been needed or run.
> Preview keeps the legacy flag on (decision N-E) and the API flag is still on (S2, with AA-680). Evidence:
> `docs/audits/2026-10-19-S244-aa816-cutover/cutover-report.md`.
<!-- callout break -->
> [!NOTE]
> The flag is the legacy admin login flag, `LEGACY_ADMIN_LOGIN_ENABLED`. Its name contains underscores: Nghiệp edits
> it by hand (Vercel dashboard, or Terraform in VSCode). Agents do not write commands that set it.

## What the flag does (ADR 0006a A6)

- Values: on by default. Only `0`, `false`, `no` or `off` (case and spaces ignored) turn it off; unset, empty or a
  typo keeps the legacy login on. The API and the BFF parse it the same way.
- It gates the CIS UI password form, the BFF route `/api/auth/login` (404 when off) and the HS256 path of
  `/auth/verify-admin`.
- It does **not** gate `/auth/admin-login`. Booking no longer uses it: the CIS → Booking bridge and
  `/auth/booking-token` are retired (AA-911, ADR 0006a A11), so S2 is possible once the CIS PR UI smoke has another
  sign-in (see A11).
- It is read in two places: the BFF (Vercel `aa-cis-frontend` environment, per target) and the API (ECS task
  definition; not set today, so on). The API serves Production and Preview alike.
- Recommended cutover (S243 plan, Nghiệp's call N5): turn off **only the Production BFF**. The API stays on until
  AA-680, so Booking and Preview logins keep working.

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

6. The principal-aware admin-secret check, the Preview credential and the admin-secret rotation (AA-816 C9 + I6,
   [secret rotation](secret-rotation.md)) did not wait for AA-680 (decision N-C): done on 19/10/2026 right after S1.
   Later, with AA-680 shipped (S2): the API flag off (Terraform env on the api task definition, an Infra PR edited by
   hand). Decision N-E: the API flag stays on until Previews have another way to sign in.

## Verify the result

- Production: password route 404, Cognito sign-in works for every staff member.
- Preview: unchanged (password login still works there, by design).

## Roll back or abort

- Step 5 restores the legacy login in one redeploy (about 2 minutes). Abort before step 2 if step 1 shows an unlinked
  active human row.

## Escalation

- Staff locked out of the admin: SEV2; use step 5 first, then [break-glass](break-glass.md) if nobody can sign in.

## Tested log

| Date | Where | By | Evidence | Result |
|---|---|---|---|---|
| 2026-10-19 | dev-acc2, step 1 only (S243 main session) | Claude Code | `docs/audits/2026-10-19-S243-platform-lanes/aa816-readiness-snapshot.json`: Nghiệp linked; break-glass and Ms. Thư not linked yet; two e2e accounts without email | not ready |
| 2026-10-19 | dev-acc2, steps 1-3 on Production (S244 main session) | Claude Code + Nghiệp | `docs/audits/2026-10-19-S244-aa816-cutover/cutover-report.md`: readiness snapshot (7 active rows; no email: the three `e2e-claude-code*` rows; no `cognito_sub` before the break-glass link: `admin`, the three e2e rows, `thu` — `thu` ready per N-A, `admin` linked by the break-glass test), Production flag `false` + redeploy, `POST /api/auth/login` 404, login page email-only, Cognito E2E 7/7 | pass (S1 done; rollback step 5 not run) |
