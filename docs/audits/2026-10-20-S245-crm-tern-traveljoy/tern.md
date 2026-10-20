# Tern (tern.travel): feature teardown

Researched 2026-10-20 from public sources only: marketing site, pricing page, public help center (help.tern.travel), the public "What's New" changelog, the App Store listing, and third-party reviews. There was no sign-up, no login and no bulk scraping. Every claim has a URL. Anything not stated publicly is marked **(inferred)**.

**Product in one line:** an all-in-one operating system for independent travel advisors and host agencies in the US/North America. It combines CRM, itinerary/proposal builder, client checkout (card authorization), commission back office, reporting and an AI layer. Its own tagline is "flow over features" ([home](https://www.tern.travel/)).

**Coverage gaps.** None of these were found publicly:
- a G2 or Capterra listing for this product (the search hits were unrelated products named "Tern…");
- a public developer API or Zapier connector;
- an accounting integration such as QuickBooks or Xero;
- a GDS integration.

Host Agency Reviews lists "GDS integration: None" and an empty "API Access" field ([HAR listing](https://hostagencyreviews.com/travel-agency-software/tern)).

---

## 1. Client / contact records and profiles

**What it does.** Contacts are the CRM core. Each contact record has these tabs and sections ([About tab](https://help.tern.travel/en/articles/8120692-the-about-tab-and-managing-contacts-uploading-and-editing-contact-information)):
- **About:** profile picture, Contact information, Preferences ("Activities & Interests", "Food & Drink Preferences"), Other Travel Preferences (dropdowns), Key Travel Information, Loyalty Programs and Addresses.
- **Notes, Documents, Activity, Emails, Tasks, Automations and Tags.** Sources: [notes](https://help.tern.travel/en/articles/8121721-notes-on-contacts), [documents](https://help.tern.travel/en/articles/8121353-documents-in-contacts), [activity](https://help.tern.travel/en/articles/8581083-activity-tracking-in-tern), [email intro](https://help.tern.travel/en/articles/9015404-an-introduction-to-email-in-tern), [tags](https://help.tern.travel/en/articles/9524583-how-to-add-contact-tags-and-use-automation-to-auto-apply-workflows-for-specific-tags), [contact workflows](https://help.tern.travel/en/articles/11404393-contact-workflows-and-automations).

**Data fields.** The 39 fields accepted by the core import are the most complete public field list ([core import fields](https://help.tern.travel/en/articles/8719371-what-fields-are-supported-in-the-core-import)):
- **Identity:** Import ID, Prefix, Legal First Name, Middle Name, Last Name, Suffix, Preferred First Name, Birthday, Wedding Anniversary, Job Title, Gender.
- **Contact Type:** for example Supplier or Traveler.
- **Contact details:** Primary/Secondary Email plus a "Description" for each, Primary Phone (one only), and Address Line 1/2, Country, City, State, Zip.
- **Secure travel IDs:** Known Traveler Number / PASS ID plus its expiration, and Redress Number plus its expiration.
- **Passport:** Number, Country of Issue, Date of Issue, Date of Expiration, Given Names, Surname, Gender, Place of Birth, Nationality.
- **Multi-value lists (semicolon-separated):** "Food, Drink & Allergy Preferences" and "Activities & Interests Preferences", both checked against existing options, and a Tag List, where new tags are created automatically.

**Other contact data:**
- **Several passports per contact.** The CSV export picks the passport with the latest `updated_at` ([export](https://help.tern.travel/en/articles/14795473-exporting-contacts-with-passport-data-to-csv)).
- **Export columns** add Loyalty Programs, Tags and Owner. Owner appears when you export from "Shared with me".
- **Passport photo parsing.** A client uploads a photo of a US passport and Tern parses the data ([Sept 2024 CRM post](https://tern.travel/updates/a-new-era-of-crm-for-travel-advisors)).
- **Visa data has no dedicated field.** The help center recommends storing visas in notes or documents ([visa FAQ](https://help.tern.travel/en/articles/9552569-how-can-i-store-my-client-s-visa-information)).

**Families and relationships.** There is no household object. Families are pairwise links between contacts. There are 11 relationship types: child, friend, grandparent, grandchild, in-law, sibling, spouse/partner, parent/guardian, referred by, referred and other. Reciprocal links are created automatically (child↔parent/guardian, grandparent↔grandchild, referred by↔referred) ([relationship import](https://help.tern.travel/en/articles/9534524-how-to-import-relationships-in-tern)). When a client adds extra travelers through a form, they get the relationship "Other" ([forms](https://help.tern.travel/en/articles/8594104-managing-forms-in-tern)). The "referred by" type doubles as basic referral tracking **(inferred)**.

**Activity timeline:**
- **Contact events:** Form Completed, Contact Created (from form), Created Account, Note Created, Agreed to Terms & Conditions.
- **Trip events:** Created, Published/Unpublished, Status Updated, Created from Form, Traveler Associated, Itinerary Created/Deleted/Status Updated, Itinerary Approved / Revisions Requested ([activity tracking](https://help.tern.travel/en/articles/8581083-activity-tracking-in-tern)).
- **Itinerary view tracking (2026):** logged-in viewers are shown by name; anonymous views appear as "someone viewed the itinerary"; repeat views are deduplicated per hour ([changelog 8/20/2026](https://www.tern.travel/updates/see-who-opened-your-itinerary-and-when.html)).

**Hygiene:**
- duplicates page and merge ([merge](https://help.tern.travel/en/articles/14732085-how-to-find-and-merge-duplicate-contacts));
- archive and unarchive, which affects automations, search and consortium CRM sync ([archived](https://help.tern.travel/en/articles/16768854-archived-contacts));
- a notes drawer reachable from anywhere, and note import from other systems ([Q1 2026](https://tern.travel/whats-new/q1-2026)).

**Ownership.** Contacts have an owner (the agent) and can be shared with the agency. An admin "Agency-managed" toggle stops an agent from removing agency access, and only the agency can then delete the contact ([agency-managed](https://help.tern.travel/en/articles/12861208-agency-managed-contacts-trips)). Ownership can be reassigned ([contact ownership reassignment](https://help.tern.travel/en/articles/10770631-contact-ownership-reassignment)).

**Import.** The process runs in staged imports:
1. core import;
2. relationships;
3. historical trips;
4. notes.

Matching is by Import ID or Tern ID. Tern recommends batches of 1,000–2,000 for files above about 2,000 contacts ([import collection](https://help.tern.travel/en/collections/7362317-importing-contact-data-into-tern), [migration guide](https://help.tern.travel/en/articles/16787209-moving-to-tern-from-another-platform)).

**Reviewers:**
- **Praise:** a Reddit advisor who moved from Travefy found Travefy's CRM "an afterthought" compared with Tern. Others praise client self-service data entry ([r/travelagents mirror](https://lr.us.psf.lt/r/travelagents/comments/1jtppso/travefy_or_tern)).
- **Complaint:** no undo ([HAR reviews](https://hostagencyreviews.com/travel-agency-software/tern/reviews)).

---

## 2. Leads and inquiry intake

**Forms.** There are four form types ([managing forms](https://help.tern.travel/en/articles/8594104-managing-forms-in-tern)):
- **Trip Request:** creates a contact and a trip, which lands in the first status column (default "Inbound"). The trip name field is required. Optional extras are traveler details, budget, multiple pages and a scheduler block.
- **Contact Detail:** creates or updates contact records, including loyalty programs, secure travel IDs and preferences.
- **Custom:** question types are Multiple Options, Single Select, Long Text, Info Blocks and Scheduler.
- **Group Trip Signup.**

**How forms behave:**
- **Multiple travelers.** A "Multiple Contact Details" block lets one submission add several travelers, each with birthday, passport and contact blocks.
- **Contact matching.** A new email creates a new contact. A known email is checked against the name: a full match updates the existing contact; a new name creates a new contact.
- **Sharing and embedding.** Forms are shared by link, email or text, or embedded on the advisor's website ([website form](https://help.tern.travel/en/articles/9750780-how-to-add-a-tern-form-to-your-website), [CTA how-to](https://help.tern.travel/en/articles/9457770-how-to-add-a-trip-request-form-to-your-website-s-call-to-action-area-and-automate-your-inquiry-process)).
- **Drafts and Info text.** Drafts are kept per browser. A submitted response stores the Info-block wording the client saw.
- **Agency terms** are added to trip request and contact forms automatically, and acceptance is timestamped ([update post, via search](https://tern.travel/updates/agency-t-and-cs-on-forms-better-ai-imports-and-easier-tour-booking)).
- **Scheduling.** Meeting types can be embedded in forms. Tern syncs with Google or Microsoft calendars, prevents overlaps, and puts the meeting on both calendars ([Sept 2024 post](https://tern.travel/updates/a-new-era-of-crm-for-travel-advisors)).
- **Marketing claim:** "Form submissions become trips with client details pre-filled. No data entry." Forms collect "budget, dates, travelers, and preferences before the first call" ([advisors page](https://www.tern.travel/advisors)).

**Email parsing as intake:**
- **Inbox Intelligence (beta)** detects supplier confirmations (cruise invoices, flights, hotels), even from non-contacts. It matches them only to contacts with an active or upcoming trip, then shows a suggestion card ("Add to trip"), or creates a task when an existing booking changed. Nothing is added automatically ([Inbox Intelligence](https://help.tern.travel/en/articles/14183098-inbox-intelligence)).
- **Lead creation from email** is described only for AI Email Triage, which "pauses to ask for input … such as before creating a trip from a lead" ([AI page](https://www.tern.travel/ai)).

**No dedicated lead object.** A lead is a trip in an early status, such as "Inbound" or "Lead" ([trip statuses](https://help.tern.travel/en/articles/7929163-best-practices-for-using-trip-statuses-in-tern); the "Lead" status trigger comes from a search snippet of [trip-from-form article](https://help.tern.travel/en/articles/10388164-creating-a-new-trip-from-a-trip-request-form-in-tern)). There is no lead scoring and no web-to-lead source attribution beyond trip tags. Tern suggests trip tags for lead-source tracking in reports ([changelog 7/23/2026](https://www.tern.travel/updates/automated-trip-statuses-new-reports-and-your-agency-back-office-home.html)).

**Limit.** Workflows cannot start directly from a form. You use the trip-created, status or tag triggers instead (search snippet of [form workflow FAQ](https://help.tern.travel/en/articles/10388253-how-can-i-create-a-workflow-and-automation-from-a-tern-form)).

---

## 3. Pipeline and workflow automation

**Pipeline.** Trip statuses are the board columns on the Trips page, with Board and List views.
- **Customizing statuses.** Statuses are user-defined (add, delete, reorder, rename) under Trip Settings. "Cancelled" and "Archived" are system statuses: they can be moved but not renamed or deleted ([trip statuses](https://help.tern.travel/en/articles/7929163-best-practices-for-using-trip-statuses-in-tern)).
- **Default list.** The full default list is not published as text; it appears only in screenshots.
- **Automatic status changes (2026).** An "update trip" automation action can, for example, set "traveling" on the start morning, "traveled" the day after the end, or archive 60 days later. The activity log records which automation changed the status ([changelog 7/23/2026](https://www.tern.travel/updates/automated-trip-statuses-new-reports-and-your-agency-back-office-home.html)).

**Workflow model** ([mastering workflows](https://help.tern.travel/en/articles/15025814-mastering-workflows-and-automations-in-tern)):

| Concept | Detail |
|---|---|
| Workflow | A container of automations and tasks, built in Library > Workflows. Two types: **Trip** and **Contact** |
| Triggers (4) | Trip status change; Payment due date; Before/after event (trip start/end); Contact birthday/anniversary (contact workflows only). Passport expiration is also used in practice ([client care](https://help.tern.travel/en/articles/11404393-contact-workflows-and-automations)) |
| Timing | N days before or after; "0 days immediately". An "Immediate" option exists for Trip Created and Status Changed. Client Approves Trip, Client Authorizes Payment and Client Requests Trip Edits fire immediately (search snippet of [send immediately](https://help.tern.travel/en/articles/10514376-trigger-an-automation-to-send-immediately)) |
| Actions | Send Email (template, recipient such as "Primary Contact on Trip", attachments); Create Task (assignee, relative due date); Update trip (status) ([changelog](https://www.tern.travel/updates/automated-trip-statuses-new-reports-and-your-agency-back-office-home.html)); **Run AI Agent** with free-text instructions, whose output is a chat under Recents ([AI agent action](https://help.tern.travel/en/articles/15437686-run-ai-agent-automation-action)) |
| Auto-apply | When a trip is created; when the status changes to X; when trip tag Y is added; when a contact is created; when contact tag Y is added ([tags](https://help.tern.travel/en/articles/9524583-how-to-add-contact-tags-and-use-automation-to-auto-apply-workflows-for-specific-tags)) |
| Apply modes | Manual per trip; Bulk Apply (all, or by tag, with a preview count of affected records ([changelog](https://www.tern.travel/updates/automated-trip-statuses-new-reports-and-your-agency-back-office-home.html))); "Apply Updates" pushes library edits and overwrites per-trip changes, but does not resend emails already sent |
| Conditions | None beyond trigger, timing and auto-apply. An automation will not schedule if required data (email, dates) is missing |
| Prebuilt | A "Client Care" community workflow: birthday, anniversary, and passport expiry at 200 days ([client care](https://help.tern.travel/en/articles/11404393-contact-workflows-and-automations)) |

**Gotchas from the docs:**
- **Payment-due triggers** cannot tell a deposit from a final payment, so the email copy must be generic.
- **Editing an automation** requires toggling it off first.
- **Tag auto-apply** is tied to the account that configured it ([mastering workflows](https://help.tern.travel/en/articles/15025814-mastering-workflows-and-automations-in-tern)).
- **Status-change troubleshooting:** if emails don't fire, revert the status and set it again (search snippet, [automation in Tern](https://help.tern.travel/en/articles/9064843-automation-in-tern)).
- **AI Automations** (recurring pre-trip and welcome-home messages, agent drafting on status change, lead outreach) are a **closed beta** ([AI page](https://www.tern.travel/ai)).

**Tasks:**
- created from a trip, a contact or the global nav;
- assignee, due date, and automatic "Overdue / Due Today / Due Soon / Due Later" buckets;
- an email reminder the day before the due date, which can be turned off;
- task templates with relative due dates (from trip start/end or from task creation);
- a relative date cannot be calculated when competing itineraries have conflicting dates ([tasks intro](https://help.tern.travel/en/articles/7929158-an-introduction-to-tasks-in-tern)).

Agencies can assign task templates to admins or collaborators at the template, workflow and automation level ([assign](https://help.tern.travel/en/articles/15021017-assigning-task-templates-to-other-agency-members)).

---

## 4. Itinerary and proposal builder

**Builder:**
- a drag-and-drop day "planning board", with day swapping, reusable activity, hotel and itinerary templates in folders, and an own-photo library tagged by destination ([advisors](https://www.tern.travel/advisors), [home](https://www.tern.travel/));
- activity components include lodging (separate check-in/out activities and room options), flights (separate legs), transportation, tours and dining ([trip planning collection](https://help.tern.travel/en/collections/4012761-trip-planning)).

**Proposal mechanics:**
- **Multiple itineraries per trip** to present several trip ideas ([multiple trip ideas](https://help.tern.travel/en/articles/8418254-presenting-clients-with-multiple-trip-ideas)).
- **Option blocks.** A named block holds 2–3 alternatives of one activity type. The client can "Choose Later", and option blocks never block payment ([option blocks](https://help.tern.travel/en/articles/7929166-using-option-blocks-to-present-your-client-with-choices)).
- **Room options** with occupancy-based pricing, flexible lodging dates, and optional add-ons the client can select; pricing updates automatically ([room options](https://help.tern.travel/en/articles/10246068-set-up-room-options-for-lodging-in-tern), [occupancy](https://help.tern.travel/en/articles/11503908-use-occupancy-rates-to-customize-room-option-pricing), [add-ons](https://help.tern.travel/en/articles/10450232-a-guide-to-optional-add-ons)).
- **Pricing per item:** flat, per room or per person ([lodging pricing](https://help.tern.travel/en/articles/8345138-lodging-activity-pricing-options-flat-rate-per-room-or-per-person-pricing)).
- **Packages** bundle items under one price, with optional itemized cost tracking. You can hide individual costs from clients and still track supplier and commission ([packages](https://help.tern.travel/en/articles/7913306-using-packages-to-group-and-price-items), [hide costs](https://help.tern.travel/en/articles/10307010-how-can-i-hide-individual-costs-from-clients-but-still-track-individual-suppliers-and-commissions)).
- **Versioning.** The working copy stays hidden until "Publish". Published versions are kept, but the working copy has no rollback ([versioning](https://help.tern.travel/en/articles/8114228-trip-versioning-on-itineraries)).
- **Client approval or "request revisions"** notifies the advisor by email ([approval notice](https://help.tern.travel/en/articles/9512045-how-will-i-know-if-a-client-approves-or-makes-changes-to-a-proposal)).
- **Other proposal tools:** a pre-travel section, hide-from-traveler items, a day location that sets time zones, and Unsplash images ([collection](https://help.tern.travel/en/collections/4012761-trip-planning)).
- **PDF export** with customization (2026) ([changelog 9/3/2026](https://www.tern.travel/updates/your-itinerary-pdfs-exactly-how-you-want-them.html)).

**Content sources:**
- **Cruises:** "Cruise database with 50k+ sailings" ([home](https://www.tern.travel/)).
- **Tours, activities and transfers:** quote and book via Project Expedition, including a client-side tour search ([PE tours](https://help.tern.travel/en/articles/12683769-project-expedition-tours), [PE client search](https://help.tern.travel/en/articles/13860779-project-expedition-client-tour-search)).
- **ALG Vacations** reservation import by ID ([ALG via recommend.com](https://recommend.com/?p=167502)).
- **Chrome extension** imports itineraries, activities, email and form templates and images from any site. Imports use AI and count toward usage. Known beta flaw: everything can land on one day ([extension](https://help.tern.travel/en/articles/13928943-using-the-chrome-extension)).
- **AI Assist** turns a supplier PDF or email into a structured itinerary ([AI Assist](https://help.tern.travel/en/articles/9274873-introduction-to-tern-s-ai-assist-feature), [advisors](https://www.tern.travel/advisors)).

**Group travel.** A parent group trip carries the template itinerary, "rates" and a landing page. Each party gets a sub-trip with its own payments and authorization. Self-service signup builds sub-trips. Room-option inventory is tracked, and group syncing pushes parent changes down (2026) ([group guide](https://help.tern.travel/en/articles/10059452-a-guide-to-group-trip-functionality), [group syncing](https://help.tern.travel/en/articles/15445464-group-trip-syncing)).

**Reviewers:**
- **Praise:** "everything is drag and drop" ([HAR](https://hostagencyreviews.com/travel-agency-software/tern/reviews)).
- **Complaint:** a DDIY roundup lists "limited itinerary customization" as a con. Its page returned 403 to direct fetch, so this rests on the search snippet only ([ddiy.co](https://ddiy.co/best-travel-agency-software/)).
- **Complaint:** the docs warn that shortening trip dates drops lodging pricing with no undo ([versioning](https://help.tern.travel/en/articles/8114228-trip-versioning-on-itineraries)).

---

## 5. Quotes, invoicing, payments and commissions

**Card authorization (core differentiator)** ([payments & authorizations](https://help.tern.travel/en/articles/12176225-payments-authorizations-in-tern)):
- **Payment schedules.** Each priced activity becomes a booking with a schedule: Deposit + Final Balance, Installments (with editable labels), or Package.
- **Client flow.** The client sees "Authorize Payments" and ticks the items to authorize (selective authorization since 10/2026, [changelog](https://www.tern.travel/updates/authorize-what-you-want-book-in-one-click.html)). They then see supplier terms and cancellation policies, pick or add a card, sign and submit.
- **No charge at authorization.** Authorization is **not** a hold and Tern does not charge. The advisor charges the card through the supplier. The exceptions are Project Expedition bookings and integrated insurance, which charge automatically.
- **Card visibility windows.** The advisor sees the full card number and CVV for 30 days in 5-minute secure sessions. Unlogged authorizations expire after 30 days.
- **Payment logging.** The advisor records a payment after charging. Outside payments can be logged too.
- **Prerequisites:** 2FA, business name and logo, and Terms & Conditions.
- **Chargeback alert** when dates, supplier or price change after authorization.
- **Manual entry blocked.** Advisors cannot type card details on a client's behalf ([manual entry FAQ](https://help.tern.travel/en/articles/8958553-can-i-manually-enter-credit-card-information-for-clients)).
- **Marketing claims:** "Chargeback protection built in", "Automatic decline documentation" (an insurance-decline PDF waiver), "Variable deposits by room type" ([home](https://www.tern.travel/), [advisors](https://www.tern.travel/advisors)).

**Invoicing:**
- **Client invoice PDF** from the Bookings tab. It covers every item above $0 and you cannot pick items. It includes payment schedule and status, the last four card digits and refund policies, uses a memo template, and generating it also publishes the trip ([invoicing](https://help.tern.travel/en/articles/11165214-invoicing)).
- **Agency outbound invoices (10/2026)** to suppliers, clients or agents for one-off charges: void, record payment, CSV export ([changelog 10/8/2026](https://www.tern.travel/updates/invoice-suppliers-clients-and-agents-right-from-tern.html), [outbound invoicing](https://help.tern.travel/en/articles/16045114-outbound-invoicing)).
- **Supplier commission invoices** with status and overdue flags ([invoicing suppliers](https://help.tern.travel/en/articles/16100850-invoicing-suppliers-for-commission)).

**Service fees.** Planning fees are collected through the advisor's own Stripe Connect account. Tern takes **0.6%** on top of Stripe's fees. One Stripe account per Tern account ([service fees](https://help.tern.travel/en/articles/8866875-professional-service-fees)).

**Commissions (agency back office):**
- **Booking states.** A booking counts once it is marked "Booked" ([why not in reports](https://help.tern.travel/en/articles/15028084-why-a-booking-isn-t-showing-in-reports-or-the-commission-dashboard)).
- **Reconciliation process** ([overview](https://help.tern.travel/en/articles/12904145-commission-reconciliation-overview)):
  1. Log the supplier statement (single supplier, multiple suppliers, or host agency, or by file upload with AI parsing).
  2. Match statement lines to bookings.
  3. Track unclaimed commission.
  4. Close the statement (host statements use "Approve for payout").
  5. Add adjustments.
  6. Create payout statements, which move from Due to Pay Agents.
- **Objects and rules:**
  - standard advisor rates, which can change over time;
  - commission types, such as personal travel or lead referral, with optional required documentation;
  - multi-agent and mentor splits;
  - agent claims on unclaimed commission;
  - tax separation (HST);
  - locked commission rates on trips and contacts ([commission collection](https://help.tern.travel/en/collections/16811016-commission-reconciliation), [lock rates](https://help.tern.travel/en/articles/13648503-lock-commission-rates-on-trips-contacts)).
- **Supplier payout rules.** Ready-to-pay and expected-commission dates are set per category (Activities, Air Travel, Cruises, Dining & Drinks, DMC, Land, Lodging, Other, Packaged Travel, Transportation, Trip Protection), with per-supplier overrides. They key off booked date, travel start or end, or commission received ([payout rules](https://help.tern.travel/en/articles/15518413-agency-supplier-payout-rules)).
- **Quick booking entry.** "Quick Submit Booking" and the 2026 dashboard "Create Booking" drawer log a booking without building a full trip ([quick submit](https://help.tern.travel/en/articles/16964995-quick-submit-booking), [changelog 10/1/2026](https://www.tern.travel/updates/authorize-what-you-want-book-in-one-click.html)).

**Insurance.** One-click quotes from Arch RoamRight, Chubb, Faye, Trawick and Travel Insured International, with commission. Insurance selection can be made mandatory, and a decline produces a PDF waiver ([trip planning collection](https://help.tern.travel/en/collections/4012761-trip-planning), [Q1 2026](https://tern.travel/whats-new/q1-2026)).

**Limits by plan.** Commission reconciliation, supplier payment management and agency reporting come only with agency plans (3+ seats) ([pricing](https://tern.travel/pricing)).

---

## 6. Supplier and partner records

**Fields.** Agency supplier records hold Category, Supplier ID, Website, Status (Active/Archived), "Agency Preferred" (a gold-star highlight only), Tags, Description (booking and contact details, logins, advisor notes) and T&Cs / cancellation policies as link, file or text ([managing agency suppliers](https://help.tern.travel/en/articles/10715150-managing-agency-suppliers)). Individual advisors create a lightweight supplier with name, website, location and description ([new supplier](https://help.tern.travel/en/articles/8228608-creating-a-new-supplier-in-tern)).

**Controls:**
- an "Agency supplier" booking requirement under Agency controls;
- supplier merge ([merging suppliers](https://help.tern.travel/en/articles/16911185-merging-suppliers));
- bulk supplier import with tags and preferred flag ([import suppliers](https://help.tern.travel/en/articles/15370353-importing-your-agency-suppliers-into-tern));
- mapping of agency suppliers to host suppliers ([mapping](https://help.tern.travel/en/articles/14813417-how-to-map-agency-suppliers-to-host-suppliers)).

**Not seen publicly:** supplier-side contacts as structured sub-records, or supplier commission-rate fields on the record. The help center routes rates through commission types and payout rules **(inferred)**.

**Suppliers as a channel.** Tern markets a supplier offer: "Put your inventory directly into their daily workflow" ([home](https://www.tern.travel/)).

---

## 7. Email and messaging

**Integration** ([email intro](https://help.tern.travel/en/articles/9015404-an-introduction-to-email-in-tern)):
- **Providers.** One Google or Microsoft account per user, and email and calendar must come from the same provider. HAR also lists Yahoo ([HAR](https://hostagencyreviews.com/travel-agency-software/tern)).
- **Sync.** All mail is synced. The inbox opens on an "Important" view (mail from Tern contacts or tagged to a trip), with "Inbox" for everything. Any email can be tagged to a trip.
- **Search and filters** by sender, date and attachments. Archive single or bulk; archived non-contact mail is deleted after 7 days.
- **Open and click tracking** on every email sent from Tern.
- **Sending options:** schedule send, Cc/Bcc, and "Send separately" for one thread per recipient ([recipients](https://help.tern.travel/en/articles/16394931-choosing-email-recipients-to-cc-bcc-and-separate-threads), [schedule](https://help.tern.travel/en/articles/10079502-scheduling-emails-to-send-later)).
- **Templates** in Library → Emails, with folders and duplication. Variables cover recipient names, trip and sub-trip names and links, and form name and link ([variables](https://help.tern.travel/en/articles/14731133-using-variables-in-emails)).

**Three sending identities** ([which emails](https://help.tern.travel/en/articles/13976544-which-emails-come-from-you-and-which-come-from-tern)):
1. **The advisor's own address:** conversations, published itineraries and workflow emails.
2. **"Business via Tern" with branding:** payment authorization and insurance decline confirmations.
3. **Tern system notifications.**

**Limits:**
- **No bulk or marketing email** ([bulk FAQ](https://help.tern.travel/en/articles/9528236-can-i-send-emails-to-multiple-recipients-at-once-like-a-marketing-email-campaign)).
- **Thread restrictions:** no forwarding rules, replies only to existing thread participants, and no subject edits.
- **Formatting:** pasted rich HTML loses its formatting.

**Messaging.** In-app chat between client and advisor; the client app offers "contact your travel advisor directly" ([App Store](https://apps.apple.com/us/app/-/id6476008962), [which emails](https://help.tern.travel/en/articles/13976544-which-emails-come-from-you-and-which-come-from-tern)). There is no SMS or WhatsApp channel publicly documented **(inferred: not found)**.

**Reviewers:**
- **Complaint:** a Canva email signature does not render cleanly (Reddit mirror, above).
- **Older complaint (2025):** email was still missing ("with the exception of email which should be coming") ([HAR](https://hostagencyreviews.com/travel-agency-software/tern/reviews)).
- **Wish list:** "marketing features" ([HAR](https://hostagencyreviews.com/travel-agency-software/tern/reviews)).

---

## 8. Client portal and mobile

**Portal.** Clients get a web itinerary and a **"Tern for Travelers"** iOS app ([App Store](https://apps.apple.com/us/app/-/id6476008962)). The App Store listing shows 5.0 from 32 ratings, version 4.7, and the developer declares that it collects no data. The app supports:
- day-by-day itinerary, confirmation numbers, addresses and documents;
- real-time flight push alerts;
- approving or requesting edits;
- choosing options and add-ons;
- authorizing payments (v3.3+).

The flight-alert feature has its own help collection ([flight tracker collection](https://help.tern.travel/en/collections/4026313-flight-tracker)).

**Access levels** ([traveler access](https://help.tern.travel/en/articles/8694749-traveler-access-permissions)):
- **Levels.** Primary Traveler and Full Access can approve, comment, view documents and authorize. Limited Access is view-only, with no documents or payments. Full Access is the default.
- **Account required.** An account (email, password, name) is needed for gated actions, and the login email must match the contact's email. A guest checkout is "may come later".

**Branding.** Custom brand colors, a client-facing contact email, and custom itinerary subtitles ([home](https://www.tern.travel/), [changelog 8/20](https://www.tern.travel/updates/see-who-opened-your-itinerary-and-when.html), [changelog 10/8](https://www.tern.travel/updates/invoice-suppliers-clients-and-agents-right-from-tern.html)).

**Advisor mobile.** No advisor app. A 2025 reviewer asked for "A mobile App from the Agent side" ([HAR](https://hostagencyreviews.com/travel-agency-software/tern/reviews)). In 2026 Tern made page headers and the itinerary builder usable on small screens ([changelog 9/24](https://www.tern.travel/updates/cleaner-pages-live-kpis-smarter-templates.html), [changelog 10/1](https://www.tern.travel/updates/authorize-what-you-want-book-in-one-click.html)).

---

## 9. Documents and e-signature

**Documents.** Stored on contacts, trips and activities: "Contracts, invoices, and receipts stored with each trip" ([advisors](https://www.tern.travel/advisors), [contact documents](https://help.tern.travel/en/articles/8121353-documents-in-contacts), [trip documents update](https://help.tern.travel/en/articles/12508305-updates-to-documents-on-trips-and-activities)). Generated invoices are added to trip documents ([invoicing](https://help.tern.travel/en/articles/11165214-invoicing)).

**E-signature.** An E-Signature form block placed after a Terms block; responses are timestamped. No legal standard is claimed, though the article calls it "secure and compliant" ([e-sign](https://help.tern.travel/en/articles/9670279-can-i-add-an-e-signature-to-my-forms)). The card-authorization flow also captures a signature ([payments](https://help.tern.travel/en/articles/12176225-payments-authorizations-in-tern)).

**Agency T&Cs** are enforced in payments, invoices and forms ([agency T&Cs](https://help.tern.travel/en/articles/13515359-agency-terms-conditions)). There is no DocuSign-style integration publicly **(inferred: not found)**.

---

## 10. Reporting and analytics

**Standard reports** ([reporting collection](https://help.tern.travel/en/collections/15412483-reporting)):
- **Advisor:** Your Clients, Expected Commission, Received Commission, Sales, KPIs, Trips.
- **Agency:** Agency Clients, Agency Expected / Received Commission, Commission Payouts (including 1099 export), Agency Sales, Agency KPIs, Agency Trips (trip-to-booking conversion).
- **Specials:** "Where Are My Clients?" (live traveler locations, lags up to 1 h) and a Planning report of bookings not yet marked booked ([changelog 7/23](https://www.tern.travel/updates/automated-trip-statuses-new-reports-and-your-agency-back-office-home.html)).

**Explore and filter.** An "Explore" mode on dashboard tiles lets you filter, add columns, swap dimensions and compare periods ([explore](https://help.tern.travel/en/articles/14183201-explore-data-from-your-reporting-dashboards)). Filters include client residence state, consortium or marketing codes, trip tags and final-payment due date. Reports update almost immediately; agency KPIs are "coming soon" to live ([changelog 9/24](https://www.tern.travel/updates/cleaner-pages-live-kpis-smarter-templates.html), [changelog 10/8](https://www.tern.travel/updates/invoice-suppliers-clients-and-agents-right-from-tern.html)).

**Custom reporting.** A Report Builder and AI Assist for custom tables and charts, **only with Tern Pro** ([custom reporting](https://help.tern.travel/en/articles/14422894-custom-reporting), [Tern Pro](https://help.tern.travel/en/articles/15292346-tern-pro)).

**Agency pitch.** Itinerary-level supplier detail (hotels, cruise lines, operators) to negotiate preferred rates and overrides, sliced by advisor, destination, supplier and date ([agencies](https://www.tern.travel/agencies)).

**Reviewers.** A 2025 complaint: "reporting could be a little more in depth and it needs a dashboard". This predates the 2026 dashboards ([HAR](https://hostagencyreviews.com/travel-agency-software/tern/reviews)).

---

## 11. Team, roles and permissions

**Agency roles** ([roles](https://help.tern.travel/en/articles/9621179-what-is-the-difference-between-agency-roles-in-tern-owner-admin-collaborator-agent)):

| Role | Can do |
|---|---|
| **Owner** | Everything an Admin can, plus transfer ownership |
| **Admin** | Team, billing, settings, commissions, reporting |
| **Collaborator** | Edit trips and contacts shared with the agency. No settings, commissions or reporting: "access to build content without seeing your financials" ([agencies](https://www.tern.travel/agencies)) |
| **Agent** | Own account and trips; no agency-level access |

**Per-member toggles** ([agency user permissions](https://help.tern.travel/en/articles/15192055-agency-user-permissions)):
- **Credit card details:** full card visibility, settable per member or per trip.
- **Admin-only toggles:** manage agency suppliers, team management (roles and splits), billing management (seats).

**Data ownership:**
- **Sharing and agency-managed records.** Contacts and trips are shared with the default agency automatically. "Agency-managed" locks agency access, and a trip becomes agency-managed once a booking uses agency credentials ([agency-managed](https://help.tern.travel/en/articles/12861208-agency-managed-contacts-trips)).
- **Emergency trip access** for managers ([agencies](https://www.tern.travel/agencies)).
- **Trip and booking reassignment** ([collaboration](https://help.tern.travel/en/collections/9578186-collaboration)).
- **Agency-level tags** that advisors cannot remove ([changelog 8/20](https://www.tern.travel/updates/see-who-opened-your-itinerary-and-when.html)).
- **Sub-agency hierarchies:** host → agency → advisor ([home](https://www.tern.travel/), [host overview](https://help.tern.travel/en/articles/14327284-host-agency-overview)).

**Communities.** A cross-account content-sharing construct, separate from agencies ([agency vs community](https://help.tern.travel/en/articles/9621263-when-should-i-use-an-agency-vs-a-community)).

**Audit.** "Complete audit trail" is claimed ([home](https://www.tern.travel/)). The trip activity log is read-only with no restore ([versioning](https://help.tern.travel/en/articles/8114228-trip-versioning-on-itineraries)).

**Security.** 2FA via SMS, an authenticator app or passkeys ([security collection](https://help.tern.travel/en/collections/5447672-security-and-data)). There is no public SOC 2 or PCI statement **(inferred: not found)**.

---

## 12. Integrations and API

| Area | What exists publicly | Source |
|---|---|---|
| Consortia | Virtuoso, Signature, Travel Leaders Network ("consortia sync" of marketing data). Signature trip sync pushes booking changes in 1–2 minutes and needs a linked advisor plus a matched traveler | [Q1 2026](https://tern.travel/whats-new/q1-2026), [Signature trip syncing](https://help.tern.travel/en/articles/15121393-signature-trip-syncing) |
| Tours, transfers | Project Expedition (quote, book, charge) | [PE tours](https://help.tern.travel/en/articles/12683769-project-expedition-tours), [PE transfers](https://help.tern.travel/en/articles/14080912-project-expedition-transfers) |
| Packages | ALG Vacations reservation import | [recommend.com](https://recommend.com/?p=167502) |
| Insurance | Arch RoamRight, Chubb, Faye, Trawick, Travel Insured International | [trip planning collection](https://help.tern.travel/en/collections/4012761-trip-planning) |
| Email and calendar | Google, Microsoft | [email intro](https://help.tern.travel/en/articles/9015404-an-introduction-to-email-in-tern) |
| Payments | Stripe Connect (service fees only) | [service fees](https://help.tern.travel/en/articles/8866875-professional-service-fees) |
| Video meetings | Zoom, Meet, Teams (Notetaker) | [notetaker](https://help.tern.travel/en/articles/14182360-ai-notetaker) |
| Content | Unsplash; Chrome extension; Google address autofill | [Unsplash](https://help.tern.travel/en/articles/8303043-using-unsplash-to-add-trip-cover-photos-and-images-to-activities), [extension](https://help.tern.travel/en/articles/13928943-using-the-chrome-extension), [autofill](https://help.tern.travel/en/articles/16769108-google-address-autofill) |
| GDS | None | [HAR](https://hostagencyreviews.com/travel-agency-software/tern) |
| Public API, Zapier, accounting (QuickBooks/Xero) | Not found. A help FAQ says Tern does not offer APIs for rates, availability or content for agency websites (search snippet; the page returned 404 on fetch) | [API FAQ](https://help.tern.travel/en/articles/10387030-does-tern-provide-apis-for-rates-availability-and-content-for-travel-agency-websites) |

Tern is hiring supplier-integration engineers, which suggests more direct supplier connections are coming **(inferred)** ([job post](https://jobs.upfront.com/companies/tern-travel-2/jobs/81632244-senior-supplier-integration-lead)).

---

## 13. AI features

| Feature | What it does | Source |
|---|---|---|
| AI Assist | Supplier PDF, email or URL into a structured itinerary; destination guides; packing lists | [AI Assist](https://help.tern.travel/en/articles/9274873-introduction-to-tern-s-ai-assist-feature), [guides](https://help.tern.travel/en/articles/11020414-ai-assist-destination-guides), [home](https://www.tern.travel/) |
| AI Chat ("Ask Tern anything") | Reads notes, contacts (prefs, relationships, last 10 trips), trips, forms, and email in email flows. **Writes** trips, contacts, tasks and itineraries via preview cards that need accepting. Cannot delete or book. Full passport, KTN and Redress numbers are never sent to the model. Model picker: Standard or Premium | [AI chat](https://help.tern.travel/en/articles/14182386-ai-chat-for-notes-and-crm) |
| Email Triage / Smart Inbox | Drafts replies in the advisor's voice. Nothing sends without approval. Asks before creating a trip from a lead | [AI page](https://www.tern.travel/ai) |
| Inbox Intelligence (beta) | Parses supplier confirmations and suggests bookings or tasks on a trip | [inbox intelligence](https://help.tern.travel/en/articles/14183098-inbox-intelligence) |
| AI Notetaker | Joins Zoom, Meet or Teams. Produces summary, action items and a speaker-labelled transcript, attached to contacts matched by email. Audio is deleted after processing. Rules: external, internal, organized or invited | [notetaker](https://help.tern.travel/en/articles/14182360-ai-notetaker) |
| Pre-call client summary | Past trips, notes and emails condensed into a brief | [AI page](https://www.tern.travel/ai) |
| Writing style | A brand-voice profile used for drafts | [writing style](https://help.tern.travel/en/articles/15382045-build-your-writing-style-for-tern) |
| Run AI Agent automation | Triggered agent ("Review this trip") that outputs a chat; model is Light or Premium | [agent action](https://help.tern.travel/en/articles/15437686-run-ai-agent-automation-action), [changelog 10/1](https://www.tern.travel/updates/authorize-what-you-want-book-in-one-click.html) |
| AI commission reconciliation (beta) | Parses statements and matches lines to bookings; flags "needs review" | [AI reconciliation](https://help.tern.travel/en/articles/14489431-ai-commission-reconciliation-in-beta) |
| AI onboarding guide | An AI interview that replaces the live agency setup call | [AI onboarding](https://help.tern.travel/en/articles/16769370-agency-setup-with-the-ai-onboarding-guide) |
| Voice input, prompt library | Dictation (does not count toward usage) and shared prompts | [voice](https://help.tern.travel/en/articles/15184732-voice-input-in-tern), [prompt library](https://help.tern.travel/en/articles/15607912-agentic-ai-prompt-library) |

**Usage metering** ([AI usage limits](https://help.tern.travel/en/articles/15303956-ai-usage-limits)):
- **What counts:** Chat, triage, agents, AI Assist, extension imports, Notetaker and AI reconciliation share **one monthly pool**. The base allowance is not published as a number.
- **Alerts and pausing.** Alerts go out at 75%, 90% and 100%. At 100% AI pauses with no overage charge; the rest of Tern keeps working.
- **Enforcement and resets.** Enforced since 2026-07-01. Usage resets on the billing date (agency-paid seats reset on the 1st).
- **Conflicting docs.** Older help pages counted Notetaker hours separately (base 5 h; Pro 10/20/50 h) (search snippets of [Tern Pro (July)](https://help.tern.travel/en/articles/15292346-tern-pro-coming-july-1st-2026), [notetaker beta](https://help.tern.travel/en/articles/13901556-tern-notetaker-beta)).

**Reviewers.** "AI is being implemented on a weekly basis and is saving so much time". The same reviewer says the pace of change is "hard to keep up" ([HAR](https://hostagencyreviews.com/travel-agency-software/tern/reviews)).

---

## 14. Pricing tiers and limits

**Base plan.** **$49/seat/mo** billed monthly; **$35/seat/mo** billed quarterly or annually ([pricing](https://tern.travel/pricing)). Seat bands are Just me, 1–2, 3–24, 25–99, 100–499 and 500+ (custom). Agency per-seat prices are not shown.

**What every plan includes.** Itineraries, CRM, AI with base usage, email integration, scheduling, card authorization, client forms, and reports.

**Agency extras (3+ seats).** Commission reconciliation, supplier payment management, agency reporting, collaboration, shared library and centralized billing.

**Billing terms.** Prorated upgrades and downgrades at any time. Free trial: 14 days in 2024 ([Sept 2024 post](https://tern.travel/updates/a-new-era-of-crm-for-travel-advisors), [HAR](https://hostagencyreviews.com/travel-agency-software/tern)); the length is not stated on the current page.

**Tern Pro add-on.** Monthly billing only ([Tern Pro](https://help.tern.travel/en/articles/15292346-tern-pro)):
- **Tiers:** $19 (Pro), $39 (2x), $99 (5x), $149 (10x).
- **Includes:** more AI usage, more Notetaker, and Custom Reporting.

**Transaction fee.** 0.6% on Stripe service-fee invoices ([service fees](https://help.tern.travel/en/articles/8866875-professional-service-fees)).

**Services marketplace.** Lucia CoPilots are vetted human contractors for migration, setup and automations, priced per project ([Lucia](https://www.tern.travel/lucia)).

**Reviewer note.** DDIY lists "non-transparent pricing" as a con (search snippet, [ddiy.co](https://ddiy.co/best-travel-agency-software/)). The current public per-seat price makes this partly outdated **(inferred)**.

---

## 15. Onboarding and ease of use

**Onboarding:**
- **Learning resources.** "Tern & Learn" in-app videos of 2–8 minutes ([Sept 2024 post](https://tern.travel/updates/a-new-era-of-crm-for-travel-advisors)), product webinars ([webinars collection](https://help.tern.travel/en/collections/17101239-product-webinars)) and weekend support ([home](https://www.tern.travel/)).
- **Migration.** A migration guide (TravelJoy-specific notes). Workflows are not importable and images need re-upload ([migration](https://help.tern.travel/en/articles/16787209-moving-to-tern-from-another-platform)).
- **Agency setup.** "Business in a Box" pre-shares forms, templates, workflows and libraries with new advisors. Small agencies self-implement in "a few weeks" ([agencies](https://www.tern.travel/agencies)).
- **Channel deals.** Host and consortium partnerships, for example Travel Planners International with an onboarding buy-down ([travelagentcentral](https://www.travelagentcentral.com/your-business/travel-planners-international-partners-tern)).

**Reviewer sentiment** ([HAR reviews](https://hostagencyreviews.com/travel-agency-software/tern/reviews), Reddit mirror above):
- **Praise:** "One integrated solution for CRM, authorizations, itinerary building, automation, workflow"; "ease of use and the layout is very user friendly"; founders who listen and ship requests.
- **Complaints:** too much change to keep up with, waiting for promised features, no undo, and in the past no email, dashboard or groups (most now shipped).

---

## 16. Notable UX patterns

1. **Trip-centric everything.** Leads, proposals, bookings, payments, emails, tasks and documents all hang off a trip. A lead is just a trip in an early status column ([statuses](https://help.tern.travel/en/articles/7929163-best-practices-for-using-trip-statuses-in-tern)).
2. **Forms create records.** A form submission creates the contact and the trip together and deduplicates by email and name ([forms](https://help.tern.travel/en/articles/8594104-managing-forms-in-tern)).
3. **Approve-before-write AI.** Every AI write is a preview card or a "Waiting for input" chat item ([AI chat](https://help.tern.travel/en/articles/14182386-ai-chat-for-notes-and-crm), [inbox intelligence](https://help.tern.travel/en/articles/14183098-inbox-intelligence)).
4. **Working copy vs. published itinerary**, with view tracking on the published one ([versioning](https://help.tern.travel/en/articles/8114228-trip-versioning-on-itineraries), [changelog 8/20](https://www.tern.travel/updates/see-who-opened-your-itinerary-and-when.html)).
5. **Client checkout as part of the itinerary:** options, then rooms, then add-ons, then insurance, then selective authorization, then signature ([option blocks](https://help.tern.travel/en/articles/7929166-using-option-blocks-to-present-your-client-with-choices), [payments](https://help.tern.travel/en/articles/12176225-payments-authorizations-in-tern)).
6. **Library + workflow "Apply Updates".** Library templates propagate to records already using them ([mastering workflows](https://help.tern.travel/en/articles/15025814-mastering-workflows-and-automations-in-tern)).
7. **Global search, a notes drawer and a task dashboard** reachable from anywhere ([home](https://www.tern.travel/), [Q1 2026](https://tern.travel/whats-new/q1-2026)).
8. **Weekly public changelog** with small "quality-of-life" lists, a visible signal of shipping speed ([What's New](https://www.tern.travel/blog)).

---

## Takeaways for the AA tenant CRM (PR-19)

These are our analysis, not Tern claims. They are **(inferred)** relevance notes for the CRM spec in `docs/research/partner-crm-spec.md`.

- **Tern serves a different segment.** It is a US retail-advisor tool built on commission and card authorization. AA's tenants are B2B tour operators and agencies in Asia, so the payment model (authorize, then charge via the supplier) and the US-only passport parsing do not carry over directly.
- **Patterns worth copying:**
  - form → contact + trip in one step;
  - pairwise relationships with reciprocal types;
  - preference pick-lists;
  - passport, KTN and loyalty fields;
  - trip-status workflows with relative timing;
  - approve-before-write AI;
  - itinerary view tracking;
  - per-member financial visibility (a Collaborator-like role).
- **Gaps that could differentiate AA:**
  - a household object;
  - a lead entity separate from the trip, with source attribution;
  - conditional workflow logic;
  - bulk or marketing email;
  - WhatsApp/Zalo messaging;
  - a public API, webhooks or Zapier;
  - accounting sync.
