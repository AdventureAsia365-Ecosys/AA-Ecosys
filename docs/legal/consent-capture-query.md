---
id: SEC-04-consent-query
title: Consent capture check (DM-6.5)
description: Read-only SQL that proves each customer's contact consent is stored with value, time and source in tripplanner.customers and the Booking master, and how to run it through DB Migrate run-script.
type: how-to
status: draft
owner: nghiep
audience: [engineer, cio]
applies_to: [tripplanner-lambda, aa-booking]
last_reviewed: 2026-10-20
review_every_days: 90
related: [SEC-04, AA-886, AA-676, AA-877, AA-839]
---

# Consent capture check (DM-6.5)

> [!WARNING]
> UNTESTED - do not follow in an incident without checking each step. The query has not run on Dev yet.

Data standard DM-6.5 ([`02-data-management.md`](../architecture/data-standards/02-data-management.md)) says:
consent MUST be stored with **value, timestamp and source**, and Booking's record is the master. This page holds
the read-only query that shows it, and the steps to run it. It is the evidence for the AA-886 done-when line "a
test inquiry stores consent value, time and source".

## Where consent lives

Column names are from [`db-schema-reference.md`](../architecture/db-schema-reference.md) (verified 2026-10-19).

| Step | Table | Value | Time | Source | Written by |
|---|---|---|---|---|---|
| 1. The traveller ticks the box and sends a trip | `tripplanner.customers` | `contact_consent` | `contact_consent_at` | implicit: the TripPlanner form | TripPanel form, then `backend/assembly/registration.py` (AA-676) |
| 2. Hand-off event | `tripplanner.outbox.payload` then `booking.inbox_events.payload` | `customer.consent` | `customer.consent_at` | `booking.inbox_events.source` = `tripplanner` | `backend/assembly/handoff.py`, contract `inquiry.submitted` v1.1/v1.2 |
| 3. Booking master | `booking.customers` | `contact_consent` | `contact_consent_at` | `source` = `tripplanner_lead` (CHECK `manual`, `otp`, `tripplanner_lead`) | AA-Booking `backend/app/inquiry/intake.py` |

`booking.customers.external_ref` holds `tripplanner.customers.id` (as text) when TripPlanner linked a customer, so
the two records join without comparing personal data. Each inquiry creates a new Booking lead row, so one
TripPlanner customer can have several Booking rows.

## The query

Four read-only statements. They print ids, booleans, timestamps and counts only: no name, email or phone
(`db/scripts/README.md` in AA-CIS-Infra forbids customer row values in the task log).

```sql
-- Q1. Coverage: how consent is recorded, per app (counts only).
SELECT 'booking' AS app, source, contact_consent, (contact_consent_at IS NOT NULL) AS has_time, count(*) AS n
FROM booking.customers
WHERE deleted_at IS NULL
GROUP BY 1, 2, 3, 4
UNION ALL
SELECT 'tripplanner', 'tripplanner_form', contact_consent, (contact_consent_at IS NOT NULL), count(*)
FROM tripplanner.customers
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4;

-- Q2. Integrity: consent without a time, or a time without consent. Expected: all zero.
SELECT 'booking' AS app,
       count(*) FILTER (WHERE contact_consent AND contact_consent_at IS NULL)         AS consent_without_time,
       count(*) FILTER (WHERE NOT contact_consent AND contact_consent_at IS NOT NULL) AS time_without_consent
FROM booking.customers
WHERE deleted_at IS NULL
UNION ALL
SELECT 'tripplanner',
       count(*) FILTER (WHERE contact_consent AND contact_consent_at IS NULL),
       count(*) FILTER (WHERE NOT contact_consent AND contact_consent_at IS NOT NULL)
FROM tripplanner.customers;

-- Q3. Chain: does the Booking master carry the same consent as the TripPlanner record it came from?
--     Expected: value_mismatch = 0, time_mismatch = 0, wrong_source = 0.
SELECT count(DISTINCT t.id)                                                            AS tp_customers,
       count(DISTINCT t.id) FILTER (WHERE b.id IS NOT NULL)                            AS tp_customers_in_booking,
       count(b.id)                                                                     AS booking_leads,
       count(b.id) FILTER (WHERE b.contact_consent IS DISTINCT FROM t.contact_consent)       AS value_mismatch,
       count(b.id) FILTER (WHERE b.contact_consent_at IS DISTINCT FROM t.contact_consent_at) AS time_mismatch,
       count(b.id) FILTER (WHERE b.source <> 'tripplanner_lead')                       AS wrong_source
FROM tripplanner.customers t
LEFT JOIN booking.customers b ON b.external_ref = t.id::text AND b.deleted_at IS NULL;

-- Q4. One test inquiry, end to end. $1 = a LIKE pattern on the test email, e.g. 'aa886-consent-test%@example.com'.
SELECT 'tripplanner.customers' AS step, t.id::text AS id, NULL::text AS source,
       t.contact_consent AS consent, t.contact_consent_at AS consent_at, t.created_at AS at
FROM tripplanner.customers t
WHERE lower(t.email) LIKE $1
UNION ALL
SELECT 'booking.inbox_events', i.id::text, i.source,
       (i.payload -> 'customer' ->> 'consent')::boolean,
       (i.payload -> 'customer' ->> 'consent_at')::timestamptz,
       i.received_at
FROM booking.inbox_events i
WHERE i.contract = 'inquiry.submitted' AND lower(i.payload -> 'customer' ->> 'email') LIKE $1
UNION ALL
SELECT 'booking.customers', b.id::text, b.source, b.contact_consent, b.contact_consent_at, b.created_at
FROM booking.customers b
WHERE b.deleted_at IS NULL AND lower(b.email) LIKE $1
ORDER BY at;
```

Notes:

- Q3 `time_mismatch` can be non-zero for a legitimate reason: when the contact matched an existing TripPlanner
  customer, the hand-off carries a snapshot with `customer_id` null, `consent_at` = the submit time, and no
  `external_ref`. Those rows do not join, so they do not count. A row that joins and still differs is a defect.
- Q4 reads `booking.inbox_events.payload`. After 90 days the payload's personal data is redacted (DM-6.6), so run
  the test-inquiry check within that window.
- `contact_consent` covers "an advisor may contact me about this trip". It is not marketing consent; DM-6.5 says it
  MUST be checked before any marketing use.

## How to run it

The query reads `booking.*` and `tripplanner.*`, which only the RDS master can read since X1 (the CIS task role cannot,
and ECS exec runs as `cis_app`). So it runs through **DB Migrate `mode=run-script`** in AA-CIS-Infra, as a reviewed
read-only script (contract: `db/scripts/README.md` in the AA-CIS-Infra repo).

1. Send a test inquiry on the live Trip Planner: build a short trip, open "Send to an advisor", name
   `AA886 consent test`, email `aa886-consent-test+<yyyymmdd><letter>@example.com` (a new address each run:
   TripPlanner refuses to create a second customer for an email it already holds), tick the consent box, send.
   Expected: "Sent to advisor". Abort if the form refuses the address.
2. Wait for Booking intake: the `bk_inquiry_pull` recurring job runs every 60 seconds; allow a few minutes. Q4 in
   step 4 shows whether it arrived (a `booking.inbox_events` row).
3. Open an AA-CIS-Infra PR adding `db/scripts/dm65_consent_capture.py` (below). CI checks the shape. Merge it.
4. Dispatch DB Migrate on `main`: `mode=run-script`, `script=db/scripts/dm65_consent_capture.py`, `migration` and
   `role` empty. Expected: exit 0 and the `SCRIPT` lines in the job log.
5. Save the job log lines to `docs/audits/<date>-S<nnn>-aa886-consent/` and link them on the Linear issue.
6. Leave the test rows in place and list their ids in the audit folder: the AA-839 erasure runbook removes them.

Expected result for a correct capture (Q4): three rows (`tripplanner.customers`, `booking.inbox_events`,
`booking.customers`), each with consent `true` and a time; the Booking row has source `tripplanner_lead`. If the
TripPlanner row is missing, the email was already known (see step 1).

### Script for AA-CIS-Infra

```python
"""DM-6.5 consent capture check (AA-886): consent value, time and source in tripplanner.customers and the
Booking master. Read-only; prints ids, booleans, timestamps and counts only (no name, email or phone).
Query text: AA-Ecosys docs/legal/consent-capture-query.md.
"""

READ_ONLY = True

TEST_EMAIL_PATTERN = "aa886-consent-test%@example.com"

Q1 = """
SELECT 'booking' AS app, source, contact_consent, (contact_consent_at IS NOT NULL) AS has_time, count(*) AS n
FROM booking.customers WHERE deleted_at IS NULL GROUP BY 1, 2, 3, 4
UNION ALL
SELECT 'tripplanner', 'tripplanner_form', contact_consent, (contact_consent_at IS NOT NULL), count(*)
FROM tripplanner.customers GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4
"""

Q2 = """
SELECT 'booking' AS app,
       count(*) FILTER (WHERE contact_consent AND contact_consent_at IS NULL) AS consent_without_time,
       count(*) FILTER (WHERE NOT contact_consent AND contact_consent_at IS NOT NULL) AS time_without_consent
FROM booking.customers WHERE deleted_at IS NULL
UNION ALL
SELECT 'tripplanner',
       count(*) FILTER (WHERE contact_consent AND contact_consent_at IS NULL),
       count(*) FILTER (WHERE NOT contact_consent AND contact_consent_at IS NOT NULL)
FROM tripplanner.customers
"""

Q3 = """
SELECT count(DISTINCT t.id) AS tp_customers,
       count(DISTINCT t.id) FILTER (WHERE b.id IS NOT NULL) AS tp_customers_in_booking,
       count(b.id) AS booking_leads,
       count(b.id) FILTER (WHERE b.contact_consent IS DISTINCT FROM t.contact_consent) AS value_mismatch,
       count(b.id) FILTER (WHERE b.contact_consent_at IS DISTINCT FROM t.contact_consent_at) AS time_mismatch,
       count(b.id) FILTER (WHERE b.source <> 'tripplanner_lead') AS wrong_source
FROM tripplanner.customers t
LEFT JOIN booking.customers b ON b.external_ref = t.id::text AND b.deleted_at IS NULL
"""

Q4 = """
SELECT 'tripplanner.customers' AS step, t.id::text AS id, NULL::text AS source,
       t.contact_consent AS consent, t.contact_consent_at AS consent_at, t.created_at AS at
FROM tripplanner.customers t WHERE lower(t.email) LIKE $1
UNION ALL
SELECT 'booking.inbox_events', i.id::text, i.source,
       (i.payload -> 'customer' ->> 'consent')::boolean,
       (i.payload -> 'customer' ->> 'consent_at')::timestamptz, i.received_at
FROM booking.inbox_events i
WHERE i.contract = 'inquiry.submitted' AND lower(i.payload -> 'customer' ->> 'email') LIKE $1
UNION ALL
SELECT 'booking.customers', b.id::text, b.source, b.contact_consent, b.contact_consent_at, b.created_at
FROM booking.customers b WHERE b.deleted_at IS NULL AND lower(b.email) LIKE $1
ORDER BY at
"""


def _line(tag, row):
    print(f"SCRIPT {tag} " + " ".join(f"{k}={row[k]}" for k in row.keys()), flush=True)


async def main(conn):
    for row in await conn.fetch(Q1):
        _line("coverage", row)
    for row in await conn.fetch(Q2):
        _line("integrity", row)
    _line("chain", await conn.fetchrow(Q3))
    rows = await conn.fetch(Q4, TEST_EMAIL_PATTERN)
    print(f"SCRIPT test_inquiry rows={len(rows)}", flush=True)
    for row in rows:
        _line("test_inquiry", row)
```
