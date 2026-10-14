# Figma UI spec — module 03 Trip Cases (AA-Booking staff admin)

Source: `docs/AAA/figma_AAA/` (13 PNGs, all read successfully). Read against ADR 0004 (O1, O7, O8),
ADR 0005, ERD v2 `docs/AAA/erd-v2/booking.dbml`, `apps/AA-Booking/CONTEXT.md` and the applied
`migrations/002_inquiry_intake.sql` (what actually exists on Dev today).

Screens covered:

| # | File | Real subject |
|---|---|---|
| S1 | `TRIP CASES MANAGEMENT.png` | Trip case list |
| S2 | `TRIP CASES  DETAILS.png` | Case detail, tab Overview |
| S3 | `TRIP CASES  DETAILS-1.png` | Case detail, tab Itinerary & Versions |
| S4 | `TRIP CASES  DETAILS-2.png` | Case detail, tab Invoices & Payments |
| S5 | `ADD NEW TRIP 8.png` | Create trip case form |
| S6 | `DELETE TRIP.png` | Delete confirm modal (drawn over the **Trip Templates** list, not over Trip Cases) |
| S7 | `TRIP CHECKS.png` | Trip checks list |
| S8 | `View Details-3.png` | Trip Check Details drawer (drawn over Payments page) |
| S9–S11 | `View Details.png`, `-1`, `-2` | Invoice detail modal in Paid / Pending / Overdue state (Payments module, opened from S4 eye icon too) |
| S12 | `Assigned Trips.png` | Staff profile → Assigned Trips tab (Admins module) |
| S13 | `Assigned Trips-1.png` | Alternate case detail ("workspace" variant, 10-step ERD-like stepper) |

Global shell (all screens): left sidebar (Overview: Dashboard, Admins, End-users, Suppliers, Audit Logs;
Content & Inventory: Countries, Hotels, Destination, Trip Plan Templates, Activities, Itinerary Builder,
Trip Cases; Trip Operations & Sales: Payment & Invoice, Trip Checks, Settings), collapse chevron, footer
user card (avatar, name, role "Super Admin", logout icon). Top bar: page title, notification bell with
unread dot, "Admin" label + avatar.

---

## S1 — Trip Cases list

- **Route:** `/cases`
- **Purpose:** central queue of customer trip requests from inquiry to completion.
- **Header:** title "Trip Cases Management", subtitle "This Module is central to handling individual
  customer trip requests from inquiry to completion…".
- **Toolbar:** search input "Search by ID…" (text, searches case code); button **Export CSV**
  (secondary, download icon); button **+ Create New Trip Case** (primary, → `/cases/new`).
- **Filters row:** `Filter:` date range select (default "Last 30 Days"); `Status:` select (default "All
  Statuses"); `Agent / Sales Reps:` select (default "All"); link **Reset Filters** (red, right).
- **Table columns:** row checkbox + header select-all (bulk select; no bulk action visible) | CASE ID
  (`#TC-2024-089`) | CUSTOMER (avatar or initials fallback "DC", name, email) | LINKED TRIP TEMPLATE
  (template title + template code `#TP-2024-089`) | AGENT (short name, e.g. "Alice.A") | STATUS badge |
  ACTION (arrow button → `/cases/[code]`).
- **Status badges shown:** Draft (grey), In Progress (yellow), Sent (orange), Approved (blue),
  Completed (green), Cancelled (red).
- **Selected row:** highlighted warm background + orange checkbox.
- **Pagination:** "Showing 1 to 4 of 42 entries" (copy bug: 6 rows shown), "1 of 16 pages", Prev / Next.
- **Empty / loading:** not drawn. Spec: kit skeleton rows; empty state "No trip cases match these
  filters" + Reset Filters.
- Note: duplicate case IDs in the mock (`#TC-2024-089` three times) — mock data only; code is unique.

## S2 — Case detail, Overview tab

- **Route:** `/cases/[code]` (default tab `overview`; tabs as `?tab=` or nested `/cases/[code]/itinerary`,
  `/cases/[code]/invoices`).
- **Header bar:** back arrow → `/cases`; breadcrumb "Trip Case - TC-2024-089".
- **Title block:** `#TC-2024-089 - Classic Bali Explorer` + status badge (In Progress); meta row:
  calendar "Oct 12 - Oct 24, 2024 (12 Days)", person "Sarah Jenkins", briefcase "Agent: Mark T.".
  Button **Edit Details** (primary, pencil).
- **Status stepper (8 steps):** 1 New Inquiry (done, green check), 2 Draft (current, green ring),
  3 In progress, 4 Sent, 5 Approved, 6 Booked, 7 Completed, 8 Cancelled. Contradiction: header badge says
  "In Progress" while stepper current = Draft.
- **Tabs:** Overview | Itinerary & Versions | Invoices & Payments.
- **Linked template strip:** "#TC-2024-089 - Classic Bali Explorer Template" + link **Preview** (eye icon).
- **Card "Trip Information"** (map icon, pencil edit button top-right), 2-column read view:
  Template Name, Status ("Published" = template status), Trip Style / Category, Duration ("10 Days/ 9
  Nights"), Description (long text), Country, City, Duration (repeated), Destination ("Ubud, Seminyak,
  Nusa Penida"), Latitude, Longitude, Supplier, Total Amount ("$1,950").
  Data inconsistencies in mock: case dates = 12 days, template = 10 days; Total Amount $1,950 vs version
  $3,200; lat/lng 27.7172, 85.3240 is Kathmandu, not Bali.
- **Card "Customer Profile"** (right column): avatar, name, "ID: TRV-8924", Email, Phone, Past Trips
  ("0 (First time traveler)"), button **View Full Profile** (→ `/customers/[id]`).
- No edit form for "Edit Details" or the Trip Information pencil is drawn — spec must define it (see
  Conflicts).

## S3 — Case detail, Itinerary & Versions tab

- Same header / stepper / tabs as S2.
- **Card "Itinerary & Versions":** `Filter:` date select (Last 30 Days); `Sort by:` select (Newest to
  Oldest); button **+ Export CSV** (outlined orange; icon is "+", likely should be download).
- **Table columns:** checkbox | VERSION ID (`#VI-2024-089`) | NAME ("Classic Bali Explorer VI") |
  DATE SENT ("Oct 01, 2025") | AMOUNT ("$3,200.00") | ACTIONS: eye (view), trash (delete, red), button
  **Send to Customer** (paper-plane).
- Pagination "Showing 1 to 1 of 1 result", "1 of 1 pages", Prev/Next.
- Missing in Figma: "Create version / Open Builder" button (only S13 has it), approved/draft badge per
  version, a delete confirm for versions.

## S4 — Case detail, Invoices & Payments tab

- Same header / stepper / tabs.
- **KPI cards (3):** Total Trip Cost "$3,200.00" + caption "Based on Approved V1" (green trend icon);
  Amount Paid "$0.00" + "0% of total"; Balance Due "$3,200.00" + red "Next payment due: Oct 01".
- **Card "Invoices":** `Filter:` (Last 30 Days), `Sort by:` (Newest to Oldest), button **+ Create
  Invoice** (outlined orange; form not drawn in this module).
- **Table columns:** INVOICE ID (`INV-2025-001`) | DATE SENT | DUE DATE | AMOUNT | STATUS badge
  ("Pending Payment", yellow) | ACTIONS: eye (→ invoice modal S9–S11), trash (red).
- Pagination as above. No payment-schedule (deposit/second/final) or payments list visible.

## S5 — Create New Trip Case

- **Route:** `/cases/new`
- **Header bar:** back arrow; title "Create New Trip Case"; buttons **Cancel** (secondary) and
  **Create Trip Case** (primary).
- **Section "Customer Information":** `Select Customer` — search combobox, placeholder "Search existing
  customer by name or email…" (search icon). Required (implied; ERD `customer_id NOT NULL`). No "create
  new customer" path drawn.
- **Section "Trip Details":** `Trip Plan Template` — select, placeholder "Select trip template".
  Optional per ERD (`trip_plan_id` nullable); label carries no "(Optional)" marker.
- **Section "Assignment & Notes":** `Assigned Agent` — select (default value "Mark T."); `Internal
  Notes (Optional)` — textarea (focused state, orange border; placeholder "Client is interested in
  cultural activities…").
- No visible validation messages, no dates / pax / countries / currency fields.

## S6 — Delete Trip confirm modal

- **Context:** drawn over the Trip Templates list (`/templates`), with a row kebab menu showing View
  Details / Edit Profile / Block User / Delete User (copy pasted from Users).
- **Modal:** warning icon (red circle), title "Delete Trip", body "Are you sure you want to permanently
  delete **Micheal Scott Trip**? This action cannot be undone", buttons **Cancel** (secondary) and
  **Delete Trip** (destructive red).
- Ambiguous target: the text names a customer's trip ("Micheal Scott" = case customer in S1) while the
  backdrop is the template list. Spec it as the generic destructive confirm used for both, with the
  entity name injected.

## S7 — Trip Checks list

- **Route:** `/checks` (sidebar "Trip Checks").
- **Header:** "Trip Checks & Tasks", subtitle "Monitor pre-trip and post-trip tasks to ensure
  operations run smoothly."
- **Tabs with counts:** All Active Trips (42) | Pending Checks (18) | Completed (102).
- **Toolbar:** search "Search by ID…"; button **Export CSV** (primary here, orange).
- **Filters:** `Filter:` (Last 30 Days), `Status:` (All Statuses), `Method` (All Methods — meaning
  unclear, likely copied from Payments), **Reset Filters**.
- **Table columns:** checkbox | TRIP CASE ID (`TC-2025-089`) | CUSTOMER (avatar, name, email) |
  ASSIGNED AGENT | PROGRESS ("3/9 Tasks" + progress bar; orange partial, green full) | STATUS badge
  (Complete green, In Progress yellow) | ACTION arrow (→ drawer S8).
- Mock contradictions: 3/9 marked "Complete", 9/9 marked "In Progress". Spec: status derived from
  progress (all done = Complete).
- Pagination "Showing 1-5 of 42 flows…", "1 of 16 pages".

## S8 — Trip Check Details drawer

- **Route:** drawer over `/checks` (`/checks?case=TC-…`), also reachable from case detail.
- **Header:** "Trip Check Details", subtitle case code (orange link) • customer name; close X.
- **Summary card:** DEPARTURE DATE, ASSIGNED AGENT, DESTINATION ("Bali, Indonesia"), STATUS badge
  (In Progress, solid orange).
- **Checklist Progress:** "80% (12/15)" + bar.
- **Pending Tasks (3):** each row = checkbox, task title, due line ("Due: Oct 10, 2024" with calendar
  icon, or red "Overdue: Oct 5, 2024" with alert icon), assignee chip (avatar + name), kebab menu
  (actions not drawn: likely edit / reassign / delete).
- **Completed Tasks (12):** checked orange checkbox, strike-through title, "Completed: Sep 15, 2024",
  assignee; link "View all 12 completed tasks" (only 3 shown).
- **Footer:** **Close**, **Save Changes** (primary, check icon) — batch save of checkbox toggles.
- Task examples: Send Pre-departure Briefing, Confirm Airport Transfer, Upload Final Itinerary PDF,
  Collect Initial Deposit, Book Flights, Confirm Hotel Accommodations.
- No "add task" control drawn. Count mismatch: list says x/9, drawer says x/15.

## S9–S11 — Invoice detail modal (Paid / Pending / Overdue)

- **Route:** modal; owned by Payments module (`/payments`), reused from S4 eye.
- **Header:** "Invoice INV-2024-1102" + status badge (Paid green / Pending yellow / Overdue red); X.
- **Billed To:** customer name, email, "Trip Case: TC-2024-089". **Dates:** Issue Date, Due Date.
- **Line items table:** DESCRIPTION (title + sub-line "12-day custom itinerary (Oct 12 - Oct 24,
  2024)") | QTY | UNIT PRICE | TOTAL.
- **Totals:** Subtotal, Tax (0%), Total Due.
- **Footer:** **Close**, **Download PDF**, **Send Reminder** (mail), **Mark as Paid** (primary).
  Bug: the Paid state still shows Send Reminder and Mark as Paid — spec hides both when paid.
- Background list (Payments) visible: tabs All Invoices 124 / Pending 18 / Paid 102, KPI "Total Revenue
  (YTD)", "Invoices Sent (This Month)", Record Payment button, row actions eye / pencil / trash. Belongs
  to the Payments module spec.

## S12 — Staff profile, Assigned Trips tab

- **Route:** `/staff/[id]?tab=assigned-trips` (Admins module; listed here because it lists cases).
- **Header:** back; "Users - Sarah Mitchell" + Active badge; avatar, name, role chip "Admin", employee
  code "EMP-2023-091", email, "Since Oct 2023"; buttons block (icon), **Reset Password**, **Edit
  Profile**. Tabs: Overview & Settings | Activity Log | Assigned Trips.
- **Card "Assigned Trip Cases":** `Filter:` (Last 30 Days), `Status:` (All Statuses), `Sort by:`
  (Newest to Oldest).
- **Table columns:** TRIP CASE (title + code `TC-2023-891`) | CUSTOMER (avatar, name, email) | DATES &
  DURATION ("Nov 12 - Nov 26, 2023", "14 Days") | STATUS badge | ACTIONS arrow → `/cases/[code]`.
- **Status badges:** Update (yellow), Created (green), Success (green), Deleted (red) — a third,
  incompatible status vocabulary (looks like audit-event labels).
- Pagination "Showing 1 to 5 of 5 result".

## S13 — Case detail, workspace variant

- **Route:** `/cases/[code]` (alternative layout to S2–S4; reached from S12).
- **Header bar:** back; case title "Vietnam Explorer"; code "TC-2023-891"; dates "Nov 12 - Nov 26, 2023
  (14 Days)"; pax "2 Adults".
- **Stepper (10 steps):** New Inquiry ✓, Discovery ✓, Building (current), Confirmed, Supplier
  Confirming, Invoice Sent, Paid, Pre-Departure, On Trip, Completed. This matches ERD
  `trip_case_status` minus `proposal_sent`, `payment_pending`, `cancelled`.
- **Card "Itinerary Versions"** + **View All** link: rows = version chip (V2, V1), title ("Vietnam
  Explorer - Revised"), badge (Draft grey / Sent to Client yellow), meta ("Last edited by Eleanor Rigby
  • Today at 10:30 AM" or "Sent on Oct 12, 2023 • Waiting for feedback"), action **Open Builder** (draft)
  / **View PDF** (sent).
- **Card "People":** CUSTOMER (avatar, name, email); ASSIGNED SALES (avatar, name, role "Admin / Sales").
- **Card "Trip Details":** DESTINATIONS ("Hanoi, Halong Bay, Hoi An, HCMC"), LINKED TEMPLATE (orange
  link "Essential Vietnam 14D"), BUDGET RANGE ("$4,000 - $5,000 / person").

---

## Data mapping

Legend: **C** = COMMERCIAL (Booking owns, editable), **CT** = CONTENT (CIS owns per ADR 0002 / O7,
read-only in Booking from CIS catalog views), **ID** = IDENTITY (staff = CIS `shared.admin_users` via
O1 + thin `booking.staff_users`; customer = `booking.customers`). "Live" = present in applied bk-001/002.

### Trip case core (S1, S2, S5, S13, S7)

| Field (screen) | ERD table.column | Class | Notes |
|---|---|---|---|
| Case ID `#TC-2024-089` | `trip_cases.code` (live) | C | Live default format is `TC-000123` (sequence); Figma shows `TC-YYYY-NNN`. Decide format. |
| Status badge / stepper | `trip_cases.status` (live, TEXT+CHECK, 13 values) | C | Figma vocab differs (see Conflicts) |
| Dates "Oct 12 - Oct 24" | `trip_cases.start_date`, `end_date` (live) | C | Day count derived |
| "2 Adults" | `trip_cases.pax` (live) | C | No adult/child split in ERD → missing |
| Trip title "Classic Bali Explorer" | missing in ERD (no `trip_cases.title`) | C | Derive from template title / first leg tour title, or add `title` |
| Linked template + code `#TP-…` | `trip_cases.trip_plan_id` → `trip_plans.title`, `sku` | CT (title) / C (link) | `trip_plan_id` not live yet (bk-00x after AA-679) |
| Agent / Assigned Sales | `staff_assignments.staff_user_id` (role `sales`) → `staff_users.name` | ID | Not live; `created_by` only. Needs O1 staff tables |
| Internal Notes (S5) | missing in ERD (`trip_cases` has no notes) | C | Add `trip_cases.internal_notes` or a notes table |
| Customer (search/select) | `trip_cases.customer_id` → `customers.name/email` (live) | ID | |
| Customer avatar | `customers.profile_media_id` → `media_files` | ID | |
| Customer "ID: TRV-8924" | missing in ERD (only uuid) | ID | Add display code or show short uuid |
| Phone, Email | `customers.phone`, `customers.email` (live) | ID | |
| Past Trips "0 (First time…)" | derived: count `trip_cases` where `customer_id` and status `completed` | ID | Read-only |
| Destinations (S13) / Destination (S2) | `trip_case_legs.source_tour_id` → CIS tour; or `trip_plan_destinations` → `shared.destinations.name` | CT | Read-only, CIS golden record |
| Country (S2) | `trip_case_countries.country_code` → `country_profiles.name` | C (link) / CT (name) | Not live (O7/ISO) |
| City (S2) | missing in ERD (replaced by `destination_id`) | CT | Drop field; show destinations |
| Latitude / Longitude (S2) | missing in ERD by design (CIS owns places) | CT | Drop from UI |
| Template Name / Status "Published" / Trip Style / Duration / Description (S2) | `trip_plans.title`, `is_published`, `trip_style`, `duration_days/nights`, `summary` | CT (title, summary, description) / C (`is_published`, `trip_style` on case) | Read-only in case view; `trip_cases.trip_style` (live) is the case's own value |
| Supplier (S2) | `trip_plans.supplier_id` → `suppliers.company_name` | C | Per-case suppliers really live in `supplier_bookings` |
| Total Amount (S2) | missing on `trip_cases` by design; = approved `trip_case_versions.total_price` | C | Show from approved version, read-only |
| Budget Range "$4,000-$5,000 / person" (S13) | missing in ERD; may be in `trip_cases.inquiry_snapshot` (live JSONB) if TripPlanner sends it | C | Add `budget_min/max/currency` or read from snapshot |
| Created by / source | `trip_cases.created_by`, `source_system`, `source_id` (live) | ID / C | Show "From TripPlanner" chip — not in Figma |

### Versions (S3, S13)

| Field | ERD | Class | Notes |
|---|---|---|---|
| Version ID `#VI-2024-089` / V1, V2 | `trip_case_versions.version_number` | C | Display `V{n}`; Figma code format not in ERD |
| Name "Vietnam Explorer - Revised" | missing in ERD (`notes` only) | C | Add `trip_case_versions.title` |
| Date sent | missing (`is_sent_to_customer` bool only) | C | Add `sent_at` |
| Amount | `trip_case_versions.total_price`, `currency` | C | Computed from version items / pricing (ADR 0005) |
| Draft / Sent to Client / Approved badge | `is_sent_to_customer`, `is_approved`, `approved_at` | C | Derived status |
| "Last edited by … • time" | `trip_case_versions.updated_at` + missing `updated_by` | ID | Add `updated_by` or read `audit_logs` |
| "Waiting for feedback" | missing | C | Derived (sent, not approved) |
| View PDF | missing (no `pdf_media_id`) | C | Generate on demand or add `media_files` link |
| Version itinerary items (behind Open Builder) | `trip_case_version_itinerary.*` | C (prices, dates) / CT (activity/hotel/destination text) | Builder is another module |

### Invoices & payments (S4, S9–S11)

| Field | ERD | Class |
|---|---|---|
| Total Trip Cost "Based on Approved V1" | approved `trip_case_versions.total_price` | C |
| Amount Paid / % | sum `payments.amount` via `invoices` | C |
| Balance Due / Next payment due | total − paid; min `payment_schedule.due_date` where status in (scheduled, due, overdue) | C |
| Invoice ID | `invoices.invoice_number` | C |
| Date Sent / Issue Date | `invoices.issued_at` | C |
| Due Date | missing on `invoices`; = `payment_schedule.due_date` (first open) | C |
| Amount | `invoices.amount`, `currency` | C |
| Status (Pending Payment / Paid / Pending / Overdue) | `invoices.status` (draft, sent, partially_paid, paid, cancelled) — "overdue" missing, derive from schedule `overdue` | C |
| Billed To name/email | `customers.name/email` via `trip_cases.customer_id` | ID |
| Line items Description / Qty / Unit / Total | `invoice_items.description`, `quantity`, `unit_price`, `amount` | C (description may quote CIS tour title — snapshot text) |
| Line sub-line "12-day custom itinerary…" | missing (no secondary description) | C |
| Subtotal / Tax (0%) / Total Due | derived; tax missing in ERD (ADR 0005 dec. 10 → `tax_rules`, invoice tax lines) | C |
| Mark as Paid | creates `payments` row (+ evidence) and sets schedule/invoice status | C |
| Send Reminder | `notifications` (+ e-mail, out of scope today) | C |

### Trip checks (S7, S8)

| Field | ERD | Class | Notes |
|---|---|---|---|
| Trip Case ID, Customer | `trip_cases.code`, `customers.*` | C / ID | |
| Assigned Agent | `staff_assignments` (role `ops`/`sales`) | ID | |
| Progress "3/9 Tasks", "80% (12/15)" | derived from tasks — ERD `trip_case_checks` has **6 fixed booleans**, not a task list | C | Mismatch, see Conflicts |
| Task title, due date, overdue, assignee, completed date | missing in ERD | C / ID | Needs `trip_case_tasks(id, trip_case_id, title, due_date, assignee_staff_id, completed_at, completed_by, position)` |
| Departure date | `trip_cases.start_date` | C | |
| Destination "Bali, Indonesia" | CIS `shared.destinations` / country | CT | Read-only |
| Status Complete / In Progress | derived | C | |
| "Method" filter | no meaning in ERD | — | Drop |

### Staff assigned trips (S12)

| Field | ERD | Class |
|---|---|---|
| Name, role chip, email, "Since" | CIS `shared.admin_users` + `booking.staff_users.role`, `created_at` | ID |
| EMP-2023-091 | missing in ERD | ID |
| Reset Password / block | CIS login owns passwords (O1) | ID — not Booking |
| Rows | `staff_assignments` where `staff_user_id` and `unassigned_at IS NULL` → `trip_cases` | C |
| Status Update/Created/Success/Deleted | no ERD equivalent (audit verbs) | — |

---

## Conflicts / decisions

1. **Three status vocabularies vs ERD's 13 values.** S1/S2 use Draft / In Progress / Sent / Approved /
   Booked / Completed / Cancelled (8-step stepper incl. "Cancelled" as a step); S13 uses 10 ERD-like
   steps; S12 uses Update/Created/Success/Deleted. Live DB has the ERD 13 values.
   **Recommend:** keep the 13 DB values; UI shows the S13 stepper (all non-cancelled values, grouped if
   too wide) and a separate "Cancelled" banner, never a stepper step. Badge labels map from DB values
   (e.g. `proposal_sent` → "Proposal sent"). Drop Draft/Booked/S12 verbs. Options: (a) 13 ERD values
   [recommended]; (b) collapse to ~7 display phases mapped from 13 values; (c) adopt Figma's 8 (needs a
   migration and loses ops granularity).
2. **Content edited from the case (O7).** S2 shows template Description, Country, City, Destination,
   Lat/Lng with an edit pencil and "Edit Details". These are CIS content / golden records.
   **Recommend:** Trip Information card is read-only for template/content fields with a "from CIS"
   source tag; drop City/Lat/Lng; "Edit Details" edits only commercial case fields: dates, pax, trip
   style, currency, countries, agent, internal notes, budget. Content changes → link to CIS admin.
3. **Template link vs legs.** S5 makes "Trip Plan Template" the only trip input; ADR 0001/ERD say cases
   from TripPlanner carry `trip_case_legs` (multi-tour chains) and `trip_plan_id` is not live
   (waits AA-679 catalog sync). **Recommend:** form v1 = customer + dates + pax + countries + agent +
   notes; template select optional and hidden until `trip_plans` exist; detail shows legs from
   `trip_case_legs` (CIS tour titles read-only).
4. **Create form too thin.** No dates, pax, countries, currency; no "new customer" path. Most cases
   come from TripPlanner intake (live bk_inquiry_process), so manual create is the exception.
   **Recommend:** add those fields (optional except customer); "+ New customer" inline (name + email
   or phone, unverified lead, same rules as intake). Options: (a) enrich form [recommended]; (b) keep
   Figma minimal and fill on detail page.
5. **Delete trip case.** S6 "permanently delete… cannot be undone". ERD uses soft delete
   (`deleted_at`) and audit logs; money/supplier records hang off cases. **Recommend:** no hard delete;
   "Cancel case" (status `cancelled` + reason) for normal flow, admin-only "Archive" (soft delete) only
   when there are no versions sent/invoices; confirm copy changed accordingly.
6. **Version delete + Send to Customer on any row.** ERD locks the approved version. **Recommend:**
   delete only unsent drafts; Send only on draft/latest; approved version read-only with "Approved"
   badge; FX locked at send (ADR 0005 dec. 5).
7. **"Total Amount" on case and template "Supplier".** ERD deliberately has no price on `trip_cases`;
   ADR 0005 prices come from cost sheets → versions. **Recommend:** show amount from the approved (or
   latest sent) version only; supplier list from `supplier_bookings`, not template.
8. **Invoice status "Overdue" and due date.** Not in `invoice_status`; due date sits on
   `payment_schedule`. **Recommend:** derive Overdue from schedule rows; show schedule (deposit/second/
   final) under the invoice; hide Mark as Paid/Send Reminder when paid; Mark as Paid opens a Record
   Payment form (amount, method, date, evidence upload) rather than a one-click flag. Tax line from
   `tax_rules` (rates still open with accountant) — show "Tax: not configured" until then.
9. **Trip checks model.** Figma = free task list with assignee/due dates (9 or 15 tasks); ERD =
   one row of 6 booleans. **Recommend:** new `trip_case_tasks` table with a default template of tasks
   seeded per case (the 6 ERD checks become seeded tasks). Options: (a) task table [recommended];
   (b) keep 6 booleans and render as fixed checklist without assignees/due dates.
10. **Staff identity screens (S12).** Reset Password / block / EMP code are CIS login concerns (O1:
    staff log in via CIS `shared.admin_users`). **Recommend:** Booking shows Booking role +
    assignments only; Reset Password links to CIS staff admin; no EMP code unless CIS adds it.
11. **Two detail layouts (S2–S4 tabs vs S13 workspace).** **Recommend:** one page: S13 header + stepper
    + People/Trip Details side cards, with tabs Overview / Itinerary & Versions / Invoices & Payments /
    Checks / Activity (audit_logs). Add an "Inquiry" panel showing `inquiry_snapshot` + source
    TripPlanner (not in Figma, needed for intake cases).
12. **Case code format.** Live `TC-000123` vs Figma `TC-2024-089`. Options: (a) keep live format
    [recommended, no migration]; (b) change default to `TC-YYYY-NNNN` (bk migration; codes already
    issued on Dev stay).
13. **"Customer" bulk select / Export CSV.** Checkboxes with no bulk action. **Recommend:** keep
    Export CSV (exports filtered set, audited); drop row checkboxes until a bulk action exists.
14. **Mock data errors to ignore:** duplicate IDs, Kathmandu coordinates for Bali, 12 vs 10 days,
    $1,950 vs $3,200, "Showing 1 to 4" with 6 rows, Complete/In Progress swapped in S7, Paid invoice
    still offering Mark as Paid, S6 kebab menu copied from Users ("Block User").

## Backend dependencies (for slicing)

Live today: `trip_cases` (no trip_plan_id, no notes/title), `trip_case_legs`, `customers`,
`notifications`, `audit_logs`. Needed before this module's UI works end to end: staff identity (O1:
JWT from CIS + `staff_users` + `staff_assignments`) → case list/detail read endpoints (CONTEXT: none
exist yet); then versions/invoices/payments/checks tables (bk-003 per ADR 0004 dec. 7) and catalog
`trip_plans` (AA-679). Suggested first UI slice: S1 list + S13-style detail read-only (legs, inquiry
snapshot, customer, status change with history) + S5 create (enriched).
