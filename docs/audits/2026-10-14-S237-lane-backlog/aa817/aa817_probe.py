"""AA-817 step 1 — READ-ONLY role x table RLS probe for the shared Dev RDS (S237).

Run inside the CIS api container (python3 + asyncpg + boto3), e.g. with .tmp-session/s237/exec.sh.
Prints ONE JSON line. Never prints a password or a DSN, only user names.

Safety: every DB statement runs inside a READ ONLY transaction that is ROLLED BACK at the end.
SET LOCAL ROLE / set_config(..., true) only change transaction-local state. Nothing is granted,
created or altered. If `SET ROLE aa_app_user` is not allowed for the runner, the probe opens a
second read-only connection with the existing secret aa-cis/dev/rds-app-user (the same DSN the
API's tenant pool already uses) instead of granting anything.

What it answers (AA-817 scope 1):
  * who the runtime is: current_user/session_user, attributes, the full pg_auth_members chain with
    each inherited role's rolsuper/rolbypassrls (incl. rds_superuser, catalog_owner);
  * per table/view in the CIS schemas: owner, relrowsecurity, relforcerowsecurity, tenant_id type,
    privileges of aa_app_user / tripplanner / booking / catalog_owner, row_security_active();
  * every policy (pg_policies) in those schemas;
  * the empirical matrix: count(*) of every RLS table + gold_aa_internal.tenant_tour_versions as the
    runner, as aa_app_user and (when SET ROLE is allowed) tripplanner / booking / catalog_owner, under
    app.tenant_id = unset | '' | random foreign uuid | AA master | the table's busiest tenant.

How to read the matrix (mechanism of the S236 observation "aa_cis_admin reads every row of
published_tours under a foreign tenant"):
  * runner sees rows under `foreign` on published_tours/raw_tours but 0 on the OTHER FORCE-RLS tables
    (generated_content, seo_context, quality_scores, content_exports, ...) -> the runner still
    inherits catalog_owner (policy catalog_owner_aa_master_read, migration 225), not a bypass;
  * runner sees rows under `foreign` on every FORCE-RLS table -> a real bypass (an inherited role
    with BYPASSRLS / rds_superuser semantics) — see `membership_chain`;
  * runner sees rows under `foreign` only on ENABLE-without-FORCE tables -> the normal owner
    exemption (expected for 115/116/145).
"""
import asyncio
import json
import os
import uuid
from urllib.parse import urlparse

import asyncpg
import boto3

REGION = os.environ.get("AWS_REGION", "us-west-1")
MAIN_SECRET = "aa-cis/dev/rds"
APP_USER_SECRET = "aa-cis/dev/rds-app-user"
SCHEMAS = ["gold_aa_internal", "silver_aa_internal", "acp_shared", "acp_contract", "shared", "catalog", "geo"]
PROBE_ROLES = ["aa_app_user", "tripplanner", "booking", "catalog_owner"]
MASTER = "00000000-0000-0000-0000-000000000001"
FOREIGN = str(uuid.uuid4())
FOCUS_EXTRA = ["gold_aa_internal.tenant_tour_versions"]  # counted even without RLS (229 target)
STMT_TIMEOUT = "15s"
OUT_BUCKET = "aa-cis-bronze-005097885195"
OUT_KEY = "scripts/out/s237_aa817_probe.json"


class _Undo(Exception):
    """Raised to roll a savepoint back (undo SET LOCAL ROLE / set_config)."""


def _secret(client, sid):
    return client.get_secret_value(SecretId=sid)["SecretString"].strip()


def _parse(dsn):
    u = urlparse(dsn)
    return dict(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password,
                database=(u.path or "/").lstrip("/") or None)


async def _connect(dsn):
    p = _parse(dsn)
    return await asyncpg.connect(host=p["host"], port=p["port"], user=p["user"], password=p["password"],
                                 database=p["database"], ssl="require", timeout=20)


def _err(e):
    return f"{type(e).__name__}: {str(e)[:160]}"


async def _identity(c):
    r = await c.fetchrow("""
        SELECT current_user AS cu, session_user AS su, current_database() AS db,
               current_setting('server_version') AS ver, current_setting('row_security') AS row_security,
               current_setting('is_superuser') AS is_superuser,
               r.rolsuper, r.rolbypassrls, r.rolcreaterole, r.rolcreatedb, r.rolinherit, r.rolcanlogin
          FROM pg_roles r WHERE r.rolname = current_user""")
    return dict(r)


async def _chain(c, role):
    """Every role `role` is a member of (recursive), with how it is reached and its attributes."""
    rows = await c.fetch("""
        WITH RECURSIVE ch(roleid, depth, path) AS (
            SELECT m.roleid, 1, ARRAY[$1::text, m.roleid::regrole::text]
              FROM pg_auth_members m WHERE m.member = $1::text::regrole
            UNION ALL
            SELECT m.roleid, ch.depth + 1, ch.path || m.roleid::regrole::text
              FROM pg_auth_members m JOIN ch ON m.member = ch.roleid
             WHERE ch.depth < 10 AND NOT (m.roleid::regrole::text = ANY(ch.path))
        )
        SELECT ch.roleid::regrole::text AS role, ch.depth, array_to_string(ch.path, ' > ') AS path,
               r.rolsuper, r.rolbypassrls, r.rolinherit, r.rolcanlogin,
               pg_has_role($1::text::name, ch.roleid, 'USAGE') AS inherits_privs,
               pg_has_role($1::text::name, ch.roleid, 'MEMBER') AS can_set_role
          FROM ch JOIN pg_roles r ON r.oid = ch.roleid
         ORDER BY ch.depth, 1""", role)
    return [dict(x) for x in rows]


async def _roles(c):
    rows = await c.fetch("""
        SELECT r.rolname, r.rolsuper, r.rolbypassrls, r.rolcreaterole, r.rolinherit, r.rolcanlogin,
               ARRAY(SELECT m.member::regrole::text FROM pg_auth_members m WHERE m.roleid = r.oid ORDER BY 1)
                   AS members,
               ARRAY(SELECT m.roleid::regrole::text FROM pg_auth_members m WHERE m.member = r.oid ORDER BY 1)
                   AS member_of
          FROM pg_roles r
         WHERE r.rolname = ANY($1::text[]) OR r.rolname = current_user OR r.rolname LIKE 'rds%'
            OR r.rolbypassrls OR r.rolsuper
         ORDER BY 1""", PROBE_ROLES + ["aa_cis_admin"])
    return [dict(x) for x in rows]


async def _tables(c, existing_roles):
    rows = await c.fetch("""
        SELECT n.nspname AS s, c.relname AS t, c.relkind::text AS k,
               pg_get_userbyid(c.relowner) AS owner, c.relrowsecurity AS rls, c.relforcerowsecurity AS force,
               (SELECT format_type(a.atttypid, a.atttypmod) FROM pg_attribute a
                 WHERE a.attrelid = c.oid AND a.attname = 'tenant_id' AND NOT a.attisdropped) AS tenant_col,
               c.reltuples::bigint AS est_rows,
               CASE WHEN c.relkind IN ('r','p') THEN row_security_active(c.oid) END AS rls_active_for_me,
               c.reloptions AS opts
          FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
         WHERE n.nspname = ANY($1::text[]) AND c.relkind IN ('r','p','v','m')
         ORDER BY 1, 2""", SCHEMAS)
    out = []
    for r in rows:
        d = dict(r)
        fq = f'{d["s"]}.{d["t"]}'
        privs = {}
        for role in existing_roles:
            letters = ""
            for p, ch in (("SELECT", "S"), ("INSERT", "I"), ("UPDATE", "U"), ("DELETE", "D")):
                if await c.fetchval("SELECT has_table_privilege($1, $2::regclass, $3)", role, fq, p):
                    letters += ch
            if letters:
                privs[role] = letters
        d["privs"] = privs
        if not d["opts"]:
            d.pop("opts")
        out.append(d)
    return out


async def _schemas(c, existing_roles):
    out = {}
    for s in SCHEMAS:
        row = await c.fetchrow("SELECT pg_get_userbyid(nspowner) AS owner FROM pg_namespace WHERE nspname = $1", s)
        if row is None:
            out[s] = None
            continue
        out[s] = {"owner": row["owner"], "usage": {
            role: await c.fetchval("SELECT has_schema_privilege($1, $2, 'USAGE')", role, s)
            for role in existing_roles}}
    return out


async def _policies(c):
    rows = await c.fetch("""
        SELECT schemaname AS s, tablename AS t, policyname AS p, permissive, roles::text[] AS roles, cmd,
               qual, with_check
          FROM pg_policies WHERE schemaname = ANY($1::text[]) ORDER BY 1, 2, 3""", SCHEMAS)
    return [dict(x) for x in rows]


async def _default_acl(c):
    rows = await c.fetch("""
        SELECT pg_get_userbyid(d.defaclrole) AS for_role, n.nspname AS s, d.defaclobjtype::text AS objtype,
               d.defaclacl::text AS acl
          FROM pg_default_acl d LEFT JOIN pg_namespace n ON n.oid = d.defaclnamespace
         WHERE n.nspname IS NULL OR n.nspname = ANY($1::text[]) ORDER BY 2, 1""", SCHEMAS)
    return [dict(x) for x in rows]


async def _set_guc(c, mode, own):
    if mode == "unset":
        return await c.fetchval("SELECT current_setting('app.tenant_id', true)")
    val = {"empty": "", "foreign": FOREIGN, "master": MASTER, "own": own}[mode]
    await c.execute("SELECT set_config('app.tenant_id', $1, true)", val)
    return val


async def _count(c, fq, mode, own):
    """One matrix cell: "<rows>/<distinct tenant_id>" (or "<rows>" when the table has no tenant_id),
    or "ERR <exception>", under one GUC mode, inside its own savepoint (rolled back). For mode
    `unset` the cell is prefixed with the GUC value actually seen (a pooled connection reports ''
    once any set_config(..., true) ran on it, so `unset` and `empty` usually coincide)."""
    cell = None
    try:
        async with c.transaction():
            seen = await _set_guc(c, mode, own)
            has_tenant = await c.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = $1::regclass "
                "AND attname = 'tenant_id' AND NOT attisdropped)", fq)
            sql = f"SELECT count(*) AS n{', count(DISTINCT tenant_id) AS nt' if has_tenant else ''} FROM {fq}"
            row = await c.fetchrow(sql)
            cell = f'{row["n"]}/{row["nt"]}' if has_tenant else str(row["n"])
            if mode == "unset":
                cell = f"guc={seen!r} {cell}"
            raise _Undo()
    except _Undo:
        pass
    except Exception as e:  # noqa: BLE001 — record, keep probing
        cell = "ERR " + _err(e)
    return cell


async def _matrix_as(c, targets, owns):
    out = {}
    for fq in targets:
        out[fq] = {m: await _count(c, fq, m, owns.get(fq, MASTER))
                   for m in ("unset", "empty", "foreign", "master", "own")}
    return out


async def _busiest_tenant(c, fq):
    """The tenant with most rows, as the runner with app.tenant_id unset (owner view)."""
    try:
        async with c.transaction():
            v = await c.fetchval(f"SELECT tenant_id::text FROM {fq} GROUP BY 1 ORDER BY count(*) DESC LIMIT 1")
            raise _Undo(v)
    except _Undo as u:
        return u.args[0] if u.args and u.args[0] else None
    except Exception:  # noqa: BLE001
        return None


async def _as_role(c, role, targets, owns):
    """SET LOCAL ROLE inside a savepoint, count, roll the savepoint back (resets the role)."""
    res = {}
    try:
        async with c.transaction():
            await c.execute(f'SET LOCAL ROLE "{role}"')
            res["current_user"] = await c.fetchval("SELECT current_user")
            res["chain_effective"] = await c.fetchval("SELECT current_setting('role')")
            res["matrix"] = await _matrix_as(c, targets, owns)
            raise _Undo()
    except _Undo:
        pass
    except Exception as e:  # noqa: BLE001
        res["set_role_error"] = _err(e)
    return res


async def main():
    out = {}
    try:
        await _main(out)
    except Exception as e:  # noqa: BLE001 — always emit one JSON line, with what was collected
        out["fatal"] = _err(e)
    line = json.dumps(out, default=str, separators=(",", ":"))
    try:  # full copy inside the container too, in case the exec session truncates a long line
        with open("/tmp/aa817_probe_out.json", "w") as f:
            f.write(line)
    except OSError:
        pass
    try:  # and in S3 (same prefix as s209_schema_dump), readable without a second exec session
        boto3.client("s3", region_name=REGION).put_object(
            Bucket=OUT_BUCKET, Key=OUT_KEY, Body=line.encode(), ContentType="application/json")
    except Exception:  # noqa: BLE001 — the stdout line is still the primary output
        pass
    print(line)


async def _main(out):
    out.update({"probe": "aa817_role_matrix", "foreign_uuid": FOREIGN, "master_uuid": MASTER})
    sm = boto3.client("secretsmanager", region_name=REGION)
    try:
        main_dsn = _secret(sm, MAIN_SECRET)
    except Exception as e:  # noqa: BLE001
        main_dsn = os.environ.get("DATABASE_URL", "")
        out["main_secret_error"] = _err(e)
    out["main_secret_user"] = _parse(main_dsn)["user"]
    env_url = os.environ.get("DATABASE_URL")
    out["api_env_database_url_user"] = _parse(env_url)["user"] if env_url else None
    out["api_env_database_url_same_host"] = (
        _parse(env_url)["host"] == _parse(main_dsn)["host"] if env_url else None)

    c = await _connect(main_dsn)
    tr = c.transaction(readonly=True)
    await tr.start()
    try:
        await c.execute(f"SET LOCAL statement_timeout = '{STMT_TIMEOUT}'")
        await c.execute("SET LOCAL lock_timeout = '3s'")
        ident = await _identity(c)
        out["identity"] = ident
        me = ident["cu"]
        out["membership_chain"] = await _chain(c, me)
        out["roles"] = await _roles(c)
        existing = [r for r in PROBE_ROLES if await c.fetchval("SELECT 1 FROM pg_roles WHERE rolname = $1", r)]
        out["probe_roles_existing"] = existing
        out["aa_app_user_chain"] = await _chain(c, "aa_app_user") if "aa_app_user" in existing else None
        out["schemas"] = await _schemas(c, existing)
        tables = await _tables(c, existing)
        out["tables"] = tables
        out["policies"] = await _policies(c)
        out["default_acl"] = await _default_acl(c)

        targets = [f'{t["s"]}.{t["t"]}' for t in tables if t["k"] in ("r", "p") and t["rls"]]
        for fq in FOCUS_EXTRA:
            if fq not in targets and any(f'{t["s"]}.{t["t"]}' == fq for t in tables):
                targets.append(fq)
        out["matrix_targets"] = targets
        owns = {fq: (await _busiest_tenant(c, fq)) or MASTER for fq in targets}
        out["own_tenant_per_table"] = owns

        out["matrix_runner"] = await _matrix_as(c, targets, owns)
        out["as_role"] = {role: await _as_role(c, role, targets, owns) for role in existing}
    finally:
        await tr.rollback()

    # aa_app_user via its own login when SET ROLE was not allowed (the tenant pool's real path).
    if "aa_app_user" in out.get("probe_roles_existing", []) and \
            "set_role_error" in out["as_role"].get("aa_app_user", {}):
        try:
            app_dsn = _secret(sm, APP_USER_SECRET)
            out["app_user_secret_user"] = _parse(app_dsn)["user"]
            a = await _connect(app_dsn)
            atr = a.transaction(readonly=True)
            await atr.start()
            try:
                await a.execute(f"SET LOCAL statement_timeout = '{STMT_TIMEOUT}'")
                await a.execute("SET LOCAL lock_timeout = '3s'")
                out["app_user_login"] = {
                    "identity": await _identity(a),
                    "matrix": await _matrix_as(a, out["matrix_targets"], out["own_tenant_per_table"]),
                }
            finally:
                await atr.rollback()
                await a.close()
        except Exception as e:  # noqa: BLE001
            out["app_user_login_error"] = _err(e)
    await c.close()


asyncio.run(main())
