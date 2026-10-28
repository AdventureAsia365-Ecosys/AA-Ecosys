---
id: APP-10-booking-figma-audit
title: "AA-Booking Figma visual audit: 120 frames vs live Dev (S254)"
description: "Scores every exported Figma frame of the AA-Booking design against the live Dev staff app (1440 px, light), lists the real deviations with file-level fixes and groups them into five PR-sized slices."
type: report
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-booking]
last_reviewed: 2026-10-28
review_every_days: 180
related: [AA-996]
---

# AA-Booking Figma visual audit: 120 frames vs live Dev (S254)

Agent: Claude Code (read-only reviewer). Date: 28/10/2026. Inputs: the 120 Figma PNG exports in
`docs/AAA/figma_AAA/`, the coverage matrix `apps/AA-Booking/docs/figma-coverage.md` (AA-996) and
`apps/AA-Booking/docs/ui-spec.md`. Evidence in this folder: `capture.json` (one row per frame: route, URL, status,
console/HTTP errors), `live/` (118 screenshots, named like the Figma file) and `scores.json` (the scored items below,
machine-readable).

## Result

**Overall score: 7.3 / 10** (mean of the 118 captured frames; median 7.0, range 5–9). Excluding the 8 frames whose low
score comes from the evidence rather than the product (wrong state captured, empty record; marked *evidence gap* in the
per-screen table), the mean is **7.4**.

| Dimension | Mean (118 frames) |
|---|---|
| Layout | 7.76 |
| Components | 7.43 |
| Content (data shown, copy, completeness) | 6.68 |
| Visual (tokens, type, spacing) | 7.73 |

Deviations recorded: **34 major**, **268 minor**, **180 intended** (agreed adaptations, not counted against the
score). Of the 34 majors, **25 are product gaps** and **9 are evidence gaps** (8 recapture items plus the
not-capturable `EDIT PAYMENT.png`).

Reading the numbers: no frame is below 5, and every Figma screen has a live answer (AA-996 coverage holds). The
design language matches; what drags the score down is **content** (6.68): placeholder thumbnails, empty commercial
columns, missing photos on CIS-backed pages, synthetic Dev records, and a few Booking-owned features that the spec
promises but are not built yet (trip-plan supplier + price matrix).

## Method

- **Design side:** the 120 PNG frames exported from the Figma file, one row each in `figma-coverage.md`.
- **Live side:** `https://booking.lumiguides.it.com` (Dev), Playwright Chromium, 1440 × 900, light theme, signed in
  once as the E2E staff user `e2e-booking`. Full-page screenshots for pages (capped at 4000 px); viewport-only for
  dialogs, drawers, the bell popover and menus. The login frame was shot in a separate signed-out context.
- **Read-only:** no confirm button was pressed. Dialogs were opened for the screenshot and closed with Escape or
  Cancel. The E2E account also gets 403 on every write. The saved session state and the discovery dump were deleted
  after the run.
- **Records:** SYNTHETIC Dev records were preferred (TC-000022 main case, TC-000010 inquiry, TC-000015 create invoice,
  TC-000007 V1 draft builder, TC-000022 V1 approved version and preview, INV-000004 cancel and record payment,
  INV-000003 paid invoice view, PMT-000007 void and payment detail, SVC-000002, HTL-000002, SUP-000002, CUS-000016,
  CUS-000010, a sellable trip plan, country VN, the staff page of the program owner).
- **Scoring:** each captured frame gets 0–10 on four dimensions (layout, components, content, visual) and an overall
  score. Deviations are tagged:
  - **intended**: an agreed adaptation from the coverage matrix or ui-spec (Activities → Services, no hard delete →
    deactivate / archive / void / cancel / not sellable, CIS-owned content shown read-only "From CIS" with
    "Edit in CIS ↗", CIS-owned accounts and passwords, kit tokens: pill uppercase buttons, soft-danger buttons, dark
    toast, Poppins, warm background, 0.75× density). Intended deviations do **not** lower the score.
  - **minor**: a visible gap that does not block the screen's job.
  - **major**: a missing Booking-owned feature the spec promises, a broken layout at 1440 px, or a frame whose
    evidence cannot be judged.
- **Not scored:** 2 frames (no screenshot). The overall score is the mean of the 118 captured frames.

## Score distribution

| Score band | Screens | Share |
|---|---|---|
| 9–10 | 21 | 18 % |
| 8–8.9 | 16 | 14 % |
| 7–7.9 | 46 | 39 % |
| 6–6.9 | 23 | 19 % |
| 5–5.9 | 12 | 10 % |
| < 5 | 0 | 0 % |

## Per module

Frames are grouped by the coverage module they answer (misfiled exports count where the live route sits:
`COUNTRY MANAGAMENT-2/-3` are the hotel list, `ADD NEW ACTIVITY-2` is the case edit drawer, `DELETE SUPPLIER` and
`DELETE USER` are archive customer, `DELETE USER-1` is deactivate supplier).

| Module | Frames | Captured | Mean | Min | Major | Minor | Intended |
|---|---|---|---|---|---|---|---|
| Shell (login, dashboard, notifications, settings, audit log) | 8 | 8 | 7.75 | 6.5 | 0 | 19 | 11 |
| Users: staff | 8 | 8 | 7.81 | 5.5 | 1 | 13 | 13 |
| Users: customers and inquiries | 15 | 15 | 7.33 | 5 | 2 | 27 | 20 |
| Trip cases and trip checks | 10 | 10 | 7.05 | 6 | 3 | 30 | 14 |
| Itinerary builder (proposals) | 7 | 7 | 6.79 | 5 | 3 | 17 | 10 |
| Templates (trip plans) | 17 | 17 | 6.65 | 5.5 | 15 | 40 | 24 |
| Geo (countries, destinations) | 14 | 14 | 7.46 | 6 | 3 | 30 | 23 |
| Activities (services) and hotels | 19 | 19 | 7.37 | 6 | 2 | 44 | 35 |
| Suppliers | 7 | 7 | 7.86 | 7 | 0 | 19 | 10 |
| Payments and invoices | 15 | 13 | 7.12 | 5 | 5 | 29 | 20 |

Weakest modules: **Templates (6.65)**, driven by the commercial drawer (no supplier, no price matrix) and the trip-plan
list default view, and **Itinerary builder (6.79)**, driven by the empty approved version used as evidence and the
quote-preview 403. Strongest: Suppliers (7.86), Users: staff (7.81), Shell (7.75). The destructive dialogs (all
"Delete …" frames) score 8.5–9 across modules: the shared `ConfirmDialog` matches the Figma layout.

## Top 15 real deviations

Ranked by severity × reach (how many frames show the gap and how central the screen is). Evidence-only issues are
listed separately under [Recapture list](#recapture-list). Paths are under `apps/AA-Booking/frontend/`.

| # | Deviation | Severity | Frames | Fix |
|---|---|---|---|---|
| 1 | Trip-plan commercial drawer has **no Supplier select and no price matrix**: only a single "price hint". ui-spec route map lists the commercial edit as "sellable, supplier, price matrix, trip style"; Figma has Supplier and Pricing cards. Inclusions / exclusions are not shown read-only either. | major | 6 (`CREATE NEW TEMPLATE*`, `EDIT TEMPLATE*`) | `app/(staff)/catalog/trip-plans/_parts/CommercialDrawer.tsx`: Supplier select (active suppliers, `trip_plans.supplier_id`), price-matrix row editor (season / validity × pax band × currency × amount) backed by `GET/PUT /booking/catalog/trip-plans/{source_id}/prices`, read-only Included / Not included `CisField`s. |
| 2 | **Trip-plan list looks empty** by default: Title A–Z over 892 CIS tours puts unsellable tours first, so Trip style and Price hint are "—" on every row; thumbnails are the broken-image glyph (`cover_photo_path` null on list rows); Days is a bare number; subtitle "No SKU". | major | 7 (`TEMPLATE MANAGEMENT*`, `TRIP PLAN TEMPLATES*`, `TRIP TEMPLATES*`, `UNPUBLISH TEMPLATE`) | `catalog/trip-plans/_parts/TripPlansView.tsx`: sellable first by default, `N days / N-1 nights`, destinations (fallback short CIS id) as subtitle, row menu "Edit commercial" + "Edit in CIS ↗"; list API returns the cover photo; `ui/booking/CisPhoto.tsx` neutral fallback tile instead of `ImageOff`. |
| 3 | **No CIS photos on country pages**: cards are text-only, the detail page has no hero or gallery, drawers show only a count. Image counts look wrong (VN 106 places / 0, JP 530 / 0, IN 1628 / 0 vs BT 288 / 157). | major | 8 (`COUNTRY MANAGAMENT`, `-1`, `COUNTRY DETAILS`, `-1`, `ADD/EDIT COUNTRY`, `DELETE COUNTRY`, `UNPUBLISHED COUNTRY`) | Geo API: `cover_image_url` + first page of photo paths per country, and verify the photo aggregate. `catalog/countries/_parts/CountriesView.tsx` card cover + count chip; `CountryDetailView.tsx` hero + "Photos · From CIS" grid with lightbox; `catalog/_parts/GeoDrawers.tsx` thumbnail strip. |
| 4 | **Dates drift from en-GB.** Native `<input type=date>` shows `mm/dd/yyyy` / `10/28/2026` (FilterBar date ranges, case edit drawer, new case, record payment, send proposal, trip-check drawer, use-for-trip-case, audit log); time inputs are 12 h. Formatted text also drifts: `Sent 27/10/2026`, ISO `next due 2026-11-06`, ISO `since 2026-10-01` KPI hints, ISO dates in notifications. | minor | 20+ | One en-GB `DateField` / 24 h `TimeField` in `ui/booking` used by `FilterBar.tsx` (lines ~120–128) and every form above; `formatDate` in `billing/_parts/InvoiceView.tsx` (~206, ~255), billing KPI hints, `SupplierBills.tsx`; backend notification templates format dates en-GB. Run audits with locale `en-GB`. |
| 5 | **Billing invoice table wraps codes and dates mid-value** (`INV-` / `000004`, `TC-` / `000023`), rows look broken on the main money list. | major | 2 (`PAYMENT & INVOICE`, `-1`) | `app/(staff)/billing/page.tsx` `INVOICE_COLUMNS`: `whitespace-nowrap` + `font-mono` on number, case, issued and next-due cells; customer column absorbs truncation. |
| 6 | **Case Overview hierarchy is inverted**: main column holds only an empty "Trip legs" card; trip facts sit in a narrow right rail. Header lacks customer, agent and date range / duration on every case tab. | major | 4 (`TRIP CASES DETAILS*`, `Assigned Trips-1`) | `app/(staff)/cases/[code]/page.tsx`: Trip details as a two-column grid in the main column with Edit pencil, duration / end date, destinations, approved total; collapse empty legs to one line; header meta adds customer, sales owner, `start – end (N days)`; `pax_children ?? 0`. |
| 7 | **Case Proposals tab has no row actions** (Figma: preview, send, delete). Rows only open by click. | major | 1 (`TRIP CASES DETAILS-1`) | `app/(staff)/cases/[code]/ProposalsTab.tsx`: actions column with Preview, Send to customer (`SendProposalModal`) for unsent drafts, Discard draft via `ConfirmDialog`. |
| 8 | **Trip checks table overflows at 1440 px**: Status column clipped at the card edge (`STAT`, `• O`). No status tabs, no per-trip progress, no CSV. | major | 1 (`TRIP CHECKS`) + drawer context gap on `View Details-3` | `app/(staff)/trip-checks/page.tsx`: lower `tableMinWidth` (980), truncate Check / Customer, keep Status visible; SavedTabs Open / Overdue / Done; progress bar from `v_trip_check_board`; `_parts/CheckDrawer.tsx` context strip + "n of m checks done" link. |
| 9 | **Export CSV missing** on Services, Hotels, Suppliers, Countries, Payments, Invoices, Proposals, Trip checks and the case Proposals tab, while Cases, Customers, Staff, Destinations, Trip plans and Audit log have it. | minor | ~22 | `enableCsv` + `csvFilename` on the `DataTable` in `services/_parts/ServicesView.tsx`, `hotels/_parts/HotelsView.tsx`, `suppliers/_parts/SuppliersListView.tsx`, `billing/page.tsx` (both tabs), `proposals/page.tsx`, `trip-checks/page.tsx`, `cases/[code]/ProposalsTab.tsx`; `ui/csv.ts` for the countries grid. |
| 10 | **Filter bars wrap and tools float**: Sort / Status drop alone onto a second row (trip plans, cases); Columns / CSV sit on their own row under the filters (customers); Reset filters missing on hotels, destinations, payments, suppliers, notifications. | minor | ~16 | `ui/booking/FilterBar.tsx`: search `flex-1` with selects on one row at ≥ 1280 px, a trailing slot for the DataTable Columns / CSV tools, a Reset filters link whenever a filter is non-default. |
| 11 | **Draft builder quote fails**: `POST /api/booking/pricing/quote-preview` returned 403, so the price panel never shows a total. The E2E account's read-only guard blocks every POST, so this may be audit-only; real A / S roles must be checked. | major (verify) | 1 (`ITINERARY BUILDER-3`) | Check the BFF route `app/api/booking/pricing/quote-preview` and the API permission. If real roles get 403: grant quote to version editors (ui-spec §4.8). Either way, show a clear "no permission to quote" state in `cases/[code]/proposals/[n]/page.tsx` instead of failing silently. |
| 12 | **Approved version with zero items** carries a total of 2,400.00 USD; the locked price panel still says "No quote yet", the preview says "Valid for 14 days once sent". | minor (data rule) | 3 (`ITINERARY BUILDER-4`, `ITINERARY PREVIEW`, `TRIP CASES DETAILS-1`) | Block approval of a version with no items in the approve flow; in `proposals/[n]/page.tsx` and `preview/page.tsx` show the saved total / FX lock / approved date when locked. |
| 13 | **Invoice detail is thinner than the design**: no Subtotal / Tax / Total due footer, no Issue date / Due date pair, no Download PDF, a Columns button and pager on a one-line table drawn outside the card padding, `2400.00 USD overdue` unformatted, placeholder issuer text. Payment detail has no Customer / Related trip column. | minor | 5 (`View Details*`, `TRIP CASES DETAILS-2`, `PAYMENT DETAILS`) | `billing/_parts/InvoiceView.tsx`: totals footer, dates pair, money formatter on the overdue hint, hide pager / column tools for short lists, padded toolbar; PDF or a ui-spec "deferred" note; issuer legal name + address in Booking settings; `billing/payments/[ref]/page.tsx` two-column layout with Customer and Trip case cards. |
| 14 | **Hotels list is a table, not the spec'd photo grid** ("/hotels: Hotel grid"); hotel drawers lack updated-at / by, a large photo preview, and a consistent action placement; links are a `Label \| URL` textarea instead of a row repeater; no From CIS block in the hotel form. | major | 7 (`HOTEL MANAGEMENT`, `COUNTRY MANAGAMENT-2/-3`, `HOTEL DETAILS`, `EDIT HOTEL*`, `ADD NEW HOTEL`) | `hotels/_parts/HotelsView.tsx` grid / table toggle (first supplier photo or placeholder, count badge, place chip, updated); `HotelDrawer.tsx` header meta + photo strip; `HotelFormDrawer.tsx` links repeater, Deactivate in footer, From CIS customer-text block. |
| 15 | **Notifications are hard to read**: raw type keys (`invoice.overdue`, `trip_check.due`) that the Type filter cannot select, one bell icon for every type, raw tour UUIDs, no "Open invoice" action; popover cuts the last item without a fade. Inquiry panel also ignores the snapshot message / budget / travel style, and Countries is "—" despite a leg. | minor | 5 (`NOTIFICATION`, `OVERVIEW-1`, `USER DETAILS-3/-4/-5`) | `ui/booking/notifications.ts` labels + `notificationTarget()` invoice branch; `NotificationItem.tsx` `TYPE_ICON` + `CODE_RE`; `NotificationPopover.tsx` line clamp / fade; `cases/[code]/page.tsx` `Overview()` snapshot readers; API derives `countries` from legs. |

Smaller items worth folding into the slices: staff Deactivate lacks the optional audited reason that spec §4.13 asks
for (`staff/_parts/useStaffActions.tsx`); audit-log badge tones do not follow ui-spec §1.3 and there is no search;
Convert / Decline inquiry dialogs render their buttons in the body instead of the Modal `footer`; the dashboard has 5
KPI tiles in a 4-column grid and lacks Open trip cases / Outstanding balance / Active suppliers; customer names are cut
at 220 px (`customers/page.tsx` `PersonCell`); Services row menu lacks Edit and Duplicate; service and add-service
drawers have no section headings; destinations default sort opens on photo-less noise places (use `-photos`) and the
actions column header is blank; Settings copy leaks internals (`booking.settings`, "to confirm with Ms. Thu").

## Not capturable

| Figma file | Reason | Next step |
|---|---|---|
| `EDIT PAYMENT.png` | Every Dev payment is verified (PMT-000007) or voided (PMT-000005, PMT-000008); the API returns `actions.edit=false`, so the Edit button never renders. | The orchestrator records one unverified payment on a synthetic case, then recapture. Figma "Delete Payment" should appear as Void. |
| `SEND REMAINDER.png` | No reminder dialog exists: the invoice Remind button posts `invoices/{n}/remind` at once (`billing/_parts/InvoiceView.tsx` L231), so opening it would send. The frame duplicates CANCEL INVOICE (captured). | Decide: add a confirm dialog before Remind (matches Figma, avoids accidental mails) or record "no dialog, direct send" in `figma-coverage.md`, whose route column currently claims a dialog. |

## Recapture list

The 8 *evidence gap* frames and a few others need a second capture pass (no code change) before their scores are final:

- **Wrong state or element:** `USER MANAGEMENT-1` ↔ `-2` tabs swapped (map to `?tab=active` / `?tab=lead`);
  `USER MANAGEMENT-4` opened the account menu, click `button[aria-label^="Actions for"]` in the first row;
  `PAYMENT & INVOICE-1` → `/billing?tab=payments`, `-2` → invoices with a row menu, `-3` → payments (not supplier
  bills); `View Details.png` must use a fully paid invoice (it captured overdue INV-000004);
  `USER DETAILS-4` needs an existing cancelled TripPlanner case (never decline one for the audit).
- **Menus not opened:** `ACTIVITY MANAGEMENT-1`, `TRIP PLAN TEMPLATES-1` (open the first row's RowMenu, then Escape).
- **Empty or synthetic records:** `Assigned Trips` (staff with open assignments), `EDIT HOTEL-1` / `HOTEL DETAILS` /
  `EDIT HOTEL` (populated hotel, e.g. HTL-000001), `ITINERARY BUILDER-4` / `ITINERARY PREVIEW` (approved version with
  items from a CIS tour), `ACTIVITY DETAILS*` (SVC-000001 / 000003), `EDIT COUNTRY` (`?edit=BT`), destination
  drawers (a place with CIS photos), `Activity Log` (staff with many audit rows), `USER MANAGEMENT-3` (one completed
  case), supplier pages (SUP-000001).
- **Cut by the viewport or inner scroller:** `ADD SUPPLIER`, `CREATE NEW TEMPLATE*` drawer, `ITINERARY BUILDER-3`,
  `NOTIFICATION`, `RESET PASSWORD`, `TRIP TEMPLATE DETAILS*`: take element or scrolled screenshots of the main
  scroller.
- **Toasts** (`ACTIVITY MANAGEMENT-2`, `EDIT ACTIVITY`, `DESTINATION MANAGEMENT-1`, supplier and template list
  variants): only appear after a save. Either capture after a save on a synthetic record by the orchestrator, or record
  them as not capturable in the manifest.
- A Dev demo seed (complete service, hotel, supplier, customer with phone and address, a plan-based case, a completed
  case, a supplier bill) would remove most of the content penalty on the next audit.

Coverage matrix corrections found by the run: the hotel drawer opens with `?hotel=<code>` (not `?view=` / `?edit=`);
there is no `?new=1` (Add hotel and Edit hotel open from the button and the row menu); the `ADD NEW HOTEL` note is
empty although description and photos are deliberately CIS-owned; the staff action label is "Manage staff & invites in
CIS ↗", not "Invite staff in CIS ↗".

## Next fixes: five PR-sized slices

All in AA-Booking (`frontend/` unless stated). Slices 1, 4 and 5 are frontend-only or nearly so; slices 2 and 3 touch
the API, and slice 2 may need a `bk-` migration (review before merge per the risky-PR rule).

1. **Shared list and date primitives** (frontend, `ui/booking`): en-GB `DateField` and 24 h `TimeField` replacing
   native inputs everywhere (item 4); `formatDate` / money formatting in InvoiceView, KPI hints, SupplierBills;
   `FilterBar` one-row layout + trailing tools slot + Reset filters (item 10); Export CSV on the 8 lists (item 9);
   billing table `nowrap` codes (item 5); trip-checks table width (item 8, first half); Destinations Actions header;
   customers `PersonCell` width. Touches roughly 40 frames.
2. **Trip-plan commercial and list** (API + frontend): Supplier select and price matrix with `…/prices` endpoints
   (item 1); read-only inclusions / exclusions; list default sellable-first, cover photo on list rows, days format,
   destinations subtitle, row-menu Edit commercial / Edit in CIS (item 2). Also wire "Trip plan" into `/cases/new`
   and the Convert inquiry dialog now that W2 plans are live. Targets the Templates module (17 frames).
3. **CIS photos on catalog and supply** (API + frontend): country `cover_image_url` + photo paths and a checked
   photo aggregate; country cards, detail gallery, drawer strips; destination drawer thumbnails; `CisPhoto` neutral
   fallback; hotels grid / table toggle and hotel drawer photo strip (items 3, 14). Targets Geo and Hotels.
4. **Case workspace and proposals**: Overview hierarchy + header meta (item 6); Proposals tab actions (item 7); locked
   version price panel and preview copy, block approval of zero-item versions (item 12); quote-preview 403 handling
   (item 11, after the role check); inquiry snapshot fields + countries from legs (item 15, second half); trip-check
   tabs, progress and drawer context (item 8, second half); Convert / Decline dialogs use the Modal footer.
5. **Billing detail, notifications and staff**: invoice totals footer, dates pair, short-list table, PDF or deferral
   note, issuer settings; payment detail two-column layout, payments row actions and customer subline (item 13);
   notification labels, icons, invoice target and en-GB templates (item 15, first half); staff Deactivate reason;
   audit-log tones and search; Settings copy clean-up; the Remind confirm decision.

Spec decisions to record in `ui-spec.md` / `figma-coverage.md` alongside these slices (build or drop, so the next
audit stops flagging them): row-selection checkboxes and bulk actions on lists, the service Intensity field, destination
Description and Address, invoice Download PDF, period ("Last 30 days") filters on lists, itinerary period slots
(morning / afternoon / evening) now that typed items have landed.

## Per screen

Score `n/c` = not captured. L / C / Ct / V = layout / components / content / visual. "Top deviation" is the first
major, else the first minor, else the first intended deviation of the row; the full list per row is in `scores.json`.

| # | Figma file | Module | Live route / dialog | Score | L / C / Ct / V | Top deviation |
|---|---|---|---|---|---|---|
| 1 | `Group 1410084962.png` | Shell | `/login` (background) | 8.5 | 9 / 9 / 9 / 7 | **minor**: Background gradient is much paler than Figma: Figma has a saturated dark-gold top-right corner and gold glow bottom-left/right; live is a faint cream wash on warm bg. |
| 2 | `OVERVIEW.png` | Shell | / Dashboard | 7 | 7 / 8 / 6 / 7 | **minor**: The KPI row lacks the spec's 'Open trip cases' tile with its month-over-month delta (W1), and the Figma's money tile ('Pending $…') and 'Active suppliers' tile. … |
| 3 | `OVERVIEW-1.png` | Shell | / (topbar bell popover open) | 7.5 | 8 / 7 / 7 / 7 | **minor**: All popover items use the same bell icon. The Figma varies the icon by type (trip, payment, avatar, alert). |
| 4 | `NOTIFICATION.png` | Shell | /notifications | 6.5 | 8 / 6 / 6 / 6 | **minor**: Type chips show raw keys 'invoice.overdue' and 'trip_check.due', while other types show human labels ('Tour withdrawn'). … |
| 5 | `SETTINGS.png` | Shell | /settings?tab=general | 8 | 9 / 8 / 7 / 9 | **minor**: 'CIS role' field shows an empty '—' for the signed-in staff user |
| 6 | `SETTINGS-1.png` | Shell | /settings?tab=notifications | 8 | 9 / 8 / 7 / 9 | **minor**: Three preference rows (Tour withdrawn, Tour back in catalog, B2B on request) have no help line while the first four do, so rows look inconsistent |
| 7 | `SETTINGS-2.png` | Shell | /settings?tab=security | 9 | 9 / 9 / 9 / 9 | **intended**: Change-password form replaced by read-only sign-in facts (company e-mail code, MFA, session times, access) and CIS staff/invite pointer … |
| 8 | `AUDIT LOGS.png` | Shell | /audit-log | 7.5 | 7 / 8 / 8 / 8 | **minor**: The Figma 'Search description, action…' box is missing (acknowledged in AuditLogView.tsx: no API yet). |
| 9 | `ADMINS.png` | Users: staff | /staff | 8.5 | 9 / 8 / 8 / 9 | **minor**: Several rows (e2e-claude-code, admin, e2e-claude-code-2) show no e-mail under the name, while the Figma always shows a second line. … |
| 10 | `USER.png` | Users: staff | /staff + "Invite staff in CIS ↗" action | 9 | 9 / 9 / 9 / 9 | **minor**: The page action label is 'Manage staff & invites in CIS ↗', but the coverage row names it 'Invite staff in CIS ↗'. … |
| 11 | `USER DETAILS.png` | Users: staff | /staff/[cisUserId] | 8.5 | 9 / 8 / 8 / 8.5 | **minor**: The 'Admin' role chip next to the name has almost no visible pill background on the warm page header, so it reads as plain text. Figma shows a grey chip. |
| 12 | `Activity Log.png` | Users: staff | /staff/[cisUserId]?tab=activity | 7 | 8 / 7 / 6 / 8 | **minor**: The Figma 'Last 30 Days', 'Status' and 'Sort by' filters above the activity list are missing, so a busy staff member's history cannot be narrowed. |
| 13 | `Assigned Trips.png` | Users: staff | /staff/[cisUserId]?tab=cases | 5.5 (evidence gap) | 8 / 6 / 3 / 8 | **major**: The table is in its empty state ('No open assignments'). None of the Figma columns or rows are evidenced: the chosen staff member has 0 assignments. |
| 14 | `BLOCK ADMIN.png` | Users: staff | Deactivate staff member dialog | 7.5 | 8 / 7 / 7 / 8 | **minor**: The Figma 'Blockage Reason' textarea is missing. Spec §4.13 says Deactivate has 'a confirm and an optional reason (audited)', but the dialog sends only {active:false}. |
| 15 | `EDIT PROFILE.png` | Users: staff | Staff role dialog (`/staff`) | 7.5 | 7 / 8 / 7 / 8 | **minor**: The drawer has no identity header (avatar, name, e-mail, Active/Inactive badge) – the user is named only inside a sentence … |
| 16 | `RESET PASSWORD.png` | Users: staff | /settings?tab=security | 9 | 9 / 9 / 9 / 9 | **minor**: The 'Manage staff & invites in CIS' link sits below the 900px fold and is cut off in the capture … |
| 17 | `USER MANAGEMENT.png` | Users: customers and inquiries | /customers (tabs All / Leads / Active / Past, row menu) | 7.5 | 8 / 7.5 / 7 / 7.5 | **minor**: No row checkboxes or header select-all, which Figma shows. Bulk selection is neither built nor dropped in the spec. |
| 18 | `USER MANAGEMENT-1.png` | Users: customers and inquiries | /customers (tabs All / Leads / Active / Past, row menu) | 7.5 | 8 / 7.5 / 7 / 7.5 | **minor**: Wrong capture state: the Figma frame shows the 'Active Traveler's' tab, but the live capture opened ?tab=lead (Leads). USER MANAGEMENT-2 has the opposite swap. |
| 19 | `USER MANAGEMENT-2.png` | Users: customers and inquiries | /customers (tabs All / Leads / Active / Past, row menu) | 7.5 | 8 / 7.5 / 7 / 7.5 | **minor**: Wrong capture state: the Figma frame is the 'Leads' tab, but the live capture shows ?tab=active (Active, 5 rows). It is swapped with USER MANAGEMENT-1. |
| 20 | `USER MANAGEMENT-3.png` | Users: customers and inquiries | /customers (tabs All / Leads / Active / Past, row menu) | 6.5 | 8 / 7 / 4 / 8 | **minor**: The Past clients tab is empty ('No past clients yet', count 0) because Dev has no completed trip case. … |
| 21 | `USER MANAGEMENT-4.png` | Users: customers and inquiries | /customers (tabs All / Leads / Active / Past, row menu) | 5 (evidence gap) | 8 / 5 / 4 / 7 | **major**: Wrong element captured: the Figma frame is the open row action menu (View Profile / Create Trip Case / Block Customer). … |
| 22 | `USER  DETAILS.png` | Users: customers and inquiries | /customers/[id] (Overview / Trip cases / Inquiries) | 8 | 9 / 9 / 7 / 8 | **minor**: The Recent activity items show raw machine text: 'invoice_sent -> payment_pending (automatic: payment PMT-000007 verified, script:aa682_s3_live_check)'. … |
| 23 | `USER  DETAILS-1.png` | Users: customers and inquiries | /customers/[id] (Overview / Trip cases / Inquiries) | 8 | 9 / 8 / 7 / 9 | **minor**: The location meta item is missing from the header because the customer's address is null. … |
| 24 | `USER  DETAILS-2.png` | Users: customers and inquiries | /customers/[id] (Overview / Trip cases / Inquiries) | 6 | 6 / 6 / 6 / 8 | **minor**: The inquiries are a card list, not the Figma table. The Est. travel dates and Party size fields are missing … |
| 25 | `USER  DETAILS-3.png` | Users: customers and inquiries | /cases/[code] inquiry panel | 7 | 8 / 8 / 5 / 8 | **minor**: No 'Client message & preferences' block and no Estimated budget, Travel style or travel-window fields. … |
| 26 | `USER  DETAILS-4.png` | Users: customers and inquiries | /cases/[code] inquiry panel | 5 (evidence gap) | 7 / 5 / 4 / 7 | **major**: Figma -4 is the DECLINED state: a red 'Declined' badge, a 'Reopen Inquiry' action and a red 'Declined reason' banner. … |
| 27 | `USER  DETAILS-5.png` | Users: customers and inquiries | /cases/[code] inquiry panel | 7 | 8 / 8 / 5 / 8 | **minor**: No client message/budget/travel style/travel dates block and no client location/lead source. Countries shows '—' although a leg exists. |
| 28 | `USER  DETAILS-6.png` | Users: customers and inquiries | Convert inquiry dialog (case workspace) | 8 | 8 / 7 / 8 / 8 | **minor**: The 'Link Trip Template (optional)' select is missing. It was deferred as W2, but trip plans are now live (catalog/trip-plans with UseForTripCaseModal). |
| 29 | `USER  DETAILS-7.png` | Users: customers and inquiries | Decline inquiry dialog (case workspace) | 9 | 9 / 8 / 9 / 9 | **minor**: The buttons are rendered inside the body without the footer band that ConfirmDialog/Figma use (same inconsistency as the Convert dialog). |
| 30 | `DELETE USER.png` | Users: customers and inquiries | Archive customer dialog | 9 | 9 / 9 / 9 / 9 | **minor**: Behind the dialog, the Phone and Location columns show '—' on every visible row (synthetic Dev customers have no phone or city) … |
| 31 | `DELETE SUPPLIER.png` | Users: customers and inquiries | Archive customer dialog | 9 | 9 / 9 / 9 / 9 | **intended**: The Figma 'Delete User' (permanent delete) is replaced by 'Archive customer' (soft delete; open inquiries cancelled; audit history kept). … |
| 32 | `TRIP CASES MANAGEMENT.png` | Trip cases and trip checks | /cases | 7.5 | 7 / 7.5 / 7.5 / 7.5 | **minor**: The 'Created' date-range inputs are native date fields that show 'mm/dd/yyyy' (US order), which contradicts the agreed en-GB dates. |
| 33 | `TRIP PLAN MANAGEMENT.png` | Trip cases and trip checks | /cases | 7.5 | 7 / 7.5 / 7.5 / 7.5 | **minor**: The 'Created' date-range inputs show native 'mm/dd/yyyy' (US order), not en-GB. |
| 34 | `TRIP CASES  DETAILS.png` | Trip cases and trip checks | /cases/[code] Overview | 6 | 5.5 / 6.5 / 5.5 / 7 | **major**: The hierarchy is inverted. The main column holds only an empty 'Trip legs' card ('A custom trip: no CIS tour is linked yet'), while the trip facts (status … |
| 35 | `TRIP CASES  DETAILS-1.png` | Trip cases and trip checks | /cases/[code]?tab=proposals | 6.5 | 7.5 / 6 / 6 / 7.5 | **major**: The Proposal versions table has no Actions column. The Figma row has Preview (eye), Delete and 'Send to Customer'. Live, a row can only be opened by clicking. |
| 36 | `TRIP CASES  DETAILS-2.png` | Trip cases and trip checks | /cases/[code]?tab=billing | 7 | 6.5 / 7.5 / 7.5 / 6.5 | **minor**: Dates are formatted in three ways on one card: 'Sent 27/10/2026' (numeric), 'next due 2026-11-06' (raw ISO), and the kit format elsewhere ('27 Oct 2026'). … |
| 37 | `Assigned Trips-1.png` | Trip cases and trip checks | /cases/[code] workspace layout | 8.5 | 9 / 9 / 8 / 8 | **minor**: The header shows only the start date ('6 Dec 2026'). The Figma shows the range plus duration ('Nov 12 - Nov 26 (14 Days)'). |
| 38 | `ADD NEW TRIP 8.png` | Trip cases and trip checks | /cases/new | 7.5 | 8 / 8 / 7 / 8 | **minor**: The Figma 'Trip Plan Template' select is missing. Spec §4.6 hid 'Start from trip plan' only until W2, and W2 trip plans are now live (/catalog/trip-plans). … |
| 39 | `ADD NEW ACTIVITY-2.png` | Trip cases and trip checks | Edit case details drawer (/cases/TC-000022) | 8 | 8 / 8 / 8 / 8 | **minor**: Native date input renders '12/06/2026' (US mm/dd/yyyy) while the page header shows '6 Dec 2026' (en-GB); ambiguous and inconsistent with the en-GB date rule. |
| 40 | `TRIP CHECKS.png` | Trip cases and trip checks | /trip-checks | 6 | 5 / 6.5 / 6.5 / 6 | **major**: The table overflows at 1440px: the Status column is clipped at the card edge (header 'STAT', pills cut to '• O') and needs a horizontal scroll inside the card. |
| 41 | `View Details-3.png` | Trip cases and trip checks | Trip check drawer | 6 | 7 / 6 / 5 / 7 | **minor**: The drawer has almost no trip context. Figma's header shows the customer, departure date, assigned agent, destination … |
| 42 | `ITINERARY BUILDER.png` | Itinerary builder | /proposals | 7 | 8 / 7 / 6 / 7 | **minor**: There is no Export CSV button. The Figma list shows Export CSV next to the primary action, and ui-spec does not drop it. |
| 43 | `ITINERARY BUILDER-1.png` | Itinerary builder | `/proposals` (+ row actions) | 7.5 | 8 / 8 / 7 / 7 | **minor**: Trip column shows 'Custom' and only a start date for most rows (no destination list, no end date/duration) where Figma shows destinations and 'Oct 12 - Oct 24 … |
| 44 | `ITINERARY BUILDER-2.png` | Itinerary builder | Send proposal dialog | 8 | 9 / 9 / 6 / 8 | **minor**: When the version and case have no title the summary title and the subject read the lowercase placeholder 'custom' ('Your Adventure Asia proposal: custom'). |
| 45 | `ITINERARY BUILDER-3.png` | Itinerary builder | /cases/TC-000007/proposals/1 (draft version builder) | 6.5 | 7 / 7 / 6 / 7 | **major**: The live quote call failed: POST /api/booking/pricing/quote-preview returned 403 during capture (capture.json errors). … |
| 46 | `ITINERARY BUILDER-4.png` | Itinerary builder | /cases/TC-000022/proposals/1 (approved version builder) | 5 (evidence gap) | 7 / 6 / 3 / 6 | **major**: The approved version has no items ('No items in this version') yet carries a saved total of 2,400.00 USD. The Figma shows a filled multi-day itinerary. … |
| 47 | `ITINERARY PREVIEW.png` | Itinerary builder | /cases/TC-000022/proposals/1/preview | 5 (evidence gap) | 7 / 6 / 3 / 6 | **major**: The preview shows 'This version has no days yet'. There are no day cards with title, hero photo, body or item lines, and Destinations is '—'. … |
| 48 | `DELETE ITINERARY BUILDER.png` | Itinerary builder | Delete draft version dialog | 8.5 | 9 / 9 / 9 / 8 | **minor**: In the Proposals list behind the dialog, the 'Updated' date-range filter shows the native US placeholder 'mm/dd/yyyy'. This conflicts with the agreed en-GB date format. |
| 49 | `TEMPLATE MANAGEMENT.png` | Templates | /catalog/trip-plans | 6.5 | 7 / 7 / 5.5 / 7 | **major**: The list looks empty. The default view (Title A–Z over all 892 CIS tours) shows unsellable tours … |
| 50 | `TEMPLATE MANAGEMENT-1.png` | Templates | /catalog/trip-plans | 7 | 7 / 8 / 5 / 7 | **minor**: Est. price and Trip style are '—' on every visible row because the default view lists not-for-sale tours A–Z; Figma shows priced, styled rows |
| 51 | `TRIP PLAN TEMPLATES.png` | Templates | /catalog/trip-plans | 6.5 | 7 / 7 / 5.5 / 7 | **major**: The visible rows have no Trip style, no Price hint and placeholder thumbnails, so the 'est. … |
| 52 | `TRIP PLAN TEMPLATES-1.png` | Templates | /catalog/trip-plans | 6 | 7 / 6 / 5 / 7 | **major**: The list content is mostly placeholders: unsellable tours sort first, so Trip style and Price hint are '—' on every row and the thumbnails show the no-image icon. |
| 53 | `TRIP TEMPLATES.png` | Templates | /catalog/trip-plans | 7 | 7 / 7 / 6 / 8 | **minor**: The Sort select wraps to a second filter row. |
| 54 | `TRIP TEMPLATES-1.png` | Templates | /catalog/trip-plans | 7 | 7 / 7 / 6 / 8 | **minor**: The Sort select wraps onto its own second row under the search box. It leaves one control on its own line and wastes vertical space before the table. |
| 55 | `TRIP TEMPLATE DETAILS.png` | Templates | /catalog/trip-plans/[sourceId] | 7.5 | 8 / 7.5 / 7 / 7.5 | **minor**: The header shows an initials avatar instead of the tour's cover thumbnail. |
| 56 | `TRIP TEMPLATE DETAILS-1.png` | Templates | Use trip plan for a trip case dialog | 7 | 7.5 / 7 / 6.5 / 7 | **minor**: The 'Internal Notes (Optional)' textarea is missing. Figma has it, and the spec endpoint POST /booking/catalog/trip-plans/{source_id}/trip-cases accepts notes. |
| 57 | `TRIP TEMPLATE DETAILS-2.png` | Templates | /catalog/trip-plans/[sourceId] | 7.5 | 8 / 7.5 / 7 / 7.5 | **minor**: The header shows an initials avatar ('BT') even though the tour has a cover photo. Figma shows the tour thumbnail. |
| 58 | `CREATE NEW TEMPLATE.png` | Templates | Commercial drawer (/catalog/trip-plans/[sourceId]/commercial) | 5.5 | 6 / 7 / 4 / 7 | **major**: The Supplier section is missing. |
| 59 | `CREATE NEW TEMPLATE-1.png` | Templates | Commercial drawer (/catalog/trip-plans/[sourceId]/commercial) | 5.5 | 6 / 7 / 4 / 7 | **major**: There is no Supplier section, although the Figma right column has a 'Supplier / Select supplier' card. Spec ui-spec line 227 lists supplier as part of commercial edit. … |
| 60 | `CREATE NEW TEMPLATE-2.png` | Templates | Commercial drawer (/catalog/trip-plans/[sourceId]/commercial) | 5.5 | 6 / 7 / 4 / 7 | **major**: The Supplier select card is missing (spec line 227 commercial edit includes supplier). |
| 61 | `EDIT TEMPLATE.png` | Templates | Commercial drawer (`/catalog/trip-plans/[sourceId]/commercial`) | 5.5 | 5 / 6 / 5 / 7 | **major**: Supplier field missing (Figma Supplier card; spec lists supplier as a commercial field). |
| 62 | `EDIT TEMPLATE-1.png` | Templates | Commercial drawer (`/catalog/trip-plans/[sourceId]/commercial`) | 5.5 | 5 / 6 / 5 / 7 | **major**: No Supplier field: ui-spec route map lists the commercial edit as 'sellable, supplier, price matrix, trip style', and Figma has a 'Supplier / Select Supplier' card … |
| 63 | `EDIT TEMPLATE-2.png` | Templates | Commercial drawer (`/catalog/trip-plans/[sourceId]/commercial`) | 5.5 | 5 / 6 / 5 / 7 | **major**: Supplier field missing from the commercial edit (spec: sellable, supplier, price matrix, trip style). |
| 64 | `DELETE TRIP.png` | Templates | Make not sellable dialog (`/catalog/trip-plans`, trip plan detail) | 9 | 9 / 9 / 9 / 9 | **intended**: 'Delete Trip' is replaced by 'Make not sellable': the tour stays in CIS and existing cases keep their proposals. The dialog body explains this clearly. |
| 65 | `UNPUBLISH TEMPLATE.png` | Templates | Make not sellable dialog | 9 | 8 / 9 / 9 / 9 | **minor**: In the background list the Sort select still wraps to a second row (same as the list rows). |
| 66 | `COUNTRY MANAGAMENT.png` | Geo | /catalog/countries | 7 | 8 / 7 / 7 / 6 | **minor**: The Figma cards lead with a large cover photo and a photo-count badge. … |
| 67 | `COUNTRY MANAGAMENT-1.png` | Geo | /catalog/countries | 6.5 | 8 / 7 / 7 / 5 | **major**: The cards have no cover photo or image-count overlay. The Figma card is photo-led … |
| 68 | `COUNTRY DETAILS.png` | Geo | /catalog/countries/[iso] | 6 | 7 / 6 / 5 / 6 | **major**: The 'Media' block (hero + thumbnail strip + 'View all N images') is missing. Nothing renders CIS photos on the country page. |
| 69 | `COUNTRY DETAILS-1.png` | Geo | /catalog/countries/[iso] | 6 | 7 / 6 / 5 / 6 | **major**: There is no hero image and no 'Destination Images' gallery. The page renders only an 'Images' KPI, and CountryDetailView.tsx has no photo rendering at all … |
| 70 | `ADD COUNTRY.png` | Geo | Country profile drawer (/catalog/countries?edit=VN) | 8 | 8 / 8 / 7 / 9 | **minor**: 'Images: 0 place photos' for Vietnam while the CIS block is otherwise populated; Figma media area has no visual equivalent (no thumbnails/preview of CIS photos). |
| 71 | `EDIT COUNTRY.png` | Geo | Country profile drawer (`/catalog/countries`, `/catalog/countries/[iso]`) | 8 | 8 / 8 / 7 / 8 | **minor**: Media is shown only as a count ('0 place photos'), with no thumbnails. The Figma MEDIA section shows an image strip. … |
| 72 | `DELETE COUNTRY.png` | Geo | Deactivate country dialog | 9 | 9 / 9 / 9 / 9 | **intended**: Permanent delete becomes 'Deactivate country' (Booking status → inactive). The text explains that CIS content, cases and suppliers are kept. … |
| 73 | `UNPUBLISHED COUNTRY.png` | Geo | Deactivate country dialog | 9 | 9 / 9 / 9 / 8 | **minor**: The country cards behind the dialog have no hero photo or image-count overlay, which Figma shows. They are text-only stat cards even where Images > 0 (e.g. China 389). |
| 74 | `DESTINATION MANAGEMENT.png` | Geo | `/catalog/destinations` | 7 | 8 / 7 / 6 / 8 | **minor**: The default sort, Name A–Z, opens on near-duplicate CIS noise places ('100 Waterfalls' ×4) with no photos and '0 files' … |
| 75 | `DESTINATION MANAGEMENT-1.png` | Geo | `/catalog/destinations` | 7 | 8 / 7 / 6 / 8 | **minor**: The Figma frame shows the 'Destination Saved Successfully' toast. … |
| 76 | `DESTINATION DETAILS.png` | Geo | Destination drawer (view) | 7 | 8 / 7 / 6 / 8 | **minor**: The Figma GEOGRAPHY section has an embedded map preview with a pin. The live drawer only has a coordinate link, so there is no map. |
| 77 | `ADD DESTINATION.png` | Geo | Destination profile drawer (edit) (/catalog/destinations?place=...&edit=1) | 8 | 9 / 9 / 7 / 9 | **minor**: Figma 'Description (optional)' field has no live counterpart, not even read-only, and the coverage note does not list it. |
| 78 | `EDIT DESTINATION.png` | Geo | Destination profile drawer (edit) | 7 | 8 / 7 / 6 / 8 | **minor**: The Figma Address field is missing; the read-only CIS fieldset shows no address. |
| 79 | `DELETE DESTINATION.png` | Geo | Deactivate destination dialog | 9 | 9 / 9 / 9 / 9 | **minor**: In the background list, every destination row shows a placeholder thumbnail and '0 files' (the Figma rows show photos and file counts). … |
| 80 | `ACTIVITY MANAGEMENT.png` | Activities | /services | 7 | 8 / 7 / 5 / 8 | **minor**: Export CSV button shown in Figma is missing, while other Booking lists (cases, customers, staff, destinations, trip plans, audit log) have it - inconsistent. |
| 81 | `ACTIVITY MANAGEMENT-1.png` | Activities | /services (row menu open) | 6 | 8 / 6 / 5 / 8 | **minor**: The Figma frame shows the row action menu open (View Details, Edit Activity, Duplicate, Unpublish, Delete) … |
| 82 | `ACTIVITY MANAGEMENT-2.png` | Activities | /services (success toast) | 7 | 8 / 7 / 5 / 8 | **minor**: List body same as ACTIVITY MANAGEMENT: Export CSV missing, no thumbnails/checkboxes, synthetic data. |
| 83 | `ACTIVITY  DETAILS.png` | Activities | /services/[id] (SVC-000002) | 7 | 8 / 8 / 5 / 8 | **minor**: Captured record is synthetic and almost empty: City/place, Country, Max group size, Duration, Inclusions, CIS catalog reference all '—', customer content 'Not drafted' … |
| 84 | `ACTIVITY  DETAILS-1.png` | Activities | Deactivate service dialog (/services/SVC-000002) | 9 | 9 / 9 / 9 / 9 | **minor**: Underlying page is a synthetic record (SYNTHETIC S248 Activity) with most facts '—', so the backdrop does not show the Figma-like populated detail page. |
| 85 | `ACTIVITY  DETAILS-2.png` | Activities | Deactivate service dialog (/services/SVC-000002) | 9 | 9 / 9 / 9 / 9 | **minor**: Same live PNG as ACTIVITY DETAILS-1 (identical file hash) on a sparse synthetic record … |
| 86 | `ADD NEW ACTIVITY.png` | Activities | Add service drawer (/services) | 7 | 7 / 7 / 7 / 8 | **minor**: No section headings (Figma: General information / Location details / Media) - one flat field list, inconsistent with the sectioned case drawer. |
| 87 | `ADD NEW ACTIVITY-1.png` | Activities | Edit service drawer (/services/SVC-000002) | 7 | 7 / 7 / 6 / 8 | **minor**: The From CIS block has no 'Edit in CIS ↗' link for this record: CisContentBlock only passes editPath when content.edit_url exists … |
| 88 | `EDIT ACTIVITY.png` | Activities | `/services` | 7 | 8 / 7 / 6 / 8 | **minor**: The frame shows the 'Activity updated successfully' toast after an edit. … |
| 89 | `DELETE ACTIVITY.png` | Activities | Deactivate service dialog | 9 | 9 / 9 / 9 / 9 | **intended**: 'Delete Activity … cannot be undone' becomes 'Deactivate service': the record stays with its rates and history. … |
| 90 | `UNPUBLISH ACTIVITY.png` | Activities | Deactivate service dialog | 9 | 9 / 9 / 9 / 9 | **intended**: 'Unpublish Activity' becomes 'Deactivate service' (replaced-by row). The copy explains the soft deactivate and an optional Reason field is added. |
| 91 | `HOTEL MANAGEMENT.png` | Activities | `/hotels` | 6.5 | 5 / 7 / 7 / 7 | **major**: Figma and ui-spec route map ('/hotels \| Hotel grid', §FE 'Hotels (grid + drawer)') call for a photo card grid (image, image count badge, 'City, Country' pin chip, name … |
| 92 | `COUNTRY MANAGAMENT-2.png` | Activities | /hotels | 7.5 | 7 / 7 / 8 / 8 | **minor**: The Figma 'Export CSV' button is missing. Other Booking lists (destinations, trip plans) have CSV export, but Hotels does not. |
| 93 | `COUNTRY MANAGAMENT-3.png` | Activities | /hotels | 7.5 | 7 / 7 / 8 / 8 | **minor**: No Export CSV on the Hotels list. |
| 94 | `HOTEL DETAILS.png` | Activities | Hotel drawer (`/hotels?hotel=HTL-000002`) | 6 | 7 / 7 / 4 / 7 | **minor**: Captured hotel is an empty synthetic record: every fact is '—', no photos, CIS content 'Not drafted' … |
| 95 | `ADD NEW HOTEL.png` | Activities | Add hotel drawer (/hotels, Add hotel button) | 7 | 8 / 7 / 7 / 8 | **minor**: Figma 'Hotel Links' repeater (URL name + URL rows, delete icon … |
| 96 | `EDIT HOTEL.png` | Activities | `/hotels?edit=[id]` (Edit hotel drawer from row menu) | 6.5 | 7 / 7 / 5 / 7 | **minor**: No Deactivate action in the edit drawer footer: Figma puts the destructive action bottom-left of the edit form … |
| 97 | `EDIT HOTEL-1.png` | Activities | `/hotels?view=[id]` hotel drawer | 6 (evidence gap) | 7 / 7 / 4 / 7 | **major**: The captured hotel (HTL-000002, SYNTHETIC S248) has every fact empty: Style, Star rating, City/Place, Country, Street address, Geo point, Check-in/out … |
| 98 | `DELETE HOTEL.png` | Activities | Deactivate hotel dialog | 9 | 9 / 9 / 9 / 9 | **intended**: 'Delete Hotel … cannot be undone' becomes 'Deactivate hotel'. It keeps rates and history, blocks new proposal items, and has an optional reason. … |
| 99 | `SUPPLIER MANAGEMENT.png` | Suppliers | /suppliers | 7 | 8 / 6 / 7 / 8 | **minor**: Export CSV action missing |
| 100 | `SUPPLIER MANAGEMENT-1.png` | Suppliers | /suppliers | 7 | 8 / 6 / 7 / 8 | **minor**: Export CSV action missing |
| 101 | `SUPPLIER MANAGEMENT-2.png` | Suppliers | /suppliers | 7 | 8 / 6 / 7 / 8 | **minor**: Export CSV action missing |
| 102 | `SUPPLIER  DETAILS.png` | Suppliers | /suppliers/SUP-000002 | 7 | 9 / 7 / 5 / 8 | **minor**: Figma primary header action 'Add Activity' is missing; only Edit profile and Deactivate are offered |
| 103 | `ADD SUPPLIER.png` | Suppliers | /suppliers/new | 9 | 9 / 9 / 9 / 9 | **minor**: The capture is viewport-only, so the Location section (Street address, City, Country, State/province, Postal code … |
| 104 | `EDIT SUPPLIER.png` | Suppliers | `/suppliers/[id]/edit` | 9 | 9 / 9 / 9 / 9 | **minor**: Header 'Cancel' is a plain text link while Figma (and other Booking forms) use an outline button next to the primary action. |
| 105 | `DELETE USER-1.png` | Suppliers | Deactivate supplier dialog | 9 | 9 / 9 / 10 / 9 | **minor**: The supplier list behind the dialog has no 'Export CSV' action. Figma shows one, and Customers, Cases, Trip plans and Destinations all have one (DataTable enableCsv). |
| 106 | `PAYMENT & INVOICE.png` | Payments and invoices | /billing (Invoices tab) | 7 | 7 / 6 / 8 / 6 | **major**: Invoice and trip-case codes wrap mid-code ('INV-' / '000004', 'TC-' / '000023'), and the Issued and Next due dates wrap. This is a visual bug in the main table. |
| 107 | `PAYMENT & INVOICE-1.png` | Payments and invoices | /billing?tab=invoices | 6.5 | 7 / 6 / 7 / 6 | **major**: Codes wrap at the hyphen ('INV-' / '000004', 'TC-' / '000023'), and the Issued and Next due dates wrap onto two lines. Rows look broken and misaligned. |
| 108 | `PAYMENT & INVOICE-2.png` | Payments and invoices | /billing?tab=payments | 6.5 | 7 / 6 / 7 / 7 | **minor**: Capture mismatch: the Figma frame is the Invoices tab with the row '…' menu open (Send Reminder / Download PDF / Delete), but the live shot is the Payments tab. |
| 109 | `PAYMENT & INVOICE-3.png` | Payments and invoices | /billing?tab=supplier-bills | 5 (evidence gap) | 7 / 6 / 3 / 7 | **major**: Capture mismatch: the Figma frame is the Payment tab with the row menu open (Edit Payment / Download PDF / Delete), but the live shot is the Supplier bills tab … |
| 110 | `PAYMENT MANAGEMENt.png` | Payments and invoices | /billing?tab=payments | 7 | 8 / 6 / 7 / 8 | **minor**: Export CSV action missing from the payments table |
| 111 | `PAYMENT DETAILS.png` | Payments and invoices | /billing/payments/PMT-000007 | 6.5 | 6 / 7 / 6 / 7 | **minor**: The Figma's right column is missing: the 'Customer' card (name, email, phone, open link) and the 'Related trip' card (trip code, style, start date, total). … |
| 112 | `CREATE INVOICE.png` | Payments and invoices | Create invoice stepper (case Billing tab) | 7 | 6 / 8 / 7 / 7 | **minor**: Step 1 shows only one sentence about the locked approved line and leaves a large empty area in the modal. … |
| 113 | `CANCEL INVOICE.png` | Payments and invoices | Cancel invoice dialog | 9 | 9 / 9 / 9 / 9 | **minor**: On the backdrop invoice page the subtitle reads 'Sent 27/10/2026' (numeric). The rest of the app uses en-GB '27 Oct 2026'. |
| 114 | `RECORD PAYMENT.png` | Payments and invoices | Record payment dialog (/billing/invoices/INV-000004) | 8 | 9 / 8 / 8 / 8 | **minor**: Payment date field renders browser-locale US format '10/28/2026' instead of en-GB '28 Oct 2026' required by ui-spec 1.2 |
| 115 | `EDIT PAYMENT.png` | Payments and invoices | Edit payment dialog | n/c | – | **major**: Not capturable: every live payment (PMT-000005/7/8) is verified or voided, the API returns actions.edit=false … |
| 116 | `SEND REMAINDER.png` | Payments and invoices | Send reminder dialog | n/c | – | **intended**: Not capturable: no reminder dialog exists; the invoice 'Remind' button posts invoices/{n}/remind directly (InvoiceView.tsx L231), so opening it would send. … |
| 117 | `DELETE.png` | Payments and invoices | Void payment dialog | 9 | 9 / 9 / 10 / 9 | **intended**: 'Delete Payment' becomes 'Void PMT-…'. The payment is kept and audited, and a reason is required (the confirm button stays disabled until one is entered). |
| 118 | `View Details.png` | Payments and invoices | /billing/invoices/[number] | 6 (evidence gap) | 8 / 7 / 4 / 7 | **major**: Wrong state captured: the Figma frame is a 'Paid' invoice, but the capture opened INV-000004, which is Overdue (the same screenshot as View Details-2). … |
| 119 | `View Details-1.png` | Payments and invoices | /billing/invoices/[number] | 7.5 | 8 / 8 / 7 / 7 | **minor**: Dates do not use the kit en-GB format: 'Sent 27/10/2026' (numeric) and 'next due 2026-11-06' (raw ISO). The spec requires '27 Oct 2026'. |
| 120 | `View Details-2.png` | Payments and invoices | /billing/invoices/[number] | 7.5 | 8 / 8 / 7 / 7 | **minor**: The overdue hint shows an unformatted amount, '2400.00 USD overdue', next to '2,400.00 USD' in the same tile. |
