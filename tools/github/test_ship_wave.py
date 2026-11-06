"""Tests for ship_wave.py (AA-1024 G1). Offline: gh/aws scripted, migrations and health reads injected.

Run: python -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import threading
import unittest

import ship_common
import ship_wave
from ship_common import Result, ShipError
from ship_fakes import FakeRunner, pr

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

    def tearDown(self):
        self._redirect.__exit__(None, None, None)

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


if __name__ == "__main__":
    unittest.main()
