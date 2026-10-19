# AA-860 — X1 step S20 rollback file (`rl-002` undo)

File: `docs/audits/2026-10-17-S241-x1/s20-undo/0NN_x1_rl002_undo.sql`. Prepared, not merged into AA-CIS-Infra
`db/migrations/roles/`; same convention as `s3-undo/` (rl-001) and `s6-undo/` (bk-014). The forward file and its
notes are in AA-CIS-Infra (`db/migrations/roles/002_x1_cis_owner_db_migrator.sql`,
`docs/implementation-notes/AA-860-S20.md`).

## Decisions
- **`DROP OWNED BY cis_owner` + `DROP ROLE db_migrator, cis_owner`.** A bare `DROP ROLE` fails on `cis_owner`
  ("privileges for database aa_cis_dev", reproduced in the dry run) because rl-002 grants it CREATE on the
  database; `DROP OWNED BY` revokes privileges on shared objects too.
- **No `DROP OWNED BY db_migrator`.** On PostgreSQL 15 it needs the master to have `db_migrator`'s privileges, i.e. a
  temporary membership that would also make the master a member of `catalog_owner` inside the transaction (§1.4).
  X1 grants `db_migrator` memberships only, so it has no `pg_shdepend` row; guard 1 refuses (listing the rows) if
  that ever changes.
- **Guard 1** (before): master session; both roles exist; master member of `cis_owner`; `cis_owner` owns nothing
  (`pg_shdepend` deptype `o`, incl. default-privilege rows → apply the 245 undo first); no reference from another
  database; `db_migrator` has no `pg_shdepend` row; no `db_migrator` session (→ roll S22 back first).
  **Guard 2** (after): both roles gone; master still not a member of `aa_app_user` / `catalog_owner`.

## Changed
- New prepared file `s20-undo/0NN_x1_rl002_undo.sql`.
- `x1-plan.md` §5 S20 "Rollback" points to it.

## Tradeoffs
- Leaving the secret `aa-cis/dev/db-migrator` and the alarm row in place after an undo (both harmless: the DSN's
  role is gone, the alarm sees no data) keeps the undo a pure DB file; the header says what to remove if Wave 5 is
  abandoned.

## Should know
- Dry run on a throwaway PostgreSQL 16 cluster (S244), key replaced by `rl-003`: each refusal fired with its
  message (schema owned by `cis_owner`; default privileges FOR ROLE `cis_owner`; a table privilege held by
  `db_migrator`; an open `db_migrator` session); the clean run dropped both roles and the database ACL entry,
  registered the key; a second run refused ("does not exist … already undone"); rl-002 re-applied after it.
  One PG 16 artifact: the sandbox master had ADMIN on `catalog_owner` (PG 16 needs it to grant), which PG 16 counts
  as membership, so guard 2's `catalog_owner` check was replaced by `false` for the clean run only. RDS runs 15.
- After an apply `rl-002` stays registered: the probe cells keyed on it (`owner_role.cis_owner`,
  `sessions.db_migrator_below_limit`) turn red until a redo (new rl- key); waive them in the session log.
