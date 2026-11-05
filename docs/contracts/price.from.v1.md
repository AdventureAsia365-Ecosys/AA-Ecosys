# price.from.v1 — the public "from" price of a catalog tour (AA-Booking → TripPlanner, AA-CIS-App)

AA-Booking owns every price (root ADR 0005 decision 1). The public **"from" price** of a tour (ADR 0005 decision 6, as
amended by root ADR 0019 b15) is the **suggested retail price (RRP)** per person for 2 travellers: the agency price of
the tour (the `b2b` row of Booking's price matrix) plus the RRP markup of the `b2b` pricing rule in force (policy
data, 25 % to start), rounded up like every selling price. Booking publishes it as a view in its own schema; readers
never compute a price.

| | |
|---|---|
| View | `booking.v_from_prices` (Booking migration `bk-039`, AA-1029), owner `bk_owner` |
| Readers | role `tripplanner` (the browse Lambda's tour detail): `SELECT` on the view + `USAGE` on schema `booking`, nothing else of `booking` (Infra `db/owners.yaml` consumer grant, isolation probe cell `consumer.contract_grants.bk-039`); role `cis_app` (Booking `bk-040`: CIS `GET /v1/tours/pool`, read on its main pool after the tenant block, returned as `from_price` to the agency Content studio Marketplace; probe cell `consumer.contract_grants.bk-040`); role `booking` itself (staff pages, B2B price parity) |
| Key | `(source_system, source_id)` = the catalog tour key of `catalog.tour.v1` (never the CIS `tour_id`) |
| Rows | one per key that has a `b2b` price row with an RRP covering 2 travellers and still valid today (UTC); no row = no price shown |

## Columns

| Column | Type | Meaning |
|---|---|---|
| `source_system` | text | `cis` |
| `source_id` | text | catalog key |
| `amount` | numeric(12,2) | the RRP per person (the cheapest among the qualifying rows, USD first) |
| `currency` | text | ISO 4217 (USD today, b16) |
| `basis` | text | `per_person` |
| `pax` | integer | `2` (the party the price is for) |
| `season` | text, null | the season label of the row (`Low`, `High / Peak`, …) |
| `valid_from` | date | first day of the row's validity (may be before today: a cost sheet row starts where its supplier rates start) |
| `valid_to` | date | last day of the row's validity (a reader may show "valid until"); `9999-12-31` = open-ended, no end date to show |
| `price_kind` | text | `rrp` (a later kind is a new value, never a new meaning of `rrp`) |
| `priced_at` | timestamptz | when the row was written (by staff or the cost sheet) |

## Rules

- **Never** a supplier net, an agency (`b2b`) price, a margin or a rule value: only the public suggested price.
- Columns are **append-only**; a change of meaning is `price.from.v2` (a new view).
- A reader treats `UndefinedTable` / `InsufficientPrivilege` / no row as "no price" and shows none (fail soft); the
  reader may ship before `bk-039` is applied.
- Agency tiers and contract rate cards (ADR 0019 b15, AA-1030, Booking bk-043) change only the agency (`b2b`) price a
  partner is quoted through `booking.b2b.v1`; the RRP served here is the same for every agency. The per-tenant tour
  read (`catalog.v_tenant_tour_v1`, ADR 0019 d10) is a later view; this one is the AA catalogue price.
- How the row is produced (Booking `CONTEXT.md`, "Tour price chain"): the cost sheet job computes the net per pax band
  and season from the plan's components and the supplier rates in force, the engine prices it with the `b2b` rule, the
  RRP is stored on the row; hand rows and staff overrides are kept; every change is kept in
  `booking.trip_plan_price_history`.
