# ADR 0006 — Ecosystem identity on Amazon Cognito (staff, tenant users, travellers)

- **Status:** Accepted (14/10/2026, S236 — Nghiệp: Cognito on acc2, email code for staff (Google dropped: mail is on DreamHost, not Workspace), AA-703 as the epic).
- **Amended by:** [ADR 0006a](0006a-identity-phase1-amendments.md) (18/10/2026, S242): Phase 1 as shipped —
  Booking roles in `shared.staff_app_grant`, owner-only staff writes, "reset" = sign-out + re-enable,
  break-glass address `admin@adventure.asia` and its secret shape/guards, managed login on
  `staff-auth.lumiguides.it.com` with branding in Terraform, legacy flag scoped to the CIS UI, the
  `email_verified` gap and the residual `AdminCreateUser` risk. Where the two differ, 0006a wins.
- **Scope:** AA-Ecosys as a whole: AA-CIS-App (staff admin, tenant portal), AA-Booking (staff app,
  customer app), AA-TripPlanner-Web (traveller sign-in), AA-CIS-Infra (pools, triggers, domains, SES).
- **Amends:** ADR 0001 decision 6 (the clause "AA-Booking owns the customer identity (OTP)") and
  ADR 0004 O1 (staff identity = CIS-issued JWT). Both become the **interim** design; the target is below.
- **Implements:** ADR 0001 decision 7 (one IaC repo: everything is provisioned in acc2 by AA-CIS-Infra).
- **Related Linear:** AA-703 (epic, ecosystem identity) with children AA-680 (Booking customer OTP +
  staff RBAC), AA-813 (tenant users), AA-816 (staff management), AA-811 (SES email). Interim bridge:
  CIS PR #721 (CIS-issued RS256 token, `aud=booking`) + Booking `/login` via CIS credentials.
- **Research:** `docs/research/2026-10-14-cognito-identity.md` (primary sources with URLs; to be
  moved into `docs/audits/2026-10-14-S236-*/` with this ADR).

## Context

Each app grew its own sign-in, and none of them can serve the other two:

| App | Population | Today | Problem |
|---|---|---|---|
| CIS | Staff (admin / reviewer / content) | `shared.admin_users` (username + password hash + `admin_role`, no email); HS256 JWT signed with `aa-cis/dev/jwt-secret`; the BFF also sends `X-Admin-Secret` | Shared passwords, no email, no MFA, no offboarding beyond `is_active`, HS256 secret cannot be shared with other apps |
| CIS | Tenant users | `/auth/tenant-login` with the tenant's API key (`shared.tenants.api_key_hash`) → `cis_tenant_token` (role `tenant`) | One shared key per tenant for every human; no per-person account, role or audit |
| Booking | Staff | Bridge: CIS issues an RS256 token with `aud=booking` (PR #721), Booking `/login` takes CIS credentials | Works, but inherits all CIS staff-login problems |
| Booking | Customers | `booking.customers` (`verified`, lead/merge columns) + `customer_otps` + `customer_sessions` (bk-001) — a home-made OTP stack, not built out | Own OTP, sessions, rate limits and email to build and secure; no Google/Facebook |
| TripPlanner | Travellers | Guest sessions (`tripplanner.sessions.guest_token`) + `tripplanner.customers`; a typed email proves nothing (S235 Phase 0 fix in `registration.py`) | No way for a traveller to prove an email, so guest trips cannot be safely linked to a customer |

Nghiệp's decisions (S236, 14/10/2026): one identity service for the whole ecosystem, built on
**Amazon Cognito in acc2 (`005097885195`, us-west-1)**, with **two user pools** (WORKFORCE and
EXTERNAL); every app verifies JWTs via JWKS; the PR #721 bridge must be swappable by configuration.

## Decisions

### 1. Two user pools, both on the Essentials plan

| Pool | Who | Sign-up | Plan |
|---|---|---|---|
| `aa-workforce` | CIS staff (admin, reviewer, content) and Booking staff (admin, sales, contracting); one break-glass account | **Admin-create only** (`allow_admin_create_user_only = true`). Users exist only because the staff directory (AA-816) created them | Essentials. Plus (threat protection) is optional at about $0.62/month; decide after Phase 1 |
| `aa-external` | Tenant users (CIS portal) and travellers (TripPlanner, Booking customer app) | Self sign-up **allowed at pool level**, but the pre sign-up trigger rejects any self sign-up that does not come through a traveller app client (decision 5) | Essentials |

- Essentials is required for email one-time codes, managed login with branding, and access-token
  customisation. Lite would not cover them.
- Both pools have `deletion_protection = ACTIVE` and no SMS configuration (removing SMS later forces a
  pool rebuild).
- **MFA:** WORKFORCE = optional, TOTP only, used **only by break-glass**. EXTERNAL = **off**. Reason: when
  MFA is optional, a user who activates MFA can no longer use an email one-time code as first factor;
  a passwordless traveller or tenant user who enrolled TOTP would lock themselves out of email sign-in.
- **Settings that cannot change after creation, decided now:** `username_attributes = ["email"]`
  (email is the sign-in name, **not** an alias) and `username_configuration.case_sensitive = false`.
  Changing either means a new pool, and a new pool means **new `sub` values for everyone** (decision 9).
- **Account recovery = `admin_only`** in both pools. Otherwise `ForgotPassword` would let any staff member
  (or anyone holding their mailbox) set a password and sign in with it, bypassing Google and its 2-step
  verification; travellers have no password to recover.
- `user_attribute_update_settings.attributes_require_verification_before_update = ["email"]`: an email
  change keeps the old, verified address until the new one is proven.
- **AWS WAF web ACL on both pools** (supported on every plan; covers managed login and the public
  `SignUp` / `InitiateAuth` APIs): rate-based rules per IP on sign-up and code requests. Without it,
  anyone can script `SignUp` / email-code requests against the public traveller clients: each sign-up
  is a billable MAU above the free tier, each code is an SES email, and bounces damage the SES
  reputation that **staff** sign-in codes also depend on (see Costs).
- **Custom attributes: none in the first version.** They can never be changed or removed. The only
  candidate, `custom:hd`, is added only if the Google `hd` spike (Open items) needs it.
- Passwords are **not** offered to staff or travellers. The only password account is break-glass
  (decision 11).
- **Alternative kept open:** split EXTERNAL into a tenant pool and a traveller pool (no extra cost,
  the free tier is per account; costs one more custom domain, three of four used). Chosen against for
  now because one traveller who is also a tenant user would have two accounts, and the client-aware
  pre sign-up trigger is a small, testable function. Nghiệp confirms (Open item 4).

### 2. App clients, one per app surface

| App client | Pool | Used by | Flow | Accepted by API |
|---|---|---|---|---|
| `cis-admin` | WORKFORCE | CIS admin UI (Next.js BFF on Vercel) | Authorization code + PKCE, confidential (secret held by the BFF) | CIS API; Booking API (price entry and other staff screens in the shared admin, ADR 0005 decision 1) |
| `booking-staff` | WORKFORCE | Booking staff UI | Authorization code + PKCE, confidential | Booking API |
| `cis-portal` | EXTERNAL | CIS tenant portal | Authorization code + PKCE, confidential | CIS API (tenant routes only) |
| `booking-customer` | EXTERNAL | Booking customer app (sign-in, My Trips, payments — ADR 0004 O8) | Authorization code + PKCE | Booking API (customer routes only) |
| `tripplanner` | EXTERNAL | TripPlanner web + its Lambdas | Authorization code + PKCE | TripPlanner backend; Booking API (customer routes, when TripPlanner shows trip status) |

- Every client enables `ALLOW_USER_AUTH` (choice-based sign-in) with **refresh-token rotation on**
  (grace period ≤ 60 s). `ALLOW_REFRESH_TOKEN_AUTH` is **not** enabled: AWS documents that rotation is
  incompatible with the `REFRESH_TOKEN_AUTH` flow; refresh goes through `/oauth2/token`
  (`grant_type=refresh_token`) or `GetTokensFromRefreshToken`. No client enables
  `ALLOW_USER_PASSWORD_AUTH` or `ALLOW_USER_SRP_AUTH`. `PASSWORD` is an allowed first factor **only in
  WORKFORCE** (break-glass); EXTERNAL allows `EMAIL_OTP` only (plus federation).
- **OAuth scopes = `openid email profile`** on every client. `aws.cognito.signin.user.admin` is **not**
  allowed: with it, a user's own access token can call `UpdateUserAttributes`, `DeleteUser`, MFA set-up
  and similar self-service APIs directly. Every client sets explicit `read_attributes` and a minimal
  `write_attributes` (`name` only); `email`, `email_verified` and any `custom:*` attribute are never
  client-writable.
- Break-glass signs in through its own client `breakglass` (WORKFORCE, callback = CIS admin), so its
  shorter token lifetimes (decision 7) can be enforced — lifetimes are set per app client, not per user.
- The traveller clients (`booking-customer`, `tripplanner`) share one managed-login session, so a
  traveller who signed in on TripPlanner is already signed in on the Booking customer app.
- Machine callers do **not** get Cognito clients (client-credentials tokens are billed per request).
  Tenant API keys stay for machine access to the CIS API (decision 12, Phase 3).

### 3. Roles: Cognito groups for staff, app database for tenants

**Staff (WORKFORCE groups).** Group name = `<app>-<role>`:

| Group | Maps to |
|---|---|
| `cis-admin`, `cis-reviewer`, `cis-content` | `shared.admin_role` values `admin`, `reviewer`, `content` |
| `booking-admin`, `booking-sales`, `booking-contracting`, `booking-content_creator` | Booking staff roles (replaces the planned `staff_role` enum in `booking.staff_users`). `booking-content_creator` added S241 (Nghiệp, Q4/Q5): staff who only write Booking content; applied with the Phase 0 pools (Infra #162). |

- **Source of truth = the staff directory** (AA-816): `shared.admin_users` gains `email` (unique,
  lower-cased, `@adventure.asia`), `display_name`, `cognito_sub` and per-app role columns;
  `password_hash` becomes nullable and is dropped after cutover (CIS migration, CIS-owned).
  *(Amended by 0006a A1–A3: Booking roles live in `shared.staff_app_grant` (CIS 247), and only owners
  (`is_owner`, Cognito session) write the directory.)*
- The directory's admin UI (in the CIS admin) is the **only writer** of Cognito users and group
  memberships: each change writes the directory row, then calls `AdminCreateUser` /
  `AdminAddUserToGroup` / `AdminRemoveUserFromGroup` / `AdminDisableUser`. A reconcile job
  (`shared.job` kind) compares the directory with the pool daily and on demand, and reports drift
  in the admin UI. **The reconcile job only reports; it never creates, enables or re-groups a user**
  (a corrupted directory row must not turn into a staff account by itself). It uses `ListUsers` /
  `ListUsersInGroup`, which do not count as MAU (`AdminGetUser` does). Nobody edits groups in the console.
- **IAM for the directory writer (CIS task role) is an explicit allow-list** on the WORKFORCE pool ARN:
  `AdminCreateUser`, `AdminAddUserToGroup`, `AdminRemoveUserFromGroup`, `AdminDisableUser`,
  `AdminEnableUser`, `AdminUserGlobalSignOut`, `ListUsers`, `ListUsersInGroup`. It explicitly **excludes**
  `AdminSetUserPassword`, `AdminUpdateUserAttributes`, `AdminLinkProviderForUser`, `AdminInitiateAuth`,
  `AdminRespondToAuthChallenge` and `AdminDeleteUser`: with any of them, a compromised CIS API could
  point a staff account at an attacker mailbox or password and sign in as that person. An email change
  for staff is a manual, logged procedure. The same rule applies to the EXTERNAL pool (invitations):
  `AdminCreateUser`, `ListUsers`, `AdminDisableUser`, `AdminUserGlobalSignOut` only.
- The directory UI rejects any email not ending in `@adventure.asia`, and so does the WORKFORCE pre token
  trigger (decision 5), so a directory bug cannot create a non-staff account that signs in by email code.
- `booking.staff_users` stays a thin profile (ADR 0004 O1), keyed by the Cognito `sub` and
  `admin_users.id`, with **no role column**: Booking reads roles from `cognito:groups` in the token.
- A staff member can hold several groups (for example `cis-content` + `booking-sales`).

**Tenant users (EXTERNAL).** Tenant scope is **not** stored in Cognito:

- CIS owns a new table (name decided in AA-813, e.g. `shared.tenant_members`):
  `tenant_id`, `user_sub`, `role` (`owner` / `editor` / `viewer`), `status`
  (`invited` / `active` / `removed`), `invited_by`, `invited_email`, timestamps.
- The CIS API resolves membership from the token's `(iss, sub)` on each request (cache ≤ 60 s,
  invalidated on any membership write). A user can belong to several tenants and picks one in the
  portal; the chosen `tenant_id` travels in the request (header or path) and is **always** checked
  against an `active` membership row — the tenant is never taken from the token or trusted from the
  client. The resulting tenant context has the same shape the API-key path produces today
  (`verify_tenant_api_key`), so the per-tenant DB scoping (AA-544 tenant pool) keeps working.
- The **membership table is the security boundary** for tenants. Anyone can hold an EXTERNAL account
  (travellers self-sign-up, and one managed-login session covers every EXTERNAL client), so holding a
  valid `cis-portal` token proves nothing about a tenant on its own.
- Reason: per-tenant groups (`tenant:<id>:owner`) hit the hard limit of 100 groups per user and put
  business data in an IdP that cannot be queried with SQL.

**Travellers** have no group and no role. Booking and TripPlanner map `sub` to their own customer rows
(decision 9).

### 4. Sign-in methods per population

| Population | Primary | Fallback | Not allowed |
|---|---|---|---|
| Staff | **Google** (Workspace accounts `@adventure.asia` that already exist in the staff directory) | **Email one-time code** to the same address (native profile, Essentials `EMAIL_OTP`) | Passwords, Facebook, self sign-up |
| Break-glass | Password + TOTP MFA | — | Google, OTP |
| Tenant users | **Email one-time code** (by invitation) | Google, once linked by verified email (decision 6) | Self sign-up, Facebook (until Nghiệp decides otherwise) |
| Travellers | **Email one-time code**, Google, Facebook | — | Passwords |

- **Passkeys are off** in both pools until the production auth domain is fixed. A passkey is bound to
  the relying-party ID, which defaults to the custom domain; moving from `lumiguides.it.com` to a
  production domain would orphan every passkey.
- The staff email-code fallback is single-factor (mailbox possession) and **bypasses Google 2-step
  verification and Workspace context-aware access**. Accepted for availability; the fallback is
  only as strong as the `@adventure.asia` mailboxes (no auto-forwarding to personal mail — Workspace
  policy, Open item 6). Plus (Open item 9) adds risk detection on these native sign-ins.
- Google 2-step verification for staff is enforced in the Google Workspace admin console, not in
  Cognito (Open item 6).

### 5. Allow-list and domain enforcement by Lambda triggers

Triggers are Python 3.12 Lambdas in AA-CIS-Infra, **outside the VPC and without database access**:
they only call the Cognito API on their own pool. Reason: the trigger timeout is 5 seconds and cannot
be changed, and a VPC cold start plus an RDS connection would eat most of it. The allow-list therefore
lives **in the pool itself**: a staff member is allowed if and only if the directory has pre-created an
enabled native user for that email.

**WORKFORCE**

1. **Pre sign-up** (`PreSignUp_ExternalProvider`, first Google sign-in only). Reject unless **all** hold:
   - `email_verified` is true (the Google IdP attribute mapping **must** map `email_verified`);
   - the email ends with `@adventure.asia` and the Google `hd` claim equals `adventure.asia`
     (how `hd` reaches the trigger is the spike in Open item 3);
   - exactly one **enabled native** user with that email exists in the pool (exact, lower-cased
     match; reject any email containing `"` or `\` before building the `ListUsers` filter, and
     re-compare the returned `email` exactly);
   - that native user has **no Google identity linked yet** (`identities` attribute empty). A second
     Google account for the same address (e.g. a deleted and re-created Workspace account) is
     rejected until an admin clears the old link by the documented procedure.

   Then call `AdminLinkProviderForUser` (destination = that native user, source = `Google` /
   `Cognito_Subject` = Google `sub`). Every later Google sign-in lands on the native profile. The
   self-created `Google_<sub>` profile is never kept. Cognito may retry the trigger, so an
   "already linked to this same `sub`" result counts as success.
   - `PreSignUp_AdminCreateUser` (directory creating a user) is allowed. Any other self sign-up is rejected.
   - The trigger never sets `autoVerifyEmail` / `autoConfirmUser`.
2. **Pre token generation** (V2_0, every issue **including refresh**), a pure function of the event
   (no Cognito or network call, so it cannot time out on a dependency):
   - deny unless the user is in at least one staff group **and** `email` ends with `@adventure.asia`
     (disabled users never reach the trigger: Cognito already refuses them);
   - strip any group that is not in the table in decision 3 (`groupOverrideDetails`);
   - add `email` to the **access** token (Cognito access tokens carry no email by default);
   - when the user is the break-glass user, write a structured log line that a metric filter turns into
     an alarm (decision 11).

   This closes the gap that pre authentication does not fire on refresh.
3. Error messages are generic ("Not authorised for AA staff sign-in"), because Cognito shows them to
   the user.

**The Inbound federation trigger is not used.** It is the only trigger that sees raw Google claims, but
the Terraform provider does not support it and `apply` silently removes it if set by hand
(hashicorp/terraform-provider-aws #49707). Revisit when provider PR #47954 ships.

**EXTERNAL**

1. **Pre sign-up**, by `callerContext.clientId`:
   - `cis-portal`: reject **every** `SignUp` and every federated first sign-in. The trigger has no
     database access, so it cannot see pending invitations; invited users are created by the CIS API
     with `AdminCreateUser` (Phase 3), and a person who already has an EXTERNAL account accepts the
     invitation with that account (Phase 3). This rule is hygiene, not the tenant boundary (decision 3);
   - `tripplanner`, `booking-customer`: allow; for a federated sign-up, link to an existing native
     user **only** under decision 6;
   - `PreSignUp_AdminCreateUser` (invitations): allow;
   - unknown or missing `clientId`: reject (fail closed).
2. **Pre token generation** (V2_0): no tenant claims (decision 3). It removes every group, so an
   EXTERNAL token can never carry a staff-looking group, and it adds `email` and `email_verified` to the
   **access** token, so APIs can apply decision 6 without calling `userInfo`.

**Trigger failure modes (both pools).** Every trigger fails **closed**: an exception, a timeout (5 s,
fixed) or a throttle denies the sign-in or token issue. That is the right side for security, but a bad
trigger deploy denies **everyone, break-glass included** (break-glass is a user of the same pool).
Therefore: triggers are pinned to a Lambda **alias** and released through Terraform only after unit tests
over recorded events of every `triggerSource`; no reserved-concurrency cap that could throttle sign-ins;
CloudWatch alarms on trigger `Errors` / `Throttles` / `Duration p99 > 3 s`; rollback = repoint the alias.
The recovery path for a broken trigger is an AWS admin with MFA (Terraform or console), not break-glass.

### 6. Account linking rules

- Cognito never merges accounts by email on its own. Linking happens **only** in our triggers or in
  the invitation flow, and **only on a verified email**:
  - native email confirmed by a one-time code, or
  - Google with `email_verified = true`.
- A link target must be a native user in status **`CONFIRMED`** with `email_verified = true` and no
  existing link from the same provider. An `UNCONFIRMED` native user (someone called `SignUp` with an
  address but never entered the code) is never a link target: otherwise anyone could pre-register a
  victim's address and have the victim's Google identity attached to a profile created by the attacker.
- Triggers **never** set `autoVerifyEmail` or `autoConfirmUser`. Besides skipping proof, AWS documents
  that auto-verifying an address used by another user moves it and marks the other user's email
  unverified.
- Email addresses an admin sets as verified (`AdminCreateUser` for staff and invitations) are trusted
  only because the address's mailbox (OTP) or a Google account with that verified address is the only
  way to sign in to that user. APIs read `email_verified` from the access token (decision 5) and use an
  email for any linking or merge only when it is `true`.
- **A Facebook email is never trusted for linking.** Facebook sends no `email_verified`; a Facebook
  sign-in always creates or reuses its own profile, and the traveller can link it to an email account
  later only after proving that email with a one-time code.
- **Social sign-in never creates staff access or tenant membership.** Staff exist only through the
  directory (WORKFORCE is a different pool); tenant membership exists only through an accepted
  invitation (decision 3).
- Link before first sign-in: AWS supports linking only before the federated user's first sign-in;
  linking later requires deleting the auto-created profile. At most 5 linked identities per user.

### 7. Token lifetimes

| Pool / client | Access + ID token | Refresh token | Notes |
|---|---|---|---|
| WORKFORCE (`cis-admin`, `booking-staff`) | **15 min** | **12 h** (one working day), rotation on | Offboarding = `AdminDisableUser` + `AdminUserGlobalSignOut`; worst case a stolen access token lives 15 min |
| Break-glass (own client `breakglass`) | 15 min | 1 h (the minimum) | Lifetimes are per app client, so break-glass needs its own client |
| EXTERNAL `cis-portal` | 30 min | 7 days | |
| EXTERNAL traveller clients | 60 min | 30 days | |

Revocation cannot be detected offline, so access tokens stay short. APIs do not call Cognito per request.

- Rotation does not extend a refresh token: the window is fixed from the first sign-in, so staff sign in
  again at least once a working day.
- The managed-login session cookie lasts one hour and is not cleared by `AdminUserGlobalSignOut`
  (AWS: access tokens shorter than one hour do not stop silent re-sign-in within that hour). Offboarding
  is therefore **`AdminDisableUser` first** (a disabled user cannot re-authenticate even with the cookie),
  then `AdminUserGlobalSignOut`; the worst case remains one live access token (15 min).

### 8. JWT verification contract (every app)

Every API (CIS FastAPI, Booking FastAPI, TripPlanner Lambdas) uses **one verifier, driven by
configuration only**. Per accepted issuer it holds:

| Setting | Cognito value | Bridge value (PR #721) |
|---|---|---|
| Issuer (`iss`) | The pool's issuer **as published by Terraform output / the pool's `openid-configuration`**: `https://cognito-idp.us-west-1.amazonaws.com/<poolId>` for the original issuer type, or `https://issuer-cognito-idp.us-west-1.amazonaws.com/<poolId>` if the pool uses the updated issuer type. Never the custom domain, never hand-built | CIS issuer string |
| JWKS URL | `<issuer>/.well-known/jwks.json` | CIS JWKS endpoint (key `aa-cis/dev/booking-jwt-signing-key`, kid `bk-2026-10`) |
| Audience claim | `client_id` (access token) | `aud` |
| Allowed audiences | the app client IDs accepted by this API (decision 2) | `booking` |
| `token_use` | `access` | not checked |
| Roles claim | `cognito:groups` | `role` |

Rules:

1. RS256 only (reject `none`, `HS*` and any other `alg`); ignore `jku` / `x5u` / `jwk` headers.
2. **Select the issuer entry by the unverified `iss`, then use only that issuer's JWKS.** A `kid` is never
   looked up across issuers (otherwise a token claiming the Cognito issuer could be checked against the
   bridge key set, or the reverse). Unknown `iss` → 401.
3. Keys cached by `kid` per issuer, refetched at most once per minute on an unknown `kid`; the last good
   key set is kept if a refetch fails. CIS and Booking reach the JWKS through the single NAT instance, so
   keys are fetched at start-up and a NAT blip must not turn into a sign-in outage.
4. Check signature, `exp` (≤ 60 s leeway), `iss`, `token_use`, and audience (`client_id` for Cognito
   access tokens).
5. **APIs accept access tokens only.** ID tokens are for the UI to read the profile.
6. **Each route class declares the exact `(issuer, client_id)` pairs it accepts**, not "any configured
   issuer": e.g. CIS staff routes = WORKFORCE × {`cis-admin`, `breakglass`}; CIS tenant routes =
   EXTERNAL × {`cis-portal`}; Booking staff routes = WORKFORCE × {`cis-admin`, `booking-staff`,
   `breakglass`} (+ bridge during Phase 2); Booking customer routes = EXTERNAL × {`booking-customer`,
   `tripplanner`}. Staff authorisation therefore never rests on a group claim alone.
7. The verifier returns a `Principal` (`issuer`, `sub`, `client_id`, `groups`, `email`,
   `email_verified`; email fields come from the pre token trigger, decision 5). Authorisation
   (staff role, tenant membership, customer ownership) is the app's job, after verification.
8. Several issuers can be configured at once, so the bridge and Cognito are accepted together during a
   switch, then the bridge entry is removed.
9. The module is written once (reference implementation in the research doc §7), copied byte-identical
   into each repo with the same unit tests, until a shared package exists (same pattern as the UI kit).
10. Resource binding (`resource=` → `aud` = API URL) is **not** used in the first version; `client_id`
   allow-lists are enough. It can be added per API without changing the contract.

### 9. Identity keys in app data

- **The identity key is the pair `(iss, sub)`** everywhere. `sub` alone is unique only inside one pool:
  bridge tokens carry `admin_users.id` as `sub`, and a pool rebuild (forced by changing an immutable
  setting) or a future production pool issues new `sub` values. Email is a contact attribute and can change.
- One person can legitimately hold **more than one** EXTERNAL profile (a Facebook profile is never
  linked automatically, and a native email profile cannot be merged into an earlier Google-only
  profile — AWS links only an external identity into a destination user). Apps therefore keep an
  identity table, not a single column: Booking `booking.customer_identities (iss, sub) UNIQUE →
  customer_id` (`bk-NNN`); a second identity is attached to an existing customer only through a verified
  email (decision 6).
- `shared.admin_users.cognito_sub` (+ issuer) (CIS), `booking.staff_users` keyed by `(iss, sub)`
  (Booking), tenant membership by `(iss, sub)` (CIS). TripPlanner keeps `tripplanner.customers` for
  guest contact data only and stores `(iss, sub)` on a signed-in session.
- Booking keeps ownership of the **customer record** (profile, `verified`, lead/merge logic, ADR 0004
  O6). Cognito owns only **authentication**. This is the amendment to ADR 0001 decision 6.

### 10. Email via SES (AA-811) and custom domains

- Both pools send through **Amazon SES (`DEVELOPER` mode)**. The Cognito default sender (50 emails/day
  per account, not raisable) is used only before AA-811 lands, and email one-time codes do not work on it.
- The SES identity must be in **acc2, us-west-1** (in-region only for a us-west-1 pool), with DKIM, and
  the account must be **out of the SES sandbox in us-west-1**. AA-811 therefore blocks every OTP phase.
- Branded, localised messages through the custom message trigger (templates in AA-CIS-Infra).
- **Custom domains** (one per pool; 2 of the 4 allowed per region):
  - EXTERNAL: `auth.lumiguides.it.com`;
  - WORKFORCE: `staff-auth.lumiguides.it.com`.
  - ACM certificate in **us-east-1**, public, issued in acc2. The parent `lumiguides.it.com` must have an
    A record. DNS records at Namecheap (CNAME/alias to the Cognito CloudFront target).
  - Managed login version 2, TLS policy `TLS_V1_2_2021` or stricter. The provider cannot set the TLS
    policy yet (#48731); the default applies.
- Until the certificate exists, Dev uses the Cognito prefix domains; Google and Facebook then register
  both redirect URIs.

### 11. Break-glass

- One native WORKFORCE user (`breakglass@adventure.asia` or a dedicated mailbox), password + TOTP,
  member of `cis-admin` and `booking-admin`. *(Amended by 0006a A4: the address is `admin@adventure.asia`;
  secret shape, resource policy, alerts and the enable/disable runbook are there.)*
- Password and TOTP seed in Secrets Manager (`aa-identity/dev/breakglass`), readable only by the admin
  role, retrieval alerted (CloudTrail → email).
- It passes the pre token trigger like any staff user (enabled + staff groups); it never goes through
  pre sign-up because it is not federated. Used only when Google or SES is down; each use is logged
  in the session log.
- Signs in only through the `breakglass` client (decision 2). Every token issue for it raises an alarm
  from the pre token trigger log (decision 5); CloudTrail alone does not reliably show user sign-ins.
- Kept **disabled** (`AdminDisableUser`) between uses; enabling it needs AWS admin credentials with MFA,
  which is itself logged in CloudTrail. This keeps a leaked secret from being usable on its own.
- **Limits:** break-glass covers a Google or SES outage only. It does **not** cover a broken trigger, a
  wrong app-client setting or a Cognito outage, because it is a user of the same pool. Those are
  recovered by an AWS admin (decision 5, failure modes) and, during migration, by the legacy-login flag
  (Migration plan).

### 12. Infrastructure as code

- Pools, clients, groups, IdPs, domains, Lambda triggers and permissions are in Terraform in
  AA-CIS-Infra (`accounts/aa365/identity.tf`, self-contained like `booking.tf`).
- The provider is pinned `~> 5.40` (locked 5.100.0). Pool tier, passwordless sign-in and the
  managed-login domain work on 5.x. **Managed-login branding needs provider 6.12+**: branding stays out
  of Terraform (CLI script in the repo) until a separate 5 → 6 upgrade issue is done.
- Google and Facebook client secrets live in Secrets Manager, set out-of-band by Nghiệp (placeholder +
  `ignore_changes`, the `booking/dev/database-url` pattern).

## Migration plan

Each phase is shippable on its own and leaves the old path working until its cutover step.

| Phase | Scope | Depends on | Cutover / done when |
|---|---|---|---|
| **0 — Pools and triggers** | `identity.tf`: two pools, six clients (incl. `breakglass`), groups, WAF web ACL, Google IdP (WORKFORCE + EXTERNAL), Facebook IdP (EXTERNAL, disabled until the app is live), triggers, prefix domains; break-glass user. Spike (Open item 3) before the pre sign-up code is final | Google OAuth clients (Open item 1) | Plan/apply green; a test staff user signs in with Google and with an email code; the pre token trigger denies a user with no group |
| **1 — CIS staff login + directory** (AA-816) | CIS migration: `admin_users` + `email`, `cognito_sub`, `display_name`, Booking role column; directory UI in CIS admin writes DB + Cognito; reconcile job. CIS admin UI signs in through `cis-admin`; CIS API verifier accepts Cognito; staff routes authorise from `cognito:groups`. The first two WORKFORCE users (Nghiệp + break-glass) are created by a one-off script, since the directory UI itself needs a signed-in admin | Phase 0; AA-811 for the email-code fallback (Google works without it) | **Preconditions before switching anything off:** every active `admin_users` row has an `@adventure.asia` email and a `cognito_sub` filled by a **successful Cognito sign-in** of that person; break-glass sign-in tested end to end. **Then:** password login is switched off by a config flag (`LEGACY_ADMIN_LOGIN_ENABLED=false`), **not deleted**: code and `password_hash` stay for 30 days as the rollback path if a trigger or client misconfiguration locks staff out. The BFF stops sending `X-Admin-Secret` and the secret is **rotated** (the old value lives in Vercel env and grants full admin plus tenant impersonation through `verify_tenant_api_key`); the new value stays only for docs/ops until a later issue removes it |
| **2 — Booking staff** (AA-680 staff part) | Booking verifier config: add the Cognito WORKFORCE issuer, then remove the CIS bridge issuer. Booking staff UI signs in through `booking-staff`. `booking.staff_users` keyed by `sub` | Phase 1 | Booking `/login` via CIS credentials removed; the CIS bridge token endpoint and `aa-cis/dev/booking-jwt-signing-key` retired after one release with both issuers |
| **3 — Tenant users** (AA-813) | CIS migration: tenant membership table; invitation flow: owner invites by email → CIS stores a single-use, expiring (7 days), **hashed** invitation token → `AdminCreateUser` in EXTERNAL (`MessageAction=SUPPRESS`, no password, `email_verified=true`; if the address already has a profile, nothing is created) → branded SES mail with the portal link + token → the person signs in through `cis-portal` (email code or Google) → CIS activates the membership **only if** the token is valid **and** the access token's `email_verified=true` and `email` equals `invited_email`; the membership binds to that token's `(iss, sub)`. A membership is never bound by looking a user up by email (a Facebook or unconfirmed profile can carry any address). Roles owner/editor/viewer enforced in the CIS API; only `owner` invites/removes, and the last owner cannot be removed | Phase 0, AA-811 | `/auth/tenant-login` with the API key is **closed for human sessions** (portal no longer offers it). **API keys remain for machine access** (`X-API-Key` on the public API), unchanged |
| **4 — Travellers** (AA-680 customer part) | TripPlanner and Booking customer app sign in through their clients (email code, Google, Facebook). Booking: `customers` gains the identity `sub`; on first sign-in with a **verified** email, Booking merges the lead customer created from `inquiry.submitted` (ADR 0004 O6) and links the trip cases. Lead fields were typed by an unauthenticated guest, so the merge keeps the verified profile's contact data and imports **no** unverified field (phone, address) without the customer confirming it. TripPlanner: a signed-in session carries `(iss, sub)`; a guest trip is claimed only by **the browser that holds its `guest_token`** at the moment it signs in — never by matching a typed email against other guest sessions. Retire `booking.customer_otps` and `booking.customer_sessions` (a later `bk-NNN` drops them once nothing reads them) | Phase 0, AA-811, Facebook app live for Facebook sign-in | Booking has no own OTP or session code; `registration.py` Phase 0 rule ("typed contact proves nothing") stays for guests, and a verified sign-in is the only way to attach a guest trip to a customer |

Order constraints:

- AA-811 (SES in us-west-1, out of sandbox) blocks the email-code parts of Phases 1, 3 and 4.
  Google-only staff sign-in can go live first.
- The PR #721 bridge stays in service until Phase 2 cutover. No new consumer may start using it.
- Every schema change is a migration in its owner repo applied by DB Migrate (ADR 0001 decision 6).

## Consequences

- **Positive:**
  - one place to add, change and remove a person; offboarding is one action plus a 15-minute worst case;
  - staff sign in with the Google account they already have; no shared passwords; AA-656 passwords retire;
  - per-person tenant accounts with roles and audit, instead of one API key per tenant;
  - travellers can prove an email, which finally makes guest → customer linking safe;
  - one verifier contract for three apps; the PR #721 bridge swaps by configuration;
  - no OTP, session or rate-limit code to build in Booking.
- **Negative / cost:**
  - a managed dependency in the sign-in path (Cognito quotas: 120 sign-ins/s, 25 federation callbacks/s
    and a non-raisable 25 admin updates/s — all far above our scale);
  - Lambda triggers with a hard 5-second limit; their errors are shown to users;
  - the Google `hd` check depends on a spike (Open item 3);
  - custom attributes are permanent, so the schema must stay minimal;
  - managed-login branding outside Terraform until the provider upgrade;
  - one more set of secrets (Google, Facebook, break-glass) set out-of-band.

## Costs (research §2, prices at 14/10/2026)

- Essentials: **10,000 free MAU per month per account**, shared by both pools, no expiry; then
  **$0.015/MAU**. Google and Facebook users are billed as ordinary MAU; a user with linked identities
  is 1 MAU. SES: **$0.10 per 1,000 emails**.

| Scenario | MAU | Cognito / month | OTP email / month |
|---|---|---|---|
| 30 staff + 1 break-glass + 50 tenant users + 2,000 travellers | ~2.1k | **$0** | ~$0.63 |
| Same with 20,000 travellers | ~20.1k | **~$151** | ~$6 |
| WORKFORCE on Plus (optional) | +31 | +$0.62 | — |

Lambda triggers and Secrets Manager add cents.

Cost surprises to plan for:

- **AWS WAF on the two pools** (decision 1): about $5 per web ACL + $1 per rule + $0.60 per million
  requests, i.e. roughly **$12–15/month** for two small web ACLs. One web ACL can be shared if the rules
  are the same.
- **Sign-up abuse:** a sign-up counts as an MAU even if never confirmed, and every code is an SES mail.
  Without WAF, a script calling `SignUp` on the public traveller client could push the account past the
  10,000 free MAU ($0.015 each above it) and get SES paused for bounces, which would stop **staff**
  email codes too. Mitigations: WAF rate rules, an SES configuration set with bounce/complaint alarms, a
  separate configuration set (and ideally sender sub-domain) for WORKFORCE vs EXTERNAL mail, and a
  monthly job that deletes `UNCONFIRMED` users older than 7 days.
- `AdminGetUser` counts as MAU; reconcile and support tools use `ListUsers` (decision 3).

## Alternatives considered

- **Keep the CIS staff login as the identity provider for everyone** (ADR 0004 O1 extended). Rejected:
  we would build email codes, social sign-in, MFA, rate limits and key rotation ourselves.
- **One pool for everyone.** Rejected: staff must be admin-create-only and Google-restricted, travellers
  self-sign-up; one pool would rely on triggers for the most sensitive rule.
- **Three pools (staff, tenants, travellers).** Kept as a fallback (decision 1, Open item 4).
- **Tenant roles as Cognito groups.** Rejected: 100 groups per user, no SQL, business data in the IdP.
- **Inbound federation trigger for `hd`.** Rejected for now: Terraform drops it (#49707).
- **Auth0 / Clerk.** Not evaluated in depth: a second vendor and billing outside acc2, against ADR 0001
  ("no new accounts", acc2 governance).

## Decisions on open items (S236)

- Staff sign-in: **email one-time code only** (amended S236). adventure.asia mail is hosted on DreamHost (MX mailchannels.net, SPF dreamhost), not Google Workspace, so there is no Workspace organization, no Internal consent screen and no `hd` claim — Google sign-in for staff would let a personal Google account registered on an @adventure.asia address pass. The WORKFORCE Google IdP stays disabled (`count = 0` in Infra #105). Passkeys may be added once the production auth domain is fixed. Nothing to register with Google.
- EXTERNAL pool shape: one pool with the client-aware pre sign-up (item 4).
- SES sender for Dev: `no-reply@lumiguides.it.com` (item 5); production domain decided with AA-811.
- Plus tier for WORKFORCE: later (item 9). Break-glass custodian: Nghiệp (item 7).

## Open items needing Nghiệp

1. **Google OAuth clients** in Google Cloud console:
   - WORKFORCE: a client in a project whose consent screen is **Internal** — **mandatory**, not
     optional. Google limits Internal apps to members of the Google Cloud Organization that owns the
     project (`org_internal` error for anyone else), so a consumer Google account that happens to use an
     `@adventure.asia` address (a "conflicting account") cannot sign in at all. This is the primary
     domain control while the `hd` check depends on the spike. **Precondition:** the Google Cloud
     project must sit under the `adventure.asia` Cloud Organization (Workspace admin access needed);
   - EXTERNAL: a separate client with an **External** consent screen, basic scopes only
     (`openid email profile`) to avoid the 100-user unverified-app cap;
   - redirect URIs: `https://staff-auth.lumiguides.it.com/oauth2/idpresponse`,
     `https://auth.lumiguides.it.com/oauth2/idpresponse`, plus the two Cognito prefix-domain URIs for Dev;
   - authorised domain `lumiguides.it.com`; client secrets into Secrets Manager.
2. **Facebook app**: Business Verification, Advanced Access for `email`, Live mode; same redirect URI
   as the EXTERNAL Google client. Facebook sign-in stays disabled until then.
3. **Spike before Phase 0 closes:** (a) first Google sign-in with pre sign-up linking to a pre-created
   native user (AWS documents it; not yet tested by us); (b) whether `hd` can be mapped through the
   Google attribute mapping into the trigger without the Inbound federation trigger. If not: rely on
   the Internal consent screen + allow-list and add `custom:hd` only if the spike shows it is needed.
   A mapped `custom:hd` must be mutable (mapping writes it on each sign-in), so it must be absent from
   every client's `write_attributes`, or a user could set it themselves.
   (c) a directory user created by `AdminCreateUser` **without a password** and with
   `MessageAction=SUPPRESS`: its status, and that it can sign in with an email code and be the link
   target in (a). (d) the first-sign-in UX when pre sign-up links (whether the user sees an error once).
4. **EXTERNAL pool shape:** one pool with the client-aware pre sign-up (recommended) or separate tenant
   and traveller pools.
5. **Sender domain for SES (AA-811):** which domain sends the codes (e.g. `no-reply@lumiguides.it.com`
   for Dev, `adventure.asia` for production — needs DNS access for DKIM) and the SES production-access
   request in us-west-1.
6. **Google Workspace policy:** enforce 2-step verification for staff accounts.
7. **Break-glass custodian:** who holds the TOTP device and who may read the secret.
8. **ACM certificate in us-east-1** for the two auth sub-domains, and the apex A record on
   `lumiguides.it.com`.
9. **Plus for WORKFORCE** (~$0.62/month, compromised-credential and risk detection): yes or later.

## Review notes (S236)

Adversarial security and architecture review, 14/10/2026. AWS claims were checked against these AWS docs
on the same day: refresh tokens and rotation, the access token, federation endpoints and issuer types,
the pre sign-up trigger, and WAF for user pools. Google Internal consent was checked against Google
Cloud help 15549945.

Changes made to this draft:

1. **Refresh flow fixed (decision 2).** The draft enabled `ALLOW_REFRESH_TOKEN_AUTH` together with
   rotation. AWS: "Refresh token rotation isn't compatible with the authentication flow
   `REFRESH_TOKEN_AUTH`." Clients now refresh through `/oauth2/token` or `GetTokensFromRefreshToken`.
2. **Self-service scope removed (decision 2).** `aws.cognito.signin.user.admin` lets a user's own access
   token update its attributes and MFA settings. Scopes are now `openid email profile`, with explicit
   minimal `write_attributes`.
3. **Break-glass client (decisions 2, 7, 11).** Token lifetimes are set per app client, so the 1-hour
   break-glass refresh token was not enforceable. Added a `breakglass` client. The account is disabled
   between uses, every token issue raises an alarm, and the docs now say what break-glass does not cover:
   a broken trigger or a broken pool.
4. **Pool settings that cannot change later (decision 1).** Email is the username, not an alias.
   Usernames are case-insensitive. Account recovery is `admin_only`, so `ForgotPassword` cannot set a
   password that bypasses Google. Email changes need verification. MFA is off in EXTERNAL, because an
   enrolled TOTP blocks email-code sign-in.
5. **WAF plus sign-up-abuse costs (decision 1, Costs).** Unconfirmed sign-ups still count as MAU and
   still send SES mail. Shared SES reputation would also take down staff codes.
6. **Directory IAM allow-list (decision 3).** The draft let the CIS task role write to Cognito without
   naming actions. Now `AdminSetUserPassword`, `AdminUpdateUserAttributes`, `AdminLinkProviderForUser`
   and `Admin*Auth` are excluded. The reconcile job is report-only. A pre token check for
   `@adventure.asia` covers directory bugs.
7. **WORKFORCE pre sign-up hardening (decision 5).** The trigger now does the following:
   - matches emails exactly and escapes the filter;
   - rejects a target that already has a linked Google identity, which stops email-recycling takeover;
   - treats a retried link as idempotent;
   - never sets auto-verify or auto-confirm.
8. **Pre token is pure and adds email claims (decision 5).** Cognito access tokens carry no `email`, but
   the draft's `Principal.email` assumed they did. Both pools now inject `email` (EXTERNAL also gets
   `email_verified`).
9. **Contradiction fixed: the `cis-portal` "pending invitation" check.** Triggers have no database
   access by design (decision 5), so they could not see invitations. `cis-portal` now rejects every
   self sign-up. The docs state that tenant membership in the CIS database is the real boundary.
10. **Linking takeover closed (decision 6).** An attacker could call `SignUp` with the victim's address
    and leave the user `UNCONFIRMED`. Federated linking to such a user is now forbidden: targets must be
    `CONFIRMED` and have `email_verified = true`.
11. **Trigger failure modes made explicit (decision 5).** Triggers fail closed. Releases go through an
    alias with tests, with alarms, no concurrency cap, and recovery by an AWS admin.
12. **Verifier hardening (decision 8).** Changes:
    - per-issuer JWKS selection, so a `kid` is never mixed across issuers;
    - alg and header restrictions;
    - fail-static JWKS cache, because the single NAT instance sits in the fetch path;
    - each route class declares the `(issuer, client_id)` pairs it accepts;
    - the issuer comes from Terraform output, because AWS has an "updated issuer" format
      (`issuer-cognito-idp…`).
13. **Identity key = `(iss, sub)`, plus a Booking identity table (decision 9).** One person can have
    several EXTERNAL profiles: Facebook is never auto-linked, and a native profile cannot be merged into
    an earlier Google-only profile. A pool rebuild changes every `sub`.
14. **Token lifetimes vs the managed-login cookie (decision 7).** The cookie lasts one hour and global
    sign-out does not clear it. Offboarding now disables the user first, then signs them out.
15. **Migration lock-out guard (Phase 1).** Changes:
    - preconditions are verified per person before cut-over;
    - legacy login sits behind a flag for 30 days instead of being deleted;
    - the first users are created by a bootstrap script;
    - `ADMIN_SECRET` is rotated, since it grants admin plus tenant impersonation today.
16. **Invitation binding (Phase 3).** The invitation token is single-use, expiring and hashed. The
    membership binds to whoever proves the invited, verified email, never through an email lookup.
17. **Guest and lead merge safety (Phase 4).** A guest trip is claimed only with the `guest_token`. A
    merge imports no unverified lead fields.
18. **Google Internal consent made mandatory (Open item 1).** It is the primary domain control and needs
    a Cloud Organization. A mapped `custom:hd` must not be client-writable. Spikes (c) and (d) were
    added.
19. **The staff email-code fallback is documented as bypassing Google 2SV (decision 4).**

Remaining open risks (not solved by this ADR):

- **Staff email-code fallback.** A compromised `@adventure.asia` mailbox signs in without 2SV. Plus risk
  detection reduces this risk but does not remove it. To remove it, drop the fallback and rely on
  break-glass.
- **Pre sign-up linking on the first Google sign-in is still unproven** (spike 3a/3d). Linking for a
  user who already signed in requires deleting the auto-created profile.
- **`hd` is not checked by Cognito itself** until the spike passes. Domain control then rests on the
  Internal consent screen and the pre-created directory user.
- **Cognito or trigger outage = total sign-in outage** for all three apps. Only the 30-day legacy flag
  (CIS staff) mitigates it during migration. After that there is no non-Cognito path.
- **The CIS API task role can create WORKFORCE users.** A CIS compromise can therefore add a staff user
  for any `@adventure.asia` address (not usable without that mailbox or Google account) and change
  groups, including granting `cis-admin` to an existing staff member. This is inherent while the
  directory lives in CIS. An alternative is a separate directory worker role.
- **The single NAT instance (t4g.nano)** is in the JWKS fetch path for CIS and Booking. The cache masks
  short outages only.
- **The SES sandbox exit in us-west-1 is an AWS-side approval** with no fixed time. It blocks every
  email-code phase.
