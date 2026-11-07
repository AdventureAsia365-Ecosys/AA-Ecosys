"""Tests for guard_runs.py (AA-1024 G14). Offline: gh is a stub. Run: python3 -m unittest discover -s tools/github"""
from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guard_runs as g  # noqa: E402

NOW = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)


def run_row(name: str, created: str, conclusion: str | None, status: str = "completed") -> dict:
    return {"name": name, "created_at": created, "status": status, "conclusion": conclusion,
            "html_url": f"https://github.com/x/runs/{abs(hash((name, created))) % 1000}"}


RUNS = {
    "AA-Ecosys": [run_row("Secret scan (history)", "2026-11-07T02:00:00Z", "failure"),
                  run_row("Secret scan (history)", "2026-11-06T02:00:00Z", "success"),
                  run_row("Docs lint", "2026-11-02T01:17:00Z", "success")],
    "AA-CIS-App": [run_row("Nightly integration (random order)", "2026-11-07T03:00:00Z", None, "in_progress"),
                   run_row("Nightly integration (random order)", "2026-11-06T03:00:00Z", "failure"),
                   run_row("Old weekly thing", "2026-10-01T03:00:00Z", "failure")],
}


def fake_run(cmd, **kw):
    repo = cmd[4].split("/")[2]
    if repo == "AA-Partner":
        return subprocess.CompletedProcess(cmd, 1, "", "HTTP 502")
    return subprocess.CompletedProcess(cmd, 0, json.dumps(RUNS.get(repo, [])), "")


class GuardRunsTest(unittest.TestCase):
    def test_latest_per_workflow_red_first(self):
        rows, unreadable = g.collect(8, fake_run, NOW)
        self.assertEqual(unreadable, ["AA-Partner"])
        self.assertEqual([(r["repo"], r["workflow"], g.label(r)) for r in rows], [
            ("AA-Ecosys", "Secret scan (history)", "failure"),
            ("AA-CIS-App", "Nightly integration (random order)", "in_progress"),
            ("AA-Ecosys", "Docs lint", "success"),
        ])  # the 06/11 failure is superseded by the newer run; the October run is outside the window

    def test_main_exit_codes(self):
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            self.assertEqual(g.main([], fake_run, NOW), 1)
        self.assertIn("RED AA-Ecosys", out.getvalue())
        self.assertIn("??? AA-Partner", out.getvalue())

        def green(cmd, **kw):
            return subprocess.CompletedProcess(cmd, 0, json.dumps([run_row("Docs lint", "2026-11-06T00:00:00Z",
                                                                           "success")]), "")
        with mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(g.main(["--json"], green, NOW), 0)


if __name__ == "__main__":
    unittest.main()
