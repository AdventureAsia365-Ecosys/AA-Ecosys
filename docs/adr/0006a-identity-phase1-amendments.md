# ADR 0006 — Amendment A: identity Phase 1 as shipped (CIS staff on Cognito WORKFORCE)

- **Status:** Accepted (18/10/2026, S242). Records what Phase 1 (CIS staff login + staff directory) shipped on Dev
  and where it departs from the ADR 0006 text. Separate file referenced from `docs/adr/0006-ecosystem-identity.md`.
- **Amends:** ADR 0006 decision 3 (Booking role storage, who may write the directory, directory operations, IAM),
  decision 7 (what "reset" means), decision 10 (custom domain timing, DNS), decision 11 (break-glass address,
  secret shape, guards), decision 12 (branding now in Terraform), the Phase 1 row of the Migration plan (legacy
  flag scope) and the "Remaining open risks" list (the `AdminCreateUser` line). A10 (19/10/2026, S243) adds a
  temporary exception to the `@adventure.asia`-only staff rule for the E2E test account; A10a (24/10/2026, S250)
  adds a second E2E address for the Booking staff admin. A10b (26/10/2026, S252) adds a third, Dev-only E2E address for
  the CIS admin, read-only except the content-quality sentence-apply routes; A10b-1 adds the Content studio invitation
  routes and A10b-2 (05/11/2026, S268) a read-only view-as session, both on synthetic tenants only. A10c (01/11/2026,
  S262) adds a fourth, Dev-only E2E address for the AA-Partner staff console (crm-ops + crm-support, synthetic agencies only).
  A10d (05/11/2026, S270) adds a fifth, Dev-only E2E address for a CIS customer_success member, read-only with no write
  allow-list, synthetic tenants only in its book. A10b-3 (12/11/2026, S278) lets the A10b admin release a held piece of
  a synthetic tenant, and A10e (12/11/2026, S278) adds three Dev-only write-capable AA-Booking E2E addresses (supplier
  ops; a finance maker / checker pair), each held to its own writes on synthetic agencies. A11 and A12 (22/10/2026,
  S247, recorded S248) add the Preview staff sign-in and switch the legacy flag off by default (cutover S2). A13
  (06/11/2026, S271) retires the CIS -> Booking bridge once the staff frontends run on ECS (ADR 0019 d23).
- **Implements:** ADR 0006 Phase 1 for CIS. Booking (Phase 2) was unchanged and still pending on 18/10/2026.
- **Update 2026-10-28:** Booking Phase 2 has shipped in part: Booking verifies WORKFORCE tokens of the
  `booking-staff` and `breakglass` clients and takes roles from the `booking-*` groups; the CIS bridge stays until
  AA-911 P6b (A12). The A8 alarm is built (AA-CIS-Infra `identity_alerts.tf`, section 4). The staff invitation
  email is built (`staff_invite_email` job). The daily reconcile is scheduled by the ops-probe Lambda
  (`/admin/job-runner/staff-reconcile/schedule`).
- **Plan and evidence:** `docs/audits/2026-10-18-S242-cognito-phase1/plan.md` (judged plan, stages A/B/S/D),
  `docs/audits/2026-10-18-S242-cognito-phase1/aa854-evidence.md` (Phase 0 done-when evidence).
  Implementation notes: AA-CIS-App `docs/implementation-notes/AA-816*.md`; AA-CIS-Infra
  `docs/implementation-notes/AA-854.md`, `AA-816.md`, `AA-816-staff-auth-domain.md`.
- **Related Linear:** AA-703 (epic), AA-854 (Phase 0 finish + Phase 1 prerequisites), AA-816 (staff directory).

## Context

Phase 0 finished on 18/10/2026: WORKFORCE pool `aa-workforce-dev`, a staff user signs in
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

- **Address `admin@adventure.asia`** (tech lead, S241), not `breakglass@…`. The tech lead's own staff account is a
  separate personal `@adventure.asia` address.
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
  `nghiep-admin-12h` (by `aws:PrincipalArn`). Since AA-1004 (S273) that role is managed in Terraform (AA-CIS-Infra
  `accounts/aa365/admin_role.tf`); it replaced the hand-made `nghiep-admin-8h-session`. `DescribeSecret` and `GetResourcePolicy` are not denied,
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
- **Runbook** (single-line commands, MFA admin profile; record every use in the session log). `<workforce-pool-id>`
  is the id of the pool `aa-workforce-dev`, from the Terraform output of `identity.tf` or from
  `aws cognito-idp list-user-pools --max-results 20 --profile aa365-admin --region us-west-1 --query "UserPools[?Name=='aa-workforce-dev'].Id" --output text`:
  1. Enable:
     `aws cognito-idp admin-enable-user --user-pool-id <workforce-pool-id> --username admin@adventure.asia --profile aa365-admin --region us-west-1`
  2. Read the secret in the Secrets Manager console. This sends an alert e-mail by design. Add `totp_seed`
     to an authenticator if it is not there yet.
  3. Open `https://aa-cis.lumiguides.it.com/api/auth/signin/cognito-breakglass` and sign in with password +
     TOTP. The token alarm fires. The refresh window is 1 h.
  4. When done, log out, then:
     `aws cognito-idp admin-user-global-sign-out --user-pool-id <workforce-pool-id> --username admin@adventure.asia --profile aa365-admin --region us-west-1`
     and
     `aws cognito-idp admin-disable-user --user-pool-id <workforce-pool-id> --username admin@adventure.asia --profile aa365-admin --region us-west-1`
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
  `aa-cis.lumiguides.it.com`. *Update 07/11/2026 (S272, AA-911):* the apex is now an alias A record to the shared ALB,
  whose :443 listener redirects it to `aa-cis.` (AA-CIS-Infra `dns.tf`, `alb_rules.tf`); the Vercel claim is gone with
  the project (A13).
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
  would also end Preview password logins. The tech lead decides at cutover between "API flag stays on, only the
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

- **Decision (tech lead, option B):** the Cognito email-code E2E test (AA-816 E1, AA-CIS-App `e2e-cognito.yml`) signs
  in as a staff user whose address is the SES inbound test mailbox itself, `e2e@e2e-mail.lumiguides.it.com`
  (AA-CIS-Infra `e2e_mailbox.tf`). Option A, a company address forwarded to that mailbox, needed a manual
  change in the adventure.asia mail host. It was the only staff address outside `@adventure.asia` until A10a added the Booking E2E address. It is
  **temporary**: it is removed when the E2E work is finished.
- **Guards:**
  - **One exact address per allow-map entry** (this one; A10a adds the second), with no pattern and no other local
    part or sub-domain. It is a code constant in each place, never configuration: CIS migration 250 (`admin_users_email_chk`), CIS
    `staff_directory.E2E_TEST_STAFF_EMAIL`, and the WORKFORCE pre sign-up and pre token triggers.
  - **Content only** (reviewer until 05/11/2026). The DB CHECK accepts the address only with `role = 'content'`, not
    an owner and with no password. The directory refuses any other CIS role. The pre token trigger denies the token
    unless the staff groups are exactly `cis-content`. *Update S269 (AA-1035 R2 close-out, root ADR 0019 d3):* the
    `reviewer` role merged into `content` (CIS 363) and its alias is gone (CIS 375 moves this row to `content` and
    forbids `reviewer`; the CIS API maps no role to `cis-reviewer`; AA-CIS-Infra drops the `cis-reviewer` group and the
    trigger's map entry becomes `cis-content`). The exception is otherwise unchanged: same address, same mailbox, no
    Booking access, still temporary.
  - **No Booking access.** The directory refuses a Booking grant for the address, and the pre token trigger
    denies any `booking-*` group on it.
  - **Short-lived codes at rest.** Mailbox objects expire after 1 day.
  - **Narrow reader.** The reader role `aa-cis-dev-e2e-mail-reader` is read-only (List + Get). Its trust is the
    `e2e` environment and `refs/heads/main` of two repos: AA-CIS-App and, since AA-936, AA-Partner (its synthetic
    agency users' codes). The bucket policy also lets the MFA admin role read the objects.
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
  3. Add a new CIS migration that restores the 247 CHECK. It RAISEs while a row still uses either E2E address
     (A10 `e2e@`, A10b `e2e-cis-admin@`, A10d `e2e-cis-cs@`; migration 283's header holds the SQL).
  4. Remove `E2E_TEST_STAFF_EMAIL` and the scope checks from CIS. Remove the trigger exception from Infra and
     run Terraform Apply.
  5. Point the E2E test at a company address, or retire it.
  6. Add a closing line here.
  The A10a Booking address, the A10b CIS admin address, the A10c CRM staff address and the A10d customer success
  address go in the same cleanup (see each one's "Removal").

#### A10a. Second E2E address: the Booking staff admin (24/10/2026, S250, AA-910)

- **Decision (tech lead, S250):** agents, and later CI, need a signed-in check of the Booking staff admin. A second
  dedicated E2E staff identity, `e2e-booking@e2e-mail.lumiguides.it.com`, may sign in with the staff groups exactly
  `booking-admin`. It is the least-privileged Booking group that reads every staff page, `/staff` and `/audit-log`
  included (AA-Booking `backend/app/auth/staff.py`). Temporary, like A10.
- **How the trigger holds it:** the WORKFORCE pre sign-up and pre token triggers now keep a fixed, read-only
  allow-map `{address: exact group tuple}` (`workforce.E2E_TEST_STAFF`, a code constant, never configuration):
  the A10 address with `cis-reviewer` (`cis-content` since S269, see A10), this address with `booking-admin`. Exact match after lower-casing, and only
  when the raw email attribute is ASCII: `str.lower()` folds some non-ASCII letters to ASCII (U+212A KELVIN SIGN
  becomes `k`), so a look-alike user would otherwise pass as this one. Any other group set on either address denies
  the token (logged `workforce_pre_token_denied`), it is never stripped. The A10 address behaves as before.
- **Exposure.** `booking-admin` is Booking's full write admin, not a read role: `staff.admin`, `retention.admin`
  (DRY RUN and live delete / redaction of Booking rows), `b2b.admin` (which agencies may call `booking.b2b.v1`),
  `customer.admin` and every write. Whoever can read a sign-in code can get that role on the production client
  `booking-staff`. Code readers: the mailbox reader role (AA-CIS-App and AA-Partner, environment `e2e`, `main`), the
  MFA admin role, and anyone who controls mail for `e2e-mail.lumiguides.it.com`. A10's **domain dependency**
  applies to this address too: losing the registration, the zone or the MX triggers the removal of both
  addresses at once.
- **Read-only session, enforced by Booking.** Because of that exposure, AA-Booking refuses every request other than
  GET / HEAD / OPTIONS from this user with 403 `e2e_read_only`, on every client, before any DB access
  (`backend/app/auth/staff.py` `E2E_TEST_STAFF_EMAIL`, next to the A11 `preview_read_only` cap). Reads keep the admin
  permissions, so the smoke can open `/staff` and `/audit-log`. What stays exposed is the admin reads of Dev Booking
  data (synthetic, no real customers in Dev).
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
- **Booking side:** the first sign-in provisions a `booking.staff_users` row (`cog:<sub>`, role admin, active). It
  shows on `/staff` and in the StaffPicker, so real staff could assign trip cases to it; deactivate it between runs if
  that happens.
- **Removal (with A10):** `AdminDisableUser` + global sign-out, delete the Cognito user (console), drop the map
  entry and the receipt-rule recipient (AA-CIS-Infra), Terraform Apply, deactivate the Booking staff row, and
  remove `E2E_TEST_STAFF_EMAIL` and its write cap from AA-Booking `app/auth/staff.py`.

#### A10b. Third E2E address: the CIS admin, Dev only, read-only (26/10/2026, S252, AA-816)

- **Decision (S252, orchestrator under the tech lead's standing approval; design reviewed in the S252 session):** the orchestrating agent must sign itself in to the CIS
  admin as an **admin** to screenshot the admin-only pages (`/admin/content-quality`, `/admin/writing-memory`) and to
  produce the AA-916 WM-07 sample (admin sentence actions through the UI, on synthetic Dev tenants). The A10 account is
  a reviewer only (content since S269). A third dedicated WORKFORCE E2E identity, `e2e-cis-admin@e2e-mail.lumiguides.it.com`, signs in with
  the staff groups exactly `cis-admin`, on Dev only. The name carries the app (`e2e-cis-admin@`, not `e2e-admin@`), so
  nothing that greps for `admin@` (the break-glass address `admin@adventure.asia`, username `admin`) confuses them.
  Temporary, like A10.
- **Groups (trigger):** a second read-only map in the WORKFORCE triggers, `workforce.E2E_DEV_ONLY_TEST_STAFF =
  {e2e-cis-admin@: ("cis-admin",)}`, a code constant consulted only while the Lambda env
  `E2E_DEV_ONLY_STAFF_ENABLED` is exactly `"true"` (read per call; missing or anything else is off). The flag can
  only switch the entry on; it cannot add an address or widen the group set. Any other group set (another `cis-*`,
  any `booking-*` or `crm-*`) denies the token, never stripped. Same ASCII-only exact lookup as A10a. `e2e@` and
  `e2e-booking@` cannot borrow `cis-admin` (the map is per address).
- **Environment guard (two layers):**
  - Terraform (`identity.tf`): `E2E_DEV_ONLY_STAFF_ENABLED = var.environment == "dev" ? "true" : "false"`, plus a
    `precondition` on the trigger Lambdas that refuses `"true"` outside dev.
  - CIS API: the directory creates, re-enables or syncs the account only where `ENVIRONMENT` is exactly `dev` (403
    `e2e_not_allowed_here`, no `"dev"` default), and `staff_identity.resolve_staff` refuses its token with the same
    403 anywhere else. Disabling it stays allowed everywhere.
- **Directory row:** `shared.admin_users`, `role = 'admin'`, `is_owner = false`, `password_hash IS NULL`, no
  `staff_app_grant`. CIS migration 283 extends `admin_users_email_chk` with exactly that tuple (the A10 clause is
  unchanged). `staff.write` needs `is_owner`, so the account can never change the directory.
- **Read-only cap with one allow-list (CIS):** the identity carries `e2e_read_only`. The staff bearer middleware
  refuses every method other than GET / HEAD / OPTIONS on the staff paths with 403 `e2e_read_only`, before the route
  runs, except POST `/admin/content-quality/pieces/{piece_id}/sentences/apply` and POST
  `/admin/content-quality/tour-versions/{version_id}/sentences/apply` (Cut and manual Edit with a reason chip). Those
  routes accept only `mode` `cut` / `manual` from it; `…/sentences/suggest` (the paid model call), the exemplar
  toggle, labels, place cards and everything else stay refused. `staff_authz` refuses the same writes again by route
  template (defence in depth). Since A10b-1 (AA-979) the allow-list also holds the two Content studio invitation
  routes, synthetic tenants only. `/auth/verify-admin` returns `admin`, so the BFF opens the admin pages.
- **Mailbox isolation (Infra `e2e_mailbox.tf`):** its own SES receipt rule `e2e-cognito-admin` (dev only; recipient
  this address only; TLS Require; spam / virus scan), writing to its own prefix `inbound-admin/`. The address is never
  a recipient of `e2e-cognito`. The SES PutObject statements pair rule ARN and prefix, so neither rule writes into the
  other's prefix. A bucket-policy Deny (`DenyAdminPrefixReadsExceptMfaAdmin`) refuses object reads under
  `inbound-admin/*` to every principal except the MFA admin role, the CI reader role included whatever its identity
  policy says; that policy stays scoped to `inbound/*` (which does not match `inbound-admin/…`). 1-day expiry like the
  rest of the bucket.
- **Exposure.** Code readers: the MFA admin role (already full AWS admin) and whoever controls mail for
  `e2e-mail.lumiguides.it.com` (A10's domain dependency applies: losing it removes all three addresses at once). What a
  code yields: CIS admin **reads** on Dev (tenant text in writing memory, the staff directory's emails and display
  names, the audit log, spend and AI settings, CRM ops reads) plus sentence Cut / Edit on synthetic Dev tenants. The CI
  apply role can still rewrite the bucket policy (true for every statement; PR review and the plan guard cover it).
  Since S255 (AA-898) a code also yields read access to the owner-only pages of `/admin/docs` on Dev, through the
  `docs.owner_read` permission (AA-CIS-App `staff_authz.docs_owner_read_via` returns `"e2e_dev"`); `is_owner` stays
  false and no owner write opens.
- **Cross-app:** no `booking-*` group, so Booking answers `no_booking_role`; the CIS to Booking bridge mints only from
  password sessions (A11), so no Booking token. AA-Partner `/crm/ops/v1` gives `cis-admin` reads only (writes need
  `crm-platform-admin`, which the trigger never allows on this address); a Preview-host session is the viewer (A11).
- **Created through the directory:** an S3-mediated ECS exec script on the CIS API calls `staff_directory.create_staff`
  with `role="admin"`, `booking_role=None`, `send_invite=False`, the active owner row as the audited actor
  (`staff.created`). Not Terraform (the directory is the only writer of WORKFORCE users, ADR 0006 §3), not
  `workforce_bootstrap.py` (company addresses only, no row). `AdminCreateUser` is SUPPRESS with no password, so the A8
  alarm does not fire.
- **Reconcile:** before the first sign-in the user is listed under `pending_first_sign_in` (not counted); after it,
  nowhere. Group or grant drift on the row is reported as `group_drift`.
- **Detection:** `workforce_e2e_test_token_issued` (with `email`), `staff_bearer_verified` (`e2e_read_only`),
  `staff_identity_e2e_read_only`, `staff_bearer_refused reason=e2e_read_only`.
- **Used only by the agent, locally:** AA-CIS-App Playwright project `admin-evidence` (`E2EADMIN=1`, no workflow sets
  it), run by the orchestrator with the MFA admin role (`AWS_PROFILE=aa365-admin`). Never CI: no CI role can read the
  prefix.
- **Removal (end of project code, with A10 / A10a):** directory disable + global sign-out; delete the row (DRY RUN
  procedure) and the Cognito user (console); the restore-247 migration (A10 step 3); drop the CIS constants
  (`api/core/e2e_staff.py`), the environment guard, the read-only cap and the allow-list; drop the trigger map and flag,
  the `E2E_DEV_ONLY_STAFF_ENABLED` env and precondition, the receipt rule `e2e-cognito-admin` and the two bucket
  statements; Terraform Apply; a closing line here. Also drop the `docs.owner_read` E2E branch (AA-CIS-App
  `staff_authz.docs_owner_read_via` `"e2e_dev"`, AA-898): owner-only `/admin/docs` pages are then read by verified
  Cognito owners only.

##### A10b-1. Amendment: Content studio invitations on synthetic tenants (26/10/2026, S252, AA-979)

- **Decision (tech lead, S252, option (a)):** the A10b identity may call exactly two more write routes, the Content
  studio invitation routes of Tenant 360, so the AA-979 phase 2 re-enrolment E2E (AA-Partner `e2e/phase2/`, mode
  `a10b`) runs without a person:
  - POST `/admin/tenants/{tenant_id}/members/invitations` (create an `invited` membership, relay the mail once to
    the CRM);
  - POST `/admin/tenants/{tenant_id}/members/{membership_id}/invitation/send` (send the same invitation again).
  Option (b), keeping A10b read-only and having the tech lead send each invitation from their own staff session, was not
  chosen: every phase 2 run and every 7-day clean-up run would wait for a person.
- **Scope, enforced by CIS (AA-CIS-App `api/core/e2e_staff.py`, `api/routers/admin_tenant360.py`):**
  - **Two routes only.** They join `E2E_ALLOWED_WRITES` (route templates, `staff_authz`) and
    `E2E_ALLOWED_WRITE_PATHS` (concrete paths, UUIDs, full match, bearer middleware). Every other write, including
    every other Tenant 360 write (member role change, member removal, tenant status, plan, key, config, offboard),
    still gets 403 `e2e_read_only` before the route runs.
  - **Synthetic tenants only.** On both routes, for the A10b session, CIS reads `shared.tenants.is_canary` (CIS
    migration 058: "TRUE for synthetic canary tenant") and refuses with 403 `e2e_read_only` unless it is exactly
    TRUE. NULL, FALSE or no row count as real. The check runs after the tenant lookup and before any membership row,
    audit row or CRM relay, so a refused call changes nothing and sends no mail.
  - **E2E mailbox addresses only.** The invitee address must be on `e2e-mail.lumiguides.it.com` (exact domain,
    ASCII only, no sub-domain, the A10a look-alike rule). The two dedicated recipients are
    `e2e-test-studio-viewer@` and `e2e-test-studio-editor@` (AA-CIS-Infra `tools/identity/crm_e2e_users.json`
    `studio_invitees`, receipt rule `e2e-cognito`, prefix `inbound/`).
  - **Viewer or editor only.** A new invitation from A10b may grant `viewer` or `editor`, never `owner`. A
    send-again re-seals the existing invitation to the address in the request, so A10b may send again only an
    `invited` membership whose stored role is `viewer` or `editor`: an `owner` invitation a real admin created on a
    synthetic tenant cannot be redirected to an E2E mailbox (403 `e2e_read_only`, before the relay).
  - **Dev only.** Unchanged from A10b: the token exists only where the WORKFORCE flag is on (Terraform: dev), and
    CIS refuses the identity unless `ENVIRONMENT` is exactly `dev` (403 `e2e_not_allowed_here`).
- **Audit, one row per call.** Every A10b write that passes the bearer cap gets the AA-884 `staff.request` row in
  `acp_shared.audit_log` (actor `admin:<the A10b admin_users.id>`, route, status), whether the route allowed or
  refused it. An accepted invitation also writes `tenant.member_invited`. A refusal by the route is logged
  `tenant_member_invitation_e2e_refused` with `reason` (`tenant_not_synthetic`, `address`, `role`; no address). A
  refusal by the bearer cap stays `staff_bearer_refused reason=e2e_read_only` (log only, as before).
- **Cross-app (corrects A10b "Cross-app" for this route).** AA-Partner `crm.ops.v1 POST
  /tenants/{id}/studio-invitations` (AA-979 P2b) accepts any OPS caller, `cis-admin` included, and does not check
  for synthetic tenants. So a leaked A10b code could already call that CRM route directly before this amendment; CIS
  is the gate this amendment adds. A matching CRM check (refuse the A10b address unless the agency or tenant is
  synthetic) is an open follow-up, AA-Partner.
  - *Closing line (26/10/2026, S252, AA-979):* AA-Partner #83 adds that CRM check (for the A10b address only:
    synthetic-only environment, E2E mailbox address, a synthetic CRM agency with that id, and an `invited` viewer or
    editor membership CIS confirms through `tenant.membership.v1` getTenantMembers). Because the CRM marks every Dev
    agency synthetic, the agency term alone is weak on Dev, so `tenant.membership.v1` 1.2 adds
    `TenantMembers.is_synthetic` (from `shared.tenants.is_canary`, NULL = false) and the CRM also requires it to be
    true, in the same call; a CIS answer without the field is refused (fail closed). Real admins are unchanged.
- **Exposure added.** Whoever reads an A10b code can now also send AA system invitation mails to the E2E mailbox
  and claim a partner-pool account as a viewer or editor of a synthetic Dev tenant. No real tenant and no address
  outside the mailbox domain can be reached.
- **Revoke (any time, without waiting for the A10 / A10a / A10b removal):** drop the two routes from
  `E2E_STUDIO_INVITATION_WRITES` and `E2E_ALLOWED_WRITE_PATHS` and the route check (`_refuse_e2e_invitation`) in
  AA-CIS-App, update the guard test `test_the_write_allow_list_is_exactly_the_reviewed_routes`, deploy. Faster stop
  on Dev: disable the A10b user (directory disable + global sign-out) or clear `is_canary` on the synthetic tenants.
  Then drop `studio_invitees` from `crm_e2e_users.json` (AA-CIS-Infra), Terraform Apply, and delete the two
  partner-pool accounts (`crm_dev_identity.py --pool partner invitee-reset --invitee studio-viewer|studio-editor
  --apply`). Add a closing line here. The A10b removal list covers all of this as well.

##### A10b-2. Amendment: a read-only view-as session on synthetic tenants (05/11/2026, S268, AA-1035)

- **Decision (S268, orchestrator under the tech lead's standing approval and the dev-phase merge rule; root ADR 0019
  d5 "view as tenant"):** the A10b identity may start and end a read-only view-as session on a synthetic Dev tenant,
  so the orchestrator's admin-evidence run (AA-CIS-App Playwright project `admin-evidence`) can show the view-as
  banner, the partner reads and the audit rows without a person. Two more write routes:
  - POST `/admin/tenants/{tenant_id}/view-as` (open a session: reason, optional ticket, at most 60 minutes);
  - POST `/admin/view-as/sessions/{session_id}/end` (end it).
- **Scope, enforced by CIS (AA-CIS-App `api/core/e2e_staff.py` `E2E_VIEW_AS_WRITES`, `api/routers/admin_view_as.py`):**
  - **Two routes only.** They join `E2E_ALLOWED_WRITES` (route templates, `staff_authz`) and
    `E2E_ALLOWED_WRITE_PATHS` (concrete paths, UUIDs, full match, bearer middleware). Every other write still gets 403
    `e2e_read_only` before the route runs.
  - **Synthetic tenants only.** On both routes, for the A10b session, CIS reads `shared.tenants.is_canary` and refuses
    with 403 `e2e_read_only` unless it is exactly TRUE (the A10b-1 rule), before any session row, audit row or token.
  - **Its own sessions only (S268 follow-up).** The A10b identity holds the admin role, but its session list
    (`GET /admin/view-as/sessions`) is scoped to its own sessions, and another member's session is a 404 to it on
    read and end: the evidence run never lists, reads or revokes a real member's view.
  - **Read-only session.** A session opened by A10b is the same read-only view as any other (root ADR 0019 d5): only
    the allow-listed side-effect-free tenant reads, every request logged (`tenant.view_as_request`), the session ends
    with its expiry, its end, the tenant's offboarding or the member's sign-out, each with one
    `tenant.view_as_ended` row.
  - **Dev only.** Unchanged from A10b: the token exists only where the WORKFORCE flag is on (Terraform: dev), and CIS
    refuses the identity unless `ENVIRONMENT` is exactly `dev` (403 `e2e_not_allowed_here`).
- **Audit.** Every A10b write that passes the bearer cap gets the AA-884 `staff.request` row; a start writes
  `tenant.view_as_started`, an end `tenant.view_as_ended`, each read with the token `tenant.view_as_request`. A refusal
  by the route is logged `view_as_e2e_refused reason=tenant_not_synthetic`.
- **Exposure added.** Whoever reads an A10b code can read, for at most 60 minutes per session, what the partner's own
  API answers for a synthetic Dev tenant (the allow-listed reads). Synthetic tenants hold invented data only; no real
  tenant can be viewed.
- **Revoke (any time, without waiting for the A10 / A10a / A10b removal):** drop the two routes from
  `E2E_VIEW_AS_WRITES` and the route check (`_refuse_e2e`) in AA-CIS-App, update the guard test of the write
  allow-list, deploy. Faster stop on Dev: disable the A10b user (directory disable, which also ends its open view-as
  sessions) or clear `is_canary` on the synthetic tenants. Add a closing line here. The A10b removal list covers this
  as well.

##### A10b-3. Amendment: release a held piece on synthetic tenants (12/11/2026, S278, AA-1087)

- **Decision (tech lead, S278: build Dev-only write-capable E2E staff identities before the synthetic pilot rehearsal;
  system audit gap B2; designed by the orchestrated lane under the dev-phase merge rule, independent review before
  merge):** the A10b identity may call one more write route, the staff review "approve" of an agency's held content:
  - POST `/admin/tenant-qa/compliance/{flag_id}/release` (resolve an open subject_gate flag as released for the text
    the gate read, so exactly that text may publish).
  The Review Queue approve (`/admin/review-queue/{id}/approve`) is NOT added: it only claims rows of the AA master
  tenant and publishes AA master content, which no E2E identity may change.
- **Scope, enforced by CIS (AA-CIS-App `api/core/e2e_staff.py` `E2E_COMPLIANCE_RELEASE_WRITES`,
  `api/routers/admin_tenant_compliance.py`):** the route joins `E2E_ALLOWED_WRITES` and `E2E_ALLOWED_WRITE_PATHS`;
  for the A10b session the route reads the flag's tenant and refuses with 403 `e2e_read_only` unless it is synthetic
  (`is_canary IS TRUE` and not the pilot, the A10b-1 rule), before the flag is resolved or audited (log
  `compliance_release_e2e_refused reason=tenant_not_synthetic`); A10d and any other Dev-only E2E identity is refused
  outright. Dev only, unchanged from A10b.
- **Audit.** The AA-884 `staff.request` row (actor `admin:<A10b id>`) for every call that passes the bearer cap; an
  accepted release also writes `content_compliance.released`.
- **Exposure added.** Whoever reads an A10b code can let a synthetic Dev tenant's held text publish to that tenant's
  (test) channels. No real tenant, no pilot, no AA master content.
- **Revoke (any time):** drop the route from `E2E_COMPLIANCE_RELEASE_WRITES` and `_refuse_e2e` in AA-CIS-App, update
  the guard test of the write allow-list, deploy; faster on Dev: disable the A10b user or clear `is_canary`. Add a
  closing line here. The A10b removal list covers this as well.

#### A10c. Fourth E2E address: the AA-Partner staff console, Dev only, synthetic agencies only (01/11/2026, S262, AA-1019)

- **Decision (S262, orchestrator under the tech lead's standing approval and the dev-phase merge rule; the AA-1019
  issue asks for "a Dev E2E WORKFORCE user in crm-ops + crm-support, read-limited like the other E2E users"):** the
  orchestrating agent must sign itself in to the AA-Partner staff console (CRM web `/staff`, WORKFORCE `crm-staff`
  client, root ADR 0006b decision 6) to screenshot S-02 / S-04 and to run the live checks of AA-956 / AA-971 (open
  one release and see the agency's view count move; a support read refused after the owner revokes; break-glass mails
  the owner and raises the AA ops alarm). No E2E identity holds `crm-ops` or `crm-support` today. A fourth dedicated
  WORKFORCE identity, `e2e-crm-staff@e2e-mail.lumiguides.it.com`, signs in with the staff groups exactly `crm-ops` +
  `crm-support`, on Dev only. Temporary, like A10.
- **Groups (trigger):** one more entry in the Dev-only map of A10b, `workforce.E2E_DEV_ONLY_TEST_STAFF =
  {e2e-cis-admin@: ("cis-admin",), e2e-crm-staff@: ("crm-ops", "crm-support")}`, behind the same
  `E2E_DEV_ONLY_STAFF_ENABLED` flag (exactly `"true"` on dev only, a Terraform precondition elsewhere). Any other
  group set (one of the two alone, `crm-platform-admin`, any `cis-*` / `booking-*`) denies the token, never stripped.
  Same ASCII-only exact lookup. The other E2E addresses cannot borrow these groups (the map is per address).
- **Synthetic agencies only (AA-Partner, `api/app/auth/e2e_staff.py`):** the CRM recognises the identity by the access
  token's `email` claim (set by the pre token trigger, signed by the pool). The class guard refuses it outside
  `ENVIRONMENT` dev / test / local (403 `e2e_read_only`). Every staff context (`ops_tx`, `staff_tx`, `support_tx`)
  refuses an agency whose `crm.tenant.is_synthetic` is not true (403 `e2e_synthetic_only`), and the S-02 board and
  both agency lists leave such an agency out. On a synthetic agency it works like any `crm-ops` / `crm-support` member:
  it reads S-02, downloads a watermarked manifest, starts a support session inside the owner's grant, opens
  break-glass (the owners of that synthetic agency, E2E mailbox addresses, are mailed; the AA ops alarm fires, which is
  what the live check needs). It can never read, export or open a real agency. Unlike A10b this is not "read-only": the
  staff class has no write besides one's own session rows and the S-02 view / manifest records (AA-971, AA-956), and
  those are exactly what the checks exercise.
- **Mailbox isolation (Infra `e2e_mailbox.tf`):** the address is a second recipient of the A10b rule
  `e2e-cognito-admin` (dev only), so its codes land under `inbound-admin/`, which only the MFA admin role reads; it is
  never a recipient of `e2e-cognito` (the CI-readable `inbound/`).
- **Created outside the CIS directory**, like A10a's Booking address: AA-CIS-Infra
  `tools/identity/crm_dev_identity.py e2e-staff --apply` (AdminCreateUser with SUPPRESS and `email_verified=true`, no
  password, AdminAddUserToGroup for the two groups; refuses a user that holds any other group). The A8 alarm does not
  fire (no password). The CIS reconcile may list it as not in the directory, as it does the A10a user.
- **Exposure.** Code readers: the MFA admin role and whoever controls mail for `e2e-mail.lumiguides.it.com` (A10's
  domain dependency). What a code yields: S-02 and S-04 on synthetic Dev agencies only, including break-glass mails
  to E2E mailbox owners and the AA ops alarm. No CIS, Booking or `/crm/ops/v1` access (no `cis-*` / `booking-*` /
  `crm-platform-admin` group; `/crm/v1` refuses every WORKFORCE token).
- **Detection:** `workforce_e2e_test_token_issued` (with `email`), AA-Partner `route_guard_e2e_crm_staff_refused`
  (outside dev) and `crm_e2e_staff_refused tenant=...` (a real agency), plus every staff action in the synthetic
  agency's own access log (actor kinds `aa_ops`, `support`, `breakglass`).
- **Used only by the agent, locally**, with the MFA admin role reading the code (runbook in AA-CIS-Infra
  `tools/identity/README.md`). Never CI.
- **Removal (end of project code, with A10 / A10a / A10b):** `admin-delete-user` of the address; drop the trigger entry,
  the mailbox recipient, the `e2e-staff` command and the AA-Partner `E2E_CRM_STAFF_EMAIL` rule
  (`Caller.e2e_synthetic_only`); Terraform Apply; a closing line here. Faster stop on Dev: disable the user.

#### A10d. Fifth E2E address: a CIS customer_success member, Dev only, read-only with no write allow-list (05/11/2026, S270, AA-1035)

- **Decision (S270, orchestrator under the tech lead's standing approval and the dev-phase merge rule; AA-1035
  Done-when "Live on Dev: a customer_success E2E user sees only the assigned tenants (403 on another tenant)"):** the
  S267 probe proved the tenant-book scoping only through the header path in the container, without a Cognito session.
  A fifth dedicated WORKFORCE identity, `e2e-cis-cs@e2e-mail.lumiguides.it.com`, signs in with the staff groups
  exactly `cis-customer_success`, on Dev only, so the orchestrator's admin-evidence run proves the scoping end to end
  (AA-CIS-App Playwright `admin-evidence/cs-scope.spec.ts`). Temporary, like A10.
- **Groups (trigger):** one more entry in the Dev-only map of A10b, `workforce.E2E_DEV_ONLY_TEST_STAFF =
  {…, e2e-cis-cs@: ("cis-customer_success",)}`, behind the same `E2E_DEV_ONLY_STAFF_ENABLED` flag (exactly `"true"`
  on dev only, a Terraform precondition elsewhere). Any other group set (another `cis-*`, any `booking-*` or `crm-*`)
  denies the token, never stripped. Same ASCII-only exact lookup; no address can borrow another address's groups (the
  map is per address).
- **Environment guard (two layers), as A10b:** Terraform switches the trigger entry on for dev only; the CIS API creates,
  re-enables or syncs the account only where `ENVIRONMENT` is exactly `dev` and `staff_identity.resolve_staff` refuses
  its token with 403 `e2e_not_allowed_here` anywhere else (AA-CIS-App `api/core/e2e_staff.py`
  `DEV_ONLY_E2E_STAFF_ROLES`). Disabling it stays allowed everywhere.
- **Directory row:** `shared.admin_users`, `role = 'customer_success'`, `is_owner = false`, `password_hash IS NULL`, no
  `staff_app_grant` (no Booking role), no `staff_crm_grant` (no CRM role). CIS migration 378 extends
  `admin_users_email_chk` with exactly that tuple (the A10 and A10b clauses are unchanged); the directory refuses any
  other role, a Booking grant or a CRM role for the address (400 `e2e_test_scope`).
- **Read-only cap with NO write allow-list (CIS):** the identity carries `e2e_read_only` but not
  `e2e_allowlisted_writes`, a second identity flag that only the A10b address carries and that every A10b exception now
  keys on: the bearer middleware allow-list, `staff_authz.denial_reason`, the `docs.owner_read` `"e2e_dev"` branch and
  the route checks of the sentence-apply routes (A10b), the Content studio invitations (A10b-1) and view-as (A10b-2).
  So every method other than GET / HEAD / OPTIONS is refused with 403 `e2e_read_only` before the route runs: no
  sentence apply, no A10b-1 invitation, no A10b-2 view-as, no assignment change, nothing else. The route checks refuse
  it outright as a third layer. `/auth/verify-admin` returns `customer_success`, so the BFF opens the desk pages.
- **Synthetic tenants only in its book:** `PUT /admin/tenants/{id}/assignments/{staff}` answers 409 for a Dev-only E2E
  staff row (A10b or A10d) on a tenant that is not synthetic (`shared.tenants.is_canary IS TRUE` and not the pilot,
  the A10b-1 rule), before any row or audit write. The book therefore never holds a real tenant or the pilot, and the
  identity's reads stay on synthetic data.
- **Mailbox:** a third recipient of the A10b rule `e2e-cognito-admin` (dev only), so its codes land under
  `inbound-admin/`, which only the MFA admin role reads; it is never a recipient of `e2e-cognito` (the CI-readable
  `inbound/`).
- **Exposure.** Code readers: the MFA admin role and whoever controls mail for `e2e-mail.lumiguides.it.com` (A10's
  domain dependency applies: losing it removes every E2E address at once). What a code yields: the customer_success
  **reads** of the synthetic tenants in its book on Dev (Tenant 360, members, the Content quality lists of its book,
  the CRM desk reads CIS scopes). No write anywhere.
- **Cross-app:** no `booking-*` group, so Booking answers `no_booking_role`; the CIS to Booking bridge mints only from
  password sessions (A11). AA-Partner `/crm/ops/v1` accepts `cis-customer_success` as a desk caller whose reads CIS
  scopes (`tenant.membership.v1` staff-scope); the CRM flags this identity `Caller.e2e_no_write` (deliberately not
  `e2e_read_only`, which would open the A10b-1 invitation path), refuses it outside dev / test / local, and refuses the
  studio-invitation relay (its one reachable write) and every `crm-platform-admin` write with 403 `e2e_read_only`.
- **Created through the directory:** an S3-mediated ECS exec script on the CIS API calls `staff_directory.create_staff`
  with `role="customer_success"`, `booking_role=None`, no CRM roles, `send_invite=False`, the active owner row as the
  audited actor (`staff.created`), after the Infra trigger is applied. Then an admin assigns ONE synthetic tenant to it
  (the route above). `AdminCreateUser` is SUPPRESS with no password, so the A8 alarm does not fire.
- **Reconcile:** listed under the known E2E exceptions on Dev (clause `ADR 0006a A10d`), not counted as drift.
- **Detection:** `workforce_e2e_test_token_issued` (with `email`), `staff_identity_e2e_read_only`
  (`allowlisted_writes=false`), `staff_bearer_refused reason=e2e_read_only`, `tenant_assignment_e2e_refused`, AA-Partner
  `route_guard_e2e_cis_cs_refused` and `studio_invitation_e2e_no_write_refused`.
- **Used only by the agent, locally**, with the MFA admin role reading the code (`E2ECS=1`, no workflow sets it). Never
  CI.
- **Removal (end of project code, with A10 / A10a / A10b / A10c):** directory disable + global sign-out; delete the row
  and its assignments (DRY RUN procedure) and the Cognito user (console); the restore-247 migration (A10 step 3, which
  RAISEs while a row still uses an E2E address); drop the CIS constants and the `e2e_allowlisted_writes` split with the
  rest of `api/core/e2e_staff.py`, the assignment guard, the trigger entry, the receipt-rule recipient and the AA-Partner
  `E2E_CIS_CS_EMAIL` rule (`Caller.e2e_no_write`); Terraform Apply; a closing line here. Faster stop on Dev: disable the
  user. The full end-of-project removal list is therefore A10, A10a, A10b (with A10b-1, A10b-2 and A10b-3), A10c, A10d
  and A10e (AA-1054).

#### A10e. Dev-only write-capable AA-Booking E2E addresses (12/11/2026, S278, AA-1087)

- **Decision (tech lead, S278; system audit gap B2; independent review before merge):** the synthetic pilot rehearsal
  must prove the Booking staff steps through the browser, and the A10a Booking E2E user is read-only (every POST is
  403, including dry runs). Three more WORKFORCE identities, Dev only, each with exactly one group:
  `e2e-booking-staff@e2e-mail.lumiguides.it.com` (`booking-sales`), `e2e-booking-maker@…` and
  `e2e-booking-checker@…` (both `booking-finance`). A10a is not widened: its codes sit in the CI-readable `inbound/`.
- **Groups (trigger):** three more entries of the Dev-only map of A10b (`workforce.E2E_DEV_ONLY_TEST_STAFF`), behind
  the same `E2E_DEV_ONLY_STAFF_ENABLED` flag (exactly `"true"` on dev only, a Terraform precondition elsewhere). Any
  other group set denies the token; same ASCII-only exact lookup. The maker and the checker share one tuple on purpose:
  AA-Booking separates them by address.
- **Scope, enforced by AA-Booking (`backend/app/auth/e2e_staff.py`, called from `current_staff`):**
  - **Dev only:** the process `ENVIRONMENT` must be exactly `dev`, else every request of the identity, reads included,
    is 403 `e2e_not_allowed_here` before any DB access.
  - **Exact groups:** else 403 `e2e_scope`.
  - **Its own writes only** (before any DB access, else 403 `e2e_read_only`): staff — POST
    `/booking/supplier-bookings/{id}/request` and `/confirm`; maker — POST `/booking/agency-invoices/{ref}/payments`;
    checker — POST `/booking/agency-payments/{id}/approve` and `/reject`. The maker never approves, the checker never
    records (and the `agency_payment_maker_checker_chk` CHECK refuses an approve by the recorder anyway).
  - **Synthetic agencies only:** an allowed write is refused 403 `e2e_synthetic_only`, before the staff row is synced
    or the route runs, unless the record (supplier booking -> trip case `party_tenant_id`; invoice; payment ->
    invoice) belongs to an agency whose `catalog.v_tenant_account_v1.is_synthetic` is true (CIS 401, contract
    tenant.entitlements.v1 1.6: `is_canary IS TRUE` and not the pilot, the A10b-1 rule). A record of no agency (a B2C
    case, a departure-owned supplier booking), an unknown id, a missing column or a database error count as real.
  - Reads keep the role's permissions (`sales`, `finance`), like A10a's admin reads.
- **Mailbox:** recipients of the A10b rule `e2e-cognito-admin` (dev only), so the codes land under `inbound-admin/`,
  which only the MFA admin role reads; never recipients of `e2e-cognito`.
- **Created outside the CIS directory,** like A10a / A10c: AA-CIS-Infra `tools/identity/crm_dev_identity.py
  e2e-booking-writers --apply` (AdminCreateUser SUPPRESS, `email_verified=true`, no password, exact groups; refuses a
  user in any other group). No secret: sign-in is the email code. The first sign-in creates each one's
  `booking.staff_users` row.
- **Exposure.** Code readers: the MFA admin role and whoever controls mail for `e2e-mail.lumiguides.it.com` (A10's
  domain dependency). What a code yields: the role's reads of Dev Booking data and at most the writes above, on
  synthetic agencies only. A CIS admin who marks a real tenant `is_canary` widens the scope (the A10b-1 trust).
- **Audit and detection:** the routes run unchanged, so `booking.audit_logs` names the identity's staff key
  (`cog:<sub>`) as the actor; `workforce_e2e_test_token_issued`, Booking `booking_e2e_writer_refused identity=…
  reason=…` and `booking_e2e_write_allowed`.
- **Used only by the agent, locally** (AA-Booking Playwright project `e2e-writers`, `BOOKING_E2E_WRITERS=1`, dry run
  `BOOKING_E2E_WRITERS_DRY_RUN=1`; a unit test keeps every workflow from setting the switch). Never CI.
- **Removal (AA-1054, with A10 / A10a / A10b / A10c / A10d):** delete the three Cognito users; drop the trigger entries,
  the mailbox recipients and the `e2e-booking-writers` command (AA-CIS-Infra), Terraform Apply; drop
  `app/auth/e2e_staff.py` and its call (AA-Booking); deactivate the three staff rows; a closing line here. Faster
  stop on Dev: disable a user, or clear `is_canary` on the synthetic tenants.

### A11. Preview staff sign-in on one fixed host, capped at viewer (22/10/2026, S247; AA-911 D-1, AA-816 P6a)

> **Superseded by A13 (07/11/2026, S272).** The fixed Preview hosts, the Preview-only clients and the Vercel projects
> are retired. The text below is the record of what ran from S247 to S272.

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

### A13. The CIS -> Booking bridge is retired; the staff apps sign in on their own hosts (06/11/2026, S271; AA-911)

Supersedes the "not changed" line of A11 and the "still not gated" line of A12 for `/auth/booking-token`, and the
A11 Preview design as the way staff sign in outside Production.

- **Why now:** ADR 0019 d23 moves the CIS admin and the Booking admin from Vercel to one ECS task behind the shared
  ALB, on the same hosts (`aa-cis.`, `booking.`), and replaces per-PR Vercel previews with `next start` checks in CI.
  Every staff sign-in then happens on a registered host with the app's WORKFORCE client, so nothing needs the bridge.
- **Booking:** accepts the WORKFORCE issuer only (`booking-staff`, `breakglass`; roles, finance included, from the
  `booking-*` groups). A bridge token is 401. The legacy CIS password form and `/api/auth/login` are removed from the
  Booking admin; a leftover `bk_cis_session` cookie is cleared.
- **CIS:** `POST /auth/booking-token` and `GET /auth/.well-known/jwks.json` are removed (404); the signing-key secret
  `aa-cis/dev/booking-jwt-signing-key` is scheduled for deletion with a 7-day recovery window.
- **Bridge-era rows:** the three `booking.staff_users` rows keyed by a CIS id are linked to their Cognito identity or
  deactivated by a one-time DB Migrate run-script (AA-CIS-Infra `db/scripts/aa911_bridge_staff_rows.py`, DRY RUN
  first).
- **Order:** staff web cut-over (runbook `docs/ops/runbooks/staff-web-ecs-cutover.md`) -> Booking bridge off ->
  CIS routes removed -> staff rows script -> secret deletion.
- **Still open (A10 family):** the E2E mailbox exceptions stay until go-live, as decided in S265.
- **Follow-up:** the Booking endpoint tests still sign in with a test-only bridge issuer; moving them to WORKFORCE
  tokens lets the bridge profile code be deleted.
- **Closing line (07/11/2026, S272, Vercel retirement; root runbook `staff-web-ecs-cutover.md` section 4):** the
  apex points at the shared ALB; the Vercel projects `aa-cis-frontend` and `aa-booking-admin`, their deploy workflows,
  the Preview hosts `aa-cis-preview.` / `booking-preview.`, the WORKFORCE clients `cis-admin-preview` /
  `booking-staff-preview` and the `aa-booking-admin.vercel.app` callback are removed. Both APIs accept no preview
  client by default (the viewer / read-only cap code stays for a client set through the env). Per-PR UI evidence is
  `Visual (next start)` in CI; the signed-in smoke runs on the production staff hosts after each `Deploy Admin Dev`.

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
  - The apex domain depended on a Vercel project claim until S272 (an unclaimed apex A record to Vercel would have
    been a takeover risk); since the AA-911 Vercel retirement it is an alias to the shared ALB.

## Links

- `docs/adr/0006-ecosystem-identity.md` (amended ADR).
- `docs/audits/2026-10-18-S242-cognito-phase1/plan.md`, `aa854-evidence.md`, `reader-maps.md`.
- `docs/database/schema-ownership.md` (`shared.staff_app_grant` in the CIS row).
- AA-CIS-App: `CONTEXT.md` § "Staff roles and permissions"; `api/core/identity_verifier.py`,
  `api/core/identity_config.py`, `api/core/staff_identity.py`, `api/middleware/staff_bearer.py`,
  `api/services/staff_directory.py`, `services/staff_reconcile.py`, `frontend/lib/cognito.ts`,
  `api/migrations/247_admin_users_identity.sql`, `api/migrations/250_admin_users_e2e_test_email.sql` (A10),
  `api/migrations/283_admin_users_e2e_cis_admin_email.sql`, `api/core/e2e_staff.py`,
  `docs/implementation-notes/AA-816-e2e-cis-admin.md` (A10b).
- AA-CIS-Infra: `accounts/aa365/identity.tf`, `identity_alerts.tf`, `identity_iam.tf`, `identity_variables.tf`,
  `dns.tf`, `tools/identity/workforce_bootstrap.py`, `e2e_mailbox.tf` and
  `lambda_src/identity_triggers/workforce.py` (A10, A10a), `docs/implementation-notes/AA-910-booking-e2e-staff.md`
  (A10a); `e2e_mailbox.tf` rule `e2e-cognito-admin`, `docs/implementation-notes/AA-816-e2e-cis-admin.md` (A10b).
- AA-Booking: `backend/app/auth/staff.py` (A10a write cap, A11 preview cap), `frontend/e2e/SIGNED-IN-SMOKE.md` (A10a).
