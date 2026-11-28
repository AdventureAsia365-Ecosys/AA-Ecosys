"""tools/security/dsn_new_password.py (AA-1182): new password, everything else kept, nothing echoed. Invented DSNs."""
import io
import sys
import unittest
import urllib.parse
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dsn_new_password as tool  # noqa: E402

OLD = "old-" + "value-" + "123"
DSN = f"postgresql://booking:{OLD}@db.example.internal:5432/sample_db?sslmode=require"


class RotateTest(unittest.TestCase):
    def test_only_the_password_changes(self):
        new = tool.rotate(DSN + "\n")
        parsed = urllib.parse.urlparse(new)
        self.assertEqual((parsed.username, parsed.hostname, parsed.port, parsed.path, parsed.query),
                         ("booking", "db.example.internal", 5432, "/sample_db", "sslmode=require"))
        self.assertNotEqual(parsed.password, OLD)
        self.assertEqual(len(parsed.password), tool.LENGTH)
        self.assertTrue(parsed.password.isalnum())
        self.assertNotEqual(tool.rotate(DSN), tool.rotate(DSN))       # random every time

    def test_a_dsn_without_a_password_gets_one(self):
        self.assertEqual(tool.rotate("postgresql://crm_app@db.example.internal/sample_db", "x" * 40),
                         "postgresql://crm_app:" + "x" * 40 + "@db.example.internal/sample_db")

    def test_refusals_never_echo_the_input(self):
        for bad in ("mysql://u:" + OLD + "@h/db", "postgresql://h/db", "postgresql://u:" + OLD + "@@h/db",
                    "postgresql://:" + OLD + "@h/db", "not a url " + OLD):
            with self.subTest(bad=bad[:12]):
                with self.assertRaises(ValueError) as ctx:
                    tool.rotate(bad)
                self.assertNotIn(OLD, str(ctx.exception))

    def test_main_pipes_stdin_to_stdout_and_errors_go_to_stderr_only(self):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO(DSN)), redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(tool.main(), 0)
        self.assertTrue(out.getvalue().startswith("postgresql://booking:") and OLD not in out.getvalue())
        self.assertEqual(err.getvalue(), "")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO("mysql://u:" + OLD + "@h/db")), redirect_stdout(out), \
                redirect_stderr(err):
            self.assertEqual(tool.main(), 1)
        self.assertEqual(out.getvalue(), "")
        self.assertNotIn(OLD, err.getvalue())


if __name__ == "__main__":
    unittest.main()
