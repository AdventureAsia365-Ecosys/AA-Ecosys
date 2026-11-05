"""Red-team table for pilot_pii_guard.py (AA-969 part 2, root ADR 0019 d16).

Run: python3 -m unittest .claude/hooks/test_pilot_pii_guard.py   (or python3 .claude/hooks/test_pilot_pii_guard.py)
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pilot_pii_guard as g  # noqa: E402

PROTECTED = {
    ("crm", "traveler"): {"email", "display_name", "phone"},
    ("crm", "trip"): {"notes"},
    ("booking", "customers"): {"email"},
    ("shared", "tenants"): {"billing_email"},
}

REFUSED = [
    "SELECT email FROM crm.traveler",
    "select t.display_name, t.status from crm.traveler t where t.status = 'active'",
    "SELECT * FROM crm.traveler",
    "SELECT t.* FROM crm.traveler AS t",
    "SELECT row_to_json(t) FROM crm.traveler t",
    "SELECT lower(email) AS e FROM crm.traveler",
    "SELECT min(display_name) FROM crm.traveler",
    "SELECT string_agg(phone, ',') FROM crm.traveler",
    "SELECT tr.trip_id, t.email FROM crm.trip tr JOIN crm.traveler t ON t.traveler_id = tr.traveler_id",
    "SELECT s.e FROM (SELECT email AS e FROM crm.traveler) s",
    "WITH c AS (SELECT notes FROM crm.trip) SELECT count(*) FROM c",          # the inner select list (strict)
    "SELECT DISTINCT email FROM booking.customers",
    "SELECT billing_email FROM shared.tenants",
    "UPDATE crm.traveler SET status = 'x' WHERE traveler_id = $1 RETURNING email",
    "COPY crm.traveler TO STDOUT",
    "COPY crm.traveler (traveler_id, email) TO STDOUT",
    'SELECT "email" FROM crm."traveler"',
]
ALLOWED = [
    "SELECT count(*) AS n FROM crm.traveler",
    "SELECT count(DISTINCT email) AS n FROM crm.traveler",
    "SELECT count(*) FILTER (WHERE email IS NOT NULL) AS n FROM crm.traveler",
    "SELECT (email IS NULL) AS missing, count(*) AS n FROM crm.traveler GROUP BY 1",
    "SELECT status, count(*) FROM crm.traveler WHERE email LIKE '%@example.test' GROUP BY status",
    "SELECT traveler_id FROM crm.traveler WHERE display_name = 'x' ORDER BY email",
    "SELECT 1 FROM crm.traveler WHERE EXISTS (SELECT 1 FROM crm.trip WHERE notes IS NULL)",
    "SELECT name, slug FROM shared.tenants",
    "SELECT email FROM shared.admin_users",                                  # not a tenant table
    "SELECT 'email' AS label FROM crm.traveler",
    "SELECT now()",
    "UPDATE crm.traveler SET email = NULL WHERE traveler_id = $1 RETURNING traveler_id",
    "COPY crm.traveler (traveler_id, status) TO STDOUT",
    "-- SELECT email FROM crm.traveler\nSELECT count(*) FROM crm.traveler",
]

SCRIPT = '''
import asyncio, asyncpg, os
SQL = """
SELECT t.traveler_id, t.email
  FROM crm.traveler t
"""
async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    print(await conn.fetch(SQL))
    print(await conn.fetchval("SELECT count(*) FROM " + "crm.traveler"))
asyncio.run(main())
'''
SAFE_SCRIPT = '''
import asyncio, asyncpg, os
async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    n = await conn.fetchval("SELECT count(*) FILTER (WHERE " + "email IS NULL) FROM crm.traveler")
    print(f"SCRIPT missing={n}")
asyncio.run(main())
'''


def bash(command, cwd):
    return {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd}


class StatementTest(unittest.TestCase):
    def test_refused(self):
        for sql in REFUSED:
            with self.subTest(sql=sql):
                self.assertTrue(g.text_reads(sql, PROTECTED, python=False), sql)

    def test_allowed(self):
        for sql in ALLOWED:
            with self.subTest(sql=sql):
                self.assertEqual(g.text_reads(sql, PROTECTED, python=False), [], sql)

    def test_python_strings_are_joined(self):
        self.assertEqual(g.text_reads(SCRIPT, PROTECTED, python=True), ["crm.traveler.email"])
        self.assertEqual(g.text_reads(SAFE_SCRIPT, PROTECTED, python=True), [])
        joined = 'q = "SELECT t.email " + "FROM crm.traveler t"\n'
        self.assertEqual(g.text_reads(joined, PROTECTED, python=True), ["crm.traveler.email"])


class CommandTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="l1-aa969-hook-")
        Path(self.tmp, "leak.py").write_text(SCRIPT)
        Path(self.tmp, "safe.py").write_text(SAFE_SCRIPT)

    def refused(self, command):
        return g.check(bash(command, self.tmp), PROTECTED)

    def test_s3_upload_of_an_ecs_exec_script(self):
        cp = "aws s3 cp {} s3://aa-cis-bronze-example/scripts/x.py --profile aa365-admin --region us-west-1"
        self.assertIn("leak.py: crm.traveler.email", self.refused(cp.format("leak.py")))
        self.assertIsNone(self.refused(cp.format("safe.py")))
        self.assertIsNone(self.refused(cp.format("missing.py")))           # nothing to read: passes

    def test_ecsx_wrapper(self):
        self.assertIsNotNone(self.refused(f"tools/ecs/ecsx.sh {self.tmp}/leak.py ACTION=read"))
        self.assertIsNone(self.refused(f"bash tools/ecs/ecsx.sh {self.tmp}/safe.py"))

    def test_inline_ecs_exec_and_psql(self):
        ex = ('aws ecs execute-command --cluster c --task t --container api --interactive --command '
              '"python3 -c \\"print(1)\\" ; psql -c \'SELECT email FROM crm.traveler\'"')
        self.assertIsNotNone(self.refused(ex))
        self.assertIsNotNone(self.refused("psql -h h -c 'SELECT t.email FROM crm.traveler t'"))
        self.assertIsNone(self.refused("psql -h h -c 'SELECT count(*) FROM crm.traveler'"))

    def test_run_script_dispatch_reads_the_infra_file(self):
        infra = Path(self.tmp, "infra/AA-CIS-Infra/db/scripts")
        infra.mkdir(parents=True)
        (infra / "aa969_leak.py").write_text(SCRIPT.replace("asyncio.run(main())", ""))
        old = g.INFRA
        g.INFRA = Path(self.tmp, "infra/AA-CIS-Infra")
        try:
            msg = self.refused("gh workflow run db-migrate.yml -f mode=run-script -f script=db/scripts/aa969_leak.py")
            self.assertIn("AA-CIS-Infra db/scripts/aa969_leak.py: crm.traveler.email", msg)
            self.assertIsNotNone(self.refused("tools/github/dbmig.sh run-script:db/scripts/aa969_leak.py"))
        finally:
            g.INFRA = old

    def test_other_commands_pass(self):
        for cmd in ("git status", f"cat {self.tmp}/leak.py", f"python3 {self.tmp}/leak.py",
                    "aws s3 cp s3://b/k ./local.py", "grep -rn 'SELECT email FROM crm.traveler' ."):
            with self.subTest(cmd=cmd):
                self.assertIsNone(self.refused(cmd))
        self.assertIsNone(g.check({"tool_name": "Edit", "tool_input": {"file_path": "x"}}, PROTECTED))

    def test_the_hook_script_exits_2_with_a_message(self):
        hook = HERE / "pilot-pii-guard.sh"
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(HERE.parents[1]))
        # the real schema reference: crm.traveler keeps its e-mail in email_enc (pii:contact)
        Path(self.tmp, "real.py").write_text('SQL = "SELECT t.email_enc FROM crm.traveler t"\n')
        data = json.dumps(bash(f"aws s3 cp {self.tmp}/real.py s3://bucket/scripts/x.py", self.tmp))
        out = subprocess.run(["bash", str(hook)], input=data, capture_output=True, text=True, env=env)
        self.assertEqual(out.returncode, 2, out.stderr)
        self.assertIn("BLOCKED by the pilot PII guard", out.stderr)
        ok = subprocess.run(["bash", str(hook)], input=json.dumps(bash("git status", self.tmp)), capture_output=True,
                            text=True, env=env)
        self.assertEqual(ok.returncode, 0)
        bad = subprocess.run(["bash", str(hook)], input="not json", capture_output=True, text=True, env=env)
        self.assertEqual(bad.returncode, 0)


class ReferenceTest(unittest.TestCase):
    """The live schema reference gives the scope the rule promises."""

    def test_scope_of_the_reference(self):
        protected = g.load_protected(g.REFERENCE.read_text(encoding="utf-8"))
        self.assertIn(("crm", "traveler"), protected)
        self.assertIn("billing_email", protected[("shared", "tenants")])
        self.assertNotIn(("shared", "admin_users"), protected)               # staff, no tenant_id
        self.assertNotIn(("booking", "staff_users"), protected)              # the AA staff directory
        self.assertIn(("booking", "customers"), protected)
        self.assertTrue(all(s in ("crm", "booking", "tripplanner", "shared") for s, _ in protected))


if __name__ == "__main__":
    unittest.main()
