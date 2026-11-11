"""Tests for ship_wave.py (AA-1024 G1). Offline: gh/aws scripted, migrations and health reads injected.

Run: python -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

import ship_common
import ship_merge
import ship_wave
from ship_common import Result, Runner, ShipError
from ship_fakes import FakeRunner, GitSandbox, HybridRunner, pr

MERGE_SHA = {1350: "c" * 40, 1351: "d" * 40, 1349: "e" * 40, 601: "f" * 40}


def js(obj) -> Result:
    return Result(0, json.dumps(obj))


class Recorder:
    """Order of events across the worker threads."""

    def __init__(self):
        self.events: list[str] = []
        self.lock = threading.Lock()

    def add(self, e: str) -> None:
        with self.lock:
            self.events.append(e)


def scripted(numbers, rec: Recorder, *, wait_for: dict | None = None, repo_of: dict | None = None,
             dirty: tuple = ()) -> FakeRunner:
    """A FakeRunner where each PR is OPEN and green until its merge call ran, then MERGED.

    wait_for {a: b}: the merge call of PR a blocks until the merge call of PR b has STARTED (proves parallelism:
    a serial run would wait for ever, so the call gives up after 5 s and fails)."""
    started = {n: threading.Event() for n in numbers}
    merged: set[int] = set()
    r = FakeRunner()
    r.on(("export-credentials",), Result(1, "", "no session"))
    r.on(("--paginate",), Result(0, "[]\n"))

    def view(n):
        def answer(argv):
            if n in merged:
                return js(pr(n, state="MERGED", merge_oid=MERGE_SHA.get(n, "a" * 40)))
            return js(pr(n, mss="DIRTY" if n in dirty else "CLEAN", base=ship_common.default_branch(
                (repo_of or {}).get(n, "AA-CIS-App"))))
        return answer

    def merge(n):
        def answer(argv):
            started[n].set()
            rec.add(f"merge-start {n}")
            other = (wait_for or {}).get(n)
            if other is not None and not started[other].wait(5):
                rec.add(f"merge-timeout {n}")
                return Result(4, "", "partner never started: serial run")
            merged.add(n)
            rec.add(f"merged {n}")
            return Result(0, f"MERGED {n}")
        return answer

    for n in numbers:
        r.on(("gh", "pr", "view", str(n)), view(n))
        r.on((ship_common.MERGEQ, str(n)), merge(n))
        r.on(("gh", "pr", "merge", str(n)), merge(n))
    return r


class ParseTest(unittest.TestCase):
    def test_forms(self):
        items = ship_wave.parse_items(["cis#1350", "cis#1349>apply:cis/383,cis/384", "booking#201@after=bk/38",
                                       "AA-Partner#45>apply:crm/41@after=cis/384"])
        self.assertEqual([(i.repo, i.n) for i in items],
                         [("AA-CIS-App", 1350), ("AA-CIS-App", 1349), ("AA-Booking", 201), ("AA-Partner", 45)])
        self.assertEqual(items[1].applies, [("cis", "383"), ("cis", "384")])
        self.assertEqual(items[2].after, [("booking", "038")])
        self.assertEqual((items[3].applies, items[3].after), ([("crm", "041")], [("cis", "384")]))

    def test_refusals(self):
        for bad in (["cis#1", "cis#1"], ["cis#1>apply:cis/383", "cis#2>apply:cis/383"], ["cis#1>apply:383"],
                    ["cis#1>apply:cis/383@after=cis/383"], ["nope#1"]):
            with self.assertRaises(ShipError, msg=bad):
                ship_wave.parse_items(bad)

    def test_plan(self):
        lines = ship_wave.plan_lines(ship_wave.parse_items(
            ["cis#1350", "cis#1349>apply:cis/384,cis/383", "cis#1351@after=cis/384"]))
        self.assertEqual(lines[0], "at once (2, in parallel): AA-CIS-App#1350, AA-CIS-App#1349")
        self.assertIn("cis/383 (after AA-CIS-App#1349 merges) -> cis/384", lines[1])
        self.assertEqual(lines[2], "hold AA-CIS-App#1351 until applied: cis/384")


class WaveTest(unittest.TestCase):
    def setUp(self):
        self.out = io.StringIO()
        self._redirect = contextlib.redirect_stdout(self.out)
        self._redirect.__enter__()
        # The default stacked-branch check of a held PR finds no local clone here (it is tested on its own below).
        self._tmp = tempfile.TemporaryDirectory(prefix="ship-wave-")
        self._clone = mock.patch.object(ship_wave, "local_checkout", lambda repo: Path(self._tmp.name) / "no-clone")
        self._clone.start()

    def tearDown(self):
        self._clone.stop()
        self._tmp.cleanup()
        self._redirect.__exit__(None, None, None)

    def test_held_pr_branch_is_updated_after_apply_and_before_its_gate(self):
        # AA-1084: the stacked-branch update runs once the migration is applied, before the held PR is gated, and
        # the gate then waits for the pushed head; the independent PR is never touched.
        rec = Recorder()
        r = scripted([1349, 1350, 1351], rec)

        def apply_fn(owner, nnn):
            rec.add(f"apply {owner}/{nnn}")
            return 0

        seen = []

        def restack(runner, repo, n):
            rec.add(f"restack {n}")
            seen.append((repo, n))
            return "a" * 40  # the head the scripted PR view shows

        with mock.patch.object(ship_merge, "merge_one", wraps=ship_merge.merge_one) as m1:
            code = ship_wave.main(["cis#1349>apply:cis/383", "cis#1351@after=cis/383", "cis#1350"], runner=r,
                                  apply_fn=apply_fn, fetch=lambda url: {}, restack=restack)
        self.assertEqual(code, 0, self.out.getvalue())
        self.assertEqual(seen, [("AA-CIS-App", 1351)])
        ev = rec.events
        self.assertLess(ev.index("apply cis/383"), ev.index("restack 1351"))
        self.assertLess(ev.index("restack 1351"), ev.index("merge-start 1351"))
        heads = {c.args[2]: c.kwargs.get("expect_head") for c in m1.call_args_list}
        self.assertEqual(heads, {1349: None, 1350: None, 1351: "a" * 40})

    def test_failed_branch_update_stops_that_pr_only(self):
        rec = Recorder()
        r = scripted([1349, 1350, 1351], rec)

        def restack(runner, repo, n):
            raise ShipError(f"{repo}#{n}: merging origin/main into feat/x conflicts in api/x.py", 4)

        code = ship_wave.main(["cis#1349>apply:cis/383", "cis#1351@after=cis/383", "cis#1350"], runner=r,
                              apply_fn=lambda o, n: 0, fetch=lambda url: {}, restack=restack)
        self.assertEqual(code, 4)
        self.assertNotIn("merge-start 1351", rec.events)
        self.assertIn("merged 1350", rec.events)
        self.assertIn("AA-CIS-App#1351: exit 4 - AA-CIS-App#1351: merging origin/main into feat/x conflicts",
                      self.out.getvalue())

    def test_check_only_never_updates_a_branch(self):
        r = scripted([1349, 1351], Recorder())
        called = []
        code = ship_wave.main(["cis#1349>apply:cis/383", "cis#1351@after=cis/383", "--check-only"], runner=r,
                              apply_fn=lambda o, n: 0, fetch=lambda url: {},
                              restack=lambda runner, repo, n: called.append(n))
        self.assertEqual(code, 0, self.out.getvalue())
        self.assertEqual(called, [])

    def test_independent_prs_are_merged_in_parallel(self):
        # Each merge call waits until the other one has started: only a parallel run gets both through.
        rec = Recorder()
        r = scripted([1350, 1351], rec, wait_for={1350: 1351, 1351: 1350})
        code = ship_wave.main(["cis#1350", "cis#1351"], runner=r, apply_fn=lambda o, n: 0,
                              fetch=lambda url: {})
        self.assertEqual(code, 0, self.out.getvalue())
        self.assertNotIn("merge-timeout 1350", rec.events)
        self.assertEqual(sorted(e for e in rec.events if e.startswith("merged")), ["merged 1350", "merged 1351"])

    def test_held_pr_waits_for_its_migration_and_independent_pr_does_not(self):
        rec = Recorder()
        r = scripted([1349, 1350, 1351], rec, wait_for={1350: 1349})

        def apply_fn(owner, nnn):
            rec.add(f"apply {owner}/{nnn}")
            return 0

        code = ship_wave.main(["cis#1349>apply:cis/383,cis/384", "cis#1351@after=cis/384", "cis#1350"],
                              runner=r, apply_fn=apply_fn, fetch=lambda url: {})
        self.assertEqual(code, 0, self.out.getvalue())
        ev = rec.events
        self.assertLess(ev.index("merged 1349"), ev.index("apply cis/383"))
        self.assertLess(ev.index("apply cis/383"), ev.index("apply cis/384"))
        self.assertLess(ev.index("apply cis/384"), ev.index("merge-start 1351"))
        self.assertNotIn("merge-timeout 1350", ev)

    def test_failed_apply_skips_the_held_pr_only(self):
        rec = Recorder()
        r = scripted([1349, 1350, 1351], rec)
        code = ship_wave.main(["cis#1349>apply:cis/383", "cis#1351@after=cis/383", "cis#1350"], runner=r,
                              apply_fn=lambda o, n: 1, fetch=lambda url: {})
        self.assertEqual(code, 4)
        self.assertIn("merged 1350", rec.events)
        self.assertNotIn("merge-start 1351", rec.events)
        self.assertIn("AA-CIS-App#1351: exit 4 - skipped: migration(s) cis/383 not applied", self.out.getvalue())

    def test_dirty_pr_is_refused_without_blocking_the_rest(self):
        rec = Recorder()
        r = scripted([1350, 1351], rec, dirty=(1350,))
        code = ship_wave.main(["cis#1350", "cis#1351"], runner=r, apply_fn=lambda o, n: 0, fetch=lambda url: {})
        self.assertEqual(code, 4)
        self.assertIn("DIRTY", self.out.getvalue())
        self.assertEqual([e for e in rec.events if e.startswith("merged")], ["merged 1351"])

    def test_hold_on_a_migration_nothing_applies_must_be_registered(self):
        r = scripted([1351], Recorder())
        code = ship_wave.main(["cis#1351@after=cis/384"], runner=r, apply_fn=lambda o, n: 0,
                              fetch=lambda url: {"registered_keys": ["383"]})
        self.assertEqual(code, 2)
        self.assertIn("no PR in this wave applies", self.out.getvalue())
        rec = Recorder()
        r = scripted([1351], rec)
        code = ship_wave.main(["cis#1351@after=cis/384"], runner=r, apply_fn=lambda o, n: 0,
                              fetch=lambda url: {"registered_keys": ["384"]})
        self.assertEqual(code, 0, self.out.getvalue())
        self.assertIn("merged 1351", rec.events)

    def test_non_queue_repo_squashes_one_at_a_time(self):
        rec = Recorder()
        r = scripted([601, 602], rec, repo_of={601: "AA-Ecosys", 602: "AA-Ecosys"})
        code = ship_wave.main(["root#601", "root#602"], runner=r, apply_fn=lambda o, n: 0, fetch=lambda url: {})
        self.assertEqual(code, 0, self.out.getvalue())
        starts = [e for e in rec.events if e.startswith(("merge-start", "merged"))]
        self.assertIn(starts, (["merge-start 601", "merged 601", "merge-start 602", "merged 602"],
                               ["merge-start 602", "merged 602", "merge-start 601", "merged 601"]))

    def test_wait_deploy_once_per_app_until_the_wave_is_live(self):
        rec = Recorder()
        r = scripted([1350, 1351], rec)
        r.on(("gh", "api", f"repos/{ship_common.ORG}/AA-CIS-App/compare/{'c' * 40}...{'9' * 40}"),
             js({"status": "ahead"}))
        r.on(("gh", "api", f"repos/{ship_common.ORG}/AA-CIS-App/compare/{'d' * 40}...{'9' * 40}"),
             js({"status": "ahead"}))
        reads = iter([{"git_sha": "1" * 40}, {"git_sha": "1" * 40}, {"git_sha": "9" * 40}])
        r.on(("gh", "api"), js({"status": "behind"}))
        urls = []

        def fetch(url):
            urls.append(url)
            return next(reads)

        code = ship_wave.main(["cis#1350", "cis#1351", "--wait-deploy"], runner=r, apply_fn=lambda o, n: 0,
                              fetch=fetch)
        self.assertEqual(code, 0, self.out.getvalue())
        self.assertEqual(set(urls), {ship_wave.DEPLOY_URL["AA-CIS-App"]})
        self.assertEqual(len(urls), 3)  # one wait for the app, not one per PR
        self.assertIn("contains 2 merge(s)", self.out.getvalue())

    def test_wait_deploy_timeout_is_exit_5(self):
        r = scripted([1350], Recorder())
        r.on(("gh", "api"), js({"status": "behind"}))
        code = ship_wave.main(["cis#1350", "--wait-deploy", "--deploy-timeout", "60"], runner=r,
                              apply_fn=lambda o, n: 0, fetch=lambda url: {"git_sha": "1" * 40})
        self.assertEqual(code, 5)

    def test_dry_run_touches_nothing(self):
        r = FakeRunner()
        code = ship_wave.main(["cis#1349>apply:cis/383", "cis#1351@after=cis/383", "--dry-run"], runner=r)
        self.assertEqual(code, 0)
        self.assertEqual(r.calls, [])

    def test_merge_marks_the_gate_for_as_app(self):
        import os
        os.environ.pop(ship_common.GATE_ENV, None)
        r = scripted([1350], Recorder())
        ship_wave.main(["cis#1350"], runner=r, apply_fn=lambda o, n: 0, fetch=lambda url: {})
        self.assertEqual(os.environ.get(ship_common.GATE_ENV), "ship_merge")
        os.environ.pop(ship_common.GATE_ENV, None)


MIG = "api/migrations/400_add_widget.sql"
MIG_SQL = "CREATE TABLE demo.widget (id int);\n"


class StackedBranchTest(unittest.TestCase):
    """update_stacked_branch on real git: a bare origin, a 'clone' (the app checkout) and an 'other' clone that plays
    the lane and GitHub's squash merge. gh and as-app.sh are scripted; the scripted push runs the real git push."""

    def setUp(self):
        self.s = GitSandbox()
        self.out = io.StringIO()
        self._redirect = contextlib.redirect_stdout(self.out)
        self._redirect.__enter__()
        self.tmp_wt = os.path.join(self.s.tmp.name, "tmp-wt")
        self._patches = [mock.patch.object(ship_wave, "local_checkout", lambda repo: Path(self.s.wt)),
                         mock.patch.object(ship_wave, "TMP_WT", Path(self.tmp_wt)),
                         mock.patch.dict(os.environ, {"AA_PREPUSH_SKIP_INTEGRATION": ""})]
        for p in self._patches:
            p.start()
        self.pushes: list[list[str]] = []

    def tearDown(self):
        for p in reversed(self._patches):
            p.stop()
        self._redirect.__exit__(None, None, None)
        self.s.close()

    # -- scenario helpers ------------------------------------------------------------------------------------------

    def git(self, cwd, *args):
        return self.s.git(cwd, *args)

    def stacked_branch(self, *, main_sql: str = MIG_SQL, extra_code: dict | None = None) -> str:
        """Lane: feat/mig adds the migration, feat/code is stacked on it; then the migration PR squash-merges (main
        gets the same file under another commit, plus an unrelated commit). Return the code head."""
        o = self.s.other
        self.git(o, "checkout", "-q", "-b", "feat/mig", "origin/main")
        self.s.commit(o, MIG, MIG_SQL, "feat: add widget table")
        self.git(o, "checkout", "-q", "-b", "feat/code")
        self.s.commit(o, "api/widget.py", "WIDGET = 1\n", "feat: widget reader")
        for path, text in (extra_code or {}).items():
            self.s.commit(o, path, text, f"chore: {path}")
        self.git(o, "push", "-q", "origin", "feat/mig", "feat/code")
        head = self.git(o, "rev-parse", "HEAD")
        self.git(o, "checkout", "-q", "main")
        self.s.commit(o, MIG, main_sql, "feat: add widget table (#1)")
        self.s.commit(o, "docs/other.md", "unrelated\n", "docs: unrelated")
        self.git(o, "push", "-q", "origin", "main")
        return head

    def runner(self, head: str, *, push_result: Result | None = None, bash: list | None = None) -> HybridRunner:
        r = HybridRunner()
        r.on(("gh", "pr", "view", "7"), Result(0, json.dumps(pr(7, head=head, branch="feat/code"))))

        def push(argv):
            self.pushes.append(argv)
            if push_result is not None:
                return push_result
            return Runner().run(argv[argv.index("--") + 1:], timeout=120)

        r.on((ship_common.AS_APP,), push)
        r.on(("bash",), *(bash or [Result(0, "integration: passed; stamp x written")]))
        return r

    def remote(self, ref: str) -> str:
        self.git(self.s.wt, "fetch", "-q", "origin")
        return self.git(self.s.wt, "rev-parse", f"origin/{ref}")

    def tmp_worktrees(self) -> list[str]:
        return sorted(os.listdir(self.tmp_wt)) if os.path.isdir(self.tmp_wt) else []

    # -- cases -----------------------------------------------------------------------------------------------------

    def test_stacked_branch_gets_main_merged_and_pushed_without_force(self):
        head = self.stacked_branch()
        r = self.runner(head)
        new = ship_wave.update_stacked_branch(r, "AA-CIS-App", 7)
        self.assertEqual(new, self.remote("feat/code"))
        self.assertNotEqual(new, head)
        # a fast-forward of the old head (no force), now containing main, and the PR diff lost the migration
        self.git(self.s.wt, "merge-base", "--is-ancestor", head, "origin/feat/code")
        self.git(self.s.wt, "merge-base", "--is-ancestor", "origin/main", "origin/feat/code")
        diff = self.git(self.s.wt, "diff", "--name-only", "origin/main...origin/feat/code").split()
        self.assertEqual(diff, ["api/widget.py"])
        argv = self.pushes[0]
        self.assertNotIn("--force", " ".join(argv))
        self.assertIn(f"core.hooksPath={ship_wave.SAFE_HOOKS}", argv)
        self.assertEqual(argv[-1], "HEAD:refs/heads/feat/code")
        self.assertEqual(self.tmp_worktrees(), [])  # the temporary worktree is removed
        log = self.out.getvalue()
        self.assertIn(f"still carries {MIG}, already on main", log)
        self.assertIn("temporary worktree", log)
        self.assertIn("pushed", log)

    def test_clean_lane_worktree_is_reused(self):
        head = self.stacked_branch()
        lane = os.path.join(self.s.tmp.name, "lane")
        self.git(self.s.wt, "fetch", "-q", "origin")
        self.git(self.s.wt, "worktree", "add", "-q", "-b", "feat/code", lane, "origin/feat/code")
        new = ship_wave.update_stacked_branch(self.runner(head), "AA-CIS-App", 7)
        self.assertEqual(self.git(lane, "rev-parse", "HEAD"), new)
        self.assertEqual(new, self.remote("feat/code"))
        self.assertEqual(self.tmp_worktrees(), [])
        self.assertIn(f"reusing the clean lane worktree {lane}", self.out.getvalue())

    def test_lane_worktree_with_modified_files_is_left_alone(self):
        head = self.stacked_branch()
        lane = os.path.join(self.s.tmp.name, "lane")
        self.git(self.s.wt, "fetch", "-q", "origin")
        self.git(self.s.wt, "worktree", "add", "-q", "-b", "feat/code", lane, "origin/feat/code")
        with open(os.path.join(lane, "api", "widget.py"), "w", encoding="utf-8") as fh:
            fh.write("WIDGET = 2\n")
        new = ship_wave.update_stacked_branch(self.runner(head), "AA-CIS-App", 7)
        self.assertEqual(new, self.remote("feat/code"))
        self.assertEqual(self.git(lane, "rev-parse", "HEAD"), head)  # untouched, edit kept
        self.assertIn("M api/widget.py", self.git(lane, "status", "--porcelain"))
        self.assertIn("not clean: not reused", self.out.getvalue())

    def test_branch_without_a_main_migration_is_left_as_is(self):
        o = self.s.other
        self.git(o, "checkout", "-q", "-b", "feat/code", "origin/main")
        head = self.s.commit(o, "api/widget.py", "WIDGET = 1\n", "feat: widget reader")
        self.git(o, "push", "-q", "origin", "feat/code")
        r = self.runner(head)
        self.assertIsNone(ship_wave.update_stacked_branch(r, "AA-CIS-App", 7))
        self.assertEqual(self.pushes, [])
        self.assertIn("already contains origin/main: gating as is", self.out.getvalue())

    def test_code_branch_built_before_the_migration_merged_gets_main_merged(self):
        # S277 (Booking #224, #229): the code branch was cut from main before the migration PR merged, so it carries
        # no migration file but is behind main; its PR checks ran without the migration. Main is merged in and pushed.
        o = self.s.other
        self.git(o, "checkout", "-q", "-b", "feat/code", "origin/main")
        head = self.s.commit(o, "api/widget.py", "WIDGET = 1\n", "feat: widget reader")
        self.git(o, "push", "-q", "origin", "feat/code")
        self.git(o, "checkout", "-q", "main")
        self.s.commit(o, MIG, MIG_SQL, "feat: add widget table (#1)")
        self.git(o, "push", "-q", "origin", "main")
        new = ship_wave.update_stacked_branch(self.runner(head), "AA-CIS-App", 7)
        self.assertEqual(new, self.remote("feat/code"))
        self.git(self.s.wt, "merge-base", "--is-ancestor", head, "origin/feat/code")
        self.git(self.s.wt, "merge-base", "--is-ancestor", "origin/main", "origin/feat/code")
        self.assertNotIn("--force", " ".join(self.pushes[0]))
        self.assertIn("is behind origin/main", self.out.getvalue())

    def test_own_new_migration_is_not_mistaken_for_a_stacked_one(self):
        # A code branch that adds a migration main does not have (a normal expand PR) is not touched.
        o = self.s.other
        self.git(o, "checkout", "-q", "-b", "feat/code", "origin/main")
        head = self.s.commit(o, "api/migrations/401_more.sql", "SELECT 1;\n", "feat: more")
        self.git(o, "push", "-q", "origin", "feat/code")
        self.assertIsNone(ship_wave.update_stacked_branch(self.runner(head), "AA-CIS-App", 7))
        self.assertEqual(self.pushes, [])

    def test_conflict_stops_with_a_clear_message_and_pushes_nothing(self):
        head = self.stacked_branch(main_sql="CREATE TABLE demo.widget (id bigint);\n")  # main's squash differs
        with self.assertRaises(ShipError) as cm:
            ship_wave.update_stacked_branch(self.runner(head), "AA-CIS-App", 7)
        self.assertEqual(cm.exception.code, 4)
        self.assertIn(f"conflicts in {MIG}", str(cm.exception))
        self.assertIn("not resolved automatically", str(cm.exception))
        self.assertEqual(self.pushes, [])
        self.assertEqual(self.remote("feat/code"), head)
        self.assertEqual(self.tmp_worktrees(), [])

    def test_integration_mode_runs_before_the_push(self):
        head = self.stacked_branch(extra_code={"scripts/pre-push.sh": "case $1 in --integration) ;; esac\n"})
        r = self.runner(head)
        ship_wave.update_stacked_branch(r, "AA-CIS-App", 7)
        order = [c[0] for c in r.calls if c[0] in ("bash", ship_common.AS_APP)]
        self.assertEqual(order, ["bash", ship_common.AS_APP])
        self.assertEqual(r.called("bash")[0][-2:][0], "ship-wave")
        self.assertIn("pre-push.sh --integration", r.called("bash")[0][2])

    def test_failed_integration_keeps_the_merge_and_pushes_nothing(self):
        head = self.stacked_branch(extra_code={"scripts/pre-push.sh": "case $1 in --integration) ;; esac\n"})
        r = self.runner(head, bash=[Result(1, "!! [integration] failed (exit 1): no stamp written")])
        with self.assertRaises(ShipError) as cm:
            ship_wave.update_stacked_branch(r, "AA-CIS-App", 7)
        self.assertIn("the merge is kept in", str(cm.exception))
        self.assertEqual(self.pushes, [])
        self.assertEqual(len(self.tmp_worktrees()), 1)

    def test_skip_integration_env_skips_the_run(self):
        head = self.stacked_branch(extra_code={"scripts/pre-push.sh": "case $1 in --integration) ;; esac\n"})
        r = self.runner(head)
        with mock.patch.dict(os.environ, {"AA_PREPUSH_SKIP_INTEGRATION": "1"}):
            ship_wave.update_stacked_branch(r, "AA-CIS-App", 7)
        self.assertEqual(r.called("bash"), [])
        self.assertEqual(len(self.pushes), 1)

    def test_refused_push_reports_the_hook_and_keeps_the_merge(self):
        head = self.stacked_branch()
        refused = Result(1, "", "FAIL  unit  2 failed\nerror: failed to push some refs")
        with self.assertRaises(ShipError) as cm:
            ship_wave.update_stacked_branch(self.runner(head, push_result=refused), "AA-CIS-App", 7)
        self.assertIn("FAIL  unit  2 failed", str(cm.exception))
        self.assertIn("no force", str(cm.exception))
        self.assertEqual(self.remote("feat/code"), head)
        self.assertEqual(len(self.tmp_worktrees()), 1)

    def test_merged_pr_is_not_touched(self):
        r = HybridRunner()
        r.on(("gh", "pr", "view", "7"), Result(0, json.dumps(pr(7, state="MERGED", merge_oid="e" * 40))))
        self.assertIsNone(ship_wave.update_stacked_branch(r, "AA-CIS-App", 7))
        self.assertEqual([c for c in r.calls if c[0] == "git"], [])


if __name__ == "__main__":
    unittest.main()
