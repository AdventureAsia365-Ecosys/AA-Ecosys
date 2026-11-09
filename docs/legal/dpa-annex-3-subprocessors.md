---
id: SEC-04-dpa-annex3
title: "DPA Annex 3: sub-processors (draft v0.4)"
description: "Annex 3 of the partner-agency DPA (SCC Annex III): every third party that may receive agency personal data, with data, apps and location, from the live AI gateway and AWS; plus non-sub-processors and the Vercel exit (completed 2026-11-08)."
type: reference
status: draft
owner: nghiep
audience: [owner, cio, engineer, agent]
applies_to: [ecosystem, aa-crm-api, aa-crm-web, aa-partner-portal, aa-cis-api, aa-cis-worker, aa-booking-api]
last_reviewed: 2026-11-09
review_every_days: 30
related: [SEC-04-dpa-agreement, SEC-04-dpa-annex1, SEC-04-dpa-annex4, SEC-04, APP-06-ai-register, ARCH-01-ai-gateway, AA-820, AA-1042, AA-1038, AA-900]
---

# DPA Annex 3: sub-processors (draft v0.4)

> [!WARNING]
> Draft for counsel, not legal advice. Part of the [Data Processing Agreement](dpa.md); also Annex III of the SCCs
> ([Annex 4](dpa-annex-4-transfers.md)). **No data processing agreement with any vendor below has been signed or checked
> in this repository** (register section (b)); the "Vendor terms to check" column is the to-do list for that **[COUNSEL]**.

**Sources, read on 2026-11-05, AI rows re-read on 2026-11-09.** AI providers: the
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

Every AI path runs on accounts AA holds in its own company name (ADR 0019 b19); the Agency has no account with any of
them. Since CIS migration 366 (2026-11-04) each stage is a chain of models, and each model is tried on each of its
deployments before the next model. **Which deployment of a model goes first is a live gateway setting** (route
control in the CIS admin, audited and versioned). Since 2026-11-05 (route control version 6, preset "Prefer
Anthropic API for Claude", session S269) every Claude model is called on the **Anthropic API first** and on Amazon
Bedrock second; GPT models are called on Amazon Bedrock first and on the OpenAI API second. **Since 2026-11-06 (CIS
migration 383, route control version 7)** no writer route ends on an OpenAI model and no judge route (nor the claim
extraction `t10_claims`) ends on Amazon Nova Lite: a writer whose Claude paths all fail stops and its job is queued
again, and a check whose GPT paths all fail leaves its verdict missing (migration 383, "Behaviour on Dev"). AA's AI
account on Amazon Bedrock has refused the main models since 2026-10-29; at the last recorded check (2026-11-06) it
still refused the seven newest ones (Claude 5.x, GPT-6, GPT-5.6), and the access requests are open with AWS
([acc3 case notes](../audits/2026-10-31-S261-aws-bedrock-org-access/acc3-case-notes.md), timeline). A refused
deployment is skipped without a call (CIS #1332), so **today the Anthropic API answers the Claude stages and the
OpenAI API answers the GPT scoring, audit, check and extraction stages**. Going back to AWS first is one setting
(preset "Prefer AWS"); it changes the order, not this list.

| Sub-processor | Path | Agency data it receives | Apps and stages | Where | Vendor terms to check |
|---|---|---|---|---|---|
| **Amazon Web Services: Amazon Bedrock** (AA's AI account and infrastructure account) | Content studio: Claude (Anthropic) writers, second after the Anthropic API since 2026-11-05; GPT models (OpenAI) for scoring and checks, first; Amazon Nova Lite in the infrastructure account only as the fallback of the two FAQ checks, which are switched off by default (flag `T9_FAQ_LLM_FILTER`; CIS 383 kept them on purpose); Meta Llama only on two platform stages over AA's own catalogue (`a3_place_card_check`, `a3_place_dedupe`), which receive no Agency data; Cohere Embed for search over catalogue text. **CRM: Amazon Nova Lite is the reply-draft writer** on Dev (infrastructure account; the Claude entries of the CRM route are switched off while the AI account refuses every model) | Content studio inputs and outputs (brand settings, briefs, the Agency's text); no personal data of the Agency's clients by rule (DM-6.4). CRM: scrubbed text only, placeholders for personal data | Studio (every T-stage); CRM (reply drafts, Bedrock only, only with the `ai_assist` entitlement and AI switched on, off by default, always after the F3 scrub); TP (narration) | Studio: API calls in us-west-1; content stages may use `global.` cross-region inference profiles, which can process a prompt in another AWS region; a stage classed `pii` is held to US deployments (CIS 373). **CRM: US regions via a `us.` inference profile** (us-east-1, us-east-2, us-west-1, us-west-2; never outside the US; AA-CIS-Infra `modules/environment/crm_llm.tf`, root ADR 0009 decision 14 amendment of 2026-11-03, Dev only) | As for AWS. Per AWS documentation the model makers receive no data on Bedrock (CRM research `04-economics-compliance-security.md`); counsel decides whether the model makers are listed at all |
| **Anthropic, PBC** (Anthropic API) | **The first path of every Claude model** since 2026-11-05 (route control version 6); Amazon Bedrock is second | Content studio inputs and outputs (brand settings, briefs, the Agency's text): today every Claude call of the Content studio answers here. TP narration once the Trip Planner gateway can call it (it calls Bedrock only today); CRM only after its own gateway change (ADR 0008a §5-6), with the scrub kept | Studio (writers, sentence repair, FAQ checks, and the Claude fallbacks of the audit and extraction stages); TP (later); CRM (later) | **[To confirm from Anthropic's commercial terms and DPA]**. One key for every product, capped at 150 USD a month with a hard stop (CIS 366); connection `anthropic-direct` switched on 2026-11-05 (session S269) | Commercial terms allow serving tenants as end users from AA's account (AI Schedule Q15); data retention and zero-retention options; the DPA and its transfer terms |
| **OpenAI** (OpenAI API) | GPT-6 Luna right behind its Amazon Bedrock deployment in every scoring, audit, check and extraction route: **while Bedrock refuses, the path that answers them**. It **no longer writes**: CIS 383 (2026-11-06) removed it from the 13 writer routes where it was the last resort | Content studio inputs and outputs (drafts it scores or checks) | Studio (judges, brand audits, claim extraction) | **[To confirm from OpenAI's terms]**. Capped at 10 USD a month with a hard stop (CIS 327) | Abuse-monitoring logs kept up to 30 days unless zero retention is approved (register section (b)); the DPA and its transfer terms |
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

AA tells the Agency of a new or replaced sub-processor as in DPA clause 6.2. A removal needs no notice; AA updates
this page.
