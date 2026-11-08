---
id: GUIDE-12-tripplanner
title: TripPlanner runbook
description: How travellers use TripPlanner as a guest or signed in (plan a trip, send it to an advisor, My trips and payments), how a traveller account is created, what staff do with the requests, and where to look when something is wrong.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer]
applies_to: [tripplanner-web, tripplanner-lambda]
last_reviewed: 2026-11-01
review_every_days: 90
related: [GUIDE-12, GUIDE-12-booking, GUIDE-04, OPS-04, AA-1020]
---

# TripPlanner runbook

Part of [app access and operations](app-access-and-operations.md). A Vietnamese version of this page is
[tripplanner-runbook.vi.md](tripplanner-runbook.vi.md).

## 1. Who uses it

TripPlanner is the public website where a traveller explores Adventure Asia destinations and tours, builds a trip on
a map and sends it to an Adventure Asia advisor. Travellers use it as **guests** (no account) or **signed in** (to see
their trips on any device and the payment requests for trips they sent while signed in). Adventure Asia staff do not
sign in here: the trips sent to an advisor arrive in the [Booking admin](booking-admin-runbook.md).

## 2. Address

| What | Dev address |
|---|---|
| Home page | `https://tripplanner.lumiguides.it.com` |
| Map planner | `https://tripplanner.lumiguides.it.com/plan` |
| Destinations | `https://tripplanner.lumiguides.it.com/destinations` |
| Sign in | `https://tripplanner.lumiguides.it.com/sign-in` |
| My trips | `https://tripplanner.lumiguides.it.com/trips` |

## 3. Get an account

Nobody creates traveller accounts by hand. A traveller creates their own account the first time they sign in with an
e-mail code. Travellers who only plan a trip and send it need no account.

## 4. Sign in and out

1. Choose **Sign in** in the header (or **Sign in or create an account**).
2. Type an e-mail address and choose **Email me a code**.
3. Type the code from the e-mail. A new address gets one code to confirm it, then one more to sign in ("Your email is
   confirmed. We sent one more code to sign you in.").
4. You land on **My trips**. Trips planned in this browser as a guest are added to your account. A trip you already
   sent as a guest still gets its payment requests by e-mail from the advisor, not under **Payments**.
5. To sign out, choose **Sign out**. On a shared computer, always sign out.

There is no password. A code that expired or was mistyped shows a message; ask for a new one.

## 5. Guest and signed-in traveller

| | Guest | Signed in |
|---|---|---|
| Explore destinations and tours, plan on the map | Yes | Yes |
| Send a trip to an advisor | Yes (name, e-mail and phone in the form) | Yes (the e-mail is filled in) |
| Find the trip again | In the same browser only | **My trips**, on any device |
| See payment requests from Adventure Asia | No: the advisor sends them by e-mail | **Payments** on **My trips**, only for trips sent while signed in (a trip sent as a guest stays by e-mail, even after signing in) |

## 6. Day-to-day use (traveller)

### Plan a trip

1. On the home page, fill **Where to**, **How long** and **Travellers**, then **Plan a trip**. Or open a destination
   or a tour page and choose **Customise this trip** or **Ask an advisor**.
2. On the map planner, click a marker and **+ Add to trip**. Switch between **Map** and **List of tours**.
3. Use **Reorder & send** to drag days into order. Extra days and free days can be added.

### Send it to an advisor

1. Open the trip panel and fill **Full name**, **Email** and **Phone**.
2. Tick "An Adventure Asia advisor may contact me about this trip." and choose **Send to an advisor**.
3. The page says "Sent to an advisor. They'll be in touch shortly." The request reaches the Booking admin as a new
   inquiry.

### Follow trips and payments (signed in)

1. Open **My trips**. Each trip shows its status (Draft or Sent to an advisor), stops and days. **Open** reopens it on
   the map.
2. Under **Payments**, see the payment schedule, payments received and **How to pay** while money is owed. There is no
   pay button: payment instructions come from the advisor.
3. **Payments** lists only trips sent while signed in. A trip sent as a guest never shows its payment requests here,
   even after you sign in and it is added to **My trips**: the advisor sends those by e-mail.

## 7. What staff do

- New trips sent to an advisor appear in Booking admin › **Trip Cases** (tab **Inquiries**), and staff get a "new
  inquiry" e-mail. Follow the [Booking admin runbook](booking-admin-runbook.md#a-new-inquiry-arrives).
- Tour and destination pages are built from CIS Master Content. A tour that Adventure Asia stops selling disappears
  from lists within minutes and its page answers "gone".
- The CIS admin **Apps** page has a TripPlanner card with today's AI spend against its daily cap. When the spend
  cannot be read, TripPlanner stops calling AI and serves the simple version without AI text.

## 8. When something looks wrong

| The traveller or staff see | Then |
|---|---|
| "We could not send the email" or no code arrives | Check the address and the spam folder; wait a few minutes ("Too many attempts") |
| A notice says the browser is not keeping the planner's cookie | Allow cookies for the site; without them changes to the trip cannot be saved |
| **Send to an advisor** fails | Try again; if it keeps failing, note the time and tell the engineer on duty |
| A sent trip is not in Booking | The engineer on duty checks the inquiry hand-off report (CIS admin › **Reports**) |
| **We could not load your payments** | Choose **Try again**; if it stays, tell the engineer on duty |
| A tour page shows "not found" | The tour may be paused or no longer sold; check it in CIS admin › **Master Content** |

During the dev phase the tech lead is the engineer on duty. Rollback for engineers:
[TripPlanner Lambda rollback](../ops/runbooks/rollback-tp-lambda.md) and, for the web app on ECS, [ECS rollback](../ops/runbooks/rollback-ecs.md) (service `aa-tripplanner-dev-web`; the Vercel project was retired, AA-1038).

## 9. Dev-phase caveats

- The site is a **preview**: search engines are told not to index it, and the footer says "Preview site".
- **Terms** and **Privacy** are drafts pending legal review.
- The AI text in the planner (route narration) needs a chat model. The main model account has refused calls since
  2026-10-29, so that text may be missing on Dev; planning, maps and sending still work.
- Data on Dev is test data; real travellers are not invited yet.

## Sources (for maintainers)

Read from AA-TripPlanner-Web `main` on 2026-11-01: the `frontend/app` route folders, `frontend/components/SignInForm.tsx`,
`TripPanel.tsx`, `MyTrips.tsx`, `MyPayments.tsx`, `site/HomeSearch.tsx`, and `CONTEXT.md` (sections "Pages", "Guest
identity", "Traveller sign-in in the BFF", "My Payments", "Contracts with other apps"). Decisions: root ADR 0006
(Phase 4, traveller sign-in). Keep [tripplanner-runbook.vi.md](tripplanner-runbook.vi.md) in step with this page.
