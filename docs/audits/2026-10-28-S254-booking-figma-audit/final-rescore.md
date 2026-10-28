---
id: APP-10-booking-figma-audit-rescore
title: "AA-Booking Figma audit: final rescore of the 8 evidence-gap frames (S255)"
description: "Re-captures the 8 frames the S254 audit marked as evidence gaps on live Dev with the E2E staff login, compares them with the Figma exports and gives the final audit score."
type: report
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-booking]
last_reviewed: 2026-10-28
review_every_days: 180
related: [AA-996]
---

# Final rescore of the 8 evidence-gap frames (S255)

Agent: Claude Code (lane AA-996, S255). Date: 28/10/2026. Follows `README.md` (S254, 7.3 / 10). Same method:
`https://booking.lumiguides.it.com` (Dev), Playwright Chromium 1440 × 900, light, one sign-in as the E2E staff user
`e2e-booking` (booking-admin, read-only session: every write is 403 `e2e_read_only`), compared with the Figma exports
in `docs/AAA/figma_AAA/`. No write was made and no confirm button pressed; menus closed with Escape.
Evidence: `recapture-S255/` (8 screenshots named like the Figma file, `capture.json`: URL, note, console / 5xx errors
per frame; none recorded).

## Result

**Overall: 7.39 / 10** (was 7.27, shown as 7.3; mean of the same 118 captured frames, median 7.0, range 5.5–9).

| Dimension | S254 | Final |
|---|---|---|
| Layout | 7.76 | 7.81 |
| Components | 7.43 | 7.51 |
| Content | 6.68 | 6.84 |
| Visual | 7.73 | 7.81 |

| Score band | S254 | Final |
|---|---|---|
| 9–10 | 21 | 21 |
| 8–8.9 | 16 | 17 |
| 7–7.9 | 46 | 52 |
| 6–6.9 | 23 | 22 |
| 5–5.9 | 12 | 6 |

The 8 evidence majors are closed. Two frames still cannot show the exact Figma state because Dev has no such
record and the audit must not create one (see "Still open"). Recapturing also surfaced one new product gap (payments
row menu).

## Per frame

Scores are overall (layout / components / content / visual).

| # | Figma frame | Live record (route) | S254 | Final | What the recapture shows |
|---|---|---|---|---|---|
| 13 | `Assigned Trips.png` | staff `e2e-claude-code` → `/staff/[id]?tab=cases` (TC-000003) | 5.5 (8/6/3/8) | **7** (8/7/6/8) | The table now has a row: case, customer, assigned as, status badge, trip start, assigned date, "Assigned cases (1)" tab count. **minor:** no trip title column (TC-000003 is a custom trip), dates show the start only (no end / duration), no period or sort filters (a search box instead), no per-row arrow (the code is the link). |
| 21 | `USER MANAGEMENT-4.png` | `/customers`, first row's `Actions for …` menu | 5 (8/5/4/7) | **8** (9/8/6/9) | The row menu is the Figma one: View profile, New trip case, divider, Block customer (red); plus Archive (intended: no hard delete). **minor:** no row checkboxes / bulk select, no period and country filters (merge-review and source instead), phone and location empty on the synthetic Dev customers. |
| 26 | `USER  DETAILS-4.png` | `/cases/TC-000013` (cancelled B2B case) | 5 (7/5/4/7) | **6.5** (8/7/5/8) | Nearest state on Dev: red "Cancelled" badge and a red reason banner ("This trip case is cancelled. Reason: …"), the same pattern as Figma's "Declined reason" box; two-column layout with details left and people right. Still **evidence-limited:** Dev has no declined or cancelled TripPlanner inquiry, so the client message panel and the "Reopen inquiry" action cannot be shown (declining a real inquiry for the audit is not allowed). |
| 46 | `ITINERARY BUILDER-4.png` | `/cases/TC-000003/proposals/2` (approved V2, 2 items, 1,675 USD) | 5 (7/6/3/6) | **7** (8/7/6/8) | A filled multi-day itinerary: collapsible day cards with dates, items spanning days ("Days 1–2", "Continues: … day 2 of 2"), the lock banner, and a price panel with net costs per item. **minor:** no morning / afternoon / evening slots or item descriptions on these two items (the approved items were built without them), no drag handles (locked version: intended), no template picker on an approved version (intended). |
| 47 | `ITINERARY PREVIEW.png` | `/cases/TC-000003/proposals/2/preview` | 5 (7/6/3/6) | **7** (8/7/5/8) | Same structure as Figma: day header (DAY n, title, date), the big day number column, item rows, and the right "Overview" card (trip case, customer, dates, travellers, destinations, status, sales) plus the price card. **minor:** no day hero photo or day body text (custom items, not CIS tour days), Destinations shows the ISO code `VN` instead of place names, no download / send actions on the preview (the builder holds them). |
| 97 | `EDIT HOTEL-1.png` | `/hotels?hotel=HTL-000001` drawer | 6 (7/7/4/7) | **7** (8/7/5/8) | A populated hotel: style Boutique, 4 stars, country Bhutan, supplier link, status, Edit / Deactivate, the "From CIS" customer content block and the supplier photos section. **minor:** city, address, geo point, check-in/out and links are empty on this Dev record; no gallery (photos and description are CIS-owned: intended). |
| 109 | `PAYMENT & INVOICE-3.png` | `/billing?tab=payments` | 5 (7/6/3/7) | **7** (8/6/7/8) | The right tab now: summary cards, Payments tab, search, status / type / method filters, rows with payment ref, invoice + case, date, method, amount, recorded by, status. **New product gap (minor):** the payment rows have **no row menu** (Figma: view eye + "…" with Edit / Download PDF / Delete); the row is a link and the actions live on `/billing/payments/[ref]`. The S254 note "open the row menu" cannot be done; the shot is the table itself. Also **minor:** no "Record payment" button on this tab (payments are recorded from the invoice), no row checkboxes, no period filter. |
| 118 | `View Details.png` | `/billing/invoices/INV-000003` (partially paid) | 6 (8/7/4/7) | **7.5** (8/8/7/8) | The full invoice view: billed to, issue / due dates, a lines table (line, qty, unit price, amount), totals (total due, paid, left to pay) and record payment / amend / remind actions. Shown as a page, not Figma's modal (intended). Still **evidence-limited:** Dev has no fully paid invoice (`billing/summary`: paid 0), so the "Paid" badge and the paid footer cannot be shown. |

## Still open

- **Data only (no code):** a declined TripPlanner inquiry (`USER DETAILS-4`) and a fully paid invoice
  (`View Details`) do not exist on Dev. The E2E session is read-only, so the audit cannot make them. A Dev demo seed
  (already proposed in `README.md`) or a session with a writing staff account would close them; until then both
  frames keep a small evidence penalty in the score above.
- **Product gap found here:** no row menu on the payments (and invoices) tables. Fold into the payments slice of the
  `README.md` fix plan: either a RowMenu (View, Download PDF when the PDF exists, Void) or record it as an intended
  adaptation (actions on the detail page) in `apps/AA-Booking/docs/figma-coverage.md`.
- `EDIT PAYMENT.png` stays not capturable (every Dev payment is verified or voided, `actions.edit=false`).
- Figma MCP was not needed: the comparison used the same exported Figma PNGs as S254 (`docs/AAA/figma_AAA/`), so the
  rescore is like-for-like. A second pass (same lane, later in S255) re-checked `Assigned Trips` and
  `PAYMENT & INVOICE-3` side by side against the exports and kept both scores; it added the missing "Record payment"
  button and checkboxes to the payments row.
