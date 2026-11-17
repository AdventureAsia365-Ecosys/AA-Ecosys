---
id: OPS-03-tabletop
title: Security tabletop script
description: A 60-minute tabletop for the tech lead, the second key-holder and the business owner - two scenarios (a secret leaked on a public repo, one agency reading another agency's data), a low-risk real secret rotation and the CRM data-key rotation step list, with what to record.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, cto, owner]
applies_to: [ecosystem, aa-crm-api, aa-cis-infra]
last_reviewed: 2026-11-17
review_every_days: 90
related: [OPS-03-drills, OPS-01-no-agent, OPS-04, OPS-10, SEC-02-rotation, OPS-04-crm-keys, OPS-05-db-migrate, OPS-11, SEC-05-access-register, AA-1110]
---

# Security tabletop script

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.
> This is the script of the first run. After the run, add its row to the [drill index](README.md) and keep the
> notes in `docs/audits/<date>-S<nnn>-security-tabletop/`.

A tabletop is a talk-through: people say what they would do, step by step, against the real runbooks. Only Part C
changes something real, and it is chosen to be safe on Dev. Cost: 0 USD.

## Who and what

| Role | Does |
|---|---|
| Facilitator (the tech lead) | Reads each inject aloud, keeps time, asks the questions, does not answer them |
| Second key-holder | Answers first: the point is that someone other than the tech lead can act |
| Business owner | Decides on tenant notice and wording (SEV1 rule in [incident response](../incident-response.md)) |
| Scribe (any participant, or the agent from the transcript) | Writes each answer, each gap and each runbook line that was wrong or missing |

Bring: a laptop with the AWS admin profile and GitHub access of the second key-holder, the
[run without the agent](../run-without-agent.md) page, the [incident response](../incident-response.md) page and the
[secret rotation](../runbooks/secret-rotation.md) runbook open.

## Agenda (60 minutes)

| Minute | Part |
|---|---|
| 0-5 | Ground rules, roles, where the notes go |
| 5-20 | Part A: a secret leaked on a public repo |
| 20-35 | Part B: agency A reads agency B's data |
| 35-50 | Part C: a real, low-risk secret rotation |
| 50-57 | Part D: walk the CRM data-key rotation step list (talk-through only) |
| 57-60 | Gaps, owners, the next date |

## Part A: a secret leaked on a public repo (15 minutes)

Inject 1 (minute 5): "A GitHub secret-scanning e-mail says a vendor API key was pushed to a public app repo in a
commit on a feature branch 40 minutes ago. The PR is still open." Invented example; do not use a real key name in the
notes.

Ask, in order:

1. What severity is this, and who is told by when? Expected: SEV1 ("secret leaked"), the business owner within
   30 minutes ([incident response](../incident-response.md#severity)).
2. Is deleting the commit or force-pushing enough? Expected: no. A pushed value is public: rotate it, even if the
   branch is rewritten. Rewriting the branch only stops the CI Secret Scan from failing.
3. Which runbook and which class? Expected: [secret rotation](../runbooks/secret-rotation.md), class 1 (app key in
   Secrets Manager) or class 6 (token outside AWS); the secrets register row names every copy.
4. Who may read the old value while rotating? Expected: nobody; the new value is typed by the tech lead in the vendor
   console and Secrets Manager, never pasted in chat.
5. How do you know the key was not used? Expected: the vendor's usage page for the key's window; for an AWS key,
   CloudTrail by access key.

Inject 2 (minute 15): "The tech lead is unreachable." Ask: can the second key-holder do steps 1 to 5 alone today?
Write down every access that is missing; it goes into the [access register](../../security/access-register.md).

## Part B: agency A reads agency B's data (15 minutes)

Inject 1 (minute 20): "An agency owner on the pilot e-mails a screenshot: the client list in their CRM shows a client
name that belongs to another agency." Invented example.

Ask, in order:

1. Severity and first move? Expected: SEV1 ("tenant sees another tenant's data"); contain first: block the route, not
   the whole product, if that is enough.
2. How do you stop one route fast? Expected: the tenant-pool emergency switch is the opposite tool (it removes RLS for
   a route); the containment is a rollback of the last CRM deploy ([rollback-ecs](../runbooks/rollback-ecs.md),
   `aa-crm-dev-api`) or turning the feature off with its flag ([feature flags](../feature-flags.md)).
3. Where is the evidence? Expected: `crm.audit_event` rows for both agencies around the time (outcome `denied` rows
   survive a rolled-back request); a value that does not open under the reader's key raises `decrypt_denied`. Data
   rules: read with the CRM support role, never the master login.
4. Is isolation broken everywhere or on one route? Expected: run the DB isolation probe
   ([isolation probe](../runbooks/isolation-probe.md)) and read the CRM RLS checks.
5. Who tells the two agencies, and when? Expected: the business owner, within 2 hours for affected tenants, with the
   [personal data breach](../incident-response.md#personal-data-breach) branch and the notice template.

Inject 2 (minute 30): "The screenshot turns out to be from a shared test agency on Dev." Ask: what do you still write
down? Expected: the time each step took, and every step nobody knew how to do.

## Part C: a real, low-risk secret rotation (15 minutes)

Rotate the password of the `db_migrator` database login (class 2 of [secret rotation](../runbooks/secret-rotation.md)).
It is low risk on Dev: only the short migration tasks log in with it; no running service reads it, so nothing
restarts. The second key-holder runs it; the tech lead watches.

Preconditions: no `Migration Apply (expand auto-apply)` or `DB Migrate (shared RDS)` run in progress on AA-CIS-Infra
(not between :35 and :45 past the hour, when Migration Apply starts).

1. Check the account.

   ```bash
   aws sts get-caller-identity --profile aa365-admin
   ```

   Expected: the acc2 account from the [account map](../../onboarding.md#account-map).
2. The tech lead writes a new DSN with a new password into the secret `aa-cis/dev/db-migrator` in the Secrets Manager
   console (**Retrieve secret value**, **Edit**). Nobody reads or pastes the old value. Expected: a new version with
   `AWSCURRENT`; the old one is `AWSPREVIOUS`.
3. In AA-CIS-Infra **Actions**, `DB Migrate (shared RDS)`, **Run workflow** on `main` with `environment` `dev`,
   `mode` `set-password`, `role` `db_migrator` ([DB Migrate](../runbooks/db-migrate.md) step 3). Expected: green; the
   log prints `current_user` and `rolconnlimit` of a successful test login, never the password.
4. Verify: run `DB Migrate (shared RDS)` with `mode` `check` and `migration` set to any file that is already applied.
   Expected: green, `ran as` the owner role, which proves the migrator logs in with the new password.
5. Roll back if step 3 or 4 fails: in the console, move `AWSCURRENT` back to the previous version (one line in
   [secret rotation](../runbooks/secret-rotation.md), class 1 step 5, with `aa-cis/dev/db-migrator`), then run
   `set-password` again.
6. Record: the date and "rotated" in the secrets register row (names and dates only), the run links in the evidence
   folder.

## Part D: CRM data-key rotation (talk-through, 7 minutes)

> [!CAUTION]
> Talk-through only. Today no admin page, route or job kind calls the CRM key rotation; it exists only as a code
> function (`KeyProvider.rotate` in AA-Partner `api/app/vault/provider.py`). Do not run it by hand until an
> operator entry point exists and was tested on a synthetic agency.

What a rotation is: each agency has one data key (DEK) per purpose (`vault`, `docs`, `integration`, `scrub`,
`ops_release`, `export`, `mail`), stored only wrapped by the CRM KMS key in `crm.tenant_key`. A rotation retires the
current version of one purpose and creates the next one. Old values stay readable because the retired version is
kept (only an offboarding destroys keys). New writes use the new version. So a rotation needs no data rewrite and no
undo.

Step list to walk:

1. Pick a synthetic agency only (`crm.tenant.is_synthetic` true; real agencies only after the Go-real gate).
2. Before: count that agency's live key rows per purpose and note the current `key_version` of the purpose to rotate
   (columns `purpose`, `key_version`, `retired_at`, `destroyed_at`; never select `wrapped_dek`). Read inside the
   agency's tenant context: the table has RLS with FORCE.
3. Rotate one purpose inside the agency's tenant transaction (the future operator entry point). Expected: the old row
   gets `retired_at`, a new row has `key_version` + 1, and one `crm.audit_event` row with `action` `key_rotate`,
   outcome `allowed`.
4. Verify in the CRM web as that agency's owner: an existing client still opens (old version), a new client saves and
   opens (new version). A `decrypt_denied` audit row means stop.
5. Abort: nothing to undo; do not destroy the retired row. Watch the CRM KMS alarms ([CRM keys](../runbooks/crm-keys.md)):
   a rotation decrypts and encrypts a few keys, far under the decrypt-rate alarm.

Ask: who may run this, with which role, and where is the evidence kept? Write the answers as the requirements of the
operator entry point.

## After the tabletop

1. Evidence folder `docs/audits/<date>-S<nnn>-security-tabletop/README.md`: participants by role, the answers, the
   time per part, the Part C run links, every gap.
2. Add the run to the [drill index](README.md) table.
3. Each gap becomes a Linear issue (ask the tech lead first) or a line in an open one.
4. Next run: before the first paying tenant, then once a quarter from prod (DM-9.3).
