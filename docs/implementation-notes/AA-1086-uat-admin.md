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
- **Steps 1b and 12b: the act is not filmed, the result is.** The tech lead provisions the marker and ends its pilot;
  the API answers stay JSON evidence (job steps, `pilot_taken`, `changed` true, the audit row, the pilot slot query).
  `REH-01b-pilot-on` / `REH-12b-pilot-off` then film Tenant 360 › Subscription of the marker (env
  `UAT_REH_MARKER_ID`). The marker is the Dev pilot then, so it is not on the pilot guard's allow-list: each scenario
  reads the tenant through the admin API before the first paint and stops with `pilot_guard` unless it carries the
  invented name "E2E Pilot Rehearsal Marker" and kind agency (the runbook now names it so).
- **Booking writers as identities.** `booking-staff`, `booking-maker`, `booking-checker` (A10e) sign in through
  `lib/signin.cjs` like `booking`, codes from `inbound-admin/`; a reused session must answer staff/me for the same
  address. They are writable and write-set only.
- **The rehearsal agency on the pilot guard** by id (`crmKey`), both scopes: its id is public in the runbook.
- **Seeder output as input.** The write scenarios read the Booking seeder's APPLY JSON (`UAT_BOOKING_FIXTURES`) and
  refuse a file of any other agency before the browser opens; `allowWrites` is narrowed to that run's record ids.

## Changed

- The dry-run manifest gains `REH-00-baseline` only (platform pages, no fixture). `REH-01-provisioned`,
  `REH-01-crm-agency` and `REH-01-booking-partner` need the rehearsal fixture, which Dev does not hold until the live
  rehearsal: they stay out of the routine dry run (review S279) and are recorded with `run.sh` like the other
  state-dependent ones.
- Review fixes (S279): `REH-12-budget-off` waits for the budget source line before asserting it (it passed before the
  read loaded); `REH-12-budget-on` checks the override's reason, author and end date; `REH-01-crm-agency` asserts the
  loaded Seats tile and the owner-exists note, and loads more agency pages until the agency shows; captions name the
  "Usage & Billing" tab and no longer claim an idle queue or a noted spend at step 0.
- `limitWrites` (`lib/uat-page.cjs`) caps every write method on a rule's path, not only POST: a rule names its
  `method` (default POST); any other write method there is aborted, and all count against the same `max`.
- Catalogue rows for the step 1 parts with no page: `REH-01c-real-refused` (the 422 of a second real agency) and
  `REH-01-ai-budget`, both blocked / manual.
- `tests/dryrun.test.cjs`: the writable list and the "dry run covers every identity" check know the write-only ones.

## Tradeoffs

- The Booking partner is found through `GET /pricing/partner-terms` instead of the Agencies tab, so no other agency's
  name is on screen (the Booking kit table has no per-table hook for a scoped row blur).
- `REH-11-checker` allows the approve of any payment id in the browser (the id is only known on the page); Booking
  still refuses a payment of a real agency and the checker's own recordings.

## Should know

- The values the scenarios compare against (0.05 USD override, at least 3 priced tours) are the rehearsal's own inputs
  from the runbook, not app thresholds, so there is no settings registry value to read for them.

- `REH-01-prices` fails until the price import is done (Dev had 1 priced, sellable tour with a from-price on
  2026-11-13); `REH-02-members` fails until the owner accepted; `REH-12-budget-on` fails until the override is set.
- The Booking seeder copies a template hold of the agency: run it for the rehearsal agency only after step 8 booked a
  trip for it.

## S280 update: who makes the admin writes

### Decisions

- **The admin-role writes are not the tech lead's alone.** Provisioning the marker as the Dev pilot, the second-pilot
  probe, the `ai.budget_usd_monthly` override and its removal, End pilot and the marker's offboarding are admin-role
  writes on existing routes (`tenant.write`, `_require_tenant_admin`). What keeps the Dev-only E2E admin (A10b) out is
  its read-only session, not a person-only rule. The orchestrator can make them through the admin route with the main
  admin secret and `x-admin-role: admin` (the same pattern as the existing orchestrator-only LLM key tool under
  `tools/llm/`), with its own `x-admin-user-id` as the audit actor. So the narration of `REH-01b-pilot-on`,
  `REH-12-budget-on`, `REH-12-budget-off` and `REH-12b-pilot-off` names "an administrator", not "the tech lead": the
  take stays true whoever made the write.
- The erasure approval of the offboarded marker stays a person's act (the erasure saga's own rule).

### Changed

- Four CIS admin scenarios: English and Vietnamese narration and the header comments are actor-neutral. Asserts are
  unchanged.
- Catalogue notes of `REH-01b-pilot-start`, `REH-12-budget-set` and `REH-12b-pilot-end` name the admin-role write
  (orchestrator or tech lead); status and identity are unchanged (`blocked`, `manual`: no scenario films the write).

### Tradeoffs

- The main admin secret carries header trust (any role it names). Using it for these writes matches the existing
  orchestrator tooling and the dev-phase rule; the audit rows name the agent, so they stay apart from the tech lead's.

### Should know

- The override row's "granted by" cell then reads `admin:<the agent's actor id>`; `REH-12-budget-on` only asserts
  that the cell is not empty.
