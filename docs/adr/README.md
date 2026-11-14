# Ecosystem ADRs

Cross-repo architecture decisions for AA-Ecosys (AA-CIS-App, AA-TripPlanner-Web, AA-Booking,
AA-CIS-Infra). Decisions that affect one repo only stay in that repo's `docs/adr/`; infrastructure-only
decisions go to `infra/AA-CIS-Infra/docs/adr/` (rule: `skill/ai-nghiep/references/adr.md`).
An amendment is a separate file `<nnnn>a-<slug>.md` and the amended ADR carries a pointer to it.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-ecosystem-target-architecture.md) | Ecosystem target architecture: shared platform services and contracts between apps | Accepted (tightened by 0008, amended by 0001a, 0009 d2, 0018 and 0019) |
| [0001a](0001a-retire-acc1-llm-on-acc3-only.md) | Amendment: retire acc1; LLM chat models run on acc3 only, no cross-account fallback (AA-998) | Accepted (amended by 0009 d14) |
| [0002](0002-only-cis-writes-content.md) | Only CIS writes content; other apps read it through views | Accepted |
| [0003](0003-one-durable-job-model.md) | One durable job model for all deferred work | Accepted (amended by 0003a) |
| [0003a](0003a-per-owner-job-tables.md) | Amendment: one job table per owner schema, from a shared DDL template | Accepted |
| [0004](0004-aa-booking-stack-and-bootstrap.md) | AA-Booking: stack, repo layout, runtime and bootstrap on acc2 | Accepted (amended by 0004a, 0004b, 0019) |
| [0004a](0004a-supply-content-ownership.md) | Amendment: supply data in Booking, customer-facing supply content in CIS | Accepted |
| [0004b](0004b-per-app-security-groups.md) | Amendment: one security group per caller (per-app network isolation) | Accepted |
| [0005](0005-pricing-and-supplier-rates.md) | Pricing and supplier rates | Accepted (amended by 0005a, 0005b, 0019) |
| [0005a](0005a-b2b-resale-warn-and-vnd.md) | Amendment: B2B resale by partner agencies (warn below the "from" price, no subscription line, VND quotes) | Accepted (amended by 0005b, 0019) |
| [0005b](0005b-price-versions.md) | Amendment: price versions: no overwrite, a second person publishes, quotes and agency tariffs pin a version id, confirmed bookings never repriced (one contract surcharge line), the travel date decides season and version; season calendars and yearly holiday events, versioned Excel, provisional prices on request only, 12 pricing policy parameters with defaults; `booking.b2b.v1` 1.9 (AA-1091; design: [S278 advisory](../audits/2026-11-12-S278-pricing-advice/README.md)) | Proposed (2026-11-12, S278; d1–d15) |
| [0006](0006-ecosystem-identity.md) | Ecosystem identity on Amazon Cognito (staff, tenant users, travellers) | Accepted (amended by 0006a, 0006b, 0019) |
| [0006a](0006a-identity-phase1-amendments.md) | Amendment: identity Phase 1 as shipped (CIS staff on Cognito WORKFORCE) | Accepted |
| [0006b](0006b-partner-pool-and-mfa.md) | Amendment: a partner pool with required MFA for agency people, and an M2M pool for service calls | Accepted (A1 S263: `AdminDeleteUser` for never-signed-in accounts) |
| [0007](0007-place-pipeline-in-cis.md) | Place pipeline in CIS: `geo` schema, `catalog.*` views, background jobs | Accepted |
| [0008](0008-new-app-integration-and-data-platform-rules.md) | New-app integration and data platform rules | Accepted (amended by 0008a) |
| [0008a](0008a-crm-separate-app-exceptions.md) | Amendment: the partner CRM is a separate app; traveller OTP and an own LLM gateway as playbook exceptions | Accepted |
| [0009](0009-ai-platform-and-provider-gateway.md) | AI platform and provider gateway: one gateway for every paid AI and data provider (LLM all sources and families, Jev, DataForSEO, Geoapify), every app and stage; on acceptance amends CIS ADRs 0005 d4/d9, 0006 §4–5, 0008 and 0012; root ADRs 0001 d2, 0001a d1–2, 0008 d5 and 0018 (AA-804; design: [S261 v2](../audits/2026-10-31-S261-ai-gateway-design-v2/README.md)) | Accepted 31/10/2026 (decisions 1–9, 13, 14, UI); 10–12 Proposed; amended by 0020 |
| [0010](0010-aa-partner-app.md) | AA-Partner: one app for partner agencies (CRM and tenant portal) | Accepted (amended by 0010a, 0019) |
| [0010a](0010a-content-studio-partner-sign-in.md) | Amendment: Content studio sign-in through the partner pool and a CIS token exchange; studio invitations CIS-created and CRM-delivered (AA-979 P2b) | Proposed (amended by 0019: decisions 1 and 6 superseded) |
| [0011](0011-github-app-identity-and-merge-rights.md) | GitHub App identity for agents and bots, and merge rights per risk tier | Proposed (amended by 0011a; S280: scope covers six repos and the template repo) |
| [0011a](0011a-ci-bot-merges-copy-and-dump-prs.md) | Amendment: ci-bot opens and merges migration-copy PRs in AA-CIS-Infra and schema-dump PRs in the root repo (AA-993, needed by 0017) | Proposed |
| [0012](0012-environment-model.md) | Environment model: Dev and prod on the infrastructure account (acc2), isolated per environment; Terraform roots, the `prod` GitHub environment rename, promotion, data between environments, go-live trigger (AA-880) | Accepted (S257; build at the go-live date; decisions 1, 2, 5 superseded by 0018) |
| [0014](0014-repo-visibility-and-github-plan.md) | Repo visibility and GitHub plan: app repos public, root and Infra private, GitHub Free | Proposed (amended S247: root + Infra public for now; S248: switch precondition, AA-981; S280: public template repo, AA-1102) |
| [0015](0015-tour-liveness-and-retirement-propagation.md) | Tour liveness and retirement propagation: one CIS-owned served state per catalog key, one write service, a tombstone/outbox for the other apps (AA-986; design: [S248 audit memo](../audits/2026-10-23-S248-tour-deletion-propagation/memo.md)) | Accepted (Q1–Q10 decided S248; Q11 proposed) |
| [0016](0016-one-design-system-guarded-kit-copies.md) | One design system for the ecosystem frontends: a canonical kit core in AA-CIS-App, guarded byte copies, one token set for all five apps (AA-994; closes AA-655) | Accepted (amended by 0019) |
| [0017](0017-migrations-in-app-pr-expand-auto-apply.md) | Migrations ship in the app PR; expand files are auto-applied on Dev by an Infra pipeline before deploy (AA-993 D2; design: [S252 audit](../audits/2026-10-26-S252-aa993-delivery-pipeline/design.md)) | Accepted (S259; amended by 0017a) |
| [0017a](0017a-dev-auto-applies-contract-migrations.md) | Amendment: on Dev, Migration Apply also applies contract migration files when every job table is idle and no rerun wave is open; destructive files stay manual; prod unchanged (AA-1032) | Accepted (S263) |
| [0018](0018-lean-aws-account-model.md) | Lean AWS account model: an AA-owned organization (management account), prod in its own account, two environments; supersedes ADR 0012 decisions 1, 2 and 5; prod in us-west-1 (decision 7) (AA-1004; design: [S258 blueprint](../audits/2026-10-29-S258-aws-org-blueprint/README.md) §0) | Accepted 31/10/2026 (S262, tech lead; amended by 0009 d14 and 0019) |
| [0019](0019-b2b-only-ecosystem-model.md) | B2B-only ecosystem model: AA sells to partner agencies (tenants) only; Content is the base product, CRM and TripPlanner are add-ons, Booking is the B2B back office; tenant master in CIS `shared`, feature keys, staff roles and tenant scope, one agency app (AA-1034; design: [S265 audit](../audits/2026-11-03-S265-ecosystem-restructure/README.md)) | Accepted 03/11/2026 (S265, tech lead; d1–d23; b1–b21 business choices the business owner may revisit) |
| [0020](0020-content-quality-architecture.md) | Content quality architecture: one policy registry, one FactSheet, measured gates, one exit contract for every AI-written tour page, blog and social post; amends 0009 d5, d8, d10, d12 (AA-900, AA-741; design: [S271 audit](../audits/2026-11-06-S271-writing-quality-audit/README.md)) | Accepted 06/11/2026 (S271, tech lead; D1–D16) |
| [0021](0021-github-org-security-and-ci-hygiene.md) | GitHub organisation security and CI/CD hygiene: org-level controls first, repos stay public, zero added cost; CI hygiene in four automated layers; amends 0014 d4 (AA-1024, AA-1004) | Accepted 08/11/2026 (S273, tech lead) |
| [0022](0022-aa-academy-learning-platform.md) | AA Academy: courses and learner records in CIS (schema `learn`), one academy host on the CRM web, a learning route class `/learn/v1` with its own WORKFORCE client `academy-web`; amends 0006b decision 6 (AA-1098, AA-1105) | Accepted |

## Numbering

The table and the next-free line below are read by `tools/adr/check_adr_numbers.py` (root CI `contracts.yml`). A new
ADR takes a next-free number; an amendment takes the next letter of the ADR it amends. A reserved number is used only
by an ADR whose header cites the reserving issue, and that PR deletes the row. Reserve a number only when other pages
already cite it.

| Number | Status | For |
|---|---|---|
| 0013 | Reserved | HTTP API conventions, before any `/booking/v1` prefix (AA-899; cited by the engineering handbook) |

Next free root numbers: **0023**.

AA-901 took 0011 (agent and bot identity, merge rights) and 0014 (repo visibility and GitHub plan), the next free
numbers when its ADRs were written (S247).

The enforceable rules that ADR 0008 points to live in `docs/architecture/data-standards/` (v1.0).
