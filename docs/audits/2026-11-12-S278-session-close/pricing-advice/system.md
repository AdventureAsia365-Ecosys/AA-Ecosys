AA-Booking pricing today: current model, what already acts like versions, and the gaps (read-only; Booking HEAD 69c4ffb, bk-048)

Linear AA-1091 (In Progress, project "TripPlanner & AA-Booking"). The issue is a price setup workbench for the customer-service team: CIS itinerary → components, bulk Excel import with a DRY RUN, a provisional price taken from the CIS reference, and a structured CIS reference price. Readiness today: 2 of 892 plans priced, 890 `no_components`. A comment from the tech lead (S278, 12/11) adds **price versions** to the scope:
- Every rate, hand price, rule or provisional price the team enters or changes is a version, not an overwrite.
- Each version carries a validity window (travel dates vs booking dates), a season, maker and approver, a reason, and a diff to the version before.
- Quotes and tariffs pin a version, and a quoted or booked trip never re-prices.
- The workbench shows version history per tour.
- Export and import carry the version.
- An industry-practice review comes first.

## 1. Current model in plain English

The price chain is in `apps/AA-Booking/CONTEXT.md`, section "Tour price chain" (about l.777–818) and "Agency price tiers" (l.823–862). Design is in root `docs/adr/0005-pricing-and-supplier-rates.md` (d2: "New rates are new rows with new validity — never overwrite"), `0005a`, and `0019` b15.

1. **Supplier contract** (`backend/app/suppliers/service.py`, bk-008)
   - Fields: one supplier, `valid_from`/`valid_to` (NULL = open-ended), one currency, payment and cancellation terms.
   - Life: `draft` → `published` → `expired`. Expiry is a manual step.
   - The computed `phase` is draft / upcoming / in_force / ended / expired.
2. **Supplier rates** (`backend/app/supply/rates.py`, bk-010)
   - Rows under one contract: room type (`room_night`, meal plan) or service (its unit).
   - Each row has a free-text `season` label, its own `valid_from`/`valid_to` inside the contract's, an optional pax band, and a net amount.
   - Rates can be written only while the contract is a draft (trigger `supplier_rate_guard`).
   - "In force on day D" = contract published, and both validities cover D (`supply/records.py` `RATE_IN_FORCE_ON`). When several rates match: newest `valid_from`, then a rate with a pax band, then the lowest net.
   - Validity is judged on the **service day** only. There is no booking-date window.
3. **Rate-sheet import** (`backend/app/supply/rate_sheet.py`)
   - One AA template .xlsx becomes one **draft** contract with its rates, written through the same `create_contract`/`create_rate` code, so the same checks and audit apply.
   - `dry_run` reports errors by sheet, row and column, plus `impact` (which plans would move to priced).
   - Nothing is written while one error is left. A second person publishes.
   - It only prices hotels and services that already exist.
   - There is no export of current rates.
4. **Pricing rules and FX**
   - Files: `backend/app/pricing/engine.py`, `repository.py`, `policy.py`, `service.py`, `fx.py`; bk-004 and bk-007.
   - Rules are **global per channel** (b2b, fixed_departure; B2C retired): target and floor margin, peak uplift points, card fee, RRP markup (0.25), child %, infant flat fee, early-booking days and points.
   - FX rows: units per USD, buffer, `as_of`, `source`.
   - Both are append-only and count only once a second person approves them (`policy_approvals`).
   - In force = the newest approved row dated on or before the day. Status is pending / in_force / scheduled / superseded.
   - Rules have `valid_from` only, no end date and no per-tour or per-season scope. The `note` is optional.
   - A pending row cannot be edited, rejected or withdrawn (CONTEXT "Out of scope", l.1836).
   - Engine formula: `sell_usd = net_usd / (1 - margin - card_fee)`, then FX × (1 + buffer), then rounding.
5. **Price matrix per trip plan** (`backend/app/catalog/trip_plan_prices.py` bk-032; `cost_sheet.py` bk-039)
   - One row per channel × season label and validity window × pax band × currency, priced per person.
   - Computed rows: the job `bk_price_recompute` builds them from components × rates in force × rule. Windows are cut at rate validity edges, and `peak` is set when a rate's season label contains "peak". The job re-runs by itself whenever a rate, rule, FX row, component or the day changes.
   - Hand rows: entered by staff with `PUT …/prices`, which replaces the whole set. This needs `trip_plan.write` and **has no maker-checker**. A reason is required only when an override is below the floor.
   - Every b2b row also carries `rrp_amount`.
6. **Readiness** (`backend/app/catalog/price_readiness.py`)
   - One status per plan: priced / hand_priced / no_components / inactive_component / no_rule / missing_rates / missing_fx.
   - Offered as JSON or CSV.
7. **Agency tiers and rate cards** (`backend/app/b2b/agency_pricing.py`, bk-043)
   - Tier discounts (seeded 0 / 3 / 6 %) and per-partner rate cards (whole catalogue or one plan, `valid_from`..`valid_to`).
   - Both are append-only and maker-checker (`partner_price_approvals`). An "end card" (`discount_pct` NULL) ends a card.
   - Each row has a `note`; cards also have `contract_ref`.
8. **Departure price adjustments** (`backend/app/b2b/price_adjustments.py`, bk-048)
   - A % or an amount per traveller on one departure, with a required `reason` (max 300).
   - Life: pending → in force (second person) → `withdrawn`; a pending row can be `rejected`.
   - A change is a new row that names the row it `replaces_id`; approving the new row ends the old one.
   - Early-booking discount: the rule's `early_days`/`early_discount_pts`, judged on the quote day.
9. **B2B quote** (`backend/app/b2b/quotes.py`, `components.py`; contract root `docs/contracts/booking.b2b.v1.openapi.yaml` v1.8)
   - Priced **live from components × rates in force on each service day**, never from the matrix.
   - Inputs: the b2b rule, FX, the agency discount and the adjustment in force on the quote day. B2B quotes run with `peak = false`, so peak uplift reaches only the matrix and RRP.
   - Each line is rounded up to the cent, or up to 1,000 VND.
   - Stored append-only in `b2b_quotes` / `b2b_quote_lines`, with `valid_until` = 48 h.
10. **Agency tariff** (`backend/app/b2b/tariff.py`, `GET /booking/b2b/v1/tariff`)
    - Computed **live** with the quote engine and `priced_on` = today. It has no tariff id or version.
    - Plans that cannot be quoted are left out, and that includes **hand-priced plans with no components**.
11. **Price history** (`backend/app/catalog/price_history.py`, bk-039)
    - Every matrix change, by staff or by the cost sheet, closes the open rows (`effective_to`) and inserts the new set, with `change_source` (staff | cost_sheet) and `changed_by`.
    - `as_of(T)` gives the price list at a time.
    - The app may only insert rows and set `effective_to`.
    - The audit row `trip_plan.prices_replaced` also holds the rows before and after.
12. **CIS reference price**
    - CIS migration 365 (`apps/AA-CIS-App/api/migrations/365_tour_price_reference_view.sql`) adds `catalog.v_tour_price_reference_v1`: the raw `raw_tours.price_raw` of live tours, readable by `booking` only.
    - `backend/app/catalog/trip_plan_sync.py` keeps it on `trip_plans.reference_price_raw` and parses it into `reference_amount`/`reference_currency`. A changed text clears `reference_reviewed_by`/`_at`.
    - It is never a selling price and never reaches `v_from_prices`.
13. **Public "from" price**: `booking.v_from_prices` (contract `price.from.v1`) = the cheapest RRP for 2 travellers among the b2b rows still valid.

## 2. What already behaves like versions

- **Supplier contracts = versioned rate sets.**
  - "New terms are a new contract". Once published they are fixed by a DB trigger and expire only.
  - Maker-checker: the publisher must not be the last writer, and writing a rate makes you the maker.
  - Validity window: yes.
  - Missing: a link to the contract it supersedes, and a diff.
- **Rules, FX, tier discounts, rate cards.** Append-only, dated, maker-checker, `created_by` plus the approval row, and an optional `note`. Their status (pending / in_force / scheduled / superseded) is in effect a version timeline.
- **Departure price adjustments = the most complete model.** They have every piece:
  - a required reason;
  - a `replaces_id` chain;
  - maker-checker;
  - pending / in force / rejected / withdrawn.
- **Matrix history.** `trip_plan_price_history` (dated, immutable rows, `as_of`, source and who) plus before/after in the audit row. A diff can be derived from these, but no UI shows one.
- **Quote snapshot / pin.**
  - `b2b_quote_lines.supplier_rate_ids`, `net_cost_usd`, the agency discount and `rate_card_id`, `price_note` (adjustment or early discount, `below_floor`).
  - The quote stores the rule's `valid_from`, margin and card fee, the FX lock (rate, buffer, date, source), the rounding rule and the tier.
  - `price_hash` is SHA-256 of all of it.
  - A hold needs the same hash and an unexpired quote, else 409 `price_changed`: no re-pricing within the 48 h validity.
- **Confirm freezes.**
  - Confirm writes one **approved, locked** trip case version, with the cost rows taken from the quote (bk-005/006 lock triggers on sent and approved versions).
  - The cancellation policy in force is locked on the hold.
  - FX snapshots are taken on supplier bookings at confirm and on bills at approval (`pricing/fx.py`, bk-045).
- **CRM side** (`apps/AA-Partner/api/app/proposals/builder.py`, `holds.py`; Partner CONTEXT "Proposal", "Money of AA lines").
  - A sent proposal version fixes its own `price_hash` and supersedes the earlier sent version. The client accepts on the same hash.
  - The AA line's cost is frozen at the quote's `b2b_price` (`aa_quote_lock`). A hold answered `price_changed` is re-quoted once.
  - Agreements (terms) are versioned: a published version never changes and carries a SHA-256.
  - Booking partner-terms clauses carry `version` and `approved_at`, and include a `price_error` clause with a free-cancel window.

## 3. Gaps against the target ("every price change is a version with validity, season, author, approver, reason, diff; quotes pin a version")

1. **No first-class "price version" entity.**
   - Versioning is spread over different shapes: contract, rule row, FX row, tier row, card row, adjustment row, matrix history.
   - None has a version number or label.
   - There is no single "price list version of tour X" that a quote, tariff or export can name.
2. **Hand prices (the matrix PUT) have no maker-checker and no required reason** (only below-floor overrides need one). The customer-service team would enter these.
   - History has who, but no approver and no reason.
   - A change is live at once: no draft or pending stage.
3. **Season is a free-text label** on each rate and matrix row.
   - There is no season calendar (high/low/peak date ranges per destination, blackout dates).
   - "Peak" is detected by the substring "peak".
   - Peak uplift is ignored by B2B quotes (`peak = false`), so the RRP and the agency price can follow different season logic.
4. **Validity is service-date only.**
   - Supplier rates have no booking-date (sale) window and no stop-sale.
   - There is no release period on hotel rates. Release exists only for agency allotments on departures (`b2b/allotments.py`).
   - Pricing rules have no `valid_to` and no per-tour or per-season scope.
   - The only booking-date rule is early-booking.
5. **No diff or supersede link between contracts.** A new contract for the same supplier does not record which contract it replaces. Overlaps resolve silently by newest `valid_from`. Nothing shows "rate X: 85 → 92 USD from 01/04".
6. **Pending rules and FX rows cannot be rejected or withdrawn**, only overtaken by a newer row. A draft contract has no reject state either.
7. **The tariff is not pinned.**
   - The agency tariff is computed live with `priced_on` = today and has no version id or ETag.
   - The CRM cannot tell that a tariff changed, and a tariff row is not a promise (only a quote is, for 48 h).
   - `GET /price-parity` and the from price are also live.
8. **Quotes pin inputs, not a named version.**
   - `supplier_rate_ids` and the rule and FX values are stored, but there is no `price_version_id` / matrix history id. The rule is stored by value, not by id.
   - Quote validity is 48 h, where the industry norm is longer (14 days was the old B2C `quote_validity_days`).
   - After 48 h a re-quote re-prices on current data, with no "honour the old price" path except a staff adjustment.
9. **Automatic re-pricing has no second check.**
   - Publishing a contract or approving a rule or FX row re-computes every affected matrix and RRP via `bk_price_recompute`.
   - Nobody sees an impact or diff before the new sell prices go live. The rate-sheet dry-run `impact` lists plans that move to priced, but not price deltas.
10. **Hand-priced plans cannot be sold to agencies.** Quotes and the tariff price only components, so a `hand_priced` plan with no components is left out. This matters for the AA-1091 provisional-price item, which needs a defined meaning.
11. **Import and export**
    - The rate sheet imports one contract at a time.
    - There is no export of current rates or of the matrix with version ids (readiness CSV and tariff CSV only).
    - There is no bulk matrix or season import.
12. **Not modelled**
    - net vs commissionable rates (no commission anywhere in `app/`);
    - supplier rate types beyond net (rack, promo, free-night offers);
    - per-market or per-currency contracting.
    - The selling currency is USD (b16), plus VND for B2B quotes.
13. **CIS reference price** is parse-once text with a review flag on the Booking side. In CIS there is no structured amount, currency or basis, and no history (that is AA-1091 item 5).

Main files:
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Booking/CONTEXT.md`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Booking/backend/app/pricing/{engine,repository,policy,service,fx}.py`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Booking/backend/app/catalog/{cost_sheet,price_history,price_readiness,trip_plan_prices,trip_plan_sync}.py`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Booking/backend/app/suppliers/service.py`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Booking/backend/app/supply/{rates,rate_sheet,records}.py`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Booking/backend/app/b2b/{quotes,components,tariff,agency_pricing,price_adjustments,allotments}.py`
- `/home/nghiep/projects/AA-Ecosys/docs/contracts/booking.b2b.v1.openapi.yaml`
- `/home/nghiep/projects/AA-Ecosys/docs/adr/0005-pricing-and-supplier-rates.md`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/api/migrations/365_tour_price_reference_view.sql`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Partner/api/app/proposals/builder.py`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Partner/api/app/proposals/holds.py`