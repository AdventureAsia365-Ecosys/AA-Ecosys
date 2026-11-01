"""Tests for ship_copy_apply.py (AA-1032). Offline: gh, as-app.sh and the readiness endpoint are scripted.

Run: python -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import base64
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ship_common
import ship_copy_apply as sca
from ship_common import Result, ShipError
from ship_fakes import FakeRunner, pr

T0 = "2026-10-28T03:00:00Z"  # FakeRunner clock starts 2026-10-26T07:33:20Z
LATER = "2026-10-28T03:30:00Z"


def js(obj) -> Result:
    return Result(0, json.dumps(obj))


def content(text: str) -> Result:
    return js({"content": base64.b64encode(text.encode()).decode()})


def run_row(rid: int, title: str = "DB Migrate (shared RDS)", created: str = LATER) -> dict:
    return {"databaseId": rid, "createdAt": created, "displayTitle": title, "status": "queued",
            "url": f"https://github.com/x/y/actions/runs/{rid}"}


class ParseTest(unittest.TestCase):
    def test_targets(self):
        self.assertEqual(sca.parse_target("crm", "crm-038"), ("crm", "038", None))
        self.assertEqual(sca.parse_target("bk", "035_ops_view.sql"), ("booking", "035", "035_ops_view.sql"))
        self.assertEqual(sca.parse_target("cis", "cis/330_x.sql"), ("cis", "330", "330_x.sql"))
        self.assertEqual(sca.parse_target("tp", "tp-021"), ("tripplanner", "021", None))
        for owner, target in (("shared", "001"), ("cis", "abc"), ("cis", "33")):
            with self.assertRaises(ShipError):
                sca.parse_target(owner, target)
        self.assertEqual(sca.parse_target("roles", "rl-004"), ("roles", "004", None))
        self.assertEqual(sca.ready_key("booking", "035"), "bk-035")
        self.assertEqual(sca.ready_key("cis", "330"), "330")


class DbmigWrapperTest(unittest.TestCase):
    def test_usage_errors_exit_2_before_any_call(self):
        script = str(Path(__file__).resolve().parent / "dbmig.sh")
        for args in (["cis", "apply"], ["cis/330", "deploy"]):
            p = subprocess.run(["bash", script, *args], capture_output=True, text=True, timeout=30)
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)


class CopyPrTest(unittest.TestCase):
    def test_open_wins_closed_ignored_latest_merged(self):
        head = "bot/migration-copy/cis-329"
        rows = [{"number": 591, "state": "CLOSED", "headRefName": head, "createdAt": "1"},
                {"number": 592, "state": "MERGED", "headRefName": head, "mergedAt": "2026-11-01T12:00:00Z"},
                {"number": 580, "state": "MERGED", "headRefName": head, "mergedAt": "2026-10-30T12:00:00Z"}]
        r = FakeRunner().on(("gh", "pr", "list"), js(rows))
        self.assertEqual(sca.find_copy_pr(r, "cis", "329")["number"], 592)
        r = FakeRunner().on(("gh", "pr", "list"), js(rows + [{"number": 600, "state": "OPEN", "headRefName": head}]))
        self.assertEqual(sca.find_copy_pr(r, "cis", "329")["number"], 600)
        r = FakeRunner().on(("gh", "pr", "list"), js(rows[:1]))
        self.assertIsNone(sca.find_copy_pr(r, "cis", "329"))

    def test_file_class_from_the_leading_comment_block(self):
        cases = {
            "-- migrate: expand\n-- adds a column\nALTER TABLE x ADD COLUMN y int;\n": "expand",
            "-- crm-040: drop a table\n-- migrate: destructive\nDROP TABLE x;\n": "destructive",
            "-- migrate: lock_timeout=10s\nCREATE POLICY p ON x;\n": "contract",
            "CREATE TABLE x (id int);\n-- migrate: expand\n": "contract",
        }
        for text, want in cases.items():
            r = FakeRunner().on(("gh", "api"), content(text))
            self.assertEqual(sca.file_class(r, "crm/040_x.sql"), want, text)


class OwnRunTest(unittest.TestCase):
    def test_takes_the_run_titled_for_this_file_not_the_latest(self):
        # S263: another file's apply was dispatched right after ours; "the latest run" was the other one.
        before = {1, 2}
        runs = [run_row(4, "DB Migrate apply crm/037_y.sql"), run_row(3, "DB Migrate apply cis/330_x.sql"),
                run_row(2), run_row(1)]
        since = sca._ts(T0)
        self.assertEqual(sca.pick_own_run(before, runs, since, "DB Migrate apply cis/330_x.sql")["databaseId"], 3)

    def test_untitled_runs_one_is_taken_two_are_refused(self):
        since = sca._ts(T0)
        self.assertEqual(sca.pick_own_run({1}, [run_row(5), run_row(1)], since, "DB Migrate apply a")["databaseId"],
                         5)
        with self.assertRaises(ShipError):
            sca.pick_own_run({1}, [run_row(6), run_row(5), run_row(1)], since, "DB Migrate apply a")
        self.assertIsNone(sca.pick_own_run({1}, [run_row(1)], since, "DB Migrate apply a"))
        # A run created before the dispatch is never ours, even if it was not in the first listing.
        old = run_row(7, created="2026-10-27T00:00:00Z")
        self.assertIsNone(sca.pick_own_run({1}, [old], since, "DB Migrate apply a"))


class MainFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lock = mock.patch.object(sca, "LOCK_FILE", Path(self.tmp.name) / "lock")
        self.lock.start()
        self.out = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.out)
        self.redirect.__enter__()

    def tearDown(self):
        self.redirect.__exit__(None, None, None)
        self.lock.stop()
        self.tmp.cleanup()

    def runner(self, header: str, *, conclusion: str = "success", copy_state: str = "OPEN") -> FakeRunner:
        fname = "038_crm_workflows.sql"
        state = {"dispatched": False, "merged": copy_state == "MERGED"}
        head = "bot/migration-copy/crm-038"

        def copy_list(argv):
            st = "MERGED" if state["merged"] else copy_state
            return js([{"number": 589, "state": st, "headRefName": head, "labels": [{"name": "migration:contract"}],
                        "mergedAt": T0, "createdAt": T0}])

        def copy_view(argv):
            return js(pr(589, state="MERGED", merge_oid="5" * 40) if state["merged"] else pr(589))

        def app(argv):
            if "merge" in argv:
                state["merged"] = True
            if "workflow" in argv:
                state["dispatched"] = True
                state["mode"] = [a for a in argv if a.startswith("mode=")][0][5:]
            return Result(0, "")

        def runs(argv):
            rows = [run_row(10, "DB Migrate apply cis/329_z.sql", created="2026-10-27T00:00:00Z")]
            if state["dispatched"]:
                rows = [run_row(12, "DB Migrate apply cis/330_other.sql"),
                        run_row(11, f"DB Migrate {state['mode']} crm/{fname}")] + rows
            return js(rows)

        r = FakeRunner()
        r.on(("aws",), js({"Expiration": "2026-10-28T12:00:00Z"}))
        r.on(("gh", "pr", "list"), copy_list)
        r.on(("gh", "pr", "view"), copy_view)
        r.on(("gh", "api", f"repos/{sca.INFRA_SLUG}/pulls/589/files?per_page=100"), Result(0, "[]\n"))
        r.on(("gh", "api", f"repos/{sca.INFRA_SLUG}/contents/db/migrations/crm?ref=main"),
             lambda argv: Result(0, f"037_x.sql\n{fname}\n") if state["merged"] else Result(0, "037_x.sql\n"))
        r.on(("gh", "api", f"repos/{sca.INFRA_SLUG}/contents/db/migrations/crm/{fname}?ref=main"), content(header))
        r.on((ship_common.AS_APP,), app)
        r.on(("gh", "run", "list"), runs)
        r.on(("gh", "run", "view", "11", "status,conclusion"),
             js({"status": "in_progress"}), js({"status": "completed", "conclusion": conclusion}))
        r.on(("gh", "run", "view", "11", "jobs"), js({"jobs": [{"databaseId": 77}]}))
        r.on(("gh", "api", f"repos/{sca.INFRA_SLUG}/actions/jobs/77/logs"),
             Result(0, "2026-10-28T03:01:00.0000000Z MIGRATE ran as: crm_owner\n"
                       "2026-10-28T03:01:01.0000000Z ##[group]Run something\n"
                       "2026-10-28T03:01:02.0000000Z applied crm/038 in 1.2s\n"))
        return r

    @staticmethod
    def ready(keys):
        return lambda url: {"status": "ok", "schema_version": keys[-1], "registered_keys": keys}

    @staticmethod
    def ready_after_dispatch(r: FakeRunner):
        """crm-038 shows up in registered_keys only once a DB Migrate run was dispatched."""
        def fetch(url):
            keys = ["crm-037"] + (["crm-038"] if r.called("workflow") else [])
            return {"status": "ok", "schema_version": keys[-1], "registered_keys": keys}
        return fetch

    def test_contract_copy_merged_dispatched_own_run_followed(self):
        r = self.runner("-- crm-038: tasks\nCREATE TABLE crm.task (id int);\n")
        code = sca.main(["crm", "crm-038"], runner=r, fetch=self.ready_after_dispatch(r))
        out = self.out.getvalue()
        self.assertEqual(code, 0, out)
        merge = [c for c in r.called(ship_common.AS_APP) if "merge" in c][0]
        self.assertIn("589", merge)
        [dispatch] = [c for c in r.called(ship_common.AS_APP) if "workflow" in c]
        self.assertIn("migration=crm/038_crm_workflows.sql", dispatch)
        self.assertIn("mode=apply", dispatch)
        self.assertIn("run=11 conclusion=success", out)
        self.assertFalse(r.called("gh", "run", "view", "12"))
        self.assertIn("MIGRATE ran as: crm_owner", out)
        self.assertNotIn("##[group]", out)
        self.assertIn("key crm-038 registered=yes", out)

    def test_already_merged_copy_is_found(self):
        r = self.runner("CREATE TABLE crm.task (id int);\n", copy_state="MERGED")
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready_after_dispatch(r)), 0)
        self.assertFalse([c for c in r.called(ship_common.AS_APP) if "merge" in c])
        self.assertEqual(len([c for c in r.called(ship_common.AS_APP) if "workflow" in c]), 1)

    def test_key_already_registered_is_not_dispatched(self):
        # Dev Migration Apply applied the contract file on its own (AA-1032 part 1).
        r = self.runner("CREATE TABLE crm.task (id int);\n", copy_state="MERGED")
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready(["crm-037", "crm-038"])), 0)
        self.assertFalse([c for c in r.called(ship_common.AS_APP) if "workflow" in c])
        self.assertIn("already registered; not dispatching", self.out.getvalue())

    def test_red_run_but_applied_by_another_run_passes_with_a_warning(self):
        # Exit 17: Migration Apply held the apply lock and applied the file itself.
        r = self.runner("CREATE TABLE crm.task (id int);\n", conclusion="failure", copy_state="MERGED")
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready_after_dispatch(r)), 0)
        self.assertIn("applied by another run", self.out.getvalue())

    def test_expand_is_not_dispatched_and_destructive_is_refused(self):
        r = self.runner("-- migrate: expand\nALTER TABLE crm.task ADD COLUMN x int;\n")
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready(["crm-038"])), 0)
        self.assertFalse([c for c in r.called(ship_common.AS_APP) if "workflow" in c])
        r = self.runner("-- migrate: destructive\nDROP TABLE crm.old;\n")
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready(["crm-038"])), 4)
        self.assertFalse([c for c in r.called(ship_common.AS_APP) if "workflow" in c])

    def test_red_run_and_unregistered_key_fail(self):
        r = self.runner("CREATE TABLE crm.task (id int);\n", conclusion="failure")
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready(["crm-037"])), 1)
        r = self.runner("CREATE TABLE crm.task (id int);\n")
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready(["crm-037"])), 1)
        self.assertIn("key crm-038 registered=no", self.out.getvalue())

    def test_red_copy_pr_is_not_merged(self):
        r = self.runner("CREATE TABLE crm.task (id int);\n")
        from ship_fakes import check
        r.rules.insert(0, (("gh", "pr", "view"), [js(pr(589, checks=[check("Copies match owner main",
                                                                           "FAILURE")]))]))
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready(["crm-038"])), 3)
        self.assertFalse(r.called(ship_common.AS_APP))

    def test_no_copy_mode_dispatches_without_looking_for_a_pr(self):
        r = self.runner("-- migrate: expand\nALTER TABLE crm.task ADD COLUMN x int;\n", copy_state="MERGED")
        self.assertEqual(sca.main(["crm", "038", "--no-copy", "--mode", "check"], runner=r,
                                  fetch=self.ready(["crm-038"])), 0)
        self.assertFalse(r.called("gh", "pr", "list"))
        [dispatch] = [c for c in r.called(ship_common.AS_APP) if "workflow" in c]
        self.assertIn("mode=check", dispatch)


if __name__ == "__main__":
    unittest.main()
