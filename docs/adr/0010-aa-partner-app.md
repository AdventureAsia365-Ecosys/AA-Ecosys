# ADR 0010 — AA-Partner: one app for partner agencies (CRM and tenant portal)

- **Status:** Proposed (22/10/2026, S247). Nghiệp accepts (design: S248).
- **Scope:** AA-Ecosys: the new public repo **AA-Partner** (CRM API, CRM web and client host, the tenant portal after
  the move), AA-CIS-App (portal code moves out; membership, catalog and AA content contracts), AA-Booking (B2B API),
  AA-CIS-Infra (ECS service, CloudFront, KMS, Cognito, DB owner `crm`, DB Migrate), the root repo (contracts, ADRs).
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
  studio, moved from CIS with history in P2a). One UI kit shared with CIS (byte-compare guard until a package exists).
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
guard inverted (final design §4.4).

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
sign-off that real net rates are entered.

## Consequences

- **Positive:**
  - one app, host, sign-in and sidebar for agencies; the CRM's privacy boundary does not depend on CIS deploys or
    the CIS task role;
  - every cross-app flow has a contract checked in CI;
  - CRM releases are not blocked by CIS content waves (each app's deploy guard checks its own job table).
- **Negative / cost:**
  - a fourth repo, service, pipeline and set of contracts to run;
  - AWS *(est., per month, design §8)*: Dev ≈ $13–22; 10 agencies ≈ $84–97 ($104–152 for a separate prod cell);
    50 agencies ≈ $319–344. AA's vendor cost is $0 (each agency pays its own Stripe, Twilio, mailbox);
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
- On acceptance: `docs/ecosystem-architecture.md` app row, `docs/database/schema-ownership.md` row for `crm` (with
  AA-932), index status here.
