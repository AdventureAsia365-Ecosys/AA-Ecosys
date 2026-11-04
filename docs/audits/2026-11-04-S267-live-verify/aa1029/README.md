# AA-1029 R4 tour price chain, live on Dev (S267, 04/11/2026)

Shipped: root #521 (price.from.v1 contract, DM-7.1 row), CIS #1291 (365 `catalog.v_tour_price_reference_v1`),
Booking #179 (bk-039) + #180 `3ef1434b` (catalog bridge, cost sheet, RRP, rate-sheet import, price history), Infra #660
(TripPlanner grant, seed run-script) + #661 (seed apply), TripPlanner #224 `cf6faf9a` (tour page reads price.from.v1).
Applied: DB Migrate 365 (41797085229), bk-039 (41797598359); seed run-script 41801245083 (DRY RUN 41800519848 first).
Two review rounds (lane: 2 majors fixed, 1 rejected with evidence — `fixed_departure` stays priced per the S265
re-scope; adversarial re-review: 2/2 approve, 0 findings). Cost: 0 USD.

| Step | Result |
|---|---|
| Seed (invented supplier, hotel, guide, transfer, 6 rates, b2b rule with RRP 25 %; all `SYNTHETIC S267`) | applied, 22 steps, E2E tour `0079d599…` (Okinawa from Naha, 5 days) |
| Booking worker `bk_price_recompute` (no hand step) | succeeded 08:41Z |
| `booking.v_from_prices` for the tour | **235.00 USD** per person, 2 travellers, season Low, `price_kind` rrp, valid 2026-11-04 .. 2027-02-01 |
| TripPlanner tour page | "From **$235** per person — Suggested price for 2 travellers"; schema.org Offer price 235.00 USD, priceValidUntil 2027-02-01 |

Expected by the seed: net 150 per person → b2b 185 → RRP 235 (b2b x 1.25, ADR 0019 b15). Matches.

Screenshots: `tp-tour-from-price-{1440,390}-{light,dark}.png`.

Not done here: the portal marketplace read of price.from.v1 (the studio moved into the agency web this session;
follow-up) and a Booking admin screenshot (the agent's staff session on Booking admin is read-only / refused; the
Booking side is evidenced by the view row above).
