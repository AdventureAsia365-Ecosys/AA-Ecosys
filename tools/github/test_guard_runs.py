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


def wf_run(event: str, created: str, conclusion: str | None, status: str = "completed", branch: str = "master") -> dict:
    return {"name": "Catalogue", "event": event, "created_at": created, "status": status, "conclusion": conclusion,
            "head_branch": branch, "html_url": f"https://github.com/x/runs/{event}-{created[:13]}"}


def superseding_run(dispatch_runs: dict, sched: dict):
    """gh stub: scheduled runs per repo (sched) and the runs of workflow 41 on the default branch (dispatch_runs)."""
    calls = []

    def run(cmd, **kw):
        calls.append(cmd)
        path, repo = cmd[4], cmd[4].split("/")[2]
        if "/actions/workflows/" in path:
            if repo == "AA-Booking":
                return subprocess.CompletedProcess(cmd, 1, "", "HTTP 502")
            return subprocess.CompletedProcess(cmd, 0, json.dumps(dispatch_runs.get(repo, [])), "")
        return subprocess.CompletedProcess(cmd, 0, json.dumps(sched.get(repo, [])), "")
    return run, calls


class SupersededTest(unittest.TestCase):
    """S294: Catalogue and Image Scan were reported red after a green hand dispatch had already fixed them."""

    def sched(self, repo: str = "AA-Ecosys") -> dict:
        row = run_row("Catalogue", "2026-11-07T02:00:00Z", "failure")
        row["workflow_id"] = 41
        return {repo: [row]}

    def test_a_later_green_dispatch_or_push_supersedes_the_red_scheduled_run(self):
        for event in ("workflow_dispatch", "push"):
            run, calls = superseding_run({"AA-Ecosys": [wf_run(event, "2026-11-07T09:30:00Z", "success"),
                                                        wf_run(event, "2026-11-07T08:00:00Z", "success")]},
                                         self.sched())
            rows, _ = g.collect(8, run, NOW)
            [row] = rows
            self.assertFalse(g.is_red(row), event)
            self.assertEqual(g.label(row), f"superseded (green {event} 2026-11-07T09:30)")
            [lookup] = [c for c in calls if "/actions/workflows/" in c[4]]
            self.assertIn("repos/AdventureAsia365-Ecosys/AA-Ecosys/actions/workflows/41/runs", lookup)
            self.assertIn("branch=master", lookup)  # the root repo's default branch
            out = io.StringIO()
            with mock.patch("sys.stdout", out):
                self.assertEqual(g.main([], run, NOW), 0)
            self.assertIn("0 red of 1", out.getvalue())
            self.assertNotIn("RED ", out.getvalue())
            self.assertIn("superseded (green", out.getvalue())

    def test_older_red_or_other_branch_or_scheduled_runs_do_not_supersede(self):
        cases = [wf_run("workflow_dispatch", "2026-11-06T09:00:00Z", "success"),       # before the red run
                 wf_run("workflow_dispatch", "2026-11-07T09:00:00Z", "failure"),       # later but red
                 wf_run("workflow_dispatch", "2026-11-07T09:00:00Z", None, "in_progress"),
                 wf_run("pull_request", "2026-11-07T09:00:00Z", "success"),            # not dispatch / push
                 wf_run("schedule", "2026-11-07T09:00:00Z", "success"),                # the schedule list decides
                 wf_run("push", "2026-11-07T09:00:00Z", "success", branch="feat/x")]   # not the default branch
        for case in cases:
            run, _ = superseding_run({"AA-Ecosys": [case]}, self.sched())
            rows, _ = g.collect(8, run, NOW)
            self.assertTrue(g.is_red(rows[0]), case)
            self.assertEqual(g.label(rows[0]), "failure")

    def test_a_failed_lookup_leaves_the_row_red_and_json_counts_it(self):
        run, _ = superseding_run({}, self.sched("AA-Booking"))
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            self.assertEqual(g.main(["--json"], run, NOW), 1)
        data = json.loads(out.getvalue())
        self.assertEqual(data["red"], 1)
        self.assertNotIn("superseded", data["rows"][0])

    def test_json_keeps_the_superseding_run(self):
        run, _ = superseding_run({"AA-CIS-App": [wf_run("workflow_dispatch", "2026-11-07T10:00:00Z", "success",
                                                        branch="main")]}, self.sched("AA-CIS-App"))
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            self.assertEqual(g.main(["--json"], run, NOW), 0)
        data = json.loads(out.getvalue())
        self.assertEqual(data["red"], 0)
        self.assertEqual(data["rows"][0]["superseded"]["event"], "workflow_dispatch")


if __name__ == "__main__":
    unittest.main()
