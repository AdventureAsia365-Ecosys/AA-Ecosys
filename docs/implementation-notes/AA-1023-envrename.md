# AA-1023 — rename of the Dev apply environment `prod` -> `dev` (root part, lane l4 of S265)

The Infra part (three PRs: trust both subjects, workflows on `dev`, trust only `dev`) and its decisions are in
AA-CIS-Infra `docs/implementation-notes/AA-1023-envrename.md`. This root PR only brings the docs that name the
environment or the workflow up to date: `README.md`, `docs/ecosystem-architecture.md`, `docs/ops/README.md`,
`docs/guides/devops.md` and the status of data standard C7.2d (a status fact, not a rule change: no version bump).

## Decisions

- Merge after the third Infra PR is applied: the devops guide says the Dev apply role trusts only `environment:dev`.
- ADR 0012 keeps its text (a decision record); the rename is its decision 6, steps 1 to 3.

## Should know

- The workflow file is still `terraform-apply.yml`; only its display name changed to "Terraform Apply Dev".
