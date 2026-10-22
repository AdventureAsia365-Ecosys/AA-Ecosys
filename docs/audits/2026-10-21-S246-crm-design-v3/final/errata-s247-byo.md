# AA Partner CRM: design errata S247 — integrations are bring-your-own

Status: proposed with [ADR 0010](../../../adr/0010-aa-partner-app.md) decision 9 (Proposed, S247). Owner: nghiep.
Related: AA-821, AA-928, AA-930. Applies on top of [`crm-design-final.md`](crm-design-final.md) (accepted S246);
where the two differ, this errata wins once ADR 0010 is accepted.

**Decided by Nghiệp, S247 (22/10/2026):** (1) CRM-23 Stripe v1 uses the agency's own restricted key (`rk_`), no AA
Stripe platform or Connect account: approved. (2) Maps: the BYO-maps proposal is **reversed**. A map is a product
feature, not a vendor account that carries legal duties, so AA provides it (Mapbox under AA's own token, restricted to
the CRM hosts); agencies connect no map token and Mapbox stays an AA sub-processor.

S247, 2026-10-22. Agent: Claude Code. Source: Nghiệp's product direction of 22/10/2026 (below), the readiness checks
([AA-930](../../2026-10-22-S247-crm-readiness/README.md)) and the proposal for Ms. Thư
([`proposal-thu.md`](../../2026-10-22-S247-crm-byo/proposal-thu.md)).

**The rule in one paragraph.** Each agency brings its own vendor accounts (Twilio and its WhatsApp sender, Stripe,
mailbox, an e-sign provider if it wants one) and does its own registrations with those vendors. AA builds the
connectors, a setup wizard with test buttons and health status, and stores the credentials encrypted; AA holds no
master vendor account on an agency's behalf. AA's SES sends system mail only. Maps are AA's own product feature
(Mapbox, AA token). The agency is the data controller for its travellers; AA is the processor and keeps platform
security as its own engineering job. AI stays AA's feature. Legal wording is a proposal for Ms. Thư.

Conventions as in the final design (`CRM-nn` = v3 card, `AA-nnn` = Linear issue, *(est.)* = estimate).

---

## 1. Changes per module and issue

| Card (issue) | Was (final design / v3 card) | Now |
|---|---|---|
| **CRM-06 KeyProvider** (AA-934) | `integration` DEK purpose; `integration_credential.provider twilio\|google\|microsoft\|boldsign` | Same key and table, **wider provider list**: `twilio`, `stripe_key`, `stripe_webhook_secret`, `google`, `microsoft`, `smtp`, `esign` (`boldsign` and later others). Health columns for the wizard (§2). Contract test: no serializer of any route returns `secret_enc` or a decrypted value; decrypt allowed only in the dispatcher, webhook and health-check paths (lint). Change = audit row; owner-only |
| **CRM-17 email** (AA-945) | Send-as Gmail + Outlook; forward-in through SES; `allow_platform_sender` opt-in (Fix B18); sender kinds `agency_mailbox\|platform\|system` | **Gmail, Microsoft 365 and SMTP** (host, port, TLS required, user, app password; send only, no IMAP in v1, the CRM keeps its copy). Forward-in through AA's SES receipt rule **kept** (receive-only). **`allow_platform_sender` removed**; sender kinds become `agency_mailbox\|system`. AA system mail is a closed list (§3). A dead mailbox holds every client message in `held_reconnect`; the owner gets a system alert; nothing to a traveller leaves from AA's domain except one-time codes |
| **CRM-23 payments** (AA-952) | Stripe Connect Standard (test), direct charges, AA platform key + `Stripe-Account` header; Nghiệp creates a Stripe test platform account | **Agency's own Stripe through a restricted key (`rk_`) in v1** *(decided: Nghiệp, S247, 22/10/2026)*: the owner creates the key in its own Stripe Dashboard with the listed permissions; the CRM checks the permissions, reads the account id, creates its webhook endpoint through the key and stores the signing secret. Tenant = per-tenant hook URL + that tenant's secret + stored account id. No AA Stripe platform account. Connect stays a later adapter mode (`mode own_key\|connect`). Expiry formula, refunds from approved requests only, no stored cards, VN agencies manual: unchanged |
| **CRM-25 contracts and waivers** (AA-955) | Self-built e-sign; BoldSign fallback paid by AA (≈ $30/month) and listed as AA sub-processor | Built-in e-sign stays **AA's feature** (no vendor). The BoldSign slot becomes **the agency's own provider account**, connected in the wizard; then it is the agency's processor. Terms, waiver and consent texts are the agency's documents; AA templates are examples. The insurer question (Q2 5.1) stays for AA's own products; an agency's insurer is the agency's question |
| **CRM-28 WhatsApp + SMS** (AA-958) | Agency's own Twilio; fallback "AA subaccounts, re-billed, Twilio becomes AA sub-processor" if Twilio requires Meta Tech Provider | **Agency-owned Twilio only; fallback removed.** AA never onboards a WhatsApp sender, never runs Embedded Signup, never creates subaccounts. The agency registers its sender (Twilio Self Sign-up), its SMS brand / campaign or sender ID, and gets its templates approved in its own Twilio account; the CRM reads approved templates and enforces the 24 h window. AA needs **no ISV / Tech Provider registration** (readiness check 11) |
| **CRM-31 onboarding + import** (AA-962) | 3 required steps (connect Gmail or Outlook, invite team, embed form) + "Later" | Same 3 required steps (step 1 accepts SMTP too). New **"Connections"** page and wizard (§2) with a test button and health status per connection; **controller settings** (privacy-notice link shown on forms, data-request contact, consent text, retention choices inside fixed limits); a one-time **owner acknowledgement** of the shared responsibility (wording from Ms. Thư, versioned, logged) |
| **CRM-36 campaigns** (AA-968) | SES `crm-marketing` configuration set, "<Agency> via <neutral domain>" | **Sent from the agency's mailbox, or from the agency's own email service connected by SMTP.** No `crm-marketing` set. Consent gate, one-click unsubscribe (handled by the CRM), suppression and "a list over the daily limit is spread over days" stay |
| **CRM-03 infra** (AA-931) | SES actions for transactional + marketing sets; per-agency SES identity / DKIM at Go-real | SES grants for **system mail only** (one configuration set) and the inbound receipt rule; no marketing set, no per-agency SES identities or tenants |
| **CRM-20 builder map / CRM-21b client proposal** (AA-948, AA-950) | Mapbox with an AA token; Mapbox an AA sub-processor | **Unchanged: Mapbox with an AA token (decided: Nghiệp, S247, 22/10/2026)**, public token URL-restricted to the CRM hosts; Mapbox stays an AA sub-processor; no map connection for agencies. CRM-21a's day-list builder stays the core; the CRM-20 builder map stays an enhancement that does not block M3 |
| **CRM-29a workflows** (AA-959) | Deposit and Stage 3 nudges in `crm-transactional` | Nudges and reminders to travellers go from the agency's mailbox; held if it is disconnected |
| **CRM-30 calendar** (AA-961) | Google / Graph sync through AA's OAuth app | Unchanged (already the agency's own calendar); health status shown in Connections |
| **CRM-33a AI** (AA-964) | AA's gateway on AA's Bedrock | **Unchanged: AI is AA's feature, not BYO.** No agency LLM keys. AA pays inside the $2 per-agency cap |
| **CRM-35 portability + deletion** (AA-967) | Export, verified erasure | Add a small **data-request log** (received, type, due date, done) so the agency can track its own replies; AA forwards requests it receives to the owner *(est. 2 business days, wording in the DPA)* |
| **CRM-13b support L2** (AA-971) | Integration changes blocked during support | Support sees connection **health only**, never credentials or the account references behind them |
| **CRM-37b data page** (AA-970) | AA sub-processors: AWS, Mapbox (to confirm), conditional Twilio, BoldSign, flight API, Sentry | AA sub-processors: **AWS** and **Mapbox** (maps, AA token); conditional AA tools only (Sentry if enabled). The agency's own processors (Stripe, Twilio/Meta, Google, Microsoft, its SMTP and e-sign providers) are listed as "connected by the agency, under its own contract" |
| **CRM-38 Go-real** (AA-980) | Vendor verifications (Google, Microsoft, Meta if Twilio requires it); Stripe live per agency | Verifications = **AA's own OAuth apps** (Google verification, Microsoft publisher verification); **Meta not needed**. "Stripe live" = the agency connects its live key and passes the test |
| **CRM-02 readiness** (AA-930) | Check 11 pending | **Resolved by BYO** (readiness note updated) |

Final-design rows affected: §1.2 (WhatsApp / SMS, card payments, email, e-sign, sub-processors, vendor
verifications), §3.2 onboarding row, §6 integrations table, §7.5 "free test accounts", §8 cost, §9.1 Twilio risk,
§9.2 open point 6.

## 2. Connections (CRM-31, with CRM-06)

One page under Settings, owner edits, agents and assistants see status only.

| Connection | Required? | What the agency does at the vendor | What the CRM asks for | Test button | Health check |
|---|---|---|---|---|---|
| Mailbox | Yes (onboarding step 1) | Nothing (Gmail / Microsoft 365) or create an app password (SMTP) | OAuth consent, or SMTP host / port / user / app password; then set forwarding to its forward-in address | Sends a test mail to the owner's own address; checks the forward-in address received the forwarding confirmation | Nightly token or login check; send failures |
| Card payments (Stripe) | No ("Later") | Opens and verifies its Stripe account; creates a restricted key with the listed permissions | The restricted key (test or live) | Permission probe; in test mode creates and expires a Checkout Session and waits for the webhook | Nightly account read; webhook failures; `livemode` matches the key |
| SMS and WhatsApp (Twilio) | No | Opens its Twilio account; registers its SMS brand / campaign or sender ID; registers its WhatsApp sender (Self Sign-up); gets templates approved | Account SID, Auth Token, optional API key; which numbers / sender to use | Sends a test SMS / approved template to the owner's own phone; checks the inbound webhook with a reply | Nightly account read; delivery error codes surfaced in plain words |
| Calendar | No | Nothing | OAuth consent (Google / Microsoft) | Creates and deletes a test event | Nightly token check |
| E-sign provider | Hidden unless needed | Opens its provider account | API key | Creates and voids a test request | Nightly check |

- **States:** `not_set_up`, `connected`, `needs_attention` (permission missing, vendor warning), `disconnected`
  (revoked, failed login). Columns on `integration_credential`: `status`, `last_checked_at`, `last_ok_at`,
  `failure_class` (`auth_revoked|permission_missing|vendor_rejected|rate_limited|unreachable`), `last_test_at`,
  `last_test_result`. (`status ok|reconnect_needed|revoked` from the lane becomes these four states.)
- **On failure:** red banner for the owner, a system alert mail, sends on that channel held (mail) or blocked with a
  clear reason (SMS / WhatsApp / card link); bank transfer stays available when card payments fail.
- **Each card says who pays** ("billed by Stripe / Twilio / your mail provider to you; AA charges nothing for this")
  and links to the vendor's own setup page. Help pages per connection (CRM-37b).
- **Disconnect** deletes the credential row (and with it the only copy of the secret), keeps the history, audits it.

## 3. AA system mail (closed list, AA's SES)

1. Invitations, sign-in and security mail to agency people (partner pool, ADR 0006b).
2. One-time codes to travellers: client portal sign-in and e-sign (ADR 0008a decision 4).
3. Operational alerts to agency people: morning digest (no PII), new inquiry, hold expiring, connection failed,
   AA incident.

Everything else to a traveller comes from the agency's mailbox or does not leave. One SES configuration set; per-tenant
suppression for the codes; display name carries the agency's name on traveller codes.

## 4. Cost (final design §8)

AA's AWS per month *(est.)*; only the changed lines.

| Line | Was | Now |
|---|---|---|
| Guardrails, SES, S3, logs, secrets, ECR, alarms | 4–6 / 10 / 30 | 4–6 / ≈ 9–10 / ≈ 20–30 (campaign volume leaves SES: about $0.10 per 1,000 mails, so ≈ −$0–10 at 50 agencies) |
| **Total AA AWS** | ≈ $13–22 / $84–97 / $319–344 | ≈ $13–22 / ≈ $83–97 / ≈ $309–344 |

Vendor lines that leave AA entirely:

| Conditional vendor line (final design §8) | Now |
|---|---|
| BoldSign ≈ $30/month if the insurer refuses self-built e-sign | $0 for AA: the agency's own account if it wants one |
| Twilio Tech Provider fallback (subaccounts, re-billed) | Removed; no AA Twilio account |
| Per-agency SES tenants / DKIM identities at Go-real | Removed |
| Stripe platform account (Connect) | Not needed in v1 |

Unchanged: Mapbox stays AA's line (AA token; decided S247): free tier about 50,000 web map loads a month, so Dev
costs $0; overage about $5 per 1,000 loads *(est.)*, watched by the existing budget alarms. CASA ($675–5,400/year, only if two-way mail sync is ever required, AA's OAuth app), the paid flight API
(approval first; now the agency's own account if it ever wants one), the AI line (AA's feature). The readiness
deltas (no +$38 line, `us.` +10 %, Cognito partner pool $0) apply as written there.

## 5. Effort (final design §7)

*(est.)* About **+0.5 session** net, inside W5–W6 (re-planned at S262 anyway):

| Card | Delta |
|---|---|
| CRM-17 | +0.25 (SMTP connector) − 0.1 (no platform sender) |
| CRM-23 | ≈ 0 (own-key path instead of Connect onboarding) |
| CRM-28 | 0 to build; removes the W8 clock risk (3–4 weeks Tech Provider) |
| CRM-31 | +0.25–0.5 (Connections page, tests, health checks, controller settings, acknowledgement) |
| CRM-36 | ≈ 0 (mailbox / SMTP send instead of a marketing set) |
| CRM-06, CRM-35 | +0.1 each at most |
| CRM-20/21b | 0 (maps stay AA's, as in the final design) |

## 6. Risks and open points (final design §9)

| Risk | Level | Mitigation |
|---|---|---|
| ~~Twilio requires the Meta Tech Provider programme~~ | — | Resolved by BYO (check 11). Residual (Low): Twilio's reply says the rule also covers software using customer-owned credentials → only the WhatsApp half of CRM-28 is re-opened; SMS unaffected |
| Agency setup friction: vendor sign-ups and reviews take days (WhatsApp sender approval, SMS brand / campaign review, Stripe verification) | Medium | Email-first onboarding; SMS, WhatsApp and cards are "Later"; per-connection help pages; plain-words vendor errors |
| An agency mishandles a key (wrong permissions, shared, leaked) | Medium | Restricted key with a permission probe; write-only fields; rotation guidance; decrypt-spike alarm; disconnect deletes the secret |
| Campaign volume limited by the agency's mailbox | Low | Spread over days (CRM-36); own email service by SMTP for volume |
| An agency thinks AA is responsible for its vendor or its legal duties | Medium | Acknowledgement at onboarding, Terms and DPA wording (Ms. Thư), sentences on each Connections card |

Open point 6 of §9.2: "Twilio ISV" is closed. The two choices this errata raised are decided (Nghiệp, S247,
22/10/2026): Stripe own restricted key first (§1, CRM-23) approved; maps BYO (§1, CRM-20/21b) reversed, maps stay
AA-provided (Mapbox, AA token). No open choices remain in this errata.
