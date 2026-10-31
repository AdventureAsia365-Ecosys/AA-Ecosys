---
id: SEC-04-packet
title: Legal readiness packet
description: Summary for the business owner of the privacy, terms, consent, DPA, sub-processor, erasure, transfer, SLA, support, status page, Vercel plan and AI clause questions, each with options and a proposed answer.
type: explanation
status: draft
owner: nghiep
audience: [owner, cio]
applies_to: [ecosystem]
last_reviewed: 2026-10-28
review_every_days: 90
related: [SEC-04, SEC-04-dpa, SEC-04-dsar, SEC-04-retention, SEC-04-consent-query, AA-886, AA-820, AA-839, AA-877]
---

# Legal readiness packet

The Vietnamese version of this page is [readiness-packet.vi.md](readiness-packet.vi.md).

## Summary

The Trip Planner and the Partner Portal now each have a draft privacy notice and draft terms. The four pages
are online, marked "Draft — pending legal review" and hidden from search engines. Every factual sentence on them
describes what the system does today; the points that need a business or legal answer are marked "[to be confirmed]".
A test on 2026-10-20 showed that when a traveller ticks the consent box, the system stores the answer, the date and time,
and where it came from, and that the copy in the booking system matches. Behind the pages there is now a register of
what personal data is processed and which service providers receive it, a draft data processing agreement for
partners, a deletion procedure and a retention log. Twelve topics below each give the current fact, the options and a
proposed answer. The system runs only on a development environment, and it holds no real traveller or customer data:
every traveller and customer record there was a test or internal entry when checked on 2026-10-17, and the
2026-10-20 consent test used a test address. Staff accounts, alert e-mail recipients and the tour catalog are real data. Whether
to involve a lawyer, and on which topics, is the business owner's call.

| # | Topic | Proposed answer |
|---|---|---|
| 1 | Data controller entity | The entity that runs adventure.asia |
| 2 | Privacy, cookie and terms wording | Read Annex A, fill the business points |
| 3 | Consent capture | Keep one purpose: contact about the trip |
| 4 | DPA and service providers | Use the template; list every provider |
| 5 | Records of processing | Use the provisional register now |
| 6 | Access and deletion requests | Manual procedure now, tested job before real data |
| 7 | Data stored in the US | Keep US hosting, prepare transfer documents |
| 8 | Service levels | Response times only until production |
| 9 | Support address | `support@` to a shared mailbox |
| 10 | Status page | None until the first paying partner |
| 11 | Vercel plan | Pro before the first partner is charged (D-18) |
| 12 | AI acceptable-use clause | A or C: adopt the AI Schedule now (no partners yet); answer needed by 2026-11-11 |

## 1. Data controller entity

*Current fact:* both privacy notices say the legal entity responsible for the data and its registered address
are "[to be confirmed]" (Trip Planner and portal `/privacy` §1). The terms leave the operating entity open the same way.
*Options:* (A) the company that runs adventure.asia and publishes its privacy policy; (B) another group entity, for
example one created for the platform. *Proposed answer:* A, with its full name and registered address, so the notices,
the partner agreement and the DPA name the same party. *Detail:* [register](register.md), section (a).

## 2. Privacy, cookie and terms wording

*Current fact:* the four draft pages are live:
`https://aa-tripplanner.vercel.app/privacy`, `https://aa-tripplanner.vercel.app/terms`,
`https://portal.lumiguides.it.com/privacy` and `https://portal.lumiguides.it.com/terms`. They are linked from the site
footers and next to the Trip Planner contact form. Annex A below quotes their full text. On cookies: the Trip Planner
uses one guest cookie (a random token, stored only as a one-way hash), sign-in cookies only for a traveller who signs
in, and browser storage for the current trip and the display theme; the portal uses sign-in cookies only. Neither uses advertising or analytics cookies, and the code
contains no analytics tool. *Options:* (A) the business owner reads Annex A and answers the business points
(entity, address, minimum age, answer time for requests, booking conditions, fees), then decides whether counsel
reviews the result; (B) send Annex A to counsel as it is. Table A.0 lists every open point on the four pages.
*Proposed answer:* A.
*Detail:* Annex A; [register](register.md), "Page copy follow-ups".

## 3. Consent capture

*Current fact:* the Trip Planner form asks the traveller to agree that an advisor may contact them about the
trip. A test inquiry on 2026-10-20 was followed through three records (the Trip Planner record, the hand-off message, the
booking system customer): each stored consent "yes" with the same date and time, and the booking record names the Trip
Planner as the source. Across all records there were 0 cases of consent without a time, a time without consent, or a
mismatch between the two systems. This consent covers contact about the trip only, not newsletters or other marketing.
*Options:* (A) keep this single purpose; (B) add a second, optional, unticked box for marketing when marketing is
planned. *Proposed answer:* A now, B only when a marketing use exists. *Detail:* [consent capture check](consent-capture-query.md).

## 4. DPA template and service providers

*Current fact:* a draft data processing agreement for partners is ready for review. It sets out that the
partner is the controller for data it puts into the portal and Adventure Asia is the processor, lists the processor
duties, and has annexes for the processing, the security measures (each marked live or planned) and the service
providers. The register lists the providers found in the code: AWS (hosting, e-mail, sign-in, AI models through Amazon
Bedrock), the AI providers OpenAI and Jev, Sentry (error reports), Vercel (websites), Mapbox (maps), Geoapify,
DataForSEO, Google (photo files), the adventure.asia mail host, and work tools. Jev receives partner content only for a short list of test partners, until a data processing and zero-retention
agreement with Jev is in place; that agreement is an open item. Other open points: whether the AWS resellers
(TrueIDC for the hosting account, eCloudvalley for the AI account) and the model makers behind Bedrock must be listed,
and the contract status of each provider. *Options:* (A) list every provider, including resellers, and remove any that
counsel says are not needed; (B) list only providers that process data directly. *Proposed answer:* A. *Detail:*
[DPA template](dpa-template.md); [register](register.md), section (b).

## 5. Records of processing

*Current fact:* the register lists eight processing activities: Trip Planner inquiries and consent, the
booking customer record and trip cases, booking notifications and audit, staff accounts, partner accounts, AI content
generation, alert e-mails, and supplier contacts. For each it gives the people concerned, the kinds of data, where the data is stored,
how long it is kept, who receives it and where it goes. It was built by hand from the database structure, so personal
data inside free-text notes may be missed; it will be rebuilt automatically once every personal-data column is tagged
in the database. *Options:* (A) use the provisional register now; (B) wait for the automatic version. *Proposed
answer:* A. *Detail:* [register](register.md), section (a).

## 6. Access and deletion requests

*Current fact:* requests can be sent to `info@adventure.asia`, as both privacy notices say. A written procedure
exists for checking the person's identity, finding their records in both systems, and deleting them under a counted
dry run that the tech lead approves first. The records are found by a one-way code (hash) computed from the e-mail
address and then deleted by record number, so the address itself is never written into code, logs or files. Database
backups keep a copy for up to 7 days after a deletion and then expire. The content system has a deletion job with a
counted dry run. Its partner part was tested once on the development environment, on 2026-10-23, on a made-up
partner: the dry run, the approval, the deletion and the check all passed. The traveller part has not been run yet,
and the booking system and Trip Planner deletion scripts are not written yet. No real deletion has happened, and three
test records are kept for the first traveller test. Ending a partner account first only switches it off; its data is
erased later, as a separate step that the tech lead approves. The time within which a request is answered is
"[to be confirmed]" on the pages. *Options:* (A) use the manual procedure now and finish the tested traveller deletion
before real traveller data is stored; (B) finish the traveller deletion first. *Proposed answer:* A, and choose the answer time (for example [●] days). *Detail:*
[DSAR and erasure runbook](dsar-erasure-runbook.md); [retention log](retention-log.md).

## 7. Data stored in the United States

*Current fact:* the database and servers are in the United States (AWS, us-west-1), and most service providers
are US companies (AWS, Vercel, Mapbox, Sentry, OpenAI); Vercel and Mapbox serve pages and maps from locations close to
the visitor. One point goes beyond "United States": the AI account calls Amazon Bedrock through "global" routing,
which can process a request (trip contents, tour text, never a name or contact detail) in a region outside the US. The
Vercel functions that carry the Trip Planner contact form run in Vercel's San Francisco region (`sfo1`) since
2026-10-28, and the partner portal now runs on AWS in us-west-1. The pages leave the transfer safeguards
"[to be confirmed]". The S245 research notes, for counsel to confirm: Vietnam's personal data
protection law (Law 91/2025/QH15) and Decree 356/2025/ND-CP took effect on 2026-01-01 and require a transfer impact
assessment, also for offshore cloud hosting, filed within 60 days of the transfer starting; for EU partners, the
standard contractual clauses (Module 2, controller to processor) apply to US hosting; for Australian partners, APP 8
on cross-border disclosure applies. This packet makes no legal claim of its own on these points. *Options:* (A) keep
US hosting and prepare the transfer documents the chosen regimes require; (B) consider a region closer to customers
later, which changes cost and setup. *Proposed answer:* A. *Detail:*
[`04-economics-compliance-security.md`](../audits/2026-10-20-S245-tenant-crm/research/04-economics-compliance-security.md) §4.

## 8. Service levels

*Current fact:* the portal terms leave service levels and support hours "[to be confirmed]" (§8). Internally,
incidents are handled by severity: SEV1 (a product is down for customers or partners, or data is exposed or lost) is
handled at once, at any hour, the business owner is told within 30 minutes and affected partners within 2 hours; SEV2 (a feature is
broken with a workaround) is handled the same working day; SEV3 (internal only) goes to the backlog. *Options:* (A)
until production, promise response times only, based on these levels, and no uptime percentage; (B) promise an uptime
percentage with service credits, which needs the production setup first. *Proposed answer:* A now, B when production
exists. *Detail:* [incident response](../ops/incident-response.md), "Severity".

## 9. Support address

*Current fact:* the pages give `info@adventure.asia` for questions and privacy requests. The adventure.asia
mailboxes are hosted by DreamHost, which therefore receives any personal data in those e-mails. *Options:* (A) keep
`info@adventure.asia`; (B) create `support@` and forward it into the team's issue tracker (Linear) for triage: the
tracker's free plan has a limit on open items, and e-mail content would put traveller data into the tracker, which would
then have to be listed as a service provider; (C) create `support@` as an alias to a shared mailbox, and let staff open
a tracker item by hand without personal data. *Proposed answer:* C. *Detail:* [register](register.md), section (b),
DreamHost and Linear rows.

## 10. Status page

*Current fact:* there is no public status page. The goal is a $0 option with no new AWS service. *Options:*
(A) a free hosted status page from a status-page provider, which adds a provider to the list; (B) a page built by
scheduled GitHub Actions (for example Upptime) in a **public** repository, where Actions minutes are free. The main
repository is public only until the coding phase ends; once it is private again, a status page there would use the
2,000 free minutes a month that other work also uses; (C) no status page until
the first paying partner. *Proposed answer:* C, then A or B in a public repository. *Detail:* this section.

## 11. Vercel plan

*Current fact:* the Trip Planner, the content system admin and the booking admin run on Vercel's free Hobby plan.
The partner portal moved from Vercel to AWS in October 2026; its old Vercel project stays only as a fallback until
2026-11-03. Vercel describes Hobby as "for personal, non-commercial use", per the S245 research. The engineering decision already taken (D-18) is: Hobby until the first
paying partner, then Pro. Pro costs 20 USD per member per month, plus usage above the amounts the plan includes.
*Options:* (A) move to Pro before the first partner is charged, as D-18 says; (B) move earlier, when the first partner
starts using the portal even if it pays nothing, which the S245 research suggests because Hobby is non-commercial.
Since the portal left Vercel, the Hobby question concerns mainly the Trip Planner, which is the public sales front.
Any new spend needs the tech lead's approval (DM-10.7). *Proposed answer:* A. *Detail:*
[`04-economics-compliance-security.md`](../audits/2026-10-20-S245-tenant-crm/research/04-economics-compliance-security.md).

## 12. AI acceptable-use clause

*Current fact:* Anthropic's Usage Policy takes effect on 2026-11-12 (the live text was re-read on 2026-10-24)
and reaches partners whose content is written with Claude through Amazon Bedrock. The full AI Schedule for the partner
terms is at Draft v0.2. Since the AA-820 portal change, the portal terms §3 carry a short summary of it (Annex A.4),
still under the "Draft — pending legal review" banner. There are no real or paying partners yet, so nobody needs a
notice: each partner accepts the Schedule when it joins, with its partner agreement. The agency CRM does not call
Claude yet; the Schedule must be part of the agency terms before it does. The business owner's answer is needed by
2026-11-11, one day before the policy takes effect. *Options:* (A) adopt the Schedule as written: the portal summary
is already live before 2026-11-11, the Schedule is attached to every partner agreement at onboarding, and a lawyer's review is optional and
her call; (B) a lawyer reviews the Schedule first, and the portal keeps the summary marked as a draft until then;
(C) adopt it now as in A, and have a lawyer review it before the first paying partner. *Proposed answer:* A or C. With
no partners yet, adopting now costs nothing and covers the 2026-11-12 date; C adds a review before the first partner pays.
*Detail:* [AI acceptable-use clause draft](tenant-terms-ai-clause-draft.md): where each part goes (§0), the Schedule
(§2) and 14 questions for a lawyer (§6).

## Annex A: current text of the four pages

The text below is copied from the page source as rendered: A.1 and A.2 at AA-TripPlanner-Web commit `8327bb0`
(2026-10-28), A.3 and A.4 at AA-Partner commit `a33ccf4` (2026-10-28). The portal pages moved from AA-CIS-App to
AA-Partner with their history (AA-979); their text is the one of 2026-10-20 plus the AA-820 text of A.4 §3
(2026-10-24) and the AI provider list of A.3 §5–§6 and A.4 §3 (2026-10-31, S262, from the
[AI Use Register](../architecture/ai-use-register.md)). Each page shows the banner "Draft — pending legal review". The Trip Planner pages show the version
"Draft v0.1" (20 October 2026), although their text gained the traveller sign-in and Geoapify parts later; the two
portal pages show "Draft v0.3" (31 October 2026) since the provider-list change. Links are shown as their text. The pages
exist in English only. If a page changes after those commits, the live page wins.

Two page-copy follow-ups are known. The portal privacy notice §6 still says that Vercel hosts the portal pages,
although the portal now runs on AWS. The Trip Planner pages changed after 2026-10-20 but still show that date.

### A.0 Points to be confirmed on the four pages

Every "[to be confirmed]" point in A.1 to A.4, with the packet topic that proposes an answer.

| Page, section | Point | Topic |
|---|---|---|
| A.1 §1, A.3 §1 | Data controller entity and registered address | 1 |
| A.2 §1, A.4 §1 | Operating legal entity | 1 |
| A.1 §4, A.3 §4 | Legal basis for each use of the data | 2 |
| A.1 §6 | Full list of service providers, kept in a register | 4 |
| A.1 §7, A.3 §7 | Safeguards for transfers outside the person's country | 7 |
| A.1 §8 | Retention periods: the customer record after the enquiry or booking ends; trips never sent; a sign-in account | 2, 5 |
| A.3 §8 | Retention of publish records and the admin log; account data and content after the account ends | 2, 5 |
| A.1 §9, A.3 §9 | Time to answer a request; the right to complain to a data protection authority | 6 |
| A.1 §11 | Minimum age | 2 |
| A.2 §2 | Booking conditions | 2 |
| A.2 §7 | Limits of liability, warranties and consumer rights | 2 |
| A.2 §8, A.4 §9 | Governing law and competent courts (A.4 §9 also limits of liability) | 2 |
| A.3 §10 | Data processing agreement between the partner and Adventure Asia | 4 |
| A.4 intro | How the terms relate to the signed partner agreement | 2 |
| A.4 §3 | Approval of the AI acceptable-use summary (draft; no longer marked [to be confirmed]) | 12 |
| A.4 §5 | Notice periods, termination, and what happens to the content afterwards | 2 |
| A.4 §6 | Ownership of generated content; licence to the catalog tours | 2 |
| A.4 §7 | Plans, fees and payment terms | 2 |
| A.4 §8 | Service levels and support hours | 8 |

### A.1 Trip Planner: Privacy notice (`/privacy`)

This notice explains what personal data the Adventure Asia Trip Planner (this website) collects, why, who receives it
and what you can ask us to do with it. It covers the Trip Planner only. Adventure Asia's company-wide policy is at
adventure.asia/privacy-policy.

**1. Who we are.** The Trip Planner is run by Adventure Asia. The legal entity responsible for your data (the data
controller) and its registered address are [to be confirmed]. For any privacy question or request, write to
`info@adventure.asia`.

**2. What we collect.** You can browse tours and build a trip without giving us your name or contact details.

- **Your trip.** The destinations, stops, activities, number of days and travellers you choose, and the order of your
  days. It is saved under a random guest identifier, not under your name.
- **What you type in the planner search.** Used to find matching places and activities. Please do not type personal
  details into the search box.
- **Your contact details, only when you send a trip to an advisor.** Your full name, your phone number and/or email
  address, and whether you agreed that an advisor may contact you, with the date and time you agreed.
- **Your account, only if you sign in.** Your email address, which you prove with a code we email you (there is no
  password), is kept by our sign-in service (Amazon Cognito). The planner itself stores only a random account
  identifier and the time you last signed in, and links the trips you plan to it so you can open them on any device.
  When you sign in, the trips planned in this browser before you signed in (and not yet in another account) are added
  to your account, so on a shared computer, sign out when you are done. When you send a trip while signed in, the
  advisor receives your signed-in email, marked as confirmed.
- **Technical data.** Our hosting providers process your IP address, browser type and the pages you request in order to
  deliver the site and keep it secure.

**3. Cookies and browser storage.** We use only what the planner needs to work. We do not use advertising or analytics
cookies.

- **Guest cookie** (set on the planner page only): a random token that proves a saved trip is yours. It cannot be read
  by scripts on the page, and it lasts up to 400 days, renewed each time you use the planner. We store only a one-way
  hash of it.
- **Sign-in cookies** (only if you sign in): your encrypted sign-in session, so you stay signed in for up to 30 days,
  and, for 10 minutes while you enter the emailed code, the step you are on. Scripts on the page cannot read them.
  Signing out removes them, together with the guest cookie of that browser.
- **Browser storage:** the random ids of your current trip, so a reload restores it, and your light or dark display
  choice.

Clearing your browser data removes them; you then start a new trip.

**4. How we use your data.**

- To build, save and show your trip (providing the service you asked for).
- To pass your trip and contact details to an Adventure Asia advisor who contacts you about that trip. We do this only
  after you tick the consent box on the form, and we record that consent with its date, time and source.
- Your consent covers contact about the trip you sent. We do not use it for newsletters or other marketing.
- To keep the service secure and prevent abuse.

The legal basis for each use under the laws that apply to you is [to be confirmed].

**5. AI features.** The planner uses AI models to write the day-by-day description of your trip and to match your
search text to places. These models run on Amazon Bedrock (Amazon Web Services). We send them the contents of your trip
(places, activities, days) and your search text, never your name or contact details. Every itinerary is reviewed by an
Adventure Asia advisor before you book.

**6. Who receives your data.**

- **Adventure Asia advisors**, through Adventure Asia's booking system, which receives the trips you send and keeps the
  customer record. Advisors are notified of a new inquiry by email.
- **Amazon Web Services** — hosting, database, the AI models above (Amazon Bedrock), sign-in (Amazon Cognito) and the
  emails: advisor notifications and sign-in codes (Amazon SES).
- **Vercel** — hosts and delivers this website.
- **Mapbox** — map images and the interactive map. Your browser loads them from Mapbox, which receives your IP address
  and the map area you view.

We do not sell your personal data. The full list of service providers will be kept in a register [to be confirmed].

**7. Where your data is stored.** Our database and servers are in the United States (Amazon Web Services). Vercel and
Mapbox serve the site and maps from locations close to you. The safeguards for transfers outside your country are [to be
confirmed].

**8. How long we keep it.** Retention periods are being set and are [to be confirmed]. The current plan: the copy of
your contact details inside the message that sends your trip to the booking system is removed after 90 days, and the
customer record in the booking system is kept while your enquiry or booking is active and then for a period [to be
confirmed]. Trips that were never sent [retention to be confirmed]. A sign-in account is kept while it is in use and is
erased with its link to your trips on request [period to be confirmed].

**9. Your rights.** You can ask us to show you the data we hold about you, correct it, delete it, or stop contacting
you, and you can withdraw your consent at any time. Write to `info@adventure.asia`. The time within which we answer, and
your right to complain to a data protection authority, are [to be confirmed].

**10. Security.** The site uses encrypted connections (HTTPS). Our database is not reachable from the internet, and
access to it is limited to the systems that need it. No method is perfectly secure; if a breach affects your data we
will inform you as the law requires.

**11. Children.** The Trip Planner is not meant for children. The minimum age is [to be confirmed].

**12. Changes to this notice.** We will publish changes on this page with a new date. See also our Terms of use.

### A.2 Trip Planner: Terms of use (`/terms`)

These terms apply when you use the Adventure Asia Trip Planner (this website). By using it you accept them. If you do
not agree, please do not use the site.

**1. What the Trip Planner is.** The Trip Planner is a free tool for exploring Adventure Asia tours and shaping a trip
idea day by day. It is run by Adventure Asia; the operating legal entity is [to be confirmed].

**2. A trip plan is not a booking.**

- A trip you build or send to an advisor is an enquiry. Nothing is reserved or paid, and no contract for travel services
  is made through this site.
- An Adventure Asia advisor reviews your trip and contacts you to confirm logistics, availability and price. A booking
  exists only when you agree to it with Adventure Asia under separate booking conditions [booking conditions to be
  confirmed].
- Prices, availability and itineraries shown on the site are indicative and can change.

**3. AI-assisted content.** Some descriptions on the site, including the day-by-day text of your trip, are written with
the help of AI and are labelled as such. They can contain mistakes. Do not rely on them for travel, visa, health or
safety decisions; your advisor confirms the details before anything is booked.

**4. Using the site.**

- Give accurate contact details when you send a trip, and only your own.
- Use the site only for planning your own travel, and in line with the law.
- Do not try to access other people's trips, overload or disrupt the service, or copy its content in bulk with
  automated tools.

We may limit or block access that breaks these rules.

**5. Content and maps.** The tours, texts, photos and design of the site belong to Adventure Asia or its licensors. Maps
are provided by Mapbox and OpenStreetMap contributors under their own terms. Place locations are geocoded with Geoapify
(geoapify.com) from OpenStreetMap data (© OpenStreetMap contributors, ODbL); a place we could only place approximately
is shown as an area, not as an exact point. You may use the site for your personal, non-commercial trip planning.

**6. Availability and changes.** The site is under active development. Features can change, and the site may be
unavailable at times. We may update these terms; the date at the top of the page shows the current version.

**7. Liability.** Limits of liability, warranties and consumer rights under the laws that apply to you are [to be
confirmed].

**8. Governing law.** The governing law and competent courts are [to be confirmed].

**9. Contact.** Questions about these terms: `info@adventure.asia`. How we handle personal data is described in our
Privacy notice.

### A.3 Partner Portal: Privacy notice (`/privacy`)

This notice explains what personal data the Adventure Asia Partner Portal collects about partner businesses and the
people who use it, why, and who receives it. Adventure Asia's company-wide policy is at adventure.asia/privacy-policy.

**1. Who we are.** The Partner Portal is run by Adventure Asia. The legal entity responsible for your data (the data
controller) and its registered address are [to be confirmed]. Privacy questions and requests: `info@adventure.asia`.

**2. What we collect.**

- **Partner account.** Your business name, plan and account status, and the API key you sign in with. We check the key
  on our server; the browser then holds a sign-in session.
- **Brand settings and content.** The brand voice and settings you enter, the tour rewrites and social or blog pieces
  generated for you, and your edits.
- **Channel connections.** The details you give us to publish to your own channels (for example a WordPress site or a
  Facebook Page).
- **Activity records.** Each AI model call (provider, model, cost, time, partner and job), each publish and unpublish
  (piece, channel, post id, status, time, and whether your account or an Adventure Asia admin acted), and an admin log
  of changes to partner accounts.
- **Technical data.** IP address, browser type and request logs, processed by our hosting providers and our security
  systems.

**3. Cookies.** The portal uses only sign-in cookies, which scripts on the page cannot read. They hold your session and
expire after 24 hours or when you sign out. We do not use advertising or analytics cookies.

**4. How we use your data.**

- To run your account and produce the content you ask for.
- To publish or unpublish a piece on your channels when you tell us to.
- To support you, keep the service secure, and enforce the partner terms.
- To measure our own costs and service quality.

The legal basis for each use is [to be confirmed].

**5. AI processing.** Content is generated and checked by AI models. Claude (Anthropic), through Amazon Bedrock, writes
it; OpenAI models, also through Amazon Bedrock, review, score and check the drafts. If Amazon Bedrock is unavailable, the
Anthropic API or the OpenAI API, used directly and with a spending cap, may be used as a fallback; those calls go from
Amazon Web Services to Anthropic or OpenAI. For some partners, a decision-checking service (Jev, by TypeSafe) also answers
yes-or-no checks about the drafts. These providers receive tour content, your brand settings and the instructions for each
piece. Our policy is not to send personal data to these models and not to store any in our AI call records, so please do
not enter personal data about other people in brand settings or content.

**6. Who receives your data.**

- **Adventure Asia staff**, for support and moderation (they can suspend an account or unpublish a post that Adventure
  Asia published for you).
- **Amazon Web Services** — hosting, database, Amazon Bedrock.
- **Vercel** — hosts and delivers the portal pages.
- **AI providers** — Anthropic and OpenAI (through Amazon Bedrock, and directly only as a fallback), and Jev (TypeSafe)
  for some partners, as described above.
- **Your channels** (for example WordPress or Meta), when you publish to them.

We do not sell personal data.

**7. Where your data is stored.** Our database and servers are in the United States (Amazon Web Services). The
safeguards for transfers outside your country are [to be confirmed].

**8. How long we keep it.**

- AI model call records: 180 days.
- Security logs: 365 days.
- Publish records and the admin log: a period will be set before production [to be confirmed].
- Account data and content: while your account is active, then [to be confirmed].

**9. Your rights.** You can ask to see, correct or delete personal data we hold about you. Write to `info@adventure.asia`.
Response times and your right to complain to a data protection authority are [to be confirmed].

**10. Data about your own customers.** If you put personal data of other people into the portal, you are responsible
for having the right to do so. A data processing agreement between you and Adventure Asia is [to be confirmed].

**11. Changes to this notice.** We will publish changes on this page with a new date. See also the partner terms.

### A.4 Partner Portal: Partner terms (`/terms`)

These terms apply to partner businesses that use the Adventure Asia Partner Portal and its API. They will form part of,
or sit next to, the partner agreement you sign with Adventure Asia [relationship to be confirmed].

**1. The service.** The portal gives you Adventure Asia catalog tours rewritten in your brand voice, social and blog
pieces about those tours, and tools to export them or publish them to your own channels. The operating legal entity is
[to be confirmed].

**2. Your account and API key.**

- Keep your API key secret. Activity under your key is treated as yours.
- Tell us at once at `info@adventure.asia` if you think the key is known to someone else, so we can revoke it.

**3. AI-generated content and acceptable use.**

- Content is generated with AI and can contain mistakes. The portal shows this at review, publish and export: "This
  content was generated with AI. Review it before publishing; you are responsible for what you publish."
- The content is written and checked with models from third-party providers: Anthropic's Claude, through Amazon Bedrock
  (Amazon Web Services), writes it, and OpenAI models, also through Amazon Bedrock, review, score and check it. If Amazon
  Bedrock is unavailable, the Anthropic API or the OpenAI API, used directly and with a spending cap, may be used as a
  fallback.
- You must follow these providers' usage policies, including the Anthropic Usage Policy, the OpenAI Usage Policies and
  the AWS Acceptable Use Policy, as well as these terms.
- You must not use the portal or its content for:
  - fake reviews, ratings or testimonials, or quotes and stories presented as coming from customers who did not give
    them;
  - invented personas, sockpuppet accounts, or content attributed to a real person who did not write or approve it;
  - astroturfing, or networks of websites or accounts that look independent but are not;
  - hiding sponsorship or a commercial relationship, or removing a disclosure the law or a channel requires;
  - seeding search engines or AI systems with content that misrepresents its origin, authorship or independence;
  - spam, or posting meant to get around the publishing limit;
  - false or misleading information, in particular about visas and entry rules, health, safety, prices or
    availability;
  - advice on insurance, finance, visas or other high-risk matters, unless a qualified person reviews it before it is
    delivered and the person receiving it is told that AI was used;
  - getting around Adventure Asia's content checks, limits or other safeguards.
- If the law or a channel's rules require content to be labelled as AI-generated, you add that label.
- You review each piece before it is published, and you are its publisher. Telling Adventure Asia to publish a piece,
  in the portal or through the API, confirms that you have reviewed it.
- Adventure Asia may hold, rewrite or decline to generate or publish content that breaks these rules. Unpublishing and
  suspension are covered in sections 4 and 5.

**4. Publishing to your channels.**

- Adventure Asia publishes a piece to your channels only when you tell it to publish that piece, using the access you
  connected. The post appears under your name.
- There is a daily limit on the number of posts Adventure Asia publishes for you.
- You can unpublish your posts. Adventure Asia can also unpublish a post it published for you, for example when it
  breaks these terms.

**5. Suspension and ending the service.** Adventure Asia may suspend an account, which stops its API access and
publishing at once, for example to protect the service or when these terms are broken. Notice periods, termination and
what happens to your content afterwards are [to be confirmed].

**6. Content rights.** Who owns the generated content and the licence to the catalog tours are [to be confirmed].

**7. Plans and fees.** Plans, fees and payment terms are [to be confirmed].

**8. Availability.** The portal is under active development; features can change and the service may be unavailable at
times. Service levels and support hours are [to be confirmed].

**9. Liability and governing law.** Limits of liability, the governing law and the competent courts are [to be
confirmed].

**10. Contact.** Questions: `info@adventure.asia`. How we handle personal data is described in the privacy notice.
