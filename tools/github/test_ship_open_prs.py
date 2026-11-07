"""Tests for ship_open_prs.py (AA-1032): journal parsing, PR text guards, push + create through the App.

Real git in a temporary repository; gh and as-app.sh are scripted. Run:
python -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ship_common
import ship_open_prs as sop
from ship_common import Result, ShipError
from ship_fakes import GitSandbox, HybridRunner

# S272: drop git's repo-local variables before any git call in a temporary repo (test_git_env_isolation.py; the
# safe-hooks test below runs git directly, not only through ship_fakes).
for _git_var in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR"):
    os.environ.pop(_git_var, None)

BODY = "## What\n- A small invented change to the lantern catalogue.\n\nRefs AA-9001\n"


def lane_pr(wt: str, **kw) -> dict:
    p = {"repo": "AA-Partner", "worktree": wt, "branch": "feat/lanterns", "base": "main",
         "pr_title": "feat: lantern catalogue sorts by glow", "pr_body": BODY,
         "live_steps": ["curl /crm/health -> git_sha = merge SHA"]}
    p.update(kw)
    return p


def write_journal(path: Path, results: list[dict]) -> None:
    lines = [json.dumps({"type": "launched"})]
    for i, res in enumerate(results):
        lines.append(json.dumps({"type": "started", "key": f"k{i}", "label": f"step:{i}"}))
        lines.append(json.dumps({"type": "result", "key": f"k{i}", "agentId": f"a{i}", "result": res}))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class TextTest(unittest.TestCase):
    def test_add_refs(self):
        self.assertIn("Refs AA-9001, AA-1032\n", sop.add_refs(BODY, ["AA-1032"]))
        self.assertEqual(sop.add_refs(BODY, ["AA-9001"]), BODY)
        self.assertTrue(sop.add_refs("no refs line", ["AA-1"]).endswith("Refs AA-1\n"))
        # an id added to a Refs line with free text goes into the id list, not after the text
        self.assertEqual(sop.add_refs("x\nRefs AA-1 (lane l2)\n", ["AA-2"]), "x\nRefs AA-1, AA-2 (lane l2)\n")

    def test_attribution_is_added_once(self):
        once = sop.with_attribution(BODY)
        self.assertTrue(once.rstrip().endswith(sop.ATTRIBUTION))
        self.assertEqual(sop.with_attribution(once), once)


class JournalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "journal.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def test_last_result_with_prs_wins_and_reviews_are_skipped(self):
        impl = {"ready": True, "prs": [lane_pr("/x", branch="impl")]}
        review = {"verdict": "approve", "findings": []}
        fix = {"ready": True, "prs": [lane_pr("/x", branch="fixed")]}
        write_journal(self.path, [impl, review, review, fix])
        prs, res = sop.load_prs(self.path)
        self.assertEqual([p["branch"] for p in prs], ["fixed"])
        write_journal(self.path, [impl, review, {"ready": True, "prs": []}])
        self.assertEqual(sop.load_prs(self.path)[0][0]["branch"], "impl")
        write_journal(self.path, [review])
        with self.assertRaises(ShipError):
            sop.load_prs(self.path)

    def test_find_journal_by_run_id(self):
        home = Path(self.tmp.name)
        d = home / ".claude/projects/p/s/subagents/workflows/wf_abc-123"
        d.mkdir(parents=True)
        write_journal(d / "journal.jsonl", [{"ready": True, "prs": []}])
        with mock.patch.dict(os.environ, {"HOME": str(home)}):
            self.assertEqual(sop.find_journal("wf_abc-123"), d / "journal.jsonl")
            with self.assertRaises(ShipError):
                sop.find_journal("wf_missing")


class OpenTest(unittest.TestCase):
    def setUp(self):
        self.sb = GitSandbox()
        g, wt = self.sb.git, self.sb.wt
        g(wt, "checkout", "-q", "-b", "feat/lanterns")
        self.sb.commit(wt, "lantern.py", "GLOW = 3\n", "feat: lantern glow")
        self.journal = Path(self.sb.tmp.name) / "journal.jsonl"
        self.tmpdir = mock.patch.object(sop, "ROOT", Path(self.sb.tmp.name))
        self.tmpdir.start()
        self.env = mock.patch.dict(os.environ, {"AA_GITLEAKS": "gitleaks", "AA_SKIP_GITLEAKS": ""})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmpdir.stop()
        self.sb.close()

    def runner(self, existing: str = "") -> tuple[HybridRunner, dict]:
        seen: dict = {}

        def app(argv):
            if "create" in argv:
                seen["title"] = argv[argv.index("--title") + 1]
                seen["body"] = Path(argv[argv.index("--body-file") + 1]).read_text(encoding="utf-8")
                seen["create"] = argv
                return Result(0, "https://github.com/AdventureAsia365-Ecosys/AA-Partner/pull/77\n")
            seen.setdefault("push", []).append(argv)
            return Result(0, "")

        r = HybridRunner()
        r.on(("gitleaks", "version"), Result(0, "8.30.1\n"))
        r.on(("gitleaks", "git"), Result(0, ""))
        r.on((ship_common.AS_APP,), app)
        r.on(("gh", "pr", "list"), Result(0, existing))
        r.on(("gh", "pr", "view"), Result(0, "app/aa-agent\n"))
        return r, seen

    def test_validation_catches_title_body_and_git_state(self):
        r, _ = self.runner()
        ok, _w = sop.validate(r, lane_pr(self.sb.wt))
        self.assertEqual(ok, [])
        bad = lane_pr(self.sb.wt, pr_title="fix: AA-9001 lantern glow", pr_body="Fixes AA-9001\n")
        problems, _ = sop.validate(r, bad)
        text = " ".join(problems)
        self.assertIn("issue id", text)
        self.assertIn("Refs AA-<n>", text)
        self.assertIn("closing phrase", text)
        self.assertTrue(sop.validate(r, lane_pr(self.sb.wt, pr_title="lantern glow"))[0])
        # AA-1024 G11: an id outside the Refs line is linked by Linear (and moved to Done on merge)
        stray = lane_pr(self.sb.wt, pr_body="Joins the AA-9002 lane.\n\nRefs AA-9001\n")
        self.assertIn("AA-9002, which the Refs line does not", " ".join(sop.validate(r, stray)[0]))
        self.assertEqual(sop.stray_issue_ids("x\nRefs AA-1, AA-2\n"), [])
        self.assertEqual(sop.stray_issue_ids("see AA-3 and AA-3\nRefs AA-1"), ["AA-3"])
        self.assertEqual(sop.stray_issue_ids("Refs AA-1 (and AA-4 later)"), ["AA-4"])
        self.assertEqual(sop.stray_issue_ids("Refs AA-1040 (EU AI Act Art. 50(2), root ADR 0019 d19)."), [])
        # the PR's own issue in prose is fine: the Refs line already links it
        own = "AA-9001 lantern retirement, catalogue side.\r\n\r\nRefs AA-9001\r\n"
        self.assertEqual(sop.stray_issue_ids(own), [])
        self.assertEqual(sop.validate(r, lane_pr(self.sb.wt, pr_body=own))[0], [])
        # an id inside a file path is a path (the implementation notes CLAUDE.md asks for), not an issue link
        notes = "Notes: docs/implementation-notes/AA-9003-lantern-l2.md and AA-9004.md\n\nRefs AA-9001\n"
        self.assertEqual(sop.stray_issue_ids(notes), [])
        self.assertEqual(sop.stray_issue_ids("AA-9005. Then docs/x/AA-9001.md\nRefs AA-9001"), ["AA-9005"])
        with open(os.path.join(self.sb.wt, "lantern.py"), "w", encoding="utf-8") as fh:
            fh.write("GLOW = 4\n")
        self.assertIn("modified", " ".join(sop.validate(r, lane_pr(self.sb.wt))[0]))
        self.sb.git(self.sb.wt, "checkout", "--", "lantern.py")
        self.sb.git(self.sb.wt, "checkout", "-q", "-b", "feat/empty", "origin/main")
        self.assertIn("no commit ahead", " ".join(sop.validate(r, lane_pr(self.sb.wt, branch="feat/empty"))[0]))

    def test_a_repo_with_a_pre_push_hook_must_have_it_installed(self):
        r, _ = self.runner()
        hooks = os.path.join(self.sb.wt, ".githooks")
        os.makedirs(hooks)
        with open(os.path.join(hooks, "pre-push"), "w", encoding="utf-8") as fh:
            fh.write("#!/usr/bin/env bash\nexit 0\n")
        self.sb.git(self.sb.wt, "add", "-A")
        self.sb.git(self.sb.wt, "commit", "-qm", "chore: hook")
        problems, _ = sop.validate(r, lane_pr(self.sb.wt))
        self.assertIn("pre-push hook is not installed (core.hooksPath=unset)", " ".join(problems))
        self.assertIn("scripts/install-hooks.sh", " ".join(problems))
        self.sb.git(self.sb.wt, "config", "core.hooksPath", ".githooks")
        self.assertEqual(sop.validate(r, lane_pr(self.sb.wt))[0], [])

    def test_gitleaks_scans_the_branch_with_the_base_rules_before_any_push(self):
        # AA-1024 G14: the orchestrator's own commits were never scanned before the push (lessons S250-S266)
        self.sb.git(self.sb.wt, "checkout", "-q", "main")
        self.sb.commit(self.sb.wt, ".gitleaks.toml", "[extend]\nuseDefault = true\n", "chore: rules")
        self.sb.git(self.sb.wt, "push", "-q", "origin", "HEAD:main")
        self.sb.git(self.sb.wt, "checkout", "-q", "feat/lanterns")
        self.sb.git(self.sb.wt, "rebase", "-q", "origin/main")
        r, _ = self.runner()
        self.assertEqual(sop.validate(r, lane_pr(self.sb.wt))[0], [])
        [scan] = r.called("gitleaks", "git")
        self.assertIn("--log-opts=--diff-merges=remerge --no-renames origin/main..feat/lanterns", scan)
        self.assertIn("--redact", scan)
        cfg = scan[scan.index("-c") + 1]
        self.assertTrue(cfg.endswith(".gitleaks.toml") and not cfg.startswith(self.sb.wt), cfg)
        self.assertNotIn("-i", scan)  # the base has no .gitleaksignore
        leak = HybridRunner()
        leak.on(("gitleaks", "version"), Result(0, "v8.30.1"))
        leak.on(("gitleaks", "git"), Result(1, "", "WRN leaks found: 1"))
        text = " ".join(sop.validate(leak, lane_pr(self.sb.wt))[0])
        self.assertIn("gitleaks found a leak", text)
        self.assertIn("git reset --soft $(git merge-base HEAD origin/main)", text)
        old = HybridRunner()
        old.on(("gitleaks", "version"), Result(0, "8.18.0"))
        self.assertIn("CI uses 8.30.1", " ".join(sop.validate(old, lane_pr(self.sb.wt))[0]))
        with mock.patch.dict(os.environ, {"AA_GITLEAKS": ""}), \
                mock.patch.object(sop.shutil, "which", return_value=None):
            self.assertIn("no gitleaks binary", " ".join(sop.validate(old, lane_pr(self.sb.wt))[0]))
        with mock.patch.dict(os.environ, {"AA_SKIP_GITLEAKS": "1"}):
            problems, warnings = sop.validate(old, lane_pr(self.sb.wt))
        self.assertEqual(problems, [])
        self.assertIn("gitleaks skipped", " ".join(warnings))

    def test_stacked_pr_is_compared_with_the_local_branch_below(self):
        self.sb.git(self.sb.wt, "checkout", "-q", "-b", "feat/lanterns-2")
        self.sb.commit(self.sb.wt, "lantern2.py", "GLOW = 5\n", "feat: brighter lantern")
        r, _ = self.runner()
        upper = lane_pr(self.sb.wt, branch="feat/lanterns-2", base="feat/lanterns")
        self.assertIn("cannot compare", " ".join(sop.validate(r, upper)[0]))
        self.assertEqual(sop.validate(r, upper, frozenset({"feat/lanterns"}))[0], [])

    def test_open_pushes_and_creates_with_refs_and_attribution(self):
        write_journal(self.journal, [{"ready": True, "prs": [lane_pr(self.sb.wt)]}])
        r, seen = self.runner()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = sop.main([str(self.journal), "--extra-refs", "AA-1032"], runner=r)
        self.assertEqual(code, 0, out.getvalue())
        [push] = seen["push"]
        self.assertIn("push", push)
        self.assertNotIn("--force", " ".join(push))
        self.assertEqual(seen["title"], "feat: lantern catalogue sorts by glow")
        self.assertIn("Refs AA-9001, AA-1032", seen["body"])
        self.assertIn("Generated with [Claude Code]", seen["body"])
        self.assertIn("--base", seen["create"])
        self.assertIn("opened https://github.com/AdventureAsia365-Ecosys/AA-Partner/pull/77", out.getvalue())
        self.assertIn("live: curl /crm/health", out.getvalue())
        self.assertEqual(list(Path(self.sb.tmp.name).glob("pr-body-*")), [])

    def test_a_push_that_skipped_the_integration_stamp_says_so_in_the_body(self):
        write_journal(self.journal, [{"ready": True, "prs": [lane_pr(self.sb.wt)]}])
        r, seen = self.runner()
        with mock.patch.dict(os.environ, {"AA_PREPUSH_SKIP_INTEGRATION": "1"}), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sop.main([str(self.journal)], runner=r), 0)
        self.assertIn("AA_PREPUSH_SKIP_INTEGRATION=1", seen["body"])
        self.assertTrue(seen["body"].rstrip().endswith(sop.ATTRIBUTION))
        self.assertEqual(sop.skip_note(seen["body"]).count("AA_PREPUSH_SKIP_INTEGRATION"), 1)
        with mock.patch.dict(os.environ, {"AA_PREPUSH_SKIP_INTEGRATION": ""}):
            self.assertEqual(sop.skip_note(BODY), BODY)

    def test_existing_pr_is_reused_and_dry_run_pushes_nothing(self):
        write_journal(self.journal, [{"ready": True, "prs": [lane_pr(self.sb.wt)]}])
        r, seen = self.runner(existing="https://github.com/AdventureAsia365-Ecosys/AA-Partner/pull/70\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sop.main([str(self.journal)], runner=r), 0)
        self.assertNotIn("create", seen)
        r, seen = self.runner()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sop.main([str(self.journal), "--dry-run"], runner=r), 0)
        self.assertEqual(seen, {})

    def test_not_ready_and_invalid_prs_open_nothing(self):
        write_journal(self.journal, [{"ready": False, "blocked_reason": "lamp oil missing",
                                      "prs": [lane_pr(self.sb.wt)]}])
        r, seen = self.runner()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sop.main([str(self.journal)], runner=r), 4)
        self.assertIn("lamp oil missing", out.getvalue())
        good = lane_pr(self.sb.wt)
        bad = lane_pr(self.sb.wt, repo="AA-Ecosys (root)", pr_title="docs: notes", pr_body="no refs")
        write_journal(self.journal, [{"ready": True, "prs": [good, bad]}])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sop.main([str(self.journal)], runner=r), 4)
        self.assertEqual(seen, {})


class PushTimeoutTest(unittest.TestCase):
    """S272: the CIS pre-push hook runs longer than the old fixed 300 s push limit."""

    def test_default_and_env_bounds(self):
        from unittest import mock
        import ship_open_prs as m
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AA_PUSH_TIMEOUT", None)
            self.assertEqual(m.push_timeout(), 900)
        for raw, want in (("1200", 1200), ("5", 60), ("99999", 3600), ("x", 900)):
            with mock.patch.dict(os.environ, {"AA_PUSH_TIMEOUT": raw}):
                self.assertEqual(m.push_timeout(), want)


class SafeHooksTest(unittest.TestCase):
    """S272 incident: a hook-run test inherited GIT_DIR and rewrote the real clone. The push goes through
    safe-hooks/pre-push, which drops the git repo env before running the repo's own hook."""

    def _git(self, *args, cwd):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        return subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True)

    def _push(self, hooks_path):
        import shutil
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        remote, main = os.path.join(d, "remote.git"), os.path.join(d, "main")
        self._git("init", "-q", "--bare", remote, cwd=d)
        self._git("init", "-q", "-b", "main", main, cwd=d)
        os.makedirs(os.path.join(main, ".githooks"))
        hook = os.path.join(main, ".githooks", "pre-push")
        with open(hook, "w") as f:  # what a careless unit test does: git init + config in "its own" temp dir
            f.write('#!/usr/bin/env bash\nt=$(mktemp -d)\ngit init -q "$t"\ngit -C "$t" config user.name evil\nexit 0\n')
        os.chmod(hook, 0o755)
        self._git("add", "-A", cwd=main)
        self._git("commit", "-q", "-m", "a", cwd=main)
        wt = os.path.join(d, "wt")
        self._git("worktree", "add", "-q", "-b", "feat", wt, cwd=main)
        self._git("-c", f"core.hooksPath={hooks_path}", "push", "-q", remote, "feat", cwd=wt)
        out = self._git("config", "--file", os.path.join(main, ".git", "config"), "--get", "user.name", cwd=d)
        return out.stdout.strip()

    def test_wrapper_keeps_the_clone_clean(self):
        self.assertEqual(self._push(sop.SAFE_HOOKS), "")

    def test_without_the_wrapper_the_clone_is_written(self):
        # proves the test reproduces the incident; if git ever stops exporting GIT_DIR this turns red, drop it then
        self.assertEqual(self._push(".githooks"), "evil")

    def test_push_argv_uses_the_wrapper(self):
        self.assertTrue(os.access(os.path.join(sop.SAFE_HOOKS, "pre-push"), os.X_OK))


class PushFailureReasonTest(unittest.TestCase):
    def test_a_refused_push_names_the_failing_hook_steps_and_the_venv_hint(self):
        err = ("FAIL tf-plan-guard / pytest\n  command (run from the repo root):\n    python3 -m pytest -q tools\n"
               "  missing: python module pytest (in /usr/bin/python3)\n"
               "  install: scripts/install-hooks.sh --venv\n"
               "error: failed to push some refs to 'https://example.invalid/lanterns.git'\n")
        text = sop.push_failure_reason(Result(1, "", err))
        self.assertIn("failed to push some refs", text)
        self.assertIn("FAIL tf-plan-guard / pytest", text)
        self.assertIn("missing: python module pytest", text)
        self.assertIn("AA_PREPUSH_PYTHON", text)

    def test_a_plain_git_error_keeps_the_last_line(self):
        self.assertEqual(sop.push_failure_reason(Result(1, "", "error: rejected (non-fast-forward)\n")),
                         "error: rejected (non-fast-forward)")

    def test_many_failing_steps_are_capped(self):
        err = "".join(f"FAIL step {i}\n" for i in range(20)) + "error: failed to push\n"
        text = sop.push_failure_reason(Result(1, "", err))
        self.assertIn("FAIL step 11", text)
        self.assertNotIn("FAIL step 12", text)
        self.assertIn("8 more", text)


if __name__ == "__main__":
    unittest.main()
