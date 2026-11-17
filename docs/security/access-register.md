---
id: SEC-05-access-register
title: Access register (key-holders)
description: Who holds each account that can stop or recover the platform - GitHub organization, AWS accounts, domain registrar, break-glass - with the second key-holder, registrar ownership and auto-renew, by role; a template until the second key-holder's access is tested.
type: reference
status: draft
owner: nghiep
audience: [cto, owner, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-17
review_every_days: 90
related: [SEC-05-index, SEC-02, SEC-01, OPS-01-no-agent, OPS-03-tabletop, OPS-10, AA-1110]
---

# Access register (key-holders)

One person holds every access and every approval today. This register lists each account that can stop, recover or
pay for the platform, and who holds it, **by role**. It is filled in when the second key-holder is named and their
access is tested; until then the rows are a template. It holds no password, no recovery code, no account ID and no
personal e-mail address: account IDs live only in the account map in [onboarding](../onboarding.md#account-map), and
secrets only in Secrets Manager or the holder's password manager.

Review: with the quarterly access review ([security index](README.md#access-reviews-sec-05)) and after any change of
holder. A row is "tested" only when the second key-holder signed in and did the check in the last column themselves,
with the date and the evidence folder.

## How to fill a row

- **Primary / second key-holder**: a role ("tech lead", "business owner", "engineer on duty"), never a name.
- **How held**: the kind of access (organization owner, Identity Center permission set, registrar account owner,
  sealed break-glass secret), not the credential.
- **MFA**: the factor kind (TOTP app, hardware key); "none" is a finding.
- **Tested**: the date the second key-holder last used it, and `docs/audits/<date>-S<nnn>-<slug>/`.
- **Status**: `template` (not set up), `granted` (set up, not tested), `tested`.

## Code and delivery

| Asset | Primary key-holder | Second key-holder | How held | MFA | Proof check | Tested | Status |
|---|---|---|---|---|---|---|---|
| GitHub organization `AdventureAsia365-Ecosys` | tech lead | business owner | organization owner | TOTP | opens organization **Settings**, sees **Member privileges** | - | template |
| GitHub App `aa-agent` and `aa-ecosys-ci-bot` keys ([GitHub Apps](github-apps.md)) | tech lead | business owner (through the organization owner role) | App settings in the organization | as above | opens the App settings page; does not create a key | - | template |

## AWS

| Asset | Primary key-holder | Second key-holder | How held | MFA | Proof check | Tested | Status |
|---|---|---|---|---|---|---|---|
| Management account (`aa-management`): organization, Identity Center, billing | tech lead | business owner | Identity Center user with the admin permission set; root e-mail on a company mailbox | TOTP | signs in to the access portal, opens Billing | - | template |
| acc2 (Dev workloads) | tech lead | business owner | Identity Center permission set into acc2, or the admin role with MFA | TOTP | `aws sts get-caller-identity` returns acc2 | - | template |
| LLM account(s) (Bedrock) | tech lead | business owner | Identity Center or the account's own admin role | TOTP | `aws sts get-caller-identity` returns that account | - | template |
| Root user of each account | tech lead | business owner | root e-mail mailbox access + root MFA device | hardware key or TOTP | knows where the root MFA device is; does not sign in as root | - | template |

## Domains

| Domain | Registrar | Account owner (role) | Second key-holder | Auto-renew | Registrar lock | Expiry (date) | Tested | Status |
|---|---|---|---|---|---|---|---|---|
| `lumiguides.it.com` (Dev hostnames; DNS in Route 53) | Namecheap | tech lead | business owner | on / off (check) | on / off (check) | yyyy-mm-dd | - | template |
| `adventure.asia` (company site and mail; DNS outside AWS) | to confirm | business owner | tech lead | to confirm | to confirm | yyyy-mm-dd | - | template |

Ownership rule: a production domain is registered to the company account, not a personal one, with auto-renew on and a
payment card that does not expire before the renewal date.

## Break-glass

| Asset | Primary key-holder | Second key-holder | How held | Proof check | Tested | Status |
|---|---|---|---|---|---|---|
| Cognito break-glass admin ([break-glass](../ops/runbooks/break-glass.md), path A) | tech lead | business owner | password + TOTP in the break-glass secret; only the MFA admin role can read it, and every read alerts | runs the break-glass sign-in on Dev with the tech lead watching, then the password is rotated | - | template |
| RDS master login (path B) | tech lead | none until prod | Secrets Manager, master use is break-glass only | - | - | template |

## Gaps to close

Each `template` row above is an open gap of AA-1110 until its status is `tested`. Record the evidence of each test in
the dated audit folder and change the row in the same root PR.
