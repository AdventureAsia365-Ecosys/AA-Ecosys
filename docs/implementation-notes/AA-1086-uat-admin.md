# AA-1086: pilot rehearsal UAT scenarios, staff side (CIS admin and Booking staff)

Scenarios `REH-*` for the rehearsal steps 0, 1, 1b, 2, 9, 11, 12 and 12b of
[the pilot rehearsal plan](../ops/runbooks/pilot-rehearsal.md), plus the price setup result (AA-1091).
Catalogue rows in `tools/uat/catalogue.json`; helper `tools/uat/lib/rehearsal-admin.cjs`.

## Decisions

- **Ids** `REH-<nn>[letter]-<slug>`: the catalogue id rule gained this form (and `DRILL-<nn>-<slug>`).
- **Read-only evidence, hand writes.** Every CIS write of these steps (owner invitation, AI budget override and its
  removal, pilot start and end) and the Booking price import belong to the tech lead: no Dev-only E2E identity may make
  them (root ADR 0006a A10b, A10e). They are catalogue rows with status `blocked`, identity `manual`, and a note; the
  filmed scenario is the read-only result right after the hand step (`REH-02-members`, `REH-12-budget-on`,
  `REH-12-budget-off`, `REH-01-prices`, `REH-01-from-price`).
- **Steps 1b and 12b are not filmed.** The marker tenant is the pilot while they run; the pilot guard never puts the
  pilot on camera. Evidence = the API answers saved as JSON (job steps, `pilot_taken`, `changed` true, the audit row,
  the pilot slot query).
- **Booking writers as identities.** `booking-staff`, `booking-maker`, `booking-checker` (A10e) sign in through
  `lib/signin.cjs` like `booking`, codes from `inbound-admin/`; a reused session must answer staff/me for the same
  address. They are writable and write-set only.
- **The rehearsal agency on the pilot guard** by id (`crmKey`), both scopes: its id is public in the runbook.
- **Seeder output as input.** The write scenarios read the Booking seeder's APPLY JSON (`UAT_BOOKING_FIXTURES`) and
  refuse a file of any other agency before the browser opens; `allowWrites` is narrowed to that run's record ids.

## Changed

- The dry-run manifest gains the four stable read-only scenarios (`REH-00-baseline`, `REH-01-provisioned`,
  `REH-01-crm-agency`, `REH-01-booking-partner`). The state-dependent ones are recorded with `run.sh`.
- `tests/dryrun.test.cjs`: the writable list and the "dry run covers every identity" check know the write-only ones.

## Tradeoffs

- The Booking partner is found through `GET /pricing/partner-terms` instead of the Agencies tab, so no other agency's
  name is on screen (the Booking kit table has no per-table hook for a scoped row blur).
- `REH-11-checker` allows the approve of any payment id in the browser (the id is only known on the page); Booking
  still refuses a payment of a real agency and the checker's own recordings.

## Should know

- `REH-01-prices` fails until the price import is done (Dev had 1 priced, sellable tour with a from-price on
  2026-11-13); `REH-02-members` fails until the owner accepted; `REH-12-budget-on` fails until the override is set.
- The Booking seeder copies a template hold of the agency: run it for the rehearsal agency only after step 8 booked a
  trip for it.
