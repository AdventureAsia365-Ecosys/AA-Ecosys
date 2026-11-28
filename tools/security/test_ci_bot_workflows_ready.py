"""AA-1183 part 2: the guard of `ci_bot_key_consolidate.sh cleanup` fails CLOSED. Offline: a fake `gh` (runner or a
stub on PATH); invented repo and workflow names. Run: python3 -m unittest discover -s tools/security -p 'test_*.py'.
"""
from __future__ import annotations

import base64
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ci_bot_workflows_ready as wr  # noqa: E402

HERE = Path(__file__).resolve().parent
KEY = "${{ secrets.AA_CI_BOT_PRIVATE_KEY }}"

GOOD = f"""
name: demo
on: workflow_dispatch
jobs:
  build:
    runs-on: ubuntu-latest
    steps: [{{run: echo hi}}]
  mint:
    runs-on: ubuntu-latest
    environment: ci-bot
    steps:
      - uses: actions/create-github-app-token@v2
        with:
          private-key: {KEY}
"""
OLD_ENV = GOOD.replace("environment: ci-bot", "environment: release")
# One job is in ci-bot, another reads the key without it: a file-level grep passed this.
MIXED = GOOD + f"""
  other:
    runs-on: ubuntu-latest
    steps:
      - run: echo x
        env:
          K: {KEY}
"""
TOP_LEVEL = (f"name: demo\non: push\nenv:\n  K: {KEY}\njobs:\n  a:\n    runs-on: ubuntu-latest\n"
             "    environment: ci-bot\n    steps: [{run: echo}]\n")
REUSABLE = f"name: demo\non: push\njobs:\n  call:\n    uses: ./.github/workflows/x.yml\n    secrets:\n      k: {KEY}\n"


def _b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


class FakeGh:
    def __init__(self, repos: dict, fail: tuple = ()):
        self.repos = repos           # repo -> {path: text}
        self.fail = fail             # substrings of a path that fail
        self.calls = []

    def __call__(self, argv):
        path = argv[-1]
        self.calls.append(path)
        if any(f in path for f in self.fail):
            return 1, "", "gh: API rate limit exceeded (HTTP 403)"
        repo = path.split("/")[2]
        files = self.repos.get(repo, {})
        if "/contents/.github/workflows?" in path:
            return 0, json.dumps([{"type": "file", "name": p.rsplit("/", 1)[1], "path": p} for p in files]
                                 + [{"type": "dir", "name": "sub", "path": ".github/workflows/sub"}]), ""
        p = path.split("/contents/", 1)[1].split("?", 1)[0]
        if p not in files:
            return 1, "", "gh: Not Found (HTTP 404)"
        return 0, json.dumps({"encoding": "base64", "content": _b64(files[p])}), ""


def _check(repos, fail=()):
    gh = FakeGh(repos, fail)
    return wr.check("Demo-Org", [(r, "main") for r in sorted(repos)] or [("Demo-Empty", "main")], gh), gh


class WorkflowsReadyTest(unittest.TestCase):
    def test_all_ci_bot_is_ready(self):
        problems, _ = _check({"Demo-A": {".github/workflows/a.yml": GOOD},
                              "Demo-B": {".github/workflows/b.yaml": "name: x\non: push\njobs: {}\n"}})
        self.assertEqual(problems, [])

    def test_failed_listing_is_not_ready(self):
        problems, gh = _check({"Demo-A": {".github/workflows/a.yml": GOOD}}, fail=("contents/.github/workflows?",))
        self.assertTrue(problems and "cannot read Demo-A workflow list" in problems[0], problems)

    def test_failed_file_read_is_not_ready(self):
        problems, _ = _check({"Demo-A": {".github/workflows/a.yml": GOOD, ".github/workflows/b.yml": GOOD}},
                             fail=("b.yml",))
        self.assertTrue(any("cannot read Demo-A .github/workflows/b.yml" in p for p in problems), problems)

    def test_empty_listing_is_not_ready(self):
        problems, _ = _check({"Demo-A": {}})
        self.assertTrue(any("no workflow file listed" in p for p in problems), problems)

    def test_one_unreadable_repo_does_not_hide_behind_a_good_one(self):
        problems, _ = _check({"Demo-A": {".github/workflows/a.yml": GOOD},
                              "Demo-B": {".github/workflows/b.yml": GOOD}}, fail=("repos/Demo-Org/Demo-B/",))
        self.assertEqual(len(problems), 1)
        self.assertIn("Demo-B", problems[0])

    def test_jobs_outside_ci_bot_are_not_ready(self):
        for text, needle in ((OLD_ENV, "environment 'release'"), (MIXED, "x.yml:other"),
                             (TOP_LEVEL, "outside any job"), (REUSABLE, "reusable workflow"),
                             ("jobs: [unclosed", "not valid YAML"), ("   \n", "empty file")):
            problems = wr.workflow_problems(".github/workflows/x.yml", text)
            self.assertTrue(problems and any(needle in p for p in problems), (needle, problems))
        self.assertEqual(wr.workflow_problems("x.yml", GOOD), [])

    def test_bad_content_is_not_ready(self):
        def runner(argv):
            if "workflows?" in argv[-1]:
                return 0, json.dumps([{"type": "file", "name": "a.yml", "path": ".github/workflows/a.yml"}]), ""
            return 0, json.dumps({"encoding": "none", "content": ""}), ""   # a file too large for inline content
        problems = wr.check("Demo-Org", [("Demo-A", "main")], runner)
        self.assertTrue(problems and "no inline content" in problems[0], problems)

    def test_main_exit_codes(self):
        self.assertEqual(wr.main(["--owner", "Demo-Org", "Demo-A"]), 1)       # bad target


class ConsolidateCleanupGuardTest(unittest.TestCase):
    """The shell `cleanup --apply` refuses, and deletes nothing, when gh cannot list the workflows."""

    def test_cleanup_refuses_when_gh_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "gh.log"
            stub = Path(tmp) / "gh"
            stub.write_text(f'#!/usr/bin/env bash\necho "$*" >> "{log}"\necho "gh: HTTP 503" >&2\nexit 1\n')
            stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
            env = {**os.environ, "PATH": f"{tmp}:{os.environ.get('PATH', '')}"}
            proc = subprocess.run(["bash", str(HERE / "ci_bot_key_consolidate.sh"), "cleanup", "--apply"],
                                  capture_output=True, text=True, env=env, timeout=60, stdin=subprocess.DEVNULL)
            self.assertEqual(proc.returncode, 1, proc.stderr)
            # Refused by the workflow guard itself (the old shell guard passed here and only a later check stopped it).
            self.assertIn("cleanup refused: merge the workflow PRs first", proc.stderr)
            self.assertIn("not ready: cannot read AA-Ecosys workflow list", proc.stderr)
            calls = log.read_text() if log.exists() else ""
            self.assertNotIn("delete", calls)
            self.assertNotIn("DELETE", calls)


if __name__ == "__main__":
    unittest.main()
