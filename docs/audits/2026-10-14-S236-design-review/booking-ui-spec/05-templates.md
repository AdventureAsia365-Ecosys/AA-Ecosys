# 05 — Trip Plan Templates (AA-Booking staff admin) — UI spec from Figma

Source: `docs/AAA/figma_AAA/` (17 PNGs, all read). Inputs cross-checked: ADR 0004 (O1, O6, O7, O8),
ADR 0005, ERD v2 `docs/AAA/erd-v2/booking.dbml`, `apps/AA-Booking/CONTEXT.md`.
Author: Claude Code (S236 figma-spec lane). Read-only extraction. Nothing in the repo was changed.

## Screens read

| File | What it shows |
|---|---|
| TRIP TEMPLATES.png | List + "Template Published Successfully" toast; row subtitle = destinations |
| TRIP TEMPLATES-1.png | Identical to TRIP TEMPLATES.png (duplicate export) |
| TRIP PLAN TEMPLATES.png | List, row subtitle = SKU `#TP-2024-0xx`, "Reset Filters" link visible |
| TRIP PLAN TEMPLATES-1.png | List with row action menu open (Preview / Edit Template / Unpublish / Delete) |
| TEMPLATE MANAGEMENT.png | List + "Template updated successfully" toast |
| TEMPLATE MANAGEMENT-1.png | Identical to TEMPLATE MANAGEMENT.png (duplicate export) |
| UNPUBLISH TEMPLATE.png | Unpublish confirm dialog over a list variant with tabs (All / Published / Drafts) and a Country filter. The copy was pasted from Activities/Users ("Unpublish Activity", "Everest Base Camp Trek", menu "Edit Profile / Block User / Delete User") |
| CREATE NEW TEMPLATE.png | Create form, empty itinerary ("Add Day") |
| CREATE NEW TEMPLATE-1.png | Create form with Day 1 expanded (Morning / Afternoon / empty Evening + "Add Activity") |
| CREATE NEW TEMPLATE-2.png | Identical to CREATE NEW TEMPLATE.png |
| EDIT TEMPLATE.png | Edit form, header actions Cancel / Save Changes / **Send to Customer** |
| EDIT TEMPLATE-1.png | Edit form, header actions Cancel / Save as Draft / Save Changes, Day 1 + Day 2 |
| EDIT TEMPLATE-2.png | Same as EDIT TEMPLATE-1, itinerary section cut off (empty area) |
| TRIP TEMPLATE DETAILS.png | Preview/detail page, header actions Unpublish / Edit Template / Use for Trip Case |
| TRIP TEMPLATE DETAILS-1.png | "Create Trip Case" modal over the detail page (header SKU shown as `ACT-2941`, copy-paste leftover) |
| TRIP TEMPLATE DETAILS-2.png | Detail page with no header actions (read-only variant, sidebar highlights "Trip Cases"). Probably the view a sales user reaches from a trip case |
| TRIP PLAN MANAGEMENT.png | **Not a template screen.** It is the Trip Cases list (title "Trip Cases Management"), belongs to module 06 (cases). Recorded here only for the "Linked Trip Template" column |

No image failed to load. Not in Figma: loading skeletons, empty-list state, validation error states,
the activity-slot editor (the pencil on each slot opens something that is not drawn), the "Delete
template" confirm dialog, and the CSV export format.

Global shell, same on every screen: left sidebar (Overview: Dashboard, Admins, End-users, Suppliers,
Audit Logs; Content & Inventory: Countries, Hotels, Destination, Trip Plan Templates, Activities,
Itinerary Builder, Trip Cases; Trip Operations & Sales: Payment & Invoice, Trip Checks, Settings),
the staff card at the bottom (name + role "Super Admin" + logout), and a top bar with page title,
notification bell, "Admin" label and avatar. Note: in most template mocks the sidebar highlights
"Countries" by mistake. The active item should be "Trip Plan Templates".

---

## Screen 1 — Trip Templates list

- **Route:** `/templates` (sidebar "Trip Plan Templates").
- **Purpose:** browse, filter and manage reusable trip templates (`booking.trip_plans`), the starting
  point for trip cases.
- **Layout:**
  1. Page header: H1 "Trip Templates" + subtitle "This module focuses on the creation and management
     of reusable trip templates, which serve as the foundation for customer trip cases."
  2. (Variant in UNPUBLISH TEMPLATE.png only) tabs **All Templates / Published / Drafts**.
  3. Card: toolbar row (search left; Export CSV + primary button right), filter row, table, footer pager.
- **Search:** text input "Search by name.." (the tab variant says "Search by name, email or phone…",
  a copy-paste error; use name + SKU).
- **Toolbar buttons:**
  - `Export CSV` (secondary, download icon). Exports the current filtered set.
  - `+ Create Trip Plan` (primary, orange), goes to `/templates/new`.
- **Filters (dropdowns):**
  - `Filter:` date range, default "Last 30 Days" (on created_at or updated_at; not specified, propose `updated_at`).
  - `Status:` "All Statuses" | Published | Draft (+ Unpublished, see decisions).
  - `Category:` "All Category" | trip style values.
  - (tab variant) `Country:` "All Countries".
  - `Reset Filters` text link (red), right-aligned, shown when a filter is not at its default.
- **Table columns:**

  | # | Header | Content | Notes |
  |---|---|---|---|
  | 0 | (checkbox) | Row select; header checkbox shows the indeterminate state | Bulk actions are not drawn. Selection is only used for Export? Propose bulk export only |
  | 1 | TEMPLATES NAME | Title (bold) + 2nd line: either destinations list ("Ubud, Seminyak, Nusa Penida") or SKU ("#TP-2024-089") | Two variants. Propose title + SKU, destinations as a tooltip, or both on the 2nd line |
  | 2 | DURATIONS | "10 Days / 9 Nights" | |
  | 3 | EST. PRICE | "$1,450" | "from" price; currency USD |
  | 4 | TRIP STYLE / CATEGORY | "Culture & Beach", "Highlights", "Beach & Relaxation", "Culture & Food", "Nature & Wildlife" | free label |
  | 5 | STATUS | badge | see badges |
  | 6 | ACTION | `…` kebab button | menu below |

- **Row action menu (kebab):** `Preview` (eye) goes to `/templates/[id]`; `Edit Template` (pencil) goes to
  `/templates/[id]/edit`; divider; `Unpublish` (eye-off) opens Unpublish dialog (only for Published; for
  Draft show `Publish`); divider; `Delete` (trash, red) opens a delete confirm (not drawn).
- **Status badges:** `Published` (green, dot), `Draft` (grey, dot). (Detail page also shows a
  separate `Active` badge, see below.)
- **Selected row:** highlighted cream background + orange checkbox.
- **Pager:** "Showing 1 to 5 of 124 results", "1 of 16 pages", `Prev` / `Next`.
- **Toasts (top-right, green border, closable ×):**
  - "Template Published Successfully" / "Template has been created and added to the catalog." (after Publish)
  - "Template updated successfully" / "Changes to {title} has been saved." (after Save Changes)
- **Empty/loading:** not drawn. Propose: table skeleton rows, and an empty state "No templates yet" + Create button;
  "No results" + Reset Filters when filters match nothing.

## Screen 2 — Unpublish confirm dialog

- **Route:** modal on `/templates` and `/templates/[id]`.
- **Content (corrected):** warning icon (red circle), title **"Unpublish Template"**, body "Are you sure
  you want to unpublish **{title}**? This will hide the template from all users and remove it from any
  active search results." Buttons: `Cancel` (secondary), `Unpublish Template` (red/destructive).
- Figma text says "Unpublish Activity" / "Everest Base Camp Trek" (copy from Activities). Treat it as a template.
- **Effect:** `trip_plans.is_published = false`. Existing trip cases that reference the template are not
  affected (they copied the itinerary into a version).

## Screen 3 — Create New Template

- **Route:** `/templates/new`.
- **Purpose:** author a template: general info, location, pricing, media, day-by-day itinerary,
  inclusions/exclusions, supplier.
- **Header bar:** back arrow, title "Create New Template"; buttons `Cancel` (ghost), `Save as Draft`
  (secondary), `✓ Publish Template` (primary).
- **Layout:** two columns. Left (main, wide): sections General Information, Location Details, Pricing,
  Media, Itinerary Builder. Right (narrow sidebar cards): Inclusions, Exclusions, Supplier.
- **Fields (no required markers or error states are drawn; requiredness below is proposed):**

  | Section | Field | Type | Placeholder / example | Required (proposed) |
  |---|---|---|---|---|
  | General | Template Name | text | "e.g., Everest Base Camp Trek" | yes (publish + draft) |
  | General | Status | select | "Select type..." (Draft / Published) | redundant with header buttons, see decisions |
  | General | Trip Style / Category | select | "Select type..." | yes to publish |
  | General | Description | textarea (focused, orange ring) | "provide a detailed description of the activity..." | yes to publish |
  | General | Start Date | date "YYYY - MM - DD" + calendar icon | | see decisions (templates have no dates in ERD) |
  | General | End Date | date | | same |
  | Location | Country | select | "Select country..." | yes |
  | Location | City | select (combobox) | "e.g., Kathmandu" | yes |
  | Location | Latitude (Geo-coordinate) | number text | "e.g., 27.7172" | ERD drops it |
  | Location | Longitude (Geo-coordinate) | number text | "e.g., 85.3240" | ERD drops it |
  | Pricing | repeatable row: Category | text | "Adult (12+ years)", "Enter Category" | ≥1 row to publish |
  | Pricing | repeatable row: Amount | money, "$" prefix | "Enter amount" | yes per row |
  | Pricing | row delete | trash icon button (red) | | |
  | Pricing | `+ Add` | adds a row | | |
  | Media | Thumbnail Image | dropzone "Click to upload or drag and drop", "SVG, PNG, JPG or GIF (max. 800x400px)" | | yes to publish (proposed) |
  | Media | Media Gallery | multi dropzone "Click to upload multiple images", "Upload up to 10 images" | | max 10 |
  | Itinerary | `Add Day` / `Add another Day` | button | | ≥1 day to publish |
  | Inclusions | list of text rows + trash; `+ Add` | text | "Accommodation (5-star resort)", "Meals", "Airport pickup", "Spa" | no |
  | Exclusions | list of text rows + trash; `+ Add` | text | "Local transport", "Personal expenses" | no |
  | Supplier | Select Supplier | select | "Bali Horizon Tours" | no (proposed) |

- **Itinerary Builder (CREATE NEW TEMPLATE-1):**
  - Day card: drag handle, "Day 1", sub-line date "Saturday, Oct 12, 2024", delete (trash), collapse (chevron).
  - Inside each day: time-slot cards **Morning / Afternoon / Evening** (sunrise / sun / moon icons),
    each with drag handle and pencil (edit). Slot content: duration ("1 hr", "1 hr 30 mins"), transport
    mode ("Flight", "Private Car", "Walking"), hotel ("Bali Premium Hotels & Suites"), note/description
    ("Welcome to Bali! After arriving at Ngurah Rai Airport, ..."). Empty slot shows "--- • ---".
  - `+ Add Activity` (dashed) inside the day; `Add another Day` below the last day.
  - Reorder: drag days and slots (handles drawn).
  - The slot editor (pencil) is not drawn. Assume a drawer/modal: pick activity (from catalog), hotel,
    period, transfer type, travel hours, note.
- **Actions:**
  - `Save as Draft` creates with `is_published=false`, stays on the edit page.
  - `Publish Template` validates the publish rules, sets `is_published=true`, goes back to the list with
    the "Template Published Successfully" toast.
  - `Cancel` / back arrow: leave (propose an unsaved-changes confirm).

## Screen 4 — Edit Template

- **Route:** `/templates/[id]/edit`.
- **Header:** back arrow, "Edit Template - {title}". Two variants:
  - EDIT TEMPLATE.png: `Cancel`, `Save Changes`, `Send to Customer` (primary).
  - EDIT TEMPLATE-1/-2: `Cancel`, `Save as Draft`, `Save Changes` (primary).
- **Fields:** same as Create, pre-filled. Example values: Status "Published", Trip Style "Culture & Beach",
  Start 2025-10-01, End 2025-10-10, Country "Indonesia", City "Bali", Lat 27.7172 / Lng 85.3240 (these are
  Kathmandu coordinates, mock data), Pricing rows Adult (12+ years) $1000, Child (4-11 yrs) $800,
  Infant (0-3 yrs) $150.
- **Media (filled state):** thumbnail preview with overlay `Change Image` button; hint "Recommended
  size: 1200x675px (16:9)" (contradicts the Create hint "max. 800x400px"); gallery thumbnails each with
  an `×` remove; `+ Add More` tile.
- **Itinerary:** Day 1 expanded (Morning/Afternoon/Evening filled), Day 2 collapsed, `Add another Day`.
- **Save Changes** goes back to the list with the toast "Template updated successfully".

## Screen 5 — Template detail / Preview

- **Route:** `/templates/[id]` (title bar "{title} - Preview").
- **Header block:** thumbnail, H1 title, meta row: `# TP-2024-089` (SKU), badge `Published` (green, check),
  badge `Active` (green dot), "Created At: Oct 12, 2023" (calendar icon).
- **Header actions:** `Unpublish` (eye-off, secondary), `Edit Template` (pencil, secondary),
  `Use for Trip Case` (primary, briefcase icon). DETAILS-2 shows no actions (read-only variant).
- **Main column cards:**
  - **Overview** (two-column key/value): Template Name, Status, Trip Style / Category, Duration,
    Description (full width), Country, City, Duration (duplicated), Destination ("Ubud, Seminyak, Nusa
    Penida"), Latitude, Longitude, Supplier.
  - **Media Gallery:** 3-up image grid.
  - **Itinerary:** accordion of days (Day N + date). Expanded day lists Morning/Afternoon/Evening slot
    cards (same content as the builder, read-only).
- **Right column cards:**
  - **Pricing Summary:** "Estimated Price (Per Person)" **$1,950** (orange, large) + disclaimer "*Prices
    are estimated and may vary based on travel dates, availability, and specific client customizations."
    (Note: list shows $1,450 for the same template. Mock inconsistency.)
  - **Inclusions:** green check list.
  - **Exclusions:** red × list.
- **Badges:** status `Published` / `Draft`; record `Active` / `Inactive`.

## Screen 6 — "Create Trip Case" modal (Use for Trip Case)

- **Route:** modal on `/templates/[id]`; on submit goes to `/cases/[code]`.
- **Title:** "Create Trip Case", subtitle `Using template "{title}"`.
- **Fields:**

  | Field | Type | Notes |
  |---|---|---|
  | Customer / Lead | text (should be a customer search combobox + "create lead") | required |
  | Start Date | date "Select Date" | required |
  | End Date (Figma typo "Edn Date") | read-only, grey, "Auto-calculated (10 Days)" | = start + duration_days - 1 |
  | Adults | number stepper, default 2 | required, ≥1 |
  | Children | number stepper, default 0 | ≥0 |
  | Internal Notes (Optional) | textarea | |

- **Buttons:** `Cancel`, `Create Trip Case` (primary).
- **Effect:** create `trip_cases` (status `new_inquiry`, trip_plan_id, dates, pax) + V1
  `trip_case_versions` with the itinerary copied from `trip_plan_itinerary`, dated from start_date.

## (Out of module) TRIP PLAN MANAGEMENT.png = Trip Cases list

Belongs to module 06. Relevant here only: column **LINKED TRIP TEMPLATE** shows template title + SKU
(`#TP-2024-089`), so `trip_plans.sku` must be human-readable and stable. Its status badges (Draft, In
Progress, Sent, Approved, Completed, Cancelled) do not match the ERD `trip_case_status` enum; module 06 handles that.

---

## Data mapping

Classes: **COMMERCIAL** = owned by Booking (ADR 0001/0005). **CONTENT** = owned by CIS (ADR 0002, ADR 0004
O7), read-only in Booking and read from CIS catalog views. **IDENTITY** = staff/customer.

### Template (list, form, detail)

| UI field | ERD table.column | Class | Note |
|---|---|---|---|
| Template Name | `trip_plans.title` | CONTENT when `source_system='cis'` (title of the CIS published tour); COMMERCIAL label only for `manual` | see C1 |
| SKU `#TP-2024-089` | `trip_plans.sku` | COMMERCIAL | format not defined; propose `TP-YYYY-NNN` |
| Slug | `trip_plans.slug` | COMMERCIAL (ERD) | not in UI |
| Description | `trip_plans.summary` | CONTENT | CIS owns tour copy (O7) |
| Status Published/Draft | `trip_plans.is_published` | COMMERCIAL | "is this template sellable" |
| Active badge | `trip_plans.status` (`record_status` active/inactive) | COMMERCIAL | |
| Trip Style / Category | `trip_plans.trip_style` (varchar) | COMMERCIAL (classification) | no lookup table/enum in ERD; missing a list of values |
| Duration "10 Days / 9 Nights" | `trip_plans.duration_days`, `duration_nights` | CONTENT when CIS-synced (derived from CIS day structure); COMMERCIAL for manual | |
| Start Date / End Date | **missing in ERD (deliberately)** | — | ERD note: "No start/end date: a template has a duration; dates belong to a trip case." |
| Country | derived: `trip_plan_destinations` → CIS `shared.destinations` → country | CONTENT | ERD has no single country_id (multi-country) |
| City | `trip_plan_destinations.destination_id` (CIS `shared.destinations.id`) | CONTENT (golden record, read-only) | UI is single city; ERD is ordered list |
| Destination list "Ubud, Seminyak, Nusa Penida" | `trip_plan_destinations` (position) → `shared.destinations.name` | CONTENT | |
| Latitude / Longitude | **missing in ERD (deliberately)** — from `shared.destinations` | CONTENT | ERD note "No lat/lng" |
| Supplier | `trip_plans.supplier_id` → `suppliers.company_name` | COMMERCIAL | |
| Inclusions | `trip_plans.what_it_has` (jsonb) | CONTENT (customer-facing copy) when CIS-synced; COMMERCIAL if it describes the commercial package | see C3 |
| Exclusions | `trip_plans.what_it_does_not_have` (jsonb) | same as above | |
| Pricing rows (Adult/Child/Infant + amount) | `trip_plan_prices` (season, valid_from/to, pax_min/max, price, currency) | COMMERCIAL | **mismatch**: ERD has no age-category column; it prices by pax band × season. See C4 |
| EST. PRICE / Estimated Price (Per Person) | `booking.v_from_prices` (ADR 0005 §6, view not yet in ERD) | COMMERCIAL | derived, never typed |
| Currency "$" | `trip_plan_prices.currency` | COMMERCIAL | UI hard-codes $ |
| Thumbnail Image | `entity_media` (entity_type `trip_plan`, position 0) → `media_files`; or CIS `shared.v_tour_photos` | CONTENT for CIS tours (photos from `v_tour_photos`); COMMERCIAL-owned upload only for manual | ERD has no `cover_media_id` on trip_plans; see C2 |
| Media Gallery (≤10) | `entity_media` (entity_type `trip_plan`) / `shared.v_tour_photos` | same as thumbnail | |
| Created At | `trip_plans.created_at` | COMMERCIAL | |
| Created by | `trip_plans.created_by` → `staff_users` | IDENTITY | not shown |
| Source (CIS / manual) | `trip_plans.source_system`, `source_id` | COMMERCIAL | not shown in Figma; needed (C1) |

### Itinerary builder (day / slot)

| UI field | ERD table.column | Class | Note |
|---|---|---|---|
| Day N | `trip_plan_itinerary.day_number` | CONTENT when CIS-synced (day structure is CIS, ADR 0005 §1) | |
| Day date "Saturday, Oct 12, 2025" | **missing in ERD (deliberately)** | — | only meaningful on a trip case (`trip_case_version_itinerary.date`) |
| Slot Morning/Afternoon/Evening | `trip_plan_itinerary.activity_period` (enum morning/afternoon/evening) | COMMERCIAL structure | matches |
| Activity (title) | `trip_plan_itinerary.activity_id` → `activities.title` (CIS-synced via `source_system/source_id`) | CONTENT | |
| Slot description ("Welcome to Bali! …") | `trip_plan_itinerary.note` or `activities.description` | CONTENT (activity copy) / COMMERCIAL (internal note) | ambiguous; see C5 |
| Duration "1 hr 30 mins" | `trip_plan_itinerary.travel_hours` (numeric 4,1)? | COMMERCIAL | activity duration ≠ travel hours; **missing** an activity-duration column |
| Transport "Flight / Private Car / Walking" | `trip_plan_itinerary.transfer_type` | COMMERCIAL | free varchar, no enum |
| Hotel "Bali Premium Hotels & Suites" | `trip_plan_itinerary.hotel_id` → `hotels.name` | COMMERCIAL (hotel = supplier inventory) | |
| Location type (start/end/overnight) | `trip_plan_itinerary.location_type` | COMMERCIAL | not shown in UI |
| Slot order (drag) | **missing in ERD** — no position within day | — | period gives 3 fixed slots; multiple activities per period need `position` |

### Create Trip Case modal

| UI field | ERD table.column | Class |
|---|---|---|
| Customer / Lead | `trip_cases.customer_id` → `customers` (lead = unverified email, ADR 0004 O6) | IDENTITY |
| Template | `trip_cases.trip_plan_id` | COMMERCIAL |
| Start Date / End Date | `trip_cases.start_date`, `end_date` | COMMERCIAL |
| Adults / Children | `trip_cases.pax` (single smallint) | COMMERCIAL — **missing** adults/children split |
| Internal Notes | `trip_case_status_history.note` (first row) or `trip_case_versions.notes` | COMMERCIAL — no dedicated column; propose `trip_cases.internal_notes` |
| Trip style | `trip_cases.trip_style` (copied from plan) | COMMERCIAL |
| Created by | `trip_cases.created_by` | IDENTITY |

### Staff / shell

| UI | ERD | Class |
|---|---|---|
| "Martha Kent / Super Admin" | `staff_users.name`, `staff_users.role` (thin profile keyed by CIS `shared.admin_users.id`, O1) | IDENTITY | role "Super Admin" is not in enum (admin/sales/content_creator; + `contracting` from ADR 0005 §8) |

---

## Conflicts / decisions

Each item gives the conflict, then options, then the recommendation (marked **Rec**).

**C1. Who authors a template: CIS or Booking?** Figma has a full content editor (name, description,
photos, day-by-day copy). ADR 0004 O7 and ADR 0002 say customer-facing content is authored in CIS, and ADR
0005 §3 says `trip_plans` are "synced from a CIS published tour". ERD keeps `source_system`
(cis | manual).
- (a) Templates are only CIS-synced. In Booking the content is read-only and staff edit only commercial
  fields (published flag, supplier, prices, hotels per day, inclusions as package terms).
- (b) Allow `manual` templates authored in Booking, which goes against O7.
- (c) Hybrid: CIS-synced is the default, content is locked. A `manual` template only holds commercial
  structure (title as an internal label, days → CIS activities + hotels). Any customer-facing text links back to CIS.
- **Rec (a), with (c) kept as an escape hatch for later.** The edit page shows content fields
  (Description, photos, day copy, destinations) **read-only with an "Edit in CIS" link**. "Create Trip
  Plan" becomes **"Import from CIS catalog"**: pick a CIS published tour, which creates `trip_plans`
  (source_system='cis') plus its itinerary skeleton. Then staff fill in the commercial parts.

**C2. Photos upload (Thumbnail + Gallery up to 10).** CIS owns tour photos (`shared.v_tour_photos`, ERD
header). The ERD has no `trip_plans.cover_media_id`.
- **Rec:** for CIS templates, show the photos from `v_tour_photos` read-only (cover = first photo; to change it, go to CIS).
  Drop the upload dropzones from the Booking UI for v1. The Create (800x400) and Edit (1200x675) size hints also contradict each other. They do not matter if upload is dropped.

**C3. Inclusions / Exclusions.** Customer-facing copy, so CIS content. They also define the commercial
package, which Booking owns.
- (a) Read from CIS (tour inclusions in CIS content); (b) Booking-owned `what_it_has` as package terms.
- **Rec (b)** for v1. ERD already has `what_it_has` / `what_it_does_not_have`, and inclusions follow what is
  priced (meals, transfers), which ADR 0005 puts in Booking. Mark this as an O7 exception and confirm it with
  Nghiệp. Otherwise move it to CIS later.

**C4. Pricing model.** Figma uses free-text age categories (Adult 12+ / Child 4-11 / Infant 0-3) with one
amount each. ADR 0005 uses season × pax band (1, 2, 3–4, 5–6, 7–10, 11+) × currency × validity. Selling
price = cost ÷ (1 − margin), entered by the `contracting` role with maker-checker. Sales never type net
rates. The ERD `trip_plan_prices` has no age column.
- (a) Replace the Pricing section with a **read-only price matrix** (season × pax band, per currency) from
  `trip_plan_prices`, plus a link to the cost sheet / price publishing (ADR 0005 §7). Child/infant become child policy rules.
- (b) Keep the Figma rows and add `age_category` to `trip_plan_prices`, which conflicts with ADR 0005.
- **Rec (a).** EST. PRICE and "Estimated Price (Per Person)" read `booking.v_from_prices`. They are
  never typed. Child policy goes to the rate sheet (ADR 0005 §8 already lists "child policy").

**C5. Start/End Date and day dates on a template.** The ERD deliberately has none. Dates belong to the trip case.
- **Rec:** remove Start/End Date from the template form. Show days as "Day 1, Day 2…" with no calendar
  date. Dates appear only after "Use for Trip Case" (start_date + day_number).

**C6. Country / City / Latitude / Longitude inputs.** CIS `shared.destinations` owns places (golden
record, ERD). The ERD has no lat/lng and no single country, because templates can be multi-country.
- **Rec:** replace them with an ordered **destinations picker** (`trip_plan_destinations`, CIS
  destinations search). Show country as derived chips. Show the lat/lng/map read-only from CIS. Do not
  allow free-text coordinates. The mock lat/lng (27.7172, 85.3240) is Kathmandu, labelled "Bali".

**C7. Status in two places.** The "Status" dropdown in the form duplicates the Save as Draft / Publish buttons.
- **Rec:** drop the dropdown. Draft or Published is set only by the header buttons and the Unpublish dialog.
  `Active/Inactive` (record_status) is an archive flag. Propose to show it only on the detail page and to use "Delete"
  = soft delete (`deleted_at`). Block delete when trip cases reference the template; offer Unpublish instead.

**C8. "Send to Customer" on Edit Template.** A template has no customer. Sending is a trip-case-version
action (`trip_case_versions.is_sent_to_customer`).
- **Rec:** remove it from the template edit page. Use the EDIT TEMPLATE-1 header (Cancel / Save as Draft / Save Changes).

**C9. Slot fields vs ERD.**
- Duration of the activity has no column. `travel_hours` means transfer time. **Rec:** add
  `trip_plan_itinerary.duration_hours`, or read the duration from the CIS activity/atom.
- There is no ordering within a period. **Rec:** add `position smallint` (drag-reorder is drawn).
- The slot description is either `note` (internal, COMMERCIAL) or the activity description (CIS CONTENT).
  **Rec:** show the CIS activity description read-only and use `note` as an internal staff note.
- `transfer_type` is free text. **Rec:** a small enum or lookup (flight, private_car, shared_van, boat, train, walking).

**C10. Create Trip Case modal vs ERD.** Adults/Children vs single `trip_cases.pax`. There is no internal-notes column.
Customer is a plain text box.
- **Rec:** add `pax_adults`, `pax_children` (keep `pax` as the generated total), or store the split in the
  version. Add `trip_cases.internal_note`. Make Customer/Lead a combobox: search `customers` by
  name/email/phone, with "+ New lead (name + email)" per O6. The new case starts `new_inquiry`, and V1 is copied
  from the template itinerary. Fix the typo "Edn Date".

**C11. Trip style / category.** Free varchar in ERD, while Figma uses a filter + select. **Rec:** a fixed list.
Either reuse the CIS tour taxonomy if CIS has one (content classification belongs to CIS), or add a small Booking
lookup table. Decide together with C1.

**C12. Roles.** The UI says "Super Admin". The ERD enum is admin / sales / content_creator (+ contracting, ADR
0005). With O7, `content_creator` has nothing to author in Booking. **Rec:** template commercial edits go to
admin + contracting (prices). Sales can only read and "Use for Trip Case". Add a role matrix to the UI spec (AA-683).

**C13. Copy-paste defects in Figma** (fix in the implementation, no decision needed): "Unpublish Activity" →
"Unpublish Template"; "Everest Base Camp Trek" in the dialog; user-menu items (Edit Profile / Block
User / Delete User) in the tab variant; "Search by name, email or phone"; header SKU "ACT-2941"; sidebar
highlights "Countries"; "Description: … of the activity"; "ITINERARY BUIDER" (typo); duplicate "Duration"
in the Overview card; list price $1,450 vs detail $1,950.

### Options for Nghiệp to approve (summary)

1. C1 template authoring: **(a) CIS-synced only, content read-only + "Edit in CIS"** / (b) Booking manual authoring / (c) hybrid.
2. C4 pricing UI: **(a) read-only season × pax-band matrix + from-price view** / (b) Figma age rows (needs an ERD change and conflicts with ADR 0005).
3. C3 inclusions/exclusions owner: **(b) Booking package terms** / (a) CIS content.
4. ERD additions for the UI: `trip_plan_itinerary.position`, `duration_hours`; `trip_cases.pax_adults/pax_children/internal_note` (yes/no).
5. Remove from Booking UI: template dates, lat/lng inputs, photo upload, Status dropdown, "Send to Customer" (yes/no).
