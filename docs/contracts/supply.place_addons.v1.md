# supply.place_addons.v1 — the optional activities of a place, per day (AA-Booking → TripPlanner)

AA-Booking owns what AA sells (root ADR 0004a decision 1): an **add-on offer** wraps one Booking service of an AA
supplier (an optional activity such as an evening food walk) with the CIS places it is sold at and its sale rules; a
second person publishes it (AA-1151, Booking `bk-068`). Booking publishes, per place and day, which add-ons can be
sold, so a reader can offer them on the matching day of a trip without computing anything. Readers never compute a
price: they quote the component through `booking.b2b.v1` (prices are fixed at quote time).

| | |
|---|---|
| View | `booking.v_place_addons` (Booking migration `bk-068`, AA-1151), owner `bk_owner`, security barrier |
| Readers | role `tripplanner` (the day cards of the trip planner, next slice): `SELECT` on the view + `USAGE` on schema `booking` (held since bk-039), nothing else of `booking` (Infra `db/owners.yaml` consumer grant, isolation probe cell `consumer.contract_grants.bk-068`); role `booking` itself (the staff preview `GET /booking/add-ons/place-days`) |
| Key | `(offer_id, destination_id, service_date)`; `component_id` = `sv:<service id>`, the id a B2B quote line takes |
| Rows | one per **published** offer, place and day from today (UTC) for `addon_days_ahead` days (Booking Pricing > Policy, seeded 365) on which the offer runs (its weekday) **and** an adult rate of the service is in force under a published contract of its supplier **and** no stop-sale is in effect; the service and the supplier are active. No row = not offered that day (B3) |

## Columns

| Column | Type | Meaning |
|---|---|---|
| `component_id` | text | `sv:<service id>`: quote it through `booking.b2b.v1` |
| `service_id` | uuid | the Booking service; also the `source_id` of its customer text in `catalog.v_supply_content` (CIS) |
| `offer_id` | uuid | the add-on offer |
| `destination_id` | uuid | a `catalog.v_destination` id |
| `place_role` | text | `operates` (the activity happens there) or `pickup` (travellers staying there are collected) |
| `service_date` | date | the day it can be sold |
| `service_type` | text | `activity`, `entrance`, `meal`, `guide` or `transfer` |
| `unit` | text | how it is priced: `person`, `group`, `vehicle` or `day` |
| `duration_minutes` | integer, null | how long it lasts |
| `max_group_size` | smallint, null | the most travellers in one group |
| `country_code` | text, null | ISO 3166-1 alpha-2 of the service |
| `min_pax` | smallint | it runs for this many travellers or more |
| `cutoff_hours` | smallint | book at least this many hours before the earliest start time (the day start when none) |
| `operating_weekdays` | smallint[] | ISO weekdays it runs (1 = Monday .. 7 = Sunday) |
| `start_times` | text[] | local start times `HH:MM`, sorted; empty = flexible |
| `sort_order`, `featured` | smallint, boolean | the order AA staff chose for display (featured first, then sort order) |
| `inventory_kind` | text | `free_sale` (AA confirms at once up to `free_sale_max_pax`), `allotment` (seats held for AA) or `on_request` (the supplier confirms) |
| `free_sale_max_pax` | smallint, null | `free_sale` only: the most travellers per booking AA confirms at once (null = no limit) |
| `supply_version` | bigint | the service's facts version (`supply.service.v1`) |
| `published_at` | timestamptz | when a second person published the offer |

## Rules

- **Never** a net, an agency price, a margin or a supplier identity; a price shown to a traveller comes from a quote.
- The cut-off is not applied in the view (the place's time zone is not in the catalog): a reader hides a day whose
  closing time has passed, and the B2B quote refuses it (422 `invalid`, "past_cutoff").
- Columns are **append-only**; a change of meaning is `supply.place_addons.v2` (a new view).
- A reader treats `UndefinedTable` / `InsufficientPrivilege` / no row as "no add-on" (fail soft), so it may ship
  before `bk-068` is applied.
- Agencies never write to the catalogue: the CRM reads add-ons through `booking.b2b.v1` (next slice), never this view
  (root ADR 0008a decision 1: no AA app role reads `crm`, and `crm_app` reads nothing outside `crm`).
