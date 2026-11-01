"""Tests for ship_open_prs.py (AA-1032): journal parsing, PR text guards, push + create through the App.

Real git in a temporary repository; gh and as-app.sh are scripted. Run:
python -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ship_common
import ship_open_prs as sop
from ship_common import Result, ShipError
from ship_fakes import GitSandbox, HybridRunner

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

    def tearDown(self):
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
        with open(os.path.join(self.sb.wt, "lantern.py"), "w", encoding="utf-8") as fh:
            fh.write("GLOW = 4\n")
        self.assertIn("modified", " ".join(sop.validate(r, lane_pr(self.sb.wt))[0]))
        self.sb.git(self.sb.wt, "checkout", "--", "lantern.py")
        self.sb.git(self.sb.wt, "checkout", "-q", "-b", "feat/empty", "origin/main")
        self.assertIn("no commit ahead", " ".join(sop.validate(r, lane_pr(self.sb.wt, branch="feat/empty"))[0]))

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


if __name__ == "__main__":
    unittest.main()
