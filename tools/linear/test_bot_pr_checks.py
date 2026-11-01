"""Unit tests for bot_pr_checks.py (S263, AA-896 lane plan-sync): the merge gate of the Plan sync bot PR.

Run: python3 -m unittest discover -s tools/linear -p 'test_*.py'   (stdlib only, no network)
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bot_pr_checks as bpc  # noqa: E402

REQUIRED = ["Docs lint", "gitleaks"]


def run(name, status="completed", conclusion="success"):
    return {"name": name, "status": status, "conclusion": conclusion if status == "completed" else None}


class VerdictTest(unittest.TestCase):
    def test_green_when_both_named_checks_passed(self):
        runs = [run("Docs lint"), run("gitleaks"), run("Docs freshness report", conclusion="skipped")]
        self.assertEqual(bpc.checks_verdict(runs, REQUIRED), (0, "green: Docs lint, gitleaks"))

    def test_no_runs_yet_is_pending_not_green(self):
        # The case `gh pr checks --required` got wrong: nothing to wait for must never read as green.
        rc, verdict = bpc.checks_verdict([], REQUIRED)
        self.assertEqual(rc, 2)
        self.assertIn("not reported yet", verdict)

    def test_missing_required_check_is_pending(self):
        rc, verdict = bpc.checks_verdict([run("Docs lint")], REQUIRED)
        self.assertEqual(rc, 2)
        self.assertIn("gitleaks", verdict)

    def test_running_check_is_pending(self):
        rc, verdict = bpc.checks_verdict([run("Docs lint"), run("gitleaks", status="in_progress")], REQUIRED)
        self.assertEqual((rc, verdict), (2, "pending: gitleaks"))

    def test_any_red_run_blocks(self):
        runs = [run("Docs lint"), run("gitleaks"), run("Contracts", conclusion="failure")]
        self.assertEqual(bpc.checks_verdict(runs, REQUIRED), (1, "red check(s): Contracts"))
        self.assertEqual(bpc.checks_verdict([run("Docs lint", conclusion="cancelled"), run("gitleaks")],
                                            REQUIRED)[0], 1)

    def test_required_check_that_only_skipped_blocks(self):
        rc, verdict = bpc.checks_verdict([run("Docs lint", conclusion="skipped"), run("gitleaks")], REQUIRED)
        self.assertEqual(rc, 1)
        self.assertIn("Docs lint", verdict)

    def test_rerun_with_one_success_counts(self):
        runs = [run("Docs lint", conclusion="skipped"), run("Docs lint"), run("gitleaks")]
        self.assertEqual(bpc.checks_verdict(runs, REQUIRED)[0], 0)

    def test_empty_required_list_refuses(self):
        self.assertEqual(bpc.checks_verdict([run("Docs lint")], [])[0], 1)


class CliTest(unittest.TestCase):
    def test_reads_check_runs_json_from_stdin(self):
        payload = json.dumps({"total_count": 2, "check_runs": [run("Docs lint"), run("gitleaks")]})
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(payload)), contextlib.redirect_stdout(out):
            rc = bpc.main(["--required", " Docs lint , gitleaks "])
        self.assertEqual(rc, 0)
        self.assertEqual(out.getvalue().strip().splitlines()[-1], "green: Docs lint, gitleaks")


if __name__ == "__main__":
    unittest.main()
