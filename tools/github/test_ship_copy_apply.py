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
GREEN_LOG = ("2026-10-28T03:01:00.0000000Z MIGRATE ran as: crm_owner\n"
             "2026-10-28T03:01:01.0000000Z ##[group]Run something\n"
             "2026-10-28T03:01:02.0000000Z applied crm/038 in 1.2s\n"
             "2026-10-28T03:01:03.0000000Z exit code: 0  status: STOPPED  stopped: Essential container exited\n")
# The step's script is printed in the log too: these words after `echo "` / `if [` are not the lock message.
SCRIPT_ECHO = ("2026-10-28T03:00:59.0000000Z   if [ \"$EXIT\" = \"17\" ]; then\n"
               "2026-10-28T03:00:59.0000000Z     echo \"::error::the apply lock is held by another DB Migrate run\"\n")
LOCK_LOG = (SCRIPT_ECHO + "2026-10-28T03:26:00.0000000Z exit code: 17  status: STOPPED  stopped: exited\n"
            "2026-10-28T03:26:00.0000000Z ##[error]the apply lock is held by another DB Migrate or auto-apply run\n")
POSTCHECK_LOG = (SCRIPT_ECHO + "2026-10-28T03:05:00.0000000Z exit code: 9  status: STOPPED  stopped: exited\n"
                 "2026-10-28T03:05:00.0000000Z ##[error]ownership post-check failed: clean up by hand\n")


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

    def runner(self, header: str, *, conclusion: str = "success", copy_state: str = "OPEN",
               job_log: str = GREEN_LOG, lower_open: tuple = ()) -> FakeRunner:
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

        def open_list(argv):
            rows = [{"number": 500 + int(n), "state": "OPEN", "headRefName": f"bot/migration-copy/crm-{n}"}
                    for n in lower_open]
            rows += [{"number": 700, "state": "OPEN", "headRefName": "bot/migration-copy/cis-020"},
                     {"number": 701, "state": "OPEN", "headRefName": "feat/crm-030-something"}]
            if not state["merged"] and copy_state == "OPEN":
                rows.append({"number": 589, "state": "OPEN", "headRefName": head})
            return js(rows)

        r = FakeRunner()
        r.on(("aws",), js({"Expiration": "2026-10-28T12:00:00Z"}))
        r.on(("gh", "pr", "list", "open"), open_list)
        r.on(("gh", "pr", "list"), copy_list)
        r.on(("gh", "pr", "view"), copy_view)
        r.on(("gh", "api", f"repos/{sca.INFRA_SLUG}/pulls/589/files?per_page=100"), Result(0, "[]\n"))
        r.on(("gh", "api", f"repos/{sca.INFRA_SLUG}/contents/db/migrations/crm?ref=main"),
             lambda argv: Result(0, f"036_w.sql\n037_x.sql\n{fname}\n") if state["merged"]
             else Result(0, "036_w.sql\n037_x.sql\n"))
        r.on(("gh", "api", f"repos/{sca.INFRA_SLUG}/contents/db/migrations/crm/{fname}?ref=main"), content(header))
        r.on((ship_common.AS_APP,), app)
        r.on(("gh", "run", "list"), runs)
        r.on(("gh", "run", "view", "11", "status,conclusion"),
             js({"status": "in_progress"}), js({"status": "completed", "conclusion": conclusion}))
        r.on(("gh", "run", "view", "11", "jobs"), js({"jobs": [{"databaseId": 77}]}))
        r.on(("gh", "api", f"repos/{sca.INFRA_SLUG}/actions/jobs/77/logs"), Result(0, job_log))
        return r

    @staticmethod
    def ready(keys):
        return lambda url: {"status": "ok", "schema_version": keys[-1], "registered_keys": keys}

    @staticmethod
    def ready_after_dispatch(r: FakeRunner):
        """crm-038 shows up in registered_keys only once a DB Migrate run was dispatched."""
        def fetch(url):
            keys = ["crm-036", "crm-037"] + (["crm-038"] if r.called("workflow") else [])
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

    def test_red_run_with_the_lock_held_and_the_key_registered_passes_with_a_warning(self):
        # Exit 17: Migration Apply held the apply lock (nothing ran here) and applied the file itself.
        r = self.runner("CREATE TABLE crm.task (id int);\n", conclusion="failure", copy_state="MERGED",
                        job_log=LOCK_LOG)
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready_after_dispatch(r)), 0)
        self.assertIn("applied by the run that held the lock", self.out.getvalue())

    def test_red_run_for_another_reason_fails_even_with_the_key_registered(self):
        # Exit 9: the post-check failed after COMMIT, so the key IS registered and the run needs hand cleanup.
        r = self.runner("CREATE TABLE crm.task (id int);\n", conclusion="failure", copy_state="MERGED",
                        job_log=POSTCHECK_LOG)
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready_after_dispatch(r)), 1)
        out = self.out.getvalue()
        self.assertIn("exit code: 9", out)
        self.assertNotIn("WARN run", out)

    def test_lock_line_match_ignores_the_printed_script(self):
        lines = [sca.re.sub(r"^\S+Z\s", "", x).strip() for x in POSTCHECK_LOG.splitlines()]
        self.assertFalse(sca.lock_held(lines))
        self.assertEqual(sca.exit_line(lines), "exit code: 9  status: STOPPED  stopped: exited")
        lines = [sca.re.sub(r"^\S+Z\s", "", x).strip() for x in LOCK_LOG.splitlines()]
        self.assertTrue(sca.lock_held(lines))

    def test_open_lower_copy_pr_refuses_merge_and_dispatch(self):
        # Migration Sync merges in owner order: crm-037's copy is still open.
        r = self.runner("CREATE TABLE crm.task (id int);\n", lower_open=("037",))
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready_after_dispatch(r)), 4)
        self.assertFalse(r.called(ship_common.AS_APP))
        self.assertIn("lower copy PRs still open: #537 (crm-037)", self.out.getvalue())
        r = self.runner("CREATE TABLE crm.task (id int);\n", copy_state="MERGED", lower_open=("037",))
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready_after_dispatch(r)), 4)
        self.assertFalse([c for c in r.called(ship_common.AS_APP) if "workflow" in c])

    def test_lower_file_not_registered_refuses_the_dispatch(self):
        # crm-037 is on Infra main but not applied on Dev: applying 038 would leave 037 out-of-order (AA-920).
        r = self.runner("CREATE TABLE crm.task (id int);\n", copy_state="MERGED")
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready(["crm-036"])), 4)
        self.assertFalse([c for c in r.called(ship_common.AS_APP) if "workflow" in c])
        self.assertIn("lower files not registered on Dev: crm-037", self.out.getvalue())
        # dbmig.sh path (--no-copy) is checked too, and --allow-out-of-order bypasses the check.
        r = self.runner("CREATE TABLE crm.task (id int);\n", copy_state="MERGED")
        self.assertEqual(sca.main(["crm", "038", "--no-copy"], runner=r, fetch=self.ready(["crm-036"])), 4)
        r = self.runner("CREATE TABLE crm.task (id int);\n", copy_state="MERGED")
        fetch = self.ready_after_dispatch(r)
        self.assertEqual(sca.main(["crm", "038", "--allow-out-of-order"], runner=r,
                                  fetch=lambda url: {**fetch(url), "registered_keys": [
                                      k for k in fetch(url)["registered_keys"] if k != "crm-037"]}), 0)
        self.assertEqual(len([c for c in r.called(ship_common.AS_APP) if "workflow" in c]), 1)

    def test_unreadable_readiness_refuses_the_dispatch(self):
        def down(url):
            raise OSError("connection refused")
        r = self.runner("CREATE TABLE crm.task (id int);\n", copy_state="MERGED")
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=down), 4)
        self.assertFalse([c for c in r.called(ship_common.AS_APP) if "workflow" in c])
        r = self.runner("CREATE TABLE crm.task (id int);\n", copy_state="MERGED")
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=lambda url: {"status": "degraded"}), 4)

    def test_cis_baseline_skips_legacy_unregistered_files(self):
        r = FakeRunner().on(("gh", "api"), Result(0, "232_a.sql\n263_b.sql\n264_c.sql\n330_d.sql\n331_e.sql\n"))
        body = {"status": "ok", "registered_keys": ["264", "330"], "keys_baseline": "263"}
        self.assertEqual(sca.unapplied_below(r, "cis", "331", lambda url: body), [])
        body["registered_keys"] = ["264"]
        self.assertEqual(sca.unapplied_below(r, "cis", "331", lambda url: body), ["330"])
        self.assertEqual(sca.unapplied_below(r, "tripplanner", "021", lambda url: body), [])

    def test_expand_is_not_dispatched_and_destructive_is_refused(self):
        r = self.runner("-- migrate: expand\nALTER TABLE crm.task ADD COLUMN x int;\n")
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready(["crm-038"])), 0)
        self.assertFalse([c for c in r.called(ship_common.AS_APP) if "workflow" in c])
        r = self.runner("-- migrate: destructive\nDROP TABLE crm.old;\n")
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready(["crm-038"])), 4)
        self.assertFalse([c for c in r.called(ship_common.AS_APP) if "workflow" in c])

    def test_red_run_and_unregistered_key_fail(self):
        r = self.runner("CREATE TABLE crm.task (id int);\n", conclusion="failure", job_log=LOCK_LOG)
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready(["crm-036", "crm-037"])), 1)
        r = self.runner("CREATE TABLE crm.task (id int);\n")
        self.assertEqual(sca.main(["crm", "038"], runner=r, fetch=self.ready(["crm-036", "crm-037"])), 1)
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
        self.assertFalse(r.called("gh", "pr", "list"))  # a check reads no copy PR and no owner order
        [dispatch] = [c for c in r.called(ship_common.AS_APP) if "workflow" in c]
        self.assertIn("mode=check", dispatch)


if __name__ == "__main__":
    unittest.main()
