---
id: SEC-04-dpa-annex3
title: "DPA Annex 3: sub-processors (draft v0.5)"
description: "Annex 3 of the partner-agency DPA (SCC Annex III): every third party that may receive agency personal data, with data, apps and location, from the live AI gateway and AWS; plus non-sub-processors and the Vercel exit (completed 2026-11-08)."
type: reference
status: draft
owner: nghiep
audience: [owner, cio, engineer, agent]
applies_to: [ecosystem, aa-crm-api, aa-crm-web, aa-partner-portal, aa-cis-api, aa-cis-worker, aa-booking-api]
last_reviewed: 2026-11-13
review_every_days: 30
related: [SEC-04-dpa-agreement, SEC-04-dpa-annex1, SEC-04-dpa-annex4, SEC-04, APP-06-ai-register, ARCH-01-ai-gateway, AA-820, AA-1042, AA-1038, AA-900, AA-1095, AA-1093]
---

# DPA Annex 3: sub-processors (draft v0.5)

> [!WARNING]
> Draft for counsel, not legal advice. Part of the [Data Processing Agreement](dpa.md); also Annex III of the SCCs
> ([Annex 4](dpa-annex-4-transfers.md)). **No data processing agreement with any vendor below has been signed or checked
> in this repository** (register section (b)); the "Vendor terms to check" column is the to-do list for that **[COUNSEL]**.

**Sources, read on 2026-11-05, AI rows re-read on 2026-11-09 and 2026-11-13** (the 2026-11-13 pass: [ADR 0001a](../adr/0001a-retire-acc1-llm-on-acc3-only.md) Notes S278 and S279 and the [S278 session log](../sessions/2026-11-12-S278-pricing-tools-prepii-e2e-bedrock-acc1.md), route control versions 10 and 11). AI providers: the
[AI Use Register](../architecture/ai-use-register.md) v1.13, "Providers, for the tenant terms" (routes after CIS
migrations 366, 373, 376 and 383), the [AI gateway](../architecture/ai-gateway.md) §4.1 (route control), AA-CIS-App
migration `383_llm_w0_remove_uncalibrated_rungs.sql` (route control version 7, applied on Dev on 2026-11-06 with CIS
381-385: [S271 session log](../sessions/2026-11-06-S271-pilot-gate-tags-writing-quality-w0-guards.md)) and the gateway
state of the S269 and S270 close snapshots (`docs/audits/2026-11-05-S269-close/`,
`docs/audits/2026-11-06-S270-close/`); the CRM draft model from AA-CIS-Infra `modules/environment/crm_llm.tf` and the
live CRM task environment. Hosting: AA-CIS-Infra `main`. Other
vendors: the [compliance register](register.md) section (b) and the vendor rows of the
[secrets register](../security/secrets-register.md) (re-read 2026-11-09). Sentry region: read from the Sentry
organisation (`us.sentry.io`) on 2026-11-05.

**What changed in v0.5 (2026-11-13).** The AI rows follow what serves the models today ([ADR 0001a](../adr/0001a-retire-acc1-llm-on-acc3-only.md),
Note S278 of 2026-11-12 and Note S279 of 2026-11-13, AA-1095): AWS still refuses the main models on AA's AI account,
so **Amazon Bedrock now serves the chat models from a second AWS account held by the tech lead** (the account that pays
the AI account's bill), as a billing-only exception that holds one role allowed to call the models and nothing else:
no data, no secret, no compute. AA's AI account stays configured behind it. Route control versions 10 and 11 set the
order per model family: Claude models on the Anthropic API first, then Amazon Bedrock (the tech lead's account, then
AA's AI account); GPT models on Amazon Bedrock first (same order), then the OpenAI API. No sub-processor was added or
removed: Amazon Web Services, Anthropic and OpenAI were already listed; what changed is the AWS account and the order
(§1.2). Point C4 of the DPA (vendor terms) now also covers the account holder **[COUNSEL]**.

**What changed in v0.4 (2026-11-09).** Route control version 7 (CIS 383, 2026-11-06) took the OpenAI API off every
writer route and Amazon Nova Lite off every judge route, so the OpenAI row no longer says "last-resort writer" and the
Amazon Bedrock row says where Nova and Llama still run (§1.2). Amazon Cognito and SES name what they do for the Trip
Planner (traveller sign-in by e-mail code, lead e-mails to an agency). The company mail row names the second vendor in
the secrets register (Zoho) next to DreamHost (§1.3). DataForSEO's row says which tenant settings shape its queries
(§2). No sub-processor was added or removed. The gateway's reply store (CIS 385) is AA's own storage on AWS, not a
vendor: [Annex 1](dpa-annex-1-processing.md) §3 describes it.

**Who the vendor serves.** CRM = AA-Partner CRM; Studio = the Content studio (AA-CIS behind the agency app);
Booking = Booking B2B; TP = the Trip Planner (only for an Agency that takes it, pilot milestone 2). "Agency data"
means Agency Personal Data as in [Annex 1](dpa-annex-1-processing.md).

## 1. Sub-processors

### 1.1 Hosting and platform

| Sub-processor | Service | Agency data it receives | Apps | Where | Vendor terms to check |
|---|---|---|---|---|---|
| **Amazon Web Services** (AA's infrastructure account) | Compute (ECS Fargate), database (RDS PostgreSQL), storage (S3), keys (KMS), secrets (Secrets Manager), logs and metrics (CloudWatch), API Gateway, load balancer, CloudFront, WAF, Cognito sign-in (AA staff, the Agency's users, and Trip Planner travellers who choose to sign in by e-mail code: `tripplanner.traveller_accounts`, TripPlanner migration tp-019), SES mail (CRM forward-in mail, AA system mail, sign-in codes, Trip Planner lead e-mails to an agency with the traveller as Reply-To: AA-TripPlanner-Web `backend/assembly/leads.py`), SNS alerts | All Agency data at rest and in transit (CRM personal fields encrypted with the Agency's own keys, M-3) | CRM, Studio, Booking, TP | United States, us-west-1. CloudFront serves pages from edge locations worldwide (in transit, cached responses) | The AWS terms reach AA through a billing reseller: whether the AWS Data Processing Addendum binds through the reseller, and whether the reseller is itself a sub-processor (it has privileged account access, S241 review P0-12) |
| **Amazon Web Services: Amazon Bedrock Guardrails** | Detects personal data in CRM text before a model call (detect mode; the match is never logged) | CRM client text before it is scrubbed | CRM | us-west-1 | As above |

### 1.2 AI models (from the live AI gateway)

Every AI path runs on accounts AA holds in its own company name (ADR 0019 b19), with **one exception since
2026-11-12**: the Amazon Bedrock calls of the chat models run on a second AWS account held by AA's tech lead (the
account that pays the bill of AA's AI account), because AWS refuses those models on AA's AI account at account level
(at the last check, seven models refused and token quota 0 on five; the access requests are open with AWS and the
reseller: [acc3 case notes](../audits/2026-10-31-S261-aws-bedrock-org-access/acc3-case-notes.md)). That account holds
only a role that the CIS service may assume to call the chat models, a break-glass admin role, its Terraform state and
free spend alerts: no Agency data is stored there, no secret, no compute ([ADR 0001a](../adr/0001a-retire-acc1-llm-on-acc3-only.md)
Notes S278 and S279). The prompts pass through it in transit to Amazon Bedrock and are not kept by it. It is reversed
when AWS serves the models on AA's AI account again. The Agency has no account with any provider.

Since CIS migration 366 (2026-11-04) each stage is a chain of models, and each model is tried on each of its
deployments before the next model. **Which deployment of a model goes first is a live gateway setting** (route
control in the CIS admin, audited and versioned). **Since 2026-11-12 (route control versions 10 and 11, AA-1095)**:
every Claude model is called on the **Anthropic API first**, then on Amazon Bedrock in the tech lead's account, then
in AA's AI account; every GPT model is called on **Amazon Bedrock in the tech lead's account first**, then in AA's AI
account, then on the OpenAI API (version 11 also puts the three GPT judge routes on Amazon Bedrock first). Route
control version 7 (CIS migration 383, 2026-11-06) still holds: no writer route ends on an OpenAI model and no judge
route (nor the claim extraction `t10_claims`) ends on Amazon Nova Lite. A refused deployment is skipped without a call
(CIS #1332), so **today the Anthropic API answers the Claude stages, Amazon Bedrock in the tech lead's account answers
the GPT scoring, audit, check and extraction stages and stands behind the Anthropic API for Claude, AA's AI account is
skipped, and the OpenAI API is the last fallback of the GPT stages**. Changing the order is one setting; it changes
the order, not this list.

*Drafting note [COUNSEL]: the exception departs from ADR 0019 b19 (accounts in AA's company name). Whether a
provider account held by an individual on AA's behalf needs its own clause (or the account moves into AA's AWS
organisation, the tech lead's review planned for early December 2026) is for counsel and the business owner. AWS
remains the sub-processor either way; the data path, region rules and deployment classes below are unchanged.*

| Sub-processor | Path | Agency data it receives | Apps and stages | Where | Vendor terms to check |
|---|---|---|---|---|---|
| **Amazon Web Services: Amazon Bedrock** (the tech lead's account for the chat models since 2026-11-12, then AA's AI account; AA's infrastructure account for Nova Lite and the embedding model) | Content studio: Claude (Anthropic) writers, second after the Anthropic API since 2026-11-05; GPT models (OpenAI) for scoring and checks, first (the tech lead's account answers them today); Amazon Nova Lite in the infrastructure account only as the fallback of the two FAQ checks, which are switched off by default (flag `T9_FAQ_LLM_FILTER`; CIS 383 kept them on purpose); Meta Llama only on two platform stages over AA's own catalogue (`a3_place_card_check`, `a3_place_dedupe`), which receive no Agency data; Cohere Embed for search over catalogue text. **CRM: Amazon Nova Lite is the reply-draft writer** on Dev (infrastructure account; the Claude entries of the CRM route are switched off while the AI account refuses every model) | Content studio inputs and outputs (brand settings, briefs, the Agency's text); no personal data of the Agency's clients by rule (DM-6.4). CRM: scrubbed text only, placeholders for personal data | Studio (every T-stage); CRM (reply drafts, Bedrock only, only with the `ai_assist` entitlement and AI switched on, off by default, always after the F3 scrub); TP (narration) | Studio: API calls in us-west-1; content stages may use `global.` cross-region inference profiles, which can process a prompt in another AWS region; a stage classed `pii` is held to US deployments (CIS 373). **CRM: US regions via a `us.` inference profile** (us-east-1, us-east-2, us-west-1, us-west-2; never outside the US; AA-CIS-Infra `modules/environment/crm_llm.tf`, root ADR 0009 decision 14 amendment of 2026-11-03, Dev only) | As for AWS. Per AWS documentation the model makers receive no data on Bedrock (CRM research `04-economics-compliance-security.md`); counsel decides whether the model makers are listed at all |
| **Anthropic, PBC** (Anthropic API) | **The first path of every Claude model** since 2026-11-05 (route control version 6, kept by versions 10 and 11); Amazon Bedrock is second (the tech lead's account, then AA's AI account) | Content studio inputs and outputs (brand settings, briefs, the Agency's text): today every Claude call of the Content studio answers here. TP narration once the Trip Planner gateway can call it (it calls Bedrock only today); CRM only after its own gateway change (ADR 0008a §5-6), with the scrub kept | Studio (writers, sentence repair, FAQ checks, and the Claude fallbacks of the audit and extraction stages); TP (later); CRM (later) | **[To confirm from Anthropic's commercial terms and DPA]**. One key for every product, capped at 150 USD a month with a hard stop (CIS 366); connection `anthropic-direct` switched on 2026-11-05 (session S269) | Commercial terms allow serving tenants as end users from AA's account (AI Schedule Q15); data retention and zero-retention options; the DPA and its transfer terms |
| **OpenAI** (OpenAI API) | GPT-6 Luna behind its Amazon Bedrock deployments in every scoring, audit, check and extraction route: **the last fallback** since 2026-11-12, when Amazon Bedrock in the tech lead's account began to answer them (from 2026-10-29 to 2026-11-12, while Bedrock refused, it was the path that answered). It **no longer writes**: CIS 383 (2026-11-06) removed it from the 13 writer routes where it was the last resort | Content studio inputs and outputs (drafts it scores or checks) | Studio (judges, brand audits, claim extraction) | **[To confirm from OpenAI's terms]**. Capped at 10 USD a month with a hard stop (CIS 327) | Abuse-monitoring logs kept up to 30 days unless zero retention is approved (register section (b)); the DPA and its transfer terms |
| **Jev** (TypeSafe API) | Yes / no content decisions | Content studio text, **only for agencies on an allowlist** (`shared.jev_tenant_allowlist`) | Studio | **[To confirm]** | A DPA or zero-retention agreement is required before tenant content is sent (DM-6.4, ADR 0001). **Proposal:** the pilot agency is not put on the allowlist until that agreement exists |

*Drafting note: the AI Schedule clause .1 names the same Model Providers; a route change that adds a provider updates
the AI Use Register, the AI Schedule, this annex and the app pages together (AI Use Register "Who updates it").*

### 1.3 Other services

| Sub-processor | Service | Agency data it receives | Apps | Where | Vendor terms to check |
|---|---|---|---|---|---|
| **Sentry** (Functional Software, Inc.) | Error tracking | Error events after scrubbing: no default personal data, no request bodies, no cookies, no local variables; a residual risk that an error message quotes a value | CRM, Studio, Booking (and TP) | United States (organisation region `us.sentry.io`, read 2026-11-05) | DPA and transfer terms **[●]** |
| **DreamHost**; **Zoho** | Company mail: DreamHost is the mail host of AA's company domain ([compliance register](register.md) section (b)); Zoho is listed in the [secrets register](../security/secrets-register.md) vendor rows as "mail / business tooling" | Only if an Agency or a data subject writes to AA's company mailbox about Agency data (support or privacy requests) | — | **[To confirm]** | **[To confirm]** which of the two holds the company mailbox today, and whether it is listed; the support address may move to SES-based handling **[BUSINESS OWNER]** |

## 2. Not sub-processors (no Agency Personal Data)

| Vendor | Why not |
|---|---|
| Mapbox | Maps in the Trip Planner browser: receives the visitor's IP address and the map area directly from the browser. Becomes relevant to the Agency with the Trip Planner (milestone 2): listed then, or covered by the joint-controller clause ([pilot contract set](pilot-contract-set.md) §3) **[COUNSEL]** |
| Geoapify | Geocodes place names of AA's catalogue (CIS worker; register section (b)). The Trip Planner only shows the attribution next to points located earlier |
| DataForSEO | Search keywords and place names, one market (country of the searcher) per query. The market list can come from a tenant's settings (`target_market.countries`), and the admin-only question top-up reads the place topics chosen for tenant blogs; no tenant text and no personal data is sent. The tenant routes (T2, T7, T8, T9) only read stored search data and buy nothing (S273 audit `docs/audits/2026-11-08-S273-session/dfs-cost-audit/report.vi.md` §4; AA-CIS-App `services/seo_intelligence/seed_builder.py`, `services/acp_shared/question_topup.py`) |
| Google (Drive API) | Reads AA's own tour photos |
| GitHub, Linear, Notion, Atlassian | Code and work tracking; no Agency Personal Data by rule (DM-6.10). A support ticket names a ticket id, never a traveller |
| Namecheap | Domain registration |

## 3. The Agency's own providers (bring-your-own)

Services the Agency connects with **its own account** are the Agency's processors, chosen and contracted by the
Agency. AA's software sends data to them only on the Agency's instruction, with credentials the Agency supplies
(ADR 0019 invariant 5; ADR 0010 decision 9):

- e-mail sending through the Agency's Gmail, Microsoft 365 or SMTP server;
- SMS and WhatsApp through the Agency's own Twilio account;
- payments through the Agency's own payment provider account;
- calendars the Agency subscribes to (the ICS feed);
- the Agency's website (WordPress) and social pages (Facebook Pages through Meta) for Content studio publishing.

*Drafting note [COUNSEL]: whether AA, operating the connector, is a sub-processor of the Agency towards these providers
is open (register "Tenant CRM (open)"); the BYO decision (S247) treats them as the Agency's.*

## 4. Changes and the Vercel exit (ADR 0019 d23)

| Date | Change | Notice |
|---|---|---|
| 2026-10-28 | Agency portal moved from Vercel to AWS ECS (Vercel project removed) | Before this list existed |
| 2026-11-06 | Route control version 7 (CIS 383): the OpenAI API stopped writing (it still scores and checks); Amazon Nova Lite stopped serving judge routes (it remains the fallback of the two FAQ checks, off by default). Recorded here on 2026-11-09 | None needed (a narrower use of listed sub-processors) |
| 2026-11-07 | CIS admin and Booking admin moved to AWS ECS Fargate (their Vercel projects removed) | None needed (a removal) |
| 2026-11-08 | Trip Planner frontend moved to AWS ECS Fargate behind CloudFront, with its rules in the load balancer's WAF web ACL (Vercel project removed). **Vercel, Inc. left this list**: no AA app runs on Vercel any more | None needed (a removal) |
| 2026-11-12 | Route control versions 10 and 11 (AA-1095): Amazon Bedrock chat models served from a second AWS account held by the tech lead (billing-only exception, ADR 0001a Note S278), AA's AI account behind it; Claude = Anthropic API, then Bedrock; GPT = Bedrock, then the OpenAI API. Recorded here on 2026-11-13 | None needed (no new sub-processor; the AWS account and the order changed). Point for counsel in §1.2 |

AA tells the Agency of a new or replaced sub-processor as in DPA clause 6.2. A removal needs no notice; AA updates
this page.
