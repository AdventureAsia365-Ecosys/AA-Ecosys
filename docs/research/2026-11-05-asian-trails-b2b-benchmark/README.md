# Asian Trails B2B benchmark against the AA-Booking R4 design

Research note, S269, 05/11/2026. Author: Claude Code (research lane, AA-710; Jira KAN-20). Read-only: no code, no
paid call. It replaces the first look of 15/10/2026
([`../2026-10-15-asian-trails-b2b-benchmark.md`](../2026-10-15-asian-trails-b2b-benchmark.md)) and corrects one of
its facts and downgrades another to unconfirmed (see [Corrections](#corrections-to-the-first-look)).

**Question.** What does Asian Trails (a Bangkok DMC) offer B2B agents, feature by feature, and what does that mean
for R4 of ADR 0019 (Booking B2B only: AA-1037, the price chain AA-1029, agency price tiers AA-1030, "Book with AA"
d17)?

**Method.** Public primary sources only: Asian Trails' own site, news posts and terms; Lemax's site, support and
developer pages and a Lemax-authored case study; Juniper's client page; one trade-press article. Every claim about
Asian Trails or Lemax carries a source ID from [Sources](#sources), all accessed 05/11/2026. Anything no public
source states is written **unknown**. Nothing here comes from a login-only page (eConnect, Cloud Tariff), so the
agent-side screens themselves are not seen. AA facts come from the repos (paths given) and ADR 0019.

## Summary

- **Asian Trails sells inventory; AA sells its own operated tours plus content.** eConnect is a free, real-time B2B
  booking portal for accommodation, activities, transfers, multi-day tours and flights, with 20,000+ hotels and
  5,000+ activities, tours and transfers [S2][S3][S4]. AA sells only tours it operates (ADR 0019 b6) and puts the
  weight on the catalogue, per-agency content, TripPlanner and the agency CRM.
- **Most of what eConnect shows publicly is already in AA-Booking on Dev** (`booking.b2b.v1`: products, quotes with
  an FX lock, holds, confirm, cancel with a fee schedule, an event feed, an on-request desk). R4 adds what Asian
  Trails' terms describe on the money side: settlement invoices, deposits and balance terms, credit terms, tiers.
- **Asian Trails' rates are net and non-commissionable, with no published tier table** [S7][S8]. Its terms do mention
  "special contracted rates" tied to the business volume a client can drive and a confidential tariff with currencies
  agreed per partner [S8], so partner-specific terms exist in some form; their structure is unknown. AA's three
  published tiers (0 / 3 / 6 %) and an RRP of net + 25 % (b15) are more than Asian Trails shows publicly.
- **Five gaps are worth adding to R4** (one line each in [Gaps](#gaps-worth-adding-to-r4)): the cancellation policy
  on the quote, a booking confirmation for "Book with AA", a per-agency tariff export, a credit stop with overdue
  reminders, and an accountant export.
- **Not to copy now:** the flight engine and hotel wholesale, aggregator listings (TravelgateX, Juniper), card
  payments with surcharges, FX-difference invoicing, a bought DMC back office, and anti-publishing rules that would
  fight AA's content model.

## Sources

All accessed 05/11/2026.

| ID | Source | Owner / kind | Date on page |
|---|---|---|---|
| S1 | [Asian Trails, "2022" timeline entry](https://www.asiantrails.travel/?p=1040751) | Asian Trails | 2022 entry |
| S2 | [Asian Trails, "Asian Trails connects the world"](https://www.asiantrails.travel/?p=1032376) | Asian Trails news | 24/07/2023 |
| S3 | [Asian Trails, eConnect page](https://www.asiantrails.travel/econnect/) | Asian Trails product page | none (footer © 2024) |
| S4 | [Asian Trails, "Asian Trails views a bright 2024"](https://www.asiantrails.travel/?p=1034568) | Asian Trails, CEO article | 26/01/2024 |
| S5 | [Asian Trails, Technology page](https://www.asiantrails.travel/technology/) | Asian Trails | none |
| S6 | [Asian Trails, "How to Access Asian Trails' Cloud Tariff"](https://www.asiantrails.travel/?p=1032235) | Asian Trails news | 24/07/2023 |
| S7 | [Asian Trails, Conditions](https://www.asiantrails.travel/conditions/) | Asian Trails terms | none |
| S8 | [Asian Trails, B2B Terms and conditions](https://www.asiantrails.travel/destinations/b2b-terms-and-conditions/) | Asian Trails terms | none (footer © 2024) |
| S9 | [Lemax, "A warm welcome to our customer, Asian Trails"](https://lemax.net/news/lemax-unrivaled-on-the-competitive-tender-for-the-digital-transformation-of-asian-trails/) | Lemax news | 18/10/2018 |
| S10 | [Lemax case study: Asian Trails](https://www.casestudies.com/company/lemax/case-study/asian-trails-highly-automated-processes-fully-loaded-product-database-functional-operations-and-quoting-an-all-in-one-solution) | Lemax-authored, hosted on CaseStudies.com | none |
| S11 | [Lemax home page](https://lemax.net/) | Lemax product | none |
| S12 | [Lemax, Sales](https://lemax.net/sales/) | Lemax product | none |
| S13 | [Lemax, Operations](https://lemax.net/operations/) | Lemax product | none |
| S14 | [Lemax, Finances and accounting](https://lemax.net/finances-and-accounting/) | Lemax product | none |
| S15 | [Lemax developer documentation index](https://support.lemax.net/developer-category/documentation) | Lemax support | none |
| S16 | [Lemax B2B API (XML Out) developer guide](https://support.lemax.net/developers/b2b-api-developer-guide/) | Lemax support | none |
| S17 | [Juniper, client page "Asian Trails"](https://ejuniper.com/en/clients/asian-trails/) | Juniper | none |
| S18 | [TTR Weekly, "Asian Trails: Blazing new trails in digital space"](https://ttrweekly.com/site/2025/03/asian-trails-blazing-new-trails-in-digital-space) | Trade press | 19/03/2025 |

S11–S16 describe **Lemax's product in general**. They show what Asian Trails *could* use. No public source says
which of those modules Asian Trails runs today, except S9 and S10.

## What Asian Trails runs (public facts)

- **eConnect (agent portal).** Launched with technology partner 11Infotech [S1], first shown at WTM London at the
  end of 2022 [S2], live since November 2022 [S4]. A "real-time booking solution for B2B travel products and
  services", free to register, custom-designed with 11-Infotech [S3]. Agents can "build a multi-country journey of
  hotels, transfers, tours, excursions, and flight services" and book "any product type online in real time", with
  Google Maps on properties and a flight booking engine added in 2023 [S2]. Inventory: 20,000+ accommodation options
  and 5,000+ activities, tours and transfers; channel-manager integrations give real-time rates and availability; it
  "compares prices from multiple contracting models" [S3].
- **API.** Direct connectivity for OTAs, tour operators and others, and access through aggregators "such as
  TravelgateX or Juniper"; the APIs cover hotels, transfers, tours and excursions, with static and dynamic rates and
  "all services immediately confirmed" [S4]. The eConnect page states under 0.5 s response, a Kubernetes / Kafka /
  Cassandra stack and a real-time cache for metasearch [S3]. Juniper lists Asian Trails as a client of Juniper Hub
  (type "Accommodation providers", Thailand) [S17]. **Protocol (XML or JSON), authentication and the API document
  are unknown**: no public Asian Trails API reference was found; requests go to an e-mail address [S3].
- **Cloud Tariff.** An "exclusive, agents-only hub for tour information, rates and special offers", behind a login,
  with tariffs per destination for hotels, excursions, transfers and seat-in-coach tours [S6]; "a one-stop portal for
  rates, destination information and industry resources" [S5]. It descends from a printed annual tariff (1999) [S18].
  S6 adds: "Ask your Asian Trails sales contact for more information about how to access exclusive rates and services
  via the Cloud Tariff." S8 calls it a "confidential tariff" whose rates are "in various currencies, as mutually agreed
  between Asian Trails Ltd. and the B2B (Business-to-Business) partner", and offers "special contracted rates" based on
  the business volume a client can drive. **Whether the tariff content differs per agent, its file formats and its
  update rhythm are unknown** [S6][S8].
- **Media library.** More than 200,000 hotel and destination images for registered partners [S5].
- **Back office: Lemax.** Lemax won Asian Trails' digital-transformation tender in 2018: cloud software for
  operations, integrated with accounting and other systems, plus a new website [S9]. The Lemax case study (vendor
  text) reports go-live in 2019, a product database of hotels, transfers, excursions and packages, "auto-confirmations,
  auto-invoices, auto-itineraries", operations for transfers, excursions, private services and coaches, and "more than
  half of its FIT bookings" moved into Lemax; before, about 90 % of FIT tours were quoted in Excel [S10]. **Whether
  Lemax still runs the back office in 2026, and how eConnect links to it, are unknown**; a 2025 article speaks only of
  a "cloud-based system landscape" [S18].
- **Commercial terms (B2B).** "Not an open platform"; free for B2B partners, no reservation fee; quoted rates are net
  and non-commissionable; a pre-agreed handling fee applies when Asian Trails acts on the client's own supplier
  contracts [S8]. Full prepayment at least 30 days before arrival unless a credit arrangement exists; credit can be
  suspended when unpaid invoices pass the agreed terms; each invoice carries its own booking reference and the
  client's reference; payment per country [S8]. Cancellation terms follow each supplier's policy and are shown in the
  reservation [S8], "on the website during booking" [S7]. A confirmation e-mail carries the exchange e-voucher(s); "on
  request" bookings are confirmed later, with no fee if they cannot be [S7]. A rate-error clause lets Asian Trails
  correct large published-rate errors (70 % or more, or 500 USD/EUR or more per booking), with free cancellation if the
  agent does not reconfirm within 7 days [S7]. Agents may not resell, deep-link, scrape or redistribute content or
  rates; confidential rates may not be shown or sold online unless packaged [S8]. Asian Trails follows Minimum Selling
  Price guidelines from its supplier contracts [S7]. Rate currency: S8 says "US$ only" in one section and "various
  currencies, as mutually agreed" in another; **which applies is unknown**.

### Corrections to the first look

- eConnect was built with **11Infotech**, not on Lemax [S1][S3]. Lemax is the back office (2018 tender, 2019 go-live)
  [S9][S10]; the link between the two is unknown.
- "Online rate sheets published per partner" is **unconfirmed**, not disproved. Public sources show one agents-only
  hub behind a login [S6]. S6 says exclusive rates are accessed via the Cloud Tariff (ask the sales contact), and S8
  describes a confidential tariff with currencies agreed per partner and special contracted rates by business volume.
  Whether the tariff content differs per agent is unknown.

## Feature by feature

"AA today" = on Dev now (repo paths). "R4" = planned in AA-1037 / AA-1029 / AA-1030 / d17 (ADR 0019,
`docs/audits/2026-11-03-S265-ecosystem-restructure/clarifications.md` BO-15..17 and the R4 row).

| Feature | Asian Trails | AA today (Dev) | AA after R4 | Read |
|---|---|---|---|---|
| Search and availability | Real-time search over hotels, activities, transfers, multi-day tours, flights; maps; channel-manager rates [S2][S3] | `booking.b2b.v1` products sync and `GET /departures` (seats counted, never stored); a quote marks each line `available` / `on_request`; CRM keeps a cache of AA tours (Booking and Partner `CONTEXT.md`) | Unchanged; tours retired by CIS block new holds (d20) | AA covers its own tours. Hotels and flights are out of scope by design (b6) |
| Quoting | Prices compared across contracting models [S3]; Lemax quote with several offers [S12] | `POST /quotes`: priced lines, `price_hash`, `valid_until`, FX lock, VND quotes (AA-972, AA-974) | Tier price per agency (AA-1030); RRP on every b2b row (AA-1029, live S267) | Covered. Gap: the quote does not show the cancellation policy (G1) |
| Booking and confirmation | Real-time booking, "all services immediately confirmed" [S2][S4]; on-request confirmed later [S7] | Holds (48 h, one extension, re-hold limit), confirm into a B2B trip case; `auto_confirm` departures; on-request desk with a 1-business-day answer SLA (AA-973..975) | "Book with AA" quote/hold form in Content for tenants without the CRM, plus a "Bookings with AA" page (d17) | Covered. Gap: no confirmation document for "Book with AA" (G2) |
| Cancellation and amendments | Supplier policy, shown at booking; some rates non-refundable [S7][S8] | One AA policy per plan or the B2B default (tiers by days, maker-checker), `?dry_run=true` fee check (AA-974) | Unchanged | AA is clearer (one schedule, dry run) once G1 shows it before booking |
| Invoicing | Invoice per booking with the client's reference [S8]; Lemax auto-invoices and batch invoices [S10][S14] | B2C invoices only (frozen with d8) | `agency_invoice` with two kinds (software fee, tour settlement), gap-free number series, tax rules as data, drafts made by jobs (AA-1037, d9) | Covered by AA-1037. Gap: no export for the accountant (G5) |
| Payments, deposits, credit | Full prepayment 30 days before arrival unless credit; credit suspended on overdue invoices [S8]; card payments for some hotels, with a surcharge [S7]; Lemax: payment rules, credit limit per agent, bank-statement import, reminders [S14] | Maker-checker manual payments (B2C side) | `agency_payment` maker-checker with evidence; partner terms: 30 % deposit at confirmation, balance 30 days before departure, credit after about 6 months with a limit (b16, AA-1037); no card payments (b14) | Covered in design. Gap: enforcing the credit limit on new holds and reminding overdue invoices (G4) |
| Agent tiers, markups, commission | Net, non-commissionable rates; handling fee for the client's own contracts [S8]; "special contracted rates" by the client's business volume and tariff currencies agreed per partner [S8]; exclusive rates accessed via the Cloud Tariff, details from the sales contact [S6]; tier structure unknown. Lemax supports commission rules per market [S12] (use by Asian Trails unknown) | One global `b2b` margin rule; RRP = net + `rrp_markup_pct` (25 %) on b2b rows (AA-1029) | Three tiers 0 / 3 / 6 % with an optional contract rate card per partner; CRM suggests a retail markup (AA-1030) | AA goes further than Asian Trails shows |
| Rate sheets for agents | Cloud Tariff hub per destination, behind a login; exclusive rates accessed through it; per-agent content unknown [S6][S8] | "From" price (cheapest RRP) in the tenant Marketplace and TripPlanner (`price.from.v1`) | Tier price in quotes | Gap: no downloadable per-agency tariff (G3) |
| API for agencies | Direct API plus aggregators; hotels, transfers, tours, excursions [S4]; protocol unknown | `booking.b2b.v1` (REST/JSON, OpenAPI in the Booking repo) for AA-Partner only, `aa-m2m` client credentials | No change: a public agency API waits for R8, built when a paying tenant asks (d6, d17) | Keep the R8 trigger. Not to copy now: aggregators |
| White label and branding | Not stated for eConnect; resale and online display of rates restricted [S8]. Lemax has white-label documents [S12] (use by Asian Trails unknown) | Tenant brand voice on generated content; CRM documents carry the agency's name; "Powered by AA" off by default (b8) | Unchanged | AA is ahead: content is made for the agency to publish |
| Payments to AA online | Card gateway for some hotels [S7]; Lemax payment links on quotes and invoices [S14] | None (manual, b14) | None (b14; asked again when volume passes manual capacity) | Not to copy now |
| Document generation | Confirmation e-mail with e-vouchers [S7]; Lemax auto-itineraries, invoices and vouchers [S10][S12][S13] | B2B cases take no voucher or document (traveller data stays with the agency, DM-6.8); the CRM builds client proposals, an offline itinerary and invoices to travellers (AA-Partner `CONTEXT.md`) | Agency invoice documents generated in Booking (d9, b14); a guest-list path for "Book with AA" (R4 row of `clarifications.md`) | Gap: a name-free booking confirmation for "Book with AA" (G2) |
| Content and media | 200,000+ images for partners [S5]; tariff includes country information [S6] | Rewritten catalogue, per-agency versions, SEO, publish to WordPress and Facebook (CIS) | Unchanged | AA's main edge |
| Supplier side | Suppliers get access to update rates, availability and policies [S8]; Lemax YES/NO supplier links [S13] | Supplier rate-sheet Excel import with maker-checker (AA-1029); supplier bookings and bills (AA-682) | Unchanged | Not to copy now: supplier extranet |
| Accounting link | Lemax integrated with accounting [S9]; QuickBooks, Oracle ERP, an accounting API [S14] | None | VAT e-invoice issued by the accountant in the e-invoice software, number stored on the invoice (AA-1037) | Gap: export file for the accountant (G5) |
| Price errors | Rate-error clause: correction, free cancellation if not reconfirmed in 7 days [S7] | `price_hash` refuses a changed price within quote validity | Unchanged | Optional policy line in partner terms (G6) |

## What R4 already covers

- **Money terms as data** (AA-1037, BO-15..17): deposit, balance days, credit terms and limit, tiers, tax wording, all
  editable in admin with a second approver. This matches the substance of Asian Trails' B2B payment terms [S8].
- **Settlement invoicing** (AA-1037, d9): one series per invoice kind, drafts from jobs, maker-checker payments, the
  VAT e-invoice number field. Comparable to Lemax auto-invoices [S10], without a payment gateway.
- **Agency prices** (AA-1029 live on Dev, AA-1030): net per season from supplier rates, RRP = net + 25 %, three tiers
  and contract rate cards. Asian Trails publishes no tier model [S8].
- **Booking for tenants without the CRM** (d17): a quote/hold form in Content, "Bookings with AA", e-mail fallback.
  This is AA's equivalent of eConnect for Content-only agencies.
- **Already built before R4:** quotes, holds, confirm, cancel with fee and dry run, event feed, on-request desk with
  an SLA, departure incidents (AA-972..975). Asian Trails publishes none of these API details.

## Gaps worth adding to R4

Each line is a proposal; the issue in brackets is where it would go. None needs a paid service.

- **G1** Add the cancellation policy in force (tiers by days, fee %) to the `booking.b2b.v1` quote and hold answers,
  so an agency sees the fees before it books, as Asian Trails shows them during booking [S7] (AA-1037; a contract
  minor version).
- **G2** Give "Bookings with AA" a booking confirmation document per booking: booking reference, services, dates, pax
  counts by age band, supplier confirmation refs, the policy in force; no traveller names (AA-1037, d17 Booking end).
- **G3** Add a per-agency tariff export (the agency's tier price per tour, season and pax band, as CSV and a printable
  page) from the price matrix, as AA's answer to the Cloud Tariff [S6] (AA-1030).
- **G4** Enforce the partner's credit terms: new holds answer a clear refusal code while settlement is overdue past
  the agency's terms, and overdue agency invoices get reminder e-mails through the existing Booking mailer, as Asian
  Trails suspends credit on overdue invoices [S8] (AA-1037).
- **G5** Add a period export of agency invoices and payments (CSV) for the accountant, instead of an ERP integration
  (AA-1037).
- **G6** Optional: a price-error line in partner terms (how AA corrects a published price that was clearly wrong, and
  the agency's free-cancel window), for the business owner to word, as in Asian Trails' conditions [S7] (AA-1037,
  terms data only).

## What not to copy

- **Hotel wholesale and a flight engine** [S2][S3]: AA sells only tours it operates (b6); agencies add flights and
  other ancillaries in their own CRM.
- **Aggregator listings (TravelgateX, Juniper)** [S4][S17]: they expose net rates to unknown resellers and fight the
  per-agency content model; any machine API waits for the R8 trigger (a paying tenant asks).
- **Card payments with surcharges and payment links** [S7][S14]: b14 keeps invoices and payment marking manual until
  volume needs more; Stripe is not open to a Vietnamese entity (`clarifications.md` BO-14).
- **FX-difference invoicing before travel** [S14]: AA locks FX on the quote; agencies get one price.
- **Buying a DMC back office (Lemax)** [S9][S10]: AA-Booking is built in-house (root ADR 0004) and already covers
  rates, supplier bookings, bills and B2B; buying now would mean a migration with no gain at pilot volume.
- **"No publishing" rules on content** [S8]: Asian Trails forbids redistributing its content; AA's product is content
  the agency publishes. AA's resale rule is about price (b7), not content.
- **Supplier extranet / channel manager** [S3][S8]: the rate-sheet import (AA-1029) is enough for AA's own tours at
  current volume.

## Unknowns

- eConnect's agent-side features beyond the public pages: markup settings, user roles, sub-agents, invoices and
  statements in the portal, vouchers in the portal, multi-currency display.
- Asian Trails' API protocol (XML or JSON), document, authentication and rate limits.
- Whether the Cloud Tariff content differs per agent (S6 and S8 hint at partner-specific rates and currencies; not
  confirmed), and its formats and update rhythm.
- Whether Lemax is still the back office in 2026 and how eConnect connects to it.
- Rate currency (S8 states both "US$ only" and "various currencies").
- TravelgateX listing: stated by Asian Trails [S4], not confirmed by a TravelgateX source.

## Next step

The tech lead picks which of G1–G6 go into R4; each fits the named issue without a new Linear issue. The KAN-20
comment draft for the business owner is in [`kan-20-jira-comment-DRAFT.md`](kan-20-jira-comment-DRAFT.md)
(not posted).
