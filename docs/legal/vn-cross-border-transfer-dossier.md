---
id: SEC-04-vn-transfer-dossier
title: "Vietnam cross-border transfer dossier (Article 20): engineering facts (draft v0.1)"
description: "The facts AA's systems give for the cross-border personal data transfer impact assessment dossier of Vietnam's personal data protection law (Law 91/2025/QH15 Article 20): what leaves Vietnam, to whom, where, how it is protected, and the questions for counsel before the first real personal data."
type: reference
status: draft
owner: nghiep
audience: [owner, cio, engineer, agent]
applies_to: [ecosystem, aa-crm-api, aa-crm-web, aa-partner-portal, aa-cis-api, aa-cis-worker, aa-booking-api, tripplanner-frontend]
last_reviewed: 2026-11-08
review_every_days: 30
related: [SEC-04-dpa-agreement, SEC-04-dpa-annex1, SEC-04-dpa-annex2, SEC-04-dpa-annex3, SEC-04-dpa-annex4, SEC-04-dpa-pack, SEC-04-pilot-set, OPS-04, AA-820]
---

# Vietnam cross-border transfer dossier (Article 20): engineering facts (draft v0.1)

> [!WARNING]
> **Draft for counsel, not legal advice.** Engineering wrote down where personal data goes and what protects it.
> The reading of the law below comes from the S261 architecture review (the electronic text of Law 91/2025/QH15 and
> the data list of Decree 356/2025/ND-CP, read on 2026-10-31) and the S245 CRM research; it is not checked by a lawyer.
> The official form of the dossier, who files it, when and where are for counsel **[COUNSEL]**. Whether and when
> counsel reviews it is the business owner's decision (ADR 0019 b10, b20).

| | |
|---|---|
| Linear | AA-820 (scope added in session S263: the PDPL incident branch and this dossier) |
| Law | Vietnam's personal data protection law, Law 91/2025/QH15, and Decree 356/2025/ND-CP, both in force since 2026-01-01 |
| Companion pages | [DPA](dpa.md) clause 10 and [Annex 4](dpa-annex-4-transfers.md) (transfers, the TIA template: this page fills its sections A, B and D for Vietnam); [Annex 1](dpa-annex-1-processing.md) (data per app); [Annex 2](dpa-annex-2-security.md) (measures); [Annex 3](dpa-annex-3-subprocessors.md) (recipients); breach notice: [Incident response](../ops/incident-response.md), "Personal data breach" |

## 1. When the dossier is needed

As the S261 review read the law:

- **Article 20:** keeping personal data collected in Vietnam on a system outside Vietnam is a cross-border transfer.
  The party that transfers it prepares a transfer impact assessment dossier and files it **within 60 days of the
  first transfer**; the S245 research adds that it is updated when the transfer changes.
- **Article 38** lets a small business or start-up skip Articles 21, 22 and 33(2) for five years (a micro business is
  exempt from them), unless it offers personal data processing services, processes sensitive data directly or
  processes data of a large number of people. **The exemption does not cover Article 20 (this dossier) or Article 23
  (breach notice).**
- Every AA app stores its data in the United States (AWS us-west-1, [Annex 3](dpa-annex-3-subprocessors.md) §1.1), so
  **the 60 days start with the first real personal data collected in Vietnam**: the client data of a Vietnamese
  agency (the pilot agency, if it is Vietnamese), or AA's own Vietnamese customers in Booking or the Trip Planner.
- **On 2026-11-06 nothing has started:** Dev holds synthetic agencies and test data only; the Dev guard refuses a real
  agency unless it is the one pilot ([Annex 2](dpa-annex-2-security.md) M-25 item 1), and no pilot agency is marked
  yet. Date of the first real Vietnamese personal data: **[●]**; filing deadline: that date + 60 days.

## 2. Who files

| Data | AA's role ([DPA](dpa.md) clause 1) | Proposed filer | Open point **[COUNSEL]** |
|---|---|---|---|
| A Vietnamese agency's client and lead data in the CRM, its Content studio inputs, its Trip Planner leads | Processor for the agency | The agency, as controller, files; AA gives it this page and the annexes (DPA clause 9) | Whether a processor that hosts abroad must file its own dossier as well |
| AA's own records: agency account and billing contacts, AA staff, AA's own Booking and Trip Planner customers held today, AI and usage ledgers, security logs | Controller | AA's contracting entity (DPA C1, [●]) | Which AA entity, and whether AA needs a Vietnamese licence or establishment (ADR 0019 b10) |

## 3. What leaves Vietnam, to whom and where

One row per destination of [Annex 4](dpa-annex-4-transfers.md) §1 that receives personal data. Content studio AI
stages carry no personal data of the agency's clients by rule (DM-6.4, classed `content` by CIS migration 373), so
they appear only for completeness.

| # | Destination and recipient | Data | Apps | Form at the destination | Evidence |
|---|---|---|---|---|---|
| 1 | United States, Amazon Web Services, us-west-1 (AA's infrastructure account) | All stored data of every app: for an agency, the CRM categories of [Annex 1](dpa-annex-1-processing.md) §2, including identity documents and the health codes (sensitive data) | CRM, Content studio, Booking, Trip Planner | CRM personal fields and files encrypted with keys that belong to the agency (AWS KMS); the rest encrypted at rest by the database and storage | Annex 2 M-1 to M-6; Annex 3 §1.1 |
| 2 | United States, Amazon Bedrock in AWS US regions (us-east-1, us-east-2, us-west-1, us-west-2) | CRM reply-draft text after the scrub: placeholders, never identity fields; only for an agency with AI switched on (off by default) | CRM | Scrubbed text; no prompt or output text in the AI call records | Annex 2 M-18, M-20; Annex 3 §1.2 |
| 3 | Amazon Bedrock, any AWS commercial region (`global.` inference profiles) | Content studio inputs; no client personal data by rule | Content studio | Content only | Annex 2 M-19 |
| 4 | Anthropic, PBC (Anthropic API), location **[to confirm]** | Content studio inputs; no client personal data by rule. The first path of every Claude model since 2026-11-05 | Content studio | Content only; no prompt or output text in AA's AI call records | Annex 3 §1.2; [AI Use Register](../architecture/ai-use-register.md) v1.11 |
| 5 | OpenAI (OpenAI API), location **[to confirm]** | Content studio inputs; no client personal data by rule. Answers the scoring and checking stages while Bedrock refuses; writes as a last resort | Content studio | As row 4 | Annex 3 §1.2 |
| 6 | Sentry (Functional Software, Inc.), United States | Error events after scrubbing: no default personal data, no request bodies, cookies or local variables; a residual risk that an error message quotes a value | All apps | Scrubbed events | Annex 2 M-21; Annex 3 §1.3 |

Vercel, Inc. (United States) is no longer a destination: the staff apps left it on 2026-11-07 and the Trip Planner
frontend on 2026-11-08; every frontend now runs on AWS (row 1; [Annex 3](dpa-annex-3-subprocessors.md) §4).

Onward transfers: none beyond the rows above. Services the agency connects with its own account (its mailbox, Twilio,
payment provider, website) are the agency's own processors ([Annex 3](dpa-annex-3-subprocessors.md) §3).

Volume and frequency: continuous (storage); per AI call (rows 2 to 5); per error (row 6). Number of data subjects:
**[●]** per agency at signing (the pilot agency gives its client count).

## 4. How it is protected

From [Annex 2](dpa-annex-2-security.md), Live measures only:

- **Encryption:** CRM personal fields and files with a key per agency, crypto-shredding at offboarding (M-3 to M-5);
  TLS everywhere, the database refuses other connections (M-6).
- **Access:** no public database endpoint, audited sessions only (M-7); row-level isolation per agency in the CRM
  (M-9, M-10); per-agency scoping in the Content studio and Booking B2B, partly in application code (M-9b, M-9c);
  agency users with MFA (M-11); staff roles and tenant scope (M-13); three levels of AA support access, each one in
  the agency's own access log (M-14); agents and maintenance scripts cannot read personal data (M-25 item 2).
- **AI:** scrub before any CRM model call (M-18); no client personal data in Content studio prompts (M-19); no prompt
  or output text in AI call records (M-20).
- **Audit:** append-only CRM audit trail exported to write-once storage (M-23); CloudTrail (M-24).
- **Recovery:** 14-day database backups (M-29) and a nightly one-agency export with a tested restore (M-25 items 4-5).

## 5. Contract and notice

- **Contract:** the [DPA](dpa.md) between the agency and AA; sub-processor terms per [Annex 3](dpa-annex-3-subprocessors.md)
  (none signed or checked yet, DPA C4).
- **Notice to data subjects:** the model privacy notice the agency publishes names the United States as the hosting
  country ([pilot contract set](pilot-contract-set.md) §4). Whether consent, notice or another basis is needed for the
  transfer is **[COUNSEL]**.

## 6. What the dossier is expected to hold

Engineering can supply each item below from this page and the annexes; the decree's official form decides the final
list and wording **[COUNSEL]**.

| Item | Source |
|---|---|
| The transferring party and the recipients, with contacts | §2; Annex 3 |
| What data, about whom, for which purpose | §3; Annex 1 |
| Where it goes and how long it is kept | §3; Annex 1 retention rows |
| How it is protected | §4; Annex 2 |
| Risks of the transfer and how they are reduced | §4; Annex 4 §4 (TIA, sections C and E filled by counsel) |
| Notice or consent of the data subjects | §5 |
| Who to contact at AA | **[●]** (DPA contact, Annex 2 M-35) |

## 7. Questions for counsel

1. Is AA a small business or a micro business under Article 38, and does the CRM lose the exemption because it is a
   processing service for agencies and holds health data (S261 review BO-9)?
2. The current form of the Article 20 dossier and of the Article 23 breach notice, and the channel to file them.
3. For agency data, does the agency alone file, or does AA as the processor hosting abroad file too (§2)?
4. Does a pilot on AA's development environment (ADR 0019 d16) count as a transfer that starts the 60 days?
5. Does AA need a Vietnamese licence or establishment to offer the CRM to Vietnamese agencies (ADR 0019 b10)?

## 8. Keeping it current

The PR that changes a destination of §3 (a new sub-processor in Annex 3, a route change in the AI Use Register, a
new hosting provider, an EU cell) updates this page too. A filed dossier is updated when the transfer changes.
