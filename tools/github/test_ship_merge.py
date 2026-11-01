"""Tests for ship_merge.py and ship_common.py (AA-1032). Offline: every gh/aws call is scripted.

Run: python -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import unittest

import ship_common
import ship_merge
from ship_common import Result, ShipError, classify_checks, normalize_repo, parse_targets
from ship_fakes import FakeRunner, check, pr, run_row, status_ctx


def js(obj) -> Result:
    return Result(0, json.dumps(obj))


NO_DELETES = Result(0, "[]\n")


class NamesTest(unittest.TestCase):
    def test_normalize_repo_variants(self):
        self.assertEqual(normalize_repo("AA-Ecosys (root)"), "AA-Ecosys")
        self.assertEqual(normalize_repo("apps/AA-CIS-App"), "AA-CIS-App")
        self.assertEqual(normalize_repo("AdventureAsia365-Ecosys/AA-Booking"), "AA-Booking")
        self.assertEqual(normalize_repo("infra/AA-CIS-Infra"), "AA-CIS-Infra")
        self.assertEqual(normalize_repo("crm"), "AA-Partner")
        self.assertEqual(normalize_repo("tp"), "AA-TripPlanner-Web")
        with self.assertRaises(ShipError):
            normalize_repo("AA-Unknown")

    def test_parse_targets_forms(self):
        self.assertEqual(parse_targets(["AA-CIS-App 1230", "infra#585", "root", "438", "tp #208"]),
                         [("AA-CIS-App", 1230), ("AA-CIS-Infra", 585), ("AA-Ecosys", 438),
                          ("AA-TripPlanner-Web", 208)])
        with self.assertRaises(ShipError):
            parse_targets(["AA-CIS-App"])


class ClassifyTest(unittest.TestCase):
    def test_red_non_required_check_is_red(self):
        # S263 #1225: every required check green, the non-required "Migration preflight" red.
        s = classify_checks([check("OpenAPI breaking changes", wf="API contract"), check("Unit tests"),
                             check("Migration preflight", "FAILURE")])
        self.assertEqual(s.red, ["CI / Migration preflight (failure)"])
        self.assertEqual(len(s.green), 2)

    def test_rerun_replaces_older_run_but_latest_cancelled_is_red(self):
        older = check("gitleaks", "CANCELLED", wf="Secret scan", started="2026-11-01T09:00:00Z")
        newer = check("gitleaks", "SUCCESS", wf="Secret scan", started="2026-11-01T09:05:00Z")
        self.assertEqual(classify_checks([older, newer]).red, [])
        self.assertEqual(classify_checks([newer, older]).red, [])
        latest_cancelled = check("gitleaks", "CANCELLED", wf="Secret scan", started="2026-11-01T09:10:00Z")
        self.assertEqual(len(classify_checks([newer, latest_cancelled]).red), 1)

    def test_status_contexts_and_pending(self):
        s = classify_checks([status_ctx("Vercel", "PENDING"), check("Build", None, status="IN_PROGRESS"),
                             status_ctx("Vercel Preview", "FAILURE"), check("Skipped job", "SKIPPED"),
                             check("Neutral job", "NEUTRAL")])
        self.assertEqual(len(s.pending), 2)
        self.assertEqual(s.red, ["Vercel Preview (failure)"])
        self.assertEqual(len(s.green), 2)


class GateAndMergeTest(unittest.TestCase):
    def setUp(self):
        self.out = io.StringIO()
        self._redirect = contextlib.redirect_stdout(self.out)
        self._redirect.__enter__()

    def tearDown(self):
        self._redirect.__exit__(None, None, None)

    def test_refuses_red_check_and_never_merges(self):
        r = FakeRunner().on(("gh", "pr", "view"), js(pr(checks=[check("Unit tests"),
                                                                check("Migration preflight", "FAILURE")])))
        with self.assertRaises(ShipError) as cm:
            ship_merge.merge_one(r, "AA-CIS-App", 1225)
        self.assertEqual(cm.exception.code, 3)
        self.assertIn("Migration preflight", str(cm.exception))
        self.assertFalse(r.called(ship_common.MERGEQ))
        self.assertFalse(r.called("merge"))

    def test_waits_for_pending_then_merges_through_queue(self):
        pending = pr(checks=[check("Unit tests"), check("Integration", None, status="IN_PROGRESS")])
        r = (FakeRunner()
             .on(("gh", "pr", "view"), js(pending), js(pr()), js(pr()), js(pr(state="MERGED", merge_oid="b" * 40)))
             .on(("gh", "api"), NO_DELETES)
             .on((ship_common.MERGEQ,), Result(0, "AA-CIS-App #7 MERGED bbbbbbbb")))
        sha = ship_merge.merge_one(r, "AA-CIS-App", 7, interval=60)
        self.assertEqual(sha, "b" * 40)
        self.assertEqual(r.called(ship_common.MERGEQ), [[ship_common.MERGEQ, "AA-CIS-App", "7"]])
        self.assertGreaterEqual(r.slept, 60)

    def test_non_queue_repo_squashes_the_gated_head_as_the_app(self):
        head = "c" * 40
        r = (FakeRunner()
             .on(("gh", "pr", "view"), js(pr(head=head, base="master")), js(pr(head=head, base="master")),
                 js(pr(state="MERGED", merge_oid="d" * 40, base="master")))
             .on(("gh", "api"), NO_DELETES)
             .on((ship_common.AS_APP,), Result(0, "")))
        ship_merge.merge_one(r, "AA-Ecosys", 438)
        [call] = r.called(ship_common.AS_APP)
        self.assertEqual(call[:4], [ship_common.AS_APP, "--repos", "AA-Ecosys", "--"])
        self.assertIn("--squash", call)
        self.assertNotIn("--auto", call)
        self.assertEqual(call[call.index("--match-head-commit") + 1], head)

    def test_refusals_draft_base_dirty_deletes(self):
        cases = [(pr(draft=True), "draft"), (pr(base="feat/below"), "base"), (pr(mss="DIRTY"), "DIRTY")]
        for p, word in cases:
            r = FakeRunner().on(("gh", "pr", "view"), js(p)).on(("gh", "api"), NO_DELETES)
            with self.assertRaises(ShipError) as cm:
                ship_merge.merge_one(r, "AA-CIS-Infra", 5)
            self.assertEqual(cm.exception.code, 4)
            self.assertIn(word, str(cm.exception))
        r = FakeRunner().on(("gh", "pr", "view"), js(pr())).on(("gh", "api"), Result(0, '["a.py","b.py"]\n'))
        with self.assertRaises(ShipError) as cm:
            ship_merge.merge_one(r, "AA-CIS-Infra", 5)
        self.assertIn("deletes 2 file", str(cm.exception))
        r = (FakeRunner().on(("gh", "pr", "view"), js(pr()), js(pr()), js(pr(state="MERGED", merge_oid="e" * 40)))
             .on((ship_common.AS_APP,), Result(0, "")))
        self.assertEqual(ship_merge.merge_one(r, "AA-CIS-Infra", 5, allow_deletes=True), "e" * 40)

    def test_already_merged_and_check_only(self):
        r = FakeRunner().on(("gh", "pr", "view"), js(pr(state="MERGED", merge_oid="f" * 40)))
        self.assertEqual(ship_merge.merge_one(r, "AA-Booking", 3), "f" * 40)
        r = FakeRunner().on(("gh", "pr", "view"), js(pr())).on(("gh", "api"), NO_DELETES)
        self.assertEqual(ship_merge.merge_one(r, "AA-Booking", 3, check_only=True), "")
        self.assertFalse(r.called(ship_common.MERGEQ))

    def test_pending_timeout_and_no_checks(self):
        r = FakeRunner().on(("gh", "pr", "view"), js(pr(checks=[check("Slow", None, status="QUEUED")])))
        with self.assertRaises(ShipError) as cm:
            ship_merge.merge_one(r, "AA-Partner", 9, timeout=300, interval=60)
        self.assertEqual(cm.exception.code, 5)
        r = FakeRunner().on(("gh", "pr", "view"), js(pr(checks=[])))
        with self.assertRaises(ShipError) as cm:
            ship_merge.merge_one(r, "AA-Partner", 9)
        self.assertEqual(cm.exception.code, 3)
        self.assertIn("no check", str(cm.exception))

    def test_queue_says_not_merged_but_github_already_merged(self):
        # Lesson S255: mergeq.sh can report "not merged" while the queue has just merged the PR.
        r = (FakeRunner()
             .on(("gh", "pr", "view"), js(pr()), js(pr()), js(pr()), js(pr(state="MERGED", merge_oid="1" * 40)))
             .on(("gh", "api"), NO_DELETES)
             .on((ship_common.MERGEQ,), Result(4, "not merged and not in the queue")))
        self.assertEqual(ship_merge.merge_one(r, "AA-CIS-App", 11), "1" * 40)

    def test_merge_failure_is_reported(self):
        r = (FakeRunner().on(("gh", "pr", "view"), js(pr()))
             .on(("gh", "api"), NO_DELETES)
             .on((ship_common.MERGEQ,), Result(4, "dropped from the queue")))
        with self.assertRaises(ShipError) as cm:
            ship_merge.merge_one(r, "AA-CIS-App", 12)
        self.assertEqual(cm.exception.code, 4)
        self.assertIn("dropped from the queue", str(cm.exception))


class SettleTest(unittest.TestCase):
    """A green read is confirmed by a second read and by the workflow runs on the head (late checks)."""

    def setUp(self):
        self.redirect = contextlib.redirect_stdout(io.StringIO())
        self.redirect.__enter__()

    def tearDown(self):
        self.redirect.__exit__(None, None, None)

    def test_new_pending_check_on_the_second_read_is_waited_for(self):
        # A `needs:` job registers its check only once it is queued: it shows up on the settle read.
        first = pr(checks=[check("Lint"), check("Unit tests")])
        late_pending = pr(checks=[check("Lint"), check("Unit tests"), check("Apply plan", None, status="QUEUED")])
        late_red = pr(checks=[check("Lint"), check("Unit tests"), check("Apply plan", "FAILURE")])
        r = (FakeRunner().on(("gh", "pr", "view"), js(first), js(late_pending), js(late_red))
             .on(("gh", "api"), NO_DELETES).on((ship_common.MERGEQ,), Result(0, "")))
        with self.assertRaises(ShipError) as cm:
            ship_merge.merge_one(r, "AA-CIS-App", 21)
        self.assertEqual(cm.exception.code, 3)
        self.assertIn("Apply plan", str(cm.exception))
        self.assertFalse(r.called(ship_common.MERGEQ))
        self.assertGreaterEqual(r.slept, ship_merge.SETTLE_SECONDS)

    def test_new_green_check_resets_the_settle_read(self):
        first = pr(checks=[check("Lint")])
        more = pr(checks=[check("Lint"), check("Copy guard")])
        r = (FakeRunner().on(("gh", "pr", "view"), js(first), js(more), js(more),
                             js(pr(state="MERGED", merge_oid="9" * 40)))
             .on(("gh", "api"), NO_DELETES).on((ship_common.AS_APP,), Result(0, "")))
        self.assertEqual(ship_merge.merge_one(r, "AA-CIS-Infra", 22), "9" * 40)
        self.assertEqual(len(r.called("gh", "pr", "view")), 4)
        self.assertEqual(len(r.called("--commit")), 1)

    def test_pending_or_red_workflow_run_on_the_head_blocks(self):
        # A workflow_run workflow has no check on the PR yet, but its run on the head commit is queued, then red.
        runs_pending = js([run_row("CI"), run_row("Migration Copy Guard", status="queued", conclusion=None,
                                              event="workflow_run")])
        runs_red = js([run_row("CI"), run_row("Migration Copy Guard", conclusion="failure", event="workflow_run")])
        r = (FakeRunner().on(("gh", "pr", "view"), js(pr(base="master")))
             .on(("gh", "run", "list", "--commit"), runs_pending, runs_red)
             .on(("gh", "api"), NO_DELETES).on((ship_common.AS_APP,), Result(0, "")))
        with self.assertRaises(ShipError) as cm:
            ship_merge.merge_one(r, "AA-Ecosys", 23)
        self.assertEqual(cm.exception.code, 3)
        self.assertIn("Migration Copy Guard (workflow_run) failure", str(cm.exception))
        self.assertFalse(r.called(ship_common.AS_APP))
        self.assertEqual(len(r.called("--commit")), 2)

    def test_superseded_cancelled_run_does_not_block(self):
        runs = [run_row("CI", conclusion="cancelled", created="2026-11-01T09:00:00Z"),
                run_row("CI", created="2026-11-01T09:05:00Z")]
        s = ship_common.classify_runs(runs)
        self.assertEqual((s.red, s.pending), ([], []))
        s = ship_common.classify_runs(list(reversed(runs)) + [run_row("CI", conclusion="cancelled",
                                                                        created="2026-11-01T09:10:00Z")])
        self.assertEqual(s.red, ["CI (pull_request) cancelled"])


class RunTargetsTest(unittest.TestCase):
    def test_one_red_one_green_in_parallel(self):
        def view(argv):
            n = argv[argv.index("view") + 1]
            if n == "1":
                return js(pr(1, checks=[check("Migration preflight", "FAILURE")]))
            return js(pr(2, base="master", state="MERGED" if r.called(ship_common.AS_APP) else "OPEN",
                         merge_oid="2" * 40))
        r = FakeRunner().on(("gh", "pr", "view"), view).on(("gh", "api"), NO_DELETES).on(
            (ship_common.AS_APP,), Result(0, ""))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = ship_merge.run_targets(r, [("AA-CIS-App", 1), ("AA-Ecosys", 2)])
        self.assertEqual(code, 3)
        self.assertIn("AA-Ecosys#2: ok - MERGED 22222222", out.getvalue())
        self.assertFalse(r.called(ship_common.MERGEQ))

    def test_serial_stops_at_first_failure(self):
        r = FakeRunner().on(("gh", "pr", "view"), js(pr(checks=[check("Unit tests", "FAILURE")])))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = ship_merge.run_targets(r, [("AA-Booking", 1), ("AA-Booking", 2)], serial=True)
        self.assertEqual(code, 4)
        self.assertIn("AA-Booking#2: exit 4 - AA-Booking#2 skipped", out.getvalue())
        self.assertEqual(len(r.called("gh", "pr", "view")), 1)


class MfaTest(unittest.TestCase):
    def test_reads_only_expiration_and_prints_no_secret(self):
        secret = "SECRETVALUE-not-to-print"
        creds = {"Version": 1, "AccessKeyId": "AKIAEXAMPLE", "SecretAccessKey": secret, "SessionToken": secret,
                 "Expiration": "2026-10-28T03:20:00+00:00"}
        r = FakeRunner().on(("aws", "configure", "export-credentials"), js(creds))
        r.t = 1_793_156_400.0  # 2026-10-28T03:00:00Z: 20 minutes left
        with contextlib.redirect_stdout(io.StringIO()) as out:
            ship_common.warn_mfa(r, need_minutes=30)
        self.assertIn("MFA session ends in 20 min", out.getvalue())
        self.assertNotIn(secret, out.getvalue())
        self.assertNotIn("AKIA", out.getvalue())

    def test_session_start_line(self):
        r = FakeRunner().on(("aws",), js({"Expiration": "2026-10-28T08:00:00+00:00", "SessionToken": "x" * 20}))
        r.t = 1_793_156_400.0  # 03:00Z
        code, line = ship_common.mfa_status_line(r)
        self.assertEqual(code, 0)
        self.assertIn("(2026-10-28T08:00Z), 300 min left; remind the tech lead at", line)
        self.assertNotIn("x" * 20, line)
        code, line = ship_common.mfa_status_line(FakeRunner().on(("aws",), Result(255, "", "expired")))
        self.assertEqual(code, 1)
        self.assertIn("aws sts get-caller-identity --profile aa365-admin", line)

    def test_expired_session_warns(self):
        r = FakeRunner().on(("aws",), Result(255, "", "token expired"))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            ship_common.warn_mfa(r)
        self.assertIn("expired or unreadable", out.getvalue())


if __name__ == "__main__":
    unittest.main()
