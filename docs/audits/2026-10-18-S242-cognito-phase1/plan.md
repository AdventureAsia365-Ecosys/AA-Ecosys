# Judge report: AA-854 finish, Cognito Phase 1 (CIS) and AA-816

I read everything at `origin/main`: CIS f273dc85 and Infra b69c8b1. Plan 1 says Infra is at f633ac7; that is wrong. Both local checkouts are behind, so run `git pull` before starting. Nothing was edited and no AWS calls were made.

## 1. Scores (out of 5)

| | Correctness | Lock-out safety | Verifiable on Dev | Size (5 = small) |
|---|---|---|---|---|
| Plan 1 | 4 | 5 | 5 | 3 |
| Plan 2 | 3 | 4 | 4 | 4 |

**Corrections, checked against the files:**

- **Plan 2's `scripts/identity/` location must be rejected.** Infra ignores `scripts/` (`infra/AA-CIS-Infra/.gitignore:3`), so new scripts there would silently never be committed. This is the same way `create_staff_user.py` was lost (LES:15). Plan 1's `tools/identity/` is correct.
- **Plan 2 misses a crash.** `_verify_password` calls `password_hash.encode()` and catches only ValueError and TypeError (`api/routers/auth.py:299-305`). Login passes `row["password_hash"]` straight in (`api/main.py:334`). Once migration 247 makes the hash nullable, a Cognito-only row makes the legacy login fail with a 500 (AttributeError on None). Plan 1's fix and test (C1) are required.
- **Plan 1's 403 on role drift goes against ADR:390** ("staff routes authorise from cognito:groups"), and it creates a lock-out path. Take Plan 2's rule instead: the group decides the role, drift is logged, and the reconcile job reports it.
- **Plan 1 puts IAM in `modules/ecs/main.tf`, but the repo pattern is a root-level policy on `module.ecs.task_role_name`.** That output exists at `modules/ecs/outputs.tf:18` and is already used this way at `ses.tf:212` and `observability_ecosys.tf:513`. Take Plan 2's `identity_iam.tf`.
- **Plan 1 adds Cognito env vars to the api and worker task definitions; Plan 2 does not.** Plan 2 uses code constants with an env override, following Booking's settings defaults (`settings.py:45-63`). That means no new underscore env vars in the task definitions. Take Plan 2's approach, and check the constant against the pool's `/.well-known/openid-configuration` (`identity.tf:907-908`).
- **Cookie: Plan 2 keeps the name `cis_admin_token`.** This avoids changing the pages that test for the cookie by name (`middleware.ts:85,120`, `auth-server.ts:154`, `tenant/[...path]/route.ts:50`, `aa656-forged-cookie.spec.ts:16`). Take it. Inside `/auth/verify-admin`, choose the path by the unverified `iss`; legacy HS256 tokens have no `iss` (`auth.py:308-316`). Each path pins its own algorithm.
- **Neither plan notices that the CI apply role has no permissions for EventBridge rules.** `cicd.tf:376-381` notes that CloudWatchFullAccess does not cover `events:*`, and the only `events` grants are for the ACP bus and the scheduler. I1 must add a rule grant, and that grant is applied locally with MFA first, like the bootstrap grants at `cicd_split.tf:598-600`. No `aws_cloudwatch_event_rule` exists yet in `accounts/aa365`. The secret resource policy is covered by `SecretsManagerReadWrite` (`cicd.tf:24`).
- **Role lint (`db/owners.yaml:85`, rule at `run_migration.py:770-790`).** Migration 247 must be a single BEGIN…COMMIT block with no SET ROLE that lacks LOCAL. The runner checks only "already applied" and has no order check (`run_migration.py:1202-1215`), so 247 can go before 244–246. Integration tests apply files in sorted order (`tests/integration/conftest.py:153`), so tests and Dev will apply them in different orders.
- **Where the bearer middleware goes.** The rate limiter is registered at `api/main.py:257`. Starlette makes the last-registered middleware the outermost, so the new middleware must be registered after line 257–258 to wrap the rate limiter.
- **Vercel env.** Tick Production and Preview for the client secrets (LES:52). `LEGACY_ADMIN_LOGIN_ENABLED` must stay `true` on Preview, because preview hosts cannot be registered as callbacks (`identity_variables.tf:143-146`).

## 2. Final merged plan

**Rules for every step:**
- Merge backend PRs one at a time (LES:63).
- No deploy or DB Migrate apply while `shared.job` has queued or running jobs (LES:57-58).
- Apply Terraform only from merged main (LES:65), with credentials from `export-credentials` (LES:67).
- Keep legacy login on until the cutover stage (S).

### Stage A: finish AA-854 (Infra PRs plus runs Nghiệp does)

**I1 (Infra) `feat: identity phase 1 prerequisites (break-glass alerts)`**, Refs AA-854.

- **`accounts/aa365/identity_variables.tf`:**
  - `identity_breakglass_email` set by D1 (`:14-18`). This also changes `BREAKGLASS_EMAIL` on the trigger (`identity.tf:182`).
  - The `booking-staff` callback and logout change from localhost:3001 to `https://aa-booking-admin.vercel.app/...` (`:151-153`).
- **New `accounts/aa365/identity_alerts.tf`:**
  - An `aws_cloudwatch_event_rule` on GetSecretValue and PutSecretValue for the secret `aa-identity/dev/breakglass` (`identity.tf:779-784`), with `state = "ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS"`. GetSecretValue is a read-only event; confirm on plan that provider 5.100.0 accepts this. It reads from the existing trail (`observability.tf:446`).
  - Target: `aws_sns_topic.alerts`, plus a topic-policy statement for `events.amazonaws.com`.
  - `aws_secretsmanager_secret_policy` that denies only GetSecretValue and PutSecretValue to every principal except the admin role (by `aws:PrincipalArn`). Do not deny Describe or GetResourcePolicy, or Terraform refresh breaks (ADR:359-360).
- **`cicd.tf` or `cicd_split.tf`:** grant `events:PutRule/DeleteRule/DescribeRule/PutTargets/RemoveTargets/ListTargetsByRule/TagResource/ListTagsForResource` on `rule/aa-identity-*`. Apply this grant locally with MFA before the rest.
- **Tests:** CI plan shows 0 changes to the pool and clients; identity-triggers-test passes.
- **Verify:** `describe-rule` shows the state. An admin reads the secret once and the SNS email arrives (CloudTrail adds a few minutes of delay).

**A1 (run, needs MFA): branding.** Run each command from the output `identity_branding_commands` (`identity.tf:972-978`) for the 3 WORKFORCE clients.
- Verify: `describe-managed-login-branding-by-client` returns a style for each client, and the authorize URL for cis-admin with `redirect_uri=http://localhost:3000/api/auth/callback/cognito` renders the v2 page.

**I2 (Infra) `chore: workforce bootstrap tool`**: `tools/identity/workforce_bootstrap.py`. Confirm it is tracked with `git ls-files`.

- Uses stdlib and boto3 only. TOTP is RFC 6238 written on `hmac`, with no pyotp.
- **`create-staff --email --groups`:** AdminCreateUser with `MessageAction=SUPPRESS` (`identity.tf:51-58`) and `email_verified=true` (`workforce.py:98-99`), then AdminAddUserToGroup. It never sets a password.
- **`breakglass-init`:**
  1. Create the user (SUPPRESS) and add it to cis-admin and booking-admin (ADR:357-358).
  2. Set a random password with AdminSetUserPassword(Permanent). This is allowed for the admin; the ban at ADR:119 is for the CIS task role only.
  3. Sign in with InitiateAuth USER_AUTH / PASSWORD on the breakglass client, with SECRET_HASH. The client secret is read with describe-user-pool-client and held in memory only.
  4. AssociateSoftwareToken, VerifySoftwareToken, then AdminSetUserMFAPreference. TOTP must be enrolled, or no MFA challenge is sent (`identity.tf:357-363`).
  5. PutSecretValue with `{username, password, totp_seed, created_at}`.
  6. RevokeToken, AdminUserGlobalSignOut, then AdminDisableUser.
  - It prints only status lines and the VersionId.
- **`breakglass-verify`:** enable, sign in with password and answer SOFTWARE_TOKEN_MFA, print only the claim summary, then revoke and disable.
- **Tests:** in `tools/identity/tests/`:
  - RFC 6238 test vectors.
  - A capsys test that no secret value appears on stdout or stderr.
  - A botocore Stubber test that SUPPRESS and `email_verified` are always sent.
  - Add the path to `identity-triggers-test.yml`.

**A2 (Nghiệp runs, needs MFA, after D1):** `breakglass-init`, then `breakglass-verify`.
- Evidence:
  - `admin-get-user` shows Enabled=false, CONFIRMED, and SOFTWARE_TOKEN_MFA enrolled.
  - `describe-secret` shows an AWSCURRENT version.
  - Alarm `aa-identity-dev-breakglass-token-issued` history shows ALARM then OK (`identity.tf:892-906`).
  - The I1 secret alert email arrived.

**A3 (spike).** Run `create-staff` for Nghiệp's own address with groups cis-admin and booking-admin. Then sign in with an email code through managed login using the localhost callback, and exchange the code locally. This answers the open question: can a user created with SUPPRESS (status FORCE_CHANGE_PASSWORD) sign in with EMAIL_OTP? If not, D4 applies.
- Evidence:
  - The user moved to CONFIRMED.
  - The decoded access token has `token_use=access`, `client_id`, `cognito:groups` and `email` (`workforce.py:119`).
  - The code was entered within 3 minutes (`identity.tf:595`).

**A4 / A5 (refusal tests):**
1. Remove the groups, try to sign in, and get `workforce_pre_token_denied` "user is in no staff group" (`workforce.py:105`). Then re-add the groups.
2. `create-staff` with `x@example.com` is refused with "admin-created user outside the staff domain" (`workforce.py:72`).
3. `SignUp` is refused with NotAuthorized (`identity.tf:348`).

**A6.** Save everything, redacted, in `docs/audits/2026-10-18-S<n>-aa854-identity-evidence/` with a root PR. Update `infra/AA-CIS-Infra/docs/implementation-notes/AA-854.md`. Then AA-854 can be marked Done according to aa-ship.

### Stage B: Phase 1 in CIS (AA-816 and readiness for cutover)

**C1 (CIS) `feat: admin_users Cognito identity columns (CIS 247)`**, plus **I4**, the byte-identical copy in Infra `db/migrations/cis/247_*.sql`, shipped the same day (LES:133).

- **New file `api/migrations/247_admin_users_identity.sql`.** One BEGIN…COMMIT block, ending with the `schema_versions` row, following the convention of `218_admin_role_content.sql:11-21`. It:
  - adds `email`, with a unique index on `lower(email)` and a CHECK that it ends in `@adventure.asia`;
  - adds `display_name`;
  - adds `cognito_iss` and `cognito_sub`, with a CHECK that both are null or both are set, and a unique index on the pair (ADR:322-332);
  - adds `last_login_at` and `is_owner boolean NOT NULL DEFAULT false` (AC:243);
  - runs `password_hash DROP NOT NULL` (`074_admin_users_jwt_auth.sql:58`);
  - creates the table `shared.staff_app_grant(admin_user_id FK, app CHECK ('booking'), role CHECK (admin|sales|contracting|content_creator), PK (admin_user_id, app))` (DEC:32; Booking `003_staff_trip_case_workflow.sql:51`);
  - keeps `role` NOT NULL (DEC:33).
- **Code:** a NULL `password_hash` must fail closed. Pass the dummy hash when the stored hash is NULL (`main.py:334`), or catch AttributeError (`auth.py:303`).
- **Tests:**
  - New `tests/integration/test_aa854_admin_users_identity.py` on real Postgres (LES:31, LES:43).
  - Update `test_aa680_booking_staff_lookup.py`.
  - A unit test that login with a NULL hash returns 401, not 500.
- **Verify:**
  - DB Migrate check, then apply.
  - Then regenerate `docs/architecture/db-schema-reference.md`.
  - The legacy UI smoke stays green.
- **Timing with X1:** land 247 before the X1 245 copy (`x1-plan.md:185, 741`). Tell the X1 lane that 245 and the 246 probe must also cover `shared.staff_app_grant` and the new columns.

**C2 (CIS) `feat: multi-issuer staff token verifier (not wired)`**

- **New `api/core/identity_verifier.py` and `identity_config.py`.** It follows ADR §8 (`0006:295-317`):
  - choose the issuer by the unverified `iss`, with one JWKS cache per issuer and no `kid` lookup across issuers;
  - RS256 only; ignore `jku`, `x5u` and `jwk`;
  - `token_use=access`, `client_id` in {cis-admin, breakglass}, no `aud` check, leeway at most 60 s;
  - refetch at most once a minute on an unknown `kid`, keep the last good key set, prefetch at startup (the JWKS goes through the NAT, ADR:588-589);
  - return a Principal `(iss, sub, client_id, groups, email)`.
  - Dev issuer and client IDs are code constants with an env override.
- **Pin `PyJWT[crypto]==2.15.1`**, the same as Booking (`requirements.txt:51`; Booking `requirements.txt:9`). The module is meant to be copied byte-identical into Booking. Do not copy the reference implementation at RES:237-249; it breaks rules 2–3.
- **Tests:** `tests/unit/test_identity_verifier.py` with a local RSA issuer, following Booking `backend/tests/staff_tokens.py:13-60`. Cases:
  - `none` / HS256 confusion;
  - wrong `iss`; a `kid` from the other issuer;
  - ID token rejected; client not allowed; expired;
  - JWKS outage keeps the last good keys; refetch rate limit.
- **Verify:** the deploy changes nothing visible, and the startup log shows the JWKS was prefetched.

**I3 (Infra) `feat: CIS task role may manage WORKFORCE staff`**: new `accounts/aa365/identity_iam.tf`.

- Inline policy on `module.ecs.task_role_name`, resource `aws_cognito_user_pool.workforce.arn`.
- Allowed actions, exactly the ADR list (ADR:117-123): AdminCreateUser, AdminAddUserToGroup, AdminRemoveUserFromGroup, AdminDisableUser, AdminEnableUser, AdminUserGlobalSignOut, ListUsers, ListUsersInGroup.
- **No AdminGetUser.** The infra reader listed it, but it counts toward MAU (ADR:445).
- Confirm the worker task definition uses the same `ecs_task` role (`modules/ecs/main.tf:115`).
- **Verify:** a probe inside the container through S3-mediated ECS exec, with the output returned through S3 (LES:14, LES:51):
  - `list_users(Limit=1)` succeeds;
  - `admin_set_user_password` on a dummy name returns AccessDenied.

**C8 (CIS) `chore: link first staff rows to their email`**: `scripts/link_staff_identity.py`, added with `git add -f` and confirmed with `git ls-files`.
- Runs through S3-mediated exec. Sets `email` and `display_name` for Nghiệp's row. The `e2e-claude-code` row is decided by D2.
- **Verify:** the S3 report shows `email` set and `cognito_sub` NULL.

**C3 (CIS) `feat: API accepts Cognito staff tokens`.** This is the main security PR.

- **`/auth/verify-admin` (`main.py:367-393`):**
  - Choose the path by `iss`. HS256 stays as it is (gated by `LEGACY_ADMIN_LOGIN_ENABLED`, default true, read with `os.environ` following `shared/jobs/worker.py:314-319`).
  - Cognito path:
    1. Require a `cis-*` group. The trigger is not client-aware: a user with only `booking-*` groups still gets a cis-admin token (`workforce.py:101-105`).
    2. Resolve the row by `(iss, sub)`. If none, link once by `lower(email)` where `cognito_sub IS NULL AND is_active`. The email claim can be trusted: the trigger checks the domain and `email_verified` first (`workforce.py:96-99`), and clients can write only `name` (`identity.tf:597-598`).
    3. Role = the highest `cis-*` group. Log a mismatch with the DB role as drift; do not deny.
    4. Set `last_login_at`. Deny when the user is inactive or unknown.
    5. The response adds `email`, `display_name` and `auth`.
  - Extend `_current_staff` and `_load_active_staff` (`main.py:348-364, 410-424`) with a 60 s cache keyed by `(iss, sub)`.
- **New pure-ASGI middleware `api/middleware/staff_bearer.py`** on `STAFF_PATH_PREFIXES` (`staff_authz.py:283`), registered after `main.py:257-258`:
  - When a Cognito Bearer token is present: verify it, resolve the row, and rewrite `x-admin-role` and `x-admin-user-id` from the verified principal, dropping whatever the client sent. Set a contextvar.
  - An invalid Bearer gets 401. No Bearer means behaviour is unchanged.
  - The 150 inline `verify_admin_secret` calls are not touched.
  - This ends header trust (`staff_authz.py:24-30`) for Bearer requests.
- **Tests:**
  - New `test_aa854_verify_admin_cognito.py` and `test_aa854_staff_bearer_middleware.py`: a forged role header is overwritten; booking-only groups get 403; an inactive row gets 401; first-link happens only once; drift is logged.
  - Update `test_aa656_staff_roles.py`, `test_s241_admin_routes_require_auth.py:46-83`, and the aa882 snapshot if it changes.
- **Verify live:**
  - Nghiệp's access token from A3 on `/auth/verify-admin` at api-cis returns 200 with role admin.
  - `cognito_sub` is now filled in the DB.
  - A forged `x-admin-role: content` sent with the Bearer token still acts as admin, and the audit actor is `admin_users.id`.

**C4 (CIS) `feat: admin sign-in through Cognito (auth code + PKCE), legacy kept`.** This includes deleting the dead files `lib/admin-auth.ts`, `components/LogoutButton.tsx` and `lib/api.ts`.

- **New `frontend/lib/cognito.ts`** (server-only): PKCE S256, state, Basic-auth token exchange, single-flight refresh through `/oauth2/token` (rotation is on, `identity.tf:588-591`), and revoke.
- **New routes:**
  - `app/api/auth/signin/cognito[-breakglass]/route.ts`;
  - `app/api/auth/callback/cognito[-breakglass]/route.ts`. These paths are fixed by `identity_variables.tf:144,148`.
  - `app/api/auth/refresh/route.ts`.
- **Cookies:**
  - `cis_admin_token` now holds the Cognito access token for 15 min.
  - New httpOnly `cis_staff_rt`, `path=/api/auth`, 12 h.
  - `cis_role` and `cis_user` are set by the server. This fixes the clash with the tenant cookie (`tenant-login/route.ts:63` vs `login/page.tsx:43`).
- **Edits to existing files:**
  - `middleware.ts:85-165`: refresh when the token is expired, and no dev fail-open on the Cognito path (`:157-164`).
  - `lib/auth-server.ts:153-184`.
  - `app/login/page.tsx`: a button, the password form only when the server flag is on, and no automatic redirect (ADR:275-277).
  - `app/api/auth/login/route.ts:35`: 404 when the flag is off.
  - `admin-logout/route.ts:21-28`: revoke, then return the Cognito `/logout` URL.
  - `Topbar.tsx:268-275`: navigate with `window.location`.
- **Tests:**
  - A full `npm run build` (LES:146-147).
  - `aa656-forged-cookie.spec.ts`: add a forged RS256 token in `cis_admin_token`.
- **Verify on `https://aa-cis.lumiguides.it.com`** (LES:34):
  - An email-code sign-in lands on the dashboard.
  - Logout does not silently sign back in.
  - The legacy smoke stays green.
  - Managed-login break-glass through `/api/auth/callback/cognito-breakglass`: the alarm fires, then disable the user again. This is the cutover precondition at ADR:390.

**C5 (CIS) `feat: BFF forwards the staff Bearer token`**: add `Authorization: Bearer` to the 5 proxies, keeping the secret for now:
- `app/api/admin/[...path]/route.ts:68-73`
- `pipeline/[...path]:36-38`
- `tour-full/[id]:28-31`
- `tenant/pipeline/brand-identity:14-20`
- `tenant/[...path]:55-64`

Verify: the count of `staff_bearer_verified` log lines is above 0, and an audit row written from the UI has the actor taken from the token.

**C6 (CIS) `feat: staff directory writes via Cognito (AA-816)`**

- **Routes** in `api/routers/admin_platform.py`: create, roles (the CIS role plus the Booking grant), disable, enable, sign-out ("reset").
- **New `api/services/staff_directory.py`:**
  - Write the DB first, then Cognito (ADR:109-115).
  - Create always uses SUPPRESS and `email_verified=true`, and refuses anything outside `@adventure.asia`.
  - Disable order: AdminDisableUser, then AdminUserGlobalSignOut (ADR:275-278).
  - A Cognito failure returns 502 "saved, Cognito pending" with an idempotent retry.
  - Guards against removing the last owner and against demoting yourself.
- **Policy:** `staff.write` requires `auth=cognito` and `is_owner` (`staff_authz.py:88-90, 263-264`). Regenerate the snapshot.
- **Audit** goes through `services/acp_shared/audit_log.py`.
- **UI:** forms on the existing staff pages. Update `lib/rbac.ts:14-21`.
- **Packaging:** add the new module to the Dockerfile `COPY` and the deploy path filter if needed (LES:61).
- **Tests:** extend `test_aa883_admin_platform.py` with Stubber (SUPPRESS always sent, non-domain addresses refused), the route-policy test, and a `staff_app_grant` integration test.
- **Verify live:** create a second staff address from the UI; that person signs in with an email code; disable them and sign-in is refused. Save screenshots.

**C7 (CIS) `feat: staff directory reconcile job`**
- A new `shared.job` kind on the worker, daily and on demand. It calls only ListUsers and ListUsersInGroup, and only reports drift.
- It shows "cutover readiness": active rows missing an email or a `cognito_sub`.
- **Verify:** a run reports 0 drift. Remove a group in the console, and the next run flags it.

**I5 (Infra) `feat: SES inbound mailbox for Cognito E2E`** (after D2), followed by **E1 (CIS) `test: cognito email-code login e2e`**.

- **I5:**
  - MX on `e2e-mail.lumiguides.it.com` pointing to `10 inbound-smtp.us-west-1.amazonaws.com`. The apex MX is Zoho (`dns.tf:37-41`) and `bounce.` is already taken (`ses.tf:157-163`).
  - A receipt rule set, its activation, and a rule writing to S3 (a new bucket with a 1-day lifecycle and a policy for `ses.amazonaws.com`).
  - CI grants for the receipt-rule actions; today the role has only identity and configuration-set actions (`cicd_split.tf:607-613`).
  - An OIDC read role limited to that bucket, subject `environment:e2e`.
  - Only if D2 picks (b): `EXTRA_ALLOWED_EMAIL_DOMAINS` on the trigger (`identity.tf:180`, `workforce.py:71,96`), with a dev-only precondition and tests.
- **E1:**
  - `tests/e2e/cognito/cognito-login.spec.ts` and `tests/e2e/helpers/mailbox.ts`.
  - New workflow `cognito-e2e.yml`: production domain only, the user is in `cis-reviewer`, never break-glass (`workforce.py:107-114`), and it finishes within 3 minutes.
  - **Verify:** one green CI run (LES:138-140).

**R1 (root) `docs: ADR 0006 amendment (Phase 1)`.** Updates `docs/adr/0006-ecosystem-identity.md`:
- the `staff_app_grant` table (replacing ADR:106-107, 390);
- owner-only `staff.write` through `is_owner`, with no `platform-admin` group;
- "reset" means sign-out plus re-enable;
- remove Google (ADR:154, 179-194);
- the split of the legacy flag (D3);
- the break-glass address and its secret's JSON shape;
- the runbook for enabling and disabling break-glass.

The same PR also updates CIS `CONTEXT.md:454-505`, `docs/ecosystem-architecture.md:226`, the backlog, and implementation notes `AA-854.md` and `AA-816.md` in each repo.

### Stage S: cutover (gated, probably not this session)

**Preconditions (ADR:390):**
- Every active row has an `@adventure.asia` email.
- Every active row has a `cognito_sub` from that person's own sign-in. C7 shows 0 missing.
- Managed-login break-glass has been tested.

**Steps:**
1. **C9 (CIS):** a contextvar check in `verify_admin_secret` (`admin.py:113-117`) and its variants (`admin_settings.py:29-33`, `v1_pipeline.py:43-58`, `core/staff_secret.py:33-48`, `admin_atoms.py:84-102`). The BFF stops sending the secret for Cognito sessions.
2. **I6 (Infra):** rotate `ADMIN_SECRET`, and move the plaintext copy at `dfs_balance.tf:161` to a secret reference.
3. Set `LEGACY_ADMIN_LOGIN_ENABLED=false` for the CIS UI and the HS256 path in verify-admin only.
4. `/auth/admin-login` and `/auth/booking-token` stay on until Booking Phase 2. Booking signs in through them (`AA-Booking/frontend/app/api/auth/login/route.ts:49`; `main.py:432`).
5. Disable the legacy `e2e-claude-code` row, and switch the smoke tests to E1.

### Stage D: Booking Phase 2 is deferred

Booking cannot accept Cognito by configuration alone:
- it supports one issuer only (`tokens.py:133-136`);
- it requires `aud` (`:150-158`);
- it requires a `cis_role` claim (`:165-166`).

About 27 foreign keys point at `cis_user_id`, and bridge tokens carry no `email` (`booking_jwt.py:192-203`). Optional next PR: a byte copy of C2 into Booking that resolves only rows already linked, with no auto-provisioning. Add bk-014 identity-link columns once the role-source decision is made (`owners.yaml:140`).

## 3. Infra changes and monthly cost

| Change | Monthly cost |
|---|---|
| Branding (A1), Essentials MAU (about 6 users), task-role IAM, secret policy | $0 |
| EventBridge rule on the existing trail, plus SNS email | $0 |
| SES outbound email codes | under $0.05 |
| SES inbound, S3 with 1-day lifecycle, MX record (I5) | under $0.05 |
| Break-glass secret (already exists) | $0.40, already paid |

**New spend is about $0.10 a month.** WAF stays off; turning it on would add about $7 a month (`identity_variables.tf:171-174`).

## 4. True human blockers

- **D1 (blocks I1 and A2): break-glass address.** The username is the email, and `admin@adventure.asia` is both the break-glass default (`identity_variables.tf:14-18`, DEC:41) and Nghiệp's own address.
  - Recommendation: `breakglass@adventure.asia` with no mailbox, so the only way in is password + TOTP. Nghiệp keeps `admin@`.
- **D2 (blocks I5, E1 and the cutover): mailbox for the E2E email codes.**
  - (a) A Workspace forward from `e2e-cognito@adventure.asia` to the SES inbound address. Recommended, because the domain rule stays intact.
  - (b) A dev-only extra domain in the trigger.
- **D3: split the legacy flag** (Booking keeps admin-login and booking-token). This goes into R1.
- **D4: only if the A3 spike fails.** The directory's create flow then needs a random permanent password, which goes against ADR:119.
- **Manual actions:**
  - Local MFA apply of the I1 CI grants, then the Terraform applies.
  - A1 branding.
  - `breakglass-init` and `breakglass-verify`.
  - Vercel env. ⚠️ This contains underscore env vars — edit manually in VSCode: `COGNITO_CIS_ADMIN_CLIENT_SECRET`, `COGNITO_BREAKGLASS_CLIENT_SECRET`, `LEGACY_ADMIN_LOGIN_ENABLED` (it stays true on Preview). Do this early in the day because of the deploy limit (LES:69). The secrets come from describe-user-pool-client; Terraform does not output them (`identity.tf:911`).

## 5. Risks

1. **Lock-out.** Legacy login stays on until Stage S. Break-glass is verified twice (through the API in A2 and through managed login after C4). Rolling back is one Vercel env change and a redeploy.
2. **Missing branding** makes managed login fail. Run A1 before any test.
3. **SUPPRESS + EMAIL_OTP not proven** (the pool has 0 users). If A3 fails, D4 applies.
4. **The secret resource policy could deny the wrong principal.** Deny only Get/PutSecretValue, and check on plan that the admin role ARN matches the assumed-role session.
5. **Ordering with X1.** If 247 lands after 245, it needs `SET LOCAL ROLE cis_owner`. 245 and 246 must cover the new table. Do not stack I3 with the X1 task-def/SG PRs; apply them one after the other.
6. **A booking-only user still gets a cis-admin token.** C3 must deny without a `cis-*` group.
7. **Break-glass can sign in through the cis-admin client;** the client restriction is procedure only (`identity.tf:71-73`). The alarm still fires, so treat any `client_id` other than breakglass in that log line as an incident.
8. **Refresh races** with about 8 parallel calls (`auth-server.ts:18-28`) under the 60 s rotation grace. Refresh only in middleware or the single-flight route.
9. **Header trust remains for legacy and secret-only requests** until C9. Keep that window short.
10. **The 3-minute auth session** limits how slow mail delivery plus polling can be in E1.
11. **ECS exec cuts output off silently** (LES:51/77). Return probe and link output through S3.
12. **A disabled user keeps a valid token for up to 15 minutes**, which ADR:266 accepts.

## 6. Facts appendix

- **Pool:** us-west-1_bCcFvbSOS.
  - Issuer: `https://cognito-idp.us-west-1.amazonaws.com/us-west-1_bCcFvbSOS`. Check it against `/.well-known/openid-configuration` (`identity.tf:907-908`).
  - Hosted domain: `https://aa365-staff-auth-dev.auth.us-west-1.amazoncognito.com`.
- **Client IDs:**
  - cis-admin: `3oqkumijh04cp81k3nlnub6qtv`
  - booking-staff: `5ifl9dgkr8a5outnmsjc8v1kt3`
  - breakglass: `2g3f3ncfuqdiuu1o5b70o4h0lq`
- **Client settings:**
  - Flow `code`, scopes `openid email profile`, `ALLOW_USER_AUTH` only, refresh-token rotation with 60 s grace, revocation on, `auth_session_validity` 3 (`identity.tf:571-599`).
  - Access token 15 min. Refresh 12 h, or 1 h for breakglass.
  - Pool is admin-create only (`:348`); MFA OPTIONAL with TOTP (`:357-363`).
- **Callback URLs** (`identity_variables.tf:143-154`):
  - cis-admin: `https://aa-cis.lumiguides.it.com/api/auth/callback/cognito` and `http://localhost:3000/api/auth/callback/cognito`; logout `/login`.
  - breakglass: `https://aa-cis.lumiguides.it.com/api/auth/callback/cognito-breakglass` only.
  - booking-staff: still localhost:3001; changed in I1.
- **Trigger** (`workforce.py`):
  - out-of-domain create refused at `:71-72`;
  - domain and `email_verified` checks at `:96-99`;
  - no staff group denied at `:104-105`;
  - break-glass log line at `:107-114`;
  - `email` added to the access token at `:119`.
- **Migrations:**
  - CIS head is 243 in both CIS and Infra. X1 reserves 244, 245 and 246. Phase 1 uses 247.
  - Role lint: CIS from 243 (`owners.yaml:85`), Booking from 14 (`:140`).
- **Env var names:**
  - Backend: `LEGACY_ADMIN_LOGIN_ENABLED`, default true, read with `os.environ`. The Cognito issuer and client values are code constants with an env override, so the task definitions need no new values.
  - BFF: `COGNITO_CIS_ADMIN_CLIENT_SECRET`, `COGNITO_BREAKGLASS_CLIENT_SECRET`, `LEGACY_ADMIN_LOGIN_ENABLED`.
  - Existing: `ADMIN_SECRET` and `JWT_SECRET` (`modules/ecs/main.tf:402-403, 603-604`).
- **CIS anchors:**
  - `/auth/admin-login` at `main.py:313-343` (password check at `:334`); `/auth/verify-admin` at `:367-393`; `/auth/booking-token` at `:427-454`.
  - Rate limiter registered at `main.py:257`.
  - `_verify_password` at `auth.py:299-305`.
  - `staff_authz.py`: header trust at `:24-30`, `OWNER_PERMS` at `:88-90`, staff-directory policy at `:263-264`, prefixes at `:283`, machine routes at `:288-298`.
  - `admin_platform.py:35-82`.
- **Infra anchors:**
  - CIS task role: `modules/ecs/main.tf:115`, output at `outputs.tf:18`.
  - Existing trail: `observability.tf:446`.
  - Break-glass secret: `identity.tf:779-784`; its alarm: `:892-906`.
  - Branding output: `:972-978`.
  - CI role has no EventBridge grant (`cicd.tf:376-381`); SES grants at `cicd_split.tf:607-613`.
  - Plaintext `ADMIN_SECRET` in the Lambda env: `dfs_balance.tf:161`.
  - Provider lock: aws 5.100.0.