"""AA-859 P0 pre-flight — READ-ONLY evidence for migration 241 and the S240 waves (plan PR-0 items 1-5, + Q7).

Run inside the CIS api container (python3 + asyncpg + boto3) with the S3-mediated ECS exec pattern.
Writes ONE JSON document to s3://aa-cis-bronze-005097885195/scripts/out/s240_aa859_p0.json and prints
only `OK <bytes>` (lesson S237: ECS exec output is cut silently; read the S3 copy, check `wc -c` against
<bytes> and `json.loads` before reading). A DB failure is recorded in the JSON as "fatal", never printed.
Never prints or stores a password or a DSN, only role names.

Safety: every DB statement runs inside ONE `READ ONLY` transaction that is ROLLED BACK at the end, on the
main secret aa-cis/dev/rds (the runner, also the DB Migrate runner: same api task DATABASE_URL). GUCs
(`set_config(..., true)`) and `SET LOCAL ROLE aa_app_user` happen only inside savepoints that are always
rolled back. Nothing is granted, created, altered or written (READ ONLY refuses writes anyway). Only if
SET ROLE is refused, the catalog-view reads of item 2 use ONE read-only connection with
aa-cis/dev/rds-app-user (the tenant pool's own login; one of aa_app_user's 15 connections for seconds).
If that fallback login fails too (secret read, connect, CONNECTION LIMIT 15), the failure is recorded under
"catalog_reads_as" and only item 2's two catalog-view reads are lost (recorded as errors); every other item
still runs.

Items (plan aa859_plan.md, PR-0):
  1. Every ACL item of aa_app_user, of PUBLIC and of any role aa_app_user inherits, on every relation
     without RLS, read from pg_class.relacl / pg_attribute.attacl via aclexplode (NOT information_schema,
     which hides grants by roles the runner is not a member of, e.g. catalog_owner), with owner, grantor,
     schema, relkind, column. Classes (D1):
       a   241 will revoke: aa_app_user item, runner can act for the owner, owner not catalog_owner /
           tripplanner / booking, schema not tripplanner / booking (241's scope skips both schemas,
           whose tables aa_cis_admin owns), not the catalog contract;
       b   catalog contract (kept): schema catalog, owner catalog_owner, table level, SELECT;
       c   everything else granted to aa_app_user or a role it inherits -> MUST be empty before 241 merges;
       seq sequences (out of the 241 rule);
       PUBLIC items listed apart, with "aa_app_user has USAGE on the schema" (guard 0 input).
     Also: class-a items granted by a role other than the relation's owner (241 guard 0 raises: a REVOKE
     run as the owner leaves them), aa_app_user's role memberships (241 guard 0 raises on any), and the
     invariant query of 241 guard 4 (NO_PRIVILEGE_WITHOUT_RLS_SQL in AA-CIS-App
     tests/integration/_rls_fixture_helpers.py, same text; pre-241 it is expected to return rows).
  2. acp_contract.tour_atoms owner_scope distribution (platform / canonical lower-case uuid /
     non-canonical; tenant row exact / case-insensitive / orphan) and D9: non-platform active atoms on
     live master tours, and how many rows of catalog.v_tour_place (joins tour_atoms, 235:54-55) and
     catalog.v_tour_component (built from geo.tour_place, whose atom_ids carry atom provenance, 228:249)
     they reach, read through the views as aa_app_user.
  3. acp_shared.angle_gate_option per tenant through its parent request; acp_deliver.tenant_tour_pages
     distinct tenant_id; acp_shared.subject and acp_shared.quarter_plan (+ quarter_plan_version) per tenant.
  4. pg_stat_activity grouped by application_name (cis-api / cis-tenant / cis-worker / cis-job /
     db-migrate / tripplanner / booking ...): the D5 baseline, with max_connections and role limits.
  5. shared.job queued / running (must be 0 right before any DB Migrate apply).
  6. (not a plan item; runbook admin_atoms_tenant_callers.md Q7) shared.tenant_api_usage admin rows on
     /admin/atoms* per UTC day, method and status over 30 days: the DB side of the 14-day ECS cross-check.
     Not part of gate_241_ready.
"""
import asyncio
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

import asyncpg
import boto3

REGION = os.environ.get("AWS_REGION", "us-west-1")
MAIN_SECRET = "aa-cis/dev/rds"
APP_USER_SECRET = "aa-cis/dev/rds-app-user"
TENANT_ROLE = "aa_app_user"
MASTER = "00000000-0000-0000-0000-000000000001"
OUT_BUCKET = "aa-cis-bronze-005097885195"
OUT_KEY = "scripts/out/s240_aa859_p0.json"
STMT_TIMEOUT = "15s"
VIEW_STMT_TIMEOUT = "30s"            # v_tour_place is a heavy security-barrier view
OWNERS_241_SKIPS = ("catalog_owner", "tripplanner", "booking")   # 241 loop: explicit owner exclusion
SCHEMAS_241_SKIPS = ("tripplanner", "booking")                    # 241 loop: other apps' schemas
WRITE_PRIVS = ("INSERT", "UPDATE", "DELETE", "TRUNCATE")
PREDEFINED_DATA_ROLES = ("pg_read_all_data", "pg_write_all_data")
EXPECTED_CATALOG_CONTRACT_VIEWS = 13  # 225/228 grant SELECT on 13 catalog.v_* views (_tour_day_text not granted)


class _Undo(Exception):
    """Raised to roll a savepoint back (undoes SET LOCAL ROLE / set_config)."""


def _err(e):
    return f"{type(e).__name__}: {str(e)[:200]}"


def _parse(dsn):
    u = urlparse(dsn)
    return dict(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password,
                database=(u.path or "/").lstrip("/") or None)


async def _connect(dsn):
    p = _parse(dsn)
    return await asyncpg.connect(host=p["host"], port=p["port"], user=p["user"], password=p["password"],
                                 database=p["database"], ssl="require", timeout=20,
                                 server_settings={"application_name": "s240-aa859-p0"})


async def _savepoint(c, fn):
    """Run fn(c) in a savepoint that is always rolled back; return its value or {'error': ...}."""
    try:
        async with c.transaction():
            raise _Undo(await fn(c))
    except _Undo as u:
        return u.args[0]
    except Exception as e:  # noqa: BLE001 — record, keep probing
        return {"error": _err(e)}


def _rows(records):
    return [dict(r) for r in records]


# ── 1. ACL items on relations without RLS ─────────────────────────────────────────────────────────

# Table-level and column-level items are exploded separately (UNION ALL), so neither hides the other.
# Grantee set: PUBLIC (oid 0), aa_app_user, and every role aa_app_user inherits.
ACL_SQL = """
WITH roles AS (
    SELECT 0::oid AS oid, 'PUBLIC'::text AS role_name
    UNION ALL
    SELECT r.oid, r.rolname::text
      FROM pg_roles r
     WHERE r.rolname = 'aa_app_user'
        OR (r.rolname <> 'aa_app_user' AND pg_has_role('aa_app_user', r.oid, 'MEMBER'))
),
rels AS (
    SELECT c.oid, c.relname, c.relnamespace, ns.nspname, c.relkind, c.relowner, c.relacl
      FROM pg_class c
      JOIN pg_namespace ns ON ns.oid = c.relnamespace
     WHERE c.relkind IN ('r', 'p', 'v', 'm', 'f', 'S')
       AND NOT c.relrowsecurity
       AND ns.nspname NOT IN ('pg_catalog', 'information_schema') AND ns.nspname NOT LIKE 'pg_toast%'
),
items AS (
    SELECT r.oid AS relid, NULL::text AS column_name, a.grantor, a.grantee, a.privilege_type, a.is_grantable
      FROM rels r
     CROSS JOIN LATERAL aclexplode(r.relacl) a
    UNION ALL
    SELECT r.oid, att.attname::text, a.grantor, a.grantee, a.privilege_type, a.is_grantable
      FROM rels r
      JOIN pg_attribute att ON att.attrelid = r.oid AND att.attnum > 0 AND NOT att.attisdropped
                           AND att.attacl IS NOT NULL
     CROSS JOIN LATERAL aclexplode(att.attacl) a
)
SELECT r.nspname::text                                      AS schema,
       r.relname::text                                      AS relation,
       r.relkind::text                                      AS relkind,
       pg_get_userbyid(r.relowner)::text                    AS owner,
       i.column_name,
       ro.role_name                                         AS grantee,
       pg_get_userbyid(i.grantor)::text                     AS grantor,
       i.privilege_type,
       i.is_grantable,
       pg_has_role(current_user, r.relowner, 'USAGE')       AS runner_acts_for_owner,
       pg_has_role(current_user, i.grantor, 'USAGE')        AS runner_acts_for_grantor,
       (i.grantor = r.relowner)                             AS grantor_is_owner,
       has_schema_privilege('aa_app_user', r.relnamespace, 'USAGE') AS aa_app_user_schema_usage
  FROM items i
  JOIN rels r ON r.oid = i.relid
  JOIN roles ro ON ro.oid = i.grantee
 ORDER BY 1, 2, 5 NULLS FIRST, 6, 8
"""

# The invariant of 241 guard 4, the same text as NO_PRIVILEGE_WITHOUT_RLS_SQL in AA-CIS-App
# tests/integration/_rls_fixture_helpers.py (a CI test pins the migration to it). Not the plan's D1 draft:
# its LEFT JOIN pg_attribute / COALESCE(att.attacl, c.relacl) hides the table-level items of a relation
# that also has a column grant, and its plain `relowner = to_regrole(...)` hides violations when the role
# is missing. Pre-241 it is expected to return rows; post-241 (probe v3) it must return none.
D1_INVARIANT_SQL = """
SELECT c.oid::regclass::text AS rel, a.privilege_type, NULL::text AS column_name
  FROM pg_class c
  JOIN pg_namespace ns ON ns.oid = c.relnamespace
 CROSS JOIN LATERAL aclexplode(c.relacl) a
 WHERE c.relkind IN ('r', 'p', 'v', 'm', 'f')
   AND NOT c.relrowsecurity
   AND ns.nspname NOT IN ('pg_catalog', 'information_schema')
   AND ns.nspname NOT LIKE 'pg_toast%'
   AND a.grantee = 'aa_app_user'::regrole
   AND NOT (ns.nspname = 'catalog'
            AND c.relowner IS NOT DISTINCT FROM to_regrole('catalog_owner')
            AND a.privilege_type = 'SELECT')
UNION ALL
SELECT c.oid::regclass::text, a.privilege_type, att.attname::text
  FROM pg_class c
  JOIN pg_namespace ns ON ns.oid = c.relnamespace
  JOIN pg_attribute att ON att.attrelid = c.oid AND att.attacl IS NOT NULL AND NOT att.attisdropped
 CROSS JOIN LATERAL aclexplode(att.attacl) a
 WHERE c.relkind IN ('r', 'p', 'v', 'm', 'f')
   AND NOT c.relrowsecurity
   AND ns.nspname NOT IN ('pg_catalog', 'information_schema')
   AND ns.nspname NOT LIKE 'pg_toast%'
   AND a.grantee = 'aa_app_user'::regrole
ORDER BY 1, 3, 2"""

APP_USER_ROLE_SQL = """
SELECT r.rolsuper, r.rolbypassrls, r.rolconnlimit, r.rolinherit,
       ARRAY(SELECT m.member::regrole::text FROM pg_auth_members m WHERE m.roleid = r.oid ORDER BY 1)
           AS members,
       ARRAY(SELECT o.rolname::text FROM pg_roles o
              WHERE o.rolname <> r.rolname AND pg_has_role(r.oid, o.oid, 'MEMBER') ORDER BY 1)
           AS member_of
  FROM pg_roles r
 WHERE r.rolname = 'aa_app_user'
"""


def _classify(row):
    """D1 rule, written once. Returns 'a' | 'b' | 'c' | 'seq' | 'public'."""
    if row["relkind"] == "S":
        return "seq"
    if row["grantee"] == "PUBLIC":
        return "public"
    if row["grantee"] != TENANT_ROLE:
        return "c"                                     # inherited role: 241's loop never names it
    if (row["schema"] == "catalog" and row["owner"] == "catalog_owner" and row["column_name"] is None
            and row["privilege_type"] == "SELECT"):
        return "b"
    if row["schema"] in SCHEMAS_241_SKIPS:
        return "c"                                     # 241 scope skips the schema: guard 0 raises
    if row["runner_acts_for_owner"] and row["owner"] not in OWNERS_241_SKIPS:
        return "a"
    return "c"


def _fq(row):
    return f'{row["schema"]}.{row["relation"]}'


async def _item1(c, out):
    rows = _rows(await c.fetch(ACL_SQL))
    for r in rows:
        r["class"] = _classify(r)
    by_class = {k: [r for r in rows if r["class"] == k] for k in ("a", "b", "c", "seq", "public")}
    role = await c.fetchrow(APP_USER_ROLE_SQL)
    role = dict(role) if role else None
    member_of = list(role["member_of"]) if role else []
    public_write = [r for r in by_class["public"]
                    if r["aa_app_user_schema_usage"] and r["privilege_type"] in WRITE_PRIVS]
    public_select = [r for r in by_class["public"]
                     if r["aa_app_user_schema_usage"] and r["privilege_type"] not in WRITE_PRIVS]
    a_foreign_grantor = [r for r in by_class["a"] if not r["grantor_is_owner"]]   # 241 guard 0 rule
    catalog_contract = sorted({_fq(r) for r in by_class["b"]})
    d1 = await _savepoint(c, lambda cc: cc.fetch(D1_INVARIANT_SQL))
    d1 = ({"error": d1["error"]} if isinstance(d1, dict)
          else {"rows": [{"rel": r["rel"], "privilege_type": r["privilege_type"],
                          "column_name": r["column_name"]} for r in d1]})
    out["item1_acl"] = {
        "aa_app_user_role": role,
        "items": rows,
        "counts": {k: len(v) for k, v in by_class.items()},
        "revoke_241_relations": sorted({_fq(r) for r in by_class["a"]}),
        "catalog_contract_relations": catalog_contract,
        "class_c": by_class["c"],
        "class_a_foreign_grantor": a_foreign_grantor,
        "public_write_in_aa_app_user_schemas": public_write,
        "public_select_in_aa_app_user_schemas": [
            {"relation": _fq(r), "column": r["column_name"], "privilege_type": r["privilege_type"]}
            for r in public_select],
        "predefined_data_roles_inherited": [x for x in member_of if x in PREDEFINED_DATA_ROLES],
        "d1_invariant_241_guard4": d1,
    }
    out["verdict"]["item1_class_c_empty"] = not by_class["c"]
    out["verdict"]["item1_class_a_grantors_ok"] = not a_foreign_grantor
    out["verdict"]["item1_no_public_write"] = not public_write
    out["verdict"]["item1_no_predefined_data_roles"] = not out["item1_acl"]["predefined_data_roles_inherited"]
    out["verdict"]["item1_member_of_no_role"] = bool(role) and not member_of      # 241 guard 0a
    out["verdict"]["item1_catalog_contract_count"] = len(catalog_contract)
    out["verdict"]["item1_catalog_contract_count_as_expected"] = (
        len(catalog_contract) == EXPECTED_CATALOG_CONTRACT_VIEWS)


# ── 2. tour_atoms owner_scope + D9 ────────────────────────────────────────────────────────────────

ATOM_SCOPE_SQL = """
WITH s AS (
    SELECT CASE WHEN a.owner_scope = 'platform' THEN 'platform'
                WHEN a.owner_scope ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                    THEN 'canonical_uuid'
                ELSE 'non_canonical' END                       AS scope_class,
           a.owner_scope = 'platform'                          AS is_platform,
           t_exact.tenant_id IS NOT NULL                       AS tenant_exact,
           t_ci.tenant_id IS NOT NULL                          AS tenant_ci,
           (NOT a.deleted AND NOT a.is_empty_marker)           AS active,
           a.owner_scope, a.tour_id
      FROM acp_contract.tour_atoms a
      LEFT JOIN shared.tenants t_exact ON t_exact.tenant_id::text = a.owner_scope
      LEFT JOIN shared.tenants t_ci    ON t_ci.tenant_id::text = lower(btrim(a.owner_scope))
)
SELECT scope_class,
       CASE WHEN is_platform THEN NULL ELSE tenant_exact END  AS tenant_row_exact,
       CASE WHEN is_platform THEN NULL ELSE tenant_ci END     AS tenant_row_case_insensitive,
       count(*)                                               AS atoms,
       count(*) FILTER (WHERE active)                         AS active_atoms,
       count(DISTINCT owner_scope)                            AS scopes,
       count(DISTINCT tour_id)                                AS tours
  FROM s
 GROUP BY 1, 2, 3
 ORDER BY 1, 2, 3
"""

ATOM_SCOPE_DETAIL_SQL = """
SELECT a.owner_scope,
       t.slug::text                                                   AS tenant_slug,
       count(*)                                                       AS atoms,
       count(*) FILTER (WHERE NOT a.deleted AND NOT a.is_empty_marker) AS active_atoms,
       count(DISTINCT a.tour_id)                                      AS tours
  FROM acp_contract.tour_atoms a
  LEFT JOIN shared.tenants t ON t.tenant_id::text = lower(btrim(a.owner_scope))
 WHERE a.owner_scope <> 'platform'
 GROUP BY 1, 2
 ORDER BY 3 DESC, 1
 LIMIT 100
"""

# Live master tours = the base-table rule of catalog.v_tour (225:142-157); np = non-platform active atoms
# on them (the v_active_tour_atoms rule the catalog views apply, 225:257-258).
D9_CTE = """
WITH live AS (
    SELECT pt.tour_id
      FROM gold_aa_internal.published_tours pt
      JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = pt.tour_id
     WHERE pt.tenant_id = '00000000-0000-0000-0000-000000000001'::uuid
       AND pt.master_status = 'active'
       AND pt.deleted_at IS NULL
       AND rt.source_status = 'active'
       AND rt.deleted_at IS NULL
),
np AS (
    SELECT a.atom_id, a.tour_id, a.owner_scope, a.itinerary_day, a.place
      FROM acp_contract.tour_atoms a
      JOIN live l ON l.tour_id = a.tour_id
     WHERE NOT a.deleted AND NOT a.is_empty_marker AND a.owner_scope <> 'platform'
)"""

D9_SUMMARY_SQL = D9_CTE + """
SELECT (SELECT count(*) FROM live)                                       AS live_master_tours,
       count(*)                                                          AS np_active_atoms,
       count(DISTINCT tour_id)                                           AS np_tours,
       count(DISTINCT owner_scope)                                       AS np_scopes,
       count(*) FILTER (WHERE place IS NOT NULL AND btrim(place) <> '') AS np_atoms_with_place
  FROM np
"""

D9_BY_SCOPE_SQL = D9_CTE + """
SELECT owner_scope, count(*) AS np_active_atoms, count(DISTINCT tour_id) AS tours
  FROM np
 GROUP BY 1
 ORDER BY 2 DESC, 1
 LIMIT 50
"""

# v_tour_place groups (tour, day, lower(btrim(place))) that contain a non-platform atom; np_only = no
# active platform atom in the same group, i.e. the view row exists only because of tenant atoms.
D9_PLACE_GROUPS_SQL = D9_CTE + """,
g AS (
    SELECT tour_id, itinerary_day, lower(btrim(place)) AS place_key, count(*) AS np_atoms
      FROM np
     WHERE place IS NOT NULL AND btrim(place) <> ''
     GROUP BY 1, 2, 3
)
SELECT g.tour_id, g.itinerary_day::int AS day, g.place_key, g.np_atoms,
       NOT EXISTS (SELECT 1
                     FROM acp_contract.tour_atoms p
                    WHERE p.tour_id = g.tour_id
                      AND p.owner_scope = 'platform'
                      AND NOT p.deleted AND NOT p.is_empty_marker
                      AND p.itinerary_day IS NOT DISTINCT FROM g.itinerary_day
                      AND p.place IS NOT NULL
                      AND lower(btrim(p.place)) = g.place_key) AS np_only
  FROM g
"""

# geo.tour_place components (source of catalog.v_tour_component) whose atom provenance holds a
# non-platform atom in any state; np_only = no platform atom among them.
D9_COMPONENTS_SQL = """
SELECT gp.component_id,
       NOT EXISTS (SELECT 1 FROM acp_contract.tour_atoms p
                    WHERE p.atom_id = ANY(gp.atom_ids) AND p.owner_scope = 'platform') AS np_only
  FROM geo.tour_place gp
 WHERE EXISTS (SELECT 1 FROM acp_contract.tour_atoms a
                WHERE a.atom_id = ANY(gp.atom_ids) AND a.owner_scope <> 'platform')
"""

# Read as aa_app_user (catalog contract SELECT): rows of the views those keys reach.
VIEW_PLACE_SQL = """
SELECT count(*)                                AS rows,
       count(*) FILTER (WHERE k.np_only)       AS np_only_rows,
       COALESCE(sum(p.atom_count), 0)::bigint  AS atom_count_sum,
       count(DISTINCT p.tour_id)               AS tours
  FROM catalog.v_tour_place p
  JOIN unnest($1::uuid[], $2::int[], $3::text[], $4::bool[]) AS k(tour_id, day, place_key, np_only)
    ON p.tour_id = k.tour_id
   AND p.day_number IS NOT DISTINCT FROM k.day
   AND lower(p.place_name) = k.place_key
 WHERE p.tour_id = ANY($1::uuid[])
"""

VIEW_COMPONENT_SQL = """
SELECT count(*)                                                  AS rows,
       count(*) FILTER (WHERE component_id = ANY($2::uuid[]))    AS np_only_rows,
       count(DISTINCT tour_id)                                   AS tours
  FROM catalog.v_tour_component
 WHERE component_id = ANY($1::uuid[])
"""


async def _as_master_runner(c, fn):
    """Runner reads of published_tours / raw_tours (FORCE RLS): pin app.tenant_id to the master tenant in
    a savepoint, so the master rows are visible whether or not the runner is filtered."""
    async def run(cc):
        await cc.execute("SELECT set_config('app.tenant_id', $1, true)", MASTER)
        return await fn(cc)
    return await _savepoint(c, run)


async def _as_reader(c, reader, fn):
    """Catalog-view reads as aa_app_user: SET LOCAL ROLE on the runner connection when allowed, else the
    tenant-pool login (reader) in its own read-only transaction. Always rolled back."""
    async def run(cc):
        await cc.execute(f"SET LOCAL statement_timeout = '{VIEW_STMT_TIMEOUT}'")
        if reader is None:
            await cc.execute(f'SET LOCAL ROLE "{TENANT_ROLE}"')
        await cc.execute("SELECT set_config('app.tenant_id', '', true)")   # no tenant: catalog rows only
        return await fn(cc)
    return await _savepoint(reader if reader is not None else c, run)


async def _item2(c, reader, out):
    d = {"scope_classes": _rows(await c.fetch(ATOM_SCOPE_SQL)),
         "non_platform_scopes": _rows(await c.fetch(ATOM_SCOPE_DETAIL_SQL))}
    d["runner_rls_active"] = {t: await c.fetchval("SELECT row_security_active($1::regclass)", t)
                              for t in ("gold_aa_internal.published_tours", "silver_aa_internal.raw_tours")}

    d9 = {}
    summ = await _as_master_runner(c, lambda cc: cc.fetchrow(D9_SUMMARY_SQL))
    d9["summary"] = dict(summ) if not isinstance(summ, dict) else summ
    by_scope = await _as_master_runner(c, lambda cc: cc.fetch(D9_BY_SCOPE_SQL))
    d9["by_scope"] = _rows(by_scope) if not isinstance(by_scope, dict) else by_scope

    groups = await _as_master_runner(c, lambda cc: cc.fetch(D9_PLACE_GROUPS_SQL))
    if isinstance(groups, dict):
        d9["v_tour_place"] = groups
    else:
        g = _rows(groups)
        place = {"groups": len(g), "np_only_groups": sum(1 for x in g if x["np_only"]),
                 "np_atoms_in_groups": sum(x["np_atoms"] for x in g)}
        if g:
            args = ([x["tour_id"] for x in g], [x["day"] for x in g], [x["place_key"] for x in g],
                    [x["np_only"] for x in g])
            seen = await _as_reader(c, reader, lambda cc: cc.fetchrow(VIEW_PLACE_SQL, *args))
            place["through_view_as_aa_app_user"] = dict(seen) if not isinstance(seen, dict) else seen
        else:
            place["through_view_as_aa_app_user"] = {"rows": 0, "np_only_rows": 0, "skipped": "no groups"}
        d9["v_tour_place"] = place

    comps = await _savepoint(c, lambda cc: cc.fetch(D9_COMPONENTS_SQL))
    if isinstance(comps, dict):
        d9["v_tour_component"] = comps
    else:
        cr = _rows(comps)
        comp = {"geo_components_with_np_atoms": len(cr),
                "geo_components_np_only": sum(1 for x in cr if x["np_only"])}
        if cr:
            ids = [x["component_id"] for x in cr]
            only = [x["component_id"] for x in cr if x["np_only"]]
            seen = await _as_reader(c, reader, lambda cc: cc.fetchrow(VIEW_COMPONENT_SQL, ids, only))
            comp["through_view_as_aa_app_user"] = dict(seen) if not isinstance(seen, dict) else seen
        else:
            comp["through_view_as_aa_app_user"] = {"rows": 0, "np_only_rows": 0, "skipped": "no components"}
        d9["v_tour_component"] = comp

    d["d9"] = d9
    out["item2_tour_atoms"] = d
    s = d9["summary"] if isinstance(d9.get("summary"), dict) else {}
    out["verdict"]["d9_np_active_atoms_on_live_master_tours"] = s.get("np_active_atoms")
    out["verdict"]["d9_v_tour_place_rows"] = (d9.get("v_tour_place", {})
                                              .get("through_view_as_aa_app_user", {}).get("rows"))
    out["verdict"]["d9_v_tour_component_rows"] = (d9.get("v_tour_component", {})
                                                  .get("through_view_as_aa_app_user", {}).get("rows"))
    out["verdict"]["item2_non_canonical_or_orphan_scopes"] = sum(
        r["atoms"] for r in d["scope_classes"]
        if r["scope_class"] != "platform" and (r["scope_class"] == "non_canonical" or not r["tenant_row_exact"]))


# ── 3. per-tenant baselines for wave 3 / 4 tables ─────────────────────────────────────────────────

AGO_SQL = """
SELECT r.tenant_id::text                          AS tenant_id,
       count(o.option_id)                         AS options,
       count(DISTINCT o.request_id)               AS requests,
       count(*) FILTER (WHERE o.chosen)           AS chosen
  FROM acp_shared.angle_gate_option o
  LEFT JOIN acp_shared.angle_gate_request r ON r.request_id = o.request_id
 GROUP BY 1
 ORDER BY 2 DESC, 1 NULLS FIRST
"""

TTP_SQL = """
SELECT p.tenant_id,
       p.tenant_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' AS canonical_uuid,
       EXISTS (SELECT 1 FROM shared.tenants t WHERE t.tenant_id::text = p.tenant_id)  AS tenant_row,
       count(*)                                                                     AS pages
  FROM acp_deliver.tenant_tour_pages p
 GROUP BY 1
 ORDER BY 4 DESC, 1
"""

SUBJECT_SQL = """
SELECT tenant_id::text AS tenant_id, state, count(*) AS subjects
  FROM acp_shared.subject
 GROUP BY 1, 2
 ORDER BY 1, 2
"""

QUARTER_PLAN_SQL = """
SELECT q.tenant_id::text            AS tenant_id,
       count(DISTINCT q.plan_id)    AS plans,
       count(v.version_id)          AS versions
  FROM acp_shared.quarter_plan q
  LEFT JOIN acp_shared.quarter_plan_version v ON v.plan_id = q.plan_id
 GROUP BY 1
 ORDER BY 2 DESC, 1
"""

QPV_ORPHAN_SQL = """
SELECT count(*) FROM acp_shared.quarter_plan_version v
 WHERE NOT EXISTS (SELECT 1 FROM acp_shared.quarter_plan q WHERE q.plan_id = v.plan_id)
"""


async def _item3(c, out):
    async def grab(sql):
        v = await _savepoint(c, lambda cc: cc.fetch(sql))
        return _rows(v) if not isinstance(v, dict) else v
    ago = await grab(AGO_SQL)
    out["item3_per_tenant"] = {
        "angle_gate_option_by_parent_tenant": ago,
        "tenant_tour_pages_by_tenant": await grab(TTP_SQL),
        "subject_by_tenant_state": await grab(SUBJECT_SQL),
        "quarter_plan_by_tenant": await grab(QUARTER_PLAN_SQL),
        "quarter_plan_version_orphans": await _savepoint(c, lambda cc: cc.fetchval(QPV_ORPHAN_SQL)),
    }
    if isinstance(ago, list):
        out["verdict"]["item3_angle_gate_option_orphans"] = sum(
            r["options"] for r in ago if r["tenant_id"] is None)


# ── 4. connections by application_name (D5 baseline) ──────────────────────────────────────────────

ACTIVITY_SQL = """
SELECT COALESCE(NULLIF(application_name, ''), '(none)') AS application_name,
       COALESCE(usename::text, '(none)')                AS usename,
       COALESCE(state, '(n/a)')                         AS state,
       count(*)                                         AS n
  FROM pg_stat_activity
 WHERE pid <> pg_backend_pid()
   AND application_name IS DISTINCT FROM 's240-aa859-p0'
   AND usename IS NOT NULL
   -- backend_type / state read NULL for other roles' sessions without pg_read_all_stats
   AND COALESCE(backend_type, 'client backend') = 'client backend'
 GROUP BY 1, 2, 3
 ORDER BY 1, 2, 3
"""

ROLE_LIMITS_SQL = """
SELECT rolname::text AS role, rolconnlimit
  FROM pg_roles
 WHERE rolcanlogin AND rolname NOT LIKE 'rds%'
 ORDER BY 1
"""


async def _item4(c, out):
    rows = _rows(await c.fetch(ACTIVITY_SQL))
    by_app, by_user = {}, {}
    for r in rows:
        by_app[r["application_name"]] = by_app.get(r["application_name"], 0) + r["n"]
        by_user[r["usename"]] = by_user.get(r["usename"], 0) + r["n"]
    out["item4_connections"] = {
        "max_connections": await c.fetchval("SHOW max_connections"),
        "superuser_reserved_connections": await c.fetchval("SHOW superuser_reserved_connections"),
        "by_application_name": by_app,
        "by_usename": by_user,
        "detail": rows,
        "login_role_limits": _rows(await c.fetch(ROLE_LIMITS_SQL)),
        "note": "excludes this probe's own backend (and its fallback login, application_name s240-aa859-p0, "
                "if used); state reads (n/a) for other roles' sessions without pg_read_all_stats",
    }


# ── 5. shared.job idle check ──────────────────────────────────────────────────────────────────────

JOB_SQL = """
SELECT status, kind, count(*) AS n, min(created_at) AS oldest_created_at, max(locked_until) AS max_locked_until
  FROM shared.job
 WHERE status IN ('queued', 'running')
 GROUP BY 1, 2
 ORDER BY 1, 2
"""


async def _item5(c, out):
    rows = _rows(await c.fetch(JOB_SQL))
    queued = sum(r["n"] for r in rows if r["status"] == "queued")
    running = sum(r["n"] for r in rows if r["status"] == "running")
    out["item5_job"] = {"queued": queued, "running": running, "by_kind": rows}
    out["verdict"]["item5_job_idle"] = queued == 0 and running == 0


# ── 6. /admin/atoms* admin-authenticated calls (runbook Q7) ──────────────────────────────────────

# _track_admin_call (api/middleware/rate_limit.py) writes a row only when X-Admin-Secret matches; endpoint =
# request.url.path. Day in UTC so it lines up with the Logs Insights bin(1d) of the ECS access log (Q5).
ADMIN_ATOMS_USAGE_SQL = """
SELECT (called_at AT TIME ZONE 'UTC')::date AS day, method, status_code, count(*) AS n
  FROM shared.tenant_api_usage
 WHERE actor_type = 'admin' AND endpoint LIKE '/admin/atoms%' AND called_at >= now() - interval '30 days'
 GROUP BY 1, 2, 3
 ORDER BY 1, 2, 3
"""


async def _item6(c, out):
    rows = _rows(await c.fetch(ADMIN_ATOMS_USAGE_SQL))
    out["item6_admin_atoms_usage"] = {
        "window": "30 days, UTC days",
        "by_day_method_status": rows,
        "total": sum(r["n"] for r in rows),
        "status_200": sum(r["n"] for r in rows if r["status_code"] == 200),
    }


# ── main ──────────────────────────────────────────────────────────────────────────────────────────

async def _main(out):
    sm = boto3.client("secretsmanager", region_name=REGION)
    main_dsn = sm.get_secret_value(SecretId=MAIN_SECRET)["SecretString"].strip()
    c = await _connect(main_dsn)
    a = atr = None
    try:
        tr = c.transaction(readonly=True)
        await tr.start()
        try:
            await c.execute(f"SET LOCAL statement_timeout = '{STMT_TIMEOUT}'")
            await c.execute("SET LOCAL lock_timeout = '3s'")
            out["identity"] = dict(await c.fetchrow(
                "SELECT current_user AS cu, session_user AS su, r.rolsuper, r.rolbypassrls, "
                "pg_has_role(current_user, to_regrole('rds_superuser'), 'MEMBER') AS rds_superuser_member, "
                "current_setting('server_version') AS ver, "
                "current_setting('transaction_read_only') AS read_only "
                "FROM pg_roles r WHERE r.rolname = current_user"))
            out["schema_versions_latest"] = await c.fetchval(
                "SELECT max(version::int) FROM shared.schema_versions WHERE version ~ '^[0-9]+$'")
            out["schema_version_241_present"] = await c.fetchval(
                "SELECT EXISTS (SELECT 1 FROM shared.schema_versions WHERE version = '241')")
            can_set = await _savepoint(c, lambda cc: cc.execute(f'SET LOCAL ROLE "{TENANT_ROLE}"'))
            out["set_role_aa_app_user"] = "ok" if not isinstance(can_set, dict) else can_set
            if isinstance(can_set, dict):
                # SET ROLE refused: catalog-view reads use the tenant-pool login, read-only, rolled back.
                # A failure here (secret read, connect, CONNECTION LIMIT 15) is recorded and the probe goes
                # on: with a = None, _as_reader retries SET LOCAL ROLE, which fails again and is recorded
                # under item 2's through_view_as_aa_app_user; items 1, 3-6 are unaffected.
                try:
                    app_dsn = sm.get_secret_value(SecretId=APP_USER_SECRET)["SecretString"].strip()
                    reader_user = _parse(app_dsn)["user"]
                    a = await _connect(app_dsn)
                    atr = a.transaction(readonly=True)
                    await atr.start()
                    out["catalog_reads_as"] = f"login {reader_user} (SET ROLE refused)"
                except Exception as e:  # noqa: BLE001 — record, keep probing
                    out["catalog_reads_as"] = {"error": _err(e), "set_role": "refused"}
                    if a is not None:
                        try:
                            await a.close()
                        except Exception:  # noqa: BLE001
                            pass
                    a, atr = None, None
            else:
                out["catalog_reads_as"] = f"runner + SET LOCAL ROLE {TENANT_ROLE}"
            try:
                for name, step in (("item1", lambda: _item1(c, out)), ("item2", lambda: _item2(c, a, out)),
                                   ("item3", lambda: _item3(c, out)), ("item4", lambda: _item4(c, out)),
                                   ("item5", lambda: _item5(c, out)), ("item6", lambda: _item6(c, out))):
                    try:
                        async with c.transaction():        # savepoint: one failed item never aborts the rest
                            await step()
                    except Exception as e:  # noqa: BLE001 — record, keep probing
                        out["errors"][name] = _err(e)
            finally:
                if atr is not None:
                    await atr.rollback()
        finally:
            await tr.rollback()
    finally:
        if a is not None:
            await a.close()
        await c.close()


async def main():
    out = {"probe": "s240_aa859_p0", "issue": "AA-859", "phase": "pre-241",
           "started_at": datetime.now(timezone.utc).isoformat(), "verdict": {}, "errors": {}}
    try:
        await _main(out)
    except Exception as e:  # noqa: BLE001 — always upload one JSON document, with what was collected
        out["fatal"] = _err(e)
    v = out["verdict"]
    v["gate_241_ready"] = bool(v.get("item1_class_c_empty") and v.get("item1_class_a_grantors_ok")
                               and v.get("item1_no_public_write") and v.get("item1_no_predefined_data_roles")
                               and v.get("item1_member_of_no_role")
                               and not (set(out["errors"]) - {"item6"}) and "fatal" not in out)
    out["finished_at"] = datetime.now(timezone.utc).isoformat()
    body = json.dumps(out, default=str, separators=(",", ":")).encode()
    try:
        boto3.client("s3", region_name=REGION).put_object(
            Bucket=OUT_BUCKET, Key=OUT_KEY, Body=body, ContentType="application/json")
    except Exception as e:  # noqa: BLE001
        print(f"ERR s3 {type(e).__name__}")
        return
    print(f"OK {len(body)}")


asyncio.run(main())
