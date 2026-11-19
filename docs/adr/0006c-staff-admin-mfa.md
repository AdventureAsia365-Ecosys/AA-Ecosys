# ADR 0006 — Amendment: administrators sign in with password + TOTP, checked by each staff API

- **Status:** Accepted (2026-11-19, S285). The tech lead decided TOTP for staff administrators on 2026-11-17 (S283)
  and, on 2026-11-19 (S285), that the WAF geo rule of the staff hosts goes once administrator MFA is enforced. This
  page records how it is built (AA-1111 slice S2).
- **Scope:** AA-CIS-Infra (WORKFORCE pool, enrolment tool, runbook, WAF), AA-CIS-App, AA-Booking and AA-Partner (the
  staff APIs). TripPlanner, the PARTNER pool and the EXTERNAL pool are not affected.
- **Amends:** [ADR 0006](0006-ecosystem-identity.md) decision 4 (sign-in methods: "MFA: WORKFORCE = optional, TOTP
  only, used only by break-glass"). [ADR 0006a](0006a-identity-phase1-amendments.md) (break-glass) and
  [ADR 0006b](0006b-partner-pool-and-mfa.md) (partner pool, MFA required) are unchanged.
- **Related Linear:** AA-1111 (pre-pilot identity hardening).

## Context

Staff sign in to the WORKFORCE pool with an e-mail one-time code. Whoever controls an administrator's mailbox can open
every admin page of CIS, Booking and the CRM operations surface. The S282 audit (R08) asked for a second factor before
a pilot with real personal data. The pool already allows TOTP as optional MFA for break-glass; Cognito does not let an
app client ask for TOTP for some users only, and turning MFA **on** for the pool would force every staff member (desk
roles, the Dev E2E accounts) onto TOTP. Cognito now writes the factors a sign-in used into the access token's `amr`
claim (`["pwd", "otp", "mfa"]` after password + TOTP, `["email_otp"]` after an e-mail code); a pre token trigger
cannot change it.

## Decision

1. **The pool stays MFA optional, TOTP only, no SMS** (no new paid feature). A Terraform postcondition keeps it so.
2. **Administrators enrol TOTP** with the AA-CIS-Infra tool `workforce_bootstrap.py staff-totp-enroll` (the person
   sets a password and adds the key to an authenticator app; afterwards Cognito offers them password + code only, no
   e-mail code). `staff-totp-check` proves the `amr` claim on the pool before any API enforces it.
3. **Each staff API checks the verified access token's `amr` for `otp`** for its administrator roles, and refuses a
   session without it with **403 `mfa_required`**, only while its own switch is on:
   - CIS: role `admin` (`cis-admin`) or the owner flag; setting `cis.platform.admin_mfa_required`;
   - AA-Partner: groups `crm-platform-admin`, `crm-ops`, `cis-admin`; setting `crm.platform.admin_mfa_required`;
   - Booking: role `admin` (`booking-admin`); pricing policy parameter `staff_admin_mfa_required`.
   Each switch is an admin-editable, audited, maker-checker value (tech lead rule S279), default **off**, with no env
   override. Off, the API only logs `staff_admin_mfa_check outcome=would_refuse`. Desk roles, agency members and the
   Dev-only E2E identities are never checked. The claim is read from the already verified token string, so the
   byte-copied verifier (ADR 0006 §8 rule 9) is unchanged.
4. **Order:** merge with the switches off → every administrator enrols → `staff-totp-check` shows `otp` → the three
   switches go on → the WAF stops geo-blocking the staff web hosts (they join `geo_exempt_hosts`). Runbook:
   AA-CIS-Infra `docs/runbooks/staff-admin-mfa.md`.

## Consequences

- An administrator with TOTP can no longer use the e-mail code; a lost phone is fixed by the tech lead re-running the
  enrolment with `--rotate`. If everyone is locked out, break-glass (password + TOTP) turns a switch off.
- Turning the Booking switch on needs two administrators (maker-checker on every pricing policy change).
- The staff web hosts become reachable from any country once the geo rule is dropped; the managed rules, rate limits,
  Cognito sign-in and TOTP remain.

## Alternatives considered

- **MFA ON for the whole pool.** Rejected: forces desk staff and the Dev E2E accounts onto TOTP.
- **Google IdP with 2-Step Verification.** Rejected: the company mail is not on Google Workspace (S282 finding).
- **Check enrolment with AdminGetUser instead of the token.** Rejected: an extra AWS call per session, and it says what
  the user has, not what this sign-in used.
- **Add `amr` to the shared verifier's `Principal`.** Rejected for now: it changes a byte copy in three repos at once.
