---
id: SEC-04-ai-schedule
title: "Tenant AI Schedule: acceptable use of AI features (v1.0)"
description: "The AI Schedule attached to every partner agreement: compliance with the model providers' usage policies (Anthropic Usage Policy effective 2026-11-12), prohibited uses, disclosure, publishing duties, safeguards, records; where each part ships, the pilot-letter clause and the questions for counsel."
type: reference
status: active
owner: nghiep
audience: [owner, cio, engineer, agent]
applies_to: [ecosystem, aa-partner-portal, aa-crm-web, tripplanner-frontend]
last_reviewed: 2026-11-03
review_every_days: 30
related: [SEC-04, SEC-04-packet, SEC-04-dpa, SEC-04-dpa-pack, APP-06-ai-register, AA-820]
---

# Tenant AI Schedule: acceptable use of AI features (v1.0)

> **Approved by the tech lead for use in the pilot and in partner agreements (ADR 0019 b20, S265, 03/11/2026).
> Counsel has not reviewed it. Counsel reviews it before the first paying agency (b20).** This text was prepared by
> engineering from the product facts. It is not legal advice. The app pages that summarise it keep the banner
> "Draft — pending legal review" until counsel has read it. Counsel may rewrite it to fit the partner agreement
> (defined terms, numbering, liability, governing law); a rewrite becomes v1.1 and the app pages follow.

| | |
|---|---|
| Linear | AA-820 part 1 (due 11/11/2026, one day before the Anthropic Usage Policy update takes effect). Part 2 (the DPA pack) is outlined in [dpa-pack-outline.md](dpa-pack-outline.md) |
| Decision | ADR 0019 [b20](../adr/0019-b2b-only-ecosystem-model.md) (approve the AI-terms draft now; counsel before the first paying agency), b19 (Anthropic account in the AA company's name, AI included per plan with a soft stop), b9 and d16 (pilot on Dev with one agency, a pilot letter and a DPA) |
| Version | **v1.0, 03/11/2026.** History: v0.1 15/10/2026 (root PRs #72, #74), v0.2 24/10/2026 (root PR #240); the earlier file name was `tenant-terms-ai-clause-draft.md` |
| Provider list | Taken from the [AI Use Register](../architecture/ai-use-register.md) (ADR 0009). A route change that adds a provider updates the register, this page and the app pages together |
| Placeholders | `[●]` = a value the business owner or counsel fills in. *Drafting notes* (in italics) are for the reviewer and are not part of the clause |

## 1. The provider policies, as checked

| Policy | URL | Checked | What was found |
|---|---|---|---|
| Anthropic Usage Policy | <https://www.anthropic.com/legal/aup> | **03/11/2026, live page** (also 14/10 and 24/10/2026) | Effective date "Nov 12, 2026". Scope: it "applies to anyone who submits inputs to Anthropic's products or services", and covers "customers accessing Claude through cloud providers and authorized resellers", "developers and businesses using our API and developer platforms" and "the end users of products or services integrating Claude". So it reaches AA on both paths (Amazon Bedrock **and** the direct Anthropic API under AA's company account, b19) and reaches every tenant as an end user. On AI disclosure: "The disclosure does not need to identify Anthropic, Claude, or the model used." |
| OpenAI Usage Policies | <https://openai.com/policies/usage-policies/> | 03/11/2026: **not verified** (the page answered HTTP 403 to the fetch). A web search result shows a newer effective date on the page; it was not read | Linked as "as updated from time to time". Re-check before counsel review |
| AWS Acceptable Use Policy | <https://aws.amazon.com/aup/> | 03/11/2026, live page | "Last updated" 1 July 2021; it "governs your use of the services offered by Amazon Web Services, Inc. and its affiliates" |

The quotations in §4 come from the Anthropic page as read on 03/11/2026. Counsel should read the live text again before
relying on them.

## 2. Where the Schedule ships

| # | Place | What goes there | Status (03/11/2026) |
|---|---|---|---|
| (a) | Content studio `/terms` §3 (AA-Partner `portal/app/terms/page.tsx`) | The plain-English summary of clauses .2 to .8, with the links to the three provider policies, the statement that the direct API accounts are AA's own company accounts, and "the AI Schedule v1.0 attached to your partner agreement governs" | S266: v1.0 summary, page version Draft v0.4 |
| (b) | CRM `/legal/terms` §1 "AI-generated content" (AA-Partner `web/lib/i18nTerms.ts`, EN and VI) | What the CRM drafts do, the provider policies, the prohibited uses, and the high-risk advice rule for ancillaries (insurance, visas, financing; b6) | S266: v1.0 summary. This meets the earlier gate "the Schedule is part of the agency terms before a real model is switched on for a CRM agency" |
| (c) | Trip Planner `/terms` §3 "Use of AI" (AA-TripPlanner-Web) | Travellers are not tenants, so the Schedule does not bind them. The page names who writes the AI text (Claude through Amazon Bedrock) and links the Anthropic Usage Policy, because travellers are end users of a product that integrates Claude | S266: page version Draft v0.2 |
| (d) | Partner agreement | This Schedule in full (§3), as an attachment accepted when the agency signs | To attach at onboarding |
| (e) | Pilot letter (ADR 0019 d16) | The clause in §5: the Schedule ships with the pilot letter, since no tenant exists to notify | Ready; the business owner settles the letter's wording |
| (f) | CIS admin and other AA staff surfaces | Nothing: staff are not tenants. Only the tenant-facing pages carry the summary | No change |

The app pages carry the same version label, "AI Schedule v1.0", and the same three policy links. A unit test in
AA-Partner checks that the Content studio and CRM pages agree; the Trip Planner test checks its own link.

## 3. The Schedule (v1.0)

*Drafting note: written as a stand-alone schedule so it can be attached to the partner agreement. "Agreement",
"Tenant", "Services", "Portal", "Confidential Information" and "Personal Data" are assumed to be defined in the main
agreement. Counsel aligns these terms.*

### Schedule [●]: Acceptable Use of AI Features

**[●].1 Definitions.** In this Schedule:

- **"AI Features"** means the parts of the Services that use artificial-intelligence or machine-learning models to
  generate, rewrite, translate, summarise, score or review content. They include tour rewrites, social, blog and
  marketing content in the Content studio, AI reply and follow-up drafts in the CRM, and any AI feature AA adds later.
- **"AI Output"** means any content produced, in whole or in part, by the AI Features, including after editing by the
  Tenant.
- **"Model Provider"** means any third party whose AI model is used to provide the AI Features. Today these are:
  Anthropic, PBC (Claude models), reached through Amazon Bedrock (Amazon Web Services) and directly through the
  Anthropic API; OpenAI (OpenAI models), reached through Amazon Bedrock and directly through the OpenAI API; and Amazon
  and Meta models on Amazon Bedrock. AA lists the current Model Providers in the Portal, and may change them by updating
  that list.
- **"AA Provider Accounts"** means the accounts that AA holds **in its own company name** with Amazon Web Services and
  with Model Providers, through which every AI Feature is provided.
- **"Model Provider Policies"** means the acceptable-use and usage policies of the Model Providers and of the cloud
  platform through which they are reached, as updated from time to time. They include the Anthropic Usage Policy
  (<https://www.anthropic.com/legal/aup>), the OpenAI Usage Policies (<https://openai.com/policies/usage-policies/>)
  and the AWS Acceptable Use Policy (<https://aws.amazon.com/aup/>).
- **"Channel"** means any website, social-media page or account, newsletter, marketplace, messaging service or other
  medium on which the Tenant, or AA acting on the Tenant's instruction, publishes or sends AI Output.
- **"Published Content"** means AI Output that has been published, posted, sent or otherwise made available to anyone
  outside the Tenant's organisation, by the Tenant or by AA on the Tenant's instruction.

**[●].2 Model Providers and their policies.**
(a) The Tenant must use the AI Features and AI Output only in compliance with this Schedule, the Model Provider
Policies and applicable law.
(b) The Tenant acknowledges that the Model Provider Policies apply to it as an end user of a service that integrates
the Model Providers' models, whichever path AA uses to reach a model (Amazon Bedrock or a Model Provider's own API).
The Model Provider Policies may change. AA will use reasonable efforts to tell the Tenant of a material change that
affects the Tenant's use; the change applies from the date the Model Provider makes it effective.
(c) Every AI Feature runs on the AA Provider Accounts. The Tenant receives no account, key or credential of a Model
Provider, and must not try to reach a Model Provider through the Services other than through the AI Features. AA is
responsible to the Model Providers for the AA Provider Accounts, including their spending caps.
(d) If this Schedule and a Model Provider Policy conflict, the stricter rule applies.

**[●].3 Prohibited uses.** The Tenant must not use the AI Features or AI Output, and must not publish Published
Content, to:

1. **create fake reviews or testimonials:** customer reviews, ratings, endorsements, quotes or "guest stories" that
   were not given by a real customer about a real experience, or that are presented as independent when they are not;
2. **impersonate or invent people or organisations:** fake personas, sockpuppet accounts, content attributed to a
   named real person who did not write or approve it, or content that claims to come from a customer, journalist,
   guide or other third party when it does not;
3. **run deceptive or inauthentic campaigns:** astroturfing; networks of websites, outlets or accounts that appear
   independent but share a common source; content that misrepresents how widely a view is held; or bots that claim to
   be human;
4. **conceal sponsorship or commercial relationships:** presenting advertising, sponsored or commissioned content as
   independent or editorial, or removing a disclosure the law or a Channel requires;
5. **manipulate search engines or AI systems:** seeding the sources they draw on with content that misrepresents its
   origin, authorship or independence;
6. **send spam:** unsolicited bulk messages, or high-volume or repetitive posting that Channel rules or applicable law
   forbid, or that is designed to get around AA's publishing limits;
7. **publish false or misleading information:** in particular about entry, visa, health, safety or legal
   requirements, prices, availability, inclusions or the Tenant's licences and memberships;
8. **give high-risk advice without a qualified person:** use AI Output to advise or decide about a specific person on
   insurance (including travel insurance, its choice, underwriting or claims), finance, credit, instalments or tax,
   immigration or visas, legal, medical or any other matter the Model Provider Policies classify as high-risk, unless
   a qualified person in the Tenant's organisation has meaningfully reviewed it, with authority to change it, before it
   is delivered, **and** the person receiving it is clearly told that AI was used. General travel information that
   does not apply a rule to a specific person (for example "a visa on arrival is available for many nationalities") is
   not advice under this item;
9. **misuse personal data:** submit personal data to the AI Features except as the Agreement and the Data Processing
   Addendum permit, or use the AI Features to compile or enrich profiles of individuals without their knowledge and
   agreement;
10. **copy without permission:** publish AI Output that reproduces third-party material without permission, or present
    AI-assisted work in a context that requires disclosure of AI use without making that disclosure;
11. **circumvent safeguards:** try to bypass, disable or reverse-engineer AA's content checks, publishing limits,
    personal-data scrubbing or other safeguards; or
12. **use AI agents or automations against these rules:** the Tenant is responsible for any automation it builds or
    runs on the Services (for example through the API) and for what it does, as if the Tenant had done it by hand.

**[●].4 AI-generated content: notice and disclosure.**
(a) *AA's notice.* AA tells the Tenant, wherever the Services show AI Output for review, publication, export or
sending, that the content was generated with AI. The Tenant acknowledges that AI Output can be inaccurate, incomplete
or unsuitable, even after AA's automated checks.
(b) *Tenant's labelling duty.* If applicable law, a Channel's rules or a regulator requires content to be labelled as
AI-generated or AI-assisted, the Tenant adds that label to its Published Content.
(c) *Direct AI interaction.* If the Tenant uses the AI Features to communicate directly with its customers or the
public (for example a chat assistant or automated replies), the Tenant tells them they are interacting with AI rather
than a human, at least at the start of each conversation or permanently in the interface. The disclosure need not name
AA or any Model Provider.
(d) The Tenant must not remove, hide or contradict any AI disclosure that AA shows to end users through the Services.

**[●].5 Tenant responsibility for publication and sending.**
(a) The Tenant is the publisher of all Published Content and is responsible for it, including its accuracy, its
compliance with consumer-protection, advertising, fair-trading and AI-labelling laws, and each Channel's terms.
(b) The Tenant reviews each item of AI Output before it is published or sent. AA publishes an item to a Channel only
when the Tenant instructs it to, in the Portal or through the API, and each such instruction confirms that the Tenant
has reviewed the item. The CRM never sends an AI draft: a person in the Tenant's organisation sends it.
(c) The Tenant is responsible for the Channel accounts and credentials it connects to the Services, and for keeping
its authorisations to publish on those Channels in force.
(d) AA's content checks, limits and notices help the Tenant comply. They do not move responsibility for Published
Content to AA, and AA has no obligation to monitor Published Content.

**[●].6 Safeguards and limits.** AA may, at any time and without liability:
(a) apply automated or human checks to AI Output, and remove, rewrite or hold any part that appears to breach clause
[●].3 (for example, a sentence that reads as a customer testimonial);
(b) set and change limits on the volume or frequency of generation and publication for each Tenant or each Channel,
including a monthly AI allowance for the Tenant's plan. When the allowance is used up, the AI Features pause for the
rest of the month unless AA raises it; no overage is charged unless the Agreement says so; and
(c) decline to generate or publish an item that AA reasonably believes would breach this Schedule, a Model Provider
Policy or applicable law.

**[●].7 Suspension and termination.**
(a) AA may suspend the Tenant's access to the AI Features, to publishing, or to the Services as a whole, with
immediate effect and with notice as soon as reasonably practicable, if AA reasonably believes that: (i) the Tenant has
breached this Schedule or a Model Provider Policy; (ii) the Tenant's use exposes AA or a Model Provider to legal,
regulatory or reputational harm; or (iii) a Model Provider, a Channel operator, a court or a competent authority
requires it.
(b) Where the breach can be remedied and is not serious, AA gives the Tenant [●] days to remedy it before suspending,
unless (a)(iii) applies.
(c) AA may terminate the Agreement or the AI Features for a material or repeated breach of this Schedule under clause
[●] (Termination) of the Agreement.
(d) While the Tenant is suspended, or on a Model Provider's, Channel operator's or authority's request, AA may
unpublish from a connected Channel any Published Content that AA published on the Tenant's instruction and that AA
reasonably believes breaches clause [●].3. The Tenant authorises AA to use the connected Channel credentials for that
purpose.
(e) Suspension does not relieve the Tenant of its payment obligations or of responsibility for Published Content
already live.

**[●].8 Records and cooperation.**
(a) For each use of the AI Features AA records the model and provider, the processing stage, time and cost, and for
each publication or unpublication the item, Channel, external post identifier, status, time, and whether the Tenant or
AA acted. AA does not store the prompts or the AI Output in its AI call records. AA also keeps an audit log of
administrative actions on the Tenant's account.
(b) AA uses these records to operate, secure and bill the Services; to detect and investigate abuse; to show
compliance with the Model Provider Policies; and to deal with disputes and complaints.
(c) AA keeps these records for the periods in its Data Processing Addendum (AI call records: 180 days).
(d) AA may disclose relevant records to a Model Provider, a Channel operator, or a court or competent authority where
the law or the Model Provider Policies require it, or to investigate a suspected breach of this Schedule, and tells
the Tenant where the law allows.
(e) The Tenant cooperates in good faith with any investigation by AA or a Model Provider into suspected misuse.

**[●].9 Changes.** AA may update this Schedule to follow changes in the Model Provider Policies, the law or the AI
Features, by giving [●] days' notice in the Portal or by e-mail. A shorter period applies where a Model Provider or the
law requires it. Continued use of the AI Features after the effective date is acceptance.

**[●].10 No warranty on AI Output.** Except as the Agreement expressly states, AI Output is provided "as is". AA does
not warrant that AI Output is accurate, complete, original or fit for any particular purpose. Clause [●] (Limitation
of liability) of the Agreement applies.

### What changed from v0.2

- **.1 and .2(b)-(c):** the Model Providers are reached through Amazon Bedrock **and** directly through the Anthropic
  API and the OpenAI API, on accounts AA holds in its own company name (b19). The Anthropic Usage Policy covers both
  paths (§1). The tenant gets no provider account or key.
- **.2(b):** a policy change applies from the provider's effective date. v0.2 offered "the later of" that date and AA's
  notice; with no tenant signed before 12/11/2026 there is no gap to cover, so the simpler rule stays.
- **.1, .3(8) and .5(b):** the AI Features include the CRM drafts; the high-risk item now names travel insurance,
  instalments and visas for a specific person (the CRM sells these ancillaries, b6) and takes the policy's exclusion
  for general information (Q12 of v0.2).
- **.3(12):** new, from the policy's agentic-use rule ("Users are responsible for ensuring that agents they build or
  deploy" comply).
- **.6(b):** the monthly AI allowance per plan with a soft stop and no overage (b19).
- **.8(a):** says that prompts and outputs are not kept in the AI call records (ADR 0009 decision 8).
- **.7(a):** "with notice as soon as reasonably practicable" chosen over "without prior notice".

## 4. Clause-to-policy map (for the reviewer)

| Clause | Anthropic Usage Policy (live text, 03/11/2026) | Product control today |
|---|---|---|
| .2 | Scope: "customers accessing Claude through cloud providers and authorized resellers", "developers and businesses using our API and developer platforms", "the end users of products or services integrating Claude" | This Schedule; the app pages link the policies |
| .3(1)-(3) | "Create or operate fake personas, accounts, media outlets, or organizations"; "(e.g., sockpuppets, astroturfing, fake reviews, or bots that claim to be human)" | Authenticity check on T9 pieces; writer instructions forbid invented testimonials; T2 rewrites keep to the source tour |
| .3(4) | "Misrepresent or intentionally conceal the sponsorship of content or messaging intended to influence public opinion" | Independence-claim check on T9; otherwise the Tenant's duty |
| .3(5) | "Manipulate the sources from which search engines or AI systems draw answers" | Tenant's duty plus the authenticity check |
| .3(6) | "Promote or facilitate the generation or distribution of spam" | Daily publish limit per tenant on posts AA publishes |
| .3(7) | Deceptive or misleading information | Writers keep to source facts; the Tenant reviews before publishing; the CRM shows a check reminder under every draft |
| .3(8) | High-risk Areas include Finance, Credit, Insurance and Legal status and adjudication; "A qualified person must meaningfully review a High-risk AI Recommendation"; the recipient "must be clearly told that AI was used to produce it"; exclusions for "General information or educational content" and "Business operations that do not advise or decide about a specific individual" | Not offered as a feature. Recorded as a rule in AA-Partner `CONTEXT.md` (CRM ancillaries) and AA-Booking `CONTEXT.md`; every CRM draft goes through a person |
| .3(9) | "Compile, aggregate, or enrich personal data from multiple sources to build profiles of individuals" without awareness and agreement | No personal data in prompts or AI call records (DM-6.4); the CRM scrubs personal data before any model call |
| .3(10) | "Plagiarize or submit AI-assisted work without proper permission or attribution" | Tenant's duty; see Q1 |
| .3(12) | "Users are responsible for ensuring that agents they build or deploy" comply | API keys per tenant; suspend and offboard |
| .4(c) | Chatbots and agents that talk to external users "must disclose to users that they are interacting with AI rather than a human", at the start of each session or in the product interface; "The disclosure does not need to identify Anthropic, Claude, or the model used" | No tenant chat today; the kit AI notice (ADR 0019 d19, before 02/12/2026) |
| .7 | (Enforcement) | Admin suspend, resume, offboard; force-unpublish of a single post |
| .8 | (Evidence of compliance) | AI call ledger (180 days), publish log, admin audit log |

## 5. Pilot letter: AI clause

Dev has no real tenant today, so nobody is notified of the Schedule. AA-820's "notify existing tenants" becomes:
**the clause ships in the pilot letter** (ADR 0019 d16). The pilot letter is the business owner's document; this is
the text engineering proposes for its AI section. It sits next to the letter's "test environment, no SLA" wording and
the DPA (part 2, [dpa-pack-outline.md](dpa-pack-outline.md)).

> **AI features.** Some tools in the Adventure Asia platform use AI models from third-party providers: Anthropic's
> Claude, OpenAI models, and Amazon and Meta models on Amazon Bedrock. Adventure Asia reaches them through Amazon Web
> Services and, as a fallback, through Anthropic's and OpenAI's own services, always on accounts held in Adventure
> Asia's own company name. Your agency does not need an account with any of them.
>
> By joining the pilot, your agency accepts the **AI Schedule (v1.0)** attached to this letter. In short:
>
> - you follow the providers' usage policies, including the Anthropic Usage Policy that takes effect on
>   12 November 2026;
> - you never use AI content for fake reviews, testimonials, made-up personas, networks of accounts or sites that
>   look independent, hidden sponsorship or spam;
> - you review every AI draft or piece before it is published or sent, and you are responsible for what you publish
>   or send;
> - AI is not used to advise a specific client on insurance, visas, financing or similar matters unless a qualified
>   person in your team checks the advice first and the client is told that AI was used;
> - Adventure Asia keeps records of AI use and publishing, may hold content that breaks these rules, and may pause AI
>   features or publishing for an account that breaches them;
> - AI use is included in the pilot up to a monthly allowance of [●] USD; when it is reached, AI features pause until
>   the next month. Nothing extra is charged.
>
> The Schedule has not yet been reviewed by Adventure Asia's legal counsel. If a reviewed version changes it, we will
> send you the new version before it applies.

*Drafting note: the allowance comes from ADR 0019 b19 (Starter 15, Growth 40, Business 80 USD a month). The pilot
agency's plan, and so the number, is the business owner's call.*

## 6. Product facts the Schedule relies on (03/11/2026)

| Fact | Detail |
|---|---|
| Tenants | **No real or paying tenant.** The Dev tenants are test tenants. The first real one is the single pilot agency of ADR 0019 d16 (at most 8 weeks, or until `aa-prod` exists) |
| Content studio AI | Tour rewrites (T2) and social and blog pieces (T9). Claude through Amazon Bedrock writes; OpenAI models through Amazon Bedrock review and check; Amazon Nova and Meta Llama on Bedrock are fallbacks for checks; the Anthropic API and, as a last resort, the OpenAI API may write when Claude on Bedrock is unavailable, with a spending cap ([AI Use Register](../architecture/ai-use-register.md), CIS migration 344) |
| CRM AI | Reply and follow-up drafts (`crm_draft_reply`), Amazon Bedrock only (ADR 0008a §5-6). Personal data the CRM knows or detects is replaced by placeholders before the model call. A person sends every draft. Off by default per agency, and gated by the plan's `ai_assist` feature |
| Trip Planner AI | Trip narration (`tp_compose`): Claude through Amazon Bedrock, no fallback outside AWS. AI text is labelled on the site |
| Direct API accounts | Held in the AA company's name (b19), monthly cap 150 USD for Anthropic; tenants never get a key |
| Records | AI call ledgers (`shared.llm_call_log`, `crm.llm_call`) without prompt or output text, 180 days; publish log; admin audit log |

## 7. Questions for counsel (before the first paying agency)

The v0.2 questions stay open unless marked. Counsel's answers become v1.1.

1. **Attribution (Q1).** Does content published under the tenant's own name **without an AI label** comply with the
   policy's "origin or attribution" and "AI-assisted work without proper … attribution" items? AA's reading is yes.
2. **Trip Planner disclosure (Q2).** Is the permanent "AI-assisted" label plus the narration badges enough?
3. **Local AI-labelling and advertising law (Q3).** For the tenant markets [●]: EU AI Act Article 50 and its dates
   (ADR 0019 d19 works to 02/12/2026, from secondary sources), EU unfair commercial practices rules, US FTC 16 CFR
   Part 465, Vietnam's AI labelling rules.
4. **Binding (Q4).** Is acceptance with the partner agreement (and the pilot letter) enough, or must the portal record
   a click-through per user (not built)?
5. **Timing (Q5).** *Closed by v1.0:* no tenant signs before 12/11/2026, so a change binds from the provider's date.
6. **Suspension (Q6).** Is suspension with notice "as soon as reasonably practicable" enforceable; cure period [●]?
7. **Unpublishing through tenant credentials (Q7).** Is .7(d) the right basis for the existing force-unpublish tool?
8. **Records (Q8).** Controller or processor per record kind; retention in the DPA only?
9. **Liability (Q9).** Indemnity, cap or carve-out for breaches of .3 and .5?
10. **Governing law (Q10).** Which law and template; renumber and align defined terms.
11. **Providers (Q11).** Does naming the providers in the Portal list suffice, and does tenant content sent to the
    direct Anthropic and OpenAI APIs need their DPA or zero-retention terms (ADR 0001)? Part 2 lists them as
    sub-processors.
12. **High-risk boundary (Q12).** *Answered in v1.0 by the policy's own exclusion* (general information about a rule is
    not advice to a specific person); counsel to confirm.
13. **AA's own site note (Q13, optional).** A brand decision.
14. **Review claims in the tenant's call to action (Q14).** Is the portal warning plus .5 enough?
15. **Direct API accounts (new, b19).** Do the Anthropic and OpenAI commercial terms allow AA to serve tenants as end
    users from AA's company accounts, and does .2(c) pass down every duty they require?
16. **Pilot with real data on Dev (new, d16).** Is the pilot letter (test environment, no SLA) plus the DPA enough to
    run the AI Features on one agency's real data for up to 8 weeks?

## 8. Related rules outside the tenant terms

- **AA-Partner `CONTEXT.md`, "AI boundary for high-risk advice (AA-820)":** the CRM sells non-AA ancillaries
  (insurance, visas, transfers, fees; ADR 0019 b6), so no CRM AI feature may advise a specific client on insurance,
  visas, financing, refunds or claims without a qualified agency member's review and an AI disclosure.
- **AA-Booking `CONTEXT.md`, same heading:** Booking makes no AI calls; the same rule applies if it ever does.
