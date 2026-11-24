"""Tests for tools/sync/change_guard.py (AA-1136). Run: python3 .claude/hooks/test_sync_change_guard.py

Builds throw-away git repos in a temp folder (invented file names only); no network, no AWS.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SYNC = HERE.parents[1] / "tools" / "sync"
sys.path.insert(0, str(SYNC))
import change_guard as cg  # noqa: E402

# S272: a git hook (pre-push) exports GIT_DIR and friends; a git command run in a temporary repo below would then act
# on the real repo. Drop git's repo-local variables for this whole test process (`git rev-parse --local-env-vars`;
# tools/github/test_git_env_isolation.py).
for _git_var in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR"):
    os.environ.pop(_git_var, None)


def git(top: Path, *args: str) -> str:
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    return subprocess.run(["git", "-C", str(top), "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                           "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, check=True,
                          env=env).stdout


def write(top: Path, rel: str, text: str = "x = 1\n") -> None:
    p = top / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def new_repo(base: Path, name: str = "Demo") -> Path:
    top = base / name
    top.mkdir(parents=True)
    git(top, "init", "-q", "-b", "main")
    write(top, "README.md", "# demo\n")
    git(top, "add", "-A")
    git(top, "commit", "-q", "-m", "chore: start")
    git(top, "update-ref", "refs/remotes/origin/main", "HEAD")
    return top


class ClassifyTest(unittest.TestCase):
    def test_table(self):
        cases = {
            "api/routers/orders.py": "code",
            "frontend/app/page.tsx": "code",
            "scripts/pre-push.sh": "code",
            "tests/unit/test_orders.py": "test",
            "api/tests/conftest.py": "test",
            ".claude/hooks/test_stop_dispatch.py": "test",
            ".claude/hooks/test_kit_core_edit_guard.sh": "test",
            "frontend/app/page.test.tsx": "test",
            "web/e2e/login.spec.ts": "test",
            "pkg/orders_test.py": "test",
            "docs/implementation-notes/AA-12.md": "note",
            "docs/implementation-notes/AA-12-l3-lane.md": "note",
            "docs/implementation-notes/S291-crm-perf.md": "note",
            "docs/guides/devops.md": "doc",
            "docs/audits/x/audit_data.py": "doc",
            "CONTEXT.md": "doc",
            "api/migrations/301_add_orders.sql": "schema",
            "modules/ecs/main.tf": "schema",
            "package.json": "other",
            "frontend/app/globals.css": "other",
            ".tmp-session/S1-checklist.md": "ignored",
            "frontend/node_modules/x/index.js": "ignored",
            "": "ignored",
        }
        for rel, want in cases.items():
            self.assertEqual(cg.classify(rel), want, rel)


class IdsAndWaiversTest(unittest.TestCase):
    def test_issue_ids_from_branch_and_refs(self):
        self.assertEqual(cg.issue_ids("feat/aa-1136-sync-hooks", ""), ["AA-1136"])
        msgs = "feat: x\n\nRefs AA-7, AA-12\n\nfix: y mentions AA-99 in prose\n"
        self.assertEqual(cg.issue_ids("main", msgs), ["AA-7", "AA-12"])
        self.assertEqual(cg.issue_ids("", ""), [])

    def test_waivers_need_a_reason(self):
        texts = ["## Should know\n- No test needed: pure rename of a private helper\n",
                 "**No note needed:** typo fix in one comment\n"]
        self.assertEqual(cg.find_waivers(texts), {"test": "pure rename of a private helper",
                                                  "note": "typo fix in one comment"})
        self.assertEqual(cg.find_waivers(["No test needed:\n", "No note needed: x\n"]), {})
        self.assertEqual(cg.find_waivers(["No test needed: <reason>\n"]), {}, "the template placeholder is no reason")


class EvaluateTest(unittest.TestCase):
    def run_eval(self, changed, issues=("AA-5",), notes_text=()):
        return cg.evaluate(cg.Report(repo="Demo", top="/x", issues=list(issues)), changed, list(notes_text))

    def test_code_alone_gets_both_findings(self):
        r = self.run_eval(["api/a.py"])
        self.assertEqual(r.findings, ["no-test", "no-note"])
        msg = r.message()
        self.assertIn("No test needed: <reason>", msg)
        self.assertIn("docs/implementation-notes/AA-5.md", msg)

    def test_code_with_test_and_note_is_clean(self):
        r = self.run_eval(["api/a.py", "tests/test_a.py", "docs/implementation-notes/AA-5-l2.md"])
        self.assertEqual(r.findings, [])
        self.assertEqual(r.message(), "")

    def test_note_of_another_issue_does_not_count(self):
        r = self.run_eval(["api/a.py", "tests/test_a.py", "docs/implementation-notes/AA-6.md"])
        self.assertEqual(r.findings, ["no-note"])

    def test_session_note_covers_the_issue(self):
        r = self.run_eval(["api/a.py", "tests/test_a.py", "docs/implementation-notes/S291-crm-perf.md"])
        self.assertEqual(r.findings, [])

    def test_without_issue_any_note_counts(self):
        r = self.run_eval(["api/a.py", "tests/test_a.py", "docs/implementation-notes/AA-6.md"], issues=())
        self.assertEqual(r.findings, [])
        r = self.run_eval(["api/a.py", "tests/test_a.py"], issues=())
        self.assertIn("no issue id", r.message())

    def test_schema_needs_a_note_not_a_test(self):
        self.assertEqual(self.run_eval(["api/migrations/301_x.sql"]).findings, ["no-note"])

    def test_docs_and_config_need_nothing(self):
        self.assertEqual(self.run_eval(["docs/a.md", "package.json", "web/x.css"]).findings, [])

    def test_waivers(self):
        r = self.run_eval(["api/a.py"], notes_text=["No test needed: config constant only\n",
                                                    "No note needed: one-line chore\n"])
        self.assertEqual(r.findings, [])
        self.assertEqual(sorted(r.waivers), ["note", "test"])

    def test_message_is_short(self):
        r = self.run_eval([f"api/m{i}.py" for i in range(40)])
        self.assertLessEqual(len(r.message()), 1500)
        self.assertIn("(+37)", r.message())


class CheckOnGitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.top = new_repo(self.base)

    def tearDown(self):
        self.tmp.cleanup()

    def test_main_branch_reads_only_the_working_tree(self):
        self.assertEqual(cg.check(self.top).findings, [])
        write(self.top, "api/new.py")
        r = cg.check(self.top)
        self.assertEqual((r.branch, r.base, r.code), ("main", "", ["api/new.py"]))
        self.assertEqual(r.findings, ["no-test", "no-note"])

    def test_branch_commits_and_refs_line(self):
        git(self.top, "checkout", "-q", "-b", "feat/some-work")
        write(self.top, "api/svc.py")
        git(self.top, "add", "-A")
        git(self.top, "commit", "-q", "-m", "feat: svc\n\nRefs AA-42")
        r = cg.check(self.top)
        self.assertEqual((r.base, r.issues, r.code), ("origin/main", ["AA-42"], ["api/svc.py"]))
        self.assertEqual(r.findings, ["no-test", "no-note"])
        write(self.top, "docs/implementation-notes/AA-42.md",
              "# AA-42\n\nNo test needed: wiring only, covered upstream\n")
        r = cg.check(self.top)  # the untracked note counts, and its waiver is read
        self.assertEqual(r.findings, [])
        self.assertEqual(r.waivers, {"test": "wiring only, covered upstream"})

    def test_waiver_in_an_unchanged_note_on_disk(self):
        write(self.top, "docs/implementation-notes/AA-43.md", "No note needed: tiny chore\n")
        git(self.top, "add", "-A")
        git(self.top, "commit", "-q", "-m", "docs: note")
        git(self.top, "update-ref", "refs/remotes/origin/main", "HEAD")
        git(self.top, "checkout", "-q", "-b", "chore/aa-43-tiny")
        write(self.top, "api/tiny.py")
        write(self.top, "tests/test_tiny.py")
        self.assertEqual(cg.check(self.top).findings, [])

    def test_lane_worktree(self):
        wt = self.base / "Demo" / ".tmp-session" / "wt" / "lane-x"
        git(self.top, "worktree", "add", "-q", str(wt), "-b", "feat/aa-77-lane", "origin/main")
        write(wt, "tools/t.py")
        r = cg.check(wt)
        self.assertEqual((r.repo, r.branch, r.issues), ("Demo", "feat/aa-77-lane", ["AA-77"]))
        self.assertEqual(r.findings, ["no-test", "no-note"])

    def test_rename_in_status(self):
        write(self.top, "api/old.py")
        git(self.top, "add", "-A")
        git(self.top, "commit", "-q", "-m", "x")
        git(self.top, "mv", "api/old.py", "api/new_name.py")
        self.assertIn("api/new_name.py", cg.check(self.top).code)

    def test_not_a_repo_is_an_error_not_an_exception(self):
        plain = self.base / "plain"
        plain.mkdir()
        r = cg.check(plain)
        self.assertTrue(r.error)
        self.assertEqual(r.findings, [])

    def test_cli_check_exit_codes(self):
        write(self.top, "api/new.py")
        for mode, want in (("log", 0), ("warn", 0), ("block", 1)):
            with mock.patch.dict(os.environ, {"AA_SYNC_HOOKS": mode}):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(cg.main(["check", "--repo-dir", str(self.top)]), want, mode)


class MeasureTest(unittest.TestCase):
    def test_percentile(self):
        self.assertIsNone(cg.percentile([], 50))
        vals = [float(v) for v in range(1, 101)]
        self.assertEqual(cg.percentile(vals, 50), 51.0)
        self.assertEqual(cg.percentile(vals, 95), 95.0)

    def test_report_from_log(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "log.jsonl"
            rows = [
                {"ts": "2026-01-01T00:00:00", "event": "PostToolUse", "latency_ms": 10, "agent": "a1",
                 "repo_kind": "worktree"},
                {"ts": "2026-01-02T00:00:00", "event": "PostToolUse", "latency_ms": 30, "agent": "a2",
                 "session": "s1", "repo": "Demo", "repo_kind": "worktree", "would": "remind",
                 "docs_entries": ["orders"]},
                # the same edit reminder again in the same session: counted once
                {"ts": "2026-01-02T00:00:00", "event": "PostToolUse", "latency_ms": 30, "agent": "a2",
                 "session": "s1", "repo": "Demo", "repo_kind": "worktree", "would": "remind",
                 "docs_entries": ["orders"]},
                {"ts": "2026-01-02T00:00:01", "event": "SubagentStop", "latency_ms": 50, "wall_ms": 64, "agent": "a1",
                 "session": "s1", "repo_kind": "worktree",
                 "checks": [{"repo": "Demo", "branch": "feat/a", "code": 2, "findings": ["no-test"],
                             "waivers": ["note"]}]},
                {"ts": "2026-01-02T00:00:02", "event": "Stop", "latency_ms": 70, "agent": "main", "error": "boom"},
                # one open finding on every turn's Stop: counted once per (session, agent, repo, branch, finding)
                {"ts": "2026-01-02T00:00:03", "event": "Stop", "latency_ms": 70, "agent": "main", "session": "s1",
                 "repo_kind": "main", "checks": [
                     {"repo": "Demo", "branch": "feat/b", "code": 1, "findings": ["no-note"], "waivers": []},
                     {"repo": "Other", "branch": "fix/c", "code": 1, "findings": [], "waivers": ["test"]}]},
                {"ts": "2026-01-02T00:00:04", "event": "Stop", "latency_ms": 70, "agent": "main", "session": "s1",
                 "repo_kind": "main", "checks": [
                     {"repo": "Demo", "branch": "feat/b", "code": 1, "findings": ["no-note"], "waivers": []},
                     {"repo": "Other", "branch": "fix/c", "code": 1, "findings": [], "waivers": ["test"]}]},
                # the same finding in a later session would be said again in warn mode: counted again
                {"ts": "2026-01-03T00:00:00", "event": "Stop", "latency_ms": 70, "agent": "main", "session": "s2",
                 "repo_kind": "main", "checks": [
                     {"repo": "Demo", "branch": "feat/b", "code": 1, "findings": ["no-note"], "waivers": []}]},
            ]
            log.write_text("\n".join(json.dumps(r) for r in rows) + "\nnot json\n", encoding="utf-8")
            out = cg.summarize_log(cg.read_log(log, since="2026-01-02"))
            self.assertEqual(out["events"], 7)
            self.assertEqual(out["errors"], 1)
            self.assertEqual(out["latency_ms"]["SubagentStop"], {"n": 1, "p50": 50.0, "p95": 50.0})
            self.assertEqual(out["wall_ms"], {"SubagentStop": {"n": 1, "p50": 64.0, "p95": 64.0}})
            self.assertEqual(out["lane_agents"], {"PostToolUse": 1, "SubagentStop": 1})
            self.assertEqual(out["would_remind"], {"Demo": {"no-note": 2, "no-test": 1, "post-edit": 1}})
            self.assertEqual(out["findings"], [["Demo", "feat/a", "no-test"], ["Demo", "feat/b", "no-note"],
                                               ["Demo", "feat/b", "no-note"]])
            self.assertEqual(out["waivers"], {"Demo": {"note": 1}, "Other": {"test": 1}})
            self.assertEqual(out["code_changes"], {"Demo": 2, "Other": 1})
            self.assertEqual(out["waived_share"], {"Demo": 0.5, "Other": 1.0})
            with contextlib.redirect_stdout(io.StringIO()) as out_text:
                self.assertEqual(cg.main(["report", "--log", str(log)]), 0)
            self.assertIn("p95=", out_text.getvalue())
            self.assertIn("Other: would remind none; waivers {'test': 1}; code changes 1, waived 100%",
                          out_text.getvalue())

    def test_uncovered_commits(self):
        with tempfile.TemporaryDirectory() as d:
            top = new_repo(Path(d))
            write(top, "api/a.py")
            git(top, "add", "-A")
            git(top, "commit", "-q", "-m", "feat: a\n\nRefs AA-1")  # code, no note: uncovered
            write(top, "api/b.py")
            write(top, "docs/implementation-notes/AA-2.md", "# AA-2\n")
            git(top, "add", "-A")
            git(top, "commit", "-q", "-m", "feat: b\n\nRefs AA-2")  # covered
            write(top, "docs/implementation-notes/AA-3.md", "No note needed: tiny\n")
            git(top, "add", "-A")
            git(top, "commit", "-q", "-m", "docs: waiver")
            write(top, "api/c.py", "y = 2\n")
            git(top, "add", "-A")
            git(top, "commit", "-q", "-m", "chore: c\n\nRefs AA-3")  # waived by the note at that commit
            git(top, "update-ref", "refs/remotes/origin/main", "HEAD")
            out = cg.uncovered_commits(top)
            self.assertEqual((out["code_commits"], out["uncovered"], out["rate"]), (3, 1, 0.333))
            with contextlib.redirect_stdout(io.StringIO()) as out_text:
                self.assertEqual(cg.main(["commits", "--repo-dir", str(top), "--json"]), 0)
            self.assertEqual(json.loads(out_text.getvalue())["uncovered"], 1)


if __name__ == "__main__":
    unittest.main()
