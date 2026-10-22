# Ecosystem ADRs

Cross-repo architecture decisions for AA-Ecosys (AA-CIS-App, AA-TripPlanner-Web, AA-Booking,
AA-CIS-Infra). Decisions that affect one repo only stay in that repo's `docs/adr/`; infrastructure-only
decisions go to `infra/AA-CIS-Infra/docs/adr/` (rule: `skill/ai-nghiep/references/adr.md`).
An amendment is a separate file `<nnnn>a-<slug>.md` and the amended ADR carries a pointer to it.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-ecosystem-target-architecture.md) | Ecosystem target architecture: shared platform services and contracts between apps | Accepted (tightened by 0008) |
| [0002](0002-only-cis-writes-content.md) | Only CIS writes content; other apps read it through views | Accepted |
| [0003](0003-one-durable-job-model.md) | One durable job model for all deferred work | Accepted (amended by 0003a) |
| [0003a](0003a-per-owner-job-tables.md) | Amendment: one job table per owner schema, from a shared DDL template | Accepted |
| [0004](0004-aa-booking-stack-and-bootstrap.md) | AA-Booking: stack, repo layout, runtime and bootstrap on acc2 | Accepted (amended by 0004a, 0004b) |
| [0004a](0004a-supply-content-ownership.md) | Amendment: supply data in Booking, customer-facing supply content in CIS | Accepted |
| [0004b](0004b-per-app-security-groups.md) | Amendment: one security group per caller (per-app network isolation) | Accepted |
| [0005](0005-pricing-and-supplier-rates.md) | Pricing and supplier rates | Accepted (amendment 0005a proposed) |
| [0005a](0005a-b2b-resale-warn-and-vnd.md) | Amendment: B2B resale by partner agencies (warn below the "from" price, no subscription line, VND quotes) | Proposed |
| [0006](0006-ecosystem-identity.md) | Ecosystem identity on Amazon Cognito (staff, tenant users, travellers) | Accepted (amended by 0006a; amendment 0006b proposed) |
| [0006a](0006a-identity-phase1-amendments.md) | Amendment: identity Phase 1 as shipped (CIS staff on Cognito WORKFORCE) | Accepted |
| [0006b](0006b-partner-pool-and-mfa.md) | Amendment: a partner pool with required MFA for agency people, and an M2M pool for service calls | Proposed |
| [0007](0007-place-pipeline-in-cis.md) | Place pipeline in CIS: `geo` schema, `catalog.*` views, background jobs | Accepted |
| [0008](0008-new-app-integration-and-data-platform-rules.md) | New-app integration and data platform rules | Accepted (amendment 0008a proposed) |
| [0008a](0008a-crm-separate-app-exceptions.md) | Amendment: the partner CRM is a separate app; traveller OTP and an own LLM gateway as playbook exceptions | Proposed |
| [0010](0010-aa-partner-app.md) | AA-Partner: one app for partner agencies (CRM and tenant portal) | Proposed |

## Numbering

The table and the next-free line below are read by `tools/adr/check_adr_numbers.py` (root CI `contracts.yml`). A new
ADR takes a next-free number; an amendment takes the next letter of the ADR it amends. A reserved number is used only
by an ADR whose header cites the reserving issue, and that PR deletes the row. Reserve a number only when other pages
already cite it.

| Number | Status | For |
|---|---|---|
| 0009 | Reserved | AI platform and governance (AA-804) |
| 0012 | Reserved | Prod blueprint and environment model (AA-880; cited by the engineering handbook and the guides) |
| 0013 | Reserved | HTTP API conventions, before any `/booking/v1` prefix (AA-899; cited by the engineering handbook) |

Next free root numbers: **0011**, **0014**.

Nothing is reserved for AA-901 (GitHub App identity, release-please): it takes the next free numbers when its ADRs
are written.

The enforceable rules that ADR 0008 points to live in `docs/architecture/data-standards/` (v1.0).
