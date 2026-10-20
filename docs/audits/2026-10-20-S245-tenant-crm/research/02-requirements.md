# Tenant CRM: requirements research (AA-821 / Jira PR-19)

> Raw research note from the S245 workflow (research lane 2), kept as returned. Written before the S245
> "complete product, no MVP" decision; item 7 of §3 ("MVP-first") is superseded by `../README.md`.

Sources were read on 20/10/2026. The task was read-only: nothing was written to Jira, Linear, Notion or any file.

## 1. Sources consulted

| Source | What it holds |
|---|---|
| Jira **PR-19** (https://adventure-asia.atlassian.net/browse/PR-19), created 18/10/2026 by `thule` (Ms. Thư), status Backlog, **0 comments** | The summary line, plus a description that is only a Drive link to `partner-crm-spec.md` |
| Jira search `text ~ "CRM"` | 3 hits: PR-19; **PR-21** (Nghiệp's period-1 platform report, §1 and §5); **KAN-19** (Leigh Wilson, 16/03/2026, an epic on AI that mentions a "partner CRM partner virtual assistant") |
| Linear **AA-821** (Backlog, Low, project "CIS Portal — Admin & Tenant UI") + 4 comments (18/10 and 19/10) | Research questions; Ms. Thư's direction from Zalo on 19/10 |
| Linear **AA-813** (Backlog) | Tenant user accounts with roles `owner` / `editor` / `viewer` |
| `/home/nghiep/projects/AA-Ecosys/docs/research/partner-crm-spec.md` | Copy of the Drive spec linked from PR-19, committed in root PR #97 (145cfa9, 18/10/2026). The repo does not record who wrote it. |
| `docs/sessions/`: S236 (14/10), S237 (15/10), S242 (18/10), S243 (19/10), S244 jira-drafts | Session-log mentions |
| `docs/architecture/data-standards/02-data-management.md` **DM-6.8** (plus DM-6.2 to 6.5) | Data rules for a tenant CRM |
| `docs/audits/2026-10-14-S237-lane-backlog/data-architecture/README.md` §6.4 | A worked data-model sketch for the CRM |
| `docs/adr/0006-ecosystem-identity.md` (Phase 3, lines 139–140 and 400) | Tenant users |
| Notion Program Brain `memory.md` (S242/S243 entries) and `memory_archive_2026H5` (S236) | Only restates the Linear and session-log content |
| Notion "AA_TripPlanner_AI — PRD Canonical v0.3" | A side mention: `trip_draft` is kept as structured JSON "sẵn sàng cho CRM/hệ thống khác đọc sau" ("ready for a CRM or other system to read later") |
| Auto-memory `tenant-crm-idea.md` | S236 note |

## 2. Requirements in Ms. Thư's own words

| # | Quote (verbatim) | English | Date / channel | Source |
|---|---|---|---|---|
| T1 | "Chị đang suy nghĩ build 1 cái CRM, quản lý khách hàng cho tenant." | "I'm thinking of building a CRM to manage customers for tenants." | 14/10/2026 (S236). The channel isn't recorded; it reached us through Nghiệp. | Linear AA-821 description; memory `tenant-crm-idea.md`; session log `docs/sessions/2026-10-14-S236-…md:23` |
| T2 | "CRM cho travel agencies (tenant) dùng với khách hàng của họ, Không phải AA quản lý tenant." | "A CRM for travel agencies (tenants) to use with *their own* customers. Not AA managing tenants." | 18/10/2026, Jira | PR-19 summary |
| T3 | PR-19 description: the Drive link `https://drive.google.com/file/d/1_mZnhtLLt8BdvVWCAaL74EIk8TdJDmDc/view` | She attached the spec as the requirement document | 18/10/2026 | PR-19; repo copy `docs/research/partner-crm-spec.md` |
| T4 | Paraphrase only, no verbatim quote recorded: "The CRM is integrated INSIDE the tenant portal (portal.lumiguides.it.com, AA-885) for tenants to manage their B2C customers. It is not a separate product sold outside the portal." | — | 19/10/2026, Zalo 11:07 | AA-821 comment 62495471 (Nghiệp's transcription) |
| T5 | "Cái CRM em cứ lơ đi cái 40 tuần đi" | "For the CRM, just ignore the 40-week thing." This was her reply to Nghiệp, who had pointed out on 19/10 at 10:22 that the spec's plan is about 40 weeks. | 19/10/2026, Zalo 11:21 | AA-821 comment 17d43815; S243 log line 24 |

Not from Ms. Thư, but relevant: KAN-19 (Leigh Wilson, 16/03/2026) names a "partner CRM partner virtual assistant" as one place where AI could give AA an edge. That loosely supports the spec's AI-agent layer (module 14).

### 2.1 Requirements in the attached spec (`partner-crm-spec.md`)

She attached this spec herself (T3). It is a requirement source, but it is not in her own words, and T5 says to ignore its 40-week plan. How much of its *scope* still stands is an open question (Q1). Short quotes:

- **Purpose:** "A CRM given to Adventure Asia (AA) partner travel agencies to manage **their own customers (B2C)**: inquiry → proposal → booking → payment → trip → follow-up." (§1)
- **Differentiators:** "Live AA supply inside the CRM", "Traveler-configurable proposals", "Privacy by architecture. AI agents and AA never see who a traveler is, only what they want." (§1)
- **Positioning:** "free for partners, and it pays for itself when they sell AA product." (§1)
- **Principles (§2):**
  - "Traveler data belongs to the agency. AA never markets to an agency's travelers."
  - "AI drafts, humans send."
  - "Ask clients only what is needed at each stage."
  - "Every task must be faster than the agency's current Gmail + WhatsApp + spreadsheet routine."
  - "Privacy foundation ships before any feature that stores or reads traveler data."
- **Users (§3):** Agency owner, Agency agent, Agency assistant ("no margin visibility"), Traveler, AA ops ("Confirmed-departure traveler details only"), AA management ("Aggregated, anonymized insights only").
- **Pipeline (§4):** "Inquiry → Qualifying → Proposal → Booked → Pre-departure → Travelling → Completed", with Lost reachable from any stage before Booked. Stage gates include "Stage 2 info ≥ 80% complete, or agent override" and Booked = "Deposit paid".
- **Data collection (§5):** three staged forms (Inquiry under 2 minutes; Qualifying; Booked, which "unlocks only after the deposit is paid"). Rules: bands rather than numbers; health data stored "as flags, never free text"; repeat travellers get pre-filled forms.
- **Modules (§6), 5 foundation + 18 feature modules (23 in total):**
  - Foundation: F1 Identity vault ("encrypted with the agency's own key"), F2 Pseudonymous profile, F3 PII scrubber, F4 Tenancy & access, F5 Audit log.
  - Features: 1 intake form; 2 pipeline; 3 interactive proposal; 4 text proposal; 5 email inbox; 6 bookings ledger; 7 invoices / Stripe; 8 AA ops release ("deleted automatically 90 days after the trip"); 9 WhatsApp/SMS; 10 workflow automation; 11 client portal; 12 e-sign; 13 commission; 14 AI agents; 15 supplier directory; 16 reports; 17 AA insights (k ≥ 10); 18 data portability.
- **Integrations (§9):** AA inventory API, visual itinerary builder, Stripe, Gmail/Outlook, Twilio/360dialog, e-sign provider, an LLM with zero retention.
- **Non-code track (§10):** legal review ("Australian Privacy Act, GDPR, Vietnam data protection law"), DPA template, a partner agreement "with no-poaching clause", waiver review by the insurer.
- **The spec's own open gaps (§11):** user stories, edge cases, onboarding/import, NFRs ("currencies (AUD / USD / VND / EUR)"), and "Pricing model for agencies (free / per seat / commission-linked)".

## 3. Implied requirements (inferred from her statements plus the platform rules already in force)

1. **Tenant-owned data, AA as processor.** T2 ("not AA managing tenants") together with the spec's "Traveler data belongs to the agency" means the tenant is the data controller and AA is the processor. That is already written down as DM-6.8.
2. **It lives in the existing tenant portal** (T4), at portal.lumiguides.it.com (AA-885). So it reuses portal auth and navigation, and tenant identity comes from AA-813 / ADR 0006 Phase 3 (Cognito EXTERNAL). Today a tenant still logs in with one shared API key, and AA-813 is in Backlog. Multi-user access is therefore a hard prerequisite.
3. **Per-user roles inside a tenant.** The spec's owner / agent / assistant (assistant has "no margin visibility") doesn't match AA-813 / ADR 0006's `owner` / `editor` / `viewer`. Either the role model gets extended or the roles have to be mapped.
4. **Strict separation from AA's own customers.** DM-6.8: CRM data lives only in schema `crm` and "MUST NOT be joined with, copied to or read from `booking.customers` / `tripplanner.customers`". This means a tenant CRM **cannot reuse** Booking's customer/lead model. That answers AA-821 research question 3 at the data level. A hand-off to AA only happens through an event with recorded consent (`crm.lead.handoff_requested.v1`), and Booking then creates its own customer.
5. **Isolation must actually be enforced before any traveller data is stored.** This follows from the spec's "Privacy foundation ships before…" and from DM-6.8's caveat that until the CIS role split (X1/AA-817) the runtime "can still read `crm.*`". The CLAUDE.md for 19/10 says the X1 S18/S19 cutover to `cis_app` is done. The `crm` REVOKE and the isolation probe are preconditions of L10 / U-58 that haven't been checked yet.
6. **Privacy and compliance work:**
   - consent with value, timestamp and source (DM-6.5)
   - per-tenant retention, and hard delete on erasure or offboarding (DM-6.8)
   - **a DPA template before the first tenant** (DM-6.8; `docs/guides/cio.md:153`)
   - no contact PII in LLM prompts or `llm_call_log` (DM-6.4), which lines up with the spec's F3 scrubber
   - export / delete (spec module 18; AA-839, the erasure runbook, is parked)
7. **MVP-first, replanned in-house** (T5 plus Nghiệp's reading in the AA-821 comment): "we build on our own plan after research and re-planning (MVP-first, inside the tenant portal for the tenants' B2C customers)". AA-821 is done when a short phased plan has been reviewed and approved by Nghiệp and Ms. Thư.
8. **Lead capture from tenant content.** AA-821 Q1 and the S237 sketch: leads come in from published T9/T11 content and the tenant's website through the tenant's `X-API-Key` on a CIS endpoint, with an idempotency key.
9. **A cost quote before any new AWS service** (DM-10.7, cited in AA-821). A `crm` value already exists for the `App` cost tag (`docs/ops/finops.md:48`).
10. **Product rule from "tenant sees content only":** AA-side QA and diagnostics of the CRM stay in admin (S237 §6.4).

## 4. Users vs data subjects

| | Who | Evidence |
|---|---|---|
| **Users (operators)** | The tenant (a partner travel agency / B2B travel brand on the CIS portal). Spec roles: **agency owner** (full access, margins, reports, team), **agency agent** (leads, trips, proposals, inbox), **agency assistant** (bookings, documents, no margins). Platform roles today, planned in AA-813 / ADR 0006: `owner` / `editor` / `viewer`. | PR-19 summary; spec §3; AA-813; ADR 0006 :139–140 |
| **Secondary users** | **AA ops**: confirmed-departure traveller details only, deleted 90 days after the trip (module 8). **AA management**: aggregates with k ≥ 10 only (module 17). **AA support**: optional read-only `crm_staff` role under an explicit policy (DM-6.8). | spec §3, §8; DM-6.8 |
| **Data subjects** | The **tenant's own B2C travellers**: leads and customers, lead traveller plus companions (`TripTraveler` role lead / companion). Personal data held about them: contact details; passport / date of birth / emergency contact (Stage 3); health and dietary flags with consent; budget and fitness bands; message history. | spec §5, §7 |
| **Travellers as users** | The traveller also touches the system through intake forms, the interactive proposal (no login), the client portal, payments and e-sign. | spec §3, modules 1, 3, 11 |
| **Who they are not** | AA's own B2C customers in `booking.customers` / `tripplanner.customers`. That is a different controller, and "AA sales must never see a tenant's leads" (DM-6.8). The CRM is also not AA managing its tenants (T2). | DM-6.8; PR-19 |

## 5. Open questions to check with 2–3 tenants (and with Ms. Thư)

**For Ms. Thư first**
1. Q1. Does "lơ đi cái 40 tuần" ("ignore the 40 weeks") drop only the timeline, or also the spec's full scope (all 23 modules)? Which modules make up the MVP she expects?
2. Q2. Pricing: the spec says "free for partners", but AA-821 Q6 asks which membership plans include it. Is it free, per seat, or tied to commission?
3. Q3. Is "Live AA supply" (net rates, availability, hold/confirm via an AA inventory API) in scope for the MVP? Whether such an API exists today was **not checked** in this task. `catalog.v_tour` is a content view, not an inventory API.
4. Q4. Who are the real tenants today? The S241 dump showed `shared.tenants` = 4 rows on Dev. Which 2–3 friendly agencies can we interview? The spec plans "3–5 friendly agencies" as pilots.
5. Q5. Jurisdictions of the first tenants (AU / EU / VN)? This drives the DPA and the legal review (spec §10, non-code track).

**For tenants (discovery)**

6. Q6. The current routine: how do they handle inquiries today (Gmail, WhatsApp, Zalo?, spreadsheet, an existing CRM such as HubSpot/Zoho)? How many leads per month, and how many staff? This tests the spec's "faster than Gmail + WhatsApp + spreadsheet" bar and informs build-vs-integrate (AA-821 Q2).
7. Q7. Where do leads come from: the tenant's own site, AA-published content (T9/T11), social, OTAs, phone? Would they put an embeddable intake form on their site?
8. Q8. Which pipeline stages do they actually use? Is the spec's 7-stage pipeline right, or too heavy for the MVP?
9. Q9. Must-have vs nice-to-have:
   - contact list + notes + tasks
   - email sync (Gmail/Outlook)
   - WhatsApp (and is Zalo needed for VN travellers? The spec only lists WhatsApp/SMS/Messenger/IG)
   - proposals
   - invoices / payments
   - e-sign
10. Q10. Do they sell non-AA products in the same trips (spec module 15, supplier directory)? What share is AA product?
11. Q11. How many roles do they need, and do they need margin hiding (spec "assistant")? Does `owner/editor/viewer` cover it?
12. Q12. Will they accept AA hosting their customers' personal data under a DPA? How do they feel about AI drafting replies ("AI drafts, humans send"), and about AA seeing aggregated demand data (k ≥ 10)?
13. Q13. Data portability: do they need to import existing contacts (CSV, Gmail) at onboarding, and to export on exit?
14. Q14. Currencies and languages for their travellers (spec lists AUD / USD / VND / EUR; Booking uses USD + EUR / GBP / AUD / SGD).
15. Q15. Mobile use: do agents work mainly from a phone?

**Unknowns flagged**
- Who wrote `partner-crm-spec.md` is unknown. Ms. Thư attached it, but the repo doesn't record its author.
- Ms. Thư's 19/10 11:07 direction exists only as Nghiệp's paraphrase. No verbatim text is stored.
- PR-19 has no comments and no acceptance criteria beyond the summary and the spec link.
- No tenant interviews or tenant feedback on a CRM appear anywhere in Jira, Linear, Notion or the repo.
