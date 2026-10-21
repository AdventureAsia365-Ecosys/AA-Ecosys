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

**The requester's address is never written into a script, a PR, a log or a work item.** run-script takes no
parameters, so the lookup holds a constant, and that constant is the SHA-256 hash of the address, never the address
itself. The lookup prints full row ids, and the erasure scripts in section 3 act on those ids only. The hash and the ids
are the only identifiers that go into an AA-CIS-Infra PR or the DSAR work item (DM-6.3, DM-6.10). The hash is
pseudonymous, not anonymous: anyone who already knows the address can recompute it, so it stays in the private Infra
repo and the work item, nowhere else. After the erasure it matches no row.

1. Run the account check first.

   ```bash
   aws sts get-caller-identity --profile aa365-admin
   ```

   Expected: acc2 (see the account map in [onboarding](../onboarding.md)). Abort on any other account.

2. Compute the hash. The address is typed at a hidden prompt, so it stays out of the terminal output, the shell
   history and every file. Trim and lowercase it, as the SQL below does.

   ```bash
   python3 -c 'import getpass, hashlib; print(hashlib.sha256(getpass.getpass("address: ").strip().lower().encode()).hexdigest())'
   ```

   Expected: 64 hex characters. Copy them into the script below; do not keep the address anywhere. If the person also
   gave a phone number, the same hash of the phone in the format stored in `phone` can be added as a second constant.
3. Open an AA-CIS-Infra PR adding `db/scripts/dsar_<yyyymmdd>_lookup.py`. Outline:

   ```python
   """DSAR lookup <yyyy-mm-dd>: ids and counts of rows holding one person's data. Read-only; no row values."""

   READ_ONLY = True
   # sha256 hex of the trimmed, lowercased e-mail address (section 2 step 2). Never the address itself.
   EMAIL_SHA256 = "<64-hex-characters>"

   H = "encode(sha256(convert_to(lower(btrim({col})), 'UTF8')), 'hex') = $1"
   BY_EMAIL = H.format(col="email")
   BY_PAYLOAD = H.format(col="payload -> 'customer' ->> 'email'")
   TP_CUST = f"SELECT id FROM tripplanner.customers WHERE {BY_EMAIL}"
   BK_CUST = f"SELECT id FROM booking.customers WHERE {BY_EMAIL}"
   TP_SESS = f"SELECT id FROM tripplanner.sessions WHERE customer_id IN ({TP_CUST})"
   BK_CASE = f"SELECT id FROM booking.trip_cases WHERE customer_id IN ({BK_CUST})"

   QUERIES = {
       "tp_customers": TP_CUST,
       "tp_sessions": TP_SESS,
       "tp_trip_drafts": f"SELECT id FROM tripplanner.trip_drafts WHERE session_id IN ({TP_SESS})",
       "tp_trip_events": f"SELECT id FROM tripplanner.trip_events WHERE session_id IN ({TP_SESS})",
       "tp_outbox": f"SELECT id FROM tripplanner.outbox WHERE {BY_PAYLOAD}",
       "bk_customers": BK_CUST,
       "bk_merge_refs": f"SELECT id FROM booking.customers WHERE merge_candidate_id IN ({BK_CUST})",
       "bk_trip_cases": BK_CASE,
       "bk_inbox_events": f"SELECT id FROM booking.inbox_events WHERE {BY_PAYLOAD}",
       "bk_notifications": f"SELECT id FROM booking.notifications WHERE entity_id IN ({BK_CASE})",
       "bk_audit_logs": f"SELECT id FROM booking.audit_logs WHERE entity_id IN ({BK_CUST}) OR entity_id IN ({BK_CASE})",
       "bk_customer_otps": f"SELECT id FROM booking.customer_otps WHERE customer_id IN ({BK_CUST})",
       "bk_customer_sessions": f"SELECT id FROM booking.customer_sessions WHERE customer_id IN ({BK_CUST})",
       "bk_media_files": f"SELECT profile_media_id FROM booking.customers WHERE {BY_EMAIL} AND profile_media_id IS NOT NULL",
   }


   async def main(conn):
       for tag, sql in QUERIES.items():
           rows = await conn.fetch(sql, EMAIL_SHA256)
           print(f"SCRIPT {tag} rows={len(rows)} ids={[str(r[0]) for r in rows]}", flush=True)
   ```

   `sha256()` is built into PostgreSQL 11 and later (Dev runs 15.17). Python's and PostgreSQL's `lower()` agree on
   ASCII addresses; for an address with non-ASCII letters, confirm the `tp_customers` count is 1 before going on.
   Check every column name against `db-schema-reference.md` before the PR, since this outline is not run in CI.
   Expected: CI shape check green.
4. Merge, then dispatch DB Migrate on `main`: `mode=run-script`, `script=db/scripts/dsar_<yyyymmdd>_lookup.py`.
   Expected: exit 0 and the `SCRIPT` lines in the job log. Verify: the TripPlanner and Booking counts agree with the
   consent chain (one TripPlanner customer may have several Booking leads). Abort: exit 13 → fix the script in a new PR.
5. **Name check, by hand.** Free text cannot be matched by a hash, and the name must not go into a committed script, so
   staff check `booking.trip_cases.notes` in the Booking admin: open each trip case the lookup found and look for the
   person's name or contact details in the notes, and search the admin customer list for the name in case another
   customer's trip mentions them. Record only the trip-case ids where the name was found. If the admin cannot search
   notes, record that gap in the work item for AA-839.
6. Record the counts and full ids per tag in the DSAR work item. No address, name or phone goes there.

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
(itinerary and dates, linked through `session_id`), the staff mailbox copy of each `bk_notify_email`, any Sentry event
(step 9), the pre-erasure snapshot (step 8) and the automated backups.

Each owner erases its own schema: one reviewed script for `booking.*` (AA-Booking lane) and one for `tripplanner.*`
(TripPlanner lane), both run through DB Migrate `mode=run-script`. **The scripts act on the full row ids from the
section 2 lookup only**, held as constants: no address, name or phone in the code, the PR or the log.

**Delete order.** The foreign keys set it (AA-839 settles the final order and whether rows are deleted or nulled):

- Booking: `booking.customers.merge_candidate_id` points from another customer row to this one (the `bk_merge_refs`
  ids): null it first. `booking.trip_cases.customer_id` and `trip_cases.inbox_event_id` point at the customer and the
  inbox event, and `trip_case_countries`, `trip_case_legs`, `trip_case_status_history`, `trip_case_versions` and
  `staff_assignments` point at the trip case, and `trip_case_version_itinerary` at `trip_case_versions`;
  `notification_reads` points at `notifications`; `customer_otps` and `customer_sessions` point at the customer.
  Children first, then trip cases, then the customer and the inbox events. The customer points at
  `booking.media_files` (`profile_media_id`, the `bk_media_files` ids): that row and its S3 object go after the
  customer.
- TripPlanner: `trip_drafts` and `trip_events` point at `sessions` (`session_id`), and `sessions` points at
  `customers`. Drafts and events first, then sessions, then the customer.

1. **DRY RUN.** Re-run the section 2 lookup (counts and ids) and post the counts per table in the DSAR work item.
   Expected: the same counts and ids as the intake lookup. Abort: counts changed without explanation.
2. **Approval.** Nghiệp approves the counts in the work item ([`destructive-ops.md`](../../skill/aa-cis-schema/references/destructive-ops.md)
   step 1). Abort: no approval, no erasure.
3. **Snapshot.** run-script takes no RDS snapshot, so take a manual one first and note it in the work item. It holds
   the person's data, so it never takes the `keep-` prefix and is deleted in step 8 once the erasure is verified.

   ```bash
   aws rds create-db-snapshot --db-instance-identifier aa-cis-dev-db --db-snapshot-identifier dsar-<yyyymmdd>-pre --profile aa365-admin --region us-west-1 # WRITE
   ```

   Expected: status `creating`, then `available`. Rollback: this snapshot is the rollback for the next step.
4. **Erase, one transaction per owner script.** In each script, for the listed ids: delete or null the rows in the
   order above, redact the personal keys inside jsonb (`payload`, `inquiry_snapshot`, `data`, `before`, `after`), and
   compare the affected counts with the DRY RUN inside the transaction; raise (roll back) on any difference.
   `booking.audit_logs` rows are redacted, never deleted. Trip-case notes where the name check (section 2 step 5) found
   the name are cleared by id.
   Expected: the affected counts equal the DRY RUN. Abort: the script raises, nothing is committed.
5. **Cognito EXTERNAL user**, if one exists. No traveller sign-in is wired today, so none is expected before ADR 0006
   Phase 4; check anyway. The pool id comes from `aws cognito-idp list-user-pools --max-results 20 --profile aa365-admin --region us-west-1`.
   Cognito filters on the plain address, so type it at the prompt only: never in a script or file, and clear it from
   the shell history afterwards.

   ```bash
   aws cognito-idp list-users --user-pool-id <external-pool-id> --filter "email = \"<the-requester-address>\"" --profile aa365-admin --region us-west-1
   aws cognito-idp admin-delete-user --user-pool-id <external-pool-id> --username <username-from-list-users> --profile aa365-admin --region us-west-1 # WRITE
   ```

   Expected: `list-users` returns 0 or 1 user; after the delete it returns 0.
6. **S3 archives (AA-825).** Booking's inbox redaction rewrites rows in place and archives nothing
   (`backend/app/retention/policy.py:9-15`); job archives hold job rows. Check `archive/booking/` for an
   `inbox_events` prefix before assuming there is nothing to erase.
7. **Verify** from a new session: re-run the section 2 lookup with the same hash, and repeat the name check by hand.
   Expected: 0 rows in every tag, the name found in no trip-case notes, and the Cognito user is gone.
8. **Delete the pre-erasure snapshot** once step 7 passes, so no manual copy of the person's data remains.

   ```bash
   aws rds delete-db-snapshot --db-snapshot-identifier dsar-<yyyymmdd>-pre --profile aa365-admin --region us-west-1 # WRITE
   ```

   Expected: `describe-db-snapshots --db-snapshot-identifier dsar-<yyyymmdd>-pre` returns `DBSnapshotNotFound`. The
   automated backups (7 days on Dev, `backup_retention_period = 7` in AA-CIS-Infra `modules/rds/main.tf:143`) still hold
   the erased rows and cannot be edited; they age out within 7 days of the erasure. The reply to the person can say so.
9. **Copies outside the database.**
   - **Staff mailbox:** each inquiry sent a `bk_notify_email` message with the traveller's name, e-mail and phone to
     the Booking staff inbox (AA-Booking `backend/app/notifications/staff_email.py:174-190`). Staff delete those
     messages, and the privacy request thread once it is closed, from that mailbox and its trash.
   - **Sentry:** CIS events carry no default PII (`send_default_pii=False`), but search the CIS Sentry project for the
     e-mail address (in the Sentry search box, not in a file) and delete any event that holds it. Booking and
     TripPlanner have no Sentry.
   Expected: 0 hits in both. Abort: none; record what was found.
10. **Record**: one `booking.audit_logs` row for the erasure (actor, action, entity, no personal data in `after`), a row
    in the [retention log](retention-log.md), and a reply to the person that the data is erased and that the backup
    copies expire within 7 days.

## 4. Tenant offboarding

`POST /admin/tenants/{id}/offboard` is **soft only**: it revokes the key and cancels queued jobs, deletes nothing, and
`/restore` brings the tenant back. Tenant erasure (content, brand identity, planning config, T2 versions, integrations
and `acp/cms/*` / `acp/social/*` secrets, usage and log rows, S3 prefixes) is AA-839 scope item 2. It runs only after
offboarding plus a retention window Nghiệp sets, needs Nghiệp's explicit approval, and is not described here.

## 5. Test data

Three linked test rows from the DM-6.5 consent check are kept for the first Dev test of this runbook: see the
[retention log](retention-log.md#test-data-kept-for-the-erasure-test).
