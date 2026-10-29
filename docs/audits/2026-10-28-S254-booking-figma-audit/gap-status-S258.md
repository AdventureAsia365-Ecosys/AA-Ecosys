---
id: APP-10-booking-figma-audit-gap-status
title: "AA-Booking Figma audit: status of the 25 product gaps in code (S258)"
description: "Checks each of the 25 product-gap majors of the S254 Booking Figma audit against AA-Booking main, names the PR that closed it or what is still open, and sets up the screenshot run for the re-score."
type: report
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-booking]
last_reviewed: 2026-10-29
review_every_days: 180
related: [AA-996]
---

# Status of the 25 product gaps in code (S258)

Agent: Claude Code (lane L4, S258). Date: 29/10/2026. Read against AA-Booking `origin/main` at `73a9caf` (release
0.12.0). Sources: `README.md` (S254, 34 majors: 25 product gaps + 9 evidence gaps), `scores.json` (the majors one by
one), `final-rescore.md` (S255, closed the 9 evidence gaps, score 7.39). This page checks the code only; the score
moves only after the screenshots below are taken and scored.

## Result

- **23 of 25 closed in code**, by the five AA-996 fix slices (Booking #125–#131) shipped in S254.
- **1 closed as an explained state** (#20: the draft-builder quote 403 is the E2E read-only guard, not a role gap;
  the price panel now says so).
- **1 open**: #19, the hotels photo grid (`/hotels` is still a table).
- **1 open outside the 25** (found by the S255 rescore): no row menu on the payments and invoices tables.
- `catalog.v_tour_place_name` (lane L4 first half) is **already done**: CIS 298 live, Booking #141 `ad4be194` reads it
  for the trip-plans list destinations, the perf guard forbids `catalog.v_tour_place` on the list
  (`backend/tests/catalog_perf.py` `LIST_FORBIDDEN_RE`), live budget `BUDGET_OK` (`v-tour-place-name-live-S256.md`).
  The schema reference (dump 29/10 07:18 UTC) lists the view with `grant booking: SELECT`. No other Booking read uses
  `catalog.v_tour_place` (the detail page reads `v_tour_day`). Nothing left to switch.

## The 25 product gaps

Item = the S254 "Top 15" row. Paths are under `apps/AA-Booking/frontend/` unless they start with `backend/`.

| # | Figma frame | Item | Gap (S254) | Status | Evidence on main |
|---|---|---|---|---|---|
| 1 | `CREATE NEW TEMPLATE.png` | 1 | No Supplier section | Closed | Booking #129 (bk-032 table) + #130 `d78ae20`: Supplier select (active suppliers, search) in `catalog/trip-plans/_parts/CommercialDrawer.tsx` |
| 2 | `CREATE NEW TEMPLATE.png` | 1 | No price matrix, only a price hint | Closed | #130: `PriceMatrixEditor.tsx` (channel × season × pax band), `GET/PUT …/trip-plans/{source_id}/prices` |
| 3 | `CREATE NEW TEMPLATE-1.png` | 1 | No Supplier section | Closed | as #1 |
| 4 | `CREATE NEW TEMPLATE-1.png` | 1 | No pricing rows / matrix | Closed | as #2 |
| 5 | `CREATE NEW TEMPLATE-2.png` | 1 | No Supplier select | Closed | as #1 |
| 6 | `CREATE NEW TEMPLATE-2.png` | 1 | No pricing rows / matrix | Closed | as #2 |
| 7 | `EDIT TEMPLATE.png` | 1 | No Supplier field | Closed | as #1 |
| 8 | `EDIT TEMPLATE.png` | 1 | Price hint instead of the matrix | Closed | as #2 |
| 9 | `EDIT TEMPLATE-1.png` | 1 | No Supplier field | Closed | as #1; read-only Included / Not included `CisField`s added too |
| 10 | `EDIT TEMPLATE-1.png` | 1 | Price hint instead of the matrix | Closed | as #2 |
| 11 | `EDIT TEMPLATE-2.png` | 1 | No Supplier field | Closed | as #1 |
| 12 | `EDIT TEMPLATE-2.png` | 1 | Price hint instead of the matrix | Closed | as #2 |
| 13 | `TEMPLATE MANAGEMENT.png` | 2 | List looks empty: unsellable first, placeholder thumbnails | Closed | #130: sellable first by default (API sort), `N days / N-1 nights`, destinations subtitle, row menu Edit commercial / Edit in CIS (`TripPlansView.tsx`); #125: `CisPhoto` neutral tile; #131 / #134 / #141: list extras (cover photo, destinations) read fast and fail soft |
| 14 | `TRIP PLAN TEMPLATES-1.png` | 2 | Rows of placeholders | Closed | as #13 |
| 15 | `TRIP PLAN TEMPLATES.png` | 2 | No trip style / price hint / photos in the default view | Closed | as #13 |
| 16 | `COUNTRY DETAILS-1.png` | 3 | No hero, no destination image gallery | Closed | #125 `26b8a8a`: `CountryHero` + `CountryGallery` with lightbox (`catalog/countries/_parts/CountryPhotos.tsx`), `cover_photo_path` + `photo_items` from `backend/app/catalog/geo.py` |
| 17 | `COUNTRY DETAILS.png` | 3 | No media block | Closed | as #16 |
| 18 | `COUNTRY MANAGAMENT-1.png` | 3 | Text-only country cards | Closed | #125: card cover + "N images" chip (`CountriesView.tsx`). Countries without a CIS Drive folder (VN, JP, IN) still show the neutral tile: CIS content, not a Booking gap |
| 19 | `HOTEL MANAGEMENT.png` | 14 | Table instead of the spec'd photo grid | **Open** | `hotels/_parts/HotelsView.tsx` is still a `DataTable`; no slice built the grid / table toggle. `docs/ui-spec.md` route map still says "Hotel grid" and `docs/figma-coverage.md` says "built" |
| 20 | `ITINERARY BUILDER-3.png` | 11 | Quote preview 403, no total | Closed (explained) | The 403 is the E2E read-only guard (`e2e_read_only`), not a role gap: the route needs `pricing.read` (`backend/app/routers/pricing.py` `CanPrice`). #127: `ui/booking/PricePanel.tsx` `quoteErrorView` shows "Live quote not available in this session" instead of failing silently |
| 21 | `PAYMENT & INVOICE-1.png` | 5 | Codes and dates wrap mid-value | Closed | #126 `7473755`: `whitespace-nowrap` on number, case, issued and next-due cells (`billing/page.tsx`) |
| 22 | `PAYMENT & INVOICE.png` | 5 | Codes and dates wrap mid-value | Closed | as #21 |
| 23 | `TRIP CASES  DETAILS-1.png` | 7 | Proposals tab rows have no actions | Closed | #127 `de3be3c`: Preview, Send to customer, Discard draft (`cases/[code]/ProposalsTab.tsx`) |
| 24 | `TRIP CASES  DETAILS.png` | 6 | Overview hierarchy inverted | Closed | #127: Trip details in the main column with an Edit pencil, duration / end date, header meta (`cases/[code]/page.tsx`) |
| 25 | `TRIP CHECKS.png` | 8 | Table overflows at 1440 px, Status clipped | Closed | #126 + #127: truncating Check / Customer / Owner cells, SavedTabs, per-trip progress (`trip-checks/page.tsx`) |

## Still open

1. **Hotels photo grid (#19).** Build the grid / table toggle from the S254 fix (first supplier photo or the neutral
   tile, photo count, place chip, updated, row menu), or record the table as an intended adaptation in
   `docs/figma-coverage.md` and change the ui-spec route map from "Hotel grid" to "Hotel table". The coverage matrix
   says "built" today, which is not true for the grid.
2. **Payments / invoices row menu (S255).** No `RowMenu` in `billing/page.tsx`; actions live on the detail pages.
   Add a row menu (View, Void, Download PDF when one exists) or record "actions on the detail page" as intended in
   `docs/figma-coverage.md`.
3. **Evidence only:** a declined TripPlanner inquiry and a fully paid invoice do not exist on Dev; `EDIT PAYMENT` and
   `SEND REMAINDER` stay not capturable (S255 "Still open").

## Re-score run

The script (outside the repo, run by the orchestrator: it signs in through the E2E mailbox with the MFA admin
profile) is in `.tmp-session/S258/booking/capture/` with a `RUNBOOK.md`:

- `MODE=gaps` (default): the 35 frames that evidence the gaps above (items 1, 2, 3, 5, 6, 7, 8, 11, 14 and the S255
  payments menu), for a quick check that the closed gaps look closed live.
- `MODE=all`: all 118 capturable frames (S254 records with the S254 recapture-list and S255 corrections; Bhutan for
  the country frames because Vietnam has no CIS photos), for the full re-score that replaces 7.39.

Scoring follows the S254 method (`README.md` "Method"): four dimensions, intended deviations do not lower the score.
