"""Run: python3 -m unittest discover -s tools/ops -p 'test_*.py' (from the repo root).

tools/ops/gameday_seed_job.py: the decision logic on a fake connection (always), and the SQL on a real PostgreSQL
when GAMEDAY_PG_DSN points at a scratch database (skipped otherwise; the table is created from the column list of
docs/architecture/db-schema-reference.md, shared.job, with the defaults of CIS migration 174).
"""
from __future__ import annotations

import asyncio
import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gameday_seed_job as g  # noqa: E402


class FakeConn:
    def __init__(self, open_rows=()):
        self.open_rows = list(open_rows)
        self.calls = []

    async def fetch(self, sql, *args):
        self.calls.append((sql, args))
        if sql == g.OPEN_SQL:
            return self.open_rows
        if sql == g.CANCEL_QUEUED_SQL:
            return [{"id": r["id"]} for r in self.open_rows if r["status"] == "queued"]
        if sql == g.CANCEL_RUNNING_SQL:
            return [{"id": r["id"]} for r in self.open_rows if r["status"] == "running"]
        raise AssertionError(sql)

    async def fetchrow(self, sql, *args):
        self.calls.append((sql, args))
        assert sql == g.SEED_SQL
        return {"id": "00000000-0000-4000-8000-000000000001", "status": "queued", "run_after": "now"}


def run(conn, action, env=None):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = asyncio.run(g.run(conn, action, env or {}))
    return code, out.getvalue()


def row(status):
    return {"id": f"id-{status}", "status": status, "attempt": 0, "run_after": "t", "started_at": None,
            "cancel_requested": False}


class SeedLogicTest(unittest.TestCase):
    def test_seed_inserts_one_tagged_noop_row(self):
        conn = FakeConn()
        code, out = run(conn, "seed", {"SLEEP_SECONDS": "600"})
        self.assertEqual(code, 0)
        self.assertIn("SEEDED id=00000000-0000-4000-8000-000000000001 kind=noop_sleep status=queued seconds=600", out)
        sql, args = conn.calls[-1]
        self.assertEqual(args, ("noop_sleep", json.dumps({"seconds": 600}), "aa1023-gameday"))

    def test_seed_refuses_when_a_tagged_row_is_open(self):
        conn = FakeConn([row("running")])
        code, out = run(conn, "seed")
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", out)
        self.assertEqual(len(conn.calls), 1)                     # no insert

    def test_seconds_bounds(self):
        self.assertEqual(g.seconds_from_env({}), 900)
        for bad in ("59", "3601", "x", "-5", "1e3"):
            with self.subTest(bad), self.assertRaises(ValueError):
                g.seconds_from_env({"SLEEP_SECONDS": bad})

    def test_clear_cancels_queued_and_flags_running(self):
        code, out = run(FakeConn([row("queued"), row("running")]), "clear")
        self.assertEqual(code, 0)
        self.assertIn("CLEARED queued_cancelled=1 running_cancel_requested=1", out)

    def test_status_and_unknown_action(self):
        code, out = run(FakeConn([row("queued")]), "status")
        self.assertEqual(code, 0)
        self.assertIn("OPEN_COUNT 1", out)
        code, out = run(FakeConn(), "drop")
        self.assertEqual(code, 2)

    def test_every_write_is_scoped_to_the_tag_and_kind(self):
        for sql in (g.CANCEL_QUEUED_SQL, g.CANCEL_RUNNING_SQL, g.OPEN_SQL):
            self.assertIn("kind = $1 AND created_by = $2", sql)


JOB_DDL = """
CREATE SCHEMA IF NOT EXISTS shared;
DROP TABLE IF EXISTS shared.job;
CREATE TABLE shared.job (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(), kind text NOT NULL, payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'queued', attempt integer NOT NULL DEFAULT 0, max_attempts integer NOT NULL DEFAULT 3,
    run_after timestamptz NOT NULL DEFAULT now(), locked_by text, locked_until timestamptz,
    cancel_requested boolean NOT NULL DEFAULT false, idempotency_key text, progress jsonb NOT NULL DEFAULT '{}'::jsonb,
    result jsonb, cost_usd numeric(12,6) NOT NULL DEFAULT 0, error text, parent_job_id uuid, created_by text,
    created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz, finished_at timestamptz,
    CONSTRAINT job_status_check CHECK (status IN ('queued','running','succeeded','failed','stopped_budget','cancelled')));
"""


@unittest.skipUnless(os.environ.get("GAMEDAY_PG_DSN"), "set GAMEDAY_PG_DSN to a scratch PostgreSQL database")
class SeedSqlOnPostgresTest(unittest.TestCase):
    def test_seed_status_clear_round_trip(self):
        import asyncpg

        async def go():
            conn = await asyncpg.connect(os.environ["GAMEDAY_PG_DSN"])
            try:
                await conn.execute(JOB_DDL)
                await conn.execute("INSERT INTO shared.job (kind, created_by) VALUES ('noop_sleep', 'someone-else')")
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(await g.run(conn, "seed", {"SLEEP_SECONDS": "120"}), 0)
                    self.assertEqual(await g.run(conn, "seed", {}), 1)
                    await conn.execute("UPDATE shared.job SET status = 'running', started_at = now() "
                                       "WHERE created_by = 'aa1023-gameday'")
                    await g.run(conn, "seed", {})
                    self.assertEqual(await g.run(conn, "clear", {}), 0)
                text = out.getvalue()
                self.assertIn("status=queued seconds=120", text)
                self.assertIn("CLEARED queued_cancelled=0 running_cancel_requested=1", text)
                rows = await conn.fetch("SELECT created_by, status, cancel_requested, payload FROM shared.job "
                                        "ORDER BY created_by")
                self.assertEqual([(r["created_by"], r["status"], r["cancel_requested"]) for r in rows],
                                 [("aa1023-gameday", "running", True), ("someone-else", "queued", False)])
                self.assertEqual(json.loads(rows[0]["payload"]), {"seconds": 120})
                await conn.execute("UPDATE shared.job SET status = 'queued' WHERE created_by = 'aa1023-gameday'")
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    await g.run(conn, "clear", {})
                    await g.run(conn, "status", {})
                self.assertIn("queued_cancelled=1", out.getvalue())
                self.assertIn("OPEN_COUNT 0", out.getvalue())
                self.assertEqual(await conn.fetchval("SELECT count(*) FROM shared.job WHERE created_by = "
                                                     "'someone-else' AND status = 'queued'"), 1)
            finally:
                await conn.execute("DROP TABLE IF EXISTS shared.job")
                await conn.close()

        asyncio.run(go())


if __name__ == "__main__":
    unittest.main()
