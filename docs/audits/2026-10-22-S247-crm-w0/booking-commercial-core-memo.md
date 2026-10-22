# Booking commercial-core memo: B2B lane (AA-972…AA-975) vs Booking operations (AA-682)

S247, 22/10/2026. Agent: Claude Code (AA-928). Read-only note for the Booking lane; nothing applied. Sources: root
ADR 0005 / [0005a](../../adr/0005a-b2b-resale-warn-and-vnd.md), [0008a](../../adr/0008a-crm-separate-app-exceptions.md)
decision 3, the contract [`booking.b2b.v1`](../../contracts/booking.b2b.v1.openapi.yaml), the CRM final design §5.3,
the live schema [`db-schema-reference.md`](../../architecture/db-schema-reference.md) (Booking at **bk-018**, verified
21/10/2026) and the AA-682 issue text.

## Why

Two streams will change the same Booking tables in the next sessions: the CRM's Lane B (AA-972 M2M + B2B quote,
AA-973 departures and holds, AA-974 commercial rules, AA-975 event feed; planned keys bk-019…bk-022) and AA-682
(operations MVP: supplier bookings per itinerary item, trip-case checks, customer invoices with a payment schedule,
supplier bills). Without a shared plan they would collide on trip cases, versions, cancellation and invoicing. This
memo fixes the seams so both can proceed in any order.

## What exists today (bk-018)

- `trip_cases`: `customer_id` **NOT NULL**, `source_system ∈ {cis, tripplanner, manual}`, 13 statuses
  (`new_inquiry` … `completed`, `cancelled`) with a transitions table and trigger.
- `trip_case_versions` already carry `channel ∈ {b2c_tailor_made, fixed_departure, b2b}`, `valid_until`,
  `fx_rate_locked`, `fx_as_of`, approval and a lock trigger; items in `trip_case_version_itinerary`, net costs in
  `version_item_costs` (`conf:commercial`).
- `pricing_rules` has a `b2b` channel row type; `fx_rates` stores `rate_per_usd` per currency and date (USD is the
  base and cannot be a row; VND can already be a row).
- `supplier_contracts.cancellation_policy` is free text (supplier-side terms).
- No departures, capacity, holds, B2B partners, B2B quotes, cancellation-fee model, customer invoices or payments.

## Seams and the rule for each

| # | Seam | Rule |
|---|---|---|
| 1 | **Where a B2B sale lives** | A B2B **quote** and **hold** are Lane B objects of their own (`b2b_quote` + lines, `b2b_hold` + lines): they happen many times per proposal before any sale, and must not create trip cases or versions. Only `POST /holds/{id}/confirm` creates Booking's commercial record: a **B2B trip case** plus **one approved version** whose items are the confirmed quote lines and whose costs come from the cost sheet (`version_item_costs`, `supplier_rate_id`). From there AA-682's supplier bookings, trip-case checks and supplier bills hang off version items exactly as for B2C. |
| 2 | **Trip case without a customer** | AA-973 (bk-020) relaxes `trip_cases.customer_id` to NULL **only** for `channel = 'b2b'` (CHECK), adds `channel` (`b2c` default, `b2b`) and `party_tenant_id` (the agency, soft key), and adds `crm` to `source_system`. AA-682 must not add a NOT NULL dependency on `customer_id` (invoices to customers are B2C only, row 5). No traveller name ever enters Booking for B2B (ADR 0008a decision 3). |
| 3 | **Cancellation** | Two different policies, never merged: the **supplier-side** text stays in `supplier_contracts`; the **customer-side** fee schedule (days before departure → fee %, per product or contract, versioned) is a new Booking table set owned by AA-974 (bk-021), used by `POST /bookings/{id}/cancel` and its dry run. AA-682 reuses the same fee model for B2C cancellations later rather than adding its own. |
| 4 | **Status vocabularies** (X22) | The trip-case status machine stays the single case status for both channels (`confirmed`, `supplier_confirming`, … `cancelled`). Hold and line states (`active / confirmed / expired / released`; `available / on_request / confirmed / declined / cancelled`) live on the Lane B tables and are exposed only through `booking.b2b.v1` events. AA-682's supplier-booking status drives the line events (`line.confirmed`, `line.declined`), so the on-request desk and AA-682's supplier booking are one action, not two. |
| 5 | **Invoices and payments** | AA-682 invoices **customers** (B2C) with a deposit / balance schedule. B2B settlement with agencies is outside the CRM under the current B2B terms (ADR 0005a decision 1); a B2B invoice to an agency is a later Booking feature (design O-10). AA-682's invoice table should still name its bill-to party as a kind (`customer` now, `b2b_partner` later) so that feature is additive. The CRM's own client invoices live in `crm`, never in Booking. |
| 6 | **FX and VND** | One FX source: `fx_rates`. A B2B quote locks the rate the same way a version does (`fx_rate_locked`, `fx_as_of`); the confirmed B2B version copies the quote's lock, so no re-conversion happens at confirm. VND rounding (proposed: nearest 1,000 VND) is a pricing-engine rule in AA-974, shared with B2C when VND is enabled there. |
| 7 | **Pricing engine** | B2B prices come from the existing `app/pricing` engine with the `b2b` channel rule; Lane B adds no second engine. `b2b_price` is the engine's selling price for that channel; `supplier_net` never leaves Booking (CI-enforced in the contract). |
| 8 | **Events** | Lane B owns the `b2b_event` outbox and `GET /events` (AA-975). AA-682 writes no CRM-facing event; it changes supplier-booking state, and a trigger or service hook in Lane B turns that into `line.*` events. |
| 9 | **Migration keys** | Planned: bk-019 (AA-972), bk-020 (AA-973), bk-021 (AA-974), bk-022 (AA-975). AA-682 takes the next free key when it starts. Whoever starts a Booking migration first re-checks every branch and worktree for a taken number before creating the file (lessons log, AA-847 collision) and creates the Infra copy branch at once to hold the number. |
| 10 | **Staff UI** | The on-request desk (accept / decline within 1 business day, SLA badge) and "Flag incident on departure" live in the Booking staff admin (AA-975). AA-682's supplier-booking screen links to the same desk instead of duplicating it. |

## Order that avoids rework

1. AA-972 (bk-019): `b2b_partner`, `b2b_quote`; no change to trip cases.
2. AA-973 (bk-020): `departure`, `b2b_hold`, the trip-case changes of row 2, confirm → B2B trip case + approved
   version (row 1).
3. AA-974 (bk-021): VND, rounding, cancellation-fee model (row 3), `extend` once, re-hold limit.
4. AA-975 (bk-022): `b2b_event` outbox and feed.
5. AA-682 at any point after step 2, following rows 2, 4, 5 and 10; before step 2 only if it keeps `customer_id`
   optional-ready (no new NOT NULL FK paths through it).

## Open points (Booking lane decides, none blocks AA-928)

- Hold lengths (proposed: 48 h for seats, on-request until ops answer + 24 h, extension +72 h).
- VND rounding step and the VND rate source (AA-930).
- Whether the B2B confirmed version is visible in the existing staff "versions" list or only in a B2B tab.
