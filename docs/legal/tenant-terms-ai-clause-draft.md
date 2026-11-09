---
id: SEC-04-ai-clause
title: "Tenant Terms clause: AI model providers' usage policies (draft v0.3)"
description: "Short clause for the main tenant terms: the AI providers' usage policies (Anthropic, effective 2026-11-12), prohibited uses and suspension of AI features, mapped to the AI Schedule v1.0."
type: reference
status: draft
owner: nghiep
audience: [owner, cio, engineer, agent]
applies_to: [ecosystem, aa-partner-portal, aa-crm-web]
last_reviewed: 2026-11-09
review_every_days: 30
related: [SEC-04-ai-schedule, SEC-04-pilot-set, SEC-04-dpa-agreement, SEC-04-packet, APP-06-ai-register, AA-820]
---

# Tenant Terms clause: AI model providers' usage policies (draft v0.3)

> [!WARNING]
> **Draft for counsel, not legal advice.** Engineering wrote this clause from the product facts and from the
> [AI Schedule v1.0](tenant-ai-schedule.md), which the tech lead approved for the pilot and for partner agreements
> (ADR 0019 b20). The clause adds **no duty, right or date** that the Schedule does not already contain; it only puts
> the core of the Schedule into the main body of the tenant terms, so that a reader of the terms alone sees it. Counsel
> has not reviewed it. Whether and when counsel reviews it is the business owner's decision (ADR 0019 b20: before the
> first paying agency at the latest). `[●]` is a value the business owner or counsel fills in.

| | |
|---|---|
| Linear | AA-820 scope point 1 (due 2026-11-11, one day before the Anthropic Usage Policy update takes effect) |
| Version | **Draft v0.3, 2026-11-09.** v0.1 (2026-10-15, root PRs #72, #74) and v0.2 (2026-10-24, root PR #240) of this file were a longer draft that became the [AI Schedule v1.0](tenant-ai-schedule.md) on 2026-11-03 (root PR #492); from then until 2026-11-09 this file only pointed there. v0.3 is the short clause for the main terms; the Schedule stays the full text |
| Source of every sentence | AI Schedule v1.0 clauses .1 to .9 (§3 below maps each sentence) |
| Provider policies, as read | The Anthropic Usage Policy page shows the effective date "Nov 12, 2026" and covers "the end users of products or services integrating Claude" (read live on 2026-11-03 and 2026-11-05: [AI Schedule §1](tenant-ai-schedule.md#1-the-provider-policies-as-checked), [pilot contract set §2](pilot-contract-set.md#2-partner-terms-clauses-for-the-pilot-letter-later-the-partner-agreement)). Not re-read for this version; counsel reads the live text before relying on it |

## 1. Where the clause goes

| Place | What carries the clause | State |
|---|---|---|
| Partner agreement (main body) | This clause, as clause [●], with the AI Schedule attached | No partner agreement template exists in this repository yet ([pilot contract set](pilot-contract-set.md) §2, drafting note) **[BUSINESS OWNER]** |
| Pilot letter | Clause [●].2 of the [pilot contract set](pilot-contract-set.md) §2: the same substance in three sentences, with the AI Schedule attached | Ready; the business owner settles the letter's wording |
| Online terms of the agency app: Content studio `/legal/partner-terms` §3, CRM `/legal/terms` §1 (AA-Partner) | A plain-English summary of the AI Schedule with the three policy links and the 12 November 2026 date | Live since S266 ([AI Schedule](tenant-ai-schedule.md) §2 rows (a), (b)). The pages do not need this clause's wording: they already summarise the Schedule it comes from |

There is no real or paying agency on Dev, so no agency is notified of the clause: the first agency receives it with
the pilot letter, before it uses any AI feature ([AI Schedule](tenant-ai-schedule.md) §5, §9 row 3).

## 2. The clause

*Drafting note: "Agreement", "Tenant", "Services", "Portal", "AI Features", "AI Output", "Model Provider" and "Model
Provider Policies" have the meaning in the AI Schedule clause .1 and the partner agreement. Counsel aligns the
numbering.*

**[●] Use of AI features and the AI model providers' usage policies.**

**[●].1 Provider policies passed on.** Some features of the Services use AI models of third-party Model Providers,
which Adventure Asia reaches through Amazon Web Services and through the Model Providers' own services, on accounts
held in Adventure Asia's own company name. The Tenant must use the AI Features and AI Output only in line with the
Model Provider Policies, as updated from time to time, including the **Anthropic Usage Policy that takes effect on
12 November 2026** (<https://www.anthropic.com/legal/aup>), the OpenAI Usage Policies
(<https://openai.com/policies/usage-policies/>) and the AWS Acceptable Use Policy (<https://aws.amazon.com/aup/>).
Those policies apply to the Tenant as an end user of a service that integrates the Model Providers' models, whichever
path Adventure Asia uses to reach a model. Where these terms and a Model Provider Policy differ, the stricter rule
applies.

**[●].2 Prohibited uses.** The Tenant must not use the AI Features or AI Output for any use that a Model Provider
Policy prohibits or that the AI Schedule clause .3 lists, and in particular must not use them to: create fake reviews
or testimonials; impersonate or invent people or organisations; run deceptive or inauthentic campaigns, including
networks of sites or accounts that appear independent; conceal sponsorship; manipulate search engines or AI systems;
send spam; publish false or misleading information about entry, visa, health, safety or legal requirements, prices or
inclusions; advise a specific person on insurance, finance, visas, legal or other high-risk matters unless a qualified
person in the Tenant's organisation has reviewed the advice and the person is told that AI was used; misuse personal
data; get around Adventure Asia's safeguards; or run automations that do any of these.

**[●].3 Review and responsibility.** The Tenant reviews AI Output before it is published or sent, is the publisher
of what it publishes or sends, and is responsible for it.

**[●].4 Suspension of AI features.** Adventure Asia may suspend the Tenant's access to the AI Features, to publishing
or to the Services, with immediate effect and with notice as soon as reasonably practicable, if it reasonably believes
that the Tenant has breached this clause, the AI Schedule or a Model Provider Policy, that the Tenant's use exposes
Adventure Asia or a Model Provider to legal, regulatory or reputational harm, or that a Model Provider, a Channel
operator, a court or a competent authority requires it. The AI Schedule clause .7 sets out the cure period, the
unpublishing of content Adventure Asia published on the Tenant's instruction, and termination for a material or
repeated breach.

**[●].5 Effective date and changes.** This clause applies from the date the Tenant accepts the Agreement. The update of
the Anthropic Usage Policy applies from 12 November 2026, the date Anthropic makes it effective; any later change to a
Model Provider Policy applies from the date its Model Provider makes it effective, and Adventure Asia uses reasonable
efforts to tell the Tenant of a material change that affects the Tenant's use.

**[●].6 The AI Schedule.** The AI Schedule (v1.0) attached to the Agreement forms part of it and sets out the details
of this clause. If this clause and the AI Schedule differ, the AI Schedule prevails.

*Drafting note [COUNSEL]: the order of precedence of the pilot letter ([pilot contract set](pilot-contract-set.md)
§2 clause [●].3) already puts the AI Schedule above the letter on AI features; [●].6 repeats that rule for the
partner agreement. Counsel confirms both.*

## 3. Sentence-by-sentence map

Every sentence of §2 and where it comes from. "Product control" is what the software does today; the clause does not
depend on it, and a missing control is not a promise.

| Clause | Source in AI Schedule v1.0 | Product control today (source) |
|---|---|---|
| .1 providers and company accounts | .1 "Model Provider", "AA Provider Accounts"; .2(c) | Every direct API path runs on a key held in the AA company name; tenants never get a key ([AI Use Register](../architecture/ai-use-register.md), "Providers, for the tenant terms"; ADR 0019 b19) |
| .1 policies passed on, Anthropic Usage Policy from 12 November 2026 | .1 "Model Provider Policies"; .2(a), (b) | The Content studio and CRM terms pages link the three policies ([AI Schedule](tenant-ai-schedule.md) §2 rows (a), (b)) |
| .1 stricter rule applies | .2(d) | — |
| .2 prohibited uses | .3 items 1-12 (shortened; .2 refers to the full list) | Authenticity and independence checks on T9 pieces, writer instructions against invented testimonials, daily publish limit per tenant ([AI Schedule](tenant-ai-schedule.md) §4, rows .3(1)-(6)) |
| .2 high-risk advice | .3 item 8 | No feature gives such advice; the rule is recorded in AA-Partner and AA-Booking `CONTEXT.md` ([AI Schedule](tenant-ai-schedule.md) §8) |
| .3 review and responsibility | .5(a), (b) | AA publishes only on the Tenant's instruction; the CRM never sends an AI draft by itself ([AI Schedule](tenant-ai-schedule.md) .5(b), §4 row .3(7)) |
| .4 suspension | .7(a) | A tenant account can be set to `suspended` with the reason `compliance` (`shared.tenants.account_status`, `suspend_reason`: [db-schema-reference](../architecture/db-schema-reference.md)); AI alone can be stopped for one tenant: a disabled override of `ai.budget_usd_monthly` is served as a 0 USD budget and the AI stages stop (CIS migration 390, `catalog.v_tenant_ai_budget_v1`; the CIS cost guard's fail-closed rule), and the CRM's AI switch is per agency (`crm.tenant_settings.ai_enabled`, default off: [AI Use Register](../architecture/ai-use-register.md), CRM row); force-unpublish of a single post ([AI Schedule](tenant-ai-schedule.md) §4 row .7) |
| .4 cure period, unpublishing, termination | .7(b)-(d) | As above |
| .5 effective date and changes | .2(b), .9 | — |
| .6 the Schedule prevails | Pilot contract set §2 clause [●].3 (order of precedence) | — |

## 4. Open items

| # | Item | Whose |
|---|---|---|
| 1 | Counsel review of this clause and of the AI Schedule before the first paying agency; a rewrite becomes Schedule v1.1 and this clause follows | **[COUNSEL]**, timing **[BUSINESS OWNER]** |
| 2 | The partner agreement template this clause sits in (none exists yet) | **[BUSINESS OWNER]** |
| 3 | Whether acceptance with the agreement is enough or a click-through per user is needed (AI Schedule §7 Q4) | **[COUNSEL]** |
| 4 | Whether suspension "with notice as soon as reasonably practicable" is enforceable, and the cure period `[●]` (AI Schedule §7 Q6) | **[COUNSEL]**, then **[BUSINESS OWNER]** |
| 5 | The OpenAI Usage Policies page could not be read on 2026-11-03 (HTTP 403); it is linked "as updated" (AI Schedule §1) | **[COUNSEL]** reads it |
| 6 | Whether the provider list of the AI Schedule clause .1 should be narrowed: since route control version 7 (CIS 383, 2026-11-06) OpenAI models only score and check, and Meta models serve no AI Feature (AI Schedule .1, drafting note of 2026-11-09) | **[COUNSEL]** (Q11) |
