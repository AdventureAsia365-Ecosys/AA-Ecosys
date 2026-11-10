"""Tests for gateway_status.py (S275): circuit-open refusals are counted apart from errors. Invented rows, no DB.

Run: python3 -m unittest discover -s tools/llm -p 'test_*.py'
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import os
import sys
import types
import unittest
from datetime import datetime, timezone
from unittest import mock

import gateway_status as gs

AT = datetime(2026, 11, 9, 18, 7, tzinfo=timezone.utc)


class _Conn:
    """A fake asyncpg connection: answers each of the tool's queries with invented rows."""

    def __init__(self):
        self.seen = []

    async def fetch(self, sql):
        self.seen.append(sql)
        if sql is gs.CONNECTIONS_SQL:
            return [{"connection_key": "probe-decide", "enabled": True, "access_state": "ok", "last_probe_at": AT,
                     "monthly_budget_usd": None, "mtd": 0.5, "ok24": 16085, "err24": 20, "exp24": 0,
                     "circ24": 4997}]
        if sql is gs.CIRCUIT_SQL:
            return [{"connection_key": "probe-decide", "stage": "probe_stage", "error_class": "other", "n": 4997}]
        if sql is gs.ERRORS_SQL:
            return [{"stage": "probe_stage", "connection_key": "probe-decide", "error_class": "other", "n": 20}]
        return []

    async def fetchrow(self, sql):
        return None

    async def fetchval(self, sql):
        return 0

    async def close(self):
        return None


class GatewayStatusTest(unittest.TestCase):
    def test_circuit_refusals_are_left_out_of_the_errors(self):
        self.assertIn("'circuit_open'", gs.CIRCUIT)
        self.assertIn("nothing was sent to the provider", gs.CIRCUIT)
        self.assertIn(gs.CIRCUIT, gs.NOT_ERROR)
        self.assertIn(f"NOT {gs.NOT_ERROR}", gs.ERRORS_SQL)
        self.assertIn(f"NOT {gs.NOT_ERROR}", gs.CONNECTIONS_SQL)
        self.assertIn("AS circ24", gs.CONNECTIONS_SQL)
        self.assertIn(gs.CIRCUIT, gs.CIRCUIT_SQL)

    def test_a_circuit_refusal_of_a_model_without_access_is_counted_once(self):
        """S276: a row matching both rules (a skipped deployment of a model with no access yet) is circuit-open only."""
        self.assertEqual(gs.EXPECTED_SENT, f"({gs.EXPECTED} AND NOT {gs.CIRCUIT})")
        self.assertIn(f"FILTER (WHERE {gs.EXPECTED_SENT})", gs.CONNECTIONS_SQL)
        self.assertIn(f"FILTER (WHERE {gs.CIRCUIT})", gs.CONNECTIONS_SQL)
        self.assertIn(f"AND {gs.EXPECTED_SENT}", gs.EXPECTED_SQL)
        self.assertNotIn(gs.EXPECTED_SENT, gs.CIRCUIT_SQL)
        self.assertIn(f"NOT {gs.NOT_ERROR}", gs.ERRORS_SQL)          # errors: still neither rule

    def test_the_report_prints_the_circuit_refusals_apart(self):
        conn = _Conn()

        async def connect(*a, **kw):
            return conn
        fake = types.SimpleNamespace(connect=connect)
        buf = io.StringIO()
        with mock.patch.dict(sys.modules, {"asyncpg": fake}), \
                mock.patch.dict(os.environ, {"DATABASE_URL": "postgresql://probe"}), \
                contextlib.redirect_stdout(buf):
            asyncio.run(gs.main())
        out = buf.getvalue()
        self.assertIn("16085 ok / 20 err / 0 expected / 4997 circuit-open", out)
        self.assertIn("== 24h circuit-open refusals", out)
        self.assertIn(gs.CIRCUIT_SQL, conn.seen)


if __name__ == "__main__":
    unittest.main()
