---
id: GUIDE-12-booking
title: Booking admin runbook
description: How Adventure Asia sales, contracting and content staff get into the Booking admin, what each Booking role can do, the daily flows from inquiry to trip case, proposal, supplier bookings, invoice and payment, and where to look when something is wrong.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer]
applies_to: [aa-booking-admin, aa-booking-api]
last_reviewed: 2026-11-01
review_every_days: 90
related: [GUIDE-12, GUIDE-12-cis-admin, GUIDE-12-tripplanner, GUIDE-04, OPS-04, AA-1020]
---

# Booking admin runbook

Part of [app access and operations](app-access-and-operations.md). A Vietnamese version of this page is
[booking-admin-runbook.vi.md](booking-admin-runbook.vi.md).

## 1. Who uses it

The Booking admin is where Adventure Asia staff handle each traveller request: the customer, the trip case, the
proposal and its price, the supplier bookings, the invoice and the checks before departure. Sales, contracting and
content staff use it; the business owner can open it with a Booking role. Travellers never sign in here: they plan on
[TripPlanner](tripplanner-runbook.md) and see their payment requests there.

## 2. Address

| What | Dev address |
|---|---|
| Booking admin | `https://booking.lumiguides.it.com` (opens the sign-in page) |
| API health, for engineers | `https://api-booking.lumiguides.it.com/booking/health` |

## 3. Get an account

The Booking admin uses the **same staff account as the CIS admin**.

1. Ask a platform owner (today the tech lead).
2. The owner opens CIS admin › **Platform › Staff**, adds you or opens your row, and sets a **Booking role**: Booking
   admin, Sales, Contracting or Content creator.
3. You receive the invitation e-mail if you are new. Your Booking role is read again at every sign-in, so a change
   applies at your next request.

The Booking **Staff** page shows the same people. Roles are changed only in CIS; a Booking admin can suspend or
reactivate someone in Booking.

## 4. Sign in and out

1. Open `https://booking.lumiguides.it.com`.
2. Choose **Sign in with company email**, type your work e-mail, then the one-time code from the e-mail.
3. Sign out from the account menu. There is no password.

An account without a Booking role is refused with a message; ask the owner for a role.

## 5. Roles

| Role | Can do |
|---|---|
| **Booking admin** | Everything, including **Staff**, **Audit Log**, verifying payments, B2B partners, and the Booking status of countries and destinations |
| **Sales** | Trip cases, customers and proposals (read and write), prices and margins (read), supplier bookings and trip checks, invoices and payments |
| **Contracting** | Reads trip cases and customers; writes suppliers, hotels, services, rates and contracts, pricing rules and FX rates, the commercial row of a trip plan, supplier bills; supplier bookings and trip checks. No customer money |
| **Content creator** | The catalog from CIS (trip plans, destinations, countries) without prices |

Two-person rules (maker-checker): a pricing rule, FX rate or supplier contract is approved by someone other than its
author; a payment is verified by a Booking admin other than the person who recorded it; a supplier bill is approved
by someone other than the person who entered it.

## 6. The menu

- **Overview**: **Dashboard**.
- **Sales**: **Trip Cases**, **Proposals**, **Customers**, **Pricing calculator**.
- **Operations**: **Payments & Invoices**, **Trip Checks**, **B2B desk**.
- **Supply**: **Suppliers**, **Hotels**, **Services**, **Pricing rules & FX**.
- **Catalog (from CIS)**: **Trip Plans**, **Destinations**, **Countries**.
- **Admin**: **Staff**, **Audit Log**.

**Settings** is in the menu footer and the account menu; **Notifications** is the bell in the top bar.

## 7. Day-to-day tasks

### A new inquiry arrives

1. A traveller sends a trip from TripPlanner with **Send to an advisor**. Booking picks it up by itself and sends the
   staff a "new inquiry" e-mail.
2. Open **Trip Cases**, tab **Inquiries** (or **Unassigned**). Open the case.
3. Set the **Sales rep** and check the trip details and the customer.

A request by phone or e-mail: **Trip Cases › New trip case** (or **New lead**), or start from a trip plan with
**Use for trip case**.

### Build and send the proposal

1. In the case, tab **Proposals**, choose **New proposal**. Add days and items (**Add item**, **Add item on day**), or
   **Start from a trip plan**.
2. Check the **Price**; the **Pricing calculator** shows how the price is built.
3. **Preview** what the customer will see, then **Send to customer**.
4. A change after sending: a **New version**. A sent or approved version keeps what the customer saw.
5. When the customer agrees (by e-mail, phone or in person), choose **Record approval** with a note on how they
   approved. The version is locked and the trip is confirmed; the standard checks are added.

### Book the suppliers

1. In the case, tab **Suppliers**, create the supplier bookings for the approved version.
2. Request each booking from the supplier and enter the supplier's reference when it confirms. A declined booking is
   replaced with another supplier.
3. **Items without a live booking** lists what is still missing.

### Invoice and payment (B2C)

1. In the case, tab **Billing**, create the invoice from the approved version: deposit and balance follow the
   settings.
2. Send it. The traveller sees it on TripPlanner under **My trips**.
3. When money arrives: **Record payment** (here or in **Payments & Invoices**).
4. A Booking admin who did not record it opens the payment and chooses **Verify payment**. Only verified money marks
   the invoice paid.

### Before departure

1. Open **Trip Checks** (or the case tab **Checks**). Each confirmed trip has three standard checks (pre-trip recheck,
   emergency contact, insurance) plus any you add with **Add check**.
2. Mark each check done or not applicable. The case moves to pre-departure, on trip and completed by itself when the
   suppliers are booked and, for B2C, the invoice is paid; a blocked move raises a notification.

### Agency (B2B) bookings

Partner agencies book Adventure Asia tours from their CRM. Lines that need a supplier answer show on **B2B desk**:
confirm or decline the supplier booking on the case's **Suppliers** tab, and the agency's line follows.

### Supply and prices (contracting)

1. **Suppliers** › **Add supplier**, then **New contract** and rates; **Hotels** (room types) and **Services**.
2. Hotel and service descriptions are content: **Edit in CIS** opens them in the CIS admin (**Supply (Booking)**).
3. **Pricing rules & FX**: **New rule**, **New FX rate**. Another person approves the row.
4. Supplier bills: **Enter bill** on the supplier; another person approves; a Booking admin records the payout.

## 8. When something looks wrong

| You see | Then |
|---|---|
| The bell shows a notification such as a blocked trip move | Open it; it names the case and the reason |
| "Too many sign-in attempts" | Wait the time shown, then try again |
| A page cannot load data | Check `https://api-booking.lumiguides.it.com/booking/health`, or CIS admin › **Apps** (Booking row); send a screenshot with the time |
| An inquiry from TripPlanner did not arrive | The engineer on duty checks the inquiry hand-off report on CIS admin › **Reports** |
| A permission message (for example "Billing needs the billing role") | Your role does not include it; ask the owner |

During the dev phase the tech lead is the engineer on duty: Jira for normal issues, a direct message when urgent.
Rollback for engineers: [Booking rollback](../ops/runbooks/rollback-booking.md).

## 9. Dev-phase caveats

- Test data only: customers and cases on Dev are invented.
- There is no card payment: payments are recorded and verified by hand. Invoices are proforma payment requests; the
  legal VAT invoice stays outside Booking.
- The **Staff** page only mirrors CIS; change roles in CIS.

## Sources (for maintainers)

Read from AA-Booking `main` on 2026-11-01: `frontend/ui/local/nav.tsx` (menu), the `(staff)` route folders and their
labels, `CONTEXT.md` ("Staff authentication and permissions", "Supplier bookings", "Trip checks and the case
lifecycle", "Invoices and manual payments"); AA-CIS-App `frontend/app/admin/platform/staff/messages.ts` (Booking
roles). Decisions: root ADR 0004, 0005, 0006 and 0006a. Keep [booking-admin-runbook.vi.md](booking-admin-runbook.vi.md)
in step with this page.
