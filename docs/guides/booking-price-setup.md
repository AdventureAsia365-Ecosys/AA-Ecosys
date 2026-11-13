---
id: GUIDE-12-booking-pricing
title: Booking price setup
description: How the customer-service team enter tour prices - access, Price setup, hotels and services from the CIS itinerary, the price workbook with its DRY RUN, price versions, seasons, provisional and CIS reference prices, and checking a tour is on sale.
type: how-to
status: draft
owner: nghiep
audience: [staff, owner]
applies_to: [aa-booking-admin, aa-booking-api, aa-cis-frontend, aa-cis-api]
last_reviewed: 2026-11-13
review_every_days: 90
related: [GUIDE-12, GUIDE-12-booking, GUIDE-12-cis-admin, AA-1091]
---

# Booking price setup

This guide is for the customer-service team who enter tour prices. It walks through each page in the order you use
it. Sign-in, roles and the other Booking work are in the [Booking admin runbook](booking-admin-runbook.md). A
Vietnamese version of this page is [booking-price-setup.vi.md](booking-price-setup.vi.md).

Button and page names below are the English screen text. **Price setup**, **Seasons**, **Holiday events** and the
CIS **Reference prices** page also have an EN | VI switch.

## 1. Get access

1. Ask a platform owner (today the tech lead).
2. The owner opens CIS admin › **Platform › Staff & access**, opens your row and chooses **Apply pricing preset**.
   One save gives you CIS **Customer Success** (Reference prices) and Booking **Contracting** (supplier rates,
   pricing rules, trip plans, departures, price versions, seasons).
3. Sign out and sign in again in both apps.

The preset only adds rights. If you already hold another role in one app (for example Booking **Sales** or
**Finance**), the button is disabled and names that role: each app gives one role per person, so the owner changes
it by hand. Booking **Sales** can read every pricing page but changes nothing.

Every price change needs **two people**: you make it, a second person with Contracting or Booking admin approves it.
You never approve your own change.

## 2. Read the Price setup page

Open Booking › **Supply › Price setup**. Each row is one tour (trip plan) with seven checks: **Hotels & services**,
**Supplier rates**, **Exchange rate**, **Pricing rule**, **Price**, **Sellable** and **Departures** (optional: tailor-made
tours have none). The tiles on top count every tour; filter by **Next step**, **Missing**, **Price status** or
**Country**, or search a title or key.

The **Next step** column says what the tour waits for:

| Next step | What to do |
|---|---|
| **Add hotels & services** | Open **Hotels & services** for the tour (section 3) or use the workbook (section 4) |
| **Replace an inactive item** | A hotel, room type or service was switched off: replace it in **Hotels & services** |
| **Load supplier rates** | A component has no published supplier rate: load the supplier's rate sheet (section 3, last step) |
| **Approve an exchange rate** | A rate currency has no approved FX rate today: ask for one on **Pricing rules & FX** |
| **Approve a pricing rule** | No approved agency pricing rule is in force: ask the pricing lead on **Pricing rules & FX** |
| **Recompute prices** | Everything is there but prices are not computed yet: select the tours, **Recompute prices** (50 at a time) |
| **Make sellable** | Select the tours, **Make sellable** |
| **Ready to sell** | Nothing left to do |

Hand prices alone never make a tour **Ready to sell**: an agency quote prices the tour from its hotels and services
and their supplier rates.

## 3. Add hotels and services from the CIS itinerary

1. On **Price setup**, click the tour or its **Hotels & services** link.
2. For each day Booking suggests the hotel of the night and the services the CIS itinerary names (transfer, guide,
   entrance, activity, lunch or dinner), with **Why** and a strength (strong, likely or weak match).
3. For each suggestion choose **Accept**, pick an **Other match** or another **Room type**, or **Reject**. **Remove**
   items that are wrong; **Already on the tour** means nothing is needed.
4. Click **Save N hotel and service item(s)**. Nothing changes before you save; a rejected suggestion comes back
   the next time you open the tour.
5. **No match** means Booking has no such hotel or service yet: use **Create supplier**, **Hotels** or **Services**,
   then open the tour again.
6. For a component without a rate: **Supply › Suppliers**, open the supplier, **Import rate sheet**, **Download the
   template**, fill it, **Check**, then **Import as draft**. A second person publishes the draft contract.

## 4. Many tours at once: the workbook

### Download and fill it

1. On **Price setup**, filter the tours you want, then **Download workbook** (prefilled with those tours, at most
   300). For new tours, open **Import workbook** and choose **Blank workbook**.
2. Fill the sheets. Keep **Tour key**; **Title** and **Country** are for reading only. Dates are `YYYY-MM-DD`.

| Sheet | Columns | Rule |
|---|---|---|
| **Tours** | Tour key, Sellable | `yes` or `no`; empty keeps it as it is. A sellable tour needs hotels and services |
| **Components** | Tour key, Day, Hotel code + Room type, or Service code | One item a row. A tour listed here gets exactly these items (the rest are removed) |
| **Prices** | Tour key, Channel, Season, Peak, Valid from, Valid to, Pax min, Pax max, Currency, Price per person, Child price, Infant price, Single supplement | See below |
| **Departures** | Tour key, Start date, Capacity, Min to operate, Sales cutoff days, Decision days before, Auto confirm, Status | New dates only, after today; a date the tour already has is skipped. Status `scheduled` (default) or `guaranteed` |

**Prices** sheet, one row per pax band and date range:

- **Channel**: `b2b` (default) or `fixed_departure`. **Currency**: empty = USD; the **Check** names any currency
  that is not a selling currency.
- **Pax min** / **Pax max**: the group size of the band, for example 2–2, 3–4, 11 and empty (empty = no upper
  limit). Rows of one channel and currency must not overlap in dates and pax.
- **Valid from** / **Valid to**: travel dates; the last day is included.
- **Season** is a label for people. **Peak** is still read but decides nothing: the tour's season calendar decides
  the season and the peak uplift (section 6).
- A tour listed here gets a **draft price version** with exactly these hand prices. Prices worked out from supplier
  rates stay, unless a hand row covers the same dates and pax.

### Check, then import

1. Open **Import workbook**, pick the file under **Filled workbook (.xlsx)** (at most 2 MB) and click **Check**.
   This is the DRY RUN: nothing is written.
2. Read the result. Each problem names the sheet, the row and the column. Fix the file and **Check** again until no
   problem is left. For each tour the result shows what changes and its price status **now** and **after**.
3. Click **Import**. Importing the same file again changes nothing.
4. Open each tour's **Versions** tab and submit its draft (section 5). Its new prices count only after approval.

## 5. Price versions: submit and approve

Every price change is a new **version**; nothing is overwritten or deleted.

1. On **Price setup**, open the tour's **Price versions** link (or the tour, tab **Versions**).
2. A workbook import already made the draft. To change prices by hand: **New draft from the prices in force**, edit
   the rows and the travel window, **Save draft**.
3. Type the **Reason for the change** (required, at most 300 characters) and click **Submit for approval**.
4. The second person opens the same tab and reads **Changes against the prices in force**: each row before and
   after, large changes highlighted, rows below the floor margin flagged, rows that stop. **What it touches** counts
   open quotes, departures and agency price rows in those dates.
5. The second person clicks **Approve** (or **Reject** with a reason). The version is **Published** and the tour's
   prices are updated.

What changes after approval:

- New quotes, the agency tariff and the suggested retail price use the new prices for the travel dates the version
  covers. Future departures in those dates take them.
- An open quote keeps its price until it expires; a re-quote after that uses the new version. A confirmed booking
  never changes price.
- **Withdraw** stops a version for anything new; the dialog shows which older version prices those dates again and
  which dates can no longer be quoted. A published version is withdrawn by a second person.

Quote validity, the group size quoted on request and other business rules are on **Supply › Pricing policy**. Their
changes also need a second person; see the [Booking admin runbook](booking-admin-runbook.md).

## 6. Season calendars and holiday events

Each destination has a season calendar; a tour uses the calendar of its first day's destination. Until a calendar
has an approved range, every date is low season and no price moves.

1. Open **Supply › Seasons** and open the calendar.
2. **Add a range**: **Kind** (**Season** or **Stop-sale**), **Season** (Low, High, Peak, Festive), **First day**,
   **Last day**, a **Reason**, then **Propose**. A festive range can **Follow a holiday event** instead of fixed
   dates (event country, event code, days before and after).
3. A second person clicks **Approve**. **Season of the other dates** sets the season of every date no range covers
   (**Ask to change**, then approval).
4. Holiday dates are data: **Supply › Holiday events**, **New holiday event** for each country and year (for example
   the Lunar New Year), approved by a second person.

Peak and festive dates take the peak uplift of the pricing rule. A festive date also shortens the quote validity. A
stop-sale range puts the tour on request on those dates; it never changes the price. To give a tour another
calendar, use **Season calendar** on its **Versions** tab: the change waits for a second person.

## 7. Provisional price from the CIS reference

For a tour with no supplier price yet you may show the CIS reference price as a **provisional** retail price.

1. On **Price setup**, select the tours and click **Show CIS price as provisional**.
2. The workbench marks them **Provisional: no supplier price yet**. **Clear provisional price** removes it.

A provisional price is never a contract price. It is never quoted to an agency and never appears in the agency
tariff or on TripPlanner: they use supplier and hand prices only. A tour is skipped when CIS has no reference
amount, when it already has a supplier price, or when staff typed a price hint by hand.

## 8. CIS reference prices

The reference price is the price the source sheet names for a tour: amount, currency and basis. Booking staff
compare it with the computed price. It is never a selling price.

Open CIS admin › **AA Catalogue › Reference prices**. Statuses: **No price**, **Suggested** (CIS read a price in the
text), **Not reviewed**, **Needs review** (doubts, or the source text changed), **Confirmed**.

- **One tour**: type the **Amount**, pick the **Currency** and the **Basis** (**Per person**, **Per group**, **From
  (per person)**), an optional note without personal data, then **Save**. **Accept** confirms a suggestion as it is.
- **Many tours on screen**: **Read source texts** (a DRY RUN), then **Save these suggestions**. Filter **Not
  reviewed**, select the rows and click **Accept N selected**.
- **Excel**: **Export Excel** (follows the filter), fill Amount, Currency, Basis and keep **Key**. Type `yes` in
  **Confirm** to confirm a price as it is. **Import Excel**, **Check the file (DRY RUN)**, fix every error line, then
  **Apply import**. A file with one error saves nothing.

A **Per group** price gives Booking no per-person amount, so it cannot become a provisional price.

## 9. Check that a tour is on sale

1. **Price setup**: the tour's next step is **Ready to sell**, its status **Priced**, and **Sellable** is ticked.
   **Supply › Price readiness** shows the same status for every tour.
2. **Agency tariff**: **Supply › Agency tiers**, tab **Agencies**, **View tariff** on an agency. The tour is listed
   with its price per season and pax band. A sellable tour that a quote cannot price is listed apart with the reason.
3. **TripPlanner**: the tour page shows **From $X**, the lowest suggested retail price per person for 2 travellers
   among the agency prices still valid. A provisional price never shows there.

## 10. When something looks wrong

| You see | Then |
|---|---|
| **Check** lists problems | Fix each named sheet, row and column in the file and check again; nothing was written |
| A tour stays on **Load supplier rates** | A rate sheet is still a draft, or a rate does not cover the coming year: ask a second person to publish it |
| The approve button is missing | You made this version: a second person approves it |
| **No approved agency pricing rule is in force** banner | No tour prices from supplier rates; ask the pricing lead |
| A page refuses a change | Your role does not include it; ask the platform owner |

During the dev phase the tech lead is the engineer on duty: a Jira issue for normal problems, a direct message when
urgent. Give the page address, the tour key, the time and a screenshot.

## Sources (for maintainers)

Read from AA-Booking `main` on 2026-11-13: `frontend/ui/local/nav.tsx`, the `(staff)/pricing` pages and their
`messages.ts` (workbench, versions, seasons), `suppliers/_parts/RateSheetDrawer.tsx`,
`backend/app/catalog/price_import.py` (workbook columns, checks and the Read me lines), `CONTEXT.md` ("Tour price
chain", "Agency price tiers"), `docs/implementation-notes/AA-1091*.md`; AA-CIS-App `frontend/lib/adminIa.ts`,
`frontend/app/admin/reference-prices/messages.ts`, `frontend/app/admin/platform/staff/messages.ts`,
`docs/implementation-notes/AA-1091-cis.md`. Decisions: root ADR 0005, 0005b and 0019. Keep
[booking-price-setup.vi.md](booking-price-setup.vi.md) in step with this page.
