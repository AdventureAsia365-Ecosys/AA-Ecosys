"""Run: python3 -m unittest discover -s tools/ops -p 'test_aa1191*.py' (from the repo root).

tools/ops/aa1191_vnd_dry_run.py on a fake connection: aggregate rows only (codes and counts), a section the login
cannot read is reported as skipped without stopping the others, the crm section counts agency by agency and sums,
every statement is a SELECT (or the role / tenant switch of the crm section). Invented values only.
"""
from __future__ import annotations

import asyncio
import contextlib
import io
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aa1191_vnd_dry_run as d  # noqa: E402

TENANTS = ["00000000-0000-4000-8000-000000000001", "00000000-0000-4000-8000-000000000002"]


class InterfaceMismatch(Exception):
    """Stands in for asyncpg's InterfaceError on an argument count mismatch."""


class Denied(Exception):
    sqlstate = "42501"


class FakeTx:
    def __init__(self, conn, readonly=False):
        self.conn, self.readonly = conn, readonly

    async def __aenter__(self):
        if self.readonly:
            self.conn.readonly = True
        return self

    async def __aexit__(self, *exc):
        return False


class FakeConn:
    def __init__(self, *, deny=(), role_ok=True):
        self.deny = set(deny)            # table prefixes this login cannot read
        self.role_ok = role_ok
        self.tenant = ""
        self.readonly = False
        self.statements = []

    def transaction(self, readonly=False):
        return FakeTx(self, readonly)

    async def execute(self, sql, *args):
        self.statements.append(sql)
        if "SET LOCAL ROLE" in sql and not self.role_ok:
            raise Denied("permission denied to set role")
        if "set_config('app.tenant_id'" in sql:
            self.tenant = args[0] if args else ""

    async def fetch(self, sql, *args):
        self.statements.append(sql)
        # like asyncpg: the argument count must match the $n placeholders (S297: a parameter sent to a query with
        # no $1 raised InterfaceError and the whole cis section read as "skipped")
        wanted = len(set(re.findall(r"\$(\d+)", sql)))
        if len(args) != wanted:
            raise InterfaceMismatch(f"the server expects {wanted} argument(s), {len(args)} were passed")
        for prefix in self.deny:
            if prefix in sql:
                raise Denied(f"permission denied for {prefix}")
        if sql == d.CRM_TENANTS_SQL:
            return [{"tenant_id": t} for t in TENANTS]
        if "FROM shared.plan" in sql:
            return [{"live": True, "product": "content", "n": 3}]
        if "FROM shared.tenants" in sql:
            return [{"kind": "agency", "account_status": "active", "n": 1}]
        if "FROM shared.tenant_subscription" in sql:
            return []
        if "FROM booking.agency_invoice" in sql:
            return [{"invoice_kind": "saas", "status": "draft", "n": 2}]
        if "FROM booking.billing_terms" in sql:
            return []
        if "FROM crm.proposal" in sql:
            return [{"kind": "text", "status": "draft", "n": 1}] if self.tenant == TENANTS[0] else []
        if "FROM crm.tenant_settings" in sql:
            return [{"field": "base_currency", "n": 1}]
        raise AssertionError(sql)


def run(conn):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        report = asyncio.run(d.main(conn))
    return report, out.getvalue()


class DryRunTest(unittest.TestCase):
    def test_master_login_reads_every_section_and_sums_the_agencies(self):
        conn = FakeConn()
        report, text = run(conn)
        self.assertTrue(conn.readonly)
        self.assertEqual(report["cis"]["plans_with_vnd_price"], [{"live": True, "product": "content", "n": 3}])
        invoices = report["booking"]["agency_invoices_vnd"]
        self.assertEqual(invoices, [{"invoice_kind": "saas", "status": "draft", "n": 2}])
        self.assertEqual(report["crm"]["proposals_vnd"], [{"kind": "text", "status": "draft", "n": 1}])
        self.assertEqual(report["crm"]["tenant_settings_base_currency_vnd"], [{"field": "base_currency", "n": 2}])
        self.assertEqual((report["crm"]["agencies_scanned"], report["crm"]["agencies_with_vnd"]), (2, 2))
        self.assertIn("DRYRUN cis ", text)
        self.assertEqual(json.loads(text.split("DRYRUN_JSON ", 1)[1])["issue"], "AA-1191")

    def test_an_app_login_skips_the_sections_it_cannot_read(self):
        report, _ = run(FakeConn(deny=("booking.", "crm.", "shared.tenants ORDER BY"), role_ok=False))
        self.assertIn("tenants_billing_currency_vnd", report["cis"])
        self.assertEqual(report["booking"], {"skipped": "Denied 42501"})
        self.assertEqual(report["crm"], {"skipped": "Denied 42501"})

    def test_only_reads_and_the_crm_context_switch(self):
        conn = FakeConn()
        run(conn)
        for sql in conn.statements:
            head = sql.strip().split()[0].upper()
            self.assertIn(head, {"SELECT", "SET"}, sql)
        for sql in conn.statements:
            self.assertNotRegex(sql.upper(), r"\b(INSERT|UPDATE|DELETE|ALTER|DROP|TRUNCATE)\b")

    def test_no_row_value_beyond_codes_and_counts(self):
        report, _ = run(FakeConn())
        for section in ("cis", "booking"):
            for rows in report[section].values():
                for row in rows:
                    self.assertTrue(set(row) <= {"live", "product", "kind", "account_status", "status", "invoice_kind",
                                                 "default_row", "n"}, row)


if __name__ == "__main__":
    unittest.main()
