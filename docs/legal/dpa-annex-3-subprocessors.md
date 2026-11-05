---
id: SEC-04-dpa-annex3
title: "DPA Annex 3: sub-processors (draft v0.2)"
description: "Annex 3 of the partner-agency DPA (SCC Annex III): every third party that may receive agency personal data, with data, apps and location, from the live AI gateway and AWS; plus non-sub-processors and the Vercel exit."
type: reference
status: draft
owner: nghiep
audience: [owner, cio, engineer, agent]
applies_to: [ecosystem, aa-crm-api, aa-crm-web, aa-partner-portal, aa-cis-api, aa-cis-worker, aa-booking-api]
last_reviewed: 2026-11-05
review_every_days: 30
related: [SEC-04-dpa-agreement, SEC-04-dpa-annex1, SEC-04-dpa-annex4, SEC-04, APP-06-ai-register, AA-820]
---

# DPA Annex 3: sub-processors (draft v0.2)

> [!WARNING]
> Draft for counsel, not legal advice. Part of the [Data Processing Agreement](dpa.md); also Annex III of the SCCs
> ([Annex 4](dpa-annex-4-transfers.md)). **No data processing agreement with any vendor below has been signed or checked
> in this repository** (register section (b)); the "Vendor terms to check" column is the to-do list for that **[COUNSEL]**.

**Sources, read on 2026-11-05.** AI providers: the [AI Use Register](../architecture/ai-use-register.md) v1.9,
"Providers, for the tenant terms" (routes after CIS migrations 366 and 373); the CRM draft model from AA-CIS-Infra
`modules/environment/crm_llm.tf` and the live CRM task environment. Hosting: AA-CIS-Infra `main`. Other
vendors: the [compliance register](register.md) section (b). Sentry region: read from the Sentry organisation
(`us.sentry.io`) on 2026-11-05.

**Who the vendor serves.** CRM = AA-Partner CRM; Studio = the Content studio (AA-CIS behind the agency app);
Booking = Booking B2B; TP = the Trip Planner (only for an Agency that takes it, pilot milestone 2). "Agency data"
means Agency Personal Data as in [Annex 1](dpa-annex-1-processing.md).

## 1. Sub-processors

### 1.1 Hosting and platform

| Sub-processor | Service | Agency data it receives | Apps | Where | Vendor terms to check |
|---|---|---|---|---|---|
| **Amazon Web Services** (AA's infrastructure account) | Compute (ECS Fargate), database (RDS PostgreSQL), storage (S3), keys (KMS), secrets (Secrets Manager), logs and metrics (CloudWatch), API Gateway, load balancer, CloudFront, WAF, Cognito sign-in, SES mail (CRM forward-in mail, AA system mail, sign-in codes), SNS alerts | All Agency data at rest and in transit (CRM personal fields encrypted with the Agency's own keys, M-3) | CRM, Studio, Booking, TP | United States, us-west-1. CloudFront serves pages from edge locations worldwide (in transit, cached responses) | The AWS terms reach AA through a billing reseller: whether the AWS Data Processing Addendum binds through the reseller, and whether the reseller is itself a sub-processor (it has privileged account access, S241 review P0-12) |
| **Amazon Web Services: Amazon Bedrock Guardrails** | Detects personal data in CRM text before a model call (detect mode; the match is never logged) | CRM client text before it is scrubbed | CRM | us-west-1 | As above |

### 1.2 AI models (from the live AI gateway)

Every AI path runs on accounts AA holds in its own company name (ADR 0019 b19); the Agency has no account with any of
them. Since CIS migration 366 (2026-11-04, "AWS preferred, not AWS only") each model is tried on AWS first and then on
its maker's own API before the next model.

| Sub-processor | Path | Agency data it receives | Apps and stages | Where | Vendor terms to check |
|---|---|---|---|---|---|
| **Amazon Web Services: Amazon Bedrock** (AA's AI account and infrastructure account) | Content studio: Claude (Anthropic) writers; GPT models (OpenAI) for scoring and checks; Amazon Nova and Meta Llama as fallback checks; Cohere Embed for search over catalogue text. **CRM: Amazon Nova Lite is the reply-draft writer** on Dev (infrastructure account; the Claude entries of the CRM route are switched off while the AI account refuses every model) | Content studio inputs and outputs (brand settings, briefs, the Agency's text); no personal data of the Agency's clients by rule (DM-6.4). CRM: scrubbed text only, placeholders for personal data | Studio (every T-stage); CRM (reply drafts, Bedrock only, only with the `ai_assist` entitlement and AI switched on, off by default, always after the F3 scrub); TP (narration) | Studio: API calls in us-west-1; content stages may use `global.` cross-region inference profiles, which can process a prompt in another AWS region; a stage classed `pii` is held to US deployments (CIS 373). **CRM: US regions via a `us.` inference profile** (us-east-1, us-east-2, us-west-1, us-west-2; never outside the US; AA-CIS-Infra `modules/environment/crm_llm.tf`, root ADR 0009 decision 14 amendment of 2026-11-03, Dev only) | As for AWS. Per AWS documentation the model makers receive no data on Bedrock (CRM research `04-economics-compliance-security.md`); counsel decides whether the model makers are listed at all |
| **Anthropic, PBC** (Anthropic API) | The same Claude model when its AWS deployment refuses or fails | Content studio inputs and outputs; TP narration once the Trip Planner gateway can call it; CRM only after its own gateway change (ADR 0008a §5-6), with the scrub kept | Studio (writers, the brand audit, FAQ checks, claim extraction); TP (later); CRM (later) | **[To confirm from Anthropic's commercial terms and DPA]**. One key for every product, capped at 150 USD a month with a hard stop (CIS 366). Whether the path is switched on is a live gateway setting (connection `anthropic-direct`); the tenant writing stages follow ADR 0019 d18 step 2, after the AI Schedule | Commercial terms allow serving tenants as end users from AA's account (AI Schedule Q15); data retention and zero-retention options; the DPA and its transfer terms |
| **OpenAI** (OpenAI API) | GPT-6 Luna when its AWS deployment refuses or fails (judges, checks and extraction stages); GPT-6 Luna as the **last resort writer** when no Claude path answers | Content studio inputs and outputs | Studio (judges, brand audits, claim extraction, last-resort writing); TP (last rung, once its gateway can call it) | **[To confirm from OpenAI's terms]**. Capped at 10 USD a month with a hard stop (CIS 327) | Abuse-monitoring logs kept up to 30 days unless zero retention is approved (register section (b)); the DPA and its transfer terms |
| **Jev** (TypeSafe API) | Yes / no content decisions | Content studio text, **only for agencies on an allowlist** (`shared.jev_tenant_allowlist`) | Studio | **[To confirm]** | A DPA or zero-retention agreement is required before tenant content is sent (DM-6.4, ADR 0001). **Proposal:** the pilot agency is not put on the allowlist until that agreement exists |

*Drafting note: the AI Schedule clause .1 names the same Model Providers; a route change that adds a provider updates
the AI Use Register, the AI Schedule, this annex and the app pages together (AI Use Register "Who updates it").*

### 1.3 Other services

| Sub-processor | Service | Agency data it receives | Apps | Where | Vendor terms to check |
|---|---|---|---|---|---|
| **Sentry** (Functional Software, Inc.) | Error tracking | Error events after scrubbing: no default personal data, no request bodies, no cookies, no local variables; a residual risk that an error message quotes a value | CRM, Studio, Booking (and TP) | United States (organisation region `us.sentry.io`, read 2026-11-05) | DPA and transfer terms **[●]** |
| **Vercel, Inc.** | Hosting of the AA staff apps (CIS admin, Booking admin) and of the Trip Planner frontend | Pages AA staff open (Studio content, agency names and B2B records); the Trip Planner form in transit | Studio and Booking (staff views); TP | Functions in `sfo1` (San Francisco) since 2026-10-28; edge worldwide | **Leaves this list** when each frontend moves to AWS under ADR 0019 d23 (dates in §4). The agency app (CRM and Content studio for agencies) already runs on AWS ECS |
| **DreamHost** | Mail host of AA's company domain | Only if an Agency or a data subject writes to AA's company mailbox about Agency data (support or privacy requests) | — | **[To confirm]** | **[To confirm]** whether listed; the support address may move to SES-based handling **[●]** |

## 2. Not sub-processors (no Agency Personal Data)

| Vendor | Why not |
|---|---|
| Mapbox | Maps in the Trip Planner browser: receives the visitor's IP address and the map area directly from the browser. Becomes relevant to the Agency with the Trip Planner (milestone 2): listed then, or covered by the joint-controller clause ([pilot contract set](pilot-contract-set.md) §3) **[COUNSEL]** |
| Geoapify, DataForSEO | Place names and search keywords of AA's catalogue only (register section (b)) |
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
| [●] (R5, about S272-S277) | Trip Planner frontend to AWS ECS behind CloudFront and a CloudFront-scope WAF | Vercel removed for TP |
| [●] (AA-911) | CIS admin and Booking admin to one AWS Fargate task | Vercel removed from this list |

AA tells the Agency of a new or replaced sub-processor as in DPA clause 6.2. A removal needs no notice; AA updates
this page.
