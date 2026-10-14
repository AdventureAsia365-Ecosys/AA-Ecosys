# 06-geo — Countries & Destinations (AA-Booking staff admin) — Figma UI spec

Source: `docs/AAA/figma_AAA/` (16 PNGs matched, all 16 read successfully).
Read against: ADR 0004 (O1, O7, O8), ADR 0005, ERD v2 `docs/AAA/erd-v2/booking.dbml`, `apps/AA-Booking/CONTEXT.md`,
`docs/architecture/db-schema-reference.md` (`shared.destinations`, `shared.v_destination_photos`).

| File | Actually shows |
|---|---|
| COUNTRY MANAGAMENT.png | Country list (card grid) |
| COUNTRY MANAGAMENT-1.png | Country list + toast "Country Published Successfully" |
| COUNTRY MANAGAMENT-2.png | **Hotel Management** list + toast "Hotel Published Successfully" (misnamed; belongs to the hotels module) |
| COUNTRY MANAGAMENT-3.png | **Byte-identical-looking duplicate of -2** (Hotel Management) (misnamed) |
| ADD COUNTRY.png | Add Country drawer |
| EDIT COUNTRY.png | Edit Country drawer |
| COUNTRY DETAILS.png | Country Details drawer (quick view) |
| COUNTRY DETAILS-1.png | Country Details full page (Japan) |
| DELETE COUNTRY.png | Delete Country confirm modal (+ row "..." menu visible) |
| UNPUBLISHED COUNTRY.png | Unpublish Country confirm modal |
| DESTINATION MANAGEMENT.png | Destination list (table) |
| DESTINATION MANAGEMENT-1.png | Destination list + toast "Destination Saved Successfully" |
| ADD DESTINATION.png | Add Destination drawer |
| EDIT DESTINATION.png | Edit Destination drawer |
| DESTINATION DETAILS.png | Destination Details drawer |
| DELETE DESTINATION.png | Delete Destination confirm modal |

Shared chrome (all screens): left sidebar (Adventure Asia logo, collapse chevron). Groups: OVERVIEW (Dashboard, Admins,
End-users, Suppliers, Audit Logs); CONTENT & INVENTORY (Countries, Hotels, Destination, Trip Plan Templates, Activities,
Itinerary Builder, Trip Cases); TRIP OPERATIONS & SALES (Payment & Invoice, Trip Checks, Settings). Footer: staff avatar,
name "Martha Kent", role "Super Admin", logout icon. Top bar: page title on the left; bell (with unread dot), "Admin" label
and avatar on the right. Drawers open from the right over a dimmed page; modals are centred.

Note: the drawers behind ADD/EDIT/DETAILS COUNTRY show the top-bar title "Templates", not "Country Management". This is a
Figma copy-paste artefact; use "Country Management".

---

## 1. Countries list — `/geo/countries`

Purpose: browse the country pages. Figma subtitle: "Manage country details, destination photos, and localized travel information."

Layout
- Page header: H1 "Countries" + subtitle.
- Toolbar card: search input "Search countries..." (left); buttons **Export CSV** (secondary, download icon) and
  **+ Add Country** (primary orange) on the right.
- Filter row: `Filter:` date range dropdown (default "Last 30 Days"; presumably filters on updated_at), `Status:` dropdown
  (default "All Statuses"; values not shown, inferred Published / Unpublished, maybe Active / Inactive), `Sort by:` dropdown
  (default "Newest - Oldest"), **Reset Filters** link (red, right).
- Card grid, 3 columns. Each card: cover image, image-count chip top-right (gallery icon + N, e.g. 4, 2, 6, 12, 3);
  country name; "Updated <relative time>" (e.g. "Updated 2 days ago"); "..." kebab button.
- Kebab menu (seen in DELETE/UNPUBLISHED screens): View Details, Edit Profile, Block User (red), Delete User (red).
  Labels are copy-pasted from the Users module; intended labels: **View Details, Edit Country, Unpublish, Delete Country**.
- Pagination footer: "Showing 1 to 5 of 124 results", "1 of 16 pages", Prev / Next.
- Toast (MANAGAMENT-1): green check, "Country Published Successfully", "Country has been created and added to the catalog.", close X.
  Fires after Add Country save.

States: no empty or loading state shown. Proposed: skeleton cards while loading; empty state "No countries yet" + Add Country (if allowed, see Conflicts).
Note: the Indonesia image-count chip renders "1 2" wrapped (layout bug for 2-digit counts; use `white-space: nowrap`).

## 2. Country details (full page) — `/geo/countries/[countryCode]`

Source: COUNTRY DETAILS-1.png ("Country Details - Japan").
- Header bar: back arrow, breadcrumb title "Country Details - Japan".
- Identity row: thumbnail; name "Japan"; record code "#CON-2024-089"; badge **Published** (green, check icon); badge
  **Active** (green dot); "Created At: Oct 12, 2023" (calendar icon). Actions right: **Unpublish** (secondary, eye-off icon),
  **Edit Country** (primary, pencil icon).
- Left: hero image. Under it 3 stat tiles: "Images — 4 photos"; "Active Suppliers — Moments ago" (label/value mismatch in
  Figma; intended: count of active suppliers in this country); "Visibility — Published".
- Right card "Record summary": Country = Japan; Status = Active; Images count = "4 uploaded assets"; Updated at = "Today, 10:42 AM".
- Card "Destination Images" with right caption "Gallery synced from country record": grid of 5 images (3 + 2). No actions.
- Card "Country information": label "Description" + multi-paragraph rich text (read).
- Not shown on this page (but present in the drawer variant): lat/lng, FAQ, festivals.

## 3. Country details (drawer) — `/geo/countries?view=[countryCode]` (or keep the full page only)

Source: COUNTRY DETAILS.png ("Country Details" right drawer, Thailand).
- Card "Media": hero image (with burned-in title "THAILAND: ROYAL SPLENDOR"), 4 thumbnails, button "View All 12 Images" (opens gallery/lightbox).
- Fields grid: Country Name = Thailand; Country ID = "CTR-8492"; Latitude = "15.8700° N"; Longitude = "100.9925° E".
- Section DESCRIPTION (lines icon): plain paragraph.
- Section FREQUENCY ASKED QUESTION (typo, should be "Frequently Asked Questions"): list of Q (bold) + A (muted).
- Section KEY FESTIVALS (calendar icon): each item = name, month pill (e.g. "April", "November"), summary.
- Footer: **Close** (secondary), **Edit Country** (primary, pencil).
- Inconsistencies with page variant: ID format "CTR-8492" vs "#CON-2024-089"; drawer has lat/lng/FAQ/festivals, page does not.
  Recommend one detail view (full page) containing all sections.

## 4. Add Country (drawer) — `/geo/countries/new` (drawer over list)

Title "Add Country", close X. Footer: **Close**, **Save Country** (primary).
Sections:
- GENERAL
  - Country Name — select, placeholder "Select a country" (chooses from a fixed country list, i.e. ISO list). Required (implied; no asterisk anywhere).
  - Description — rich-text editor; toolbar: Bold, Italic, Underline, H1, H2, bullet list, numbered list, link, inline image.
    Placeholder "Type your information here...".
- MEDIA
  - Country Images — dropzone "Click to upload or drag and drop", "SVG, PNG, JPG or GIF (max. 10MB)", helper "Up to 20 images".
- GEOGRAPHY
  - Longitude — text/number, placeholder "e.g 100.5018".
  - Latitude — text/number, placeholder "e.g 13.7563". (Order is Longitude then Latitude; recommend Latitude first.)
- FREQUENCY ASKED QUESTION — "+ Add FAQ" link (right). Repeating card "FAQ #n" with delete (trash) button:
  - Question — text, placeholder "e.g What is the best time to visit Thailand?"
  - Answer — textarea, placeholder "e.g The best time to visit is between November and early April...".
- FESTIVALS — "+ Add Festival" link. Repeating card "Festival #n" with delete:
  - Festival Name — text, placeholder "e.g Songkran (Thai New Year)"
  - Month — select "Select month" (Jan–Dec)
  - Brief Summary — textarea.
- Not in Figma but in ERD: `subtitle`, `area_id`, `weather`, `status`. No status/publish toggle on the form; the toast says
  "Published", so save = publish in the design.
- Validation hints visible: only file type/size and "Up to 20 images". No required markers, no inline errors shown.

## 5. Edit Country (drawer) — `/geo/countries/[countryCode]/edit`

Same sections as Add, prefilled (Japan). Differences:
- MEDIA "Images": existing thumbnails each with remove X, plus "Upload Image" tile; helper "Recommended ratio 16:9, max 5MB per image"
  (conflicts with Add's "max. 10MB"; pick one, recommend 10MB or a single server limit).
- Longitude rendered as a select with chevron (Figma bug; should be a number input).
- Festival Month rendered as a text input "April" (Add uses a select; use the select).
- Sample data mixes Japan with Thailand FAQ/festival text (mock data only).
- Footer: **Delete Country** (danger, left, trash icon), **Close**, **Save Changes** (primary, check icon).

## 6. Delete Country (modal)

Warning icon (red). Title "Delete Country". Body: "Are you sure you want to permanently delete **Japan**? This action cannot be undone".
Buttons: **Cancel**, **Delete Country** (danger).

## 7. Unpublish Country (modal)

Title "Unpublished Country" (grammar: should be "Unpublish Country"). Body: "Are you sure you want to unpublished **Japan**? This will hide
the country from all users and remove it from any active search results." Buttons: **Cancel**, **Unpublished Country** (danger; should be "Unpublish").
No "Publish" (re-publish) counterpart is drawn; needed for symmetry.

## 8. Destinations list — `/geo/destinations`

Purpose (Figma subtitle): "Manage city destinations used across itineraries, hotels, and trip planning. Each destination includes geographic
coordinates, activity status, and media."
- KPI tiles: Total destinations (48), Active destinations (29), Countries covered (12).
- Toolbar: search "Search destinations..."; **Export CSV**; **+ Add Destination** (primary).
- Filters: `Filter:` "Last 30 Days"; `Country:` "All Countries"; `Status:` "All statuses"; **Reset Filters**.
- Table columns: [checkbox, with header select-all] | NAME (thumbnail + name + one-line tagline, e.g. "Urban gateway destination") |
  COUNTRY | LONGITUDE | LATITUDE | STATUS | MEDIA (image icon + "N files") | ACTION ("..." menu).
- Row selection: selected row highlighted (cream bg, orange checkbox). No bulk-action bar is drawn; propose bulk Activate/Deactivate/Export.
- Status badge values: **Active** (green, dot), **Inactive** (grey, dot).
- Row menu (from DELETE DESTINATION): View Details, Edit Profile, Block User, Delete User (copy-paste labels; intended: View Details, Edit Destination,
  Deactivate, Delete Destination).
- Pagination: "Showing 1 to 5 of 124 results", "1 of 16 pages", Prev / Next (124 conflicts with KPI 48: mock data).
- Toast (MANAGEMENT-1): "Destination Saved Successfully" / "Destination name created and added to catalog."
- Mock data has Bangkok twice (rows 1 and 5) — a real duplicate-destination risk; see Conflicts.
- No empty/loading states drawn.

## 9. Destination details (drawer) — `/geo/destinations/[destinationId]`

- MEDIA: grid of images (2 columns) + "Upload Image" tile (upload directly from the details view).
- GENERAL DETAILS: Name (Chiang Mai), Country (Thailand), Status (badge "Active"), Date Added (Oct 24, 2024).
- GEOGRAPHY: Longitude "98.9817° E", Latitude "18.7883° N", embedded map with a pin.
- Footer: **Close**, **Edit Destination** (primary).
- Description is not displayed (although it is collected on Add).

## 10. Add Destination (drawer) — `/geo/destinations/new`

Fields: Destination Name (text, "e.g., Bangkok"); Country (select "Select a country"); Longitude ("e.g., 100.5018");
Latitude ("e.g., 13.7563"); Description (optional) — textarea "Provide a detailed description about the destination...";
Destination Media — dropzone "SVG, PNG, JPG or GIF (max. 10MB)".
Only "(optional)" marker is on Description, so Name, Country, Lng, Lat are implicitly required.
No status field. Footer: **Close**, **Save Destination**.

## 11. Edit Destination (drawer) — `/geo/destinations/[destinationId]/edit`

Fields: Destination Name (Bangkok); Country Name (select, Thailand); Longitude; Latitude; **Address** (textarea, sample is a Tokyo
hotel address — this field replaces Description from Add); Destination Media grid (5 images, each with X) + "Upload Image";
helper "Recommended ratio 16:9, max 5MB per image". Footer: **Close**, **Save Changes**. No Delete button here (unlike Edit Country).
Sample images are hotel interiors — mock data copied from the Hotels module.

## 12. Delete Destination (modal)

"Delete Destination" / "Are you sure you want to permanently delete **Bangkok**. This action cannot be undone" / **Cancel**, **Delete** (danger).

---

## Data mapping

Legend: COMMERCIAL = owned by Booking; CONTENT = owned by CIS (ADR 0002 + ADR 0004 O7) → read-only in Booking;
GOLDEN = CIS golden record (`shared.destinations`) → read-only in Booking; IDENTITY = staff/customer; DERIVED = computed.

### Country

| UI field | ERD / source | Class |
|---|---|---|
| Country Name (select) | `booking.country_profiles.name` + PK `country_code` (ISO 3166-1) | IDENTITY-of-record (reference data; ISO list) |
| Country ID "CTR-8492" / "#CON-2024-089" | missing in ERD (PK is `country_code`); show ISO code instead | — |
| Description (rich text) | `booking.country_profiles.description` | **CONTENT** (O7: country text authored in CIS) |
| Subtitle | `country_profiles.subtitle` (not in Figma) | CONTENT |
| Country Images / gallery / cover | `country_profiles.cover_media_id` + `booking.entity_media(entity_type='country_profile')` → `media_files` | **CONTENT** (customer-facing photos; CIS photo views are the source per ERD header) |
| Image count chip / "4 photos" / "4 uploaded assets" | DERIVED count of `entity_media` | DERIVED |
| Latitude / Longitude | **missing in ERD by design** ("lat/lng dropped (CIS owns places)") | GOLDEN/CONTENT (CIS) |
| FAQ (question, answer) | `country_profiles.faqs jsonb` | **CONTENT** |
| Festivals (name, month, summary) | `country_profiles.festivals jsonb` | **CONTENT** |
| Weather | `country_profiles.weather jsonb` (not in Figma) | CONTENT |
| Area | `country_profiles.area_id → booking.areas` (not in Figma) | COMMERCIAL (sales grouping) |
| Status "Active" | `country_profiles.status` (`record_status`: active/inactive) | COMMERCIAL (sellable or not) |
| Visibility / "Published" badge, Unpublish action | **missing in ERD** (`record_status` has no published/unpublished) | conflicts with CIS publish (see C3) |
| Created At / Updated at / "Updated 2 days ago" | `country_profiles.created_at / updated_at` | system |
| Active Suppliers tile | DERIVED from `booking.suppliers` by country (ERD supplier→country path to verify) | COMMERCIAL |
| Destination Images ("Gallery synced from country record") | `shared.v_destination_photos` for destinations whose country = this country | CONTENT (CIS) |

### Destination

| UI field | ERD / source | Class |
|---|---|---|
| Destination Name | `shared.destinations.name` (via `destination_profiles.destination_id`) | **GOLDEN** (CIS) |
| Tagline under name ("Urban gateway destination") | missing in ERD (could be derived from `destination_profiles.description` first line) | CONTENT |
| Country | `destination_profiles.country_code` (FK `country_profiles`); CIS has `shared.destinations.country` as **text name**, not ISO | GOLDEN (needs ISO mapping, open per ERD README line 113) |
| Longitude / Latitude / map pin | `shared.destinations.lng / lat` | **GOLDEN** (CIS) |
| Description (optional) | `destination_profiles.description` | **CONTENT** (O7) |
| Address (Edit only) | missing in ERD | not a destination attribute (hotel field leaked in); drop |
| Destination Media / "N files" / thumbnail | `destination_profiles.cover_media_id` + `entity_media(entity_type='destination_profile')`; CIS source `shared.v_destination_photos` (+ `shared.destinations.cover_image_url`) | **CONTENT** |
| Status Active / Inactive | `destination_profiles.status` (`record_status`) | COMMERCIAL |
| Date Added | `destination_profiles.created_at` (or `shared.destinations.created_at`) | system |
| KPI Total / Active / Countries covered | DERIVED counts | DERIVED |

### Staff/identity on these screens
| UI | Source | Class |
|---|---|---|
| Sidebar user "Martha Kent / Super Admin", top-bar avatar | CIS `shared.admin_users` (JWT, O1) + `booking.staff_users.role` | IDENTITY |
| "Super Admin" role | not in `booking.staff_role` (admin, sales, content_creator, + contracting per ADR 0005 d8) | IDENTITY — label to map to `admin` |

---

## Conflicts / decisions

C1. **Country content editing in Booking vs ADR 0004 O7.** Figma lets staff author country Description, FAQ, Festivals and Images
(Add/Edit Country). O7: "All customer-facing content (activities, country text) is authored in CIS. Booking keeps commercial fields only."
ERD v2 still has `description/faqs/festivals/weather/cover_media_id` on `country_profiles` (drafted before O7).
- Option A (recommended): Booking country page is **read-only for content**; Description/FAQ/Festivals/Images are read from a CIS
  view (e.g. `shared.v_country_profiles`, to be defined by CIS) and shown with a "Managed in CIS" label + deep link to the CIS editor.
  Booking edits only `status` (sellable), `area_id`, and other commercial flags. Drop content columns from `country_profiles` in `bk-002`.
- Option B: keep the Figma editor but host it in CIS admin (same UI kit), not in Booking.
- Option C (not recommended): allow editing in Booking → violates ADR 0002/O7, needs an ADR amendment.

C2. **Destination create/edit (name, country, lat/lng) vs CIS golden record.** `shared.destinations` (~1178 rows) is CIS-owned; ERD says
"Name and lat/lng come from shared.destinations; only AAA copy lives here". Figma "Add Destination" creates new places with coordinates.
- Recommended: "Add Destination" in Booking = **pick an existing CIS destination** (searchable select over `shared.destinations`) and attach
  commercial status. Name/country/lat/lng are read-only. Creating a missing place is a request to CIS (link "Request new place in CIS").
- Delete Destination in Booking = delete the `destination_profiles` row only (soft delete / deactivate), never the CIS place. Rename modal
  copy to "Remove from Booking" and block if referenced by trip plans / hotels / trip case items.
- The Bangkok duplicate in mock data shows the risk Booking-created places would cause (same issue as the S236 CIS duplicate-card audit).

C3. **Published vs Active (two badges).** Figma shows both "Published" and "Active" plus an Unpublish flow ("hide from all users and search").
Customer-facing visibility belongs to CIS/TripPlanner (O8: TripPlanner is the front door). ERD `record_status` = active/inactive only.
- Recommended: one Booking flag `status` (active = sellable in Booking quotes/trip plans; inactive = hidden from Booking pickers). Rename the
  Unpublish action to "Deactivate"/"Activate". Publication of the public country page stays in CIS. Remove the "Published/Visibility" badge or
  show CIS publish state read-only.

C4. **Delete Country permanently.** Countries are ISO reference data; trip cases reference `country_profiles.country_code` (`trip_case_countries`).
Recommended: no hard delete; replace with Deactivate. If kept, soft delete + block when referenced.

C5. **Lat/lng on country.** ERD dropped country coordinates ("CIS owns places"). Recommended: do not store; if a map centre is needed, derive from
CIS destinations' bbox. Remove Geography section from Country forms.

C6. **Country identity.** Figma "Country ID" (CTR-xxxx / #CON-yyyy-nnn) contradicts ERD PK `country_code` (ISO). Recommended: show ISO code; no
synthetic ID. Also needs the open ISO mapping for `shared.destinations.country` (text name today) before destination→country joins work (AA-679).

C7. **Media upload in Booking.** Upload dropzones on Country/Destination (Add, Edit, Details) conflict with O7 (photos are content; ERD header:
"photos come from shared.v_tour_photos"; CIS has `shared.v_destination_photos`). Recommended: galleries are read-only from CIS views; remove upload
tiles. If Booking ever needs internal (non-customer) images, use `entity_media` with an `internal` purpose — not in scope now.

C8. **Edit Destination "Address"** is a hotel field leaked into the destination form (sample is a Tokyo hotel address, hotel photos). Drop it.

C9. **Misnamed files**: COUNTRY MANAGAMENT-2/-3 are Hotel Management; hand them to the hotels module spec.

C10. **Copy/consistency fixes** (non-blocking): kebab menu labels (Block User / Delete User / Edit Profile) → entity-specific; "Frequency Asked Question"
→ "Frequently Asked Questions"; "Unpublished Country" → "Unpublish Country"; image limit 10MB vs 5MB; Longitude as select; Festival Month input
vs select; Longitude-before-Latitude order; "Active Suppliers — Moments ago" tile; top-bar title "Templates" on drawers; Indonesia chip wrap.

C11. **Role**: "Super Admin" is not a `staff_role`. Recommended: map to `admin`; geo screens visible to admin + content_creator (read) and
admin (status changes). Confirm in the role matrix.

C12. **Navigation placement**: if C1/C2 Option A is chosen, the Countries/Destination menu entries become thin read+status screens. Option: merge them
into one "Geography" page (country list with expandable destinations), reducing two modules to one.

### Proposed MVP for Booking (if A chosen)
- `/geo/countries`: card grid (CIS name/cover/photo count), status filter, Activate/Deactivate, Export CSV. Details page: CIS content read-only + commercial
  stats (active suppliers, hotels, trip plans in country).
- `/geo/destinations`: table (CIS name/country/lat/lng/photos read-only, Booking status), "Add" = attach CIS destination, Remove = soft-delete profile.
- No content editors, no uploads, no hard deletes.
