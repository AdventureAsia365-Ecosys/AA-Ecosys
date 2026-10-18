# Adventure Asia Partner CRM — Product Spec

## 1. What we're building

A CRM given to Adventure Asia (AA) partner travel agencies to manage **their own customers (B2C)**: inquiry → proposal → booking → payment → trip → follow-up.

A separately built **visual itinerary builder** plugs into it. The CRM covers Tern + TravelJoy-style functionality, plus three things competitors don't have:

1. **Live AA supply inside the CRM.** AA trips, net rates and availability are pre-loaded and confirmed automatically.
2. **Traveler-configurable proposals.** Clients swap per-day options on real inventory with live pricing.
3. **Privacy by architecture.** AI agents and AA never see who a traveler is, only what they want.

**Positioning:** free for partners, and it pays for itself when they sell AA product.

## 2. Principles

- Traveler data belongs to the agency. AA never markets to an agency's travelers.
- AI drafts, humans send. Nothing goes to a client without agent approval.
- Ask clients only what is needed at each stage.
- Every task must be faster than the agency's current Gmail + WhatsApp + spreadsheet routine.
- Privacy foundation ships before any feature that stores or reads traveler data.

## 3. Users

| User | Role |
|---|---|
| Agency owner | Full access, margins, reports, team management |
| Agency agent | Leads, trips, proposals, inbox |
| Agency assistant | Bookings, documents, no margin visibility |
| Traveler | Intake forms, interactive proposal, client portal, payments, e-sign |
| AA ops | Confirmed-departure traveler details only (via module 8) |
| AA management | Aggregated, anonymized insights only (module 17) |

## 4. Pipeline

```
Inquiry → Qualifying → Proposal → Booked → Pre-departure → Travelling → Completed
                                                                      ↘ Lost (from any stage before Booked)
```

| Stage | Entered when | Gate to next stage |
|---|---|---|
| Inquiry | Stage 1 intake form submitted (auto-creates lead, profile, trip) | — |
| Qualifying | Agent starts working the lead | Stage 2 info ≥ 80% complete, or agent override |
| Proposal | Proposal sent | Client accepts |
| Booked | Deposit paid | Stage 3 info complete + waiver signed |
| Pre-departure | Stage 3 complete | Departure date |
| Travelling | Departure date | Return date |
| Completed | Return date | — |

## 5. Information collected from travelers

### Stage 1 — Inquiry (intake form, under 2 minutes)
Destination(s) (multi-select + "not sure"), dates or month ± flexibility, nights, adults / children with ages, party type, **budget band per person excluding flights**, trip style (relaxed / balanced / adventure-packed), name, email, phone, preferred contact channel, lead source.

### Stage 2 — Qualifying (auto-sent follow-up form, or agent fills in during a call)
Fitness (hours of hiking per day, trekking experience, altitude), accommodation tier, private vs. small group, must-do / must-avoid, interests, occasion, dietary flags, mobility / health flags (optional, with consent), past trips liked / disliked, budget flexibility, decision maker, booking timeline, competing quotes.

### Stage 3 — Booked (client portal; unlocks only after the deposit is paid)
Full names as on passport, passport number / expiry / nationality, date of birth, flight details or "book flights for me", travel insurance, emergency contact, room setup, signed terms + trekking waiver.

### Rules
1. Never ask in an earlier stage what is only needed later.
2. Use bands for budget and fitness, not open numbers.
3. Health questions are optional, gentle, and explain why they're asked. Stored as flags, never free text.
4. Repeat travelers get pre-filled forms; they only confirm or edit.
5. Stage 2 answers set the default options in the interactive proposal.

### Data placement

| Data | Store | Visible to |
|---|---|---|
| Contact details, Stage 3 identity data | F1 Identity vault | Agency only |
| Bands, flags, interests, preferences | F2 Pseudonymous profile | Agency, AI agents, AA (aggregated only) |
| Health / dietary flags | F1 (with consent), mirrored as flags in F2 | Agency; AI sees flags only |

### Trip view — "Traveler info" panel

```
┌─ Traveler info ──────────────────────────────────────────────┐
│ ✅ Basics (Stage 1)            100%                           │
│ 🟡 Planning info (Stage 2)      60%  missing: fitness, dietary│
│    [Send follow-up form] [Fill in from call]                  │
│ 🔒 Booking details (Stage 3)    locked until deposit paid     │
└───────────────────────────────────────────────────────────────┘
```

Automation:
- Stage 2 under 80% complete creates the task "Get planning info" before a proposal can be sent.
- Stage 3 incomplete 21 days before departure triggers a client nudge and an agent alert.

## 6. Modules

### Foundation

| # | Module | Function | Success |
|---|---|---|---|
| F1 | Identity vault | Traveler personal data, encrypted with the agency's own key | No access outside the agency, AA included |
| F2 | Pseudonymous profile | `traveler_token` + bands, flags, interests, AA trip history | No personal data appears in AA reports or AI context |
| F3 | PII scrubber | Strips personal data from free text before any LLM call; real values are restored in the agency session | Zero personal data leaks in audit; AI drafts restore real values correctly |
| F4 | Tenancy & access | Per-agency isolation; roles: owner / agent / assistant | New user set up in under 5 minutes; permissions enforced |
| F5 | Audit log | Agency-visible log of who or what accessed which fields, and why | Every read is logged; agencies can check it themselves |

### Selling

| # | Module | Function | Success |
|---|---|---|---|
| 1 | Intake form | Embeddable Stage 1 form; auto-creates lead, profile and trip | ≥ 80% of inquiries include a budget band; first reply under 2 hours |
| 2 | Trip pipeline | Board of trips by stage, one timeline per trip, Traveler info panel | No lead goes quiet for more than 3 days unnoticed |
| 3 | Interactive proposal | Per-day option blocks from AA inventory; defaults from Stage 2; dependency rules; live price and availability; keep / swap / request change; no client login | Emails per trip drop from about 8 to 2–3; conversion up; upgrade picked ≥ 20% of the time |
| 4 | Text proposal mode | Same trip data rendered as an email or short WhatsApp message, with a link to the option picker | Under 2 minutes from finished trip to sent; prices always match the visual version |
| 5 | Unified inbox (email) | Two-way Gmail / Outlook sync, threads linked to trip, saved replies, internal notes | Agency stops using Gmail for client work |

### Getting paid & delivering

| # | Module | Function | Success |
|---|---|---|---|
| 6 | Bookings ledger | One line per supplier booking: confirmation number, cost, sell price, commission; AA lines fill themselves | Margin per trip known without a spreadsheet |
| 7 | Invoices & payments | Deposit / balance schedule, Stripe pay links, automatic reminders | ≥ 70% of deposits paid within 48 hours of acceptance; no manual chasing |
| 8 | AA ops release | Traveler details sent to AA only for confirmed departures; deleted automatically 90 days after the trip | Zero ground ops errors; deletion can be verified |
| 12 | Contracts & waivers | E-signature for terms and trekking waiver | 100% signed before departure; accepted by insurer |
| 13 | Commission tracking | Expected vs. received, overdue flags | No unclaimed commission; overdue amounts found within days |

### Automating

| # | Module | Function | Success |
|---|---|---|---|
| 9 | Unified inbox (WhatsApp / SMS) | Twilio / 360dialog; approved templates; 24-hour reply window handled | Agents stop using personal WhatsApp for clients |
| 10 | Workflow automation | Tasks and emails per stage; quiet-client nudges; Stage 2 form auto-send | Nothing forgotten before departure |
| 14 | AI agent layer | Drafts replies, proposals, follow-ups using only F2 / F3 data; approval required | ≥ 60% of drafts sent with light edits; 5+ hours saved per agent per week |

### Client experience & scale

| # | Module | Function | Success |
|---|---|---|---|
| 11 | Client portal | One link: proposal, Stage 3 forms, documents, invoices, itinerary | "Can you resend…" emails near zero |
| 15 | Supplier directory | AA as default plus the agency's own suppliers | Mixed AA / non-AA trips built in-app |
| 16 | Agency reports | Conversion by stage, margin, lead source, option picks | Agency adjusts marketing at least quarterly from this |
| 17 | AA insights | Aggregated demand and willingness-to-pay; groups under 10 suppressed (k ≥ 10) | AA product decisions are traceable to this data |
| 18 | Data portability | Full export (CSV / JSON) and verified deletion | Works on first try; is a reason agencies sign up |

## 7. Core data model

```
Agency 1─* User (role)
Agency 1─* IdentityVault.Traveler (traveler_id, name, email, phone, passport, dob, emergency_contact)
Traveler 1─1 Profile (traveler_token, age_band, country, budget_band, fitness_level, pace,
                      accommodation_tier, interests[], dietary_flags[], mobility_flags[])
Traveler *─* Trip  (via TripTraveler: role = lead | companion)
Trip (stage, dates, proposal_format ∈ {visual, email, text}, intake_completeness{s1,s2,s3})
Trip 1─* Booking (supplier_id, conf_no, cost, sell, commission, status)
Trip 1─1 Proposal (version, builder_itinerary_id)
Proposal 1─* Day 1─* OptionBlock (type: day|activity|lodging|transfer)
OptionBlock 1─* Option (aa_product_id, price_delta, availability, requires[], excludes[])
Proposal 1─* Selection (day, option_id, by: client|agent, at)
Trip 1─* Invoice 1─* Payment
Trip 1─* Task (from WorkflowTemplate)
Trip 1─* Document (passport, waiver, ticket)
Traveler 1─* Conversation (channel ∈ {email, whatsapp, sms, messenger, ig})
Conversation 1─* Message (direction, body, attachments, external_id, status)
AuditEvent (actor: user|ai_agent|aa_ops, agency_id, fields[], reason, at)
```

## 8. Privacy architecture

- **Split stores.** F1 identity (agency key) vs. F2 pseudonymous profile (random token, not derived from identity).
- **Scrub before AI.** All free text passes through `scrub()` (Presidio or equivalent). Placeholders like `<PERSON_1>` are restored only in the agency session.
- **LLM provider:** zero data retention, no training on our data.
- **AA access:** confirmed-departure ops data only (module 8) and aggregates with k ≥ 10 (module 17). Never contact details or non-AA bookings.
- **Agency controls:** agency-held keys, visible audit log, one-click export / delete.

## 9. Integrations

| System | Purpose | Contract needed |
|---|---|---|
| AA inventory API | Products, net rates, availability, hold / confirm | Endpoints, payloads, hold expiry, error / outage behaviour |
| Visual itinerary builder | Proposal rendering and editing | Events: `itinerary.sent`, `itinerary.accepted`, `itinerary.updated`; line-item sync |
| Stripe | Payments | Pay links, webhooks, refunds, multi-currency |
| Gmail / Outlook | Email sync | OAuth scopes, threading, send-as |
| Twilio / 360dialog | WhatsApp / SMS | Template approval, 24-hour window, inbound matching |
| E-sign provider | Terms + waiver | Signed PDF storage, audit trail |
| LLM provider | AI agent layer | Zero data retention terms |

## 10. Build plan

Assumes 2–3 developers in 2-week sprints, about 40 weeks.

| Phase | Weeks | Sprints → modules |
|---|---|---|
| 0 Foundation | 1–6 | S1 F4 · S2 F1 + F2 · S3 F3 + F5 |
| 1 Sell a trip | 7–16 | S4 1 + 2 · S5 6 · S6–S7 3 · S8 4 + 5 |
| 2 Get paid & deliver | 17–22 | S9 7 · S10 8 + 12 · S11 13 |
| 3 Automate | 23–30 | S12 9 · S13 10 · S14–S15 14 |
| 4 Experience & scale | 31–40 | S16 11 · S17 15 · S18 16 · S19 17 · S20 18 |

**Pilot:** 3–5 friendly agencies at the end of Phase 2 (week 22).

**Dependencies:**
- F1–F3 come before any traveler data is stored.
- Start the AA inventory API in parallel with Phase 0.
- Module 3 needs the inventory API and the builder contract.
- Module 14 needs F3, F5, 5 and 9.
- Module 17 needs 3–6 months of real data.

### Non-code track

| Phase | Item |
|---|---|
| 0 | Legal review (Australian Privacy Act, GDPR, Vietnam data protection law); data processing agreement template |
| 1 | Partner agreement with no-poaching clause |
| 2 | Trekking waiver reviewed by AA's insurer |
| 3 | WhatsApp Business verification and template approvals (2–4 weeks) |
| 4 | Public plain-language data page for agencies |

## 11. Open gaps (to write next)

1. User stories with Given / When / Then acceptance criteria per module, starting with **module 3**.
2. Edge cases: option unavailable mid-session, concurrent edits, failed payment, unknown inbound number, AA API down.
3. A day-in-the-life walkthrough: one inquiry followed end to end.
4. Clickable mockups: pipeline, intake form, interactive proposal (agent + client), inbox, trip view.
5. **Onboarding module:** import from Gmail / CSV, first-run setup, team invites.
6. Non-functional requirements: mobile-first scope, languages, currencies (AUD / USD / VND / EUR), time zones, performance, uptime.
7. Event tracking plan so every success metric above can be measured.
8. Pricing model for agencies (free / per seat / commission-linked).
