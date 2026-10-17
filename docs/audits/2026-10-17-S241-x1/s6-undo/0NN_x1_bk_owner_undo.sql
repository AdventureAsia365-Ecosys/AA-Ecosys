-- Migration rl-0NN: AA-852 (X1 plan S6 rollback) — UNDO of Booking bk-014: every booking.* object back to the RDS
-- master aa_cis_admin, default privileges of role booking back to bk-001's FOR ROLE aa_cis_admin rows.
--
-- PREPARED, NOT MERGED. Infra-native roles/ file (key rl-NNN): rename to db/migrations/roles/<next free NNN>_x1_bk_owner_undo.sql
-- and replace 0NN in the version key below with that number only if bk-014 has to be rolled back. It must be a roles/ file:
-- once schema booking is owned by bk_owner, DB Migrate runs booking/ files as bk_owner (X1 XD8), and bk_owner cannot give
-- objects to aa_cis_admin (not a member of it). roles/ files always run as the master, which is a member of bk_owner
-- (rl-001). After it commits the runner runs booking/ files as aa_cis_admin again, automatically. Never key bk-015 (the
-- S9 probe key). bk-014 stays registered (history); a later re-transfer is a new bk-NNN.
--
-- Same object list as bk-014 (32 tables, 2 views, 5 standalone sequences, 12 functions). Objects created by bk-015+
-- are not in it: the last guard raises; add them (ALTER ... OWNER TO aa_cis_admin) before applying.
-- Locks: held until COMMIT, taken up front, as in bk-014: right after the guard one LOCK TABLE statement takes ACCESS
-- EXCLUSIVE on the 32 tables and v_customer_summary, hot tables first (job, inbox_events, inbox_cursor, customers,
-- trip_cases, audit_logs: the app inbox path's order), so under lock_timeout 5s the file gets every lock or none and
-- fails before it changes anything. Not in it: sequences (LOCK refuses them; only table defaults use them) and
-- v_schema_versions (LOCK on a view also locks shared.schema_versions with the view owner's rights, and bk_owner may
-- not; its ALTER VIEW takes that one lock, readiness is its only reader). bk_inquiry_pull is exempt from the DB Migrate
-- idle check, so Booking requests may wait for the file (well under a second once the locks are held).

BEGIN;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '15min';

DO $$
BEGIN
    IF current_user <> 'aa_cis_admin' THEN
        RAISE EXCEPTION 'rl undo: runs only as the RDS master aa_cis_admin (got %)', current_user;
    END IF;
    IF NOT pg_has_role('aa_cis_admin', 'bk_owner', 'MEMBER') THEN
        RAISE EXCEPTION 'rl undo: aa_cis_admin is not a member of bk_owner (rl-001)';
    END IF;
END $$;

-- Every table lock this file needs, in one statement (header, Locks): all or none within lock_timeout, held until COMMIT.
LOCK TABLE booking.job, booking.inbox_events, booking.inbox_cursor, booking.customers, booking.trip_cases,
    booking.audit_logs, booking.countries, booking.customer_otps, booking.customer_sessions, booking.fx_rates,
    booking.hotel_room_types, booking.hotels, booking.media_files, booking.notification_reads,
    booking.notifications, booking.policy_approvals, booking.pricing_rules, booking.services, booking.settings,
    booking.staff_assignments, booking.staff_users, booking.supplier_contracts, booking.supplier_rates,
    booking.suppliers, booking.trip_case_countries, booking.trip_case_legs, booking.trip_case_status_history,
    booking.trip_case_status_transitions, booking.trip_case_version_itinerary, booking.trip_case_versions,
    booking.trip_plans, booking.version_item_costs, booking.v_customer_summary
    IN ACCESS EXCLUSIVE MODE;

ALTER SCHEMA booking OWNER TO aa_cis_admin;

ALTER TABLE booking.audit_logs OWNER TO aa_cis_admin;
ALTER TABLE booking.countries OWNER TO aa_cis_admin;
ALTER TABLE booking.customer_otps OWNER TO aa_cis_admin;
ALTER TABLE booking.customer_sessions OWNER TO aa_cis_admin;
ALTER TABLE booking.customers OWNER TO aa_cis_admin;
ALTER TABLE booking.fx_rates OWNER TO aa_cis_admin;
ALTER TABLE booking.hotel_room_types OWNER TO aa_cis_admin;
ALTER TABLE booking.hotels OWNER TO aa_cis_admin;
ALTER TABLE booking.inbox_cursor OWNER TO aa_cis_admin;
ALTER TABLE booking.inbox_events OWNER TO aa_cis_admin;
ALTER TABLE booking.job OWNER TO aa_cis_admin;
ALTER TABLE booking.media_files OWNER TO aa_cis_admin;
ALTER TABLE booking.notification_reads OWNER TO aa_cis_admin;
ALTER TABLE booking.notifications OWNER TO aa_cis_admin;
ALTER TABLE booking.policy_approvals OWNER TO aa_cis_admin;
ALTER TABLE booking.pricing_rules OWNER TO aa_cis_admin;
ALTER TABLE booking.services OWNER TO aa_cis_admin;
ALTER TABLE booking.settings OWNER TO aa_cis_admin;
ALTER TABLE booking.staff_assignments OWNER TO aa_cis_admin;
ALTER TABLE booking.staff_users OWNER TO aa_cis_admin;
ALTER TABLE booking.supplier_contracts OWNER TO aa_cis_admin;
ALTER TABLE booking.supplier_rates OWNER TO aa_cis_admin;
ALTER TABLE booking.suppliers OWNER TO aa_cis_admin;
ALTER TABLE booking.trip_case_countries OWNER TO aa_cis_admin;
ALTER TABLE booking.trip_case_legs OWNER TO aa_cis_admin;
ALTER TABLE booking.trip_case_status_history OWNER TO aa_cis_admin;
ALTER TABLE booking.trip_case_status_transitions OWNER TO aa_cis_admin;
ALTER TABLE booking.trip_case_version_itinerary OWNER TO aa_cis_admin;
ALTER TABLE booking.trip_case_versions OWNER TO aa_cis_admin;
ALTER TABLE booking.trip_cases OWNER TO aa_cis_admin;
ALTER TABLE booking.trip_plans OWNER TO aa_cis_admin;
ALTER TABLE booking.version_item_costs OWNER TO aa_cis_admin;
ALTER VIEW booking.v_customer_summary OWNER TO aa_cis_admin;
ALTER VIEW booking.v_schema_versions OWNER TO aa_cis_admin;
ALTER SEQUENCE booking.customer_code_seq OWNER TO aa_cis_admin;
ALTER SEQUENCE booking.hotel_code_seq OWNER TO aa_cis_admin;
ALTER SEQUENCE booking.service_code_seq OWNER TO aa_cis_admin;
ALTER SEQUENCE booking.supplier_code_seq OWNER TO aa_cis_admin;
ALTER SEQUENCE booking.trip_case_code_seq OWNER TO aa_cis_admin;
ALTER FUNCTION booking.policy_approval_maker_checker() OWNER TO aa_cis_admin;
ALTER FUNCTION booking.set_updated_at() OWNER TO aa_cis_admin;
ALTER FUNCTION booking.supplier_contract_lock() OWNER TO aa_cis_admin;
ALTER FUNCTION booking.supplier_contract_rates_fit() OWNER TO aa_cis_admin;
ALTER FUNCTION booking.supplier_rate_guard() OWNER TO aa_cis_admin;
ALTER FUNCTION booking.trip_case_check_transition() OWNER TO aa_cis_admin;
ALTER FUNCTION booking.trip_case_record_status() OWNER TO aa_cis_admin;
ALTER FUNCTION booking.trip_case_version_item_lock() OWNER TO aa_cis_admin;
ALTER FUNCTION booking.trip_case_version_item_sent_lock() OWNER TO aa_cis_admin;
ALTER FUNCTION booking.trip_case_version_lock() OWNER TO aa_cis_admin;
ALTER FUNCTION booking.trip_case_version_sent_lock() OWNER TO aa_cis_admin;
ALTER FUNCTION booking.version_item_cost_lock() OWNER TO aa_cis_admin;

ALTER DEFAULT PRIVILEGES FOR ROLE aa_cis_admin IN SCHEMA booking
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO booking;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_cis_admin IN SCHEMA booking
    GRANT USAGE, SELECT ON SEQUENCES TO booking;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_cis_admin IN SCHEMA booking
    GRANT EXECUTE ON FUNCTIONS TO booking;

ALTER DEFAULT PRIVILEGES FOR ROLE bk_owner IN SCHEMA booking
    REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM booking;
ALTER DEFAULT PRIVILEGES FOR ROLE bk_owner IN SCHEMA booking
    REVOKE USAGE, SELECT ON SEQUENCES FROM booking;
ALTER DEFAULT PRIVILEGES FOR ROLE bk_owner IN SCHEMA booking
    REVOKE EXECUTE ON FUNCTIONS FROM booking;

DO $$
DECLARE
    stray TEXT;
BEGIN
    SELECT string_agg(o, ', ' ORDER BY o) INTO stray FROM (
        SELECT format('schema booking (%s)', nspowner::regrole) AS o FROM pg_namespace
         WHERE nspname = 'booking' AND nspowner <> 'aa_cis_admin'::regrole
        UNION ALL
        SELECT format('%s %s (%s)', relkind, relname, relowner::regrole) FROM pg_class
         WHERE relnamespace = 'booking'::regnamespace AND relowner <> 'aa_cis_admin'::regrole
        UNION ALL
        SELECT format('function %s (%s)', oid::regprocedure, proowner::regrole) FROM pg_proc
         WHERE pronamespace = 'booking'::regnamespace AND proowner <> 'aa_cis_admin'::regrole
        UNION ALL
        SELECT format('type %s (%s)', typname, typowner::regrole) FROM pg_type
         WHERE typnamespace = 'booking'::regnamespace AND typowner <> 'aa_cis_admin'::regrole
    ) s;
    IF stray IS NOT NULL THEN
        RAISE EXCEPTION 'rl undo: objects in schema booking still not owned by aa_cis_admin (add them above): %', stray;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_default_acl
                WHERE defaclnamespace = 'booking'::regnamespace AND defaclrole <> 'aa_cis_admin'::regrole) THEN
        RAISE EXCEPTION 'rl undo: default privileges FOR ROLE other than aa_cis_admin remain in schema booking';
    END IF;
END $$;

INSERT INTO shared.schema_versions (version, applied_at, description)
VALUES ('rl-0NN', now(), 'AA-852 (X1 S6 rollback): undo bk-014, booking.* back to aa_cis_admin, default privileges FOR ROLE aa_cis_admin')
ON CONFLICT (version) DO NOTHING;

COMMIT;
