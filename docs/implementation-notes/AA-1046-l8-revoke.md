# AA-1046 follow-up implementation notes (root repo: booking inquiry grant revoked, S273 lane l8)

Scope: the root docs of the revoke chain for the residual tp-009 grants of the retired inquiry.submitted contract.
TripPlanner tp-027 revokes role `booking`'s `SELECT` on `tripplanner.v_inquiry_outbox` and `USAGE` on schema
`tripplanner`; AA-CIS-Infra drops the registry row and the probe's consumer row and adds a cross-app 42501 cell;
AA-CIS-App drops the two RLS catalogue allowlist rows. Refs AA-1046, AA-1038.

## Decisions

- The contracts README paragraph keeps its place above the registry table and changes from "revoke pending" to
  "revoked (tp-027)", naming what each repo changed; the v1.1 registry row says the tp-009 grant was revoked.
- `schema-ownership.md`: the AA-Booking reader of `tripplanner` is now "none"; the view stays until a destructive drop.
- `ecosystem-architecture.md` §3.3 / §3.4: the view is no longer listed as published to Booking, and the
  inquiry.submitted bullet says the contract is retired.

## Changed

- `docs/contracts/README.md`, `docs/database/schema-ownership.md`, `docs/ecosystem-architecture.md`.

## Tradeoffs

- Data standards (`01-engineering.md`, `02-data-management.md`, `03-scaling.md`), `docs/legal/register.md`, the
  KPI catalog and the `aa-ecosys-repos` skill references still use the inquiry outbox as an example or a historic
  row; left for the retirement sweep of the inquiry hand-off, so this PR stays about the grant.

## Should know

- Merge after the Migration Apply run shows `tripplanner/027_revoke_booking_inquiry_grant.sql` applied: the text says
  the grant is revoked. Built on top of the l1 root branch `docs/s273-inquiry-contract-retired` (the paragraph it
  rewrites is added there), so it joins that PR.
