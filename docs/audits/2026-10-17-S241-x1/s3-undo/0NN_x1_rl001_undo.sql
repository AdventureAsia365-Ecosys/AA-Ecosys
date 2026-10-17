-- Migration rl-0NN: AA-852 (X1 plan S3 rollback) — UNDO of rl-001: drop the roles bk_owner, tp_owner and cis_app,
-- with everything that still references them (CIS 243's grants and key guard, CIS 244's grants, policies and
-- default privileges if 244 was applied).
--
-- PREPARED, NOT MERGED. Infra-native roles/ file (key rl-NNN): copy it to db/migrations/roles/<next free NNN>_x1_rl001_undo.sql
-- and replace 0NN in the version key below with that number, only if the X1 role bootstrap has to be rolled back
-- (for example the S8 train is aborted after rl-001 + 243 because bk-014 fails). roles/ files run only as the RDS
-- master, which is a member of all three roles (rl-001): DROP OWNED BY needs that membership.
--
-- Why not `DROP ROLE IF EXISTS cis_app, tp_owner, bk_owner` alone (the first rollback text of rl-001, wrong):
-- DROP ROLE fails with "role cannot be dropped because some objects depend on it" as soon as anything references
-- the role. In the S8 train CIS 243 runs right after rl-001 and grants USAGE on schema shared and SELECT, INSERT on
-- shared.schema_versions to bk_owner / tp_owner; CIS 244 (S16) adds policies TO cis_app, grants to cis_app and
-- default privileges FOR ROLE aa_cis_admin … TO cis_app. DROP OWNED BY revokes all of those in this database
-- (privileges, default-privilege entries naming the role as grantee, the role in a policy's role list; a policy
-- whose only role it was is dropped), so DROP ROLE then succeeds.
--
-- Valid only while the three roles own nothing. DROP OWNED BY also DROPS every object a role owns (all booking.*
-- objects after bk-014!), so guard 1 refuses while any owner dependency exists: after bk-014 / tp-013 apply their
-- prepared undo files first (S6 / S7 rollback, rl-0xx), which give the objects back to aa_cis_admin and revoke
-- the FOR ROLE bk_owner / tp_owner default privileges. Not valid once cis_app is the CIS runtime (S18): guard 1
-- refuses while a cis_app session exists; roll S18 back first.
--
-- What (explicit statements, MIG-4):
--   1. CIS 243's registry key guard: DROP TRIGGER schema_versions_key_guard + FUNCTION
--      shared.schema_versions_key_guard() (IF EXISTS: 243 may not be applied). It exists only for bk_owner /
--      tp_owner; 243's grants go with DROP OWNED below, so this file undoes 243 as a whole. To keep the key guard
--      (it then lets members of the registry owner insert and refuses every other role) delete these two lines.
--   2. DROP OWNED BY cis_app, tp_owner, bk_owner;  (owns nothing at this point: revokes only)
--   3. DROP ROLE cis_app, tp_owner, bk_owner;      (the memberships of aa_cis_admin go with them)
--   The N3 connection limits of rl-001 stay (they are CIS 234's values).
--
-- Guards:
--   1. before: the session is the master and a member of the three roles; none of them owns anything in this
--      database or in a shared catalog (pg_shdepend deptype 'o', which DROP OWNED would drop: relations, functions,
--      types, schemas, default-privilege rows FOR ROLE r, …); none is referenced from another database (DROP OWNED
--      works on this database only); no client session runs as cis_app.
--   2. after: none of the three roles exists; no trigger is left on shared.schema_versions.
--
-- After an apply: rl-001 and 243 (and 244 if applied) stay registered (history, rows are never deleted): a later
-- redo is a new rl- key and a new CIS file. db/owners.yaml is unchanged (owner_role_today was never switched). The
-- S2 probe cells keyed on rl-001 / 243 / 244 turn red because their keys stay registered: re-key them or waive them
-- in the session log until the redo. Regenerate the schema reference (DB Schema Dump).
--
-- Locks: DROP TRIGGER takes ACCESS EXCLUSIVE on shared.schema_versions (~240 rows, milliseconds; only DB Migrate
-- writes it); DROP OWNED takes a lock on each object whose ACL or policy it rewrites (milliseconds each; the CIS
-- tables of 244 if applied: run with every job table idle, the DB Migrate idle check). lock_timeout 5s.

BEGIN;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '5min';

-- ── Guard 1: preconditions ───────────────────────────────────────────────────────────────────────
DO $$
DECLARE
    r       text;
    owned   text;
    other   text;
BEGIN
    IF session_user <> 'aa_cis_admin' OR current_user <> 'aa_cis_admin' THEN
        RAISE EXCEPTION 'rl undo: runs only as the RDS master aa_cis_admin (session %, current %)', session_user, current_user;
    END IF;
    FOREACH r IN ARRAY ARRAY['bk_owner', 'tp_owner', 'cis_app'] LOOP
        IF to_regrole(r) IS NULL THEN
            RAISE EXCEPTION 'rl undo: role % does not exist (rl-001 not applied, or already undone)', r;
        END IF;
        IF NOT pg_has_role('aa_cis_admin', r, 'MEMBER') THEN
            RAISE EXCEPTION 'rl undo: aa_cis_admin is not a member of % (rl-001 grants it); DROP OWNED BY needs it', r;
        END IF;
    END LOOP;
    SELECT string_agg(format('%s owns %s', d.refobjid::regrole,
                             coalesce(pg_describe_object(d.classid, d.objid, d.objsubid), d.classid::regclass::text)),
                      ', ' ORDER BY 1)
      INTO owned
      FROM pg_shdepend d
     WHERE d.refclassid = 'pg_authid'::regclass AND d.deptype = 'o'
       AND d.refobjid IN ('bk_owner'::regrole, 'tp_owner'::regrole, 'cis_app'::regrole)
       AND d.dbid IN (0, (SELECT oid FROM pg_database WHERE datname = current_database()));
    IF owned IS NOT NULL THEN
        RAISE EXCEPTION 'rl undo: the roles still own objects, DROP OWNED would drop them — apply the bk-014 / tp-013 undo files first: %', owned;
    END IF;
    SELECT string_agg(DISTINCT db.datname, ', ') INTO other
      FROM pg_shdepend d JOIN pg_database db ON db.oid = d.dbid
     WHERE d.refclassid = 'pg_authid'::regclass
       AND d.refobjid IN ('bk_owner'::regrole, 'tp_owner'::regrole, 'cis_app'::regrole)
       AND db.datname <> current_database();
    IF other IS NOT NULL THEN
        RAISE EXCEPTION 'rl undo: the roles are referenced in other database(s) %, which DROP OWNED here cannot clear', other;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_stat_activity WHERE usename = 'cis_app') THEN
        RAISE EXCEPTION 'rl undo: cis_app has open sessions (the CIS runtime runs as cis_app, X1 S18): roll S18 back first';
    END IF;
END $$;

-- ── 1. CIS 243's registry key guard (exists only for bk_owner / tp_owner) ─────────────────────────
DROP TRIGGER IF EXISTS schema_versions_key_guard ON shared.schema_versions;
DROP FUNCTION IF EXISTS shared.schema_versions_key_guard();

-- ── 2–3. Every reference, then the roles ──────────────────────────────────────────────────────────
DROP OWNED BY cis_app, tp_owner, bk_owner;
DROP ROLE cis_app, tp_owner, bk_owner;

-- ── Guard 2: result ──────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname IN ('bk_owner', 'tp_owner', 'cis_app')) THEN
        RAISE EXCEPTION 'rl undo: a role is still there';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = 'shared.schema_versions'::regclass AND NOT tgisinternal) THEN
        RAISE EXCEPTION 'rl undo: a user trigger is left on shared.schema_versions';
    END IF;
END $$;

INSERT INTO shared.schema_versions (version, applied_at, description)
VALUES ('rl-0NN', now(), 'AA-852 (X1 S3 rollback): undo rl-001 — DROP OWNED BY + DROP ROLE cis_app, tp_owner, bk_owner; CIS 243 key guard dropped (243/244 grants revoked by DROP OWNED)')
ON CONFLICT (version) DO NOTHING;

COMMIT;
