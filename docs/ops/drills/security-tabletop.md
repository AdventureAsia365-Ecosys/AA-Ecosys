---
id: OPS-03-tabletop
title: Security tabletop script
description: A 60-minute tabletop for the business owner (the second on-call person and second key-holder) with the tech lead - who calls whom, a real break-glass sign-in test, the CRM data-key rotation walk-through and a leaked-secret talk-through - plus an optional 30-minute extra part, with what to record.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, owner]
applies_to: [ecosystem, aa-crm-api, aa-cis-infra, aa-workforce-dev]
last_reviewed: 2026-11-28
review_every_days: 90
related: [OPS-03-drills, OPS-01-no-agent, OPS-03-runbook-only, OPS-04, OPS-04-chat-alerts, OPS-10, SEC-02-rotation, OPS-04-crm-keys, OPS-05-db-migrate, OPS-11, SEC-05-access-register, SEC-05-second-keyholder, AA-1110]
---

# Security tabletop script

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> This is the script of the first run. After the run, add its row to the [drill index](README.md) and keep the
> notes in `docs/audits/<date>-S<nnn>-security-tabletop/`.

A tabletop is a talk-through: people say what they would do, step by step, against the real runbooks. Only Part B
changes something real (a break-glass sign-in on Dev, then a rotation), and it is chosen to be safe. Cost: 0 USD.

The audience is the **business owner**, who is the second on-call person and the second key-holder (root decision
sec-Q16): when an urgent alert arrives and the tech lead has not reacted, the business owner calls the tech lead
within 30 minutes. The hour checks that the business owner knows who to call, can sign in through the break-glass path
with the tech lead watching, and understands what a key rotation and a leaked secret mean for the company.

## Who and what

| Role | Does |
|---|---|
| Facilitator (the tech lead) | Reads each inject aloud, keeps time, asks the questions, runs the AWS commands of Part B |
| Business owner | Answers first; does the break-glass sign-in of Part B on their own phone and laptop; decides on tenant notice and wording |
| Scribe (the tech lead, or the agent from the transcript) | Writes each answer, each gap and each runbook line that was wrong or missing |

Bring: the business owner's laptop and phone (an authenticator app installed: any TOTP app), the tech lead's laptop
with the AWS admin profile, the [incident response](../incident-response.md), [break-glass](../runbooks/break-glass.md)
and [second key-holder checklist](../../security/second-key-holder-checklist.md) pages open. Book a time outside
:35-:45 past the hour (when the hourly Migration Apply starts) in case the extra part is run.

## Agenda (60 minutes)

| Minute | Part |
|---|---|
| 0-5 | Ground rules, roles, where the notes go |
| 5-15 | Part A: who calls whom (the card below, one inject) |
| 15-35 | Part B: break-glass sign-in test (real, on Dev) |
| 35-47 | Part C: CRM data-key rotation walk-through (talk-through only) |
| 47-55 | Part D: a secret leaked on a public repo (talk-through) |
| 55-60 | Gaps, owners, the next date |

## Part A: who calls whom (10 minutes)

The card (print it, or keep it on the business owner's phone):

| When | Who | Does | Within |
|---|---|---|---|
| A page alert arrives (e-mail subject or Slack card names a security, identity, NAT or database alarm) | tech lead | acknowledges in the alerts channel, starts the [first 15 minutes](../incident-response.md#first-15-minutes) | 15 min |
| No acknowledgement from the tech lead | business owner | **calls the tech lead by phone**; no answer: calls again after 10 minutes and sends a Zalo message | 30 min from the alert |
| Tech lead reached | tech lead | owns the incident, tells the business owner the severity | - |
| SEV1 confirmed (customers cannot work, data exposed, secret leaked) | tech lead | tells the business owner (who decides on tenant notice) | 30 min |
| Tenants affected | business owner (wording), tech lead (sends) | e-mail to the affected tenants | 2 h |
| Tech lead unreachable for 2 hours during a SEV1 | business owner | uses the break-glass path only if a person must sign in (Part B), otherwise waits; writes down the times | - |
| Personal data involved | business owner, with counsel | the [personal data breach](../incident-response.md#personal-data-breach) branch | 72 h at the latest |

Inject (minute 7): "Saturday 23:10. Your phone shows a page alert: the database instance stopped. Nothing in the
alerts channel from the tech lead." Ask, in order:

1. What do you do first, and by when? Expected: call the tech lead before 23:40; again at 23:50 with a Zalo message.
2. Do you try to fix the database yourself? Expected: no. The business owner's job is to reach the tech lead and to
   decide on notices; the database runbooks need the tech lead's access.
3. Where do you write what happened? Expected: times of the alert and each call, in a note sent to the tech lead.
4. Which channels get the alert today? Expected: the e-mail inboxes and, once switched on, the Slack channel
   ([second alert channel](../runbooks/chat-alert-channel.md)). If the business owner did not get this alert, that is a
   gap: piece C of that page (page alerts only, to the business owner's inbox).

## Part B: break-glass sign-in test (20 minutes, real)

Purpose: the second key-holder completes the break-glass sign-in to the CIS admin once, so the path is proven for a
person other than the tech lead. Follow [break-glass](../runbooks/break-glass.md) section A; the steps below say who
does what. Every read of the break-glass secret and every token it issues sends a page alert by design: the alerts
are expected and are part of the test (the business owner should see them arrive).

1. The tech lead checks the account and enables the user (break-glass step 1, `admin-enable-user`).
   Expected: `Enabled` is `true`.
2. The tech lead opens the break-glass secret in the Secrets Manager console (step 2). The business owner adds the
   TOTP seed to their own authenticator app from the tech lead's screen; nobody copies it into chat, e-mail or a file.
   Expected: a page alert for the secret read arrives in the inboxes (and the Slack channel if it is on).
3. The business owner opens the break-glass sign-in URL of step 3 in a private browser window and signs in with the
   password (read from the tech lead's screen) and a TOTP code from their own app.
   Expected: the CIS admin opens; a page alert for the break-glass token arrives.
4. The business owner opens one admin page (for example the alerts catalogue), touches nothing, and logs out from
   the top bar. Expected: the browser passes through the logout page and lands on `/login`.
5. The tech lead closes (step 5: global sign-out and disable). Expected: `Enabled` is `false`; the token alarm goes
   back to `OK` later.
6. The tech lead rotates the password and the TOTP seed ([secret rotation](../runbooks/secret-rotation.md) class 4,
   `breakglass-init`, then `breakglass-verify`). The business owner removes the old entry from the authenticator app.
   Whether the business owner keeps a copy of the **new** seed is the tech lead's decision; record it in the
   [access register](../../security/access-register.md) break-glass row.
7. Record: the times of steps 1 to 5, the alert times, and whether each alert reached the business owner.

Abort: anything unexpected (a sign-in that does not ask for TOTP, a token without the break-glass client, an alert that
does not arrive) stops the test at step 5 (close) and becomes a finding.

## Part C: CRM data-key rotation walk-through (12 minutes)

> [!CAUTION]
> Talk-through only. Today no admin page, route or job kind calls the CRM key rotation; it exists only as a code
> function (`KeyProvider.rotate` in AA-Partner `api/app/vault/provider.py`). Do not run it by hand until an
> operator entry point exists and was tested on a synthetic agency.

What a rotation is, in plain words: each agency's private data in the CRM is locked with that agency's own keys, one
per kind of data (`vault`, `docs`, `integration`, `scrub`, `ops_release`, `export`, `mail`). The keys themselves are
locked again by a master key in AWS (KMS) that nobody can download. A rotation retires the current key of one kind and
makes the next one. Old data stays readable because the retired key is kept (only an agency leaving the platform
destroys keys); new data uses the new key. So a rotation rewrites no data and needs no undo.

Step list to walk (the future operator entry point does steps 2 to 4):

1. Pick a synthetic agency only (`crm.tenant.is_synthetic` true; real agencies only after the Go-real gate).
2. Before: count that agency's live key rows per purpose and note the current `key_version` of the purpose to rotate
   (columns `purpose`, `key_version`, `retired_at`, `destroyed_at`; never select `wrapped_dek`), inside the agency's
   tenant context (the table has row-level security with FORCE).
3. Rotate one purpose inside the agency's tenant transaction. Expected: the old row gets `retired_at`, a new row has
   `key_version` + 1, and one `crm.audit_event` row with `action` `key_rotate`, outcome `allowed`.
4. Verify in the CRM web as that agency's owner: an existing client still opens (old key), a new client saves and
   opens (new key). A `decrypt_denied` audit row means stop.
5. Abort: nothing to undo; never destroy the retired row. Watch the CRM KMS alarms ([CRM keys](../runbooks/crm-keys.md)).

Ask the business owner: when would you want a rotation (a staff member with access leaves, a suspected leak, once a
year)? Who may press the button, and must a second person approve it? Write the answers down as the requirements of
the operator entry point.

## Part D: a secret leaked on a public repo (8 minutes, talk-through)

Inject (minute 47): "GitHub e-mails that a vendor API key was pushed to a public app repo 40 minutes ago." Invented
example; never use a real key name in the notes.

1. Severity and who is told by when? Expected: SEV1 ("secret leaked"); the business owner within 30 minutes.
2. Is deleting the commit enough? Expected: no. A pushed value is public: rotate it even if the branch is rewritten
   ([secret rotation](../runbooks/secret-rotation.md); the [secrets register](../../security/secrets-register.md) row
   names every copy).
3. How do we know it was not used? Expected: the vendor's usage page for the key's window (the tech lead checks);
   the business owner decides whether a customer must be told.
4. What does the business owner need to approve? Expected: any paid vendor change, and the tenant notice wording.

## After the tabletop (5 minutes, then the write-up)

1. Evidence folder `docs/audits/<date>-S<nnn>-security-tabletop/README.md`: participants by role, the answers, the
   time per part, the Part B times and alert arrival times, every gap.
2. Add the run to the [drill index](README.md) table.
3. Fill the break-glass row of the [second key-holder checklist](../../security/second-key-holder-checklist.md) with
   the Part B evidence.
4. Each gap becomes a Linear issue (ask the tech lead first) or a line in an open one.
5. Next run: before the first paying tenant, then once a quarter from prod (DM-9.3).

## Extra part (optional, 30 minutes, the tech lead and the business owner)

Run it in the same sitting if time allows, or as a second short session.

### E1. Agency A reads agency B's data (15 minutes, talk-through)

Inject: "An agency owner on the pilot e-mails a screenshot: the client list in their CRM shows a client name that
belongs to another agency." Invented example.

1. Severity and first move? Expected: SEV1 ("tenant sees another tenant's data"); contain first: a rollback of the last
   CRM deploy ([rollback-ecs](../runbooks/rollback-ecs.md), `aa-crm-dev-api`) or the feature's flag
   ([feature flags](../feature-flags.md)), not the whole product if a route is enough.
2. Where is the evidence? Expected: `crm.audit_event` rows for both agencies around the time; read with the CRM support
   role, never the master login. Is isolation broken everywhere? Run the [isolation probe](../runbooks/isolation-probe.md).
3. Who tells the two agencies, and when? Expected: the business owner, within 2 hours, with the
   [personal data breach](../incident-response.md#personal-data-breach) branch.

### E2. A real, low-risk rotation of the `db_migrator` password (15 minutes)

Class 2 of [secret rotation](../runbooks/secret-rotation.md). Low risk on Dev: only the short migration tasks log in
with it; no running service reads it. Preconditions: no `Migration Apply (expand auto-apply)` or `DB Migrate (shared
RDS)` run in progress on AA-CIS-Infra (not between :35 and :45 past the hour).

1. `aws sts get-caller-identity --profile aa365-admin`. Expected: the acc2 account from the
   [account map](../../onboarding.md#account-map).
2. The tech lead writes a new DSN with a new password into the secret `aa-cis/dev/db-migrator` in the Secrets Manager
   console (**Retrieve secret value**, **Edit**). Nobody reads or pastes the old value. Expected: a new version with
   `AWSCURRENT`; the old one is `AWSPREVIOUS`.
3. AA-CIS-Infra **Actions**, `DB Migrate (shared RDS)`, **Run workflow** on `main`: `environment` `dev`, `mode`
   `set-password`, `role` `db_migrator` ([DB Migrate](../runbooks/db-migrate.md) step 3). Expected: green; the log
   prints `current_user` and `rolconnlimit` of a successful test login, never the password.
4. Verify: `DB Migrate (shared RDS)` with `mode` `check` and `migration` set to any file that is already applied.
   Expected: green, `ran as` the owner role.
5. Roll back if step 3 or 4 fails: move `AWSCURRENT` back to the previous version in the console, then run
   `set-password` again. Record the date in the secrets register row (names and dates only).
