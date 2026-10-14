# Figma spec — module 07: Activities & Hotels (AA-Booking staff admin)

Source: `docs/AAA/figma_AAA/` — 18 PNGs matched the module filter; **all 18 were read**.
Read against: root ADR 0004 (O1 staff login via CIS, O7 content in CIS, O8 TripPlanner front door),
ADR 0005 (pricing/suppliers), ADR 0002 (only CIS writes content), ERD v2 `booking.dbml`,
`apps/AA-Booking/CONTEXT.md`.

## 0. Screen inventory

| File | What it really shows | Notes |
|---|---|---|
| ACTIVITY MANAGEMENT.png | Activities list (default) | canonical list |
| ACTIVITY MANAGEMENT-1.png | List + row "…" menu open | menu: View Details / Edit Activity / Duplicate / Unpublish / Delete |
| ACTIVITY MANAGEMENT-2.png | List + toast "Activity Published successfully" | after create |
| ACTIVITY  DETAILS.png | Activity detail page | |
| ACTIVITY  DETAILS-1.png | Detail + Unpublish confirm | |
| ACTIVITY  DETAILS-2.png | Detail + Delete confirm | |
| ADD NEW ACTIVITY.png | Create activity, full page form | |
| ADD NEW ACTIVITY-1.png | **Edit** activity form (prefilled) | page header says "Dashboard" and title "Edit Activity - Everest Base Camp Trek" while data is Ubud — Figma copy errors |
| ADD NEW ACTIVITY-2.png | **Mis-filed: "Edit Trip Case #TC-2024-089"** | belongs to the trip-case module, not here; ignore for 07 |
| EDIT ACTIVITY.png | List + toast "Activity updated successfully" | header says "Dashboard" (Figma error) |
| DELETE ACTIVITY.png | Delete confirm over an **older list variant** | older variant has Category + Supplier filters and a BASE PRICE column; row menu is copy-pasted from End-users (Edit Profile / Block User / Delete User) |
| UNPUBLISH ACTIVITY.png | Unpublish confirm over the same older list variant | same notes |
| HOTEL MANAGEMENT.png | Hotels list as card grid | |
| HOTEL DETAILS.png | Hotel detail, full page | sidebar highlights "Countries" (Figma error); ID shows `#CON-2024-089` (country prefix, copy error) |
| ADD NEW HOTEL.png | Create hotel, right drawer | background is the Countries page (Figma error) |
| EDIT HOTEL.png | Edit hotel, right drawer | has Delete Hotel button |
| EDIT HOTEL-1.png | **View** hotel, right drawer ("Last updated … by Jane Smith") | second detail pattern, competes with HOTEL DETAILS page |
| DELETE HOTEL.png | Delete hotel confirm over hotel grid | row menu copy-pasted from End-users |

Shared chrome (all screens): dark left sidebar (Overview: Dashboard, Admins, End-users, Suppliers,
Audit Logs; Content & Inventory: Countries, Hotels, Destination, Trip Plan Templates, Activities,
Itinerary Builder, Trip Cases; Trip Operations & Sales: Payment & Invoice, Trip Checks, Settings),
footer user card (name + role "Super Admin" + logout icon), collapse chevron; top bar with page
title, bell, "Admin" + avatar.

---

## 1. Activities

### 1.1 Activities list — `/activities`

Purpose: browse, search, filter all activities used in itineraries; entry to create/view/edit.

Layout:
- Page header: H1 "Activities", subtitle "Allows for the creation, editing, and organization of all
  individual activities that form part of trip itineraries."
- Card: toolbar row → filter row → table → pagination footer.

Toolbar:
- Search input, placeholder "Search activities by name…" (matches title).
- Button secondary "Export CSV" (download icon) — exports current filter result.
- Button primary "+ Add New Activity" → `/activities/new`.

Filters (row, label "Filter:"):
- Date range select, default "Last 30 Days" (on `created_at`; values not shown — propose: Last 7 /
  30 / 90 days, All time).
- "Status:" select, default "All Statuses" (values: Published, Draft; propose also Unpublished).
- "Experience Type:" select, default "All".
- Link "Reset Filters" (red, right).
- Older variant (DELETE/UNPUBLISH screens): "Category:" and "Supplier:" selects instead of
  Experience Type. Treat Experience Type = Category; Supplier filter — see Conflicts C4.

Table columns:
| Column | Content |
|---|---|
| ☐ (select all / row checkbox) | multi-select; selected row gets cream highlight. No bulk-action bar is drawn. |
| ACTIVITY NAME | 56px thumbnail + title (primary) + supplier name (secondary, e.g. "Bali Horizon Tours") |
| EXPERIENCE TYPE | text (Trekking, Hiking, Water Sports, Wildlife) |
| LOCATION | "City, Region/Country" (e.g. "Ubud, Bali", "Phuket, Thailand") |
| BASE PRICE | **older variant only** ($1,450, $2,100, $800, $1,200) |
| STATUS | badge |
| ACTION | "…" icon button → menu |

Status badges: `Published` (green dot, green pill), `Draft` (grey dot, grey pill).

Row menu (ACTIVITY MANAGEMENT-1): View Details (eye) → `/activities/[id]`; Edit Activity (pencil)
→ `/activities/[id]/edit`; divider; Duplicate (copy); Unpublish (eye-off) → confirm; divider;
Delete (red, trash) → confirm.

Pagination footer: "Showing 1 to 6 of 124 results", "1 of 16 pages", Prev (disabled on page 1) /
Next. (Numbers are inconsistent in Figma — 6 per page vs 16 pages; use server page size 10/20.)

Toasts (top-right, green left border, check icon, close ×):
- "Activity Published successfully" / "Activity has been created and added to the catalog."
- "Activity updated successfully" / "Changes to <title> has been saved."

Empty/loading states: **not drawn**. Propose kit defaults: skeleton rows; empty "No activities
match these filters" + Reset Filters.

### 1.2 Activity detail — `/activities/[id]`

Layout:
- Sub-header: back arrow + "Activity - <title>".
- Hero row: 88px thumbnail; H1 title; meta line: `# ACT-2941` (human code), badge `Published`
  (check-circle, green outline), badge `• Active` (green), calendar icon "Created At: Oct 12, 2023".
- Actions (right): icon button trash (red) → Delete confirm; "Unpublish" (eye-off, secondary) →
  Unpublish confirm; "Edit Activity" (primary, pencil) → edit.
- Left column cards: "Description" (paragraph); "Media Gallery" (3-up image grid).
- Right column card "Key Information": Experience Type (Trekking), Intensity (Moderate), Max Group
  Size (10 People), Location (Ubud, Bali, Indonesia), Latitude (27.7172), Longitude (85.3240).

Confirm dialogs (modal, dim backdrop, red warning icon):
- **Unpublish Activity**: "Are you sure you want to unpublish <title>? This will hide the activity
  from all users and remove it from any active search results." Buttons: Cancel / "Unpublish
  Activity" (red).
- **Delete Activity**: "Are you sure you want to permanently delete <title>? This action cannot be
  undone". Buttons: Cancel / "Delete Activity" (red).
  (Figma dialogs show "Everest Base Camp Trek" on an Ubud page — placeholder copy.)

No Publish/Re-publish button is drawn for a Draft or unpublished activity (gap — see C6).

### 1.3 Add activity — `/activities/new`; Edit activity — `/activities/[id]/edit`

Full-page form, centered single column card.
Sub-header: back arrow + "Add New Activity" | "Edit Activity - <title>".
Actions (top right): "Cancel" | "Save as Draft" | primary "Publish Activity" (create) / "Save
Changes" (edit).

Sections and fields (no required asterisks are drawn on this form; no inline validation shown):
| Section | Field | Type | Placeholder / value | Validation hint visible |
|---|---|---|---|---|
| GENERAL INFORMATION | Activity Title | text | "e.g., Everest Base Camp Trek" | none (propose required) |
| | Description / Notes | textarea | "provide a detailed description of the activity…" | none |
| | Experience Type | select | "Select type…" (edit: Hiking) | none |
| | Intensity Level | select | "Select level" (edit: Medium) | none |
| LOCATION DETAILS | Country | select | "Select country…" (Indonesia) | none |
| | City | select (combobox) | "e.g., Kathmandu" (Bali) | none |
| | Latitude (Geo-coordinate) | number text | "e.g., 27.7172" | none |
| | Longitude (Geo-coordinate) | number text | "e.g., 85.3240" | none |
| MEDIA | Thumbnail Image | dropzone | "Click to upload or drag and drop — SVG, PNG, JPG or GIF (max. 800x400px)"; edit: image preview + "Change Image" overlay, hint "Recommended size: 1200x675px (16:9)" | conflicting size hints |
| | Media Gallery | multi dropzone | "Click to upload multiple images — Upload up to 10 images"; edit: tiles with × remove + "Add More" tile | max 10 |

Max Group Size appears on the detail page but **not** in the form.

Behaviour: "Save as Draft" → `is_draft = true`; "Publish Activity" → toast 1.1 and back to list.

---

## 2. Hotels

### 2.1 Hotels list — `/hotels`

Purpose: "Manage hotel inventory, destination properties, and location imagery."

Toolbar: search "Search hotels by name…"; "Export CSV"; primary "+ Add Hotel" → opens Add drawer.
Filters: "Filter:" date (Last 30 Days), "Country:" (All Countries), "Sort by:" (Newest - Oldest;
propose also Oldest - Newest, Name A–Z, Recently updated), "Reset Filters".

Body: **card grid, 3 columns** (not a table). Card = cover image with top-right image-count chip
(icon + 12) and bottom-left location chip (pin + "Tokyo, Japan"); below: hotel name, "Updated 2 days
ago" (relative), "…" menu. No status badge on the card.

Card menu (seen only on DELETE HOTEL, copy-pasted): View Details / Edit Profile / Block User /
Delete User → implement as **View Details / Edit Hotel / Delete Hotel**.

Pagination: "Showing 1 to 5 of 124 results", "1 of 16 pages", Prev / Next.

Delete confirm: "Delete Hotel — Are you sure you want to permanently delete <name>? This action
cannot be undone" — Cancel / "Delete Hotel" (red).

Empty/loading: not drawn (propose skeleton cards; empty "No hotels yet" + Add Hotel).

### 2.2 Hotel detail — two competing patterns

(a) Full page `/hotels/[id]` (HOTEL DETAILS): back + "Hotel Details - <name>"; hero: thumbnail,
name, code `#CON-2024-089`, badges `Published` + `• Active`, "Created At: Oct 12, 2023"; actions
"Delete" (red outline) / "Edit Hotel" (primary). Body: large image viewer + thumbnail strip (selected
thumb has amber border, last thumb "+7 more"); right card "Hotel Details" key/value: Name, Country,
Total Images, Updated at ("Today, 10:42 AM").

(b) Right drawer (EDIT HOTEL-1): title = name, subtitle "Last updated on Oct 24, 2024 by Jane
Smith"; cards: Basic Information (Hotel Name, Country, City, Status badge `Active`); Location Details
(Address); Hotel Description; Gallery (12 Images) 3×2 grid + "View All 12 Images"; Hotel Links
(label/url pairs, read-only). Footer: Close / "Edit Details" (primary) → edit drawer.

Recommendation: use (b) drawer as the canonical view (`/hotels?view=<id>`, deep-linkable) — it holds
every field; keep (a) only if a lightbox gallery is needed. Decision D-H1 below.

### 2.3 Add / Edit hotel — right drawer (`/hotels?new=1`, `/hotels?edit=<id>`)

Header: "Add New Hotel" | "Edit Hotel", close ×.
| Field | Type | Placeholder / value | Validation visible |
|---|---|---|---|
| Hotel Name * | text | "e.g., The Siam Hotel" | required (asterisk) — the only required mark |
| Hotel Description | textarea | "Provide a detailed description for this hotel.." | none |
| Country Name | select | "Select a country" (Japan) | none |
| City | **free text** | "Enter city" (Tokyo) | none |
| Address | textarea | "Provide a detailed address for this hotel.." | none |
| Supplier | select | "Select supplier" (Tokyo Horizon Tour) | none |
| Hotel Images | multi dropzone / tile grid with × and "Upload Image" tile | "SVG, PNG, JPG or GIF (max. 10MB)", "Up to 20 images"; edit: "Recommended ratio 16:9, max 5MB per image." | max 20; size hint conflicts 10MB vs 5MB |
| Hotel Links | repeatable row: "Enter URL name" + "Paste URL links" + trash; "+ Add" | Youtube / amantokyo/youtube.com | none (propose URL validation) |

Footer: Add → Close / "Save Hotel" (primary). Edit → "Delete Hotel" (red, left) / Close / "Save
Changes" (primary, check icon).
No Status / Publish control in the hotel form although detail shows Published + Active (gap, C6).

---

## 3. Data mapping

Legend: COMMERCIAL = owned by Booking; CONTENT = owned by CIS (ADR 0002 / ADR 0004 O7) → read-only in
Booking, from CIS views; IDENTITY = staff/customer.

### 3.1 Activities

| UI field | ERD v2 column | Class | Note |
|---|---|---|---|
| Internal id | `booking.activities.id` | COMMERCIAL | |
| Code `ACT-2941` | **missing in ERD** | COMMERCIAL | add `code varchar unique` or derive from id |
| Activity Title | `activities.title` | CONTENT | customer-facing → CIS atom/segment title when `source_system='cis'` |
| Description / Notes | `activities.description` | CONTENT (description) / COMMERCIAL (internal notes) | Figma merges two things in one field — split (C2) |
| Experience Type | `activities.experience_type` (enum hiking, biking, culture, wildlife, food, nature, boat, adventure, urban, relaxation) | CONTENT (taxonomy) | Figma values "Trekking", "Water Sports" are not in the enum (C5) |
| Intensity Level | `activities.intensity` (rest, low, medium, high, extreme) | CONTENT | Figma shows "Moderate" on detail vs "Medium" in form → use enum label "Medium" |
| Max Group Size | **missing in ERD** | COMMERCIAL (operational capacity) | add `max_group_size smallint` or move to supplier rate (activity per group, ADR 0005 §2) |
| Country | derived from `activities.destination_id` → CIS `shared.destinations` | CONTENT | ERD note: destination_id replaces country_id + city + lat/lng |
| City | `activities.destination_id` → `shared.destinations` | CONTENT | picker over CIS places, not free text |
| Latitude / Longitude | **removed in ERD** (from `shared.destinations`) | CONTENT | read-only display from CIS place (C3) |
| Location column "Ubud, Bali" | `shared.destinations` name + parent/country | CONTENT | |
| Supplier (row subtitle, older Supplier filter) | **missing in ERD** (`activities` has no `supplier_id`) | COMMERCIAL | link via supplier contracts/net rates (ADR 0005 §2) or add `supplier_id` (C4) |
| Base Price (older variant) | **missing — must not be on activity** | COMMERCIAL | ADR 0005: activity net rate per pax/group in supplier rates; selling price computed (C4) |
| Thumbnail | **missing column**; `booking.entity_media` (entity_type='activity', position 0) or CIS photo view | CONTENT | |
| Media Gallery (≤10) | `booking.entity_media` → `booking.media_files` | CONTENT | photos are CIS content (ADR 0002 §1) → `shared.v_tour_photos` / CIS view (C1) |
| Status `Published`/`Draft` | `activities.is_draft` (+ `status`) | COMMERCIAL (catalog availability for selling) | mapping proposal C6 |
| Badge `Active` | `activities.status` = active/inactive | COMMERCIAL | |
| Created At | `activities.created_at` | system | |
| Created by | `activities.created_by` → `staff_users.id` | IDENTITY | O1: staff_users keyed by `shared.admin_users.id` |
| Source | `activities.source_system`, `source_id` | system | not shown in Figma; should show a "From CIS" chip |
| Delete | `activities.deleted_at` (soft) | — | Figma says "permanently" — UI copy must not (C7) |
| Duplicate | new row copy | — | only for manual activities |

### 3.2 Hotels

| UI field | ERD v2 column | Class | Note |
|---|---|---|---|
| Internal id | `booking.hotels.id` | COMMERCIAL | |
| Code `#CON-2024-089` | **missing in ERD** | COMMERCIAL | add `code` (prefix HTL-) or drop from UI |
| Hotel Name * | `hotels.name` | COMMERCIAL (supplier inventory name) | hotels have no CIS home today (C1-H) |
| Hotel Description | `hotels.description` | CONTENT | customer-facing (C1-H) |
| Country Name | derived from `hotels.destination_id` → `shared.destinations` | CONTENT | ERD: "country is derived from the destination" |
| City | `hotels.destination_id` (not null) | CONTENT | Figma free text → must be a CIS place picker |
| Address | **missing in ERD** | COMMERCIAL (operational, for vouchers/transfers) | add `address varchar` |
| Supplier | `hotels.supplier_id` → `booking.suppliers` | COMMERCIAL | |
| Hotel Images (≤20) | `booking.entity_media` (entity_type='hotel') → `media_files` | CONTENT (customer-facing photos) | (C1-H) |
| Total Images / count chip | count of `entity_media` | derived | |
| Hotel Links (name + url) | `hotels.links` jsonb `[{label,url}]` | COMMERCIAL (staff reference) | |
| Hotel style | `hotels.hotel_style` | CONTENT | **in ERD, not in Figma** — add to form or drop |
| Status `Active` | `hotels.status` | COMMERCIAL | |
| Badge `Published` | **missing in ERD** (no `is_draft`/`is_published` on hotels) | COMMERCIAL | drop badge or add column (C6) |
| Created At / Updated at | `hotels.created_at` / `updated_at` | system | |
| "Last updated … by Jane Smith" | **missing** (`hotels` has no `updated_by`) | IDENTITY | read latest `booking.audit_logs` row (actor_id → staff profile) |
| Delete | `hotels.deleted_at` (soft) | — | (C7) |
| Room types / rates | not in Figma; ADR 0005 supplier contract rates | COMMERCIAL | Figma has **no rate entry at all** (C8) |

---

## 4. Conflicts / decisions

Each item: what Figma does → what the ADR says → recommendation (options where Nghiệp must choose).

**C1 — Activity content editing in Booking vs ADR 0004 O7 / ADR 0002.** Figma lets staff create and
edit activity title, description, type, intensity, location and photos in Booking. O7: all
customer-facing content (activities) is authored in CIS; ADR 0002: photos and places are CIS content.
Options:
- (A, recommended) Booking activities are a **commercial overlay on CIS activities**: the list reads
  CIS (`source_system='cis'`, synced via AA-679 catalog views of atoms/segments); title, description,
  type, intensity, place and gallery are read-only with an "Edit in CIS" deep link to the CIS admin;
  Booking edits only commercial fields (status/sellable, supplier link, max group size, internal
  notes). "Add New Activity" becomes "Add commercial activity" only for `source_system='manual'`
  services CIS does not have (e.g. a private transfer add-on), with a short internal description,
  and is flagged not customer-facing until CIS adopts it.
- (B) Booking keeps the full Figma form; CIS ingests Booking activities as a new content source.
  Contradicts O7 and ADR 0002 ("revisit if a second app authors content … through a CIS API").
- (C) Remove the Activities page from Booking entirely; itinerary builder picks CIS atoms directly.
  Simplest, but loses the supplier/capacity overlay.

**C1-H — Hotels have no owner in CIS.** CIS has no hotel/accommodation table (checked
`db-schema-reference.md`); ERD v2 puts `hotels` in Booking, ADR 0005 treats hotels as supplier
inventory with net rates. But description and photos are customer-facing (shown in proposals).
Options:
- (A, recommended) Hotel is **COMMERCIAL in Booking** (name, supplier, address, links, status, rates);
  hotel description + photos are allowed in Booking as a documented **exception to O7**, recorded in
  an ADR amendment, until CIS gets an accommodation model; place stays a CIS `destination_id` picker.
- (B) Hotel description/photos move to CIS (new CIS content type, CIS job + admin); Booking form keeps
  only commercial fields. Correct per ADR 0002 but adds CIS scope before Booking can ship.
- (C) Hotels show no description/photos at all in v1 (staff-only inventory); add later.

**C2 — "Description / Notes" is one field.** Split into customer-facing `description` (CONTENT, C1)
and `internal_notes` (COMMERCIAL, missing in ERD → add `activities.internal_notes text`).

**C3 — Country/City/Latitude/Longitude inputs.** ERD v2 removed lat/lng and country/city from
activities and hotels in favour of `destination_id` (CIS `shared.destinations`, ADR 0002 places =
CIS content). Recommendation: one "Place" combobox searching CIS destinations (country shown as
read-only, lat/lng shown read-only from the place); if a place is missing, link "Request place in
CIS" — never type coordinates in Booking. Hotel "City" free-text field likewise becomes the place
picker; "Address" stays free text (commercial).

**C4 — Base Price and Supplier on activities (older list variant).** ADR 0005: net rates live in
supplier contracts (activity per pax or per group, validity, currency), selling price = net ÷ (1 −
margin), owned by role `contracting`, maker-checker. Recommendation: drop BASE PRICE from the list (or
show a read-only "from net rate" computed from the active contract, contracting/admin only); supplier
on an activity comes from its active contract rate (no `supplier_id` column) — Supplier filter = "has
an active rate from supplier X". Option: add `activities.supplier_id` as the default supplier if ops
want a simple link (ERD change).

**C5 — Experience Type values.** Figma uses Trekking, Hiking, Water Sports, Wildlife; ERD enum has
hiking, biking, culture, wildlife, food, nature, boat, adventure, urban, relaxation. If C1-A, the
taxonomy is CIS's: reuse the CIS atom/experience vocabulary and make the Booking enum (or a TEXT +
CHECK, as `bk-002` did for status) follow it. Map Trekking→hiking, Water Sports→boat/adventure, or
add values before creating the enum (enum values are hard to remove, ADR 0004 decision 7).

**C6 — Status model.** Figma: list badges Published/Draft; detail shows Published **and** Active;
Unpublish action; no Re-publish action; hotels show Published with no column backing it. ERD:
activities `is_draft` + `status active|inactive`; hotels only `status`. Recommendation (activities):
Draft = `is_draft=true`; Published = `is_draft=false AND status='active'`; Unpublished =
`is_draft=false AND status='inactive'` (add badge `Unpublished`, grey/amber, and a "Publish" action
on Draft/Unpublished rows and detail). Show one badge, not two. Hotels: single `Active`/`Inactive`
badge; drop "Published". "Unpublish" semantics = not selectable in new itineraries/proposals; must
not change already-sent or approved trip case versions (ADR 0005 transactional integrity).

**C7 — "Permanently delete … cannot be undone".** ERD uses soft delete (`deleted_at`) and
`audit_logs`; activities/hotels are referenced by `trip_plan_itinerary` and
`trip_case_version_itinerary`. Recommendation: copy "Delete <name>? It will be removed from lists and
can no longer be added to itineraries. Existing trip cases keep it."; block delete (or force
Unpublish) when referenced by an approved version; CIS-sourced activities cannot be deleted in
Booking at all (only unpublished).

**C8 — No rate entry on Hotel/Activity screens.** ADR 0005 needs hotel rates (room type, season, meal
plan, single supplement, extra bed) and activity rates per pax/group, entered by `contracting` via
Excel upload (phase 1). Figma has none. Recommendation: add a read-only "Rates" tab on hotel/activity
detail listing active contract rows (supplier, variant, season/validity, unit, net, currency) with a
link to the supplier-contract module; entry stays in the contracting flow, not these forms.

**C9 — Roles / permissions (O1, ADR 0005 §8).** Figma shows "Super Admin" with every action.
Staff log in via CIS (`shared.admin_users`, JWT `aud=booking`); Booking role from `staff_users`
(admin / sales / content_creator + contracting). Recommendation: admin + contracting can
create/edit/unpublish/delete commercial fields; sales read-only; content_creator — no write in
Booking if C1-A (content is edited in CIS).

**C10 — Two hotel detail patterns** (full page vs drawer) and full-page activity forms vs drawer
hotel forms. Recommendation D-H1: drawer for hotel view/add/edit (fewer fields), full page for
activity detail/edit; or unify both on full pages for consistency — Nghiệp to choose; default to the
CIS UI kit (`app/_kit`) drawer + page patterns already used in CIS admin.

**C11 — Figma copy/placement errors to ignore:** ADD NEW ACTIVITY-2 is a trip-case screen; "Dashboard"
headers on Edit screens; "Everest Base Camp Trek" placeholder names in dialogs on Ubud data;
`#CON-` hotel code; Countries highlighted on Hotel Details; Countries page behind Add Hotel; End-user
menu items (Edit Profile / Block User / Delete User) on activity/hotel menus; image-size hints
conflicting (800x400 vs 1200x675; 10MB vs 5MB → use 16:9, ≤10MB, server resizes);
"Showing 1 to 6 of 124 / 16 pages" arithmetic.

**C12 — Media storage.** If any media stays in Booking (C1-H option A), use `booking.media_files`
(S3 bucket/key, URL built at read time) + `entity_media` positions; thumbnail = position 0 (no
separate column). CIS-sourced photos are read from CIS photo views, never copied.

### Proposed ERD deltas (only if the options above are chosen)
- `activities`: `code`, `internal_notes`, `max_group_size` (or via rates); maybe `supplier_id`.
- `hotels`: `code`, `address`; decide on `hotel_style` in UI.
- Enum `activity_experience_type` aligned to CIS taxonomy before it is created (`bk-00x`).
- No `price`/`base_price` columns on activities/hotels (ADR 0005).
