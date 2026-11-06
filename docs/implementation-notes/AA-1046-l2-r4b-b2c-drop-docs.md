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
