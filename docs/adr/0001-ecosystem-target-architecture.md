# ADR 0001 — Ecosystem target architecture: shared platform services and contracts between apps

- **Status:** Proposed (28/09/2026, S199). Accepted once Nghiệp signs off the open decisions in
  `docs/architecture/ecosystem-review-2026-09.md` §10.
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
     queue plus a worker service, pending Nghiệp's choice versus SQS.
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
   - First contracts: `catalog.tour.*` (CIS → AA-Booking) and `inquiry.submitted` (TripPlanner →
     AA-Booking, carrying the multi-tour leg chain).
   - AA-Booking owns the customer identity (OTP).
7. **One IaC repo, one design system.**
   - AA-CIS-Infra provisions AA-Booking inside acc2: ECS service, ECR, DB role, API route. There are no
     new accounts.
   - All frontends consume one token source and one shared component set.
8. **Language.** Everything in Git is English, including root docs, READMEs and CONTEXT files.
   Session logs and the Notion memory stay in Vietnamese.

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
