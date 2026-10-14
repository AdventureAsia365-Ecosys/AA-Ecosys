# Amazon Cognito user pools — research for AA-703 (ecosystem identity)

- Date: 14/10/2026 (S236). Author: Claude Code (research subagent).
- Scope: two pools in acc2 (005097885195, us-west-1). WORKFORCE holds staff for CIS and Booking. EXTERNAL holds tenant users and travellers for TripPlanner and Booking.
- Sources: primary only. AWS documentation and pricing pages, Google Identity docs for the `hd` claim, and the HashiCorp provider repo for Terraform. Each fact has its URL. Lines marked **[inference]** are our own design conclusions. Lines marked **[unverified]** need a spike.

---

## 1. Feature plans: Lite, Essentials, Plus

Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html

- The plan is set per user pool through `UserPoolTier`. A new pool defaults to **Essentials**. Setting `AdvancedSecurityMode` to `AUDIT` or `ENFORCED` requires `PLUS`. The plan can be changed at any time, but some changes require turning features off first.

| Feature | Lite | Essentials | Plus |
|---|---|---|---|
| Sign-up/sign-in, groups, social/SAML/OIDC federation, OIDC issuer, M2M, resource servers, user import | yes | yes | yes |
| Classic hosted UI and CSS customisation | yes | yes | yes |
| **Managed login** (new UI) plus the **visual branding editor** | – | yes | yes |
| **Passwordless first factor: EMAIL_OTP / SMS_OTP** ("choice-based sign-in", `USER_AUTH`) | – | yes | yes |
| **Passkeys (WebAuthn)** as first factor | – | yes | yes |
| Email MFA | – | yes | yes |
| Access-token customisation (pre token generation V2_0/V3_0) | – | yes | yes |
| ID-token customisation (pre token V1_0), all other Lambda triggers | yes | yes | yes |
| Step-up auth (`acr_values`, `TARGET_ACR_VALUES`) | – | yes | yes |
| **Threat protection**: compromised-credential check, adaptive/risk-based sign-in, user activity logs and export | – | – | yes |

- Choice-based sign-in needs **both** the `ALLOW_USER_AUTH` flow on the app client **and** `Policies.SignInPolicy.AllowedFirstAuthFactors`, which takes `PASSWORD`, `EMAIL_OTP`, `SMS_OTP` and `WEB_AUTHN`. Source: https://docs.aws.amazon.com/cognito/latest/developerguide/authentication-flows-selection-sdk.html
- **EMAIL_OTP requires the Essentials plan or higher and the Amazon SES email configuration (`DEVELOPER`).** It does not work with the default Cognito email sender. Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-email.html (message options table, footnote 1).
- Passwordless OTP and MFA interact as follows. Source: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-authentication-flow-methods.html
  - OTP sign-in "isn't compatible with **required** MFA".
  - When MFA is optional, a user who has activated MFA **can't** use an OTP first factor.
  - A passkey with user verification can satisfy MFA when `FactorConfiguration=MULTI_FACTOR_WITH_USER_VERIFICATION`.
  - Users can sign up and be created by an admin **without a password**.
  - A correct OTP marks the email as verified and sets the user to CONFIRMED.
- Passkey rules (same source):
  - Each user can register up to 20 passkeys, and only after their first sign-in.
  - The RP ID defaults to the **custom domain FQDN** when one exists. Otherwise it is the prefix domain. It can also be "a domain of your own choosing" through `WebAuthnConfiguration.RelyingPartyId`.
  - Managed login prompts a new user to register a passkey after sign-up.
- Managed login branding:
  - Styles are created per app client, with up to 20 styles per pool.
  - Text can't be edited. Localisation is chosen with the `?lang=` parameter on the authorize URL.
  - The API is `CreateManagedLoginBranding` / `UpdateManagedLoginBranding`. Requests are limited to 2 MB and use a PATCH model.
  - Source: https://docs.aws.amazon.com/cognito/latest/developerguide/managed-login-brandingeditor.html

**[inference]** Both pools need **Essentials**, because email OTP, managed login and access-token claims are all Essentials features. Plus is worth considering only for WORKFORCE, for compromised-credential and risk detection. At 31 MAU it would cost about $0.62 per month. Plus would add nothing for Google sign-ins, because Google already protects those.

## 2. Pricing (as of 14/10/2026) and cost estimate

Source: https://aws.amazon.com/cognito/pricing/

| Item | Price |
|---|---|
| Essentials | **10,000 MAU free per month, per account or per AWS organization** (not per pool, and it does not expire). Above that, **$0.015/MAU** |
| Plus | **No free tier. $0.020/MAU** |
| Lite | 10,000 MAU free. The worked example bills $0.0055/MAU at first, then $0.0046 at volume. Formal breakpoints aren't listed |
| Social IdPs (**Google, Facebook**, Apple, Amazon) | **Billed as ordinary direct MAU**, not as federated MAU |
| SAML/OIDC federated MAU | 50 MAU free per account or organization, then $0.015/MAU on every plan. (This does not affect us unless Google is configured as generic OIDC; see §3.) |
| Linked users | A user profile with zero or more linked federated identities counts as **1 MAU**. Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-identity-federation-consolidate-users.html |
| M2M | Charged per token request, e.g. $0.00225. No free tier |
| Email (SES, à la carte) | **$0.10 per 1,000 emails**. Source: https://aws.amazon.com/ses/pricing/ |
| Legacy ASF add-on (Lite) | $0.05/MAU for the first 50k. This is superseded by Plus |

What counts as an MAU: any identity operation for the user in the calendar month, such as sign-up, sign-in, refresh or sign-out. CSV import does not count, and neither does `ListUsers`. `AdminGetUser` **does** count. Source: https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html#monthly-active-users

**Estimate.** Both pools are on Essentials and sit in the same account, so they share the 10,000 free MAU:

| Scenario | WORKFORCE | EXTERNAL | Billable MAU | Cognito $/mo | OTP email (SES) |
|---|---|---|---|---|---|
| A: 30 staff + 1 break-glass, 50 tenant users, **2,000** travellers | 31 | 2,050 | 0 (2,081 < 10k) | **$0** | ~2,100×3 mails ≈ 6.3k → **$0.63** |
| B: same, **20,000** travellers | 31 | 20,050 | 10,081 | 10,081 × 0.015 = **$151.22** | ~60k mails → **$6** |
| B with WORKFORCE on **Plus** | 31 × $0.02 = $0.62 | 20,050 | EXTERNAL 10,050 billable | ≈ **$151.37** | same |

**[inference]** The OTP mail count assumes about 3 emails per active traveller per month. Lambda triggers add pennies at this volume.

## 3. Restricting Google to the Workspace domain plus an allow-list; account linking

### What Cognito can and can't do

- Cognito **can't forward `hd`** to Google.
  - `/oauth2/authorize` forwards `prompt` (all values except `none`).
  - `login_hint` is forwarded only to OIDC IdPs: "You can't forward login hints to SAML, Apple, Login With Amazon, Google, or Facebook (Meta) IdPs."
  - No generic parameter pass-through is documented.
  - Source: https://docs.aws.amazon.com/cognito/latest/developerguide/authorization-endpoint.html
- Even if `hd` could be sent, Google says the `hd` request parameter is only a UI hint: "Don't rely on this UI optimization to control who can access your app". The **`hd` claim in the ID token** is authoritative: "You must check this claim when restricting access…". Google also warns: "You also can't rely on the domain of the email claim to identify users of Google Workspace… use `hd`", and recommends `sub`, not email, as the identifier. Source: https://developers.google.com/identity/openid-connect/openid-connect
- Google IdP setup:
  - Redirect URI: `https://<domain>/oauth2/idpresponse`.
  - Scopes: `profile email openid`.
  - **Map `email_verified`.** If it isn't mapped, Cognito treats the email as unverified.
  - Keep to the basic scopes to avoid the unverified-app cap of 100 users.
  - "Amazon Cognito doesn't automatically merge a Google user with an existing user that has the same email."
  - Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-social-idp-google.html

### Triggers that can enforce the rule

| Trigger | When it fires for Google users | What it can do |
|---|---|---|
| **Inbound federation** (`InboundFederation_ExternalProvider`) | **Every** federated sign-in, before the profile is created or updated | Receives the **raw `idToken` claims, so `hd` is available**, plus `userInfo` and `tokenResponse`. Returns `userAttributesToMap`. Lets us copy `hd` into `custom:hd`. Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-inbound-federation.html. **⚠ Terraform does not support it (see §6).** |
| **Pre sign-up** (`PreSignUp_ExternalProvider`) | **First** federated sign-in only | Receives mapped `userAttributes`. Throwing an error **denies** the sign-up. It can call `AdminLinkProviderForUser` to link to a pre-created native profile. Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-sign-up.html |
| **Pre authentication** | Subsequent federated sign-ins | Can deny by throwing an error. It does **not** fire on session renewal or refresh. Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-authentication.html |
| **Pre token generation** | Every token issue: `TokenGeneration_HostedAuth` (federated), `TokenGeneration_Authentication`, `TokenGeneration_RefreshTokens` | Throwing an error stops tokens from being issued. It can set `cognito:groups` and add claims. V2_0/V3_0 can also modify the access token (Essentials). Source: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html |

Trigger limits. Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-working-with-lambda-triggers.html
- Invocation is synchronous, with a **5-second timeout that can't be changed**. Cognito may retry. It does not retry on 5xx Invoke errors.
- An error message is shown to the user: managed login displays it above the form, and the API returns `"<trigger> failed with error <text>"`. **Don't put sensitive information in error messages.**
- A function version can be pinned only through an alias ARN in the API, not in the console.
- The Lambda resource policy must allow `cognito-idp.amazonaws.com` with `SourceArn`/`SourceAccount` conditions.
- Federated sign-in never invokes the custom-auth, migrate-user, custom-message or custom-sender triggers.
- Pre-token generation: at most **5,000 combined claims and scopes** per transaction (adjustable). Claims that can't be modified: `iss`, `aud` (ID token), `client_id`, `token_use`, `sub`, `username`, `cognito:username`, `identities`, `exp`/`iat`/`auth_time`. Groups are changed through `groupOverrideDetails`. In V2+, `aud` can be added to the access token, but only with the value of the current client ID.

### Account linking (federated to native, by email)

Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-identity-federation-consolidate-users.html
- `AdminLinkProviderForUser` must be called **before the federated user's first sign-in**, either in a pre-staging job or in a pre sign-up trigger. For a social IdP, use `ProviderAttributeName=Cognito_Subject` and the Google `sub` as the value.
- After that, the user "always signs in to that profile". The ID token's `identities` claim lists the linked providers.
- To link a user who already signed in federated, you **must delete** the auto-created `Google_<sub>` profile first.
- Limits: at most **5 linked identities per user**, and only 5 distinct source attribute names per IdP. Linking can't be done in the console.
- Security warning: use linking "only with external IdPs and provider attributes that have been trusted". Only link on trusted `email_verified=true`.
- **Facebook returns no `email_verified`.** Cognito treats a Facebook email as unverified, so never auto-link by a Facebook email. Facebook also needs Live mode, Business Verification and Advanced Access for `email`. Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-social-idp-facebook.html

### [inference] Recommended WORKFORCE pattern

1. A staff-directory job, owned by the AA-816 admin UI, calls `AdminCreateUser` for each staff member. It sets `email` = `@adventure.asia`, `email_verified=true`, suppresses the invite, sets no password, and adds the user to groups such as `cis-admin` or `booking-sales`.
   - `admin_create_user_config.allow_admin_create_user_only = true`, so there is no self-service sign-up.
   - The native profile is what makes **EMAIL_OTP the fallback**.
2. **Pre sign-up** (`PreSignUp_ExternalProvider`):
   - Require `email_verified=true`, and require the email to match an existing enabled native user. Otherwise throw "Not authorised".
   - Then call `AdminLinkProviderForUser(destination=native, source=Google/Cognito_Subject=<sub>)`.
   - The `hd` check belongs here too, but `hd` is not a mappable attribute unless it is mapped to `custom:hd`. Google attribute mapping supports arbitrary provider attributes, but that needs verifying. The Inbound federation trigger is the documented way to read `hd`. **[unverified: whether `hd` can be mapped directly in the Google attribute mapping]**
3. **Pre token generation** (V2_0) runs on every issue, refresh included. Re-check that the user is enabled and on the allow-list, read roles from the directory, and set `cognito:groups`. This closes the gap where pre authentication doesn't fire on refresh.
4. Offboarding: `AdminDisableUser` plus `AdminUserGlobalSignOut`. Keep access tokens short-lived (15–60 min), because offline JWT checks can't detect revocation (see §7).
5. Break-glass: one native user with a strong password and TOTP MFA (MFA optional at pool level). Store the credential in Secrets Manager, not in Google. An MFA-enabled user can't use OTP, which is the intended behaviour here.

**[unverified, spike]** Confirm with a real Google sign-in that linking in pre sign-up works on the very first sign-in, with no "already found an entry" error. AWS documents this path, but it must be tested before we rely on it.

### [inference] EXTERNAL pool: conflict between invite-only and self-sign-up

`allow_admin_create_user_only` is **pool-wide**. Tenant users must be invite-only, but travellers must be able to sign up themselves. The options are:

- (a) **One pool, two app clients.** The pre sign-up trigger checks `callerContext.clientId`. It rejects self sign-up on the tenant-portal client, and on the traveller client it lets federated or OTP sign-up through.
- (b) Split into **three pools**. There is no extra cost, because the free tier is per account.

Tenant scope (owner/editor/viewer per tenant) should stay in the app database (CIS tenant membership). Pre-token generation can inject a `tenants` claim, or the app can resolve membership from `sub`. Groups such as `tenant:<id>:owner` hit the hard cap of **100 groups per user** and 10,000 per pool, so they should not carry tenant scope.

Linking a TripPlanner guest by verified email: only native EMAIL_OTP or Google `email_verified=true` emails qualify. Facebook emails do not.

## 4. Email sending for OTP: default sender vs SES

Sources: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-email.html and https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html

- **The default (`COGNITO_DEFAULT`) sender is limited to 50 emails per day per AWS account.** The limit can't be raised and resets at 09:00 UTC. The sender is `no-reply@verificationemail.com`, and bounces go to an AWS-managed suppression list we can't control. AWS says the default "is below the required delivery volume" for typical production.
- **EMAIL_OTP and email MFA require the SES (`DEVELOPER`) configuration.**
- **SES region for a us-west-1 pool is "In-Region only"**, so the verified SES identity must be in **us-west-1**. Other regions (for example Oregon or Virginia) are not allowed.
- SES identity requirements:
  - Verify a domain or address in SES us-west-1. DKIM on the sending domain is recommended.
  - **Move the account out of the SES sandbox in us-west-1.** Sandbox mode can only send to verified addresses.
  - Choosing `DEVELOPER` makes Cognito create a service-linked role, so the caller needs `iam:CreateServiceLinkedRole`.
  - An optional configuration set is supported.
  - The FROM address must be in the verified identity. When the identity is a domain, the FROM address must be set explicitly.
  - Resources can't be shared across accounts, so the SES identity must be in acc2.
- With SES, delivery limits are the account's SES limits, and an account-level suppression list is available.
- Code-level limits:
  - Email MFA: **5–20 messages per address per hour per requester IP**.
  - MFA/OTP code validity is 3–15 minutes.
  - `ResendConfirmationCode` is limited to 5 per user per hour.
- Branded or localised mail: use the custom message trigger (templates) or the custom email sender trigger, which takes `lambda_version` V1_0 and a KMS key.

**[inference]** AA-811 (SES email) is a **hard prerequisite** for the OTP part of AA-703. The SES domain identity must be in acc2 **us-west-1** and out of the sandbox before any EMAIL_OTP testing goes beyond verified addresses.

## 5. Custom domain for managed login (lumiguides.it.com)

Source: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-add-custom-domain.html

- **The ACM certificate must be in us-east-1 (N. Virginia)**, whatever region the pool is in, because Cognito fronts the domain with a CloudFront distribution that AWS manages. The cert must be public and issued in acc2.
- **The parent domain must have a valid DNS A record.** For `auth.lumiguides.it.com`, `lumiguides.it.com` must resolve. An SOA record alone doesn't count. TLDs aren't allowed.
- DNS: create an A-alias (Route 53) or CNAME to the CloudFront alias target. Route 53 propagation takes about 60 seconds. A certificate swap takes up to 1 hour.
- Managed login (version 2) requires TLS policy `TLS_V1_2_2021` or stricter (`TLS_V1_3_2025`).
- Cognito sets cookies (`cognito`, `cognito-fl`, `XSRF-TOKEN`). The app should not set its own cookies on the auth subdomain.
- `/.well-known/openid-configuration` is served **only on the custom domain** when both domain types exist.
- One domain per pool, and a pool's branding version (managed login or hosted UI) applies to all its clients. **Custom domains: 4 per region per account (hard limit).** Two pools use two of the four.
- Google and Facebook must register `https://<custom-domain>/oauth2/idpresponse` and add the root domain under Authorized domains.

**[inference]** Proposed names are `auth.lumiguides.it.com` (EXTERNAL) and `staff-auth.lumiguides.it.com` (WORKFORCE). Check that the apex `lumiguides.it.com` has an A record first. Passkeys are bound to the RP ID, which defaults to the custom domain. Moving to a production domain later (such as adventure.asia) would orphan existing passkeys, so we should **wait to enable passkeys until the production domain is fixed**, or set the RP ID deliberately.

## 6. Terraform (hashicorp/aws)

Sources: provider docs at https://github.com/hashicorp/terraform-provider-aws/tree/main/website/docs/r/ (files `cognito_*.html.markdown`) and the CHANGELOGs (main branch and `release/5.x`). The latest release is **v6.68.0 (07/10/2026)**.

| Need | Resource / argument | Since |
|---|---|---|
| Pool, plan | `aws_cognito_user_pool.user_pool_tier` (`LITE`/`ESSENTIALS`/`PLUS`) | 5.83.0 |
| Passwordless / passkeys | `sign_in_policy.allowed_first_auth_factors`, `web_authn_configuration{relying_party_id,user_verification}` | 5.83.0 |
| Email via SES | `email_configuration{email_sending_account="DEVELOPER", source_arn, from_email_address, configuration_set}`, `email_mfa_configuration` | – |
| Triggers | `lambda_config{pre_sign_up, pre_authentication, post_confirmation, pre_token_generation_config{lambda_arn, lambda_version=V2_0}, custom_email_sender, custom_message, …}` plus `aws_lambda_permission` | – |
| Invite-only | `admin_create_user_config.allow_admin_create_user_only` | – |
| Safety | `deletion_protection = "ACTIVE"` | – |
| App clients | `aws_cognito_user_pool_client` (`explicit_auth_flows` incl. `ALLOW_USER_AUTH`, `supported_identity_providers`, `refresh_token_rotation`, callback/logout URLs, token validity) | `refresh_token_rotation` 5.95.0 |
| Google/Facebook | `aws_cognito_identity_provider` (`provider_details{client_id, client_secret, authorize_scopes}`, `attribute_mapping`) | – |
| Domain | `aws_cognito_user_pool_domain{domain, certificate_arn (us-east-1), managed_login_version=2}`. Exports `cloudfront_distribution`/`_zone_id` for the Route 53 alias | `managed_login_version` 5.95.0 |
| Branding | `aws_cognito_managed_login_branding{user_pool_id, client_id, settings (JSON), asset{…}, use_cognito_provided_values}` | **6.12.0** (Sep 2025) |
| Groups / users | `aws_cognito_user_group`, `aws_cognito_user`, `aws_cognito_user_in_group` | – |
| Others | `aws_cognito_resource_server`, `aws_cognito_risk_configuration` (Plus), `aws_cognito_log_delivery_configuration` | – |

Known gaps and traps:
- **The Infra repo pins `hashicorp/aws ~> 5.40`, locked at 5.100.0** (`infra/AA-CIS-Infra/accounts/aa365/versions.tf`). Managed login branding needs **v6.12+**, which means a major 5 → 6 upgrade, or managing branding through the CLI or console. Everything else in the table works on 5.100.
- **The Inbound federation trigger is not supported** in `lambda_config`. There is an open PR (#47954) and issue (#46216). Issue **#49707, "Terraform apply silently drops Inbound Federation Cognito Trigger"**: if the trigger is set out-of-band, the next `apply` removes it. This makes the trigger unsafe to depend on until the PR merges. Pre sign-up and pre-token generation can be used instead.
- **No `security_policy` (minimum TLS) on `aws_cognito_user_pool_domain`.** There is an open issue (#48731) and PR (#48870). The default applies.
- `schema` attributes can be added but **never modified or removed**. A wrong `custom:` attribute would stay forever.
- Removing `sms_configuration` forces the pool to be recreated.
- `password_history_size` needs advanced security.
- The `settings` keys for branding are not documented in the provider. Export them from `DescribeManagedLoginBrandingByClient` and adapt.
- The `asset` argument name is inconsistent in the docs (`extension` vs `extensions`).
- `custom_email_sender` supports only `V1_0` and needs `kms_key_id`.

## 7. JWT claims and FastAPI verification

Source: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html

- Algorithm and keys: **RS256**. The JWKS is at `https://cognito-idp.us-west-1.amazonaws.com/<poolId>/.well-known/jwks.json`. There are separate keys for ID and access tokens. Cache the keys by `kid` and refetch when an unknown `kid` arrives, because keys may rotate.
- `iss` = `https://cognito-idp.us-west-1.amazonaws.com/<poolId>`. This is the region endpoint, **not** the custom domain.
- **ID token:** `aud` = app client ID, `token_use=id`. It carries user attributes, `cognito:groups`, `cognito:username` and `identities`.
- **Access token:** **no `aud`** and `client_id` = app client ID. `token_use=access`, plus `scope`, `cognito:groups`, `username` and `sub`.
  - **Exception: resource binding.** `/oauth2/authorize?resource=https://api-booking.lumiguides.it.com` (RFC 8707) sets the access token's `aud` to that resource URL. Source: https://docs.aws.amazon.com/cognito/latest/developerguide/authorization-endpoint.html
  - API Gateway JWT authorizers match `aud`, or `client_id` when `aud` is missing.
- Checks to apply:
  1. Signature against the JWKS.
  2. `exp`.
  3. `iss`.
  4. `token_use`.
  5. `client_id` (access) or `aud` (ID) in the allowed client list, or the resource URL in `aud` when resource binding is used.
  6. Scopes and groups as needed.
- **Revocation can't be detected offline.** Keep access-token lifetimes short. ID and access tokens last 5 min to 1 day, refresh tokens 1 h to 3,650 days. Source: https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html
- AWS recommends `aws-jwt-verify` for Node.js (useful for the Next.js BFF). In Python, any OIDC-compliant library works.

**[inference]** A FastAPI verifier for CIS, Booking and TripPlanner should be **config-driven**, so the interim bridge (CIS RS256 token, `aud=booking`, PR #721) and Cognito share one verifier:

```python
# settings (one per accepted issuer): ISSUER, JWKS_URL, AUDIENCES (set), AUD_CLAIM ("aud" | "client_id"),
#                                     TOKEN_USE ("access" | None), ROLES_CLAIM ("cognito:groups" | "role")
jwks = jwt.PyJWKClient(JWKS_URL, cache_keys=True, lifespan=3600)
def verify(token: str) -> Principal:
    key = jwks.get_signing_key_from_jwt(token).key
    claims = jwt.decode(token, key, algorithms=["RS256"], issuer=ISSUER,
                        options={"verify_aud": AUD_CLAIM == "aud", "require": ["exp", "iss", "sub"]},
                        audience=list(AUDIENCES) if AUD_CLAIM == "aud" else None)
    if AUD_CLAIM == "client_id" and claims.get("client_id") not in AUDIENCES: raise Unauthorized
    if TOKEN_USE and claims.get("token_use") != TOKEN_USE: raise Unauthorized
    return Principal(sub=claims["sub"], roles=claims.get(ROLES_CLAIM, []), raw=claims)
```

Switching the bridge to Cognito then means changing `ISSUER`, `JWKS_URL` and `AUDIENCES`, with no code change. Both issuers can be accepted during the cutover. Use access tokens for APIs, not ID tokens.

## 8. Quotas relevant to us

Source: https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html. Request-rate quotas are per account per region, pooled across all pools.

| Quota | Value | Adjustable |
|---|---|---|
| UserAuthentication (InitiateAuth, RespondToAuthChallenge, refresh, managed-login sign-in) | 120 RPS | yes |
| UserFederation (Google/Facebook callbacks) | 25 RPS | yes |
| UserCreation (SignUp, AdminCreateUser, Confirm) | 50 RPS | yes |
| UserRead (AdminGetUser, GetUser) | 120 RPS | yes |
| UserUpdate (AdminLinkProviderForUser, AdminAddUserToGroup, AdminDisableUser, GlobalSignOut…) | **25 RPS** | **no** |
| UserList (ListUsers) | 30 RPS | no |
| UserAccountRecovery | 30 RPS | no |
| Per-user read and write | 10 ops/s each | – |
| Managed-login domain | 500 RPS per domain, 300 per source IP, 300 per app client | no |
| App clients / pool | 1,000 | yes |
| User pools / region | 1,000 | yes |
| IdPs / pool | 300 | yes |
| Users / pool | 40M | yes |
| Custom attributes / pool | **50 (immutable once created)** | no |
| Groups / pool, groups / user | 10,000 / **100** | no |
| Linked identities / user | **5** | no |
| Passkeys / user | 20 | no |
| Callback / logout URLs per client | 100 / 100 | no |
| **Custom domains / region** | **4** | no |
| Branding styles / pool | 20 | no |
| **Default-sender email** | **50 / day / account** | no |
| Email MFA per address per hour per IP | 5–20 | no |
| Pre-token claims + scopes per transaction | 5,000 | yes |
| Lambda trigger timeout | **5 s** | no |

At our scale (less than 25k MAU), every default limit is ample. AWS says accounts under 2M MAU fit the default quotas. The quotas that matter are design limits, not throughput: 100 groups per user, 5 linked identities, 50 custom attributes, 4 custom domains, and 50 emails per day on the default sender.

---

## Open items / spikes before AA-703 build
1. SES domain identity in **acc2 us-west-1**, DKIM, and leaving the sandbox (AA-811). This blocks EMAIL_OTP.
2. ACM cert in **us-east-1** for the auth subdomains, plus an A record on the parent domain.
3. Decide on the EXTERNAL pool: one pool with a client-aware pre sign-up, or separate tenant and traveller pools.
4. Spike: Google first sign-in with pre sign-up linking to a pre-created native user. Also test the `hd` mapping without the Inbound federation trigger.
5. Terraform: bump the AWS provider from 5.100 to 6.x (for branding), or keep branding out of Terraform. Avoid the Inbound federation trigger until provider PR #47954 ships.
6. Shared config-driven JWT verifier library for FastAPI (CIS, Booking, TripPlanner Lambdas), compatible with the PR #721 bridge.
