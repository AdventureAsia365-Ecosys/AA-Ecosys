-- Migration rl-0NN: AA-860 (X1 plan S20 rollback) — UNDO of rl-002: drop the roles db_migrator and cis_owner, with
-- everything that still references them (cis_owner's CREATE on the database).
--
-- PREPARED, NOT MERGED. Infra-native roles/ file (key rl-NNN): copy it to db/migrations/roles/<next free NNN>_x1_rl002_undo.sql
-- and replace 0NN in the version key below with that number, only if rl-002 has to be rolled back (for example
-- set-password for db_migrator or 245 cannot be made to work and Wave 5 is postponed). roles/ files run only as the RDS
-- master, which is a member of cis_owner (rl-002): DROP OWNED BY cis_owner needs that membership.
--
-- Order of rollbacks (each one first if it was applied):
--   S22 (DB Migrate logs in as db_migrator) → revert the S22 PR + Terraform apply, so the migrator task definition
--       injects the master DSN again; guard 1 refuses while db_migrator has a session.
--   S21 (CIS 245, CIS objects to cis_owner)  → its own prepared roles/ undo (objects and default privileges back to
--       aa_cis_admin); guard 1 refuses while cis_owner owns anything, because DROP OWNED BY would DROP those objects.
--
-- Why DROP OWNED BY cis_owner and not only DROP ROLE: rl-002 grants CREATE ON DATABASE aa_cis_dev to cis_owner;
-- DROP ROLE fails ("some objects depend on it") while that privilege exists. DROP OWNED BY revokes the role's
-- privileges in this database and on shared objects (the database itself), and drops what it owns (nothing, guard 1).
-- db_migrator gets role memberships only (rl-002) and no object privilege anywhere in X1, so it has no pg_shdepend
-- row and a plain DROP ROLE works; guard 1 refuses if someone granted it a privilege since (revoke it by hand in this
-- file, then re-run). Not DROP OWNED BY db_migrator: on PostgreSQL 15 that needs the privileges of db_migrator, and
-- making the master a member of it would, for the transaction, make the master a member of catalog_owner (§1.4).
-- Memberships (db_migrator in bk_owner, tp_owner, cis_owner, catalog_owner, cis_app, pg_read_all_stats; aa_cis_admin
-- in cis_owner) go with DROP ROLE.
--
-- What (explicit statements, MIG-4):
--   1. DROP OWNED BY cis_owner;            (owns nothing at this point: revokes CREATE on the database only)
--   2. DROP ROLE db_migrator, cis_owner;
--
-- Guards:
--   1. before: the session is the master and a member of cis_owner; both roles exist; cis_owner owns nothing in this
--      database or in a shared catalog (pg_shdepend deptype 'o': schemas, relations, functions, types, default-
--      privilege rows FOR ROLE cis_owner, …); neither role is referenced from another database; db_migrator has no
--      pg_shdepend row at all (no ownership, privilege, default-privilege entry or policy); no client session runs
--      as db_migrator.
--   2. after: neither role exists; the master is still not a member of aa_app_user or catalog_owner.
--
-- After an apply: rl-002 stays registered (history, rows are never deleted): a later redo is a new rl- key. The S2
-- probe cells keyed on rl-002 (owner_role.cis_owner, sessions.db_migrator_below_limit) turn red because their key
-- stays registered: waive them in the session log until the redo. The secret aa-cis/dev/db-migrator keeps a DSN whose
-- role no longer exists (harmless: no login can use it; Nghiệp may leave it or write a new value at the redo). The
-- CloudWatch alarm aa-cis-dev-rds-role-connections-db_migrator gets no data (treat_missing_data = notBreaching):
-- remove its row from rds_role_connection_limits (Infra, observability_ecosys.tf) in the same rollback PR if Wave 5 is
-- abandoned. db/owners.yaml is unchanged (owner_role_today of cis is still aa_cis_admin before 245). Regenerate the
-- schema reference (DB Schema Dump).
--
-- Locks: DROP OWNED on cis_owner touches only the pg_database ACL row; DROP ROLE takes the shared role-catalog lock.
-- Milliseconds, no table lock. lock_timeout 5s.

BEGIN;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '2min';

-- ── Guard 1: preconditions ───────────────────────────────────────────────────────────────────────
DO $$
DECLARE
    r       text;
    owned   text;
    other   text;
    refs    text;
BEGIN
    IF session_user <> 'aa_cis_admin' OR current_user <> 'aa_cis_admin' THEN
        RAISE EXCEPTION 'rl undo: runs only as the RDS master aa_cis_admin (session %, current %)', session_user, current_user;
    END IF;
    FOREACH r IN ARRAY ARRAY['cis_owner', 'db_migrator'] LOOP
        IF to_regrole(r) IS NULL THEN
            RAISE EXCEPTION 'rl undo: role % does not exist (rl-002 not applied, or already undone)', r;
        END IF;
    END LOOP;
    IF NOT pg_has_role('aa_cis_admin', 'cis_owner', 'MEMBER') THEN
        RAISE EXCEPTION 'rl undo: aa_cis_admin is not a member of cis_owner (rl-002 grants it); DROP OWNED BY needs it';
    END IF;
    SELECT string_agg(format('%s owns %s', d.refobjid::regrole,
                             coalesce(pg_describe_object(d.classid, d.objid, d.objsubid), d.classid::regclass::text)),
                      ', ' ORDER BY 1)
      INTO owned
      FROM pg_shdepend d
     WHERE d.refclassid = 'pg_authid'::regclass AND d.deptype = 'o'
       AND d.refobjid IN ('cis_owner'::regrole, 'db_migrator'::regrole)
       AND d.dbid IN (0, (SELECT oid FROM pg_database WHERE datname = current_database()));
    IF owned IS NOT NULL THEN
        RAISE EXCEPTION 'rl undo: the roles still own objects, DROP OWNED would drop them — apply the CIS 245 undo file first (S21 rollback): %', owned;
    END IF;
    SELECT string_agg(DISTINCT db.datname, ', ') INTO other
      FROM pg_shdepend d JOIN pg_database db ON db.oid = d.dbid
     WHERE d.refclassid = 'pg_authid'::regclass
       AND d.refobjid IN ('cis_owner'::regrole, 'db_migrator'::regrole)
       AND db.datname <> current_database();
    IF other IS NOT NULL THEN
        RAISE EXCEPTION 'rl undo: the roles are referenced in other database(s) %, which DROP OWNED here cannot clear', other;
    END IF;
    SELECT string_agg(format('%s (deptype %s)',
                             coalesce(pg_describe_object(d.classid, d.objid, d.objsubid), d.classid::regclass::text),
                             d.deptype), ', ' ORDER BY 1)
      INTO refs
      FROM pg_shdepend d
     WHERE d.refclassid = 'pg_authid'::regclass AND d.refobjid = 'db_migrator'::regrole;
    IF refs IS NOT NULL THEN
        RAISE EXCEPTION 'rl undo: db_migrator holds privileges X1 never granted it; REVOKE them in this file before DROP ROLE: %', refs;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_stat_activity WHERE usename = 'db_migrator') THEN
        RAISE EXCEPTION 'rl undo: db_migrator has open sessions (DB Migrate / Schema Dump / probe log in as db_migrator, X1 S22): roll S22 back first';
    END IF;
END $$;

-- ── 1–2. cis_owner's database privilege, then the roles ──────────────────────────────────────────
DROP OWNED BY cis_owner;
DROP ROLE db_migrator, cis_owner;

-- ── Guard 2: result ──────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname IN ('cis_owner', 'db_migrator')) THEN
        RAISE EXCEPTION 'rl undo: a role is still there';
    END IF;
    IF pg_has_role('aa_cis_admin', 'aa_app_user', 'MEMBER') OR pg_has_role('aa_cis_admin', 'catalog_owner', 'MEMBER') THEN
        RAISE EXCEPTION 'rl undo: aa_cis_admin must not be a member of aa_app_user or catalog_owner (policies TO r reach members)';
    END IF;
END $$;

INSERT INTO shared.schema_versions (version, applied_at, description)
VALUES ('rl-0NN', now(), 'AA-860 (X1 S20 rollback): undo rl-002 — DROP OWNED BY cis_owner (CREATE on the database) + DROP ROLE db_migrator, cis_owner')
ON CONFLICT (version) DO NOTHING;

COMMIT;
