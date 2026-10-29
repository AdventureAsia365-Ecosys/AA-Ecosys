# Angle 1: AWS partners in Vietnam for Claude and OpenAI models on Bedrock

Researched 29/10/2026 (S257). Sources are primary where possible: AWS docs, the AWS Solution Provider Program (SPP) Authorized Services List, the AWS Partner Solutions Finder (PSF) API, and partners' own websites. Each claim has a URL. **[UNVERIFIED]** marks a claim that rests only on a secondary or self-published source, or on my inference.

---

## 0. Summary

1. **Why TrueIDC accounts cannot use Claude has a documented cause.** AWS's SPP/Distribution Authorized Services List (updated 24/09/2026) lets partners resell Amazon Bedrock. Anthropic models carry a footnote: *"Before you or your End Customer can access and use any model offered by Anthropic, you must first apply for and obtain resale authority from Anthropic."* An account billed by a reseller that does not hold this Anthropic authorization cannot use Claude, whatever IAM settings the customer applies. OpenAI's proprietary (non-open-weight) models are listed as resellable with no such footnote. If TrueIDC also blocks OpenAI, that block probably comes from TrueIDC's own policy, such as an SCP or a Marketplace restriction **[UNVERIFIED, inference]**. Sources: [SPP Authorized Services List PDF](https://solution-provider-program-legal-documents.s3-us-west-2.amazonaws.com/Solution+Provider+Program+List+of+Services.pdf), [AWS APN blog, 14/10/2025](https://aws.amazon.com/blogs/apn/amazon-bedrock-now-available-for-partner-resale).
2. **The question to ask any Vietnamese reseller is: "Are you an Anthropic Authorized Reseller for Amazon Bedrock?"** Tier alone does not settle it. TechX is an AWS Premier partner, but this research found no public claim that it holds Anthropic authorization.
3. **Vietnamese partners that publicly claim Anthropic authorization:**
   - **Renova Cloud** (HCMC/Hanoi, Premier tier, SPP, AI Services Competency). It calls itself *"one of the Anthropic authorized resellers in Vietnam"* and also acts as a CPPO/Marketplace reseller. The post carries no date; its images were uploaded in 2026/06, so "about June 2026". The post names Amazon Bedrock as the integration point but does not say whether Claude is billed through Bedrock or by Renova directly. [Renova post](https://renovacloud.com/en/renova-cloud-accelerates-enterprise-ai-as-anthropic-authorized-reseller-in-vietnam/)
   - **eCloudvalley** (HCMC office, Premier, SPP plus Authorized Commercial Reseller plus MSP). Its press release of 09/02/2026 says it is authorized by Anthropic to sell Claude through Amazon Bedrock to enterprise customers in **"Taiwan and Southeast Asia"** (台灣及東南亞). **Vietnam is not named explicitly** in the scope; it appears only in eCloudvalley's office list. This is the reseller acc3 already worked under. [iThome reprint of the eCloudvalley press release, 09/02/2026](https://www.ithome.com.tw/pr/173818); the English newsroom page renders client-side and could not be read: [eCloudvalley newsroom](https://www.ecloudvalley.com/en/newsroom/ecloudvalley-becomes-authorized-anthropic-reseller-delivering-claude-ai-solutions-to-enterprises)
   - **Westcon-Comstor**, an AWS Distributor with an HCMC office (the only partner with the "AWS Distributor" PSF label that the Vietnam location search returned; Westcon's own announcement does not say "only" **[unverified]**). It signed an Anthropic reseller agreement so its downstream partners can offer Claude "in the Amazon Bedrock catalogue, through AWS Resale Programs". The geographic scope is not stated, and the page has no absolute date. [Westcon announcement](https://www.westconcomstor.com/uk/en/news/announcements/2026/bringing-anthropic-s-claude-to-the-channel-through-aws.html)
4. **VND invoices with VAT:** Of the partners checked, only CMC Telecom publicly promises them (*"Receive all invoices with VND (including VAT)"*, ~30-day terms, FCT and VAT handled). Its Anthropic authorization is unknown, so ask. [CMC billing page](https://aws.cmctelecom.vn/en/dich-vu/cloud-billing-service/). Renova and TrueIDC advertise billing services with extended due dates and payment without a credit card, but their pages do not say "VND" explicitly **[UNVERIFIED for VND]**.
5. **Going direct to AWS does not give a Vietnamese VAT invoice.** AWS Inc. charges 10% VAT from 01/07/2025, or 0% for B2B customers who file their tax details under Circular 103. It issues only a commercial invoice: *"AWS is not required and will not be issuing you a tax e-invoice or VAT invoice."* [AWS Vietnam tax help](https://aws.amazon.com/tax-help/vietnam/)

**Recommended shortlist for quotes:** Renova Cloud and eCloudvalley Vietnam, both with Anthropic authorization claimed publicly. Renova names Vietnam; eCloudvalley says "Southeast Asia", so ask it to confirm Vietnam in writing. CMC Telecom is a third option: VND invoicing is confirmed, but it must confirm Anthropic authorization in writing. Use the question list in §5.

---

## 1. How Bedrock third-party models, Marketplace and resellers interact (AWS docs)

### 1.1 Third-party Bedrock models are AWS Marketplace subscriptions
- *"Access to many Amazon Bedrock foundation models is enabled by default with the correct AWS Marketplace permissions."* On the first invoke, *"Amazon Bedrock automatically initiates the subscription process in the background."* [Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)
- Prerequisites for that auto-subscription:
  - IAM permissions `aws-marketplace:Subscribe`, `aws-marketplace:Unsubscribe` and `aws-marketplace:ViewSubscriptions`.
  - For Anthropic models, the First Time Use (FTU) form, which an account inherits from its organization's management account.
  - *"Valid payment method: Your AWS account must have a valid payment method configured for AWS Marketplace purchases."* (same page)
- OpenAI open-weight models (gpt-oss-*) *"don't require a AWS Marketplace subscription"*, but the doc states that other OpenAI models do have Marketplace product keys. The OpenAI judge models we use therefore go through Marketplace. (same page)
- Separate account-level gate: *"Some models require additional account-level access … Access is determined separately for each AWS account, so accounts in the same AWS Organization can have different access … contact AWS Sales."* (same page). Note that this paragraph describes an `AccessDeniedException`, while "Error 002" is a `ValidationException`. Linking the two is therefore an inference, not something AWS documents **[UNVERIFIED, inference]**.
- Community evidence on "Error 002" (re:Post, read in full this pass) **[community]**:
  - One poster saw it on four Organization member accounts vended in the same batch. It hit **every model family, including Amazon Nova and Cohere Embed**, which need neither a Marketplace subscription nor the Anthropic form. IAM simulation and SCPs were ruled out.
  - `GetFoundationModelAvailability` still reported `authorizationStatus: AUTHORIZED` and `entitlementAvailability: AVAILABLE` on the blocked accounts. [re:Post thread 1](https://www.repost.aws/questions/QUrt7TJfi4SqqvBh9DXMtE0A/bedrock-error-002-access-to-bedrock-models-is-not-allowed-for-this-account-on-four-organization-member-accounts-vended-the-same-day-accounts-vended-one-day-earlier-and-three-months-later-work)
  - A new standalone free-tier account got it on all models and regions. Its support case waited 1–2+ weeks. [re:Post thread 2](https://www.repost.aws/questions/QUds-ksyBsTkqiLcBEq-NQJQ/error-002-access-to-bedrock-models-is-not-allowed-for-this-account)
  - What this means for us: because acc3 also fails on *all* models, the block is more likely an AWS account-level restriction than the Anthropic channel gate (which would hit only Claude). Only AWS Support can lift it.

### 1.2 Bedrock under the Solution Provider and Distribution programs
- On 14/10/2025, Bedrock *"joins our Authorized Services List and is now available for resale by our AWS Channel Partners"*. The listed providers are AI21, Anthropic\*, Cohere, DeepSeek, Luma, Meta, Mistral, OpenAI, Stability, TwelveLabs and Amazon. The footnote reads: *"\*Resale of Anthropic models subject to certain limitations."* [APN blog](https://aws.amazon.com/blogs/apn/amazon-bedrock-now-available-for-partner-resale)
- The Authorized Services List (last updated 24/09/2026) says:
  - "Amazon Bedrock\*, and only with respect to foundational models from the following":
    - *Eligible for discount:* Amazon, DeepSeek, Meta, Mistral, OpenAI open-weight models.
    - *Ineligible for discount:* AI21 Labs, **Anthropic\*\***, Cohere, Luma AI, **OpenAI non-open-weight models**, Stability AI, TwelveLabs, Writer.
  - The \*\* footnote: *"Before you or your End Customer can access and use any model offered by Anthropic, you must first apply for and obtain resale authority from Anthropic … aws-reseller-program@anthropic.com"*.
  - Source: [SPP list PDF](https://solution-provider-program-legal-documents.s3-us-west-2.amazonaws.com/Solution+Provider+Program+List+of+Services.pdf)
  - What this means for us: a reseller earns **no AWS discount** on Claude or proprietary OpenAI usage. Any reseller price for these models is AWS list price plus the reseller's markup, or minus a margin the reseller chooses to give up. Claims of "better pricing" mainly apply to other services.
- Partner confirmation: *"In October, AWS enabled its Solution Provider Partners to resell Amazon Bedrock … While models from providers such as AI21, Cohere, Meta, Mistral, and others were immediately available for resale … Anthropic required partners to undergo a separate and rigorous approval process."* (Opti9, 08/04/2026) [Opti9](https://opti9tech.com/news/opti9-approved-anthropic-reseller-amazon-bedrock/)
- The error an account sees when its reseller lacks authorization is reportedly `ValidationException: "Access to this model is not available for channel program accounts."`, with *"no documented workaround"* other than an account managed by a partner holding both the Bedrock-resale and the Anthropic authorization. [kloia blog, 15/03/2026](https://www.kloia.com/blog/amazon-bedrock-claude-validationexception) **[UNVERIFIED, secondary; exact string not found on AWS docs]**

### 1.3 Other ways a reseller can block Marketplace or Bedrock (customer side)
- **SCP or IAM deny.** The Bedrock doc tells organizations wanting to block third-party models to *"apply Deny policies on `bedrock:InvokeModel` at the Organization (SCP) or Account (IAM) level"*. Denying `aws-marketplace:Subscribe` alone does not stop the auto-subscription. [Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) A reseller that owns the Organization management account (the "partner-held account" model) can therefore switch Bedrock or Marketplace off for every member account.
- **Private Marketplace.** An organization's administrator can limit which Marketplace products member accounts may buy. A search-index summary claims AWS docs say *Bedrock models with automatic access are not governed by Private Marketplace*. The current [Private Marketplace doc](https://docs.aws.amazon.com/marketplace/latest/buyerguide/private-marketplace-current.html) does not contain that sentence; it says only *"For the latest information on access to Amazon Bedrock models, see the Amazon Bedrock User Guide"* **[unverified]**. A Bedrock block is still more likely an SCP or the Anthropic channel gate than Private Marketplace, but this is inference.
- **Payment method or liability.** Marketplace needs a valid payment method on the payer. In a partner-held organization, the partner pays for every Marketplace charge. Partners often limit Marketplace to avoid charges they cannot rebill or discount **[UNVERIFIED, inference]**. The doc requirement itself is in the [Bedrock model access doc](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html).
- **CPPO (Channel Partner Private Offers)** is the route through which a reseller sells Marketplace software. The ISV authorizes the reseller, and the reseller sends the buyer a private offer at its own markup. [AWS Marketplace CPPO doc](https://docs.aws.amazon.com/marketplace/latest/userguide/channel-partner-offers.html). Bedrock pay-per-token models do not need CPPO; they are billed as Marketplace usage on the account's payer.

### 1.4 Account models: keep our own organization (Billing Transfer)
- Since 19/11/2025, SPP and Distribution partners can resell through **Billing Transfer**. *"Partners take on financial responsibility for customer AWS Organizations, while customers retain full control of their management accounts."* [AWS What's New](https://aws.amazon.com/about-aws/whats-new/2025/11/aws-channel-partner-billing-transfer)
- Mechanics from the docs:
  - The partner (bill-transfer account) invites our management account.
  - Start and end dates align with calendar months. After a withdrawal, the end date is *"23:59:59 UTC on the last day of the current or next month"*.
  - *"Either management account involved in a transfer can withdraw the transfer at any time."*
  - After withdrawal, our own management account pays again.
  - Our side loses CUR, Cost Anomaly Detection and the AWS-priced view, and sees only Billing Conductor pro-forma costs.
  - Setting up Billing Transfer in the console requires AWS Billing Conductor, which the partner (bill-transfer account) pays for.
  - Source: [Billing transfer doc](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/orgs_transfer_billing.html)
- Why it matters for AA: the reseller would not own our Organization or SCPs, and leaving would not move or strand accounts (unlike acc3 leaving the eCloudvalley organization). Whether Billing Transfer accounts count as "channel program accounts" for the Anthropic gate is not documented, but they are resold accounts, so assume yes **[UNVERIFIED]**. The Anthropic-authorized-reseller requirement therefore still applies.

---

## 2. AWS partners with a Vietnam presence (PSF data, 29/10/2026)

Method: queried the PSF backend (`https://api.finder.partners.aws.a2z.com/search`, the API behind [partners.amazonaws.com](https://partners.amazonaws.com/)) with `location` = "Viet Nam", "Vietnam", "Ho Chi Minh" and "Hanoi", plus keyword searches. Then fetched each partner's detail record for its program and competency memberships. The location search is fuzzy, so global firms with a Vietnam office also appear. A partner detail page is `https://partners.amazonaws.com/partners/<id>/`.

Program labels as PSF prints them:
- "AWS Solution Provider Program" (SPP) is the AWS resale program.
- "Authorized Commercial Reseller" (ACR) is a separate PSF reseller label whose exact meaning AWS does not document publicly **[UNVERIFIED]**.
- "AWS Distributor".
- "AI Services Competency" is PSF's current label that includes Generative AI consulting. The PSF facet "Use Case: AI: Generative AI Consulting Services" lists the same partners.

### 2.1 Comparison table: Vietnam-headquartered or Vietnam-office resellers relevant to us

| Partner (PSF id) | PSF tier | Resale programs (PSF) | AI competency | Anthropic-authorized for Claude on Bedrock? | Marketplace / CPPO | VND + VAT invoice | Credits | Contact |
|---|---|---|---|---|---|---|---|---|
| **Renova Cloud** ([PSF](https://partners.amazonaws.com/partners/0010L00001oCHJVQA4/)) HQ HCMC | Premier | SPP, Well-Architected, Backed by AWS Support, Authorized Training Partner | AI Services, DevOps, Migration | **Yes, self-declared** "one of the Anthropic authorized resellers in Vietnam" (undated; about June 2026) [post](https://renovacloud.com/en/renova-cloud-accelerates-enterprise-ai-as-anthropic-authorized-reseller-in-vietnam/) | **Yes**: "Consulting Partner Private Offers (CPPO) và Reseller trên AWS Marketplace tại Việt Nam" [page](https://renovacloud.com/services/aws-marketplace/) | Billing service: "official AWS reseller … better pricing and extended due date" [page](https://renovacloud.com/en/services/cloud-billing/). VND not stated **[UNVERIFIED]** | "preferred access to AWS credits" (same page) | info@renovacloud.com; HCMC 3A Fl., 117 Nguyen Cuu Van; Hanoi 17F Ladeco, 266 Doi Can [contact](https://renovacloud.com/en/contact/) |
| **eCloudvalley** ([PSF](https://partners.amazonaws.com/partners/0010h00001cCURkAAO/)) HCMC office (Toong, 126 Nguyen Thi Minh Khai, D3) | Premier | SPP, ACR, MSP, Public Sector SP, ISV Accelerate | AI Services, ML Consulting, plus 8 others | **Yes, for "Taiwan and Southeast Asia"** via Bedrock (press release 09/02/2026, [iThome reprint](https://www.ithome.com.tw/pr/173818)). Vietnam is not named explicitly; confirm in writing. Our acc3 worked under them until 29/10/2026 | Yes (ISV Accelerate, ACR); details on JS site not retrievable | Not found publicly **[UNVERIFIED]**; ask | Acc3 had a credit/cover arrangement (internal fact) | HCMC office per PSF; [eCloudvalley VN site](https://www.ecloudvalley.com/vn/) |
| **TechX / Xora by TechX** ([PSF](https://partners.amazonaws.com/partners/0010h00001d4ct2AAA/)) HQ Hanoi | Premier ("first AWS Premier Tier Services Partner in Vietnam" [site](https://techxcorp.com/)) | SPP, Well-Architected, Training | AI Services, Data, Cloud Ops, Migration | **Not found** in public sources; ask | Not stated | Not stated | Not stated | [contact](https://techxcorp.com/contact): Hanoi (VMT, 86 Duy Tan); HCMC (4 Bis Nguyen Thi Minh Khai) |
| **CMC Telecom** ([PSF](https://partners.amazonaws.com/partners/0010L00001nFsCSQA0/)) | Advanced | SPP, Public Sector SP | Migration, Networking (no AI) | **Not found**; ask | Not stated | **Yes**: "CMC Telecom issues invoices in VND", "Receive all invoices with VND (including VAT)", ~30-day terms, "We handle tax responsibilities (FCT và VAT)" [page](https://aws.cmctelecom.vn/en/dich-vu/cloud-billing-service/) | "discounts or special packages" (same page) | aws@cmctelecom.vn, hotline 1900 2020; 11F CMC Tower, 11 Duy Tan, Hanoi |
| **CMC Technology & Solution** ([PSF](https://partners.amazonaws.com/partners/0010h00001aQeBLAA0/)) | Advanced | SPP, Public Sector SP | Migration | Not found | n/a | Not checked | n/a | [cmc.com.vn](https://www.cmc.com.vn) |
| **CMC Global** ([PSF](https://partners.amazonaws.com/partners/0010h00001hg1jBAAQ/)) | Advanced | ACR only | none | Not found | n/a | n/a | n/a | [cmcglobal.com.vn](https://cmcglobal.com.vn/) |
| **FPT Software** ([PSF](https://partners.amazonaws.com/partners/001E000000UfacWIAR/)) | Advanced (was "Premier Consulting" 2018) | SPP, ACR | AI Services, Security, DevOps, Migration, plus 2 others | Not found; ask | Not stated | Not stated | Not stated | [AWS partner page](https://fptsoftware.com/about-us/our-partner-network/aws) |
| **FPT Telecom International (FTI)** ([PSF](https://partners.amazonaws.com/partners/0010h00001cCj5aAAC/)) | Advanced | SPP, ACR, Public Sector SP | Networking | Not found | Not stated | Not stated (FTI sells its own e-invoice product; AWS billing terms not published) [page](https://fti.fpt.vn/dich-vu/aws/) | n/a | fti.support@fpt.com |
| **TrueIDC Vietnam** (PSF name "Arise Internet Data Center", website trueidc.com, [PSF](https://partners.amazonaws.com/partners/001E0000012bc1JIAQ/)), HQ Thailand, HCMC office (Me Linh Point, D1) | Advanced | SPP, Well-Architected | Digital Workplace, Migration (no AI) | **Not authorized as far as we can tell**: our acc2 (TrueIDC-billed) cannot use Bedrock LLMs, consistent with §1.2 | Not stated | Billing service: "Sử dụng thanh toán cho các hóa đơn trên Cloud thay vì thẻ tín dụng" [page](https://trueidc.com.vn/dich-vu/true-idc-cloud-billing/). VND not explicit **[UNVERIFIED]** | n/a | contact@trueidc.com.vn |
| **Cloudino** ([PSF](https://partners.amazonaws.com/partners/0010L00001kX0qgQAC/)) HQ Hanoi | Advanced | SPP, Public Sector SP, Training | Education, Migration | Not found | n/a | Not stated | n/a | hello@cloudino.vn [site](https://cloudino.vn/) |
| **GalaxyOne** ([PSF](https://partners.amazonaws.com/partners/0010h00001jCANPAA4/)) | Advanced | SPP | none | Not found | n/a | n/a | n/a | [galaxy.one](https://galaxy.one/) |
| **Viettel IDC** ([PSF](https://partners.amazonaws.com/partners/0010h00001aCJOnAAO/)) | Advanced | ACR only (no SPP listed) | none | Not found | n/a | Not stated for AWS | n/a | [viettelidc.com.vn](https://viettelidc.com.vn/) |
| **Westcon-Comstor** ([PSF](https://partners.amazonaws.com/partners/001E000000dGUHeIAO/)) HCMC office (181 Dien Bien Phu, D1) | Advanced | **AWS Distributor** (the only distributor the PSF Vietnam search returned; "only" is **[unverified]**), Marketplace Skilled Consulting, Authorized Training, Backed by AWS Support | Security | **Has an Anthropic reseller agreement** for Claude on Bedrock "through AWS Resale Programs" (region unstated) [announcement](https://www.westconcomstor.com/uk/en/news/announcements/2026/bringing-anthropic-s-claude-to-the-channel-through-aws.html) | Yes (distributor; CPPO for ISVs) [news 03/04/2025](https://www.westconcomstor.com/rs/en/news/announcements/2025/westcon-comstor-expands-amazon-web-services-to-vietnam.html) | Sells only through resellers, not to end customers | n/a | Use through a Vietnamese reseller |

Other Vietnam-HQ partners holding only the "Authorized Commercial Reseller" label (Advanced/Select, no SPP and no AI competency except CoderPush): Sotatek, CoderPush (AI Services), HBLAB, VSEC, TitanBases, FPT IS, DATATYK, DHTECH, Financial Software Solutions, Nimbus Layer, Haposoft. These are not good candidates for a Bedrock or Claude billing relationship.

### 2.2 Global SPP partners that list a Vietnam office (PSF)
SoftwareOne, Noventiq, Deloitte, Bespin Global, Cloud Kinetics, EPAM, Kyndryl, HCLTech, MegazoneCloud, Classmethod, G-Asiapacific and Hitachi Digital Services are all Premier with SPP and AI Services Competency. They are generally aimed at large enterprises and invoice from offshore entities **[UNVERIFIED for Vietnam invoicing]**. Classmethod holds an Anthropic Authorized Reseller agreement, but its announcement covers Japan only. [Classmethod 02/03/2026](https://classmethod.jp/english/news/260302-anthropic/)

### 2.3 Named in the brief but not found as Vietnam AWS resellers
- **VNG / VNG Cloud:** no PSF listing found under "VNG" (keyword search returned only an unrelated partner).
- **Nextlink** ([PSF](https://partners.amazonaws.com/partners/001E000000sUl2xIAC/)) is a Taiwan-HQ Premier SPP partner. Its PSF offices are Singapore, Shanghai, Taiwan and Hong Kong, with no Vietnam office listed.
- **CloudMile** ([PSF](https://partners.amazonaws.com/partners/0010h00001jE91QAAS/)) is an Advanced ACR partner with offices in Hong Kong, Taiwan and Singapore, and no Vietnam office listed.
- **"Mekong":** no matching partner found.

---

## 3. Vietnamese invoicing: direct AWS vs reseller

| Path | Invoice | VAT treatment | Vietnamese e-invoice (for input VAT) |
|---|---|---|---|
| Direct AWS Inc. (card or wire) | USD commercial invoice | 10% VAT from 01/07/2025, or 0% if B2B tax details filed under Circular 103. Marketplace sales by foreign sellers also carry 10% VAT from 01/07/2025 [AWS VN tax](https://aws.amazon.com/tax-help/vietnam/) | **No**: "will not be issuing you a tax e-invoice or VAT invoice" (same page) |
| Vietnamese reseller (e.g. CMC Telecom) | VND invoice from a Vietnamese entity | Reseller handles FCT and VAT [CMC](https://aws.cmctelecom.vn/en/dich-vu/cloud-billing-service/) | Yes, as a domestic sale. Confirm that **Marketplace and Bedrock third-party charges** appear on the same VND invoice **[UNVERIFIED]** |

Note: Decree 254/2026 and Circular 91/2026 (from 01/07/2026) let foreign platforms voluntarily register to issue Vietnamese e-invoices. This research found no evidence that AWS has registered **[UNVERIFIED]** (search summary of [vatcalc](https://www.vatcalc.com/?p=51862)).

---

## 4. What this means for AA_Ecosys

- **acc2 (TrueIDC):** Claude will not work through TrueIDC unless TrueIDC obtains Anthropic resale authority, and the PSF data gives no sign that it has. For OpenAI proprietary models, ask TrueIDC directly whether it blocks Marketplace or Bedrock for its accounts. AWS's list permits their resale.
- **acc3 (left the eCloudvalley organization):** it is now a standalone account. It needs its own Marketplace-valid payment method, plus AWS Support or Sales to clear the account-level "Error 002" flag (§1.1). AWS Organizations docs add two points. First, an account that leaves *"is no longer covered by organization agreements that were accepted on its behalf"* by the management account. Second, its *"service quota limits may change"*, and AWS says to contact Support afterwards. Both fit acc3's sudden all-model block. [Leaving an organization](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts_leave-as-member.html) Alternatively, eCloudvalley could take it back as a paying customer, preferably through **Billing Transfer**, so we keep the organization next time.
- **Durable option:** put the LLM account (or the whole organization) under an **Anthropic-authorized Vietnamese reseller using Billing Transfer**. Renova Cloud and eCloudvalley are the only Vietnam-present candidates found with public Anthropic authorization. This gives Claude and OpenAI on Bedrock under one AWS bill, a VND invoice if the reseller offers one, and no account lock-in. Either side can withdraw a billing transfer at any time, and it ends at the end of the current or the next month.
- **Price expectation:** Claude and proprietary OpenAI models are "ineligible for discount" for resellers. Expect AWS list price or slightly higher. Value comes from VND invoicing, payment terms and credits, not from token discounts.

## 5. Questions to send each shortlisted partner (Renova, eCloudvalley Vietnam, CMC Telecom)

1. Are you an **Anthropic Authorized Reseller for Amazon Bedrock**, so that your resold accounts can invoke Claude Sonnet and Haiku in us-west-1 (and cross-region inference profiles)? Please provide written confirmation.
2. Can your resold accounts invoke **OpenAI non-open-weight models on Bedrock** (Marketplace product keys)? Do you apply any SCP or Private Marketplace rule that denies `aws-marketplace:Subscribe` or `bedrock:InvokeModel`?
3. Account model: do you support **Billing Transfer**, so we keep our own management account and SCPs? Or must the account move into your organization?
4. Invoicing: VND invoice and Vietnamese VAT e-invoice covering **all** charges, including Bedrock Marketplace usage? What exchange-rate basis? What payment terms?
5. Pricing on non-discountable models (Anthropic, OpenAI): list price, markup, or rebate?
6. Credits: AWS credit programs you can nominate us for (e.g. GenAI or POC credits), and their conditions.
7. Exit terms: notice period, and what happens to accounts and model access when the contract or credit cover ends. This is to avoid a repeat of the acc3 situation.
8. Support: who handles AWS Support cases (e.g. Bedrock access errors) for resold accounts?

## Unverified or open items
- The exact meaning of PSF "Authorized Commercial Reseller" vs "AWS Solution Provider Program".
- Whether Billing-Transfer accounts are "channel program accounts" for the Anthropic gate.
- VND invoicing at Renova, eCloudvalley Vietnam and TrueIDC (stated only by CMC Telecom).
- Anthropic authorization status of TechX, FPT, CMC, Viettel IDC and TrueIDC. No public claim was found; absence of a claim is not proof.
- The exact error text `"Access to this model is not available for channel program accounts."` comes from a secondary blog only.
- eCloudvalley's Anthropic scope for Vietnam specifically: its press release says "Taiwan and Southeast Asia" only.
- Whether Westcon-Comstor is the *only* AWS Distributor for Vietnam.

## Verification

Adversarial re-check on 29/10/2026 (S257). Every cited source was re-fetched where possible: WebFetch, curl, and the PSF API at `api.finder.partners.aws.a2z.com/search?id=<id>`. Changes made:

1. **eCloudvalley scope corrected.** The earlier text said its authorization covers APJ "including … Vietnam". The press release (09/02/2026, via iThome) says **"Taiwan and Southeast Asia"** and does not name Vietnam. The newsroom URL still renders empty. Updated in §0, the §2.1 table, the shortlist and the open items.
2. **Anthropic reseller email fixed:** `aws-reseller-program@anthropic.com` (was `aws-resellerprogram@`). The SPP PDF was decrypted and read in full this pass. "Last Updated on September 24, 2026", the Bedrock eligible/ineligible lists and the `**` footnote are all confirmed verbatim.
3. **Westcon "only AWS Distributor in Vietnam" marked [unverified].** Its 03/04/2025 announcement (Hanoi) confirms the AWS distribution expansion and the CPPO role, but does not say "only". The Anthropic announcement confirms "through AWS Resale Programs", has no region and no absolute date.
4. **Renova date** changed from "June 2026" to "undated, about June 2026". The page has no date; its images were uploaded in 2026/06. Added the PSF program "Authorized Training Partner". The Premier tier, SPP and AI Services competency are confirmed in the PSF record.
5. **Error 002 analysis tightened.** The Bedrock doc's "additional account-level access" paragraph refers to `AccessDeniedException`, not the `ValidationException` "Error 002", so the link is now marked inference. The re:Post threads were read in full: Error 002 hits Amazon Nova and Cohere too, and status APIs report AUTHORIZED/AVAILABLE on blocked accounts. Conclusion added: acc3's all-model failure points to an AWS account-level block, not the Anthropic channel gate.
6. **Private Marketplace claim downgraded to [unverified].** The current AWS page no longer contains the "Bedrock automatic access not governed" sentence and links to the Bedrock guide instead.
7. **Billing Transfer details corrected.** A withdrawal ends at the end of the current or next month, not immediately at month end. Console setup needs Billing Conductor. Both are confirmed on the AWS doc; the What's New post of 19/11/2025 is confirmed.
8. **acc3 note added**, from the AWS Organizations leave-organization doc: the account loses organization agreements, and its quotas may change.

Confirmed unchanged:
- PSF tier, programs and competencies for all 13 partners in the table, all matching the live PSF records with timestamp 29/10/2026.
- The CMC Telecom VND/VAT/FCT/~30-day quotes and contacts. The site has a broken TLS chain; it was read with `curl -k`.
- TrueIDC "thay vì thẻ tín dụng", with no VND or VAT mentioned.
- Renova CPPO and billing quotes.
- TechX "first AWS Premier Tier Services Partner in Vietnam".
- AWS Vietnam tax page: 5% from 01/03/2025, 10% from 01/07/2025, the Circular 103 exemption, no VAT e-invoice, Marketplace VAT.
- The APN blog of 14/10/2025, Opti9 (08/04/2026), the kloia error string (15/03/2026, still secondary), and Classmethod (02/03/2026; its announcement targets Japanese enterprises).
