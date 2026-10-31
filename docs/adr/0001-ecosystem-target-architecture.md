# ADR 0001 — Ecosystem target architecture: shared platform services and contracts between apps

- **Status:** Accepted (14/10/2026, tech lead, S235), together with the S235 ecosystem blueprint
  (`docs/audits/2026-10-14-S235-ecosystem-team-pilot/01-ecosystem-blueprint.html`). Proposed
  28/09/2026 (S199). See "Amendments (S235)" below.
- **Tightened by:** ADR 0008 (S237): decision 6 contracts are views only; new-app integration follows ADR 0008's gate and playbook.
- **Amended by:** [ADR 0001a](0001a-retire-acc1-llm-on-acc3-only.md) (S255, AA-998): decision 2, acc1 retired; LLM chat models run on acc3 only, no cross-account fallback.
- **Amended by:** [ADR 0009](0009-ai-platform-and-provider-gateway.md) (decisions 1–9, 13 and 14 Accepted 2026-10-31, S261): decision 2, the gateway covers every paid AI and data provider (LLM of every source and family, Jev, DataForSEO, Geoapify, Guardrails) for every app and stage; the direct Anthropic and OpenAI APIs are capped warm paths outside AWS; acc2 may serve chat models for eval, judge and validate stages only.
- **Amended by:** [ADR 0018](0018-lean-aws-account-model.md) (Accepted 2026-10-31, S262): the S235 amendment "Production also runs on acc2 … no new AWS account is created for any environment" is replaced: prod runs in its own account `aa-prod` inside an AA-owned AWS organization, in us-west-1.
- **Implemented by:** [ADR 0016](0016-one-design-system-guarded-kit-copies.md) (S252): decision 7 "one design system" through a canonical CIS kit core and guarded copies.
- **Update 2026-10-28:** decision 2: acc1 left the ecosystem (AA-998, S255). LLM calls run on acc3 only, and
  the fallback chain stays inside acc3; there is no cross-account fallback. Decision 8: an English page may have a
  Vietnamese translation next to it, `<name>.vi.md` ([STYLE, Language](../STYLE.md#language)).
- **Scope:** AA-Ecosys as a whole (AA-CIS-App, AA-TripPlanner-Web, AA-CIS-Infra, future AA-Booking).
  Repo-level ADRs (for example `apps/AA-CIS-App/docs/adr/0001..0004`) stay in their repos. This series
  covers only cross-repo decisions.

## Context

The review (`docs/architecture/ecosystem-review-2026-09.md`) found five problems that no single repo
can solve on its own:

- One tenant action triggered a platform-wide DataForSEO purchase, and nothing capped the spend
  ($49 in one day).
- Long LLM work runs as in-process tasks that die on deploy.
- New models are available only on acc3, and the current client and IAM cannot call them.
- TripPlanner can produce trips no AA tour can fulfil.
- AA-Booking has no defined contract with the rest of the ecosystem, and lives in another region and
  other accounts.

## Decisions

1. **CIS is the content system of record.**
   - Other apps consume a published **Catalog & Tour Graph read model** and versioned events.
   - Nobody reads CIS pipeline tables (`acp_*`, `*_aa_internal`) directly.
   - Existing read-only TripPlanner access is migrated to the read model.
2. **Single Model Gateway.** Every LLM, Jev and embedding call goes through one gateway with:
   - a DB model catalog (the only source for the admin dropdowns and the pricing);
   - stage routing, with a fallback chain and a shadow model;
   - three seams: `generate`, `decide`, `embed`;
   - the Bedrock **Converse API**;
   - a cost log for every call.

   New models (Sonnet 5, Opus 5.5, GPT-5.6 Luna, GPT-6 Astra) run on **acc3 only**. The fallback
   stays inside acc3 (previous model) until acc1 accepts the same agreements. The invoker IAM
   allow-list is changed together with the catalog.
3. **Durable jobs.**
   - Rewrite, write, research, atomize, rerun and extraction run on a durable job runner: a Postgres
     queue plus a worker service, pending the tech lead's choice versus SQS
     (a Postgres queue was chosen, ADR 0003).
   - Every job carries idempotency, retries, a reaper and per-provider concurrency caps.
   - The UI reads job status and never infers it from row state.
   - This replaces the Bedrock Batch dependency (AA-624) for the rerun.
4. **Cost guard.**
   - Every external spend (DFS, LLM, Jev) checks a DB-configured budget per run and per day, and stops
     hard when it is exceeded.
   - DFS research is admin-triggered and scoped; a tenant action never triggers it.
5. **Route-constrained, multi-tour trip planning.**
   - TripPlanner only offers destinations that keep the trip covered by a chain of **legs**. A leg is a
     day-span of a real AA tour; legs are chained at junctions (same or nearby destination) in the Tour
     Graph.
   - Combining several tours is allowed (decided 28/09/2026).
   - Drafts carry the leg chain, so AA-Booking can open a complete Trip Case.
6. **Contracts between apps.**
   - Versioned JSON contracts live in `docs/contracts/`.
   - AA-Booking shares the acc2 RDS (schema `booking`, decided 28/09/2026), so the transport is a
     **transactional outbox table** consumed by the receiving app's job runner, with an idempotency key.
   - Apps never write each other's schemas. They read only published views (read models) and
     `shared.*` golden records.
   - Each schema's migrations live in its owner repo; an app never migrates another app's schema.
     Owners, `shared.*` table owners and the per-owner version key (`NNN` / `tp-NNN` / `bk-NNN`):
     `docs/database/schema-ownership.md` (AA-684, 11/10/2026).
   - First contracts: `catalog.tour.*` (CIS → AA-Booking) and `inquiry.submitted` (TripPlanner →
     AA-Booking, carrying the multi-tour leg chain).
   - AA-Booking owns the customer identity (OTP). **Superseded S236 by ADR 0006:** one ecosystem identity on Amazon Cognito (staff, tenant users, travellers).
7. **One IaC repo, one design system.**
   - AA-CIS-Infra provisions AA-Booking inside acc2: ECS service, ECR, DB role, API route. There are no
     new accounts.
   - All frontends consume one token source and one shared component set.
     **How (S252):** [ADR 0016](0016-one-design-system-guarded-kit-copies.md): one canonical kit core in
     AA-CIS-App `frontend/app/_kit/core/`, guarded byte copies in the other apps, one token set (AA-994).
8. **Language.** Everything in Git is English, including root docs, READMEs and CONTEXT files.
   Session logs and the Notion memory stay in Vietnamese.

## Amendments (S235, 14/10/2026)

Approved by the tech lead with the S235 ecosystem blueprint:

- **Production also runs on acc2** ([account map](../onboarding.md)) when it comes. No new AWS account is created for
  any environment. *(Replaced by [ADR 0018](0018-lean-aws-account-model.md), accepted 2026-10-31: prod runs in its
  own account `aa-prod`.)* The old Quanskill AAA accounts (dev/stg/prod in ap-southeast-1) are **not part of the
  ecosystem**.
- **Dev hostnames are sub-domains of `lumiguides.it.com`** (pattern of `api-cis.lumiguides.it.com`,
  e.g. `api-booking.lumiguides.it.com`).
- **Frontend reviews happen on Vercel domains** (preview and project URLs); no custom domain is needed
  for review.

## Consequences

- **Positive:**
  - spend is bounded and visible;
  - deploys stop killing work;
  - new models are adopted by configuration, not code edits;
  - TripPlanner only sells what can be delivered;
  - AAA can start against stable contracts.
- **Negative / cost:**
  - one more ECS service (the worker);
  - a Gateway migration touching every LLM call site (done in phases, with the old path kept behind a
    flag until parity);
  - an outbox and webhook infrastructure to maintain;
  - the Jev dependency needs a DPA/ZDR agreement before tenant content is sent.
- **Rejected alternatives:**
  - direct cross-schema writes between apps. The database is shared on acc2, but each schema keeps a
    single writer;
  - separate AWS accounts and a separate region for AA-Booking (closed 28/09/2026);
  - waiting for Bedrock Batch (blocked by AWS with no date);
  - letting TripPlanner suggest any place (creates unsellable trips);
  - calling OpenAI models through the OpenAI API only (a second billing/key path, no acc3 governance).
