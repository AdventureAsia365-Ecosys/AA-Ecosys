---
id: GUIDE-12
title: App access and operations
description: Index of the per-app runbooks - for each app who uses it, its Dev address, how people sign in and who owns the accounts; start here to get into an app or to run it day to day.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer, devops]
applies_to: [ecosystem]
last_reviewed: 2026-11-01
review_every_days: 90
related: [CAT-00, GUIDE-04, GUIDE-01, GUIDE-05, OPS-04, AA-1020]
---

# App access and operations

This page is the entry point to the app runbooks: one page per app that says **how to get in** and **how to run
it day to day**. They are written for the business owner, Adventure Asia staff and the people at partner agencies
who help their own colleagues. A Vietnamese version of this page is
[app-access-and-operations.vi.md](app-access-and-operations.vi.md).

What each app does for the business is in the [CEO guide](ceo.md). Engineering access (AWS, GitHub, Vercel) is in
[onboarding](../onboarding.md); this page covers only the apps themselves.

## The apps

| App | Users | Dev address | Sign-in method | Account owner | Runbook |
|---|---|---|---|---|---|
| **CIS admin** (content system) | Adventure Asia staff and the business owner | `https://aa-cis.lumiguides.it.com` | Company e-mail and a one-time code (staff sign-in) | A platform owner adds the account on **Staff** (today the tech lead) | [CIS admin runbook](cis-admin-runbook.md) |
| **Content studio** (tenant portal) | Partner brands that buy content (tenant members: owner, editor, viewer) | `https://portal.lumiguides.it.com/portal/dashboard` | E-mail, password and an authenticator app (partner sign-in) | Adventure Asia staff create the tenant and send the invitation; the tenant owner manages day-to-day use | [Content studio runbook](content-studio-runbook.md) |
| **CRM for agencies** (AA Partner) | Partner agencies (owner, agent, assistant); their travellers through links; Adventure Asia support and ground operations staff | `https://portal.lumiguides.it.com` (agency app), `https://go-dev.lumiguides.it.com` (traveller pages), `/staff` on the agency host (AA staff console) | Agencies: e-mail, password and an authenticator app. AA staff: company e-mail and a one-time code | Adventure Asia creates the agency and invites its first owner; the agency owner invites the team | [CRM runbook](crm-runbook.md) |
| **Booking admin** | Adventure Asia sales, contracting and content staff | `https://booking.lumiguides.it.com` | Company e-mail and a one-time code (same staff account as CIS) | A platform owner sets the Booking role on CIS **Staff** | [Booking admin runbook](booking-admin-runbook.md) |
| **TripPlanner** | Travellers, as guests or signed in | `https://tripplanner.lumiguides.it.com` | None to plan a trip; e-mail and a one-time code for My trips | The traveller creates their own account at the first sign-in | [TripPlanner runbook](tripplanner-runbook.md) |

Inside the CIS admin, two areas have their own runbook because the business owner reads them often:
[AI providers and reports](ai-providers-and-reports-runbook.md) (AI and data spend, model health, the report
register).

## Three kinds of sign-in

| Sign-in | Who | What you need | Where the code or password comes from |
|---|---|---|---|
| **Staff sign-in** | Adventure Asia staff in CIS admin, Booking admin and the CRM staff console | An `@adventure.asia` address added by a platform owner | A one-time code e-mailed to you; the sign-in page is `staff-auth.lumiguides.it.com` with the Adventure Asia logo. No password |
| **Partner sign-in** | People at partner agencies and tenants (CRM and Content studio share one account and one host) | An invitation e-mail | You choose your own password at the first sign-in and set up an authenticator app; two-step sign-in is always required |
| **Traveller sign-in** | Travellers on TripPlanner | Any e-mail address | A one-time code e-mailed to you; the account is created at the first sign-in. Travellers of a partner agency never sign in: they use the links the agency sends |

Never share a one-time code, a password or an authenticator code with anyone, the tech lead included.

## When something is wrong

1. Check the app's own health signs first (each runbook names them: the bell, the **Apps** page, the **Jobs** page,
   the CRM health page).
2. Alarm e-mails go to the people on CIS admin **Platform › Alert recipients**, on ALARM and again on OK.
3. Normal problems: a Jira issue in the projects you already use. Urgent problems (an app is down, wrong data is
   visible, a partner complains): message the engineer on duty at once. During the dev phase the tech lead is the
   engineer on duty for every app.
4. Always give the page address, the time, a screenshot, what you expected and what you saw.

How incidents are handled and who is told: [incident response](../ops/incident-response.md).

## Dev phase today

- **Dev is the only environment.** It holds test data only: synthetic agencies, invented travellers and tenants,
  no real customer. Records can be reset.
- **Model calls are limited.** The main chat-model account has refused calls since 2026-10-29, so AI writing and
  checking that needs a chat model waits or fails on Dev until a model path is back
  ([postmortem](../ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md)). Search embeddings still work. The CRM
  runs a built-in stand-in instead of a real model, and its SMS and WhatsApp use a sandbox provider.
- **Addresses change at go-live.** The `lumiguides.it.com` hosts are Dev hosts. Production addresses are set when
  the go-live date is set.
- These runbooks were written from the code and checked on Dev by opening each address on 2026-11-01. A walk-through
  by staff is still to come; report any step that does not match the screen.
