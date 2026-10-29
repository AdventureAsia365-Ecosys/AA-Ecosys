# Angle 2: LLM access paths that do not depend on an AWS reseller

Research date: 29/10/2026 (S257). Author: Claude Code research subagent.
Scope: how Adventure Asia (a Vietnamese company, HCMC) can keep using Claude (Sonnet/Haiku 5.5) and OpenAI
(gpt-5.6-luna / gpt-6-luna judges) at about $250/month without depending on an AWS Solution Provider such as
TrueIDC or eCloudvalley.
Tags: **[V]** = verified on a primary source this session. **[S]** = secondary source (partner press release,
community post). **[U]** = unverified or inferred; check before relying on it.

---

## 0. Why resellers matter: what the sources say

- **Anthropic itself limits which resellers may sell Claude.** Google Cloud's partner-model docs say: if your
  billing account is managed by a reseller that Anthropic prohibits, "you will be unable to accept the Terms of
  Service or enable Claude models"; contact the reseller. [V]
  <https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/use-partner-models>
- On AWS, Anthropic runs an **"Authorized Reseller" program for Amazon Bedrock**, sold through the AWS
  Solution Provider Program. Partners must pass Anthropic's approval process. [S]
  - Atayo, "authorized to provision and sell Claude models … through Amazon Bedrock via the AWS Solution Provider
    Partner (SPP) program": <https://atayogroup.com/blog/atayo-approved-anthropic-reseller-bedrock>
  - Classmethod, Skaylink, Solita, Cloudvisor announcements:
    <https://classmethod.jp/english/news/260302-anthropic/>, <https://www.skaylink.com/en/insights/press/reseller-anthropic-claude-aws/>,
    <https://www.solita.fi/news/solita-becomes-one-of-anthropics-first-authorised-resellers-in-europe-via-amazon-bedrock/>
  - **eCloudvalley is an Anthropic authorized reseller for Claude on Bedrock**, with a stated scope of "Taiwan
    and Southeast Asia" (press release 09/02/2026). Vietnam is not named explicitly. This plausibly explains why
    acc3 could use Claude while it was in eCloudvalley's organization. [S]
    <https://www.ithome.com.tw/pr/173818> (the newsroom page renders empty:
    <https://www.ecloudvalley.com/en/newsroom/ecloudvalley-becomes-authorized-anthropic-reseller-delivering-claude-ai-solutions-to-enterprises>)
  - A Benelux partner (Cloudar) is quoted in search results as saying that since an AWS policy change in October
    2025, customers of a partner Anthropic does not recognise "simply cannot activate these models". The page
    could not be fetched (bot wall). [S/U] <https://cloudar.be/?p=22741>
- Our own code agrees: `shared/llm_client/pricing.py` notes that "native Sonnet is blocked for channel-program
  accounts (AA-291/AA-329)", which is the acc2/TrueIDC case.

**What this means:** "use a reseller in Vietnam" only works if that reseller is in **Anthropic's** program. A
generic AWS, Google or Microsoft partner is not enough. Every option below avoids that dependency, either by
buying directly from the model vendor or by being billed directly by the cloud provider.

---

## 1. Comparison table

| # | Option | Vietnamese company allowed? | Claude | OpenAI GPT | How you pay / invoice | VN VAT invoice? | Gateway work (our `shared/llm_client`) | Reliability / risk |
|---|---|---|---|---|---|---|---|---|
| 1 | **Standalone AWS account billed directly by AWS** (acc3 after it left eCloudvalley's org, or a new one) | Yes. AWS charges Vietnam VAT under Circular 80 [V] | Bedrock, if Error 002 is cleared. Also "Claude Platform on AWS" (Anthropic-operated, AWS Marketplace billing) [V] | Bedrock OpenAI models via Marketplace [V] | Card (USD), postpaid monthly. AWS commercial invoice from Amazon Web Services, Inc. [V] | **No.** AWS: "will not be issuing you a tax e-invoice or VAT invoice" [V] | **0 days** if Bedrock comes back (same code). Claude Platform on AWS: same adapter as #2 | Blocked today (Error 002, support case pending). Fix depends on AWS Support |
| 2 | **Anthropic API direct** (platform.claude.com) | Yes. Vietnam is on Anthropic's supported list [V] | All models at list price. Batch -50%, prompt caching [V] | — | Prepaid credits by card (expire after 1 year), or monthly invoice via Sales. Stripe invoices [V] | No (foreign Stripe invoice) [U] | **~3–5 dev-days**: new `anthropic_native` adapter (the api_style is already allowed in the catalog CHECK) + provider value + Message Batches port | High. First-party, no reseller in the path. Needs a key in Secrets Manager |
| 3 | **OpenAI API direct** | Yes. Vietnam is on OpenAI's API country list [V via search snippet; page returned 403] | — | All GPT models | Prepaid credits (expire after 1 year) or monthly billing [V via search snippet; help pages 403]. Tax ID field on invoices [unverified this pass, 403] | No (foreign invoice) [U] | **Hours**: `_call_openai` already exists. Enable the catalog row (provider `openai`) and set `OPENAI_API_KEY`. Today it is gated off by S235 "Bedrock-only policy" | High. Note: the adapter is chat-completions only, no streaming |
| 4a | **Azure via a Microsoft CSP partner in Vietnam** (e.g. FPT) | Yes | **Not possible.** Microsoft: "Cloud Solution Provider subscriptions" are not supported for Claude; CSP "can't purchase third-party model offerings" [V] | Yes. gpt-6-luna and gpt-5.6-luna are "sold by Azure" with Chat Completions + Structured outputs [V]. SEA region capacity [U] | Partner invoice, usually in local currency [U] | **Likely yes** from the local CSP partner [U] | ~1 day: `openai.AzureOpenAI` / `base_url` per catalog row | Good for GPT. Does not solve Claude |
| 4b | **Azure direct (Microsoft bills; pay-as-you-go / MCA)** | Yes. Vietnam is a "Microsoft-managed" Marketplace tax country [V] | Yes, "Claude in Microsoft Foundry" (Sonnet 5.5, Haiku 5.5) at Anthropic rates, billed as CCU on the Azure bill [V]. The Claude offer is available to billing accounts in "Microsoft Managed Countries/Regions (except Belarus and Russia)", and Vietnam is on that list [V]. **No Message Batches API** [V] | Yes (as 4a) | Card or invoice. Microsoft collects and remits the tax [V] | Microsoft invoices "under Microsoft's applicable registration number"; whether that is a VN e-invoice is [U] | Same adapter as #2 (`AnthropicFoundry` client) + Azure OpenAI client | Good. Claude Sonnet 5.5 is Global Standard only; US Data Zone costs 1.1x [V] |
| 5 | **Google Vertex AI (Claude, Google-managed)** via a Vietnamese Google Cloud partner | Yes, but **a reseller-managed billing account is blocked if Anthropic prohibits that reseller** [V] | Sonnet 5.5, Haiku 5.5 on the global endpoint or the us/eu multi-region endpoint (+10%). Regional endpoints serve only Sonnet 4.6 and earlier [V]. No Anthropic Message Batches API [V]. Vertex "Batch predictions" for Claude [U] | Not native (GPT is not on Vertex) | Partner invoice (local) or Google direct (card / invoice) | Partner: likely [U]. Google direct: Google charges VN VAT 5% on applicable transactions [S] | Same adapter as #2 (`AnthropicVertex`) | Same reseller trap as AWS unless the partner is Anthropic-approved. Google direct is fine |
| 6 | **OpenRouter** (or similar aggregators) | No country limit stated [V] | Yes (routes to upstream providers) | Yes | Card / crypto credits; 5.5% fee on credit purchases [S]; invoicing for enterprise [S] | No [U] | ~1 day (OpenAI-compatible API) | Extra processor between us and the vendor; prompts not logged by default [V]; upstream retention differs [S]. Use only as an emergency fallback |

---

## 2. Detail per option

### 2.1 Standalone AWS account billed directly by AWS

**Billing and tax.**
- AWS registered under Vietnam's Circular 80 and charges **10% VAT from 1 July 2025** (5% from 1 March 2025).
  It does **not** issue a Vietnamese e-invoice: "As a non-resident taxpayer, AWS is not required and will not be
  issuing you a tax e-invoice or VAT invoice." It issues a commercial invoice. [V]
  <https://aws.amazon.com/tax-help/vietnam>
- **B2B exemption:** VAT is not charged if Tax Settings holds all four values: Tax Code, Enterprise ID number,
  Electronic Transaction Code and Payment Voucher number from the latest **Circular 103** (foreign contractor tax)
  filing. Linked accounts do not inherit the payer's tax settings. [V] (same page)
- From 1 July 2025 AWS also charges 10% VAT on **AWS Marketplace** sales by foreign corporate sellers to
  Vietnamese customers, unless the Circular 103 exemption applies. [V] (same page) That this covers Anthropic
  and OpenAI models on Bedrock is our inference [U].
- AWS has a Vietnamese legal entity, Amazon Web Services Vietnam Company Limited (Level 36, Bitexco Financial
  Tower, District 1). It is listed on AWS's "marketing entities" page, which lists entities that "may send you
  messages". That page does not say whether the entity contracts or invoices. The tax page names Amazon Web
  Services, Inc. (US) as the company. [V] <https://aws.amazon.com/legal/marketingentities>
- Payment is in USD by card. Whether pay-by-invoice / bank transfer is open to Vietnamese accounts was not found. [U]

**Bedrock access on a direct account (official docs).** [V] <https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html>
- Third-party models are enabled automatically on first invocation. This needs:
  1. `aws-marketplace:Subscribe/Unsubscribe/ViewSubscriptions` on the calling role,
  2. for Anthropic, the **First Time Use (FTU) form** (`PutUseCaseForModelAccess`), and
  3. "a valid payment method configured for AWS Marketplace purchases".
- **"The form submission at the root account will be inherited by other accounts in the same AWS Organization."**
  acc3's FTU and its Marketplace payment method came from eCloudvalley's management account. After leaving the
  org, acc3 has neither. **The FTU must be resubmitted and a card added on acc3 itself.** [V for the rule; applying it to acc3 is our inference]
- "Some models require additional account-level access… Access is determined separately for each AWS account…
  contact AWS Sales." [V]
- Check status with `GetFoundationModelAvailability` (`agreementAvailability`, `authorizationStatus`,
  `entitlementAvailability`). [V]
- Leaving an organization requires completing standalone sign-up, which "might include" contact name and
  address, a valid payment method, phone verification and support plan options. After leaving, the account "is
  no longer covered by organization agreements that were accepted on [its] behalf", and its "service quota
  limits may change" (AWS says to contact Support). [V]
  <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts_leave-as-member.html>

**What "Error 002: Access to Bedrock models is not allowed for this account" usually means.** No official AWS doc
explains this code. Community reports: [S]
- It is an account-level block, not IAM or SCP. IAM policy simulation allows the call. It is a
  `ValidationException`, and it hits **every model family, including Amazon Nova and Cohere**, which need
  no Marketplace subscription or form.
- Status APIs mislead on blocked accounts. `GetFoundationModelAvailability` showed `authorizationStatus:
  AUTHORIZED` and `entitlementAvailability: AVAILABLE`, while `agreementAvailability` was `NOT_AVAILABLE`.
- The fix comes from AWS Support. The threads show waits of 1–2+ weeks. That the case type should be
  "Account and billing" is not stated in these threads [U].
- Reported triggers:
  - a batch of Organization member accounts vended on the same day;
  - a new free-tier account with little billing history (that poster's own guess).
  - "Failing payment method" and "accounts moved between orgs" are not mentioned in these threads [U].
- Threads (fetched in full this pass):
  - <https://www.repost.aws/questions/QUds-ksyBsTkqiLcBEq-NQJQ/error-002-access-to-bedrock-models-is-not-allowed-for-this-account>
  - <https://www.repost.aws/questions/QUrt7TJfi4SqqvBh9DXMtE0A/bedrock-error-002-access-to-bedrock-models-is-not-allowed-for-this-account-on-four-organization-member-accounts-vended-the-same-day-accounts-vended-one-day-earlier-and-three-months-later-work>
- Related: AISPL (India) accounts get `INVALID_PAYMENT_INSTRUMENT` on Anthropic Marketplace agreements. This
  shows that the Marketplace payment path, not IAM, often blocks Claude on Bedrock. [S]
  <https://www.repost.aws/questions/QUt8eiNw6YRpmtEHbB0zQklA/bedrock-marketplace-agreement-for-claude-sonnet-4-6-created-then-instantly-expires-invalid-payment-instrument-despite-valid-payment-method>

**Claude Platform on AWS (new, separate from Bedrock).** [V] <https://platform.claude.com/docs/en/build-with-claude/claude-platform-on-aws>
- Anthropic operates the inference. AWS provides SigV4/IAM authentication and AWS Marketplace billing in CCU
  ($0.01 each, Anthropic list rates, postpaid). <https://platform.claude.com/docs/en/about-claude/pricing#claude-platform-on-aws-pricing>
- Same Messages API as first-party, including **Batch and prompt caching**. "All AWS commercial regions are
  supported."
- It still goes through AWS Marketplace. It probably meets the same Marketplace and reseller checks, and it is
  unknown whether Error 002 (a Bedrock entitlement) applies to it. [U]

- Setup needs a one-time `aws iam enable-outbound-web-identity-federation` per account, plus the
  `aws-external-anthropic:CreateInference` permission. For workspaces created before 18/09/2026, Anthropic might
  process data outside AWS. The page does not mention resellers or channel accounts either way. [V] (same page)

**Migration effort: none** if Bedrock comes back on acc3 (the code is unchanged). Claude Platform on AWS uses the
same `anthropic_native` adapter as option 2 (`AnthropicAWS` client).

### 2.2 Anthropic API direct

- **Availability:** Vietnam is on Anthropic's Supported Regions list (policy effective 12 Nov 2026). The policy also
  covers "cloud platforms and authorized resellers". [V] <https://www.anthropic.com/supported-countries>
- **Payment:**
  - Most organizations use **prepaid credits** bought in the Console. Credits expire 1 year after purchase, are
    non-refundable, and can **auto-reload** at a threshold.
  - Monthly invoicing in arrears (Stripe invoice) needs an arrangement with Anthropic Sales.
  - Invoices download from Console Invoice history.
  - [V] <https://support.claude.com/en/articles/8977456-how-do-i-pay-for-claude-api-use>,
    <https://support.claude.com/en/articles/16608069-understanding-your-claude-api-invoices>
  - There is a separate help article on tax/VAT ID. Its content was not retrieved, so the tax treatment for Vietnam
    is [U].
- **Pricing (USD/MTok)** [V] <https://platform.claude.com/docs/en/about-claude/pricing>

  | Model | Input | Output | Cache hit | Batch input | Batch output |
  |---|---|---|---|---|---|
  | Sonnet 5.5 | $2 | $10 | $0.10 | $1 | $5 |
  | Haiku 5.5 (≤100k prompt) | $0.10 | $0.50 | $0.01 | $0.05 | $0.25 |

  - Batch and caching discounts stack.
  - `inference_geo: "us"` adds 1.1x. Global (the default) is standard price.
  - Bedrock sets its own prices: Anthropic says partner-operated platforms "have independent regional pricing".
    Bedrock regional endpoints carry +10% over global endpoints for Claude 4.5 and later. [V]
  - **On global routing, list prices match.** We lose nothing on unit price by moving off Bedrock global profiles.
    Compare exact Bedrock prices on <https://aws.amazon.com/bedrock/pricing/> [U for exact Bedrock numbers].
- **Data:** Anthropic is the processor. ZDR is available on request through Sales (stated for Claude Platform on
  AWS; for first-party, see the data-residency doc). [V]/[U]
  <https://platform.claude.com/docs/en/manage-claude/data-residency>
- **Effort:**
  - The `shared.llm_model_catalog` CHECK already allows `api_style='anthropic_native'`.
  - `provider` is limited to `bedrock|openai|typesafe` (CHECK). Adding `anthropic` needs **1 migration** (CIS
    owner, via DB Migrate).
  - New `_call_anthropic_native()` beside `_call_bedrock_converse()` (`client.py` around lines 733–800).
    Converse→Messages mapping: system blocks, `cache_control` instead of Converse `cachePoint`, forced tool for
    JSON, usage fields, and stop reasons. The streaming sink (`stream_sink`) must be wired.
  - **Batch:** `bedrock_batch.py` (S3 + CreateModelInvocationJob) and `services/content_generation/s1_batch.py`
    need a Message Batches API backend. It is simpler (no S3, no PassRole).
  - **Direct satellite call sites outside the gateway** that call `bedrock_satellite`/`get_satellite_client`
    directly must be moved onto the catalog path or the new adapter:
    - `services/acp_contract/a3_atomize.py`
    - `services/acp_shared/atom_extraction.py`
    - `services/golden_set/llm_guard.py`
    - `services/content_generation/s1_batch.py`
    - `api/routers/admin_pipeline.py`
  - Estimate: **3–5 dev-days** including tests, and one SDK (`anthropic`) that also covers options 1 (Claude
    Platform on AWS), 4b (Foundry) and 5 (Vertex).

### 2.3 OpenAI API direct

- **Availability:** Vietnam is on OpenAI's API supported countries list. OpenAI says that list is authoritative and
  that access from unsupported locations may lead to blocking. [V via search snippet; live page 403]
  <https://help.openai.com/en/articles/5347006-openai-api-supported-countries-and-territories>
- **Payment:**
  - Prepaid credits expire after 1 year and are non-refundable except for listed cases. [V via search snippet;
    the live page returned 403 this pass] That they can offset a monthly invoice is [unverified this pass].
    <https://help.openai.com/en/articles/8264778-what-is-prepaid-billing>
  - Tax ID / VAT ID in Billing preferences applies to future invoices only. [unverified this pass; page 403]
    <https://help.openai.com/en/articles/9038389-how-do-i-update-my-accounts-billing-information-eg-vat-id>
  - Vietnam VAT treatment is [U].
- **Batch:** 50% discount, 24 h window [S] (secondary sources only this session).
- **Effort: hours.** `LLMClient._call_openai()` already exists (chat completions + strict `json_schema`). It runs
  only when the catalog row has provider `openai` and is enabled (`openai_platform_allowed`, S235 policy). Steps:
  - put `OPENAI_API_KEY` in the task env through Secrets Manager,
  - enable the `gpt-6-luna-openai`-style rows with prices.
  - Gap: no streaming on this path, and judge calls via the OpenAI Decisions API would need extra work.

### 2.4 Azure (OpenAI + Claude)

- **Azure OpenAI ("sold by Azure", first-party):**
  - `gpt-6-luna` (2026-09-22) and `gpt-5.6-luna` (2026-07-09) are listed with Chat Completions + Structured
    outputs. [V] <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure>
  - Region and deployment-type availability (Global Standard vs Data Zone APAC) is on a separate page; not checked
    for Southeast Asia. [U]
    <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability>
  - First-party Azure services are normally purchasable on CSP. That this holds for these exact models is [U].
- **Claude in Microsoft Foundry:**
  - Sonnet 5.5, Haiku 5.5, Opus 5.5 and others.
  - Anthropic list rates billed as CCU through Azure Marketplace, postpaid. **Message Batches API not supported.**
    Sonnet 5.5 is Global Standard only.
  - "Hosted on Azure: prompts and completions remain within Azure."
  - [V] <https://platform.claude.com/docs/en/build-with-claude/claude-in-microsoft-foundry>
- **Hard limit:** Microsoft lists **"Cloud Solution Provider subscriptions"** as not supported for Claude, and the
  troubleshooting table says "CSP subscriptions can't purchase third-party model offerings". Also unsupported:
  credit-only or sponsored subscriptions without a pay-as-you-go method. [V]
  <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/use-foundry-models-claude>,
  <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-from-partners>
  → **A Vietnamese CSP partner can give us GPT with a local invoice, but not Claude.** Claude on Azure needs a
  direct Microsoft billing account (pay-as-you-go/MCA).
- **Tax:** Vietnam is a **Microsoft-managed** Marketplace country: "Microsoft assumes responsibility for … calculating,
  collecting, and remitting certain taxes … Microsoft invoices under Microsoft's applicable registration number." [V]
  <https://learn.microsoft.com/en-us/partner-center/marketplace/tax-details-marketplace>
  Whether this yields a Vietnamese e-invoice usable for CIT deduction is [U]; ask the accountant.
- **Local CSP example:** FPT Telecom International calls itself "the Microsoft Cloud Solution Provider (CSP)
  Tier I in Vietnam". [S, partner's own page] <https://fti.fpt.vn/en/services/microsoft/>
- **Effort:**
  - GPT: switch to `openai.AzureOpenAI` or a per-row `base_url` + key, about 1 day.
  - Claude: `AnthropicFoundry` client on the option-2 adapter (no batch: fall back to live calls or keep batch on
    another provider).

### 2.5 Google Vertex AI with Claude

- Google-managed Claude: Messages API through `:rawPredict`, prompt caching, structured outputs. Global endpoint
  recommended; multi-region (us/eu) and regional cost +10%. **Regional endpoints serve Sonnet 4.6 and earlier
  only**, so Sonnet 5.5 and Haiku 5.5 use the global or multi-region endpoint. **No Anthropic Message Batches
  API.** Google invoices. [V] Whether Vertex's own "Batch predictions" covers Claude 5.5 is not stated on this
  page [U].
  <https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed>
- Enabling needs the Consumer Procurement Entitlement Manager role and the Cloud Commerce Consumer Procurement API.
  **A billing account managed by a reseller that Anthropic prohibits cannot enable Claude.** [V]
  <https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/use-partner-models>
- Vietnamese Google Cloud partners exist (e.g. CMC Telecom "Sell" Premier Partner, Gimasys). Whether they are
  Anthropic-approved is [U]. [S] <https://www.channelasia.tech/?p=1264623>
- Google direct: Google Payments says "we will begin charging value added tax (VAT) of 5% to applicable
  transactions" in Vietnam and puts the tax code on invoices. The page has no date. Whether it covers Cloud,
  and whether the rate is now 10% (as AWS's rate became on 01/07/2025), is [U]. [V for the quote]
  <https://support.google.com/paymentscenter/contact/vietnam_tax_info>
- No OpenAI GPT on Vertex, so a second vendor is still needed for the judges.
- **Effort:** `AnthropicVertex` client on the option-2 adapter, plus GCP service-account auth from ECS (workload
  identity federation or a key in Secrets Manager), about 1–2 days on top of option 2.

### 2.6 OpenRouter / aggregators

- No markup on provider token prices. Fee on credit purchases (rate not rendered on the FAQ page; secondary sources
  say 5.5%, $0.80 minimum). Card / AliPay / USDC. Prompts and completions are not logged by default. Automatic
  provider fallback. BYOK allowance. [V] <https://openrouter.ai/docs/faq>; fee [S] <https://www.morphllm.com/openrouter-alternative>
- Enterprise plan: "Invoiced billing or card payments", "Credit lines", "VAT compliance and usage reporting",
  ZDR and in-region routing. [V] <https://openrouter.ai/enterprise>
- **Risks:**
  - Adds a third processor for tour and tenant content.
  - Upstream retention follows each provider. [S] <https://nexos.ai/blog/is-openrouter-safe/>
  - No Vietnamese invoice.
  - Model and parameter parity (Anthropic `cache_control`, batch) depends on OpenRouter's translation.
  - Anthropic's own reseller rules could reach aggregators too. [U]
- Use only as a short emergency bridge, not as the main path.

---

## 3. Takeaways for the decision

1. **Fastest restore without any reseller:**
   - **Anthropic API direct** for Claude: list price equals Bedrock global, Batch -50%, caching, Vietnam supported.
   - **OpenAI API direct** for the judges: the adapter already exists, so it is a config change plus S235 policy
     sign-off.
   - Cost at today's volume is unchanged in USD. Payment is by company card, USD, foreign invoice.
2. **Keep pursuing acc3 standalone in parallel:**
   - Add a card.
   - Resubmit the Anthropic FTU form on acc3 itself (the org-level FTU no longer applies).
   - Verify Marketplace permissions.
   - Check `GetFoundationModelAvailability`, but do not trust a "healthy" result. On Error 002 accounts it
     reports AUTHORIZED/AVAILABLE; only a real invoke proves access (§2.1).
   - Keep the Support case open. Mention that the block covers all model families, including Amazon Nova,
     since that is the account-level symptom. Which case type to use is not documented [U].
   - If it is cleared, nothing in code changes. Bedrock on a direct account gives AWS's commercial invoice with
     10% VAT, or no VAT if the Circular 103 numbers are entered. Still **no Vietnamese e-invoice**.
3. **If a Vietnamese VAT invoice in VND is a hard requirement:**
   - The only clean local-invoice paths found are a Microsoft CSP partner (GPT only, **no Claude**) or an
     **Anthropic-authorized** reseller (AWS/Google). See angle 1 for who in Vietnam is authorized.
   - A generic local partner (like TrueIDC on AWS) cannot sell Claude.
4. **Build once, switch by catalog:** one `anthropic_native` adapter (Anthropic SDK) serves Anthropic direct,
   Claude Platform on AWS, Foundry and Vertex. The `openai_chat` adapter, with a per-row base_url, serves OpenAI
   direct and Azure OpenAI. Cost: one catalog migration (`provider` CHECK) and about 3–5 days total. That removes
   the single-account dependency that broke on 29/10.
5. Ask the accountant: is a foreign commercial invoice (Anthropic/OpenAI/AWS) plus a Circular 103 FCT filing enough
   for CIT deductibility? The AWS page shows AWS expects Vietnamese B2B customers to self-declare under Circular 103.

## 4. Open items (not verified this session)

- Exact Bedrock prices for Sonnet 5.5 / Haiku 5.5 global vs regional in us-west-1.
- Anthropic's tax/VAT handling for Vietnamese API customers (help article not retrieved).
- OpenAI VAT handling for Vietnam; live country page returned 403.
- Azure OpenAI gpt-6-luna region list (SEA / Data Zone APAC) and CSP eligibility of these exact models.
- Whether Claude Platform on AWS is subject to the same reseller and Error 002 checks as Bedrock.
- Vertex Claude batch prediction pricing and discount.
- Which Vietnamese partners are Anthropic-authorized (angle 1).
- Whether the AWS Support case type matters for Error 002, and whether payment-method or organization moves are
  known triggers.

## Verification

Adversarial re-check on 29/10/2026 (S257). Cited sources were re-fetched; changes made:

1. **eCloudvalley scope.** The press release (09/02/2026) says "Taiwan and Southeast Asia", not Vietnam
   explicitly. A primary-ish citation (iThome reprint) was added, because the newsroom URL renders empty.
2. **Error 002 section rewritten** from the full re:Post threads, which are now fetchable:
   - Added: it hits Amazon Nova and Cohere too, and `GetFoundationModelAvailability` misreports blocked accounts.
   - Downgraded to [U]: "case type Account and billing", "failing payment method" and "accounts moved between
     orgs" as triggers. None of these appears in the cited threads.
   - The takeaway for acc3 is adjusted accordingly.
3. **Vertex endpoints corrected.** Regional endpoints serve only Sonnet 4.6 and earlier, so Claude 5.5 runs on
   global or us/eu multi-region (+10%). Vertex batch predictions for Claude downgraded to [U].
4. **OpenAI billing claims downgraded.** help.openai.com returned 403 again. Credit expiry and non-refund are
   confirmed only via search snippet; the "offset monthly invoice" and "Tax ID applies to future invoices"
   claims are now marked unverified.
5. **Leave-organization prerequisites corrected.** The doc says sign-up "might include" these items. Added the
   loss of organization agreements and the possible quota change.
6. **AWS Marketplace VAT.** The page says "foreign corporate sellers". Applying it to Bedrock models is marked
   as inference. The AWS Vietnam entity wording was softened: the page lists entities that "may send you
   messages", and nothing about contracting.
7. **Claude in Foundry for Vietnam strengthened.** The offer region is "Microsoft Managed Countries/Regions
   (except Belarus and Russia)", and Vietnam is on Microsoft's managed list. The CSP exclusion and the "CSP
   subscriptions can't purchase third-party model offerings" text are confirmed verbatim.
8. **OpenRouter enterprise wording** corrected to the page text ("VAT compliance and usage reporting", not
   "international VAT compliance"). The FAQ fee percentage is still not rendered (secondary 5.5%).
9. **Google Vietnam VAT quote** confirmed, with a note that the page is undated and 5% may be outdated.
10. **Claude Platform on AWS:** added the outbound web identity federation prerequisite and the pre-18/09/2026
    workspace data note. The page says nothing about resellers.

Confirmed unchanged:
- Anthropic pricing: Sonnet 5.5 $2/$10, cache hit $0.10, batch $1/$5; Haiku 5.5 ≤100k $0.10/$0.50, cache
  $0.01, batch $0.05/$0.25; `inference_geo` us 1.1x; CCU $0.01.
- Anthropic Supported Regions (Vietnam listed; policy effective 12/11/2026; mentions cloud platforms and
  authorized resellers).
- Anthropic payment help: prepaid credits expire after 1 year, non-refundable, auto-reload; Stripe monthly
  invoicing via Sales.
- Foundry: Message Batches not supported, Sonnet 5.5 Global Standard only, "prompts and completions remain
  within Azure".
- Azure "sold by Azure": gpt-6-luna (2026-09-22) and gpt-5.6-luna (2026-07-09) with Chat Completions and
  Structured outputs.
- Google partner-models reseller-prohibition text, the Consumer Procurement Entitlement Manager role and the API.
- AWS Vietnam tax page.
- Bedrock model-access doc: FTU inheritance from the root account, the Marketplace payment-method prerequisite,
  and the `GetFoundationModelAvailability` fields.
- Atayo (07/07/2026, SPP via Bedrock).
- Classmethod (02/03/2026).
