# CRM-02 readiness checks (AA-930, S247, 22/10/2026)

Card CRM-02 of the CRM design v3 ([design-v3.md](../2026-10-21-S246-crm-design-v3/design-v3.md) §6.3, W0).
Every check is read-only. AWS calls ran as `nghiep_aa365` (acc3) and `aa365-admin` (acc2), us-west-1 unless stated,
on 22/10/2026 between 06:30 and 07:30 UTC. **Spend: $0.** No LLM was called, no guardrail was created, no resource was written.

Verdicts: **pass** = the plan can go ahead as written or with the stated delta; **fail** = the plan must change;
**pending** = waiting on a vendor answer or on a step this lane may not run.

## Summary

| # | Check | Verdict | Plan delta (short) |
|---|---|---|---|
| 1 | Haiku 5.5 `us.` inference profile on acc3 | **pass** | CRM gateway pins `us.anthropic.claude-haiku-5-5` (the CIS catalog uses `global.`); `us.` is +10 % on price; fallback cost line (+$38) is dropped |
| 2 | Bedrock Guardrails on acc2 | **pass** (permission probe), smoke pending | Fix C9 path changes: Guardrails can run **in acc2, us-west-1**. The LLM call stays on acc3. The acc3 CRM-only role is still needed, for `InvokeModel` only |
| 3 | Bedrock Guardrails on acc3 + `ApplyGuardrail` smoke | **pass** (permission probe), smoke pending | Smoke not run: it needs `CreateGuardrail` (a write). Moves to CRM-33a, which creates the guardrail through Terraform |
| 4 | Google OAuth scope classes | **pass** | `gmail.send` and `calendar.events` are both *Sensitive*: brand + scope verification, **no CASA**. Testing mode is enough on Dev |
| 5 | Microsoft Graph scope classes | **pass** | `Mail.Send`, `Calendars.ReadWrite`, `offline_access` (delegated) need no admin consent. Publisher verification (free, Partner One ID) before Go-real |
| 6 | Cognito tier + MAU price for passkeys/MFA | **pass** | Partner pool on **Essentials**, `FactorConfiguration=MULTI_FACTOR_WITH_USER_VERIFICATION`. Cost $0 under 10,000 MAU (cost line ≈ $0 at 10 and 50 agencies) |
| 7 | Free FX source with VND | **pass** | Primary: ExchangeRate-API open access (attribution on pages that show rates). Cross-check: fawazahmed0 `exchange-api` (CC0). SBV not used. Store the provider per row |
| 8 | Stripe Checkout session expiry range | **pass** | 30 min to 24 h confirmed; the design's formula and 30-minute floor stand. "Unverified" is removed |
| 9 | BoldSign regions | **pass** | US, EU, Canada, Australia; no Asia. If the fallback is ever switched on, pick **US** (same region class as AWS) |
| 10 | Mapbox on the sub-processor list | **pass** (one point open) | Add Mapbox, Inc. as AA sub-processor, "AWS US + global CDN", 2021 SCCs in DPA Schedule C. Whether the DPA is part of the ToS by reference is checked at W8 |
| 11 | Twilio ISV / Meta Tech Provider rule | **pending** (Twilio answer) | Twilio docs lean to "required". If confirmed: CRM-28 switches to AA subaccounts, Twilio becomes an AA sub-processor, the clock moves to W8 |
| 12 | TrueIDC / eCloudvalley IAM roles in acc2 / acc3 | **pending** (vendors + an IAM read this lane may not run) | The orchestrator runs the one read-only IAM listing below; vendor answers are still asked |

No check failed because of MFA: the STS sessions of both profiles were valid.

---

## 1. Haiku 5.5 `us.` inference profile on acc3 — pass

- **Evidence (live, 22/10/2026):** `aws bedrock list-inference-profiles` on acc3 shows `us.anthropic.claude-haiku-5-5`
  **ACTIVE** in us-west-1, us-west-2 and us-east-1 (also `global.anthropic.claude-haiku-5-5`). `get-inference-profile` in
  us-west-1: `SYSTEM_DEFINED`, routes to us-east-1, us-east-2, us-west-1, us-west-2 only. acc2 lists the same profiles.
- **Callable:** S246 smoke on acc3 (16:29 UTC, 21/10) passed for Haiku 5.5 through `global.` after the foundation-model
  agreement was created ([ecloudvalley-request.md](../2026-10-21-S246-bedrock-models/ecloudvalley-request.md)). The
  agreement is per account and model, not per profile, so `us.` uses the same access. No `us.` call was made in this
  check (no paid call allowed for it here).
- **Price (AWS Price List API, `AmazonBedrockFoundationModels`, us-west-2, "Claude Haiku 5.5 (Amazon Bedrock Edition)"):**
  input $0.10 / output $0.50 per Mtok **Global**; input $0.11 / output $0.55 per Mtok for the regional (`us.`) profile.
  Cache read $0.01 global / $0.011 regional.
- **Plan delta:**
  - CRM-33a pins `us.anthropic.claude-haiku-5-5` and runs one invoke test through the CRM-only role. Note that the CIS
    catalog row from migration 259 maps acc3 to `global.`; the CRM gateway must not reuse it, because the DPA says "US regions".
  - Cost: the `us.` premium is 10 %, about +$1.3–1.5/month at 10 agencies on the $13–15 LLM line. The "+$38/month if
    Haiku 5.5 `us.` is missing" line in design §7 no longer applies.
  - Carry the S246 lesson: Haiku 5.5 adaptive thinking counts against `maxTokens` ([place-trial-haiku-5-5.md](../2026-10-21-S246-bedrock-models/place-trial-haiku-5-5.md)).
    CRM draft calls set effort / `max_tokens` explicitly.
- **Source:** live CLI output above; AWS Price List API (`aws pricing get-products --service-code AmazonBedrockFoundationModels`), 22/10/2026.

## 2. Bedrock Guardrails on acc2 — pass (permission probe); end-to-end smoke pending

- **Evidence (live):**
  - `aws bedrock list-guardrails` succeeds on acc2 in us-west-1, us-west-2, us-east-1 (no guardrails exist yet).
  - `aws bedrock-runtime apply-guardrail` with a well-formed but non-existent guardrail id returns
    `ValidationException: The guardrail identifier or version provided in the request does not exist` on acc2 — not
    `AccessDeniedException`. The request passed authorisation (SCP + IAM) and failed only on the resource lookup. No text
    unit was processed, so the call is free.
  - Service quotas on acc2 (us-west-1) equal acc3: `ApplyGuardrail` 100 requests/s, sensitive-information filter
    50 text units/s, 100 guardrails per account.
- **Why acc2 works here when Bedrock LLMs do not:** the Claude/GPT models are sold through AWS Marketplace ("AWS
  Marketplace software usage" in the price list), and that is what the TrueIDC payer blocks. Guardrails is a first-party
  AWS charge under service code `AmazonBedrock` (for example `Guardrail-SensitiveInformationPolicyPaidUnitsConsumed`).
  This is an inference from the price list and the probe, not a TrueIDC statement.
- **Price (Price List API, us-west-2):** sensitive-information filter (PII) $0.10 per 1,000 text units, regex filter $0,
  word filter $0, content filter $0.15, denied topics $0.15. One text unit = up to 1,000 characters
  ([Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)).
- **Plan delta (Fix C9):**
  - The **planned path changes**: the F3 scrubber calls `ApplyGuardrail` in **acc2, us-west-1**, in-region and without
    a cross-account hop. PII never leaves acc2 before the scrub.
  - The acc3 role `AA3-Bedrock-Invoker-CRM` keeps only `bedrock:InvokeModel` on the `us.` Haiku profile; drop
    `ApplyGuardrail` from it unless the acc2 smoke fails.
  - CRM-33a: create the guardrail in Terraform (acc2), grant the CRM task role `bedrock:ApplyGuardrail` on that ARN,
    and run the first real call (< $0.01). If it is refused, fall back to acc3, the old planned path.
  - The probe ran as the admin role. The task role needs its own grant; that is not a readiness question.
- **Source:** live CLI output above, 22/10/2026.

## 3. Bedrock Guardrails on acc3 + `ApplyGuardrail` smoke — pass (permission probe); smoke pending

- **Evidence:** the same `list-guardrails` and `apply-guardrail` probe on acc3 gives the same results as acc2:
  listing works, the probe reaches the resource lookup, and the quotas are the same.
- **Smoke not run:** a real `ApplyGuardrail` call needs a guardrail, and `CreateGuardrail` is a write. This card is
  read-only, so the smoke (< $0.01) moves to CRM-33a, where the guardrail is created in Terraform anyway.
- **Plan delta:** none beyond §2. acc3 stays the fallback location for Guardrails.

## 4. Google OAuth scope classes — pass

| Scope | Class | Needs |
|---|---|---|
| `https://www.googleapis.com/auth/gmail.send` | **Sensitive** (Google's Gmail scope table) | Brand verification + sensitive-scope verification (justification, demo video), 3–5 business days typical. **No security assessment (CASA)** |
| `https://www.googleapis.com/auth/calendar.events` | **Sensitive** (Google gives "reading events stored in Google Calendar" as its sensitive example; only Gmail/Drive-type scopes are Restricted) | Same as above, no CASA |

- Restricted Gmail scopes, which would need the annual security assessment, are `mail.google.com`, `gmail.readonly`,
  `gmail.compose`, `gmail.insert`, `gmail.modify`, `gmail.metadata`, `gmail.settings.basic`, `gmail.settings.sharing`.
  The design uses none of them.
- Apps "in the development, testing, or staging phases" need no verification. They show an "unverified app" screen,
  have a test-user cap and shorter refresh-token lifetimes. That fits Dev with synthetic agencies.
- **Plan delta:** none to the build. R15 keeps Google `calendar.events` sync; the ICS fallback is needed only if Google
  reclassifies the scope. Google verification of both scopes is a W8 (Go-real) task, as already planned. It needs the
  public home page, privacy policy and a demo video.
- **Sources:** [Gmail API scopes](https://developers.google.com/workspace/gmail/api/auth/scopes) ·
  [Calendar API scopes](https://developers.google.com/workspace/calendar/api/auth) ·
  [Sensitive scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification) ·
  [OAuth app verification help](https://support.google.com/cloud/answer/13464321), all read 22/10/2026.
  The scope class for `calendar.events` is also listed as Sensitive by a third party ([Nylas guide](https://developer.nylas.com/docs/dev-guide/provider-guides/google/google-verification-security-assessment-guide)).

## 5. Microsoft Graph scope classes — pass

| Permission (delegated) | Admin consent required |
|---|---|
| `Mail.Send` | No (also consentable by personal Microsoft accounts) |
| `Calendars.ReadWrite` | No |
| `offline_access` | No |

- Microsoft has no Sensitive/Restricted classes like Google. The gate is **publisher verification**: for apps
  registered after 8 November 2020, when risk-based step-up consent is on, users cannot consent to an unverified
  multitenant app that asks for more than sign-in and basic profile.
- Publisher verification is free. It needs a verified Microsoft AI Cloud Partner Program (Partner One) global account,
  an Entra work tenant (not a personal Microsoft account) and a publisher domain that is not `*.onmicrosoft.com`.
- A customer tenant can still block user consent by policy. The agency admin then grants consent, so onboarding copy
  needs a line for it.
- **Plan delta:** add "Microsoft publisher verification (Partner One ID, AA domain)" to the W8 vendor-verification row,
  next to Google. No build change.
- **Sources:** [Graph permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference) (source
  file `microsoftgraph/microsoft-graph-docs-contrib`, `concepts/permissions-reference.md`) ·
  [Publisher verification overview](https://learn.microsoft.com/en-us/entra/identity-platform/publisher-verification-overview), 22/10/2026.

## 6. Cognito tier + MAU price for passkeys/MFA — pass

| Tier | Price per MAU | Free MAU / month | Passkeys | Authenticator app (TOTP) MFA | Email MFA |
|---|---|---|---|---|---|
| Lite | $0.0055 (first tier above free) | 10,000 | No | Yes | No |
| **Essentials** | **$0.015** | **10,000** | **Yes** | Yes | Yes |
| Plus | $0.020 | none | Yes | Yes | Yes |

- Passkeys (`WebAuthnConfiguration`) need **Essentials or higher**. With
  `FactorConfiguration = MULTI_FACTOR_WITH_USER_VERIFICATION`, a passkey with user verification **satisfies MFA**, so
  "MFA required (passkey or TOTP)" from design §2 point 7 works as written. With a custom domain and managed login, the
  relying-party id must be the custom domain's FQDN.
- **Live (acc2):** the existing pools `aa-workforce-dev` and `aa-external-dev` are already on `ESSENTIALS`
  (4 and 0 users). The partner pool uses the same tier, so no new tier is introduced.
- SAML/OIDC federated users have a separate 50-MAU free tier and cost $0.015 above it. The partner pool does not plan
  SAML/OIDC federation.
- **Plan delta:** CRM-11 creates the partner pool on Essentials with `UserVerification=required` and
  `MULTI_FACTOR_WITH_USER_VERIFICATION`. Cost line in design §7: Dev $0, 10 agencies $0, 50 agencies $0 while the
  account stays under 10,000 MAU across all pools (the "≈ 0–1 / ≈ 1–5" range drops to $0). The TOTP-only fallback is
  not needed.
- **Sources:** [Cognito pricing](https://aws.amazon.com/cognito/pricing/) ·
  [WebAuthnConfigurationType](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_WebAuthnConfigurationType.html) ·
  live `describe-user-pool`, 22/10/2026.

## 7. Free FX source with VND — pass

ECB reference rates do not include VND (already noted in the design). Candidates checked live on 22/10/2026:

| Source | VND per USD (fetched) | Licence / terms | Verdict |
|---|---|---|---|
| ExchangeRate-API open access `open.er-api.com/v6/latest/USD` | 25,846.20 (update 21/10 00:02 UTC), 166 currencies | Free, no key. **Attribution required** ("Rates By Exchange Rate API" link on pages that use the rates). Caching and commercial currency conversion allowed; **no redistribution** of the data. Updates once a day; 429 for 20 min if rate-limited | **Primary** |
| fawazahmed0 `exchange-api` (jsDelivr `@fawazahmed0/currency-api`) | 25,888.92 (date 2026-10-21) | **CC0-1.0**, daily, no rate limit. Upstream data source not stated | **Cross-check** only |
| Vietcombank XML rate board | buy/transfer/sell per currency against VND | "For reference only. Only one request every 5 minutes"; no reuse terms published | Not used |
| State Bank of Vietnam central rate | not fetched | Terms unverified (as in the design) | Not used |

The two usable sources differ by 0.17 % on USD/VND.

- **Plan delta (R17):**
  - The daily FX job (`crm_fx_fetch`, data lane §3.1; card CRM-16) reads ExchangeRate-API daily for the VND crosses and keeps ECB for the rest.
  - It cross-checks against fawazahmed0 and flags a gap > 1 %.
  - The FX block keeps `fx_source=platform_daily`; `fx_rate_platform` gains a `provider` column
    (`ecb|exchangerate_api|...`) in CRM-16.
  - Any page or PDF that shows a platform rate carries the attribution line. CRM-16 and CRM-19 add it to their UI checklists.
  - We do not expose a rates feed or API to agencies, because that would be redistribution.
  - Dev keeps synthetic rates, as planned.
- **Sources:** [ExchangeRate-API open access docs](https://www.exchangerate-api.com/docs/free) ·
  [ExchangeRate-API terms](https://www.exchangerate-api.com/terms) ·
  [fawazahmed0/exchange-api](https://github.com/fawazahmed0/exchange-api) · live fetches 22/10/2026.

## 8. Stripe Checkout session expiry range — pass

- Stripe API reference, `expires_at`: "It can be anywhere from 30 minutes to 24 hours after Checkout Session creation.
  By default, this value is 24 hours from creation." Direct charges on the agency's Connect Standard account create the
  session with the same parameter.
- **Plan delta:** none to the logic. `expires_at = min(earliest hold − 15 min, now + 24 h)` and "re-check if < 30 min
  left" stand. Remove "the 30-minute floor is Stripe's allowed range and is unverified" from design §3.5 (card flow).
  CRM-23 adds a test that clamps to `now + 30 min + margin` and never sends a value under 30 min.
- **Source:** [Stripe API: Create a Checkout Session](https://docs.stripe.com/api/checkout/sessions/create), 22/10/2026.

## 9. BoldSign regions — pass

- Data residency regions, chosen at sign-up: **US** (eastern US), **EU** (Netherlands), **Canada** (Toronto),
  **Australia** (Sydney). There is no Asia region. Per BoldSign's own blog the platform runs on Google Cloud.
- **Plan delta:** BoldSign stays a fallback only (self-built e-sign is the plan). If it is ever switched on, use the
  **US** region, so the sub-processor entry reads "US", the same region class as AWS. No build change.
- **Sources:** [BoldSign data residency](https://boldsign.com/data-residency-compliance) ·
  [BoldSign data storage article](https://support.boldsign.com/kb/article/14573/data-storage-and-security-in-boldsign) ·
  [BoldSign 50,000 customers blog (regions, GCP)](https://boldsign.com/blogs/boldsign-50000-customers-worldwide/), 22/10/2026.

## 10. Mapbox sub-processor terms — pass (one point open)

- Mapbox publishes a sub-processor list ("Last Updated: June 4, 2026"): AWS hosting (USA), CloudFront CDN in many
  regions, Snowflake, Zendesk, GitHub, plus affiliates in the USA, UK, Poland, Japan, Germany, Finland, Canada and Belarus.
- The Mapbox DPA page says data is processed "In AWS in the United States". Mapbox cannot limit processing to one
  region, and its staff in affiliate countries may access personal data. Transfers rely on DPA Schedule C (2021 SCCs).
- **Open point:** neither page says whether the DPA is incorporated into the Terms of Service by reference, or how
  sub-processor changes are announced (the "Request updates" section has no steps). Check this at W8, together with the
  public data page.
- **Plan delta:** design §5.10 changes "Mapbox (to be confirmed)" to "Mapbox, Inc. — maps/geocoding, AWS US + global
  CDN, SCCs". The tile requests carry the viewer's IP, not CRM records. Keep the Mapbox token URL-restricted, as in
  TripPlanner.
- **Sources:** [Mapbox sub-processors](https://www.mapbox.com/legal/subprocessors) ·
  [Mapbox DPA](https://www.mapbox.com/legal/dpa), 22/10/2026.

## 11. Twilio ISV / Meta Tech Provider rule — pending (Twilio answer)

- **Question (sent by Nghiệp):** when each agency owns its **own** Twilio account and its own WABA through Self
  Sign-up, and AA only stores the agency's credentials, is AA an "ISV" that must join Meta's Tech Provider programme?
- **What Twilio's docs say (22/10/2026):**
  - The sender-registration page says: "If you're an Independent Software Vendor (ISV), you must join Meta's Tech
    Provider program, complete a technical integration, and onboard your customers through the program."
  - The Twilio FAQ says "ISVs can onboard themselves on Self Sign-Up, however for their end clients they need to
    integrate to the Tech Provider Program."
  - The Tech Provider page itself says an ISV "can join". Its flow assumes one **subaccount per customer** under the ISV.
- **Reading:** the docs lean to "required" whenever a software vendor onboards WhatsApp senders for its customers. The
  agency-owned-account case is not addressed directly, so it stays **pending** until Twilio answers.
- **Plan delta if Twilio says "required":**
  - CRM-28 switches to AA-owned **Twilio subaccounts** (one per agency), with cost re-billed to the agency.
  - Twilio becomes an AA sub-processor (DPA + public data page).
  - AA joins Meta's Tech Provider programme: Meta app approval + Twilio Partner Solution, 3–4 weeks, plus Embedded
    Signup integration. It needs 2FA and Meta business verification for AA's own Business Portfolio. The clock moves
    to W8.
  - Until the answer arrives, build CRM-28 behind the provider-neutral adapter, so both credential models fit.
  - SMS is not affected; the Tech Provider rule is WhatsApp-only.
- **Sources:** [Twilio Self Sign-up](https://www.twilio.com/docs/whatsapp/self-sign-up) ·
  [Twilio Tech Provider program](https://www.twilio.com/docs/whatsapp/isv/tech-provider-program) ·
  [Tech Provider integration guide](https://www.twilio.com/docs/whatsapp/isv/tech-provider-program/integration-guide) ·
  [Which onboarding applies to me](https://support.twilio.com/hc/en-us/articles/7356734623643-How-do-I-know-which-WhatsApp-onboarding-process-applies-to-me), 22/10/2026.

## 12. TrueIDC / eCloudvalley IAM roles — pending (vendors + orchestrator IAM read)

- **Question:** do the payers (TrueIDC for acc2, eCloudvalley for acc3) hold IAM roles inside our accounts (for example
  a billing or support role that trusts their account)? This matters for DPA wording (who can reach PII) and for Q1 3.11.
- **Not run here:** the subagent guardrail hook blocks `aws iam` calls for subagents, so this lane could not list the
  roles. The vendor answers have not been asked in this lane.
- **Next step for the orchestrator (read-only, one line per account):**
  `aws iam list-roles --profile aa365-admin --query "Roles[].[RoleName,AssumeRolePolicyDocument.Statement[].Principal]" --output json </dev/null`
  (and the same with `--profile nghiep_aa365`). Flag every role whose trust principal is an account other than acc1/acc2/acc3,
  or a SAML provider. Compare with [access review 2026-Q4](../2026-10-20-S245-access-review/README.md).
- **Plan delta:**
  - If such roles exist, the DPA and the public data page name the reseller as an entity with technical access.
  - The CRM KMS key policies (CRM-04) must not grant `kms:Decrypt` to those roles. They already allow only the CRM
    task roles, so this is a test to add, not a redesign.
  - If no roles exist, nothing changes.

---

## Updates to the CRM design (to apply when the design doc is next edited)

1. §4.5 / Fix C9: Guardrails runs in acc2 us-west-1. acc3 role = `InvokeModel` on `us.` Haiku 5.5 only. acc3 Guardrails = fallback.
2. §7 cost: drop "+$38 if Haiku 5.5 `us.` is missing"; add "+10 % `us.` premium (≈ +$1.5 at 10 agencies)"; Cognito partner pool $0 under 10,000 MAU.
3. §5.10: Mapbox confirmed as sub-processor (US + CDN, SCCs); BoldSign region = US if activated.
4. R17: FX provider = ExchangeRate-API open access (+ attribution) with CC0 cross-check; `fx_rate_platform.provider`.
5. §3.5 card flow: Stripe 30 min – 24 h range confirmed.
6. W8 row: add Microsoft publisher verification next to Google verification.
7. Still open: Twilio ISV answer (CRM-28 path), reseller IAM roles, Mapbox DPA incorporation.
