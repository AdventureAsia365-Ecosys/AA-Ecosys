# TravelJoy (traveljoy.com): feature teardown

- **Product:** TravelJoy, an all-in-one CRM, itinerary/proposal builder, payments and booking platform for independent (mostly US, host-affiliated) travel advisors.
- **Research date:** 2026-10-20.
- **Method:** public sources only. These were the marketing site, the pricing and premium pages, the TravelJoy blog (product-update posts), help-center article titles and search-indexed excerpts, the Zapier app listing, app-store listings and third-party reviews (Host Agency Reviews, Trustpilot, G2, Tripkit, jess.travel). No sign-up, no login, no scraping, no reverse engineering.
- **Source caveat:** `help.traveljoy.com` returns HTTP 403 to direct automated fetches. Help-center facts below come from search-engine excerpts of the named article, so each citation points to that article's URL. Excerpts may lag the live article.
- **Labels:** "inferred" marks anything not stated publicly. Third-party and competitor sources are labelled as such.

---

## 0. Product shape at a glance

| Item | Finding | Source |
|---|---|---|
| Positioning | Six pillars: "Group trip management", "Payments and authorizations", "All-in-one CRM", "AI and automation", "Itinerary builder", "Booking platform". | https://traveljoy.com/ |
| Core object | The **Trip**. Trips "can be thought of as file folders": they hold all communication, documents, invoices and more for one trip. Each trip page has Messages, Files, Tasks and private Notes tabs. | https://help.traveljoy.com/hc/en-us/articles/360016089792-Create-and-manage-an-individual-trip |
| Secondary objects | Client (contact) profile, Supplier contact, Group (a collection of trips with a shared destination or theme), Form/Template, Invoice, Library item. | https://help.traveljoy.com/hc/en-us/articles/48027861867412-Groups-in-TravelJoy-An-Overview ; https://help.traveljoy.com/hc/en-us/articles/9484158141076-Pay-your-suppliers |
| Target user | Solo advisors and small teams. Most Host Agency Reviews reviewers are "solo travel agency". Cruise booking is under "your IATA or your host's IATA". | https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews ; https://traveljoy.com/cruises.html |
| Release cadence | Release notes since Feb 2022. Monthly blog "product updates" posts in 2026 (Jan 23, Feb 9, Jul 31). | https://help.traveljoy.com/hc/en-us/articles/45082755210772-See-what-s-new-with-TravelJoy ; https://traveljoy.com/blog/traveljoy-news-and-updates |

---

## 1. Client / contact records and profiles

**What it does.** Contacts hold client profiles (preferences, loyalty numbers, past trips) and supplier contacts. Profiles feed forms, trips, reminders and the AI "Client opportunities" list.

| Aspect | Detail | Source |
|---|---|---|
| Profile contents | "clear, easy-to-use profiles" storing client preferences, loyalty numbers and past trips. | https://traveljoy.com/blog/post/traveljoy-a-comprehensive-crm-for-travel-agents |
| Traveler data in trip sidebar | Passport information, loyalty numbers and dates of birth can be viewed and copied from the trip sidebar (Feb 2026). | https://traveljoy.com/blog/post/product-updates-faster-invoicing-email-campaigns-and-more |
| Passport | Passport images are stored on a "Passport Info" tab of the profile. A "Client Passport Photo" form field lets the client upload their own. **Limit: one passport image per profile.** Multiple travelers need one form submission each, and each traveler needs an email address. | https://help.traveljoy.com/hc/en-us/articles/360047051511-Collect-and-store-client-passport-photos |
| Passport parsing (AI) | "Upload documents and let tools like Magic Importer and passport parsing extract the data for you automatically." | https://traveljoy.com/ai.html |
| Custom fields | Profiles are customizable. Custom fields can be added to forms so clients fill them in. Any form field whose name starts with "Client" maps to the profile card, and the same client field cannot appear twice on one form (forms capture one traveler at a time). | https://help.traveljoy.com/hc/en-us/articles/360016307211-Create-a-form-template ; https://www.youtube.com/watch?v=-Ho1MRXmDVM |
| Families / additional travelers | A primary traveler can submit the form for each companion via an "Add Traveler" button on the confirmation page. Each companion gets a profile and is attached to the trip. Travelers can be added or removed on a trip. | https://help.traveljoy.com/hc/en-us/articles/360016308471-Can-the-client-fill-out-a-form-multiple-times-to-cover-additional-travelers ; https://help.traveljoy.com/hc/en-us/articles/360016089772-Add-or-remove-additional-travelers-on-a-trip |
| Household / family entity | No household object is described publicly. Families are modelled as several traveler profiles attached to one trip (**inferred**). | — |
| Import | Client list import (CSV, **inferred** format). Task list import. | https://help.traveljoy.com/hc/en-us/articles/360016022032-Import-your-client-list |
| Files on client | "Upload and store client files" lives under the help section "Clients and suppliers". | https://help.traveljoy.com/hc/en-us/categories/33837415650708-Using-TravelJoy |
| Important dates | Birthday, anniversary and passport expiration drive automated client reminder emails (see §3). | https://help.traveljoy.com/hc/en-us/articles/36032853714324-Send-automated-birthday-anniversary-or-passport-expiration-emails-to-your-clients |

**Reviewer feedback**
- Praise: "A huge step from word & spreadsheets!" Another reviewer switched for "Better CRM features". Source: https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews
- Complaint: a reviewer wants to sort clients by status and year for exports and marketing (no such segmentation today). Source: same page.

---

## 2. Leads and inquiry intake

| Aspect | Detail | Source |
|---|---|---|
| Embedded inquiry form | Pick the "Client Inquiry (default)" or a custom template, click "Embed Form" and paste the code into your website. **Each submission creates a new Trip on the dashboard and a new client profile card.** Duplicate submissions create duplicate trips, which can be merged. Submissions are logged under a Responses tab, and the client gets the template's confirmation email. | https://help.traveljoy.com/hc/en-us/articles/360016308691-Embed-a-client-inquiry-form-on-your-website |
| Public inquiry page | A standalone hosted page (Feb 2026) to link from social media, link-in-bio tools or an email signature. It feeds the existing inquiry form. | https://traveljoy.com/blog/post/meet-your-new-marketing-tab |
| Shareable form template | Public share links for templates exist, e.g. `traveljoy.com/share/questionnaire_templates/...`. | https://traveljoy.com/share/questionnaire_templates/5une8Fn9gMeqrjQek8HQ9ebh |
| Form builder | Conditional logic and page breaks (Jan 2026). Magic Importer can generate a form from a URL, image or screenshot. Error auto-scroll (2025). | https://traveljoy.com/blog/post/product-updates-smarter-forms-easier-approvals-and-more ; https://help.traveljoy.com/hc/en-us/articles/45082755210772-See-what-s-new-with-TravelJoy |
| Email parsing of inbound leads | **Not supported.** External inquiries still arrive in Gmail/Outlook and do not flow into TravelJoy (third-party, competitor claim). Magic Email parses *supplier* confirmations, not leads. | https://journeyfuse.com/compare/traveljoy (competitor) ; https://traveljoy.com/blog/post/product-updates-crm-groups-proposals-and-more |
| Lead stage | There is no separate Lead object: an inquiry is a Trip in an early stage (**inferred** from "each submission creates a new trip"). | https://help.traveljoy.com/hc/en-us/articles/360016308691-Embed-a-client-inquiry-form-on-your-website |

**Reviewer feedback**
- Praise: "I love the embedded client inquiry form in TravelJoy." Source: https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews

---

## 3. Pipeline, workflow automation, tasks and reminders

| Aspect | Detail | Source |
|---|---|---|
| Dashboard pipeline | Shows every trip, the stage it is in and what needs action. You can search by client, invoice, trip or group. Clicking a stage lists all trips in it, for batch work such as following up proposals awaiting approval. | https://help.traveljoy.com/hc/en-us/articles/360016247971-Using-the-Dashboard |
| Stage vs. status | A trip has both a **stage** (pipeline step; Zapier exposes `update_trip_stage`) and a **status** of "waiting on" **you / traveler / supplier / None** ("None" added Feb 2025). The stage list itself is not published, and whether stages are fixed or configurable is **inferred** to be fixed. | https://help.traveljoy.com/hc/en-us/articles/360016089792-Create-and-manage-an-individual-trip ; https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025 ; https://zapier.com/apps/traveljoy/integrations |
| Task list templates | Prebuilt task collections imported into any trip or group "in three clicks". **Max 30 tasks per list.** | https://help.traveljoy.com/hc/en-us/articles/360016089212-Create-a-task-list-template |
| Auto-apply rule 1 | Settings → Automation: a template is applied to **all new trips**. This affects only trips created after the change, and only trips that have start and end dates. | https://help.traveljoy.com/hc/en-us/articles/6024164844180-Automatically-add-a-task-list-to-all-new-trips |
| Auto-apply rule 2 | **Trip tags** (e.g. "disney", "cruise") auto-import the matching task list (Jan 2026). | https://traveljoy.com/blog/post/product-updates-smarter-forms-easier-approvals-and-more |
| Task automations | Tasks can be "automated", i.e. send an email or reminder (**inferred** from the docs' wording). Automations fire immediately on task list import (Jan 27, 2026). Task assignment to team members with notifications (Jan 23, 2026). | https://traveljoy.com/blog/post/product-updates-faster-invoicing-email-campaigns-and-more ; https://help.traveljoy.com/hc/en-us/articles/45082755210772-See-what-s-new-with-TravelJoy |
| Form follow-up | Settings → Automation: days after send plus send time. Uses the editable "Form Follow-up (default)" email template. | https://help.traveljoy.com/hc/en-us/articles/40443173634964-Set-up-automated-form-reminders |
| Proposal follow-up | Same mechanism, with the "Proposal Follow-up (default)" template. | https://help.traveljoy.com/hc/en-us/articles/40442701359764-Set-up-automated-proposal-reminders |
| Payment reminders | Payment schedules generate reminder tasks. These email the **agent** by default and can be switched to email the **client** directly. SMS payment reminders are available with the SMS add-on (Jan 2026). | https://help.traveljoy.com/hc/en-us/articles/360051796412-Automatically-send-payment-reminders-to-clients ; https://traveljoy.com/blog/post/product-updates-smarter-forms-easier-approvals-and-more |
| Client reminders | Automated birthday, anniversary and passport-expiration emails (formerly "Important dates", now under the Marketing tab). | https://traveljoy.com/blog/post/meet-your-new-marketing-tab |
| Scheduled emails | Messages can be scheduled. Since Feb 2025 a manual override sends one immediately. | https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025 |
| Calendar | Syncs with Google Calendar and Outlook. | https://traveljoy.com/blog/post/traveljoy-a-comprehensive-crm-for-travel-agents |
| Plan gating | "AI and automations" are **Pro and above only**. Starter is described as "deliberately manual" (third-party). | https://traveljoy.com/pricing ; https://tripkit.com/traveljoy-reviews |

**Reviewer feedback**
- Praise: "The automated tasks are priceless; I never miss a beat".
- Praise: templates, forms and automated reminders are "SUCH a timesaver!"
- Praise: "I've never missed a final payment or deadline, thanks to TJ!"
- Complaint: wants more customization of automated emails.
- Source for all four: https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews

---

## 4. Itinerary and proposal builder

| Aspect | Detail | Source |
|---|---|---|
| Three document types | **Itinerary** (no client approval needed), **Smart proposal** (client reviews and approves, then it converts into the itinerary) and **Proposal** (legacy or simple type; the help article "What's the Difference?" exists, and the exact difference is **inferred**). | https://help.traveljoy.com/hc/en-us/articles/4407244320532-Create-an-Itinerary-or-Smart-proposal ; https://help.traveljoy.com/hc/en-us/articles/37209140980884-Itineraries-Smart-Proposals-and-Proposals-What-s-the-Difference |
| Option sets | Several choices per item (hotels, activities, cruise cabins). Each group is single-select or multi-select. The client sees all options in one place and approves the preferred ones. The selection appears in the trip feed and the approval email. | https://traveljoy.com/blog/post/travel-advisor-itinerary-maker-now-offers-options ; https://traveljoy.com/blog/post/product-updates-smarter-forms-easier-approvals-and-more |
| Approve + pay in one step | The client approves and authorizes supplier payment in one step, and an invoice is auto-created in the trip's Files tab (Feb 2025). | https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025 |
| Price display | Itemized costs or a single total price. | same |
| Live document | "build once, share with the client, and continue updating in the same document". After approval the proposal becomes a live itinerary and edits appear for the client in real time. | https://traveljoy.com/blog/post/create-client-ready-itineraries-in-minutes-with-itinerary-copilot |
| Library | Reusable items and whole sections (2025), shareable with the team (Feb 2025). Template folders and bulk actions (Jul 2026). | https://help.traveljoy.com/hc/en-us/articles/34287790008724-See-what-s-new-with-TravelJoy ; https://traveljoy.com/blog/post/product-updates-crm-groups-proposals-and-more |
| Editor UX | Drag-and-drop editor, customizable templates (third-party listing). Expandable sidebar. Image hover previews (Jan 2026). Selective hotel photo import (Jul 2026). | https://hostagencyreviews.com/travel-agency-software/traveljoy ; https://traveljoy.com/blog/post/product-updates-smarter-forms-easier-approvals-and-more |
| Booked items | Booked hotels, Viator activities and transfers sync into itineraries automatically. | https://traveljoy.com/blog/post/how-to-search-quote-and-book-on-traveljoy |
| Data fields (from Magic Email) | Dates, times, locations, booking references and inclusions are mapped into itinerary/proposal sections. | https://www.thetraveler.org/traveljoys-magic-email-brings-ai-to-booking-busywork/ |

**Reviewer feedback**
- Praise: "I love how easy this program has made quoting and itinerary building". Trips "look so professional". Sources: https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews ; https://www.trustpilot.com/review/traveljoy.com
- Complaint: "Itinerary output trails Travefy, AXUS and Safari Portal noticeably". Source: https://tripkit.com/traveljoy-reviews (competitor, 3rd party)
- Complaint: "Would love more pictures already loaded in of hotels and activities". An early reviewer said itinerary creation needed simplifying, which has since been addressed. Source: https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews
- An advisor guide (2020) called the proposal-to-itinerary conversion "quick and looks ok". Source: https://www.jess.travel/post/sample-client-start-to-finish

---

## 5. Quotes, invoicing, payments and commissions

**Two invoice types are the core concept.**

| Aspect | Detail | Source |
|---|---|---|
| Direct invoice | Charges the client's card or ACH. Money lands in the trip's or group's **Funds** balance, which can pay suppliers or be withdrawn as earnings. | https://traveljoy.com/blog/post/how-travel-advisors-can-handle-payments-like-a-pro-a-recap-of-traveljoys-payments-workshop |
| Supplier invoice | **Authorization only.** Card details and a signed permission are stored and nothing is charged. The advisor uses them to pay the supplier. "card details are never stored on TravelJoy's servers" (PCI). | same ; https://help.traveljoy.com/hc/en-us/articles/9483414497812-Collect-payments-or-authorizations-from-your-clients |
| CC authorization form | Create → Form → "Credit Card Authorization". The result arrives as an attachment in the trip message feed. Authorizations can be converted to a direct payment. | https://help.traveljoy.com/hc/en-us/articles/360016023452-Request-a-credit-card-authorization-via-form ; https://help.traveljoy.com/hc/en-us/articles/9484724806292-Withdraw-funds-from-TravelJoy |
| Planning fees | "Invoice (Planning Fee)". Paid fees go straight to the connected bank account and bypass Funds. | https://traveljoy.com/blog/post/how-travel-advisors-can-handle-payments-like-a-pro-a-recap-of-traveljoys-payments-workshop |
| Payment schedules | Splits the remaining balance into equal payments with due dates and auto-generates reminder tasks. | same |
| Magic Importer (invoicing) | Upload a supplier PDF and it extracts "Package details, totals, payment schedules, dates, confirmation numbers" into a branded invoice. | same ; https://traveljoy.com/blog/post/product-updates-faster-invoicing-email-campaigns-and-more |
| Paying suppliers | From Funds via **virtual credit card** (AUTHORIZED state, supplier captures in 1–2 business days) or wire. Markup can be withdrawn. | https://help.traveljoy.com/hc/en-us/articles/9484158141076-Pay-your-suppliers ; https://help.traveljoy.com/hc/en-us/articles/18509612952596-Virtual-Cards-What-are-they-and-how-do-they-work |
| Bank account | Required for any direct payment processing. | https://help.traveljoy.com/hc/en-us/articles/6191729546644-Trip-Funds-Group-Funds-FAQ |
| Processing fees | Starter: card 5% + 30c, ACH 3%. Pro/Premium: card 3.5% + 30c, ACH 1.5%. | https://traveljoy.com/pricing |
| Commission fields (per invoice line) | Supplier Type, Booking Date, Commission Split (host %), Expected Commission Date, Total Commission. The advisor's share is auto-calculated. Commission is internal and never shown to the client. | https://www.jess.travel/post/how-to-track-travel-agent-commissions-in-traveljoy (3rd party) |
| Commissions & Sales report | Four tabs. A Suppliers view shows expected, collected and past-due commission by supplier. Date filters. One version per invoiced currency (USD default). Requires Booking Date. **Markup is not reported separately.** | https://help.traveljoy.com/hc/en-us/articles/360016090912-Commissions-Sales-Reports |
| Team commission | Auto-split of team sales between owner and member (Feb 2025). Statements and Team payouts tabs reconcile supplier commission statements against bookings and track payouts to members (Jul 2026). | https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025 ; https://traveljoy.com/blog/post/product-updates-crm-groups-proposals-and-more |
| In-platform booking commission | Hotels 12% (plus markup; client discounts reduce it), activities and transfers 8% (Viator), insurance 24% (Faye). Paid "automatically through the platform". Hotel commission is paid to a linked bank account within a week of travel completion. | https://traveljoy.com/blog/post/how-to-search-quote-and-book-on-traveljoy ; https://help.traveljoy.com/hc/en-us/articles/30747881190036-Find-propose-and-book-hotels-with-TravelJoy |
| Mark unpaid | Payments can be marked unpaid from the invoice (Feb 2026). | https://traveljoy.com/blog/post/product-updates-faster-invoicing-email-campaigns-and-more |

**Reviewer feedback**
- Praise: forms and payments scored 4.7/5; clients complete authorizations "without hand-holding". Source: https://tripkit.com/traveljoy-reviews (3rd party)
- Complaint: the card fee of "3.5% plus $0.30 per transaction" is "a bit high compared to other platforms". The reviewer also wants more invoice customization. Source: https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews
- Complaint: a 1-star review reports an unauthorized $300 debit and an account-lock threat tied to client chargebacks. TravelJoy replied that disputed funds may be held. Source: https://www.trustpilot.com/review/traveljoy.com

---

## 6. Supplier and partner records

| Aspect | Detail | Source |
|---|---|---|
| Supplier contacts | Contacts → Suppliers → "Add contact". The "Supplier name" field holds the business name. | https://help.traveljoy.com/hc/en-us/articles/9484158141076-Pay-your-suppliers |
| Supplier on line items | Entering a supplier on an invoice or group-booking item enables the Suppliers tab of the commission report. | https://help.traveljoy.com/hc/en-us/articles/360016090912-Commissions-Sales-Reports |
| Export | "Export your supplier contacts" (09/30/2026). | https://help.traveljoy.com/hc/en-us/articles/45082755210772-See-what-s-new-with-TravelJoy |
| Contract rates / allotments | Not described publicly. TravelJoy is not a DMC or inventory tool, and suppliers are mainly payees and commission sources (**inferred**). | — |

---

## 7. Email and messaging

| Aspect | Detail | Source |
|---|---|---|
| Per-trip message feed | Every message, form response and authorization attaches to the trip feed. | https://help.traveljoy.com/hc/en-us/articles/360016089792-Create-and-manage-an-individual-trip |
| Sending identity | Connect Gmail/Google Workspace ("Sign in with Gmail" under Settings → Messaging), Microsoft (Office 365, Outlook, Hotmail, Live) or a custom domain, so clients see the advisor's address. | https://help.traveljoy.com/hc/en-us/articles/360028239552-Connect-your-Google-Mail-account-to-TravelJoy ; https://help.traveljoy.com/hc/en-us/articles/360030721131-Help-clients-recognize-your-messages-by-connecting-your-business-email-account-to-TravelJoy |
| Inbox sync | **Send-only.** No two-way sync of the advisor's existing mailbox is described (third-party; **inferred** from docs). | https://aiemaily.com/blog/best-crm-email-software-for-travel-advisors (3rd party) |
| Templates | Editable email templates under Settings → Email Templates (e.g. Form Follow-up, Proposal Follow-up). Message drafts (Jul 2026). | https://help.traveljoy.com/hc/en-us/articles/40443173634964-Set-up-automated-form-reminders ; https://traveljoy.com/blog/post/product-updates-crm-groups-proposals-and-more |
| SMS (add-on) | Text clients inside trip feeds with one inbox, and send SMS announcements to groups. Dedicated local number, **up to 1,000 msgs/month, $49/mo**. SMS templates. | https://traveljoy.com/premium.html ; https://traveljoy.com/blog/post/product-updates-smarter-forms-easier-approvals-and-more |
| Email campaigns | Drag-and-drop builder that sends to TravelJoy contacts, with unsubscribe management. **Pro: 12 campaigns × 300 recipients per calendar year.** Unlimited costs $29/mo. No segmentation is mentioned. | https://traveljoy.com/blog/post/meet-your-new-marketing-tab |

**Reviewer feedback**
- Complaint: wants better email aesthetics for clients. Source: https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews
- Praise: a reviewer switched to TravelJoy for the "Ability to send emails- forms-look and feel". Source: same page.

---

## 8. Client portal and mobile

| Aspect | Detail | Source |
|---|---|---|
| Client app | "Itineraries by TravelJoy" (iOS and Android, free). Clients view itineraries, documents and images, **offline**, and can message the advisor. **No push notifications. US-only.** | https://help.traveljoy.com/hc/en-us/articles/21439262542484-Send-our-app-for-itineraries-to-your-clients ; https://play.google.com/store/apps/details?id=com.traveljoy.app |
| App rating | App Store: 4.6–4.7 from about 27–28 ratings. Requires iOS 15.6+. | https://apps.apple.com/us/app/-/id6464438601 |
| Web client view | Clients act through emailed links to forms, smart proposals, invoices and group booking pages. No logged-in client portal is described (**inferred**). | — |
| Advisor mobile app | No advisor-side native app is publicly described, and a directory lists the agency app as unavailable. One reviewer praises "complete access to my business from anywhere" (likely the web app, **inferred**). | https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews |

---

## 9. Documents and e-signature

| Aspect | Detail | Source |
|---|---|---|
| Forms as contracts | Forms collect client details, signed agreements and authorizations. Example uses: insurance waiver (client signs off on declining insurance) and terms. | https://help.traveljoy.com/hc/en-us/articles/360016308711-Send-forms-to-collect-client-details-signed-agreements-and-authorizations ; https://www.jess.travel/post/sample-client-start-to-finish |
| Audit log | Records when a form is sent, opened and signed, **including IP addresses** (Feb 2025). | https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025 |
| Files | The trip Files tab holds invoices and authorizations (since Feb 2025). There is also a "File cabinet". | same ; https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews |
| Upload from dashboard | Upload documents and create proposals from the dashboard (Jul 23, 2026). | https://help.traveljoy.com/hc/en-us/articles/45082755210772-See-what-s-new-with-TravelJoy |

**Reviewer feedback (complaints)**
- "Subfolders in the File cabinet would help document organization."
- "I wish TJ would keep the name I give it" (when uploading documents).
- Source for both: https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews

---

## 10. Groups (a major differentiator)

| Aspect | Detail | Source |
|---|---|---|
| Model | A Group is a collection of trips. Each booking creates its own trip and invoice inside the group. **One itinerary per group.** | https://help.traveljoy.com/hc/en-us/articles/48027861867412-Groups-in-TravelJoy-An-Overview ; https://help.traveljoy.com/hc/en-us/articles/31469144224148-Create-a-group-itinerary |
| Booking page | "combines your itinerary, an intake form, and a checkout flow into a single shareable link". | https://traveljoy.com/blog/post/how-to-book-group-travel-like-a-pro-traveljoys-first-groups-workshop |
| Packages and extras | Each package is tied to a group-itinerary item, with single and double occupancy pricing and a computed per-person cost. Extra options are add-ons. Inventory caps show a package as sold out. Each booking has a minimum and maximum traveler count. | same ; https://help.traveljoy.com/hc/en-us/articles/18811310252180-Build-and-edit-packages-for-your-group-booking-page ; https://help.traveljoy.com/hc/en-us/articles/18811281673620-Build-and-edit-extra-options-for-your-group-booking-page |
| Deposits | Per person or per room. Full payment can be required (Mar 2026). Percentage deposits and child pricing bands are in beta (Jul 2026). | https://help.traveljoy.com/hc/en-us/articles/360016308231-Build-your-first-group-booking-page ; https://traveljoy.com/blog/post/product-updates-crm-groups-proposals-and-more |
| Discount codes | Fixed or percentage, with expiry (Jan 2026). | https://traveljoy.com/blog/post/product-updates-smarter-forms-easier-approvals-and-more |
| Group Status / rooming | Real-time view of who booked, who paid and who rooms with whom. Move travelers between rooms and combine roommates. Rooming list exports to a spreadsheet. | https://traveljoy.com/blog/post/how-to-book-group-travel-like-a-pro-traveljoys-first-groups-workshop |
| Plan | Pro and above. | https://traveljoy.com/pricing |

**Reviewer feedback**
- Praise: "One of the strongest group workflows at any price in this category". Source: https://tripkit.com/traveljoy-reviews (3rd party)
- Complaint: wants the group booking page process to be "easier". Source: https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews

---

## 11. Booking platform (embedded inventory)

| Aspect | Detail | Source |
|---|---|---|
| Inventory | Hotels (300K+), Viator activities and transfers, insurance (Faye; Arch RoamRight since 2026), cruises. | https://traveljoy.com/blog/post/how-to-search-quote-and-book-on-traveljoy ; https://traveljoy.com/blog/post/product-updates-crm-groups-proposals-and-more |
| Cruises | Search the cruise library, show sailings side by side in a proposal, and book under your or your host's IATA. The host pays commission and TravelJoy "does not receive or distribute your cruise commission". Included in Pro and Premium via a **waitlist**, with priority for partner hosts. | https://traveljoy.com/cruises.html |
| Viator limits | Outside Viator links cannot be booked through TravelJoy. | https://help.traveljoy.com/hc/en-us/articles/27765263323412-Find-propose-and-book-activities-and-transfers-from-Viator |
| GDS / air | **None.** "No GDS or booking inventory — searching and ticketing stay in other tools" (3rd party). | https://tripkit.com/traveljoy-reviews |

**Reviewer feedback**
- Praise: the Viator integration is "a game changer".
- Complaint: "I don't feel like direct booking for clients highlights the agent's value."
- Source for both: https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews

---

## 12. Reporting and analytics

| Aspect | Detail | Source |
|---|---|---|
| Reports | Sales, commissions and performance metrics. The main report is Commissions & Sales (see §5). | https://traveljoy.com/blog/post/traveljoy-a-comprehensive-crm-for-travel-agents ; https://help.traveljoy.com/hc/en-us/articles/360016090912-Commissions-Sales-Reports |
| Team reporting | Owners can grant members or assistants a team-wide report view. | https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025 |
| Dashboard | Pipeline by stage plus "waiting on" filters (see §3). | https://help.traveljoy.com/hc/en-us/articles/360016247971-Using-the-Dashboard |
| Gaps | No custom report builder, conversion funnel or marketing attribution is described (**inferred** from absence). | — |

---

## 13. Team, roles and permissions

| Aspect | Detail | Source |
|---|---|---|
| Roles | **Owner**, **Team member** and **Assistant**. | https://help.traveljoy.com/hc/en-us/articles/360028239792-Introduction-to-TravelJoy-teams-and-assistants |
| Member scope | Each member has their own client list, trip queue and settings, plus custom templates. This is a siloed-by-advisor model. | same |
| Assistant | Paid only by the owner, on the owner's billing cycle. Detailed limits are not in the public excerpts. | same |
| Owner-only powers | Assign trip collaborators across members' dashboards. Refer (transfer) a trip to a member, which is **irreversible**. Toggle a member's access to Direct Payments settings. Create and edit team templates unless delegated. Grant team reporting. | https://help.traveljoy.com/hc/en-us/articles/4408517071508-Collaborate-on-a-trip ; https://help.traveljoy.com/hc/en-us/articles/4409220256148-Refer-a-trip-to-your-team-member ; https://help.traveljoy.com/hc/en-us/articles/24610981558548-Toggle-team-member-access-to-direct-payments-settings ; https://help.traveljoy.com/hc/en-us/articles/360016307271-Create-and-use-team-templates |
| Billing | Members are owner-paid (prorated, bundled) or self-paid. Premium includes 2 Pro team members + 1 Pro assistant. | https://help.traveljoy.com/hc/en-us/articles/360028239792-Introduction-to-TravelJoy-teams-and-assistants ; https://traveljoy.com/premium.html |
| Security | PCI compliant (third-party audit), 2FA login, encrypted stored data (directory listing). | https://hostagencyreviews.com/travel-agency-software/traveljoy |

---

## 14. Integrations and API

| Aspect | Detail | Source |
|---|---|---|
| Zapier triggers (13) | Complete Task, Delete Client, Delete Task, Due Task, New Client, New Form Submission, New Group Booking, New Task, New Trip, Update Client, Update Commission, Update Trip, Update Trip Stage. | https://zapier.com/apps/traveljoy/integrations |
| Zapier actions | The listing shows Create New Client and Create New Trip. TravelJoy's own FAQ says actions are "Not yet, but this is coming soon!" The two sources conflict. | same ; https://help.traveljoy.com/hc/en-us/articles/43480339335188-How-does-Zapier-work-with-TravelJoy |
| Zapier access | Premium, or the Zapier add-on at $29/mo. Example uses on the premium page: Flodesk, QuickBooks, Google Drive. | https://traveljoy.com/premium.html |
| Calendar / email | Google Calendar, Outlook, Gmail, Microsoft 365. | https://traveljoy.com/blog/post/traveljoy-a-comprehensive-crm-for-travel-agents |
| Public REST API | **None published.** | — |
| Native accounting | None. QuickBooks only through Zapier. | https://traveljoy.com/premium.html |
| GDS | None. | https://tripkit.com/traveljoy-reviews |

---

## 15. AI features

| Feature | What it does | Plan / limits | Source |
|---|---|---|---|
| Itinerary Copilot | Prompt-driven editing inside the proposal sidebar: title, intro, cover photo, inserting days, adding Library items, turning call notes into **option sets**, packing lists, stateroom selection. | Pro: **50 requests/month** ("five to ten proposals"), with a usage tracker. Add-on 10x for $49/mo, or Premium. | https://traveljoy.com/blog/post/create-client-ready-itineraries-in-minutes-with-itinerary-copilot ; https://traveljoy.com/premium.html |
| Magic Importer | Supplier document, URL or screenshot in; a proposal, itinerary, invoice or form out. | Pro+ | https://traveljoy.com/ai.html ; https://help.traveljoy.com/hc/en-us/articles/45082755210772-See-what-s-new-with-TravelJoy |
| Magic Email | Forward a supplier email to `magic@traveljoy.ai` and get back a draft proposal or itinerary, "typically under 40 seconds". | Pro and Premium | https://traveljoy.com/blog/post/product-updates-crm-groups-proposals-and-more ; https://www.thetraveler.org/traveljoys-magic-email-brings-ai-to-booking-busywork/ |
| Passport parsing | Extracts passport data from an upload. | Pro+ (**inferred**) | https://traveljoy.com/ai.html |
| Client opportunities | AI list of past clients "likely ready to travel again". Weekly refresh on Premium. | Pro+, weekly on Premium | https://traveljoy.com/ai.html ; https://traveljoy.com/premium.html |
| Data policy | "We don't use your information or your clients' data to train public AI models". | — | https://traveljoy.com/ai.html |

Reviewer praise: Copilot "dramatically cuts down the time it takes to create beautiful, client-facing itineraries". Source: https://www.trustpilot.com/review/traveljoy.com

---

## 16. Pricing tiers and limits

| Plan | Price | Key limits / inclusions | Source |
|---|---|---|---|
| Starter | $19/mo | **12 trips/year**. Unlimited clients, forms and invoices. **No AI/automations, no groups, no team.** Card 5% + 30c, ACH 3%. Ticket support only (no live chat). | https://traveljoy.com/pricing ; https://help.traveljoy.com/hc/en-us/articles/360016023172-How-to-reach-TravelJoy-support |
| Pro | $39/mo monthly, $32/mo annual | Unlimited trips. AI and automations. Groups. Add-on team seats. Card 3.5% + 30c, ACH 1.5%. Copilot 50 req/mo. 12 email campaigns × 300 recipients/yr. Live chat. | https://traveljoy.com/pricing ; https://traveljoy.com/blog/post/traveljoy-a-comprehensive-crm-for-travel-agents |
| Premium | $79/mo annual ($948 first year, early access), $99/mo monthly | Pro plus 10x Copilot, Zapier, SMS, unlimited email campaigns, cruise booking, weekly Opportunities refresh, enhanced support, 2 team members + 1 assistant. **No free trial.** | https://traveljoy.com/premium.html |
| Add-ons (on Pro) | Zapier $29, SMS $49 (1,000 msgs), Copilot 10x $49, Email campaigns $29 | per month | https://traveljoy.com/premium.html |
| Trial / refunds | 7-day free trial with no card (Pro). 30-day money-back guarantee, and refunds **only** within 30 days of first paid activation. | https://traveljoy.com/blog/post/how-to-search-quote-and-book-on-traveljoy ; https://help.traveljoy.com/hc/en-us/articles/360038485732-Cancel-or-pause-your-TravelJoy-account |
| Team seat price | Not published. A directory lists $30–39 per user per month. | https://hostagencyreviews.com/travel-agency-software/traveljoy |

Reviewer complaints about pricing:
- "refunds are ONLY available within the first 30 days" (Trustpilot, 1★). Source: https://www.trustpilot.com/review/traveljoy.com
- Starter is "heavily gated". Source: https://tripkit.com/traveljoy-reviews

---

## 17. Onboarding, support and ease of use

| Aspect | Detail | Source |
|---|---|---|
| Training | Weekly live workshops (Thursdays 2 PM ET via Livestorm, recordings sent) on groups, templates, payments and Copilot. Earlier "TravelJoy 101" and Office Hours. | https://traveljoy.com/blog/post/traveljoy-training-workshops ; https://traveljoy.com/blog/post/traveljoy-a-comprehensive-crm-for-travel-agents |
| Getting started | A 3-step help path: "Set yourself up for success", "Optimize your workflow", "Become a TravelJoy expert". | https://help.traveljoy.com/hc/en-us/articles/9335087444116-Step-1-Set-yourself-up-for-success ; https://help.traveljoy.com/hc/en-us/articles/9335768898836-Step-2-Optimize-your-workflow ; https://help.traveljoy.com/hc/en-us/articles/9335719297684-Step-3-Become-a-TravelJoy-expert |
| Support | Email (hello@traveljoy.com), live chat for Pro and Premium, tickets for Starter, scheduled 1:1 calls. Mon–Fri business hours. | https://help.traveljoy.com/hc/en-us/articles/360016023172-How-to-reach-TravelJoy-support ; https://www.extruct.ai/hub/traveljoy-com/ |
| Review scores | Trustpilot 4.1/5 (45 reviews; 85% 5★, 11% 1★). G2 has 1 review (4/5). Host Agency Reviews has 27 reviews. | https://www.trustpilot.com/review/traveljoy.com ; https://www.g2.com/products/traveljoy/reviews ; https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews |

**Reviewer feedback**
- Praise:
  - Ease of use is the dominant theme: "intuitive and easy to use", "extremely easy to use".
  - The team "listens to agents".
  - "CONSTANTLY improving".
  - "training and support that is provided is remarkable".
- Complaints:
  - "You are forced to submit tickets or schedule calls".
  - "a few hiccups along the way".
- Sources: https://hostagencyreviews.com/travel-agency-software/traveljoy/reviews ; https://www.trustpilot.com/review/traveljoy.com
- Reddit: no substantive public threads were found in this pass.

---

## 18. Notable UX patterns

1. **Trip as the universal container.** Messages, files, tasks, notes, invoices, forms and authorizations all hang off one trip. Inquiry, booking and group registration all *create a trip*. Sources: help "Create and manage an individual trip"; embed-form article.
2. **"Waiting on" ball-in-court status** (you / traveler / supplier / none), shown alongside the pipeline stage. It makes the dashboard an action queue. Source: https://help.traveljoy.com/hc/en-us/articles/360016247971-Using-the-Dashboard
3. **Approve-and-pay in one click.** A smart proposal with option sets goes to approval plus authorization, which auto-generates the invoice and then becomes a live itinerary. Source: Feb 2025 updates post.
4. **Form field names as data binding.** A field named "Client …" writes to the profile card. This gives no-code schema extension. Source: form template article.
5. **Tag-triggered automation.** A trip tag auto-imports a task list, which fires automations immediately. Source: Jan 2026 updates post.
6. **AI as importer, not author.** Magic Importer and Magic Email turn supplier PDFs and emails into structured proposals and invoices. Copilot edits in place in a sidebar with a visible usage meter. Sources: §15.
7. **One shareable link for groups.** Itinerary, intake form and checkout combine into one link. Each booking spawns its own trip and invoice. Rooming is managed by drag. Source: Groups workshop post.
8. **Funds wallet per trip or group**, with virtual-card supplier payout and separate routing for planning fees. Source: payments workshop post.

## 19. Gaps / weaknesses (publicly evidenced or inferred)

- **Inbound email:** no inbound email/lead parsing or two-way inbox sync. Source: competitor claim, plus absence from docs.
- **Profiles:** one passport per profile, no household entity (**inferred**), and no client segmentation for exports or marketing (reviewer request).
- **API:** no public REST API. Zapier offers 13 triggers and actions that are disputed or limited.
- **Inventory and accounting:** no GDS or air, and no native accounting sync.
- **Mobile:** the client app is US-only, has no push notifications, and there is no advisor native app (**inferred**).
- **Team model:** silos per advisor. Trip referral is irreversible, and only the owner can collaborate across members.
- **Reporting:** the commission report does not separate markup, and there is no custom report builder (**inferred**).
- **Customization:** reviewers ask for more invoice and email customization and file-cabinet folders.
