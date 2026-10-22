"""AA-859 S247 wave 4 — READ-ONLY preflight (and postflight) for CIS migrations 265 and 266, modelled on
aa859_262_preflight.py.

Run inside the CIS api container with the S3-mediated ECS exec pattern (python3 + asyncpg + boto3):

    python3 aa859_w4_preflight.py pre-265    # before DB Migrate apply of 265
    python3 aa859_w4_preflight.py post-265   # after it
    python3 aa859_w4_preflight.py pre-266    # before DB Migrate apply of 266 (after 254 and 265)
    python3 aa859_w4_preflight.py post-266   # after it

Connects with the container's own DSN over SSL (ssl="require"; the CIS runtime role cis_app since X1 S18). One READ
ONLY transaction, rolled back. Nothing is granted, created, altered or written. Writes ONE JSON document to
s3://aa-cis-bronze-005097885195/scripts/out/s247_aa859_w4_<mode>.json and prints only `OK <bytes>` (ECS exec cuts
output silently: read the S3 copy). Never prints or stores a DSN or a password.

What it reads:
  * the five 265 tables (acp_shared.subject, quarter_plan, quarter_plan_version, year_plan,
    acp_deliver.tenant_tour_pages): RLS / FORCE, owner, every ACL item (relacl + attacl, grantor), policies with their
    expressions, dependent views and owners, the key column, row count (and distinct tenants), non-canonical
    tenant_tour_pages ids;
  * the 7 platform relations: RLS, tenant_id / owner_scope columns, aa_app_user's privileges; USAGE on acp_contract;
  * acp_contract.tour_atoms: the same as a 265 table, plus every grantee (table and column level: tripplanner must be
    gone, CIS 254), D9 (live non-platform atoms on live master tours), non-canonical owner_scope values, and EXPLAIN
    (ANALYZE) of two worker-shaped reads (the members read of the pick path on the base table and a tour_atoms
    tour_id = ANY read) for the before / after comparison (lesson S238). TripPlanner's catalog.v_tour_place /
    v_tour_component EXPLAIN needs a catalog reader (cis_app has no USAGE on catalog): it is attempted and recorded
    as skipped when refused; run it from TripPlanner's side or a DB Migrate run-script;
  * aa_app_user / cis_app / cis_owner attributes and memberships; invariant v1 (241 guard 4) and v2 (265 / 266 guard
    5) violations; the last CIS migration and 254 / 265 / 266 registration; shared.job and booking.job queued /
    running (DB Migrate refuses to apply otherwise; booking.job recorded as skipped when cis_app cannot read it).

Verdicts: gate_265_ready / post_265_ok / gate_266_ready / post_266_ok with the reasons when false.
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

import asyncpg
import boto3

BUCKET = "aa-cis-bronze-005097885195"
MASTER = "00000000-0000-0000-0000-000000000001"
# 265 review fix: aa_app_user reads only (card_id, status) of acp_shared.place_card (column grants); every other platform
# relation is table-level SELECT. The invariant query reports column grants, so these two are expected, not violations.
PLATFORM_READ_COLUMNS = {("acp_shared.place_card", "card_id"), ("acp_shared.place_card", "status")}
EXPECTED_PRIVS = {"acp_shared.place_card": ["SELECT(card_id)", "SELECT(status)"]}

T265 = ("acp_shared.subject", "acp_shared.quarter_plan", "acp_shared.quarter_plan_version", "acp_shared.year_plan",
        "acp_deliver.tenant_tour_pages")
PLATFORM = ("acp_contract.route", "acp_contract.atom_segment", "acp_contract.atom_segment_member",
            "acp_contract.atom_segment_alias", "acp_shared.place_card", "acp_shared.place_card_alias",
            "acp_shared.atom_place_card")
ATOMS = "acp_contract.tour_atoms"
CANONICAL = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
PRIVS_265 = {
    "acp_shared.subject": {"SELECT", "UPDATE(state)"},
    "acp_shared.year_plan": {"SELECT", "INSERT(tenant_id)", "INSERT(year)"},
    "acp_shared.quarter_plan": {"SELECT", "INSERT(tenant_id)", "INSERT(year)", "INSERT(quarter)",
                                "INSERT(year_plan_id)", "UPDATE(year_plan_id)", "UPDATE(current_version_id)"},
    "acp_shared.quarter_plan_version": {"SELECT", "INSERT(plan_id)", "INSERT(version_no)", "INSERT(payload)",
                                        "INSERT(source)", "INSERT(approval_status)", "UPDATE(approval_status)",
                                        "UPDATE(approved_by)", "UPDATE(approved_at)"},
    "acp_deliver.tenant_tour_pages": {"SELECT"},
}
POLICIES_265 = {t: sorted([f"{t.split('.')[1]}_cis_app_all", "tenant_isolation"]
                          + (["aa_app_user_aa_master_read"] if t.endswith("tenant_tour_pages") else []))
                for t in T265}
POLICIES_266 = sorted(["atoms_platform_read", "catalog_owner_read", "tenant_isolation", "tour_atoms_cis_app_all"])

_V1_HEAD = """\
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
            AND a.privilege_type = 'SELECT')"""
_V2_EXTRA = """
   AND NOT (ns.nspname || '.' || c.relname = ANY (ARRAY['acp_contract.route', 'acp_contract.atom_segment',
                                                        'acp_contract.atom_segment_member',
                                                        'acp_contract.atom_segment_alias', 'acp_shared.place_card',
                                                        'acp_shared.place_card_alias', 'acp_shared.atom_place_card'])
            AND a.privilege_type = 'SELECT')"""
_V1_TAIL = """
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
INVARIANT_V1 = _V1_HEAD + _V1_TAIL
INVARIANT_V2 = _V1_HEAD + _V2_EXTRA + _V1_TAIL

# The pick path's member read on the base table (services/acp_shared/subject_seed.py _MEMBERS_SQL, wave 4).
MEMBERS_SQL = """
    SELECT m.segment_id, ta.atom_id, ta.tour_id::text AS tour_id, ta.place, ta.evidence,
           rt.country, apc.card_id::text AS card_id
    FROM acp_contract.atom_segment_member m
    JOIN acp_contract.tour_atoms ta ON ta.atom_id = m.atom_id
    JOIN gold_aa_internal.published_tours pt
      ON pt.tour_id = ta.tour_id AND pt.master_status = 'active' AND pt.deleted_at IS NULL
    LEFT JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = ta.tour_id
    LEFT JOIN acp_shared.atom_place_card apc ON apc.atom_id = ta.atom_id
    WHERE m.segment_id = ANY($1::text[]) AND NOT m.is_alias
      AND ta.owner_scope IN ('platform', $2::text) AND NOT ta.deleted AND NOT ta.is_empty_marker
"""
ATOMS_BY_TOUR_SQL = "SELECT atom_id, place FROM acp_contract.tour_atoms WHERE tour_id = ANY($1::uuid[]) AND NOT deleted"
CATALOG_SQL = "SELECT * FROM catalog.v_tour_place WHERE source_id = ANY($1::text[])"


async def _table(conn, t):
    out = {}
    r = await conn.fetchrow("""SELECT c.relrowsecurity, c.relforcerowsecurity, pg_get_userbyid(c.relowner) AS owner
                                 FROM pg_class c WHERE c.oid = $1::regclass""", t)
    out.update(rls=r["relrowsecurity"], force=r["relforcerowsecurity"], owner=r["owner"])
    out["acl"] = [dict(x) for x in await conn.fetch("""
        SELECT CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE a.grantee::regrole::text END AS grantee,
               a.grantor::regrole::text AS grantor, a.privilege_type AS priv, NULL::text AS col
          FROM pg_class c, aclexplode(c.relacl) a WHERE c.oid = $1::regclass
        UNION ALL
        SELECT CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE a.grantee::regrole::text END,
               a.grantor::regrole::text, a.privilege_type, att.attname::text
          FROM pg_attribute att, aclexplode(att.attacl) a
         WHERE att.attrelid = $1::regclass AND att.attacl IS NOT NULL AND NOT att.attisdropped
         ORDER BY 1, 4, 3""", t)]
    out["policies"] = [dict(x) for x in await conn.fetch("""
        SELECT polname::text AS name, polpermissive AS permissive, polcmd::text AS cmd,
               polroles::regrole[]::text[] AS roles, pg_get_expr(polqual, polrelid) AS using,
               pg_get_expr(polwithcheck, polrelid) AS with_check
          FROM pg_policy WHERE polrelid = $1::regclass ORDER BY polname""", t)]
    out["dependent_views"] = [dict(x) for x in await conn.fetch("""
        SELECT DISTINCT v.oid::regclass::text AS view, pg_get_userbyid(v.relowner) AS owner
          FROM pg_depend d JOIN pg_rewrite rw ON rw.oid = d.objid JOIN pg_class v ON v.oid = rw.ev_class
         WHERE d.classid = 'pg_rewrite'::regclass AND d.refclassid = 'pg_class'::regclass
           AND d.refobjid = $1::regclass AND v.oid <> $1::regclass""", t)]
    out["columns"] = {r["attname"]: {"type": r["type"], "not_null": r["attnotnull"]} for r in await conn.fetch("""
        SELECT attname, format_type(atttypid, atttypmod) AS type, attnotnull FROM pg_attribute
         WHERE attrelid = $1::regclass AND attname IN ('tenant_id', 'plan_id', 'owner_scope') AND NOT attisdropped""",
        t)}
    try:
        await conn.execute("SAVEPOINT cnt")
        tenant_col = "tenant_id" if "tenant_id" in out["columns"] else None
        sql = (f"SELECT count(*) AS n, count(DISTINCT {tenant_col}) AS tenants FROM {t}" if tenant_col
               else f"SELECT count(*) AS n, NULL::bigint AS tenants FROM {t}")
        r = await conn.fetchrow(sql)
        out.update(rows=r["n"], tenants=r["tenants"])
        await conn.execute("RELEASE SAVEPOINT cnt")
    except Exception as e:  # noqa: BLE001 — recorded, not fatal
        await conn.execute("ROLLBACK TO SAVEPOINT cnt")
        out["count_error"] = repr(e)[:200]
    out["aa_app_user_privs"] = sorted(a["priv"] + (f"({a['col']})" if a["col"] else "")
                                      for a in out["acl"] if a["grantee"] == "aa_app_user")
    out["grantees"] = sorted({a["grantee"] for a in out["acl"]})
    return out


async def _platform(conn, t):
    r = await conn.fetchrow("SELECT c.relrowsecurity FROM pg_class c WHERE c.oid = $1::regclass", t)
    cols = [x["attname"] for x in await conn.fetch(
        "SELECT attname FROM pg_attribute WHERE attrelid = $1::regclass AND attname IN ('tenant_id', 'owner_scope') "
        "AND NOT attisdropped", t)]
    privs = [x["p"] for x in await conn.fetch("""
        SELECT a.privilege_type AS p FROM pg_class c, aclexplode(c.relacl) a
         WHERE c.oid = $1::regclass AND a.grantee = 'aa_app_user'::regrole
        UNION ALL
        SELECT a.privilege_type || '(' || att.attname || ')' FROM pg_attribute att, aclexplode(att.attacl) a
         WHERE att.attrelid = $1::regclass AND att.attacl IS NOT NULL AND a.grantee = 'aa_app_user'::regrole""", t)]
    return {"rls": r["relrowsecurity"], "tenant_columns": cols, "aa_app_user_privs": sorted(privs)}


async def _explain(conn, name, sql, *args):
    try:
        await conn.execute("SAVEPOINT ex")
        plan = await conn.fetchval(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}", *args)
        await conn.execute("RELEASE SAVEPOINT ex")
        p = json.loads(plan)[0] if isinstance(plan, str) else plan[0]
        return {"name": name, "execution_ms": p.get("Execution Time"), "planning_ms": p.get("Planning Time"),
                "top": p["Plan"].get("Node Type"), "rows": p["Plan"].get("Actual Rows")}
    except Exception as e:  # noqa: BLE001 — recorded, not fatal
        await conn.execute("ROLLBACK TO SAVEPOINT ex")
        return {"name": name, "skipped": repr(e)[:200]}


async def collect(mode):
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        return {"fatal": "no DSN in the container environment"}
    conn = await asyncpg.connect(dsn, ssl="require")
    doc = {"mode": mode, "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    try:
        tr = conn.transaction(readonly=True)
        await tr.start()
        try:
            doc["login"] = await conn.fetchval("SELECT current_user")
            doc["last_cis_migration"] = await conn.fetchval(
                "SELECT max(version) FROM shared.schema_versions WHERE version ~ '^[0-9]+$'")
            doc["registered"] = {v: bool(await conn.fetchval(
                "SELECT 1 FROM shared.schema_versions WHERE version = $1", v)) for v in ("254", "265", "266")}
            doc["roles"] = {r["rolname"]: dict(r) for r in await conn.fetch("""
                SELECT rolname, rolsuper, rolbypassrls, rolcanlogin, rolconnlimit,
                       ARRAY(SELECT m.member::regrole::text FROM pg_auth_members m WHERE m.roleid = r.oid) AS members,
                       ARRAY(SELECT m.roleid::regrole::text FROM pg_auth_members m WHERE m.member = r.oid) AS member_of
                  FROM pg_roles r WHERE rolname IN ('aa_app_user', 'cis_app', 'cis_owner', 'catalog_owner')""")}
            doc["tables"] = {t: await _table(conn, t) for t in T265 + (ATOMS,)}
            doc["platform"] = {t: await _platform(conn, t) for t in PLATFORM}
            doc["acp_contract_usage"] = await conn.fetchval(
                "SELECT has_schema_privilege('aa_app_user', 'acp_contract', 'USAGE')")
            doc["pages_non_canonical"] = await conn.fetchval(
                "SELECT count(*) FROM acp_deliver.tenant_tour_pages WHERE tenant_id !~ $1", CANONICAL)
            doc["atoms_non_canonical_scope"] = await conn.fetchval(
                "SELECT count(*) FROM acp_contract.tour_atoms WHERE owner_scope <> 'platform' AND owner_scope !~ $1",
                CANONICAL)
            doc["d9"] = await conn.fetchval("""
                SELECT count(*) FROM acp_contract.tour_atoms ta
                 WHERE ta.owner_scope <> 'platform' AND NOT ta.deleted AND NOT ta.is_empty_marker
                   AND EXISTS (SELECT 1 FROM gold_aa_internal.published_tours pt WHERE pt.tour_id = ta.tour_id
                                 AND pt.master_status = 'active' AND pt.deleted_at IS NULL)""")
            doc["acp_contract_view_privs"] = [r["v"] for r in await conn.fetch("""
                SELECT c.oid::regclass::text AS v FROM pg_class c
                 WHERE c.relnamespace = 'acp_contract'::regnamespace AND c.relkind IN ('v', 'm')
                   AND (has_table_privilege('aa_app_user', c.oid, 'SELECT, INSERT, UPDATE, DELETE')
                        OR has_any_column_privilege('aa_app_user', c.oid, 'SELECT'))""")]
            doc["invariant_v1_violations"] = [dict(x) for x in await conn.fetch(INVARIANT_V1)]
            doc["invariant_v2_violations"] = [dict(x) for x in await conn.fetch(INVARIANT_V2)]
            doc["job_busy"] = {"shared.job": await conn.fetchval(
                "SELECT count(*) FROM shared.job WHERE status IN ('queued', 'running')")}
            try:
                await conn.execute("SAVEPOINT bkjob")
                doc["job_busy"]["booking.job"] = await conn.fetchval(
                    "SELECT count(*) FROM booking.job WHERE status IN ('queued', 'running')")
                await conn.execute("RELEASE SAVEPOINT bkjob")
            except Exception as e:  # noqa: BLE001 — recorded, not fatal
                await conn.execute("ROLLBACK TO SAVEPOINT bkjob")
                doc["job_busy"]["booking.job"] = None
                doc["booking_job_read_skipped"] = repr(e)[:200]
            if mode.endswith("266"):
                segs = [r["segment_id"] for r in await conn.fetch(
                    "SELECT segment_id FROM acp_contract.atom_segment_member WHERE NOT is_alias "
                    "GROUP BY segment_id ORDER BY count(*) DESC LIMIT 20")]
                tours = [r["tour_id"] for r in await conn.fetch(
                    "SELECT tour_id FROM gold_aa_internal.published_tours WHERE master_status = 'active' "
                    "AND deleted_at IS NULL ORDER BY tour_id LIMIT 20")]
                sources = [str(t) for t in tours]
                doc["explain"] = [
                    await _explain(conn, "pick members (base table)", MEMBERS_SQL, segs, "platform"),
                    await _explain(conn, "worker atoms by tour", ATOMS_BY_TOUR_SQL, tours),
                    await _explain(conn, "TripPlanner catalog.v_tour_place = ANY($1)", CATALOG_SQL, sources),
                ]
        finally:
            await tr.rollback()
    finally:
        await conn.close()
    doc.update(_verdict(doc, mode))
    return doc


def _jobs(doc, bad, unchecked):
    for table, n in doc["job_busy"].items():
        if n:
            bad.append(f"{table} has {n} queued / running job(s): DB Migrate apply will refuse")
    if doc["job_busy"].get("booking.job") is None:
        unchecked.append("booking.job not readable by the runtime login (skipped): DB Migrate apply still refuses "
                         "while it has queued / running jobs; check it there")


def _verdict(doc, mode):
    bad, unchecked = [], []
    app = doc["roles"].get("aa_app_user", {})
    if app.get("rolsuper") or app.get("rolbypassrls") or app.get("members") or app.get("member_of"):
        bad.append("aa_app_user is privileged, has members or is a member of a role")
    if doc["acp_contract_view_privs"]:
        bad.append(f"aa_app_user holds privileges on acp_contract views {doc['acp_contract_view_privs']}")
    for t, x in doc["platform"].items():
        if x["rls"] or x["tenant_columns"]:
            bad.append(f"platform relation {t}: rls={x['rls']} tenant columns {x['tenant_columns']}")
    if mode == "pre-265":
        if doc["invariant_v1_violations"]:
            bad.append(f"{len(doc['invariant_v1_violations'])} invariant v1 violation(s) before 265")
        if doc["registered"]["265"]:
            bad.append("265 is already registered")
        if doc["pages_non_canonical"]:
            bad.append(f"{doc['pages_non_canonical']} non-canonical tenant_tour_pages tenant ids (265 guard 1)")
        for t in T265:
            x = doc["tables"][t]
            if x["rls"] or x["force"] or x["policies"]:
                bad.append(f"{t}: already has RLS / FORCE / policies {[p['name'] for p in x['policies']]}")
            if x["aa_app_user_privs"]:
                bad.append(f"{t}: aa_app_user already holds {x['aa_app_user_privs']}")
            others = sorted(set(x["grantees"]) - {x["owner"], "aa_app_user", "cis_app"})
            if others:
                bad.append(f"{t}: other grantees {others} (265 guard 1 refuses login roles / PUBLIC)")
        _jobs(doc, bad, unchecked)
        return {"gate_265_ready": not bad, "reasons": bad, "unchecked": unchecked}
    if mode == "post-265":
        if not doc["registered"]["265"]:
            bad.append("265 is not registered")
        v2 = [v for v in doc["invariant_v2_violations"]
              if (v.get("rel"), v.get("column_name")) not in PLATFORM_READ_COLUMNS]
        if v2:
            bad.append(f"{len(v2)} invariant v2 violation(s)")
        if not doc["acp_contract_usage"]:
            bad.append("aa_app_user has no USAGE on acp_contract")
        for t, x in doc["platform"].items():
            if x["aa_app_user_privs"] != EXPECTED_PRIVS.get(t, ["SELECT"]):
                bad.append(f"platform relation {t}: aa_app_user privileges {x['aa_app_user_privs']}")
        for t in T265:
            x = doc["tables"][t]
            if not x["rls"] or x["force"]:
                bad.append(f"{t}: RLS {x['rls']} FORCE {x['force']} (expected on, not forced)")
            if sorted(p["name"] for p in x["policies"]) != POLICIES_265[t]:
                bad.append(f"{t}: policies {[p['name'] for p in x['policies']]}")
            if set(x["aa_app_user_privs"]) != PRIVS_265[t]:
                bad.append(f"{t}: aa_app_user privileges {x['aa_app_user_privs']}")
            if "rows" not in x:
                bad.append(f"{t}: cis_app could not count it ({x.get('count_error')}): parity policy missing?")
        return {"post_265_ok": not bad, "reasons": bad}
    x = doc["tables"][ATOMS]
    if mode == "pre-266":
        for v in ("254", "265"):
            if not doc["registered"][v]:
                bad.append(f"{v} is not registered (266 needs it first)")
        if doc["registered"]["266"]:
            bad.append("266 is already registered")
        if "tripplanner" in x["grantees"]:
            bad.append("tripplanner still holds privileges on tour_atoms: apply CIS 254 first")
        others = sorted(set(x["grantees"]) - {x["owner"], "cis_app", "catalog_owner", "aa_app_user", "tripplanner"})
        if others:
            bad.append(f"tour_atoms: other grantees {others} (266 guard 1)")
        if x["rls"] or x["force"] or x["policies"]:
            bad.append(f"tour_atoms already has RLS / FORCE / policies {[p['name'] for p in x['policies']]}")
        if doc["d9"]:
            bad.append(f"D9 = {doc['d9']} (live tenant atoms on live master tours): Q4, 266 refuses")
        if doc["atoms_non_canonical_scope"]:
            bad.append(f"{doc['atoms_non_canonical_scope']} non-canonical owner_scope values (266 guard 1)")
        v2 = [v for v in doc["invariant_v2_violations"]
              if (v.get("rel"), v.get("column_name")) not in PLATFORM_READ_COLUMNS]
        if v2:
            bad.append(f"{len(v2)} invariant v2 violation(s)")
        bad_views = [v for v in x["dependent_views"] if v["owner"] not in (x["owner"], "catalog_owner")]
        if bad_views:
            bad.append(f"tour_atoms dependent views owned by a filtered role: {bad_views}")
        _jobs(doc, bad, unchecked)
        return {"gate_266_ready": not bad, "reasons": bad, "unchecked": unchecked}
    if not doc["registered"]["266"]:
        bad.append("266 is not registered")
    if not x["rls"] or x["force"]:
        bad.append(f"tour_atoms: RLS {x['rls']} FORCE {x['force']} (expected on, not forced)")
    if sorted(p["name"] for p in x["policies"]) != POLICIES_266:
        bad.append(f"tour_atoms: policies {[p['name'] for p in x['policies']]}")
    if x["aa_app_user_privs"] != ["SELECT"]:
        bad.append(f"tour_atoms: aa_app_user privileges {x['aa_app_user_privs']}")
    if "rows" not in x:
        bad.append(f"tour_atoms: cis_app could not count it ({x.get('count_error')}): parity policy missing?")
    v2 = [v for v in doc["invariant_v2_violations"]
          if (v.get("rel"), v.get("column_name")) not in PLATFORM_READ_COLUMNS]
    if v2:
        bad.append(f"{len(v2)} invariant v2 violation(s)")
    return {"post_266_ok": not bad, "reasons": bad,
            "compare_with_pre": "tables.acp_contract.tour_atoms.rows and explain[] against the pre-266 document"}


MODES = ("pre-265", "post-265", "pre-266", "post-266")


def main():
    mode = (sys.argv[1:] or ["pre-265"])[0]
    if mode not in MODES:
        raise SystemExit(f"usage: aa859_w4_preflight.py {'|'.join(MODES)}")
    key = f"scripts/out/s247_aa859_w4_{mode}.json"
    try:
        doc = asyncio.run(collect(mode))
    except Exception as e:  # noqa: BLE001 — recorded in the JSON, never printed
        doc = {"mode": mode, "fatal": repr(e)[:500]}
    body = json.dumps(doc, default=str, indent=1).encode()
    boto3.client("s3", region_name="us-west-1").put_object(Bucket=BUCKET, Key=key, Body=body)
    print("OK", len(body))


if __name__ == "__main__":
    main()
