# AA-816 — Cognito Phase 1 cutover (Stage S): report

What was run on 19/10/2026 (S244, Claude Code main session + Nghiệp) against the plan in
[cutover-prep.md](cutover-prep.md), step by step, with the evidence for each step and what is still open.
Agent: Claude Code. Dev only (acc2, us-west-1). No secret value, partial value or hash appears in this file.
Pool and client ids are not copied (they are looked up at run time, as in the plan).

Result in one line: **S1 is done on Production** (the CIS admin has no password login any more), the Preview god-key
is gone (C9), the main admin secret and the break-glass credentials are rotated (I6, B7), and the break-glass path
through managed login is proven. S2 (API flag off) waits for AA-680, as planned.

## Decisions taken (plan "Decisions needed from Nghiệp")

| Id | Decision | How it shows |
|---|---|---|
| N-A | Passwordless rows with an email and a CONFIRMED Cognito user count as ready | `thu` stays listed as not linked; S1 went ahead |
| N-B | Clear the break-glass row's legacy `password_hash` through a reviewed DB Migrate `run-script` | AA-CIS-Infra #224 |
| N-C | Readiness → S1 → C9 + Preview credential + I6 right after, without waiting for AA-680 | All done the same day |
| N-D | Live HS256 production sessions expire on their own (24 h); no BFF change | CIS #858 notes |
| N-E | The API flag stays on until a Preview sign-in exists | API flag untouched; Preview BFF flag on |
| N-F | `e2e-claude-code-2`: disable now (proposed) | **Open**: needs an owner Cognito session on the Staff page (Nghiệp) |

## Checklist: done and evidence

| Step (plan) | Status | Evidence |
|---|---|---|
| A1 Sign-out PR + `e2e-cognito.yml` | Done | AA-CIS-App #856 (sign-out same-origin only; the E2E proves a new email code after sign-out). Cognito E2E 7/7 after S1 |
| A3 AA-878 N1: GitHub `E2E_ADMIN_*` → viewer (hand edit) | Done | GitHub AA-CIS-App `E2E_ADMIN_*` hold the `e2e-claude-code-viewer` values (`aa-cis/dev/e2e-test-viewer`); the preview smoke runs in viewer mode: 59 passed / 7 skipped (AA-CIS-App #859 added the ops-overview skip for a viewer run) |
| A4 N-F: disable `e2e-claude-code-2` | **Open** | Still active; see "What remains" |
| B1-B5 Break-glass through managed login | Pass | Playwright run: enable; sign-in at `/api/auth/signin/cognito-breakglass` with password + TOTP; token alarm `aa-identity-dev-breakglass-token-issued` went to ALARM as designed; sign-out through the managed-login `/logout`; the next sign-in asks for the password again; close (global sign-out + disable). The sign-in linked the `admin` row by email |
| B6 N-B: clear the `admin` row's legacy `password_hash` | Done | AA-CIS-Infra #224 (`run-script`, one row, audit row `a64deb6e…` in the same transaction) |
| B7 Rotate the break-glass password | Done | AA-CIS-Infra `tools/identity/workforce_bootstrap.py breakglass-init` (password + TOTP), then `breakglass-verify` OK. Secret `aa-identity/dev/breakglass` LastChangedDate 2026-10-19 12:20 UTC (`list-secrets`, metadata only) |
| C Readiness snapshot | Done | Counts below |
| D1 Retire `scripts/create_staff_user.py`; N-D change | Done (no N-D change, by decision) | AA-CIS-App #858 (D1) |
| D2 Production `LEGACY_ADMIN_LOGIN_ENABLED` = `false` (hand edit) + production redeploy | Done | Vercel `aa-cis-frontend`, Production target only. Preview keeps the legacy flag (N-E) |
| D3 Verify S1 | Pass | `POST https://aa-cis.lumiguides.it.com/api/auth/login` → 404; the login page shows only "Sign in with company email"; Cognito E2E 7/7 after the change |
| D4 Rollback | Not needed, not run | Root runbook OPS-06-legacy-login step 5: set the Production value back to `true` (or delete it), then redeploy production |
| D5 Root follow-ups | This PR | `skill/aa-ui-verify/SKILL.md`, runbook tested logs (`break-glass.md`, `legacy-login-flag.md`), secrets register |
| E1 C9: principal-aware admin-secret check + Preview credential (code) | Done | AA-CIS-App #858: the API admin-secret guards accept a verified Cognito principal; the Preview credential, read by the code-constant name `aa-cis/dev/admin-secret-preview` (`api/core/staff_credential.py`), gives a principal capped at viewer, never the machine |
| E2 Create the Preview secret | Done | `aa-cis/dev/admin-secret-preview`, created 2026-10-19 12:33 UTC (`list-secrets`); about 0.40 USD a month |
| E3 Vercel Preview `ADMIN_SECRET` → the Preview value (hand edit) | Done | Preview smoke in viewer mode green (59 passed / 7 skipped) |
| F I6: rotate `aa-cis/dev/admin-secret` | Done | LastChangedDate 2026-10-19 13:13 UTC (`list-secrets`). New value → 200, old value → 403 on a machine route. Copies updated: GitHub AA-CIS-App env `dev` `ADMIN_SECRET`, Vercel `aa-cis-frontend` Production `ADMIN_SECRET`. ECS api + worker restarted (force new deployment) |

## Readiness snapshot (checklist C)

Read-only, 19/10/2026 (cutover readiness block of the Staff page / `GET /admin/platform/staff-directory/health`).

| Count | Value |
|---|---|
| `active_rows` | 7 |
| `missing_email` (3) | `e2e-claude-code`, `e2e-claude-code-2`, `e2e-claude-code-viewer` |
| `missing_cognito_sub` before the break-glass link (5) | `admin`, `e2e-claude-code`, `e2e-claude-code-2`, `e2e-claude-code-viewer`, `thu` |
| `missing_cognito_sub` after the break-glass link (4, derived from B3, not a second snapshot) | the three e2e rows, `thu` |

Read with the plan's per-account table: the three e2e rows are the agreed test rows (kept for Preview and Booking
until S2; `-2` to be disabled per N-F); `thu` is ready per N-A; `admin` was linked by the managed-login break-glass
test (B3). The other active rows (`nghiep`, the E2E Cognito reviewer row) have an email and are linked.

## State after S244

| Path | Before | After |
|---|---|---|
| CIS admin on Production | Password form + email code | Email code only (Cognito) |
| CIS PR previews | Password form, BFF held the main admin secret (full admin) | Password form still there, BFF holds the Preview credential: every session has viewer rights |
| PR smoke (`ui-smoke.yml`) | `e2e-claude-code` (full admin) | `e2e-claude-code-viewer` (viewer mode) |
| Main admin secret copies | GitHub (repo level), Vercel Production + Preview | GitHub AA-CIS-App env `dev`, Vercel Production |
| Break-glass row | Not linked, legacy password hash set | Linked, no legacy password; password + TOTP rotated |
| Staff creation | `create_staff_user.py` (password rows) | Staff page (Cognito users); the script is gone |
| API legacy flag, Booking `/auth/admin-login` + `/auth/booking-token` | On | On (S2, AA-680) |

## What remains

1. **N-F** — disable `e2e-claude-code-2` on the Staff page (audited `staff.disabled`). Needs an owner Cognito
   session: Nghiệp. Re-enable is one audited click when a Booking maker-checker check is due.
2. **S2** — API flag off (Infra task-definition env, hand edit in VSCode), with AA-680 and only once Previews have
   another way to sign in (N-E). Then disable `e2e-claude-code`.
3. **A10** — remove the temporary E2E staff exception (the E2E mailbox address) when the E2E work is finished.
4. **AA-680 bridge removal** — Booking stops using `/auth/admin-login` / `/auth/booking-token` (Booking accepts
   Cognito tokens); then `aa-cis/dev/booking-jwt-signing-key` can be retired.
5. **Repo-level GitHub `ADMIN_SECRET`** on AA-CIS-App: the I6 copy went to env `dev`. If the repo-level copy still
   exists it holds the refused pre-I6 value: the main session confirms it with a secret listing and deletes it
   (register row `orphan-delete`).
6. **TOTP** — the break-glass TOTP seed changed with B7: Nghiệp re-adds the new seed to an authenticator if he wants
   one (a seed added before 19/10 no longer works).
7. Open, not part of this cutover: the API's header trust for the main secret stays until S2 (whoever holds it can
   claim any role); the CIS task role still reads `*` minus the explicit Denies (register item 2).

## Tradeoffs seen in practice

- Previews can no longer check admin writes or admin-only pages: those checks now happen on Production after merge
  (Nghiệp signs in with the email code), or on reviewer pages through `e2e-cognito.yml`. The `aa-ui-verify` skill says
  so.
- The legacy `e2e-claude-code` password still opens the API's `/auth/admin-login` until S2; through a Preview BFF it
  reaches only viewer rights.
