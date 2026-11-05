---
id: SEC-04-dpa-annex4
title: "DPA Annex 4: international transfers, SCC fill-ins and TIA template (draft v0.2)"
description: "Annex 4 of the partner-agency DPA: transfer basis per agency market, EU SCC Module 2 option choices and Annex I-III cross-references, and a transfer impact assessment template."
type: template
status: draft
owner: nghiep
audience: [owner, cio, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-05
review_every_days: 30
related: [SEC-04-dpa-agreement, SEC-04-dpa-annex1, SEC-04-dpa-annex2, SEC-04-dpa-annex3, SEC-04-dpa-pack, AA-820]
---

# DPA Annex 4: international transfers, SCC fill-ins and TIA template (draft v0.2)

> [!WARNING]
> **Draft for counsel, not legal advice.** The choice of transfer mechanism per market, the SCC options and every
> legal assessment in the TIA are for a lawyer. Engineering filled in only the facts: where the data is, who receives
> it and what protects it. The business owner decides whether and when counsel reviews it (ADR 0019 b10, b20).

## 1. Where the data goes

| Destination | What | Since / source |
|---|---|---|
| United States, AWS us-west-1 | Every app's storage and compute | ADR 0018 d7 as amended by ADR 0019 d12 ("US by default, EU cell on triggers"); [Annex 3](dpa-annex-3-subprocessors.md) §1.1 |
| Any AWS commercial region (cross-region inference) | Content studio inputs only, when a stage uses a Bedrock `global.` profile; never a stage classed `pii` (CIS 373) | Annex 3 §1.2 |
| The Anthropic API and the OpenAI API (location [to confirm]) | Content studio inputs, when the AWS deployment of a model refuses or fails | AI Use Register v1.8; Annex 3 §1.2 |
| Sentry, United States | Scrubbed error events | Annex 3 §1.3 |
| Vercel, United States (`sfo1`) and edge | Staff views and the Trip Planner form in transit, until ADR 0019 d23 completes | Annex 3 §1.3, §4 |

An EU hosting cell exists only after a d12 trigger: (a) a signed contract requires EU hosting; (b) about 3-5 paying EU
agencies pay about 3 times the cell's cost; or (c) a legal change under which SCCs plus a TIA no longer hold.

## 2. Transfer basis per Agency market

The contracting entity is open (ADR 0019 b10). Its location changes the analysis: if AA contracts from outside the
EU, the transfer from an EU Agency to AA is itself a restricted transfer.

| Agency market | Proposed mechanism | Open points **[COUNSEL]** |
|---|---|---|
| EU / EEA | EU Standard Contractual Clauses (Commission Implementing Decision (EU) 2021/914), **Module 2 (controller to processor)**, with Annexes I-III = DPA Annexes 1-3; AA's onward transfers to its US sub-processors under the sub-processors' own terms (Module 3 where needed) | Whether AA needs an EU representative (b10); the options in §3; whether any vendor relies on the EU-US Data Privacy Framework instead (check each vendor's certification, not assumed here) |
| United Kingdom | The UK International Data Transfer Addendum to the EU SCCs | Whether needed for the first agencies |
| Switzerland | The EU SCCs with the Swiss amendments (FDPIC as authority, Swiss law references) | Whether needed |
| Vietnam | A cross-border transfer impact assessment dossier under Vietnam's personal data protection law (the S263 scope add of AA-820 names Article 20); it reuses §1, Annex 1 and Annex 2 | The decree's form, who files (the Agency as controller, AA for its own data), timing; a Vietnamese licence for AA (b10) |
| Australia | APP 8: reasonable steps by contract (this DPA) so that the overseas recipient does not breach the APPs | Whether the Agency's notice must name the US |
| Mainland China | Not offered: Content only, no personal data (ADR 0019 b11) | — |
| Others | This DPA as the contractual basis | Per market, when an agency signs |

## 3. EU SCC Module 2: options and fill-ins

| SCC clause | Choice proposed | Note |
|---|---|---|
| Clause 7 (docking) | Include | Lets an Agency's affiliate join later |
| Clause 9(a) (sub-processors) | **Option 2, general written authorisation**, with notice of **[30]** days | Matches DPA clause 6.2 |
| Clause 11(a) (redress) | Do not include the optional independent dispute body | [COUNSEL] |
| Clause 13 (supervision) | The authority of the Member State where the Agency is established, or of its EU representative | [COUNSEL] |
| Clause 17 (governing law) | Option 1: the law of [●] (an EU Member State that allows third-party beneficiary rights) | [COUNSEL] |
| Clause 18 (forum) | Courts of [●] | [COUNSEL] |
| Annex I.A (parties) | Exporter: the Agency (controller), its contact and DPO if any. Importer: AA [●] (processor), its contact [●] | From the Agreement |
| Annex I.B (description) | [Annex 1](dpa-annex-1-processing.md) sections 1 to 4 (and 5 for an Agency with the Trip Planner) | Special categories: CRM health codes with explicit consent (Annex 1 §2); restrictions = Annex 2 M-3, M-9, M-14, M-18 |
| Annex I.C (authority) | As Clause 13 | |
| Annex II (measures) | [Annex 2](dpa-annex-2-security.md), Live measures only; the Planned ones are not promised | |
| Annex III (sub-processors) | [Annex 3](dpa-annex-3-subprocessors.md) §1 | |

## 4. Transfer impact assessment (TIA) template

Fill one TIA per destination in §1 that receives Agency Personal Data. Engineering fills sections A, B and D; counsel
fills C and E. Store each filled TIA as `docs/legal/tia-<destination>.md` with this page's structure.

### A. The transfer

| Field | Fill in |
|---|---|
| Destination and recipient | (for example "United States, Amazon Web Services, us-west-1") |
| Apps and data | Annex 1 rows that reach it |
| Purpose | |
| Format at the destination | In clear / encrypted with keys the recipient also holds / encrypted with keys only AA can use / pseudonymised |
| Onward transfers | |
| Volume and frequency | |

### B. Facts about access

| Field | Fill in |
|---|---|
| Who at the recipient can read the data | |
| Government access requests AA has received | None to date [●] (AA keeps a log from the first request) |
| The recipient's published transparency data | Link, read date |

### C. Law and practice of the destination (counsel)

| Field | Fill in |
|---|---|
| Laws that allow public authority access (for the US, for example FISA section 702, Executive Order 12333, and the safeguards of Executive Order 14086) | |
| Whether the recipient is in scope of them | |
| Redress available to data subjects | |
| Assessment | |

### D. Supplementary measures (engineering)

Pick the ones that apply from Annex 2 and say what each protects against at this destination:

| Measure | Applies | Effect at this destination |
|---|---|---|
| M-3 / M-4 CRM field and file encryption with a key per agency (AWS KMS) | | Data unreadable without a KMS call that is logged in CloudTrail; note that AWS operates KMS, so this is not a key AWS cannot reach |
| M-5 Crypto-shredding at offboarding | | |
| M-18 Scrub before any CRM model call | | Model providers see placeholders, not identities |
| M-19 No identifying personal data in Content studio prompts; `pii` stages held to US AWS | | |
| M-20 No prompt or output text in AI call records | | |
| M-9 / M-10 Isolation and access control | | |
| M-23 / M-24 Audit trails | | |
| Contractual: notice of access requests, challenge where possible | | |

### E. Conclusion (counsel)

| Field | Fill in |
|---|---|
| Level of protection essentially equivalent? | |
| Conditions or further measures | |
| Reviewed by, date | |
| Next review | On a d12 trigger (c), a new sub-processor at this destination, or [12] months |

### Destinations to assess first

1. United States hosting (AWS us-west-1): every app.
2. Cross-region AI inference (`global.` profiles): Content studio only.
3. The Anthropic API: Content studio (and later the Trip Planner and the CRM).
4. The OpenAI API: Content studio.
5. Sentry (United States) and Vercel (until d23 completes): low-volume, scrubbed or in-transit data.

*Drafting note: the Vietnamese dossier of §2 and the EU TIA share sections A, B and D; write the facts once.*
