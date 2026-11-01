---
id: GUIDE-12-cis-admin
title: CIS admin runbook
description: How Adventure Asia staff get into the CIS admin console, what each staff role can do, the daily content flows from upload to Master Content, managing staff, tenants and agencies, and where to look when something is wrong.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer]
applies_to: [aa-cis-frontend, aa-cis-api]
last_reviewed: 2026-11-01
review_every_days: 90
related: [GUIDE-12, GUIDE-12-ai-reports, GUIDE-04, GUIDE-01, OPS-04, AA-1020]
---

# CIS admin runbook

Part of [app access and operations](app-access-and-operations.md). A Vietnamese version of this page is
[cis-admin-runbook.vi.md](cis-admin-runbook.vi.md).

## 1. Who uses it

The CIS admin console is the staff website of the content system. Adventure Asia staff use it to bring tour files in,
rewrite and review tours, keep the tour catalog (Master Content), and look after tenants, partner agencies, jobs and
spend. The business owner uses it to see the whole platform. Partner agencies never use it.

## 2. Address

| What | Dev address |
|---|---|
| Admin console | `https://aa-cis.lumiguides.it.com` (opens the sign-in page) |
| Staff sign-in page | `https://staff-auth.lumiguides.it.com` (you reach it from the console; do not bookmark it) |
| API health, for engineers | `https://api-cis.lumiguides.it.com/health` |

## 3. Get an account

1. Ask a platform owner (today the tech lead) for access, with your `@adventure.asia` address and the work you do.
2. The owner opens **Platform › People & access › Staff**, chooses **Add staff**, types your name and work e-mail,
   and picks a **CIS role** and, if you also work in Booking, a **Booking role**.
3. You receive an invitation e-mail. If it does not arrive within a few minutes, the owner presses **Resend invite**
   on your row.

Only a platform owner who signed in with a company e-mail can add accounts, change roles or disable an account.
Leaving the company: the owner disables the row (it is never deleted, so the history stays).

## 4. Sign in and out

1. Open `https://aa-cis.lumiguides.it.com`.
2. Choose **Sign in with company email**.
3. On the Adventure Asia sign-in page, type your work e-mail address.
4. Type the one-time code from the e-mail. You land on the first page your role may open.
5. To sign out, open the account menu (your initial, top right) and choose **Sign out**. The next sign-in asks for a
   new code.

A session renews itself while you work and ends after about 12 hours. There is no password.

## 5. Roles

| Role | What it can do |
|---|---|
| **admin** | Every page, including the Platform section (people, apps, tenants, agencies, jobs, AI and spend, reports, docs) and the tenant-output quality pages. The business owner has this role |
| **reviewer** | Content work: **Upload (S0)**, **Rewrite (S1)**, **Review Queue**, **Master Content**, **AA content (CRM)**, **Supply (Booking)**, **Facts** (read), **Settings** |
| **content** | The same content pages as reviewer |
| **viewer** | Read only, used by the automated checks; it cannot be given to a person |
| **Owner flag** | An admin with the owner flag also manages staff accounts. Today: the tech lead and one locked emergency account |

Some buttons need more than the page: for example editing **Facts**, publishing **AA content (CRM)** and every tenant
setting are admin only. The server checks the role again on every change.

## 6. The menu

The left menu has two sections.

- **Platform**: Overview (**Overview**, **Data coverage**, **Reports**); People & access (**Staff**, **Audit log**,
  **Alert recipients**); **Apps**; Tenants (**Tenants**, **Agencies (CRM)**); Jobs (**Jobs**, **Data erasure**);
  AI & spend (**AI providers**, **Cost Operations**, **Cost per app**, **Jev Decisions**); Developer (**API Docs**,
  **Data model**, **Docs**).
- **CIS Content**: Pipeline (**Upload (S0)**, **Rewrite (S1)**, **Review Queue**, **Master Content**); Assets
  (**Photos**, **Places**, **AA content (CRM)**, **Facts**, **Supply (Booking)**); Intelligence (**Social Content**,
  **SEO Intelligence**); Tenant output (**Content Trace**, **A4 Quality**, **Content Quality**, **Writing memory**).

**Settings** sits at the bottom of the menu. The UI opens in English; switch the language in the top bar.

## 7. Day-to-day tasks

### Bring new tours in

1. Open **Upload (S0)**.
2. Follow the steps on the page: **Select Files** (the tour Excel file), **Upload to S3**, **Parse & Review**,
   **Commit**, then **Dup Review** for tours that look like ones already in the catalog.
3. The new tours appear under **Tours Ready for Rewrite**. **Trash** removes a wrong source tour; **Show Trashed**
   lets you restore it.

### Rewrite tours

1. Open **Rewrite (S1)**, filter by country or file, and select the tours.
2. Check **Brand Identity** and **SEO Mode** (Standard, Aggressive or Minimal). The model is set on
   **AI providers › Routing**, not here.
3. Start the run and follow each tour through Generating content, Validating & scoring, Brand audit and Final check.

> [!WARNING]
> A rewrite calls paid AI models. Start with about three tours, then at most about fifty. A larger run needs the
> business owner's approval with a price first.

### Review and publish

1. Open **Review Queue** and keep the **Pending** filter.
2. Open a tour and read the new version against the source. Fix text in place and press **Save edits**; the page
   asks you to validate again before you approve.
3. Choose **Approve** to publish it to Master Content, **Reject** to keep it out, or **Regenerate** to rewrite it again
   (a paid call).

### Read and export Master Content

1. Open **Master Content** and search for the tour.
2. Use **+ Add Panel** to compare versions side by side, **Export Comparison XLSX** or **Export this version as
   DOCX** to share one.

### Manage staff (owners only)

1. **Staff**: add, change role, disable or sign someone out. **Open in Booking** opens the same person in Booking
   admin.
2. **Audit log**: who changed what and when.
3. **Alert recipients**: who receives alarm and budget e-mails.

### Tenants and partner agencies

1. **Tenants**: **New Tenant**, then **Create Tenant**, creates a partner brand for the Content studio. Open a tenant
   for its tabs (Tours, Pipeline, Activity, API Usage, Brand, Social Content, Usage & Billing, Cost, Quality, Markets,
   Audit, Settings). Inviting tenant members has no button yet: see the
   [Content studio runbook](content-studio-runbook.md#3-get-an-account).
2. **Agencies (CRM)**: the partner agencies of the CRM. **Create agency**, **Invite first owner**, **Lock** and
   **Unlock** need the CRM platform-admin staff group and a ticket reference; other admins can read the list and the
   usage. Details: [CRM runbook](crm-runbook.md#3-get-an-account).

### A person asks for their data to be deleted

1. Open **Data erasure**. Run the DRY RUN first and read what it would delete.
2. Apply only after the check, following the [data request and erasure runbook](../legal/dsar-erasure-runbook.md).
   Only the CIS part has a button; the other apps follow that runbook by hand.

### Watch the platform

- **Overview**: one screen with the state of the system. **Data coverage**: tours counted from upload to TripPlanner,
  Booking and the CRM.
- **Apps**: is each app up, which commit it runs (**Same commit** or **Mismatch**), and the **Deploy gate** (**Safe to
  deploy** or **Deploy waits**).
- **Jobs**: background work, queued, running and failed, with a drawer per job.
- Spend and reports: see the [AI providers and reports runbook](ai-providers-and-reports-runbook.md).

## 8. When something looks wrong

| You see | Look at | Then |
|---|---|---|
| A red dot on the bell (top bar) | The bell list: the newest notifications | Open the page it names |
| A page shows an error or stays empty | **Apps**: is CIS up and is the commit the same on API and workers? | Take a screenshot and send it with the time |
| Rewrites or reviews do not move | **Jobs** (failed jobs) and **AI providers** (a provider not OK) | If a provider refuses calls, tell the engineer on duty; refused jobs are put back in the queue once it answers again |
| The sign-in code does not arrive or the code page refuses you | Spam folder; wait two minutes, then ask for a new code | Still failing: the engineer on duty follows the [staff sign-in playbook](../ops/playbooks/cognito-login.md) |
| An alarm e-mail | The alarm name in the subject | Forward it to the engineer on duty if it stays in ALARM |

During the dev phase the tech lead is the engineer on duty. Normal issues go to Jira; urgent ones by direct message.

## 9. Dev-phase caveats

- Test data only. Tours, tenants and agencies on Dev are for testing.
- Chat models are refused since 2026-10-29 on the main model account, so **Rewrite (S1)**, **Regenerate** and the
  AI checks fail or wait until a model path is back. Refused jobs are put back in the queue from **AI providers**
  once the provider answers again.
- The address `aa-cis-preview.lumiguides.it.com` is a test copy of the console for engineers, read-only for staff.

## Sources (for maintainers)

Read from AA-CIS-App `main` on 2026-11-01: `frontend/app/_kit/adminNav.tsx` (menu), `frontend/lib/rbac.ts` (roles),
`frontend/app/login/page.tsx`, the `messages.ts` files of `admin/platform/staff`, `upload`, `s1-rewrite`, `review`,
`master-content`, `platform/apps`, `tenants`, `platform/agencies`, `_kit/Topbar.tsx` (bell), and `CONTEXT.md`
("Staff roles and permissions"). Sign-in design: root ADR 0006 and 0006a. Keep
[cis-admin-runbook.vi.md](cis-admin-runbook.vi.md) in step with this page.
