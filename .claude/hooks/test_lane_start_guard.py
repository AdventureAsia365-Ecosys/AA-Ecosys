"""Tests for lane_start_guard.py (AA-1024 G12). Run: python3 .claude/hooks/test_lane_start_guard.py"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lane_start_guard as g  # noqa: E402

LANE = "/home/someone/projects/AA-Ecosys/tools/workflows/lane.js"


def args(**kw) -> dict:
    base = {"key": "l1-demo", "goal": "AA-900: build the demo slice", "session": "S271", "date": "07/11/2026"}
    base.update(kw)
    return base


class LaneStartGuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs/backlog/tracker").mkdir(parents=True)
        self.plan({"session": "S271", "issues": [{"id": "AA-900", "session": "S271"},
                                                  {"id": "AA-741", "session": "S271–S272"},
                                                  {"id": "AA-1024", "session": "≥10/11"}]})

    def tearDown(self):
        self.tmp.cleanup()

    def plan(self, data: dict) -> None:
        (self.root / g.PLAN).write_text(json.dumps(data), encoding="utf-8")

    def check(self, tool_input: dict, avail_mib: int = 8000) -> str | None:
        proc = self.root / "proc"
        proc.mkdir(exist_ok=True)
        (proc / "meminfo").write_text(f"MemAvailable: {avail_mib * 1024} kB\n")
        return g.check(tool_input, self.root, proc)

    def test_up_to_date_plan_passes(self):
        self.assertIsNone(self.check({"scriptPath": LANE, "args": args()}))
        # A JSON-encoded object is parsed by the harness: it passes like the object.
        self.assertIsNone(self.check({"scriptPath": LANE, "args": json.dumps(args())}))
        self.assertIsNone(self.check({"scriptPath": LANE, "args": args(goal="AA-741 part 2")}))
        self.assertIsNone(self.check({"scriptPath": LANE, "args": args(goal="AA-1099 not in the tracker")}))
        self.assertIsNone(self.check({"scriptPath": LANE, "args": args(goal="no issue id: docs sweep")}))

    def test_plan_still_on_previous_session_is_refused(self):
        self.plan({"session": "S270", "issues": []})
        msg = self.check({"scriptPath": LANE, "args": args()})
        self.assertIn("session='S270'", msg)
        self.assertIn("republish the tracker", msg)

    def test_issue_not_slotted_for_this_session_is_refused(self):
        msg = self.check({"scriptPath": LANE, "args": args(goal="AA-1024: guards")})
        self.assertIn("AA-1024 is slotted for '≥10/11'", msg)

    def test_placeholder_or_incomplete_args_are_refused(self):
        self.assertIn("not a JSON object", self.check({"scriptPath": LANE, "args": "__FROM_FILE__"}))
        self.assertIn("not a JSON object", self.check({"scriptPath": LANE, "args": "[1, 2]"}))
        self.assertIn("got missing", self.check({"scriptPath": LANE}))
        self.assertIn("got list", self.check({"scriptPath": LANE, "args": [1]}))
        self.assertIn("lack session", self.check({"scriptPath": LANE, "args": args(session="")}))

    def test_skip_with_reason_passes_and_is_logged(self):
        self.plan({"session": "S270", "issues": []})
        self.assertIsNone(self.check({"scriptPath": LANE, "args": args(plan_gate="skip: prod hotfix")}))
        self.assertIn("prod hotfix", (self.root / g.HITS_LOG).read_text())
        self.assertIsNotNone(self.check({"scriptPath": LANE, "args": args(plan_gate="skip:")}))

    def test_low_memory_refuses_a_new_lane(self):
        msg = self.check({"scriptPath": LANE, "args": args()}, avail_mib=3000)
        self.assertIn("MemAvailable is 3000 MiB", msg)
        self.assertIsNone(self.check({"scriptPath": LANE, "args": args(ram_gate="skip: last small lane")},
                                     avail_mib=3000))
        self.assertIsNone(self.check({"scriptPath": "/x/tools/workflows/review.js", "args": {}}, avail_mib=100))

    def test_existing_worktree_needs_resume(self):
        wt = self.root / ".tmp-session/wt/s271-l1-demo-cis"
        wt.mkdir(parents=True)
        (self.root / ".tmp-session/wt/s271-l10-other-root").mkdir()
        msg = self.check({"scriptPath": LANE, "args": args()})
        self.assertIn("already exist", msg)
        self.assertIn("s271-l1-demo-cis", msg)
        self.assertNotIn("l10-other", msg)
        self.assertIsNone(self.check({"scriptPath": LANE, "args": args(resume=True)}))
        self.assertIsNotNone(self.check({"scriptPath": LANE, "args": args(resume="yes")}))
        self.assertIsNone(self.check({"scriptPath": LANE, "args": args(key="l2-new")}))

    def test_other_workflows_and_unreadable_plan(self):
        self.assertIsNone(self.check({"script": "export const meta = {name: 'audit'}", "args": "x"}))
        self.assertIsNone(self.check({"scriptPath": "/x/tools/workflows/review.js", "args": None}))
        self.assertIsNotNone(self.check({"name": "aa-lane", "args": "x"}))
        (self.root / g.PLAN).write_text("{not json")
        self.assertIn("cannot read", self.check({"scriptPath": LANE, "args": args()}))

    def test_hook_exit_codes(self):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.root))
        sh = HERE / "lane-start-guard.sh"
        self.assertTrue(os.access(sh, os.X_OK))

        def run(payload: str) -> int:
            return subprocess.run([str(sh)], input=payload, text=True, capture_output=True, env=env,
                                  timeout=30).returncode

        # Exit 0 on a launch that is not gated (a lane launch would also read the real /proc memory here).
        self.assertEqual(run(json.dumps({"tool_name": "Workflow", "tool_input": {"scriptPath": "/x/review.js",
                                                                                 "args": args()}})), 0)
        self.assertEqual(run(json.dumps({"tool_name": "Workflow", "tool_input": {"scriptPath": LANE,
                                                                                 "args": "{}"}})), 2)
        self.assertEqual(run("not json"), 0)


if __name__ == "__main__":
    unittest.main()
