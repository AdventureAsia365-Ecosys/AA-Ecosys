# ADR 0006 — Amendment: a partner pool with required MFA for agency people, and an M2M pool for service calls

- **Status:** Accepted (2026-10-22, S247, tech lead). Proposed the same day. Amended by **A1** (2026-11-01, S263,
  section "Amendment A1" below: `AdminDeleteUser` for never-signed-in partner-pool accounts).
- **Scope:** AA-CIS-Infra (pools, clients, groups, domains), AA-Partner ([ADR 0010](0010-aa-partner-app.md): CRM and,
  after P2b, the tenant portal), AA-CIS-App (tenant membership, CIS admin calling `crm.ops.v1`), AA-Booking
  (B2B API receiving M2M tokens). TripPlanner and the Booking customer app are **not** affected.
- **Amends:** [ADR 0006](0006-ecosystem-identity.md) decision 1 (takes up the "alternative kept open": a separate
  tenant pool), decision 2 (app clients; the sentence "Machine callers do **not** get Cognito clients"), decision 3
  (tenant users), decision 4 (sign-in methods, row "Tenant users"), decision 8 rule 6 (route classes) and Migration
  plan Phase 3 (AA-813). [ADR 0006a](0006a-identity-phase1-amendments.md) is unchanged.
- **Implements:** the owner's answer Q1 3.13 (two-step sign-in required for agency owner and agent), design decision
  D3 (partner pool on Dev in AA-939, synthetic users only), v2.2 S5 (Cognito M2M instead of self-signed JWTs), and
  contradiction X16 of the CRM design.
- **Design and evidence:** [`final/crm-design-final.md`](../audits/2026-10-21-S246-crm-design-v3/final/crm-design-final.md)
  §1.1 (D3), §4.2, §4.5, §5.5 (F4), §6; design v3 §2.1, §4.7; [`decisions.json`](../audits/2026-10-21-S246-crm-design-v3/decisions.json) D3.
- **Related Linear:** AA-939 (partner pool, roles, MFA), AA-972 (M2M pool), AA-978 (membership feed), AA-979 (P2b
  sign-in switch), AA-980 (prod pool), AA-930 (Cognito tier, price and passkey checks), AA-813 (re-scoped), AA-762
  (closed as a duplicate of AA-939).

## Context

ADR 0006 put tenant users and travellers in one EXTERNAL pool with **MFA off**, because a user who enrols TOTP can no
longer sign in with an email code, and travellers sign in by email code. The owner then required two-step sign-in for
agency owners and agents (Q1 3.13). Turning MFA on in EXTERNAL would change sign-in for every TripPlanner and Booking
traveller (X16). ADR 0006 already named the way out as an "alternative kept open": split tenant users into their own
pool.

Two more facts: the tenant portal still signs in with the tenant API key (checked 2026-10-21), so no tenant user is
on EXTERNAL yet; and the CRM calls Booking and CIS server to server, which ADR 0006 decision 2 assumed would not need
Cognito clients.

## Decisions

### 1. A partner pool for agency people

- New user pool **`aa-partner-<env>`** for the people of partner agencies: CRM owners, agents and assistants, and,
  after P2b, Content studio users. Essentials plan, `deletion_protection = ACTIVE`, the immutable settings of ADR
  0006 decision 1 (`username_attributes = ["email"]`, case-insensitive), account recovery `admin_only`, email change
  only after verification, the same WAF rate rules.
- **Admin-create only** (invitations). People are created by the invitation flow (decision 5), never by self
  sign-up.
- **MFA required** for every user of the pool. The intended sign-in is a **passkey** with user verification; the
  fallback for a person without a passkey is **password + TOTP**. An email code alone is never enough for this pool.
  Whether Cognito counts a passkey sign-in as satisfying required MFA, and on which tier, is checked in AA-930 before
  AA-939 *(unverified today)*; if it does not, the pool runs password + TOTP only (the design's "TOTP-only fallback").
- Passkeys are bound to the relying-party ID of the pool's domain. On Dev that is acceptable (synthetic users only);
  the prod pool (AA-980) gets its own domain and enrolment. ADR 0006's "passkeys off" rule stays for WORKFORCE and
  EXTERNAL.
- A lost second factor is reset by an AA admin only after the agency owner confirms it, and the reset is logged in
  the agency's audit (runbook in AA-939).
- Custom domain for the managed login: one more per region (3 of the 4 allowed), name fixed in AA-939
  (`partner-auth.` on the Dev parent domain proposed).
- **When:** on Dev in AA-939 (W2), synthetic users only; the prod pool in AA-980 (W8).

### 2. EXTERNAL stays as it is

- EXTERNAL keeps travellers of TripPlanner and the Booking customer app, MFA off, sign-in methods unchanged.
- The `cis-portal` EXTERNAL client is used only by the CRM on Dev before AA-939, for synthetic users. After P2b no
  human signs in through it; it is removed in the P2b clean-up.
- Agency travellers (the agencies' own clients) never get an account in any AA pool
  ([ADR 0008a](0008a-crm-separate-app-exceptions.md) decision 4).

### 3. One human sign-in for agency people

- From P2b (AA-979), the partner pool is the **only** way a person signs in to AA-Partner, for the CRM and for
  Content studio alike. Before P2b, synthetic CRM users sign in on the CRM and the portal keeps its API-key sign-in;
  nobody real is affected because Dev holds synthetic agencies only.
- `/auth/tenant-login` with the API key is closed for human sessions at P2b. **Tenant API keys remain for machine
  access** (ADR 0006 decision 12, unchanged).
- Pointer (S247): the Gmail / Microsoft 365 / calendar OAuth grants an agency gives the CRM are **integration
  credentials** under [ADR 0010](0010-aa-partner-app.md) decision 9 (bring-your-own), never a way to sign in; there
  is no "Sign in with Google/Microsoft" for agency people. Invitation and security mail for this pool is AA system
  mail through AA's SES.

### 4. Roles stay in app data, keyed by `(iss, sub)`

- Holding a partner-pool token proves nothing about an agency, exactly as decision 3 says for EXTERNAL. The partner
  pool has no tenant groups.
- **CIS** owns agency membership ("this person belongs to agency X") and the Content studio roles
  (owner / editor / viewer), keyed by the partner pool's `(iss, sub)`, and publishes them as `tenant.membership.v1`.
- **The CRM** owns CRM roles (owner / agent / assistant) in `crm.member`, keyed by `(iss, sub)`, written only by the
  agency owner's actions. A membership event from CIS can never grant a CRM role; removal in CIS invalidates the CRM
  cache within 60 s.

### 5. Invitations (replaces Migration plan Phase 3)

Phase 3 of ADR 0006 (tenant users on EXTERNAL through `cis-portal`) is replaced: the invitation flow is the same
(single-use, expiring, hashed invitation token; `AdminCreateUser` with `MessageAction=SUPPRESS`; activation only if
the token is valid **and** the access token's verified email equals the invited email; the membership binds to that
token's `(iss, sub)`; never bound by an email lookup), but it creates the user in the **partner pool**, and the person
enrols the second factor before the membership becomes active. The IAM allow-list of decision 3 for the EXTERNAL
writer applies to the partner pool too (`AdminCreateUser`, `ListUsers`, `AdminDisableUser`,
`AdminUserGlobalSignOut` only; amendment A1 adds `AdminDeleteUser` for never-signed-in accounts only). Content studio users already active at P2b are re-enrolled by invitation, keeping
their tenant and content (AA-979).

### 6. Staff groups, clients and route classes

- WORKFORCE gets three groups: **`crm-platform-admin`** (writes of the L1 platform console), **`crm-ops`** (spec
  module 8 ops release) and **`crm-support`** (owner-granted support sessions), plus one WORKFORCE app client for the
  AA-Partner staff routes (`crm-staff`).
- Route classes (decision 8 rule 6), each accepting only the listed `(issuer, client)` pairs:

| Route class | Accepts | Authorisation |
|---|---|---|
| `/crm/v1` (agency UI) | PARTNER × {the AA-Partner web client}; on Dev before AA-939 only, EXTERNAL × {`cis-portal`} | CRM membership + role from `crm.member` |
| `/crm/ops/v1` (L1 console) | WORKFORCE × {`cis-admin`} (the CIS admin BFF forwards the staff token) | group `cis-admin` reads; `crm-platform-admin` writes |
| `/crm/staff/v1` (ops, support) | WORKFORCE × {`crm-staff`} | groups `crm-ops`, `crm-support`; support also needs an active owner grant |
| `/learn/v1` (AA Academy learning API on CIS; [ADR 0022](0022-aa-academy-learning-platform.md) decisions 6 and 7, added S280, proposed until the tech lead reviews them) | WORKFORCE × {`academy-web`} (the CRM web BFF on the academy host forwards the learner's token); `/learn/public/v1` is public | active CIS staff directory row matched on `(iss, sub)`, any role; draft modules need the CIS capability `learn.preview`; partner tokens refused until P7 |
| Client host (travellers) | no Cognito token; CRM link tokens and email codes (ADR 0008a decision 4) | per-person access rows |

- `cis-admin` and `breakglass` tokens are **refused** on `/crm/v1`, with a negative test per route group.
- **Note (2026-11-01, S263, AA-1031): who grants the three groups.** Like every other WORKFORCE staff group (ADR 0006
  §3), they are granted only from the CIS staff directory: the CIS admin Staff page stores the person's CRM roles
  (`platform_admin`, `ops`, `support`; several per person) in `shared.staff_crm_grant` (CIS migration 330), audits
  each change like the Booking role, and adds and removes the matching group; a directory sync now removes a CRM group
  the row does not hold, so a group set by hand is set on the Staff page first. The page's "Platform owner" preset
  grants `cis-admin`, `booking-admin` and `crm-platform-admin` in one change and never sets the owner flag. The Dev-only
  CRM staff E2E user of [ADR 0006a](0006a-identity-phase1-amendments.md) A10c stays outside the directory (exactly
  `crm-ops` + `crm-support`); the directory health check lists it apart on Dev. The decisions above are unchanged.

### 7. An M2M pool for service-to-service calls

- ADR 0006 decision 2's "Machine callers do **not** get Cognito clients" is replaced for **service** callers: a
  separate pool **`aa-m2m-<env>`** issues client-credentials tokens, one app client per calling service (first: the
  CRM), one resource server per API with scopes such as `booking.b2b/read`, `booking.b2b/quote`, `booking.b2b/hold`,
  `booking.b2b/book`, `cis.catalog/read`, `cis.tenant/read`. Tokens live 6 h and are cached in process. The token
  endpoint uses the pool's Cognito prefix domain; no custom domain is needed (it is never shown to a person).
- Receivers verify the JWT with the same verifier module (decision 8) and pin the client id and scope; the CRM sends
  `X-AA-Tenant-Id` on every B2B call and Booking checks it against its own partner table.
- Tenant API keys for tenant machine access are unchanged. ⚠️ This contains underscore env vars — edit manually in
  VSCode (M2M client configuration in the services' environment).

### Amendment A1 (2026-11-01, S263): `AdminDeleteUser` for never-signed-in accounts

- **Status:** Accepted (2026-11-01, S263, on the tech lead's request "clean up the e-mail accounts too", dev phase
  DM-11.5; review before the first prod pool, AA-980).
- **Amends:** decision 5 (the partner-pool allow-list) and decision 1 (the partner admin-bypass alert).
- **Related Linear:** AA-939 (follow-up). Built in: AA-Partner `app/members/accounts.py` (job
  `crm_partner_accounts`, migration crm-039), AA-CIS-Infra `identity_partner.tf`
  (`crm_ecs_task_partner_pool`, `identity_partner_admin_bypass`), `crm_app.tf` (`PARTNER_ACCOUNT_CLEANUP_DRY_RUN`).

**Context.** A claim creates the invited person's partner-pool account before they sign in. When the invitation then
ends unused (AA withdraws a first-owner invitation, an owner revokes one, it expires, or AA deletes a synthetic test
agency), the account stays in `FORCE_CHANGE_PASSWORD` for ever: Dev already holds such test addresses (S263, after a
test agency was deleted). Nothing in the allow-list could remove them; only a person with the admin profile could, and
that raises the bypass alert each time.

**Decision.**

1. The CRM API task role's partner-pool allow-list becomes `AdminCreateUser`, `ListUsers`, `AdminDisableUser`,
   `AdminUserGlobalSignOut`, **`AdminDeleteUser`**, on the partner pool only. Still nothing that writes a password,
   an attribute or an MFA setting, and nothing on WORKFORCE or EXTERNAL: the explicit Deny of
   `AdminDeleteUser` on the staff pools (AA-CIS-Infra `identity_iam.tf`) stays as it is.
2. The CRM uses it **only** for an account that (a) a CRM invitation claim bound (the clean-up never lists the pool),
   (b) never signed in (`FORCE_CHANGE_PASSWORD`, re-read from Cognito right before the delete, and unchanged since the
   last of its invitations ended), (c) no CRM member row in any agency, no live CRM invitation and no Content studio
   invitation or membership still needs, and (d) whose invitations all ended more than 7 days ago, or at once when
   they belonged to a deleted synthetic test agency. A `CONFIRMED` account is never deleted by this code. Each delete
   is audited in every agency whose invitation it was (`partner_account_delete`, invitation id and reason code only,
   never the address). A daily run (dry run switch, at most 50 deletes per run) and one run queued by a test agency's
   delete.
3. The partner admin-bypass alert keeps watching `AdminDeleteUser`; like `AdminCreateUser`, it excludes the CRM task
   role only. A person, the e2e identity tool, any other role or a static key deleting a partner-pool user still
   alerts.

**Threat model.** IAM cannot limit `AdminDeleteUser` to unused accounts; the limit is the app's (2). Worst case, a
compromised CRM API (or a bug) deletes partner-pool accounts: agency people cannot sign in until they are invited
again (denial of service, recoverable: memberships are keyed by `(iss, sub)` in app data and a new invitation binds a
new account). No takeover: the role still cannot set a password, change an e-mail or attribute, or touch MFA, and a
new account for the same address is reachable only through an invitation link. Detective controls: the app's audit
event per delete, the CRM's CloudWatch log line per delete (ids only), and the bypass alert for every other caller.
The same compromised API could already disable and sign people out (`AdminDisableUser`, `AdminUserGlobalSignOut`),
so the denial-of-service ceiling barely moves.

**Alternatives considered.** Keep deleting by hand with the admin profile (an alert mail per address, and nobody
notices most leftovers); disable instead of delete (`AdminDisableUser` is allowed, but a disabled account still
blocks a fresh claim's `AdminCreateUser` and keeps the address in the pool); a separate delete-only role for a
Lambda (more moving parts for the same blast radius).

## Consequences

- **Positive:**
  - agency owners and agents get two-step sign-in without touching a single traveller's sign-in;
  - one person, one agency sign-in after P2b; the API-key sign-in for humans goes away;
  - service calls carry scoped, short-lived tokens instead of shared secrets.
- **Negative / cost:**
  - a third and a fourth pool to run, with their own domain and triggers;
  - a person who is both an agency user and a TripPlanner traveller has two accounts (the reason ADR 0006 deferred
    the split), accepted because they are different roles;
  - *(est., per month)*: partner pool MAU inside the free tier at Dev and pilot scale ($0–5, tier price checked in
    AA-930); M2M pool ≈ $4 including its KMS-held secret (design §6); one more custom domain certificate ($0).

## Alternatives considered

- **Turn MFA on in EXTERNAL.** Rejected: changes sign-in for every TripPlanner and Booking traveller and locks out
  email-code users (ADR 0006 decision 1).
- **Keep agency people on EXTERNAL without MFA until Go-real.** Rejected (D3 option b): the MFA flow and the
  "invite → active in under 5 minutes" test would land only in W8.
- **Self-signed service JWTs (KMS).** Rejected in v2.2 (S5): a home-made token service; Cognito M2M is the standard
  client-credentials pattern.

## Follow-ups

- AA-930: Cognito passkey-with-required-MFA behaviour, tier and price, M2M price.
- AA-939: partner pool, groups, `crm-staff` client, route-class tests, lost-factor runbook.
- AA-972: M2M pool and Booking scopes. AA-978: membership feed. AA-979: P2b switch and `cis-portal` removal.
- On acceptance: status line here and in the index; ADR 0006 header pointer.
