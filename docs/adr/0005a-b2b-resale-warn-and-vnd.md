# ADR 0005 — Amendment: B2B resale by partner agencies (warn below the "from" price, no subscription line, VND quotes)

- **Status:** Accepted (22/10/2026, S247, Nghiệp). Proposed the same day.
- **Scope:** AA-Booking (owner of prices and the B2B API), AA-Partner (consumer, [ADR 0010](0010-aa-partner-app.md)),
  CIS and TripPlanner (readers of `price.from.v1`, unchanged).
- **Amends:** [ADR 0005](0005-pricing-and-supplier-rates.md) decision 9 (tenant resale), decision 5 (currencies) and
  the last sentence of decision 6 (how B2B price lists are exposed).
- **Implements:** the owner's questionnaire answers Q1 1.1 (free for agencies now), Q2 1.1 (B2B price at the existing
  15 % margin, the agency sets its sell price), Q2 1.2 (AA bills the agency under the current B2B terms, outside the
  CRM), Q2 1.3 (below the public price: contract clause only); contradictions X10 and X11 of the CRM design.
- **Design and evidence:**
  [`final/crm-design-final.md`](../audits/2026-10-21-S246-crm-design-v3/final/crm-design-final.md) §1.2, §5.3, §6;
  design v3 §3.4, §5.2; [`lanes/data-privacy-integrations.md`](../audits/2026-10-21-S246-crm-design-v3/lanes/data-privacy-integrations.md)
  §6.2; the Booking commercial-core memo
  [`docs/audits/2026-10-22-S247-crm-w0/booking-commercial-core-memo.md`](../audits/2026-10-22-S247-crm-w0/booking-commercial-core-memo.md).
- **Related Linear:** AA-972 (M2M + B2B quote), AA-973 (departures, holds), AA-974 (commercial rules: VND,
  cancellation fees, extend, re-hold limit), AA-975 (event feed), AA-682 (Booking operations, invoices).

## Context

ADR 0005 decision 9 says: "a tenant **may not** advertise below AA's public B2C 'from' price. A second revenue line
next to the subscription." The CRM design and the owner's answers say the opposite on both points: the system only
**warns** below the public price (the rule lives in the partner contract), and agencies pay nothing for the CRM
now, so there is no subscription for a B2B line to sit next to (X11). Decision 5 lists USD, EUR, GBP, AUD and SGD as
selling currencies; Vietnamese agencies need **VND** quotes (X10). Decision 6 says B2B net price lists are exposed
"only to authorised B2B channels" without naming the channel.

## Decisions

### 1. Decision 9 replaced: B2B resale through `booking.b2b.v1`

- Partner agencies resell AA products through the Booking B2B API, contract
  [`booking.b2b.v1`](../contracts/booking.b2b.v1.openapi.yaml), called by AA-Partner with an M2M token and the
  agency's `tenant_id` in `X-AA-Tenant-Id`. Booking checks the agency in its own `b2b_partner` table.
- The price Booking returns per line is the **B2B price**: net cost ÷ (1 − margin) with the `b2b` channel rule of
  decision 4 (15 % target, 10 % floor, policy data in `booking.pricing_rules`). The agency sets its own sell price in
  the CRM.
- **Rate parity: warn, never block.** When the agency's sell price per person is below AA's public B2C "from" price
  (`price.from.v1` basis, served to the CRM as `GET /price-parity`), the CRM shows a warning on the line. Nothing is
  refused. The obligation is a clause in the partner contract (Q2 1.3).
- **No subscription line.** The CRM is free for partner agencies at launch (Q1 1.1). AA's revenue from the channel is
  the B2B margin. Paid tiers are a later decision with their own triggers (final design §1.2); the entitlement fields
  exist from AA-939 but carry no price.
- **Settlement** between AA and the agency stays outside the CRM, under AA's current B2B terms (Q2 1.2). Invoicing an
  agency from Booking is part of the Booking operations work (AA-682 area), not of the CRM.

### 2. Naming: `b2b_price` leaves Booking, `supplier_net` never does

- In every contract the agency-facing price is called **`b2b_price`** (what agencies call "net"). The supplier net
  cost (`booking.supplier_rates`, decision 2) and anything derived only from it never leave Booking; no contract
  field is named `supplier_net` (Fix B19).
- Enforced in CI: the root `contracts.yml` check rejects any `booking.b2b.v1` schema or sample with a
  `supplier_net` key.
- Decision 6's last sentence becomes: "B2B price lists are exposed only through `booking.b2b.v1` to authorised M2M
  clients, per agency."

### 3. Decision 5 amended: VND is a quote and selling currency

- **VND** is added as a quote / selling currency, first for B2B quotes (AA-974); B2C may enable it later as policy
  data. The base currency stays **USD**.
- The conversion uses the `booking.fx_rates` row in force on the pricing day (`rate_per_usd`, `buffer_pct`), and the
  quote **locks** it: the quote carries the rate, its date and a `price_hash`; a confirmed line never re-converts.
- VND has no minor unit (ISO 4217 exponent 0). Rounding of VND sell and B2B amounts is set by the Booking lane in
  AA-974 *(proposed: to the nearest 1,000 VND)*; the rounding rule is part of the quote, so the `price_hash` covers
  it.
- The VND rate source is chosen in AA-930 (the State Bank of Vietnam terms of use are unverified). Dev uses synthetic
  rates only.

### 4. Cancellation fees for B2B bookings

- The **customer-side** cancellation policy (what AA charges the agency when a confirmed booking is cancelled) is a
  Booking policy per product or contract: a fee schedule by days before departure, returned by
  `POST /bookings/{id}/cancel` and by its dry run (`?dry_run=true`) so the CRM can preview a cancellation (C12).
- The existing free-text `booking.supplier_contracts.cancellation_policy` stays what it is: the **supplier-side**
  terms AA has with its supplier. The two are not merged (memo §3).

## Consequences

- **Positive:**
  - the rule matches what agencies were promised (warn, free CRM) and is enforced in one place (the CRM line UI);
  - the `b2b_price` / `supplier_net` split is checked by CI, not only by review;
  - VND quotes become possible without changing the base currency or the FX table shape.
- **Negative / cost:**
  - a below-parity sale is possible and is policed by contract and reporting, not by the system;
  - VND rounding and a VND rate source are new policy items to maintain.

## Alternatives considered

- **Keep the block below the "from" price.** Rejected: the owner answered "contract clause only" (Q2 1.3), and a hard
  block cannot see legitimate cases (an agency absorbing its own margin).
- **Charge a subscription and keep the B2B margin as a second line.** Rejected for now: the CRM is free (Q1 1.1);
  tiers come only at measured triggers.
- **Quote VND by converting USD in the CRM.** Rejected: prices and FX belong to Booking (decision 1); a CRM-side
  conversion would make the price hash meaningless.

## Follow-ups

- AA-972: `b2b_partner`, quotes with `b2b_price`, `GET /price-parity`.
- AA-974: VND, rounding, cancellation-fee policy with dry run, `extend` once per hold, re-hold limit.
- AA-930: VND rate source.
- On acceptance: status line here and in the index.
