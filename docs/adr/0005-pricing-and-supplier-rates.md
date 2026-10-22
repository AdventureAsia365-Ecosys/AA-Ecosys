# ADR 0005 — Pricing and supplier rates

- **Status:** Accepted (14/10/2026, Nghiệp, S235), including the former open recommendations (decisions 8–10).
  Tax rates are still to be confirmed by the AA accountant; margin numbers are policy data and are checked with
  Ms. Thư before the first price load.
- **Amendment proposed:** [ADR 0005a](0005a-b2b-resale-warn-and-vnd.md) (Proposed 22/10/2026, S247): decision 9
  (warn, not block, below the "from" price; no subscription line), VND quotes, `b2b_price` naming.
- **Scope:** AA-Booking (owner), CIS and TripPlanner (readers). Answers AA-709.
- **Related:** ADR 0001 (Booking owns commercial data), ADR 0002 (only CIS writes content), ADR 0004 (Booking
  bootstrap, O7: all customer-facing content in CIS), ERD v2 `docs/AAA/erd-v2/booking.dbml`
  (`suppliers`, `hotels`, `trip_plan_prices`, `supplier_bookings`).

## Context

Raw tours carry at most one free-text `silver_aa_internal.raw_tours.price_raw` ("$1,722/person", "from USD 495").
Most have none. There is no supplier, net cost, currency, unit, season, pax tier or validity. Quotes, invoices,
supplier bookings and payments (AA-681/682) all need prices with transactional integrity: once a customer approves
version V3, the V3 price cannot change.

## Decision

1. **Ownership.** All price and supplier data lives in schema `booking`: suppliers, contracts, net rates, FX rates,
   pricing rules, cost sheets, selling prices, quotes. CIS keeps tour **content** and the tour's day/service
   structure; Booking references CIS ids (`source_system='cis'`, `source_id`). The price **entry UI** lives in the
   shared staff admin (one staff login, ADR 0004 O1) and calls the Booking API — staff do not need to know which
   schema stores it.
2. **Supplier contracts and net rates.** A contract has a supplier, validity (`valid_from`/`valid_to`), currency,
   payment terms and cancellation policy. Net rates per service type:
   hotel (room type, season, meal plan, single supplement, extra bed), transport (vehicle type, per day/transfer,
   capacity), guide (language, per day), entrance fee (adult/child, per pax), activity (per pax or per group), meal.
   New rates are new rows with new validity — never overwrite.
3. **Cost sheet.** Each priced tour (Booking `trip_plans`, synced from a CIS published tour) maps its days to
   services. Net cost per person is computed per **pax band** (1, 2, 3–4, 5–6, 7–10, 11+) and **season**, because
   fixed costs (vehicle, guide) are shared by the group.
4. **Selling price = net cost ÷ (1 − margin)**, margin = gross margin on the selling price (not markup).

   | Channel | Target margin | Floor |
   |---|---|---|
   | B2C direct, tailor-made (TripPlanner, AA web) | 30% (25–35%; private 2 pax up to 35%, groups ≥ 8 about 25%) | 20% |
   | B2C fixed departure / seat-in-coach | 25% | 18% |
   | B2B reseller (travel agent, CIS tenant reselling AA tours) | 15% on the net price given to them (12–18%) | 10% |
   | Peak season (Tết, festivals, high months) | +3 to +5 points | — |

   Sales may override a quote price; below the floor the override needs a reason and is audited. Card/payment
   fees (~3%) are built into the price, not added as a surcharge. Prices are rounded (USD to $5).
5. **Currencies.** Base currency **USD**. Selling currencies also EUR, GBP, AUD, SGD (more per tenant market).
   Supplier costs are entered in the supplier's currency (VND, THB, BTN, …) and converted with dated FX rates.
   Non-USD selling prices = USD price × FX × (1 + 2–3% buffer), rounded. The FX rate is **locked when a quote is
   sent**; quotes are valid 7–14 days; invoices and payments use the quote's currency.
6. **Outputs.** `booking.trip_plan_prices` (season × pax band × currency × validity) is the published price list.
   The **"from" price** = lowest per-person B2C price for 2 pax in low season, exposed as a read view
   (`booking.v_from_prices`) for TripPlanner and CIS tour pages (contract `price.from.v1`, `docs/contracts`).
   B2B net price lists are exposed only to authorised B2B channels.
7. **Loading.** Phase 1: supplier rate sheets uploaded as an Excel template → validation → staff review → publish
   (versioned). Phase 2: edit in the admin UI. Later: supplier extranet/API. Existing `price_raw` strings may be
   parsed once into a **reference price** with a review flag, used as the "from" price only until a cost sheet
   exists. Price entry is owned by the `contracting` role (decision 8).

## Consequences

- Booking needs bk-00x migrations for contracts, rates, FX, pricing rules and cost sheets before AA-681 quotes.
- CIS stops treating `price_raw` as a price; it stays raw source data.
- TripPlanner shows "from" prices only via the Booking view; it never computes prices.
- Margin numbers are policy and editable (pricing rules table), not code constants.

## Decisions on the former open items (approved by Nghiệp, 14/10/2026)

<!-- markdownlint-disable MD029 -- numbering continues decisions 1-7 above, which other text cites (decision 8) -->
8. **Who enters prices.** A new staff role `contracting` (next to admin / sales / content_creator) owns supplier
   contracts and net rates; Ms. Thư or a named ops/product person holds it at first. **Maker-checker:** one person
   uploads or edits, another publishes; every change is audited. Sales never edit net rates — they quote and may
   override the selling price within the floor. Ops checks availability and books suppliers.
   **Format:** one AA Excel template, one sheet per service type (hotel, transport, guide, entrance, activity,
   meal); each row = supplier, service, variant (room type / vehicle / language), season or date range, unit
   (per pax / room-night / vehicle-day / group), net price, currency, supplements, child policy. Upload validates
   and reports errors per row. Later: a supplier extranet, still behind the publish step.
9. **Tenant resale.** Yes, after AA-Booking can quote (AA-681): tenants see a B2B net price list (15% margin) per
   tour in their portal and set their own retail price; bookings arrive through a B2B channel carrying
   `tenant_id`; AA invoices the tenant, not the end customer. **Rate parity:** a tenant may not advertise below
   AA's public B2C "from" price. A second revenue line next to the subscription.
10. **Tax / VAT.** Rates depend on the selling entity and the service, so the accountant confirms them
    (still open). The system never hard-codes tax: a `tax_rules` table keyed by selling entity × country of
    consumption × service type × validity. B2C prices are shown tax-inclusive (all-in) and invoices itemise tax;
    B2B net prices state whether tax is included, per the agent contract. If an EU entity or EU sales appear
    later, check the EU tour-operator margin scheme (TOMS) with the accountant.
<!-- markdownlint-enable MD029 -->
