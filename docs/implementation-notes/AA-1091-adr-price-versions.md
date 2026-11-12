# AA-1091 — design part: ADR 0005b price versions and booking.b2b.v1 1.9 (S278, lane l13)

Docs only (root repo). No app code, no migration.

## Decisions

- **Amendment letter 0005b**, not a new number: the change amends ADR 0005 decisions 2, 3, 5, 6 and 7 and ADR 0005a
  decision 1; ADR 0019 is cited (b15, b16, d3), not amended.
- **Status Proposed** for d1–d15. The 12 policy items are parameters with shipped defaults, so the business owner can
  change them later as policy data without reopening the ADR.
- **Trip plan quote lines price from the published version** (d5), not from a live components × rates computation.
  Without this a quote could not pin a price version honestly, and hand-priced plans with no components could never be
  quoted. The live cost stays inside Booking for the margin view.
- **`price_version_id` and `tariff_version_id` per quote line**, not per quote: one quote can span two tariff years
  (current and next run in parallel).
- **Tariff ETag** covers the tariff version, the agency discount row, the FX row, currency, `source_id` and format,
  because the agency tariff changes when any of them changes, not only on a new version.
- **Tariff change summary as counts** (`TariffChanges`), never the maker's free-text reason: the reason is internal
  (`pii:free_text` class like `departure_price_adjustments.reason`) and the contract policy forbids `*_by` fields.
- **Provisional from the CIS reference price is display-only by default** (Q12), matching AA-1091 item 4 ("never quoted
  to agencies as a contract price"); provisional from last year + uplift is quotable on request only.
- **Post-confirmation surcharge line** stays out of 1.9; it reaches the CRM in a later minor once Booking builds it.
- The S278 advisory (Vietnamese, for the tech lead) is saved as `docs/audits/2026-11-12-S278-pricing-advice/` so the
  ADR links resolve.

## Changed

- New `docs/adr/0005b-price-versions.md`; pointers in ADR 0005 and 0005a; index row in `docs/adr/README.md`.
- `docs/contracts/booking.b2b.v1.openapi.yaml` 1.8 → 1.9 (additive): QuoteLine, Tariff, TariffItem, new
  `TariffChanges`, `GET /tariff` params `period`, `tariff_version_id`, `If-None-Match`, ETag header, 304 and 404;
  event `tariff.published` and `Event.tariff_version_id`; changelog paragraph; `x-aa-issues` gains AA-1091.
- Four samples: a valid quote with versions and a provisional line, a valid next-year tariff version, a valid event page,
  and a rejected tariff carrying `approved_by`.
- `docs/contracts/README.md` registry row gains the 1.9 entry.

## Tradeoffs

- Pricing trip plan lines from the version changes the quote engine (Booking work); a test must prove the version and
  the live computation agree right after a cost-sheet publish.
- Auto-publish of recomputes within ± 3 % keeps the checker from becoming a bottleneck, at the price of small automatic
  changes; hand and imported prices always need a checker.
- Half-open ranges inside, inclusive outside: one conversion at the edges, existing inclusive columns unchanged.

## Should know

- The registry row in `docs/contracts/README.md` never listed minors 1.7 and 1.8 (they are in the YAML changelog); not
  back-filled here.
- No code or migration numbers are reserved; the Booking lanes take the next free `bk-` numbers when they build.
- Booking `CONTEXT.md` ("Tour price chain", roles) is updated by the code lanes, together with the permission names.
