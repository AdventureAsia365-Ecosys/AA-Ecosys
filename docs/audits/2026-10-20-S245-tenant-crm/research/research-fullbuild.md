# Tenant CRM (PR-19 / AA-821): economics, compliance and security prerequisites

Research date: 20/10/2026. This was a read-only pass: nothing was edited, pushed or written to any tool. The spec is `/home/nghiep/projects/AA-Ecosys/docs/research/partner-crm-spec.md`, and the scope is the complete product (Nghiệp, S245: no MVP). Where a fact could not be confirmed it says "unknown". Prices are list prices in USD unless marked otherwise.

---

## 0. Findings that change the design or plan

1. **Stripe does not support Vietnam.** stripe.com/global lists AU, HK, JP, MY, NZ, SG and TH. ID and IN are in preview. VN is absent. Vietnamese agencies cannot onboard to Stripe, so module 7 needs a second payment rail for VN agencies (OnePay, 2C2P/M-Pay or 9Pay) or manual recording. The country of AA's own contracting entity is unknown from the repo. `docs/guides/cio.md` does treat AA as bound by "Vietnamese data protection law".
2. **Vietnam may require a licence before AA can host this CRM for VN agencies.** Rajah & Tann's summary of Decree 356/2025 lists "Providing systems or software that process personal data for controllers" as a regulated personal-data-processing service. Such a service needs an MPS Certificate of Eligibility, and the provider must be "established and operate in accordance with Vietnamese law". This needs a counsel opinion before any VN agency onboards. **Nothing in the repo or Linear tracks it.**
3. **WhatsApp service messages are no longer free.** Meta's pricing page says that from **1 Oct 2026**, service messages beyond the 1,000 free per number per month are charged. Utility templates sent inside the customer-service window are also charged now. The spec's "24-hour window handled" assumption needs re-costing.
4. **"No access outside the agency, AA included" (F1) is not true with keys in AA's AWS account.** A per-agency KMS key in acc2 is still controlled by AA's IAM administrators. The key policy can restrict use to the CRM runtime role with an `agency_id` encryption context, and CloudTrail logs every Decrypt. That makes AA access technically restricted and audited, not impossible. Truly agency-held keys would need client-side encryption or BYOK in the agency's own AWS account, and both break server features (email matching, reminders, ops release, search). The claim should be reworded in the spec and the DPA.
5. **Real traveller data cannot go on Dev.** Rule C7.1a (`docs/architecture/data-standards/03-scaling.md:350`) and decision D-01 forbid it. The week-22 pilot with 3–5 agencies therefore needs the prod environment first (AA-880 / ADR 0012, estimated ~150–300 USD/month in `docs/engineering-handbook.md` §8.4). Vercel Hobby is "for personal, non-commercial use", so Vercel Pro (D-18) is needed before any agency uses the portal, even though the CRM is free to them.
6. **The Bedrock cross-region profile conflicts with the residency promise.** CIS code uses `global.anthropic.claude-*` profiles. AWS documents that global profiles route to "any supported AWS commercial Region worldwide". CRM routes should use a geographic (`us.`) profile and set Bedrock `data_retention_mode: none`, enforced by SCP.
7. **Google restricted-scope verification has a recurring cost.** Two-way Gmail sync needs `gmail.modify`/`gmail.readonly`, which are restricted scopes. That means a CASA security assessment every 12 months: about $675 (AL1) to $5,400 (AL2) a year, per one secondary source. Google says it "can potentially take several weeks". A design without restricted scopes would avoid this (see §2.2).

---

## 1. Assumptions used for the cost model

All figures are per agency per month. They are inputs, not measurements, so change them and re-run the arithmetic.

| Driver | Value |
|---|---|
| Seats | 3 (owner, agent, assistant) |
| Inquiries / bookings / travellers | 40 / 10 / 25 |
| Connected mailboxes | 3 |
| WhatsApp messages | 1 number; 300 outbound service + 300 inbound + 40 utility templates + 10 marketing templates |
| SMS | 20 |
| E-sign envelopes | 10 (one per booking, terms and waiver together) |
| AI drafts (module 14) | 400 drafts × (4k input + 0.6k output tokens), plus 50% for proposal and text mode |
| System e-mails (SES) | 1,000 |
| KMS | 1 key; about 5k Decrypt calls with data-key caching |

Unit prices (all accessed 20/10/2026):

| Item | Price | Source |
|---|---|---|
| Fargate us-west-1 | x86 $0.04656/vCPU-h, $0.00511/GB-h; ARM $0.03725 / $0.00409 | AWS public price list JSON (pricing.us-east-1.amazonaws.com …/AmazonECS/current/us-west-1) |
| RDS PostgreSQL us-west-1 | t4g.small $0.043/h single-AZ, $0.085/h Multi-AZ; t4g.medium $0.085 / $0.171; t4g.large $0.171 / $0.342; gp3 $0.138/GB-month | AWS price list JSON (AmazonRDS us-west-1) |
| KMS us-west-1 | $1 per customer-managed key-month; the first and second rotations add $1/month each; $0.03 per 10k symmetric requests; 20k requests/month free | AWS price list JSON; [KMS pricing](https://aws.amazon.com/kms/pricing/) |
| Secrets Manager | $0.40 per secret-month | AWS price list JSON |
| Cognito | Essentials: 10,000 MAU free, then $0.015/MAU | [Cognito pricing](https://aws.amazon.com/cognito/pricing/) |
| SES | $0.10 per 1,000 outbound; $0.10 per 1,000 inbound plus $0.09 per 1,000 inbound 256 KB chunks | [SES pricing](https://aws.amazon.com/ses/pricing/) |
| Comprehend PII | DetectPii $0.0001 per 100-character unit, 3-unit minimum. Documented languages are English and Spanish only | [Comprehend pricing](https://aws.amazon.com/comprehend/pricing/); [DetectPiiEntities API](https://docs.aws.amazon.com/comprehend/latest/APIReference/API_DetectPiiEntities.html) |
| Claude list price | Sonnet 5.5 $2/$10 per MTok; Haiku 5.5 $0.10/$0.50 per MTok | Anthropic list, cached 2026-10-06 in the claude-api skill. **Bedrock prices could not be read** from [aws.amazon.com/bedrock/pricing](https://aws.amazon.com/bedrock/pricing/) (tables load dynamically), so parity is assumed. AWS says global profiles are about 10% cheaper. |
| Vercel Pro | $20 per developer seat-month plus $20 usage credit; Hobby is non-commercial | [vercel.com/pricing](https://vercel.com/pricing) |

---

## 2. External dependencies (spec §9)

### 2.1 Stripe: multi-currency, pay links, webhooks

- **Australia fees** ([stripe.com/au/pricing](https://stripe.com/au/pricing)):
  - Domestic cards 1.65% + A$0.30; international cards 3.5% + A$0.30; +2% when currency conversion is needed. GST is included.
  - Payment Links carry no extra fee. Post-payment invoices cost 0.4%, capped at US$2.
  - Disputes cost A$25.
- **Connect** ([stripe.com/connect/pricing](https://stripe.com/connect/pricing)):
  - **"Stripe handles pricing"** (Standard accounts): $0 to the platform. The agency pays Stripe directly.
  - **"You handle pricing"**: $2 per monthly active account, 0.25% + 25¢ per payout, and 0.25% funds routing.
- **Recommendation:** use Connect with Standard accounts. AA is then never merchant of record and pays nothing, and refunds, disputes and multi-currency stay on the agency's own account. Webhooks need signature checks and idempotent handlers (the inbox pattern Booking already uses). Pay links work through Checkout Sessions on the connected account.
- **Vietnamese agencies:** Stripe is not available ([stripe.com/global](https://stripe.com/global)). Local options:
  - OnePay: "from 1.5%", third-party listing only.
  - 2C2P via M-Pay: pricing not public.
  - 9Pay: reportedly needs no local entity; single news report.
  - Sources: [inai.io](https://www.inai.io/blog/top-12-payment-gateways-in-vietnam), [2c2p.com/countries/vietnam](https://2c2p.com/countries/vietnam/), [fintechnews.sg](https://fintechnews.sg/134026/vietnam/9pay-visa/).
  - Real rates are unknown and need quotes.
  - Fallback: manual payment recording, with the invoice tracked in the CRM.

### 2.2 Gmail two-way sync and Google verification

- **Scopes:** `gmail.readonly`, `gmail.modify`, `gmail.metadata`, `gmail.compose` and `mail.google.com` are restricted. `gmail.send` is only sensitive.
- **Who needs an assessment:** Google's rule is "If you store or transmit restricted scope data on servers, then you need to complete a security assessment." The assessor is Google-empanelled and uses the CASA framework.
- **Timeline:** restricted-scope review "can potentially take several weeks". Brand verification takes 2–3 business days. Reassessment is due "at least every 12 months after your assessor's Letter of Assessment (LOA) approval date" ([Google restricted-scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification)).
- **Cost:** Google publishes no price. One source says TAC Security lists AL1 from $675 and AL2 at $5,400. Other sources say $500–4,500 and 2–6 weeks ([deepstrike.io](https://deepstrike.io/blog/google-casa-security-assessment-2025), [agenticfabriq.com](https://www.agenticfabriq.com/blog/google-oauth-verification-casa)). Google, not AA, decides whether AL1 or AL2 applies.
- **Limited Use policy:** use is restricted to "providing or improving user-facing features". Humans may not read the data without the user's affirmative agreement, except for security or legal reasons ([API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy)). This matters for AA ops and support access to synced mail.
- **Design options:**
  - (a) Full sync with restricted scopes: CASA every year.
  - (b) `gmail.send` only for sending, plus an inbound forwarding or BCC rule to an SES inbound address per agency: no CASA, but weaker threading and setup friction.
  - (c) A unified mail API such as Nylas (about $1.50–2.00 per connected account per month) or Unipile (€49 for 10 accounts, then €5.00 down to €3.00 per account) ([nylas.com/pricing](https://nylas.com/pricing/), [Unipile billing](https://developer.unipile.com/v2.0/docs/billing)). Whether these remove AA's own CASA obligation is **unknown** and needs checking with each vendor.

### 2.3 Microsoft Graph (Outlook)

- **API cost:** no per-call fee is documented for mail and change notifications. Exact confirmation is unknown.
- **Consent:** `Mail.ReadWrite` is treated as high-impact and is often blocked from end-user consent, so a tenant admin of each agency's Microsoft 365 may have to grant consent.
- **Publisher verification:** affects warnings, and can block end-user consent in some tenants. The steps are Partner Network membership, domain verification and linking the Partner ID ([Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/5861727/how-to-add-mail-readwrite-permission-in-user-conse), [MC1304287](https://mc.merill.net/message/MC1304287)). Cost appears to be $0, unverified against Microsoft Learn.
- **Lead time:** unknown. Plan days to weeks for publisher verification.

### 2.4 WhatsApp Business (Twilio or 360dialog) and SMS

**Meta pricing** ([developers.facebook.com/docs/whatsapp/pricing](https://developers.facebook.com/docs/whatsapp/pricing)):
- Billing is per delivered message (since 1 Jul 2025). Inbound messages are free.
- Each number gets 1,000 free service messages per month. From **1 Oct 2026**, service messages beyond that and utility messages inside the window are charged.
- Click-to-WhatsApp ads open a free 7-day entry-point window.
- Volume tiers apply only to utility and authentication messages.

**Rates from 1 Oct 2026, per secondary sources that cite Meta's rate card:**

| Market | Marketing | Utility / authentication / service | Source |
|---|---|---|---|
| US | $0.0250 | $0.0034 | [formbeep](https://formbeep.com/whatsapp-api-pricing/) |
| UK | $0.0635 | $0.0220 | formbeep |
| Germany | $0.1365 | $0.0550 | formbeep |
| Australia | $0.0842 | $0.0113 | [whautomate](https://whautomate.com/whatsapp-business-api-pricing), [getkanal](https://getkanal.com/blog/whatsapp-business-pricing-guide) |
| Vietnam / Rest of APAC | unknown | unknown | not found |

**Business service provider (BSP) fees:**
- **Twilio:** $0.005 per message, inbound or outbound, on top of Meta's fee ([landbot](https://landbot.io/blog/twilio-whatsapp-pricing)).
- **360dialog:** €49/$49 per number per month (Premium €99, top tier €299), with no markup on Meta fees ([docs.360dialog.com/docs/pricing](https://docs.360dialog.com/docs/pricing)).
- **Direct Meta Cloud API** as a Tech Provider: no BSP fee. Meta onboarding requirements and timeline are unknown beyond the spec's "2–4 weeks".

**Classification risk:** "quiet-client nudges" (module 10) will probably count as **marketing** templates, which cost 3–12× a utility template.

**Recommendation:** use Embedded Signup so each agency owns its WhatsApp Business account and pays Meta directly. AA's cost then becomes only the BSP fee, or $0 on the direct Cloud API. Avoid 360dialog's per-number fee, which costs about $9.8k/month at 200 agencies.

**SMS (Twilio):**
- Australia: $0.0515 per segment plus possible carrier fees ([twilio.com/sms/pricing/au](https://www.twilio.com/en-us/sms/pricing/au)).
- Vietnam: $0.2852 per segment, with the column ambiguous on the page ([twilio.com/sms/pricing/vn](https://www.twilio.com/en-us/sms/pricing/vn)).
- Sender-ID registration rules: unknown.

### 2.5 E-signature

| Provider | Price | Notes | Source |
|---|---|---|---|
| BoldSign API | $30/month including 40 envelopes, then $0.75 each | Residency in US, EU, CA or AU | [boldsign.com/pricing](https://boldsign.com/pricing/) |
| Documenso | Teams $40/month (embedded signing); Platform $250/month (unlimited documents and API, white-label embed); self-host available | Self-host licence terms not stated on the page (CE/BE; possibly AGPL, unverified) | [documenso.com/pricing](https://documenso.com/pricing) |
| Dropbox Sign API | Essentials about $75/month for 50 requests; Standard about $250/month for 100 | Page layout ambiguous; overage not stated | [sign.dropbox.com](https://sign.dropbox.com/products/dropbox-sign-api/pricing) |
| DocuSign API | About $50/month for 40 envelopes, overage $3–5.80 | Secondary source; DocuSign's own page returned 404 | [goodsign.io](https://goodsign.io/blog/eSignature-API-Pricing) |

Whether the insurer accepts a given e-signature for the trekking waiver is **unknown** (spec non-code track, Phase 2).

### 2.6 PII scrubbing (F3)

| | Presidio self-hosted | Amazon Comprehend |
|---|---|---|
| Cost | Fixed compute: one 1 vCPU / 4 GB Fargate task in us-west-1 ≈ $48.91/month (x86) or $39.14 (ARM); about 2× for HA | $0.0001 per 100 characters (3-unit minimum). A 3,000-character prompt ≈ $0.003, so ≈ $1.2–3 per agency-month at the assumed volume |
| Languages | Multilingual through the NLP engine you choose; **Vietnamese quality unknown**, needs a custom or third-party model | **English and Spanish only** (API reference) |
| Data path | Stays in the VPC | Another AWS service, same account |
| Region | Runs anywhere | Availability in us-west-1 **unknown**, check |

Recommendation: Presidio, self-hosted (Python, MIT licence, unverified), with custom recognisers for passport numbers, VN phone numbers and Vietnamese names. Add a regression test set; the spec's success metric is "zero leaks in audit".

### 2.7 KMS keys per agency (F1 identity vault)

- **Cost per agency:** $1/month in year one, $2 after the first rotation and $3 after the second. With data-key caching, requests cost about $0.02. At 10, 50 and 200 agencies that is **$10–30, $50–150 and $200–600 per month**.
- **Cheaper alternative:** one KMS key plus a per-agency data key stored wrapped in the DB costs about $1/month in total. But shredding then means deleting a DB row, and that row survives in RDS PITR backups for 7 to 14 days. Deleting a whole KMS key (7–30 day waiting period) makes backups unreadable too, which is cleaner for "verified deletion" (module 18).
- **Do not store OAuth refresh tokens one per secret** in Secrets Manager: 600 mailboxes × $0.40 = $240/month. Store them envelope-encrypted in `crm.*` instead.

### 2.8 LLM zero data retention: Bedrock vs OpenAI

**Bedrock** ([data retention](https://docs.aws.amazon.com/bedrock/latest/userguide/data-retention.html), [abuse detection](https://docs.aws.amazon.com/bedrock/latest/userguide/abuse-detection.html), [cross-region inference](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html)):
- Mode `none` means "No request or response data is written to durable storage by AWS or shared with the model provider".
- "There is no data retention change to Claude models released before Claude Fable 5." Claude Opus 4.8, for example, permits `none`.
- **Claude Fable 5 and 5.1 require `aws_review`**: retained up to 30 days and possibly reviewed by AWS. They are **not usable** for CRM data under ZDR.
- Model providers don't receive prompts.
- An SCP can force `none` across the organisation.
- Global profiles route worldwide; geographic profiles stay within the geography.

**OpenAI** ([developers.openai.com/api/docs/guides/your-data](https://developers.openai.com/api/docs/guides/your-data)):
- By default, "abuse monitoring logs … retained for up to 30 days".
- ZDR or Modified Abuse Monitoring are "subject to prior approval by OpenAI".
- API data is not used for training unless you opt in.

**Recommendation:** CRM AI calls go only through the gateway to Bedrock on acc3, using a `us.` profile, Sonnet 5.5 or Haiku 5.5 (not Fable), with mode `none` enforced by SCP. Exclude the OpenAI fallback and Jev from CRM routes; DM-6.4 already forbids sending identifying PII to them. acc3 is billed through the reseller eCloudvalley (memory `acc2-bedrock-claude-gpt-blocked`). Whether the resellers TrueIDC and eCloudvalley must be listed as sub-processors is a question for counsel. AA-886 already lists TrueIDC.

---

## 3. Monthly running cost (CRM increment only)

Not included: the prod environment baseline (ADR 0012, ~$150–300) and the agencies' own pass-through fees (Stripe processing, and Meta fees if each agency owns its WhatsApp account).

### 3.1 Per-agency variable cost (mid case)

| Item | $/agency-month | Basis |
|---|---|---|
| WhatsApp via Twilio | ~5 (range 3.95–6.82) | 650 msgs × $0.005, plus 40 utility and 10 marketing templates at US–DE rates; service messages under the free 1,000 |
| SMS | ~3 (1.03 AU – 5.70 VN) | 20 messages |
| LLM, Sonnet 5.5 list | ~8.4 | 1.6M input × $2 + 0.24M output × $10, +50% |
| KMS | 1–3 | |
| SES | ~0.3 | |
| Cognito | 0 | Under 10k MAU |
| Stripe (Standard accounts) | 0 | |
| **Subtotal** | **~18.7** | |

### 3.2 Totals

| | 10 agencies | 50 agencies | 200 agencies |
|---|---|---|---|
| Variable (§3.1) | ~187 | ~935 | ~3,740 |
| E-sign | BoldSign 30 + 60 × 0.75 = **75** | Documenso Platform **250** (BoldSign would be 375) | Documenso Platform **250** (fair-use limit unknown; BoldSign would be 1,500) |
| Compute, us-west-1 x86 | API 2 × (0.5 vCPU/1 GB), worker 1, Presidio 1 × (1 vCPU/4 GB) = **111** | API 2 × (1 vCPU/2 GB), worker 2, Presidio 2 = **222** | API 3, worker 3 × (1 vCPU/2 GB), Presidio 3 = **395** |
| RDS increment | ~0 (fits the shared prod instance) | t4g.small → medium Multi-AZ: **+63** | → t4g.large Multi-AZ: **+188**, plus storage up to ~28 |
| Vercel Pro (D-18) | 40–60 | 60 | 60–100 |
| Google CASA, amortised | 56 (AL1) – 450 (AL2) | 56–450 | 56–450 |
| Security baseline (AA-873, WAF), rough | 25–40 | 25–40 | 25–40 |
| **Total** | **≈ $500–925/month** | **≈ $1.6k–2.0k/month** | **≈ $4.7k–5.2k/month** (≈ $24–26 per agency) |

### 3.3 Sensitivities

- Haiku 5.5 instead of Sonnet 5.5: saves about $8 per agency, which is −$80, −$400 and −$1,600 at the three sizes.
- Agency-owned WhatsApp account on the direct Cloud API: saves about $3–5 per agency.
- 360dialog: adds $49 per agency, which is +$490, +$2,450 and +$9,800.
- 360dialog fee bands and Twilio number rental are excluded. Twilio lists international numbers at $1.15/month; AU number price is unknown.

Because the product is "free for partners", AA carries about $5k/month at 200 agencies. Pass-through (agency-owned Stripe and WhatsApp accounts, agency-paid SMS) cuts that to roughly LLM + KMS + infrastructure, about $2.5k. The pricing model is gap #8 in the spec.

### 3.4 One-off costs and lead times

| Item | Cost | Time |
|---|---|---|
| Google brand + restricted-scope verification + CASA | $675–5,400, then **every year** | Several weeks, plus 2–3 days brand verification |
| Microsoft publisher verification | ~$0 (unverified) | Unknown |
| Meta business verification, Tech Provider / BSP onboarding, template approvals | $0 Meta fee (unverified) | 2–4 weeks (spec) |
| Stripe Connect platform setup | $0 | Days |
| Legal: DPA, terms, privacy notices, VN DPIA + TIA dossiers, possible VN certificate, EU SCCs, AU review, insurer waiver review | **Unknown**, needs quotes from VN and AU/EU counsel | VN TIA is due 60 days after transfers start; A05 replies in 15 days |
| GDPR Art. 27 EU representative (if needed) | Unknown | — |
| Prod environment (AA-880) | ~$150–300/month (handbook estimate) | Must exist before the pilot |

---

## 4. Compliance: AA as processor of agencies' traveller data

### 4.1 Vietnam PDPL

- **Status:** Law No. 91/2025/QH15 was passed 26 Jun 2025 and took **effect 1 Jan 2026**. **Decree 356/2025/ND-CP** was issued 31 Dec 2025, took effect 1 Jan 2026 and replaces Decree 13/2023. Sources: [bewiseapps](https://bewiseapps.com/doing-business-in-vietnam/intellectual-property-data-and-technology/personal-data-protection), [vietnam-briefing](https://www.vietnam-briefing.com/news/vietnam-personal-data-protection-regulation-decree-356.html), [Rajah & Tann](https://www.rajahtannasia.com/?p=184709), [DLA Piper](https://www.dlapiperdataprotection.com/?t=law&c=VN).
- **Penalty decree:** one source cites **Decree 330/2026/ND-CP, effective 19 Aug 2026**. This is not verified against an official gazette, so treat it as unconfirmed.
- **Processor duties:**
  - Process only on instruction; apply security measures; assist the controller.
  - Delete or return data at the end of the contract.
  - Notify the controller of a breach promptly. The controller notifies A05 within 72 hours.
  - A written agreement with prescribed content is required.
- **Impact assessments:** a DPIA is required for controllers **and processors**. A TIA is required for transfers abroad, **including offshore cloud** (acc2 is in us-west-1). It must be filed within 60 days of the transfer starting, and updated on change.
  - The TIA exemptions include transfers needed for "cross-border transport, logistics, payments, hotel, visa" procedures. That helps module 8 (ops release) but not CRM hosting.
- **Sensitive data:** health, ID-card images, precise location, and bank, card and financial transaction data. The CRM holds health flags, passport scans and payments, so the small-business grace period (to 31 Dec 2030) **does not apply**: it excludes sensitive data, processing service providers and processing of 100k or more subjects.
- **Licensing:** see §0.2 (Certificate of Eligibility, Vietnamese establishment).
- **Fines:** up to VND 3bn; up to 5% of the prior year's Vietnamese revenue for cross-border transfer breaches.
- Article numbers could not be extracted; the EY PDF is encrypted.

### 4.2 GDPR (EU and UK agencies)

- AA is a processor under Art. 28. The AA DPA must cover:
  - Instructions, confidentiality, security (Art. 32), and help with data subject requests, DPIAs and breaches.
  - Deletion or return at the end of the contract.
  - Audits.
  - Sub-processors, with prior general authorisation and notice of changes.
- Hosting in the US is a transfer out of the EU, so **SCC Module 2** (controller to processor) applies. It already contains Art. 28 terms, so a separate set of Art. 28 clauses is not needed ([BCLP FAQ](https://www.bclplaw.com/en-US/events-insights-news/bclp-global-data-privacy-faqs-how-do-the-new-article-28-clauses-fit-with-the-new-sccs-are-both-needed-for-a-non-eu-processor.html)). UK agencies need the IDTA or UK Addendum.
- Health and mobility flags (and dietary flags that reveal religion) are **Art. 9** special-category data, so they need explicit consent. The spec already makes them optional "with consent".
- A DPIA is likely for the agency, with AA assisting.
- **Open question for counsel:** whether a non-EU processor serving EU controllers must appoint an Art. 27 representative and keep Art. 30(2) records. The EDPB view is mixed in the sources found ([gdpr-info Art. 27](https://gdpr-info.eu/art-27-gdpr/)).

### 4.3 Australian Privacy Act

- Agencies with A$3M or less turnover are generally exempt (small-business exemption). The Tranche 2 exposure draft (Privacy Amendment (Personal Data Protection) Bill 2026) **does not remove the exemption**, per HSF Kramer, Sep 2026 ([hsfkramer](https://www.hsfkramer.com/insights/2026-09/the-draft-tranche-2-privacy-act-reforms-whats-there-whats-new-and-whats-missing)). Its contents (any controller/processor split, APP 8 changes) are **unknown**; the page returned 403.
- **APP 8 (cross-border):** OAIC APP Guidelines 8.14 (updated 3 Oct 2025) say an overseas cloud provider can be a "use", not a "disclosure", when the contract limits purpose, binds sub-contractors and gives the agency effective control ([OAIC Ch. 8](https://www.oaic.gov.au/privacy/australian-privacy-principles-guidelines/chapter-8-app-8-cross-border-disclosure-of-personal-information/)). The AA DPA should be written to meet that test. APP 11 (security) and the Notifiable Data Breaches scheme still apply to covered agencies.
- From my own knowledge, to verify: POLA Act 2024 created a statutory privacy tort from 10 Jun 2025, and automated-decision transparency duties from 10 Dec 2026. "AI drafts, humans send" probably falls outside the automated-decision duty.

### 4.4 Deliverables before the first agency stores traveller data

- **DPA template:** processor clauses for VN, GDPR and AU; SCC Module 2 and UK Addendum annexes; the 90-day deletion of AA ops data (module 8); the k ≥ 10 aggregation (module 17); and a sub-processor annex. DM-6.8 already requires a DPA before the first tenant; AA-886 has a DPA template in scope.
- **Sub-processor list** (extends AA-886):

  | Party | Role |
  |---|---|
  | AWS acc2, through TrueIDC | Hosting, DB, SES, Cognito, KMS |
  | AWS Bedrock on acc3, through eCloudvalley | AI; Anthropic receives no data, per AWS docs |
  | Vercel | Frontend, data in transit |
  | Twilio or 360dialog / Meta | Messaging |
  | E-sign vendor | Signing |
  | Sentry | Must hold no PII (DM-6.4) |
  | Stripe (Standard), agency's Google/Microsoft mailbox | Agency's own direct contract with that provider; AA only connects through the agency's OAuth grant. Counsel to confirm |
  | OpenAI, Jev | Excluded from CRM routes |

- **Consent records** per purpose, with value, time and source (DM-6.5). Health consent is a separate optional step. PDPL forbids default or pre-ticked consent.
- **Export and erasure:** module 18 plus crypto-shredding of the agency key on offboarding. Traveller-level erasure deletes F1 rows and redacts F2, audit and outbox data. Tax-record retention for invoices is the agency's duty; periods are **unknown** per country.
- **Retention:** a row for every new `crm.*` table in the DM-7 registry (DM-7.1). Retention is set per tenant with hard delete (DM-6.8).

---

## 5. Security prerequisites (Linear, read 20/10/2026)

| Issue | Status | Relevance to the CRM | Gap vs the CRM spec |
|---|---|---|---|
| **AA-813** Tenant users | Backlog, Medium | F4 depends on it. Backlog README §4 says the description is outdated (password login + `acp_shared.tenant_users`) and should be rescoped to ADR 0006 Phase 3 Cognito invitations | Its roles are owner/editor/viewer; the spec needs owner/agent/assistant with **margin visibility** rules. Needs CRM-specific roles |
| **AA-817** RLS / `aa_cis_admin` | **Done** (High) | CRM tables need FORCE RLS on a non-owner runtime role | DM-6.8 warns `aa_cis_admin` could read `crm.*` through `pg_read_all_data` until the role split. **Probe again** that no runtime role holds `pg_read_all_data` or BYPASSRLS before `crm-001`. Use its own `crm_owner` / `crm_app` roles and FORCE RLS from day one (DM-8.4) |
| **AA-839** Erasure runbook | Backlog, Low, parked | Module 18 and F1 | Explicitly scopes **out** "tenant CRM deletion (DM-6.8, AA-821)". The CRM needs its own erasure and crypto-shred runbook plus a DRY RUN |
| **AA-877** PII tags (bk/tp) | Backlog, Medium | RoPA and sub-processor list | CRM migrations must tag every column with `pii:` / `conf:` from `crm-001` (DM-6.1). Add an X2 lint |
| **AA-873** GuardDuty, Access Analyzer, S3 BPA, CloudTrail multi-region + KMS | Backlog, Medium | Detection before real PII | Add a CloudTrail data-event or metric alarm on KMS `Decrypt` outside the CRM role for F1 keys |
| **AA-874** Redis AUTH/TLS/at-rest | Backlog, High | Needed if the CRM uses Redis for sessions or queues | — |
| **AA-875** SSRF-safe `safe_http` | Backlog, High | Webhooks, attachment fetches, supplier URLs (module 15) | — |
| **AA-876** Edge hardening (rate limits, WAF, CORS, headers) | Backlog, High | The public intake form (module 1), no-login proposal links (module 3) and the client portal are internet-facing | Add bot protection on intake and unguessable, expiring, hashed proposal tokens (cf. AA-827, AA-909) |
| **AA-886** /privacy, /terms, legal packet | **In Progress** | DPA template and sub-processor list | Extend for the CRM vendors in §4.4 |
| **AA-821** Tenant CRM research | Backlog, Low | Umbrella issue | Done-when is "research note + design proposal"; it needs updating for the S245 decision to build the complete product |

Not tracked anywhere (nothing found in Linear, backlog or docs):
- VN Certificate of Eligibility, DPIA and TIA filings.
- Rewording the F1 "AA included" claim.
- Per-agency KMS and crypto-shred design.
- Bedrock `us.` profile with an SCP forcing ZDR.
- CASA budget and schedule.
- Webhook signature verification for Stripe, Twilio, Meta and Graph.
- F5 audit-log volume and retention (every read is logged).
- Prod environment as a prerequisite for the pilot.
- Second payment rail for Vietnamese agencies.

---

## 6. Repo sources

- `/home/nghiep/projects/AA-Ecosys/docs/research/partner-crm-spec.md` (§1–§11)
- `/home/nghiep/projects/AA-Ecosys/docs/architecture/data-standards/02-data-management.md`: DM-6.1, 6.4, 6.5, 6.8, DM-7
- `/home/nghiep/projects/AA-Ecosys/docs/architecture/data-standards/03-scaling.md:350` (C7.1a)
- `/home/nghiep/projects/AA-Ecosys/docs/guides/cio.md`: vendors, legal items, retention
- `/home/nghiep/projects/AA-Ecosys/docs/security/baseline.md`
- `/home/nghiep/projects/AA-Ecosys/docs/engineering-handbook.md` §8.4: Vercel Pro, prod estimate
- `/home/nghiep/projects/AA-Ecosys/docs/ops/finops.md`: the `crm` App cost tag already exists
- `/home/nghiep/projects/AA-Ecosys/docs/backlog/README.md`: rows for AA-813, AA-821, AA-839, AA-873–877, AA-886
- `/home/nghiep/projects/AA-Ecosys/docs/legal/tenant-terms-ai-clause-draft.md`
- `/home/nghiep/projects/AA-Ecosys/apps/AA-Booking/docs/ui-spec.md:780` (Q22: payment gateway still undecided)
- AWS price-list extracts (Fargate, RDS, KMS, Secrets Manager for us-west-1) are cached under `/tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/6a3e7693-d257-47b5-af70-a2ea05d8dec5/scratchpad/px/`

Web sources are linked inline above and were all accessed 20/10/2026. Where a figure comes from a secondary source, it is attributed to that source rather than to the vendor.