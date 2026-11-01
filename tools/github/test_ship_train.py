"""Tests for ship_train.py (AA-1032): real git in a temporary repository, scripted gh and as-app.sh.

Run: python -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import unittest

import ship_common
import ship_train
from ship_common import Result, ShipError
from ship_fakes import GitSandbox, HybridRunner, pr


def js(obj) -> Result:
    return Result(0, json.dumps(obj))


class ParseItemTest(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(ship_train.parse_item("feat/a:12"), ship_train.Item("feat/a", 12, None))
        self.assertEqual(ship_train.parse_item("feat/a:12:3"), ship_train.Item("feat/a", 12, 3))
        self.assertEqual(ship_train.parse_item("feat/a 12 3"), ship_train.Item("feat/a", 12, 3))
        for bad in ("feat/a", "feat/a:x", "feat/a:1:y", "a:1:2:3"):
            with self.assertRaises(ShipError):
                ship_train.parse_item(bad)


class TrainTest(unittest.TestCase):
    """Stack: main <- A (2 commits) <- B (1 commit). A is squash-merged into main, then B is restacked."""

    def setUp(self):
        self.sb = GitSandbox()
        self.out = contextlib.redirect_stdout(io.StringIO())
        self.out.__enter__()
        g, wt = self.sb.git, self.sb.wt
        g(wt, "checkout", "-q", "-b", "feat/a")
        self.sb.commit(wt, "a1.txt", "a1\n", "feat: a1")
        self.sb.commit(wt, "a2.txt", "a2\n", "feat: a2")
        g(wt, "checkout", "-q", "-b", "feat/b")
        self.sb.commit(wt, "b1.txt", "b1\n", "feat: b1")
        g(wt, "push", "-q", "origin", "feat/a", "feat/b")
        self.git = ship_train.Git(HybridRunner(), wt)

    def tearDown(self):
        self.out.__exit__(None, None, None)
        self.sb.close()

    def squash_a_into_main(self):
        o = self.sb.other
        self.sb.git(o, "fetch", "-q", "origin")
        self.sb.git(o, "checkout", "-q", "-B", "main", "origin/main")
        self.sb.git(o, "merge", "-q", "--squash", "origin/feat/a")
        self.sb.git(o, "commit", "-q", "-m", "feat: a (#1)")
        self.sb.git(o, "push", "-q", "origin", "main")

    def runner_for(self, branch: str, n: int, base: str = "main", draft: bool = False) -> HybridRunner:
        r = HybridRunner()
        self.git.runner = r
        state = {"merged": False}

        def view(argv):
            head = self.sb.git(self.sb.wt, "rev-parse", branch)
            if state["merged"]:
                return js(pr(n, state="MERGED", merge_oid="9" * 40, head=head))
            # The fake PR follows the App's retarget / ready calls.
            now_base = "main" if r.called(ship_common.AS_APP, "edit") else base
            now_draft = draft and not r.called(ship_common.AS_APP, "ready")
            return js(pr(n, head=head, base=now_base, draft=now_draft))

        def queue(argv):
            state["merged"] = True
            return Result(0, "MERGED")

        r.on(("gh", "pr", "view"), view).on(("gh", "api"), Result(0, "[]\n"))
        r.on((ship_common.MERGEQ,), queue).on((ship_common.AS_APP,), Result(0, ""))
        return r

    def test_plan_counts_own_commits_before_anything_moves(self):
        items = ship_train.plan(self.git, "main", [ship_train.Item("feat/a", 1), ship_train.Item("feat/b", 2)])
        self.assertEqual([i.own for i in items], [2, 1])

    def test_restack_moves_only_own_commits_and_pushes_with_lease(self):
        items = ship_train.plan(self.git, "main", [ship_train.Item("feat/a", 1), ship_train.Item("feat/b", 2)])
        old_b = self.sb.git(self.sb.wt, "rev-parse", "feat/b")
        self.squash_a_into_main()
        r = self.runner_for("feat/b", 2, base="feat/a", draft=True)
        sha = ship_train.ship_branch(r, self.git, "AA-Partner", items[1], interval=30)
        self.assertEqual(sha, "9" * 40)
        wt = self.sb.wt
        # B now holds exactly its own commit on top of the squashed main, and all files are there.
        self.assertEqual(self.sb.git(wt, "rev-list", "--count", "origin/main..feat/b"), "1")
        self.assertEqual(self.sb.git(wt, "log", "-1", "--format=%s", "feat/b"), "feat: b1")
        files = set(self.sb.git(wt, "ls-tree", "--name-only", "feat/b").split())
        self.assertTrue({"a1.txt", "a2.txt", "b1.txt"} <= files)
        # Retarget + ready before the push, push with an explicit lease on the old remote SHA, merge via the queue.
        app_calls = r.called(ship_common.AS_APP)
        self.assertIn("edit", app_calls[0])
        self.assertIn("ready", app_calls[1])
        push = app_calls[2]
        self.assertIn(f"--force-with-lease=feat/b:{old_b}", push)
        self.assertEqual(len(r.called(ship_common.MERGEQ)), 1)

    def test_conflict_aborts_the_rebase_and_stops(self):
        items = ship_train.plan(self.git, "main", [ship_train.Item("feat/b", 2, 1)])
        o = self.sb.other
        self.sb.git(o, "fetch", "-q", "origin")
        self.sb.git(o, "checkout", "-q", "-B", "main", "origin/main")
        self.sb.commit(o, "b1.txt", "other\n", "feat: conflicting")
        self.sb.git(o, "push", "-q", "origin", "main")
        r = self.runner_for("feat/b", 2)
        with self.assertRaises(ShipError) as cm:
            ship_train.ship_branch(r, self.git, "AA-Partner", items[0])
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("rebase conflict", str(cm.exception))
        self.assertFalse(os.path.exists(os.path.join(self.sb.wt, ".git", "rebase-merge")))
        self.assertFalse(r.called(ship_common.AS_APP))

    def test_refuses_when_remote_has_commits_the_local_branch_lacks(self):
        o = self.sb.other
        self.sb.git(o, "fetch", "-q", "origin")
        self.sb.git(o, "checkout", "-q", "-B", "feat/b", "origin/feat/b")
        self.sb.commit(o, "bot.txt", "bot\n", "chore: bot push")
        self.sb.git(o, "push", "-q", "origin", "feat/b")
        r = self.runner_for("feat/b", 2)
        with self.assertRaises(ShipError) as cm:
            ship_train.ship_branch(r, self.git, "AA-Partner", ship_train.Item("feat/b", 2, 1))
        self.assertIn("lacks", str(cm.exception))
        self.assertFalse(r.called(ship_common.AS_APP))

    def test_refuses_dirty_worktree_and_unstacked_branch(self):
        with open(os.path.join(self.sb.wt, "b1.txt"), "w", encoding="utf-8") as fh:
            fh.write("changed\n")
        with self.assertRaises(ShipError) as cm:
            ship_train.preflight_worktree(self.git)
        self.assertIn("modified", str(cm.exception))
        self.sb.git(self.sb.wt, "checkout", "--", "b1.txt")
        self.sb.git(self.sb.wt, "checkout", "-q", "-b", "feat/c", "origin/main")
        self.sb.commit(self.sb.wt, "c.txt", "c\n", "feat: c")
        with self.assertRaises(ShipError) as cm:
            ship_train.plan(self.git, "main", [ship_train.Item("feat/a", 1), ship_train.Item("feat/c", 3)])
        self.assertIn("not stacked", str(cm.exception))

    def test_main_dry_run_prints_plan_and_changes_nothing(self):
        r = HybridRunner()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = ship_train.main(["partner", self.sb.wt, "feat/a:1", "feat/b:2", "--dry-run"], runner=r)
        self.assertEqual(code, 0)
        self.assertIn("rebase --onto origin/main feat/b~1 feat/b", out.getvalue())
        self.assertFalse([c for c in r.calls if c[0] != "git"])


if __name__ == "__main__":
    unittest.main()
