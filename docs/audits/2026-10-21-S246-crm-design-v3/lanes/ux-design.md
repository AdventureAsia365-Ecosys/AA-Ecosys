# AA Partner CRM v3: UX design (information architecture, flows, wireframes, client pages)

Draft, S246, 21/10/2026. Role: UX designer. Agent: Claude Code. Read-only on repos; this file is a draft under
`.tmp-session/s246-crm-v3/`. No paid calls.

**Inputs used:**

- Spec (Ms. Thu): `docs/research/partner-crm-spec.md`. The path `v2.1/partner-crm-spec.md` named in the task does not
  exist; this is the only copy (same finding as `reply-to-notes.md`).
- Design v2 §3.4 (one app, two hosts), §5 (spec trace), §6 (main flow); v2.1-tech §4 (slice, waves D1–D7);
  v2.2 simplified (`.tmp-session/s245-r2/r4/crm-v2.2-simplified.md`; S1–S7, 3-layer AA access A1);
  `owner-approvals-r2.md`.
- Competitor teardown: `docs/audits/2026-10-20-S245-crm-tern-traveljoy/` (U1–U14 patterns, R1–R16).
- New ideas R17–R44 + C12, C31: `docs/audits/2026-10-21-S246-crm-more-ideas/README.md`.
- Questionnaire v1 (41 answers), notes reply, v2 (12, all treated as decided with the recommended option):
  `docs/audits/2026-10-21-S246-thu-questionnaire/`.
- Platform: `docs/ecosystem-architecture.md`, AA-CIS-App `CONTEXT.md` (tenant portal, AA-885), AA-Booking
  `CONTEXT.md` (pricing, FX, trip cases).

**Conventions:**

- `Mn` = spec module n (1–18), `F1`–`F5` = foundation modules, `§n` = spec section.
- `Rn` = approved recommendation (R1–R44). `Un` = usability pattern from the teardown (`comparison.md` §3).
- `Q v1 x.y` / `Q v2 x.y` = questionnaire answer. `A-nn` = agency screen, `C-nn` = client page, `S-nn` = AA staff screen.
- Wireframes are low fidelity: boxes show content and priority, not visual style. Desktop width; the mobile rule for
  each screen is written under it.

---

## 0. Summary

1. **One app, two hosts, no new top-level product for the agency.** The CRM lives inside the tenant portal (AA-Partner
   web, today `portal.lumiguides.it.com`, Dev `partner-dev.`), next to the existing Content studio pages. Clients use a
   separate host (`go.`, Dev `go-dev.`; a neutral product domain later, agency custom domain optional, Q v1 2.6).
   Cookies are host-only, so the two never share a session (v2 §3.4).
2. **The trip is the folder** (U1). A lead is a trip in the first column. Every message, task, proposal, booking line,
   invoice, document and audit line hangs off one trip workspace (A-03). The pipeline board (A-02) is an action queue,
   not a report: each card says who the ball is with ("waiting on", R1/U2) and every column has bulk actions (U3).
3. **The agency works in five places:** Home (today), Pipeline, Trip workspace, Inbox, Tasks. Everything else (money,
   reports, library, automations, settings) is one click away but is not needed for the daily loop.
4. **Client pages need no account.** The proposal page and Stage 1/2 forms open from a signed link. The client portal
   asks for a one-time code per person (R22): each traveller sees only their own forms and documents, the lead
   traveller also sees payments. Passport data can be uploaded but never shown back.
5. **AA inventory is a side panel in the builder**, not a separate system: search AA products for the day, see net,
   sell and margin, availability (instant / on request / sold out), add as an option block. The hold placed at
   acceptance drives the deposit link's validity (C31) and the trip's cancellation path (C12, R21).
6. **Privacy is visible in the UI:** F1 fields are masked until revealed (each reveal is logged, F5), assistants never
   see margin, AI drafts carry a "Draft – review before sending" chip, AA support sessions show a banner, and the
   agency can read its own access log (Q v1 3.8, 3.9).
7. **Mapping:** all 23 spec modules, all 44 R-items, C12 and C31 are placed on a screen (§6). Items placed only as a
   rule or deferred by an owner decision are listed in §6.4.

---

## 1. Information architecture

### 1.1 Hosts and who uses them

| Host | Users | Auth | Contains |
|---|---|---|---|
| Agency host (`portal.` → AA-Partner; Dev `partner-dev.`) | Agency owner, agent, assistant (§3); AA support staff only inside a granted support session (S-04) | Cognito EXTERNAL; 2-step required for owner and agent (Q v1 3.13) | Content studio (existing portal pages) + CRM (§1.2) |
| Client host (`go.`; Dev `go-dev.`) | Travellers and prospects | None for forms and proposal (signed link); email one-time code per person for the client portal (R22) | Intake form + widget, Stage 2 form, proposal page, accept and deposit, client portal, sign, itinerary (installable, R16), preferences |
| CIS admin (`aa-cis.`) | AA staff (WORKFORCE + MFA) | Existing | S-01 Agencies (CRM) console (no PII), S-03 AA insights (k ≥ 10, ≥ 3 agencies) |
| AA-Partner staff routes | AA ops (`crm-ops` group), AA support (`crm-support` group) | WORKFORCE, separate app client | S-02 Ops release list (M8), S-04 support session |

### 1.2 Agency app navigation (sidebar)

Groups follow the daily loop first, then money, then growth. Badge counts in brackets. Items an assistant cannot use
are hidden for that role, not disabled.

```
AA Partner  [agency name v]
---------------------------------------------
HOME                          A-01  KPI tiles, today, onboarding checklist
CRM
  Pipeline                    A-02  Board | List | Travelling now | Closed
  Clients                     A-06  Directory, tags, archived, duplicates
  Inbox            [5]        A-08  Email, WhatsApp, SMS, AI drafts, unmatched
  Tasks            [7]        A-09  Overdue / Today / Upcoming / Later / Waiting for dates
MONEY
  Payments                    A-10  Receivables, schedules, reminders, owed to suppliers
  Bookings                    A-11  All booking lines across trips (ledger)
  Commissions                 A-12  Expected vs received, overdue           (hidden: assistant)
GROW
  Reports                     A-14  Conversion, margin, sources, option picks (margin hidden: assistant)
  Marketing                   A-15  Ready to travel again, special dates, campaigns
  Suppliers                   A-13  AA (default) + own suppliers
  Library                     A-16  Itinerary items, task lists, messages, forms, pre-travel packs, terms
  Automations                 A-17  Workflows, tags, triggers                (owner only edits)
CONTENT STUDIO                      existing portal pages: Brand, Rewrite, My catalog tours, Social content,
                                    Angle gate, My content, Publish, Marketplace
---------------------------------------------
Settings                      A-18  (Trash, access log, support access, export, team, channels...)
Help & what's new                   R42, R43
```

Inside a trip (A-03), tabs: **Overview · Proposal · Bookings · Payments · Travellers & documents · Messages ·
Tasks & notes · Activity**. The builder (A-04) opens full screen from the Proposal tab.

### 1.3 Global shell (A-00, every agency screen)

| Element | Behaviour | Implements |
|---|---|---|
| Search box, always visible; Ctrl/Cmd+K focuses it | Detects the query type: `bk-` Booking code, supplier confirmation number, E.164 phone, email (exact match through blind index), trip name, tag. Accent-insensitive for Vietnamese. Recent searches stay in the browser only | R35, U11 |
| `+ New` | Trip (opens quick form: client, destination, month, pax), Client, Task, Note | U1 |
| Tasks drawer | Same grouping as A-09, filtered to "mine" | U11, R20 |
| Notes drawer | Free note attached to the current trip or client | U11 |
| Bell | Simple list: client viewed proposal, client chose options, payment received, hold expiring, AA confirmed or declined an on-request line, AA incident flag, mailbox disconnected | R4, R19, C31, R26, R37, R24 |
| AI meter (only when AI is on) | "AI this month: 62 %"; warns at 75 / 90 / 100 %; at 100 % AI stops, nothing is charged | R5, U9, M14 |
| Language EN / VI; date format per locale; dates written with month names in everything sent out | | R32, E7 |
| Support banner (amber, cannot be dismissed) | "AA support (name) is viewing this account read-only until 14:20. [End now]" | v2.2 §3 layer 2, Q v1 3.5 |
| Undo toast | Every stage move, bulk action, archive and delete shows "Undo" for 10 s | Avoids Tern "no undo" complaint (`comparison.md` §3) |

### 1.4 Client host pages

| Page | URL shape | Access | Implements |
|---|---|---|---|
| C-01 Inquiry form (+ embeddable widget, hosted link-in-bio page) | `/f/{agency}/{form}` | Public, rate-limited | M1, §5 Stage 1, U4, R7, R15, R31, R32 |
| C-02 Planning form (Stage 2) | `/s/{signed}` | Signed link | §5 Stage 2, R31, rule 4 (pre-fill bands only) |
| C-03 Proposal page (option picker) | `/p/{signed}` | Signed link, no login | M3, M4 link target, R4, R19, R22, R26 |
| C-04 Accept and deposit | `/p/{signed}/accept` | Signed link; typed name | M3, M7, M12 (terms click), R25, R26, R34, C31 |
| C-05 One-time code sign-in | `/t/{trip}` | Email code per person | M11, R22 |
| C-06 Client portal home | `/t/{trip}/home` | After C-05 | M11, R22, R16 |
| C-07 My forms (Stage 3) | `/t/{trip}/forms` | After C-05 | §5 Stage 3, R31, R33, R32 |
| C-08 Sign | `/t/{trip}/sign` | After C-05 + code at signing | M12 (self-built simple e-sign, Q v1 4.1), R13 (insurance decline), R34 |
| C-09 Itinerary | `/t/{trip}/itinerary` | After C-05; installable, offline | M11, R16, R38, R33, R22 (hide cancelled lines) |
| C-10 Payments | `/t/{trip}/pay` | Lead traveller only | M7, M11, R25, R27 |
| C-11 Preferences / unsubscribe | `/u/{signed}` | Signed link | R2, R14, R23, R36 consent gates |
| C-12 Link expired / hold expired | any | — | C31, R21 |

### 1.5 AA staff screens (outside the agency app)

| Screen | Where | Shows | Implements |
|---|---|---|---|
| S-01 Agencies (CRM) console | CIS admin | Per agency: seats, active users, storage, inbound mail, AI cost, failed jobs, last active. Actions: create agency, invite first owner (only before any owner and any client), lock/unlock, retry jobs, entitlements (allow, never switch on), raise export/delete **request** (owner confirms), owner recovery (promote an existing member after 14 days, Q v1 6.3). No trips, pipeline or revenue per agency | v2.2 §3 layer 1, R42 (release notes source) |
| S-02 Ops release | AA-Partner `crm-ops` | Confirmed departures only: names, pax, dietary/mobility flags, arrival/departure flights; passport only when the supplier requires it (Q v1 3.10). Countdown to deletion (return + 90 days). "Flag incident on departure" (R37). Export list to hotel/transport (logged) | M8, R33, R37, R44, Q v1 3.9/3.10 |
| S-03 AA insights | CIS admin | Demand, willingness to pay, option picks, Lost reasons; cells with < 10 travellers or < 3 agencies are suppressed (Q v1 3.12) | M17, R23 |
| S-04 Support session | AA-Partner, agency UI in read-only mode | The agency's own screens, F1 masked unless the owner ticked "show identity", banner on both sides | v2.2 §3 layer 2 |

---

## 2. What we copy from Tern and TravelJoy (the easy parts)

| Pattern | Seen at | Where it lands here |
|---|---|---|
| Trip is the folder; a lead is a trip in the first column (U1) | [TravelJoy trip](https://help.traveljoy.com/hc/en-us/articles/360016089792-Create-and-manage-an-individual-trip), [Tern statuses](https://help.tern.travel/en/articles/7929163-best-practices-for-using-trip-statuses-in-tern) | A-02, A-03; no separate Lead object |
| "Waiting on" you / traveller / supplier / none, next to the stage (U2) | [TravelJoy dashboard](https://help.traveljoy.com/hc/en-us/articles/360016247971-Using-the-Dashboard) | Card chip + filter on A-02; set automatically (§3.2) |
| Click a stage to work the whole batch (U3) | same | Column menu on A-02 |
| One form creates client + trip, dedupes by email + name, several travellers in one submit (U4) | [Tern forms](https://help.tern.travel/en/articles/8594104-managing-forms-in-tern) | C-01; companions without email allowed |
| Tag-triggered task lists; bulk apply with a preview count (U5) | [TravelJoy Jan 2026](https://traveljoy.com/blog/post/product-updates-smarter-forms-easier-approvals-and-more), [Tern Jul 2026](https://www.tern.travel/updates/automated-trip-statuses-new-reports-and-your-agency-back-office-home.html) | A-17, bulk dialogs everywhere |
| Status moves by date, with "changed by automation X" in the log (U6) | Tern Jul 2026 (above) | A-03 timeline |
| Approve and pay in one flow: options → rooms → add-ons → insurance → pay → sign (U7) | [TravelJoy Feb 2025](https://traveljoy.com/blog/post/traveljoy-travel-agency-software-updates-feb-2025), [Tern payments](https://help.tern.travel/en/articles/12176225-payments-authorizations-in-tern) | C-03 → C-04 → C-08 |
| Payment reminders go to the agent first; one switch sends them to the client (U8) | [TravelJoy reminders](https://help.traveljoy.com/hc/en-us/articles/360051796412-Automatically-send-payment-reminders-to-clients) | A-10 reminder queue |
| AI writes only through a preview card; usage meter 75/90/100 % (U9) | [Tern AI chat](https://help.tern.travel/en/articles/14182386-ai-chat-for-notes-and-crm), [Tern limits](https://help.tern.travel/en/articles/15303956-ai-usage-limits) | A-21 draft card, A-00 meter |
| Working copy vs published version, "client viewed at" (U10) | [Tern versioning](https://help.tern.travel/en/articles/8114228-trip-versioning-on-itineraries), [Tern viewed](https://www.tern.travel/updates/see-who-opened-your-itinerary-and-when.html) | A-04 header, A-03 timeline |
| Notes, search and tasks reachable from anywhere (U11) | [Tern Q1 2026](https://tern.travel/whats-new/q1-2026) | A-00 |
| Quick copy of passport / DOB from the trip side bar (U12) | [TravelJoy](https://traveljoy.com/blog/post/product-updates-faster-invoicing-email-campaigns-and-more) | A-03 Travellers tab; each copy is an F1 read, logged |
| Form fields named "Client …" write to the profile (U13) | [TravelJoy form template](https://help.traveljoy.com/hc/en-us/articles/360016307211-Create-a-form-template) | A-16 forms: custom fields map to profile (never F1 fields) |
| Starter pack of templates, short in-app videos (U14) | [Tern agencies](https://www.tern.travel/agencies) | A-20 onboarding, A-16 seeded EN/VI + AA content |
| Option blocks with "choose later" that never block payment | [Tern option blocks](https://help.tern.travel/en/articles/7929166-using-option-blocks-to-present-your-client-with-choices) | C-03; "choose later" allowed only where no hold is needed (§3.5) |
| Task buckets Overdue / Today / Soon / Later | [Tern tasks](https://help.tern.travel/en/articles/7929158-an-introduction-to-tasks-in-tern) | A-09 + "Waiting for dates" (R20) |

**Not copied** (`comparison.md` §3): no-undo editing; date changes silently dropping prices (we re-quote and show the
diff); payment reminders that cannot tell deposit from balance (separate templates); trip referral that cannot be
taken back (owner reassigns, R8); one passport photo per client (documents are a list per traveller).

---

## 3. Main flows

Each step: **actor** → screen → what the system does. Spec gates from §4 are marked **GATE**.

### 3.1 Flow 1: inquiry → trip (Inquiry stage)

1. **Prospect** opens the agency's inquiry form (C-01) from the agency website widget, a hosted link-in-bio page, or a
   CTA on AA-made content in Content studio (E3; lead source recorded automatically).
2. Prospect fills Stage 1 in under 2 minutes: destinations (multi-select + "not sure"), month or dates ± flexibility,
   nights, adults / children with ages, party type, budget band per person excluding flights, style, name, email,
   phone, preferred channel, source. Adds companions in the same submit (name, optional email; R7, U4). Optional "book
   a call" slot from the agent's calendar (R15). Dates echo in words under the field (R32).
3. **System** (`crm_intake_process`): dedupe by blind index on email/phone (R6); creates or matches the client (F1),
   profile (F2 bands), companions with relationship "travels with" (R7), trip at **Inquiry**, system tags from the
   destination (R29), first task "Reply within 2 hours" (M1 success), sends the form's confirmation email. If the
   prospect already has an open Inquiry trip, the new submission is attached to it instead (C47 merged into R6 intake).
4. **Agent** gets a bell + morning digest line; the card appears on A-02 within a minute, waiting on **Me**.
5. Agent opens the trip (A-03). Overview shows the Traveler info panel: Basics 100 %, Planning 0 %, Booking locked.

### 3.2 Flow 2: qualifying

1. **Agent** drags the card to **Qualifying**, or the first reply from Inbox moves it automatically.
2. Agent chooses one: **[Send planning form]** (C-02, auto-sent if the workflow is on, M10) or **[Fill in from call]**
   (same questions inside A-03; R40 can turn call notes into suggested answers and option ideas, preview only).
3. **Client** completes C-02: conditional questions (fitness only for treks with altitude, health flags only after a
   consent screen, R31); returning clients see their earlier bands pre-filled and only confirm (§5 rule 4).
4. **System** updates the panel percentage. Below 80 %, task "Get planning info" exists (§5 automation).
5. "Waiting on" moves to **Client** when a form is sent, back to **Me** when it comes in, to **None** if the agent
   sets it.
6. **GATE Qualifying → Proposal:** Stage 2 ≥ 80 % or agent override with a reason (logged in Activity).

### 3.3 Flow 3: build the proposal with AA live inventory and options

1. **Agent** opens Proposal tab → **Build** (A-04). If Stage 2 ≥ 80 %, the builder pre-fills a skeleton: days from
   nights, region from destinations, default options from Stage 2 (accommodation tier, pace, private vs small group;
   §5 rule 5).
2. For each day the agent picks from the **AA inventory panel**: search by place, activity, tier; each result shows
   net (owner/agent only), suggested sell, margin, availability badge (**Instant** for fixed-schedule products,
   **On request – AA confirms within 1 business day**, **Sold out**; Q v1 6.2), age/fitness limits (R32).
3. Agent adds 2–3 alternatives as an **option block** (day, activity, lodging or transfer). Marks one as default.
   Adds dependency rules with two chips: *requires* / *excludes* (spec §7 `requires[]`, `excludes[]`).
4. Non-AA items come from the agency's suppliers (M15) or the library (R9) and are marked "Agency books".
   R10: a forwarded supplier PDF/email can be turned into suggested lines (preview card, F3 scrubbed).
5. Agent sets the sell price per line or a markup rule; the price bar shows trip total sell, net, margin. If the sell
   price for an AA product falls below AA's public "from" price, a yellow warning shows; it never blocks (Q v1 1.4).
   Pay-on-arrival items (park fees, permits) are flagged `collect: on arrival`, suggested from the CIS tour
   `exclusions` (R25). Per-day time zone is set from the AA product location (R33). Pre-travel section is filled from
   AA prep packs + the agency checklist (R38).
6. Agent previews as client (desktop and phone) and clicks **Publish version n** (working copy stays private, U10).

### 3.4 Flow 4: send

1. **Agent** clicks **Send** (A-05). **GATE:** if Stage 2 < 80 % and no override, the dialog shows the gate first.
2. Agent picks the format (spec `proposal_format`): **Visual link** (email with C-03 link), **Email text**, or
   **WhatsApp/SMS short text** (M4) — all three render from the same priced version, so prices always match (same
   price hash). Saved replies and AI draft (M14, R41 voice profile) are available; nothing leaves without the agent
   pressing Send.
3. **System** moves the trip to **Proposal**, "waiting on: Client", starts the proposal follow-up workflow (M10).
   Sender rule: email goes from the agency's own Gmail/Outlook (send-as); if the mailbox token is dead the message is
   held in "Waiting for reconnect" and a red banner shows, nothing is sent through the platform silently (R24).

### 3.5 Flow 5: client choice

1. **Client** opens C-03 (no login). **System** records "viewed" (R4); if viewed and nothing chosen in 2 days, a
   follow-up task or template fires (R4, M10).
2. For each option block the client taps **Keep**, **Swap** to another option, or **Choose later** (only for
   non-AA or instant items that need no hold). Price and availability refresh live per swap (Booking quote). Options
   that clash with a dependency rule are greyed with the reason ("Needs the Day 3 lodge").
3. Client can **Request a change** (free text + the day it refers to). This sends the agent one bundled notification
   with the diff, not one per tap (R19).
4. **Edge cases** (spec §11.2): option sold out mid-session → the block falls back to the default with a notice and
   the agent is told; agent publishes a new version → the page shows "Your agent updated this proposal" and keeps the
   client's picks where the options still exist; AA inventory down → prices show "last checked 10:42", **Accept**
   is disabled until a fresh quote succeeds, agent is alerted.
5. **System** writes each pick to `Selection(by=client)`; the agent sees the diff in the timeline ("Day 3: Homestay →
   Lodge, +$40 sell / +$12 margin", margin only for owner/agent, R19).

### 3.6 Flow 6: accept → hold → deposit

1. **Client** taps **Accept** on C-03 → C-04. Review screen groups lines (R26): **Confirmed now** (instant AA,
   already-booked agency items) · **AA confirms within 1 business day** (on-request) · **Your agent is booking**
   (non-AA). Pay-on-arrival amounts are listed separately and are not in the deposit (R25).
2. Client confirms travellers and rooms, ticks the agency terms (the version in force is stored with the acceptance
   and the price hash, R34), types their full name.
3. **System** places holds in AA-Booking for every AA line (B2B `hold`) and shows the hold deadline on the deposit
   button: "Deposit link valid until 23 Oct, 17:00 (your reservation is held until then)". **C31:** the link's
   validity equals the earliest hold expiry; after that C-12 says "Your reservation hold has expired" with
   **[Check availability again]**, which re-quotes and, if still available, places a new hold and a new price.
4. Client pays the deposit: Stripe Checkout on the agency's own Stripe account (Connect Standard, Q v1 4.5), or bank
   transfer instructions with "I have paid" (VN and any agency without Stripe; agent marks it received, Q v1 4.6).
   A service-fee invoice, if the agency uses one, is a separate line, never mixed into trip money (R27).
5. **System** on payment: invoice paid, trip → **Booked** (§4: "Entered when deposit paid"), AA holds → confirm
   requests (instant lines confirm at once; on-request lines wait for AA ops), "waiting on: Supplier" while any AA line
   is pending, client portal invite emails go out (one per traveller with an email, R22), Stage 3 unlocks.
6. On a failed payment: hold stays until expiry; after the second failure the agent gets a task.

### 3.7 Flow 7: booking lines (ledger)

1. Each priced line becomes a booking line (M6) with status **Planning → Confirmed → Cancelled** (R18). Only
   **Confirmed** counts in revenue, margin and commission.
2. **AA lines** fill themselves: confirmation (bk- code), net cost, sell, FX rate locked at booking date and source
   (R17); status comes from the Booking event feed and cannot be edited by hand.
3. **Agency lines**: agent enters the supplier confirmation number, cost, sell, commission. The owner chooses the
   strictness in settings (Off / Basic / Strict: which fields are required before Confirmed; R18). Missing commission
   never blocks an assistant: it creates a task for the owner.
4. If AA declines an on-request line, the line turns red and a task offers two buttons: **Swap product** (opens the
   builder on that day) or **Refund that part** (R26).

### 3.8 Flow 8: pre-trip

1. **Travellers** sign in to the client portal with their own email code (C-05), complete their own Stage 3 form
   (C-07: passport fields, DOB, flights or "book flights for me", insurance, emergency contact, room setup), and sign
   terms + trekking waiver + insurance decline if they do not buy insurance (C-08, self-built simple e-sign: email
   code, typed name, consent, sealed PDF; Q v1 4.1, Q v2 5.1, R13).
2. Lead traveller can fill a companion's form when the companion has no email; once sent, the lead cannot read it back
   (passport upload-only, R22).
3. **GATE Booked → Pre-departure:** Stage 3 complete for all travellers + waiver signed.
4. **System** at Pre-departure: AA ops release (M8) sends the confirmed-departure data for AA lines to S-02; the
   agency's access log shows "AA ops viewed trip X on <date>" when ops opens it (Q v1 3.9).
5. Automations: Stage 3 incomplete at T-21 → client nudge + agent alert (§5); trek waiver missing at T-21 → alert
   (R29); passport expiring within 200 days of return → task (R2); T-48 h before arrival flight → task "Confirm arrival
   flight" with a status link (R44 step 1, $0, agency and AA ops only, never the client).
6. Remaining balance: reminder schedule (separate deposit and balance templates; agent-first, U8) → C-10.

### 3.9 Flow 9: travelling

1. **System** moves the trip to **Travelling** on the departure date (log line "moved by: date rule", U6).
2. Agent uses **Pipeline → Travelling now** (R37): grouped by AA region, names hidden until clicked (each reveal logged).
3. If AA ops flags an incident on a `departure_id` (weather, landslide), every agency with travellers on it gets a
   banner and a pre-written WhatsApp draft to its own clients (R37). AA never messages travellers.
4. Client uses the itinerary (C-09), offline-capable (R16), with per-day local time (R33).

### 3.10 Flow 10: post-trip

1. **System** moves the trip to **Completed** on the return date; workflow "Welcome home" (library template) offers a
   draft message (M10, approval required if AI-drafted).
2. Commission check (M13): expected vs received; overdue flags after the supplier's due date.
3. AA ops data for the trip is deleted at return + 90 days; the trip's Activity shows the deletion receipt (M8).
4. The client returns to the pool for **Ready to travel again** (R36; rule with a visible reason, e.g. "Trekked
   2 years ago, new AA trek in the same country") and special-date reminders (R2); sending needs marketing consent.
5. Reports pick up conversion, margin, option picks and lead source (M16).

### 3.11 Side flows

**Lost (before Booked).** Card menu or bulk → **Mark lost** → reason from a fixed list (R23): Price · Price (AA tour) ·
AA sold out (pre-selected when a hold or quote failed) · Chose another agency · Postponed · No response · Other.
Optional "Archive client" (stops all automated sending, keeps history; R23).

**Cancel a booked trip (C12, R21).** **Cancel trip** replaces Delete on any trip with money, signatures, commission or
AA lines. One dialog: (1) shows the AA cancellation terms and charges for each AA line, (2) cancels or releases AA
holds/bookings through the adapter, (3) expires open payment links and voids unpaid invoices, (4) proposes refunds per
the terms version the client accepted (R34), each refund a task (Stripe refund or manual), (5) stops workflows,
(6) tells AA ops to drop the release, (7) moves the trip to the **Cancelled** outcome. Records are kept.

**Delete and trash (R21).** Only trips with none of the above can be deleted; they go to Trash (restore window per
Q2). Restoring re-checks Booking first. A client data-deletion request (M18) bypasses Trash.

**Onboarding (spec §11.5, R43, R6, U14, Q v2 2.1).** First run shows a checklist on Home: connect Gmail or Outlook
(send-as + forwarding address), invite team, import CSV in order clients → relationships → past trips → notes (R6),
review duplicates, embed the inquiry form, connect Stripe or choose bank transfer, set deposit rules, pick the EN/VI
starter templates, book the kickoff call, open the help centre. The agency runs imports itself; AA never touches the
file (R43).

---

## 4. Wireframes (12 key screens)

### WF-1 Pipeline board (A-02)

```
+------------------------------------------------------------------------------------------------------------------+
| AA Partner | [ Search trips, clients, bk-1234, conf. no, phone  Ctrl+K ] [+ New] [Tasks 7] [Bell 3] [EN|VI] [ML] |
+------------+-----------------------------------------------------------------------------------------------------+
| HOME       | Pipeline              View: [Board] List  Travelling now  Closed         [Filters v] [Saved views v]|
| CRM        | Waiting on: (All) (Me 9) (Client 14) (Supplier 3)  Owner: [Anyone v]  Tags: [trekking x] [+ tag]    |
| >Pipeline  | ! 4 trips quiet for more than 3 days  [Show]              ! 2 holds expire in 24 h  [Show]          |
|  Clients   +---------------+---------------+---------------+---------------+---------------+---------------+------+
|  Inbox  5  | INQUIRY 6  [:]| QUALIFYING 5[:]| PROPOSAL 8 [:]| BOOKED 4   [:]| PRE-DEP 3  [:]| TRAVELLING 2  | DONE |
|  Tasks  7  |  $ -          |  $ -          |  $48.2k sell  |  $31.0k       |  $22.4k       |               | >    |
| MONEY      | +-----------+ | +-----------+ | +-----------+ | +-----------+ | +-----------+ | +-----------+ |      |
|  Payments  | |Sapa trek  | | |Ha Giang 6d| | |Laos+Cambo.| | |Mekong 4d  | | |Nepal ABC  | | |Hoi An fam.| |      |
|  Bookings  | |Anna M. +2 | | |Tom K.     | | |Lee family | | |Ruiz x2    | | |Kim S. +1  | | |Do family  | |      |
|  Commiss.  | |Mar 27 ~   | | |Apr 27     | | |12-26 Feb  | | |3-6 Jan    | | |T-19       | | |day 3/9    | |      |
| GROW       | |$1.5-2.5k  | | |S2 60%     | | |v2 viewed  | | |AA 2/3 conf| | |S3 2/2 ok  | | |           | |      |
|  Reports   | |[Me] 2h    | | |[Client]   | | |[Client] 1d| | |[Supplier] | | |waiver 1/2 | | |[None]     | |      |
|  Marketing | |trekking   | | |quiet 4d ! | | |hold 20h ! | | |           | | |[Me]       | | |           | |      |
|  Suppliers | +-----------+ | +-----------+ | +-----------+ | +-----------+ | +-----------+ | +-----------+ |      |
|  Library   | +-----------+ | ...           | ...           | ...           |               |               |      |
|  Automat.  | |...        | |               |               |               |               |               |      |
| CONTENT    | +-----------+ |               |               |               |               |               |      |
| STUDIO  >  |               |               |               |               |               |               |      |
| Settings   | Lost / Cancelled are under "Closed". Drag a card to move stage; gates ask for a reason when not met. |
+------------+-----------------------------------------------------------------------------------------------------+

Column menu [:] (bulk by stage, U3/U5), e.g. on PROPOSAL:
+------------------------------------------------------+
| 8 trips in Proposal                                  |
|  ( ) Send follow-up to clients waiting > 2 days (5)  |
|  ( ) Apply workflow...           (preview: 8 trips)  |
|  ( ) Add / remove tag...                             |
|  ( ) Reassign owner...           (owner only)        |
|  ( ) Mark lost... reason [ v ]   (before Booked)     |
|  ( ) 3 trips missing workflow "Proposal follow-up"   |  <- R30 badge
|                         [Preview 5 messages] [Run]   |
+------------------------------------------------------+
```

Card anatomy: trip name · lead traveller display name + party size · dates or month · budget band (Inquiry,
Qualifying) or sell total (later) · one status line that matters for that stage (Stage 2 %, version viewed, AA lines
confirmed, Stage 3 / waiver) · **waiting on** chip with age · warnings (quiet > 3 days, hold expiring) · tags.
Margin is never on cards (assistants see the board).

Implements: M2, §4, R1, U2, U3, U5, R3, R29, R30, R4, C31, R18, R23 (Closed view), R37 (Travelling now view), R35, R8.

Mobile: one stage per screen with a stage switcher at the top; swipe left/right changes stage; card menu replaces
drag.

### WF-2 Trip workspace, Overview tab (A-03)

```
+------------------------------------------------------------------------------------------------------------------+
| < Pipeline   Laos + Cambodia, 14 days  [PROPOSAL v]  Waiting on: [Client v] since 1 d   Owner: Minh L. [v]       |
|              Lee family (4) . 12-26 Feb 2027 . AUD . tags: family, culture [+]          [Cancel trip] [... ]       |
| Overview | Proposal (v2 sent) | Bookings 3 | Payments | Travellers & docs 4 | Messages 6 | Tasks & notes 2 | Activ.|
+--------------------------------------------------------------+---------------------------------------------------+
| TRAVELER INFO                                                | NEXT ACTIONS                                      |
| [ok] Basics (Stage 1)            100%                        | [ ] Follow up if no choice by Fri   due Fri  Me    |
| [..] Planning info (Stage 2)      60%  missing: fitness,     | [ ] Check visa info pack sent       due -     Me    |
|      dietary   [Send follow-up form] [Fill in from call]     | [+ task]                                          |
| [lock] Booking details (Stage 3)  locked until deposit paid  |                                                   |
+--------------------------------------------------------------+---------------------------------------------------+
| PROPOSAL                                                     | MONEY (owner/agent)                               |
| v2 published 18 Oct . viewed 19 Oct 21:04 (3x) . no choice  | Sell AUD 18,640  Net 15,220  Margin 3,420 (18%)   |
| Client picks so far: Day 3 Lodge (+$40) . Day 7 kept         | Deposit 30% due on accept . Pay on arrival AUD 180|
| Holds: none yet (placed at accept)                           | (assistant sees Sell and payments only)           |
| [Open builder] [Send reminder] [Preview as client]           |                                                   |
+--------------------------------------------------------------+---------------------------------------------------+
| TIMELINE                                      [All] [Messages] [Client actions] [System] [Notes]               |
| 19 Oct 21:06  Client chose Day 3: Homestay -> Riverside Lodge  +$40 sell / +$12 margin  [available, instant]   |
| 19 Oct 21:04  Client viewed proposal v2 (phone)                                                                |
| 18 Oct 10:15  Minh sent proposal v2 by email + WhatsApp text (same price hash 7f3a)                            |
| 18 Oct 10:14  Stage moved Qualifying -> Proposal (gate override: "call covered fitness", Minh)                  |
| 16 Oct 09:00  Planning form reminder sent (moved by: workflow "Qualifying follow-up")                          |
| 15 Oct 14:22  Email from client: "Can we add a cooking class?"  [Open in Inbox]                                |
| 14 Oct 08:51  Inquiry received from website widget (source: AA blog "Laos slow travel")                        |
+------------------------------------------------------------------------------------------------------------------+
| [Note...]                                       [Ask AI: draft follow-up]  (AI 62% of month)                    |
+------------------------------------------------------------------------------------------------------------------+
```

Bookings tab (same workspace):

```
+------------------------------------------------------------------------------------------------------------------+
| Bookings  (only Confirmed lines count in revenue and margin)         Strictness: Basic (settings)  [+ Add line]  |
+----+--------------------------+----------------+-------------+-----------+----------+---------+---------+--------+
|Day | Item                     | Supplier       | Conf. no    | Status    | Cost     | Sell    | FX      | Collect|
+----+--------------------------+----------------+-------------+-----------+----------+---------+---------+--------+
| 1-3| Luang Prabang 3d (AA)    | Adventure Asia | bk-20931    | Confirmed | USD 1,120| AUD 2,100| 1.52 @  | agency |
|    |                          |                |             | (feed)    |          |         | 14 Oct  |        |
| 3  | Riverside Lodge (AA)     | Adventure Asia | bk-20932    | On request| USD 260  | AUD 520 | quote   | agency |
|    |   AA confirms in 1 bus.d |                |             | (feed)    |          |         | lock    |        |
| 8  | Siem Reap hotel          | Hotel Prima    | [ enter ]   | Planning  | [ ]      | AUD 900 | [manual]| agency |
| 9  | Angkor pass              | -              | -           | Planning  | AUD 90   | AUD 90  |         | arrival|
+----+--------------------------+----------------+-------------+-----------+----------+---------+---------+--------+
| ! Hotel Prima needs a confirmation number before Confirmed (Basic).  Commission missing -> task for owner      |
| [Forward a supplier confirmation to AI] -> preview card with suggested line (R10)                              |
+------------------------------------------------------------------------------------------------------------------+
```

Implements: M2 (one timeline, Traveler info panel), §5 panel + automation, M3 (summary), M6, M7 summary, R1, R4,
R17, R18, R19, R25, R26, R10, R3, U6, U10, U11, F3/F5 (Activity tab = per-trip audit lines), C12 (Cancel trip), R21
(Delete in [...] only when allowed), R8 (owner field), §4 gates.

Travellers & docs tab: one row per traveller (role lead/companion, Stage 3 %, waiver, insurance decision, documents
list with a "visible to traveller" flag per document, R22). F1 fields show as `••••` with **Reveal** and **Copy**
(U12); each reveal/copy writes an access event with reason (F5). Health and dietary show as flags only.

Mobile: tabs become a select; Overview stacks panels in the order Next actions → Traveler info → Timeline.

### WF-3 Client profile with relationships (A-07)

```
+------------------------------------------------------------------------------------------------------------------+
| < Clients   Anna Martin  [Reveal contact]  ••••@gmail.com  +61 4•• ••• •12      Owner: agency (assigned Minh)   |
|             Tags: trekking, repeat [+]   Consent: transactional yes . marketing yes (12 Mar 2026, form)         |
|             [Archive client] [Merge...] [Export client] [Delete client data...]                                |
+-----------------------------------------+------------------------------------------------------------------------+
| PROFILE (bands, no identity)            | RELATIONSHIPS                                      [+ Add]            |
| Age band (at next departure) 35-44      | Tom Martin       spouse        <-> (auto reverse)  2 trips together   |
| Budget band   AUD 2.5-4k pp             | Lily Martin      child (9 at Mar 2027 departure)                       |
| Fitness       4-6 h hiking, no altitude | Sarah Nguyen     referred Anna   (lead source: referral)               |
| Pace          balanced                  |                                                                        |
| Lodging tier  comfort                   | SPECIAL DATES (reminders need marketing consent for promos)           |
| Interests     food, culture, trekking   | Birthday       14 Jun         [workflow: Client care]                  |
| Dietary       vegetarian (flag)         | Anniversary    02 Sep                                                  |
| Mobility      none                      | Passport       expires within 200 days of Mar 2027 trip return: no     |
+-----------------------------------------+------------------------------------------------------------------------+
| TRIPS                                                                                                            |
| Sapa trek 5d          Mar 2027   INQUIRY      lead       waiting on Me                                           |
| Ha Long + Ninh Binh   Oct 2025   COMPLETED    lead       AUD 6,200 sell                                          |
| Bali (agency trip)    2024       COMPLETED    companion  imported                                                |
+------------------------------------------------------------------------------------------------------------------+
| CONVERSATIONS: email 14 . WhatsApp 22 . last contact 2 d ago            [Open in Inbox]                          |
| READY TO TRAVEL AGAIN: yes - "Trekked 2025, new AA trek in Vietnam (Pu Luong)"  [Draft message]                  |
+------------------------------------------------------------------------------------------------------------------+
```

Implements: F1 (masked identity, reveal logged), F2 (profile = bands and flags), F5, R7 (relationships with
auto-reverse, referral = lead source), R2, R3, R6 (merge), R8 (client belongs to the agency, owner reassigns), R23
(archive), R32 (age band at departure), R36, M18 (export, deletion bypasses trash), §5 rule 3 (health as flags).

Mobile: header collapses to name + actions menu; sections stack.

### WF-4 Proposal builder with AA live inventory and options (A-04)

```
+------------------------------------------------------------------------------------------------------------------+
| < Trip  Laos + Cambodia   Working copy (v3 draft)  Published: v2 (viewed 19 Oct)   [Preview client v] [Publish v3]|
| Price bar: Sell AUD 18,680  Net AUD 15,248  Margin 3,432 (18.4%)  Pay on arrival AUD 180   Currency AUD  [Send...] |
+------------------------+---------------------------------------------------+-------------------------------------+
| DAYS          [+ Day]  | DAY 3  Luang Prabang  (UTC+7, from AA product)     | AA INVENTORY  (live . synced 10:42) |
|  Pre-travel  (packs)   |                                                   | [ Search place, activity, tier    ] |
|  1 Arrive LPQ          | OPTION BLOCK: Lodging        default from Stage 2 | Filters: Day 3 . 4 pax (2A 2C 7,9)  |
|  2 Kuang Si            | +-----------------------------------------------+ | Tier [comfort v] Group [private v]  |
| >3 Luang Prabang       | | (*) Homestay Ban Xang  comfort    Instant      | | --------------------------------- |
|  4 Mekong slow boat    | |     net 140 . sell 280 . margin 140   default | | Riverside Lodge   comfort  On req. |
|  5 ...                 | | ( ) Riverside Lodge   comfort   On request    | |   net USD 260 . sugg. sell 520     |
|  ...                   | |     net 260 . sell 520 . +40 vs default        | |   AA confirms in 1 business day    |
|  14 Depart PNH         | |     requires: Day 4 slow boat (private)        | |   [+ Add to block] [Details]       |
|                        | | ( ) Amantaka           luxury    Sold out 12-14| | Kayak + village   Instant  min age 8|
| MAP (forked builder)   | |     (cannot add)                               | |   net 45 . sugg. sell 90  [+ Add]  |
| +--------------------+ | +-----------------------------------------------+ | Cooking class     Instant          |
| | LPQ *---* Kuang Si | | Rules: [requires v] [excludes v]                  |   [+ Add as option]                 |
| |  \                 | | Client may: [x] swap  [ ] choose later            | ---------------------------------  |
| |   * Nong Khiaw     | | OPTION BLOCK: Activity (morning)                  | AGENCY SUPPLIERS / LIBRARY          |
| +--------------------+ | (*) Alms + market walk (AA)     Instant           | Hotel Prima (Siem Reap)  [+ Add]    |
|                        | ( ) Cooking class (agency)      Agency books      | Library: "LPQ evening" item [+ Add] |
| Checks                 |                                                   | --------------------------------- |
| ! Day 1 flight lands   | [+ Option block]  [+ Single item]  [AI: ideas from| ! Sell for "Kayak" below AA public  |
|   19:40 after 18:00    |  call notes]  (suggestions only from AA stock)    |   "from" price: warning only        |
|   welcome dinner       |                                                   |                                     |
+------------------------+---------------------------------------------------+-------------------------------------+
| Assistant view: Net/Margin columns and the price bar margin are hidden; sell and availability remain.           |
+------------------------------------------------------------------------------------------------------------------+
```

Implements: M3 (per-day option blocks from AA inventory, defaults from Stage 2, dependency rules, live price and
availability), M15 (agency suppliers next to AA), R9 (library items), R17 (currency/FX lock at quote), R25, R32 (age
limits from inventory), R33 (time zone per day, late-arrival check), R38 (pre-travel day), R40 (AI ideas only from
the day's AA stock, closed list of product codes, server re-checks with Booking), R39 (AI suggestions validated before
the card shows), U10 (working copy vs published), §1 differentiators 1 and 2, Q v1 1.2 (net B2B rates, agency sets
sell), Q v1 1.4 (warn below public price), Q v1 6.2 (instant vs on request), S4 (forked map component).

Edge cases on this screen: AA inventory offline → panel shows "offline, last synced 10:42", AA items cannot be added,
agency items still can; option goes sold out while editing → block shows the red badge and Publish asks to replace
it; shortening the trip re-quotes and shows a before/after price diff instead of dropping prices.

Mobile: builder is usable for edits (change option, price, text) but adding days and the map are desktop-first
(spec §11.6 mobile-first scope: the agent's daily loop is mobile; building is a desk task).

### WF-5 Send proposal dialog (A-05)

```
+------------------------------------------------------------------+
| Send proposal v3 to Lee family                                   |
| ! Planning info 60% (< 80%). [Send planning form first]          |
|   [Override: reason ______________ ]  (logged)                   |
| Format:  (*) Visual link   ( ) Email text   ( ) WhatsApp text    |
| To: lead traveller [Reveal]   Channel: email via minh@agency.au  |
| Template [Proposal - EN v]   Voice: [Minh - email EN v]          |
| +--------------------------------------------------------------+ |
| | Hi {first name}, here is your Laos + Cambodia plan. Tap to   | |
| | keep or swap the options for each day: {proposal link}       | |
| | Total AUD 18,680 for 4 . deposit 30% on acceptance.          | |
| +--------------------------------------------------------------+ |
| [AI: improve draft]  Draft by AI - review before sending         |
| Price hash 7f3a = same as visual version                         |
|                                   [Save draft]  [Send]           |
+------------------------------------------------------------------+
```

Implements: M4 (email / WhatsApp short text, link to picker, prices always match), §4 gate, M5/M9 (channel), M14
(AI drafts, human sends), R41, R24 (sender shown).

### WF-6 Client-facing proposal page (C-03)

```
+----------------------------------------------+
| [Agency logo]           Laos + Cambodia      |
| 12-26 Feb 2027 . 2 adults, 2 children         |
| Prepared by Minh, Sunshine Travel            |
| -------------------------------------------- |
| Total  AUD 18,680                            |
| (park fees AUD 180 paid on arrival)          |
| [ Accept and continue ]   (disabled if price |
|   check is stale: "checking availability")  |
| -------------------------------------------- |
| Before you go  >  (packing, visa links, ...)  |
| -------------------------------------------- |
| DAY 3 . Luang Prabang                        |
| Where you stay   (choose one)                |
| +------------------------------------------+ |
| | [photo] Homestay Ban Xang       Included | |
| |  Family room, garden. [Keep]  (selected) | |
| +------------------------------------------+ |
| | [photo] Riverside Lodge          +$40 pp | |
| |  Confirmed by our partner within         | |
| |  1 business day after you accept         | |
| |  Needs the private slow boat on Day 4    | |
| |                       [Swap to this]     | |
| +------------------------------------------+ |
| | [photo] Amantaka        Not available    | |
| +------------------------------------------+ |
| Morning: Alms + market walk  Included        |
|          Cooking class     +$25 pp [Swap]    |
| [Ask for a change on Day 3]                  |
| -------------------------------------------- |
| DAY 4 . Mekong slow boat ...                 |
| -------------------------------------------- |
| Questions? [Email Minh] [WhatsApp Minh]      |
| Agency terms . Privacy                       |
+----------------------------------------------+
```

Rules: no login; signed link; no traveller names or contact data on the page (only the agency's agent name); price
deltas per person, running total at the top; availability in plain words; cancelled or hidden lines never appear
(R22); "Your agent updated this proposal" banner on a new version; opening the page logs "viewed" (R4). Mobile first:
this wireframe is the phone layout; desktop puts the day list in a left column.

Implements: M3 client side (keep / swap / request change, no client login, live price and availability, dependency
rules shown in words), M11 entry, R4, R19, R22, R26 wording, R38, U7, §11.2 edge cases.

### WF-7 Accept and deposit (C-04), with hold-tied link (C31)

```
+----------------------------------------------+
| Step 1 Review . 2 Travellers . 3 Terms . 4 Pay|
| -------------------------------------------- |
| CONFIRMED AS SOON AS YOU PAY                 |
|   Luang Prabang 3 days, Kuang Si, ...        |
| CONFIRMED BY OUR PARTNER WITHIN 1 BUSINESS DAY|
|   Riverside Lodge (Day 3)                    |
|   If it is not available we will offer an    |
|   alternative or refund that part.           |
| YOUR AGENT BOOKS                              |
|   Hotel in Siem Reap (Day 8-10)              |
| PAID ON ARRIVAL (not in this payment)        |
|   Angkor pass AUD 90 x2 ...      AUD 180     |
| -------------------------------------------- |
| Travellers: 2 adults, 2 children (7, 9)      |
| Rooms: [1 family room v]                     |
| -------------------------------------------- |
| [x] I accept Sunshine Travel's booking terms |
|     (version 2026-09, read)                  |
| Full name [ Grace Lee               ]         |
| -------------------------------------------- |
| Deposit now (30%)              AUD 5,604     |
| Balance due 12 Dec 2026        AUD 13,076    |
| Your places are held until 23 Oct, 17:00.    |
| [ Pay deposit by card ]  (agency Stripe)     |
| [ Pay by bank transfer ]  -> instructions    |
+----------------------------------------------+

After the hold expires (C-12):
+----------------------------------------------+
| Your reservation hold has expired            |
| Prices and places were held until 23 Oct.    |
| [ Check availability again ]                 |
| (new hold + possibly new price; your agent   |
|  has been told)                              |
+----------------------------------------------+
```

Implements: M7 (deposit / balance schedule, pay link on the agency's Stripe, bank transfer for VN), M3 accept,
M12/R34 (versioned terms click, not the waiver e-sign), R25, R26, R27 (service fee shown as a separate invoice when
used), C31, U7, Q v1 4.5/4.6.

### WF-8 Client portal: one-time code and per-person home (C-05, C-06)

```
Sign-in (C-05)                                   Home for a companion (C-06)
+----------------------------------------------+ +----------------------------------------------+
| [Agency logo]  Your trip: Laos + Cambodia    | | Hi Tom                     [EN|VI] [Sign out]|
|                                              | | Laos + Cambodia . 12-26 Feb 2027 . T-112     |
| Enter your email to get a 6-digit code.      | | -------------------------------------------- |
| [ t***@o*****.com  (hint)          ]         | | TO DO FOR YOU                                |
| [ Send code ]                                | |  [ ] My booking details   2 of 6 done  >     |
|                                              | |  [ ] Sign terms + trekking waiver        >   |
| Code [ _ _ _ _ _ _ ]   [ Continue ]          | |  [x] Insurance: I have my own            |
| Codes expire in 10 minutes.                  | | -------------------------------------------- |
| Install this trip on your phone (offline)    | | ITINERARY        >  (works offline)          |
+----------------------------------------------+ | DOCUMENTS        >  e-ticket (mine), waiver  |
                                                 | MESSAGES: [Email Minh] [WhatsApp Minh]       |
Lead traveller home adds:                        | -------------------------------------------- |
+----------------------------------------------+ | You see your own details only. Grace (lead)  |
| PARTY STATUS                                 | | manages payments.                            |
|  Grace (you)   details 6/6  signed           | +----------------------------------------------+
|  Tom           details 2/6  not signed       |
|  Lily (9)      details 4/6  guardian signs   |
|  Max (7)       details 0/6  [Fill for Max]   |
| PAYMENTS     Balance AUD 13,076 due 12 Dec > |
+----------------------------------------------+
```

Rules (R22): every traveller with an email signs in with their own code; the lead sees each person's **progress**, not
their data; the lead can fill a form for a child or a companion without email, but cannot read it back after sending;
passport fields are upload/enter-only, shown back as "received"; cancelled lines and documents not flagged "visible to
traveller" never appear; AA vouchers appear for the right person automatically. Waiver signing per adult; guardian
signs for minors (open point O-6).

Implements: M11 (one link: proposal, Stage 3, documents, invoices, itinerary), §5 Stage 3, M12, R22, R16, R13, F1/F4
(`traveller_self_reveal` only for the signed-in person, v2.2 S6).

### WF-9 Payments (A-10)

```
+------------------------------------------------------------------------------------------------------------------+
| Payments          [Receivables] [Schedules] [Reminders queue 4] [Owed to suppliers]        Currency: all v      |
+------------------------------------------------------------------------------------------------------------------+
| Tiles: Due this week AUD 21,400 . Overdue AUD 3,100 (2) . Deposits paid within 48 h of acceptance: 74% (goal 70)|
+----------+-------------------+-------------+----------+-----------+--------------+-----------+-----------------+
| Trip     | Invoice           | Kind        | Amount   | Due       | Status       | Method    | Actions         |
+----------+-------------------+-------------+----------+-----------+--------------+-----------+-----------------+
| Lee fam. | INV-0142 deposit  | trip        | AUD 5,604| on accept | Link active  | Stripe    | [Copy link]     |
|          |   link valid until hold expiry 23 Oct 17:00              |              |           | [Void]          |
| Ruiz x2  | INV-0139 balance  | trip        | AUD 4,200| 02 Nov    | Overdue 3 d  | Transfer  | [Mark received] |
| Kim S.   | INV-0137          | service fee | AUD 250  | paid      | Paid 12 Oct  | Stripe    | [Receipt]       |
| Do fam.  | INV-0131 balance  | trip        | VND 48.2m| paid      | Paid (manual)| Transfer  | [Receipt]       |
+----------+-------------------+-------------+----------+-----------+--------------+-----------+-----------------+

Reminders queue (agent-first, U8):
| Ruiz x2  balance reminder #2  -> to agent (Me)   [Send to client now] [Edit] [Skip]     Auto-send to clients: [off]|
| Lee fam. deposit reminder     -> to client (auto)  scheduled 22 Oct 09:00                                         |

Owed to suppliers (from booking lines; AA terms per the existing B2B agreement):
| Adventure Asia  bk-20931  USD 1,120  due per B2B terms  [View in Booking]   Hotel Prima  AUD 900  due 01 Dec |
```

Implements: M7 (schedule, Stripe pay links, automatic reminders, success metric tile), R17 (amounts received at the
receipt-date rate), R25 (pay-on-arrival never in links or reminders), R27 (service-fee kind), C31 (link validity),
U8, Q v1 1.3 (AA payable per existing B2B terms), Q v1 4.6 (manual "mark received"). Refund tasks from C12 land here.

Mobile: list of cards; the queue is the default tab on phones.

### WF-10 Tasks grouped by due (A-09)

```
+------------------------------------------------------------------------------------------------------------------+
| Tasks   Assignee: [Me v]  Trip: [any v]  Source: [all v] (workflow / AI / manual / AA event)   [+ Task]          |
| Morning digest email: [on] (one email per day, no client names)                                                  |
+------------------------------------------------------------------------------------------------------------------+
| OVERDUE (2)                                                                                                      |
|  [ ] Reply to inquiry (2 h target)          Sapa trek         Minh   due today 10:30  (late 1 h)                  |
|  [ ] Confirmation no. for Hotel Prima        Laos + Cambodia   Minh   due 20 Oct                                  |
| TODAY (3)                                                                                                        |
|  [ ] AA hold expires 17:00 - deposit not paid   Laos + Cambodia   Minh   [Open payment]                          |
|  [ ] Confirm arrival flight VN611 (T-48 h)      Nepal ABC         Linh   [Flight status]                          |
|  [ ] Stage 3 incomplete at T-21 (Tom, Max)      Nepal ABC         Linh   [Nudge travellers]                       |
| UPCOMING - next 7 days (4)                                                                                       |
| LATER (9)                                                                                                        |
| WAITING FOR DATES (3)   due "T-21" - trip has no dates yet; due date fills in when dates are set                 |
|  [ ] Send pre-travel pack (T-30)             Ha Giang 6d       Minh                                              |
+------------------------------------------------------------------------------------------------------------------+
```

Implements: M10 (tasks per stage, nothing forgotten), R20 (buckets, relative due dates, waiting-for-dates, digest),
§5 automation (T-21), R44 (T-48 h), C31 (hold-expiry task), R2 (special-date tasks), R9 (task lists from library),
U11 (same list in the drawer). Edited due dates are not recalculated when trip dates change (R20).

### WF-11 Inbox and messages (A-08)

```
+------------------------------------------------------------------------------------------------------------------+
| Inbox  [All] [Email] [WhatsApp] [SMS] [AI drafts 3] [Unmatched 2] [Waiting for reconnect 0]   [Mine v]           |
+---------------------------------+--------------------------------------------------------+-----------------------+
| Grace Lee - Laos+Cam.   WA  2m  | Grace Lee  (WhatsApp +61 4•• ••• •12)  [Reveal]        | TRIP                  |
| "Can Max do the kayak?"         | Linked trip: Laos + Cambodia [change]                  | Laos + Cambodia       |
| Tom K. - Ha Giang      @ 1h    | -------------------------------------------------------| PROPOSAL . waiting on |
| "Dates for April"               | 19 Oct 21:10  Grace: Can Max do the kayak? He is 7.   |   Me (auto: new msg)  |
| +84 9•• (unknown)      WA  3h   | 19 Oct 21:12  (internal note, Minh) min age is 8 ...  | Stage 2 60%           |
| "Hi, saw your tour..."  [Link]  | -------------------------------------------------------| [Open trip]           |
| Kim S. - Nepal         @ 1d    | AI DRAFT (review before sending)       thumbs: [+] [-] | QUICK                 |
|                                 | "Hi Grace, the kayak trip has a minimum age of 8,     | [Insert proposal link]|
|                                 |  so for Max I suggest the village bike ride..."      | [Saved replies v]     |
|                                 | checked: product codes in stock . price unchanged     | [Planning form link]  |
|                                 | [Use draft] [Edit] [Discard]  reason for [-]: [v]     |                       |
|                                 | -------------------------------------------------------|                       |
|                                 | WhatsApp window open 21 h left (outside: templates)   |                       |
|                                 | [Type a reply...]               [Template v] [Send]    |                       |
+---------------------------------+--------------------------------------------------------+-----------------------+
| Email: sent from minh@sunshine.au (send-as) . inbound via forwarding address in+sunshine@... (BCC also works)    |
+------------------------------------------------------------------------------------------------------------------+
```

Implements: M5 (email threads linked to trip, saved replies, internal notes; inbound by forwarding/BCC and send-as
from Gmail/Outlook, Q v2 4.1, Q v1 4.8), M9 (WhatsApp/SMS through the agency's own Twilio, approved templates, 24-hour
window shown; Q v1 4.2/4.4/4.3), M14 + R39 (draft card, rule checks before showing, thumbs with fixed reason codes),
R24 (sender shown; "Waiting for reconnect" folder), R1 (new message flips waiting-on to Me), §11.2 (unknown inbound
number → Unmatched → link to client or create trip). Messenger/Instagram and Zalo are not in v1 (Q v1 4.3, 2.7).

Mobile: list → thread → trip panel as three screens.

### WF-12 Settings and templates (A-18 + A-16)

```
+------------------------------------------------------------------------------------------------------------------+
| Settings                                                                                                         |
+---------------------------+--------------------------------------------------------------------------------------+
| Agency & branding         | LIBRARY > Messages                         [EN] [VI]   Scope: [Agency v]  [+ New]   |
| Team & roles              | +--------------------------------------------------------------------------------+   |
| Security (2-step)         | | Name                      Channel   Stage / trigger        Lang  Source       |   |
| Channels                  | | Proposal - first send      email     Proposal sent          EN VI AA starter  |   |
|   Email (Gmail/Outlook)   | | Proposal follow-up (2 d)   email     viewed, no choice      EN VI AA starter  |   |
|   WhatsApp & SMS (Twilio) | | Deposit reminder           email/WA  deposit due            EN VI AA starter  |   |
|   Calendar (call booking) | | Balance reminder           email/WA  balance due            EN VI AA starter  |   |
| Payments                  | | Stage 3 nudge (T-21)       email/WA  T-21, Stage 3 < 100%   EN VI AA starter  |   |
|   Stripe / bank transfer  | | Welcome home               email     Completed              EN VI agency      |   |
|   Deposit & balance rules | +--------------------------------------------------------------------------------+   |
|   Currencies & FX         | Other library tabs: Itinerary items . Task lists . Forms (intake, planning,         |
|   Service fee (off)       |   booking details) . Pre-travel packs (AA) . Terms, waivers, consents (versioned)   |
|   Booking line rules      |                                                                                      |
| Forms & embed code        | TERMS & WAIVERS (R34)                                                                |
| AI                        |  Booking terms   v2026-09 in force (since 01 Sep)  [View] [New version]  accepted 14x|
|   On/off, usage, voices   |  Trekking waiver v2026-10 (insurer review: pending)                                 |
| Data & privacy            |                                                                                      |
|   Access log (12 months)  | DATA & PRIVACY                                                                       |
|   AA support access       |  AA support access: [off]  -> Allow for [24 h v] (1-7 days), read-only,             |
|   AA insights: included   |     show traveller identity [ ]   (every view is logged; revoke any time)          |
|   Export all data         |  Access log: [user] [AI agent] [AA ops] [AA support] [AA emergency]  [Download]     |
|   Trash                   |   20 Oct 14:02  AA ops viewed trip "Nepal ABC" (ops release)                        |
| Plan & usage: Free        |   19 Oct 09:11  Minh revealed passport (Tom) - reason: supplier booking              |
| What's new . preview [ ]  |  AA insights: included (groups >= 10 travellers, >= 3 agencies) [Request opt-out]   |
+---------------------------+--------------------------------------------------------------------------------------+
```

Implements: F4 (team, roles owner/agent/assistant, invites < 5 min; R8 reassign on deactivation), Q v1 3.13 (2-step),
F5 + Q v1 3.8/3.9 (access log), v2.2 layer 2 + Q v1 3.5 (support access 1–7 days, default 24 h), M17 + Q v1 3.12
(default include + opt-out request), M18 (export, deletion), R21 (trash), M5/M9/R15 channels, R24 (sender table
under Channels → Email), M7/R17/R25/R27/R18 payment settings, M1/R31 forms + embed code, M14/R5/R41 AI, R9 + U14
(library seeded EN/VI + AA content), R34, R38, R42 (what's new, one preview switch), R11 (Plan: Free, fair-use AI).

### Supporting wireframe: Reports and Home KPI tiles (A-14, A-01)

```
+------------------------------------------------------------------------------------------------------------------+
| Reports    Period [Last 12 months v]  Compare [same period last year v]  Owner [all v]        [Export CSV]       |
+---------------------+---------------------+---------------------+---------------------+---------------------------+
| Inquiries      142  | Win rate      31%   | Margin    AUD 61k   | AA product share 64%| (Home shows the same 4    |
|   +18% YoY          |   +4 pts YoY        |   +9% YoY           |   of sell           |  tiles + "needs you"      |
| [list]              | [list]              | (owner/agent only)  | [list]              |  tiles that open a list)  |
+---------------------+---------------------+---------------------+---------------------+---------------------------+
| FUNNEL  Inquiry 142 -> Qualifying 118 -> Proposal 77 -> Booked 44 -> Completed 39     Lost 61 / Cancelled 3     |
| LOST REASONS  Price 21 . Chose another agency 14 . No response 12 . AA sold out 6 . Price (AA tour) 5 . Other 3 |
| LEAD SOURCES  Website form 61 . AA content CTA 28 . Referral 22 . Instagram link 18 . Import 13                |
| OPTION PICKS  Upgrade chosen 23% (goal >= 20%) . most swapped: Day 3 lodging . kept default 61%                |
| MARGIN BY TRIP TYPE (system tags)  trekking 19% . family 16% . day tours 22%                                    |
| New agency (< 12 months): trend shows the last 3 months instead of YoY                                          |
+------------------------------------------------------------------------------------------------------------------+
```

Implements: M16 (conversion by stage, margin, lead source, option picks), R28 (YoY tiles, computed on open, 3-month
trend for new agencies), R23 (Lost reasons), R17 (stable converted amounts), R18 (Confirmed lines only), E3 (AA content
as a source). Assistant: margin tiles and columns hidden.

### Small dialogs (referenced above)

```
Cancel trip (C12)                                        Mark lost (R23)
+------------------------------------------------------+ +---------------------------------------------+
| Cancel "Mekong 4d" (Booked, deposit paid)            | | Mark 1 trip as lost                         |
| 1 AA lines: bk-20811 cancel fee USD 60 (AA terms)    | | Reason [AA sold out (suggested) v]          |
|   bk-20812 on request -> release hold, no fee        | | Note (optional) [...................]       |
| 2 Payment links: INV-0140 balance -> void            | | [ ] Archive client (stop all sending)       |
| 3 Refund proposal per terms v2026-09:                | |                    [Cancel] [Mark lost]     |
|   AUD 1,800 of 2,400 paid -> creates refund task     | +---------------------------------------------+
| 4 Workflows stop; AA ops release withdrawn           |
| Reason [Client illness v]                            | Stage gate override (§4)
| Type CANCEL to confirm [______]                      | +---------------------------------------------+
|                      [Keep trip] [Cancel trip]       | | Planning info is 60% (needs 80%).           |
+------------------------------------------------------+ | Reason [ covered on call 18 Oct ]  (logged) |
                                                         |                   [Back] [Move anyway]      |
                                                         +---------------------------------------------+
```

---

## 5. Client-facing pages: rules

1. **No account, ever.** Forms (C-01, C-02) and the proposal (C-03, C-04) work from signed links. The client portal
   (C-05+) uses a 6-digit email code per person, valid 10 minutes; the session cookie is host-only on the client
   host and tied to one trip (v2.2 S6 `traveller_self_reveal`). A code is asked again before signing (C-08).
2. **Per-person view (R22).** Two roles only: lead and companion. A person sees their own forms, documents flagged
   "visible to traveller", the itinerary, and their own signatures. The lead also sees party progress (not data) and
   payments. The OTP email hint is masked (`t***@o*****.com`).
3. **What the client never sees:** other travellers' data; passport numbers after upload; net cost or margin;
   cancelled lines; internal notes; AI drafts; any AA branding unless the agency chooses it (the agency is the brand;
   AA product names appear as products).
4. **Stage rules (§5):** Stage 3 forms appear only after the deposit; health questions only after a consent screen
   that explains why; budget and fitness as bands; returning travellers confirm pre-filled answers (rule 4; identity
   pre-fill only inside the portal after the code).
5. **Money words:** deposit and balance always labelled separately (avoids the Tern reminder flaw); pay-on-arrival
   amounts listed but never charged (R25); grouped confirmation wording (R26); hold deadline printed next to every pay
   button and the link stops working at the hold expiry (C31).
6. **Language and format:** EN/VI switch on every page; dates with month names; currency of the proposal; per-day
   local time on the itinerary (R32, R33).
7. **Offline:** the itinerary page is installable (PWA) and caches the itinerary and the traveller's own documents
   for offline reading (R16). No push notifications in v1.
8. **Consent and sending:** every marketing message (special dates, re-engage, campaigns) carries an unsubscribe link
   to C-11; archived clients and opted-out clients are blocked at the dispatcher, not only in the UI (R14, R23, R36).
9. **Accessibility and phones:** all client pages are designed phone-first (the wireframes above are phone width);
   large tap targets for Keep/Swap; the error summary jumps to the first error (R31).

---

## 6. Mapping

### 6.1 Spec modules → screens

| Spec | Screen(s) | Notes |
|---|---|---|
| F1 Identity vault | A-03 Travellers tab, A-07, A-08 (masked + Reveal), C-07, C-08 | Reveal/copy logged; passport upload-only on client side |
| F2 Pseudonymous profile | A-07 Profile panel, A-04 defaults | Bands and flags only |
| F3 PII scrubber | A-21 AI draft cards (A-05, A-08, A-03), R10 import preview | Invisible except "scrubbed" note in AI card details |
| F4 Tenancy & access | A-18 Team & roles, role-based hiding everywhere, S-04 | Assistant: no margin, no commissions |
| F5 Audit log | A-18 Access log, A-03 Activity tab | 12 months in app, download (Q v1 3.8) |
| M1 Intake form | C-01, A-18 Forms & embed | Widget, hosted page, multi-traveller |
| M2 Trip pipeline | A-02, A-03 Overview | Waiting on, bulk by stage, quiet > 3 d flag |
| M3 Interactive proposal | A-04, C-03, C-04 | AA inventory panel, option blocks, rules, live price |
| M4 Text proposal mode | A-05 | Same price hash |
| M5 Unified inbox (email) | A-08, A-18 Channels | Forwarding/BCC in + send-as out (Q v2 4.1) |
| M6 Bookings ledger | A-03 Bookings tab, A-11 | AA lines auto, statuses R18 |
| M7 Invoices & payments | A-10, A-03 Payments tab, C-04, C-10 | Stripe Connect Standard, bank transfer, reminders |
| M8 AA ops release | S-02, A-03 Activity, A-18 Access log | Deletion at return + 90 d |
| M9 Inbox WhatsApp/SMS | A-08, A-18 Channels | Agency's own Twilio |
| M10 Workflow automation | A-17, A-09, A-16 Messages | Tag and system-tag triggers |
| M11 Client portal | C-05 – C-10 | Per person |
| M12 Contracts & waivers | C-08, A-16 Terms & waivers, A-03 Travellers tab | Self-built simple e-sign |
| M13 Commission tracking | A-12, A-03 Bookings tab | Expected vs received, overdue |
| M14 AI agent layer | A-21 draft cards in A-03/A-05/A-08, A-00 meter, A-18 AI | Approve before send |
| M15 Supplier directory | A-13, A-04 side panel | AA default + own |
| M16 Agency reports | A-14, A-01 tiles | |
| M17 AA insights | S-03; agency side: A-18 "AA insights: included / request opt-out" | k ≥ 10, ≥ 3 agencies |
| M18 Data portability | A-18 Export / Trash, A-07 Export client / Delete client data | Deletion bypasses trash |
| §4 Pipeline + gates | A-02, A-03, gate dialog | Lost + Cancelled under Closed |
| §5 Traveler info panel + automation | A-03 Overview, A-09 | |
| §11.5 Onboarding | A-20 (checklist on A-01, import wizard) | |
| §11.6 NFR (mobile, languages, currencies, time zones) | All screens (mobile notes), A-00, A-18 Payments | |
| §11.2 Edge cases | A-04, C-03, C-04, A-08 Unmatched, A-10 | §3.5 step 4 |

### 6.2 R1–R44 → screens

| R | Item | Screen(s) |
|---|---|---|
| R1 | Waiting on + bulk by stage | A-02, A-03 header |
| R2 | Special dates (passport 200 d, birthday, anniversary) | A-07, A-17 trigger, A-09, A-15 |
| R3 | Tags + workflows by tag, bulk with preview | A-02, A-06, A-07, A-17 |
| R4 | Proposal viewed event + nudge | A-03 timeline, A-02 card, A-00 bell, A-17 |
| R5 | AI usage meter 75/90/100 % | A-00, A-18 AI |
| R6 | Duplicate merge + staged import | A-06 Duplicates, A-07 Merge, A-20 import |
| R7 | Relationships + multi-traveller form | A-07, C-01 |
| R8 | Clients belong to the agency; owner reassigns | A-03 owner field, A-07, A-18 Team (deactivate → reassign) |
| R9 | Library (items, task lists, messages), seeded EN/VI + AA content | A-16, A-04 side panel |
| R10 | AI reads other suppliers' confirmations → suggested lines | A-03 Bookings tab, A-08 (forward), A-21 card |
| R11 | Tiers (decided: free now, tiers later) | A-18 Plan & usage (shows "Free", fair-use AI) |
| R12 | Group booking (decided: after 23 modules) | Reserved: A-02 view "Groups" + C-03 group landing (not designed in v3) |
| R13 | Insurance (decided: v1 = signed decline only) | C-08, C-07, A-03 Travellers tab |
| R14 | Email campaigns (decided: yes, consent + unsubscribe, AA content to choose) | A-15 Campaigns, C-11 |
| R15 | Book a call in the form + calendar sync (add now) | C-01, A-18 Channels → Calendar, A-09 |
| R16 | Offline itinerary PWA (add now) | C-09, C-05 install hint |
| R17 | FX rules (booking-date / receipt-date, frozen) | A-03 Bookings, A-10, A-14, A-18 Payments |
| R18 | Booking line status Planning/Confirmed/Cancelled; strictness | A-03 Bookings, A-11, A-18 Payments |
| R19 | Client choice diff in timeline + bundled notice | A-03 timeline, A-00 bell |
| R20 | Task buckets, relative due dates, waiting-for-dates, digest | A-09, A-00 drawer |
| R21 | Trash + delete block → Cancel trip | A-03 [...], A-18 Trash, cancel dialog |
| R22 | Per-person client view, hide cancelled, doc visibility | C-05 – C-10, A-03 Travellers tab |
| R23 | Archive client + Lost reasons | A-07, Lost dialog, A-02 Closed, A-14 |
| R24 | Sender table + mailbox disconnect rule | A-08 "Waiting for reconnect", A-18 Channels, A-05 |
| R25 | Pay on arrival | A-04, A-03 Bookings, C-03, C-04, A-10 |
| R26 | Grouped confirmation wording; AA decline → swap/refund task | C-04, A-03 Bookings, A-09 |
| R27 | Service-fee invoice kind | A-10, A-18 Payments, C-10 |
| R28 | KPI tiles YoY | A-01, A-14 |
| R29 | Workflows by trip type via system tags | A-17, A-02 tags |
| R30 | "N trips missing workflow Y" + bulk fix | A-02 column menu, A-17 badge |
| R31 | Conditional, paged forms, jump to first error | C-01, C-02, C-07, A-16 Forms |
| R32 | Locale dates, age band at departure | A-00, A-07, A-04, all client pages |
| R33 | Time zone per day, overnight flights | A-04 checks, C-09, C-07 flights, S-02 |
| R34 | Versioned terms tied to acceptance | C-04, A-16 Terms, A-18 |
| R35 | Global search Ctrl/Cmd+K by bk- code, conf. no, phone | A-00 |
| R36 | Ready to travel again (rules, reasons, consent at send) | A-15, A-07 |
| R37 | Where are my clients + AA incident flag by departure | A-02 Travelling now, S-02, A-00 bell |
| R38 | Pre-travel section from AA packs (decided per Q v1 2.3) | A-04 Pre-travel day, A-16 packs, C-03, C-09 |
| R39 | AI guardrails: checks before preview, chips, thumbs with reason codes | A-21 card in A-08/A-05/A-04 |
| R40 | AI notes → option blocks from the day's AA stock | A-04 "AI: ideas from call notes", A-03 Qualifying |
| R41 | Voice profiles per agent (max 4) | A-18 AI → Voices, A-05 voice picker |
| R42 | What's new (EN/VI), stable layout, one preview switch | A-00 Help & what's new, A-18, S-01 (release notes source) |
| R43 | Support model: self-serve checklist, help centre, office hours; bot later | A-20 checklist on A-01, Help menu |
| R44 | T-48 h "confirm arrival flight" task ($0 step) | A-09, S-02 |
| C12 | One-action trip cancellation | A-03 [Cancel trip], cancel dialog, A-10 refund tasks |
| C31 | Deposit link validity = AA hold expiry | C-04, C-12, A-10, A-09, A-02 card warning |

### 6.3 Questionnaire decisions reflected in the UI

| Decision | Where |
|---|---|
| Q v1 1.1 free for all now | A-18 Plan & usage "Free"; no upsell screens |
| Q v1 1.2 / v2 1.1 B2B net (15 % margin), agency sets sell | A-04 net/sell/margin |
| Q v1 1.3 / v2 1.2 AA collects per existing B2B terms | A-10 Owed to suppliers |
| Q v1 1.4 / v2 1.3 warn below public "from" price | A-04 warning |
| Q v1 2.6 neutral domain, agency custom domain optional, email from agency mailbox | §1.1, A-18 Channels / Branding |
| Q v1 3.5 support access 1–7 days, default 24 h, read-only, identity hidden | A-18, A-00 banner, S-04 |
| Q v1 3.8 / 3.9 access log 12 months; "AA ops viewed trip X" | A-18 Access log |
| Q v1 3.10 ops data minimal | S-02 |
| Q v1 3.12 insights default + opt-out | A-18 |
| Q v1 3.13 2-step for owner and agent | A-18 Security, sign-in |
| Q v1 4.1 self-built simple e-sign | C-08 |
| Q v1 4.2–4.4 WhatsApp + SMS via agency Twilio; Messenger/IG later | A-08, A-18 Channels |
| Q v1 4.5 / 4.6 Stripe Connect Standard; VN manual | C-04, A-10 |
| Q v2 4.1 + Q v1 4.8 forwarding/BCC + send-as, Gmail and Outlook together | A-08, A-18 Channels |
| Q v1 6.2 / v2 6.1 instant vs on request (1 business day) | A-04, C-03, C-04, A-03 Bookings |
| Q v1 6.3 owner recovery after 14 days | S-01; agency side: email + banner "Owner change requested, [Cancel]" for every member |

### 6.4 Not placed, or placed only partly

| Item | Status | Why |
|---|---|---|
| R12 group booking | Reserved slot only | Decided "after 23 modules" (Q v1 2.1); needs Booking departures/allotment, which do not exist in AA-Booking today (only a `fixed_departure` pricing channel) |
| R13 in-app insurance quote/sale | Not placed | Decided: v1 = signed decline only; sale after 23 modules (Q v2 5.1 note, 5.2) |
| R43 help bot | Not placed | Turns on after ~50 real questions (Q v2 2.1) |
| R44 paid flight tracking | Not placed | Only after ops reports a real missed pickup, price approved first |
| R11 paid tiers | Rule only (A-18 shows "Free") | Tiers start at the Q v1 1.1 triggers |
| R42 monthly release train | Process rule, no screen | Only the "What's new" panel and preview switch are UI |
| Messenger / Instagram (§7 enum) | Not placed | After 23 modules (Q v1 4.3) |
| Zalo | Not placed | Q v1 2.7 |
| Two-way mailbox sync (spec M5 wording) | Not placed | Q v2 4.1: forwarding + send-as; spec wording to be changed |
| Post-trip feedback form | Not placed | Not in the spec or any approved R-item; see open point O-9 |

---

## 7. Dependencies the UI assumes

1. **Booking B2B API** (v2.1 D4): catalogue search via CIS `catalog.v1`, quote (price + availability + FX lock),
   `on_request` flag, hold with an expiry timestamp, confirm, cancel with fee, event feed (confirmed / declined /
   cancelled), and an incident flag by departure. None of this exists in AA-Booking yet (CONTEXT has pricing rules,
   FX, trip cases; no departures or allotment). A-04, C-03, C-04, A-03 Bookings, C12 and C31 all depend on it.
2. **Hold duration and on-request SLA** come from Booking; the UI prints whatever Booking returns.
3. **CIS tour fields** for pay-on-arrival suggestions (`exclusions`) and system tags (duration, activities,
   intensity); pre-travel packs are AA-written content (R38 notes the catalogue lacks packing/fitness/altitude/visa
   fields).
4. **Forked TripPlanner map** for A-04 (v2.2 S4).

---

## 8. Screen index

| ID | Screen | Wireframe |
|---|---|---|
| A-00 | Global shell (search, new, tasks/notes drawers, bell, AI meter, language, support banner, undo) | in WF-1 header |
| A-01 | Home: KPI tiles, "needs you" tiles, onboarding checklist | Reports supporting WF |
| A-02 | Pipeline: Board / List / Travelling now / Closed | WF-1 |
| A-03 | Trip workspace (Overview, Proposal, Bookings, Payments, Travellers & docs, Messages, Tasks & notes, Activity) | WF-2 |
| A-04 | Proposal builder | WF-4 |
| A-05 | Send proposal dialog | WF-5 |
| A-06 | Clients directory (tags, archived, duplicates) | — (standard list) |
| A-07 | Client profile | WF-3 |
| A-08 | Inbox | WF-11 |
| A-09 | Tasks | WF-10 |
| A-10 | Payments | WF-9 |
| A-11 | Bookings ledger (all trips) | — (same table as WF-2 Bookings tab, with trip column) |
| A-12 | Commissions | — (table: supplier, trip, expected, received, due, overdue flag) |
| A-13 | Suppliers | — (list; AA pinned first) |
| A-14 | Reports | supporting WF |
| A-15 | Marketing: Ready to travel again, Special dates, Campaigns | — (list with reason + consent state + [Draft]) |
| A-16 | Library | WF-12 (right pane) |
| A-17 | Automations | — (workflow list: trigger, timing, actions, auto-apply rule, "missing on N trips" badge) |
| A-18 | Settings | WF-12 |
| A-20 | Onboarding checklist + import wizard | — (checklist in §3.11) |
| A-21 | AI draft card (component used in A-03, A-04, A-05, A-08) | in WF-11 |
| C-01 … C-12 | Client pages | WF-6, WF-7, WF-8 (+ §1.4) |
| S-01 … S-04 | AA staff screens | §1.5 |

---

## 9. Open points for the owner

| # | Point | Proposal |
|---|---|---|
| O-1 | Showing traveller names on the board, inbox and lists is an F1 read at volume. Logging every card render floods F5 and may trip the KMS "Decrypt spike" alarm | One batched `list_view` access event per page load (record ids, field = display name); sensitive classes (passport, DOB, health, emergency contact) always click-to-reveal per field. Needs the security reviewer's sign-off |
| O-2 | Spec §4 has Lost only before Booked; a booked trip that is cancelled has no stage | Add a terminal **Cancelled** outcome (C12, R21). Spec wording change for Ms. Thu |
| O-3 | Accepting on a no-login page: who accepted? | Typed full name + terms version + timestamp + link id (TravelJoy-style approve-and-pay). Ask for an email code at accept only if the insurer or lawyer requires it |
| O-4 | "Choose later" vs holds | Allowed only for blocks that need no AA hold (agency items, instant items with open availability); AA on-request blocks must be decided at accept |
| O-5 | Hold length unknown; a bank transfer may take longer than the hold | Booking to define hold length per product; if a client picks bank transfer, the agent can request one hold extension from A-03 (Booking rule) |
| O-6 | Waiver signing for a party | Each adult signs their own waiver; the lead (guardian) signs for minors. Confirm with the insurer (Q v2 5.1) |
| O-7 | Price detail on C-03 | Running total + per-person option deltas only, no line-by-line prices. C13 ("show total only") was not approved; confirm the deltas do not reveal AA prices in a way that undercuts TripPlanner |
| O-8 | Builder on phones | Edit on phone (swap option, price, text); build on desktop. Matches spec §11.6 "mobile-first scope" if the scope is the daily loop |
| O-9 | Post-trip feedback | Not in spec or R-items. A "Welcome home" template exists; a rating form would be a new item |
| O-10 | "Owed to suppliers" for AA lines | Needs Booking to expose B2B invoices and due dates per agency; until then show "per B2B terms" with a link only |
| O-11 | Trash restore window | 7 days (Tern) unless Ms. Thu sets another value; client data-deletion requests skip Trash |
| O-12 | Content studio → CRM cross-link | Suggestion only: "Start a proposal with this tour" on My catalog tours, and AA content CTAs that carry the lead source (E3). Not an approved R-item |
| O-13 | File paths | The task's `v2.1/partner-crm-spec.md` does not exist (spec is at `docs/research/partner-crm-spec.md`); v2.2 is still only in `.tmp-session/s245-r2/r4/`. Copy v2.2 into `docs/audits/` with the root PR |
