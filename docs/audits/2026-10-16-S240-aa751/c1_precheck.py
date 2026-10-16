"""AA-751 C1 pre-check — READ-ONLY evidence that migration 242 can apply to Dev shared.job (plan §2 C1, step 2).

The dump (docs/architecture/db-schema-reference.md) is stale for shared.job (plan F1), so this probe is the
source of truth for both the data and the current catalog before 242 merges / window A applies it.

Run inside the CIS api container (python3 + asyncpg + boto3) with the S3-mediated ECS exec pattern.
Writes ONE JSON document to s3://aa-cis-bronze-005097885195/scripts/out/s240_aa751_c1_precheck.json and
prints only `OK <bytes>` (lesson S237: ECS exec output is cut silently; read the S3 copy, compare its size
with <bytes> and json.loads it before reading). A DB failure is recorded in the JSON as "fatal" / "errors",
never printed. Never prints or stores a password or a DSN, only role names.

Safety: every statement runs inside ONE `READ ONLY` transaction on the main secret aa-cis/dev/rds (the API
task's runner, the same role DB Migrate applies 242 as), ROLLED BACK at the end; statement_timeout 15s,
lock_timeout 3s (a catalog read never queues behind a lock for long). Nothing is created, altered or written.

Items (each in its own savepoint, so one failure never loses the rest):
  identity    current_user, shared.job owner, runner is a member of the owner (242 guard 1a), runner has CREATE
              on schema shared (242's CREATE OR REPLACE FUNCTION shared.job_set_updated_at(); guard 1a does not
              check it), server version, latest schema version, 242 already registered?
  data        the plan's counts: lease_bad (running without locked_by / locked_until), attempt_bad
              (attempt < 0 or max_attempts < 1), kind_bad (kind !~ the CIS pattern), n; up to 20 offending
              rows per rule (id, kind, status, created_at); every kind with its row count per status.
  catalog     columns, constraints (name, type, validated, definition), indexes, non-internal triggers with
              their functions, reloptions, plus 242 specifics: is the 174 max_attempts CHECK still there
              and under which name, do job_kind_chk / job_lease_chk / job_attempts_chk / the function
              shared.job_set_updated_at() / trigger job_set_updated_at already exist (and with which
              definition), are the template's six indexes all present (by definition).
  stats       pg_stat_user_tables for shared.job (live / dead tuples, last (auto)vacuum / analyze).
  queue       shared.job queued / running per kind (the DB Migrate idle rule; exempt kind
              ops_rds_role_connections listed apart), and open shared.rerun_wave rows (window A step 0).

verdict.precheck_242_ok = no bad row, the runner may alter the table, the runner may create in schema shared,
shared.job_set_updated_at() absent or owned by a role the runner is a member of (CREATE OR REPLACE and COMMENT ON
need the function's owner), no name collision with another definition, every template index present, no error.
Anything else: fix the rows / ask Nghiệp before window A.
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
OUT_BUCKET = "aa-cis-bronze-005097885195"
OUT_KEY = "scripts/out/s240_aa751_c1_precheck.json"
STMT_TIMEOUT = "15s"
CIS_KIND_PATTERN = "^(?!bk_|tp_)[a-z][a-z0-9_]*$"
IDLE_EXEMPT_KINDS = ["ops_rds_role_connections"]
SAMPLE = 20

# The definitions 242 adds, exactly as pg_get_constraintdef prints them (242 guard 1b refuses another one).
WANT_CHECKS = {
    "job_kind_chk": "CHECK ((kind ~ '^(?!bk_|tp_)[a-z][a-z0-9_]*$'::text))",
    "job_lease_chk": "CHECK (((status <> 'running'::text) OR ((locked_by IS NOT NULL) AND (locked_until IS NOT NULL))))",
    "job_attempts_chk": "CHECK (((attempt >= 0) AND (max_attempts >= 1)))",
}
SUPERSEDED_CHECK = "CHECK ((max_attempts >= 1))"
# The template's indexes, name and table dropped (shared/jobs/job_table_shape.normalise_index), PK included.
WANT_INDEXES = [
    "UNIQUE USING btree (id)",
    "UNIQUE USING btree (idempotency_key) WHERE (idempotency_key IS NOT NULL)",
    "USING btree (run_after, created_at) WHERE (status = 'queued'::text)",
    "USING btree (kind, locked_until) WHERE (status = 'running'::text)",
    "USING btree (kind, created_at DESC)",
    "USING btree (parent_job_id) WHERE (parent_job_id IS NOT NULL)",
    "USING btree (finished_at, id) WHERE (finished_at IS NOT NULL)",
]


def _err(e):
    return f"{type(e).__name__}: {str(e)[:300]}"


def _parse(dsn):
    u = urlparse(dsn)
    return dict(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password,
                database=(u.path or "/").lstrip("/") or None)


async def _connect(dsn):
    p = _parse(dsn)
    return await asyncpg.connect(host=p["host"], port=p["port"], user=p["user"], password=p["password"],
                                 database=p["database"], ssl="require", timeout=20,
                                 server_settings={"application_name": "s240-aa751-c1-precheck"})


def _norm_index(definition):
    # "CREATE [UNIQUE] INDEX <name> ON shared.job USING ..." -> "[UNIQUE ]USING ..."
    unique = "UNIQUE " if definition.startswith("CREATE UNIQUE INDEX ") else ""
    i = definition.find(" USING ")
    return unique + (definition[i + 1:] if i >= 0 else definition)


async def _identity(c, out):
    out["identity"] = dict(await c.fetchrow(
        "SELECT current_user AS cu, session_user AS su, r.rolsuper, "
        "pg_has_role(current_user, to_regrole('rds_superuser'), 'MEMBER') AS rds_superuser_member, "
        "current_setting('server_version') AS ver, current_setting('transaction_read_only') AS read_only, "
        "has_schema_privilege(current_user, 'shared', 'CREATE') AS can_create_in_shared "
        "FROM pg_roles r WHERE r.rolname = current_user"))
    row = await c.fetchrow(
        "SELECT pg_get_userbyid(relowner) AS owner, "
        "pg_has_role(current_user, relowner, 'MEMBER') AS runner_member_of_owner, relpersistence::text, "
        "relkind::text FROM pg_class WHERE oid = 'shared.job'::regclass")
    out["table"] = dict(row)
    out["schema_versions_latest"] = await c.fetchval(
        "SELECT max(version::int) FROM shared.schema_versions WHERE version ~ '^[0-9]+$'")
    out["schema_version_242_present"] = await c.fetchval(
        "SELECT EXISTS (SELECT 1 FROM shared.schema_versions WHERE version = '242')")


async def _data(c, out):
    row = await c.fetchrow(
        """SELECT count(*) FILTER (WHERE status = 'running' AND (locked_by IS NULL OR locked_until IS NULL)) AS lease_bad,
                  count(*) FILTER (WHERE attempt < 0 OR max_attempts < 1) AS attempt_bad,
                  count(*) FILTER (WHERE kind !~ $1) AS kind_bad,
                  count(*) AS n
             FROM shared.job""", CIS_KIND_PATTERN)
    out["data"] = dict(row)
    cols = "id::text, kind, status, attempt, max_attempts, locked_by IS NOT NULL AS has_locked_by, " \
           "locked_until IS NOT NULL AS has_locked_until, created_at"
    out["data"]["lease_bad_rows"] = [dict(r) for r in await c.fetch(
        f"SELECT {cols} FROM shared.job WHERE status = 'running' AND (locked_by IS NULL OR locked_until IS NULL) "
        f"ORDER BY created_at LIMIT {SAMPLE}")]
    out["data"]["attempt_bad_rows"] = [dict(r) for r in await c.fetch(
        f"SELECT {cols} FROM shared.job WHERE attempt < 0 OR max_attempts < 1 ORDER BY created_at LIMIT {SAMPLE}")]
    out["data"]["kind_bad_rows"] = [dict(r) for r in await c.fetch(
        f"SELECT {cols} FROM shared.job WHERE kind !~ $1 ORDER BY created_at LIMIT {SAMPLE}", CIS_KIND_PATTERN)]
    out["data"]["kinds"] = [dict(r) for r in await c.fetch(
        "SELECT kind, status, count(*)::int AS n, (kind ~ $1) AS kind_ok FROM shared.job "
        "GROUP BY kind, status ORDER BY kind, status", CIS_KIND_PATTERN)]


async def _catalog(c, out):
    # Pinned path: pg_get_*def then qualifies shared.job whatever the runner's search_path (plan F15).
    await c.execute("SET LOCAL search_path = pg_catalog")
    cat = out["catalog"] = {}
    cat["columns"] = [dict(r) for r in await c.fetch(
        """SELECT a.attnum, a.attname, format_type(a.atttypid, a.atttypmod) AS type, a.attnotnull,
                  pg_get_expr(d.adbin, d.adrelid) AS dflt
             FROM pg_attribute a LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
            WHERE a.attrelid = 'shared.job'::regclass AND a.attnum > 0 AND NOT a.attisdropped
            ORDER BY a.attnum""")]
    cons = [dict(r) for r in await c.fetch(
        "SELECT conname, contype::text, convalidated, pg_get_constraintdef(oid) AS def FROM pg_constraint "
        "WHERE conrelid = 'shared.job'::regclass ORDER BY conname")]
    cat["constraints"] = cons
    cat["indexes"] = [r["def"] for r in await c.fetch(
        "SELECT pg_get_indexdef(indexrelid) AS def FROM pg_index WHERE indrelid = 'shared.job'::regclass "
        "ORDER BY indexrelid")]
    cat["triggers"] = [dict(r) for r in await c.fetch(
        """SELECT t.tgname, t.tgtype::int, t.tgenabled::text, p.oid::regprocedure::text AS function, p.prosrc,
                  p.proconfig
             FROM pg_trigger t JOIN pg_proc p ON p.oid = t.tgfoid
            WHERE t.tgrelid = 'shared.job'::regclass AND NOT t.tgisinternal ORDER BY t.tgname""")]
    cat["reloptions"] = await c.fetchval("SELECT reloptions FROM pg_class WHERE oid = 'shared.job'::regclass")
    func = await c.fetchrow(
        "SELECT p.oid::regprocedure::text AS sig, pg_get_userbyid(p.proowner) AS owner, "
        "pg_has_role(current_user, p.proowner, 'MEMBER') AS runner_member_of_owner, p.prosrc, p.proconfig "
        "FROM pg_proc p WHERE p.oid = to_regprocedure('shared.job_set_updated_at()')")

    by_name = {x["conname"]: x for x in cons}
    m242 = cat["m242"] = {}
    m242["superseded_max_attempts_check"] = [x["conname"] for x in cons
                                             if x["contype"] == "c" and x["def"] == SUPERSEDED_CHECK]
    m242["check_names"] = {
        name: ("absent" if name not in by_name else
               "same_definition" if by_name[name]["def"] == want else f"DIFFERENT: {by_name[name]['def']}")
        for name, want in WANT_CHECKS.items()}
    m242["same_definition_other_name"] = {
        name: [x["conname"] for x in cons if x["def"] == want and x["conname"] != name]
        for name, want in WANT_CHECKS.items()}
    m242["function_job_set_updated_at"] = dict(func) if func else None
    m242["trigger_job_set_updated_at"] = next((t for t in cat["triggers"] if t["tgname"] == "job_set_updated_at"),
                                              None)
    have = [_norm_index(d) for d in cat["indexes"]]
    m242["template_indexes_missing"] = [w for w in WANT_INDEXES if w not in have]
    m242["indexes_not_in_template"] = [d for d, n in zip(cat["indexes"], have) if n not in WANT_INDEXES]
    m242["unvalidated_constraints"] = [x["conname"] for x in cons if not x["convalidated"]]
    status = [x for x in cons if x["contype"] == "c" and "status = ANY" in x["def"]]
    m242["status_checks"] = [x["def"] for x in status]


async def _stats(c, out):
    row = await c.fetchrow(
        "SELECT n_live_tup, n_dead_tup, n_mod_since_analyze, last_vacuum, last_autovacuum, last_analyze, "
        "last_autoanalyze, autovacuum_count, autoanalyze_count FROM pg_stat_user_tables "
        "WHERE relid = 'shared.job'::regclass")
    out["stats"] = dict(row) if row else None


async def _queue(c, out):
    rows = [dict(r) for r in await c.fetch(
        "SELECT kind, status, count(*)::int AS n, "
        "count(*) FILTER (WHERE status = 'queued' AND run_after <= now())::int AS due "
        "FROM shared.job WHERE status IN ('queued', 'running') GROUP BY kind, status ORDER BY kind, status")]
    q = out["queue"] = {"rows": rows}
    q["busy_non_exempt"] = sum(r["n"] for r in rows if r["kind"] not in IDLE_EXEMPT_KINDS)
    q["exempt"] = IDLE_EXEMPT_KINDS
    if await c.fetchval("SELECT to_regclass('shared.rerun_wave') IS NOT NULL"):
        q["open_waves"] = [dict(r) for r in await c.fetch(
            "SELECT id::text, name, created_at FROM shared.rerun_wave WHERE status = 'open' ORDER BY created_at")]
    else:
        q["open_waves"] = None


async def _main(out):
    sm = boto3.client("secretsmanager", region_name=REGION)
    dsn = sm.get_secret_value(SecretId=MAIN_SECRET)["SecretString"].strip()
    c = await _connect(dsn)
    try:
        tr = c.transaction(readonly=True)
        await tr.start()
        try:
            await c.execute(f"SET LOCAL statement_timeout = '{STMT_TIMEOUT}'")
            await c.execute("SET LOCAL lock_timeout = '3s'")
            for name, step in (("identity", _identity), ("data", _data), ("catalog", _catalog),
                               ("stats", _stats), ("queue", _queue)):
                try:
                    async with c.transaction():        # savepoint: one failed item never aborts the rest
                        await step(c, out)
                except Exception as e:  # noqa: BLE001 — record, keep probing
                    out["errors"][name] = _err(e)
        finally:
            await tr.rollback()
    finally:
        await c.close()


def _verdict(out):
    v = out["verdict"]
    d = out.get("data") or {}
    m = (out.get("catalog") or {}).get("m242") or {}
    v["no_bad_rows"] = bool(d) and d.get("lease_bad") == 0 and d.get("attempt_bad") == 0 and d.get("kind_bad") == 0
    v["runner_may_alter"] = bool((out.get("table") or {}).get("runner_member_of_owner"))
    v["runner_may_create_in_shared"] = bool((out.get("identity") or {}).get("can_create_in_shared"))
    func = m.get("function_job_set_updated_at")
    v["function_replaceable"] = bool(m) and "function_job_set_updated_at" in m and (
        func is None or bool(func.get("runner_member_of_owner")))
    v["no_name_collision"] = bool(m) and all(s in ("absent", "same_definition")
                                             for s in (m.get("check_names") or {}).values())
    v["template_indexes_present"] = bool(m) and m.get("template_indexes_missing") == []
    v["superseded_check_found"] = m.get("superseded_max_attempts_check") or []
    v["queue_idle_now"] = (out.get("queue") or {}).get("busy_non_exempt") == 0
    v["no_open_wave"] = not (out.get("queue") or {}).get("open_waves")
    v["precheck_242_ok"] = bool(v["no_bad_rows"] and v["runner_may_alter"] and v["runner_may_create_in_shared"]
                                and v["function_replaceable"] and v["no_name_collision"]
                                and v["template_indexes_present"] and not out["errors"] and "fatal" not in out)


async def main():
    out = {"probe": "s240_aa751_c1_precheck", "issue": "AA-751", "phase": "pre-242",
           "started_at": datetime.now(timezone.utc).isoformat(), "verdict": {}, "errors": {}}
    try:
        await _main(out)
    except Exception as e:  # noqa: BLE001 — always upload one JSON document, with what was collected
        out["fatal"] = _err(e)
    _verdict(out)
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
