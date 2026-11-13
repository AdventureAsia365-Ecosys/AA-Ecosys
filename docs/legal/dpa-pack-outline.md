---
id: SEC-04-dpa-pack
title: "B2B contract pack, part 2: DPA pack outline"
description: "Outline only of AA-820 part 2: Art. 28 DPA (agency controller, AA processor) with annexes, SCC Module 2 and a TIA template, sub-processors after d23, the joint-controller clause and the tenant-as-controller privacy text."
type: reference
status: draft
owner: nghiep
audience: [owner, cio, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-09
review_every_days: 30
related: [SEC-04, SEC-04-dpa, SEC-04-ai-schedule, SEC-04-packet, SEC-04-dpa-agreement, SEC-04-pilot-set, AA-820, AA-970]
---

# B2B contract pack, part 2: DPA pack outline

> **Outline only.** Nothing below is clause text. It lists what part 2 of AA-820 must contain, where each fact comes
> from, and what is still open. Drafting happens in S269–S271 and must be finished **before any real pilot PII reaches
> Dev** (ADR 0019 d16). Counsel reviews the pack before the first paying agency (b20). Not legal advice.

**Drafted on 2026-11-05 (S269), draft v0.2; brought to draft v0.3 on 2026-11-06 (S271)** to match what runs on Dev
(pilot safeguards live, 14-day backups, the Anthropic API as the first path of Claude models); **DPA draft v0.4 on
2026-11-09 (S274)** with Annex 1 v0.4, Annex 2 v0.5, Annex 3 v0.4 and Annex 4 v0.4 (route control version 7, the AI
gateway's reply store and quality records, the Trip Planner's per-agency lead routing and traveller sign-in); **DPA
draft v0.5 on 2026-11-13 (S279, AA-1093)** with Annex 3 v0.5 (clause 11: CRM exit window 90 days, other services 30
days, one erasure process with a receipt; the Amazon Bedrock chat models served from the tech lead's AWS account).
Every item below now has text:

| Item | Page |
|---|---|
| P1 | [Data Processing Agreement](dpa.md) (supersedes the [DPA template v0.1](dpa-template.md)) |
| P2 | [Annex 1: processing per app](dpa-annex-1-processing.md) |
| P3 | [Annex 2: technical and organisational measures](dpa-annex-2-security.md) |
| P4 | [Annex 3: sub-processors](dpa-annex-3-subprocessors.md) |
| P5, P6 | [Annex 4: transfers, SCC fill-ins and TIA template](dpa-annex-4-transfers.md); the Vietnamese Article 20 dossier's facts in the [Vietnam transfer dossier](vn-cross-border-transfer-dossier.md) |
| P7, P8, P9 | [Pilot contract set](pilot-contract-set.md) (partner-terms clauses with the AI Schedule and the Anthropic Usage Policy, joint-controller clause, model privacy notice, readiness checks) |

The table below stays as the plan of record for what each item had to cover.

| | |
|---|---|
| Linear | AA-820 part 2 (S265 plan review: "DPA pack S269–S271, before pilot PII"); the DPA and sub-processor part of AA-970 moved here |
| Decisions | ADR 0019 invariant 2 and b9 (agency = controller, AA = processor, on every app; joint-controller clause for embedded collection; agencies show their own cookie notice), b10 and b11 (worldwide from US hosting with SCCs plus a TIA; contracting entity and counsel advice before Vietnamese or EU agencies store data), d12 (residency "US by default, EU cell on triggers"), d16 (pilot on Dev), d23 (frontends leave Vercel) |
| Starting material | [DPA template v0.1](dpa-template.md), [compliance register](register.md) (RoPA and sub-processors), [retention log](retention-log.md), [DSAR and erasure runbook](dsar-erasure-runbook.md), [AI Schedule v1.0](tenant-ai-schedule.md) |

## 1. Pack contents

| # | Document | Purpose | Main inputs | Open points |
|---|---|---|---|---|
| P1 | **Data Processing Agreement (Art. 28 GDPR, plus Vietnam PDPL and Australia APP equivalents)** | The agency is the controller of its end-customer data; AA is the processor on every app (Content, CRM, Trip Planner, Booking B2B) | DPA template v0.1 §1-4; ADR 0019 invariant 2 | Template §1.3 still makes AA the controller of Trip Planner travellers and Booking customers: superseded by ADR 0019 (no AA-owned end-customer record after cut-over). Which regimes apply per agency market (b10, b11) |
| P2 | **DPA Annex 1: description of the processing** | Categories of data subjects and data, purposes, duration, per app | Register (a) RoPA and its `pii:` column inventory | Rows for the pilot tenant's CRM data and Trip Planner leads (`lead.submitted.v1`) |
| P3 | **DPA Annex 2: technical and organisational measures** (moved from AA-970) | Security measures the processor commits to | CRM vault (per-tenant DEKs, blind indexes), FORCE RLS, F3 PII scrubber, audit export to Object Lock, RDS backups (7 days, 14 optional), MFA on the partner pool, d16 pilot safeguards (agent hook, skip lists, nightly per-tenant export) | State only what runs on `main`; PITR restores the whole database, never one tenant (d16 caveat) |
| P4 | **DPA Annex 3: sub-processor list after d23** | Who receives personal data, where, for what | Register (b); AI Use Register "Providers, for the tenant terms" | See §2. Vercel has left the list: d23 landed for every frontend (portal 2026-10-28, staff apps 2026-11-07, Trip Planner 2026-11-08; dates in Annex 3 §4) |
| P5 | **SCC Module 2 (controller to processor)** with the Annex I-III fill-ins | Transfers from EU/EEA agencies to AA in the US (b11) | P2 and P3 reused as SCC Annexes I and II; P4 as Annex III | Docking clause, governing law and courts (counsel); the UK addendum and the Swiss amendments if needed |
| P6 | **Transfer impact assessment (TIA) template** | Evidence that SCCs plus measures hold for US hosting | d12 triggers; P3 measures; AWS and model-provider terms | One filled TIA per destination (US hosting; direct Anthropic and OpenAI APIs); the Vietnam PDPL cross-border transfer dossier (Article 20, S263 scope add) shares the same facts |
| P7 | **Joint-controller clause (Art. 26) for embedded collection** | Where AA's embedded widget or Trip Planner launcher collects data on an agency's site, the arrangement between agency and AA | b9; d10/d11 (traveller as guest, leads into CRM intake) | Which purposes are joint (for example abuse prevention, rate limits) and which are the agency's alone; contact point for data subjects; the agency's own cookie notice (b9) |
| P8 | **Tenant-as-controller privacy text** | The model privacy notice an agency publishes for its own customers, and the change to AA's own pages | Portal privacy §10 "Data about your own customers"; Trip Planner privacy notice | AA's Trip Planner privacy notice becomes a processor notice pointing to the agency's notice; the CRM client portal shows the agency's notice |
| P9 | **Pilot letter attachments** | What the single pilot agency signs (d16) | AI Schedule v1.0 §5 pilot clause; P1-P8 | "Test environment, no SLA" wording and the 8-week limit: business owner |

## 2. Sub-processor list: shape after d23

To be filled from the register when drafting. Each row: provider, service, data categories, location, transfer
mechanism, the app it serves.

| Group | Expected rows (to verify against the register and the AI Use Register at drafting time) |
|---|---|
| Hosting | Amazon Web Services (compute, database, storage, e-mail, CDN and WAF), US region |
| AI | Anthropic (through Amazon Bedrock and directly through the Anthropic API, AA company account); OpenAI (through Amazon Bedrock and directly through the OpenAI API); Amazon and Meta models on Amazon Bedrock; Jev (allowlisted tenants only); which of them ever see personal data (CRM: scrubbed before the call) |
| Maps and data | Mapbox, Geoapify, DataForSEO (no personal data, per the register) |
| Frontend hosting | None outside AWS: every frontend runs on ECS since 2026-11-08 (d23 done); Vercel removed |
| Bring-your-own | Services the agency connects with its own account (mail, payments, messaging) are the agency's processors, not AA's sub-processors (invariant 5) |

## 3. Order of work (S269-S271)

1. P1 and P4 first: they decide what every other annex refers to.
2. P2 and P3 from the register and the code facts.
3. P5 and P6 from P2-P4.
4. P7 and P8 with the R5 Trip Planner design (lead flow and launcher).
5. P9: assemble the pilot set; the business owner settles the letter.

## 4. Not in this pack

- The AI Schedule itself (part 1, [tenant-ai-schedule.md](tenant-ai-schedule.md)).
- Commercial terms (plans, fees, SLA, merchant of record): the partner agreement (b2-b5, b18).
- AA's own staff data and AA-internal processing: AA is the controller; the register covers it.
