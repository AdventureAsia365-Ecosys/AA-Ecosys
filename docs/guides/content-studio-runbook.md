---
id: GUIDE-12-content-studio
title: Content studio runbook
description: How a partner brand (tenant) gets into the Content studio, what the owner, editor and viewer roles can do, the daily flows from picking tours to publishing content, and what to do when something is wrong.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer]
applies_to: [aa-crm-web, aa-cis-api]
last_reviewed: 2026-11-01
review_every_days: 90
related: [GUIDE-12, GUIDE-12-crm, GUIDE-12-cis-admin, GUIDE-04, AA-1020]
---

# Content studio runbook

Part of [app access and operations](app-access-and-operations.md). A Vietnamese version of this page is
[content-studio-runbook.vi.md](content-studio-runbook.vi.md).

## 1. Who uses it

The Content studio (the tenant portal) is where a partner brand that buys content from Adventure Asia picks tours,
rewrites them in its own brand voice, writes social posts and articles, and publishes them to its own website or
Facebook Page. Its users are the members of a **tenant**. Adventure Asia staff set tenants up from the CIS admin; they
do not work inside the studio.

The studio shares one host, one account and one sign-out with the [CRM for agencies](crm-runbook.md): an agency
that has both opens the studio from the CRM menu (**Open Content studio**), and the studio links back (**Open CRM**).

## 2. Address

| What | Dev address |
|---|---|
| Content studio | `https://portal.lumiguides.it.com/portal/dashboard` |
| Sign-in | Starts from the address above; the partner sign-in page opens by itself |

## 3. Get an account

<!-- learn-tier: staff -->

1. **Adventure Asia creates the tenant.** An admin opens CIS admin › **Tenants**, chooses **New Tenant**, fills the
   form and presses **Create Tenant**.
2. **Adventure Asia invites the first member.** The invitation names the address and the studio role (owner, editor or
   viewer). The CIS admin has no button for it yet: ask the engineer on duty, who sends it through the staff
   invitation route. CIS keeps the role; the CRM sends the e-mail.
3. **The member opens the e-mail** "Your invitation to AA Partner" and chooses **Open invitation**.
4. The page shows the sign-in address and a **one-time password**, shown only once. Keep the page open, choose
   **Continue to sign in**, sign in with it, then choose your own password.
5. Set up an **authenticator app** on your phone (Google Authenticator, Microsoft Authenticator, 1Password or similar)
   and type its code. Two-step sign-in is always required.
6. Choose **Accept invitation**. The page says **Your Content studio access is ready**; choose **Open the Content
   studio**.

If the address already has an AA Partner account (for example from the CRM), the person signs in with that account and
only accepts. If the one-time password is lost before the first sign-in, a new invitation is needed.

## 4. Sign in and out

1. Open `https://portal.lumiguides.it.com/portal/dashboard`.
2. On the sign-in page type your e-mail address, your password and the code from your authenticator app.
3. If your account belongs to several studios, choose one on **Choose a Content studio**.
4. To sign out, open **Account settings** and sign out. This also signs you out of the CRM on the same host.

A page that says **No Content studio access** means the account has no studio membership: sign in with the address
the invitation was sent to, or ask Adventure Asia for an invitation.

## 5. Roles

| Role | What it can do |
|---|---|
| **owner** | Everything in the studio, including **Integrations**, the **API** key and account pages |
| **editor** | Picks tours and writes, edits and publishes content; cannot change **Integrations**, the account or webhooks |
| **viewer** | Reads only |

Roles are set by Adventure Asia (CIS); the **Members** page lists the tenant's members and their roles.

## 6. The menu

- **Overview**: **Dashboard** (usage and quota at a glance).
- **Tours**: **Marketplace** (every tour you can pick, and the tours you picked), **My Tours** (your rewritten
  versions).
- **Brand**: **Brand Identity** (voice, tone, calls to action, rules), **Facts** (prices, seasons, visas, transfers and
  terms your writer may cite).
- **Create**: **Social Posts**, **Articles**.
- **Content**: **My Content** (everything written, ready to review and publish).
- **Account**: **Billing**, **Activity**, **Account settings**, **Members**, **API**, **Integrations**.

On a phone the bottom bar shows Dashboard, Tours, Create and Content; **More** opens the rest. Press ⌘K (Ctrl+K) to
search for any page.

## 7. Day-to-day tasks

### Set up the brand once

1. Open **Brand Identity** and fill in the voice, tone, calls to action and rules.
2. Open **Facts** and add the facts your writing may use (prices, seasons, terms), each with its source.

### Pick and rewrite tours

1. Open **Marketplace**. Filter by name, country or length; new tours carry a "New" mark for 14 days.
2. Open a tour and choose **Rewrite this tour** (or select several). The quota note shows how many rewrites are left
   this period.
3. The rewritten version appears in **My Tours** and under **In my catalog** on Marketplace.

### Write and publish content

1. Open **Create › Social Posts** or **Create › Articles**, pick a tour or an angle and choose **Write**.
2. Review the piece in **My Content**. **Write again** asks for a new version.
3. Connect your channels once in **Integrations** (**Connect WordPress**, **Connect your Facebook Page**) and use the
   channel test.
4. Open **Publish** from **My Content** and publish the piece. It shows as **Published**.

### Keep an eye on the account

- **Billing**: your plan, the rewrite meter (used, quota, reset date) and overage so far.
- **Activity**: everything that happened, with filters and a CSV export.
- **API**: the masked API key for your own systems. A new key is requested by e-mail to Adventure Asia.

## 8. When something looks wrong

<!-- learn-tier: staff -->

| You see | Then |
|---|---|
| The page reloads or asks you to sign in again | Your session ended; sign in again |
| **Content studio unavailable** | The studio could not check your access; try again in a minute |
| A rewrite or a post fails | Check **Billing** (quota used up?); then tell Adventure Asia with the page, time and a screenshot |
| Publishing fails | Run the channel test in **Integrations**; reconnect the channel if the test fails |
| Lost phone or authenticator app | Ask Adventure Asia; the engineer on duty resets the second step |

Partner brands contact their Adventure Asia contact. Inside Adventure Asia, the engineer on duty (during the dev
phase, the tech lead) checks **Tenants** and **Content Trace** in the CIS admin and the
[incident response](../ops/incident-response.md) rules.

## 9. Dev-phase caveats

<!-- learn-tier: staff -->

- Only synthetic test tenants exist on Dev.
- AI writing (rewrites, posts, articles) needs a chat model. The main model account has refused calls since
  2026-10-29, so writing fails or waits on Dev until a model path is back.
- **Billing** has no invoices yet (an empty state). **Terms** and **Privacy** are drafts pending legal review.
- Sign-in by tenant API key is off for people; API keys are for machines only.

## Sources (for maintainers)

<!-- learn-tier: staff -->

Read from AA-Partner `main` on 2026-11-01: `portal/app/_kit/local/portalNav.tsx` (menu), `portal/app/portal-access/*`,
`web/lib/i18n.ts` (`join.*` strings), `CONTEXT.md` ("Tenant portal", "Content studio invitations"); AA-CIS-App
`CONTEXT.md` ("Tenant membership directory": studio roles) and `frontend/app/admin/tenants/messages.ts`. Decisions:
root ADR 0010 and 0010a. Keep [content-studio-runbook.vi.md](content-studio-runbook.vi.md) in step with this page.
