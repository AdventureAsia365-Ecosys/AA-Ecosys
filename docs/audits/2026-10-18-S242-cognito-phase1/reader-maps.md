# map:infra-identity

# Review of the Cognito WORKFORCE Terraform for Phase 1 (AA-854)

All three workforce clients are deployed. None of them has managed login branding yet, so the v2 sign-in pages cannot render, and this is the first blocker for Phase 1. The other gaps: the BFF has no stored client secret, the CIS task role cannot call Cognito, there are no Vercel preview callbacks, and the trigger accepts only one email domain. SES email receiving does work in us-west-1.

I ran only read-only AWS calls, all on 2026-10-18. I edited no files and ran no git write commands.

## 1. Workforce client settings
All three clients come from one `for_each` block (identity.tf:566-599). Their per-client values are in identity.tf:146-159.

| Setting | cis-admin | booking-staff | breakglass |
|---|---|---|---|
| Client secret | yes (:148) | yes (:152) | yes (:156) |
| Access / ID token | 15 min | 15 min | 15 min |
| Refresh token | 12 h | 12 h | 1 h |
| Identity providers | COGNITO only | COGNITO only | COGNITO only |

**Settings shared by all three:**
- **OAuth:** flow `code` only, user-pool OAuth on, scopes `openid email profile` (:572-574). There is no `aws.cognito.signin.user.admin` scope and no custom scope.
- **Auth flows:** `ALLOW_USER_AUTH` only (:575). There is no `ALLOW_REFRESH_TOKEN_AUTH`, because refresh-token rotation is ENABLED with a 60 s grace period (:588-591). Refresh must therefore go through `/oauth2/token` (:564).
- **Token units:** minutes / minutes / hours (:580-587).
- **`enable_token_revocation`:** true (:593).
- **`prevent_user_existence_errors`:** ENABLED (:594).
- **`auth_session_validity`:** 3 minutes (:595). This is the minimum, so an email code must be entered within 3 minutes. That matters for automated E2E email tests (point 5).
- **Attributes:** read `email, email_verified, name`, write `name` (:597-598).

**Callback and logout URLs.** These are the defaults in identity_variables.tf:136-168. terraform.tfvars does not override them (no `identity` key in that file).
- **cis-admin:**
  - Callbacks: `https://aa-cis.lumiguides.it.com/api/auth/callback/cognito` and `http://localhost:3000/api/auth/callback/cognito` (:144).
  - Logout: `https://aa-cis.lumiguides.it.com/login` and `http://localhost:3000/login` (:145).
- **breakglass:**
  - Callback: `https://aa-cis.lumiguides.it.com/api/auth/callback/cognito-breakglass` only (:148).
  - Logout: `https://aa-cis.lumiguides.it.com/login` (:149).
  - There is no localhost entry.
- **booking-staff:**
  - Callback: `http://localhost:3001/api/auth/callback/cognito` only (:152).
  - Logout: `http://localhost:3001/login` only (:153).

**Live client IDs (from `list-user-pool-clients`):**
- cis-admin: 3oqkumijh04cp81k3nlnub6qtv
- booking-staff: 5ifl9dgkr8a5outnmsjc8v1kt3
- breakglass: 2g3f3ncfuqdiuu1o5b70o4h0lq

## 2. Domains and managed login branding
- **Prefix domains** use `managed_login_version = 2`:
  - WORKFORCE: `aa365-staff-auth-dev` (identity.tf:647-651, identity_variables.tf:21-25).
  - EXTERNAL: `aa365-auth-dev` (identity.tf:653-657, identity_variables.tf:27-31).
- **Base URL:** `https://aa365-staff-auth-dev.auth.us-west-1.amazoncognito.com` (output at identity.tf:945-950).
- **Custom domains** `staff-auth.` and `auth.` are created only when `identity_custom_domains_enabled = true`, which defaults to false (identity.tf:659-673, identity_variables.tf:33-37). The us-east-1 certificate for them is `aws_acm_certificate.auth` (custom_domains.tf:65-78). Its validation step is gated by `custom_domains_enabled` (custom_domains.tf:108-114).
- **Branding is not managed by Terraform.**
  - The file says so deliberately (identity.tf:74-76).
  - The branding resource needs provider 6.12+, but the provider is pinned to `~> 5.40` (versions.tf:12), locked at 5.100.0.
  - The output `identity_branding_commands` prints one `create-managed-login-branding --use-cognito-provided-values` command per client (identity.tf:972-978).
  - Live check: `describe-managed-login-branding-by-client` returns **ResourceNotFoundException for all three WORKFORCE clients**.
  - **This blocks Phase 1: managed login v2 pages will not render until those commands are run.**
  - The CI apply role's `cognito-idp:Create*` grant would also cover this call (cicd_split.tf:640-652).

## 3. Groups in the tokens
- The pool uses pre token generation **V2_0** (identity.tf:388-395) on the Essentials plan (:338).
- The trigger returns `groupOverrideDetails.groupsToOverride` holding only the staff groups (workforce.py:101-105 and :120). `groupOverrideDetails` changes `cognito:groups` in **both the ID and the access token**.
- It also adds an `email` claim to the access token (workforce.py:119).
- Tests cover this:
  - Staff groups kept and email added (test_workforce.py:80-84).
  - Same rules on refresh (:88).
  - Terraform group list matches the trigger's default list (:124-132).
- The BFF and API get groups with no extra scope. A resource server is not needed for this.
- **Verifier notes (ADR 0006:300-310):**
  - Cognito access tokens carry `client_id`, not `aud`.
  - Check `token_use=access`.
  - CIS staff routes accept the pairs WORKFORCE × {cis-admin, breakglass}.

## 4. Missing for Phase 1
1. **Vercel preview callbacks:** none exist for cis-admin (identity_variables.tf:143-146). Cognito does not accept wildcard callback URLs, so we need a fixed preview alias added to `identity_client_urls`, or previews must sign in another way. localhost:3000 is already registered for cis-admin. breakglass has no localhost entry (:148).
2. **Resource server / custom scopes:** none exist. No `aws_cognito_resource_server` resource is in identity.tf, and scopes are fixed at :574. This is optional, because authorisation uses groups plus the issuer/client_id pairs.
3. **Client secret for the BFF:** not stored anywhere.
   - Terraform deliberately does not output it (identity.tf:911).
   - Live: no `aa-cis/dev/cognito*` secret exists. The only `aa-identity*` secret is the break-glass one.
   - Phase 1 must read it with `describe-user-pool-client` and put it in Vercel env, or in a new Secrets Manager secret.
4. **IAM for the staff directory:** missing.
   - The CIS task role (modules/ecs/main.tf:115-128) has no `cognito-idp` action. Its policies are main.tf:166-254 and :272-308, plus the SES send policy (ses.tf:210-214), the Bedrock/Cost Explorer assume-role policies and the PutMetricData policy (observability_ecosys.tf:453). The same holds for the Booking task role (booking.tf:228-260).
   - The workload boundary allows `*` except IAM writes and account/organization actions (cicd_split.tf:122-146), so an inline policy would work.
   - Needed actions: `cognito-idp:AdminCreateUser`, `AdminAddUserToGroup`, `AdminRemoveUserFromGroup`, `AdminDisableUser`, `AdminEnableUser`, `AdminUserGlobalSignOut`, `AdminGetUser`, `AdminListGroupsForUser`, `ListUsers` and `ListUsersInGroup`.
   - Scope the resource to the WORKFORCE pool ARN (`aws_cognito_user_pool.workforce.arn`).
   - The CI apply role intentionally has no `Admin*` actions (cicd_split.tf:637-639).
5. **Bootstrap script requirements:**
   - Every `AdminCreateUser` call must pass `MessageAction=SUPPRESS` (identity.tf:51-58).
   - It must set `email_verified=true`, or the pre token trigger denies the user (workforce.py:98-99).
   - Each user must be in at least one staff group (workforce.py:104-105).
   - Live: WORKFORCE currently has **0 users**.
   - **Still to test:** whether a user created with SUPPRESS (status FORCE_CHANGE_PASSWORD) can sign in with EMAIL_OTP through managed login.
6. **CIS task definition:** it still injects `ADMIN_SECRET` and `JWT_SECRET` (modules/ecs/main.tf:378-383 and :582). It has no Cognito issuer, client-id or JWKS env vars yet. The values are available as outputs (identity.tf:921-943).

## 5. SES email receiving for automated email-code tests
- **Feasible in us-west-1.** Live: `ses describe-active-receipt-rule-set` and `list-receipt-rule-sets` return exit 0 with `RuleSets: []`, and `inbound-smtp.us-west-1.amazonaws.com` resolves.
- The apex SES identity is already verified (identity_variables.tf:64, ses.tf:123-134), and the zone is in Route 53 (dns.tf:19-30). What would be needed:
  - An MX record on a **new** subdomain such as `e2e-mail.lumiguides.it.com`, pointing to `10 inbound-smtp.us-west-1.amazonaws.com`. `bounce.` is taken by the MAIL FROM MX (ses.tf:157-163), and the apex MX is Zoho (dns.tf:37-41).
  - A receipt rule set, its activation, and a rule that writes to S3 (bucket policy for `ses.amazonaws.com`).
  - CI apply role grants for `ses:*ReceiptRule*` and `ses:SetActiveReceiptRuleSet`. Today it has only identity and configuration-set actions (cicd_split.tf:598-604).
  - A cost quote before applying.
- **Trigger change needed:**
  - `ALLOWED_EMAIL_DOMAIN` is a single domain (identity.tf:180, workforce.py:38-42). Matching is a simple `endswith("@"+domain)` (common.py:66-67).
  - Add a Dev-only variable, e.g. `identity_test_email_domains` (default `[]`), and an env var `EXTRA_ALLOWED_EMAIL_DOMAINS` in `local.id_workforce_env`.
  - Use it in both `_pre_sign_up` (workforce.py:71) and `_pre_token_generation` (workforce.py:96).
  - Add a precondition that blocks it when the environment is not dev, plus tests.
  - The break-glass email precondition (identity.tf:402-405) can stay as it is.
- **Timing risk:** the 3-minute `auth_session_validity` (identity.tf:595) puts a ceiling on SES-to-S3 delivery latency plus polling time in a test.

## 6. Break-glass
- **Secret `aa-identity/dev/breakglass`:**
  - It is an empty container (identity.tf:779-784).
  - Its description says "password + TOTP seed" (:781). ADR 0006 says the same (lines 359-360).
  - **No JSON shape is defined anywhere.** A suggested shape is `{"username","password","totp_seed"}`, but this is not specified.
  - Live: `VersionIdsToStages` is null, so no value has been set.
- **Break-glass client flows:**
  - Same as the other clients: `code` plus `ALLOW_USER_AUTH`, with a secret (identity.tf:571-575).
  - PASSWORD is a pool-wide first factor (identity.tf:106, :373-375).
  - MFA is OPTIONAL with TOTP only (:359-362). After a PASSWORD first factor, Cognito sends the SOFTWARE_TOKEN_MFA challenge **only if TOTP is enrolled**, so the bootstrap must enrol TOTP.
  - Its tokens pass the pre token trigger like any staff user's: email in the domain, `email_verified`, and a staff group, with cis-admin and booking-admin per ADR (lines 357-358).
  - `identity_breakglass_email` defaults to `admin@adventure.asia` (identity_variables.tf:14-18). ADR line 357 suggests `breakglass@adventure.asia` or a dedicated mailbox.
  - Restricting break-glass to its own client is by procedure only (identity.tf:71-73). The token log records `client_id` (workforce.py:110-114).
- **Metric filter and alarms:**
  - Filter `aa-identity-dev-breakglass-token` on `/aws/lambda/aa-identity-dev-workforce-pre-token`, pattern `{ $.event = "breakglass_token_issued" }`. It produces metric `AA/Identity` / `BreakglassTokenIssued` (identity.tf:878-890).
  - Alarm `aa-identity-dev-breakglass-token-issued`: period 60 s, threshold ≥ 1, ALARM and OK actions to `aws_sns_topic.alerts` (identity.tf:892-906).
  - Related alarm `aa-identity-dev-trigger-unexpected-error` (identity.tf:808-822).
  - The ADR's "secret retrieval alerted (CloudTrail → email)" (lines 359-360) is **not implemented** in these files.


# map:booking

## AA-Booking staff auth map: Phase 2 readiness (read-only, nothing changed)

### 1. How Booking verifies staff tokens today (CIS bridge)

- **Module:** `backend/app/auth/tokens.py`. The contract is in its docstring at lines 1-11: RS256, `kid` header, `iss` = CIS base URL, `aud=booking`, 15-minute expiry, `sub` = CIS `shared.admin_users.id`, claims `email`, `name`, `cis_role`.
- **Constants:** `AUDIENCE="booking"` (tokens.py:28), `ALGORITHM="RS256"` (:29), JWKS TTL 600 s (:32), unknown-`kid` refetch at most every 30 s (:33), leeway 30 s (:35), JWKS body capped at 256 KB (:36).
- **`JwksCache`** (tokens.py:89-129) holds **one** key set. A failed fetch keeps the last good keys (:111-113). With no keys at all it raises `AuthUnavailable`, which becomes HTTP 503 (:125-126). An unknown `kid` raises `InvalidToken`, which becomes 401 (:127-128). `_rsa_keys` keeps only RSA keys with `use=sig` and `alg=RS256` (:74-86). Cognito's JWKS fits this filter.
- **`StaffTokenVerifier`** (tokens.py:132-172) takes **one** issuer and **one** audience (:133-136):
  - It checks the header alg is RS256 (:143) and that a `kid` is present (:145-147).
  - It decodes with `audience=self._audience`, `issuer=self._issuer` and `require=["exp","iss","aud","sub"]` (:150-158).
  - It requires a non-empty `cis_role` claim (:165-166) and `sub` ≤ 128 characters (:163).
  - It returns `StaffClaims(sub, email, name, cis_role)` (:49-54, :167-172).
  - It does not check `token_use` or `client_id`.
- **Bridge issuer (CIS side):**
  - Constants `BOOKING_JWT_ISSUER="https://api-cis.lumiguides.it.com"`, audience `booking`, TTL 900 s are in `apps/AA-CIS-App/api/core/booking_jwt.py:45-48`.
  - The claims are built at booking_jwt.py:192-203: `sub`=admin id, `name`=username, `preferred_username`, `cis_role`, `jti`. **There is no `email` claim.**
  - The key comes from Secrets Manager `aa-cis/dev/booking-jwt-signing-key` (booking_jwt.py:7-13, :49). Its `kid` is `bk-2026-10` according to ADR 0006 :288.
  - Endpoints: `POST /auth/booking-token` (AA-CIS-App `api/main.py:390-417`) re-reads `shared.admin_users WHERE is_active` on every mint (main.py:373-387). `GET /auth/.well-known/jwks.json` is at main.py:420.
- **Verifier config** (`backend/app/settings.py`):
  - `CIS_JWKS_URL` (documented at :14-15) defaults to `https://api-cis.lumiguides.it.com/auth/.well-known/jwks.json` (:45-46, :62, :118).
  - `STAFF_JWT_ISSUER` (documented at :16-17) defaults to `https://api-cis.lumiguides.it.com` (:63, :119).
  - Both must be `https://` outside test and local (:83-92).
  - These are scalars: there is **no issuer list and no audience or client_id setting**.
- **Wiring:** `create_app` builds one `StaffTokenVerifier(JwksCache(http_fetcher(settings.cis_jwks_url)), settings.staff_jwt_issuer)` (main.py:60) and stores it in `app.state.staff_verifier` (main.py:104).
- **Infra:** the ECS task does not set `CIS_JWKS_URL` or `STAFF_JWT_ISSUER`, so the code defaults apply (`infra/AA-CIS-Infra/accounts/aa365/booking.tf:295-304`). The API GW methods use `authorization = "NONE"` and the app authenticates (booking.tf:474, :492).

### 2. `booking.staff_users` and roles

- **DDL:** `migrations/003_staff_trip_case_workflow.sql:39-62`.
  - `cis_user_id TEXT PRIMARY KEY` (= CIS `admin_users.id` = JWT `sub`), plus `email`, `name`, `role NOT NULL`, `active DEFAULT false`, `cis_role`, `last_seen_at`.
  - CHECK on role: `admin`/`sales`/`contracting`/`content_creator` (:51).
  - `preferences JSONB` was added by bk-005 (`migrations/005_w1_extras.sql:267-268`).
  - There is no Postgres enum `staff_role`. Role is a TEXT column with a CHECK.
- **About 27 FKs point at `staff_users(cis_user_id)`:** 4 in 003, 4 in 005, 3 in 004, 6 in 008, 2 in 009, 8 in 010 (count from `grep -c`). On top of that:
  - `policy_approvals.approved_by` is TEXT without an FK (`007_policy_approvals.sql:19`, :43).
  - `audit_logs.actor_ref` stores the CIS id (003:30-31).
  - `cis_user_id` appears 178 times in `backend/app` and 33 times in the frontend.
- **Provisioning** (`backend/app/auth/staff.py:281-325`): `INSERT … ON CONFLICT (cis_user_id)`.
  - The first token maps `cis_role` to a Booking role through `ROLE_FROM_CIS` (staff.py:207-209): admin→admin (active), reviewer→sales (inactive), content→content_creator (inactive).
  - Later tokens refresh email, name and `cis_role`, but never role or active.
  - An unknown `cis_role` gets 403 `unknown_cis_role` (staff.py:346-348). An inactive row gets 403 `staff_inactive` (:352-353).
- **Role source of truth:** today it is `booking.staff_users.role`, edited by a Booking admin through `PATCH /booking/staff/{cis_user_id}` (`routers/staff.py:80-88` → `auth/admin.py:391-430`, with a guard against demoting yourself at :403-404).

### 3. Role checks per route

- **Permission matrix** in `PERMISSIONS` (staff.py:211-235), with `Staff.can` = active AND role in the permission's set (:261-262), and `require(permission)` (:357-366).
- **Routes and permissions:**

| Router | Permissions |
|---|---|
| `trip_cases.py:26-29` | trip_case.read / write / assign, version.write |
| `customers.py:19-21` | customer.read / write / admin |
| `pricing.py:36-38` | pricing.read / write |
| `supply.py:29-30`, `suppliers.py:26-27` | supply.read / write |
| `catalog.py:38-40` | catalog.read, trip_plan.write, trip_case.write |
| `staff.py:18-20` | staff.admin, staff.directory |
| `reference.py:19` | audit.read |
| `retention.py:28` | retention.admin |

- `/staff/me*` and the notifications routes only need `current_staff` (`routers/staff.py:19`, :37-51).
- **Frontend page rules** (display only) are in `frontend/lib/rbac.ts:9-60`.

### 4. How the staff frontend logs in today

- **Sign-in** (`frontend/app/api/auth/login/route.ts:27-90`): the BFF posts username and password to CIS `POST /auth/admin-login` (:46-65) and gets a 24 h HS256 CIS session. It swaps that for the bridge token at `POST /auth/booking-token` (:68-77, `lib/session.ts:66-92`). It then calls `/booking/staff/me` (:80). The result goes into two httpOnly cookies, `bk_cis_session` and `bk_access` (:88-89, session.ts:13-16).
- **Page gate** (`frontend/proxy.ts`): no `bk_cis_session` cookie sends the user to `/login` (:167-168). The bridge token is re-minted when it has under 2 minutes left (:170-181).
- **BFF proxy** (`app/api/booking/[...path]/route.ts`): requires `bk_cis_session` (:162-163). It re-mints before a call when needed (:181-184) and once more after an upstream 401 (:210-214), then forwards `Authorization: Bearer <bk_access>` (:196-198). Logout clears both cookies (`app/api/auth/logout/route.ts:107-110`).
- **Config:** `CIS_API_URL` defaults to the Dev CIS (`lib/config.ts:113-116`). A "Continue with Google" button exists but is empty: `NEXT_PUBLIC_GOOGLE_SIGNIN_URL` (config.ts:125-126, `LoginForm.tsx:111-119`).
- There is no OAuth / PKCE / callback route in the frontend today.

### 5. Tests

- **Helper:** `backend/tests/staff_tokens.py:13-60`. `LocalCis` holds a local RSA key, serves its JWKS and mints tokens with `cis_role`. Its `verifier()` uses a single issuer (:59-60).
- **`tests/unit/test_staff_tokens.py`**: 14 tests (:27-186). `test_rejected_tokens` (:40-60) covers aud, iss, expired, no `cis_role`, empty and long sub, no `kid`, unknown `kid`.
- **`tests/unit/test_staff_auth.py`**: 17 tests (:65-240) covering provisioning, inactive, 403, admin patch.
- **`tests/unit/test_settings.py:56-68`**: auth URL defaults and https checks.
- **8 integration test files** build tokens with `LocalCis` (bk003, bk004, bk005, bk007_policy, bk008_suppliers, bk010_supply, bk012_retention, aa679).
- **The frontend has no tests** (no `*.test.*` or `*.spec.*` files, no test script in `package.json`).

### 6. Can Booking accept Cognito WORKFORCE tokens by config only? **No.** One code change is needed first.

Today's blockers:
1. Only one issuer and one JWKS can be configured (tokens.py:133-136; settings.py:62-63; main.py:60). ADR 0006 §8 rules 2 and 8 (:297-299, :314-315) require choosing the issuer entry by the unverified `iss`, with JWKS kept per issuer.
2. **Cognito access tokens have no `aud`.** The audience is in `client_id` and `token_use=access` (ADR 0006 :289-291). The decode at tokens.py:150-158 requires `aud` and checks it equals `booking`, so every Cognito access token would fail with 401.
3. A `cis_role` claim is mandatory (tokens.py:165-166), and roles come from `ROLE_FROM_CIS` (staff.py:208, :346-348). Cognito carries roles in `cognito:groups`.
   - The workforce pre-token trigger keeps every staff group and refuses a token only when the user has none (`lambda_src/identity_triggers/workforce.py:101-105`).
   - So a user holding only `cis-*` groups still gets a valid WORKFORCE token. Booking must require a `booking-*` group, and the ADR also requires a `(issuer, client_id)` allow-list per route class (ADR :306-310).
4. The Cognito access token has no `name`. The trigger adds only `email` (workforce.py:116-121). `name` would come from the DB or the ID token.
5. **Identity key.** `staff_users.cis_user_id` = `admin_users.id`, but a Cognito `sub` is a different UUID. ADR 0006 :126-127 and :332 say "keyed by `(iss, sub)`" and "no role column, roles from `cognito:groups`", while the Phase 1 table (:390) puts a Booking role column on `shared.admin_users`. With about 27 FKs on `cis_user_id`, changing the key is a large migration. The cheaper path:
   - Keep `cis_user_id` as the internal primary key.
   - Add `identity_iss` and `identity_sub` columns with a unique pair (new migration bk-014).
   - Link existing rows to their Cognito identity. Linking by email does not work: bridge tokens carry no `email` (booking_jwt.py:192-203), so bridge-provisioned rows probably have NULL email. The link has to come from CIS `admin_users.cognito_sub` (filled in Phase 1), either through a read grant/view owned by CIS or through a Booking admin backfill. The `booking` DB role has no access outside schema `booking` (001_booking_foundation.sql:28-35).
6. **Role source of truth** is undecided: `booking.staff_users.role` (Booking admin edits it today) or Cognito groups written by the AA-816 directory. The current `PATCH /booking/staff` would conflict with the directory.

What one code change would need to contain (after it, adding and removing issuers is config only):
- **Verifier:** multi-issuer. Read env as a JSON list, for example `STAFF_ISSUERS=[{iss, jwks_url, kind: bridge|cognito, audiences|client_ids}]`. The scalar `CIS_JWKS_URL` / `STAFF_JWT_ISSUER` stay as a fallback.
  - Choose the entry by the unverified `iss` and keep one `JwksCache` per issuer.
  - For Cognito entries: `token_use=="access"`, `client_id` in the allow-list, skip `aud`.
  - Return a Principal `(iss, sub, client_id, groups, email)`.
- **`current_staff`:** take the role from the `booking-*` groups when the issuer is Cognito; keep `cis_role` for the bridge. Look up or provision by `(iss, sub)`.
- **Allowed clients:** `aa-workforce-dev-booking-staff`, `aa-workforce-dev-cis-admin` (3oqkumijh04cp81k3nlnub6qtv) and `aa-workforce-dev-breakglass`. Cognito issuer `https://cognito-idp.us-west-1.amazonaws.com/us-west-1_bCcFvbSOS`; take the value from the Terraform output or the pool's openid-configuration, never hand-built (ADR :287).
- **Infra:** add the issuer env to the Booking task definition (booking.tf:295-302). Change the `booking-staff` callback/logout URLs from `http://localhost:3001/...` (`identity_variables.tf:151-153`) to the real host, e.g. `https://aa-booking-admin.vercel.app/api/auth/callback/cognito`.
- **Frontend:** BFF auth code + PKCE flow with a new callback route and the client secret held server-side. Replace `bk_cis_session` minting with the Cognito refresh token rotated through `/oauth2/token` (rotation is on: identity.tf:588-591). Rewrite `proxy.ts` (:167-181), the BFF proxy (:162-214), login and logout. ⚠️ This adds env vars with underscores (client id / secret / domain), which must be edited by hand in VSCode or Vercel, not auto-generated.
- **Tests:** add a second local issuer (Cognito-shaped access token: `client_id`, `token_use`, `cognito:groups`, no `aud`) and cross-issuer `kid` rejection tests. The existing 14 + 17 unit tests and 8 integration files keep working while the bridge stays.

### 7. Same session as Phase 1? Small or large?

- **Full Phase 2 is LARGE. Do not do it in the same session as Phase 1.**
  - It depends on Phase 1 outputs: WORKFORCE users exist with `booking-*` groups, `admin_users.cognito_sub` is filled, and the role-source decision is made (ADR :391 lists Phase 1 as the prerequisite).
  - It spans backend verifier + migration bk-014 + linking backfill, the whole frontend auth flow, Terraform callback URLs, Vercel env, and the Booking task definition.
  - Bridge removal must wait one release with both issuers (ADR :391, :399).
- **The backend dual-issuer verifier alone is SMALL to MEDIUM** (one PR, roughly 300-400 lines with tests, touching tokens.py, settings.py, main.py:60, staff.py:335-354 and the tests). It can follow Phase 1 in the same session if time allows, as long as Cognito identities resolve only to already-linked rows (no auto-provision until the key and role decision is made). It only becomes useful once a client actually sends Cognito tokens to Booking (the CIS admin calling the Booking API with the `cis-admin` client, or the Booking frontend rewrite).

### 8. Repo discrepancies to raise

- ADR 0006 :126-127 says `booking.staff_users` has no role column. bk-003 has one (`003_staff_trip_case_workflow.sql:43`), and Booking admins edit it (admin.py:391-430).
- AA-Booking `CONTEXT.md:39-40` and :139 describe only the bridge. They need an update when Phase 2 lands.
- `identity_variables.tf:151-153` still points `booking-staff` at localhost:3001, while Booking `settings.py:28-29` / :48 already treat `https://aa-booking-admin.vercel.app` as the staff admin URL.


# map:docs-tests

# ADR 0006 Phase 1 (CIS staff on Cognito WORKFORCE): requirements, verifier rules, lifetimes, revocation, open items, lessons

I read every listed doc, plus `identity.tf`, the workforce trigger, the S241 session log and the S241 decisions log to check facts. Nothing was edited and no AWS calls were made.

Path shorthand used below (all under `/home/nghiep/projects/AA-Ecosys/`):
- **ADR** = `docs/adr/0006-ecosystem-identity.md`
- **RES** = `docs/research/2026-10-14-cognito-identity.md`
- **CTX** = `apps/AA-CIS-App/CONTEXT.md`
- **ARCH** = `docs/ecosystem-architecture.md`
- **LES** = `skill/aa-lessons/lessons.md`
- **AC** = `docs/audits/2026-10-17-S241-admin-console/README.md`
- **SDLC** = `docs/audits/2026-10-17-S241-sdlc-review/README.md`
- **UR** = `docs/audits/2026-10-17-S241-sdlc-review/unified-roadmap.md`
- **API** = `docs/audits/2026-10-17-S241-sdlc-review/areas/api.md`
- **ESI** = `docs/audits/2026-10-17-S241-sdlc-review/areas/environments-secrets-iam.md`
- **DEC** = `docs/sessions/2026-10-17-S241-decisions.md`
- **SLOG** = `docs/sessions/2026-10-17-S241-sdlc-admin-console-x1-security.md`
- **TF** = `infra/AA-CIS-Infra/accounts/aa365/identity.tf`
- **TFV** = `infra/AA-CIS-Infra/accounts/aa365/identity_variables.tf`
- **WF** = `infra/AA-CIS-Infra/accounts/aa365/lambda_src/identity_triggers/workforce.py`
- **CICD** = `infra/AA-CIS-Infra/accounts/aa365/cicd_split.tf`

---

## 1. Phase 1 checklist

### Dependencies
- [ ] Phase 0 applied: green plan/apply, a test staff user signs in, and a user with no group is denied (ADR:389). Per SLOG:67-70 it is applied: pool us-west-1_bCcFvbSOS, 7 groups, 4 triggers, 14 alarms.
- [ ] AA-811 SES is live. Email codes need it; ADR says it blocks the email-code part of Phase 1 (ADR:390, :397, :340-343; RES:29, :168).
  - TF:33-36 says SES has been on by default since AA-854: identity verified, DKIM SUCCESS, out of sandbox, checked live 17/10.
  - Staff sign-in is email code only: Google was dropped in the S236 amendment and there is no IdP on WORKFORCE (ADR:3, :461; TF:22-25).
  - The ADR body still describes Google in decision 4 (ADR:154) and decision 5 pre sign-up (ADR:179-194). UR:166 flags that this needs cleaning up.

### Scope (ADR:390, :106-128)
- [ ] **CIS migration** (CIS-owned, goes through DB Migrate with a byte-identical copy in Infra; ADR:108, :400):
  - Add to `shared.admin_users`: `email` (unique, lower-cased, `@adventure.asia`), `display_name`, `cognito_sub` plus the issuer, and the Booking role storage.
  - `password_hash` becomes nullable (ADR:106-108, :332).
  - Identity key is `(iss, sub)`, never `sub` alone (ADR:323-325, :332).
  - S241 additions to the same migration: `last_login_at` and `is_owner boolean NOT NULL DEFAULT false` (AC:243). Today the table has only `id`, `username`, `role`, `is_active`, `created_at`, `updated_at` (AC:242).
- [ ] **CIS admin UI** signs in through the `cis-admin` client: authorization code + PKCE, confidential, client secret held by the BFF (ADR:73, :390).
  - The client allows `ALLOW_USER_AUTH` only, with refresh-token rotation (ADR:79-84; TF:575, :588-590).
  - Refresh goes through `/oauth2/token` with `grant_type=refresh_token`, or `GetTokensFromRefreshToken`. `REFRESH_TOKEN_AUTH` must not be used (ADR:80-82, :511-513).
  - Scopes are `openid email profile` (ADR:85-89; TF:574). Client secrets are not Terraform outputs; read them with `describe-user-pool-client` (TF:909).
  - Registered callback: `https://aa-cis.lumiguides.it.com/api/auth/callback/cognito` plus localhost. The breakglass callback is `/api/auth/callback/cognito-breakglass` (TFV:144-149).
- [ ] **CIS API verifier** accepts Cognito access tokens through JWKS (§2 below; ADR:390, :280-319).
- [ ] **Staff routes authorise from `cognito:groups`.** `cis-admin`, `cis-reviewer` and `cis-content` map to `admin_role` values `admin`, `reviewer` and `content` (ADR:101-104, :390).
  - Authorisation never rests on the group claim alone: the route class's `(issuer, client_id)` pair must also match (ADR:306-310).
  - Plug into the existing AA-882 `staff_policy`, which is keyed by (method, route) and already re-reads role and `is_active` (SLOG:60-61; AC:213).
- [ ] **Staff directory UI (AA-816) writes the DB row first, then Cognito.**
  - Calls: `AdminCreateUser`, `AdminAddUserToGroup`, `AdminRemoveUserFromGroup`, `AdminDisableUser` (ADR:109-115).
  - Reject any email that is not `@adventure.asia` (ADR:124-125).
  - Every `AdminCreateUser` **must** pass `MessageAction=SUPPRESS`. Otherwise Cognito mails a temporary password, and that person could set a password and sign in without an email code (TF:47-60).
  - Set `email_verified=true` (RES:123). Otherwise the pre token trigger denies with "email not verified" (WF:98-99).
  - `staff.write` (changing role or active) is limited to owners: Nghiệp and break-glass (AC:202; DEC:31).
- [ ] **Reconcile job** (`shared.job` kind), daily and on demand. It only reports drift; it never creates, enables or re-groups a user. It uses `ListUsers` / `ListUsersInGroup`, never `AdminGetUser`, which counts as MAU (ADR:111-115, :445).
- [ ] **CIS task role IAM** gets an explicit allow-list on the WORKFORCE pool ARN (ADR:116-123):
  - Allowed: `AdminCreateUser`, `AdminAddUserToGroup`, `AdminRemoveUserFromGroup`, `AdminDisableUser`, `AdminEnableUser`, `AdminUserGlobalSignOut`, `ListUsers`, `ListUsersInGroup`.
  - Never: `AdminSetUserPassword`, `AdminUpdateUserAttributes`, `AdminLinkProviderForUser`, `Admin*Auth`, `AdminDeleteUser`.
  - This grant does not exist in Terraform yet. The only Cognito grants are the CI control-plane role (CICD:638-647) and the trigger role (TF:285). It needs an Infra PR.
- [ ] **Bootstrap script for the first two users** (Nghiệp + break-glass), because the directory UI itself needs a signed-in admin (ADR:390).
  - The break-glass user is deliberately not in Terraform (TF:75-76).
  - Remaining break-glass steps (SLOG:119-122): `AdminCreateUser` with SUPPRESS, add to `cis-admin` and `booking-admin`, then disable. Nghiệp sets the secret value himself.
  - Break-glass email is set to `admin@adventure.asia` (DEC:41).

### Preconditions before switching anything off (ADR:390)
- [ ] Every active `admin_users` row has an `@adventure.asia` email.
- [ ] Every active row has a `cognito_sub` filled by **that person's own successful Cognito sign-in**.
- [ ] Break-glass sign-in has been tested end to end.

### Cutover (ADR:390, :559-563; AC:235-238)
- [ ] Set `LEGACY_ADMIN_LOGIN_ENABLED=false`. Do not delete anything: the code and `password_hash` stay for 30 days as the rollback path.
- [ ] The BFF stops sending `X-Admin-Secret`.
- [ ] **Rotate** `ADMIN_SECRET`. The old value grants full admin plus tenant impersonation through `verify_tenant_api_key`.
  - The new value stays for docs/ops only (ADR:390). In practice that means the machine principal: CI deploy-gate/smoke and the Lambda scheduler (AC:219-227).
  - The secret currently lives in 5–6 places: Secrets Manager, ECS api and worker, Vercel prod and preview, GitHub, and the Lambda env in plaintext at `dfs_balance.tf:161` (SDLC:369; UR:195).
- [ ] The new tokens carry no `cis_role`. Today Booking derives its role from `claims.cis_role` (`ROLE_FROM_CIS`), and the CIS middleware sends a null role back to `/login`. Keep the CIS `role NOT NULL` until Cognito replaces this (AC:248; DEC:33). The Booking verifier switch itself is Phase 2 (ADR:391).

---

## 2. Verifier rules the CIS API must implement (ADR decision 8, ADR:280-319)

**One module, configured per issuer.** Settings per issuer: `iss`, JWKS URL, audience claim, allowed audiences, `token_use`, roles claim. The Cognito profile is: `aud` claim = `client_id`, `token_use=access`, roles from `cognito:groups`. The bridge profile is: `aud=booking`, `token_use` not checked, roles from `role` (ADR:285-292).

**Issuer selection**
- Take the issuer from Terraform output or from the pool's `openid-configuration`. Never use the custom domain and never build it by hand (ADR:287). Note the updated-issuer form `issuer-cognito-idp…`.
- TF outputs `https://${endpoint}` (TF:921-935) and says to check it against `/.well-known/openid-configuration` after apply (TF:907-908).
- Pick the issuer entry from the **unverified `iss`**, then use **only that issuer's** JWKS. Never look up a `kid` across issuers. Unknown `iss` → 401 (ADR:297-299).

**Algorithm and headers**
- RS256 only. Reject `none`, `HS*` and anything else. Ignore `jku`, `x5u` and `jwk` headers (ADR:296).

**aud vs client_id**
- A Cognito access token has **no `aud`**; check `client_id` against the allow-list (RES:222; ADR:289, :303-304).
- `aud` appears only with resource binding (RES:223), which the first version does not use (ADR:318-319).
- A V2 pre token trigger can add `aud`, but only with the current client ID as value (RES:109).

**token_use**
- Must equal `access`. APIs accept access tokens only; ID tokens are for the UI (ADR:291, :303, :305).

**Other claims**
- Check signature, `exp` with at most 60 s leeway, `iss`, `token_use` and audience (ADR:303-304).

**Accepted (issuer, client_id) pairs per route class**
- CIS staff routes accept WORKFORCE × {`cis-admin`, `breakglass`} (ADR:306-310).
- TF:72-74 says break-glass is limited to its own client only by procedure. The trigger cannot see client ids, so a break-glass token could arrive via `cis-admin`.

**JWKS caching and refetch**
- Cache keys by `kid`, separately per issuer.
- On an unknown `kid`, refetch at most once per minute.
- **Keep the last good key set** if a refetch fails.
- Fetch keys at start-up, because the JWKS is reached through the single t4g.nano NAT instance, and a NAT blip must not become a sign-in outage (ADR:300-302, :588-589).
- The existing Booking JWKS contract does the same: refetch once at most every 60 s (CTX:489-491).

**Principal and authorisation**
- The verifier returns a `Principal` with `issuer`, `sub`, `client_id`, `groups`, `email` and `email_verified`. Authorisation comes after verification and is the app's job (ADR:311-313).
- The WORKFORCE trigger injects only `email` into the access token, not `email_verified` (WF:119).

**Coexistence and code reuse**
- Several issuers can be configured at once, so the switch is done by configuration (ADR:314-315).
- Copy the module byte-identical into each repo, with the same tests (ADR:316-317).

**Gap in the reference implementation:** RES:237-249 is single-issuer, uses `PyJWKClient(lifespan=3600)` and has no last-good fallback and no once-per-minute refetch limit. It does **not** meet rules 2 and 3, even though ADR:316 calls it the reference.

---

## 3. Token lifetimes per client (ADR:262-278; matches TF:148-171)

| Client | Access + ID token | Refresh token |
|---|---|---|
| `cis-admin`, `booking-staff` | 15 min | 12 h, rotation on |
| `breakglass` | 15 min | 1 h (the minimum) |
| `cis-portal` | 30 min | 7 days |
| `booking-customer`, `tripplanner` | 60 min | 30 days |

- Rotation does not extend the refresh window, so staff sign in again at least once a working day (ADR:273-274).
- APIs never call Cognito per request (ADR:271).
- Rotation grace period is 60 s, and token revocation is enabled (TF:590, :593).
- Break-glass needs its own client because lifetimes are set per client, not per user (ADR:267, :90-91).

---

## 4. Logout and revocation rules

- **Offboarding order:** `AdminDisableUser` first, then `AdminUserGlobalSignOut`.
  - The managed-login session cookie lasts 1 h and global sign-out does not clear it. Access tokens shorter than 1 h do not stop silent re-sign-in within that hour.
  - A disabled user cannot re-authenticate, even with the cookie. Worst case is one live access token for 15 min (ADR:275-278, :266, :557-558).
- Revocation cannot be detected offline, which is why access tokens stay short (ADR:271; RES:232).
- Disabled users never reach the pre token trigger, because Cognito refuses them first (ADR:198-199).
- The trigger runs on every token issue, refresh included. It denies when the user has no staff group or the email is outside `@adventure.asia` (ADR:196-205; WF:97-105).
- Break-glass stays disabled between uses. Enabling it needs AWS admin with MFA (ADR:366-367).

---

## 5. Open items still undecided or in conflict

1. **The ADR 0006 amendment has not been written.**
   - Q3 chose a grant table, `shared.staff_app_grant` (person, app, role) (DEC:32; AC:244, :419). The ADR still says per-app role columns (ADR:106-107, :390).
   - Q2 chose owner-only `staff.write` (DEC:31), with a Cognito group `platform-admin` proposed (AC:418). That group is not in the ADR group table (ADR:101-104). The trigger would strip it (ADR:200; WF:101), so adding it also needs an Infra change.
   - The planned amendment PR is listed at AC:344.
2. **Identity clash:** break-glass email = `admin@adventure.asia` (DEC:41), but Nghiệp is the other bootstrap user (ADR:390). Nghiệp's own WORKFORCE user needs a different `@adventure.asia` mailbox. This is not decided anywhere.
3. **How break-glass gets its password and TOTP is undefined.** SUPPRESS leaves only a temporary password (TF:47-60), and `AdminSetUserPassword` is banned only for the CIS task role (ADR:119). The procedure for the AWS-admin bootstrap script and TOTP enrolment (it must be enabled to enrol, then disabled again) is unwritten.
4. **E2E / UI-smoke login under Cognito is unresolved.**
   - Today ui-smoke and Kiro use username/password secrets and `ADMIN_SECRET` (SDLC:683, :708; ESI:13). Vercel also holds `ADMIN_USERNAME/PASSWORD` and `ADMIN2_*`.
   - Email codes need a mailbox, so turning legacy login off breaks smoke unless an E2E path exists.
   - ADR:390's precondition (every active row has a Cognito-signed-in sub) also covers E2E rows. The audits only recommend "Cognito users with MFA instead of env logins" (ESI:103; `areas/adlc-standards.md:126`).
5. **Vercel preview callback URLs are not registered.** Only production and localhost are (TFV:144-145), so Cognito login cannot be verified on a preview.
   - AA-885, splitting the tenant portal onto its own domain, will also change the `cis-portal` callbacks (TFV:156-157; DEC:37).
6. **The rotated `ADMIN_SECRET` stays as the machine principal** (ADR:390; AC:233-234). Removing it is "a later issue" with no number.
7. **WAF on the pools is off.** It is billable and needs a quote and approval (TF:39-40; DEC:34, :41). Not required for Phase 1, which has no self sign-up.
8. **Plus tier for WORKFORCE: "later"** (ADR:464, :500).
9. **Staff email-code fallback risk** (no 2SV) is accepted, but mailbox-forwarding policy is an open item (ADR:162-165, :575-577).
10. **CTX is stale versus S241.**
    - CTX:463-466 still says backend roles are not narrowed and that `content_creator` maps to `content`. AC:389 says this is wrong, and AA-882 `staff_policy` has since shipped.
    - ARCH:226 still describes "admin secret added by the BFF".
    - Both need updating with Phase 1 (session-workflow rule: CONTEXT.md is updated in the same session as the change).

---

## 6. Lessons that apply (LES)

**Before building**
- LES:8 — Check premises against real data first: count active `admin_users` rows and which have mailboxes before planning the cutover.
- LES:11 — Read the issue's own implementation notes before "fixing" towards Done-when.
- LES:14 — "Role applied" ≠ "role usable": after adding Cognito IAM to the CIS task role, probe it once from inside the container.
- LES:56 — Probe with each app's own role before applying a change.
- LES:15 — `scripts/` is gitignored: the bootstrap script must be `git add -f`, then confirmed with `git ls-files`. `create_staff_user.py` was lost exactly this way.
- LES:17 — Workflow agent prompts must say "only this task".

**Verify and Done**
- LES:27 — Claim "works" only per channel actually tested live end to end, with evidence.
- LES:30 — Read Done-when before moving an issue to Done.
- LES:34 — Verify on the real domain.
- LES:29 — UI scripts wait for server state, not for transient toasts.
- LES:31 — New SQL needs an integration test on real Postgres.
- LES:43 — Confirm the migration is actually applied in the test DB.
- LES:32 — Grep every caller when a signature changes, including the `role` / `x-admin-role` callers.

**Migrations and deploy**
- LES:133 — Ship the Infra migration copy at once, or Copy Guard turns red.
- LES:57-58 — No backend deploy while `shared.job` has queued/running jobs, including recompute.
- LES:61 — A new top-level module needs a Dockerfile `COPY` and a `deploy-dev.yml` path filter.
- LES:63 — Merge backend PRs one after another.
- LES:62 — Commits use `Refs`.

**Terraform and secrets**
- LES:65 — Apply only from merged `main`.
- LES:67 — Use the safe `export-credentials` form.
- LES:73 — Check that the apply role has permission on the exact ARN.
- LES:74 — Scope `ADMIN_SECRET` to an environment and delete orphan repo secrets.
- LES:46 — WAF logs must redact `Authorization` and `X-Admin-Secret`. API:48 says they already do.
- LES:51 / LES:77 — ECS exec output is cut off silently: return bootstrap-script output through S3, or use a one-off task.

**Frontend and Vercel**
- LES:52 — New env vars must be ticked for Preview.
- LES:69 — Vercel Hobby allows about 100 deploys per day; rotating `ADMIN_SECRET` and adding new env needs a redeploy, so do it early in the day.
- LES:138-140 — Playwright timeouts, selectors, and run the CI workflow for real once.
- LES:146-147 — Next 16 compiler lint, and always run the full `npm run build`.
- LES:145 — In FastAPI, no helper between the decorator and the function.
- LES:148 — **⚠️ This contains underscore env vars — edit manually in VSCode:** `LEGACY_ADMIN_LOGIN_ENABLED`, `ADMIN_SECRET` and the Cognito client id/secret env vars must be set by Nghiệp by hand, never by a generated script. The global CLAUDE.md "ENV VAR CORRUPTION" rule says the same.


# map:cis-frontend

# CIS admin frontend auth: map and Phase 1 change list

Read-only. I edited no files, ran no git writes and made no AWS calls. Repo HEAD is `cafd13a8`. Paths are relative to `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/frontend` unless shown in full.

## 1. Stack
- **Next.js and React:** `next 16.2.4`, `react 19.2.4` (`package.json:17-19`).
- **Auth libraries:** none. There is no next-auth, jose, openid-client or aws-amplify (`package.json:11-22`). Everything is hand-written fetch plus cookies.
- **Middleware:** it is `middleware.ts`, an Edge-safe file. `lib/rbac.ts:12` says so explicitly. Next 16 prefers the name `proxy.ts`; `middleware.ts` still works.
- **Deploys:** the Vercel Git integration is off (`vercel.json:3-5`). Previews and production are deployed by `.github/workflows/vercel-deploy.yml:128-145`. Each preview gets a random `*.vercel.app` URL behind Vercel SSO.

## 2. Current auth map

### Admin login
- **Page:** `app/login/page.tsx:26-30` POSTs `{username, password}` to `/api/auth/login`. After that, the browser sets two **non-httpOnly** display cookies itself: `cis_role` and `cis_user` (`:43-44`). It then does a full navigation to `/admin/dashboard` (`:64`), and middleware redirects that to the role's landing page (`middleware.ts:68-72`).
- **Login route:** `app/api/auth/login/route.ts:45-50` calls backend `POST /auth/admin-login`. The backend checks a bcrypt hash in `shared.admin_users` and returns an HS256 JWT (`api/main.py:307-337`).
- **Session cookie** is set at `route.ts:75-81`:
  - name `cis_admin_token`, value = the raw HS256 JWT
  - `httpOnly`, `secure` only when NODE_ENV is production, `sameSite=lax`, `path=/`
  - `maxAge` 24h
  - the JSON body carries only role, name and admin_id, never the token (`:66-70`)

### Middleware (page gating)
- **Matcher:** `/admin/:path*`, `/portal/:path*`, `/login`, `/tenant-login` (`middleware.ts:212-219`). `/api/**` is **not** matched, so every BFF route checks auth itself.
- **Public paths:** `/login` and `/tenant-login` (`:47`, `:54`).
- **Allow-list:** `lib/rbac.ts:31-54`. A path with no rule redirects to `/login` (`middleware.ts:74-79`).
- **Admin check:** if `cis_admin_token` is present, the token is POSTed to backend `/auth/verify-admin` with a 3s timeout (`:119-165`), using a shared cache (`:137`).
  - In development, a network failure lets the request through (`:157-164`).
  - The role is taken from the verified token, never from the cookie (`:85-99`).
- **Tenant check:** if `cis_tenant_token` is present, `/auth/verify-tenant` is called (`:102-106`, `:170-210`).
- **Backend URL:** middleware uses `NEXT_PUBLIC_API_URL` (`:49`), but every BFF route uses `API_URL`. The two are inconsistent.
- **Backend verify is stateless:** HS256 signature plus the role claim only (`api/main.py:339-356`).

### BFF verification (`lib/auth-server.ts`)
- `requireAdmin(req, roles)` (`:142-151`) calls `verifyStaff` (`:153-184`), which reads `cis_admin_token` and POSTs it to `/auth/verify-admin`. It fails closed.
- A role outside the allowed list gets 403 (`:147-149`).
- `requireTenant` (`:193-226`) does the same for the tenant token.
- **Verify cache:** admin entries live up to 5 min (`:55`), tenant entries 20s (`:56`). Each entry is capped at the token's own `exp` (`:64-74`, `:97-101`). The cache is keyed by token and is per serverless instance.

### BFF proxy routes and the headers they attach
| Route | Gate | Outbound auth |
|---|---|---|
| `app/api/admin/[...path]/route.ts` | `requireAdmin(API_RULES.admin)` `:41`, read/write rules `:55-61` | `X-Admin-Secret` = env `ADMIN_SECRET`, plus `x-admin-user-id` (`auth.adminId`, which is the `admin_users.id` UUID) and `x-admin-role` (`:68-73`); passes `x-reviewer-id` through (`:77-80`) |
| `app/api/pipeline/[...path]/route.ts` | `requireAdmin` `:17` | `X-Admin-Secret` only (`:36-38`), no user id or role |
| `app/api/tenant/[...path]/route.ts` | staff if a `cis_admin_token` cookie exists (`:50`), else tenant | staff: `x-admin-secret` plus `x-admin-user-id` to **any backend path** (`:55-64`, `:86`); tenant: `Authorization: Bearer <cis_tenant_token>` (`:65-71`) |
| `app/api/tenant/pipeline/brand-identity/route.ts` | `requireAdmin` `:23,:35` | `X-Admin-Secret` plus `X-API-Key` = env `INTERNAL_API_KEY` (`:14-20`) |
| `app/api/tour-full/[id]/route.ts` | `requireAdmin` `:17` | `X-Admin-Secret` plus `X-API-Key` (`:28-31`) |
| `app/api/playground/proxy/route.ts` | `requireTenant` `:27` | Bearer tenant token (`:57-60`) |
| `app/api/tenant/me/route.ts` | `requireTenant` `:15` | none (returns tenant display info) |

The staff JWT itself is **never** sent to the backend on data calls. Only the secret, plus the user id and role headers, go out.

### Logout
- `app/api/auth/admin-logout/route.ts:21-28` sets `maxAge=0` on `cis_admin_token`, `cis_role`, `cis_user` and `cis_api_token`.
- It is called from `app/_kit/Topbar.tsx:268-275` (the account menu), followed by `router.push("/login")`.
- The token is not revoked server-side and the verify cache is not cleared (`lib/auth-server.ts:46-48`).

### Role-based UI hiding
- `app/_kit/useAdminIdentity.ts:17-36` reads the client-writable `cis_role` and `cis_user` cookies. The value is cached once per page load (`:46-51`).
- The cookie is used by:
  - `Sidebar.tsx:31,102` via `canSeePage`
  - `adminNav.tsx:67-74` and `CommandPalette.tsx:47,78`
  - `Topbar.tsx:256,306`
  - Content Quality: `SentenceActions.tsx:35,39`, `PieceLabel.tsx:148-155`, `PlaceCardFactsDrawer.tsx:38`, `TourVersionDrawer.tsx`
- This only hides UI. Real enforcement is in middleware and the BFF (`lib/rbac.ts:4-5`).

### Tenant portal login (API key)
- **Page:** `app/tenant-login/page.tsx:25-37` POSTs to `/api/auth/tenant-login`.
- **Route:** `app/api/auth/tenant-login/route.ts:38-70` sets five **httpOnly** cookies: `cis_role=tenant`, `cis_tenant_token`, `cis_tenant_id`, `cis_tenant_name`, `cis_tenant_plan`. All are 24h, `path=/`.
- **Logout:** `app/api/auth/tenant-logout/route.ts:12-25`, called from `portal/_components/Sidebar.tsx:62` and `PlaceholderTabs.tsx:226`.
- **Code shared with admin:**
  - the same `middleware.ts`
  - the same `lib/auth-server.ts` caches
  - the `/portal` rule allows both `admin` and `tenant` (`lib/rbac.ts:53`)
  - the same `cis_role` cookie **name** on the same host and path

### Dead or legacy code (no importers found)
- `lib/admin-auth.ts:1-21`: stores `cis_admin_secret` in sessionStorage and sends `x-admin-secret` from the browser.
- `components/LogoutButton.tsx:8-13`: client-side cookie clear only.
- `lib/api.ts:1-39`: direct backend calls to `NEXT_PUBLIC_API_URL`.
- `app/_kit/api.ts:18-25` still adds `x-reviewer-id` from localStorage.

### Environment variables (names only)
- **Used in code:** `API_URL`, `NEXT_PUBLIC_API_URL`, `ADMIN_SECRET`, `INTERNAL_API_KEY`, `NODE_ENV`, `NEXT_PUBLIC_ENV`, `NEXT_PUBLIC_BUILD_SHA`, `NEXT_PUBLIC_SENTRY_DSN`.
- **Stale names in the local Vercel snapshot** `.env.local.check`: `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `CONTENT_USERNAME`, `CONTENT_PASSWORD`, `ADMIN_DISPLAY_NAME`, `CONTENT_DISPLAY_NAME`, `NEXT_PUBLIC_LANGFUSE_URL`. The code no longer reads them; if they are still set in Vercel, they can be removed.

### E2E tests
- **Config:** `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/playwright.config.ts:24-41` defines three projects (`chromium`, `smoke-setup`, `smoke`).
- **Login:** `tests/e2e/helpers/auth.ts:35-40` fills `/login` with `E2E_ADMIN_USERNAME` and `E2E_ADMIN_PASSWORD` and clicks "Login".
- **Session reuse:** `tests/e2e/smoke/auth.setup.ts:15-34` saves the storageState to `tests/e2e/.auth/admin-state.json`.
- **Secrets:** CI passes the GitHub secrets `E2E_ADMIN_USERNAME`, `E2E_ADMIN_PASSWORD` and `VERCEL_AUTOMATION_BYPASS_SECRET` (`.github/workflows/ui-smoke.yml:20-26,54-60`). Those GitHub secrets mirror `aa-cis/dev/e2e-test-admin` (user `e2e-claude-code`).
- **Vercel SSO bypass:** origin-scoped, with `x-vercel-set-bypass-cookie: samesitenone` (`tests/e2e/smoke/smoke-helpers.ts:54-75`).
- **Forged-cookie suite:** `tests/e2e/smoke/aa656-forged-cookie.spec.ts:12-28` hard-codes the cookie names and proxy routes.
- **Portal smoke:** skips unless `E2E_TENANT_API_KEY` is set (`tests/e2e/smoke/ui-smoke.spec.ts:152-158`).

### URLs Terraform expects
From `/home/nghiep/projects/AA-Ecosys/infra/AA-CIS-Infra/accounts/aa365/identity_variables.tf`:

| Client | Callback | Logout |
|---|---|---|
| cis-admin (`:143-146`) | `https://aa-cis.lumiguides.it.com/api/auth/callback/cognito` and `http://localhost:3000/api/auth/callback/cognito` | `https://aa-cis.lumiguides.it.com/login` and `http://localhost:3000/login` |
| breakglass (`:147-150`) | `https://aa-cis.lumiguides.it.com/api/auth/callback/cognito-breakglass` | `https://aa-cis.lumiguides.it.com/login` |
| cis-portal (`:155-158`, Phase 3) | `/portal/api/auth/callback/cognito` | `/portal/login` |

Client settings in `identity.tf`:
- Clients are confidential, code flow only, scopes `openid email profile`, `ALLOW_USER_AUTH` only (`:566-578`).
- cis-admin tokens: access and ID 15 min, refresh 12h. Breakglass refresh: 1h (`:146-158`).
- Refresh-token rotation is on with a 60s grace, and token revocation is on (`:588-593`). Refresh therefore goes through `/oauth2/token` (ADR `0006:79-82`).
- Prefix domain is `aa365-staff-auth-dev.auth.us-west-1.amazoncognito.com` (`identity_variables.tf:21-25`).

## 3. Everything that must change for Phase 1

1. **New authorize route,** for example `app/api/auth/signin/cognito/route.ts`:
   - generate `state`, `nonce` and a PKCE `code_verifier`/`S256` challenge
   - store them in a short-lived httpOnly cookie
   - redirect to `{domain}/oauth2/authorize`
   - provide a separate variant for breakglass with its own client id and secret
2. **New callback routes** at `app/api/auth/callback/cognito/route.ts` and `app/api/auth/callback/cognito-breakglass/route.ts` (paths fixed by TF `:144,:148`):
   - check `state`
   - exchange the code at `/oauth2/token` using HTTP Basic client_id:secret plus the verifier
   - verify the ID token (`iss`, `aud`, `nonce`, `token_use`)
   - map `cognito:groups` to a CIS role: `cis-admin`→admin, `cis-reviewer`→reviewer, `cis-content`→content
   - refuse users with no `cis-*` group
   - set the session cookies
   - set `cis_role`/`cis_user` server-side, replacing what `login/page.tsx:43-44` does today
   - redirect to `landingPage(role)` (`lib/rbac.ts:124`)
3. **`app/login/page.tsx:6-118`:** add a "Sign in with Adventure Asia" button that goes to the authorize route. Render the username/password form only while `LEGACY_ADMIN_LOGIN_ENABLED` is true; the page is a client component, so it needs a server-passed prop or a `NEXT_PUBLIC_` mirror of the flag. Keep the "B2B Tenant login" link (`:113`).
4. **`app/api/auth/login/route.ts:35`:** return 404/403 when `LEGACY_ADMIN_LOGIN_ENABLED=false`. Keep the code for 30 days per ADR `0006:390`.
5. **Session cookie, `login/route.ts:75-81`:** `cis_admin_token` currently means "HS256 JWT, 24h".
   - Decide between (a) keeping the name and storing the Cognito access token (15 min), or (b) a new `cis_staff_at` cookie plus an httpOnly refresh cookie (`cis_staff_rt`, 12h, ideally `path=/api/auth`).
   - Every place that checks for the cookie's presence uses the name: `middleware.ts:85,120`, `auth-server.ts:154`, `api/tenant/[...path]/route.ts:50`, `admin-logout/route.ts:21`, and `aa656-forged-cookie.spec.ts:16`.
6. **Token verification:**
   - `lib/auth-server.ts:153-184` (`verifyStaff`) and `middleware.ts:119-165` (`verifyAdminToken`) both POST to `/auth/verify-admin`, which only understands HS256 (`api/main.py:339-356`).
   - Either extend `/auth/verify-admin` to accept Cognito JWTs (lowest FE churn), or verify locally against the JWKS with `jose`, which would be a new dependency (`package.json:11-22`).
   - The result must carry `adminId` = `admin_users.id`, not the Cognito `sub`. `x-admin-user-id` (`api/admin/[...path]/route.ts:70`, `api/tenant/[...path]/route.ts:64`) feeds backend writes keyed by the admin UUID, so the lookup must go through `cognito_sub`.
7. **Refresh:** a 15-min access token against a 24h cookie today. Pages (middleware `:85-99`) and proxies (`auth-server.ts:153`) must refresh through `/oauth2/token` with `grant_type=refresh_token` and rewrite both cookies. `ALLOW_REFRESH_TOKEN_AUTH` is not enabled. Put this in one helper.
8. **Logout, `app/api/auth/admin-logout/route.ts:23-28`:** also call `/oauth2/revoke` with the refresh token, clear the new cookies, and return a redirect to `{domain}/logout?client_id=…&logout_uri=https://aa-cis.lumiguides.it.com/login`. `Topbar.tsx:268-275` must then follow that URL (`window.location`) instead of `router.push("/login")`.
9. **Dropping X-Admin-Secret** (after cut-over, while the legacy flag is still on):
   - remove the secret at `api/admin/[...path]/route.ts:35,44-46,69`, `api/pipeline/[...path]/route.ts:11,20-22,37`, `api/tenant/[...path]/route.ts:41,60-63`, `api/tenant/pipeline/brand-identity/route.ts:11,16` and `api/tour-full/[id]/route.ts:10,29`
   - send `Authorization: Bearer <access token>` on all of them
   - the backend has 152 `verify_admin_secret(` calls across 21 files (`api/routers/admin.py:110` and others) that must accept Bearer first
   - then rotate `ADMIN_SECRET` per ADR `0006:390`
10. **Role display, `app/_kit/useAdminIdentity.ts:27-35`:** either keep the `cis_role`/`cis_user` cookies written by the callback (display only), or switch to a new `/api/auth/me` route. Same for `Topbar.tsx:306` (role label).
11. **Delete dead code** that would confuse reviewers: `lib/admin-auth.ts`, `components/LogoutButton.tsx`, `lib/api.ts`.
12. **E2E:**
    - `tests/e2e/helpers/auth.ts:35-40` and `smoke/auth.setup.ts` need a Cognito path, for example a WORKFORCE e2e user signing in with PASSWORD through managed login. Email OTP can't be automated.
    - Otherwise preview smoke has to keep the legacy flag on.
    - `aa656-forged-cookie.spec.ts:12-18` needs the new cookie names.
    - `ui-smoke.yml:20-26` secrets may change.
13. **Docs:** update the auth sections of `CONTEXT.md` (`:445`, `:477`, `:400-410`).

## 4. Pitfalls
- **Vercel previews can't do Cognito login.** Preview URLs are random `*.vercel.app` hosts, Cognito callback URLs allow no wildcards, and TF lists only the prod host plus `localhost:3000` (`identity_variables.tf:144`). Options: keep `LEGACY_ADMIN_LOGIN_ENABLED=true` in Vercel's Preview environment, or add a stable preview alias to `identity_client_urls`. Preview is also behind Vercel SSO; the bypass cookie is `samesitenone` (`smoke-helpers.ts:75`). The `lax` OAuth state cookie must survive the cross-site return, which works because the return is a top-level GET.
- **Switching the legacy flag off breaks AA-Booking login.** `AA-Booking/frontend/app/api/auth/login/route.ts:3-4,49` calls CIS `/auth/admin-login` and then `/auth/booking-token`, which reads `cis_admin_token` or a Bearer HS256 token (`api/main.py:358-370`). Either the flag must gate only the CIS UI path, or Phase 2 must land first.
- **Pre-token trigger isn't client-aware.** A user with only `booking-*` groups still gets a token for the cis-admin client (`lambda_src/identity_triggers/workforce.py:101-105`). CIS must deny when there is no `cis-*` group, and pick the highest role when several apply.
- **Cookie collision between admin and portal.** The same host and `path=/` carry an httpOnly `cis_role=tenant` (`tenant-login/route.ts:63`) and a JS-written `cis_role` (`login/page.tsx:43`). A browser won't let JS overwrite an httpOnly cookie, so after a tenant session the admin nav shows the wrong role. Setting `cis_role` server-side in the callback fixes this.
  - When both sessions exist, middleware prefers the staff token (`middleware.ts:85` before `:102`).
  - The tenant proxy picks the staff branch whenever `cis_admin_token` exists (`api/tenant/[...path]/route.ts:50`), so a staff session forwards admin credentials even on portal calls.
- **Future cis-portal callback (Phase 3).** `/portal/api/auth/callback/cognito` sits under the middleware matcher `/portal/:path*` (`middleware.ts:215`) and the `/portal` page rule. An unauthenticated callback would be redirected to `/tenant-login`, so it must be added to `PUBLIC_PATHS`. Also, `/portal/login` (the TF logout URL) doesn't exist; the tenant login is at `/tenant-login`. And `app/(tenant)/portal/api/page.tsx` already owns `/portal/api`.
- **Logout and silent re-login.** The managed-login cookie lasts 1h and isn't cleared by global sign-out (ADR `0006:275-277`). If `/login` auto-redirects to Cognito, logout bounces straight back in. Logout must hit Cognito `/logout`, and `/login` must not auto-redirect.
- **Refresh races with rotation.** The atom-curation page fires about 8 concurrent proxy calls (`auth-server.ts:18-28`). Parallel refreshes each rotate the token, and only the 60s grace saves them (`identity.tf:588-591`). Refresh should happen in one place (middleware on navigation, or a single-flight `/api/auth/refresh`), not inside every proxy.
- **Cookie sizes.** The Cognito access, ID and refresh tokens are each roughly 1–2 KB. Store only what is needed (access plus refresh; the ID token is only for the callback check). Never put all three in one cookie, and stay under the 4 KB per-cookie limit.
- **Verify cache.** Keyed by token, 5-min TTL capped at `exp` (`auth-server.ts:55,97-101`). That is fine for 15-min tokens, but a disabled user stays valid until access-token expiry. This matches the ADR's 15-min worst case.
- **Development fail-open.** Middleware allows requests through on a verify network error in development and trusts `cis_role` (`middleware.ts:157-164`). That shortcut must not survive into a Cognito path that runs on preview.
- **Mixed backend URL variables.** Middleware uses `NEXT_PUBLIC_API_URL` (`:49`) while the BFF uses `API_URL`. New Cognito env vars (pool or domain, client ids and secrets for cis-admin and breakglass) should be server-only, never `NEXT_PUBLIC_`. Client secrets go only into Vercel Production/Preview env. Underscore env var names must be edited by hand in Vercel/VSCode, per the CLAUDE.md rule.
- **localhost port.** The TF callback uses `localhost:3000` (`next dev` default), but Playwright's default `baseURL` is `localhost:3001` (`playwright.config.ts:18`). Local Cognito E2E would fail with redirect_mismatch.
- **Breakglass.** It needs its own client secret in env and its own callback route. Refresh is 1h, and every token issued raises an alarm (`workforce.py:107-114`), so E2E must never use breakglass.


# map:cis-backend

# CIS staff auth map, and what changes for Cognito Phase 1 (AA-854 / AA-816)

**Source:** every `file:line` below is in `apps/AA-CIS-App` at **`origin/main` f273dc85 (#806)**. Your local `main` is 12 commits behind (it stops at #789) and has no `api/core/staff_authz.py` or `admin_platform.py`, so I read `origin/main` through `git archive`, exported to `/tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/c768b1bc-cbab-44a1-88fe-8b5f8f744c75/scratchpad/cis`. The local AA-CIS-Infra checkout is also 14 commits behind, so Infra citations use `origin/main` too. Nothing was edited, no git write commands ran, and no AWS calls were made.

## A. Current map

### A1. Admin login and password check
- **Endpoint `POST /auth/admin-login`** is `api/main.py:313-343`.
  - It runs `SELECT id, username, password_hash, role::text, is_active FROM shared.admin_users WHERE username=$1` (`api/main.py:326-331`).
  - It always runs a bcrypt compare, against a dummy hash when no row is found (`api/main.py:333-334`), then returns the same 401 for every failure (`api/main.py:335-336`).
  - It mints the token at `api/main.py:337`.
- **Helpers** live in `api/routers/auth.py`:
  - `_verify_password` (bcrypt, fails closed) at `api/routers/auth.py:299-305`.
  - `_create_admin_jwt` at `api/routers/auth.py:308-316`.
  - Models `AdminLoginRequest/Response` and `VerifyAdminResponse` at `api/routers/auth.py:273-289`.
  - `STAFF_ROLES = ("admin","reviewer","content")` at `api/routers/auth.py:270`.
- The `/auth` APIRouter in auth.py is **not mounted**. The live routes are declared again in main.py (`api/routers/auth.py:257-266`).
- **Accounts are created only by `scripts/create_staff_user.py`.** It prompts for the password, stores a bcrypt hash, and runs INSERT/UPDATE on `shared.admin_users` (`scripts/create_staff_user.py:44,59-70`).

### A2. HS256 JWT (secret `aa-cis/dev/jwt-secret`)
- `JWT_SECRET` comes from the environment. The app refuses to start without it (AA-506) (`api/routers/auth.py:33-38`).
- `JWT_ALG="HS256"` and the 24 h expiry are at `api/routers/auth.py:39-40`.
- The staff token carries `sub=admin_users.id`, `username`, `role`, `iat` and `exp`. It has no `iss` or `aud` (`api/routers/auth.py:308-316`).
- The tenant token uses the **same secret** with `role='tenant'` (`api/routers/auth.py:63-72`).
- `verify_jwt` decodes HS256 with no `iss`/`aud` check (`api/routers/auth.py:75-82`). `verify_tenant_jwt` requires `role=='tenant'` (`api/routers/auth.py:85-93`).
- Infra injects `JWT_SECRET` and `ADMIN_SECRET` from Secrets Manager into the api task def (`infra/AA-CIS-Infra/modules/ecs/main.tf:402-403`) and the worker task def (`modules/ecs/main.tf:603-604`). The variables are at `accounts/aa365/variables.tf:118,123`.

### A3. `POST /auth/verify-admin`
- Defined at `api/main.py:367-393`.
  - It decodes the HS256 token and requires the role claim to be in `STAFF_ROLES` (`api/main.py:377-380`).
  - It then re-reads `shared.admin_users` through `_current_staff`, cached 60 s (`api/main.py:348-364`, using `_load_active_staff` at `api/main.py:410-424`).
  - It returns the **DB role**, not the claim, and answers 401 if the user is inactive or unknown (`api/main.py:381-393`).
- Callers are the BFF `verifyStaff()` (`frontend/lib/auth-server.ts:153-184`, cached up to 5 min at `frontend/lib/auth-server.ts:55`) and `frontend/middleware.ts:119-141`.

### A4. X-Admin-Secret handling
- **`admin.ADMIN_SECRET`** is read once at import (`api/routers/admin.py:34`). `verify_admin_secret` returns 503 when the secret is unset and 403 on a mismatch, using a constant-time compare (`api/routers/admin.py:113-117`, helper at `api/core/secret_compare.py:17-23`).
- **The secret is checked inline in 150 places:** 150 route bodies call `verify_admin_secret(x_admin_secret)` directly. Per router: admin_pipeline 52, admin 25, admin_content_quality 19, admin_llm_ops/admin_dashboard/admin_decisions 7 each, admin_a4 6, admin_job_runner/admin_waves 5, others 1-3 (for example `api/routers/admin_pipeline.py:1139,1153,1173...`).
- **Copies and variants of the same check:**
  - `admin_settings.verify_admin` (`api/routers/admin_settings.py:29-33`).
  - `v1_pipeline._require_admin`, which reads the env per call; any JWT gets 403 and no credentials get 401 (`api/routers/v1_pipeline.py:43-58`).
  - `staff_secret.require_staff_secret` for /v1/rules and /v1/social (`api/core/staff_secret.py:33-48`; attached at `api/routers/v1_rules.py:24` and `api/routers/v1_social.py:26`).
  - `admin_atoms._require_atoms_staff` (`api/routers/admin_atoms.py:84-102`).
  - `main.require_admin_secret_for_docs` for /docs, /redoc and /openapi.json, active only on ECS (`api/main.py:178-209`).
- **`verify_tenant_api_key`** turns the secret into the AA-internal admin principal (`sub` = sentinel `000…001`, `role=admin`) (`api/routers/auth.py:202-254`, sentinel at `api/routers/auth.py:182`). This is the tenant-impersonation path the ADR names.
- **The rate-limit middleware** tracks `/admin/*` calls only when the secret matches, and reads `x-admin-user-id` as the actor (`api/middleware/rate_limit.py:152-193`).
- **BFF senders:**
  - `frontend/app/api/admin/[...path]/route.ts:35,44,69` (it also sends `x-admin-user-id` and `x-admin-role` at `:70-72`).
  - `frontend/app/api/pipeline/[...path]/route.ts:11,20,37`.
  - `frontend/app/api/tour-full/[id]/route.ts:10,29`.
  - `frontend/app/api/tenant/pipeline/brand-identity/route.ts:11,22`.
  - `frontend/app/api/tenant/[...path]/route.ts:41,60-63` (staff branch).

### A5. `staff_policy` (AA-882) and the admin_role values
- All of this is in `api/core/staff_authz.py`:
  - Capabilities: `api/core/staff_authz.py:56-74`.
  - `ROLE_PERMS` for admin, reviewer and content: `api/core/staff_authz.py:78-86`.
  - `OWNER_PERMS={staff.write}`, which has no column yet (planned as `is_owner` in GĐ5): `api/core/staff_authz.py:88-90`.
  - `STAFF_ROLES = tuple(ROLE_PERMS)`: `api/core/staff_authz.py:94`.
  - `POLICY` keyed by `(method, route template)`: `api/core/staff_authz.py:102-273`. The staff-directory entries are at `api/core/staff_authz.py:263-264`.
  - `STAFF_PATH_PREFIXES`: `api/core/staff_authz.py:283`.
  - `MACHINE_ROUTES` (CI deploy gate and smoke, the ops Lambda): `api/core/staff_authz.py:288-298`.
- **How it decides:**
  - `principal_from_role`: no `x-admin-role` header means the machine principal; an unknown role gets no capabilities (`api/core/staff_authz.py:318-327`).
  - `denial_reason`: `api/core/staff_authz.py:334-347`.
  - The route template comes from `scope["route"].path` (`api/core/staff_authz.py:350-359`).
  - `staff_policy` checks the secret, then the policy (`api/core/staff_authz.py:386-398`). `staff_policy_if_staff` is a no-op unless the valid secret is present (`api/core/staff_authz.py:401-429`).
  - The role is **trusted from the `x-admin-role` header**, as the module itself says at `api/core/staff_authz.py:24-30`.
- **Role checks inside handlers, all using `x_admin_role`:**
  - `admin._require_tenant_admin` (`api/routers/admin.py:122-127`).
  - `has_perm` checks at `api/routers/admin.py:812` (tenant details) and `api/routers/admin.py:2145`.
  - `admin_api_docs.require_admin_role` (`api/routers/admin_api_docs.py:23-26`).
  - `admin_content_quality._require_admin_role` / `_require_label_admin` (`api/routers/admin_content_quality.py:408-411,691-692,1416`).
  - `admin_search` filters by `has_perm` (`api/routers/admin_search.py:113-114`).
- **The actor comes from the `x-admin-user-id` header** (81 uses in 15 files), via `admin._admin_actor` (`api/routers/admin.py:130`), `services/acp_shared/audit_log.py:85` and `shared/services/billing_service.py:14-32`.
- **Enum `shared.admin_role`:**
  - Created as `('admin','reviewer')` in `api/migrations/074_admin_users_jwt_auth.sql:41-50`.
  - `'content'` added by `api/migrations/218_admin_role_content.sql:15`.
  - The live values are admin, reviewer and content (`docs/architecture/db-schema-reference.md:3722`).
  - The frontend mirror is `frontend/lib/rbac.ts:14-21`, kept in sync by `tests/unit/test_aa882_staff_authz.py:40-48`.

### A6. How routes get the current staff user
There is no `get_current_staff` dependency. Routers attach `dependencies=[Depends(staff_policy)]` (for example `api/routers/admin.py:33`) or `Depends(verify_admin_secret), Depends(staff_policy)` (for example `api/routers/admin_platform.py:31-32`, `api/routers/admin_llm_ops.py:66`). Identity reaches handlers only as the headers `x_admin_role` and `x_admin_user_id`. `staff_policy` returns a `StaffPrincipal` (kind and role only, `api/core/staff_authz.py:303-315`) that no handler uses.

### A7. Booking bridge (PR #721 / AA-680)
- **`POST /auth/booking-token`** is `api/main.py:427-454`.
  - It reads the session from a Bearer header or the `cis_admin_token` cookie (`api/main.py:403-407`).
  - It verifies the **HS256** token and requires a staff role (`api/main.py:432-434`), then re-reads the DB row (`api/main.py:435-441`).
  - It mints the token at `api/main.py:448-450`.
- **`GET /auth/.well-known/jwks.json`** is `api/main.py:457-463` (Cache-Control `max-age=600` at `api/main.py:400`).
- **Key handling** is in `api/core/booking_jwt.py`:
  - Issuer, `aud=booking`, RS256 and the 15 min TTL: `api/core/booking_jwt.py:45-49`.
  - The secret JSON holds `kid` `bk-2026-10` plus previous/next keys (`api/core/booking_jwt.py:7-13`); the secret name comes from `BOOKING_JWT_SECRET_NAME` (`api/core/booking_jwt.py:72-73`).
  - TTL cache: `api/core/booking_jwt.py:126-162`.
  - Claims are `sub`, `name`, `preferred_username`, `cis_role`, `jti`, with the `kid` header (`api/core/booking_jwt.py:183-206`). **There is no `email` claim**, although the Booking verifier docstring expects one (`apps/AA-Booking/backend/app/auth/tokens.py:3-5`).
- **The Booking frontend logs in with a password through CIS:** it calls `/auth/admin-login`, then `/auth/booking-token` (`apps/AA-Booking/frontend/app/api/auth/login/route.ts:3-4,49`; `apps/AA-Booking/frontend/lib/session.ts:5-6,65-69`).

### A8. Read-only staff directory (AA-883)
- `api/routers/admin_platform.py`:
  - `GET /admin/platform/staff` at `api/routers/admin_platform.py:53-68`.
  - `GET /admin/platform/staff/{staff_id}` at `api/routers/admin_platform.py:71-82`.
  - The columns are an explicit list: id, username, role, is_active, created_at, updated_at, and never `password_hash` (`api/routers/admin_platform.py:35-40`).
  - The router is mounted at `api/main.py:247`.
- Access is `staff.read`, admin only (`api/core/staff_authz.py:263-264`). Tests: `tests/unit/test_aa883_admin_platform.py` (10 tests).

### A9. `shared.admin_users`
- **Live columns:** `id uuid`, `username varchar(100)`, `password_hash varchar(255)`, `role shared.admin_role`, `is_active bool`, `created_at`, `updated_at`. All are NOT NULL. There is a UNIQUE index on `username` and the owner is `aa_cis_admin` (`docs/architecture/db-schema-reference.md:2282-2294`).
- **Foreign keys into it:** `tenant_api_usage.admin_user_id`, `generated_content.reviewed_by` and `raw_tours.reviewed_by` (`docs/architecture/db-schema-reference.md:3866,3875,3884`).
- **Migrations:**
  - 074 creates the table and the FK wiring (`api/migrations/074_admin_users_jwt_auth.sql:55-63`).
  - 110 adds the FK from `tenant_api_usage` (`api/migrations/110_tenant_api_usage_admin_actor.sql:35`).
  - 218 adds the enum value `content`.
  - There are no columns for email, cognito_sub, display_name, Booking role or owner.

### A10. Migration number and convention
- **The latest CIS migration on main is 243** (`api/migrations/243_x1_owner_role_grants.sql`). The schema reference was dumped at 242 (`docs/architecture/db-schema-reference.md:5`).
- **244, 245 and 246 are reserved by the X1 plan:**
  - 244 is `cis_app` grants (`docs/audits/2026-10-17-S241-x1/x1-plan.md:180`).
  - 245 moves CIS objects to `cis_owner` (`docs/audits/2026-10-17-S241-x1/x1-plan.md:185`).
  - 246 is the probe (`docs/audits/2026-10-17-S241-x1/x1-plan.md:151,186`).
  - CIS migrations are **frozen from the 245 Infra copy until the 246 probe passes** (`docs/audits/2026-10-17-S241-x1/x1-plan.md:741`).
  - **So Phase 1 needs 247 or later, or a coordinated renumber with X1.**
- **File convention:** `api/migrations/NNN_snake_case.sql`. Each file has a header comment (why/what), wraps the change in `BEGIN; … COMMIT;`, ends with `INSERT INTO shared.schema_versions (version, applied_at, description) … ON CONFLICT (version) DO NOTHING`, and is copied byte-identical to `infra/AA-CIS-Infra/db/migrations/cis/`, where the DB Migrate workflow applies it (`api/migrations/218_admin_role_content.sql:11-21`; `api/migrations/243_x1_owner_role_grants.sql` tail). Enum DDL goes outside the transaction (`api/migrations/074_admin_users_jwt_auth.sql:33-50`).

### A11. Config and flag conventions
- There is **no pydantic `BaseSettings` module in CIS**. Settings are read directly with `os.environ.get(...)`, either at import (`api/routers/admin.py:34`, `api/routers/auth.py:33`) or per call (`api/core/staff_secret.py:37`). Boolean flags follow the pattern `os.environ.get(X,"false").lower() in ("1","true","yes")` (`shared/jobs/worker.py:314-319`).
- Runtime toggles are **Redis flags** (`api/core/aa544_tenant_pool.py:68-69`).
- Env values are set in the Infra ECS task def: plain values at `modules/ecs/main.tf:380-397`, secrets at `modules/ecs/main.tf:398-410`.
- CI provides test env values at `.github/workflows/ci.yml:72-84` and `tests/unit/conftest.py:16`.
- (Booking does have a settings dataclass with env parsing, `apps/AA-Booking/backend/app/settings.py:45-119`.)

### A12. JWT/JWKS libraries
- `requirements.txt:51` has `PyJWT[crypto]>=2.8.0` and `requirements.txt:52` has `bcrypt>=4.1.0`.
- **python-jose and authlib are not present.** `PyJWKClient` is not used anywhere.
- There is no existing CIS verifier for an outside issuer.
- The nearest reusable code is the Booking `JwksCache` / `decode_rs256` / `StaffTokenVerifier` (single issuer; `apps/AA-Booking/backend/app/auth/tokens.py:89-188`, `PyJWT==2.15.1` at `apps/AA-Booking/backend/requirements.txt:9`).
- ADR 0006 says the verifier is written once and copied byte-identical into each repo (`docs/adr/0006-ecosystem-identity.md:316`). The contract is at `docs/adr/0006-ecosystem-identity.md:280-317`.

### A13. Tests covering auth (unit tests unless noted)
| File | Tests | What it covers |
|---|---|---|
| `test_aa656_staff_roles.py` | 9 | verify-admin for every role |
| `test_aa680_booking_jwt.py` | 24 | bridge token and JWKS |
| `test_aa882_staff_authz.py` | 40 | decision table, role sync with rbac.ts |
| `test_aa882_route_policy.py` | — | enforcing; snapshot `tests/unit/snapshots/aa882_staff_route_policy.json` |
| `test_aa882_gd3_router_samples.py` | 6 | sample routes per router, per principal |
| `test_aa882_review_fixes.py` | 12 | admin-only reads closed |
| `test_aa883_admin_platform.py` | 10 | staff directory |
| `test_aa577_swagger_docs_gate.py` | 10 | docs gate |
| `test_aa799_pipeline_auth.py` | 12 | /v1/pipeline admin-only |
| `test_auth_tenant_api_key.py` | 5 | `verify_tenant_api_key` |
| `test_aa859_admin_atoms_staff_only.py` | — | /admin/atoms staff only |
| `tests/integration/test_aa680_booking_staff_lookup.py` (integration) | 3 | staff lookup on real Postgres |

### A14. CI route-auth guard
- **`tests/unit/test_s241_admin_routes_require_auth.py`** walks every route in `app.routes`.
  - `STAFF_DEPENDENCIES` is the allowlist of staff checks (`tests/unit/test_s241_admin_routes_require_auth.py:46-56`).
  - `STAFF_INLINE_CHECKS` is at `:62`, `STAFF_ONLY_PREFIXES` at `:64`, and `ALLOWED_PUBLIC` (the /auth endpoints) at `:76-83`.
- **`tests/unit/test_aa882_route_policy.py:1-17`** requires every staff route to run `staff_policy` or `staff_policy_if_staff`, and every write to have a POLICY entry.
- Both run in the CI "Run unit tests" step (`.github/workflows/ci.yml:85-91`).

## B. Places that must change for Phase 1

### B1. Database migration (CIS 247 or later, see A10)
1. Add `email` (unique on `lower()`, CHECK that it ends with `@adventure.asia`), `display_name`, `cognito_sub` plus `cognito_iss` (ADR §9 keys on `(iss, sub)`, `docs/adr/0006-ecosystem-identity.md:322-332`) and a Booking role column to `shared.admin_users`.
2. Make `password_hash` nullable. Today it is NOT NULL (`docs/architecture/db-schema-reference.md:2286`; `api/migrations/074_admin_users_jwt_auth.sql:58`), so Cognito-only users cannot be inserted.
3. Optionally add `is_owner` for `staff.write` (`api/core/staff_authz.py:88-90`).
4. Copy the file to `infra/AA-CIS-Infra/db/migrations/cis/`, then regenerate `docs/architecture/db-schema-reference.md`.

### B2. New verifier module (`api/core/`, copied from the ADR reference or the Booking verifier)
- One RS256 verifier with per-issuer JWKS cache. It checks `iss`, `token_use=access` and `client_id ∈ {cis-admin, breakglass}`, and returns a Principal with groups and email (ADR rules at `docs/adr/0006-ecosystem-identity.md:295-315`).
- New env vars in the Infra task def next to `modules/ecs/main.tf:380-397`: issuer, JWKS URL, allowed client IDs, `LEGACY_ADMIN_LOGIN_ENABLED`. The issuer and client IDs come from the Infra outputs `infra/AA-CIS-Infra/accounts/aa365/identity.tf:913-940`.
- Add the same values to the CI env (`.github/workflows/ci.yml:72-84`) and `tests/unit/conftest.py:16`.
- Add a pinned PyJWT if it is not already enough; it currently floats at `requirements.txt:51`.

### B3. Principal resolution, replacing header trust
- **`api/core/staff_authz.py:318-327, 362-429`.** Build the principal from a verified Bearer token: role from `cognito:groups` (cis-admin, cis-reviewer, cis-content mapped to admin, reviewer, content), user from `cognito_sub` looked up to `admin_users.id`. Keep the secret-only machine principal for `MACHINE_ROUTES` (`api/core/staff_authz.py:288-298`).
- **Map groups to roles.** `ROLE_PERMS` is keyed by role (`api/core/staff_authz.py:78-86`). If someone holds several `cis-*` groups, the code must define which one wins (a union of permissions, or the highest role).
- **`api/routers/admin.py:113-117` (`verify_admin_secret`) is the key decision point.** Its 150 inline calls take only the header value. Either it accepts a request-scoped verified principal (which means a signature change or a contextvar, because the callers pass no `request`), or the secret stays as the BFF-to-API transport during the 30-day window. Moving off the secret also touches the variants:
  - `api/routers/admin_settings.py:29-33`
  - `api/routers/v1_pipeline.py:43-58`
  - `api/core/staff_secret.py:33-48`
  - `api/routers/admin_atoms.py:84-102`
  - `api/main.py:178-186`
- **Handlers that read `x_admin_role` must read the principal instead:**
  - `api/routers/admin.py:122-127, 812, 2145`
  - `api/routers/admin_api_docs.py:23-26`
  - `api/routers/admin_content_quality.py:408-411, 691-692, 1416`
  - `api/routers/admin_search.py:113-114`
- **The actor (`x-admin-user-id`) must come from the verified principal:**
  - `api/routers/admin.py:130`
  - `api/middleware/rate_limit.py:163-193`, which also gates tracking on the secret
  - `services/acp_shared/audit_log.py:85`
  - `shared/services/billing_service.py:14-32`
  - the remaining `x_admin_user_id` parameters in admin_pipeline, admin_llm_ops, admin_a4, admin_decisions, admin_places, admin_segment_research, admin_photos, admin_waves, admin_budgets, admin_job_runner and admin_content_quality

### B4. Auth endpoints (`api/main.py`)
- **`/auth/admin-login`** (`api/main.py:313-343`): put it behind `LEGACY_ADMIN_LOGIN_ENABLED`. **Do not switch it off until Booking Phase 2.** The Booking frontend logs in through it (`apps/AA-Booking/frontend/app/api/auth/login/route.ts:49`).
- **`/auth/verify-admin`** (`api/main.py:367-393`): accept the Cognito access token too, or add a separate verify endpoint. `_load_active_staff` / `_current_staff` (`api/main.py:353-364, 410-424`) need a lookup by `(cognito_iss, cognito_sub)`, and the response should add email and display_name (`api/routers/auth.py:285-289`).
- **`/auth/booking-token`** (`api/main.py:427-454`): today it accepts only the HS256 session (`api/main.py:432`). A Cognito-signed-in CIS admin cannot get a Booking bridge token until it also accepts the Cognito principal. Booking still needs the bridge until Phase 2 (`docs/adr/0006-ecosystem-identity.md:391`).
- **Optional:** add an `email` claim to `api/core/booking_jwt.py:192-203`, which the Booking docstring expects.

### B5. Staff directory, AA-816 (from read-only to write)
- `api/routers/admin_platform.py:1-20, 35-40, 53-82`: add email, display_name, cognito_sub and the Booking role to `STAFF_COLUMNS`. Add create, disable and change-role routes that write the DB and then Cognito (`AdminCreateUser`, `AdminAdd/RemoveUserFromGroup`, `AdminDisable/EnableUser`, `AdminUserGlobalSignOut`).
- Each new write needs a `POLICY` entry next to `api/core/staff_authz.py:263-264` (capability `staff.write`, owner flag), a regenerated snapshot `tests/unit/snapshots/aa882_staff_route_policy.json`, and new `tests/unit/test_aa883_admin_platform.py` cases.
- **IAM:** the ECS task role (`infra/AA-CIS-Infra/modules/ecs/main.tf:115, 166`) has no `cognito-idp` permissions. Add the explicit allow-list from `docs/adr/0006-ecosystem-identity.md:117-123`.
- The reconcile job is a new `shared.job` kind (`docs/adr/0006-ecosystem-identity.md:108-115`).

### B6. One-off bootstrap for the first two users
`scripts/create_staff_user.py:44-70` only does password plus role. It needs a Cognito variant (or a new script) that runs `AdminCreateUser` with SUPPRESS, adds the groups, and writes `email`/`display_name` with `cognito_sub` NULL until the first successful sign-in fills it (the ADR precondition at `docs/adr/0006-ecosystem-identity.md:390`).

### B7. BFF (Next.js in the same repo)
- **`frontend/app/api/auth/login/route.ts:35-88`:** move to auth code + PKCE against `cis-admin`, with a callback route and the client secret held server-side. The client is defined at `infra/AA-CIS-Infra/accounts/aa365/identity.tf:146-155, 566-580`.
- **Session and verification:**
  - `frontend/lib/auth-server.ts:153-184`: the 5 min verify cache at `:55` is longer than the 15 min access-token lifetime allows for comfortably, and refresh is needed.
  - `frontend/middleware.ts:85-141`.
  - `frontend/app/login/page.tsx`.
  - `frontend/app/api/auth/admin-logout/route.ts`.
- **Proxies send Bearer instead of `X-Admin-Secret` / `x-admin-role` / `x-admin-user-id`:**
  - `frontend/app/api/admin/[...path]/route.ts:35-73`
  - `frontend/app/api/pipeline/[...path]/route.ts:11-37`
  - `frontend/app/api/tour-full/[id]/route.ts:10-29`
  - `frontend/app/api/tenant/pipeline/brand-identity/route.ts:11-22`
  - `frontend/app/api/tenant/[...path]/route.ts:41-63`
- **Rotate `ADMIN_SECRET` afterwards** (`docs/adr/0006-ecosystem-identity.md:390`).
- Keep `frontend/lib/rbac.ts:14-21` in sync.

### B8. Tests and CI guard
- **`tests/unit/test_s241_admin_routes_require_auth.py:46-62, 76-83`:** add the new Cognito staff dependency to `STAFF_DEPENDENCIES` / `STAFF_INLINE_CHECKS`, and add any new public auth routes (callback, token exchange) to `ALLOWED_PUBLIC`.
- **`tests/unit/test_aa882_route_policy.py`:** the snapshot changes.
- **`tests/unit/test_aa882_staff_authz.py:40-48`:** update if the principal source or the group mapping changes.
- **Update these:**
  - `test_aa656_staff_roles.py` (verify-admin with Cognito)
  - `test_aa680_booking_jwt.py` (booking-token with a Cognito session)
  - `tests/integration/test_aa680_booking_staff_lookup.py` (the new columns and nullable `password_hash`)
- **Add these:**
  - verifier unit tests (alg/iss/kid isolation, `token_use`, `client_id`, JWKS refetch), which per ADR are the same tests copied byte-identical into each repo
  - legacy-flag tests

### B9. Docs
- `CONTEXT.md:454-505`, the staff roles section. It currently describes header trust and HS256.
- `docs/implementation-notes/AA-854.md` / `AA-816.md`, per CLAUDE.md.

## C. Risks to settle before building
1. **Turning off the legacy login breaks Booking staff login.** `LEGACY_ADMIN_LOGIN_ENABLED=false` would stop Booking staff signing in (`apps/AA-Booking/frontend/app/api/auth/login/route.ts:49`), and `/auth/booking-token` accepts only HS256 (`api/main.py:432`). Phase 1 cannot finish before Booking Phase 2 unless booking-token also accepts Cognito.
2. **The migration number collides with X1.** 244, 245 and 246 are reserved, and the 245 to 246 freeze applies (`docs/audits/2026-10-17-S241-x1/x1-plan.md:180-186, 741`). The Phase 1 migration needs 247 or later, or a renumber agreed with X1.
3. **Removing `X-Admin-Secret` is a large change.** It touches 150 inline `verify_admin_secret(x_admin_secret)` calls plus 5 copies of the guard. The smallest safe step is probably: the BFF sends Bearer *and* the secret during the 30 days, `staff_policy` takes role and user from the verified Bearer token, and the secret becomes machine-only later.
