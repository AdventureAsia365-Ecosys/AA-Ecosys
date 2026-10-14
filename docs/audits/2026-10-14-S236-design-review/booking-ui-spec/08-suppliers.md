# 08 — Suppliers (Figma → UI spec)

Source: `docs/AAA/figma_AAA/` — 7 PNGs, all read (5760px wide, rendered at 2000px; legible).

| File | What it actually shows |
|---|---|
| `SUPPLIER MANAGEMENT.png` | List page, default state |
| `SUPPLIER MANAGEMENT-1.png` | List page + "Supplier Added Successfully" toast (STATUS column missing, KPI labels differ) |
| `SUPPLIER MANAGEMENT-2.png` | List page + "Supplier Updated Successfully" toast |
| `ADD SUPPLIER.png` | Add form (full page) |
| `EDIT SUPPLIER.png` | Edit form (full page, prefilled) |
| `SUPPLIER  DETAILS.png` (two spaces) | Supplier detail page |
| `DELETE SUPPLIER.png` | **Wrong export**: it is the *Delete User* dialog on *User Management / Customer Directory*, not a supplier dialog |

Shell (all screens): left nav (OVERVIEW: Dashboard, Admins, End-users, **Suppliers**, Audit Logs; CONTENT & INVENTORY:
Countries, Hotels, Destination, Trip Plan Templates, Activities, Itinerary Builder, Trip Cases; TRIP OPERATIONS & SALES:
Payment & Invoice, Trip Checks, Settings), staff card bottom-left ("Martha Kent / Super Admin", logout icon), top bar
with page title "Suppliers", bell icon, "Admin" + avatar. Note: Suppliers sits under OVERVIEW in the nav (not under
inventory). EDIT SUPPLIER highlights "End-users" in the nav (Figma bug; should be Suppliers).

---

## Screen 1 — Supplier list

- **Route:** `/suppliers`
- **Purpose:** browse, filter, export and manage supplier records used for contracting and supplier bookings.
- **Layout regions:**
  1. Page header: H1 "Supplier Management", subtitle "Manages supplier information, ensuring accurate records for
     collaboration and booking."
  2. KPI strip — 3 cards:
     | Card | Value (mock) | Sub-line |
     |---|---|---|
     | Total Suppliers | 112 | green trend "Across 8 countries" |
     | Active Suppliers (variant -1: "Active Contracts") | 105 | green trend "Fully verified" |
     | Deactivated (variant -1: "Inactive") | 4 | amber "— Awaiting document check" |
     Note: 112 ≠ 105 + 4, and list footer says 124 results — mock numbers inconsistent.
  3. Toolbar: search input (placeholder "Search supplies..." — typo, should be "Search suppliers..."); right side
     buttons **Export CSV** (secondary, download icon) and **+ Add Supplier** (primary amber).
  4. Filter row: `Filter:` date range dropdown (default "Last 30 Days"); `Status:` ("All Statuses");
     `Category:` ("All Category"); `Location:` ("All Location"); link **Reset Filters** (red, right).
  5. Table with bulk-select checkbox in header (indeterminate "–" state shown); selected row highlighted cream with
     amber checkbox.
  6. Footer: "Showing 1 to 5 of 124 results", "1 of 16 pages", **Prev** / **Next**.
- **Columns:**
  | Column | Content |
  |---|---|
  | (checkbox) | row select |
  | SUPPLIER NAME | category icon tile (hotel building / boat / car / palm / tent) + name |
  | CATEGORY | Accommodation, Activity, Transport (detail page also shows "Water Activities" — sub-category?) |
  | STATUS | badge — `Active` (green dot) / `Deactivated` (red dot). Missing in variant -1 |
  | LOCATION | "City, Country" (e.g. "Hanoi, Vietnam") |
  | CONTACT PERSON | primary contact name |
  | ACTION | "…" kebab menu (items not shown; infer View / Edit / Deactivate / Delete) |
- **Toasts:** green-bar toast, top-right, with close ×:
  - "Supplier Added Successfully — Supplier has been created and added to the catalog."
  - "Supplier Updated Successfully — Changes to {name} has been saved." (mock says "James Wilson": copy-paste from users; grammar "have been").
- **Bulk actions:** checkbox selection exists but no bulk action bar is drawn.
- **Empty / loading states:** not shown.

## Screen 2 — Add supplier

- **Route:** `/suppliers/new`
- **Purpose:** create a supplier record.
- **Layout:** sub-header with back arrow, title "Add New Supplier", buttons **Cancel** (secondary) and
  **Save Supplier** (primary). Centered single card with three sections.
- **Fields:**
  | Section | Field | Type | Required (visible) | Placeholder / hint |
  |---|---|---|---|---|
  | BASIC INFORMATION | Supplier Name | text | not marked (assume yes) | "Enter suppler name" (typo) |
  | | Category Type | select | not marked (assume yes) | "Select category..." |
  | | Website (optional) | url | explicitly optional | "https://" |
  | | Description | textarea (focus ring shown) | not marked | "Brief description of the supplier and their services..." |
  | CONTACT DETAILS | Primary Contact Person | text | — | "Full name" |
  | | Job Title | text | — | "e.g. Sales Manager" |
  | | Email Address | email | — | "contact@supplier. com" |
  | | Phone Number | tel | — | "e.g. +1 234 567 890" |
  | LOCATION | Street Address | text | — | "Full street address" |
  | | City | select (dropdown) | — | "City name" |
  | | Country | select | — | "Select country" |
  | | State/Provice (typo) | select | — | "Select" |
  | | Postal Code | text | — | "Enter postal code" |
- No asterisks, no inline validation, no error state drawn. Only "Website (optional)" signals optionality, implying all
  others required — unrealistic for postal code / state in BT/MN/TB.
- On save → back to list with "Supplier Added Successfully" toast.

## Screen 3 — Edit supplier

- **Route:** `/suppliers/[id]/edit`
- **Purpose:** edit an existing supplier.
- **Layout:** identical to Add; title "Edit Supplier Profile"; buttons **Cancel** / **Save Changes**. Website field is
  half width here (full width in Add — inconsistency).
- **Prefilled mock:** Hanoi Emerald Waters Hotel / Accommodation / description about "Oceanic Adventures" scuba diving
  (mismatched mock data) / Michael Chen / Operations Manager / m.chen@oceanicadventures.com / +66 81 234 5678 /
  128 Marina Blvd, Suite 4B / Phuket / Thailand / Phuket Province / "Phuket 83150".
- On save → list with "Supplier Updated Successfully" toast.

## Screen 4 — Supplier detail

- **Route:** `/suppliers/[id]`
- **Purpose:** read-only profile with entry points to edit, deactivate, delete and add an activity.
- **Layout:**
  1. Sub-header: back arrow + "Supplier - {name}" (mock shows "Hanoi Emerald Waters Hotel" while body shows "Bali
     Horizon Tours" — mock mismatch).
  2. Hero: H1 supplier name + status badge `Active`; meta line: tag icon + category ("Activity"), pin icon +
     location ("Bali, Indonesia").
  3. Actions (right): **Delete** (red trash icon button), **Deactivate** (ban icon button), **Edit Profile**
     (secondary, pencil), **+ Add Activity** (primary).
  4. Left column cards: **Basic Information** (Description; Category "Water Activities"; Website as amber link) and
     **Location** (Street Address; City; State / Province; Country; Postal Code).
  5. Right column card: **Contact Details** (Primary Contact; Job Title; Email; Phone Number).
- **Not shown but expected for Booking:** contracts, net rates, linked hotels/activities, supplier bookings, bills.
  The detail page is purely an address book.

## Screen 5 — Delete confirm (from mislabelled export)

- **Route:** modal on `/suppliers` or `/suppliers/[id]`.
- The exported PNG shows the generic destructive dialog pattern: warning-triangle icon in red circle, title
  "Delete User", body "Are you sure you want to permanently delete **Emma Watson**? This action cannot be undone.",
  buttons **Cancel** (secondary) / **Delete User** (red). Backdrop dims page.
- Supplier version (inferred): "Delete Supplier" / "Are you sure you want to permanently delete {name}? ..." /
  Cancel / Delete Supplier. The Deactivate (ban) action has no dialog drawn.

---

## Data mapping

ERD: `booking.suppliers` (id, company_name, address, contact_name, contact_email, contact_phone, status, created_at,
updated_at, deleted_at). Enum `booking.record_status` = active | inactive.

| UI field | ERD table.column | Class |
|---|---|---|
| Supplier Name | `booking.suppliers.company_name` | COMMERCIAL |
| Category Type (Accommodation / Activity / Transport / "Water Activities") | **missing in ERD** (needs `service_type` enum aligned with ADR 0005 rate types: hotel, transport, guide, entrance_fee, activity, meal) | COMMERCIAL |
| Website | **missing in ERD** (`website varchar`) | COMMERCIAL |
| Description | **missing in ERD** (`internal_notes text`, see conflicts) | COMMERCIAL (internal) |
| Primary Contact Person | `booking.suppliers.contact_name` | COMMERCIAL (supplier contact data, not staff/customer identity) |
| Job Title | **missing in ERD** (`contact_title`) | COMMERCIAL |
| Email Address | `booking.suppliers.contact_email` | COMMERCIAL |
| Phone Number | `booking.suppliers.contact_phone` | COMMERCIAL |
| Street Address | `booking.suppliers.address` (single varchar) | COMMERCIAL |
| City | **missing in ERD**; recommend `destination_id` → CIS `shared.destinations.id` (read-only golden record), as `hotels`/`activities` do | CONTENT (reference, read-only from CIS) |
| Country | **missing in ERD**; `country_code char(2)` or derived from the destination | CONTENT (reference) |
| State/Province | **missing in ERD** (`region varchar`) | COMMERCIAL |
| Postal Code | **missing in ERD** (`postal_code varchar`) | COMMERCIAL |
| Status badge Active / Deactivated | `booking.suppliers.status` (`active`/`inactive`; label "Deactivated" = `inactive`) | COMMERCIAL |
| Delete | `booking.suppliers.deleted_at` (soft delete) | COMMERCIAL |
| LOCATION column "City, Country" | derived from destination + country | CONTENT (reference) |
| KPI "Across N countries" | count distinct country over suppliers | derived |
| KPI "Active Contracts" (variant) | **missing in ERD** — needs `supplier_contracts` (ADR 0005 decision 2) | COMMERCIAL |
| KPI sub-line "Awaiting document check" | **missing in ERD** — no verification/document state | COMMERCIAL |
| Filter "Last 30 Days" | `booking.suppliers.created_at` (assumed) | — |
| Toast / audit of add/edit/delete | `booking.audit_logs` (entity_type='supplier', actor = staff) | IDENTITY (actor) |
| Logged-in staff "Martha Kent / Super Admin" | CIS `shared.admin_users` via JWT; `booking.staff_users` thin profile (O1) | IDENTITY |
| "+ Add Activity" target | `booking.activities` (no `supplier_id` column today) | CONTENT (activity text owned by CIS, O7) + COMMERCIAL link |

---

## Conflicts / decisions

1. **"+ Add Activity" on the supplier page vs O7.** Activity title/description are customer-facing content, which CIS
   writes (ADR 0002, ADR 0004 O7). `booking.activities` also has no `supplier_id`.
   **Recommendation:** replace with **"+ Add rate / contract"** (ADR 0005 decision 2): pick a CIS-sourced activity
   (or hotel/transport service) and attach net rates. Optionally a "Linked services" tab that lists CIS items
   read-only. Option B: keep a "Link activity" picker (no create) and add `supplier_id` (or a
   `supplier_services` join table).
2. **Supplier Description.** It is not shown to customers, so it does not breach O7, but the mock text reads like
   marketing copy. **Recommendation:** label it "Internal notes", keep it in Booking (`suppliers.internal_notes`),
   never expose it on TripPlanner.
3. **Who may create/edit suppliers.** ADR 0005 decision 8 assigns supplier contracts and rates to a new
   `contracting` role with maker-checker. The ERD enum `staff_role` still has only admin/sales/content_creator, and
   the Figma shows a "Super Admin" doing everything with a single Save. **Recommendation:** gate `/suppliers` write
   actions to `admin` + `contracting`; sales read-only. Supplier profile edits can be single-step; maker-checker
   applies to rates/contracts (not drawn here). The ERD needs `contracting` added to the enum.
4. **Delete = "permanently delete … cannot be undone"** conflicts with the ERD soft delete (`deleted_at`) and with
   referential integrity (supplier_bookings, supplier_bills, hotels, trip_plans reference suppliers).
   **Recommendation:** primary action = Deactivate (`status=inactive`); Delete = soft delete only, blocked (409 with
   reason) when bookings/bills/active contracts exist; copy "This supplier will be archived". The Deactivate dialog
   also needs to be designed.
5. **City / Country as free dropdowns.** CIS owns places (`shared.destinations`). **Recommendation:** City =
   typeahead on CIS destinations (store `destination_id`); Country derived; keep free-text Street / State / Postal as
   commercial address fields. A migration (bk-00x) must add these columns.
6. **Category taxonomy missing.** The Figma uses Accommodation/Activity/Transport plus "Water Activities".
   ADR 0005 rate sheets use hotel/transport/guide/entrance/activity/meal. **Recommendation:** one enum
   `supplier_category` = those six values (a supplier may have several → array or join table); drop
   "Water Activities" or make it a free tag.
7. **Missing commercial core.** Neither list nor detail shows contracts, validity, currency, payment terms,
   cancellation policy or net rates — the main reason Booking owns suppliers (ADR 0005). **Recommendation:** add
   tabs on `/suppliers/[id]`: Profile | Contracts | Rates (Excel upload → validate → review → publish) | Bookings |
   Bills. Needs new Figma or a Claude-designed screen.
8. **KPI inconsistency.** "Active Suppliers" vs "Active Contracts", "Deactivated" vs "Inactive", and "Awaiting document
   check" implies a verification workflow not in any ADR/ERD. **Recommendation:** KPIs = Total, Active, Inactive
   (from `status`), plus "Contracts expiring in 30 days" once contracts exist; drop "document check" unless Ms. Thư
   confirms a supplier verification step.
9. **Export CSV** of supplier contacts is personal data of supplier staff. **Recommendation:** admin/contracting only;
   audit the export in `audit_logs`.
10. **Mislabelled / inconsistent exports:** DELETE SUPPLIER.png is the user dialog; EDIT nav highlight on End-users;
    detail header vs body names differ; STATUS column missing in variant -1; Website width differs between Add and Edit;
    typos ("supplies", "suppler", "Provice", "has been saved"). Treat as design bugs; ask the designer for a real
    Delete/Deactivate Supplier frame or reuse the generic dialog component.
11. **Location filter / "Last 30 Days" filter** on a master-data list is of low value. **Recommendation:** keep
    Status, Category, Country; replace the date filter with sort by updated_at.
