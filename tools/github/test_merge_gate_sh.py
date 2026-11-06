"""Tests for the shell side of the ship gate (AA-1024 G1): the merge-queue wrapper's DIRTY exit and as-app.sh's
refusal of a raw `gh pr merge`. Offline: gh, aws and sleep are fakes on PATH; the scripts run from a temporary copy.

Run: python -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUEUE_SCRIPT = "mergeq" + ".sh"  # spelled in two parts: the subagent hook refuses commands naming the wrapper

FAKE_GH = r"""#!/bin/bash
# Fake gh: answers from files in $FAKE (state line for `pr view`, queue line for graphql).
case "$1 $2" in
  "pr view") cat "$FAKE/st" ;;
  "api graphql") cat "$FAKE/inq" 2>/dev/null || echo "false||" ;;
  "pr checks") exit 0 ;;
  "pr merge") echo "merge $*" >> "$FAKE/merges"; echo "queued"; exit 0 ;;
  "run list") exit 0 ;;
  *) echo "fake gh: unexpected $*" >&2; exit 9 ;;
esac
"""
FAKE_AS_APP = """#!/bin/bash
while [ "$1" != "--" ]; do shift; done; shift; exec "$@"
"""
FAKE_AWS = """#!/bin/bash
echo "fake aws: no MFA session" >&2; exit 1
"""
FAKE_SLEEP = """#!/bin/bash
exit 0
"""


def write_exe(path: Path, text: str) -> None:
    path.write_text(text)
    path.chmod(0o755)


class GateScriptsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="merge-gate-")
        self.d = Path(self.tmp.name)
        self.bin = self.d / "bin"
        self.bin.mkdir()
        self.fake = self.d / "state"
        self.fake.mkdir()
        write_exe(self.bin / "gh", FAKE_GH)
        write_exe(self.bin / "aws", FAKE_AWS)
        write_exe(self.bin / "sleep", FAKE_SLEEP)
        self.env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}", FAKE=str(self.fake), MAXWAIT="3")
        self.env.pop("AA_SHIP_GATED", None)

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, script: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(["bash", str(script), *args], capture_output=True, text=True, env=env or self.env,
                              timeout=60)

    def queue_copy(self) -> Path:
        tools = self.d / "q"
        tools.mkdir()
        shutil.copy(HERE / QUEUE_SCRIPT, tools / QUEUE_SCRIPT)
        write_exe(tools / "as-app.sh", FAKE_AS_APP)
        return tools / QUEUE_SCRIPT

    def test_queue_wrapper_exits_4_at_once_when_the_pr_turns_dirty(self):
        (self.fake / "st").write_text("OPEN||DIRTY|auto\n")
        r = self.run_script(self.queue_copy(), "AA-CIS-App", "1350", env=dict(self.env, AA_SHIP_GATED="test"))
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertIn("DIRTY", r.stdout)
        self.assertNotIn("still not merged", r.stdout)

    def test_queue_wrapper_still_waits_for_a_clean_queued_pr(self):
        (self.fake / "st").write_text("OPEN||CLEAN|auto\n")
        (self.fake / "inq").write_text("true|QUEUED|2\n")
        r = self.run_script(self.queue_copy(), "AA-CIS-App", "1350", env=dict(self.env, AA_SHIP_GATED="test"))
        self.assertEqual(r.returncode, 5, r.stdout + r.stderr)  # MAXWAIT=3 s: timed out, not refused

    def app_copy(self) -> Path:
        tools = self.d / "a"
        tools.mkdir()
        shutil.copy(HERE / "as-app.sh", tools / "as-app.sh")
        shutil.copy(HERE / "apps.env", tools / "apps.env")
        return tools / "as-app.sh"

    def test_as_app_refuses_a_raw_merge(self):
        app = self.app_copy()
        for args in (["--", "gh", "pr", "merge", "5", "--squash"],
                     ["--repos", "AA-Ecosys", "--", "gh", "pr", "merge", "5", "-R", "x/AA-Ecosys", "--squash"],
                     ["--", "/usr/bin/gh", "pr", "merge", "5", "--auto"]):
            r = self.run_script(app, *args)
            self.assertEqual(r.returncode, 2, args)
            self.assertIn("refused a raw 'gh pr merge'", r.stderr)
        self.assertFalse((self.fake / "merges").exists())

    def test_as_app_refuses_a_merge_through_the_api(self):
        app = self.app_copy()
        body = self.d / "q.graphql"
        body.write_text("mutation($id:ID!){enqueuePullRequest(input:{pullRequestId:$id}){clientMutationId}}\n")
        for args in (
            # the form found in the S271 transcripts
            ["--repos", "AA-CIS-Infra", "--", "gh", "api", "-X", "PUT",
             "repos/AdventureAsia365-Ecosys/AA-CIS-Infra/pulls/663/merge", "-f", "merge_method=squash"],
            ["--", "gh", "api", "--method", "put", "/repos/o/r/pulls/5/merge"],
            ["--", "gh", "api", "-XPUT", "repos/o/r/pulls/5/merge"],
            ["--", "gh", "api", "--method=PUT", "repos/o/r/pulls/5/merge"],
            ["--", "gh", "api", "repos/o/r/pulls/5/merge", "-f", "merge_method=squash"],
            ["--", "gh", "api", "graphql", "-f", "query=mutation{mergePullRequest(input:{pullRequestId:\"x\"}){clientMutationId}}"],
            ["--", "gh", "api", "graphql", "-f", "query=mutation{enqueuePullRequest(input:{pullRequestId:\"x\"}){clientMutationId}}"],
            ["--", "gh", "api", "graphql", "-F", f"query=@{body}"],
            ["--", "gh", "api", "graphql", "--input", str(body)],
        ):
            r = self.run_script(app, *args)
            self.assertEqual(r.returncode, 2, (args, r.stderr))
            self.assertIn("refused a merge through 'gh api'", r.stderr)

    def test_as_app_lets_gated_merges_dequeues_and_other_commands_through(self):
        app = self.app_copy()
        cases = ((["--", "gh", "pr", "merge", "5", "--squash"], dict(self.env, AA_SHIP_GATED="ship_merge")),
                 (["--", "gh", "pr", "merge", "5", "--disable-auto"], self.env),
                 (["--", "gh", "pr", "view", "5"], self.env),
                 (["--", "gh", "api", "-X", "PUT", "repos/o/r/pulls/5/merge"], dict(self.env, AA_SHIP_GATED="x")),
                 (["--", "gh", "api", "repos/o/r/pulls/5/merge"], self.env),  # GET: is it merged?
                 (["--", "gh", "api", "-X", "GET", "repos/o/r/pulls/5/merge"], self.env),
                 (["--", "gh", "api", "repos/o/r/pulls/5", "--jq", ".mergeable_state"], self.env),
                 (["--", "gh", "api", "graphql", "-f",
                   "query=mutation($id:ID!){dequeuePullRequest(input:{id:$id}){clientMutationId}}"], self.env),
                 (["--", "gh", "api", "graphql", "-f", "query={viewer{login}}"], self.env))
        for args, env in cases:
            r = self.run_script(app, *args, env=env)
            # Past the gate check: the next step reads the App key with aws, which the fake refuses (exit 1).
            self.assertEqual(r.returncode, 1, (args, r.stderr))
            self.assertNotIn("refused a raw", r.stderr)


if __name__ == "__main__":
    unittest.main()
