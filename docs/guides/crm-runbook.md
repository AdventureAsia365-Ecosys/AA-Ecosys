---
id: GUIDE-12-crm
title: CRM runbook
description: How partner agencies and Adventure Asia staff get into the CRM for agencies (AA Partner), what the owner, agent and assistant roles can do, the daily flows from inquiry to payment, the AA staff console and the Agencies (CRM) admin page, and what to do when something is wrong.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer]
applies_to: [aa-crm-web, aa-crm-api, aa-cis-frontend]
last_reviewed: 2026-11-01
review_every_days: 90
related: [GUIDE-12, GUIDE-12-content-studio, GUIDE-12-cis-admin, GUIDE-04, OPS-04, AA-1020]
---

# CRM runbook

Part of [app access and operations](app-access-and-operations.md). A Vietnamese version of this page is
[crm-runbook.vi.md](crm-runbook.vi.md).

## 1. Who uses it

The CRM for agencies (shown to users as **AA Partner**) is the app Adventure Asia gives to partner travel agencies to
run their own clients, with Adventure Asia tours inside it. Four groups use it:

| Group | Where | What for |
|---|---|---|
| **Agency team**: owner, agent, assistant | The agency app | Inquiries, clients, proposals, payments, bookings, team and settings |
| **The agency's travellers** | Pages opened from links the agency sends | Inquiry forms, proposals, the traveller portal. They never get an account |
| **Adventure Asia support and ground operations** | The AA staff console (`/staff`) | Read an agency's data with the owner's permission; see what travellers share for confirmed Adventure Asia tours |
| **Adventure Asia admins** | CIS admin › **Agencies (CRM)** | Create agencies, invite the first owner, lock and unlock, usage |

The agency owns its clients' data; Adventure Asia only processes it. Adventure Asia staff therefore see usage
numbers, never trips or revenue, unless the owner allows support access.

## 2. Addresses

<!-- learn-tier: staff -->

| What | Dev address |
|---|---|
| Agency app (the CRM, and the Content studio on the same host) | `https://portal.lumiguides.it.com` |
| Traveller pages (forms, proposals, traveller portal) | `https://go-dev.lumiguides.it.com/c/...` (only through the links the agency sends; the bare host shows nothing) |
| AA staff console | `https://portal.lumiguides.it.com/staff` |
| CRM health page | `https://portal.lumiguides.it.com/health` |
| CRM agencies admin page (Tenants › CRM agencies) | `https://aa-cis.lumiguides.it.com/admin/tenants/agencies` |

The old host `partner-dev.lumiguides.it.com` forwards to `portal.lumiguides.it.com`.

## 3. Get an account

### A new agency (Adventure Asia)

<!-- learn-tier: staff -->

1. An Adventure Asia admin with the CRM platform-admin staff group opens CIS admin › **Agencies (CRM)**.
2. **Create agency**: choose the agency source (**For a CIS tenant**, or **New synthetic agency (test)**), then the
   **Agency name**, the **Default language and region** and the support or Jira ticket it belongs to (for example
   `SUP-1024`; the ticket is written in the agency's access log). No member is created yet.
3. Open the agency's panel and choose **Invite first owner** with the owner's e-mail address. The address is never
   stored in clear or shown again.

A new agency starts on the free plan with 10 seats.

### Joining an agency (every member)

1. Open the e-mail "Your invitation to AA Partner" and choose **Open invitation**.
2. The page shows the address to sign in with and a **one-time password**, shown only once. Keep the page open and
   choose **Continue to sign in**.
3. Sign in with the one-time password, then choose your own password.
4. Set up an **authenticator app** on your phone and type its code. Two-step sign-in is always required.
5. Choose **Accept invitation**, then **Go to AA Partner**.

If you lose the one-time password before the first sign-in, ask the owner for a new invitation.

### The owner invites the team

1. **Settings › Team & roles › Team, roles and plan**.
2. **Invite someone**: the e-mail address and the role (owner, agent or assistant), then **Send invitation**.
3. The invitation shows as **Invited** until the person accepts. The owner can change a role or remove a member here;
   open trips and clients of a removed member move to the reassign queue on the same page.

### Adventure Asia staff console

<!-- learn-tier: staff -->

The console uses the staff sign-in (company e-mail and a one-time code). The tech lead adds your staff account to the
**ground operations** group, the **agency support** group, or both. Without a group the console signs you out with a
message.

## 4. Sign in and out

### Agency team

1. Open `https://portal.lumiguides.it.com` and choose **Sign in**.
2. Type your e-mail, your password and the code from your authenticator app.
3. If you belong to several agencies, choose one. A locked agency shows "This agency is locked by AA".
4. To sign out, choose **Sign out** in the menu. This also signs you out of the Content studio.

### Adventure Asia staff

<!-- learn-tier: staff -->

Open `https://portal.lumiguides.it.com/staff` and choose **Sign in with your AA staff
account**. Signing out of the console (**Sign out of the staff console**) leaves any agency session alone.

### Travellers

Travellers open the links the agency sends. The traveller portal asks for a code sent to their e-mail.

## 5. Roles

<!-- learn-tier: staff -->

| Role | What it can do |
|---|---|
| **Owner** | Everything: team and plan, payments settings, import, data and privacy, the access log, allowing AA support, the getting-started checklist |
| **Agent** | Sales work on trips and clients, proposals, payments and bookings; sees margins and **Commissions**; no team or owner settings |
| **Assistant** | The daily work of the team, without **Commissions**, **Marketing** or any margin, net cost or commission figure |

Hiding a menu entry is only a convenience: the server checks the role on every action.

AA staff groups: **agency support** may read an agency only while its owner allows support; **ground operations**
reads ops releases and may open emergency access; the **CRM platform-admin** group makes changes on **Agencies
(CRM)**. Every staff page view is written to the agency's access log, which the owner can read.

## 6. The menu (agency app)

- **Home**: what needs you, the getting-started checklist, the last 12 months.
- **CRM**: **Pipeline**, **Clients**, **Inbox**, **Tasks**, **Travelling now**, **Calendar**.
- **Money**: **Payments**, **Bookings**, **Commissions**.
- **Grow**: **Reports**, **Marketing**, **Suppliers**, **Library**, **Automations**.
- **Content studio**: **Open Content studio** (when the agency is also a tenant).
- **Settings** and **Help & what's new**.

The app opens in English. Change the language and date format in **Settings › Language and dates**.

## 7. Day-to-day tasks

### First day (owner)

1. Open **Home** and the **Get started** checklist. Three steps are required; the others can wait (**Later**).
2. Read and accept **Shared responsibility** (once, owner only).
3. **Settings › Getting started › Connections and privacy**: connect your own mailbox, card payments or bank transfer,
   SMS and WhatsApp. These are your agency's own accounts; Adventure Asia does not provide them.
4. **Settings › Getting started › Import clients** (owner): upload a CSV or Excel file. A dry run shows the result
   before anything is stored.

### Receive inquiries

1. **Settings › Inquiry forms › Inquiry forms and embed code**, then **New form**.
2. **Copy** the embed code onto your website, or share the form link.
3. Each inquiry appears on **Pipeline** in the **Inquiry** column. A repeat inquiry from the same person joins the open
   trip.

### Work a trip from inquiry to booking

1. On **Pipeline**, open the trip card. Move it through **Qualifying**, **Proposal**, **Booked**, **Pre-departure**,
   **Travelling**, **Completed** (or **Lost** / **Cancelled**).
2. Build the proposal in the trip: days, Adventure Asia tours (live prices and holds) and your own suppliers.
3. **Send to the client**. The client opens the proposal link, picks options and accepts. A change after sending
   needs a **New version**.
4. When the client pays: **Record payment**. Adventure Asia lines are confirmed after the deposit.
5. **Send portal link** gives the traveller their portal: documents, flights, the agreement to sign, and the trip
   itinerary, also offline on a phone.

### Clients

1. **Clients** lists names only. **New client** adds one by hand.
2. Contact details, identity documents and health information open only on **Reveal**, with a reason. Every reveal is
   written to the access log.

### Money and follow-up

- **Payments** and **Bookings**: what is paid, owed and booked. **Commissions** (owner and agent).
- **Travelling now** and **Calendar**: who is away today and what is coming; the calendar can feed Google, Outlook or
  Apple Calendar through a private link.
- **Reports**: the agency's own numbers.

### Allow Adventure Asia support (owner)

1. **Settings › Data and privacy › AA support access**.
2. **Allow AA support** for 1 to 7 days, read only. Showing names stays off unless you turn it on.
3. An amber banner shows on every page while support is allowed. **End now** stops it at once.

A red banner means **emergency access**: Adventure Asia opened it without your permission for a security, data or
legal reason, for at most 60 minutes. The owner gets an e-mail and the banner closes by itself.

### Leave or delete data (owner)

**Settings › Data and privacy** holds the data rules, the trash, legal holds, client erasure, the agency export and
leaving AA Partner. A request raised by Adventure Asia shows there with **Confirm** or **Decline**.

### Adventure Asia staff

<!-- learn-tier: staff -->

- **Agencies (CRM)** in the CIS admin: the list with usage (seats, active members, storage, AI spend, failed jobs);
  **Lock** / **Unlock**; retry a failed job; open an owner recovery when an agency lost its only owner (it completes
  after 14 days, and every member can see and cancel it).
- **Staff console › Ops releases**: traveller details agencies share for confirmed Adventure Asia tours, the minimum the
  ground team needs, deleted 90 days after the return date.
- **Staff console › Support access**: the agencies that allow support now; start a session with a ticket (one staff
  member at a time; it ends with the owner's permission or after 8 hours). Ground operations staff can open emergency
  access with a reason, a ticket and 15 to 60 minutes; names are never shown there.

## 8. When something looks wrong

<!-- learn-tier: staff -->

| You see | Then |
|---|---|
| A page says the CRM service did not answer | Open the CRM health page; try again in a minute |
| "This agency is locked by AA" | The owner contacts Adventure Asia; an admin unlocks it on **Agencies (CRM)** |
| Lost phone or authenticator app | The owner asks Adventure Asia; if the only owner is locked out, an admin opens an owner recovery |
| An invitation does not arrive | Check spam; the owner sends a new invitation |
| Staff console says your account has no access | Ask the tech lead to add you to the support or ground operations group |
| Failed jobs on **Agencies (CRM)** or on CIS admin › **Apps** (CRM jobs) | Retry from the agency drawer; if it fails again, tell the engineer on duty |

Agencies contact their Adventure Asia contact. Inside Adventure Asia, the engineer on duty (during the dev phase, the
tech lead) follows [incident response](../ops/incident-response.md); the CRM encryption keys runbook is
[CRM keys](../ops/runbooks/crm-keys.md).

## 9. Dev-phase caveats

<!-- learn-tier: staff -->

- You can create as many agencies as you need on Dev (for a demo, for training): **Create agency** marks every agency created on Dev as **synthetic** (test data) by itself, and the agency then has every CRM feature. The label keeps test data apart from real data: production will refuse synthetic agencies, and Dev must never hold real customer data (real names, phone numbers, passports). For a demo, invite your own e-mail as the owner, or use the ready test agency that already has sample trips, proposals, invoices and WhatsApp messages.
- AI drafting runs a built-in stand-in, not a real model, so its texts are placeholders.
- SMS and WhatsApp use a sandbox provider that sends nothing. Card payments by Stripe are not built yet; payments are
  recorded by hand.
- `portal.lumiguides.it.com` and the traveller host `go-dev.lumiguides.it.com` are Dev addresses; the production host
  names come with go-live.

## Sources (for maintainers)

<!-- learn-tier: staff -->

Read from AA-Partner `main` on 2026-11-01: `web/lib/nav.ts` (menu and role visibility), `web/lib/i18n.ts` and
`web/lib/i18nStaff.ts` (labels), `web/app/(crm)/settings/page.tsx`, `CONTEXT.md` (sections "Web", "Tenant portal",
"F4 roles and team", "L1 console", "AA support access L2 + break-glass L3", "AA staff console", "Domain terms");
AA-CIS-App `frontend/app/admin/tenants/agencies/messages.ts`. Decisions: root ADR 0010, 0006b, 0008a. Keep
[crm-runbook.vi.md](crm-runbook.vi.md) in step with this page.
