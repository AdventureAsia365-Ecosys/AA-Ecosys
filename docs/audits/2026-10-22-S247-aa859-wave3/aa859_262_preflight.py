"""AA-859 S247 — READ-ONLY preflight (and postflight) for CIS migration 262 and the D5b / wave-3 flips.

Run inside the CIS api container with the S3-mediated ECS exec pattern (python3 + asyncpg + boto3):

    python3 aa859_262_preflight.py pre     # before DB Migrate apply of 262
    python3 aa859_262_preflight.py post    # after the apply

Connects with the container's own DSN over SSL (ssl="require"; the CIS runtime role cis_app since X1 S18; the task
role may not read the master secret). One READ ONLY transaction, rolled back. Nothing is granted, created,
altered or written. Writes ONE JSON document to
s3://aa-cis-bronze-005097885195/scripts/out/s247_aa859_262_<mode>.json and prints only `OK <bytes>` (ECS exec
cuts output silently: read the S3 copy). Never prints or stores a DSN or a password.

What it reads, per table (shared.tenant_brand_rules, shared.tenant_seo_config): RLS / FORCE, owner, every ACL item
(aclexplode on relacl and attacl, grantor included), policies with their expressions, dependent views and their
owners, the tenant_id column, row count and distinct tenants. Plus: aa_app_user / cis_app role attributes and
memberships, the AA-859 invariant (241 guard 4 text: rows = violations), the last CIS migration, shared.job and
booking.job queued / running (DB Migrate refuses to apply otherwise; booking.job is recorded as skipped when the
runtime login cannot read it), and the D5b pre-flip divergence counts (master published
tours whose raw_tours / seo_context row is not the AA master tenant's; must be 0, see AA-859-d5b-wave3.md).

Verdict `gate_262_ready` (pre) / `post_262_ok` (post) with the list of reasons when false.
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

import asyncpg
import boto3

BUCKET = "aa-cis-bronze-005097885195"
TABLES = ("shared.tenant_brand_rules", "shared.tenant_seo_config")
MASTER = "00000000-0000-0000-0000-000000000001"
NO_PRIVILEGE_WITHOUT_RLS_SQL = """\
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
BRAND_PRIVS = {"SELECT", "UPDATE(is_active)"} | {
    f"INSERT({c})" for c in ("tenant_id", "system_prompt", "style_guide", "forbidden_words", "version", "is_active",
                             "updated_at", "brand_name", "brand_type", "core_idea", "customer_segment",
                             "customer_mindset", "voice_examples", "good_examples", "target_markets", "default_cta")}
SEO_PRIVS = {"SELECT", "INSERT(tenant_id)", "INSERT(target_market)", "UPDATE(target_market)", "UPDATE(updated_at)"}


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
    col = await conn.fetchrow("""SELECT format_type(atttypid, atttypmod) AS type, attnotnull FROM pg_attribute
                                  WHERE attrelid = $1::regclass AND attname = 'tenant_id' AND NOT attisdropped""", t)
    out["tenant_id"] = dict(col) if col else None
    try:
        await conn.execute("SAVEPOINT cnt")
        r = await conn.fetchrow(f"SELECT count(*) AS n, count(DISTINCT tenant_id) AS tenants FROM {t}")
        out.update(rows=r["n"], tenants=r["tenants"])
        await conn.execute("RELEASE SAVEPOINT cnt")
    except Exception as e:  # noqa: BLE001 — recorded, not fatal
        await conn.execute("ROLLBACK TO SAVEPOINT cnt")
        out["count_error"] = repr(e)[:200]
    out["aa_app_user_privs"] = sorted(a["priv"] + (f"({a['col']})" if a["col"] else "")
                                      for a in out["acl"] if a["grantee"] == "aa_app_user")
    return out


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
            doc["v262_registered"] = bool(await conn.fetchval(
                "SELECT 1 FROM shared.schema_versions WHERE version = '262'"))
            doc["roles"] = {r["rolname"]: dict(r) for r in await conn.fetch("""
                SELECT rolname, rolsuper, rolbypassrls, rolcanlogin, rolconnlimit,
                       ARRAY(SELECT m.member::regrole::text FROM pg_auth_members m WHERE m.roleid = r.oid) AS members,
                       ARRAY(SELECT m.roleid::regrole::text FROM pg_auth_members m WHERE m.member = r.oid) AS member_of
                  FROM pg_roles r WHERE rolname IN ('aa_app_user', 'cis_app', 'cis_owner')""")}
            doc["tables"] = {t: await _table(conn, t) for t in TABLES}
            doc["invariant_violations"] = [dict(x) for x in await conn.fetch(NO_PRIVILEGE_WITHOUT_RLS_SQL)]
            # DB Migrate apply waits on EVERY job table (DM-11.4): shared.job and booking.job. cis_app may not
            # read booking.*; then the read is recorded as skipped (not counted as idle) and DB Migrate's own
            # guard stays the authority for booking.job.
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
            doc["d5b_divergence"] = {
                "raw_tours": await conn.fetchval(
                    "SELECT count(*) FROM gold_aa_internal.published_tours pt JOIN silver_aa_internal.raw_tours rt "
                    "ON rt.tour_id = pt.tour_id WHERE pt.tenant_id = $1::uuid "
                    "AND rt.tenant_id IS DISTINCT FROM pt.tenant_id", MASTER),
                "seo_context": await conn.fetchval(
                    "SELECT count(*) FROM gold_aa_internal.published_tours pt JOIN silver_aa_internal.seo_context sc "
                    "ON sc.tour_id = pt.tour_id WHERE pt.tenant_id = $1::uuid "
                    "AND sc.tenant_id IS DISTINCT FROM pt.tenant_id", MASTER),
            }
        finally:
            await tr.rollback()
    finally:
        await conn.close()
    doc.update(_verdict(doc, mode))
    return doc


def _verdict(doc, mode):
    bad = []
    app = doc["roles"].get("aa_app_user", {})
    if app.get("rolsuper") or app.get("rolbypassrls") or app.get("members") or app.get("member_of"):
        bad.append("aa_app_user is privileged, has members or is a member of a role")
    if doc["invariant_violations"]:
        bad.append(f"{len(doc['invariant_violations'])} aa_app_user privilege(s) on relations without RLS")
    if any(doc["d5b_divergence"].values()):
        bad.append(f"D5b divergence not 0: {doc['d5b_divergence']} (do not keep t2_version_detail_reads ON)")
    for t, x in doc["tables"].items():
        rel = t.split(".")[1]
        others = sorted({a["grantee"] for a in x["acl"]} - {x["owner"], "aa_app_user", "cis_app"})
        if others:
            bad.append(f"{t}: other grantees {others} (guard 1 refuses login roles / PUBLIC)")
        if x["dependent_views"]:
            bad.append(f"{t}: dependent views {x['dependent_views']} (check their owners)")
        if not x["tenant_id"] or x["tenant_id"]["type"] != "uuid" or not x["tenant_id"]["attnotnull"]:
            bad.append(f"{t}: tenant_id is not uuid NOT NULL")
        if mode == "pre":
            if x["rls"] or x["force"] or x["policies"]:
                bad.append(f"{t}: already has RLS / FORCE / policies {[p['name'] for p in x['policies']]}")
            if x["aa_app_user_privs"]:
                bad.append(f"{t}: aa_app_user already holds {x['aa_app_user_privs']}")
        else:
            if not x["rls"] or x["force"]:
                bad.append(f"{t}: RLS {x['rls']} FORCE {x['force']} (expected on, not forced)")
            if sorted(p["name"] for p in x["policies"]) != sorted([f"{rel}_cis_app_all", "tenant_isolation"]):
                bad.append(f"{t}: policies {[p['name'] for p in x['policies']]}")
            want = BRAND_PRIVS if rel == "tenant_brand_rules" else SEO_PRIVS
            if set(x["aa_app_user_privs"]) != want:
                bad.append(f"{t}: aa_app_user privileges {x['aa_app_user_privs']}")
            if "rows" not in x:
                bad.append(f"{t}: the runtime login could not count it ({x.get('count_error')})")
    if mode == "pre":
        if doc["v262_registered"]:
            bad.append("262 is already registered")
        for table, n in doc["job_busy"].items():
            if n:
                bad.append(f"{table} has {n} queued / running job(s): DB Migrate apply will refuse")
        unchecked = []
        if doc["job_busy"].get("booking.job") is None:
            unchecked.append("booking.job not readable by the runtime login (skipped): DB Migrate apply still "
                             "refuses while it has queued / running jobs; check it there")
        return {"gate_262_ready": not bad, "reasons": bad, "unchecked": unchecked}
    if not doc["v262_registered"]:
        bad.append("262 is not registered")
    return {"post_262_ok": not bad, "reasons": bad}


def main():
    mode = (sys.argv[1:] or ["pre"])[0]
    if mode not in ("pre", "post"):
        raise SystemExit("usage: aa859_262_preflight.py pre|post")
    key = f"scripts/out/s247_aa859_262_{mode}.json"
    try:
        doc = asyncio.run(collect(mode))
    except Exception as e:  # noqa: BLE001 — recorded in the JSON, never printed
        doc = {"mode": mode, "fatal": repr(e)[:500]}
    body = json.dumps(doc, default=str, indent=1).encode()
    boto3.client("s3", region_name="us-west-1").put_object(Bucket=BUCKET, Key=key, Body=body)
    print("OK", len(body))


if __name__ == "__main__":
    main()
