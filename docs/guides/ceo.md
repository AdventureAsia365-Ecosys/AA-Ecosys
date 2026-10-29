---
id: GUIDE-04
title: CEO guide
description: Guide for the business owner (CEO) - what the four apps do for the business, where to sign in, what to look at, how to read cost, which decisions are the owner's and how to report a problem.
type: tutorial
status: draft
owner: nghiep
audience: [owner]
applies_to: [ecosystem]
last_reviewed: 2026-10-28
review_every_days: 90
related: [CAT-00, GUIDE-03, OPS-04, FIN-01, FIN-02, AA-897, AA-855]
---

# CEO guide

How the whole delivery system works: [engineering handbook](../engineering-handbook.md). A Vietnamese version of this
page is [ceo.vi.md](ceo.vi.md).

## 1. Who this is for

This guide is for the business owner, the CEO of Adventure Asia. It needs no technical background. After reading it
you will know what each app does for the business, where to sign in, which pages to look at, how to read the monthly
cost and which decisions wait for you. The tech lead keeps this page up to date; a PDF copy is placed on Google Drive.

## 2. The four apps

| App | What it does for the business | Who uses it |
|---|---|---|
| **CIS** (Content system) | Turns our tour files into clean, checked tour content, keeps the tour catalog, and writes content for partner brands (tenants). | Adventure Asia staff (admin console) |
| **TripPlanner** | The website where a traveller explores places, builds a trip and sends a request to an advisor. | Travellers |
| **Booking** | Where staff handle each traveller request: customer, trip case, proposal, price, suppliers. | Adventure Asia sales and contracting staff |
| **Partner** (agency app) | The app we give to partner travel agencies: a CRM to run their own clients, with our tours inside it. Since 2026-10-25 it also holds the tenant portal (Content studio), where partners manage their brand content. | Partner agencies |

The four apps share one AWS account and one database, with a clear owner for each part. Only CIS creates or
changes tour content; the other apps read it.

## 3. Where to sign in

| Page | Address | How you sign in |
|---|---|---|
| **CIS admin console** (your main page) | `https://aa-cis.lumiguides.it.com` | Click **Sign in with company email**, type your company e-mail address, then type the one-time code sent to your inbox. The code page is `staff-auth.lumiguides.it.com` with the Adventure Asia logo. |
| Booking admin | `https://booking.lumiguides.it.com` | Same company e-mail code, only with a Booking role. Ask the tech lead if you need one. |
| Partner app and tenant portal | `https://portal.lumiguides.it.com` | For **partner agencies** only, with their own sign-in. Staff do not use it. |
| TripPlanner | `https://tripplanner.lumiguides.it.com` | Public traveller site (Dev version). No sign-in needed to plan a trip. |

Your CIS role is **admin**: you can see every page. Changing who has access (the Staff page) is reserved for CIS
owner accounts: the tech lead and one locked emergency account.

> [!NOTE]
> On 2026-10-18 we asked Google to review a false "dangerous site" warning on `lumiguides.it.com`. If your browser
> shows a red warning page, tell the tech lead; do not click through on a shared computer.

## 4. What you can see and do

The console has two areas in the left menu.

**Platform** (the whole company):

- **Overview** - one screen with the state of the system; **Data coverage** - live counts of tours from upload to TripPlanner, Booking and the CRM.
- **People & access** - **Staff** (who has access and with which role), **Audit log** (who did what and when; the
  log shows if a record was changed afterwards), **Alert recipients** (who receives alarm and budget e-mails).
- **Apps** - is each app up, which version runs, is it safe to update now.
- **Tenants** and **Agencies (CRM)** - partner brands and partner agencies.
- **Jobs** (background work in progress) and **Data erasure** (deleting a person's or a partner's data on request).
- **AI & spend** - **Cost Operations**, **Cost per app** (section 5) and **Jev Decisions** (automatic content checks).
- **Developer** - API Docs, Data model and **Docs**, the company documents, this guide included.

**CIS Content** (the tour work): Upload, Rewrite, Review Queue, Master Content; Photos, Places, AA content (CRM),
Supply (Booking); Social Content, SEO Intelligence; Content Trace, A4 Quality, Content Quality, Writing memory.

You can look at everything safely. Buttons that change data (approve, regenerate, refresh from AWS) do real work;
when unsure, ask the tech lead first.

## 5. Reading the cost

- **Cost per app** (Platform → AI & spend): pick a month. Four boxes show the total, the AWS bill, AI model spend and
  "untagged" AWS cost (not yet assigned to an app). The table splits the money by app: CIS, Booking, TripPlanner and
  Partner CRM, plus "shared" (the database and network all apps use) and "identity" (staff sign-in).
- **Cost Operations**: what the platform spends on AI models, DataForSEO, Jev and the AWS bill, against budget; our
  own records next to the real bill.
- **Refresh from AWS** asks Amazon for new numbers and costs about 0.04 USD per click. The page already refreshes by
  itself about once a day, so the button is rarely needed.
- **Budgets with e-mail alerts** on the main AWS account, sent to the alert recipient list: 300 USD per month in total
  (raised from 250 on 2026-10-28), split CIS 90, shared 120, Partner CRM 35, Booking 25, staff sign-in 10,
  TripPlanner 10.
- **Monthly cost and capacity report**: from November 2026, in the first working session of each month, the tech lead
  sends you a short summary: total by app, the five biggest items, change from last month with reasons, and a
  "cost per published tour" figure.
- **New paid services**: nothing new that costs money is switched on without a price quote and approval first.

## 6. Decisions that need you

| Topic | What we bring you | Today |
|---|---|---|
| Legal and terms | A calm proposal with options; whether a lawyer is needed is your call | Tenant terms clause on AI-written content, answer wanted by 2026-11-11 |
| Pricing and offers | Pricing rules and margins proposed for Booking | Booking pricing engine is built; business rules are yours |
| Tenants (partners) | Who becomes a tenant, which plan, when | No paying tenant yet |
| Large paid runs | Any AI batch beyond a small trial (about 50 tours) | Asked case by case with a price |
| Go-live date | When Dev becomes a real service (prod), with a checklist and cost | Not dated yet |
| Vendors | New paid tools or plan upgrades, for example Vercel Pro when the first paying tenant arrives | Free plans today |
| Customer data requests | A traveller asks to see or delete their data; with the lawyer if needed | Handled step by step with the erasure runbook; only the CIS part has a button |
| Incidents with personal data | Whether and how to notify people | Only if it happens |

## 7. Reporting a problem

1. **Normal requests and bugs**: create or comment on a Jira issue in the projects you already use (PR, KAN, CON).
   The tech lead answers there after checking; replies are reviewed before they are posted.
2. **Urgent** (something is down, wrong data is visible, a partner complains): message the tech lead on Zalo.
3. Include: the page address, a screenshot, the time, what you expected and what you saw.

If something serious happens (a product is down for everyone, data is exposed or lost), the tech lead tells you
within 30 minutes and keeps you updated until it is fixed.

## 8. Dev and prod today

- **Dev** is the only environment today. It is for building and testing. It holds **test data only**: no real
  customers. Pages can change quickly, and test records can be reset.
- **Prod** (production) will be the real service for travellers and partners. It will use a separate database on the
  same AWS account. It starts when you set a go-live date; building it takes about three to four weeks of work
  before that date. Before the date we finish a checklist: security keys renewed, backups and restore tested,
  alerts and response targets in place.
- Acceptance testing will be recorded as short videos for all apps once the technical work is done.

## 9. Keeping your account safe

- You sign in with a one-time code sent to your company e-mail. There is no password to remember.
- **Never share a code** with anyone, including the tech lead. Nobody from our team will ever ask for it.
- A code you did not request means someone typed your address: ignore it and tell the tech lead.
- Sign out on shared or public computers.
- Lost access to your e-mail? Tell the tech lead; a CIS owner account can disable and restore your CIS access.
- Security logs (sign-in and network records) are kept for 365 days; app logs for 30 days.

## 10. Fifteen key terms

| Term | Meaning |
|---|---|
| Tenant | A partner brand that uses our content platform. |
| Tenant portal | The partner's own website area. |
| Admin console | The staff website for CIS. |
| Master Content | Our checked version of each tour, shared by all tenants. |
| Atom | A small reusable piece of tour content. |
| Trip case | One traveller request handled in Booking. |
| Proposal | The offer staff send to a traveller. |
| Dev | Build-and-test environment, test data only. |
| Prod | The future live service. |
| Deploy | Putting a new version on a server. |
| Release | Users start seeing a feature. |
| Incident | Something broken that affects users. |
| Budget alert | E-mail when spend nears the monthly limit. |
| Personal data (PII) | Data that identifies a person. |
| UAT | Business acceptance test before go-live. |

The full glossary with more terms: [glossary](../glossary.md).

## Sources (for maintainers)

Keep this page in step with: staff sign-in ADR 0006a; CIS admin navigation (`AA-CIS-App` `frontend/app/_kit/adminNav.tsx`,
read 2026-10-28); cost per app AA-884 (`api/core/app_registry.py`, `api/services/platform_cost.py`), monthly report
AA-896 with AA-838; budgets in Infra `accounts/aa365/variables.tf` and `observability.tf` (read live 2026-10-28);
legal AA-820, AA-886; Dev test data only D-01; prod ADR 0001 / ADR 0012 / C7.2a / D-17 / AA-880; Vercel plan D-18; data requests
D-11 and the [DSAR and erasure runbook](../legal/dsar-erasure-runbook.md); log retention D-09 / AA-872; incident duties
[incident response](../ops/incident-response.md); UAT videos AA-855; Safe Browsing review AA-816. Keep
[ceo.vi.md](ceo.vi.md) in step with this page.
