# AA-854 evidence — Cognito Phase 0 finished on Dev (S242, 18/10/2026)

Agent: Claude Code. Account 005097885195 (acc2), us-west-1. WORKFORCE pool `us-west-1_bCcFvbSOS`
(`aa-workforce-dev`), EXTERNAL pool `us-west-1_nKOvHan0W` (applied S241, Infra #162).
No secret value appears in this file or in the session transcript.

## Done-when checklist

| # | Condition (AA-854) | Result |
|---|---|---|
| 1 | `list-user-pools` lists aa-workforce and aa-external | ✅ since S241 (Infra #162) |
| 2 | A test staff user receives an email code and signs in through the workforce managed login (screenshot + decoded token with `cognito:groups`) | ✅ see §2, screenshots `screens/01–04` |
| 3 | A workforce user with no staff group is denied by the pre token trigger | ✅ see §3 |
| 4 | Self sign-up on the workforce pool is rejected | ✅ see §4 |
| 5 | Break-glass signs in end to end (password + TOTP), the token-issue alarm fires, the user is disabled afterwards | ✅ see §5 |

## 1. Users created

| User | How | Groups | State after the session |
|---|---|---|---|
| `admin@adventure.asia` (break-glass, S241 decision) | AdminCreateUser `MessageAction=SUPPRESS`, `email_verified=true` | cis-admin, booking-admin | **Disabled**, CONFIRMED, MFA `SOFTWARE_TOKEN_MFA` |
| `nghieppham@adventure.asia` (Nghiệp, first staff user) | AdminCreateUser `SUPPRESS`, `email_verified=true`, no password | none at first, then cis-admin, booking-admin | Enabled, CONFIRMED |

A user created with SUPPRESS and no password is **CONFIRMED** immediately on the Essentials tier and signs in with
`EMAIL_OTP` (ADR 0006 open items 3c/3d answered: no FORCE_CHANGE_PASSWORD step, no random password needed, plan D4 not needed).

## 2. Email-code sign-in through managed login (v2)

- Managed login branding created for the three WORKFORCE clients (`--use-cognito-provided-values`):
  cis-admin `70d07784…`, booking-staff `a965331a…`, breakglass `01c3d2c1…`.
- Flow: `https://aa365-staff-auth-dev.auth.us-west-1.amazoncognito.com/oauth2/authorize` (cis-admin client,
  PKCE S256, redirect `http://localhost:3000/api/auth/callback/cognito`) → email → "Check your email" → code typed
  → redirect to the callback with `code` and the same `state` → `/oauth2/token` (Basic auth + `code_verifier`).
- Screenshots: `screens/01-managed-login.png`, `02-after-email.png`, `03-code-entered.png`, `04-after-submit.png`.
- Decoded access token (non-secret claims):
  `token_use=access`, `client_id=3oqkumijh04cp81k3nlnub6qtv`, `cognito:groups=[booking-admin, cis-admin]`,
  `email=nghieppham@adventure.asia`, `scope=openid profile email`,
  `iss=https://cognito-idp.us-west-1.amazonaws.com/us-west-1_bCcFvbSOS`, lifetime 15 min.
- ID token: `aud=3oqkumijh04cp81k3nlnub6qtv`, `email_verified=true`, same groups.
- Refresh token revoked afterwards (`/oauth2/revoke` 200).
- The same sign-in also passed through the API (`InitiateAuth USER_AUTH`, `PREFERRED_CHALLENGE=EMAIL_OTP`).

## 3. No staff group → denied

`nghieppham@adventure.asia` before any group: `RespondToAuthChallenge(EMAIL_OTP)` →
`UserLambdaValidationException: PreTokenGenerationV2_0 failed with error Not authorised for AA staff sign-in.`

## 4. Self sign-up rejected

`SignUp` on the cis-admin client (with SECRET_HASH, no attributes) →
`NotAuthorizedException: SignUp is not permitted for this user pool`.
(With an `email` attribute the call fails earlier: "A client attempted to write unauthorized attribute".)

## 5. Break-glass

One-off script `.tmp-session/s242/breakglass_setup.py` (committed successor: AA-CIS-Infra
`tools/identity/workforce_bootstrap.py`, Phase 1 step I2), run with the MFA admin profile:

```
user created (SUPPRESS, no mail sent)
groups: ['booking-admin', 'cis-admin']
password set (permanent)
TOTP verify: SUCCESS
refresh token revoked
secret aa-identity/dev/breakglass written, VersionId=25a91985-b822-470a-a9c1-f90a22e21f36
challenge: SOFTWARE_TOKEN_MFA
end-to-end sign-in OK (password + TOTP)
access token: token_use=access, cognito:groups=[booking-admin, cis-admin], client_id=2g3f3ncfuqdiuu1o5b70o4h0lq, ttl 15 min
refresh token revoked
disabled: enabled=False status=CONFIRMED mfa=['SOFTWARE_TOKEN_MFA']
```

- Secret JSON keys: `username, password, totp_seed, pool_id, client_id, created_at`. Nghiệp adds `totp_seed` to an
  authenticator app from the Secrets Manager console.
- Alarm `aa-identity-dev-breakglass-token-issued`: `OK → ALARM` at 2026-10-18 01:44:31 UTC (history), i.e. every
  break-glass token issue is alarmed.

## Follow-ups (Phase 1, AA-816 / AA-703)

- I1: alert on any GetSecretValue/PutSecretValue of the break-glass secret + resource policy.
- Break-glass through managed login (`/api/auth/callback/cognito-breakglass`) once the CIS admin UI has the callback (C4).
- Note: break-glass can technically sign in through the cis-admin client too (client restriction is procedural);
  the alarm fires on any client, so any `client_id` other than breakglass in that log line is an incident.
