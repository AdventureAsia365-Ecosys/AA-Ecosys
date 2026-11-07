"""The PR body rule of .github/workflows/pr-title.yml runs as written and agrees with the PR opener (AA-1024 G11).

The workflow step is plain Python (shell: python3 {0}); this test runs that exact text with the env CI gives it, so a
broken edit fails here and not on the next PR. The same step text is copied into the five child repos' pr-title.yml.
Offline, invented issue numbers. Run: python -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

import ship_open_prs as sop

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "pr-title.yml"
STEP = "Linear ids only on the Refs line, no closing keywords"


def body_step() -> dict:
    jobs = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    for job in jobs.values():
        for step in job["steps"]:
            if step.get("name") == STEP:
                return step
    raise AssertionError(f"no step {STEP!r} in {WORKFLOW}")


def run_step(body: str, author: str = "aa-agent[bot]", head: str = "chore/aa-9001-lantern") -> int:
    step = body_step()
    env = {k: v for k, v in os.environ.items() if not k.startswith(("BODY", "HEAD_REF", "AUTHOR"))}
    env.update(BODY=body, HEAD_REF=head, AUTHOR=author)
    return subprocess.run([sys.executable, "-c", step["run"]], env=env, capture_output=True, text=True).returncode


class PrTitleBodyRuleTest(unittest.TestCase):
    def test_step_is_python_with_the_login_not_the_user_type(self):
        step = body_step()
        self.assertEqual(step["shell"], "python3 {0}")
        self.assertIn("user.login", step["env"]["AUTHOR"])
        self.assertFalse(any("user.type" in str(v) for v in step["env"].values()))

    def test_orchestrator_app_prs_are_checked(self):
        # aa-agent[bot] is a Bot to the GitHub API; exempting by type skipped every orchestrator PR
        self.assertEqual(run_step("Joins the AA-9002 lane.\n\nRefs AA-9001\n"), 1)
        self.assertEqual(run_step("AA-9001 lantern retirement, catalogue side.\r\n\r\nRefs AA-9001\r\n"), 0)
        self.assertEqual(run_step("Notes: docs/implementation-notes/AA-9003-lantern-l2.md\n\nRefs AA-9001\n"), 0)

    def test_generated_bot_bodies_skip_only_the_id_rule(self):
        cites = "Bumps lantern from 1 to 2 (see AA-9002).\n"
        self.assertEqual(run_step(cites, author="dependabot[bot]"), 0)
        self.assertEqual(run_step(cites, author="aa-ecosys-ci-bot[bot]", head="release-please--branches--main"), 0)
        self.assertEqual(run_step(cites, author="aa-ecosys-ci-bot[bot]", head="bot/db-schema-reference"), 0)
        self.assertEqual(run_step("Fixes AA-9002\n", author="dependabot[bot]"), 1)

    def test_closing_keywords_fail(self):
        for body in ("Fixes AA-9001", "closes: AA-9001", "Resolved AA-9001", "completing AA-9001"):
            self.assertEqual(run_step(body + "\n\nRefs AA-9001\n"), 1, body)
        self.assertEqual(run_step("Prefixes AA-9001 nothing\n\nRefs AA-9001\n"), 0)

    def test_same_verdict_as_the_pr_opener(self):
        bodies = [
            "x\nRefs AA-1, AA-2\n",
            "see AA-3 and AA-3\nRefs AA-1",
            "Refs AA-1 (and AA-4 later)",
            "AA-9005. Then docs/x/AA-9001.md\nRefs AA-9001",
            "Own AA-7 in prose, tools/x/AA-8-notes.md\n\nRefs AA-7\n",
            "  Refs AA-5 , AA-6  \nBoth AA-5 and AA-6 move.\n",
        ]
        for body in bodies:
            self.assertEqual(run_step(body) == 0, sop.stray_issue_ids(body) == [], body)


if __name__ == "__main__":
    unittest.main()
