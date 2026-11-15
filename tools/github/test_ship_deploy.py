"""Tests for ship_deploy.py (AA-1048): deploy paths per service and the ECS exec guard. Offline: gh/aws scripted.

Run: python -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import ship_common
import ship_deploy
from ship_common import Result, ShipError
from ship_fakes import FakeRunner

# The drift test runs real `git -C <clone>`; a pre-push hook exports GIT_DIR and friends, which would point it at the
# root repo instead. Drop git's repo-local variables (`git rev-parse --local-env-vars`; test_git_env_isolation.py).
for _git_var in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR"):
    os.environ.pop(_git_var, None)

FILES_JQ = "[.[] | .filename, (.previous_filename // empty)]"


def js(obj) -> Result:
    return Result(0, json.dumps(obj))


def iso(t: float) -> str:
    return datetime.fromtimestamp(t, tz=timezone.utc).isoformat()


class PathsTest(unittest.TestCase):
    def test_globs_follow_github_order_and_negation(self):
        p = ("api/**", "!api/tests/**", "!api/pyproject.toml", ".github/workflows/deploy-dev.yml")
        self.assertTrue(ship_deploy.path_matches(p, "api/app/main.py"))
        self.assertFalse(ship_deploy.path_matches(p, "api/tests/unit/test_x.py"))
        self.assertFalse(ship_deploy.path_matches(p, "api/pyproject.toml"))
        self.assertTrue(ship_deploy.path_matches(p, ".github/workflows/deploy-dev.yml"))
        self.assertFalse(ship_deploy.path_matches(p, "apix/main.py"))
        self.assertFalse(ship_deploy.path_matches(p, "docs/api/x.md"))
        q = ("frontend/**", "!frontend/**/*.test.mjs")
        self.assertFalse(ship_deploy.path_matches(q, "frontend/lib/a.test.mjs"))
        self.assertFalse(ship_deploy.path_matches(q, "frontend/a.test.mjs"))
        self.assertTrue(ship_deploy.path_matches(q, "frontend/lib/a.mjs"))

    def test_touched_services_per_repo(self):
        names = lambda repo, files: [s.name for s in ship_deploy.touched_services(repo, files)]  # noqa: E731
        self.assertEqual(names("AA-Partner", ["web/app/page.tsx"]), ["web"])
        self.assertEqual(names("AA-Partner", ["api/app/x.py"]), ["api"])
        self.assertEqual(names("AA-Partner", ["api/app/x.py", "web/lib/y.ts"]), ["api", "web"])
        self.assertEqual(names("AA-Partner", ["docs/x.md", "api/migrations/050_x.sql", "web/tests/a.spec.ts"]), [])
        self.assertEqual(names("AA-CIS-App", ["api/version.py", "CHANGELOG.md"]), [])  # release PR: no restart
        self.assertEqual(names("AA-CIS-App", ["requirements.txt"]), ["api"])
        self.assertEqual(names("AA-CIS-App", ["frontend/app/page.tsx"]), ["admin"])
        self.assertEqual(names("AA-Booking", ["backend/app/x.py", "frontend/e2e/smoke.spec.ts"]), ["api"])
        self.assertEqual(names("AA-TripPlanner-Web", ["backend/x.py"]), [])

    def test_running_sha_reads_both_shapes(self):
        self.assertEqual(ship_deploy.running_sha({"git_sha": "abc"}), "abc")
        self.assertEqual(ship_deploy.running_sha({"sha": "def"}), "def")
        self.assertEqual(ship_deploy.running_sha(None), "")

    def test_changed_files_reads_paged_lists_and_old_names(self):
        r = FakeRunner().on(("--paginate",), Result(0, '["web/a.ts", "api/old.py"]\n["docs/b.md"]\n'))
        self.assertEqual(ship_deploy.changed_files(r, "AA-Partner", 9), ["web/a.ts", "api/old.py", "docs/b.md"])
        self.assertIn(f"repos/{ship_common.ORG}/AA-Partner/pulls/9/files?per_page=100", r.calls[0])
        bad = FakeRunner().on(("--paginate",), Result(1, "", "HTTP 404"))
        with self.assertRaises(ShipError):
            ship_deploy.changed_files(bad, "AA-Partner", 9)


def _workflow_push_paths(text: str) -> list[str]:
    """on.push.paths of a workflow file (no YAML library: the block under `push:` -> `paths:`)."""
    lines = text.splitlines()
    out: list[str] = []
    in_push = in_paths = False
    for line in lines:
        if line.strip() == "push:":
            in_push = True
            continue
        if in_push and line.strip() == "paths:":
            in_paths = True
            continue
        if in_paths:
            s = line.strip()
            if s.startswith("- "):
                out.append(s[2:].strip().strip("'\""))
                continue
            if s.startswith("#") or not s:
                continue
            break
        if in_push and line and not line.startswith(" " * 4):
            in_push = False
    return out


class WorkflowDriftTest(unittest.TestCase):
    """SERVICES mirrors each deploy workflow's push paths: compare with origin/main of the local app clones."""

    def test_paths_match_the_deploy_workflows(self):
        checked = 0
        for s in ship_deploy.SERVICES:
            clone = ship_common.local_checkout(s.repo)
            if not (clone / ".git").exists():
                continue
            p = subprocess.run(["git", "-C", str(clone), "show", f"origin/main:{s.workflow}"], capture_output=True,
                               text=True, stdin=subprocess.DEVNULL)
            if p.returncode != 0:
                continue
            self.assertEqual(tuple(_workflow_push_paths(p.stdout)), s.paths,
                             f"{s.repo} {s.workflow}: on.push.paths changed; update ship_deploy.SERVICES")
            checked += 1
        if not checked:
            self.skipTest("no local app clone (CI): drift check runs on the orchestrator workstation")

    def test_parser_reads_a_paths_block(self):
        text = ("on:\n  push:\n    branches: [main]\n    paths:\n      - \"web/**\"\n      # note\n"
                "      - '!web/tests/**'\n  workflow_dispatch:\n")
        self.assertEqual(_workflow_push_paths(text), ["web/**", "!web/tests/**"])


class ListingTest(unittest.TestCase):
    NOW = 1_793_000_000.0

    def test_fresh_stale_done(self):
        objs = [
            {"Key": "scripts/out/run-a.txt.running", "LastModified": iso(self.NOW - 20)},  # fresh
            {"Key": "scripts/out/run-b.txt.running", "LastModified": iso(self.NOW - 600)},  # stale (died)
            {"Key": "scripts/out/run-c.txt.running", "LastModified": iso(self.NOW - 5)},  # finished
            {"Key": "scripts/out/run-c.txt.done", "LastModified": iso(self.NOW - 4)},
            {"Key": "scripts/out/run-d.txt", "LastModified": iso(self.NOW - 1)},
            {"Key": "scripts/out/run-e.txt.running", "LastModified": "2026-10-26T07:31:30.000Z"},  # 110 s, Z form
        ]
        self.assertEqual(ship_deploy.running_from_listing(objs, self.NOW),
                         [{"run_id": "run-e", "age_s": 110}, {"run_id": "run-a", "age_s": 20}])


class ExecGuardTest(unittest.TestCase):
    def setUp(self):
        self.out = io.StringIO()
        self._redirect = contextlib.redirect_stdout(self.out)
        self._redirect.__enter__()
        self._tmp = tempfile.TemporaryDirectory(prefix="ship-deploy-")
        self.log = Path(self._tmp.name) / "overrides.jsonl"
        self._log = mock.patch.object(ship_deploy, "OVERRIDE_LOG", self.log)
        self._log.start()
        self._env = mock.patch.dict(os.environ, {"ECSX_BUCKET": "demo-scripts-bucket", "ECSX_PROFILE": "demo"})
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._log.stop()
        self._tmp.cleanup()
        self._redirect.__exit__(None, None, None)

    def runner(self, files: list[str], ages: list[int] | None = None, listing: Result | None = None) -> FakeRunner:
        r = FakeRunner()
        r.on(("--paginate", FILES_JQ), js(files))

        def beats(argv):
            return js([{"Key": f"scripts/out/run-{i}.txt.running", "LastModified": iso(r.t - a)}
                       for i, a in enumerate(ages or [])])

        r.on(("s3api", "list-objects-v2"), listing or beats)
        return r

    def test_fresh_heartbeat_refuses_a_backend_pr(self):
        r = self.runner(["api/routers/x.py"], ages=[45])
        with self.assertRaises(ShipError) as cm:
            ship_deploy.exec_guard(r, "AA-CIS-App", 7)
        self.assertEqual(cm.exception.code, 4)
        self.assertIn("run-0 (heartbeat 45s ago)", str(cm.exception))
        self.assertIn("--allow-running-exec", str(cm.exception))
        argv = r.called("s3api")[0]
        self.assertEqual(argv[argv.index("--bucket") + 1], "demo-scripts-bucket")
        self.assertEqual(argv[argv.index("--profile") + 1], "demo")
        self.assertFalse(self.log.exists())

    def test_stale_heartbeat_passes(self):
        r = self.runner(["api/routers/x.py"], ages=[ship_deploy.FRESH_S + 60])
        ship_deploy.exec_guard(r, "AA-CIS-App", 7)

    def test_override_passes_and_is_logged(self):
        r = self.runner(["shared/jobs/x.py"], ages=[10])
        ship_deploy.exec_guard(r, "AA-CIS-App", 7, allow=True)
        self.assertIn("WARN AA-CIS-App#7: --allow-running-exec (tech lead's call)", self.out.getvalue())
        row = json.loads(self.log.read_text().splitlines()[0])
        self.assertEqual((row["pr"], row["flag"]), ("AA-CIS-App#7", "--allow-running-exec"))
        self.assertIn("run-0", row["what"])

    def test_frontend_or_docs_pr_does_not_read_heartbeats(self):
        for files in (["frontend/app/page.tsx"], ["docs/x.md", "api/migrations/430_x.sql"]):
            r = self.runner(files, ages=[5])
            ship_deploy.exec_guard(r, "AA-CIS-App", 7)
            self.assertEqual(r.called("s3api"), [])

    def test_other_repos_are_not_checked(self):
        r = FakeRunner()  # any call would fail the test
        for repo in ("AA-Booking", "AA-Partner", "AA-Ecosys", "AA-CIS-Infra", "AA-TripPlanner-Web"):
            ship_deploy.exec_guard(r, repo, 7)
        self.assertEqual(r.calls, [])

    def test_unreadable_listing_refuses_unless_overridden(self):
        r = self.runner(["api/x.py"], listing=Result(255, "", "Token has expired and refresh failed"))
        with self.assertRaises(ShipError) as cm:
            ship_deploy.exec_guard(r, "AA-CIS-App", 7)
        self.assertIn("cannot read the ECS exec heartbeats", str(cm.exception))
        self.assertIn("aws sts get-caller-identity --profile demo", str(cm.exception))
        ship_deploy.exec_guard(r, "AA-CIS-App", 7, allow=True)
        self.assertTrue(self.log.exists())

    def test_unreadable_file_list_counts_as_backend(self):
        r = FakeRunner()
        r.on(("--paginate",), Result(1, "", "HTTP 502"))
        r.on(("s3api",), js([{"Key": "scripts/out/run-x.txt.running", "LastModified": iso(r.t - 1)}]))
        with self.assertRaises(ShipError):
            ship_deploy.exec_guard(r, "AA-CIS-App", 7)

    def test_empty_listing_passes(self):
        r = self.runner(["api/x.py"], listing=Result(0, "null\n"))
        ship_deploy.exec_guard(r, "AA-CIS-App", 7)

    def test_bucket_default_comes_from_ecsx_sh(self):
        with mock.patch.dict(os.environ, {"ECSX_BUCKET": ""}):
            bucket = ship_deploy.exec_bucket()
        self.assertIn(f"${{ECSX_BUCKET:-{bucket}}}", ship_deploy.ECSX_SH.read_text(encoding="utf-8"))


class MergeOneTest(unittest.TestCase):
    """merge_one runs the guard after the gate and before the merge call."""

    def setUp(self):
        self.out = io.StringIO()
        self._redirect = contextlib.redirect_stdout(self.out)
        self._redirect.__enter__()

    def tearDown(self):
        self._redirect.__exit__(None, None, None)

    def test_refusal_happens_before_the_queue(self):
        import ship_merge
        from ship_fakes import pr

        r = FakeRunner()
        r.on(("gh", "pr", "view"), js(pr(7)))
        r.on(("--paginate", FILES_JQ), js(["worker/main.py"]))
        r.on(("--paginate",), Result(0, "[]\n"))
        r.on(("s3api",), lambda argv: js([{"Key": "scripts/out/r.txt.running", "LastModified": iso(r.t - 3)}]))
        with mock.patch.dict(os.environ, {"ECSX_BUCKET": "demo-scripts-bucket"}):
            with self.assertRaises(ShipError) as cm:
                ship_merge.merge_one(r, "AA-CIS-App", 7)
        self.assertEqual(cm.exception.code, 4)
        self.assertEqual(r.called(ship_common.MERGEQ), [])


if __name__ == "__main__":
    unittest.main()
