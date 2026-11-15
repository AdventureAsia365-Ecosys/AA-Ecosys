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
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import ship_common
import ship_deploy
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
             dirty: tuple = (), files: dict | None = None, heartbeats: list | None = None) -> FakeRunner:
    """A FakeRunner where each PR is OPEN and green until its merge call ran, then MERGED.

    wait_for {a: b}: the merge call of PR a blocks until the merge call of PR b has STARTED (proves parallelism:
    a serial run would wait for ever, so the call gives up after 5 s and fails).
    files {n: [paths]}: the PR's changed files (default none: docs-only, no deploy, no ECS exec check).
    heartbeats: the scripts/out/ listing the ECS exec guard reads (default empty)."""
    started = {n: threading.Event() for n in numbers}
    merged: set[int] = set()
    r = FakeRunner()
    r.on(("export-credentials",), Result(1, "", "no session"))

    def paginate(argv):
        if any("removed" in a for a in argv):  # removed_files: the gate's deletion check
            return Result(0, "[]\n")
        n = int(next(a for a in argv if "/pulls/" in a).split("/pulls/")[1].split("/")[0])
        return js((files or {}).get(n, ["docs/notes.md"]))

    def listing(argv):  # heartbeats: (key, age in seconds at the time of the read, on the fake clock)
        return js([{"Key": k, "LastModified": datetime.fromtimestamp(r.t - age, tz=timezone.utc).isoformat()}
                   for k, age in (heartbeats or [])])

    r.on(("--paginate",), paginate)
    r.on(("s3api", "list-objects-v2"), listing)

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

    def test_busy_job_tables_hold_the_chain_and_the_wave_is_resumable(self):
        # S281: a recompute kept shared.job busy; the apply refused (exit 7), nothing ran. The held code PR and the
        # owner's higher migration are held (not failed), the independent PR merges, the exit is 7 with a RESUME line.
        rec = Recorder()
        r = scripted([1349, 1350, 1351], rec)
        calls = []

        def apply_fn(owner, nnn):
            calls.append(f"{owner}/{nnn}")
            return ship_wave.EXIT_HELD, "shared.job: recompute:running=1"

        code = ship_wave.main(["cis#1349>apply:cis/383,cis/384", "cis#1351@after=cis/384", "cis#1350"], runner=r,
                              apply_fn=apply_fn, fetch=lambda url: {})
        out = self.out.getvalue()
        self.assertEqual(code, ship_wave.EXIT_HELD, out)
        self.assertEqual(calls, ["cis/383"])  # 384 is never dispatched past a held 383 (owner order)
        self.assertIn("cis/383: apply held: job tables busy (shared.job: recompute:running=1)", out)
        self.assertIn("AA-CIS-App#1351: held - held: migration(s) cis/384 not applied yet", out)
        self.assertIn("apply cis/384: HELD (apply held: job tables busy", out)
        self.assertIn("RESUME: the wave is held, not failed", out)
        self.assertIn("merged 1350", rec.events)
        self.assertNotIn("merge-start 1351", rec.events)
        self.assertIn("RESUME", out)

    def test_wait_idle_redispatches_until_the_apply_goes_through(self):
        rec = Recorder()
        r = scripted([1349, 1351], rec)
        naps = []
        real_sleep = r.sleep
        r.sleep = lambda s: (naps.append(s), real_sleep(s))
        answers = iter([(ship_wave.EXIT_HELD, "shared.job: recompute:running=1"),
                        (ship_wave.EXIT_HELD, "shared.job: recompute:queued=1"), 0])
        calls = []

        def apply_fn(owner, nnn):
            calls.append(nnn)
            return next(answers)

        code = ship_wave.main(["cis#1349>apply:cis/383", "cis#1351@after=cis/383", "--wait-idle", "3"], runner=r,
                              apply_fn=apply_fn, fetch=lambda url: {})
        out = self.out.getvalue()
        self.assertEqual(code, 0, out)
        self.assertEqual(calls, ["383", "383", "383"])
        self.assertEqual(naps.count(ship_wave.IDLE_INTERVAL), 2)  # 5 minutes apart, once per re-dispatch
        self.assertIn("re-dispatching in 300s (--wait-idle 1/3)", out)
        self.assertIn("merged 1351", rec.events)
        self.assertNotIn("RESUME", out)

    def test_wait_idle_gives_up_after_n_and_stays_held(self):
        r = scripted([1349], Recorder())
        calls = []

        def apply_fn(owner, nnn):
            calls.append(nnn)
            return ship_wave.EXIT_HELD, ""

        code = ship_wave.main(["cis#1349>apply:cis/383", "--wait-idle", "2"], runner=r, apply_fn=apply_fn,
                              fetch=lambda url: {})
        self.assertEqual(code, ship_wave.EXIT_HELD, self.out.getvalue())
        self.assertEqual(len(calls), 3)  # the first try and 2 re-dispatches
        self.assertIn("apply held: job tables busy (busy)", self.out.getvalue())

    def test_a_real_failure_wins_over_a_hold(self):
        r = scripted([1349, 1352, 1350], Recorder(), dirty=(1350,))
        code = ship_wave.main(["cis#1349>apply:cis/383", "cis#1352>apply:crm/41", "cis#1350"], runner=r,
                              apply_fn=lambda o, n: (ship_wave.EXIT_HELD, "x") if o == "cis" else 1,
                              fetch=lambda url: {})
        self.assertEqual(code, 4, self.out.getvalue())
        self.assertEqual(ship_wave.final_exit([0, ship_wave.EXIT_HELD, 5]), 5)
        self.assertEqual(ship_wave.final_exit([0, ship_wave.EXIT_HELD]), ship_wave.EXIT_HELD)
        self.assertEqual(ship_wave.final_exit([0, 0]), 0)

    def test_plan_names_the_busy_rule_when_the_wave_applies(self):
        lines = ship_wave.plan_lines(ship_wave.parse_items(["cis#1349>apply:cis/383", "cis#1350"]))
        self.assertIn("apply held: job tables busy", lines[-1])
        self.assertNotIn("note:", " ".join(ship_wave.plan_lines(ship_wave.parse_items(["cis#1350"]))))

    def test_wait_idle_must_not_be_negative(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(ship_wave.main(["cis#1350", "--wait-idle", "-1"], runner=FakeRunner()), 2)

    def test_default_apply_passes_the_hold_reason_from_copy_apply(self):
        seen = {}

        def fake_main(argv, runner=None, fetch=None, report=None):
            seen["argv"] = argv
            report["held"] = "crm.job: send_mail:running=1"
            return ship_wave.EXIT_HELD

        r = scripted([1352], Recorder())
        with mock.patch.object(ship_wave.ship_copy_apply, "main", fake_main):
            code = ship_wave.main(["cis#1352>apply:crm/41"], runner=r, fetch=lambda url: {})
        self.assertEqual(code, ship_wave.EXIT_HELD, self.out.getvalue())
        self.assertEqual(seen["argv"], ["crm", "041"])
        self.assertIn("crm/041: apply held: job tables busy (crm.job: send_mail:running=1)", self.out.getvalue())

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
        r = scripted([1350, 1351], rec, files={1350: ["api/routers/x.py"], 1351: ["shared/y.py"]})
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
        self.assertEqual(set(urls), {ship_deploy.service("AA-CIS-App", "api").url})
        self.assertEqual(len(urls), 3)  # one wait for the app, not one per PR
        self.assertIn("contains 2 merge(s)", self.out.getvalue())

    def test_wait_deploy_timeout_is_exit_5(self):
        r = scripted([1350], Recorder(), files={1350: ["api/x.py"]})
        r.on(("gh", "api"), js({"status": "behind"}))
        code = ship_wave.main(["cis#1350", "--wait-deploy", "--deploy-timeout", "60"], runner=r,
                              apply_fn=lambda o, n: 0, fetch=lambda url: {"git_sha": "1" * 40})
        self.assertEqual(code, 5)

    def _partner_wave(self, files: list[str], live: dict) -> tuple[int, list[str], str]:
        """One Partner PR (#323) with `files`; `live` maps a health URL to the commit it serves."""
        merged = "a" * 40  # what scripted() reports for a merged PR without a MERGE_SHA entry
        r = scripted([323], Recorder(), files={323: files})
        r.rules.insert(0, (("gh", "api", f"repos/{ship_common.ORG}/AA-Partner/compare/{merged}...{'1' * 40}"),
                           [js({"status": "behind"})]))
        urls: list[str] = []

        def fetch(url):
            urls.append(url)
            return {"git_sha": live.get(url, "1" * 40)}

        code = ship_wave.main(["crm#323", "--wait-deploy", "--deploy-timeout", "60"], runner=r,
                              apply_fn=lambda o, n: 0, fetch=fetch)
        return code, urls, self.out.getvalue()

    def test_web_only_partner_pr_waits_on_the_crm_web_not_the_api(self):
        # S281 #323: only web/ changed; the web /healthz already serves the merge, the API keeps its old commit.
        web, api = ship_deploy.service("AA-Partner", "web"), ship_deploy.service("AA-Partner", "api")
        code, urls, out = self._partner_wave(["web/app/page.tsx", "web/tests/x.test.ts"], {web.url: "a" * 40})
        self.assertEqual(code, 0, out)
        self.assertEqual(set(urls), {web.url})
        self.assertNotIn(api.url, urls)
        self.assertIn("deploy AA-Partner web: live aaaaaaaa contains 1 merge(s)", out)

    def test_api_only_partner_pr_waits_on_the_crm_api(self):
        api = ship_deploy.service("AA-Partner", "api")
        code, urls, out = self._partner_wave(["api/app/routers/x.py"], {api.url: "a" * 40})
        self.assertEqual(code, 0, out)
        self.assertEqual(set(urls), {api.url})

    def test_partner_pr_touching_both_waits_on_both(self):
        web, api = ship_deploy.service("AA-Partner", "web"), ship_deploy.service("AA-Partner", "api")
        code, urls, out = self._partner_wave(["api/app/x.py", "web/lib/y.ts"], {api.url: "a" * 40})
        self.assertEqual(code, 5, out)  # the web never served the merge: that service times out, named
        self.assertEqual(set(urls), {api.url, web.url})
        self.assertIn(f"ERROR deploy AA-Partner web: {web.url} still 11111111", out)

    def test_docs_only_partner_pr_expects_no_deploy(self):
        code, urls, out = self._partner_wave(["docs/guide.md", "api/tests/unit/test_x.py", "api/migrations/050_x.sql"],
                                             {})
        self.assertEqual(code, 0, out)
        self.assertEqual(urls, [])
        self.assertIn("deploy AA-Partner#323: no deploy expected", out)

    def test_unreadable_file_list_waits_on_every_service_of_the_repo(self):
        r = scripted([323], Recorder())
        r.rules.insert(0, (("--paginate", "repos/AdventureAsia365-Ecosys/AA-Partner/pulls/323/files?per_page=100",
                            "[.[] | .filename, (.previous_filename // empty)]"), [Result(1, "", "HTTP 502")]))
        plan_wave = ship_wave.Wave(r, ship_wave.parse_items(["crm#323"]), merge_kw={}, apply_fn=None, fetch=None,
                                   check_only=False)
        plan_wave.merged_sha["AA-Partner#323"] = "f" * 40
        plan_wave.results["AA-Partner#323"] = (0, "MERGED")
        plan = ship_wave.deploy_plan(r, plan_wave)
        self.assertEqual({s.name for s in plan}, {"api", "web"})
        self.assertIn("HTTP 502", self.out.getvalue())

    def test_running_ecs_exec_refuses_the_cis_backend_pr_only(self):
        # AA-1048: a fresh heartbeat holds the CIS api PR; the CIS frontend PR and the root PR merge.
        rec = Recorder()
        r = scripted([1350, 1351, 601], rec, repo_of={601: "AA-Ecosys"},
                     files={1350: ["api/x.py"], 1351: ["frontend/app/page.tsx"], 601: ["tools/x.py"]},
                     heartbeats=[("scripts/out/20261026T070000-42-recount.txt.running", 30)])
        code = ship_wave.main(["cis#1350", "cis#1351", "root#601"], runner=r, apply_fn=lambda o, n: 0,
                              fetch=lambda url: {})
        out = self.out.getvalue()
        self.assertEqual(code, 4, out)
        self.assertNotIn("merge-start 1350", rec.events)
        self.assertIn("merged 1351", rec.events)
        self.assertIn("merged 601", rec.events)
        self.assertIn("20261026T070000-42-recount (heartbeat 30s ago)", out)
        self.assertEqual(len(r.called("s3api")), 1)  # only the backend PR reads the heartbeats

    def test_allow_running_exec_lets_the_wave_merge_and_logs_it(self):
        rec = Recorder()
        r = scripted([1350], rec, files={1350: ["api/x.py"]},
                     heartbeats=[("scripts/out/run-1.txt.running", 10)])
        with mock.patch.object(ship_deploy, "OVERRIDE_LOG", Path(self._tmp.name) / "overrides.jsonl"):
            code = ship_wave.main(["cis#1350", "--allow-running-exec"], runner=r, apply_fn=lambda o, n: 0,
                                  fetch=lambda url: {})
            logged = (Path(self._tmp.name) / "overrides.jsonl").read_text()
        self.assertEqual(code, 0, self.out.getvalue())
        self.assertIn("merged 1350", rec.events)
        self.assertIn("WARN AA-CIS-App#1350: --allow-running-exec", self.out.getvalue())
        self.assertIn('"pr": "AA-CIS-App#1350"', logged)

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
