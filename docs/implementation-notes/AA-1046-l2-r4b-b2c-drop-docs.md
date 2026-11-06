# AA-1046 lane l2-r4b-b2c-drop: root docs for the B2C drop (S271)

Second root PR of the lane (the first fixes the DRY RUN pins, `docs/audits/2026-11-05-S270-aa1037-b2c-drop-dryrun/`).
It moves the root text off the dropped Booking objects so it agrees with the code PRs of the same lane.

## Decisions

- **The KPI registry moves with CIS.** `docs/reports/kpis.yaml` and `catalog.yaml` are byte copies of the AA-CIS-App
  registry: the agency money KPIs (aging, overdue, unverified, cash, invoiced) read `booking.agency_invoice`,
  `booking.agency_payment` and `booking.v_tenant_billing_status` (v2); the customer-source KPI has no source left; the
  consent KPI reads `crm.consent` only. Merge together with the CIS PR (the registry check compares the copies).
- **The customer contract is kept, marked retired.** `booking.customer.v1.openapi.yaml` stays as the record of what
  was served (the contracts CI still checks its samples); the README row and the file say it is retired and that no
  consumer may call it. Deleting it would also drop the field-policy samples that prove the old surface never leaked a
  staff member or a net cost.
- **Registry rows stay until the drop is applied.** The dead-table rows now name `045_aa1037_retire_b2c.sql`
  (state still `candidate`, approval pending); the DM-7.1 rows say `retired: dropped by bk-045`. After the apply the
  orchestrator turns them to `dropped` with the run ids, as for tp-018.

## Changed

- `docs/contracts/ops.overview.v1.md`: the `booking.v_ops_inquiry_inbox` row is retired; the example probe cell is
  `cross.cis_app.booking.trip_cases` (the Infra probe moved off `booking.customers`).
- `docs/architecture/data-standards/02-data-management.md`: E8 row, the customers KPI row, DM-6.2, DM-6.5, DM-6.7,
  the DM-7.1 rows of the credential, identity, money and archive tables, and an S271 note.

## Should know

- No number from Dev is in this PR: the DRY RUN has not run yet (it runs after the Booking code PR deploys).

## Review fixes (S271)

- **DSAR runbook** (`docs/legal/dsar-erasure-runbook.md`, DM-6.7's required path): sections 2 and 3 no longer name
  the dropped tables. A traveller's kept b2c cases are found through the hand-off row (`trip_cases.inbox_event_id`,
  hash of `payload.customer.email`, while unredacted) and, lastingly, through the TripPlanner trip id
  (`trip_cases.source_id` = `tripplanner.trip_events.trip_id` of the person's sessions). `inquiry_snapshot` holds no
  contact (days and legs only, Booking `app/inquiry/contract.py`), so it is not a lookup key. New lookups on
  `booking.retired_b2c_record` (`record ->> 'bill_to_email'` hash or `trip_case_id`, then the item, schedule and
  payment rows by `invoice_id`) and a redact-in-place step on the `pii:`-tagged keys of the source tables. The lookup
  outline ran on PostgreSQL 16 against a minimal schema with invented rows: the case was found through the trip id
  with the inbox payload already redacted.
- **Consent query** (`docs/legal/consent-capture-query.md`): TripPlanner part on `tripplanner.customers` and its
  unredacted hand-off rows (same text as the Infra script `db/scripts/dm65_consent_capture.py`), CRM part on
  `crm.consent` (per tenant: FORCE RLS, so not a master run-script). K-PRIV-CONSENT (here and in the CIS copy)
  names the three sources.
- **UAT**: BK-08 opens Supplier bills, Agency billing and Trip checks; BK-10 the audit log and staff (`/customers`
  is gone). `catalogue.json` stories follow. `node --test tools/uat/tests/*.test.cjs`: 90 passed.
