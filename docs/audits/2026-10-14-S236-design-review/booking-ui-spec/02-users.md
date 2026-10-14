# Module 02 — Users (staff "Admins" + customer "End-users") — Figma UI spec

Source: `docs/AAA/figma_AAA/` — 20 PNGs (5760×3724, `USER.png` 5760×3924), all read successfully.
Read against: ADR 0004 (O1 staff login via CIS, O6 guest leads, O7 content in CIS, O8 TripPlanner front
door), ADR 0005, ERD v2 `booking.dbml`, AA-Booking `CONTEXT.md`, live migrations `bk-001`/`bk-002`,
contract `inquiry.submitted` v1.1, `shared.admin_users` (db-schema-reference).

Shared shell on every screen: dark left sidebar (logo "Adventure Asia", collapse chevron; groups
OVERVIEW: Dashboard, Admins, End-users, Suppliers, Audit Logs; CONTENT & INVENTORY: Countries, Hotels,
Destination, Trip Plan Templates, Activities, Itinerary Builder, Trip Cases; TRIP OPERATIONS & SALES:
Payment & Invoice, Trip Checks, Settings), footer user card ("Martha Kent / Super Admin" + logout icon).
Top bar: page group title ("User Management" / "Admin Management"), bell with red dot, "Admin" label +
avatar.

Screen inventory:

| File | Screen |
|---|---|
| ADMINS.png | Admin Users list |
| USER.png | Admin Users list + "Invite User" modal |
| BLOCK ADMIN.png | Admin Users list + row kebab menu + "Block User Account" modal |
| USER DETAILS.png (single space) | Admin user detail "Users - Sarah Mitchell" |
| USER MANAGEMENT.png | Customer Directory (no tabs, Export only) |
| USER MANAGEMENT-1/-2/-3.png | Customer Directory tabs: Active Traveler's / Leads / Past Clients (+ "add New Customer") |
| USER MANAGEMENT-4.png | Customer Directory + row action menu |
| DELETE USER.png | Customer Directory (All Users tab) + "Delete User" confirm |
| USER  DETAILS.png (two spaces) | Customer detail — Overview tab |
| USER  DETAILS-1.png | Customer detail — Trip History tab, empty state |
| USER  DETAILS-2.png | Customer detail — Inquiries tab |
| USER  DETAILS-3.png | Inquiry detail (New Inquiry) |
| USER  DETAILS-4.png | Inquiry detail after decline (Declined + toast + reason box) |
| USER  DETAILS-5.png | Inquiry detail + "Trip Case Successful" toast |
| USER  DETAILS-6.png | "Convert to Trip Case" modal |
| USER  DETAILS-7.png | "Decline Inquiry" modal |
| DELETE USER-1.png | Off-module: Suppliers list + "Deactivate Suppplier" confirm (belongs to module Suppliers) |
| DELETE.png | Off-module: Payments & Invoices list + "Delete Payment" confirm (belongs to module Payments) |

---

## A. Staff ("Admins")

### A1. Admin Users list — `ADMINS.png`
- **Route:** `/staff` (sidebar "Admins").
- **Purpose:** list and manage staff accounts and their access level.
- **Header:** title "Admin Users"; subtitle "Facilitates the creation, modification, and oversight of
  administrative user accounts and their access levels."
- **KPI cards (3):** Total Users (142), Total Active Staff (18), Pending Invites (5).
  Note: in `USER.png`/`BLOCK ADMIN.png` the middle card reads "Active Sessions" — label inconsistency.
- **Toolbar:** search "Search by name or email…"; buttons "Export CSV" (secondary, download icon),
  "Add New Admin" (primary, user-plus icon → Invite modal A3).
- **Filters:** "Filter:" date range (Last 30 Days ▾), "Status:" (All Statuses ▾), "Role:" (All Roles ▾);
  "Reset Filters" link (red).
- **Table columns:** [select-all checkbox] · USER (avatar or initials + full name + email) · ROLE (grey
  pill) · STATUS (badge) · LAST ACTIVE (relative "Just now", "Yesterday", "3 days ago", "1 week ago" or
  date "Oct 24, 2024") · ACTIONS (4 icon buttons: view profile, edit, reset password (key), block (⊘ red)).
- **Row selection:** checkbox; selected row highlighted cream + orange checkbox (no bulk-action bar shown).
- **Role values seen:** Super Admin, Admin, Sales, Content Creator.
- **Status badges:** Active (green), Invited (yellow), Suspended (red), Inactive (grey).
- **Footer:** "Showing 1-5 of 42 flows. Use filters to refine results." (copy bug: "flows"),
  "1 of 16 pages", Prev / Next.
- Empty/loading states: none shown.

### A2. Row kebab menu — `BLOCK ADMIN.png` (background)
Items: View Profile, Edit Details, Permissions, Reset Password, Suspend User (red). (The A1 row shows
icon buttons instead of a kebab — two designs of the same actions; pick one.)

### A3. Invite User modal — `USER.png`
- Title "Invite User"; subtitle "Send an invitation to a new team member to join the platform."; ✕ close.
- Fields:
  | Field | Type | Required (visible) | Hint/placeholder |
  |---|---|---|---|
  | First Name | text | not marked | e.g. Sarah |
  | Last Name | text | not marked | e.g. Mitchell |
  | Email Address | email | not marked | user@adventureasia.com (implies company domain) |
  | Phone Number | country-code select (+66 ▾) + text | not marked | 81 234 5678 |
  | Role | select | not marked | "Select a role…"; help "Determines system access level and permissions." |
  | Status | radio Active / Blocked | default Active | — |
- Buttons: Cancel; "Send Invitation" (primary, mail icon).
- No validation errors shown.

### A4. Block User Account modal — `BLOCK ADMIN.png`
- Title "Block User Account"; body "You are about to block **Alexander Adepoju**. This action will
  immediately revoke their access to the portal."
- Red info box: "**Impact:** All task associated with this user will be unaccessible until the
  suspension is lifted." (copy: "tasks", "inaccessible").
- Field: "Blockage Reason" textarea, placeholder "Please provide a reason for this action (e.g., Policy
  violation, Contract expiry)…" — required not marked.
- Buttons: Cancel; "Block User" (destructive red).
- Terminology clash: menu says "Suspend User", modal says "Block", badge says "Suspended".

### A5. Admin user detail — `USER DETAILS.png`
- **Route:** `/staff/[id]`.
- **Breadcrumb bar:** ← back · "Users - Sarah Mitchell" · status badge "Active" (green, check icon).
- **Header:** avatar, name, role pill "Admin"; meta: "# EMP-2023-091" (staff id), mail icon + email,
  calendar "Since Oct 2023".
- **Header actions:** block icon button (⊘ red, → A4), "Reset Password" (key icon), "Edit Profile"
  (primary, pencil).
- **Tabs:** Overview & Settings (active) · Activity Log · Assigned Trips (only the first tab drawn).
- **Card "User Details":** Phone Number (+44 20 7123 4567), Staff ID (EMP-2023-091), ROLE (Sales),
  Last Active (Just now).
- Inconsistency: header pill says "Admin", card says ROLE "Sales".
- Not drawn: Edit Profile form, Permissions screen, Reset Password confirm, Activity Log tab, Assigned
  Trips tab.

---

## B. Customers ("End-users")

### B1. Customer Directory — `USER MANAGEMENT.png`, `-1`, `-2`, `-3`, `-4`, `DELETE USER.png`
- **Route:** `/customers` with tab query `?tab=all|active|leads|past` (sidebar "End-users").
- **Header:** title "Customer Directory"; subtitle "Enables comprehensive control over all system users,
  including customer, sales, and content creator accounts." (wrong: this list is customers only).
- **Tabs (variants -1/-2/-3, DELETE USER):** All Users · Active Traveler's · Leads · Past Clients.
  `USER MANAGEMENT.png` and `-4` show no tabs and only Export CSV (older variant).
- **Toolbar:** search "Search by name, email or phone…"; "Export CSV"; "add New Customer" (primary, +)
  — form for it is not drawn.
- **Filters:** "Filter:" Last 30 Days ▾ · "Status:" All Statuses ▾ · "Country" All Countries ▾ ·
  "Reset Filters".
- **Table columns:** [checkbox] · CUSTOMER (avatar/initials + name + email) · CONTACT INFO (phone) ·
  LOCATION (city, country — truncated "London, UK…") · STATUS (badge) · TOTAL TRIP (integer) · ACTION
  (kebab "⋯").
- **Status badges:** New Lead (yellow), Active (green), Past Client (grey). (Tabs filter on these; the
  Leads/Past tab mocks show mixed TOTAL TRIP values that contradict the status, mock data only.)
- **Row action menu (-4):** View Profile (eye) · Create Trip Case (suitcase) · divider · Block Customer
  (red, trash icon — icon mismatch).
- **Delete confirm (DELETE USER.png):** warning icon, "Delete User", "Are you sure you want to
  permanently delete **Emma Watson**? This action cannot be undone." Buttons Cancel / "Delete User"
  (red). Entry point not shown in any menu.
- **Footer:** "Showing 1 to 5 of 124 results", "1 of 16 pages", Prev / Next.
- Empty/loading: not shown.

### B2. Customer detail — `USER  DETAILS.png`, `-1`, `-2`
- **Route:** `/customers/[id]` with tabs `overview | trips | inquiries`.
- **Breadcrumb bar:** ← · "Users - John Doe".
- **Header:** avatar, name, status badge "New Lead"; meta "Customer ID: CUST-84920", pin "New York,
  USA", calendar "Added on Oct 24, 2023".
- **Header actions:** "Edit Profile" (secondary; missing on the Overview variant) · "Create Trip Case"
  (primary).
- **Tabs:** Overview · Trip History (n) · Inquiries (n) — counts in labels.
- **Overview:** card "Contact Information": EMAIL ADDRESS, PHONE NUMBER, LOCATION ("London, United
  Kingdom" — contradicts header "New York, USA"). Card "Recent Activity" (timeline): "Submitted Inquiry
  #INQ-892" + time + quoted message excerpt; "Customer Profile Created" + time.
- **Trip History, empty state:** plane icon, "No trip history", "This customer hasn't completed any
  trips with Adventure Asia yet.", button "+ Create First Trip Case". Populated table not drawn.
- **Inquiries tab:** card "Recent Inquiries"; Filter (Last 30 Days ▾), Sort by (Newest to Oldest ▾).
  Columns: INQUIRY ID (INQ-3029) · DATE RECEIVED · DESTINATION ("Japan (Kyoto & Tokyo)") · EST. TRAVEL
  DATES ("Spring 2024") · PARTY SIZE ("2 Adults") · STATUS (badge "New Inquiry") · ACTIONS (→ arrow to
  B3). Footer "Showing 1 to 1 of 1 result", pager.

### B3. Inquiry detail — `USER  DETAILS-3.png`, `-4`, `-5`
- **Route:** `/inquiries/[id]` (breadcrumb "User Profile - Inquiry Details"; reachable from customer).
- **Header:** "Inquiry INQ-3029" + badge; "Received on Oct 24, 2023 at 14:30 PM via Web Form" (copy:
  "14:30 PM").
- **Actions (New Inquiry):** "✕ Decline" (→ B5) · "Convert to Trip Case" (primary → B4).
  **Actions (Declined):** "Reopen Inquiry" (rotate icon) only.
- **Card "Travel Request Details":** Destination · Estimated Travel Dates ("Spring 2024 (Approx.
  April)") · Duration ("10 - 14 Days") · Party Size ("2 Adults") · Estimated Budget ("$10,000 -
  $15,000 USD total") · Travel Style ("Cultural & Luxury").
- **Card "Client Message & Preferences":** free-text quote box. When declined: red box "Declined
  Reason: Budget too low" + notes + "Automated email sent to client."
- **Right card "Client Information":** mini profile (avatar, name, Customer ID), Email, Phone, Location,
  Lead Source ("Organic Search").
- **Status badges:** New Inquiry (yellow), Declined (red).
- **Toasts (top-right, green check, ✕):** "Inquiry Declined — The inquiry has been marked as declined
  and the client was notified." / "Trip Case Successful — The inquiry has been converted to a trip case,
  and the client has been notified". Note `-5` still shows status "New Inquiry" + both buttons after
  conversion (design bug; after convert it should show "Converted" + link to the trip case).

### B4. Convert to Trip Case modal — `USER  DETAILS-6.png`
- Title, ✕; intro "Create a new Trip Case from this inquiry to start building an itinerary for John Doe".
- Fields:
  | Field | Type | Required (visible) | Notes |
  |---|---|---|---|
  | Trip Case Name | text, prefilled "John Doe - Japan Spring 2024" | not marked | |
  | Assign Sales Representative | select (staff) | not marked | value "Sarah Jenkins" |
  | Link Trip Template (Optional) | select | optional | "Select a template to start with"; help "You can also start with a blank itinerary." |
  | Initial Status | select | not marked | value "Discovery" |
  | Internal Notes (Optional) | textarea | optional | |
- Buttons: Cancel · "✓ Create Trip Case" (primary).

### B5. Decline Inquiry modal — `USER  DETAILS-7.png`
- Body: "Are you sure you want to decline inquiry **INQ-3029** from John Doe ? This action cannot be
  easily undone."
- Fields: "Reason for Declining" select (value "Budget too low"; other options not shown) · "Additional
  Notes (Optional)" textarea.
- Buttons: Cancel · "✓ Decline Inquiry" (destructive red).

### Off-module screens matched by the filename filter
- `DELETE USER-1.png` — Suppliers "Supplier Management" (KPIs Total Suppliers 112 / Active Contracts
  105 / Pending Approval 4 / Expiring Soon 3; columns SUPPLIER NAME, type, location, CONTACT PERSON,
  RATING, STATUS Active/Pending, ACTION) with confirm "Deactivate Suppplier" (typo) — body says
  deactivate/reactivate but button reads "Delete User" (copy bug). Spec it in the Suppliers module.
- `DELETE.png` — "Payments & Invoices" (tabs All 124 / Pending 18 / Paid 102 / Overdue 4; KPIs Total
  Revenue YTD, Pending Payments, Overdue Amount, Invoices Sent (This Month); columns INVOICE ID, trip
  case + customer, amount, issued, DUE DATE, STATUS Paid/Pending/Overdue, ACTION view/edit/delete) with
  confirm "Delete Payment … INV-2025-1101" / button "Delete Invoice". Spec it in the Payments module.

---

## Data mapping

Classes: **IDENTITY** (staff or customer identity), **COMMERCIAL** (Booking-owned sales/ops data),
**CONTENT** (CIS-owned, read-only in Booking). "live" = exists in applied `bk-001`/`bk-002`.

### Staff (A1–A5)

| UI field | Maps to | Class |
|---|---|---|
| Full name (First/Last) | `booking.staff_users.name` (ERD, not migrated; O1 = thin profile). `shared.admin_users` has only `username` — **missing** name | IDENTITY |
| Email | `booking.staff_users.email` (ERD) — **missing in `shared.admin_users`** (`username` only) | IDENTITY |
| Phone (+ country code) | **missing in ERD** | IDENTITY |
| Avatar | missing in ERD (`staff_users` has no media FK) | IDENTITY |
| Role (Super Admin/Admin/Sales/Content Creator) | `booking.staff_users.role` enum `staff_role` = admin/sales/content_creator (+ ADR 0005 adds `contracting`); "Super Admin" **missing**; CIS `shared.admin_users.role` (`admin_role`) is the login role | IDENTITY |
| Status Active / Invited / Suspended / Inactive | `staff_users.is_blocked` (bool) + `shared.admin_users.is_active`; Invited/pending **missing** (no invite table) | IDENTITY |
| Last Active | **missing** (no last_login/session table for staff; CIS issues JWT) | IDENTITY |
| Staff ID "EMP-2023-091" | **missing** (only uuid) | IDENTITY |
| Since (date) | `staff_users.created_at` | IDENTITY |
| Block reason | `booking.audit_logs` (`action='staff.block'`, `after.reason`) — no column | IDENTITY |
| KPIs Total Users / Active Staff / Pending Invites | computed (count); Pending Invites missing | IDENTITY |
| Activity Log tab | `booking.audit_logs` where `actor_type='staff' AND actor_id=…` (live table) | IDENTITY |
| Assigned Trips tab | `booking.staff_assignments` (ERD, bk-003, not migrated) | COMMERCIAL |
| Reset Password / Send Invitation | no Booking data — CIS login owns passwords (O1) | IDENTITY |
| Permissions | role matrix in code (ERD README), no table | IDENTITY |

### Customers (B1–B2)

| UI field | Maps to | Class |
|---|---|---|
| Name | `booking.customers.name` (live) | IDENTITY |
| Email | `customers.email` (live) | IDENTITY |
| Phone | `customers.phone` (live) | IDENTITY |
| Avatar | `customers.profile_media_id` → `media_files` (live) | IDENTITY |
| Location (city, country) | `customers.address` (free text, live); separate city/country **missing** → Country filter cannot be exact | IDENTITY |
| Customer ID "CUST-84920" | **missing** (uuid only; trip cases have `code`, customers do not) | IDENTITY |
| Added on | `customers.created_at` | IDENTITY |
| Status New Lead / Active / Past Client | derived, **no column**: Lead = `verified=false` or no trip case past `new_inquiry`; Active = has a trip case in an open status; Past Client = only `completed` cases. Inputs: `customers.verified`, `customers.source` (live), `trip_cases.status` (live) | COMMERCIAL (derived) |
| Blocked | `customers.is_blocked` (live) — no badge drawn for it | IDENTITY |
| Total Trip | `count(trip_cases)` per customer (define: completed only, or all) | COMMERCIAL |
| Merge warning | `customers.needs_merge_review`, `merge_candidate_id` (live) — **not in Figma** | IDENTITY |
| Consent | `customers.contact_consent`, `contact_consent_at` (live) — **not in Figma** | IDENTITY |
| Recent Activity timeline | `booking.audit_logs` (entity customer / trip_case) + `inbox_events` | COMMERCIAL |
| Trip History rows | `booking.trip_cases` where `customer_id` | COMMERCIAL |
| Delete User | `customers.deleted_at` (soft delete; ERD convention) | IDENTITY |

### Inquiries (B2 tab, B3–B5)

Booking has no `inquiries` table: an inquiry is a `booking.inbox_events` row (`contract='inquiry.submitted'`)
that the worker turns into a `trip_cases` row with `status='new_inquiry'` and `inquiry_snapshot` jsonb.

| UI field | Maps to | Class |
|---|---|---|
| Inquiry ID "INQ-3029" | `trip_cases.code` ("TC-000123") or `inbox_events.id`; INQ-prefix **missing** | COMMERCIAL |
| Date received / "via Web Form" | `inbox_events.received_at`, `trip_cases.source_system` (tripplanner/manual) | COMMERCIAL |
| Status New Inquiry / Declined / (Converted) | `trip_cases.status`: `new_inquiry` / `cancelled` (no `declined` value) | COMMERCIAL |
| Destination "Japan (Kyoto & Tokyo)" | derived from `trip_case_legs.source_tour_id` → CIS published tour + `inquiry_snapshot.itinerary.days[].name/destination_id` (CIS `shared.destinations`); `trip_case_countries` not migrated | CONTENT (read) |
| Estimated travel dates | `trip_cases.start_date`/`end_date` (exact dates; "Spring 2024 approx." fuzzy **missing**; contract has no dates) | COMMERCIAL |
| Duration "10-14 days" | derived from legs `day_from/day_to`; range **missing** | COMMERCIAL |
| Party size | `trip_cases.pax` (adults/children split **missing**; contract has no pax) | COMMERCIAL |
| Estimated budget | **missing in ERD and in contract `inquiry.submitted` v1.1** | COMMERCIAL |
| Travel style | `trip_cases.trip_style` (not in contract) | COMMERCIAL |
| Client message | **missing in ERD and contract** | COMMERCIAL |
| Lead source "Organic Search" | `customers.source` = manual/otp/tripplanner_lead (channel only; marketing source **missing**) | IDENTITY |
| Decline reason + notes | **missing** (use `trip_case_status_history.note` — table not migrated — or `audit_logs.after`) | COMMERCIAL |
| Convert: Trip Case Name | **missing** (`trip_cases` has `code`, no `title`) | COMMERCIAL |
| Convert: Sales rep | `booking.staff_assignments` (bk-003, not migrated; needs O1 staff ids) | COMMERCIAL |
| Convert: Trip template | `trip_cases.trip_plan_id` → `trip_plans` (bk-002 ERD part not migrated; templates synced from CIS published tours, AA-679) | COMMERCIAL (template content = CONTENT) |
| Convert: Initial status | `trip_cases.status` (e.g. `discovery`) | COMMERCIAL |
| Convert: Internal notes | **missing** (no notes column on `trip_cases`) | COMMERCIAL |
| "Client was notified" | `booking.notifications` (recipient customer) + e-mail (out of scope today) | COMMERCIAL |

---

## Conflicts / decisions

1. **Staff create/invite/reset-password vs O1.** Figma has Booking invite staff, set status, reset
   passwords. O1: staff log in through CIS `shared.admin_users`; Booking holds a thin profile with the
   Booking role, no password. **Recommend:** `/staff` in Booking manages only the Booking profile (role,
   blocked, phone, display name) for existing CIS logins; "Add New Admin" = pick an existing CIS admin
   user (or deep-link to CIS admin create); Reset Password and invite e-mails live in CIS. Option B:
   build invite + password in CIS first (AA-656) and call it from the shared admin. Needs Nghiệp.
2. **`shared.admin_users` lacks name/email/phone/last-login.** The staff list cannot render USER
   (name+email) or LAST ACTIVE from the CIS login store. **Recommend:** add `name`, `email`, `phone` to
   `booking.staff_users` (thin profile, keyed by `admin_users.id`) and record `last_seen_at` on JWT
   verification; or CIS adds those columns (CIS migration). Decide which owner holds display identity.
3. **Role vocabulary.** Figma: Super Admin/Admin/Sales/Content Creator; ERD: admin/sales/content_creator;
   ADR 0005 adds `contracting`; CIS `admin_role` is separate. **Recommend:** Booking role enum =
   admin, sales, contracting, ops (finance later); drop "Content Creator" from Booking — content creators
   work in CIS (O7/ADR 0002); "Super Admin" = CIS admin, not a Booking role.
4. **Staff status values.** Figma 4 states (Active/Invited/Suspended/Inactive) vs ERD `is_blocked`.
   **Recommend:** Active / Blocked only in Booking (+ Inactive = CIS `is_active=false`, read-only);
   "Invited" only if option B of #1. Unify wording Block vs Suspend → "Block".
5. **Customer directory header copy** says it covers sales and content creator accounts. It is
   customers only; fix copy.
6. **Customer status is derived, not stored.** **Recommend:** compute New Lead / Active / Past Client
   in a view `booking.v_customer_summary` (status, total trips, last trip) from `customers.verified` +
   `trip_cases.status`; add a "Blocked" badge and a "Needs merge review" flag (live columns the Figma
   misses — required by O6 lead handling).
7. **"add New Customer" and "Delete User".** O8 makes TripPlanner the front door and O6 creates leads
   automatically; manual create is still useful for phone/e-mail leads (`source='manual'`). Hard delete
   conflicts with ERD soft delete, audit, and invoices/payments FKs. **Recommend:** keep manual create
   (name + email or phone, consent checkbox); replace "permanently delete" with soft delete (archive)
   allowed only when the customer has no trip case beyond `new_inquiry`; otherwise Block only. GDPR
   erasure = separate anonymise action later.
8. **Inquiry is not a separate entity.** Figma has INQ-xxxx with its own lifecycle (New → Declined /
   Converted) and then a separate Trip Case. In Booking the intake already creates a trip case in
   `new_inquiry`. **Recommend:** "Inquiry" = trip case in `new_inquiry`; "Convert" = status change to
   `discovery` + assign sales + optional template; "Decline" = `cancelled` with reason; "Reopen" =
   back to `new_inquiry`. Needs `trip_case_status_history` (+ note) and a transition rule allowing
   `cancelled → new_inquiry` (or a `declined` status — enum change, decide now). Show `TC-` code, drop
   `INQ-`. Option B: a separate `booking.inquiries` table — rejected-leaning (duplicates intake).
9. **Inquiry fields missing from the contract.** Budget, message, travel dates, party size, travel
   style, duration range, lead source are not in `inquiry.submitted` v1.1. **Recommend:** a v1.2
   additive contract (TripPlanner owns the form) with `preferences{budget_min,budget_max,currency,
   pax_adults,pax_children,travel_window,trip_style,message}` + `utm_source`; Booking stores them in
   `inquiry_snapshot` and promotes pax/dates/style to columns. Until then hide those rows when null.
10. **Trip case name and internal notes** are not in ERD. **Recommend:** add `trip_cases.title` and a
    `trip_case_notes` table (staff, timestamped) in the next `bk-NNN`.
11. **"Client was notified" / "Automated email sent".** E-mail is out of scope in CONTEXT.md.
    **Recommend:** write a `notifications` row now; the e-mail send is a later `bk_*` job; toast copy
    must not claim e-mail until it exists.
12. **Destination text is CIS content.** "Japan (Kyoto & Tokyo)" and the template picker come from CIS
    (published tours, `shared.destinations`) — read-only in Booking (O7, ADR 0002). Templates
    (`trip_plans`) are blocked on AA-679 catalog views; show the template select disabled/hidden until
    then. No content editing in this module — no conflict found beyond that.
13. **Customer location** is one free-text `address`; the Country filter needs `country_code`.
    **Recommend:** add `customers.country_code char(2)` (+ `city`) in the next migration.
14. **Customer ID / Staff ID human codes** (CUST-, EMP-) missing. **Recommend:** `customers.code`
    (sequence like `trip_cases.code`); drop Staff ID (use CIS username).
15. **Design defects to fix before build:** header role "Admin" vs card "Sales"; header "New York" vs
    card "London"; Convert-success still shows "New Inquiry" + buttons; "Block Customer" uses trash
    icon; "flows" in pager; "14:30 PM"; "Deactivate Suppplier" + button "Delete User"; KPI "Total Active
    Staff" vs "Active Sessions"; required-field markers absent on every form.

Not drawn (needed for build): Edit Profile (staff + customer), Add New Customer form, Permissions page,
staff Activity Log / Assigned Trips tabs, populated Trip History, list empty/loading/error states,
bulk actions for the row checkboxes, CSV export column set.
