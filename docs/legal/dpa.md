---
id: SEC-04-dpa-agreement
title: "Data Processing Agreement for partner agencies (draft v0.2)"
description: "The Art. 28 Data Processing Agreement between Adventure Asia (processor) and a partner agency (controller) for the Content studio, the CRM and Booking B2B, with the breach notice timeline, sub-processor rules, transfers and return or deletion at the end; draft for counsel, not legal advice."
type: reference
status: draft
owner: nghiep
audience: [owner, cio, engineer, agent]
applies_to: [ecosystem, aa-partner-portal, aa-crm-api, aa-crm-web, aa-cis-api, aa-booking-api]
last_reviewed: 2026-11-05
review_every_days: 30
related: [SEC-04, SEC-04-dpa-pack, SEC-04-dpa-annex1, SEC-04-dpa-annex2, SEC-04-dpa-annex3, SEC-04-dpa-annex4, SEC-04-pilot-set, SEC-04-ai-schedule, SEC-04-dsar, AA-820]
---

# Data Processing Agreement for partner agencies (draft v0.2)

> [!WARNING]
> **DRAFT FOR COUNSEL. NOT LEGAL ADVICE. NOT APPROVED.** Engineering wrote this text from the product facts on
> `main` on 2026-11-05. Counsel has not read it and no agency has signed it. Every item marked **[COUNSEL]** needs a
> lawyer's answer; whether and when a lawyer reviews the pack is the business owner's decision (ADR 0019 b20, b10).
> `[●]` is a value the business owner or counsel fills in. *Drafting notes* in italics are for the reviewer and are
> not part of the agreement.

| | |
|---|---|
| Version | **Draft v0.2, 2026-11-05** (AA-820 part 2). Replaces the [DPA template v0.1](dpa-template.md) of 2026-10-21, whose clause 1.3 made AA the controller of travellers; ADR 0019 invariant 2 superseded that |
| Decisions | [ADR 0019](../adr/0019-b2b-only-ecosystem-model.md) invariant 2 and b9 (agency = controller, AA = processor, on every app), b10 (contracting entity and counsel before Vietnamese or EU agencies store data), b11 (worldwide from US hosting with SCCs plus a TIA), d12 (US by default, EU cell on triggers), d16 (pilot on Dev with one agency, a pilot letter and this DPA); ADR 0008a (CRM: agency controller, AA processor) |
| Annexes | [Annex 1: processing per app](dpa-annex-1-processing.md) · [Annex 2: security measures](dpa-annex-2-security.md) · [Annex 3: sub-processors](dpa-annex-3-subprocessors.md) · [Annex 4: transfers, SCC fill-ins and TIA](dpa-annex-4-transfers.md) |
| Ships with | The [pilot contract set](pilot-contract-set.md): the partner-terms clauses that incorporate this DPA and the [AI Schedule v1.0](tenant-ai-schedule.md) (Anthropic Usage Policy effective 12 November 2026), the joint-controller clause and the model privacy notice for the agency |
| Pack plan | [DPA pack outline](dpa-pack-outline.md) (items P1-P9) |

## 1. Parties, scope and roles

**1.1 Parties.** This Data Processing Agreement ("**DPA**") is between [●] (the Adventure Asia contracting entity,
"**AA**") and the partner agency named in the partner agreement or the pilot letter (the "**Agency**"). It forms part
of that agreement (the "**Agreement**").

*Drafting note [COUNSEL]: the contracting entity, its country and its licences are open (ADR 0019 b10). The answer
decides which regimes apply to AA itself and which SCC module fits (Annex 4).*

**1.2 Agency Personal Data.** "**Agency Personal Data**" means personal data that the Agency, its users, or its
clients through the Agency's forms and links, put into the Services, or that AA collects on the Agency's behalf
through the Services. Annex 1 describes it per service.

**1.3 Roles.** For Agency Personal Data the Agency is the **controller** and AA is the **processor**, in every service:
the Content studio, the CRM, Booking B2B and, once the Agency takes it, the Trip Planner. AA does not use Agency
Personal Data for its own purposes, does not market to the Agency's clients, and does not copy the Agency's clients
into any AA customer record (ADR 0019 b1 commitment; data standard DM-6.8).

**1.4 What AA controls itself.** AA is an independent controller only for:

- (a) the Agency's account, contract and billing contact data (`shared.tenants` billing fields), and the identities of
  the Agency's users needed to sign them in;
- (b) security, audit and usage records AA keeps to run, secure and bill the Services and to show compliance with the
  Model Provider Policies (AI Schedule clause .8);
- (c) the commercial records of AA tours the Agency books with AA (Booking B2B quotes, holds, bookings, invoices),
  which carry passenger counts and age bands but no traveller identity (DM-6.8).

*Drafting note [COUNSEL]: item (b) is the open question Q8 of the AI Schedule (controller or processor per record
kind). Item (c) treats AA as a supplier to the Agency for its own tours; counsel confirms that role.*

**1.5 Out of scope.** Data AA holds as a controller from before the B2B model (legacy Trip Planner inquiries and
Booking customer records, ADR 0019 invariant 1 "after cut-over") is not Agency Personal Data and is covered by AA's
own privacy notices. Services the Agency connects with its own accounts (mail, messaging, payments, calendars,
websites, social pages) are the Agency's own processors, not AA's sub-processors (ADR 0019 invariant 5; Annex 3 §3).

## 2. Definitions

Terms not defined here have the meaning given in the Agreement, or else in the GDPR (Regulation (EU) 2016/679).
"**Data Protection Law**" means every law on personal data that applies to the processing, which may include the GDPR,
the UK GDPR, Vietnam's personal data protection law and its implementing decree, and the Australian Privacy Act 1988
(APPs) **[COUNSEL: confirm the list per Agency market]**. "**Personal Data Breach**", "**data subject**" and
"**processing**" have their GDPR meaning. "**Model Provider Policies**" and "**Model Provider**" have the meaning in the
AI Schedule clause .1. "**Sub-processor**" means a third party AA engages that processes Agency Personal Data.

## 3. Instructions

**3.1** AA processes Agency Personal Data only on the Agency's documented instructions. The instructions are: the
Agreement; this DPA; and the actions the Agency's users take in the Services (for example sending a message,
publishing a piece, running an export, logging an erasure, granting AA support access). The Agency may give further
written instructions that are consistent with the Agreement.

**3.2** AA may process Agency Personal Data otherwise only where the law requires it; AA then tells the Agency of that
requirement before processing, unless the law forbids it.

**3.3** AA tells the Agency at once if, in AA's opinion, an instruction breaches Data Protection Law. AA does not have
to carry out an instruction that would breach Data Protection Law, the AI Schedule or a Model Provider Policy
(including the Anthropic Usage Policy that takes effect on 12 November 2026), and may suspend the affected processing
until the Agency changes the instruction.

**3.4 AI processing.** The AI Features (AI Schedule clause .1) process Agency Personal Data only as Annex 1 states.
In the CRM, personal data the CRM knows or detects is replaced by placeholders before any model call and restored only
for the Agency's user (Annex 2, M-14). In the Content studio, the Agency puts no personal data of its clients into
brand settings, briefs or content inputs (clause 13.3). AA keeps no prompt or AI output text in its AI call records
(AI Schedule clause .8(a)).

## 4. Confidentiality

AA ensures that every person it authorises to process Agency Personal Data is bound by a duty of confidentiality, by
contract or by law, and sees the data only as far as the task needs (Annex 2, M-9 to M-12).

*Drafting note [COUNSEL]: AA's staff contracts and confidentiality terms are not in this repository. The business
owner confirms they exist and cover contractors and agents.*

## 5. Security

**5.1** AA applies the technical and organisational measures in **Annex 2**. Each measure there is marked **Live** (runs
today, with evidence) or **Planned** (not running yet, with the gate it must pass). AA does not promise a Planned
measure as if it were Live.

**5.2** AA may change a measure if the change does not lower the overall level of protection. AA records material
changes in Annex 2 and tells the Agency of them with the next DPA update.

## 6. Sub-processors

**6.1 General authorisation.** The Agency authorises AA to engage the Sub-processors listed in **Annex 3**, for the
purposes and in the locations stated there.

**6.2 Changes.** AA tells the Agency at least **[30]** days before it adds or replaces a Sub-processor, by e-mail to
the Agency's account contact and on the list page. The Agency may object on reasonable data-protection grounds within
**[15]** days. If the parties cannot resolve the objection, the Agency may end the affected service, with a pro-rata
refund of prepaid fees for it **[COUNSEL]**.

**6.3 Flow-down.** AA imposes on each Sub-processor, by contract, data-protection obligations that give at least the
protection of this DPA, and remains liable to the Agency for the Sub-processor's performance as Data Protection Law
requires.

*Drafting note [COUNSEL]: today no DPA with any vendor has been signed or checked in this repository (register
section (b)). Annex 3 names, per vendor, the terms to check: the AWS terms reached through a reseller, and the direct
Anthropic and OpenAI API terms, including data retention and zero-retention options.*

## 7. Data-subject requests

**7.1** AA tells the Agency without undue delay of any request it receives directly from a data subject about Agency
Personal Data, and does not answer it except to refer the person to the Agency.

**7.2** AA helps the Agency answer requests by the tools in the Services:

| Request | CRM (live) | Content studio | Booking B2B |
|---|---|---|---|
| Log and track | Settings > Data and privacy: the data-request log (kind, channel, received, due date up to 92 days, outcome) | Through AA support **[●]** | Not applicable: no traveller identity |
| Access and portability | One-client export (a sealed ZIP with every row that names the client, its profile, documents up to 25 MiB per export) | On request, by AA staff **[manual, not built as a self-serve tool]** | Not applicable |
| Correction | Edit in the client profile | Edit in the studio | Not applicable |
| Erasure | One-client erasure: dry run first, then delete, verify, receipt (kept signed evidence and accounting exceptions stated) | On request, by AA staff | Not applicable |

**7.3** Where a request cannot be met with these tools, AA helps the Agency within **[10]** business days of the
Agency's written request **[COUNSEL]**.

## 8. Personal Data Breach

**8.1** AA notifies the Agency of a Personal Data Breach affecting Agency Personal Data **without undue delay after
becoming aware of it, and in any case within [24] hours** **[COUNSEL]**. AA's internal incident process sets a shorter
target (see 8.3).

**8.2** The notice gives, as far as AA knows at the time: the nature of the breach, the categories and approximate
numbers of data subjects and records concerned, the likely consequences, the measures taken or proposed, and a
contact point. AA sends what it knows first and the rest in phases, without undue further delay.

**8.3 Timeline.**

| When | AA does | Source of the commitment |
|---|---|---|
| T0: AA becomes aware (an alarm, a report, an audit finding) | Opens a SEV1 incident and contains it first (closes the route, revokes the credential, rolls back) | [Incident response](../ops/incident-response.md), Severity table and first steps |
| T0 + 30 minutes | Tells the business owner | Incident response, Who / SEV1 |
| **T0 + 2 hours (operational target)** | E-mails the affected Agency's owner: what is known, from when, what the Agency sees | Incident response: "Tenants told within 2 h if they are affected"; notice template there |
| **T0 + [24] hours (contractual limit)** | The breach notice of 8.2, with the information known so far | This clause **[COUNSEL]** |
| On each material change, at least every [24] hours while open | An update | Incident response: "then on each change and on resolution" |
| Resolution + [5] business days | A written summary: timeline, cause, data concerned, fix, prevention | Incident response: write-up within 2 working days |

*Drafting note: the controller's own deadline to its authority is the Agency's duty (GDPR Art. 33: 72 hours; the
Vietnamese deadline is reported as 72 hours in the CRM research, `04-economics-compliance-security.md` §4.1, not
checked against the decree). The 24-hour contractual limit leaves the Agency most of its window. A "PDPL branch" for
the incident runbook (controller path for the Agency) is an open AA-820 item (S263 scope add).*

**8.4** AA's notice is not an admission of fault. AA does not notify authorities or data subjects about Agency
Personal Data on the Agency's behalf unless the Agency asks it in writing or the law requires AA to.

## 9. Assistance

AA gives the Agency the information it reasonably needs for data protection impact assessments, prior consultations
with authorities and transfer impact assessments about the Services, taking into account the nature of the processing
and the information available to AA. Annexes 1, 2 and 4 are AA's standing input; further help is at [●] cost
**[COUNSEL]**.

## 10. International transfers

**10.1** AA processes Agency Personal Data in the United States (AWS region us-west-1, northern California) and with
the Sub-processors in Annex 3, in the locations stated there. Each Agency's account carries a data region field that
is `us` by default (ADR 0019 d1, d12). An EU hosting cell is built only on the triggers of d12 (a signed contract that
requires it, enough EU agencies to pay for it, or a legal change that breaks the SCCs plus TIA basis).

**10.2** Where Data Protection Law restricts a transfer, the transfer mechanism in **Annex 4** applies (for example the
EU Standard Contractual Clauses, Module 2, with Annexes 1 to 3 of this DPA as their Annexes I to III). If the
mechanism stops being valid, the parties cooperate in good faith to put another in place, and AA may suspend the
affected processing in the meantime.

**10.3** AA makes no claim that AI processing happens in the EU (ADR 0019 d12).

## 11. Return and deletion at the end

**11.1** When the Agreement or a service ends, the Agency may export its data with the self-serve tools during the
term and for **[30]** days after it (the "**exit window**"). After the exit window, or earlier on the Agency's written
confirmation, AA deletes the Agency Personal Data of that service, and confirms the deletion in writing with a receipt.

**11.2 How each service returns and deletes.**

| Service | Return (export) | Deletion | What stays, and why |
|---|---|---|---|
| **CRM** (live, AA-Partner) | The Agency owner exports the whole agency or one client from Settings > Data and privacy: a ZIP sealed under the Agency's own export key, its SHA-256 shown, downloaded through a single-use link valid 5 minutes; the export expires after 7 days. Offboarding builds its own full export (every table in the export catalogue, personal fields decrypted, internal indexes and secrets left out) before anything is deleted | Offboarding: request with dry-run counts, export, download, typed confirmation, then a **cool-off of 72 hours** during which the owner may cancel; then every row is erased through one database function, the Agency's encryption keys are destroyed (crypto-shredding), a sealed test value must no longer open, and a receipt with a verification block is written. Document and export files are deleted last | The Agency's audit trail (codes and ids, no traveller names) stays: 12 months in the database, and its hourly export in write-once storage up to 7 years in total (on Dev: governance mode only until go-live). Receipts of erasures, exports and data requests stay (ids, codes and counts, no personal data). Offboarding deletes everything else, including the Agency's invoices, payments and signed agreements, so the Agency keeps what its own law requires from the offboarding export **[COUNSEL]**. (On a single-client erasure during the term, invoices and payments stay for the Agency's statutory period and signed agreements until trip end + 3 years (est.); the receipt says so) |
| **Content studio** (live, AA-CIS) | Per item during the term: export of each piece as a full HTML document or an HTML fragment, and the tour rewrite as a DOCX file. A whole-account export is prepared by AA staff on request **[not built as a self-serve tool]** | AA offboards the Agency (reversible), then after a retention window (default 30 days) runs the tenant erasure job: a dry run with counts and a fingerprint, the tech lead's approval of that fingerprint, a database snapshot, the erasure in one transaction with a recount that must find 0, then the files and stored channel credentials outside the database. Tested once on Dev on a synthetic agency (2026-10-23) | The audit log (append-only hash chain) and one "erased" row. AI cost records are kept without the Agency link (they hold no text). Archived cost and usage files hold no personal data (DSAR runbook §4 step 8) |
| **Booking B2B** (live, AA-Booking) | The Agency's own copies are in its CRM (AA lines, invoices from AA) | Not applicable to Agency Personal Data: Booking holds no traveller identity for the Agency (DM-6.8) | AA's commercial and accounting records of the Agency's bookings, for AA's statutory period (AA as controller, 1.4(c)) |

**11.3 Backups.** Deleted data leaves AA's automated database backups when they expire, within **7 days**, and is never
restored into the live Services except in a disaster recovery that covers every app; after such a restore AA erases
the data again before the Services reopen **[COUNSEL]**. A manual snapshot taken for an erasure is deleted once the
erasure is verified. The CRM erasure receipt states a backup purge date of erasure + 30 days, a conservative bound.

*Drafting note: automated backups are 7 days (`backup_retention_period = 7`, AA-CIS-Infra `modules/rds/main.tf`, read
2026-11-05). The 14-day option of ADR 0019 d16 has its cost yes but is not applied; if it is applied, this number
becomes 14.*

## 12. Audits and information

**12.1** AA makes available the information needed to show compliance with this DPA: this DPA and its annexes, the
evidence cited in Annex 2, and summaries of security reviews and restore drills.

**12.2** The Agency, or an independent auditor it mandates under confidentiality, may audit AA's compliance once a
year with **[30]** days' notice, during business hours, at the Agency's cost, and more often after a Personal Data
Breach or where an authority requires it **[COUNSEL]**. AA holds no SOC 2 or ISO 27001 report and will seek one only
when a large or EU agency asks (ADR 0019 b18).

## 13. Agency obligations

**13.1** The Agency has a lawful basis for the personal data it puts into the Services and gives its clients the
notices Data Protection Law requires. A model notice is in the [pilot contract set](pilot-contract-set.md) §4.

**13.2** Health data. The CRM stores health information only as closed-list codes and only while the client's explicit
consent to it stands; the Agency obtains and records that consent (DM-6.1 `health`; the CRM refuses to show health
codes after consent is withdrawn).

**13.3** Content studio. The Agency does not put its clients' personal data into brand settings, briefs, prompts or
content inputs of the Content studio. Those inputs may be sent to the Model Providers in Annex 3 (DM-6.4).

**13.4** The Agency keeps its users' sign-in credentials safe and removes users who leave.

**13.5** The Agency complies with the AI Schedule, including the Model Provider Policies (clause 3.3).

## 14. AA's access to Agency Personal Data

AA staff reach Agency Personal Data only as follows (Annex 2, M-10 to M-12):

- **CRM.** Level 1: a platform console without personal data. Level 2: read-only support that the Agency owner grants
  for 1 to 7 days, with names hidden unless the owner chooses to show them; the owner can end it at any time. Level 3:
  emergency access for a named reason (security incident, data corruption, legal request, owner unreachable, service
  outage), 15 to 60 minutes, without names, with an automatic e-mail to every Agency owner. Every read is written to the
  Agency's own access log.
- **Content studio.** Staff roles reach the Agency's content only through the routes their role allows and only for
  the Agency accounts in their scope; a "view as tenant" session is read-only, time-boxed (5 to 60 minutes), needs a
  reason and is audited.
- **Database.** No personal database logins; humans reach the database only through audited sessions, and the
  administrator credential is break-glass only (DM-8.8, DM-8.9).

## 15. Pilot terms (ADR 0019 d16)

While the Agency is the pilot agency:

1. The Services run in AA's development environment, shared with test data of other apps, with no service level
   (the pilot letter's "test environment, no SLA" wording).
2. The pilot lasts at most 8 weeks, or until AA's production environment exists, whichever comes first. At the end
   AA moves the Agency's data to production with the Agency's agreement, or returns and deletes it under clause 11.
3. **Before any real personal data enters the pilot**, AA puts in place the five pilot safeguards of Annex 2, M-25
   (only the pilot agency may hold real data; agents and maintenance scripts cannot read its personal data; clean-up,
   test and batch jobs skip it; a nightly export of the pilot agency; a one-agency restore drill). AA tells the Agency
   when they are in place. *Drafting note: none of the five is built on 2026-11-05 (S268 CRM security review §4).*
4. A database point-in-time restore resets every app on the shared instance, never one agency. AA does not run one
   without telling the Agency first; per-agency recovery uses the nightly export.

## 16. Term, liability and precedence

**16.1** This DPA runs for as long as AA processes Agency Personal Data, including the exit window.

**16.2** Liability under this DPA is subject to the limits in the Agreement, except where Data Protection Law forbids
a limit **[COUNSEL]**.

**16.3** If this DPA and the Agreement conflict on the processing of personal data, this DPA prevails. If the SCCs
(Annex 4) apply and conflict with this DPA, the SCCs prevail.

**16.4** Governing law and courts: those of the Agreement, except where the SCCs require otherwise **[COUNSEL]**.

## 17. Points for counsel

Each is also marked inline.

| # | Point | Clause |
|---|---|---|
| C1 | Contracting entity, its country and licences; which regimes apply to AA itself (b10) | 1.1, 2 |
| C2 | AA as independent controller for account, security, usage and AI ledgers (AI Schedule Q8) and as supplier for Booking B2B | 1.4 |
| C3 | Sub-processor notice and objection periods; refund on objection | 6.2 |
| C4 | Vendor terms: AWS through a reseller; direct Anthropic and OpenAI APIs (retention, zero-retention, location); Jev | 6.3, Annex 3 |
| C5 | Breach notice limit (24 hours proposed) and update cadence; the Vietnamese controller deadline | 8.1, 8.3 |
| C6 | Data-subject request help period; whole-account Content studio export as a manual step | 7.2, 7.3, 11.2 |
| C7 | Exit window length; retention exceptions (accounting, signed agreements, audit archive seven years) | 11.1, 11.2 |
| C8 | Backup wording after deletion | 11.3 |
| C9 | Audit right scope and cost; no SOC 2 / ISO today | 12.2 |
| C10 | Transfer mechanism per Agency market; SCC options; the Vietnamese cross-border dossier; APP 8 | 10, Annex 4 |
| C11 | Pilot on Dev with real data: is the pilot letter plus this DPA enough (AI Schedule Q16) | 15 |
| C12 | Liability caps and carve-outs; governing law | 16 |
