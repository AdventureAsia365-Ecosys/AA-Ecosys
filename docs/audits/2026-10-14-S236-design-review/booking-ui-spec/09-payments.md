# 09 — Payments & Invoices (AA-Booking staff admin) — UI spec from Figma

Source screens: `docs/AAA/figma_AAA/` (all 11 read OK):
`PAYMENT & INVOICE.png`, `PAYMENT & INVOICE-1.png`, `PAYMENT & INVOICE-2.png`, `PAYMENT & INVOICE-3.png`,
`PAYMENT MANAGEMENt.png`, `PAYMENT DETAILS.png`, `CREATE INVOICE.png`, `RECORD PAYMENT.png`,
`EDIT PAYMENT.png`, `CANCEL INVOICE.png`, `SEND REMAINDER.png`.

Read against: ADR 0004 (O1 staff login via CIS, O7 content in CIS, O8 TripPlanner front door),
ADR 0005 (pricing, currency lock, tax rules, maker-checker), ERD v2 `booking.dbml`
(`invoices`, `invoice_items`, `payment_schedule`, `payments`, enums `invoice_status`,
`payment_status`, `payment_kind`), `apps/AA-Booking/CONTEXT.md` (frontend not started).

Notes on the exports themselves:
- `SEND REMAINDER.png` is visually the same frame as `CANCEL INVOICE.png` (a "Delete Payment" dialog
  that names an invoice). There is **no Send Reminder form/preview** in the exports — only the
  "Send Reminder" menu item in `PAYMENT & INVOICE-2.png`. Designer must supply that screen.
- `PAYMENT MANAGEMENt.png` = `PAYMENT & INVOICE-1.png` + a success toast.
- Figma has three tab-bar variants for the same page (see Conflicts C1).
- All copy shows `$` only; no currency selector anywhere (Conflict C4).

Shared shell (all screens): left sidebar (Overview: Dashboard, Admins, End-users, Suppliers,
Audit Logs; Content & Inventory: Countries, Hotels, Destination, Trip Plan Templates, Activities,
Itinerary Builder, Trip Cases; Trip Operations & Sales: **Payment & Invoice** (active), Trip Checks,
Settings), footer user card (name + role "Super Admin" + logout), top bar title "Payment Management",
bell with unread dot, "Admin" label + avatar.

---

## Screen 1 — Payments & Invoices list, Invoice tab

Files: `PAYMENT & INVOICE.png` (tab "Invoice"), `PAYMENT & INVOICE-2.png` (tab "Invoices"/"Pending"
variant + row menu open), background of `CANCEL INVOICE.png` / `RECORD PAYMENT.png` (tab variant
"All Invoices 124 / Pending 18 / Paid 102 / Overdue 4").

Route proposal: `/payments` (default tab) → `/payments?tab=invoices`; per-case view
`/cases/[code]/billing` reuses the same table filtered by `trip_case_id`.

Purpose: list all customer invoices across trip cases; create invoice; reminders; export.

Layout regions:
1. Page header: H1 "Payments Management" (one variant "Payments & Invoices"), subtitle
   "Manage all customer invoices, payments, and financial records."
2. Tabs: `Invoice | Payment` (variant B: `Invoices | Pending`; variant C with count chips:
   `All Invoices (124) | Pending (18) | Paid (102) | Overdue (4)`).
3. KPI strip (4 cards): Total Revenue (YTD) `$1,245,000`; Pending Payments `$84,500`;
   Overdue Amount `$12,400` (red); Invoices Sent (This Month) `24`.
4. Table card: toolbar (search, Export CSV, primary CTA), filter row, table, footer pagination.

Toolbar:
- Search input, placeholder "Search by ID..." (variant: "Search by reference, trip, or user...").
- Button `Export CSV` (secondary, download icon).
- Primary CTA `+ Create Invoice` (variant -2 shows `+ Record Payment` on the invoice tab — inconsistency).

Filters (row): `Filter:` date range select (default "Last 30 Days"); `Status:` select ("All Statuses");
`Method` select ("All Methods" — meaningless for invoices, see C6); link `Reset Filters` (red).

Table columns:
| Column | Content |
|---|---|
| (checkbox) | row select; header tri-state checkbox; selected row tinted |
| INVOICE ID | e.g. `INV-2025-1102` |
| TRIP CASE & CUSTOMER | 2 lines: case code `TC-2025-089` / customer name `Sarah Jenkins` |
| AMOUNT | `$3,200.00` |
| ISSUE DATE | `Oct 1, 2025` |
| DUE DATE | `Oct 15, 2025` |
| STATUS | badge |
| ACTION | eye (view) + `…` menu (variant in CANCEL INVOICE bg: eye, pencil edit, red trash) |

Status badges (invoice): `Paid` (green), `Pending` (yellow), `Overdue` (red).
Row `…` menu: `Send Reminder` (paper-plane), `Download PDF`, divider, `Delete` (red).

Footer: "Showing 1-5 of 42 flows. Use filters to refine results." + "1 of 16 pages" + Prev/Next
(copy bug: "flows"; counts inconsistent).

Bulk actions: checkboxes exist but no bulk action bar is drawn.
Empty / loading states: **not drawn**.

## Screen 2 — Payments list, Payment tab

Files: `PAYMENT & INVOICE-1.png`, `PAYMENT MANAGEMENt.png` (with toast), `PAYMENT & INVOICE-3.png`
(row menu open).

Route proposal: `/payments?tab=payments`.

Same header, tabs (Payment active), KPI strip, toolbar (search "Search by ID...", Export CSV,
primary `+ Record Payment`), filters (Last 30 Days / All Statuses / All Methods / Reset Filters).

Table columns:
| Column | Content |
|---|---|
| (checkbox) | |
| ID | `PMT-00124` |
| TRIP CASE & CUSTOMER | `TC-2025-089` / `Sarah Jenkins` |
| AMOUNT | `$3,200.00` |
| METHOD | `Credit Card`, `Bank Transfer`, `PayPal` |
| DUE DATE | `Oct 15, 2025` |
| PAYMENT TYPE | badge — actually a status: `Paid` (green), `Pending` (yellow), `Failed` (red), `Refunded` (grey/blue) |
| ACTION | eye (→ detail) + `…` menu: `Edit Payment`, `Download PDF`, divider, `Delete` (red) |

Toast (top-right, green check): title "Changes Updated Successfully", body
"Changes to PMT-00124 has been saved." (grammar: "have"), close ×.

Footer pagination same as Screen 1. Empty / loading: not drawn.

## Screen 3 — Payment detail

File: `PAYMENT DETAILS.png`. Route proposal: `/payments/[paymentRef]` (e.g. `/payments/PMT-00124`);
also reachable from `/cases/[code]/billing`.

Header bar: back arrow + breadcrumb `PMT-00124`.
Title row: "Payment PMT-00124" + status badge `Active` (green, check icon — a 5th, unexplained status;
see C5). Actions: trash icon button (red, delete), `Receipt` (download), primary `Edit` (pencil).

Left card "Transaction Information" (2-column definition list):
- Reference ID — `PMT-00124`
- Transaction ID / Receipt No. — `TXN-982374982374`
- Amount — `$500.00` (large)
- Payment Method — card icon + `Credit Card`
- Date & Time — `Oct 10, 2024 at 10:30 AM`
- Linked Invoice — `INV-2025-1102`
- Internal Notes — read-only text block ("Initial deposit ... Processed via Stripe gateway successfully.")

Right card "Related Trip Plan" (external-link icon → trip case): Trip ID `TP-10045` (red link),
Trip Style `Cultural Explorer`, Start Date `Nov 15, 2024`, divider, Total Amount `$3,500.00`.

Right card "Customer" (external-link icon → customer): avatar, name `John Doe`, email, phone
`+1 (555) 123-4567`.

Not drawn: evidence/receipt image preview, schedule instalment (deposit/second/final), audit trail,
who recorded it.

## Screen 4 — Create Invoice (modal)

File: `CREATE INVOICE.png`. Route proposal: modal on `/payments` and on `/cases/[code]/billing`
(pre-selects the case). Opened by `+ Create Invoice`.

Fields:
| Field | Type | Required | Hint / validation visible |
|---|---|---|---|
| Trip Case | searchable select, placeholder "Select Trip Case..." | yes (*) | — |
| Customer | read-only, "Auto-filled from Trip Case" | yes (*) | disabled grey |
| Issue Date | date picker (default today, `Oct 20, 2024`) | yes (*) | — |
| Due Date | date picker (`Nov 4, 2024`, i.e. +15 d) | yes (*) | should be ≥ issue date (not shown) |
| Line Items table | repeatable rows: DESCRIPTION (text, "Add description..."), QTY (number, default 1), UNIT PRICE (money, `$ 0.00`), TOTAL (computed), trash icon | ≥1 row implied | — |
| `+ Add Line Item` | button | | |
| Subtotal / Tax (0%) / **Total Amount** | computed summary | | Tax shown as a single % |
| Notes / Payment Terms | textarea, "Add any notes or payment terms here..." | no | |
| Send to customer immediately | checkbox (checked by default) | | |

Buttons: `Cancel`, primary `Create Invoice`; × close.
Not shown: currency, payment schedule (deposit/balance split), link to approved version, invoice number preview.

## Screen 5 — Record Payment (modal)

File: `RECORD PAYMENT.png`. Opened by `+ Record Payment`. Modal on `/payments` and `/cases/[code]/billing`.

| Field | Type | Required | Notes |
|---|---|---|---|
| Trip Plan | read-only text `John Doe - TP-10045` (pre-filled — no picker drawn when opened from list) | implied | |
| Amount | money input `$ 1500.00` | implied | no max/remaining hint |
| Payment Method | select (`Bank Transfer`; also Credit Card, PayPal per table) | implied | |
| Payment Type | select (`Pending`; values = status list) | implied | label wrong, it is a status |
| Linked to an Invoice | select "Select an Invoice" | implied | should be required (ERD `invoice_id not null`) |
| Payment Date | date picker `Oct 15, 2024` | implied | |

No required asterisks drawn. Missing vs ERD: evidence upload, description/note, schedule instalment,
transaction/receipt no. (shown on detail but never entered).
Buttons: `Cancel`, primary `Save Payment`; × close.

## Screen 6 — Edit Payment (modal)

File: `EDIT PAYMENT.png`. Opened from detail `Edit` or row menu `Edit Payment`.

Fields: Reference ID (read-only `PMT-00124`); Trip Plan / User (text-looking input `TP-10045 — John Doe`,
should be read-only); Amount (`$ 1500.00`); Payment Method (select, `Credit Card`); Payment Type
(select with status dot, `Paid`); Linked to an Invoice (select `INV-2025-1102`); Payment Date
(date-time `Oct 10, 2024 10:30 AM`).
Footer: left red link `Delete Payment` (trash), `Cancel`, primary `Save Changes`. Success → toast (Screen 2).

## Screen 7 — Delete confirm (shared dialog)

Files: `CANCEL INVOICE.png`, `SEND REMAINDER.png` (same frame). Alert dialog: red warning icon,
title "Delete Payment", body "Are you sure you want to permanently delete **INV-2025-1101**? This action
cannot be undone", buttons `Cancel` + red `Delete Invoice`. Title/body/button mismatch (payment vs invoice);
the filename says "Cancel invoice" but the action is "permanently delete" (Conflict C2).

## Screen 8 — Send Reminder

Only the row-menu entry exists (`PAYMENT & INVOICE-2.png`). No compose/preview/confirm screen exported.
Proposal: confirm dialog showing recipient email, invoice no., amount due, due date, template preview
(read-only), `Cancel` / `Send reminder`; on success toast + `notifications` row + audit.

---

## Data mapping

Classes: COMMERCIAL = owned by Booking; CONTENT = CIS-owned, read-only in Booking; IDENTITY = staff/customer.

| UI field | ERD table.column | Class |
|---|---|---|
| Invoice ID `INV-2025-1102` | `invoices.invoice_number` | COMMERCIAL |
| Trip case code `TC-2025-089` | `trip_cases.code` (via `invoices.trip_case_id`) | COMMERCIAL |
| Customer name (list, modal auto-fill) | `customers.*` name via `trip_cases.customer_id` | IDENTITY |
| Customer email / phone / avatar (detail) | `customers.*` (email/phone); avatar → `media_files` (missing link in ERD) | IDENTITY |
| Invoice Amount | `invoices.amount` (+ `currency`) | COMMERCIAL |
| Issue Date | `invoices.issued_at` | COMMERCIAL |
| Invoice Due Date | **missing in ERD** on `invoices` (only `payment_schedule.due_date`) — derive = earliest open schedule due date, or add `invoices.due_date` | COMMERCIAL |
| Invoice status Paid/Pending/Overdue | `invoices.status` enum {draft, sent, partially_paid, paid, cancelled}; **"Overdue" missing** (derived from schedule `overdue`), "Pending" ≈ sent/partially_paid | COMMERCIAL |
| Line item description / qty / unit price / total | `invoice_items.description / quantity / unit_price / amount` | COMMERCIAL (description is commercial free text, not CIS content) |
| Subtotal | computed Σ `invoice_items.amount` | COMMERCIAL |
| Tax (0%) | **missing in ERD** (ADR 0005 §10 → `tax_rules` table + itemised tax; no tax columns on invoices/items) | COMMERCIAL |
| Total Amount | `invoices.amount` | COMMERCIAL |
| Notes / Payment Terms | **missing in ERD** (`invoices` has no notes/terms) | COMMERCIAL |
| Send to customer immediately | `invoices.status='sent'` + `issued_at` + `notifications` row | COMMERCIAL |
| Cancel invoice | `invoices.status='cancelled'`, `cancelled_at`, `cancel_reason` | COMMERCIAL |
| Payment ID `PMT-00124` / Reference ID | **missing in ERD** — `payments` has only uuid `id`; need `payments.reference` (human code) | COMMERCIAL |
| Transaction ID / Receipt No. | **missing in ERD** (`payments.external_ref`/`provider_txn_id`) | COMMERCIAL |
| Payment Amount | `payments.amount` (+ `currency`) | COMMERCIAL |
| Payment Method | `payments.payment_method` (varchar; recommend enum/check) | COMMERCIAL |
| Payment "Type"/status Paid/Pending/Failed/Refunded/Active | **missing in ERD** — `payments` has no status; `payment_status` enum lives on `payment_schedule` {scheduled,due,paid,overdue,cancelled} and has no failed/refunded | COMMERCIAL |
| Payment kind (deposit/second/final) | `payment_schedule.kind` — not shown in Figma | COMMERCIAL |
| Payment DUE DATE (payment list) | `payment_schedule.due_date` via `payments.payment_schedule_id` | COMMERCIAL |
| Payment Date / Date & Time | `payments.received_at` | COMMERCIAL |
| Linked Invoice | `payments.invoice_id` → `invoices.invoice_number` | COMMERCIAL |
| Internal Notes | `payments.payment_description` | COMMERCIAL |
| Receipt download | `payments.evidence_media_id` → `media_files` (evidence) or generated PDF (missing: no generated-receipt store) | COMMERCIAL |
| Recorded by | `payments.recorded_by` → `staff_users` (not shown in UI) | IDENTITY |
| Related Trip Plan: Trip ID `TP-10045` | ambiguous: `trip_cases.code` (should be TC-…) vs `trip_plans` id; Figma mixes TP/TC | COMMERCIAL |
| Trip Style "Cultural Explorer" | `trip_cases.trip_style` | COMMERCIAL (label only) |
| Start Date | `trip_cases.start_date` | COMMERCIAL |
| Related Trip "Total Amount" `$3,500` | approved `trip_case_versions.total_price` (+ currency) | COMMERCIAL |
| KPI Total Revenue (YTD) | Σ `payments.amount` received this year (needs FX to USD, ADR 0005 §5) | COMMERCIAL (derived) |
| KPI Pending Payments | Σ open `payment_schedule.amount` (scheduled/due) | COMMERCIAL (derived) |
| KPI Overdue Amount | Σ `payment_schedule.amount` where status overdue | COMMERCIAL (derived) |
| KPI Invoices Sent (This Month) | count `invoices` with `issued_at` this month, status ≠ draft/cancelled | COMMERCIAL (derived) |
| Admin name/role in shell | CIS `shared.admin_users` via JWT (O1); `staff_users` thin profile | IDENTITY |

No CONTENT-class field appears on these screens (no descriptions/photos of tours, countries,
activities, hotels).

## Conflicts / decisions

C1. **Three different tab bars** for one page (Invoice|Payment; Invoices|Pending; All Invoices/Pending/Paid/Overdue with counts).
→ Recommend: top tabs `Invoices | Payments`; status as a filter chip row inside each tab
(Invoices: All/Draft/Sent/Partially paid/Paid/Overdue/Cancelled with counts). Needs Nghiệp/designer pick.

C2. **Hard delete of invoices/payments** ("permanently delete … cannot be undone") contradicts ADR 0005
(every change audited, transactional integrity) and ERD (`invoices.cancelled_at/cancel_reason`, audit_logs).
→ Recommend: no delete for invoices once `sent` — replace with `Cancel invoice` (reason required → `cancel_reason`).
Drafts may be deleted (soft). Payments: no delete; use `Void/Reverse` (reason, audited) or refund entry.
Also fix the dialog copy (title/body/button mismatch).

C3. **Free-form line items + editable unit price** vs ADR 0005 (invoice derives from the approved, locked
version; FX locked at quote; sales override only within floor with reason).
→ Recommend: Create Invoice pre-fills lines from the approved `trip_case_versions` (read-only total);
free lines only as adjustments (role-gated, reason, audited); block create when no approved version.

C4. **No currency** anywhere (`$` hard-coded) vs ADR 0005 §5 (USD base + EUR/GBP/AUD/SGD; invoices and
payments use the quote's currency). → Show currency from the case/version (read-only on invoice); payment
amount in invoice currency; KPIs converted to USD with a "USD equiv." label.

C5. **Payment status model missing/inconsistent**: column labelled "Payment Type" shows statuses; values
Paid/Pending/Failed/Refunded/Active don't exist in ERD (`payments` has no status; `payment_status` is on
`payment_schedule`). → Decide: (a) add `payments.status` enum {pending, succeeded, failed, refunded, voided}
in a bk-NNN migration, keep schedule status separate; rename UI column to "Status" and add a "Kind"
column (deposit/second/final from `payment_schedule.kind`). Drop "Active".

C6. **Tax hard-coded "Tax (0%)"** vs ADR 0005 §10 (tax from `tax_rules`, B2C prices tax-inclusive, invoice
itemises tax; rates still unconfirmed by accountant). → Show tax line computed from `tax_rules` (read-only),
"tax included" for B2C; until rules exist, render "Tax: pending accountant confirmation" and keep 0 with a flag.
Also "Method" filter on the Invoice tab is meaningless → remove there.

C7. **Missing payment-schedule UI** (deposit/second/final, due dates) although ERD has `payment_schedule`
and the list shows per-payment DUE DATE. → Add a "Schedule" step/section in Create Invoice (default
deposit % + balance N days before start_date) and a schedule panel on invoice detail.

C8. **No invoice detail screen** (eye icon target undrawn) and **no Send Reminder screen**. → Spec
`/payments/invoices/[invoiceNumber]`: header (number, status, amount, currency), line items, tax, schedule,
payments received, balance due, PDF, Send/Resend, Cancel; reminder as confirm dialog (Screen 8).

C9. **Record Payment lacks evidence + reference fields** while ERD has `evidence_media_id` and Mr. Mạnh's
`payment_description`, and detail screen shows Transaction ID. → Add: receipt upload (image/PDF → media_files),
Transaction/Receipt no. (needs new column), note; make Linked Invoice required; amount ≤ balance warning.
Also ADR 0005 maker-checker spirit: consider "verified by" (`trip_case_checks.payment_verified`) as a second-person check.

C10. **TP-/TC- identifier mix** ("Trip Plan TP-10045" on payment screens vs "TC-2025-089" in lists).
In ERD, trip_plans are catalogue templates; customer money hangs off `trip_cases`. → Use Trip Case (`TC-…`
= `trip_cases.code`) everywhere on billing screens; rename "Related Trip Plan" → "Trip Case".

C11. **Online gateway implied** ("Processed via Stripe gateway", PayPal, "Failed") but no gateway is decided
in ADR 0004/0005 (O8: customer app does payments). → Phase 1 staff-recorded manual payments only; gateway
(Stripe/PayPal) is a separate decision; Failed/Refunded statuses only appear once a gateway exists.

C12. **Role / permissions**: shell shows "Super Admin"; ERD roles admin/sales/content_creator (+ `contracting`
from ADR 0005). → Proposal: create/send invoice = sales + admin; record/edit payment = admin (or a finance role,
to decide); cancel/void = admin with reason; content_creator no access. JWT from CIS (O1).

C13. Copy bugs: "flows" in footer, "has been saved", "REMAINDER" filename, H1 "Payments Management" vs
"Payments & Invoices". Empty, loading, error states not designed for any screen → use kit defaults.
