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
| [0005](0005-pricing-and-supplier-rates.md) | Pricing and supplier rates | Accepted |
| [0006](0006-ecosystem-identity.md) | Ecosystem identity on Amazon Cognito (staff, tenant users, travellers) | Accepted |
| [0007](0007-place-pipeline-in-cis.md) | Place pipeline in CIS: `geo` schema, `catalog.*` views, background jobs | Accepted |
| [0008](0008-new-app-integration-and-data-platform-rules.md) | New-app integration and data platform rules | Accepted |

Reserved: **0009** AI platform (AA-804).

The enforceable rules that ADR 0008 points to live in `docs/architecture/data-standards/` (v1.0).
