# 04 — Itinerary Builder (AA-Booking staff admin) — UI spec from Figma

Source screens (all 7 read, none failed), folder `docs/AAA/figma_AAA/`:

| # | File | What it shows |
|---|---|---|
| S1 | `ITINERARY BUILDER.png` | Itineraries list (default state, one row selected) |
| S2 | `ITINERARY BUILDER-1.png` | Same list, row "..." menu open |
| S3 | `ITINERARY BUILDER-2.png` | Modal "Send Itinerary to Customer" |
| S4 | `ITINERARY BUILDER-3.png` | Create Itinerary, no template chosen, Day 1 with an empty Evening slot |
| S5 | `ITINERARY BUILDER-4.png` | Create Itinerary, template chosen, Day 1 filled + Day 2 collapsed |
| S6 | `ITINERARY PREVIEW.png` | Itinerary Preview (customer-style rendering + side panels) |
| S7 | `DELETE ITINERARY BUILDER.png` | Confirm dialog "Delete Itinerary" |

Inputs read first: root ADR 0004 (O1 staff login via CIS, O7 content in CIS, O8 TripPlanner front door),
ADR 0005 (pricing, FX lock on send, maker-checker), ERD v2 `booking.dbml`, `apps/AA-Booking/CONTEXT.md`
(bk-001 + bk-002 live; `trip_case_versions*` are planned for `bk-003`; staff tables wait on O1).

Shared chrome (all screens): left nav (Overview: Dashboard, Admins, End-users, Suppliers, Audit Logs;
Content & Inventory: Countries, Hotels, Destination, Trip Plan Templates, Activities, **Itinerary Builder**
(active), Trip Cases; Trip Operations & Sales: Payment & Invoice, Trip Checks, Settings), collapse
chevron, staff card bottom-left (avatar, "Martha Kent", role "Super Admin", logout icon); top bar with page
title "Itinerary Builder", bell (red unread dot), "Admin" label + avatar.

---

## What an "itinerary" is (interpretation)

Page subtitle (S1): *"This module provides the tools necessary to construct and refine detailed itineraries
for trip plans and trip case versions."* Every list row carries a trip case code (`#TC-2024-089`), so in
practice a row = **one itinerary of one trip case version** (`booking.trip_case_versions` +
`trip_case_version_itinerary`). Template (trip plan) itineraries are not listed here. Recommendation in
"Conflicts" C1: this module edits **trip case versions only**; trip-plan itineraries are read-only
(synced from CIS).

---

## S1/S2 — Itineraries list

- **Route:** `/itineraries` (cross-case list of versions). Row deep links go to `/cases/[code]/versions/[n]`
  (builder) and `/cases/[code]/versions/[n]/preview`.
- **Purpose:** find and open itineraries (proposal versions) across all trip cases, by recency, status, agent.
- **Layout regions:**
  1. Page header: H1 "Itineraries" + subtitle.
  2. Card toolbar: search input (left), "Export CSV" (secondary, download icon), "+ Create Itinerary" (primary, orange).
  3. Filter bar: "Filter:" date range select, "Status:" select, "Agent:" select, "Reset Filters" (red link, right).
  4. Table with bulk-select checkbox column.
  5. Footer: "Showing 1 to 4 of 42 entries" · "1 of 16 pages" · Prev / Next.
- **Search:** placeholder "Search by name..." (S1/S2); S3/S7 backgrounds show "Search by user name or email..."
  (inconsistent copy). Proposal: search on trip case code, itinerary/trip title, customer name or email.
- **Filters:**

  | Filter | Control | Values visible | Proposal |
  |---|---|---|---|
  | Date range | select | "Last 30 Days" (default) | Last 7 / 30 / 90 days, All; applies to Last Edited (`updated_at`) |
  | Status | select | "All" | All, Draft, Building, Finalized (see badge note) |
  | Agent | select | "All" | All + staff with an assignment (`staff_assignments`, role sales) |
  | Reset Filters | link | — | clears search + 3 filters |

- **Table columns:**

  | Column | Content (example) | Notes |
  |---|---|---|
  | ☐ (checkbox) | header = select-all (shows indeterminate "–"); row checkbox; selected row tinted (row 3) | No bulk action button is visible anywhere — selection has no visible purpose (see C9) |
  | TRIP CASE / CUSTOMER | Title "Classic Bali Explorer"; sub-line "#TC-2024-089 • Sarah Jenkins" | Customer name optional: rows 4–5 show only the code |
  | DESTINATION | "Ubud, Seminyak" / "Tokyo, Hakone, Kyoto" / "Japan" / "Indonesia" | Mixed granularity: places or country |
  | Dates & Duration | "Oct 12 - Oct 24, 2025" + "12 Days" | Note: Oct 12–24 is 13 days inclusive; Nov 05–12 shown as 7 Days; Dec 01–15 as 15 Days → duration rule inconsistent in mock |
  | STATUS | badge | see below |
  | Last Edited | "Today, 10:45 AM" / "Yesterday, 4:20 PM" / "Sep 01, 2025" + "by Mark T." / "by System" | relative date for today/yesterday, else date |
  | ACTION | eye icon button (preview) + "..." icon button (menu) | |

- **Status badges (Figma values):** `Draft` (grey dot), `Building` (yellow dot), `Finanlized` (green dot —
  typo for **Finalized**). These are not the ERD `trip_case_status` enum (13 values) and not a version field;
  see C3.
- **Row "..." menu (S2):** "Edit Itinerary" (pencil) · divider · "Duplicate" (copy) · "Send to Customer"
  (paper plane) · divider · "Delete" (red, trash).
  The menu shown behind S3/S7 is a different, wrong one ("View Details / Edit Profile / Block User /
  Delete User" — copied from End-users); ignore it (C10).
- **Empty / loading states:** none visible. Proposal: kit skeleton rows while loading; empty state
  "No itineraries match these filters" + Reset Filters; zero-data state with "Create Itinerary".
- **Pagination:** page size not stated (4 rows shown, "42 entries", "16 pages" — numbers inconsistent);
  propose 20/page, server-side.

## S3 — Modal "Send Itinerary to Customer"

- **Trigger:** row menu "Send to Customer" (S2) or preview header button "Send to Customer" (S6).
- **Route:** modal over current route (no own URL).
- **Regions:** title + close ×; read-only summary card (trip title "Classic Bali Explorer"; "Customer: Sarah
  Jenkins • Dates: Oct 12 - Oct 24, 2024"); form; footer.
- **Form fields:**

  | Label | Type | Prefilled | Required | Validation hint visible |
  |---|---|---|---|---|
  | TO | text/email input | customer email "sarah.j@example.com" | yes (implied) | none visible; propose email format check, default = customer email, allow edit only to another customer contact |
  | SUBJECT | text input | "Your Adventure Asia Itinerary: Classic Bali Explorer" | yes (implied) | none |
  | MESSAGE | textarea (focused, orange ring) | greeting + body + signature with agent name "Mark T." | yes (implied) | none |

- **Buttons:** "Cancel" (secondary), primary **"✓ Create Invoice"** — wrong label for a send action (C5);
  should be "Send".
- No attachment/PDF, version picker, price, currency or validity-date field is shown (C6).

## S4/S5 — Create Itinerary (builder)

- **Route:** `/cases/[code]/versions/new` (create) and `/cases/[code]/versions/[n]/edit` (edit, same layout;
  "Edit Itinerary" from the menu and the pencil in S6 land here).
- **Header bar:** back arrow, title "Create Itinerary"; buttons "Cancel" (secondary), "Save as Draft"
  (secondary), "✓ Create Itinerary" (primary).
- **Section "ITINERARY BUIDER"** (typo for BUILDER):
  - **Trip Plan Template** — select (dropdown), placeholder "Select trip template" (S4). Selected value
    (S5): "#TC-2024-089 - Classic Bali Explorer Template" — the template is labelled with a **trip case**
    code, which is wrong (templates have `sku`); see C2. Choosing a template pre-fills days (S5 shows Day 1
    filled, Day 2 present).
  - Not present but required for a version: **which trip case** (customer), **start date**, **pax**,
    **currency** — S4/S5 have no such field, yet day headers show real dates (C4).
- **Section "EDITOR"** — list of Day cards:
  - **Day header:** drag handle (reorder days), "Day 1", date line "Saturday, Oct 12, 2024" (S4) /
    "Saturday, Oct 12, 2025" (S5); Day 2 "Saturday, Oct 13, 2025" (wrong weekday — Oct 13 2025 is a
    Monday; dates must be computed from start date + day_number). Buttons: delete day (trash), collapse /
    expand (chevron). Day 2 in S5 is collapsed.
  - **Slot cards** inside a day, one per period: **Morning** (sunrise icon), **Afternoon** (sun),
    **Evening** (moon). Each card: drag handle (reorder), period icon + label, line 1 "🕒 duration •
    📍 transfer mode" (e.g. "1 hr • Flight", "1 hr 30 mins • Private Car", "1 hr • Walking"), line 2
    "🏨 hotel name" ("Bali Premium Hotels & Suites"), line 3 free text description ("Welcome to Bali!
    After arriving at Ngurah Rai Airport…", "City tour and local market visit", "Dinner and overnight
    stay"). Edit pencil per slot (opens an editor — **the slot edit form/modal is not in the Figma set**,
    C7).
  - **Empty slot** (S4 Evening): placeholders "--- • ---", "🏨 ---", no pencil; dashed button
    "⊕ Add Activity" inside the day.
  - Slot card does **not** show an activity title — only duration, transfer, hotel, description.
  - Footer: dashed button "📅 Add another Day".
- **Validation hints visible:** none. Proposal: at least 1 day; a day may have 0–3 period slots (one per
  `activity_period`) or allow multiple items per period (Figma shows exactly one per period — decide, C8);
  duration ≥ 0, ≤ 24 h; hotel must belong to the day's destination.
- **States:** S4 = unselected template, one empty slot; S5 = template applied. No loading/saving/error state
  visible.

## S6 — Itinerary Preview

- **Route:** `/cases/[code]/versions/[n]/preview` (row eye icon).
- **Header bar:** back arrow, "Itinerary Preview".
- **Title block:** "#TC-2024-089 - Classic Bali Explorer" + status badge "Building"; meta row: 📅 "Oct 12 -
  Oct 24, 2024 (12 Days)", 👤 "Sarah Jenkins", 📍 "Ubud,Seminyak". Actions: edit (pencil icon button →
  builder), download (icon button → PDF, C6), primary "Send to Customer" (→ S3).
- **Main column — Day sections:** section header "DAY 1" + day title "Arrival in Bali & Transfer to Ubud" +
  date right "Oct 12, 2024"; inner card: big day number "1 / DAY", title repeated, date "Saturday, Oct 12,
  2024", **hero photo**, **narrative paragraph**, then **service items** (icon + title + sub-line):
  - "Private Airport Transfer" — "DPS Airport to Ubud • 1 hr 30 mins" (car icon)
  - "Check-in: Mandapa, a Ritz-Carlton Reserve" — "River Front Suite • 3 Nights" (hotel icon)
  - Day 2 "Ubud Cultural Highlights": "Guided Tegalalang Rice Terrace Trek" — "08:00 AM • 3 hours •
    Private Guide" (pin icon); "Lunch at Swept Away Restaurant" — "13:00 PM • Reservation Included"
    (cutlery icon; "13:00 PM" is a format bug → use 24 h "13:00" or "1:00 PM").
  - Day 2 inner date says "Saturday, Oct 12, 2024" while header says Oct 13 (mock bug).
  Note the preview's item model (transfer / hotel stay / activity with start time / meal) is richer than the
  builder's period slots — the two screens describe different data (C8).
- **Right column panels:**
  1. **Itinerary Overview:** Trip Case "#TC-2024-089", Customer "Sarah Jenkins", Dates "Oct 12 - Oct 24,
     2024 (12 Days)", Destinations "Ubud, Seminyak, Nusa Penida" (differs from header's 2 places), Status
     badge "Building", Assigned Agent "Mark T.".
  2. **Included Elements:** checklist, green check = included ("Luxury Accommodations", "Private Airport
     Transfers", "Daily Breakfast", "3 Guided Private Tours"), grey ⊗ = excluded ("International
     Flights").
  3. **Map Overview:** placeholder box "Interactive Map Preview".
- **No price, total, currency, version number or approval state is shown** anywhere in the preview (C6).
- Empty/loading: none visible.

## S7 — Confirm "Delete Itinerary"

- Modal: warning icon (red), title "Delete Itinerary", body "Are you sure you want to permanently delete
  **Classic Bali Explorer**? This action cannot be undone"; buttons "Cancel" (secondary) and **"Delete
  Trip"** (red; label should be "Delete itinerary"/"Delete version", C10). Background subtitle differs from
  S1: "Manage and Build detailed day - by -day plans for trip cases."
- "Permanently delete" conflicts with soft-delete and version immutability (C9).

---

## Data mapping

Classification: **COMMERCIAL** = owned by Booking (`booking.*`); **CONTENT** = owned by CIS (ADR 0002 /
0004 O7) → read-only in Booking, from CIS catalog/golden-record views; **IDENTITY** = staff (CIS
`shared.admin_users` + `booking.staff_users` thin profile, O1) or customer (`booking.customers`).
ERD tables named here; "bk-003" = planned, not yet migrated.

### List (S1/S2)

| UI field | ERD source | Class |
|---|---|---|
| Itinerary title ("Classic Bali Explorer") | **missing in ERD** for a version. Candidates: `trip_plans.title` via `trip_cases.trip_plan_id` (null for TripPlanner/scratch cases), or CIS tour title via `trip_case_legs.source_tour_id`. Propose `trip_case_versions.title` (commercial label) or derive | CONTENT if derived from tour; COMMERCIAL if a version label |
| Trip case code | `trip_cases.code` | COMMERCIAL |
| Customer name | `customers.name` via `trip_cases.customer_id` | IDENTITY (customer) |
| Destination list | `trip_case_version_itinerary.destination_id` → CIS `shared.destinations.name` (distinct, ordered); country fallback via `trip_case_countries` | CONTENT (names) |
| Dates | `trip_cases.start_date` / `end_date` (or min/max of `trip_case_version_itinerary.date`) | COMMERCIAL |
| Duration "12 Days" | derived: `max(day_number)` or end−start+1 | COMMERCIAL (derived) |
| Status Draft/Building/Finalized | **missing in ERD** as such. Nearest: `trip_case_versions.is_sent_to_customer`, `is_approved`; case-level `trip_cases.status` (`building`, `proposal_sent`, `confirmed`…) | COMMERCIAL |
| Last Edited time | `trip_case_versions.updated_at` | COMMERCIAL |
| Last edited by | **missing in ERD** (`trip_case_versions` has `created_by` only). Use latest `audit_logs` row (actor) or add `updated_by` | IDENTITY (staff) |
| "by System" | `audit_logs.actor_type = 'system'` | — |
| Agent filter | `staff_assignments.staff_user_id` (role `sales`, `unassigned_at IS NULL`) → `staff_users.name` | IDENTITY (staff) |
| Date-range filter | `trip_case_versions.updated_at` | — |
| Export CSV | API export of the filtered list | — |

### Send modal (S3)

| UI field | ERD source | Class |
|---|---|---|
| Summary title / customer / dates | as list | mixed (see above) |
| TO | `customers.email` (default) | IDENTITY (customer) |
| SUBJECT | **missing in ERD** (no outbound message table) — store in `audit_logs.after` or a new `booking.outbound_messages` | COMMERCIAL |
| MESSAGE | **missing in ERD** (same) | COMMERCIAL (per-case correspondence, not catalog content) |
| Send effect | `trip_case_versions.is_sent_to_customer = true`; `trip_cases.status → proposal_sent` + `trip_case_status_history`; `notifications` (recipient_type customer); `audit_logs` | COMMERCIAL |
| FX lock / quote validity (ADR 0005 §5) | **missing in ERD** (`trip_case_versions` has `total_price`, `currency` only; no `fx_rate`, `sent_at`, `valid_until`) | COMMERCIAL |

### Builder (S4/S5)

| UI field | ERD source | Class |
|---|---|---|
| Trip Plan Template select | `trip_plans` (`sku`, `title`) → copies `trip_plan_itinerary` rows into the version; `trip_cases.trip_plan_id` | template = CONTENT-structure synced from CIS (ADR 0005 §1: CIS keeps day/service structure); the copy in the version = COMMERCIAL |
| Trip case / customer / start date | `trip_cases.id`, `customer_id`, `start_date` — **no field on the screen** | COMMERCIAL / IDENTITY |
| Version number | `trip_case_versions.version_number` — **not on screen** | COMMERCIAL |
| Day number / order | `trip_case_version_itinerary.day_number` | COMMERCIAL |
| Day date | `trip_case_version_itinerary.date` (derive = start_date + day_number − 1) | COMMERCIAL |
| Period (Morning/Afternoon/Evening) | `trip_case_version_itinerary.activity_period` (`morning`/`afternoon`/`evening`) | COMMERCIAL |
| Order within a period / day | **missing in ERD** (no `position` column; drag-reorder needs one) | COMMERCIAL |
| Duration ("1 hr 30 mins") | `travel_hours numeric(4,1)` (only travel time; activity duration **missing in ERD**) | COMMERCIAL / CONTENT (activity duration comes from CIS atom) |
| Transfer mode ("Flight", "Private Car", "Walking") | `transfer_type varchar` (free text; propose enum/lookup) | COMMERCIAL |
| Hotel ("Bali Premium Hotels & Suites") | `hotel_id` → `booking.hotels.name` | COMMERCIAL (hotel commercial record; hotel description/photos = CONTENT) |
| Slot description text | `trip_case_version_itinerary.note` — or the activity's text via `activity_id` → `activities.description` (CIS-sourced) | CONTENT if activity text; COMMERCIAL only as a short per-case note (C1) |
| Activity (Add Activity) | `activity_id` → `booking.activities` (synced from CIS atoms, `source_system='cis'`) | CONTENT (read-only) |
| Destination of the day | `destination_id` → CIS `shared.destinations` — **no field visible** | CONTENT |
| Location type (start/end/overnight) | `location_type` — **no field visible** | COMMERCIAL |
| Unit price | `trip_case_version_itinerary.unit_price` — **no field visible** | COMMERCIAL |
| Save as Draft / Create | `trip_case_versions` insert (`is_sent_to_customer=false`) | COMMERCIAL |

### Preview (S6)

| UI field | ERD source | Class |
|---|---|---|
| Title "#TC-… - Classic Bali Explorer" | `trip_cases.code` + title (see list) | COMMERCIAL + CONTENT |
| Status badge | see list status | COMMERCIAL |
| Day title ("Arrival in Bali & Transfer to Ubud") | **missing in ERD** (no day-level row). Source should be CIS tour day title (`published_tours` day structure / segment) | CONTENT |
| Day hero photo | **missing in ERD** for a day; CIS `shared.v_tour_photos` / `shared.v_destination_photos` | CONTENT |
| Day narrative paragraph | **missing in ERD**; CIS atom/segment text (`acp_contract.v_active_tour_atoms` via a catalog view) | CONTENT |
| Service item "Private Airport Transfer — DPS Airport to Ubud • 1 hr 30 mins" | `transfer_type` + `travel_hours` + from/to destinations (**from/to missing in ERD**, only one `destination_id`) | COMMERCIAL |
| "Check-in: Mandapa…" — "River Front Suite • 3 Nights" | `hotel_id` → `hotels.name`; room type and nights **missing in ERD** (room type lives in supplier rates, ADR 0005 §2, not yet modelled) | COMMERCIAL |
| "Guided … Trek — 08:00 AM • 3 hours • Private Guide" | `activity_id` → `activities.title`; start time **missing in ERD**; duration **missing**; guide type **missing** | CONTENT (title) + COMMERCIAL (time, guide service) |
| "Lunch at Swept Away Restaurant — 13:00 • Reservation Included" | meal item type **missing in ERD** (no meal/restaurant entity; ADR 0005 §2 lists meal as a rate type) | COMMERCIAL |
| Overview: Trip Case / Customer / Dates | `trip_cases.code`, `customers.name`, `start_date`/`end_date` | COMMERCIAL / IDENTITY |
| Overview: Destinations | distinct `destination_id` → `shared.destinations.name` | CONTENT |
| Overview: Assigned Agent | `staff_assignments` (role sales, active) → `staff_users.name` | IDENTITY (staff) |
| Included Elements (✓ / ⊗) | `trip_plans.what_it_has` / `what_it_does_not_have` (jsonb) on the template only; **missing for a version** | CONTENT (template inclusions from CIS) or COMMERCIAL if per-proposal (C11) |
| Map Overview | lat/lng from CIS `shared.destinations` (ERD stores none in Booking, by design) | CONTENT |
| Download | PDF render — no ERD field; generated file could go to `media_files` | COMMERCIAL |

---

## Conflicts / decisions (Figma vs ADR 0004/0005, ERD, CONTEXT)

| # | Conflict | Options | Recommendation |
|---|---|---|---|
| C1 | **Free-text narratives in Booking.** Builder slots have a free description; preview shows day titles, long narratives and hero photos. ADR 0004 O7 / ADR 0002: all customer-facing content is authored in CIS; Booking keeps commercial fields only. | (a) Day title/narrative/photo come read-only from CIS (tour day / atoms / photo views); staff only pick, order and schedule; per-case `note` is short and commercial (pickup time, room note). (b) Allow free per-proposal narrative in Booking (tailor-made text per customer) as a COMMERCIAL "proposal note", never written back to the catalog. (c) Staff edit text in CIS, Booking re-syncs. | **(a) + a bounded (b)**: CIS text is read-only and rendered by reference; one optional per-day "personal note to customer" (plain text, length-capped, audited) is allowed because it is case correspondence, not catalog content. Needs Nghiệp's call — it extends O7. |
| C2 | **Template editing.** Subtitle says the module also builds itineraries for *trip plans*. ADR 0005 §1: CIS keeps the tour's day/service structure; `trip_plans` are synced from CIS. The template select also labels a template with a trip-case code. | (a) Templates read-only in Booking (synced from CIS); only versions are edited. (b) Allow manual (`source_system='manual'`) templates edited in Booking. | **(a)**; manual templates later only if Ms. Thư needs them. Template label = `sku — title`. |
| C3 | **Status vocabulary.** Badges Draft / Building / "Finanlized" don't exist in the ERD (case status has 13 values; versions have `is_sent_to_customer` / `is_approved`). | (a) Derive a version badge: Draft (not sent), Sent, Approved (locked), Superseded; show the case status separately. (b) Add a version status enum. | **(a)** derived badge, plus the case status chip; fix typo. Add (b) only if a "ready for review" state is needed (maker-checker). |
| C4 | **Builder has no trip case / customer / start date / pax / currency**, yet days show dates. A version cannot exist without a trip case (`trip_case_versions.trip_case_id NOT NULL`). | (a) Create only from inside a case (`/cases/[code]/versions/new`), header shows the case. (b) Add a case picker to the global "Create Itinerary". | **(a)**; the global button opens a case picker then routes to (a). Dates are computed from `trip_cases.start_date`. |
| C5 | **Send modal primary button says "Create Invoice".** Invoices come after approval (`confirmed` → `invoice_sent`); sending a proposal is not invoicing. | — | Label "Send"; invoice creation stays in Payment & Invoice. |
| C6 | **Send without price / FX lock / validity.** ADR 0005 §5: FX is locked when a quote is sent; quotes valid 7–14 days. Neither the builder nor the preview shows price, currency or validity; ERD versions lack `fx_rate`, `sent_at`, `valid_until`. Email sending is out of scope today (CONTEXT). | (a) Send = lock version (price, currency, FX, valid_until) + mark sent + notify in the customer app (My Trips, O8) + email with a link. (b) Email-only with PDF attached. | **(a)**; add a price summary panel to the preview and builder; PDF (download icon) is a secondary export. Add the missing columns in `bk-003`. |
| C7 | **Slot edit form missing.** Pencil per slot and "Add Activity" have no designed modal. | — | Spec a drawer: period, activity (search CIS-synced activities), destination, hotel, transfer type (lookup), travel hours, start time, unit price (sales: read; contracting/rates source per ADR 0005), note. Ask design for it. |
| C8 | **Two item models.** Builder = one slot per period (morning/afternoon/evening); preview = typed items (transfer, hotel stay with nights/room, activity with start time, meal). ERD row has `activity_id` + `hotel_id` + transfer fields in one row, no item type, no position, no start time, no room type/nights, no meal. | (a) Typed items: add `item_type` (transfer/hotel/activity/meal/free), `position`, `start_time`, `duration_hours`, `from_destination_id`, `nights`, `room_type` to `trip_case_version_itinerary`. (b) Keep period slots only and drop the richer preview. | **(a)** in `bk-003`, periods become an optional grouping; it also matches ADR 0005 rate types (hotel, transport, guide, entrance, activity, meal). |
| C9 | **"Permanently delete" + bulk checkboxes.** ERD: soft delete pattern; an approved version is locked; sent versions are customer-visible history. | (a) Delete allowed only for unsent drafts (soft delete + audit); sent/approved versions can only be superseded. (b) Hard delete any. | **(a)**; hide Delete for sent/approved; copy "Delete draft version"; drop row checkboxes until a bulk action exists (or limit to Export selected). |
| C10 | Copy bugs: wrong background menu (End-users actions) in S3/S7, "Delete Trip" label, "ITINERARY BUIDER", "Finanlized", "13:00 PM", wrong weekdays, inconsistent durations/page counts, two different subtitles and search placeholders. | — | Fix in build; don't replicate. |
| C11 | **Included Elements** exist only on `trip_plans` (template). For a tailor-made version they may differ. | (a) Read template inclusions (CIS) read-only. (b) Per-version inclusions list (commercial, because it is what is sold). | **(b)**, seeded from the template; it is part of the commercial offer and must be locked with the quote. |
| C12 | **Staff identity.** "Assigned Agent", "by Mark T.", agent filter, signature in message require staff profiles; `staff_users` not migrated (O1: CIS login + thin profile). | — | Build after O1 slice (CIS JWT `aud=booking`, `staff_users` keyed by `admin_users.id`). Until then this module cannot ship. |
| C13 | **Duplicate** has no ERD meaning. | (a) Duplicate = new version `version_number+1` of the same case (copy rows). (b) Copy to another case. | **(a)** default; (b) later. |
| C14 | **Sequencing.** The module needs `trip_case_versions*` (bk-003), staff identity (O1), catalog sync for activities/hotels/templates (AA-679) and pricing tables (ADR 0005). None exist yet. | — | Treat 04-itinerary as a late slice: after O1 staff auth, AA-679 catalog read model and the first pricing migrations. A read-only preview of a case built from TripPlanner legs (`trip_case_legs`) could ship earlier. |
