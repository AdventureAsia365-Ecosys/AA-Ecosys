# ADR 0005 — Amendment: price versions (no overwrite, a second person publishes, quotes and agency tariffs pin a version, seasons from calendars)

- **Status:** Proposed (2026-11-12, S278). The technical decisions (d1–d14) wait for the tech lead. The policy
  parameters of decision 15 are business choices: the system ships with the proposed defaults and the business owner
  may change any of them later as policy data, without a code change or a new ADR.
- **Amends:** [ADR 0005](0005-pricing-and-supplier-rates.md) decision 2 ("new rates are new rows, never overwrite",
  extended to every price), decision 3 (season from a calendar, not a label), decision 5 (quote validity becomes a
  policy parameter), decision 6 (the published price list is a versioned entity) and decision 7 (loading: versioned
  Excel import and export); [ADR 0005a](0005a-b2b-resale-warn-and-vnd.md) decision 1 (the agency tariff gains a
  version and an ETag). ADR 0005a decision 3 (the quote locks the FX rate) is unchanged.
- **Cites:** [ADR 0019](0019-b2b-only-ecosystem-model.md) b15 (one net price per tour per season, three agency tiers
  0 / 3 / 6 %, RRP = net + 25 %), b16 (deposit and balance, USD), d3 (the Booking `finance` role); ADR 0003a (the
  Booking job table `booking.job`); ADR 0017 / 0017a (migration classes).
- **Scope:** AA-Booking (owner of every price, version, season calendar and policy parameter), AA-Partner (consumer of
  the versioned tariff and the pinned quote through [`booking.b2b.v1`](../contracts/booking.b2b.v1.openapi.yaml)
  1.9), AA-CIS-App (source of the structured reference price used for provisional prices, AA-1091 item 5).
  TripPlanner is unchanged: it reads `price.from.v1`.
- **Design and evidence:** the S278 pricing advisory
  [`docs/audits/2026-11-12-S278-pricing-advice/`](../audits/2026-11-12-S278-pricing-advice/README.md): industry
  practice (sections 2–4), today's system against it (section 5), the proposed design (section 6), the policy
  questions (section 7) and the delivery order (section 8); the code reading of Booking at bk-048 in
  [`system.md`](../audits/2026-11-12-S278-pricing-advice/system.md).
- **Related Linear:** AA-1091 (price setup workbench; this ADR is its design part).

## Context

The customer-service team will enter prices for 890 trip plans that have none today (`GET
/booking/catalog/price-readiness`: 2 of 892 priced). The tech lead asked that every price the team enters or changes
is a version, not an overwrite, and that quotes and agency tariffs pin the version they were priced on.

Booking already has many of the right pieces (advisory section 5, system.md section 2):

- supplier contracts are fixed by a DB trigger once published, and the publisher must not be the last writer;
- pricing rules, FX rows, tier discounts and rate cards are append-only and count only after a second person
  approves them;
- departure price adjustments (bk-048) have the full model: a required reason, a `replaces_id` chain, maker-checker,
  and the states pending, in force, rejected and withdrawn;
- the price matrix keeps a dated, insert-only history (`booking.trip_plan_price_history`);
- a quote stores its inputs and a `price_hash`, and a hold of a changed quote answers 409 `price_changed`;
- confirm writes a locked trip case version and locks the cancellation policy and the FX rate.

The gaps are:

1. **Hand prices** (`PUT …/prices`, the screen the customer-service team will use) need no approval and no reason
   (except below the floor), replace the whole set and are live at once.
2. **Season** is a free-text label on each rate and matrix row. "Peak" is detected by the substring `peak`, and B2B
   quotes run with `peak = false`, so the agency price and the RRP follow two season logics.
3. **No named version.** Quotes pin inputs by value. The agency tariff is computed live (`priced_on` = today) and
   has no id, no ETag and no next-year edition, so the CRM cannot tell that it changed.
4. **No diff or impact before approval.** Publishing a contract or approving a rule or FX row re-computes every
   affected matrix at once (`bk_price_recompute`). Contracts do not say which contract they replace.
5. **Pending rules and FX rows** cannot be rejected or withdrawn. Rules have no end date.
6. **No export** of current prices, and the import carries no version.
7. **Hand-priced plans with no components** cannot be quoted to agencies, and "provisional price" has no defined
   meaning.

Industry practice (advisory sections 2–4): no tour-operator system overwrites a price; every change is a new dated
record with its author. Quotes and bookings keep the price of the moment they were made. Seasons are date ranges
inside each supplier contract and are matched on the travel date. Mid-year price changes apply to new quotes and
bookings only.

## Decision

### Principles

1. **No overwrite.** Every price change is a new version. A published version is never edited.
2. **A version takes effect only after a second person approves it.** The maker can never approve their own version
   (the self-approval block Booking already has stays). Decision 8 names the only automatic publish.
3. **Quotes and agency tariffs pin a version id.** A quote line names the price list version it was priced from. A
   tariff answer names its tariff version.
4. **A confirmed booking is never repriced.** The one exception is a separate contract surcharge line under the
   conditions of decision 11.
5. **The travel date decides the season and the version.** The booking (quote) date decides only offers: the
   early-booking discount and a version's optional sale window.

### d1 The price list version

A **price list version** is one approved, immutable set of selling prices of one trip plan for one travel window.

| Field | Meaning |
|---|---|
| scope | `trip_plan_id` (the selling price matrix of one plan) |
| identity | `version_no` (1, 2, 3 … per plan), `label` (for example "2027 v3"), `tariff_year` |
| travel window | `travel_from` / `travel_to`: the departure dates the version prices (half-open inside, d10) |
| sale window | `sale_from` / `sale_to`, optional: the quote dates the version may be used on (an offer) |
| people | `created_by` (maker), `approved_by` / `approved_at` (checker), `rejected_by` / `withdrawn_by` with times |
| reason | required, at most 300 characters, written by the maker; a reject or withdraw also needs one |
| chain | `replaces_id`: the version this one replaces (null for the first one) |
| source | `staff` (hand entry), `import` (Excel, with the file's SHA-256), `cost_sheet` (computed by `bk_price_recompute`), `provisional` (d12) |
| review data | `diff` and `impact` (JSON), computed when the version is submitted (d9) |
| rows | today's `booking.trip_plan_prices` row shape (channel × season × pax band × currency, with RRP, child, infant and single supplement), plus `version_id` and `season_id` in place of the free-text label |

The history table `booking.trip_plan_price_history` becomes the rows of past versions: the existing history is
migrated into versions with `source` taken from its `change_source`, so nothing is lost. The rows in force today in
`booking.trip_plan_prices` become each priced plan's latest version, `published`, and the migration publishes tariff
version 1 of the tariff year covering today from them (d7), so the tariff and the quotes of today's priced plans keep
their prices.

Pricing rules, FX rows, tier discounts and partner rate cards keep their own append-only tables and their approval
tables (`booking.policy_approvals`, `booking.partner_price_approvals`). They gain three things, following the bk-048
model: a pending row can be **rejected** or **withdrawn**, a reason is **required** on every new row, and pricing rules
gain `valid_to`.

### d2 States

`draft` → `pending` → `published` → `superseded`, plus `rejected` and `withdrawn`, the same model as the departure
price adjustments of bk-048.

| State | Who moves it there | Effect |
|---|---|---|
| `draft` | the maker creates it (form, Excel import, copy to next year) | editable by its maker; prices nothing |
| `pending` | the maker submits it; the diff and impact are computed and frozen | read-only; prices nothing |
| `published` | the checker approves it, or the auto-publish rule of d8 | prices quotes, the tariff and the RRP from that moment |
| `superseded` | newer published versions of the same plan together cover **every** date of its travel window | prices nothing new; pinned quotes keep it |
| `rejected` | the checker refuses a pending version, with a reason | final |
| `withdrawn` | the maker withdraws a draft or pending version, or the checker withdraws a published one with a reason | final; a withdrawn published version prices nothing new, pinned quotes keep it |

At most one pending version per plan and overlapping travel window at a time (a second submit is refused until the
first is decided). A version is never deleted.

**Overlap rule (which published version prices a date).** Among the published versions of a plan whose travel window
covers the service date (and whose sale window, when set, covers the quote day), a non-provisional version wins over a
provisional one (d12); among the rest, the one with the latest `approved_at` wins, then the highest `version_no`. A
partially overlapped version stays `published` and keeps pricing the dates no newer version covers (for example v2
covers November to October and v3 changes prices from 2027-04-01: v2 prices November to March, v3 from April). It
becomes `superseded` only when newer published versions cover all of its window. `superseded` is derived from the
published set, so Booking recomputes it on every publish and withdrawal.

**Withdrawal of a published version.** The withdrawn version leaves the published set and the overlap rule is applied
again to the versions that remain: a version it had superseded returns to `published` for the dates no remaining newer
version covers, because that price was approved by a checker for those dates and was never edited. Dates no remaining
version covers become unquotable (d5). The withdraw dialog shows this outcome (which version prices each date again,
which dates become unquotable) as its diff and impact (d9) before the checker confirms. A withdrawal publishes the next
tariff version of each tariff year it touches (d7), like a publish.

### d3 Supplier contracts are versions

A supplier contract already is the version of its supplier's rates (published = fixed by trigger, maker-checker on
publish). It gains:

- `supersedes_id`: the contract it replaces for the same supplier. Overlapping published contracts of one supplier
  without that link are refused at publish, instead of resolving silently by the newest `valid_from`;
- a **diff per rate row** shown before publish (for example "Deluxe twin, High: 85 → 92 USD from 2027-04-01");
- a `rejected` state for a submitted draft, with a reason;
- the **stay pricing flag** `per_night` (default: each night priced by its own season) or `arrival_season` (the whole
  stay priced by the season of the arrival night), because hotels differ.

Supplier contracts keep their own season labels inside the contract calendar of d4.

### d4 Season calendars and holiday events

Seasons become data, never a substring or a hard-coded date:

- a **season calendar** belongs either to one supplier contract (the supplier's seasons) or to one destination (the
  seasons of AA's sell-side price list);
- a calendar holds date ranges, each with a season code `low`, `high`, `peak` or `festive`; one season may have
  several ranges in a year (high season twice). The season ranges of one calendar never overlap (a save that makes
  two ranges cover one date is refused), and a date no range covers takes the calendar's `default_season` (`low`
  unless set), so every date has exactly one season;
- a calendar also holds **stop-sale ranges** (no sale from an allotment; every request goes on request). Stop-sale is
  an overlay, independent of the season: it changes availability, never the season or the price, and compulsory
  surcharges still apply on a stop-sale date;
- **holiday events** (Tet, Songkran, Lebaran, Chinese New Year, Christmas, New Year and others) are rows per country
  and **per year**, entered as data each year. No Tet or Lebaran date is ever written in code. A holiday event is
  **referenced, never copied**: a `festive` range of a calendar may name a holiday event (with optional days before
  and after) instead of fixed dates, and then takes its dates from that event's row for the year. Entering the event
  row for a year therefore fills the festive range of every calendar that references it; a calendar that references
  no event has no festive range from it. Holiday events also feed the compulsory surcharges below and nothing else;
- a supplier contract may attach a **compulsory surcharge** (a gala dinner on 24/25 or 31 December, a Tet surcharge)
  to a date or a holiday event; a stay that touches that date adds it.

The `peak` flag of a price row comes from the calendar. B2B quotes and the RRP use the same season logic, so the
`peak = false` path of the B2B quote goes away.

**Which calendar a trip plan uses.** A trip plan names one sell-side calendar in `season_calendar_id`. When the plan
is created it defaults to the calendar of the destination of its first day; staff may change it (for example a plan
that starts with one night in a gateway city and spends the rest in another destination). A multi-destination plan
is never priced by several sell-side calendars at once: its sell-side row is chosen by the **departure date** in its
own calendar. The cost sheet under it prices each night and service by its own day, in the calendar of the supplier
contract that prices it, with that contract's stay pricing flag (d3).

### d5 Which version applies to a quote

For a `trip_plan` line, Booking uses the version of that plan that is **published at the moment of the quote** and
whose **travel window covers the line's service date** (and whose sale window, when set, covers the quote day). When
several qualify, the overlap rule of d2 picks one. The season row inside it is the one for the service date (d4).

- When the next tariff year's version is published, a quote for a date in that year uses it, even while the current
  year is still on sale.
- The early-booking discount is judged on the quote day, as today.
- The agency discount (tier or rate card), the departure price adjustment, the FX lock and the rounding apply on top,
  as today.
- When the plan has published versions but none covers the date (a provisional one counts, d12), the line is **not
  quotable**: `POST /quotes` answers **409 `price_not_published`** with `line_refs` naming every such line, and no
  partial quote is written (contract 1.9; sample `problem-price-not-published-valid.json`). The CRM drops those lines
  or offers other dates.
- **Transition.** A plan with no published version at all (none of the 890 unpriced plans has one yet) keeps the 1.8
  pricing of its line, live from components × supplier rates, with `price_version_id` null, so no quote that works
  under contract 1.8 starts failing. The first published version of the plan switches it to version pricing. The
  existing matrix rows of the plans priced today are migrated into each plan's version 1 (d1), published, so those
  plans keep their prices.

This changes the B2B quote of a trip plan line: its agency price now comes from the published version, not from a
live re-computation of components × supplier rates. Booking still computes the live cost of the line for staff (the
margin view, the below-floor flag), and that cost never leaves Booking. `hotel_room` and service lines, which have no
plan, keep pricing from the supplier rates in force; their version is the supplier contract, pinned by the existing
`supplier_rate_ids`.

The quote line stores `price_version_id` and `tariff_version_id` (d7). Both are part of the `price_hash`.

### d6 Roles

| Role | Does |
|---|---|
| Customer service (maker) | creates drafts, imports Excel, copies to next year, submits for approval, withdraws own drafts |
| Product or pricing lead (checker) | approves or rejects pending price versions and supplier contracts, with a reason; withdraws a published version |
| Finance (`finance` role, ADR 0019 d3) | approves FX rows, tax rules and post-confirmation surcharge lines |

The maker and the checker are always two people. Booking maps these to permissions (proposed `price_version.write` and
`price_version.approve`) on its existing roles; the customer-service staff member gets the maker role from the CIS
Staff page grant (AA-1091 item 6), never from an engineer. The exact role-to-permission table goes into the Booking
`CONTEXT.md` with the code.

### d7 Agency tariff versions

A **tariff version** is a published snapshot of the B2B price list for one tariff year: the price list versions in
force for that tariff year, **one or more per sellable plan** (a mid-year change such as the d2 example adds a
version; each tariff row names its own `price_version_id`), with an id, a version number, `travel_from` /
`travel_to` (the tariff year), `published_at` and a change summary (how many tours and rows went up, down, in or out).

- Publishing or withdrawing price list versions (one approval, one withdrawal, or one auto-publish run) publishes the
  next tariff version of each tariff year they touch. The previous one becomes `superseded`.
- The **current** and the **next** tariff year run in parallel once the next one is published (decision 15, Q1).
- `GET /booking/b2b/v1/tariff` answers one tariff version for the calling agency: the version's rows, priced with the
  agency's discount and the FX rate in force today, cut from today at the earliest as in contract 1.4, and only for
  tours AA serves today (ADR 0015).
- **No version covering today.** `period=current` with no published tariff version covering today (before the first
  one, or a gap between two tariff years) answers **200** with no rows and every version field
  (`tariff_version_id`, `tariff_version_no`, `tariff_year`, `travel_from`, `travel_to`, `published_at`, `status`,
  `changes`, `next_tariff_version_id`) null; a 1.4 reader sees an empty tariff, never an error. 404 `not_found`
  applies only to `period=next` before it is published and to an unknown or withdrawn `tariff_version_id`.
- **ETag.** The answer carries a strong ETag: the SHA-256 of the exact body answered (the canonical JSON or the CSV
  bytes) for this agency, currency, `source_id`, `period` or `tariff_version_id`, and format. It therefore changes
  whenever anything the body shows changes: `priced_on` and the cut to today (so at least daily), the tariff version,
  its `status`, `next_tariff_version_id`, the RRP (from `booking.pricing_rules`), the agency discount, the FX rate and
  the set of tours served. `If-None-Match` with that value answers 304. The 304 saves the transfer, not the
  computation.
- An event `tariff.published` tells every agency that a new tariff version exists.
- A tariff row is information, not a promise; the quote stays the binding price (as in contract 1.4).

### d8 Recompute and the auto-publish threshold

`bk_price_recompute` no longer writes the matrix directly. It writes a version with `source = cost_sheet`:

- the version **publishes automatically** when every row it changes moves within ± the policy threshold
  (`recompute_auto_publish_pct`, decision 15, Q4, default 3 %) of the version it replaces, no row falls below the floor margin and no row is added or removed;
- otherwise it is **pending** and waits for the checker, with its diff and impact;
- the first version of a plan, and every hand-entered or imported version, always waits for a checker.

After every publish Booking re-prices four sample days of each changed plan (the first and last day of the window, one
peak day and one day the change did not touch) with the quote engine and alerts staff when a result differs from the
version's rows.

### d9 Diff and impact before approval

When a version is submitted Booking computes and freezes:

- the **diff** per row (season × pax band × channel × currency): old price, new price, change in percent; rows whose
  change in either direction is above the highlight threshold (`diff_highlight_pct`, decision 15, default 10 %) are
  marked, rows below the floor margin are flagged;
- the **impact**: the open quotes that will re-price when they expire, the tariff rows that change, the public "from"
  price change, and the margin per traveller at the expected party size.

The approve call carries the SHA-256 of the diff the checker saw; a mismatch is refused (409). The approve button
shows only after the diff has been shown. Supplier contracts, pricing rules and FX rows get the same preview before
their approval (advisory section 8, step 5).

### d10 Dates: inclusive outside, half-open inside

Excel, the staff UI and the contracts show **inclusive** end dates (the last travel date that the row prices),
the way supplier rate sheets are written. Inside Booking, new version and calendar tables store half-open ranges
`[from, to)`, converted only at the edges, so two adjacent ranges never leave a night without a price. Existing
inclusive columns (`booking.trip_plan_prices.valid_to`, `TariffItem.valid_to`) keep their meaning.

### d11 Confirmed bookings

A confirmed booking is never repriced. When a supplier cost changes after confirmation, staff see the difference as a
**margin variance** on the booking; the agency sees nothing and pays the confirmed price.

The only exception is a separate **contract surcharge line** added to the booking, never a change to an existing line.
All of these must hold:

- the cause is one the agency terms allow and the policy enables (`surcharge_causes`, decision 15, Q3: government tax
  and an FX move by default; fuel only if enabled). An FX move counts only when the rate in force on the day the line
  is raised differs from the rate **locked on the booking** (the quote's rate, ADR 0005a d3) by more than
  `surcharge_fx_threshold_pct` (default 5 %), measured in the agency's currency against USD;
- the partner terms clause exists, states the method of calculation and gives the same right when the cost goes down
  (a decrease is passed back as a negative line);
- finance approves the line (maker-checker);
- the agency is told in writing at least the notice period before departure (`surcharge_notice_days`, default 20
  days);
- an increase above the free-cancellation threshold (`surcharge_free_cancel_pct`, default 8 % of the booking price)
  lets the agency cancel free of charge.

Every other change is AA's cost. These conditions follow the EU package travel directive (Art. 10) and the UK Package
Travel Regulations (reg. 10), which bind AA's EU and UK agencies, who may recover their loss from AA. A lawyer confirms
the clause text (and the 2026 revision of the directive) before it goes into the partner terms. The surcharge line
reaches the CRM in a later minor of `booking.b2b.v1`, not in 1.9.

### d12 Provisional prices

A **provisional** version (`source = provisional`) fills a gap when a supplier has not sent next year's rates:

- it is built from last year's price of the same season plus the policy uplift (`provisional_uplift_pct`, decision
  15, Q12, default 5 %), or from
  the structured CIS reference price (AA-1091 item 5);
- it is flagged for staff and agencies (`provisional: true` on the quote line and the tariff row);
- a quote line priced from it is always `on_request`: AA staff confirm it by hand (the "book with review" path) and it
  is never confirmed automatically. On review staff either confirm at the provisional price (AA bears any difference)
  or decline the line so the agency re-quotes; the price never changes silently;
- a provisional version built from the CIS reference price serves the RRP and "from" display only, and is quoted to
  agencies only when the policy allows it (`provisional_cis_ref_quotable`, Q12, default false);
- a non-provisional published version wins over it on every date both cover (the overlap rule of d2), whatever their
  approval order; the provisional version becomes `superseded` once non-provisional versions cover all its window.

This also makes a hand-priced plan with no components sellable: its hand-entered version is published by a checker
and priced like any other version.

### d13 Excel export and import carry the version

- **Export** from a published version to `.xlsx`: every row carries `version_id` and `row_id`; dates are
  `YYYY-MM-DD` with inclusive end dates (d10).
- **Import** creates a new **draft** with `replaces_id` = the exported version. It is refused as a conflict when,
  after the export, another version of the same plan **whose travel window overlaps the exported version's travel
  window** was published or submitted (pending). Versions that do not overlap it, such as the next tariff year's
  version or the provisional draft of "copy to next year", never block a round-trip of the current year.
- One error anywhere means nothing is written. The dry run shows the errors by sheet, row and column, then the diff
  and impact (d9).
- **Copy to next year + x %** creates a provisional draft for the next tariff year.

### d14 Quote validity

The quote validity becomes policy data (decision 15, Q2: `quote_validity_days`, `quote_validity_festive_days`) in
place of the hard-coded 48 hours: default 14 days, 3 days for a quote that touches a festive period. A quote touches a
festive period when a service date of any of its lines falls in a `festive` range of the sell-side calendar used for
that line (d4): the plan's `season_calendar_id` for a `trip_plan` line, the calendar of the hotel's or service's
destination otherwise. One festive line shortens the whole quote. The code refuses a parameter value outside 1–30
days. Inside the validity the
quote is the promise (`price_hash`, 409 `price_changed` as today). After it expires, a re-quote prices on the
versions in force and the CRM shows "old price X, new price Y". Honouring the old price is an explicit departure
price adjustment with a reason (bk-048), never a silent re-use.

### d15 Policy parameters (business owner; the system ships with these defaults)

Pricing policy is a business decision. Each item below is a **policy parameter** in Booking: policy data, append-only
and approved by a second person like the pricing rules, never a code constant. The system ships with the proposed
default; the business owner may change any of them, and the change applies to new versions and quotes only.

| # | Question for the business owner | Proposed default |
|---|---|---|
| Q1 | When does the agency tariff year run, and when is it published? | 1 November to 31 October; the next year published by 31 August. Supplier contracts keep their own years |
| Q2 | How long is a B2B quote valid? | 14 days; 3 days when the trip touches a festive period (d14). At most 30 days |
| Q3 | May the price of a confirmed booking change? | No, except a surcharge line for government tax and an FX move above 5 %; at least 20 days' notice; decreases passed back; above 8 % the agency may cancel free. Fuel off |
| Q4 | Which price changes publish without a second person? | None entered by hand or imported. A recompute publishes by itself when every row moves within ± 3 %; outside that it waits for approval |
| Q5 | Who approves prices? | The product or operations lead approves prices; finance approves FX rates, tax rules and surcharges |
| Q6 | Which seasons does the agency price list use? | One calendar per destination: low, high, peak, festive. Supplier contracts keep their own seasons |
| Q7 | How are gala dinners and holiday surcharges charged? | A compulsory gala is charged at its full cost plus the standard margin; a Tet surcharge per hotel contract |
| Q8 | Deposit and cancellation | ADR 0019 b16: 30 % at confirmation, balance 30 days before departure. Cancellation: 30–22 days 10 %, 21–15 days 25 %, 14–8 days 50 %, 7 days to 48 hours 75 %, under 48 hours 100 %. Groups: 25 % deposit 8 weeks before. Festive periods: non-refundable within 30 days |
| Q9 | Groups of 9 travellers or more | Quoted on request in the first year; free places (FOC) per supplier contract, usually 1 per 15 |
| Q10 | Agency tiers | Keep three tiers, 0 / 3 / 6 % (ADR 0019 b15). A partner rate card only for large partners, with an end date and a volume commitment, reviewed yearly |
| Q11 | Currencies | USD for foreign agencies, VND for Vietnamese agencies; FX locked at the quote with the existing buffer (ADR 0005a d3). Circular 32 and VAT are checked by a lawyer or accountant |
| Q12 | Provisional prices when a supplier has not sent next year's rates | Allowed: last year's same-season price + 5 %, flagged, on request only. From the CIS reference price: display only, not quoted |

**The parameters.** Each scalar answer above is one named policy parameter. Booking validates a new value against the
allowed range and refuses anything outside it; the range is the code's only bound.

| Key | Question | Type | Unit | Default | Allowed range |
|---|---|---|---|---|---|
| `tariff_year_start` | Q1 | month-day | MM-DD | `11-01` | any valid month-day |
| `tariff_next_publish_by` | Q1 | month-day | MM-DD | `08-31` | a month-day before `tariff_year_start`; a reminder date, it blocks nothing |
| `quote_validity_days` | Q2 | integer | days | 14 | 1–30 |
| `quote_validity_festive_days` | Q2 | integer | days | 3 | 1 to `quote_validity_days` |
| `surcharge_causes` | Q3 | set of `tax`, `fx`, `fuel` | — | `{tax, fx}` | any subset; empty = no surcharge line ever |
| `surcharge_fx_threshold_pct` | Q3 | decimal | % against the rate locked on the booking (d11) | 5 | 0.5–50 |
| `surcharge_notice_days` | Q3 | integer | days before departure | 20 | 20–90 (20 is the legal minimum) |
| `surcharge_free_cancel_pct` | Q3 | decimal | % of the booking price | 8 | 1–8 (8 is the legal maximum) |
| `recompute_auto_publish_pct` | Q4 | decimal | % per row against the replaced version | 3 | 0–10; 0 = a recompute never publishes by itself |
| `diff_highlight_pct` | d9 | decimal | % per row | 10 | 1–50 |
| `provisional_uplift_pct` | Q12 | decimal | % on last year's same-season price | 5 | 0–25 |
| `provisional_cis_ref_quotable` | Q12 | boolean | — | false | true or false |
| `group_on_request_min_pax` | Q9 | integer | travellers | 9 | 2–60 |

The other answers are not scalar parameters; they are data Booking already has or this ADR adds: Q5 is the
role-to-permission table (d6, Booking `CONTEXT.md`); Q6 the season calendars (d4); Q7 the compulsory surcharges of
supplier contracts (d4) priced with the margin of `booking.pricing_rules`; Q8 the deposit and cancellation policy of
ADR 0019 b16; Q9's free places the supplier contract; Q10 the tier discounts and partner rate cards; Q11 the FX rows
and their buffer (ADR 0005a d3).

One more parameter set is not new: the target and floor margin per channel (`booking.pricing_rules`), always a
margin on the selling price, not a markup. The staff screens show both the margin and the equivalent markup.

### Contract change: `booking.b2b.v1` 1.9 (additive)

- `QuoteLine` gains `price_version_id`, `tariff_version_id` and `provisional` (a provisional line is always
  `on_request`).
- `Tariff` gains `tariff_version_id`, `tariff_version_no`, `tariff_year`, `travel_from`, `travel_to`,
  `published_at`, `status` (published or superseded), `changes` (counts only) and `next_tariff_version_id`;
  `TariffItem` gains `price_version_id` and `provisional`.
- `GET /tariff` takes `period` (`current` or `next`) and `tariff_version_id`, answers a strong `ETag` (SHA-256 of
  the body) and 304 on a matching `If-None-Match`; with no published tariff version covering today, `period=current`
  answers 200 with no rows and the version fields null (d7).
- `POST /quotes` may answer 409 `price_not_published` with `Problem.line_refs` (d5).
- The event type `tariff.published` with `Event.tariff_version_id`.
- No maker, checker, reason, cost or margin ever crosses the API (the root contract policy rejects `*_by`, net and cost
  fields; a rejected sample proves it).

A reader that ignores unknown fields and event types keeps working (contracts README rule 2). Until Booking serves
1.9 the new fields are absent; the CRM treats a missing `provisional` as false and a missing ETag as "always changed".

## Consequences

- **Positive:**
  - the customer-service screen gets maker-checker, a required reason and a diff, closing the largest gap;
  - one season logic for the agency price and the RRP, and no hard-coded holiday dates;
  - quotes and tariffs name what they were priced on, so a dispute can be answered from the record;
  - the CRM can cache the tariff and refresh it only when it changes (ETag, event);
  - versions exist from the first price the team enters, so the 890 plans never need a later migration of their
    prices;
  - pricing policy changes without a deploy.
- **Negative / cost:**
  - more Booking tables (versions, version rows, season calendars and ranges, holiday events, tariff versions, policy
    parameters) and contract migrations on existing tables (`trip_plan_prices`, `supplier_contracts`,
    `pricing_rules`, `b2b_quote_lines`): MIG-4 chains, each with its DM-7.1 retention row;
  - the B2B quote of a trip plan line changes its price source from live components to the published version (d5);
    a test proves the two agree right after a cost-sheet publish;
  - a checker becomes a bottleneck if the business owner sets no auto-publish threshold;
  - Excel round-trips can conflict when two people export the same version (d13 refuses the second import).

## Alternatives considered

- **Keep the overwrite and rely on the history table.** Rejected: history records who changed a price but not who
  approved it or why, and nothing stops a wrong price going live at once.
- **One global version number for all prices.** Rejected: plans change independently; a global number would make
  every unrelated change look like a new price list to every agency. The tariff version (d7) is the global view.
- **A version per price row.** Rejected: a diff and an approval are about a set of rows (a season table), not a cell.
- **Re-price confirmed bookings when supplier costs change.** Rejected: agencies choose suppliers that guarantee the
  price, and EU and UK package travel law limits it to stated surcharges (d11).
- **A commission (gross) model and a live BAR rate feed.** Out of scope: AA sells net prices to agencies (ADR 0019).
  A supplier with dynamic rates is priced by hand on the quote.

## Delivery order

1. Booking ships the policy parameters of d15 with the proposed defaults; the business owner may change any of them
   at any time as policy data, and a change applies to new versions and quotes only.
2. This ADR and `booking.b2b.v1` 1.9 (contract only).
3. Hand prices as versions: draft → pending → published, required reason, diff (inside the AA-1091 workbench).
4. Season calendars and holiday events; the `peak` substring goes; one peak logic for quotes and the RRP.
5. Diff and impact before approval of contracts, rules and FX; recompute through the auto-publish rule; reject and
   withdraw for pending rows; `supersedes_id` on contracts.
6. Quotes pin `price_version_id`; quote validity from policy; re-quote shows the difference.
7. Tariff versions, ETag and the next-year edition; the CRM reads by version.
8. Versioned Excel export and import, copy to next year, provisional prices.
9. Later: child age bands per product, single supplement and extra bed, FOC, group cancellation scale, automatic gala
   surcharges, hotel inventory type and release days, the post-confirmation surcharge line in the contract, a supplier
   invoice variance report.
