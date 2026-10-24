# ADR 0006 — Amendment A: identity Phase 1 as shipped (CIS staff on Cognito WORKFORCE)

- **Status:** Accepted (18/10/2026, S242). Records what Phase 1 (CIS staff login + staff directory) shipped on Dev
  and where it departs from the ADR 0006 text. Separate file referenced from `docs/adr/0006-ecosystem-identity.md`.
- **Amends:** ADR 0006 decision 3 (Booking role storage, who may write the directory, directory operations, IAM),
  decision 7 (what "reset" means), decision 10 (custom domain timing, DNS), decision 11 (break-glass address,
  secret shape, guards), decision 12 (branding now in Terraform), the Phase 1 row of the Migration plan (legacy
  flag scope) and the "Remaining open risks" list (the `AdminCreateUser` line). A10 (19/10/2026, S243) adds a
  temporary exception to the `@adventure.asia`-only staff rule for the E2E test account; A10a (24/10/2026, S250)
  adds a second E2E address for the Booking staff admin. A11 and A12 (22/10/2026,
  S247, recorded S248) add the Preview staff sign-in and switch the legacy flag off by default (cutover S2).
- **Implements:** ADR 0006 Phase 1 for CIS. Booking (Phase 2) is unchanged and still pending.
- **Plan and evidence:** `docs/audits/2026-10-18-S242-cognito-phase1/plan.md` (judged plan, stages A/B/S/D),
  `docs/audits/2026-10-18-S242-cognito-phase1/aa854-evidence.md` (Phase 0 done-when evidence).
  Implementation notes: AA-CIS-App `docs/implementation-notes/AA-816*.md`; AA-CIS-Infra
  `docs/implementation-notes/AA-854.md`, `AA-816.md`, `AA-816-staff-auth-domain.md`.
- **Related Linear:** AA-703 (epic), AA-854 (Phase 0 finish + Phase 1 prerequisites), AA-816 (staff directory).

## Context

Phase 0 finished on 18/10/2026: WORKFORCE pool `us-west-1_bCcFvbSOS` (`aa-workforce-dev`), a staff user signs in
with an email code through managed login, a user without a staff group is refused by the pre token trigger, self
sign-up is refused, and break-glass signs in with password + TOTP and raises its alarm. A user created with
`AdminCreateUser` (`MessageAction=SUPPRESS`, no password, `email_verified=true`) is `CONFIRMED` at once and signs
in with `EMAIL_OTP`, which answers open items 3c/3d: no random password and no `FORCE_CHANGE_PASSWORD` step.

Phase 1 then shipped in CIS (PRs #807–#813, #826) and Infra (#183–#186, #194):

- CIS migration 247 (identity columns + `shared.staff_app_grant`);
- the multi-issuer verifier and its use in `/auth/verify-admin` and a staff Bearer middleware;
- admin sign-in through Cognito (authorization code + PKCE in the BFF), legacy password login kept behind a flag;
- staff directory writes (create, roles, disable, enable, sign-out) and a report-only reconcile job;
- the CIS task role grant on WORKFORCE, break-glass secret alerts, and managed login on our own domain.

Building it forced the choices below. Each one replaces the matching ADR 0006 text.

## Decisions

### A1. Booking roles live in `shared.staff_app_grant`, not in a column on `admin_users`

Replaces "per-app role columns" (decision 3) and "Booking role column" (Phase 1 row).

- CIS 247 creates `shared.staff_app_grant (admin_user_id → admin_users ON DELETE CASCADE, app, role,
  created_at, updated_at)`, PK `(admin_user_id, app)`. `app` CHECK = `booking`; `role` CHECK =
  `admin | sales | contracting | content_creator` (the Booking `staff_users_role_chk` values). One row per
  person per app; a new app widens the CHECK in a CIS migration.
- `admin_users.role` stays NOT NULL and keeps the CIS role.
- The directory writes the grant first, then mirrors it to the `booking-<role>` WORKFORCE group.
- Booking does not read the table. It keeps the PR #721 bridge until Phase 2, and from Phase 2 it reads
  `cognito:groups` (decision 3, unchanged).
- The same migration adds to `admin_users`:
  - `email`: lower-case, exactly `…@adventure.asia`, unique on `lower(email)`;
  - `display_name`;
  - `cognito_iss` + `cognito_sub`: both set or both NULL, unique as a pair (decision 9);
  - `last_login_at`: means "last seen", written at most once per 60 s cache entry;
  - `is_owner`.

  `password_hash` becomes nullable. A NULL hash fails closed on the legacy login (401, not 500).

### A2. Only owners write the staff directory (`staff.write` = admin + Cognito session + `is_owner`)

Narrows decision 3 ("the directory's admin UI is the only writer").

- A directory write needs all three: CIS role `admin`; a request authenticated by a verified Cognito Bearer
  (`auth = cognito`; a legacy password session can read the directory but never write it); and
  `admin_users.is_owner = true`.
- There is no `platform-admin` group. Owner is a directory flag. It is set out of band by
  `scripts/link_staff_identity.py` (audited) and is never writable through the directory API.
- Every write locks the owner rows and re-reads the actor (active, `is_owner`, role `admin`) inside its own
  transaction. This closes the 60 s identity-cache window and the 15-minute window of a demoted owner's token.
- Guards: the last active owner cannot be demoted or disabled; nobody can demote or disable themselves.

### A3. Directory operations, and "reset" = sign-out everywhere + re-enable

Details decision 3 and decision 7.

- **Order:** the DB is written first, then Cognito (decision 3, unchanged).
  - If a Cognito step fails, the API answers 502 "saved, Cognito pending" with the failed step, and an
    idempotent retry (`POST …/{id}/sync`) repairs it.
  - Cognito steps run under a 20 s deadline, so the UI gets the pending answer before the API Gateway
    timeout.
- **Create:** `AdminCreateUser` with `MessageAction=SUPPRESS` and `email_verified=true`, `@adventure.asia`
  only, then the `cis-<role>` and `booking-<role>` groups. Cognito sends no mail; the staff invitation email
  is a follow-up (in progress).
- **Disable:** `AdminDisableUser`, then `AdminUserGlobalSignOut` (decision 7 order).
- **Enable:** `AdminEnableUser`.
- **Reset:** staff have no password to reset. "Reset" means `AdminEnableUser`, then
  `AdminUserGlobalSignOut`, plus `is_active = true` if the row was disabled. The person signs in again with a
  fresh email code.
- **Allow-list in code:** the CIS writer refuses any Cognito operation outside its allow-list, on top of IAM.
- **IAM:** `accounts/aa365/identity_iam.tf` grants the CIS task role exactly the eight decision-3 actions on
  the WORKFORCE pool ARN. The worker shares this role.
  - It adds an explicit Deny on both pools for `AdminSetUserPassword`, `AdminUpdateUserAttributes`,
    `AdminLinkProviderForUser`, `AdminInitiateAuth`, `AdminRespondToAuthChallenge`, `AdminDeleteUser` and
    `AdminSetUserMFAPreference`, so a later broad grant cannot undo the exclusions.
  - There is no EXTERNAL grant yet.
- **Break-glass row:** the break-glass row is read-only in the UI; every write to it answers 403.
- **Reconcile:** the job `staff_directory_reconcile` (`shared.job`) is report-only. It calls `ListUsers` /
  `ListUsersInGroup` only and reports these as drift:
  - Cognito users missing from the directory;
  - rows missing from Cognito;
  - group/role drift;
  - users bound to another `sub` or issuer;
  - status findings;
  - break-glass state.

  It also shows **cutover readiness**: active rows without an email or a `cognito_sub`. It runs on demand from
  the Staff page. The daily trigger needs one Infra line in the ops-probe Lambda's path list (follow-up).

### A4. Break-glass: address, secret shape, guards

Replaces decision 11's address and makes "readable only by the admin role, retrieval alerted" concrete.

- **Address `admin@adventure.asia`** (Nghiệp, S241), not `breakglass@…`. Nghiệp's own staff account is
  `nghieppham@adventure.asia`.
  - The break-glass user has TOTP enrolled. With optional MFA, an enrolled TOTP removes the email code as a
    first factor (decision 1), so the mailbox alone does not sign in.
  - Groups: `cis-admin` + `booking-admin`. MFA `SOFTWARE_TOKEN_MFA`.
  - It is kept **disabled** between uses.
- **Secret `aa-identity/dev/breakglass`:** JSON `{username, password, totp_seed, pool_id, client_id, created_at}`,
  with `created_at` in UTC ISO-8601.
  - It is written only by AA-CIS-Infra `tools/identity/workforce_bootstrap.py breakglass-init`, which uses
    `PutSecretValue` only and rotates without reading the old value. Terraform holds the container, never a
    version.
- **Resource policy:** denies `GetSecretValue` and `PutSecretValue` to every principal except the MFA admin role
  `nghiep-admin-8h-session` (by `aws:PrincipalArn`). `DescribeSecret` and `GetResourcePolicy` are not denied,
  so Terraform refresh keeps working.
- **Alerts:**
  - EventBridge rule `aa-identity-dev-breakglass-secret-access` (`ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS`)
    sends to the alerts SNS topic on any read or write of the secret. Denied attempts are included, as are
    `UpdateSecret`, resource-policy changes, delete/restore, replicate and rotate.
  - Alarm `aa-identity-dev-breakglass-token-issued` fires on every break-glass token issue, whichever client
    is used. Any `client_id` other than `breakglass` in that log line is an incident: the client restriction
    is procedural.
- **Directory row:** break-glass needs an active `admin_users` row (role `admin`, `password_hash` NULL), because
  the CIS API admits no WORKFORCE token without one.
- **Runbook** (single-line commands, MFA admin profile; record every use in the session log):
  1. Enable:
     `aws cognito-idp admin-enable-user --user-pool-id us-west-1_bCcFvbSOS --username admin@adventure.asia --profile aa365-admin --region us-west-1`
  2. Read the secret in the Secrets Manager console. This sends an alert e-mail by design. Add `totp_seed`
     to an authenticator if it is not there yet.
  3. Open `https://aa-cis.lumiguides.it.com/api/auth/signin/cognito-breakglass` and sign in with password +
     TOTP. The token alarm fires. The refresh window is 1 h.
  4. When done, log out, then:
     `aws cognito-idp admin-user-global-sign-out --user-pool-id us-west-1_bCcFvbSOS --username admin@adventure.asia --profile aa365-admin --region us-west-1`
     and
     `aws cognito-idp admin-disable-user --user-pool-id us-west-1_bCcFvbSOS --username admin@adventure.asia --profile aa365-admin --region us-west-1`
  5. API-only check without the UI: `workforce_bootstrap.py breakglass-verify` (enable → sign in → revoke →
     disable; fails closed if cleanup fails). Rotation: `breakglass-init`.

### A5. Managed login on our own domain, branded, now (not "later")

Brings decision 10's custom domain forward and replaces decision 12's "branding stays out of Terraform".

- **Why now:** Chrome Safe Browsing flagged `lumiguides.it.com` as deceptive once staff sign-in redirected to the
  unbranded prefix domain `aa365-staff-auth-dev.auth.us-west-1.amazoncognito.com`.
- **Domain:** WORKFORCE managed login is served on **`https://staff-auth.lumiguides.it.com`**. The BFF uses it
  for `/oauth2/authorize`, `/oauth2/token`, `/oauth2/revoke` and `/logout`.
  - It is a code constant with the env override `COGNITO_WORKFORCE_DOMAIN`. Setting that override back to the
    prefix domain is the zero-deploy rollback, since a pool keeps both domains.
  - The issuer is unchanged: it is the pool endpoint, not the domain.
- **Apex:** Cognito needs an A record on the parent name. The apex `lumiguides.it.com` is now an A record to
  Vercel (`76.76.21.21`), claimed by the `aa-cis-frontend` project, which redirects it to
  `aa-cis.lumiguides.it.com`.
- **DNS:** the custom-domain records are Route 53 alias records (`dns.tf`, `identity.tf`), not Namecheap.
- **EXTERNAL:** `auth.lumiguides.it.com` exists too, but EXTERNAL keeps the prefix URL until it has its own style.
- **Branding:** `aws_cognito_managed_login_branding` for the three WORKFORCE clients, now that Infra runs AWS
  provider 6.x (#193).
  - Light mode, Adventure Asia logo and colours.
  - The page shows no "adventure.asia" text: a brand domain shown on a different domain is an impersonation
    signal.
  - The page footer is off: Cognito's 1:1–4:1 logo ratio rule rules out a readable text strip.
- **Long term:** the brand/domain mismatch goes away only with a sign-in host under `adventure.asia`. That is a
  business decision.

### A6. The legacy flag is split (D3): CIS UI only, Booking keeps its paths until Phase 2

Narrows the Phase 1 cutover text ("password login is switched off by a config flag").

- **Values:** `LEGACY_ADMIN_LOGIN_ENABLED` defaults to on. Only `0`, `false`, `no` or `off` (case and spaces
  ignored) switch it off; unset, empty or a typo keeps legacy on. The API and the BFF parse it the same way.
- **What it gates:**
  - the CIS UI password form and the BFF `/api/auth/login` route (404 when off);
  - the HS256 path of `/auth/verify-admin`.
- **What it does not gate:** `/auth/admin-login` and `/auth/booking-token`. Booking signs in through them until
  Phase 2, and `/auth/booking-token` accepts only an HS256 CIS session.
- **Preview:** keeps password login. Preview hosts cannot be registered callbacks, and the sign-in route refuses
  any host outside its allow-list. So the BFF flag stays on for Preview.
- **Open for the cutover (Stage S):** the API is one service for Production and Preview, so turning its flag off
  would also end Preview password logins. Nghiệp decides at cutover between "API flag stays on, only the
  Production BFF switches off" and "previews lose admin login".
- **Superseded in part by A12 (S247):** the values above (default on) and the open cutover item. Since S2 the flag
  is off by default in the API and the BFF, and Preview signs in through Cognito (A11), not with a password.

### A7. Gap: WORKFORCE access tokens carry `email` but no `email_verified`

Qualifies decisions 6 and 8 rule 7.

- **What exists:** the WORKFORCE pre token trigger adds only `email` to the access token. It refuses to issue
  any token unless `email_verified` is true and the address is `@adventure.asia`.
- **What CIS does:** the first sign-in binds the directory row by that email, once
  (`WHERE lower(email) = … AND cognito_iss IS NULL AND cognito_sub IS NULL AND is_active`). It refuses only when
  the claim is present and false. The verifier's `Principal.email_verified` is therefore `None` for WORKFORCE
  tokens.
- **Rebinding:** a row bound to another `sub` is never rebound automatically. Rebinding is an owner action.
- **Follow-up:** make the trigger emit `email_verified` as a JSON boolean, then require it to be true at first
  link.

### A8. Residual risk: `AdminCreateUser` can still mint a staff login without a mailbox

Corrects the "Remaining open risks" line, which said a CIS-created staff user is "not usable without that
mailbox or Google account". That is too strong.

- **The gap:** IAM has no condition key for `MessageAction` or `TemporaryPassword`, and `PASSWORD` is a
  pool-wide first factor (break-glass needs it). So a compromised CIS task role could:
  - create a user with its own temporary password, add staff groups and sign in through
    `NEW_PASSWORD_REQUIRED`; or
  - use `MessageAction=RESEND` to set a new temporary password on a user still in `FORCE_CHANGE_PASSWORD`.
- **Mitigation (detective):**
  - The reconcile job flags Cognito users missing from the directory.
  - It reports every user not in `CONFIRMED`: `FORCE_CHANGE_PASSWORD` is listed as pending first sign-in,
    other statuses count as drift.
  - Directory-created users are `CONFIRMED` from the start (A3), so a non-confirmed staff user is a signal.
- **Not built:** an EventBridge alarm on `AdminCreateUser` with a password or `RESEND`. Add it before Booking
  honours `booking-admin` or before production.

### A9. CIS API verification rules for staff tokens (decision 8 applied)

- **Token selection:** the issuer is chosen by the unverified `iss`, and only the WORKFORCE issuer is accepted
  on staff routes. Then: RS256 only, `client_id` ∈ {`cis-admin`, `breakglass`}, `token_use = access`, no `aud`
  check, leeway ≤ 60 s.
- **JWKS:** one cache per issuer, prefetched at start-up. On an unknown `kid` it refetches at most once a
  minute, and it keeps the last good key set.
- **Role:** the CIS role is the highest `cis-*` group (`admin > reviewer > content`). No `cis-*` group → 403,
  even with `booking-*` groups, because the trigger is not client-aware.
  - The group decides. A different DB role is logged as `staff_role_drift` and reported by the reconcile job,
    not denied: denying would be a lock-out path.
- **Staff Bearer middleware:** on every staff path, a verified Cognito Bearer overwrites `x-admin-role` and
  `x-admin-user-id` from the verified principal and drops the client's copies. This ends header trust for
  Bearer requests.
  - `X-Admin-Secret` is still required until the cutover step that makes the secret check principal-aware
    (plan C9).
  - Header trust remains for secret-only and legacy requests until then.
- **BFF:** authorization code + PKCE with a confidential client. Cookies:
  - `cis_admin_token` holds the 15-minute Cognito access token. The cookie lives for the refresh window, so
    middleware can refresh.
  - `cis_staff_rt` holds the refresh token: httpOnly, `path=/api/auth`, 12 h, or 1 h for break-glass.
  - There is one refresh route, single-flight.
- **Staff sign-in method:** email one-time code only. The WORKFORCE Google IdP and the decision 4/5 Google
  linking rules do not apply to staff (S236 decision, unchanged).

### A10. Temporary exception: the E2E test mailbox as one staff address (19/10/2026, S243)

- **Decision (Nghiệp, option B):** the Cognito email-code E2E test (AA-816 E1, AA-CIS-App `e2e-cognito.yml`) signs
  in as a staff user whose address is the SES inbound test mailbox itself, `e2e@e2e-mail.lumiguides.it.com`
  (AA-CIS-Infra `e2e_mailbox.tf`). Option A, a company address forwarded to that mailbox, needed a manual
  change in the adventure.asia mail host. It was the only staff address outside `@adventure.asia` until A10a added the Booking E2E address. It is
  **temporary**: it is removed when the E2E work is finished.
- **Guards:**
  - **One exact address,** with no pattern and no other local part or sub-domain. It is a code constant in each
    place, never configuration: CIS migration 250 (`admin_users_email_chk`), CIS
    `staff_directory.E2E_TEST_STAFF_EMAIL`, and the WORKFORCE pre sign-up and pre token triggers.
  - **Reviewer only.** The DB CHECK accepts the address only with `role = 'reviewer'`, not an owner and with no
    password. The directory refuses any other CIS role. The pre token trigger denies the token unless the
    staff groups are exactly `cis-reviewer`.
  - **No Booking access.** The directory refuses a Booking grant for the address, and the pre token trigger
    denies any `booking-*` group on it.
  - **Short-lived codes at rest.** Mailbox objects expire after 1 day.
  - **Narrow reader.** The reader role `aa-cis-dev-e2e-mail-reader` is read-only (List + Get). Its trust is the
    AA-CIS-App repo, the `e2e` environment and `refs/heads/main` only.
  - **Created like any staff member:** through the staff directory (`create_staff`, audited
    `staff.created`), without an invitation. The Staff page still accepts `@adventure.asia` only.
  - **Domain dependency.** Whoever receives mail for `e2e-mail.lumiguides.it.com` can receive the sign-in
    codes. This access therefore depends on keeping the `lumiguides.it.com` registration and its Route 53 zone
    and MX record. Losing control of any of them (lapsed registration, zone or MX change) triggers the removal
    below at once. The SES receipt rule requires TLS.
  - **Tracked removal.** The removal is an open item under AA-816 in `docs/backlog/README.md` until it is done.
- **Removal (when the E2E work is finished):**
  1. Disable the user (directory disable + global sign-out).
  2. Delete the `shared.admin_users` row (DRY RUN procedure) and the Cognito user (console; the writer may
     not call `AdminDeleteUser`).
  3. Add a new CIS migration that restores the 247 CHECK. It RAISEs while a row still uses the address.
  4. Remove `E2E_TEST_STAFF_EMAIL` and the scope checks from CIS. Remove the trigger exception from Infra and
     run Terraform Apply.
  5. Point the E2E test at a company address, or retire it.
  6. Add a closing line here.
  The A10a Booking address goes in the same cleanup (see A10a "Removal").

#### A10a. Second E2E address: the Booking staff admin (24/10/2026, S250, AA-910)

- **Decision (Nghiệp, S250):** agents, and later CI, need a signed-in check of the Booking staff admin. A second
  dedicated E2E staff identity, `e2e-booking@e2e-mail.lumiguides.it.com`, may sign in with the staff groups exactly
  `booking-admin`. It is the least-privileged Booking group that reads every staff page, `/staff` and `/audit-log`
  included (AA-Booking `backend/app/auth/staff.py`). Temporary, like A10.
- **How the trigger holds it:** the WORKFORCE pre sign-up and pre token triggers now keep a fixed, read-only
  allow-map `{address: exact group tuple}` (`workforce.E2E_TEST_STAFF`, a code constant, never configuration):
  the A10 address with `cis-reviewer`, this address with `booking-admin`. Exact match after lower-casing; any
  other group set on either address denies the token (logged `workforce_pre_token_denied`), it is never
  stripped. The A10 address behaves as before.
- **No CIS access.** The address is not in the CIS staff directory: migration 250's CHECK accepts only the A10
  address, so the directory cannot hold a row for it. CIS refuses its tokens with 403 `no_cis_group` (it has no
  `cis-*` group) before any row lookup. No CIS change.
- **Created outside the directory, without a password.** An admin creates it once with `AdminCreateUser`,
  `MessageAction=SUPPRESS`, `email_verified=true`, and adds it to `booking-admin`. It never gets a password (the
  identity.tf rule "nobody but break-glass holds a usable password" and the A8 alarm apply); it signs in with an
  email code read from the SES mailbox, like the A10 user. So there is no Secrets Manager secret for it. The CIS
  reconcile job reports it under `cognito_without_row` (expected, not in the directory).
- **Mailbox:** the SES receipt rule `e2e-cognito` lists the address. Its codes share the `inbound/` prefix, so
  the existing reader role can read them too (accepted for Dev). An AA-Booking CI job needs its own `sub` added to
  the reader role's trust (AA-Booking repo, environment `e2e`, `refs/heads/main`) in the PR that adds the job.
- **Booking side:** the first sign-in provisions a `booking.staff_users` row (`cog:<sub>`, role admin, active).
- **Removal (with A10):** `AdminDisableUser` + global sign-out, delete the Cognito user (console), drop the map
  entry and the receipt-rule recipient (AA-CIS-Infra), Terraform Apply, deactivate the Booking staff row.

### A11. Preview staff sign-in on one fixed host, capped at viewer (22/10/2026, S247; AA-911 D-1, AA-816 P6a)

Settles the Preview half of the A6 open item: previews get a Cognito sign-in instead of keeping the password form.

- **Host and client:** `aa-cis-preview.lumiguides.it.com` (a Vercel domain of `aa-cis-frontend`) is the only
  callback and sign-out URL of a Preview-only WORKFORCE client `cis-admin-preview` (AA-CIS-Infra). The production
  `cis-admin` client does not list it; break-glass stays production-only. Per-deployment `*.vercel.app` previews
  have no staff sign-in (Cognito allows no wildcard callbacks).
- **Which build uses which client:** a Vercel production build signs in with `cis-admin` on the production host
  only; a preview build with `cis-admin-preview` on the fixed host only, with its own Preview-only client secret.
  A preview build never reads the production client secret.
- **Cap:** the CIS API maps every `cis-admin-preview` token to role `viewer`, `is_owner` false, whatever its
  `cis-*` groups. Writes and admin-only reads are refused. The cap also relies on the Vercel Preview
  `ADMIN_SECRET` being the viewer-capped Preview credential (AA-816 C9).
- **Opt-in alias:** the Vercel Deploy workflow points the fixed host at a preview only on the PR label
  `preview-signin` or a dispatch from `main`.
- **Smoke split:** per-PR previews run only unauthenticated UI smoke; the signed-in smoke runs as the Cognito E2E
  user (A10 mailbox) on Production after each production deploy and, on dispatch, on the fixed Preview host
  (setup fails unless the role is `viewer`).
- **Not changed:** the CIS → Booking token bridge (`/auth/booking-token`) still mints only from an HS256 password
  session, so no Cognito session (the Preview one included) gets a Booking token. Its retirement is AA-911 P6b at
  the end of the project.

### A12. The legacy flag is off by default (cutover S2, 22/10/2026, S247; AA-816)

Supersedes the A6 values and closes its open cutover item.

- **Values:** `LEGACY_ADMIN_LOGIN_ENABLED` is off unless set to `1`, `true`, `yes` or `on` (case and spaces
  ignored). Unset, empty or a typo = off (fail closed). The API (`api/core/staff_identity.py`) and the BFF
  (`frontend/lib/staffSession.ts`) parse it the same way; a test keeps the two lists equal.
- **Where it is turned on:** nowhere. Vercel Production holds an explicit `false` (since S1) and the api task
  definition does not set it, so the code default (off) decides everywhere: the HS256 path of `/auth/verify-admin` answers 401 "Password
  sessions are switched off; sign in again", and the BFF password form and `/api/auth/login` (404) are off on every
  host.
- **Why a code default and not a Terraform env value:** a `false` only in the task definition would leave every
  other runtime (tests, a new task definition) on the old default. One reviewed code change fails closed.
- **Still not gated (unchanged from A6):** `/auth/admin-login` and `/auth/booking-token`. AA-Booking's legacy staff
  path (CIS password → booking-token) keeps working until AA-911 P6b; Booking's own Cognito sign-in
  (`booking-staff` client) is the primary way in.
- **Rollback:** revert the S2 commit (CIS #922) and deploy, or set the flag to `true` on the api task definition
  (AA-CIS-Infra) and on the Vercel target, then redeploy both. Runbook: `docs/ops/runbooks/legacy-login-flag.md`.
- **Accounts:** the legacy full-admin test accounts (`e2e-claude-code`, `e2e-claude-code-2`) are disabled; staff
  and agents sign in with Cognito only (agents through the E2E mailbox, A10).

## Phase 1 status (18/10/2026)

| Item | State |
|---|---|
| Phase 0 done-when (pools, email-code sign-in, no-group refusal, sign-up refusal, break-glass + alarm) | Done (`aa854-evidence.md`) |
| CIS 247, verifier, verify-admin + middleware, Cognito sign-in in the CIS admin, directory writes, reconcile job | Live on Dev |
| CIS task role grant, break-glass secret alert + policy, staff-auth custom domain + branding | Applied |
| Staff invitation email for directory-created users | In progress (follow-up) |
| Daily reconcile trigger (ops-probe Lambda path) | Follow-up (Infra one line) |
| Cutover (Stage S): every active row with an email + its own `cognito_sub`, managed-login break-glass test, principal-aware secret check (C9), `ADMIN_SECRET` rotation, flag off per A6, E2E mailbox (D2) | S1 done 19/10 (Production BFF flag off); S2 done 22/10 (flag off by default, A12). Update S248 |
| Booking Phase 2 (verifier copy, `booking-staff` sign-in, bridge retirement) | Not started |

## Consequences

- **Positive:**
  - CIS staff sign in with an email code on an Adventure Asia branded page on our own domain, with no shared
    password.
  - Offboarding is one owner action: disable, then global sign-out. The worst case is one live 15-minute
    access token.
  - Booking roles have a home in the directory before Booking reads them, and adding another app is a CHECK
    change, not a new column.
  - Break-glass is disabled at rest. Its secret is readable only by the MFA admin role, and every read, write or
    token issue alerts.
  - Roll-back stays cheap: the legacy flag, the prefix domain override, and the DB-first directory with retry.
- **Negative:**
  - Header trust and the shared admin secret remain until the cutover (C9 + rotation).
  - Two login paths coexist for the legacy-flag window (30 days after cutover, decision unchanged).
  - The reconcile job is a detective control only, and A8 remains a real gap until an alarm exists.
  - Break-glass depends on one IAM role name, so renaming that role makes the secret unreadable until the policy
    changes.
  - The apex domain now depends on a Vercel project claim. An unclaimed apex A record to Vercel would be a
    takeover risk.

## Links

- `docs/adr/0006-ecosystem-identity.md` (amended ADR).
- `docs/audits/2026-10-18-S242-cognito-phase1/plan.md`, `aa854-evidence.md`, `reader-maps.md`.
- `docs/database/schema-ownership.md` (`shared.staff_app_grant` in the CIS row).
- AA-CIS-App: `CONTEXT.md` § "Staff roles and permissions"; `api/core/identity_verifier.py`,
  `api/core/identity_config.py`, `api/core/staff_identity.py`, `api/middleware/staff_bearer.py`,
  `api/services/staff_directory.py`, `services/staff_reconcile.py`, `frontend/lib/cognito.ts`,
  `api/migrations/247_admin_users_identity.sql`, `api/migrations/250_admin_users_e2e_test_email.sql` (A10).
- AA-CIS-Infra: `accounts/aa365/identity.tf`, `identity_alerts.tf`, `identity_iam.tf`, `identity_variables.tf`,
  `dns.tf`, `tools/identity/workforce_bootstrap.py`, `e2e_mailbox.tf` and
  `lambda_src/identity_triggers/workforce.py` (A10, A10a), `docs/implementation-notes/AA-910-booking-e2e-staff.md`
  (A10a).
