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
        # S294: the gitleaks resolver also looks at the mise install under HOME (and MISE_DATA_DIR / XDG_DATA_HOME); a
        # machine with gitleaks installed through mise made the FakeRunner meet an unexpected `version` call. Point
        # them at the sandbox so only the test decides which binaries exist (git is hermetic through GIT_ENV).
        self.home = Path(self.sb.tmp.name) / "home"
        self.env = mock.patch.dict(os.environ, {"AA_GITLEAKS": "gitleaks", "AA_SKIP_GITLEAKS": "",
                                                "HOME": str(self.home), "MISE_DATA_DIR": "", "XDG_DATA_HOME": ""})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmpdir.stop()
        self.sb.close()

    def runner(self, existing: str = "", merged=""):
        """merged: the `gh pr list --state merged` answer (a URL, a Result or a function of argv)."""
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
        r.on(("gh", "pr", "list", "--state", "merged"), Result(0, merged) if isinstance(merged, str) else merged)
        r.on(("gh", "pr", "list", "--state", "open"), Result(0, existing))
        r.on(("gh", "pr", "view"), Result(0, "app/aa-agent\n"))
        return r, seen

    def test_validation_catches_title_body_and_git_state(self):
        r, _ = self.runner()
        ok, _w = sop.validate(r, lane_pr(self.sb.wt))
        self.assertEqual(ok, [])
        # S285: a lane may report its base as "origin/<branch>"; it means the same branch, not origin/origin/<branch>
        self.assertEqual(sop.validate(r, lane_pr(self.sb.wt, base="origin/main"))[0], [])
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
                mock.patch.object(sop.gitleaks_resolve, "which_all", return_value=[]):
            self.assertIn("no gitleaks binary", " ".join(sop.validate(old, lane_pr(self.sb.wt))[0]))
        # S281: a mise shim with no version set is skipped, the checked download under ROOT is used instead
        shim = HybridRunner()
        shim.on(("/fake/shims/gitleaks", "version"), Result(1, "", "mise ERROR No version is set for shim: gitleaks"))
        local = Path(self.sb.tmp.name) / sop.GITLEAKS_LOCAL
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text("#!/bin/sh\n", encoding="utf-8")
        local.chmod(0o755)
        shim.on((str(local), "version"), Result(0, "8.30.1\n"))
        shim.on((str(local), "git"), Result(0, ""))
        with mock.patch.dict(os.environ, {"AA_GITLEAKS": ""}), \
                mock.patch.object(sop.gitleaks_resolve, "which_all", return_value=["/fake/shims/gitleaks"]):
            self.assertEqual(sop.validate(shim, lane_pr(self.sb.wt))[0], [])
        self.assertEqual(len(shim.called(str(local), "git")), 1)
        self.assertEqual(shim.called("/fake/shims/gitleaks", "git"), [])
        local.unlink()
        with mock.patch.dict(os.environ, {"AA_GITLEAKS": ""}), \
                mock.patch.object(sop.gitleaks_resolve, "which_all", return_value=["/fake/shims/gitleaks"]):
            text = " ".join(sop.validate(shim, lane_pr(self.sb.wt))[0])
        self.assertIn("no gitleaks binary", text)
        self.assertIn("No version is set for shim", text)
        # S282: the mise install of the pin is used before the broken shim on PATH
        mise = self.home / ".local" / "share" / "mise" / "installs" / "gitleaks" / sop.GITLEAKS_VERSION / "gitleaks"
        mise.parent.mkdir(parents=True)
        mise.write_text("#!/bin/sh\n", encoding="utf-8")
        mise.chmod(0o755)
        shim.on((str(mise), "version"), Result(0, "8.30.1\n"))
        shim.on((str(mise), "git"), Result(0, ""))
        with mock.patch.dict(os.environ, {"AA_GITLEAKS": ""}), \
                mock.patch.object(sop.gitleaks_resolve, "which_all", return_value=["/fake/shims/gitleaks"]):
            self.assertEqual(sop.validate(shim, lane_pr(self.sb.wt))[0], [])
        self.assertEqual(len(shim.called(str(mise), "git")), 1)
        # the shim was probed once, by the run before; with the mise install in place it is not probed again
        self.assertEqual(len(shim.called("/fake/shims/gitleaks", "version")), 1)
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

    def test_a_branch_with_a_merged_pr_is_skipped_not_reopened(self):
        # S292: a second run after part of the lane merged opened duplicates of the merged PRs (open-PR lookup only)
        merged_url = "https://github.com/AdventureAsia365-Ecosys/AA-Partner/pull/70"
        self.sb.git(self.sb.wt, "checkout", "-q", "-b", "feat/lamps")
        self.sb.commit(self.sb.wt, "lamp.py", "OIL = 1\n", "feat: lamp oil")
        write_journal(self.journal, [{"ready": True, "prs": [lane_pr(self.sb.wt),
                                                              lane_pr(self.sb.wt, branch="feat/lamps")]}])
        r, seen = self.runner(merged=lambda argv: Result(0, merged_url + "\n" if "feat/lanterns" in argv else ""))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sop.main([str(self.journal)], runner=r), 0, out.getvalue())
        self.assertIn(f"SKIP AA-Partner feat/lanterns: already MERGED as {merged_url}", out.getvalue())
        [push] = seen["push"]
        self.assertEqual(push[-1], "feat/lamps")
        self.assertEqual(len(r.called("gitleaks", "git")), 1)  # the merged branch is not even validated
        # every branch merged: nothing pushed, exit 0, said so
        write_journal(self.journal, [{"ready": True, "prs": [lane_pr(self.sb.wt)]}])
        r, seen = self.runner(merged=merged_url + "\n")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sop.main([str(self.journal)], runner=r), 0)
        self.assertEqual(seen, {})
        self.assertIn("nothing to open", out.getvalue())

    def test_a_failed_merged_lookup_refuses_that_pr(self):
        write_journal(self.journal, [{"ready": True, "prs": [lane_pr(self.sb.wt)]}])
        r, seen = self.runner(merged=Result(1, "", "HTTP 502"))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sop.main([str(self.journal)], runner=r), 4)
        self.assertIn("cannot check for a merged PR of feat/lanterns: HTTP 502", out.getvalue())
        self.assertEqual(seen, {})

    def test_a_body_without_refs_says_how_to_fix_it_and_refs_inserts_the_first_line(self):
        bare = "## What\n- A small invented change to the lantern catalogue.\n"
        write_journal(self.journal, [{"ready": True, "prs": [lane_pr(self.sb.wt, pr_body=bare)]}])
        r, seen = self.runner()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sop.main([str(self.journal)], runner=r), 4)
        self.assertIn("body has no 'Refs AA-<n>' line: pass --refs AA-<n>", out.getvalue())
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sop.main([str(self.journal), "--refs", "AA-9001, AA-9002"], runner=r), 0, out.getvalue())
        self.assertTrue(seen["body"].startswith("Refs AA-9001, AA-9002\n\n## What\n"), seen["body"])
        # S294: --extra-refs alone also makes the body valid now (the checks read the body as it is opened)
        r, seen = self.runner()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sop.main([str(self.journal), "--extra-refs", "AA-9001"], runner=r), 0, out.getvalue())
        self.assertIn("\nRefs AA-9001\n", seen["body"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sop.main([str(self.journal), "--refs", "9001"], runner=r), 2)

    def test_refs_on_a_body_that_has_a_refs_line_joins_its_list(self):
        self.assertEqual(sop.insert_refs(BODY, ["AA-9002"]), BODY.replace("Refs AA-9001", "Refs AA-9001, AA-9002"))
        self.assertEqual(sop.insert_refs(BODY, []), BODY)
        self.assertEqual(sop.insert_refs("\n\nlantern notes\n", ["AA-1"]), "Refs AA-1\n\nlantern notes\n")

    def test_an_issue_id_outside_the_refs_line_is_refused_before_any_push(self):
        # S292 (two root PRs): the lane told the history with other issue ids; pr-title.yml refused them on GitHub
        body = "Builds on the AA-9002 stacked-branch merge and the AA-9003 notes.\n\nRefs AA-9001\n"
        write_journal(self.journal, [{"ready": True, "prs": [lane_pr(self.sb.wt, pr_body=body)]}])
        r, seen = self.runner()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sop.main([str(self.journal)], runner=r), 4)
        self.assertIn("body names AA-9002, AA-9003, which the Refs line does not", out.getvalue())
        self.assertEqual(seen, {})
        # the orchestrator may decide the PR does those issues: the ids then join the Refs line and the body passes
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(sop.main([str(self.journal), "--extra-refs", "AA-9002,AA-9003"], runner=r), 0,
                             out.getvalue())
        self.assertIn("Refs AA-9001, AA-9002, AA-9003", seen["body"])

    def test_project_template_needs_no_refs_and_refuses_any_issue_id(self):
        tpl = dict(repo="project-template", pr_title="docs: lantern kit readme",
                   pr_body="## What\n- The lantern kit readme names its glow levels.\n")
        r, _ = self.runner()
        self.assertEqual(sop.validate(r, lane_pr(self.sb.wt, **tpl))[0], [])
        bad = sop.validate(r, lane_pr(self.sb.wt, **dict(tpl, pr_body=BODY)))[0]
        self.assertIn("project-template is public and its denylist forbids issue ids: the title or body names AA-9001",
                      " ".join(bad))
        self.assertNotIn("Refs AA-<n>' line", " ".join(bad))
        self.assertTrue(sop.validate(r, lane_pr(self.sb.wt, **dict(tpl, pr_title="docs: AA-12 readme")))[0])
        # --refs / --extra-refs are not applied there (a warning says so); the body opens without an id
        write_journal(self.journal, [{"ready": True, "prs": [lane_pr(self.sb.wt, **tpl)]}])
        r, seen = self.runner()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = sop.main([str(self.journal), "--refs", "AA-9001", "--extra-refs", "AA-9002"], runner=r)
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("--refs / --extra-refs not applied (project-template forbids issue ids)", out.getvalue())
        self.assertNotRegex(seen["body"], r"AA-\d")
        self.assertIn("/project-template", " ".join(seen["create"]))

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
