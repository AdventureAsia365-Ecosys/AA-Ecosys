"""S239 AA-817 — read-only pre-237 probe of shared.tenant_integrations on Dev.

Everything runs in BEGIN READ ONLY and is rolled back. Prints counts and catalog facts only: never a
secret_key value, a DSN or a password.
"""
import asyncio, json
from urllib.parse import urlparse

import asyncpg, boto3

T = "shared.tenant_integrations"
FOREIGN = "00000000-0000-0000-0000-00000000dead"


def _dsn(secret_id):
    return boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId=secret_id)["SecretString"]


async def _connect(secret_id):
    u = urlparse(_dsn(secret_id))
    return await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password,
                                 database=u.path.lstrip("/"), ssl="require")


async def main():
    o = {}
    c = await _connect("aa-cis/dev/rds")
    tr = c.transaction(readonly=True)
    await tr.start()
    try:
        o["runner"] = dict(await c.fetchrow(
            "SELECT current_user AS cu, r.rolsuper, r.rolbypassrls, r.rolcreaterole, "
            "current_setting('server_version') AS ver, "
            "pg_has_role(current_user, 'aa_app_user', 'MEMBER') AS member_of_aa_app_user "
            "FROM pg_roles r WHERE r.rolname = current_user"))
        o["table"] = dict(await c.fetchrow(
            "SELECT c.relowner::regrole::text AS owner, c.relrowsecurity AS rls, c.relforcerowsecurity AS force, "
            "pg_has_role(current_user, c.relowner, 'USAGE') AS runner_owns FROM pg_class c WHERE c.oid = $1::regclass", T))
        o["acl"] = [dict(r) for r in await c.fetch(
            "SELECT CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE a.grantee::regrole::text END AS grantee, "
            "string_agg(a.privilege_type, ',' ORDER BY a.privilege_type) AS privs "
            "FROM pg_class c, aclexplode(c.relacl) a WHERE c.oid = $1::regclass GROUP BY 1 ORDER BY 1", T)]
        o["policies"] = [dict(r) for r in await c.fetch(
            "SELECT policyname, roles::text[] AS roles, cmd FROM pg_policies "
            "WHERE schemaname = 'shared' AND tablename = 'tenant_integrations'")]
        o["aa_app_user_privs"] = {p: await c.fetchval("SELECT has_table_privilege('aa_app_user', $1, $2)", T, p)
                                  for p in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")}
        o["rows_total"] = await c.fetchval(f"SELECT count(*) FROM {T}")
        o["rows_per_tenant"] = [r["n"] for r in await c.fetch(
            f"SELECT count(*) AS n FROM {T} GROUP BY tenant_id ORDER BY 1 DESC")]
        o["rows_per_type"] = {r["integration_type"]: r["n"] for r in await c.fetch(
            f"SELECT integration_type, count(*) AS n FROM {T} GROUP BY 1")}
        o["schema_versions_cis_max"] = await c.fetchval(
            "SELECT max(version) FROM shared.schema_versions WHERE version ~ '^[0-9]+$'")
        o["has_237"] = await c.fetchval("SELECT count(*) FROM shared.schema_versions WHERE version = '237'")
        o["jobs_active"] = {r["status"]: r["n"] for r in await c.fetch(
            "SELECT status, count(*) AS n FROM shared.job WHERE status IN ('queued', 'running') GROUP BY 1")}
    finally:
        await tr.rollback()
        await c.close()

    # Before-state for the tenant role: log in as aa_app_user (the tenant pool's secret), read only.
    try:
        a = await _connect("aa-cis/dev/rds-app-user")
        tr = a.transaction(readonly=True)
        await tr.start()
        try:
            o["app_user_login"] = await a.fetchval("SELECT current_user")
            res = {}
            for label, guc in (("foreign", FOREIGN), ("empty", "")):
                await a.execute("SELECT set_config('app.tenant_id', $1, true)", guc)
                try:
                    async with a.transaction():
                        res[label] = {"rows": await a.fetchval(f"SELECT count(*) FROM {T}"),
                                      "tenants": await a.fetchval(f"SELECT count(DISTINCT tenant_id) FROM {T}")}
                except Exception as e:
                    res[label] = {"error": type(e).__name__}
            o["app_user_where_less_reads"] = res
        finally:
            await tr.rollback()
            await a.close()
    except Exception as e:
        o["app_user_login_error"] = type(e).__name__
    print(json.dumps(o, default=str))


asyncio.run(main())
