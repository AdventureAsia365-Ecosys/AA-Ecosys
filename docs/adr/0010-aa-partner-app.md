# ADR 0010 — AA-Partner: one app for partner agencies (CRM and tenant portal)

- **Status:** Accepted (22/10/2026, S247, Nghiệp), decision 9 included. Decision 9 (integrations are
  bring-your-own; shared responsibility) added in S247 before acceptance, from Nghiệp's product direction of the same
  day; it is part of this ADR, not a separate amendment. Two points in decision 9 decided by Nghiệp, S247
  (22/10/2026): Stripe v1 uses the agency's own restricted key (approved); maps stay AA-provided (the BYO-maps
  proposal is reversed).
- **Scope:** AA-Ecosys: the new public repo **AA-Partner** (CRM API, CRM web and client host, the tenant portal after
  the move), AA-CIS-App (portal code moves out; membership, catalog and AA content contracts), AA-Booking (B2B API),
  AA-CIS-Infra (ECS service, CloudFront, KMS, Cognito, DB owner `crm`, DB Migrate), the root repo (contracts, ADRs).
- **Amended by:** [ADR 0010a](0010a-content-studio-partner-sign-in.md) (S252, AA-979 P2b: the Content studio signs in
  through the partner pool with a CIS token exchange; studio invitations are CIS-created and CRM-delivered; the agency
  host is cut over by one DNS value).
- **Amends / Supersedes:** none directly. It is the placement decision that
  [ADR 0008a](0008a-crm-separate-app-exceptions.md) points to.
- **Implements:** ADR 0008 decision 2 (gate answer 3) and its 12-step playbook, with the exceptions in ADR 0008a;
  ADR 0003a (job table per owner); ADR 0004b (one security group per caller); ADR 0002 (only CIS writes content);
  ADR 0005 / [0005a](0005a-b2b-resale-warn-and-vnd.md) (Booking owns prices); ADR 0006 /
  [0006b](0006b-partner-pool-and-mfa.md) (identity).
- **Design and evidence:**
  [`final/crm-design-final.md`](../audits/2026-10-21-S246-crm-design-v3/final/crm-design-final.md) (accepted S246,
  D1–D8), [`design-v3.md`](../audits/2026-10-21-S246-crm-design-v3/design-v3.md) and its lanes; spec
  [`docs/research/partner-crm-spec.md`](../research/partner-crm-spec.md) (errata at its end); v2.2 base decisions
  ([`inputs/crm-v2.2-simplified.md`](../audits/2026-10-21-S246-crm-design-v3/inputs/crm-v2.2-simplified.md), D8).
- **Related Linear:** AA-821 (epic, Jira PR-19) and its 53 children AA-928…AA-980; AA-933 (repo), AA-979 (portal
  move), AA-978 (membership feed), AA-972…AA-977 (Booking and CIS lanes).

## Context

Ms. Thư's spec asks for a CRM that AA gives to partner travel agencies to run their own B2C clients, with live AA
supply inside it and privacy by architecture. On 20/10/2026 (S245) Nghiệp chose to build the complete product (23
modules, no MVP cut) as **its own app**, and to move the existing tenant portal (Content studio,
`apps/AA-CIS-App/portal/`, deployed separately since AA-885) into the same app so that an agency has one host, one
sign-in and one sidebar.

What exists today (checked 21/10/2026, final design §4.1): the portal signs in with the tenant API key through a BFF;
AA-Booking has no departures, holds, B2B API, VND selling currency or cancellation-fee policy; CIS has no tenant
membership table. The repo AA-Partner does not exist yet.

## Decisions

### 1. A fourth app, AA-Partner, in its own public repo

- Repo **AA-Partner** in org AdventureAsia365-Ecosys, public, same stack as AA-Booking: `api/` (FastAPI, Pydantic v2,
  asyncpg with plain SQL, in-process `crm.job` worker), `web/` (Next.js CRM UI and the client host), `portal/` (Content
  studio, moved from CIS with history in P2a). One UI kit shared with CIS (byte-compare guard until a package exists;
  superseded S252 by [ADR 0016](0016-one-design-system-guarded-kit-copies.md): `portal/` and `web/` vendor the canonical
  CIS kit core with integrity and provenance checks, no package).
- Branch protection and required CI from the first commit, including the public-repo scan for account IDs, ARNs and
  network IDs (DM-6.10) and an import-boundary test (no CIS or TripPlanner backend modules).
- A `CONTEXT.md` at the repo root from the first PR (AA-933); `docs/ecosystem-architecture.md` gets the app row when
  this ADR is accepted.

### 2. Runtime and hosts

- One ECS Fargate service on the shared cluster with its own security group (ADR 0004b), its own immutable ECR repo
  (SHA tags), its own `crm/<env>/*` secrets and `App=crm` cost tags.
- Hosts: the agency host `portal.` (Dev: `partner-dev.` until P2b), the client host `go-dev.` for travellers, and
  staff routes for AA (`crm-ops`, `crm-support`). Cookies are host-only, so agency and client sessions never mix.
- Edge: CloudFront → VPC origin → internal ALB → Fargate, proven by the AA-931 spike before AA-933. If the spike
  fails, the fallback is the pattern CIS and Booking use (API Gateway REST + VPC link).
- App-level rate limits on public and sign-in routes from AA-933 (CloudFront → VPC origin bypasses API Gateway
  throttling; WAF arrives with the first real agency).

### 3. Data

- Schema `crm` under ADR 0008 / 0008a: owner `crm_owner`, runtime `crm_app` (limit 6, pool 3), NOLOGIN readers
  `crm_ai_reader`, `crm_insights`, `crm_support_reader` and `crm_eraser` reached only by `SET LOCAL ROLE` inside
  `tenant_tx()`; ENABLE + FORCE RLS on every tenant table from `crm-001`; trash columns from the first migration;
  status as `TEXT + CHECK` plus a transitions table.
- Privacy foundation (spec F1–F5, design v3 §4): one KMS data key per environment plus `ingest` and `seal` keys, one
  data key per agency per purpose, field encryption with blind indexes for exact search, client-side document
  encryption, an append-only agency-visible audit exported hourly to Object Lock buckets, verified deletion through
  `crm.erase_subject()`.
- **Dev holds synthetic agencies only** (`tenant.is_synthetic = true` enforced). Prod placement (a prod cell or the
  shared prod RDS) is decided at Go-real (AA-980), after ADR 0012.

### 4. Integration only through versioned HTTP contracts

| Contract | Producer → consumer | File |
|---|---|---|
| `booking.b2b.v1` | AA-Booking → AA-Partner | [`docs/contracts/booking.b2b.v1.openapi.yaml`](../contracts/booking.b2b.v1.openapi.yaml) |
| `catalog.http.v1` | AA-CIS-App → AA-Partner | [`docs/contracts/catalog.http.v1.openapi.yaml`](../contracts/catalog.http.v1.openapi.yaml) |
| `tenant.membership.v1` | AA-CIS-App → AA-Partner | [`docs/contracts/tenant.membership.v1.openapi.yaml`](../contracts/tenant.membership.v1.openapi.yaml) |
| `crm.ops.v1` (`/crm/ops/v1`) | AA-Partner → AA-CIS-App admin | [`docs/contracts/crm.ops.v1.openapi.yaml`](../contracts/crm.ops.v1.openapi.yaml) |
| `tenant.entitlements.v1`, `cis.tenant-api.v1`, `crm.insights.v1` | CIS → AA-Partner; AA-Partner → CIS | added by AA-939, AA-978, AA-966 |

- Service calls use the M2M pool (ADR 0006b decision 7) and `X-AA-Tenant-Id` on every B2B call.
- The root CI workflow `contracts.yml` validates every contract and its samples, and enforces the design's forbidden
  fields: no trip counts, revenue or PII in `crm.ops.v1`; no `supplier_net` in `booking.b2b.v1`.
- A breaking change is a new major served in parallel (default 30 days), as for the view contracts (ADR 0008
  decision 5).

### 5. Who owns what

| Data or behaviour | Owner |
|---|---|
| Agency clients (travellers), trips, proposals, the agency's own suppliers and money records, CRM roles (owner / agent / assistant), the agency audit | AA-Partner (`crm`) |
| Tenants and agency membership, Content studio roles (owner / editor / viewer), Content studio data, AA-authored prep packs, starter templates and campaign blocks (ADR 0002) | AA-CIS-App |
| Prices, B2B price lists, FX, departures, capacity, holds, cancellation-fee policy, B2B trip cases | AA-Booking (ADR 0005, 0005a) |
| Identity pools and clients | AA-CIS-Infra (ADR 0006, 0006b) |

A CIS event can never grant a CRM role; one person can hold both a Content studio role and a CRM role.

### 6. Portal move, staged

P2a (code move with history into `AA-Partner/portal/`, Vercel and API-key sign-in kept) → P1 (membership feed,
AA-978) → P2b (host to CloudFront → Fargate, partner-pool sign-in, re-enrolment by invitation, 301 for `/trip/*`),
Vercel kept at least 7 calendar days after P2b with a rollback drill, then the CIS copy is deleted and the AA-885
guard inverted (final design §4.4). How P2b signs people in, re-enrols them and cuts the host over:
[ADR 0010a](0010a-content-studio-partner-sign-in.md) (S252; status of the stage: prepared, cutover not run yet).

### 7. "CIS App first" risk

Moving Content studio into AA-Partner, and giving the CRM about 40–45 sessions of work, can pull CIS work into the
new repo and starve CIS (the standing rule: CIS App first, parallel lanes agreed since S234). Rules:

- Content studio **business logic and data stay in the CIS API**. AA-Partner's `portal/` is UI only: a new Content
  studio capability is a CIS API change first and an AA-Partner page second. A CIS issue is never moved to the
  AA-Partner project to be built there unless it is UI-only work on the moved portal.
- About 2.8 CRM sessions a week, the rest for CIS / Booking / TripPlanner; the CIS / CRM split is stated in every
  session plan (D5). At most about 3 CRM items per session (including Lane B and Lane P), at most one critical-path
  step per session.
- One session of portal feature freeze before P2a; the P2a → P2b gap stays at most 3 sessions.
- Signal for Nghiệp: two sessions in a row with no CIS item merged, or a CIS issue re-labelled to AA-Partner without
  being UI-only.

### 8. Go-real gate

No real agency, traveller or payment before W8 (AA-980): prod placement, prod partner pool, WAF, ECS exec off, an
independent pentest, vendor verifications, Stripe live per agency, DPA and the public data page, and the ops owner's
sign-off that real net rates are entered. Under decision 9, "vendor verifications" means AA's own connector
registrations only (the Google OAuth client and the Microsoft app); "Stripe live per agency" means the agency's own
live key or account, connected and tested by the agency.

### 9. Integrations are bring-your-own; shared responsibility

Product direction from Nghiệp (S247, 22/10/2026), binding for every CRM module: build a product agencies can really
use, and leave to the agency what is the agency's by nature — its vendor accounts, its legal duties to its own
travellers, and its own registrations — as other SaaS companies do in their Terms and data processing agreements.
Platform security stays AA's engineering job.

**Rules.**

- **BYO integrations.** Every external vendor the CRM talks to on the agency's behalf is the **agency's own account**:
  its Twilio account (SMS) and WhatsApp Business sender (registered by the agency through Twilio Self Sign-up, brand
  and campaign registrations included), its Stripe account (the agency is the merchant of record), its mailbox (Gmail
  or Microsoft 365 through OAuth, or SMTP), its e-sign provider if it ever wants one instead of the built-in e-sign,
  a later payment gateway or flight-status service. **AA holds no master vendor account on an agency's behalf**: no
  Twilio subaccounts, no Meta Tech Provider enrolment, no Stripe Connect platform in v1, no shared SMTP relay for
  client mail.
- **Stripe v1 = the agency's restricted key** (decided: Nghiệp, S247, 22/10/2026). The agency pastes a restricted key
  (`rk_`) it creates in its own Stripe Dashboard; AA runs no Stripe platform or Connect account. Connect stays a later
  adapter option.
- **Maps are AA's product feature, not BYO** (decided: Nghiệp, S247, 22/10/2026; reverses the BYO-maps proposal). A
  map is a product feature, not a vendor account that carries legal duties, so AA provides it: Mapbox under AA's own
  public token, URL-restricted to the CRM hosts. Agencies connect no map token. Mapbox stays an AA sub-processor
  (readiness check 10). Cost *(est.)*: Mapbox's free tier (about 50,000 web map loads a month) covers Dev, so $0;
  overage about $5 per 1,000 loads, watched by the existing budget alarms.
- **AA builds the connectors.** A setup wizard ("Connections", AA-962) with a test button and a health status per
  connection; credentials stored encrypted under the agency's `integration` data key (KeyProvider, AA-934), write-only
  in the UI, decrypted only in the dispatcher, webhook and health-check paths, every change in the agency's audit; owner-only
  changes; AA support (L2) and the L1 console can never read or change them.
- **AA keeps its own connector identities.** The Google OAuth client and the Microsoft app registration are AA's and
  AA verifies them (W8). They are how the CRM asks the agency for access, not an account held for the agency.
- **AA's SES sends system mail only**: invitations and security mail to agency people, one-time codes to travellers
  (client portal sign-in, e-sign), and operational alerts to agency people. Mail to travellers (proposals, payment
  reminders, Stage 3 nudges, portal invitations, campaigns) leaves from the agency's own mailbox or not at all; there
  is no platform-sender fallback. Inbound forward-in through AA's SES receipt rule stays (receive-only, AA domain).
- **AI is AA's feature, not BYO.** CRM AI runs on AA's Bedrock (ADR 0008a decision 5), AA pays inside the per-agency
  cap, AI is off until the owner turns it on, a person approves every send. No agency-supplied LLM keys.
- **Data roles.** The agency is the **controller** of its travellers' data (consent, lawful basis, privacy notice,
  replies to data-subject requests, retention choices inside the product's limits, notifying its regulator and
  travellers of a breach). AA is the **processor** (acts on the agency's instructions, tools for those duties,
  forwards any request it receives, notifies the agency of a breach without undue delay, lists its sub-processors).
  The agency's vendors are the agency's processors, not AA's sub-processors.
- **Legal wording is Ms. Thư's call.** The Terms clauses, the DPA wording, the in-app acknowledgement and whether
  counsel reviews them are a proposal for her
  ([`proposal-thu.md`](../audits/2026-10-22-S247-crm-byo/proposal-thu.md)); the build does not wait on the wording.
- "BYO" here is about **vendor accounts**. Customer-managed encryption keys (BYOK) stay out of v1, unchanged.

**Responsibility matrix.**

| Area | Agency | AA (platform engineering) | Ms. Thư (wording) |
|---|---|---|---|
| Vendor accounts (Twilio, WhatsApp sender, Stripe, mailbox, e-sign provider, later gateways; not maps, which AA provides) | Opens, verifies, pays and registers them (WhatsApp sender, SMS brand and campaign, Stripe identity checks); accepts the vendor's terms; keeps the vendor log-ins secure | Connectors, setup wizard, test buttons, health checks, encrypted credential storage, clear errors when a vendor refuses | Terms clause on third-party services and customer-owned accounts |
| Messaging rules (WhatsApp opt-in and templates, SMS rules per country, opt-out words) | Gets opt-in, writes and gets templates approved, follows the vendor's and the country's rules | Enforces the 24 h window and template-only sends, records opt-in and opt-out, blocks sends without consent | Acceptable-use wording |
| Payments | Merchant of record: refunds, disputes, payouts, fees, its own tax invoices | Payment links on the agency's account, no stored cards, verified webhooks, refund approval matrix | "AA is not a party to the agency's payments" wording |
| Email | Its mailbox, sending limits, its domain's sender records, what it writes | Send-as and SMTP connectors, forward-in, held-until-reconnect, system mail from AA's domain | — |
| Travellers' personal data (controller duties) | Privacy notice, lawful basis and consent text, data-subject replies, retention choices, breach notices to its regulator and travellers | Consent records, per-traveller export and verified erasure, retention settings inside fixed limits, request forwarding, breach notice to the agency, DPA annex and sub-processor list | DPA and Terms wording; whether counsel is needed |
| Platform security | Who it invites and which role, its people's second factors, rotating vendor credentials when staff leave | Encryption and keys, MFA, tenant isolation, access control, audit, backups, AI PII filter, security review and pentest, incident response | Public data page wording |
| Content shown to travellers (terms, waivers, consent text) | Its own documents and their legal fit for its trips | Versioning, signing, sealing, storage; AA templates are examples only | Whether templates carry a "not legal advice" note |
| AI | Turns it on, reviews every draft before sending | Runs and pays for it, filters PII first, caps and logs it | AI wording in the Terms |

**Consequences per module** (details: design errata
[`final/errata-s247-byo.md`](../audits/2026-10-21-S246-crm-design-v3/final/errata-s247-byo.md)):

| Module (issue) | Change |
|---|---|
| CRM-06 KeyProvider (AA-934) | `integration` data key covers every provider (Twilio, Stripe key + webhook secret, OAuth refresh tokens, SMTP, e-sign; no map token, maps are AA's); serializer test that no credential ever leaves the API |
| CRM-17 email (AA-945) | Gmail, Microsoft 365 **and SMTP**; `allow_platform_sender` removed; a dead mailbox holds client mail; system mail list closed |
| CRM-23 payments (AA-952) | Agency's own Stripe through its **restricted key** in v1 (decided: Nghiệp, S247; no AA platform account); Connect kept as a later adapter option; VN agencies manual |
| CRM-25 contracts and waivers (AA-955) | Built-in e-sign stays AA's feature; the BoldSign slot becomes the agency's own provider account; terms and waiver text are the agency's |
| CRM-28 WhatsApp + SMS (AA-958) | Agency-owned Twilio only; subaccount / Tech Provider fallback removed; AA never onboards a sender |
| CRM-31 onboarding (AA-962) | "Connections" wizard with test sends and health status; controller settings (privacy notice link, data-request contact, retention choices); owner acknowledgement of the shared responsibility |
| CRM-36 campaigns (AA-968) | Sent from the agency's mailbox or its own email service by SMTP; no `crm-marketing` SES set |
| CRM-03 infra (AA-931) | SES grants for system mail and the inbound receipt rule only; no per-agency SES identities |
| CRM-20 / CRM-21b maps (AA-948, AA-950) | Mapbox with an AA token, URL-restricted to the CRM hosts (decided: Nghiệp, S247); no agency map connection. The CRM-21a day-list builder stays the core; the CRM-20 builder map is an enhancement that does not block M3 |
| CRM-33a AI (AA-964) | Unchanged in scope: AA's feature, AA's account |
| CRM-35, CRM-37b, CRM-38 (AA-967, AA-970, AA-980) | Data-request tools for the agency; sub-processor page lists AWS and Mapbox (plus conditional AA tools) only; W8 verifications = AA's OAuth apps |

**Other ADRs.** [0008a](0008a-crm-separate-app-exceptions.md) decision 1 (controller / processor) and decision 5 (own
LLM gateway) are unchanged and point here for the matrix. [0006b](0006b-partner-pool-and-mfa.md) is unchanged:
mailbox and calendar OAuth grants are integration credentials, never a sign-in; the partner pool stays the only human
sign-in, and its invitation mail is AA system mail. [0005a](0005a-b2b-resale-warn-and-vnd.md) is not affected
(AA↔agency settlement for AA lines stays outside the CRM).

## Consequences

- **Positive:**
  - one app, host, sign-in and sidebar for agencies; the CRM's privacy boundary does not depend on CIS deploys or
    the CIS task role;
  - every cross-app flow has a contract checked in CI;
  - CRM releases are not blocked by CIS content waves (each app's deploy guard checks its own job table).
- **Negative / cost:**
  - a fourth repo, service, pipeline and set of contracts to run;
  - AWS *(est., per month, design §8)*: Dev ≈ $13–22; 10 agencies ≈ $84–97 ($104–152 for a separate prod cell);
    50 agencies ≈ $319–344. AA's vendor cost is $0 (each agency pays its own Stripe, Twilio, mailbox); under
    decision 9 the conditional vendor lines BoldSign and Twilio Tech Provider re-billing leave AA too. Mapbox stays
    AA's: $0 inside the free tier (about 50,000 web map loads a month), overage about $5 per 1,000 loads, watched by
    the existing budget alarms;
  - decision 9 moves work to the agency (vendor sign-ups and registrations) and to the product (a setup wizard with
    tests and health checks, clear error states); an agency without a connected mailbox cannot email its travellers
    from the CRM, by design;
  - the portal move is a risky step for live tenants (mitigated by decision 6).

## Alternatives considered

- **CIS module with its own ECS service** (S245 panel). Rejected by the owner (S245 round 2): shared repo, shared
  deploy guard and CIS task role, and the portal still had to leave CIS.
- **CRM UI as a Vercel multi-zone inside the CIS portal** (S245 draft). Rejected: keeps two sign-ins and two apps for
  one agency, and the portal moves anyway.
- **Buy (HubSpot / Zoho) and integrate.** Rejected in the S245 research benchmark
  ([`2026-10-20-S245-tenant-crm/README.md`](../audits/2026-10-20-S245-tenant-crm/README.md)): neither models tours
  or pax, so live AA supply cannot sit inside the proposal; no per-agency privacy split; a per-seat price on every
  agency.

## Follow-ups

- AA-933: repo, `CONTEXT.md`, CI, health routes. AA-932: infra and DB owner. AA-931: CloudFront → VPC origin spike.
- Decision 9: the design errata above; Ms. Thư's answers to the proposal; the AA-930 readiness note (check 11
  resolved by BYO); AA-929 checks whether data standards DM-6/DM-7 need a line for "agency-owned processors".
- On acceptance: `docs/ecosystem-architecture.md` app row, `docs/database/schema-ownership.md` row for `crm` (with
  AA-932), index status here.
