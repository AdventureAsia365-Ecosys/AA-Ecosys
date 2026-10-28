---
id: SEC-04-dsar
title: Data-subject requests and erasure runbook
description: How to answer a traveller's access or deletion request and erase a tenant after offboarding, across Booking, TripPlanner, CIS, Cognito and S3, under the DRY RUN procedure; the tenant part was drilled on Dev, the traveller part not yet.
type: how-to
status: draft
owner: nghiep
audience: [engineer, cio]
applies_to: [aa-booking, tripplanner-lambda, aa-cis-worker, ecosystem]
last_reviewed: 2026-10-28
review_every_days: 90
last_tested: 2026-10-23
tested_where: dev-acc2
tested_evidence: docs/audits/2026-10-23-S248-aa839-erasure-drill/README.md
related: [SEC-04, SEC-04-retention, SEC-04-consent-query, AA-839, AA-825, AA-877]
---

# Data-subject requests and erasure runbook

> [!WARNING]
> Partly tested - check each step before you rely on it. The tenant erasure (section 4) ran once on Dev on a
> synthetic tenant on 2026-10-23. The traveller part (sections 2 and 3) has not run on Dev, and the Booking and
> TripPlanner scripts are not written yet.

This page is the working procedure for a traveller who asks to see or delete their personal data (sections 1-3) and
for erasing a tenant after offboarding (section 4). Data standards DM-6.7 points here. AA-839 moves it to `active`
after the Dev drills of section 5. The tenant drill (DRY RUN, apply, verification) passed on 2026-10-23
([evidence](../audits/2026-10-23-S248-aa839-erasure-drill/README.md)); the traveller drill is still to do.

**What is automated.** CIS has one job kind, `data_erasure` (AA-CIS-App `services/jobs/erasure_job.py`, inventory
`services/erasure/inventory.py`). It runs a **DRY RUN** by default: counts per CIS table and action, blockers, the
delete order, the tenant's S3 objects and secrets, the per-app checklist and a `fingerprint` that binds the subject
and the counts (`fingerprint_version` 2): for a tenant it hashes the tenant id with the counts, so another tenant
with the same counts has another fingerprint; for a traveller it hashes the address hash with a random salt drawn by
that DRY RUN (kept in the job's `result.subject_salt` and removed together with the hash after the apply), so the
fingerprint left in the job rows and the audit row cannot be tested against a guessed address. Its
**apply** exists but is off: the api and worker get `ERASURE_APPLY_ENABLED=false` from AA-CIS-Infra (local
`erasure_drill = false` in `accounts/aa365/main.tf`). Turning it on is a Terraform change that needs the tech lead's
approval. Booking and TripPlanner rows are other owners' schemas: their lookup and erasure run through DB
Migrate `mode=run-script` (sections 2 and 3). Every erasure follows the DRY RUN procedure
([`destructive-ops.md`](../../skill/aa-cis-schema/references/destructive-ops.md)) with the tech lead's approval.

**Operator UI.** The CIS admin page **Jobs › Data erasure** (`/admin/data-erasure`, admin role; AA-CIS-App #960) is
the usual way to run the CIS part: it shows the settings (apply on or off, retention days, DRY RUN max age), starts a
DRY RUN for an offboarded tenant or for a traveller (the address is hashed in the browser and cleared; only the hash
is sent), shows the plan and the fingerprint, opens the apply panel only while apply is on and only for a succeeded,
unblocked, unused DRY RUN within the max age, starts the verification DRY RUN after a traveller apply, and lists the
history. The apply needs a Cognito staff sign-in. The `curl` commands below call the same API and stay as the
terminal fallback.

Scope: travellers and customers (TripPlanner guests, Booking customers) and offboarded tenants. Staff data is out of
scope. A tenant's own CRM contacts (AA-Partner, schema `crm`) are the tenant's records (DM-6.8): forward such a
request to the tenant.

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
pseudonymous, not anonymous: anyone who already knows the address can recompute it, so it stays in the Infra repo
and the work item, nowhere else. After the erasure it matches no row.

> [!CAUTION]
> AA-CIS-Infra is public until the coding phase ends (ADR 0014 amendment). While it is public, a lookup PR shows the
> hash to anyone, and anyone who knows the address can then confirm that the person made a request. Ask the tech
> lead how to run the lookup before you open such a PR.

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
       "tp_traveller_accounts": f"SELECT DISTINCT account_id FROM tripplanner.sessions WHERE id IN ({TP_SESS}) AND account_id IS NOT NULL",
       "bk_customers": BK_CUST,
       "bk_merge_refs": f"SELECT id FROM booking.customers WHERE merge_candidate_id IN ({BK_CUST})",
       "bk_trip_cases": BK_CASE,
       "bk_inbox_events": f"SELECT id FROM booking.inbox_events WHERE {BY_PAYLOAD}",
       "bk_notifications": f"SELECT id FROM booking.notifications WHERE entity_id IN ({BK_CASE})",
       "bk_audit_logs": f"SELECT id FROM booking.audit_logs WHERE entity_id IN ({BK_CUST}) OR entity_id IN ({BK_CASE})",
       "bk_customer_otps": f"SELECT id FROM booking.customer_otps WHERE customer_id IN ({BK_CUST})",
       "bk_customer_sessions": f"SELECT id FROM booking.customer_sessions WHERE customer_id IN ({BK_CUST})",
       "bk_customer_identities": f"SELECT customer_id FROM booking.customer_identities WHERE customer_id IN ({BK_CUST})",
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
6. **CIS check (DRY RUN job).** CIS holds no traveller data by design, so this step proves absence: it hashes the
   e-mail-shaped tokens in notification, job and audit text and compares them with the same hash, and compares the
   hash with the staff and alert-recipient e-mail columns. It takes the hash only; the API refuses an address.

   ```bash
   A=$(aws secretsmanager get-secret-value --secret-id aa-cis/dev/admin-secret --query SecretString --output text --profile aa365-admin --region us-west-1)
   curl -s -X POST https://api-cis.lumiguides.it.com/admin/job-runner/erasure/run -H "x-admin-secret: $A" -H "x-admin-role: admin" -H "content-type: application/json" -d '{"subject":"traveller","email_sha256":"<64-hex-characters>"}'
   ```

   Or on `/admin/data-erasure`, tab "Traveller (DSAR)": type the address there (it is hashed in the browser and
   cleared) and start the DRY RUN. Expected: `{"job_id": "...", "mode": "dry_run"}`. Read the result with
   `curl -s https://api-cis.lumiguides.it.com/admin/job-runner/jobs/<job_id> -H "x-admin-secret: $A" -H "x-admin-role: admin"`
   (or the admin Jobs page, kind `data_erasure`). Expected: `status` `succeeded`, every `rows` 0, `blocked` false.
   A non-zero `delete` or `redact` row is a CIS copy to erase in section 3 step 4b; a non-zero `manual` row
   (staff account, alert recipient, audit chain) is not a traveller erasure: record it and ask the tech lead. Abort: the job
   fails → read `error`; nothing was written.
7. Record the counts and full ids per tag in the DSAR work item, and the CIS job id and `fingerprint` as one pair. A
   traveller fingerprint is salted per DRY RUN, so it changes with every DRY RUN even when the counts do not: an
   approval names the fingerprint of that exact `dry_run_job_id`, and a new DRY RUN needs a new approval. No address,
   name or phone goes there.

**Access requests.** The task log must not hold row values, so this lookup cannot produce the copy the person asked
for. Personal values never go to workflow logs, the repo, Google Drive or a laptop (DM-6.3, DM-6.10). Until a tested
export exists (AA-839), delivery is manual and `[to be confirmed]`: staff read the Booking admin customer and
trip-case views and reply to the person from the support mailbox, stating that the TripPlanner record holds the same
contact details and consent (DM-6.2).

## 3. Erasure

**Tables and stores to cover** (AA-839 scope 1, as written):

- `booking.customers`, `booking.customer_identities` (the traveller sign-in link), and `customer_otps` /
  `customer_sessions` until Phase 4 drops them
- `booking.inbox_events.payload`
- `booking.trip_cases.notes` / `inquiry_snapshot`
- `booking.notifications`
- `booking.audit_logs` before/after jsonb: redact, never delete
- `tripplanner.customers`, `tripplanner.outbox.payload`, `tripplanner.sessions`, and
  `tripplanner.traveller_accounts` (the traveller sign-in account, linked through `sessions.account_id`)
- the Cognito EXTERNAL user
- the S3 archives written by AA-825

CIS (`data_erasure`, traveller): `shared.notifications` rows that carry the address (deleted), `shared.job`
payload / result / error that carry it (redacted), and a report of the staff, alert-recipient, audit and tenant
config matches (left for a person).

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
  `notification_reads` points at `notifications`; `customer_identities`, `customer_otps` and `customer_sessions`
  point at the customer.
  Children first, then trip cases, then the customer and the inbox events. The customer points at
  `booking.media_files` (`profile_media_id`, the `bk_media_files` ids): that row and its S3 object go after the
  customer.
- TripPlanner: `trip_drafts` and `trip_events` point at `sessions` (`session_id`), and `sessions` points at
  `customers` and at `traveller_accounts` (`account_id`). Drafts and events first, then sessions, then the customer
  and the traveller account.

1. **DRY RUN.** Re-run the section 2 lookup (counts and ids) and post the counts per table in the DSAR work item.
   Expected: the same counts and ids as the intake lookup. Abort: counts changed without explanation.
2. **Approval.** The tech lead approves the counts in the work item ([`destructive-ops.md`](../../skill/aa-cis-schema/references/destructive-ops.md)
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

   4b. **CIS**, only when the section 2 step 6 DRY RUN found `delete` or `redact` rows, and only while
   `ERASURE_APPLY_ENABLED=true` on the api and worker (Terraform, approved). From a Cognito staff session (admin role;
   the apply refuses a password session or the bare secret):

   The usual path is the apply panel of `/admin/data-erasure` on that DRY RUN (it builds the body from the DRY RUN
   job). The terminal equivalent:

   ```bash
   curl -s -X POST https://api-cis.lumiguides.it.com/admin/job-runner/erasure/run -H "Authorization: Bearer <staff-id-token>" -H "content-type: application/json" -d '{"subject":"traveller","email_sha256":"<64-hex>","dry_run":false,"dry_run_job_id":"<dry-run job id>","approved_fingerprint":"<its fingerprint>","approved_by":"<approver>","snapshot_id":"dsar-<yyyymmdd>-pre"}' # WRITE
   ```

   `approved_fingerprint` is the fingerprint the tech lead approved for exactly this `dry_run_job_id` (section 2 step 7):
   the fingerprint of another DRY RUN of the same person differs (its salt differs) and is refused. The job refuses
   unless the DRY RUN is a succeeded one for the same hash, at most 24 hours old, still holds its salt, and has
   `fingerprint_version` 2; it then recomputes the fingerprint with that DRY RUN's salt, and the recount in its
   transaction must give the same fingerprint. A DRY RUN made before the deploy of the subject-bound fingerprint (v1,
   no `fingerprint_version`) is refused: run a new DRY RUN after the deploy and get that one approved. It deletes / redacts exactly the approved rows, writes one
   `acp_shared.audit_log` row (`dsar.cis_erased`, counts only) and replaces the hash with `stripped-after-apply` in
   every `data_erasure` job row that holds it (this apply, its DRY RUN and any earlier DRY RUN of the request),
   removing each row's `subject_salt` with it.
   Expected: result `verified: true`. Abort: the job fails, nothing is committed. A DRY RUN serves one apply only,
   and a failed apply is never retried (the Jobs page retry answers 409): run a new DRY RUN, get it approved, and
   start a new apply.
5. **Cognito EXTERNAL user**, if one exists. Travellers can sign in to TripPlanner with an e-mail code (EXTERNAL
   pool, AA-908), so expect one when the lookup found a `tp_traveller_accounts` or `bk_customer_identities` row.
   The pool id comes from `aws cognito-idp list-user-pools --max-results 20 --profile aa365-admin --region us-west-1`.
   Cognito filters on the plain address, so type it at the prompt only: never in a script or file, and clear it from
   the shell history afterwards.

   ```bash
   aws cognito-idp list-users --user-pool-id <external-pool-id> --filter "email = \"<the-requester-address>\"" --profile aa365-admin --region us-west-1
   aws cognito-idp admin-delete-user --user-pool-id <external-pool-id> --username <username-from-list-users> --profile aa365-admin --region us-west-1 # WRITE
   ```

   Expected: `list-users` returns 0 or 1 user; after the delete it returns 0.
6. **S3 archives (AA-825).** Booking's inbox redaction rewrites rows in place and archives nothing
   (AA-Booking `backend/app/retention/policy.py`); job archives hold job rows. Check `archive/booking/` for an
   `inbox_events` prefix before assuming there is nothing to erase.
7. **Verify** from a new session: re-run the section 2 lookup with the same hash, the CIS DRY RUN (section 2 step 6)
   with `"verify": true`, and repeat the name check by hand:

   ```bash
   curl -s -X POST https://api-cis.lumiguides.it.com/admin/job-runner/erasure/run -H "x-admin-secret: $A" -H "x-admin-role: admin" -H "content-type: application/json" -d '{"subject":"traveller","email_sha256":"<64-hex-characters>","verify":true}'
   ```

   On `/admin/data-erasure` the verification DRY RUN is started from the finished apply (it uses the hash held in
   the page's memory; after a reload, type the address again). The verification job replaces the hash in its own
   row with `stripped-after-verify` when it ends (`result.hash_stripped: true`) and never stores a salt, so it
   leaves no copy behind.
   Expected: 0 rows in every tag and every CIS `delete` / `redact` row, the name found in no trip-case notes, and the
   Cognito user is gone.
8. **Delete the pre-erasure snapshot** once step 7 passes, so no manual copy of the person's data remains.

   ```bash
   aws rds delete-db-snapshot --db-snapshot-identifier dsar-<yyyymmdd>-pre --profile aa365-admin --region us-west-1 # WRITE
   ```

   Expected: `describe-db-snapshots --db-snapshot-identifier dsar-<yyyymmdd>-pre` returns `DBSnapshotNotFound`. The
   automated backups (7 days on Dev, `backup_retention_period = 7` in AA-CIS-Infra `modules/rds/main.tf`) still hold
   the erased rows and cannot be edited; they age out within 7 days of the erasure. The reply to the person can say so.

   The hash itself: after steps 4b and 7 no `data_erasure` job row holds it (apply and `verify` strip it), and a
   traveller job that failed or was cancelled had it replaced at once (`stripped-on-failed` / `stripped-on-cancelled`),
   so the AA-825 archive of failed jobs (`archive/job/`, 90 days) never carries it. Check:
   `SELECT count(*) FROM shared.job WHERE kind = 'data_erasure' AND payload ->> 'email_sha256' = '<64-hex>'` in a
   DB Migrate run-script (expected 0). Only a DRY RUN of a request that never reached an apply keeps it, until
   `retention_job` deletes that succeeded row after 30 days (not archived).
9. **Copies outside the database.**
   - **Staff mailbox:** each inquiry sent a `bk_notify_email` message with the traveller's name, e-mail and phone to
     the Booking staff inbox (AA-Booking `backend/app/notifications/staff_email.py`). Staff delete those
     messages, and the privacy request thread once it is closed, from that mailbox and its trash.
   - **Sentry:** CIS, Booking and TripPlanner send errors to Sentry with no default PII (`send_default_pii=False`)
     and no stack-frame locals (`include_local_variables=False`, AA-941, AA-871), so no event should hold the address
     or the hash. Search each of the three Sentry projects for the e-mail address anyway (in the Sentry search box,
     not in a file) and delete any event that holds it.
   Expected: 0 hits in the mailbox and in Sentry. Abort: none; record what was found.
10. **Record**: one `booking.audit_logs` row for the erasure (actor, action, entity, no personal data in `after`), a row
    in the [retention log](retention-log.md), and a reply to the person that the data is erased and that the backup
    copies expire within 7 days.

## 4. Tenant erasure (after offboarding)

`POST /admin/tenants/{id}/offboard` is **soft only**: it revokes the key and cancels queued jobs, deletes nothing, and
`/restore` brings the tenant back. Erasure is the separate, final step: after it the tenant cannot be restored. It
runs only after offboarding plus a retention window (`ERASURE_TENANT_RETENTION_DAYS`, default 30 days until the tech
lead sets the value), with the tech lead's explicit approval.

**What it covers in CIS** (inventory `services/erasure/inventory.py`; `GET /admin/job-runner/erasure` lists it live):

- **Deleted:** content and planning (T9 pieces, labels, publish log, T7/T8 subjects and angles, quarter/year plans,
  route picks), brand identity and its history, planning, export and SEO config, integrations rows, T2 versions,
  the tenant's own uploads and raw tours with everything derived from them (atoms, routes, rankings, photos, found
  through foreign keys), usage counters, API usage, notifications, the tenant's finished jobs, and the
  `shared.tenants` row last.
- **Detached** (row kept, tenant link nulled): `shared.llm_call_log`, `shared.decision_log`, `shared.dfs_call_log`,
  so platform cost history stays. **Merged:** `shared.llm_call_daily` rows are added into the platform (NULL tenant)
  row of the same day and key.
- **Kept:** `acp_shared.audit_log` (append-only hash chain) - the audit trail of the tenant, plus one `tenant.erased`
  row.
- **Outside the database** (operator steps below): bronze S3 `raw-inbox/<tenant>/` and `brand-identity/<tenant>/`,
  Secrets Manager `acp/cms/<tenant>` and `acp/social/<tenant>`; the tenant's CRM rows in AA-Partner (`crm`, DM-6.8);
  Cognito tenant users once AA-813 exists; Sentry events tagged with the tenant; automated backups (7 days).

A table that has `tenant_id` but no inventory entry is reported as `unregistered` and blocks the apply (CI fails on
it too). A row of another tenant, a kept row or another owner's row that points at a row to erase is a blocker, never
deleted.

1. **Account check.** `aws sts get-caller-identity --profile aa365-admin` → acc2. Abort on any other account.
2. **Offboarded?** The tenant shows "offboarded" on `/admin/tenants` (include inactive). If not, offboard it first
   (`POST /admin/tenants/{id}/offboard`, a reason is required) and wait for the retention window.
3. **DRY RUN.**

   ```bash
   A=$(aws secretsmanager get-secret-value --secret-id aa-cis/dev/admin-secret --query SecretString --output text --profile aa365-admin --region us-west-1)
   curl -s -X POST https://api-cis.lumiguides.it.com/admin/job-runner/erasure/run -H "x-admin-secret: $A" -H "x-admin-role: admin" -H "content-type: application/json" -d '{"subject":"tenant","tenant_id":"<tenant uuid>"}'
   curl -s https://api-cis.lumiguides.it.com/admin/job-runner/jobs/<job_id> -H "x-admin-secret: $A" -H "x-admin-role: admin"
   ```

   Expected: `status` `succeeded`; `result.tenant_state` `offboarded`; `result.blockers` empty; `result.unregistered`
   empty; `result.rows` lists rows per table and action (`delete`, `cascade`, `detach`, `merge`, `keep`,
   `null_first:*`); `result.s3` and `result.secrets` list what exists outside the DB (an `error` there means the
   worker could not look: check by hand with the commands of step 8); `result.s3_refs[]` lists, per DB column the
   apply deletes, the S3 keys outside the tenant's two prefixes (`outside_keys`): copy that list into the work item,
   it is the only pointer to those objects once the rows are gone; `result.fingerprint` is 64 hex characters.
   Abort: any blocker → resolve it first (wait for or cancel live jobs; a `cross_tenant` or `self_reference` row,
   e.g. another tenant's T2 version or a child job pointing at the tenant's rows, is a question for the tech lead;
   `s3_refs_unlisted` = more than 200 keys outside the prefixes, list them by hand first), then run a new DRY RUN.
4. **Approval.** Post the totals per action, the per-table rows, the DRY RUN job id and its fingerprint in the work
   item; the tech lead approves that fingerprint (destructive-ops.md step 1). The fingerprint binds the tenant id: it cannot
   approve another tenant with the same counts. A DRY RUN made before the deploy of the subject-bound fingerprint
   (no `fingerprint_version` in its result) is refused at apply: run a new DRY RUN after the deploy. Abort: no
   approval, no erasure.
5. **Snapshot** (destructive-ops.md step 2):

   ```bash
   aws rds create-db-snapshot --db-instance-identifier aa-cis-dev-db --db-snapshot-identifier tenant-erase-<yyyymmdd>-pre --profile aa365-admin --region us-west-1 # WRITE
   ```

   Expected: `available`. It holds the tenant's data: no `keep-` prefix, deleted in step 10.
6. **Enable the apply** (approved Terraform change in AA-CIS-Infra): `ERASURE_APPLY_ENABLED=true` on the api and
   worker task definitions, and `ERASURE_TENANT_RETENTION_DAYS` if the tech lead set a value; apply, then deploy CIS.
   Without it the API answers 403 and the job refuses. The only switch in Terraform today is the local
   `erasure_drill` in `accounts/aa365/main.tf`: `true` turns the apply on **and** sets the retention window to 0 days,
   so it is for a drill on a synthetic tenant only. A real tenant erasure needs a change that turns on the apply
   alone and keeps the window.
7. **Apply**, within 24 hours of the DRY RUN, from a Cognito staff session (admin role): the apply panel of
   `/admin/data-erasure` on that DRY RUN, or:

   ```bash
   curl -s -X POST https://api-cis.lumiguides.it.com/admin/job-runner/erasure/run -H "Authorization: Bearer <staff-id-token>" -H "content-type: application/json" -d '{"subject":"tenant","tenant_id":"<tenant uuid>","dry_run":false,"dry_run_job_id":"<dry-run job id>","approved_fingerprint":"<fingerprint>","approved_by":"<approver>","snapshot_id":"tenant-erase-<yyyymmdd>-pre"}' # WRITE
   ```

   One transaction: the recount must give the approved fingerprint and no blocker; nullable FK columns that close a
   cycle are nulled first, then detach, merge, and deletes children-first; every statement must touch exactly the
   approved rows; a recount must find 0; one `tenant.erased` audit row (counts, approval, snapshot id). Before the
   recount it locks the tenant row and checks again that the tenant is offboarded and past the retention window, so
   a restore in between stops it. Expected: result `verified: true`. Abort: the job fails with a reason, nothing is
   committed; the DRY RUN is used up and the apply is never retried: start again at step 3.
8. **Outside the database** (only after step 7 succeeded):

   ```bash
   aws s3 rm s3://aa-cis-bronze-005097885195/raw-inbox/<tenant uuid>/ --recursive --profile aa365-admin --region us-west-1 # WRITE
   aws s3 rm s3://aa-cis-bronze-005097885195/brand-identity/<tenant uuid>/ --recursive --profile aa365-admin --region us-west-1 # WRITE
   aws secretsmanager delete-secret --secret-id acp/cms/<tenant uuid> --recovery-window-in-days 7 --profile aa365-admin --region us-west-1 # WRITE
   aws secretsmanager delete-secret --secret-id acp/social/<tenant uuid> --recovery-window-in-days 7 --profile aa365-admin --region us-west-1 # WRITE
   ```

   Run only the lines whose object the DRY RUN listed. Then remove each key of the DRY RUN's
   `s3_refs[].outside_keys` (the bucket is the one in the key when it starts with `s3://`, else the bronze bucket):

   ```bash
   aws s3 rm s3://<bucket>/<key> --profile aa365-admin --region us-west-1 # WRITE
   ```

   Expected: `aws s3 ls` of each prefix and key prints nothing; `describe-secret` shows `DeletedDate`.
   **Retention archives (AA-825):** `s3://<bronze>/archive/{llm_call_log,tenant_api_usage,job,decision_log}/` hold
   gzipped JSONL rows archived before the erasure, some with the tenant id (cost rows, API usage, failed job
   payloads). They hold no personal data; the tech lead decides per erasure: keep them until their lifecycle expiry
   (record that decision in the work item), or scan the objects of the tenant's active months for the tenant id
   (S3 Select) and rewrite or remove the matching objects. Then the AA-Partner CRM erasure for the tenant (DM-6.8,
   its own runbook), and Sentry events tagged with the tenant id.
9. **Verify** with a new DRY RUN (step 3). Expected: every `delete`, `cascade`, `detach`, `merge` row 0 and
   `tenant_state` null; only the `keep` audit rows remain.
10. **Clean up:** delete the step 5 snapshot; set the apply back off (Terraform, then deploy CIS); add a row to the
    [retention log](retention-log.md) (tenant id, date, totals, job ids; no tenant content).

## 5. Test data and the Dev drill

Three linked test rows from the DM-6.5 consent check are kept for the first Dev test of the traveller part: see the
[retention log](retention-log.md#test-data-kept-for-the-erasure-test). Their address is a synthetic test address;
its hash is the traveller of the drill (CIS DRY RUN expected: all 0).

The synthetic tenant of the drill is made through the admin API, never with SQL (all with the admin secret and
`x-admin-role: admin`, as in section 4 step 3):

1. `POST /admin/tenants` with a name and slug starting `aa839-drill-` (the response holds the tenant id);
2. `PUT /admin/tenants/{id}/config` (one market, one channel) and `PUT /admin/tenants/{id}/brand-identity`, so the
   DRY RUN has rows to count;
3. `POST /admin/tenants/{id}/offboard` with reason `AA-839 erasure drill`;
4. section 4 steps 3-10, with `erasure_drill = true` in AA-CIS-Infra for the drill (apply on, retention 0 days;
   approved with step 6), and `erasure_drill = false` again in step 10.

This tenant drill ran on 2026-10-23 on the synthetic tenant `aa839-drill-1`: DRY RUN, approval, apply and
verification DRY RUN all passed, with the apply switched on for about 25 minutes
([evidence](../audits/2026-10-23-S248-aa839-erasure-drill/README.md)).

The CI tests (`tests/integration/test_aa839_erasure_job.py` in AA-CIS-App) run the same flow on synthetic rows for a
tenant (with a cross-tenant blocker and an FK cycle) and a traveller.
