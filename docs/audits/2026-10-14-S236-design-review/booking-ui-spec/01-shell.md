# AA-Booking staff admin: Figma spec, module 01-shell

Source: `docs/AAA/figma_AAA/`. All 11 matching PNGs were read:
`OVERVIEW.png`, `OVERVIEW-1.png`, `NOTIFICATION.png`, `SETTINGS.png`, `SETTINGS-1.png`, `SETTINGS-2.png`,
`EDIT PROFILE.png`, `RESET PASSWORD.png`, `Activity Log.png`, `AUDIT LOGS.png` and `Group 1410084962.png`.
None failed to load.

Frames are exported at 3x a 1920 px desktop frame (5760 px wide). Pixel sizes below are given at the 1920 frame
(1x). Hex values were sampled from the PNGs with PIL. Where a value is marked "≈", it was read off antialiased text.

Governing decisions: ADR 0004 (O1 staff log in through CIS `shared.admin_users`, `booking.staff_users` = thin
profile with no password; O7 content is authored in CIS; O8 TripPlanner is the customer front door), ADR 0005
(Booking owns prices and suppliers, plus a new `contracting` role with maker-checker) and ERD v2 `booking.dbml`.
CONTEXT.md lists what is built today: bk-001 + bk-002 (customers lead columns, trip_cases, trip_case_legs,
notifications, booking.job). There are no staff tables, no staff endpoints and no frontend yet.

---

## 0. Design tokens / visual language (whole app)

### 0.1 Palette (sampled)

The palette matches the CIS kit (`apps/AA-CIS-App/frontend/app/_kit`, `globals.css`). `--brand-gold` there is
exactly `#DB9628`. Reuse the kit tokens (ADR 0004 decision 1) and do not invent new ones.

| Token | Hex | Where seen | CIS kit equivalent |
|---|---|---|---|
| primary / brand-gold | `#DB9628` | active nav text+icon, primary buttons ("Save Changes", "Export CSV", "Edit Profile"), active tab text + 2px underline, "View All Cases"/"Mark all as read" links, logo, current page in pagination | `--brand-gold` |
| primary-hover | ≈`#B87A1A` | not shown; use kit | `--brand-gold-dark` |
| primary-soft | `#F8ECD6` | gold button edge/halo, unread notification left border tint | (derive: gold 15%) |
| sidebar bg | `#18212A` top → `#111820` bottom (vertical gradient) | sidebar | `--brand-blackblue` `#1F2933` (close) |
| sidebar logo band | gradient `#18212A` → gold `#DB9628` (left→right, top 96 px) | logo area | new: `--sidebar-brand-gradient` |
| sidebar active item bg | `#303941`, radius 10, 1px lighter border | active nav pill | — |
| sidebar divider | `#293037` | above user footer | — |
| sidebar text | ≈`#E5E7EB` items, ≈`#9CA3AF` section labels (uppercase) | nav | — |
| page bg / topbar | `#FFFFFF` | top bar, content area | `--bg-card` |
| page-header band | `#F4F6F8` | title + subtitle band under topbar | (kit `--bg-primary` is warm `#F4F1EC`; Figma is cool grey, so pick one, see C-12) |
| surface/card | `#FFFFFF` with 1px border `#E2E4E9`, radius ≈16, outer "double border" (card inside a 6px padded light frame) | KPI group, table cards, form cards | `--bg-card` |
| table header bg | `#F4F6F8` | table head row | — |
| input bg | `#F4F6F8` (filled style, no visible border) in Settings; white + border `#E2E4E9` in Edit Profile | inputs | — |
| text primary | ≈`#111827` | headings, cell text | `--text-primary` `#1F2933` |
| text secondary | ≈`#6B7280` | subtitles, emails, sub-lines | `--text-secondary` |
| text muted | ≈`#9CA3AF` | placeholders, "Prev" disabled | `--text-muted` |
| danger | `#D9534F` (button) / `#DB5E5A` (text) | "Send Reset Link", "Remove", "Reset Filters", "Requires attentions" | — |
| success | `#1F9D55` | trend up text, toggle on | — |
| overlay | page dimmed to ≈`#6D7C8F` (navy scrim ≈ 55%) | modal backdrop | kit Modal |

### 0.2 Status badges (pill, radius full, 4–6px leading dot, 14px medium text)

Tailwind-like soft pairs:

| Variant | bg | text/dot | Used for |
|---|---|---|---|
| neutral | `#F1F5F9` | `#64748B` | Draft |
| warning/yellow | `#FEF9C3` | `#A16207` | In Progress, Update (activity log), STATUS (audit) |
| orange | `#FFEDD5` | `#EA580C` | Sent |
| info/blue | `#E0F2FE` | `#075985` | Approved, UPDATE (audit) |
| success/green | `#DCFCE7` | `#166534` | Completed, Created, Success, CREATE, LOGIN, Active |
| danger/red | `#FEE2E2` | `#991B1B` | Deleted, DELETE, BLOCK, Suspended |
| plain grey (no dot) | `#F1F5F9` | `#475569` | role chips ("Admin", "Sales") |
| tag-red solid | `#D9534F` bg, white text, radius 4 | "Recommended" |

Audit-log badges are UPPERCASE. All other badges are Title Case.

### 0.3 Typography

The font is a geometric/grotesk sans, probably Inter or similar. Use the CIS kit font.

| Role | Size (1x) | Weight |
|---|---|---|
| Topbar title | 24 | 500 |
| Page H1 (header band) | 32 | 500 |
| Page subtitle | 18 | 400, secondary |
| Section title ("key System Metric", "Recent Trip Cases", card headings) | 22 | 500 |
| KPI value | 32 | 600 |
| KPI label | 18 | 400, secondary |
| KPI trend line | 16 | 400, coloured + icon |
| Body / table cell | 17–18 | 400 |
| Table header | 15 | 400, UPPERCASE, secondary (Audit Logs header is mixed: "Date & Time" title case and the rest uppercase, so normalise it) |
| Sidebar item | 18 | 400 |
| Sidebar section label | 14 | 400, UPPERCASE, letter-spacing ≈ 0.04em |
| Badge | 14–15 | 500 |
| Helper text | 14 | 400, secondary |

### 0.4 Spacing / layout

- Frame width 1920. Sidebar ≈ 346 px (fixed and full height), with a collapse chevron button (round, 28 px,
  translucent) at the top right of the logo band. Content padding is 32 px left and right.
- Topbar ≈ 96 px tall, white, with a 1px bottom border.
- Page header band ≈ 108 px, holding H1 and subtitle, bg `#F4F6F8` and a bottom border. Detail pages put a back
  arrow, a vertical divider, "Entity – Name" and a status badge in the band. Primary actions sit on the right of
  the band (e.g. Edit Profile: Cancel + Save).
- Cards: 24 px inner padding, radius 16, 24 px vertical gap between cards.
- Base spacing unit is 8 px (gaps of 8, 16, 24, 32).
- Two-column settings layout: a left column ≈ 340 px (section title + description) and a right card with the form.

### 0.5 Components

- **Sidebar nav**: three groups with uppercase labels. The active item is a pill (bg `#303941`) with gold icon
  and text. Icons are line icons at 24 px, stroke 1.5, Lucide-style. The footer has a 48 px avatar, name, role
  (secondary) and a logout icon button (Lucide `LogOut`).
- **Topbar right cluster**: a pill container (border `#E2E4E9`, radius 12) holding a bell icon button (square
  40, radius 10, bordered, with a red unread dot), a 1px vertical dashed divider, the label "Admin" (the current
  role) and a 40 px avatar.
- **Buttons**:
  - primary: gold fill, white text, radius 8, height 48, optional leading icon;
  - secondary: white fill, 1px `#E2E4E9` border, dark text;
  - danger-outline: white, red border, red text ("Remove" in Settings);
  - danger-link: red text only ("Remove" in Edit Profile, "Reset Filters" underlined);
  - danger-solid: `#D9534F` ("Send Reset Link");
  - icon-only square: 44 px, bordered, used for the row actions and the "block" circle-slash icon.
- **Inputs**: height 48, radius 8, label above (16 px, primary). Read-only fields look disabled (`#F4F6F8` bg,
  muted text). A locked field shows a lock icon on the right plus helper text below.
- **Select / filter dropdowns**: "Filter: [Last 30 Days ▾]", with inline label text before each select. A
  "Reset Filters" link is right-aligned. The search input is 40% width with a magnifier icon and filled bg.
- **Tables**: rounded container with border. Header row on bg `#F4F6F8`. Rows ≈ 100 px tall (two-line cells:
  title + secondary sub-line), with 1px row dividers and vertical column dividers. Leading checkbox column for
  bulk select (checked = red/rose checkbox in Audit Logs). The footer reads "Showing 1 to N of M …" on the left
  and pagination on the right, which comes in two styles: simple ("1 of 16 pages · Prev · Next") or numbered
  (Previous · [1] 2 3 … 24 · Next, current page gold-filled).
- **Avatars**: 48 px circle photo. The fallback is initials ("LG") on light grey.
- **Tabs**: text tabs with a gold 2px underline and gold text when active, and a 1px grey baseline.
- **Toggle**: green `#1F9D55` when on, inside a filled grey row card with title and description.
- **Modal**: centred, ≈ 730 px wide, radius 16, header bg `#F4F6F8` with a title (24 px) and a close X. Body
  padding 32. Footer right-aligned Cancel (secondary) + action button. Gold outline glow around the modal.
- **Radio card**: a bordered card with a radio. When selected it gets a red border and a faint red bg, with
  title, inline tag and description.
- **Notification popover**: anchored to the bell, ≈ 500 px wide, with title + "Mark all as read" (gold link).
  Unread items have a gold left border and grey bg. Each item has a 56 px round icon (gold circle with white
  glyph, or an actor avatar), a title, a 2-line message in dark text with entity codes in bold, and a timestamp
  (gold when unread). The footer link is "View all notifications".
- **Activity row icon**: a 44 px light-grey square holding a glyph (edit, plus, log-in, trash).
- **Empty / loading states**: **none are drawn in this module's frames.** Use the CIS kit DataTable skeleton and
  empty-state primitives (see C-13).
- **`Group 1410084962.png`**: a full-bleed blurred cream/gold gradient (white centre, gold top-right corner) at
  8784×4940. It is a background asset, most likely for the login / auth splash. No login screen exists in the
  set, and login is in CIS anyway (O1).

### 0.6 Sidebar nav (in order, as drawn)

| # | Group | Label | Icon (Lucide guess) | Proposed route |
|---|---|---|---|---|
| 1 | OVERVIEW | Dashboard | `LayoutGrid` (2×2 grid) | `/` (or `/dashboard`) |
| 2 | OVERVIEW | Admins | `Shield` | `/staff` |
| 3 | OVERVIEW | End-users | `Users` | `/customers` |
| 4 | OVERVIEW | Suppliers | `Store` | `/suppliers` |
| 5 | OVERVIEW | Audit Logs | `ClipboardList` | `/audit-logs` |
| 6 | CONTENT & INVENTORY | Countries | `Globe` | `/countries` |
| 7 | CONTENT & INVENTORY | Hotels | `Building` | `/hotels` |
| 8 | CONTENT & INVENTORY | Destination | `MapPin`-person (`UserRound` in pin) | `/destinations` |
| 9 | CONTENT & INVENTORY | Trip Plan Templates | `CalendarDays` | `/trip-plans` |
| 10 | CONTENT & INVENTORY | Activities | `Activity` (pulse line) | `/activities` |
| 11 | CONTENT & INVENTORY | Itinerary Builder | `Map` (folded map) | `/itinerary-builder` |
| 12 | CONTENT & INVENTORY | Trip Cases | `Briefcase` | `/cases` |
| 13 | TRIP OPERATIONS & SALES | Payment & Invoice | `CreditCard` | `/payments` |
| 14 | TRIP OPERATIONS & SALES | Trip Checks | `SquareCheck` | `/trip-checks` |
| 15 | TRIP OPERATIONS & SALES | Settings | `Settings` (gear) | `/settings` |

The footer shows the signed-in staff member (avatar, "Martha Kent", "Super Admin") and logout.

Recommended re-grouping (see C-1 and C-10): "Trip Cases" is the core sales object and belongs under TRIP
OPERATIONS & SALES, not CONTENT. "Settings" is personal and belongs in the avatar menu or footer, not in sales
operations. The Content items (Countries, Destination, Activities) become read-only "Catalog (from CIS)".

---

## 1. Screens

### 1.1 Dashboard (OVERVIEW.png)

- **Route**: `/` (alias `/dashboard`).
- **Purpose**: at-a-glance metrics and pending work "relevant to the user's role" (subtitle text).
- **Layout**: topbar title "Dashboard Overview". Header band: H1 "Dashboard" and the subtitle "Provides an
  at-a-glance overview of key system metrics and pending tasks relevant to the user's role." Then the section
  "key System Metric" (sic), a 4-up KPI card group, and a "Recent Trip Cases" table card.
- **KPI cards** (label / value / trend line):
  1. Total Trip Cases: `248`, with "↗ +12% from last month" in green.
  2. New Inquiries: `15`, with "↗ Requires attentions" in red.
  3. Pending: `$42,500`, with "— Across 8 bookings" in green.
  4. Active Suppliers: `112`, with "↗ 3 pending approval" in amber.
- **Recent Trip Cases table**:
  - header action "View All Cases" (secondary button, gold text) → `/cases`;
  - columns: [checkbox] CASE ID | CUSTOMER (avatar + name + email) | LINKED TRIP TEMPLATE (title + `#TP-2024-089`
    sku) | STATUS (badge) | SALES REP | LAST UPDATE (relative time);
  - 5 rows shown, with no pagination;
  - row click → `/cases/[code]` (implied);
  - status values seen: Draft, In Progress, Sent, Approved, Completed.
- **Empty/loading**: not drawn.

### 1.2 Dashboard with notification popover (OVERVIEW-1.png)

- **Route**: the same page, with the popover opened from the bell. Topbar title reads "Dashboard" here; the two
  frames are inconsistent.
- **Popover**:
  - header "Notifications" + "Mark all as read" link;
  - 4 items: "New Trip Plan Created" (unread, gold briefcase icon), "Payment Received" (unread, gold card icon),
    "Activity Updated" (read, actor avatar), "System Alert" (read, gold warning icon);
  - each item: title, message, timestamp (relative "2 mins ago", "1 hour ago", "Yesterday at 14:30", or an
    absolute date);
  - footer "View all notifications" → `/notifications`.
- **Behaviour**: unread = gold left border + grey bg + gold timestamp. Clicking an item should mark it read and
  navigate to the linked entity (implied).

### 1.3 All Notifications (NOTIFICATION.png)

- **Route**: `/notifications`.
- **Purpose**: view and manage all system alerts, activity updates and messages.
- **Layout**: header band "All Notifications" + subtitle. One card holds a toolbar, a filter row, a list and a
  footer.
- **Toolbar**: search "Search notifications…" on the left, and "✓✓ Mark all as read" (secondary) on the right.
- **Filters**:
  - Filter: date range select (default "Last 30 Days");
  - Status: "All Statuses" (read / unread implied);
  - Type: "All Types" (types below);
  - "Reset Filters" (red link).
- **List items** (6 per page): icon, title, rich message with bold entity codes and amounts, right-aligned
  absolute timestamp ("Oct 10, 2024 at 09:15"), and contextual action buttons:
  - New Trip Plan Created: "Review Plan" (rendered invisible in the export as white-on-grey, a Figma bug) + "Mark
    as Read". Unread.
  - Payment Received: "View Receipt" + "Mark as Read". Unread. The message says "trip status has been
    automatically updated to 'Confirmed'".
  - Activity Updated: "View Activity". The message: "Bob Content updated the details for the activity 'Kyoto
    Walking Tour'. Changes were made to the itinerary schedule and base price."
  - System Alert: "View Error Logs". The message: "Failed to sync with external booking provider API for trip plan
    TP-10038. Automatic retry has been scheduled in 15 minutes."
  - New User Registration: "View Profile". A customer verified via OTP.
  - Trip Plan Status Changed: "View Trip Plan". The message: "Alice Admin changed the status of trip plan TP-10035
    from 'Draft' to 'In Progress'". This item has no icon.
- **Footer**: "Showing 1 to 6 of 142 notifications", "1 of 16 pages", Prev (disabled), Next. The 6 × 16 ≠ 142
  arithmetic is placeholder data.

### 1.4 Settings, General tab (SETTINGS.png)

- **Route**: `/settings` (tab `?tab=general`).
- **Header**: "Settings" with a Lorem-ipsum subtitle (placeholder, needs copy).
- **Tabs**: General | Security. SETTINGS-1 shows a third tab, Notification, so the tab set is inconsistent.
- **Left column**: "Profile Information", "Update your photo and personal details."
- **Form card**:
  - Profile Photo: 112 px avatar, "Upload New" (secondary), "Remove" (danger outline), hint "Recommended:
    400x400px. JPG, PNG, or GIF."
  - First Name: text, editable.
  - Last Name: text, editable.
  - Email Address: read-only, lock icon, helper "Contact system administrator to change your primary email."
  - Role: read-only ("Super Admin").
  - Footer: Discard (secondary), Save Changes (primary).
- **Validation shown**: none apart from the photo hint.

### 1.5 Settings, Notification tab (SETTINGS-1.png)

- **Route**: `/settings?tab=notification`.
- **Content**: an exact duplicate of the All Notifications list (search, Mark all as read, filters, the same 6
  items) with a numbered paginator: Previous [1] 2 3 … 24 Next, "Showing 1 to 6 of 142 notifications".
- **Note**: this is a duplicate of `/notifications`. See C-9.

### 1.6 Settings, Security tab (SETTINGS-2.png)

- **Route**: `/settings?tab=security`.
- **Left column**: "Password", "Update your password to keep your account secure. Use at least 12 characters."
- **Form**:
  - Current Password: password, filled.
  - New Password: password, placeholder "Enter new password".
  - Confirm New Password: password, placeholder "Confirm new password".
  - Info hint: "Password must contain at least one uppercase letter, one number, and one special character."
  - Discard / Save Changes.
- **Validation hints**: length ≥ 12, ≥ 1 uppercase, ≥ 1 digit, ≥ 1 special character, confirmation must match.
- **Note**: conflicts with ADR 0004 O1. See C-2.

### 1.7 Admin – Edit Profile (EDIT PROFILE.png)

- **Route**: `/staff/[id]/edit`.
- **Topbar**: "Admin Management". Sidebar active item: Admins.
- **Header band**: back arrow, "Users - Edit Profile", "Active" badge (green, check-circle icon). Right side:
  Cancel (secondary) and "Save Changs" (primary with save icon; the typo is in the Figma).
- **Card "Personal Information"** (user icon):
  - photo 112 px + "Change Photo" (secondary) + "Remove" (red link), hint "JPG, GIF or PNG. Max size of 2MB.";
  - First Name, Last Name (text);
  - Email Address (text, editable here, unlike in Settings);
  - Phone Number (text, e.g. "+44 20 7123 4567").
- **Card "Role & Access"** (shield icon):
  - Assigned Role: select (value "Admin"; options implied: Super Admin, Admin, Sales, …);
  - Account Status: a toggle row "Active Account – User can log in and perform actions based on their role."
- **Validation**: only the photo type and size hint is shown. Email format and phone format are implied.

### 1.8 Reset Password modal (RESET PASSWORD.png)

- **Route**: a modal over `/staff`. The background is the Admin Users list (ADMINS.png, module 02 presumably).
- **Background context visible**:
  - "Admin Users" with the subtitle "Facilitates the creation, modification, and oversight of administrative user
    accounts and their access levels.";
  - KPIs: Total Users 142, Active Sessions 18, Pending Invites 5;
  - toolbar: search "Search by name or…", Export CSV, "Add New Admin" (primary);
  - filter "Last 30 Days" and Reset Filters;
  - columns: [checkbox] USER (avatar, name, email) | ROLE chip (Sales/Admin) | STATUS (Suspended red, Inactive
    grey) | LAST ACTIVE | row actions (view, edit, reset-key, block);
  - row "more" menu: View Profile, Edit Details, Permissions, Reset Password, Suspend User (red);
  - footer: "Showing 1-5 of 42 flows" (sic) and "1 of 16 pages".
- **Modal**:
  - title "Reset Password" with X;
  - body "Select a method to reset the password for **Alexander Adepoju**";
  - radio card 1 (selected): "Send Reset Link via Email" with a "Recommended" tag and "Sends a secure link to
    alex.a@adventureasia.com. The user will create their own new password.";
  - radio card 2: "Set Temporary Password" with "Manually set a temporary password now. You must communicate this
    password to the user securely." (no input is drawn; one is implied once selected);
  - footer: Cancel and "Send Reset Link" (danger solid; the label presumably switches for option 2).
- **Note**: conflicts with O1. See C-2.

### 1.9 Admin detail – Activity Log tab (Activity Log.png)

- **Route**: `/staff/[id]?tab=activity`.
- **Header band**: back arrow, "Users - Sarah Mitchell", "Active" badge.
- **Profile header**:
  - 80 px avatar, name (32 px), role chip "Admin";
  - meta row: `# EMP-2023-091` (employee code), mail icon + email, calendar icon + "Since Oct 2023";
  - right side: block icon button (red circle-slash), "Reset Password" (secondary, key icon), "Edit Profile"
    (primary, pencil icon).
- **Tabs**: Overview & Settings | Activity Log (active) | Assigned Trips. The other tabs are in other frames
  (`Assigned Trips*.png`, module 02).
- **Card "Recent Activity"**:
  - filters: Filter "Last 30 Days", Status "All Statuses", Sort by "Newest to Oldest";
  - table columns: ACTION (icon tile + title + sub-line "entity code: name") | MODULE | STATUS (badge) | DATE &
    TIME (date + time on two lines);
  - row examples: Updated Trip Case "TC-2023-891: Vietnam Explorer" / Trip Cases / Update; Create New Template
    "TMP-THAI-001: Classic Thailand" / Templates / Created; Logged In "Successful login" / System / Success;
    Deleted Activity "ACT-092: Outdated Trek" / Activities / Deleted; "Wildlife Safari Package TC-2023-895: African
    Savanna Experience" / Trip Cases / Update (placeholder copy, not an Asia trip);
  - status values: Update, Created, Success, Deleted;
  - footer: "Showing 1 to 5 of 5 result", "1 of 1 pages", Prev/Next.

### 1.10 Audit Logs (AUDIT LOGS.png)

- **Route**: `/audit-logs`.
- **Topbar**: "Audit Logs Management". Sidebar active item: Audit Logs.
- **Header**: "Audit Logs" with "This Module provides a comprehensive record of all significant actions performed
  within the Admin Dashboard, crucial for accountability, compliance, and troubleshooting."
- **Toolbar**: search "Search description, action…" and "⤓ Export CSV" (primary, gold).
- **Filters**: Filter (date range, "Last 30 Days"), Modules ("All Modules"), Admin ("All Admins"), "Reset Filters".
- **Table columns**: [checkbox] | Date & Time ("Oct 10, 2024 10:30 AM") | ADMIN (avatar, name, email) | ACTION
  (uppercase badge) | MODULE | DESCRIPTION.
  - Action values: CREATE, UPDATE, BLOCK, STATUS, LOGIN, DELETE.
  - Module values: Payments, Activity, Admin Mgmt, Trip Plan, Auth.
  - Descriptions are human-readable sentences with entity codes ("Recorded new payment PMT-00124 for $500.00",
    "Logged into system from IP 192.168.1.10").
- **Bulk select**: checkboxes exist, but no bulk action is drawn. Probably "export selected".
- **Footer**: "Showing 1 to 10 of 2,481 entries", "1 of 16 pages", Prev/Next. The figures are placeholder
  arithmetic.
- **Row click / detail drawer**: not drawn. A before/after diff drawer is recommended (`audit_logs.before/after`
  exist).

### 1.11 Background asset (Group 1410084962.png)

A blurred cream/gold gradient image with no UI. It is probably the login/splash background. Not used in Booking
if login stays in CIS (O1). It can serve as a decorative background for an empty dashboard or an error page.

---

## 2. Data mapping

Classes:
- COMMERCIAL: owned by Booking.
- CONTENT: owned by CIS (O7). Read-only in Booking, from CIS views.
- IDENTITY: staff or customer.
- SYSTEM: audit, notification or job.

Status as of today: the "Built" column says whether the target table exists after bk-002.

### 2.1 Dashboard

| UI field | ERD table.column | Class | Built? / note |
|---|---|---|---|
| Total Trip Cases (count) | `count(booking.trip_cases) where deleted_at is null` | COMMERCIAL | yes (bk-002) |
| "+12% from last month" | derived: count by `trip_cases.created_at` month | COMMERCIAL | derived |
| New Inquiries | `count(trip_cases) where status='new_inquiry'` (or unprocessed `inbox_events`) | COMMERCIAL | yes |
| Pending $ | `sum(payment_schedule.amount) where status in ('due','overdue')` (or invoices not paid) | COMMERCIAL | bk-003 (not built). Multi-currency sum needs an FX/base-currency rule (ADR 0005 §5: USD base) |
| "Across 8 bookings" | `count(distinct invoices.trip_case_id)` among the pending set | COMMERCIAL | bk-003 |
| Active Suppliers | `count(suppliers) where status='active'` | COMMERCIAL | bk-00x |
| "3 pending approval" | **missing in ERD**. `suppliers` has only `status active/inactive`. ADR 0005 maker-checker implies a draft/pending-publish state, but on rates/contracts, not on suppliers | COMMERCIAL | missing |
| Case ID `TC-1029` | `trip_cases.code` | COMMERCIAL | yes |
| Customer name / email | `customers.name`, `customers.email` | IDENTITY (customer) | yes |
| Customer avatar | `customers.profile_media_id → media_files` | IDENTITY | yes (column), fallback initials |
| Linked Trip Template title | `trip_plans.title` via `trip_cases.trip_plan_id`. Title = CIS tour title when `source_system='cis'` | CONTENT (title from CIS published tour) | `trip_plan_id` **not in bk-002**. For TripPlanner cases the "template" is `trip_case_legs.source_tour_id` (CIS tour), so show the first leg or "Custom" |
| Template code `#TP-2024-089` | `trip_plans.sku` | COMMERCIAL | bk-00x |
| Status badge | `trip_cases.status` (13-value enum) | COMMERCIAL | yes. Figma shows 5 values: see C-6 |
| Sales Rep | `staff_assignments.staff_user_id (role='sales', unassigned_at is null) → staff_users.name` (name really from `shared.admin_users`, O1) | IDENTITY (staff) | bk-003 + O1 |
| Last update | `trip_cases.updated_at` | COMMERCIAL | yes |

### 2.2 Notifications (popover + `/notifications` + Settings tab)

| UI field | ERD | Class | Note |
|---|---|---|---|
| title | `notifications.title` | SYSTEM | yes (bk-002) |
| message (rich, bold codes) | `notifications.message` (plain text) | SYSTEM | rich formatting **missing**. Render from structured params instead (see below) |
| type (filter "All Types", icon) | `notifications.type` (varchar) | SYSTEM | free text. Needs a fixed vocabulary, e.g. `inquiry.new`, `payment.received`, `trip_case.status_changed`, `customer.registered`, `job.failed`, `catalog.changed` |
| read/unread (Status filter, Mark as read, Mark all) | `notifications.read_at` | SYSTEM | yes |
| timestamp | `notifications.created_at` | SYSTEM | yes |
| recipient | `notifications.recipient_type/recipient_id` | IDENTITY | bk-002 has `recipient_id NULL` until O1 (staff queue). Per-user read state needs a recipient, so either fan out a row per staff member or add a `notification_reads(notification_id, staff_id)` table |
| actor avatar ("Bob Content") | **missing in ERD** (`actor_type/actor_id`) | IDENTITY | add `actor_id` |
| linked entity / action buttons (Review Plan, View Receipt, View Activity, View Error Logs, View Profile, View Trip Plan) | **missing in ERD** (`entity_type`, `entity_id`, or `link`) | SYSTEM | add `entity_type`, `entity_id`, `payload jsonb`. The button set derives from type |
| search | full text over title/message | SYSTEM | ILIKE is enough at Dev scale |

### 2.3 Settings (own profile) and Admin Edit Profile / Detail

| UI field | ERD | Class | Note |
|---|---|---|---|
| First Name / Last Name | `staff_users.name` (single) and CIS `shared.admin_users` | IDENTITY (staff) | ERD has one `name`. O1: the name is owned by CIS `admin_users`, so it is read-only in Booking or edited through a CIS endpoint |
| Email (locked in Settings, editable in Edit Profile) | `shared.admin_users.email` (`staff_users.email` copy) | IDENTITY | owned by CIS (O1) |
| Phone Number | **missing in ERD** (`staff_users` has no phone) | IDENTITY | CIS `admin_users` to confirm |
| Profile photo | **missing in ERD** for staff (`media_files.uploaded_by` only) | IDENTITY | add `staff_users.profile_media_id` or use the CIS avatar |
| Role ("Super Admin", "Admin", "Sales") | `staff_users.role` enum `admin/sales/content_creator` | IDENTITY | "Super Admin" **missing**. ADR 0005 adds `contracting`, so the enum is stale. Booking role ≠ CIS role (O1: Booking role on the thin profile) |
| Account Status toggle / Active badge / Block button | `staff_users.is_blocked` | IDENTITY | blocking login is a CIS concern (it issues the JWT). Booking can only deny `aud=booking` access |
| Suspended / Inactive statuses (list) | only `is_blocked` boolean | IDENTITY | "Inactive" **missing** (3 states in Figma vs 2 in ERD; Inactive maybe = never logged in or no recent login) |
| Employee code `EMP-2023-091` | **missing in ERD** | IDENTITY | drop it, or add `staff_users.employee_code` |
| "Since Oct 2023" | `staff_users.created_at` (or `admin_users.created_at`) | IDENTITY | yes |
| Last active / Active Sessions / Pending Invites (list KPIs) | **missing** (sessions and invites live in CIS auth) | IDENTITY | CIS only |
| Password fields, Reset Password modal | none in Booking (O1: no password) | IDENTITY | CIS `admin_users` |
| Assigned Trips tab | `staff_assignments` | COMMERCIAL | bk-003 |

### 2.4 Activity Log (per staff) and Audit Logs

| UI field | ERD | Class | Note |
|---|---|---|---|
| Date & Time | `audit_logs.created_at` | SYSTEM | yes (bk-001) |
| Admin (avatar, name, email) | `audit_logs.actor_id` (+ `actor_type='staff'`) → staff profile / `admin_users` | IDENTITY | yes (no FK; join at read) |
| Action badge (CREATE/UPDATE/DELETE/STATUS/BLOCK/LOGIN) | `audit_logs.action` (varchar) | SYSTEM | vocabulary not fixed. Define an enum-like CHECK |
| Activity "STATUS" column (Update/Created/Success/Deleted) | derived from `action` (it is the action category, not an outcome) | SYSTEM | rename the column to "Action". There is no success/failure field, so "Success" for login is **missing** (`outcome`) |
| Module (Payments, Activity, Admin Mgmt, Trip Plan, Auth) | derived from `audit_logs.entity_type` | SYSTEM | needs a mapping table in code |
| Entity code + name sub-line ("TC-2023-891: Vietnam Explorer") | `entity_type`/`entity_id` + lookup, or snapshot in `after` | SYSTEM | missing `entity_label`. Store a label snapshot at write time so deleted entities still read well |
| Description sentence | **missing** column. Derive from action + entity + before/after | SYSTEM | add a `summary` text column, or render it in code |
| IP address ("from IP 192.168.1.10") | **missing** (`ip`, `user_agent`) | SYSTEM | add if needed. Login events are in CIS, see C-5 |
| Filters: date range, module, admin, status, sort | indexes on `(created_at)`, `(actor_id, created_at)`, `(entity_type, created_at)` | SYSTEM | add indexes |
| Export CSV | read only | SYSTEM | the CIS kit has `csv.ts` |

---

## 3. Conflicts and decisions

| # | Figma says | Rule it hits | Recommended resolution |
|---|---|---|---|
| C-1 | Nav group "CONTENT & INVENTORY" with Countries, Destination, Activities, Hotels, Itinerary Builder, Trip Plan Templates, all with full CRUD (ADD/EDIT/DELETE/UNPUBLISH frames exist in other modules) | **O7 / ADR 0002**: customer-facing content (country text, activity descriptions, destinations, photos) is authored in CIS only | Rename the group "Catalog" (or "Catalog (CIS)"). Countries, Destinations and Activities become **read-only views** of CIS data, with an "Edit in CIS" deep link to the CIS admin. Hotels keep only commercial fields (supplier, rates, room types; ADR 0005) and their descriptions and photos come from CIS or are deferred. Trip Plan Templates = Booking `trip_plans` synced from CIS published tours, with only commercial fields (sku, prices, supplier, publish-for-sale flag) editable. Move "Trip Cases" out of the content group into "Sales & Operations" |
| C-2 | Settings → Security tab (change password); Reset Password modal (email link / temporary password); "Add New Admin", "Pending Invites" | **O1**: staff log in through CIS `shared.admin_users`, and Booking stores no password | Drop the Security tab and the Reset Password modal from Booking. Replace them with a "Manage sign-in in CIS" link (or let the CIS admin own the whole Admins module). Booking's Admins page only edits the **Booking role** on the thin profile `staff_users` and can disable Booking access. Staff creation and invites happen in CIS |
| C-3 | Editable First/Last name, email, phone and photo for staff | O1: identity is in CIS | Name, email and photo are read-only, from CIS. Show "Managed in CIS". If Nghiệp wants editing here, Booking calls a CIS API; it never writes `shared.admin_users` (schema ownership) |
| C-4 | Roles shown: Super Admin, Admin, Sales | ERD enum `admin/sales/content_creator`; ADR 0005 adds `contracting` | Booking roles = `admin`, `sales`, `ops`, `contracting` (+ read-only `viewer`?). "Super Admin" = a CIS-level flag, not a Booking role. `content_creator` has no Booking job once content is in CIS (O7), so drop it. **Needs Nghiệp's choice** |
| C-5 | Activity/Audit logs include "Logged In" / LOGIN events with IP | Login happens in CIS (O1) | Booking's audit shows Booking actions only. Login and IP come from the CIS auth log, if it is surfaced at all. Option: a combined view later |
| C-6 | Trip case statuses on the dashboard: Draft, In Progress, Sent, Approved, Completed | ERD/bk-002: 13 values (`new_inquiry … cancelled`) | Map them to display groups: Draft ← new_inquiry/discovery; In Progress ← building; Sent ← proposal_sent; Approved ← confirmed…paid/pre_departure/on_trip; Completed ← completed; plus Cancelled (missing in Figma). Or show the 13 raw values with colour by group. **Needs Nghiệp's choice** |
| C-7 | Notification "Payment received → trip status automatically updated to Confirmed" | ERD: `confirmed` comes **before** `invoice_sent`/`paid` | Payment moves the status to `paid`, not `confirmed`. The copy follows the state machine. The status-transition trigger (bk-00x) is the source of truth |
| C-8 | Notification "Activity Updated: Bob Content … changed itinerary schedule and **base price**"; "System Alert: failed to sync with external booking provider API" | O7 (content edits are in CIS), ADR 0005 (price is on trip_plan_prices/rates, not on an activity); there is no external booking-provider integration | Notification types are limited to Booking events: new inquiry, status change, payment recorded, invoice due/overdue, supplier booking changed, `booking.job` failed (→ "View job" instead of "View Error Logs"), CIS catalog change affecting a priced plan (`catalog.tour.*`) |
| C-9 | Notifications appear twice: `/notifications` page and a Settings → Notification tab with the same list | duplication | Keep the single `/notifications` page. The Settings → Notification tab becomes **notification preferences** (which types, email on/off) or is removed. **Needs Nghiệp's choice** |
| C-10 | "Settings" sits in the TRIP OPERATIONS & SALES nav group | IA | Move Settings to the avatar menu / sidebar footer |
| C-11 | Dashboard "Active Suppliers – 3 pending approval" | ERD `suppliers.status` active/inactive; ADR 0005 maker-checker is on rates | Either add a supplier `pending` state, or change the hint to "N rate sheets awaiting publish" (ADR 0005 maker-checker). Recommend the latter |
| C-12 | Page-header band is cool grey `#F4F6F8`; the CIS kit background is warm `#F4F1EC`/`#F8F6F2` | ADR 0004 decision 1: copy the CIS kit and brand tokens | Use the CIS kit tokens (warm). The Figma cool greys are treated as approximations. Same font as CIS |
| C-13 | No empty, loading or error states, and no mobile frames | the CIS UI verify rules (aa-ui-verify: desktop/mobile, light/dark) | Use kit DataTable skeleton rows, an empty state ("No trip cases yet: inquiries from TripPlanner appear here"), and toasts for errors. Dark mode comes from the kit. The sidebar collapses to the kit BottomNav on mobile |
| C-14 | Placeholder and typo copy: "key System Metric", "Requires attentions", "Save Changs", Lorem-ipsum subtitle, "42 flows", "African Savanna Experience", years 2023–2025 | — | Fix the copy in the implementation. Do not copy it literally |
| C-15 | The notification "Review Plan" button is white text on grey (invisible) | Figma bug | Render it as a primary gold button |
| C-16 | "Pending $42,500" with no currency context | ADR 0005: multi-currency, USD base | Show the USD-equivalent total with an FX-dated tooltip, or a per-currency breakdown |
| C-17 | Dashboard "Linked Trip Template" for every case | O8/ERD: TripPlanner cases may have no template (`trip_plan_id` null; legs instead) | Show the template if present, else the first leg's CIS tour title + "+N legs", else "Custom" |

## 4. Build-order implication (shell)

1. The shell (sidebar, topbar, page-header band, tabs, tables, badges, modal) is copied from the CIS kit
   (`AdminShell`, `Sidebar`, `Topbar`, `DataTable`, `Modal`, `Drawer`, `Toast`, `tokens.ts`) and re-skinned with
   the Booking nav. The Figma matches the kit's brand gold `#DB9628`, so very little new styling is needed.
2. Blocked by O1 implementation: the staff JWT (`aud=booking`) and the `staff_users` thin profile are needed
   before any staff page can call the API. The CONTEXT.md "no staff endpoints until staff auth" rule still holds.
3. The first useful pages on today's data (bk-002) are: Dashboard (only the Total cases / New inquiries KPIs plus
   the Recent cases table), `/notifications` (needs `recipient_id` or a fan-out decision) and `/audit-logs`
   (bk-001 `audit_logs`). Pending $, Active Suppliers and Sales Rep wait for bk-003 / bk-00x.
