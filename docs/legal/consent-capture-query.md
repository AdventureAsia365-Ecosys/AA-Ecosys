---
id: SEC-04-consent-query
title: Consent capture check (DM-6.5)
description: Read-only SQL that proves traveller contact consent is stored with value, time and source in tripplanner.customers and its Booking hand-off, where agency consent lives (crm.consent), and how to run it through DB Migrate run-script.
type: how-to
status: draft
owner: nghiep
audience: [engineer, cio]
applies_to: [tripplanner-lambda, aa-booking, aa-partner]
last_reviewed: 2026-11-06
review_every_days: 90
last_tested: 2026-10-20
tested_where: dev-acc2
tested_evidence: AA-886 Linear comment of 2026-10-20 (DB Migrate run-script run 39363696312)
related: [SEC-04, AA-886, AA-676, AA-877, AA-839, AA-1046]
---

# Consent capture check (DM-6.5)

Data standard DM-6.5 ([`02-data-management.md`](../architecture/data-standards/02-data-management.md)) says:
consent MUST be stored with **value, timestamp and source**. This page holds the read-only query that shows it, and
the steps to run it. It is the evidence for the AA-886 done-when line "a test inquiry stores consent value, time and
source", and the source of KPI K-PRIV-CONSENT (`docs/reports/kpis.yaml`).

> [!NOTE]
> Since Booking bk-045 (AA-1046, root ADR 0019: B2B-only) Booking keeps no customer master: `booking.customers` and
> its consent columns were dropped. The TripPlanner part below checks `tripplanner.customers` and its hand-off rows
> in `booking.inbox_events` (kept, personal data redacted after 90 days). Consent of an agency's travellers is held
> per purpose in `crm.consent` (AA-Partner); see "CRM part". The 2026-10-20 result below predates the drop.

## Result on Dev (2026-10-20)

Ran once on Dev (acc2) through DB Migrate `mode=run-script`, run 39363696312, after a test inquiry through the live
TripPlanner form (consent ticked). Evidence: the AA-886 Linear comment of 2026-10-20.

- Test inquiry (with the query of that date, which still read `booking.customers`): 3 rows,
  `tripplanner.customers` → `booking.inbox_events` (source tripplanner) → `booking.customers`
  (source `tripplanner_lead`), each with consent `true` and the same consent time (2026-10-20 03:16:26Z).
- Integrity: consent without a time 0, a time without consent 0, in both apps.
- Chain: value, time and source mismatches 0 across 5 linked customers.
- The three test rows are kept for the first erasure test (see the
  [retention log](retention-log.md#test-data-kept-for-the-erasure-test)).

## Where consent lives

Column names are from [`db-schema-reference.md`](../architecture/db-schema-reference.md) (dump of 2026-10-28).

| Step | Table | Value | Time | Source | Written by |
|---|---|---|---|---|---|
| 1. The traveller ticks the box and sends a trip | `tripplanner.customers` | `contact_consent` | `contact_consent_at` | implicit: the TripPlanner form | TripPanel form, then `backend/assembly/registration.py` (AA-676) |
| 2. Hand-off event | `tripplanner.outbox.payload` then `booking.inbox_events.payload` | `customer.consent` | `customer.consent_at` | `booking.inbox_events.source` = `tripplanner` | `backend/assembly/handoff.py`, contract `inquiry.submitted` v1.1/v1.2 |
| ~~3. Booking master~~ | retired: `booking.customers` was dropped by bk-045 (AA-1046) | | | | |
| Agency travellers (B2B) | `crm.consent` (one row per purpose, append-only) | `value` | `at` | `source` (`form`, `portal`, `agent_recorded`, `import`) | AA-Partner CRM |

The hand-off payload carries `customer.customer_id` = `tripplanner.customers.id` (as text) when TripPlanner linked
a customer, so the two records join without comparing personal data. Each trip sent is one hand-off row, so one
TripPlanner customer can have several.

## The query (TripPlanner part)

Four read-only statements. They print ids, booleans, timestamps and counts only: no name, email or phone
(`db/scripts/README.md` in AA-CIS-Infra forbids customer row values in the task log).

```sql
-- Q1. Coverage: how consent is recorded (counts only).
SELECT 'tripplanner' AS app, 'tripplanner_form' AS source, contact_consent,
       (contact_consent_at IS NOT NULL) AS has_time, count(*) AS n
FROM tripplanner.customers GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4;

-- Q2. Integrity: consent without a time, or a time without consent. Expected: all zero.
SELECT 'tripplanner' AS app,
       count(*) FILTER (WHERE contact_consent AND contact_consent_at IS NULL) AS consent_without_time,
       count(*) FILTER (WHERE NOT contact_consent AND contact_consent_at IS NOT NULL) AS time_without_consent
FROM tripplanner.customers;

-- Q3. Chain: does each hand-off row carry the same consent as the TripPlanner record it came from? Unredacted
--     inquiry.submitted rows only (DM-6.6 redacts the payload after 90 days).
--     Expected: value_mismatch = 0, time_mismatch = 0, wrong_source = 0.
SELECT count(DISTINCT t.id) AS tp_customers,
       count(DISTINCT t.id) FILTER (WHERE i.id IS NOT NULL) AS tp_customers_handed_off,
       count(i.id) AS handoffs,
       count(i.id) FILTER (WHERE (i.payload -> 'customer' ->> 'consent')::boolean
                                 IS DISTINCT FROM t.contact_consent) AS value_mismatch,
       count(i.id) FILTER (WHERE (i.payload -> 'customer' ->> 'consent_at')::timestamptz
                                 IS DISTINCT FROM t.contact_consent_at) AS time_mismatch,
       count(i.id) FILTER (WHERE i.source <> 'tripplanner') AS wrong_source
FROM tripplanner.customers t
LEFT JOIN booking.inbox_events i ON i.contract = 'inquiry.submitted' AND i.redacted_at IS NULL
     AND i.payload -> 'customer' ->> 'customer_id' = t.id::text;

-- Q4. One test inquiry, end to end. $1 = a LIKE pattern on the test email, e.g. 'aa886-consent-test%@example.com'.
SELECT 'tripplanner.customers' AS step, t.id::text AS id, NULL::text AS source,
       t.contact_consent AS consent, t.contact_consent_at AS consent_at, t.created_at AS at
FROM tripplanner.customers t WHERE lower(t.email) LIKE $1
UNION ALL
SELECT 'booking.inbox_events', i.id::text, i.source,
       (i.payload -> 'customer' ->> 'consent')::boolean,
       (i.payload -> 'customer' ->> 'consent_at')::timestamptz, i.received_at
FROM booking.inbox_events i
WHERE i.contract = 'inquiry.submitted' AND i.redacted_at IS NULL
  AND lower(i.payload -> 'customer' ->> 'email') LIKE $1
ORDER BY at;
```

Notes:

- Q3 `time_mismatch` can be non-zero for a legitimate reason: when the contact matched an existing TripPlanner
  customer, the hand-off carries a snapshot with `customer_id` null and `consent_at` = the submit time. Those rows
  do not join, so they do not count. A row that joins and still differs is a defect.
- Q3 and Q4 read `booking.inbox_events.payload`. After 90 days the payload's personal data is redacted (DM-6.6), so
  run the test-inquiry check within that window. Booking no longer pulls new hand-offs since its B2C intake was
  retired (AA-1046), so the chain covers the rows that came in before that.
- `contact_consent` covers "an advisor may contact me about this trip". It is not marketing consent; DM-6.5 says it
  MUST be checked before any marketing use.

## CRM part (agency travellers)

`crm.consent` holds one append-only row per traveller and purpose (`contact`, `marketing`, `health_data`,
`ops_release`, `ai_processing`, `terms`) with `value`, `at` and `source`; the latest row per (`traveler_id`,
`purpose`) is the current answer. The table has RLS with FORCE per tenant (`app.tenant_id`), so the master
run-script below cannot count it across tenants: the CRM part of K-PRIV-CONSENT has to be computed inside each
tenant's session (C1). Not run yet on Dev.

```sql
-- C1. Per tenant session: current consent per purpose and source (counts only).
SELECT purpose, value, source, count(*) AS n
FROM (SELECT DISTINCT ON (traveler_id, purpose) purpose, value, source
      FROM crm.consent ORDER BY traveler_id, purpose, at DESC) c
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
```

## How to run it

The TripPlanner part reads `booking.*` and `tripplanner.*`, which only the RDS master can read since X1 (the CIS task role cannot,
and ECS exec runs as `cis_app`). So it runs through **DB Migrate `mode=run-script`** in AA-CIS-Infra, as a reviewed
read-only script (contract: `db/scripts/README.md` in the AA-CIS-Infra repo).

1. Send a test inquiry on the live Trip Planner: build a short trip, open "Send to an advisor", name
   `AA886 consent test`, email `aa886-consent-test+<yyyymmdd><letter>@example.com` (a new address each run:
   TripPlanner refuses to create a second customer for an email it already holds), tick the consent box, send.
   Expected: "Sent to advisor". Abort if the form refuses the address.
2. Since the Booking B2C intake was retired (AA-1046) no new hand-off reaches `booking.inbox_events`: Q4 then shows
   the `tripplanner.customers` row only, and the chain is checked on the older hand-off rows (Q3).
3. `db/scripts/dm65_consent_capture.py` is in AA-CIS-Infra (the script below, same text). A change to it goes
   through an AA-CIS-Infra PR; CI checks the shape.
4. Dispatch DB Migrate on `main`: `mode=run-script`, `script=db/scripts/dm65_consent_capture.py`, `migration` and
   `role` empty. Expected: exit 0 and the `SCRIPT` lines in the job log.
5. Save the job log lines to `docs/audits/<date>-S<nnn>-aa886-consent/` and link them on the Linear issue.
6. Leave the test rows in place and list their ids in the audit folder: the AA-839 erasure runbook removes them.

Expected result for a correct capture (Q4): the `tripplanner.customers` row with consent `true` and a time, plus
the `booking.inbox_events` row (source `tripplanner`, same consent and time) for an inquiry sent before the intake was
retired. If the TripPlanner row is missing, the email was already known (see step 1).

### Script for AA-CIS-Infra

```python
"""DM-6.5 consent capture check (AA-886; AA-1046 after Booking bk-045): consent value, time and source in
tripplanner.customers and in its hand-off to Booking (booking.inbox_events, inquiry.submitted). Read-only; prints
ids, booleans, timestamps and counts only (no name, email or phone).
Query text: AA-Ecosys docs/legal/consent-capture-query.md.

bk-045 (AA-1037, root ADR 0019) dropped the Booking customer master (booking.customers): Booking keeps no traveller
consent of its own any more. The hand-off rows stay under DM-6.6 (personal data redacted after 90 days), so the chain
check reads the unredacted ones only. Consent of an agency's travellers lives in crm.consent (RLS per tenant): the
CRM part of the page, not this master script.
"""

READ_ONLY = True

TEST_EMAIL_PATTERN = "aa886-consent-test%@example.com"

Q1 = """
SELECT 'tripplanner' AS app, 'tripplanner_form' AS source, contact_consent,
       (contact_consent_at IS NOT NULL) AS has_time, count(*) AS n
FROM tripplanner.customers GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4
"""

Q2 = """
SELECT 'tripplanner' AS app,
       count(*) FILTER (WHERE contact_consent AND contact_consent_at IS NULL) AS consent_without_time,
       count(*) FILTER (WHERE NOT contact_consent AND contact_consent_at IS NOT NULL) AS time_without_consent
FROM tripplanner.customers
"""

Q3 = """
SELECT count(DISTINCT t.id) AS tp_customers,
       count(DISTINCT t.id) FILTER (WHERE i.id IS NOT NULL) AS tp_customers_handed_off,
       count(i.id) AS handoffs,
       count(i.id) FILTER (WHERE (i.payload -> 'customer' ->> 'consent')::boolean
                                 IS DISTINCT FROM t.contact_consent) AS value_mismatch,
       count(i.id) FILTER (WHERE (i.payload -> 'customer' ->> 'consent_at')::timestamptz
                                 IS DISTINCT FROM t.contact_consent_at) AS time_mismatch,
       count(i.id) FILTER (WHERE i.source <> 'tripplanner') AS wrong_source
FROM tripplanner.customers t
LEFT JOIN booking.inbox_events i ON i.contract = 'inquiry.submitted' AND i.redacted_at IS NULL
     AND i.payload -> 'customer' ->> 'customer_id' = t.id::text
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
WHERE i.contract = 'inquiry.submitted' AND i.redacted_at IS NULL
  AND lower(i.payload -> 'customer' ->> 'email') LIKE $1
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
