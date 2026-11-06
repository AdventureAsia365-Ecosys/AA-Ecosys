# AA-1004 lane l8: AWS tagging standard (root side, S271)

Infra side and plan evidence: AA-CIS-Infra `docs/implementation-notes/AA-1004-tagging.md`.

## Decisions

- New catalog page `docs/architecture/tagging-standard.md`, ID **FIN-03** (next to FIN-01 FinOps process), so the
  rule DM-10.1 stays one short row and the detail has one home.
- Eight mandatory keys; App keeps the seven values Cost Explorer already shows; security and CI/CD are Components of
  `shared`, not new Apps (the per-App budgets must keep summing to the account budget).
- Environment values follow root ADR 0018 (`staging`, not `stg`), plus `shared` for organization-level resources.
- Cost allocation tags: App, Environment, Component, Project, CostCenter. Owner, ManagedBy and DataClassification are
  governance keys, not cost keys.
- Prod: same keys, `Environment = prod`; an Organizations tag policy from the management account is added when prod
  exists (ADR 0018 lists tag policies as "not now"; prod is the trigger); SCP enforcement optional and later.
- The monthly untagged report reads the stored CIS cost bundle, not Cost Explorer (FIN-01 forbids a new Cost Explorer
  script). It is C8b item 10.

## Changed

- DM-10.1 now points to FIN-03 and names the CI guard as its enforcement (was "Terraform review; partial").
- C8b gets item 10 (untagged spend and resources missing keys).
- FIN-01 "Tags" section shortened to a summary that links FIN-03.

## Tradeoffs

- One `technology` CostCenter today: a finance split by business unit is not needed for a two-environment startup;
  a new value is a one-line change here and in the policy file.
- Tag policy deferred to prod: it would only report today (one member account, billed by the reseller).

## Should know

- Status `draft` until the tech lead reads it (STYLE.md).
- Payer activation of the new cost allocation keys is a request to the reseller while acc2 is billed there; the
  one-line CLI in FIN-03 is for our management account once acc2 has joined the organization.
