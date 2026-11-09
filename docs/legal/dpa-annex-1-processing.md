---
id: SEC-04-dpa-annex1
title: "DPA Annex 1: description of the processing per app (draft v0.4)"
description: "Annex 1 of the partner-agency DPA (and SCC Annex I.B): subject matter, purposes, data subjects, data categories, special categories, storage, recipients and retention for the CRM, the Content studio, Booking B2B and the Trip Planner, from the live schema dump and the DM-7.1 retention table."
type: reference
status: draft
owner: nghiep
audience: [owner, cio, engineer, agent]
applies_to: [ecosystem, aa-crm-api, aa-crm-web, aa-partner-portal, aa-cis-api, aa-booking-api]
last_reviewed: 2026-11-09
review_every_days: 30
related: [SEC-04-dpa-agreement, SEC-04-dpa-annex2, SEC-04-dpa-annex3, SEC-04, ARCH-08-data-management, AA-820, AA-900, AA-1038]
---

# DPA Annex 1: description of the processing per app (draft v0.4)

> [!WARNING]
> Draft for counsel, not legal advice. Part of the [Data Processing Agreement](dpa.md). The table and column names
> come from the live schema dump ([`db-schema-reference.md`](../architecture/db-schema-reference.md), Verified
> 2026-11-08 11:46 UTC: CIS 390, TripPlanner tp-027, Booking bk-044, CRM crm-047); retention windows come from the [DM-7.1 retention table](../architecture/data-standards/02-data-management.md#7-retention-and-archival).
> Windows marked "(est.)" are estimates that counsel or the tech lead still confirms. A window marked "proposed" in
> DM-7.1 has no deletion job yet: until the job exists, rows of that table are kept (Annex 2 §0, "Retention").

**What changed in v0.4 (2026-11-09).** The Content studio section (§3) adds the quality records the writing-quality
work created on Dev from 2026-11-06 (CIS migrations 385, 386, 388 and 391): the gateway's store of raw model replies,
the FactSheets, the claim labels and the shadow verdicts, with their purposes, data and proposed windows; and the AI row
follows route control version 7 (CIS 383: no OpenAI writer, no Amazon Nova Lite judge). The Trip Planner section (§5)
adds the optional traveller sign-in by e-mail code and the lead routing per agency that release R5 built (CIS 379, 390;
TripPlanner tp-019, tp-026). §1 no longer says that AA keeps no AI output text at all: the call records keep none,
the reply store does, for a short window. v0.3 was root PR #581 (2026-11-06).

This annex also serves as Annex I.B of the EU Standard Contractual Clauses ([Annex 4](dpa-annex-4-transfers.md)).

## 1. Common to every app

| Item | Description |
|---|---|
| Controller | The Agency |
| Processor | AA (contracting entity [●]) |
| Duration | The term of the Agreement plus the exit window and deletion period of DPA clause 11 |
| Frequency | Continuous |
| Location | AWS region us-west-1 (United States); Sub-processors as in [Annex 3](dpa-annex-3-subprocessors.md) |
| Not done with Agency Personal Data | Marketing by AA; selling or sharing; building AA customer profiles; copying the Agency's clients into AA's Booking or Trip Planner records (DM-6.2, DM-6.8); training AI models (AA does not train or fine-tune models; the AI call records keep no prompt or output text; the reply store and the quality records of §3 are used to replay and measure AA's own checks, not to train a model) |

## 2. CRM (AA-Partner, schema `crm`)

The Agency's client relationship system: leads, clients, trips, proposals, messages, documents, payments it records,
and the operational hand-over of AA tours.

| Item | Description |
|---|---|
| Nature and purposes | Storing and organising the Agency's client and trip records; receiving enquiries from the Agency's forms and forwarded mail; sending messages through the Agency's own mailboxes and messaging accounts; building and sending proposals and collecting acceptances and signatures; recording invoices, payments and commissions; reminders, tasks and workflows; reports for the Agency; AI reply drafts after personal data is replaced by placeholders (off by default, per Agency); exports and erasures on the Agency's request; passing to AA operations the traveller details needed to run an AA tour the Agency booked (the "ops release"); security, audit and support |
| Data subjects | The Agency's clients and leads (travellers); their companions, guardians and related persons; their emergency contacts; people who write to the Agency's forwarded mailbox; contacts of the Agency's own suppliers; the Agency's users |
| Identity and contact data | Names, e-mail, phone, address fields in channel accounts and forms (`crm.traveler` `given_name_enc`, `family_name_enc`, `display_name_enc`, `email_enc`, `phone_enc`; `crm.agency_supplier` contact name and e-mail; `crm.form_submission.payload_enc`) |
| Identity-document data | Date of birth, nationality, passport number, expiry and issuing country, document scans (`crm.traveler` `dob_enc`, `nationality_enc`, `passport_no_enc`, `passport_expiry_enc`, `passport_country_enc`; `crm.document`, files in the documents bucket) |
| Emergency contact | `crm.traveler.emergency_contact_enc` |
| Travel data | Trips, dates, party, flights, destinations, proposals and the day plan (`crm.trip`, `crm.trip_party`, `crm.traveler_flight`, `crm.proposal`, `crm.proposal_day`) |
| Preference profile (pseudonymous) | Budget, pace, fitness, interests, dietary and mobility codes, age band at departure, held apart from identity under a random token (`crm.traveler_profile`, reached through `crm.traveler.profile_token_enc`) |
| Communications | Mail and SMS / WhatsApp messages, their subjects, bodies and addresses (`crm.message` `subject_enc`, `body_enc`, `body_html_enc`, `from_enc`, `to_enc`), notes, saved replies, templates |
| Agreements and payments | Booking-terms acceptances, signatures with the typed name, invoices, payment records with references only (no card numbers), refunds, commissions |
| Online identifiers and credentials | The Agency users' sign-in identity (Cognito issuer and subject); hashed client-link and sign-in codes; the Agency's own vendor credentials, encrypted (`crm.integration_credential.secret_enc`) |
| Audit data | Who viewed, revealed, changed or exported what, with ids and codes only (`crm.audit_event`) |
| **Special categories** | **Health:** dietary, medical and mobility needs as closed-list codes only, stored only with the client's explicit consent and hidden when it is withdrawn (`crm.traveler_health.health_flags_enc`; DM-6.1 `health`). No other special category is intended; free-text notes and messages may contain one if a client writes it **[COUNSEL: Agency instruction for free text]** |
| Storage | Every personal field is encrypted with a key of the Agency's own (Annex 2, M-3); documents are encrypted before storage; mail arriving at the forwarding address is held raw for at most 1 day, then parsed and deleted |
| Recipients inside AA | The CRM service; AA operations staff for the ops release of AA tours (name, age band, dietary and mobility codes while consent stands, flights, the waiver's insurance choice; never phone, e-mail, emergency contact, passport, nationality, date of birth or notes); AA support only with the owner's grant, or emergency access with an owner notice (DPA clause 14) |
| AI | Reply and follow-up drafts on Amazon Bedrock after a three-pass scrub (known values, patterns, Amazon Bedrock Guardrails) replaces personal data with placeholders; the model never sees the identity fields. A person sends every draft. Only for an Agency with the `ai_assist` entitlement and AI switched on (off by default), always after the scrub. On Dev the drafts run on **Amazon Nova Lite** (Amazon Bedrock, AA's infrastructure account) through a `us.` cross-region inference profile, so a call may be served in any of the US regions us-east-1, us-east-2, us-west-1 or us-west-2, never outside the US (AA-CIS-Infra `modules/environment/crm_llm.tf`; root ADR 0009 decision 14 amendment of 2026-11-03, "the CRM draft writer on acc2, Dev only"; CRM task environment read 2026-11-05) |
| Aggregated statistics | AA may compute anonymous statistics across agencies (a cell is shown only with at least 10 travellers from at least 3 agencies and no agency above 70 % of it; no agency id). On the Agency's written request AA sets its opt-out and its trips are left out of every cell (`crm.tenant_entitlement.insights_opt_out`). DPA clause 1.6 governs it **[COUNSEL: confirm this is permitted processing or an AA purpose on anonymised data]** |
| Retention (DM-7.1 `crm` rows) | Clients and their identity data: until the Agency deletes the client or offboards; an archive suggestion after 36 months without trip activity (est.). Trips, messages, proposals, notes, tasks: until the trip is deleted or the Agency offboards. Ops release: trip end + 90 days, then purged with a receipt. Form and inbox payloads: personal data redacted after 90 days. Sign-in codes and placeholder maps: 24 hours. AI draft prompts (scrubbed): cleared after 30 days (est.). AI call records (no text): 180 days. Deleted items: 7 days in the trash. Audit: 12 months in the database, archive up to 7 years. On a single-client erasure: invoices and payments kept for the Agency's statutory period; signed agreements until trip end + 3 years (est.). Offboarding deletes all agency data except the audit and the receipts (DPA clause 11) |

## 3. Content studio (AA-CIS, schemas `shared`, `acp_*`; served in the agency app)

The Agency's marketing content: tour rewrites in the Agency's brand voice, blog and social pieces, and publishing to
the Agency's own website and social pages on its instruction.

| Item | Description |
|---|---|
| Nature and purposes | Storing brand settings and content; AI generation, scoring and checking of content; publishing to the Agency's channels and unpublishing on its instruction; exports; usage metering and billing; support and moderation; security and audit; measuring and improving the quality of the AI checks that hold or pass the Agency's content (replaying a model reply at no cost, comparing a new check with the live one, labelling claims for calibration) **[COUNSEL: whether this last purpose is processing on the Agency's instruction, as part of the service AA provides to every agency, or an AA purpose that needs its own basis or the Agency's consent (DPA clause 1.3)]** |
| Data subjects | The Agency's users; people the Agency names in its own brand settings, briefs or content (for example a guide named in a blog post) |
| Personal data | Users: Cognito issuer and subject (`shared.tenant_members`), membership changes (`shared.tenant_membership_event`); account and billing contact of the Agency (`shared.tenants` `legal_entity_name`, `tax_id`, `billing_email`, `billing_address`; AA as controller, DPA 1.4(a)); free text in add-on requests (`shared.tenant_addon_request.note`); whatever the Agency types into brand settings, briefs and content; edits and labels the Agency makes, which feed its own writing rules (`shared.writing_signal`, `shared.writing_rule`); channel credentials for its website and social pages, stored in AWS Secrets Manager and `shared.tenant_integrations`; publish and audit records naming the Agency account or an AA staff member (`acp_shared.audit_log`) |
| Special categories | None intended. The Agency must not put its clients' personal data into Content studio inputs (DPA clause 13.3) |
| AI | Content inputs (brand settings, briefs, tour text, the Agency's text) are sent to the AI models of [Annex 3](dpa-annex-3-subprocessors.md) §1.2: Claude on the Anthropic API first and on Amazon Bedrock second (a live gateway setting since 2026-11-05); OpenAI models on Amazon Bedrock and then the OpenAI API for scoring and checking (while Bedrock refuses, the OpenAI API answers them); Amazon Nova Lite on Bedrock only as the fallback of the two FAQ checks, which are off by default. Since route control version 7 (CIS 383, 2026-11-06) no OpenAI model writes and no Nova model judges. Every Content studio stage is classed `content`, not `pii` (CIS migration 373), because it receives no personal data of the Agency's clients by rule (DM-6.4) |
| Quality records (since 2026-11-06) | **Reply store** `shared.llm_cassette` (CIS 385): the raw reply of every model attempt the CIS AI gateway receives, at most 256 KiB, with the request and system-prompt hashes (never the prompt text), the model, the provider and links to the job, the Agency and the piece; written by the gateway only (switch `LLM_CASSETTE`, default `record`: AA-CIS-App `shared/llm_client/cassette.py`), no text kept for a stage classed `pii`. **FactSheets** `acp_shared.fact_sheet` (CIS 386): the typed facts a writer and its checks read, including the Agency's own facts, brand and audience lines. **Claim labels** `shared.eval_claim_label` (CIS 388): claims quoted from the Agency's pieces with a judgement and a reason, made by AA's review panel or the tech lead. **Shadow verdicts** `shared.claim_shadow_verdict` (CIS 391): a second check's verdict next to the live one, with spans and hashes only, no text. All four: never read by an Agency route, deleted with the Agency by the tenant erasure job (AA-CIS-App `services/erasure/inventory.py`). The reply store, the FactSheets and the shadow verdicts are never exported. Claim labels are: AA's claim-label tool (AA-CIS-App `scripts/aa1048/cli.py`, commands `finals` and `payload`) writes them with the quoted claim text to a file in AA's git-ignored scratch folder, for the panel and the calibration of the checks, and the panel reads that text in AA's engineering sessions with AI agents **[open item, tech lead: neither the sample selection nor this export skips the pilot agency yet; Annex 2 §2 item 9, pilot contract set check 9]** |
| Recipients inside AA | AA staff in roles that may read tenant content (content lead, tenant QA, AI operations, admin), each view through role-scoped routes; customer success only for the agencies assigned to it, support for those and the unassigned pool (Annex 2 M-13); read-only "view as tenant" sessions, audited (DPA clause 14) |
| Retention | While the account is active. AI call records: 180 days, no text. Tenant writing rules and edits: while the account is active, deleted with it. Quality records (DM-7.1, all **proposed**, no deletion job yet, the tech lead approves each window before production): reply store 30 days; FactSheets while a stored version or piece names them, then 90 days; claim labels while their label set is in use, a superseded set 12 months; shadow verdicts 180 days. Audit log: kept (window to be set before production). After offboarding: the tenant erasure job of DPA clause 11 |

## 4. Booking B2B (AA-Booking, schema `booking`)

AA's own back office for AA tours that the Agency quotes, holds and books with AA through the CRM (and, once built,
the Content studio's "Book with AA" form, ADR 0019 d17).

| Item | Description |
|---|---|
| Role | For the Agency's bookings of AA tours, AA acts as a supplier to the Agency and keeps its commercial records as a controller (DPA clause 1.4(c)) **[COUNSEL]**. No Agency Personal Data about travellers is processed here |
| Data kept | The Agency as a B2B partner (`booking.b2b_partners`: agency name, status, billing currency, credit terms reference, machine client id); quotes, holds and bookings with passenger counts, age bands, rooms, dates and the Agency's proposal reference (`booking.b2b_quotes`, `b2b_holds`, `b2b_hold_lines`, B2B `trip_cases` with `customer_id` empty); cancellations and fees; AA invoices to the Agency |
| What never reaches Booking | Traveller names, contact details, dates of birth or passport data: the B2B contract `booking.b2b.v1` has no field for them, and CI fails a contract sample that carries personal fields (DM-6.8) |
| Traveller details for running an AA tour | Stay in the CRM as the encrypted ops release and are read by AA operations inside the CRM, every view written to the Agency's audit trail (section 2) |
| Retention | AA's statutory accounting period for invoices and bookings **[COUNSEL]**; no window is set yet in DM-7.1 for these tables |

## 5. Trip Planner (AA-TripPlanner-Web, schema `tripplanner`): from pilot milestone 2

The Trip Planner becomes a per-agency service in release R5 (ADR 0019 d10, d11). On 2026-11-09 the per-agency site
settings (CIS 379) and the lead routing and AI budget per agency (CIS 390, TripPlanner tp-026) are built on Dev; CIS
379 seeds AA's own demo tenant (`aa-tripplanner`) for the planner, and no real agency exists on Dev (whether a Dev test
tenant holds a Trip Planner subscription was not checked live for this page). Until an Agency takes it, it is AA's own
site, AA is its controller, and it is **not** part of this DPA. When an Agency takes it:

| Item | Description |
|---|---|
| Nature and purposes | A trip planner on the Agency's page (`/{agency slug}` plus a launcher button on the Agency's site; site settings in `shared.tenant_tripplanner_site`, read through `catalog.v_tenant_tripplanner_v1`, CIS 379); AI narration of the traveller's plan, counted against the Agency's monthly AI budget (`catalog.v_tenant_ai_budget_v1`, CIS 390); sending the traveller's request to the Agency as a lead (`lead.submitted.v1`): into the CRM intake when the Agency has the CRM, otherwise a signed webhook to the Agency's URL or one e-mail through Amazon SES to the Agency's address, with the traveller as Reply-To (CIS 390 `lead_channel`; AA-TripPlanner-Web `backend/assembly/leads.py`). With no channel set, the planner refuses the request and stores nothing |
| Data subjects | Travellers who use the planner: guests, and travellers who choose to sign in by e-mail code to keep their trips (My Trips) |
| Personal data | Name, e-mail and phone given when they submit, with their contact consent; the trip plan and dates; free text they write into the plan; a guest cookie stored as a hash; IP-based rate-limit counters (`tripplanner.ai_rate_counter` holds a keyed hash, a window and a count); for a signed-in traveller, the sign-in identity (`tripplanner.traveller_accounts` `iss`, `sub`; tp-019) and the link of their sessions to it, the e-mail address held in the Amazon Cognito pool, not in this table |
| AI | Trip narration on Amazon Bedrock (Claude); traveller free text may be in the prompt without an identifier (DM-6.4; no automated scrub yet, AI Use Register `tp_compose`) |
| Joint collection | Abuse prevention and rate limits on the planner may make AA a joint controller with the Agency for that purpose only: see the joint-controller clause in the [pilot contract set](pilot-contract-set.md) §3 |
| Retention | Lead payload (DM-7.1 `tripplanner.outbox`, tp-026): redacted on delivery (the CRM's acknowledgement, a 2xx webhook answer or a sent e-mail) and at the latest 7 days after it was written when it could not be delivered; other outbox payloads redacted after 90 days (DM-6.6). Rate-limit counters: 2 days (proposed). Traveller accounts: while the account is active, erased on account deletion (proposed, L3). Other windows proposed in L3 |

*Drafting note: this section is written now so that counsel reads the whole set once. It is attached to an Agency's
DPA only when that Agency takes the Trip Planner.*
