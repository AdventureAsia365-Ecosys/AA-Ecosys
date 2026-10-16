"""AA-817 probe v2 — READ-ONLY per-table RLS evidence for the tenant role (S239, Done-when set).

Run inside the CIS api container (python3 + asyncpg + boto3) with the S3-mediated ECS exec pattern.
Prints ONE JSON line (also written to /tmp/aa817_probe_v2_out.json in the container and to
s3://aa-cis-bronze-005097885195/scripts/out/s239_aa817_probe_v2_<phase>.json). Never prints a
password or a DSN, only user names.

Safety: every DB statement runs inside ONE `READ ONLY` transaction that is ROLLED BACK at the end, on
the main secret aa-cis/dev/rds (the runner, aa_cis_admin). The tenant role is reached with
`SET LOCAL ROLE aa_app_user` inside savepoints (RDS lets the runner do it, S237 probe); nothing is
granted, created, altered or written (a READ ONLY transaction refuses writes anyway). Only if SET ROLE
is refused, the probe opens ONE read-only connection with aa-cis/dev/rds-app-user (the tenant pool's
own login; it counts against aa_app_user's CONNECTION LIMIT 15 for a few seconds).

Per RLS table (the 15 of AA-817 plan §0, plus any other table with RLS found in the CIS schemas):
  * rls / force / owner, policies, aa_app_user privileges, row_security_active for the runner and for
    aa_app_user;
  * the runner (control): rows under a foreign GUC (must equal the total: main pool unaffected);
  * aa_app_user, WHERE-less `SELECT count(*)`, under app.tenant_id = unset | '' | random foreign uuid |
    AA master | own (busiest non-master tenant of the table, else master): rows, distinct tenants, master
    rows, rows of a tenant other than the GUC and master ("leak"), or the error;
  * a verdict per cell against the expectation for the migration phase found (pre-239 / post-239).
Also: aa_app_user write privileges on tables WITHOUT RLS (critique C1/C2; 239 revokes three of them).

Expected (post-239):
  229/237 tables       foreign 0 · '' 0 · own n_own (facts: + platform rows, tenant_id NULL)
  pt / rt / sc         foreign = master rows · '' = master rows · own = n_own + master · leak 0
  gc / qs / ce / wd / pr  foreign 0 · '' 0 (no 22P02) · own n_own · master = master rows
  acp_output_rules     permission denied
Pre-239: pt/rt/sc show 0 master rows under foreign / ''; sc, gc, qs, ce, wd, pr raise 22P02 under ''.
Several Dev tables are empty (publish_log, content_exports, webhook_deliveries, tenant_integrations):
there, 0 under foreign proves nothing — the CI test (test_aa817_rls_tenant_isolation.py) seeds them.
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
TENANT_ROLE = "aa_app_user"
MASTER = "00000000-0000-0000-0000-000000000001"
FOREIGN = str(uuid.uuid4())
OUT_BUCKET = "aa-cis-bronze-005097885195"
SCHEMAS = ["acp_contract", "acp_deliver", "acp_shared", "catalog", "geo", "gold_aa_internal", "shared",
           "silver_aa_internal"]
STMT_TIMEOUT = "15s"

TEMPLATE_229 = ["acp_shared.angle_gate_request", "acp_shared.content_piece", "acp_shared.publish_log",
                "acp_shared.facts", "gold_aa_internal.tenant_tour_versions", "shared.tenant_integrations"]
MASTER_READ = ["gold_aa_internal.published_tours", "silver_aa_internal.raw_tours", "silver_aa_internal.seo_context"]
LEGACY_TENANT_ONLY = ["silver_aa_internal.generated_content", "silver_aa_internal.quality_scores",
                      "gold_aa_internal.content_exports", "gold_aa_internal.webhook_deliveries",
                      "shared.pipeline_runs"]
DENY_ALL = ["acp_shared.acp_output_rules"]
RLS_TABLES = TEMPLATE_229 + MASTER_READ + LEGACY_TENANT_ONLY + DENY_ALL      # the 15 of plan §0
NO_WRITE_239 = ["acp_shared.angle_gate_option", "acp_shared.tenant_atom_state", "acp_shared.year_plan"]
MODES = ("unset", "empty", "foreign", "master", "own")


class _Undo(Exception):
    """Raised to roll a savepoint back (undoes SET LOCAL ROLE / set_config)."""


def _err(e):
    return f"{type(e).__name__}: {str(e)[:160]}"


def _parse(dsn):
    u = urlparse(dsn)
    return dict(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password,
                database=(u.path or "/").lstrip("/") or None)


async def _connect(dsn):
    p = _parse(dsn)
    return await asyncpg.connect(host=p["host"], port=p["port"], user=p["user"], password=p["password"],
                                 database=p["database"], ssl="require", timeout=20)


async def _savepoint(c, fn):
    """Run fn(c) in a savepoint that is always rolled back; return its value or {'error': ...}."""
    try:
        async with c.transaction():
            raise _Undo(await fn(c))
    except _Undo as u:
        return u.args[0]
    except Exception as e:  # noqa: BLE001 — record, keep probing
        return {"error": _err(e)}


async def _guc(c, mode, own):
    if mode == "unset":
        return await c.fetchval("SELECT current_setting('app.tenant_id', true)")
    val = {"empty": "", "foreign": FOREIGN, "master": MASTER, "own": own}[mode]
    await c.execute("SELECT set_config('app.tenant_id', $1, true)", val)
    return val


def _cell_sql(fq):
    return (f"SELECT count(*) AS rows, count(DISTINCT tenant_id) AS tenants, "
            f"count(*) FILTER (WHERE tenant_id::text = '{MASTER}') AS master_rows, "
            f"count(*) FILTER (WHERE tenant_id IS NULL) AS null_tenant_rows, "
            f"count(*) FILTER (WHERE tenant_id IS NOT NULL AND tenant_id::text <> '{MASTER}' "
            f"AND tenant_id::text IS DISTINCT FROM NULLIF(current_setting('app.tenant_id', true), '')) "
            f"AS leak_rows FROM {fq}")                                         # no tenant WHERE on purpose


async def _cell(c, fq, mode, own, role):
    async def run(cc):
        seen = await _guc(cc, mode, own)
        if role:
            await cc.execute(f'SET LOCAL ROLE "{role}"')
        row = dict(await cc.fetchrow(_cell_sql(fq)))
        row["rls_active"] = await cc.fetchval("SELECT row_security_active($1::regclass)", fq)
        if mode == "unset":
            row["guc_seen"] = seen
        return row
    return await _savepoint(c, run)


async def _runner_counts(c, fq, own):
    """As the runner (control): total, per-tenant counts, and the count under a foreign GUC."""
    async def run(cc):
        total = await cc.fetchval(f"SELECT count(*) FROM {fq}")
        master = await cc.fetchval(f"SELECT count(*) FROM {fq} WHERE tenant_id::text = $1", MASTER)
        own_n = await cc.fetchval(f"SELECT count(*) FROM {fq} WHERE tenant_id::text = $1", own)
        nulls = await cc.fetchval(f"SELECT count(*) FROM {fq} WHERE tenant_id IS NULL")
        await cc.execute("SELECT set_config('app.tenant_id', $1, true)", FOREIGN)
        foreign = await cc.fetchval(f"SELECT count(*) FROM {fq}")
        active = await cc.fetchval("SELECT row_security_active($1::regclass)", fq)
        return {"total": total, "master": master, "own": own_n, "null_tenant": nulls,
                "foreign_guc": foreign, "rls_active": active, "unaffected": (foreign == total and not active)}
    return await _savepoint(c, run)


async def _busiest_non_master(c, fq):
    async def run(cc):
        return await cc.fetchval(f"SELECT tenant_id::text FROM {fq} WHERE tenant_id IS NOT NULL "
                                 f"AND tenant_id::text <> $1 GROUP BY 1 ORDER BY count(*) DESC, 1 LIMIT 1", MASTER)
    v = await _savepoint(c, run)
    return v if isinstance(v, str) else None


def _expect(fq, mode, runner, own_is_master, phase):
    """Expected aa_app_user cell: ('rows', n) / ('error', '22P02') / ('denied',) / None (no expectation).
    mode "unset_null" is `unset` when the GUC was really NULL (never set on the session): no rows, never
    22P02; `unset` holding '' is judged as "empty"."""
    null_guc = mode == "unset_null"
    if null_guc:
        mode = "unset"
    if fq in DENY_ALL:
        return ("denied",)
    if not isinstance(runner, dict) or "total" not in runner:
        return None
    n_master, n_own, n_null = runner["master"], runner["own"], runner["null_tenant"]
    tenant_n = {"unset": 0, "empty": 0, "foreign": 0, "master": n_master, "own": n_own}[mode]
    if own_is_master and mode == "own":
        tenant_n = n_master
    if fq == "acp_shared.facts":
        return ("rows", tenant_n + n_null)                 # platform facts (tenant_id NULL) for everyone
    if fq in TEMPLATE_229:
        return ("rows", tenant_n)
    post = phase == "post-239"
    if fq in MASTER_READ:
        if post:
            return ("rows", tenant_n if mode == "master" or (mode == "own" and own_is_master)
                    else tenant_n + n_master)
        if mode in ("unset", "empty") and fq == "silver_aa_internal.seo_context" and not null_guc:
            return ("error", "22P02")
        return ("rows", tenant_n)
    if fq in LEGACY_TENANT_ONLY:
        if mode in ("unset", "empty") and not post and not null_guc:
            return ("error", "22P02")
        return ("rows", tenant_n)
    return None


def _verdict(exp, cell):
    if exp is None:
        return "no-expectation"
    err = cell.get("error") if isinstance(cell, dict) else None
    if exp[0] == "denied":
        return "pass" if err and "InsufficientPrivilege" in err else "FAIL"
    if exp[0] == "error":
        return "pass-known-gap" if err and "InvalidTextRepresentation" in err else "FAIL"
    if err:
        return "FAIL"
    return "pass" if cell["rows"] == exp[1] and cell["leak_rows"] == 0 else "FAIL"


async def _privs(c, fq, role):
    letters = ""
    for p, ch in (("SELECT", "S"), ("INSERT", "I"), ("UPDATE", "U"), ("DELETE", "D"), ("TRUNCATE", "T")):
        if await c.fetchval("SELECT has_table_privilege($1, $2::regclass, $3)", role, fq, p):
            letters += ch
    return letters


async def _probe(c, out, cell_conn, role_for_cells):
    """Metadata and runner counts on c (the runner); aa_app_user cells on cell_conn (c with SET ROLE, or
    the aa_app_user login with role_for_cells None)."""
    phase = "post-239" if await c.fetchval(
        "SELECT EXISTS (SELECT 1 FROM shared.schema_versions WHERE version = '239')") else "pre-239"
    out["phase"] = phase
    out["schema_versions_latest"] = await c.fetchval(
        "SELECT max(version) FROM shared.schema_versions WHERE version ~ '^[0-9]+$'")

    found = [r["fq"] for r in await c.fetch(
        "SELECT n.nspname || '.' || c.relname AS fq FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE c.relrowsecurity AND c.relkind IN ('r', 'p') AND n.nspname = ANY($1::text[]) ORDER BY 1", SCHEMAS)]
    out["rls_tables_found"] = found
    out["rls_tables_missing"] = [t for t in RLS_TABLES if t not in found]
    out["rls_tables_extra"] = [t for t in found if t not in RLS_TABLES]

    tables = {}
    summary = {"pass": 0, "pass-known-gap": 0, "FAIL": 0, "no-expectation": 0}
    for fq in RLS_TABLES + out["rls_tables_extra"]:
        if await c.fetchval("SELECT to_regclass($1)", fq) is None:
            tables[fq] = {"missing": True}
            continue
        meta = dict(await c.fetchrow(
            "SELECT pg_get_userbyid(relowner) AS owner, relrowsecurity AS rls, relforcerowsecurity AS force "
            "FROM pg_class WHERE oid = $1::regclass", fq))
        meta["policies"] = [dict(r) for r in await c.fetch(
            "SELECT policyname, permissive, roles::text[] AS roles, cmd, qual, with_check FROM pg_policies "
            "WHERE schemaname || '.' || tablename = $1 ORDER BY policyname", fq)]
        meta["aa_app_user_privs"] = await _privs(c, fq, TENANT_ROLE)
        own = await _busiest_non_master(c, fq)
        own_is_master = own is None
        own = own or MASTER
        meta["own_tenant"] = own
        meta["runner"] = await _runner_counts(c, fq, own)
        cells, verdicts = {}, {}
        for mode in MODES:
            cell = await _cell(cell_conn, fq, mode, own, role_for_cells)
            cells[mode] = cell
            judged = mode
            if mode == "unset" and isinstance(cell, dict) and "error" not in cell and cell.get("guc_seen") is None:
                judged = "unset_null"
            v = _verdict(_expect(fq, judged, meta["runner"], own_is_master, phase), cell)
            verdicts[mode] = v
            summary[v] += 1
        meta["aa_app_user"] = cells
        meta["verdict"] = verdicts
        meta["runner_verdict"] = "pass" if isinstance(meta["runner"], dict) and meta["runner"].get("unaffected") \
            else ("n/a" if fq in DENY_ALL else "FAIL")
        tables[fq] = meta
    out["tables"] = tables
    out["summary"] = summary

    # tenant-role writes on tables WITHOUT RLS (239 revokes the three of NO_WRITE_239)
    rows = await c.fetch(
        "SELECT n.nspname || '.' || c.relname AS fq FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE NOT c.relrowsecurity AND c.relkind IN ('r', 'p') AND n.nspname = ANY($1::text[]) "
        "AND has_table_privilege($2, c.oid, 'INSERT, UPDATE, DELETE, TRUNCATE') ORDER BY 1", SCHEMAS, TENANT_ROLE)
    out["no_rls_tables_tenant_role_can_write"] = {r["fq"]: await _privs(c, r["fq"], TENANT_ROLE) for r in rows}
    out["no_write_239"] = {t: await _privs(c, t, TENANT_ROLE) for t in NO_WRITE_239}
    out["aa_app_user_role"] = dict(await c.fetchrow(
        "SELECT rolsuper, rolbypassrls, rolconnlimit, "
        "ARRAY(SELECT m.member::regrole::text FROM pg_auth_members m WHERE m.roleid = r.oid) AS members "
        "FROM pg_roles r WHERE rolname = $1", TENANT_ROLE))
    out["aa_app_user_connections_now"] = await c.fetchval(
        "SELECT count(*) FROM pg_stat_activity WHERE usename = $1", TENANT_ROLE)


async def _main(out):
    out.update({"probe": "aa817_probe_v2", "foreign_uuid": FOREIGN, "master_uuid": MASTER})
    sm = boto3.client("secretsmanager", region_name=REGION)
    main_dsn = sm.get_secret_value(SecretId=MAIN_SECRET)["SecretString"].strip()
    out["main_secret_user"] = _parse(main_dsn)["user"]
    c = await _connect(main_dsn)
    a = None
    try:
        tr = c.transaction(readonly=True)
        await tr.start()
        try:
            await c.execute(f"SET LOCAL statement_timeout = '{STMT_TIMEOUT}'")
            await c.execute("SET LOCAL lock_timeout = '3s'")
            out["identity"] = dict(await c.fetchrow(
                "SELECT current_user AS cu, r.rolsuper, r.rolbypassrls, current_setting('server_version') AS ver, "
                "current_setting('transaction_read_only') AS read_only FROM pg_roles r WHERE r.rolname = current_user"))
            can_set = await _savepoint(c, lambda cc: cc.execute(f'SET LOCAL ROLE "{TENANT_ROLE}"'))
            out["set_role_aa_app_user"] = "ok" if not isinstance(can_set, dict) else can_set
            if not isinstance(can_set, dict):
                out["cells_as"] = f"runner + SET LOCAL ROLE {TENANT_ROLE}"
                await _probe(c, out, c, TENANT_ROLE)
                return
            # SET ROLE refused (nothing is granted): the aa_app_user cells come from the tenant pool's own
            # login, in its own READ ONLY transaction, rolled back; metadata and the runner control counts
            # stay on this connection.
            app_dsn = sm.get_secret_value(SecretId=APP_USER_SECRET)["SecretString"].strip()
            out["cells_as"] = f"login {_parse(app_dsn)['user']} (SET ROLE refused)"
            a = await _connect(app_dsn)
            atr = a.transaction(readonly=True)
            await atr.start()
            try:
                await a.execute(f"SET LOCAL statement_timeout = '{STMT_TIMEOUT}'")
                await _probe(c, out, a, None)
            finally:
                await atr.rollback()
        finally:
            await tr.rollback()
    finally:
        if a is not None:
            await a.close()
        await c.close()


async def main():
    out = {}
    try:
        await _main(out)
    except Exception as e:  # noqa: BLE001 — always emit one JSON line, with what was collected
        out["fatal"] = _err(e)
    out["s3_key"] = f"scripts/out/s239_aa817_probe_v2_{out.get('phase', 'unknown')}.json"
    line = json.dumps(out, default=str, separators=(",", ":"))
    try:
        with open("/tmp/aa817_probe_v2_out.json", "w") as f:
            f.write(line)
    except OSError:
        pass
    try:  # full copy in S3, readable without a second exec session if the exec output is truncated
        boto3.client("s3", region_name=REGION).put_object(
            Bucket=OUT_BUCKET, Key=out["s3_key"], Body=line.encode(), ContentType="application/json")
    except Exception as e:  # noqa: BLE001 — the stdout line is still the primary output
        out["s3_key"] = None
        out["s3_error"] = _err(e)
        line = json.dumps(out, default=str, separators=(",", ":"))
    print(line)


asyncio.run(main())
