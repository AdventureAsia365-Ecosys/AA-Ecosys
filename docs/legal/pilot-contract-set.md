---
id: SEC-04-pilot-set
title: "Pilot contract set: partner-terms clauses, AI and DPA incorporation, joint-controller clause, agency privacy notice"
description: "What the pilot agency signs: clauses that incorporate the DPA and the AI Schedule (Anthropic Usage Policy from 2026-11-12), precedence, joint-controller clause, model privacy notice, readiness checks."
type: reference
status: draft
owner: nghiep
audience: [owner, cio, engineer, agent]
applies_to: [ecosystem, aa-partner-portal, aa-crm-web, tripplanner-frontend]
last_reviewed: 2026-11-09
review_every_days: 30
related: [SEC-04-dpa-agreement, SEC-04-ai-schedule, SEC-04-dpa-pack, SEC-04-dpa-annex1, SEC-04-dpa-annex2, SEC-04-dpa-annex3, SEC-04-dpa-annex4, AA-820]
---

# Pilot contract set: partner-terms clauses, AI and DPA incorporation, joint-controller clause, agency privacy notice

> [!WARNING]
> **Draft for counsel, not legal advice.** Items P7-P9 of the [DPA pack outline](dpa-pack-outline.md). The pilot
> letter itself is the business owner's document (ADR 0019 d16); this page gives the clauses engineering proposes for
> it. **[COUNSEL]** marks what needs a lawyer; whether a lawyer reviews it before the pilot is the business owner's
> call (b20: counsel before the first **paying** agency).

## 1. What the pilot agency receives

| # | Document | Version | State |
|---|---|---|---|
| 1 | Pilot letter: test environment, no service level, at most 8 weeks or until AA's production environment exists, the monthly AI allowance | Business owner's wording | To write; §2 gives its legal clauses |
| 2 | [AI Schedule: acceptable use of AI features](tenant-ai-schedule.md) | **v1.0** (2026-11-03) | Adopted by the tech lead; counsel review pending |
| 3 | [Data Processing Agreement](dpa.md) with [Annex 1](dpa-annex-1-processing.md), [Annex 2](dpa-annex-2-security.md), [Annex 3](dpa-annex-3-subprocessors.md), [Annex 4](dpa-annex-4-transfers.md) | **Draft v0.4** (2026-11-09): Annex 1 v0.4, Annex 2 v0.5, Annex 3 v0.4, Annex 4 v0.4 | Engineering draft, matched to Dev on 2026-11-09 (route control version 7, the AI gateway's reply store and quality records, the Trip Planner's lead routing and traveller sign-in); the tech lead reads it, then counsel. Annex 2 §3 and DPA §17 (C1-C14) list the points for counsel and the business owner |
| 4 | EU SCC Module 2 with the fill-ins of Annex 4 §3 | Only if the pilot agency is in the EU, UK or Switzerland | Not needed for a non-EU pilot **[COUNSEL]** |
| 5 | Model privacy notice for the agency's own clients (§4) | Draft | The agency adapts and publishes it |
| 6 | [Tenant Terms clause](tenant-terms-ai-clause-draft.md): the provider usage policies, prohibited uses and suspension in the main terms | **Draft v0.3** (2026-11-09) | Engineering draft; each sentence maps to AI Schedule v1.0, so it adds no duty. For the partner agreement once its template exists; the pilot letter keeps clause [●].2 below |

## 2. Partner-terms clauses (for the pilot letter, later the partner agreement)

*Drafting note: there is no partner agreement template in this repository yet (commercial terms are b2-b5, b18). These
clauses are written to sit in the pilot letter now and move into the partner agreement unchanged.*

**[●].0 Definitions.** In this letter and the documents attached to it: "**Adventure Asia**" (or "**AA**") means [●]
(the Adventure Asia contracting entity); the "**Agency**" means the partner agency that signs this letter; the
"**Agreement**" means this letter with the documents attached to it (later, the partner agreement); the
"**Services**" means the services Adventure Asia provides to the Agency under the Agreement: the Content studio, the
CRM and Booking B2B, and the Trip Planner once the Agency takes it; the "**Portal**" means the agency app through which
the Agency's users reach the Services. In the AI Schedule, "**Tenant**" means the Agency and "**Personal Data**" has
the meaning of "personal data" in the DPA (clause 2). "**Confidential Information**" has the meaning in clause [●]
of this letter **[COUNSEL: the pilot letter's confidentiality clause]**. Other capitalised terms have the meaning in
the DPA.

**[●].1 Data protection.** The Data Processing Agreement attached to this letter (the "**DPA**") forms part of it. For
Agency Personal Data (as defined in the DPA) the Agency is the controller and Adventure Asia the processor, and the
DPA governs that processing. Adventure Asia's own role for the Agency's account and billing data, the sign-in
identities of the Agency's users and its security and usage records is set out in DPA clause 1.4.

**[●].2 Acceptable use of AI features.** The AI Schedule (v1.0) attached to this letter forms part of it. The Agency
uses the AI features only in line with the AI Schedule and with the usage policies of the AI model providers named
there, as updated from time to time, including the **Anthropic Usage Policy that takes effect on 12 November 2026**
(<https://www.anthropic.com/legal/aup>). That policy applies to the Agency as an end user of a service that
integrates Claude, whether Adventure Asia reaches the model through Amazon Web Services or through Anthropic's own
service. Adventure Asia may suspend AI features or publishing for a breach, as the AI Schedule clause .7 sets out.

**[●].3 Order of precedence.** If the documents conflict: (1) the EU Standard Contractual Clauses, where they apply, on
transfers; (2) the DPA, on personal data; (3) the AI Schedule, on AI features and AI output; (4) this letter (later,
the partner agreement); (5) the online terms of the Services.

**[●].4 Pilot environment.** The pilot runs in Adventure Asia's development environment with no service level, for
at most 8 weeks or until Adventure Asia's production environment exists, whichever comes first. Adventure Asia does
not load the Agency's real client data until it has confirmed in writing that the pilot safeguards of DPA clause 15.3
are in place.

**[●].5 End of the pilot.** At the end of the pilot the Agency chooses to move to the production service (its data
moves with it) or to leave, in which case DPA clause 11 (return and deletion) applies.

### Where the AI clause is wired in

| Surface | What it says | State on 2026-11-05 |
|---|---|---|
| Pilot letter (§2 above, clauses [●].0 and [●].2) | Defines the terms the AI Schedule assumes (Services, Tenant = the Agency, Personal Data); incorporates AI Schedule v1.0 and names the Anthropic Usage Policy effective 12 November 2026 | This draft |
| Partner agreement, main body | The [Tenant Terms clause](tenant-terms-ai-clause-draft.md) (draft v0.3, 2026-11-09): provider policies passed on, prohibited uses, AA's right to suspend AI features, effective 12 November 2026 for the Anthropic update; the Schedule prevails on details | Drafted; no partner agreement template yet **[BUSINESS OWNER]** |
| AI Schedule v1.0 clauses .1-.2 | Defines Model Provider Policies, binds the Agency from the provider's effective date | [tenant-ai-schedule.md](tenant-ai-schedule.md) |
| DPA clause 3.3 | AA need not follow an instruction that breaches the AI Schedule or a Model Provider Policy, "including the Anthropic Usage Policy that takes effect on 12 November 2026" | [dpa.md](dpa.md) |
| Agency app: Content studio `/terms` §3 and CRM `/legal/terms` §1 | Summary of AI Schedule v1.0 with the three policy links | Live since S266 (AA-820 part 1) |
| Trip Planner `/terms` §3 | Names the narration model and links the Anthropic Usage Policy | Live since S266 |

The Anthropic Usage Policy page was read again on 2026-11-05: it shows the effective date "Nov 12, 2026", applies to
"customers accessing Claude through cloud providers and authorized resellers" and to "the end users of products or
services integrating Claude", and says Anthropic may "warn you or throttle, limit, suspend, or terminate your access".
The OpenAI usage policies page refused the fetch again (HTTP 403); it is linked "as updated" and checked by counsel.

## 3. Joint-controller clause for embedded collection (Art. 26 GDPR)

*Drafting note: applies only when an Agency takes the Trip Planner (pilot milestone 2, ADR 0019 d10, d11) or another
AA-hosted surface that collects data on the Agency's page. The CRM intake form is not joint: AA processes it for the
Agency only. Which purposes are joint is the main question for counsel.*

**[●].1 Scope.** When a traveller uses the Trip Planner on the Agency's page, the Agency and Adventure Asia are joint
controllers only for: (a) protecting the service from abuse (rate limits per visitor and per address, bot challenges)
and (b) the security logs those measures produce. For everything else, including the trip the traveller plans, the
narration and the request sent to the Agency, the Agency is the controller and Adventure Asia its processor under the
DPA. **[COUNSEL: confirm the split]**

**[●].2 Responsibilities.**

| Duty | Agency | Adventure Asia |
|---|---|---|
| Privacy notice to the traveller | Publishes it on its page and in the planner, covering both roles (§4 includes the text) | Supplies the text about the joint purposes |
| Cookie notice and consent | Shows its own cookie notice (ADR 0019 b9) | Sets only the cookies the planner needs and lists them for the Agency **[●]** |
| Requests from travellers about the joint purposes | Receives them and forwards those about abuse protection | Answers them within [●] days |
| Security of the joint data | — | Annex 2 measures |
| Breach of the joint data | Notifies its authority if required | Notifies the Agency as in DPA clause 8 |

**[●].3 Contact point.** Travellers may exercise their rights with either party; the Agency is the contact point named
in the notice. The essence of this arrangement is made available to travellers in the notice.

## 4. Model privacy notice for the Agency's own clients

*Drafting note: a model the Agency adapts and publishes under its own name; Adventure Asia is named only as its
service provider. Text in [brackets] is for the Agency to fill. It replaces nothing on AA's own sites today; when the
Trip Planner becomes per-agency, AA's Trip Planner notice changes into a short processor notice that points to the
Agency's notice (an app change in AA-TripPlanner-Web, outside this pack).*

> **How [Agency name] uses your personal data**
>
> **Who we are.** [Agency legal name, address, contact for privacy questions]. We decide how your personal data is
> used for planning and booking your trip.
>
> **What we collect.** Your name and contact details; details of the trips you ask about and book; the people
> travelling with you; passport and other travel-document details when a booking needs them; an emergency contact;
> dietary, medical or mobility needs only if you choose to tell us and agree to us keeping them; our messages with you;
> payments you make to us.
>
> **Why.** To answer your enquiry, plan and book your trip, arrange services with our suppliers, look after you while
> you travel, keep accounts we are required to keep, and [send you offers, only if you agree].
>
> **Our legal basis.** [Contract / steps before a contract; your consent for health information and marketing; legal
> obligations for accounts; legitimate interests for running our business safely.]
>
> **Who helps us.** We use a travel software service provided by Adventure Asia to store our records and send our
> messages. Adventure Asia acts only on our instructions and may not use your data for itself. Its service runs on
> Amazon Web Services in the United States. Some features use AI models; any personal details are removed before text
> is sent to an AI model, and a person on our team reviews every message before we send it. When you book a tour
> operated by Adventure Asia, we share with its operations team only what it needs to run your tour (your name, age
> group, flights, and dietary or mobility needs if you agreed). [Other recipients: our suppliers, payment provider,
> mail and messaging providers.]
>
> **Transfers abroad.** Your data is stored in the United States. [We protect it by the European Commission's standard
> contractual clauses / other basis for your country.]
>
> **How long we keep it.** While we work with you, and then [period]. Accounting records are kept as the law
> requires.
>
> **Your rights.** You can ask to see, correct or delete your data, ask for a copy, or object, by writing to [contact].
> You can complain to [the data protection authority of your country].
>
> **Trip Planner (if offered).** When you use our trip planner, Adventure Asia also uses limited technical data (such as
> your IP address and request counts) with us to protect the service from abuse. [Cookie notice link.]

## 5. Readiness checks before the pilot letter is signed

| # | Check | Owner | State on 2026-11-09 |
|---|---|---|---|
| 1 | The tech lead has read the DPA and its annexes (status `draft` → reviewed) | Tech lead | Pending |
| 2 | Contracting entity and counsel decision (b10, b20) | Business owner | Open |
| 3 | The pilot safeguards of Annex 2 M-25 are built and verified live | Engineering | **Done** (all five on Dev since 2026-11-05, AA-969; restore drill 24 of 24 and 5,206 of 5,206 rows on synthetic agencies). Left: the pilot exception for the pilot agency's CRM account (Annex 2 §2 item 2), and AA's written confirmation to the Agency (clause [●].4) |
| 4 | 14-day database backups applied (Annex 2 M-29) | Engineering | Done: 14 days since the AA-CIS-Infra #694 apply on 2026-11-06 |
| 5 | The Agency's market known, and the transfer mechanism chosen (Annex 4 §2) | Business owner, counsel | Open |
| 6 | Vendor terms checked for AWS (through the reseller), the Anthropic API, the OpenAI API (Annex 3). The two direct APIs now carry most AI calls (Annex 3 §1.2), so this check is no longer only about a fallback | Counsel | Open |
| 7 | Jev allowlist does not include the pilot agency without a DPA / zero-retention agreement | Engineering | Proposal (Annex 3 §1.2) |
| 8 | The monthly AI allowance number in the pilot letter | Business owner | Open (AI Schedule §5) |
| 9 | The quality panel's sample tools skip the pilot agency, or the Agency is told (Annex 2 §2 item 9) | Engineering; the tech lead decides | Open: `scripts/aa729/select_samples.py` and `scripts/aa1048/cli.py` (AA-CIS-App) have no pilot check on `main` (read 2026-11-09) |
| 10 | The quality records of the Content studio (reply store, FactSheets, claim labels, shadow verdicts) have approved windows and deletion jobs, or the pilot letter says they are kept until then (Annex 1 §3; DPA point C14) | Tech lead (windows, DM-7.5); counsel (C14) | Open: all four windows are proposed in DM-7.1, no deletion job yet |
