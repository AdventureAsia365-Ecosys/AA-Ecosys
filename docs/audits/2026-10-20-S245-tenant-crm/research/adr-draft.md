# ADR 0010 (draft): AA-CRM, the tenant partner CRM as the fourth ecosystem app

> **Superseded draft (kept for the record).** This draft was written for option A before the real judge panel output
> reached the write-up. The panel split (product owner: CIS module; CTO: AA-CRM app) and `../README.md` §7 now
> recommends the CIS module with its own ECS service and a clean bounded context. Numbers 0010/0011 are also reserved
> for the GitHub App work (AA-901); the CRM ADRs are 0014 (Tenant CRM) and 0015 (B2B channel). Do not move this file
> into `docs/adr/`. If Nghiệp picks option A (D1 b), it is the starting point, renumbered to 0014.

- **Status:** Proposed (draft in an audit folder; not in `docs/adr/` until Nghiệp approves decision D1 and D2 of
  `../README.md` §14)
- **Date:** 20/10/2026 (S245)
- **Issue:** AA-821 (Jira PR-19)
- **Amends:** ADR 0008 §8 (tenant CRM placement and the "no AA app reads `crm.*`" rule); data standards DM-6.1, DM-6.8,
  KEY-6, SEC-12
- **Implements:** ADR 0003a (per-owner job tables), ADR 0004b (per-app security groups), ADR 0005 decision 9 (B2B
  resale), ADR 0006 decision 3 (tenant membership is the boundary)
- **Number:** 0009 is reserved for the AI platform (AA-804). 0010 is the next free number at the time of writing; the
  number is final only at merge.

## Context

Ms. Thư asked for a CRM that partner travel agencies (tenants) use with their own B2C travellers (Jira PR-19, spec
`docs/research/partner-crm-spec.md`). On 19/10/2026 she placed it inside the tenant portal and dropped the spec's
40-week plan. On 20/10/2026 (S245) Nghiệp decided to design and build the complete product from the spec, without an
MVP cut: 5 foundation modules (F1–F5) and 18 feature modules.

ADR 0008 §8 assumed a smaller CRM: "research first; if built, it is a CIS module with its own `crm` schema". The
complete product is a different shape:

- three public surfaces (embeddable intake, no-login proposal links, a client portal);
- six inbound webhook sources (Stripe, a VN payment gateway, Twilio/Meta, Microsoft Graph, Gmail Pub/Sub, e-sign);
- a per-agency key vault (KMS), an in-VPC PII scrubber, and an agency-visible audit log;
- contracts with Booking (B2B price, availability, holds, ops release) and TripPlanner (visual builder).

Running all of that inside the CIS API process would couple CRM releases to CIS content waves (DM-11.4 blocks CIS
deploys while `shared.job` holds jobs), give the CIS task role read access to the `crm_app` secret, and put tenant PII
decryption in the same blast radius as the content pipeline. Privacy is the product's main promise to agencies.

## Decision

1. **New app `AA-CRM`** in org AdventureAsia365-Ecosys, same stack as AA-Booking (FastAPI + asyncpg, Next.js on
   Vercel). Own ECS service on the shared cluster, own REST API (`api-crm` host) on the shared VPC link, own per-app
   security group (ADR 0004b), own ECR repo with immutable SHA tags, own `crm/dev/*` secrets prefix, `App=crm` tags.
2. **Data:** schema `crm`, key space `crm-NNN`, owner `crm_owner` (NOLOGIN), runtime `crm_app` (LOGIN, connection
   limit set in git), registered in `infra/AA-CIS-Infra/db/owners.yaml`; migrations only through Infra DB Migrate.
   NOLOGIN roles `crm_ai_reader` and `crm_insights` (reached by `SET LOCAL ROLE` from `crm_app`) see only the
   pseudonymous views; `crm_staff` is reached only through an agency-granted, expiring support grant. FORCE RLS on
   every tenant table from `crm-001`, NULLIF template, fail closed. Job table `crm.job` from the ADR 0003a template.
3. **UI placement:** the agent UI is a Next.js app in the AA-CRM repo served **inside the portal host** as a Vercel
   multi-zone (`/portal/crm/*`), so tenants see one portal and one sign-in. Travellers use a separate client app with
   signed, expiring, hashed link tokens. Travellers get no Cognito accounts (the EXTERNAL pool is AA's traveller pool,
   ADR 0006).
4. **Identity:** tenant users sign in on Cognito EXTERNAL through `cis-portal`; the CRM checks
   `catalog.v_tenant_member` (created by AA-813) on every request, then its own `crm.member` role
   (owner / agent / assistant, margin visibility). The membership row, never the token, is the boundary.
5. **Integration only through versioned contracts** (`docs/contracts/`):
   - CIS → CRM: `catalog.v_tenant_member`, `catalog.v_tenant`, `catalog.v_tenant_content_piece`, `catalog.v_tour*`,
     `catalog.graph`.
   - CRM ↔ Booking: Booking B2B API (IAM-authorised; price, availability, holds, requests) and
     `booking.v_b2b_status_outbox` (`booking.b2b_status.v1`); ops release `crm.v_ops_release_outbox`
     (`crm.ops_release.v1`), after which Booking holds its own copy with a 90-day TTL and reports the purge back.
   - CRM ↔ TripPlanner: the `/builder` route is UI only; state persists in `crm.*` through `crm.builder.v1`, authorised
     by a short-lived CRM-signed builder token.
6. **Two contract exceptions to "no AA app reads `crm.*`"** (amends ADR 0008 §8 and DM-6.8): `booking` may SELECT
   `crm.v_ops_release_outbox` (consented, minimised payload); `cis_app` may SELECT `crm.v_aa_insights_k10` (groups
   with n < 10 suppressed). No other grant on `crm.*` to any other app role.
7. **Privacy foundation** (detailed in a companion ADR, proposed 0011): per-agency KMS key with encryption context
   `tenant_id` and optional BYOK; AES-256-GCM field encryption with HMAC blind indexes; crypto-shred on offboarding;
   pseudonymous profile; three-pass scrubber before any LLM call; per-tenant hash-chained `crm.access_event` written
   in the same transaction as each vault read. The spec's F1 wording "no access outside the agency, AA included"
   becomes "restricted to the CRM runtime and logged; agency-revocable with BYOK".
8. **AI:** CRM stages call Bedrock on acc3 through the gateway only, with a `us.` geographic profile, a model that
   permits data retention mode `none` (not Fable 5/5.1), enforced by SCP. OpenAI and Jev are excluded from CRM routes.
   `shared.llm_call_log` gets stage and cost, never text (DM-6.4).
9. **Real traveller data only on prod** (C7.1a). The pilot waits for the AA-880 prod environment (ADR 0012).

## Consequences

- One more repo, ECS service, REST API, Vercel project pair and CI pipeline to run (~$20/month on Dev for the API
  task; the Presidio sidecar ~$40–50/month is needed in any placement).
- CRM deploys have their own guard (`crm.job` idle), independent of CIS waves.
- The CIS task role never holds a CRM secret; the isolation probe gains `crm` cells (`cis_app`, `booking`,
  `tripplanner` get 42501 on `crm.*` except the two contract views).
- `max_connections` budget (C2.2) needs a `crm_app` row with an offset elsewhere, or a t4g.medium on Dev.
- Data standards bump: DM-6.1 adds `pii:gov_id` and `pii:special`; DM-6.8 / KEY-6 / SEC-12 drop the obsolete
  "`aa_cis_admin` runtime can read `crm.*`" caveat (X1 done) and list the two exceptions.
- Companion ADRs: 0011 tenant traveller data protection; 0005a Booking B2B channel, availability/hold and ops release
  (Booking repo or root, per the ADR placement rule: ≥2 repos → root); 0006b CRM roles and traveller signed links; an
  Infra ADR for the KMS key provisioner.

## Alternatives considered

- **CRM module inside AA-CIS-App (ADR 0008 §8 as written).** Same scope and nearly the same cost; most reuse.
  Rejected for release coupling to CIS waves, a shared task role and process for PII decryption, and the X1 CIS
  migration freeze. The `crm-NNN` key space keeps a later move cheap either way.
- **Integrate the agency's own CRM (HubSpot / Zoho / Pipedrive); AA only as lead source.** Cheapest (≈3–4 sessions)
  but does not deliver the spec (interactive proposal on AA inventory, privacy by architecture, ops release,
  insights). Kept inside AA-CRM as an export path (`crm.integration_link` + outbox).
