# AA-860 — X1 S21 rollback file (prepared `roles/` undo of CIS 245) and the S21 plan amendment

Branch `docs/x1-s21-undo`. Files: `docs/audits/2026-10-17-S241-x1/s21-undo/0NN_x1_cis_owner_undo.sql`, an "S244
amendments" block at the top of `docs/audits/2026-10-17-S241-x1/x1-plan.md`. Companions: AA-CIS-App
`feat/x1-s21-cis-owner` (245), AA-CIS-Infra `chore/x1-s21-introspect` (read-only run-script).

## Decisions
- **A `roles/` file, kept here unmerged as a migration** (s3-undo / s6-undo precedent). After 245, DB Migrate runs
  `cis/` files as `cis_owner` (XD8), which cannot give objects to the master; `roles/` files run as the master
  (a member of `cis_owner` through rl-002). To use it: copy to AA-CIS-Infra `db/migrations/roles/<next NNN>_…`,
  replace `0NN` in the key, apply. It never takes the CIS key 246 (the S22 probe).
- **Catalog-driven, the same object kinds as 245 step 4**, filtered on owner `cis_owner` over the 12 schemas
  (catalog included: a `cis/` file after 245 may have created something there as `cis_owner`; the `catalog_owner`
  views are not `cis_owner`'s and stay). So objects created after 245 go back too, with no list to maintain.
- Drops the 8 `<table>_cis_owner_all` policies, restores CIS 244's default privileges FOR ROLE `aa_cis_admin` and
  revokes the FOR ROLE `cis_owner` rows, restates the registry REVOKE, registers `rl-0NN`.
- Guards: master login; nothing in the 12 schemas left with `cis_owner`; no default privilege or policy names
  `cis_owner`; exactly 244's 33 default-privilege rows; non-owner privileges byte-equal to the snapshot taken first.

## Changed
- Nothing applied. The plan amendment records the S21 design pass (FORCE policies TO `cis_owner`, catalog-driven
  transfer, the guards actually in 245, the apply order).

## Tradeoffs
- Catalog-driven DDL in an undo is less reviewable than a list, but an explicit list would go stale with every
  `cis/` file applied after 245; the NOTICE per object is the record.
- No behavioural block: after the undo the master owns everything again and reads unfiltered, which is the
  pre-245 state; the probe's CIS ownership cells go back to pending.

## Should know
- Before S22 only as written: after S22 the DB Migrate login is `db_migrator`, and a `roles/` file needs the
  runner's master connection (plan S22). The SQL is the same.
- Dry run (local PostgreSQL 16, the AA-CIS-App `test_aa860_migration_245` fixture: RDS-like master, 244, 245): the
  undo committed (127 objects back plus the 12 schemas), the owner / default-privilege / policy state equalled the
  state after 244, and 245 applied again on top of it (round trip).
