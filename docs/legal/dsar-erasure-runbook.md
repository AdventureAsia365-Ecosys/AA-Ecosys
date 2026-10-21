---
id: SEC-04-dsar
title: Data-subject requests and erasure runbook
description: How to receive, check and answer a traveller's access or deletion request, and the erasure steps across Booking, TripPlanner, Cognito and S3 under the DRY RUN procedure; untested.
type: how-to
status: draft
owner: nghiep
audience: [engineer, cio]
applies_to: [aa-booking, tripplanner-lambda, ecosystem]
last_reviewed: 2026-10-21
review_every_days: 90
related: [SEC-04, SEC-04-retention, SEC-04-consent-query, AA-839, AA-825, AA-877]
---

# Data-subject requests and erasure runbook

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step.

This page is the working procedure for a traveller who asks to see or delete their personal data. It has never run.
AA-839 owns the tested erasure job, the link from DM-6.7 and moving this page to `active` after a Dev test. Until then
every erasure is manual, under the DRY RUN procedure, with Nghiệp's approval.

Scope: travellers and customers (TripPlanner guests, Booking customers). Tenant offboarding is at the end. Staff data
is out of scope.

## 1. Intake

1. **Where requests arrive.** Today the published contact is `info@adventure.asia` (TripPlanner `/privacy` §9, portal
   `/privacy` §9). A `support@` alias is an option in the [readiness packet](readiness-packet.md) (domain 9).
2. **Log the request** the same day: a row in the
   [register's data-subject requests log](register.md#d-data-subject-requests-log) with the date, the type (access,
   correction, deletion, objection, consent withdrawal) and the mail thread's date and subject. Put no name, e-mail or
   phone in the row. If engineering work follows (a lookup or an erasure script), open one work item that points to
   the row, also without personal data.
   Expected: one row per request. Abort: none.
3. **Check identity.** Answer from the same mailbox to the address the request came from, and act only on data held
   under that address (or phone, if the person gives it in that thread). If the request names a different address,
   ask the person to write from it. The time limit for an answer is `[to be confirmed]` (TripPlanner `/privacy` §9).
   Verify: the request address matches the address you will search. Abort: no match after one reply → close as
   "identity not confirmed" in the requests log row.

## 2. Find the data (read-only)

The data sits in `booking.*` and `tripplanner.*`, which only the RDS master can read, so the lookup runs through
**DB Migrate `mode=run-script`** as a reviewed read-only file, the same contract as
`db/scripts/dm65_consent_capture.py` in AA-CIS-Infra (`db/scripts/README.md`): `READ_ONLY = True`, output = ids, counts
and timestamps only, never row values. Column names: [`db-schema-reference.md`](../architecture/db-schema-reference.md).

1. Run the account check first.

   ```bash
   aws sts get-caller-identity --profile aa365-admin
   ```

   Expected: acc2 (see the account map in [onboarding](../onboarding.md)). Abort on any other account.

2. Open an AA-CIS-Infra PR adding `db/scripts/dsar_<yyyymmdd>_lookup.py`. run-script takes no parameters, so the
   address is a constant in the file; it appears only in the reviewed PR, never in the output. Outline:

   ```python
   """DSAR lookup <yyyy-mm-dd>: ids and counts of rows holding one person's data. Read-only; no row values."""

   READ_ONLY = True
   EMAIL = "<the-requester-address>"  # constant: run-script takes no parameters

   QUERIES = {
       "tp_customers": "SELECT id::text FROM tripplanner.customers WHERE lower(email) = lower($1)",
       "tp_sessions": "SELECT s.id::text FROM tripplanner.sessions s JOIN tripplanner.customers c ON c.id = s.customer_id WHERE lower(c.email) = lower($1)",
       "tp_trip_drafts": "SELECT d.id::text FROM tripplanner.trip_drafts d JOIN tripplanner.sessions s ON s.id = d.session_id JOIN tripplanner.customers c ON c.id = s.customer_id WHERE lower(c.email) = lower($1)",
       "tp_outbox": "SELECT id::text FROM tripplanner.outbox WHERE lower(payload -> 'customer' ->> 'email') = lower($1)",
       "bk_customers": "SELECT id::text FROM booking.customers WHERE lower(email) = lower($1)",
       "bk_inbox_events": "SELECT id::text FROM booking.inbox_events WHERE lower(payload -> 'customer' ->> 'email') = lower($1)",
       "bk_trip_cases": "SELECT t.id::text FROM booking.trip_cases t JOIN booking.customers c ON c.id = t.customer_id WHERE lower(c.email) = lower($1)",
   }


   async def main(conn):
       for tag, sql in QUERIES.items():
           rows = await conn.fetch(sql, EMAIL)
           print(f"SCRIPT {tag} rows={len(rows)} ids={[r[0][:8] for r in rows]}", flush=True)
   ```

   Extend it with `booking.notifications` (rows whose `entity_id` is one of the trip-case ids), `booking.audit_logs`
   (rows whose `entity_id` is the customer or a trip case), `booking.customer_otps` and `booking.customer_sessions`
   (by `customer_id`), and a free-text check of `booking.trip_cases.notes` for the name. Expected: CI shape check green.

3. Merge, then dispatch DB Migrate on `main`: `mode=run-script`, `script=db/scripts/dsar_<yyyymmdd>_lookup.py`.
   Expected: exit 0 and the `SCRIPT` lines in the job log. Verify: the TripPlanner and Booking counts agree with the
   consent chain (one TripPlanner customer may have several Booking leads). Abort: exit 13 → fix the script in a new PR.
4. Record the counts and id prefixes in the DSAR work item.

**Access requests.** The task log must not hold row values, so this lookup cannot produce the copy the person asked
for. Personal values never go to workflow logs, the repo, Google Drive or a laptop (DM-6.3, DM-6.10). Until a tested
export exists (AA-839), delivery is manual and `[to be confirmed]`: staff read the Booking admin customer and
trip-case views and reply to the person from the support mailbox, stating that the TripPlanner record holds the same
contact details and consent (DM-6.2).

## 3. Erasure

**Tables and stores to cover** (AA-839 scope 1, as written):

- `booking.customers` (+ `customer_identities` once Phase 4 adds it; `customer_otps` / `customer_sessions` until Phase
  4 drops them)
- `booking.inbox_events.payload`
- `booking.trip_cases.notes` / `inquiry_snapshot`
- `booking.notifications`
- `booking.audit_logs` before/after jsonb: redact, never delete
- `tripplanner.customers`, `tripplanner.outbox.payload`, `tripplanner.sessions`
- the Cognito EXTERNAL user
- the S3 archives written by AA-825

Also outside AA-839's list: `tripplanner.trip_drafts` and `tripplanner.trip_events` rows of the person's sessions
(itinerary and dates, linked through `session_id`), the staff mailbox copy of each `bk_notify_email`, and any Sentry
event (step 8).

Each owner erases its own schema: one reviewed script for `booking.*` (AA-Booking lane) and one for `tripplanner.*`
(TripPlanner lane), both run through DB Migrate `mode=run-script`.

1. **DRY RUN.** Re-run the section 2 lookup (counts only) and post the counts per table in the DSAR work item.
   Expected: the same counts as the intake lookup. Abort: counts changed without explanation.
2. **Approval.** Nghiệp approves the counts in the work item ([`destructive-ops.md`](../../skill/aa-cis-schema/references/destructive-ops.md)
   step 1). Abort: no approval, no erasure.
3. **Snapshot.** run-script takes no RDS snapshot, so take a manual one first; name it with the `keep-` prefix only if
   it must outlive the 30-day expiry (DM-7 manual snapshot rule), and note it in the work item.

   ```bash
   aws rds create-db-snapshot --db-instance-identifier aa-cis-dev-db --db-snapshot-identifier dsar-<yyyymmdd>-pre --profile aa365-admin --region us-west-1 # WRITE
   ```

   Expected: status `creating`, then `available`. Rollback: this snapshot is the rollback for the next step.
4. **Erase, one transaction per owner script.** In each script: delete or null the person's rows, redact the matching
   keys inside jsonb (`payload`, `inquiry_snapshot`, `data`, `before`, `after`), and compare the affected counts with
   the DRY RUN inside the transaction; raise (roll back) on any difference. `booking.audit_logs` rows are redacted,
   never deleted.
   Expected: the affected counts equal the DRY RUN. Abort: the script raises, nothing is committed.
5. **Cognito EXTERNAL user**, if one exists. No traveller sign-in is wired today, so none is expected before ADR 0006
   Phase 4; check anyway. The pool id comes from `aws cognito-idp list-user-pools --max-results 20 --profile aa365-admin --region us-west-1`.

   ```bash
   aws cognito-idp list-users --user-pool-id <external-pool-id> --filter "email = \"<the-requester-address>\"" --profile aa365-admin --region us-west-1
   aws cognito-idp admin-delete-user --user-pool-id <external-pool-id> --username <username-from-list-users> --profile aa365-admin --region us-west-1 # WRITE
   ```

   Expected: `list-users` returns 0 or 1 user; after the delete it returns 0.
6. **S3 archives (AA-825).** Booking's inbox redaction rewrites rows in place and archives nothing
   (`backend/app/retention/policy.py:9-15`); job archives hold job rows. Check `archive/booking/` for an
   `inbox_events` prefix before assuming there is nothing to erase.
7. **Verify** from a new session: re-run the lookup. Expected: 0 rows holding the e-mail or the name in every listed
   table and jsonb column; the Cognito user is gone.
8. **Copies outside the database.**
   - **Staff mailbox:** each inquiry sent a `bk_notify_email` message with the traveller's name, e-mail and phone to
     the Booking staff inbox (AA-Booking `backend/app/notifications/staff_email.py:174-190`). Staff delete those
     messages, and the privacy request thread once it is closed, from that mailbox and its trash.
   - **Sentry:** CIS events carry no default PII (`send_default_pii=False`), but search the CIS Sentry project for the
     e-mail address and delete any event that holds it. Booking and TripPlanner have no Sentry.
   Expected: 0 hits in both. Abort: none; record what was found.
9. **Record**: one `booking.audit_logs` row for the erasure (actor, action, entity, no personal data in `after`), a row
   in the [retention log](retention-log.md), and a reply to the person.

## 4. Tenant offboarding

`POST /admin/tenants/{id}/offboard` is **soft only**: it revokes the key and cancels queued jobs, deletes nothing, and
`/restore` brings the tenant back. Tenant erasure (content, brand identity, planning config, T2 versions, integrations
and `acp/cms/*` / `acp/social/*` secrets, usage and log rows, S3 prefixes) is AA-839 scope item 2. It runs only after
offboarding plus a retention window Nghiệp sets, needs Nghiệp's explicit approval, and is not described here.

## 5. Test data

Three linked test rows from the DM-6.5 consent check are kept for the first Dev test of this runbook: see the
[retention log](retention-log.md#test-data-kept-for-the-erasure-test).
