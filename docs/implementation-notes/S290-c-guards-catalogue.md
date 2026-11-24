# S290 lane c-guards: Catalogue surface refresh (no Linear issue; CI hygiene follow-up)

## Decisions

- Scheduled Catalogue run 45185991203 failed "Surface drift": the snapshot missed 8 pages / route groups and 38
  settings keys that landed on the app mains since the last refresh. The snapshot was refreshed from each app's
  `origin/main` (a `git archive` of the paths the CI job checks out sparsely, not the local working trees, which may
  lag or carry lane edits).
- New surfaces mapped to features (`docs/catalogue/features.yaml`):
  - Booking `route:operability` (can-operate check, no-hotel nights, sale exception) -> BK-F005 trip plans.
  - Booking `route:supplier_bank`, `route:supplier_profile_options` -> BK-F009 suppliers.
  - Booking `route:b2b_addons` (the AA add-ons an agency can quote, booking.b2b.v1) -> BK-F017 B2B API.
  - Booking `route:staff_view_as` (owner "view as a lower role") -> BK-F018 staff and roles.
  - Booking `page:/add-ons`, `route:addons` -> new feature BK-F020 "AA add-ons" (next free BK id; ids are never
    reused).
  - CRM `route:ops_privacy_evidence` -> CRM-F028 platform ops API.
  Summaries (EN + VI) extended with one clause each so the Product map describes the new surface.
- Settings keys need no mapping (the catalogue check maps them by registry); none added to a feature's conditions.
- `python tools/docs/gen_sections.py --write --repos-root <workspace> --repos-ref origin/main` refreshed the
  generated blocks (job kinds, release versions, latest migrations, Infra facts) the same run warned about.

## Changed

- `docs/catalogue/surface.snapshot.json`, `docs/catalogue/features.yaml`, `docs/generated/facts.snapshot.json` and the
  generated blocks of `docs/guides/devops.md`, `docs/ops/job-kinds.md`, `docs/ops/runbooks/restore-schema.md`.

## Tradeoffs

- BK-F020 is a new feature rather than folding add-ons into suppliers (BK-F009): add-ons have their own page, own
  maker-checker capability and an agency-facing B2B list.

## Should know

- Other S290 lanes that add a page, route group or setting make the snapshot stale again: refresh it in the session
  close root PR (lessons: "Snapshot surface của Catalogue cũ đi sau mỗi phiên").
