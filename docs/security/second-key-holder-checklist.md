---
id: SEC-05-second-keyholder
title: Second key-holder access checklist
description: The step-by-step test that the second key-holder (the business owner) can reach the GitHub organization, the AWS management account, the domain registrar and the break-glass path, with an evidence field for each check; the results go into the access register.
type: how-to
status: draft
owner: nghiep
audience: [cto, owner, devops]
applies_to: [ecosystem]
last_reviewed: 2026-11-28
review_every_days: 90
related: [SEC-05-access-register, SEC-05-index, OPS-03-tabletop, OPS-03-runbook-only, OPS-01-no-agent, OPS-10, AA-1110]
---

# Second key-holder access checklist

The [access register](access-register.md) says who holds each account that can stop, recover or pay for the platform.
This page is how a row becomes `tested`: the second key-holder (the business owner) does each check **themselves**,
on their own devices, with the tech lead watching, and the scribe fills the evidence fields. A row is never marked
tested from a screenshot sent later or from the tech lead doing it on their behalf.

Rules for the evidence: role names only, no person names; no password, recovery code, TOTP seed, account ID or e-mail
address in the evidence or in this page; screenshots crop out account IDs and addresses (the root repo is public).
Evidence goes to `docs/audits/<date>-S<nnn>-second-key-holder/README.md`, one section per check below. Time: about
45 minutes, plus the break-glass part, which is run inside the [security tabletop](../ops/drills/security-tabletop.md).

## Before the session

- [ ] The business owner has a password manager and an authenticator app (TOTP) on their own phone.
- [ ] The tech lead has created, or is ready to create, each access below (invitations sent, Identity Center user
      created). The checks test access; they do not create it.
- [ ] Both laptops on a normal network (no VPN that hides GitHub or AWS).

## 1. GitHub organization

Target state: the business owner is an **organization owner** of `AdventureAsia365-Ecosys` with two-factor
authentication on, so they can recover the organization, change members and reach every repository if the tech lead
is unavailable.

| # | Check (done by the business owner) | Expected | Evidence field |
|---|---|---|---|
| 1.1 | Sign in to github.com with their own account | signed in; their profile shows two-factor authentication on (**Settings › Password and authentication**) | date: ____ · 2FA kind (TOTP app / security key / passkey): ____ |
| 1.2 | Open the organization **People** page | their account is listed with the role **Owner** | screenshot (role column, names cropped): ____ |
| 1.3 | Open the organization **Settings › Member privileges** | the page opens (only owners can) | yes / no: ____ |
| 1.4 | Open `AA-Booking` › **Actions** › **Deploy Admin Dev** | the **Run workflow** button is visible (write access) | yes / no: ____ |
| 1.5 | Open the organization **Settings › GitHub Apps** | the `aa-agent` and `aa-ecosys-ci-bot` apps are listed; nothing is changed | yes / no: ____ |
| 1.6 | Store the GitHub recovery codes in the password manager | stored; never shared | yes / no (do not paste them): ____ |

Register row: "GitHub organization" → `tested`, date, evidence folder.

## 2. AWS management account (`aa-management`)

Target state: the business owner has their own **Identity Center user** with MFA in the company organization and can
open the management account (organization, billing) and acc2 (Dev workloads). Root users are not used.

| # | Check (done by the business owner) | Expected | Evidence field |
|---|---|---|---|
| 2.1 | Accept the Identity Center invitation, set a password, register an MFA device | the access portal opens after the MFA prompt | date: ____ · MFA kind: ____ |
| 2.2 | In the access portal, open the management account with the admin permission set | the AWS console opens; the top-right account menu shows the management account alias | screenshot (account ID cropped): ____ |
| 2.3 | Open **Billing and Cost Management** › **Bills** | the current month's bill is visible | yes / no: ____ |
| 2.4 | Open **AWS Organizations** | the organization's accounts are listed; nothing is changed | yes / no: ____ |
| 2.5 | From the access portal, open acc2 | the console opens in acc2; **ECS** › cluster `aa-cis-dev-cluster` lists the services | yes / no: ____ |
| 2.6 | Optional, for the [runbook-only drill](../ops/drills/runbook-only-deploy-rollback.md): set up the AWS CLI with Identity Center (`aws configure sso`) and run `aws sts get-caller-identity --profile <their profile>` | the acc2 account of the [account map](../onboarding.md#account-map) | yes / no: ____ |
| 2.7 | Ask the tech lead where each account's root MFA device and root mailbox are | the business owner can say where, without signing in as root | yes / no: ____ |

Register rows: "Management account", "acc2", "Root user of each account" → `tested` (or `granted` where a check was
skipped), date, evidence folder.

## 3. Domain registrar

Target state: the business owner can sign in to the registrar account that holds each production domain, or has
delegated access to it, and can see expiry, auto-renew and the registrar lock.

| # | Check (done by the business owner) | Expected | Evidence field |
|---|---|---|---|
| 3.1 | Sign in to the registrar that holds `lumiguides.it.com` (company login from the password manager, or their own login with delegated access) | the domain list opens after the MFA prompt | date: ____ · how held (company login / delegated access): ____ · MFA kind: ____ |
| 3.2 | Open the domain's details | expiry date, auto-renew and registrar lock are visible | expiry: ____ · auto-renew on/off: ____ · lock on/off: ____ |
| 3.3 | Check the payment method on file for renewals | a card that does not expire before the renewal date | yes / no: ____ |
| 3.4 | Same as 3.1-3.3 for `adventure.asia` (company site and mail) | as above | as above: ____ |

Register rows: the two "Domains" rows → fill auto-renew, lock, expiry and `tested`.

## 4. Break-glass

Target state: the business owner has completed one break-glass sign-in to the CIS admin with the tech lead watching
([break-glass](../ops/runbooks/break-glass.md) section A). Run as Part B of the
[security tabletop](../ops/drills/security-tabletop.md).

| # | Check | Expected | Evidence field |
|---|---|---|---|
| 4.1 | The business owner signs in through the break-glass path (password + TOTP from their own app) | the CIS admin opens | date and time: ____ |
| 4.2 | The page alerts of the secret read and the token arrive | each alert reached the business owner's inbox (and the Slack channel if on) | alert times: ____ · reached business owner yes/no: ____ |
| 4.3 | The tech lead closes and rotates (global sign-out, disable, `breakglass-init`, `breakglass-verify`) | `Enabled` false; verify OK | yes / no: ____ |
| 4.4 | Decision recorded: does the business owner keep a copy of the new TOTP seed? | the tech lead's decision written in the register row | decision: ____ |

Register row: "Cognito break-glass admin" → `tested`, date, evidence folder.

## After the session

1. Change each register row in one root PR, with the evidence folder.
2. Every check that failed or was skipped stays `granted` or `template` and becomes a gap line in the register's
   "Gaps to close" section.
3. When every row of sections 1 to 4 is `tested`, the first "Done when" line of AA-1110 is met.
4. Repeat with the quarterly access review ([security index](README.md#access-reviews-sec-05)) and after any change
   of holder.
